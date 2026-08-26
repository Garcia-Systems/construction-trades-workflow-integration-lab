"""Delivery-economics sensitivity built from, but never measured by, repository structure.

The central invariant is deliberately executable: implementation units, files, tests,
and adapters are qualitative evidence only.  No function converts their counts to hours.
"""

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from types import MappingProxyType
from typing import Mapping

from trades_lab.chapter0 import BASELINE_HYPOTHESIS
from trades_lab.evidence import EvidenceCategory


class DeliveryCategory(StrEnum):
    DISCOVERY = "Technical discovery"
    API_VALIDATION = "API / interface validation"
    ADAPTERS = "Adapters"
    IDENTITY = "Identity normalization"
    ORCHESTRATION = "Orchestration / workflow logic"
    RELIABILITY = "Reliability / error handling"
    EXCEPTIONS = "Exception handling"
    DOCUMENTATION = "Documentation"
    QA = "QA / testing"
    DEPLOYMENT = "Deployment / production integration"
    REWORK = "Rework reserve"


class UncertaintyLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ReuseCharacter(StrEnum):
    STRONG_SHARED_COMPONENT = "STRONG_SHARED_COMPONENT"
    MIXED = "MIXED"
    MOSTLY_SPECIALIZED = "MOSTLY_SPECIALIZED"
    CUSTOMER_SPECIFIC = "CUSTOMER_SPECIFIC"
    UNKNOWN = "UNKNOWN"


class SensitivityDirection(StrEnum):
    LOWER_PLAUSIBLE = "LOWER_PLAUSIBLE"
    ORIGINAL_PLAUSIBLE = "ORIGINAL_PLAUSIBLE"
    HIGHER_PLAUSIBLE = "HIGHER_PLAUSIBLE"
    WIDE_RANGE = "WIDE_RANGE"


class StructuralComparison(StrEnum):
    SUPPORTED_STRUCTURALLY = "SUPPORTED_STRUCTURALLY"
    POSSIBLY_UNDERSTATED = "POSSIBLY_UNDERSTATED"
    POSSIBLY_OVERSTATED = "POSSIBLY_OVERSTATED"
    HIGHLY_VARIABLE = "HIGHLY_VARIABLE"
    NOT_EVALUABLE = "NOT_EVALUABLE"


class DeliveryVerdict(StrEnum):
    HEALTHY_DELIVERY = "HEALTHY_DELIVERY"
    THIN_DELIVERY = "THIN_DELIVERY"
    UNATTRACTIVE_DELIVERY = "UNATTRACTIVE_DELIVERY"
    SCOPE_REDESIGN_REQUIRED = "SCOPE_REDESIGN_REQUIRED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


@dataclass(frozen=True)
class DeliveryEvidenceCategory:
    category: DeliveryCategory
    original_modeled_hours: Decimal
    evidence_references: tuple[str, ...]
    observed_structure_summary: str
    uncertainty: UncertaintyLevel
    reuse_character: ReuseCharacter
    sensitivity_direction: SensitivityDirection
    comparison: StructuralComparison
    evidence_category: EvidenceCategory = EvidenceCategory.OBSERVED_IMPLEMENTATION_STRUCTURE


@dataclass(frozen=True)
class DeliveryCostAssumption:
    """A configurable hypothetical internal delivery cost, not a market rate."""
    engineering_cost_per_hour: Decimal
    evidence_category: EvidenceCategory = EvidenceCategory.SENSITIVITY_ASSUMPTION


@dataclass(frozen=True)
class DeliveryModel:
    category_hours: Mapping[DeliveryCategory, Decimal]
    reusable_labor_percentage: Decimal
    implementation_price: Decimal
    annual_recurring_fee: Decimal
    evidence_category: EvidenceCategory = EvidenceCategory.MODELED_ASSUMPTION

    @property
    def total_hours(self) -> Decimal:
        return sum(self.category_hours.values(), Decimal("0"))


@dataclass(frozen=True)
class DeliverySensitivityScenario:
    name: str
    category_hours: Mapping[DeliveryCategory, Decimal]
    reusable_labor_percentage: Decimal
    source_specific_labor_percentage: Decimal
    customer_specific_labor_percentage: Decimal
    automation_scope: str
    value_caveat: str
    verdict: DeliveryVerdict
    cost_assumption: DeliveryCostAssumption
    implementation_price: Decimal = BASELINE_HYPOTHESIS.implementation_price
    evidence_category: EvidenceCategory = EvidenceCategory.SENSITIVITY_ASSUMPTION

    @property
    def total_modeled_hours(self) -> Decimal:
        return sum(self.category_hours.values(), Decimal("0"))

    @property
    def delivery_labor_cost(self) -> Decimal:
        return self.total_modeled_hours * self.cost_assumption.engineering_cost_per_hour

    @property
    def modeled_contribution(self) -> Decimal:
        return self.implementation_price - self.delivery_labor_cost

    @property
    def contribution_margin(self) -> Decimal | None:
        if self.implementation_price <= 0:
            return None
        return self.modeled_contribution / self.implementation_price

    @property
    def modeled_break_even_implementation_price(self) -> Decimal:
        return self.delivery_labor_cost


