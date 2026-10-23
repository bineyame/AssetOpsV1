/**
 * W5-02 K2a (`.agent/W5-02-build-spec.md` "Shared Site UI and mock slots", U1, U3, P-K2a-33..36/48): the typed
 * client for the Site domain Action reads mounted by `backend/assetops_backend/domain_work_api.py`.
 *
 * - `GET /api/sites/{site}/domain-work/action-index?from=&to=&limit=5[&known_at=][&cursor=]` is the union of the
 *   Site's W1 battery Actions and its cold-chain domain Actions (`site-domain-action-index-1`).
 * - `GET /api/sites/{site}/domain-work/actions/{id}[?known_at=]` is one domain Action's declared intent
 *   (`domain-action-intent-read-1`).
 *
 * Every refusal is a named state, never a thrown error and never an empty list. A network failure and a malformed
 * success each carry their own fixed sentence. The page size is fixed to five here; it is not a URL query. The client
 * owns parsing only; labels and criterion copy live in `coldWorkPresentation.ts`.
 */
import { SITES_API_PATH } from "./siteDirectoryClient";
import { isObject } from "./evidenceRead";
import type { ActionIndexState } from "./actionIndexClient";

export const DOMAIN_INDEX_SCHEMA = "site-domain-action-index-1";
export const DOMAIN_DETAIL_SCHEMA = "domain-action-intent-read-1";
/** U3: the client requests five rows; the list folds after four. */
export const DOMAIN_INDEX_LIMIT = 5;
export const COLD_DOMAIN = "COLDCHAIN";

/** Spec "Mock element and literal ledger": network error and malformed 200. */
export const COLD_WORK_UNREACHABLE = "The cold work read could not be reached.";
export const COLD_WORK_UNEXPECTED = "The cold work read answered in an unexpected shape.";

export const DOMAIN_STATUSES = ["CURRENT", "HISTORICAL", "PENDING_RECOMPUTE", "STALE_SOURCE", "UNKNOWN"] as const;
export type DomainStatus = (typeof DOMAIN_STATUSES)[number];
export const COVERAGE_STATES = ["UNKNOWN", "PARTIAL", "COMPLETE"] as const;
export type CoverageState = (typeof COVERAGE_STATES)[number];

/** The page query the Site Work URL carries for the cold Actions tab: `[from,to)`, an optional cutoff and cursor. */
export interface DomainIndexScope {
  from: string;
  to: string;
  knownAt: string | null;
  cursor: string | null;
}

interface DomainRowBase {
  action_id: string;
  action_code: string;
  title: string | null;
  owner_label: string | null;
  due_at: string | null;
  raised_at: string;
  recorded_at: string;
  origin: { finding_id: string; finding_revision_id: string; label: string; href: string | null };
  criterion_summary: string | null;
  links: { action: string; history: string | null };
}

/** A cold-chain domain Action row: stored title/owner/due, state always `OPEN`. */
export interface DomainActionRow extends DomainRowBase {
  domain: "COLDCHAIN";
  title: string;
  state: "OPEN";
}

/** A W1 battery Action row on the same Site: W1 state object, no title, no criterion. */
export interface W1UnionRow extends DomainRowBase {
  domain: string;
  state: ActionIndexState;
}

export type DomainIndexRow = DomainActionRow | W1UnionRow;

export interface DomainIndexBody {
  schema_version: typeof DOMAIN_INDEX_SCHEMA;
  site_code: string;
  window: { from: string; to: string; bounds: string };
  known_at: string;
  status: DomainStatus;
  coverage: { state: CoverageState; reason: string | null };
  total_count: number;
  all_due_dates_unset: boolean;
  rows: DomainIndexRow[];
  next_cursor: string | null;
  selection_token: string;
}

export interface DomainCriterion {
  key: string;
  label: string;
  required_evidence: string;
}

