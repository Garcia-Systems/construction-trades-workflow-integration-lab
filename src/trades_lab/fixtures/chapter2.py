"""A deterministic canonical workflow snapshot, not an executed handoff."""

from datetime import datetime, timezone

from trades_lab.domain import (Completion, Crew, Customer, Estimate, IntegrationEvent,
                               InvoiceReadiness, InvoiceReadinessState, Job, JobState,
                               Lead, MaterialRequirement, Provenance, ScheduleAssignment,
                               SourceReference, EstimateState)

OBSERVED_AT = datetime(2026, 2, 3, 14, 0, tzinfo=timezone.utc)


def ref(system: str, record_id: str) -> SourceReference:
    return SourceReference(system, record_id)


def provenance(source: SourceReference, correlation: str = "corr-002") -> Provenance:
    return Provenance(source, OBSERVED_AT, "v1", correlation)


CUSTOMER_REFS = (ref("RiverLead CRM", "rl-customer-441"), ref("EstimateWorks", "ew-client-842"))
CUSTOMER = Customer("customer-001", CUSTOMER_REFS, provenance(CUSTOMER_REFS[0]), "Acme Facilities")
LEAD_REF = ref("RiverLead CRM", "rl-lead-101")
LEAD = Lead("lead-001", (LEAD_REF,), provenance(LEAD_REF), CUSTOMER.canonical_id)
ESTIMATE_REF = ref("EstimateWorks", "ew-estimate-210")
ESTIMATE = Estimate("estimate-001", (ESTIMATE_REF,), provenance(ESTIMATE_REF), CUSTOMER.canonical_id, EstimateState.ACCEPTED)
JOB_REF = ref("CrewBoard", "cb-job-310")
JOB = Job("job-001", (JOB_REF,), provenance(JOB_REF), ESTIMATE.canonical_id, JobState.PENDING)
CREW_REF = ref("CrewBoard", "cb-crew-07")
CREW = Crew("crew-001", (CREW_REF,), provenance(CREW_REF), "Crew Seven")
SCHEDULE_REF = ref("CrewBoard", "cb-assignment-12")
SCHEDULE = ScheduleAssignment("schedule-001", (SCHEDULE_REF,), provenance(SCHEDULE_REF), JOB.canonical_id, CREW.canonical_id, datetime(2026, 2, 5, 13, 0, tzinfo=timezone.utc))
MATERIAL_REF = ref("SupplyDesk", "sd-requirement-55")
MATERIAL = MaterialRequirement("material-001", (MATERIAL_REF,), provenance(MATERIAL_REF), JOB.canonical_id, "Replacement valve")
COMPLETION_REF = ref("FieldTrack", "ft-completion-81")
COMPLETION = Completion("completion-001", (COMPLETION_REF,), provenance(COMPLETION_REF), JOB.canonical_id, JobState.COMPLETED, datetime(2026, 2, 5, 20, 0, tzinfo=timezone.utc))
INVOICE_REF = ref("LedgerPro", "lp-readiness-91")
INVOICE_READINESS = InvoiceReadiness("invoice-ready-001", (INVOICE_REF,), provenance(INVOICE_REF), JOB.canonical_id, InvoiceReadinessState.READY)
EVENTS = (
    IntegrationEvent("event-001", "estimate.observed", "EstimateWorks", "ew-estimate-210", "Estimate", "estimate-001", OBSERVED_AT, "corr-002", (("source_state", "CUSTOMER_APPROVED"),)),
    IntegrationEvent("event-002", "completion.observed", "FieldTrack", "ft-completion-81", "Completion", "completion-001", datetime(2026, 2, 5, 20, 1, tzinfo=timezone.utc), "corr-003", (("source_state", "DONE"),)),
)

WORKFLOW_SNAPSHOT = (CUSTOMER, LEAD, ESTIMATE, JOB, CREW, SCHEDULE, MATERIAL, COMPLETION, INVOICE_READINESS)
