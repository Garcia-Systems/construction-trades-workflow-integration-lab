# Construction / Trades Workflow Integration Lab

An executable textbook for testing—not defending—a custom-software opportunity
hypothesis. It asks whether a narrow integration layer can reliably coordinate
meaningful transitions among existing CRM, estimating, scheduling, field,
purchasing, and accounting systems **without becoming a bespoke workflow
platform**, and whether the resulting complexity still supports the economics.
Evidence may strengthen, weaken, or reject the hypothesis.

> **Fictional-customer notice:** James River Mechanical, its approximately 44
> employees, seven field crews, people, systems, workflows, figures, vendors,
> datasets, and scenarios are entirely fictional or synthetic. Tidewater Specialty
> Services and its deliberately awkward Chapter 15 systems and rules are likewise
> fictional and synthetic. No value is a real-world benchmark.

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
Chapter 8 adds explainable invoice-readiness validation and an idempotent LedgerPro
billing-work-item handoff. LedgerPro remains authoritative; no invoice creation exists.
Chapter 9 adds deterministic fault scripts, explicit failure categories, bounded retry, replay,
and targeted uncertain-outcome lookup. It is not a production messaging platform.
Chapter 10 adds read-oriented reconciliation across authoritative snapshots, logical delivery
history, and unresolved exceptions. It reports inconsistencies and performs no repair.
Chapter 11 adds deterministic ownership, a bounded review lifecycle and actions, immutable audit
history, active-condition deduplication, aging, and explicit replay approval. Resolution never
makes the integration authoritative for source business state.
Chapter 12 adds a read-only operational-briefing layer over handoff, delivery, reconciliation,
and exception evidence. It highlights current bottlenecks and ownership without a dashboard or
new system of record.
Chapter 13 wraps those application layers in a deterministic production-runtime simulation:
configuration and credential references, startup/health validation, capability-aware degradation,
redacted logs, bounded metrics and alerts, scheduled run records, and recovery runbooks. It is not
a real deployment and does not rewrite the earlier workflows.
Chapter 14 inventories the implementation that actually emerged. Its curated units, chapter-use
matrix, classifications, evidence levels, reuse scopes, change simulations, and support tags test
structural reuse without treating repository counts as labor. It is preserved as additional implementation evidence.
Chapter 15 returns to the original roadmap with a bespoke-customer stress test. Tidewater rules remain
at the edge with no shared-core modification, but new adapters, mappings, workflow layers, validation,
exceptions, and support obligations complicate the repeatability hypothesis.
Chapter 16 holds the business handoffs constant while varying synthetic interface access. Clean,
difficult, and closed profiles drive API-write, export-assisted, human-assisted, read-only, or native
scope redesign; unsupported consequential writes are never simulated.
Chapter 17 maps that accumulated implementation structure back to the original delivery categories,
then uses explicit standardized, mixed, bespoke, difficult-access, and closed-redesign sensitivities.
Repository metrics remain structural evidence, never measured labor.
Chapter 18 keeps recurring support separate from initial delivery. It inventories access, vendor,
mapping, failure, reconciliation, exception, customer-rule, observability, configuration, and runbook
obligations, then tests the modeled $12,000 fee using explicit event/hour/cost sensitivities and an
included-support versus change-request boundary. It issues no final market verdict.

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
python -m trades_lab chapter8
python -m trades_lab chapter9
python -m trades_lab chapter10
python -m trades_lab chapter11
python -m trades_lab chapter12
python -m trades_lab chapter13
python -m trades_lab chapter14
python -m trades_lab chapter15
python -m trades_lab chapter16
python -m trades_lab chapter17
python -m trades_lab chapter18
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
Chapter 8 contrasts fully ready, partial completion, missing accounting identity,
material/metadata blockers, exact replay, and a customer-approval change.
Chapter 9 contrasts temporary outage, timeout-before-write, acknowledgement loss,
no-lookup uncertainty, permanent/conflict/authentication stops, and retry exhaustion.
Chapter 10 contrasts a clean workflow with missing, conflicting, exhausted, unresolved,
and orphaned state; successful execution history is distinct from current consistency.
Chapter 11 contrasts identity, material/accounting mapping, state conflict, access repair,
exhausted delivery, finding dismissal, invalid action, deduplication, and aging scenarios.
Chapter 12 contrasts healthy and degraded current snapshots, traceable attention items, and
deterministic completion-to-readiness timing.
Chapter 13 contrasts healthy startup, missing credentials, partial SupplyDesk/LedgerPro outages,
uncertain-write and overdue-exception alerts, scheduled reconciliation and overlap prevention,
secret redaction, and runbook lookup.
Chapter 14 prints the machine-readable inventory summaries, reuse matrix, negative evidence,
support surface, and bounded `MIXED` structural-confidence verdict. Its implementation-unit ratio
has a different denominator from Chapter 0's modeled reusable-effort percentage.
Chapter 15 runs the deliberately unusual Tidewater scenarios: signed versus verbal acceptance,
early jobs, approval-gated scheduling, partial kit expansion, paper provenance, qualified identity,
billing-project readiness, and context-sensitive `DONE` semantics.
Chapter 16 compares the same six handoffs under clean, difficult, and closed access, including safe-write
recovery, nightly CSV ingestion, strict schema-drift failure, no-sandbox constraints, and a validated
human packet that performs no destination write.
Chapter 17 preserves the original 466 hours, 52.8% reusable effort, and commercial assumptions as
**MODELED ASSUMPTION**; interprets repository components as **OBSERVED IMPLEMENTATION STRUCTURE**;
and labels every revised hour, labor-reuse percentage, cost, and contribution as a **SENSITIVITY
ASSUMPTION**. It revisits delivery economics only, not recurring support economics or a final verdict.
Chapter 18 preserves the original $12,000 recurring fee as **MODELED ASSUMPTION**, treats repository
support surfaces as **OBSERVED IMPLEMENTATION STRUCTURE**, and labels every annual event, hour, labor
rate, direct cost, contribution, and break-even result **SENSITIVITY ASSUMPTION**. Routine credential,
mapping, replay, and reconciliation work is distinguished from new systems/workflows and major redesign.

