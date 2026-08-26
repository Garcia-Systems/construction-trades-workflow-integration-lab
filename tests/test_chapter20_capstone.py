from decimal import Decimal
from trades_lab.chapter20 import (DiscoveryAnswers, DiscoveryGateResult, EvidenceDirection,
    FinalVerdict, QualitativeRating, build_report, build_scorecard, discovery_gate)
from trades_lab.evidence import EvidenceCategory


def ideal_answers(**changes):
    values = dict(systems=5, repeated_handoffs=True, measurable_burden=True, meaningful_burden=True,
        supported_access=True, consequential_writes_reconcilable=True, stable_identity=True,
        mostly_configurable_rules=True, native_or_suite_covers_most=False, bounded_gap_remains=True,
        exception_owner=True, support_economics_fit=True, price_and_payback_tolerable=True)
    values.update(changes)
    return DiscoveryAnswers(**values)


def test_original_hypothesis_is_preserved_as_modeled():
    h = build_report().original_hypothesis
    assert h.evidence_category is EvidenceCategory.MODELED_ASSUMPTION
    assert (h.annual_current_state_burden, h.annual_recoverable_value) == (Decimal("130584.22"), Decimal("64619.29"))
    assert (h.implementation_price, h.annual_recurring_fee) == (Decimal("50000.00"), Decimal("12000.00"))
    assert (h.modeled_engineering_hours, h.reusable_core_percentage) == (466, Decimal("52.8"))


def test_inventory_has_all_directions_and_distinct_categories():
    evidence = build_report().evidence
    assert {EvidenceDirection.SUPPORTS_OPPORTUNITY, EvidenceDirection.WEAKENS_OPPORTUNITY,
            EvidenceDirection.QUALIFIES_OPPORTUNITY} <= {x.direction for x in evidence}
    assert {EvidenceCategory.MODELED_ASSUMPTION, EvidenceCategory.OBSERVED_LAB_RESULT,
            EvidenceCategory.OBSERVED_IMPLEMENTATION_STRUCTURE, EvidenceCategory.SENSITIVITY_ASSUMPTION,
            EvidenceCategory.FICTIONAL_ALTERNATIVE_ASSUMPTION} <= {x.category for x in evidence}


def test_scorecard_is_deterministic_and_qualitative():
    assert build_scorecard() == build_scorecard()
    assert all(isinstance(item.rating, QualitativeRating) for item in build_scorecard())
    assert not hasattr(build_report(), "numeric_score")


def test_scenario_verdicts_apply_disqualifiers_and_prior_chapters():
    by_id = {x.scenario_id: x for x in build_report().scenario_verdicts}
    assert by_id["A"].verdict is FinalVerdict.REPEATABLE_PROJECT
    assert by_id["B"].verdict is FinalVerdict.CONFIGURE_OR_BUY
    assert by_id["C"].verdict is FinalVerdict.NARROW_CUSTOM_EDGE
    assert by_id["D"].verdict is FinalVerdict.VALIDATE_IN_DISCOVERY
    assert by_id["E"].verdict is FinalVerdict.BESPOKE_PROJECT and "C20-BESPOKE" in by_id["E"].evidence_ids
    assert by_id["F"].verdict is FinalVerdict.VALIDATE_IN_DISCOVERY and "C20-ACCESS-DIFFICULT" in by_id["F"].evidence_ids
    assert by_id["G"].verdict not in {FinalVerdict.PRODUCT_CANDIDATE, FinalVerdict.REPEATABLE_PROJECT, FinalVerdict.BESPOKE_PROJECT}
    assert by_id["H"].verdict is FinalVerdict.NO_DEAL


def test_report_reuses_chapters_17_18_19_and_does_not_call_code_a_product():
    report = build_report()
    assert report.delivery_economics_source.original_model.total_hours == Decimal("466")
    assert report.support_economics_source.annual_recurring_fee == Decimal("12000")
    assert len(report.alternatives_source) == 8
    assert report.structural_opportunity_class is FinalVerdict.REPEATABLE_PROJECT
    assert report.current_commercial_readiness is FinalVerdict.VALIDATE_IN_DISCOVERY
    assert all(v.verdict is not FinalVerdict.PRODUCT_CANDIDATE for v in report.scenario_verdicts)


def test_discovery_gate_is_deterministic_and_material():
    answers = ideal_answers()
    assert discovery_gate(answers) == discovery_gate(answers) == DiscoveryGateResult.QUALIFIED_FOR_TECHNICAL_DISCOVERY
    assert discovery_gate(ideal_answers(meaningful_burden=False)) is DiscoveryGateResult.NOT_QUALIFIED
    assert discovery_gate(ideal_answers(supported_access=False)) is DiscoveryGateResult.NARROW_SCOPE
    assert discovery_gate(ideal_answers(native_or_suite_covers_most=True, bounded_gap_remains=False)) is DiscoveryGateResult.INVESTIGATE_ALTERNATIVES
    assert discovery_gate(DiscoveryAnswers()) is DiscoveryGateResult.INSUFFICIENT_INFORMATION


def test_real_customer_unknowns_remain_explicit():
    unknowns = build_report().critical_unknowns
    assert "actual customer burden" in unknowns and "actual implementation hours" in unknowns
    assert "actual vendor API access" in unknowns and "actual native integration coverage" in unknowns
