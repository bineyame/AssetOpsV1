/**
 * W3-02 commit-2 fix (r1 L1): plain words for the Evidence `Record details` disclosure. Every entry is copied from
 * an already reviewed dictionary (W1 `EvidenceClaimLimit` role and reason sentences, cold `coldSiteViews` capability
 * and role words, EV `EvSiteViews` claim labels). An unmapped key never prints; it falls back to the stated sentence.
 */
export const NO_DESCRIPTION = "Description not available";
export const NO_REASON_DETAILS = "Reason details are not available";

const CLAIM_WORDS: Readonly<Record<string, string>> = {
  TEMPERATURE_POINT: "Temperature compliance",
  EXCURSION_BOUNDS: "Temperature compliance",
  BACKUP_START_RESULT: "Backup response",
  TRANSFER_POSITION: "Backup response",
  COOLING_RESPONSE: "Cooling recovery",
  PRODUCT_EXPOSURE: "Product exposure",
  SESSION_OUTCOME: "Session outcomes",
  SERVICE_STATE: "Connector availability",
  DELIVERED_ENERGY: "Delivered energy",
  FAULT_ASSOCIATION: "Cause of interruption",
  SITE_POWER_CONTEXT: "Site power context",
  POWER_CONSTRAINT: "Site power constraint",
  GROSS_TARIFF_SCENARIO: "Gross tariff scenario",
};

const ROLE_WORDS: Readonly<Record<string, string>> = {
  generator_state: "Generator on or off",
  feeder_demand: "Site demand",
  pv_available_power: "Solar power available",
  pcs_discharge_capability: "Battery output limit",
  battery_soc: "Battery charge level",
  chamber_temperature: "Chamber temperature",
  grid_power_event: "Grid event",
  backup_start_event: "Start request and result",
  transfer_result: "Transfer position",
  backup_bus_state: "Bus voltage",
  compressor_state: "Compressor state",
  door_event: "Door and loading context",
};

const STATE_WORDS: Readonly<Record<string, string>> = {
  FULL: "Full",
  SUPPORTED: "Full",
  LIMITED: "Limited",
  NONE: "None",
  UNAVAILABLE: "None",
  UNKNOWN: "Unknown",
  CONTRADICTORY: "Conflicting records",
  NOT_APPLICABLE: "N/A",
};

export const roleWord = (role: unknown): string => (typeof role === "string" ? ROLE_WORDS[role] : undefined) ?? NO_DESCRIPTION;
export const stateWord = (state: unknown): string => (typeof state === "string" ? STATE_WORDS[state] : undefined) ?? "Not assessed";

/** Reviewed reason sentences (the W1 wording, without periods); an unmapped or malformed reason has the fallback. */
export function reasonSentence(reason: unknown): string {
  if (typeof reason !== "object" || reason === null) return NO_REASON_DETAILS;
  const r = reason as { code?: unknown; role?: unknown };
  const named = typeof r.role === "string" && ROLE_WORDS[r.role] !== undefined ? ROLE_WORDS[r.role] : null;
  switch (r.code) {
    case "MISSING_ROLE":
      return named === null ? "Some needed readings are missing." : `${named} missing.`;
    case "POOR_QUALITY":
      return named === null ? "Some readings are unreliable." : `${named}: unreliable readings.`;
    case "CONFLICTING":
      return named === null ? "Some readings conflict." : `${named}: conflicting reports.`;
    case "GENERATOR_UNOBSERVED":
      return "The generator's on or off state was not observed.";
    case "OPEN_BOUND":
      return "The end of the generator's operation is not yet known, so its length is a lower bound.";
    case "MODEL_LIMIT":
      return "Part of the period cannot be classified from these readings.";
    case "COHORT":
      return "The set of reporting devices for this day was not settled.";
    case "CONFIGURATION":
      return "The site's recorded configuration limits this conclusion.";
    case "RULE_BASIS_INCOMPLETE":
      return "The rule's inputs for this period were incomplete.";
    default:
      return NO_REASON_DETAILS;
  }
}

/** Plain reason sentences, deduplicated with order kept. */
export function reasonSentences(reasons: unknown): string[] {
  if (!Array.isArray(reasons)) return [];
  const out: string[] = [];
  for (const r of reasons) {
    const s = reasonSentence(r);
    if (!out.includes(s)) out.push(s);
  }
  return out;
}

const plainText = (v: unknown): string | null => (typeof v === "string" && v.trim() !== "" ? v : null);
const sentence = (t: string): string => (/[.!?]$/.test(t) ? t : `${t}.`);

/** One selected observation: `claim label — readiness word`, its limitation sentence and missing-input labels. */
export function observationSummary(c: Record<string, unknown>, fallbackLabel: string): string {
  const label = typeof c.claim === "string" ? (CLAIM_WORDS[c.claim] ?? NO_DESCRIPTION) : fallbackLabel;
  const parts = [sentence(`${label} — ${stateWord(c.state)}`)];
  const limitation = plainText(c.limitation) ?? plainText(c.statement);
  if (limitation !== null) parts.push(sentence(limitation));
  const missing = Array.isArray(c.missing_roles) ? c.missing_roles : [];
  if (missing.length > 0) parts.push(`Missing: ${missing.map(roleWord).join(", ")}.`);
  return parts.join(" ");
}

/** Plain label of a historical gap object (`gap_code` + `missing_role`), or the fallback. */
export function gapWord(gap: unknown): string {
  if (typeof gap !== "object" || gap === null) return NO_REASON_DETAILS;
  const g = gap as { gap_code?: unknown; missing_role?: unknown };
  return reasonSentence({ code: g.gap_code, role: g.missing_role });
}

/** Earlier selection: readiness word, limitation, selected observations, then reasons; absent parts omitted. */
export function priorSelectionText(prior: Record<string, unknown>, fallbackLabel: string): string {
  const parts: string[] = [];
  const readiness = prior.readiness ?? prior.state;
  if (readiness !== undefined) parts.push(sentence(stateWord(readiness)));
  const limitation = plainText(prior.limitation);
  if (limitation !== null) parts.push(sentence(limitation));
  const observations = Array.isArray(prior.interval_ceilings) ? prior.interval_ceilings : [];
  for (const o of observations) {
    if (typeof o === "object" && o !== null) parts.push(observationSummary(o as Record<string, unknown>, fallbackLabel));
  }
  parts.push(...reasonSentences(prior.reasons));
  return parts.join(" ");
}
