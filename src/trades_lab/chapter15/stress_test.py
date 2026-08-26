"""Tidewater-specific experiments kept deliberately outside the shared domain core."""

from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from hashlib import sha256


class VariationResponse(StrEnum):
    CONFIGURATION_ONLY = "CONFIGURATION_ONLY"
    NEW_MAPPING = "NEW_MAPPING"
    NEW_SOURCE_ADAPTER = "NEW_SOURCE_ADAPTER"
    SHARED_CORE_EXTENSION = "SHARED_CORE_EXTENSION"
    WORKFLOW_SPECIFIC_EXTENSION = "WORKFLOW_SPECIFIC_EXTENSION"
    CUSTOMER_SPECIFIC_RULE = "CUSTOMER_SPECIFIC_RULE"
    MANUAL_PROCESS = "MANUAL_PROCESS"
    UNSUPPORTED = "UNSUPPORTED"


class BaselineFit(StrEnum):
    SAME = "SAME"
    CONFIGURATION_CHANGE = "CONFIGURATION_CHANGE"
    STRUCTURAL_CHANGE = "STRUCTURAL_CHANGE"
    UNSUPPORTED = "UNSUPPORTED"


@dataclass(frozen=True)
class CustomerVariation:
    variation_id: str
    name: str
    description: str
    affected_workflow: str
    response: VariationResponse
    affected_components: tuple[str, ...]
    new_tests_required: bool
    support_surface_added: bool
    notes: str


class AcceptanceDecision(StrEnum):
    AUTOMATION_ELIGIBLE = "AUTOMATION_ELIGIBLE"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    INELIGIBLE = "INELIGIBLE"


class BidForgeAdapter:
    """New source adapter; it does not broaden canonical estimate semantics."""

    def acceptance_decision(self, source_status: str) -> AcceptanceDecision:
        return {"SIGNED": AcceptanceDecision.AUTOMATION_ELIGIBLE,
                "CUSTOMER_VERBAL_OK": AcceptanceDecision.HUMAN_REVIEW}.get(
                    source_status, AcceptanceDecision.INELIGIBLE)

    def may_authorize_job(self, source_status: str) -> bool:
        return self.acceptance_decision(source_status) is AcceptanceDecision.AUTOMATION_ELIGIBLE


@dataclass(frozen=True)
class ProspectiveJobDecision:
    state: str
    enters_shared_handoff: bool
    approach: str = "B_TIDEWATER_PRE_AUTHORIZATION"


def prospective_job(source_state: str) -> ProspectiveJobDecision:
    """Approach B avoids falsely calling an unaccepted prospect JOB_PENDING."""
    return ProspectiveJobDecision(source_state, source_state in {"AUTHORIZED", "ACTIVE"})


@dataclass(frozen=True)
class ScheduleGateResult:
    eligible: bool
    request_status: str
    exception: str | None


def schedule_gate(authorized: bool, operations_approved: bool) -> ScheduleGateResult:
    if not authorized:
        return ScheduleGateResult(False, "BLOCKED", "JOB_NOT_AUTHORIZED")
    if not operations_approved:
        return ScheduleGateResult(False, "BLOCKED", "OPERATIONS_APPROVAL_REQUIRED")
    return ScheduleGateResult(True, "REQUESTED", None)


@dataclass(frozen=True)
class KitLine:
    line_id: str
    destination_material_id: str | None
    quantity: int


@dataclass(frozen=True)
class KitExpansionResult:
    kit_id: str
    lines: tuple[KitLine, ...]
    mapped: int
    unresolved: int
    status: str
    exception: str | None


