"""Deterministic capstone: classify the opportunity without revising prior evidence."""

from dataclasses import dataclass
from enum import StrEnum

from trades_lab.chapter0 import BASELINE_HYPOTHESIS, BaselineHypothesis
from trades_lab.chapter17 import build_report as build_delivery_report
from trades_lab.chapter18 import build_report as build_support_report
from trades_lab.chapter19 import build_decisions
from trades_lab.evidence import EvidenceCategory


class FinalVerdict(StrEnum):
    PRODUCT_CANDIDATE = "PRODUCT_CANDIDATE"
    REPEATABLE_PROJECT = "REPEATABLE_PROJECT"
    BESPOKE_PROJECT = "BESPOKE_PROJECT"
    CONFIGURE_OR_BUY = "CONFIGURE_OR_BUY"
    NARROW_CUSTOM_EDGE = "NARROW_CUSTOM_EDGE"
    VALIDATE_IN_DISCOVERY = "VALIDATE_IN_DISCOVERY"
    NO_DEAL = "NO_DEAL"


VERDICT_MEANINGS = {
    FinalVerdict.PRODUCT_CANDIDATE: "Standardization, repeatable delivery and support make productization plausible; SaaS is not validated.",
    FinalVerdict.REPEATABLE_PROJECT: "A shared core exists, but discovery, adapters, configuration, testing and onboarding remain meaningful.",
    FinalVerdict.BESPOKE_PROJECT: "The solution can work, but customer-specific variation dominates repeatability.",
    FinalVerdict.CONFIGURE_OR_BUY: "A configurable, native or replacement alternative is more appropriate than custom development.",
    FinalVerdict.NARROW_CUSTOM_EDGE: "Use a bounded custom component only for the valuable gap left by other solutions.",
    FinalVerdict.VALIDATE_IN_DISCOVERY: "Critical customer, access or commercial unknowns prevent a responsible recommendation.",
    FinalVerdict.NO_DEAL: "Economics, access, alternatives or delivery/support burden undermine the custom opportunity.",
}


class EvidenceDirection(StrEnum):
    SUPPORTS_OPPORTUNITY = "SUPPORTS_OPPORTUNITY"
    WEAKENS_OPPORTUNITY = "WEAKENS_OPPORTUNITY"
    QUALIFIES_OPPORTUNITY = "QUALIFIES_OPPORTUNITY"
    NEUTRAL = "NEUTRAL"


class QualitativeRating(StrEnum):
    STRONG = "STRONG"
    MODERATE = "MODERATE"
    WEAK = "WEAK"
    UNKNOWN = "UNKNOWN"
    VARIABLE = "VARIABLE"


class DiscoveryGateResult(StrEnum):
    QUALIFIED_FOR_TECHNICAL_DISCOVERY = "QUALIFIED_FOR_TECHNICAL_DISCOVERY"
    INVESTIGATE_ALTERNATIVES = "INVESTIGATE_ALTERNATIVES"
    NARROW_SCOPE = "NARROW_SCOPE"
    NOT_QUALIFIED = "NOT_QUALIFIED"
    INSUFFICIENT_INFORMATION = "INSUFFICIENT_INFORMATION"


@dataclass(frozen=True)
class CapstoneEvidence:
    evidence_id: str
    chapter: int
    category: EvidenceCategory
    finding: str
    implication: str
    direction: EvidenceDirection


@dataclass(frozen=True)
class ScorecardEntry:
    dimension: str
    rating: QualitativeRating
    evidence_ids: tuple[str, ...]
    explanation: str


@dataclass(frozen=True)
class ScenarioVerdict:
    scenario_id: str
    name: str
    verdict: FinalVerdict
    evidence_ids: tuple[str, ...]
    reason: str


@dataclass(frozen=True)
class DiscoveryAnswers:
    systems: int | None = None
    repeated_handoffs: bool | None = None
    measurable_burden: bool | None = None
    meaningful_burden: bool | None = None
    supported_access: bool | None = None
    consequential_writes_reconcilable: bool | None = None
    stable_identity: bool | None = None
    mostly_configurable_rules: bool | None = None
    native_or_suite_covers_most: bool | None = None
    bounded_gap_remains: bool | None = None
    exception_owner: bool | None = None
    support_economics_fit: bool | None = None
    price_and_payback_tolerable: bool | None = None


