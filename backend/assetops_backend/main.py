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

import os

from datetime import datetime

from typing import Callable, Sequence

from fastapi import APIRouter, FastAPI

from assetops_backend.analytics.assessment_ports import AssessmentStoreUnavailable
from assetops_backend.analytics.composition import build_assessment_store
from assetops_backend.analytics.composition import build_claim_limit_read_service
from assetops_backend.analytics.composition import build_cold_read_service, build_ev_read_service
from assetops_backend.analytics.ports import AssessmentStore
from assetops_backend.analytics.service import AssessmentService
from assetops_backend.analytics.composition import (build_dispatch_read_service, build_finding_index_service,
                                                     build_finding_read_service, build_lineage_reader,
                                                     finding_store_unavailable)
from assetops_backend.analytics.performance_comparison import (
    basis_aware_gate,
    comparison_summary,
    permits_performance_cutover,
)
from assetops_backend.analytics import dispatch_v3
from assetops_backend.analytics.assessment_inputs import BRACKET as ASSESSMENT_BRACKET
from assetops_backend.finding_api import ACCESS_BASIS, Access, build_finding_router, development_access
from assetops_backend.finding_index_api import build_finding_index_router
from assetops_backend.estate.composition import (build_estate_evidence_service, build_estate_index_service,
                                                 build_estate_portfolio_service, registry_tenant)
from assetops_backend.estate_api import build_estate_router
from assetops_backend.estate_evidence_money_api import build_estate_evidence_money_router
from assetops_backend.estate_portfolio_api import build_estate_portfolio_router
from assetops_backend.source_health_api import build_source_health_router
from assetops_backend.asset_boundary_api import build_asset_boundary_router
from assetops_backend.analytics.cold_depth import ColdDepthReadService
from assetops_backend.analytics.cold_site_reads import ColdSiteReadService
from assetops_backend.cold_assessment_api import build_cold_assessment_router
from assetops_backend.cold_foundation_api import build_cold_foundation_router
from assetops_backend.ev_assessment_api import build_ev_assessment_router
from assetops_backend.ev_depth_api import build_ev_depth_router
from assetops_backend.ev_site_api import build_ev_site_router
from assetops_backend.ev_foundation_api import build_ev_foundation_router
from assetops_backend.cold_replay import ColdReplayService
from assetops_backend.cold_replay_api import build_cold_replay_router, no_owner_principal
from assetops_backend.ev_replay import EvReplayService
from assetops_backend.ev_replay_api import build_ev_replay_router
from assetops_backend.cold_depth_api import build_cold_depth_router
from assetops_backend.cold_scenarios.service import ColdScenarioService
from assetops_backend.cold_scenarios.store import PostgresColdScenarioStore
from assetops_backend.cold_scenarios_api import build_cold_scenarios_router
from assetops_backend.ev_scenarios.service import EvScenarioService
from assetops_backend.ev_scenarios.store import PostgresEvScenarioStore
from assetops_backend.ev_scenarios_api import build_ev_scenarios_router
from assetops_backend.cold_site_api import build_cold_site_router
from assetops_backend.action_api import build_action_router
from assetops_backend.actions.composition import ACTION_UNAVAILABLE, build_action_service
from assetops_backend.actions.site_index import ActionIndexService
from assetops_backend.action_index_api import build_action_index_router
from assetops_backend.work.composition import (WORK_UNAVAILABLE, build_domain_action_read_service,
                                               build_domain_intent_service, build_global_work_detail_service,
                                               build_global_work_index_service, build_work_detail_service,
                                               build_work_index_service, build_work_service)
