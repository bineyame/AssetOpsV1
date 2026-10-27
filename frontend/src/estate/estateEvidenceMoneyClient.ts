/**
 * W3-02 commit 2: the typed client for the estate Evidence root, `GET /api/estate/evidence`
 * (`estate-evidence-1`; `.agent/W3-02-build-spec.md` "Proof and builder handoff" literal wire vectors, closure 4
 * "Wire, token, links, registry and mock"). It is separate from the W3-01 `EstateClient`, which stays unchanged.
 * Commit 4 adds the Financials read (`GET /api/estate/financials`, `estate-financials-1`) as its own
 * `EstateFinancialsClient`. The cursor is opaque and passed back unchanged.
 */
import { estateQueryString, invalidWindowCopy, type EstateCoverageSite, type EstateQuery, type EstateSourceBlock } from "./estateClient";

export const ESTATE_EVIDENCE_API_PATH = "/api/estate/evidence";
export const EVIDENCE_SCHEMA = "estate-evidence-1";
export const ESTATE_FINANCIALS_API_PATH = "/api/estate/financials";
export const FINANCIALS_SCHEMA = "estate-financials-1";

/** Closure 4: the two new roots add `EMPTY_SCOPE` to the status union and `EMPTY` to coverage state. */
export type EstateRootStatus = "CURRENT" | "PENDING_RECOMPUTE" | "STALE_SOURCE" | "HISTORICAL" | "UNKNOWN" | "EMPTY_SCOPE";
export type EvidenceDomain = "mini_grid" | "cold_chain" | "ev_charging";
export type EvidenceReadiness = "FULL" | "LIMITED" | "NONE" | "UNKNOWN" | "CONTRADICTORY" | "NOT_APPLICABLE";

export interface EvidenceEnvelope {
  schema_version: string;
  scope: { tenant_id: string | null; authorized_site_count: number; covered_site_count: number; access_basis: string };
  window: { from: string; to: string; bounds: string; known_at: string };
  status: EstateRootStatus;
  coverage: { state: "COMPLETE" | "PARTIAL" | "UNKNOWN" | "EMPTY"; sites: EstateCoverageSite[] };
  order: string;
  total_count: number | null;
  next_cursor: string | null;
  selection_token: string;
}

export interface EvidenceHistorical {
  label: string;
  statements: string[];
  gaps?: unknown[];
}

export interface EvidenceRow {
  site_id: string;
  site_code: string;
  site_name: string;
  domain: EvidenceDomain;
  domain_label: string;
  capability_key: string;
  capability_label: string;
  window_start: string | null;
  window_end: string | null;
  /** Raw selected state (`UNASSESSED`, `PENDING_RECOMPUTE`, `STALE_SOURCE`, `HISTORICAL`, ...); disclosure only. */
  raw_state: string;
  readiness: EvidenceReadiness;
  current_ceiling: string | null;
  ceiling: unknown;
  ceiling_source: string;
  next_evidence: string | null;
  gap_codes: string[];
  selected_revision_ids: string[];
  source_provenance: EstateSourceBlock;
  links: { site: string; site_readiness: string; site_readiness_label: string | null };
  disclosure: {
    capability_key: string;
    constituents: Record<string, unknown>[];
    reasons: Record<string, unknown>[];
    historical: EvidenceHistorical | null;
    prior_selection?: Record<string, unknown>;
    [key: string]: unknown;
  };
}

export interface EvidenceGap {
  domain: EvidenceDomain;
  gap_code: string;
  missing_role: string | null;
  label: string;
  site_ids: string[];
  site_codes: string[];
  /** c2-q1: the authorized stored Site names, parallel to `site_ids`/`site_codes`, for the full group. */
  site_names: (string | null)[];
  unlocks: string[];
  next_step: string | null;
  link: string | null;
}

