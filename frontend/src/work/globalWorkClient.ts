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

/** W6-01e E2 (P-E2-1): the four stored operational record kinds. */
export type GlobalOperationalKind = "OPERATOR_LOG" | "MANUAL_READING" | "SHIFT_NOTE" | "SITE_VISIT";
export const GLOBAL_OPERATIONAL_KINDS: readonly GlobalOperationalKind[] = ["OPERATOR_LOG", "MANUAL_READING", "SHIFT_NOTE", "SITE_VISIT"];

/** W6-01e E2 (P-E2-1): the section 1 operational-records row, exactly. */
export interface GlobalOperationalRow {
  site_code: string;
  site_name: string;
  site_id: string;
  site_code_key: string;
  canonical_record_id: string;
  root_id: string;
  head_id: string;
  code: string;
  kind: GlobalOperationalKind;
  body: string;
  root_occurred_at: string;
  occurred_at: string;
  recorded_at: string;
  period_end: string | null;
  actor_kind: string;
  actor_id: string;
  quantity: string | null;
  unit: string | null;
  source_document_sha256: string | null;
  case_id: string | null;
  case_kind: "INCIDENT" | "MAINTENANCE_REQUEST" | null;
  case_code: string | null;
  state: "SUBMITTED";
  supersedes_record_id: string | null;
  correction_reason: string | null;
  source_provenance: GlobalWorkProvenance;
  links: { site: GlobalWorkLink; case: GlobalWorkLink | null };
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
export type GlobalOperationalBody = GlobalWorkEnvelope<GlobalOperationalRow, null>;

/** The list root a read asks for; it decides the `state_counts` shape the answer must carry (P-B2-2). */
export type GlobalWorkRoot = "incidents" | "maintenance" | "preventive" | "operational-records";

/**
 * The page query (A2Q10): window, optional cutoff and optional opaque cursor. Nothing else is forwarded. W6-01e
 * (P-E2-1): Operational records alone may carry `kind` (a stored kind; absent means `all`); the other roots never set
 * it, so their URLs and client calls are unchanged.
 */
export interface GlobalWorkQuery {
  from: string;
  to: string;
  known_at: string | null;
  cursor: string | null;
  kind?: GlobalOperationalKind;
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
  /** W6-01e E2 (P-E2-1): `GET /api/work/operational-records`; absent reads as `WORK_STORE_UNAVAILABLE`. */
  operationalRecords?(query: GlobalWorkQuery): Promise<GlobalWorkResult<GlobalOperationalBody>>;
  /** W6-01c C2: the request detail read (`global-work-detail-1`); absent reads as `WORK_STORE_UNAVAILABLE`. */
  detail?(query: GlobalWorkDetailQuery): Promise<GlobalWorkDetailResult>;
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
    operationalRecords(query) {
      // P-E2-1: `kind` reaches the API on this root only, and only when a stored kind is chosen (absent = all).
      const kind = query.kind ? `&kind=${encodeURIComponent(query.kind)}` : "";
      return readGlobalWork<GlobalOperationalBody>(
        `${basePath}/operational-records?${globalWorkApiQuery(query)}${kind}`,
        "operational-records",
      );
    },
    detail(query) {
      return readGlobalWorkDetail(`${basePath}/requests/${encodeURIComponent(query.case_id)}?${globalWorkDetailApiQuery(query)}`);
    },
  };
}

// ---------------------------------------------------------------------------------------------------------------
// W6-01c C2 (".agent/W6-01-build-spec.md" section 1 Detail DTO and the "C1-C3 pre-flight rulings" P-C1-1..11,
// P-C2-9): the request detail wire `GET /api/work/requests/{case_id}?site_id={site_code}[&known_at=]`. C2 owns these
// types for the whole C1 wire; C3/C4 import them. The detail result is separate from the list code union: the list
// copy map and its enumerable codes are unchanged.

export const GLOBAL_WORK_DETAIL_SCHEMA = "global-work-detail-1";

/** The page inputs a detail read forwards: the request ID, its Site code and an optional explicit cutoff. */
export interface GlobalWorkDetailQuery {
  case_id: string;
  site_id: string;
  known_at: string | null;
}

