import type { Ref } from "./chainRef";
import { outcomeBoardSearch, type OutcomeBoardQuery } from "./outcomeBoardClient";
import { SITES_API_PATH } from "./siteDirectoryClient";

/**
 * CH-5b3 (CH5b3-R Q2): the "Why?" chain client. One `{etag, body}` memory per full request URL (every query
 * parameter is part of the key). A repeat request sends `If-None-Match`; a `304` reuses the stored body. Any other
 * status never shows the stored body, and drops it.
 *
 * Known deviation: the build sheet names `F/shell/chainClient.ts`. The board (`F/sites/OutcomeBoard.tsx`) needs the
 * module default and the Site substrate may not import shell code (site-substrate guard, rule 8), so the client sits
 * beside `outcomeBoardClient.ts` in the substrate.
 */

export const WHY_SCHEMA = "outcome-chain-why-1";
const ESTATE_API_PATH = "/api/estate";

export type WhyCategory = "GROW_REVENUE" | "OPTIMIZE_COST" | "PROTECT_ASSET" | "ASSURE_PERFORMANCE";

export interface WhyText {
  title: string;
  say: string | null;
  comes_from: string[];
  days_used: string | null;
  would_change: string | null;
  evidence_ref: Ref | null;
  evidence_label: string | null;
}

export interface WhyBody {
  schema_version: string;
  category: string;
  window?: { from: string | null; to: string | null; known_at: string | null };
  text: WhyText;
}

export type WhyRead =
  | { status: "loaded"; value: WhyBody }
  | { status: "refused"; httpStatus: number; code: string }
  | { status: "unavailable" };

export interface WhyWindow {
  from: string;
  to: string;
  known_at: string | null;
}

export interface ChainClient {
  getSiteWhy(siteCode: string, category: string, query: OutcomeBoardQuery): Promise<WhyRead>;
  getEstateWhy(category: string, window: WhyWindow): Promise<WhyRead>;
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function isWhy(value: unknown): value is WhyBody {
  if (!isObject(value) || value.schema_version !== WHY_SCHEMA || !isObject(value.text)) return false;
  const t = value.text;
  return typeof t.title === "string" && Array.isArray(t.comes_from);
}

export function siteWhyUrl(
  siteCode: string,
  category: string,
  query: OutcomeBoardQuery,
  basePath = SITES_API_PATH,
): string {
  const board = outcomeBoardSearch(query);
  const params = new URLSearchParams(board === "" ? "" : board.slice(1));
  params.set("category", category);
  return `${basePath}/${encodeURIComponent(siteCode)}/chain/why?${params.toString()}`;
}

export function estateWhyUrl(category: string, window: WhyWindow, basePath = ESTATE_API_PATH): string {
  const params = new URLSearchParams();
  params.set("from", window.from);
  params.set("to", window.to);
  if (window.known_at) params.set("known_at", window.known_at);
  params.set("category", category);
  return `${basePath}/chain/why?${params.toString()}`;
}

export function createChainClient(
  options: {
    sitesPath?: string;
    estatePath?: string;
    fetch?: typeof fetch;
  } = {},
): ChainClient {
  const memory = new Map<string, { etag: string; body: WhyBody }>();
  const doFetch = options.fetch ?? ((input: RequestInfo | URL, init?: RequestInit) => fetch(input, init));

  async function read(url: string): Promise<WhyRead> {
    const stored = memory.get(url);
    const headers: Record<string, string> = { Accept: "application/json" };
    if (stored) headers["If-None-Match"] = stored.etag;
    let response: Response;
    try {
      // `no-store`: the browser cache adds no validator of its own, so the 304 reaches this client.
      response = await doFetch(url, { headers, cache: "no-store" });
    } catch {
      return { status: "unavailable" };
    }
    if (response.status === 304) {
      return stored ? { status: "loaded", value: stored.body } : { status: "unavailable" };
    }
    let body: unknown = null;
    try {
      body = await response.json();
    } catch {
      body = null;
    }
    if (response.status === 200) {
      if (!isWhy(body)) {
        memory.delete(url);
        return { status: "unavailable" };
      }
      const etag = response.headers.get("ETag");
      if (etag) memory.set(url, { etag, body });
      else memory.delete(url);
      return { status: "loaded", value: body };
    }
    memory.delete(url);
    const detail = isObject(body) && isObject(body.detail) ? body.detail : null;
    const code = detail !== null && typeof detail.code === "string" ? detail.code : "";
    return { status: "refused", httpStatus: response.status, code };
  }

  return {
    getSiteWhy: (siteCode, category, query) => read(siteWhyUrl(siteCode, category, query, options.sitesPath)),
    getEstateWhy: (category, window) => read(estateWhyUrl(category, window, options.estatePath)),
  };
}

/** The module default the board and the Portfolio cards use unless a test passes its own. */
export const defaultChainClient: ChainClient = createChainClient();
