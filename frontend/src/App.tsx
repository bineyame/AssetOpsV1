import { Navigate, Route, Routes } from "react-router-dom";

import { featureFlags, type FeatureFlags } from "./config/featureFlags";
import { LegacySiteConfigurationRedirect } from "./shell/LegacySiteConfigurationRedirect";
import { OperatorShellLayout } from "./shell/OperatorShellLayout";
import { RouteNotAvailableFrame } from "./shell/RouteNotAvailableFrame";
import { SiteEvidenceFrame } from "./shell/SiteEvidenceFrame";
import {
  FindingDetailFrame,
  SiteActionFrame,
  SiteWorkFrame,
  SiteWorkCasesFrame,
  SiteFoundationChangeFrame,
  SiteFoundationChangesFrame,
  SiteFinancialsFrame,
  SiteFindingFrame,
  SiteFindingsFrame,
  SitePerformanceFrame,
  SiteOpportunityFrame,
} from "./shell/SiteAnalyticsFrames";
import { SiteAssetFrame, SiteAssetsFrame, SiteHealthFrame } from "./shell/SiteHealthFrames";
import { SiteDetailFrame } from "./shell/SiteDetailFrame";
import { SiteFoundationFrame } from "./shell/SiteFoundationFrame";
import { SitesFrame } from "./shell/SitesFrame";
import { WorkspaceShellLayout } from "./shell/WorkspaceShellLayout";
import {
  ACTIONS_PATH,
  EVIDENCE_PATH,
  FINANCIALS_PATH,
  PORTFOLIO_ROOT_PATH,
  INCIDENTS_PATH,
  MAINTENANCE_PATH,
  MAINTENANCE_PREVENTIVE_PATH,
  WORK_REQUEST_ROUTE_PATH,
  FINDINGS_COST_PATH,
  FINDINGS_OPPORTUNITIES_PATH,
  FINDINGS_PATH,
  FINDINGS_RISKS_PATH,
  FINDING_ROUTE_PATH,
  FINDING_TAB_ROUTE_PATH,
  LEGACY_SITE_CONFIGURATION_ROUTE_PATH,
  SITE_ACTION_ROUTE_PATH,
  SITE_ASSET_ROUTE_PATH,
  SITE_ASSETS_ROUTE_PATH,
  SITE_HEALTH_ROUTE_PATH,
  SITE_ACTION_VIEW_ROUTE_PATH,
  SITE_FINANCIAL_ASSUMPTIONS_ROUTE_PATH,
  SITE_FINANCIAL_SCENARIOS_ROUTE_PATH,
  SITE_OPPORTUNITY_ROUTE_PATH,
  SITE_FINANCIALS_ROUTE_PATH,
  SITE_FINDING_ROUTE_PATH,
  SITE_FINDING_VIEW_ROUTE_PATH,
  SITE_FINDINGS_ROUTE_PATH,
  SITE_WORK_ROUTE_PATH,
  SITE_WORK_INCIDENTS_ROUTE_PATH,
  SITE_WORK_MAINTENANCE_ROUTE_PATH,
  SITE_PERFORMANCE_ROUTE_PATH,
  SITE_PERFORMANCE_SUBTAB_ROUTE_PATH,
  SITES_PATH,
  SITE_DETAIL_ROUTE_PATH,
  SITE_EVIDENCE_ROUTE_PATH,
  SITE_EV_ANALYSIS_ROUTE_PATH,
  SITE_EV_ASSUMPTIONS_ROUTE_PATH,
  SITE_EV_EVIDENCE_ROUTE_PATH,
  SITE_EV_FINANCIALS_ROUTE_PATH,
  SITE_EV_ROUTE_PATH,
  SITE_FOUNDATION_CHANGE_ROUTE_PATH,
  SITE_FOUNDATION_CHANGES_ROUTE_PATH,
  SITE_FOUNDATION_ROUTE_PATH,
  SITE_FOUNDATION_VIEW_ROUTE_PATH,
} from "./shell/operatorSiteRoutes";
import type { RunSetupClient } from "./shell/runSetupClient";
import type { ColdScenarioChoiceClient } from "./shell/coldScenarioChoiceClient";
import type { EvScenarioChoiceClient } from "./shell/evScenarioChoiceClient";
import type { ScenarioCatalogClient } from "./shell/scenarioCatalogClient";
import {
  simulatorLabRoutes,
  simulatorLabSiteTemplateLineage,
} from "./shell/simulatorLabRoutes";
import type { SiteCreationClient } from "./shell/siteCreationClient";
import type { SiteTemplateCatalogClient } from "./shell/siteTemplateCatalogClient";
import type { SiteTemplateLineageClient } from "./sites/siteTemplateLineage";
import {
  createSiteAnalyticsClient,
  type SiteAnalyticsClient,
} from "./sites/siteAnalyticsClient";
import type { FindingIndexClient } from "./sites/findingIndexClient";
import {
  createSiteFoundationClient,
  type SiteFoundationClient,
} from "./sites/siteFoundationClient";
import { createColdFoundationClient, type ColdFoundationClient } from "./sites/coldFoundationClient";
import { createEvFoundationClient, type EvFoundationClient } from "./sites/evFoundationClient";
import { createColdAssessmentClient, type ColdAssessmentClient } from "./sites/coldAssessmentClient";
import { createEvAssessmentClient, type EvAssessmentClient } from "./sites/evAssessmentClient";
import { createMiniDepthClient, type MiniDepthClient } from "./sites/miniDepthClient";
import { createColdDepthClient, type ColdDepthClient } from "./sites/ColdDepthClient";
import { createMiniDecisionsClient, type MiniDecisionsClient } from "./sites/miniDecisionsClient";
import { createEvSiteClient, type EvSiteClient } from "./sites/evSiteClient";
import { SiteEvFrame } from "./shell/evSiteRoutes";
import { createColdSiteClient, type ColdSiteClient } from "./sites/coldSiteClient";
import { createEstateClient, type EstateClient } from "./estate/estateClient";
import { createGlobalWorkClient, type GlobalWorkClient } from "./work/globalWorkClient";
import { GlobalIncidentsFrame } from "./work/GlobalIncidents";
import { GlobalMaintenanceFrame } from "./work/GlobalMaintenance";
import { GlobalPreventiveFrame } from "./work/GlobalPreventive";
import { WorkRequestOverviewFrame } from "./work/WorkRequestOverview";
import {
  createEstateEvidenceMoneyClient,
  createEstateFinancialsClient,
  type EstateEvidenceMoneyClient,
  type EstateFinancialsClient,
} from "./estate/estateEvidenceMoneyClient";
import {
  EstateActionsFrame,
  EstateEvidenceFrame,
  EstateFinancialsFrame,
  EstateFindingsFrame,
  EstatePortfolioFrame,
} from "./shell/EstateRootFrames";
import {
  createSiteEvidenceClient,
  type SiteEvidenceClient,
} from "./sites/siteEvidenceClient";
import {
  createSiteOverviewClient,
  type SiteOverviewClient,
} from "./sites/siteOverviewClient";
import {
  createSiteDirectoryClient,
  type SiteDetailClient,
  type SiteDirectoryClient,
} from "./sites/siteDirectoryClient";

