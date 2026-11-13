/**
 * SR-7a / SR-7b / SR-11 (sequence doc rev 10 §10.3, rev 10b.3): the per-day range reads of one mini-grid Site.
 *
 * - `GET /api/sites/{code}/service-range?from&to[&known_at]` (`site-service-range-1`)
 * - `GET /api/sites/{code}/backup-range?from&to[&known_at]` (`site-backup-range-1`)
 * - `GET /api/sites/{code}/claim-limit-range?from&to[&known_at]` (`site-claim-limit-range-1`)
 *
 * A 503 `SITE_*_RANGE_UNAVAILABLE` (or INFRA-1's `TEMPORARILY_UNAVAILABLE`) is retried after 2, 4 and 8 s while the
 * page shows "Temporarily unavailable. Retrying…"; it is never a data state. Every other refusal is a named state.
 */
import { SITES_API_PATH } from "./siteDirectoryClient";
import { RETRY_DELAYS_MS, TEMPORARILY_UNAVAILABLE } from "./temporarilyUnavailable";

export interface RangeWindowQuery {
  from: string;
  to: string;
  known_at: string | null;
}

export interface RangeSite {
  site_code: string;
  site_name?: string | null;
  timezone: string | null;
}

export interface RangeWindow {
  from: string;
  to: string;
  known_at: string | null;
  basis?: string;
}

/* ---------- SR-7a Service (`mini_depth/service_range.py`) ---------- */

export type ServiceDayState =
  | "SERVED_ALL"
  | "SHORTFALL"
  | "NO_VALUE"
  | "NO_READINGS"
  | "NOT_ENOUGH_READINGS"
  | "STILL_PROCESSING"
  | "NOT_EXPECTED";

export interface ServiceRangeDay {
  local_day: string;
  grade: string | null;
  served_kwh: string | number | null;
  unserved_kwh: string | number | null;
  demand_kwh: string | number | null;
  covered_hours: number | null;
  operating_hours: number | null;
  state: ServiceDayState | string;
  partial: boolean;
  hour_link: string;
}

export interface ServiceRangeBody {
  schema_version: "site-service-range-1";
  site: RangeSite;
  window: RangeWindow;
  days: ServiceRangeDay[];
  totals: {
    served_kwh: string | null;
    unserved_kwh: string | null;
    demand_kwh: string | null;
    days_counted: number;
    days_requested: number;
  };
}

/* ---------- SR-11 Backup (`mini_depth/day_summary.py`) ---------- */

export interface BackupRangeSequence {
  chain_id: string;
  outage_start: string | null;
  result: "PASS" | "FAIL" | "INCOMPLETE" | string | null;
  service_outcome: string | null;
  critical_recovery: { seconds: number | null; target_seconds: number | null } | null;
}

export interface SequenceCounts {
  PASS: number;
  FAIL: number;
  INCOMPLETE: number;
}

export interface BackupRangeDay {
  local_day: string;
  stored: boolean;
  hours_expected: number | null;
  hours_assessed: number | null;
  hours_pending: number | null;
  hours_missing: number | null;
  status_counts: Record<string, number> | null;
  limitations: string[] | null;
  sequences: BackupRangeSequence[] | null;
  sequence_counts: SequenceCounts | null;
  start_success_count: number | null;
  slowest_recovery: { seconds: number; target_seconds: number | null } | null;
  state: string;
  partial: boolean;
  hour_link: string;
}

export interface BackupRangeBody {
  schema_version: "site-backup-range-1";
  site: RangeSite;
  window: RangeWindow;
  days: BackupRangeDay[];
  totals: {
    days_counted: number;
    days_requested: number;
    partial: boolean;
    sequence_counts: SequenceCounts;
    start_success_count: number | null;
  };
}

/* ---------- SR-7b claim limit (`estate/claim_limit_range.py`) ---------- */

export interface ClaimLimitRangeDay {
  day: string;
  revision_id: string | null;
  available: boolean;
  /** `reduce_day`: FULL, LIMITED, NONE, CONTRADICTORY, UNKNOWN; or NO_SELECTION (no window revision). */
  state: string;
  current_ceiling: string | null;
  ceiling_statement: string | null;
  window_assessment_revision_id: string | null;
  gap_count: number;
  reasons: Array<{ code: string; text?: string; role?: string }>;
  link: string | null;
}

