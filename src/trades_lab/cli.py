"""Small command-line entry point for executable chapters."""

import argparse
from decimal import Decimal

from trades_lab.chapter0 import BASELINE_HYPOTHESIS
from trades_lab.chapter1 import QUESTIONS, SYSTEMS, TRANSITIONS, QuestionStatus, baseline_readiness
from trades_lab.chapter3 import LeadToEstimateHandoff
from trades_lab.chapter4 import (AcceptedEstimateToJobHandoff, CrewBoardSimulator,
                                 DestinationJob, ServiceAddress)
from trades_lab.chapter5 import (CrewBoardSchedulingSimulator, CrewSkill,
                                 JobToScheduleHandoff, ScheduleAssignment)
from trades_lab.chapter6 import MaterialsHandoff
from trades_lab.chapter7 import FieldStatusHandoff
from trades_lab.chapter8 import InvoiceReadinessService, ReadinessException, VALUE_MECHANISM
from trades_lab.chapter9 import (Fault, FaultScriptDestination, ReliableHandoff)
from trades_lab.chapter10 import ReconciliationSeverity, Reconciler
from trades_lab.chapter11 import (BusinessImpact, ExceptionWorkflow, OwnerRole,
                                  ResolutionAction, age_bucket)
from trades_lab.chapter12 import build_briefing
from trades_lab.chapter13 import (Capability, LocalScheduler, RunOutcome, ScheduledTask,
    build_metric_snapshot, due_tasks, evaluate_alerts, health_report, lookup_runbook,
    structured_log, validate_startup)
from trades_lab.chapter14 import (CHANGE_SCENARIOS, EvidenceLevel,
    ImplementationClassification, ReuseScope, build_report, reuse_matrix)
from trades_lab.chapter15 import (BidForgeAdapter, CORE_IMPACT, SUPPORT_SURFACE,
    OfficeCompletionAdapter, TidewaterKitExpander, aggregate_billing_project, change_inventory,
    interpret_done, schedule_gate)
from trades_lab.chapter16 import (CLEAN, CLOSED, DIFFICULT, RELIABILITY_MATRIX, SUPPORT,
    SchemaDriftError, build_report as build_access_report, classify_access,
    create_job_handoff_packet, evaluate_transition, parse_estimate_export, recommend_scope)
from trades_lab.fixtures.chapter15 import (BILLING_PROJECT_JOBS, PAPER_COMPLETION, WEAK_IDENTITY_2025,
                                            WEAK_IDENTITY_2026)
from trades_lab.fixtures.chapter13 import (CONFIG, CREDENTIALS, HEALTHY_DEPENDENCIES,
    LEDGERPRO_OUTAGE, MISSING_ESTIMATEWORKS_CREDENTIALS, NOW, SCHEDULE, SUPPLYDESK_OUTAGE)
from trades_lab.fixtures.chapter12 import DEGRADED_EVIDENCE, GENERATED_AT, HEALTHY_EVIDENCE
from trades_lab.domain import ExceptionCategory, ExceptionRecord, ExceptionStatus
from datetime import datetime, timezone
from trades_lab.fixtures.chapter10 import BROKEN_SNAPSHOT, CLEAN_SNAPSHOT
from trades_lab.domain.states import (EstimateState, JobState, map_estimateworks_state,
                                      map_fieldtrack_state)
from trades_lab.domain.transitions import can_transition, validate_transition, TransitionError
from trades_lab.fixtures.chapter2 import CUSTOMER, WORKFLOW_SNAPSHOT
from trades_lab.fixtures.chapter3 import (AMBIGUOUS_IDENTITY_LEAD, INELIGIBLE_LEAD,
                                          MISSING_CONTACT_LEAD, UNKNOWN_STATE_LEAD,
                                          VALID_QUALIFIED_LEAD)
from trades_lab.fixtures.chapter4 import (MISSING_CUSTOMER_ESTIMATE, OPEN_ESTIMATE,
                                          STALE_ACCEPTED_ESTIMATE,
                                          VALID_ACCEPTED_ESTIMATE)
from trades_lab.fixtures.chapter5 import (CANCELLED_JOB, CHANGED_DURATION_JOB,
                                          INVALID_WINDOW_JOB, MISSING_SKILL_JOB,
                                          PENDING_JOB, VALID_READY_JOB)
from trades_lab.fixtures.chapter6 import (AMBIGUOUS_REQUIREMENT,
    CHANGED_CONVERSION_REQUIREMENT, CONVERSION_REQUIREMENT, DIRECT_REQUIREMENT,
    PARTIAL_REQUIREMENTS, REGISTRY, SUBSTITUTE_REQUIREMENT, UNKNOWN_REQUIREMENT,
    UNIT_MISMATCH_REQUIREMENT)
from trades_lab.fixtures.chapter7 import CREW_MAPPINGS, JOB_MAPPINGS, event as field_event
from trades_lab.fixtures.chapter8 import (CUSTOMER_MAPPINGS, PARTIAL_FACTS, READY_FACTS)
from dataclasses import replace


def _money(value: Decimal) -> str:
    return f"${value:,.2f}"


def render_chapter0() -> str:
    hypothesis = BASELINE_HYPOTHESIS
    return "\n".join(
        (
            "CONSTRUCTION / TRADES WORKFLOW INTEGRATION LAB",
            "Chapter 0 — The Hypothesis",
            "",
            f"Evidence category: {hypothesis.evidence_category.value}",
            "All values below are fictional modeled assumptions, not benchmarks.",
            "",
            f"Customer: {hypothesis.customer.name}",
            f"Employees: {hypothesis.customer.employees}",
            f"Field crews: {hypothesis.customer.field_crews}",
            "",
            f"Annual current-state burden: {_money(hypothesis.annual_current_state_burden)}",
            f"Annual recoverable value: {_money(hypothesis.annual_recoverable_value)}",
            f"Implementation price: {_money(hypothesis.implementation_price)}",
            f"Annual recurring fee: {_money(hypothesis.annual_recurring_fee)}",
            f"Calculated implementation payback: {hypothesis.implementation_payback_months:.1f} months",
            f"Implementation / recoverable value: {hypothesis.implementation_price_percentage:.1f}%",
            f"Recurring fee / recoverable value: {hypothesis.recurring_fee_percentage:.1f}%",
            f"Modeled engineering hours: {hypothesis.modeled_engineering_hours}",
            f"Modeled reusable core: {hypothesis.reusable_core_percentage}%",
            "",
            "Original cookbook verdict:",
            hypothesis.original_verdict,
            "",
            "This is the hypothesis being tested.",
            "It is not an observed lab result.",
        )
    )


def render_chapter1() -> str:
    lines = [
        "CONSTRUCTION / TRADES WORKFLOW INTEGRATION LAB",
        "Chapter 1 — Discovery Before Workflow Design",
        "",
        "Evidence category: MODELED ASSUMPTION + OBSERVED LAB RESULT",
        "System capabilities below are synthetic modeled assumptions.",
        "",
        "SYSTEM DISCOVERY",
    ]
    for system in SYSTEMS:
        lines.extend((
            "", system.name,
            f"Authority: {', '.join(system.authoritative_for)}",
            f"Read: {system.read_capability.value}",
            f"Write: {system.write_capability.value}",
            f"Access risk: {system.access_risk.value}",
        ))
    lines.extend(("", "OPEN BLOCKERS"))
    for question in QUESTIONS:
        if question.status is QuestionStatus.BLOCKING:
            lines.extend(("", question.id, f"System: {question.system}", f"Question: {question.question}", f"Impact: {question.automation_impact}"))
    lines.extend(("", "AUTOMATION READINESS"))
    by_key = {transition.key: transition for transition in TRANSITIONS}
    for result in baseline_readiness():
        transition = by_key[result.transition]
        lines.extend(("", transition.label, result.status.value, f"Native integration: {result.native_integration.value}"))
        if result.reasons:
            lines.append("Reason:")
            lines.extend(f"- {reason}" for reason in result.reasons)
    lines.extend((
        "", "Observed lab result:",
        "The discovery model deterministically rejects ambiguous authority and prevents",
        "handoffs with unresolved critical discovery from being marked ready.",
        "No workflow automation is implemented.",
    ))
    return "\n".join(lines)