@dataclass(frozen=True)
class DeliveryEconomicsReport:
    original_model: DeliveryModel
    evidence_categories: tuple[DeliveryEvidenceCategory, ...]
    sensitivity_scenarios: tuple[DeliverySensitivityScenario, ...]
    conclusions: tuple[str, ...]
    final_commercial_verdict: None = None


_ORIGINAL = {
    DeliveryCategory.DISCOVERY: 24, DeliveryCategory.API_VALIDATION: 36,
    DeliveryCategory.ADAPTERS: 104, DeliveryCategory.IDENTITY: 34,
    DeliveryCategory.ORCHESTRATION: 58, DeliveryCategory.RELIABILITY: 48,
    DeliveryCategory.EXCEPTIONS: 34, DeliveryCategory.DOCUMENTATION: 22,
    DeliveryCategory.QA: 54, DeliveryCategory.DEPLOYMENT: 16,
    DeliveryCategory.REWORK: 36,
}


def _hours(values: Mapping[DeliveryCategory, int]) -> Mapping[DeliveryCategory, Decimal]:
    """Freeze explicit assumptions; importantly, this accepts no implementation metrics."""
    if set(values) != set(DeliveryCategory):
        raise ValueError("every delivery category requires an explicit hour assumption")
    return MappingProxyType({key: Decimal(value) for key, value in values.items()})


ORIGINAL_MODEL = DeliveryModel(
    _hours(_ORIGINAL), BASELINE_HYPOTHESIS.reusable_core_percentage,
    BASELINE_HYPOTHESIS.implementation_price, BASELINE_HYPOTHESIS.annual_recurring_fee,
)


def _e(cat, refs, summary, uncertainty, reuse, direction, comparison):
    return DeliveryEvidenceCategory(cat, Decimal(_ORIGINAL[cat]), refs, summary,
                                    uncertainty, reuse, direction, comparison)


EVIDENCE_CATEGORIES = (
    _e(DeliveryCategory.DISCOVERY, ("Chapter 1 authority inventory", "Chapter 16 access profiles"), "Authority, permissions, native alternatives, sandbox and write safety are first-class discovery concerns.", UncertaintyLevel.HIGH, ReuseCharacter.MOSTLY_SPECIALIZED, SensitivityDirection.HIGHER_PLAUSIBLE, StructuralComparison.POSSIBLY_UNDERSTATED),
    _e(DeliveryCategory.API_VALIDATION, ("Chapter 16 clean/difficult/closed profiles", "CSV schema validation"), "Lookup, idempotency, export drift and sandbox availability materially change feasible scope.", UncertaintyLevel.HIGH, ReuseCharacter.MOSTLY_SPECIALIZED, SensitivityDirection.WIDE_RANGE, StructuralComparison.HIGHLY_VARIABLE),
    _e(DeliveryCategory.ADAPTERS, ("RiverLead and EstimateWorks boundaries", "CrewBoard, SupplyDesk, FieldTrack and LedgerPro", "BidForge, office completion and CSV export"), "Shared contracts exist, but every source and destination retains boundary-specific work.", UncertaintyLevel.HIGH, ReuseCharacter.MOSTLY_SPECIALIZED, SensitivityDirection.WIDE_RANGE, StructuralComparison.HIGHLY_VARIABLE),
    _e(DeliveryCategory.IDENTITY, ("canonical source references", "material/accounting mappings", "Chapter 15 weak contextual identifiers"), "Reusable identity shapes coexist with customer, material and accounting ambiguity.", UncertaintyLevel.HIGH, ReuseCharacter.MIXED, SensitivityDirection.HIGHER_PLAUSIBLE, StructuralComparison.POSSIBLY_UNDERSTATED),
    _e(DeliveryCategory.ORCHESTRATION, ("Chapters 3–8 workflow handoffs", "Chapter 15 approval and billing aggregation"), "Core transition contracts recur while eligibility, aggregation and approval semantics remain workflow/customer specific.", UncertaintyLevel.HIGH, ReuseCharacter.MIXED, SensitivityDirection.WIDE_RANGE, StructuralComparison.HIGHLY_VARIABLE),
    _e(DeliveryCategory.RELIABILITY, ("Chapters 9–10 retry/replay/reconciliation", "Chapter 13 alerts and scheduler overlap"), "Idempotency, acknowledgement, uncertain outcomes, replay, reconciliation and runtime recovery are visible structures.", UncertaintyLevel.MEDIUM, ReuseCharacter.STRONG_SHARED_COMPONENT, SensitivityDirection.HIGHER_PLAUSIBLE, StructuralComparison.POSSIBLY_UNDERSTATED),
    _e(DeliveryCategory.EXCEPTIONS, ("Chapter 11 lifecycle and routing", "aging and replay approval"), "A reusable exception contract still needs routing, ownership, resolution and aging setup.", UncertaintyLevel.MEDIUM, ReuseCharacter.MIXED, SensitivityDirection.HIGHER_PLAUSIBLE, StructuralComparison.POSSIBLY_UNDERSTATED),
    _e(DeliveryCategory.DOCUMENTATION, ("chapter boundary documentation", "Chapter 13 runbooks"), "Boundaries, recovery and support procedures are structurally necessary; document counts are not effort.", UncertaintyLevel.MEDIUM, ReuseCharacter.MIXED, SensitivityDirection.ORIGINAL_PLAUSIBLE, StructuralComparison.SUPPORTED_STRUCTURALLY),
    _e(DeliveryCategory.QA, ("scenario and failure fixtures", "cross-customer and access-profile regression tests"), "Failure, customer-variation and access-path coverage expands beyond happy-path feature tests.", UncertaintyLevel.MEDIUM, ReuseCharacter.MIXED, SensitivityDirection.HIGHER_PLAUSIBLE, StructuralComparison.POSSIBLY_UNDERSTATED),
    _e(DeliveryCategory.DEPLOYMENT, ("Chapter 13 config, secrets, health and readiness", "metrics, alerts, schedules and runbooks"), "Production integration introduces configuration, credentials, observability, scheduled work and recovery obligations.", UncertaintyLevel.MEDIUM, ReuseCharacter.MIXED, SensitivityDirection.HIGHER_PLAUSIBLE, StructuralComparison.POSSIBLY_UNDERSTATED),
    _e(DeliveryCategory.REWORK, ("No repository observation can measure reserve"), "Reserve is not observable from repository structure and remains only an assumption.", UncertaintyLevel.HIGH, ReuseCharacter.UNKNOWN, SensitivityDirection.WIDE_RANGE, StructuralComparison.NOT_EVALUABLE),
)


