from dataclasses import fields
from decimal import Decimal

from trades_lab.chapter6 import (ARCHITECTURE_INVENTORY, MaterialHandoffOutcome,
                                 MaterialReadiness, MaterialsHandoff, MaterialUnit)
from trades_lab.domain import ExceptionCategory
from trades_lab.fixtures.chapter6 import (AMBIGUOUS_REQUIREMENT,
    CHANGED_CONVERSION_REQUIREMENT, CONVERSION_REQUIREMENT, DIRECT_REQUIREMENT,
    PARTIAL_REQUIREMENTS, REGISTRY, SUBSTITUTE_REQUIREMENT, UNKNOWN_REQUIREMENT,
    UNIT_MISMATCH_REQUIREMENT)


def test_direct_mapping_produces_narrow_correct_acknowledged_command():
    handoff = MaterialsHandoff(REGISTRY)
    result = handoff.process(DIRECT_REQUIREMENT)
    assert result.outcome is MaterialHandoffOutcome.REQUESTED
    assert result.command.destination_material_id == "SD-HVAC-30017"
    assert result.command.quantity == Decimal("1")
    assert result.command.unit is MaterialUnit.EACH
    assert result.acknowledgement.request_id == "SD-REQ-0001"
    assert result.acknowledgement.correlation_id == result.command.correlation_id
    assert len(handoff.commands) == len(handoff.destination.requests) == 1
    assert {f.name for f in fields(result.command)} == {
        "correlation_id", "idempotency_key", "authoritative_job_id", "requirement_id",
        "requirement_version", "destination_material_id", "quantity", "unit",
        "required_by", "provenance"}


def test_exact_replay_does_not_duplicate_destination_request():
    handoff = MaterialsHandoff(REGISTRY)
    first = handoff.process(DIRECT_REQUIREMENT)
    replay = handoff.process(DIRECT_REQUIREMENT)
    assert replay.outcome is MaterialHandoffOutcome.IDEMPOTENT_REPLAY
    assert replay.acknowledgement.request_id == first.acknowledgement.request_id
    assert replay.acknowledgement.created is False
    assert len(handoff.destination.requests) == len(handoff.commands) == 1


def test_approved_conversion_is_explicit_and_deterministic():
    first = MaterialsHandoff(REGISTRY).process(CONVERSION_REQUIREMENT)
    second = MaterialsHandoff(REGISTRY).process(CONVERSION_REQUIREMENT)
    assert first.outcome is MaterialHandoffOutcome.REQUESTED
    assert first.command.quantity == second.command.quantity == Decimal("0.40")
    assert first.command.unit is second.command.unit is MaterialUnit.ROLL
    converted = next(e for e in first.events if e.event_type == "MATERIAL_UNIT_CONVERTED")
    assert dict(converted.metadata)["rule_id"] == "FEET-TO-100FT-ROLL"


def test_unknown_identifier_is_mapping_exception_and_never_guessed():
    result = MaterialsHandoff(REGISTRY).process(UNKNOWN_REQUIREMENT)
    assert result.outcome is MaterialHandoffOutcome.EXCEPTION
    assert result.exception.category is ExceptionCategory.MAPPING
    assert result.mapping is result.command is result.acknowledgement is None


def test_unit_mismatch_without_rule_is_rejected():
    handoff = MaterialsHandoff(REGISTRY)
    result = handoff.process(UNIT_MISMATCH_REQUIREMENT)
    assert result.outcome is MaterialHandoffOutcome.EXCEPTION
    assert result.exception.category is ExceptionCategory.VALIDATION
    assert result.command is None and not handoff.destination.requests


def test_ambiguous_mapping_stops_without_arbitrary_destination():
    result = MaterialsHandoff(REGISTRY).process(AMBIGUOUS_REQUIREMENT)
    assert result.outcome is MaterialHandoffOutcome.EXCEPTION
    assert result.exception.category is ExceptionCategory.MAPPING
    assert result.mapping is result.command is None


def test_substitution_suggestion_requires_human_review():
    result = MaterialsHandoff(REGISTRY).process(SUBSTITUTE_REQUIREMENT)
    assert result.outcome is MaterialHandoffOutcome.REVIEW_REQUIRED
    assert result.command is None
    assert "MATERIAL_SUBSTITUTION_REVIEW_REQUIRED" in [e.event_type for e in result.events]


def test_partial_readiness_preserves_valid_and_exposes_unresolved_requirements():
    handoff = MaterialsHandoff(REGISTRY)
    summary = handoff.process_job(PARTIAL_REQUIREMENTS)
    assert summary.readiness is MaterialReadiness.PARTIALLY_READY
    assert (summary.requirement_count, summary.ready_count, summary.exception_count) == (4, 2, 2)
    assert len(handoff.destination.requests) == 2
    assert {r.requirement.requirement_id for r in summary.results if r.exception} == {"MR-003", "MR-004"}


def test_changed_quantity_is_linked_update_and_preserves_previous_provenance():
    handoff = MaterialsHandoff(REGISTRY)
    first = handoff.process(CONVERSION_REQUIREMENT)
    changed = handoff.process(CHANGED_CONVERSION_REQUIREMENT)
    assert changed.outcome is MaterialHandoffOutcome.UPDATED_REQUIREMENT
    assert changed.command.idempotency_key != first.command.idempotency_key
    assert handoff.destination.requests[-1].previous_request_id == first.acknowledgement.request_id
    assert handoff.destination.requests[0].command.provenance == CONVERSION_REQUIREMENT.provenance
    assert len(handoff.destination.requests) == 2


def test_correlation_survives_command_acknowledgement_and_events():
    result = MaterialsHandoff(REGISTRY).process(DIRECT_REQUIREMENT)
    correlation = DIRECT_REQUIREMENT.provenance.correlation_id
    assert result.command.correlation_id == result.acknowledgement.correlation_id == correlation
    assert all(e.correlation_id == correlation for e in result.events)


def test_mapping_mechanism_and_customer_content_are_separately_classified():
    customer_mapping = next(m for m in REGISTRY.mappings
                            if m.source_material_id == "JRM-COND-3T-16S")
    assert customer_mapping.classification == "CUSTOMER-SPECIFIC RULE"
    assert "material normalization" in ARCHITECTURE_INVENTORY["WORKFLOW-SPECIFIC LOGIC"]
    assert "mapping content" in ARCHITECTURE_INVENTORY["CONFIGURATION"]
    assert "retired products" in ARCHITECTURE_INVENTORY["SUPPORT SURFACE"]