/** W4 `work-case-detail-1`, nested unchanged as `work_detail`. */
interface WorkCaseDetailEventBase {
  id: string;
  occurred_at: string;
  recorded_at: string;
  actor_kind: string;
  actor_id: string;
}
export type KnownWorkCaseEvent = WorkCaseDetailEventBase &
  (
    | { kind: "CREATED"; payload: Record<string, never> }
    | { kind: "ASSIGN"; payload: { assignee: string } }
    | { kind: "COMMENT"; payload: { text: string } }
    | { kind: "COMPLETE"; payload: { maintenance_record_id: string } }
    | { kind: "CLOSE" | "REOPEN" | "CANCEL"; payload: { reason: string } }
  );
export const KNOWN_WORK_CASE_EVENT_KINDS = ["CREATED", "ASSIGN", "COMMENT", "COMPLETE", "CLOSE", "REOPEN", "CANCEL"] as const;
export type UnknownWorkCaseEvent = WorkCaseDetailEventBase & { kind: string; payload: Record<string, unknown> };
export type WorkCaseDetailEvent = KnownWorkCaseEvent | UnknownWorkCaseEvent;
export function isKnownWorkCaseEvent(e: WorkCaseDetailEvent): e is KnownWorkCaseEvent {
  return (KNOWN_WORK_CASE_EVENT_KINDS as readonly string[]).includes(e.kind);
}

const EVENT_PAYLOAD_KEY: Readonly<Record<string, string>> = {
  ASSIGN: "assignee",
  COMMENT: "text",
  COMPLETE: "maintenance_record_id",
  CLOSE: "reason",
  REOPEN: "reason",
  CANCEL: "reason",
};

export interface WorkCaseDetailRecord {
  id: string;
  activity: string;
  outcome_note: string | null;
  occurred_at: string;
  recorded_at: string;
  supersedes_record_id: string | null;
}

export interface WorkCaseDetail {
  schema_version: string;
  site_code: string;
  case: {
    id: string;
    code: string;
    kind: string;
    asset_id: string | null;
    occurred_at: string;
    created_at: string;
    state: string;
    incident_id: string | null;
  };
  selected_revision: {
    id: string;
    revision_no: number;
    supersedes_revision_id: string | null;
    title: string;
    narrative: string;
    reason: string | null;
    recorded_at: string;
    actor_kind: string;
    actor_id: string;
    occurred_at: string;
  };
  finding_links: { finding_id: string; finding_revision_id: string }[];
  action_links: { action_id: string; action_event_id: string | null; kind?: string; finding_revision_id?: string }[];
  cited_accepted_evidence_ids: string[];
  events: WorkCaseDetailEvent[];
  records: WorkCaseDetailRecord[];
  source_provenance: GlobalWorkProvenance;
  coverage: { state: string; reason: string | null };
}

export interface GlobalWorkDetailRevision {
  id: string;
  revision_no: number;
  supersedes_revision_id: string | null;
  title: string;
  reason: string | null;
  occurred_at: string;
  recorded_at: string;
  actor_kind: string;
  actor_id: string;
}

export interface GlobalWorkDetailOperationalRecord {
  canonical_record_id: string;
  head_id: string;
  code: string;
  kind: string;
  body: string;
  root_occurred_at: string;
  occurred_at: string;
  recorded_at: string;
}

export interface GlobalWorkDetailBody {
  schema_version: typeof GLOBAL_WORK_DETAIL_SCHEMA;
  selected: { site_code: string; site_id: string; case_id: string; case_code: string; case_kind: string; known_at: string };
  work_detail: WorkCaseDetail;
  work_asset: { code: string; type: string } | null;
  history: { revisions: GlobalWorkDetailRevision[]; operational_records: GlobalWorkDetailOperationalRecord[] };
  links: {
    site: GlobalWorkLink;
    overview: GlobalWorkLink;
    record: GlobalWorkLink;
    history: GlobalWorkLink;
    source_incident: GlobalWorkLink | null;
    findings: GlobalWorkLink[];
    actions: GlobalWorkLink[];
  };
}

/** P-C2-9: the detail refusals; network failure and a malformed 200 read as `WORK_STORE_UNAVAILABLE`. */
export type GlobalWorkDetailRefusalCode =
  | "UNAUTHENTICATED"
  | "SITE_SCOPE_FORBIDDEN"
  | "SITE_NOT_FOUND"
  | "WORK_CASE_NOT_FOUND"
  | "INVALID_KNOWN_AT"
  | "WORK_STORE_UNAVAILABLE";

export type GlobalWorkDetailResult =
  | { status: "loaded"; value: GlobalWorkDetailBody }
  | { status: "refused"; code: GlobalWorkDetailRefusalCode };

