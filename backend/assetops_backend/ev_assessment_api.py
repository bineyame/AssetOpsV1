"""W2-06 commit 4: the selected EV session and Finding reads (`.agent/W2-06-build-spec.md` "Commit 4: selected
reads and refusal dry-read" and "Run 5 rulings (r5)").

`GET /api/sites/{code}/ev/sessions`, `/ev/sessions/{id}`, `/ev/findings` and `/ev/findings/{id}`. Lists take only
`from`, `to`, `known_at`, `cursor`, `limit` (1..200, default 50); details only `from`, `to`, `known_at`. Bounds are
paired UTC instants (at most microseconds), `[from,to)` at most 31 days; both omitted selects the latest selected EV
window at the cutoff and echoes it. Authentication precedes the Site lookup; the Site, tenant, type and disclosure
checks precede any record lookup. Refusals are exactly `{error:{code,message}}`. A valid selection without a
selected assessment is 200 `UNKNOWN` with null counts and empty arrays.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Callable
from uuid import UUID

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from assetops_backend.analytics.ev_reads import (
    DEFAULT_LIMIT,
    MAX_LIMIT,
    MAX_WINDOW,
    EvReadRefused,
    EvReadUnavailable,
)
from assetops_backend.finding_api import Access, development_access
from assetops_backend.sites.cutover import ImportedSiteRegistry
from assetops_backend.sites.ports import SiteStoreUnavailable

EV_SITE_TYPE = "EV_CHARGING"
EV_ROUTE = "/api/sites/{site_code}/ev"
WINDOW_KEYS = frozenset({"from", "to", "known_at"})
LIST_KEYS = WINDOW_KEYS | {"cursor", "limit"}
_UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?(Z|\+00:00)$")
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
    at = None
    if _UTC.match(raw):
        try:
            at = datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(timezone.utc)
        except ValueError:
            at = None
    if at is None:
        raise _Refused(422, "EV_TIME_INVALID",
                       f"'{key}' must be a UTC instant such as 2026-10-06T08:00:00Z (at most microseconds).")
    return at


def _not_found() -> _Refused:
    return _Refused(404, "EV_RECORD_NOT_FOUND", "No such EV record in this Site, window and cutoff.")


class EvGate:
    """The W2-06 request gate (authentication, query keys, window, Site, disclosure), refusal wrapper and `limit`
    rule, shared verbatim by the W2-07 Site reads (`ev_site_api`)."""

    def __init__(self, opened: Callable, served: Callable, limit_of: Callable) -> None:
        self.opened, self.served, self.limit_of = opened, served, limit_of


def ev_gate(registry: ImportedSiteRegistry, reads: Any | None, access: Access = development_access,
            disclosure: Disclosure = allow_disclosure) -> EvGate:
    def opened(request: Request, site_code: str, keys: frozenset) -> tuple[UUID, UUID, dict[str, Any]]:
        refusal = access(request, site_code)
        if refusal == 401:
            raise _Refused(401, "UNAUTHENTICATED", "Sign in to read EV assessments.",
                           {"WWW-Authenticate": "Bearer"})
        if refusal == 403:
            raise _Refused(403, "SITE_SCOPE_FORBIDDEN", f"No access to Site {site_code!r}.")
        names = [k for k, _ in request.query_params.multi_items()]
        repeated = sorted({k for k in names if names.count(k) > 1})
        if repeated:
            raise _Refused(422, "EV_PARAMETER_UNKNOWN", f"Parameters may not repeat: {repeated}.")
        unknown = sorted(set(names) - keys)
        if unknown:
            raise _Refused(422, "EV_PARAMETER_UNKNOWN", f"Unknown parameters {unknown}.")
        lo, hi, known = _instant(request, "from"), _instant(request, "to"), _instant(request, "known_at")
        if (lo is None) != (hi is None):
            raise _Refused(422, "EV_WINDOW_INVALID", "Give both 'from' and 'to', or neither.")
        if lo is not None and not lo < hi:
            raise _Refused(422, "EV_WINDOW_INVALID", "'from' must be before 'to'.")
        if lo is not None and hi - lo > MAX_WINDOW:
            raise _Refused(422, "EV_WINDOW_TOO_LONG", "An EV read window is at most 31 days.")
        try:
            site = registry.imported(site_code)
            tenant = registry.tenant() if site is not None else None
        except SiteStoreUnavailable as error:
            raise _Refused(503, "EV_READ_UNAVAILABLE", "The EV Site registry is unavailable.") from error
        if site is None or tenant is None or site.site_type != EV_SITE_TYPE:
            raise _Refused(404, "SITE_NOT_FOUND", f"No EV charging Site {site_code!r} in this tenant.")
        if reads is None:
            raise _Refused(503, "EV_READ_UNAVAILABLE", "No product database is configured.")
        if not disclosure(site_code, tenant.id, site.id):
            raise _Refused(403, "EV_SOURCE_DISCLOSURE_FORBIDDEN",
                           f"The source provenance of Site {site_code!r} may not be disclosed to this caller.")
        return tenant.id, site.id, {"lo": lo, "hi": hi, "known_at": known}

    def served(work: Callable[[], Any]) -> Any:
        try:
            return work()
        except _Refused as error:
            return _refusal(error)
        except EvReadRefused as error:
            return _refusal(_Refused(error.status, error.code, str(error)))
        except EvReadUnavailable:
            return _refusal(_Refused(503, "EV_READ_UNAVAILABLE", "EV assessments cannot be read right now."))

    def limit_of(request: Request) -> int:
        raw = request.query_params.get("limit")
        if raw is None:
            return DEFAULT_LIMIT
        # r8 L1: ASCII digits only; `int(raw)` runs only after both checks (a non-ASCII digit such as '²' is
        # `isdigit()` but not an integer literal).
        if not (raw.isascii() and raw.isdigit() and 1 <= int(raw) <= MAX_LIMIT):
            raise _Refused(422, "EV_LIMIT_INVALID", f"'limit' must be 1 to {MAX_LIMIT}.")
        return int(raw)

    return EvGate(opened, served, limit_of)


def build_ev_assessment_router(registry: ImportedSiteRegistry, reads: Any | None,
                               access: Access = development_access,
                               disclosure: Disclosure = allow_disclosure) -> APIRouter:
    router = APIRouter()
    gate = ev_gate(registry, reads, access, disclosure)
    opened, served, limit_of = gate.opened, gate.served, gate.limit_of

    def record_id(raw: str) -> UUID:
        try:
            return UUID(raw)
        except ValueError:
            raise _not_found() from None

    @router.get(EV_ROUTE + "/sessions")
    def sessions(request: Request, site_code: str) -> Any:
        def work():
            t, s, w = opened(request, site_code, LIST_KEYS)
            return reads.sessions(t, s, site_code, w["lo"], w["hi"], w["known_at"],
                                  request.query_params.get("cursor"), limit_of(request))
        return served(work)

    @router.get(EV_ROUTE + "/sessions/{session_id}")
    def session(request: Request, site_code: str, session_id: str) -> Any:
        def work():
            t, s, w = opened(request, site_code, WINDOW_KEYS)
            body = reads.session(t, s, site_code, record_id(session_id), w["lo"], w["hi"], w["known_at"])
            if body is None:
                raise _not_found()
            return body
        return served(work)

    @router.get(EV_ROUTE + "/findings")
    def findings(request: Request, site_code: str) -> Any:
        def work():
            t, s, w = opened(request, site_code, LIST_KEYS)
            return reads.findings(t, s, site_code, w["lo"], w["hi"], w["known_at"],
                                  request.query_params.get("cursor"), limit_of(request))
        return served(work)

    @router.get(EV_ROUTE + "/findings/{finding_id}")
    def finding(request: Request, site_code: str, finding_id: str) -> Any:
        def work():
            t, s, w = opened(request, site_code, WINDOW_KEYS)
            body = reads.finding(t, s, site_code, record_id(finding_id), w["lo"], w["hi"], w["known_at"])
            if body is None:
                raise _not_found()
            return body
        return served(work)

    return router
