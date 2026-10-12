import { useCallback, useState, type ReactNode } from "react";
import { useParams } from "react-router-dom";

import { FindingDetail, type FindingDetailTab } from "../sites/FindingDetail";
import { FindingsIndex, SiteFindings } from "../sites/FindingsIndexes";
import { createFindingClient, type FindingClient } from "../sites/findingClient";
import { SiteFinding } from "../sites/SiteFinding";
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
  FINDINGS_PATH,
  findingHref,
  siteDetailHref,
  siteEvidenceHref,
  siteEvidenceAssessmentHref,
  siteEvidenceRecordHref,
  siteFindingHref,
  siteFindingsHref,
  sitePerformanceHref,
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

export function SiteFindingsFrame({
  detail,
  analytics,
  sitesPath,
}: {
  detail: SiteDetailClient;
  analytics: SiteAnalyticsClient;
  sitesPath: string;
}) {
  const { siteId } = useParams<{ siteId: string }>();
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
          <SiteFindings
            siteId={site.site_id}
            client={analytics}
            profile={presentationProfileFor(site.site_type)}
            findingHref={(id, tab) => findingHref(site.site_id, id, tab)}
            dispatchHref={sitePerformanceHref(site.site_id, "dispatch")}
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

const FINDING_TABS: FindingTab[] = ["overview", "analysis", "evidence", "alternatives"];

export function FindingDetailFrame({
  detail,
  analytics,
  evidence,
}: {
  detail: SiteDetailClient;
  analytics: SiteAnalyticsClient;
  evidence: SiteEvidenceClient;
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
const DEFAULT_FINDINGS = createFindingClient();

/**
 * S4-01: one durable Finding of an imported Site, at
 * `/sites/{site}/findings/{finding}[?revision_id=]`. The trail returns to the
 * Site and its Findings tab; the body links to the Dispatch days it covers.
 */
export function SiteFindingFrame({
  detail,
  sitesPath,
  findings = DEFAULT_FINDINGS,
}: {
  detail: SiteDetailClient;
  sitesPath: string;
  findings?: FindingClient;
}) {
  const { siteId, findingId } = useParams<{ siteId: string; findingId: string }>();
  const [title, setTitle] = useState("Finding");
  const onTitle = useCallback((next: string) => setTitle(next), []);
  return (
    <SiteScoped siteId={siteId} detail={detail} title="Finding" headingId={SITE_FINDING_HEADING_ID}>
      {(site) => (
        <main aria-labelledby={SITE_FINDING_HEADING_ID}>
          <Breadcrumbs
            trail={[
              { label: "Sites", to: sitesPath },
              { label: site.site_id, to: siteDetailHref(site.site_id) },
              { label: "Findings", to: siteFindingsHref(site.site_id) },
              { label: "Finding" },
            ]}
          />
          <PageHeader
            title={title}
            headingId={SITE_FINDING_HEADING_ID}
            subtitle={`${site.display_name} · ${site.site_id} · generator support`}
          />
          <OperatorSiteTabs siteId={siteId} current="Findings" />
          <SiteFinding
            siteId={site.site_id}
            findingId={findingId ?? ""}
            client={findings}
            onTitle={onTitle}
            links={{
              finding: (id, revisionId) => siteFindingHref(site.site_id, id, revisionId),
              dispatch: (day, intervalRevisionId) =>
                `${sitePerformanceHref(site.site_id, "dispatch")}?day=${encodeURIComponent(day)}` +
                (intervalRevisionId ? `&revision=${encodeURIComponent(intervalRevisionId)}` : ""),
              evidence: siteEvidenceHref(site.site_id),
            }}
          />
        </main>
      )}
    </SiteScoped>
  );
}
