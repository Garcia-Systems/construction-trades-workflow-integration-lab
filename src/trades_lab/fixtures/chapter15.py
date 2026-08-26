"""Deterministic Tidewater fixtures."""

from datetime import date
from trades_lab.chapter15 import JobBillingState, OfficeCompletionEntry, QualifiedIdentity

PAPER_COMPLETION = OfficeCompletionEntry("JOB-A", "LEGACY-1", date(2026, 8, 20), "PHYSICAL_DONE", "OFFICE_COORDINATOR", "PAPER-2026-0042")
WEAK_IDENTITY_2026 = QualifiedIdentity("LegacyWork", "RESIDENTIAL", 2026, "WORK-001")
WEAK_IDENTITY_2025 = QualifiedIdentity("LegacyWork", "COMMERCIAL", 2025, "WORK-001")
BILLING_PROJECT_JOBS = (JobBillingState("JOB-A", True), JobBillingState("JOB-B", False))
