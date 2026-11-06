import type { Ref } from "./chainRef";
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

/** CH-2: the thread a Finding sits on (additive; nothing renders it until CH-5a). */
export interface FindingThreadRef {
  id: string;
  occurrence_no: number;
  occurrences: number;
  /** CH-3: the thread segment, and its state and state effective day on the board day (additive). */
  segment_no?: number;
  state?: string | null;
  state_effective_day?: string | null;
  /** CH-3: the Site-local day the state was read on (additive). */
  state_day?: string | null;
}

/** A FINDING issue's ref; `thread` is null when the Finding has no thread. */
export interface OutcomeFindingRef {
  finding_id: string;
  finding_revision_id: string;
  thread?: FindingThreadRef | null;
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
  /** CH5a2-R4: the Ref this link renders from; absent or null renders no link. */
  link_ref?: Ref | null;
}

export interface OutcomeIssue {
  kind: IssueKind | string;
  role: "MOVES" | "CHECKED" | string;
  text: string;
  href: string | null;
  /** CH5a2-R4: the Ref this link renders from; absent or null renders no link. */
  link_ref?: Ref | null;
  /** OUT-C: an EARLY_WARNING/RISK issue carries its warning key here. */
  ref: OutcomeRef | OutcomeFindingRef | string | null;
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
  /** CH5a2-R4: the Ref this link renders from; absent or null renders no link. */
  link_ref?: Ref | null;
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
  /** CH5a2-R4: the Ref this link renders from; absent or null renders no link. */
  link_ref?: Ref | null;
  evidence_refs: OutcomeWarningRef[];
  count: number | null;
  subject_label: string | null;
  /** Rulings C final review F1: the open linked fault's noun phrase; non-null only on REPEATED warnings. */
  fault_name?: string | null;
}

export interface OutcomeLinkItem {
  text: string;
  href: string | null;
  /** CH5a2-R4: the Ref this link renders from; absent or null renders no link. */
  link_ref?: Ref | null;
  /** POLISH P-10 (Addendum 12 Q1, PA-3): a case item's stored kind (INCIDENT, WORK_REQUEST or PLAN); absent on an older body. */
  kind?: string;
  /** POLISH P-10 (Addendum 12 Q1, PA-3): when a case item occurred; absent on an older body. */
  occurred_at?: string | null;
}

export interface OutcomeInHandItem extends OutcomeLinkItem {
  state_label: string | null;
}

export interface OutcomeEarlierItem extends OutcomeLinkItem {
  result_label: string | null;
  /** OUT-E: the trial's modelled cost change and before/after line, joined by " · "; null when none applies. */
  detail?: string | null;
}

export interface OutcomeMoney {
  amount_low: string | number | null;
  amount_high: string | number | null;
  currency: string | null;
}

/** CH-6a3: one node claim of a row (`chain/vocabulary.py` `Claim.to_json`). */
export interface NodeClaim {
  key: string;
  value: unknown;
  basis: "COMPLETE" | "CHECKED_DAYS" | "NOT_KNOWN" | string;
  days: Record<string, number> | null;
  text: string;
  /** R2b: this claim's own days line (the server's `days_line` over its own days); null when it has no days. */
  days_line?: string | null;
}

export interface RowNodes {
  kpi: NodeClaim | null;
  earnings: NodeClaim | null;
  potential: NodeClaim | null;
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
  must_not_harm: { text: string; href: string | null; link_ref?: Ref | null } | null;
  contributors: OutcomeContributor[];
  issues: OutcomeIssue[];
  options: OutcomeLinkItem[];
  in_hand: OutcomeInHandItem[];
  earlier: OutcomeEarlierItem[];
  /** Addendum 2: set exactly when `earlier` is empty on a measured row; absent on an older body. */
  earlier_empty_text?: string | null;
  evidence_link: { label: string; href: string | null; link_ref?: Ref | null } | null;
  outcomes: { key: string; label: string; state: string; reason: string }[];
  /**
   * WALK1-3b: an open opportunity on a row whose state is not "Opportunity" (the declared objective sets the state);
   * rendered as a second header chip. Null or absent on an older body.
   */
  potential?: { label: string; text: string | null } | null;
  /** CH-6a3: the row's three node claims, its days line and the R7 target note; absent on an older body. */
  nodes?: RowNodes | null;
  target_note?: string | null;
  /** CH-6b2 (§B3): the Grow row's `ob-val` (earnings, else potential, else target); absent on other rows. */
  grow_headline?: string | null;
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
  /** IDX-GAPS (mini only): the Finding index gap line under the rows; null or absent when no day is a gap. */
  finding_gaps?: { text: string; days: string[]; withheld?: boolean } | null;
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
