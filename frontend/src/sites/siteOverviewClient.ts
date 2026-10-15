/**
 * Read-only client for a Site's mini-grid Overview (T027 phase 2).
 *
 * The Overview read lives beside Site > Evidence (`GET
 * /api/sites/{id}/overview`, `evidence_api.py`) and, like it, is an operator
 * capability served with the Simulator Lab gate closed. Every value is the
 * backend's: card state, metrics, coverage gaps and the timeline are computed
 * from accepted evidence; nothing here derives a number.
 *
 * Values are exact decimal text, never floats. Failures are named states
 * (`EvidenceRead`), and a response of the wrong shape is `unavailable` rather
 * than a partial page.
 */

import type { TimelineSource } from "./assessmentGraphics";
import { SITES_API_PATH } from "./siteDirectoryClient";
import {
  arrayOf,
  hasKeys,
  isObject,
  query,
  read,
  type EvidenceRead,
  type EvidenceWindowQuery,
} from "./siteEvidenceClient";

export interface OverviewAssessment {
  /** `NO_ASSESSMENT` until an analytic exists; never `UNKNOWN` for that. */
  status: string;
  label: string;
  reason: string;
  /** T028: present when an analytic assessed this domain. */
  capability_id?: string;
  capability_display_name?: string;
  model_version?: string;
  assessment_ids?: string[];
  lead_assessment_id?: string;
  lead_revision?: number;
  /**
   * T028 presentation checkpoint 2a: the lead assessment's stored segments,
   * interval and fuel bounds, copied for the card's compact timeline so the
   * card draws the same period as its Finding without fetching it.
   */
  lead_timeline?: CardTimeline;
}

export interface CardTimeline extends TimelineSource {
  segments: (TimelineSource["segments"][number] & { outcome: string })[];
  fuel: {
    status: string;
    low_litres: string | null;
    high_litres: string | null;
    label: string;
    text: string | null;
    note: string;
  };
}

export interface OverviewEvidenceLink {
  device_id: string;
  signal_id: string;
  message_id: string;
}

export interface OverviewMetric {
  metric_id: string;
  label: string;
  unit: string;
  value: string | null;
  at: string | null;
  basis: string;
  /** Interval metrics: the measured share of the window, e.g. "2.67 h of the 8.00 h window measured". */
  window_note: string | null;
  evidence: OverviewEvidenceLink[];
  unavailable_because: string | null;
}

export interface OverviewCoverage {
  device_id: string;
  signal_id: string;
  status:
    | "REPORTED"
    | "NOT_REPORTED"
    | "NO_GOOD_RECORD"
    | "NO_INTERVAL_SPAN"
    | "OVERLAPPING_ONLY"
    | "OVERLAPPING_OR_NO_SPAN"
    | string;
  records: number;
  good: number;
  /** Records a metric can read: non-overlapping, with an interval span where needed. */
  usable: number;
  unavailable: number;
  last_source_time: string | null;
}

export interface OverviewCard {
  domain_id: string;
  label: string;
  assessment: OverviewAssessment;
  metrics: OverviewMetric[];
  coverage: OverviewCoverage[];
  gaps: {
    device_id: string;
    signal_id: string;
    status: string;
    reason: string;
  }[];
}

export interface OverviewIntervalPoint {
  start: string;
  end: string;
  value: string;
  message_id: string | null;
}

export interface OverviewInstantPoint {
  at: string;
  value: string;
  message_id: string;
}

export interface OverviewSeries {
  series_id: string;
  label: string;
  unit: string;
  kind: "INTERVAL_MEAN" | "STATE_AT_INSTANT" | string;
  basis: string;
  points: (OverviewIntervalPoint | OverviewInstantPoint)[];
}

export interface SiteOverviewReadModel {
  site_id: string;
  site_type: string;
  window: {
    start: string | null;
    end: string | null;
    basis: string;
    hours: string | null;
  };
  accepted_in_window: number;
  source_gateway_pairs_in_window: number;
  objective: {
    assessment: OverviewAssessment;
    service_delivered: OverviewMetric | null;
  };
  cards: OverviewCard[];
  interval_statement: string;
  timeline: OverviewSeries[];
  timeline_statement: string;
  findings: unknown[];
  findings_statement: string;
}

/**
 * S5-01: the selection an imported Site's Overview carries in its URL. `date`
 * is one UTC day (`YYYY-MM-DD`); the Finding pin is optional and checked by
 * the server against the Site's scope.
 */
export interface OverviewSelection {
  date?: string | null;
  finding_id?: string | null;
  finding_revision_id?: string | null;
}

