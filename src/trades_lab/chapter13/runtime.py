"""Deterministic production-operability structures around the lab workflows.

Nothing here deploys, probes a network, or changes an authoritative business system.
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from enum import StrEnum
import json
from typing import Mapping

from trades_lab.chapter9 import DeliveryState
from trades_lab.chapter11 import OwnerRole
from trades_lab.chapter12 import BriefingEvidence, build_briefing


class Environment(StrEnum):
    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION_LIKE = "production-like"


@dataclass(frozen=True)
class CredentialReference:
    name: str
    provider: str = "environment"


@dataclass(frozen=True)
class IntegrationRuntimeConfig:
    environment: str
    service_name: str
    reconciliation_enabled: bool
    reconciliation_interval_minutes: int
    retry_limit: int
    briefing_enabled: bool
    configured_adapters: tuple[str, ...]
    credential_references: tuple[CredentialReference, ...]
    mapping_configuration_loaded: bool = True


REQUIRED_ADAPTERS = ("EstimateWorks", "Job system", "CrewBoard", "SupplyDesk", "FieldTrack", "LedgerPro")


def fixture_config() -> IntegrationRuntimeConfig:
    return IntegrationRuntimeConfig(Environment.PRODUCTION_LIKE, "trades-integration", True, 60, 3, True,
        REQUIRED_ADAPTERS, tuple(CredentialReference(x.lower().replace(" ", "-") + "-api") for x in REQUIRED_ADAPTERS))


def load_runtime_config(values: Mapping[str, str]) -> IntegrationRuntimeConfig:
    """Load only an explicit mapping, so tests never inherit the caller's shell."""
    base = fixture_config()
    return IntegrationRuntimeConfig(values.get("ENVIRONMENT", base.environment),
        values.get("SERVICE_NAME", base.service_name), values.get("RECONCILIATION_ENABLED", "true").lower() == "true",
        int(values.get("RECONCILIATION_INTERVAL_MINUTES", base.reconciliation_interval_minutes)),
        int(values.get("RETRY_LIMIT", base.retry_limit)), values.get("BRIEFING_ENABLED", "true").lower() == "true",
        base.configured_adapters, base.credential_references, values.get("MAPPINGS_LOADED", "true").lower() == "true")


class StartupState(StrEnum): READY = "READY"; DEGRADED = "DEGRADED"; FAILED = "FAILED"
class HealthStatus(StrEnum): HEALTHY = "HEALTHY"; DEGRADED = "DEGRADED"; UNHEALTHY = "UNHEALTHY"
class CapabilityState(StrEnum): AVAILABLE = "AVAILABLE"; DEGRADED = "DEGRADED"; UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True)
class StartupStatus:
    state: StartupState
    diagnostics: tuple[str, ...]


def validate_startup(config: IntegrationRuntimeConfig, available_credentials: frozenset[str]) -> StartupStatus:
    errors = []
    if config.environment not in set(Environment): errors.append(f"unsupported environment: {config.environment}")
    if not config.service_name.strip(): errors.append("service_name is required")
    if config.retry_limit < 1: errors.append("retry_limit must be at least 1")
    if config.reconciliation_enabled and config.reconciliation_interval_minutes < 1: errors.append("reconciliation interval must be positive")
    missing_adapters = sorted(set(REQUIRED_ADAPTERS) - set(config.configured_adapters))
    if missing_adapters: errors.append("missing required adapters: " + ", ".join(missing_adapters))
    if not config.mapping_configuration_loaded: errors.append("required mapping configuration is not loaded")
    missing_credentials = sorted(r.name for r in config.credential_references if r.name not in available_credentials)
    if missing_credentials: errors.append("unresolvable credential references: " + ", ".join(missing_credentials))
    return StartupStatus(StartupState.READY if not errors else StartupState.FAILED, tuple(errors))


@dataclass(frozen=True)
class DependencyHealth:
    name: str
    status: HealthStatus
    diagnostic: str = ""


