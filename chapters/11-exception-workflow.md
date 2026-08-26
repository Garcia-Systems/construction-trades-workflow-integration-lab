# Chapter 11 — Exception Workflow

Human exceptions are not integration failure. **Uncontrolled exceptions are.** When safe
automation stops, this chapter turns an ambiguous condition into a small, owned decision;
it does not attempt to eliminate human work or become ticketing, CRM, workflow, or reporting software.

```text
AUTOMATION STOPS
      ↓
EXCEPTION CREATED
      ↓
ROUTE TO OWNER
      ↓
HUMAN REVIEW
      ↓
   ┌──┼───────────────┐
   ↓  ↓               ↓
RESOLVE DISMISS   NEEDS FOLLOW-UP
   ↓
OPTIONAL REPLAY APPROVAL
   ↓
AUTOMATION MAY RESUME

SOURCE SYSTEMS REMAIN AUTHORITATIVE
```

## Finding and exception

A reconciliation **finding** is evidence of disagreement or a missing handoff. An
**exception** is an actionable operational item requiring intervention. The deterministic
conversion predicate admits warning/critical review work but leaves informational report
items alone. Repeated detection of the same condition returns the active occurrence. If a
resolved condition genuinely recurs, a new ID is created; the resolved occurrence remains historical.

## Controlled lifecycle and ownership

The bounded lifecycle is `OPEN → IN_REVIEW → RESOLVED | DISMISSED`; a clear category-specific
action may resolve an open item directly. Invalid transitions and invalid category/action pairs
fail before mutation. Routing assigns fictional roles: identity to `OFFICE_MANAGER`, mapping and
state conflicts to `OPERATIONS_MANAGER`, access to `INTEGRATION_SUPPORT`, and accounting mapping
to `ACCOUNTING_LEAD`. Validation defaults to `ESTIMATOR`. These routes are not industry guidance.

Actions are bounded: identity confirmation, mapping/substitution approval, state confirmation,
missing-data provision, access repair, expected-difference marking, and false-finding dismissal.
The immutable result retains prior status, owner and actor roles, action and summary, timestamp,
entity/correlation identity, resume eligibility, replay recommendation, and follow-up state.
Append-only immutable audit events retain creation, assignment, review, resolution/dismissal, and
separate replay approval.

## Authority and replay boundary

Identity and material/accounting decisions add only integration mappings. They never alter source
customers or create a LedgerPro customer. State-conflict review records a decision without changing
CrewBoard. Access repair records modeled integration access maintenance. Mapping and access repair
can recommend replay, but resolution performs no replay and cannot fabricate an acknowledged
delivery. `REPLAY_APPROVED` is a separate audited action; Chapter 9 execution remains separate.

## Queue, aging, and support

The read-only queue filters status, owner, impact, category, and age. Fixed fixture-time thresholds
are **MODELED ASSUMPTIONS**: `NEW` is under one day, `AGING` is one through three days, and
`OVERDUE` is over three days. Aging only makes work visible; it never resolves it.

More automation does not necessarily mean zero human work. It can replace repeated manual
coordination with less frequent but higher-skill exception review. Support must therefore account
for queue ownership, mapping maintenance, access repair, replay approval, stale-item cleanup, and
audit retention. No Chapter 18 economic calculation is made.

## Reuse and implementation inventory

- **SHARED CORE:** Chapter 2 `ExceptionRecord` and status, correlation/entity identity,
  deterministic IDs, immutable event concepts; Chapter 10 findings; Chapter 9 replay eligibility.
- **WORKFLOW-SPECIFIC LOGIC / VALIDATION:** allowed actions, impacts, lifecycle, and finding conversion.
- **CUSTOMER-SPECIFIC RULE / CONFIGURATION:** fictional James River Mechanical roles, routing,
  action/replay policy, and aging thresholds.
- **EXCEPTION HANDLING:** active-condition deduplication, recurrence, resolution, dismissal, and audit.
- **SUPPORT SURFACE:** owner queue, mapping/access maintenance, replay decisions, cleanup, retention.
- **TESTING:** source-authority, no-mutation rejection, audit, lifecycle, replay, queue, and aging behavior.

There is no new source adapter: this boundary coordinates decisions around existing adapters.

## Evidence and limitations

**OBSERVED LAB RESULT:** within deterministic in-memory fixtures, routing is deterministic; invalid
actions do not mutate an exception; audit history survives resolution; duplicate active conditions
deduplicate; recurrences preserve history; mappings do not rewrite sources; access/mapping resolution
can become a separately approved replay candidate; dismissal stays auditable; and aging is deterministic.

**MODELED ASSUMPTION:** roles, routes, impacts, thresholds, allowed actions, fixture evidence, and which
actions permit resumption/replay. They are not claimed to be optimal operating procedures.

This is process-local demonstration code, not persistence, authentication, permissions, notification,
SLA, background processing, or a generic case system. It does not implement Chapter 12's management briefing.
