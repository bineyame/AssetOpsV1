/**
 * W6-01a A2 / W6-01b B2-B3: the read-only global work list client, `GET /api/work/incidents`, `/maintenance` and
 * `/preventive` (`global-work-index-1`, `.agent/W6-01-build-spec.md` section 1, section 2, section 3.1 A2Q1-A2Q10
 * and the B1-B3 pre-flight rulings P-B2-1/2 and P-B3-1).
 *
 * The client asks for five rows, forwards only `from`, `to`, `known_at` and `cursor` exactly as given, and maps
 * every refusal, network failure or malformed answer to a typed refusal. A refusal never reads as zero: it carries
 * no rows and no count.
 */

export const GLOBAL_WORK_API_PATH = "/api/work";
export const GLOBAL_WORK_SCHEMA = "global-work-index-1";
/** Section 2: the UI sends `limit=5` for every root. */
export const GLOBAL_WORK_PAGE_LIMIT = 5;

export interface GlobalWorkLink {
  label: string;
  href: string | null;
}

export interface GlobalWorkProvenance {
  classification: string;
  state: string;
  source_ids: string[];
  evidence_ids: string[];
  basis_sha256: string;
  reasons: string[];
}

export type GlobalIncidentState = "OPEN" | "IN_PROGRESS" | "CLOSED";

export interface GlobalIncidentRow {
  site_code: string;
  site_name: string;
  site_id: string;
  site_code_key: string;
  case_id: string;
  code: string;
  kind: "INCIDENT";
  revision_id: string;
  title: string;
  narrative: string;
  occurred_at: string;
  created_at: string;
  recorded_at: string;
  state: GlobalIncidentState;
  owner: string | null;
  asset_id: string | null;
  asset_label: string | null;
  incident_id: string | null;
  linked_request_codes: string[];
  finding_links: GlobalWorkLink[];
  action_links: GlobalWorkLink[];
  source_provenance: GlobalWorkProvenance;
  links: { site: GlobalWorkLink; site_incidents: GlobalWorkLink };
}

export type GlobalMaintenanceState = "OPEN" | "IN_PROGRESS" | "COMPLETED" | "CANCELLED";

export interface GlobalMaintenanceRow {
  site_code: string;
  site_name: string;
  site_id: string;
  site_code_key: string;
  case_id: string;
  code: string;
  kind: "MAINTENANCE_REQUEST";
  revision_id: string;
  title: string;
  narrative: string;
  occurred_at: string;
  created_at: string;
  recorded_at: string;
  state: GlobalMaintenanceState;
  owner: string | null;
  asset_id: string | null;
  asset_label: string | null;
  incident_id: string | null;
  record_id: string | null;
  activity: string | null;
  outcome_note: string | null;
  finding_links: GlobalWorkLink[];
  action_links: GlobalWorkLink[];
  source_provenance: GlobalWorkProvenance;
  links: { site: GlobalWorkLink; site_maintenance: GlobalWorkLink; detail: GlobalWorkLink | null };
}

export interface GlobalPreventiveRow {
  site_code: string;
  site_name: string;
  site_id: string;
  site_code_key: string;
  canonical_plan_id: string;
  root_id: string;
  head_id: string;
  code: string;
  title: string;
  trigger_kind: "CALENDAR" | "RUN_HOURS";
  next_due_at: string | null;
  next_due_hours: string | null;
  state: "DRAFT";
  asset_id: string | null;
  asset_label: string | null;
  root_occurred_at: string;
  occurred_at: string;
  recorded_at: string;
  supersedes_plan_id: string | null;
  correction_reason: string | null;
  source_provenance: GlobalWorkProvenance;
  links: { site: GlobalWorkLink };
}

export type GlobalWorkStatus = "CURRENT" | "HISTORICAL" | "EMPTY_SCOPE" | "PARTIAL";

export interface GlobalWorkEnvelope<Row, Counts> {
  schema_version: typeof GLOBAL_WORK_SCHEMA;
  scope: { tenant_id: string | null; authorized_site_count: number; covered_site_count: number; access_basis: string };
  window: { from: string; to: string; bounds: string };
  known_at: string;
  status: GlobalWorkStatus;
  coverage: {
    state: "COMPLETE" | "EMPTY_SCOPE";
    reason: string | null;
    sites: { site_code: string; site_id: string; state: "COVERED" }[];
  };
  total_count: number;
  state_counts: Counts;
  rows: Row[];
  next_cursor: string | null;
  selection_token: string;
}

export type GlobalIncidentsBody = GlobalWorkEnvelope<GlobalIncidentRow, Record<GlobalIncidentState, number>>;
export type GlobalMaintenanceBody = GlobalWorkEnvelope<GlobalMaintenanceRow, Record<GlobalMaintenanceState, number>>;
export type GlobalPreventiveBody = GlobalWorkEnvelope<GlobalPreventiveRow, null>;

