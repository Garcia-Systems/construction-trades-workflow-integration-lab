# Chapter 13 — Production Integration Engineering

## Working logic is not an operable service

Chapters 3–12 demonstrate workflow decisions, bounded writes, reliability, reconciliation,
human review, and briefing. An operable service needs another layer around that application
logic. This chapter adds a deterministic **production-like simulation**, not a deployment:

```text
BUSINESS WORKFLOWS
       ↓
RELIABILITY + EXCEPTIONS
       ↓
RECONCILIATION
       ↓
PRODUCTION RUNTIME
       ↓
 ┌─────┼─────┬─────┬─────┐
 ↓     ↓     ↓     ↓     ↓
CONFIG HEALTH LOGS METRICS ALERTS
                    ↓
              OPERATIONS
                    ↓
              RUNBOOKS
```

The runtime wraps existing application services; it does not move business rules into a
scheduler or make integration state authoritative.

## Configuration, secrets, and startup

`IntegrationRuntimeConfig` describes environment (`development`, `test`, or
`production-like`), service name, enabled recurring work, retry limit, configured adapters,
and mapping availability. `load_runtime_config` accepts an explicit mapping rather than
implicitly reading the user's environment, so tests remain deterministic.

A `CredentialReference` says **which credential is required and where it would come from**.
It never contains the credential value. The local fixture supplies only available reference
names. Startup validates supported environment, service name, positive retry/schedule values,
adapters, mapping configuration, and resolvable references. It returns `READY` or `FAILED`
with explicit diagnostics instead of deferring a mysterious error until workflow execution.

Deployment configuration, reference availability, adapter requirements, and validation rules
are **MODELED ASSUMPTIONS**.

## Liveness, readiness, and capability-aware degradation

Liveness answers whether the process is running. Readiness answers whether expected work can
currently be performed. These are deliberately distinct: a live process can be degraded.
Synthetic dependency health uses `HEALTHY`, `DEGRADED`, and `UNHEALTHY`.

An explicit capability graph derives `AVAILABLE`, `DEGRADED`, or `UNAVAILABLE` for lead to
estimate, estimate to job, scheduling, materials, field status, invoice readiness,
reconciliation, and operational briefing. A SupplyDesk outage disables material handoff but
leaves estimate-to-job, scheduling, and field status available. A LedgerPro outage disables
invoice-readiness handoff while earlier operations remain available. Reconciliation depends on
all modeled adapters, so it is unavailable under either outage; this avoids claiming false
independence. Dependency behavior, outage behavior, and this graph are **MODELED ASSUMPTIONS**.

The executable result that liveness and readiness differ, and that only graph-dependent
capabilities stop, is an **OBSERVED LAB RESULT**.

## Structured logs and bounded metrics

`StructuredLogRecord` preserves timestamp, level, event, correlation, entity, attempt, and
exception reference when applicable. Context keys associated with passwords, tokens, secrets,
or credential values are redacted. A safe credential *reference* may remain. Tests inject a
synthetic sensitive value and prove it is absent from serialized output. This is a small safety
boundary, not a complete production data-loss-prevention system.

`MetricSnapshot` derives a bounded inventory from Chapter 9–12 evidence:

- handoff attempts and failures;
- retry attempts, uncertain deliveries, and exhausted deliveries;
- open and overdue exceptions;
- critical reconciliation findings; and
- completed-but-not-invoice-ready work.

Identifiers such as job ID, customer ID, correlation ID, delivery ID, and exception ID belong
in logs, traces, and referenced evidence—not metric labels. Only bounded dimensions such as
`workflow`, `outcome`, and `failure_category` are allowed. The snapshot is deterministic data;
it does not implement Prometheus.

## Alerts are not exceptions

An **exception** is a business/integration case requiring resolution. An **alert** signals that
operators should pay attention to system or workflow health. One exception can contribute to
an alert, but not every exception becomes one, and an alert is not automatically an exception.

The evaluator deterministically produces critical signals for uncertain consequential writes,
critical reconciliation findings, and required dependency outages, plus warnings for overdue
exceptions, retry exhaustion, and excess completed-not-ready work. Evidence references and an
owner survive into alerts. An uncertain-write alert instructs operators to reconcile destination
state and explicitly rejects blind replay. Thresholds and severity rules are **MODELED
ASSUMPTIONS**; no real alert is sent.

