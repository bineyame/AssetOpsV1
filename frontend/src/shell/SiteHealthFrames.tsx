/**
 * S7-01b route frames: Site Health (`/sites/{site}/health[?gateway=]`), the
 * Site battery entry (`/sites/{site}/assets`) and one configured battery
 * (`/sites/{site}/assets/{asset}`). Each is Site-scoped (unknown Site is "not
 * found", never an empty healthy page) and highlights the Health tab.
 */
import { useCallback, useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";

import { coldWindowFromParams } from "../sites/coldAssessmentClient";
import { createColdDepthClient, type ColdDepthClient } from "../sites/ColdDepthClient";
import { ColdHealthDepth } from "../sites/ColdHealthDepth";
import { createHealthClient, type HealthClient } from "../sites/healthClient";
import { SiteBattery, SiteBatteryEntry, type BatteryHeader } from "../sites/SiteBattery";
import { HealthLinksContext, SiteHealth, SiteHealthSources, type HealthLinks } from "../sites/SiteHealth";
import type { SiteDetailClient } from "../sites/siteDirectoryClient";
import { siteSourceModeLabel } from "../sites/siteViewModel";
import { Breadcrumbs, PageHeader, SITE_SCREEN_DESCRIPTIONS, SitePageHeader } from "../ui";
import { coldSiteRoutes } from "./coldSiteRoutes";
import { siteAssetHref, siteAssetsHref, siteDetailHref, siteHealthHref } from "./operatorSiteRoutes";
import { OperatorSiteTabs } from "./operatorSiteTabs";
import { SiteScoped } from "./SiteAnalyticsFrames";

const DEFAULT_HEALTH = createHealthClient();
const DEFAULT_COLD_DEPTH = createColdDepthClient();
const LINKS: HealthLinks = { health: siteHealthHref, assets: siteAssetsHref, asset: siteAssetHref };
export const SITE_HEALTH_HEADING_ID = "site-health-heading";
export const SITE_BATTERY_HEADING_ID = "site-battery-heading";

export function SiteHealthFrame({
  detail,
  sitesPath,
  health = DEFAULT_HEALTH,
  coldDepth = DEFAULT_COLD_DEPTH,
}: {
  detail: SiteDetailClient;
  sitesPath: string;
  health?: HealthClient;
  /** W5-01a C3: a COLDCHAIN Site renders `cold-health` from the selected `/cold/health` read. */
  coldDepth?: ColdDepthClient;
}) {
  const { siteId } = useParams<{ siteId: string }>();
  const [params] = useSearchParams();
  const gateway = params.get("gateway");
  return (
    <SiteScoped siteId={siteId} detail={detail} title="Health" headingId={SITE_HEALTH_HEADING_ID}>
      {(site) => (
        <main aria-labelledby={SITE_HEALTH_HEADING_ID}>
          <Breadcrumbs
            trail={[
              { label: "Sites", to: sitesPath },
              { label: site.display_name, to: siteDetailHref(site.site_id) },
              gateway === null ? { label: "Health" } : { label: "Health", to: siteHealthHref(site.site_id) },
              ...(gateway === null ? [] : [{ label: "Gateway" }]),
            ]}
          />
          {/* W1-F5a: the mock's Site page heading (carry 1). */}
          <SitePageHeader
            siteName={site.display_name}
            siteId={site.site_id}
            mode={siteSourceModeLabel(site)}
            description={SITE_SCREEN_DESCRIPTIONS.health}
            headingId={SITE_HEALTH_HEADING_ID}
          />
          <OperatorSiteTabs siteId={site.site_id} current="Health" />
          <HealthLinksContext.Provider value={LINKS}>
            {site.site_type === "COLDCHAIN" ? (
              <>
                {/* W5-01a C3: condition cards, Condition and evidence, the condition notice, then (Q-C3-1, labelled
                    mock deviation) the S7 Data sources panel alone; no S7 battery strip, panel or blue notice. */}
                <ColdHealthDepth
                  siteCode={site.site_id}
                  window={coldWindowFromParams(params)}
                  client={coldDepth}
                  routes={coldSiteRoutes(site.site_id)}
                />
                <SiteHealthSources siteId={site.site_id} client={health} selectedGateway={gateway} />
              </>
            ) : (
              <SiteHealth siteId={site.site_id} siteName={site.display_name} client={health} selectedGateway={gateway} />
            )}
          </HealthLinksContext.Provider>
        </main>
      )}
    </SiteScoped>
  );
}

export function SiteAssetsFrame({
  detail,
  sitesPath,
  health = DEFAULT_HEALTH,
}: {
  detail: SiteDetailClient;
  sitesPath: string;
  health?: HealthClient;
}) {
  const { siteId } = useParams<{ siteId: string }>();
  return (
    <SiteScoped siteId={siteId} detail={detail} title="Battery" headingId={SITE_BATTERY_HEADING_ID}>
      {(site) => (
        <main aria-labelledby={SITE_BATTERY_HEADING_ID}>
          <Breadcrumbs
            trail={[
              { label: "Sites", to: sitesPath },
              { label: site.display_name, to: siteDetailHref(site.site_id) },
              { label: "Health", to: siteHealthHref(site.site_id) },
              { label: "Battery" },
            ]}
          />
          <PageHeader title="Battery" headingId={SITE_BATTERY_HEADING_ID} subtitle={`Site: ${site.display_name}`} />
          <OperatorSiteTabs siteId={site.site_id} current="Health" />
          <HealthLinksContext.Provider value={LINKS}>
            <SiteBatteryEntry siteId={site.site_id} client={health} />
          </HealthLinksContext.Provider>
        </main>
      )}
    </SiteScoped>
  );
}

export function SiteAssetFrame({
  detail,
  sitesPath,
  health = DEFAULT_HEALTH,
}: {
  detail: SiteDetailClient;
  sitesPath: string;
  health?: HealthClient;
}) {
  const { siteId, assetId } = useParams<{ siteId: string; assetId: string }>();
  const [header, setHeader] = useState<BatteryHeader | null>(null);
  const onHeader = useCallback((next: BatteryHeader) => setHeader(next), []);
  const title = header?.name ?? "Battery";
  return (
    <SiteScoped siteId={siteId} detail={detail} title="Battery" headingId={SITE_BATTERY_HEADING_ID}>
      {(site) => (
        <main aria-labelledby={SITE_BATTERY_HEADING_ID}>
          <Breadcrumbs
            trail={[
              { label: "Sites", to: sitesPath },
              { label: site.display_name, to: siteDetailHref(site.site_id) },
              { label: "Health", to: siteHealthHref(site.site_id) },
              { label: "Battery", to: siteAssetsHref(site.site_id) },
              { label: title },
            ]}
          />
          {/* W1-F5a: the mock's asset heading - the battery's name, its declared rating and its site. */}
          <PageHeader
            title={title}
            headingId={SITE_BATTERY_HEADING_ID}
            subtitle={
              header?.nominal
                ? `Battery · ${header.nominal} nominal · site: ${site.display_name}`
                : `Battery · site: ${site.display_name}`
            }
          />
          <OperatorSiteTabs siteId={site.site_id} current="Health" />
          <HealthLinksContext.Provider value={LINKS}>
            <SiteBattery
              siteId={site.site_id}
              siteName={site.display_name}
              assetId={assetId ?? ""}
              client={health}
              onHeader={onHeader}
            />
          </HealthLinksContext.Provider>
        </main>
      )}
    </SiteScoped>
  );
}
