import { useParams } from "react-router-dom";

import type { FeatureFlags } from "../config/featureFlags";
import {
  SITE_DETAIL_HEADING_ID,
  SiteDetails,
  SiteQuickAction,
} from "../sites/SiteDetails";
import type { SiteDetailClient } from "../sites/siteDirectoryClient";
import { OperatorSiteTabs } from "./operatorSiteTabs";
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
  sitesPath: string;
  flags: FeatureFlags;
}

export function SiteDetailFrame({
  detail,
  sitesPath,
  flags,
}: SiteDetailFrameProps) {
  const { siteId } = useParams<{ siteId: string }>();

  return (
    <main aria-labelledby={SITE_DETAIL_HEADING_ID}>
      <SiteDetails
        siteId={siteId}
        detail={detail}
        tabs={<OperatorSiteTabs siteId={siteId} current="Overview" />}
        parentTrail={() => [{ label: "Sites", to: sitesPath }]}
        quickActions={simulatorLabSiteActions(flags).map((action) => (
          <SiteQuickAction
            key={action.label}
            label={action.label}
            unavailableBecause={action.unavailableBecause}
          />
        ))}
      />
    </main>
  );
}
