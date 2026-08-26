"""Synthetic Chapter 6 mapping configuration and material requirements."""

from dataclasses import replace
from datetime import date, datetime, timezone
from decimal import Decimal

from trades_lab.chapter6 import (MappingStatus, MaterialMapping, MaterialMappingRegistry,
                                 MaterialRequirement, MaterialUnit, UnitConversion)
from trades_lab.domain import Provenance, SourceReference

OBSERVED_AT = datetime(2026, 2, 3, 12, tzinfo=timezone.utc)


def requirement(requirement_id: str, material_id: str, quantity: str,
                unit: MaterialUnit, version: int = 1, description: str = "Synthetic material",
                substitute: str | None = None) -> MaterialRequirement:
    source = SourceReference("CrewBoard Jobs", requirement_id)
    return MaterialRequirement(requirement_id, "JOB-9001", material_id, description,
                               Decimal(quantity), unit, date(2026, 2, 5), version,
                               Provenance(source, OBSERVED_AT, str(version), "corr-job-job-9001"),
                               substitute)


DIRECT = MaterialMapping("CrewBoard Jobs", "JRM-COND-3T-16S", "SupplyDesk",
                         "SD-HVAC-30017", "MAT-CONDENSER-3T", MaterialUnit.EACH,
                         MaterialUnit.EACH, MappingStatus.APPROVED,
                         "CUSTOMER-SPECIFIC RULE")
TUBING = MaterialMapping("CrewBoard Jobs", "JRM-COPPER-LINE", "SupplyDesk",
                         "SD-LINE-100FT", "MAT-COPPER-LINE", MaterialUnit.FOOT,
                         MaterialUnit.ROLL, MappingStatus.APPROVED, "CONFIGURATION",
                         UnitConversion(MaterialUnit.FOOT, MaterialUnit.ROLL,
                                        Decimal("0.01"), "FEET-TO-100FT-ROLL"))
FILTER_BOX = MaterialMapping("CrewBoard Jobs", "JRM-FILTER-20X20", "SupplyDesk",
                             "SD-FILTER-2020-EA", "MAT-FILTER-2020", MaterialUnit.EACH,
                             MaterialUnit.EACH, MappingStatus.APPROVED, "CONFIGURATION")
AMBIGUOUS_A = MaterialMapping("CrewBoard Jobs", "JRM-THERMOSTAT", "SupplyDesk",
                              "SD-CTRL-101", "MAT-THERMOSTAT-A", MaterialUnit.EACH,
                              MaterialUnit.EACH, MappingStatus.APPROVED, "CONFIGURATION")
AMBIGUOUS_B = replace(AMBIGUOUS_A, destination_material_id="SD-CTRL-102",
                      canonical_material_id="MAT-THERMOSTAT-B")
REGISTRY = MaterialMappingRegistry((DIRECT, TUBING, FILTER_BOX, AMBIGUOUS_A, AMBIGUOUS_B))

DIRECT_REQUIREMENT = requirement("MR-001", "JRM-COND-3T-16S", "1", MaterialUnit.EACH,
                                 description="Condensing unit")
CONVERSION_REQUIREMENT = requirement("MR-002", "JRM-COPPER-LINE", "40", MaterialUnit.FOOT,
                                     description="Copper tubing")
UNKNOWN_REQUIREMENT = requirement("MR-003", "JRM-UNKNOWN-44", "1", MaterialUnit.EACH)
UNIT_MISMATCH_REQUIREMENT = requirement("MR-004", "JRM-FILTER-20X20", "2", MaterialUnit.BOX)
AMBIGUOUS_REQUIREMENT = requirement("MR-005", "JRM-THERMOSTAT", "1", MaterialUnit.EACH)
SUBSTITUTE_REQUIREMENT = requirement("MR-006", "JRM-COND-3T-16S", "1", MaterialUnit.EACH,
                                     substitute="SD-HVAC-30018")
CHANGED_CONVERSION_REQUIREMENT = requirement("MR-002", "JRM-COPPER-LINE", "55",
                                             MaterialUnit.FOOT, version=2,
                                             description="Copper tubing")
PARTIAL_REQUIREMENTS = (DIRECT_REQUIREMENT, CONVERSION_REQUIREMENT,
                        UNKNOWN_REQUIREMENT, UNIT_MISMATCH_REQUIREMENT)
