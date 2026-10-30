import type {
  OutcomeBoardBody,
  OutcomeBoardClient,
  OutcomeBoardQuery,
  OutcomeBoardRead,
  OutcomeBoardRow,
} from "../sites/outcomeBoardClient";

/** OUT-B B5 test fixture: a §B.1 board body with every column shape (backend-shaped texts, no outcome codes). */
function row(over: Partial<OutcomeBoardRow> & Pick<OutcomeBoardRow, "category" | "label" | "state" | "state_label" | "tone">): OutcomeBoardRow {
  return {
    definition: `${over.label} definition`,
    icon: "grow",
    lead_outcome: { key: "X-1", label: "Lead outcome" },
    headline: null,
    headline_money: null,
    subline: null,
    not_measured_text: null,
    counts: { issues: 0, in_hand: 0 },
    must_not_harm: null,
    contributors: [],
    issues: [],
    options: [],
    in_hand: [],
    earlier: [],
    earlier_empty_text: null,
    evidence_link: null,
    outcomes: [],
    ...over,
  };
}

export function boardRows(): OutcomeBoardRow[] {
  return [
    row({
      category: "GROW_REVENUE",
      label: "Grow revenue",
      definition: "Capture more value from existing infrastructure and expand earning potential",
      state: "OPPORTUNITY",
      state_label: "Opportunity",
      tone: "green",
      lead_outcome: { key: "MG-1", label: "Productive sales" },
      headline: "18–20 kW of daytime solar unused",
      subline: "Sales to productive users are not metered",
      counts: { issues: 1, in_hand: 0 },
      contributors: [
        { key: "headroom", label: "Daytime solar headroom", text: "18–20 kW unused at noon", confidence: { label: "Limited", tone: "amber" }, href: null },
      ],
      issues: [{ kind: "OPPORTUNITY", role: "MOVES", text: "Productive use headroom", href: "/sites/KOBO-001/findings/f-1", ref: null }],
      earlier_empty_text: "Not available yet · no completed work or checked change for this outcome",
      evidence_link: { label: "Renewable evidence", href: "/sites/KOBO-001/performance/renewable" },
    }),
    row({
      category: "OPTIMIZE_COST",
      label: "Optimize cost and efficiency",
      definition: "Eliminate avoidable expenditure and get more output from operational resources",
      icon: "cost",
      state: "NEEDS_ATTENTION",
      state_label: "Needs attention",
      tone: "amber",
      lead_outcome: { key: "MG-2", label: "Supply cost per kWh" },
      headline: "exposure in this hour",
      headline_money: { amount_low: "12.40", amount_high: "18.75", currency: "USD" },
      subline: "Generator ran longer than needed",
      counts: { issues: 2, in_hand: 1 },
      must_not_harm: {
        text: "Reliable service and battery and generator life are checked as safeguards when the trial is verified",
        href: "/sites/KOBO-001/actions/a-1/verification?event_id=e-1",
      },
      contributors: [
        { key: "generator_use", label: "Generator use", text: "30 minutes longer than needed", confidence: { label: "Low", tone: "amber" }, href: "/sites/KOBO-001/performance/dispatch" },
      ],
      issues: [
        { kind: "FINDING", role: "MOVES", text: "Generator support review", href: "/sites/KOBO-001/findings/f-2", ref: null },
        { kind: "EVIDENCE_GAP", role: "MOVES", text: "Battery output not reported limits this conclusion", href: null, ref: null },
      ],
      options: [{ text: "Generator stop trial", href: "/sites/KOBO-001/findings/f-2/recommendation" }],
      in_hand: [{ text: "Trial action · Plan ready", href: "/sites/KOBO-001/actions/a-1", state_label: "Plan ready" }],
      earlier: [{ text: "Generator inspection", href: "/maintenance/requests/c-1", result_label: "Did not fix it" }],
      earlier_empty_text: null,
      evidence_link: { label: "Dispatch evidence", href: "/sites/KOBO-001/performance/dispatch" },
    }),
    row({
      category: "PROTECT_ASSET",
      label: "Protect asset and capital",
      definition: "Preserve asset value, avoid premature replacement and reduce service disruption",
      icon: "protect",
      state: "WATCH",
      state_label: "Watch",
      tone: "blue",
      lead_outcome: { key: "MG-3", label: "Reliable service" },
      headline: "No unserved energy recorded",
      earlier_empty_text: "No earlier work has been checked for this",
      evidence_link: { label: "Service evidence", href: "/sites/KOBO-001/performance/service" },
    }),
    row({
      category: "ASSURE_PERFORMANCE",
      label: "Assure performance and returns",
      definition: "Establish with defensible evidence whether the infrastructure is delivering expected results",
      icon: "assure",
      state: "NOT_MEASURED",
      state_label: "Not measured yet",
      tone: "none",
      not_measured_text: "Targets are not declared for this site",
    }),
  ];
}

export function boardBody(over: Partial<OutcomeBoardBody> = {}): OutcomeBoardBody {
  return {
    schema_version: "site-outcome-board-1",
    policy_versions: { catalogue: "outcome-catalogue/1", outcome_map: "outcome-map/1", status: "outcome-status/1", warnings: null },
    site_code: "KOBO-001",
    site_id: "site-1",
    site_name: "Kobo Mini-grid",
    domain: "mini_grid",
    window: { from: "2026-10-06T00:00:00Z", to: "2026-10-07T00:00:00Z", known_at: null },
    read_state: "AVAILABLE",
    rows: boardRows(),
    warnings: [],
    links: { self: "/api/sites/KOBO-001/outcome-board?date=2026-10-06" },
    ...over,
  };
}

/** A fake board client recording its calls; `read` answers every call. */
export function fakeOutcomeBoard(read: OutcomeBoardRead | ((siteCode: string) => OutcomeBoardRead) = { status: "loaded", value: boardBody() }) {
  const calls: { siteCode: string; query: OutcomeBoardQuery }[] = [];
  const client: OutcomeBoardClient = {
    getOutcomeBoard: (siteCode, query) => {
      calls.push({ siteCode, query });
      return Promise.resolve(typeof read === "function" ? read(siteCode) : read);
    },
  };
  return { client, calls };
}
