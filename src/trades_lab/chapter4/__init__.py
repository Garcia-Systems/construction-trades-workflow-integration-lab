"""Chapter 4's bounded consequential-write experiment."""

from .handoff import (
    ARCHITECTURE_INVENTORY,
    AcceptedEstimate,
    AcceptedEstimateToJobHandoff,
    CrewBoardSimulator,
    DestinationJob,
    EstimateValidationError,
    EstimateWorksAdapter,
    IdempotencyRecord,
    IdempotencyStatus,
    JobCreateCommand,
    JobCreationAcknowledgement,
    JobHandoffOutcome,
    JobHandoffResult,
    ServiceAddress,
)

# Familiar short names for callers reading this as the chapter's one handoff.
HandoffOutcome = JobHandoffOutcome
HandoffResult = JobHandoffResult

__all__ = [name for name in globals() if not name.startswith("_")]
