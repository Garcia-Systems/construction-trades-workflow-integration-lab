# Chapter 4 — Accepted Estimate to Job

This is the lab's first **consequential write**. A job can drive scheduling,
crews, materials, reporting, field work, and billing, so receiving a message is
not equivalent to being safe to write. The experiment asks whether one accepted
estimate can create or resolve to exactly one operational job.

```text
ESTIMATEWORKS
     ↓
ACCEPTED ESTIMATE
     ↓
VALIDATE + NORMALIZE
     ↓
BUSINESS IDEMPOTENCY KEY
     ↓
CHECK EXISTING JOB
     ↓
     ├── SAME JOB EXISTS
     │       ↓
     │  IDEMPOTENT REPLAY
     │
     ├── CONFLICT
     │       ↓
     │  HUMAN EXCEPTION
     │
     └── NO JOB
             ↓
        CREATE JOB
             ↓
       ACKNOWLEDGEMENT
             ↓
      AUTHORITATIVE JOB ID
```

## Authority and the discovery gate

EstimateWorks is authoritative for estimate identity, version, and acceptance.
CrewBoard is authoritative for job identity, existence, and operational state.
The integration owns validation, correlation, the handoff attempt, process-local
idempotency records, acknowledgement history, and exceptions—never the Job.

Chapter 1's baseline remains **BLOCKED** because `DISC-001` and `DISC-002` were
unresolved. Chapter 4 uses a separate resolved-discovery variant. Its **MODELED
ASSUMPTIONS** are that externally created CrewBoard jobs are permitted; a stable
external reference is accepted and deduplicated; lookup returns enough fields
to compare a job; creation returns an acknowledgement with the authoritative
job ID; write approval is known; and accepted EstimateWorks identity/version is
readable. These are fictional conditions, not discovered vendor facts.

## Validation and narrow transfer

The adapter requires estimate identity/version, `CUSTOMER_APPROVED`, an accepted
timestamp, customer identity, complete service location, and scope. The handoff
also requires confirmed destination write capability and a known consequential-
write approval boundary. `OPEN` is `NOT_ELIGIBLE`, while missing identity is a
controlled exception. No customer identity is guessed. The command transfers
only the customer reference, address, scope, source estimate identity/version,
provenance, correlation, and idempotency key; price is unnecessary for job creation.

## Transport identity is not business identity

`event-001` and `event-002` can deliver the same accepted business event. Their
transport identities differ, but both derive
`accepted-estimate:EW-EST-2001:v3`. This deterministic source identity/version
key survives process attempts; a random attempt ID would not. A changed version
is distinguishable. Once version 3 is known, version 2 is explicitly `STALE` and
cannot roll CrewBoard backward.

The simulator checks CrewBoard before creation. A compatible job at the exact
external reference yields `IDEMPOTENT_REPLAY` and its original job ID. A job
claiming the same estimate with incompatible version, address, customer, or
scope yields `STATE_CONFLICT`: there is no overwrite and no second job. Human
review is required.

## Sent is not acknowledged

The successful history distinguishes `JOB_CREATE_READY`, `JOB_CREATE_SENT`, and
`JOB_CREATE_ACKNOWLEDGED`. The acknowledgement carries CrewBoard's authoritative
job ID and retained provenance/correlation. This matters at the dangerous partial
failure boundary:

```text
CrewBoard may have created the job
              ↓
integration fails before recording acknowledgement
```

Blind creation after that uncertainty is unsafe. Chapter 4 can safely inspect
CrewBoard by external reference and repeat its idempotent operation. It does not
add a retry queue, durable registry, replay platform, or reconciliation engine.
Those failure concerns remain unresolved for later experiments.

## No exactly-once delivery claim

The lab does **not** demonstrate exactly-once message delivery. It observes that,
inside this modeled synthetic boundary, at-least-once/repeated processing can
produce one intended business effect when the destination supports idempotency
and sufficient lookup. The distinction is between one business effect and the
number of message deliveries.

## Observed implementation structure

- **SHARED CORE:** canonical source identity, provenance, integration events,
  and controlled exceptions.
- **SOURCE-SPECIFIC ADAPTER:** `EstimateWorksAdapter` normalization.
- **WORKFLOW-SPECIFIC LOGIC:** accepted eligibility, narrow job-command creation,
  and stale-version rules.
- **RELIABILITY:** deterministic business key, duplicate-event protection,
  destination lookup, and acknowledgement handling.
- **EXCEPTION HANDLING:** missing identity, stale state, and incompatible job state.
- **TESTING:** deterministic first delivery, replays, stale input, validation,
  non-eligibility, conflict, authority, provenance, and discovery scenarios.

These are implementation categories, not claimed labor hours.

## Evidence and limitations

**OBSERVED LAB RESULT:** inside the synthetic model, an accepted estimate makes a
narrow command; identical business identity makes an identical key; identical
and separately enveloped deliveries leave one CrewBoard job; stale data cannot
overwrite it; conflicts stop automation; missing customer identity stops the
write; and acknowledgement retains the authoritative job ID, provenance, and
correlation.

**MODELED ASSUMPTION:** all record formats, permissions, business rules, state
mapping, external-reference/idempotency behavior, lookup detail, acknowledgement
semantics, and fictional vendor capabilities. The simulator is synchronous and
in-memory. The integration registry is not durable, no real vendor was called,
and network ambiguity is not solved generally. Chapter 5 scheduling behavior is
not implemented.

Run `python -m trades_lab chapter4` to compare first delivery, exact replay, a
second envelope, missing identity, stale input, conflict, and nonaccepted input.
