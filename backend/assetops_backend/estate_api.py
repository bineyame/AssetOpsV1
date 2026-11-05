"""W3-01 estate roots (`A-estate-index-scope`, `A-estate-action-summary`): read-only, no Site parameter.

`GET /api/estate/scope?from=&to=&known_at=`, `GET /api/estate/findings?from=&to=&known_at=&lens=&state=&limit=&cursor=`
and `GET /api/estate/actions?from=&to=&known_at=&limit=&cursor=`. Order of checks (Run 6 reading 3):

1. `authenticate(request)`: 401 `UNAUTHENTICATED` with `WWW-Authenticate: Bearer`, before any tenant lookup,
   Site enumeration, parameter parsing or cursor decoding.
2. The strict shared parser: typed 422 with no rows or count.
3. One read-only snapshot: the tenant comes only from the server's registry; each imported candidate Site is
   admitted by the existing per-Site `access(request, site_code)` before any value enters a response or digest, so
   estate roots never answer 403/404 and never disclose a denied Site. 409 `ESTATE_BASIS_CHANGED` /
   `ESTATE_SELECTION_INCONSISTENT`, 503 `ESTATE_STORE_UNAVAILABLE`.
"""

from __future__ import annotations

from typing import Any, Callable
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.encoders import jsonable_encoder

from assetops_backend import perf
from assetops_backend.chain.response_store import ResponseStore, StoredRoute, finish, parsed_key
from assetops_backend.estate.index import EstateIndexService
from assetops_backend.estate.scope import EstateRefusal, EstateStoreUnavailable, MESSAGES, parse_request
from assetops_backend.finding_api import Access, development_access

FINDINGS = "/api/estate/findings"

# request -> None to admit, else 401.
Authenticate = Callable[[Request], "int | None"]


def development_authenticate(request: Request) -> int | None:
    return None


def build_estate_router(service: EstateIndexService | None, tenant: Callable[[], UUID | None], *,
                        authenticate: Authenticate = development_authenticate, access: Access = development_access,
                        unavailable: tuple[type[BaseException], ...] = (),
                        responses: ResponseStore | None = None) -> APIRouter:
    """`responses` (CH-5c) stores the Findings index; the scope and Action roots are not stored routes."""
    router = APIRouter()
    down = (EstateStoreUnavailable, *unavailable)

    def store_down() -> HTTPException:
        return HTTPException(status_code=503, detail={"code": "ESTATE_STORE_UNAVAILABLE",
                                                      "message": MESSAGES["ESTATE_STORE_UNAVAILABLE"],
                                                      "rows": None, "total_count": None})

    def serve(kind: str, request: Request, route: str | None = None) -> Any:
        if authenticate(request) == 401:
            raise HTTPException(status_code=401, headers={"WWW-Authenticate": "Bearer"},
                                detail={"code": "UNAUTHENTICATED", "message": MESSAGES["UNAUTHENTICATED"],
                                        "rows": None, "total_count": None})
        try:
            parsed = parse_request(kind, request.query_params.multi_items())
            if service is None:
                raise store_down()
            admit = lambda code: access(request, code) is None  # noqa: E731
            tenant_id = tenant()
            if route is not None and responses is not None and tenant_id is not None:
                return responses.serve(StoredRoute(route, tenant_id, parsed_key(parsed), admit=admit),
                                       lambda: {route: jsonable_encoder(getattr(service, kind)(tenant_id, parsed,
                                                                                               admit))})
            body = getattr(service, kind)(tenant_id, parsed, admit)
        except EstateRefusal as error:
            headers = {"WWW-Authenticate": "Bearer"} if error.status == 401 else None
            raise HTTPException(status_code=error.status, detail=error.detail, headers=headers) from error
        except down as error:
            raise store_down() from error
        return jsonable_encoder(body)

    @router.get("/api/estate/scope")
    def estate_scope(request: Request) -> dict[str, Any]:
        return serve("scope", request)

    @router.get(FINDINGS)
    def estate_findings(request: Request, response: Response) -> dict[str, Any]:
        with perf.route(FINDINGS, response):  # CH-5c Q7: one `assetops.perf` line per request, no semantics
            out = serve("findings", request, FINDINGS)
        return finish(out, response) if isinstance(out, Response) else out

    @router.get("/api/estate/actions")
    def estate_actions(request: Request) -> dict[str, Any]:
        return serve("actions", request)

    return router
