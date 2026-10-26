/**
 * W4-01 commit 5 (`I-incident-ui`, `I-maintenance-ui`): the Site Incident and
 * Maintenance list reads, `GET /api/sites/{site}/work/{incidents|maintenance}`
 * (`site-work-index-1`, `.agent/W4-01-build-spec.md` B1/B8-B10, Run 7 q7-5).
 *
 * The client asks for five rows (`limit=5`), passes the window, an optional
 * fixed cutoff (`known_at`) and the server cursor exactly as given, and maps
 * every refusal to a typed state. A refusal never reads as an empty list: it
 * carries no rows and no count.
 */
import { SITES_API_PATH } from "./siteDirectoryClient";
import { hasKeys, isObject } from "./evidenceRead";
import type { SourceProvenance } from "./sourceProvenance";

export type WorkKind = "incidents" | "maintenance";

/** The rows one page asks for (B10/S19: five rows inside the panel). */
export const WORK_PAGE_LIMIT = 5;

export interface WorkScope {
  /** UTC instant, window start (included). */
  from: string;
  /** UTC instant, window end (excluded). */
  to: string;
  /** The fixed cutoff the earlier page was read at; null on a fresh first page. */
  knownAt?: string | null;
  /** The server's opaque cursor; null for page one. */
  cursor?: string | null;
  /** Page size; the lists use the fixed page limit, the subtab counts ask for one row. */
  limit?: number;
}

export interface WorkFindingLink {
  finding_id: string;
  finding_revision_id: string;
  label: string;
  /** Present only when the pinned revision is selectable at the cutoff. */
  href: string | null;
}

export interface WorkActionLink {
  /** W5-02a: present only on an explicit cold domain Action link. */
  kind?: "DOMAIN_ACTION";
  action_id: string;
  /** Null for a domain Action link, which has no W1 Action event. */
  action_event_id: string | null;
  /** A domain Action link's pinned Finding revision. */
  finding_revision_id?: string;
  label: string;
  href: string | null;
}

export interface WorkRow {
  case_id: string;
  revision_id: string;
  code: string;
  title: string;
  narrative: string;
  occurred_at: string;
  recorded_at: string;
  state: string;
  asset_id: string | null;
  asset_label: string | null;
  finding_links: WorkFindingLink[];
  action_links: WorkActionLink[];
  url: string | null;
  source_provenance: SourceProvenance | null;
  /** Maintenance rows only. */
  request_state?: string;
  incident_id?: string | null;
  record_id?: string | null;
  activity?: string | null;
  outcome_note?: string | null;
  outcome_state?: string;
  next_evidence?: string | null;
  next_evidence_copy?: string;
}

export interface WorkIndexBody {
  schema_version: "site-work-index-1";
  site_code: string;
  site_name: string;
  window: { from: string; to: string; bounds: string };
  known_at: string;
  status: string;
  coverage: { state: string; reason: string | null };
  source_provenance: SourceProvenance | null;
  total_count: number;
  rows: WorkRow[];
  next_cursor: string | null;
  selection_token: string;
}

export type WorkRefusalStatus =
  | "unauthenticated"
  | "forbidden"
  | "not_found"
  | "basis_changed"
  | "invalid"
  | "unavailable";

export type WorkIndexResult =
  | { status: "loaded"; value: WorkIndexBody }
  | { status: WorkRefusalStatus; code: string | null; message: string | null };

export interface WorkClient {
  getWorkIndex(siteId: string, kind: WorkKind, scope: WorkScope): Promise<WorkIndexResult>;
}

function isWorkBody(value: unknown): value is WorkIndexBody {
  return (
    hasKeys(value, ["schema_version", "status", "rows", "total_count", "window", "known_at", "coverage"]) &&
    (value as { schema_version: unknown }).schema_version === "site-work-index-1" &&
    Array.isArray((value as { rows: unknown }).rows) &&
    typeof (value as { total_count: unknown }).total_count === "number"
  );
}

const text = (value: unknown): string | null => (typeof value === "string" ? value : null);

export async function readWorkIndex(path: string): Promise<WorkIndexResult> {
  let response: Response;
  try {
    response = await fetch(path);
  } catch {
    return { status: "unavailable", code: null, message: null };
  }
  let body: unknown = null;
  try {
    body = await response.json();
  } catch {
    body = null;
  }
  if (response.ok && isWorkBody(body)) return { status: "loaded", value: body };
  const detail = isObject(body) ? body.detail : null;
  const fields = isObject(detail) ? detail : {};
  const code = text(fields.code);
  const message = typeof detail === "string" ? detail : text(fields.message);
  switch (response.status) {
    case 401:
      return { status: "unauthenticated", code, message };
    case 403:
      return { status: "forbidden", code, message };
    case 404:
      return { status: "not_found", code, message };
    case 409:
      return { status: code === "WORK_BASIS_CHANGED" ? "basis_changed" : "unavailable", code, message };
    case 422:
      return { status: "invalid", code, message };
    default:
      return { status: "unavailable", code, message };
  }
}

/** The API query: window, five rows, and the bound cutoff and cursor when present. */
export function workIndexQuery(scope: WorkScope): string {
  const query = new URLSearchParams({ from: scope.from, to: scope.to, limit: String(scope.limit ?? WORK_PAGE_LIMIT) });
  if (scope.knownAt) query.set("known_at", scope.knownAt);
  if (scope.cursor) query.set("cursor", scope.cursor);
  return query.toString();
}

/** The page URL query (`from,to,known_at,cursor`, B10): the same scope, without the fixed limit. */
export function workPageQuery(scope: WorkScope): string {
  const query = new URLSearchParams({ from: scope.from, to: scope.to });
  if (scope.knownAt) query.set("known_at", scope.knownAt);
  if (scope.cursor) query.set("cursor", scope.cursor);
  return query.toString();
}

export function workIndexPath(basePath: string, siteId: string, kind: WorkKind, scope: WorkScope): string {
  return `${basePath}/${encodeURIComponent(siteId)}/work/${kind}?${workIndexQuery(scope)}`;
}

export function createWorkClient(basePath: string = SITES_API_PATH): WorkClient {
  return {
    getWorkIndex(siteId, kind, scope) {
      return readWorkIndex(workIndexPath(basePath, siteId, kind, scope));
    },
  };
}

/**
 * post-W6 W5-cold R338 (B14-09; W5 rulings 1, as W6 Q7): seven UTC calendar days including today,
 * `[today − 6 days 00:00Z, tomorrow 00:00Z)`. Shared by cold/EV Actions and every Site type's Work cases.
 */
export function defaultWorkWindow(now: Date = new Date()): { from: string; to: string } {
  const today = new Date(`${now.toISOString().slice(0, 10)}T00:00:00Z`);
  const from = new Date(today);
  from.setUTCDate(from.getUTCDate() - 6);
  const to = new Date(today);
  to.setUTCDate(to.getUTCDate() + 1);
  return { from: `${from.toISOString().slice(0, 10)}T00:00:00Z`, to: `${to.toISOString().slice(0, 10)}T00:00:00Z` };
}
