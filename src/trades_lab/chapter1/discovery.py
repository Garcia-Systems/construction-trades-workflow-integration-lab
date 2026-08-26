"""Executable discovery evidence for Chapter 1.

The records in this module describe a synthetic environment.  The behavior of
validation and readiness evaluation is observable; vendor capabilities are not.
"""

from dataclasses import dataclass, replace
from enum import StrEnum


class Capability(StrEnum):
    NONE = "NO"
    LIMITED = "LIMITED"
    SUPPORTED = "YES"
    UNKNOWN = "UNKNOWN"


class AuthorityRole(StrEnum):
    AUTHORITATIVE = "AUTHORITATIVE"
    REFERENCE = "CONSUMING / REFERENCE ONLY"
    DERIVED = "DERIVED INTEGRATION STATE"
    NOT_APPLICABLE = "NOT APPLICABLE"


class AccessRisk(StrEnum):
    CLEAN = "CLEAN"
    CONSTRAINED = "CONSTRAINED"
    FRAGILE = "FRAGILE"
    CLOSED = "CLOSED"
    UNKNOWN = "UNKNOWN"


class NativeIntegrationStatus(StrEnum):
    NONE_KNOWN = "NONE_KNOWN"
    PARTIAL = "PARTIAL"
    POSSIBLE = "POSSIBLE"
    SUFFICIENT = "SUFFICIENT"
    UNKNOWN = "UNKNOWN"


class QuestionStatus(StrEnum):
    OPEN = "OPEN"
    ANSWERED = "ANSWERED"
    BLOCKING = "BLOCKING"


class TransitionRisk(StrEnum):
    LOW_RISK = "LOW_RISK"
    CONSEQUENTIAL_WRITE = "CONSEQUENTIAL_WRITE"


class Readiness(StrEnum):
    READY = "READY"
    READY_WITH_CONSTRAINTS = "READY_WITH_CONSTRAINTS"
    BLOCKED = "BLOCKED"
    UNKNOWN = "UNKNOWN"


class ApprovalKnowledge(StrEnum):
    NOT_REQUIRED = "NOT_REQUIRED"
    DOCUMENTED = "DOCUMENTED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class DiscoveryQuestion:
    id: str
    system: str
    question: str
    importance: str
    status: QuestionStatus
    automation_impact: str


@dataclass(frozen=True)
class SystemDiscovery:
    name: str
    business_purpose: tuple[str, ...]
    authoritative_for: tuple[str, ...]
    read_capability: Capability
    write_capability: Capability
    interface_types: tuple[str, ...]
    event_support: Capability
    export_support: Capability
    sandbox_available: Capability
    identifier_quality: str
    identifier_stability: str
    documentation_quality: str
    expected_latency: str
    credential_type: str
    write_approval: ApprovalKnowledge
    known_failure_behavior: tuple[str, ...]
    native_integration_capability: str
    integration_confidence: str
    unresolved_question_ids: tuple[str, ...]
    access_risk: AccessRisk


@dataclass(frozen=True)
class ProposedTransition:
    key: str
    label: str
    source_system: str
    destination_system: str
    source_concept: str
    destination_concept: str
    risk: TransitionRisk
    native_integration: NativeIntegrationStatus
    question_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class ReadinessResult:
    transition: str
    status: Readiness
    reasons: tuple[str, ...]
    native_integration: NativeIntegrationStatus


CORE_CONCEPTS = (
    "lead status", "estimate acceptance", "job existence", "crew assignment",
    "field completion", "invoice state", "payment state",
)

