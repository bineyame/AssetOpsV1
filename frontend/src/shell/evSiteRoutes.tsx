import { useSearchParams, useParams } from "react-router-dom";

import { Panel } from "../ui";
import { coldWindowFromParams } from "../sites/coldAssessmentClient";
import { EV_SITE_HEADING_ID, EvSiteFrame, type EvSiteRoutes, type EvSiteView } from "../sites/EvSiteViews";
import type { EvSiteClient } from "../sites/evSiteClient";
import type { EvScenariosClient } from "../sites/evScenariosClient";
import type { SiteDetailClient } from "../sites/siteDirectoryClient";
import { deriveSiteView } from "../sites/siteViewModel";
import { siteDetailHref, siteEvHref, siteFindingHref, siteFoundationViewHref, sitePerformanceHref } from "./operatorSiteRoutes";
import { OperatorSiteTabs } from "./operatorSiteTabs";
import { SiteScoped } from "./SiteAnalyticsFrames";

/** W2-07: the UI route bases (no query) the five EV Site screens link to. */
export function evSiteRoutes(siteId: string): EvSiteRoutes {
  return {
    overview: siteEvHref(siteId),
    evidence: siteEvHref(siteId, "evidence"),
    analysis: siteEvHref(siteId, "analysis"),
    financials: siteEvHref(siteId, "financials"),
    assumptions: siteEvHref(siteId, "assumptions"),
    scenarios: siteEvHref(siteId, "scenarios"),
    sessions: sitePerformanceHref(siteId, "sessions"),
    availability: sitePerformanceHref(siteId, "availability"),
    energy: sitePerformanceHref(siteId, "energy"),
    finding: (findingId) => siteFindingHref(siteId, findingId),
    // W2-F B2/M8: the Foundation SLD takes only `at`; the Overview passes the window end (cutoff is not carried).
    sld: (at) => siteFoundationViewHref(siteId, "sld", at),
  };
}

const CURRENT_TAB: Record<EvSiteView, string> = {
  overview: "Overview",
  evidence: "Evidence",
  analysis: "Evidence",
  financials: "Financials",
  assumptions: "Financials",
  scenarios: "Financials",
};

/** W2-07: an EV_CHARGING Site's `ev`, `ev-evidence`, `ev-evidence-analysis`, `ev-financials` or `ev-assumptions` screen. */
export function SiteEvFrame({
  detail,
  sitesPath,
  view,
  evSite,
  evScenarios,
}: {
  detail: SiteDetailClient;
  sitesPath: string;
  view: EvSiteView;
  evSite: EvSiteClient;
  /** W5-03b E6: the authored EV scenario list client for the Scenarios view. */
  evScenarios?: EvScenariosClient;
}) {
  const { siteId } = useParams<{ siteId: string }>();
  const [params] = useSearchParams();
  return (
    <SiteScoped siteId={siteId} detail={detail} title="EV charging" headingId={EV_SITE_HEADING_ID}>
      {(site) =>
        site.site_type !== "EV_CHARGING" ? (
          <main aria-labelledby={EV_SITE_HEADING_ID}>
            <h1 id={EV_SITE_HEADING_ID}>{site.display_name}</h1>
            <Panel heading="Not an EV charging Site" headingId="ev-site-wrong-type-heading">
              <p>This EV Site or record was not found.</p>
            </Panel>
          </main>
        ) : (
          <EvSiteFrame
            view={view}
            siteId={site.site_id}
            siteName={site.display_name}
            mode={deriveSiteView(site).sourceMode}
            window={coldWindowFromParams(params)}
            scenarioAt={params.get("scenario_at")}
            scenarios={evScenarios}
            client={evSite}
            routes={evSiteRoutes(site.site_id)}
            tabs={<OperatorSiteTabs siteId={site.site_id} current={CURRENT_TAB[view]} />}
            parentTrail={[
              { label: "Sites", to: sitesPath },
              view === "overview" ? { label: site.display_name } : { label: site.display_name, to: siteDetailHref(site.site_id) },
            ]}
          />
        )
      }
    </SiteScoped>
  );
}