class Capability(StrEnum):
    LEAD_TO_ESTIMATE="LEAD_TO_ESTIMATE"; ESTIMATE_TO_JOB="ESTIMATE_TO_JOB"; JOB_TO_SCHEDULE="JOB_TO_SCHEDULE"
    MATERIAL_HANDOFF="MATERIAL_HANDOFF"; FIELD_STATUS="FIELD_STATUS"; INVOICE_READINESS="INVOICE_READINESS"
    RECONCILIATION="RECONCILIATION"; OPERATIONAL_BRIEFING="OPERATIONAL_BRIEFING"


CAPABILITY_DEPENDENCIES = {
    Capability.LEAD_TO_ESTIMATE: ("EstimateWorks",), Capability.ESTIMATE_TO_JOB: ("EstimateWorks", "Job system"),
    Capability.JOB_TO_SCHEDULE: ("Job system", "CrewBoard"), Capability.MATERIAL_HANDOFF: ("Job system", "SupplyDesk"),
    Capability.FIELD_STATUS: ("FieldTrack", "Job system"), Capability.INVOICE_READINESS: ("FieldTrack", "LedgerPro"),
    Capability.RECONCILIATION: REQUIRED_ADAPTERS, Capability.OPERATIONAL_BRIEFING: (),
}


@dataclass(frozen=True)
class CapabilityHealth:
    capability: Capability
    state: CapabilityState
    unavailable_dependencies: tuple[str, ...] = ()


@dataclass(frozen=True)
class HealthReport:
    liveness: HealthStatus
    readiness: HealthStatus
    dependencies: tuple[DependencyHealth, ...]
    capabilities: tuple[CapabilityHealth, ...]


def health_report(config: IntegrationRuntimeConfig, credentials: frozenset[str], dependencies: tuple[DependencyHealth, ...], *, process_running: bool=True) -> HealthReport:
    startup = validate_startup(config, credentials)
    by_name = {d.name: d for d in dependencies}
    capabilities = []
    for capability, required in CAPABILITY_DEPENDENCIES.items():
        unavailable = tuple(x for x in required if x not in by_name or by_name[x].status is HealthStatus.UNHEALTHY)
        degraded = tuple(x for x in required if x in by_name and by_name[x].status is HealthStatus.DEGRADED)
        enabled = not ((capability is Capability.RECONCILIATION and not config.reconciliation_enabled) or
                       (capability is Capability.OPERATIONAL_BRIEFING and not config.briefing_enabled))
        state = CapabilityState.UNAVAILABLE if unavailable or not enabled else CapabilityState.DEGRADED if degraded else CapabilityState.AVAILABLE
        capabilities.append(CapabilityHealth(capability, state, unavailable))
    if startup.state is StartupState.FAILED:
        # Missing credentials only disable capabilities touching their named adapter.
        missing = {r.name for r in config.credential_references if r.name not in credentials}
        capabilities = [CapabilityHealth(c.capability, CapabilityState.UNAVAILABLE,
            c.unavailable_dependencies + tuple(a for a in CAPABILITY_DEPENDENCIES[c.capability]
                if a.lower().replace(" ", "-") + "-api" in missing)) if any(
                a.lower().replace(" ", "-") + "-api" in missing for a in CAPABILITY_DEPENDENCIES[c.capability]) else c for c in capabilities]
    unavailable_count = sum(c.state is CapabilityState.UNAVAILABLE for c in capabilities)
    readiness = HealthStatus.UNHEALTHY if startup.state is StartupState.FAILED and unavailable_count == len(capabilities) else (HealthStatus.DEGRADED if startup.state is StartupState.FAILED or unavailable_count or any(c.state is CapabilityState.DEGRADED for c in capabilities) else HealthStatus.HEALTHY)
    return HealthReport(HealthStatus.HEALTHY if process_running else HealthStatus.UNHEALTHY, readiness, dependencies, tuple(capabilities))