export interface SiteOverviewClient {
  getOverview(
    siteId: string,
    window: EvidenceWindowQuery,
    selection?: OverviewSelection,
  ): Promise<EvidenceRead<SiteOverviewReadModel | SiteWindowSummary>>;
}

const METRIC_KEYS = [
  "metric_id",
  "label",
  "unit",
  "value",
  "at",
  "basis",
  "window_note",
  "evidence",
  "unavailable_because",
] as const;

const EVIDENCE_KEYS = ["device_id", "signal_id", "message_id"] as const;

function isMetric(value: unknown): boolean {
  return (
    hasKeys(value, METRIC_KEYS) &&
    isObject(value) &&
    arrayOf(value.evidence, EVIDENCE_KEYS)
  );
}

function isPoint(value: unknown): boolean {
  return (
    hasKeys(value, ["value", "message_id"]) &&
    (hasKeys(value, ["start", "end"]) || hasKeys(value, ["at"]))
  );
}

/**
 * Every field the Overview renders is checked (review F4): a response that
 * lacks one is `unavailable`, so backend drift reads as "Overview unavailable"
 * rather than as empty text on a card.
 */
function isSiteOverview(value: unknown): value is SiteOverviewReadModel {
  return (
    hasKeys(value, [
      "site_id",
      "site_type",
      "window",
      "objective",
      "cards",
      "timeline",
      "findings",
      "accepted_in_window",
      "source_gateway_pairs_in_window",
      "interval_statement",
      "timeline_statement",
      "findings_statement",
    ]) &&
    isObject(value) &&
    hasKeys(value.window, ["start", "end", "basis", "hours"]) &&
    hasKeys(value.objective, ["assessment", "service_delivered"]) &&
    isObject(value.objective) &&
    hasKeys(value.objective.assessment, ["status", "label", "reason"]) &&
    (value.objective.service_delivered === null ||
      isMetric(value.objective.service_delivered)) &&
    arrayOf(value.cards, [
      "domain_id",
      "label",
      "assessment",
      "metrics",
      "coverage",
      "gaps",
    ]) &&
    (value.cards as unknown[]).every(
      (card) =>
        isObject(card) &&
        hasKeys(card.assessment, ["status", "label", "reason"]) &&
        Array.isArray(card.metrics) &&
        card.metrics.every(isMetric) &&
        arrayOf(card.coverage, [
          "device_id",
          "signal_id",
          "status",
          "records",
          "good",
          "unavailable",
        ]) &&
        arrayOf(card.gaps, ["device_id", "signal_id", "status", "reason"]),
    ) &&
    arrayOf(value.timeline, [
      "series_id",
      "label",
      "unit",
      "kind",
      "basis",
      "points",
    ]) &&
    (value.timeline as unknown[]).every(
      (series) =>
        isObject(series) &&
        Array.isArray(series.points) &&
        series.points.every(isPoint),
    ) &&
    Array.isArray(value.findings)
  );
}

// ---------------------------------------------------------------- S5-01
// The imported-Site selected-window read (`site-window-summary-1`). Every
// state, reason, amount and link is the server's; the UI chooses words for
// the server's state names and derives nothing.

export const SITE_WINDOW_SUMMARY_SCHEMA = "site-window-summary-1";

export interface WindowAssessmentInterval {
  revision_id: string;
  start: string | null;
  end: string | null;
  claim_level: string | null;
  assessment_key: string | null;
  link: string;
}

export interface WindowAssessment {
  /** `UNKNOWN` (no selected S3 day), `CLOSED` (source gate), or the S3 status. */
  state: string;
  status: string | null;
  status_reasons?: string[];
  reason?: string;
  run_id: string | null;
  window_assessment_revision_id: string | null;
  claim_level: string | null;
  limitations: unknown[];
  objective?: unknown;
  coverage: unknown;
  dispatch_intervals: WindowAssessmentInterval[];
  links: Record<string, string>;
}

export interface WindowReading {
  evidence_id: string;
  time: string | null;
  interval: { start: string | null; end: string | null } | null;
  device_id: string;
  signal_id: string;
  role: string | null;
  value: string | null;
  unit: string | null;
  quality: string;
  unavailable_reason: string | null;
}

export interface WindowCoverage {
  device_id: string;
  signal_id: string;
  role: string | null;
  unit: string | null;
  records: number;
  good: number;
  first_source_time: string | null;
  last_source_time: string | null;
}

export interface WindowContext {
  series: WindowReading[] | null;
  total?: number;
  truncated?: boolean;
  limit?: number;
  coverage: WindowCoverage[] | null;
  gaps: unknown;
  gaps_reason?: string;
  reason?: string;
  evidence_links: Record<string, string>;
}

