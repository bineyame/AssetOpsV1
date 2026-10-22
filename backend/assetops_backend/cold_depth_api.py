"""W5-01 C1: the selected cold depth route (`.agent/W5-01-build-spec.md` "Shared selected read and guards").

`GET /api/sites/{site_code}/cold/cooling` and `/cold/health` with optional paired strict UTC `from,to`
(half-open, at most 31 days) and optional `known_at`, through the W2-04 cold Site gate
(`cold_site_api.build_cold_gate`) and its refusal mapping. Cursorless, so no 409. Composition only; no SQL driver here.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from assetops_backend.cold_assessment_api import COLD_ROUTE, WINDOW_KEYS, Disclosure, allow_disclosure
from assetops_backend.cold_site_api import build_cold_gate, cold_served
from assetops_backend.finding_api import Access, development_access
from assetops_backend.sites.cutover import ImportedSiteRegistry


def build_cold_depth_router(registry: ImportedSiteRegistry, reads: Any | None,
                            access: Access = development_access,
                            disclosure: Disclosure = allow_disclosure) -> APIRouter:
    router = APIRouter()
    opened = build_cold_gate(registry, reads, access, disclosure)

    @router.get(COLD_ROUTE + "/cooling")
    def cooling(request: Request, site_code: str) -> Any:
        def work():
            t, s, w = opened(request, site_code, WINDOW_KEYS)
            return reads.cooling(t, s, site_code, w["lo"], w["hi"], w["known_at"])
        return cold_served(work)

    @router.get(COLD_ROUTE + "/health")
    def health(request: Request, site_code: str) -> Any:
        def work():
            t, s, w = opened(request, site_code, WINDOW_KEYS)
            return reads.health(t, s, site_code, w["lo"], w["hi"], w["known_at"])
        return cold_served(work)

    return router
