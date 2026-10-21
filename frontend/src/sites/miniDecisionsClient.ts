/**
 * W4-03 unit 6: the read-only mini decision reads. The route token is the public Site code (`site_id` in Site detail).
 *
 * - `GET /api/sites/{site_code}/financials/scenarios` (`mini-scenarios-1`): the first request omits both bounds; the
 *   server resolves creation-time `[1970-01-01, read_time + 1 microsecond)` and returns them with `known_at`, which
 *   the page reuses for every cursor page and reload (closure 4 S15, u5 unit 6a).
 *
 * - `GET /api/sites/{site_code}/findings/{finding_id}/alternatives?revision_id=` (`mini-alternatives-1`, unit 6b):
 *   the authored alternatives of one exact W1 Finding revision. The caller passes the revision resolved by the W1
 *   Finding read (u6 ruling 5), never a raw missing query parameter.
 *
 * - `GET /api/sites/{site_code}/opportunities/{opportunity_id}` (`mini-opportunity-detail-1`, unit 7): one typed
 *   five-day opportunity; and `GET /api/sites/{site_code}/opportunities?from=&to=&known_at=&limit=`
 *   (`mini-opportunities-1`), the scoped list the W4-02 renewable CTA filters for the exact five-day study (S14).
 *
 * The frontend has no write path: no scenario drawer or create form (closure 1).
 */
import { SITES_API_PATH } from "./siteDirectoryClient";

export interface DecisionLimitation {
  code: string;
  evidence_ids: string[];
}

export interface ScenarioAssumption {
  key: string;
  value: string | null;
  unit: string | null;
  source: string;
}

export interface ScenarioRow {
  id: string;
  code: string;
  revision_id: string;
  name: string;
  kind: string;
  narrative: string;
  authored_at: string;
  actor_id: string;
  assumptions: ScenarioAssumption[];
  pinned_mini_revision_ids: string[];
  scenario_state: "DEFINED" | "HISTORICAL" | string;
  calculation_state: string;
  energy_kwh: string | null;
  gross_sales: { amount: string; currency: string; basis: string } | null;
  limitations: DecisionLimitation[];
  url: string | null;
}

export interface ScenarioListBody {
  schema_version: string;
  window: { from: string | null; to: string | null; known_at: string | null };
  status: string;
  currentness: { state: string; job_state: string };
  total_count: number;
  rows: ScenarioRow[];
  next_cursor: string | null;
  selection_token: string | null;
  limitations?: DecisionLimitation[];
}

export interface AlternativeRow {
  id: string;
  revision_id: string;
  finding_revision_id: string;
  explanation: string;
  evidence_summary: string;
  cited_accepted_evidence_ids: string[];
  missing_evidence_reason: string | null;
  disposition: "PLAUSIBLE" | "CANNOT_EXCLUDE" | "INDETERMINATE" | "RULED_OUT" | string;
  reason: string;
  review_state: "CURRENT" | "HISTORICAL" | "NEEDS_REVIEW" | string;
}

export interface AlternativeListBody {
  schema_version: string;
  window: { from: string | null; to: string | null; known_at: string | null };
  status: string;
  currentness: { state: string; job_state: string };
  total_count: number;
  rows: AlternativeRow[];
  next_cursor: string | null;
  selection_token: string | null;
}

export interface OpportunityBound {
  low: string;
  high: string;
}

export interface OpportunityDayRow {
  local_day: string;
  decision: string | null;
  opportunity_kwh: OpportunityBound | null;
  constraints: string[];
  evidence_ids: string[];
  selection_seq: number | null;
  mini_revision_id: string | null;
}

export interface OpportunityObject {
  id: string;
  code: string;
  revision_id: string | null;
  revision_no: number | null;
  first_day: string;
  last_day: string;
  model_version: string;
  study_days: number;
  eligible_days: number | null;
  assessed_days: number | null;
  headroom_kw: OpportunityBound | null;
  proposed_load_kw: string | null;
  gross_sales_scenario: { amount: string; currency: string; basis: string } | null;
  demand_state: string;
  collection_state: string;
  scenario_id: string | null;
  day_rows: OpportunityDayRow[];
}

export interface DecisionSourceBlock {
  classification: string | null;
  [key: string]: unknown;
}

export interface OpportunityRowBody {
  opportunity: OpportunityObject | null;
  status: "SUPPORTED" | "LIMITED" | "UNKNOWN" | string;
  currentness: { state: string; job_state: string; selection_seq?: number | null; selected_at?: string | null };
  source_provenance?: DecisionSourceBlock | null;
  selected_source_provenance: DecisionSourceBlock | null;
  pending_source_provenance: DecisionSourceBlock | null;
  limitations: DecisionLimitation[];
}

export interface OpportunityDetailBody extends OpportunityRowBody {
  schema_version: string;
  history: { revision_id: string; revision_no: number; status: string; current: boolean; selected_at: string }[];
  scenario_links: { id: string; scenario_id: string; selected: boolean; compatible: boolean }[];
  links: { renewable: string | null; site_work: string | null; scenario: string | null };
}

