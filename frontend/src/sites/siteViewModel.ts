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

import type {
  SiteComponentReadModel,
  SiteDetailReadModel,
  SiteSummary,
} from "./siteReadModel";

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
  /** See `NO_ANALYSIS_IN_WINDOW`. Always that value in M1. */
  lastAnalysed: string;
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

/**
 * What the `Last analysed` column shows while no evidence has been analysed.
 *
 * This is v6.9's own rendering for a site with no data in the selected window,
 * not a placeholder standing in for a timestamp the product will fill in later.
 * The canonical mockup puts real timestamps in this column; those are evidence
 * the product does not have, and reproducing them would be the clearest case of
 * a mockup literal becoming content.
 *
 * It is a constant rather than a literal in the table so that the day evidence
 * exists, there is one place that stops being true.
 */
export const NO_ANALYSIS_IN_WINDOW = "--";

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
    lastAnalysed: NO_ANALYSIS_IN_WINDOW,
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
 * lifecycle status. Three have no field behind them in this build -
 * integration readiness, evidence availability, source health - and each is
 * stated as unavailable with its reason rather than defaulted, zeroed, or
 * derived from one of the other three.
 *
 * Each of those three says what this build records, not what the site has.
 * The record carries no integration field and no source-health field, so a
 * sentence here about how a site is integrated, or about whether its source
 * reports, would be a claim this substrate cannot back for the site in front
 * of it. Source health in particular is not rendered as a health value, and no
 * source-health vocabulary appears here.
 */
export interface SiteDetailView extends SiteView {
  timezone: string;
  foundationVersion: string;
  foundationValidFrom: string;
  /** The summary the foundation document carries, verbatim. */
  foundationSummary: string;
  integrationReadiness: SiteUnavailableFact;
  evidenceAvailability: SiteUnavailableFact;
  sourceHealth: SiteUnavailableFact;
}

/**
 * Integration readiness: a separate concept, with no field behind it.
 *
 * What this states is what the build records, because that is all the record
 * proves. "No integration is configured for this site" would be a claim about
 * the site, and nothing in the record says whether one is: a site registered
 * against a real integration would arrive here with the same fields and be
 * described wrongly by it.
 */
export const INTEGRATION_READINESS_UNAVAILABLE: SiteUnavailableFact = {
  value: "Not recorded",
  reason:
    "This build records no integration readiness for a site, so nothing here " +
    "states whether an integration is configured. Readiness is its own fact: " +
    "it is not lifecycle status, not source mode, and not derived from either.",
};

/** Evidence availability: a statement about evidence, not a measurement. */
export const EVIDENCE_AVAILABILITY_UNAVAILABLE: SiteUnavailableFact = {
  value: "No evidence",
  reason:
    "No evidence has been accepted for this site, so there is nothing to " +
    "show and nothing to analyse. This is a statement about evidence, not a " +
    "reading of zero and not a statement about the site's lifecycle status.",
};

/**
 * Source health: not recorded, because the record carries no health field.
 *
 * Not "not applicable", which would state that this site's source could have
 * no health, and not "no source is expected to report", which would state
 * something about the site's source that the record does not carry. What is
 * true is about the build: it records no source health for any site.
 */
export const SOURCE_HEALTH_UNAVAILABLE: SiteUnavailableFact = {
  value: "Not recorded",
  reason:
    "This build records no source health for a site, and the record carries " +
    "no field that could carry one. Nothing here states whether this site's " +
    "source is reporting, so nothing here is a health value.",
};

export function deriveSiteDetailView(site: SiteDetailReadModel): SiteDetailView {
  return {
    ...deriveSiteView(site),
    timezone: site.timezone,
    foundationVersion: `${site.foundation.version}`,
    foundationValidFrom: site.foundation.valid_from,
    foundationSummary: site.foundation.summary,
    integrationReadiness: INTEGRATION_READINESS_UNAVAILABLE,
    evidenceAvailability: EVIDENCE_AVAILABILITY_UNAVAILABLE,
    sourceHealth: SOURCE_HEALTH_UNAVAILABLE,
  };
}

/**
 * One component a site's foundation declares, as display.
 *
 * The rating is the archetype's declared design rating, copied from the
 * template when the site was created. It is nameplate intent from a document
 * and never a measurement, so it is never rendered beside, or in the
 * vocabulary of, anything a device has reported.
 */
export interface SiteComponentView {
  componentId: string;
  displayName: string;
  componentType: string;
  rating: string;
}

/**
 * What a component with no declared rating shows.
 *
 * Not `0`, and not an empty cell. A component that declares no rating and a
 * component rated at zero are different facts, and the document states only
 * the first.
 */
export const NO_RATING_DECLARED = "No rating declared";

const COMPONENT_TYPE_LABELS: Record<string, string> = {
  PV_ARRAY: "PV array",
  INVERTER: "Inverter",
  BATTERY: "Battery",
  POWER_CONVERSION_SYSTEM: "Power conversion system",
  GENERATOR: "Generator",
  FUEL_TANK: "Fuel tank",
  AC_BUS: "AC bus",
  LOAD: "Load",
  COLD_ROOM: "Cold room",
  METER: "Meter",
};

/**
 * The statement that configuration does not change after a site is created.
 *
 * Written once, here, because it is the load-bearing sentence of this surface:
 * it is what makes the absence of every editing control a stated product
 * position rather than something a user has to infer from an empty toolbar.
 *
 * It says what M1 does and does not do. It does not say "not yet", does not
 * name an editing workflow, and does not describe the present arrangement as
 * temporary, because none of those is a promise this product has made.
 */
