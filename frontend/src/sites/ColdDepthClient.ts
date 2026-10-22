/**
 * W5-01a C2: read-only client for a cold-chain Site's two selected depth reads (`.agent/W5-01-build-spec.md`
 * "Shared selected read and guards", C1 "Cooling payload" and "Health read", C2 "DTO, label and link sources"):
 *
 *   GET /api/sites/{site_code}/cold/cooling
 *   GET /api/sites/{site_code}/cold/health
 *
 * Each takes the optional strict-UTC window `from`, `to` (both or neither) and `known_at`. A 200 answer is
 * accepted only when its key sets are exactly the C1 key sets (order-insensitive) and every value is in its C1
 * value set; anything else is malformed and is returned as `unavailable`, never as an empty read. Refusals are
 * `{error:{code,message}}` and are returned as `refused`. W5-01a C3 validates the `health` payload against the C1
 * Health literal table (`HEALTH_ROW_LITERALS`).
 */
import { SITES_API_PATH } from "./siteDirectoryClient";
import { isObject } from "./evidenceRead";
import { type ColdRead, type ColdWindowQuery, coldWindowSearch } from "./coldAssessmentClient";

export const COLD_DEPTH_SCHEMA_VERSION = "cold-depth-1";
export const COLD_DEPTH_STATES = ["CURRENT", "PENDING_RECOMPUTE", "STALE_SOURCE", "HISTORICAL", "UNKNOWN"] as const;
export type ColdDepthState = (typeof COLD_DEPTH_STATES)[number];
export const COOLING_RECOVERY_STATES = ["LIMITED", "CONTRADICTORY", "UNKNOWN"] as const;
export type CoolingRecoveryState = (typeof COOLING_RECOVERY_STATES)[number];
export const COOLING_CONTEXT_LABELS = [
  "Ambient temperature",
  "Power availability",
  "Door-open duration",
  "Loading / batch",
  "Defrost",
] as const;
export type CoolingContextLabel = (typeof COOLING_CONTEXT_LABELS)[number];
const DOOR_ROW: CoolingContextLabel = "Door-open duration";

export interface ColdDepthWindow {
  from: string | null;
  to: string | null;
  known_at: string | null;
  committed_watermark: string | null;
}

export interface ColdDepthSelection {
  state: ColdDepthState;
  assessment_revision_ids: string[];
  accepted_evidence_ids: string[];
  source_provenance: Record<string, unknown>;
}

export interface ColdDepthLinks {
  temperature: string | null;
  backup: string | null;
  evidence: string | null;
  health: string | null;
}

export interface CoolingPoint {
  role: string;
  source_time: string;
  evidence_ids: string[];
}

export interface CoolingContextRow {
  label: CoolingContextLabel;
  state: "Observed" | "Unknown";
  evidence_ids: string[];
  duration_seconds: number | null;
}

/** The C1 "Cooling payload" keys exactly. The four time/duration fields are always null for W2. */
export interface ColdCooling {
  recovery_state: CoolingRecoveryState;
  policy_high_deg_c: string | null;
  selected_points: CoolingPoint[];
  observed_restart_at: null;
  observed_return_to_policy_at: null;
  duration_lower_seconds: null;
  duration_upper_seconds: null;
  comparison_state: "CONTEXT_MISSING";
  context: CoolingContextRow[];
}

interface ColdDepthHead {
  schema_version: typeof COLD_DEPTH_SCHEMA_VERSION;
  site_id: string;
  window: ColdDepthWindow;
  selection: ColdDepthSelection;
  links: ColdDepthLinks;
}

export interface ColdCoolingRead extends ColdDepthHead {
  cooling: ColdCooling;
}

export type ColdHealthKind = "BACKUP_GENERATOR" | "COOLING_PLANT" | "TEMPERATURE_SENSING";
export type ColdHealthCondition = "NEEDS_INVESTIGATION" | "LIMITED" | "UNKNOWN" | "NOT_CONFIGURED";

/** One C1 "Health read" row; keys exactly, in order, as the C1 Health table. */
export interface ColdHealthRow {
  kind: ColdHealthKind;
  label: string;
  asset_id: string | null;
  assets: { asset_id: string; asset_code: string; display_name: string | null }[];
  observation: string;
  condition_state: ColdHealthCondition;
  limitation: string;
  next_evidence: string;
  evidence_ids: string[];
  link: string | null;
}

export interface ColdHealthRead extends ColdDepthHead {
  health: { foundation_revision_id: string | null; rows: ColdHealthRow[] };
}

export interface ColdDepthClient {
  getCooling(siteCode: string, window: ColdWindowQuery): Promise<ColdRead<ColdCoolingRead>>;
  getHealth(siteCode: string, window: ColdWindowQuery): Promise<ColdRead<ColdHealthRead>>;
}

/* ---------- exact validation ---------- */

