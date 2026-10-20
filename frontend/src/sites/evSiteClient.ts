/**
 * Read-only client for an EV_CHARGING Site's five W2-07 selected reads (`.agent/W2-07-build-spec.md` "Commits 2-3",
 * "Run 6 rulings (q5)" R5 and "Run 7 rulings (q6)"):
 *
 *   GET /api/sites/{code}/ev/overview               (from, to, known_at)
 *   GET /api/sites/{code}/ev/evidence               (from, to, known_at)
 *   GET /api/sites/{code}/ev/evidence/analysis      (from, to, known_at, cursor, limit)
 *   GET /api/sites/{code}/ev/financials             (from, to, known_at, cursor, limit)
 *   GET /api/sites/{code}/ev/financial-assumptions  (from, to, known_at)
 *
 * Every successful body carries W2-06's common envelope; refusals are `{error:{code,message}}`. Decimal values are
 * strings and are never parsed into numbers for display.
 */

import { coldWindowSearch } from "./coldAssessmentClient";
import type { EvDenominator, EvEnvelope, EvExcludedRecord, EvRead, EvStatus, EvWindowQuery } from "./evAssessmentClient";
import { isObject } from "./evidenceRead";
import { SITES_API_PATH } from "./siteDirectoryClient";

export interface EvSiteLinks {
  self: string | null;
  evidence: string | null;
  analysis: string | null;
  finding: string | null;
  financials: string | null;
}

export interface EvCoverage {
  known_seconds: number | null;
  expected_seconds: number | null;
  ratio: string | null;
  unit: "WINDOW_SECONDS" | "SESSION_SECONDS" | null;
}

export interface EvServiceOccurrence {
  from: string;
  to: string;
  connector_asset_ids?: string[];
}

export interface EvConsequence {
  revision_id: string | null;
  revision_no: number | null;
  state: string;
  reason: string | null;
  quantity_kwh: string | null;
  tariff_revision_id: string | null;
  tariff_value: string | null;
  currency: string | null;
  amount: string | null;
  overlap_group: string | null;
  recorded_at: string | null;
  tariff_recorded_at: string | null;
  source_gate: string | null;
  session_revision_ids: string[];
  evidence_ids: string[];
  limitation: string | null;
  label?: string;
}

export interface EvOverviewRead extends EvEnvelope {
  status: EvStatus;
  objective: {
    text: string;
    configured_service_window: EvServiceOccurrence | null;
    configured_service_windows: EvServiceOccurrence[];
    service_schedule_declared: boolean;
    site_import_limit_kw: string | null;
    as_of: string | null;
    limitation: string | null;
  };
  denominator: EvDenominator;
  energy: { supported_kwh: string | null; complete_kwh: string | null; partial_kwh: string | null; unknown_seconds: number | null; as_of: string | null; limitation: string | null };
  site_power: { observed_peak_kw: string | null; configured_limit_kw: string | null; coverage: EvCoverage; claim_limit: string; as_of: string | null; limitation: string | null };
  findings: {
    count: number;
    items: { finding_id: string; revision_id: string; session_id: string | null; title: string; claim_level: string; as_of: string | null; links: EvSiteLinks; start_evidence_id: string | null; fault_evidence_id: string | null; abort_evidence_id: string | null }[];
    as_of: string | null;
    limitation: string | null;
  };
  needs_attention: { code: string; text: string; link: string | null }[];
  consequence_summary: { state: string | null; reason: string | null; quantity_kwh: string | null; amount: string | null; currency: string | null; overlap_group: string | null; as_of: string | null; limitation: string | null };
  links: EvSiteLinks;
}

export interface EvCapability {
  claim: string;
  state: string;
  required_roles: string[];
  missing_roles: string[];
  coverage: EvCoverage;
  accepted_evidence_ids: string[];
  as_of: string | null;
  limitation: string | null;
}

export interface EvContactDetail {
  state: string;
  last_seen_at: string | null;
  age_seconds: number | null;
  diagnostic_id: string | null;
  diagnostic_received_at: string | null;
  cadence_seconds: number | null;
}

export interface EvSource {
  slot: "CONNECTOR_1" | "CONNECTOR_2" | "SITE_METER" | "BILLING" | string;
  asset_id: string | null;
  display_name: string;
  contact: EvContactDetail & { checked_at: string | null; by_source: (EvContactDetail & { source_id: string })[] };
  quality: { state: string; accepted_count: number };
  roles: string[];
  as_of: string | null;
  limitation: string | null;
}

export interface EvEvidenceRead extends EvEnvelope {
  capabilities: EvCapability[];
  sources: EvSource[];
  next_evidence: { code: string; text: string; why: string; link: string | null }[];
  links: EvSiteLinks;
}

export interface EvAnalysisItem {
  evidence_id: string;
  source_label: string;
  role: string | null;
  record_kind: string | null;
  value_display: string | null;
  unit: string | null;
  source_time: string | null;
  sent_at: string | null;
  received_at: string | null;
  quality: string | null;
  use: string | null;
  reason: string | null;
  session_id: string | null;
  interval_start: string | null;
  interval_end: string | null;
  note: string | null;
  record_target_state: string;
  links: EvSiteLinks;
}

