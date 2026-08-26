"""The bounded, synthetic EstimateWorks-to-CrewBoard write experiment.

CrewBoard remains authoritative for jobs.  The process-local registry records
only integration facts and is intentionally neither persistence nor job state.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any, Mapping

from trades_lab.domain import (ExceptionCategory, ExceptionRecord, ExceptionStatus,
                               IntegrationEvent, Provenance, SourceReference)

SOURCE_SYSTEM = "EstimateWorks"
DESTINATION_SYSTEM = "CrewBoard"


class JobHandoffOutcome(StrEnum):
    CREATED = "CREATED"
    IDEMPOTENT_REPLAY = "IDEMPOTENT_REPLAY"
    NOT_ELIGIBLE = "NOT_ELIGIBLE"
    STALE = "STALE"
    EXCEPTION = "EXCEPTION"


class IdempotencyStatus(StrEnum):
    PENDING = "PENDING"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    CONFLICT = "CONFLICT"


@dataclass(frozen=True)
class ServiceAddress:
    line1: str
    city: str
    state: str
    postal_code: str


@dataclass(frozen=True)
class AcceptedEstimate:
    source_reference: SourceReference
    version: int
    customer_reference: str
    accepted_at: datetime
    service_address: ServiceAddress
    scope_summary: str
    provenance: Provenance


@dataclass(frozen=True)
class JobCreateCommand:
    idempotency_key: str
    correlation_id: str
    source_estimate_id: str
    source_estimate_version: int
    customer_reference: str
    service_address: ServiceAddress
    scope_summary: str
    provenance: Provenance


@dataclass(frozen=True)
class JobCreationAcknowledgement:
    destination_job_id: str
    external_reference: str
    created: bool
    correlation_id: str
    provenance: Provenance


@dataclass(frozen=True)
class DestinationJob:
    job_id: str
    external_reference: str
    source_estimate_id: str
    source_estimate_version: int
    customer_reference: str
    service_address: ServiceAddress
    scope_summary: str


@dataclass(frozen=True)
class IdempotencyRecord:
    idempotency_key: str
    source_estimate_id: str
    source_estimate_version: int
    correlation_id: str
    destination_job_id: str | None
    status: IdempotencyStatus


@dataclass(frozen=True)
class JobHandoffResult:
    outcome: JobHandoffOutcome
    correlation_id: str
    explanation: str
    estimate: AcceptedEstimate | None
    command: JobCreateCommand | None
    acknowledgement: JobCreationAcknowledgement | None
    exception: ExceptionRecord | None
    events: tuple[IntegrationEvent, ...]


class EstimateValidationError(ValueError):
    pass


class DestinationConflict(ValueError):
    pass


class EstimateWorksAdapter:
    """Normalize the one modeled EstimateWorks record shape used by this lab."""

    def normalize(self, raw: Mapping[str, Any], correlation_id: str) -> AcceptedEstimate:
        estimate_id = self._text(raw, "estimate_id")
        version = raw.get("estimate_version")
        if not isinstance(version, int) or isinstance(version, bool) or version < 1:
            raise EstimateValidationError("estimate_version is required and must be positive")
        customer_id = self._text(raw, "customer_id", ExceptionCategory.IDENTITY)
        accepted_text = self._text(raw, "accepted_at")
        try:
            accepted_at = datetime.fromisoformat(accepted_text.replace("Z", "+00:00"))
        except ValueError as error:
            raise EstimateValidationError("accepted_at must be an ISO timestamp") from error
        scope = self._text(raw, "scope")
        address_raw = raw.get("service_address")
        if not isinstance(address_raw, Mapping):
            raise EstimateValidationError("service_address is required")
        address = ServiceAddress(*(self._text(address_raw, key) for key in
                                   ("line1", "city", "state", "postal_code")))
        source = SourceReference(SOURCE_SYSTEM, estimate_id)
        provenance = Provenance(source, accepted_at, str(version), correlation_id)
        return AcceptedEstimate(source, version, customer_id, accepted_at, address, scope,
                                provenance)

    @staticmethod
    def _text(raw: Mapping[str, Any], key: str,
              category: ExceptionCategory = ExceptionCategory.VALIDATION) -> str:
        value = raw.get(key)
        if not isinstance(value, str) or not value.strip():
            error = EstimateValidationError(f"{key} is required and must be text")
            error.category = category
            raise error
        return value.strip()


class CrewBoardSimulator:
    """Small authoritative boundary with external-reference lookup semantics."""

    def __init__(self) -> None:
        self._jobs: dict[str, DestinationJob] = {}
        self._by_estimate: dict[str, str] = {}

    @property
    def jobs(self) -> tuple[DestinationJob, ...]:
        return tuple(self._jobs.values())

    def find_by_external_reference(self, reference: str) -> DestinationJob | None:
        return self._jobs.get(reference)

    def find_by_source_estimate(self, estimate_id: str) -> DestinationJob | None:
        reference = self._by_estimate.get(estimate_id)
        return self._jobs.get(reference) if reference else None

    def preload_job(self, job: DestinationJob) -> None:
        self._jobs[job.external_reference] = job
        self._by_estimate[job.source_estimate_id] = job.external_reference

    seed_job = preload_job

    def create_job(self, command: JobCreateCommand) -> JobCreationAcknowledgement:
        existing = self.find_by_external_reference(command.idempotency_key)
        if existing:
            if not self._compatible(existing, command):
                raise DestinationConflict("external reference belongs to incompatible job data")
            return self._ack(existing, command, False)
        claimed = self.find_by_source_estimate(command.source_estimate_id)
        if claimed:
            raise DestinationConflict("source estimate is already claimed by an incompatible job")
        job = DestinationJob(f"JOB-{9001 + len(self._jobs)}", command.idempotency_key,
                             command.source_estimate_id, command.source_estimate_version,
                             command.customer_reference, command.service_address,
                             command.scope_summary)
        self.preload_job(job)
        return self._ack(job, command, True)

    @staticmethod
    def _compatible(job: DestinationJob, command: JobCreateCommand) -> bool:
        return (job.source_estimate_id, job.source_estimate_version,
                job.customer_reference, job.service_address, job.scope_summary) == (
                    command.source_estimate_id, command.source_estimate_version,
                    command.customer_reference, command.service_address,
                    command.scope_summary)

    @staticmethod
    def _ack(job: DestinationJob, command: JobCreateCommand,
             created: bool) -> JobCreationAcknowledgement:
        return JobCreationAcknowledgement(job.job_id, job.external_reference, created,
                                          command.correlation_id, command.provenance)


class AcceptedEstimateToJobHandoff:
    """Coordinates one consequential write under Chapter 4's modeled capabilities."""

    def __init__(self, destination: CrewBoardSimulator | None = None,
                 adapter: EstimateWorksAdapter | None = None,
                 *, write_capability_confirmed: bool = True,
                 approval_boundary_known: bool = True) -> None:
        self.destination = destination or CrewBoardSimulator()
        self.adapter = adapter or EstimateWorksAdapter()
        self.write_capability_confirmed = write_capability_confirmed
        self.approval_boundary_known = approval_boundary_known
        self.registry: dict[str, IdempotencyRecord] = {}
        self.commands: list[JobCreateCommand] = []
        self._highest_versions: dict[str, int] = {}

    @staticmethod
    def idempotency_key(estimate_id: str, version: int) -> str:
        # Business identity is stable across random transport delivery attempts.
        return f"accepted-estimate:{estimate_id}:v{version}"

    def process(self, raw: Mapping[str, Any], delivery_id: str = "event-001") -> JobHandoffResult:
        raw = raw if isinstance(raw, Mapping) else {}
        estimate_id = raw.get("estimate_id") if isinstance(raw.get("estimate_id"), str) else "UNKNOWN"
        version = raw.get("estimate_version")
        correlation = self._correlation(estimate_id, version)
        time = self._time(raw.get("accepted_at"))
        events = [self._event("ESTIMATE_OBSERVED", estimate_id, correlation, time, 1,
                              delivery_id)]
        status = raw.get("status")
        if status != "CUSTOMER_APPROVED":
            events.append(self._event("ESTIMATE_NOT_ELIGIBLE", estimate_id, correlation,
                                      time, 2, delivery_id))
            return JobHandoffResult(JobHandoffOutcome.NOT_ELIGIBLE, correlation,
                                    f"EstimateWorks state {status!r} is not ACCEPTED",
                                    None, None, None, None, tuple(events))
        try:
            if not self.write_capability_confirmed:
                raise EstimateValidationError("destination write capability is not confirmed")
            if not self.approval_boundary_known:
                raise EstimateValidationError("consequential-write approval boundary is unknown")
            estimate = self.adapter.normalize(raw, correlation)
        except EstimateValidationError as error:
            category = getattr(error, "category", ExceptionCategory.VALIDATION)
            events.append(self._event("ESTIMATE_VALIDATION_FAILED", estimate_id, correlation,
                                      time, 2, delivery_id))
            return self._exception(estimate_id, correlation, str(error), category, events, time)

        highest = self._highest_versions.get(estimate_id)
        if highest is None:
            existing = self.destination.find_by_source_estimate(estimate_id)
            highest = existing.source_estimate_version if existing else None
        if highest is not None and estimate.version < highest:
            events.append(self._event("STALE_ESTIMATE_DETECTED", estimate_id, correlation,
                                      time, 2, delivery_id))
            return JobHandoffResult(JobHandoffOutcome.STALE, correlation,
                                    f"version {estimate.version} is older than version {highest}",
                                    estimate, None, None, None, tuple(events))

        key = self.idempotency_key(estimate_id, estimate.version)
        existing = self.destination.find_by_external_reference(key)
        command = self._command(estimate, key, correlation)
        if existing:
            try:
                acknowledgement = self.destination.create_job(command)
            except DestinationConflict as error:
                return self._conflict(estimate, command, correlation, str(error), events, time,
                                      delivery_id)
            self.registry[key] = IdempotencyRecord(key, estimate_id, estimate.version,
                                                   correlation, existing.job_id,
                                                   IdempotencyStatus.ACKNOWLEDGED)
            self._highest_versions[estimate_id] = max(estimate.version, highest or 0)
            events.extend((self._event("IDEMPOTENT_REPLAY_DETECTED", estimate_id,
                                       correlation, time, 2, delivery_id),
                           self._event("JOB_EXISTING_CONFIRMED", estimate_id, correlation,
                                       time, 3, delivery_id)))
            return JobHandoffResult(JobHandoffOutcome.IDEMPOTENT_REPLAY, correlation,
                                    "existing authoritative CrewBoard job confirmed", estimate,
                                    command, acknowledgement, None, tuple(events))

        # A different version or incompatible preloaded claim is a conflict, not a new job.
        if self.destination.find_by_source_estimate(estimate_id):
            return self._conflict(estimate, command, correlation,
                                  "source estimate is already claimed by an incompatible job",
                                  events, time, delivery_id)
        events.append(self._event("ESTIMATE_VALIDATED", estimate_id, correlation, time, 2,
                                  delivery_id))
        events.append(self._event("JOB_CREATE_READY", estimate_id, correlation, time, 3,
                                  delivery_id))
        self.registry[key] = IdempotencyRecord(key, estimate_id, estimate.version,
                                               correlation, None, IdempotencyStatus.PENDING)
        self.commands.append(command)
        events.append(self._event("JOB_CREATE_SENT", estimate_id, correlation, time, 4,
                                  delivery_id))
        try:
            acknowledgement = self.destination.create_job(command)
        except DestinationConflict as error:
            return self._conflict(estimate, command, correlation, str(error), events, time,
                                  delivery_id)
        self.registry[key] = IdempotencyRecord(key, estimate_id, estimate.version,
                                               correlation, acknowledgement.destination_job_id,
                                               IdempotencyStatus.ACKNOWLEDGED)
        self._highest_versions[estimate_id] = estimate.version
        events.append(self._event("JOB_CREATE_ACKNOWLEDGED", estimate_id, correlation, time, 5,
                                  delivery_id))
        return JobHandoffResult(JobHandoffOutcome.CREATED, correlation,
                                "CrewBoard acknowledged the authoritative job", estimate,
                                command, acknowledgement, None, tuple(events))

    @staticmethod
    def _command(estimate: AcceptedEstimate, key: str,
                 correlation: str) -> JobCreateCommand:
        return JobCreateCommand(key, correlation, estimate.source_reference.source_id,
                                estimate.version, estimate.customer_reference,
                                estimate.service_address, estimate.scope_summary,
                                estimate.provenance)

    def _conflict(self, estimate: AcceptedEstimate, command: JobCreateCommand,
                  correlation: str, summary: str, events: list[IntegrationEvent],
                  time: datetime, delivery_id: str) -> JobHandoffResult:
        key = command.idempotency_key
        self.registry[key] = IdempotencyRecord(key, command.source_estimate_id,
                                               command.source_estimate_version, correlation,
                                               None, IdempotencyStatus.CONFLICT)
        events.append(self._event("JOB_CONFLICT_DETECTED", command.source_estimate_id,
                                  correlation, time, len(events) + 1, delivery_id))
        result = self._exception(command.source_estimate_id, correlation, summary,
                                 ExceptionCategory.STATE_CONFLICT, events, time, estimate,
                                 command)
        return result

    def _exception(self, estimate_id: str, correlation: str, summary: str,
                   category: ExceptionCategory, events: list[IntegrationEvent], time: datetime,
                   estimate: AcceptedEstimate | None = None,
                   command: JobCreateCommand | None = None) -> JobHandoffResult:
        events.append(self._event("EXCEPTION_CREATED", estimate_id, correlation, time,
                                  len(events) + 1, "integration"))
        exception = ExceptionRecord(f"exception-{correlation}", category, "Estimate",
                                    estimate_id, SOURCE_SYSTEM, summary, ExceptionStatus.OPEN,
                                    time, correlation)
        return JobHandoffResult(JobHandoffOutcome.EXCEPTION, correlation, summary, estimate,
                                command, None, exception, tuple(events))

    @staticmethod
    def _correlation(estimate_id: str, version: object) -> str:
        return f"corr-estimate-{estimate_id.lower()}-v{version if isinstance(version, int) else 'unknown'}"

    @staticmethod
    def _time(value: object) -> datetime:
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return datetime.fromisoformat("2000-01-01T00:00:00+00:00")

    @staticmethod
    def _event(kind: str, estimate_id: str, correlation: str, time: datetime,
               sequence: int, delivery_id: str) -> IntegrationEvent:
        return IntegrationEvent(f"{correlation}-event-{sequence}", kind, SOURCE_SYSTEM,
                                estimate_id, "Estimate", estimate_id, time, correlation,
                                (("delivery_id", delivery_id),))


ARCHITECTURE_INVENTORY = {
    "SHARED CORE": ("canonical identity", "provenance", "integration events", "exceptions"),
    "SOURCE-SPECIFIC ADAPTER": ("EstimateWorksAdapter",),
    "WORKFLOW-SPECIFIC LOGIC": ("accepted eligibility", "job command", "stale versions"),
    "RELIABILITY": ("deterministic idempotency key", "business-event deduplication",
                    "acknowledgement handling"),
    "EXCEPTION HANDLING": ("missing identity", "stale state", "destination conflict"),
    "TESTING": ("consequential-write scenarios",),
}
