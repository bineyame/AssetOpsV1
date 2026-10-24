/**
 * W5-03a E2: read-only client for an EV charging Site's three selected depth reads (`.agent/W5-03-build-spec.md`
 * "E1a/E1b wire payloads" and the W5-03a pre-flight rulings):
 *
 *   GET /api/sites/{site_code}/ev/availability
 *   GET /api/sites/{site_code}/ev/energy
 *   GET /api/sites/{site_code}/ev/health
 *
 * Each takes the optional strict-UTC window `from`, `to` (both or neither) and `known_at`. A 200 answer is accepted
 * only when its key sets are exactly the `ev-depth-1` key sets and every value is in its value set; anything else is
 * malformed and returned as `unavailable` with the shared copy, never as an empty read. Refusals are
 * `{error:{code,message}}` and are returned as `refused`. E3/E4 may wire further but keep every validator.
 */
import { SITES_API_PATH } from "./siteDirectoryClient";
import { isObject } from "./evidenceRead";
import { type ColdRead, type ColdWindowQuery, coldWindowSearch } from "./coldAssessmentClient";

export const EV_DEPTH_SCHEMA_VERSION = "ev-depth-1";
export const EV_DEPTH_STATES = ["CURRENT", "PENDING_RECOMPUTE", "STALE_SOURCE", "HISTORICAL", "UNKNOWN"] as const;
export type EvDepthState = (typeof EV_DEPTH_STATES)[number];
export const EV_DEPTH_UNREACHABLE = "The EV depth read could not be reached.";
export const EV_DEPTH_MALFORMED = "The EV depth read answered in an unexpected shape.";
export const SCHEDULE_STATES = ["SCHEDULED", "DECLARED_EMPTY", "NOT_ESTABLISHED"] as const;
export type ScheduleState = (typeof SCHEDULE_STATES)[number];
export const SPAN_STATES = ["AVAILABLE", "UNAVAILABLE", "UNKNOWN"] as const;
export type SpanState = (typeof SPAN_STATES)[number];

export interface EvDepthWindow {
  from: string | null;
  to: string | null;
  known_at: string | null;
  committed_watermark: string | null;
}

export interface EvDepthSelection {
  state: EvDepthState;
  assessment_revision_id: string | null;
  session_revision_ids: string[];
  accepted_evidence_ids: string[];
  source_provenance: Record<string, unknown>;
}

export interface EvDepthLinks {
  sessions: string;
  evidence_analysis: string;
  financials: string;
}

interface EvDepthHead {
  schema_version: typeof EV_DEPTH_SCHEMA_VERSION;
  site_id: string;
  window: EvDepthWindow;
  selection: EvDepthSelection;
  links: EvDepthLinks;
}

export interface AvailabilitySpan {
  from: string;
  to: string;
  state: SpanState;
  evidence_ids: string[];
}

export interface AvailabilityConnector {
  asset_id: string;
  label: string;
  scheduled_seconds: number | null;
  known_available_seconds: number | null;
  known_unavailable_seconds: number | null;
  unknown_seconds: number | null;
  spans: AvailabilitySpan[];
}

export interface EvAvailability {
  calculation_version: "ev-availability/1";
  schedule_state: ScheduleState;
  scheduled_seconds: number | null;
  known_available_seconds: number | null;
  known_unavailable_seconds: number | null;
  unknown_seconds: number | null;
  known_time_ratio: string | null;
  full_lower: string | null;
  full_upper: string | null;
  connectors: AvailabilityConnector[];
}

export interface EvAvailabilityRead extends EvDepthHead {
  availability: EvAvailability;
}

export interface ImportSample {
  source_time: string;
  import_kw: string;
  evidence_id: string;
}

export interface EvConsequence {
  state: string;
  quantity_kwh: string | null;
  tariff_value: string | null;
  currency: string | null;
  amount: string | null;
  limitation: string | null;
  [key: string]: unknown;
}

export interface EvEnergy {
  metered_complete_kwh: string | null;
  partial_kwh: string | null;
  unknown_seconds: number | null;
  energy_limitation: string | null;
  import_sample_count: number;
  import_samples: ImportSample[];
  observed_peak_import_kw: string | null;
  peak_sample_at: string | null;
  configured_import_limit_kw: string | null;
  peak_below_limit: "YES" | "NO" | "UNKNOWN";
  power_constraint_state: "UNKNOWN";
  consequence: EvConsequence | null;
}

