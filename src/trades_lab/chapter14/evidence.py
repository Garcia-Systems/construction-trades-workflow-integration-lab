"""Curated evidence about the implementation that emerged in Chapters 0--13.

Units are an explanatory measuring device, not equal-sized work items and never hours.
The registry is intentionally explicit rather than a brittle source-code/AST counter.
"""

from collections import Counter
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from trades_lab.chapter0 import BASELINE_HYPOTHESIS


class ImplementationClassification(StrEnum):
    SHARED_CORE = "SHARED_CORE"
    SOURCE_SPECIFIC_ADAPTER = "SOURCE_SPECIFIC_ADAPTER"
    WORKFLOW_SPECIFIC_LOGIC = "WORKFLOW_SPECIFIC_LOGIC"
    CUSTOMER_SPECIFIC_RULE = "CUSTOMER_SPECIFIC_RULE"
    CONFIGURATION = "CONFIGURATION"
    VALIDATION = "VALIDATION"
    RELIABILITY = "RELIABILITY"
    EXCEPTION_HANDLING = "EXCEPTION_HANDLING"
    TESTING = "TESTING"
    SUPPORT_SURFACE = "SUPPORT_SURFACE"


class ReuseScope(StrEnum):
    CROSS_WORKFLOW = "CROSS_WORKFLOW"
    SAME_DOMAIN = "SAME_DOMAIN"
    CUSTOMER_SPECIFIC = "CUSTOMER_SPECIFIC"
    DESTINATION_SPECIFIC = "DESTINATION_SPECIFIC"
    SOURCE_SPECIFIC = "SOURCE_SPECIFIC"
    UNKNOWN = "UNKNOWN"


class EvidenceLevel(StrEnum):
    OBSERVED_REUSE = "OBSERVED_REUSE"
    OBSERVED_SPECIALIZATION = "OBSERVED_SPECIALIZATION"
    CANDIDATE_REUSE = "CANDIDATE_REUSE"
    MODELED_ONLY = "MODELED_ONLY"


class ReuseConfidence(StrEnum):
    STRENGTHENED = "STRENGTHENED"
    MIXED = "MIXED"
    WEAKENED = "WEAKENED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


@dataclass(frozen=True)
class ImplementationUnit:
    unit_id: str
    name: str
    introduced_chapter: int
    primary_classification: ImplementationClassification
    secondary_tags: tuple[ImplementationClassification, ...]
    reuse_scope: ReuseScope
    evidence_level: EvidenceLevel
    evidence_references: tuple[str, ...]
    used_by_chapters: tuple[int, ...]
    support_surface: bool
    notes: str
    negative_evidence: str | None = None


def _u(unit_id: str, name: str, chapter: int, primary: ImplementationClassification,
       scope: ReuseScope, level: EvidenceLevel, reference: str, used: tuple[int, ...],
       *, tags: tuple[ImplementationClassification, ...] = (), support: bool = False,
       notes: str = "", negative: str | None = None) -> ImplementationUnit:
    return ImplementationUnit(unit_id, name, chapter, primary, tags, scope, level,
                              (reference,), used, support, notes, negative)


C = ImplementationClassification
R = ReuseScope
E = EvidenceLevel

