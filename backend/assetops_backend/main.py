"""FastAPI application root for AssetOps.

The app is built by `create_app`, which reads the file-backed feature flags in
`config/app-config.json` and decides which routers are mounted. Gating happens
at the serving boundary: when `simulator_lab.enabled` is false the Simulator Lab
router is never included, so its paths do not exist on the app at all.

No Site schema, simulator execution, ingestion, analytics, configuration
editing, or Findings are served, and no endpoint here implies that operational
evidence exists.
"""

from __future__ import annotations

from fastapi import APIRouter, FastAPI

from assetops_backend.config import FeatureFlags, load_feature_flags
from assetops_backend.simulator_lab_api import build_simulator_lab_router
from assetops_backend.sites.composition import build_site_template_catalog
from assetops_backend.sites.ports import SiteTemplateCatalog

health_router = APIRouter()


@health_router.get("/api/health")
def read_health() -> dict[str, str]:
    """Report that the backend process is serving.

    This is a liveness signal about the service only. It is not evidence about
    any Site, device, source, or simulator run.
    """
    return {"status": "ok", "service": "assetops-backend"}


def create_app(
    flags: FeatureFlags | None = None,
    *,
    site_template_catalog: SiteTemplateCatalog | None = None,
) -> FastAPI:
    """Build the application for a given set of feature flags.

    Operator and product surfaces are always mounted: the Simulator Lab gate
    controls simulator surfaces and execution only, never Site semantics,
    evidence, provenance, or operator routes.

    The template catalog is composed here and injected as a port, so no route
    module imports a storage adapter and a test can supply a fake catalog
    without touching the shipped configuration root. The catalog is built only
    when the gate is open: a closed gate serves no template surface and must
    not touch the store to find that out.
    """
    resolved_flags = load_feature_flags() if flags is None else flags

    app = FastAPI(title="AssetOps", version="0.0.0")
    app.include_router(health_router)

    if resolved_flags.simulator_lab_enabled:
        catalog = (
            build_site_template_catalog()
            if site_template_catalog is None
            else site_template_catalog
        )
        app.include_router(build_simulator_lab_router(catalog))

    return app


app = create_app()