QUESTIONS = (
    DiscoveryQuestion("DISC-001", "EstimateWorks", "Does EstimateWorks emit an immutable accepted-estimate version?", "HIGH", QuestionStatus.OPEN, "Constrains accepted estimate → job"),
    DiscoveryQuestion("DISC-002", "CrewBoard", "Can externally created jobs be safely deduplicated with a supplied key?", "CRITICAL", QuestionStatus.BLOCKING, "Blocks accepted estimate → job"),
    DiscoveryQuestion("DISC-003", "LedgerPro", "Can invoice status be read without invoice-create permission?", "HIGH", QuestionStatus.ANSWERED, "Required for a read-only accounting boundary"),
    DiscoveryQuestion("DISC-004", "SupplyDesk", "Does SupplyDesk preserve stable material identifiers?", "HIGH", QuestionStatus.BLOCKING, "Blocks job → materials"),
    DiscoveryQuestion("DISC-005", "FieldTrack", "Are completion events replayable?", "HIGH", QuestionStatus.OPEN, "Constrains field status → office and completion readiness"),
    DiscoveryQuestion("DISC-006", "RiverLead CRM", "Is customer identity stable across merged leads?", "MEDIUM", QuestionStatus.OPEN, "Constrains lead → estimate"),
)

SYSTEMS = (
    SystemDiscovery("RiverLead CRM", ("lead intake", "customer/contact information", "opportunity status"), ("lead identity", "lead contact data", "lead status"), Capability.SUPPORTED, Capability.LIMITED, ("REST API", "webhook"), Capability.LIMITED, Capability.NONE, Capability.SUPPORTED, "GOOD", "merge behavior unresolved", "DOCUMENTED", "seconds to minutes", "OAuth client", ApprovalKnowledge.DOCUMENTED, ("rate limits", "merged identifiers may redirect"), "possible outbound webhook", "MEDIUM", ("DISC-006",), AccessRisk.CLEAN),
    SystemDiscovery("EstimateWorks", ("estimating", "scope and price", "estimate acceptance"), ("estimate identity", "estimate version", "estimate status", "estimate acceptance"), Capability.SUPPORTED, Capability.LIMITED, ("REST API", "accepted export"), Capability.LIMITED, Capability.SUPPORTED, Capability.SUPPORTED, "GOOD", "accepted version immutability unresolved", "PARTIAL", "minutes", "API token", ApprovalKnowledge.DOCUMENTED, ("exports may be delayed",), "partial CRM connector", "MEDIUM", ("DISC-001",), AccessRisk.CONSTRAINED),
    SystemDiscovery("CrewBoard", ("operational jobs", "scheduling", "dispatch"), ("job existence", "schedule assignment", "crew assignment", "scheduled date"), Capability.SUPPORTED, Capability.SUPPORTED, ("REST API",), Capability.LIMITED, Capability.SUPPORTED, Capability.SUPPORTED, "GOOD", "STABLE", "DOCUMENTED", "seconds", "OAuth client", ApprovalKnowledge.DOCUMENTED, ("timeouts can leave creation outcome unclear",), "possible estimating connector", "MEDIUM", ("DISC-002",), AccessRisk.CONSTRAINED),
    SystemDiscovery("FieldTrack", ("crew field status",), ("dispatch status", "arrival status", "work status", "field completion"), Capability.SUPPORTED, Capability.LIMITED, ("REST API", "webhook"), Capability.SUPPORTED, Capability.SUPPORTED, Capability.LIMITED, "GOOD", "STABLE", "PARTIAL", "near-real-time, occasionally delayed", "signed webhook / API token", ApprovalKnowledge.DOCUMENTED, ("events may arrive late or duplicated",), "partial CrewBoard connector", "MEDIUM", ("DISC-005",), AccessRisk.CONSTRAINED),
    SystemDiscovery("SupplyDesk", ("material requirements", "purchasing coordination"), ("purchasing record", "material issue status", "material receipt status"), Capability.SUPPORTED, Capability.LIMITED, ("CSV", "limited REST API"), Capability.NONE, Capability.SUPPORTED, Capability.NONE, "MIXED", "unresolved", "PARTIAL", "daily export", "API key / human export", ApprovalKnowledge.UNKNOWN, ("CSV schema may drift",), "none known", "LOW", ("DISC-004",), AccessRisk.FRAGILE),
    SystemDiscovery("LedgerPro", ("accounting", "billing"), ("invoice state", "payment state", "accounting customer identity", "financial posting state"), Capability.SUPPORTED, Capability.LIMITED, ("read API", "controlled write API"), Capability.NONE, Capability.SUPPORTED, Capability.SUPPORTED, "GOOD", "STABLE", "DOCUMENTED", "minutes to daily posting", "scoped OAuth client", ApprovalKnowledge.DOCUMENTED, ("posting locks", "permission failures"), "possible accounting connectors", "HIGH for reads; no custom invoice create", ("DISC-003",), AccessRisk.CONSTRAINED),
)

