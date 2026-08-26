from dataclasses import replace
from datetime import timedelta

from trades_lab.chapter11 import OwnerRole
from trades_lab.chapter13 import (ALLOWED_METRIC_DIMENSIONS, ARCHITECTURE_INVENTORY,
    AlertSeverity, Capability, CapabilityState, HealthStatus, LocalScheduler, RunOutcome,
    ScheduledTask, build_metric_snapshot, due_tasks, evaluate_alerts, health_report,
    lookup_runbook, structured_log, validate_startup)
from trades_lab.fixtures.chapter12 import DEGRADED_EVIDENCE
from trades_lab.fixtures.chapter13 import (CONFIG, CREDENTIALS, HEALTHY_DEPENDENCIES,
    LEDGERPRO_OUTAGE, MISSING_ESTIMATEWORKS_CREDENTIALS, NOW, SCHEDULE, SUPPLYDESK_OUTAGE)


def state(report, capability):
    return next(x.state for x in report.capabilities if x.capability is capability)


def test_valid_runtime_configuration_and_healthy_dependencies_are_ready():
    assert validate_startup(CONFIG, CREDENTIALS).state.value == "READY"
    report = health_report(CONFIG, CREDENTIALS, HEALTHY_DEPENDENCIES)
    assert report.liveness is report.readiness is HealthStatus.HEALTHY
    assert all(x.state is CapabilityState.AVAILABLE for x in report.capabilities)


def test_missing_critical_configuration_is_explicit():
    result = validate_startup(replace(CONFIG, retry_limit=0, mapping_configuration_loaded=False), CREDENTIALS)
    assert result.state.value == "FAILED"
    assert "retry_limit" in " ".join(result.diagnostics)
    assert "mapping" in " ".join(result.diagnostics)


def test_missing_credential_affects_readiness_and_capability():
    report = health_report(CONFIG, MISSING_ESTIMATEWORKS_CREDENTIALS, HEALTHY_DEPENDENCIES)
    assert report.readiness is HealthStatus.DEGRADED
    assert state(report, Capability.LEAD_TO_ESTIMATE) is CapabilityState.UNAVAILABLE
    assert "estimateworks-api" in " ".join(validate_startup(CONFIG, MISSING_ESTIMATEWORKS_CREDENTIALS).diagnostics)


def test_secret_is_never_emitted_but_safe_reference_remains():
    secret = "super-sensitive-synthetic-value"
    output = structured_log(NOW, "INFO", "CHECK", correlation_id="corr-1",
        context={"credential_reference": "estimateworks-api", "password": secret,
                 "access_token": secret, "ordinary": "safe"}).to_json()
    assert secret not in output
    assert "estimateworks-api" in output and "corr-1" in output


def test_supplydesk_outage_degrades_only_dependent_capabilities():
    report = health_report(CONFIG, CREDENTIALS, SUPPLYDESK_OUTAGE)
    assert report.liveness is HealthStatus.HEALTHY and report.readiness is HealthStatus.DEGRADED
    assert state(report, Capability.MATERIAL_HANDOFF) is CapabilityState.UNAVAILABLE
    assert state(report, Capability.ESTIMATE_TO_JOB) is CapabilityState.AVAILABLE
    assert state(report, Capability.JOB_TO_SCHEDULE) is CapabilityState.AVAILABLE
    assert state(report, Capability.FIELD_STATUS) is CapabilityState.AVAILABLE


def test_ledgerpro_outage_affects_invoice_readiness_not_earlier_workflows():
    report = health_report(CONFIG, CREDENTIALS, LEDGERPRO_OUTAGE)
    assert state(report, Capability.INVOICE_READINESS) is CapabilityState.UNAVAILABLE
    assert state(report, Capability.ESTIMATE_TO_JOB) is CapabilityState.AVAILABLE


def test_liveness_is_distinct_from_readiness():
    report = health_report(CONFIG, CREDENTIALS, SUPPLYDESK_OUTAGE)
    assert report.liveness is HealthStatus.HEALTHY and report.readiness is HealthStatus.DEGRADED


def test_metrics_derive_existing_evidence_and_dimensions_are_bounded():
    snapshot = build_metric_snapshot(DEGRADED_EVIDENCE, NOW)
    assert snapshot.value("uncertain_deliveries") == 1
    assert snapshot.value("exhausted_deliveries") == 1
    assert snapshot.value("open_exceptions") == 5
    assert snapshot.value("completed_not_invoice_ready") == 1
    assert ALLOWED_METRIC_DIMENSIONS == {"workflow", "outcome", "failure_category"}
    assert all(set(dict(m.dimensions)) <= ALLOWED_METRIC_DIMENSIONS for m in snapshot.metrics)


def test_uncertain_and_overdue_alerts_retain_evidence_and_owners():
    metrics = build_metric_snapshot(DEGRADED_EVIDENCE, NOW)
    alerts = evaluate_alerts(metrics, uncertain_evidence=("DEL-104",),
        overdue_evidence=(("EXC-015", OwnerRole.OPERATIONS_MANAGER),))
    uncertain = next(x for x in alerts if x.category == "UNCERTAIN_WRITE")
    overdue = next(x for x in alerts if x.category == "EXCEPTION_AGING")
    assert uncertain.severity is AlertSeverity.CRITICAL and uncertain.evidence_reference == "DEL-104"
    assert "RECONCILE" in uncertain.recommended_action and "BLINDLY REPLAY" in uncertain.recommended_action
    assert overdue.severity is AlertSeverity.WARNING and overdue.evidence_reference == "EXC-015"
    assert overdue.owner is OwnerRole.OPERATIONS_MANAGER


def test_schedule_is_due_run_is_recorded_and_overlap_is_skipped():
    assert due_tasks(SCHEDULE, NOW) == (ScheduledTask.RECONCILIATION,)
    scheduler = LocalScheduler()
    first = scheduler.begin(ScheduledTask.RECONCILIATION, NOW)
    second = scheduler.begin(ScheduledTask.RECONCILIATION, NOW)
    assert first.outcome is RunOutcome.RUNNING and second.outcome is RunOutcome.SKIPPED_ALREADY_RUNNING
    done = scheduler.finish(first, NOW + timedelta(minutes=1), "RECON-REPORT-013")
    assert done.outcome is RunOutcome.SUCCESS and done.evidence_reference == "RECON-REPORT-013"
    assert len(scheduler.runs) == 2


def test_runbooks_encode_safe_action_and_ownership():
    uncertain = lookup_runbook("UNCERTAIN_WRITE")
    authentication = lookup_runbook("AUTHENTICATION")
    assert uncertain.safe_first_action == "RECONCILE DESTINATION STATE"
    assert "BLINDLY REPLAY" in uncertain.action_not_to_take
    assert authentication.owner is OwnerRole.INTEGRATION_SUPPORT


def test_runtime_has_no_authoritative_business_write_and_inventory_classifies_work():
    scheduler = LocalScheduler()
    assert not hasattr(scheduler, "write_business_state")
    categories = {x[0] for x in ARCHITECTURE_INVENTORY}
    assert {"POTENTIAL REUSABLE PLATFORM/CORE", "DESTINATION-SPECIFIC", "WORKFLOW-SPECIFIC",
            "CUSTOMER-SPECIFIC CONFIGURATION", "SUPPORT SURFACE"} <= categories
    support = next(text for category, text in ARCHITECTURE_INVENTORY if category == "SUPPORT SURFACE")
    assert all(term in support for term in ("credential", "outages", "mapping", "exception", "scheduler", "runbook"))