@dataclass(frozen=True)
class CapstoneReport:
    original_hypothesis: BaselineHypothesis
    evidence: tuple[CapstoneEvidence, ...]
    scorecard: tuple[ScorecardEntry, ...]
    scenario_verdicts: tuple[ScenarioVerdict, ...]
    ideal_customer: tuple[str, ...]
    disqualifiers: tuple[str, ...]
    critical_unknowns: tuple[str, ...]
    structural_opportunity_class: FinalVerdict
    current_commercial_readiness: FinalVerdict
    overall_verdict: FinalVerdict
    overall_rule_reasons: tuple[str, ...]
    next_gate: str
    delivery_economics_source: object
    support_economics_source: object
    alternatives_source: tuple[object, ...]


def evidence_inventory() -> tuple[CapstoneEvidence, ...]:
    observed = EvidenceCategory.OBSERVED_IMPLEMENTATION_STRUCTURE
    return (
        CapstoneEvidence("C20-H0", 0, EvidenceCategory.MODELED_ASSUMPTION, "The original burden, value, price, fee, 466 hours, 52.8% reuse and payback are modeled.", "Commercial attractiveness remains unvalidated.", EvidenceDirection.QUALIFIES_OPPORTUNITY),
        CapstoneEvidence("C20-CORE", 2, observed, "Canonical identity and provenance recur across handoffs.", "A meaningful shared contract exists.", EvidenceDirection.SUPPORTS_OPPORTUNITY),
        CapstoneEvidence("C20-HANDOFF", 8, EvidenceCategory.OBSERVED_LAB_RESULT, "Correlation, idempotency and acknowledged handoffs operate in synthetic workflows.", "Substantial portions are technically feasible.", EvidenceDirection.SUPPORTS_OPPORTUNITY),
        CapstoneEvidence("C20-RELIABILITY", 10, observed, "Retry, replay, uncertain-outcome handling and reconciliation reuse shared mechanisms.", "Recovery is reusable infrastructure.", EvidenceDirection.SUPPORTS_OPPORTUNITY),
        CapstoneEvidence("C20-OPS", 13, observed, "Exceptions, health, metrics, schedules and runbooks create reusable operations mechanisms.", "Production concerns are visible rather than ignored.", EvidenceDirection.SUPPORTS_OPPORTUNITY),
        CapstoneEvidence("C20-VISIBILITY", 12, EvidenceCategory.OBSERVED_LAB_RESULT, "Management briefing is derived from shared operational evidence.", "Shared evidence can support visibility without new truth.", EvidenceDirection.SUPPORTS_OPPORTUNITY),
        CapstoneEvidence("C20-ADAPTERS", 14, observed, "Every source and destination still needs adapter and validation work.", "Repository reuse does not imply zero customer delivery.", EvidenceDirection.WEAKENS_OPPORTUNITY),
        CapstoneEvidence("C20-MAPPING", 14, observed, "Mapping mechanisms recur while mapping content remains customer-specific.", "Onboarding and maintenance remain real work.", EvidenceDirection.WEAKENS_OPPORTUNITY),
        CapstoneEvidence("C20-BESPOKE", 15, observed, "Tidewater adds approvals, kits, manual completion, billing aggregation and weak-identity rules without changing the core.", "Edge isolation helps, but bespoke workflow and identity burden can dominate.", EvidenceDirection.WEAKENS_OPPORTUNITY),
        CapstoneEvidence("C20-ACCESS-CLEAN", 16, EvidenceCategory.OBSERVED_LAB_RESULT, "Clean modeled access supports acknowledged, reconcilable automation.", "Access must be qualified before sale.", EvidenceDirection.QUALIFIES_OPPORTUNITY),
        CapstoneEvidence("C20-ACCESS-DIFFICULT", 16, observed, "Difficult access adds export drift, testing, human assistance and support burden.", "The same business workflow can become thinner while automating less.", EvidenceDirection.WEAKENS_OPPORTUNITY),
        CapstoneEvidence("C20-ACCESS-CLOSED", 16, EvidenceCategory.OBSERVED_LAB_RESULT, "Closed consequential write access redesigns automation to a human packet/read-only edge.", "A positive full-custom verdict is unavailable.", EvidenceDirection.WEAKENS_OPPORTUNITY),
        CapstoneEvidence("C20-DELIVERY", 17, EvidenceCategory.SENSITIVITY_ASSUMPTION, "Standardized delivery is healthy; baseline/mixed are thin; bespoke is unattractive; constrained access requires redesign.", "Economics are customer-sensitive, not a new measured estimate.", EvidenceDirection.QUALIFIES_OPPORTUNITY),
        CapstoneEvidence("C20-SUPPORT", 18, EvidenceCategory.SENSITIVITY_ASSUMPTION, "The $12,000 fee can fit bounded support, while high-variance rules and access can consume it.", "Support scope must be bounded contractually.", EvidenceDirection.QUALIFIES_OPPORTUNITY),
        CapstoneEvidence("C20-ALTERNATIVES", 19, EvidenceCategory.FICTIONAL_ALTERNATIVE_ASSUMPTION, "Modeled configuration, native, low-code and replacement choices can beat custom software.", "Screen alternatives before proposing custom work.", EvidenceDirection.WEAKENS_OPPORTUNITY),
    )


