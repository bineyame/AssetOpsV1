import { UnavailableTab } from "../ui/UnavailableEntry";
import { FoundationSubtabs, foundationViewSegment } from "../sites/FoundationSubtabs";
import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import { Link, useLocation, useNavigate, useParams, useSearchParams } from "react-router-dom";

import { FindingDetail, type FindingDetailTab } from "../sites/FindingDetail";
import { SiteFindings } from "../sites/FindingsIndexes";
import { createActionClient, type ActionClient } from "../sites/actionClient";
import {
  actionIndexQuery,
  createActionIndexClient,
  type ActionIndexClient,
  type ActionIndexScope,
} from "../sites/actionIndexClient";
import { SiteWorkActions } from "../sites/SiteWorkActions";
import { SiteWorkIncidents } from "../sites/SiteWorkIncidents";
import { SiteWorkMaintenance } from "../sites/SiteWorkMaintenance";
import type { WorkTrail } from "../sites/siteWorkCases";
import { createWorkClient, defaultWorkWindow, workPageQuery, type WorkClient, type WorkKind, type WorkScope } from "../sites/workClient";
import {
  createFindingIndexClient,
  FINDING_INDEX_DOMAIN,
  type FindingIndexClient,
  type FindingIndexScope,
} from "../sites/findingIndexClient";
import { SiteFindingIndex } from "../sites/SiteFindingIndex";
import { createFindingClient, type FindingClient } from "../sites/findingClient";
import { ACTION_VIEWS, ACTION_VIEW_LABELS, SiteAction, type ActionSelector, type ActionView } from "../sites/SiteAction";
import { ChangesWorkPageHeader, NoChangeSelected, SiteFoundationChange, type SiteFoundationChangeLinks } from "../sites/SiteFoundationChange";
import { SiteRecommendation } from "../sites/SiteRecommendation";
import { createFinancialsClient, type FinancialsClient } from "../sites/financialsClient";
import { SiteAssumptions, SiteFinancialsOverview, type FinancialsLinks } from "../sites/SiteFinancials";
import { MiniScenarios } from "../sites/MiniScenarios";
import {
  MiniOpportunityPage,
  OPPORTUNITY_LOADING,
  OPPORTUNITY_ROOT_GAP,
  decisionRefusalCopy,
  renewableHref,
  useOpportunity,
} from "../sites/MiniOpportunity";
import { ALTERNATIVES_FINDING_UNAVAILABLE, MiniAlternatives } from "../sites/MiniAlternatives";
import { createMiniDecisionsClient, scenarioScopeSearch, type MiniDecisionsClient, type ScenarioScope } from "../sites/miniDecisionsClient";
import { SiteFinding } from "../sites/SiteFinding";
import { FindingSections, SiteFindingEvidence, type FindingSectionLink } from "../sites/SiteFindingEvidence";
import { SiteFindingHistory } from "../sites/SiteFindingHistory";
import { SitePerformance } from "../sites/SitePerformance";
import { BUILT_MINI_PAGES, MiniBackup, MiniFuel, MiniPerformanceSubtabs, MiniRenewable, MiniService } from "../sites/MiniPerformance";
import {
  createMiniDepthClient,
  isMiniDomain,
  renewableWindowFromParams,
  serviceWindowFromParams,
  type MiniDepthClient,
} from "../sites/miniDepthClient";
import { ColdFindingFrame, ColdPerformanceFrame, type ColdLinks } from "../sites/ColdAssessmentViews";
import { coldWindowFromParams, coldWindowSearch, type ColdAssessmentClient, type ColdWindowQuery } from "../sites/coldAssessmentClient";
import type { ColdSiteClient } from "../sites/coldSiteClient";
import { EvFindingFrame, EvSessionsFrame, evFindingHref } from "../sites/EvAssessmentViews";
import type { EvAssessmentClient } from "../sites/evAssessmentClient";
import { coldSiteRoutes, coldSiteScreen } from "./coldSiteRoutes";
import { createColdDepthClient, type ColdDepthClient } from "../sites/ColdDepthClient";
import { presentationProfileFor } from "../sites/presentationProfile";
import type { SiteAnalyticsClient } from "../sites/siteAnalyticsClient";
import type { SiteDetailClient } from "../sites/siteDirectoryClient";
import type { SiteEvidenceClient } from "../sites/siteEvidenceClient";
import type { SiteDetailReadModel } from "../sites/siteReadModel";
import { useSiteRecord } from "../sites/useSiteRecord";
import { Breadcrumbs, PageHeader, Panel, SITE_SCREEN_DESCRIPTIONS, SitePageHeader } from "../ui";
import { localView } from "../sites/findingPresentation";
import { deriveSiteView, siteSourceModeLabel } from "../sites/siteViewModel";
import { OperatorSiteTabs } from "./operatorSiteTabs";
import {
  FINDING_CHILD_VIEWS,
  FINDINGS_PATH,
  findingHref,
  siteActionHref,
  siteDetailHref,
  siteEvidenceHref,
  siteEvidenceAssessmentHref,
  siteEvidenceRecordHref,
  siteEvidenceAcceptedRecordHref,
  siteFindingHref,
  siteFindingViewHref,
  siteFindingAlternativesHref,
  siteFindingsHref,
  siteFinancialAssumptionsHref,
  siteFinancialScenariosHref,
  siteFinancialsHref,
  siteOpportunityHref,
  siteFoundationChangeHref,
  siteFoundationHref,
  siteFoundationViewHref,
  sitePerformanceHref,
  siteWorkHref,
  siteWorkIncidentsHref,
  siteWorkMaintenanceHref,
  type FindingChildView,
  type FindingTab,
} from "./operatorSiteRoutes";

/**
 * The T028 operator frames: Site > Performance, Site > Findings, the Findings
 * rail root and Finding detail. Each frame supplies the landmark, the trail
 * and the addresses, and composes the substrate (`frontend/src/sites/`) for
 * the body. All are operator routes, never gated: every body is read from
 * accepted evidence through the analytics read models.
 */

type LoadedSite = SiteDetailReadModel;

/** Loading, not-found and unavailable states shared by the site-scoped frames. */
export function SiteScoped({
  siteId,
  detail,
  title,
  headingId,
  children,
}: {
  siteId: string | undefined;
  detail: SiteDetailClient;
  title: string;
  headingId: string;
  children: (site: LoadedSite) => ReactNode;
}) {
  const result = useSiteRecord(siteId, detail);
  if (result === null) {
    return (
      <main aria-labelledby={headingId}>
        <PageHeader title={title} headingId={headingId} />
        <p>Loading the configured site.</p>
      </main>
    );
  }
  if (result.status !== "loaded") {
    const missing = result.status === "not_found";
    return (
      <main aria-labelledby={headingId}>
        <PageHeader title={missing ? "Site not found" : title} headingId={headingId} />
        <Panel
          heading={missing ? "No such site" : "Site unavailable"}
          headingId={`${headingId}-state`}
        >
          <p>
            {missing
              ? "No site with that site ID is configured. This is a statement that the site does not exist, not a site with nothing to show."
              : "The site store could not be read, so nothing is known about whether the site is configured."}
          </p>
        </Panel>
      </main>
    );
  }
  return <>{children(result.site)}</>;
}

export const SITE_PERFORMANCE_HEADING_ID = "site-performance-heading";

/** W2-03: the addresses the cold assessment screens link to, keeping the selected window. */
function coldLinks(siteId: string, window: ColdWindowQuery): ColdLinks {
  const search = coldWindowSearch(window);
  return {
    temperature: `${sitePerformanceHref(siteId, "temperature")}${search}`,
    backup: `${sitePerformanceHref(siteId, "backup")}${search}`,
    finding: (findingId) => `${siteFindingHref(siteId, findingId)}${search}`,
    record: (evidenceId) => siteEvidenceAcceptedRecordHref(siteId, evidenceId),
    analysis: (revisionId) => siteEvidenceAssessmentHref(siteId, revisionId),
  };
}

const COLD_PERFORMANCE_VIEWS: Record<string, "temperature" | "backup" | "cooling"> = { temperature: "temperature", backup: "backup", cooling: "cooling" };

const DEFAULT_COLD_DEPTH = createColdDepthClient();

const DEFAULT_MINI_DEPTH = createMiniDepthClient();

