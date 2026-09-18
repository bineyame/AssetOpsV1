/**
 * Where the operator shell puts its site surfaces.
 *
 * One module owns the operator site addresses, so the route table, the
 * navigation list, the Site tab row, and the link out of a Sites index row
 * cannot disagree about where a site lives. These are operator paths, not
 * simulator paths: they are served in both gate states and nothing here reads
 * the feature flag.
 *
 * A site is addressed by `site_id` and by nothing else. There is no
 * parameterless site destination here at all. The T002 `/site-details` and
 * `/site-configuration` frames were route placeholders from before site
 * identity existed, and a link that names no site is not a destination. Each
 * was removed by the slice that made its identified route real: Site Details
 * by T007, the Foundation surface by T008. Both are reached from a site, and
 * neither is an operator navigation item, because a navigation item cannot say
 * which site it would open.
 *
 * A site's foundation hangs off that site's address rather than sitting beside
 * it. One site is one subject, and its foundation is an aspect of it, so the
 * address says so.
 *
 * The product name of that surface is Foundation, from v6.9's operator Site
 * tab row and its Foundation content row. T008 built it under the working name
 * Site Configuration and T011A renames it. `configuration` remains the domain
 * word for the document a site is created from - a site's configuration origin
 * is still configuration origin, and configuration is still fixed at creation -
 * but the screen the operator opens is Foundation.
 */

/** The operator Sites index. Not a simulator path, and never gated. */
export const SITES_PATH = "/sites";

/** The route pattern for one site's page. */
export const SITE_DETAIL_ROUTE_PATH = `${SITES_PATH}/:siteId`;

/**
 * The address of one site's page.
 *
 * The identity is encoded rather than interpolated raw. A `site_id` is
 * charset-constrained at the backend port, so nothing awkward can reach this
 * for a configured site; encoding is what keeps a *requested* identity that is
 * not a valid one from changing the shape of the address it is refused at.
 */
export function siteDetailHref(siteId: string): string {
  return `${SITES_PATH}/${encodeURIComponent(siteId)}`;
}

/** The route pattern for one site's Foundation. */
export const SITE_FOUNDATION_ROUTE_PATH = `${SITE_DETAIL_ROUTE_PATH}/foundation`;

/**
 * The address of one site's Foundation.
 *
 * Built from the site's own address, for the same reason it is encoded there:
 * the two can then never disagree about how a site is spelled into a URL.
 */
export function siteFoundationHref(siteId: string): string {
  return `${siteDetailHref(siteId)}/foundation`;
}

/**
 * The address T008 served this surface at, kept working and nothing else.
 *
 * A rename that breaks a bookmark is a rename that costs the person who used
 * the old name, so the old address still resolves. It is a compatibility
 * redirect and not a second product surface: no link, tab, breadcrumb or route
 * inventory offers it, it renders nothing itself, and the only module allowed
 * to name it is the route table that registers the redirect.
 *
 * It is deliberately not built by an href function. There is no caller that
 * should be constructing this address, so there is nothing to construct it
 * with.
 */
export const LEGACY_SITE_CONFIGURATION_ROUTE_PATH = `${SITE_DETAIL_ROUTE_PATH}/configuration`;
