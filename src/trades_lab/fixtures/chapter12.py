"""Deterministic healthy and degraded operational-briefing evidence."""

from datetime import datetime, timedelta, timezone

from trades_lab.chapter9 import Delivery, DeliveryState
from trades_lab.chapter10 import (EstimateSnapshot, FieldSnapshot, InvoiceReadinessSnapshot,
    JobSnapshot, MaterialRequirementSnapshot, Reconciler, ReconciliationSnapshot, ScheduleSnapshot)
from trades_lab.chapter11 import BusinessImpact, ManagedException, OwnerRole
from trades_lab.chapter12 import BriefingEvidence, CompletionObservation
from trades_lab.domain import ExceptionCategory, ExceptionRecord, ExceptionStatus

GENERATED_AT = datetime(2026, 8, 26, 21, 0, tzinfo=timezone.utc)


def _delivery(identifier: str, state: DeliveryState) -> Delivery:
    return Delivery(identifier, f"event-{identifier}", f"key-{identifier}", f"corr-{identifier}", {}, state)


def _exception(identifier: str, category: ExceptionCategory, entity: str, age_hours: int,
               owner: OwnerRole, impact: BusinessImpact) -> ManagedException:
    record = ExceptionRecord(identifier, category, "JOB", entity, "Integration",
        category.value.replace("_", " ") + " requires review", ExceptionStatus.OPEN,
        GENERATED_AT - timedelta(hours=age_hours), f"corr-{entity}")
    return ManagedException(record, f"{category.value}:{entity}", owner, impact, ())


HEALTHY_SNAPSHOT = ReconciliationSnapshot(
    estimates=(EstimateSnapshot("EW-EST-3001", "ACCEPTED", "EW-EST-3001"),),
    jobs=(JobSnapshot("JOB-9001", "EW-EST-3001", "COMPLETED", scheduling_required=False),),
    field_observations=(FieldSnapshot("JOB-9001", "COMPLETED"),),
    invoice_readiness=(InvoiceReadinessSnapshot("JOB-9001", "READY"),),
    deliveries=(_delivery("DEL-100", DeliveryState.ACKNOWLEDGED),),
)

DEGRADED_EXCEPTIONS = (
    _exception("EXC-014", ExceptionCategory.ACCOUNTING_MAPPING, "JOB-9107", 31,
               OwnerRole.ACCOUNTING_LEAD, BusinessImpact.BLOCKS_BILLING),
    _exception("EXC-015", ExceptionCategory.MAPPING, "JOB-9110", 100,
               OwnerRole.OPERATIONS_MANAGER, BusinessImpact.BLOCKS_HANDOFF),
    _exception("EXC-016", ExceptionCategory.STATE_CONFLICT, "JOB-9111", 97,
               OwnerRole.FIELD_SUPERVISOR, BusinessImpact.OPERATIONAL_REVIEW),
    _exception("EXC-017", ExceptionCategory.DELIVERY, "DEL-102", 12,
               OwnerRole.INTEGRATION_SUPPORT, BusinessImpact.BLOCKS_HANDOFF),
    _exception("EXC-018", ExceptionCategory.RECONCILIATION, "EW-EST-3011", 8,
               OwnerRole.OPERATIONS_MANAGER, BusinessImpact.OPERATIONAL_REVIEW),
)

DEGRADED_SNAPSHOT = ReconciliationSnapshot(
    estimates=(EstimateSnapshot("EW-EST-3011", "ACCEPTED", "EW-EST-3011", "corr-est-3011"),),
    jobs=(
        JobSnapshot("JOB-9107", None, "COMPLETED", scheduling_required=False),
        JobSnapshot("JOB-9110", None, "READY", scheduling_required=True),
        JobSnapshot("JOB-9111", None, "IN_PROGRESS", scheduling_required=False),
    ),
    schedules=(ScheduleSnapshot("SCH-9110", "JOB-9110", "REVIEW_REQUIRED"),),
    materials=(
        MaterialRequirementSnapshot("MAT-01", "JOB-9110", "UNRESOLVED"),
        MaterialRequirementSnapshot("MAT-02", "JOB-9110", "UNRESOLVED"),
    ),
    field_observations=(FieldSnapshot("JOB-9107", "COMPLETED"), FieldSnapshot("JOB-9111", "BLOCKED")),
    invoice_readiness=(InvoiceReadinessSnapshot("JOB-9107", "BLOCKED", ("ACCOUNTING_CUSTOMER_MAPPING",)),),
    deliveries=(_delivery("DEL-102", DeliveryState.EXHAUSTED), _delivery("DEL-103", DeliveryState.UNCERTAIN)),
    exceptions=tuple(x.record for x in DEGRADED_EXCEPTIONS),
)

HEALTHY_EVIDENCE = BriefingEvidence(HEALTHY_SNAPSHOT, Reconciler().reconcile(HEALTHY_SNAPSHOT, GENERATED_AT), (), (
    CompletionObservation("JOB-9001", datetime(2026, 8, 24, 14, tzinfo=timezone.utc),
                          datetime(2026, 8, 25, 9, tzinfo=timezone.utc)),))
DEGRADED_EVIDENCE = BriefingEvidence(DEGRADED_SNAPSHOT,
    Reconciler().reconcile(DEGRADED_SNAPSHOT, GENERATED_AT), DEGRADED_EXCEPTIONS, (
        CompletionObservation("JOB-9107", GENERATED_AT - timedelta(hours=31), None,
                              "ACCOUNTING_CUSTOMER_MAPPING"),))
