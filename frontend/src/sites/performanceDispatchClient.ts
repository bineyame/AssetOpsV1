/**
 * S3-01 phase 3b: the imported-Site Performance > Dispatch reads over the
 * durable dispatch assessment (`backend/assetops_backend/performance_api.py`).
 *
 * The cutover read is always served and says whether the stored assessment may
 * be shown, with the newest file-backed comparison summary. Window, run and
 * revision reads answer 409 PERFORMANCE_CUTOVER_CLOSED until it opens and 503
 * when a store is unreadable; each failure is a named state, never a thrown
 * error and never an empty result.
 */
import { SITES_API_PATH } from "./siteDirectoryClient";
import { hasKeys, isObject, read, type EvidenceRead } from "./evidenceRead";

export type ProjectionStatus = "UNASSESSED" | "PENDING" | "CURRENT" | "STALE_PROJECTION" | "FAILED";

export interface ComparisonClaim {
  class: "MATCH" | "INTENTIONAL_DELTA" | "MISSING_SOURCE" | "UNPROVEN" | string;
  legacy_assessment_id?: string;
  legacy_claim?: string;
  legacy_span?: [string, string] | null;
  postgres_claim?: string;
  postgres_revision_id?: string;
  missing_message_ids?: string[];
  rule?: string;
  rule_change?: { from: string; to: string; table_rows: string; explanation: string };
  interval_limitations?: string[];
  compared_evidence_ids?: string[];
  reason?: string;
}

export interface ComparisonSummary {
  report_id: string;
  compared_at: string;
  model_version: string | null;
  outcome: "PASSED" | "FAILED" | "EXCEPTIONS" | string;
  empty_set: boolean;
  statement: string;
  counts: Record<string, number>;
  lineage_breaks: Record<string, number>;
  selected_postgres_intervals?: number;
  claims: ComparisonClaim[];
}

export interface CutoverState {
  site_code: string;
  read: "POSTGRES_DISPATCH_3_1" | "CLOSED" | string;
  permitted: boolean;
  reason: string;
  comparison: ComparisonSummary | null;
  /** Set when the gate could not be checked (HTTP 503). */
  unavailable?: { code: string; message: string } | null;
}

export interface DispatchSegment {
  start: string;
  end: string;
  minutes: string;
  classification: string;
  reasons?: string[];
  missing?: string[];
  load_kw?: string | null;
  margin_kw?: string | null;
  observed?: boolean;
  binding_constraint?: string | null;
  evidence_ids?: string[];
}

export interface IntervalResult {
  interval: {
    first_on: string | null;
    last_on: string | null;
    off_before?: string | null;
    off_after?: string | null;
    lower_minutes?: string | null;
    upper_minutes?: string | null;
  };
  segments: DispatchSegment[];
  claim_level?: string;
  confidence?: { level: string; basis: string[] };
  limitations?: string[];
  alternatives?: Record<string, string>;
  portions_minutes?: Record<string, string>;
  candidate_bound?: string;
  binding_constraints?: string[];
  foundation_revision_ids?: string[];
}

export interface AssessmentRevision {
  id: string;
  model_version: string;
  assessment_key: string;
  revision_no: number;
  analytic_run_id: string;
  window_start: string;
  window_end: string;
  claim_level: string;
  result: IntervalResult;
  evidence_ids: string[];
  basis_sha256: string;
  created_at: string;
  scope?: string | null;
}

export interface RoleCoverage {
  status: string;
  readings: number;
  not_good: number;
  assets?: string[];
  role_sets?: string[];
}

export interface DemoAnnotation {
  [key: string]: unknown;
}

export interface WindowSelection {
  run_id: string;
  selected_at: string;
  selected_by_job: string | null;
  knowledge_cutoff: string;
  knowledge_cutoff_label: string;
  model_version: string;
  input_sha256: string;
  configuration_sha256: string;
  cohort_status: string;
  cohort_sha256: string;
  cohort: { status: string; reason: string | null; members: { source_id: string; gateway_id: string; sequence_epoch: string }[] };
  foundation_revision_ids: string[];
  binding_set_revision_ids: string[];
  built_at: string;
}

export interface RecomputeJob {
  id: string;
  status: string;
  window_start: string;
  window_end: string;
  attempts: number;
  last_error: string | null;
}