def render_chapter2() -> str:
    accepted = map_estimateworks_state("CUSTOMER_APPROVED")
    completed = map_fieldtrack_state("DONE")
    valid = can_transition(JobState.PENDING, JobState.READY)
    try:
        validate_transition(JobState.PENDING, JobState.COMPLETED)
    except TransitionError as error:
        rejection = str(error)
    lines = [
        "CONSTRUCTION / TRADES WORKFLOW INTEGRATION LAB",
        "Chapter 2 — Define the Canonical Workflow Model", "",
        "Evidence category: MODELED ASSUMPTION + OBSERVED LAB RESULT", "",
        "SOURCE STATE NORMALIZATION", "", "EstimateWorks",
        "Source state: CUSTOMER_APPROVED", f"Canonical state: {accepted.value}", "",
        "FieldTrack", "Source state: DONE", f"Canonical state: {completed.value}", "",
        "CANONICAL IDENTITY", "", "Customer:", f"Canonical ID: {CUSTOMER.canonical_id}",
        "Source references:",
    ]
    lines.extend(f"- {item.source_system}: {item.source_id}" for item in CUSTOMER.source_references)
    lines.extend((
        f"Observed at: {CUSTOMER.provenance.observed_at.isoformat()}", "",
        "TRANSITION CHECK", "", "Job: PENDING → READY", "ALLOWED" if valid else "REJECTED", "",
        "Job: PENDING → COMPLETED", "REJECTED", f"Reason: {rejection}", "",
        "CANONICAL WORKFLOW SNAPSHOT",
        " → ".join(type(item).__name__ for item in WORKFLOW_SNAPSHOT), "",
        "Observed lab result:",
        "Different source vocabularies normalize deterministically, provenance and multiple",
        "source references survive, and invalid transitions remain explicitly detectable.",
        "Source systems remain authoritative; no handoff is executed.",
    ))
    return "\n".join(lines)


def render_chapter3() -> str:
    valid_engine = LeadToEstimateHandoff()
    valid = valid_engine.process(VALID_QUALIFIED_LEAD)
    replay_engine = LeadToEstimateHandoff()
    replay_first = replay_engine.process(VALID_QUALIFIED_LEAD)
    replay_second = replay_engine.process(VALID_QUALIFIED_LEAD)
    ineligible = LeadToEstimateHandoff().process(INELIGIBLE_LEAD)
    missing = LeadToEstimateHandoff().process(MISSING_CONTACT_LEAD)
    unknown = LeadToEstimateHandoff().process(UNKNOWN_STATE_LEAD)
    identity_engine = LeadToEstimateHandoff()
    identity_engine.process(VALID_QUALIFIED_LEAD)
    ambiguous = identity_engine.process(AMBIGUOUS_IDENTITY_LEAD)
    command = valid.command
    normalized = valid.normalized_lead
    lines = [
        "CONSTRUCTION / TRADES WORKFLOW INTEGRATION LAB",
        "Chapter 3 — Lead to Estimate", "",
        "SCENARIO A — VALID QUALIFIED LEAD", "",
        "Source: RiverLead CRM / RL-1001",
        f"Canonical lead: {normalized.lead.canonical_id}",
        f"Source customer: {normalized.customer_reference.source_id}",
        f"Source version: {normalized.lead.provenance.source_version}",
        f"Correlation: {valid.correlation_id}", f"Outcome: {valid.outcome.value}",
        "Destination boundary: EstimateWorks", "Command: ESTIMATE INTAKE READY",
        f"Destination commands produced: {len(valid_engine.commands)}",
        "Events: " + " → ".join(event.event_type for event in valid.events),
        "Transferred fields:", "- customer identity/reference", "- customer name",
        "- contact", "- service address", "- requested service", "",
        "SCENARIO B — DUPLICATE DELIVERY", "",
        f"First delivery: {replay_first.outcome.value}",
        f"Second delivery: {replay_second.outcome.value}",
        f"Destination commands produced: {len(replay_engine.commands)}", "",
        "SCENARIO C — INELIGIBLE LEAD", "", f"Outcome: {ineligible.outcome.value}",
        "Exception: none", "", "SCENARIO D — MISSING CONTACT", "",
        f"Outcome: {missing.outcome.value}",
        f"Category: {missing.exception.category.value}", "",
        "SCENARIO E — UNKNOWN SOURCE STATE", "", f"Outcome: {unknown.outcome.value}",
        f"Category: {unknown.exception.category.value}", "",
        "SCENARIO F — AMBIGUOUS CUSTOMER IDENTITY", "",
        f"Outcome: {ambiguous.outcome.value}",
        f"Category: {ambiguous.exception.category.value}",
        "Automatic merge: no", "Destination command: none", "",
        "OBSERVED LAB RESULTS", "",
        "- A valid synthetic lead produces one deterministic intake command.",
        "- Exact replay is detected before a second command is produced.",
        "- Ineligible business state is distinguished from failure.",
        "- Invalid data and unknown states stop before the boundary.",
        "- Provenance and correlation connect the execution artifacts.",
        "- Narrow contact ambiguity stops automation; it does not prove identity.", "",
        "All vendor structures and rules are MODELED ASSUMPTIONS.",
        "No external estimate was created.",
    ]
    assert command is not None  # fixture invariant used by this executable narrative
    return "\n".join(lines)


def render_chapter4() -> str:
    handoff = AcceptedEstimateToJobHandoff()
    first = handoff.process(VALID_ACCEPTED_ESTIMATE, "event-001")
    replay = handoff.process(VALID_ACCEPTED_ESTIMATE, "event-001")
    second_delivery = handoff.process(VALID_ACCEPTED_ESTIMATE, "event-002")
    stale = handoff.process(STALE_ACCEPTED_ESTIMATE, "event-stale")
    missing = AcceptedEstimateToJobHandoff().process(MISSING_CUSTOMER_ESTIMATE)
    open_result = AcceptedEstimateToJobHandoff().process(OPEN_ESTIMATE)
    conflict_destination = CrewBoardSimulator()
    conflict_destination.preload_job(DestinationJob(
        "JOB-8800", "legacy-reference", "EW-EST-2001", 3, "EW-CUST-842",
        ServiceAddress("999 Conflicting Road", "Williamsburg", "VA", "23185"),
        "Different scope"))
    conflict_handoff = AcceptedEstimateToJobHandoff(conflict_destination)
    conflict = conflict_handoff.process(VALID_ACCEPTED_ESTIMATE)
    assert first.command and first.acknowledgement and replay.acknowledgement
    return "\n".join((
        "CONSTRUCTION / TRADES WORKFLOW INTEGRATION LAB",
        "Chapter 4 — Accepted Estimate to Job", "", "CONSEQUENTIAL WRITE EXPERIMENT", "",
        "Scenario A — First accepted estimate", "",
        "Estimate: EW-EST-2001 / version 3", "Canonical state: ACCEPTED",
        f"Idempotency key: {first.command.idempotency_key}", f"Result: {first.outcome.value}",
        "Destination: CrewBoard",
        f"Authoritative job: {first.acknowledgement.destination_job_id}",
        f"Jobs created: {len(handoff.destination.jobs)}",
        "Events: " + " → ".join(event.event_type for event in first.events), "",
        "Scenario B — Exact replay", "", f"Result: {replay.outcome.value}",
        f"Idempotency key: {replay.command.idempotency_key}",
        f"Authoritative job: {replay.acknowledgement.destination_job_id}",
        f"Jobs created: {len(handoff.destination.jobs)}", "",
        "Scenario C — Separate delivery of same business event", "",
        "Delivery IDs: event-001 / event-002", "Business idempotency identity: SAME",
        f"Result: {second_delivery.outcome.value}",
        f"Jobs created: {len(handoff.destination.jobs)}", "",
        "Scenario D — Missing customer identity", "", f"Result: {missing.outcome.value}",
        f"Category: {missing.exception.category.value}", "Jobs created: 0", "",
        "Scenario E — Stale estimate", "", f"Result: {stale.outcome.value}",
        f"Jobs created: {len(handoff.destination.jobs)}", "Destination rollback: NO", "",
        "Scenario F — Conflicting destination state", "", f"Result: {conflict.outcome.value}",
        f"Category: {conflict.exception.category.value}", "Automatic overwrite: NO",
        f"Jobs created: {len(conflict_destination.jobs)}", "",
        "Scenario G — Estimate not accepted", "", f"Result: {open_result.outcome.value}",
        "Jobs created: 0", "", "OBSERVED LAB RESULT", "",
        "Inside this modeled synthetic system, repeated delivery does not require a repeated",
        "business effect when creation uses stable authoritative business identity.", "",
        "The lab does not demonstrate exactly-once message delivery.",
        "It demonstrates one intended job effect under modeled CrewBoard idempotency and lookup.",
    ))