class TidewaterKitExpander:
    """One bounded kit rule, intentionally not a generic BOM system."""

    KIT_A = (("copper-tube", 2), ("isolation-valve", 1), ("tss-special-bracket", 1))

    def __init__(self, mappings: dict[str, str] | None = None) -> None:
        self.mappings = mappings or {"copper-tube": "SD-COPPER", "isolation-valve": "SD-VALVE"}
        self._requests: dict[str, KitLine] = {}

    @property
    def requests(self) -> tuple[KitLine, ...]:
        return tuple(self._requests.values())

    def expand(self, kit_id: str, job_id: str = "JOB-A") -> KitExpansionResult:
        if kit_id != "TSS-KIT-A":
            return KitExpansionResult(kit_id, (), 0, 1, "BLOCKED", "UNKNOWN_KIT")
        lines = tuple(KitLine(f"{kit_id}-{i}", self.mappings.get(source), quantity)
                      for i, (source, quantity) in enumerate(self.KIT_A, 1))
        for line in lines:
            if line.destination_material_id:
                key = sha256(f"{job_id}|{line.line_id}|{line.destination_material_id}".encode()).hexdigest()
                self._requests.setdefault(key, line)
        unresolved = sum(line.destination_material_id is None for line in lines)
        return KitExpansionResult(kit_id, lines, len(lines) - unresolved, unresolved,
                                  "READY" if not unresolved else "PARTIALLY_READY",
                                  None if not unresolved else "KIT_LINE_MAPPING_REQUIRED")


@dataclass(frozen=True)
class OfficeCompletionEntry:
    job_reference: str
    crew: str
    completion_date: date | None
    completion_code: str
    entered_by_role: str
    source_document_reference: str


@dataclass(frozen=True)
class CompletionAdaptation:
    accepted: bool
    source_system: str
    provenance: tuple[tuple[str, str], ...]
    exception: str | None = None


class OfficeCompletionAdapter:
    def adapt(self, entry: OfficeCompletionEntry) -> CompletionAdaptation:
        values = (entry.job_reference, entry.crew, entry.completion_date, entry.completion_code,
                  entry.entered_by_role, entry.source_document_reference)
        provenance = (("entered_by_role", entry.entered_by_role),
                      ("source_document_reference", entry.source_document_reference))
        if not all(values):
            return CompletionAdaptation(False, "OfficeCompletionEntry", provenance,
                                        "MANUAL_COMPLETION_VALIDATION_FAILED")
        return CompletionAdaptation(True, "OfficeCompletionEntry", provenance)


@dataclass(frozen=True)
class QualifiedIdentity:
    source: str
    division: str
    year: int
    source_id: str

    @property
    def canonical_key(self) -> str:
        return "|".join((self.source, self.division, str(self.year), self.source_id))


@dataclass(frozen=True)
class JobBillingState:
    job_id: str
    individually_ready: bool


@dataclass(frozen=True)
class BillingProjectResult:
    project_id: str
    ready: bool
    ready_jobs: int
    blocked_jobs: int
    invoice_created: bool = False


def aggregate_billing_project(project_id: str, jobs: tuple[JobBillingState, ...]) -> BillingProjectResult:
    ready = sum(job.individually_ready for job in jobs)
    return BillingProjectResult(project_id, bool(jobs) and ready == len(jobs), ready, len(jobs) - ready)


@dataclass(frozen=True)
class CompletionMeaning:
    canonical_completed: bool
    paperwork_complete: bool
    invoice_eligible: bool


def interpret_done(source_context: str, status: str) -> CompletionMeaning:
    if status != "DONE":
        return CompletionMeaning(False, False, False)
    if source_context == "DIGITAL_SERVICE_CREW":
        return CompletionMeaning(True, True, True)
    if source_context == "LEGACY_CREW":
        return CompletionMeaning(False, False, False)
    return CompletionMeaning(False, False, False)


