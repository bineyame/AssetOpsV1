/**
 * W5-04 V2a (`.agent/W5-04-build-spec.md` "Mock element, table cells and copy ledger", "EV producer, UI and registry";
 * readiness rulings 14, 19, 20, 44-46): the EV charging Site Work words. No fetches; `domainActionClient.ts` owns the
 * reads. Cold literals stay in `coldWorkPresentation.ts` (ruling 47 moves shared literals only in V4a).
 */
import { coldCurrentnessNotice, coldCurrentnessTone } from "./coldWorkPresentation";
import type { DomainIndexScope } from "./domainActionClient";
import type { DomainActionPresentation } from "./DomainActionVerification";

/** The v69 `ev-work` panel title (`index.html:340-343`, `siteWorkScreen`). */
export const EV_WORK_PANEL_TITLE = "Actions at this site";

// MOCK DEVIATION (D1) R04 (spec E4): the mock strip reads "Same records and states as the global Actions list" with
// "Manage in Actions →"; W3 global Actions excludes EV domain roots, so the strip states the EV-only scope and the plain
// gap instead of a link to a list that omits these rows.
export const EV_WORK_STRIP_DETAIL = "EV Actions recorded at this site";
export const EV_WORK_GLOBAL_GAP = "Global Actions does not include EV Actions yet.";

// MOCK DEVIATION (D4) R76 (pre-flight 25): the mock's "Due dates are not yet set in this example" describes its
// fixture; the subtitle appears only when the full selected set has no due date (`all_due_dates_unset`).
export const EV_WORK_DUE_UNSET = "Due dates are not yet set";

/** Pre-flight 27: the exact mock successful zero (`WORK_EMPTY.Actions`); no deviation. */
export const EV_WORK_EMPTY = ["No actions at this site", "No accepted recommendation or evidence request has been raised here yet."] as const;

export const EV_WORK_LOADING = "Loading the site's Actions.";
export const EV_WORK_UNAVAILABLE = "EV work unavailable";
export const EV_WORK_RETRY = "Retry";

export const EV_OWNER_MISSING = "Not assigned";
export const EV_DUE_MISSING = "Not set";
export const EV_CRITERION_MISSING = "No success criterion declared";
export const EV_STATE_OPEN = "Open";

/**
 * Ruling 20 / pre-flight 32: the EV Work page subtitle, always (the Site read has no subtitle; never a synthesized
 * connector count or power limit). MOCK DEVIATION (D4) R78: the mock `SITES.ev` subtitle is illustrative configuration.
 */
export const EV_WORK_SUBTITLE_FALLBACK = "EV charging operations at this site.";

/**
 * Ruling 46 / R113: the one switch for the EV Action code. V2a/V3a kept it plain text while the EV detail route was
 * unmounted; W5-04 V4a mounts that route and turns the selected `links.action` href live, closing MOCK DEVIATION (D1)
 * R113.
 */
export const EV_ACTION_LINK_LIVE = true;

/**
 * Readiness rulings 67 and 71: the EV Action detail address from the server `links.action` pathname plus the page's
 * selected `from`, `to` and explicitly selected `known_at` (the detail keeps them on its own links, ruling 14). Used by
 * the EV Work Action row and both EV case-row `UTC and IDs` links; never carries a list cursor or a server query.
 */
export function evActionHref(serverHref: string, scope: Pick<DomainIndexScope, "from" | "to" | "knownAt">): string {
  const [path] = serverHref.split("?");
  const query = new URLSearchParams({ from: scope.from, to: scope.to });
  if (scope.knownAt) query.set("known_at", scope.knownAt);
  return `${path}?${query.toString()}`;
}

/**
 * Pre-flight 24 / R75: the selected Finding revision cannot be opened at its exact revision (the EV Finding frame
 * ignores `revision_id`); the `Finding version` disclosure says so beside the revision ID.
 */
export const EV_SOURCE_FINDING_UNAVAILABLE = "The selected Finding revision cannot be opened here yet.";

/** Ruling 19 / MOCK DEVIATION (D2) R79: `1 action`, otherwise `{n} actions` (the mock's `1 actions` is corrected). */
export function evActionCount(count: number): string {
  return count === 1 ? "1 action" : `${count} actions`;
}

/** `Show all {N} Actions`: the current page's row count past the four-row fold (R108). */
export function evShowAll(rows: number): string {
  return `Show all ${rows} Actions`;
}

/** W5-04 V4a: the v69 `ev-action` page words (`frontend/mockups/v69/index.html:710-713`; build spec ledger `ev-action`). */
export const EV_ACTION_SUBTITLE = "What would establish successful service restoration?";
/** Readiness ruling 16: the untitled state panel's loading and 404 sentences. */
export const EV_ACTION_LOADING = "Loading the EV Action declaration.";
export const EV_ACTION_NOT_FOUND = "Action was not found at this site.";
export const EV_ACTION_NOTICE = "A completed investigation or diagnostic reset would not establish a verified outcome.";
/** Readiness ruling 15: the sole loaded mock panel and its columns. */
export const EV_PLAN_TITLE = "Declared verification plan";
export const EV_PLAN_COLUMNS = ["Criterion", "Required evidence", "Current result"] as const;
/** Build spec "EV closure contract": the plan panel keeps its heading and omits its table for a missing intent. */
export const EV_INTENT_MISSING = "No verification criteria have been declared for this Action.";
/** Pre-flight 45: the three EV result cells are plain `Pending` text (`work/domain_action.py` EV initial results). */
export const EV_RESULT_LABELS: Record<string, string> = { PENDING: "Pending" };

/**
 * W5-04 V4a (readiness rulings 15, 16, 40, 41; pre-flight 44-46): the EV domain Action detail presentation. The status
 * is `{owner ?? 'Not assigned'} · {full selected Site display_name}` with no Finding version disclosure; the sole
 * `Declared verification plan` panel has no Related activity panel or control; the detail's own links keep the
 * selected `from,to,known_at` (ruling 14) and there is no Window control. MOCK DEVIATION (D2) R80/R104 reuse the cold
 * currentness notice and tone; (D2) R109 wraps the full title/owner; (D2) R110 is the untitled non-loaded panel;
 * (D4) R111 is the stored Site name.
 */
export const EV_ACTION_PRESENTATION: DomainActionPresentation = {
  subtitle: EV_ACTION_SUBTITLE,
  stateOpen: EV_STATE_OPEN,
  ownerMissing: EV_OWNER_MISSING,
  statusTail: ({ siteName }) => siteName,
  revisionDisclosure: false,
  notice: coldCurrentnessNotice,
  tone: coldCurrentnessTone,
  loading: EV_ACTION_LOADING,
  notFound: EV_ACTION_NOT_FOUND,
  unavailable: EV_WORK_UNAVAILABLE,
  retry: EV_WORK_RETRY,
  closingNotice: EV_ACTION_NOTICE,
  windowQuery: true,
  panel: {
    criteriaTitle: EV_PLAN_TITLE,
    columns: EV_PLAN_COLUMNS,
    intentMissing: EV_INTENT_MISSING,
    resultLabels: EV_RESULT_LABELS,
    related: false,
  },
};
