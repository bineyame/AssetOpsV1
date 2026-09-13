/**
 * Read-only client for the operator Sites API.
 *
 * The Sites index is an operator capability and is never gated, so this client
 * spells an operator path and is built with no reference to the feature flag.
 * It reads. There is no create, edit, save, publish, rename, duplicate, or
 * delete method here, so no screen built on it can offer one; creating a site
 * is a Simulator Lab capability with its own gated client.
 *
 * Failures are returned as named states rather than thrown or swallowed. A
 * response that does not match the expected shape is `unavailable`, not a
 * partially rendered row: a screen must not show half a site and imply the
 * rest is missing from the configuration.
 */

import type {
  SiteDetailReadModel,
  SiteDetailResult,
  SiteListResult,
  SiteSummary,
} from "./siteReadModel";

/** The operator Sites API. Not a simulator path, and never gated. */
export const SITES_API_PATH = "/api/sites";

export interface SiteDirectoryClient {
  listSites(): Promise<SiteListResult>;
}

/**
 * Reading one site by its identity.
 *
 * A second interface rather than a second method on the one above, so that a
 * screen declares which capability it needs and a caller that only lists
 * sites cannot reach a lookup it never uses. Both are satisfied by the one
 * client built below, and both are read-only: there is still no create, edit,
 * save, publish, rename, duplicate, or delete method anywhere in this module.
 *
 * A site is addressed by `site_id` and by nothing else. The display name and
 * the template a site was created from are not identity and never appear in a
 * request path.
 */
export interface SiteDetailClient {
  getSite(siteId: string): Promise<SiteDetailResult>;
}

function isTemplateProvenance(value: unknown): boolean {
  if (value === null) {
    return true;
  }
  if (typeof value !== "object") {
    return false;
  }
  const provenance = value as Record<string, unknown>;
  return (
    typeof provenance.template_id === "string" &&
    typeof provenance.template_version === "number"
  );
}

export function isSiteSummary(value: unknown): value is SiteSummary {
  if (value === null || typeof value !== "object") {
    return false;
  }
  const site = value as Record<string, unknown>;
  const location = site.location as Record<string, unknown> | undefined;
  const source = site.source as Record<string, unknown> | undefined;

  return (
    typeof site.site_id === "string" &&
    typeof site.display_name === "string" &&
    typeof site.site_type === "string" &&
    typeof site.timezone === "string" &&
    typeof site.lifecycle_status === "string" &&
    typeof site.origin === "string" &&
    location !== undefined &&
    typeof location.country === "string" &&
    typeof location.locality === "string" &&
    source !== undefined &&
    typeof source.mode === "string" &&
    isTemplateProvenance(site.template)
  );
}

export function isSiteDetail(value: unknown): value is SiteDetailReadModel {
  if (!isSiteSummary(value)) {
    return false;
  }
  const foundation = (value as unknown as Record<string, unknown>).foundation as
    | Record<string, unknown>
    | undefined;

  return (
    foundation !== undefined &&
    foundation !== null &&
    typeof foundation.version === "number" &&
    typeof foundation.valid_from === "string"
  );
}

export function createSiteDirectoryClient(
  basePath: string = SITES_API_PATH,
): SiteDirectoryClient & SiteDetailClient {
  return {
    async listSites(): Promise<SiteListResult> {
      try {
        const response = await fetch(basePath);
        if (!response.ok) {
          return { status: "unavailable" };
        }
        const body: unknown = await response.json();
        const sites = (body as Record<string, unknown>)?.sites;
        if (!Array.isArray(sites) || !sites.every(isSiteSummary)) {
          return { status: "unavailable" };
        }
        return { status: "loaded", sites };
      } catch {
        return { status: "unavailable" };
      }
    },

    async getSite(siteId: string): Promise<SiteDetailResult> {
      try {
        const response = await fetch(
          `${basePath}/${encodeURIComponent(siteId)}`,
        );
        if (response.status === 404) {
          return { status: "not_found" };
        }
        if (!response.ok) {
          return { status: "unavailable" };
        }
        const body: unknown = await response.json();
        if (!isSiteDetail(body)) {
          return { status: "unavailable" };
        }
        return { status: "loaded", site: body };
      } catch {
        return { status: "unavailable" };
      }
    },
  };
}