export function SitePerformanceFrame({
  detail,
  analytics,
  sitesPath,
  coldAssessment,
  evAssessment,
  miniDepth = DEFAULT_MINI_DEPTH,
  miniDecisions,
  coldDepth = DEFAULT_COLD_DEPTH,
}: {
  detail: SiteDetailClient;
  analytics: SiteAnalyticsClient;
  sitesPath: string;
  /** W2-03: the selected cold assessment reads; a COLDCHAIN Site renders `temperature` / `coldbackup` from them. */
  coldAssessment?: ColdAssessmentClient;
  /** W2-06: the selected EV session reads; an EV_CHARGING Site renders `sessions` from them. */
  evAssessment?: EvAssessmentClient;
  /** W4-02: the MINIGRID mini-depth reads; a MINIGRID Site renders `service|fuel|renewable|backup` from them. */
  miniDepth?: MiniDepthClient;
  /** W4-03 unit 7: the scoped opportunity list behind the renewable page's exact five-day CTA (S14). */
  miniDecisions?: MiniDecisionsClient;
  /** W5-01a C2: the selected cold depth reads; a COLDCHAIN Site renders `cooling` from them. */
  coldDepth?: ColdDepthClient;
}) {
  const { siteId, capabilityId } = useParams<{ siteId: string; capabilityId?: string }>();
  const [params] = useSearchParams();
  // W1-F2: the Dispatch route (and its Analysis view) carries the v69 Site page heading; the other
  // Performance subtabs keep the shared "Performance" heading until their own fidelity pass.
  const dispatchRoute = capabilityId === undefined || capabilityId === "dispatch";
  return (
    <SiteScoped
      siteId={siteId}
      detail={detail}
      title="Performance"
      headingId={SITE_PERFORMANCE_HEADING_ID}
    >
      {(site) => {
        const coldView = capabilityId === undefined ? "temperature" : COLD_PERFORMANCE_VIEWS[capabilityId];
        if (site.site_type === "EV_CHARGING" && evAssessment !== undefined && (capabilityId === undefined || capabilityId === "sessions")) {
          const window = coldWindowFromParams(params);
          return (
            <EvSessionsFrame
              siteId={site.site_id}
              siteName={site.display_name}
              mode={deriveSiteView(site).sourceMode}
              window={window}
              client={evAssessment}
              tabs={<OperatorSiteTabs siteId={siteId} current="Performance" />}
              parentTrail={[
                { label: "Sites", to: sitesPath },
                { label: site.display_name, to: siteDetailHref(site.site_id) },
              ]}
              sessionsHref={`${sitePerformanceHref(site.site_id, "sessions")}${coldWindowSearch(window)}`}
              findingHref={evFindingHref((id) => siteFindingHref(site.site_id, id), window)}
            />
          );
        }
        if (site.site_type === "COLDCHAIN" && coldAssessment !== undefined && coldView !== undefined) {
          const window = coldWindowFromParams(params);
          return (
            <ColdPerformanceFrame
              view={coldView}
              siteId={site.site_id}
              siteName={site.display_name}
              mode={deriveSiteView(site).sourceMode}
              window={window}
              client={coldAssessment}
              links={coldLinks(site.site_id, window)}
              tabs={<OperatorSiteTabs siteId={siteId} current="Performance" />}
              parentTrail={[
                { label: "Sites", to: sitesPath },
                { label: site.display_name, to: siteDetailHref(site.site_id) },
              ]}
              subtabHref={(id) => `${sitePerformanceHref(site.site_id, id)}${coldWindowSearch(window)}`}
              depth={coldDepth}
              routes={coldSiteRoutes(site.site_id)}
            />
          );
        }
        if (site.site_type === "MINIGRID" && isMiniDomain(capabilityId) && BUILT_MINI_PAGES.has(capabilityId)) {
          const timeZone = site.timezone || null;
          const pageHref = (search: string) => `${sitePerformanceHref(site.site_id, capabilityId)}${search}`;
          return (
            <main aria-labelledby={SITE_PERFORMANCE_HEADING_ID}>
              <Breadcrumbs
                trail={[
                  { label: "Sites", to: sitesPath },
                  { label: site.display_name, to: siteDetailHref(site.site_id) },
                  { label: "Performance" },
                ]}
              />
              <SitePageHeader
                siteName={site.display_name}
                siteId={site.site_id}
                mode={deriveSiteView(site).sourceMode}
                description={SITE_SCREEN_DESCRIPTIONS[capabilityId]}
                headingId={SITE_PERFORMANCE_HEADING_ID}
              />
              <OperatorSiteTabs siteId={siteId} current="Performance" />
              <MiniPerformanceSubtabs
                client={miniDepth}
                siteCode={site.site_id}
                profile={presentationProfileFor(site.site_type)}
                current={capabilityId}
                subtabHref={(id) => sitePerformanceHref(site.site_id, id)}
              />
              {capabilityId === "service" ? (
                <MiniService
                  client={miniDepth}
                  siteCode={site.site_id}
                  timeZone={timeZone}
                  window={timeZone === null ? null : serviceWindowFromParams(params, timeZone)}
                  pageHref={pageHref}
                />
              ) : capabilityId === "backup" ? (
                <MiniBackup
                  client={miniDepth}
                  siteCode={site.site_id}
                  timeZone={timeZone}
                  window={timeZone === null ? null : serviceWindowFromParams(params, timeZone)}
                  pageHref={pageHref}
                />
              ) : capabilityId === "fuel" ? (
                <MiniFuel
                  client={miniDepth}
                  siteCode={site.site_id}
                  timeZone={timeZone}
                  window={timeZone === null ? null : serviceWindowFromParams(params, timeZone)}
                  pageHref={pageHref}
                />
              ) : (
                <MiniRenewable
                  client={miniDepth}
                  decisions={miniDecisions ?? DEFAULT_MINI_DECISIONS}
                  opportunityHref={(opportunityId, knownAt) => siteOpportunityHref(site.site_id, opportunityId, knownAt)}
                  siteCode={site.site_id}
                  timeZone={timeZone}
                  window={timeZone === null ? null : renewableWindowFromParams(params, timeZone)}
                  pageHref={pageHref}
                />
              )}
            </main>
          );
        }
        return (
        <main aria-labelledby={SITE_PERFORMANCE_HEADING_ID}>
          <Breadcrumbs
            trail={[
              { label: "Sites", to: sitesPath },
              { label: site.display_name, to: siteDetailHref(site.site_id) },
              { label: "Performance" },
            ]}
          />
          {dispatchRoute ? (
            <SitePageHeader
              siteName={site.display_name}
              siteId={site.site_id}
              mode={deriveSiteView(site).sourceMode}
              description={SITE_SCREEN_DESCRIPTIONS[localView(params) === "analysis" ? "analysis" : "dispatch"]}
              headingId={SITE_PERFORMANCE_HEADING_ID}
            />
          ) : (
            <PageHeader
              title="Performance"
              headingId={SITE_PERFORMANCE_HEADING_ID}
              subtitle={`${site.display_name} · ${site.site_id}`}
            />
          )}
          <OperatorSiteTabs siteId={siteId} current="Performance" />
          <SitePerformance
            siteId={site.site_id}
            client={analytics}
            miniDepth={site.site_type === "MINIGRID" ? miniDepth : undefined}
            profile={presentationProfileFor(site.site_type)}
            capabilityId={capabilityId}
            subtabHref={(id) => sitePerformanceHref(site.site_id, id)}
            findingHref={(id) => findingHref(site.site_id, id)}
            findings={DEFAULT_FINDINGS}
            siteFindingHref={(id) => siteFindingHref(site.site_id, id)}
            findingAlternativesHref={(id, rev) => siteFindingAlternativesHref(site.site_id, id, rev)}
            findingAnalysisHref={(id) => findingHref(site.site_id, id, "analysis")}
            recordHref={(link) =>
              siteEvidenceRecordHref(
                site.site_id,
                `${link.device_id}/${link.signal_id}`,
                link.message_id,
              )
            }
            coverageHref={(id) => siteEvidenceAssessmentHref(site.site_id, id)}
          />
        </main>
        );
      }}
    </SiteScoped>
  );
}

export const SITE_FINDINGS_HEADING_ID = "site-findings-page-heading";

const DEFAULT_FINDING_INDEX = createFindingIndexClient();

/** Today's UTC day, `[00:00Z, next 00:00Z)`: the window when the URL names none. */
function todayWindow(now: Date = new Date()): { from: string; to: string } {
  const day = now.toISOString().slice(0, 10);
  const next = new Date(`${day}T00:00:00Z`);
  next.setUTCDate(next.getUTCDate() + 1);
  return { from: `${day}T00:00:00Z`, to: `${next.toISOString().slice(0, 10)}T00:00:00Z` };
}

/**
 * S4-04: the index scope persisted in the URL (`?domain=&from=&to=&limit=&cursor=`),
 * so reload, back and a shared link reopen the same window and page.
 */
export function findingIndexScopeQuery(scope: FindingIndexScope): string {
  const query = new URLSearchParams({ domain: scope.domain, from: scope.from, to: scope.to });
  if (scope.limit) query.set("limit", String(scope.limit));
  if (scope.cursor) query.set("cursor", scope.cursor);
  return query.toString();
}

function scopeFromQuery(params: URLSearchParams): FindingIndexScope {
  const today = todayWindow();
  const limit = Number(params.get("limit"));
  return {
    domain: params.get("domain") ?? FINDING_INDEX_DOMAIN,
    from: params.get("from") ?? today.from,
    to: params.get("to") ?? today.to,
    limit: params.get("limit") === null || !Number.isFinite(limit) ? null : limit,
    cursor: params.get("cursor"),
  };
}

