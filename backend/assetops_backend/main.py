"""FastAPI application root for AssetOps.

The app is built by `create_app`, which reads the file-backed feature flags in
`config/app-config.json` and decides which routers are mounted. Gating happens
at the serving boundary: when `simulator_lab.enabled` is false the Simulator Lab
router is never included, so its paths do not exist on the app at all.

The operator Sites API is mounted in both gate states, because the gate covers
simulator surfaces and execution, never objects or stores. Creating a Site is a
Simulator Lab capability and its route lives on the gated router.

Simulator EXECUTION is served behind the gate since T022, and this module cannot
compose it. Only `host/` may import both a kernel and the product, and nothing may
import `host/`, so an execution port arrives here as an argument or not at all:
`create_app` takes one, passes it to the gated router, and a build without one
serves the execution routes answering that no port is composed. The composed
entry point is the leaf's own application module.

No ingestion, analytics, configuration editing, or Findings are served, and no
endpoint here implies that operational evidence exists.
"""

from __future__ import annotations

from fastapi import APIRouter, FastAPI

from assetops_backend.config import FeatureFlags, load_feature_flags
from assetops_backend.runs.composition import build_run_repository
from assetops_backend.runs.execution_ports import LabExecutionPort
from assetops_backend.runs.ports import SimulationRunRepository
from assetops_backend.runs.profiles import (
    MODEL_PROFILES,
    PUBLICATION_PROFILES,
)
from assetops_backend.scenarios.composition import build_scenario_repository
from assetops_backend.scenarios.ports import ScenarioDefinitionRepository
from assetops_backend.simulator_lab_api import build_simulator_lab_router
from assetops_backend.sites.composition import (
    build_site_repository,
    build_site_template_catalog,
)
from assetops_backend.sites.ports import SiteRepository, SiteTemplateCatalog
from assetops_backend.sites_api import build_sites_router

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
    site_repository: SiteRepository | None = None,
    scenario_repository: ScenarioDefinitionRepository | None = None,
    run_repository: SimulationRunRepository | None = None,
    execution: LabExecutionPort | None = None,
) -> FastAPI:
    """Build the application for a given set of feature flags.

    Operator and product surfaces are always mounted: the Simulator Lab gate
    controls simulator surfaces and execution only, never Site semantics,
    evidence, provenance, or operator routes.

    The ports are composed here and injected, so no route module imports a
    storage adapter and a test can supply fakes without touching a
    configuration root or writing to disk.

    The template catalog is built only when the gate is open: a closed gate
    serves no template surface and no create route, and must not touch the
    catalog to find that out. The Site repository is built in both states,
    because the Sites index is an operator capability that the gate does not
    reach.

    The scenario repository is built only when the gate is open, for the same
    reason as the template catalog and not for the reason the Site repository
    is built in both. Scenarios are a Simulator Lab surface: no operator route
    reads one, so a closed gate must not touch the scenario store to discover
    that it serves no scenario route. The store still exists and is still
    readable; nothing about a scenario is gated except the surfaces that show
    it.

    The run store is built only when the gate is open too, and for a stronger
    version of the same reason: setting a run up is a Simulator Lab
    capability, so a closed build must not so much as open the directory runs
    would be written to. The versioned profiles are passed in from the one
    module that declares them, so a route never reaches for a catalog it
    could also have imported.

    `execution` is injected and never built here. It is the one port this module
    could not compose even if it wanted to: only the neutral leaf may import a
    kernel, and nothing may import the leaf. It is also only passed on when the
    gate is open, which is what makes a closed build unable to reach a kernel
    however it was composed - the gate covers execution, so a closed gate hands
    the router nothing.
    """
    resolved_flags = load_feature_flags() if flags is None else flags

    app = FastAPI(title="AssetOps", version="0.0.0")
    app.include_router(health_router)

    repository = build_site_repository() if site_repository is None else site_repository
    app.include_router(build_sites_router(repository))

    if resolved_flags.simulator_lab_enabled:
        catalog = (
            build_site_template_catalog()
            if site_template_catalog is None
            else site_template_catalog
        )
        scenarios = (
            build_scenario_repository()
            if scenario_repository is None
            else scenario_repository
        )
        runs = build_run_repository() if run_repository is None else run_repository
        app.include_router(
            build_simulator_lab_router(
                catalog,
                repository,
                scenarios,
                runs,
                MODEL_PROFILES,
                PUBLICATION_PROFILES,
                execution,
            )
        )

    return app


app = create_app()
