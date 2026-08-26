"""Bounded integration-level state vocabularies and source normalization."""

from enum import StrEnum


class EstimateState(StrEnum):
    DRAFT = "DRAFT"
    SENT = "SENT"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class JobState(StrEnum):
    PENDING = "PENDING"
    READY = "READY"
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    BLOCKED = "BLOCKED"
    PARTIALLY_COMPLETE = "PARTIALLY_COMPLETE"
    COMPLETED = "COMPLETED"


class InvoiceReadinessState(StrEnum):
    NOT_READY = "NOT_READY"
    READY = "READY"
    BLOCKED = "BLOCKED"


ESTIMATEWORKS_STATES = {
    "OPEN": EstimateState.SENT,
    "CUSTOMER_APPROVED": EstimateState.ACCEPTED,
    "DECLINED": EstimateState.REJECTED,
    "VOID": EstimateState.EXPIRED,
}

FIELDTRACK_STATES = {
    "EN_ROUTE": JobState.SCHEDULED,
    "ONSITE": JobState.IN_PROGRESS,
    "WORKING": JobState.IN_PROGRESS,
    "HOLD": JobState.BLOCKED,
    "PARTIAL": JobState.PARTIALLY_COMPLETE,
    "DONE": JobState.COMPLETED,
}


def _map(state: str, mapping: dict[str, EstimateState | JobState], system: str):
    try:
        return mapping[state]
    except KeyError as error:
        raise ValueError(f"unknown {system} source state: {state}") from error


def map_estimateworks_state(state: str) -> EstimateState:
    return _map(state, ESTIMATEWORKS_STATES, "EstimateWorks")


def map_fieldtrack_state(state: str) -> JobState:
    return _map(state, FIELDTRACK_STATES, "FieldTrack")
