# Chapter 3 — Lead to Estimate

This is the lab's first operational handoff. It precedes the more consequential
accepted-estimate-to-job transition because it stops at a validated destination
command: it neither creates an estimate nor changes an external system. The lesson
is **validate, normalize, preserve provenance, detect duplicates, and either
produce a safe command or stop explicitly**—not “copy a record.”

```text
RIVERLEAD CRM
      ↓
RAW LEAD
      ↓
VALIDATE ELIGIBILITY + REQUIRED DATA
      ↓
NORMALIZE
      ↓
IDENTITY / REPLAY CHECK
      ↓
      ├── EXCEPTION / SKIP
      │
      └── ESTIMATE INTAKE COMMAND
                 ↓
          ESTIMATEWORKS BOUNDARY
```

## Authority and minimum transfer

RiverLead CRM remains authoritative for the fictional source lead. EstimateWorks
would remain authoritative for an estimate it eventually creates. The integration
owns only validation, normalization, correlation, provenance, replay/ambiguity
decisions, commands, events, and exceptions. It is not a customer or lead master.

The fictional intake requirement is bounded: source and canonical lead identity,
source customer reference, customer name, contact, service address, scope,
correlation, and source observation version. CRM ownership and marketing metadata
in the fixture are intentionally not transferred.

## Validation, eligibility, and normalization

`RiverLeadAdapter` directly maps a local synthetic record without a generic mapping
framework. It validates identity, name, contact, location, scope, and timestamp,
then creates the Chapter 2 canonical `Lead`, `SourceReference`, and `Provenance`.
`QUALIFIED` and `ESTIMATE_REQUESTED` are eligible modeled states. `NEW`,
`CLOSED_LOST`, `SPAM`, and `DUPLICATE` produce `SKIPPED_NOT_ELIGIBLE`, not an
exception. Unknown state is never guessed. Malformation, missing data, and unknown
state create a validation `ExceptionRecord` before the destination boundary.

Successful output is one immutable `EstimateIntakeCommand`. Deterministic events
make execution inspectable without implying an event bus:
`LEAD_OBSERVED → LEAD_NORMALIZED → ESTIMATE_INTAKE_READY`. Failed validation emits
`LEAD_OBSERVED → LEAD_VALIDATION_FAILED`. Correlation connects canonical
provenance, events, result, command, and exception as applicable.

## Replay and identity limitation

The process-local set detects only exact replay of source lead ID plus observed
version. It is intentionally not durable idempotency. A narrow contact-key check
signals ambiguity when a different source lead ID has the same email/phone
evidence; it stops with an identity exception rather than merging or commanding.

**Chapter 3 does not solve general customer identity reconciliation.** Matching
contact data does not prove that two records represent the same human or business,
and nonmatching data does not prove that they differ. Replay across restarts,
concurrency, production identity quality, vendor semantics, network behavior, and
external writes remain untested.

## Observed implementation structure

| Classification | Chapter 3 evidence |
|---|---|
| **SHARED CORE** | Canonical identity, provenance, events, exceptions |
| **SOURCE-SPECIFIC ADAPTER** | `RiverLeadAdapter` normalization |
| **WORKFLOW-SPECIFIC LOGIC** | Lead eligibility and EstimateWorks intake requirements |

No customer-specific rule is claimed. This classification is repository evidence,
not an estimate of human hours.

## Evidence discipline

**OBSERVED LAB RESULT:** Synthetic valid input deterministically produces one
bounded command; invalid input stops before the boundary; exact replay produces no
second command; ineligible input is skipped; provenance and correlation survive;
and narrow ambiguity prevents automatic merging.

**MODELED ASSUMPTION:** RiverLead's shape, statuses, version semantics and
capabilities; EstimateWorks intake needs; eligibility; contact usability; and
synthetic identity behavior are fictional. This does not demonstrate that a real
CRM/estimating integration is feasible.

Run `python -m trades_lab chapter3` for all six scenarios. Chapter 4's job creation,
consequential-write idempotency, persistence, retries, and conflict handling are
explicitly not implemented.