def healthy_dependencies() -> tuple[DependencyHealth, ...]:
    return tuple(DependencyHealth(x, HealthStatus.HEALTHY) for x in REQUIRED_ADAPTERS)


SENSITIVE_KEYS = frozenset({"secret", "password", "token", "api_key", "credential_value", "authorization"})


@dataclass(frozen=True)
class StructuredLogRecord:
    timestamp: datetime
    level: str
    event: str
    correlation_id: str | None = None
    entity_id: str | None = None
    attempt: int | None = None
    exception_reference: str | None = None
    context: Mapping[str, object] = field(default_factory=dict)

    def to_json(self) -> str:
        value = asdict(self); value["timestamp"] = self.timestamp.isoformat()
        return json.dumps(value, sort_keys=True)


def structured_log(timestamp: datetime, level: str, event: str, *, context: Mapping[str, object] | None=None, **fields: object) -> StructuredLogRecord:
    safe = {k: ("[REDACTED]" if k.lower() in SENSITIVE_KEYS or any(word in k.lower() for word in ("secret", "password", "token")) else v) for k, v in (context or {}).items()}
    allowed = {k: v for k, v in fields.items() if k in {"correlation_id", "entity_id", "attempt", "exception_reference"}}
    return StructuredLogRecord(timestamp, level, event, context=safe, **allowed)


@dataclass(frozen=True)
class Metric:
    name: str
    value: int
    dimensions: tuple[tuple[str, str], ...] = ()

@dataclass(frozen=True)
class MetricSnapshot:
    generated_at: datetime
    metrics: tuple[Metric, ...]

    def value(self, name: str) -> int: return next(m.value for m in self.metrics if m.name == name)


def build_metric_snapshot(evidence: BriefingEvidence, generated_at: datetime) -> MetricSnapshot:
    briefing = build_briefing(evidence, generated_at); deliveries = evidence.snapshot.deliveries
    attempts = sum(len(d.attempts) for d in deliveries)
    metrics = (Metric("handoff_attempts_total", attempts), Metric("handoff_failures_total", sum(any(a.outcome.value != "SUCCESS" for a in d.attempts) for d in deliveries)),
        Metric("retry_attempts_total", sum(max(0, len(d.attempts)-1) for d in deliveries)), Metric("uncertain_deliveries", briefing.workflow_counts.uncertain_deliveries),
        Metric("exhausted_deliveries", briefing.workflow_counts.exhausted_deliveries), Metric("open_exceptions", briefing.exception_summary.open_count),
        Metric("overdue_exceptions", briefing.exception_summary.overdue_count), Metric("reconciliation_critical_findings", briefing.reconciliation_summary.critical_count),
        Metric("completed_not_invoice_ready", briefing.workflow_counts.completed_not_invoice_ready))
    return MetricSnapshot(generated_at, metrics)


ALLOWED_METRIC_DIMENSIONS = frozenset({"workflow", "outcome", "failure_category"})


class AlertSeverity(StrEnum): CRITICAL="CRITICAL"; WARNING="WARNING"
@dataclass(frozen=True)
class OperationalAlert:
    alert_id: str; severity: AlertSeverity; category: str; summary: str; evidence_reference: str | None; recommended_action: str; owner: OwnerRole

@dataclass(frozen=True)
class AlertThresholds:
    overdue_exceptions: int = 0 # MODELED ASSUMPTION
    completed_not_ready: int = 0 # MODELED ASSUMPTION


