"""Explainable Chapter 19 solution-strategy comparisons.

Alternatives are synthetic.  Rules deliberately choose the smallest adequate
solution rather than converting qualitative evidence into a numeric score.
"""

from dataclasses import dataclass
from enum import StrEnum


class SolutionStrategy(StrEnum):
    DO_NOTHING = "DO_NOTHING"
    PROCESS_CHANGE = "PROCESS_CHANGE"
    CONFIGURE_EXISTING = "CONFIGURE_EXISTING"
    NATIVE_INTEGRATION = "NATIVE_INTEGRATION"
    LOW_CODE_INTEGRATION = "LOW_CODE_INTEGRATION"
    NARROW_CUSTOM_EDGE = "NARROW_CUSTOM_EDGE"
    CUSTOM_INTEGRATION_LAYER = "CUSTOM_INTEGRATION_LAYER"
    PLATFORM_REPLACEMENT = "PLATFORM_REPLACEMENT"


class QualitativeRating(StrEnum):
    STRONG = "STRONG"
    MODERATE = "MODERATE"
    WEAK = "WEAK"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNKNOWN = "UNKNOWN"


class EvidenceStatus(StrEnum):
    OBSERVED_LAB_EVIDENCE = "OBSERVED_LAB_EVIDENCE"
    MODELED_ALTERNATIVE_ASSUMPTION = "MODELED_ALTERNATIVE_ASSUMPTION"
    SENSITIVITY_ASSUMPTION = "SENSITIVITY_ASSUMPTION"


class DecisionDimension(StrEnum):
    WORKFLOW_COVERAGE = "workflow coverage"
    EXISTING_SYSTEM_FIT = "fit with existing systems"
    CUSTOM_FLEXIBILITY = "custom workflow flexibility"
    ACCESS_DEPENDENCY = "integration-access dependency"
    IMPLEMENTATION_BURDEN = "implementation burden"
    MIGRATION_BURDEN = "migration burden"
    SUPPORT_BURDEN = "ongoing support burden"
    RELIABILITY_RECOVERY = "reliability/recovery capability"
    EXCEPTION_HANDLING = "exception-handling capability"
    TIME_TO_VALUE = "time-to-value"
    VENDOR_DEPENDENCY = "vendor dependency"
    REVERSIBILITY = "reversibility"
    ORGANIZATIONAL_CHANGE = "organizational change required"


@dataclass(frozen=True)
class EvidenceStatement:
    status: EvidenceStatus
    statement: str


@dataclass(frozen=True)
class SolutionAlternative:
    alternative_id: str
    name: str
    strategy: SolutionStrategy
    workflow_coverage: tuple[str, ...]
    strengths: tuple[str, ...]
    limitations: tuple[str, ...]
    assumptions: tuple[EvidenceStatement, ...]


@dataclass(frozen=True)
class DecisionDimensionRating:
    dimension: DecisionDimension
    rating: QualitativeRating
    evidence: EvidenceStatement


@dataclass(frozen=True)
class AlternativeEvaluation:
    alternative_id: str
    strategy: SolutionStrategy
    ratings: tuple[DecisionDimensionRating, ...]
    evidence: tuple[EvidenceStatement, ...]
    disqualifiers: tuple[str, ...] = ()


@dataclass(frozen=True)
class ContractorScenario:
    scenario_id: str
    name: str
    facts: tuple[str, ...]
    preferred: SolutionStrategy
    reasons: tuple[str, ...]
    disqualified: tuple[tuple[SolutionStrategy, str], ...] = ()
    custom_technically_feasible: bool = False


@dataclass(frozen=True)
class SolutionDecision:
    scenario_id: str
    recommended_strategy: SolutionStrategy
    considered_alternatives: tuple[AlternativeEvaluation, ...]
    reasons: tuple[str, ...]
    unresolved_questions: tuple[str, ...]
    final_opportunity_verdict: None = None


MODELED = EvidenceStatus.MODELED_ALTERNATIVE_ASSUMPTION
OBSERVED = EvidenceStatus.OBSERVED_LAB_EVIDENCE