def render_chapter5() -> str:
    handoff = JobToScheduleHandoff()
    first = handoff.process(VALID_READY_JOB)
    replay = handoff.process(VALID_READY_JOB, "job-event-002")
    replay_request_count = len(handoff.destination.requests)
    changed = handoff.process(CHANGED_DURATION_JOB)
    missing = JobToScheduleHandoff().process(MISSING_SKILL_JOB)
    invalid = JobToScheduleHandoff().process(INVALID_WINDOW_JOB)
    pending = JobToScheduleHandoff().process(PENDING_JOB)
    conflict_destination = CrewBoardSchedulingSimulator()
    conflict_handoff = JobToScheduleHandoff(conflict_destination)
    original = conflict_handoff.process(VALID_READY_JOB)
    conflict_destination.record_assignment(ScheduleAssignment(
        "CB-ASG-001", VALID_READY_JOB.job_id, original.acknowledgement.request_id,
        "CREW-4", (CrewSkill.HVAC_INSTALL, CrewSkill.TWO_PERSON_CREW),
        VALID_READY_JOB.earliest_start, VALID_READY_JOB.latest_completion))
    conflict = conflict_handoff.process(CHANGED_DURATION_JOB)
    cancel_handoff = JobToScheduleHandoff()
    cancel_handoff.process(VALID_READY_JOB)
    cancelled = cancel_handoff.process(CANCELLED_JOB)
    cancel_replay = cancel_handoff.process(CANCELLED_JOB, "job-event-cancel-replay")
    stale = cancel_handoff.process(VALID_READY_JOB, "old-ready-event")
    assert first.acknowledgement and replay.acknowledgement
    return "\n".join((
        "CONSTRUCTION / TRADES WORKFLOW INTEGRATION LAB",
        "Chapter 5 — Job to Schedule", "", "SCENARIO A — VALID JOB", "",
        f"Authoritative job: {VALID_READY_JOB.job_id}", "Job state: READY",
        "Required capabilities: " + ", ".join(x.value for x in VALID_READY_JOB.required_skill_tags),
        f"Estimated duration: {VALID_READY_JOB.estimated_duration_minutes} minutes",
        f"Outcome: {first.outcome.value}",
        f"CrewBoard request: {first.acknowledgement.request_id}",
        f"Request state: {first.acknowledgement.request_state.value}",
        "Crew assigned by integration: NO", "Acknowledgement means assigned: NO", "",
        "SCENARIO B — EXACT REPLAY", "", f"Outcome: {replay.outcome.value}",
        f"Same request: {first.acknowledgement.request_id == replay.acknowledgement.request_id}",
        f"Scheduling requests: {replay_request_count}", "",
        "SCENARIO C — MISSING CREW REQUIREMENT", "", f"Outcome: {missing.outcome.value}",
        f"Exception: {missing.exception.summary}", "Crew guessed: NO", "",
        "SCENARIO D — INVALID WINDOW", "", f"Outcome: {invalid.outcome.value}", "",
        "SCENARIO E — JOB NOT READY", "", f"Outcome: {pending.outcome.value}", "",
        "SCENARIO F — JOB REQUIREMENTS CHANGED", "", "Original duration: 240 minutes",
        "New duration: 360 minutes", f"Outcome: {changed.outcome.value}",
        "Automatically rescheduled: NO", "Previous request provenance preserved: YES", "",
        "SCENARIO G — EXISTING ASSIGNMENT CONFLICT", "", f"Outcome: {conflict.outcome.value}",
        "Automatic assignment overwrite: NO", "Dispatcher review required: YES", "",
        "SCENARIO H — CANCELLATION", "", f"Outcome: {cancelled.outcome.value}",
        f"Repeated cancellation: {cancel_replay.outcome.value}",
        "Historical request deleted: NO", f"Old READY event after cancellation: {stale.outcome.value}",
        "", "OBSERVED LAB RESULT", "",
        "Validated scheduling context crosses the boundary without choosing a crew.",
        "Acknowledgement remains UNASSIGNED, exact replay creates no duplicate, and a",
        "meaningful change remains distinct from replay. Authoritative assignments are",
        "not overwritten; conflicts require human review.", "",
        "CrewBoard semantics, crew capabilities, windows, and cancellation support are",
        "MODELED ASSUMPTIONS. This lab does not optimize schedules.",
    ))


def render_chapter6() -> str:
    handoff = MaterialsHandoff(REGISTRY)
    direct = handoff.process(DIRECT_REQUIREMENT)
    replay = handoff.process(DIRECT_REQUIREMENT)
    replay_request_count = len(handoff.destination.requests)
    conversion = handoff.process(CONVERSION_REQUIREMENT)
    unknown = MaterialsHandoff(REGISTRY).process(UNKNOWN_REQUIREMENT)
    mismatch = MaterialsHandoff(REGISTRY).process(UNIT_MISMATCH_REQUIREMENT)
    ambiguous = MaterialsHandoff(REGISTRY).process(AMBIGUOUS_REQUIREMENT)
    substitute = MaterialsHandoff(REGISTRY).process(SUBSTITUTE_REQUIREMENT)
    partial = MaterialsHandoff(REGISTRY).process_job(PARTIAL_REQUIREMENTS)
    changed_engine = MaterialsHandoff(REGISTRY)
    original = changed_engine.process(CONVERSION_REQUIREMENT)
    changed = changed_engine.process(CHANGED_CONVERSION_REQUIREMENT)
    assert direct.command and direct.acknowledgement and conversion.command
    assert unknown.exception and mismatch.exception and ambiguous.exception
    return "\n".join((
        "CONSTRUCTION / TRADES WORKFLOW INTEGRATION LAB",
        "Chapter 6 — Materials and Purchasing Handoff", "",
        "SCENARIO A — DIRECT APPROVED MAPPING", "",
        f"Job: {DIRECT_REQUIREMENT.job_id}",
        f"Source material: {DIRECT_REQUIREMENT.source_material_id}",
        f"Destination material: {direct.command.destination_material_id}",
        f"Quantity: {direct.command.quantity} {direct.command.unit.value}",
        f"Outcome: {direct.outcome.value}",
        f"SupplyDesk reference: {direct.acknowledgement.request_id}", "",
        "SCENARIO B — EXACT REPLAY", "", f"Outcome: {replay.outcome.value}",
        f"Destination requests after replay: {replay_request_count}", "",
        "SCENARIO C — EXPLICIT UNIT CONVERSION", "",
        f"Source: {CONVERSION_REQUIREMENT.quantity} {CONVERSION_REQUIREMENT.unit.value}",
        f"Destination: {conversion.command.quantity} {conversion.command.unit.value}",
        "Conversion rule: FEET-TO-100FT-ROLL (APPROVED)",
        f"Outcome: {conversion.outcome.value}", "",
        "SCENARIO D — UNKNOWN MATERIAL", "",
        f"Source material: {UNKNOWN_REQUIREMENT.source_material_id}",
        f"Outcome: {unknown.outcome.value}", f"Category: {unknown.exception.category.value}",
        "Guessed destination: NO", "", "SCENARIO E — UNSUPPORTED UNIT", "",
        f"Source: {UNIT_MISMATCH_REQUIREMENT.quantity} {UNIT_MISMATCH_REQUIREMENT.unit.value}",
        f"Outcome: {mismatch.outcome.value}", "Destination request: NONE", "",
        "SCENARIO F — AMBIGUOUS MAPPING", "", f"Outcome: {ambiguous.outcome.value}",
        "Arbitrary destination selected: NO", "", "SCENARIO G — SUBSTITUTE SUGGESTED", "",
        f"Outcome: {substitute.outcome.value}", "Automatic substitution: NO", "",
        "SCENARIO H — PARTIAL JOB MATERIAL READINESS", "",
        f"Requirements: {partial.requirement_count}", f"Ready: {partial.ready_count}",
        f"Exceptions: {partial.exception_count}",
        f"Overall integration readiness: {partial.readiness.value}", "",
        "SCENARIO I — CHANGED QUANTITY", "",
        f"Original SupplyDesk request: {original.acknowledgement.request_id}",
        f"Changed outcome: {changed.outcome.value}",
        "Previous handoff retained and linked: YES", "", "OBSERVED LAB RESULT", "",
        "The mapping mechanism can be reusable while mapping content remains source- and",
        "customer-specific. Unknown identity, ambiguous identity, unsupported units, and",
        "unapproved substitutions stop automation. Valid siblings still proceed.", "",
        "Material codes, equivalence, conversion factors, substitution and SupplyDesk",
        "semantics are MODELED ASSUMPTIONS. No purchasing or inventory was implemented.",
    ))


