"""Bounded material-requirement handoff; not purchasing or inventory."""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from hashlib import sha256

from trades_lab.domain import (ExceptionCategory, ExceptionRecord, ExceptionStatus,
                               IntegrationEvent, Provenance)

SOURCE_SYSTEM = "CrewBoard Jobs"
DESTINATION_SYSTEM = "SupplyDesk"


class MaterialUnit(StrEnum):
    EACH = "EACH"
    FOOT = "FOOT"
    BOX = "BOX"
    ROLL = "ROLL"


class MappingStatus(StrEnum):
    APPROVED = "APPROVED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    RETIRED = "RETIRED"


class MaterialHandoffOutcome(StrEnum):
    REQUESTED = "REQUESTED"
    IDEMPOTENT_REPLAY = "IDEMPOTENT_REPLAY"
    UPDATED_REQUIREMENT = "UPDATED_REQUIREMENT"
    EXCEPTION = "EXCEPTION"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


class MaterialReadiness(StrEnum):
    READY = "READY"
    PARTIALLY_READY = "PARTIALLY_READY"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class MaterialRequirement:
    requirement_id: str
    job_id: str
    source_material_id: str
    description: str
    quantity: Decimal
    unit: MaterialUnit
    required_by: date | datetime | None
    version: int
    provenance: Provenance
    substitute_suggested: str | None = None


@dataclass(frozen=True)
class UnitConversion:
    source_unit: MaterialUnit
    destination_unit: MaterialUnit
    multiplier: Decimal
    rule_id: str


@dataclass(frozen=True)
class MaterialMapping:
    source_system: str
    source_material_id: str
    destination_system: str
    destination_material_id: str
    canonical_material_id: str
    approved_source_unit: MaterialUnit
    destination_unit: MaterialUnit
    status: MappingStatus
    classification: str
    conversion: UnitConversion | None = None


class MaterialMappingRegistry:
    """Exact-key lookup over inspectable configuration; descriptions are never searched."""

    def __init__(self, mappings: tuple[MaterialMapping, ...]) -> None:
        self.mappings = mappings

    def candidates(self, source_system: str, source_material_id: str) -> tuple[MaterialMapping, ...]:
        return tuple(m for m in self.mappings if m.source_system == source_system
                     and m.source_material_id == source_material_id
                     and m.status is not MappingStatus.RETIRED)


@dataclass(frozen=True)
class MaterialRequestCommand:
    correlation_id: str
    idempotency_key: str
    authoritative_job_id: str
    requirement_id: str
    requirement_version: int
    destination_material_id: str
    quantity: Decimal
    unit: MaterialUnit
    required_by: date | datetime | None
    provenance: Provenance


@dataclass(frozen=True)
class MaterialRequest:
    request_id: str
    command: MaterialRequestCommand
    previous_request_id: str | None = None


@dataclass(frozen=True)
class MaterialRequestAcknowledgement:
    request_id: str
    correlation_id: str
    idempotency_key: str
    created: bool


@dataclass(frozen=True)
class MaterialHandoffResult:
    outcome: MaterialHandoffOutcome
    requirement: MaterialRequirement
    mapping: MaterialMapping | None
    command: MaterialRequestCommand | None
    acknowledgement: MaterialRequestAcknowledgement | None
    exception: ExceptionRecord | None
    events: tuple[IntegrationEvent, ...]


@dataclass(frozen=True)
class JobMaterialSummary:
    job_id: str
    requirement_count: int
    ready_count: int
    exception_count: int
    readiness: MaterialReadiness
    results: tuple[MaterialHandoffResult, ...]


class SupplyDeskSimulator:
    def __init__(self) -> None:
        self._requests: list[MaterialRequest] = []
        self._by_key: dict[str, MaterialRequest] = {}

    @property
    def requests(self) -> tuple[MaterialRequest, ...]:
        return tuple(self._requests)

    def find_material_request(self, idempotency_key: str) -> MaterialRequest | None:
        return self._by_key.get(idempotency_key)

    def latest_for_requirement(self, job_id: str, requirement_id: str) -> MaterialRequest | None:
        return next((r for r in reversed(self._requests)
                     if r.command.authoritative_job_id == job_id
                     and r.command.requirement_id == requirement_id), None)

    def submit_material_request(self, command: MaterialRequestCommand,
                                previous_request_id: str | None = None) -> MaterialRequestAcknowledgement:
        existing = self._by_key.get(command.idempotency_key)
        if existing:
            return self._ack(existing, False)
        request = MaterialRequest(f"SD-REQ-{len(self._requests) + 1:04d}", command,
                                  previous_request_id)
        self._requests.append(request)
        self._by_key[command.idempotency_key] = request
        return self._ack(request, True)

    @staticmethod
    def _ack(request: MaterialRequest, created: bool) -> MaterialRequestAcknowledgement:
        return MaterialRequestAcknowledgement(request.request_id, request.command.correlation_id,
                                              request.command.idempotency_key, created)