export function SiteFindingsFrame({
  detail,
  analytics,
  sitesPath,
  findingIndex = DEFAULT_FINDING_INDEX,
}: {
  detail: SiteDetailClient;
  analytics: SiteAnalyticsClient;
  sitesPath: string;
  findingIndex?: FindingIndexClient;
}) {
  const { siteId } = useParams<{ siteId: string }>();
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const scope = scopeFromQuery(params);
  return (
    <SiteScoped
      siteId={siteId}
      detail={detail}
      title="Findings"
      headingId={SITE_FINDINGS_HEADING_ID}
    >
      {(site) => (
        <main aria-labelledby={SITE_FINDINGS_HEADING_ID}>
          <Breadcrumbs
            trail={[
              { label: "Sites", to: sitesPath },
              { label: site.display_name, to: siteDetailHref(site.site_id) },
              { label: "Findings" },
            ]}
          />
          {/* W1-F5a carry 1: the mock's Site page heading. */}
          <SitePageHeader
            siteName={site.display_name}
            siteId={site.site_id}
            mode={siteSourceModeLabel(site)}
            description={SITE_SCREEN_DESCRIPTIONS.sitefindings}
            headingId={SITE_FINDINGS_HEADING_ID}
          />
          <OperatorSiteTabs siteId={siteId} current="Findings" />
          <SiteFindingIndex
            siteId={site.site_id}
            opportunityHelper={site.site_type === "MINIGRID"}
            client={findingIndex}
            scope={scope}
            links={{
              scope: (next) => `${siteFindingsHref(site.site_id)}?${findingIndexScopeQuery(next)}`,
              finding: (id, revisionId) => siteFindingHref(site.site_id, id, revisionId),
            }}
            onScope={(next) => navigate(`${siteFindingsHref(site.site_id)}?${findingIndexScopeQuery(next)}`)}
            fallback={
              <SiteFindings
                siteId={site.site_id}
                client={analytics}
                profile={presentationProfileFor(site.site_type)}
                findingHref={(id, tab) => findingHref(site.site_id, id, tab)}
                dispatchHref={sitePerformanceHref(site.site_id, "dispatch")}
              />
            }
          />
        </main>
      )}
    </SiteScoped>
  );
}

export const FINDING_HEADING_ID = "finding-heading";
const DEFAULT_FINDINGS = createFindingClient();
const DEFAULT_ACTIONS = createActionClient();

const FINDING_TABS: FindingTab[] = ["overview", "analysis", "evidence", "alternatives"];

export function FindingDetailFrame({
  detail,
  analytics,
  evidence,
  findings = DEFAULT_FINDINGS,
}: {
  detail: SiteDetailClient;
  analytics: SiteAnalyticsClient;
  evidence: SiteEvidenceClient;
  findings?: FindingClient;
}) {
  const { siteId, assessmentId, findingTab } = useParams<{
    siteId: string;
    assessmentId: string;
    findingTab?: string;
  }>();
  const [title, setTitle] = useState("Finding");
  const tab: FindingDetailTab = FINDING_TABS.includes(findingTab as FindingTab)
    ? (findingTab as FindingDetailTab)
    : "overview";
  return (
    <SiteScoped siteId={siteId} detail={detail} title="Finding" headingId={FINDING_HEADING_ID}>
      {(site) => (
        <main aria-labelledby={FINDING_HEADING_ID}>
          <Breadcrumbs
            trail={[
              { label: "Findings", to: FINDINGS_PATH },
              { label: site.display_name, to: siteFindingsHref(site.site_id) },
              { label: title },
            ]}
          />
          <PageHeader
            title={title}
            headingId={FINDING_HEADING_ID}
            subtitle={`${site.display_name} · ${site.site_id}`}
          />
          <FindingDetail
            siteId={site.site_id}
            siteName={site.display_name}
            assessmentId={assessmentId ?? ""}
            tab={tab}
            client={analytics}
            evidence={evidence}
            profile={presentationProfileFor(site.site_type)}
            tabHref={(next) => findingHref(site.site_id, assessmentId ?? "", next)}
            dispatchHref={`${sitePerformanceHref(site.site_id, "dispatch")}?interval=${encodeURIComponent(assessmentId ?? "")}`}
            currentResultsHref={sitePerformanceHref(site.site_id, "dispatch")}
            evidencePageHref={siteEvidenceHref(site.site_id)}
            findings={findings}
            durableEvidenceHref={(findingId) => siteFindingViewHref(site.site_id, findingId, "evidence")}
            onLoaded={(loaded) =>
              setTitle(
                loaded.finding_id === null
                  ? "Assessed period"
                  : `Finding: ${loaded.reading?.outcome ?? "Assessed period"}`,
              )
            }
          />
        </main>
      )}
    </SiteScoped>
  );
}

const SITE_FINDING_HEADING_ID = "site-finding-heading";

/**
 * S4-01: one durable Finding of an imported Site, at
 * `/sites/{site}/findings/{finding}[?revision_id=]`. The trail returns to the
 * Site and its Findings tab; the body links to the Dispatch days it covers.
 *
 * S4-03: the same frame renders the root's named child views at
 * `/sites/{site}/findings/{finding}/{view}[?revision_id=]` (`FINDING_CHILD_VIEWS`).
 * The section links keep the exact selected version (Evidence and History).
 *
 * W4-03 unit 6b (u5 6b, u6): a MINIGRID Site's Finding is the canonical mini Finding (`CanonicalMiniFinding`); a
 * COLDCHAIN or EV_CHARGING Site's Finding root is its domain frame, and its child addresses are a noninteractive
 * section gap with a link back to that root (u6 ruling 3).
 */
const FINDING_SECTION_LABELS: Record<FindingChildView, string> = {
  evidence: "Evidence",
  history: "History",
  recommendation: "Recommendation",
  alternatives: "Alternatives",
};

/** u6 ruling 4: the plain helper beside the canonical mini row on child views (outside the guarded tab). */
export const ANALYSIS_HELPER_ALTERNATIVES =
  "Analysis unavailable for this authored alternative; use the Finding overview and evidence.";
export const ANALYSIS_HELPER_SECTION = "Analysis unavailable for this Finding section; use the Finding overview and evidence.";
/** u6 ruling 1: the W1 detail supplies no public Finding code. */
export const FINDING_CODE_UNAVAILABLE = "Finding code unavailable";
/** u6 ruling 3: a cold or EV Finding child address. */
export const FINDING_SECTION_UNAVAILABLE = "Finding section unavailable for this site.";
/** u6b ruling 13: a cold/EV Finding root whose domain read is not composed; never the generic W1 read. */
export const FINDING_DOMAIN_UNAVAILABLE = "This site's Finding view is unavailable.";