# Each entry names a concrete module or fixture. Chapter usage is curated evidence of use,
# not a claim that every line in that chapter imports the referenced symbol directly.
IMPLEMENTATION_INVENTORY = (
    _u("identity", "Canonical identity and source references", 2, C.SHARED_CORE, R.CROSS_WORKFLOW, E.OBSERVED_REUSE, "src/trades_lab/domain/identity.py", tuple(range(2, 14)), notes="Identity crosses implemented handoffs."),
    _u("provenance", "Immutable provenance model", 2, C.SHARED_CORE, R.CROSS_WORKFLOW, E.OBSERVED_REUSE, "src/trades_lab/domain/entities.py", tuple(range(2, 14))),
    _u("correlation", "Correlation mechanism", 3, C.SHARED_CORE, R.CROSS_WORKFLOW, E.OBSERVED_REUSE, "src/trades_lab/domain/events.py", tuple(range(3, 14))),
    _u("canonical-states", "Canonical workflow states and events", 2, C.SHARED_CORE, R.CROSS_WORKFLOW, E.OBSERVED_REUSE, "src/trades_lab/domain/states.py", (2,3,4,5,7,8,10,11,12,13)),
    _u("exception-contract", "Exception record contract", 2, C.EXCEPTION_HANDLING, R.CROSS_WORKFLOW, E.OBSERVED_REUSE, "src/trades_lab/domain/entities.py", tuple(range(2, 14)), tags=(C.SHARED_CORE,), support=True),
    _u("estimateworks-adapter", "EstimateWorks intake boundary", 3, C.SOURCE_SPECIFIC_ADAPTER, R.DESTINATION_SPECIFIC, E.OBSERVED_SPECIALIZATION, "src/trades_lab/chapter3/handoff.py", (3,), support=True),
    _u("job-boundary", "Accepted estimate job-system boundary", 4, C.SOURCE_SPECIFIC_ADAPTER, R.DESTINATION_SPECIFIC, E.OBSERVED_SPECIALIZATION, "src/trades_lab/chapter4/handoff.py", (4,10), support=True),
    _u("crewboard-adapter", "CrewBoard scheduling boundary", 5, C.SOURCE_SPECIFIC_ADAPTER, R.DESTINATION_SPECIFIC, E.OBSERVED_SPECIALIZATION, "src/trades_lab/chapter5/handoff.py", (5,10), support=True),
    _u("supplydesk-adapter", "SupplyDesk request boundary", 6, C.SOURCE_SPECIFIC_ADAPTER, R.DESTINATION_SPECIFIC, E.OBSERVED_SPECIALIZATION, "src/trades_lab/chapter6/handoff.py", (6,10), support=True),
    _u("fieldtrack-adapter", "FieldTrack observation adapter", 7, C.SOURCE_SPECIFIC_ADAPTER, R.SOURCE_SPECIFIC, E.OBSERVED_SPECIALIZATION, "src/trades_lab/chapter7/handoff.py", (7,10), support=True),
    _u("ledgerpro-adapter", "LedgerPro billing-work-item boundary", 8, C.SOURCE_SPECIFIC_ADAPTER, R.DESTINATION_SPECIFIC, E.OBSERVED_SPECIALIZATION, "src/trades_lab/chapter8/readiness.py", (8,10), support=True),
    _u("lead-eligibility", "Qualified-lead eligibility rule", 3, C.WORKFLOW_SPECIFIC_LOGIC, R.SAME_DOMAIN, E.OBSERVED_SPECIALIZATION, "src/trades_lab/chapter3/handoff.py", (3,)),
    _u("estimate-eligibility", "Accepted-estimate eligibility rule", 4, C.WORKFLOW_SPECIFIC_LOGIC, R.SAME_DOMAIN, E.OBSERVED_SPECIALIZATION, "src/trades_lab/chapter4/handoff.py", (4,)),
    _u("schedule-eligibility", "Scheduling eligibility rule", 5, C.WORKFLOW_SPECIFIC_LOGIC, R.SAME_DOMAIN, E.OBSERVED_SPECIALIZATION, "src/trades_lab/chapter5/handoff.py", (5,)),
    _u("mapping-registry", "Material mapping registry", 6, C.SHARED_CORE, R.SAME_DOMAIN, E.CANDIDATE_REUSE, "src/trades_lab/chapter6/handoff.py", (6,), tags=(C.CONFIGURATION,), support=True, notes="Mechanism is isolated; only one customer proves no cross-customer reuse."),
    _u("material-normalization", "Material unit normalization", 6, C.WORKFLOW_SPECIFIC_LOGIC, R.SAME_DOMAIN, E.CANDIDATE_REUSE, "src/trades_lab/chapter6/handoff.py", (6,), tags=(C.VALIDATION,)),
    _u("field-state-mapping", "FieldTrack state mapping", 7, C.WORKFLOW_SPECIFIC_LOGIC, R.SOURCE_SPECIFIC, E.OBSERVED_SPECIALIZATION, "src/trades_lab/domain/states.py", (7,), tags=(C.CONFIGURATION,), support=True),
    _u("field-progression", "Field progression and sequence rules", 7, C.WORKFLOW_SPECIFIC_LOGIC, R.SAME_DOMAIN, E.OBSERVED_SPECIALIZATION, "src/trades_lab/chapter7/handoff.py", (7,)),
    _u("invoice-gates", "Invoice-readiness gates", 8, C.WORKFLOW_SPECIFIC_LOGIC, R.SAME_DOMAIN, E.OBSERVED_SPECIALIZATION, "src/trades_lab/chapter8/readiness.py", (8,10,12)),
    _u("idempotency", "Stable idempotency mechanism", 4, C.RELIABILITY, R.CROSS_WORKFLOW, E.OBSERVED_REUSE, "src/trades_lab/chapter4/handoff.py", (4,5,6,7,8,9,10), tags=(C.SHARED_CORE,)),
    _u("acknowledgement", "Destination acknowledgement pattern", 4, C.RELIABILITY, R.CROSS_WORKFLOW, E.OBSERVED_REUSE, "src/trades_lab/chapter4/handoff.py", (4,5,6,8,9,10)),
    _u("retry-policy", "Bounded retry policy", 9, C.RELIABILITY, R.CROSS_WORKFLOW, E.OBSERVED_REUSE, "src/trades_lab/chapter9/reliability.py", (9,10,11,12,13), support=True),
    _u("uncertain-outcome", "Uncertain-write lookup handling", 9, C.RELIABILITY, R.DESTINATION_SPECIFIC, E.OBSERVED_SPECIALIZATION, "src/trades_lab/chapter9/reliability.py", (9,10,11,12,13), support=True, negative="Lookup capability and failure semantics vary by destination."),
    _u("replay", "Audited replay model", 9, C.RELIABILITY, R.CROSS_WORKFLOW, E.OBSERVED_REUSE, "src/trades_lab/chapter9/reliability.py", (9,10,11,12,13), support=True),
    _u("reconciliation", "Cross-system reconciliation checks", 10, C.VALIDATION, R.SAME_DOMAIN, E.CANDIDATE_REUSE, "src/trades_lab/chapter10/reconciliation.py", (10,11,12,13), tags=(C.SUPPORT_SURFACE,), support=True, negative="Relationship checks encode one-off workflow expectations."),
    _u("exception-workflow", "Owned exception-review workflow", 11, C.EXCEPTION_HANDLING, R.CROSS_WORKFLOW, E.OBSERVED_REUSE, "src/trades_lab/chapter11/workflow.py", (11,12,13), support=True),
    _u("briefing", "Operational briefing aggregator", 12, C.SUPPORT_SURFACE, R.SAME_DOMAIN, E.CANDIDATE_REUSE, "src/trades_lab/chapter12/briefing.py", (12,13), support=True),
    _u("health", "Runtime health and capability model", 13, C.RELIABILITY, R.CROSS_WORKFLOW, E.CANDIDATE_REUSE, "src/trades_lab/chapter13/runtime.py", (13,), support=True, notes="One runtime observes several capabilities, but only one chapter/runtime exists."),
    _u("metrics", "Bounded operational metrics", 13, C.SUPPORT_SURFACE, R.SAME_DOMAIN, E.CANDIDATE_REUSE, "src/trades_lab/chapter13/runtime.py", (13,), support=True),
    _u("alerts", "Operational alert rules", 13, C.SUPPORT_SURFACE, R.CUSTOMER_SPECIFIC, E.MODELED_ONLY, "src/trades_lab/chapter13/runtime.py", (13,), tags=(C.CONFIGURATION,), support=True),
    _u("scheduler", "Scheduled run records and overlap control", 13, C.RELIABILITY, R.CROSS_WORKFLOW, E.CANDIDATE_REUSE, "src/trades_lab/chapter13/runtime.py", (13,), support=True),
    _u("runbooks", "Recovery runbook definitions", 13, C.SUPPORT_SURFACE, R.SAME_DOMAIN, E.MODELED_ONLY, "src/trades_lab/chapter13/runtime.py", (13,), support=True),
    _u("credentials", "Credential references", 13, C.CONFIGURATION, R.CUSTOMER_SPECIFIC, E.MODELED_ONLY, "src/trades_lab/chapter13/runtime.py", (13,), tags=(C.SUPPORT_SURFACE,), support=True),
    _u("jrm-materials", "James River Mechanical material mappings", 6, C.CUSTOMER_SPECIFIC_RULE, R.CUSTOMER_SPECIFIC, E.OBSERVED_SPECIALIZATION, "src/trades_lab/fixtures/chapter6.py", (6,), tags=(C.CONFIGURATION,C.SUPPORT_SURFACE), support=True),
    _u("jrm-routing", "James River exception routing", 11, C.CUSTOMER_SPECIFIC_RULE, R.CUSTOMER_SPECIFIC, E.MODELED_ONLY, "src/trades_lab/chapter11/workflow.py", (11,12,13), tags=(C.CONFIGURATION,C.SUPPORT_SURFACE), support=True),
    _u("jrm-approval", "Customer approval policy", 8, C.CUSTOMER_SPECIFIC_RULE, R.CUSTOMER_SPECIFIC, E.OBSERVED_SPECIALIZATION, "src/trades_lab/fixtures/chapter8.py", (8,), tags=(C.CONFIGURATION,), support=True),
    _u("jrm-thresholds", "Alert and aging thresholds", 12, C.CUSTOMER_SPECIFIC_RULE, R.CUSTOMER_SPECIFIC, E.MODELED_ONLY, "src/trades_lab/fixtures/chapter12.py", (12,13), tags=(C.CONFIGURATION,C.SUPPORT_SURFACE), support=True),
    _u("schedule-config", "Schedule intervals", 13, C.CONFIGURATION, R.CUSTOMER_SPECIFIC, E.MODELED_ONLY, "src/trades_lab/fixtures/chapter13.py", (13,), tags=(C.SUPPORT_SURFACE,), support=True),
    _u("capability-config", "Runtime capability configuration", 13, C.CONFIGURATION, R.CUSTOMER_SPECIFIC, E.MODELED_ONLY, "src/trades_lab/chapter13/runtime.py", (13,), support=True),
    _u("mapping-tests", "Material boundary behavior tests", 6, C.TESTING, R.SAME_DOMAIN, E.OBSERVED_SPECIALIZATION, "tests/test_chapter6_materials_handoff.py", (6,)),
    _u("reliability-tests", "Reliability behavior tests", 9, C.TESTING, R.CROSS_WORKFLOW, E.OBSERVED_REUSE, "tests/test_chapter9_failure_retry_replay.py", (9,10,11,13)),
    _u("runtime-tests", "Runtime operability tests", 13, C.TESTING, R.SAME_DOMAIN, E.OBSERVED_SPECIALIZATION, "tests/test_chapter13_production_runtime.py", (13,)),
    _u("strategy-rules", "Build/buy/configure decision rules", 19, C.WORKFLOW_SPECIFIC_LOGIC, R.SAME_DOMAIN, E.OBSERVED_SPECIALIZATION, "src/trades_lab/chapter19/decision.py", (19,), notes="Explainable scenario strategy selection; not shared integration core."),
    _u("alternative-config", "Fictional alternative assumptions", 19, C.CONFIGURATION, R.CUSTOMER_SPECIFIC, E.MODELED_ONLY, "src/trades_lab/chapter19/decision.py", (19,), notes="Synthetic capabilities, never vendor facts."),
    _u("decision-tests", "Strategy decision behavior tests", 19, C.TESTING, R.SAME_DOMAIN, E.OBSERVED_SPECIALIZATION, "tests/test_chapter19_decisions.py", (19,)),
)


