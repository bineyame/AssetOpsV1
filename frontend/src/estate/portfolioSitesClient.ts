/**
 * IA-P P4b (spec §6 P4b, `spec-period.md` P.8): the client of E1, `GET /api/portfolio/sites?from=&to=`. The server
 * resolves the range into the Overview's whole months and returns one row per Site, ordered, with every string made
 * there; the browser renders them as given. A body whose `schema` is not `portfolio-sites-1` is an error. Refusals are
 * E2's: `{"code", "text"}`.
 */
import { fetchRetrying } from "../sites/temporarilyUnavailable";
import type { PortfolioPeriod } from "./portfolioPeriodClient";

export const SITES_API_PATH = "/api/portfolio/sites";
export const SITES_SCHEMA = "portfolio-sites-1";

/** One Site (P.8 "A row"); `below` is false on a row not compared. */
export interface PortfolioSiteRow {
  site_code: string;
  site: string;
  group: string;
  contribution: string;
  gap: string;
  gap_word: string | null;
  driver: string;
  driver_heading: string | null;
  below: boolean;
  months_text: string | null;
}

/** E1's body: E2's header keys, then the Sites (P.8 "The JSON"). */
export type PortfolioSites = Pick<
  PortfolioPeriod,
  "from" | "to" | "mode" | "months" | "served" | "period_words" | "notes" | "shown" | "nav" | "suggest"
> & {
  schema: string;
  as_of_text: string | null;
  headline: { text: string; evidence: string[] } | null;
  columns: string[];
  rows: PortfolioSiteRow[];
  total: { gap: string; word: string } | null;
  without_target: { count: number; text: string | null };
};

export type PortfolioSitesResult =
  | { status: "loaded"; body: PortfolioSites }
  | { status: "refused"; httpStatus: number; code: string | null; text: string | null };

export interface PortfolioSitesClient {
  fetchSites(from: string, to: string): Promise<PortfolioSitesResult>;
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function portfolioSitesPath(from: string, to: string): string {
  return `${SITES_API_PATH}?${new URLSearchParams({ from, to }).toString()}`;
}

/** `fetchRetrying` over the route; a network failure or a body of another schema is a refusal with no code. */
export async function fetchPortfolioSites(from: string, to: string): Promise<PortfolioSitesResult> {
  let response: Response;
  let body: unknown;
  try {
    ({ response, body } = await fetchRetrying(portfolioSitesPath(from, to)));
  } catch {
    return { status: "refused", httpStatus: 0, code: null, text: null };
  }
  if (response.ok) {
    if (isObject(body) && body.schema === SITES_SCHEMA && Array.isArray(body.rows)) return { status: "loaded", body: body as unknown as PortfolioSites };
    return { status: "refused", httpStatus: response.status, code: null, text: null };
  }
  const code = isObject(body) && typeof body.code === "string" ? body.code : null;
  const text = isObject(body) && typeof body.text === "string" ? body.text : null;
  return { status: "refused", httpStatus: response.status, code, text };
}

export function createPortfolioSitesClient(): PortfolioSitesClient {
  return { fetchSites: fetchPortfolioSites };
}
