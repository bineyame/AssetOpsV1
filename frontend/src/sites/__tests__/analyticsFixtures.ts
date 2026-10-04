/**
 * T028 analytics read-model fixtures, shaped as the backend serves them
 * (`backend/assetops_backend/analytics/dispatch.py` and `service.py`).
 */
import type {
  Assessment,
  AssessmentDetail,
  AssessmentSummary,
  CapabilityReadiness,
  SiteAnalytics,
  SiteAnalyticsClient,
} from "../siteAnalyticsClient";
import type { EvidenceRead } from "../siteEvidenceClient";
import { RECORD_DETAIL } from "./evidenceFixtures";

const LINK = {
  message_id: RECORD_DETAIL.message_id,
  device_id: "GEN-1",
  signal_id: "output_kw",
  source_time: "2026-09-22T04:00:00Z",
};

const INPUTS = {
  load_kw: "18",
  pv_available_kw: "0",
  soc_pct: "82",
  reserve_pct: "30",
  discharge_capability_kw: "40",
  generator_kw: "20",
  reserve_source: "policy",
};

function assessment(level: "CANDIDATE_AVOIDABLE" | "NECESSARY", start: string, end: string): Assessment {
  const candidate = level === "CANDIDATE_AVOIDABLE";
  return {
    analytic_id: "dispatch",
    model_version: "dispatch-1",
    finding_type: "generator-dispatch-interval",
    claim_level: level,
    label: candidate ? "Candidate avoidable" : "Necessary",
    summary: candidate
      ? "Generator ran 4 h while battery capability covered load; a bounded candidate."
      : "Generator ran while the battery sat at reserve; necessary.",
    raises_finding: candidate,
    interval: {
      first_running_observed: start,
      last_running_observed: end,
      last_stopped_before: null,
      first_stopped_after: null,
      duration_hours: { low: "3.75", high: "4.25" },
      open_start: false,
      open_end: false,
      statement: `Running observed ${start} to ${end}.`,
    },
    assessed_window: { start: "2026-09-22T03:00:00Z", end: "2026-09-22T11:00:00Z" },
    portions_hours: candidate
      ? {
          CANDIDATE_AVOIDABLE: { low: "3.5", high: "4" },
          NECESSARY: { low: "0" },
          INDETERMINATE: { low: "0.25" },
        }
      : { CANDIDATE_AVOIDABLE: { low: "0", high: "0" }, NECESSARY: { low: "2" }, INDETERMINATE: { low: "0" } },
    binding_constraints: candidate ? [] : ["BATTERY_AT_RESERVE"],
    missing_evidence: candidate ? ["Battery discharge capability: no record 05:00 to 05:15"] : [],
    segments: [
      {
        start,
        end,
        minutes: 240,
        observed: true,
        classification: level,
        label: candidate ? "Candidate avoidable" : "Necessary",
        binding_constraint: candidate ? null : "BATTERY_AT_RESERVE",
        reasons: [candidate ? "Battery and PV capability exceeded load." : "SOC at reserve."],
        missing: [],
        inputs: { at_start: INPUTS, at_end: INPUTS },
        evidence: [LINK],
      },
    ],
    coverage: {
      inputs: [
        { input: "soc", label: "Battery SOC", usable_segments: 15, evaluated_segments: 16, gaps: [] },
      ],
      unobserved_generator_state: [],
      statement: "15 of 16 segments had every required input.",
    },
    confidence: {
      level: candidate ? "MEDIUM" : "HIGH",
      basis: candidate ? ["An Indeterminate portion lies inside the interval."] : [],
    },
    alternatives: [
      {
        id: "UNOBSERVED_OVERRIDE",
        label: "Operator-commanded override",
        status: "NOT_EXCLUDED",
        statement: "No operator-commanded override record observed; this is not proof none existed.",
        evidence: [],
      },
      {
        id: "PCS_CAPABILITY_UNAVAILABLE",
        label: "PCS capability unavailable",
        status: "NOT_EXCLUDED",
        statement: "Discharge capability is unrecorded for 15 min.",
        evidence: [LINK],
        gaps: [{ start: "2026-09-22T05:00:00Z", end: "2026-09-22T05:15:00Z", minutes: "15" }],
      },
    ],
    claim_limits: [
      "No operator-commanded override record observed; this is not proof none existed.",
      "A 15 min capability gap limits this claim.",
    ],
    fuel: candidate
      ? {
          status: "BOUNDED",
          basis: "modelled",
          statement: "Indicative only; not a reconciled tank loss or a saving.",
          low_litres: "21.6",
          high_litres: "29.3",
          unit: "L",
          formula: "duration x generator output x specific fuel consumption",
          inputs: {
            duration_hours: { low: "3.5", high: "4", basis: "measured", note: "Candidate segments." },
            generator_kw: { low: "18", high: "20", basis: "measured", note: "Usable means." },
            specific_fuel_consumption: {
              value: "0.3",
              unit: "L/kWh",
              basis: "configured",
              uncertainty_pct: "10",
              source: "Foundation GEN-1",
            },
          },
        }
      : {
          status: "NOT_APPLICABLE",
          basis: "modelled",
          reason: "Only a candidate interval has an indicative fuel quantity.",
          statement: "Not applicable.",
        },
    evidence_basis: { message_ids: [LINK.message_id], digest: "abc123" },
  };
}

function summary(id: string, a: Assessment): AssessmentSummary {
  return {
    assessment_id: id,
    finding_id: a.raises_finding ? id : null,
    analytic_id: a.analytic_id,
    finding_type: a.finding_type,
    active: true,
    retired_at: null,
    revision: 1,
    revisions: 1,
    claim_level: a.claim_level,
    label: a.label,
    summary: a.summary,
    interval: a.interval,
    assessed_window: a.assessed_window,
    confidence: a.confidence.level,
    model_version: a.model_version,
  };
}

