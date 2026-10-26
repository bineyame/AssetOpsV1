/**
 * W5-02 K2a ("Shared Site UI and mock slots", "Mock element and literal ledger", U2, U3, P-K2a-41/43): the cold-chain
 * Work and domain Action words. No fetches; `domainActionClient.ts` owns the reads. A mini-grid Site never reads these.
 */
import type { DomainActionPresentation } from "./DomainActionVerification";
import type { DomainStatus } from "./domainActionClient";

/** The v69 `cold-work` panel title. */
export const COLD_WORK_PANEL_TITLE = "Actions at this site";
export const COLD_WORK_COLUMNS = ["Action", "Source", "Owner", "Due", "State", "Success criterion"] as const;

// MOCK DEVIATION (D1) R02 (spec M4): the mock strip reads "Same records and states as the global Actions list" with
// "Manage in Actions →"; the global Actions root reads battery Actions only, so the strip states the cold-only scope
// and the plain gap instead of a link to a list that omits these rows.
export const COLD_WORK_STRIP_DETAIL = "Cold-chain Actions recorded at this site";
export const COLD_WORK_GLOBAL_GAP = "Global Actions does not include cold-chain Actions yet.";

// MOCK DEVIATION (D4) R67 (spec M1/P-K2a-41): the mock's "Due dates are not yet set in this example" describes its
// fixture; the subtitle appears only when the full selected set has no due date (`all_due_dates_unset`).
export const COLD_WORK_DUE_UNSET = "Due dates are not yet set";

/** post-W6 W5-cold R338 (B14-09; guide §3): the empty copy names the selected window, not "yet". */
export const COLD_WORK_EMPTY = ["No actions at this site", "No Action was raised here in the selected window."] as const;

export const COLD_WORK_LOADING = "Loading the site's Actions.";
export const COLD_ACTION_LOADING = "Loading the cold Action declaration.";
export const COLD_WORK_UNAVAILABLE = "Cold work unavailable";
export const COLD_WORK_RETRY = "Retry";

export const COLD_OWNER_MISSING = "Not assigned";
export const COLD_DUE_MISSING = "Not set";
export const COLD_CRITERION_MISSING = "No success criterion declared";
export const COLD_STATE_OPEN = "Open";

/**
 * P-K2a-40 / K2 ruling 9: the cold Work page subtitle, always (no Site subtitle field exists; never Foundation
 * `summary`). MOCK DEVIATION (D4) R90: the mock's site-specific subtitle is illustrative configuration copy.
 */
export const COLD_WORK_SUBTITLE_FALLBACK = "Cold-room operations at this site.";

/** U2: the domain Action page (v69 `cold-action`) PageHeader subtitle and state copy. */
export const COLD_ACTION_SUBTITLE = "Has backup service been restored after the inspection?";
export const COLD_ACTION_NOT_FOUND = "Action was not found at this site.";
export const COLD_ACTION_NOTICE = "Completed inspection does not establish successful service restoration.";

/** W5-02c K4a ruling 4 (moved here by W5-04 V4a, ruling 47): the v69 `cold-action` criteria panel words. */
export const COLD_CRITERIA_TITLE = "Declared outcome criteria";
export const COLD_CRITERIA_COLUMNS = ["Criterion", "Required evidence", "Current result"] as const;
/** Build spec "Empty intent": the criteria panel keeps its heading and omits its table. */
export const COLD_INTENT_MISSING = "No outcome criteria have been declared for this Action.";

/** Build spec "Shared Site UI": the three stored initial result labels. */
export const COLD_RESULT_LABELS: Record<string, string> = {
  NOT_TESTED: "Not tested",
  NOT_ESTABLISHED: "Not established",
  PENDING: "Pending",
};

/** U4: text longer than this previews at two lines with the full text in a "Read full text" disclosure. */
export const LONG_TEXT_THRESHOLD = 80;
export const READ_FULL_TEXT = "Read full text";

/** post-W6 W5-cold R334 (B14-03; guide §4 local plural, as `evActionCount`): `1 action`, otherwise `{n} actions`. */
export function coldActionCount(count: number): string {
  return count === 1 ? "1 action" : `${count} actions`;
}

/** `Show all {N} Actions`: the current page's row count past the fold. */
export function coldShowAll(rows: number): string {
  return `Show all ${rows} Actions`;
}

/** `2026-10-20 14:05 UTC`, with the explicit `UTC` suffix. */
export function coldUtcText(instant: string): string {
  const date = new Date(instant);
  if (Number.isNaN(date.getTime())) return instant;
  return `${date.toISOString().slice(0, 16).replace("T", " ")} UTC`;
}

/** A due date as `YYYY-MM-DD` in UTC, or `Not set`. */
export function coldDueText(due: string | null): string {
  if (due === null) return COLD_DUE_MISSING;
  const date = new Date(due);
  return Number.isNaN(date.getTime()) ? due : date.toISOString().slice(0, 10);
}