export function SiteFindingFrame({
  detail,
  sitesPath,
  findings = DEFAULT_FINDINGS,
  actions = DEFAULT_ACTIONS,
  coldAssessment,
  evAssessment,
  miniDecisions = DEFAULT_MINI_DECISIONS,
}: {
  detail: SiteDetailClient;
  sitesPath: string;
  findings?: FindingClient;
  actions?: ActionClient;
  /** W2-03: a COLDCHAIN Site's Finding renders `cold-finding` or `cold-finding-excursion` by its kind. */
  coldAssessment?: ColdAssessmentClient;
  /** W2-06: an EV_CHARGING Site's Finding renders `ev-finding` from the selected EV reads. */
  evAssessment?: EvAssessmentClient;
  /** W4-03 unit 6b: the authored Alternatives read of the canonical mini Finding. */
  miniDecisions?: MiniDecisionsClient;
}) {
  const { siteId, findingId, findingView } = useParams<{ siteId: string; findingId: string; findingView?: string }>();
  const [params] = useSearchParams();
  const revisionId = params.get("revision_id");
  const [title, setTitle] = useState("Finding");
  const onTitle = useCallback((next: string) => setTitle(next), []);
  const view: FindingChildView | "finding" | null =
    findingView === undefined
      ? "finding"
      : (FINDING_CHILD_VIEWS as readonly string[]).includes(findingView)
        ? (findingView as FindingChildView)
        : null;
  return (
    <SiteScoped siteId={siteId} detail={detail} title="Finding" headingId={SITE_FINDING_HEADING_ID}>
      {(site) => {
        const id = findingId ?? "";
        // u6b ruling 13: a cold/EV `/recommendation` address stays in its domain frame's Overview | Recommendation row.
        const domainRoot = findingView === undefined || findingView === "recommendation";
        const domainSite = site.site_type === "COLDCHAIN" || site.site_type === "EV_CHARGING";
        if (site.site_type === "EV_CHARGING" && evAssessment !== undefined && domainRoot) {
          return (
            <EvFindingFrame
              siteId={site.site_id}
              siteName={site.display_name}
              findingId={id}
              window={coldWindowFromParams(params)}
              client={evAssessment}
              tabs={<OperatorSiteTabs siteId={siteId} current="Findings" />}
              parentTrail={[
                { label: "Sites", to: sitesPath },
                { label: site.display_name, to: siteDetailHref(site.site_id) },
                { label: "Findings", to: siteFindingsHref(site.site_id) },
              ]}
            />
          );
        }
        if (site.site_type === "COLDCHAIN" && coldAssessment !== undefined && domainRoot) {
          const window = coldWindowFromParams(params);
          return (
            <ColdFindingFrame
              siteId={site.site_id}
              siteName={site.display_name}
              findingId={id}
              window={window}
              client={coldAssessment}
              links={coldLinks(site.site_id, window)}
              tabs={<OperatorSiteTabs siteId={siteId} current="Findings" />}
              parentTrail={[
                { label: "Sites", to: sitesPath },
                { label: site.display_name, to: siteDetailHref(site.site_id) },
                { label: "Findings", to: siteFindingsHref(site.site_id) },
              ]}
            />
          );
        }
        if (site.site_type === "MINIGRID") {
          return (
            <CanonicalMiniFinding
              site={site}
              routeSiteId={siteId}
              findingId={id}
              view={view}
              revisionId={revisionId}
              title={title}
              onTitle={onTitle}
              findings={findings}
              actions={actions}
              miniDecisions={miniDecisions}
            />
          );
        }
        // u6 ruling 3: a cold/EV (or other non-mini) Finding has no W1 canonical section row. A child address is a
        // noninteractive gap with a real link to the domain Finding root; it issues no W4-03 Alternatives read.
        const root = `${siteFindingHref(site.site_id, id)}${coldWindowSearch(coldWindowFromParams(params))}`;
        return (
          <main aria-labelledby={SITE_FINDING_HEADING_ID}>
            <Breadcrumbs
              trail={[
                { label: "Sites", to: sitesPath },
                { label: site.display_name, to: siteDetailHref(site.site_id) },
                { label: "Findings", to: siteFindingsHref(site.site_id) },
                view === "finding" ? { label: "Finding" } : { label: "Finding", to: root },
              ]}
            />
            <PageHeader title={title} headingId={SITE_FINDING_HEADING_ID} subtitle={`${site.display_name} · finding`} />
            <OperatorSiteTabs siteId={siteId} current="Findings" />
            {domainSite && domainRoot ? (
              <Panel heading="Finding" headingId="site-finding-domain-unavailable-heading">
                <p data-finding-domain-unavailable>{FINDING_DOMAIN_UNAVAILABLE}</p>
              </Panel>
            ) : view === "finding" ? (
              <SiteFinding
                siteId={site.site_id}
                findingId={id}
                client={findings}
                onTitle={onTitle}
                links={{
                  finding: (other, rev) => siteFindingHref(site.site_id, other, rev),
                  dispatch: (day) => `${sitePerformanceHref(site.site_id, "dispatch")}?day=${encodeURIComponent(day)}`,
                  evidence: siteEvidenceHref(site.site_id),
                  findingEvidence: () => root,
                  history: () => root,
                  recommendation: () => root,
                }}
              />
            ) : (
              <Panel heading="Finding section" headingId="site-finding-section-unavailable-heading">
                <p data-finding-section-unavailable={findingView}>
                  {FINDING_SECTION_UNAVAILABLE} <Link to={root}>Open Finding overview</Link>
                </p>
              </Panel>
            )}
          </main>
        );
      }}
    </SiteScoped>
  );
}

type MiniSelection =
  | { status: "loading" }
  | { status: "loaded"; revisionId: string; title: string }
  | { status: "refused" };

/**
 * W4-03 unit 6b: the canonical mini Finding shell. Its six context tabs are, in order, `Overview`, unavailable
 * `Analysis`, `Evidence`, live `Alternatives`, `Recommendation`, `History` (u5 6b). One W1 Finding read
 * (`getFinding(site, finding, revision_id|null)`) resolves the exact selected revision before any Alternatives href or
 * Alternatives read exists, and the same resolved selection pins the sibling tabs (u6 ruling 5). The global breadcrumb
 * is `Findings › Finding code unavailable › {section} · site: {Site}` (u6 ruling 1, u5 6b).
 */
