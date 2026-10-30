/**
 * W3-03 run 2: a typed Portfolio response shaped like the clean 10-06 four-Site fixture (one W1 mini-grid, one
 * cold-chain, two EV Sites). IDs and amounts are test values, never page copy.
 */
import type {
  EstateClient,
  EstateCoverageSite,
  EstateOutcomeSummaryBody,
  EstateOutcomeSummaryRow,
  EstateQuery,
  EstatePortfolioBody,
  EstatePortfolioQuery,
  EstatePortfolioRow,
  EstatePortfolioStatus,
  EstateResult,
  EstateValueCard,
} from "../estateClient";

export const SITES = [
  { site_id: "11111111-0000-4000-8000-000000000001", site_code: "KOBO-001", site_name: "Kobo", domain: "MINIGRID" },
  { site_id: "22222222-0000-4000-8000-000000000002", site_code: "COLD-001", site_name: "GreenHarvest", domain: "COLDCHAIN" },
  { site_id: "33333333-0000-4000-8000-000000000003", site_code: "EV-LAB-001", site_name: "Depot", domain: "EV_CHARGING" },
  { site_id: "44444444-0000-4000-8000-000000000004", site_code: "EV-LAB-002", site_name: "Harbour", domain: "EV_CHARGING" },
] as const;

export function coverageSite(siteId: string, state: EstateCoverageSite["state"] = "CURRENT"): EstateCoverageSite {
  return {
    site_id: siteId,
    state,
    committed_watermark: "2026-10-06T23:00:00Z",
    selection_id: "aaaaaaaa-0000-4000-8000-00000000000a",
    match_state: "MATCHED",
    job_state: "SETTLED",
    source_freshness: "FRESH",
  };
}

export function row(over: Partial<EstatePortfolioRow> = {}): EstatePortfolioRow {
  return {
    site_id: SITES[0].site_id,
    site_code: "KOBO-001",
    site_name: "Kobo",
    domain: "MINIGRID",
    finding_id: "f1f1f1f1-0000-4000-8000-000000000001",
    finding_revision_id: "e1e1e1e1-0000-4000-8000-000000000001",
    finding_label: "Extended generator support",
    title: "Extended generator support",
    mechanism: "GENERATOR_SUPPORT_CANDIDATE",
    episode_start: "2026-10-06T14:20:00Z",
    episode_end: "2026-10-06T15:20:00Z",
    lifecycle: "SUPPORTED",
    lens_flags: ["COST"],
    priority: null,
    // CC-R2: a server-placed row (a priced single line with a closed episode and no Action).
    placement: {
      policy_version: "estate-placement/1",
      group: "COMPARE_VALUE",
      group_rank: 3,
      reasons: [{ code: "PRICED_SINGLE", text: "Priced cost exposure; no like line to compare with" }],
    },
    confidence: "SUPPORTED_SOURCE_COHERENT",
    confidence_reasons: ["Supported Finding", "Prepared example data source"],
    consequence: {
      state: "PRICED",
      amount: null,
      amount_low: "3.3100",
      amount_high: "3.9700",
      currency: "USD",
      source_revision_id: "c0c0c0c0-0000-4000-8000-000000000001",
    },
    action_id: null,
    action_title: null,
    action_state: null,
    application_state: null,
    resolution_state: null,
    verification_outcome: null,
    workflow_label: "Recommendation not accepted",
    next_move: null,
    source_provenance: { state: "KNOWN" },
    links: {
      site: "/sites/KOBO-001",
      finding: "/sites/KOBO-001/findings/f1f1f1f1-0000-4000-8000-000000000001?revision_id=e1e1e1e1-0000-4000-8000-000000000001",
      action: null,
    },
    ...over,
  };
}

