import { useParams, useSearchParams } from "react-router-dom";

import { SiteEvidence } from "../sites/SiteEvidence";
import { presentationProfileFor } from "../sites/presentationProfile";
import type { SiteAnalyticsClient } from "../sites/siteAnalyticsClient";
import type { SiteDetailClient } from "../sites/siteDirectoryClient";
import type { SiteEvidenceClient } from "../sites/siteEvidenceClient";
import { useSiteRecord } from "../sites/useSiteRecord";
import { localView } from "../sites/findingPresentation";
import { deriveSiteView } from "../sites/siteViewModel";
import { Breadcrumbs, PageHeader, Panel, SITE_SCREEN_DESCRIPTIONS, SitePageHeader } from "../ui";
import { OperatorSiteTabs } from "./operatorSiteTabs";
import { siteDetailHref, sitePerformanceHref } from "./operatorSiteRoutes";

/** The heading id the Evidence landmark is labelled by. */
export const SITE_EVIDENCE_HEADING_ID = "site-evidence-heading";

/**
 * The operator route for one site's Evidence, addressed by `site_id`.
 *
 * It composes the same Site header and tab row the Foundation frame does, with
 * `Evidence` current, and a site that is not configured gets the same
 * statement of absence rather than an Evidence page for a site that does not
 * exist. Like every operator route it is never gated.
 *
 * The body is `SiteEvidence`: the T028 capability table (part B, scored by
 * the backend) above T027 part A - source health, per-signal coverage, the
 * mapping and configuration basis, rejections and the record inspector
 * drill-down, all read from accepted evidence only.
 */
export interface SiteEvidenceFrameProps {
  detail: SiteDetailClient;
  evidence: SiteEvidenceClient;
  analytics?: SiteAnalyticsClient;
  sitesPath: string;
}

export function SiteEvidenceFrame({
  detail,
  evidence,
  analytics,
  sitesPath,
}: SiteEvidenceFrameProps) {
  const { siteId } = useParams<{ siteId: string }>();
  const result = useSiteRecord(siteId, detail);
  const [params] = useSearchParams();

  if (result === null) {
    return (
      <main aria-labelledby={SITE_EVIDENCE_HEADING_ID}>
        <PageHeader title="Evidence" headingId={SITE_EVIDENCE_HEADING_ID} />
        <p>Loading the configured site.</p>
      </main>
    );
  }

  if (result.status === "not_found") {
    return (
      <main aria-labelledby={SITE_EVIDENCE_HEADING_ID}>
        <PageHeader
          title="Site not found"
          headingId={SITE_EVIDENCE_HEADING_ID}
        />
        <Panel
          heading="No such site"
          headingId="site-evidence-not-found-heading"
        >
          <p>
            No site with that site ID is configured, so there is no evidence to
            read. This is a statement that the site does not exist, not a site
            with no evidence.
          </p>
        </Panel>
      </main>
    );
  }

  if (result.status === "unavailable") {
    return (
      <main aria-labelledby={SITE_EVIDENCE_HEADING_ID}>
        <PageHeader title="Evidence" headingId={SITE_EVIDENCE_HEADING_ID} />
        <Panel
          heading="Site unavailable"
          headingId="site-evidence-unavailable-heading"
        >
          <p>
            The site store could not be read, so this site&apos;s evidence
            cannot be shown. This is a statement about the store: nothing is
            known about whether the site is configured.
          </p>
        </Panel>
      </main>
    );
  }

  const site = result.site;

  return (
    <main aria-labelledby={SITE_EVIDENCE_HEADING_ID}>
      <Breadcrumbs
        trail={[
          { label: "Sites", to: sitesPath },
          { label: site.display_name, to: siteDetailHref(site.site_id) },
          { label: "Evidence" },
        ]}
      />
      {/* W1-F2: the v69 Site page heading - site name, provenance badge, the screen's description. */}
      <SitePageHeader
        siteName={site.display_name}
        siteId={site.site_id}
        mode={deriveSiteView(site).sourceMode}
        description={SITE_SCREEN_DESCRIPTIONS[localView(params) === "analysis" ? "evidence-analysis" : "evidence"]}
        headingId={SITE_EVIDENCE_HEADING_ID}
      />
      <OperatorSiteTabs siteId={siteId} current="Evidence" />
      <SiteEvidence
        siteId={site.site_id}
        client={evidence}
        analytics={analytics}
        profile={presentationProfileFor(site.site_type)}
        assessmentHref={(day, revisionId) =>
          `${sitePerformanceHref(site.site_id, "dispatch")}?day=${encodeURIComponent(day)}&revision=${encodeURIComponent(revisionId)}`
        }
      />
    </main>
  );
}
