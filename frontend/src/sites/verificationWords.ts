/**
 * S6-02b: plain words for the verification read states, outcomes, metrics and
 * evidence problems. The typed values (states, outcomes, reason codes, metric
 * keys) stay on `data-*` attributes and in the "Dig deeper" disclosures; the
 * default reading uses these words (owner presentation direction 2026-10-16).
 *
 * The three interim labels are fixed by `D-2026-10-16-s602-questions`:
 * "Trial missed a safety or service limit" (INEFFECTIVE with a measured
 * GUARDRAIL_FAIL), "Target not met" (INEFFECTIVE, target only) and "Could not
 * conclude" (INCONCLUSIVE). GUARDRAIL_FAIL is a reason, never a fourth outcome.
 */

export const GUARDRAIL_FAIL = "GUARDRAIL_FAIL";
export const TARGET_MISS = "TARGET_MISS";

export const LABEL_GUARDRAIL_FAIL = "Trial missed a safety or service limit";
export const LABEL_TARGET_MISS = "Target not met";
export const LABEL_INCONCLUSIVE = "Could not conclude";

/** The headline for a read state or outcome with its reasons. */
export function stateLabel(state: string, reasons: readonly string[] = []): string {
  switch (state) {
    case "VERIFIED":
      return "Target met within every limit";
    case "INEFFECTIVE":
      return reasons.includes(GUARDRAIL_FAIL) ? LABEL_GUARDRAIL_FAIL : LABEL_TARGET_MISS;
    case "INCONCLUSIVE":
      return LABEL_INCONCLUSIVE;
    case "PENDING":
      return reasons.includes("LATER_WINDOW_OPEN") ? "Waiting for the later window" : "Waiting for evaluation";
    case "REASSESSMENT_PENDING":
      return "Being reassessed";
    case "NO_PLAN":
      return "No verification plan yet";
    default:
      return "State not recognised";
  }
}

/** The recorded outcome, in plain words (the typed value stays in Dig deeper). */
export function outcomeName(outcome: string): string {
  return outcome === "VERIFIED"
    ? "Verified"
    : outcome === "INEFFECTIVE"
      ? "Ineffective"
      : outcome === "INCONCLUSIVE"
        ? "Inconclusive"
        : "Not recognised";
}

/** One sentence under the headline. */
export function stateSentence(state: string, reasons: readonly string[] = []): string {
  switch (state) {
    case "VERIFIED":
      return "The later window met the frozen target and kept every service, reserve and end-of-window limit.";
    case "INEFFECTIVE":
      return reasons.includes(GUARDRAIL_FAIL)
        ? "A measured service or reserve limit failed in the later window. The outcome is recorded as ineffective."
        : "Every limit held, but generator time did not fall by the frozen target. The outcome is recorded as ineffective.";
    case "INCONCLUSIVE":
      return "At least one required fact is missing or not comparable, so no verdict is given. Known failures are listed below.";
    case "PENDING":
      return "No outcome exists for the current plan yet. Pending is a waiting state, not an outcome.";
    case "REASSESSMENT_PENDING":
      return "New evidence or a changed basis withdrew the earlier outcome. It is being reassessed; the earlier outcome stays readable but is not current.";
    case "NO_PLAN":
      return "A verification plan is frozen after the change is applied. Until then nothing can be judged.";
    default:
      return "";
  }
}

export type Tone = "pass" | "fail" | "unknown" | "waiting";

export function stateTone(state: string): Tone {
  return state === "VERIFIED" ? "pass" : state === "INEFFECTIVE" ? "fail" : state === "INCONCLUSIVE" ? "unknown" : "waiting";
}

export function checkWord(state: string): string {
  return state === "PASS" ? "Pass" : state === "FAIL" ? "Fail" : state === "UNKNOWN" ? "Unknown" : "Not recognised";
}

export function checkTone(state: string): Tone {
  return state === "PASS" ? "pass" : state === "FAIL" ? "fail" : "unknown";
}

/** Metric rows of an outcome, by metric key and window. */
export const METRIC_WORDS: Record<string, { name: string; role: string }> = {
  candidate_avoidable_seconds: { name: "Generator time that could have been avoided", role: "Target" },
  target_reduction: { name: "Reduction in avoidable generator time", role: "Target" },
  unserved_critical_energy: { name: "Critical demand not served", role: "Service limit" },
  below_reserve_seconds: { name: "Time below the reserve (checked every five minutes)", role: "Reserve limit" },
  terminal_soc: { name: "Battery charge at the end of the window", role: "Stored-energy limit" },
  feeder_demand_energy_band: { name: "Site demand energy", role: "Window comparability" },
  pv_available_energy_band: { name: "Available solar energy", role: "Window comparability" },
  initial_soc_band: { name: "Battery charge at the start", role: "Window comparability" },
  window_coverage: { name: "Required readings present", role: "Evidence coverage" },
  source_provenance: { name: "Source of the readings", role: "Evidence source" },
};

export function metricName(key: string): string {
  return METRIC_WORDS[key]?.name ?? "Unrecognised measure";
}

export const GUARDRAIL_KEYS = ["unserved_critical_energy", "below_reserve_seconds", "terminal_soc"] as const;