function CanonicalMiniFinding({
  site,
  routeSiteId,
  findingId: id,
  view,
  revisionId,
  title,
  onTitle,
  findings,
  actions,
  miniDecisions,
}: {
  site: SiteDetailReadModel;
  routeSiteId: string | undefined;
  findingId: string;
  view: FindingChildView | "finding" | null;
  revisionId: string | null;
  title: string;
  onTitle: (next: string) => void;
  findings: FindingClient;
  actions: ActionClient;
  miniDecisions: MiniDecisionsClient;
}) {
  const navigate = useNavigate();
  const [selection, setSelection] = useState<MiniSelection>({ status: "loading" });
  // The address replaced with the revision this read already resolved is the same selection: no second read.
  const settled = useRef<{ key: string; revisionId: string } | null>(null);
  useEffect(() => {
    const key = `${site.site_id}/${id}`;
    if (revisionId !== null && settled.current?.key === key && settled.current.revisionId === revisionId) return;
    let active = true;
    setSelection({ status: "loading" });
    void findings.getFinding(site.site_id, id, revisionId).then((read) => {
      if (!active) return;
      // u6 ruling 6: only a same-Site canonical W1 read of this exact Finding resolves a revision.
      // u6b ruling 6: a supplied UUID is an input to W1 validation; a different selected revision never replaces it.
      if (
        read.status === "loaded" &&
        read.value.site_code === site.site_id &&
        read.value.finding.id.toLowerCase() === id.toLowerCase() &&
        read.value.selection.revision_id !== "" &&
        (revisionId === null || read.value.selection.revision_id.toLowerCase() === revisionId.toLowerCase())
      ) {
        settled.current = { key, revisionId: read.value.selection.revision_id };
        setSelection({ status: "loaded", revisionId: read.value.selection.revision_id, title: read.value.revision.title });
      } else {
        settled.current = null;
        setSelection({ status: "refused" });
      }
    });
    return () => {
      active = false;
    };
  }, [findings, site.site_id, id, revisionId]);
  const resolved = selection.status === "loaded" ? selection.revisionId : null;
  // u6 ruling 5: an Alternatives address without `revision_id` is replaced with the resolved exact revision.
  useEffect(() => {
    if (view === "alternatives" && revisionId === null && resolved !== null) {
      navigate(siteFindingAlternativesHref(site.site_id, id, resolved), { replace: true });
    }
  }, [view, revisionId, resolved, navigate, site.site_id, id]);
  useEffect(() => {
    if (view === "alternatives" && selection.status === "loaded") onTitle(selection.title);
  }, [view, selection, onTitle]);

  // u6b ruling 6: a revision-carrying sibling, Overview or money href exists only for the loaded W1 selection; before
  // that each sibling is noninteractive text and the money link is omitted, so no raw `revision_id` leaks.
  const pinned = resolved;
  const child = (c: FindingChildView): FindingSectionLink =>
    resolved === null
      ? { id: c, gap: FINDING_SECTION_LABELS[c] }
      : { id: c, label: FINDING_SECTION_LABELS[c], href: siteFindingViewHref(site.site_id, id, c, resolved) };
  const sections: FindingSectionLink[] = [
    resolved === null
      ? { id: "finding", gap: "Overview" }
      : { id: "finding", label: "Overview", href: siteFindingHref(site.site_id, id, resolved) },
    { id: "analysis", label: "Analysis", unavailable: true },
    child("evidence"),
    resolved === null
      ? { id: "alternatives", gap: ALTERNATIVES_FINDING_UNAVAILABLE }
      : { id: "alternatives", label: "Alternatives", href: siteFindingAlternativesHref(site.site_id, id, resolved) },
    child("recommendation"),
    child("history"),
  ];
  const section = view === "finding" ? "Overview" : view === null ? null : FINDING_SECTION_LABELS[view];
  const dispatch = (day: string, intervalRevisionId?: string | null) =>
    `${sitePerformanceHref(site.site_id, "dispatch")}?day=${encodeURIComponent(day)}` +
    (intervalRevisionId ? `&revision=${encodeURIComponent(intervalRevisionId)}` : "");
  return (
    <main aria-labelledby={SITE_FINDING_HEADING_ID}>
      <nav className="breadcrumbs mini-finding-crumbs" aria-label="Breadcrumb" data-mini-finding-crumbs>
        <ol className="breadcrumbs__list">
          <li className="breadcrumbs__item">
            <Link to={FINDINGS_PATH}>Findings</Link>
          </li>
          {selection.status === "loaded" ? (
            <li className="breadcrumbs__item">
              <span data-finding-code-gap>{FINDING_CODE_UNAVAILABLE}</span>
            </li>
          ) : null}
          {section === null ? null : (
            <li className="breadcrumbs__item">
              <span className="breadcrumbs__current" aria-current="page">
                {section}
              </span>
            </li>
          )}
        </ol>
        <span className="mini-finding-crumbs__site" data-mini-finding-site>
          <span className="mini-finding-crumbs__lead">· site:</span>{" "}
          <Link to={siteDetailHref(site.site_id)}>{site.display_name}</Link>
        </span>
      </nav>
      <PageHeader
        title={title}
        headingId={SITE_FINDING_HEADING_ID}
        subtitle={`${site.display_name} · generator support finding`}
        // H3 (final review; build-spec ledger l.186): Alternatives carries the v69 `Open site` header action, which
        // resolves the authorized Site Overview, as the Opportunity frame does.
        actions={
          view === "alternatives" ? (
            <Link to={siteDetailHref(site.site_id)} data-alternatives-open-site>
              Open site
            </Link>
          ) : undefined
        }
      />
      {/* uF 3 (final review M6): the v69 Alternatives screen is a Findings surface with no Site tab row; every other
          W1 Finding view keeps it. */}
      {view === "alternatives" ? null : <OperatorSiteTabs siteId={routeSiteId} current="Findings" />}
      {view === null ? (
        <Panel heading="No such Finding section" headingId="site-finding-section-missing-heading">
          <p data-finding-read="not_found">
            A Finding has no section with that name. <Link to={siteFindingHref(site.site_id, id, pinned)}>Open the Finding</Link>
          </p>
        </Panel>
      ) : (
        <>
          {/* W1-F3: the money link sits on the section-tab line; W1-F4: on Recommendation it is a qualified line inside "Proposed intervention" instead. */}
          <FindingSections
            sections={sections}
            current={view}
            aside={
              view === "recommendation" || resolved === null ? undefined : (
                <span className="finding-financials-link" data-finding-financials-link>
                  <Link to={siteFinancialsHref(site.site_id, { findingId: id, revisionId: pinned })}>
                    What this finding means in money
                  </Link>
                </span>
              )
            }
            helper={
              view === "finding"
                ? undefined
                : view === "alternatives"
                  ? ANALYSIS_HELPER_ALTERNATIVES
                  : ANALYSIS_HELPER_SECTION
            }
          />
          {view === "alternatives" ? (
            selection.status === "loaded" && revisionId !== null ? (
              <MiniAlternatives
                key={`${site.site_id}|${id}|${selection.revisionId}`}
                siteCode={site.site_id}
                findingId={id}
                revisionId={selection.revisionId}
                client={miniDecisions}
                recordHref={(evidenceId) => siteEvidenceAcceptedRecordHref(site.site_id, evidenceId)}
              />
            ) : selection.status === "refused" ? (
              <p className="mini-alternatives-note" data-alternatives-finding-unavailable>
                {ALTERNATIVES_FINDING_UNAVAILABLE}
              </p>
            ) : (
              <p data-alternatives-finding-loading>Loading the Finding.</p>
            )
          ) : view === "evidence" ? (
            <SiteFindingEvidence
              siteId={site.site_id}
              findingId={id}
              client={findings}
              onTitle={onTitle}
              links={{
                evidence: (rev) => siteFindingViewHref(site.site_id, id, "evidence", rev),
                finding: (other, rev) => siteFindingHref(site.site_id, other, rev),
                dispatch,
                record: (evidenceId) => siteEvidenceAcceptedRecordHref(site.site_id, evidenceId),
                history: (rev) => siteFindingViewHref(site.site_id, id, "history", rev),
              }}
            />
          ) : view === "recommendation" ? (
            <SiteRecommendation
              siteId={site.site_id}
              findingId={id}
              client={actions}
              onTitle={onTitle}
              links={{
                finding: (rev) => siteFindingHref(site.site_id, id, rev),
                action: (actionId) => siteActionHref(site.site_id, actionId),
                actionChild: (actionId, view, chosen) => siteActionHref(site.site_id, actionId, view, chosen),
                money: (rev) => siteFinancialsHref(site.site_id, { findingId: id, revisionId: rev }),
              }}
            />
          ) : view === "history" ? (
            <SiteFindingHistory
              siteId={site.site_id}
              findingId={id}
              client={findings}
              onTitle={onTitle}
              links={{
                history: (rev) => siteFindingViewHref(site.site_id, id, "history", rev),
                evidence: (rev) => siteFindingViewHref(site.site_id, id, "evidence", rev),
                finding: (other, rev) => siteFindingHref(site.site_id, other, rev),
                otherHistory: (other) => siteFindingViewHref(site.site_id, other, "history"),
              }}
            />
          ) : (
            <SiteFinding
              siteId={site.site_id}
              findingId={id}
              client={findings}
              onTitle={onTitle}
              links={{
                finding: (other, rev) => siteFindingHref(site.site_id, other, rev),
                dispatch,
                evidence: siteEvidenceHref(site.site_id),
                findingEvidence: (rev) => siteFindingViewHref(site.site_id, id, "evidence", rev),
                history: (rev) => siteFindingViewHref(site.site_id, id, "history", rev),
                recommendation: (rev) => siteFindingViewHref(site.site_id, id, "recommendation", rev),
              }}
            />
          )}
        </>
      )}
    </main>
  );
}

export const SITE_FINANCIALS_HEADING_ID = "site-financials-heading";
const DEFAULT_FINANCIALS = createFinancialsClient();
const FINANCIALS_SECTIONS_LABEL = "Financials sections";

/**
 * The Financials subtab row (Overview, Assumptions, Scenarios). W2-04: a cold Site's Financials screens reuse it with
 * the selected window (`search`) carried in both links. W4-03 unit 6a (closure 4 S13): split by Site type - a MINIGRID
 * Site's Scenarios is a live route; every other Site keeps the mock's Scenarios as "Not available yet" text (one
 * occurrence, cold's). EV Financials has its own Overview/Assumptions pair in `EvSiteViews.tsx` and no Scenarios slot.
 */
export function FinancialsSections({
  siteId,
  view,
  search = "",
  scenarios = "unavailable",
}: {
  siteId: string;
  view: "overview" | "assumptions" | "scenarios";
  search?: string;
  scenarios?: "live" | "unavailable";
}) {
  const links: [string, string, string][] = [
    ["overview", "Overview", `${siteFinancialsHref(siteId)}${search}`],
    ["assumptions", "Assumptions", `${siteFinancialAssumptionsHref(siteId)}${search}`],
  ];
  if (scenarios === "live") links.push(["scenarios", "Scenarios", siteFinancialScenariosHref(siteId)]);
  return (
    <nav className="site-tabs site-subtabs" aria-label={FINANCIALS_SECTIONS_LABEL}>
      <ol className="site-tabs__list">
        {links.map(([id, label, href]) => (
          <li className="site-tabs__item" key={id}>
            <Link className="site-tabs__link" to={href} data-financials-section={id} aria-current={id === view ? "page" : undefined}>
              {label}
            </Link>
          </li>
        ))}
        {scenarios === "live" ? null : <UnavailableTab label="Scenarios" />}
      </ol>
    </nav>
  );
}

const DEFAULT_MINI_DECISIONS = createMiniDecisionsClient();


export const SITE_OPPORTUNITY_HEADING_ID = "site-opportunity-heading";

/**
 * W4-03 unit 7: the typed five-day Opportunity detail at `/sites/:siteId/opportunities/:opportunityId`. Overview is
 * the only context tab (closure 4 B5). u7 PR-9 (1): the breadcrumb is exactly
 * `Findings › {opportunity.code} › Overview · site: {Site}`; the `Findings` slot is the noninteractive root gap, the
 * code (only once loaded) and `Overview` are text, and the Site suffix links the authorized Site Overview. There is
 * no `Sites` or `Renewable evaluation` slot; `Open renewable evaluation` stays the separate exact study link.
 */
export function SiteOpportunityFrame({
  detail,
  miniDecisions = DEFAULT_MINI_DECISIONS,
}: {
  detail: SiteDetailClient;
  /** Kept for the shared frame signature; u7 PR-9 removed the `Sites` breadcrumb slot. */
  sitesPath: string;
  miniDecisions?: MiniDecisionsClient;
}) {
  const { siteId, opportunityId } = useParams<{ siteId: string; opportunityId: string }>();
  // PR-12.6: `?known_at=` is parsed and preserved as given; no query means current time.
  const [params] = useSearchParams();
  const knownAt = params.getAll("known_at");
  return (
    <SiteScoped siteId={siteId} detail={detail} title="Opportunity" headingId={SITE_OPPORTUNITY_HEADING_ID}>
      {(site) => (
        <OpportunityScreen site={site} opportunityId={opportunityId ?? ""} client={miniDecisions} knownAt={knownAt} />
      )}
    </SiteScoped>
  );
}

