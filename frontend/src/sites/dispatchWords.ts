/**
 * Plain words for the durable dispatch read (S3-01 phase 3b). The default
 * reading names each state and limitation in client language
 * (D-2026-10-04-plain-language-analysis-views); the stored code is kept on a
 * `data-` attribute and shown verbatim only in the Analysis view.
 */
import type { ProjectionStatus } from "./performanceDispatchClient";

export const STATUS_WORDS: Record<ProjectionStatus, { label: string; sentence: string }> = {
  CURRENT: {
    label: "Up to date",
    sentence: "This result uses every accepted record for the day and the site settings in force.",
  },
  PENDING: {
    label: "Being assessed",
    sentence: "Records for this day are waiting to be assessed. No result is shown until the assessment finishes.",
  },
  STALE_PROJECTION: {
    label: "Out of date",
    sentence:
      "The result below was made before newer records, settings or rules. It is kept for reference and is being replaced.",
  },
  FAILED: {
    label: "Reassessment failed",
    sentence:
      "The latest reassessment of this day failed. The earlier result below is kept so it can still be inspected; it is not current.",
  },
  UNASSESSED: {
    label: "Not assessed",
    sentence: "No assessment exists for this day. Nothing is shown in its place.",
  },
};

/** The plain meaning of a status reason, by its code. */
export function reasonWords(reason: string): string {
  const code = reason.split(":")[0];
  switch (code) {
    case "RECOMPUTE_OUTSTANDING":
      return "A reassessment of this day has not finished yet.";
    case "RECOMPUTE_FAILED":
      return "The reassessment stopped with an error after its retries.";
    case "MODEL_VERSION_CHANGED":
      return "The assessment rules have been updated since this result was made.";
    case "CONFIGURATION_CHANGED":
      return "The site settings that apply to this day changed after this result was made.";
    case "INPUT_BASIS_CHANGED":
      return "Accepted records for this day changed after this result was made.";
    case "NOT_ASSESSED":
      return "Accepted records exist for this day, but no assessment has been run on them.";
    default:
      return "Another reason is recorded; see Analysis.";
  }
}

const LIMITATION_WORDS: Record<string, string> = {
  MISSING_ROLE: "A measurement this assessment needs is not set up for part of the day",
  EVIDENCE_GAP: "Records needed for part of a generator period are missing",
  INTERVAL_LIMITED: "A generator period is only partly bounded by the records",
  OPEN_BOUND: "The generator's start or stop falls outside the records",
  AMBIGUOUS_COHORT:
    "Two overlapping series of records report the same times; neither is chosen, so the day is not assessed",
  SEQUENCE_ORDER_INVERTED: "Some records arrived in a different order from when they were taken",
  REPORTS_OVERLAP: "Some reports cover overlapping times",
  GENERATOR_SERIES_AMBIGUOUS: "The generator's records could not be put in one proven time order",
  NO_COHORT: "No single series of records could be chosen for this day, so it is not assessed",
  NO_GENERATOR_STATE: "No generator on/off record for this day",
};

export function limitationCode(limitation: string): string {
  return limitation.split(/[: ]/)[0];
}

export function limitationWords(code: string): string {
  return LIMITATION_WORDS[code] ?? "Another limitation is recorded; see Analysis";
}

/** Group a list of limitations by code, keeping first-seen order. */
export function groupLimitations(limitations: string[]): { code: string; items: string[] }[] {
  const groups = new Map<string, string[]>();
  for (const item of limitations) {
    const code = limitationCode(item);
    groups.set(code, [...(groups.get(code) ?? []), item]);
  }
  return [...groups.entries()].map(([code, items]) => ({ code, items }));
}

const ROLE_WORDS: Record<string, string> = {
  generator_state: "Generator on/off",
  generator_power: "Generator output",
  load_power: "Site demand",
  pv_power: "Solar output",
  battery_power: "Battery output",
  battery_soc: "Battery charge",
  pv_available_power: "Available solar power",
  pcs_discharge_capability: "Battery output limit",
  fuel_level: "Fuel level",
  feeder_demand: "Feeder demand",
  pv_irradiance: "Solar irradiance",
  battery_reserve: "Reported battery reserve level (the reserve used comes from site settings)",
};

export function roleWords(role: string): string {
  return ROLE_WORDS[role] ?? role.replace(/_/g, " ");
}

const COVERAGE_WORDS: Record<string, string> = {
  BOUND: "Set up",
  MISSING: "Not set up",
  UNBOUND: "Not set up",
};

export function coverageWords(status: string): string {
  return COVERAGE_WORDS[status] ?? status.toLowerCase().replace(/_/g, " ");
}

const CONSTRAINT_WORDS: Record<string, string> = {
  BATTERY_AT_RESERVE: "Battery at its reserve level",
  BATTERY_NEAR_RESERVE: "Battery near its reserve level",
  CAPABILITY_SHORTFALL: "Demand above what solar and battery could supply",
  OPERATOR_OVERRIDE: "An operator instruction kept the generator on",
  MINIMUM_RUNTIME: "The generator was within its minimum operating time",
};

export function constraintWords(code: string): string {
  return CONSTRAINT_WORDS[code] ?? code.toLowerCase().replace(/_/g, " ");
}

/** Plain words for a record's quality flag. */
export function qualityWords(quality: string): string {
  const text = quality.toLowerCase().replace(/_/g, " ");
  return text.charAt(0).toUpperCase() + text.slice(1);
}

/** "14:20" from an ISO instant (UTC), or the text unchanged. */
export function clock(instant: string | null | undefined): string {
  if (!instant) {
    return "open";
  }
  const match = /T(\d{2}):(\d{2})/.exec(instant);
  return match === null ? instant : `${match[1]}:${match[2]}`;
}

/** "2026-10-02 04:15" from an ISO instant (UTC), or the text unchanged. */
export function stamp(instant: string | null | undefined): string {
  if (!instant) {
    return "not reported";
  }
  const match = /^(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2})/.exec(instant);
  return match === null ? instant : `${match[1]} ${match[2]}`;
}

/** Whole minutes from a decimal string, or null. */
export function minutes(value: string | null | undefined): number | null {
  if (value === null || value === undefined || value === "") {
    return null;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? Math.round(parsed) : null;
}

export function durationText(total: number): string {
  if (total < 60) {
    return `${total} min`;
  }
  const h = Math.floor(total / 60);
  const m = total % 60;
  return m === 0 ? `${h} h` : `${h} h ${m} min`;
}

/** The UTC day before or after `day` (YYYY-MM-DD). */
export function shiftDay(day: string, by: number): string {
  const at = new Date(`${day}T00:00:00Z`);
  at.setUTCDate(at.getUTCDate() + by);
  return at.toISOString().slice(0, 10);
}

export function isDay(value: string | null): value is string {
  return value !== null && /^\d{4}-\d{2}-\d{2}$/.test(value) && !Number.isNaN(Date.parse(`${value}T00:00:00Z`));
}
