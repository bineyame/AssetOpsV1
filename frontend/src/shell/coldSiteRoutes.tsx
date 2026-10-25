import type { ReactNode } from "react";

import type { ColdAssessmentClient } from "../sites/coldAssessmentClient";
import { coldWindowFromParams, coldWindowSearch } from "../sites/coldAssessmentClient";
import type { ColdSiteClient } from "../sites/coldSiteClient";
import { ColdSiteFrame, type ColdSiteRoutes, type ColdSiteView } from "../sites/coldSiteViews";
import type { SiteDetailReadModel } from "../sites/siteReadModel";
import { deriveSiteView } from "../sites/siteViewModel";
import {
  EVIDENCE_PATH,
  siteDetailHref,
  siteEvidenceHref,
  siteFinancialAssumptionsHref,
  siteFinancialsHref,
  siteFindingHref,
  siteFindingsHref,
  siteFoundationHref,
  siteHealthHref,
  sitePerformanceHref,
  siteWorkMaintenanceHref,
} from "./operatorSiteRoutes";

/**
 * post-W6 W2-cold (cross-card ruling 3, B14-10): a COLDCHAIN Site's main tabs keep the selected `from`, `to` and
 * `known_at` through W2-EV's `OperatorSiteTabs` `search` override; other Site types get no query (undefined).
 */
export function coldTabSearch(site: { site_type: string }, params: URLSearchParams): string | undefined {
  return site.site_type === "COLDCHAIN" ? coldWindowSearch(coldWindowFromParams(params)) : undefined;
}

/** W2-04: the UI route bases (no query) the five cold Site screens link to. */
export function coldSiteRoutes(siteId: string): ColdSiteRoutes {
  return {
    overview: siteDetailHref(siteId),
    evidence: siteEvidenceHref(siteId),
    financials: siteFinancialsHref(siteId),
    assumptions: siteFinancialAssumptionsHref(siteId),
    temperature: sitePerformanceHref(siteId, "temperature"),
    backup: sitePerformanceHref(siteId, "backup"),
    cooling: sitePerformanceHref(siteId, "cooling"),
    health: siteHealthHref(siteId),
    findings: siteFindingsHref(siteId),
    finding: (findingId) => siteFindingHref(siteId, findingId),
    foundation: siteFoundationHref(siteId),
    // The Foundation SLD view with no `at` (the same base as `siteFoundationViewHref(siteId, "sld", null)`).
    sld: `${siteFoundationHref(siteId)}/sld`,
    workMaintenance: siteWorkMaintenanceHref(siteId),
    portfolioEvidence: EVIDENCE_PATH,
  };
}

/** W2-04: a COLDCHAIN Site's Overview, Evidence (and its Analysis view), Financials or Assumptions screen. */
export function coldSiteScreen({
  view,
  site,
  params,
  coldSite,
  coldAssessment,
  tabs,
  sections,
  sitesPath,
}: {
  view: ColdSiteView;
  site: SiteDetailReadModel;
  params: URLSearchParams;
  coldSite: ColdSiteClient;
  coldAssessment: ColdAssessmentClient;
  tabs: ReactNode;
  /** The Financials subtab row, shared with the generic Financials frame (one Scenarios entry). */
  sections?: ReactNode;
  sitesPath: string;
}) {
  const overview = view === "overview";
  return (
    <ColdSiteFrame
      view={view}
      siteId={site.site_id}
      siteName={site.display_name}
      mode={deriveSiteView(site).sourceMode}
      window={coldWindowFromParams(params)}
      client={coldSite}
      assessment={coldAssessment}
      routes={coldSiteRoutes(site.site_id)}
      tabs={tabs}
      sections={sections}
      timeZone={site.timezone}
      parentTrail={[
        { label: "Sites", to: sitesPath },
        overview ? { label: site.display_name } : { label: site.display_name, to: siteDetailHref(site.site_id) },
      ]}
    />
  );
}