export const COLD_ROW = row({
  site_id: SITES[1].site_id,
  site_code: "COLD-001",
  site_name: "GreenHarvest",
  domain: "COLDCHAIN",
  finding_id: "f2f2f2f2-0000-4000-8000-000000000002",
  finding_revision_id: "e2e2e2e2-0000-4000-8000-000000000002",
  title: "Temperature excursion",
  finding_label: "Temperature excursion",
  // CC-R2: the W3-03 fixture's cold excursion: RISK lens, open episode, no Action, so ACT_NOW.
  mechanism: "COLD_EXCURSION",
  lens_flags: ["RISK"],
  episode_start: "2026-10-06T19:00:00Z",
  episode_end: null,
  placement: {
    policy_version: "estate-placement/1",
    group: "ACT_NOW",
    group_rank: 2,
    reasons: [
      { code: "EPISODE_OPEN", text: "No end is recorded for this episode" },
      { code: "NO_ACTION_RECORDED", text: "No accepted Action; open the recommendation" },
    ],
  },
  confidence_reasons: ["Supported Finding", "Generated test data source"],
  consequence: { state: "UNPRICED", amount: null, amount_low: null, amount_high: null, currency: null, source_revision_id: "c2" },
  links: { site: "/sites/COLD-001", finding: null, action: null },
});

const card = (over: Partial<EstateValueCard> & Pick<EstateValueCard, "key" | "state">): EstateValueCard => ({
  display_value: null,
  currency: null,
  line_keys: [],
  group_key: null,
  basis: null,
  destination: null,
  detail: null,
  basis_text: "",
  tone: "neutral",
  ...over,
});

export const CLEAN_CARDS: EstateValueCard[] = [
  card({ key: "OPERATING_COST", state: "SITE_OWNED", line_keys: ["w1-line"], group_key: "g-w1", currency: "USD", destination: "/financials", basis_text: "Site-owned selected consequence", tone: "amber" }),
  card({ key: "SERVICE_PRODUCT_RISK", state: "UNKNOWN", display_value: "Not assessed", destination: "/findings/risks", detail: "No reviewed estate risk classification", basis_text: "Risk count unavailable" }),
  card({ key: "PRODUCTIVE_USE", state: "UNSUPPORTED", display_value: "Not established", detail: "No reviewed opportunity Finding or headroom basis", basis_text: "Demand and scenario basis unavailable" }),
  card({ key: "ASSET_LIFE", state: "UNSUPPORTED", display_value: "Not established", detail: "Capacity and life exposure are not assessed", basis_text: "No reviewed life assessment" }),
  card({ key: "VERIFIED_RECOVERY", state: "NOT_ESTABLISHED", display_value: "Not established", destination: "/financials", detail: "Verification outcome is separate from recovered value", basis_text: "Completed work does not establish savings" }),
];

const objectiveCells = (cost: "REVIEW" | "NOT_APPLICABLE" | "UNKNOWN", evidence: "FULL" | "LIMITED" | "UNKNOWN") => [
  { key: "SERVICE_PRODUCT" as const, state: "UNKNOWN" as const, label: "Unknown", reason: "No reviewed objective assessment", destination: null },
  { key: "BACKUP" as const, state: "UNKNOWN" as const, label: "Unknown", reason: "No reviewed objective assessment", destination: null },
  { key: "ASSET_CONDITION" as const, state: "UNKNOWN" as const, label: "Unknown", reason: "No reviewed objective assessment", destination: null },
  { key: "COST_CONTROL" as const, state: cost, label: cost === "REVIEW" ? "Review" : cost === "NOT_APPLICABLE" ? "N/A" : "Unknown", reason: "reason", destination: null },
  { key: "EVIDENCE" as const, state: evidence, label: evidence === "FULL" ? "Full" : evidence === "LIMITED" ? "Limited" : "Unknown", reason: "reason", destination: null },
];

