from dataclasses import replace
from trades_lab.chapter10 import *
from trades_lab.chapter9 import Delivery, DeliveryState
from trades_lab.domain import ExceptionCategory, ExceptionRecord, ExceptionStatus
from trades_lab.fixtures.chapter10 import BROKEN_SNAPSHOT, CLEAN_SNAPSHOT, T


def findings(snapshot, category=None):
    result = Reconciler().reconcile(snapshot).findings
    return tuple(x for x in result if category is None or x.category is category)


def test_clean_workflow_has_no_findings():
    report = Reconciler().reconcile(CLEAN_SNAPSHOT)
    assert report.critical_count == report.warning_count == 0 and not report.findings


def test_missing_estimate_job_and_present_job_behavior():
    assert any(x.entity_id == "EW-EST-3002" for x in findings(BROKEN_SNAPSHOT, ReconciliationCategory.MISSING_HANDOFF))
    assert not any(x.entity_id == "EW-EST-3001" for x in findings(CLEAN_SNAPSHOT))


def test_schedule_missing_but_unassigned_request_is_legitimate():
    assert any(x.entity_id == "JOB-9102" for x in findings(BROKEN_SNAPSHOT, ReconciliationCategory.MISSING_HANDOFF))
    assert not any(x.entity_id == "JOB-9101" for x in findings(CLEAN_SNAPSHOT))


def test_material_ack_and_unresolved_are_detected():
    result = findings(BROKEN_SNAPSHOT)
    assert any(x.entity_id == "MAT-201" and x.category is ReconciliationCategory.MISSING_HANDOFF for x in result)
    assert any(x.entity_id == "MAT-202" and x.recommended_action is RecommendedAction.RESOLVE_MAPPING for x in result)


def test_invoice_missing_evaluation_and_legitimate_blocker():
    missing = replace(CLEAN_SNAPSHOT, invoice_readiness=())
    assert any("readiness evaluation" in x.summary for x in findings(missing))
    blocked = [x for x in findings(BROKEN_SNAPSHOT) if x.entity_id == "JOB-9103" and "legitimately blocked" in x.summary]
    assert blocked and "accounting customer mapping" in blocked[0].summary


def test_delivery_logical_state_not_historical_attempt_count():
    assert any(x.entity_id == "DEL-EXHAUSTED" for x in findings(BROKEN_SNAPSHOT, ReconciliationCategory.FAILED_DELIVERY))
    successful = Delivery("D", "E", "K", "C", {}, state=DeliveryState.ACKNOWLEDGED)
    assert not findings(ReconciliationSnapshot(deliveries=(successful,)), ReconciliationCategory.FAILED_DELIVERY)
    uncertain = replace(successful, delivery_id="U", state=DeliveryState.UNCERTAIN)
    assert findings(ReconciliationSnapshot(deliveries=(uncertain,)), ReconciliationCategory.FAILED_DELIVERY)


def test_only_open_exception_is_surfaced():
    resolved = ExceptionRecord("X", ExceptionCategory.MAPPING, "Job", "J", "S", "fixed", ExceptionStatus.RESOLVED, T, "C")
    assert findings(BROKEN_SNAPSHOT, ReconciliationCategory.UNRESOLVED_EXCEPTION)
    assert not findings(ReconciliationSnapshot(exceptions=(resolved,)), ReconciliationCategory.UNRESOLVED_EXCEPTION)


def test_state_mismatch_and_orphan_are_detected():
    result = findings(BROKEN_SNAPSHOT)
    assert any(x.category is ReconciliationCategory.STATE_MISMATCH and x.entity_id == "JOB-9104" for x in result)
    assert any(x.category is ReconciliationCategory.ORPHAN_RECORD and x.requires_review for x in result)


def test_actions_are_advisory_and_reconciliation_writes_nothing():
    before = BROKEN_SNAPSHOT
    report = Reconciler().reconcile(before)
    assert report.automatic_repairs_performed == 0
    assert BROKEN_SNAPSHOT == before
    assert all(isinstance(x.recommended_action, RecommendedAction) for x in report.findings)


def test_output_is_deterministic_and_preserves_correlation():
    one = Reconciler().reconcile(BROKEN_SNAPSHOT)
    two = Reconciler().reconcile(BROKEN_SNAPSHOT)
    assert one == two
    assert next(x for x in one.findings if x.entity_id == "EW-EST-3002").correlation_id == "corr-missing-job"


def test_architecture_inventory_classifies_new_structure():
    inventory = dict(ARCHITECTURE_INVENTORY)
    assert "estimate-job" in inventory["WORKFLOW-SPECIFIC LOGIC"]
    assert "recurring reconciliation" in inventory["SUPPORT SURFACE"]
    assert "logical delivery-state" in inventory["RELIABILITY"]
