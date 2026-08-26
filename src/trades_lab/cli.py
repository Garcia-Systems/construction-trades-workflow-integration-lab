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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run executable textbook chapters")
    parser.add_argument("chapter", choices=("chapter0", "chapter1", "chapter2", "chapter3", "chapter4", "chapter5"))
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
    return 0
