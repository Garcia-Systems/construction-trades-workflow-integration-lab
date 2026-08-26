# Chapter 8 — Completion to Invoice Readiness

> All gates, identities, vendor capabilities, metadata, approval policies, evidence
> semantics, and exception policies are **MODELED ASSUMPTIONS**.

Completion is an operational observation; invoice readiness is a validated business
condition. FieldTrack owns modeled completion, the operational job system owns job
state, SupplyDesk owns material status, and LedgerPro owns accounting customer
identity, invoices, posting, payment, and financial state. The integration says only
that modeled prerequisites *appear satisfied*. It never creates or models an invoice.

```text
FIELD COMPLETED
      ↓
READINESS CHECKS
      ↓
      ├── JOB STATE
      ├── MATERIALS
      ├── COMPLETION EVIDENCE
      ├── ACCOUNTING IDENTITY
      ├── BILLING METADATA
      ├── APPROVAL
      └── BLOCKING EXCEPTIONS
                ↓
         ┌──────┴──────┐
         ↓             ↓
      BLOCKED        READY
                       ↓
             LEDGERPRO WORK ITEM
                       ↓
               ACCOUNTING OWNS
                  THE INVOICE
```

## Explainable gates

The evaluator reports every gate as `PASS`, `FAIL`, `BLOCKED`, or `N/A` rather
than hiding policy behind a boolean. `COMPLETED` is required both from FieldTrack
and the authoritative job. The fixture narrowly requires resolved material
blockers, an acknowledged completion code, an approved LedgerPro customer map,
job reference, completion date, summary and billing category. Missing values are
reported and never invented. Commercial change orders require customer approval;
residential standard work does not. That distinction is customer-specific.

An unresolved exception blocks only when its explicit
`blocks_invoice_readiness` policy is true. Thus an operational note may coexist
with readiness, while a material dispute blocks it. This is deliberately not a
rules engine or document-management system.

## Consequential handoff and changed facts

The narrow `InvoiceReadyCommand` carries job, mapped customer, completion date,
reference, summary, correlation, and deterministic idempotency key. It contains
no invoice number, balance, posting, or payment state. LedgerPro acknowledges a
synthetic **billing work item**, not an invoice.

The fingerprint includes only billing-relevant job/completion versions and state,
completion date/evidence version, approved mapping, metadata version, approval,
job type, and billing-blocking exceptions. Exact evaluation replay returns the
same work item. Changed approval produces a different fingerprint. An observation
older than newer authoritative job state is blocked synchronously. This is not
Chapter 9 retry, recovery, reconciliation, a replay tool, or a delivery guarantee.

## Economic discipline

```text
COMPLETION
      ↓
manual reconciliation / missing prerequisites / delay
      ↓
INVOICE READINESS

May reduce: administrative touches, prerequisite chasing, avoidable readiness delay
Invoice principal: NOT INCLUDED
```

The possible mechanism is less handling, fewer missed prerequisites, and a shorter
avoidable cash-conversion delay—not the underlying customer revenue. No measured
savings or Chapter 17 economics are asserted.

## Reuse and implementation structure

Actually reused are canonical states, correlation/events, bounded mappings,
acknowledgement and exception shapes, and deterministic idempotency patterns.
Billing gates, completion evidence, exception impact, and approval policy are
workflow-specific. LedgerPro mapping/boundary is source-specific. Approval job
types, required fields, mappings, and exception policy are customer configuration.

The inventory classifies these as **SHARED CORE**, **SOURCE-SPECIFIC ADAPTER**,
**WORKFLOW-SPECIFIC LOGIC**, **CUSTOMER-SPECIFIC RULE**, **CONFIGURATION**,
**VALIDATION**, **RELIABILITY**, **EXCEPTION HANDLING**, **TESTING**, and
**SUPPORT SURFACE**. Support includes mapping and metadata changes, approval rules,
LedgerPro interface changes, exception types, and completion-evidence semantics.

## Evidence and limitations

**OBSERVED LAB RESULTS:** deterministic fixtures show partial completion cannot
pass; completed jobs can remain blocked; missing identity is not guessed; blocking
and non-blocking exceptions differ; approval change differs from replay; and exact
ready replay does not duplicate a billing work item. A ready notification exists
without invoice creation.

The policies and vendor boundary remain **MODELED ASSUMPTIONS**. Execution is
process-local and synchronous. There is no external API, durable store, generic
workflow engine, retry queue, recovery, reconciliation, invoice, posting, or
payment behavior. Those limitations must not be mistaken for production evidence.
