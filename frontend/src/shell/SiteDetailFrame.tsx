import { useParams, useSearchParams } from "react-router-dom";

import type { FeatureFlags } from "../config/featureFlags";
import {
  SITE_DETAIL_HEADING_ID,
  SiteDetails,
  SiteQuickAction,
} from "../sites/SiteDetails";
import type { SiteDetailClient } from "../sites/siteDirectoryClient";
import { SiteOverview } from "../sites/SiteOverview";
import type { SiteOverviewClient } from "../sites/siteOverviewClient";
import { createFindingIndexClient, type FindingIndexClient } from "../sites/findingIndexClient";
import type { SiteTemplateLineageClient } from "../sites/siteTemplateLineage";
import { OperatorSiteTabs } from "./operatorSiteTabs";
import type { ColdAssessmentClient } from "../sites/coldAssessmentClient";
import type { ColdSiteClient } from "../sites/coldSiteClient";
import { useSiteRecord } from "../sites/useSiteRecord";
import { coldSiteScreen } from "./coldSiteRoutes";
import {
  findingHref,
  siteEvidenceAcceptedRecordHref,
  siteEvidenceHref,
  siteEvidenceRecordHref,
  siteFinancialAssumptionsHref,
  siteFinancialsHref,
  siteFindingHref,
  siteFindingsHref,
  sitePerformanceHref,
} from "./operatorSiteRoutes";
import { findingIndexScopeQuery } from "./SiteAnalyticsFrames";
import { simulatorLabSiteActions } from "./simulatorLabRoutes";

/**
 * The operator route for one site, addressed by `site_id`.
 *
 * This frame composes the shared site substrate and adds nothing to what it
 * renders. Every value, label, unavailable state and refusal comes from
 * `frontend/src/sites/`, so the Lab's site view will present a site the same
 * way rather than growing a second opinion about what a site is.
 *
 * What the shell adds is what is genuinely a shell concern: the landmark, the
 * operator Site tab row, the breadcrumb's parent, and the Site actions that
 * belong to the Simulator Lab.
 *
 * T008's `Back to Sites` link is gone. The breadcrumb leads to the same place
 * under the same name, and a page with two links to one address makes a reader
 * wonder which is which - the same reason T011A dropped `Back to this site`
 * when the Overview tab arrived.
 *
 * The gated actions come from `simulatorLabSiteActions`, the one gated module,
 * which returns nothing at all when the flag is off. So a gate-off build
 * renders no simulator control and no hint that one exists, and this frame
 * makes no decision about it - it renders what the list contains. The
 * substrate could not own them: deciding them means reading the flag and
 * naming the Lab, and the substrate may do neither.
 *
 * `View Live Data` is deliberately not here. It is an operator capability
 * unavailable for an operator reason, identical in both gate states, so the
 * substrate owns it and both shells will show it the same way.
 *
 * The tab row replaces T008's plain `Site configuration` link. That link was
 * what this slice could say truthfully at the time - one aspect of a site,
 * named and reachable - and the canonical row is what replaces it: the same
 * destination under its product name, beside the rest of the aspects a site
 * has. `Back to Sites` stays, because the Sites index is not an aspect of a
 * site and has no tab.
 *
 * The Overview body (T027 phase 2) is the substrate's `SiteOverview`, read
 * from accepted evidence beside Site > Evidence; this frame only hands it the
 * client and the inspector addresses its evidence links open.
 *
 * This route is an operator capability and is never gated. It is registered
 * and served identically with `simulator_lab.enabled` true and false, and it
 * offers no crossing into the Simulator Lab in either state.
 *
 * It replaces the parameterless `/site-details` frame from T002. That frame
 * described no site because no site identity existed when it was written; a
 * site now has one, so the placeholder and its navigation item are gone rather
 * than left standing beside their identified replacement.
 */
