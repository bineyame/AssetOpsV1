import { Link } from "react-router-dom";

import type { FeatureFlags } from "../config/featureFlags";
import { PageHeader } from "../ui";
import { SitesIndex } from "../sites/SitesIndex";
import type { SiteDirectoryClient } from "../sites/siteDirectoryClient";
import { siteDetailHref } from "./operatorSiteRoutes";
import { simulatorLabCreateSiteEntryPoints } from "./simulatorLabRoutes";

/**
 * The operator Sites route.
 *
 * This frame composes the shared Site substrate and adds nothing to it. The
 * listing, the empty state, the unavailable state, and every label come from
 * `frontend/src/sites/`, so the Lab's site view will render the same things
 * the same way rather than growing a second opinion about what a site is.
 *
 * What the operator shell adds is the one thing that is genuinely a shell
 * concern: a gated way into the Simulator Lab create flow. It is rendered
 * outside the shared region, not injected into it, so there is no extension
 * slot to build and nothing about the substrate depends on the gate.
 *
 * The entry point comes from the existing Simulator Lab entry-point module, so
 * it goes through the single chokepoint T004 established rather than adding a
 * second one. With `simulator_lab.enabled` false that module returns nothing,
 * this frame renders no action at all, and it does not name the Simulator Lab:
 * a build that does not serve a surface must not teach that the surface
 * exists. An empty Sites index with no way to add a site is the correct state
 * for a gate-off build, not a defect.
 *
 * Each row opens that site. Where a site's page lives is a shell fact about
 * the shell's own routes, so this frame supplies the address and the substrate
 * renders the link. That is the one operator destination this slice adds, and
 * it is not a navigation item: a navigation item cannot name which site it
 * would open.
 *
 * The Sites index itself is never gated. It is served identically in both flag
 * states, and a site created while the Lab was enabled is fully listed when it
 * is disabled, because the gate covers surfaces and execution and never
 * objects or stores.
 */
export interface SitesFrameProps {
  flags: FeatureFlags;
  directory: SiteDirectoryClient;
}

export function SitesFrame({ flags, directory }: SitesFrameProps) {
  const createEntryPoints = simulatorLabCreateSiteEntryPoints(flags);

  return (
    <main aria-labelledby="sites-heading">
      <PageHeader title="Sites" headingId="sites-heading" />

      <SitesIndex directory={directory} siteHref={siteDetailHref} />

      {/*
       * The gated create entry point stays exactly where T006 put it, in the
       * same two flag states, with the same label from the same module.
       * Moving it into the page header and styling it as the canonical
       * `+ New Site` action is T011's work, which this slice's scope limits
       * name explicitly: fidelity stage 1 is the vocabulary, not any screen's
       * information architecture.
       */}
      {createEntryPoints.length > 0 ? (
        <p>
          {createEntryPoints.map((entryPoint) => (
            <Link key={entryPoint.to} to={entryPoint.to}>
              {entryPoint.label}
            </Link>
          ))}
        </p>
      ) : null}
    </main>
  );
}
