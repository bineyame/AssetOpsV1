/**
 * S7-01b route frames: Site Health (`/sites/{site}/health[?gateway=]`), the
 * Site battery entry (`/sites/{site}/assets`) and one configured battery
 * (`/sites/{site}/assets/{asset}`). Each is Site-scoped (unknown Site is "not
 * found", never an empty healthy page) and highlights the Health tab.
 */
import { useCallback, useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";

import { coldWindowFromParams, type ColdWindowQuery } from "../sites/coldAssessmentClient";
import { ReportSelected } from "../sites/evSelectedWindow";
import { createColdDepthClient, type ColdDepthClient } from "../sites/ColdDepthClient";
import { ColdHealthDepth } from "../sites/ColdHealthDepth";
import { createEvDepthClient, type EvDepthClient } from "../sites/evDepthClient";
import { EvHealthDepth } from "../sites/EvHealthDepth";
import { createHealthClient, type HealthClient } from "../sites/healthClient";
import { SiteBattery, SiteBatteryEntry, type BatteryHeader } from "../sites/SiteBattery";
import { HealthLinksContext, SiteHealth, type HealthLinks } from "../sites/SiteHealth";
import { createHealthRangeClient, type HealthRangeClient } from "../sites/healthRangeClient";
import { SiteHealthRange } from "../sites/SiteHealthRange";
import type { SiteDetailClient } from "../sites/siteDirectoryClient";
import { siteSourceModeLabel } from "../sites/siteViewModel";
import { Breadcrumbs, PageHeader, SITE_SCREEN_DESCRIPTIONS, SitePageHeader } from "../ui";
import { coldSiteRoutes, coldTabSearch } from "./coldSiteRoutes";
import { siteAssetHref, siteAssetsHref, siteDetailHref, siteHealthHref, sitePerformanceHref } from "./operatorSiteRoutes";
import { EV_SITE_TAB_HREFS } from "./evSiteRoutes";
import { OperatorSiteTabs } from "./operatorSiteTabs";
import { RangeNotUsed, RangeSpan } from "../ui/rangeFocus";
import { RangeLink as Link } from "../ui/RangeLink";
import { focusDayOf, rangeWindow, readSharedRange } from "../ui/sharedRange";
import { SiteScoped } from "./SiteAnalyticsFrames";

const DEFAULT_HEALTH = createHealthClient();
const DEFAULT_COLD_DEPTH = createColdDepthClient();
const DEFAULT_EV_DEPTH = createEvDepthClient();
const DEFAULT_HEALTH_RANGE = createHealthRangeClient();
const LINKS: HealthLinks = { health: siteHealthHref, assets: siteAssetsHref, asset: siteAssetHref };
export const SITE_HEALTH_HEADING_ID = "site-health-heading";
export const SITE_BATTERY_HEADING_ID = "site-battery-heading";

/**
 * R347 (W5-EV): the EV Health main tabs open the built EV pages and carry the loaded read's own selected window
 * (Q14/Q23); a refused or no-window read carries none.
 */
function EvHealthWithTabs({ siteId, window, client }: { siteId: string; window: ColdWindowQuery; client: EvDepthClient }) {
  const selectedKey = `${siteId}|${window.from ?? ""}|${window.to ?? ""}|${window.known_at ?? ""}`;
  const [selected, setSelected] = useState<{ key: string; search: string } | null>(null);
  const report = useCallback((search: string) => setSelected({ key: selectedKey, search }), [selectedKey]);
  const search = selected !== null && selected.key === selectedKey ? selected.search : "";
  return (
    <>
      <OperatorSiteTabs siteId={siteId} current="Health" hrefs={EV_SITE_TAB_HREFS} search={search} />
      <ReportSelected.Provider value={report}>
        <EvHealthDepth siteCode={siteId} window={window} client={client} sessionsPath={sitePerformanceHref(siteId, "sessions")} />
      </ReportSelected.Provider>
    </>
  );
}

export function SiteHealthFrame({
  detail,
  sitesPath,
  health = DEFAULT_HEALTH,
  coldDepth = DEFAULT_COLD_DEPTH,
  evDepth = DEFAULT_EV_DEPTH,
  healthRange = DEFAULT_HEALTH_RANGE,
}: {
  detail: SiteDetailClient;
  sitesPath: string;
  health?: HealthClient;
  /** SR-6b: a mini-grid Site with a range in its address reads `/health-range`. */
  healthRange?: HealthRangeClient;
  /** W5-01a C3: a COLDCHAIN Site renders `cold-health` from the selected `/cold/health` read. */
  coldDepth?: ColdDepthClient;
  /** W5-03b E4: an EV_CHARGING Site renders `ev-health` from the selected `/ev/health` read. */
  evDepth?: EvDepthClient;
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
          {site.site_type === "EV_CHARGING" ? null : <OperatorSiteTabs siteId={site.site_id} current="Health" search={coldTabSearch(site, params)} />}
          <HealthLinksContext.Provider value={LINKS}>
            {site.site_type === "COLDCHAIN" ? (
              /* W5-F1 F1-1 (R22): v69 cold-health ends at Condition and evidence; no Data sources panel. */
              <ColdHealthDepth
                siteCode={site.site_id}
                window={coldWindowFromParams(params)}
                client={coldDepth}
                routes={coldSiteRoutes(site.site_id)}
              />
            ) : site.site_type === "EV_CHARGING" ? (
              /* W5-03b E4 (R60 withdrawn): v69 ev-health ends at Condition and evidence; no Data sources panel. */
              <EvHealthWithTabs siteId={site.site_id} window={coldWindowFromParams(params)} client={evDepth} />
            ) : (
              <MiniGridHealth
                siteId={site.site_id}
                siteName={site.display_name}
                params={params}
                health={health}
                healthRange={healthRange}
                gateway={gateway}
              />
            )}
          </HealthLinksContext.Provider>
        </main>
      )}
    </SiteScoped>
  );
}

