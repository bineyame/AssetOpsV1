"""Composition for the scheduling domain: the only module that imports its adapters (S4-02d).

Callers receive the `ScheduleStore` port; `SCHEDULE_UNAVAILABLE` is the store's unavailable error type.
"""

from __future__ import annotations

from assetops_backend.scheduling.adapters.postgres_schedule_store import (
    PostgresScheduleStore,
    ScheduleStoreUnavailable,
)
from assetops_backend.scheduling.ports import ScheduleStore

__all__ = ["SCHEDULE_UNAVAILABLE", "build_schedule_store"]

SCHEDULE_UNAVAILABLE = ScheduleStoreUnavailable


def build_schedule_store(database_url: str | None, *, statement_timeout_ms: int = 30_000,
                         lock_timeout_ms: int = 5_000) -> ScheduleStore:
    return PostgresScheduleStore(database_url, statement_timeout_ms=statement_timeout_ms,
                                 lock_timeout_ms=lock_timeout_ms)
