import type { ReactNode } from "react";

import type { ColdAssessmentClient } from "../sites/coldAssessmentClient";
import { coldWindowFromParams } from "../sites/coldAssessmentClient";
import type { ColdSiteClient } from "../sites/coldSiteClient";
import { ColdSiteFrame, type ColdSiteRoutes, type ColdSiteView } from "../sites/coldSiteViews";
import type { SiteDetailReadModel } from "../sites/siteReadModel";
import { deriveSiteView } from "../sites/siteViewModel";
import {
  siteDetailHref,
  siteEvidenceHref,
  siteFinancialAssumptionsHref,
  siteFinancialsHref,
  siteFindingHref,
  siteFindingsHref,
  siteFoundationHref,
  sitePerformanceHref,
} from "./operatorSiteRoutes";

/** W2-04: the UI route bases (no query) the five cold Site screens link to. */
export function coldSiteRoutes(siteId: string): ColdSiteRoutes {
  return {
    overview: siteDetailHref(siteId),
    evidence: siteEvidenceHref(siteId),
    financials: siteFinancialsHref(siteId),
    assumptions: siteFinancialAssumptionsHref(siteId),
    temperature: sitePerformanceHref(siteId, "temperature"),
    backup: sitePerformanceHref(siteId, "backup"),
    findings: siteFindingsHref(siteId),
    finding: (findingId) => siteFindingHref(siteId, findingId),
    foundation: siteFoundationHref(siteId),
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
      parentTrail={[
        { label: "Sites", to: sitesPath },
        overview ? { label: site.display_name } : { label: site.display_name, to: siteDetailHref(site.site_id) },
      ]}
    />
  );
}
