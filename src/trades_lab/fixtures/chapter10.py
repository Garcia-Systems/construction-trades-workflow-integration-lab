"""Compact clean and deliberately broken authoritative snapshots."""
from datetime import datetime, timezone
from trades_lab.chapter9 import Delivery, DeliveryState
from trades_lab.chapter10 import (EstimateSnapshot, FieldSnapshot, InvoiceReadinessSnapshot,
    JobSnapshot, MaterialRequirementSnapshot, ReconciliationSnapshot, ScheduleSnapshot)
from trades_lab.domain import ExceptionCategory, ExceptionRecord, ExceptionStatus

T = datetime(2026, 1, 9, 9, 0, tzinfo=timezone.utc)

CLEAN_SNAPSHOT = ReconciliationSnapshot(
    estimates=(EstimateSnapshot("EW-EST-3001", "ACCEPTED", "accepted:EW-EST-3001:v1", "corr-clean-1"),),
    jobs=(JobSnapshot("JOB-9101", "accepted:EW-EST-3001:v1", "COMPLETED", correlation_id="corr-clean-1", material_summary_state="READY"),),
    schedules=(ScheduleSnapshot("CB-SCHED-101", "JOB-9101", "UNASSIGNED", "corr-clean-1"),),
    materials=(MaterialRequirementSnapshot("MAT-101", "JOB-9101", "REQUESTED", "SD-REQ-101", "corr-clean-1"),),
    field_observations=(FieldSnapshot("JOB-9101", "COMPLETED", "corr-clean-1"),),
    invoice_readiness=(InvoiceReadinessSnapshot("JOB-9101", "READY", correlation_id="corr-clean-1"),),
    deliveries=(Delivery("DEL-CLEAN", "event-clean", "key-clean", "corr-clean-1", {}, state=DeliveryState.ACKNOWLEDGED),),
)

BROKEN_SNAPSHOT = ReconciliationSnapshot(
    estimates=(EstimateSnapshot("EW-EST-3002", "ACCEPTED", "accepted:EW-EST-3002:v1", "corr-missing-job"),),
    jobs=(
        JobSnapshot("JOB-9102", None, "READY", correlation_id="corr-schedule"),
        JobSnapshot("JOB-9103", None, "COMPLETED", scheduling_required=False, material_summary_state="READY", correlation_id="corr-material"),
        JobSnapshot("JOB-9104", None, "CANCELLED", scheduling_required=False, correlation_id="corr-state"),
    ),
    schedules=(ScheduleSnapshot("CB-SCHED-ORPHAN", "JOB-DOES-NOT-EXIST", "ASSIGNED", "corr-orphan"),),
    materials=(
        MaterialRequirementSnapshot("MAT-201", "JOB-9103", "REQUESTED", None, "corr-material-ack"),
        MaterialRequirementSnapshot("MAT-202", "JOB-9103", "UNRESOLVED", None, "corr-material-map"),
    ),
    field_observations=(FieldSnapshot("JOB-9103", "COMPLETED", "corr-invoice"),
                        FieldSnapshot("JOB-9104", "IN_PROGRESS", "corr-state")),
    invoice_readiness=(InvoiceReadinessSnapshot("JOB-9103", "BLOCKED", ("accounting customer mapping missing",), "corr-invoice"),),
    deliveries=(Delivery("DEL-EXHAUSTED", "event-bad", "key-bad", "corr-delivery", {}, state=DeliveryState.EXHAUSTED),),
    exceptions=(ExceptionRecord("EX-MAP-1", ExceptionCategory.MAPPING, "Job", "JOB-9103", "SupplyDesk",
                                "material identity requires review", ExceptionStatus.OPEN, T, "corr-exception"),),
)
