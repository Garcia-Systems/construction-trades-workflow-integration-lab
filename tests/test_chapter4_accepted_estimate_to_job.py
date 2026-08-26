from dataclasses import fields

from trades_lab.chapter1 import (Readiness, baseline_readiness,
                                 chapter4_resolved_readiness)
from trades_lab.chapter4 import (AcceptedEstimateToJobHandoff, CrewBoardSimulator,
                                 DestinationJob, IdempotencyStatus, JobHandoffOutcome,
                                 ServiceAddress)
from trades_lab.domain import ExceptionCategory
from trades_lab.fixtures.chapter4 import (MISSING_CUSTOMER_ESTIMATE, OPEN_ESTIMATE,
                                          STALE_ACCEPTED_ESTIMATE,
                                          VALID_ACCEPTED_ESTIMATE, estimate_record)


def test_first_acceptance_creates_exactly_one_acknowledged_authoritative_job():
    handoff = AcceptedEstimateToJobHandoff()
    result = handoff.process(VALID_ACCEPTED_ESTIMATE)
    assert result.outcome is JobHandoffOutcome.CREATED
    assert len(handoff.destination.jobs) == len(handoff.commands) == 1
    assert result.acknowledgement.destination_job_id == "JOB-9001"
    assert result.acknowledgement.created is True
    assert handoff.registry[result.command.idempotency_key].status is IdempotencyStatus.ACKNOWLEDGED


def test_command_is_narrow_and_does_not_copy_unneeded_total():
    command = AcceptedEstimateToJobHandoff().process(VALID_ACCEPTED_ESTIMATE).command
    assert {field.name for field in fields(command)} == {
        "idempotency_key", "correlation_id", "source_estimate_id",
        "source_estimate_version", "customer_reference", "service_address",
        "scope_summary", "provenance"}
    assert not hasattr(command, "total")


def test_business_key_is_deterministic_and_version_sensitive():
    key = AcceptedEstimateToJobHandoff.idempotency_key("EW-EST-2001", 3)
    assert key == "accepted-estimate:EW-EST-2001:v3"
    assert key == AcceptedEstimateToJobHandoff.idempotency_key("EW-EST-2001", 3)
    assert key != AcceptedEstimateToJobHandoff.idempotency_key("EW-EST-2001", 4)


def test_exact_and_separate_transport_replays_resolve_to_original_job():
    handoff = AcceptedEstimateToJobHandoff()
    first = handoff.process(VALID_ACCEPTED_ESTIMATE, "event-001")
    exact = handoff.process(VALID_ACCEPTED_ESTIMATE, "event-001")
    separate = handoff.process(VALID_ACCEPTED_ESTIMATE, "event-002")
    assert exact.outcome is separate.outcome is JobHandoffOutcome.IDEMPOTENT_REPLAY
    assert first.command.idempotency_key == exact.command.idempotency_key == separate.command.idempotency_key
    assert first.acknowledgement.destination_job_id == exact.acknowledgement.destination_job_id == separate.acknowledgement.destination_job_id
    assert len(handoff.destination.jobs) == 1
    assert exact.events[0].metadata != separate.events[0].metadata


def test_missing_identity_and_nonaccepted_state_never_write():
    missing_handoff = AcceptedEstimateToJobHandoff()
    missing = missing_handoff.process(MISSING_CUSTOMER_ESTIMATE)
    assert missing.outcome is JobHandoffOutcome.EXCEPTION
    assert missing.exception.category is ExceptionCategory.IDENTITY
    assert not missing_handoff.destination.jobs
    open_handoff = AcceptedEstimateToJobHandoff()
    opened = open_handoff.process(OPEN_ESTIMATE)
    assert opened.outcome is JobHandoffOutcome.NOT_ELIGIBLE
    assert opened.exception is None and not open_handoff.destination.jobs


def test_stale_version_is_detected_without_rollback_or_overwrite():
    handoff = AcceptedEstimateToJobHandoff()
    original = handoff.process(VALID_ACCEPTED_ESTIMATE)
    stale = handoff.process(STALE_ACCEPTED_ESTIMATE)
    assert stale.outcome is JobHandoffOutcome.STALE
    assert len(handoff.destination.jobs) == 1
    job = handoff.destination.jobs[0]
    assert job.source_estimate_version == 3
    assert job.job_id == original.acknowledgement.destination_job_id


def test_conflicting_destination_claim_stops_without_create_or_overwrite():
    destination = CrewBoardSimulator()
    preloaded = DestinationJob("JOB-8800", "legacy", "EW-EST-2001", 3,
                               "EW-CUST-842",
                               ServiceAddress("999 Other", "Williamsburg", "VA", "23185"),
                               "Incompatible scope")
    destination.preload_job(preloaded)
    result = AcceptedEstimateToJobHandoff(destination).process(VALID_ACCEPTED_ESTIMATE)
    assert result.outcome is JobHandoffOutcome.EXCEPTION
    assert result.exception.category is ExceptionCategory.STATE_CONFLICT
    assert destination.jobs == (preloaded,)


def test_provenance_correlation_and_event_history_survive_all_success_artifacts():
    left = AcceptedEstimateToJobHandoff().process(VALID_ACCEPTED_ESTIMATE)
    right = AcceptedEstimateToJobHandoff().process(VALID_ACCEPTED_ESTIMATE)
    assert left.events == right.events
    assert tuple(event.event_type for event in left.events) == (
        "ESTIMATE_OBSERVED", "ESTIMATE_VALIDATED", "JOB_CREATE_READY",
        "JOB_CREATE_SENT", "JOB_CREATE_ACKNOWLEDGED")
    assert left.estimate.provenance == left.command.provenance == left.acknowledgement.provenance
    assert left.correlation_id == left.command.correlation_id == left.acknowledgement.correlation_id
    assert all(event.correlation_id == left.correlation_id for event in left.events)


def test_capability_and_approval_validation_stop_unsafe_writes():
    for handoff in (AcceptedEstimateToJobHandoff(write_capability_confirmed=False),
                    AcceptedEstimateToJobHandoff(approval_boundary_known=False)):
        result = handoff.process(VALID_ACCEPTED_ESTIMATE)
        assert result.outcome is JobHandoffOutcome.EXCEPTION
        assert not handoff.destination.jobs


def test_destination_not_registry_is_authoritative_for_job_existence():
    destination = CrewBoardSimulator()
    first_handoff = AcceptedEstimateToJobHandoff(destination)
    first = first_handoff.process(VALID_ACCEPTED_ESTIMATE)
    fresh_integration_process = AcceptedEstimateToJobHandoff(destination)
    replay = fresh_integration_process.process(VALID_ACCEPTED_ESTIMATE)
    assert not first_handoff.registry is fresh_integration_process.registry
    assert replay.outcome is JobHandoffOutcome.IDEMPOTENT_REPLAY
    assert replay.acknowledgement.destination_job_id == first.acknowledgement.destination_job_id


def test_chapter1_baseline_stays_blocked_but_modeled_chapter4_variant_can_proceed():
    baseline = next(result for result in baseline_readiness()
                    if result.transition == "accepted_estimate_to_job")
    assert baseline.status is Readiness.BLOCKED
    assert chapter4_resolved_readiness().status is Readiness.READY_WITH_CONSTRAINTS
