"""S7-01a configured-battery boundary routes (`I-asset-boundary-read`, `D-2026-10-16-a-s7-health`).

`GET /api/sites/{site_code}/battery` - Site entry: configured battery asset IDs from the effective
basis, or typed `NOT_CONFIGURED` without a fabricated asset ID.
`GET /api/sites/{site_code}/assets/{asset_id}/battery` - one battery's boundary: basis/binding IDs and
`UNKNOWN` physical condition with named missing causal inputs.

Checks: 401 / 403 with the Finding route seam (`finding_api.Access`); 404 for a foreign or unknown
Site; 422 `INVALID_ASSET_ID` for a malformed ID; 404 for an asset that is not a battery of the
effective basis; 503 when the Foundation store cannot be read; 409 when no Foundation revision is
effective now. No refusal returns a condition row.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request

from assetops_backend.finding_api import ACCESS_BASIS, Access, development_access
from assetops_backend.sites.battery_boundary import AssetNotInBasis, battery_detail, battery_entry
from assetops_backend.sites.cutover import ImportedSiteRegistry
from assetops_backend.sites.foundation_records import FoundationStoreError
from assetops_backend.sites.foundation_service import FoundationRefused, FoundationView
from assetops_backend.sites.ports import SiteStoreUnavailable


def build_asset_boundary_router(registry: ImportedSiteRegistry, access: Access = development_access,
                                access_basis: str = ACCESS_BASIS) -> APIRouter:
    router = APIRouter()

    def unavailable(message: str) -> HTTPException:
        return HTTPException(status_code=503, detail={"code": "ASSET_BOUNDARY_UNAVAILABLE", "message": message,
                                                      "physical_condition": None})

    def effective_view(request: Request, site_code: str) -> FoundationView:
        refusal = access(request, site_code)
        if refusal == 401:
            raise HTTPException(status_code=401, headers={"WWW-Authenticate": "Bearer"},
                                detail={"code": "UNAUTHENTICATED", "message": "Sign in to read Site assets."})
        if refusal == 403:
            raise HTTPException(status_code=403, detail={"code": "SITE_SCOPE_FORBIDDEN",
                                                         "message": f"No access to Site {site_code!r}."})
        service = registry.service
        try:
            site = registry.imported(site_code)
            if site is not None and service is None:
                raise unavailable("No product Foundation store is configured.")
            tenant = registry.tenant() if site is not None else None
            if site is None or tenant is None:
                raise HTTPException(status_code=404, detail=f"No imported Site {site_code!r} in this tenant.")
            return service.read(site, tenant, None, None)
        except (SiteStoreUnavailable, FoundationStoreError) as error:
            raise unavailable(str(error)) from error
        except FoundationRefused as error:
            raise HTTPException(status_code=409, detail={"code": "FOUNDATION_BASIS_UNAVAILABLE",
                                                         "message": str(error), "physical_condition": None}
                                ) from error

    @router.get("/api/sites/{site_code}/battery")
    def battery(request: Request, site_code: str) -> dict[str, Any]:
        view = effective_view(request, site_code)
        return battery_entry(view, view.now, access_basis)

    @router.get("/api/sites/{site_code}/assets/{asset_id}/battery")
    def battery_asset(request: Request, site_code: str, asset_id: str) -> dict[str, Any]:
        view = effective_view(request, site_code)
        try:
            wanted = UUID(asset_id)
        except ValueError as error:
            raise HTTPException(status_code=422, detail={"code": "INVALID_ASSET_ID",
                                                         "message": f"{asset_id!r} is not an asset ID."}) from error
        try:
            return battery_detail(view, wanted, view.now, access_basis)
        except AssetNotInBasis as error:
            raise HTTPException(status_code=404, detail={"code": "ASSET_NOT_IN_EFFECTIVE_BASIS",
                                                         "message": str(error), "physical_condition": None}
                                ) from error

    return router