export { SITES_PATH };

/**
 * One client for the whole app, built once at module scope.
 *
 * The routes are rebuilt on every render, and a fresh client each time would
 * change the identity of the prop the Sites index keys its load effect on, so
 * the store would be re-read in a loop.
 */
const defaultSiteDirectory = createSiteDirectoryClient();
const defaultSiteEvidence = createSiteEvidenceClient();
const defaultSiteOverview = createSiteOverviewClient();
const defaultSiteAnalytics = createSiteAnalyticsClient();
const defaultSiteFoundation = createSiteFoundationClient();
const defaultColdFoundation = createColdFoundationClient();
const defaultEvFoundation = createEvFoundationClient();
const defaultColdAssessment = createColdAssessmentClient();
const defaultEvAssessment = createEvAssessmentClient();
const defaultMiniDepth = createMiniDepthClient();
const defaultColdDepth = createColdDepthClient();
const defaultMiniDecisions = createMiniDecisionsClient();
const defaultColdSite = createColdSiteClient();
const defaultEstateIndex = createEstateClient();
const defaultEstateEvidenceMoney = createEstateEvidenceMoneyClient();
const defaultEstateFinancials = createEstateFinancialsClient();
const defaultGlobalWork = createGlobalWorkClient();
const defaultEvSite = createEvSiteClient();

