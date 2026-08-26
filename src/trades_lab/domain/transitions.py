"""Explicit eligibility checks; deliberately not a workflow engine."""

from enum import Enum

from .states import EstimateState, JobState

ALLOWED_TRANSITIONS = {
    (EstimateState.DRAFT, EstimateState.SENT),
    (EstimateState.SENT, EstimateState.ACCEPTED),
    (EstimateState.SENT, EstimateState.REJECTED),
    (EstimateState.SENT, EstimateState.EXPIRED),
    (JobState.PENDING, JobState.READY),
    (JobState.READY, JobState.SCHEDULED),
    (JobState.SCHEDULED, JobState.IN_PROGRESS),
    (JobState.IN_PROGRESS, JobState.BLOCKED),
    (JobState.BLOCKED, JobState.IN_PROGRESS),
    (JobState.IN_PROGRESS, JobState.PARTIALLY_COMPLETE),
    (JobState.PARTIALLY_COMPLETE, JobState.IN_PROGRESS),
    (JobState.IN_PROGRESS, JobState.COMPLETED),
    (JobState.PARTIALLY_COMPLETE, JobState.COMPLETED),
}


class TransitionError(ValueError):
    pass


def can_transition(current: Enum, proposed: Enum) -> bool:
    return type(current) is type(proposed) and (current, proposed) in ALLOWED_TRANSITIONS


def validate_transition(current: Enum, proposed: Enum) -> None:
    if not can_transition(current, proposed):
        raise TransitionError(
            f"transition {current.value} -> {proposed.value} is not allowed by the canonical integration model"
        )