/** P-C2-9 and A2Q6: the detail UI sentences (401, 422 and 503 reuse the list rows). */
export const GLOBAL_WORK_DETAIL_REFUSAL_COPY: Readonly<Record<GlobalWorkDetailRefusalCode, string>> = {
  UNAUTHENTICATED: GLOBAL_WORK_REFUSAL_COPY.UNAUTHENTICATED,
  SITE_SCOPE_FORBIDDEN: "No access to this Site's work request.",
  SITE_NOT_FOUND: "No imported Site found for this request.",
  WORK_CASE_NOT_FOUND: "No work case with this ID at this site.",
  INVALID_KNOWN_AT: GLOBAL_WORK_REFUSAL_COPY.INVALID_KNOWN_AT,
  WORK_STORE_UNAVAILABLE: GLOBAL_WORK_REFUSAL_COPY.WORK_STORE_UNAVAILABLE,
};

const DETAIL_STATUS: Readonly<Record<number, ReadonlySet<string>>> = {
  401: new Set(["UNAUTHENTICATED"]),
  403: new Set(["SITE_SCOPE_FORBIDDEN"]),
  404: new Set(["SITE_NOT_FOUND", "WORK_CASE_NOT_FOUND"]),
  422: new Set(["INVALID_KNOWN_AT"]),
  503: new Set(["WORK_STORE_UNAVAILABLE"]),
};

const isString = (value: unknown): value is string => typeof value === "string";
const isNullableString = (value: unknown): boolean => value === null || typeof value === "string";
const everyItem = (value: unknown, check: (item: unknown) => boolean): boolean => Array.isArray(value) && value.every(check);
const isLink = (value: unknown): boolean => isObject(value) && isString(value.label) && isNullableString(value.href);

function isWorkDetail(value: unknown): boolean {
  if (!isObject(value) || !isObject(value.case) || !isObject(value.selected_revision)) return false;
  const kase = value.case;
  const revision = value.selected_revision;
  return (
    isString(value.schema_version) &&
    isString(kase.id) &&
    isString(kase.code) &&
    isString(kase.kind) &&
    isString(kase.state) &&
    isNullableString(kase.asset_id) &&
    isNullableString(kase.incident_id) &&
    isString(revision.id) &&
    isString(revision.title) &&
    isString(revision.narrative) &&
    everyItem(value.finding_links, (x) => isObject(x) && isString(x.finding_id) && isString(x.finding_revision_id)) &&
    everyItem(
      value.action_links,
      (x) =>
        isObject(x) &&
        isString(x.action_id) &&
        isNullableString(x.action_event_id) &&
        (!("kind" in x) || isString(x.kind)) &&
        (!("finding_revision_id" in x) || isString(x.finding_revision_id)),
    ) &&
    everyItem(value.cited_accepted_evidence_ids, isString) &&
    everyItem(
      value.events,
      (x) =>
        isObject(x) &&
        isString(x.id) &&
        isString(x.kind) &&
        isObject(x.payload) &&
        isString(x.occurred_at) &&
        isString(x.recorded_at) &&
        isString(x.actor_kind) &&
        isString(x.actor_id) &&
        (!(x.kind in EVENT_PAYLOAD_KEY) || isString(x.payload[EVENT_PAYLOAD_KEY[x.kind]])),
    ) &&
    (value.events as unknown[]).some((x) => isObject(x) && x.kind === "CREATED") &&
    everyItem(
      value.records,
      (x) =>
        isObject(x) &&
        isString(x.id) &&
        isString(x.activity) &&
        isNullableString(x.outcome_note) &&
        isString(x.occurred_at) &&
        isString(x.recorded_at) &&
        isNullableString(x.supersedes_record_id),
    ) &&
    isObject(value.source_provenance) &&
    isString(value.source_provenance.classification) &&
    isObject(value.coverage)
  );
}

