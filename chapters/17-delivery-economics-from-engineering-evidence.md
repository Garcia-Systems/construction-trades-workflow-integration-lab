# Chapter 17 — Delivery Economics From Engineering Evidence

## Question and evidence discipline

What does the engineering evidence do to confidence in the original delivery economics? It constrains assumptions; it does not manufacture time sheets.

```text
ORIGINAL MODELED DELIVERY
          ↓
ENGINEERING EVIDENCE
          ↓
STRUCTURAL INTERPRETATION
          ↓
SENSITIVITY ASSUMPTIONS
          ↓
DELIVERY ECONOMICS RANGE

NOT: repository metrics → fake measured hours
```

Three labels are kept separate:

* **MODELED ASSUMPTION:** every original hour, 466 total hours, 52.8% reusable effort, the $50,000 implementation price, and $12,000 annual fee.
* **OBSERVED IMPLEMENTATION STRUCTURE:** adapters, mappings, workflow/customer rules, validators, reliability, exception handling, tests, runtime structures, reuse patterns, and access-driven alternatives.
* **SENSITIVITY ASSUMPTION:** every revised hour, revised labor-reuse percentage, and the configurable $100/hour hypothetical delivery-cost input. It is not a market rate.

Repository structure **≠** human effort measurement. Unit, adapter, file, test, line, or chapter counts are never multiplied into hours. Chapter 14's implementation-unit reuse ratio and a scenario's hypothetical reusable-labor percentage have different denominators and are never interchangeable.

## Original modeled delivery

| Category | MODELED ASSUMPTION |
|---|---:|
| Technical discovery | 24h |
| API validation | 36h |
| Adapters | 104h |
| Identity normalization | 34h |
| Orchestration | 58h |
| Reliability / error handling | 48h |
| Exception handling | 34h |
| Documentation | 22h |
| QA / testing | 54h |
| Deployment | 16h |
| Rework reserve | 36h |
| **Total** | **466h** |

These values are untouched, not observed. Rework reserve is especially not observable from a repository.

## Structural interpretation by category

| Category | Qualitative comparison | Engineering evidence |
|---|---|---|
| Discovery | POSSIBLY_UNDERSTATED | Ch. 1 authority and Ch. 16 access, permission, sandbox, native-alternative, and safe-write questions. |
| API/interface validation | HIGHLY_VARIABLE | Clean/difficult/closed profiles, lookup assumptions, no sandbox, CSV validation and drift. |
| Adapters | HIGHLY_VARIABLE | RiverLead, EstimateWorks, job/CrewBoard, SupplyDesk, FieldTrack, LedgerPro, BidForge, office/manual and export boundaries. |
| Identity | POSSIBLY_UNDERSTATED | Source references reuse, but customer, material, contextual, and accounting identities remain specialized. |
| Orchestration | HIGHLY_VARIABLE | Ch. 3–8 handoffs plus customer-specific approval, completion and billing aggregation. |
| Reliability | POSSIBLY_UNDERSTATED | Idempotency, acknowledgements, retry, uncertain outcomes, replay, reconciliation, conflict/stale checks and scheduler overlap. |
| Exceptions | POSSIBLY_UNDERSTATED | Routing, lifecycle, actions, ownership, aging, and replay approval. |
| Documentation | SUPPORTED_STRUCTURALLY | Boundaries, chapter explanations, runbooks and procedures; document count is not labor. |
| QA | POSSIBLY_UNDERSTATED | Scenarios, failures, regression, customer variation and access profiles. |
| Deployment | POSSIBLY_UNDERSTATED | Runtime config, secret boundary, readiness, health, metrics, alerts, schedules and runbooks. |
| Rework reserve | NOT_EVALUABLE | Only a modeled or sensitivity concept. |

Chapter 14 positively identifies reused correlation, provenance, idempotency, acknowledgement, exception, retry/replay, reconciliation and runtime concepts. Chapter 15 shows that bespoke approval, kits, weak identity, manual completion and billing aggregation remain at specialized edges. Chapter 16 shows interface quality can expand discovery/validation/testing or force export, human-assisted, or read-only redesign.

## Transparent delivery sensitivities

Every scenario carries an explicit value for all eleven categories in the machine-readable report; there are no hidden multipliers. At the hypothetical **SENSITIVITY ASSUMPTION** cost of $100/hour:

| Scenario | Hours | Reusable labor assumption | Cost | Contribution at $50,000 | Delivery verdict |
|---|---:|---:|---:|---:|---|
| Original baseline | 466 | 52.8% | $46,600 | $3,400 | THIN_DELIVERY |
| Standardized / reusable | 336 | 65% | $33,600 | $16,400 | HEALTHY_DELIVERY |
| Mixed customer | 500 | 48% | $50,000 | $0 | THIN_DELIVERY |
| Bespoke customer | 658 | 34% | $65,800 | -$15,800 | UNATTRACTIVE_DELIVERY |
| Difficult access | 650 | 38% | $65,000 | -$15,000 | SCOPE_REDESIGN_REQUIRED |
| Closed integration redesign | 330 | 42% | $33,000 | $17,000 | SCOPE_REDESIGN_REQUIRED |

The standardized case retains discovery, credentials, mappings, adapters, tests, exception rules and production setup: shared code does not make delivery nearly free. The mixed case illustrates thin contribution. Bespoke workflow/customer rules increase specialization. Difficult access can cost more while achieving reduced automation. Closed redesign costs less because its scope is read-only/human-assisted, but that is **not equal customer value**; customer-value economics must be revisited later.

Modeled labor cost is `explicit scenario hours × explicit sensitivity rate`. Modeled contribution is `$50,000 − modeled labor cost`; no other direct cost is silently invented. The modeled direct cost is also shown as the **modeled break-even implementation price under that sensitivity scenario**, not a recommended sales price.

## Balanced evidence

**Positive:** stable shared contracts and reuse of idempotency, correlation/provenance, exception handling, reliability/replay, reconciliation and production-runtime concepts; some variation stayed in configuration and edge modules.

**Negative:** shared architecture did not remove adapter work; mapping content and workflow rules remain customer-specific; access may eliminate consequential writes; reconciliation and production engineering extend visible feature scope; human exceptions and support onboarding remain obligations even with core reuse.

A technically successful integration can therefore fail economically when delivery, rework, access friction and customer-specific work approach or exceed implementation price. Reuse does not guarantee contribution.

## Limits and next learning

Actual customer discovery must establish authority, credentials, permissions, sandbox behavior, schemas, identifiers, mapping volume/quality, workflow exceptions, deployment constraints and acceptance criteria. Only delivery records can measure labor. This chapter issues a delivery-side sensitivity verdict only—**not a final commercial verdict**. Chapters 18–20 subsequently address support, alternatives, and the final verdict.
