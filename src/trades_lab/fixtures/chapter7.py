"""Deterministic, wholly synthetic FieldTrack events and identity configuration."""
from datetime import datetime, timezone

from trades_lab.chapter7 import RawFieldTrackEvent

JOB_MAPPINGS = {"FT-JOB-8821": "JOB-9001"}
CREW_MAPPINGS = {"FT-CREW-04": "CREWBOARD-CREW-04"}

def event(event_id: str, status: str, sequence: int | None, notes: str | None = None,
          job_id: str = "FT-JOB-8821", crew_id: str = "FT-CREW-04") -> RawFieldTrackEvent:
    return RawFieldTrackEvent(event_id, job_id, crew_id, status,
                              datetime(2026, 8, 25, 18, 20, tzinfo=timezone.utc), sequence, notes)
