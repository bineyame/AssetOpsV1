import { UnavailableTab } from "../ui/UnavailableEntry";
import { FoundationSubtabs, foundationViewSegment } from "../sites/FoundationSubtabs";
import { useCallback, useState, type ReactNode } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";

import { FindingDetail, type FindingDetailTab } from "../sites/FindingDetail";
import { FindingsIndex, SiteFindings } from "../sites/FindingsIndexes";
import { createActionClient, type ActionClient } from "../sites/actionClient";
import {
  actionIndexQuery,
  createActionIndexClient,
  type ActionIndexClient,
  type ActionIndexScope,
} from "../sites/actionIndexClient";
import { SiteWorkActions } from "../sites/SiteWorkActions";
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
import { SiteFinding } from "../sites/SiteFinding";
import { FindingSections, SiteFindingEvidence, type FindingSectionLink } from "../sites/SiteFindingEvidence";
import { SiteFindingHistory } from "../sites/SiteFindingHistory";
import { SitePerformance } from "../sites/SitePerformance";
import { ColdFindingFrame, ColdPerformanceFrame, type ColdLinks } from "../sites/ColdAssessmentViews";
import { coldWindowFromParams, coldWindowSearch, type ColdAssessmentClient, type ColdWindowQuery } from "../sites/coldAssessmentClient";
import type { ColdSiteClient } from "../sites/coldSiteClient";
import { EvFindingFrame, EvSessionsFrame, evFindingHref } from "../sites/EvAssessmentViews";
import type { EvAssessmentClient } from "../sites/evAssessmentClient";
import { coldSiteScreen } from "./coldSiteRoutes";
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
  siteFindingsHref,
  siteFinancialAssumptionsHref,
  siteFinancialsHref,
  siteFoundationChangeHref,
  siteFoundationHref,
  siteFoundationViewHref,
  sitePerformanceHref,
  siteWorkHref,
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

const COLD_PERFORMANCE_VIEWS: Record<string, "temperature" | "backup"> = { temperature: "temperature", backup: "backup" };