## Chapter index and study path

- **Chapter 0 — The Hypothesis:** implemented ([read it](chapters/00-the-hypothesis.md)).
- **Chapter 1 — Discovery Before Workflow Design:** implemented ([read it](chapters/01-discovery-before-workflow-design.md)). Run `python -m trades_lab chapter1` to study the discovery briefing and blocked handoffs.
- **Chapter 2 — Define the Canonical Workflow Model:** implemented ([read it](chapters/02-canonical-workflow-model.md)). Run `python -m trades_lab chapter2` to inspect the canonical snapshot.
- **Chapter 3 — Lead to Estimate:** implemented ([read it](chapters/03-lead-to-estimate.md)). Run `python -m trades_lab chapter3` to compare successful and explicitly stopped handoffs.
- **Chapter 4 — Accepted Estimate to Job:** implemented ([read it](chapters/04-accepted-estimate-to-job.md)). Run `python -m trades_lab chapter4` and compare first delivery, duplicate delivery, and conflict.
- **Chapter 5 — Job to Schedule:** implemented ([read it](chapters/05-job-to-schedule.md)). Run `python -m trades_lab chapter5` to contrast request acknowledgement, assignment, replay, and changed context.
- **Chapter 6 — Materials and Purchasing Handoff:** implemented ([read it](chapters/06-materials-and-purchasing-handoff.md)). Run `python -m trades_lab chapter6` to compare direct mapping, unknown identity, conversion, and partial readiness.
- **Chapter 7 — Field Status to Office:** implemented ([read it](chapters/07-field-status-to-office.md)). Run `python -m trades_lab chapter7` to study blocked, partial, complete, replay, repeated-state, and stale-event scenarios.
- **Chapter 8 — Completion to Invoice Readiness:** implemented ([read it](chapters/08-completion-to-invoice-readiness.md)). Run `python -m trades_lab chapter8` to compare fully ready, partial-completion, missing-accounting-identity, replay, and approval-change scenarios.
- **Chapter 9 — Failure, Retry, and Replay:** implemented ([read it](chapters/09-failure-retry-and-replay.md)). Run `python -m trades_lab chapter9` to compare bounded recovery, targeted lookup, blocked uncertainty, and exhaustion.
- **Chapter 10 — Reconciliation:** implemented ([read it](chapters/10-reconciliation.md)). Run `python -m trades_lab chapter10` to compare clean and broken authoritative snapshots.
- **Chapter 11 — Exception Workflow:** implemented ([read it](chapters/11-exception-workflow.md)). Run `python -m trades_lab chapter11` to inspect routing, resolution, audit, aging, replay eligibility, and rejected actions.
- **Chapter 12 — Operational Briefing:** implemented ([read it](chapters/12-operational-briefing.md)). Run `python -m trades_lab chapter12` to compare healthy and degraded management snapshots.
- **Chapter 13 — Production Integration Engineering:** implemented ([read it](chapters/13-production-integration-engineering.md)). Run `python -m trades_lab chapter13` to inspect healthy startup, partial outages, uncertain-write alerting, scheduler overlap, and secret redaction.
- **Chapter 14 — Measure What Was Actually Built:** implemented ([read it](chapters/14-measure-what-was-actually-built.md)). Run `python -m trades_lab chapter14` to compare Chapter 0 assumptions with observed repository structure.
- **Chapter 15 — Customer-Specific Rules Stress Test:** implemented ([read it](chapters/15-customer-specific-rules-stress-test.md)). Run `python -m trades_lab chapter15` to inspect the bespoke-customer scenarios and structural change inventory.
- **Chapter 16 — Integration Access Stress Test:** implemented ([read it](chapters/16-integration-access-stress-test.md)). Run `python -m trades_lab chapter16` to compare clean, difficult, closed, CSV-drift, and human-assisted scenarios.
- **Chapter 17 — Delivery Economics From Engineering Evidence:** implemented ([read it](chapters/17-delivery-economics-from-engineering-evidence.md)). Run `python -m trades_lab chapter17` to inspect category evidence and explicit delivery sensitivities.
- **Chapter 18 — Support Economics:** implemented ([read it](chapters/18-support-economics.md)). Run `python -m trades_lab chapter18` to inspect recurring obligations, support sensitivities, and scope examples.
- **Chapter 19 — Build-versus-Buy:** planned and not implemented.

