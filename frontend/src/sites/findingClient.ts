/**
 * S4-01 phase 3: the Site-scoped durable Finding reads
 * (`backend/assetops_backend/finding_api.py`).
 *
 * `GET /api/sites/{site}/findings/{id}[?revision_id=]` and
 * `GET /api/sites/{site}/finding-windows/{day}`. Every refusal is a named
 * state, never a thrown error and never an empty result: 401 sign-in
 * required, 403 no access to the Site, 404 no such Site/Finding/revision,
 * 409 `PERFORMANCE_CUTOVER_CLOSED` (the Site's assessments are not released;
 * an exact revision still reads as audit material), 503 store unavailable.
 */
import { SITES_API_PATH } from "./siteDirectoryClient";
import { hasKeys, isObject } from "./evidenceRead";

export type FindingReadResult<T> =
  | { status: "loaded"; value: T }
  | { status: "not_found"; message: string | null }
  | { status: "unauthenticated"; message: string | null }
  | { status: "forbidden"; message: string | null }
  | { status: "closed"; message: string | null; note: string | null }
  | { status: "unavailable"; message: string | null };

export type Lifecycle = "SUPPORTED" | "UNCONFIRMED" | "NO_LONGER_SUPPORTED" | "MERGED";

export interface RevisionSummary {
  id: string;
  revision_no: number;
  recorded_at: string;
  transition: string;
  lifecycle: Lifecycle;
  claim_level: string;
  support_changed: boolean;
  model_version: string;
  matcher_version: string;
  episode: { start: string; end: string };
  candidate_minutes: string;
  primary_assessment_revision_id: string;
  window_assessment_revision_ids: string[];
  interval_assessment_revision_ids: string[];
  prior_window_assessment_revision_ids: string[] | null;
  prior_interval_assessment_revision_ids: string[] | null;
  foundation_revision_ids: string[];
  binding_set_revision_ids: string[];
  cited_evidence_count: number;
}

export interface FindingSpan {
  start: string;
  end: string;
  minutes: string;
  assessment_revision_id: string;
  evidence_ids?: string[];
}

export interface FindingPortion {
  start: string;
  end: string;
  classification: string;
  observed: boolean;
  assessment_revision_id: string;
}

export interface ContinuityStop {
  start: string;
  end: string;
  off_after: string;
  off_before: string;
  proof?: { status?: string; reason?: string; evidence_ids?: string[] } | null;
}

export interface ContinuityGap {
  start: string;
  end: string;
  minutes: string;
  bridged_by: string[];
  stops?: ContinuityStop[];
  candidate_minutes_added?: string;
}

export interface RecurrenceRecord {
  status: string;
  reason?: string | null;
  prior_finding_id?: string | null;
  separation_minutes?: string | number | null;
  off_after_prior?: { at: string; assessment_revision_id: string; evidence_ids?: string[] } | null;
  off_before_new?: { at: string; assessment_revision_id: string; evidence_ids?: string[] } | null;
}

export interface FindingClaim {
  statement?: string;
  candidate_spans?: FindingSpan[];
  other_portions?: FindingPortion[];
  continuity?: ContinuityGap[];
  window_claims?: string[];
  [key: string]: unknown;
}

export interface CitedAssessment {
  assessment_revision_id: string;
  scope: "INTERVAL" | "WINDOW";
  window_start: string;
  is_primary?: boolean;
  [key: string]: unknown;
}

export interface FindingRunRecord {
  run_id?: string;
  id?: string;
  model_version?: string;
  cohort_sha256?: string;
  window_start?: string;
  completed_at?: string | null;
  input_evidence_count?: number;
  [key: string]: unknown;
}

export interface CitedEvidence {
  evidence_id: string;
  role?: string;
  source_time?: string | null;
  interval_start?: string | null;
  interval_end?: string | null;
  value?: string | null;
  unit?: string | null;
  quality?: string;
  batch_id?: string;
  gateway_id?: string;
  source_id?: string;
  sequence_epoch?: string;
  envelope_sha256?: string;
  message_id?: string;
  status?: string;
  [key: string]: unknown;
}

export interface CurrentnessWindow {
  day: string;
  cited_window_assessment_revision_id: string;
  status: string;
  status_reasons: string[];
  currently_selected_window_assessment_revision_id: string | null;
  cited_is_current_selection: boolean;
}

export interface Currentness {
  state: string;
  windows: CurrentnessWindow[];
  basis?: string;
  latest_revision_id?: string;
  note?: string;
}

export interface MergeRecord {
  superseded_finding_id: string;
  canonical_finding_id: string;
  finding_revision_id: string;
  created_at: string;
}

export interface RevisionGroup {
  kind: "BASIS_REFRESHED" | "REVISION";
  label: string;
  count: number;
  revision_ids: string[];
  first_revision_no: number;
  last_revision_no: number;
  support_changed: boolean;
}