/** Exactly these keys, in any order. */
function keysExactly(value: unknown, keys: readonly string[]): value is Record<string, unknown> {
  if (!isObject(value) || Array.isArray(value)) return false;
  const own = Object.keys(value);
  return own.length === keys.length && keys.every((key) => Object.prototype.hasOwnProperty.call(value, key));
}

const isString = (value: unknown): value is string => typeof value === "string";
const isNullableString = (value: unknown): boolean => value === null || isString(value);
const isStringArray = (value: unknown): value is string[] => Array.isArray(value) && value.every(isString);
const oneOf = (value: unknown, set: readonly string[]): boolean => isString(value) && set.includes(value);

const TOP_COOLING = ["schema_version", "site_id", "window", "selection", "cooling", "links"] as const;
const TOP_HEALTH = ["schema_version", "site_id", "window", "selection", "health", "links"] as const;
const WINDOW_KEYS = ["from", "to", "known_at", "committed_watermark"] as const;
const SELECTION_KEYS = ["state", "assessment_revision_ids", "accepted_evidence_ids", "source_provenance"] as const;
const LINK_KEYS = ["temperature", "backup", "evidence", "health"] as const;
const COOLING_KEYS = [
  "recovery_state",
  "policy_high_deg_c",
  "selected_points",
  "observed_restart_at",
  "observed_return_to_policy_at",
  "duration_lower_seconds",
  "duration_upper_seconds",
  "comparison_state",
  "context",
] as const;
const POINT_KEYS = ["role", "source_time", "evidence_ids"] as const;
const CONTEXT_KEYS = ["label", "state", "evidence_ids", "duration_seconds"] as const;

function isHead(value: unknown, top: readonly string[]): value is Record<string, unknown> {
  if (!keysExactly(value, top)) return false;
  if (value.schema_version !== COLD_DEPTH_SCHEMA_VERSION || !isString(value.site_id)) return false;
  const window = value.window;
  if (!keysExactly(window, WINDOW_KEYS) || !WINDOW_KEYS.every((key) => isNullableString(window[key]))) return false;
  const selection = value.selection;
  if (
    !keysExactly(selection, SELECTION_KEYS) ||
    !oneOf(selection.state, COLD_DEPTH_STATES) ||
    !isStringArray(selection.assessment_revision_ids) ||
    !isStringArray(selection.accepted_evidence_ids) ||
    !isObject(selection.source_provenance) ||
    Array.isArray(selection.source_provenance)
  ) {
    return false;
  }
  const links = value.links;
  return keysExactly(links, LINK_KEYS) && LINK_KEYS.every((key) => isNullableString(links[key]));
}

function isContextRow(row: unknown, label: CoolingContextLabel): boolean {
  if (!keysExactly(row, CONTEXT_KEYS) || row.label !== label || !oneOf(row.state, ["Observed", "Unknown"])) return false;
  if (!isStringArray(row.evidence_ids)) return false;
  if (row.state === "Unknown" && row.evidence_ids.length !== 0) return false;
  const seconds = row.duration_seconds;
  if (label === DOOR_ROW && row.state === "Observed") return typeof seconds === "number" && Number.isInteger(seconds);
  return seconds === null;
}

export function isColdCooling(value: unknown): value is ColdCooling {
  if (!keysExactly(value, COOLING_KEYS)) return false;
  if (!oneOf(value.recovery_state, COOLING_RECOVERY_STATES) || !isNullableString(value.policy_high_deg_c)) return false;
  if (
    !Array.isArray(value.selected_points) ||
    !value.selected_points.every(
      (point) => keysExactly(point, POINT_KEYS) && isString(point.role) && isString(point.source_time) && isStringArray(point.evidence_ids),
    )
  ) {
    return false;
  }
  if (
    value.observed_restart_at !== null ||
    value.observed_return_to_policy_at !== null ||
    value.duration_lower_seconds !== null ||
    value.duration_upper_seconds !== null ||
    value.comparison_state !== "CONTEXT_MISSING"
  ) {
    return false;
  }
  const context = value.context;
  return (
    Array.isArray(context) &&
    context.length === COOLING_CONTEXT_LABELS.length &&
    COOLING_CONTEXT_LABELS.every((label, index) => isContextRow(context[index], label))
  );
}

export function isColdCoolingRead(value: unknown): value is ColdCoolingRead {
  return isHead(value, TOP_COOLING) && isColdCooling(value.cooling);
}

/** The C1 "Health read" literal table: per kind, its `next_evidence` and the allowed condition tuples. */
export const HEALTH_ROW_LITERALS: Record<
  ColdHealthKind,
  { next_evidence: string; tuples: { condition_state: ColdHealthCondition; observation: string; limitation: string }[] }