export function portfolioBody(over: Partial<EstatePortfolioBody> = {}): EstatePortfolioBody {
  return {
    schema_version: "estate-portfolio-1",
    scope: { tenant_id: "t", authorized_site_count: 4, covered_site_count: 4, access_basis: "estate-access/1" },
    window: { from: "2026-10-06T00:00:00Z", to: "2026-10-07T00:00:00Z", bounds: "[from,to)", known_at: "2026-10-07T00:05:00Z" },
    status: "CURRENT",
    coverage: {
      state: "COMPLETE",
      finding_state: "COMPLETE",
      evidence_state: "COMPLETE",
      money_state: "COMPLETE",
      sites: SITES.map((s) => coverageSite(s.site_id)),
    },
    lens: "all",
    summary: {
      finding_count: 2,
      priority_site_count: null,
      opportunity_count: 0,
      evidence_gap_site_count: 1,
      accepted_action_count: 0,
      verified_resolution_count: 0,
      combined_value: null,
      combined_value_state: "NOT_COMPARABLE",
      placement_counts: { NEEDS_INVESTIGATION: 0, ACT_NOW: 1, COMPARE_VALUE: 1, UNPRICED_RISK: 0, MONITOR: 0 },
    },
    value_cards: CLEAN_CARDS,
    objectives: SITES.map((s) => ({
      site_id: s.site_id,
      site_code: s.site_code,
      site_name: s.site_name,
      domain: s.domain,
      cells: objectiveCells(s.domain === "MINIGRID" ? "REVIEW" : "NOT_APPLICABLE", s.domain === "COLDCHAIN" ? "LIMITED" : "FULL"),
    })),
    evidence_prompt: {
      state: "AVAILABLE",
      text: "Restore the battery report at Kobo to address the selected evidence gap.",
      site_id: SITES[0].site_id,
      site_code: "KOBO-001",
      gap_code: "MISSING_REPORT",
      destination: "/evidence",
    },
    opportunity: { state: "UNSUPPORTED", finding_id: null, scenario_amount: null, headroom: null, destination: null },
    progress: {
      state: "NO_COMPARABLE_BASELINE",
      completed_activity_count: null,
      pending_trial_count: 0,
      verified_resolution_count: 0,
      recovered_value: null,
      rows: [],
    },
    footer: {
      line_key: "ev-line-1",
      site_name: "Depot",
      quantity_display: null,
      amount_display: null,
      source_provenance: {
        classification: "SITE_RECORD",
        state: "KNOWN",
        source_ids: ["src-ev-1"],
        evidence_ids: [],
        basis_sha256: "ab12cd34",
        reasons: [{ code: "WINDOW_SELECTED", accepted_evidence_ids: [] }],
      },
      window_start: "2026-10-06T08:00:00Z",
      window_end: "2026-10-06T16:00:00Z",
      destination: "/sites/EV-LAB-001/ev/evidence",
    },
    selected_lines: [
      { line_key: "w1-line", domain: "mini_grid", site_id: SITES[0].site_id, site_code: "KOBO-001", site_name: "Kobo", category: "CANDIDATE_OPERATING_COST_EXPOSURE", window_start: "2026-10-06T14:20:00Z", window_end: "2026-10-06T15:20:00Z", quantity: { low: "1.5", high: "1.8", unit: "L" }, amount: { low: "3.3100", high: "3.9700", currency: "USD" }, eligibility: "ELIGIBLE", group_key: "g-w1" },
      { line_key: "ev-line-1", domain: "ev_charging", site_id: SITES[2].site_id, site_code: "EV-LAB-001", site_name: "Depot", category: "GROSS_TARIFF_SCENARIO", window_start: "2026-10-06T08:00:00Z", window_end: "2026-10-06T16:00:00Z", quantity: { low: "120", high: "120", unit: "kWh" }, amount: { low: "36.005", high: "36.005", currency: "USD" }, eligibility: "ELIGIBLE", group_key: "g-ev" },
    ],
    money: {
      groups: [
        { group_key: "g-w1", category: "CANDIDATE_OPERATING_COST_EXPOSURE", currency: "USD", window_start: "2026-10-06T14:20:00Z", window_end: "2026-10-06T15:20:00Z", state: "SINGLE_LINE", line_keys: ["w1-line"], amount: null, reason_codes: [] },
      ],
      exclusions: [],
      diagnostics: [],
      estate_total: null,
    },
    scope_disclosure: {
      sites: SITES.map((s) => ({
        site_id: s.site_id,
        site_code: s.site_code,
        site_name: s.site_name,
        domain: s.domain,
        window: { from: "2026-10-06T00:00:00Z", to: "2026-10-07T00:00:00Z" },
        coverage: coverageSite(s.site_id),
        selected_revision_ids: ["e1e1e1e1-0000-4000-8000-000000000001"],
        source_provenance: { state: "KNOWN" },
      })),
      exclusions: [],
    },
    order: "episode_start desc nulls last",
    total_count: 2,
    next_cursor: null,
    selection_token: `sha256:${"a".repeat(64)}`,
    rows: [COLD_ROW, row()],
    ...over,
  };
}

