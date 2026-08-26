# Chapter 15 — Customer-Specific Rules Stress Test

## Purpose and evidence boundary

Deliberately awkward customers are useful because mechanism reuse alone does not establish repeatable delivery. This chapter asks how quickly customer rules destroy repeatability by modeling **Tidewater Specialty Services**, a wholly fictional, synthetic contractor that is intentionally not representative. Its systems, policies, kits, records, and behavior are **MODELED ASSUMPTIONS**. Deterministic behavior demonstrated by the executable is an **OBSERVED LAB RESULT**.

```text
SHARED INTEGRATION CORE
        ↓
   NEW CUSTOMER
        ↓
 ┌──────┼────────┬───────────┐
 ↓      ↓        ↓           ↓
CONFIG MAPPING ADAPTER   CUSTOM RULE
                         ↓
                    DOES CORE CHANGE?
                         ↓
                  REUSE STRESS RESULT
```

## The differences under test

| Area | Tidewater variation | Compared with James River | Response |
|---|---|---|---|
| Estimate acceptance | BidForge `SIGNED` automates; `CUSTOMER_VERBAL_OK` requires review | Structural change | New adapter, mapping, and customer rule |
| Job creation | `PROSPECTIVE_JOB` exists before authorization | Structural change | Workflow-specific pre-authorization state |
| Scheduling | Operations-manager approval is mandatory | Structural change | Customer-specific gate |
| Materials | `TSS-KIT-A` expands to three requirements | Structural change | Customer-specific one-to-many expansion |
| Field completion | Office staff transcribe a paper sheet | Structural change | New adapter, validation, provenance, manual process |
| Invoice readiness | Several jobs belong to one billing project | Structural change | Bounded workflow aggregation |
| Identity | `WORK-001` is unique only within division and year | Structural change | Customer-specific qualified key |
| Completion meaning | Crew context changes the meaning of `DONE` | Structural change | Customer-specific evidence policy |
| Reliability | Existing retry/idempotency mechanisms | Same | Reused |
| Exceptions | New categories and routing content | Configuration change | Reused mechanism, new support content |
| Operational support | Eight additional obligations | Structural change | Specialized support |

## Eight experiments

### Acceptance and early creation

The new `BidForgeAdapter` maps `SIGNED` to automatic eligibility and `CUSTOMER_VERBAL_OK` to human review. Verbal approval cannot silently authorize a job. For early jobs, Approach A would force `PROSPECTIVE_JOB` into `JOB_PENDING` and lie about authorization. The implementation selects **Approach B**: retain a Tidewater pre-authorization state outside the original handoff. It is smaller and safer and preserves negative evidence rather than widening the canonical model.

### Approval before scheduling

A small Tidewater function checks authorization and operations approval. Only then does the existing scheduling-request boundary become eligible. This reuses the destination/idempotency pattern without inventing a generic approval engine. The approval exception and routing become support obligations.

### Material kit expansion

`TSS-KIT-A` deterministically expands to three lines. Two fixture mappings resolve and one remains explicit, producing `PARTIALLY_READY`; exact replay produces no duplicate destination requests. Mapping concepts partly reuse, but one-to-many expansion is customer code—not a BOM system.

### Partial paper workflow

`OfficeCompletionEntry` carries job, crew, date, code, entering role, and paper reference. The adapter rejects missing fields and preserves role and source-document reference as provenance. It models neither documents nor OCR. Compared with FieldTrack, the canonical idea of completion survives while adapter, confidence boundary, validation, and support differ.

### Billing aggregation

The bounded aggregation layer distinguishes an individually ready job from a ready billing project. `BP-100` remains blocked while either member job is blocked and never creates an invoice. The original per-job readiness abstraction therefore only partly reuses; rewriting Chapter 8 would hide specialization.

### Weak identity and conflicting completion semantics

Legacy identity is qualified by `source + division + year + source_id`, so residential 2026 `WORK-001` differs from commercial 2025 `WORK-001`. This adds onboarding and support burden without changing shared identity classes. A digital-crew `DONE` means modeled requirements and paperwork are complete; a legacy-crew `DONE` means physical work only. Literal status alone never implies readiness, and invoice eligibility remains an explicit separate gate.

## Reuse, change inventory, and core impact

The observed matrix reuses correlation, idempotency, retry, exception workflow, and the scheduling boundary. Identity reuses only with edge qualification. Estimate, material, completion, and invoice-readiness concepts partly reuse. BidForge and office-completion adapters are new; estimate policy, scheduling eligibility, kit expansion, weak identity, and completion semantics are customer-specific; early-job and billing-project layers are workflow-specific.

The deterministic structural inventory records 5 unchanged reused units, 1 configuration-only variation, 1 new mapping, 2 new adapters, 2 workflow-specific extensions, 4 customer-specific rules, **0 shared-core changes**, 2 new validation surfaces, 3 new exception shapes, 24 required behavior checks, and 8 support additions. These units are not hours and are not converted to labor or economics.

The verdict is **LOW_CORE_IMPACT**: all Tidewater policy is isolated in Chapter 15 and no shared domain abstraction changed. This is the better technical outcome, but it does not erase the amount of specialized edge and support structure.

## Support-surface growth

Support now includes BidForge status semantics, verbal-review exceptions, operations approval routing, kit definitions, manual completion validation, billing-project membership, weak-identifier qualification, and crew-specific completion semantics. Configuration itself becomes ongoing support when meaning or membership changes.

## Evidence for and against repeatability

**Supporting evidence:** shared correlation, idempotency, retry, exception, provenance concepts, and destination-boundary patterns remain useful without modification. Replay and controlled partial failure survive a one-to-many specialization.

**Negative evidence:** two adapters, two bounded workflow layers, four customer rules, new mapping content, validation, exceptions, and eight operational obligations appear for one deliberately unusual customer. Semantic reuse is substantially weaker than infrastructure reuse. The result **complicates** the original meaningful-reuse hypothesis: the core matters technically, while the economics remain unknown if every customer's edges stay expensive.

## Limitations and restraint

The experiment is synthetic, process-local, and deliberately adversarial. It does not establish prevalence among real contractors, production reliability, human effort, support cost, or economic viability. No workflow DSL, rules engine, plugin platform, BPMN/approval engine, BOM system, or generic billing framework was introduced. Chapter 16's integration-access stress test, export/read-only fallbacks, economics, verdict, and capstone remain unimplemented.
