"""A deliberately small, in-memory exception workflow (not a ticket system)."""

from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from enum import StrEnum

from trades_lab.domain import ExceptionCategory, ExceptionRecord, ExceptionStatus

FIXTURE_TIME = datetime(2026, 1, 11, 12, 0, tzinfo=timezone.utc)


class OwnerRole(StrEnum):
    OFFICE_MANAGER = "OFFICE_MANAGER"
    OPERATIONS_MANAGER = "OPERATIONS_MANAGER"
    ESTIMATOR = "ESTIMATOR"
    FIELD_SUPERVISOR = "FIELD_SUPERVISOR"
    ACCOUNTING_LEAD = "ACCOUNTING_LEAD"
    INTEGRATION_SUPPORT = "INTEGRATION_SUPPORT"


class BusinessImpact(StrEnum):
    BLOCKS_HANDOFF = "BLOCKS_HANDOFF"
    BLOCKS_BILLING = "BLOCKS_BILLING"
    OPERATIONAL_REVIEW = "OPERATIONAL_REVIEW"
    INFORMATIONAL = "INFORMATIONAL"


class ResolutionAction(StrEnum):
    CONFIRM_IDENTITY = "CONFIRM_IDENTITY"
    CREATE_MAPPING = "CREATE_MAPPING"
    APPROVE_SUBSTITUTION = "APPROVE_SUBSTITUTION"
    CONFIRM_STATE = "CONFIRM_STATE"
    PROVIDE_MISSING_DATA = "PROVIDE_MISSING_DATA"
    REPAIR_ACCESS = "REPAIR_ACCESS"
    APPROVE_REPLAY = "APPROVE_REPLAY"
    MARK_EXPECTED_DIFFERENCE = "MARK_EXPECTED_DIFFERENCE"
    DISMISS_INVALID_FINDING = "DISMISS_INVALID_FINDING"


class AgeBucket(StrEnum):
    NEW = "NEW"
    AGING = "AGING"
    OVERDUE = "OVERDUE"


class AuditEventType(StrEnum):
    EXCEPTION_CREATED = "EXCEPTION_CREATED"
    EXCEPTION_ASSIGNED = "EXCEPTION_ASSIGNED"
    EXCEPTION_REVIEW_STARTED = "EXCEPTION_REVIEW_STARTED"
    EXCEPTION_RESOLVED = "EXCEPTION_RESOLVED"
    EXCEPTION_DISMISSED = "EXCEPTION_DISMISSED"
    REPLAY_APPROVED = "REPLAY_APPROVED"


@dataclass(frozen=True)
class AuditEvent:
    event_type: AuditEventType
    occurred_at: datetime
    actor_role: OwnerRole
    detail: str


@dataclass(frozen=True)
class ResolutionResult:
    exception_id: str
    prior_status: ExceptionStatus
    owner_role: OwnerRole
    resolution_action: ResolutionAction
    resolution_summary: str
    resolved_at: datetime
    actor_role: OwnerRole
    entity_id: str
    correlation_id: str
    automation_may_resume: bool
    replay_recommended: bool
    manual_follow_up_remains: bool


@dataclass(frozen=True)
class ManagedException:
    record: ExceptionRecord
    condition_key: str
    owner_role: OwnerRole
    impact: BusinessImpact
    history: tuple[AuditEvent, ...]
    resolution: ResolutionResult | None = None
    replay_approved: bool = False

    @property
    def status(self) -> ExceptionStatus:
        return self.record.status


ROUTING = {
    ExceptionCategory.IDENTITY: OwnerRole.OFFICE_MANAGER,
    ExceptionCategory.MAPPING: OwnerRole.OPERATIONS_MANAGER,
    ExceptionCategory.STATE_CONFLICT: OwnerRole.OPERATIONS_MANAGER,
    ExceptionCategory.VALIDATION: OwnerRole.ESTIMATOR,
    ExceptionCategory.UNSUPPORTED: OwnerRole.ESTIMATOR,
    ExceptionCategory.ACCESS: OwnerRole.INTEGRATION_SUPPORT,
    ExceptionCategory.AUTHENTICATION: OwnerRole.INTEGRATION_SUPPORT,
    ExceptionCategory.ACCOUNTING_MAPPING: OwnerRole.ACCOUNTING_LEAD,
    ExceptionCategory.DELIVERY: OwnerRole.INTEGRATION_SUPPORT,
    ExceptionCategory.RECONCILIATION: OwnerRole.OPERATIONS_MANAGER,
}

