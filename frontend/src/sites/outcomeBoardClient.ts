import { SITES_API_PATH } from "./siteDirectoryClient";

/**
 * OUT-B B5: the typed client for `GET /api/sites/{site_code}/outcome-board` (build spec §B.1, wire
 * `site-outcome-board-1`). Every text field is backend-delivered and renders as data; the only value the
 * frontend formats is `headline_money` (ruling B-Q14).
 */
export const OUTCOME_BOARD_SCHEMA = "site-outcome-board-1";

export type OutcomeState =
  | "NEEDS_ATTENTION"
  | "WATCH"
  | "OPPORTUNITY"
  | "ON_TRACK"
  | "UNKNOWN"
  | "NO_OBJECTIVE"
  | "NOT_MEASURED"
  | "NOT_APPLICABLE";

export type OutcomeTone = "amber" | "blue" | "green" | "gray" | "none";

export type IssueKind = "FINDING" | "EVIDENCE_GAP" | "RISK" | "EARLY_WARNING" | "OPPORTUNITY";

export interface OutcomeRef {
  key: string;
  label: string;
}

export interface OutcomeConfidence {
  label: string;
  tone: string;
}

export interface OutcomeContributor {
  key: string;
  label: string;
  text: string;
  confidence: OutcomeConfidence | null;
  href: string | null;
}

export interface OutcomeIssue {
  kind: IssueKind | string;
  role: "MOVES" | "CHECKED" | string;
  text: string;
  href: string | null;
  /** OUT-C: an EARLY_WARNING/RISK issue carries its warning key here. */
  ref: OutcomeRef | string | null;
}

/** OUT-C §4: the `categories` object of one warning (the outcome map's MOVES/CHECKED items). */
export interface OutcomeWarningCategories {
  policy_version: string;
  state: "MAPPED" | "NOT_MAPPED" | string;
  items: { category: string; label: string; role: "MOVES" | "CHECKED" | string; outcomes: OutcomeRef[] }[];
}

export interface OutcomeWarningRef {
  kind: string;
  id: string;
  label: string | null;
  href: string | null;
}

/** OUT-C §4: one early warning, board and estate summary alike. Every text is backend data; no money on it. */
export interface OutcomeWarning {
  key: string;
  kind: string;
  badge: "RISK" | "EARLY_WARNING" | "OPPORTUNITY" | string;
  badge_label: string;
  lens: "COST" | "RISK" | "OPPORTUNITY" | string;
  title: string;
  seen: string;
  persistence: string;
  persistence_label: string;
  price_needs: string;
  status_effect: string;
  categories: OutcomeWarningCategories;
  site_code: string;
  site_name: string;
  href: string | null;
  evidence_refs: OutcomeWarningRef[];
  count: number | null;
  subject_label: string | null;
  /** Rulings C final review F1: the open linked fault's noun phrase; non-null only on REPEATED warnings. */
  fault_name?: string | null;
}

export interface OutcomeLinkItem {
  text: string;
  href: string | null;
}

export interface OutcomeInHandItem extends OutcomeLinkItem {
  state_label: string | null;
}

export interface OutcomeEarlierItem extends OutcomeLinkItem {
  result_label: string | null;
}

export interface OutcomeMoney {
  amount_low: string | number | null;
  amount_high: string | number | null;
  currency: string | null;
}

export interface OutcomeBoardRow {
  category: string;
  label: string;
  definition: string;
  icon: string;
  state: OutcomeState | string;
  state_label: string;
  tone: OutcomeTone | string;
  lead_outcome: OutcomeRef | null;
  headline: string | null;
  headline_money: OutcomeMoney | null;
  subline: string | null;
  not_measured_text: string | null;
  counts: { issues: number; in_hand: number };
  must_not_harm: { text: string; href: string | null } | null;
  contributors: OutcomeContributor[];
  issues: OutcomeIssue[];
  options: OutcomeLinkItem[];
  in_hand: OutcomeInHandItem[];
  earlier: OutcomeEarlierItem[];
  /** Addendum 2: set exactly when `earlier` is empty on a measured row; absent on an older body. */
  earlier_empty_text?: string | null;
  evidence_link: { label: string; href: string | null } | null;
  outcomes: { key: string; label: string; state: string; reason: string }[];
}

export interface OutcomeBoardBody {
  schema_version: typeof OUTCOME_BOARD_SCHEMA;
  policy_versions: Record<string, string | null>;
  site_code: string;
  site_id: string;
  site_name: string;
  domain: string;
  window: { from: string | null; to: string | null; known_at: string | null };
  read_state: "AVAILABLE" | "PARTIAL" | "UNAVAILABLE";
  rows: OutcomeBoardRow[];
  warnings: OutcomeWarning[];
  links: { self: string };
}

/** Mini: `date` (one UTC day) plus the optional Finding pin. Cold and EV: `from`, `to`, `known_at`. */
export interface OutcomeBoardQuery {
  from?: string | null;
  to?: string | null;
  known_at?: string | null;
  date?: string | null;
  finding_id?: string | null;
  finding_revision_id?: string | null;
}

export type OutcomeBoardRead =
  | { status: "loaded"; value: OutcomeBoardBody }
  | { status: "refused"; httpStatus: number; code: string }
  | { status: "unavailable" };

export interface OutcomeBoardClient {
  getOutcomeBoard(siteCode: string, query: OutcomeBoardQuery): Promise<OutcomeBoardRead>;
}

const QUERY_KEYS = ["date", "from", "to", "known_at", "finding_id", "finding_revision_id"] as const;

export function outcomeBoardSearch(query: OutcomeBoardQuery): string {
  const params = new URLSearchParams();
  for (const key of QUERY_KEYS) {
    const value = query[key];
    if (value !== null && value !== undefined && value !== "") params.set(key, value);
  }
  const text = params.toString();
  return text === "" ? "" : `?${text}`;
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isBoard(value: unknown): value is OutcomeBoardBody {
  return isObject(value) && value.schema_version === OUTCOME_BOARD_SCHEMA && Array.isArray(value.rows);
}

export function createOutcomeBoardClient(basePath: string = SITES_API_PATH): OutcomeBoardClient {
  return {
    async getOutcomeBoard(siteCode, query) {
      let response: Response;
      try {
        response = await fetch(`${basePath}/${encodeURIComponent(siteCode)}/outcome-board${outcomeBoardSearch(query)}`, {
          headers: { Accept: "application/json" },
        });
      } catch {
        return { status: "unavailable" };
      }
      let body: unknown = null;
      try {
        body = await response.json();
      } catch {
        body = null;
      }
      if (response.ok) return isBoard(body) ? { status: "loaded", value: body } : { status: "unavailable" };
      const detail = isObject(body) && isObject(body.detail) ? body.detail : null;
      const code = detail !== null && typeof detail.code === "string" ? detail.code : "";
      return { status: "refused", httpStatus: response.status, code };
    },
  };
}