> = {
  BACKUP_GENERATOR: {
    next_evidence: "Witness an automatic-start test",
    tuples: [
      { condition_state: "NOT_CONFIGURED", observation: "Not configured", limitation: "No backup generator is declared in the selected Foundation" },
      { condition_state: "UNKNOWN", observation: "Start results conflict", limitation: "Selected start results conflict; no condition is assessed" },
      { condition_state: "NEEDS_INVESTIGATION", observation: "Automatic start failed", limitation: "Failed automatic start observed; part not diagnosed" },
      { condition_state: "UNKNOWN", observation: "Automatic start succeeded", limitation: "A successful start does not establish generator condition" },
      { condition_state: "UNKNOWN", observation: "No accepted start result", limitation: "No accepted automatic-start result in this window" },
    ],
  },
  COOLING_PLANT: {
    next_evidence: "Record matched loading, door and ambient context",
    tuples: [
      { condition_state: "NOT_CONFIGURED", observation: "Not configured", limitation: "No cooling plant is declared in the selected Foundation" },
      { condition_state: "UNKNOWN", observation: "Condition unknown", limitation: "Comparable recovery and condition evidence absent" },
    ],
  },
  TEMPERATURE_SENSING: {
    next_evidence: "Add calibrated spatial coverage",
    tuples: [
      { condition_state: "NOT_CONFIGURED", observation: "Not configured", limitation: "No temperature probe is declared in the selected Foundation" },
      { condition_state: "LIMITED", observation: "Single-point observation", limitation: "One accepted probe does not establish room-wide coverage" },
      { condition_state: "UNKNOWN", observation: "No accepted probe", limitation: "No accepted probe observation in this window" },
      { condition_state: "UNKNOWN", observation: "Multiple probe observations", limitation: "Multiple selected probes do not establish room-wide condition" },
    ],
  },
};
export const HEALTH_KINDS: readonly ColdHealthKind[] = ["BACKUP_GENERATOR", "COOLING_PLANT", "TEMPERATURE_SENSING"];
const HEALTH_KEYS = ["foundation_revision_id", "rows"] as const;
const HEALTH_ROW_KEYS = [
  "kind",
  "label",
  "asset_id",
  "assets",
  "observation",
  "condition_state",
  "limitation",
  "next_evidence",
  "evidence_ids",
  "link",
] as const;
const ASSET_KEYS = ["asset_id", "asset_code", "display_name"] as const;

function isHealthRow(row: unknown, kind: ColdHealthKind): boolean {
  if (!keysExactly(row, HEALTH_ROW_KEYS) || row.kind !== kind || !isString(row.label)) return false;
  if (!isNullableString(row.asset_id) || !isStringArray(row.evidence_ids) || !isNullableString(row.link)) return false;
  if (
    !Array.isArray(row.assets) ||
    !row.assets.every((a) => keysExactly(a, ASSET_KEYS) && isString(a.asset_id) && isString(a.asset_code) && isNullableString(a.display_name))
  ) {
    return false;
  }
  const literals = HEALTH_ROW_LITERALS[kind];
  return (
    row.next_evidence === literals.next_evidence &&
    literals.tuples.some(
      (t) => t.condition_state === row.condition_state && t.observation === row.observation && t.limitation === row.limitation,
    )
  );
}

/** C3: exact `health` key sets, the three rows in kind order, and each row's C1 literal tuple. */
export function isColdHealth(value: unknown): value is ColdHealthRead["health"] {
  if (!keysExactly(value, HEALTH_KEYS) || !isNullableString(value.foundation_revision_id)) return false;
  const rows = value.rows;
  return Array.isArray(rows) && rows.length === HEALTH_KINDS.length && HEALTH_KINDS.every((kind, index) => isHealthRow(rows[index], kind));
}

export function isColdHealthRead(value: unknown): value is ColdHealthRead {
  return isHead(value, TOP_HEALTH) && isColdHealth(value.health);
}

/* ---------- reads ---------- */

async function read<T>(url: string, shape: (value: unknown) => boolean): Promise<ColdRead<T>> {
  let response: Response;
  try {
    response = await fetch(url);
  } catch {
    return { status: "unavailable", message: null };
  }
  let body: unknown = null;
  try {
    body = await response.json();
  } catch {
    body = null;
  }
  if (response.ok) {
    return shape(body)
      ? { status: "loaded", value: body as T }
      : { status: "unavailable", message: "The cold depth read answered in an unexpected shape." };
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
  return { status: "unavailable", message: null };
}

export function createColdDepthClient(basePath: string = SITES_API_PATH): ColdDepthClient {
  const base = (siteCode: string) => `${basePath}/${encodeURIComponent(siteCode)}/cold`;
  return {
    getCooling: (siteCode, window) => read(`${base(siteCode)}/cooling${coldWindowSearch(window)}`, isColdCoolingRead),
    getHealth: (siteCode, window) => read(`${base(siteCode)}/health${coldWindowSearch(window)}`, isColdHealthRead),
  };
}

/** C2 card labels from `cooling.policy_high_deg_c`, the value inserted verbatim (`"4"` gives `4°C`). */
export function coolingCardLabels(policyHigh: string | null): { usual: string; current: string } {
  const target = policyHigh === null ? "policy" : `${policyHigh}°C`;
  return { usual: `Usual time back to ${target}`, current: `This time back to ${target}` };
}
