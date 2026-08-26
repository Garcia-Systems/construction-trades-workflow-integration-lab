from trades_lab.chapter9 import (ARCHITECTURE_INVENTORY, DeliveryState, FailureCategory,
    Fault, FaultScriptDestination, ReliableHandoff, RetryDecision, retry_decision)


def delivery(faults, *, lookup=True, maximum=3):
    destination = FaultScriptDestination(faults, supports_lookup=lookup)
    handoff = ReliableHandoff(destination, maximum_attempts=maximum)
    item = handoff.new_delivery("business-event-1", "accepted-estimate:EW-1:v1", "correlation-1")
    return handoff, destination, item


def test_policy_classifies_retry_stop_reconcile_and_repair_explicitly():
    assert retry_decision(FailureCategory.TRANSIENT, 1) is RetryDecision.RETRY
    assert retry_decision(FailureCategory.TRANSIENT, 3) is RetryDecision.STOP
    assert retry_decision(FailureCategory.PERMANENT_VALIDATION, 1) is RetryDecision.STOP
    assert retry_decision(FailureCategory.CONFLICT, 1) is RetryDecision.STOP
    assert retry_decision(FailureCategory.AUTHENTICATION, 1) is RetryDecision.WAIT_FOR_REPAIR
    assert retry_decision(FailureCategory.UNCERTAIN_OUTCOME, 1) is RetryDecision.RECONCILE_FIRST


def test_outage_and_timeout_retry_to_one_effect():
    for faults in ([Fault.UNAVAILABLE, Fault.UNAVAILABLE, Fault.SUCCESS],
                   [Fault.TIMEOUT_BEFORE_WRITE, Fault.SUCCESS],
                   [Fault.SERVICE_BUSY, Fault.SUCCESS]):
        handoff, destination, item = delivery(faults)
        result = handoff.execute(item)
        assert result.state is DeliveryState.ACKNOWLEDGED
        assert len(destination.effects) == 1
        assert len(result.attempts) == len(faults)


def test_persistent_transient_is_bounded_exhausted_and_visible():
    handoff, destination, item = delivery([Fault.UNAVAILABLE] * 9)
    result = handoff.execute(item)
    assert result.state is DeliveryState.EXHAUSTED
    assert len(result.attempts) == 3 and not destination.effects
    assert result.events[-1].event_type == "DELIVERY_RETRY_EXHAUSTED"


def test_ack_lost_is_uncertain_until_lookup_and_never_rewrites():
    handoff, destination, item = delivery([Fault.ACKNOWLEDGEMENT_LOST])
    uncertain = handoff.execute(item, reconcile_uncertain=False)
    assert uncertain.state is DeliveryState.UNCERTAIN and destination.write_calls == 1
    assert handoff.replay(item.delivery_id).state is DeliveryState.ACKNOWLEDGED
    assert destination.lookup_calls == 1 and destination.write_calls == 1
    assert len(destination.effects) == 1


def test_no_lookup_uncertainty_blocks_for_human_review():
    handoff, destination, item = delivery([Fault.ACKNOWLEDGEMENT_LOST], lookup=False)
    result = handoff.execute(item)
    assert result.state is DeliveryState.BLOCKED and result.human_review_required
    assert destination.write_calls == 1 and len(destination.effects) == 1


def test_validation_and_conflict_do_not_retry_and_conflict_has_exception():
    for fault, category in ((Fault.MALFORMED, FailureCategory.PERMANENT_VALIDATION),
                            (Fault.CONFLICT, FailureCategory.CONFLICT)):
        handoff, destination, item = delivery([fault, Fault.SUCCESS])
        result = handoff.execute(item)
        assert result.state is DeliveryState.BLOCKED and len(result.attempts) == 1
        assert result.exception.category is category and not destination.effects


def test_authentication_requires_repair_and_explicit_replay_preserves_identity():
    handoff, destination, item = delivery([Fault.EXPIRED_CREDENTIALS, Fault.SUCCESS])
    result = handoff.execute(item)
    original = (result.business_event_id, result.idempotency_key, result.correlation_id)
    assert result.state is DeliveryState.BLOCKED and len(result.attempts) == 1
    destination.repair_credentials()
    replay = handoff.replay(item.delivery_id)
    assert replay.state is DeliveryState.ACKNOWLEDGED and len(replay.attempts) == 2
    assert (replay.business_event_id, replay.idempotency_key, replay.correlation_id) == original
    assert len(destination.effects) == 1


def test_duplicate_transport_delivery_joins_logical_delivery():
    handoff, destination, first = delivery([Fault.UNAVAILABLE, Fault.SUCCESS])
    duplicate = handoff.new_delivery("transport-copy", first.idempotency_key,
                                     "different-correlation", delivery_id="delivery-duplicate")
    assert duplicate is first
    handoff.execute(first)
    assert len(handoff.deliveries) == len(destination.effects) == 1
    assert {a.attempt_id for a in first.attempts} == {
        "delivery-001:attempt:1", "delivery-001:attempt:2"}
    assert {event.correlation_id for event in first.events} == {"correlation-1"}


def test_history_and_inventory_are_deterministic_and_expand_support_surface():
    one = delivery([Fault.UNAVAILABLE, Fault.SUCCESS])[0:3]
    two = delivery([Fault.UNAVAILABLE, Fault.SUCCESS])[0:3]
    histories = []
    for handoff, _, item in (one, two):
        histories.append([(e.event_type, e.occurred_at, e.correlation_id) for e in
                          handoff.execute(item).events])
    assert histories[0] == histories[1]
    categories = {category for category, _ in ARCHITECTURE_INVENTORY}
    assert {"RELIABILITY", "SUPPORT SURFACE", "EXCEPTION HANDLING", "TESTING"} <= categories
