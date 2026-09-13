/**
 * The Site view model: the one place a site record becomes display.
 *
 * Vocabulary lives here and nowhere else, because the failure this substrate
 * exists to prevent is two shells labelling the same field differently. Every
 * label, every fallback, and every unavailable state is decided once.
 *
 * The rule this module must not break: configuration origin, source mode, and
 * lifecycle status are independent facts and none is derived from, defaulted
 * from, or rendered as a proxy for another. In M1 every `USER`-origin site
 * also has `SIMULATED` source mode, because the Simulator Lab is the only
 * creation path. They coincide by circumstance, not by definition, so nothing
 * here may compute one from the other: a shipped demo site would be `SHIPPED`
 * plus `SIMULATED`, and a site registered against a real integration would be
 * `USER` plus `LIVE`.
 *
 * `Simulated` is the rendering of `source.mode`. It is provenance, never
 * status, never health, and never an assessment, so it never shares a column
 * or a label with lifecycle status.
 *
 * An unrecognised value is shown as it arrived rather than mapped to a
 * plausible-looking label. Inventing a label for a value this build does not
 * know would be a claim about a site rather than a statement about the record.
 */

import type { SiteSummary } from "./siteReadModel";

/** What the Sites index renders for one site. */
export interface SiteView {
  siteId: string;
  displayName: string;
  siteType: string;
  location: string;
  lifecycleStatus: string;
  sourceMode: string;
  configurationOrigin: string;
  templateProvenance: string;
}

const SITE_TYPE_LABELS: Record<string, string> = {
  MINIGRID: "Mini-grid",
  COLDCHAIN: "Cold chain",
};

const LIFECYCLE_STATUS_LABELS: Record<string, string> = {
  PLANNED: "Planned",
  COMMISSIONED: "Commissioned",
  ACTIVE: "Active",
  DECOMMISSIONED: "Decommissioned",
  ARCHIVED: "Archived",
};

const SOURCE_MODE_LABELS: Record<string, string> = {
  SIMULATED: "Simulated",
  LIVE: "Live",
};

const CONFIGURATION_ORIGIN_LABELS: Record<string, string> = {
  USER: "User",
  SHIPPED: "Shipped",
};

/** What a site with no template provenance shows. It came from no template. */
export const NO_TEMPLATE_PROVENANCE = "Not created from a template";

function label(value: string, labels: Record<string, string>): string {
  return labels[value] ?? value;
}

export function deriveSiteView(site: SiteSummary): SiteView {
  return {
    siteId: site.site_id,
    displayName: site.display_name,
    siteType: label(site.site_type, SITE_TYPE_LABELS),
    location: `${site.location.locality}, ${site.location.country}`,
    lifecycleStatus: label(site.lifecycle_status, LIFECYCLE_STATUS_LABELS),
    sourceMode: label(site.source.mode, SOURCE_MODE_LABELS),
    configurationOrigin: label(site.origin, CONFIGURATION_ORIGIN_LABELS),
    templateProvenance:
      site.template === null
        ? NO_TEMPLATE_PROVENANCE
        : `${site.template.template_id} v${site.template.template_version}`,
  };
}
