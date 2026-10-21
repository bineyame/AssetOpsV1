/**
 * W3-02 commit 2: the typed client for the estate Evidence root, `GET /api/estate/evidence`
 * (`estate-evidence-1`; `.agent/W3-02-build-spec.md` "Proof and builder handoff" literal wire vectors, closure 4
 * "Wire, token, links, registry and mock"). It is separate from the W3-01 `EstateClient`, which stays unchanged.
 * Commit 4 adds the Financials read to this file. The cursor is opaque and passed back unchanged.
 */
import { estateQueryString, type EstateCoverageSite, type EstateQuery, type EstateSourceBlock } from "./estateClient";

export const ESTATE_EVIDENCE_API_PATH = "/api/estate/evidence";
export const EVIDENCE_SCHEMA = "estate-evidence-1";

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

/**
 * The W3-02 refusal copy ("Refusals and UI states"), keyed by the code the estate wrapper sends. Codes that table
 * does not name use its generic `This selection cannot be read. Reset the filters.` (see pending ruling c2-q2).
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
  INVALID_WINDOW: "Choose a UTC window of up to 31 days with a start before its end.",
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

async function read<T>(path: string, schema: string): Promise<EvidenceResult<T>> {
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
  const copy = EVIDENCE_REFUSAL_COPY[code];
  if (copy === undefined) return unavailable();
  return { status: "refused", httpStatus: response.status, code, copy };
}

export function createEstateEvidenceMoneyClient(evidencePath: string = ESTATE_EVIDENCE_API_PATH): EstateEvidenceMoneyClient {
  return {
    evidence: (query) =>
      read(
        `${evidencePath}${estateQueryString({ from: query.from, to: query.to, known_at: query.known_at, limit: query.limit, cursor: query.cursor })}`,
        EVIDENCE_SCHEMA,
      ),
  };
}
