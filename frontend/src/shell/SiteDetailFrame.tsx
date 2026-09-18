import { Link, useParams } from "react-router-dom";

import {
  SITE_DETAIL_HEADING_ID,
  SiteDetails,
} from "../sites/SiteDetails";
import type { SiteDetailClient } from "../sites/siteDirectoryClient";
import { OperatorSiteTabs } from "./operatorSiteTabs";

/**
 * The operator route for one site, addressed by `site_id`.
 *
 * This frame composes the shared site substrate and adds nothing to what it
 * renders. Every value, label, unavailable state and refusal comes from
 * `frontend/src/sites/`, so the Lab's site view will present a site the same
 * way rather than growing a second opinion about what a site is.
 *
 * What the shell adds is the one thing that is genuinely a shell concern: the
 * landmark, the operator Site tab row, and a way back to the shell's own Sites
 * index. All of it is navigation rather than action on the site.
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
}

export function SiteDetailFrame({ detail, sitesPath }: SiteDetailFrameProps) {
  const { siteId } = useParams<{ siteId: string }>();

  return (
    <main aria-labelledby={SITE_DETAIL_HEADING_ID}>
      <SiteDetails
        siteId={siteId}
        detail={detail}
        tabs={<OperatorSiteTabs siteId={siteId} current="Overview" />}
      />

      <p>
        <Link to={sitesPath}>Back to Sites</Link>
      </p>
    </main>
  );
}