export interface DomainActionDetail {
  schema_version: typeof DOMAIN_DETAIL_SCHEMA;
  site_code: string;
  action: {
    id: string;
    action_code: string;
    domain: "COLDCHAIN";
    title: string;
    owner_label: string | null;
    due_at: string | null;
    raised_at: string;
    recorded_at: string;
    state: "OPEN";
  };
  known_at: string;
  status: DomainStatus;
  intent: { id: string; recorded_at: string; criteria: DomainCriterion[]; basis: Record<string, unknown> } | null;
  results: { key: string; result: string; evidence_ids: string[] }[] | null;
  links: {
    finding: { label: string; href: string | null };
    work: Record<string, string | null>;
  };
  source_provenance: unknown;
  selection_token: string;
}

/** A refused or unreadable read: the server's code and message, or the fixed network/shape sentence. */
export interface DomainRefusal {
  status: "refused";
  /** HTTP status, or null when the server was not reached. */
  http: number | null;
  code: string | null;
  message: string;
}

export type DomainIndexResult =
  | { status: "loaded"; value: DomainIndexBody }
  | { status: "basis_changed"; http: 409; code: "WORK_BASIS_CHANGED"; message: string }
  | DomainRefusal;

export type DomainDetailResult =
  | { status: "loaded"; value: DomainActionDetail }
  | { status: "not_found"; http: 404; code: string; message: string }
  | DomainRefusal;

export interface DomainActionClient {
  getIndex(siteCode: string, scope: DomainIndexScope): Promise<DomainIndexResult>;
  getDetail(siteCode: string, actionId: string, knownAt: string | null): Promise<DomainDetailResult>;
}

const isString = (value: unknown): value is string => typeof value === "string";
const isNullableString = (value: unknown): value is string | null => value === null || typeof value === "string";
const isCount = (value: unknown): value is number => typeof value === "number" && Number.isInteger(value) && value >= 0;
const isStatus = (value: unknown): value is DomainStatus => (DOMAIN_STATUSES as readonly unknown[]).includes(value);

/** Exactly these keys: the K1b envelopes are exhaustive. */
function exactKeys(value: unknown, keys: readonly string[]): value is Record<string, unknown> {
  if (!isObject(value)) return false;
  const own = Object.keys(value);
  return own.length === keys.length && keys.every((key) => key in value);
}

const ROW_KEYS = [
  "action_id",
  "action_code",
  "domain",
  "title",
  "owner_label",
  "due_at",
  "raised_at",
  "recorded_at",
  "origin",
  "state",
  "criterion_summary",
  "links",
] as const;
const INDEX_KEYS = [
  "schema_version",
  "site_code",
  "window",
  "known_at",
  "status",
  "coverage",
  "total_count",
  "all_due_dates_unset",
  "rows",
  "next_cursor",
  "selection_token",
] as const;
const DETAIL_KEYS = [
  "schema_version",
  "site_code",
  "action",
  "known_at",
  "status",
  "intent",
  "results",
  "links",
  "source_provenance",
  "selection_token",
] as const;

function isW1State(value: unknown): value is ActionIndexState {
  return isObject(value) && isString(value.application) && isCount(value.failed_attempts);
}

function isRow(value: unknown): value is DomainIndexRow {
  if (!exactKeys(value, ROW_KEYS)) return false;
  const origin = value.origin;
  const links = value.links;
  const shared =
    isString(value.action_id) &&
    isString(value.action_code) &&
    isString(value.domain) &&
    isNullableString(value.owner_label) &&
    isNullableString(value.due_at) &&
    isString(value.raised_at) &&
    isString(value.recorded_at) &&
    isNullableString(value.criterion_summary) &&
    isObject(origin) &&
    isString(origin.finding_id) &&
    isString(origin.finding_revision_id) &&
    isString(origin.label) &&
    isNullableString(origin.href) &&
    isObject(links) &&
    isString(links.action) &&
    isNullableString(links.history);
  if (!shared) return false;
  if (value.domain === COLD_DOMAIN) {
    return isString(value.title) && value.state === "OPEN" && links.history === null;
  }
  // A W1 battery row: no title, no criterion, the W1 state object.
  return value.title === null && value.criterion_summary === null && isW1State(value.state);
}

