"""5c (spec section 4.2; D-5C.7, PF6): `GET /api/portfolio/month?month=YYYY-MM`, the month explained.

Refusal order: the read and the served tenant (503 `DEEP_DIVE_UNAVAILABLE`); with the real-data switch on, a signed-in
person of that tenant (401 `PERSON_REQUIRED`; off, no person is needed, RC7); the month (422 `BAD_MONTH`); a store
fault (503). The 200 body is `month_view`'s JSON. Every answer carries `Cache-Control: no-store`; every refusal is
`{"code", "text"}`, its text an SC-1 statement.
"""
from __future__ import annotations

from datetime import date
import logging
from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse

from assetops_backend.accounts.principal import person_from_request
from assetops_backend.deep_dive.period import BAD_RANGE, refused_text
from assetops_backend.deep_dive.sites import SiteRef
from assetops_backend.deep_dive.read import BAD_MONTH, BadMonth, BadRange, DeepDiveRead
from assetops_backend.deep_dive.tables import DAY_PATTERN, NO_STORE, PERIOD_ROUTE, RANGE_FROM, RANGE_TO, ROUTE, SITES_ROUTE
from assetops_backend.i18n import State, message, render

if TYPE_CHECKING:
    from assetops_backend.accounts.service import AccountService

_log = logging.getLogger(__name__)
UNAVAILABLE_CODE = "DEEP_DIVE_UNAVAILABLE"
PERSON_REQUIRED = "PERSON_REQUIRED"


def _refusal(status: int, code: str, text: str) -> JSONResponse:
    return JSONResponse(status_code=status, headers=NO_STORE, content={"code": code, "text": text})


def _refused(status: int, code: str) -> JSONResponse:
    return _refusal(status, code, render(message("deep_dive.refused", code=State(code))))


def _range_refused(code: str) -> JSONResponse:
    """E2's and E1's own 422 (`portfolio_period.refused`); `_refused` keeps the 503."""
    return _refusal(422, code, refused_text(code))


def _day(raw: str | None) -> date:
    if raw is None or DAY_PATTERN.fullmatch(raw) is None:
        raise BadRange(BAD_RANGE)
    try:
        return date.fromisoformat(raw)
    except ValueError:
        raise BadRange(BAD_RANGE) from None


def _person_required() -> JSONResponse:
    return _refusal(401, PERSON_REQUIRED, render(message("person.person_required")))


def build_deep_dive_router(read: DeepDiveRead | None, *, accounts: AccountService | None, real_data: bool,
                           unavailable: tuple[type[BaseException], ...]) -> APIRouter:
    router = APIRouter()

    def answer(request: Request, body_of) -> Any:
        """The refusal order every route here shares (module docstring); `body_of(tenant, registry)` reads."""
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
            body = body_of(tenant, registry)
        except BadMonth:
            return _refused(422, BAD_MONTH)
        except BadRange as error:
            return _range_refused(error.code)
        except unavailable:
            return _refused(503, UNAVAILABLE_CODE)
        except AssertionError:  # E1's sum check (I7): a bridge break is logged and refused, never served
            _log.exception(UNAVAILABLE_CODE)
            return _refused(503, UNAVAILABLE_CODE)
        return JSONResponse(status_code=200, content=body, headers=NO_STORE)

    def names_of(registry) -> dict[str, str]:
        return {s.site_code: s.name for s in registry.imported_sites()}

    @router.get(ROUTE)
    def portfolio_month(request: Request, month: str | None = None) -> Any:
        return answer(request, lambda tenant, registry: read.month(tenant, month, names_of(registry)))

    @router.get(PERIOD_ROUTE)
    def portfolio_period(request: Request, first: str | None = Query(None, alias=RANGE_FROM),
                         last: str | None = Query(None, alias=RANGE_TO)) -> Any:
        return answer(request, lambda tenant, registry: read.period(tenant, _day(first), _day(last),
                                                                    names_of(registry)))

    @router.get(SITES_ROUTE)
    def portfolio_sites(request: Request, first: str | None = Query(None, alias=RANGE_FROM),
                        last: str | None = Query(None, alias=RANGE_TO)) -> Any:
        def body(tenant, registry):
            refs = tuple(SiteRef(s.site_code, s.name, s.site_type) for s in registry.imported_sites())
            return read.sites(tenant, _day(first), _day(last), refs)
        return answer(request, body)

    return router


__all__ = ["PERIOD_ROUTE", "ROUTE", "SITES_ROUTE", "build_deep_dive_router"]