ALTERNATIVES = (
    SolutionAlternative("none", "No technology change", SolutionStrategy.DO_NOTHING,
        ("current manual workflow",), ("no implementation or migration",),
        ("manual burden remains",), (EvidenceStatement(MODELED, "Current human process is adequate when burden is low."),)),
    SolutionAlternative("process", "Process change", SolutionStrategy.PROCESS_CHANGE,
        ("human procedures and controls",), ("low technology dependency", "reversible"),
        ("retains manual execution",), (EvidenceStatement(MODELED, "A changed procedure can address the modeled gap."),)),
    SolutionAlternative("configure", "Existing-platform configuration", SolutionStrategy.CONFIGURE_EXISTING,
        ("rules already owned by a current platform",), ("avoids migration", "low custom maintenance"),
        ("bounded by installed capabilities",), (EvidenceStatement(MODELED, "The installed platform exposes suitable configuration."),)),
    SolutionAlternative("vendor-connect", "VendorConnect", SolutionStrategy.NATIVE_INTEGRATION,
        ("selected important handoffs",), ("vendor-supported", "lower custom maintenance"),
        ("limited transformation", "limited cross-vendor scope"), (EvidenceStatement(MODELED, "Fictional VendorConnect safely supports the selected handoff."),)),
    SolutionAlternative("flow-bridge", "FlowBridge", SolutionStrategy.LOW_CODE_INTEGRATION,
        ("simple triggers, actions, and transformations",), ("connectors", "lower initial custom-code requirement"),
        ("modeled strain under uncertain writes, reconciliation, and custom semantics",), (EvidenceStatement(MODELED, "Fictional FlowBridge supports clean writes and modest transformations."),)),
    SolutionAlternative("narrow-edge", "Narrow custom edge", SolutionStrategy.NARROW_CUSTOM_EDGE,
        ("one bounded identity, reconciliation, briefing, validation, or handoff gap",),
        ("limits custom scope", "can preserve existing systems"), ("still requires ownership and support",),
        (EvidenceStatement(OBSERVED, "Lab components demonstrate identity normalization, reconciliation, briefing, and validated human packets as separable edges."),)),
    SolutionAlternative("custom-layer", "Custom Integration Layer", SolutionStrategy.CUSTOM_INTEGRATION_LAYER,
        ("multi-system workflow and customer semantics",), ("explicit identity, recovery, reconciliation, and exceptions",),
        ("delivery and recurring support burden", "depends on supported access"),
        (EvidenceStatement(OBSERVED, "Chapters 2-16 expose canonical identity, idempotency, uncertain-write recovery, reconciliation, exceptions, variation, and access requirements."),
         EvidenceStatement(OBSERVED, "Chapter 17 exposes discovery, adapter, mapping, workflow, reliability, testing, access, and production delivery work."),
         EvidenceStatement(OBSERVED, "Chapter 18 exposes credential, mapping, reconciliation, exception, vendor-change, alert, runbook, and customer-rule support obligations."),)),
    SolutionAlternative("contractor-suite", "ContractorSuite", SolutionStrategy.PLATFORM_REPLACEMENT,
        ("estimating", "job management", "scheduling", "field workflow", "billing integration", "reporting"),
        ("broad modeled coverage", "reduces fragmentation"),
        ("migration, retraining, disruption, change-management, and vendor dependency", "less unusual-workflow flexibility"),
        (EvidenceStatement(MODELED, "Fictional ContractorSuite covers an industry-standard workflow."),)),
)

SCENARIOS = (
    ContractorScenario("A", "Standardized contractor", ("broad suite coverage: STRONG", "custom differentiation: WEAK", "migration feasibility: MODERATE"), SolutionStrategy.PLATFORM_REPLACEMENT,
        ("Fragmentation is the main problem and modeled suite coverage is broad.", "Migration is feasible; a wider custom layer adds avoidable support."), custom_technically_feasible=True),
    ContractorScenario("B", "Strong native integration", ("native workflow coverage: STRONG", "custom transformation requirement: WEAK"), SolutionStrategy.NATIVE_INTEGRATION,
        ("VendorConnect covers the important handoff.", "Narrower coverage is adequate and carries less custom maintenance."), custom_technically_feasible=True),
    ContractorScenario("C", "Simple unsupported handoff", ("clean APIs", "complex reconciliation: NO", "custom semantics: LOW"), SolutionStrategy.LOW_CODE_INTEGRATION,
        ("One safe transfer needs only modest transformation.", "Full custom reliability machinery is not required by the modeled handoff."), custom_technically_feasible=True),
    ContractorScenario("D", "One important custom gap", ("existing stack coverage: STRONG", "remaining gap: IDENTITY + RECONCILIATION"), SolutionStrategy.NARROW_CUSTOM_EDGE,
        ("Products cover most operations.", "A bounded identity and reconciliation edge avoids replacement and full-layer support."), custom_technically_feasible=True),
    ContractorScenario("E", "Fragmented multi-system contractor", ("multiple authoritative systems: YES", "cross-system workflow: YES", "custom semantics: YES", "integration access: WORKABLE", "recoverable burden: MEANINGFUL"), SolutionStrategy.CUSTOM_INTEGRATION_LAYER,
        ("Several authoritative systems must remain and native coverage is incomplete.", "Workable access, meaningful burden, and customer-specific semantics require recoverable orchestration.")),
    ContractorScenario("F", "Bespoke customer", ("unusual approvals and kits", "manual completion", "billing aggregation", "weak identifiers", "alternative coverage: WEAK"), SolutionStrategy.PROCESS_CHANGE,
        ("Modeled replacement and automation coverage do not safely resolve weak identity.", "Stabilizing identifiers and completion procedure precedes custom automation."),
        ((SolutionStrategy.PLATFORM_REPLACEMENT, "Required unusual workflow is unsupported under the modeled suite assumption."),)),
    ContractorScenario("G", "Closed critical write access", ("critical write access: NONE", "read/export access: LIMITED"), SolutionStrategy.NARROW_CUSTOM_EDGE,
        ("A read-only validated human handoff packet remains useful.", "Unsupported consequential automation must not be simulated."),
        ((SolutionStrategy.CUSTOM_INTEGRATION_LAYER, "Critical consequential write requires unsupported access."),)),
    ContractorScenario("H", "Small contractor / low burden", ("few jobs", "recoverable operational burden: LOW", "manual process: ADEQUATE"), SolutionStrategy.DO_NOTHING,
        ("The modeled burden is smaller than the organizational and support surface of automation.", "A simple manual process remains adequate."), custom_technically_feasible=True),
)

