"""A read-only management snapshot derived from existing integration evidence."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from trades_lab.chapter9 import DeliveryState
from trades_lab.chapter10 import ReconciliationReport, ReconciliationSeverity, ReconciliationSnapshot
from trades_lab.chapter11 import AgeBucket, ManagedException, OwnerRole, age_bucket
from trades_lab.domain import ExceptionStatus


class AttentionSeverity(StrEnum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class AttentionCategory(StrEnum):
    HANDOFF_DELAY = "HANDOFF_DELAY"
    SCHEDULING_BLOCKER = "SCHEDULING_BLOCKER"
    MATERIAL_BLOCKER = "MATERIAL_BLOCKER"
    FIELD_BLOCKER = "FIELD_BLOCKER"
    BILLING_READINESS_BLOCKER = "BILLING_READINESS_BLOCKER"
    DELIVERY_FAILURE = "DELIVERY_FAILURE"
    RECONCILIATION_MISMATCH = "RECONCILIATION_MISMATCH"
    EXCEPTION_AGING = "EXCEPTION_AGING"


class HealthState(StrEnum):
    HEALTHY = "HEALTHY"
    ATTENTION_REQUIRED = "ATTENTION_REQUIRED"
    DEGRADED = "DEGRADED"


@dataclass(frozen=True)
class CompletionObservation:
    job_id: str
    completed_at: datetime
    invoice_ready_at: datetime | None
    blocker: str | None = None


@dataclass(frozen=True)
class CompletionDelay:
    job_id: str
    completed_at: datetime
    invoice_ready_at: datetime | None
    elapsed: timedelta
    blocker: str | None

    @property
    def status(self) -> str:
        return "READY" if self.invoice_ready_at else "BLOCKED"


@dataclass(frozen=True)
class WorkflowCounts:
    accepted_estimates_awaiting_job: int
    jobs_awaiting_scheduling_request: int
    scheduling_review_required: int
    unresolved_material_mappings: int
    blocked_material_requirements: int
    field_blocked_jobs: int
    completed_not_invoice_ready: int
    exhausted_deliveries: int
    uncertain_deliveries: int


@dataclass(frozen=True)
class ExceptionSummary:
    open_count: int
    overdue_count: int


@dataclass(frozen=True)
class ReconciliationSummary:
    mismatch_count: int
    critical_count: int


@dataclass(frozen=True)
class HealthSummary:
    state: HealthState
    explanation: str


@dataclass(frozen=True)
class AttentionItem:
    item_id: str
    severity: AttentionSeverity
    category: AttentionCategory
    entity_type: str
    entity_id: str
    summary: str
    owner_role: OwnerRole | None
    age: timedelta | None
    evidence_reference: str
    recommended_next_action: str


@dataclass(frozen=True)
class BriefingEvidence:
    """References prior chapter artifacts; no source record is copied or mutated."""
    snapshot: ReconciliationSnapshot
    reconciliation: ReconciliationReport
    exceptions: tuple[ManagedException, ...]
    completions: tuple[CompletionObservation, ...]


@dataclass(frozen=True)
class OperationalBriefing:
    generated_at: datetime
    workflow_counts: WorkflowCounts
    attention_items: tuple[AttentionItem, ...]
    exception_summary: ExceptionSummary
    reconciliation_summary: ReconciliationSummary
    health_summary: HealthSummary
    completion_delays: tuple[CompletionDelay, ...]


def build_briefing(evidence: BriefingEvidence, generated_at: datetime) -> OperationalBriefing:
    """Aggregate existing results; notably, do not re-run reconciliation here."""
    snapshot = evidence.snapshot
    jobs_by_ref = {j.estimate_external_reference for j in snapshot.jobs if j.estimate_external_reference}
    job_ids = {j.job_id for j in snapshot.jobs}
    scheduled = {s.job_id for s in snapshot.schedules}
    counts = WorkflowCounts(
        sum(e.state == "ACCEPTED" and e.external_reference not in jobs_by_ref for e in snapshot.estimates),
        sum(j.scheduling_required and j.state not in {"DRAFT", "CANCELLED"} and j.job_id not in scheduled
            for j in snapshot.jobs),
        sum(s.state in {"REVIEW_REQUIRED", "CONFLICT", "BLOCKED"} for s in snapshot.schedules),
        sum(m.state == "UNRESOLVED" for m in snapshot.materials),
        sum(m.state == "BLOCKED" for m in snapshot.materials),
        len({f.job_id for f in snapshot.field_observations if f.state == "BLOCKED" and f.job_id in job_ids}),
        sum(r.state == "BLOCKED" for r in snapshot.invoice_readiness
            if any(c.job_id == r.job_id for c in evidence.completions)),
        sum(d.state is DeliveryState.EXHAUSTED for d in snapshot.deliveries),
        sum(d.state is DeliveryState.UNCERTAIN for d in snapshot.deliveries),
    )
    active = tuple(x for x in evidence.exceptions
                   if x.status in {ExceptionStatus.OPEN, ExceptionStatus.IN_REVIEW})
    exception_summary = ExceptionSummary(len(active), sum(
        age_bucket(x.record.created_at, generated_at) is AgeBucket.OVERDUE for x in active))
    reconciliation_summary = ReconciliationSummary(
        len(evidence.reconciliation.findings), evidence.reconciliation.critical_count)
    delays = tuple(CompletionDelay(c.job_id, c.completed_at, c.invoice_ready_at,
        (c.invoice_ready_at or generated_at) - c.completed_at, c.blocker)
        for c in sorted(evidence.completions, key=lambda x: x.job_id))

    items: list[AttentionItem] = []
    for finding in evidence.reconciliation.findings:
        severity = AttentionSeverity(finding.severity.value)
        items.append(AttentionItem(f"ATT-{finding.reconciliation_id}", severity,
            AttentionCategory.RECONCILIATION_MISMATCH, finding.entity_type, finding.entity_id,
            finding.summary, None, None, finding.reconciliation_id,
            finding.recommended_action.value))
    for exception in active:
        overdue = age_bucket(exception.record.created_at, generated_at) is AgeBucket.OVERDUE
        if overdue or exception.impact.value.startswith("BLOCKS_"):
            items.append(AttentionItem(f"ATT-{exception.record.exception_id}",
                AttentionSeverity.CRITICAL if exception.impact.value == "BLOCKS_BILLING" else AttentionSeverity.WARNING,
                AttentionCategory.EXCEPTION_AGING if overdue else AttentionCategory.BILLING_READINESS_BLOCKER,
                exception.record.entity_type, exception.record.entity_id, exception.record.summary,
                exception.owner_role, generated_at - exception.record.created_at,
                exception.record.exception_id, "Review owned exception"))
    rank = {AttentionSeverity.CRITICAL: 0, AttentionSeverity.WARNING: 1, AttentionSeverity.INFO: 2}
    items.sort(key=lambda x: (rank[x.severity], -(x.age or timedelta()).total_seconds(), x.item_id))

    # MODELED ASSUMPTION: uncertainty or a critical mismatch means DEGRADED; any other
    # actionable blocker means ATTENTION_REQUIRED. This is not an industry SLA.
    if counts.uncertain_deliveries or reconciliation_summary.critical_count:
        health = HealthSummary(HealthState.DEGRADED, "Critical reconciliation or uncertain delivery evidence exists")
    elif items or any((counts.scheduling_review_required, counts.unresolved_material_mappings,
                       counts.field_blocked_jobs, counts.completed_not_invoice_ready)):
        health = HealthSummary(HealthState.ATTENTION_REQUIRED, "Actionable warnings or blockers exist")
    else:
        health = HealthSummary(HealthState.HEALTHY, "No critical findings, overdue exceptions, or blockers")
    return OperationalBriefing(generated_at, counts, tuple(items), exception_summary,
                               reconciliation_summary, health, delays)


ARCHITECTURE_INVENTORY = (
    ("SHARED CORE", "identities, correlation, timestamps, severity and evidence references"),
    ("WORKFLOW-SPECIFIC LOGIC", "bottleneck aggregation and completion-to-readiness duration"),
    ("CONFIGURATION", "modeled health thresholds, priority ordering and inclusion rules"),
    ("SUPPORT SURFACE", "stale rules, changing priorities, owners, categories and thresholds"),
    ("TESTING", "healthy/degraded fixtures and deterministic aggregation checks"),
)
