/**
 * The shared product status vocabulary (W1-UX-01, D-2026-10-16-w1-ux).
 *
 * One map from an already-read semantic state to the plain words every W1
 * screen uses for it. It is words only. It reads no store, derives nothing and
 * never decides currentness, outcome, amount, zero, completeness or source: a
 * caller passes the code its own typed read returned, and gets back what that
 * code may honestly say. A code this map does not know gets the neutral
 * fallback, never a guess and never a positive claim. The exact code itself is
 * kept on the returned words (`code`) for the labelled exact-reference
 * disclosure only; it is not part of any default sentence.
 *
 * Domain word maps in `frontend/src/sites/` keep their domain-specific words
 * and delegate their cross-screen states here as each W1 slice migrates them.
 *
 * Tones are reading aids only. `positive` is returned solely for a code that
 * is itself the positive claim the read made (CURRENT, VERIFIED); every other
 * state is `neutral`, `waiting`, `limited` or `problem`.
 */

export type ProductTone = "positive" | "neutral" | "waiting" | "limited" | "problem";

export interface ProductWords {
  /** The short state sentence that leads (a headline or status line). */
  label: string;
  /** One plain sentence: what the state means for the reader. */
  sentence: string;
  /** The next useful step, when one exists. */
  next?: string;
  tone: ProductTone;
  /** The exact code the read returned, for labelled detail only. */
  code: string | null;
  /** True when the code was not in this map. */
  unrecognised: boolean;
}

/** The neutral fallback for a code this map does not know. */
export const UNRECOGNISED_SENTENCE = "We cannot explain the limit from this record.";

function unrecognised(code: string | null): ProductWords {
  return {
    label: "We cannot judge this yet",
    sentence: UNRECOGNISED_SENTENCE,
    next: "The exact record is listed under How this was worked out.",
    tone: "limited",
    code,
    unrecognised: true,
  };
}

type Entry = Omit<ProductWords, "code" | "unrecognised">;

function lookup(table: Readonly<Record<string, Entry>>, code: string | null | undefined): ProductWords {
  const key = code ?? null;
  if (key !== null && Object.prototype.hasOwnProperty.call(table, key)) {
    return { ...table[key], code: key, unrecognised: false };
  }
  return unrecognised(key);
}

// --- Currentness: is this answer using the latest checked readings? --------

const CURRENTNESS: Readonly<Record<string, Entry>> = {
  CURRENT: {
    label: "Using the latest checked readings",
    sentence: "This answer uses the latest readings that have been checked.",
    tone: "positive",
  },
  PENDING_REASSESSMENT: {
    label: "New readings call for another assessment",
    sentence: "Newer readings mean this period should be checked again. Until it is, the earlier answer is not current.",
    next: "Look again after the period has been checked again.",
    tone: "waiting",
  },
  REASSESSMENT_PENDING: {
    label: "New readings call for another assessment",
    sentence: "Newer readings mean this should be checked again. Until it is, the earlier answer is not current.",
    next: "Look again after it has been checked again.",
    tone: "waiting",
  },
  PENDING: {
    label: "Not checked yet",
    sentence: "This period is waiting to be checked. Nothing is concluded about it yet.",
    next: "Look again after the period has been checked.",
    tone: "waiting",
  },
  STALE: {
    label: "This result may miss newer readings",
    sentence: "Readings arrived after this answer was worked out, so it may not reflect them.",
    next: "Treat it as out of date until it is checked again.",
    tone: "limited",
  },
  STALE_PROJECTION: {
    label: "This result may miss newer readings",
    sentence: "Readings arrived after this answer was worked out, so it may not reflect them.",
    next: "Treat it as out of date until it is checked again.",
    tone: "limited",
  },
  FAILED: {
    label: "The latest check could not be completed",
    sentence: "The most recent check of this period did not finish, so no current answer is shown.",
    next: "Look again later; the period will need to be checked again.",
    tone: "problem",
  },
  UNASSESSED: {
    label: "We have not checked this period",
    sentence: "No assessment exists for this period, so nothing is concluded about it.",
    tone: "neutral",
  },
  NOT_ASSESSED: {
    label: "We have not checked this period",
    sentence: "No assessment exists for this period, so nothing is concluded about it.",
    tone: "neutral",
  },
  UNKNOWN: {
    label: "We cannot judge this yet",
    sentence: "The records do not say enough to judge this.",
    tone: "limited",
  },
  HISTORICAL: {
    label: "Earlier version, kept for the record",
    sentence: "This is an earlier version. It is shown as it was, and it is not the current answer.",
    tone: "neutral",
  },
  AUDIT_ONLY: {
    label: "For the record only",
    sentence: "This is kept for the record and is not a current answer.",
    tone: "neutral",
  },
};

/** Plain words for a read's currentness code. */
export function currentnessWords(code: string | null | undefined): ProductWords {
  return lookup(CURRENTNESS, code);
}

// --- Read results: refused, unavailable and proved-empty are different -----

export type ReadResultKind = "refused" | "unavailable" | "not-found" | "proved-empty";