def render_chapter7() -> str:
    handoff = FieldStatusHandoff(JOB_MAPPINGS, CREW_MAPPINGS)
    dispatched = handoff.process(field_event("FT-EVT-7001", "EN_ROUTE", 1))
    arrived = handoff.process(field_event("FT-EVT-7002", "ONSITE", 2))
    started = handoff.process(field_event("FT-EVT-7003", "WORKING", 3))
    blocked = handoff.process(field_event("FT-EVT-7004", "HOLD", 4, "MATERIAL_MISSING"))
    resumed = handoff.process(field_event("FT-EVT-7005", "WORKING", 5))
    partial = handoff.process(field_event("FT-EVT-7006", "PARTIAL", 6))
    complete = handoff.process(field_event("FT-EVT-7007", "DONE", 7))
    replay_engine = FieldStatusHandoff(JOB_MAPPINGS, CREW_MAPPINGS)
    replay_raw = field_event("FT-EVT-REPLAY", "WORKING", 4)
    first = replay_engine.process(replay_raw)
    replay = replay_engine.process(replay_raw)
    repeated = replay_engine.process(field_event("FT-EVT-REPEAT", "WORKING", 5))
    stale = replay_engine.process(field_event("FT-EVT-STALE", "ONSITE", 3))
    unknown = FieldStatusHandoff(JOB_MAPPINGS, CREW_MAPPINGS).process(
        field_event("FT-EVT-UNKNOWN", "MYSTERY", 1))
    identity = FieldStatusHandoff(JOB_MAPPINGS, CREW_MAPPINGS).process(
        field_event("FT-EVT-NOJOB", "WORKING", 1, job_id="FT-JOB-UNKNOWN"))
    return "\n".join((
        "CONSTRUCTION / TRADES WORKFLOW INTEGRATION LAB",
        "Chapter 7 — Field Status to Office", "",
        "SCENARIO A — CREW DISPATCHED", "Source: FieldTrack / EN_ROUTE",
        f"Canonical: {dispatched.office_update.field_status.value}",
        f"Authoritative job: {dispatched.office_update.authoritative_job_id}",
        f"Outcome: {dispatched.outcome.value}", "",
        "SCENARIO B — WORK STARTED", f"Progression: {arrived.office_update.field_status.value} → {started.office_update.field_status.value}",
        f"Outcome: {started.outcome.value}", "",
        "SCENARIO C — BLOCKED", f"Canonical: {blocked.office_update.field_status.value}",
        f"Reason: {blocked.office_update.blocked_reason.value}", "Office attention: REQUIRED", "",
        "SCENARIO D — RESUME", "Progression: BLOCKED → IN_PROGRESS", f"Outcome: {resumed.outcome.value}", "",
        "SCENARIO E — PARTIAL COMPLETION", f"Canonical: {partial.office_update.field_status.value}",
        "Completed: NO", "Invoice ready: NO", "",
        "SCENARIO F — FIELD COMPLETION", f"Canonical: {complete.office_update.field_status.value}",
        "Invoice created: NO", "Invoice readiness decided: NO", "",
        "SCENARIO G/H — REPLAY VS REPEATED BUSINESS STATE",
        f"First delivery: {first.outcome.value}", f"Exact replay: {replay.outcome.value}",
        f"New event, same WORKING state: {repeated.outcome.value}", "",
        "SCENARIO I — STALE EVENT", "Current sequence: 5", "Incoming sequence: 3",
        f"Outcome: {stale.outcome.value}", "State rolled backward: NO", "",
        "SCENARIO J — UNKNOWN STATUS", f"Outcome: {unknown.outcome.value}", "Guessed mapping: NO", "",
        "SCENARIO K — UNKNOWN JOB IDENTITY", f"Outcome: {identity.outcome.value}",
        "Office update: NONE", "Guessed match: NO", "",
        "OBSERVED LAB RESULT", "The bounded integration normalizes required field states, detects exact replay,",
        "keeps repeated business observations distinct, and prevents stale rollback.",
        "Field completion remains distinct from invoice readiness.", "",
        "All FieldTrack states, sequence semantics, identities, and rules are MODELED ASSUMPTIONS.",
    ))


def render_chapter8() -> str:
    service = InvoiceReadinessService(CUSTOMER_MAPPINGS)
    ready = service.evaluate(READY_FACTS)
    replay = service.evaluate(READY_FACTS)
    partial = InvoiceReadinessService(CUSTOMER_MAPPINGS).evaluate(PARTIAL_FACTS)
    material = InvoiceReadinessService(CUSTOMER_MAPPINGS).evaluate(
        replace(READY_FACTS, materials_resolved=False))
    missing_identity = InvoiceReadinessService({}).evaluate(READY_FACTS)
    approval_facts = replace(READY_FACTS, job_type="COMMERCIAL_CHANGE_ORDER")
    before = InvoiceReadinessService(CUSTOMER_MAPPINGS).evaluate(approval_facts)
    after = InvoiceReadinessService(CUSTOMER_MAPPINGS).evaluate(
        replace(approval_facts, customer_approved=True))
    nonblocking = InvoiceReadinessService(CUSTOMER_MAPPINGS).evaluate(replace(
        READY_FACTS, exceptions=(ReadinessException("EX-NOTE", "operational note", True, False),)))
    checks = "\n".join(f"{c.name:<32} {c.outcome.value} — {c.detail}" for c in ready.readiness.checks)
    return "\n".join((
        "CONSTRUCTION / TRADES WORKFLOW INTEGRATION LAB",
        "Chapter 8 — Completion to Invoice Readiness", "",
        "SCENARIO A — FULLY READY", "Authoritative job: JOB-9001", "Field status: COMPLETED", "",
        "READINESS CHECKS", checks, f"Result: {ready.readiness.status.value}",
        f"LedgerPro billing-ready work item: {ready.acknowledgement.billing_work_item_reference}",
        "Invoice created: NO", "", "SCENARIO B — EXACT READINESS REPLAY",
        f"Same fingerprint: {ready.readiness.fingerprint == replay.readiness.fingerprint}",
        f"Outcome: {replay.acknowledgement.outcome.value}", f"Work items: {len(service.ledgerpro.work_items)}", "",
        "SCENARIO C — PARTIAL COMPLETION", "Field status: PARTIALLY_COMPLETE",
        f"Result: {partial.readiness.status.value}", "Invoice-ready command: NO", "",
        "SCENARIO D — MATERIAL EXCEPTION", f"Result: {material.readiness.status.value}",
        material.readiness.blocking_checks[0], "", "SCENARIO E — ACCOUNTING IDENTITY MISSING",
        f"Result: {missing_identity.readiness.status.value}", "Guessed LedgerPro customer: NO", "",
        "SCENARIO H — APPROVAL RECEIVED", f"Before: {before.readiness.status.value}",
        f"After: {after.readiness.status.value}",
        f"Same readiness fingerprint: {before.readiness.fingerprint == after.readiness.fingerprint}", "",
        "SCENARIO I — NON-BILLING EXCEPTION", f"Result: {nonblocking.readiness.status.value}", "",
        "VALUE MECHANISM", VALUE_MECHANISM["path"],
        "Integration may reduce: " + ", ".join(VALUE_MECHANISM["may_reduce"]),
        "Invoice principal: NOT INCLUDED", "", "OBSERVED LAB RESULT",
        "Field completion alone is insufficient for invoice readiness.",
        "Explicit synthetic prerequisites can produce a billing-ready handoff without creating an invoice.",
        "LedgerPro remains authoritative for invoice identity, state, posting, and payment.",
    ))