export interface EvEnergyRead extends EvDepthHead {
  energy: EvEnergy;
}

export type EvHealthKind = "CONNECTOR" | "SITE_METER" | "UNKNOWN";
export interface EvHealthRow {
  kind: EvHealthKind;
  label: string;
  asset_id: string;
  asset_code: string;
  condition_state: "NEEDS_INVESTIGATION" | "UNKNOWN";
  observation: string;
  limitation: string | null;
  next_evidence: string;
  session_id: string | null;
  evidence_ids: string[];
}

export interface EvHealth {
  foundation_revision_id: string | null;
  rows: EvHealthRow[];
  battery: { condition_state: "UNKNOWN"; limitation: string };
}

export interface EvHealthRead extends EvDepthHead {
  health: EvHealth;
}

export interface EvDepthClient {
  getAvailability(siteCode: string, window: ColdWindowQuery): Promise<ColdRead<EvAvailabilityRead>>;
  getEnergy(siteCode: string, window: ColdWindowQuery): Promise<ColdRead<EvEnergyRead>>;
  getHealth(siteCode: string, window: ColdWindowQuery): Promise<ColdRead<EvHealthRead>>;
}

/* ---------- exact validation ---------- */

function keysExactly(value: unknown, keys: readonly string[]): value is Record<string, unknown> {
  if (!isObject(value) || Array.isArray(value)) return false;
  const own = Object.keys(value);
  return own.length === keys.length && keys.every((key) => Object.prototype.hasOwnProperty.call(value, key));
}

const isString = (value: unknown): value is string => typeof value === "string";
const isNullableString = (value: unknown): boolean => value === null || isString(value);
const isStringArray = (value: unknown): value is string[] => Array.isArray(value) && value.every(isString);
const oneOf = (value: unknown, set: readonly string[]): boolean => isString(value) && set.includes(value);
const isSeconds = (value: unknown): boolean => typeof value === "number" && Number.isFinite(value) && value >= 0;
const isNullableSeconds = (value: unknown): boolean => value === null || isSeconds(value);
const isDecimal = (value: unknown): boolean => isString(value) && /^-?\d+(\.\d+)?$/.test(value);
const isNullableDecimal = (value: unknown): boolean => value === null || isDecimal(value);

const WINDOW_KEYS = ["from", "to", "known_at", "committed_watermark"] as const;
const SELECTION_KEYS = [
  "state",
  "assessment_revision_id",
  "session_revision_ids",
  "accepted_evidence_ids",
  "source_provenance",
] as const;
const LINK_KEYS = ["sessions", "evidence_analysis", "financials"] as const;
const SECONDS_KEYS = ["scheduled_seconds", "known_available_seconds", "known_unavailable_seconds", "unknown_seconds"];
const AVAILABILITY_KEYS = [
  "calculation_version",
  "schedule_state",
  ...SECONDS_KEYS,
  "known_time_ratio",
  "full_lower",
  "full_upper",
  "connectors",
];
const CONNECTOR_KEYS = ["asset_id", "label", ...SECONDS_KEYS, "spans"];
const SPAN_KEYS = ["from", "to", "state", "evidence_ids"];
const ENERGY_KEYS = [
  "metered_complete_kwh",
  "partial_kwh",
  "unknown_seconds",
  "energy_limitation",
  "import_sample_count",
  "import_samples",
  "observed_peak_import_kw",
  "peak_sample_at",
  "configured_import_limit_kw",
  "peak_below_limit",
  "power_constraint_state",
  "consequence",
];
const SAMPLE_KEYS = ["source_time", "import_kw", "evidence_id"];
const HEALTH_KEYS = ["foundation_revision_id", "rows", "battery"];
const HEALTH_ROW_KEYS = [
  "kind",
  "label",
  "asset_id",
  "asset_code",
  "condition_state",
  "observation",
  "limitation",
  "next_evidence",
  "session_id",
  "evidence_ids",
];