/** Spec "Status/notice per currentness": the notice under the strip, or none for `CURRENT`. */
export function coldCurrentnessNotice(status: DomainStatus, knownAt: string): string | null {
  switch (status) {
    case "CURRENT":
      return null;
    case "HISTORICAL":
      return `Read as of ${coldUtcText(knownAt)}. Later work may differ.`;
    case "PENDING_RECOMPUTE":
      return "Linked evidence is being reassessed. The work record remains recorded.";
    case "STALE_SOURCE":
      return "Linked evidence source is out of date. The work record remains recorded.";
    default:
      return "No selected source for linked evidence. The work record remains recorded.";
  }
}

/**
 * K2 ruling 16: Historical and Unknown use the blue info tone; Pending recompute and Stale source use amber.
 * MOCK DEVIATION (D2) R91: the selected-state notice between strip and panel is a ruled live-selection improvement.
 */
export function coldCurrentnessTone(status: DomainStatus): "blue" | "amber" {
  return status === "PENDING_RECOMPUTE" || status === "STALE_SOURCE" ? "amber" : "blue";
}

export function isLongText(text: string): boolean {
  return Array.from(text).length > LONG_TEXT_THRESHOLD;
}

/**
 * post-W6 W5-cold B15-04 (cites R322; W4 Q10 exact-code taxonomy, W5 rulings 2): the cold Action refusal by exact code.
 * Never the raw server message, cutoff or Site code. Superseded in part by the final-fix M2 map below.
 */
export const COLD_ACTION_REFUSAL_COPY = {
  invalidKnownAt: "Choose a valid evidence cutoff.",
  forbidden: "You do not have access to this site.",
  unavailable: "Cold work is unavailable right now. Try again.",
  changed: "The Action changed while it was being read.",
  other: "The Action could not be read.",
} as const;
/** post-W6 final-fix M2: the one recoverable-read button label of the shared Action shell, cold and EV. */
export const COLD_WORK_RELOAD = "Reload";

/**
 * post-W6 final-fix M2: mirrors `evActionRefusal` with the cold noun. By code and status, never the raw server text:
 * `INVALID_KNOWN_AT` names the cutoff, 403 is access, 503 and an unreached server are the recoverable unavailable state,
 * 409 is a changed Action; Reload only where a retry could succeed (503, unreached, 409).
 */
export function coldActionRefusal(refusal: { http: number | null; code: string | null; message: string }): { message: string; retry: boolean } {
  if (refusal.code === "INVALID_KNOWN_AT") return { message: COLD_ACTION_REFUSAL_COPY.invalidKnownAt, retry: false };
  if (refusal.http === null || refusal.http === 503) return { message: COLD_ACTION_REFUSAL_COPY.unavailable, retry: true };
  if (refusal.http === 403) return { message: COLD_ACTION_REFUSAL_COPY.forbidden, retry: false };
  if (refusal.http === 409) return { message: COLD_ACTION_REFUSAL_COPY.changed, retry: true };
  return { message: COLD_ACTION_REFUSAL_COPY.other, retry: false };
}

/**
 * W5-04 V4a (readiness rulings 15, 41, 47): the cold domain Action detail presentation (v69 `cold-action`,
 * `frontend/mockups/v69/index.html:742-746`), with the K4 literals unchanged so the cold output stays byte-identical:
 * `{owner} · {shortName} · {Finding label}` status (ruling 9), the `Finding version` disclosure, the Related activity
 * panel and only the selected `known_at` carried by the detail's own links.
 */
export const COLD_ACTION_PRESENTATION: DomainActionPresentation = {
  subtitle: COLD_ACTION_SUBTITLE,
  stateOpen: COLD_STATE_OPEN,
  ownerMissing: COLD_OWNER_MISSING,
  statusTail: ({ siteName, siteShort, finding }) => `${siteShort || siteName} · ${finding}`,
  revisionDisclosure: true,
  notice: coldCurrentnessNotice,
  tone: coldCurrentnessTone,
  loading: COLD_ACTION_LOADING,
  notFound: COLD_ACTION_NOT_FOUND,
  unavailable: COLD_WORK_UNAVAILABLE,
  retry: COLD_WORK_RETRY,
  closingNotice: COLD_ACTION_NOTICE,
  windowQuery: false,
  refusal: coldActionRefusal,
  reloadLabel: COLD_WORK_RELOAD,
  technicalDetail: true,
  panel: {
    criteriaTitle: COLD_CRITERIA_TITLE,
    columns: COLD_CRITERIA_COLUMNS,
    intentMissing: COLD_INTENT_MISSING,
    resultLabels: COLD_RESULT_LABELS,
    related: true,
  },
};
