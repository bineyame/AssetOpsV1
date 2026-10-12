/**
 * Plain words for the durable Finding read (S4-01 phase 3). The default view
 * names each state in client language
 * (D-2026-10-04-plain-language-analysis-views); stored codes stay on `data-`
 * attributes and appear verbatim only in the Technical detail view.
 */
import { OUTCOME_WORDS } from "./findingPresentation";
import type { FindingDetailBody, Lifecycle, RevisionSummary } from "./findingClient";

export const LIFECYCLE_WORDS: Record<Lifecycle, { label: string; title: string; sentence: string }> = {
  SUPPORTED: {
    label: "Open",
    title: "Generator support merits review",
    sentence:
      "The assessment supports this: for part of this period the generator stayed on while solar power and the " +
      "battery reported enough capacity to meet site demand.",
  },
  UNCONFIRMED: {
    label: "Not confirmed",
    title: "Generator support review: not confirmed",
    sentence:
      "This assessment of the period cannot confirm the earlier result. This is not a new issue; the earlier " +
      "versions stay available below.",
  },
  NO_LONGER_SUPPORTED: {
    label: "No longer supported",
    title: "Generator support review: no longer supported",
    sentence:
      "A complete later assessment of this period finds no possibly avoidable time. This closes the review only; " +
      "it does not mean the generator was repaired or that money was saved.",
  },
  MERGED: {
    label: "Merged",
    title: "Generator support review: joined into an earlier Finding",
    sentence:
      "Later records showed this was part of one longer period, so it was joined into an earlier Finding, which " +
      "now carries the review. This Finding's own versions stay available.",
  },
};

export const TRANSITION_WORDS: Record<string, string> = {
  OPENED: "Opened",
  SUPPORT_CHANGED: "Period or amount changed",
  MODEL_REEVALUATED: "Re-checked under updated assessment rules",
  SPLIT: "Split into separate Findings",
  MERGED: "Joined with a later Finding",
  MERGED_INTO: "Joined into an earlier Finding",
  UNCONFIRMED: "Could not be confirmed",
  NO_LONGER_SUPPORTED: "No longer supported",
  BASIS_REFRESHED: "Assessment updated; amount unchanged",
  REOPENED: "Supported again",
};

export function transitionWords(code: string): string {
  return TRANSITION_WORDS[code] ?? "Another change is recorded; see Technical detail";
}

/** Whether the selected Finding's displayed state is a live, current open review. */
export const CURRENTNESS_WORDS: Record<string, { label: string; sentence: string; attention: boolean }> = {
  CURRENT: {
    label: "Up to date",
    sentence: "This uses the assessments currently in force for every day it covers.",
    attention: false,
  },
  FINDING_MATCH_PENDING: {
    label: "Being updated",
    sentence:
      "A newer assessment of these days is waiting to be compared with this Finding. What is shown is the last " +
      "recorded version.",
    attention: true,
  },
  STALE: {
    label: "Out of date",
    sentence:
      "Newer records, settings or rules affect these days and they are being reassessed. What is shown is the last " +
      "recorded version.",
    attention: true,
  },
  PENDING: {
    label: "Being assessed",
    sentence: "These days are waiting to be assessed. What is shown is the last recorded version.",
    attention: true,
  },
  FAILED: {
    label: "Reassessment failed",
    sentence:
      "The latest reassessment of these days failed. What is shown is the last recorded version; it is not current.",
    attention: true,
  },
  NOT_ASSESSED: {
    label: "Not assessed",
    sentence: "No current assessment exists for these days. What is shown is the last recorded version.",
    attention: true,
  },
  SUPERSEDED_BY_LATER_REVISION: {
    label: "Earlier version",
    sentence: "You are viewing an earlier version of this Finding. A later version replaces it.",
    attention: true,
  },
  SOURCE_CLOSED: {
    label: "Not released",
    sentence:
      "This site's assessments are not released for use yet, so this is shown as a record only and is not a " +
      "current result.",
    attention: true,
  },
  MERGED_INTO_CANONICAL: {
    label: "Merged",
    sentence: "This Finding was joined into an earlier one, which carries the current review.",
    attention: true,
  },
};

