import { Link, useParams } from "react-router-dom";

import {
  SITE_CONFIGURATION_HEADING_ID,
  SiteConfiguration,
} from "../sites/SiteConfiguration";
import type { SiteDetailClient } from "../sites/siteDirectoryClient";
import { siteDetailHref } from "./operatorSiteRoutes";

/**
 * The operator route for one site's configuration, addressed by `site_id`.
 *
 * This frame composes the shared site substrate and adds nothing to it. Every
 * value, label, stated absence and refusal comes from `frontend/src/sites/`,
 * so the Lab's site view will present a configuration the same way rather than
 * growing a second opinion about what a foundation is.
 *
 * What the shell adds is the one thing that is genuinely a shell concern: the
 * landmark, and a way back to the site this configuration belongs to. That
 * link is navigation, not an action on the configuration, and it is rendered
 * outside the shared region rather than injected into it, so there is no
 * extension slot to build.
 *
 * This route is an operator capability and is never gated. It is registered
 * and served identically with `simulator_lab.enabled` true and false, and it
 * offers no crossing into the Simulator Lab in either state.
 *
 * It replaces the parameterless `/site-configuration` frame from T002. That
 * frame described no site because no site identity existed when it was
 * written; a site now has one, so the placeholder and its navigation item are
 * gone rather than left standing beside their identified replacement. Nothing
 * took the navigation item's place: a navigation item cannot name which site's
 * configuration it would open.
 */
export interface SiteConfigurationFrameProps {
  detail: SiteDetailClient;
}

export function SiteConfigurationFrame({
  detail,
}: SiteConfigurationFrameProps) {
  const { siteId } = useParams<{ siteId: string }>();

  return (
    <main aria-labelledby={SITE_CONFIGURATION_HEADING_ID}>
      <SiteConfiguration siteId={siteId} detail={detail} />

      {siteId === undefined ? null : (
        <p>
          <Link to={siteDetailHref(siteId)}>Back to this site</Link>
        </p>
      )}
    </main>
  );
}