## Scheduled controls and overlap prevention

Schedule entries model reconciliation, operational briefing generation, and exception aging.
`due_tasks(now)` compares a fixed time with fixed intervals. `LocalScheduler` creates inspectable
run records with start, finish, outcome, and report reference. A second reconciliation invocation
while the first is active returns `SKIPPED_ALREADY_RUNNING`. Business logic remains in the
reconciler; the scheduler merely invokes and records it.

This in-memory guard only coordinates one process. A real multi-instance service would require
a durable lease or another stronger coordination mechanism. Intervals are **MODELED
ASSUMPTIONS**. Deterministic due-work calculation, run inspection, and local overlap prevention
are **OBSERVED LAB RESULTS**.

## Recovery runbooks and ownership

The machine-readable catalog covers authentication failure, uncertain write, retry exhaustion,
material mapping failure, critical reconciliation mismatch, and dependency outage. Each entry
states the symptom, evidence to inspect, safe first action, forbidden action, and escalation role.
It reuses `INTEGRATION_SUPPORT`, `OPERATIONS_MANAGER`, and `ACCOUNTING_LEAD` where appropriate.

The catalog encodes earlier safety lessons: reconcile uncertainty before replay, do not guess
material identity, preserve attempt history, do not auto-repair authoritative state, and do not
disable unrelated workflows during an outage. Ownership and procedural details remain **MODELED
ASSUMPTIONS**; deterministic lookup and preservation of safe instructions are **OBSERVED LAB
RESULTS**.

## Implementation-structure checkpoint

Actual repository structure now separates:

| Classification | Repository evidence |
|---|---|
| Potential reusable platform/core | explicit configuration loading, startup validation, health structures, redacted structured logs, metric snapshots, alert evaluator, scheduler/run records, and runbook schema |
| Destination-specific | future real dependency probes, vendor authentication semantics, lookup support, and response/failure interpretation |
| Workflow-specific | the capability dependency graph and conditions that warrant workflow alerts |
| Customer-specific configuration | thresholds, intervals, enabled workflows, credential references, and ownership roles |
| Support surface | credential rotation, vendor outages, mapping drift, alert tuning, reconciliation findings, exception review, scheduler failures, log/metric maintenance, and runbook changes |

The runtime owns no adapter method that rewrites an authoritative business system.

### Has the reusable-core hypothesis become more credible?

**Structurally, the narrow reusable-core hypothesis is more credible, but not yet quantified.**
Correlation, idempotency, exception and retry state, reconciliation structures, logging, health,
metrics, alerts, and run records recur without being tied to one vendor. Conversely, adapters,
authentication behavior, mapping content, capability dependencies, and business alert meaning
still vary. This supports reuse of mechanisms—not a claim that an entire integration is reusable,
not the Chapter 0 percentage, and not measured implementation effort.

## Support economics checkpoint

Hardening creates obligations that survive deployment: credential repair, vendor-outage response,
mapping maintenance, exception review, reconciliation, alert investigation, configuration changes,
scheduler diagnosis, observability upkeep, and runbook maintenance. Therefore:

```text
recurring support revenue ≠ pure recurring contribution
```

No support margin, delivery effort, reuse ratio, price, economics recalculation, or deal verdict is
computed here. Those Chapter 14 concerns remain unimplemented.

## Evidence and limitations

**OBSERVED LAB RESULT:** invalid configuration prevents readiness; liveness can differ from
readiness; outages degrade graph-dependent capabilities; logs preserve correlation while removing
modeled secrets; metrics derive from existing evidence; alerts retain evidence; recurring work can
be scheduled without absorbing business logic; local overlap can be prevented; and runbooks encode
safe actions.

**MODELED ASSUMPTION:** deployment configuration, credential availability, dependency behavior,
capability dependencies, alert thresholds, schedule intervals, ownership, and outage semantics.

There is no cloud, network probe, HTTP health endpoint, secrets manager, daemon, distributed lock,
external monitor, or real credential. This chapter does not prove production reliability or a
deployed service. Chapter 14 is intentionally not implemented.
