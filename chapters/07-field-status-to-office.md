# Chapter 7 — Field Status to Office

## Boundary and authority

This chapter asks whether a bounded office-facing workflow can consume synthetic field signals without becoming a field-service or billing system. **FieldTrack remains authoritative for what its modeled crews reported in the field.** The operational job system remains authoritative for the job record. The integration owns only its observation, correlation, validation, event history, exception, and handoff acknowledgement.

```text
FIELDTRACK EVENT
      ↓
SOURCE IDENTITY + STATUS
      ↓
VALIDATION
      ↓
STATUS NORMALIZATION
      ↓
SEQUENCE / REPLAY CHECK
      ↓
      ├── DUPLICATE / STALE / EXCEPTION
      │
      └── OFFICE STATUS UPDATE
                ↓
        OPERATIONAL VISIBILITY

COMPLETED
    ≠
INVOICE READY
```

## Narrow normalization

The canonical vocabulary is deliberately only `DISPATCHED`, `ARRIVED`, `IN_PROGRESS`, `BLOCKED`, `PARTIALLY_COMPLETE`, and `COMPLETED`.

| FieldTrack (modeled) | Canonical |
|---|---|
| `EN_ROUTE` | `DISPATCHED` |
| `ONSITE` | `ARRIVED` |
| `WORKING` | `IN_PROGRESS` |
| `HOLD` | `BLOCKED` |
| `PARTIAL` | `PARTIALLY_COMPLETE` |
| `DONE` | `COMPLETED` |

`BREAK_STARTED`, `BREAK_ENDED`, and `PHOTO_UPLOADED` are modeled as `IGNORED_NOT_RELEVANT`; they do not enlarge the canonical vocabulary. Any other unknown status creates a mapping exception rather than a guess. A real source could contain many useful internal states—such as customer-not-home—but downstream need, not source abundance, determines this model.

## Identity, replay, sequence, and progression

Fixture configuration maps FieldTrack job IDs to authoritative job IDs and crew IDs to CrewBoard-style crew references. Descriptions are never matched. This implementation stops both unresolved job and crew identity before an office update.

An exact replay has the same source event ID and produces `DUPLICATE` with no second effect. A later event ID reporting the same `WORKING` business state is a distinct observation and may be `APPLIED`. A per-job source sequence rejects a value less than or equal to the last applied sequence as `STALE`, retaining the current state. Events without a sequence use only modeled progression rules; this lab does not invent event-time reconciliation.

Progression permits abbreviated paths such as `ARRIVED → COMPLETED`, resume paths `BLOCKED → IN_PROGRESS` and `PARTIALLY_COMPLETE → IN_PROGRESS`, and repeated observations. Obvious regressions such as `COMPLETED → ARRIVED` become state-conflict exceptions. This is a small workflow guard, not a replica of FieldTrack.

## Blocked, partial, and completed

A blocked update carries only one controlled reason: `MATERIAL_MISSING`, `CUSTOMER_UNAVAILABLE`, `SITE_ACCESS`, `ADDITIONAL_APPROVAL`, or `UNKNOWN`. It also emits office-attention history; it does not interpret the incident.

`PARTIALLY_COMPLETE` remains a first-class observation, not completion. `DONE` maps only to `COMPLETED`, an observation of field execution. It does not create an invoice, authorize billing, declare financial completion, or decide invoice readiness:

```text
PARTIALLY_COMPLETE ≠ COMPLETED ≠ INVOICE_READY
```

Invoice-readiness validation belongs to Chapter 8 and is intentionally absent.

## Implementation structure and reuse inspection

| Classification | Observed repository structure |
|---|---|
| SHARED CORE | Existing provenance, source references, correlation, integration events, and exceptions |
| SOURCE-SPECIFIC ADAPTER | `FieldTrackAdapter`, FieldTrack status subset/mapping, fixture shape |
| WORKFLOW-SPECIFIC LOGIC | progression, stale handling, blocked propagation, completion semantics |
| CUSTOMER-SPECIFIC RULE | downstream-relevant status subset |
| CONFIGURATION | explicit job and crew maps |
| VALIDATION | mapping, identity, progression checks |
| RELIABILITY | exact source-event replay and per-job sequence tracking |
| EXCEPTION HANDLING | controlled mapping, identity, and state-conflict exceptions |
| TESTING | deterministic scenario fixtures and behavior tests |
| SUPPORT SURFACE | status additions, sequence changes, mapping failures, reasons, delivery behavior |

The shapes of correlation, provenance, events, exceptions, and process-local duplicate detection genuinely reuse earlier ideas. FieldTrack vocabulary and sequence semantics do not: they are source-specific. Progression, stale treatment, blocked context, and completion meaning are workflow-specific. Identity maps and relevant-status choices remain configuration/customer-specific. This structure does not validate an estimated reuse percentage.

## Evidence

### MODELED ASSUMPTION

FieldTrack record/state vocabulary, sequence behavior, field semantics, blocked reasons, job and crew mappings, the office boundary, relevant-status subset, acknowledgement behavior, and all vendor capabilities are synthetic assumptions. Nothing here claims compatibility with a real vendor.

### OBSERVED LAB RESULT

Within those fixtures, mappings are deterministic; unknown states and identities stop automation; exact replay differs from a repeated business state; stale sequence events do not roll state backward; blocked reasons survive; partial and complete remain distinct; provenance and correlation reach the office update; and completion produces no invoice-readiness decision.

## Limitations and support surface

Storage is process-local, acknowledgement is simulated, and there are no network calls, persistence, concurrency controls, retries, dashboards, mobile application, or event platform. Source status additions, changed sequence semantics, job/crew mapping churn, blocked-reason changes, and webhook delivery changes require support review. No support automation is implemented. Chapter 8, billing gates, invoice generation, accounting writes, payments, and reconciliation are not implemented.
