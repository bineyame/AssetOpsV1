"""Composition for the work domain: the only module that imports its adapter (W4-01 commit 2).

Callers receive the `WorkService` over `PostgresWorkStore`, whose provenance reads use the evidence ledger's
caller-connection link-row reader (the shared W3 `PublicProvenance` contract; no second DTO).
"""

from __future__ import annotations

from typing import Callable
from uuid import UUID, uuid4

from assetops_backend.evidence.composition import build_link_rows_reader
from assetops_backend.work.adapters.postgres_work_read import LinkReadPorts, PostgresWorkRead
from assetops_backend.work.adapters.postgres_work_store import PostgresWorkStore
from assetops_backend.work.detail import WorkDetailService
from assetops_backend.work.model import WorkStoreUnavailable
from assetops_backend.work.service import WorkService

__all__ = ["WORK_UNAVAILABLE", "build_work_detail_service", "build_work_read", "build_work_service",
           "build_work_store"]

WORK_UNAVAILABLE = WorkStoreUnavailable


def build_work_store(database_url: str | None) -> PostgresWorkStore:
    return PostgresWorkStore(database_url, link_rows=build_link_rows_reader())


def build_work_service(database_url: str | None, *, new_id: Callable[[], UUID] = uuid4) -> WorkService:
    return WorkService(build_work_store(database_url), new_id=new_id)


def _link_read_ports() -> LinkReadPorts:
    """Run 3 ruling 6: the one shared cold/EV `_snapshot` owner and the W3 q5 at-cutoff mini-grid reads, each bound
    to no connection of its own (every call takes the work read's connection)."""
    from assetops_backend.analytics import cold, ev
    from assetops_backend.analytics.adapters.postgres_assessment_store import SelectionPinRefused, selected_windows_on
    from assetops_backend.analytics.composition import (build_cold_read_service, build_ev_read_service,
                                                        build_finding_store, build_postgres_assessment_store)

    return LinkReadPorts(
        cold_snapshot=build_cold_read_service(None)._snapshot, ev_snapshot=build_ev_read_service(None)._snapshot,
        selected_windows=selected_windows_on, pin_refused=(SelectionPinRefused,),
        dispatch_days=build_postgres_assessment_store(None).select_dispatch_days_on,
        finding_index=build_finding_store(None).index_snapshot_on,
        cold_analytics=(cold.EXCURSION_ANALYTIC, cold.START_RESPONSE_ANALYTIC), ev_analytics=(ev.SESSION_ANALYTIC,))


def build_work_read(database_url: str | None) -> PostgresWorkRead:
    return PostgresWorkRead(database_url, link_rows=build_link_rows_reader(), ports=_link_read_ports())


def build_work_detail_service(database_url: str | None) -> WorkDetailService:
    return WorkDetailService(build_work_read(database_url))
