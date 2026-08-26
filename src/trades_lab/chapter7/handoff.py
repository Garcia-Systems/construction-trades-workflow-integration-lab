"""Bounded FieldTrack observations projected to the operational office boundary."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from trades_lab.domain import (ExceptionCategory, ExceptionRecord, ExceptionStatus,
                               IntegrationEvent, Provenance, SourceReference)

SOURCE_SYSTEM = "FieldTrack"


class FieldStatus(StrEnum):
    DISPATCHED = "DISPATCHED"
    ARRIVED = "ARRIVED"
    IN_PROGRESS = "IN_PROGRESS"
    BLOCKED = "BLOCKED"
    PARTIALLY_COMPLETE = "PARTIALLY_COMPLETE"
    COMPLETED = "COMPLETED"


class BlockedReason(StrEnum):
    MATERIAL_MISSING = "MATERIAL_MISSING"
    CUSTOMER_UNAVAILABLE = "CUSTOMER_UNAVAILABLE"
    SITE_ACCESS = "SITE_ACCESS"
    ADDITIONAL_APPROVAL = "ADDITIONAL_APPROVAL"
    UNKNOWN = "UNKNOWN"


class FieldStatusOutcome(StrEnum):
    APPLIED = "APPLIED"
    DUPLICATE = "DUPLICATE"
    STALE = "STALE"
    IGNORED_NOT_RELEVANT = "IGNORED_NOT_RELEVANT"
    EXCEPTION = "EXCEPTION"


@dataclass(frozen=True)
class RawFieldTrackEvent:
    event_id: str
    job_id: str
    crew_id: str
    status: str
    occurred_at: datetime
    sequence: int | None
    notes_code: str | None = None


@dataclass(frozen=True)
class FieldStatusObservation:
    correlation_id: str
    source_event_id: str
    authoritative_job_id: str
    source_job_id: str
    crew_reference: str
    canonical_status: FieldStatus
    occurred_at: datetime
    source_sequence: int | None
    blocked_reason: BlockedReason | None
    provenance: Provenance


@dataclass(frozen=True)
class OfficeFieldStatusUpdate:
    correlation_id: str
    authoritative_job_id: str
    field_status: FieldStatus
    crew_reference: str
    occurred_at: datetime
    blocked_reason: BlockedReason | None
    source_event_id: str


@dataclass(frozen=True)
class FieldStatusResult:
    outcome: FieldStatusOutcome
    observation: FieldStatusObservation | None
    office_update: OfficeFieldStatusUpdate | None
    exception: ExceptionRecord | None
    events: tuple[IntegrationEvent, ...]


class FieldTrackAdapter:
    """Maps only the source states required by this downstream workflow."""

    STATUS_MAP = {
        "EN_ROUTE": FieldStatus.DISPATCHED, "ONSITE": FieldStatus.ARRIVED,
        "WORKING": FieldStatus.IN_PROGRESS, "HOLD": FieldStatus.BLOCKED,
        "PARTIAL": FieldStatus.PARTIALLY_COMPLETE, "DONE": FieldStatus.COMPLETED,
    }
    NOT_RELEVANT = frozenset({"BREAK_STARTED", "BREAK_ENDED", "PHOTO_UPLOADED"})

    def normalize(self, status: str) -> FieldStatus:
        try:
            return self.STATUS_MAP[status]
        except KeyError as error:
            raise ValueError(f"unsupported FieldTrack status: {status}") from error


class FieldStatusHandoff:
    """Process-local replay/sequence model; FieldTrack remains authoritative."""

    ALLOWED_NEXT = {
        FieldStatus.DISPATCHED: {FieldStatus.DISPATCHED, FieldStatus.ARRIVED,
                                 FieldStatus.IN_PROGRESS, FieldStatus.BLOCKED,
                                 FieldStatus.PARTIALLY_COMPLETE, FieldStatus.COMPLETED},
        FieldStatus.ARRIVED: {FieldStatus.ARRIVED, FieldStatus.IN_PROGRESS,
                              FieldStatus.BLOCKED, FieldStatus.PARTIALLY_COMPLETE,
                              FieldStatus.COMPLETED},
        FieldStatus.IN_PROGRESS: {FieldStatus.IN_PROGRESS, FieldStatus.BLOCKED,
                                  FieldStatus.PARTIALLY_COMPLETE, FieldStatus.COMPLETED},
        FieldStatus.BLOCKED: {FieldStatus.BLOCKED, FieldStatus.IN_PROGRESS,
                              FieldStatus.PARTIALLY_COMPLETE, FieldStatus.COMPLETED},
        FieldStatus.PARTIALLY_COMPLETE: {FieldStatus.PARTIALLY_COMPLETE,
                                         FieldStatus.IN_PROGRESS, FieldStatus.COMPLETED},
        FieldStatus.COMPLETED: {FieldStatus.COMPLETED},
    }

    def __init__(self, job_mappings: dict[str, str], crew_mappings: dict[str, str],
                 adapter: FieldTrackAdapter | None = None) -> None:
        self.job_mappings = job_mappings
        self.crew_mappings = crew_mappings
        self.adapter = adapter or FieldTrackAdapter()
        self._seen: set[str] = set()
        self._sequences: dict[str, int] = {}
        self.current_status: dict[str, FieldStatus] = {}
        self.office_updates: list[OfficeFieldStatusUpdate] = []

    def process(self, raw: RawFieldTrackEvent) -> FieldStatusResult:
        correlation = f"corr-field-{raw.event_id.lower()}"
        events = [self._event("FIELD_EVENT_OBSERVED", raw, correlation, raw.job_id)]
        if raw.event_id in self._seen:
            events.append(self._event("FIELD_EVENT_DUPLICATE", raw, correlation, raw.job_id))
            return FieldStatusResult(FieldStatusOutcome.DUPLICATE, None, None, None, tuple(events))
        # Remember deliveries, including stopped ones: replay is still transport replay.
        self._seen.add(raw.event_id)
        if raw.status in self.adapter.NOT_RELEVANT:
            return FieldStatusResult(FieldStatusOutcome.IGNORED_NOT_RELEVANT, None, None, None,
                                     tuple(events))
        try:
            status = self.adapter.normalize(raw.status)
        except ValueError as error:
            events.append(self._event("FIELD_STATUS_MAPPING_FAILED", raw, correlation, raw.job_id))
            return self._failure(raw, correlation, events, ExceptionCategory.MAPPING, str(error))
        events.append(self._event("FIELD_STATUS_MAPPED", raw, correlation, raw.job_id,
                                  (("canonical_status", status.value),)))
        job_id = self.job_mappings.get(raw.job_id)
        if not job_id:
            return self._failure(raw, correlation, events, ExceptionCategory.IDENTITY,
                                 "unknown FieldTrack job identity")
        crew = self.crew_mappings.get(raw.crew_id)
        if not crew:
            return self._failure(raw, correlation, events, ExceptionCategory.IDENTITY,
                                 "unknown FieldTrack crew identity")
        latest = self._sequences.get(job_id)
        if raw.sequence is not None and latest is not None and raw.sequence <= latest:
            events.append(self._event("FIELD_EVENT_STALE", raw, correlation, job_id))
            return FieldStatusResult(FieldStatusOutcome.STALE, None, None, None, tuple(events))
        previous = self.current_status.get(job_id)
        if previous is not None and status not in self.ALLOWED_NEXT[previous]:
            return self._failure(raw, correlation, events, ExceptionCategory.STATE_CONFLICT,
                                 f"invalid field progression: {previous.value} -> {status.value}")
        reason = None
        if status is FieldStatus.BLOCKED:
            try:
                reason = BlockedReason(raw.notes_code or "UNKNOWN")
            except ValueError:
                reason = BlockedReason.UNKNOWN
        provenance = Provenance(SourceReference(SOURCE_SYSTEM, raw.event_id), raw.occurred_at,
                                str(raw.sequence) if raw.sequence is not None else None, correlation)
        observation = FieldStatusObservation(correlation, raw.event_id, job_id, raw.job_id, crew,
                                             status, raw.occurred_at, raw.sequence, reason, provenance)
        update = OfficeFieldStatusUpdate(correlation, job_id, status, crew, raw.occurred_at,
                                         reason, raw.event_id)
        if raw.sequence is not None:
            self._sequences[job_id] = raw.sequence
        self.current_status[job_id] = status
        self.office_updates.append(update)
        events.append(self._event("FIELD_STATUS_APPLIED", raw, correlation, job_id))
        if status is FieldStatus.BLOCKED:
            events.extend((self._event("FIELD_STATUS_BLOCKED", raw, correlation, job_id),
                           self._event("OFFICE_ATTENTION_REQUIRED", raw, correlation, job_id)))
        events.extend((self._event("OFFICE_STATUS_UPDATE_READY", raw, correlation, job_id),
                       self._event("OFFICE_STATUS_UPDATE_ACKNOWLEDGED", raw, correlation, job_id)))
        return FieldStatusResult(FieldStatusOutcome.APPLIED, observation, update, None, tuple(events))

    def _failure(self, raw, correlation, events, category, summary):
        exception = ExceptionRecord(f"EX-{raw.event_id}", category, "FIELD_EVENT", raw.event_id,
                                    SOURCE_SYSTEM, summary, ExceptionStatus.OPEN, raw.occurred_at,
                                    correlation)
        events.append(self._event("EXCEPTION_CREATED", raw, correlation, raw.job_id))
        return FieldStatusResult(FieldStatusOutcome.EXCEPTION, None, None, exception, tuple(events))

    @staticmethod
    def _event(kind, raw, correlation, entity_id, metadata=()):
        return IntegrationEvent(f"{raw.event_id}-{kind}", kind, SOURCE_SYSTEM, raw.event_id,
                                "JOB", entity_id, raw.occurred_at, correlation, metadata)


ARCHITECTURE_INVENTORY = (
    ("SHARED CORE", "provenance, correlation, integration events, and exceptions"),
    ("SOURCE-SPECIFIC ADAPTER", "FieldTrack fixture ingestion and bounded status mapping"),
    ("WORKFLOW-SPECIFIC LOGIC", "field progression, blocked context, completion semantics"),
    ("CUSTOMER-SPECIFIC RULE", "which FieldTrack statuses matter downstream"),
    ("CONFIGURATION", "job and crew identity mappings"),
    ("VALIDATION", "known status and resolved identity checks"),
    ("RELIABILITY", "source-event replay and per-job sequence checks"),
    ("EXCEPTION HANDLING", "controlled mapping and identity exceptions"),
    ("TESTING", "deterministic field scenario fixtures"),
    ("SUPPORT SURFACE", "status/sequence semantics, identity maps, reasons, delivery behavior"),
)
