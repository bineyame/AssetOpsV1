"""W3-03 estate Portfolio root: read-only, no Site parameter. Lane A mounts it after the reviewed run 1b.

`GET /api/estate/portfolio?from=&to=&known_at=&lens=&limit=&cursor=`, in W3-01 `estate_api.py` order:
authentication (401 with `WWW-Authenticate: Bearer`) before any tenant lookup or parsing, then the strict shared
parser, then one read-only snapshot with per-Site admission through the existing `access` seam. Every refusal is
W3-01's `{code,message,rows:null,total_count:null}` body inside `detail` plus Portfolio's
`value_cards:null,objectives:null,money:null` (`.agent/W3-03-build-spec.md` closure 1 refusals), including 401 and
503; no success field appears on an error.
"""

from __future__ import annotations

from typing import Any, Callable
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.encoders import jsonable_encoder

from assetops_backend import perf
from assetops_backend.chain.response_store import ResponseStore, StoredRoute, finish, parsed_key
from assetops_backend.estate.portfolio import split_scope_ids
from assetops_backend.estate.scope import (
    EstateRefusal, EstateStoreUnavailable, MESSAGES, parse_request, portfolio_cursor_key)
from assetops_backend.estate_api import Authenticate, development_authenticate
from assetops_backend.finding_api import Access, development_access

PORTFOLIO = "/api/estate/portfolio"
SCOPE_IDS = "/api/estate/portfolio/scope-ids"

#: The Portfolio null fields inside every refusal `detail`.
EXTRAS = {"value_cards": None, "objectives": None, "money": None}


def refusal(code: str) -> dict[str, Any]:
    return {"code": code, "message": MESSAGES[code], "rows": None, "total_count": None, **EXTRAS}


def build_estate_portfolio_router(service: Any | None, tenant: Callable[[], UUID | None], *,
                                  authenticate: Authenticate = development_authenticate,
                                  access: Access = development_access,
                                  unavailable: tuple[type[BaseException], ...] = (),
                                  responses: ResponseStore | None = None) -> APIRouter:
    """`responses` (CH-5c) stores both sub-routes of one composed Portfolio under one watermark."""
    router = APIRouter()
    down = (EstateStoreUnavailable, *unavailable)

    @router.get(PORTFOLIO)
    def estate_portfolio(request: Request, response: Response) -> dict[str, Any]:
        with perf.route(PORTFOLIO, response):  # QW-1: one `assetops.perf` line per request
            out = _estate_portfolio(request, PORTFOLIO)
        return finish(out, response) if isinstance(out, Response) else out

    @router.get(SCOPE_IDS)
    def estate_portfolio_scope_ids(request: Request, response: Response) -> dict[str, Any]:
        """CH-5c Q9: the per-Site selected assessment ids of the same Portfolio request (same window, Sites and
        admission), fetched when the "assessment ids" technical disclosure opens."""
        with perf.route(SCOPE_IDS, response):
            out = _estate_portfolio(request, SCOPE_IDS)
        return finish(out, response) if isinstance(out, Response) else out

    def _estate_portfolio(request: Request, route: str) -> Any:
        if authenticate(request) == 401:
            raise HTTPException(status_code=401, headers={"WWW-Authenticate": "Bearer"},
                                detail=refusal("UNAUTHENTICATED"))
        try:
            parsed = parse_request("portfolio", request.query_params.multi_items())
            # r1b2 R1: the deployment cursor key is checked at the parsed API boundary, before the store opens a
            # snapshot (a missing/malformed key makes zero database reads); the snapshot re-reads it for the MAC.
            portfolio_cursor_key()
            if service is None:
                raise EstateStoreUnavailable("No product database is configured.")
            admit = lambda code: access(request, code) is None  # noqa: E731
            tenant_id = tenant()
            if responses is not None and tenant_id is not None:
                return responses.serve(StoredRoute(route, tenant_id, parsed_key(parsed), admit=admit),
                                       lambda: _bodies(service.portfolio(tenant_id, parsed, admit)))
            body = service.portfolio(tenant_id, parsed, admit)
        except EstateRefusal as error:
            headers = {"WWW-Authenticate": "Bearer"} if error.status == 401 else None
            raise HTTPException(status_code=error.status, detail=refusal(error.code), headers=headers) from error
        except down as error:
            raise HTTPException(status_code=503, detail=refusal("ESTATE_STORE_UNAVAILABLE")) from error
        return _bodies(body)[route]

    return router


def _bodies(composed: dict[str, Any]) -> dict[str, Any]:
    """Both sub-routes of one composed Portfolio: the body without its private ids, and the ids."""
    body, ids = split_scope_ids(composed)
    return {PORTFOLIO: jsonable_encoder(body),
            SCOPE_IDS: jsonable_encoder({"schema_version": "estate-portfolio-scope-ids-1", "window": body.get("window"),
                                         "sites": ids})}

