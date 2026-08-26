"""Synchronous, synthetic invoice-readiness validation (never invoice creation)."""

from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum
from hashlib import sha256

from trades_lab.chapter7 import FieldStatus, FieldStatusObservation
from trades_lab.domain import IntegrationEvent, JobState
from trades_lab.domain.states import InvoiceReadinessState


class CheckOutcome(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    NOT_APPLICABLE = "N/A"


class SubmissionOutcome(StrEnum):
    ACKNOWLEDGED = "ACKNOWLEDGED"
    IDEMPOTENT_REPLAY = "IDEMPOTENT_REPLAY"


@dataclass(frozen=True)
class ReadinessCheck:
    name: str
    outcome: CheckOutcome
    detail: str


@dataclass(frozen=True)
class CompletionEvidence:
    completion_id: str
    authoritative_job_id: str
    completed_at: datetime
    completion_code: str
    source_system: str
    source_record_id: str
    version: str
    acknowledged: bool = True


@dataclass(frozen=True)
class BillingMetadata:
    job_reference: str | None
    completion_date: date | None
    billing_summary: str | None
    billing_category: str | None
    version: str


@dataclass(frozen=True)
class ReadinessException:
    exception_id: str
    summary: str
    unresolved: bool = True
    blocks_invoice_readiness: bool = True


@dataclass(frozen=True)
class ReadinessFacts:
    authoritative_job_id: str
    authoritative_customer_id: str
    authoritative_job_state: JobState
    authoritative_updated_at: datetime
    job_version: str
    field_observation: FieldStatusObservation
    materials_resolved: bool
    completion_evidence: CompletionEvidence | None
    billing_metadata: BillingMetadata
    job_type: str = "RESIDENTIAL_STANDARD"
    customer_approved: bool = False
    exceptions: tuple[ReadinessException, ...] = ()


@dataclass(frozen=True)
class InvoiceReadiness:
    authoritative_job_id: str
    status: InvoiceReadinessState
    evaluated_at: datetime
    correlation_id: str
    satisfied_checks: tuple[str, ...]
    blocking_checks: tuple[str, ...]
    checks: tuple[ReadinessCheck, ...]
    fingerprint: str


@dataclass(frozen=True)
class InvoiceReadyCommand:
    correlation_id: str
    idempotency_key: str
    authoritative_job_id: str
    accounting_customer_id: str
    completion_date: date
    job_reference: str
    billing_summary: str


@dataclass(frozen=True)
class BillingReadyAcknowledgement:
    correlation_id: str
    idempotency_key: str
    billing_work_item_reference: str
    outcome: SubmissionOutcome


@dataclass(frozen=True)
class ReadinessResult:
    readiness: InvoiceReadiness
    command: InvoiceReadyCommand | None
    acknowledgement: BillingReadyAcknowledgement | None
    events: tuple[IntegrationEvent, ...]
    stale_input: bool = False


class LedgerProBoundary:
    """In-memory billing-work-item boundary; it has no invoice model or operation."""

    def __init__(self) -> None:
        self.work_items: dict[str, BillingReadyAcknowledgement] = {}

    def submit_invoice_ready(self, command: InvoiceReadyCommand) -> BillingReadyAcknowledgement:
        existing = self.work_items.get(command.idempotency_key)
        if existing:
            return BillingReadyAcknowledgement(command.correlation_id, command.idempotency_key,
                                                existing.billing_work_item_reference,
                                                SubmissionOutcome.IDEMPOTENT_REPLAY)
        ack = BillingReadyAcknowledgement(command.correlation_id, command.idempotency_key,
                                          f"LP-BILL-READY-{len(self.work_items)+1:03d}",
                                          SubmissionOutcome.ACKNOWLEDGED)
        self.work_items[command.idempotency_key] = ack
        return ack

    def find_invoice_ready_reference(self, key: str) -> str | None:
        item = self.work_items.get(key)
        return item.billing_work_item_reference if item else None


class InvoiceReadinessService:
    REQUIRED_METADATA = ("job_reference", "completion_date", "billing_summary", "billing_category")

    def __init__(self, customer_mappings: dict[str, str], ledgerpro: LedgerProBoundary | None = None,
                 approval_required_job_types: frozenset[str] = frozenset({"COMMERCIAL_CHANGE_ORDER"})):
        self.customer_mappings = customer_mappings
        self.ledgerpro = ledgerpro or LedgerProBoundary()
        self.approval_required_job_types = approval_required_job_types

    def evaluate(self, facts: ReadinessFacts, evaluated_at: datetime | None = None) -> ReadinessResult:
        now = evaluated_at or facts.authoritative_updated_at
        corr = facts.field_observation.correlation_id
        events = [self._event("JOB_COMPLETION_EVALUATED", facts, now, corr),
                  self._event("INVOICE_READINESS_CHECK_STARTED", facts, now, corr)]
        stale = facts.field_observation.occurred_at < facts.authoritative_updated_at
        mapped = self.customer_mappings.get(facts.authoritative_customer_id)
        missing = [name for name in self.REQUIRED_METADATA
                   if not getattr(facts.billing_metadata, name)]
        evidence_ok = bool(facts.completion_evidence and
                           facts.completion_evidence.authoritative_job_id == facts.authoritative_job_id and
                           facts.completion_evidence.completion_code and facts.completion_evidence.acknowledged)
        approval_required = facts.job_type in self.approval_required_job_types
        blockers = tuple(e for e in facts.exceptions if e.unresolved and e.blocks_invoice_readiness)
        checks = (
            self._check("FIELD_COMPLETED", facts.field_observation.canonical_status is FieldStatus.COMPLETED,
                        "canonical field status must be COMPLETED", not_ready=True),
            self._check("JOB_STATE_VALID", facts.authoritative_job_state is JobState.COMPLETED,
                        "operational job state must be COMPLETED"),
            self._check("MATERIALS_RESOLVED", facts.materials_resolved,
                        "required material exception remains unresolved"),
            self._check("COMPLETION_EVIDENCE", evidence_ok, "required acknowledged completion code is missing"),
            self._check("ACCOUNTING_CUSTOMER_MAPPED", bool(mapped), "approved LedgerPro customer mapping is missing"),
            self._check("BILLING_METADATA_COMPLETE", not missing,
                        "missing: " + ", ".join(missing) if missing else "required billing metadata present"),
            self._check("BLOCKING_EXCEPTIONS_CLEAR", not blockers,
                        "; ".join(e.summary for e in blockers) if blockers else "no unresolved billing-blocking exception"),
            (self._check("CUSTOMER_APPROVAL", facts.customer_approved, "required customer approval is missing")
             if approval_required else ReadinessCheck("CUSTOMER_APPROVAL", CheckOutcome.NOT_APPLICABLE,
                                                       "not required for this modeled job type")),
        )
        if stale:
            checks += (ReadinessCheck("AUTHORITATIVE_FRESHNESS", CheckOutcome.BLOCKED,
                                      "completion observation predates authoritative job state"),)
        field_failed = checks[0].outcome is CheckOutcome.FAIL
        blocked = any(c.outcome is CheckOutcome.BLOCKED for c in checks)
        status = (InvoiceReadinessState.NOT_READY if field_failed else
                  InvoiceReadinessState.BLOCKED if blocked else InvoiceReadinessState.READY)
        fingerprint = readiness_fingerprint(facts, mapped)
        readiness = InvoiceReadiness(facts.authoritative_job_id, status, now, corr,
                                     tuple(c.name for c in checks if c.outcome in (CheckOutcome.PASS, CheckOutcome.NOT_APPLICABLE)),
                                     tuple(f"{c.name}: {c.detail}" for c in checks if c.outcome in (CheckOutcome.FAIL, CheckOutcome.BLOCKED)),
                                     checks, fingerprint)
        if status is not InvoiceReadinessState.READY:
            if not mapped:
                events.extend((self._event("ACCOUNTING_CUSTOMER_MAPPING_FAILED", facts, now, corr),
                               self._event("EXCEPTION_CREATED", facts, now, corr)))
            events.append(self._event("INVOICE_READINESS_BLOCKED", facts, now, corr))
            return ReadinessResult(readiness, None, None, tuple(events), stale)
        metadata = facts.billing_metadata
        command = InvoiceReadyCommand(corr, fingerprint, facts.authoritative_job_id, mapped,
                                      metadata.completion_date, metadata.job_reference,
                                      metadata.billing_summary)
        events.extend((self._event("INVOICE_READINESS_READY", facts, now, corr),
                       self._event("INVOICE_READY_COMMAND_SENT", facts, now, corr)))
        ack = self.ledgerpro.submit_invoice_ready(command)
        events.append(self._event("INVOICE_READY_REPLAY_DETECTED" if ack.outcome is SubmissionOutcome.IDEMPOTENT_REPLAY
                                  else "INVOICE_READY_ACKNOWLEDGED", facts, now, corr))
        return ReadinessResult(readiness, command, ack, tuple(events))

    @staticmethod
    def _check(name, passed, detail, not_ready=False):
        return ReadinessCheck(name, CheckOutcome.PASS if passed else
                              (CheckOutcome.FAIL if not_ready else CheckOutcome.BLOCKED),
                              "modeled prerequisite satisfied" if passed else detail)

    @staticmethod
    def _event(kind, facts, when, correlation):
        return IntegrationEvent(f"{correlation}-{kind}", kind, "CompletionReadiness",
                                facts.field_observation.source_event_id, "JOB",
                                facts.authoritative_job_id, when, correlation)


def readiness_fingerprint(facts: ReadinessFacts, accounting_customer_id: str | None) -> str:
    """Hash only modeled billing-relevant facts; ordering is deterministic."""
    evidence = facts.completion_evidence
    blockers = sorted(e.exception_id for e in facts.exceptions if e.unresolved and e.blocks_invoice_readiness)
    parts = (facts.authoritative_job_id, facts.job_version, facts.authoritative_job_state.value,
             facts.field_observation.canonical_status.value, str(evidence.completed_at if evidence else ""),
             evidence.version if evidence else "", accounting_customer_id or "UNMAPPED",
             facts.billing_metadata.version, str(facts.billing_metadata.completion_date or ""),
             facts.job_type, str(facts.customer_approved), *blockers)
    return sha256("|".join(parts).encode()).hexdigest()


VALUE_MECHANISM = {
    "path": "COMPLETION → reconciliation / missing prerequisites / delay → INVOICE READINESS",
    "may_reduce": ("administrative touches", "unresolved prerequisite chasing", "avoidable readiness delay"),
    "invoice_principal": "NOT INCLUDED",
}

ARCHITECTURE_INVENTORY = (
    ("SHARED CORE", "canonical states, correlation, events, deterministic fingerprints"),
    ("SOURCE-SPECIFIC ADAPTER", "LedgerPro customer mapping and billing-work-item boundary"),
    ("WORKFLOW-SPECIFIC LOGIC", "billing readiness gates and completion evidence"),
    ("CUSTOMER-SPECIFIC RULE", "change-order approval and exception blocking policy"),
    ("CONFIGURATION", "accounting customer mappings and required billing fields"),
    ("VALIDATION", "explicit explainable prerequisite checklist"),
    ("RELIABILITY", "business fingerprint and idempotent work-item submission"),
    ("EXCEPTION HANDLING", "missing identity and explicit billing impact"),
    ("TESTING", "deterministic ready, blocked, replay, change, and stale scenarios"),
    ("SUPPORT SURFACE", "mappings, metadata, approvals, interface, exceptions, evidence"),
)