@dataclass(frozen=True)
class ChangeScenario:
    scenario_id: str
    unchanged_units: tuple[str, ...]
    changed_or_added_units: tuple[str, ...]
    support_surface_change: str
    interpretation: str


CHANGE_SCENARIOS = (
    ChangeScenario("NEW_CUSTOMER_MATERIAL_MAPPING", ("mapping-registry",),
        ("new customer mapping configuration", "mapping tests"), "GROWS",
        "The mechanism stays stable; customer-specific content and its support obligation do not."),
    ChangeScenario("REPLACE_FIELDTRACK", ("canonical-states", "invoice-gates"),
        ("source adapter", "source status mapping", "adapter tests"), "CHANGES",
        "Canonical/downstream concepts remain, but source semantics require significant specialization."),
    ChangeScenario("NEW_CONSEQUENTIAL_HANDOFF", ("correlation", "idempotency", "acknowledgement", "retry-policy"),
        ("workflow eligibility", "destination adapter tests"), "USES_EXISTING_CORE",
        "Existing implemented handoffs demonstrate the reliability pattern without a Chapter 15 feature."),
)


@dataclass(frozen=True)
class ImplementationEvidenceReport:
    units: tuple[ImplementationUnit, ...]
    classification_counts: dict[ImplementationClassification, int]
    reuse_scope_counts: dict[ReuseScope, int]
    evidence_counts: dict[EvidenceLevel, int]
    support_surface_count: int
    support_surface_by_primary: dict[ImplementationClassification, int]
    observed_cross_workflow_count: int
    observed_cross_workflow_ratio: Decimal
    ratio_label: str
    original_modeled_reusable_effort: Decimal
    reuse_confidence: ReuseConfidence
    negative_evidence: tuple[str, ...]