function OpportunityScreen({
  site,
  opportunityId,
  client,
  knownAt,
}: {
  site: LoadedSite;
  opportunityId: string;
  client: MiniDecisionsClient;
  knownAt: readonly string[];
}) {
  const mini = site.site_type === "MINIGRID";
  const read = useOpportunity(client, site.site_id, opportunityId, mini, knownAt);
  const loaded = mini && read !== null && read.status === "loaded" && read.value.opportunity !== null ? read.value : null;
  const renewable =
    loaded === null ? null : renewableHref(loaded, site.site_id, sitePerformanceHref(site.site_id, "renewable"));
  return (
    <main aria-labelledby={SITE_OPPORTUNITY_HEADING_ID} className="mini-opportunity-screen">
      <nav className="breadcrumbs mini-finding-crumbs" aria-label="Breadcrumb" data-opportunity-crumbs>
        <ol className="breadcrumbs__list">
          <li className="breadcrumbs__item">
            <span className="mini-opportunity-crumbs__root" data-opportunity-root>
              {OPPORTUNITY_ROOT_GAP}
            </span>
          </li>
          {loaded === null ? null : (
            <li className="breadcrumbs__item">
              <span data-opportunity-code>{loaded.opportunity!.code}</span>
            </li>
          )}
          <li className="breadcrumbs__item">
            <span className="breadcrumbs__current" aria-current="page">
              Overview
            </span>
          </li>
        </ol>
        <span className="mini-finding-crumbs__site" data-opportunity-crumb-site>
          <span className="mini-finding-crumbs__lead">· site:</span>{" "}
          <Link to={siteDetailHref(site.site_id)}>{site.display_name}</Link>
        </span>
      </nav>
      <PageHeader
        title={`Productive-use headroom at ${site.display_name}`}
        headingId={SITE_OPPORTUNITY_HEADING_ID}
        subtitle={SITE_SCREEN_DESCRIPTIONS.opportunity}
        actions={<Link to={siteDetailHref(site.site_id)}>Open site</Link>}
      />
      <nav className="site-tabs site-subtabs" aria-label="Opportunity sections" data-opportunity-tabs>
        <ol className="site-tabs__list">
          <li className="site-tabs__item">
            <Link className="site-tabs__link" to={siteOpportunityHref(site.site_id, opportunityId, knownAt)} aria-current="page">
              Overview
            </Link>
          </li>
        </ol>
      </nav>
      {!mini ? (
        <Panel heading="Opportunity" headingId="site-opportunity-unsupported-heading">
          <p data-opportunity-site-type-unsupported>Opportunities are read for mini-grid sites only.</p>
        </Panel>
      ) : read === null ? (
        <p role="status">{OPPORTUNITY_LOADING}</p>
      ) : read.status !== "loaded" ? (
        <div
          className="page-refusal"
          role="status"
          data-opportunity-refusal={read.status === "refused" ? read.code : "unavailable"}
        >
          <p>{decisionRefusalCopy(read)}</p>
        </div>
      ) : loaded === null ? (
        <div className="page-refusal" role="status" data-opportunity-refusal="SITE_ROLE_UNSUPPORTED">
          <p>Opportunities are read for mini-grid sites only.</p>
        </div>
      ) : (
        <MiniOpportunityPage
          body={loaded}
          renewable={renewable}
          recordHref={(evidenceId) => siteEvidenceAcceptedRecordHref(site.site_id, evidenceId)}
        />
      )}
    </main>
  );
}

/**
 * S4-02a: Site > Financials (Overview with the Finding bridge) and Financials > Assumptions. W1-F5b
 * (D-2026-10-17-f5-subtabs-and-contact): the mock's Scenarios subtab is shown in its place as "Not available yet"
 * text, never a link or a route. W4-03 unit 6a: a MINIGRID Site's Scenarios is the live `scenarios` view.
 */
export function SiteFinancialsFrame({
  detail,
  sitesPath,
  view,
  financials = DEFAULT_FINANCIALS,
  coldSite,
  coldAssessment,
  miniDecisions = DEFAULT_MINI_DECISIONS,
}: {
  detail: SiteDetailClient;
  sitesPath: string;
  view: "overview" | "assumptions" | "scenarios";
  financials?: FinancialsClient;
  /** W2-04: a COLDCHAIN Site renders `cold-financials` / `cold-assumptions` from these reads (read-only). */
  coldSite?: ColdSiteClient;
  coldAssessment?: ColdAssessmentClient;
  /** W4-03 unit 6a: the mini scenario list read. */
  miniDecisions?: MiniDecisionsClient;
}) {
  const { siteId } = useParams<{ siteId: string }>();
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const title = view === "assumptions" ? "Financial assumptions" : view === "scenarios" ? "Financial scenarios" : "Financials";
  const scope: ScenarioScope = {
    from: params.get("from"),
    to: params.get("to"),
    known_at: params.get("known_at"),
    cursor: params.get("cursor"),
  };
  const onScope = useCallback(
    (next: ScenarioScope, replace: boolean) => navigate({ search: scenarioScopeSearch(next) }, { replace }),
    [navigate],
  );
  return (
    <SiteScoped siteId={siteId} detail={detail} title={title} headingId={SITE_FINANCIALS_HEADING_ID}>
      {(site) => {
        if (view === "scenarios") {
          return (
            <main aria-labelledby={SITE_FINANCIALS_HEADING_ID}>
              <Breadcrumbs
                trail={[
                  { label: "Sites", to: sitesPath },
                  { label: site.display_name, to: siteDetailHref(site.site_id) },
                  { label: "Financials", to: siteFinancialsHref(site.site_id) },
                  { label: "Scenarios" },
                ]}
              />
              <SitePageHeader
                siteName={site.display_name}
                siteId={site.site_id}
                mode={siteSourceModeLabel(site)}
                description={SITE_SCREEN_DESCRIPTIONS.scenarios}
                headingId={SITE_FINANCIALS_HEADING_ID}
              />
              <OperatorSiteTabs siteId={siteId} current="Financials" />
              <FinancialsSections
                siteId={site.site_id}
                view="scenarios"
                scenarios={site.site_type === "MINIGRID" ? "live" : "unavailable"}
              />
              {site.site_type === "MINIGRID" ? (
                <MiniScenarios siteCode={site.site_id} client={miniDecisions} scope={scope} onScope={onScope} />
              ) : (
                <Panel heading="Financial scenarios" headingId="site-scenarios-unsupported-heading">
                  <p data-scenarios-site-type-unsupported>Scenarios are read for mini-grid sites only.</p>
                </Panel>
              )}
            </main>
          );
        }
        if (site.site_type === "COLDCHAIN" && coldSite !== undefined && coldAssessment !== undefined) {
          return coldSiteScreen({
            view: view === "assumptions" ? "assumptions" : "financials",
            site,
            params,
            sections: <FinancialsSections siteId={site.site_id} view={view} search={coldWindowSearch(coldWindowFromParams(params))} />,
            coldSite,
            coldAssessment,
            tabs: <OperatorSiteTabs siteId={siteId} current="Financials" />,
            sitesPath,
          });
        }
        const links: FinancialsLinks = {
          finding: (findingId, rev) => siteFindingHref(site.site_id, findingId, rev),
          evidence: (findingId, rev) => siteFindingViewHref(site.site_id, findingId, "evidence", rev),
          assumptions: (pin) => siteFinancialAssumptionsHref(site.site_id, pin),
          consequence: (findingId, revisionId, consequenceRevisionId) =>
            siteFinancialsHref(site.site_id, { findingId, revisionId, consequenceRevisionId }),
          findings: siteFindingsHref(site.site_id),
        };
        return (
          <main aria-labelledby={SITE_FINANCIALS_HEADING_ID}>
            <Breadcrumbs
              trail={[
                { label: "Sites", to: sitesPath },
                { label: site.display_name, to: siteDetailHref(site.site_id) },
                view === "overview"
                  ? { label: "Financials" }
                  : { label: "Financials", to: siteFinancialsHref(site.site_id) },
                ...(view === "assumptions" ? [{ label: "Assumptions" }] : []),
              ]}
            />
            {/* W1-F5a carry 1: the mock's Site page heading. */}
            <SitePageHeader
              siteName={site.display_name}
              siteId={site.site_id}
              mode={siteSourceModeLabel(site)}
              description={SITE_SCREEN_DESCRIPTIONS[view === "assumptions" ? "assumptions" : "financials"]}
              headingId={SITE_FINANCIALS_HEADING_ID}
            />
            <OperatorSiteTabs siteId={siteId} current="Financials" />
            <FinancialsSections
              siteId={site.site_id}
              view={view}
              scenarios={site.site_type === "MINIGRID" ? "live" : "unavailable"}
            />
            {view === "assumptions" ? (
              <SiteAssumptions siteId={site.site_id} client={financials} links={links} />
            ) : (
              <SiteFinancialsOverview siteId={site.site_id} client={financials} links={links} />
            )}
          </main>
        );
      }}
    </SiteScoped>
  );
}

