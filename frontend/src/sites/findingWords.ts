/**
 * Plain words for the durable Finding read (S4-01 phase 3). The default view
 * names each state in client language
 * (D-2026-10-04-plain-language-analysis-views); stored codes stay on `data-`
 * attributes and appear verbatim only in the Technical detail view.
 */
import { currentnessWords, type ProductWords } from "../ui";
import { OUTCOME_WORDS } from "./findingPresentation";
import type { FindingDetailBody, Lifecycle, RevisionSummary, UndecidedCause } from "./findingClient";

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

/**
 * W1-UX-02: the Finding's currentness in the shared product words
 * (`currentnessWords` in `../ui`, D-2026-10-16-w1-ux). Cross-screen states
 * (CURRENT, STALE, PENDING, FAILED, NOT_ASSESSED, ...) come from the shared
 * map; a non-current one adds that what is shown is the last recorded version.
 * Finding-only states keep local `ProductWords` here. An unknown code gets the
 * shared non-positive fallback. Only CURRENT is positive.
 */
const LAST_RECORDED = " What is shown is the last recorded version.";

const FINDING_ONLY: Readonly<Record<string, Omit<ProductWords, "code" | "unrecognised">>> = {
  FINDING_MATCH_PENDING: {
    label: "Being compared with a newer assessment",
    sentence:
      "A newer assessment of these days is waiting to be compared with this Finding. What is shown is the last " +
      "recorded version; it is not current.",
    next: "Look again after the comparison is recorded.",
    tone: "waiting",
  },
  SUPERSEDED_BY_LATER_REVISION: {
    ...sharedCurrentness("HISTORICAL"),
  },
  SOURCE_CLOSED: {
    label: "For the record only",
    sentence:
      "This site's assessments are not released for use yet, so this is kept for the record and is not a current " +
      "result.",
    tone: "neutral",
  },
  MERGED_INTO_CANONICAL: {
    label: "Joined into an earlier Finding",
    sentence: "The earlier Finding carries the current review; this Finding's own versions are kept for the record.",
    tone: "neutral",
  },
  /** The Evidence and History reads carry no currentness; they only know the version is the latest when read. */
  LATEST_AT_READ: {
    label: "Latest recorded version when read",
    sentence:
      "This is the latest version recorded when the page was read. Whether it is up to date is shown on the " +
      "Finding's own page.",
    tone: "neutral",
  },
  LATEST_PINNED: {
    label: "Latest recorded version, opened by its exact reference",
    sentence: "This exact version is the latest one recorded. Whether it is up to date is shown on the Finding's own page.",
    tone: "neutral",
  },
};

function sharedCurrentness(code: string): Omit<ProductWords, "code" | "unrecognised"> {
  const words = currentnessWords(code);
  return { label: words.label, sentence: words.sentence, next: words.next, tone: words.tone };
}

/** Plain product words for a Finding currentness code; `attention` is true for anything but CURRENT. */
export function findingCurrentnessWords(state: string | null | undefined): ProductWords & { attention: boolean } {
  const code = state ?? null;
  if (code !== null && Object.prototype.hasOwnProperty.call(FINDING_ONLY, code)) {
    return { ...FINDING_ONLY[code], code, unrecognised: false, attention: true };
  }
  const shared = currentnessWords(code);
  if (shared.tone === "positive") {
    return { ...shared, attention: false };
  }
  return {
    ...shared,
    sentence: shared.unrecognised ? shared.sentence : `${shared.sentence}${LAST_RECORDED}`,
    attention: true,
  };
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
 * Why a Not confirmed version could not decide: the backend's plain cause, classified from the cited assessment
 * with the same rule the assessment uses for its own record gaps. Never assumes missing records, never echoes
 * assessment wording (that stays in Analysis).
 */
export function unconfirmedCause(cause: UndecidedCause | null | undefined): string {
  return cause?.sentence ?? "Why it could not decide is not available in this read.";
}

/** Where a record's data came from, in client words (the recorded mode stays on `data-` attributes). */
export function sourceModeWords(mode: string): string {
  return mode === "SIMULATED" ? "Demonstration data" : mode === "LIVE" ? "Live data" : "Data of unstated origin";
}
