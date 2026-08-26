from dataclasses import asdict
from datetime import timedelta

from trades_lab.chapter12 import ARCHITECTURE_INVENTORY, AttentionSeverity, HealthState, build_briefing
from trades_lab.fixtures.chapter12 import (DEGRADED_EVIDENCE, GENERATED_AT, HEALTHY_EVIDENCE)


def test_healthy_and_degraded_classification():
    assert build_briefing(HEALTHY_EVIDENCE, GENERATED_AT).health_summary.state is HealthState.HEALTHY
    assert build_briefing(DEGRADED_EVIDENCE, GENERATED_AT).health_summary.state is HealthState.DEGRADED


def test_degraded_counts_are_derived_from_source_evidence():
    briefing = build_briefing(DEGRADED_EVIDENCE, GENERATED_AT)
    assert asdict(briefing.workflow_counts) == {
        "accepted_estimates_awaiting_job": 1, "jobs_awaiting_scheduling_request": 0,
        "scheduling_review_required": 1, "unresolved_material_mappings": 2,
        "blocked_material_requirements": 0, "field_blocked_jobs": 1,
        "completed_not_invoice_ready": 1, "exhausted_deliveries": 1,
        "uncertain_deliveries": 1,
    }
    assert briefing.exception_summary.open_count == 5
    assert briefing.exception_summary.overdue_count == 2
    assert briefing.reconciliation_summary.critical_count == 3


def test_attention_is_traceable_owned_and_stably_prioritized():
    items = build_briefing(DEGRADED_EVIDENCE, GENERATED_AT).attention_items
    assert all(item.evidence_reference.startswith(("REC-", "EXC-")) for item in items)
    billing = next(item for item in items if item.evidence_reference == "EXC-014")
    assert billing.owner_role.value == "ACCOUNTING_LEAD"
    assert [item.severity for item in items] == sorted(
        (item.severity for item in items), key=lambda x: {AttentionSeverity.CRITICAL: 0,
        AttentionSeverity.WARNING: 1, AttentionSeverity.INFO: 2}[x])


def test_completion_delay_is_deterministic_and_blocked_has_no_fake_timestamp():
    healthy = build_briefing(HEALTHY_EVIDENCE, GENERATED_AT).completion_delays[0]
    blocked = build_briefing(DEGRADED_EVIDENCE, GENERATED_AT).completion_delays[0]
    assert healthy.elapsed == timedelta(hours=19)
    assert blocked.elapsed == timedelta(hours=31)
    assert blocked.invoice_ready_at is None and blocked.blocker == "ACCOUNTING_CUSTOMER_MAPPING"


def test_briefing_is_read_only_and_creates_no_invoice():
    before = repr(DEGRADED_EVIDENCE)
    briefing = build_briefing(DEGRADED_EVIDENCE, GENERATED_AT)
    assert repr(DEGRADED_EVIDENCE) == before
    assert "invoice" not in {field.lower() for field in vars(briefing)}
    assert briefing.reconciliation_summary.critical_count == DEGRADED_EVIDENCE.reconciliation.critical_count


def test_architecture_records_aggregation_and_support_surface():
    inventory = dict(ARCHITECTURE_INVENTORY)
    assert "bottleneck" in inventory["WORKFLOW-SPECIFIC LOGIC"]
    assert "threshold" in inventory["SUPPORT SURFACE"]
