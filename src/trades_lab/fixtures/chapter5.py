"""Deterministic synthetic Chapter 5 jobs."""

from dataclasses import replace
from datetime import datetime, timezone

from trades_lab.chapter4 import ServiceAddress
from trades_lab.chapter5 import AuthoritativeJob, CrewSkill, OperationalJobState
from trades_lab.domain import Provenance, SourceReference

OBSERVED_AT = datetime(2026, 2, 2, 12, tzinfo=timezone.utc)
SOURCE = SourceReference("CrewBoard Jobs", "JOB-9001")
PROVENANCE = Provenance(SOURCE, OBSERVED_AT, "1", "corr-job-job-9001")
VALID_READY_JOB = AuthoritativeJob(
    "JOB-9001", "accepted-estimate:EW-EST-2001:v3", 1, OperationalJobState.READY,
    ServiceAddress("1420 Foundry Lane", "Richmond", "VA", "23220"),
    (CrewSkill.HVAC_INSTALL, CrewSkill.TWO_PERSON_CREW), 240,
    datetime(2026, 2, 3, 13, tzinfo=timezone.utc),
    datetime(2026, 2, 6, 22, tzinfo=timezone.utc), "NORMAL", PROVENANCE)
CHANGED_DURATION_JOB = replace(VALID_READY_JOB, version=2, estimated_duration_minutes=360,
                               provenance=replace(PROVENANCE, source_version="2"))
PENDING_JOB = replace(VALID_READY_JOB, state=OperationalJobState.PENDING)
MISSING_SKILL_JOB = replace(VALID_READY_JOB, required_skill_tags=())
INVALID_WINDOW_JOB = replace(VALID_READY_JOB,
                             earliest_start=VALID_READY_JOB.latest_completion)
CANCELLED_JOB = replace(VALID_READY_JOB, version=3, state=OperationalJobState.CANCELLED,
                        provenance=replace(PROVENANCE, source_version="3"))
