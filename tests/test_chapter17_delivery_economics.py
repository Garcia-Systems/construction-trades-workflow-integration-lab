from dataclasses import replace
from decimal import Decimal

from trades_lab.chapter14 import build_report as implementation_report
from trades_lab.chapter17 import (DeliveryCategory, DeliveryVerdict, EvidenceCategory,
    REPORT, SCENARIOS)


def test_original_model_is_untouched_and_inspectable():
    model = REPORT.original_model
    assert model.total_hours == Decimal("466")
    assert model.reusable_labor_percentage == Decimal("52.8")
    assert model.implementation_price == Decimal("50000.00")
    assert model.annual_recurring_fee == Decimal("12000.00")
    assert model.evidence_category is EvidenceCategory.MODELED_ASSUMPTION
    assert set(model.category_hours) == set(DeliveryCategory)


def test_structure_is_qualitative_and_deterministic():
    assert len(REPORT.evidence_categories) == len(DeliveryCategory)
    assert tuple(REPORT.evidence_categories) == tuple(REPORT.evidence_categories)
    for item in REPORT.evidence_categories:
        assert item.evidence_category is EvidenceCategory.OBSERVED_IMPLEMENTATION_STRUCTURE
        assert item.evidence_references and item.observed_structure_summary
        # Only the original modeled number is carried beside structural evidence.
        assert item.original_modeled_hours == REPORT.original_model.category_hours[item.category]


def test_every_sensitivity_is_explicit_and_sums_categories():
    for scenario in SCENARIOS:
        assert scenario.evidence_category is EvidenceCategory.SENSITIVITY_ASSUMPTION
        assert scenario.cost_assumption.evidence_category is EvidenceCategory.SENSITIVITY_ASSUMPTION
        assert set(scenario.category_hours) == set(DeliveryCategory)
        assert scenario.total_modeled_hours == sum(scenario.category_hours.values(), Decimal("0"))


def test_cost_contribution_and_margin_are_deterministic_and_safe():
    scenario = SCENARIOS[1]
    assert scenario.delivery_labor_cost == Decimal("33600")
    assert scenario.modeled_contribution == Decimal("16400.00")
    assert scenario.modeled_break_even_implementation_price == Decimal("33600")
    assert scenario.contribution_margin == Decimal("0.328")
    assert replace(scenario, implementation_price=Decimal("0")).contribution_margin is None
    assert SCENARIOS[3].modeled_contribution < 0


def test_structural_ratio_is_not_used_as_labor_reuse():
    structural = implementation_report().observed_cross_workflow_ratio
    assert structural != SCENARIOS[1].reusable_labor_percentage
    assert "implementation-unit" in implementation_report().ratio_label
    assert "not a labor reuse percentage" in REPORT.conclusions[2]


def test_customer_and_access_scenarios_preserve_caveats():
    baseline, standardized, mixed, bespoke, difficult, closed = SCENARIOS
    assert baseline.total_modeled_hours == Decimal("466")
    assert standardized.customer_specific_labor_percentage > 0
    assert standardized.total_modeled_hours > 0
    assert bespoke.customer_specific_labor_percentage > mixed.customer_specific_labor_percentage
    assert bespoke.category_hours[DeliveryCategory.ORCHESTRATION] > baseline.category_hours[DeliveryCategory.ORCHESTRATION]
    assert difficult.category_hours[DeliveryCategory.API_VALIDATION] > baseline.category_hours[DeliveryCategory.API_VALIDATION]
    assert difficult.automation_scope == "REDUCED"
    assert closed.total_modeled_hours < difficult.total_modeled_hours
    assert "not equal customer value" in closed.value_caveat
    assert closed.verdict is DeliveryVerdict.SCOPE_REDESIGN_REQUIRED


def test_no_final_commercial_verdict_or_observed_revised_hours():
    assert REPORT.final_commercial_verdict is None
    assert all(s.evidence_category is not EvidenceCategory.OBSERVED_IMPLEMENTATION_STRUCTURE for s in SCENARIOS)

