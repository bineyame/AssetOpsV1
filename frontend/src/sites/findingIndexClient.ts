/**
 * S4-04 phase 2: the typed client for the scoped Site Finding index
 * (`backend/assetops_backend/finding_index_api.py`,
 * `GET /api/sites/{site_code}/finding-index?domain=&from=&to=&limit=&cursor=`).
 *
 * Every refusal is a named state, never a thrown error and never an empty
 * list. Only a `CURRENT` body carries rows and a count; a refusal carries
 * neither, so no state here can be read as "no Findings" except a loaded
 * `CURRENT` body whose `total_count` is 0.
 *
 * - 404 is a Site with no imported (ledger) record: the frame keeps the older
 *   Site Findings summary for it rather than relabelling that summary.
 * - 409 `PERFORMANCE_CUTOVER_CLOSED`, `INDEX_CONTINUITY_LIMIT`,
 *   `INDEX_BASIS_CHANGED` and a typed 422 are each their own state.
 */
import { SITES_API_PATH } from "./siteDirectoryClient";
import { hasKeys, isObject } from "./evidenceRead";
import type { OutcomeCategories } from "./outcomeCategories";

/** The one supported domain token (`mini_grid` / `dispatch` on the server). */
export const FINDING_INDEX_DOMAIN = "mini-grid-dispatch";

export type FindingIndexStatus = "CURRENT" | "PENDING" | "UNASSESSED" | "STALE_PROJECTION" | "FAILED";

export interface FindingIndexScope {
  domain: string;
  from: string;
  to: string;
  limit?: number | null;
  cursor?: string | null;
}

export interface FindingIndexDayWatermark {
  day: string;
  status: FindingIndexStatus;
  reasons: string[];
  s3: {
    status: string;
    selection_seq: number | null;
    run_id: string | null;
    window_assessment_revision_id: string | null;
    model_version: string | null;
    input_sha256?: string | null;
    configuration_sha256?: string | null;
    knowledge_cutoff: string | null;
    selected_at: string | null;
  };
  s4: { matched: boolean; matcher_version: string };
}

export interface FindingIndexRow {
  key: { tenant_id: string; site_id: string; finding_id: string };
  finding_id: string;
  canonical_finding_id: string;
  finding_revision_id: string;
  revision_no: number;
  title: string;
  /** OUT-A: the outcome categories (policy `outcome-map/1`); absent on an older body. */
  categories?: OutcomeCategories;
  episode: { start: string; end: string };
  lifecycle: string;
  transition: string | null;
  claim_level: string | null;
  assessment: {
    assessment_revision_id: string;
    analytic_run_id: string;
    analytic_run_ids?: string[];
    /** post-W6 W1-b Q19: the cited 15-minute interval assessment revisions (the backend emits it per row). */
    interval_assessment_revision_ids?: string[];
    model_version: string;
    matcher_version: string;
    cohort_sha256: string | null;
  };
  cited: { accepted_evidence_ids: string[]; configuration: { run_id: string }[] };
  limitations: unknown;
  relations: {
    merged_from: string[];
    recurs_after: string | null;
    recurred_by: string[];
    split_from: string | null;
    split_parts: string[];
  };
  links: { selected_revision: string; canonical: string; api_history: string; api_selected_revision: string };
  amount: { state: string; reason: string };
}

export interface FindingIndexBody {
  schema_version: "site-finding-index-1";
  site_code: string;
  site_id: string;
  access_basis: string;
  domain: { requested: string; finding_domain: string; analytic_id: string; matcher_version: string };
  window: { from: string; to: string; bounds: string; intersection: string };
  display_timezone: string;
  status: FindingIndexStatus;
  status_reasons: string[];
  is_current: boolean;
  selection_token: string;
  knowledge_at: string | null;
  knowledge_at_label: string;
  built_at: string | null;
  discovery: { days: string[]; requested_days: string[]; continuity_tolerance_minutes: number; limit_days: number };
  watermarks: {
    matcher: { match_pass_id?: string | null; matched_through_selection_seq?: number | null } | null;
    days: FindingIndexDayWatermark[];
  };
  order: string;
  rows: FindingIndexRow[];
  total_count: number | null;
  next_cursor: string | null;
  rows_statement: string | null;
  source_gate?: { permitted: boolean; reason: string };
}