function isIndexBody(value: unknown, siteCode: string): value is DomainIndexBody {
  if (!exactKeys(value, INDEX_KEYS)) return false;
  const window = value.window;
  const coverage = value.coverage;
  const ok =
    value.schema_version === DOMAIN_INDEX_SCHEMA &&
    value.site_code === siteCode &&
    isObject(window) &&
    isString(window.from) &&
    isString(window.to) &&
    isString(window.bounds) &&
    isString(value.known_at) &&
    isStatus(value.status) &&
    isObject(coverage) &&
    (COVERAGE_STATES as readonly unknown[]).includes(coverage.state) &&
    isNullableString(coverage.reason) &&
    isCount(value.total_count) &&
    typeof value.all_due_dates_unset === "boolean" &&
    Array.isArray(value.rows) &&
    value.rows.every(isRow) &&
    isNullableString(value.next_cursor) &&
    isString(value.selection_token);
  if (!ok) return false;
  const rows = value.rows as unknown[];
  const total = value.total_count as number;
  // The count is the full selected set; a page never holds more, and a zero is only a complete selection.
  if (rows.length > total) return false;
  if (total === 0 && (coverage as { state: unknown }).state !== "COMPLETE") return false;
  return true;
}

function isDetail(value: unknown, siteCode: string, actionId: string): value is DomainActionDetail {
  if (!exactKeys(value, DETAIL_KEYS)) return false;
  const action = value.action;
  const links = value.links;
  const intent = value.intent;
  const results = value.results;
  return (
    value.schema_version === DOMAIN_DETAIL_SCHEMA &&
    value.site_code === siteCode &&
    isObject(action) &&
    isString(action.id) &&
    action.id.toLowerCase() === actionId.toLowerCase() &&
    isString(action.action_code) &&
    // P-K2a-48: the domain is read from `action.domain`, never inferred from the Site type.
    action.domain === COLD_DOMAIN &&
    isString(action.title) &&
    isNullableString(action.owner_label) &&
    isNullableString(action.due_at) &&
    isString(action.raised_at) &&
    isString(action.recorded_at) &&
    action.state === "OPEN" &&
    isString(value.known_at) &&
    isStatus(value.status) &&
    (intent === null ||
      (isObject(intent) &&
        isString(intent.id) &&
        isString(intent.recorded_at) &&
        Array.isArray(intent.criteria) &&
        intent.criteria.every((c) => isObject(c) && isString(c.key) && isString(c.label) && isString(c.required_evidence)) &&
        isObject(intent.basis))) &&
    (results === null ||
      (Array.isArray(results) &&
        results.every((r) => isObject(r) && isString(r.key) && isString(r.result) && Array.isArray(r.evidence_ids)))) &&
    // An intent and its results arrive together; a missing declaration has neither.
    (intent === null) === (results === null) &&
    isObject(links) &&
    isObject(links.finding) &&
    isString(links.finding.label) &&
    isNullableString(links.finding.href) &&
    isObject(links.work) &&
    isString(value.selection_token)
  );
}

/** The refusal body `{detail:{code,message}}` (the detail read also carries `intent:null,results:null`). */
function refusalOf(http: number, body: unknown): { code: string; message: string } | null {
  if (!isObject(body) || !isObject(body.detail)) return null;
  const detail = body.detail;
  if (!isString(detail.code) || !isString(detail.message)) return null;
  // A refused read never carries a declaration or results, wherever the null pair is placed.
  for (const holder of [body, detail]) {
    if ("intent" in holder && holder.intent !== null) return null;
    if ("results" in holder && holder.results !== null) return null;
  }
  return http >= 400 ? { code: detail.code, message: detail.message } : null;
}

async function readJson(path: string): Promise<{ http: number; body: unknown } | null> {
  let response: Response;
  try {
    response = await fetch(path);
  } catch {
    return null;
  }
  let body: unknown = undefined;
  try {
    body = await response.json();
  } catch {
    body = undefined;
  }
  return { http: response.status, body };
}

const unreachable = (): DomainRefusal => ({ status: "refused", http: null, code: null, message: COLD_WORK_UNREACHABLE });
const unexpected = (http: number): DomainRefusal => ({ status: "refused", http, code: null, message: COLD_WORK_UNEXPECTED });

