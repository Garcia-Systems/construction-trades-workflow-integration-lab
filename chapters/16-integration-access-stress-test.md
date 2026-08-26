# Chapter 16 — Integration Access Stress Test

API access is a business variable because it bounds achievable scope, recovery, rollout confidence,
and ongoing support even when the business handoff is unchanged. All vendors and capabilities here
are synthetic **MODELED ASSUMPTIONS**, not claims about real products.

```text
VALUABLE BUSINESS HANDOFF
          ↓
   INTERFACE QUALITY
          ↓
 ┌────────┼─────────┐
 ↓        ↓         ↓
CLEAN   DIFFICULT  CLOSED
 ↓        ↓         ↓
WRITE   CONSTRAIN  HUMAN / READ
AUTO      SCOPE       ONLY
          ↓
   DIFFERENT ECONOMICS
```

## Profiles and the safe-write boundary

The clean profile has documented, versioned reads and writes, a sandbox, stable identity/external
reference, strong acknowledgement, and destination lookup. The difficult profile combines limited
writes with partial documentation and acknowledgement, unstable identity, no lookup or sandbox,
and a drift-prone nightly export. The closed profile has export/read visibility but **no supported
critical job write**; the vendor UI remains authoritative.

Supported write permission is necessary but insufficient for consequential automation. Full
automation additionally requires stable business identity, deduplication or external-reference
semantics, deterministic acknowledgement, and lookup after an uncertain outcome. Without those,
blind replay can duplicate business consequences. A sandbox also matters: without one, safe
production-like validation decreases and rollout should use a dry run or human confirmation. This
is constraint evidence, not an invented incident probability.

## Scope redesign

The six unchanged handoffs—lead to estimate, accepted estimate to job, job to schedule, materials,
field status to office, and completion to invoice readiness—are evaluated for every profile. Clean
access selects narrow API writes. Difficult access constrains writes and uses a known-schema export
where appropriate. Closed job creation is `BLOCKED`; the implementation cannot bypass that fact.

Instead, a deterministic packet preserves correlation, source identity, validated fields, required
action, and evidence. A person creates/confirms the job in the native UI, after which a read-only
check can reconcile the destination ID. The packet performs no write and is intentionally not a
task manager. Read-only visibility and the native vendor workflow remain legitimate alternatives.

## CSV export, drift, and batch timing

BidForge's synthetic v1 export is exactly:

```text
estimate_id,status,customer_id,updated_at
```

The standard-library parser validates that ordered schema, schema version, row width, and non-empty
values while preserving `estimate_id` and source provenance. A changed v2-like export—
`estimate_number,approval_status,customer_ref,last_modified`—raises `SchemaDriftError`; there is no
fuzzy mapping or silent reinterpretation. Automation stops and support must inspect the export.
The nightly delay, versus near-immediate API availability, is a **MODELED ASSUMPTION**: export
integration can be technically feasible and operationally slower.

## Reliability, support, and reuse

Clean access exposes credentials, versions, outages, mappings, and exceptions. Difficult access adds
file delivery/timing, monitoring, drift, partial acknowledgement, unstable IDs, manual reconciliation,
and production-only testing. Closed access adds handoff ownership, process training, reconciliation
dependency, and expectation management. These are structural support obligations, not support-cost
calculations.

Capability evaluation, scope contracts, strict schema validation, packet/provenance, and the existing
workflow identities survive. CSV parsing and profile behavior are access-specific adapters/configuration.
Limited access is initially adapter-heavy; closed consequential writes change the architecture itself:
automatic write becomes human action plus reconciliation.

Easy APIs reduce uncertainty and recovery/testing burden but may coexist with a stronger native/partner
ecosystem. Poor APIs may leave greater workflow pain while making custom delivery less supportable.
Neither side automatically wins. Clean access strengthens the narrow technical opportunity; difficult
access weakens it; closed access limits it to bounded assistive/read-only value.

## Evidence and limitations

**OBSERVED LAB RESULT:** fixed inputs produce different feasibility and scopes; safe recovery gates full
automation; v1 CSV parses; drift stops rather than guesses; a validated packet performs no write; and
read-only/native redesign preserves some value. Support surface grows as modeled access deteriorates.

**MODELED ASSUMPTION:** all API permissions, authentication/documentation quality, identifiers,
acknowledgements, lookup, export behavior/timing, schema stability, sandbox availability, and native
alternatives. The lab does not contact vendors, execute external writes, measure production reliability,
or calculate hours, delivery price, support cost, payback, contribution, or an economic verdict.
Chapter 17 remains unimplemented.
