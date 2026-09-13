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
no create, instantiate, upload, import, edit, or delete route exists, because
nothing in this slice can produce a Site.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from assetops_backend.sites.models import SiteTemplate
from assetops_backend.sites.ports import (
    SiteTemplateCatalog,
    SiteTemplateConfigurationInvalid,
    SiteTemplateNotFound,
    SiteTemplateStoreUnavailable,
)
from assetops_backend.sites.service import SiteTemplateCatalogService

SIMULATOR_LAB_API_PREFIX = "/api/simulator-lab"

SITE_TEMPLATES_ROUTE = "/site-templates"
SITE_TEMPLATE_DETAIL_ROUTE = "/site-templates/{template_id}"


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


def build_simulator_lab_router(catalog: SiteTemplateCatalog) -> APIRouter:
    """Build the gated router around an injected template catalog.

    The catalog arrives as a port. This module never learns whether templates
    are files, rows, or objects, and it never imports an adapter.
    """
    service = SiteTemplateCatalogService(catalog)
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

    return router
