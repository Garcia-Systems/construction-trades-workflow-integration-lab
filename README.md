# Construction / Trades Workflow Integration Lab

An executable textbook for testing—not defending—a custom-software opportunity
hypothesis. It asks whether a narrow integration layer can reliably coordinate
meaningful transitions among existing CRM, estimating, scheduling, field,
purchasing, and accounting systems **without becoming a bespoke workflow
platform**, and whether the resulting complexity still supports the economics.
Evidence may strengthen, weaken, or reject the hypothesis.

> **Fictional-customer notice:** James River Mechanical, its approximately 44
> employees, seven field crews, people, systems, workflows, figures, vendors,
> datasets, and scenarios are entirely fictional or synthetic. No value is a
> real-world benchmark.

## Architectural boundary

Existing business systems remain authoritative. The lab does **not** build a
CRM, estimating platform, dispatcher, field-service application, accounting
system, ERP, payroll, purchasing software, mobile workforce application, or
general-purpose workflow engine.

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

Chapter 2 introduces a compact canonical model at that translation boundary:
immutable identity and provenance, bounded state vocabularies, source-state
mappings, explicit transition eligibility, and event/exception contracts. It
describes source observations; source systems still own business state.
Chapter 3 adds the first source-specific adapter, `RiverLeadAdapter`, and first
executable cross-system handoff boundary. It produces a validated EstimateWorks
intake command, not an external estimate write.
Chapter 4 adds a bounded consequential-write experiment: a stable accepted-estimate
business key, CrewBoard lookup/idempotency, explicit conflict handling, and an
acknowledgement carrying CrewBoard's authoritative job ID.
Chapter 5 transfers validated job requirements into an acknowledged CrewBoard
schedule request. A request may remain `UNASSIGNED`: CrewBoard or a dispatcher—not
the integration—owns assignment.
Chapter 6 adds exact material-identity mapping, explicit unit normalization, partial
readiness, and an acknowledged SupplyDesk material-request boundary. It does not
purchase, track inventory, or select substitutes.
Chapter 7 adds a source-specific FieldTrack adapter and bounded office-facing field-status
normalization, with workflow-specific progression, replay, stale-sequence, blocked, partial,
and completion handling. Completion is not converted into invoice readiness.

## Evidence vocabulary

- **MODELED ASSUMPTION** — A fictional economic, effort, pricing, support, system-capability, permission, or vendor-behavior claim.
- **OBSERVED LAB RESULT** — Behavior actually demonstrated by the executable synthetic system.
- **OBSERVED IMPLEMENTATION STRUCTURE** — Repository evidence such as adapters, mappings, transitions, tests, exceptions, jobs, and reliability mechanisms. It is not automatically human-hours evidence.
- **SENSITIVITY ASSUMPTION** — A hypothetical changed value used to test economics.
- **FICTIONAL ALTERNATIVE ASSUMPTION** — An unverified capability or price attributed to a hypothetical SaaS alternative.

The enum and definitions in `trades_lab.evidence` make these labels reusable.

## Install and run