/** One UTC instant (`Z` or `+00:00`), as the server's window and cutoff parsers accept. */
export function isUtcInstant(value: string): boolean {
  const match = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2}(?:\.\d{1,6})?)?(Z|\+00:00)$/.exec(value);
  return match !== null && !Number.isNaN(new Date(value).getTime());
}

/**
 * U1/U3 "invalid page query reads nothing": a window or cutoff the server would refuse is refused here, before any
 * fetch, with the server's own literal for that code (`work/model.py` MESSAGES).
 */
export function invalidScope(scope: DomainIndexScope): DomainRefusal | null {
  const from = isUtcInstant(scope.from) ? new Date(scope.from).getTime() : NaN;
  const to = isUtcInstant(scope.to) ? new Date(scope.to).getTime() : NaN;
  if (Number.isNaN(from) || Number.isNaN(to) || !(from < to) || to - from > 31 * 24 * 3600 * 1000) {
    return { status: "refused", http: null, code: "INVALID_WINDOW", message: "The window may span at most 31 days." };
  }
  if (scope.knownAt !== null && !isUtcInstant(scope.knownAt)) return invalidKnownAt();
  return null;
}

function invalidKnownAt(): DomainRefusal {
  return {
    status: "refused",
    http: null,
    code: "INVALID_KNOWN_AT",
    message: "'known_at' must be one UTC instant no later than the read time.",
  };
}

export function domainIndexPath(basePath: string, siteCode: string, scope: DomainIndexScope): string {
  const query = new URLSearchParams({ from: scope.from, to: scope.to, limit: String(DOMAIN_INDEX_LIMIT) });
  if (scope.knownAt) query.set("known_at", scope.knownAt);
  if (scope.cursor) query.set("cursor", scope.cursor);
  return `${basePath}/${encodeURIComponent(siteCode)}/domain-work/action-index?${query.toString()}`;
}

export function domainDetailPath(basePath: string, siteCode: string, actionId: string, knownAt: string | null): string {
  const base = `${basePath}/${encodeURIComponent(siteCode)}/domain-work/actions/${encodeURIComponent(actionId)}`;
  return knownAt ? `${base}?${new URLSearchParams({ known_at: knownAt }).toString()}` : base;
}

export async function readDomainIndex(path: string, siteCode: string): Promise<DomainIndexResult> {
  const read = await readJson(path);
  if (read === null) return unreachable();
  if (read.http === 200) return isIndexBody(read.body, siteCode) ? { status: "loaded", value: read.body } : unexpected(200);
  const refusal = refusalOf(read.http, read.body);
  if (refusal === null) return unexpected(read.http);
  if (read.http === 409 && refusal.code === "WORK_BASIS_CHANGED") {
    return { status: "basis_changed", http: 409, code: "WORK_BASIS_CHANGED", message: refusal.message };
  }
  return { status: "refused", http: read.http, code: refusal.code, message: refusal.message };
}

export async function readDomainDetail(path: string, siteCode: string, actionId: string): Promise<DomainDetailResult> {
  const read = await readJson(path);
  if (read === null) return unreachable();
  if (read.http === 200) {
    return isDetail(read.body, siteCode, actionId) ? { status: "loaded", value: read.body } : unexpected(200);
  }
  const refusal = refusalOf(read.http, read.body);
  if (refusal === null) return unexpected(read.http);
  if (read.http === 404 && refusal.code === "ACTION_NOT_FOUND") {
    return { status: "not_found", http: 404, code: refusal.code, message: refusal.message };
  }
  return { status: "refused", http: read.http, code: refusal.code, message: refusal.message };
}

export function createDomainActionClient(basePath: string = SITES_API_PATH): DomainActionClient {
  return {
    getIndex(siteCode, scope) {
      const invalid = invalidScope(scope);
      if (invalid !== null) return Promise.resolve(invalid);
      return readDomainIndex(domainIndexPath(basePath, siteCode, scope), siteCode);
    },
    getDetail(siteCode, actionId, knownAt) {
      if (knownAt !== null && !isUtcInstant(knownAt)) return Promise.resolve(invalidKnownAt());
      return readDomainDetail(domainDetailPath(basePath, siteCode, actionId, knownAt), siteCode, actionId);
    },
  };
}
