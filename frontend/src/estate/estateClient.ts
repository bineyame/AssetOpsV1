/**
 * W3-01 commit 3: the typed client for the three estate reads (`.agent/W3-01-build-spec.md`, "Public API and
 * examples", Run 8 ruling 3 and Run 12 ruling 3). The Findings envelope is `estate-finding-index-2`; Actions and
 * scope stay `-1`. The cursor is opaque: the client passes it back unchanged (it carries `page_one_mode` and the
 * full-precision cutoff), and any lens, state or window change restarts at page one without it.
 */

export const ESTATE_API_PATH = "/api/estate";

export const FINDINGS_SCHEMA = "estate-finding-index-2";
export const ACTIONS_SCHEMA = "estate-action-index-1";
export const SCOPE_SCHEMA = "estate-scope-1";

export type EstateLens = "all" | "cost" | "risks" | "opportunities";
export type EstateStateFilter = "all" | "supported" | "unconfirmed" | "no_longer_supported" | "merged";
export type EstateSiteState =
  | "CURRENT"
  | "PENDING_RECOMPUTE"
  | "STALE_SOURCE"
  | "HISTORICAL"
  | "UNKNOWN"
  | "NOT_APPLICABLE";
export type EstateLifecycle = "SUPPORTED" | "UNCONFIRMED" | "NO_LONGER_SUPPORTED" | "MERGED";

/** The public provenance block (shared DTO, `D-2026-10-20-shared-provenance-dto`); read by `sourceProvenance.tsx`. */
export interface EstateSourceBlock {
  classification?: string;
  state: string;
  source_ids?: string[];
  evidence_ids?: string[];
  basis_sha256?: string | null;
  reasons?: { code: string; accepted_evidence_ids: string[] }[];
  [key: string]: unknown;
}

export interface EstateCoverageSite {
  site_id: string;
  state: EstateSiteState;
  committed_watermark: string | null;
  selection_id: string | null;
  match_state: string;
  job_state: string;
  source_freshness: string;
}

export interface EstateEnvelope {
  schema_version: string;
  scope: { tenant_id: string | null; authorized_site_count: number; covered_site_count: number; access_basis: string };
  window: { from: string; to: string; bounds: string; known_at: string };
  status: EstateSiteState;
  coverage: { state: "COMPLETE" | "PARTIAL" | "UNKNOWN"; sites: EstateCoverageSite[] };
  total_count: number | null;
  next_cursor: string | null;
  selection_token: string;
}

export interface EstateConsequence {
  state: "PRICED" | "UNPRICED" | "UNKNOWN";
  amount: string | null;
  amount_low: string | null;
  amount_high: string | null;
  currency: string | null;
  source_revision_id: string | null;
}

export interface EstateFindingRow {
  finding_id: string;
  finding_revision_id: string;
  site_id: string;
  site_code: string;
  site_name: string;
  finding_label: string;
  title: string;
  priority: string | null;
  confidence: string | null;
  confidence_reasons: unknown[];
  lifecycle: EstateLifecycle;
  lens_flags: ("COST" | "RISK" | "OPPORTUNITY")[];
  consequence: EstateConsequence;
  source_provenance: EstateSourceBlock;
  episode_start: string;
  /** The row's Site basis state (Run 12 ruling 1): page one's basis mode, never the page-two response label. */
  status: EstateSiteState;
  links: { finding: string; site: string };
}

export interface EstateFindingsBody extends EstateEnvelope {
  lens: EstateLens;
  state_filter: EstateStateFilter;
  summary: {
    high_priority: number | null;
    low_confidence: number | null;
    awaiting_verification: number | null;
    basis_count: number | null;
    supported_findings: number | null;
    as_of?: string;
  };
  order: string;
  rows: EstateFindingRow[];
}

export interface EstateActionRow {
  action_id: string;
  action_code: string;
  site_id: string;
  site_code: string;
  site_name: string;
  created_at: string;
  selected_event_id: string;
  source_finding_id: string;
  source_finding_revision_id: string;
  action_title: string;
  success_criterion: string | null;
  owner: string | null;
  due_at: string | null;
  application_state: "NONE_AT_CUTOFF" | "PENDING" | "APPLIED";
  resolution_state: "RESOLVED" | "RESOLUTION_WITHDRAWN" | null;
  verification_outcome: string | null;
  source_provenance: EstateSourceBlock;
  links: { action: string; source: string | null };
}

