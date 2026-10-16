"""S4-08 Site assumption and consequence history route (`I-assumption-consequence-history-read`).

`GET /api/sites/{site_code}/financial-assumptions/consequences?recorded_at=&after=&limit=` returns every stored
consequence revision of the Site recorded at or before one UTC cutoff (`financials/consequence_history.py`).
Missing `recorded_at` fixes the cutoff from the database clock and returns it; clients pass that exact string to
the price read and to every later page. Read-only: nothing here writes.

Scope before lookup, as the Finding and price reads: 401 / 403 from the access seam, 404 for a Site the tenant
does not know, then request validation (422, 400 for a cursor this list did not issue), then the read. A store
failure is 503 `CONSEQUENCE_HISTORY_UNAVAILABLE`, never an empty list. A closed Site source gate does not refuse
the list: every row stays listed with a typed closed-source state and no amount.

This router must be included before `financial_read_api`'s `/financial-assumptions/{revision_id}` route.
"""

from __future__ import annotations

from typing import Any, Callable
from urllib.parse import urlencode
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from fastapi.encoders import jsonable_encoder

from assetops_backend.finding_api import ACCESS_BASIS, Access, Gate, Scope, development_access, no_gate
from assetops_backend.financials.consequence_history import ConsequenceHistoryService, HistoryRefusal, parse_request


def build_consequence_history_router(history: ConsequenceHistoryService | None, scope: Scope,
                                     unavailable: tuple[type, ...] = (), access: Access = development_access,
                                     access_basis: str = ACCESS_BASIS, gate: Gate = no_gate) -> APIRouter:
    router = APIRouter()

    def store_down(message: str) -> HTTPException:
        return HTTPException(status_code=503, detail={"code": "CONSEQUENCE_HISTORY_UNAVAILABLE", "message": message,
                                                      "rows": None})

    def open_scope(request: Request, site_code: str) -> tuple[str, UUID, UUID]:
        refusal = access(request, site_code)
        if refusal == 401:
            raise HTTPException(status_code=401, headers={"WWW-Authenticate": "Bearer"},
                                detail={"code": "UNAUTHENTICATED", "message": "Sign in to read Site prices."})
        if refusal == 403:
            raise HTTPException(status_code=403, detail={"code": "SITE_SCOPE_FORBIDDEN",
                                                         "message": f"No access to Site {site_code!r}."})
        found = scope(site_code)
        if found is None or refusal == 404:
            raise HTTPException(status_code=404, detail=f"No imported Site {site_code!r} in this tenant.")
        if history is None:
            raise store_down("No product database is configured.")
        return found

    def served(work: Callable[[], Any]) -> Any:
        try:
            return work()
        except HistoryRefusal as refusal:
            raise HTTPException(status_code=refusal.status, detail=refusal.detail) from refusal
        except unavailable as error:
            raise store_down(str(error)) from error

    @router.get("/api/sites/{site_code}/financial-assumptions/consequences")
    def consequences(request: Request, site_code: str, recorded_at: str | None = None, after: str | None = None,
                     limit: str | None = None) -> dict[str, Any]:
        code, tenant_id, site_id = open_scope(request, site_code)
        parsed = served(lambda: parse_request(recorded_at, after, limit))
        source = served(lambda: gate(code, tenant_id, site_id))
        body = served(lambda: history.read(tenant_id, site_id, code, parsed, source_open=bool(source[0]),
                                           source_reason=source[1], access_basis=access_basis))
        cutoff = body["cutoff"]["recorded_at"]
        links: dict[str, Any] = {
            "assumptions_at_cutoff": f"/sites/{code}/financials/assumptions?{urlencode({'recorded_at': cutoff})}",
            "api_prices_at_cutoff": f"/api/sites/{code}/financial-assumptions?{urlencode({'recorded_at': cutoff})}"}
        if body["next_cursor"] is not None:
            query = urlencode({"recorded_at": cutoff, "after": body["next_cursor"], "limit": body["page"]["limit"]})
            links["api_next_page"] = f"/api/sites/{code}/financial-assumptions/consequences?{query}"
        return jsonable_encoder({**body, "links": links})

    return router
