"""A deliberately small, synchronous reliability experiment.

This is an in-memory fault laboratory, not a queue or production delivery system.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import StrEnum


class FailureCategory(StrEnum):
    TRANSIENT = "TRANSIENT"
    PERMANENT_VALIDATION = "PERMANENT_VALIDATION"
    CONFLICT = "CONFLICT"
    AUTHENTICATION = "AUTHENTICATION"
    UNCERTAIN_OUTCOME = "UNCERTAIN_OUTCOME"


class AttemptOutcome(StrEnum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    UNCERTAIN = "UNCERTAIN"


class DeliveryState(StrEnum):
    PENDING = "PENDING"
    RETRYABLE = "RETRYABLE"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    BLOCKED = "BLOCKED"
    UNCERTAIN = "UNCERTAIN"
    EXHAUSTED = "EXHAUSTED"


class RetryDecision(StrEnum):
    RETRY = "RETRY"
    STOP = "STOP"
    RECONCILE_FIRST = "RECONCILE_FIRST"
    WAIT_FOR_REPAIR = "WAIT_FOR_REPAIR"


class Fault(StrEnum):
    SUCCESS = "SUCCESS"
    UNAVAILABLE = "UNAVAILABLE"
    TIMEOUT_BEFORE_WRITE = "TIMEOUT_BEFORE_WRITE"
    SERVICE_BUSY = "SERVICE_BUSY"
    ACKNOWLEDGEMENT_LOST = "ACKNOWLEDGEMENT_LOST"
    MALFORMED = "MALFORMED"
    CONFLICT = "CONFLICT"
    EXPIRED_CREDENTIALS = "EXPIRED_CREDENTIALS"


@dataclass(frozen=True)
class DeliveryAttempt:
    attempt_number: int
    attempt_id: str
    started_at: datetime
    outcome: AttemptOutcome
    failure_category: FailureCategory | None = None
    detail: str | None = None


@dataclass(frozen=True)
class ReliabilityEvent:
    event_type: str
    occurred_at: datetime
    correlation_id: str
    attempt_number: int | None = None


@dataclass(frozen=True)
class DeliveryException:
    category: FailureCategory
    summary: str
    correlation_id: str


@dataclass
class Delivery:
    delivery_id: str
    business_event_id: str
    idempotency_key: str
    correlation_id: str
    payload: dict[str, str]
    state: DeliveryState = DeliveryState.PENDING
    attempts: list[DeliveryAttempt] = field(default_factory=list)
    events: list[ReliabilityEvent] = field(default_factory=list)
    acknowledgement: str | None = None
    exception: DeliveryException | None = None
    human_review_required: bool = False


MAX_ATTEMPTS = 3
FIXTURE_TIME = datetime(2026, 1, 9, 9, 0, tzinfo=timezone.utc)


def retry_decision(failure: FailureCategory, attempt_number: int,
                   maximum_attempts: int = MAX_ATTEMPTS) -> RetryDecision:
    """Make retry behavior visible rather than hiding it in an exception handler."""
    if failure is FailureCategory.TRANSIENT:
        return RetryDecision.RETRY if attempt_number < maximum_attempts else RetryDecision.STOP
    if failure is FailureCategory.UNCERTAIN_OUTCOME:
        return RetryDecision.RECONCILE_FIRST
    if failure is FailureCategory.AUTHENTICATION:
        return RetryDecision.WAIT_FOR_REPAIR
    return RetryDecision.STOP


class FaultScriptDestination:
    """A consequential-create boundary driven only by a supplied fault sequence."""

    def __init__(self, faults: list[Fault] | tuple[Fault, ...] = (), *,
                 supports_lookup: bool = True, credentials_repaired: bool = False) -> None:
        self.faults = list(faults)
        self.supports_lookup = supports_lookup
        self.credentials_repaired = credentials_repaired
        self.effects: dict[str, str] = {}
        self.write_calls = 0
        self.lookup_calls = 0

    def write(self, idempotency_key: str) -> tuple[AttemptOutcome, FailureCategory | None, str]:
        self.write_calls += 1
        fault = self.faults.pop(0) if self.faults else Fault.SUCCESS
        if fault is Fault.EXPIRED_CREDENTIALS and self.credentials_repaired:
            fault = Fault.SUCCESS
        if fault in (Fault.UNAVAILABLE, Fault.TIMEOUT_BEFORE_WRITE, Fault.SERVICE_BUSY):
            return AttemptOutcome.FAILED, FailureCategory.TRANSIENT, fault.value
        if fault is Fault.MALFORMED:
            return AttemptOutcome.FAILED, FailureCategory.PERMANENT_VALIDATION, "malformed event"
        if fault is Fault.CONFLICT:
            return AttemptOutcome.FAILED, FailureCategory.CONFLICT, "incompatible destination state"
        if fault is Fault.EXPIRED_CREDENTIALS:
            return AttemptOutcome.FAILED, FailureCategory.AUTHENTICATION, "credentials expired"
        destination_id = self.effects.setdefault(idempotency_key, f"JOB-{9000 + len(self.effects) + 1}")
        if fault is Fault.ACKNOWLEDGEMENT_LOST:
            return AttemptOutcome.UNCERTAIN, FailureCategory.UNCERTAIN_OUTCOME, "write accepted; acknowledgement lost"
        return AttemptOutcome.SUCCESS, None, destination_id

    def lookup(self, idempotency_key: str) -> str | None:
        if not self.supports_lookup:
            raise NotImplementedError("stable external-reference lookup is unavailable")
        self.lookup_calls += 1
        return self.effects.get(idempotency_key)

    def repair_credentials(self) -> None:
        self.credentials_repaired = True


class ReliableHandoff:
    """Wrap one selected consequential create with bounded retry and targeted lookup."""

    def __init__(self, destination: FaultScriptDestination, *, maximum_attempts: int = MAX_ATTEMPTS) -> None:
        self.destination = destination
        self.maximum_attempts = maximum_attempts
        self.deliveries: dict[str, Delivery] = {}

    def new_delivery(self, business_event_id: str, idempotency_key: str,
                     correlation_id: str, payload: dict[str, str] | None = None,
                     delivery_id: str = "delivery-001") -> Delivery:
        # A duplicate transport envelope joins the logical delivery; it cannot fork the effect.
        existing = next((d for d in self.deliveries.values()
                         if d.idempotency_key == idempotency_key), None)
        if existing:
            return existing
        delivery = Delivery(delivery_id, business_event_id, idempotency_key,
                            correlation_id, payload or {})
        self.deliveries[delivery_id] = delivery
        return delivery

    def execute(self, delivery: Delivery, *, reconcile_uncertain: bool = True) -> Delivery:
        while delivery.state not in (DeliveryState.ACKNOWLEDGED, DeliveryState.BLOCKED,
                                     DeliveryState.EXHAUSTED):
            if len(delivery.attempts) >= self.maximum_attempts:
                delivery.state = DeliveryState.EXHAUSTED
                self._event(delivery, "DELIVERY_RETRY_EXHAUSTED")
                break
            number = len(delivery.attempts) + 1
            self._event(delivery, "DELIVERY_ATTEMPT_STARTED", number)
            outcome, category, detail = self.destination.write(delivery.idempotency_key)
            delivery.attempts.append(DeliveryAttempt(number, f"{delivery.delivery_id}:attempt:{number}",
                FIXTURE_TIME + timedelta(minutes=number - 1), outcome, category, detail))
            if outcome is AttemptOutcome.SUCCESS:
                delivery.acknowledgement = detail
                delivery.state = DeliveryState.ACKNOWLEDGED
                self._event(delivery, "DELIVERY_ACKNOWLEDGED", number)
                break
            assert category is not None
            if category is FailureCategory.UNCERTAIN_OUTCOME:
                delivery.state = DeliveryState.UNCERTAIN
                self._event(delivery, "DELIVERY_OUTCOME_UNCERTAIN", number)
                if reconcile_uncertain:
                    self.reconcile(delivery)
                break  # never blind-write after uncertainty
            decision = retry_decision(category, number, self.maximum_attempts)
            if category is FailureCategory.TRANSIENT:
                self._event(delivery, "DELIVERY_TRANSIENT_FAILURE", number)
                if decision is RetryDecision.RETRY:
                    delivery.state = DeliveryState.RETRYABLE
                    self._event(delivery, "DELIVERY_RETRY_SCHEDULED", number)
                    continue
                delivery.state = DeliveryState.EXHAUSTED
                self._event(delivery, "DELIVERY_RETRY_EXHAUSTED", number)
            elif category is FailureCategory.AUTHENTICATION:
                delivery.state = DeliveryState.BLOCKED
                self._event(delivery, "DELIVERY_AUTHENTICATION_BLOCKED", number)
                self._exception(delivery, category, detail)
            else:
                delivery.state = DeliveryState.BLOCKED
                self._event(delivery, "DELIVERY_CONFLICT" if category is FailureCategory.CONFLICT
                            else "DELIVERY_VALIDATION_FAILED", number)
                self._exception(delivery, category, detail)
            break
        return delivery

    def reconcile(self, delivery: Delivery) -> Delivery:
        if delivery.state is not DeliveryState.UNCERTAIN:
            return delivery
        self._event(delivery, "DESTINATION_LOOKUP_STARTED")
        try:
            found = self.destination.lookup(delivery.idempotency_key)
        except NotImplementedError:
            found = None
        if found:
            delivery.acknowledgement = found
            delivery.state = DeliveryState.ACKNOWLEDGED
            self._event(delivery, "DESTINATION_EXISTING_EFFECT_CONFIRMED")
            self._event(delivery, "DELIVERY_ACKNOWLEDGED")
        else:
            delivery.state = DeliveryState.BLOCKED
            delivery.human_review_required = True
            self._exception(delivery, FailureCategory.UNCERTAIN_OUTCOME,
                            "effect cannot be proven; blind replay is unsafe")
        return delivery

    def replay(self, delivery_id: str) -> Delivery:
        """Add an attempt to the same logical event, identity, and correlation."""
        delivery = self.deliveries[delivery_id]
        if delivery.state is DeliveryState.BLOCKED and delivery.exception and \
                delivery.exception.category is FailureCategory.AUTHENTICATION and \
                self.destination.credentials_repaired:
            delivery.state, delivery.exception = DeliveryState.PENDING, None
        elif delivery.state in (DeliveryState.EXHAUSTED, DeliveryState.RETRYABLE):
            delivery.state = DeliveryState.PENDING
        elif delivery.state is DeliveryState.UNCERTAIN:
            return self.reconcile(delivery)
        return self.execute(delivery)

    @staticmethod
    def _event(delivery: Delivery, name: str, attempt: int | None = None) -> None:
        sequence = len(delivery.events)
        delivery.events.append(ReliabilityEvent(name, FIXTURE_TIME + timedelta(seconds=sequence),
                                                delivery.correlation_id, attempt))

    def _exception(self, delivery: Delivery, category: FailureCategory, detail: str) -> None:
        delivery.exception = DeliveryException(category, detail, delivery.correlation_id)
        self._event(delivery, "EXCEPTION_CREATED")


ARCHITECTURE_INVENTORY = (
    ("SHARED CORE", "business idempotency identity and correlation"),
    ("VALIDATION", "permanent malformed-event classification"),
    ("RELIABILITY", "attempt history, explicit bounded policy, replay, and targeted lookup"),
    ("EXCEPTION HANDLING", "conflict, authentication, and uncertainty records"),
    ("TESTING", "deterministic destination fault scripts"),
    ("SUPPORT SURFACE", "exhaustion, credential repair, uncertainty, replay audit, and conflicts"),
    ("SOURCE-SPECIFIC ADAPTER", "vendor response classification and lookup capability"),
    ("WORKFLOW-SPECIFIC LOGIC", "consequential-create conflict semantics"),
    ("CONFIGURATION", "maximum attempts and deterministic fixture timestamps"),
)