/** The list root a read asks for; it decides the `state_counts` shape the answer must carry (P-B2-2). */
export type GlobalWorkRoot = "incidents" | "maintenance" | "preventive" | "operational-records";

/** The page query (A2Q10): window, optional cutoff and optional opaque cursor. Nothing else is forwarded. */
export interface GlobalWorkQuery {
  from: string;
  to: string;
  known_at: string | null;
  cursor: string | null;
}

export type GlobalWorkRefusalCode =
  | "UNAUTHENTICATED"
  | "INVALID_WINDOW"
  | "INVALID_KNOWN_AT"
  | "INVALID_LIMIT"
  | "INVALID_CURSOR"
  | "WORK_BASIS_CHANGED"
  | "WORK_STORE_UNAVAILABLE";

export type GlobalWorkResult<T> = { status: "loaded"; value: T } | { status: "refused"; code: GlobalWorkRefusalCode };

/** A2Q6: the UI sentence for each refusal; network failure and a malformed 200 read as the store row. */
export const GLOBAL_WORK_REFUSAL_COPY: Readonly<Record<GlobalWorkRefusalCode, string>> = {
  UNAUTHENTICATED: "Sign in to see work records.",
  INVALID_WINDOW: "Choose a valid date range of at most 31 days.",
  INVALID_KNOWN_AT: "Choose a valid cutoff time.",
  INVALID_LIMIT: "Choose a page size from 1 to 100.",
  INVALID_CURSOR: "The list changed. Reload the first page.",
  WORK_BASIS_CHANGED: "The list changed. Reload the first page.",
  WORK_STORE_UNAVAILABLE: "Work records could not be read. Reload.",
};

/** A2Q6: the codes whose action is the `Reload the first page` link. */
export const GLOBAL_WORK_FIRST_PAGE_CODES: ReadonlySet<GlobalWorkRefusalCode> = new Set([
  "INVALID_CURSOR",
  "WORK_BASIS_CHANGED",
]);

const KNOWN_CODES = new Set<string>(Object.keys(GLOBAL_WORK_REFUSAL_COPY));

/**
 * `maintenance` and `preventive` are optional (P-B2-2), so a one-method incidents client still type-checks; a page
 * whose method is absent reads `WORK_STORE_UNAVAILABLE`. `createGlobalWorkClient()` supplies every method.
 */
export interface GlobalWorkClient {
  incidents(query: GlobalWorkQuery): Promise<GlobalWorkResult<GlobalIncidentsBody>>;
  maintenance?(query: GlobalWorkQuery): Promise<GlobalWorkResult<GlobalMaintenanceBody>>;
  preventive?(query: GlobalWorkQuery): Promise<GlobalWorkResult<GlobalPreventiveBody>>;
}

const isObject = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value !== null && !Array.isArray(value);

/** Incidents and maintenance carry an object `state_counts`; preventive and operational records carry null only. */
const NULL_COUNTS: ReadonlySet<GlobalWorkRoot> = new Set(["preventive", "operational-records"]);

function isEnvelope(value: unknown, root: GlobalWorkRoot): boolean {
  return (
    isObject(value) &&
    value.schema_version === GLOBAL_WORK_SCHEMA &&
    Array.isArray(value.rows) &&
    typeof value.total_count === "number" &&
    typeof value.known_at === "string" &&
    typeof value.status === "string" &&
    (NULL_COUNTS.has(root) ? value.state_counts === null : isObject(value.state_counts)) &&
    isObject(value.window) &&
    (value.next_cursor === null || typeof value.next_cursor === "string")
  );
}

/** The API query string: the page query plus `limit=5`. */
export function globalWorkApiQuery(query: GlobalWorkQuery): string {
  const params = new URLSearchParams({ from: query.from, to: query.to });
  if (query.known_at) params.set("known_at", query.known_at);
  if (query.cursor) params.set("cursor", query.cursor);
  params.set("limit", String(GLOBAL_WORK_PAGE_LIMIT));
  return params.toString();
}

export async function readGlobalWork<T>(path: string, root: GlobalWorkRoot): Promise<GlobalWorkResult<T>> {
  let response: Response;
  try {
    response = await fetch(path);
  } catch {
    return { status: "refused", code: "WORK_STORE_UNAVAILABLE" };
  }
  let body: unknown = null;
  try {
    body = await response.json();
  } catch {
    body = null;
  }
  if (response.ok) {
    return isEnvelope(body, root) ? { status: "loaded", value: body as T } : { status: "refused", code: "WORK_STORE_UNAVAILABLE" };
  }
  const detail = isObject(body) ? body.detail : null;
  const code = isObject(detail) && typeof detail.code === "string" ? detail.code : null;
  return { status: "refused", code: code !== null && KNOWN_CODES.has(code) ? (code as GlobalWorkRefusalCode) : "WORK_STORE_UNAVAILABLE" };
}