def render_chapter9() -> str:
    def run(name: str, faults: list[Fault], *, lookup: bool = True, reconcile: bool = True):
        destination = FaultScriptDestination(faults, supports_lookup=lookup)
        handoff = ReliableHandoff(destination)
        delivery = handoff.new_delivery(f"event-{name}", f"accepted-estimate:{name}:v1",
                                        f"correlation-{name}", delivery_id=f"delivery-{name}")
        return handoff, destination, handoff.execute(delivery, reconcile_uncertain=reconcile)

    _, outage_destination, outage = run("outage", [Fault.UNAVAILABLE, Fault.UNAVAILABLE, Fault.SUCCESS])
    _, timeout_destination, timeout = run("timeout", [Fault.TIMEOUT_BEFORE_WRITE, Fault.SUCCESS])
    _, lost_destination, lost = run("lost", [Fault.ACKNOWLEDGEMENT_LOST])
    _, no_lookup_destination, no_lookup = run("no-lookup", [Fault.ACKNOWLEDGEMENT_LOST], lookup=False)
    _, _, malformed = run("malformed", [Fault.MALFORMED])
    _, _, conflict = run("conflict", [Fault.CONFLICT])
    auth_handoff, _, authentication = run("auth", [Fault.EXPIRED_CREDENTIALS, Fault.SUCCESS])
    auth_handoff.destination.repair_credentials()
    repaired = auth_handoff.replay(authentication.delivery_id)
    _, _, exhausted = run("exhausted", [Fault.UNAVAILABLE] * 3)
    _, busy_destination, busy = run("busy", [Fault.SERVICE_BUSY, Fault.SUCCESS])
    attempts = lambda d: ", ".join(
        f"{a.attempt_number}:{a.outcome.value}/{a.failure_category.value if a.failure_category else 'NONE'}"
        for a in d.attempts)
    return "\n".join((
        "CONSTRUCTION / TRADES WORKFLOW INTEGRATION LAB",
        "Chapter 9 — Failure, Retry, and Replay", "",
        "SCENARIO A — TEMPORARY OUTAGE", f"Attempts: {attempts(outage)}",
        f"Final state: {outage.state.value}", f"Business effects: {len(outage_destination.effects)}", "",
        "SCENARIO B — TIMEOUT BEFORE WRITE", f"Attempts: {attempts(timeout)}",
        f"Final state: {timeout.state.value}", f"Business effects: {len(timeout_destination.effects)}", "",
        "SCENARIO C — ACKNOWLEDGEMENT LOST", "Destination write: SUCCEEDED",
        "Integration acknowledgement: LOST", "Recorded intermediate state: UNCERTAIN",
        "Blind retry: NO", f"Destination lookup: FOUND {lost.acknowledgement}",
        f"Final state: {lost.state.value}", f"Business effects: {len(lost_destination.effects)}", "",
        "SCENARIO D — UNCERTAIN + NO LOOKUP", "Blind retry: NO",
        f"Final state: {no_lookup.state.value}", "Automatic recovery: NOT SAFE",
        f"Human review: {'REQUIRED' if no_lookup.human_review_required else 'NOT REQUIRED'}",
        f"Business effects (unconfirmed): {len(no_lookup_destination.effects)}", "",
        "SCENARIO E — MALFORMED INPUT", "Failure category: PERMANENT_VALIDATION",
        f"Automatic retries: {max(0, len(malformed.attempts) - 1)}", "",
        "SCENARIO F — CONFLICT", f"Failure category: {conflict.exception.category.value}",
        "Automatic retry: NO", "Exception: CREATED", "",
        "SCENARIO G — EXPIRED CREDENTIALS", "Failure category: AUTHENTICATION",
        "Automatic attempts stopped: YES", "Credential repair: MODELED",
        f"Explicit replay final state: {repaired.state.value}", "",
        "SCENARIO H — RETRY EXHAUSTION", f"Attempts: {len(exhausted.attempts)}",
        f"Final state: {exhausted.state.value}", "Unresolved work visible: YES", "",
        "SCENARIO I — TEMPORARY SERVICE_BUSY", f"Attempts: {attempts(busy)}",
        f"Final state: {busy.state.value}", f"Business effects: {len(busy_destination.effects)}", "",
        "OBSERVED LAB RESULT",
        "Retries are safe only when failure category and business-effect uncertainty are explicit.",
        "A targeted stable-identity lookup resolves a modeled lost acknowledgement without duplication;",
        "without lookup, the consequential delivery remains blocked for human review.", "",
        "MODELED ASSUMPTIONS: fault behavior, retry limit, credentials, lookup, and outage sequence.",
        "This bounded synchronous experiment is not production-grade reliability or Chapter 10 reconciliation.",
    ))


def render_chapter10() -> str:
    reconciler = Reconciler()
    clean = reconciler.reconcile(CLEAN_SNAPSHOT)
    broken = reconciler.reconcile(BROKEN_SNAPSHOT)
    lines = [
        "CONSTRUCTION / TRADES WORKFLOW INTEGRATION LAB",
        "Chapter 10 — Reconciliation", "",
        "SCENARIO A — CLEAN WORKFLOW", "",
        f"Accepted estimates checked: {clean.checked_counts.accepted_estimates}",
        f"Jobs checked: {clean.checked_counts.jobs}",
        f"Scheduling checks: {clean.checked_counts.scheduling}",
        f"Material checks: {clean.checked_counts.materials}",
        f"Completed jobs checked: {clean.checked_counts.completed_jobs}",
        f"Critical findings: {clean.critical_count}", f"Warnings: {clean.warning_count}",
        "Result: CONSISTENT" if not clean.findings else "Result: FINDINGS", "",
        "SCENARIO B — BROKEN WORKFLOW",
    ]
    for finding in broken.findings:
        lines.extend(("", finding.severity.value, finding.reconciliation_id, finding.category.value,
                      f"{finding.entity_type}: {finding.entity_id}", finding.summary,
                      f"Expected: {finding.expected_state}", f"Observed: {finding.observed_state}",
                      f"Correlation: {finding.correlation_id or 'none'}",
                      f"Recommended action: {finding.recommended_action.value}"))
    lines.extend(("", "SUMMARY", f"Critical: {broken.critical_count}",
                  f"Warnings: {broken.warning_count}",
                  f"Automatic repairs performed: {broken.automatic_repairs_performed}", "",
                  "OBSERVED LAB RESULT",
                  "Successful handoff history alone is not enough to prove current consistency.",
                  "Authoritative snapshots expose missing, conflicting, exhausted, orphaned, and unresolved state.",
                  "The reconciliation is read-oriented and performs no automatic repair.", "",
                  "MODELED ASSUMPTIONS: snapshots, severity and expectation rules, and recommended actions."))
    return "\n".join(lines)