function isHead(value: unknown, payload: string): value is Record<string, unknown> {
  if (!keysExactly(value, ["schema_version", "site_id", "window", "selection", payload, "links"])) return false;
  if (value.schema_version !== EV_DEPTH_SCHEMA_VERSION || !isString(value.site_id)) return false;
  const window = value.window;
  if (!keysExactly(window, WINDOW_KEYS) || !WINDOW_KEYS.every((key) => isNullableString(window[key]))) return false;
  const selection = value.selection;
  if (
    !keysExactly(selection, SELECTION_KEYS) ||
    !oneOf(selection.state, EV_DEPTH_STATES) ||
    !isNullableString(selection.assessment_revision_id) ||
    !isStringArray(selection.session_revision_ids) ||
    !isStringArray(selection.accepted_evidence_ids) ||
    !isObject(selection.source_provenance) ||
    Array.isArray(selection.source_provenance)
  ) {
    return false;
  }
  const links = value.links;
  return keysExactly(links, LINK_KEYS) && LINK_KEYS.every((key) => isString(links[key]));
}

function isSpan(value: unknown): boolean {
  return (
    keysExactly(value, SPAN_KEYS) &&
    isString(value.from) &&
    isString(value.to) &&
    value.from < value.to &&
    oneOf(value.state, SPAN_STATES) &&
    isStringArray(value.evidence_ids)
  );
}

function isConnector(value: unknown): boolean {
  return (
    keysExactly(value, CONNECTOR_KEYS) &&
    isString(value.asset_id) &&
    isString(value.label) &&
    SECONDS_KEYS.every((key) => isNullableSeconds(value[key])) &&
    Array.isArray(value.spans) &&
    value.spans.every(isSpan)
  );
}

export function isEvAvailability(value: unknown): value is EvAvailability {
  return (
    keysExactly(value, AVAILABILITY_KEYS) &&
    value.calculation_version === "ev-availability/1" &&
    oneOf(value.schedule_state, SCHEDULE_STATES) &&
    SECONDS_KEYS.every((key) => isNullableSeconds(value[key])) &&
    ["known_time_ratio", "full_lower", "full_upper"].every((key) => isNullableDecimal(value[key])) &&
    Array.isArray(value.connectors) &&
    value.connectors.every(isConnector)
  );
}

export function isEvAvailabilityRead(value: unknown): value is EvAvailabilityRead {
  return isHead(value, "availability") && isEvAvailability(value.availability);
}

function isSample(value: unknown): boolean {
  return (
    keysExactly(value, SAMPLE_KEYS) && isString(value.source_time) && isDecimal(value.import_kw) && isString(value.evidence_id)
  );
}

function isConsequence(value: unknown): boolean {
  if (value === null) return true;
  if (!isObject(value) || Array.isArray(value)) return false;
  return (
    isString(value.state) &&
    ["quantity_kwh", "tariff_value", "currency", "amount", "limitation"].every(
      (key) => Object.prototype.hasOwnProperty.call(value, key) && isNullableString(value[key]),
    )
  );
}

export function isEvEnergy(value: unknown): value is EvEnergy {
  return (
    keysExactly(value, ENERGY_KEYS) &&
    isNullableDecimal(value.metered_complete_kwh) &&
    isNullableDecimal(value.partial_kwh) &&
    isNullableSeconds(value.unknown_seconds) &&
    isNullableString(value.energy_limitation) &&
    Number.isInteger(value.import_sample_count) &&
    Array.isArray(value.import_samples) &&
    value.import_samples.every(isSample) &&
    value.import_sample_count === value.import_samples.length &&
    isNullableDecimal(value.observed_peak_import_kw) &&
    isNullableString(value.peak_sample_at) &&
    isNullableDecimal(value.configured_import_limit_kw) &&
    oneOf(value.peak_below_limit, ["YES", "NO", "UNKNOWN"]) &&
    value.power_constraint_state === "UNKNOWN" &&
    isConsequence(value.consequence)
  );
}

export function isEvEnergyRead(value: unknown): value is EvEnergyRead {
  return isHead(value, "energy") && isEvEnergy(value.energy);
}

/**
 * W5-03b E4: the only `(kind, condition_state, observation, limitation, next_evidence)` tuples the E1b Health
 * builder emits (`analytics/ev_depth.py` CONNECTOR_FAULT, CONNECTOR_UNKNOWN, SITE_METER, METER_UNKNOWN). Any other
 * tuple is a malformed 200 and renders the unavailable state.
 */