export function createGlobalWorkClient(basePath: string = GLOBAL_WORK_API_PATH): GlobalWorkClient {
  return {
    incidents(query) {
      return readGlobalWork<GlobalIncidentsBody>(`${basePath}/incidents?${globalWorkApiQuery(query)}`, "incidents");
    },
    maintenance(query) {
      return readGlobalWork<GlobalMaintenanceBody>(`${basePath}/maintenance?${globalWorkApiQuery(query)}`, "maintenance");
    },
    preventive(query) {
      return readGlobalWork<GlobalPreventiveBody>(`${basePath}/preventive?${globalWorkApiQuery(query)}`, "preventive");
    },
  };
}

// ---------------------------------------------------------------------------------------------------------------
// The page query contract (section 1, amended by A2Q10): one `from` and `to` (UTC midnights, in order, 1-31 days),
// an optional single UTC `known_at` and an optional `cursor`. Both bounds absent means the seven complete UTC days
// ending today 00:00 UTC; one absent bound is INVALID_WINDOW. Other keys are ignored and never forwarded.

const DAY_MS = 24 * 60 * 60 * 1000;
const MIDNIGHT = /^\d{4}-\d{2}-\d{2}T00:00:00Z$/;
const INSTANT = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?Z$/;

/** The seven complete UTC days ending today 00:00 UTC, `[from, to)`. */
export function defaultGlobalWorkWindow(now: number = Date.now()): { from: string; to: string } {
  const today = `${new Date(now).toISOString().slice(0, 10)}T00:00:00Z`;
  const from = new Date(Date.parse(today) - 7 * DAY_MS).toISOString().slice(0, 10);
  return { from: `${from}T00:00:00Z`, to: today };
}

function validMidnight(value: string): boolean {
  return MIDNIGHT.test(value) && !Number.isNaN(Date.parse(value)) && new Date(value).toISOString().slice(0, 10) === value.slice(0, 10);
}

export type GlobalWorkPageQuery =
  | { status: "valid"; query: GlobalWorkQuery }
  | { status: "invalid"; code: "INVALID_WINDOW" | "INVALID_KNOWN_AT" };

export function globalWorkPageQuery(params: URLSearchParams, now?: number): GlobalWorkPageQuery {
  const froms = params.getAll("from");
  const tos = params.getAll("to");
  const knowns = params.getAll("known_at");
  const cursors = params.getAll("cursor");
  let window: { from: string; to: string };
  if (froms.length === 0 && tos.length === 0) {
    window = defaultGlobalWorkWindow(now);
  } else {
    if (froms.length !== 1 || tos.length !== 1) return { status: "invalid", code: "INVALID_WINDOW" };
    const [from, to] = [froms[0], tos[0]];
    if (!validMidnight(from) || !validMidnight(to)) return { status: "invalid", code: "INVALID_WINDOW" };
    const days = (Date.parse(to) - Date.parse(from)) / DAY_MS;
    if (days < 1 || days > 31) return { status: "invalid", code: "INVALID_WINDOW" };
    window = { from, to };
  }
  if (knowns.length > 1) return { status: "invalid", code: "INVALID_KNOWN_AT" };
  const known = knowns.length === 1 ? knowns[0] : null;
  if (known !== null && (!INSTANT.test(known) || Number.isNaN(Date.parse(known)))) {
    return { status: "invalid", code: "INVALID_KNOWN_AT" };
  }
  return { status: "valid", query: { ...window, known_at: known, cursor: cursors.length > 0 ? cursors[0] : null } };
}

/** The app href for a global page: `from`, `to`, `known_at` when present, `cursor` when given. */
export function globalWorkHref(path: string, query: Pick<GlobalWorkQuery, "from" | "to" | "known_at">, cursor?: string | null): string {
  const params = new URLSearchParams({ from: query.from, to: query.to });
  if (query.known_at) params.set("known_at", query.known_at);
  if (cursor) params.set("cursor", cursor);
  return `${path}?${params.toString()}`;
}

const DATE_FORMAT = new Intl.DateTimeFormat("en-GB", {
  day: "2-digit",
  month: "short",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
  hourCycle: "h23",
  timeZone: "UTC",
});

/** Section 2: `22 Oct 2026, 12:00 UTC` (en-GB, explicit UTC, no local-zone conversion). */
export function globalWorkUtc(instant: string): string {
  const ms = Date.parse(instant);
  if (Number.isNaN(ms)) return instant;
  return `${DATE_FORMAT.format(new Date(ms))} UTC`;
}
