"""Small, visibly synthetic RiverLead scenario fixtures."""

from copy import deepcopy

VALID_QUALIFIED_LEAD = {
    "lead_id": "RL-1001", "customer_id": "RLC-501", "status": "QUALIFIED",
    "first_name": "Jordan", "last_name": "Lee",
    "email": "jordan.lee@example.test", "phone": "757-555-0101",
    "service_address": {"line1": "101 Fictional Way", "city": "Williamsburg",
                        "state": "VA", "postal_code": "23185"},
    "requested_service": "HVAC replacement estimate",
    "updated_at": "2026-08-25T14:00:00Z",
    # Deliberately omitted by the destination command:
    "crm_owner": "Synthetic Sales Queue", "marketing_campaign": "FICTIONAL-2026",
}


def scenario_lead(**changes: object) -> dict[str, object]:
    record = deepcopy(VALID_QUALIFIED_LEAD)
    record.update(changes)
    return record


INELIGIBLE_LEAD = scenario_lead(lead_id="RL-1002", customer_id="RLC-502", status="NEW",
                                first_name="Casey", last_name="Example",
                                email="casey@example.test")
MISSING_CONTACT_LEAD = scenario_lead(lead_id="RL-1003", customer_id="RLC-503",
                                     email="", phone="")
UNKNOWN_STATE_LEAD = scenario_lead(lead_id="RL-1004", customer_id="RLC-504",
                                   status="AWAITING_MAGIC")
AMBIGUOUS_IDENTITY_LEAD = scenario_lead(lead_id="RL-1005", customer_id="RLC-505",
                                        first_name="Jordan", last_name="Lee")
MALFORMED_LEAD = {"lead_id": "RL-1006", "status": "QUALIFIED"}
