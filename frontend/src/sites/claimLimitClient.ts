/**
 * S3-02b: the selected-assessment claim-limit read (`I-claim-limit-read`,
 * `backend/assetops_backend/claim_limit_api.py`) and the day's assessed
 * periods it is chosen from (the S3 dispatch window read).
 *
 * The read is bound to one Site, one UTC day and one exact assessment
 * revision; it never swaps in the latest readings. Every refusal is a named
 * state (401, 403, 404, 409, 422, 503), never a thrown error and never an
 * empty success. Both reads take an AbortSignal so a superseded selection's
 * answer is dropped.
 */
import { SITES_API_PATH } from "./siteDirectoryClient";
import { hasKeys, isObject } from "./evidenceRead";

export const CLAIM_LIMIT_RULE_ID = "s3-claim-limit-1";

export type Currentness = "CURRENT" | "STALE_PROJECTION" | "FAILED" | "PENDING" | "HISTORICAL" | "UNASSESSED";
export type Ceiling = "CANDIDATE_AVOIDABLE" | "NECESSARY" | "INDETERMINATE";
export type SpanStatus = "COVERED" | "MISSING" | "POOR_QUALITY" | "CONFLICTED" | "NOT_EVALUATED";

export const REQUIRED_ROLES = [
  "generator_state",
  "feeder_demand",
  "pv_available_power",
  "pcs_discharge_capability",
  "battery_soc",
] as const;

export interface RoleSpan {
  status: SpanStatus | string;
  start: string;
  end: string;
  minutes: number | string;
  evidence_ids: string[];
  problems: string[];
  assessment_revision_id?: string;
}

export interface RoleCapability {
  status: "COVERED" | "INCOMPLETE" | "NO_SPANS" | string;
  covered_minutes: number | string;
  minutes_by_status: Record<string, number | string>;
  evidence_ids: string[];
  spans: RoleSpan[];
}

export interface ClaimReason {
  code: string;
  text: string;
  role?: string;
  start?: string;
  end?: string;
  minutes?: number | string;
  scope?: string;
}

export interface IntervalCeiling {
  assessment_revision_id: string;
  claim_level: string;
  ceiling: Ceiling | null;
  support: string | null;
}

export interface CeilingBody {
  ceiling: Ceiling | null;
  support: string | null;
  supported_minutes: string | null;
  statement: string | null;
  interval_ceilings?: IntervalCeiling[];
}

export interface ClaimLimitBody extends CeilingBody {
  current_positive_claim: boolean;
  historical_ceiling: CeilingBody | null;
  reasons: ClaimReason[];
  rule_id: string;
  model_version?: string;
}

export interface ClaimLimitRead {
  schema: string;
  schema_version: number;
  rule_id: string;
  site_code: string;
  tenant_id: string;
  site_id: string;
  day: string;
  window: { start: string; end: string };
  read_at: string;
  window_status: string;
  window_status_reasons: string[];
  current_selection: { run_id: string; model_version: string; revision_ids: string[] } | null;
  assessment_revision_id: string | null;
  scope?: "INTERVAL" | "WINDOW" | string;
  assessment_key?: string;
  revision_no?: number;
  claim_level?: string;
  currentness: Currentness | string;
  run?: {
    run_id: string;
    model_version: string;
    knowledge_cutoff: string;
    cohort_status: string;
    cohort_sha256: string;
    input_sha256: string;
    configuration_sha256: string;
    foundation_revision_ids: string[];
    binding_set_revision_ids: string[];
    built_at: string;
  } | null;
  accepted_evidence_ids?: string[];
  watermarks?: {
    source: { source_time: string | null; published_at: string | null; received_at: string | null; accepted_at: string | null };
    analytic_built_at: string | null;
  } | null;
  built_at?: string;
  not_inferred: string;
  capability: { roles: Record<string, RoleCapability>; required_roles?: string[]; basis?: string; rule_id?: string } | null;
  claim_limit: ClaimLimitBody | null;
}

/** One assessed period on the day, as the dispatch window read lists it. */
export interface AssessedPeriod {
  id: string;
  scope: "INTERVAL" | "WINDOW";
  start: string;
  end: string;
  claim_level: string;
}

export interface AssessedDay {
  status: string;
  periods: AssessedPeriod[];
}

