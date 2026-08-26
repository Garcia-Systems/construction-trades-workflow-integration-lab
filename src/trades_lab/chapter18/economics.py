"""Recurring support economics, kept separate from Chapter 17 delivery effort."""

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from trades_lab.chapter0 import BASELINE_HYPOTHESIS
from trades_lab.evidence import EvidenceCategory


class SupportCategory(StrEnum):
    ACCESS = "ACCESS"
    VENDOR_CHANGE = "VENDOR_CHANGE"
    MAPPING = "MAPPING"
    DELIVERY_FAILURE = "DELIVERY_FAILURE"
    RECONCILIATION = "RECONCILIATION"
    EXCEPTION_REVIEW = "EXCEPTION_REVIEW"
    CUSTOMER_RULE = "CUSTOMER_RULE"
    OBSERVABILITY = "OBSERVABILITY"
    CONFIGURATION = "CONFIGURATION"
    DOCUMENTATION_RUNBOOK = "DOCUMENTATION_RUNBOOK"


class SupportScope(StrEnum):
    INCLUDED_SUPPORT = "INCLUDED_SUPPORT"
    CHANGE_REQUEST = "CHANGE_REQUEST"
    COMMERCIAL_REVIEW = "COMMERCIAL_REVIEW"


class SupportPredictability(StrEnum):
    PREDICTABLE = "PREDICTABLE"
    VARIABLE = "VARIABLE"
    HIGH_VARIANCE = "HIGH_VARIANCE"


class SupportVerdict(StrEnum):
    HEALTHY_SUPPORT = "HEALTHY_SUPPORT"
    THIN_SUPPORT = "THIN_SUPPORT"
    INSUFFICIENT_SUPPORT = "INSUFFICIENT_SUPPORT"
    CHANGE_SCOPE_REQUIRED = "CHANGE_SCOPE_REQUIRED"
    HIGH_VARIANCE = "HIGH_VARIANCE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


@dataclass(frozen=True)
class SupportObligation:
    obligation_id: str
    name: str
    category: SupportCategory
    evidence_references: tuple[str, ...]
    customer_specific: bool
    vendor_specific: bool
    recurring: bool
    automation_possible: bool
    notes: str
    evidence_category: EvidenceCategory = EvidenceCategory.OBSERVED_IMPLEMENTATION_STRUCTURE


@dataclass(frozen=True)
class SupportEventAssumption:
    category: SupportCategory
    annual_events: Decimal
    average_hours_per_event: Decimal
    description: str = ""
    evidence_category: EvidenceCategory = EvidenceCategory.SENSITIVITY_ASSUMPTION

    @property
    def annual_hours(self) -> Decimal:
        return self.annual_events * self.average_hours_per_event


@dataclass(frozen=True)
class SupportCostAssumption:
    labor_cost_per_hour: Decimal
    other_recurring_direct_costs: Decimal = Decimal("0")
    evidence_category: EvidenceCategory = EvidenceCategory.SENSITIVITY_ASSUMPTION


@dataclass(frozen=True)
class SupportScopeExample:
    event_id: str
    name: str
    scope: SupportScope
    rationale: str
    evidence_category: EvidenceCategory = EvidenceCategory.MODELED_ASSUMPTION