SYSTEM_BY_NAME = {system.name: system for system in SYSTEMS}

# CrewBoard deliberately owns the operational Job. Integration Layer owns only
# future integration metadata, never the business concepts below.
BUSINESS_CONCEPTS = tuple(dict.fromkeys(
    concept for system in SYSTEMS for concept in system.authoritative_for
))
AUTHORITY_MATRIX: dict[str, dict[str, AuthorityRole]] = {
    concept: {system.name: (AuthorityRole.AUTHORITATIVE if concept in system.authoritative_for else AuthorityRole.NOT_APPLICABLE) for system in SYSTEMS}
    | {"Integration Layer": AuthorityRole.NOT_APPLICABLE}
    for concept in BUSINESS_CONCEPTS
}
# Explicit consumers show that holding a copy does not transfer ownership.
AUTHORITY_MATRIX["lead status"]["EstimateWorks"] = AuthorityRole.REFERENCE
AUTHORITY_MATRIX["estimate acceptance"]["CrewBoard"] = AuthorityRole.REFERENCE
AUTHORITY_MATRIX["field completion"]["CrewBoard"] = AuthorityRole.REFERENCE
AUTHORITY_MATRIX["invoice state"]["CrewBoard"] = AuthorityRole.REFERENCE
INTEGRATION_AUTHORITY = {
    concept: AuthorityRole.DERIVED
    for concept in ("correlation ID", "handoff acknowledgement", "retry state", "exception state", "reconciliation result")
}

TRANSITIONS = (
    ProposedTransition("lead_to_estimate", "Lead → Estimate", "RiverLead CRM", "EstimateWorks", "lead status", "estimate acceptance", TransitionRisk.LOW_RISK, NativeIntegrationStatus.PARTIAL, ("DISC-006",)),
    ProposedTransition("accepted_estimate_to_job", "Accepted Estimate → Job", "EstimateWorks", "CrewBoard", "estimate acceptance", "job existence", TransitionRisk.CONSEQUENTIAL_WRITE, NativeIntegrationStatus.POSSIBLE, ("DISC-001", "DISC-002")),
    ProposedTransition("job_to_schedule", "Job → Schedule", "CrewBoard", "CrewBoard", "job existence", "crew assignment", TransitionRisk.CONSEQUENTIAL_WRITE, NativeIntegrationStatus.SUFFICIENT),
    ProposedTransition("job_to_materials", "Job → Materials", "CrewBoard", "SupplyDesk", "job existence", "purchasing record", TransitionRisk.CONSEQUENTIAL_WRITE, NativeIntegrationStatus.NONE_KNOWN, ("DISC-004",)),
    ProposedTransition("field_status_to_office", "Field Status → Office", "FieldTrack", "CrewBoard", "field completion", "job existence", TransitionRisk.LOW_RISK, NativeIntegrationStatus.PARTIAL, ("DISC-005",)),
    ProposedTransition("completion_to_invoice_readiness", "Completion → Invoice Readiness", "FieldTrack", "LedgerPro", "field completion", "invoice state", TransitionRisk.CONSEQUENTIAL_WRITE, NativeIntegrationStatus.POSSIBLE, ("DISC-005",)),
)


class DiscoveryValidationError(ValueError):
    """Raised when authority discovery is dangerously ambiguous."""


def validate_authority(matrix: dict[str, dict[str, AuthorityRole]] = AUTHORITY_MATRIX, required: tuple[str, ...] = CORE_CONCEPTS) -> None:
    issues: list[str] = []
    for concept in required:
        owners = [name for name, role in matrix.get(concept, {}).items() if role is AuthorityRole.AUTHORITATIVE]
        if not owners:
            issues.append(f"missing authoritative owner for {concept}")
        elif len(owners) > 1:
            issues.append(f"multiple authoritative owners for {concept}: {', '.join(sorted(owners))}")
    if issues:
        raise DiscoveryValidationError("; ".join(issues))


