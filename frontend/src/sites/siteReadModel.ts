/**
 * The Site read model.
 *
 * One definition, here, for both shells. Where the operator shell and the
 * Simulator Lab both present a Site they present it from this substrate: one
 * read model, one view model, one set of presentation components. Neither
 * shell may declare a Site read-model type of its own, because two read models
 * with a translation layer between them is exactly the drift this directory
 * exists to prevent, and by the time anyone notices, both have users.
 *
 * `frontend/src/sites/**` is a leaf. It imports no shell code, no simulator
 * code, and no feature flag, and nothing here takes a shell, mode, variant, or
 * `isLab` discriminant. A branch inside the shared core is a fork with extra
 * steps and its branches drift independently.
 *
 * The shape mirrors the API, and the API keeps the provenance-and-status
 * concepts separate on purpose. `origin` is about the configuration document.
 * `source.mode` is about where evidence comes from. `lifecycle_status` is
 * about the site's own life. `template` is provenance about which template the
 * foundation was copied from. There is no `created_in_lab` or
 * `is_simulator_site` field, because which shell created a site is not a
 * property of the site.
 *
 * There is no evidence-derived field at all: no last-data timestamp, no source
 * health, no evidence availability, no analytics. Each arrives with the
 * evidence that fills it.
 */

export interface SiteLocationReadModel {
  country: string;
  locality: string;
}

export interface SiteTemplateProvenanceReadModel {
  template_id: string;
  template_version: number;
}

export interface SiteSourceReadModel {
  mode: string;
}

/** One configured site, as the Sites index reads it. */
export interface SiteSummary {
  site_id: string;
  display_name: string;
  site_type: string;
  location: SiteLocationReadModel;
  timezone: string;
  lifecycle_status: string;
  origin: string;
  source: SiteSourceReadModel;
  template: SiteTemplateProvenanceReadModel | null;
}

/**
 * "No sites are configured" and "the site store could not be read" are
 * different facts, so they are different states. Neither is allowed to degrade
 * into the other: an index that says nothing is configured when it simply
 * could not look is making a claim it cannot back.
 */
export type SiteListResult =
  | { status: "loaded"; sites: SiteSummary[] }
  | { status: "unavailable" };

/**
 * Foundation metadata on a site record.
 *
 * The version and the start of the validity interval only. This is metadata
 * about the configuration document, not the configuration itself: the
 * foundation summary, the components, and later topology, devices, signal
 * mappings and control assumptions belong to the read-only Site Configuration
 * surface and arrive with it. Declaring a field here before a screen renders
 * it would fix a shape nothing has proved.
 */
export interface SiteFoundationReadModel {
  version: number;
  valid_from: string;
}

/**
 * One configured site, as a site page reads it.
 *
 * Everything the Sites index reads, plus foundation metadata. There is still
 * no evidence-derived field of any kind: no last-data timestamp, no source
 * health, no evidence availability, no analytics. A configuration-only site
 * has none of those, and a field carrying a zero or a plausible default would
 * be a claim the product cannot back.
 */
export interface SiteDetailReadModel extends SiteSummary {
  foundation: SiteFoundationReadModel;
}

/**
 * Three outcomes, and none may degrade into another.
 *
 * "This site is not configured", "the store could not be read", and "here is
 * the site" are different facts. An unknown site is `not_found`, which a page
 * states explicitly; it is never rendered as a site with empty fields, which
 * would claim the product knows a site it does not know.
 */
export type SiteDetailResult =
  | { status: "loaded"; site: SiteDetailReadModel }
  | { status: "not_found" }
  | { status: "unavailable" };
