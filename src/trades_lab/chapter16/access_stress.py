"""Synthetic access-quality experiments for the same contractor handoffs."""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256


class AccessLevel(StrEnum):
    SUPPORTED = "SUPPORTED"
    LIMITED = "LIMITED"
    EXPORT_ONLY = "EXPORT_ONLY"
    NONE = "NONE"


class DocumentationQuality(StrEnum):
    GOOD = "GOOD"
    PARTIAL = "PARTIAL"
    POOR = "POOR"


class AcknowledgementQuality(StrEnum):
    STRONG = "STRONG"
    PARTIAL = "PARTIAL"
    NONE = "NONE"


class SchemaStability(StrEnum):
    STABLE = "STABLE"
    DRIFT_PRONE = "DRIFT_PRONE"
    UNKNOWN = "UNKNOWN"


class AccessRisk(StrEnum):
    CLEAN = "CLEAN"
    CONSTRAINED = "CONSTRAINED"
    FRAGILE = "FRAGILE"
    CLOSED = "CLOSED"


class Feasibility(StrEnum):
    FULLY_AUTOMATABLE = "FULLY_AUTOMATABLE"
    AUTOMATABLE_WITH_CONSTRAINTS = "AUTOMATABLE_WITH_CONSTRAINTS"
    READ_ONLY = "READ_ONLY"
    HUMAN_ASSISTED = "HUMAN_ASSISTED"
    BLOCKED = "BLOCKED"


class TechnicalScope(StrEnum):
    API_WRITE_AUTOMATION = "API_WRITE_AUTOMATION"
    API_READ_ASSIST = "API_READ_ASSIST"
    EXPORT_IMPORT_AUTOMATION = "EXPORT_IMPORT_AUTOMATION"
    CSV_HANDOFF = "CSV_HANDOFF"
    HUMAN_REVIEW_ASSIST = "HUMAN_REVIEW_ASSIST"
    READ_ONLY_VISIBILITY = "READ_ONLY_VISIBILITY"
    NATIVE_VENDOR_WORKFLOW = "NATIVE_VENDOR_WORKFLOW"
    UNSUPPORTED = "UNSUPPORTED"


@dataclass(frozen=True)
class InterfaceCapability:
    system_name: str
    read_access: AccessLevel
    write_access: AccessLevel
    sandbox_available: bool
    stable_identifiers: bool
    external_reference_support: bool
    lookup_support: bool
    documentation_quality: DocumentationQuality
    acknowledgement_quality: AcknowledgementQuality
    schema_stability: SchemaStability

    @property
    def safe_recovery(self) -> bool:
        return (self.write_access is AccessLevel.SUPPORTED and self.stable_identifiers
                and self.external_reference_support and self.lookup_support
                and self.acknowledgement_quality is AcknowledgementQuality.STRONG)


@dataclass(frozen=True)
class AccessProfile:
    key: str
    label: str
    capability: InterfaceCapability
    export_timing: str
    native_workflow_available: bool


CLEAN = AccessProfile("clean", "PROFILE A — CLEAN", InterfaceCapability(
    "CrewBoard", AccessLevel.SUPPORTED, AccessLevel.SUPPORTED, True, True, True, True,
    DocumentationQuality.GOOD, AcknowledgementQuality.STRONG, SchemaStability.STABLE),
    "near-immediate API availability", True)
DIFFICULT = AccessProfile("difficult", "PROFILE B — DIFFICULT", InterfaceCapability(
    "CrewBoard Limited", AccessLevel.EXPORT_ONLY, AccessLevel.LIMITED, False, False, False, False,
    DocumentationQuality.PARTIAL, AcknowledgementQuality.PARTIAL, SchemaStability.DRIFT_PRONE),
    "nightly CSV batch", True)
CLOSED = AccessProfile("closed", "PROFILE C — CLOSED", InterfaceCapability(
    "ClosedJob", AccessLevel.EXPORT_ONLY, AccessLevel.NONE, False, True, False, False,
    DocumentationQuality.POOR, AcknowledgementQuality.NONE, SchemaStability.UNKNOWN),
    "vendor-defined export timing", True)
PROFILES = (CLEAN, DIFFICULT, CLOSED)