export interface FindingDetailBody {
  site_code: string;
  access_basis: string;
  source_gate: { permitted: boolean; reason: string };
  audit_only: { non_current: boolean; reason: string; statement: string } | null;
  finding: {
    id: string;
    finding_key: string;
    domain: string;
    mechanism: string;
    analytic_id: string;
    generator_asset_id: string;
    anchor_start: string;
    anchor_assessment_revision_id: string;
    cohort_sha256: string;
    matcher_version: string;
    opened_at: string;
    recurs_after_finding_id: string | null;
    split_from_finding_id: string | null;
  };
  selection: {
    revision_id: string;
    revision_no: number;
    selected_by: "LATEST_RECORDED" | "EXACT_REVISION_ID";
    latest_revision_id: string;
    is_latest: boolean;
    replay: string;
  };
  revision: RevisionSummary & {
    title: string;
    analytic_run_id: string;
    window_assessment_revision_id: string;
    minutes: { candidate: string; necessary: string; indeterminate: string };
    claim: FindingClaim;
    limitations: string[];
    cited_evidence_sha256: string;
    input_evidence_sha256: string;
    assessments: CitedAssessment[];
    runs: FindingRunRecord[];
    cited_evidence: CitedEvidence[];
    off_reports: { assessment_revision_id: string; at: string; evidence_ids: string[] }[];
    previous_revision_id: string | null;
    currentness: Currentness;
  };
  state: {
    lifecycle: Lifecycle;
    latest_transition: string;
    projection: string;
    claim_is_current: boolean;
    latest_revision_id: string;
    merged_into_finding_id: string | null;
    note: string;
  };
  relations: {
    canonical_finding_id: string;
    merged_into: MergeRecord[];
    merged_from: MergeRecord[];
    split_from_finding_id: string | null;
    split_parts: string[];
    recurs_after_finding_id: string | null;
    recurred_by: string[];
    recurrence: RecurrenceRecord;
  };
  revisions: RevisionSummary[];
  revision_page: { total: number; next_after_revision_no: number | null };
  revision_groups: RevisionGroup[];
  provenance: {
    statement: string;
    cited_evidence_by_source: {
      gateway_id: string;
      source_id: string;
      sequence_epoch: string;
      source_mode: string;
      count: number;
    }[];
    case_annotations: { label?: string; note?: string; [key: string]: unknown }[];
  };
  watermarks: { finding_recorded_at: string; analytic_built_at: string | null };
  unavailable: Record<string, string>;
  links: {
    canonical: string;
    selected_revision: string;
    api_selected_revision: string;
    canonical_finding: string;
    performance: { status: "OPEN" | "CLOSED"; reason: string; note?: string };
    assessment_revisions: Record<string, string>;
    windows: Record<string, string>;
  };
}

export interface FindingWindowBody {
  day: string;
  state: string;
  note: string;
  assessment_status: string;
  findings: {
    finding_id?: string;
    id?: string;
    lifecycle: Lifecycle;
    episode_start: string;
    episode_end: string;
    cites_current_window_selection: boolean;
    [key: string]: unknown;
  }[];
}

export interface FindingClient {
  getFinding(siteId: string, findingId: string, revisionId: string | null): Promise<FindingReadResult<FindingDetailBody>>;
  getFindingWindow(siteId: string, day: string): Promise<FindingReadResult<FindingWindowBody>>;
}

function isFinding(value: unknown): value is FindingDetailBody {
  return (
    hasKeys(value, ["finding", "selection", "revision", "state", "relations", "revisions", "revision_groups", "links"]) &&
    Array.isArray((value as { revisions: unknown }).revisions)
  );
}

function isWindow(value: unknown): value is FindingWindowBody {
  return hasKeys(value, ["day", "state", "findings"]) && Array.isArray((value as { findings: unknown }).findings);
}

async function readFinding<T>(path: string, valid: (value: unknown) => value is T): Promise<FindingReadResult<T>> {
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
  if (response.ok && valid(body)) {
    return { status: "loaded", value: body };
  }
  const detail = isObject(body) ? body.detail : null;
  const message =
    typeof detail === "string"
      ? detail
      : isObject(detail) && typeof detail.message === "string"
        ? detail.message
        : null;
  switch (response.status) {
    case 401:
      return { status: "unauthenticated", message };
    case 403:
      return { status: "forbidden", message };
    case 404:
      return { status: "not_found", message };
    case 409:
      if (isObject(detail) && detail.code === "PERFORMANCE_CUTOVER_CLOSED") {
        return { status: "closed", message, note: typeof detail.note === "string" ? detail.note : null };
      }
      return { status: "unavailable", message };
    default:
      return { status: "unavailable", message };
  }
}

export function createFindingClient(basePath: string = SITES_API_PATH): FindingClient {
  const site = (siteId: string) => `${basePath}/${encodeURIComponent(siteId)}`;
  return {
    getFinding(siteId, findingId, revisionId) {
      const query = revisionId === null ? "" : `?revision_id=${encodeURIComponent(revisionId)}`;
      return readFinding(`${site(siteId)}/findings/${encodeURIComponent(findingId)}${query}`, isFinding);
    },
    getFindingWindow(siteId, day) {
      return readFinding(`${site(siteId)}/finding-windows/${encodeURIComponent(day)}`, isWindow);
    },
  };
}
