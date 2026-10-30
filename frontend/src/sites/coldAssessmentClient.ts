/**
 * Read-only client for a cold-chain Site's selected assessments (W2-03 commit 4 routes,
 * `.agent/W2-03-build-spec.md` "Commit 4 - selected reads"):
 *
 *   GET /api/sites/{code}/cold/temperature
 *   GET /api/sites/{code}/cold/backup-chain
 *   GET /api/sites/{code}/cold/findings
 *   GET /api/sites/{code}/cold/findings/{id}
 *
 * Each takes the optional strict-UTC window `from`, `to` (both or neither) and `known_at`; without a window the
 * server reads the latest selected cold window at the committed cutoff. A window with no selected assessment is
 * a valid 200 `UNKNOWN` read with null values and empty arrays; refusals are `{error:{code,message}}`.
 */

import { SITES_API_PATH } from "./siteDirectoryClient";
import { isObject } from "./evidenceRead";
import type { OutcomeCategories } from "./outcomeCategories";

export type ColdCurrentness = "CURRENT" | "PENDING_RECOMPUTE" | "STALE_SOURCE" | "HISTORICAL" | "UNKNOWN";

export interface ColdWindowQuery {
  from: string | null;
  to: string | null;
  known_at: string | null;
}

export interface ColdEnvelope {
  site_id: string;
  window: { from: string | null; to: string | null; known_at: string | null };
  currentness: {
    state: ColdCurrentness | string;
    watermark: { decided_at: string | null; assessment_revision_ids: string[] };
    latest_relevant_evidence_at: string | null;
    pending_since: string | null;
  };
  /** W3-01 (Run 3 q3): the pending-or-selected alias plus the two window siblings; each a public source DTO. */
  source_provenance: ColdSourceBlock;
  selected_source_provenance?: ColdSourceBlock | null;
  pending_source_provenance?: ColdSourceBlock | null;
  limitations: string[];
}

export interface ColdBounds {
  earliest: string | null;
  latest: string | null;
}
export interface ColdRange {
  low: string | null;
  high: string | null;
}

export interface ColdPoint {
  at: string;
  value: string | null;
  quality: string;
  evidence_id: string;
}

export interface ColdGap {
  start: string | null;
  end: string | null;
  reason: string | null;
  expected_points: number | null;
  received_points: number | null;
}

export interface ColdExcursionRead {
  episode_id: string | null;
  revision_id: string | null;
  direction: string;
  anchor_time?: string | null;
  open?: boolean;
  start_bounds: ColdBounds;
  end_bounds: ColdBounds;
  duration_bounds: ColdRange;
  degree_minute_bounds: ColdRange;
  peak_observed: string | null;
  claim_level: string;
  exposure_finding?: boolean;
  limitation: string | null;
}

export interface ColdExcludedRead {
  evidence_id: string;
  use?: string;
  reason: string | null;
  as_of: string | null;
}

export interface ColdTemperatureRead extends ColdEnvelope {
  state?: string | null;
  claim_level?: string | null;
  policy: {
    low_deg_c: string | null;
    high_deg_c: string | null;
    return_hysteresis_deg_c: string | null;
    min_excursion_min: string | number | null;
    probe_asset_id: string | null;
    room_asset_id: string | null;
  } | null;
  points: ColdPoint[];
  coverage: { known_points: number | null; expected_points: number | null; ratio: string | null };
  gaps: ColdGap[];
  excursions: ColdExcursionRead[];
  excluded: ColdExcludedRead[];
}

export interface ColdStepRead {
  kind: string;
  at: string | null;
  outcome: string | null;
  evidence_id: string | null;
  evidence_ids?: string[];
  state: string;
  limitation: string | null;
}

export interface ColdChainRead {
  correlation_id: string | null;
  episode_id: string | null;
  revision_id: string | null;
  result?: string | null;
  steps: ColdStepRead[];
  missing_steps: string[];
  claim_level: string;
  start_timeout_min: string | number | null;
  limitation: string | null;
}

export interface ColdBackupRead extends ColdEnvelope {
  state?: string | null;
  claim_level?: string | null;
  chains: ColdChainRead[];
  contradictions: { correlation_id: string | null; evidence_ids: string[]; reason: string; limitation: string | null }[];
  excluded?: ColdExcludedRead[];
}