export interface DispatchWindow {
  site_code: string;
  model_version: string;
  window: { start: string; end: string; calendar: string };
  status: ProjectionStatus;
  status_reasons: string[];
  stale: boolean;
  current_basis: { read_at: string; accepted_reading_count: number } & Record<string, unknown>;
  selection: WindowSelection | null;
  coverage: Record<string, RoleCoverage> | null;
  watermarks: Record<string, string | null> | null;
  window_assessment: AssessmentRevision | null;
  limitations: string[];
  intervals: AssessmentRevision[];
  superseded_keys: string[];
  jobs: RecomputeJob[];
  unavailable: Record<string, string>;
  evidence_count: number;
  demo_annotations: DemoAnnotation[];
}

export interface AcceptedEvidenceItem {
  evidence_id: string;
  envelope_sha256: string;
  message_id: string;
  batch_id: string;
  external_batch_id: string | null;
  gateway_id: string;
  source_id: string;
  sequence_epoch: string;
  sequence: number;
  device_id: string;
  signal_id: string;
  role: string;
  asset_id: string;
  source_time: string | null;
  interval_start: string | null;
  interval_end: string | null;
  published_at: string | null;
  received_at: string;
  accepted_at: string;
  quality: string;
  value: string | null;
  unit: string | null;
  as_accepted?: Record<string, unknown>;
  selection_note?: string | null;
}

export interface RevisionDetail extends AssessmentRevision {
  evidence: AcceptedEvidenceItem[];
  history: AssessmentRevision[];
  selected_by_runs: string[];
  selected_configuration: { foundation_revision_ids: string[]; binding_set_revision_ids: string[] };
  knowledge_cutoff_label: string;
  /** Null for the current model; names an older rule result otherwise. */
  model_note: string | null;
  demo_annotations: DemoAnnotation[];
  run: Record<string, unknown> | null;
}

export interface PerformanceDispatchClient {
  getCutover(siteId: string): Promise<EvidenceRead<CutoverState>>;
  getWindow(siteId: string, day: string): Promise<EvidenceRead<DispatchWindow>>;
  getRevision(siteId: string, revisionId: string): Promise<EvidenceRead<RevisionDetail>>;
}

function isCutover(value: unknown): value is CutoverState {
  return hasKeys(value, ["site_code", "read", "permitted", "reason"]);
}

function isWindow(value: unknown): value is DispatchWindow {
  return (
    hasKeys(value, ["status", "status_reasons", "window", "intervals", "limitations", "jobs"]) &&
    Array.isArray((value as { intervals: unknown }).intervals)
  );
}

function isRevision(value: unknown): value is RevisionDetail {
  return (
    hasKeys(value, ["id", "claim_level", "result", "evidence", "history", "model_note"]) &&
    Array.isArray((value as { evidence: unknown }).evidence)
  );
}

/** The cutover read: its 503 carries a closed body, which is shown, not discarded. */
async function readCutover(path: string): Promise<EvidenceRead<CutoverState>> {
  let response: Response;
  try {
    response = await fetch(path);
  } catch {
    return { status: "unavailable", message: null };
  }
  let body: unknown = null;
  try {
    body = await response.json();
  } catch {
    body = null;
  }
  if (response.status === 404) {
    return { status: "not_found" };
  }
  if ((response.ok || response.status === 503) && isCutover(body)) {
    return { status: "loaded", value: { ...body, comparison: body.comparison ?? null } };
  }
  const detail = isObject(body) ? body.detail : null;
  return {
    status: "unavailable",
    message: isObject(detail) && typeof detail.message === "string" ? detail.message : null,
  };
}

export function createPerformanceDispatchClient(basePath: string = SITES_API_PATH): PerformanceDispatchClient {
  const base = (siteId: string) => `${basePath}/${encodeURIComponent(siteId)}/performance/dispatch`;
  return {
    getCutover(siteId) {
      return readCutover(`${base(siteId)}/cutover`);
    },
    getWindow(siteId, day) {
      return read(`${base(siteId)}/windows/${encodeURIComponent(day)}`, isWindow);
    },
    getRevision(siteId, revisionId) {
      return read(`${base(siteId)}/revisions/${encodeURIComponent(revisionId)}`, isRevision);
    },
  };
}