@dataclass(frozen=True)
class SupportSensitivityScenario:
    scenario_id: str
    name: str
    event_assumptions: tuple[SupportEventAssumption, ...]
    cost_assumption: SupportCostAssumption
    recurring_fee: Decimal = BASELINE_HYPOTHESIS.annual_recurring_fee
    evidence_category: EvidenceCategory = EvidenceCategory.SENSITIVITY_ASSUMPTION

    @property
    def assumed_annual_support_hours(self) -> Decimal:
        return sum((event.annual_hours for event in self.event_assumptions), Decimal("0"))

    @property
    def support_labor_cost(self) -> Decimal:
        return self.assumed_annual_support_hours * self.cost_assumption.labor_cost_per_hour

    @property
    def other_recurring_direct_costs(self) -> Decimal:
        return self.cost_assumption.other_recurring_direct_costs

    @property
    def support_contribution(self) -> Decimal:
        return self.recurring_fee - self.support_labor_cost - self.other_recurring_direct_costs

    @property
    def contribution_margin(self) -> Decimal | None:
        return self.support_contribution / self.recurring_fee if self.recurring_fee > 0 else None

    @property
    def break_even_recurring_fee(self) -> Decimal:
        return self.support_labor_cost + self.other_recurring_direct_costs

    @property
    def hours_supported_before_fee_is_consumed(self) -> Decimal | None:
        rate = self.cost_assumption.labor_cost_per_hour
        available = self.recurring_fee - self.other_recurring_direct_costs
        return max(available, Decimal("0")) / rate if rate > 0 else None

    @property
    def hours_by_category(self) -> dict[SupportCategory, Decimal]:
        result: dict[SupportCategory, Decimal] = {}
        for event in self.event_assumptions:
            result[event.category] = result.get(event.category, Decimal("0")) + event.annual_hours
        return result

    @property
    def concentration(self) -> tuple[SupportCategory | None, Decimal]:
        hours = self.hours_by_category
        total = self.assumed_annual_support_hours
        if not hours or total == 0:
            return None, Decimal("0")
        category = max(hours, key=hours.__getitem__)
        return category, hours[category] / total

    @property
    def predictability(self) -> SupportPredictability:
        categories = set(self.hours_by_category)
        if SupportCategory.CUSTOMER_RULE in categories or SupportCategory.VENDOR_CHANGE in categories:
            return SupportPredictability.HIGH_VARIANCE
        if categories & {SupportCategory.ACCESS, SupportCategory.DELIVERY_FAILURE, SupportCategory.EXCEPTION_REVIEW}:
            return SupportPredictability.VARIABLE
        return SupportPredictability.PREDICTABLE

    @property
    def verdict(self) -> SupportVerdict:
        margin = self.contribution_margin
        if margin is None:
            return SupportVerdict.INSUFFICIENT_EVIDENCE
        if self.support_contribution < 0:
            return SupportVerdict.INSUFFICIENT_SUPPORT
        if self.predictability is SupportPredictability.HIGH_VARIANCE and margin < Decimal("0.25"):
            return SupportVerdict.HIGH_VARIANCE
        if margin < Decimal("0.30"):
            return SupportVerdict.THIN_SUPPORT
        return SupportVerdict.HEALTHY_SUPPORT


@dataclass(frozen=True)
class SupportEconomicsReport:
    annual_recurring_fee: Decimal
    recurring_fee_evidence_category: EvidenceCategory
    original_support_contribution: str
    obligations: tuple[SupportObligation, ...]
    scope_examples: tuple[SupportScopeExample, ...]
    scenarios: tuple[SupportSensitivityScenario, ...]
    positive_evidence: tuple[str, ...]
    negative_evidence: tuple[str, ...]
    conclusions: tuple[str, ...]
    delivery_economics_included: bool = False
    final_opportunity_verdict: None = None


def _ob(identifier: str, name: str, category: SupportCategory, refs: tuple[str, ...],
        customer: bool = False, vendor: bool = False, automation: bool = True,
        notes: str = "") -> SupportObligation:
    return SupportObligation(identifier, name, category, refs, customer, vendor, True, automation, notes)


OBLIGATIONS = (
    _ob("access", "Credential and access maintenance", SupportCategory.ACCESS,
        ("Chapter 13 credential validation and access-repair runbook", "Chapter 16 access profiles"), vendor=True),
    _ob("vendor-change", "Vendor and interface changes", SupportCategory.VENDOR_CHANGE,
        ("Chapter 16 strict CSV schema-drift detection", "Chapter 16 interface capability profiles"), vendor=True),
    _ob("mapping", "Mapping maintenance", SupportCategory.MAPPING,
        ("Chapter 6 material registry", "Chapter 8 accounting customer mappings"), customer=True, vendor=True),
    _ob("handoff", "Failed handoff and replay review", SupportCategory.DELIVERY_FAILURE,
        ("Chapter 9 retry exhaustion, uncertain outcomes, and replay",), vendor=True),
    _ob("reconciliation", "Recurring reconciliation investigation", SupportCategory.RECONCILIATION,
        ("Chapter 10 scheduled reconciliation and mismatch findings",)),
    _ob("exceptions", "Exception assignment and review", SupportCategory.EXCEPTION_REVIEW,
        ("Chapter 11 assignment, aging, resolution, and replay approval",), customer=True, automation=False),
    _ob("customer-rules", "Customer-specific workflow rules", SupportCategory.CUSTOMER_RULE,
        ("Chapter 15 approvals, kit expansion, manual completion, billing aggregation, and weak identity",), customer=True, automation=False),
    _ob("observability", "Alert, metric, and health review", SupportCategory.OBSERVABILITY,
        ("Chapter 13 health, metrics, alerts, and scheduled controls",)),
    _ob("configuration", "Configuration and deployment changes", SupportCategory.CONFIGURATION,
        ("Chapter 13 capability configuration, dependency settings, and schedules",), customer=True),
    _ob("runbooks", "Runbook and operational ownership maintenance", SupportCategory.DOCUMENTATION_RUNBOOK,
        ("Chapter 13 recovery runbooks", "Chapter 11 owner routing"), customer=True, automation=False,
        notes="Operational ownership only; no call-center operation is assumed."),
)


