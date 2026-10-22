/**
 * W5-01b C5: read-only client for a cold-chain Site's authored scenario list (`.agent/W5-01-build-spec.md` C4 GET
 * list DTO, C5 "Client" and P-C5-9..16 validator rules):
 *
 *   GET /api/sites/{site_code}/cold/financials/scenarios?from=&to=&known_at=&scenario_at=&cursor=
 *
 * A 200 answer is accepted only when every key set is exactly the `cold-scenarios-1` key set (order-insensitive),
 * every ID is a lowercase UUID, every clock a UTC ISO instant, and every ID array sorted and deduplicated; anything
 * else is malformed and is returned as `unavailable`, never as an empty list. Refusals are `{error:{code,message}}`
 * and are returned as `refused`. There is no write here: an ordinary viewer has no create control.
 */
import { SITES_API_PATH } from "./siteDirectoryClient";
import { isObject } from "./evidenceRead";
import type { ColdRead, ColdWindowQuery } from "./coldAssessmentClient";

export const COLD_SCENARIOS_SCHEMA_VERSION = "cold-scenarios-1";
export const COLD_SCENARIO_KIND = "STOCK_VALUE_CONTEXT";
export const COLD_SCENARIOS_STATES = ["CURRENT", "PENDING_RECOMPUTE", "STALE_SOURCE", "HISTORICAL", "UNKNOWN"] as const;
export type ColdScenariosState = (typeof COLD_SCENARIOS_STATES)[number];
export const COLD_SCENARIOS_MALFORMED = "The cold scenarios read answered in an unexpected shape.";

export interface ColdScenarioQuery extends ColdWindowQuery {
  scenario_at: string | null;
}

export interface ColdScenarioProvenance {
  classification: string;
  state: string;
  source_ids: string[];
  evidence_ids: string[];
  basis_sha256: string | null;
  reasons: unknown[];
  detail?: Record<string, unknown>;
}

export interface ColdScenarioAssumptions {
  stock_quantity: string;
  stock_unit: string;
  unit_value: string;
  currency: string;
}

export interface ColdScenarioBasis {
  from: string;
  to: string;
  cutoff: string | null;
  assessment_revision_ids: string[];
  accepted_evidence_ids: string[];
  foundation_revision_id: string | null;
  source_provenance: ColdScenarioProvenance;
}

export interface ColdScenarioItem {
  id: string;
  code: string;
  revision_id: string;
  revision_no: number;
  name: string;
  kind: typeof COLD_SCENARIO_KIND;
  assumptions: ColdScenarioAssumptions;
  authored_basis: ColdScenarioBasis;
  recorded_at: string;
  scenario_state: "DEFINED" | "HISTORICAL";
}

export interface ColdScenariosRead {
  schema_version: typeof COLD_SCENARIOS_SCHEMA_VERSION;
  site_id: string;
  window: { from: string | null; to: string | null; known_at: string | null; committed_watermark: string | null };
  scenario_at: string;
  selection: {
    state: ColdScenariosState;
    assessment_revision_ids: string[];
    accepted_evidence_ids: string[];
    source_provenance: ColdScenarioProvenance;
  };
  items: ColdScenarioItem[];
  next_cursor: string | null;
}

export interface ColdScenariosClient {
  /** One page: `cursor` null for the first page. */
  list(siteCode: string, query: ColdScenarioQuery, cursor: string | null): Promise<ColdRead<ColdScenariosRead>>;
}

/* ---------- exact validation ---------- */

const TOP_KEYS = ["schema_version", "site_id", "window", "scenario_at", "selection", "items", "next_cursor"] as const;
const WINDOW_KEYS = ["from", "to", "known_at", "committed_watermark"] as const;
const SELECTION_KEYS = ["state", "assessment_revision_ids", "accepted_evidence_ids", "source_provenance"] as const;
const ITEM_KEYS = [
  "id",
  "code",
  "revision_id",
  "revision_no",
  "name",
  "kind",
  "assumptions",
  "authored_basis",
  "recorded_at",
  "scenario_state",
] as const;
const ASSUMPTION_KEYS = ["stock_quantity", "stock_unit", "unit_value", "currency"] as const;
const BASIS_KEYS = [
  "from",
  "to",
  "cutoff",
  "assessment_revision_ids",
  "accepted_evidence_ids",
  "foundation_revision_id",
  "source_provenance",
] as const;
/** The C1 public provenance keys (`evidence/public_provenance.py` `_PUBLIC_KEYS`), with the optional `detail`. */
const PROVENANCE_KEYS = ["classification", "state", "source_ids", "evidence_ids", "basis_sha256", "reasons"] as const;

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
const UTC_INSTANT = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|\+00:00)$/;
const CODE = /^CSCN-\d{6,}$/;
const CURRENCY = /^[A-Z]{3}$/;

function keysExactly(value: unknown, keys: readonly string[]): value is Record<string, unknown> {
  if (!isObject(value) || Array.isArray(value)) return false;
  const own = Object.keys(value);
  return own.length === keys.length && keys.every((key) => Object.prototype.hasOwnProperty.call(value, key));
}

const isString = (value: unknown): value is string => typeof value === "string";
export const isUuid = (value: unknown): value is string => isString(value) && UUID.test(value);
export const isUtcInstant = (value: unknown): value is string =>
  isString(value) && UTC_INSTANT.test(value) && !Number.isNaN(new Date(value).getTime());
