/**
 * W5-03b E6: read-only client for an EV charging Site's authored scenario list (`.agent/W5-03-build-spec.md` E6 card
 * "Client", E6 consolidated correction and `.agent/W5-03b-ui-preflight-rulings.md` points 11-13):
 *
 *   GET /api/sites/{site_code}/ev/financials/scenarios?from=&to=&known_at=&scenario_at=
 *
 * Only the first page at the API default limit is read; no `limit` or `cursor` is sent (ruling 12). A 200 answer is
 * accepted only when its top-level, window, selection, item, assumption and authored-basis key sets are exact and
 * every value is in its value set. Provenance objects need only a string `classification` (ruling 13). Window clocks
 * and the selected assessment may be null (ruling 11). Anything else is malformed and returned as `unavailable`.
 */
import { SITES_API_PATH } from "./siteDirectoryClient";
import { isObject } from "./evidenceRead";
import type { ColdRead, ColdWindowQuery } from "./coldAssessmentClient";

export const EV_SCENARIOS_SCHEMA_VERSION = "ev-scenarios-1";
export const EV_SCENARIO_KIND = "GROSS_TARIFF_CONTEXT";
export const EV_SCENARIOS_STATES = ["CURRENT", "PENDING_RECOMPUTE", "STALE_SOURCE", "HISTORICAL", "UNKNOWN"] as const;
export type EvScenariosState = (typeof EV_SCENARIOS_STATES)[number];
export const EV_SCENARIOS_UNREACHABLE = "The EV scenarios read could not be reached.";
export const EV_SCENARIOS_MALFORMED = "The EV scenarios read answered in an unexpected shape.";

export interface EvScenarioQuery extends ColdWindowQuery {
  /** The authored clock; null reads at the current authored time. */
  scenario_at: string | null;
}

/** A public provenance object; only `classification` is read (ruling 13), other public fields are kept as given. */
export type EvScenarioProvenance = { classification: string } & Record<string, unknown>;

export interface EvScenarioBasis {
  from: string;
  to: string;
  cutoff: string;
  assessment_revision_id: string | null;
  session_revision_ids: string[];
  accepted_evidence_ids: string[];
  foundation_revision_id: string | null;
  consequence_revision_id: string | null;
  tariff_revision_id: string | null;
  source_provenance: EvScenarioProvenance;
}

export interface EvScenarioItem {
  id: string;
  code: string;
  revision_id: string;
  revision_no: number;
  name: string;
  kind: typeof EV_SCENARIO_KIND;
  assumptions: { tariff_per_kwh: string; currency: string };
  authored_basis: EvScenarioBasis;
  recorded_at: string;
  scenario_state: "DEFINED" | "HISTORICAL";
}

export interface EvScenariosRead {
  schema_version: typeof EV_SCENARIOS_SCHEMA_VERSION;
  site_id: string;
  window: { from: string | null; to: string | null; known_at: string | null; committed_watermark: string | null };
  scenario_at: string;
  selection: {
    state: EvScenariosState;
    assessment_revision_id: string | null;
    session_revision_ids: string[];
    accepted_evidence_ids: string[];
    source_provenance: EvScenarioProvenance;
  };
  items: EvScenarioItem[];
  next_cursor: string | null;
}

export interface EvScenariosClient {
  list(siteCode: string, query: EvScenarioQuery): Promise<ColdRead<EvScenariosRead>>;
}

/* ---------- exact validation ---------- */

const TOP_KEYS = ["schema_version", "site_id", "window", "scenario_at", "selection", "items", "next_cursor"];
const WINDOW_KEYS = ["from", "to", "known_at", "committed_watermark"];
const SELECTION_KEYS = ["state", "assessment_revision_id", "session_revision_ids", "accepted_evidence_ids", "source_provenance"];
const ITEM_KEYS = ["id", "code", "revision_id", "revision_no", "name", "kind", "assumptions", "authored_basis", "recorded_at", "scenario_state"];
const BASIS_KEYS = [
  "from",
  "to",
  "cutoff",
  "assessment_revision_id",
  "session_revision_ids",
  "accepted_evidence_ids",
  "foundation_revision_id",
  "consequence_revision_id",
  "tariff_revision_id",
  "source_provenance",
];

const isString = (value: unknown): value is string => typeof value === "string";
const isNullableString = (value: unknown): value is string | null => value === null || isString(value);
const isStringArray = (value: unknown): value is string[] => Array.isArray(value) && value.every(isString);

