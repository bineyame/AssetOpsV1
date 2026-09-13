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

import type { SiteDetailReadModel, SiteSummary } from "./siteReadModel";

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

/**
 * A fact the product cannot state for a configuration-only site, and the
 * reason it cannot.
 *
 * The reason is not decoration. "No evidence" without a reason reads as a
 * measurement of zero; with one it reads as what it is, a statement about what
 * has been recorded. Every one of these is written here rather than in a
 * component, so the two shells cannot explain the same absence differently.
 */
export interface SiteUnavailableFact {
  value: string;
  reason: string;
}

/**
 * What a site page renders for one site.
 *
 * The six provenance-and-status concepts appear here as six fields, never as
 * one. Three come straight off the record - configuration origin, source mode,
 * lifecycle status. Three have no truthful source for a site with no accepted
 * evidence - integration readiness, evidence availability, source health - and
 * each is stated as unavailable with its reason rather than defaulted, zeroed,
 * or derived from one of the other three.
 *
 * Source health in particular is not rendered as a health value. A source that
 * is configured but has never been expected to report has no health state at
 * all, so no source-health vocabulary appears here.
 */
export interface SiteDetailView extends SiteView {
  timezone: string;
  foundationVersion: string;
  foundationValidFrom: string;
  integrationReadiness: SiteUnavailableFact;
  evidenceAvailability: SiteUnavailableFact;
  sourceHealth: SiteUnavailableFact;
}

/** Integration readiness: a separate concept, with no field behind it yet. */
export const INTEGRATION_READINESS_UNAVAILABLE: SiteUnavailableFact = {
  value: "Not recorded",
  reason:
    "No integration is configured for this site, and this build records no " +
    "integration readiness. Readiness is its own fact: it is not lifecycle " +
    "status, not source mode, and not derived from either.",
};

/** Evidence availability: a statement about evidence, not a measurement. */
export const EVIDENCE_AVAILABILITY_UNAVAILABLE: SiteUnavailableFact = {
  value: "No evidence",
  reason:
    "No evidence has been accepted for this site, so there is nothing to " +
    "show and nothing to analyse. This is a statement about evidence, not a " +
    "reading of zero and not a statement about the site's lifecycle status.",
};

/** Source health: not applicable, because no source is expected to report. */
export const SOURCE_HEALTH_UNAVAILABLE: SiteUnavailableFact = {
  value: "Not applicable",
  reason:
    "No source is expected to report for this site yet, so there is no " +
    "source health to state. A source that is configured but has never been " +
    "expected to report has no health state at all.",
};

export function deriveSiteDetailView(site: SiteDetailReadModel): SiteDetailView {
  return {
    ...deriveSiteView(site),
    timezone: site.timezone,
    foundationVersion: `${site.foundation.version}`,
    foundationValidFrom: site.foundation.valid_from,
    integrationReadiness: INTEGRATION_READINESS_UNAVAILABLE,
    evidenceAvailability: EVIDENCE_AVAILABILITY_UNAVAILABLE,
    sourceHealth: SOURCE_HEALTH_UNAVAILABLE,
  };
}
