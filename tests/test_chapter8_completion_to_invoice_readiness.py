from dataclasses import replace
from datetime import timedelta

from trades_lab.chapter7 import FieldStatus
from trades_lab.chapter8 import (ARCHITECTURE_INVENTORY, BillingMetadata,
    InvoiceReadinessService, ReadinessException, SubmissionOutcome, VALUE_MECHANISM)
from trades_lab.domain import JobState
from trades_lab.domain.states import InvoiceReadinessState
from trades_lab.fixtures.chapter8 import CUSTOMER_MAPPINGS, PARTIAL_FACTS, READY_FACTS


def test_ready_command_ack_correlation_and_no_invoice_model():
    service = InvoiceReadinessService(CUSTOMER_MAPPINGS)
    result = service.evaluate(READY_FACTS)
    assert result.readiness.status is InvoiceReadinessState.READY
    assert result.command.accounting_customer_id == "LP-CUST-410"
    assert result.acknowledgement.correlation_id == result.command.correlation_id
    assert len(service.ledgerpro.work_items) == 1
    assert not hasattr(result, "invoice") and not hasattr(service.ledgerpro, "create_invoice")


def test_exact_replay_is_same_fingerprint_and_one_work_item():
    service = InvoiceReadinessService(CUSTOMER_MAPPINGS)
    first, replay = service.evaluate(READY_FACTS), service.evaluate(READY_FACTS)
    assert first.readiness.fingerprint == replay.readiness.fingerprint
    assert replay.acknowledgement.outcome is SubmissionOutcome.IDEMPOTENT_REPLAY
    assert len(service.ledgerpro.work_items) == 1


def test_partial_is_not_ready():
    result = InvoiceReadinessService(CUSTOMER_MAPPINGS).evaluate(PARTIAL_FACTS)
    assert result.readiness.status is InvoiceReadinessState.NOT_READY
    assert result.command is None and result.readiness.checks[0].outcome.value == "FAIL"


def test_each_billing_precondition_blocks_and_identity_is_not_guessed():
    cases = [
        (replace(READY_FACTS, authoritative_job_state=JobState.IN_PROGRESS), CUSTOMER_MAPPINGS),
        (replace(READY_FACTS, materials_resolved=False), CUSTOMER_MAPPINGS),
        (replace(READY_FACTS, completion_evidence=None), CUSTOMER_MAPPINGS),
        (READY_FACTS, {}),
        (replace(READY_FACTS, billing_metadata=replace(READY_FACTS.billing_metadata,
                                                      billing_summary=None)), CUSTOMER_MAPPINGS),
    ]
    for facts, mappings in cases:
        result = InvoiceReadinessService(mappings).evaluate(facts)
        assert result.readiness.status is InvoiceReadinessState.BLOCKED
        assert result.command is None and result.readiness.blocking_checks
    identity = InvoiceReadinessService({}).evaluate(READY_FACTS)
    assert any(e.event_type == "ACCOUNTING_CUSTOMER_MAPPING_FAILED" for e in identity.events)
    assert "billing_summary" in cases[-1][0].billing_metadata.__dataclass_fields__


def test_approval_change_is_not_replay_and_allows_ready():
    service = InvoiceReadinessService(CUSTOMER_MAPPINGS)
    before = service.evaluate(replace(READY_FACTS, job_type="COMMERCIAL_CHANGE_ORDER"))
    after = service.evaluate(replace(READY_FACTS, job_type="COMMERCIAL_CHANGE_ORDER",
                                     customer_approved=True))
    assert before.readiness.status is InvoiceReadinessState.BLOCKED
    assert after.readiness.status is InvoiceReadinessState.READY
    assert before.readiness.fingerprint != after.readiness.fingerprint


def test_exception_billing_impact_is_explicit():
    blocking = ReadinessException("EX-B", "material dispute", True, True)
    note = ReadinessException("EX-N", "operational note", True, False)
    blocked = InvoiceReadinessService(CUSTOMER_MAPPINGS).evaluate(
        replace(READY_FACTS, exceptions=(blocking,)))
    allowed = InvoiceReadinessService(CUSTOMER_MAPPINGS).evaluate(
        replace(READY_FACTS, exceptions=(note,)))
    assert blocked.readiness.status is InvoiceReadinessState.BLOCKED
    assert allowed.readiness.status is InvoiceReadinessState.READY


def test_stale_completion_cannot_recreate_ready_work_item():
    facts = replace(READY_FACTS, authoritative_updated_at=READY_FACTS.authoritative_updated_at + timedelta(minutes=1),
                    authoritative_job_state=JobState.IN_PROGRESS)
    service = InvoiceReadinessService(CUSTOMER_MAPPINGS)
    result = service.evaluate(facts)
    assert result.stale_input and result.command is None and not service.ledgerpro.work_items


def test_value_and_inventory_discipline():
    assert VALUE_MECHANISM["invoice_principal"] == "NOT INCLUDED"
    categories = {category for category, _ in ARCHITECTURE_INVENTORY}
    assert {"WORKFLOW-SPECIFIC LOGIC", "CUSTOMER-SPECIFIC RULE", "SUPPORT SURFACE"} <= categories