/** P-C2-9: the malformed-200 check for `global-work-detail-1`. */
export function isGlobalWorkDetailBody(value: unknown): value is GlobalWorkDetailBody {
  if (!isObject(value) || value.schema_version !== GLOBAL_WORK_DETAIL_SCHEMA) return false;
  const { selected, history, links, work_asset: asset } = value;
  return (
    isObject(selected) &&
    ["site_code", "site_id", "case_id", "case_code", "case_kind", "known_at"].every((k) => isString(selected[k])) &&
    isWorkDetail(value.work_detail) &&
    (asset === null || (isObject(asset) && isString(asset.code) && isString(asset.type))) &&
    isObject(history) &&
    everyItem(history.revisions, (x) =>
        isObject(x) &&
        isString(x.id) &&
        isString(x.title) &&
        typeof x.revision_no === "number" &&
        isNullableString(x.supersedes_revision_id) &&
        isNullableString(x.reason) &&
        isString(x.occurred_at) &&
        isString(x.recorded_at) &&
        isString(x.actor_kind) &&
        isString(x.actor_id),
    ) &&
    everyItem(
      history.operational_records,
      (x) =>
        isObject(x) &&
        ["canonical_record_id", "head_id", "code", "kind", "body", "root_occurred_at", "occurred_at", "recorded_at"].every(
          (k) => isString(x[k]),
        ),
    ) &&
    isObject(links) &&
    ["site", "overview", "record", "history"].every((k) => isLink(links[k])) &&
    (links.source_incident === null || isLink(links.source_incident)) &&
    everyItem(links.findings, isLink) &&
    everyItem(links.actions, isLink)
  );
}

/** The API query string: `site_id` and, only when the page URL supplied one, `known_at`. */
export function globalWorkDetailApiQuery(query: GlobalWorkDetailQuery): string {
  const params = new URLSearchParams({ site_id: query.site_id });
  if (query.known_at) params.set("known_at", query.known_at);
  return params.toString();
}

export async function readGlobalWorkDetail(path: string): Promise<GlobalWorkDetailResult> {
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
    return isGlobalWorkDetailBody(body) ? { status: "loaded", value: body } : { status: "refused", code: "WORK_STORE_UNAVAILABLE" };
  }
  const detail = isObject(body) ? body.detail : null;
  const code = isObject(detail) && typeof detail.code === "string" ? detail.code : null;
  const known = DETAIL_STATUS[response.status];
  return {
    status: "refused",
    code: code !== null && known !== undefined && known.has(code) ? (code as GlobalWorkDetailRefusalCode) : "WORK_STORE_UNAVAILABLE",
  };
}

const UUID = /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/;

/**
 * P-C2-14: the detail page query. Absent, empty or repeated `site_id` and a malformed `case_id` are the no-fetch
 * 404 sentence (`no-site` when `site_id` is absent); an invalid or repeated `known_at` is the no-fetch cutoff
 * sentence. Unknown keys are ignored.
 */
export type GlobalWorkDetailPageQuery =
  | { status: "valid"; query: GlobalWorkDetailQuery }
  | { status: "invalid"; reason: "no-site" | "not-found" | "known-at"; siteId: string | null };

export function globalWorkDetailPageQuery(caseId: string | undefined, params: URLSearchParams): GlobalWorkDetailPageQuery {
  const sites = params.getAll("site_id");
  const knowns = params.getAll("known_at");
  const siteId = sites.length === 1 && sites[0] !== "" ? sites[0] : null;
  if (sites.length === 0 || (sites.length === 1 && sites[0] === "")) return { status: "invalid", reason: "no-site", siteId: null };
  if (siteId === null || caseId === undefined || !UUID.test(caseId)) return { status: "invalid", reason: "not-found", siteId };
  if (knowns.length > 1) return { status: "invalid", reason: "known-at", siteId };
  const known = knowns.length === 1 ? knowns[0] : null;
  if (known !== null && (!INSTANT.test(known) || Number.isNaN(Date.parse(known)))) {
    return { status: "invalid", reason: "known-at", siteId };
  }
  return { status: "valid", query: { case_id: caseId, site_id: siteId, known_at: known } };
}

/** The app href for a request page: `site_id` and, only with an explicit cutoff, `known_at`. */
export function globalWorkRequestHref(path: string, query: Pick<GlobalWorkDetailQuery, "site_id" | "known_at">): string {
  const params = new URLSearchParams({ site_id: query.site_id });
  if (query.known_at) params.set("known_at", query.known_at);
  return `${path}?${params.toString()}`;
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

/**
 * The app href for a global page: `from`, `to`, `known_at` when present, `kind` when present (Operational records
 * only, P-E2-1), `cursor` when given.
 */
export function globalWorkHref(
  path: string,
  query: Pick<GlobalWorkQuery, "from" | "to" | "known_at" | "kind">,
  cursor?: string | null,
): string {
  const params = new URLSearchParams({ from: query.from, to: query.to });
  if (query.known_at) params.set("known_at", query.known_at);
  if (query.kind) params.set("kind", query.kind);
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
