/**
 * Where the operator shell puts its site surfaces.
 *
 * One module owns the operator site addresses, so the route table, the
 * navigation list, and the link out of a Sites index row cannot disagree about
 * where a site lives. These are operator paths, not simulator paths: they are
 * served in both gate states and nothing here reads the feature flag.
 *
 * A site is addressed by `site_id` and by nothing else. There is deliberately
 * no parameterless site destination here. The T002 `/site-details` frame was a
 * route placeholder from before site identity existed, and a Site Details link
 * that names no site is not a destination; it is removed by the slice that
 * makes the identified route real, and Site Details is reached from a Sites
 * row. `/site-configuration` is still a parameterless placeholder and is
 * removed the same way, by the slice that gives it an identified replacement.
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
