/**
 * W2-04: read-only client for a cold-chain Site's five selected Site reads (`.agent/W2-04-build-spec.md`
 * "Five API reads" with the Run-5 additions Q-R1..Q-R9):
 *
 *   GET /api/sites/{code}/cold/overview
 *   GET /api/sites/{code}/cold/evidence
 *   GET /api/sites/{code}/cold/evidence/analysis   (+ cursor)
 *   GET /api/sites/{code}/cold/financials
 *   GET /api/sites/{code}/cold/financial-assumptions
 *
 * Each takes the optional strict-UTC window `from`, `to` (both or neither) and `known_at`. A window with no
 * selected assessment is a valid 200 `UNKNOWN` read with null values and empty arrays; refusals are
 * `{error:{code,message}}` and are returned as `refused`, never as an empty read.
 */

import { SITES_API_PATH } from "./siteDirectoryClient";
import { isObject } from "./evidenceRead";
import { type ColdEnvelope, type ColdRead, type ColdWindowQuery, coldWindowSearch } from "./coldAssessmentClient";

export interface ColdCoverage {
  known_points: number | null;
  expected_points: number | null;
  ratio: string | null;
}

interface Dated {
  as_of: string | null;
  limitation: string | null;
}

export interface ColdAttentionItem extends Dated {
  code: string;
  text: string;
  link: string | null;
}

export interface ColdStripStep extends Dated {
  step: string;
  state: string;
  at: string | null;
  evidence_id: string | null;
}

export interface ColdOverviewRead extends ColdEnvelope {
  status: Dated & { state: string; claim_level: string | null };
  objective: Dated & {
    text: string;
    policy_low_deg_c: string | null;
    policy_high_deg_c: string | null;
    room_asset_id: string | null;
  };
  temperature_summary: Dated & {
    latest_deg_c: string | null;
    latest_at: string | null;
    coverage: ColdCoverage;
    episode_count: number;
    claim_level: string | null;
  };
  backup_summary: Dated & {
    attempts: number;
    observed_success: number;
    observed_failure: number;
    unknown: number;
    latest_chain_id: string | null;
  };
  causal_strip: ColdStripStep[];
  findings: Dated & {
    count: number;
    items: { finding_id: string; revision_id: string; title: string; claim_level: string; link: string | null }[];
  };
  needs_attention: ColdAttentionItem[];
  cooling: Dated & { state: string; text: string };
  maintenance: Dated & { state: string; text: string; record_id: string | null; link: string | null };
  consequence_summary: Dated & {
    state: string;
    quantity: { low: string | null; high: string | null; unit: string | null };
    amount: { low: null; high: null; currency: null };
    overlap_group: string | null;
  };
  links: Record<"temperature" | "backup" | "findings" | "evidence" | "analysis" | "financials", string | null>;
}

export interface ColdCapability extends Dated {
  claim: string;
  state: string;
  required_roles: string[];
  missing_roles: string[];
  coverage: ColdCoverage;
}

export interface ColdSource extends Dated {
  id: string;
  role: string;
  contact: string;
  contact_at: string | null;
  fact_age: number | null;
  accepted_count: number;
  last_accepted_at: string | null;
  quality: { good_count: number; other_count: number };
}

export interface ColdEvidenceRead extends ColdEnvelope {
  capabilities: ColdCapability[];
  sources: ColdSource[];
  links: Record<"analysis" | "foundation" | "temperature" | "backup", string | null>;
}

export interface ColdAcceptedRecord extends Dated {
  evidence_id: string;
  kind: string;
  source_time: string | null;
  received_at: string | null;
  quality: string | null;
  role: string | null;
  exclusion: string | null;
  source_id: string | null;
  envelope_sha256: string | null;
  assessment_revision_id: string | null;
  value_display: string | null;
  unit: string | null;
  sent_at: string | null;
  record_target_state: "PROVED" | "UNAVAILABLE" | string;
  link: string | null;
}

export interface ColdClaimRule extends Dated {
  rule_id: string;
  requirement: string;
  observed_roles: string[];
  missing_roles: string[];
  coverage: ColdCoverage;
  result: string | null;
}

export interface ColdAnalysisRead extends ColdEnvelope {
  accepted_records: { items: ColdAcceptedRecord[]; next_cursor: string | null };
  claim_rules: ColdClaimRule[];
  links: Record<"evidence" | "findings", string | null>;
}

export interface ColdExactBasis {
  finding_revision_id: string;
  episode_revision_id: string;
  assessment_revision_id: string;
  evidence_ids: string[];
  source_gate_sha256: string;
  assumption_revision_ids: string[];
  consequence_basis_sha256: string;
}

