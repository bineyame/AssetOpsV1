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
  evidence: OverviewEvidenceLink[];
  unavailable_because: string | null;
}

export interface OverviewCoverage {
  device_id: string;
  signal_id: string;
  status: "REPORTED" | "NOT_REPORTED" | "NO_GOOD_RECORD" | string;
  records: number;
  good: number;
  unavailable: number;
  last_source_time: string | null;
}

export interface OverviewCard {
  domain_id: string;
  label: string;
  assessment: OverviewAssessment;
  metrics: OverviewMetric[];
  coverage: OverviewCoverage[];
  gaps: { device_id: string; signal_id: string; status: string }[];
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
  sources_in_window: number;
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

export interface SiteOverviewClient {
  getOverview(
    siteId: string,
    window: EvidenceWindowQuery,
  ): Promise<EvidenceRead<SiteOverviewReadModel>>;
}

const METRIC_KEYS = [
  "metric_id",
  "label",
  "unit",
  "value",
  "basis",
  "evidence",
] as const;

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
    ]) &&
    isObject(value) &&
    hasKeys(value.window, ["start", "end", "basis", "hours"]) &&
    hasKeys(value.objective, ["assessment", "service_delivered"]) &&
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
        arrayOf(card.metrics, METRIC_KEYS) &&
        arrayOf(card.coverage, ["device_id", "signal_id", "status"]),
    ) &&
    arrayOf(value.timeline, ["series_id", "label", "unit", "kind", "points"]) &&
    Array.isArray(value.findings)
  );
}

export function createSiteOverviewClient(
  basePath: string = SITES_API_PATH,
): SiteOverviewClient {
  return {
    getOverview(siteId, window) {
      return read(
        `${basePath}/${encodeURIComponent(siteId)}/overview${query({
          from: window.from,
          to: window.to,
        })}`,
        isSiteOverview,
      );
    },
  };
}
