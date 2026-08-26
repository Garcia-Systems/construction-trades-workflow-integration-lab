# Chapter 18 — Support Economics

## The recurring question

Chapter 17 tested initial delivery economics. This chapter deliberately asks a different,
post-go-live question: **what does the deployed integration cost to support?** The original
annual recurring fee remains exactly **$12,000**, and the original support description remains
“sustainable but thin.” Both are **MODELED ASSUMPTION**, not observed market pricing.

```text
DEPLOYED INTEGRATION
        ↓
ONGOING OBLIGATIONS
        ↓
 ┌──────┼────────┬────────┬────────┐
 ↓      ↓        ↓        ↓        ↓
ACCESS MAPPINGS FAILURES RECONCILE EXCEPTIONS
        ↓
   SUPPORT EFFORT
        ↓
RECURRING FEE
   - SUPPORT COST
        ↓
RECURRING CONTRIBUTION
```

Recurring revenue is not pure contribution. Delivery hours, implementation price, and delivery
contribution remain in Chapter 17 and are not charged again here.

## Observed support surface

The inventory is **OBSERVED IMPLEMENTATION STRUCTURE**, not measured demand:

| Obligation | Repository evidence |
|---|---|
| Credential/access maintenance | Chapter 13 credentials and access-repair runbook; Chapter 16 access profiles |
| Vendor/interface change | Chapter 16 strict CSV drift detection and varying interface capabilities |
| Mapping maintenance | Chapter 6 material mappings and Chapter 8 accounting mappings |
| Failed handoffs | Chapter 9 exhaustion, uncertainty, lookup, and replay |
| Reconciliation | Chapter 10 recurring comparisons and mismatches |
| Exception workflow | Chapter 11 assignment, review, aging, resolution, and replay approval |
| Customer rules | Chapter 15 approvals, kits, manual completion, aggregation, and weak identity |
| Observability | Chapter 13 health, metrics, alerts, schedules, and controls |
| Configuration/deployment | Chapter 13 capabilities, dependencies, environments, and intervals |
| Runbooks/ownership | Chapter 13 recovery runbooks and Chapter 11 owner routing—not a call center |

The structure proves obligations exist; it cannot say how often they happen or how long they take.

## Event and labor sensitivity

Every annual event count, average hours per event, total annual hour value, hypothetical **$100/hour**
internal labor cost, zero direct cost, contribution, and break-even result is a **SENSITIVITY
ASSUMPTION**. The rate is configurable and is not a market wage. Direct non-labor recurring cost is
zero only to avoid inventing infrastructure; callers can explicitly replace it.

| Scenario | Explicit hours | Labor cost | Direct cost | Contribution | Break-even fee | Predictability / verdict |
|---|---:|---:|---:|---:|---:|---|
| A — standardized/quiet | 40 | $4,000 | $0 | $8,000 | $4,000 | PREDICTABLE / HEALTHY_SUPPORT |
| B — mixed | 100 | $10,000 | $0 | $2,000 | $10,000 | VARIABLE / THIN_SUPPORT |
| C — bespoke/high support | 150 | $15,000 | $0 | -$3,000 | $15,000 | HIGH_VARIANCE / INSUFFICIENT_SUPPORT |

These are inspectable sensitivities, not forecasts. Scenario A still contains nonzero mapping,
reconciliation, observability, and configuration work. Scenario B adds access incidents, exhausted
retries, and exceptions. Scenario C adds no-sandbox access repair, export/mapping churn, weak-identity
reconciliation, manual review, and bespoke-rule maintenance learned from Chapters 15–16.

The report also computes the largest category share of assumed hours. That concentration describes
only each hypothetical input set; it is not a measured customer frequency. Predictability is
deterministic: routine categories are `PREDICTABLE`; access, failures, or exception review make it
`VARIABLE`; vendor change or customer rules make it `HIGH_VARIANCE`.

## Included support versus change requests

This synthetic policy makes the commercial boundary inspectable:

* **INCLUDED_SUPPORT:** expired credential repair, routine material mapping, exhausted-retry
  investigation/replay, a minor one-field repair, and reconciliation investigation.
* **CHANGE_REQUEST:** a new approval workflow or new source system.
* **COMMERCIAL_REVIEW:** an incompatible replacement API, because it may be an extraordinary event,
  change request, or reimplementation risk. Major redesign is not silently absorbed into support.

## Evidence for and against recurring economics

Positive evidence includes a shared reliability framework, deterministic reconciliation, reusable
exception workflow, common logging/health/alert/runbook structure, standardized configuration, clean
APIs, and stable mappings. Negative evidence includes unstable IDs, mapping churn, bespoke approvals,
schema drift, absent sandboxes, uncertain-write recovery, manual completion, closed/human-assisted
interfaces, and high exception volume.

A reusable core can improve support scaling **only if customer-specific obligations remain bounded**.
Retry machinery may be shared, while every customer's credentials, mapping churn, and workflow rules
still scale with customer count.

## Limitations

No repository unit, adapter, file, test, or chapter is converted into hours. No measured incident
frequency, support demand, labor rate, hosted cost, or market price exists. Scope enforcement still
requires an actual contract. The scenarios do not produce a final opportunity or build-versus-buy
verdict. Chapter 19 subsequently screens alternatives, and Chapter 20 synthesizes the verdict.