def _complete_counts(enum: type[StrEnum], values: list[StrEnum]) -> dict:
    counted = Counter(values)
    return {member: counted[member] for member in enum}


def build_report() -> ImplementationEvidenceReport:
    units = IMPLEMENTATION_INVENTORY
    observed = sum(u.reuse_scope is R.CROSS_WORKFLOW and u.evidence_level is E.OBSERVED_REUSE for u in units)
    support = tuple(u for u in units if u.support_surface)
    specialized = sum(u.evidence_level is E.OBSERVED_SPECIALIZATION for u in units)
    # Explainable and deliberately not tuned for a positive result: meaningful reuse exists,
    # but specialization is at least as numerous and support remains substantial.
    confidence = ReuseConfidence.MIXED if observed >= 5 and specialized >= observed else (
        ReuseConfidence.STRENGTHENED if observed >= 5 else ReuseConfidence.INSUFFICIENT_EVIDENCE)
    return ImplementationEvidenceReport(
        units, _complete_counts(C, [u.primary_classification for u in units]),
        _complete_counts(R, [u.reuse_scope for u in units]),
        _complete_counts(E, [u.evidence_level for u in units]), len(support),
        _complete_counts(C, [u.primary_classification for u in support]), observed,
        (Decimal(observed) / Decimal(len(units))).quantize(Decimal("0.001")),
        "Observed implementation-unit cross-workflow reuse ratio",
        BASELINE_HYPOTHESIS.reusable_core_percentage, confidence,
        tuple(u.negative_evidence for u in units if u.negative_evidence))


def reuse_matrix(units: tuple[ImplementationUnit, ...] = IMPLEMENTATION_INVENTORY) -> str:
    chapters = tuple(range(2, 14))
    header = f"{'UNIT':<32} " + " ".join(f"CH{x}" for x in chapters)
    rows = [header]
    for unit in units:
        rows.append(f"{unit.name[:32]:<32} " + " ".join(" X " if x in unit.used_by_chapters else " . " for x in chapters))
    return "\n".join(rows)
