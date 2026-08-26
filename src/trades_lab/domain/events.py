"""Serializable event and exception contracts; no processing or persistence."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from .identity import _required


@dataclass(frozen=True)
class IntegrationEvent:
    event_id: str
    event_type: str
    source_system: str
    source_record_id: str
    entity_type: str
    entity_id: str
    occurred_at: datetime
    correlation_id: str
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        for value, label in ((self.event_id, "event ID"), (self.source_system, "source system"),
                             (self.source_record_id, "source record ID"),
                             (self.entity_id, "entity ID"), (self.correlation_id, "correlation ID")):
            _required(value, label)


class ExceptionCategory(StrEnum):
    VALIDATION = "VALIDATION"
    IDENTITY = "IDENTITY"
    STATE_CONFLICT = "STATE_CONFLICT"
    UNSUPPORTED = "UNSUPPORTED"
    ACCESS = "ACCESS"
    MAPPING = "MAPPING"


class ExceptionStatus(StrEnum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"


@dataclass(frozen=True)
class ExceptionRecord:
    exception_id: str
    category: ExceptionCategory
    entity_type: str
    entity_id: str
    source_system: str
    summary: str
    status: ExceptionStatus
    created_at: datetime
    correlation_id: str

    def __post_init__(self) -> None:
        _required(self.exception_id, "exception ID")
        _required(self.entity_id, "entity ID")
        _required(self.source_system, "source system")
        _required(self.summary, "summary")
