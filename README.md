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
```

The Chapter 0 CLI proves that its baseline is represented consistently and derives
ratios and payback deterministically. The Chapter 1 discovery briefing validates
authority, exposes modeled access risks and native alternatives, and gates future
handoffs. The Chapter 2 CLI displays deterministic state normalization, retained
source identity, and allowed and rejected transitions. None of the commands proves
fictional values or vendor capabilities.

## Chapter index and study path

- **Chapter 0 — The Hypothesis:** implemented ([read it](chapters/00-the-hypothesis.md)).
- **Chapter 1 — Discovery Before Workflow Design:** implemented ([read it](chapters/01-discovery-before-workflow-design.md)). Run `python -m trades_lab chapter1` to study the discovery briefing and blocked handoffs.
- **Chapter 2 — Define the Canonical Workflow Model:** implemented ([read it](chapters/02-canonical-workflow-model.md)). Run `python -m trades_lab chapter2` to inspect the canonical snapshot.
- **Chapter 3:** planned; not implemented.
- **Chapters 4–20:** planned; not implemented. Later work will introduce behavior progressively without assuming a favorable outcome.

Suggested study path: read Chapter 0 and run its CLI, then read Chapter 1 and
run the discovery briefing. Inspect why readiness changes before drawing a
workflow. Then read Chapter 2, inspect its source-state mappings, and run its CLI
to compare allowed and rejected transitions. Executable validation is an
**OBSERVED LAB RESULT**, while source capabilities, mappings, and workflow
semantics remain synthetic **MODELED ASSUMPTIONS**.

The original verdict, **PROMISING — VALIDATE IN DISCOVERY**, is a modeled starting
hypothesis—not a conclusion. Even a technically successful implementation does
not automatically demonstrate a repeatable or attractive custom-software market.