/**
 * S6-01b: the canonical Site Action root, at
 * `/sites/{site}/actions/{action}[/execution | /history]` with an optional
 * `?event_id=` or `?recorded_at=` selection carried into every section link.
 * There is no Site Action index: an Action is reached from its Finding's
 * Recommendation or by its address. S6-02b adds the Plan, Evidence and
 * Verification sections with `?plan_revision_id=` / `?outcome_id=`, carried in
 * every section link beside `event_id` / `recorded_at`.
 */
export const SITE_ACTION_HEADING_ID = "site-action-heading";
const ACTION_SECTIONS_LABEL = "Action sections";

export function SiteActionFrame({
  detail,
  sitesPath,
  actions = DEFAULT_ACTIONS,
}: {
  detail: SiteDetailClient;
  sitesPath: string;
  actions?: ActionClient;
}) {
  const { siteId, actionId, actionView } = useParams<{ siteId: string; actionId: string; actionView?: string }>();
  const [params] = useSearchParams();
  const eventId = params.get("event_id");
  const recordedAt = params.get("recorded_at");
  const planRevisionId = params.get("plan_revision_id");
  const outcomeId = params.get("outcome_id");
  const [title, setTitle] = useState("Action");
  const onTitle = useCallback((next: string) => setTitle(next), []);
  const view: ActionView | null =
    actionView === undefined
      ? "overview"
      : actionView !== "overview" && (ACTION_VIEWS as readonly string[]).includes(actionView)
        ? (actionView as ActionView)
        : null;
  return (
    <SiteScoped siteId={siteId} detail={detail} title="Action" headingId={SITE_ACTION_HEADING_ID}>
      {(site) => {
        const id = actionId ?? "";
        const selector = { eventId, recordedAt, planRevisionId, outcomeId };
        const href = (target: ActionView, chosen: ActionSelector) => siteActionHref(site.site_id, id, target, chosen);
        return (
          <main aria-labelledby={SITE_ACTION_HEADING_ID}>
            <Breadcrumbs
              trail={[
                { label: "Sites", to: sitesPath },
                { label: site.display_name, to: siteDetailHref(site.site_id) },
                { label: "Findings", to: siteFindingsHref(site.site_id) },
                view === "overview" || view === null
                  ? { label: "Action" }
                  : { label: "Action", to: href("overview", selector) },
                ...(view === "overview" || view === null ? [] : [{ label: ACTION_VIEW_LABELS[view] }]),
              ]}
            />
            <PageHeader
              title={title}
              headingId={SITE_ACTION_HEADING_ID}
              subtitle={`${site.display_name} · an action raised from a finding`}
            />
            <OperatorSiteTabs siteId={siteId} current="Findings" />
            {view === null ? (
              <Panel heading="No such Action section" headingId="site-action-section-missing-heading">
                <p data-action-read="section-not-found">
                  An Action has no section with that name. <Link to={href("overview", selector)}>Open the Action</Link>
                </p>
              </Panel>
            ) : (
              <>
                <nav className="site-tabs site-subtabs" aria-label={ACTION_SECTIONS_LABEL}>
                  <ol className="site-tabs__list">
                    {ACTION_VIEWS.map((section) => (
                      <li className="site-tabs__item" key={section}>
                        <Link
                          className="site-tabs__link"
                          to={href(section, selector)}
                          data-action-section={section}
                          aria-current={section === view ? "page" : undefined}
                        >
                          {ACTION_VIEW_LABELS[section]}
                        </Link>
                      </li>
                    ))}
                  </ol>
                </nav>
                <SiteAction
                  siteId={site.site_id}
                  actionId={id}
                  view={view}
                  selector={selector}
                  client={actions}
                  onTitle={onTitle}
                  links={{
                    view: href,
                    finding: (findingId, rev) => siteFindingHref(site.site_id, findingId, rev),
                    recommendation: (findingId, rev) => siteFindingViewHref(site.site_id, findingId, "recommendation", rev),
                    change: (changeId) => siteFoundationChangeHref(site.site_id, changeId),
                    evidenceRecord: (evidenceId) => siteEvidenceAcceptedRecordHref(site.site_id, evidenceId),
                  }}
                />
              </>
            )}
          </main>
        );
      }}
    </SiteScoped>
  );
}

/**
 * S6-01b `changes:1#a`: one Foundation change by its change ID, a deep route
 * under Foundation with the Foundation tab current and no Foundation view row
 * (Changes is not a Foundation view). The bare `/foundation/changes` address
 * is an explicit unavailable state: S6-01 has no Site change index.
 */
export const SITE_CHANGE_HEADING_ID = "site-change-heading";

function changeLinks(siteId: string): SiteFoundationChangeLinks {
  return {
    action: (actionId, view, selector) => siteActionHref(siteId, actionId, view, selector),
    actionChild: (actionId, view, chosen) => siteActionHref(siteId, actionId, view, chosen),
    foundation: siteFoundationHref(siteId),
  };
}

export function SiteFoundationChangeFrame({
  detail,
  sitesPath,
  actions = DEFAULT_ACTIONS,
}: {
  detail: SiteDetailClient;
  sitesPath: string;
  actions?: ActionClient;
}) {
  const { siteId, changeId } = useParams<{ siteId: string; changeId: string }>();
  return (
    <SiteScoped siteId={siteId} detail={detail} title="Foundation change" headingId={SITE_CHANGE_HEADING_ID}>
      {(site) => (
        <main aria-labelledby={SITE_CHANGE_HEADING_ID}>
          <Breadcrumbs
            trail={[
              { label: "Sites", to: sitesPath },
              { label: site.display_name, to: siteDetailHref(site.site_id) },
              { label: "Foundation", to: siteFoundationHref(site.site_id) },
              { label: "Change" },
            ]}
          />
          {/* W1-F4: the mock's Site page heading; the change itself leads the status strip. */}
          <ChangesWorkPageHeader site={site} screen="changes" headingId={SITE_CHANGE_HEADING_ID} />
          <OperatorSiteTabs siteId={siteId} current="Foundation" />
          <FoundationSubtabs current="changes" hrefFor={(target) => siteFoundationViewHref(site.site_id, foundationViewSegment(target), null)} />
          <SiteFoundationChange
            siteId={site.site_id}
            changeId={changeId ?? ""}
            client={actions}
            links={changeLinks(site.site_id)}
          />
        </main>
      )}
    </SiteScoped>
  );
}

export function SiteFoundationChangesFrame({ detail, sitesPath }: { detail: SiteDetailClient; sitesPath: string }) {
  const { siteId } = useParams<{ siteId: string }>();
  return (
    <SiteScoped siteId={siteId} detail={detail} title="Foundation changes" headingId={SITE_CHANGE_HEADING_ID}>
      {(site) => (
        <main aria-labelledby={SITE_CHANGE_HEADING_ID}>
          <Breadcrumbs
            trail={[
              { label: "Sites", to: sitesPath },
              { label: site.display_name, to: siteDetailHref(site.site_id) },
              { label: "Foundation", to: siteFoundationHref(site.site_id) },
              { label: "Change & effect" },
            ]}
          />
          <ChangesWorkPageHeader site={site} screen="changes" headingId={SITE_CHANGE_HEADING_ID} />
          <OperatorSiteTabs siteId={siteId} current="Foundation" />
          <FoundationSubtabs current="changes" hrefFor={(target) => siteFoundationViewHref(site.site_id, foundationViewSegment(target), null)} />
          {/* W1-F5b: the changes screen's two v69 slots, with the no-selection gap inside each. */}
          <NoChangeSelected foundationHref={siteFoundationHref(site.site_id)} />
        </main>
      )}
    </SiteScoped>
  );
}

/**
 * S6-03 (`sitework:1#a`): Site > Work > Actions. The window lives in the URL
 * (`?from=&to=&limit=&cursor=`), so reload, back and a shared link reopen the
 * same window and page. Without `from` and `to` the page asks for a window and
 * reads nothing. W4-01 makes the mock's Incidents and Maintenance subtabs live
 * (`/work/incidents`, `/work/maintenance`); the row stays one row, Actions first.
 */
export const SITE_WORK_HEADING_ID = "site-work-heading";
export const SITE_WORK_SECTIONS_LABEL = "Work lists";
const DEFAULT_ACTION_INDEX = createActionIndexClient();
const DEFAULT_WORK_CLIENT = createWorkClient();

function workScopeFromQuery(params: URLSearchParams): ActionIndexScope | null {
  const from = params.get("from");
  const to = params.get("to");
  if (!from || !to) return null;
  const limit = Number(params.get("limit"));
  return {
    from,
    to,
    limit: params.get("limit") === null || !Number.isFinite(limit) ? null : limit,
    cursor: params.get("cursor"),
  };
}

