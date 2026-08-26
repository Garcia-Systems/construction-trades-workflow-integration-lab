"""Read-only, deterministic reconciliation of the lab's important handoffs."""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum

from trades_lab.chapter9 import Delivery, DeliveryState, FailureCategory
from trades_lab.domain import ExceptionRecord, ExceptionStatus


class ReconciliationCategory(StrEnum):
    MISSING_HANDOFF = "MISSING_HANDOFF"
    STATE_MISMATCH = "STATE_MISMATCH"
    IDENTITY_MISMATCH = "IDENTITY_MISMATCH"
    FAILED_DELIVERY = "FAILED_DELIVERY"
    UNRESOLVED_EXCEPTION = "UNRESOLVED_EXCEPTION"
    STALE_RECORD = "STALE_RECORD"
    ORPHAN_RECORD = "ORPHAN_RECORD"


class ReconciliationSeverity(StrEnum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class RecommendedAction(StrEnum):
    NO_ACTION = "NO_ACTION"
    REVIEW = "REVIEW"
    REPLAY_CANDIDATE = "REPLAY_CANDIDATE"
    REPAIR_ACCESS = "REPAIR_ACCESS"
    RESOLVE_MAPPING = "RESOLVE_MAPPING"


@dataclass(frozen=True)
class EstimateSnapshot:
    estimate_id: str
    state: str
    external_reference: str
    correlation_id: str | None = None


@dataclass(frozen=True)
class JobSnapshot:
    job_id: str
    estimate_external_reference: str | None
    state: str
    scheduling_required: bool = True
    assignment_expected: bool = False
    material_summary_state: str | None = None
    correlation_id: str | None = None


@dataclass(frozen=True)
class ScheduleSnapshot:
    request_id: str
    job_id: str
    state: str = "UNASSIGNED"
    correlation_id: str | None = None


@dataclass(frozen=True)
class MaterialRequirementSnapshot:
    requirement_id: str
    job_id: str
    state: str
    destination_request_id: str | None = None
    correlation_id: str | None = None


@dataclass(frozen=True)
class FieldSnapshot:
    job_id: str
    state: str
    correlation_id: str | None = None


@dataclass(frozen=True)
class InvoiceReadinessSnapshot:
    job_id: str
    state: str
    blockers: tuple[str, ...] = ()
    correlation_id: str | None = None


@dataclass(frozen=True)
class ReconciliationSnapshot:
    estimates: tuple[EstimateSnapshot, ...] = ()
    jobs: tuple[JobSnapshot, ...] = ()
    schedules: tuple[ScheduleSnapshot, ...] = ()
    materials: tuple[MaterialRequirementSnapshot, ...] = ()
    field_observations: tuple[FieldSnapshot, ...] = ()
    invoice_readiness: tuple[InvoiceReadinessSnapshot, ...] = ()
    deliveries: tuple[Delivery, ...] = ()
    exceptions: tuple[ExceptionRecord, ...] = ()


@dataclass(frozen=True)
class ReconciliationItem:
    reconciliation_id: str
    category: ReconciliationCategory
    severity: ReconciliationSeverity
    entity_type: str
    entity_id: str
    summary: str
    expected_state: str | None
    observed_state: str | None
    correlation_id: str | None
    requires_review: bool
    recommended_action: RecommendedAction


@dataclass(frozen=True)
class CheckedCounts:
    accepted_estimates: int
    jobs: int
    scheduling: int
    materials: int
    completed_jobs: int
    deliveries: int
    exceptions: int


@dataclass(frozen=True)
class ReconciliationReport:
    generated_at: datetime
    systems_inspected: tuple[str, ...]
    checked_counts: CheckedCounts
    findings: tuple[ReconciliationItem, ...]
    automatic_repairs_performed: int = 0

    @property
    def critical_count(self) -> int:
        return sum(f.severity is ReconciliationSeverity.CRITICAL for f in self.findings)

    @property
    def warning_count(self) -> int:
        return sum(f.severity is ReconciliationSeverity.WARNING for f in self.findings)

    @property
    def unresolved_count(self) -> int:
        return len(self.findings)


FIXTURE_TIME = datetime(2026, 1, 10, 12, 0, tzinfo=timezone.utc)
SYSTEMS = ("EstimateWorks", "Job system", "CrewBoard", "SupplyDesk", "FieldTrack",
           "LedgerPro boundary", "Integration history", "Exception records")


class Reconciler:
    """Compare immutable snapshots.  It owns no adapter and performs no writes."""

    def reconcile(self, snapshot: ReconciliationSnapshot,
                  generated_at: datetime = FIXTURE_TIME) -> ReconciliationReport:
        raw: list[tuple] = []
        jobs_by_ref = {j.estimate_external_reference: j for j in snapshot.jobs
                       if j.estimate_external_reference}
        jobs_by_id = {j.job_id: j for j in snapshot.jobs}
        schedules = {s.job_id: s for s in snapshot.schedules}
        readiness = {r.job_id: r for r in snapshot.invoice_readiness}
        field = {f.job_id: f for f in snapshot.field_observations}

        accepted = [e for e in snapshot.estimates if e.state == "ACCEPTED"]
        for estimate in accepted:
            if estimate.external_reference not in jobs_by_ref:
                raw.append((ReconciliationCategory.MISSING_HANDOFF, ReconciliationSeverity.CRITICAL,
                            "ACCEPTED_ESTIMATE", estimate.estimate_id,
                            "Accepted estimate has no authoritative job", "authoritative job", "none",
                            estimate.correlation_id, False, RecommendedAction.REPLAY_CANDIDATE))

        eligible = [j for j in snapshot.jobs if j.scheduling_required and j.state not in {"CANCELLED", "DRAFT"}]
        for job in eligible:
            request = schedules.get(job.job_id)
            if request is None:
                raw.append((ReconciliationCategory.MISSING_HANDOFF, ReconciliationSeverity.CRITICAL,
                            "JOB", job.job_id, "Eligible job has no scheduling request",
                            "CrewBoard scheduling request", "none", job.correlation_id, False,
                            RecommendedAction.REPLAY_CANDIDATE))
            elif job.assignment_expected and request.state == "UNASSIGNED":
                raw.append((ReconciliationCategory.STATE_MISMATCH, ReconciliationSeverity.WARNING,
                            "JOB", job.job_id, "Assignment is expected but request remains unassigned",
                            "ASSIGNED", "UNASSIGNED", request.correlation_id, True, RecommendedAction.REVIEW))

        for requirement in snapshot.materials:
            if requirement.state == "REQUESTED" and not requirement.destination_request_id:
                raw.append((ReconciliationCategory.MISSING_HANDOFF, ReconciliationSeverity.CRITICAL,
                            "MATERIAL_REQUIREMENT", requirement.requirement_id,
                            "Integration state has no SupplyDesk acknowledgement", "SupplyDesk request",
                            "none", requirement.correlation_id, False, RecommendedAction.REPLAY_CANDIDATE))
            if requirement.state in {"UNRESOLVED", "BLOCKED"}:
                raw.append((ReconciliationCategory.UNRESOLVED_EXCEPTION, ReconciliationSeverity.WARNING,
                            "MATERIAL_REQUIREMENT", requirement.requirement_id,
                            "Material requirement remains unresolved", "mapped/ready requirement",
                            requirement.state, requirement.correlation_id, True,
                            RecommendedAction.RESOLVE_MAPPING))
                job = jobs_by_id.get(requirement.job_id)
                if job and job.material_summary_state == "READY":
                    raw.append((ReconciliationCategory.STATE_MISMATCH, ReconciliationSeverity.CRITICAL,
                                "JOB", job.job_id, "Job claims material readiness despite unresolved requirement",
                                "not READY", "READY", requirement.correlation_id, True,
                                RecommendedAction.REVIEW))

        completed_ids = {j.job_id for j in snapshot.jobs if j.state == "COMPLETED"} | \
                        {f.job_id for f in snapshot.field_observations if f.state == "COMPLETED"}
        for job_id in sorted(completed_ids):
            ready = readiness.get(job_id)
            corr = (field.get(job_id).correlation_id if field.get(job_id) else
                    jobs_by_id.get(job_id).correlation_id if jobs_by_id.get(job_id) else None)
            if ready is None:
                raw.append((ReconciliationCategory.MISSING_HANDOFF, ReconciliationSeverity.CRITICAL,
                            "JOB", job_id, "Completed job has no invoice-readiness evaluation",
                            "readiness evaluation", "none", corr, False,
                            RecommendedAction.REPLAY_CANDIDATE))
            elif ready.state == "BLOCKED":
                raw.append((ReconciliationCategory.UNRESOLVED_EXCEPTION, ReconciliationSeverity.WARNING,
                            "JOB", job_id, "Invoice readiness is legitimately blocked: " +
                            "; ".join(ready.blockers), "invoice-ready", "BLOCKED",
                            ready.correlation_id or corr, True,
                            RecommendedAction.RESOLVE_MAPPING if any("mapping" in b.lower() for b in ready.blockers)
                            else RecommendedAction.REVIEW))

        for delivery in snapshot.deliveries:
            if delivery.state in {DeliveryState.EXHAUSTED, DeliveryState.BLOCKED, DeliveryState.UNCERTAIN}:
                authentication = bool(delivery.exception and
                                      delivery.exception.category is FailureCategory.AUTHENTICATION)
                raw.append((ReconciliationCategory.FAILED_DELIVERY, ReconciliationSeverity.CRITICAL,
                            "DELIVERY", delivery.delivery_id,
                            "Logical delivery remains unresolved", "ACKNOWLEDGED", delivery.state.value,
                            delivery.correlation_id, True,
                            RecommendedAction.REPAIR_ACCESS if authentication else RecommendedAction.REVIEW))

        for exception in snapshot.exceptions:
            if exception.status is ExceptionStatus.OPEN:
                severity = (ReconciliationSeverity.INFO if exception.category.value == "UNSUPPORTED"
                            else ReconciliationSeverity.WARNING)
                raw.append((ReconciliationCategory.UNRESOLVED_EXCEPTION, severity,
                            exception.entity_type.upper(), exception.entity_id,
                            f"{exception.category.value}: {exception.summary} (opened {exception.created_at.isoformat()})",
                            "resolved exception", "OPEN", exception.correlation_id, True,
                            RecommendedAction.RESOLVE_MAPPING if exception.category.value == "MAPPING"
                            else RecommendedAction.REVIEW))

        for job_id in sorted(set(field) & set(jobs_by_id)):
            if jobs_by_id[job_id].state != field[job_id].state and \
                    jobs_by_id[job_id].state in {"COMPLETED", "CANCELLED"}:
                raw.append((ReconciliationCategory.STATE_MISMATCH, ReconciliationSeverity.CRITICAL,
                            "JOB", job_id, "Job and FieldTrack authoritative views disagree",
                            f"job={jobs_by_id[job_id].state}", f"field={field[job_id].state}",
                            field[job_id].correlation_id or jobs_by_id[job_id].correlation_id, True,
                            RecommendedAction.REVIEW))
        for schedule in snapshot.schedules:
            if schedule.job_id not in jobs_by_id:
                raw.append((ReconciliationCategory.ORPHAN_RECORD, ReconciliationSeverity.CRITICAL,
                            "SCHEDULE_REQUEST", schedule.request_id,
                            "CrewBoard request references a missing authoritative job",
                            "source job", "none", schedule.correlation_id, True,
                            RecommendedAction.REVIEW))

        raw.sort(key=lambda x: (x[0].value, x[3], x[4]))
        findings = tuple(ReconciliationItem(f"REC-{i:03d}", *values)
                         for i, values in enumerate(raw, 1))
        counts = CheckedCounts(len(accepted), len(snapshot.jobs), len(eligible), len(snapshot.materials),
                               len(completed_ids), len(snapshot.deliveries), len(snapshot.exceptions))
        return ReconciliationReport(generated_at, SYSTEMS, counts, findings)


ARCHITECTURE_INVENTORY = (
    ("SHARED CORE", "authoritative identity references, canonical states, correlation, history, exceptions"),
    ("WORKFLOW-SPECIFIC LOGIC", "estimate-job, job-schedule, material-readiness, completion-invoice expectations"),
    ("RELIABILITY", "logical delivery-state interpretation rather than failed-attempt counting"),
    ("SUPPORT SURFACE", "recurring reconciliation, mismatch review, stale configuration, access and mapping follow-up"),
)