function keysExactly(value: unknown, keys: readonly string[]): value is Record<string, unknown> {
  if (!isObject(value) || Array.isArray(value)) return false;
  const own = Object.keys(value);
  return own.length === keys.length && keys.every((key) => Object.prototype.hasOwnProperty.call(value, key));
}

/** Ruling 13: a non-array object with a string `classification`; other public fields are not enumerated. */
export function isScenarioProvenance(value: unknown): value is EvScenarioProvenance {
  return isObject(value) && !Array.isArray(value) && isString(value.classification);
}

function isBasis(value: unknown): value is EvScenarioBasis {
  return (
    keysExactly(value, BASIS_KEYS) &&
    isString(value.from) &&
    isString(value.to) &&
    isString(value.cutoff) &&
    isNullableString(value.assessment_revision_id) &&
    isStringArray(value.session_revision_ids) &&
    isStringArray(value.accepted_evidence_ids) &&
    isNullableString(value.foundation_revision_id) &&
    isNullableString(value.consequence_revision_id) &&
    isNullableString(value.tariff_revision_id) &&
    isScenarioProvenance(value.source_provenance)
  );
}

function isItem(value: unknown): value is EvScenarioItem {
  if (!keysExactly(value, ITEM_KEYS)) return false;
  const a = value.assumptions;
  return (
    isString(value.id) &&
    isString(value.code) &&
    /^ESCN-\d{6,}$/.test(value.code) &&
    isString(value.revision_id) &&
    typeof value.revision_no === "number" &&
    Number.isInteger(value.revision_no) &&
    value.revision_no >= 1 &&
    isString(value.name) &&
    value.name.length >= 1 &&
    value.name.length <= 160 &&
    value.kind === EV_SCENARIO_KIND &&
    keysExactly(a, ["tariff_per_kwh", "currency"]) &&
    isString(a.tariff_per_kwh) &&
    isString(a.currency) &&
    /^[A-Z]{3}$/.test(a.currency) &&
    isBasis(value.authored_basis) &&
    isString(value.recorded_at) &&
    (value.scenario_state === "DEFINED" || value.scenario_state === "HISTORICAL")
  );
}

export function isEvScenariosRead(value: unknown): value is EvScenariosRead {
  if (!keysExactly(value, TOP_KEYS)) return false;
  const w = value.window;
  const s = value.selection;
  return (
    value.schema_version === EV_SCENARIOS_SCHEMA_VERSION &&
    isString(value.site_id) &&
    keysExactly(w, WINDOW_KEYS) &&
    WINDOW_KEYS.every((key) => isNullableString(w[key])) &&
    isString(value.scenario_at) &&
    keysExactly(s, SELECTION_KEYS) &&
    (EV_SCENARIOS_STATES as readonly unknown[]).includes(s.state) &&
    isNullableString(s.assessment_revision_id) &&
    isStringArray(s.session_revision_ids) &&
    isStringArray(s.accepted_evidence_ids) &&
    isScenarioProvenance(s.source_provenance) &&
    Array.isArray(value.items) &&
    value.items.every(isItem) &&
    isNullableString(value.next_cursor)
  );
}

/* ---------- read ---------- */

export function evScenariosSearch(query: EvScenarioQuery): string {
  const params = new URLSearchParams();
  if (query.from !== null) params.set("from", query.from);
  if (query.to !== null) params.set("to", query.to);
  if (query.known_at !== null) params.set("known_at", query.known_at);
  if (query.scenario_at !== null) params.set("scenario_at", query.scenario_at);
  const text = params.toString();
  return text === "" ? "" : `?${text}`;
}

export function createEvScenariosClient(basePath: string = SITES_API_PATH): EvScenariosClient {
  return {
    async list(siteCode, query) {
      const url = `${basePath}/${encodeURIComponent(siteCode)}/ev/financials/scenarios${evScenariosSearch(query)}`;
      let response: Response;
      try {
        response = await fetch(url);
      } catch {
        return { status: "unavailable", message: EV_SCENARIOS_UNREACHABLE };
      }
      let body: unknown = null;
      try {
        body = await response.json();
      } catch {
        body = null;
      }
      if (response.ok) {
        return isEvScenariosRead(body) ? { status: "loaded", value: body } : { status: "unavailable", message: EV_SCENARIOS_MALFORMED };
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
      return { status: "unavailable", message: EV_SCENARIOS_MALFORMED };
    },
  };
}
