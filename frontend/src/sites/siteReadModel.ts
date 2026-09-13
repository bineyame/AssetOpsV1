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
