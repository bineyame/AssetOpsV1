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

Ingestion and the Site > Evidence read model (T027) are mounted in both gate
states: accepted evidence is a product capability, and the gate covers
simulator surfaces only. The analytics read models (T028: the capability
declaration, dispatch assessments, Findings and their revisions) are mounted
in both gate states beside them. No configuration editing is served.
"""

from __future__ import annotations

from typing import Callable, Sequence

from fastapi import APIRouter, FastAPI

from assetops_backend.analytics.composition import build_assessment_store
from assetops_backend.analytics.ports import AssessmentStore
from assetops_backend.analytics.service import AssessmentService
from assetops_backend.analytics_api import build_analytics_router
from assetops_backend.config import (
    DEVELOPMENT_TENANT_SLUG,
    FeatureFlags,
    database_url,
    load_feature_flags,
)
from assetops_backend.evidence.composition import build_evidence_store
from assetops_backend.evidence.ports import EvidenceStore
from assetops_backend.evidence.service import Clock, IngestionService, system_clock
from assetops_backend.evidence_api import build_evidence_router
from assetops_backend.foundation_api import build_foundation_router
from assetops_backend.runs.commit_ports import CommittedArtifactStore
from assetops_backend.runs.composition import build_commit_store, build_run_repository
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
    build_foundation_store,
    build_site_repository,
    build_site_template_catalog,
    legacy_site_documents,
)
from assetops_backend.sites.cutover import (
    ImportedSiteRegistry,
    LegacySiteGate,
    ProductSiteDirectory,
)
from assetops_backend.sites.foundation_records import FoundationStore
from assetops_backend.sites.foundation_service import (
    FoundationService,
    LegacyDocument,
    utc_now,
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
    evidence_store: EvidenceStore | None = None,
    clock: Clock | None = None,
    commit_store: CommittedArtifactStore | None = None,
    assessment_store: AssessmentStore | None = None,
    foundation_store: FoundationStore | None = None,
    foundation_clock: Callable[[], object] | None = None,
    legacy_documents: Callable[[], Sequence[LegacyDocument]] | None = None,
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

    The evidence store and the ingestion service are built in both gate
    states: ingestion is the one path that writes accepted evidence, for any
    source, and Site > Evidence must stay readable with the Lab gated off.
    `clock` is ingestion's clock (it assigns `received_at`). The service is
    exposed as `app.state.ingestion` so the gated Commit route can release
    through the same `ingest` method rather than a second path.

    The commit store (T027, D4) is built only when the gate is open, like the
    run store: committing a run's stage is a Lab act, so a closed build never
    opens the directory sealed artifacts are filed in. Accepted evidence does
    not depend on it - the Evidence routes read the evidence store alone.

    S1-01 Foundation-only cutover (D-2026-10-07). The product composition
    (no injected Site repository) always builds the PostgreSQL Foundation
    store from the required `DATABASE_URL`; with no URL that store answers
    as unavailable, so the product path fails closed. Product Site reads go
    through the tenant-scoped `ProductSiteDirectory`; every legacy
    file-backed surface (Evidence, Overview, analytics, ingestion, Lab)
    receives the `LegacySiteGate`, which refuses imported codes. A caller
    that injects its own Site repository and no Foundation store is a
    legacy-only test composition: no code is imported there and the
    Foundation routes answer that no store is composed.
    """
    resolved_flags = load_feature_flags() if flags is None else flags

    app = FastAPI(title="AssetOps", version="0.0.0")
    app.include_router(health_router)

    legacy_repository = (
        build_site_repository() if site_repository is None else site_repository
    )
    if foundation_store is None and site_repository is None:
        foundation_store = build_foundation_store(database_url())
    registry = ImportedSiteRegistry(
        None
        if foundation_store is None
        else FoundationService(
            foundation_store,
            DEVELOPMENT_TENANT_SLUG,
            utc_now if foundation_clock is None else foundation_clock,
        )
    )
    # The product read router: imported codes from Postgres, listed once;
    # every other code from its legacy YAML document.
    product_sites = ProductSiteDirectory(
        legacy_repository,
        registry,
        legacy_site_documents if legacy_documents is None else legacy_documents,
    )
    # Every legacy file-backed surface below sees imported codes refused.
    repository = LegacySiteGate(legacy_repository, registry)
    app.state.legacy_site_gate = repository
    app.include_router(build_sites_router(product_sites))
    app.include_router(build_foundation_router(registry, legacy_repository))

    ingestion = IngestionService(
        build_evidence_store() if evidence_store is None else evidence_store,
        repository,
        system_clock if clock is None else clock,
    )
    app.state.ingestion = ingestion
    assessments = AssessmentService(
        ingestion.store,
        (
            build_assessment_store(persistent=evidence_store is None)
            if assessment_store is None
            else assessment_store
        ),
        repository.get_site,
        system_clock if clock is None else clock,
    )
    app.state.assessments = assessments
    ingestion.add_completed_listener(assessments.assess_site)
    app.include_router(
        build_evidence_router(ingestion, repository, assessments.card_assessments)
    )
    app.include_router(build_analytics_router(assessments, ingestion.store, repository))

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
        commits = build_commit_store() if commit_store is None else commit_store
        app.include_router(
            build_simulator_lab_router(
                catalog,
                repository,
                scenarios,
                runs,
                MODEL_PROFILES,
                PUBLICATION_PROFILES,
                execution,
                commits,
                imported_site_check=repository.refuse_if_imported,
            )
        )

    return app


app = create_app()
