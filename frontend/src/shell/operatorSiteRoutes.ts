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
 * S6-01b: one Foundation change by its stable change ID, a deep route under
 * Foundation that is not a Foundation view (`FOUNDATION_SUBTABS` never lists
 * it). The bare `/foundation/changes` address has its own explicit
 * unavailable state: there is no Site change index in S6-01. Both are static
 * segments, so they rank above `:foundationView` and never reach the view frame.
 */
export const SITE_FOUNDATION_CHANGES_ROUTE_PATH = `${SITE_DETAIL_ROUTE_PATH}/foundation/changes`;
export const SITE_FOUNDATION_CHANGE_ROUTE_PATH = `${SITE_FOUNDATION_CHANGES_ROUTE_PATH}/:changeId`;

export function siteFoundationChangeHref(siteId: string, changeId: string): string {
  return `${siteFoundationHref(siteId)}/changes/${encodeURIComponent(changeId)}`;
}

/**
 * The route pattern for one of the Foundation's other views (S1-03): the
 * Single line diagram (`sld`) and configuration Readiness (`readiness`). The
 * Site model is the Foundation address itself. Which segments are views is
 * owned by `FOUNDATION_SUBTABS`; any other segment is not a view and is
 * refused by the frame, never rendered as a disabled view.
 */
export const SITE_FOUNDATION_VIEW_ROUTE_PATH = `${SITE_DETAIL_ROUTE_PATH}/foundation/:foundationView`;

/**
 * The address of one Foundation view, carrying the selected period and, when
 * one is chosen, the selected part by its stable component ID (V-01a round 2,
 * `D-2026-10-12-v01a-owner-visual-rulings`). The two are independent.
 */
export function siteFoundationViewHref(
  siteId: string,
  segment: string,
  at: string | null,
  component: string | null = null,
): string {
  const base = segment === "" ? siteFoundationHref(siteId) : `${siteFoundationHref(siteId)}/${segment}`;
  const query = new URLSearchParams();
  if (at !== null) query.set("at", at);
  if (component !== null) query.set(FOUNDATION_COMPONENT_PARAM, component);
  const search = query.toString();
  return search === "" ? base : `${base}?${search}`;
}

/** The query key that carries the selected part's component ID. */
export const FOUNDATION_COMPONENT_PARAM = "component";

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
 * S4-01: one durable Finding of a Site (`A-claim-work-routes`). An exact
 * version is `?revision_id=`, the same parameter the API takes, so a reload
 * reopens that stored version.
 */
export const SITE_FINDING_ROUTE_PATH = `${SITE_FINDINGS_ROUTE_PATH}/:findingId`;

export function siteFindingHref(siteId: string, findingId: string, revisionId?: string | null): string {
  const base = `${siteFindingsHref(siteId)}/${encodeURIComponent(findingId)}`;
  return revisionId ? `${base}?revision_id=${encodeURIComponent(revisionId)}` : base;
}

/**
 * S4-02a: Site > Financials. The Overview optionally carries a Finding bridge
 * (`?finding_id=&revision_id=`, the exact FindingRevision); Assumptions takes
 * an exact price version (`?revision_id=`) or a recorded cutoff
 * (`?recorded_at=`), the same parameters the read API takes, so reload and
 * back reopen the same stored selection.
 */
export const SITE_FINANCIALS_ROUTE_PATH = `${SITE_DETAIL_ROUTE_PATH}/financials`;
export const SITE_FINANCIAL_ASSUMPTIONS_ROUTE_PATH = `${SITE_FINANCIALS_ROUTE_PATH}/assumptions`;
/** W4-03 unit 6a: mini Financials > Scenarios; the address carries only the read's own `from`/`to`/`known_at`/`cursor`. */
export const SITE_FINANCIAL_SCENARIOS_ROUTE_PATH = `${SITE_FINANCIALS_ROUTE_PATH}/scenarios`;

export function siteFinancialScenariosHref(siteId: string): string {
  return `${siteDetailHref(siteId)}/financials/scenarios`;
}

export function siteFinancialsHref(
  siteId: string,
  bridge?: { findingId: string; revisionId?: string | null; consequenceRevisionId?: string | null },
): string {
  const base = `${siteDetailHref(siteId)}/financials`;
  if (!bridge) return base;
  const query = new URLSearchParams({ finding_id: bridge.findingId });
  if (bridge.revisionId) query.set("revision_id", bridge.revisionId);
  if (bridge.consequenceRevisionId) query.set("consequence_revision_id", bridge.consequenceRevisionId);
  return `${base}?${query.toString()}`;
}

export function siteFinancialAssumptionsHref(
  siteId: string,
  pin?: { revisionId?: string | null; recordedAt?: string | null; historyAfter?: string | null; historyLimit?: number | null },
): string {
  const base = `${siteDetailHref(siteId)}/financials/assumptions`;
  const query = new URLSearchParams();
  if (pin?.revisionId) query.set("revision_id", pin.revisionId);
  // S4-08: the cutoff string is the server's own, passed through unchanged (review L-R1).
  if (pin?.recordedAt) query.set("recorded_at", pin.recordedAt);
  if (pin?.historyAfter) query.set("history_after", pin.historyAfter);
  if (pin?.historyLimit) query.set("history_limit", String(pin.historyLimit));
  const text = query.toString();
  return text ? `${base}?${text}` : base;
}