/** One typed body per Portfolio status (r0a L3: all five values). */
export const STATUS_BODIES: Record<EstatePortfolioStatus, EstatePortfolioBody> = {
  CURRENT: portfolioBody(),
  HISTORICAL: portfolioBody({ status: "HISTORICAL", window: { from: "2026-10-06T00:00:00Z", to: "2026-10-07T00:00:00Z", bounds: "[from,to)", known_at: "2026-09-30T00:00:00Z" } }),
  PENDING: portfolioBody({ status: "PENDING", coverage: { ...portfolioBody().coverage, state: "PARTIAL", money_state: "PARTIAL", sites: SITES.map((s, i) => coverageSite(s.site_id, i === 1 ? "PENDING_RECOMPUTE" : "CURRENT")) } }),
  UNKNOWN: portfolioBody({ status: "UNKNOWN", coverage: { ...portfolioBody().coverage, state: "PARTIAL", finding_state: "PARTIAL", sites: SITES.map((s, i) => coverageSite(s.site_id, i === 3 ? "UNKNOWN" : "CURRENT")) } }),
  EMPTY_SCOPE: portfolioBody({
    status: "EMPTY_SCOPE",
    scope: { tenant_id: "t", authorized_site_count: 0, covered_site_count: 0, access_basis: "estate-access/1" },
    coverage: { state: "EMPTY", finding_state: "EMPTY", evidence_state: "EMPTY", money_state: "EMPTY", sites: [] },
    objectives: [],
    rows: [],
    total_count: 0,
    selected_lines: [],
    footer: null,
    scope_disclosure: { sites: [], exclusions: [] },
  }),
};

export function loadedPortfolio(body: EstatePortfolioBody): EstateResult<EstatePortfolioBody> {
  return { status: "loaded", value: body };
}

export function refused(httpStatus: number, code: string, copy: string): EstateResult<EstatePortfolioBody> {
  return { status: "refused", httpStatus, code, copy };
}

/** A fake client whose Portfolio reads answer in order (the last answer repeats). */
export function portfolioClient(...answers: EstateResult<EstatePortfolioBody>[]): EstateClient & { calls: EstatePortfolioQuery[] } {
  const calls: EstatePortfolioQuery[] = [];
  return {
    calls,
    findings: () => Promise.reject(new Error("Portfolio does not read Findings")),
    actions: () => Promise.reject(new Error("Portfolio does not read Actions")),
    scope: () => Promise.reject(new Error("Portfolio does not read scope")),
    portfolio: (query) => {
      calls.push(query);
      return Promise.resolve(answers[Math.min(calls.length - 1, answers.length - 1)]);
    },
  };
}

/**
 * OUT-B B6: a `estate-outcome-summary-1` body for the four fixture Sites (backend-shaped texts; no outcome codes on
 * screen). Kobo's Grow row carries the B-Q27 `short_value`; Harbour's board read failed (four UNKNOWN rows).
 */
const SUMMARY_CATEGORIES = [
  { category: "GROW_REVENUE", label: "Grow revenue", definition: "Capture more income from energy and assets" },
  { category: "OPTIMIZE_COST", label: "Optimize cost", definition: "Spend less to deliver the same service" },
  { category: "PROTECT_ASSET", label: "Protect assets", definition: "Keep equipment and service safe" },
  { category: "ASSURE_PERFORMANCE", label: "Assure performance", definition: "Show that changes worked" },
] as const;

function summaryRow(
  category: EstateOutcomeSummaryRow["category"],
  state: EstateOutcomeSummaryRow["state"],
  state_label: string,
  tone: EstateOutcomeSummaryRow["tone"],
  lead: string | null,
  short_value: string | null = null,
): EstateOutcomeSummaryRow {
  return { category, state, state_label, tone, lead_outcome: lead === null ? null : { key: "X-1", label: lead }, headline: null, short_value };
}

/** OUT-W: mini reads its day, a cold Site its latest event (the link opens it), an EV Site with no event the period. */
export const COLD_EVENT_HREF = "/sites/COLD-001?from=2026-10-06T14%3A00%3A00Z&to=2026-10-06T15%3A00%3A00Z";

const SUMMARY_HREF: Record<string, string> = {
  "KOBO-001": "/sites/KOBO-001",
  "COLD-001": COLD_EVENT_HREF,
  "EV-LAB-001": "/sites/EV-LAB-001/ev",
  "EV-LAB-002": "/sites/EV-LAB-002/ev",
};