/** Lowercase UUIDs, sorted ascending, no repeats. */
export const isIdSet = (value: unknown): value is string[] =>
  Array.isArray(value) && value.every(isUuid) && value.every((id, i) => i === 0 || (value[i - 1] as string) < id);

export function isProvenance(value: unknown): value is ColdScenarioProvenance {
  if (!isObject(value) || Array.isArray(value)) return false;
  const withDetail = Object.prototype.hasOwnProperty.call(value, "detail");
  if (!keysExactly(value, withDetail ? [...PROVENANCE_KEYS, "detail"] : PROVENANCE_KEYS)) return false;
  if (withDetail && (!isObject(value.detail) || Array.isArray(value.detail))) return false;
  return (
    isString(value.classification) &&
    isString(value.state) &&
    Array.isArray(value.source_ids) &&
    value.source_ids.every(isString) &&
    Array.isArray(value.evidence_ids) &&
    value.evidence_ids.every(isString) &&
    (value.basis_sha256 === null || isString(value.basis_sha256)) &&
    Array.isArray(value.reasons)
  );
}

/** `known_at` and a cutoff may be null only on an unavailable (`UNKNOWN`) selection. */
function isClock(value: unknown, nullable: boolean): boolean {
  return value === null ? nullable : isUtcInstant(value);
}

export function isAssumptions(value: unknown): value is ColdScenarioAssumptions {
  return (
    keysExactly(value, ASSUMPTION_KEYS) &&
    ASSUMPTION_KEYS.every((key) => isString(value[key])) &&
    CURRENCY.test(value.currency as string)
  );
}

export function isBasis(value: unknown, unavailable: boolean): value is ColdScenarioBasis {
  return (
    keysExactly(value, BASIS_KEYS) &&
    isUtcInstant(value.from) &&
    isUtcInstant(value.to) &&
    isClock(value.cutoff, unavailable) &&
    isIdSet(value.assessment_revision_ids) &&
    isIdSet(value.accepted_evidence_ids) &&
    (value.foundation_revision_id === null || isUuid(value.foundation_revision_id)) &&
    isProvenance(value.source_provenance)
  );
}

export function isItem(value: unknown, unavailable: boolean): value is ColdScenarioItem {
  return (
    keysExactly(value, ITEM_KEYS) &&
    isUuid(value.id) &&
    isString(value.code) &&
    CODE.test(value.code) &&
    isUuid(value.revision_id) &&
    typeof value.revision_no === "number" &&
    Number.isInteger(value.revision_no) &&
    value.revision_no >= 1 &&
    isString(value.name) &&
    value.name.length >= 1 &&
    value.name.length <= 160 &&
    value.kind === COLD_SCENARIO_KIND &&
    isAssumptions(value.assumptions) &&
    isBasis(value.authored_basis, unavailable) &&
    isUtcInstant(value.recorded_at) &&
    (value.scenario_state === "DEFINED" || value.scenario_state === "HISTORICAL")
  );
}

export function isColdScenariosRead(value: unknown): value is ColdScenariosRead {
  if (!keysExactly(value, TOP_KEYS)) return false;
  if (value.schema_version !== COLD_SCENARIOS_SCHEMA_VERSION || !isUuid(value.site_id)) return false;
  const selection = value.selection;
  if (
    !keysExactly(selection, SELECTION_KEYS) ||
    !isString(selection.state) ||
    !(COLD_SCENARIOS_STATES as readonly string[]).includes(selection.state) ||
    !isIdSet(selection.assessment_revision_ids) ||
    !isIdSet(selection.accepted_evidence_ids) ||
    !isProvenance(selection.source_provenance)
  ) {
    return false;
  }
  const unavailable = selection.state === "UNKNOWN";
  const window = value.window;
  if (
    !keysExactly(window, WINDOW_KEYS) ||
    !isClock(window.from, true) ||
    !isClock(window.to, true) ||
    (window.from === null) !== (window.to === null) ||
    !isClock(window.known_at, unavailable) ||
    !isClock(window.committed_watermark, true)
  ) {
    return false;
  }
  if (!isUtcInstant(value.scenario_at)) return false;
  if (!(value.next_cursor === null || isString(value.next_cursor))) return false;
  return Array.isArray(value.items) && value.items.every((item) => isItem(item, unavailable));
}

/* ---------- read ---------- */

/** The page address: the first page carries the set window clocks and `scenario_at`; a later page only its cursor. */
export function coldScenariosSearch(query: ColdScenarioQuery, cursor: string | null): string {
  const params = new URLSearchParams();
  if (cursor !== null) {
    params.set("cursor", cursor);
  } else {
    for (const key of ["from", "to", "known_at", "scenario_at"] as const) {
      const value = query[key];
      if (value !== null) params.set(key, value);
    }
  }
  const text = params.toString();
  return text === "" ? "" : `?${text}`;
}

export class HttpColdScenariosClient implements ColdScenariosClient {
  constructor(private readonly basePath: string = SITES_API_PATH) {}

  async list(siteCode: string, query: ColdScenarioQuery, cursor: string | null): Promise<ColdRead<ColdScenariosRead>> {
    const url = `${this.basePath}/${encodeURIComponent(siteCode)}/cold/financials/scenarios${coldScenariosSearch(query, cursor)}`;
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
      return isColdScenariosRead(body) ? { status: "loaded", value: body } : { status: "unavailable", message: COLD_SCENARIOS_MALFORMED };
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
}