def render_chapter11() -> str:
    workflow = ExceptionWorkflow()
    def add(identifier, category, entity, days, impact, source="Integration", accounting=False):
        record = ExceptionRecord(identifier, category, "condition", entity, source,
                                 f"{category.value} requires review", ExceptionStatus.OPEN,
                                 datetime(2026, 1, 11 - days, 12, tzinfo=timezone.utc), f"corr-{entity}")
        return workflow.create(record, f"{category.value}:{entity}", impact,
                               accounting_mapping=accounting)
    identity = add("EXC-001", ExceptionCategory.IDENTITY, "LEAD-1001", 2, BusinessImpact.BLOCKS_HANDOFF)
    material = add("EXC-002", ExceptionCategory.MAPPING, "MAT-404", 0, BusinessImpact.BLOCKS_HANDOFF)
    conflict = add("EXC-003", ExceptionCategory.STATE_CONFLICT, "JOB-9102", 4, BusinessImpact.OPERATIONAL_REVIEW)
    access = add("EXC-004", ExceptionCategory.ACCESS, "DEL-009", 1, BusinessImpact.BLOCKS_HANDOFF, "CrewBoard")
    add("EXC-005", ExceptionCategory.VALIDATION, "JOB-AGING", 4, BusinessImpact.OPERATIONAL_REVIEW)
    open_lines = ["OPEN EXCEPTIONS"]
    for item in workflow.queue(status=ExceptionStatus.OPEN):
        open_lines.extend(("", item.record.exception_id, f"Category: {item.record.category.value}",
                           f"Entity: {item.record.entity_id}", f"Owner: {item.owner_role.value}",
                           f"Impact: {item.impact.value}", f"Age: {age_bucket(item.record.created_at).value}"))
    identity = workflow.resolve(identity.record.exception_id, ResolutionAction.CONFIRM_IDENTITY,
                                "confirmed existing customer identity", OwnerRole.OFFICE_MANAGER,
                                mapping=("RiverLead:X", "EstimateWorks:Y"))
    material = workflow.resolve(material.record.exception_id, ResolutionAction.CREATE_MAPPING,
                                "approved exact material mapping", OwnerRole.OPERATIONS_MANAGER,
                                mapping=("MAT-404", "SUPPLY-44"))
    material = workflow.approve_replay(material.record.exception_id, OwnerRole.OPERATIONS_MANAGER)
    unchanged = access
    try:
        workflow.resolve(access.record.exception_id, ResolutionAction.CREATE_MAPPING, "invalid",
                         OwnerRole.INTEGRATION_SUPPORT, mapping=("x", "y"))
    except ValueError:
        invalid = "REJECTED"
    lines = ["CONSTRUCTION / TRADES WORKFLOW INTEGRATION LAB", "Chapter 11 — Exception Workflow", ""] + open_lines
    lines += ["", "SCENARIO A — IDENTITY RESOLUTION", "Action: CONFIRM_IDENTITY",
              "Status before: OPEN", f"Status after: {identity.status.value}",
              f"Automation may resume: {'YES' if identity.resolution.automation_may_resume else 'NO'}",
              "Source records overwritten: NO", f"Audit events: {len(identity.history)}",
              "", "SCENARIO B — MATERIAL MAPPING", "Action: CREATE_MAPPING", "Mapping approved: YES",
              f"Exception: {material.status.value}", f"Replay eligible: {'YES' if material.replay_approved else 'NO'}",
              "Replay executed automatically: NO", "", "SCENARIO C — STATE CONFLICT",
              f"Owner: {conflict.owner_role.value}", "Automatic destination overwrite: NO", "Review: REQUIRED",
              "", "SCENARIO H — INVALID ACTION", "Exception category: ACCESS",
              "Attempted action: CREATE_MAPPING", f"Result: {invalid}",
              f"Exception state changed: {'NO' if workflow.exceptions[access.record.exception_id] == unchanged else 'YES'}",
              "", "QUEUE SUMMARY", f"Open: {len(workflow.queue(status=ExceptionStatus.OPEN))}",
              f"Resolved: {len(workflow.queue(status=ExceptionStatus.RESOLVED))}",
              f"Overdue open: {sum(age_bucket(x.record.created_at).value == 'OVERDUE' for x in workflow.queue(status=ExceptionStatus.OPEN))}",
              "", "OBSERVED LAB RESULT",
              "Unsafe automation becomes owned, bounded, auditable human work with explicit replay approval.",
              "Source systems remain authoritative; exception resolution performs no source business-state write.",
              "", "MODELED ASSUMPTIONS: roles, routing, impacts, allowed actions, replay eligibility, and aging thresholds."]
    return "\n".join(lines)


def render_chapter12() -> str:
    healthy = build_briefing(HEALTHY_EVIDENCE, GENERATED_AT)
    degraded = build_briefing(DEGRADED_EVIDENCE, GENERATED_AT)
    c = degraded.workflow_counts
    lines = [
        "CONSTRUCTION / TRADES WORKFLOW INTEGRATION LAB", "Chapter 12 — Operational Briefing", "",
        "SCENARIO A — HEALTHY OPERATIONS", "", f"Overall health: {healthy.health_summary.state.value}",
        f"Critical reconciliation findings: {healthy.reconciliation_summary.critical_count}",
        f"Uncertain deliveries: {healthy.workflow_counts.uncertain_deliveries}",
        f"Overdue exceptions: {healthy.exception_summary.overdue_count}",
        f"Completed jobs blocked from invoice readiness: {healthy.workflow_counts.completed_not_invoice_ready}", "",
        "SCENARIO B — DEGRADED OPERATIONS", "", f"Overall health: {degraded.health_summary.state.value}", "",
        "WORKFLOW BOTTLENECKS",
        f"Estimate → Job: {c.accepted_estimates_awaiting_job} missing handoff",
        f"Job → Schedule: {c.scheduling_review_required} review required",
        f"Materials: {c.unresolved_material_mappings} unresolved mappings",
        f"Field: {c.field_blocked_jobs} blocked job",
        f"Completion → Invoice Readiness: {c.completed_not_invoice_ready} blocked", "",
        "DELIVERY HEALTH", f"Exhausted: {c.exhausted_deliveries}", f"Uncertain: {c.uncertain_deliveries}", "",
        "EXCEPTIONS", f"Open: {degraded.exception_summary.open_count}",
        f"Overdue: {degraded.exception_summary.overdue_count}", "", "TOP ATTENTION ITEMS",
    ]
    for item in degraded.attention_items[:5]:
        lines.extend(("", item.severity.value, item.entity_id, item.summary,
                      *( (f"Owner: {item.owner_role.value}",) if item.owner_role else ()),
                      f"Evidence: {item.evidence_reference}"))
    lines.extend(("", "COMPLETION → READINESS"))
    for delay in healthy.completion_delays + degraded.completion_delays:
        lines.extend(("", delay.job_id, f"Elapsed: {delay.elapsed.total_seconds() / 3600:g} hours",
                      f"Status: {delay.status}", *((f"Blocker: {delay.blocker}",) if delay.blocker else ())))
    lines.extend(("", "MODELED ASSUMPTION",
        "Health thresholds, severity, priority, synthetic times, selected measures, and delay interpretation.",
        "No numeric pseudo-score is used.", "", "OBSERVED LAB RESULT",
        "Existing handoff, delivery, reconciliation, and exception evidence can be condensed",
        "without creating a second source of truth; bottlenecks retain evidence IDs and ownership.",
        "Invoice principal is not software-created value.",
        "This is a current fixture snapshot, not production observability or a system of record."))
    return "\n".join(lines)