Python 3.12 or newer is required. The model has no runtime dependency, network,
database, or web framework.

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[test]'
pytest
python -m trades_lab chapter0
python -m trades_lab chapter1
python -m trades_lab chapter2
python -m trades_lab chapter3
python -m trades_lab chapter4
python -m trades_lab chapter5
python -m trades_lab chapter6
python -m trades_lab chapter7
```

The Chapter 0 CLI proves that its baseline is represented consistently and derives
ratios and payback deterministically. The Chapter 1 discovery briefing validates
authority, exposes modeled access risks and native alternatives, and gates future
handoffs. The Chapter 2 CLI displays deterministic state normalization, retained
source identity, and allowed and rejected transitions. None of the commands proves
fictional values or vendor capabilities. Chapter 3 compactly runs valid, replay,
ineligible, missing-data, unknown-state, and ambiguous-identity scenarios.
Chapter 4 compares first creation, two forms of replay, stale input, and conflicting
authoritative destination state.
Chapter 5 compares an initial request, exact replay, changed context, assignment
conflict, cancellation, and stale pre-cancellation input without choosing a crew.
Chapter 6 contrasts direct and converted mappings with unknown, ambiguous,
unsupported-unit and substitution stops, then demonstrates partial job readiness.
Chapter 7 contrasts blocked, partial-completion, and completion observations, exact replay
versus repeated business state, stale sequences, and mapping/identity exceptions.

## Chapter index and study path

- **Chapter 0 — The Hypothesis:** implemented ([read it](chapters/00-the-hypothesis.md)).
- **Chapter 1 — Discovery Before Workflow Design:** implemented ([read it](chapters/01-discovery-before-workflow-design.md)). Run `python -m trades_lab chapter1` to study the discovery briefing and blocked handoffs.
- **Chapter 2 — Define the Canonical Workflow Model:** implemented ([read it](chapters/02-canonical-workflow-model.md)). Run `python -m trades_lab chapter2` to inspect the canonical snapshot.
- **Chapter 3 — Lead to Estimate:** implemented ([read it](chapters/03-lead-to-estimate.md)). Run `python -m trades_lab chapter3` to compare successful and explicitly stopped handoffs.
- **Chapter 4 — Accepted Estimate to Job:** implemented ([read it](chapters/04-accepted-estimate-to-job.md)). Run `python -m trades_lab chapter4` and compare first delivery, duplicate delivery, and conflict.
- **Chapter 5 — Job to Schedule:** implemented ([read it](chapters/05-job-to-schedule.md)). Run `python -m trades_lab chapter5` to contrast request acknowledgement, assignment, replay, and changed context.
- **Chapter 6 — Materials and Purchasing Handoff:** implemented ([read it](chapters/06-materials-and-purchasing-handoff.md)). Run `python -m trades_lab chapter6` to compare direct mapping, unknown identity, conversion, and partial readiness.
- **Chapter 7 — Field Status to Office:** implemented ([read it](chapters/07-field-status-to-office.md)). Run `python -m trades_lab chapter7` to study blocked, partial, complete, replay, repeated-state, and stale-event scenarios.
- **Chapter 8:** planned; invoice readiness is not implemented.
- **Chapters 9–20:** planned; not implemented. Later work will introduce behavior progressively without assuming a favorable outcome.

Suggested study path: read Chapter 0 and run its CLI, then read Chapter 1 and
run the discovery briefing. Inspect why readiness changes before drawing a
workflow. Then read Chapter 2, inspect its source-state mappings, and run its CLI
to compare allowed and rejected transitions. Executable validation is an
**OBSERVED LAB RESULT**, while source capabilities, mappings, and workflow
semantics remain synthetic **MODELED ASSUMPTIONS**.
Then read Chapter 3 and run its successful and failed lead scenarios. The bounded
command, exceptions, provenance, correlation, and process-local replay behavior
are the lab's first executable handoff evidence—not proof of real vendor
feasibility or general identity reconciliation.
Then read Chapter 4 and contrast transport delivery IDs with the stable business
key. CrewBoard's external-reference, lookup, permission, and acknowledgement
capabilities are **MODELED ASSUMPTIONS**. One synthetic job surviving first
delivery, replay, stale input, and conflict is an **OBSERVED LAB RESULT** inside
that model—not an exactly-once delivery claim or evidence about a real vendor.
Then run Chapter 5 and compare request acknowledgement (`UNASSIGNED`) with an
authoritative assignment. Stable business-key and acknowledgement patterns, shared
provenance/events/exceptions, and Chapter 4's idempotency status reused cleanly.
Eligibility, context fingerprints, cancellation, and assignment-conflict rules stayed
workflow/destination-specific. That observed implementation structure makes reuse
more testable but does not validate the original reusable-core percentage.
Then run Chapter 6. Shared provenance, correlation, exception, idempotency, command,
and acknowledgement shapes repeat, while material IDs, units, conversion factors,
substitution rules, and the SupplyDesk boundary remain specialized. The reusable
mapping mechanism is separately identifiable from customer-specific mapping content;
retired products, new codes, and semantic changes are an explicit support surface.
This mixed evidence strengthens narrow technical-mechanism reuse while weakening any
assumption that mapping content itself will transfer between customers.
Then run Chapter 7. Shared identity, provenance, correlation, event, exception, and
duplicate-detection patterns recur; the FieldTrack adapter/mapping and sequence semantics
are source-specific, while progression and blocked/completion treatment are workflow-specific.
Job/crew maps and the relevant status subset are configuration. The executable evidence
shows `COMPLETED` only as a field observation: no invoice-readiness decision exists.

The original verdict, **PROMISING — VALIDATE IN DISCOVERY**, is a modeled starting
hypothesis—not a conclusion. Even a technically successful implementation does
not automatically demonstrate a repeatable or attractive custom-software market.
