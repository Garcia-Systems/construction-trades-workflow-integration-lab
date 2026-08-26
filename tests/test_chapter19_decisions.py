from dataclasses import fields

from trades_lab.chapter19 import (ALTERNATIVES, DECISIONS, EvidenceStatus, SCENARIOS,
                                  SolutionDecision, SolutionStrategy, build_decisions,
                                  decision_matrix)


def test_all_strategies_and_determinism_without_numeric_total_score():
    assert {item.strategy for item in ALTERNATIVES} == set(SolutionStrategy)
    assert build_decisions() == build_decisions()
    assert "score" not in {field.name for field in fields(SolutionDecision)}
    assert decision_matrix() == decision_matrix()


def test_expected_scenario_recommendations_are_rule_derived():
    recommendations = {item.scenario_id: item.recommended_strategy for item in DECISIONS}
    assert recommendations == {
        "A": SolutionStrategy.PLATFORM_REPLACEMENT,
        "B": SolutionStrategy.NATIVE_INTEGRATION,
        "C": SolutionStrategy.LOW_CODE_INTEGRATION,
        "D": SolutionStrategy.NARROW_CUSTOM_EDGE,
        "E": SolutionStrategy.CUSTOM_INTEGRATION_LAYER,
        "F": SolutionStrategy.PROCESS_CHANGE,
        "G": SolutionStrategy.NARROW_CUSTOM_EDGE,
        "H": SolutionStrategy.DO_NOTHING,
    }


def test_disqualified_custom_cannot_win_and_feasible_custom_can_lose():
    closed = next(item for item in DECISIONS if item.scenario_id == "G")
    custom = next(item for item in closed.considered_alternatives
                  if item.strategy is SolutionStrategy.CUSTOM_INTEGRATION_LAYER)
    assert custom.disqualifiers
    assert closed.recommended_strategy is not custom.strategy
    feasible_losers = {scenario.scenario_id for scenario in SCENARIOS
                       if scenario.custom_technically_feasible}
    assert feasible_losers
    assert all(next(item for item in DECISIONS if item.scenario_id == scenario_id).recommended_strategy
               is not SolutionStrategy.CUSTOM_INTEGRATION_LAYER for scenario_id in feasible_losers)


def test_custom_evidence_includes_delivery_and_support_structure():
    custom = next(item for item in ALTERNATIVES
                  if item.strategy is SolutionStrategy.CUSTOM_INTEGRATION_LAYER)
    statements = " ".join(item.statement for item in custom.assumptions)
    assert "Chapter 17" in statements
    assert "Chapter 18" in statements
    assert "credential" in statements and "reconciliation" in statements
    assert all(item.status is EvidenceStatus.OBSERVED_LAB_EVIDENCE for item in custom.assumptions)


def test_fictional_capabilities_are_labeled_and_discovery_remains_open():
    for alternative in ALTERNATIVES:
        if alternative.alternative_id in {"contractor-suite", "flow-bridge", "vendor-connect"}:
            assert all(item.status is EvidenceStatus.MODELED_ALTERNATIVE_ASSUMPTION
                       for item in alternative.assumptions)
    assert all(decision.unresolved_questions for decision in DECISIONS)
    assert all(decision.final_opportunity_verdict is None for decision in DECISIONS)