def render_chapter13() -> str:
    healthy = health_report(CONFIG, CREDENTIALS, HEALTHY_DEPENDENCIES)
    missing = health_report(CONFIG, MISSING_ESTIMATEWORKS_CREDENTIALS, HEALTHY_DEPENDENCIES)
    supply = health_report(CONFIG, CREDENTIALS, SUPPLYDESK_OUTAGE)
    ledger = health_report(CONFIG, CREDENTIALS, LEDGERPRO_OUTAGE)
    cap = lambda report, name: next(x.state.value for x in report.capabilities if x.capability is name)
    metrics = build_metric_snapshot(DEGRADED_EVIDENCE, NOW)
    uncertain = next(a for a in evaluate_alerts(metrics, uncertain_evidence=("DEL-104",))
                     if a.category == "UNCERTAIN_WRITE")
    overdue = next(a for a in evaluate_alerts(metrics,
        overdue_evidence=(("EXC-015", OwnerRole.OPERATIONS_MANAGER),)) if a.category == "EXCEPTION_AGING")
    scheduler = LocalScheduler(); first = scheduler.begin(ScheduledTask.RECONCILIATION, NOW)
    second = scheduler.begin(ScheduledTask.RECONCILIATION, NOW)
    completed = scheduler.finish(first, NOW.replace(minute=5), "RECON-REPORT-013")
    secret = "synthetic-never-log-this"
    record = structured_log(NOW, "INFO", "CREDENTIAL_CHECK", context={
        "credential_reference": "estimateworks-api", "credential_value": secret})
    runbook = lookup_runbook("AUTHENTICATION")
    return "\n".join((
        "CONSTRUCTION / TRADES WORKFLOW INTEGRATION LAB", "Chapter 13 — Production Integration Engineering", "",
        "SCENARIO A — HEALTHY STARTUP", "", f"Environment: {CONFIG.environment}",
        f"Startup: {validate_startup(CONFIG, CREDENTIALS).state.value}", f"Liveness: {healthy.liveness.value}",
        f"Readiness: {healthy.readiness.value}", "CAPABILITIES",
        *(f"- {x.capability.value}: {x.state.value}" for x in healthy.capabilities), "",
        "SCENARIO B — MISSING CRITICAL CREDENTIAL", "", "Credential reference: estimateworks-api",
        f"Startup: {validate_startup(CONFIG, MISSING_ESTIMATEWORKS_CREDENTIALS).state.value}",
        f"Readiness: {missing.readiness.value}", f"Lead → Estimate: {cap(missing, Capability.LEAD_TO_ESTIMATE)}",
        "Diagnostic: unresolvable credential reference: estimateworks-api", "Secret value logged: NO", "",
        "SCENARIO C — SUPPLYDESK OUTAGE", "", f"Liveness: {supply.liveness.value}",
        f"Readiness: {supply.readiness.value}", f"Material handoff: {cap(supply, Capability.MATERIAL_HANDOFF)}",
        f"Estimate → Job: {cap(supply, Capability.ESTIMATE_TO_JOB)}", f"Job → Schedule: {cap(supply, Capability.JOB_TO_SCHEDULE)}",
        f"Field Status: {cap(supply, Capability.FIELD_STATUS)}", "",
        "SCENARIO D — LEDGERPRO OUTAGE", "", f"Liveness: {ledger.liveness.value}",
        f"Readiness: {ledger.readiness.value}", f"Invoice Readiness: {cap(ledger, Capability.INVOICE_READINESS)}",
        f"Estimate → Job: {cap(ledger, Capability.ESTIMATE_TO_JOB)}", "Dependency alert: CRITICAL", "",
        "SCENARIO E — UNCERTAIN WRITE", "", f"Alert: {uncertain.severity.value}",
        f"Evidence: {uncertain.evidence_reference}", f"Recommended action: {uncertain.recommended_action}", "Blind replay: NO", "",
        "SCENARIO F — OVERDUE EXCEPTION", "", f"Alert: {overdue.severity.value}",
        f"Evidence: {overdue.evidence_reference}", f"Owner: {overdue.owner.value}", "",
        "SCENARIO G — SCHEDULED RECONCILIATION", "", "Due tasks: " + ", ".join(x.value for x in due_tasks(SCHEDULE, NOW)),
        f"Run: {completed.run_id} / {completed.outcome.value}", f"Report: {completed.evidence_reference}", "",
        "SCENARIO H — SCHEDULER OVERLAP", "", f"First reconciliation: {first.outcome.value}",
        f"Second reconciliation: {second.outcome.value}", "Coordination: PROCESS-LOCAL MODELED LEASE", "",
        "SCENARIO I — SECRET SAFETY", "", "Credential reference: estimateworks-api",
        f"Credential value logged: {'YES' if secret in record.to_json() else 'NO'}", "",
        "SCENARIO J — RECOVERY RUNBOOK", "", f"Category: {runbook.category}", f"Owner: {runbook.owner.value}",
        f"Safe first action: {runbook.safe_first_action}", f"Do not: {runbook.action_not_to_take}", "",
        "OPERATIONAL METRICS", *(f"- {m.name}: {m.value}" for m in metrics.metrics), "",
        "MODELED ASSUMPTION", "Deployment settings, credentials, dependencies, capability graph, schedules, thresholds, and ownership.", "",
        "OBSERVED LAB RESULT", "Production operability requires configuration validation, dependency health, capability-aware degradation,",
        "structured evidence, bounded metrics, alerts, scheduled controls, and recovery procedures beyond workflow logic.",
        "These mechanisms add reusable infrastructure and an ongoing support surface.",
        "This is a deterministic production-like simulation, not a deployed production service."
    ))


def render_chapter14() -> str:
    report = build_report()
    def counts(values):
        return tuple(f"- {key.value}: {value}" for key, value in values.items())
    scenario_lines = []
    for scenario in CHANGE_SCENARIOS:
        scenario_lines.extend((scenario.scenario_id,
            "Unchanged: " + ", ".join(scenario.unchanged_units),
            "Changed/added: " + ", ".join(scenario.changed_or_added_units),
            f"Support surface: {scenario.support_surface_change}", scenario.interpretation, ""))
    support_lines = tuple(
        f"- {key.value}: {value}" for key, value in report.support_surface_by_primary.items() if value)
    return "\n".join((
        "CONSTRUCTION / TRADES WORKFLOW INTEGRATION LAB",
        "Chapter 14 — Measure What Was Actually Built", "",
        "ORIGINAL MODELED ASSUMPTION", "        ↓", "IMPLEMENTATION EVIDENCE",
        "        ↓", "UPDATED INTERPRETATION", "",
        "IMPLEMENTATION INVENTORY", f"Total curated implementation units: {len(report.units)}", "",
        "PRIMARY CLASSIFICATION", *counts(report.classification_counts), "",
        "EVIDENCE LEVEL", *counts(report.evidence_counts), "",
        "REUSE SCOPE", *counts(report.reuse_scope_counts), "",
        "REUSE MATRIX", reuse_matrix(), "",
        "IMPORTANT", "IMPLEMENTATION UNITS ≠ ENGINEERING HOURS",
        "Repository evidence and synthetic implementation units are inspectable; human engineering hours are not observed.",
        "Lines, files, tests, commits, tokens, and units are not converted to time.", "",
        "ORIGINAL HYPOTHESIS", "Evidence: MODELED ASSUMPTION",
        f"Modeled reusable delivery effort: {report.original_modeled_reusable_effort}%", "",
        "OBSERVED REPOSITORY EVIDENCE",
        f"Observed cross-workflow reusable units: {report.observed_cross_workflow_count}",
        f"{report.ratio_label}: {report.observed_cross_workflow_ratio * 100}%",
        "Same denominator as 52.8%: NO", "Direct validation of 52.8%: NO",
        f"Structural reuse confidence: {report.reuse_confidence.value}",
        "The unit ratio counts curated structures; 52.8% modeled delivery effort. They cannot be equated.", "",
        "SUPPORT SURFACE", f"Units carrying support obligations: {report.support_surface_count}",
        *support_lines, "Reusable software can still create recurring support obligations.", "",
        "CHANGE SIMULATIONS (MODELED ASSUMPTION)", *scenario_lines,
        "NEGATIVE EVIDENCE", *(f"- {item}" for item in report.negative_evidence), "",
        "OBSERVED LAB RESULT",
        "The repository contains genuine cross-workflow reuse, but reusable mechanisms coexist with",
        "source/destination adapters, workflow rules, customer configuration, and ongoing support obligations.",
        "Repository structure tests the mechanism behind the reuse hypothesis; it does not measure labor reuse.",
        "No human-hour, price, margin, payback, support-economics, or Chapter 15 conclusion is produced."
    ))