const SUMMARY_WINDOW: Record<string, Pick<EstateOutcomeSummaryBody["sites"][number], "window" | "window_basis">> = {
  "KOBO-001": { window: { from: "2026-10-06T00:00:00Z", to: "2026-10-07T00:00:00Z", known_at: null }, window_basis: "DAY" },
  "COLD-001": { window: { from: "2026-10-06T14:00:00Z", to: "2026-10-06T15:00:00Z", known_at: "2026-10-07T00:00:00Z" }, window_basis: "LATEST_EVENT" },
  "EV-LAB-001": { window: { from: "2026-10-06T00:00:00Z", to: "2026-10-07T00:00:00Z", known_at: "2026-10-07T00:00:00Z" }, window_basis: "PERIOD" },
  "EV-LAB-002": { window: null, window_basis: null },
};

export function outcomeSummaryBody(over: Partial<EstateOutcomeSummaryBody> = {}): EstateOutcomeSummaryBody {
  const rows: Record<string, EstateOutcomeSummaryRow[]> = {
    "KOBO-001": [
      summaryRow("GROW_REVENUE", "OPPORTUNITY", "Opportunity", "green", "Unused solar", "18–20 kW unused"),
      summaryRow("OPTIMIZE_COST", "NEEDS_ATTENTION", "Needs attention", "amber", "Generator fuel"),
      summaryRow("PROTECT_ASSET", "NO_OBJECTIVE", "No objective declared", "gray", "Battery life"),
      summaryRow("ASSURE_PERFORMANCE", "WATCH", "Watch", "blue", "Evidence coverage"),
    ],
    "COLD-001": [
      summaryRow("GROW_REVENUE", "NOT_MEASURED", "Not measured yet", "none", "Product sales"),
      summaryRow("OPTIMIZE_COST", "NOT_MEASURED", "Not measured yet", "none", "Repair spend"),
      summaryRow("PROTECT_ASSET", "NEEDS_ATTENTION", "Needs attention", "amber", "Product kept cold"),
      summaryRow("ASSURE_PERFORMANCE", "ON_TRACK", "On track", "green", "Evidence coverage"),
    ],
    "EV-LAB-001": [
      summaryRow("GROW_REVENUE", "WATCH", "Watch", "blue", "Charger use"),
      summaryRow("OPTIMIZE_COST", "NOT_MEASURED", "Not measured yet", "none", "Energy cost"),
      summaryRow("PROTECT_ASSET", "NEEDS_ATTENTION", "Needs attention", "amber", "Charging service"),
      summaryRow("ASSURE_PERFORMANCE", "WATCH", "Watch", "blue", "Evidence coverage"),
    ],
    "EV-LAB-002": SUMMARY_CATEGORIES.map((c) => summaryRow(c.category, "UNKNOWN", "Unknown", "gray", null)),
  };
  return {
    schema_version: "estate-outcome-summary-1",
    policy_versions: { catalogue: "outcome-catalogue/2" },
    window: { from: "2026-10-06T00:00:00Z", to: "2026-10-07T00:00:00Z" },
    sites: SITES.map((s) => ({
      site_id: s.site_id,
      site_code: s.site_code,
      site_name: s.site_name,
      domain: s.domain,
      overview_href: SUMMARY_HREF[s.site_code],
      read_state: s.site_code === "EV-LAB-002" ? "UNAVAILABLE" : "AVAILABLE",
      rows: rows[s.site_code],
      ...SUMMARY_WINDOW[s.site_code],
    })),
    categories: SUMMARY_CATEGORIES.map((c) => ({ ...c, icon: c.category, sites_needing_attention: 0, warning_count: 0 })),
    warnings: [],
    ...over,
  };
}

/** A portfolio fake that also answers the outcome summary read, recording its windows. */
export function withOutcomeSummary<C extends EstateClient>(
  client: C,
  answer: EstateResult<EstateOutcomeSummaryBody> = { status: "loaded", value: outcomeSummaryBody() },
): C & { summaryCalls: Pick<EstateQuery, "from" | "to" | "known_at">[] } {
  const summaryCalls: Pick<EstateQuery, "from" | "to" | "known_at">[] = [];
  return Object.assign(client, {
    summaryCalls,
    getOutcomeSummary: (query: Pick<EstateQuery, "from" | "to" | "known_at">) => {
      summaryCalls.push(query);
      return Promise.resolve(answer);
    },
  });
}
