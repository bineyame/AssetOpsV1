import { Link, useParams } from "react-router-dom";

import {
  SITE_DETAIL_HEADING_ID,
  SiteDetails,
} from "../sites/SiteDetails";
import type { SiteDetailClient } from "../sites/siteDirectoryClient";
import { siteConfigurationHref } from "./operatorSiteRoutes";

/**
 * The operator route for one site, addressed by `site_id`.
 *
 * This frame composes the shared site substrate and adds nothing to it. Every
 * value, label, unavailable state and refusal comes from
 * `frontend/src/sites/`, so the Lab's site view will present a site the same
 * way rather than growing a second opinion about what a site is.
 *
 * What the shell adds is the one thing that is genuinely a shell concern: the
 * landmark, a way back to the shell's own Sites index, and a plain link to
 * this site's configuration. Both links are navigation, not actions on the
 * site, and both are rendered outside the shared region rather than injected
 * into it, so there is still no extension slot to build. The canonical tab bar
 * that will eventually carry the second one is chrome and arrives with the
 * fidelity slice; a link is what this slice can say truthfully.
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
      <SiteDetails siteId={siteId} detail={detail} />

      {siteId === undefined ? null : (
        <p>
          <Link to={siteConfigurationHref(siteId)}>Site configuration</Link>
        </p>
      )}

      <p>
        <Link to={sitesPath}>Back to Sites</Link>
      </p>
    </main>
  );
}
