/**
 * Analytics read models (T028): the backend's capability declaration, the
 * dispatch assessments, the Findings indexes and one assessment with its
 * revision history.
 *
 * Every screen that shows an assessment reads it from here, so Performance >
 * Dispatch, Finding detail, the Findings indexes and the Overview card all
 * refer to the same backend object by its `assessment_id`; nothing on the
 * client recomputes a classification, a bound or a confidence level. Numbers
 * arrive as decimal strings and are shown as they arrive.
 *
 * Operator reads, served with the Simulator Lab gate open or closed.
 */
import { SITES_API_PATH } from "./siteDirectoryClient";
import {
  arrayOf,
  hasKeys,
  isObject,
  read,
  type EvidenceRead,
} from "./siteEvidenceClient";

export const FINDINGS_API_PATH = "/api/findings";

export type ClaimLevel = "NECESSARY" | "CANDIDATE_AVOIDABLE" | "INDETERMINATE";

export interface TimeWindow {
  start: string;
  end: string;
}

export interface EvidenceLink {
  message_id: string;
  device_id: string;
  signal_id: string;
  source_time: string;
}

export interface Span {
  start: string;
  end: string;
  minutes: string;
}

export interface Bound {
  low: string;
  high?: string | null;
}

export interface DispatchIntervalRead {
  first_running_observed: string;
  last_running_observed: string;
  last_stopped_before: string | null;
  first_stopped_after: string | null;
  duration_hours: { low: string; high: string | null };
  open_start: boolean;
  open_end: boolean;
  statement: string;
}

export interface SegmentInputs {
  load_kw: string | null;
  pv_available_kw: string | null;
  soc_pct: string | null;
  reserve_pct: string | null;
  discharge_capability_kw: string | null;
  generator_kw: string | null;
  reserve_source: string | null;
}

export interface Segment {
  start: string;
  end: string;
  minutes: number;
  observed: boolean;
  classification: ClaimLevel;
  label: string;
  binding_constraint: string | null;
  reasons: string[];
  missing: string[];
  inputs: { at_start?: SegmentInputs; at_end?: SegmentInputs };
  evidence: EvidenceLink[];
}

export interface CoverageInput {
  input: string;
  label: string;
  usable_segments: number;
  evaluated_segments: number;
  gaps: Span[];
}

export interface Alternative {
  id: string;
  label: string;
  status: "OBSERVED" | "NOT_EXCLUDED" | "CONTRADICTED_BY_EVIDENCE" | string;
  statement: string;
  evidence: EvidenceLink[];
  gaps?: Span[];
}

export interface FuelInputs {
  duration_hours: { low: string; high: string; basis: string; note: string };
  generator_kw: { low: string; high: string; basis: string; note: string };
  specific_fuel_consumption: {
    value: string;
    unit: string;
    basis: string;
    uncertainty_pct: string;
    source: string;
  };
}

export interface Fuel {
  status: "BOUNDED" | "UNAVAILABLE" | "NOT_APPLICABLE" | string;
  basis: string;
  statement: string;
  reason?: string;
  low_litres?: string;
  high_litres?: string;
  unit?: string;
  formula?: string;
  inputs?: FuelInputs;
}

export interface Assessment {
  analytic_id: string;
  model_version: string;
  finding_type: string;
  claim_level: ClaimLevel;
  label: string;
  summary: string;
  raises_finding: boolean;
  interval: DispatchIntervalRead;
  assessed_window: TimeWindow;
  portions_hours: Record<string, Bound>;
  binding_constraints: string[];
  missing_evidence: string[];
  segments: Segment[];
  coverage: {
    inputs: CoverageInput[];
    unobserved_generator_state: Span[];
    statement: string;
  };
  confidence: { level: string; basis: string[] };
  alternatives: Alternative[];
  claim_limits: string[];
  fuel: Fuel;
  evidence_basis: { message_ids: string[]; digest: string };
}

/** One assessment lineage, as every index lists it. */
export interface AssessmentSummary {
  assessment_id: string;
  /** Equal to `assessment_id` when the latest revision raises a Finding; else null. */
  finding_id: string | null;
  analytic_id: string;
  finding_type: string;
  active: boolean;
  retired_at: string | null;
  revision: number;
  revisions: number;
  claim_level: ClaimLevel;
  label: string;
  summary: string;
  interval: DispatchIntervalRead;
  assessed_window: TimeWindow;
  confidence: string;
  model_version: string;
}

export interface RevisionSummary {
  revision: number;
  assessed_at: string;
  model_version: string;
  evidence_basis_digest: string;
  evidence_records: number;
  assessed_window: TimeWindow;
  claim_level: ClaimLevel;
  label: string;
  summary: string;
}

export interface AssessmentDetail extends AssessmentSummary {
  assessment: Assessment;
  revision_history: RevisionSummary[];
}

