/**
 * S5-01/S5-02 test fixtures: the imported Site's `site-window-summary-1` read for one UTC day, as the server
 * serves it. Shared by the S5-01 Overview tests and the S5-02 Finding list tests.
 */
import type { SiteWindowSummary, WindowMoney } from "../../sites/siteOverviewClient";

export const FID = "11111111-1111-4111-8111-111111111111";
export const RID = "22222222-2222-4222-8222-222222222222";
export const RID_NEW = "23232323-2323-4232-8232-232323232323";
export const CID = "33333333-3333-4333-8333-333333333333";
export const PRICE = "44444444-4444-4444-8444-444444444444";
export const EVIDENCE = "55555555-5555-4555-8555-555555555555";
export const WA = "66666666-6666-4666-8666-666666666666";
export const INTERVAL = "77777777-7777-4777-8777-777777777777";


export function money(over: Partial<WindowMoney> = {}): WindowMoney {
  return {
    state: "PRICED",
    amount_low: "0.00",
    amount_high: "15.82",
    currency: "USD",
    model_version: "fuel-cost-1",
    finding_id: FID,
    finding_revision_id: RID,
    consequence_revision_id: CID,
    eligibility: {
      version: "lr01-1",
      state: "ELIGIBLE",
      note: "gate note",
      pending_reasons: [],
      series_limits: [],
      latest_finding_revision_id: RID,
      end_reason: null,
    },
    quantity_state: "BOUNDED",
    price_state: "PRICED",
    limitation: null,
    demonstration: {
      label: "Demonstration data",
      statement: "This Finding comes from an authored demonstration case.",
      case_id: "P01-power",
      spec: "s4-power-demo-cases-v1",
    },
    label: "fuel-cost-1 model-conditioned potential fuel-cost exposure: zero lower bound. Not savings.",
    upstream: { status: "CURRENT", stage: null, reasons: [] },
    links: {
      assumption_revisions: { [PRICE]: `/api/sites/KOBO-001/financial-assumptions/${PRICE}` },
      evidence_records: { [EVIDENCE]: `/api/sites/KOBO-001/evidence/records/${EVIDENCE}` },
      assessment_revisions: { [INTERVAL]: `/api/x/${INTERVAL}` },
    },
    ...over,
  };
}

export function summary(day = "2026-10-23", over: Partial<SiteWindowSummary> = {}, m: Partial<WindowMoney> = {}): SiteWindowSummary {
  return {
    schema_version: "site-window-summary-1",
    site_id: "site-uuid",
    site_code: "KOBO-001",
    access_basis: "DEVELOPMENT_UNAUTHENTICATED",
    window: { start: `${day}T00:00:00Z`, end: `${day}T23:59:59Z`, utc_date: day, bounds: "[start, end)" },
    built_at: `${day}T12:00:00Z`,
    db_now: `${day}T12:00:00Z`,
    freshness: { state: "CURRENT", stage: null, reasons: [], errors: [], source_open: true, source_reason: "open" },
    watermarks: {
      accepted_source: { count: 3, sha256: "abc" },
      accepted_source_reason: null,
      analytic_selection_seq: 4,
      input_sha256: "def",
      configuration_sha256: "ghi",
      match_pass_id: "mp",
      matched_through_selection_seq: 4,
    },
    model_version: "dispatch-3.1",
    assessment: {
      state: "CURRENT",
      status: "CURRENT",
      status_reasons: [],
      run_id: "run-1",
      window_assessment_revision_id: WA,
      claim_level: "CANDIDATE_AVOIDABLE",
      limitations: [],
      coverage: null,
      dispatch_intervals: [
        {
          revision_id: INTERVAL,
          start: `${day}T06:00:00Z`,
          end: `${day}T08:00:00Z`,
          claim_level: "CANDIDATE_AVOIDABLE",
          assessment_key: "k",
          link: `/api/sites/KOBO-001/performance/dispatch/revisions/${INTERVAL}`,
        },
      ],
      links: {},
    },
    context: {
      series: [
        {
          evidence_id: EVIDENCE,
          time: `${day}T06:05:00Z`,
          interval: null,
          device_id: "GEN-1",
          signal_id: "P",
          role: "generator_power",
          value: "20",
          unit: "kW",
          quality: "GOOD",
          unavailable_reason: null,
        },
      ],
      total: 1,
      truncated: false,
      coverage: [
        {
          device_id: "GEN-1",
          signal_id: "P",
          role: "generator_power",
          unit: "kW",
          records: 1,
          good: 1,
          first_source_time: `${day}T06:05:00Z`,
          last_source_time: `${day}T06:05:00Z`,
        },
      ],
      gaps: null,
      gaps_reason: "No reviewed gap rule exists for the Site context.",
      evidence_links: {},
    },
    money: money(m),
    known_finding: {
      id: FID,
      revision_id: m.finding_revision_id ?? RID,
      selection_rule: "greatest episode_start, then smallest Finding UUID",
      selected_by: "DISCOVERED",
      episode: { start: `${day}T06:00:00Z`, end: `${day}T08:00:00Z` },
      audit_only: false,
      several_intersect: false,
      note: "This card covers this Finding only; it is not a Site total.",
      excluded: [],
      previous_pin: null,
      link: { page: "", api: "" },
    },
    finding_list: { state: "UNAVAILABLE", reason: "Unavailable until the Site Finding index is delivered." },
    ...over,
  };
}