/**
 * Route table.
 *
 * Three levels, in shell order:
 *
 * 1. `WorkspaceShellLayout` is workspace-level chrome. It owns the gated
 *    developer workspace entry point and nothing else.
 * 2. `OperatorShellLayout` is the operator workspace: operator navigation and
 *    the operator route frames (Sites, and, under one site, that site's page,
 *    its Foundation and its Evidence; `/` redirects to Sites). It is flag-free and served in both
 *    gate states, because the Simulator Lab gate controls simulator surfaces
 *    and execution only.
 * 3. Simulator Lab is a separate developer workspace. Its routes come from
 *    `simulatorLabRoutes(flags)`, which returns an empty list when
 *    `simulator_lab.enabled` is false. The route is then never registered, so a
 *    direct Simulator Lab URL matches the catch-all and the UI serves a
 *    not-available frame rather than a hidden-but-reachable simulator surface.
 *
 * The Simulator Lab route sits outside both layouts, so the simulator surface
 * never renders operator navigation chrome and never appears to be an operator
 * page. The catch-all sits outside them too: an address this build does not
 * serve should not be dressed as a workspace.
 *
 * The Sites routes compose the shared Site substrate in `frontend/src/sites/`
 * and are served in both gate states. A site is addressed by `site_id`, so
 * Site Details hangs off the Sites path with the identity in it and is reached
 * from a Sites row, and Foundation hangs off that site in turn and is reached
 * from its tab row. Both parameterless T002 frames, `/site-details` and
 * `/site-configuration`, are gone: a link that names no site is not a
 * destination, and no slice leaves a placeholder standing once its identified
 * route exists. Neither identified route is a navigation item, because a
 * navigation item cannot say which site it would open.
 *
 * The address T008 served Foundation at, `/sites/:siteId/configuration`, is
 * registered once more and only to redirect. It is the single place in the
 * product allowed to name that address, it renders no surface, and the site is
 * carried across, so an old bookmark lands on the same site under the name the
 * product now uses.
 *
 * `siteTemplateCatalog`, `siteDirectory`, `siteDetail`, `siteCreation`,
 * `scenarioCatalog`, `runSetup` and `siteEvidence` are injection points for tests. The default clients read
 * the real APIs; a test supplies fakes so a UI assertion is about what the
 * screen renders from a record rather than about network timing.
 */
export interface AppProps {
  flags?: FeatureFlags;
  siteTemplateCatalog?: SiteTemplateCatalogClient;
  siteDirectory?: SiteDirectoryClient;
  siteDetail?: SiteDetailClient;
  siteCreation?: SiteCreationClient;
  scenarioCatalog?: ScenarioCatalogClient;
  runSetup?: RunSetupClient;
  /** Site > Evidence reads (T027). Operator, never gated. */
  siteEvidence?: SiteEvidenceClient;
  /** Site Overview reads (T027 phase 2). Operator, never gated. */
  siteOverview?: SiteOverviewClient;
  /** Analytics read models: Performance, Findings, Finding detail (T028). Operator, never gated. */
  siteAnalytics?: SiteAnalyticsClient;
  /** S4-04: the scoped Site Finding index for imported Sites; the frame's default client when omitted. */
  siteFindingIndex?: FindingIndexClient;
  /** Persisted Foundation read and reserve change (S1-01). Operator, never gated. */
  siteFoundation?: SiteFoundationClient;
  /** W2-01: the selected cold-chain configuration read, used when the Site is COLDCHAIN. */
  coldFoundation?: ColdFoundationClient;
  /** W2-05a: the selected EV Foundation read. */
  evFoundation?: EvFoundationClient;
  /** W2-03: the selected cold assessment reads, used for a COLDCHAIN Site's Performance and Finding routes. */
  coldAssessment?: ColdAssessmentClient;
  /** W2-06: the selected EV session reads, used for an EV_CHARGING Site's Performance/Sessions and Finding routes. */
  evAssessment?: EvAssessmentClient;
  /** W4-02: the MINIGRID mini-depth reads, used for a MINIGRID Site's Service/Fuel/Renewable/Backup routes. */
  miniDepth?: MiniDepthClient;
  /** W5-01a C2: the selected cold depth reads (Cooling) for a COLDCHAIN Site's Performance route. */
  coldDepth?: ColdDepthClient;
  /** W4-03 unit 6: the read-only mini decision reads (Scenarios). */
  miniDecisions?: MiniDecisionsClient;
  /** W2-07: the five EV Site reads, used for an EV_CHARGING Site's `/ev` routes. */
  evSite?: EvSiteClient;
  /** W2-04: the five cold Site reads, used for a COLDCHAIN Site's Overview, Evidence and Financials routes. */
  coldSite?: ColdSiteClient;
  /** Overrides the gated template-lineage client; still gated by `flags`. */
  siteTemplateLineage?: SiteTemplateLineageClient;
  /** Injected so a test can pin the day the run setup defaults derive from. */
  now?: () => Date;
  /** W2-02: the gated cold-chain choice read; still gated by `flags`. */
  coldScenarios?: ColdScenarioChoiceClient;
  /** W2-05b: the gated EV test-run choice read; still gated by `flags`. */
  evScenarios?: EvScenarioChoiceClient;
  /** W3-01: the read-only estate Finding and Action roots (`/api/estate/*`). */
  estateIndex?: EstateClient;
  /** W3-02: the read-only estate Evidence root. */
  estateEvidenceMoney?: EstateEvidenceMoneyClient;
  /** W3-02 commit 4: the read-only estate Financials root. */
  estateFinancials?: EstateFinancialsClient;
  /** W6-01a: the read-only global work lists (`/api/work/*`). */
  globalWork?: GlobalWorkClient;
}