from assetops_backend.work_api import Principal, WorkGate, build_work_router, no_service_principal
from assetops_backend.domain_work_api import build_domain_work_router
from assetops_backend.global_work_api import build_global_work_router
from assetops_backend.financial_api import build_financial_assumption_router
from assetops_backend.financial_read_api import build_financial_read_router
from assetops_backend.consequence_history_api import build_consequence_history_router
from assetops_backend.financials.composition import (
    CONSEQUENCE_UNAVAILABLE,
    AssumptionStoreUnavailable,
    build_assumption_read_service,
    build_cold_consequence_store,
    build_consequence_history_service,
    build_consequence_read_service,
    build_ev_depth_read_service,
    build_ev_site_read_service,
)
from assetops_backend.performance_api import build_performance_router
from assetops_backend.mini_depth.read import MiniDepthRead
from assetops_backend.mini_depth_api import build_mini_depth_router
from assetops_backend.mini_decisions.alternatives import AlternativeService
from assetops_backend.mini_decisions.opportunities import OpportunityService
from assetops_backend.mini_decisions.work_links import WorkLinkService
from assetops_backend.mini_decisions.scenarios import ScenarioService
from assetops_backend.mini_decisions.store import PostgresMiniDecisionStore
from assetops_backend.mini_decisions_api import (
    DecisionPrincipalResolver,
    build_mini_decisions_router,
    deny_decision_writes,
    no_decision_principal,
)
from assetops_backend.claim_limit_api import build_claim_limit_router
from assetops_backend.performance_migration import legacy_dispatch_claims
from assetops_backend.analytics_api import build_analytics_router
from assetops_backend.config import (
    DEVELOPMENT_TENANT_SLUG,
    FeatureFlags,
    database_url,
    load_feature_flags,
)
from assetops_backend.evidence.composition import (
    build_cold_replay_reader,
    build_ev_replay_reader,
    build_link_rows_reader,
    build_comparison_reports,
    build_performance_comparison_reports,
    build_evidence_ledger,
    build_evidence_store,
    build_gateway_access,
)
from assetops_backend.evidence.gateway_access import (
    DiagnosticIngestionService,
    GatewayAccessStore,
    StoreGatewayPrincipals,
)
from assetops_backend.gateway_api import (
    build_gateway_router,
    install_gateway_tls_boundary,
    registered_site_scope,
)
from assetops_backend.evidence.ledger import EvidenceLedger, GatewayPrincipalResolver, LedgerUnavailable
from assetops_backend.evidence.ledger_reads import ImportedEvidenceReads
from assetops_backend.evidence.ledger_service import BatchIngestionService
from assetops_backend.evidence.ports import EvidenceStore
from assetops_backend.evidence.service import Clock, IngestionService, system_clock
from assetops_backend.evidence_api import build_evidence_router
from assetops_backend.foundation_api import build_foundation_router
from assetops_backend.runs.commit_ports import CommittedArtifactStore
from assetops_backend.evidence.legacy_comparison import environment_identity
from assetops_backend.evidence_migration import current_legacy_inventory, current_store_root
from assetops_backend.runs.composition import build_commit_store, build_run_repository
from assetops_backend.runs.execution_ports import LabExecutionPort
from assetops_backend.runs.ports import SimulationRunRepository
from assetops_backend.runs.registered_basis import RegisteredLabBasis
from assetops_backend.runs.profiles import (
    MODEL_PROFILES,
    PUBLICATION_PROFILES,
)
from assetops_backend.scenarios.composition import build_scenario_repository
from assetops_backend.scenarios.ports import ScenarioDefinitionRepository
from assetops_backend.simulator_lab_api import EvCatalogAccess, EvCatalogOwner, build_simulator_lab_router
from assetops_backend.scheduling.composition import SCHEDULE_UNAVAILABLE
from assetops_backend.site_overview.composition import build_site_overview_read
from assetops_backend.site_overview.route import SiteOverviewRoute
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
from assetops_backend.sites.ports import SiteRepository, SiteStoreUnavailable, SiteTemplateCatalog
from assetops_backend.outcome_api import build_outcome_router
from assetops_backend.site_outcomes.composition import build_outcome_board_service
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
    evidence_ledger: EvidenceLedger | None = None,
    gateway_principals: GatewayPrincipalResolver | None = None,
    gateway_access: GatewayAccessStore | None = None,
    comparison_reports=None,
    gateway_clock: Callable[[], datetime] | None = None,
    ev_access: EvCatalogAccess = development_access,
    ev_owner: EvCatalogOwner = no_owner_principal,
    mini_decision_command_access: Access = deny_decision_writes,
    mini_decision_principal: DecisionPrincipalResolver = no_decision_principal,
    domain_work_principal: Principal = no_service_principal,
    site_read_access: Access = development_access,
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

    W2-05b N1: `ev_access` and `ev_owner` default to `development_access` and
    `no_owner_principal`, so the production EV choice list answers 403 (no
    verified Lab-owner principal exists). The owner walkthrough's isolated app
    injects a Site-scoped owner check for `EV-LAB-001`; nothing here reads a
    global flag that would grant every Site.

    R373 (B19-15): `site_read_access` is the one Site-read admission callable for Site Work, domain Work and the
    global Work roots (request detail and the four lists). It defaults to `development_access`, which admits the
    development operator everywhere; estate roots and other Site reads are not threaded here (R374).
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
    # S2-02: Batch/Receipt V2 over the central ledger. Network upload stays
    # closed (401) unless a registered-gateway principal resolver is injected.
    batch_ingestion = BatchIngestionService(
        build_evidence_ledger(database_url()) if evidence_ledger is None else evidence_ledger
    )
    app.state.batch_ingestion = batch_ingestion
    # S2-02 phase 2: the registered-gateway bearer credential verifier. With no
    # product database the network route stays closed (401 GATEWAY_UPLOAD_CLOSED).
    if gateway_access is None and database_url():
        gateway_access = build_gateway_access(database_url())
    if gateway_principals is None and gateway_access is not None:
        gateway_principals = StoreGatewayPrincipals(gateway_access)
    install_gateway_tls_boundary(app)
    # S2-02 phase 3a: the newest legacy comparison report gates each imported
    # Site's Evidence cutover. A composition that injects its own evidence
    # store reads no workspace report unless it injects reports too.
    if comparison_reports is None and evidence_store is None:
        comparison_reports = build_comparison_reports()
    latest_comparison = (lambda site_code: None) if comparison_reports is None else comparison_reports.latest
    # Q14: the gate recomputes the Site's legacy inventory from the CURRENT
    # legacy evidence and committed artifacts on every read, and is scoped to
    # this environment's database. The commit store is built only when an
    # imported Site's gate is actually asked (a closed build never builds it).
    def current_inventory(site_code: str) -> dict:
        commits = build_commit_store() if commit_store is None else commit_store
        return current_legacy_inventory(ingestion.store, commits, site_code)

    # Q26: the gate is also scoped to the local store roots this process reads.
    def store_root() -> str | None:
        commits = build_commit_store() if commit_store is None else commit_store
        return current_store_root(ingestion.store, commits)
    # S3-01 phase 3: imported-Site Performance > Dispatch over the durable dispatch-3.1 store, closed
    # until the newest file-backed comparison and the live lineage pass (performance_comparison).
    performance_reads = (build_dispatch_read_service(database_url(), os.environ.get("ASSETOPS_DEMO_FIXTURE_MANIFEST"))
                         if database_url() else None)
    performance_reports = build_performance_comparison_reports() if evidence_store is None else None
    lineage = build_lineage_reader(database_url()) if database_url() else None

    def performance_gate(site_code: str, tenant_id, site_id) -> tuple[bool, str]:
        if performance_reports is None or lineage is None:
            return False, "No Performance comparison report store or product database is configured."
        return permits_performance_cutover(
            performance_reports.latest(site_code), site_code, str(site_id), tenant_id=str(tenant_id),
            environment=environment_identity(database_url()),
            legacy_claims=legacy_dispatch_claims(assessments.store, site_code),
            live_lineage=lineage.lineage_breaks(tenant_id, site_id, "dispatch", dispatch_v3.MODEL_VERSION),
            model_version=dispatch_v3.MODEL_VERSION,
            selected_revision_ids=lambda: {str(r["id"]) for r in lineage.selected_intervals(
                tenant_id, site_id, "dispatch", "dispatch", ASSESSMENT_BRACKET)})

    # S5-01: the imported-Site Overview delegate at the existing Overview route: Finding-read access convention,
    # ledger scope, the S2 comparison (ImportedEvidenceReads below) and the Performance gate above; one upstream
    # seam per process, disposed at shutdown. Every store failure is a typed 503, never an empty claim.
    site_overview_read = (build_site_overview_read(database_url(), batch_ingestion.ledger)
                          if database_url() else None)
    if site_overview_read is not None:
        # FastAPI 0.141 has no add_event_handler; the router's shutdown list runs under the default lifespan.
        app.router.on_shutdown.append(site_overview_read.dispose)
    site_overview = SiteOverviewRoute(site_overview_read, registry.ledger_scope, performance_gate,
                                      development_access, ACCESS_BASIS,
                                      (LedgerUnavailable, AssessmentStoreUnavailable, SCHEDULE_UNAVAILABLE,
                                       *finding_store_unavailable(), *CONSEQUENCE_UNAVAILABLE))
    # W4-02 q12-6: the persisted empty-legacy cutover basis (Postgres Foundation store only); any other store keeps
    # the S2 comparison requirement.
    basis_reader = getattr(foundation_store, "no_legacy_evidence_basis", None)
    if basis_reader is not None:
        site_overview.no_legacy_basis = basis_reader
    imported_reads = ImportedEvidenceReads(
        batch_ingestion.ledger,
        registry.ledger_scope,
        latest_comparison,
        current_inventory,
        environment_identity(database_url()),
        store_root,
    )
    app.include_router(
        build_evidence_router(
            ingestion,
            repository,
            assessments.card_assessments,
            batch_ingestion=batch_ingestion,
            gateway_principals=gateway_principals,
            imported_reads=imported_reads,
            site_overview=site_overview,
        )
    )
    app.include_router(
        build_gateway_router(
            gateway_principals,
            None if gateway_access is None else DiagnosticIngestionService(gateway_access, gateway_clock or utc_now),
            gateway_access,
            registered_site_scope(registry),
            gateway_clock or utc_now,
        )
    )
    # S7-01a: versioned two-clock Site source-health read and configured-battery boundary read.
    app.include_router(build_source_health_router(
        gateway_access if hasattr(gateway_access, "source_health_snapshot") else None,
        registry.ledger_scope, gateway_clock or utc_now))
    app.include_router(build_asset_boundary_router(registry))
    # W2-01: selected cold-chain Foundation read; contact from the same gateway-health store.
    app.include_router(build_cold_foundation_router(
        registry, gateway_access if hasattr(gateway_access, "gateway_health") else None, gateway_clock or utc_now))
    # W2-05a: selected EV Foundation read; contact from the same gateway-health store.
    app.include_router(build_ev_foundation_router(
        registry, gateway_access if hasattr(gateway_access, "gateway_health") else None, gateway_clock or utc_now))
    # W2-03: selected cold temperature, backup-chain and cold Finding reads; typed 503 without a database.
    cold_reads = build_cold_read_service(database_url()) if database_url() else None
    if cold_reads is not None:
        app.router.on_shutdown.append(cold_reads.dispose)
    app.include_router(build_cold_assessment_router(registry, cold_reads))
    # W2-06: selected EV session and EV Finding reads; typed 503 without a database.
    ev_reads = build_ev_read_service(database_url()) if database_url() else None
    if ev_reads is not None:
        app.router.on_shutdown.append(ev_reads.dispose)
    app.include_router(build_ev_assessment_router(registry, ev_reads))
    # W2-07 commit 3: the five selected EV Site reads (W2-06's gate and envelope, one shared money selector).
    ev_site_reads = build_ev_site_read_service(database_url()) if database_url() else None
    if ev_site_reads is not None:
        app.router.on_shutdown.append(ev_site_reads.dispose)
    app.include_router(build_ev_site_router(registry, ev_site_reads))
    # W5-03a E1b (Lane A): selected EV Availability, Energy and Health depth; typed 503 without a database.
    ev_depth_reads = build_ev_depth_read_service(database_url()) if database_url() else None
    if ev_depth_reads is not None:
        app.router.on_shutdown.append(ev_depth_reads.dispose)
    app.include_router(build_ev_depth_router(registry, ev_depth_reads))
    # W5-03b E5: authored EV scenarios. Writes need the two explicit decision injections; reads use the EV gate.
    ev_scenario_store = PostgresEvScenarioStore.from_url(database_url()) if ev_reads is not None else None
    if ev_scenario_store is not None:
        app.router.on_shutdown.append(ev_scenario_store.dispose)
    app.include_router(build_ev_scenarios_router(
        registry, None if ev_scenario_store is None else EvScenarioService(ev_scenario_store, ev_reads, ev_site_reads),
        command_access=mini_decision_command_access, principal=mini_decision_principal))
    # W2-04: the five cold Site reads over the same W2-03 read service and the cold consequence store's
    # caller-connection heads; one REPEATABLE READ snapshot per request, typed 503 without a database.
    cold_consequences = build_cold_consequence_store(database_url()) if cold_reads is not None else None
    if cold_consequences is not None:
        app.router.on_shutdown.append(cold_consequences.dispose)
    cold_site_reads = None if cold_reads is None else ColdSiteReadService(cold_reads, cold_consequences)
    app.include_router(build_cold_site_router(registry, cold_site_reads))
    # W5-01 C1: the selected cold Cooling depth read over the same W2-03 read service and the W2-04 gate.
    app.include_router(build_cold_depth_router(
        registry, None if cold_reads is None else ColdDepthReadService(cold_reads)))
    # W5-01b C4: authored cold scenarios. Writes need the two explicit decision injections; reads use the cold gate.
    cold_scenario_store = PostgresColdScenarioStore.from_url(database_url()) if cold_reads is not None else None
    if cold_scenario_store is not None:
        app.router.on_shutdown.append(cold_scenario_store.dispose)
    app.include_router(build_cold_scenarios_router(
        registry, None if cold_scenario_store is None else ColdScenarioService(cold_scenario_store, cold_reads),
        command_access=mini_decision_command_access, principal=mini_decision_principal))
    app.include_router(build_analytics_router(assessments, ingestion.store, repository))
    def performance_report(site_code: str) -> dict | None:
        return None if performance_reports is None else comparison_summary(performance_reports.latest(site_code))

    app.include_router(build_performance_router(performance_reads, registry.ledger_scope, performance_gate,
                                                performance_report))
    # W4-02 unit 5: the mini-grid depth reads; no Dispatch gate (closure 4 S1); typed 503 without a database.
    mini_reads = MiniDepthRead.from_url(database_url(), build_link_rows_reader()) if database_url() else None
    if mini_reads is not None:
        app.router.on_shutdown.append(mini_reads.dispose)
    app.include_router(build_mini_depth_router(mini_reads, registry))
    # W4-03 unit 2b (closure 2 Q1, closure 4 B2): mini scenarios. Writes need the two explicit injections; the
    # default composition refuses every write. Reads use the existing Site-scoped development access.
    decision_store = PostgresMiniDecisionStore.from_url(database_url()) if mini_reads is not None else None
    if decision_store is not None:
        app.router.on_shutdown.append(decision_store.dispose)
    app.include_router(build_mini_decisions_router(
        None if decision_store is None or mini_reads is None else ScenarioService(decision_store, mini_reads),
        registry, command_access=mini_decision_command_access, principal=mini_decision_principal,
        alternatives=None if decision_store is None or mini_reads is None
        else AlternativeService(decision_store, mini_reads),
        # W4-03 unit 5 (S10, u5): the physical opportunity reads take the Performance gate after scope and role.
        opportunities=None if decision_store is None or mini_reads is None
        else OpportunityService(decision_store, mini_reads), gate=performance_gate,
        gate_unavailable=finding_store_unavailable(),
        # W4-03 unit 8 (u5): explicit work associations and the Site Work decision-context overlay.
        work_links=None if decision_store is None else WorkLinkService(decision_store)))
    # S3-02a: selected-assessment capability and claim-limit read; same Performance gate, Finding access seam.
    app.include_router(build_claim_limit_router(
        build_claim_limit_read_service(database_url()) if database_url() else None, registry.ledger_scope,
        gate=performance_gate))
    # S4-01 phase 2: exact Finding root/revision read (A-claim-work-routes); typed 503 without a database.
    finding_manifest = os.environ.get("ASSETOPS_FINDING_CASES_MANIFEST") or os.environ.get(
        "ASSETOPS_DEMO_FIXTURE_MANIFEST")
    finding_reads = build_finding_read_service(database_url(), finding_manifest) if database_url() else None
    app.include_router(build_finding_router(
        finding_reads,
        registry.ledger_scope, finding_store_unavailable(), gate=performance_gate,
        # S4-02b phase 2a: the stored fuel-cost consequence read and the Financials bridge summary.
        consequences=build_consequence_read_service(database_url()) if database_url() else None,
        consequence_unavailable=CONSEQUENCE_UNAVAILABLE))
    # S4-04 phase 1: the Site Finding index read (D-2026-10-15-s404-contract); typed 503 without a database.
    finding_index = build_finding_index_service(database_url(), finding_manifest) if database_url() else None
    finding_index_gate = basis_aware_gate(performance_gate, basis_reader, (SiteStoreUnavailable,))
    app.include_router(build_finding_index_router(
        finding_index,
        registry.ledger_scope, finding_store_unavailable(),
        # Final review ruling 3 (M4): the Overview's Finding list states the empty-legacy reason, never inferred.
        gate=finding_index_gate))
    # S6-01a: reserve-trial recommendation, SYSTEM demonstration acceptance/observation and exact Action reads.
    actions = (build_action_service(database_url(), finding_reads, registry=registry)
               if finding_reads is not None else None)
    app.include_router(build_action_router(
        actions, registry.ledger_scope, (*finding_store_unavailable(), ACTION_UNAVAILABLE), gate=performance_gate))
    # S6-03: the Site Work Action index over the same Action store (D-2026-10-16-a-action-index).
    action_index = ActionIndexService(actions.store, clock=actions.clock) if actions is not None else None
    app.include_router(build_action_index_router(
        action_index,
        registry.ledger_scope, (*finding_store_unavailable(), ACTION_UNAVAILABLE)))
    # W3-01 commit 2 (q5 ruling 5): the read-only estate roots `/api/estate/{scope,findings,actions}`; tenant from the
    # server registry only, per-Site admission through the Finding-route access seam; typed 503 without a database.
    app.include_router(build_estate_router(
        build_estate_index_service(database_url()), registry_tenant(registry),
        access=development_access, unavailable=(SiteStoreUnavailable,)))
    # W3-02 commit 1: the read-only estate Evidence root `/api/estate/evidence` (same tenant/access seams).
    app.include_router(build_estate_evidence_money_router(
        build_estate_evidence_service(database_url()), registry_tenant(registry),
        access=development_access, unavailable=(SiteStoreUnavailable,)))
    # W3-03 run 2 (Lane A, after reviewed 1b): the read-only estate Portfolio root `/api/estate/portfolio`; same
    # tenant/access seams. Its cursor key comes only from ASSETOPS_ESTATE_PORTFOLIO_CURSOR_KEY_HEX (r1b Q-1b-1).
    estate_portfolio = build_estate_portfolio_service(database_url())
    app.include_router(build_estate_portfolio_router(
        estate_portfolio, registry_tenant(registry),
        access=development_access, unavailable=(SiteStoreUnavailable,)))
    # W4-01 commit 3 (Lane A): Site work commands and the case detail read. No server SERVICE principal is
    # injected here, so a write is 403; the detail read is available under Site read access.
    work_lists = build_work_index_service(database_url()) if database_url() else None
    app.include_router(build_work_router(
        build_work_service(database_url()) if database_url() else None, registry.ledger_scope, (WORK_UNAVAILABLE,),
        details=build_work_detail_service(database_url()) if database_url() else None,
        lists=work_lists, access=site_read_access))
    # W5-02a K1a (ruling A2): the domain Action commands through the same W4 gate. `domain_work_principal` is the
    # server SERVICE principal for tests/host wiring; by default none is injected (as for W4), so a write is 403.
    app.include_router(build_domain_work_router(
        build_domain_intent_service(database_url()) if database_url() else None,
        WorkGate(registry.ledger_scope, (WORK_UNAVAILABLE,), access=site_read_access,
                 principal=domain_work_principal), (WORK_UNAVAILABLE,),
        reads=(domain_action_reads := build_domain_action_read_service(database_url()))))
    # W6-01a (Lane A): the read-only global work roots `/api/work/{incidents,...}`; tenant from the server registry
    # only, per-Site admission through the Finding-route access seam; typed 503 without a database or cursor key.
    # W6-01c (G5): the exact request detail `/api/work/requests/{case_id}?site_id=` on the same router.
    # R373 (B19-15): Site Work, domain Work and global Work (detail and all four lists) share ONE Site-read access
    # callable, so a real principal can never be attached to Site Work while global Work stays on development access.
    app.include_router(build_global_work_router(
        build_global_work_index_service(database_url()), registry_tenant(registry),
        access=site_read_access, unavailable=(SiteStoreUnavailable,),
        details=build_global_work_detail_service(database_url()), scope=registry.ledger_scope))
    # S4-02a: the human price write route has no success path (no verified human principal yet).
    app.include_router(build_financial_assumption_router(registry.ledger_scope))
    # S4-08: the Site consequence history at one recorded cutoff (read-only). Included before the price reads so
    # `/financial-assumptions/consequences` is not taken for a price revision ID.
    app.include_router(build_consequence_history_router(
        build_consequence_history_service(database_url()) if database_url() else None,
        registry.ledger_scope, CONSEQUENCE_UNAVAILABLE, gate=performance_gate))
    # S4-02a phase 2: Site price reads (Finding-read scope semantics; typed 503 without a database).
    assumption_reads = build_assumption_read_service(database_url()) if database_url() else None
    app.include_router(build_financial_read_router(
        assumption_reads,
        registry.ledger_scope, (AssumptionStoreUnavailable,)))
    # OUT-B4 (§B.3): the Site outcome board and the estate outcome summary over the instances composed above
    # (no new store except the preventive-plan global work read, disposed at shutdown).
    outcome_board, outcome_board_dispose = build_outcome_board_service(
        database_url(), site_overview=site_overview if site_overview_read is not None else None,
        s2_scope=imported_reads.scope, mini_depth=mini_reads, dispatch=performance_reads,
        performance_gate=performance_gate, finding_index=finding_index, finding_index_gate=finding_index_gate,
        assumptions=assumption_reads, actions=actions, action_index=action_index, cold_site=cold_site_reads,
        cold_reads=cold_reads, ev_site=ev_site_reads, ev_reads=ev_reads, ev_depth=ev_depth_reads,
        domain_actions=domain_action_reads, work_index=work_lists, estate=estate_portfolio)
    app.router.on_shutdown.append(outcome_board_dispose)
    app.include_router(build_outcome_router(
        outcome_board, registry, estate=estate_portfolio, tenant=registry_tenant(registry),
        access=development_access, work_access=site_read_access, unavailable=(SiteStoreUnavailable,)))
    # addendum 4 #7: the cold and EV routers above get no disclosure argument here, so the board keeps the
    # allow defaults too; pass the same callables to the board if that changes.

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
                # S2-01a: an imported code is set up from its registered
                # Foundation + SignalBinding basis, never from the YAML Site.
                registered_bases=RegisteredLabBasis(registry),
                # W2-05b: the EV choice list requires a Lab owner principal (Q10). As for the cold
                # replay below, no production owner principal exists, so production answers 403 by
                # default; only an explicitly injected local composition (the owner walkthrough's
                # isolated app, N1) passes a Site-scoped owner check here.
                ev_access=ev_access,
                ev_owner=ev_owner,
            )
        )
        # W2-02: the explicit-run cold replay read. No production owner principal exists, so every production
        # read answers 403 (`no_owner_principal`); tests inject the owner check.
        app.include_router(build_cold_replay_router(
            ColdReplayService(build_cold_replay_reader(database_url()), runs) if database_url() else None,
            registry.ledger_scope, access=development_access, owner=no_owner_principal))
        # W2-05b N1: the EV replay read uses the same injected `ev_access`/`ev_owner` as the EV choice list, so
        # production answers 403 and only the owner walkthrough's isolated composition reads under one principal.
        app.include_router(build_ev_replay_router(
            EvReplayService(build_ev_replay_reader(database_url()), runs) if database_url() else None,
            registry.ledger_scope, access=ev_access, owner=ev_owner))

    return app


app = create_app()
