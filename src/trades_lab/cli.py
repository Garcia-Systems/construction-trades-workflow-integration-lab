"""Small command-line entry point for executable chapters."""

import argparse
from decimal import Decimal

from trades_lab.chapter0 import BASELINE_HYPOTHESIS
from trades_lab.chapter1 import QUESTIONS, SYSTEMS, TRANSITIONS, QuestionStatus, baseline_readiness
from trades_lab.chapter3 import LeadToEstimateHandoff
from trades_lab.domain.states import (EstimateState, JobState, map_estimateworks_state,
                                      map_fieldtrack_state)
from trades_lab.domain.transitions import can_transition, validate_transition, TransitionError
from trades_lab.fixtures.chapter2 import CUSTOMER, WORKFLOW_SNAPSHOT
from trades_lab.fixtures.chapter3 import (AMBIGUOUS_IDENTITY_LEAD, INELIGIBLE_LEAD,
                                          MISSING_CONTACT_LEAD, UNKNOWN_STATE_LEAD,
                                          VALID_QUALIFIED_LEAD)


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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run executable textbook chapters")
    parser.add_argument("chapter", choices=("chapter0", "chapter1", "chapter2", "chapter3"))
    args = parser.parse_args(argv)
    if args.chapter == "chapter0":
        print(render_chapter0())
    elif args.chapter == "chapter1":
        print(render_chapter1())
    elif args.chapter == "chapter2":
        print(render_chapter2())
    elif args.chapter == "chapter3":
        print(render_chapter3())
    return 0