export function SitePerformanceFrame({
  detail,
  analytics,
  sitesPath,
  coldAssessment,
  evAssessment,
}: {
  detail: SiteDetailClient;
  analytics: SiteAnalyticsClient;
  sitesPath: string;
  /** W2-03: the selected cold assessment reads; a COLDCHAIN Site renders `temperature` / `coldbackup` from them. */
  coldAssessment?: ColdAssessmentClient;
  /** W2-06: the selected EV session reads; an EV_CHARGING Site renders `sessions` from them. */
  evAssessment?: EvAssessmentClient;
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
            />
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
            profile={presentationProfileFor(site.site_type)}
            capabilityId={capabilityId}
            subtabHref={(id) => sitePerformanceHref(site.site_id, id)}
            findingHref={(id) => findingHref(site.site_id, id)}
            findings={DEFAULT_FINDINGS}
            siteFindingHref={(id) => siteFindingHref(site.site_id, id)}
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

export const FINDINGS_HEADING_ID = "findings-heading";

/** The Findings rail root: the global index. */
export function FindingsFrame({ analytics }: { analytics: SiteAnalyticsClient }) {
  return (
    <main aria-labelledby={FINDINGS_HEADING_ID}>
      <PageHeader
        title="Findings"
        headingId={FINDINGS_HEADING_ID}
        subtitle="Every configured site"
      />
      <FindingsIndex
        client={analytics}
        findingHref={(siteId, assessmentId, tab) => findingHref(siteId, assessmentId, tab)}
      />
    </main>
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
 */
const FINDING_SECTION_LABELS: Record<FindingChildView, string> = {
  evidence: "Evidence",
  history: "History",
  recommendation: "Recommendation",
};

export function SiteFindingFrame({
  detail,
  sitesPath,
  findings = DEFAULT_FINDINGS,
  actions = DEFAULT_ACTIONS,
  coldAssessment,
  evAssessment,
}: {
  detail: SiteDetailClient;
  sitesPath: string;
  findings?: FindingClient;
  actions?: ActionClient;
  /** W2-03: a COLDCHAIN Site's Finding renders `cold-finding` or `cold-finding-excursion` by its kind. */
  coldAssessment?: ColdAssessmentClient;
  /** W2-06: an EV_CHARGING Site's Finding renders `ev-finding` from the selected EV reads. */
  evAssessment?: EvAssessmentClient;
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
        if (site.site_type === "EV_CHARGING" && evAssessment !== undefined && findingView === undefined) {
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
        if (site.site_type === "COLDCHAIN" && coldAssessment !== undefined && findingView === undefined) {
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
        const dispatch = (day: string, intervalRevisionId?: string | null) =>
          `${sitePerformanceHref(site.site_id, "dispatch")}?day=${encodeURIComponent(day)}` +
          (intervalRevisionId ? `&revision=${encodeURIComponent(intervalRevisionId)}` : "");
        const child = (c: FindingChildView) => ({
          id: c,
          label: FINDING_SECTION_LABELS[c],
          href: siteFindingViewHref(site.site_id, id, c, revisionId),
        });
        // W1-F5b (D-2026-10-17-f5-subtabs-and-contact): the mock's order, with Alternatives unbuilt in its place.
        const sections: FindingSectionLink[] = [
          { id: "finding", label: "Finding", href: siteFindingHref(site.site_id, id, revisionId) },
          child("evidence"),
          { id: "alternatives", label: "Alternatives", unavailable: true },
          child("recommendation"),
          child("history"),
        ];
        return (
          <main aria-labelledby={SITE_FINDING_HEADING_ID}>
            <Breadcrumbs
              trail={[
                { label: "Sites", to: sitesPath },
                { label: site.display_name, to: siteDetailHref(site.site_id) },
                { label: "Findings", to: siteFindingsHref(site.site_id) },
                view === "finding" || view === null
                  ? { label: "Finding" }
                  : { label: "Finding", to: siteFindingHref(site.site_id, id, revisionId) },
                ...(view === "finding" || view === null ? [] : [{ label: FINDING_SECTION_LABELS[view] }]),
              ]}
            />
            <PageHeader
              title={title}
              headingId={SITE_FINDING_HEADING_ID}
              subtitle={`${site.display_name} · generator support finding`}
            />
            <OperatorSiteTabs siteId={siteId} current="Findings" />
            {view === null ? (
              <Panel heading="No such Finding section" headingId="site-finding-section-missing-heading">
                <p data-finding-read="not_found">
                  A Finding has no section with that name. <Link to={siteFindingHref(site.site_id, id, revisionId)}>Open the Finding</Link>
                </p>
              </Panel>
            ) : (
              <>
                {/* W1-F3: the money link sits on the section-tab line; W1-F4: on Recommendation it is a qualified line inside "Proposed intervention" instead. */}
                <FindingSections
                  sections={sections}
                  current={view}
                  aside={
                    view === "recommendation" ? undefined : (
                      <span className="finding-financials-link" data-finding-financials-link>
                        <Link to={siteFinancialsHref(site.site_id, { findingId: id, revisionId })}>
                          What this finding means in money
                        </Link>
                      </span>
                    )
                  }
                />
                {view === "evidence" ? (
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
      }}
    </SiteScoped>
  );
}

export const SITE_FINANCIALS_HEADING_ID = "site-financials-heading";
const DEFAULT_FINANCIALS = createFinancialsClient();
const FINANCIALS_SECTIONS_LABEL = "Financials sections";

/**
 * The Financials subtab row (Overview, Assumptions, and the mock's Scenarios as "Not available yet" text). W2-04:
 * a cold Site's Financials screens reuse it with the selected window (`search`) carried in both links.
 */
export function FinancialsSections({ siteId, view, search = "" }: { siteId: string; view: "overview" | "assumptions"; search?: string }) {
  return (
    <nav className="site-tabs site-subtabs" aria-label={FINANCIALS_SECTIONS_LABEL}>
      <ol className="site-tabs__list">
        {(
          [
            ["overview", "Overview", `${siteFinancialsHref(siteId)}${search}`],
            ["assumptions", "Assumptions", `${siteFinancialAssumptionsHref(siteId)}${search}`],
          ] as const
        ).map(([id, label, href]) => (
          <li className="site-tabs__item" key={id}>
            <Link className="site-tabs__link" to={href} data-financials-section={id} aria-current={id === view ? "page" : undefined}>
              {label}
            </Link>
          </li>
        ))}
        <UnavailableTab label="Scenarios" />
      </ol>
    </nav>
  );
}

/**
 * S4-02a: Site > Financials (Overview with the Finding bridge) and Financials > Assumptions. W1-F5b
 * (D-2026-10-17-f5-subtabs-and-contact): the mock's Scenarios subtab is shown in its place as "Not available yet"
 * text, never a link or a route (G-05 is still unbuilt).
 */
export function SiteFinancialsFrame({
  detail,
  sitesPath,
  view,
  financials = DEFAULT_FINANCIALS,
  coldSite,
  coldAssessment,
}: {
  detail: SiteDetailClient;
  sitesPath: string;
  view: "overview" | "assumptions";
  financials?: FinancialsClient;
  /** W2-04: a COLDCHAIN Site renders `cold-financials` / `cold-assumptions` from these reads (read-only). */
  coldSite?: ColdSiteClient;
  coldAssessment?: ColdAssessmentClient;
}) {
  const { siteId } = useParams<{ siteId: string }>();
  const [params] = useSearchParams();
  const title = view === "assumptions" ? "Financial assumptions" : "Financials";
  return (
    <SiteScoped siteId={siteId} detail={detail} title={title} headingId={SITE_FINANCIALS_HEADING_ID}>
      {(site) => {
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
            <FinancialsSections siteId={site.site_id} view={view} />
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
 * reads nothing. Actions is Work's only list in this build; W1-F5b shows the mock's
 * Incidents and Maintenance as "Not available yet" text in the row, never links or routes.
 */
export const SITE_WORK_HEADING_ID = "site-work-heading";
export const SITE_WORK_SECTIONS_LABEL = "Work lists";
const DEFAULT_ACTION_INDEX = createActionIndexClient();

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
}: {
  detail: SiteDetailClient;
  sitesPath: string;
  actionIndex?: ActionIndexClient;
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
          <nav className="site-tabs site-subtabs" aria-label={SITE_WORK_SECTIONS_LABEL}>
            <ol className="site-tabs__list">
              <li className="site-tabs__item">
                <Link className="site-tabs__link" to={siteWorkHref(site.site_id)} aria-current="page">
                  Actions
                </Link>
              </li>
              <UnavailableTab label="Incidents" />
              <UnavailableTab label="Maintenance" />
            </ol>
          </nav>
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