export const EV_HEALTH_TUPLES: readonly (readonly [EvHealthKind, EvHealthRow["condition_state"], string, string | null, string])[] = [
  ["CONNECTOR", "NEEDS_INVESTIGATION", "Session interruption observed", "Fault-stopped session observed; cause not diagnosed", "Retrieve diagnostic log and witness a complete session"],
  ["CONNECTOR", "UNKNOWN", "Condition unknown", "No charger condition assessment", "Record diagnostic and covered operation"],
  ["SITE_METER", "UNKNOWN", "Sampled import only", null, "Record continuous import and request/limit evidence"],
  ["UNKNOWN", "UNKNOWN", "Meter role not established", "No selected Site-import binding for this meter", "Confirm meter topology and source binding"],
];

function isHealthRow(value: unknown): boolean {
  return (
    keysExactly(value, HEALTH_ROW_KEYS) &&
    oneOf(value.kind, ["CONNECTOR", "SITE_METER", "UNKNOWN"]) &&
    isString(value.label) &&
    isString(value.asset_id) &&
    isString(value.asset_code) &&
    oneOf(value.condition_state, ["NEEDS_INVESTIGATION", "UNKNOWN"]) &&
    isString(value.observation) &&
    isNullableString(value.limitation) &&
    isString(value.next_evidence) &&
    isNullableString(value.session_id) &&
    isStringArray(value.evidence_ids) &&
    EV_HEALTH_TUPLES.some(
      ([kind, state, observation, limitation, next]) =>
        value.kind === kind &&
        value.condition_state === state &&
        value.observation === observation &&
        value.limitation === limitation &&
        value.next_evidence === next,
    )
  );
}

export function isEvHealth(value: unknown): value is EvHealth {
  if (!keysExactly(value, HEALTH_KEYS) || !isNullableString(value.foundation_revision_id)) return false;
  const battery = value.battery;
  return (
    Array.isArray(value.rows) &&
    value.rows.every(isHealthRow) &&
    keysExactly(battery, ["condition_state", "limitation"]) &&
    battery.condition_state === "UNKNOWN" &&
    isString(battery.limitation)
  );
}

export function isEvHealthRead(value: unknown): value is EvHealthRead {
  return isHead(value, "health") && isEvHealth(value.health);
}

/* ---------- reads ---------- */

async function read<T>(url: string, shape: (value: unknown) => boolean): Promise<ColdRead<T>> {
  let response: Response;
  try {
    response = await fetch(url);
  } catch {
    return { status: "unavailable", message: EV_DEPTH_UNREACHABLE };
  }
  let body: unknown = null;
  try {
    body = await response.json();
  } catch {
    body = null;
  }
  if (response.ok) {
    return shape(body) ? { status: "loaded", value: body as T } : { status: "unavailable", message: EV_DEPTH_MALFORMED };
  }
  const error = isObject(body) && isObject(body.error) ? body.error : null;
  if (error !== null && typeof error.code === "string") {
    return {
      status: "refused",
      httpStatus: response.status,
      code: error.code,
      message: typeof error.message === "string" ? error.message : null,
    };
  }
  return { status: "unavailable", message: EV_DEPTH_MALFORMED };
}

export function createEvDepthClient(basePath: string = SITES_API_PATH): EvDepthClient {
  const base = (siteCode: string) => `${basePath}/${encodeURIComponent(siteCode)}/ev`;
  return {
    getAvailability: (siteCode, window) =>
      read(`${base(siteCode)}/availability${coldWindowSearch(window)}`, isEvAvailabilityRead),
    getEnergy: (siteCode, window) => read(`${base(siteCode)}/energy${coldWindowSearch(window)}`, isEvEnergyRead),
    getHealth: (siteCode, window) => read(`${base(siteCode)}/health${coldWindowSearch(window)}`, isEvHealthRead),
  };
}

/* ---------- shared formats ---------- */

/** `{h} h {m} min`, omitting a zero hour; `0 min` for zero; seconds floored to whole minutes for display only. */
export function durationText(seconds: number): string {
  const minutes = Math.floor(seconds / 60);
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return h === 0 ? `${m} min` : `${h} h ${m} min`;
}

/** The shared non-CURRENT state sentence (shared literal ledger), or null for CURRENT. */
export function depthStateNotice(state: EvDepthState): string | null {
  switch (state) {
    case "PENDING_RECOMPUTE":
      return "New evidence is being assessed. Earlier selected results may change.";
    case "HISTORICAL":
      return "This result reflects records known at the selected cutoff.";
    case "STALE_SOURCE":
      return "Selected source records are stale for this window.";
    case "UNKNOWN":
      return "No selected EV session assessment covers this window yet.";
    default:
      return null;
  }
}