class MaterialsHandoff:
    def __init__(self, registry: MaterialMappingRegistry,
                 destination: SupplyDeskSimulator | None = None) -> None:
        self.registry = registry
        self.destination = destination or SupplyDeskSimulator()
        self.commands: list[MaterialRequestCommand] = []

    def process(self, requirement: MaterialRequirement) -> MaterialHandoffResult:
        correlation = requirement.provenance.correlation_id or f"corr-material-{requirement.requirement_id}"
        events = [self._event("MATERIAL_REQUIREMENT_OBSERVED", requirement, correlation, 1)]
        if requirement.quantity <= 0:
            return self._failure(requirement, correlation, events, ExceptionCategory.VALIDATION,
                                 "quantity must be positive")
        candidates = self.registry.candidates(SOURCE_SYSTEM, requirement.source_material_id)
        if len(candidates) != 1:
            reason = "unknown material mapping" if not candidates else "ambiguous material mapping"
            return self._failure(requirement, correlation, events, ExceptionCategory.MAPPING, reason)
        mapping = candidates[0]
        if mapping.status is not MappingStatus.APPROVED:
            return self._failure(requirement, correlation, events, ExceptionCategory.MAPPING,
                                 "mapping requires human review", mapping)
        events.append(self._event("MATERIAL_MAPPING_RESOLVED", requirement, correlation, 2))
        if requirement.substitute_suggested:
            events.append(self._event("MATERIAL_SUBSTITUTION_REVIEW_REQUIRED", requirement,
                                      correlation, 3))
            return self._failure(requirement, correlation, events, ExceptionCategory.MAPPING,
                                 "substitution proposed; approval required", mapping, review=True)
        quantity = requirement.quantity
        unit = requirement.unit
        if unit != mapping.approved_source_unit:
            return self._failure(requirement, correlation, events, ExceptionCategory.VALIDATION,
                                 "source unit does not match approved mapping", mapping)
        if mapping.destination_unit != unit:
            conversion = mapping.conversion
            if not conversion or conversion.source_unit != unit or conversion.destination_unit != mapping.destination_unit:
                return self._failure(requirement, correlation, events, ExceptionCategory.VALIDATION,
                                     "unit mismatch has no explicit conversion rule", mapping)
            quantity = quantity * conversion.multiplier
            unit = conversion.destination_unit
            events.append(self._event("MATERIAL_UNIT_CONVERTED", requirement, correlation, 3,
                                      (("rule_id", conversion.rule_id),
                                       ("normalized_quantity", str(quantity)),
                                       ("normalized_unit", unit.value))))
        key = self.idempotency_key(requirement, mapping.destination_material_id, quantity, unit)
        command = MaterialRequestCommand(correlation, key, requirement.job_id,
                                         requirement.requirement_id, requirement.version,
                                         mapping.destination_material_id, quantity, unit,
                                         requirement.required_by, requirement.provenance)
        existing = self.destination.find_material_request(key)
        if existing:
            ack = self.destination.submit_material_request(command)
            events.append(self._event("MATERIAL_REQUEST_ACKNOWLEDGED", requirement, correlation, 4))
            return MaterialHandoffResult(MaterialHandoffOutcome.IDEMPOTENT_REPLAY, requirement,
                                         mapping, command, ack, None, tuple(events))
        previous = self.destination.latest_for_requirement(requirement.job_id,
                                                           requirement.requirement_id)
        events.extend((self._event("MATERIAL_REQUEST_READY", requirement, correlation, 4),
                       self._event("MATERIAL_REQUEST_SENT", requirement, correlation, 5)))
        ack = self.destination.submit_material_request(command,
                                                       previous.request_id if previous else None)
        self.commands.append(command)
        events.append(self._event("MATERIAL_REQUEST_ACKNOWLEDGED", requirement, correlation, 6))
        outcome = (MaterialHandoffOutcome.UPDATED_REQUIREMENT if previous
                   else MaterialHandoffOutcome.REQUESTED)
        return MaterialHandoffResult(outcome, requirement, mapping, command, ack, None,
                                     tuple(events))

    def process_job(self, requirements: tuple[MaterialRequirement, ...]) -> JobMaterialSummary:
        if not requirements:
            raise ValueError("at least one material requirement is required")
        job_ids = {r.job_id for r in requirements}
        if len(job_ids) != 1:
            raise ValueError("requirements must belong to one job")
        results = tuple(self.process(r) for r in requirements)
        ready = sum(r.outcome in (MaterialHandoffOutcome.REQUESTED,
                                  MaterialHandoffOutcome.IDEMPOTENT_REPLAY,
                                  MaterialHandoffOutcome.UPDATED_REQUIREMENT) for r in results)
        failures = len(results) - ready
        readiness = (MaterialReadiness.READY if failures == 0 else
                     MaterialReadiness.BLOCKED if ready == 0 else MaterialReadiness.PARTIALLY_READY)
        return JobMaterialSummary(next(iter(job_ids)), len(results), ready, failures,
                                  readiness, results)

    @staticmethod
    def idempotency_key(requirement: MaterialRequirement, destination_id: str,
                        quantity: Decimal, unit: MaterialUnit) -> str:
        material = "|".join((requirement.job_id, requirement.requirement_id,
                             destination_id, str(quantity), unit.value,
                             str(requirement.version)))
        return "material-request:" + sha256(material.encode()).hexdigest()[:20]

    def _failure(self, requirement: MaterialRequirement, correlation: str,
                 events: list[IntegrationEvent], category: ExceptionCategory, reason: str,
                 mapping: MaterialMapping | None = None,
                 review: bool = False) -> MaterialHandoffResult:
        sequence = len(events) + 1
        events.append(self._event("MATERIAL_MAPPING_FAILED", requirement, correlation, sequence))
        events.append(self._event("EXCEPTION_CREATED", requirement, correlation, sequence + 1))
        exception = ExceptionRecord(f"EX-MAT-{requirement.requirement_id}-{sequence}", category,
                                    "MaterialRequirement", requirement.requirement_id,
                                    SOURCE_SYSTEM, reason, ExceptionStatus.OPEN,
                                    requirement.provenance.observed_at, correlation)
        outcome = MaterialHandoffOutcome.REVIEW_REQUIRED if review else MaterialHandoffOutcome.EXCEPTION
        return MaterialHandoffResult(outcome, requirement, mapping, None, None, exception,
                                     tuple(events))

    @staticmethod
    def _event(kind: str, requirement: MaterialRequirement, correlation: str,
               sequence: int, metadata: tuple[tuple[str, str], ...] = ()) -> IntegrationEvent:
        return IntegrationEvent(f"evt-{requirement.requirement_id}-{sequence}-{kind.lower()}", kind,
                                SOURCE_SYSTEM, requirement.requirement_id,
                                "MaterialRequirement", requirement.requirement_id,
                                requirement.provenance.observed_at, correlation, metadata)


ARCHITECTURE_INVENTORY = {
    "SHARED CORE": "provenance, correlation, events, exception and idempotency patterns",
    "SOURCE-SPECIFIC ADAPTER": "CrewBoard job material observation and SupplyDesk boundary",
    "WORKFLOW-SPECIFIC LOGIC": "material normalization, partial readiness and changed requirement linking",
    "CUSTOMER-SPECIFIC RULE": "James River Mechanical internal material-code mappings",
    "CONFIGURATION": "inspectable mapping content and explicit conversion factors",
    "VALIDATION": "positive quantity, approved source unit and conversion checks",
    "RELIABILITY": "content-sensitive business idempotency and acknowledgements",
    "EXCEPTION HANDLING": "unknown, ambiguous, unsupported-unit and substitution review stops",
    "TESTING": "deterministic direct, replay, conversion, failure, partial and update scenarios",
    "SUPPORT SURFACE": "retired products, new customer codes, unit and substitution-policy changes",
}
