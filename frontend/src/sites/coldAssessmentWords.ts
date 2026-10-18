/**
 * W2-03: plain words for the cold assessment reads. Every server code shown on a cold screen goes through one
 * of these maps; an unmapped code is turned into lower-case words rather than shown raw.
 */

export function plainCode(code: string | null | undefined): string {
  if (code === null || code === undefined || code === "") return "Not recorded";
  const words = code.toLowerCase().replace(/_/g, " ");
  return words.charAt(0).toUpperCase() + words.slice(1);
}

function mapped(map: Record<string, string>, code: string | null | undefined, fallback = "Not assessed"): string {
  if (code === null || code === undefined) return fallback;
  return map[code] ?? plainCode(code);
}

export const CURRENTNESS_WORDS: Record<string, string> = {
  CURRENT: "Up to date for this window",
  PENDING_RECOMPUTE: "Newer readings waiting to be assessed",
  STALE_SOURCE: "Probe readings stale at the window end",
  HISTORICAL: "Read at an earlier evidence time",
  UNKNOWN: "Not assessed",
};
export const currentnessWord = (code: string | null | undefined) => mapped(CURRENTNESS_WORDS, code);

const EXCURSION_STATE: Record<string, string> = {
  OBSERVED_EXCURSION: "Outside policy",
  NO_EXCURSION_OBSERVED: "Within policy",
  UNKNOWN: "Not assessed",
  CONTRADICTORY: "Readings disagree",
};
export const temperatureStateWord = (code: string | null | undefined) => mapped(EXCURSION_STATE, code);

const CLAIM: Record<string, string> = {
  OBSERVED: "Observed",
  BOUNDED: "Bounded",
  POSSIBLE: "Possible",
  UNKNOWN: "Not established",
  CONTRADICTORY: "Records disagree",
};
export const claimWord = (code: string | null | undefined) => mapped(CLAIM, code, "Not established");

const START_RESULT: Record<string, string> = {
  OBSERVED_SUCCESS: "Started",
  OBSERVED_FAILURE: "Start failed",
  UNKNOWN: "Not established",
  CONTRADICTORY: "Results disagree",
};
export const startResultWord = (code: string | null | undefined) => mapped(START_RESULT, code, "Not established");

export const STEP_LABELS: Record<string, string> = {
  GRID: "Grid supply",
  START_REQUEST: "Start requested",
  START_RESULT: "Start result",
  GENERATOR: "Generator",
  TRANSFER: "Transfer to backup",
  BUS: "Backup bus",
  COMPRESSOR: "Compressor",
  PROBE: "Chamber temperature",
};
export const stepLabel = (code: string) => STEP_LABELS[code] ?? plainCode(code);

/** What an observed step establishes, and the limit it leaves (the mock's "Evidence by causal step" columns). */
export const STEP_ESTABLISHES: Record<string, [string, string]> = {
  GRID: ["Supply interruption", "Not the cause of a start failure"],
  START_REQUEST: ["An automatic start was requested", "Does not identify a defective part"],
  START_RESULT: ["Whether the start succeeded", "A failed start needs inspection"],
  GENERATOR: ["Generator state after the request", "Does not show power reaching the compressor"],
  TRANSFER: ["Load moved to backup supply", "Transfer detail may be incomplete"],
  BUS: ["Backup bus powered", "Does not show the compressor running"],
  COMPRESSOR: ["Cooling resumed", "Does not show the chamber back in policy"],
  PROBE: ["Chamber temperature after recovery", "No spoilage determination"],
};

const STEP_STATE: Record<string, string> = {
  OBSERVED: "Observed",
  MISSING: "Not recorded",
  CONTRADICTORY: "Records disagree",
};
export const stepStateWord = (code: string) => mapped(STEP_STATE, code);

const REASONS: Record<string, string> = {
  SUSPECT: "Marked suspect by the source",
  CLOCK_UNATTESTED: "Source clock not confirmed",
  UNBOUND: "Not from the configured probe",
  CONTRADICTORY: "Conflicts with another accepted record",
  DOOR_EVENT: "Door record, context only",
  MISSING_PROBE: "No probe reading",
};
export const reasonWord = (code: string | null | undefined) => mapped(REASONS, code, "Not recorded");

const LIFECYCLE: Record<string, string> = {
  SUPPORTED: "Open",
  UNCONFIRMED: "Unconfirmed",
  NO_LONGER_SUPPORTED: "No longer supported",
};
export const lifecycleWord = (code: string | null | undefined) => mapped(LIFECYCLE, code, "Not recorded");

const TRANSITION: Record<string, string> = {
  OPENED: "Opened",
  SUPPORT_CHANGED: "Supporting records changed",
  BASIS_REFRESHED: "Configuration or cutoff refreshed",
  NO_LONGER_SUPPORTED: "No longer supported",
};
export const transitionWord = (code: string | null | undefined) => mapped(TRANSITION, code, "Not recorded");

const CLASSIFICATION: Record<string, string> = {
  REGISTERED_SIMULATION: "Generated test data",
  MIXED: "Mixed sources",
  MIXED_OR_UNKNOWN_SOURCE: "Mixed or unknown sources",
};
/** Shown beside the label (D-2026-10-16-s405b-label; W2-03 deviation 18). */
export const SIMULATION_SOURCE_SENTENCE = "From a registered test run; not readings from physical equipment.";
export const classificationWord = (code: string | null | undefined) => mapped(CLASSIFICATION, code, "Not recorded");

/** A server limitation sentence with any step or reason code replaced by its plain words. */
export function plainLimitation(text: string): string {
  return text.replace(/\b[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+\b|\b(?:GRID|GENERATOR|TRANSFER|BUS|COMPRESSOR|PROBE)\b/g, (code) =>
    (STEP_LABELS[code] ?? REASONS[code] ?? plainCode(code)).toLowerCase(),
  );
}