Suggested study path: read Chapter 0 and run its CLI, then read Chapter 1 and
run the discovery briefing. Inspect why readiness changes before drawing a
workflow. Then read Chapter 2, inspect its source-state mappings, and run its CLI
to compare allowed and rejected transitions. Executable validation is an
**OBSERVED LAB RESULT**, while source capabilities, mappings, and workflow
semantics remain synthetic **MODELED ASSUMPTIONS**.
After Chapters 9–12, run Chapter 13 and compare process liveness with readiness. Inspect why a
SupplyDesk outage stops material handoff without falsely stopping scheduling or field status, why
LedgerPro affects invoice readiness, why uncertainty points to reconciliation rather than blind
replay, and why the second local reconciliation run is skipped. The behavior is an **OBSERVED LAB
RESULT** inside fixed production-like fixtures; dependency behavior, credentials, thresholds,
schedules, and ownership are **MODELED ASSUMPTIONS**, not evidence of an actual deployment.
Then run Chapter 14 and inspect which units have multi-chapter use, which remain specialized,
and which carry support obligations. Treat its units and ratio as repository evidence only:
human time was not observed and the original 52.8% modeled effort assumption is not measured.
Chapter 14 differs from the originally planned standardized-second-contractor experiment: its useful
implementation inventory is preserved as additional evidence. The standardized-customer comparison
still belongs in the future roadmap; Chapter 15 is specifically the bespoke-customer stress test.
Then run Chapter 15 to compare unchanged infrastructure with specialized adapters, mappings, policies,
workflow layers, validation, exceptions, and support. Its structural units are not labor or economics.
Then run Chapter 16. The capability matrix demonstrates that interface quality changes technical
feasibility even when business need is unchanged. Strict export parsing and packet/provenance mechanisms
remain reusable; access-specific adapters and configuration grow, while a closed write changes the
architecture to human action plus reconciliation. These results are structural evidence, not economics.
Then run Chapter 17. Compare qualitative category evidence with transparent sensitivity inputs; do not
convert Chapter 14's unit ratio into labor reuse. Next run Chapter 18 and compare its standardized, mixed,
and bespoke annual support sensitivities. Delivery and recurring support remain separate; build-versus-buy
and the final opportunity verdict remain future questions.
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
Then run Chapter 8. Shared correlation, events, mappings, acknowledgements, exceptions,
and deterministic fingerprints recur; billing gates and evidence are workflow-specific,
the LedgerPro boundary is source-specific, and approval policy is customer-specific.
The synthetic result can mark prerequisites ready and create one billing work item,
but LedgerPro remains authoritative for invoice state and the lab creates no invoice.
Then run Chapter 9. Shared idempotency identity, correlation, acknowledgements, and
exceptions support bounded attempts and replay. Response classification, conflict and
authentication semantics, and lookup capability remain destination-specific. The
executable fault scenarios expand both RELIABILITY and SUPPORT SURFACE: exhausted
deliveries, uncertainty, credential repair, replay audit, and accumulated conflicts
require attention. These are implementation-structure observations, not production-grade
reliability or evidence for support economics.

