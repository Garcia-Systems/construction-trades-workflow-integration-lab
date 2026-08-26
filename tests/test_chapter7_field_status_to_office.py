import pytest

from trades_lab.chapter7 import (ARCHITECTURE_INVENTORY, BlockedReason, FieldStatus,
                                 FieldStatusHandoff, FieldStatusOutcome, FieldTrackAdapter)
from trades_lab.fixtures.chapter7 import CREW_MAPPINGS, JOB_MAPPINGS, event


@pytest.mark.parametrize(("source", "canonical"), [
    ("EN_ROUTE", FieldStatus.DISPATCHED), ("ONSITE", FieldStatus.ARRIVED),
    ("WORKING", FieldStatus.IN_PROGRESS), ("HOLD", FieldStatus.BLOCKED),
    ("PARTIAL", FieldStatus.PARTIALLY_COMPLETE), ("DONE", FieldStatus.COMPLETED),
])
def test_bounded_status_mapping(source, canonical):
    assert FieldTrackAdapter().normalize(source) is canonical


def test_unknown_status_is_a_controlled_mapping_exception():
    result = engine().process(event("FT-UNKNOWN", "TELEPORTED", 1))
    assert result.outcome is FieldStatusOutcome.EXCEPTION
    assert result.exception.category.value == "MAPPING"
    assert result.office_update is None
    assert "FIELD_STATUS_MAPPING_FAILED" in types(result)


def test_blocked_reason_and_resume_are_preserved_and_accepted():
    handoff = engine()
    blocked = handoff.process(event("FT-BLOCK", "HOLD", 4, "MATERIAL_MISSING"))
    resumed = handoff.process(event("FT-RESUME", "WORKING", 5))
    assert blocked.office_update.blocked_reason is BlockedReason.MATERIAL_MISSING
    assert resumed.outcome is FieldStatusOutcome.APPLIED
    assert handoff.current_status["JOB-9001"] is FieldStatus.IN_PROGRESS
    assert "OFFICE_ATTENTION_REQUIRED" in types(blocked)


@pytest.mark.parametrize("source, expected", [
    ("PARTIAL", FieldStatus.PARTIALLY_COMPLETE), ("DONE", FieldStatus.COMPLETED),
])
def test_partial_and_completion_are_only_field_observations(source, expected):
    result = engine().process(event(f"FT-{source}", source, 1))
    assert result.office_update.field_status is expected
    assert not hasattr(result.office_update, "invoice_ready")
    assert all("INVOICE" not in kind for kind in types(result))


def test_exact_replay_has_one_effect():
    handoff = engine()
    raw = event("FT-REPLAY", "WORKING", 4)
    assert handoff.process(raw).outcome is FieldStatusOutcome.APPLIED
    assert handoff.process(raw).outcome is FieldStatusOutcome.DUPLICATE
    assert len(handoff.office_updates) == 1


def test_distinct_events_may_repeat_business_status():
    handoff = engine()
    assert handoff.process(event("FT-W1", "WORKING", 4)).outcome is FieldStatusOutcome.APPLIED
    assert handoff.process(event("FT-W2", "WORKING", 5)).outcome is FieldStatusOutcome.APPLIED
    assert len(handoff.office_updates) == 2


def test_stale_sequence_does_not_roll_state_back():
    handoff = engine()
    handoff.process(event("FT-CURRENT", "WORKING", 5))
    stale = handoff.process(event("FT-STALE", "ONSITE", 3))
    assert stale.outcome is FieldStatusOutcome.STALE
    assert handoff.current_status["JOB-9001"] is FieldStatus.IN_PROGRESS
    assert len(handoff.office_updates) == 1
    assert "FIELD_EVENT_STALE" in types(stale)


def test_unknown_job_stops_before_office_boundary():
    result = engine().process(event("FT-NOJOB", "WORKING", 1, job_id="FT-NO-JOB"))
    assert result.outcome is FieldStatusOutcome.EXCEPTION
    assert result.exception.category.value == "IDENTITY"
    assert result.office_update is None


def test_correlation_and_provenance_survive_handoff():
    result = engine().process(event("FT-PROV", "EN_ROUTE", 1))
    assert result.observation.correlation_id == result.office_update.correlation_id
    assert result.observation.provenance.source.source_id == "FT-PROV"
    assert result.office_update.source_event_id == "FT-PROV"


def test_irrelevant_source_detail_does_not_expand_canonical_model():
    result = engine().process(event("FT-PHOTO", "PHOTO_UPLOADED", 2))
    assert result.outcome is FieldStatusOutcome.IGNORED_NOT_RELEVANT
    assert result.office_update is None


def test_architecture_inventory_identifies_fieldtrack_specific_work():
    inventory = dict(ARCHITECTURE_INVENTORY)
    assert "FieldTrack" in inventory["SOURCE-SPECIFIC ADAPTER"]
    assert "sequence" in inventory["RELIABILITY"]
    assert "SUPPORT SURFACE" in inventory


def engine():
    return FieldStatusHandoff(JOB_MAPPINGS, CREW_MAPPINGS)


def types(result):
    return {item.event_type for item in result.events}