/** A reason code from an outcome or read state, in plain words. */
export function reasonWords(reason: string): string {
  const [code, rest] = reason.split(":", 2);
  switch (code) {
    case "TARGET_AND_GUARDRAILS_PASS":
      return "Target met and every limit held.";
    case GUARDRAIL_FAIL:
      return "A measured service or reserve limit failed.";
    case "GUARDRAIL":
      return `Failed limit: ${metricName(rest ?? "")}.`;
    case TARGET_MISS:
      return "Avoidable generator time did not fall by the target.";
    case "GUARDRAIL_UNKNOWN":
      return `Not known: ${metricName(rest ?? "")}.`;
    case "KNOWN_FAILURE":
      return `Known failure: ${metricName(rest ?? "")}.`;
    case "INCOMPLETE_BASELINE_WINDOW":
      return "The earlier window is missing required readings.";
    case "INCOMPLETE_LATER_WINDOW":
      return "The later window is missing required readings.";
    case "TARGET_UNKNOWN":
      return "Avoidable generator time could not be established for both windows.";
    case "SOURCE_NOT_COHERENT":
      return "The two windows do not come from one coherent source of the same kind.";
    case "NOT_COMPARABLE":
      return "The two windows are not comparable within the frozen bands.";
    case "COMPARABILITY_UNKNOWN":
      return "Whether the two windows are comparable could not be established.";
    case "BINDINGS_NOT_COMPARABLE":
      return "The signal assignments differ between the windows.";
    case "FOUNDATION_CHANGED":
      return "The Site Foundation covering a window changed after the outcome.";
    case "BASELINE_SELECTION_CHANGED":
      return "The earlier window's selected daily assessment changed.";
    case "LATE_EVIDENCE":
      return "A reading for a window was accepted after the outcome was recorded.";
    case "LATER_WINDOW_OPEN":
      return "The later window has not closed yet.";
    case "NOT_EVALUATED":
      return "The later window has closed; the evaluation has not been recorded yet.";
    default:
      if (/^(baseline|later)_days$/.test(code)) return "A selected daily assessment is pending or has moved.";
      if (/^(baseline|later)$/.test(code)) return "A selected daily assessment is pending or has moved.";
      return "Reason given by the server (see Dig deeper).";
  }
}

/** Evidence problems from the window rules, in plain words. */
export const PROBLEM_WORDS: Record<string, string> = {
  GAP: "Gap: no reading covers part of the slot",
  CONFLICT: "Conflicting overlapping readings",
  POINT_ONLY: "Only instant readings; no energy over the slot",
  SPANS_SLOT_BOUNDARY: "A reading crosses the slot boundary",
  NOT_ACCEPTED: "A reading was not accepted for use",
  INVALID_VALUE: "A reading has an unreadable value",
  INVALID_UNIT: "A reading has an unexpected unit",
  INVALID_SPAN: "A reading has no valid time span",
  MISSING_SAMPLE: "Missing battery charge sample",
  MISSING_BINDING: "A required signal has no assignment",
  AMBIGUOUS_BINDING: "A signal is assigned more than once",
  NO_EFFECTIVE_RESERVE: "No reserve setting in effect",
  RESERVE_CHANGED_IN_SLOT: "The reserve changed inside the slot",
  DELIVERED_EXCEEDS_REQUESTED: "Delivered critical power exceeds the request",
  OPEN_BOUND: "An assessment period has an open end",
  INDETERMINATE: "An assessment period could not be classified",
  CONFLICTING_INTERVAL: "Two assessment versions disagree about a period",
  INVALID_SEGMENT: "An assessment period could not be read",
  UNKNOWN_CLASSIFICATION: "An assessment period has an unrecognised classification",
};

export function problemCode(problem: unknown): string {
  if (typeof problem === "string") return problem.split(":", 1)[0];
  if (problem && typeof problem === "object" && typeof (problem as { code?: unknown }).code === "string") {
    return (problem as { code: string }).code;
  }
  return "UNKNOWN";
}

export function problemWords(problem: unknown): string {
  return PROBLEM_WORDS[problemCode(problem)] ?? "Problem reported by the server (see Dig deeper)";
}

/** Cell states of the window slots. */
export function cellWord(state: string): string {
  switch (state) {
    case "COVERED":
    case "KNOWN":
      return "Present";
    case "PARTIAL":
      return "Partial";
    case "MISSING":
      return "Missing";
    case "CONFLICT":
      return "Conflict";
    case "UNKNOWN":
      return "Unknown";
    default:
      return "Not recognised";
  }
}

/** Where a window's readings came from (S4-05 source resolution, per window). */
export function sourceWords(state: string | null | undefined): string {
  switch (state) {
    case "REGISTERED_SIMULATION":
      return "Registered Lab trial data";
    case "AUTHORED_DEMONSTRATION":
      return "Authored test data (test-scoped example)";
    case "MIXED":
      return "Mixed sources";
    case "UNKNOWN":
    case null:
    case undefined:
      return "Source not established";
    default:
      return "Field readings";
  }
}

/** An exact decimal or fraction string ("5/3") to a short decimal. */
export function decimal(text: string | null | undefined, places = 2): string | null {
  if (text === null || text === undefined || text === "") return null;
  const [n, d] = text.split("/");
  const value = d === undefined ? Number(n) : Number(n) / Number(d);
  if (!Number.isFinite(value)) return text;
  const rounded = Number(value.toFixed(places));
  return String(rounded);
}

export function minutes(seconds: number | string | null | undefined): string | null {
  if (seconds === null || seconds === undefined || seconds === "") return null;
  const value = Number(seconds);
  if (!Number.isFinite(value)) return null;
  const m = value / 60;
  return `${Number.isInteger(m) ? m : m.toFixed(1)} min`;
}
