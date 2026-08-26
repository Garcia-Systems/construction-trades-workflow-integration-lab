from dataclasses import fields

from trades_lab.chapter4 import IdempotencyStatus
from trades_lab.chapter5 import (ARCHITECTURE_INVENTORY, CrewBoardSchedulingSimulator,
                                 CrewSkill, JobToScheduleHandoff, ScheduleAssignment,
                                 ScheduleHandoffOutcome, ScheduleRequestState)
from trades_lab.domain import ExceptionCategory
from trades_lab.fixtures.chapter5 import (CANCELLED_JOB, CHANGED_DURATION_JOB,
                                          INVALID_WINDOW_JOB, MISSING_SKILL_JOB,
                                          PENDING_JOB, VALID_READY_JOB)


def test_ready_job_produces_exactly_one_acknowledged_unassigned_request():
    handoff = JobToScheduleHandoff()
    result = handoff.process(VALID_READY_JOB)
    assert result.outcome is ScheduleHandoffOutcome.REQUESTED
    assert len(handoff.commands) == len(handoff.destination.requests) == 1
    assert result.acknowledgement.request_state is ScheduleRequestState.UNASSIGNED
    assert result.acknowledgement.created is True
    assert handoff.destination.assignments == ()
    assert handoff.registry[result.command.idempotency_key].status is IdempotencyStatus.ACKNOWLEDGED


def test_command_is_narrow_scheduling_context_not_complete_job_record():
    command = JobToScheduleHandoff().process(VALID_READY_JOB).command
    names = {item.name for item in fields(command)}
    assert names == {"idempotency_key", "scheduling_context_version", "correlation_id",
                     "authoritative_job_id", "external_job_reference", "service_address",
                     "required_skill_tags", "estimated_duration_minutes", "earliest_start",
                     "latest_completion", "priority", "provenance"}
    assert "state" not in names and "blocking_exception" not in names


def test_exact_replay_resolves_existing_request_without_duplicate():
    handoff = JobToScheduleHandoff()
    first = handoff.process(VALID_READY_JOB)
    replay = handoff.process(VALID_READY_JOB, "another-delivery")
    assert replay.outcome is ScheduleHandoffOutcome.IDEMPOTENT_REPLAY
    assert replay.command.idempotency_key == first.command.idempotency_key
    assert replay.acknowledgement.request_id == first.acknowledgement.request_id
    assert replay.acknowledgement.created is False
    assert len(handoff.commands) == len(handoff.destination.requests) == 1


def test_missing_skill_and_invalid_window_are_controlled_exceptions():
    for job in (MISSING_SKILL_JOB, INVALID_WINDOW_JOB):
        handoff = JobToScheduleHandoff()
        result = handoff.process(job)
        assert result.outcome is ScheduleHandoffOutcome.EXCEPTION
        assert result.exception.category is ExceptionCategory.VALIDATION
        assert not handoff.destination.requests


def test_pending_job_is_not_ready_not_technical_failure():
    handoff = JobToScheduleHandoff()
    result = handoff.process(PENDING_JOB)
    assert result.outcome is ScheduleHandoffOutcome.NOT_READY
    assert result.exception is None and not handoff.destination.requests


def test_changed_context_creates_explicit_linked_update_not_replay_or_assignment():
    handoff = JobToScheduleHandoff()
    first = handoff.process(VALID_READY_JOB)
    changed = handoff.process(CHANGED_DURATION_JOB)
    assert changed.outcome is ScheduleHandoffOutcome.UPDATED_REQUEST
    assert changed.command.idempotency_key != first.command.idempotency_key
    assert len(handoff.destination.requests) == 2
    assert handoff.destination.requests[-1].previous_request_id == first.acknowledgement.request_id
    assert not handoff.destination.assignments


def test_existing_assignment_conflict_requires_review_without_overwrite_or_new_request():
    destination = CrewBoardSchedulingSimulator()
    handoff = JobToScheduleHandoff(destination)
    first = handoff.process(VALID_READY_JOB)
    assignment = ScheduleAssignment("ASG-1", VALID_READY_JOB.job_id,
                                    first.acknowledgement.request_id, "CREW-4",
                                    (CrewSkill.HVAC_INSTALL,), VALID_READY_JOB.earliest_start,
                                    VALID_READY_JOB.latest_completion)
    destination.record_assignment(assignment)
    result = handoff.process(CHANGED_DURATION_JOB)
    assert result.outcome is ScheduleHandoffOutcome.REVIEW_REQUIRED
    assert result.exception.category is ExceptionCategory.STATE_CONFLICT
    assert destination.assignments == (assignment,)
    assert len(destination.requests) == 1


def test_cancellation_preserves_history_is_idempotent_and_blocks_stale_ready_event():
    handoff = JobToScheduleHandoff()
    handoff.process(VALID_READY_JOB)
    first = handoff.process(CANCELLED_JOB)
    replay = handoff.process(CANCELLED_JOB, "cancel-again")
    stale = handoff.process(VALID_READY_JOB, "old-ready")
    assert first.outcome is replay.outcome is ScheduleHandoffOutcome.CANCELLED
    assert len(handoff.destination.requests) == 1
    assert handoff.destination.requests[0].state is ScheduleRequestState.CANCELLED
    assert stale.outcome is ScheduleHandoffOutcome.STALE
    assert len(handoff.destination.requests) == 1


def test_correlation_and_provenance_survive_request_and_acknowledgement():
    result = JobToScheduleHandoff().process(VALID_READY_JOB)
    assert result.correlation_id == result.command.correlation_id == result.acknowledgement.correlation_id
    assert result.job.provenance == result.command.provenance == result.acknowledgement.provenance
    assert all(event.correlation_id == result.correlation_id for event in result.events)
    assert tuple(event.event_type for event in result.events) == (
        "JOB_OBSERVED", "JOB_SCHEDULING_VALIDATED", "SCHEDULE_REQUEST_READY",
        "SCHEDULE_REQUEST_SENT", "SCHEDULE_REQUEST_ACKNOWLEDGED")


def test_chapter4_reuse_is_precise_and_workflow_conflicts_remain_specialized():
    assert "Chapter 4 IdempotencyStatus" in ARCHITECTURE_INVENTORY["SHARED CORE"]
    assert "stable business-key pattern" in ARCHITECTURE_INVENTORY["SHARED CORE"]
    assert "assignment conflict" in ARCHITECTURE_INVENTORY["EXCEPTION HANDLING"]
    assert "context-change detection" in ARCHITECTURE_INVENTORY["WORKFLOW-SPECIFIC LOGIC"]
