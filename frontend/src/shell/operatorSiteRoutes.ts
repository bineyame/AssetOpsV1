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
 * The route pattern for one of the Foundation's other views (S1-03): the
 * Single line diagram (`sld`) and configuration Readiness (`readiness`). The
 * Site model is the Foundation address itself. Which segments are views is
 * owned by `FOUNDATION_SUBTABS`; any other segment is not a view and is
 * refused by the frame, never rendered as a disabled view.
 */
export const SITE_FOUNDATION_VIEW_ROUTE_PATH = `${SITE_DETAIL_ROUTE_PATH}/foundation/:foundationView`;

/** The address of one Foundation view, carrying the selected period. */
export function siteFoundationViewHref(siteId: string, segment: string, at: string | null): string {
  const base = segment === "" ? siteFoundationHref(siteId) : `${siteFoundationHref(siteId)}/${segment}`;
  return at === null ? base : `${base}?at=${encodeURIComponent(at)}`;
}

/** The route pattern for one site's Evidence. */
export const SITE_EVIDENCE_ROUTE_PATH = `${SITE_DETAIL_ROUTE_PATH}/evidence`;

/** The address of one site's Evidence, built from the site's own address. */
export function siteEvidenceHref(siteId: string): string {
  return `${siteDetailHref(siteId)}/evidence`;
}

/**
 * The Site > Evidence record inspector for one accepted record (T027 phase 2:
 * Overview evidence links). `signal` is `DEVICE/SIGNAL`, the same value the
 * inspector reads from its own signal rows, so the root does not change.
 */
/** Site Evidence > Analysis with one assessed period's record coverage selected. */
export function siteEvidenceAssessmentHref(siteId: string, assessmentId: string): string {
  return `${siteEvidenceHref(siteId)}?view=analysis&assessment=${encodeURIComponent(assessmentId)}`;
}

export function siteEvidenceRecordHref(
  siteId: string,
  signal: string,
  messageId: string,
): string {
  const [device, ...rest] = signal.split("/");
  const signalParam = `${encodeURIComponent(device)}/${encodeURIComponent(rest.join("/"))}`;
  return `${siteEvidenceHref(siteId)}?signal=${signalParam}&record=${encodeURIComponent(messageId)}`;
}

/** The route patterns for one site's Performance (T028), and one subtab of it. */
export const SITE_PERFORMANCE_ROUTE_PATH = `${SITE_DETAIL_ROUTE_PATH}/performance`;
export const SITE_PERFORMANCE_SUBTAB_ROUTE_PATH = `${SITE_PERFORMANCE_ROUTE_PATH}/:capabilityId`;

/**
 * The address of one site's Performance, optionally at one subtab. A subtab is
 * a backend capability id (`dispatch`), never a profile label.
 */
export function sitePerformanceHref(siteId: string, capabilityId?: string): string {
  const base = `${siteDetailHref(siteId)}/performance`;
  return capabilityId === undefined ? base : `${base}/${encodeURIComponent(capabilityId)}`;
}

/** The route pattern for one site's scoped Findings index (T028). */
export const SITE_FINDINGS_ROUTE_PATH = `${SITE_DETAIL_ROUTE_PATH}/findings`;

export function siteFindingsHref(siteId: string): string {
  return `${siteDetailHref(siteId)}/findings`;
}

/**
 * The Findings rail root (T028): the global index. A Finding is a first-class
 * object under this root, so opening one from a Site changes the root to the
 * Finding; its claim drawer is a query parameter and never changes it.
 */
export const FINDINGS_PATH = "/findings";
export const FINDING_ROUTE_PATH = `${FINDINGS_PATH}/:siteId/:assessmentId`;
export const FINDING_TAB_ROUTE_PATH = `${FINDING_ROUTE_PATH}/:findingTab`;

/**
 * Finding detail tabs rendered at T028 (D-2026-10-04-plain-language-analysis-
 * views adds Analysis); Recommendation and History land at T034.
 */
export type FindingTab = "overview" | "analysis" | "evidence" | "alternatives";

export function findingHref(siteId: string, assessmentId: string, tab: FindingTab = "overview"): string {
  const base = `${FINDINGS_PATH}/${encodeURIComponent(siteId)}/${encodeURIComponent(assessmentId)}`;
  return tab === "overview" ? base : `${base}/${tab}`;
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
