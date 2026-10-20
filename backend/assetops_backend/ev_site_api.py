"""W2-07 commit 3: the five selected EV Site reads (`.agent/W2-07-build-spec.md` "Five selected reads", the
post-W2-06 reconciliation "Commits 3-5: refusals" and q4).

`GET /api/sites/{code}/ev/overview`, `/ev/evidence`, `/ev/evidence/analysis`, `/ev/financials` and
`/ev/financial-assumptions`. They reuse W2-06's gate unchanged (`ev_assessment_api.ev_gate`): authentication before
the Site lookup, repeated keys 422 `EV_PARAMETER_UNKNOWN` before value parsing, paired UTC bounds at most 31 days,
`limit` ASCII digits 1..200, and the same `{error:{code,message}}` wrapper and messages. No route takes a record ID or
an exact-revision selector, so 404 is only `SITE_NOT_FOUND` and 409 only `EV_CURSOR_BASIS_CHANGED`.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from assetops_backend.ev_assessment_api import (
    EV_ROUTE,
    LIST_KEYS,
    WINDOW_KEYS,
    Disclosure,
    allow_disclosure,
    ev_gate,
)
from assetops_backend.finding_api import Access, development_access
from assetops_backend.sites.cutover import ImportedSiteRegistry


def build_ev_site_router(registry: ImportedSiteRegistry, reads: Any | None, access: Access = development_access,
                         disclosure: Disclosure = allow_disclosure) -> APIRouter:
    router = APIRouter()
    gate = ev_gate(registry, reads, access, disclosure)

    def window_route(path: str, method: str) -> None:
        @router.get(EV_ROUTE + path, name=f"ev_site_{method}")
        def read(request: Request, site_code: str) -> Any:
            def work():
                t, s, w = gate.opened(request, site_code, WINDOW_KEYS)
                return getattr(reads, method)(t, s, site_code, w["lo"], w["hi"], w["known_at"])
            return gate.served(work)

    def list_route(path: str, method: str) -> None:
        @router.get(EV_ROUTE + path, name=f"ev_site_{method}")
        def read(request: Request, site_code: str) -> Any:
            def work():
                t, s, w = gate.opened(request, site_code, LIST_KEYS)
                return getattr(reads, method)(t, s, site_code, w["lo"], w["hi"], w["known_at"],
                                              request.query_params.get("cursor"), gate.limit_of(request))
            return gate.served(work)

    window_route("/overview", "overview")
    window_route("/evidence", "evidence")
    list_route("/evidence/analysis", "analysis")
    list_route("/financials", "financials")
    window_route("/financial-assumptions", "assumptions")
    return router
