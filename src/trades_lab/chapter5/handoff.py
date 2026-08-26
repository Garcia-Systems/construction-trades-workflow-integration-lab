"""Bounded job-to-schedule handoff; deliberately not a scheduling algorithm."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from hashlib import sha256

from trades_lab.chapter4 import IdempotencyStatus, ServiceAddress
from trades_lab.domain import (ExceptionCategory, ExceptionRecord, ExceptionStatus,
                               IntegrationEvent, Provenance, SourceReference)

SOURCE_SYSTEM = "CrewBoard Jobs"
DESTINATION_SYSTEM = "CrewBoard Scheduling"


class OperationalJobState(StrEnum):
    PENDING = "PENDING"
    READY = "READY"
    CANCELLED = "CANCELLED"


class CrewSkill(StrEnum):
    HVAC_INSTALL = "HVAC_INSTALL"
    HVAC_SERVICE = "HVAC_SERVICE"
    ELECTRICAL = "ELECTRICAL"
    PLUMBING = "PLUMBING"
    COMMERCIAL = "COMMERCIAL"
    TWO_PERSON_CREW = "TWO_PERSON_CREW"


class ScheduleRequestState(StrEnum):
    UNASSIGNED = "UNASSIGNED"
    ASSIGNED = "ASSIGNED"
    CANCELLED = "CANCELLED"


class ScheduleHandoffOutcome(StrEnum):
    REQUESTED = "REQUESTED"
    IDEMPOTENT_REPLAY = "IDEMPOTENT_REPLAY"
    NOT_READY = "NOT_READY"
    UPDATED_REQUEST = "UPDATED_REQUEST"
    CANCELLED = "CANCELLED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    STALE = "STALE"
    EXCEPTION = "EXCEPTION"


@dataclass(frozen=True)
class AuthoritativeJob:
    job_id: str
    external_job_reference: str
    version: int
    state: OperationalJobState
    service_address: ServiceAddress
    required_skill_tags: tuple[CrewSkill, ...]
    estimated_duration_minutes: int
    earliest_start: datetime
    latest_completion: datetime
    priority: str
    provenance: Provenance
    blocking_exception: bool = False


@dataclass(frozen=True)
class ScheduleRequestCommand:
    idempotency_key: str
    scheduling_context_version: str
    correlation_id: str
    authoritative_job_id: str
    external_job_reference: str
    service_address: ServiceAddress
    required_skill_tags: tuple[CrewSkill, ...]
    estimated_duration_minutes: int
    earliest_start: datetime
    latest_completion: datetime
    priority: str
    provenance: Provenance


@dataclass(frozen=True)
class ScheduleRequest:
    request_id: str
    command: ScheduleRequestCommand
    state: ScheduleRequestState
    previous_request_id: str | None = None


@dataclass(frozen=True)
class ScheduleAssignment:
    assignment_id: str
    authoritative_job_id: str
    request_id: str
    crew_id: str
    crew_skill_tags: tuple[CrewSkill, ...]
    starts_at: datetime
    ends_at: datetime


@dataclass(frozen=True)
class ScheduleRequestAcknowledgement:
    request_id: str
    idempotency_key: str
    correlation_id: str
    request_state: ScheduleRequestState
    created: bool
    provenance: Provenance


@dataclass(frozen=True)
class ScheduleIdempotencyRecord:
    idempotency_key: str
    request_id: str
    status: IdempotencyStatus


@dataclass(frozen=True)
class ScheduleHandoffResult:
    outcome: ScheduleHandoffOutcome
    correlation_id: str
    explanation: str
    job: AuthoritativeJob
    command: ScheduleRequestCommand | None
    acknowledgement: ScheduleRequestAcknowledgement | None
    exception: ExceptionRecord | None
    events: tuple[IntegrationEvent, ...]


class SchedulingValidationError(ValueError):
    pass


class CrewBoardSchedulingSimulator:
    """Synthetic authoritative request/assignment boundary.

    ``record_assignment`` represents CrewBoard or dispatcher behavior only; the
    integration coordinator never calls it.
    """

    def __init__(self) -> None:
        self._requests: list[ScheduleRequest] = []
        self._by_key: dict[str, ScheduleRequest] = {}
        self._assignments: dict[str, ScheduleAssignment] = {}
        self._cancelled_jobs: set[str] = set()

    @property
    def requests(self) -> tuple[ScheduleRequest, ...]:
        return tuple(self._requests)

    @property
    def assignments(self) -> tuple[ScheduleAssignment, ...]:
        return tuple(self._assignments.values())

    def get_schedule_request(self, idempotency_key: str) -> ScheduleRequest | None:
        return self._by_key.get(idempotency_key)

    def latest_for_job(self, job_id: str) -> ScheduleRequest | None:
        return next((item for item in reversed(self._requests)
                     if item.command.authoritative_job_id == job_id), None)

    def get_assignment(self, job_id: str) -> ScheduleAssignment | None:
        return self._assignments.get(job_id)

    def submit_schedule_request(self, command: ScheduleRequestCommand,
                                previous_request_id: str | None = None
                                ) -> ScheduleRequestAcknowledgement:
        existing = self._by_key.get(command.idempotency_key)
        if existing:
            return self._ack(existing, False)
        request = ScheduleRequest(f"CB-REQ-{len(self._requests) + 1:03d}", command,
                                  ScheduleRequestState.UNASSIGNED, previous_request_id)
        self._requests.append(request)
        self._by_key[command.idempotency_key] = request
        return self._ack(request, True)

    def record_assignment(self, assignment: ScheduleAssignment) -> None:
        """Preload/simulate an authoritative dispatcher decision."""
        self._assignments[assignment.authoritative_job_id] = assignment

    def cancel_requests(self, job_id: str) -> bool:
        if job_id in self._cancelled_jobs:
            return False
        self._cancelled_jobs.add(job_id)
        # Preserve every request and its provenance; cancellation is a state marker.
        for index, request in enumerate(self._requests):
            if request.command.authoritative_job_id == job_id:
                self._requests[index] = ScheduleRequest(request.request_id, request.command,
                                                        ScheduleRequestState.CANCELLED,
                                                        request.previous_request_id)
                self._by_key[request.command.idempotency_key] = self._requests[index]
        return True

    @staticmethod
    def _ack(request: ScheduleRequest, created: bool) -> ScheduleRequestAcknowledgement:
        command = request.command
        return ScheduleRequestAcknowledgement(request.request_id, command.idempotency_key,
                                              command.correlation_id, request.state, created,
                                              command.provenance)


class JobToScheduleHandoff:
    def __init__(self, destination: CrewBoardSchedulingSimulator | None = None) -> None:
        self.destination = destination or CrewBoardSchedulingSimulator()
        self.commands: list[ScheduleRequestCommand] = []
        self.registry: dict[str, ScheduleIdempotencyRecord] = {}
        self._highest_versions: dict[str, int] = {}
        self._cancelled_versions: dict[str, int] = {}

    @staticmethod
    def scheduling_context_version(job: AuthoritativeJob) -> str:
        address = job.service_address
        values = (job.job_id, str(job.estimated_duration_minutes),
                  ",".join(sorted(skill.value for skill in job.required_skill_tags)),
                  job.earliest_start.isoformat(), job.latest_completion.isoformat(),
                  address.line1, address.city, address.state, address.postal_code,
                  job.priority)
        return sha256("|".join(values).encode()).hexdigest()[:16]

    @staticmethod
    def idempotency_key(job_id: str, context_version: str) -> str:
        # Reuses Chapter 4's stable business-identity pattern, not delivery identity.
        return f"schedule-request:{job_id}:{context_version}"

    def process(self, job: AuthoritativeJob, delivery_id: str = "job-event-001") -> ScheduleHandoffResult:
        correlation = job.provenance.correlation_id or f"corr-job-{job.job_id.lower()}"
        now = job.provenance.observed_at
        events = [self._event("JOB_OBSERVED", job, correlation, now, 1, delivery_id)]
        highest = self._highest_versions.get(job.job_id)
        if highest is not None and job.version < highest:
            events.append(self._event("STALE_JOB_STATE_REJECTED", job, correlation, now, 2,
                                      delivery_id))
            return ScheduleHandoffResult(ScheduleHandoffOutcome.STALE, correlation,
                                         "observed job version is not authoritative current state",
                                         job, None, None, None, tuple(events))
        self._highest_versions[job.job_id] = max(job.version, highest or 0)

        if job.state is OperationalJobState.CANCELLED:
            return self._cancel(job, correlation, events, now, delivery_id)
        if job.job_id in self._cancelled_versions:
            events.append(self._event("STALE_JOB_STATE_REJECTED", job, correlation, now, 2,
                                      delivery_id))
            return ScheduleHandoffResult(ScheduleHandoffOutcome.STALE, correlation,
                                         "cancelled job cannot recreate scheduling work", job,
                                         None, None, None, tuple(events))
        if job.state is not OperationalJobState.READY:
            events.append(self._event("JOB_NOT_SCHEDULING_READY", job, correlation, now, 2,
                                      delivery_id))
            return ScheduleHandoffResult(ScheduleHandoffOutcome.NOT_READY, correlation,
                                         f"job state {job.state.value} is not READY", job,
                                         None, None, None, tuple(events))
        try:
            self._validate(job)
        except SchedulingValidationError as error:
            return self._exception(job, correlation, str(error), events, now, delivery_id)

        events.append(self._event("JOB_SCHEDULING_VALIDATED", job, correlation, now, 2,
                                  delivery_id))
        context = self.scheduling_context_version(job)
        key = self.idempotency_key(job.job_id, context)
        command = self._command(job, key, context, correlation)
        existing = self.destination.get_schedule_request(key)
        if existing:
            acknowledgement = self.destination.submit_schedule_request(command)
            self.registry[key] = ScheduleIdempotencyRecord(key, existing.request_id,
                                                           IdempotencyStatus.ACKNOWLEDGED)
            events.extend((self._event("IDEMPOTENT_REPLAY_DETECTED", job, correlation, now, 3,
                                       delivery_id),
                           self._event("SCHEDULE_REQUEST_EXISTING_CONFIRMED", job, correlation,
                                       now, 4, delivery_id)))
            return ScheduleHandoffResult(ScheduleHandoffOutcome.IDEMPOTENT_REPLAY, correlation,
                                         "existing CrewBoard request confirmed", job, command,
                                         acknowledgement, None, tuple(events))

        previous = self.destination.latest_for_job(job.job_id)
        assignment = self.destination.get_assignment(job.job_id)
        if previous and assignment:
            events.extend((self._event("JOB_SCHEDULING_CONTEXT_CHANGED", job, correlation, now,
                                       3, delivery_id),
                           self._event("SCHEDULE_ASSIGNMENT_CONFLICT", job, correlation, now, 4,
                                       delivery_id),
                           self._event("SCHEDULE_REVIEW_REQUIRED", job, correlation, now, 5,
                                       delivery_id)))
            exception = ExceptionRecord(f"exception-{correlation}-schedule", ExceptionCategory.STATE_CONFLICT,
                                        "Job", job.job_id, SOURCE_SYSTEM,
                                        "changed scheduling context conflicts with authoritative assignment",
                                        ExceptionStatus.OPEN, now, correlation)
            events.append(self._event("EXCEPTION_CREATED", job, correlation, now, 6, delivery_id))
            return ScheduleHandoffResult(ScheduleHandoffOutcome.REVIEW_REQUIRED, correlation,
                                         exception.summary, job, command, None, exception,
                                         tuple(events))

        outcome = ScheduleHandoffOutcome.UPDATED_REQUEST if previous else ScheduleHandoffOutcome.REQUESTED
        if previous:
            events.append(self._event("JOB_SCHEDULING_CONTEXT_CHANGED", job, correlation, now, 3,
                                      delivery_id))
        events.append(self._event("SCHEDULE_REQUEST_READY", job, correlation, now,
                                  len(events) + 1, delivery_id))
        self.commands.append(command)
        events.append(self._event("SCHEDULE_REQUEST_SENT", job, correlation, now,
                                  len(events) + 1, delivery_id))
        acknowledgement = self.destination.submit_schedule_request(
            command, previous.request_id if previous else None)
        self.registry[key] = ScheduleIdempotencyRecord(key, acknowledgement.request_id,
                                                       IdempotencyStatus.ACKNOWLEDGED)
        events.append(self._event("SCHEDULE_REQUEST_ACKNOWLEDGED", job, correlation, now,
                                  len(events) + 1, delivery_id))
        return ScheduleHandoffResult(outcome, correlation,
                                     "request accepted as UNASSIGNED; no crew was selected",
                                     job, command, acknowledgement, None, tuple(events))

    @staticmethod
    def _validate(job: AuthoritativeJob) -> None:
        if not job.job_id.strip() or not job.external_job_reference.strip():
            raise SchedulingValidationError("authoritative job identity is required")
        address = job.service_address
        if not all(value.strip() for value in (address.line1, address.city, address.state,
                                               address.postal_code)):
            raise SchedulingValidationError("valid service location is required")
        if job.estimated_duration_minutes <= 0:
            raise SchedulingValidationError("estimated duration must be positive")
        if not job.required_skill_tags:
            raise SchedulingValidationError("at least one known crew requirement is required")
        if job.earliest_start >= job.latest_completion:
            raise SchedulingValidationError("earliest start must precede latest completion")
        if job.blocking_exception:
            raise SchedulingValidationError("blocking operational exception prevents scheduling")

    @staticmethod
    def _command(job: AuthoritativeJob, key: str, context: str,
                 correlation: str) -> ScheduleRequestCommand:
        return ScheduleRequestCommand(key, context, correlation, job.job_id,
                                      job.external_job_reference, job.service_address,
                                      tuple(sorted(job.required_skill_tags, key=lambda x: x.value)),
                                      job.estimated_duration_minutes, job.earliest_start,
                                      job.latest_completion, job.priority, job.provenance)

    def _cancel(self, job: AuthoritativeJob, correlation: str,
                events: list[IntegrationEvent], now: datetime,
                delivery_id: str) -> ScheduleHandoffResult:
        first = job.job_id not in self._cancelled_versions
        self._cancelled_versions[job.job_id] = max(job.version,
                                                   self._cancelled_versions.get(job.job_id, 0))
        changed = self.destination.cancel_requests(job.job_id)
        events.append(self._event("SCHEDULE_CANCELLATION_SENT" if first else
                                  "SCHEDULE_CANCELLATION_REPLAY_CONFIRMED", job, correlation,
                                  now, 2, delivery_id))
        events.append(self._event("SCHEDULE_CANCELLATION_ACKNOWLEDGED", job, correlation, now,
                                  3, delivery_id))
        return ScheduleHandoffResult(ScheduleHandoffOutcome.CANCELLED, correlation,
                                     "cancellation acknowledged" if changed else
                                     "existing cancellation confirmed", job, None, None, None,
                                     tuple(events))

    def _exception(self, job: AuthoritativeJob, correlation: str, summary: str,
                   events: list[IntegrationEvent], now: datetime,
                   delivery_id: str) -> ScheduleHandoffResult:
        events.append(self._event("JOB_SCHEDULING_VALIDATION_FAILED", job, correlation, now, 2,
                                  delivery_id))
        exception = ExceptionRecord(f"exception-{correlation}-schedule", ExceptionCategory.VALIDATION,
                                    "Job", job.job_id or "UNKNOWN", SOURCE_SYSTEM, summary,
                                    ExceptionStatus.OPEN, now, correlation)
        events.append(self._event("EXCEPTION_CREATED", job, correlation, now, 3, delivery_id))
        return ScheduleHandoffResult(ScheduleHandoffOutcome.EXCEPTION, correlation, summary, job,
                                     None, None, exception, tuple(events))

    @staticmethod
    def _event(kind: str, job: AuthoritativeJob, correlation: str, when: datetime,
               sequence: int, delivery_id: str) -> IntegrationEvent:
        return IntegrationEvent(f"{correlation}-schedule-event-{sequence}", kind, SOURCE_SYSTEM,
                                job.job_id or "UNKNOWN", "Job", job.job_id or "UNKNOWN", when,
                                correlation, (("delivery_id", delivery_id),
                                              ("job_version", str(job.version))))


ARCHITECTURE_INVENTORY = {
    "SHARED CORE": ("SourceReference/Provenance", "IntegrationEvent/ExceptionRecord",
                    "Chapter 4 IdempotencyStatus", "stable business-key pattern",
                    "acknowledgement pattern"),
    "DESTINATION-SPECIFIC ADAPTER": ("CrewBoardSchedulingSimulator",),
    "WORKFLOW-SPECIFIC LOGIC": ("scheduling eligibility", "context fingerprint",
                                "context-change detection", "cancellation eligibility"),
    "CUSTOMER-SPECIFIC RULE": ("bounded synthetic crew skills", "duration/window policy"),
    "RELIABILITY": ("request idempotency", "authoritative version stale-state check",
                    "request acknowledgement"),
    "EXCEPTION HANDLING": ("missing skill", "invalid window", "assignment conflict"),
}
