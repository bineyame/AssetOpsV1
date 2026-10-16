/**
 * S6-03 (`I-site-action-index-read`): the typed client for the Site Work
 * Action index (`backend/assetops_backend/action_index_api.py`,
 * `GET /api/sites/{site_code}/action-index?from=&to=&limit=&cursor=`).
 *
 * Every refusal is a named state, never a thrown error and never an empty
 * list. Only a loaded `CURRENT` body carries rows and a count, so the only
 * "no Actions" statement is a loaded body whose `total_count` is 0.
 */
import { SITES_API_PATH } from "./siteDirectoryClient";
import { hasKeys, isObject } from "./evidenceRead";

export interface ActionIndexScope {
  from: string;
  to: string;
  limit?: number | null;
  cursor?: string | null;
}

export interface ActionIndexState {
  application: string;
  accepted_at: string | null;
  applied_at: string | null;
  application_attempts: number;
  failed_attempts: number;
  last_failure: { event_id: string; failure_code: string | null; recorded_at: string } | null;
  outcome: { state: string; statement: string };
  resolution?: { state: string; event_id: string; recorded_at: string; outcome: string | null };
}

export interface ActionIndexRow {
  key: { tenant_id: string; site_id: string; action_id: string };
  action_id: string;
  action_code: string;
  created_at: string;
  origin: { finding_id: string; finding_revision_id: string; revision_no: number };
  selected_event: {
    id: string;
    kind: string;
    recorded_at: string;
    occurred_at: string;
    occurred_before_recorded: boolean;
  };
  event_count: number;
  state: ActionIndexState;
  links: {
    canonical: string;
    selected_event: string;
    history_at_event: string;
    api_action_at_event: string;
    api_events_at_event: string;
    origin_finding: string;
  };
}

export interface ActionIndexFence {
  max_created_at: string | null;
  max_event_recorded_at: string | null;
  action_count: number;
  event_count: number;
  zero_rows: boolean;
  token: string;
}

export interface ActionIndexBody {
  schema_version: "site-action-index-1";
  site_code: string;
  site_id: string;
  access_basis: string;
  kind: "ACTIONS";
  window: { from: string; to: string; bounds: string; membership: string };
  display_timezone: string;
  status: "CURRENT";
  is_current: boolean;
  read_at: string;
  fence: ActionIndexFence;
  order: string;
  selection: string;
  rows: ActionIndexRow[];
  total_count: number;
  next_cursor: string | null;
  page: { limit: number; shown: number; is_first: boolean };
  zero_statement: string | null;
  not_included: string;
}

export type ActionIndexResult =
  | { status: "loaded"; value: ActionIndexBody }
  | { status: "not_found"; message: string | null }
  | { status: "unauthenticated"; message: string | null }
  | { status: "forbidden"; message: string | null }
  | { status: "basis_changed"; message: string | null; reason: string | null }
  | { status: "inconsistent"; message: string | null }
  | { status: "invalid"; message: string | null; code: string | null; field: string | null }
  | { status: "unavailable"; message: string | null };

export interface ActionIndexClient {
  getActionIndex(siteId: string, scope: ActionIndexScope): Promise<ActionIndexResult>;
}

function isIndexBody(value: unknown): value is ActionIndexBody {
  return (
    hasKeys(value, ["schema_version", "status", "rows", "total_count", "fence", "window", "read_at"]) &&
    (value as { schema_version: unknown }).schema_version === "site-action-index-1" &&
    (value as { status: unknown }).status === "CURRENT" &&
    Array.isArray((value as { rows: unknown }).rows) &&
    typeof (value as { total_count: unknown }).total_count === "number"
  );
}

const text = (value: unknown): string | null => (typeof value === "string" ? value : null);

export async function readActionIndex(path: string): Promise<ActionIndexResult> {
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
      return { status: "not_found", message };
    case 409:
      if (fields.code === "ACTION_INDEX_BASIS_CHANGED") {
        return { status: "basis_changed", message, reason: text(fields.reason) };
      }
      if (fields.code === "ACTION_INDEX_INCONSISTENT") {
        return { status: "inconsistent", message };
      }
      return { status: "unavailable", message };
    case 422:
      return { status: "invalid", message, code: text(fields.code), field: text(fields.field) };
    default:
      return { status: "unavailable", message };
  }
}

/** The scope as a query string (`from`, `to`, optional `limit` and `cursor`), shared by the API path and the URL. */
export function actionIndexQuery(scope: ActionIndexScope): string {
  const query = new URLSearchParams({ from: scope.from, to: scope.to });
  if (scope.limit) query.set("limit", String(scope.limit));
  if (scope.cursor) query.set("cursor", scope.cursor);
  return query.toString();
}

export function actionIndexPath(basePath: string, siteId: string, scope: ActionIndexScope): string {
  return `${basePath}/${encodeURIComponent(siteId)}/action-index?${actionIndexQuery(scope)}`;
}

export function createActionIndexClient(basePath: string = SITES_API_PATH): ActionIndexClient {
  return {
    getActionIndex(siteId, scope) {
      return readActionIndex(actionIndexPath(basePath, siteId, scope));
    },
  };
}
