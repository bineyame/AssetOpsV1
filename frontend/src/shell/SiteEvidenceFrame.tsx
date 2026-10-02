import { useParams } from "react-router-dom";

import type { SiteDetailClient } from "../sites/siteDirectoryClient";
import { useSiteRecord } from "../sites/useSiteRecord";
import { Breadcrumbs, PageHeader, Panel } from "../ui";
import { OperatorSiteTabs } from "./operatorSiteTabs";
import { siteDetailHref } from "./operatorSiteRoutes";

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
 * The body is a placeholder: sub-phase 1c of T027 replaces it with the real
 * Evidence body (source health, per-signal coverage, record drill-down). Until
 * then it says only what is true, that nothing accepted is shown yet.
 */
export interface SiteEvidenceFrameProps {
  detail: SiteDetailClient;
  sitesPath: string;
}

export function SiteEvidenceFrame({ detail, sitesPath }: SiteEvidenceFrameProps) {
  const { siteId } = useParams<{ siteId: string }>();
  const result = useSiteRecord(siteId, detail);

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
          { label: site.site_id, to: siteDetailHref(site.site_id) },
          { label: "Evidence" },
        ]}
      />
      <PageHeader
        title="Evidence"
        headingId={SITE_EVIDENCE_HEADING_ID}
        subtitle={`${site.display_name} · ${site.site_id}`}
      />
      <OperatorSiteTabs siteId={siteId} current="Evidence" />
      <Panel heading="Accepted evidence" headingId="site-evidence-body-heading">
        <p>
          Accepted evidence for this Site appears here once a source batch has
          been ingested.
        </p>
      </Panel>
    </main>
  );
}
