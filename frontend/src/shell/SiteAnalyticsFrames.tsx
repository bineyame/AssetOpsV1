import { useCallback, useState, type ReactNode } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";

import { FindingDetail, type FindingDetailTab } from "../sites/FindingDetail";
import { FindingsIndex, SiteFindings } from "../sites/FindingsIndexes";
import {
  createFindingIndexClient,
  FINDING_INDEX_DOMAIN,
  type FindingIndexClient,
  type FindingIndexScope,
} from "../sites/findingIndexClient";
import { SiteFindingIndex } from "../sites/SiteFindingIndex";
import { createFindingClient, type FindingClient } from "../sites/findingClient";
import { createFinancialsClient, type FinancialsClient } from "../sites/financialsClient";
import { SiteAssumptions, SiteFinancialsOverview, type FinancialsLinks } from "../sites/SiteFinancials";
import { SiteFinding } from "../sites/SiteFinding";
import { FindingSections, SiteFindingEvidence } from "../sites/SiteFindingEvidence";
import { SiteFindingHistory } from "../sites/SiteFindingHistory";
import { SitePerformance } from "../sites/SitePerformance";
import { presentationProfileFor } from "../sites/presentationProfile";
import type { SiteAnalyticsClient } from "../sites/siteAnalyticsClient";
import type { SiteDetailClient } from "../sites/siteDirectoryClient";
import type { SiteEvidenceClient } from "../sites/siteEvidenceClient";
import type { SiteDetailReadModel } from "../sites/siteReadModel";
import { useSiteRecord } from "../sites/useSiteRecord";
import { Breadcrumbs, PageHeader, Panel } from "../ui";
import { OperatorSiteTabs } from "./operatorSiteTabs";
import {
  FINDING_CHILD_VIEWS,
  FINDINGS_PATH,
  findingHref,
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
  sitePerformanceHref,
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
function SiteScoped({
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

export function SitePerformanceFrame({
  detail,
  analytics,
  sitesPath,
}: {
  detail: SiteDetailClient;
  analytics: SiteAnalyticsClient;
  sitesPath: string;
}) {
  const { siteId, capabilityId } = useParams<{ siteId: string; capabilityId?: string }>();
  return (
    <SiteScoped
      siteId={siteId}
      detail={detail}
      title="Performance"
      headingId={SITE_PERFORMANCE_HEADING_ID}
    >
      {(site) => (
        <main aria-labelledby={SITE_PERFORMANCE_HEADING_ID}>
          <Breadcrumbs
            trail={[
              { label: "Sites", to: sitesPath },
              { label: site.site_id, to: siteDetailHref(site.site_id) },
              { label: "Performance" },
            ]}
          />
          <PageHeader
            title="Performance"
            headingId={SITE_PERFORMANCE_HEADING_ID}
            subtitle={`${site.display_name} · ${site.site_id}`}
          />
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
      )}
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
              { label: site.site_id, to: siteDetailHref(site.site_id) },
              { label: "Findings" },
            ]}
          />
          <PageHeader
            title="Findings"
            headingId={SITE_FINDINGS_HEADING_ID}
            subtitle={`${site.display_name} · ${site.site_id}`}
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
              { label: site.site_id, to: siteFindingsHref(site.site_id) },
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
const FINDING_SECTION_LABELS: Record<FindingChildView, string> = { evidence: "Evidence", history: "History" };

export function SiteFindingFrame({
  detail,
  sitesPath,
  findings = DEFAULT_FINDINGS,
}: {
  detail: SiteDetailClient;
  sitesPath: string;
  findings?: FindingClient;
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
        const dispatch = (day: string, intervalRevisionId?: string | null) =>
          `${sitePerformanceHref(site.site_id, "dispatch")}?day=${encodeURIComponent(day)}` +
          (intervalRevisionId ? `&revision=${encodeURIComponent(intervalRevisionId)}` : "");
        const sections = [
          { id: "finding", label: "Finding", href: siteFindingHref(site.site_id, id, revisionId) },
          ...FINDING_CHILD_VIEWS.map((child) => ({
            id: child,
            label: FINDING_SECTION_LABELS[child],
            href: siteFindingViewHref(site.site_id, id, child, revisionId),
          })),
        ];
        return (
          <main aria-labelledby={SITE_FINDING_HEADING_ID}>
            <Breadcrumbs
              trail={[
                { label: "Sites", to: sitesPath },
                { label: site.site_id, to: siteDetailHref(site.site_id) },
                { label: "Findings", to: siteFindingsHref(site.site_id) },
                view === "finding" || view === null
                  ? { label: "Finding" }
                  : { label: "Finding", to: siteFindingHref(site.site_id, id, revisionId) },
                ...(view === "finding" || view === null ? [] : [{ label: FINDING_SECTION_LABELS[view] }]),
              ]}
            />
            <PageHeader
              title={view === "evidence" ? "Finding evidence" : view === "history" ? "Finding history" : title}
              headingId={SITE_FINDING_HEADING_ID}
              subtitle={`${site.display_name} · ${site.site_id} · generator support`}
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
                <FindingSections sections={sections} current={view} />
                <p className="finding-financials-link" data-finding-financials-link>
                  <Link to={siteFinancialsHref(site.site_id, { findingId: id, revisionId })}>
                    What this finding means in money
                  </Link>
                </p>
                {view === "evidence" ? (
                  <SiteFindingEvidence
                    siteId={site.site_id}
                    findingId={id}
                    client={findings}
                    links={{
                      evidence: (rev) => siteFindingViewHref(site.site_id, id, "evidence", rev),
                      finding: (other, rev) => siteFindingHref(site.site_id, other, rev),
                      dispatch,
                      record: (evidenceId) => siteEvidenceAcceptedRecordHref(site.site_id, evidenceId),
                      history: (rev) => siteFindingViewHref(site.site_id, id, "history", rev),
                    }}
                  />
                ) : view === "history" ? (
                  <SiteFindingHistory
                    siteId={site.site_id}
                    findingId={id}
                    client={findings}
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
                      history: (rev) => siteFindingViewHref(site.site_id, id, "history", rev),
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
 * S4-02a: Site > Financials (Overview with the Finding bridge) and Financials > Assumptions. The mock's
 * Scenarios subtab is omitted for G-05, not rendered as an empty tab.
 */
export function SiteFinancialsFrame({
  detail,
  sitesPath,
  view,
  financials = DEFAULT_FINANCIALS,
}: {
  detail: SiteDetailClient;
  sitesPath: string;
  view: "overview" | "assumptions";
  financials?: FinancialsClient;
}) {
  const { siteId } = useParams<{ siteId: string }>();
  const title = view === "assumptions" ? "Financial assumptions" : "Financials";
  return (
    <SiteScoped siteId={siteId} detail={detail} title={title} headingId={SITE_FINANCIALS_HEADING_ID}>
      {(site) => {
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
                { label: site.site_id, to: siteDetailHref(site.site_id) },
                view === "overview"
                  ? { label: "Financials" }
                  : { label: "Financials", to: siteFinancialsHref(site.site_id) },
                ...(view === "assumptions" ? [{ label: "Assumptions" }] : []),
              ]}
            />
            <PageHeader
              title={title}
              headingId={SITE_FINANCIALS_HEADING_ID}
              subtitle={`${site.display_name} · ${site.site_id} · diesel price per litre`}
            />
            <OperatorSiteTabs siteId={siteId} current="Financials" />
            <nav className="site-tabs site-subtabs" aria-label={FINANCIALS_SECTIONS_LABEL}>
              <ol className="site-tabs__list">
                {(
                  [
                    ["overview", "Overview", siteFinancialsHref(site.site_id)],
                    ["assumptions", "Assumptions", siteFinancialAssumptionsHref(site.site_id)],
                  ] as const
                ).map(([id, label, href]) => (
                  <li className="site-tabs__item" key={id}>
                    <Link
                      className="site-tabs__link"
                      to={href}
                      data-financials-section={id}
                      aria-current={id === view ? "page" : undefined}
                    >
                      {label}
                    </Link>
                  </li>
                ))}
              </ol>
            </nav>
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
