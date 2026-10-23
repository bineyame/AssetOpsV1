/**
 * W5-02 K2a ("Shared Site UI and mock slots", "Mock element and literal ledger", U2, U3, P-K2a-41/43): the cold-chain
 * Work and domain Action words. No fetches; `domainActionClient.ts` owns the reads. A mini-grid Site never reads these.
 */
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

export const COLD_WORK_EMPTY = ["No actions at this site", "No accepted recommendation or evidence request has been raised here yet."] as const;

export const COLD_WORK_LOADING = "Loading the site's Actions.";
export const COLD_ACTION_LOADING = "Loading the cold Action declaration.";
export const COLD_WORK_UNAVAILABLE = "Cold work unavailable";
export const COLD_WORK_RETRY = "Retry";

export const COLD_OWNER_MISSING = "Not assigned";
export const COLD_DUE_MISSING = "Not set";
export const COLD_CRITERION_MISSING = "No success criterion declared";
export const COLD_STATE_OPEN = "Open";

/** P-K2a-40: the cold Work page subtitle when the Site has no stored subtitle. */
export const COLD_WORK_SUBTITLE_FALLBACK = "Cold-room operations at this site.";

/** U2: the domain Action page (v69 `cold-action`) PageHeader subtitle and placeholder copy. */
export const COLD_ACTION_SUBTITLE = "Has backup service been restored after the inspection?";
export const COLD_ACTION_PREPARING = "Action details are being prepared.";
export const COLD_ACTION_NOT_FOUND = "Action was not found at this site.";
export const COLD_ACTION_NOTICE = "Completed inspection does not establish successful service restoration.";

/** U4: text longer than this previews at two lines with the full text in a "Read full text" disclosure. */
export const LONG_TEXT_THRESHOLD = 80;
export const READ_FULL_TEXT = "Read full text";

/** `{n} actions`: the mock's literal count noun, kept as `1 actions` for one (U3). */
export function coldActionCount(count: number): string {
  return `${count} actions`;
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

/** The notice tone, following the W4 strip status tones (`siteWorkCases.tsx` `statusWords`). */
export function coldCurrentnessTone(status: DomainStatus): "blue" | "amber" {
  return status === "PENDING_RECOMPUTE" || status === "STALE_SOURCE" ? "amber" : "blue";
}

export function isLongText(text: string): boolean {
  return Array.from(text).length > LONG_TEXT_THRESHOLD;
}