def evaluate_readiness(transition: ProposedTransition, systems: dict[str, SystemDiscovery] = SYSTEM_BY_NAME, questions: tuple[DiscoveryQuestion, ...] = QUESTIONS, matrix: dict[str, dict[str, AuthorityRole]] = AUTHORITY_MATRIX) -> ReadinessResult:
    """Deterministically determine whether discovery supports implementation."""
    reasons: list[str] = []
    try:
        validate_authority(matrix, (transition.source_concept, transition.destination_concept))
    except DiscoveryValidationError as error:
        return ReadinessResult(transition.key, Readiness.BLOCKED, (str(error),), transition.native_integration)

    source = systems.get(transition.source_system)
    destination = systems.get(transition.destination_system)
    if source is None or destination is None:
        return ReadinessResult(transition.key, Readiness.UNKNOWN, ("source or destination discovery record is missing",), transition.native_integration)
    if source.identifier_quality in {"UNKNOWN", "POOR"}:
        reasons.append("source identifier quality is not acceptable")
    if source.read_capability in {Capability.NONE, Capability.UNKNOWN}:
        reasons.append("required source read access is not established")
    if not destination.interface_types or "UNKNOWN" in destination.interface_types:
        reasons.append("destination integration interface is unresolved")
    if transition.native_integration is NativeIntegrationStatus.UNKNOWN:
        reasons.append("native integration alternative has not been considered")

    blocking = [q for q in questions if q.id in transition.question_ids and q.status is QuestionStatus.BLOCKING]
    reasons.extend(q.automation_impact for q in blocking)

    if transition.risk is TransitionRisk.CONSEQUENTIAL_WRITE:
        if destination.write_capability is not Capability.SUPPORTED:
            reasons.append("consequential destination write permission is not established")
        if destination.write_approval is ApprovalKnowledge.UNKNOWN:
            reasons.append("write approval requirements are unknown")

    if blocking or (transition.risk is TransitionRisk.CONSEQUENTIAL_WRITE and reasons):
        status = Readiness.BLOCKED
    elif reasons:
        status = Readiness.UNKNOWN
    else:
        open_questions = [q for q in questions if q.id in transition.question_ids and q.status is QuestionStatus.OPEN]
        constraints = list(q.automation_impact for q in open_questions)
        if transition.native_integration in {NativeIntegrationStatus.PARTIAL, NativeIntegrationStatus.POSSIBLE, NativeIntegrationStatus.SUFFICIENT}:
            constraints.append(f"native integration option is {transition.native_integration.value}")
        reasons = constraints
        status = Readiness.READY_WITH_CONSTRAINTS if constraints else Readiness.READY
    return ReadinessResult(transition.key, status, tuple(reasons), transition.native_integration)


def baseline_readiness() -> tuple[ReadinessResult, ...]:
    return tuple(evaluate_readiness(transition) for transition in TRANSITIONS)


# Chapter 1 remains immutable baseline evidence.  Chapter 4 explicitly supplies
# fictional answers needed for its experiment rather than rewriting history.
CHAPTER4_MODELED_ASSUMPTIONS = (
    "CrewBoard supports externally created jobs",
    "CrewBoard accepts a deterministic external reference",
    "CrewBoard lookup exposes enough job data to detect a compatible existing job",
    "CrewBoard deduplicates creation by that external reference",
    "CrewBoard creation acknowledges the authoritative destination job ID",
    "the consequential-write permission and approval boundary are documented",
    "EstimateWorks accepted estimate identity and version are readable",
)
CHAPTER4_RESOLVED_QUESTIONS = tuple(
    replace(question, status=QuestionStatus.ANSWERED,
            automation_impact=f"MODELED ASSUMPTION resolved for Chapter 4: {question.question}")
    if question.id in {"DISC-001", "DISC-002"} else question
    for question in QUESTIONS
)


def chapter4_resolved_readiness() -> ReadinessResult:
    """Evaluate only the handoff using Chapter 4's modeled discovery variant."""
    transition = next(item for item in TRANSITIONS
                      if item.key == "accepted_estimate_to_job")
    return evaluate_readiness(transition, questions=CHAPTER4_RESOLVED_QUESTIONS)