export interface DispatchAssessments {
  site_id: string;
  analytic_id: string;
  model_version: string;
  assessments: (AssessmentSummary & { assessment: Assessment })[];
}

export interface SiteFindings {
  site_id: string;
  findings: AssessmentSummary[];
}

export interface GlobalFinding extends AssessmentSummary {
  site_id: string;
  site_display_name: string;
  site_type: string;
}

export interface GlobalFindings {
  findings: GlobalFinding[];
  statement: string;
}

export interface ClaimLevelDeclaration {
  claim_level: ClaimLevel;
  label: string;
  ceiling: string;
}

export interface EvidenceRequirement {
  device_id: string;
  signal_id: string;
  family: string;
  role: string;
  available: boolean;
  usable_records: number;
  last_source_time: string | null;
}

export interface AnalyticDeclaration {
  analytic_id: string;
  display_name: string;
  site_types: string[];
  finding_type: { id: string; display_name: string };
  model_version: string;
  claim_levels: ClaimLevelDeclaration[];
  required_evidence: EvidenceRequirement[];
  optional_evidence: EvidenceRequirement[];
}

export interface SiteAnalytics {
  site_id: string;
  site_type: string;
  statement: string;
  analytics: AnalyticDeclaration[];
}

export interface SiteAnalyticsClient {
  getDeclaration(siteId: string): Promise<EvidenceRead<SiteAnalytics>>;
  getDispatch(siteId: string): Promise<EvidenceRead<DispatchAssessments>>;
  getSiteFindings(siteId: string): Promise<EvidenceRead<SiteFindings>>;
  getAssessment(
    siteId: string,
    assessmentId: string,
  ): Promise<EvidenceRead<AssessmentDetail>>;
  getFindings(): Promise<EvidenceRead<GlobalFindings>>;
}

const SUMMARY_KEYS = [
  "assessment_id",
  "finding_id",
  "claim_level",
  "label",
  "summary",
  "interval",
  "assessed_window",
] as const;

const ASSESSMENT_KEYS = [
  "claim_level",
  "summary",
  "interval",
  "assessed_window",
  "segments",
  "coverage",
  "confidence",
  "alternatives",
  "claim_limits",
  "fuel",
  "evidence_basis",
] as const;

function isAssessment(value: unknown): value is Assessment {
  return (
    hasKeys(value, ASSESSMENT_KEYS) &&
    isObject(value) &&
    Array.isArray(value.segments) &&
    Array.isArray(value.alternatives)
  );
}

function isDeclaration(value: unknown): value is SiteAnalytics {
  return (
    hasKeys(value, ["site_id", "site_type", "analytics"]) &&
    arrayOf((value as { analytics: unknown }).analytics, [
      "analytic_id",
      "display_name",
      "finding_type",
      "claim_levels",
    ])
  );
}

function isDispatch(value: unknown): value is DispatchAssessments {
  if (!hasKeys(value, ["site_id", "assessments"])) {
    return false;
  }
  const rows = (value as { assessments: unknown }).assessments;
  return (
    arrayOf(rows, [...SUMMARY_KEYS, "assessment"]) &&
    (rows as { assessment: unknown }[]).every((row) => isAssessment(row.assessment))
  );
}

function isSiteFindings(value: unknown): value is SiteFindings {
  return (
    hasKeys(value, ["site_id", "findings"]) &&
    arrayOf((value as { findings: unknown }).findings, SUMMARY_KEYS)
  );
}

function isGlobalFindings(value: unknown): value is GlobalFindings {
  return (
    hasKeys(value, ["findings", "statement"]) &&
    arrayOf((value as { findings: unknown }).findings, [
      ...SUMMARY_KEYS,
      "site_id",
      "site_display_name",
    ])
  );
}

function isDetail(value: unknown): value is AssessmentDetail {
  return (
    hasKeys(value, [...SUMMARY_KEYS, "assessment", "revision_history"]) &&
    isAssessment((value as { assessment: unknown }).assessment)
  );
}

export function createSiteAnalyticsClient(
  basePath: string = SITES_API_PATH,
  findingsPath: string = FINDINGS_API_PATH,
): SiteAnalyticsClient {
  const site = (siteId: string) => `${basePath}/${encodeURIComponent(siteId)}`;
  return {
    getDeclaration(siteId) {
      return read(`${site(siteId)}/analytics`, isDeclaration);
    },
    getDispatch(siteId) {
      return read(`${site(siteId)}/dispatch`, isDispatch);
    },
    getSiteFindings(siteId) {
      return read(`${site(siteId)}/findings`, isSiteFindings);
    },
    getAssessment(siteId, assessmentId) {
      return read(
        `${site(siteId)}/assessments/${encodeURIComponent(assessmentId)}`,
        isDetail,
      );
    },
    getFindings() {
      return read(findingsPath, isGlobalFindings);
    },
  };
}