VARIATIONS = (
    CustomerVariation("TSS-01", "BidForge semantics", "SIGNED differs from verbal approval", "estimate acceptance", VariationResponse.NEW_SOURCE_ADAPTER, ("adapter", "mapping", "approval exception"), True, True, "New mapping and customer policy"),
    CustomerVariation("TSS-02", "Prospective job", "Job exists before authorization", "job creation", VariationResponse.WORKFLOW_SPECIFIC_EXTENSION, ("pre-authorization state",), True, True, "Kept outside shared handoff"),
    CustomerVariation("TSS-03", "Operations approval", "Approval gates scheduling", "scheduling", VariationResponse.CUSTOMER_SPECIFIC_RULE, ("eligibility", "exception"), True, True, "No generic approval engine"),
    CustomerVariation("TSS-04", "Material kit", "One source kit expands to three lines", "materials", VariationResponse.CUSTOMER_SPECIFIC_RULE, ("kit expander", "mapping"), True, True, "No BOM engine"),
    CustomerVariation("TSS-05", "Paper completion", "Office transcribes paper sheet", "completion", VariationResponse.NEW_SOURCE_ADAPTER, ("adapter", "validation", "provenance"), True, True, "Manual entry remains explicit"),
    CustomerVariation("TSS-06", "Billing aggregation", "Several jobs form one billing project", "invoice readiness", VariationResponse.WORKFLOW_SPECIFIC_EXTENSION, ("project aggregation",), True, True, "Creates no invoice"),
    CustomerVariation("TSS-07", "Weak identity", "ID unique only in division and year", "identity", VariationResponse.CUSTOMER_SPECIFIC_RULE, ("qualified identity",), True, True, "Context required"),
    CustomerVariation("TSS-08", "DONE conflict", "Crew context changes DONE meaning", "completion", VariationResponse.CUSTOMER_SPECIFIC_RULE, ("completion policy", "readiness gate"), True, True, "Literal is never normalized alone"),
    CustomerVariation("TSS-09", "BidForge state table", "New source mapping content", "estimate acceptance", VariationResponse.NEW_MAPPING, ("mapping configuration",), True, True, "Ongoing mapping support"),
    CustomerVariation("TSS-10", "Kit mappings", "Destination IDs are customer configuration", "materials", VariationResponse.CONFIGURATION_ONLY, ("material mapping",), True, True, "Mapping content changes"),
    CustomerVariation("TSS-11", "Paper transcription", "Human enters completion evidence", "completion", VariationResponse.MANUAL_PROCESS, ("office procedure",), True, True, "Not OCR"),
)

BASELINE_COMPARISON = {
    "estimate acceptance": BaselineFit.STRUCTURAL_CHANGE, "job creation": BaselineFit.STRUCTURAL_CHANGE,
    "scheduling eligibility": BaselineFit.STRUCTURAL_CHANGE, "material mapping": BaselineFit.STRUCTURAL_CHANGE,
    "field completion": BaselineFit.STRUCTURAL_CHANGE, "invoice readiness": BaselineFit.STRUCTURAL_CHANGE,
    "identity": BaselineFit.STRUCTURAL_CHANGE, "reliability": BaselineFit.SAME,
    "exception handling": BaselineFit.CONFIGURATION_CHANGE, "operational support": BaselineFit.STRUCTURAL_CHANGE,
}

REUSE_MATRIX = {
    "Canonical identity": "REUSED_WITH_EDGE_QUALIFICATION", "Correlation": "REUSED",
    "Idempotency": "REUSED", "Retry framework": "REUSED", "Exception workflow": "REUSED",
    "BidForge adapter": "NEW", "Estimate-state mapping": "NEW_CONFIGURATION",
    "Estimate eligibility": "CUSTOMER_SPECIFIC", "Scheduling destination": "REUSED",
    "Scheduling eligibility": "CUSTOMER_SPECIFIC", "Material mapping mechanism": "PARTIAL_REUSE",
    "Kit expansion": "CUSTOMER_SPECIFIC", "Field completion model": "PARTIAL_REUSE",
    "Office completion adapter": "NEW", "Invoice readiness": "PARTIAL_REUSE",
    "Billing project aggregation": "WORKFLOW_SPECIFIC",
}

SUPPORT_SURFACE = ("BidForge status semantics", "verbal-approval exception handling",
                   "operations approval routing", "material kit definitions",
                   "manual completion validation", "billing project membership",
                   "weak legacy identifier qualification", "crew-specific completion semantics")


def change_inventory() -> dict[str, int]:
    counts = {response.value: 0 for response in VariationResponse}
    for item in VARIATIONS:
        counts[item.response.value] += 1
    return {"unchanged_reused_units": sum(v == "REUSED" for v in REUSE_MATRIX.values()),
            "configuration_only": counts["CONFIGURATION_ONLY"], "new_mappings": counts["NEW_MAPPING"],
            "new_adapters": counts["NEW_SOURCE_ADAPTER"],
            "workflow_specific_extensions": counts["WORKFLOW_SPECIFIC_EXTENSION"],
            "customer_specific_rules": counts["CUSTOMER_SPECIFIC_RULE"],
            "shared_core_changes": counts["SHARED_CORE_EXTENSION"], "new_validation": 2,
            "new_exceptions": 3, "new_tests": 24,
            "support_surface_additions": len(SUPPORT_SURFACE)}


CORE_IMPACT = "LOW_CORE_IMPACT"