def build_scorecard() -> tuple[ScorecardEntry, ...]:
    return (
        ScorecardEntry("business-problem credibility", QualitativeRating.MODERATE, ("C20-H0", "C20-VISIBILITY"), "The workflow expresses plausible burden mechanisms, but no customer burden was measured."),
        ScorecardEntry("technical feasibility", QualitativeRating.STRONG, ("C20-HANDOFF", "C20-RELIABILITY"), "The synthetic implementation exercises consequential handoffs and recovery."),
        ScorecardEntry("reusable-core credibility", QualitativeRating.STRONG, ("C20-CORE", "C20-OPS"), "Identity, reliability, exceptions and runtime structures recur."),
        ScorecardEntry("customer-standardization", QualitativeRating.MODERATE, ("C20-MAPPING", "C20-BESPOKE"), "Variation can stay at edges, but its content and volume are consequential."),
        ScorecardEntry("access feasibility", QualitativeRating.VARIABLE, ("C20-ACCESS-CLEAN", "C20-ACCESS-CLOSED"), "Access changes safe scope from automation to human assistance."),
        ScorecardEntry("delivery-economic robustness", QualitativeRating.MODERATE, ("C20-DELIVERY",), "Chapter 17 sensitivities range from healthy to unattractive."),
        ScorecardEntry("support-economic robustness", QualitativeRating.MODERATE, ("C20-SUPPORT",), "Bounded support may fit; high variance may not."),
        ScorecardEntry("alternative-solution pressure", QualitativeRating.STRONG, ("C20-ALTERNATIVES",), "Several narrower modeled strategies can dominate custom work."),
        ScorecardEntry("sales/discovery uncertainty", QualitativeRating.UNKNOWN, ("C20-H0",), "No real buyer, sales motion, willingness to pay or acquisition evidence exists."),
    )


def scenario_verdicts() -> tuple[ScenarioVerdict, ...]:
    return (
        ScenarioVerdict("A", "Strong standardized customer", FinalVerdict.REPEATABLE_PROJECT, ("C20-CORE", "C20-DELIVERY", "C20-ACCESS-CLEAN"), "Common workflow and clean access support bounded but nonzero delivery."),
        ScenarioVerdict("B", "Broad-suite-fit customer", FinalVerdict.CONFIGURE_OR_BUY, ("C20-ALTERNATIVES",), "Modeled suite coverage makes a custom layer avoidable."),
        ScenarioVerdict("C", "Simple high-value gap", FinalVerdict.NARROW_CUSTOM_EDGE, ("C20-ALTERNATIVES", "C20-RELIABILITY"), "Only the bounded valuable gap warrants custom ownership."),
        ScenarioVerdict("D", "James River Mechanical baseline", FinalVerdict.VALIDATE_IN_DISCOVERY, ("C20-H0", "C20-DELIVERY", "C20-SUPPORT"), "The original verdict remains appropriate because its economics and access are modeled."),
        ScenarioVerdict("E", "Tidewater Specialty Services", FinalVerdict.BESPOKE_PROJECT, ("C20-BESPOKE", "C20-DELIVERY", "C20-SUPPORT"), "Specialized rules dominate and Chapter 17 makes full delivery unattractive without scope/economic validation."),
        ScenarioVerdict("F", "Difficult-access customer", FinalVerdict.VALIDATE_IN_DISCOVERY, ("C20-ACCESS-DIFFICULT", "C20-DELIVERY"), "Access evidence is required before fixing safe scope and economics."),
        ScenarioVerdict("G", "Closed consequential write", FinalVerdict.NARROW_CUSTOM_EDGE, ("C20-ACCESS-CLOSED",), "Only a read-only or human-assisted bounded edge is supportable."),
        ScenarioVerdict("H", "Low-burden contractor", FinalVerdict.NO_DEAL, ("C20-H0", "C20-ALTERNATIVES"), "Low recoverable burden cannot support custom delivery and support."),
    )