export function SiteWorkFrame({
  detail,
  sitesPath,
  actionIndex = DEFAULT_ACTION_INDEX,
  workClient = DEFAULT_WORK_CLIENT,
}: {
  detail: SiteDetailClient;
  sitesPath: string;
  actionIndex?: ActionIndexClient;
  workClient?: WorkClient;
}) {
  const { siteId } = useParams<{ siteId: string }>();
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const scope = workScopeFromQuery(params);
  return (
    <SiteScoped siteId={siteId} detail={detail} title="Work" headingId={SITE_WORK_HEADING_ID}>
      {(site) => (
        <main aria-labelledby={SITE_WORK_HEADING_ID}>
          <Breadcrumbs
            trail={[
              { label: "Sites", to: sitesPath },
              { label: site.display_name, to: siteDetailHref(site.site_id) },
              { label: "Work" },
            ]}
          />
          <ChangesWorkPageHeader site={site} screen="sitework" headingId={SITE_WORK_HEADING_ID} />
          <OperatorSiteTabs siteId={siteId} current="Work" />
          <WorkSubrow
            siteId={site.site_id}
            current="actions"
            window={scope ? { from: scope.from, to: scope.to } : null}
            actionIndex={actionIndex}
            workClient={workClient}
          />
          <SiteWorkActions
            siteId={site.site_id}
            siteName={site.display_name}
            client={actionIndex}
            scope={scope}
            links={{
              scope: (next) => siteWorkHref(site.site_id, actionIndexQuery(next)),
              action: (actionId) => siteActionHref(site.site_id, actionId, "overview", { eventId: null, recordedAt: null }),
              history: (actionId, eventId) =>
                siteActionHref(site.site_id, actionId, "history", { eventId, recordedAt: null }),
              finding: (findingId, revisionId) => siteFindingHref(site.site_id, findingId, revisionId),
            }}
            onScope={(next) => navigate(siteWorkHref(site.site_id, actionIndexQuery(next)))}
          />
        </main>
      )}
    </SiteScoped>
  );
}

/** The Work subrow (v69 `tabs subtabs`): Actions, Incidents, Maintenance, all live, the current one marked. */
const WORK_SUBTABS: { key: "actions" | WorkKind; label: string; href: (siteId: string) => string }[] = [
  { key: "actions", label: "Actions", href: (siteId) => siteWorkHref(siteId) },
  { key: "incidents", label: "Incidents", href: (siteId) => siteWorkIncidentsHref(siteId) },
  { key: "maintenance", label: "Maintenance", href: (siteId) => siteWorkMaintenanceHref(siteId) },
];

type WorkCounts = { actions: number | null; incidents: number | null; maintenance: number | null };
const NO_COUNTS: WorkCounts = { actions: null, incidents: null, maintenance: null };
const fullCount = (value: number): number | null => (Number.isFinite(value) && value >= 0 ? value : null);

/**
 * The subtab counts (v69 `scope-count`): the full `total_count` of each list for
 * this Site and window, one row requested, no cursor or cutoff. Each read is
 * independent; anything but a successful count stays null (shown as a dash).
 * No window selected (the Actions choose-window state) reads nothing.
 */
function useWorkCounts(
  siteId: string,
  window: { from: string; to: string } | null,
  actionIndex: ActionIndexClient,
  workClient: WorkClient,
): WorkCounts {
  const [state, setState] = useState<{ key: string; counts: WorkCounts }>({ key: "", counts: NO_COUNTS });
  const from = window?.from ?? null;
  const to = window?.to ?? null;
  const key = from && to ? `${siteId}|${from}|${to}` : "";
  useEffect(() => {
    if (!from || !to) return;
    let live = true;
    const put = (part: Partial<WorkCounts>) => {
      if (live) setState((prev) => (prev.key === key ? { key, counts: { ...prev.counts, ...part } } : { key, counts: { ...NO_COUNTS, ...part } }));
    };
    actionIndex.getActionIndex(siteId, { from, to, limit: 1, cursor: null }).then(
      (r) => put({ actions: r.status === "loaded" ? fullCount(r.value.total_count) : null }),
      () => put({ actions: null }),
    );
    (["incidents", "maintenance"] as const).forEach((kind) => {
      workClient.getWorkIndex(siteId, kind, { from, to, limit: 1, knownAt: null, cursor: null }).then(
        (r) => put({ [kind]: r.status === "loaded" ? fullCount(r.value.total_count) : null }),
        () => put({ [kind]: null }),
      );
    });
    return () => {
      live = false;
    };
  }, [siteId, from, to, key, actionIndex, workClient]);
  // Counts belong to one Site and window: a stale key reads as unknown at once.
  return state.key === key && key !== "" ? state.counts : NO_COUNTS;
}

function WorkSubrow({
  siteId,
  current,
  window,
  actionIndex,
  workClient,
}: {
  siteId: string;
  current: "actions" | WorkKind;
  window: { from: string; to: string } | null;
  actionIndex: ActionIndexClient;
  workClient: WorkClient;
}) {
  const counts = useWorkCounts(siteId, window, actionIndex, workClient);
  return (
    <nav className="site-tabs site-subtabs" aria-label={SITE_WORK_SECTIONS_LABEL}>
      <ol className="site-tabs__list">
        {WORK_SUBTABS.map((tab) => (
          <li className="site-tabs__item" key={tab.key}>
            <Link
              className="site-tabs__link"
              to={tab.href(siteId)}
              aria-current={tab.key === current ? "page" : undefined}
            >
              {`${tab.label} (${counts[tab.key] ?? "—"})`}
            </Link>
          </li>
        ))}
      </ol>
    </nav>
  );
}

/**
 * W4-01 (`sitework-incidents`, `sitework-maintenance`): Site > Work >
 * Incidents | Maintenance. The window, fixed cutoff and server cursor live in
 * the URL (`?from=&to=&known_at=&cursor=`); the earlier pages' cursors ride in
 * history state so Previous survives a reload. Without a window the first read
 * is the seven complete UTC days ending today 00:00 UTC (B10).
 */
export const SITE_WORK_CASES_HEADING_ID = "site-work-cases-heading";

function workCasesScope(params: URLSearchParams): WorkScope {
  const from = params.get("from");
  const to = params.get("to");
  const window = from && to ? { from, to } : defaultWorkWindow();
  return { ...window, knownAt: params.get("known_at"), cursor: params.get("cursor") };
}

function workTrail(state: unknown): WorkTrail {
  const trail = (state as { workTrail?: unknown } | null)?.workTrail;
  return Array.isArray(trail) && trail.every((c) => c === null || typeof c === "string") ? (trail as WorkTrail) : [];
}

export function SiteWorkCasesFrame({
  detail,
  sitesPath,
  kind,
  workClient = DEFAULT_WORK_CLIENT,
  actionIndex = DEFAULT_ACTION_INDEX,
  miniDecisions = DEFAULT_MINI_DECISIONS,
}: {
  detail: SiteDetailClient;
  sitesPath: string;
  kind: WorkKind;
  workClient?: WorkClient;
  actionIndex?: ActionIndexClient;
  /** W4-03 unit 8: the decision-context overlay, read only on a mini-grid Site. */
  miniDecisions?: MiniDecisionsClient;
}) {
  const { siteId } = useParams<{ siteId: string }>();
  const [params] = useSearchParams();
  const location = useLocation();
  const navigate = useNavigate();
  const scope = workCasesScope(params);
  const trail = workTrail(location.state);
  const hrefFor = kind === "incidents" ? siteWorkIncidentsHref : siteWorkMaintenanceHref;
  const Body = kind === "incidents" ? SiteWorkIncidents : SiteWorkMaintenance;
  return (
    <SiteScoped siteId={siteId} detail={detail} title="Work" headingId={SITE_WORK_CASES_HEADING_ID}>
      {(site) => (
        <main aria-labelledby={SITE_WORK_CASES_HEADING_ID}>
          <Breadcrumbs
            trail={[
              { label: "Sites", to: sitesPath },
              { label: site.display_name, to: siteDetailHref(site.site_id) },
              { label: "Work" },
            ]}
          />
          <ChangesWorkPageHeader site={site} screen={`sitework-${kind}`} headingId={SITE_WORK_CASES_HEADING_ID} />
          <OperatorSiteTabs siteId={siteId} current="Work" />
          <WorkSubrow
            siteId={site.site_id}
            current={kind}
            window={{ from: scope.from, to: scope.to }}
            actionIndex={actionIndex}
            workClient={workClient}
          />
          <Body
            siteId={site.site_id}
            client={workClient}
            scope={scope}
            trail={trail}
            links={{ finding: (findingId, revisionId) => siteFindingHref(site.site_id, findingId, revisionId) }}
            decisions={site.site_type === "MINIGRID" ? miniDecisions : undefined}
            onScope={(next, nextTrail) =>
              navigate(hrefFor(site.site_id, workPageQuery(next)), { state: { workTrail: nextTrail } })
            }
          />
        </main>
      )}
    </SiteScoped>
  );
}
