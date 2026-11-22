"""5c (spec section 4.2; D-5C.7, PF6): `GET /api/portfolio/month?month=YYYY-MM`, the month explained.

Refusal order: the read and the served tenant (503 `DEEP_DIVE_UNAVAILABLE`); with the real-data switch on, a signed-in
person of that tenant (401 `PERSON_REQUIRED`; off, no person is needed, RC7); the month (422 `BAD_MONTH`); a store
fault (503). The 200 body is `month_view`'s JSON. Every answer carries `Cache-Control: no-store`; every refusal is
`{"code", "text"}`, its text an SC-1 statement.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from assetops_backend.accounts.principal import person_from_request
from assetops_backend.deep_dive.read import BAD_MONTH, BadMonth, DeepDiveRead
from assetops_backend.deep_dive.tables import NO_STORE, ROUTE
from assetops_backend.i18n import State, message, render

if TYPE_CHECKING:
    from assetops_backend.accounts.service import AccountService

UNAVAILABLE_CODE = "DEEP_DIVE_UNAVAILABLE"
PERSON_REQUIRED = "PERSON_REQUIRED"


def _refusal(status: int, code: str, text: str) -> JSONResponse:
    return JSONResponse(status_code=status, headers=NO_STORE, content={"code": code, "text": text})


def _refused(status: int, code: str) -> JSONResponse:
    return _refusal(status, code, render(message("deep_dive.refused", code=State(code))))


def _person_required() -> JSONResponse:
    return _refusal(401, PERSON_REQUIRED, render(message("person.person_required")))


def build_deep_dive_router(read: DeepDiveRead | None, *, accounts: AccountService | None, real_data: bool,
                           unavailable: tuple[type[BaseException], ...]) -> APIRouter:
    router = APIRouter()

    @router.get(ROUTE)
    def portfolio_month(request: Request, month: str | None = None) -> Any:
        if read is None:
            return _refused(503, UNAVAILABLE_CODE)
        registry = request.app.state.site_registry
        try:
            tenant = registry.tenant()
            if tenant is None:
                return _refused(503, UNAVAILABLE_CODE)
            if real_data:
                if accounts is None:
                    return _refused(503, UNAVAILABLE_CODE)
                person = person_from_request(request, accounts)
                if person is None or person.tenant_id != tenant.id:
                    return _person_required()
            names = {s.site_code: s.name for s in registry.imported_sites()}
            body = read.month(tenant, month, names)
        except BadMonth:
            return _refused(422, BAD_MONTH)
        except unavailable:
            return _refused(503, UNAVAILABLE_CODE)
        return JSONResponse(status_code=200, content=body, headers=NO_STORE)

    return router


__all__ = ["ROUTE", "build_deep_dive_router"]