export const CONFIGURATION_FIXED_AT_CREATION =
  "Configuration is fixed at creation in M1. A site's foundation is copied " +
  "from its template when the site is created, and AssetOps does not edit a " +
  "site's foundation in this milestone.";

/**
 * What the foundation's validity interval means, stated rather than implied.
 *
 * The interval is half-open and open-ended: it includes the instant it starts
 * and has no recorded end. Rendering a start date alone would leave a reader
 * to guess whether the configuration has since stopped applying.
 */
export const FOUNDATION_VALIDITY_SEMANTICS =
  "The interval is half-open: it includes the instant it starts and has no " +
  "recorded end, because a foundation stays valid until a later version " +
  "supersedes it. This is the validity of one configuration document. It is " +
  "not a configuration history, and this build records no change to a " +
  "foundation.";

/**
 * A part of a site's configuration the M1 foundation cannot carry.
 *
 * These are stated rather than omitted, and the reason does the work. Silence
 * about devices on a screen that presents itself as a site's configuration
 * would read as "this site has no devices". What is true is narrower and is
 * about the document: the M1 foundation schema declares components and nothing
 * below them, so this build has nowhere to put a device, a mapping, or a
 * control assumption, and therefore states none.
 *
 * None of these is a placeholder for a future panel. There is no empty frame,
 * no heading reserved for content that has not landed, and nothing here names
 * a screen the product does not have.
 */
export const DEVICES_NOT_DECLARED: SiteUnavailableFact = {
  value: "Not declared",
  reason:
    "The M1 site foundation declares components and nothing below them, so " +
    "no device is declared for any site in this build. This is a statement " +
    "about what the configuration document can carry, not a statement that " +
    "this site has no devices.",
};

export const SIGNAL_MAPPINGS_NOT_DECLARED: SiteUnavailableFact = {
  value: "Not declared",
  reason:
    "A signal mapping binds a device signal to a canonical signal, so no " +
    "mapping can be declared while no device is. The M1 site foundation " +
    "carries none, and no mapping version is stated for this site.",
};

export const CONTROL_ASSUMPTIONS_NOT_DECLARED: SiteUnavailableFact = {
  value: "Not declared",
  reason:
    "The M1 site foundation declares no control assumptions, so nothing " +
    "here states how this site is expected to be controlled. This is a " +
    "statement about the configuration document, not a statement that this " +
    "site is uncontrolled.",
};

/**
 * What the read-only Site Configuration surface renders for one site.
 *
 * Everything a site page states about identity and provenance, plus the
 * content of the foundation document: its version, what its validity interval
 * means, its summary, and the components it declares.
 *
 * The six provenance-and-status concepts stay six here exactly as they are on
 * the site page, and for the same reason: this screen is a second place they
 * could be collapsed into one another, and one derivation in one view model
 * would be enough to make the two screens disagree about what a site is.
 */
/**
 * One headline number the foundation actually declares.
 *
 * Derived only from components that carry a rating. A component with no
 * declared rating produces no key parameter at all - not a dash, not a zero,
 * not an empty row. The components table already states that component's
 * absence of a rating in words, which is a statement about the document; a
 * blank line in a parameters list would read as a property of the site.
 */
export interface SiteKeyParameterView {
  /** The component the parameter belongs to. */
  label: string;
  /** The declared value with its canonical unit, exactly as the record has it. */
  value: string;
}

export interface SiteConfigurationView extends SiteDetailView {
  foundationSummary: string;
  foundationValiditySemantics: string;
  configurationFixedAtCreation: string;
  components: SiteComponentView[];
  keyParameters: SiteKeyParameterView[];
  devices: SiteUnavailableFact;
  signalMappings: SiteUnavailableFact;
  controlAssumptions: SiteUnavailableFact;
}

export function deriveSiteComponentView(
  component: SiteComponentReadModel,
): SiteComponentView {
  return {
    componentId: component.component_id,
    displayName: component.display_name,
    componentType: label(component.component_type, COMPONENT_TYPE_LABELS),
    rating:
      component.rating === null
        ? NO_RATING_DECLARED
        : `${component.rating.value} ${component.rating.unit}`,
  };
}

export function deriveSiteConfigurationView(
  site: SiteDetailReadModel,
): SiteConfigurationView {
  return {
    ...deriveSiteDetailView(site),
    foundationSummary: site.foundation.summary,
    foundationValiditySemantics: FOUNDATION_VALIDITY_SEMANTICS,
    configurationFixedAtCreation: CONFIGURATION_FIXED_AT_CREATION,
    components: site.foundation.components.map(deriveSiteComponentView),
    // Filtered on the record, not on the rendered string. A component whose
    // rating is absent is dropped here rather than rendered as an absence,
    // because a parameters list is a list of what the foundation declares and
    // an entry that declares nothing does not belong in one.
    keyParameters: site.foundation.components
      .filter((component) => component.rating !== null)
      .map((component) => ({
        label: label(component.component_type, COMPONENT_TYPE_LABELS),
        value: `${component.rating?.value} ${component.rating?.unit}`,
      })),
    devices: DEVICES_NOT_DECLARED,
    signalMappings: SIGNAL_MAPPINGS_NOT_DECLARED,
    controlAssumptions: CONTROL_ASSUMPTIONS_NOT_DECLARED,
  };
}
