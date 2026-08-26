"""Deterministic Chapter 8 facts."""
from dataclasses import replace
from datetime import date, datetime, timezone

from trades_lab.chapter7 import FieldStatus, FieldStatusObservation
from trades_lab.chapter8 import BillingMetadata, CompletionEvidence, ReadinessFacts
from trades_lab.domain import JobState, Provenance, SourceReference

AT = datetime(2026, 1, 8, 17, tzinfo=timezone.utc)
SOURCE = SourceReference("FieldTrack", "FT-COMP-9001")
OBSERVATION = FieldStatusObservation("corr-job-9001", "FT-COMP-9001", "JOB-9001",
    "FT-JOB-9001", "CREW-07", FieldStatus.COMPLETED, AT, 8, None,
    Provenance(SOURCE, AT, "8", "corr-job-9001"))
EVIDENCE = CompletionEvidence("COMP-9001", "JOB-9001", AT, "WORK_COMPLETE",
                              "FieldTrack", "FT-COMP-9001", "1")
METADATA = BillingMetadata("WO-9001", date(2026, 1, 8), "Replace failed rooftop unit",
                           "SERVICE", "1")
READY_FACTS = ReadinessFacts("JOB-9001", "CUST-9001", JobState.COMPLETED, AT, "8",
                             OBSERVATION, True, EVIDENCE, METADATA)
PARTIAL_FACTS = replace(READY_FACTS, field_observation=replace(OBSERVATION,
                                canonical_status=FieldStatus.PARTIALLY_COMPLETE))
CUSTOMER_MAPPINGS = {"CUST-9001": "LP-CUST-410"}