export interface EstateEvidenceBody extends EvidenceEnvelope {
  summary: {
    limited_site_count: number | null;
    priority_gap_count: number | null;
    unsupported_claim_count: number | null;
    capability_count: number | null;
    full_count: number | null;
    limited_count: number | null;
    none_count: number | null;
    unknown_count: number | null;
    as_of?: string;
  };
  rows: EvidenceRow[];
  gaps: EvidenceGap[];
}

/** Closure 1 "Money row and comparison contract": the four register categories (cold `RECORDED_REPAIR` stays its own). */
export type FinancialCategory =
  | "CANDIDATE_OPERATING_COST_EXPOSURE"
  | "POTENTIAL_PRODUCT_EXPOSURE"
  | "GROSS_TARIFF_SCENARIO"
  | "RECORDED_REPAIR";
export type FinancialEligibility = "ELIGIBLE" | "UNPRICED" | "UNKNOWN" | "PENDING" | "HISTORICAL" | "WITHHELD" | "CONFLICT";
export type FinancialGroupState =
  | "COMPARABLE"
  | "SINGLE_LINE"
  | "INELIGIBLE"
  | "OVERLAPPING_BASIS"
  | "UNKNOWN_COVERAGE"
  | "NO_LINES";
export type FinancialDiagnosticCode = "MIXED_CURRENCY" | "DIFFERENT_PERIOD" | "DIFFERENT_WINDOW" | "DIFFERENT_ASSUMPTION";

/** Stored Decimal values arrive as exact strings; a bound may be absent. */
export type WireDecimal = string | number | null;

export interface FinancialAmount {
  low: WireDecimal;
  high: WireDecimal;
  currency: string | null;
}

export interface FinancialRow {
  line_key: string;
  domain: EvidenceDomain;
  site_id: string;
  site_code: string;
  site_name: string;
  category: FinancialCategory;
  /** CC-R1 (owner Q9): who the line benefits; one constant per category, server-provided. */
  beneficiary?: string;
  finding_id: string | null;
  finding_revision_id: string | null;
  consequence_revision_id: string;
  window_start: string | null;
  window_end: string | null;
  quantity: { low: WireDecimal; high: WireDecimal; unit: string | null };
  /** Present only on an `ELIGIBLE` line; any other line's pinned value stays in `disclosure.pinned_amount`. */
  amount: FinancialAmount | null;
  period_kind: string;
  assumption_revision_ids: string[];
  assumption_fingerprint: string | null;
  basis_evidence_ids: string[];
  technical_interval_ids: string[];
  overlap_group: string | null;
  eligibility: FinancialEligibility;
  reason_codes: string[];
  limit: string | null;
  source_provenance: EstateSourceBlock;
  /** Server-owned links (closure 4, closure 5 B5); `current_view_label` is set when a link opens the current Site view. */
  links: { site: string; bridge: string | null; evidence: string | null; current_view_label: string | null };
  disclosure: { pinned_amount?: FinancialAmount | null; [key: string]: unknown };
  group_key: string | null;
}

export interface FinancialGroup {
  group_key: string | null;
  category: FinancialCategory;
  currency: string | null;
  window_start: string | null;
  window_end: string | null;
  period_kind: string | null;
  assumption_fingerprint: string | null;
  state: FinancialGroupState;
  line_keys: string[];
  /** Numeric only for `COMPARABLE`. */
  amount: FinancialAmount | null;
  reason_codes: string[];
}

export interface FinancialExclusion {
  line_key: string;
  group_key: string | null;
  reason_codes: string[];
}

export interface FinancialDiagnostic {
  category: FinancialCategory;
  code: FinancialDiagnosticCode;
  line_keys: string[];
}

export interface EstateFinancialsBody extends EvidenceEnvelope {
  summary: {
    eligible_line_count: number | null;
    unpriced_line_count: number | null;
    withheld_line_count: number | null;
    /** Always null: no estate total is promised. */
    estate_total: null;
    estate_total_state: "NO_ESTATE_TOTAL";
    as_of?: string;
  };
  rows: FinancialRow[];
  groups: FinancialGroup[];
  exclusions: FinancialExclusion[];
  diagnostics: FinancialDiagnostic[];
}

