"""Canonical identity and source provenance value objects."""

from dataclasses import dataclass
from datetime import datetime


def _required(value: str, label: str) -> None:
    if not value.strip():
        raise ValueError(f"{label} is required")


@dataclass(frozen=True)
class SourceReference:
    source_system: str
    source_id: str

    def __post_init__(self) -> None:
        _required(self.source_system, "source system")
        _required(self.source_id, "source ID")


@dataclass(frozen=True)
class Provenance:
    source: SourceReference
    observed_at: datetime
    source_version: str | None = None
    correlation_id: str | None = None


def validate_identity(canonical_id: str, sources: tuple[SourceReference, ...]) -> None:
    _required(canonical_id, "canonical ID")
    if not sources:
        raise ValueError("source-derived canonical records require a source identity")
    keys = [(item.source_system, item.source_id) for item in sources]
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate source reference")
