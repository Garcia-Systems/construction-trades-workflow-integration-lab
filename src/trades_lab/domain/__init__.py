"""Small canonical contracts used to describe, but not execute, handoffs."""

from .entities import (Completion, Crew, Customer, Estimate, InvoiceReadiness, Job,
                       Lead, MaterialRequirement, ScheduleAssignment)
from .events import ExceptionCategory, ExceptionRecord, ExceptionStatus, IntegrationEvent
from .identity import Provenance, SourceReference
from .states import EstimateState, InvoiceReadinessState, JobState
from .transitions import TransitionError, can_transition, validate_transition

__all__ = [
    "Completion", "Crew", "Customer", "Estimate", "ExceptionCategory",
    "ExceptionRecord", "ExceptionStatus", "IntegrationEvent", "InvoiceReadiness",
    "InvoiceReadinessState", "Job", "JobState", "Lead", "MaterialRequirement",
    "Provenance", "ScheduleAssignment", "SourceReference", "EstimateState",
    "TransitionError", "can_transition", "validate_transition",
]
