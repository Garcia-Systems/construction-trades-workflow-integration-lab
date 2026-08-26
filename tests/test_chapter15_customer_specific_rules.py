from dataclasses import replace

from trades_lab.chapter15 import *
from trades_lab.fixtures.chapter15 import *


def test_fixtures_are_deterministic():
    assert PAPER_COMPLETION == replace(PAPER_COMPLETION)


def test_signed_is_automatic_but_verbal_is_reviewed_and_cannot_authorize():
    adapter = BidForgeAdapter()
    assert adapter.acceptance_decision("SIGNED") is AcceptanceDecision.AUTOMATION_ELIGIBLE
    assert adapter.acceptance_decision("CUSTOMER_VERBAL_OK") is AcceptanceDecision.HUMAN_REVIEW
    assert not adapter.may_authorize_job("CUSTOMER_VERBAL_OK")


def test_prospective_job_stays_outside_shared_handoff():
    result = prospective_job("PROSPECTIVE_JOB")
    assert not result.enters_shared_handoff and result.approach.startswith("B_")


def test_schedule_approval_gate_blocks_then_allows_reused_boundary():
    assert schedule_gate(True, False).exception == "OPERATIONS_APPROVAL_REQUIRED"
    assert schedule_gate(True, True).request_status == "REQUESTED"


def test_kit_expands_deterministically_and_replay_does_not_duplicate():
    expander = TidewaterKitExpander({source: f"SD-{i}" for i, (source, _) in enumerate(TidewaterKitExpander.KIT_A)})
    first = expander.expand("TSS-KIT-A")
    second = expander.expand("TSS-KIT-A")
    assert first == second and len(first.lines) == len(expander.requests) == 3


def test_partial_kit_mapping_is_explicit():
    result = TidewaterKitExpander().expand("TSS-KIT-A")
    assert result.status == "PARTIALLY_READY" and result.unresolved == 1
    assert result.exception == "KIT_LINE_MAPPING_REQUIRED"


def test_manual_completion_preserves_provenance_and_rejects_incomplete():
    adapter = OfficeCompletionAdapter()
    accepted = adapter.adapt(PAPER_COMPLETION)
    assert accepted.accepted and dict(accepted.provenance)["source_document_reference"] == "PAPER-2026-0042"
    assert not adapter.adapt(replace(PAPER_COMPLETION, source_document_reference="")).accepted


def test_weak_identity_context_prevents_merge():
    assert WEAK_IDENTITY_2026.source_id == WEAK_IDENTITY_2025.source_id
    assert WEAK_IDENTITY_2026 != WEAK_IDENTITY_2025
    assert WEAK_IDENTITY_2026.canonical_key != WEAK_IDENTITY_2025.canonical_key


def test_billing_project_blocked_and_does_not_create_invoice():
    result = aggregate_billing_project("BP-100", BILLING_PROJECT_JOBS)
    assert not result.ready and result.ready_jobs == result.blocked_jobs == 1
    assert not result.invoice_created


def test_same_done_has_contextual_semantics_and_explicit_readiness_gate():
    digital = interpret_done("DIGITAL_SERVICE_CREW", "DONE")
    legacy = interpret_done("LEGACY_CREW", "DONE")
    assert digital.canonical_completed and digital.invoice_eligible
    assert not legacy.canonical_completed and not legacy.invoice_eligible


def test_classification_counts_and_support_are_deterministic():
    inventory = change_inventory()
    assert inventory["new_adapters"] == 2
    assert inventory["customer_specific_rules"] == 4
    assert inventory["shared_core_changes"] == 0
    assert inventory["support_surface_additions"] == len(SUPPORT_SURFACE) == 8
    assert inventory["unchanged_reused_units"] == 5


def test_reuse_is_separate_from_customer_rules_and_baseline_is_complete():
    assert REUSE_MATRIX["Idempotency"] == "REUSED"
    assert REUSE_MATRIX["Kit expansion"] == "CUSTOMER_SPECIFIC"
    expected = {"estimate acceptance", "job creation", "scheduling eligibility", "material mapping",
                "field completion", "invoice readiness", "identity", "reliability",
                "exception handling", "operational support"}
    assert set(BASELINE_COMPARISON) == expected


def test_inventory_never_infers_hours_and_core_changes_are_explicit():
    inventory = change_inventory()
    assert not any("hour" in key for key in inventory)
    assert CORE_IMPACT == "LOW_CORE_IMPACT" and inventory["shared_core_changes"] == 0