export interface WindowMoneyEligibility {
  version: string | null;
  state: string | null;
  note: string | null;
  pending_reasons: unknown;
  series_limits: unknown;
  latest_finding_revision_id: string | null;
  end_reason: string | null;
}

export interface WindowMoney {
  state: string;
  amount_low: string | null;
  amount_high: string | null;
  currency: string | null;
  model_version: string | null;
  finding_id: string | null;
  finding_revision_id: string | null;
  consequence_revision_id: string | null;
  eligibility: WindowMoneyEligibility | null;
  quantity_state: string | null;
  price_state: string | null;
  limitation: string[] | null;
  demonstration: { label: string; statement: string; case_id: string; spec: string } | null;
  label: string;
  upstream: { status: string; stage: string | null; reasons: string[] };
  consequence_currentness?: { state: string | null; reasons: unknown; pending_work: unknown };
  links: {
    finding?: string;
    financials?: string;
    consequence?: string;
    price_revision?: string;
    assumption_revisions?: Record<string, string>;
    evidence_records?: Record<string, string>;
    assessment_revisions?: Record<string, string>;
  };
}

export interface WindowKnownFinding {
  id: string;
  revision_id: string;
  selection_rule: string;
  selected_by: string;
  episode: { start: string | null; end: string | null };
  audit_only: boolean;
  several_intersect: boolean;
  note: string;
  excluded: { finding_id: string; reason: string }[];
  previous_pin: { finding_id: string; reason: string } | null;
  link: { page: string; api: string };
}

export interface SiteWindowSummary {
  schema_version: typeof SITE_WINDOW_SUMMARY_SCHEMA;
  site_id: string;
  site_code: string;
  access_basis: string;
  window: { start: string; end: string; utc_date: string; bounds: string };
  built_at: string | null;
  db_now: string | null;
  freshness: {
    state: string;
    stage: string | null;
    reasons: string[];
    errors: unknown[];
    source_open: boolean;
    source_reason: string;
  };
  watermarks: {
    accepted_source: { count: number; sha256: string } | null;
    accepted_source_reason: string | null;
    analytic_selection_seq: unknown;
    input_sha256: string | null;
    configuration_sha256: string | null;
    match_pass_id: string | null;
    matched_through_selection_seq: unknown;
  };
  model_version: string | null;
  assessment: WindowAssessment;
  context: WindowContext;
  money: WindowMoney;
  known_finding: WindowKnownFinding | null;
  finding_list: { state: "UNAVAILABLE"; reason: string };
}

/** The S5 shape is recognised by its schema version and every field the screen renders. */
export function isSiteWindowSummary(value: unknown): value is SiteWindowSummary {
  return (
    isObject(value) &&
    value.schema_version === SITE_WINDOW_SUMMARY_SCHEMA &&
    hasKeys(value, [
      "site_code",
      "access_basis",
      "window",
      "freshness",
      "watermarks",
      "assessment",
      "context",
      "money",
      "known_finding",
      "finding_list",
    ]) &&
    hasKeys(value.window, ["start", "end", "utc_date"]) &&
    isObject(value.freshness) &&
    hasKeys(value.freshness, ["state", "reasons", "source_open", "source_reason"]) &&
    Array.isArray(value.freshness.reasons) &&
    isObject(value.assessment) &&
    hasKeys(value.assessment, ["state", "run_id", "window_assessment_revision_id", "dispatch_intervals", "links"]) &&
    arrayOf(value.assessment.dispatch_intervals, ["revision_id", "start", "end", "link"]) &&
    hasKeys(value.context, ["series", "coverage", "evidence_links"]) &&
    hasKeys(value.money, [
      "state",
      "amount_low",
      "amount_high",
      "currency",
      "finding_id",
      "finding_revision_id",
      "consequence_revision_id",
      "eligibility",
      "upstream",
      "links",
      "label",
    ]) &&
    (value.known_finding === null ||
      hasKeys(value.known_finding, ["id", "revision_id", "selection_rule", "selected_by", "link"])) &&
    isObject(value.finding_list) &&
    value.finding_list.state === "UNAVAILABLE" &&
    typeof value.finding_list.reason === "string"
  );
}

function isOverviewBody(value: unknown): value is SiteOverviewReadModel | SiteWindowSummary {
  return isSiteWindowSummary(value) || isSiteOverview(value);
}

export function createSiteOverviewClient(
  basePath: string = SITES_API_PATH,
): SiteOverviewClient {
  return {
    getOverview(siteId, window, selection = {}) {
      return read(
        `${basePath}/${encodeURIComponent(siteId)}/overview${query({
          from: window.from,
          to: window.to,
          date: selection.date,
          finding_id: selection.finding_id,
          finding_revision_id: selection.finding_revision_id,
        })}`,
        isOverviewBody,
      );
    },
  };
}
