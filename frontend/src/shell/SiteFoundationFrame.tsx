import { useParams } from "react-router-dom";

import {
  SITE_CONFIGURATION_HEADING_ID,
  SiteConfiguration,
} from "../sites/SiteConfiguration";
import type { SiteDetailClient } from "../sites/siteDirectoryClient";
import { OperatorSiteTabs } from "./operatorSiteTabs";

/**
 * The operator route for one site's Foundation, addressed by `site_id`.
 *
 * This frame composes the shared site substrate and adds nothing to what it
 * renders. Every value, label, stated absence and refusal comes from
 * `frontend/src/sites/`, so the Lab's site view will present a foundation the
 * same way rather than growing a second opinion about what one is.
 *
 * What the shell adds is the one thing that is genuinely a shell concern: the
 * landmark, and the operator Site tab row, which is how this shell divides a
 * site into aspects. The tab row is navigation, not an action on the site.
 *
 * It is the first thing to use a substrate slot. The row belongs under the
 * page header and above the facts, and that position is inside the shared
 * region, so the shell hands the substrate an element and the substrate places
 * it. The substrate still imports nothing from the shell and still decides
 * nothing about what a tab row contains: it renders the slot only for a site
 * it actually loaded, which is why a site that is not found offers no tab to a
 * surface of a site that does not exist.
 *
 * T008's `Back to this site` link is gone, replaced by the Overview tab. It
 * said the same thing and led to the same address; two links to one place is
 * how a reader starts wondering whether they are different.
 *
 * This route is an operator capability and is never gated. It is registered
 * and served identically with `simulator_lab.enabled` true and false, and it
 * offers no crossing into the Simulator Lab in either state.
 *
 * ## Names
 *
 * The product name of this surface is Foundation. The substrate component it
 * composes is still called `SiteConfiguration`, and its heading id is still
 * `site-configuration-heading`: T011A renames what a reader sees and what an
 * address says, and deliberately leaves internal names under
 * `frontend/src/sites/` alone. Renaming those would touch every Site-substrate
 * test and both single-definition guard patterns without changing a single
 * rendered character, which is churn standing between a reviewer and the
 * rename that matters. The heading id is not user-visible; the heading text
 * is, and it says Foundation.
 *
 * It replaces the parameterless `/site-configuration` frame from T002. That
 * frame described no site because no site identity existed when it was
 * written; a site has one now, so the placeholder and its navigation item are
 * gone rather than left standing beside their identified replacement. Nothing
 * took the navigation item's place: a navigation item cannot name which site's
 * foundation it would open.
 */
export interface SiteFoundationFrameProps {
  detail: SiteDetailClient;
}

export function SiteFoundationFrame({ detail }: SiteFoundationFrameProps) {
  const { siteId } = useParams<{ siteId: string }>();

  return (
    <main aria-labelledby={SITE_CONFIGURATION_HEADING_ID}>
      <SiteConfiguration
        siteId={siteId}
        detail={detail}
        tabs={<OperatorSiteTabs siteId={siteId} current="Foundation" />}
      />
    </main>
  );
}
