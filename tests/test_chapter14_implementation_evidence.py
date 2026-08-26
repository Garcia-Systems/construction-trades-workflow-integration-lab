from dataclasses import replace
from decimal import Decimal

from trades_lab.chapter14 import (CHANGE_SCENARIOS, IMPLEMENTATION_INVENTORY,
    EvidenceLevel, ImplementationClassification, ReuseConfidence, ReuseScope,
    build_report, reuse_matrix)
from trades_lab.cli import render_chapter14


def unit(unit_id):
    return next(x for x in IMPLEMENTATION_INVENTORY if x.unit_id == unit_id)


def test_inventory_is_deterministic_complete_and_well_formed():
    assert build_report() == build_report()
    assert tuple(x.unit_id for x in IMPLEMENTATION_INVENTORY) == tuple(x.unit_id for x in build_report().units)
    assert len({x.unit_id for x in IMPLEMENTATION_INVENTORY}) == len(IMPLEMENTATION_INVENTORY)
    for item in IMPLEMENTATION_INVENTORY:
        assert isinstance(item.primary_classification, ImplementationClassification)
        assert len(item.secondary_tags) == len(set(item.secondary_tags))
        assert isinstance(item.reuse_scope, ReuseScope)
        assert isinstance(item.evidence_level, EvidenceLevel)
        assert item.evidence_references and all(item.evidence_references)


def test_observed_cross_workflow_claims_have_multiple_chapter_uses():
    observed = [x for x in IMPLEMENTATION_INVENTORY
        if x.reuse_scope is ReuseScope.CROSS_WORKFLOW and x.evidence_level is EvidenceLevel.OBSERVED_REUSE]
    assert observed
    assert all(len(set(x.used_by_chapters)) > 1 for x in observed)


def test_specialized_content_and_adapters_are_not_overclaimed():
    mapping = unit("jrm-materials")
    assert mapping.reuse_scope is ReuseScope.CUSTOMER_SPECIFIC
    assert mapping.evidence_level is EvidenceLevel.OBSERVED_SPECIALIZATION
    assert unit("fieldtrack-adapter").reuse_scope is ReuseScope.SOURCE_SPECIFIC
    for adapter in ("estimateworks-adapter", "job-boundary", "crewboard-adapter",
                    "supplydesk-adapter", "ledgerpro-adapter"):
        assert unit(adapter).reuse_scope is ReuseScope.DESTINATION_SPECIFIC


def test_summaries_partition_inventory_and_support_is_separate():
    report = build_report()
    assert sum(report.classification_counts.values()) == len(report.units)
    assert sum(report.evidence_counts.values()) == len(report.units)
    assert sum(report.reuse_scope_counts.values()) == len(report.units)
    assert report.support_surface_count == sum(x.support_surface for x in report.units)
    assert sum(report.support_surface_by_primary.values()) == report.support_surface_count
    assert report.support_surface_count > 0


def test_ratio_is_deterministic_bounded_and_explicitly_not_labor():
    report = build_report()
    expected = (Decimal(report.observed_cross_workflow_count) / len(report.units)).quantize(Decimal("0.001"))
    assert report.observed_cross_workflow_ratio == expected
    assert Decimal(0) <= expected <= Decimal(1)
    assert report.ratio_label == "Observed implementation-unit cross-workflow reuse ratio"
    output = render_chapter14()
    assert "IMPLEMENTATION UNITS ≠ ENGINEERING HOURS" in output
    assert "labor reuse" in output and "Direct validation of 52.8%: NO" in output


def test_original_assumption_is_retained_without_claiming_measurement():
    report = build_report()
    assert report.original_modeled_reusable_effort == Decimal("52.8")
    output = render_chapter14()
    assert "Evidence: MODELED ASSUMPTION" in output
    assert "Same denominator as 52.8%: NO" in output
    assert "No human-hour, price, margin, payback" in output


def test_change_scenarios_separate_mechanism_from_specialization():
    scenarios = {x.scenario_id: x for x in CHANGE_SCENARIOS}
    material = scenarios["NEW_CUSTOMER_MATERIAL_MAPPING"]
    assert material.unchanged_units == ("mapping-registry",)
    assert "mapping tests" in material.changed_or_added_units and material.support_surface_change == "GROWS"
    source = scenarios["REPLACE_FIELDTRACK"]
    assert "canonical-states" in source.unchanged_units and "source adapter" in source.changed_or_added_units
    reliability = scenarios["NEW_CONSEQUENTIAL_HANDOFF"]
    assert {"correlation", "idempotency", "acknowledgement", "retry-policy"} <= set(reliability.unchanged_units)


def test_negative_evidence_and_matrix_are_retained_deterministically():
    report = build_report()
    assert report.negative_evidence
    assert any("destination" in x for x in report.negative_evidence)
    assert reuse_matrix() == reuse_matrix()
    assert "Correlation mechanism" in reuse_matrix() and "CH13" in reuse_matrix()
    assert report.reuse_confidence is ReuseConfidence.MIXED


def test_negative_evidence_can_be_represented_on_a_unit():
    changed = replace(unit("reconciliation"), negative_evidence="additional one-off check")
    assert changed.negative_evidence == "additional one-off check"
