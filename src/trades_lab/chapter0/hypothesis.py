"""Fictional, modeled baseline reconstructed from the opportunity cookbook."""

from dataclasses import dataclass
from decimal import Decimal

from trades_lab.evidence import EvidenceCategory


@dataclass(frozen=True)
class CustomerProfile:
    name: str
    employees: int
    field_crews: int
    active_jobs_description: str


@dataclass(frozen=True)
class DeliveryActivity:
    name: str
    hours: int


@dataclass(frozen=True)
class BaselineHypothesis:
    """Inputs and derived economics; every input is a modeled assumption."""

    customer: CustomerProfile
    annual_current_state_burden: Decimal
    annual_recoverable_value: Decimal
    implementation_price: Decimal
    annual_recurring_fee: Decimal
    reusable_core_percentage: Decimal
    delivery_activities: tuple[DeliveryActivity, ...]
    delivery_contribution: str
    support_contribution: str
    original_verdict: str
    evidence_category: EvidenceCategory = EvidenceCategory.MODELED_ASSUMPTION

    @property
    def modeled_engineering_hours(self) -> int:
        return sum(activity.hours for activity in self.delivery_activities)

    @property
    def implementation_payback_months(self) -> Decimal:
        net_annual_value = self.annual_recoverable_value - self.annual_recurring_fee
        return self.implementation_price / net_annual_value * Decimal(12)

    @property
    def implementation_price_percentage(self) -> Decimal:
        return self.implementation_price / self.annual_recoverable_value * Decimal(100)

    @property
    def recurring_fee_percentage(self) -> Decimal:
        return self.annual_recurring_fee / self.annual_recoverable_value * Decimal(100)


BASELINE_HYPOTHESIS = BaselineHypothesis(
    customer=CustomerProfile(
        name="James River Mechanical",
        employees=44,
        field_crews=7,
        active_jobs_description="dozens",
    ),
    annual_current_state_burden=Decimal("130584.22"),
    annual_recoverable_value=Decimal("64619.29"),
    implementation_price=Decimal("50000.00"),
    annual_recurring_fee=Decimal("12000.00"),
    reusable_core_percentage=Decimal("52.8"),
    delivery_activities=(
        DeliveryActivity("technical discovery", 24),
        DeliveryActivity("API validation", 36),
        DeliveryActivity("adapters", 104),
        DeliveryActivity("identity normalization", 34),
        DeliveryActivity("orchestration", 58),
        DeliveryActivity("reliability / error handling", 48),
        DeliveryActivity("exception handling", 34),
        DeliveryActivity("documentation", 22),
        DeliveryActivity("QA / testing", 54),
        DeliveryActivity("deployment", 16),
        DeliveryActivity("rework reserve", 36),
    ),
    delivery_contribution="thin but positive",
    support_contribution="sustainable but thin",
    original_verdict="PROMISING — VALIDATE IN DISCOVERY",
)