def evaluate_alerts(metrics: MetricSnapshot, *, uncertain_evidence: tuple[str, ...]=(), overdue_evidence: tuple[tuple[str, OwnerRole], ...]=(), unavailable_dependencies: tuple[str, ...]=(), thresholds: AlertThresholds=AlertThresholds()) -> tuple[OperationalAlert, ...]:
    alerts=[]
    for ref in uncertain_evidence:
        alerts.append(OperationalAlert(f"ALERT-UNCERTAIN-{ref}", AlertSeverity.CRITICAL, "UNCERTAIN_WRITE", "Consequential write outcome is uncertain", ref, "RECONCILE DESTINATION STATE; DO NOT BLINDLY REPLAY", OwnerRole.INTEGRATION_SUPPORT))
    if metrics.value("reconciliation_critical_findings"):
        alerts.append(OperationalAlert("ALERT-RECONCILIATION", AlertSeverity.CRITICAL, "RECONCILIATION", "Critical reconciliation findings exist", "RECONCILIATION-REPORT", "INSPECT AUTHORITATIVE STATE", OwnerRole.OPERATIONS_MANAGER))
    for dep in unavailable_dependencies:
        alerts.append(OperationalAlert(f"ALERT-DEPENDENCY-{dep.upper()}", AlertSeverity.CRITICAL, "DEPENDENCY_OUTAGE", f"Required dependency unavailable: {dep}", dep, "CHECK DEPENDENCY STATUS AND DEGRADE AFFECTED CAPABILITIES", OwnerRole.INTEGRATION_SUPPORT))
    if metrics.value("overdue_exceptions") > thresholds.overdue_exceptions:
        ref, owner = overdue_evidence[0] if overdue_evidence else ("EXCEPTION-QUEUE", OwnerRole.OPERATIONS_MANAGER)
        alerts.append(OperationalAlert("ALERT-OVERDUE-EXCEPTIONS", AlertSeverity.WARNING, "EXCEPTION_AGING", "Overdue exceptions exceed modeled threshold", ref, "REVIEW OWNED EXCEPTION QUEUE", owner))
    if metrics.value("exhausted_deliveries"):
        alerts.append(OperationalAlert("ALERT-RETRY-EXHAUSTION", AlertSeverity.WARNING, "RETRY_EXHAUSTION", "Retry exhaustion exists", "DELIVERY-HISTORY", "INSPECT FAILURE BEFORE APPROVING REPLAY", OwnerRole.INTEGRATION_SUPPORT))
    if metrics.value("completed_not_invoice_ready") > thresholds.completed_not_ready:
        alerts.append(OperationalAlert("ALERT-INVOICE-READINESS", AlertSeverity.WARNING, "INVOICE_READINESS", "Completed-not-ready count exceeds modeled threshold", "BRIEFING", "REVIEW READINESS BLOCKERS", OwnerRole.ACCOUNTING_LEAD))
    rank={AlertSeverity.CRITICAL:0, AlertSeverity.WARNING:1}; return tuple(sorted(alerts, key=lambda a:(rank[a.severity], a.alert_id)))


class ScheduledTask(StrEnum): RECONCILIATION="RECONCILIATION"; OPERATIONAL_BRIEFING="OPERATIONAL_BRIEFING"; EXCEPTION_AGING="EXCEPTION_AGING"
class RunOutcome(StrEnum): RUNNING="RUNNING"; SUCCESS="SUCCESS"; SKIPPED_ALREADY_RUNNING="SKIPPED_ALREADY_RUNNING"; FAILED="FAILED"
@dataclass(frozen=True)
class ScheduleEntry:
    task: ScheduledTask; interval: timedelta; last_started_at: datetime | None
@dataclass(frozen=True)
class ScheduledRun:
    run_id: str; task: ScheduledTask; started_at: datetime; finished_at: datetime | None; outcome: RunOutcome; evidence_reference: str | None = None

def due_tasks(schedule: tuple[ScheduleEntry, ...], now: datetime) -> tuple[ScheduledTask, ...]:
    return tuple(x.task for x in schedule if x.last_started_at is None or now-x.last_started_at >= x.interval)

