"""W2-04 commit 3: the five cold Site reads (`.agent/W2-04-build-spec.md` "Five API reads").

`GET /api/sites/{code}/cold/overview`, `/cold/evidence`, `/cold/evidence/analysis`, `/cold/financials` and
`/cold/financial-assumptions`, with optional paired strict UTC `from,to` (half-open, at most 31 days) and optional
`known_at`; Analysis adds `cursor,limit` (default 50, max 200). Scope, parse and refusal order mirror
`cold_assessment_api.build_cold_assessment_router`, plus the spec's additions: an instant finer than microseconds
is 422 `COLD_TIME_INVALID`, and so is a `known_at` later than the captured committed watermark (checked inside
the snapshot by `ColdSiteReadService`). Composition only; no SQL driver here.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Callable
from uuid import UUID

from fastapi import APIRouter, Request

from assetops_backend.analytics.cold_reads import (
    DEFAULT_LIMIT,
    MAX_LIMIT,
    MAX_WINDOW,
    ColdCursorRefused,
    ColdReadUnavailable,
)
from assetops_backend.cold_assessment_api import (
    COLD_ROUTE,
    LIST_KEYS,
    WINDOW_KEYS,
    Disclosure,
    _Refused,
    _refusal,
    allow_disclosure,
)
from assetops_backend.finding_api import Access, development_access
from assetops_backend.sites.cold_foundation import COLD_SITE_TYPE
from assetops_backend.sites.cutover import ImportedSiteRegistry
from assetops_backend.sites.ports import SiteStoreUnavailable

_FRACTION = re.compile(r"\.(\d+)")


def _instant(request: Request, key: str) -> datetime | None:
    raw = request.query_params.get(key)
    if raw is None:
        return None
    fraction = _FRACTION.search(raw)
    try:
        at = None if fraction is not None and len(fraction.group(1)) > 6 else \
            datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        at = None
    if at is None or at.tzinfo is None or at.utcoffset() != timezone.utc.utcoffset(None):
        raise _Refused(422, "COLD_TIME_INVALID",
                       f"'{key}' must be a UTC instant such as 2026-10-06T19:00:00Z, at most microsecond precision.")
    return at


def build_cold_gate(registry: ImportedSiteRegistry, reads: Any | None, access: Access = development_access,
                    disclosure: Disclosure = allow_disclosure
                    ) -> Callable[[Request, str, frozenset], tuple[UUID, UUID, dict[str, Any]]]:
    """W5-01 C1: the W2-04 cold Site gate, extracted unchanged so the cold depth reads share it. Authenticate and
    Site-scope before any lookup, refuse unknown parameters, parse the strict paired half-open UTC window (at most
    31 days) and optional `known_at`, resolve the imported cold Site, then check the store and disclosure."""
    def opened(request: Request, site_code: str, keys: frozenset) -> tuple[UUID, UUID, dict[str, Any]]:
        refusal = access(request, site_code)
        if refusal == 401:
            raise _Refused(401, "UNAUTHENTICATED", "Sign in to read cold-chain Site data.",
                           {"WWW-Authenticate": "Bearer"})
        if refusal == 403:
            raise _Refused(403, "SITE_SCOPE_FORBIDDEN", f"No access to Site {site_code!r}.")
        unknown = sorted(set(request.query_params) - keys)
        if unknown:
            raise _Refused(422, "COLD_PARAMETER_UNKNOWN", f"Unknown parameters {unknown}.")
        lo, hi, known = _instant(request, "from"), _instant(request, "to"), _instant(request, "known_at")
        if (lo is None) != (hi is None):
            raise _Refused(422, "COLD_WINDOW_INVALID", "Give both 'from' and 'to', or neither.")
        if lo is not None and not lo < hi:
            raise _Refused(422, "COLD_WINDOW_INVALID", "'from' must be before 'to'.")
        if lo is not None and hi - lo > MAX_WINDOW:
            raise _Refused(422, "COLD_WINDOW_TOO_LONG", "A cold read window is at most 31 days.")
        try:
            site = registry.imported(site_code)
            tenant = registry.tenant() if site is not None else None
        except SiteStoreUnavailable as error:
            raise _Refused(503, "COLD_READ_UNAVAILABLE", str(error)) from error
        if site is None or tenant is None or site.site_type != COLD_SITE_TYPE:
            raise _Refused(404, "SITE_NOT_FOUND", f"No cold-chain Site {site_code!r} in this tenant.")
        if reads is None:
            raise _Refused(503, "COLD_READ_UNAVAILABLE", "No product database is configured.")
        if not disclosure(site_code, tenant.id, site.id):
            raise _Refused(403, "COLD_SOURCE_DISCLOSURE_FORBIDDEN",
                           f"The source provenance of Site {site_code!r} may not be disclosed to this caller.")
        return tenant.id, site.id, {"lo": lo, "hi": hi, "known_at": known}
    return opened


def cold_served(work: Callable[[], Any]) -> Any:
    """Run one gated cold read; a refusal, cursor/known_at refusal or unavailable store is its typed error body."""
    try:
        return work()
    except _Refused as error:
        return _refusal(error)
    except ColdCursorRefused as error:
        return _refusal(_Refused(error.status, error.code, str(error)))
    except ColdReadUnavailable as error:
        return _refusal(_Refused(503, "COLD_READ_UNAVAILABLE", str(error)))


def build_cold_site_router(registry: ImportedSiteRegistry, reads: Any | None,
                           access: Access = development_access,
                           disclosure: Disclosure = allow_disclosure) -> APIRouter:
    router = APIRouter()
    opened = build_cold_gate(registry, reads, access, disclosure)
    served = cold_served

    def windowed(name: str):
        def endpoint(request: Request, site_code: str) -> Any:
            def work():
                t, s, w = opened(request, site_code, WINDOW_KEYS)
                return getattr(reads, name)(t, s, site_code, w["lo"], w["hi"], w["known_at"])
            return served(work)
        return endpoint

    router.add_api_route(COLD_ROUTE + "/overview", windowed("overview"), methods=["GET"])
    router.add_api_route(COLD_ROUTE + "/evidence", windowed("evidence"), methods=["GET"])
    router.add_api_route(COLD_ROUTE + "/financials", windowed("financials"), methods=["GET"])
    router.add_api_route(COLD_ROUTE + "/financial-assumptions", windowed("assumptions"), methods=["GET"])

    @router.get(COLD_ROUTE + "/evidence/analysis")
    def analysis(request: Request, site_code: str) -> Any:
        def work():
            t, s, w = opened(request, site_code, LIST_KEYS)
            raw = request.query_params.get("limit")
            limit = DEFAULT_LIMIT
            if raw is not None:
                if not raw.isdigit() or not 1 <= int(raw) <= MAX_LIMIT:
                    raise _Refused(422, "COLD_LIMIT_INVALID", f"'limit' must be 1 to {MAX_LIMIT}.")
                limit = int(raw)
            return reads.analysis(t, s, site_code, w["lo"], w["hi"], w["known_at"],
                                  request.query_params.get("cursor"), limit)
        return served(work)

    return router
