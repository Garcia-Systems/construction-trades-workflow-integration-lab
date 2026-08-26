"""Compact immutable canonical observations.

State fields are constructor observations, not mutable business-state controls. Source
systems remain authoritative; callers may only assess proposed changes with the
transition functions.
"""

from dataclasses import dataclass
from datetime import datetime

from .identity import Provenance, SourceReference, validate_identity
from .states import EstimateState, InvoiceReadinessState, JobState


@dataclass(frozen=True)
class CanonicalEntity:
    canonical_id: str
    source_references: tuple[SourceReference, ...]
    provenance: Provenance

    def __post_init__(self) -> None:
        validate_identity(self.canonical_id, self.source_references)
        if self.provenance.source not in self.source_references:
            raise ValueError("provenance source must be retained in source references")


@dataclass(frozen=True)
class Customer(CanonicalEntity):
    display_name: str


@dataclass(frozen=True)
class Lead(CanonicalEntity):
    customer_id: str


@dataclass(frozen=True)
class Estimate(CanonicalEntity):
    customer_id: str
    state: EstimateState


@dataclass(frozen=True)
class Job(CanonicalEntity):
    estimate_id: str
    state: JobState


@dataclass(frozen=True)
class Crew(CanonicalEntity):
    name: str


@dataclass(frozen=True)
class ScheduleAssignment(CanonicalEntity):
    job_id: str
    crew_id: str
    starts_at: datetime


@dataclass(frozen=True)
class MaterialRequirement(CanonicalEntity):
    job_id: str
    description: str


@dataclass(frozen=True)
class Completion(CanonicalEntity):
    job_id: str
    state: JobState
    completed_at: datetime | None


@dataclass(frozen=True)
class InvoiceReadiness(CanonicalEntity):
    job_id: str
    state: InvoiceReadinessState