RATE = DeliveryCostAssumption(Decimal("100"))


def _scenario(name, values, reusable, source, customer, scope, caveat, verdict):
    return DeliverySensitivityScenario(name, _hours(values), Decimal(reusable), Decimal(source),
        Decimal(customer), scope, caveat, verdict, RATE)


def _changed(**updates: int) -> dict[DeliveryCategory, int]:
    values = dict(_ORIGINAL)
    lookup = {c.name.lower(): c for c in DeliveryCategory}
    values.update({lookup[key]: value for key, value in updates.items()})
    return values


SCENARIOS = (
    _scenario("Original baseline", _ORIGINAL, "52.8", "30", "17.2", "FULL", "Original hours retained; the cost rate and contribution are sensitivity assumptions.", DeliveryVerdict.THIN_DELIVERY),
    _scenario("Standardized / reusable", _changed(discovery=18, api_validation=24, adapters=72, identity=24, orchestration=42, reliability=34, exceptions=24, documentation=16, qa=42, deployment=14, rework=26), "65", "22", "13", "FULL", "Shared mechanisms reduce work, but customer delivery remains nonzero.", DeliveryVerdict.HEALTHY_DELIVERY),
    _scenario("Mixed customer", _changed(discovery=30, api_validation=42, adapters=106, identity=38, orchestration=62, reliability=50, exceptions=36, documentation=22, qa=58, deployment=18, rework=38), "48", "32", "20", "FULL", "Some access friction and specialized mapping leave contribution thin.", DeliveryVerdict.THIN_DELIVERY),
    _scenario("Bespoke customer", _changed(discovery=38, api_validation=48, adapters=138, identity=58, orchestration=94, reliability=58, exceptions=48, documentation=28, qa=72, deployment=22, rework=54), "34", "32", "34", "FULL_WITH_CUSTOM_RULES", "Manual completion, weak identity and billing aggregation increase specialized delivery.", DeliveryVerdict.UNATTRACTIVE_DELIVERY),
    _scenario("Difficult access", _changed(discovery=44, api_validation=68, adapters=118, identity=48, orchestration=68, reliability=72, exceptions=46, documentation=30, qa=76, deployment=28, rework=52), "38", "42", "20", "REDUCED", "Export drift, absent sandbox and human-assisted paths can cost more while automating less.", DeliveryVerdict.SCOPE_REDESIGN_REQUIRED),
    _scenario("Closed integration redesign", _changed(discovery=36, api_validation=40, adapters=54, identity=28, orchestration=34, reliability=30, exceptions=26, documentation=20, qa=34, deployment=10, rework=18), "42", "38", "20", "READ_ONLY_HUMAN_ASSISTED", "Lower delivery scope is not equal customer value; value economics must be revisited later.", DeliveryVerdict.SCOPE_REDESIGN_REQUIRED),
)


REPORT = DeliveryEconomicsReport(ORIGINAL_MODEL, EVIDENCE_CATEGORIES, SCENARIOS, (
    "Shared reliability, provenance, correlation, exception and runtime structures are positive reuse evidence.",
    "Adapters, mappings, workflow semantics, access constraints and production onboarding remain recurring delivery work.",
    "Observed implementation-unit reuse is not a labor reuse percentage.",
    "Shared code does not guarantee customer contribution: discovery, credentials, mappings, testing and setup remain.",
    "This is a delivery-side sensitivity, not a final commercial verdict; Chapters 18–20 remain open.",
))


def build_report() -> DeliveryEconomicsReport:
    return REPORT
