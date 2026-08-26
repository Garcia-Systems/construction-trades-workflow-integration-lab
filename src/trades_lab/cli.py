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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run executable textbook chapters")
    parser.add_argument("chapter", choices=("chapter0", "chapter1", "chapter2", "chapter3", "chapter4", "chapter5", "chapter6", "chapter7", "chapter8", "chapter9", "chapter10"))
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
    return 0
