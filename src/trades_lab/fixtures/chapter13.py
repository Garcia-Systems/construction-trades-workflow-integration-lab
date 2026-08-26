"""Fixed production-like inputs; no environment or network is consulted."""

from dataclasses import replace
from datetime import datetime, timedelta, timezone

from trades_lab.chapter13 import (DependencyHealth, HealthStatus, ScheduleEntry,
    ScheduledTask, fixture_config, healthy_dependencies)

NOW = datetime(2026, 8, 26, 22, 0, tzinfo=timezone.utc)
CONFIG = fixture_config()
CREDENTIALS = frozenset(x.name for x in CONFIG.credential_references)
MISSING_ESTIMATEWORKS_CREDENTIALS = CREDENTIALS - {"estimateworks-api"}
HEALTHY_DEPENDENCIES = healthy_dependencies()
SUPPLYDESK_OUTAGE = tuple(replace(x, status=HealthStatus.UNHEALTHY,
    diagnostic="MODELED ASSUMPTION: dependency unavailable") if x.name == "SupplyDesk" else x
    for x in HEALTHY_DEPENDENCIES)
LEDGERPRO_OUTAGE = tuple(replace(x, status=HealthStatus.UNHEALTHY,
    diagnostic="MODELED ASSUMPTION: dependency unavailable") if x.name == "LedgerPro" else x
    for x in HEALTHY_DEPENDENCIES)
SCHEDULE = (
    ScheduleEntry(ScheduledTask.RECONCILIATION, timedelta(minutes=60), NOW-timedelta(minutes=61)),
    ScheduleEntry(ScheduledTask.OPERATIONAL_BRIEFING, timedelta(days=1), NOW-timedelta(hours=2)),
    ScheduleEntry(ScheduledTask.EXCEPTION_AGING, timedelta(hours=6), NOW-timedelta(hours=1)),
)
