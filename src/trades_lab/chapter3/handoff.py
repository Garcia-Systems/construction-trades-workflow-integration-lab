"""A deliberately small, in-memory lead-to-estimate boundary.

RiverLead and EstimateWorks are fictional. This module owns translation and a
handoff decision, not either system's business records.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any, Mapping

from trades_lab.domain import (ExceptionCategory, ExceptionRecord, ExceptionStatus,
                               IntegrationEvent, Lead, Provenance, SourceReference)

SOURCE_SYSTEM = "RiverLead CRM"
DESTINATION_SYSTEM = "EstimateWorks"
ELIGIBLE_STATES = frozenset({"QUALIFIED", "ESTIMATE_REQUESTED"})
INELIGIBLE_STATES = frozenset({"NEW", "CLOSED_LOST", "SPAM", "DUPLICATE"})


class HandoffOutcome(StrEnum):
    READY = "READY"
    SKIPPED_NOT_ELIGIBLE = "SKIPPED_NOT_ELIGIBLE"
    DUPLICATE = "DUPLICATE"
    EXCEPTION = "EXCEPTION"


@dataclass(frozen=True)
class Contact:
    email: str | None
    phone: str | None


@dataclass(frozen=True)
class ServiceAddress:
    line1: str
    city: str
    state: str
    postal_code: str


@dataclass(frozen=True)
class NormalizedLead:
    lead: Lead
    customer_reference: SourceReference
    customer_name: str
    contact: Contact
    service_address: ServiceAddress
    requested_service: str
    source_state: str


@dataclass(frozen=True)
class EstimateIntakeCommand:
    """The complete and intentionally narrow EstimateWorks intake contract."""

    correlation_id: str
    source_lead_id: str
    canonical_lead_id: str
    source_customer_id: str
    customer_name: str
    contact: Contact
    service_address: ServiceAddress
    scope_summary: str
    source_observed_at: datetime
    source_version: str


@dataclass(frozen=True)
class HandoffResult:
    outcome: HandoffOutcome
    correlation_id: str
    explanation: str
    normalized_lead: NormalizedLead | None
    command: EstimateIntakeCommand | None
    exception: ExceptionRecord | None
    events: tuple[IntegrationEvent, ...]


class SourceValidationError(ValueError):
    pass


class RiverLeadAdapter:
    """Translate one local RiverLead-shaped mapping without generic machinery."""

    def normalize(self, raw: Mapping[str, Any], correlation_id: str) -> NormalizedLead:
        try:
            lead_id = self._text(raw, "lead_id")
            customer_id = self._text(raw, "customer_id")
            first_name = self._text(raw, "first_name")
            last_name = self._text(raw, "last_name")
            requested = self._text(raw, "requested_service")
            status = self._text(raw, "status")
            updated_text = self._text(raw, "updated_at")
            updated_at = datetime.fromisoformat(updated_text.replace("Z", "+00:00"))
            address = raw["service_address"]
            if not isinstance(address, Mapping):
                raise SourceValidationError("service_address must be an object")
            service_address = ServiceAddress(*(self._text(address, key) for key in
                                               ("line1", "city", "state", "postal_code")))
        except SourceValidationError:
            raise
        except (KeyError, TypeError, ValueError) as error:
            raise SourceValidationError(f"malformed RiverLead record: {error}") from error

        email = self._optional_text(raw.get("email"))
        phone = self._optional_text(raw.get("phone"))
        if not email and not phone:
            raise SourceValidationError("at least one usable contact method is required")

        lead_source = SourceReference(SOURCE_SYSTEM, lead_id)
        customer_source = SourceReference(SOURCE_SYSTEM, customer_id)
        provenance = Provenance(lead_source, updated_at, updated_text, correlation_id)
        lead = Lead(self._canonical_id(lead_id), (lead_source,), provenance,
                    f"riverlead-customer-{customer_id.lower()}")
        return NormalizedLead(lead, customer_source, f"{first_name} {last_name}",
                              Contact(email, phone), service_address, requested, status)

    @staticmethod
    def _text(record: Mapping[str, Any], key: str) -> str:
        value = record.get(key)
        if not isinstance(value, str) or not value.strip():
            raise SourceValidationError(f"{key} is required and must be text")
        return value.strip()

    @staticmethod
    def _optional_text(value: Any) -> str | None:
        return value.strip().lower() if isinstance(value, str) and value.strip() else None

    @staticmethod
    def _canonical_id(source_id: str) -> str:
        return "lead-" + source_id.lower().removeprefix("rl-")


class LeadToEstimateHandoff:
    """Process-local replay/ambiguity checks; deliberately not durable idempotency."""

    def __init__(self, adapter: RiverLeadAdapter | None = None) -> None:
        self.adapter = adapter or RiverLeadAdapter()
        self._replays: set[tuple[str, str]] = set()
        self._contact_owners: dict[tuple[str | None, str | None], str] = {}
        self.commands: list[EstimateIntakeCommand] = []

    def process(self, raw: Mapping[str, Any]) -> HandoffResult:
        if not isinstance(raw, Mapping):
            raw = {}
        lead_hint = raw.get("lead_id")
        version_hint = raw.get("updated_at")
        source_id = lead_hint if isinstance(lead_hint, str) and lead_hint else "UNKNOWN"
        version = version_hint if isinstance(version_hint, str) and version_hint else "UNKNOWN"
        correlation_id = self._correlation(source_id, version)
        observed_at = self._event_time(version)
        events = [self._event("LEAD_OBSERVED", source_id, source_id, correlation_id,
                              observed_at, 1)]

        try:
            normalized = self.adapter.normalize(raw, correlation_id)
        except (SourceValidationError, AttributeError) as error:
            events.append(self._event("LEAD_VALIDATION_FAILED", source_id, source_id,
                                      correlation_id, observed_at, 2))
            return self._exception_result(correlation_id, source_id, str(error),
                                          ExceptionCategory.VALIDATION, events, observed_at)

        state = normalized.source_state
        if state not in ELIGIBLE_STATES | INELIGIBLE_STATES:
            events.append(self._event("LEAD_VALIDATION_FAILED", source_id,
                                      normalized.lead.canonical_id, correlation_id,
                                      observed_at, 2))
            return self._exception_result(correlation_id, source_id,
                                          f"unknown RiverLead state: {state}",
                                          ExceptionCategory.VALIDATION, events, observed_at,
                                          normalized)
        if state in INELIGIBLE_STATES:
            events.append(self._event("LEAD_NOT_ELIGIBLE", source_id,
                                      normalized.lead.canonical_id, correlation_id,
                                      observed_at, 2))
            return HandoffResult(HandoffOutcome.SKIPPED_NOT_ELIGIBLE, correlation_id,
                                 f"RiverLead state {state} is not eligible", normalized,
                                 None, None, tuple(events))

        replay_key = (source_id, version)
        if replay_key in self._replays:
            events.append(self._event("LEAD_DUPLICATE_DETECTED", source_id,
                                      normalized.lead.canonical_id, correlation_id,
                                      observed_at, 2))
            return HandoffResult(HandoffOutcome.DUPLICATE, correlation_id,
                                 "identical source identity/version already processed",
                                 normalized, None, None, tuple(events))

        events.append(self._event("LEAD_NORMALIZED", source_id,
                                  normalized.lead.canonical_id, correlation_id,
                                  observed_at, 2))
        contact_key = (normalized.contact.email, normalized.contact.phone)
        owner = self._contact_owners.get(contact_key)
        if owner is not None and owner != source_id:
            events.append(self._event("LEAD_IDENTITY_AMBIGUOUS", source_id,
                                      normalized.lead.canonical_id, correlation_id,
                                      observed_at, 3))
            return self._exception_result(correlation_id, source_id,
                                          f"contact also appears on source lead {owner}; no merge performed",
                                          ExceptionCategory.IDENTITY, events, observed_at,
                                          normalized)

        command = EstimateIntakeCommand(
            correlation_id, source_id, normalized.lead.canonical_id,
            normalized.customer_reference.source_id, normalized.customer_name,
            normalized.contact, normalized.service_address, normalized.requested_service,
            normalized.lead.provenance.observed_at, version,
        )
        self._replays.add(replay_key)
        self._contact_owners[contact_key] = source_id
        self.commands.append(command)
        events.append(self._event("ESTIMATE_INTAKE_READY", source_id,
                                  normalized.lead.canonical_id, correlation_id,
                                  observed_at, 3))
        return HandoffResult(HandoffOutcome.READY, correlation_id,
                             "validated command is ready for the EstimateWorks boundary",
                             normalized, command, None, tuple(events))

    def _exception_result(self, correlation_id: str, source_id: str, summary: str,
                          category: ExceptionCategory, events: list[IntegrationEvent],
                          created_at: datetime, normalized: NormalizedLead | None = None
                          ) -> HandoffResult:
        entity_id = normalized.lead.canonical_id if normalized else source_id
        record = ExceptionRecord(f"exception-{correlation_id}", category, "Lead", entity_id,
                                 SOURCE_SYSTEM, summary, ExceptionStatus.OPEN, created_at,
                                 correlation_id)
        return HandoffResult(HandoffOutcome.EXCEPTION, correlation_id, summary, normalized,
                             None, record, tuple(events))

    @staticmethod
    def _correlation(source_id: str, version: str) -> str:
        digits = source_id.lower().removeprefix("rl-")
        version_token = "".join(character.lower() for character in version
                                if character.isalnum())
        return f"corr-lead-{digits}-v{version_token}"

    @staticmethod
    def _event_time(version: str) -> datetime:
        try:
            return datetime.fromisoformat(version.replace("Z", "+00:00"))
        except ValueError:
            return datetime.fromisoformat("2000-01-01T00:00:00+00:00")

    @staticmethod
    def _event(event_type: str, source_id: str, entity_id: str, correlation_id: str,
               occurred_at: datetime, sequence: int) -> IntegrationEvent:
        return IntegrationEvent(f"{correlation_id}-event-{sequence}", event_type,
                                SOURCE_SYSTEM, source_id, "Lead", entity_id, occurred_at,
                                correlation_id)


ARCHITECTURE_INVENTORY = {
    "SHARED CORE": ("canonical identity", "provenance", "events", "exceptions"),
    "SOURCE-SPECIFIC ADAPTER": ("RiverLeadAdapter",),
    "WORKFLOW-SPECIFIC LOGIC": ("lead eligibility", "EstimateWorks intake requirements"),
}