export interface ClaimLimitRangeBody {
  schema_version: "site-claim-limit-range-1";
  site: RangeSite;
  window: RangeWindow;
  days: ClaimLimitRangeDay[];
  summary: {
    days_with_positive_claim: number;
    days_indeterminate: number;
    days_without_selection: number;
    days_requested: number;
  };
}

/* ---------- the read ---------- */

export type RangeRead<T> =
  | { status: "loaded"; value: T }
  /** The server answered a named refusal (401, 403, 404, 409, 422). */
  | { status: "refused"; httpStatus: number; code: string | null; message: string | null }
  /** Still unavailable after the last retry, no answer, or not the documented shape. */
  | { status: "unavailable"; code: string | null };

export interface SiteRangeClient {
  getServiceRange(siteCode: string, window: RangeWindowQuery, onRetrying?: () => boolean): Promise<RangeRead<ServiceRangeBody>>;
  getBackupRange(siteCode: string, window: RangeWindowQuery, onRetrying?: () => boolean): Promise<RangeRead<BackupRangeBody>>;
  getClaimLimitRange(
    siteCode: string,
    window: RangeWindowQuery,
    onRetrying?: () => boolean,
  ): Promise<RangeRead<ClaimLimitRangeBody>>;
}

const isObject = (value: unknown): value is Record<string, unknown> => typeof value === "object" && value !== null && !Array.isArray(value);

const RANGE_UNAVAILABLE = /^SITE_[A-Z_]+_RANGE_UNAVAILABLE$/;

/** The 503 the range pages retry: a `SITE_*_RANGE_UNAVAILABLE` route refusal or INFRA-1's `TEMPORARILY_UNAVAILABLE`. */
export function isRangeRetryable(status: number, code: string | null): boolean {
  return status === 503 && code !== null && (RANGE_UNAVAILABLE.test(code) || code === TEMPORARILY_UNAVAILABLE);
}

function codeOf(body: unknown): { code: string | null; message: string | null } {
  const detail = isObject(body) && isObject(body.detail) ? body.detail : isObject(body) ? body : null;
  return {
    code: detail !== null && typeof detail.code === "string" ? detail.code : null,
    message: detail !== null && typeof detail.message === "string" ? detail.message : null,
  };
}

const wait = (ms: number) => new Promise<void>((resolve) => setTimeout(resolve, ms));

export function rangeQuery(window: RangeWindowQuery): string {
  const params = new URLSearchParams({ from: window.from, to: window.to });
  if (window.known_at !== null) params.set("known_at", window.known_at);
  return params.toString();
}

async function readRange<T>(
  url: string,
  schema: string,
  onRetrying: (() => boolean) | undefined,
  delays: readonly number[],
): Promise<RangeRead<T>> {
  for (let attempt = 0; ; attempt += 1) {
    let response: Response;
    try {
      response = await fetch(url, { headers: { Accept: "application/json" } });
    } catch {
      return { status: "unavailable", code: null };
    }
    let body: unknown = null;
    try {
      body = await response.json();
    } catch {
      body = null;
    }
    if (response.ok) {
      return isObject(body) && body.schema_version === schema && Array.isArray(body.days)
        ? { status: "loaded", value: body as T }
        : { status: "unavailable", code: null };
    }
    const { code, message } = codeOf(body);
    if (isRangeRetryable(response.status, code)) {
      if (attempt >= delays.length || onRetrying?.() === false) return { status: "unavailable", code };
      await wait(delays[attempt]);
      continue;
    }
    if (response.status >= 500 || code === null) return { status: "unavailable", code };
    return { status: "refused", httpStatus: response.status, code, message };
  }
}

export function createSiteRangeClient(basePath: string = SITES_API_PATH, delays: readonly number[] = RETRY_DELAYS_MS): SiteRangeClient {
  const url = (code: string, route: string, window: RangeWindowQuery) =>
    `${basePath}/${encodeURIComponent(code)}/${route}?${rangeQuery(window)}`;
  return {
    getServiceRange: (code, window, onRetrying) =>
      readRange(url(code, "service-range", window), "site-service-range-1", onRetrying, delays),
    getBackupRange: (code, window, onRetrying) =>
      readRange(url(code, "backup-range", window), "site-backup-range-1", onRetrying, delays),
    getClaimLimitRange: (code, window, onRetrying) =>
      readRange(url(code, "claim-limit-range", window), "site-claim-limit-range-1", onRetrying, delays),
  };
}

export const DEFAULT_SITE_RANGE_CLIENT: SiteRangeClient = createSiteRangeClient();
