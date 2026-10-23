"""W5-03a E1b: the three cursorless selected EV depth reads (`.agent/W5-03-build-spec.md` E1b).

`GET /api/sites/{code}/ev/availability`, `/ev/energy` and `/ev/health` reuse W2-06's gate unchanged
(`ev_assessment_api.ev_gate`): authentication before the Site lookup, repeated or unknown keys 422
`EV_PARAMETER_UNKNOWN`, paired UTC bounds at most 31 days, optional `known_at`, the `{error:{code,message}}` wrapper,
disclosure, and one read-only REPEATABLE READ snapshot per read. No cursor, so no basis-change 409.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from assetops_backend.ev_assessment_api import EV_ROUTE, WINDOW_KEYS, Disclosure, allow_disclosure, ev_gate
from assetops_backend.finding_api import Access, development_access
from assetops_backend.sites.cutover import ImportedSiteRegistry


def build_ev_depth_router(registry: ImportedSiteRegistry, reads: Any | None, access: Access = development_access,
                          disclosure: Disclosure = allow_disclosure) -> APIRouter:
    router = APIRouter()
    gate = ev_gate(registry, reads, access, disclosure)

    def depth_route(path: str, method: str) -> None:
        @router.get(EV_ROUTE + path, name=f"ev_depth_{method}")
        def read(request: Request, site_code: str) -> Any:
            def work():
                t, s, w = gate.opened(request, site_code, WINDOW_KEYS)
                return getattr(reads, method)(t, s, site_code, w["lo"], w["hi"], w["known_at"])
            return gate.served(work)

    depth_route("/availability", "availability")
    depth_route("/energy", "energy")
    depth_route("/health", "health")
    return router