export type ClaimLimitResult<T> =
  | { status: "loaded"; value: T }
  | { status: "unauthenticated"; message: string | null }
  | { status: "forbidden"; message: string | null }
  | { status: "not_found"; code: string | null; message: string | null }
  | { status: "closed"; message: string | null }
  | { status: "refused"; code: string | null; message: string | null }
  | { status: "unavailable"; code: string | null; message: string | null }
  | { status: "aborted" };

export interface ClaimLimitClient {
  /** `revision` null reads the day's UNASSESSED / "no assessment selected" answer. */
  getClaimLimit(
    siteId: string,
    day: string,
    revision: string | null,
    signal?: AbortSignal,
  ): Promise<ClaimLimitResult<ClaimLimitRead>>;
  getAssessedDay(siteId: string, day: string, signal?: AbortSignal): Promise<ClaimLimitResult<AssessedDay>>;
}

function isClaimLimitRead(value: unknown): value is ClaimLimitRead {
  return hasKeys(value, ["schema", "rule_id", "day", "window", "currentness", "claim_limit", "capability", "read_at"]);
}

interface WindowRevision {
  id: string;
  window_start: string;
  window_end: string;
  claim_level: string;
}

function isWindowRevision(value: unknown): value is WindowRevision {
  return hasKeys(value, ["id", "window_start", "window_end", "claim_level"]);
}

function isWindowBody(value: unknown): value is { status: string; intervals: unknown[]; window_assessment: unknown } {
  return hasKeys(value, ["status", "intervals", "window_assessment"]) && Array.isArray((value as { intervals: unknown }).intervals);
}

async function readJson<T>(
  path: string,
  valid: (value: unknown) => value is T,
  signal?: AbortSignal,
): Promise<ClaimLimitResult<T>> {
  let response: Response;
  try {
    response = await fetch(path, signal === undefined ? undefined : { signal });
  } catch {
    return signal?.aborted ? { status: "aborted" } : { status: "unavailable", code: null, message: null };
  }
  let body: unknown = null;
  try {
    body = await response.json();
  } catch {
    body = null;
  }
  if (signal?.aborted) {
    return { status: "aborted" };
  }
  if (response.ok && valid(body)) {
    return { status: "loaded", value: body };
  }
  const detail = isObject(body) ? body.detail : null;
  const code = isObject(detail) && typeof detail.code === "string" ? detail.code : null;
  const message =
    typeof detail === "string"
      ? detail
      : isObject(detail) && typeof detail.message === "string"
        ? detail.message
        : null;
  switch (response.status) {
    case 401:
      return { status: "unauthenticated", message };
    case 403:
      return { status: "forbidden", message };
    case 404:
      return { status: "not_found", code, message };
    case 409:
      return code === "PERFORMANCE_CUTOVER_CLOSED" ? { status: "closed", message } : { status: "refused", code, message };
    case 422:
      return { status: "refused", code, message };
    default:
      return { status: "unavailable", code, message };
  }
}

export function createClaimLimitClient(basePath: string = SITES_API_PATH): ClaimLimitClient {
  const windowPath = (siteId: string, day: string) =>
    `${basePath}/${encodeURIComponent(siteId)}/performance/dispatch/windows/${encodeURIComponent(day)}`;
  return {
    getClaimLimit(siteId, day, revision, signal) {
      const query = revision === null ? "" : `?revision=${encodeURIComponent(revision)}`;
      return readJson(`${windowPath(siteId, day)}/claim-limit${query}`, isClaimLimitRead, signal);
    },
    async getAssessedDay(siteId, day, signal) {
      const answer = await readJson(windowPath(siteId, day), isWindowBody, signal);
      if (answer.status !== "loaded") {
        return answer;
      }
      const periods: AssessedPeriod[] = [];
      const whole = answer.value.window_assessment;
      if (isWindowRevision(whole)) {
        periods.push({ id: whole.id, scope: "WINDOW", start: whole.window_start, end: whole.window_end, claim_level: whole.claim_level });
      }
      for (const item of answer.value.intervals) {
        if (isWindowRevision(item)) {
          periods.push({ id: item.id, scope: "INTERVAL", start: item.window_start, end: item.window_end, claim_level: item.claim_level });
        }
      }
      return { status: "loaded", value: { status: answer.value.status, periods } };
    },
  };
}