ALLOWED_ACTIONS = {
    ExceptionCategory.IDENTITY: {ResolutionAction.CONFIRM_IDENTITY},
    ExceptionCategory.MAPPING: {ResolutionAction.CREATE_MAPPING, ResolutionAction.APPROVE_SUBSTITUTION},
    ExceptionCategory.STATE_CONFLICT: {ResolutionAction.CONFIRM_STATE, ResolutionAction.MARK_EXPECTED_DIFFERENCE,
                                       ResolutionAction.DISMISS_INVALID_FINDING},
    ExceptionCategory.VALIDATION: {ResolutionAction.PROVIDE_MISSING_DATA},
    ExceptionCategory.UNSUPPORTED: {ResolutionAction.PROVIDE_MISSING_DATA},
    ExceptionCategory.ACCESS: {ResolutionAction.REPAIR_ACCESS},
    ExceptionCategory.AUTHENTICATION: {ResolutionAction.REPAIR_ACCESS},
    ExceptionCategory.ACCOUNTING_MAPPING: {ResolutionAction.CREATE_MAPPING},
    ExceptionCategory.DELIVERY: {ResolutionAction.APPROVE_REPLAY},
    ExceptionCategory.RECONCILIATION: {ResolutionAction.CONFIRM_STATE,
                                       ResolutionAction.MARK_EXPECTED_DIFFERENCE,
                                       ResolutionAction.DISMISS_INVALID_FINDING},
}


def route_owner(category: ExceptionCategory, *, accounting_mapping: bool = False) -> OwnerRole:
    if accounting_mapping:
        return OwnerRole.ACCOUNTING_LEAD
    return ROUTING[category]


def age_bucket(created_at: datetime, now: datetime = FIXTURE_TIME) -> AgeBucket:
    age = now - created_at
    if age < timedelta(days=1):
        return AgeBucket.NEW
    if age <= timedelta(days=3):
        return AgeBucket.AGING
    return AgeBucket.OVERDUE