SCOPE_EXAMPLES = (
    SupportScopeExample("A", "Expired credential", SupportScope.INCLUDED_SUPPORT, "Routine access repair."),
    SupportScopeExample("B", "New material mapping", SupportScope.INCLUDED_SUPPORT, "Routine mapping update under the modeled boundary."),
    SupportScopeExample("C", "Retry exhaustion", SupportScope.INCLUDED_SUPPORT, "Operational investigation and controlled replay."),
    SupportScopeExample("D", "Vendor changes one field name", SupportScope.INCLUDED_SUPPORT, "Minor compatible repair; larger impact requires review."),
    SupportScopeExample("E", "Vendor replaces API with an incompatible version", SupportScope.COMMERCIAL_REVIEW, "Potential extraordinary event or reimplementation risk."),
    SupportScopeExample("F", "Customer adds a new approval workflow", SupportScope.CHANGE_REQUEST, "A new workflow is project scope."),
    SupportScopeExample("G", "Reconciliation mismatch", SupportScope.INCLUDED_SUPPORT, "Investigation is routine; major redesign is not."),
    SupportScopeExample("H", "New source system", SupportScope.CHANGE_REQUEST, "A new integration boundary is delivery work."),
)


RATE = SupportCostAssumption(Decimal("100"))


def _events(values: tuple[tuple[SupportCategory, str, str, str], ...]) -> tuple[SupportEventAssumption, ...]:
    """Construct explicit sensitivities; repository unit counts are deliberately absent."""
    return tuple(SupportEventAssumption(category, Decimal(count), Decimal(hours), description)
                 for category, count, hours, description in values)


SCENARIOS = (
    SupportSensitivityScenario("A", "Standardized / quiet", _events((
        (SupportCategory.MAPPING, "8", "1", "routine stable mapping updates"),
        (SupportCategory.RECONCILIATION, "12", "1", "monthly low-burden review"),
        (SupportCategory.OBSERVABILITY, "12", "1", "monthly health and alert review"),
        (SupportCategory.CONFIGURATION, "4", "2", "minor configuration maintenance"),
    )), RATE),
    SupportSensitivityScenario("B", "Mixed customer", _events((
        (SupportCategory.ACCESS, "4", "3", "periodic credential/access issue"),
        (SupportCategory.MAPPING, "16", "1.5", "normal mapping churn"),
        (SupportCategory.DELIVERY_FAILURE, "8", "2", "exhausted retry investigation"),
        (SupportCategory.RECONCILIATION, "12", "2", "regular mismatch review"),
        (SupportCategory.EXCEPTION_REVIEW, "12", "2", "moderate exception review"),
    )), RATE),
    SupportSensitivityScenario("C", "Bespoke / high support", _events((
        (SupportCategory.ACCESS, "8", "3", "access repair without sandbox"),
        (SupportCategory.MAPPING, "20", "2", "mapping and export churn"),
        (SupportCategory.DELIVERY_FAILURE, "10", "2", "uncertain handoff investigation"),
        (SupportCategory.RECONCILIATION, "12", "2", "weak-identity reconciliation"),
        (SupportCategory.EXCEPTION_REVIEW, "14", "2", "human-assisted exception review"),
        (SupportCategory.CUSTOMER_RULE, "7", "2", "manual completion and bespoke-rule maintenance"),
    )), RATE),
)


REPORT = SupportEconomicsReport(
    BASELINE_HYPOTHESIS.annual_recurring_fee, EvidenceCategory.MODELED_ASSUMPTION,
    BASELINE_HYPOTHESIS.support_contribution, OBLIGATIONS, SCOPE_EXAMPLES, SCENARIOS,
    ("Shared reliability framework", "Deterministic reconciliation", "Reusable exception workflow",
     "Common logging, health, alerts, and runbooks", "Standardized configuration, clean APIs, and stable mappings"),
    ("Unstable IDs and mapping churn", "Customer-specific approvals", "Export/schema drift and no sandbox",
     "Uncertain-write recovery", "Manual completion, closed interfaces, and high exception volume"),
    ("Recurring revenue is not pure contribution.",
     "A reusable core improves support scaling only while customer-specific obligations remain bounded.",
     "Chapter 17 initial delivery economics are separate; annual hours here are explicit sensitivities.",
     "Major future projects are change requests, extraordinary events, or reimplementation risks—not automatically routine support.",
     "No build-versus-buy or final opportunity verdict is produced."),
)


def build_report() -> SupportEconomicsReport:
    return REPORT