const READ_RESULT: Readonly<Record<ReadResultKind, Entry>> = {
  refused: {
    label: "This cannot be shown to you",
    sentence: "Your access does not include this. It is not empty; it is withheld from this view.",
    next: "Ask a site administrator for access.",
    tone: "limited",
  },
  unavailable: {
    label: "This could not be read right now",
    sentence: "The records could not be read, so nothing is known about this right now. It is not empty.",
    next: "Try again shortly.",
    tone: "problem",
  },
  "not-found": {
    label: "This record was not found",
    sentence: "No record matches this address. Nothing is shown in its place.",
    tone: "neutral",
  },
  "proved-empty": {
    label: "Checked: nothing to report",
    sentence: "This was checked and there is nothing to report for the time shown.",
    tone: "neutral",
  },
};

/** Plain words for how a read ended. Refused and unavailable are never empty. */
export function readResultWords(kind: ReadResultKind): ProductWords {
  return { ...READ_RESULT[kind], code: kind, unrecognised: false };
}

// --- Money: an amount is shown only when the read supplies one --------------

const MONEY: Readonly<Record<string, Entry>> = {
  WITHHELD: {
    label: "No current amount can be shown",
    sentence: "An amount is not shown because the records behind it cannot support a current figure. This is not zero.",
    tone: "limited",
  },
  WITHHELD_GENERATOR_SERIES: {
    label: "No current amount can be shown",
    sentence: "The generator records are not in a proven time order, so no current amount is shown. This is not zero.",
    next: "Look again after the generator records are checked.",
    tone: "limited",
  },
  MIXED_OR_UNKNOWN_SOURCE: {
    label: "No current amount can be shown",
    sentence: "Where the records came from is not established, so no current amount is shown. This is not zero.",
    tone: "limited",
  },
  PENDING_REASSESSMENT: {
    label: "No current amount can be shown",
    sentence: "Newer readings mean this should be checked again, so no current amount is shown yet. This is not zero.",
    tone: "waiting",
  },
  NO_PRICE: {
    label: "No price recorded",
    sentence: "No diesel price is recorded for this time at this site, and no default price is used in its place.",
    next: "Record a site price to see an amount.",
    tone: "neutral",
  },
  UNPRICED: {
    label: "No price recorded",
    sentence: "No single recorded price covers the whole time, so no amount is shown. This is not zero.",
    next: "Record a site price covering the whole time.",
    tone: "neutral",
  },
};

/** Plain words for a money read that does not carry a current amount. */
export function moneyWords(code: string | null | undefined): ProductWords {
  return lookup(MONEY, code);
}

// --- Trial outcomes: keyed on (outcome, reason, source class) ---------------

export const REASON_GUARDRAIL_FAIL = "GUARDRAIL_FAIL";

/** Source classes that are demonstration or generated, never field readings. */
const DEMONSTRATION_SOURCES: Readonly<Record<string, string>> = {
  AUTHORED_DEMONSTRATION: "Prepared example data, not field readings",
  REGISTERED_SIMULATION: "Generated test data, not field readings",
  SIMULATED: "Demonstration data, not field readings",
};

const FIELD_SOURCES: Readonly<Record<string, string>> = {
  LIVE: "Field readings",
};

export interface SourceQualification {
  /** The plain source qualification, always shown beside the outcome. */
  label: string;
  /** True for authored, generated or demonstration sources. */
  demonstration: boolean;
  /** True when the source is not established or not recognised. */
  unestablished: boolean;
}

/** Plain qualification of where an outcome's readings came from. */
export function sourceQualification(sourceClass: string | null | undefined): SourceQualification {
  const key = sourceClass ?? "";
  if (Object.prototype.hasOwnProperty.call(DEMONSTRATION_SOURCES, key)) {
    return { label: DEMONSTRATION_SOURCES[key], demonstration: true, unestablished: false };
  }
  if (Object.prototype.hasOwnProperty.call(FIELD_SOURCES, key)) {
    return { label: FIELD_SOURCES[key], demonstration: false, unestablished: false };
  }
  return { label: "Where these readings came from is not established", demonstration: false, unestablished: true };
}

export const DEMONSTRATION_OUTCOME_NOTE =
  "This is a policy trial on demonstration data: it shows no savings or realized benefit.";

export interface OutcomeWords extends ProductWords {
  source: SourceQualification;
  /** Set for a demonstration source: the policy-trial, no-benefit note. */
  demonstrationNote: string | null;
  /** True when the reader must see the failed limit beside the outcome. */
  showsFailedLimit: boolean;
  /** True when known failures must stay visible beside the outcome. */
  showsKnownFailures: boolean;
}