/**
 * c2-q2: the exhaustive Evidence refusal copy, keyed by every code the shared parser, scope/read fence and Evidence
 * endpoint can send (plus the older wrapper aliases). Any other code fails closed to the 503 sentence.
 */
export const EVIDENCE_REFUSAL_COPY: Readonly<Record<string, string>> = {
  UNAUTHENTICATED: "Sign in to view estate evidence and financials.",
  ESTATE_SCOPE_FORBIDDEN: "You do not have access to this estate view.",
  ESTATE_SOURCE_DISCLOSURE_FORBIDDEN: "Source details for one or more Sites cannot be shown.",
  ESTATE_SITE_NOT_FOUND: "This Site is no longer in the selected estate.",
  ESTATE_READ_UNAVAILABLE: "Estate data is temporarily unavailable. Try again.",
  ESTATE_STORE_UNAVAILABLE: "Estate data is temporarily unavailable. Try again.",
  ESTATE_BASIS_CHANGED: "The selection changed. Refresh to see the latest basis.",
  ESTATE_SELECTION_INCONSISTENT: "The selection changed. Refresh to see the latest basis.",
  INVALID_WINDOW: "The selected window is invalid.",
  INVALID_KNOWN_AT: "This selection cannot be read. Reset the filters.",
  INVALID_LIMIT: "This selection cannot be read. Reset the filters.",
  INVALID_CURSOR: "This selection cannot be read. Reset the filters.",
  ESTATE_PARAMETER_UNKNOWN: "This selection cannot be read. Reset the filters.",
  ESTATE_CURSOR_INVALID: "This selection cannot be read. Reset the filters.",
};

export type EvidenceResult<T> =
  | { status: "loaded"; value: T }
  | { status: "refused"; httpStatus: number; code: string; copy: string };

export interface EstateEvidenceMoneyClient {
  evidence(query: EstateQuery): Promise<EvidenceResult<EstateEvidenceBody>>;
}

function unavailable<T>(): EvidenceResult<T> {
  return {
    status: "refused",
    httpStatus: 503,
    code: "ESTATE_STORE_UNAVAILABLE",
    copy: EVIDENCE_REFUSAL_COPY.ESTATE_STORE_UNAVAILABLE,
  };
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

async function read<T>(path: string, schema: string, window: EstateQuery): Promise<EvidenceResult<T>> {
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
  // Post-W6 W3-estate Q14: the shared window classifier, from the page query.
  const copy = code === "INVALID_WINDOW" ? invalidWindowCopy(window) : EVIDENCE_REFUSAL_COPY[code];
  if (copy === undefined) return unavailable();
  return { status: "refused", httpStatus: response.status, code, copy };
}

/** W3-02 commit 4: the Financials read, a separate interface so the commit-2 Evidence client stays unchanged. */
export interface EstateFinancialsClient {
  financials(query: EstateQuery): Promise<EvidenceResult<EstateFinancialsBody>>;
}

export function createEstateFinancialsClient(financialsPath: string = ESTATE_FINANCIALS_API_PATH): EstateFinancialsClient {
  return {
    financials: (query) =>
      read(
        `${financialsPath}${estateQueryString({ from: query.from, to: query.to, known_at: query.known_at, limit: query.limit, cursor: query.cursor })}`,
        FINANCIALS_SCHEMA,
        query,
      ),
  };
}

export function createEstateEvidenceMoneyClient(evidencePath: string = ESTATE_EVIDENCE_API_PATH): EstateEvidenceMoneyClient {
  return {
    evidence: (query) =>
      read(
        `${evidencePath}${estateQueryString({ from: query.from, to: query.to, known_at: query.known_at, limit: query.limit, cursor: query.cursor })}`,
        EVIDENCE_SCHEMA,
        query,
      ),
  };
}
