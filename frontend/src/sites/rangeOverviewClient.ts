/**
 * SR-5b (architect rev 9 §9.4, D-SR.11): the typed client for `GET /api/sites/{site_code}/range-overview`, schema
 * `site-range-overview-1`, the mini-grid Site's read over the shared range. Every count, amount and word set here is
 * the server's (composed from the Portfolio's own selectors); the page only words the states.
 *
 * Refusals are mapped like `outcomeBoardClient.ts`. A 503 `SITE_RANGE_OVERVIEW_UNAVAILABLE` (the route's store
 * failure) or `TEMPORARILY_UNAVAILABLE` is retried as INFRA-1 does and is reported as `TEMPORARILY_UNAVAILABLE`, so
 * the page shows "Temporarily unavailable. Retrying…", never a data state.
 */
import { SITES_API_PATH } from "./siteDirectoryClient";
import { TEMPORARILY_UNAVAILABLE, fetchRetrying, isTemporarilyUnavailable } from "./temporarilyUnavailable";
import type { EstatePartialMoney } from "../estate/estateClient";

export const RANGE_OVERVIEW_SCHEMA = "site-range-overview-1";
export const SITE_RANGE_OVERVIEW_UNAVAILABLE = "SITE_RANGE_OVERVIEW_UNAVAILABLE";

export type RangeDayState =
  | "FINDINGS"
  | "CLEAR"
  | "NO_READINGS"
  | "READINGS_CONFLICT"
  | "NOT_ENOUGH_READINGS"
  | "NOT_ANALYSED"
  | "STILL_PROCESSING"
  | "NOT_EXPECTED";

export type RangeDayMoneyState = "SUMMED" | "NO_ELIGIBLE_LINES" | "CURRENCY_MIXED" | "OVERLAPPING" | "WITHHELD";

export interface RangeMoney {
  low: string;
  high: string;
  currency: string;
}

export interface RangeDay {
  /** The UTC calendar day (`YYYY-MM-DD`), the same day `?day=` opens on the one-day board. */
  day: string;
  state: RangeDayState;
  /** Member Findings whose episode meets the day; null on a gap day. */
  finding_count: number | null;
  /** D-SR.50: non-member latest revisions (no longer supported) meeting the day; null on a gap day. */
  retired_finding_count?: number | null;
  money: RangeMoney | null;
  money_state: RangeDayMoneyState;
  accepted_readings: number | null;
  /** D-SR.56: "Readings began late this day · not counted" on a NOT_EXPECTED day with readings; absent otherwise. */
  note?: string;
}

/** The Portfolio's OPERATING_COST value card, as served (`public(operating_cost_card(...))`). */
export interface RangeMoneyCard {
  key: string;
  state: string;
  display_value: string | null;
  currency: string | null;
  detail: string | null;
  basis_text: string;
  tone: string;
  [key: string]: unknown;
}

export interface RangeCoverageDays {
  requested: number;
  checked: number;
  gaps: { day: string; state: string; reason: string }[];
  text?: string | null;
  withheld?: boolean;
  policy?: string;
}

export interface SiteRangeOverviewBody {
  schema_version: typeof RANGE_OVERVIEW_SCHEMA;
  site: { site_code: string; site_name: string; site_type: string; timezone: string | null };
  window: { from: string; to: string; known_at: string; basis: "CURRENT" | "HISTORICAL" };
  status: string;
  coverage: { state: string; days?: RangeCoverageDays | null; [key: string]: unknown };
  money: {
    card: RangeMoneyCard;
    partial: EstatePartialMoney | null;
    quantity: { low: string; high: string; unit: string } | null;
  };
  findings: { count: number | null; confirmed: number | null; not_confirmed: number | null; awaiting_verification: number | null };
  actions: { open: number | null; awaiting_verification: number | null; verified_resolution_count: number | null };
  dispatch: {
    days_requested: number | null;
    days_analysed: number | null;
    days_with_findings: number;
    days_with_retired_findings?: number;
    accepted_readings: number | null;
  };
  days: RangeDay[];
  links: { findings: string; day: string };
}

/** The range in the instant form the bar sends (`rangeParams`): `from`/`to` at UTC midnight, optional `known_at`. */
export interface RangeOverviewQuery {
  from: string;
  to: string;
  known_at?: string | null;
}

export type RangeOverviewRead =
  | { status: "loaded"; value: SiteRangeOverviewBody }
  | { status: "refused"; httpStatus: number; code: string }
  | { status: "unavailable" };

export interface RangeOverviewClient {
  /** `onRetrying` is told before each wait while the read answers 503 unavailable; returning false stops the retries. */
  getRangeOverview(siteCode: string, query: RangeOverviewQuery, onRetrying?: () => void | boolean): Promise<RangeOverviewRead>;
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function codeOf(body: unknown): string {
  const detail = isObject(body) && isObject(body.detail) ? body.detail : isObject(body) ? body : null;
  return detail !== null && typeof detail.code === "string" ? detail.code : "";
}

/** A 503 the client retries: INFRA-1's `TEMPORARILY_UNAVAILABLE` and the route's own store failure. */
export function isRangeOverviewRetryable(status: number, body: unknown): boolean {
  return isTemporarilyUnavailable(status, body) || (status === 503 && codeOf(body) === SITE_RANGE_OVERVIEW_UNAVAILABLE);
}

function isBody(value: unknown): value is SiteRangeOverviewBody {
  return isObject(value) && value.schema_version === RANGE_OVERVIEW_SCHEMA && Array.isArray(value.days);
}

export function rangeOverviewSearch(query: RangeOverviewQuery): string {
  const params = new URLSearchParams({ from: query.from, to: query.to });
  if (query.known_at) params.set("known_at", query.known_at);
  return `?${params.toString()}`;
}

export function createRangeOverviewClient(basePath: string = SITES_API_PATH): RangeOverviewClient {
  return {
    async getRangeOverview(siteCode, query, onRetrying) {
      let response: Response;
      let body: unknown;
      try {
        ({ response, body } = await fetchRetrying(
          `${basePath}/${encodeURIComponent(siteCode)}/range-overview${rangeOverviewSearch(query)}`,
          onRetrying,
          undefined,
          isRangeOverviewRetryable,
        ));
      } catch {
        return { status: "unavailable" };
      }
      if (response.ok) return isBody(body) ? { status: "loaded", value: body } : { status: "unavailable" };
      if (isRangeOverviewRetryable(response.status, body)) {
        return { status: "refused", httpStatus: 503, code: TEMPORARILY_UNAVAILABLE };
      }
      return { status: "refused", httpStatus: response.status, code: codeOf(body) };
    },
  };
}
