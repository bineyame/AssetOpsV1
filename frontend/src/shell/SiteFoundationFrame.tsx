import { useCallback, useMemo, useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";

import {
  SITE_CONFIGURATION_HEADING_ID,
  SiteConfiguration,
} from "../sites/SiteConfiguration";
import { FoundationRevisionPanel } from "../sites/FoundationRevisionPanel";
import type { SiteDetailClient } from "../sites/siteDirectoryClient";
import type { SiteFoundationClient } from "../sites/siteFoundationClient";
import type { SiteTemplateLineageClient } from "../sites/siteTemplateLineage";
import { SITE_FOUNDATION_LOADING, useSiteFoundation } from "../sites/useSiteFoundation";
import { PageHeader, Panel } from "../ui";
import { OperatorSiteTabs } from "./operatorSiteTabs";
import { siteDetailHref } from "./operatorSiteRoutes";

export interface SiteFoundationFrameProps {
  detail: SiteDetailClient;
  /** S1-01: the persisted Foundation read and its one change. */
  foundation: SiteFoundationClient;
  sitesPath: string;
  templateLineage?: SiteTemplateLineageClient;
}

/**
 * Foundation for one Site (S1-01).
 *
 * A Site imported into the persisted store renders the stored version
 * effective at the `at` instant carried in the URL (absent = in effect now),
 * so reload and share keep the selection, with the version panel above the
 * shared Foundation sections. A Site still read from its original document
 * renders as before, labelled as such. A period with no stored version is
 * stated, never filled with the current configuration.
 */
export function SiteFoundationFrame({
  detail,
  foundation,
  sitesPath,
  templateLineage,
}: SiteFoundationFrameProps) {
  const { siteId } = useParams<{ siteId: string }>();
  const [params, setParams] = useSearchParams();
  const at = params.get("at");
  const [refresh, setRefresh] = useState(0);
  const state = useSiteFoundation(siteId, at, foundation, refresh);

  const selectAt = useCallback(
    (next: string | null) => {
      const updated = new URLSearchParams(params);
      if (next === null) updated.delete("at");
      else updated.set("at", next);
      setParams(updated);
    },
    [params, setParams],
  );

  const loaded = state.foundation?.status === "loaded" ? state.foundation.value : null;
  const storedDetail = useMemo<SiteDetailClient | null>(
    () =>
      loaded === null
        ? null
        : { getSite: () => Promise.resolve({ status: "loaded", site: loaded.detail }) },
    [loaded],
  );

  const tabs = <OperatorSiteTabs siteId={siteId} current="Foundation" />;
  const parentTrail = (canonicalSiteId: string) => [
    { label: "Sites", to: sitesPath },
    { label: canonicalSiteId, to: siteDetailHref(canonicalSiteId) },
  ];

  if (state.foundation === null) {
    return (
      <main aria-labelledby={SITE_CONFIGURATION_HEADING_ID}>
        <PageHeader title="Foundation" headingId={SITE_CONFIGURATION_HEADING_ID} />
        <p>{SITE_FOUNDATION_LOADING}</p>
      </main>
    );
  }

  if (loaded !== null && storedDetail !== null && siteId !== undefined) {
    const versions = state.versions?.status === "loaded" ? state.versions.value : null;
    return (
      <main aria-labelledby={SITE_CONFIGURATION_HEADING_ID}>
        <SiteConfiguration
          siteId={siteId}
          detail={storedDetail}
          templateLineage={templateLineage}
          tabs={tabs}
          parentTrail={parentTrail}
          revision={
            <FoundationRevisionPanel
              foundation={loaded}
              versions={versions}
              selectedAt={at}
              onSelectAt={selectAt}
              onPublish={async (value, validFrom) => {
                const outcome = await foundation.publishReserve(siteId, {
                  asset_code: loaded.controls.battery_reserve.asset_code ?? "battery",
                  value,
                  valid_from: validFrom,
                });
                if (outcome.status === "published") setRefresh((count) => count + 1);
                return outcome;
              }}
            />
          }
        />
      </main>
    );
  }

  if (at !== null && (state.foundation.status === "not_found" || state.foundation.status === "invalid")) {
    return (
      <main aria-labelledby={SITE_CONFIGURATION_HEADING_ID}>
        <PageHeader title="Foundation" headingId={SITE_CONFIGURATION_HEADING_ID} subtitle={siteId} />
        {tabs}
        <Panel heading="No stored version for this period" headingId="foundation-period-empty-heading">
          <p>{state.foundation.message}</p>
          <p>The configuration in effect now is not shown in its place.</p>
          <button type="button" onClick={() => selectAt(null)}>
            Show the version in effect now
          </button>
        </Panel>
      </main>
    );
  }

  const notice =
    state.foundation.status === "migration_required" ? (
      <Panel heading="Original configuration record" headingId="foundation-legacy-heading">
        <p>
          This site is read from its original configuration document. It has no stored
          Foundation versions until it is imported, so no period can be chosen and nothing can
          be changed here.
        </p>
      </Panel>
    ) : state.foundation.status === "unavailable" ? (
      <Panel heading="Stored versions unavailable" headingId="foundation-store-unavailable-heading">
        <p>
          Stored Foundation versions could not be read
          {state.foundation.message === null ? "." : `: ${state.foundation.message}`} The
          configuration below is the site&apos;s record as served now; no period can be chosen.
        </p>
      </Panel>
    ) : null;

  return (
    <main aria-labelledby={SITE_CONFIGURATION_HEADING_ID}>
      <SiteConfiguration
        siteId={siteId}
        detail={detail}
        templateLineage={templateLineage}
        tabs={tabs}
        revision={notice}
        parentTrail={parentTrail}
      />
    </main>
  );
}