export interface ColdConsequence extends Dated {
  id: string;
  kind: string;
  state: string;
  quantity_bounds: { low: string | null; high: string | null };
  quantity_unit: string | null;
  amount_bounds: { low: null; high: null };
  currency: null;
  reason: string | null;
  overlap_group: string | null;
  exact_basis: ColdExactBasis;
}

export interface ColdFinancialsRead extends ColdEnvelope {
  consequences: ColdConsequence[];
  not_included: (Dated & { code: string; text: string })[];
  links: Record<"assumptions" | "findings" | "evidence", string | null>;
}

export interface ColdAssumptionsRead extends ColdEnvelope {
  items: (Dated & {
    key: string;
    revision_id: string;
    value: string | null;
    unit: string | null;
    currency: string | null;
    valid_from: string | null;
    valid_to: string | null;
    recorded_at: string | null;
    source: string | null;
  })[];
  missing_keys: string[];
  publication_state: string;
  currency_state: string;
  links: Record<"financials", string | null>;
}

export interface ColdSiteClient {
  getOverview(siteId: string, window: ColdWindowQuery): Promise<ColdRead<ColdOverviewRead>>;
  getEvidence(siteId: string, window: ColdWindowQuery): Promise<ColdRead<ColdEvidenceRead>>;
  getAnalysis(siteId: string, window: ColdWindowQuery, cursor: string | null): Promise<ColdRead<ColdAnalysisRead>>;
  getFinancials(siteId: string, window: ColdWindowQuery): Promise<ColdRead<ColdFinancialsRead>>;
  getAssumptions(siteId: string, window: ColdWindowQuery): Promise<ColdRead<ColdAssumptionsRead>>;
}

function isEnvelope(value: unknown): value is ColdEnvelope {
  return (
    isObject(value) &&
    isObject(value.window) &&
    isObject(value.currentness) &&
    isObject(value.source_provenance) &&
    Array.isArray(value.limitations)
  );
}

const arrays = (value: unknown, ...keys: string[]) =>
  isEnvelope(value) && keys.every((k) => Array.isArray((value as unknown as Record<string, unknown>)[k]));

const SHAPES = {
  overview: (v: unknown) =>
    arrays(v, "causal_strip", "needs_attention") && isObject((v as ColdOverviewRead).status) && isObject((v as ColdOverviewRead).consequence_summary),
  evidence: (v: unknown) => arrays(v, "capabilities", "sources"),
  analysis: (v: unknown) =>
    arrays(v, "claim_rules") && isObject((v as ColdAnalysisRead).accepted_records) && Array.isArray((v as ColdAnalysisRead).accepted_records.items),
  financials: (v: unknown) => arrays(v, "consequences", "not_included"),
  assumptions: (v: unknown) => arrays(v, "items", "missing_keys"),
};

async function read<T>(url: string, shape: (value: unknown) => boolean): Promise<ColdRead<T>> {
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
    return shape(body)
      ? { status: "loaded", value: body as T }
      : { status: "unavailable", message: "The cold Site read answered in an unexpected shape." };
  }
  const error = isObject(body) && isObject(body.error) ? body.error : null;
  if (error !== null && typeof error.code === "string") {
    return {
      status: "refused",
      httpStatus: response.status,
      code: error.code,
      message: typeof error.message === "string" ? error.message : null,
    };
  }
  return { status: "unavailable", message: null };
}

export function createColdSiteClient(basePath: string = SITES_API_PATH): ColdSiteClient {
  const base = (siteId: string) => `${basePath}/${encodeURIComponent(siteId)}/cold`;
  return {
    getOverview: (siteId, window) => read(`${base(siteId)}/overview${coldWindowSearch(window)}`, SHAPES.overview),
    getEvidence: (siteId, window) => read(`${base(siteId)}/evidence${coldWindowSearch(window)}`, SHAPES.evidence),
    getAnalysis: (siteId, window, cursor) => {
      const search = coldWindowSearch(window);
      const page = cursor === null ? "" : `${search === "" ? "?" : "&"}cursor=${encodeURIComponent(cursor)}`;
      return read(`${base(siteId)}/evidence/analysis${search}${page}`, SHAPES.analysis);
    },
    getFinancials: (siteId, window) => read(`${base(siteId)}/financials${coldWindowSearch(window)}`, SHAPES.financials),
    getAssumptions: (siteId, window) =>
      read(`${base(siteId)}/financial-assumptions${coldWindowSearch(window)}`, SHAPES.assumptions),
  };
}
