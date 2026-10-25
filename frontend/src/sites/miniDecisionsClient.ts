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

/** A recovery the page itself can offer beside the refusal copy; a closed gate offers none. */
export type DecisionRefusalAction = "first-page" | null;

export const DECISIONS_CLOSED =
  "Decisions are closed while the Performance assessment is unavailable. Try again when it opens.";
export const DECISIONS_UNAVAILABLE = "Decisions are unavailable right now. Try again.";

/** post-W6 W4 R311/R321 (Q4): exact codes first, then the HTTP status; never a raw code or server message. */
const DECISION_CODE_COPY: Record<string, { copy: string; action: DecisionRefusalAction }> = {
  PERFORMANCE_CUTOVER_CLOSED: { copy: DECISIONS_CLOSED, action: null },
  DECISION_BASIS_CHANGED: { copy: "The evidence changed. Reload this page.", action: null },
  INVALID_KNOWN_AT: { copy: "Choose a valid evidence cutoff.", action: null },
  INVALID_WINDOW: { copy: "Choose a valid Site-local window.", action: null },
  INVALID_CURSOR: { copy: "This page of results expired. Return to the first page.", action: "first-page" },
  DECISION_DUPLICATE_KEY: { copy: "This change conflicts with a recorded decision. Reload this page.", action: null },
  DECISION_CORRECTION_CONFLICT: { copy: "This change conflicts with a recorded decision. Reload this page.", action: null },
};

/** u6b ruling 9 / post-W6 W4 Q4: the decision-read refusal copy and offered action, shared by every decision mount. */
export function decisionRefusal(read: Exclude<DecisionRead<unknown>, { status: "loaded" }>): {
  copy: string;
  action: DecisionRefusalAction;
} {
  if (read.status === "refused") {
    const byCode = DECISION_CODE_COPY[read.code];
    if (byCode !== undefined) return byCode;
    if (read.httpStatus === 401) return { copy: "Sign in to see this page.", action: null };
    if (read.httpStatus === 403) return { copy: "You do not have access to this site.", action: null };
    if (read.httpStatus === 404) return { copy: "This decision was not found at this site.", action: null };
    if (read.httpStatus === 422) return { copy: "This request cannot be used. Check your entries and try again.", action: null };
    if (read.httpStatus === 409) return { copy: "The decision could not be recorded. Reload this page.", action: null };
  }
  return { copy: DECISIONS_UNAVAILABLE, action: null };
}

/** The copy alone, for mounts that offer no recovery control. */
export function decisionRefusalCopy(read: Exclude<DecisionRead<unknown>, { status: "loaded" }>): string {
  return decisionRefusal(read).copy;
}

/** u6b ruling 11: a later Alternatives page reuses the returned cutoff and cursor; the first page sends neither. */
export interface AlternativesPage {
  known_at: string | null;
  cursor: string | null;
  limit?: number | null;
}

/** W4-03 unit 8 (u5): one explicit decision association of a W4-01 case at the list cutoff. */
export interface WorkDecisionContext {
  kind: "OPPORTUNITY" | "SCENARIO";
  id: string;
  label: string;
  url: string | null;
}

export interface WorkContextsBody {
  schema_version: "mini-work-contexts-1";
  known_at: string;
  contexts: Record<string, WorkDecisionContext[]>;
}

export interface MiniDecisionsClient {
  getScenarios(siteCode: string, scope: ScenarioScope): Promise<DecisionRead<ScenarioListBody>>;
  getAlternatives(
    siteCode: string,
    findingId: string,
    revisionId: string,
    page?: AlternativesPage,
  ): Promise<DecisionRead<AlternativeListBody>>;
  /**
   * PR-12.6: zero or one `known_at` is the wire contract; every value the address carried is sent unchanged so a
   * duplicate, future or invalid cutoff is the server's own refusal. Omitted means current time.
   */
  getOpportunity(
    siteCode: string,
    opportunityId: string,
    knownAt?: string | readonly string[] | null,
  ): Promise<DecisionRead<OpportunityDetailBody>>;
  listOpportunities(
    siteCode: string,
    window: { from: string; to: string; known_at: string | null },
  ): Promise<DecisionRead<OpportunityListBody>>;
  /** The Site Work overlay: every requested case key, read at the W4-01 list's exact `known_at`. */
  getWorkContexts(siteCode: string, caseIds: string[], knownAt: string): Promise<DecisionRead<WorkContextsBody>>;
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

const isWorkContexts = (value: unknown): boolean =>
  isObject(value) &&
  value.schema_version === "mini-work-contexts-1" &&
  typeof value.known_at === "string" &&
  isObject(value.contexts) &&
  Object.values(value.contexts).every((list) => Array.isArray(list));

export function createMiniDecisionsClient(basePath: string = SITES_API_PATH): MiniDecisionsClient {
  const site = (code: string) => `${basePath}/${encodeURIComponent(code)}`;
  return {
    getScenarios: (code, scope) =>
      readDecision(`${site(code)}/financials/scenarios${scenarioScopeSearch(scope)}`, isScenarioList),
    getAlternatives: (code, findingId, revisionId, page) => {
      const params = new URLSearchParams({ revision_id: revisionId });
      if (page?.known_at) params.set("known_at", page.known_at);
      if (page?.cursor) params.set("cursor", page.cursor);
      if (page?.limit) params.set("limit", String(page.limit));
      return readDecision(
        `${site(code)}/findings/${encodeURIComponent(findingId)}/alternatives?${params.toString()}`,
        isAlternativeList,
      );
    },
    getOpportunity: (code, opportunityId, knownAt) => {
      const params = new URLSearchParams();
      for (const k of knownAtValues(knownAt)) params.append("known_at", k);
      const query = params.toString();
      return readDecision(
        `${site(code)}/opportunities/${encodeURIComponent(opportunityId)}${query === "" ? "" : `?${query}`}`,
        isOpportunityDetail,
      );
    },
    listOpportunities: (code, window) => {
      const params = new URLSearchParams({ from: window.from, to: window.to, limit: "100" });
      if (window.known_at !== null) params.set("known_at", window.known_at);
      return readDecision(`${site(code)}/opportunities?${params.toString()}`, isOpportunityList);
    },
    getWorkContexts: (code, caseIds, knownAt) => {
      const params = new URLSearchParams({ case_ids: caseIds.join(","), known_at: knownAt });
      return readDecision(`${site(code)}/work/decision-contexts?${params.toString()}`, isWorkContexts);
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

/** PR-12.6: the detail cutoff(s) as an ordered list (none, one, or every duplicate the address carried). */
export function knownAtValues(knownAt: string | readonly string[] | null | undefined): readonly string[] {
  if (knownAt === null || knownAt === undefined) return [];
  return typeof knownAt === "string" ? [knownAt] : knownAt;
}