export interface SiteDetailFrameProps {
  detail: SiteDetailClient;
  /** The Overview read (T027 phase 2). Operator, never gated. */
  overview: SiteOverviewClient;
  sitesPath: string;
  flags: FeatureFlags;
  /**
   * The gated template-lineage read. The app resolves it from the gate with
   * `simulatorLabSiteTemplateLineage`, so it is absent when the gate is
   * closed; this frame only passes it to the substrate.
   */
  templateLineage?: SiteTemplateLineageClient;
  /** S5-02: the Site Finding index read behind the Overview's selected-day Finding list. */
  findingIndex?: FindingIndexClient;
  /** W2-04: the five cold Site reads; a COLDCHAIN Site's Overview renders the `cold` screen from them. */
  coldSite?: ColdSiteClient;
  /** W2-04: the W2-03 selected temperature read behind the cold Overview's chamber chart. */
  coldAssessment?: ColdAssessmentClient;
}

const DEFAULT_FINDING_INDEX = createFindingIndexClient();

export function SiteDetailFrame({
  detail,
  overview,
  sitesPath,
  flags,
  templateLineage,
  findingIndex = DEFAULT_FINDING_INDEX,
  coldSite,
  coldAssessment,
}: SiteDetailFrameProps) {
  const { siteId } = useParams<{ siteId: string }>();
  const [params] = useSearchParams();
  // W2-04: the Site's type selects the cold Overview (the W2-01 Foundation frame's pattern).
  const record = useSiteRecord(coldSite === undefined ? undefined : siteId, detail);
  if (record?.status === "loaded" && record.site.site_type === "COLDCHAIN" && coldSite !== undefined && coldAssessment !== undefined) {
    return coldSiteScreen({
      view: "overview",
      site: record.site,
      params,
      coldSite,
      coldAssessment,
      tabs: <OperatorSiteTabs siteId={siteId} current="Overview" />,
      sitesPath,
    });
  }

  return (
    <main aria-labelledby={SITE_DETAIL_HEADING_ID}>
      <SiteDetails
        siteId={siteId}
        detail={detail}
        templateLineage={templateLineage}
        tabs={<OperatorSiteTabs siteId={siteId} current="Overview" />}
        parentTrail={() => [{ label: "Sites", to: sitesPath }]}
        overview={(canonicalId) => (
          <SiteOverview
            siteId={canonicalId}
            client={overview}
            evidencePageHref={siteEvidenceHref(canonicalId)}
            evidenceHref={(signal, messageId) =>
              siteEvidenceRecordHref(canonicalId, signal, messageId)
            }
            findingHref={(assessmentId) => findingHref(canonicalId, assessmentId)}
            dispatchHref={(assessmentId) =>
              assessmentId === undefined
                ? sitePerformanceHref(canonicalId, "dispatch")
                : `${sitePerformanceHref(canonicalId, "dispatch")}?interval=${encodeURIComponent(assessmentId)}`
            }
            windowLinks={{
              dispatchDay: (day, revisionId) =>
                `${sitePerformanceHref(canonicalId, "dispatch")}?day=${encodeURIComponent(day)}${
                  revisionId ? `&revision=${encodeURIComponent(revisionId)}` : ""
                }`,
              finding: (findingId, revisionId) => siteFindingHref(canonicalId, findingId, revisionId),
              financials: (findingId, revisionId, consequenceRevisionId) =>
                siteFinancialsHref(canonicalId, { findingId, revisionId, consequenceRevisionId }),
              assumption: (revisionId) => siteFinancialAssumptionsHref(canonicalId, { revisionId }),
              evidenceRecord: (evidenceId) => siteEvidenceAcceptedRecordHref(canonicalId, evidenceId),
              findingList: (scope) => `${siteFindingsHref(canonicalId)}?${findingIndexScopeQuery(scope)}`,
            }}
            findingIndex={findingIndex}
            analysisHref={(assessmentId, isFinding) =>
              isFinding
                ? findingHref(canonicalId, assessmentId, "analysis")
                : `${sitePerformanceHref(canonicalId, "dispatch")}?interval=${encodeURIComponent(assessmentId)}&view=analysis`
            }
          />
        )}
        quickActions={simulatorLabSiteActions(flags).map((action) => (
          <SiteQuickAction
            key={action.label}
            label={action.label}
            unavailableBecause={action.unavailableBecause}
            vocabularyExempt="lab"
          />
        ))}
      />
    </main>
  );
}