def classify_access(profile: AccessProfile) -> AccessRisk:
    capability = profile.capability
    if capability.write_access is AccessLevel.NONE:
        return AccessRisk.CLOSED
    if capability.safe_recovery and capability.sandbox_available:
        return AccessRisk.CLEAN
    if capability.write_access is AccessLevel.LIMITED and capability.read_access is not AccessLevel.NONE:
        return AccessRisk.CONSTRAINED
    return AccessRisk.FRAGILE


HANDOFFS = ("lead → estimate", "accepted estimate → job", "job → schedule",
            "materials handoff", "field status → office", "completion → invoice readiness")


@dataclass(frozen=True)
class TransitionAccessResult:
    profile_key: str
    handoff: str
    feasibility: Feasibility
    reasons: tuple[str, ...]


def evaluate_transition(profile: AccessProfile, handoff: str) -> TransitionAccessResult:
    if handoff not in HANDOFFS:
        raise ValueError(f"unknown handoff: {handoff}")
    cap = profile.capability
    if profile is CLEAN:
        return TransitionAccessResult(profile.key, handoff, Feasibility.FULLY_AUTOMATABLE,
                                      ("supported read/write and safe uncertain-write recovery",))
    if profile is CLOSED:
        if handoff == "accepted estimate → job":
            return TransitionAccessResult(profile.key, handoff, Feasibility.BLOCKED,
                                          ("critical destination write access is NONE",))
        return TransitionAccessResult(profile.key, handoff, Feasibility.READ_ONLY,
                                      ("exports preserve visibility; native UI owns consequential action",))
    if handoff in {"materials handoff", "field status → office"}:
        return TransitionAccessResult(profile.key, handoff, Feasibility.AUTOMATABLE_WITH_CONSTRAINTS,
                                      ("known-schema nightly export", "batch delay and schema drift exposure"))
    if cap.write_access is AccessLevel.LIMITED:
        return TransitionAccessResult(profile.key, handoff, Feasibility.AUTOMATABLE_WITH_CONSTRAINTS,
                                      ("write is limited", "no stable deduplication or outcome lookup",
                                       "no sandbox; dry-run or human confirmation required"))
    return TransitionAccessResult(profile.key, handoff, Feasibility.HUMAN_ASSISTED,
                                  ("interface cannot safely complete the handoff",))


@dataclass(frozen=True)
class ScopeRecommendation:
    profile_key: str
    handoff: str
    business_importance: str
    scope: TechnicalScope
    reason: str


def recommend_scope(handoff: str, profile: AccessProfile,
                    business_importance: str = "CRITICAL") -> ScopeRecommendation:
    result = evaluate_transition(profile, handoff)
    if result.feasibility is Feasibility.FULLY_AUTOMATABLE:
        scope = TechnicalScope.API_WRITE_AUTOMATION
    elif profile is DIFFICULT and handoff in {"materials handoff", "field status → office"}:
        scope = TechnicalScope.EXPORT_IMPORT_AUTOMATION
    elif profile is DIFFICULT:
        scope = TechnicalScope.HUMAN_REVIEW_ASSIST
    elif profile is CLOSED and handoff == "accepted estimate → job":
        scope = (TechnicalScope.NATIVE_VENDOR_WORKFLOW if profile.native_workflow_available
                 else TechnicalScope.HUMAN_REVIEW_ASSIST)
    elif result.feasibility is Feasibility.READ_ONLY:
        scope = TechnicalScope.READ_ONLY_VISIBILITY
    else:
        scope = TechnicalScope.UNSUPPORTED
    return ScopeRecommendation(profile.key, handoff, business_importance, scope, "; ".join(result.reasons))


@dataclass(frozen=True)
class HumanHandoffPacket:
    packet_id: str
    correlation_id: str
    source_entity_id: str
    destination_system: str
    required_action: str
    validated_fields: tuple[tuple[str, str], ...]
    evidence_reference: str
    destination_write_performed: bool = False


def create_job_handoff_packet(correlation_id: str, estimate_id: str,
                              customer_id: str, evidence_reference: str) -> HumanHandoffPacket:
    if not all((correlation_id, estimate_id, customer_id, evidence_reference)):
        raise ValueError("handoff packet fields must be non-empty")
    identity = sha256(f"{correlation_id}|{estimate_id}|ClosedJob".encode()).hexdigest()[:16]
    return HumanHandoffPacket(f"packet-{identity}", correlation_id, estimate_id, "ClosedJob",
                              "create and confirm job in native vendor UI",
                              (("estimate_id", estimate_id), ("customer_id", customer_id)), evidence_reference)


