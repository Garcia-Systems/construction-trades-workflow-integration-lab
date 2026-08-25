# Chapter 0 — The Hypothesis

## Status and question

**Evidence category: MODELED ASSUMPTION.** The economic and delivery baseline in
this chapter reconstructs a fictional cookbook hypothesis. It is not observed
engineering evidence and is not a benchmark.

The lab asks whether a narrow layer can reliably coordinate meaningful
transitions among existing systems without becoming a bespoke platform, and
whether that technical complexity preserves the economic opportunity. Evidence,
not the original verdict, is the target. A successful implementation alone does
not prove a good custom-software market.

## Fictional customer and workflow

James River Mechanical is a completely fictional regional residential and
light-commercial contractor: approximately 44 employees, seven field crews, one
office/operations team, dozens of active jobs, and fictional roles for an
owner/general manager, operations manager, office manager, estimator, field
supervisor, and accounting lead. Every person, system, workflow, financial
figure, dataset, vendor, and scenario is fictional or synthetic.

```text
LEAD
  ↓
ESTIMATE
  ↓
ACCEPTED ESTIMATE
  ↓
JOB
  ↓
SCHEDULE
  ↓
CREW
  ↓
MATERIALS
  ↓
FIELD COMPLETION
  ↓
INVOICE READY
  ↓
INVOICE
  ↓
PAYMENT / RECONCILIATION
```

Existing systems remain authoritative. The proposed layer orchestrates handoffs.
It will not replace or build a CRM, estimating platform, dispatcher,
field-service application, accounting system, ERP, payroll, purchasing software,
mobile workforce application, or general-purpose workflow engine.

```text
SYSTEM OF RECORD A
        ↓
approved event / export / API
        ↓
VALIDATION
        ↓
CUSTOM INTEGRATION LAYER
        ↓
NORMALIZED CUSTOMER / JOB / STATUS IDENTITY
        ↓
HANDOFF RULE
        ↓
SYSTEM OF RECORD B
        ↓
ACKNOWLEDGEMENT / EXCEPTION / HUMAN REVIEW
```

**ORCHESTRATE TRANSITIONS, DO NOT REPLACE SYSTEMS.**

## Original economic hypothesis

All entries in this section are **MODELED ASSUMPTIONS**:

| Input | Fictional modeled value |
|---|---:|
| Employees / field crews | 44 / 7 |
| Active jobs | dozens |
| Annual current-state burden | $130,584.22 |
| Annual recoverable value | $64,619.29 |
| Implementation price | $50,000.00 |
| Annual recurring fee | $12,000.00 |
| Implementation payback after recurring fee | approximately 11.4 months |
| Reusable core work | 52.8% |
| Delivery contribution | thin but positive |
| Support contribution | sustainable but thin |

Payback is calculated as `price / (recoverable value - recurring fee) × 12`.
The executable also derives price and recurring-fee percentages of annual
recoverable value rather than storing those results.

The fictional burden comprises duplicate entry, estimate-to-job reconciliation,
scheduling coordination, materials/purchasing coordination, field-to-office
reconciliation, completion-to-invoice administration, error correction/rework,
management reporting, and invoice-delay financing cost.

**Invoice principal is not software-created value.** Faster readiness may reduce
administration and financing/cash-conversion cost; it must never be represented
as creating the invoice revenue.

Original cookbook verdict: **PROMISING — VALIDATE IN DISCOVERY**.

## Original delivery hypothesis

| Modeled activity | Hours |
|---|---:|
| Technical discovery | 24 |
| API validation | 36 |
| Adapters | 104 |
| Identity normalization | 34 |
| Orchestration | 58 |
| Reliability / error handling | 48 |
| Exception handling | 34 |
| Documentation | 22 |
| QA / testing | 54 |
| Deployment | 16 |
| Rework reserve | 36 |
| **Total modeled engineering hours** | **466** |

Implementation will not be organized merely to validate that estimate. Future
repository evidence will instead be classified as **SHARED CORE**,
**SOURCE-SPECIFIC ADAPTER**, **WORKFLOW-SPECIFIC LOGIC**, **CUSTOMER-SPECIFIC
RULE**, **CONFIGURATION**, **VALIDATION**, **RELIABILITY**, **EXCEPTION HANDLING**,
**TESTING**, **DEPLOYMENT**, and **SUPPORT SURFACE**.

## Evidence vocabulary

### MODELED ASSUMPTION
A fictional economic, effort, pricing, or support number.

### OBSERVED LAB RESULT
Behavior actually demonstrated by the executable synthetic system.

### OBSERVED IMPLEMENTATION STRUCTURE
Repository evidence such as adapters, mappings, transitions, tests, exceptions, jobs, and reliability mechanisms.

It is not automatically human-hours evidence.

### SENSITIVITY ASSUMPTION
A hypothetical changed value used to test economics.

### FICTIONAL ALTERNATIVE ASSUMPTION
An unverified capability or price attributed to a hypothetical SaaS alternative.

Chapter 0 currently observes only that Python can represent the assumptions,
sum the delivery activities, and deterministically calculate economic ratios.
No operational integration behavior or actual effort has yet been observed.

## Claims under test and failure conditions

Later chapters must test whether narrow orchestration is reliable, reusable,
supportable, and economically justified. The opportunity may weaken or fail if:

- mature field-service SaaS already solves the problem;
- supported write access is unavailable;
- workflow variation is too high;
- customer-specific rules dominate;
- reliability engineering is too expensive;
- ongoing support consumes recurring revenue;
- configuration solves most of the gap;
- technical reuse exists but market reuse does not;
- the buyer or sales motion does not repeat; or
- narrow automation cannot justify its delivery cost.

Those claims remain unknown. Chapter 0 supplies a falsifiable baseline, not a
verdict, and deliberately implements no Chapter 1 integration machinery.

