from dataclasses import replace

import pytest

from trades_lab.chapter1 import (
    AUTHORITY_MATRIX, CORE_CONCEPTS, QUESTIONS, SYSTEMS, TRANSITIONS,
    ApprovalKnowledge, AuthorityRole, Capability, DiscoveryValidationError,
    NativeIntegrationStatus, QuestionStatus, Readiness, TransitionRisk,
    baseline_readiness, evaluate_readiness, validate_authority,
)
from trades_lab.cli import render_chapter1


def transition(key):
    return next(item for item in TRANSITIONS if item.key == key)


def test_required_fictional_systems_exist():
    assert {system.name for system in SYSTEMS} == {"RiverLead CRM", "EstimateWorks", "CrewBoard", "FieldTrack", "SupplyDesk", "LedgerPro"}


def test_required_authority_is_unambiguous_and_integration_is_not_business_authority():
    validate_authority()
    for concept in CORE_CONCEPTS:
        roles = AUTHORITY_MATRIX[concept]
        assert sum(role is AuthorityRole.AUTHORITATIVE for role in roles.values()) == 1
        assert roles["Integration Layer"] is not AuthorityRole.AUTHORITATIVE
    assert AUTHORITY_MATRIX["job existence"]["CrewBoard"] is AuthorityRole.AUTHORITATIVE


def test_multiple_authoritative_owners_are_rejected():
    matrix = {concept: dict(roles) for concept, roles in AUTHORITY_MATRIX.items()}
    matrix["lead status"]["CrewBoard"] = AuthorityRole.AUTHORITATIVE
    with pytest.raises(DiscoveryValidationError, match="multiple authoritative owners"):
        validate_authority(matrix)


def test_missing_authority_is_detected():
    matrix = {concept: dict(roles) for concept, roles in AUTHORITY_MATRIX.items()}
    matrix["payment state"] = {name: AuthorityRole.NOT_APPLICABLE for name in matrix["payment state"]}
    with pytest.raises(DiscoveryValidationError, match="missing authoritative owner"):
        validate_authority(matrix)


def test_blocking_question_blocks_affected_transition():
    result = evaluate_readiness(transition("accepted_estimate_to_job"))
    assert result.status is Readiness.BLOCKED
    assert any("Blocks accepted estimate" in reason for reason in result.reasons)


def test_consequential_write_requires_permission_and_approval_knowledge():
    item = transition("job_to_schedule")
    crewboard = next(system for system in SYSTEMS if system.name == "CrewBoard")
    systems = {system.name: system for system in SYSTEMS}
    systems["CrewBoard"] = replace(crewboard, write_capability=Capability.LIMITED, write_approval=ApprovalKnowledge.UNKNOWN)
    result = evaluate_readiness(item, systems=systems)
    assert result.status is Readiness.BLOCKED
    assert "write approval requirements are unknown" in result.reasons
    assert "consequential destination write permission is not established" in result.reasons


def test_baseline_contains_blocked_and_nonblocked_lower_risk_transition():
    results = {result.transition: result for result in baseline_readiness()}
    assert results["accepted_estimate_to_job"].status is Readiness.BLOCKED
    assert results["lead_to_estimate"].status is Readiness.READY_WITH_CONSTRAINTS
    assert transition("lead_to_estimate").risk is TransitionRisk.LOW_RISK


def test_readiness_and_cli_are_deterministic():
    assert baseline_readiness() == baseline_readiness()
    assert render_chapter1() == render_chapter1()


def test_native_integration_status_is_explicit_for_every_transition():
    assert all(isinstance(item.native_integration, NativeIntegrationStatus) for item in TRANSITIONS)
    assert all(item.native_integration is not NativeIntegrationStatus.UNKNOWN for item in TRANSITIONS)


def test_discovery_questions_are_first_class_and_include_open_blockers():
    assert {question.status for question in QUESTIONS} >= {QuestionStatus.OPEN, QuestionStatus.ANSWERED, QuestionStatus.BLOCKING}
    assert "OPEN BLOCKERS" in render_chapter1()


def test_unknown_destination_interface_blocks_write_handoff():
    item = transition("job_to_schedule")
    crewboard = next(system for system in SYSTEMS if system.name == "CrewBoard")
    systems = {system.name: system for system in SYSTEMS}
    systems["CrewBoard"] = replace(crewboard, interface_types=("UNKNOWN",))
    result = evaluate_readiness(item, systems=systems)
    assert result.status is Readiness.BLOCKED
    assert "destination integration interface is unresolved" in result.reasons