class LocalScheduler:
    """Process-local overlap guard; multi-instance operation needs stronger coordination."""
    def __init__(self): self._active:set[ScheduledTask]=set(); self.runs:list[ScheduledRun]=[]
    def begin(self, task: ScheduledTask, now: datetime) -> ScheduledRun:
        run_id=f"RUN-{len(self.runs)+1:03d}"
        outcome=RunOutcome.SKIPPED_ALREADY_RUNNING if task in self._active else RunOutcome.RUNNING
        if outcome is RunOutcome.RUNNING: self._active.add(task)
        run=ScheduledRun(run_id, task, now, now if outcome is RunOutcome.SKIPPED_ALREADY_RUNNING else None, outcome)
        self.runs.append(run); return run
    def finish(self, run: ScheduledRun, now: datetime, evidence_reference: str) -> ScheduledRun:
        if run.outcome is not RunOutcome.RUNNING: return run
        completed=ScheduledRun(run.run_id, run.task, run.started_at, now, RunOutcome.SUCCESS, evidence_reference)
        self._active.discard(run.task); self.runs[self.runs.index(run)]=completed; return completed


@dataclass(frozen=True)
class RecoveryRunbook:
    category: str; symptom: str; evidence_to_inspect: tuple[str, ...]; safe_first_action: str; action_not_to_take: str; owner: OwnerRole

RUNBOOKS = {
 "AUTHENTICATION": RecoveryRunbook("AUTHENTICATION", "Authentication failures block a destination", ("credential reference", "delivery history"), "VERIFY CREDENTIAL REFERENCE AND ROTATION STATUS", "DO NOT LOG OR SHARE SECRET VALUES", OwnerRole.INTEGRATION_SUPPORT),
 "UNCERTAIN_WRITE": RecoveryRunbook("UNCERTAIN_WRITE", "Consequential write lacks acknowledgement", ("delivery history", "destination lookup capability"), "RECONCILE DESTINATION STATE", "DO NOT BLINDLY REPLAY CONSEQUENTIAL CREATE", OwnerRole.INTEGRATION_SUPPORT),
 "RETRY_EXHAUSTION": RecoveryRunbook("RETRY_EXHAUSTION", "Bounded attempts exhausted", ("attempt history", "failure category"), "CONFIRM FAILURE CATEGORY AND CURRENT DESTINATION STATE", "DO NOT RESET ATTEMPT HISTORY", OwnerRole.INTEGRATION_SUPPORT),
 "MATERIAL_MAPPING": RecoveryRunbook("MATERIAL_MAPPING", "Material identity cannot map safely", ("mapping registry", "source requirement"), "OBTAIN APPROVED EXACT MAPPING", "DO NOT GUESS OR AUTO-SUBSTITUTE", OwnerRole.OPERATIONS_MANAGER),
 "CRITICAL_RECONCILIATION": RecoveryRunbook("CRITICAL_RECONCILIATION", "Authoritative states conflict", ("reconciliation finding", "source snapshots"), "COMPARE AUTHORITATIVE RECORDS", "DO NOT AUTO-REPAIR BUSINESS STATE", OwnerRole.OPERATIONS_MANAGER),
 "DEPENDENCY_OUTAGE": RecoveryRunbook("DEPENDENCY_OUTAGE", "Required dependency is unavailable", ("dependency health", "affected capabilities"), "DEGRADE AFFECTED CAPABILITIES AND MONITOR", "DO NOT DISABLE UNRELATED WORKFLOWS", OwnerRole.INTEGRATION_SUPPORT),
}
def lookup_runbook(category: str) -> RecoveryRunbook: return RUNBOOKS[category]

ARCHITECTURE_INVENTORY = (
 ("POTENTIAL REUSABLE PLATFORM/CORE", "configuration loading, startup validation, health, redacted logs, metrics, alerts, scheduler/run records, and runbook schema"),
 ("DESTINATION-SPECIFIC", "dependency probes, authentication semantics, and vendor failure interpretation"),
 ("WORKFLOW-SPECIFIC", "capability dependency graph and workflow alert conditions"),
 ("CUSTOMER-SPECIFIC CONFIGURATION", "thresholds, intervals, enabled workflows, and owner roles"),
 ("SUPPORT SURFACE", "credential rotation, vendor outages, mapping drift, alert tuning, reconciliation findings, exception queue, scheduler failures, observability maintenance, and runbook updates"),
)
