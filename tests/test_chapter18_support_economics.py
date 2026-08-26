from dataclasses import replace
from decimal import Decimal

from trades_lab.chapter18 import (REPORT, SCENARIOS, SupportCategory, SupportPredictability,
                                  SupportScope, SupportVerdict)
from trades_lab.evidence import EvidenceCategory


def test_original_recurring_hypothesis_is_preserved_and_labeled():
    assert REPORT.annual_recurring_fee == Decimal("12000.00")
    assert REPORT.recurring_fee_evidence_category is EvidenceCategory.MODELED_ASSUMPTION
    assert REPORT.original_support_contribution == "sustainable but thin"


def test_obligation_inventory_is_observed_structure_with_prior_chapter_evidence():
    assert set(item.category for item in REPORT.obligations) == set(SupportCategory)
    assert all(item.evidence_category is EvidenceCategory.OBSERVED_IMPLEMENTATION_STRUCTURE
               for item in REPORT.obligations)
    references = " ".join(ref for item in REPORT.obligations for ref in item.evidence_references)
    for chapter in ("Chapter 6", "Chapter 9", "Chapter 10", "Chapter 11", "Chapter 13", "Chapter 15", "Chapter 16"):
        assert chapter in references


def test_hours_come_only_from_explicit_sensitivity_events():
    for scenario in SCENARIOS:
        assert scenario.evidence_category is EvidenceCategory.SENSITIVITY_ASSUMPTION
        assert scenario.cost_assumption.evidence_category is EvidenceCategory.SENSITIVITY_ASSUMPTION
        assert all(event.evidence_category is EvidenceCategory.SENSITIVITY_ASSUMPTION
                   for event in scenario.event_assumptions)
        assert scenario.assumed_annual_support_hours == sum(
            (event.annual_events * event.average_hours_per_event for event in scenario.event_assumptions), Decimal("0"))


def test_cost_contribution_break_even_capacity_and_margin_are_deterministic():
    standardized, mixed, bespoke = SCENARIOS
    assert standardized.assumed_annual_support_hours == Decimal("40")
    assert standardized.support_labor_cost == Decimal("4000")
    assert standardized.support_contribution == Decimal("8000.00")
    assert standardized.break_even_recurring_fee == Decimal("4000")
    assert standardized.hours_supported_before_fee_is_consumed == Decimal("120.00")
    assert standardized.contribution_margin == Decimal("0.6666666666666666666666666667")
    assert mixed.assumed_annual_support_hours == Decimal("100.0")
    assert mixed.support_contribution == Decimal("2000.00")
    assert bespoke.assumed_annual_support_hours == Decimal("150")
    assert bespoke.support_contribution == Decimal("-3000.00")
    assert replace(standardized, recurring_fee=Decimal("0")).contribution_margin is None


def test_standardized_still_has_work_and_bespoke_has_larger_surface():
    standardized, _, bespoke = SCENARIOS
    assert standardized.assumed_annual_support_hours > 0
    assert len(bespoke.event_assumptions) > len(standardized.event_assumptions)
    assert bespoke.assumed_annual_support_hours > standardized.assumed_annual_support_hours


def test_scope_boundary_does_not_absorb_new_projects():
    scopes = {item.name: item.scope for item in REPORT.scope_examples}
    assert scopes["Expired credential"] is SupportScope.INCLUDED_SUPPORT
    assert scopes["New material mapping"] is SupportScope.INCLUDED_SUPPORT
    assert scopes["Retry exhaustion"] is SupportScope.INCLUDED_SUPPORT
    assert scopes["Reconciliation mismatch"] is SupportScope.INCLUDED_SUPPORT
    assert scopes["New source system"] is SupportScope.CHANGE_REQUEST
    assert scopes["Customer adds a new approval workflow"] is SupportScope.CHANGE_REQUEST
    assert scopes["Vendor replaces API with an incompatible version"] in {
        SupportScope.CHANGE_REQUEST, SupportScope.COMMERCIAL_REVIEW}


def test_predictability_and_verdicts_are_rule_based():
    standardized, mixed, bespoke = SCENARIOS
    assert standardized.predictability is SupportPredictability.PREDICTABLE
    assert mixed.predictability is SupportPredictability.VARIABLE
    assert bespoke.predictability is SupportPredictability.HIGH_VARIANCE
    assert standardized.verdict is SupportVerdict.HEALTHY_SUPPORT
    assert mixed.verdict is SupportVerdict.THIN_SUPPORT
    assert bespoke.verdict is SupportVerdict.INSUFFICIENT_SUPPORT


def test_scope_and_language_stay_within_chapter18():
    conclusions = " ".join(REPORT.conclusions)
    assert "Recurring revenue is not pure contribution" in conclusions
    assert "Chapter 17 initial delivery economics are separate" in conclusions
    assert REPORT.delivery_economics_included is False
    assert REPORT.final_opportunity_verdict is None
    assert "build-versus-buy" in conclusions
