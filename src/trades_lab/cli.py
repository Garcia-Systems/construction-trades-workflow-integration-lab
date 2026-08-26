"""Small command-line entry point for executable chapters."""

import argparse
from decimal import Decimal

from trades_lab.chapter0 import BASELINE_HYPOTHESIS
from trades_lab.chapter1 import QUESTIONS, SYSTEMS, TRANSITIONS, QuestionStatus, baseline_readiness
from trades_lab.domain.states import (EstimateState, JobState, map_estimateworks_state,
                                      map_fieldtrack_state)
from trades_lab.domain.transitions import can_transition, validate_transition, TransitionError
from trades_lab.fixtures.chapter2 import CUSTOMER, WORKFLOW_SNAPSHOT


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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run executable textbook chapters")
    parser.add_argument("chapter", choices=("chapter0", "chapter1", "chapter2"))
    args = parser.parse_args(argv)
    if args.chapter == "chapter0":
        print(render_chapter0())
    elif args.chapter == "chapter1":
        print(render_chapter1())
    elif args.chapter == "chapter2":
        print(render_chapter2())
    return 0
