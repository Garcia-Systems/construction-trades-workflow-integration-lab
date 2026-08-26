from dataclasses import fields

from trades_lab.chapter3 import (EstimateIntakeCommand, HandoffOutcome,
                                 LeadToEstimateHandoff)
from trades_lab.domain import ExceptionCategory
from trades_lab.fixtures.chapter3 import (AMBIGUOUS_IDENTITY_LEAD, INELIGIBLE_LEAD,
                                          MALFORMED_LEAD, MISSING_CONTACT_LEAD,
                                          UNKNOWN_STATE_LEAD, VALID_QUALIFIED_LEAD)


def test_valid_qualified_lead_produces_one_intentionally_bounded_command():
    handoff = LeadToEstimateHandoff()
    result = handoff.process(VALID_QUALIFIED_LEAD)
    assert result.outcome is HandoffOutcome.READY
    assert isinstance(result.command, EstimateIntakeCommand)
    assert len(handoff.commands) == 1
    assert {field.name for field in fields(result.command)} == {
        "correlation_id", "source_lead_id", "canonical_lead_id",
        "source_customer_id", "customer_name", "contact", "service_address",
        "scope_summary", "source_observed_at", "source_version",
    }
    assert not hasattr(result.command, "crm_owner")


def test_provenance_and_correlation_survive_every_success_artifact():
    result = LeadToEstimateHandoff().process(VALID_QUALIFIED_LEAD)
    normalized = result.normalized_lead
    assert normalized is not None and result.command is not None
    assert normalized.lead.provenance.source.source_id == "RL-1001"
    assert normalized.customer_reference.source_id == "RLC-501"
    assert normalized.lead.provenance.source_version == VALID_QUALIFIED_LEAD["updated_at"]
    assert normalized.lead.provenance.correlation_id == result.correlation_id
    assert result.command.correlation_id == result.correlation_id
    assert all(event.correlation_id == result.correlation_id for event in result.events)


def test_identical_replay_is_duplicate_and_does_not_emit_second_command():
    handoff = LeadToEstimateHandoff()
    first = handoff.process(VALID_QUALIFIED_LEAD)
    second = handoff.process(VALID_QUALIFIED_LEAD)
    assert (first.outcome, second.outcome) == (HandoffOutcome.READY,
                                               HandoffOutcome.DUPLICATE)
    assert second.command is None
    assert len(handoff.commands) == 1


def test_ineligible_lead_is_skipped_without_exception():
    result = LeadToEstimateHandoff().process(INELIGIBLE_LEAD)
    assert result.outcome is HandoffOutcome.SKIPPED_NOT_ELIGIBLE
    assert result.exception is None
    assert result.command is None


def test_missing_contact_produces_controlled_validation_exception():
    result = LeadToEstimateHandoff().process(MISSING_CONTACT_LEAD)
    assert result.outcome is HandoffOutcome.EXCEPTION
    assert result.exception is not None
    assert result.exception.category is ExceptionCategory.VALIDATION


def test_unknown_state_is_not_guessed():
    result = LeadToEstimateHandoff().process(UNKNOWN_STATE_LEAD)
    assert result.outcome is HandoffOutcome.EXCEPTION
    assert result.exception is not None
    assert result.exception.category is ExceptionCategory.VALIDATION
    assert "unknown RiverLead state" in result.exception.summary


def test_ambiguous_contact_is_not_automatically_merged_or_commanded():
    handoff = LeadToEstimateHandoff()
    first = handoff.process(VALID_QUALIFIED_LEAD)
    ambiguous = handoff.process(AMBIGUOUS_IDENTITY_LEAD)
    assert first.outcome is HandoffOutcome.READY
    assert ambiguous.outcome is HandoffOutcome.EXCEPTION
    assert ambiguous.exception is not None
    assert ambiguous.exception.category is ExceptionCategory.IDENTITY
    assert ambiguous.command is None
    assert len(handoff.commands) == 1
    assert ambiguous.normalized_lead.lead.canonical_id != first.normalized_lead.lead.canonical_id


def test_malformed_source_data_fails_explicitly():
    result = LeadToEstimateHandoff().process(MALFORMED_LEAD)
    assert result.outcome is HandoffOutcome.EXCEPTION
    assert result.exception is not None
    assert result.exception.category is ExceptionCategory.VALIDATION


def test_event_histories_are_deterministic_and_descriptive():
    left = LeadToEstimateHandoff().process(VALID_QUALIFIED_LEAD)
    right = LeadToEstimateHandoff().process(VALID_QUALIFIED_LEAD)
    assert left.events == right.events
    assert tuple(event.event_type for event in left.events) == (
        "LEAD_OBSERVED", "LEAD_NORMALIZED", "ESTIMATE_INTAKE_READY")
    invalid = LeadToEstimateHandoff().process(MISSING_CONTACT_LEAD)
    assert tuple(event.event_type for event in invalid.events) == (
        "LEAD_OBSERVED", "LEAD_VALIDATION_FAILED")