export interface ColdFindingItem {
  finding_id: string;
  /** OUT-A: the outcome categories (policy `outcome-map/1`); absent on an older body. */
  categories?: OutcomeCategories;
  kind: "EXCURSION" | "START_RESPONSE" | string;
  subject_asset_id: string | null;
  revision_id: string;
  lifecycle: string;
  claim_level: string;
  title: string;
  state?: string | null;
  claim: Record<string, unknown>;
  episode_bounds: { start: ColdBounds; end: ColdBounds };
  limitations: string[];
  assessment_revision_id: string;
  evidence_ids: string[];
  split_from_finding_id?: string | null;
  as_of: string | null;
  limitation: string | null;
}

export interface ColdFindingsRead extends ColdEnvelope {
  items: ColdFindingItem[];
  next_cursor: string | null;
}

export interface ColdFindingRevision {
  revision_id: string;
  revision_no: number;
  transition: string;
  lifecycle: string;
  claim_level: string;
  basis_sha256: string;
  created_at: string | null;
  evidence_ids: string[];
}

export interface ColdFindingDetailRead extends ColdEnvelope, ColdFindingItem {
  basis_sha256: string;
  episode_id: string | null;
  episode_revision_id: string | null;
  revisions: ColdFindingRevision[];
}

export type ColdRead<T> =
  | { status: "loaded"; value: T }
  /** The server answered with a refusal envelope (401, 403, 404, 409, 422, 503). */
  | { status: "refused"; httpStatus: number; code: string; message: string | null }
  /** No answer, or an answer that is not the documented shape. */
  | { status: "unavailable"; message: string | null };

export interface ColdAssessmentClient {
  getTemperature(siteId: string, window: ColdWindowQuery): Promise<ColdRead<ColdTemperatureRead>>;
  getBackupChain(siteId: string, window: ColdWindowQuery): Promise<ColdRead<ColdBackupRead>>;
  listFindings(siteId: string, window: ColdWindowQuery): Promise<ColdRead<ColdFindingsRead>>;
  getFinding(siteId: string, findingId: string, window: ColdWindowQuery): Promise<ColdRead<ColdFindingDetailRead>>;
}

export const NO_WINDOW: ColdWindowQuery = { from: null, to: null, known_at: null };

/** The window part of an address (`?from=&to=&known_at=`), only the parameters that are set. */
export function coldWindowSearch(window: ColdWindowQuery): string {
  const params = new URLSearchParams();
  if (window.from !== null) params.set("from", window.from);
  if (window.to !== null) params.set("to", window.to);
  if (window.known_at !== null) params.set("known_at", window.known_at);
  const text = params.toString();
  return text === "" ? "" : `?${text}`;
}

export function coldWindowFromParams(params: URLSearchParams): ColdWindowQuery {
  return { from: params.get("from"), to: params.get("to"), known_at: params.get("known_at") };
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

const SHAPES = {
  temperature: (v: unknown) =>
    isEnvelope(v) && Array.isArray((v as ColdTemperatureRead).points) && Array.isArray((v as ColdTemperatureRead).excursions) && isObject((v as ColdTemperatureRead).coverage),
  backup: (v: unknown) => isEnvelope(v) && Array.isArray((v as ColdBackupRead).chains),
  findings: (v: unknown) => isEnvelope(v) && Array.isArray((v as ColdFindingsRead).items),
  finding: (v: unknown) =>
    isEnvelope(v) && typeof (v as ColdFindingDetailRead).finding_id === "string" && Array.isArray((v as ColdFindingDetailRead).revisions),
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
      : { status: "unavailable", message: "The cold assessment read answered in an unexpected shape." };
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

export function createColdAssessmentClient(basePath: string = SITES_API_PATH): ColdAssessmentClient {
  const base = (siteId: string) => `${basePath}/${encodeURIComponent(siteId)}/cold`;
  return {
    getTemperature: (siteId, window) => read(`${base(siteId)}/temperature${coldWindowSearch(window)}`, SHAPES.temperature),
    getBackupChain: (siteId, window) => read(`${base(siteId)}/backup-chain${coldWindowSearch(window)}`, SHAPES.backup),
    listFindings: (siteId, window) => read(`${base(siteId)}/findings${coldWindowSearch(window)}`, SHAPES.findings),
    getFinding: (siteId, findingId, window) =>
      read(`${base(siteId)}/findings/${encodeURIComponent(findingId)}${coldWindowSearch(window)}`, SHAPES.finding),
  };
}

/** W3-01: the public source DTO (six keys plus optional `detail`). */
export type ColdSourceBlock = { classification: string | null; state?: string; source_ids: string[]; evidence_ids: string[]; basis_sha256: string | null; reasons?: { code: string; accepted_evidence_ids: string[] }[]; detail?: Record<string, unknown> };