def reconcile_packet(packet: HumanHandoffPacket, destination_job_id: str | None) -> bool:
    """Read-only evidence check; never performs a destination write."""
    return bool(destination_job_id and packet.source_entity_id)


EXPECTED_CSV_HEADERS = ("estimate_id", "status", "customer_id", "updated_at")


class CsvExportError(ValueError):
    support_action = "inspect export schema/file; automation remains stopped"


class SchemaDriftError(CsvExportError):
    pass


@dataclass(frozen=True)
class ExportEstimate:
    estimate_id: str
    status: str
    customer_id: str
    updated_at: str
    source_system: str = "BidForge CSV v1"


def parse_estimate_export(content: str, schema_version: str = "v1") -> tuple[ExportEstimate, ...]:
    if schema_version != "v1":
        raise SchemaDriftError(f"unsupported schema version {schema_version}; expected v1")
    reader = csv.DictReader(io.StringIO(content, newline=""), strict=True)
    observed = tuple(reader.fieldnames or ())
    if observed != EXPECTED_CSV_HEADERS:
        raise SchemaDriftError(f"schema drift: expected {EXPECTED_CSV_HEADERS}, observed {observed}")
    records: list[ExportEstimate] = []
    try:
        for number, row in enumerate(reader, 2):
            if (None in row or set(row) != set(EXPECTED_CSV_HEADERS)
                    or any(not isinstance(row[h], str) or not row[h].strip() for h in EXPECTED_CSV_HEADERS)):
                raise CsvExportError(f"malformed row {number}")
            records.append(ExportEstimate(*(row[h].strip() for h in EXPECTED_CSV_HEADERS)))
    except csv.Error as error:
        raise CsvExportError(f"malformed CSV: {error}") from error
    return tuple(records)


@dataclass(frozen=True)
class SupportSurfaceItem:
    profile_key: str
    item: str


SUPPORT = {
    "clean": ("credentials", "API versions", "vendor outages", "mappings", "exceptions"),
    "difficult": ("credentials", "mappings", "export monitoring", "schema drift", "file timing",
                  "partial acknowledgements", "manual reconciliation", "unstable IDs", "production-only testing"),
    "closed": ("human handoff process", "reconciliation dependency", "manual action ownership",
               "process training", "automation expectation limits"),
}

RELIABILITY_MATRIX = {
    "write acknowledgement": ("STRONG", "PARTIAL", "N/A"),
    "destination lookup": ("YES", "NO", "NO"),
    "safe auto replay": ("YES", "NO", "NO"),
    "schema drift exposure": ("LOW", "HIGH", "MEDIUM"),
    "batch delay": ("LOW", "HIGH", "VARIES"),
    "human intervention": ("LOW", "MEDIUM", "HIGH"),
}

ARCHITECTURE_INVENTORY = (
    ("access capability evaluation", "SHARED CORE"), ("scope recommendation contract", "SHARED CORE"),
    ("human-handoff packet", "SHARED CORE"), ("strict CSV parser", "SOURCE-SPECIFIC ADAPTER"),
    ("handoff access requirements", "WORKFLOW-SPECIFIC LOGIC"), ("profile and schema version", "CONFIGURATION"),
    ("lookup/replay feasibility", "RELIABILITY"), ("schema/file/manual procedures", "SUPPORT SURFACE"),
)


@dataclass(frozen=True)
class AccessStressReport:
    profiles: tuple[AccessProfile, ...]
    transition_results: tuple[TransitionAccessResult, ...]
    support_surface: tuple[SupportSurfaceItem, ...]
    recommended_scopes: tuple[ScopeRecommendation, ...]


def build_report() -> AccessStressReport:
    results = tuple(evaluate_transition(profile, handoff) for profile in PROFILES for handoff in HANDOFFS)
    support = tuple(SupportSurfaceItem(key, item) for key in ("clean", "difficult", "closed") for item in SUPPORT[key])
    scopes = tuple(recommend_scope(handoff, profile) for profile in PROFILES for handoff in HANDOFFS)
    return AccessStressReport(PROFILES, results, support, scopes)
