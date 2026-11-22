/**
 * IA-P P3b (spec §6 P3b, `spec-period.md` P.4): the client of E2, `GET /api/portfolio/period?from=&to=`. The server
 * resolves the range into whole months and returns a mode (`month`, `period`, `none`); the page renders the JSON as
 * given. A body whose `schema` is not `portfolio-period-1` is an error. Refusals are `{"code", "text"}`.
 */
import { fetchRetrying } from "../sites/temporarilyUnavailable";
import type { DeepDiveMonthBody, DeepDiveOutcome, DeepDiveTile } from "./deepDiveMonthClient";

export const PERIOD_API_PATH = "/api/portfolio/period";
export const PERIOD_SCHEMA = "portfolio-period-1";

/** A range of whole days with the server's words for it (`nav`, `suggest`). */
export interface PeriodDays {
  month_words: string;
  from: string;
  to: string;
}

export interface PeriodMonth extends PeriodDays {
  month: string;
  state: string;
}

export interface PeriodMonthRow extends PeriodMonth {
  contribution: string;
  gap: string | null;
  gap_word: string | null;
  driver: string | null;
  driver_heading: string | null;
  sites: string | null;
}

export interface PeriodBody {
  as_of_text: string;
  status_line: string;
  fresh: string | null;
  headline: { text: string; evidence: string[] };
  tiles: DeepDiveTile[];
  notices: string[];
  months: { title: string; columns: string[]; rows: PeriodMonthRow[] };
  outcomes: DeepDiveOutcome[];
  actions: NonNullable<DeepDiveMonthBody["actions"]>;
}

export interface PortfolioPeriod {
  schema: string;
  from: string;
  to: string;
  mode: "month" | "period" | "none";
  months: PeriodMonth[];
  served: string[];
  period_words: string | null;
  notes: string[];
  shown: { from: string; to: string } | null;
  nav: { previous: PeriodDays | null; next: PeriodDays | null } | null;
  suggest: { text: string; from: string; to: string } | null;
  body: PeriodBody | null;
}

export type PeriodResult =
  | { status: "loaded"; body: PortfolioPeriod }
  | { status: "refused"; httpStatus: number; code: string | null; text: string | null };

export interface PortfolioPeriodClient {
  fetchPeriod(from: string, to: string): Promise<PeriodResult>;
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function periodPath(from: string, to: string): string {
  return `${PERIOD_API_PATH}?${new URLSearchParams({ from, to }).toString()}`;
}

/** `fetchRetrying` over the route; a network failure or a body of another schema is a refusal with no code. */
export async function fetchPeriod(from: string, to: string): Promise<PeriodResult> {
  let response: Response;
  let body: unknown;
  try {
    ({ response, body } = await fetchRetrying(periodPath(from, to)));
  } catch {
    return { status: "refused", httpStatus: 0, code: null, text: null };
  }
  if (response.ok) {
    if (isObject(body) && body.schema === PERIOD_SCHEMA) return { status: "loaded", body: body as unknown as PortfolioPeriod };
    return { status: "refused", httpStatus: response.status, code: null, text: null };
  }
  const code = isObject(body) && typeof body.code === "string" ? body.code : null;
  const text = isObject(body) && typeof body.text === "string" ? body.text : null;
  return { status: "refused", httpStatus: response.status, code, text };
}

export function createPortfolioPeriodClient(): PortfolioPeriodClient {
  return { fetchPeriod };
}
