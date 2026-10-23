"""Composition for the work domain: the only module that imports its adapter (W4-01 commit 2).

Callers receive the `WorkService` over `PostgresWorkStore`, whose provenance reads use the evidence ledger's
caller-connection link-row reader (the shared W3 `PublicProvenance` contract; no second DTO).
"""

from __future__ import annotations

from typing import Callable
from uuid import UUID, uuid4

from assetops_backend.evidence.composition import build_link_rows_reader
from assetops_backend.work.adapters.postgres_domain_intent import PostgresDomainIntentStore
from assetops_backend.work.adapters.postgres_global_read import PostgresGlobalWorkRead
from assetops_backend.work.adapters.postgres_work_read import LinkReadPorts, PostgresWorkRead, _ReadTx
from assetops_backend.work.adapters.postgres_work_store import PostgresWorkStore
from assetops_backend.work.detail import WorkDetailService
from assetops_backend.work.domain_intent import DomainIntentService
from assetops_backend.work.global_index import GlobalWorkIndexService
from assetops_backend.work.site_index import WorkIndexService
from assetops_backend.work.model import WorkStoreUnavailable
from assetops_backend.work.service import WorkService

__all__ = ["WORK_UNAVAILABLE", "build_domain_intent_service", "build_domain_intent_store",
           "build_global_work_index_service", "build_global_work_read",
           "build_work_detail_service", "build_work_index_service", "build_work_read", "build_work_service",
           "build_work_store"]

WORK_UNAVAILABLE = WorkStoreUnavailable


def build_work_store(database_url: str | None) -> PostgresWorkStore:
    return PostgresWorkStore(database_url, link_rows=build_link_rows_reader())


def build_work_service(database_url: str | None, *, new_id: Callable[[], UUID] = uuid4) -> WorkService:
    return WorkService(build_work_store(database_url), new_id=new_id)


def _link_read_ports() -> LinkReadPorts:
    """Run 3 ruling 6: the one shared cold/EV `_snapshot` owner and the W3 q5 at-cutoff mini-grid reads, each bound
    to no connection of its own (every call takes the work read's connection)."""
    from assetops_backend.actions.composition import build_action_store
    from assetops_backend.analytics import cold, ev
    from assetops_backend.analytics.composition import (build_cold_ev_selection_pins, build_cold_read_service,
                                                        build_ev_read_service, build_finding_store,
                                                        build_postgres_assessment_store)

    selected_windows_on, pin_refused = build_cold_ev_selection_pins()

    return LinkReadPorts(
        cold_snapshot=build_cold_read_service(None)._snapshot, ev_snapshot=build_ev_read_service(None)._snapshot,
        selected_windows=selected_windows_on, pin_refused=(pin_refused,),
        dispatch_days=build_postgres_assessment_store(None).select_dispatch_days_on,
        finding_index=build_finding_store(None).index_snapshot_on,
        cold_analytics=(cold.EXCURSION_ANALYTIC, cold.START_RESPONSE_ANALYTIC), ev_analytics=(ev.SESSION_ANALYTIC,),
        action_window=build_action_store(None).site_window_on)


def build_work_read(database_url: str | None) -> PostgresWorkRead:
    return PostgresWorkRead(database_url, link_rows=build_link_rows_reader(), ports=_link_read_ports())


def build_work_detail_service(database_url: str | None) -> WorkDetailService:
    return WorkDetailService(build_work_read(database_url))


def build_work_index_service(database_url: str | None) -> WorkIndexService:
    """W4-01 commit 4: the Site Incident/Maintenance lists over the same work read adapter."""
    return WorkIndexService(build_work_read(database_url))


def build_global_work_read(database_url: str | None) -> PostgresGlobalWorkRead:
    """W6-01a: the cross-Site read over the W4 per-Site selection reads, on one snapshot connection."""
    return PostgresGlobalWorkRead(database_url, link_rows=build_link_rows_reader(), ports=_link_read_ports())


def build_global_work_index_service(database_url: str | None) -> GlobalWorkIndexService | None:
    """W6-01a: None without a product database; the router answers 503, never an empty list."""
    return None if not database_url else GlobalWorkIndexService(build_global_work_read(database_url))


def selected_finding_pin(ports: LinkReadPorts):
    """W5-02a K1a (ruling A3): the W4 linked-selection pin of one Finding revision at a cutoff, on the caller's
    connection - the exact selection W4 links use (`_ReadTx._pin`), not a second selection implementation."""

    def pin_of(c, tenant_id, site_id, site_code, revision, known_at):
        return _ReadTx(c, tenant_id, site_id, site_code, known_at, None, ports)._pin(revision, None, None, known_at)

    return pin_of


def build_domain_intent_store(database_url: str | None) -> PostgresDomainIntentStore:
    return PostgresDomainIntentStore(database_url, pin_of=selected_finding_pin(_link_read_ports()))


def build_domain_intent_service(database_url: str | None, *,
                                new_id: Callable[[], UUID] = uuid4) -> DomainIntentService:
    """W5-02a K1a: the domain Action commands over their sole writer."""
    return DomainIntentService(build_domain_intent_store(database_url), new_id=new_id)