export type FindingIndexResult =
  | { status: "loaded"; value: FindingIndexBody }
  /** 404: no imported Site under this code; the older summary still serves it. */
  | { status: "not_imported"; message: string | null }
  | { status: "unauthenticated"; message: string | null }
  | { status: "forbidden"; message: string | null }
  | { status: "closed"; message: string | null; note: string | null }
  | {
      status: "continuity_limit";
      message: string | null;
      limitDays: number | null;
      inspectedFrom: string | null;
      inspectedTo: string | null;
    }
  | { status: "basis_changed"; message: string | null; reason: string | null }
  | { status: "invalid"; message: string | null; code: string | null; field: string | null }
  | { status: "unavailable"; message: string | null };

export interface FindingIndexClient {
  getFindingIndex(siteId: string, scope: FindingIndexScope): Promise<FindingIndexResult>;
}

function isIndexBody(value: unknown): value is FindingIndexBody {
  return (
    hasKeys(value, ["schema_version", "status", "rows", "total_count", "watermarks", "window", "selection_token"]) &&
    (value as { schema_version: unknown }).schema_version === "site-finding-index-1" &&
    Array.isArray((value as { rows: unknown }).rows)
  );
}

const text = (value: unknown): string | null => (typeof value === "string" ? value : null);

export async function readFindingIndex(path: string): Promise<FindingIndexResult> {
  let response: Response;
  try {
    response = await fetch(path);
  } catch {
    return { status: "unavailable", message: null };
  }
  let body: unknown = null;
  try {
    body = await response.json();
  } catch {
    body = null;
  }
  if (response.ok && isIndexBody(body)) {
    return { status: "loaded", value: body };
  }
  const detail = isObject(body) ? body.detail : null;
  const fields = isObject(detail) ? detail : {};
  const message = typeof detail === "string" ? detail : text(fields.message);
  switch (response.status) {
    case 401:
      return { status: "unauthenticated", message };
    case 403:
      return { status: "forbidden", message };
    case 404:
      return { status: "not_imported", message };
    case 409:
      if (fields.code === "PERFORMANCE_CUTOVER_CLOSED") {
        return { status: "closed", message, note: text(fields.note) };
      }
      if (fields.code === "INDEX_CONTINUITY_LIMIT") {
        return {
          status: "continuity_limit",
          message,
          limitDays: typeof fields.limit_days === "number" ? fields.limit_days : null,
          inspectedFrom: text(fields.inspected_from),
          inspectedTo: text(fields.inspected_to),
        };
      }
      if (fields.code === "INDEX_BASIS_CHANGED") {
        return { status: "basis_changed", message, reason: text(fields.reason) };
      }
      return { status: "unavailable", message };
    case 422:
      return { status: "invalid", message, code: text(fields.code), field: text(fields.field) };
    default:
      return { status: "unavailable", message };
  }
}

export function findingIndexPath(basePath: string, siteId: string, scope: FindingIndexScope): string {
  const query = new URLSearchParams({ domain: scope.domain, from: scope.from, to: scope.to });
  if (scope.limit) query.set("limit", String(scope.limit));
  if (scope.cursor) query.set("cursor", scope.cursor);
  return `${basePath}/${encodeURIComponent(siteId)}/finding-index?${query.toString()}`;
}

export function createFindingIndexClient(basePath: string = SITES_API_PATH): FindingIndexClient {
  return {
    getFindingIndex(siteId, scope) {
      return readFindingIndex(findingIndexPath(basePath, siteId, scope));
    },
  };
}
