from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone

import pytest

from trades_lab.chapter11 import *
from trades_lab.domain import ExceptionCategory, ExceptionRecord, ExceptionStatus

NOW = datetime(2026, 1, 11, 12, tzinfo=timezone.utc)


def record(identifier="EXC-1", category=ExceptionCategory.IDENTITY, days=1):
    return ExceptionRecord(identifier, category, "customer", "ENTITY-1", "RiverLead", "review",
                           ExceptionStatus.OPEN, NOW - timedelta(days=days), "corr-1")


def test_routing_is_deterministic():
    assert route_owner(ExceptionCategory.IDENTITY) is OwnerRole.OFFICE_MANAGER
    assert route_owner(ExceptionCategory.MAPPING) is OwnerRole.OPERATIONS_MANAGER
    assert route_owner(ExceptionCategory.ACCESS) is OwnerRole.INTEGRATION_SUPPORT
    assert route_owner(ExceptionCategory.MAPPING, accounting_mapping=True) is OwnerRole.ACCOUNTING_LEAD


def test_lifecycle_and_invalid_transition():
    service = ExceptionWorkflow()
    item = service.create(record(), "identity:1", BusinessImpact.BLOCKS_HANDOFF)
    reviewed = service.start_review(item.record.exception_id, OwnerRole.OFFICE_MANAGER)
    assert reviewed.status is ExceptionStatus.IN_REVIEW
    with pytest.raises(ValueError):
        service.start_review(item.record.exception_id, OwnerRole.OFFICE_MANAGER)


def test_resolution_history_authority_and_resume():
    service = ExceptionWorkflow()
    source_customer = {"name": "Original"}
    item = service.create(record(), "identity:1", BusinessImpact.BLOCKS_HANDOFF)
    old_history = item.history
    resolved = service.resolve(item.record.exception_id, ResolutionAction.CONFIRM_IDENTITY, "confirmed",
                               OwnerRole.OFFICE_MANAGER, mapping=("RL-1", "EW-1"))
    assert resolved.status is ExceptionStatus.RESOLVED
    assert resolved.history[:len(old_history)] == old_history
    assert resolved.resolution.automation_may_resume
    assert source_customer == {"name": "Original"}
    with pytest.raises(FrozenInstanceError):
        resolved.history[0].detail = "rewritten"


def test_invalid_action_rejected_without_mutation():
    service = ExceptionWorkflow()
    item = service.create(record(category=ExceptionCategory.ACCESS), "access:1", BusinessImpact.BLOCKS_HANDOFF)
    before = service.exceptions.copy()
    with pytest.raises(ValueError):
        service.resolve(item.record.exception_id, ResolutionAction.CREATE_MAPPING, "wrong",
                        OwnerRole.INTEGRATION_SUPPORT, mapping=("a", "b"))
    assert service.exceptions == before
    assert service.integration_mappings == {}


def test_mapping_is_integration_only_and_replay_is_explicit():
    service = ExceptionWorkflow()
    ledger_customers = {}
    item = service.create(record(category=ExceptionCategory.MAPPING), "accounting:1",
                          BusinessImpact.BLOCKS_BILLING, accounting_mapping=True)
    resolved = service.resolve(item.record.exception_id, ResolutionAction.CREATE_MAPPING, "known customer",
                               OwnerRole.ACCOUNTING_LEAD, mapping=("job-customer", "ledger-existing"))
    assert service.integration_mappings == {"job-customer": "ledger-existing"}
    assert ledger_customers == {}
    assert resolved.resolution.replay_recommended and not resolved.replay_approved
    approved = service.approve_replay(item.record.exception_id, OwnerRole.ACCOUNTING_LEAD)
    assert approved.replay_approved
    assert approved.history[-1].event_type is AuditEventType.REPLAY_APPROVED


def test_access_repair_does_not_fabricate_delivery_success():
    service = ExceptionWorkflow()
    delivery = {"state": "EXHAUSTED"}
    item = service.create(record(category=ExceptionCategory.ACCESS), "delivery:1", BusinessImpact.BLOCKS_HANDOFF)
    resolved = service.resolve(item.record.exception_id, ResolutionAction.REPAIR_ACCESS, "credential repaired",
                               OwnerRole.INTEGRATION_SUPPORT)
    assert resolved.resolution.replay_recommended
    assert delivery["state"] == "EXHAUSTED"


def test_state_conflict_and_dismissal_do_not_write_authority():
    service = ExceptionWorkflow()
    destination = {"assignment": "CREW-7"}
    item = service.create(record(category=ExceptionCategory.STATE_CONFLICT), "state:1",
                          BusinessImpact.OPERATIONAL_REVIEW)
    dismissed = service.resolve(item.record.exception_id, ResolutionAction.DISMISS_INVALID_FINDING,
                                "false-positive finding", OwnerRole.OPERATIONS_MANAGER)
    assert dismissed.status is ExceptionStatus.DISMISSED
    assert destination == {"assignment": "CREW-7"}
    assert dismissed.history[-1].detail == "false-positive finding"


def test_deduplication_recurrence_aging_queue_and_finding_conversion():
    service = ExceptionWorkflow()
    first = service.create(record(days=4), "same-condition", BusinessImpact.BLOCKS_HANDOFF)
    duplicate = service.create(record("EXC-2", days=0), "same-condition", BusinessImpact.BLOCKS_HANDOFF)
    assert duplicate is first
    service.resolve(first.record.exception_id, ResolutionAction.CONFIRM_IDENTITY, "confirmed",
                    OwnerRole.OFFICE_MANAGER, mapping=("a", "b"))
    recurrence = service.create(record("EXC-3", days=0), "same-condition", BusinessImpact.BLOCKS_HANDOFF)
    assert recurrence.record.exception_id == "EXC-3"
    assert service.exceptions["EXC-1"].status is ExceptionStatus.RESOLVED
    assert age_bucket(first.record.created_at) is AgeBucket.OVERDUE
    assert age_bucket(NOW - timedelta(days=2)) is AgeBucket.AGING
    assert age_bucket(NOW - timedelta(hours=2)) is AgeBucket.NEW
    assert service.queue(status=ExceptionStatus.OPEN, owner=OwnerRole.OFFICE_MANAGER) == (recurrence,)
    assert finding_requires_exception(requires_review=True, severity="WARNING")
    assert not finding_requires_exception(requires_review=True, severity="INFO", informational_only=True)