/**
 * W2-07: the five EV Site screens of an EV_CHARGING Site (q5 dry-read), each read with the selected
 * `?from=&to=&known_at=`: `/sites/{site}/ev`, `/ev/evidence`, `/ev/evidence/analysis`, `/ev/financials`,
 * `/ev/financial-assumptions`.
 */
export const SITE_EV_ROUTE_PATH = `${SITE_DETAIL_ROUTE_PATH}/ev`;
export const SITE_EV_EVIDENCE_ROUTE_PATH = `${SITE_EV_ROUTE_PATH}/evidence`;
export const SITE_EV_ANALYSIS_ROUTE_PATH = `${SITE_EV_ROUTE_PATH}/evidence/analysis`;
export const SITE_EV_FINANCIALS_ROUTE_PATH = `${SITE_EV_ROUTE_PATH}/financials`;
export const SITE_EV_ASSUMPTIONS_ROUTE_PATH = `${SITE_EV_ROUTE_PATH}/financial-assumptions`;

const SITE_EV_SUFFIX = {
  overview: "",
  evidence: "/evidence",
  analysis: "/evidence/analysis",
  financials: "/financials",
  assumptions: "/financial-assumptions",
};

export function siteEvHref(siteId: string, view: keyof typeof SITE_EV_SUFFIX = "overview"): string {
  return `${siteDetailHref(siteId)}/ev${SITE_EV_SUFFIX[view]}`;
}

/**
 * S4-03: the named child views of the canonical Finding root. Each is
 * `/sites/{site}/findings/{finding}/{view}[?revision_id=]` and keeps the same
 * exact-version parameter. The frame's switch (`SiteFindingFrame`) renders
 * each view from this list (Evidence: phase 2, History: phase 3).
 * S6-01b adds Recommendation (`recommendation:1`), which keeps the same
 * `?revision_id=` so the recommendation is always for an exact version.
 */
export const FINDING_CHILD_VIEWS = ["evidence", "history", "recommendation"] as const;
export type FindingChildView = (typeof FINDING_CHILD_VIEWS)[number];
export const SITE_FINDING_VIEW_ROUTE_PATH = `${SITE_FINDING_ROUTE_PATH}/:findingView`;

export function siteFindingViewHref(
  siteId: string,
  findingId: string,
  view: FindingChildView,
  revisionId?: string | null,
): string {
  const base = `${siteFindingsHref(siteId)}/${encodeURIComponent(findingId)}/${view}`;
  return revisionId ? `${base}?revision_id=${encodeURIComponent(revisionId)}` : base;
}

/**
 * S6-01b: the canonical Site Action root and its child sections. An exact
 * event is `?event_id=`, a server recorded cutoff is `?recorded_at=`, the same
 * parameters the read API takes; the selection is carried into every section
 * so reload and navigation keep it. The `execution` segment is the address
 * only; its label is "Application".
 */
/**
 * S6-03 (`sitework:1#a`): Site > Work > Actions. The creation window and page
 * cursor ride in the query (`?from=&to=&limit=&cursor=`); without a window the
 * page shows a choose-window state and reads nothing.
 */
export const SITE_WORK_ROUTE_PATH = `${SITE_DETAIL_ROUTE_PATH}/work`;

export function siteWorkHref(siteId: string, query?: string): string {
  const base = `${siteDetailHref(siteId)}/work`;
  return query ? `${base}?${query}` : base;
}

/**
 * W4-01 (`sitework-incidents`, `sitework-maintenance`): the Work subrow's
 * Incidents and Maintenance lists. The window, the fixed cutoff and the server
 * cursor ride in the query (`?from=&to=&known_at=&cursor=`); without a window
 * the page reads the seven complete UTC days ending today.
 */
export const SITE_WORK_INCIDENTS_ROUTE_PATH = `${SITE_WORK_ROUTE_PATH}/incidents`;
export const SITE_WORK_MAINTENANCE_ROUTE_PATH = `${SITE_WORK_ROUTE_PATH}/maintenance`;

export function siteWorkIncidentsHref(siteId: string, query?: string): string {
  const base = `${siteDetailHref(siteId)}/work/incidents`;
  return query ? `${base}?${query}` : base;
}

export function siteWorkMaintenanceHref(siteId: string, query?: string): string {
  const base = `${siteDetailHref(siteId)}/work/maintenance`;
  return query ? `${base}?${query}` : base;
}