export const CANDIDATE_ID = "dispatch-cand0001";
export const NECESSARY_ID = "dispatch-nec00001";
export const CANDIDATE_ASSESSMENT = assessment(
  "CANDIDATE_AVOIDABLE",
  "2026-09-22T03:10:00Z",
  "2026-09-22T07:10:00Z",
);
export const NECESSARY_ASSESSMENT = assessment(
  "NECESSARY",
  "2026-09-22T08:00:00Z",
  "2026-09-22T10:00:00Z",
);
export const CANDIDATE_SUMMARY = summary(CANDIDATE_ID, CANDIDATE_ASSESSMENT);
export const NECESSARY_SUMMARY = summary(NECESSARY_ID, NECESSARY_ASSESSMENT);
export const EVIDENCE_LINK = LINK;

/** A Limited dispatch row as the backend scores the degraded-evidence run (AC20). */
export const LIMITED_READINESS: CapabilityReadiness = {
  basis_version: "readiness-2",
  level: "LIMITED",
  label: "Limited",
  claim_ceiling: {
    claim_level: "CANDIDATE_AVOIDABLE",
    label: "Candidate avoidable",
    statement:
      "Candidate avoidable only for portions whose required inputs are evidenced; portions without them are Indeterminate.",
  },
  missing_evidence: [
    {
      kind: "COVERAGE_GAP",
      role: "Battery discharge capability",
      device_id: null,
      signal_id: null,
      statement:
        "Battery discharge capability: no usable record for 5 of 13 evaluated segments in 1 assessed interval; 5 segment(s) that needed it are Indeterminate.",
      limits_claim: true,
      assessment_ids: [CANDIDATE_ID],
    },
  ],
  optional_not_observed: [
    { role: "Operator override", device_id: "generator-controller", signal_id: "stop-soc-override" },
    { role: "Operator override", device_id: "battery-bms", signal_id: "reserve-override" },
  ],
  assessed_intervals: 1,
  statement: "Scored from the declaration against all accepted evidence for this Site.",
};

export function declaration(
  siteId: string,
  analytics: {
    analytic_id: string;
    display_name: string;
    readiness?: CapabilityReadiness;
  }[] = [
    { analytic_id: "dispatch", display_name: "Dispatch" },
  ],
): SiteAnalytics {
  return {
    site_id: siteId,
    site_type: "MINIGRID",
    statement: "Analytics applicable to this site.",
    analytics: analytics.map((item) => ({
      ...item,
      site_types: ["MINIGRID"],
      finding_type: { id: "generator-dispatch-interval", display_name: "Generator dispatch interval" },
      model_version: "dispatch-1",
      claim_levels: [],
      required_evidence: [],
      optional_evidence: [],
    })),
  };
}

export interface AnalyticsFixture {
  declaration?: SiteAnalytics;
}

/** A fake analytics client over the candidate and Necessary fixtures for `siteId`. */
export function analyticsClient(
  siteId: string,
  options: AnalyticsFixture = {},
): SiteAnalyticsClient {
  const details: Record<string, AssessmentDetail> = {
    [CANDIDATE_ID]: { ...CANDIDATE_SUMMARY, assessment: CANDIDATE_ASSESSMENT, revision_history: [] },
    [NECESSARY_ID]: { ...NECESSARY_SUMMARY, assessment: NECESSARY_ASSESSMENT, revision_history: [] },
  };
  const loaded = <T,>(value: T): Promise<EvidenceRead<T>> =>
    Promise.resolve({ status: "loaded", value });
  return {
    getDeclaration: () => loaded(options.declaration ?? declaration(siteId)),
    getDispatch: () =>
      loaded({
        site_id: siteId,
        analytic_id: "dispatch",
        model_version: "dispatch-1",
        assessments: [
          { ...CANDIDATE_SUMMARY, assessment: CANDIDATE_ASSESSMENT },
          { ...NECESSARY_SUMMARY, assessment: NECESSARY_ASSESSMENT },
        ],
      }),
    getSiteFindings: () => loaded({ site_id: siteId, findings: [CANDIDATE_SUMMARY] }),
    getAssessment: (_site, id) =>
      Promise.resolve(
        details[id] === undefined
          ? { status: "not_found" }
          : { status: "loaded", value: details[id] },
      ),
    getFindings: () =>
      loaded({
        findings: [
          {
            ...CANDIDATE_SUMMARY,
            site_id: siteId,
            site_display_name: "Kobo",
            site_type: "MINIGRID",
          },
        ],
        statement: "Active Findings across every configured Site.",
      }),
  };
}

/**
 * A fake analytics client with no Findings anywhere: the global index loads
 * empty and every per-site read is `not_found`. For tests that only need the
 * Findings rail root to resolve to its real surface without a network read.
 */
export const EMPTY_ANALYTICS_STATEMENT = "Active Findings across every configured Site.";

export const EMPTY_ANALYTICS_CLIENT: SiteAnalyticsClient = {
  getDeclaration: () => Promise.resolve({ status: "not_found" }),
  getDispatch: () => Promise.resolve({ status: "not_found" }),
  getSiteFindings: () => Promise.resolve({ status: "not_found" }),
  getAssessment: () => Promise.resolve({ status: "not_found" }),
  getFindings: () =>
    Promise.resolve({
      status: "loaded",
      value: { findings: [], statement: EMPTY_ANALYTICS_STATEMENT },
    }),
};