## Economic discipline

Invoice principal is **not software-created value and is not included**. Chapter 8
models only a possible reduction in administrative touches, prerequisite chasing,
reconciliation, avoidable readiness delay, and associated cash-conversion burden.
Chapter 12 reports delay and prerequisites only. It adds no measured savings and does not
recalculate later-chapter economics.

The original verdict, **PROMISING — VALIDATE IN DISCOVERY**, is a modeled starting
hypothesis—not a conclusion. Even a technically successful implementation does
not automatically demonstrate a repeatable or attractive custom-software market.


## Reconciliation and support surface

Chapter 10 reuses stable external references, schedule/material request identity, field
provenance, readiness fingerprints, correlation, exception records, and Chapter 9 logical
delivery states. Its new structure is workflow-specific relationship checking rather than a
generic data-quality platform. Running reconciliation, inspecting recurring mismatches,
repairing access or mappings, deciding safe replay, and coordinating review are ongoing
**SUPPORT SURFACE** obligations. Findings and actions are advisory: no background daemon,
or automatic repair is present. Chapter 11 makes exception review and accountable ownership an
explicit support surface. Automation intentionally stops at ambiguity; only a bounded human action
may permit resumption, and replay approval remains distinct from replay execution.
Chapter 12 derives its briefing from those existing records rather than creating separate truth.
Briefing rules, changed workflow states, categories, owners, priorities, and thresholds add
reporting-maintenance **SUPPORT SURFACE**; stale aggregation can reduce management trust.
Chapter 13 expands that surface to credential rotation, vendor-outage response, mapping drift,
alert tuning and investigation, reconciliation/exception review, scheduler failures, observability
maintenance, configuration changes, and runbook updates. Chapter 14 measures this support surface
as tagged implementation units. Chapter 15 adds BidForge semantics, verbal-review handling, operations
approval routing, kit definitions, paper-entry validation, billing-project membership, weak-ID rules,
and crew-specific completion semantics. Reusable runtime mechanisms are visible, but structural counts
are not recurring support effort or contribution; economics remain open.
Chapter 16 adds export delivery/monitoring, schema drift, partial acknowledgements, production-only
testing, manual handoff ownership, reconciliation dependency, process training, and automation-expectation
maintenance. It inventories support surface but calculates no support cost.
