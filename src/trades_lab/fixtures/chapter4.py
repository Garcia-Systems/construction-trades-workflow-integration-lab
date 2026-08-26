"""Deterministic, entirely synthetic records for Chapter 4."""

VALID_ACCEPTED_ESTIMATE = {
    "estimate_id": "EW-EST-2001",
    "estimate_version": 3,
    "customer_id": "EW-CUST-842",
    "status": "CUSTOMER_APPROVED",
    "accepted_at": "2026-08-25T16:00:00Z",
    "scope": "Replace residential HVAC system",
    "service_address": {
        "line1": "101 Fictional Way", "city": "Williamsburg",
        "state": "VA", "postal_code": "23185",
    },
    "total": "12450.00",
}


def estimate_record(**changes):
    """Return an isolated fixture, including an isolated nested address."""
    record = {**VALID_ACCEPTED_ESTIMATE,
              "service_address": dict(VALID_ACCEPTED_ESTIMATE["service_address"])}
    record.update(changes)
    return record


MISSING_CUSTOMER_ESTIMATE = estimate_record(customer_id=None)
STALE_ACCEPTED_ESTIMATE = estimate_record(estimate_version=2)
OPEN_ESTIMATE = estimate_record(status="OPEN", accepted_at=None)
