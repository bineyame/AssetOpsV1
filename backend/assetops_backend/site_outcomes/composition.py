"""OUT-B4 (§B.3 "Wiring"): builds `SiteOutcomeBoardService` from the services `main.py` already composed.

This is the one module of `site_outcomes/` that may reach other packages' compositions and request parsers
(`tests/test_out_b4_imports.py`). It reuses the process's existing service instances, so the board opens no store
of its own except the global work read for the preventive list (`work/composition.py` `build_global_work_read`),
which `main.py` disposes at shutdown. Every service may be None (no product database): its port then refuses and
the board reads PARTIAL, as B.3 "Refusals" requires.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any
from uuid import UUID

from assetops_backend.actions.lifecycle import selector
from assetops_backend.actions.site_index import parse_request as parse_action_index
from assetops_backend.actions.verification import VerificationService
from assetops_backend.analytics.finding_index import parse_request as parse_finding_index
from assetops_backend.analytics.performance_comparison import basis_reason
from assetops_backend.finding_api import ACCESS_BASIS
from assetops_backend.site_outcomes.read import BoardServices, SiteOutcomeBoardService
from assetops_backend.work.composition import build_global_work_read
from assetops_backend.work.domain_action_index import parse_index_request
from assetops_backend.work.global_index import select_preventive
from assetops_backend.work.site_index import parse_list_request

Gate = Callable[[str, UUID, UUID], "tuple[bool, str]"]


class OverviewClosed(RuntimeError):
    """The S2 comparison has not passed and no empty-legacy basis exists: the Overview itself would be 409."""


def overview_source(route: Any, s2_scope: Callable[[str], Any] | None) -> Gate:
    """The Overview route's own source decision (`site_overview/route.py:139-158`), for the mini overview port:
    the persisted empty-legacy basis or a passing S2 comparison, then the Performance gate with ruling 3's
    reason. A closed basis raises, so the port fails and the board reads PARTIAL instead of an empty claim."""
    def decide(code: str, tenant_id: UUID, site_id: UUID) -> tuple[bool, str]:
        empty_legacy = bool(route.no_legacy_basis(tenant_id, site_id))
        if not empty_legacy and (s2_scope is None or s2_scope(code) is None):
            raise OverviewClosed(f"Site {code!r} has no passing Evidence comparison.")
        permitted, reason = route.gate(code, tenant_id, site_id)
        return bool(permitted), basis_reason(bool(permitted), reason, empty_legacy)
    return decide


def build_outcome_board_service(
        database_url: str | None, *, site_overview: Any = None, s2_scope: Callable[[str], Any] | None = None,
        mini_depth: Any = None, dispatch: Any = None, performance_gate: Gate | None = None,
        finding_index: Any = None, finding_index_gate: Gate | None = None, assumptions: Any = None,
        actions: Any = None, action_index: Any = None, cold_site: Any = None, cold_reads: Any = None,
        ev_site: Any = None, ev_reads: Any = None, ev_depth: Any = None, domain_actions: Any = None,
        work_index: Any = None, estate: Any = None) -> tuple[SiteOutcomeBoardService, Callable[[], None]]:
    """Returns the service and its dispose callable (the global work read it opened, if any)."""
    global_work = build_global_work_read(database_url) if database_url else None
    services = BoardServices(
        overview=None if site_overview is None else site_overview.read,
        overview_source=None if site_overview is None else overview_source(site_overview, s2_scope),
        mini_depth=mini_depth, dispatch=dispatch, finding_index=finding_index, performance_gate=performance_gate,
        finding_index_gate=finding_index_gate, assumptions=assumptions, action_index=action_index,
        actions=actions, verification=None if actions is None else VerificationService(actions),
        cold_site=cold_site, cold_reads=cold_reads, ev_site=ev_site, ev_reads=ev_reads, ev_depth=ev_depth,
        domain_actions=domain_actions, work_index=work_index, global_work=global_work,
        select_preventive=select_preventive, estate=estate, parse_finding_index=parse_finding_index,
        parse_action_index=parse_action_index, parse_work_list=parse_list_request,
        parse_domain_index=parse_index_request, action_selector=selector, access_basis=ACCESS_BASIS,
        work_access_basis=ACCESS_BASIS)

    def dispose() -> None:
        if global_work is not None:
            global_work.dispose()

    return SiteOutcomeBoardService(services), dispose