export interface EstateActionsBody extends EstateEnvelope {
  summary: {
    open_actions: number | null;
    due_overdue: number | null;
    verification_window: number | null;
    verified_in_30_days: number | null;
    basis_count: number | null;
    as_of?: string;
  };
  order: string;
  rows: EstateActionRow[];
}

export interface EstateScopeBody {
  schema_version: string;
  sites: { site_id: string; site_code: string; site_name: string; coverage_state: EstateSiteState }[];
  authorized_site_count: number;
  covered_site_count: number;
  access_basis: string;
  known_at: string;
}

/** The refusal table (spec "Refusal table and cursor"): one exact UI sentence per code. */
export const REFUSAL_COPY: Readonly<Record<string, string>> = {
  UNAUTHENTICATED: "Sign in to see estate records.",
  ESTATE_BASIS_CHANGED: "The list changed. Reload the first page.",
  ESTATE_SELECTION_INCONSISTENT: "Some records are being updated. Reload the list.",
  INVALID_WINDOW: "Choose a valid date range of at most 31 days.",
  INVALID_KNOWN_AT: "Choose a valid evidence cutoff.",
  INVALID_LENS: "Choose a supported Findings lens.",
  INVALID_LIMIT: "Choose a page size from 1 to 100.",
  INVALID_CURSOR: "Reload the first page.",
  ESTATE_STORE_UNAVAILABLE: "Estate records are unavailable right now. Try again.",
};

/** Codes whose UI copy asks the reader to start again at page one (the page offers that link). */
export const FIRST_PAGE_CODES: ReadonlySet<string> = new Set(["ESTATE_BASIS_CHANGED", "INVALID_CURSOR"]);

export type EstateResult<T> =
  | { status: "loaded"; value: T }
  | { status: "refused"; httpStatus: number; code: string; copy: string };

export interface EstateQuery {
  from: string;
  to: string;
  /** Omitted means the read's own DB time (live). */
  known_at: string | null;
  limit?: number | null;
  cursor: string | null;
}

export interface EstateFindingsQuery extends EstateQuery {
  lens: EstateLens;
  state: EstateStateFilter;
}

export interface EstateClient {
  findings(query: EstateFindingsQuery): Promise<EstateResult<EstateFindingsBody>>;
  actions(query: EstateQuery): Promise<EstateResult<EstateActionsBody>>;
  scope(query: Pick<EstateQuery, "from" | "to" | "known_at">): Promise<EstateResult<EstateScopeBody>>;
}

function unavailable<T>(): EstateResult<T> {
  return {
    status: "refused",
    httpStatus: 503,
    code: "ESTATE_STORE_UNAVAILABLE",
    copy: REFUSAL_COPY.ESTATE_STORE_UNAVAILABLE,
  };
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

/** Query string for an estate read; null/absent parameters are left out. */
export function estateQueryString(query: Partial<EstateFindingsQuery>): string {
  const params = new URLSearchParams();
  for (const key of ["from", "to", "known_at", "lens", "state", "limit", "cursor"] as const) {
    const value = query[key];
    if (value === null || value === undefined) continue;
    if ((key === "lens" || key === "state") && value === "all") continue;
    params.set(key, String(value));
  }
  const text = params.toString();
  return text === "" ? "" : `?${text}`;
}

async function readEstate<T>(path: string, schema: string): Promise<EstateResult<T>> {
  let response: Response;
  try {
    response = await fetch(path, { headers: { Accept: "application/json" } });
  } catch {
    return unavailable();
  }
  let body: unknown = null;
  try {
    body = await response.json();
  } catch {
    return unavailable();
  }
  if (response.ok) {
    if (isObject(body) && body.schema_version === schema) return { status: "loaded", value: body as T };
    return unavailable();
  }
  const detail = isObject(body) && isObject(body.detail) ? body.detail : null;
  const code = detail !== null && typeof detail.code === "string" ? detail.code : "";
  const copy = REFUSAL_COPY[code];
  if (copy === undefined) return unavailable();
  return { status: "refused", httpStatus: response.status, code, copy };
}

export function createEstateClient(basePath: string = ESTATE_API_PATH): EstateClient {
  return {
    findings: (query) => readEstate(`${basePath}/findings${estateQueryString(query)}`, FINDINGS_SCHEMA),
    actions: (query) =>
      readEstate(`${basePath}/actions${estateQueryString({ ...query, lens: undefined, state: undefined })}`, ACTIONS_SCHEMA),
    scope: (query) =>
      readEstate(
        `${basePath}/scope${estateQueryString({ from: query.from, to: query.to, known_at: query.known_at })}`,
        SCOPE_SCHEMA,
      ),
  };
}