/**
 * SR-6b (rev 10 §10.2): mini-grid Health. With a range in the address it is the range page (the bar declares nothing:
 * "All pages"); with `day=` too it is the same page for that one day (request `from=day&to=day+1`, the bar declares
 * that day, "Back to the whole range"). The point-in-time panels follow as "Battery (current settings)" and "Contact
 * now". Without a valid range it stays the point-in-time page and the bar says the range is not used (SR-4c).
 * MOCK DEVIATION R724 (v69 `health:1/2` is current contact only).
 */
function MiniGridHealth({
  siteId,
  siteName,
  params,
  health,
  healthRange,
  gateway,
}: {
  siteId: string;
  siteName: string;
  params: URLSearchParams;
  health: HealthClient;
  healthRange: HealthRangeClient;
  gateway: string | null;
}) {
  const range = readSharedRange(params);
  if (range.status !== "set") {
    return (
      <>
        {/* MOCK DEVIATION R718/R719 (v71 Change 0b shows only "All pages"). SR-4c (D-SR.6, R719): without a range, mini-grid Health reads the server clock; the bar says the range is not used. */}
        <RangeNotUsed note="shows now" />
        <SiteHealth siteId={siteId} siteName={siteName} client={health} selectedGateway={gateway} />
      </>
    );
  }
  const day = focusDayOf(params);
  const window = rangeWindow(day === null ? range : { from: day, to: day });
  return (
    <>
      {day === null ? null : (
        <>
          <RangeSpan from={day} to={day} />
          <p className="health-range-back">
            <Link to={siteHealthHref(siteId)}>Back to the whole range</Link>
          </p>
        </>
      )}
      <SiteHealthRange
        siteCode={siteId}
        query={{ from: window.from, to: window.to, known_at: range.known_at }}
        drill={day !== null}
        client={healthRange}
      />
      <SiteHealth siteId={siteId} siteName={siteName} client={health} selectedGateway={gateway} underRange />
    </>
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
          {/* SR-4c (D-SR.43): the battery list and page are Foundation configuration, not ranged. */}
          <RangeNotUsed note="current settings" />
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
  // MOCK DEVIATION D4 (post-W6 shell Q3/Q17, register R380): a refused or unnamed battery keeps the generic "Battery"
  // heading; the mock's illustrative asset name is never shown as a fact.
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
          <RangeNotUsed note="current settings" />
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