DISCOVERY_QUESTIONS = (
    "Does current software already provide or configure the required feature?",
    "Is a supported native integration licensed, and what workflow does it cover?",
    "Which APIs, exports, sandboxes, lookups, and consequential writes are actually available?",
    "Can the workflow or identifier practice be changed instead?",
    "What are actual coordination burden and exception volume?",
    "What are migration cost, retraining, disruption, and lock-in?",
    "What ongoing support ownership and vendor-change exposure are acceptable?",
    "What outcome does the customer value enough to pay for?",
)


def _rating(strategy: SolutionStrategy, dimension: DecisionDimension, scenario: ContractorScenario) -> QualitativeRating:
    if strategy is scenario.preferred:
        return QualitativeRating.STRONG
    if strategy is SolutionStrategy.CUSTOM_INTEGRATION_LAYER and scenario.custom_technically_feasible:
        return QualitativeRating.MODERATE
    if strategy is SolutionStrategy.NARROW_CUSTOM_EDGE and scenario.preferred in (SolutionStrategy.PROCESS_CHANGE, SolutionStrategy.CUSTOM_INTEGRATION_LAYER):
        return QualitativeRating.MODERATE
    if strategy in (SolutionStrategy.DO_NOTHING, SolutionStrategy.PROCESS_CHANGE) and dimension is DecisionDimension.ACCESS_DEPENDENCY:
        return QualitativeRating.NOT_APPLICABLE
    return QualitativeRating.WEAK


def evaluate_scenario(scenario: ContractorScenario) -> SolutionDecision:
    disqualified = dict(scenario.disqualified)
    evaluations = []
    for alternative in ALTERNATIVES:
        status = OBSERVED if alternative.strategy in (SolutionStrategy.NARROW_CUSTOM_EDGE, SolutionStrategy.CUSTOM_INTEGRATION_LAYER) else MODELED
        ratings = tuple(DecisionDimensionRating(d, _rating(alternative.strategy, d, scenario),
            EvidenceStatement(status, f"Qualitative fit for {scenario.name}; no numeric score.")) for d in DecisionDimension)
        evaluations.append(AlternativeEvaluation(alternative.alternative_id, alternative.strategy, ratings,
            alternative.assumptions, (disqualified[alternative.strategy],) if alternative.strategy in disqualified else ()))
    if scenario.preferred in disqualified:
        raise ValueError("A disqualified strategy cannot be recommended")
    return SolutionDecision(scenario.scenario_id, scenario.preferred, tuple(evaluations), scenario.reasons, DISCOVERY_QUESTIONS)


def build_decisions() -> tuple[SolutionDecision, ...]:
    return tuple(evaluate_scenario(scenario) for scenario in SCENARIOS)


def decision_matrix(decisions: tuple[SolutionDecision, ...] | None = None) -> str:
    decisions = decisions or build_decisions()
    columns = (SolutionStrategy.CONFIGURE_EXISTING, SolutionStrategy.NATIVE_INTEGRATION,
        SolutionStrategy.LOW_CODE_INTEGRATION, SolutionStrategy.NARROW_CUSTOM_EDGE,
        SolutionStrategy.CUSTOM_INTEGRATION_LAYER, SolutionStrategy.PLATFORM_REPLACEMENT)
    header = "Scenario | Configure | Native | Low-code | Narrow custom | Full custom | Replace | Recommended"
    rows = [header, "-" * len(header)]
    for decision in decisions:
        by_strategy = {e.strategy: e for e in decision.considered_alternatives}
        values = []
        for strategy in columns:
            evaluation = by_strategy[strategy]
            values.append("DISQUALIFIED" if evaluation.disqualifiers else evaluation.ratings[0].rating.value)
        rows.append(" | ".join((decision.scenario_id, *values, decision.recommended_strategy.value)))
    return "\n".join(rows)


DECISIONS = build_decisions()