export function App({
  flags = featureFlags,
  siteTemplateCatalog,
  siteDirectory = defaultSiteDirectory,
  siteDetail = defaultSiteDirectory,
  siteCreation,
  scenarioCatalog,
  runSetup,
  siteEvidence = defaultSiteEvidence,
  siteOverview = defaultSiteOverview,
  siteAnalytics = defaultSiteAnalytics,
  siteFindingIndex,
  siteFoundation = defaultSiteFoundation,
  coldFoundation = defaultColdFoundation,
  evFoundation = defaultEvFoundation,
  coldAssessment = defaultColdAssessment,
  evAssessment = defaultEvAssessment,
  miniDepth = defaultMiniDepth,
  miniDecisions = defaultMiniDecisions,
  coldDepth = defaultColdDepth,
  coldSite = defaultColdSite,
  evSite = defaultEvSite,
  siteTemplateLineage,
  now,
  coldScenarios,
  evScenarios,
  estateIndex = defaultEstateIndex,
  estateEvidenceMoney = defaultEstateEvidenceMoney,
  estateFinancials = defaultEstateFinancials,
  globalWork = defaultGlobalWork,
}: AppProps) {
  // Resolved once from the gate: closed, the site surfaces get no lineage read
  // and show the recorded template alone.
  const templateLineage = simulatorLabSiteTemplateLineage(
    flags,
    siteTemplateLineage,
  );

  return (
    <Routes>
      <Route element={<WorkspaceShellLayout flags={flags} />}>
        <Route element={<OperatorShellLayout />}>
          <Route path="/" element={<Navigate to={SITES_PATH} replace />} />
          <Route
            path={SITES_PATH}
            element={
              <SitesFrame
                flags={flags}
                directory={siteDirectory}
                templateLineage={templateLineage}
              />
            }
          />
          <Route
            path={SITE_DETAIL_ROUTE_PATH}
            element={
              <SiteDetailFrame
                detail={siteDetail}
                overview={siteOverview}
                sitesPath={SITES_PATH}
                flags={flags}
                templateLineage={templateLineage}
                findingIndex={siteFindingIndex}
                coldSite={coldSite}
                coldAssessment={coldAssessment}
                miniDepth={miniDepth}
              />
            }
          />
          <Route
            path={SITE_FOUNDATION_ROUTE_PATH}
            element={
              <SiteFoundationFrame
                detail={siteDetail}
                foundation={siteFoundation}
                coldFoundation={coldFoundation}
                evFoundation={evFoundation}
                sitesPath={SITES_PATH}
                templateLineage={templateLineage}
                gatewayHealth={siteEvidence.gatewayHealth}
              />
            }
          />
          <Route
            path={SITE_FOUNDATION_VIEW_ROUTE_PATH}
            element={
              <SiteFoundationFrame
                detail={siteDetail}
                foundation={siteFoundation}
                coldFoundation={coldFoundation}
                evFoundation={evFoundation}
                sitesPath={SITES_PATH}
                templateLineage={templateLineage}
                gatewayHealth={siteEvidence.gatewayHealth}
              />
            }
          />
          <Route
            path={SITE_FOUNDATION_CHANGES_ROUTE_PATH}
            element={<SiteFoundationChangesFrame detail={siteDetail} sitesPath={SITES_PATH} />}
          />
          <Route
            path={SITE_FOUNDATION_CHANGE_ROUTE_PATH}
            element={<SiteFoundationChangeFrame detail={siteDetail} sitesPath={SITES_PATH} />}
          />
          {(
            [
              [SITE_EV_ROUTE_PATH, "overview"],
              [SITE_EV_EVIDENCE_ROUTE_PATH, "evidence"],
              [SITE_EV_ANALYSIS_ROUTE_PATH, "analysis"],
              [SITE_EV_FINANCIALS_ROUTE_PATH, "financials"],
              [SITE_EV_ASSUMPTIONS_ROUTE_PATH, "assumptions"],
            ] as const
          ).map(([path, view]) => (
            <Route key={path} path={path} element={<SiteEvFrame detail={siteDetail} sitesPath={SITES_PATH} view={view} evSite={evSite} />} />
          ))}
          <Route
            path={SITE_EVIDENCE_ROUTE_PATH}
            element={
              <SiteEvidenceFrame
                detail={siteDetail}
                evidence={siteEvidence}
                analytics={siteAnalytics}
                sitesPath={SITES_PATH}
                coldSite={coldSite}
                coldAssessment={coldAssessment}
              />
            }
          />
          {[SITE_PERFORMANCE_ROUTE_PATH, SITE_PERFORMANCE_SUBTAB_ROUTE_PATH].map((path) => (
            <Route
              key={path}
              path={path}
              element={
                <SitePerformanceFrame
                  detail={siteDetail}
                  analytics={siteAnalytics}
                  sitesPath={SITES_PATH}
                  coldAssessment={coldAssessment}
                  evAssessment={evAssessment}
                  miniDepth={miniDepth}
                  miniDecisions={miniDecisions}
                  coldDepth={coldDepth}
                />
              }
            />
          ))}
          <Route
            path={SITE_FINDINGS_ROUTE_PATH}
            element={
              <SiteFindingsFrame
                detail={siteDetail}
                analytics={siteAnalytics}
                findingIndex={siteFindingIndex}
                sitesPath={SITES_PATH}
              />
            }
          />
          <Route
            path={SITE_FINANCIALS_ROUTE_PATH}
            element={<SiteFinancialsFrame detail={siteDetail} sitesPath={SITES_PATH} view="overview" coldSite={coldSite} coldAssessment={coldAssessment} />}
          />
          <Route
            path={SITE_FINANCIAL_ASSUMPTIONS_ROUTE_PATH}
            element={<SiteFinancialsFrame detail={siteDetail} sitesPath={SITES_PATH} view="assumptions" coldSite={coldSite} coldAssessment={coldAssessment} />}
          />
          <Route
            path={SITE_FINANCIAL_SCENARIOS_ROUTE_PATH}
            element={<SiteFinancialsFrame detail={siteDetail} sitesPath={SITES_PATH} view="scenarios" miniDecisions={miniDecisions} />}
          />
          <Route
            path={SITE_OPPORTUNITY_ROUTE_PATH}
            element={<SiteOpportunityFrame detail={siteDetail} sitesPath={SITES_PATH} miniDecisions={miniDecisions} />}
          />
          {[SITE_FINDING_ROUTE_PATH, SITE_FINDING_VIEW_ROUTE_PATH].map((path) => (
            <Route
              key={path}
              path={path}
              element={<SiteFindingFrame detail={siteDetail} sitesPath={SITES_PATH} coldAssessment={coldAssessment} evAssessment={evAssessment} miniDecisions={miniDecisions} />}
            />
          ))}
          <Route path={SITE_HEALTH_ROUTE_PATH} element={<SiteHealthFrame detail={siteDetail} sitesPath={SITES_PATH} coldDepth={coldDepth} />} />
          <Route path={SITE_ASSETS_ROUTE_PATH} element={<SiteAssetsFrame detail={siteDetail} sitesPath={SITES_PATH} />} />
          <Route path={SITE_ASSET_ROUTE_PATH} element={<SiteAssetFrame detail={siteDetail} sitesPath={SITES_PATH} />} />
          <Route path={SITE_WORK_ROUTE_PATH} element={<SiteWorkFrame detail={siteDetail} sitesPath={SITES_PATH} />} />
          <Route
            path={SITE_WORK_INCIDENTS_ROUTE_PATH}
            element={<SiteWorkCasesFrame key="incidents" kind="incidents" detail={siteDetail} sitesPath={SITES_PATH} miniDecisions={miniDecisions} />}
          />
          <Route
            path={SITE_WORK_MAINTENANCE_ROUTE_PATH}
            element={<SiteWorkCasesFrame key="maintenance" kind="maintenance" detail={siteDetail} sitesPath={SITES_PATH} miniDecisions={miniDecisions} />}
          />
          {[SITE_ACTION_ROUTE_PATH, SITE_ACTION_VIEW_ROUTE_PATH].map((path) => (
            <Route
              key={path}
              path={path}
              element={<SiteActionFrame detail={siteDetail} sitesPath={SITES_PATH} />}
            />
          ))}
          {/* W3-01: the estate Finding lens roots and the Actions root, registered before the legacy
              `/findings/:siteId/:assessmentId[/:findingTab]` patterns; those keep their handlers. */}
          <Route path={FINDINGS_PATH} element={<EstateFindingsFrame lens="all" client={estateIndex} />} />
          <Route path={FINDINGS_COST_PATH} element={<EstateFindingsFrame lens="cost" client={estateIndex} />} />
          <Route path={FINDINGS_RISKS_PATH} element={<EstateFindingsFrame lens="risks" client={estateIndex} />} />
          <Route
            path={FINDINGS_OPPORTUNITIES_PATH}
            element={<EstateFindingsFrame lens="opportunities" client={estateIndex} />}
          />
          <Route path={ACTIONS_PATH} element={<EstateActionsFrame client={estateIndex} />} />
          {/* W3-02: the estate Evidence root (`ESTATE_EVIDENCE_PATH`; a shell test pins the equality). */}
          <Route path={EVIDENCE_PATH} element={<EstateEvidenceFrame client={estateEvidenceMoney} />} />
          {/* W3-02 commit 4: the estate Financials root (`ESTATE_FINANCIALS_PATH`; a shell test pins the equality). */}
          <Route path={FINANCIALS_PATH} element={<EstateFinancialsFrame client={estateFinancials} />} />
          {/* W3-03 run 2: the estate Portfolio root (`PORTFOLIO_PATH`; a shell test pins the equality). */}
          <Route path={PORTFOLIO_ROOT_PATH} element={<EstatePortfolioFrame client={estateIndex} />} />
          {/* W6-01a: the global Incidents root (`INCIDENTS_PATH`). */}
          <Route path={INCIDENTS_PATH} element={<GlobalIncidentsFrame client={globalWork} />} />
          {/* W6-01b: the global Maintenance root, Corrective view (`MAINTENANCE_PATH`). */}
          <Route path={MAINTENANCE_PATH} element={<GlobalMaintenanceFrame client={globalWork} />} />
          {/* W6-01b B3: the global Maintenance root, Preventive view (`MAINTENANCE_PREVENTIVE_PATH`). */}
          <Route path={MAINTENANCE_PREVENTIVE_PATH} element={<GlobalPreventiveFrame client={globalWork} />} />
          {/* W6-01c C2: the work request Overview (`WORK_REQUEST_ROUTE_PATH`, `?site_id={site_code}`). */}
          <Route path={WORK_REQUEST_ROUTE_PATH} element={<WorkRequestOverviewFrame client={globalWork} />} />
          {[FINDING_ROUTE_PATH, FINDING_TAB_ROUTE_PATH].map((path) => (
            <Route
              key={path}
              path={path}
              element={
                <FindingDetailFrame
                  detail={siteDetail}
                  analytics={siteAnalytics}
                  evidence={siteEvidence}
                />
              }
            />
          ))}
          <Route
            path={LEGACY_SITE_CONFIGURATION_ROUTE_PATH}
            element={<LegacySiteConfigurationRedirect />}
          />
        </Route>
      </Route>
      {simulatorLabRoutes(
        flags,
        siteTemplateCatalog,
        siteCreation,
        SITES_PATH,
        scenarioCatalog,
        runSetup,
        siteDetail,
        now,
        siteDirectory,
        templateLineage,
        siteFoundation,
        coldScenarios,
        evScenarios,
      ).map((route) => (
        <Route key={route.path} path={route.path} element={route.element} />
      ))}
      <Route path="*" element={<RouteNotAvailableFrame />} />
    </Routes>
  );
}
