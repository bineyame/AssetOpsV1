"""Gated Simulator Lab API surface (product side).

`create_app` builds this router only when `simulator_lab.enabled` is true. When
the flag is false the router is never mounted, so every
`/api/simulator-lab/*` path is genuinely unserved and returns 404 rather than
being served-but-empty or hidden behind UI navigation.

This module is one of the two allowlisted places in the tree that may spell a
simulator URL; `tools/check-architecture.ps1` fails the build if one appears
anywhere else. Lab-only paths therefore hang off `SIMULATOR_LAB_API_PREFIX`,
which keeps them behind the single existing chokepoint instead of introducing
a second one.

This module owns no simulated world, no private simulator truth, and no run
execution. Its Site Templates endpoints read shipped, read-only configuration
through the `SiteTemplateCatalog` port: they return template archetypes, never
Sites, and never operational values. No template endpoint writes anything, and
no route here edits, renames, duplicates, or deletes anything.

One route writes: creating a Site from a template. Authoring a simulated Site
is a Simulator Lab capability, so the create route lives behind the gate and
under the Lab prefix, and it is absent from the served route inventory when
the flag is false. What it creates is not a Lab object: it is a normal product
Site in the product store, carrying simulated source mode as provenance, and
it stays fully visible when the Lab is switched off. There is no publish step
and no promote step, because it was a product object from the instant it
existed.

The create path runs handler to service to port to adapter, with no shortcut
to storage. This module names no file, no path, and no serialization format.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, HTTPException

from assetops_backend.sites.models import SiteTemplate
from assetops_backend.sites.ports import (
    SiteConfigurationInvalid,
    SiteIdentityConflict,
    SiteRepository,
    SiteStoreUnavailable,
    SiteTemplateCatalog,
    SiteTemplateConfigurationInvalid,
    SiteTemplateNotFound,
    SiteTemplateStoreUnavailable,
)
from assetops_backend.sites.service import (
    SiteCreationService,
    SiteTemplateCatalogService,
)
from assetops_backend.sites.site_parsing import parse_create_site_request
from assetops_backend.sites_api import site_summary

SIMULATOR_LAB_API_PREFIX = "/api/simulator-lab"

SITE_TEMPLATES_ROUTE = "/site-templates"
SITE_TEMPLATE_DETAIL_ROUTE = "/site-templates/{template_id}"
CREATE_SITE_ROUTE = "/sites"

# Refusal codes. The message is the product copy a user reads; the code is what
# a client switches on, so neither has to be parsed out of the other.
REFUSAL_INVALID_REQUEST = "SITE_REQUEST_INVALID"
REFUSAL_SITE_ID_IN_USE = "SITE_ID_IN_USE"
REFUSAL_TEMPLATE_NOT_FOUND = "TEMPLATE_NOT_FOUND"
REFUSAL_STORE_UNAVAILABLE = "SITE_STORE_UNAVAILABLE"


def _refusal(code: str, message: str) -> dict[str, object]:
    """A refusal a screen can render, rather than a stack trace."""
    return {"code": code, "message": message}


def _summarize(template: SiteTemplate) -> dict[str, object]:
    """Listing shape: template identity plus what kind of Site it would make.

    No `site_id`, no lifecycle status, no location, no timezone, no source
    mode: a template has none of those, so the wire shape has no field for
    them to leak into.
    """
    return {
        "template_id": template.template_id,
        "template_version": template.template_version,
        "display_name": template.display_name,
        "site_type": template.foundation.site_type,
        "summary": template.foundation.summary,
    }


def _detail(template: SiteTemplate) -> dict[str, object]:
    return {
        **_summarize(template),
        "components": [
            {
                "component_id": component.component_id,
                "component_type": component.component_type,
                "display_name": component.display_name,
                "rating": (
                    None
                    if component.rating is None
                    else {
                        "value": component.rating.value,
                        "unit": component.rating.unit,
                    }
                ),
            }
            for component in template.foundation.components
        ],
    }


def build_simulator_lab_router(
    catalog: SiteTemplateCatalog, repository: SiteRepository
) -> APIRouter:
    """Build the gated router around the injected ports.

    Both arrive as ports. This module never learns whether templates or Sites
    are files, rows, or objects, and it never imports an adapter.
    """
    service = SiteTemplateCatalogService(catalog)
    creation = SiteCreationService(repository, catalog)
    router = APIRouter(prefix=SIMULATOR_LAB_API_PREFIX, tags=["simulator-lab"])

    @router.get("/status")
    def read_simulator_lab_status() -> dict[str, object]:
        """Report that the Simulator Lab surface is served in this build.

        This is a statement about the gate, not about any Site, device,
        source, or simulator run. No run exists, so none can be started,
        inspected, rerun, or compared against simulator truth.
        """
        return {
            "simulator_lab_enabled": True,
            "run_execution": "not_implemented",
            "truth_overlays": "not_implemented",
        }

    @router.get(SITE_TEMPLATES_ROUTE)
    def list_site_templates() -> dict[str, object]:
        """List the shipped Site configuration templates."""
        try:
            templates = service.list_templates()
        except (
            SiteTemplateConfigurationInvalid,
            SiteTemplateStoreUnavailable,
        ) as error:
            raise HTTPException(status_code=503, detail=str(error)) from error

        return {"templates": [_summarize(template) for template in templates]}

    @router.get(SITE_TEMPLATE_DETAIL_ROUTE)
    def read_site_template(template_id: str) -> dict[str, object]:
        """Return the Foundation content one shipped template would produce."""
        try:
            template = service.get_template(template_id)
        except SiteTemplateNotFound as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        except (
            SiteTemplateConfigurationInvalid,
            SiteTemplateStoreUnavailable,
        ) as error:
            raise HTTPException(status_code=503, detail=str(error)) from error

        return _detail(template)

    @router.post(CREATE_SITE_ROUTE, status_code=201)
    def create_site(request: Any = Body(default=None)) -> dict[str, object]:
        """Create one Site from a shipped template.

        The request body is parsed by the domain's own strict parser rather
        than by a framework model, so that a refusal is product copy naming
        what is wrong and what would be acceptable, instead of a validation
        dump. Nothing is written unless the fully materialized document
        passes the same parser that reads stored documents.
        """
        try:
            parsed = parse_create_site_request(request)
        except SiteConfigurationInvalid as error:
            raise HTTPException(
                status_code=422,
                detail=_refusal(REFUSAL_INVALID_REQUEST, str(error)),
            ) from error

        try:
            record = creation.create_site_from_template(parsed)
        except SiteTemplateNotFound as error:
            raise HTTPException(
                status_code=404,
                detail=_refusal(
                    REFUSAL_TEMPLATE_NOT_FOUND,
                    f"No shipped site template with template ID "
                    f"{parsed.template_id!r} exists, so no site was created. "
                    "Choose a template from the shipped catalog.",
                ),
            ) from error
        except SiteIdentityConflict as error:
            raise HTTPException(
                status_code=409,
                detail=_refusal(
                    REFUSAL_SITE_ID_IN_USE,
                    f"{error} Site IDs are unique across every site store "
                    "and are compared without regard to case, so the same ID "
                    "in a different capitalisation is the same site. Nothing "
                    "was written. Choose a different site ID.",
                ),
            ) from error
        except SiteConfigurationInvalid as error:
            raise HTTPException(
                status_code=422,
                detail=_refusal(REFUSAL_INVALID_REQUEST, str(error)),
            ) from error
        except (SiteStoreUnavailable, SiteTemplateStoreUnavailable) as error:
            raise HTTPException(
                status_code=503,
                detail=_refusal(
                    REFUSAL_STORE_UNAVAILABLE,
                    f"{error} Nothing was written.",
                ),
            ) from error

        return site_summary(record)

    return router
