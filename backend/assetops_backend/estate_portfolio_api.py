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

from fastapi import APIRouter, HTTPException, Request
from fastapi.encoders import jsonable_encoder

from assetops_backend.estate.scope import (
    EstateRefusal, EstateStoreUnavailable, MESSAGES, parse_request, portfolio_cursor_key)
from assetops_backend.estate_api import Authenticate, development_authenticate
from assetops_backend.finding_api import Access, development_access

#: The Portfolio null fields inside every refusal `detail`.
EXTRAS = {"value_cards": None, "objectives": None, "money": None}


def refusal(code: str) -> dict[str, Any]:
    return {"code": code, "message": MESSAGES[code], "rows": None, "total_count": None, **EXTRAS}


def build_estate_portfolio_router(service: Any | None, tenant: Callable[[], UUID | None], *,
                                  authenticate: Authenticate = development_authenticate,
                                  access: Access = development_access,
                                  unavailable: tuple[type[BaseException], ...] = ()) -> APIRouter:
    router = APIRouter()
    down = (EstateStoreUnavailable, *unavailable)

    @router.get("/api/estate/portfolio")
    def estate_portfolio(request: Request) -> dict[str, Any]:
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
            body = service.portfolio(tenant(), parsed, lambda code: access(request, code) is None)
        except EstateRefusal as error:
            headers = {"WWW-Authenticate": "Bearer"} if error.status == 401 else None
            raise HTTPException(status_code=error.status, detail=refusal(error.code), headers=headers) from error
        except down as error:
            raise HTTPException(status_code=503, detail=refusal("ESTATE_STORE_UNAVAILABLE")) from error
        return jsonable_encoder(body)

    return router