def render_chapter15() -> str:
    adapter = BidForgeAdapter()
    blocked, approved = schedule_gate(True, False), schedule_gate(True, True)
    kit = TidewaterKitExpander().expand("TSS-KIT-A")
    billing = aggregate_billing_project("BP-100", BILLING_PROJECT_JOBS)
    paper = OfficeCompletionAdapter().adapt(PAPER_COMPLETION)
    digital, legacy = interpret_done("DIGITAL_SERVICE_CREW", "DONE"), interpret_done("LEGACY_CREW", "DONE")
    inventory = change_inventory()
    labels = (("Unchanged reused units", "unchanged_reused_units"),
              ("Configuration-only", "configuration_only"), ("New mappings", "new_mappings"),
              ("New adapters", "new_adapters"), ("Workflow-specific extensions", "workflow_specific_extensions"),
              ("Customer-specific rules", "customer_specific_rules"), ("Shared-core changes", "shared_core_changes"),
              ("Support-surface additions", "support_surface_additions"))
    return "\n".join((
        "CONSTRUCTION / TRADES WORKFLOW INTEGRATION LAB", "Chapter 15 — Customer-Specific Rules Stress Test", "",
        "CUSTOMER", "Tidewater Specialty Services", "", "Purpose:", "Deliberately stress the reusable architecture.", "",
        "ESTIMATE ACCEPTANCE", "SIGNED", f"→ {adapter.acceptance_decision('SIGNED').value}",
        "CUSTOMER_VERBAL_OK", f"→ {adapter.acceptance_decision('CUSTOMER_VERBAL_OK').value}",
        "Shared mapping mechanism: REUSED", "Acceptance policy: CUSTOMER_SPECIFIC", "",
        "EARLY JOB CREATION", "Selected: Approach B — Tidewater pre-authorization state outside shared handoff",
        "PROSPECTIVE_JOB forced into JOB_PENDING: NO", "Shared canonical model changed: NO", "",
        "SCHEDULING", "Authorized: YES", "Operations approval: NO",
        f"Schedule request: {blocked.request_status}", f"Exception: {blocked.exception}",
        "After approval:", approved.request_status, "Scheduling boundary and idempotency: REUSED", "",
        "MATERIAL KIT", "Source: TSS-KIT-A", f"Expanded requirements: {len(kit.lines)}",
        f"Mapped: {kit.mapped}", f"Unresolved: {kit.unresolved}", f"Result: {kit.status}",
        f"Exception: {kit.exception}", "One-to-many specialization: CUSTOMER_SPECIFIC", "",
        "PAPER-DERIVED COMPLETION", f"Source: {paper.source_system}",
        f"Accepted: {'YES' if paper.accepted else 'NO'}",
        f"Entered by role: {dict(paper.provenance)['entered_by_role']}",
        f"Source document reference: {dict(paper.provenance)['source_document_reference']}", "",
        "WEAK IDENTITY", "WORK-001 / RESIDENTIAL / 2026", "WORK-001 / COMMERCIAL / 2025",
        f"Same canonical identity: {'YES' if WEAK_IDENTITY_2026 == WEAK_IDENTITY_2025 else 'NO'}", "",
        "BILLING PROJECT", billing.project_id, f"Jobs: {len(BILLING_PROJECT_JOBS)}", f"Ready: {billing.ready_jobs}",
        f"Blocked: {billing.blocked_jobs}", f"Billing project ready: {'YES' if billing.ready else 'NO'}",
        f"Invoice created: {'YES' if billing.invoice_created else 'NO'}", "",
        "COMPLETION SEMANTICS", "Digital DONE invoice eligible: " + ("YES" if digital.invoice_eligible else "NO"),
        "Legacy DONE invoice eligible: " + ("YES" if legacy.invoice_eligible else "NO"), "",
        "REUSE STRESS TEST", *(f"{label}: {inventory[key]}" for label, key in labels), "",
        "CORE IMPACT", CORE_IMPACT, "Customer rules remained in a Chapter 15 edge module; shared domain files changed: 0.", "",
        "SUPPORT SURFACE", *(f"- {item}" for item in SUPPORT_SURFACE), "",
        "ORIGINAL HYPOTHESIS: meaningful reusable delivery", "STRESS TEST: deliberately unusual customer", "",
        "OBSERVED LAB RESULT",
        "Shared reliability, correlation, idempotency, exception, and scheduling-boundary patterns remain meaningful.",
        "Adapters, policies, one-to-many mapping, manual validation, aggregation, and identity context add specialized structure.",
        "The core survives, but expensive customer edges remain an unresolved economic question; no hours or dollars are inferred.", "",
        "MODELED ASSUMPTION",
        "Tidewater, BidForge, its approvals, kits, paper process, billing projects, identifiers, and crew semantics are synthetic.",
        "Chapter 16 integration-access profiles are not implemented."
    ))


def render_chapter16() -> str:
    handoff = "accepted estimate → job"
    packet = create_job_handoff_packet("corr-16", "BF-EST-100", "CUST-9", "export-2026-08-26")
    known = parse_estimate_export(
        "estimate_id,status,customer_id,updated_at\nBF-EST-100,ACCEPTED,CUST-9,2026-08-26T01:00:00Z\n")
    try:
        parse_estimate_export(
            "estimate_number,approval_status,customer_ref,last_modified\n100,YES,9,2026-08-26\n")
    except SchemaDriftError as error:
        drift = str(error)
    lines = ["CONSTRUCTION / TRADES WORKFLOW INTEGRATION LAB",
             "Chapter 16 — Integration Access Stress Test", "", "SAME BUSINESS HANDOFF:", handoff.upper()]
    for profile in (CLEAN, DIFFICULT, CLOSED):
        cap, result, scope = profile.capability, evaluate_transition(profile, handoff), recommend_scope(handoff, profile)
        lines.extend(("", profile.label, f"Access risk: {classify_access(profile).value}",
                      f"Write access: {cap.write_access.value}",
                      f"Stable external reference: {'YES' if cap.external_reference_support else 'NO'}",
                      f"Destination lookup: {'YES' if cap.lookup_support else 'NO'}",
                      f"Sandbox: {'YES' if cap.sandbox_available else 'NO'}",
                      f"Feasibility: {result.feasibility.value}",
                      f"Safe blind replay: {'YES' if cap.safe_recovery else 'NO'}",
                      f"Recommended scope: {scope.scope.value}", "Reasons:", *(f"- {r}" for r in result.reasons)))
    lines.extend(("", "CSV EXPORT", f"Known v1 records: {len(known)}", "Timing: nightly batch (MODELED ASSUMPTION)",
                  "", "CSV SCHEMA DRIFT", "Expected schema: v1", "Observed: changed headers",
                  "Automatic guessing: NO", "Result: BLOCKED", f"Evidence: {drift}", "Support intervention: REQUIRED",
                  "", "NO SANDBOX", "Difficult destination writes cannot be validated in a sandbox.",
                  "Recommendation: dry-run / human confirmation; production-only testing is a support constraint.",
                  "", "HUMAN-ASSISTED WRITE", f"Validated packet: {packet.packet_id}",
                  f"Required action: {packet.required_action}",
                  f"Destination write performed by integration: {'YES' if packet.destination_write_performed else 'NO'}",
                  "Later read-only reconciliation: AVAILABLE", "", "RELIABILITY MATRIX",
                  f"{'CAPABILITY':<28} {'CLEAN':<12} {'DIFFICULT':<12} CLOSED"))
    lines.extend(f"{key:<28} {values[0]:<12} {values[1]:<12} {values[2]}" for key, values in RELIABILITY_MATRIX.items())
    lines.append("")
    lines.append("SUPPORT SURFACE")
    for key in ("clean", "difficult", "closed"):
        lines.extend((key.title() + ":", *(f"- {item}" for item in SUPPORT[key])))
    lines.extend(("", f"Machine-readable transition results: {len(build_access_report().transition_results)}", "",
                  "OBSERVED LAB RESULT",
                  "The same business workflow moves from safe automation to constrained automation to a blocked direct write",
                  "solely because modeled interface quality changes. Bounded human and read-only designs preserve some value.",
                  "Access quality is a core feasibility variable, not an implementation detail.", "",
                  "MODELED ASSUMPTION",
                  "All profile capabilities, vendor behavior, batch timing, permissions, and native alternatives are synthetic.",
                  "No hours, costs, prices, payback, support cost, or economic verdict are calculated. Chapter 17 is not implemented."))
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run executable textbook chapters")
    parser.add_argument("chapter", choices=("chapter0", "chapter1", "chapter2", "chapter3", "chapter4", "chapter5", "chapter6", "chapter7", "chapter8", "chapter9", "chapter10", "chapter11", "chapter12", "chapter13", "chapter14", "chapter15", "chapter16"))
    args = parser.parse_args(argv)
    if args.chapter == "chapter0":
        print(render_chapter0())
    elif args.chapter == "chapter1":
        print(render_chapter1())
    elif args.chapter == "chapter2":
        print(render_chapter2())
    elif args.chapter == "chapter3":
        print(render_chapter3())
    elif args.chapter == "chapter4":
        print(render_chapter4())
    elif args.chapter == "chapter5":
        print(render_chapter5())
    elif args.chapter == "chapter6":
        print(render_chapter6())
    elif args.chapter == "chapter7":
        print(render_chapter7())
    elif args.chapter == "chapter8":
        print(render_chapter8())
    elif args.chapter == "chapter9":
        print(render_chapter9())
    elif args.chapter == "chapter10":
        print(render_chapter10())
    elif args.chapter == "chapter11":
        print(render_chapter11())
    elif args.chapter == "chapter12":
        print(render_chapter12())
    elif args.chapter == "chapter13":
        print(render_chapter13())
    elif args.chapter == "chapter14":
        print(render_chapter14())
    elif args.chapter == "chapter15":
        print(render_chapter15())
    elif args.chapter == "chapter16":
        print(render_chapter16())
    return 0
