"""W2-03 commit 4: the selected cold assessment reads (`.agent/W2-03-build-spec.md` "Commit 4 - selected reads").

`GET /api/sites/{code}/cold/temperature`, `/cold/backup-chain`, `/cold/findings` and `/cold/findings/{id}` with
strict UTC `from`, `to` (half-open, at most 31 days) and `known_at` (default: the committed disposition watermark
at request start); the Finding list adds `cursor` and `limit` (default 50, max 200). Without `from`/`to` the read
uses the latest selected cold window at the cutoff. Refusals use `{error:{code,message}}`: 401/403 through the
Finding-route access seam (403 also when the `disclosure` seam refuses the Site's source disclosure), 404 for an
unknown, foreign or non-COLDCHAIN Site or unknown scoped Finding, 409 for a cursor of a changed selected basis,
422 for a malformed instant, range, limit or unknown parameter, 503 when a store cannot be read. A window with no
selected assessment is 200 `UNKNOWN` with null values and empty arrays.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable
from uuid import UUID

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from assetops_backend.analytics.cold_reads import (
    DEFAULT_LIMIT,
    MAX_LIMIT,
    MAX_WINDOW,
    ColdCursorRefused,
    ColdReadService,
    ColdReadUnavailable,
)
from assetops_backend.finding_api import Access, development_access
from assetops_backend.sites.cold_foundation import COLD_SITE_TYPE
from assetops_backend.sites.cutover import ImportedSiteRegistry
from assetops_backend.sites.ports import SiteStoreUnavailable

COLD_ROUTE = "/api/sites/{site_code}/cold"
WINDOW_KEYS = frozenset({"from", "to", "known_at"})
LIST_KEYS = WINDOW_KEYS | {"cursor", "limit"}
# (site_code, tenant_id, site_id) -> True when this caller may see the Site's source provenance.
Disclosure = Callable[[str, UUID, UUID], bool]


def allow_disclosure(site_code: str, tenant_id: UUID, site_id: UUID) -> bool:
    return True


class _Refused(Exception):
    def __init__(self, status: int, code: str, message: str, headers: dict[str, str] | None = None) -> None:
        super().__init__(message)
        self.status, self.code, self.headers = status, code, headers


def _refusal(error: _Refused) -> JSONResponse:
    return JSONResponse(status_code=error.status, headers=error.headers,
                        content={"error": {"code": error.code, "message": str(error)}})


def _instant(request: Request, key: str) -> datetime | None:
    raw = request.query_params.get(key)
    if raw is None:
        return None
    try:
        at = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        at = None
    if at is None or at.tzinfo is None or at.utcoffset() != timezone.utc.utcoffset(None):
        raise _Refused(422, "COLD_TIME_INVALID", f"'{key}' must be a UTC instant such as 2026-10-06T19:00:00Z.")
    return at


def build_cold_assessment_router(registry: ImportedSiteRegistry, reads: ColdReadService | None,
                                 access: Access = development_access,
                                 disclosure: Disclosure = allow_disclosure) -> APIRouter:
    router = APIRouter()

    def opened(request: Request, site_code: str, keys: frozenset) -> tuple[UUID, UUID, dict[str, Any]]:
        refusal = access(request, site_code)
        if refusal == 401:
            raise _Refused(401, "UNAUTHENTICATED", "Sign in to read cold-chain assessments.",
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

    def served(work: Callable[[], Any]) -> Any:
        try:
            return work()
        except _Refused as error:
            return _refusal(error)
        except ColdCursorRefused as error:
            return _refusal(_Refused(error.status, error.code, str(error)))
        except ColdReadUnavailable as error:
            return _refusal(_Refused(503, "COLD_READ_UNAVAILABLE", str(error)))

    @router.get(COLD_ROUTE + "/temperature")
    def temperature(request: Request, site_code: str) -> Any:
        def work():
            t, s, w = opened(request, site_code, WINDOW_KEYS)
            return reads.temperature(t, s, site_code, w["lo"], w["hi"], w["known_at"])
        return served(work)

    @router.get(COLD_ROUTE + "/backup-chain")
    def backup_chain(request: Request, site_code: str) -> Any:
        def work():
            t, s, w = opened(request, site_code, WINDOW_KEYS)
            return reads.backup_chain(t, s, site_code, w["lo"], w["hi"], w["known_at"])
        return served(work)

    @router.get(COLD_ROUTE + "/findings")
    def findings(request: Request, site_code: str) -> Any:
        def work():
            t, s, w = opened(request, site_code, LIST_KEYS)
            raw = request.query_params.get("limit")
            limit = DEFAULT_LIMIT
            if raw is not None:
                if not raw.isdigit() or not 1 <= int(raw) <= MAX_LIMIT:
                    raise _Refused(422, "COLD_LIMIT_INVALID", f"'limit' must be 1 to {MAX_LIMIT}.")
                limit = int(raw)
            return reads.findings(t, s, site_code, w["lo"], w["hi"], w["known_at"],
                                  request.query_params.get("cursor"), limit)
        return served(work)

    @router.get(COLD_ROUTE + "/findings/{finding_id}")
    def finding(request: Request, site_code: str, finding_id: str) -> Any:
        def work():
            t, s, w = opened(request, site_code, WINDOW_KEYS)
            try:
                fid = UUID(finding_id)
            except ValueError:
                raise _Refused(404, "COLD_FINDING_NOT_FOUND", "No such cold Finding.") from None
            body = reads.finding(t, s, site_code, fid, w["lo"], w["hi"], w["known_at"])
            if body is None:
                raise _Refused(404, "COLD_FINDING_NOT_FOUND", "No such cold Finding in this Site and window.")
            return body
        return served(work)

    return router