export const SITE_ACTION_ROUTE_PATH = `${SITE_DETAIL_ROUTE_PATH}/actions/:actionId`;
export const SITE_ACTION_VIEW_ROUTE_PATH = `${SITE_ACTION_ROUTE_PATH}/:actionView`;
export const ACTION_CHILD_VIEWS = ["plan", "execution", "evidence", "verification", "history"] as const;
export type ActionChildView = (typeof ACTION_CHILD_VIEWS)[number];

/**
 * S6-02b: the verification children take `?plan_revision_id=` (an exact
 * frozen plan) and `?outcome_id=` (an exact immutable outcome) beside the
 * S6-01b `event_id` / `recorded_at`. Every selector present is carried into
 * every section link, so an explicit historical selection survives navigation
 * and reload; a conflicting combination is shown as a typed error.
 */
export interface ActionHrefSelector {
  eventId?: string | null;
  recordedAt?: string | null;
  planRevisionId?: string | null;
  outcomeId?: string | null;
}

export function siteActionHref(
  siteId: string,
  actionId: string,
  view: ActionChildView | "overview" = "overview",
  selector?: ActionHrefSelector,
): string {
  const root = `${siteDetailHref(siteId)}/actions/${encodeURIComponent(actionId)}`;
  const base = view === "overview" ? root : `${root}/${view}`;
  const query = new URLSearchParams();
  if (selector?.eventId) query.set("event_id", selector.eventId);
  if (selector?.recordedAt) query.set("recorded_at", selector.recordedAt);
  if (selector?.planRevisionId) query.set("plan_revision_id", selector.planRevisionId);
  if (selector?.outcomeId) query.set("outcome_id", selector.outcomeId);
  const text = query.toString();
  return text ? `${base}?${text}` : base;
}

/**
 * The Site Evidence record inspector opened by one exact accepted evidence ID
 * (the central-ledger inspector reads `record=` as that ID in Analysis). Never
 * a message ID: a message ID can name more than one stored record.
 */
export function siteEvidenceAcceptedRecordHref(siteId: string, evidenceId: string): string {
  return `${siteEvidenceHref(siteId)}?view=analysis&record=${encodeURIComponent(evidenceId)}`;
}

/**
 * The Findings rail root (T028): the global index. A Finding is a first-class
 * object under this root, so opening one from a Site changes the root to the
 * Finding; its claim drawer is a query parameter and never changes it.
 */
export const FINDINGS_PATH = "/findings";
/**
 * W3-01: the estate Finding lens roots and the estate Actions root. They mirror
 * `ESTATE_FINDING_LENS_PATHS` and `ESTATE_ACTIONS_PATH` in `frontend/src/estate/` (a shell test
 * pins the equality) and are registered before the legacy Finding patterns below.
 */
export const FINDINGS_COST_PATH = "/findings/cost";
export const FINDINGS_RISKS_PATH = "/findings/risks";
export const FINDINGS_OPPORTUNITIES_PATH = "/findings/opportunities";
export const ACTIONS_PATH = "/actions";
/**
 * W3-02: the estate Evidence root. It mirrors `ESTATE_EVIDENCE_PATH` in `frontend/src/estate/EstateEvidence.tsx`
 * (a shell test pins the equality) so the navigation-truthfulness guard can resolve the live rail target.
 */
export const EVIDENCE_PATH = "/evidence";
/**
 * W3-02 commit 4: the estate Financials root. It mirrors `ESTATE_FINANCIALS_PATH` in
 * `frontend/src/estate/EstateFinancials.tsx` (a shell test pins the equality) so the navigation-truthfulness guard
 * can resolve the live rail target. Site financial routes are Site-relative suffixes and do not shadow it.
 */
export const FINANCIALS_PATH = "/financials";
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

/**
 * S7-01b Site Health (`health:2#a`): gateway contact, last-reported gateway
 * facts and the battery condition entry, each in its own section. An optional
 * `?gateway=<gateway id>` selects one gateway's detail and survives reload.
 */
export const SITE_HEALTH_ROUTE_PATH = `${SITE_DETAIL_ROUTE_PATH}/health`;

export function siteHealthHref(siteId: string, gatewayId?: string | null): string {
  const base = `${siteDetailHref(siteId)}/health`;
  return gatewayId ? `${base}?gateway=${encodeURIComponent(gatewayId)}` : base;
}

/**
 * S7-01b battery boundary (`asset:3#a`). `/assets` is the Site's battery entry
 * (the configured battery, or "not configured" without an asset ID);
 * `/assets/{asset}` is one configured battery by its asset ID in the effective
 * Site configuration (`D-2026-10-16-w1-remaining-questions` answer 3).
 */
export const SITE_ASSETS_ROUTE_PATH = `${SITE_DETAIL_ROUTE_PATH}/assets`;
export const SITE_ASSET_ROUTE_PATH = `${SITE_ASSETS_ROUTE_PATH}/:assetId`;

export function siteAssetsHref(siteId: string): string {
  return `${siteDetailHref(siteId)}/assets`;
}

export function siteAssetHref(siteId: string, assetId: string): string {
  return `${siteAssetsHref(siteId)}/${encodeURIComponent(assetId)}`;
}