export function currentnessWords(state: string): { label: string; sentence: string; attention: boolean } {
  return (
    CURRENTNESS_WORDS[state] ?? {
      label: "Unknown state",
      sentence: "The state of this Finding is recorded under a code this screen does not know; see Technical detail.",
      attention: true,
    }
  );
}

export function portionWords(code: string): string {
  return OUTCOME_WORDS[code] ?? "Other";
}

export const PORTION_FILL: Record<string, string> = {
  CANDIDATE_AVOIDABLE: "avoidable",
  NECESSARY: "needed",
  INDETERMINATE: "unknown",
};

/** Window states of the bounded `finding-windows/{day}` read, in plain words. */
export const WINDOW_STATE_WORDS: Record<string, string> = {
  NOT_ASSESSED: "No assessment exists for this day, so whether there is a Finding is not known.",
  PENDING: "This day is waiting to be assessed, so whether there is a Finding is not known yet.",
  STALE: "This day is being reassessed, so whether there is a Finding is not settled.",
  FAILED: "The latest reassessment of this day failed, so whether there is a Finding is not settled.",
  NOT_DETERMINABLE: "The assessment of this day could not decide, so this is not a no-Finding result.",
  FINDING_MATCH_PENDING:
    "The newest assessment of this day has not yet been compared with Findings, so this is not a no-Finding result.",
  NO_FINDING: "This day was fully assessed and has no Finding.",
  FINDINGS_RECORDED: "Findings cover this day.",
};

/** The selected revision's position in the Finding's history, in words. */
export function versionWords(body: FindingDetailBody): string {
  const total = body.revision_page.total;
  const no = body.selection.revision_no;
  return body.selection.is_latest ? `Latest version (${no} of ${total})` : `Earlier version ${no} of ${total}`;
}

/**
 * Whether a revision's lifecycle follows a closed review. An UNCONFIRMED or
 * REOPENED revision after NO_LONGER_SUPPORTED must not read as a new active
 * issue (S4-01 phase-1 fix carry).
 */
export function followsClosure(revisions: RevisionSummary[], selected: RevisionSummary): boolean {
  const prior = revisions.filter((r) => r.revision_no < selected.revision_no);
  return prior.some((r) => r.lifecycle === "NO_LONGER_SUPPORTED");
}

/** "2026-10-06" from an ISO instant (UTC). */
export function dayOf(instant: string): string {
  return instant.slice(0, 10);
}

/** Every UTC day from `start` through `end` inclusive (episode bounds). */
export function daysBetween(start: string, end: string): string[] {
  const days: string[] = [];
  const at = new Date(`${dayOf(start)}T00:00:00Z`);
  const last = dayOf(end);
  for (let guard = 0; guard < 400; guard += 1) {
    const day = at.toISOString().slice(0, 10);
    days.push(day);
    if (day >= last) {
      break;
    }
    at.setUTCDate(at.getUTCDate() + 1);
  }
  return days;
}

/** Whole minutes between two ISO instants. */
export function spanMinutes(start: string, end: string): number {
  return Math.max(0, Math.round((Date.parse(end) - Date.parse(start)) / 60000));
}

/**
 * Why a Not confirmed version could not decide, from what the version itself records: a recorded record gap or
 * conflict, else the reason the assessment gave for each undecided portion. Never assumes missing records.
 */
export function unconfirmedCause(
  limitations: string[],
  reasons: { reasons: string[]; missing: string[] }[] | undefined,
): string {
  const list = reasons ?? [];
  const gap = limitations.length > 0 || list.some((r) => r.missing.length > 0);
  if (gap) {
    return "Some records it needs are missing or conflict.";
  }
  const texts = [...new Set(list.flatMap((r) => r.reasons).map((t) => t.replace(/\s*\(Foundation revision [^)]*\)/g, "").trim()))]
    .filter((t) => t.length > 0)
    .slice(0, 2);
  if (texts.length > 0) {
    return `No records are missing; the margin could not be decided under the settings now in force. The assessment says: ${texts.join(" ")}`;
  }
  return "No missing or conflicting records are recorded; the reason it could not be decided is under Technical detail.";
}