class ExceptionWorkflow:
    """Owns integration decisions only; it has no source-system write adapter."""

    def __init__(self) -> None:
        self.exceptions: dict[str, ManagedException] = {}
        self.integration_mappings: dict[str, str] = {}
        self.access_repairs: set[str] = set()

    def create(self, record: ExceptionRecord, condition_key: str, impact: BusinessImpact,
               *, accounting_mapping: bool = False) -> ManagedException:
        for item in self.exceptions.values():
            if item.condition_key == condition_key and item.status in {ExceptionStatus.OPEN, ExceptionStatus.IN_REVIEW}:
                return item
        owner = route_owner(record.category, accounting_mapping=accounting_mapping)
        created = AuditEvent(AuditEventType.EXCEPTION_CREATED, record.created_at, owner, condition_key)
        assigned = AuditEvent(AuditEventType.EXCEPTION_ASSIGNED, record.created_at, owner, owner.value)
        item = ManagedException(record, condition_key, owner, impact, (created, assigned))
        self.exceptions[record.exception_id] = item
        return item

    def start_review(self, exception_id: str, actor: OwnerRole,
                     at: datetime = FIXTURE_TIME) -> ManagedException:
        item = self.exceptions[exception_id]
        if item.status is not ExceptionStatus.OPEN:
            raise ValueError(f"invalid transition {item.status.value} -> IN_REVIEW")
        event = AuditEvent(AuditEventType.EXCEPTION_REVIEW_STARTED, at, actor, "review started")
        updated = replace(item, record=replace(item.record, status=ExceptionStatus.IN_REVIEW),
                          history=item.history + (event,))
        self.exceptions[exception_id] = updated
        return updated


    def resolve(self, exception_id: str, action: ResolutionAction, summary: str, actor: OwnerRole,
                *, mapping: tuple[str, str] | None = None, underlying_issue_addressed: bool = True,
                at: datetime = FIXTURE_TIME) -> ManagedException:
        item = self.exceptions[exception_id]
        if item.status not in {ExceptionStatus.OPEN, ExceptionStatus.IN_REVIEW}:
            raise ValueError(f"cannot resolve exception in {item.status.value}")
        if action not in ALLOWED_ACTIONS[item.record.category]:
            raise ValueError(f"{action.value} is not allowed for {item.record.category.value}")
        if not underlying_issue_addressed:
            raise ValueError("underlying issue must be addressed before resolution")
        if action in {ResolutionAction.CREATE_MAPPING, ResolutionAction.CONFIRM_IDENTITY}:
            if mapping is None:
                raise ValueError("an explicit integration mapping is required")
            self.integration_mappings[mapping[0]] = mapping[1]
        if action is ResolutionAction.REPAIR_ACCESS:
            self.access_repairs.add(item.record.source_system)
        dismissed = action is ResolutionAction.DISMISS_INVALID_FINDING
        status = ExceptionStatus.DISMISSED if dismissed else ExceptionStatus.RESOLVED
        replay = action in {ResolutionAction.CREATE_MAPPING, ResolutionAction.REPAIR_ACCESS,
                            ResolutionAction.APPROVE_REPLAY}
        resume = action in {ResolutionAction.CONFIRM_IDENTITY, ResolutionAction.CREATE_MAPPING,
                            ResolutionAction.PROVIDE_MISSING_DATA, ResolutionAction.REPAIR_ACCESS}
        result = ResolutionResult(exception_id, item.status, item.owner_role, action, summary, at, actor,
                                  item.record.entity_id, item.record.correlation_id, resume, replay, False)
        kind = AuditEventType.EXCEPTION_DISMISSED if dismissed else AuditEventType.EXCEPTION_RESOLVED
        updated = replace(item, record=replace(item.record, status=status), resolution=result,
                          history=item.history + (AuditEvent(kind, at, actor, summary),))
        self.exceptions[exception_id] = updated
        return updated

    def approve_replay(self, exception_id: str, actor: OwnerRole,
                       at: datetime = FIXTURE_TIME) -> ManagedException:
        item = self.exceptions[exception_id]
        if item.status is not ExceptionStatus.RESOLVED or not item.resolution or not item.resolution.replay_recommended:
            raise ValueError("exception is not an eligible replay candidate")
        updated = replace(item, replay_approved=True, history=item.history +
                          (AuditEvent(AuditEventType.REPLAY_APPROVED, at, actor, "replay authorized; not executed"),))
        self.exceptions[exception_id] = updated
        return updated

    def queue(self, *, status: ExceptionStatus | None = None, owner: OwnerRole | None = None,
              impact: BusinessImpact | None = None, category: ExceptionCategory | None = None,
              age: AgeBucket | None = None, now: datetime = FIXTURE_TIME) -> tuple[ManagedException, ...]:
        values = self.exceptions.values()
        return tuple(sorted((x for x in values if (status is None or x.status is status)
                            and (owner is None or x.owner_role is owner)
                            and (impact is None or x.impact is impact)
                            and (category is None or x.record.category is category)
                            and (age is None or age_bucket(x.record.created_at, now) is age)),
                            key=lambda x: x.record.exception_id))


def finding_requires_exception(*, requires_review: bool, severity: str, informational_only: bool = False) -> bool:
    """A finding is evidence; only actionable review becomes managed work."""
    return requires_review and not informational_only and severity in {"WARNING", "CRITICAL"}


ARCHITECTURE_INVENTORY = (
    ("SHARED CORE", "ExceptionRecord, correlation, deterministic identity, audit-event concepts"),
    ("WORKFLOW-SPECIFIC LOGIC", "allowed actions, impact semantics, finding conversion"),
    ("CUSTOMER-SPECIFIC RULE", "James River Mechanical role routing"),
    ("CONFIGURATION", "modeled owner, action, replay and aging rules"),
    ("VALIDATION", "lifecycle and category/action validation"),
    ("EXCEPTION HANDLING", "deduplication, bounded resolution, dismissal, replay approval"),
    ("SUPPORT SURFACE", "queue ownership, mapping/access maintenance, replay and audit retention"),
    ("TESTING", "authority, immutability, aging, lifecycle and replay behaviors"),
)
