from decimal import Decimal

from trades_lab.chapter0 import BASELINE_HYPOTHESIS
from trades_lab.cli import render_chapter0
from trades_lab.evidence import EvidenceCategory


def test_modeled_delivery_hours_total_466() -> None:
    assert BASELINE_HYPOTHESIS.modeled_engineering_hours == 466


def test_economic_inputs_are_exact_decimals() -> None:
    hypothesis = BASELINE_HYPOTHESIS
    assert hypothesis.annual_current_state_burden == Decimal("130584.22")
    assert hypothesis.annual_recoverable_value == Decimal("64619.29")
    assert hypothesis.implementation_price == Decimal("50000.00")
    assert hypothesis.annual_recurring_fee == Decimal("12000.00")


def test_payback_is_derived_from_inputs() -> None:
    expected = Decimal("50000.00") / (Decimal("64619.29") - Decimal("12000.00")) * Decimal(12)
    assert BASELINE_HYPOTHESIS.implementation_payback_months == expected
    assert f"{expected:.1f}" == "11.4"


def test_classification_and_original_verdict() -> None:
    assert BASELINE_HYPOTHESIS.evidence_category is EvidenceCategory.MODELED_ASSUMPTION
    assert BASELINE_HYPOTHESIS.original_verdict == "PROMISING — VALIDATE IN DISCOVERY"


def test_derived_results_and_rendering_are_deterministic() -> None:
    first = (
        BASELINE_HYPOTHESIS.implementation_price_percentage,
        BASELINE_HYPOTHESIS.recurring_fee_percentage,
        render_chapter0(),
    )
    second = (
        BASELINE_HYPOTHESIS.implementation_price_percentage,
        BASELINE_HYPOTHESIS.recurring_fee_percentage,
        render_chapter0(),
    )
    assert first == second