const OUTCOMES: Readonly<Record<string, Entry>> = {
  VERIFIED: {
    label: "Target met within the sampled limits",
    sentence:
      "The measured target was met, and the reserve and service limits held at every five-minute sample. " +
      "This is not continuous proof of battery charge between samples.",
    tone: "positive",
  },
  INCONCLUSIVE: {
    label: "Could not conclude",
    sentence: "At least one required fact is missing or not comparable, so no verdict is given.",
    next: "Known failures stay listed below.",
    tone: "limited",
  },
  PENDING: {
    label: "No trial outcome yet",
    sentence: "No outcome exists for this trial yet. Waiting is not an outcome.",
    tone: "waiting",
  },
  REASSESSMENT_PENDING: {
    label: "Earlier outcome withdrawn; being checked again",
    sentence: "New readings or a changed basis withdrew the earlier outcome. It stays readable but is not current.",
    tone: "waiting",
  },
};

const GUARDRAIL_FAIL_ENTRY: Entry = {
  label: "Trial missed a safety or service limit",
  sentence: "A measured reserve or service limit failed during the trial, so the outcome is recorded as not effective.",
  tone: "problem",
};

const TARGET_MISS_ENTRY: Entry = {
  label: "Target not met",
  sentence: "Every measured limit held, but generator time did not fall by the agreed target.",
  tone: "problem",
};

/**
 * Plain words for a trial outcome. The verdict is keyed on the outcome, its
 * reasons and its source class together: an ineffective trial with a measured
 * reserve or service failure is never worded as a plain target miss, and a
 * demonstration source always carries the policy-trial note.
 */
export function outcomeWords(
  outcome: string | null | undefined,
  reasons: readonly string[],
  sourceClass: string | null | undefined,
): OutcomeWords {
  const source = sourceQualification(sourceClass);
  const guardrailFail = reasons.some((r) => r === REASON_GUARDRAIL_FAIL || r.startsWith(`${REASON_GUARDRAIL_FAIL}:`));
  let words: ProductWords;
  if (outcome === "INEFFECTIVE") {
    words = { ...(guardrailFail ? GUARDRAIL_FAIL_ENTRY : TARGET_MISS_ENTRY), code: outcome, unrecognised: false };
  } else {
    words = lookup(OUTCOMES, outcome);
  }
  // A positive verdict on an unestablished source is not shown as positive.
  const tone: ProductTone = words.tone === "positive" && source.unestablished ? "limited" : words.tone;
  return {
    ...words,
    tone,
    source,
    demonstrationNote: source.demonstration && !words.unrecognised ? DEMONSTRATION_OUTCOME_NOTE : null,
    showsFailedLimit: outcome === "INEFFECTIVE" && guardrailFail,
    showsKnownFailures: outcome === "INCONCLUSIVE" || outcome === "INEFFECTIVE",
  };
}

// --- Limitation reasons: cause sentence and next useful step ----------------

const LIMITATIONS: Readonly<Record<string, Entry>> = {
  MISSING_READINGS: {
    label: "Some readings are missing",
    sentence: "Part of the period has no readings, so the answer covers only the time that was recorded.",
    next: "Check that the site's data source is reporting.",
    tone: "limited",
  },
  LATE_EVIDENCE: {
    label: "Readings arrived late",
    sentence: "Some readings arrived after the answer was worked out, so it may not reflect them.",
    next: "Look again after the period has been checked again.",
    tone: "limited",
  },
  SOURCE_NOT_COHERENT: {
    label: "The sources do not agree",
    sentence: "The records come from sources that do not agree, so no firm answer is given.",
    next: "Confirm which data source this site should use.",
    tone: "limited",
  },
  SOURCE_NOT_ESTABLISHED: {
    label: "Where the readings came from is not established",
    sentence: "The origin of the readings is not established, so they are not treated as field readings.",
    next: "Confirm the site's data source.",
    tone: "limited",
  },
  NOT_COMPARABLE: {
    label: "The periods cannot be compared",
    sentence: "The two periods differ too much to compare fairly, so no difference is claimed.",
    tone: "limited",
  },
  NO_PRICE: {
    label: "No price recorded",
    sentence: "No price covers the time, so no amount is worked out.",
    next: "Record a site price covering the time.",
    tone: "neutral",
  },
};

/** Cause sentence and next step for a limitation reason code. */
export function limitationWords(code: string | null | undefined): ProductWords {
  return lookup(LIMITATIONS, code);
}

// --- The plain "as of" bound -------------------------------------------------

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/** A plain instant: "16 Oct 2026, 10:05 UTC", or null when missing or unreadable. */
export function plainTime(instant: string | null | undefined): string | null {
  if (instant === null || instant === undefined || instant.length === 0) return null;
  const date = new Date(instant);
  if (Number.isNaN(date.getTime())) return null;
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${date.getUTCDate()} ${MONTHS[date.getUTCMonth()]} ${date.getUTCFullYear()}, ${pad(date.getUTCHours())}:${pad(date.getUTCMinutes())} UTC`;
}

/**
 * A plain "as of" bound for an instant the read returned: "As of 16 Oct 2026,
 * 10:05 UTC". A missing or unreadable instant says so; it never becomes "now".
 */
export function asOfText(instant: string | null | undefined): string {
  const text = plainTime(instant);
  return text === null ? "As of: time not recorded" : `As of ${text}`;
}
