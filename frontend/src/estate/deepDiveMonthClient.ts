/**
 * 5c (spec §5.1): the client for "The month", `GET /api/portfolio/month[?month=YYYY-MM]` (`deep-dive-month-1`).
 * The body is the server's display JSON (D-5C.2): every figure and word is a string the page renders as given.
 * A body whose `schema` is not `deep-dive-month-1` is an error. Refusals are `{"code", "text"}` (spec §4.2).
 */
import { fetchRetrying } from "../sites/temporarilyUnavailable";

export const DEEP_DIVE_API_PATH = "/api/portfolio/month";
export const DEEP_DIVE_SCHEMA = "deep-dive-month-1";

export interface DeepDiveTile {
  key: string;
  label: string;
  value: string;
  word: string | null;
  lines: string[];
  /** Plain decimals for the bar's width, the page's one ratio (spec §5.3). */
  bar: { actual: string; target: string } | null;
}

export interface DeepDiveDriver {
  key?: string;
  label: string;
  value: string;
  sites: string;
  detail: string | null;
  word: string | null;
  /** D-5C.21: the driver's own parts, same shape, recursively; `[]` for a leaf (absent in payloads before rev 3). */
  children?: DeepDiveDriver[];
}

export interface DeepDiveStepDrawer {
  title: string;
  lines: string[];
  sites: { site: string; value: string; text: string | null }[];
  carried: string[];
  out: string[];
  lines_org: string[];
  drivers: DeepDiveDriver[];
}

export interface DeepDiveStep {
  key: string;
  label: string;
  value: string;
  share: string | null;
  word: string | null;
  sites: string;
  drawer: DeepDiveStepDrawer;
}

export interface DeepDiveGroup {
  key: string;
  label: string;
  value: string;
  steps: DeepDiveStep[];
}

export interface DeepDiveTable {
  columns: string[];
  rows: string[][];
  total: string[];
}

export interface DeepDiveOutcome {
  key: string;
  label: string;
  value: string;
  word: string | null;
  line: string;
  drawer: { title: string; lines: string[] } | null;
}

export interface DeepDiveActionRow {
  title: string;
  owner: string;
  agreed: string;
  state: string;
}

/** Served: every key. NO_SNAPSHOT and REBUILD_NEEDED: the header keys only (`schema` to `state_text`). */
export interface DeepDiveMonthBody {
  schema: string;
  operator: string;
  month: string;
  month_words: string;
  nav: { previous: string; next: string | null };
  state: "SERVED" | "NO_SNAPSHOT" | "REBUILD_NEEDED";
  state_text: string | null;
  as_of?: string;
  as_of_text?: string;
  fresh?: { current: boolean; text: string | null; untracked_text: string | null };
  standing?: { reconciled: boolean; reason: string; text: string; details?: string[] };
  headline?: { text: string; evidence: string[] };
  status_line?: string;
  tiles?: DeepDiveTile[];
  notices?: string[];
  bridge?: {
    title: string;
    totals: { actual_label: string; actual: string; target_label: string; target: string };
    groups: DeepDiveGroup[];
    by_site: DeepDiveTable;
  };
  cash?: { title: string; text: string; word: string | null; sites: string; table: DeepDiveTable };
  outcomes?: DeepDiveOutcome[];
  decisions?: { title: string; text: string };
  actions?: { title: string; connected: boolean; text: string | null; rows: DeepDiveActionRow[]; more: number };
  not_available?: { rows: { needs: string; fills: string; sites: string }[]; not_built: string };
}

export type DeepDiveResult =
  | { status: "loaded"; body: DeepDiveMonthBody }
  | { status: "refused"; httpStatus: number; code: string | null; text: string | null };

export interface DeepDiveMonthClient {
  fetchDeepDiveMonth(month?: string): Promise<DeepDiveResult>;
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function deepDivePath(month?: string): string {
  return month === undefined || month === "" ? DEEP_DIVE_API_PATH : `${DEEP_DIVE_API_PATH}?month=${encodeURIComponent(month)}`;
}

/** `fetchRetrying` over the route; a network failure or a body of another schema is a refusal with no code. */
export async function fetchDeepDiveMonth(month?: string): Promise<DeepDiveResult> {
  let response: Response;
  let body: unknown;
  try {
    ({ response, body } = await fetchRetrying(deepDivePath(month)));
  } catch {
    return { status: "refused", httpStatus: 0, code: null, text: null };
  }
  if (response.ok) {
    if (isObject(body) && body.schema === DEEP_DIVE_SCHEMA) return { status: "loaded", body: body as unknown as DeepDiveMonthBody };
    return { status: "refused", httpStatus: response.status, code: null, text: null };
  }
  const code = isObject(body) && typeof body.code === "string" ? body.code : null;
  const text = isObject(body) && typeof body.text === "string" ? body.text : null;
  return { status: "refused", httpStatus: response.status, code, text };
}

export function createDeepDiveMonthClient(): DeepDiveMonthClient {
  return { fetchDeepDiveMonth };
}
