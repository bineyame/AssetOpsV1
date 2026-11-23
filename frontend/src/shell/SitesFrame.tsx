import { RangeLink as Link } from "../ui/RangeLink";

import type { FeatureFlags } from "../config/featureFlags";
import type { EstateClient } from "../estate/estateClient";
import type { PortfolioSitesClient } from "../estate/portfolioSitesClient";
import { SitesListPage } from "../estate/sitesList";
import type { SiteDirectoryClient } from "../sites/siteDirectoryClient";
import type { SiteTemplateLineageClient } from "../sites/siteTemplateLineage";
import { simulatorLabCreateSiteEntryPoints } from "./simulatorLabRoutes";

/**
 * The operator Sites route. The Simulator Lab create action comes from the single gated entry-point module (T004):
 * with `simulator_lab.enabled` false it returns nothing and this frame names no Lab surface. The Sites list itself is
 * never gated.
 */
export interface SitesFrameProps {
  flags: FeatureFlags;
  directory: SiteDirectoryClient;
  /**
   * The gated template-lineage read. Kept on the props for the App's wiring; the Sites list (IA-P P4b) draws no
   * template column, so it is not used here.
   */
  templateLineage?: SiteTemplateLineageClient;
  /** IA-P P4b: E1, the Sites rows for the range (tests pass a stub). */
  sites?: PortfolioSitesClient;
  /** IA-P P4b: the estate portfolio read, for E0's waiting counts. */
  estate?: EstateClient;
}

/**
 * IA-P P4b (spec §6 P4b, §5.3): `/sites` is the Sites list on the one list component, its rows from E1 for the range.
 * The directory table and its Lifecycle column are removed; the gated Simulator Lab create action stays in the header.
 */
export function SitesFrame({ flags, directory, sites, estate }: SitesFrameProps) {
  const createEntryPoints = simulatorLabCreateSiteEntryPoints(flags);
  return (
    <main aria-labelledby="sites-heading">
      <SitesListPage
        sites={sites}
        estate={estate}
        directory={directory}
        actions={createEntryPoints.map((entryPoint) => (
          <Link className="action action--primary" key={entryPoint.to} to={entryPoint.to}>
            {entryPoint.label}
          </Link>
        ))}
      />
    </main>
  );
}
