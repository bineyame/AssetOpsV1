"""Composition for the scheduling domain: the only module that imports its adapters (S4-02d).

Callers receive the `ScheduleStore` port; `SCHEDULE_UNAVAILABLE` is the store's unavailable error type.
"""

from __future__ import annotations

from assetops_backend.scheduling.adapters.postgres_schedule_store import (
    PostgresScheduleStore,
    ScheduleStoreUnavailable,
)
from assetops_backend.scheduling.ports import ScheduleStore

__all__ = ["SCHEDULE_UNAVAILABLE", "build_schedule_health", "build_schedule_store", "build_upstream_currentness"]

SCHEDULE_UNAVAILABLE = ScheduleStoreUnavailable


def build_schedule_store(database_url: str | None, *, statement_timeout_ms: int = 30_000,
                         lock_timeout_ms: int = 5_000) -> ScheduleStore:
    return PostgresScheduleStore(database_url, statement_timeout_ms=statement_timeout_ms,
                                 lock_timeout_ms=lock_timeout_ms)


def build_schedule_health(database_url: str | None, thresholds=None):
    """The read-only operator report (S4-02d phase 2) over the schedule store and the existing S3, Finding and
    consequence stores/reads, each received from its own domain's composition."""
    from assetops_backend.analytics.assessment_worker import DOMAIN
    from assetops_backend.analytics.composition import build_finding_store, build_postgres_assessment_store
    from assetops_backend.analytics.dispatch import ANALYTIC_ID
    from assetops_backend.financials.composition import build_consequence_read_service, build_consequence_store
    from assetops_backend.scheduling.health import HealthThresholds, ScheduleHealth

    return ScheduleHealth(build_schedule_store(database_url), build_postgres_assessment_store(database_url),
                          build_finding_store(database_url), build_consequence_store(database_url),
                          build_consequence_read_service(database_url), analytic_id=ANALYTIC_ID, domain=DOMAIN,
                          thresholds=thresholds or HealthThresholds())


def build_upstream_currentness(database_url: str | None, thresholds=None):
    """The S5-01 selected-window upstream seam (S4-02d phase 2, packet item 4)."""
    from assetops_backend.analytics.composition import build_dispatch_read_service, build_finding_store
    from assetops_backend.analytics.dispatch import ANALYTIC_ID
    from assetops_backend.financials.composition import build_consequence_read_service, build_consequence_store
    from assetops_backend.scheduling.health import HealthThresholds
    from assetops_backend.scheduling.upstream import UpstreamCurrentness

    return UpstreamCurrentness(build_schedule_store(database_url), build_dispatch_read_service(database_url),
                               build_finding_store(database_url), build_consequence_store(database_url),
                               build_consequence_read_service(database_url), analytic_id=ANALYTIC_ID,
                               thresholds=thresholds or HealthThresholds())