export interface OpportunityListBody {
  schema_version: string;
  window: { from: string | null; to: string | null; known_at: string | null };
  total_count: number;
  rows: OpportunityRowBody[];
  next_cursor: string | null;
}

/** The page's scope: all null on the first request; afterwards the server's own effective bounds and cutoff. */
export interface ScenarioScope {
  from: string | null;
  to: string | null;
  known_at: string | null;
  cursor: string | null;
}

export type DecisionRead<T> =
  | { status: "loaded"; value: T }
  /** The server answered with a refusal envelope `{detail:{code,message}}`. */
  | { status: "refused"; httpStatus: number; code: string; message: string | null }
  /** No answer, or an answer that is not the documented shape. */
  | { status: "unavailable"; message: string | null };

export interface MiniDecisionsClient {
  getScenarios(siteCode: string, scope: ScenarioScope): Promise<DecisionRead<ScenarioListBody>>;
  getAlternatives(siteCode: string, findingId: string, revisionId: string): Promise<DecisionRead<AlternativeListBody>>;
  getOpportunity(siteCode: string, opportunityId: string): Promise<DecisionRead<OpportunityDetailBody>>;
  listOpportunities(
    siteCode: string,
    window: { from: string; to: string; known_at: string | null },
  ): Promise<DecisionRead<OpportunityListBody>>;
}

const isObject = (value: unknown): value is Record<string, unknown> => typeof value === "object" && value !== null;

export function scenarioScopeSearch(scope: ScenarioScope): string {
  const params = new URLSearchParams();
  if (scope.from !== null) params.set("from", scope.from);
  if (scope.to !== null) params.set("to", scope.to);
  if (scope.known_at !== null) params.set("known_at", scope.known_at);
  if (scope.cursor !== null) params.set("cursor", scope.cursor);
  const text = params.toString();
  return text === "" ? "" : `?${text}`;
}

export async function readDecision<T>(url: string, shape: (value: unknown) => boolean): Promise<DecisionRead<T>> {
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
      : { status: "unavailable", message: "The decision read answered in an unexpected shape." };
  }
  const detail = isObject(body) && isObject(body.detail) ? body.detail : null;
  if (detail !== null && typeof detail.code === "string") {
    return {
      status: "refused",
      httpStatus: response.status,
      code: detail.code,
      message: typeof detail.message === "string" ? detail.message : null,
    };
  }
  return { status: "unavailable", message: null };
}

const isScenarioList = (value: unknown): boolean =>
  isObject(value) &&
  value.schema_version === "mini-scenarios-1" &&
  Array.isArray(value.rows) &&
  isObject(value.window) &&
  typeof value.total_count === "number";

const isAlternativeList = (value: unknown): boolean =>
  isObject(value) &&
  value.schema_version === "mini-alternatives-1" &&
  Array.isArray(value.rows) &&
  isObject(value.window) &&
  typeof value.total_count === "number";

const isOpportunityDetail = (value: unknown): boolean =>
  isObject(value) &&
  value.schema_version === "mini-opportunity-detail-1" &&
  isObject(value.currentness) &&
  Array.isArray(value.limitations) &&
  isObject(value.links);

const isOpportunityList = (value: unknown): boolean =>
  isObject(value) &&
  value.schema_version === "mini-opportunities-1" &&
  Array.isArray(value.rows) &&
  typeof value.total_count === "number";

export function createMiniDecisionsClient(basePath: string = SITES_API_PATH): MiniDecisionsClient {
  const site = (code: string) => `${basePath}/${encodeURIComponent(code)}`;
  return {
    getScenarios: (code, scope) =>
      readDecision(`${site(code)}/financials/scenarios${scenarioScopeSearch(scope)}`, isScenarioList),
    getAlternatives: (code, findingId, revisionId) =>
      readDecision(
        `${site(code)}/findings/${encodeURIComponent(findingId)}/alternatives?revision_id=${encodeURIComponent(revisionId)}`,
        isAlternativeList,
      ),
    getOpportunity: (code, opportunityId) =>
      readDecision(`${site(code)}/opportunities/${encodeURIComponent(opportunityId)}`, isOpportunityDetail),
    listOpportunities: (code, window) => {
      const params = new URLSearchParams({ from: window.from, to: window.to, limit: "100" });
      if (window.known_at !== null) params.set("known_at", window.known_at);
      return readDecision(`${site(code)}/opportunities?${params.toString()}`, isOpportunityList);
    },
  };
}

/** The UTC instant one microsecond before a six-digit UTC token (`...ss.ffffffZ`), in the same form (u5 6a). */
export function microsecondBefore(token: string): string | null {
  const m = /^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\.(\d{6})Z$/.exec(token);
  if (m === null) return null;
  const micros = Number(m[2]);
  if (micros > 0) return `${m[1]}.${String(micros - 1).padStart(6, "0")}Z`;
  const second = new Date(Date.parse(`${m[1]}Z`) - 1000).toISOString().slice(0, 19);
  return `${second}.999999Z`;
}
