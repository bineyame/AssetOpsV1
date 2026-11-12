"""PR-2a (BL-68): `GET /api/sites/{site_code}/prices?need=&known_at=`, the read-only Site price page.

The body is `financials.price_page.compose` over one `AssumptionReadService.series` read per stored key the Site
type uses (current, or at the `known_at` recorded cutoff). Scope and refusals are the price read's
(`financial_read_api`): 401 / 403 from the access seam, 404 for a Site the tenant does not know, 422
`INSTANT_NOT_ZONED`, 503 `ASSUMPTION_STORE_UNAVAILABLE` without a database or on a store failure.
Nothing here writes; PR-3 adds the entry route and the body's `entry` block.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Callable

from fastapi import APIRouter, HTTPException, Request
from fastapi.encoders import jsonable_encoder

from assetops_backend.finding_api import ACCESS_BASIS, Access, development_access
from assetops_backend.financials.assumption_read import AssumptionReadService
from assetops_backend.financials.price_page import compose, stored_keys
from assetops_backend.work_api import Principal, no_service_principal

#: Site code -> `(site_code, site_name, site_type, timezone, tenant_id, site_id)`, or None for an unknown Site.
SiteFacts = Callable[[str], "tuple[str, str, str, str, Any, Any] | None"]


def registry_site_facts(registry: Any) -> SiteFacts:
    """The imported-Site registry's facts for one code (`sites.cutover.ImportedSiteRegistry.imported`)."""
    def facts(site_code: str) -> tuple[str, str, str, str, Any, Any] | None:
        site = registry.imported(site_code)
        return None if site is None else (site.site_code, site.name, site.site_type, site.timezone,
                                          site.tenant_id, site.id)
    return facts


def build_price_page_router(reads: AssumptionReadService | None, site: SiteFacts,
                            unavailable: tuple[type, ...] = (), access: Access = development_access,
                            access_basis: str = ACCESS_BASIS, entry_principal: Principal = no_service_principal,
                            clock: Callable[[], datetime] = lambda: datetime.now(UTC)) -> APIRouter:
    """`entry_principal` is the same injected switch the PR-3 entry route uses (`ASSETOPS_OPERATIONAL_ENTRY`); it
    only decides the body's `entry` block and sign-in sentence here. `clock` is a server-side injection (Site-local
    "today" for the form's default); no request field sets it."""
    router = APIRouter()

    def store_down(message: str) -> HTTPException:
        return HTTPException(status_code=503, detail={"code": "ASSUMPTION_STORE_UNAVAILABLE", "message": message})

    @router.get("/api/sites/{site_code}/prices")
    def page(request: Request, site_code: str, need: str | None = None,
             known_at: datetime | None = None) -> dict[str, Any]:
        refusal = access(request, site_code)
        if refusal == 401:
            raise HTTPException(status_code=401, headers={"WWW-Authenticate": "Bearer"},
                                detail={"code": "UNAUTHENTICATED", "message": "Sign in to read Site prices."})
        if refusal == 403:
            raise HTTPException(status_code=403, detail={"code": "SITE_SCOPE_FORBIDDEN",
                                                         "message": f"No access to Site {site_code!r}."})
        try:
            found = site(site_code)
        except unavailable as error:
            raise store_down(str(error)) from error
        if found is None or refusal == 404:
            raise HTTPException(status_code=404, detail=f"No imported Site {site_code!r} in this tenant.")
        if known_at is not None and (known_at.tzinfo is None or known_at.utcoffset() is None):
            raise HTTPException(status_code=422, detail={"code": "INSTANT_NOT_ZONED",
                                                         "message": "known_at must carry a timezone offset."})
        if reads is None:
            raise store_down("No product database is configured.")
        code, name, site_type, timezone, tenant_id, site_id = found
        try:
            series = {key: reads.series(tenant_id, site_id, key, valid_at=None, recorded_at=known_at)
                      for key in stored_keys(site_type)}
        except unavailable as error:
            raise store_down(str(error)) from error
        entry_on = entry_principal(request, site_code) is not None
        return jsonable_encoder(compose(site_code=code, site_name=name, site_type=site_type, timezone=timezone,
                                        series=series, need=need, known_at=known_at, access_basis=access_basis,
                                        entry_on=entry_on, now=clock()))

    return router
