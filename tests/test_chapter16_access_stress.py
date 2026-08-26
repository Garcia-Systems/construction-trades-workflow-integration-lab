import pytest

from trades_lab.chapter16 import *


def test_profiles_classify_differently():
    assert tuple(map(classify_access, PROFILES)) == (AccessRisk.CLEAN, AccessRisk.CONSTRAINED, AccessRisk.CLOSED)


def test_clean_consequential_write_requires_and_has_safe_recovery():
    result = evaluate_transition(CLEAN, "accepted estimate → job")
    assert result.feasibility is Feasibility.FULLY_AUTOMATABLE
    assert CLEAN.capability.safe_recovery and CLEAN.capability.lookup_support


def test_raw_write_support_without_recovery_is_not_full_automation():
    assert DIFFICULT.capability.write_access is AccessLevel.LIMITED
    assert not DIFFICULT.capability.safe_recovery
    assert evaluate_transition(DIFFICULT, "accepted estimate → job").feasibility is Feasibility.AUTOMATABLE_WITH_CONSTRAINTS


def test_closed_job_write_is_blocked_but_read_visibility_remains():
    assert evaluate_transition(CLOSED, "accepted estimate → job").feasibility is Feasibility.BLOCKED
    assert evaluate_transition(CLOSED, "field status → office").feasibility is Feasibility.READ_ONLY
    assert CLOSED.capability.write_access is AccessLevel.NONE


def test_human_packet_is_validated_deterministic_and_never_writes():
    packet = create_job_handoff_packet("corr", "EST-1", "CUST-1", "evidence-1")
    assert packet == create_job_handoff_packet("corr", "EST-1", "CUST-1", "evidence-1")
    assert not packet.destination_write_performed
    assert reconcile_packet(packet, "JOB-1") and not reconcile_packet(packet, None)
    with pytest.raises(ValueError):
        create_job_handoff_packet("corr", "", "CUST-1", "evidence")


def test_known_csv_schema_parses_and_preserves_source_identity():
    rows = parse_estimate_export("estimate_id,status,customer_id,updated_at\nEST-1,ACCEPTED,C-1,2026-01-01T00:00:00Z\n")
    assert rows == (ExportEstimate("EST-1", "ACCEPTED", "C-1", "2026-01-01T00:00:00Z"),)
    assert rows[0].source_system == "BidForge CSV v1"


@pytest.mark.parametrize("content", [
    "estimate_id,status,customer_id,updated_at\nEST-1,ACCEPTED,C-1\n",
    "estimate_id,status,customer_id,updated_at\nEST-1,,C-1,2026-01-01\n",
])
def test_malformed_csv_rows_are_rejected(content):
    with pytest.raises(CsvExportError):
        parse_estimate_export(content)


def test_missing_header_and_changed_schema_are_drift_not_guessed():
    with pytest.raises(SchemaDriftError, match="schema drift"):
        parse_estimate_export("estimate_id,status,updated_at\n1,ACCEPTED,now\n")
    with pytest.raises(SchemaDriftError) as caught:
        parse_estimate_export("estimate_number,approval_status,customer_ref,last_modified\n1,YES,C,now\n")
    assert "observed" in str(caught.value) and CsvExportError.support_action
    with pytest.raises(SchemaDriftError):
        parse_estimate_export("anything\n1\n", "v2")


def test_no_sandbox_is_explicit_and_blind_replay_is_not_claimed():
    result = evaluate_transition(DIFFICULT, "accepted estimate → job")
    assert not DIFFICULT.capability.sandbox_available and not DIFFICULT.capability.lookup_support
    assert any("no sandbox" in reason for reason in result.reasons)
    assert RELIABILITY_MATRIX["safe auto replay"][1] == "NO"


def test_matrix_report_support_and_scopes_are_deterministic():
    first, second = build_report(), build_report()
    assert first == second and len(first.transition_results) == len(PROFILES) * len(HANDOFFS) == 18
    assert len(first.support_surface) == sum(map(len, SUPPORT.values()))
    scopes = tuple(recommend_scope("accepted estimate → job", p).scope for p in PROFILES)
    assert scopes == (TechnicalScope.API_WRITE_AUTOMATION, TechnicalScope.HUMAN_REVIEW_ASSIST,
                      TechnicalScope.NATIVE_VENDOR_WORKFLOW)


def test_material_scope_moves_from_api_to_export_to_read_only():
    scopes = tuple(recommend_scope("materials handoff", p).scope for p in PROFILES)
    assert scopes == (TechnicalScope.API_WRITE_AUTOMATION, TechnicalScope.EXPORT_IMPORT_AUTOMATION,
                      TechnicalScope.READ_ONLY_VISIBILITY)


def test_inventory_has_access_specific_and_architecture_effects_without_hours():
    assert ("strict CSV parser", "SOURCE-SPECIFIC ADAPTER") in ARCHITECTURE_INVENTORY
    assert ("human-handoff packet", "SHARED CORE") in ARCHITECTURE_INVENTORY
    assert not any("hour" in value.lower() for row in ARCHITECTURE_INVENTORY for value in row)
