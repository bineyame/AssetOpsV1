/**
 * SR-6b (rev 10 §10.2, D-SR.49): the typed client for `GET /api/sites/{site_code}/health-range?from&to[&known_at]`
 * (wire `site-health-range-1`). Refusals keep their HTTP status and server code, as `outcomeBoardClient.ts` reads
 * them (`detail.code`). A 503 `SITE_HEALTH_RANGE_UNAVAILABLE` (or `TEMPORARILY_UNAVAILABLE`) is retried after 2, 4
 * and 8 s, the caller told before each wait, so the page reads "Temporarily unavailable. Retrying…" meanwhile.
 */
import type { HealthRead } from "./healthClient";
import { SITES_API_PATH } from "./siteDirectoryClient";
import { RETRY_DELAYS_MS, TEMPORARILY_UNAVAILABLE } from "./temporarilyUnavailable";

export const HEALTH_RANGE_SCHEMA = "site-health-range-1";
export const SITE_HEALTH_RANGE_UNAVAILABLE = "SITE_HEALTH_RANGE_UNAVAILABLE";

export type GatewayDayContact =
  | "IN_CONTACT"
  | "PARTIAL_CONTACT"
  | "READINGS_ONLY"
  | "NO_CONTACT"
  | "NOT_EXPECTED"
  | "AFTER_CUTOFF";

export type SourceDayState = "READINGS" | "NO_READINGS" | "NOT_EXPECTED" | "AFTER_CUTOFF";

export interface HealthRangeGateway {
  gateway_external_id: string;
  mode: string;
  disabled: boolean;
  cadence_seconds: number;
  days: {
    day: string;
    diagnostics: number;
    first_received_at: string | null;
    last_received_at: string | null;
    contact: GatewayDayContact | string;
  }[];
}

export interface HealthRangeSource {
  source_external_id: string;
  disabled: boolean;
  days: { day: string; accepted_readings: number; last_received_at: string | null; state: SourceDayState | string }[];
}

export interface HealthRangeBody {
  schema_version: typeof HEALTH_RANGE_SCHEMA;
  site: { site_code: string; site_name: string; timezone: string | null };
  window: { from: string; to: string; known_at: string | null; basis: string };
  gateways: HealthRangeGateway[];
  sources: HealthRangeSource[];
  /** The SR-5a day state (ANALYSED for an analysed day); `accepted_readings` is the dispatch row's count, null on gaps. */
  days: { day: string; state: string; accepted_readings: number | null }[];
  summary: {
    days_requested: number;
    days_with_readings: number;
    days_without_readings: number;
    days_not_expected: number;
    days_after_cutoff: number;
    gateways_in_contact_all_days: number;
  };
  links: { day: string };
}

/** The UTC instants of the request: `from` included, `to` excluded. */
export interface HealthRangeQuery {
  from: string;
  to: string;
  known_at?: string | null;
}

export interface HealthRangeClient {
  /** `onRetrying` is told before each wait; returning `false` (the caller is gone) stops the retries. */
  getHealthRange(siteCode: string, query: HealthRangeQuery, onRetrying?: () => boolean): Promise<HealthRead<HealthRangeBody>>;
}

export function healthRangeSearch(query: HealthRangeQuery): string {
  const params = new URLSearchParams({ from: query.from, to: query.to });
  if (query.known_at) params.set("known_at", query.known_at);
  return `?${params.toString()}`;
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isBody(value: unknown): value is HealthRangeBody {
  return (
    isObject(value) &&
    value.schema_version === HEALTH_RANGE_SCHEMA &&
    Array.isArray(value.gateways) &&
    Array.isArray(value.sources) &&
    Array.isArray(value.days) &&
    isObject(value.summary)
  );
}

function codeOf(body: unknown): { code: string | null; message: string | null } {
  const detail = isObject(body) && isObject(body.detail) ? body.detail : isObject(body) ? body : null;
  return {
    code: detail !== null && typeof detail.code === "string" ? detail.code : null,
    message: detail !== null && typeof detail.message === "string" ? detail.message : null,
  };
}

/** The 503 the route answers when its store could not be read: worth another attempt. */
export const isRetryable = (status: number, code: string | null): boolean =>
  status === 503 && (code === SITE_HEALTH_RANGE_UNAVAILABLE || code === TEMPORARILY_UNAVAILABLE);

const wait = (ms: number) => new Promise<void>((resolve) => setTimeout(resolve, ms));

export function createHealthRangeClient(
  basePath: string = SITES_API_PATH,
  delays: readonly number[] = RETRY_DELAYS_MS,
): HealthRangeClient {
  return {
    async getHealthRange(siteCode, query, onRetrying) {
      const path = `${basePath}/${encodeURIComponent(siteCode)}/health-range${healthRangeSearch(query)}`;
      for (let attempt = 0; ; attempt += 1) {
        let response: Response;
        let body: unknown = null;
        try {
          response = await fetch(path, { headers: { Accept: "application/json" } });
        } catch {
          return { status: "refused", http: null, code: null, message: null };
        }
        try {
          body = await response.json();
        } catch {
          body = null;
        }
        if (response.ok) {
          return isBody(body)
            ? { status: "loaded", value: body }
            : { status: "refused", http: response.status, code: null, message: null };
        }
        const { code, message } = codeOf(body);
        if (isRetryable(response.status, code) && attempt < delays.length && onRetrying?.() !== false) {
          await wait(delays[attempt]);
          continue;
        }
        return { status: "refused", http: response.status, code, message };
      }
    },
  };
}
