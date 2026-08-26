from dataclasses import FrozenInstanceError

import pytest

from trades_lab.cli import render_chapter2
from trades_lab.domain import (Customer, EstimateState, ExceptionCategory, ExceptionRecord,
                               ExceptionStatus, JobState, Provenance, SourceReference,
                               TransitionError, can_transition, validate_transition)
from trades_lab.domain.states import map_estimateworks_state, map_fieldtrack_state
from trades_lab.fixtures.chapter2 import CUSTOMER, EVENTS, OBSERVED_AT, WORKFLOW_SNAPSHOT


def test_canonical_entities_require_canonical_and_source_ids():
    source = SourceReference("RiverLead CRM", "customer-1")
    with pytest.raises(ValueError, match="canonical ID"):
        Customer("", (source,), Provenance(source, OBSERVED_AT), "Customer")
    with pytest.raises(ValueError, match="source identity"):
        Customer("customer-1", (), Provenance(source, OBSERVED_AT), "Customer")


def test_source_references_and_provenance_are_preserved():
    assert CUSTOMER.source_references[0].source_id == "rl-customer-441"
    assert CUSTOMER.provenance.source == CUSTOMER.source_references[0]
    assert len(CUSTOMER.source_references) == 2


def test_duplicate_source_references_are_rejected():
    source = SourceReference("RiverLead CRM", "customer-1")
    with pytest.raises(ValueError, match="duplicate source reference"):
        Customer("customer-1", (source, source), Provenance(source, OBSERVED_AT), "Customer")


def test_source_states_normalize_and_unknown_is_rejected():
    assert map_estimateworks_state("CUSTOMER_APPROVED") is EstimateState.ACCEPTED
    assert map_fieldtrack_state("DONE") is JobState.COMPLETED
    with pytest.raises(ValueError, match="unknown EstimateWorks source state"):
        map_estimateworks_state("CUSTOMER_REVIEW_PENDING")


def test_estimate_transition_rules():
    assert can_transition(EstimateState.SENT, EstimateState.ACCEPTED)
    with pytest.raises(TransitionError, match="not allowed"):
        validate_transition(EstimateState.DRAFT, EstimateState.ACCEPTED)


def test_job_transition_rules():
    validate_transition(JobState.BLOCKED, JobState.IN_PROGRESS)
    with pytest.raises(TransitionError, match="PENDING -> COMPLETED"):
        validate_transition(JobState.PENDING, JobState.COMPLETED)


def test_state_observations_are_immutable_and_fixtures_are_deterministic():
    assert render_chapter2() == render_chapter2()
    assert WORKFLOW_SNAPSHOT == WORKFLOW_SNAPSHOT
    with pytest.raises(FrozenInstanceError):
        WORKFLOW_SNAPSHOT[2].state = EstimateState.REJECTED


def test_event_preserves_correlation_and_source_provenance():
    event = EVENTS[0]
    assert event.correlation_id == "corr-002"
    assert (event.source_system, event.source_record_id) == ("EstimateWorks", "ew-estimate-210")


def test_exception_record_represents_state_conflict():
    record = ExceptionRecord("exception-1", ExceptionCategory.STATE_CONFLICT, "Job", "job-001", "FieldTrack", "Completion conflicts with CrewBoard state", ExceptionStatus.OPEN, OBSERVED_AT, "corr-004")
    assert record.category is ExceptionCategory.STATE_CONFLICT
    assert record.status is ExceptionStatus.OPEN