export interface EvClaimRule {
  claim: string;
  required_roles: string[];
  observed_roles: string[];
  missing_roles: string[];
  coverage: EvCoverage;
  result: string;
  accepted_evidence_ids: string[];
  source_class: string | null;
  known_at: string | null;
  limitation: string | null;
}

export interface EvAnalysisRead extends EvEnvelope {
  items: EvAnalysisItem[];
  total_count: number;
  excluded_records: EvExcludedRecord[];
  claim_rules: EvClaimRule[];
  next_cursor: string | null;
  links: EvSiteLinks;
}

export interface EvFinancialsRead extends EvEnvelope {
  consequence: EvConsequence | null;
  history: EvConsequence[];
  not_included: string[];
  next_cursor: string | null;
  links: EvSiteLinks;
}

export interface EvTariff {
  revision_id: string;
  value: string;
  currency: string;
  unit: string;
  basis: string | null;
  valid_from: string | null;
  valid_to: string | null;
  recorded_at: string | null;
}

export interface EvAssumptionsRead extends EvEnvelope {
  tariff: EvTariff | null;
  tariff_revision_count: number;
  publication_note: string | null;
  consequence_tariff: { revision_id: string; value: string; currency: string; recorded_at: string | null } | null;
  billing_state: string;
  missing_keys: string[];
  links: EvSiteLinks;
}

export interface EvPage {
  cursor?: string | null;
  limit?: number;
}

export interface EvSiteClient {
  getOverview(siteId: string, window: EvWindowQuery): Promise<EvRead<EvOverviewRead>>;
  getEvidence(siteId: string, window: EvWindowQuery): Promise<EvRead<EvEvidenceRead>>;
  getAnalysis(siteId: string, window: EvWindowQuery, page?: EvPage): Promise<EvRead<EvAnalysisRead>>;
  getFinancials(siteId: string, window: EvWindowQuery, page?: EvPage): Promise<EvRead<EvFinancialsRead>>;
  getAssumptions(siteId: string, window: EvWindowQuery): Promise<EvRead<EvAssumptionsRead>>;
}

function isEnvelope(value: unknown): value is EvEnvelope {
  return isObject(value) && isObject(value.window) && isObject(value.currentness) && isObject(value.source_provenance) && Array.isArray(value.limitations);
}

const has = (v: unknown, keys: string[], arrays: string[] = []) =>
  isEnvelope(v) && keys.every((k) => k in (v as object)) && arrays.every((k) => Array.isArray((v as unknown as Record<string, unknown>)[k]));

const SHAPES = {
  overview: (v: unknown) => has(v, ["status", "objective", "denominator", "energy", "site_power", "findings", "consequence_summary", "links"], ["needs_attention"]),
  evidence: (v: unknown) => has(v, ["links"], ["capabilities", "sources", "next_evidence"]),
  analysis: (v: unknown) => has(v, ["total_count", "next_cursor", "links"], ["items", "excluded_records", "claim_rules"]),
  financials: (v: unknown) => has(v, ["consequence", "next_cursor", "links"], ["history", "not_included"]),
  assumptions: (v: unknown) => has(v, ["tariff", "billing_state", "links"], ["missing_keys"]),
};

async function read<T>(url: string, shape: (value: unknown) => boolean): Promise<EvRead<T>> {
  let response: Response;
  try {
    response = await fetch(url);
  } catch {
    return { status: "unavailable", message: null };
  }
  let body: unknown = null;
  try {
    body = await response.json();
  } catch {
    body = null;
  }
  if (response.ok) {
    return shape(body) ? { status: "loaded", value: body as T } : { status: "unavailable", message: "The EV Site read answered in an unexpected shape." };
  }
  const error = isObject(body) && isObject(body.error) ? body.error : null;
  if (error !== null && typeof error.code === "string") {
    return { status: "refused", httpStatus: response.status, code: error.code, message: typeof error.message === "string" ? error.message : null };
  }
  return { status: "unavailable", message: null };
}

function paged(window: EvWindowQuery, page?: EvPage): string {
  const search = coldWindowSearch(window);
  const params = new URLSearchParams(search.startsWith("?") ? search.slice(1) : search);
  if (page?.cursor) params.set("cursor", page.cursor);
  if (page?.limit !== undefined) params.set("limit", String(page.limit));
  const text = params.toString();
  return text === "" ? "" : `?${text}`;
}

export function createEvSiteClient(basePath: string = SITES_API_PATH): EvSiteClient {
  const base = (siteId: string) => `${basePath}/${encodeURIComponent(siteId)}/ev`;
  return {
    getOverview: (siteId, window) => read(`${base(siteId)}/overview${coldWindowSearch(window)}`, SHAPES.overview),
    getEvidence: (siteId, window) => read(`${base(siteId)}/evidence${coldWindowSearch(window)}`, SHAPES.evidence),
    getAnalysis: (siteId, window, page) => read(`${base(siteId)}/evidence/analysis${paged(window, page)}`, SHAPES.analysis),
    getFinancials: (siteId, window, page) => read(`${base(siteId)}/financials${paged(window, page)}`, SHAPES.financials),
    getAssumptions: (siteId, window) => read(`${base(siteId)}/financial-assumptions${coldWindowSearch(window)}`, SHAPES.assumptions),
  };
}