def discovery_gate(answers: DiscoveryAnswers) -> DiscoveryGateResult:
    values = tuple(answers.__dict__.values())
    if any(value is None for value in values):
        return DiscoveryGateResult.INSUFFICIENT_INFORMATION
    if answers.native_or_suite_covers_most and not answers.bounded_gap_remains:
        return DiscoveryGateResult.INVESTIGATE_ALTERNATIVES
    if not answers.meaningful_burden or not answers.measurable_burden or not answers.price_and_payback_tolerable or not answers.support_economics_fit:
        return DiscoveryGateResult.NOT_QUALIFIED
    if not answers.supported_access or not answers.consequential_writes_reconcilable or not answers.stable_identity:
        return DiscoveryGateResult.NARROW_SCOPE if answers.bounded_gap_remains else DiscoveryGateResult.NOT_QUALIFIED
    if answers.systems < 2 or not answers.repeated_handoffs or not answers.exception_owner:
        return DiscoveryGateResult.NOT_QUALIFIED
    if answers.native_or_suite_covers_most:
        return DiscoveryGateResult.NARROW_SCOPE
    return DiscoveryGateResult.QUALIFIED_FOR_TECHNICAL_DISCOVERY


IDEAL_CUSTOMER = (
    "multiple operational systems must remain", "repeated cross-system handoffs", "measured, meaningful coordination burden",
    "supported integration access and reconcilable writes", "stable or resolvable identity", "sufficient job/transaction volume",
    "limited native/configurable coverage", "variation bounded to configuration or edge logic",
    "management owns exceptions and process change", "burden supports delivery and bounded support",
)

DISQUALIFIERS = (
    "one platform or native integration already solves most of the workflow", "low volume or tiny recoverable burden",
    "closed consequential write access with no valuable narrow edge", "no reliable or resolvable identity",
    "unwillingness to change broken processes or own exceptions", "bespoke rules repeatedly require core changes",
    "support expectations exceed recurring economics",
)

CRITICAL_UNKNOWNS = (
    "actual customer burden", "actual recoverable value", "willingness to pay", "actual implementation hours",
    "actual support demand", "actual vendor API access", "actual native integration coverage", "actual sales-cycle length",
    "actual customer acquisition difficulty", "actual frequency of bespoke workflow variation",
)


def derive_structural_verdict(scorecard: tuple[ScorecardEntry, ...]) -> tuple[FinalVerdict, tuple[str, ...]]:
    ratings = {entry.dimension: entry.rating for entry in scorecard}
    if (ratings["technical feasibility"] is QualitativeRating.STRONG
            and ratings["reusable-core credibility"] is QualitativeRating.STRONG
            and ratings["customer-standardization"] in (QualitativeRating.MODERATE, QualitativeRating.STRONG)):
        return FinalVerdict.REPEATABLE_PROJECT, (
            "Technical feasibility and reusable-core credibility are STRONG.",
            "Customer work remains bounded but nontrivial, while access must be qualified.",
            "Product evidence is incomplete and alternatives must be screened.",
        )
    return FinalVerdict.VALIDATE_IN_DISCOVERY, ("The repeatable-project conditions are not established.",)


def build_report() -> CapstoneReport:
    evidence = evidence_inventory()
    scorecard = build_scorecard()
    structural, reasons = derive_structural_verdict(scorecard)
    return CapstoneReport(
        BASELINE_HYPOTHESIS, evidence, scorecard, scenario_verdicts(), IDEAL_CUSTOMER, DISQUALIFIERS,
        CRITICAL_UNKNOWNS, structural, FinalVerdict.VALIDATE_IN_DISCOVERY,
        FinalVerdict.VALIDATE_IN_DISCOVERY, reasons, "VALIDATE IN CUSTOMER DISCOVERY",
        build_delivery_report(), build_support_report(), build_decisions(),
    )


REPORT = build_report()
