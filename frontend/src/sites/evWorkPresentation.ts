/**
 * W5-04 V2a (`.agent/W5-04-build-spec.md` "Mock element, table cells and copy ledger", "EV producer, UI and registry";
 * readiness rulings 14, 19, 20, 44-46): the EV charging Site Work words. No fetches; `domainActionClient.ts` owns the
 * reads. Cold literals stay in `coldWorkPresentation.ts` (ruling 47 moves shared literals only in V4a).
 */

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
 * Ruling 46 / R113: the EV Action detail route is not mounted until V4a, so the EV Action code is plain text. MOCK
 * DEVIATION (D1) R113 (temporary; V4a closes it with the selected `links.action` href).
 */
export const EV_ACTION_LINK_LIVE = false;

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
