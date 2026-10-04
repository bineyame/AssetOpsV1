/**
 * T028 analytics read-model fixtures, shaped as the backend serves them
 * (`backend/assetops_backend/analytics/dispatch.py` and `service.py`).
 */
import type {
  Assessment,
  AssessmentDetail,
  AssessmentSummary,
  CapabilityReadiness,
  Reading,
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
    model_version: "dispatch-2",
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
    reading: reading(a),
  };
}

/** The backend's plain reading (`plain.reading`) for these fixtures. */
function reading(a: Assessment): Reading {
  const candidate = a.claim_level === "CANDIDATE_AVOIDABLE";
  return {
    outcome: candidate ? "Possibly avoidable" : "Needed",
    headline: candidate
      ? "The generator may have operated longer than needed."
      : "The generator was needed during this period.",
    reason: candidate
      ? "For 3 h 30 min to 4 h of this period, the reported solar power and available battery output were more than the site demand, and no reason the generator was needed was recorded."
      : "Battery charge was at or below its minimum reserve.",
    meaning: candidate
      ? "Possibly avoidable means that, for that time, the reported solar power and available battery output were more than the site demand, and no reason the generator was needed was recorded. It is not proof of wasted fuel and not a judgement of how the generator should have been operated."
      : "Needed means a recorded reason required the generator to operate. It does not judge whether that setting or limit is right.",
    generator: "Generator",
    operating_time: "3 h 45 min to 4 h 15 min",
    portions: candidate
      ? { possibly_avoidable: "3 h 30 min to 4 h", needed: "0 min", cannot_determine: "15 min" }
      : { possibly_avoidable: "0 min", needed: "2 h", cannot_determine: "0 min" },
    reasons_needed: candidate ? [] : ["Battery at minimum reserve"],
    missing: candidate ? ["Available battery output: no record received"] : [],
    confidence: candidate
      ? {
          word: "Medium",
          explanation: ["15 min of the period cannot be determined, which lowers confidence."],
          principal_limitation: "15 min of the period cannot be determined, which lowers confidence.",
        }
      : { word: "High", explanation: ["Every part of the period could be assessed."], principal_limitation: null },
    limits: candidate
      ? [
          "This is an assessment of the reported values, not proof of wasted fuel and not a judgement of how the generator should have been operated.",
          "No operator instruction was recorded for this period, but that does not prove none was given.",
          "15 min of this period cannot be determined and is not part of the possibly avoidable time.",
        ]
      : ["This shows the generator was needed for the reason given. It does not judge whether that setting or limit is right."],
    fuel: candidate
      ? {
          label: "Estimated fuel associated with possibly avoidable operation",
          text: "21.6 to 29.3 litres",
          note: "This is an estimate, not confirmed fuel savings, for 3 h 30 min to 4 h of possibly avoidable operation.",
        }
      : {
          label: "Estimated fuel associated with possibly avoidable operation",
          text: null,
          note: "No fuel estimate: no possibly avoidable operation was found in this period.",
        },
    duration_note:
      "The shorter figure counts only the times the generator was recorded as operating. The longer figure spans from the last record showing it off before the period to the first record showing it off after.",
    coverage_note:
      "Each assessed part of the period is checked for a usable record of each input; a part without one cannot be determined.",
    segments: a.segments.map(() =>
      candidate
        ? {
            outcome: "Possibly avoidable",
            reason:
              "The available solar power and battery output were more than the site demand, with battery charge above its minimum reserve; no reason the generator was needed was recorded.",
            missing: [],
          }
        : { outcome: "Needed", reason: "Needed: battery charge was at or below its minimum reserve.", missing: [] },
    ),
    alternatives: [
      {
        id: "UNOBSERVED_OVERRIDE",
        label: "Unrecorded operator instruction",
        status: "Still possible",
        statement: "No operator instruction was recorded for this period. That does not prove none was given.",
      },
      {
        id: "PCS_CAPABILITY_UNAVAILABLE",
        label: "Battery output not reported",
        status: "Still possible",
        statement:
          "Available battery output was not reported for 15 min of this period, so battery support there is unknown and that time is not counted as possibly avoidable.",
      },
    ],
    next_steps: candidate
      ? [
          {
            id: "CONFIRM_OPERATOR_INSTRUCTION",
            text: "Confirm whether an operator instruction kept the generator on during this period. No instruction was recorded, and that absence is not proof that none was given.",
            target: { kind: "alternative", id: "UNOBSERVED_OVERRIDE" },
          },
          {
            id: "CHECK_BATTERY_CAPABILITY",
            text: "Check why available battery output was not reported for 15 min of this period; battery support there is unknown, so that time cannot be assessed.",
            target: { kind: "alternative", id: "PCS_CAPABILITY_UNAVAILABLE" },
          },
        ]
      : [
          {
            id: "CHECK_CONSTRAINT_IF_UNEXPECTED",
            text: "No possibly avoidable operation was found. If the reason shown is unexpected, check how that setting or limit is configured; this assessment does not judge the setting.",
            target: { kind: "none" },
          },
        ],
    framing:
      "These are checks to make before considering any change. They are not an instruction to stop the generator or to change a setting.",
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
  basis_version: "readiness-3",
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
  question: "What can we assess from this site's records?",
  meaning:
    "Assessments are possible but limited: the missing records named below limit the conclusion or leave parts of periods undetermined.",
  scope:
    "Based on all of this site's accepted records, not only the selected window. It is not a rating of the site's health and not permission to act.",
  method:
    "How this is scored: Full means every required input has at least one usable accepted record and no assessed part of a period was left undetermined by a missing record.",
  conclusion:
    "Possibly avoidable operation can be identified only where the required records exist; other time cannot be determined.",
  gaps: [
    "Available battery output: no usable record for 5 of 13 assessed parts in 1 assessed period; 5 part(s) that needed it cannot be determined.",
  ],
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
      model_version: "dispatch-2",
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
        model_version: "dispatch-2",
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
