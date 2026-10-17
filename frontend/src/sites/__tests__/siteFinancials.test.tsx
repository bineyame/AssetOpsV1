import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { SiteFinancialsFrame } from "../../shell/SiteAnalyticsFrames";
import { expectV69Panels, panelTitled } from "../../test/panelStructure";
import { settledScreen } from "../../test/settled";
import { describeViolations, scanDisclosureVocabulary, scanProductVocabulary } from "../../test/productVocabulary";
import { expectStateLineVisible, visibleOutsideClosedDisclosure } from "../../test/productPresentation";
import {
  createFinancialsClient,
  type AssumptionRevisionBody,
  type AssumptionSeriesBody,
  type FinancialReadResult,
  type ConsequenceHistoryBody,
  type ConsequenceHistoryResult,
  type ConsequenceHistoryRow,
  type ConsequencePin,
  type HistoryQuery,
  type ConsequenceRevision,
  type FinancialsClient,
  type FindingConsequence,
  type FindingConsequencesBody,
  type FindingFinancialsBody,
  type PriceRevision,
  type SeriesQuery,
} from "../financialsClient";
import type { SiteDetailClient } from "../siteDirectoryClient";
import type { SourceProvenance } from "../sourceProvenance";

const V1 = "11111111-1111-4111-8111-111111111111";
const V3 = "33333333-3333-4333-8333-333333333333";
const FINDING = "f0000000-0000-4000-8000-000000000001";
const FREV = "e0000000-0000-4000-8000-000000000002";

function price(no: number, id: string, value: string, patch: Partial<PriceRevision> = {}): PriceRevision {
  return {
    revision_id: id,
    revision_no: no,
    prior_revision_id: null,
    assumption_key: "diesel_price_per_litre",
    value,
    currency: "USD",
    unit: "currency/L",
    basis: "AUTHORED_ESTIMATE",
    source_reference: "Illustrative estimate for this site",
    authored_valid: { from: "2026-01-01T00:00:00+00:00", to: null, bounds: "[)" },
    recorded_at: "2026-10-13T09:00:00+00:00",
    change_kind: "INITIAL",
    correction_reason: null,
    actor: { kind: "SYSTEM", id: "service:assetops-assumption-publisher", author_id: null },
    channel: "SYSTEM_FIXTURE",
    authorization_basis: "SERVER_ADMINISTRATIVE_TRIGGER: published by the server-side publisher",
    provenance: {},
    idempotency_key: "demo-diesel-price-v1",
    request_sha256: "a".repeat(64),
    ...patch,
  };
}

const P1 = price(1, V1, "1.25");
const P3 = price(3, V3, "1.19", {
  change_kind: "CORRECTION",
  correction_reason: "June estimate replaced",
  authored_valid: { from: "2026-06-01T00:00:00+00:00", to: "2026-07-01T00:00:00+00:00", bounds: "[)" },
});

function series(patch: Partial<AssumptionSeriesBody> = {}): AssumptionSeriesBody {
  const assignment = {
    assignment_id: "a1",
    revision_id: V1,
    publication_revision_id: V1,
    valid: { from: "2026-07-01T00:00:00+00:00", to: null, bounds: "[)" as const },
    recorded: { from: "2026-10-13T09:00:00+00:00", to: null, bounds: "[)" as const },
  };
  return {
    site_code: "KOBO-001",
    access_basis: "x",
    assumption_key: "diesel_price_per_litre",
    unit: "currency/L",
    state: "PUBLISHED",
    cutoff: { recorded_at: null, selected_by: "CURRENT", basis: "x" },
    selection: { state: "PRICED", valid_at: "2026-10-13T00:00:00Z", price: P1, ...assignment },
    timeline: [
      { ...assignment, assignment_id: "a0", valid: { from: "2026-01-01T00:00:00+00:00", to: "2026-06-01T00:00:00+00:00", bounds: "[)" }, price: P1 },
      { ...assignment, assignment_id: "a3", revision_id: V3, valid: { from: "2026-06-01T00:00:00+00:00", to: "2026-07-01T00:00:00+00:00", bounds: "[)" }, price: P3 },
      { ...assignment, price: P1 },
    ],
    revisions: [P1, P3],
    revision_page: { after_revision_no: 0, limit: 200, total: 2, next_after_revision_no: null },
    ...patch,
  };
}

function bridgeBody(state: "QUANTITY_UNAVAILABLE" | "UNPRICED" = "QUANTITY_UNAVAILABLE"): FindingFinancialsBody {
  return {
    site_code: "KOBO-001",
    audit_only: null,
    finding: { id: FINDING },
    selection: { revision_id: FREV, revision_no: 2, is_latest: true, selected_by: "EXACT_REVISION_ID" },
    revision: { id: FREV, revision_no: 2, title: "Generator on while solar could carry the site", lifecycle: "SUPPORTED", claim_level: "SUPPORTED" },
    window: { start: "2026-10-06T08:00:00+00:00", end: "2026-10-06T09:30:00+00:00" },
    consequence: {
      state,
      currentness: "CURRENT",
      quantity_source: "fuel-cost-1",
      quantity: null,
      amount: null,
      currency: null,
      price_revision_id: null,
      consequence_revision_id: null,
      quantity_reason: state === "QUANTITY_UNAVAILABLE" ? "POWER_MISSING" : null,
      price_reason: state === "UNPRICED" ? "NO_PRICE" : null,
      reason: "No fuel quantity has been calculated for this finding yet, so no diesel price is applied and no cost is shown.",
    },
  };
}

const C1 = "c1000000-0000-4000-8000-000000000001";
const C2 = "c2000000-0000-4000-8000-000000000002";
const V4 = "44444444-4444-4444-8444-444444444444";

function crev(no: number, id: string, patch: Partial<ConsequenceRevision> = {}): ConsequenceRevision {
  const priced = { value: no === 1 ? "1.25" : "1.28", high: no === 1 ? "15.8125" : "16.192", shown: no === 1 ? "15.82" : "16.20" };
  return {
    id,
    revision_no: no,
    prior_consequence_revision_id: no === 1 ? null : C1,
    finding_id: FINDING,
    finding_revision_id: FREV,
    consequence_type: "POTENTIAL_FUEL_COST",
    basis_kind: "MODELLED_CONDITIONAL",
    state: "PRICED",
    window: { start: "2026-10-23T06:05:00+00:00", end: "2026-10-23T08:00:00+00:00", bounds: "[start, end)" },
    overlap_group: "g",
    recorded_at: no === 1 ? "2026-10-14T09:00:00+00:00" : "2026-10-14T10:00:00+00:00",
    actor_id: "service:assetops-consequence-recompute",
    model: {
      model_id: "fuel-cost-1",
      formula_version: "fuel-cost-1",
      parameter_version: "fuel-cost-1-sfc-upper-1",
      parameter_sha256: "1".repeat(64),
      sfc_upper_multiplier: "1.10",
      parameter_is_reviewed: true,
    },
    quantity: { state: "AVAILABLE", reason: null, detail: null, unit: "L", low: "0", high: "12.65", high_exact: null, high_display: "12.65" },
    price: { state: "PRICED", reason: null, revision_id: no === 1 ? V1 : V4, value: priced.value, currency: "USD", unit: "currency/L", considered: [] },
    amount: { low: "0", high: priced.high, currency: "USD", unrounded: true },
    display: { state: "ROUNDED_OUTWARD", currency: "USD", amount_low: "0.00", amount_high: priced.shown },
    limitations: ["Necessary and Indeterminate time is never priced."],
    digests: { technical_input_sha256: "t".repeat(64), consequence_basis_sha256: String(no).repeat(64) },
    lineage: {
      assessments: [{ assessment_revision_id: "a-1", analytic_run_id: "r-1", is_primary: true }],
      assumptions: [{ assumption_revision_id: no === 1 ? V1 : V4, assignment_id: "as-1", role: "PRICE" }],
      power_intervals: [
        {
          evidence_id: "ev-1",
          interval_start: "2026-10-23T06:05:00+00:00",
          interval_end: "2026-10-23T06:10:00+00:00",
          mean_kw: "20",
          duration_seconds: 300,
          sfc_l_per_kwh: "0.3",
          foundation_revision_id: "fr-1",
          binding_revision_id: "br-1",
          envelope_sha256: "e".repeat(64),
          covered_spans: [],
          containment: "CONTAINED",
        },
      ],
      evidence_ids: ["ev-1"],
    },
    ...patch,
  };
}

function consequencesBody(
  revisions: ConsequenceRevision[],
  opts: { state?: FindingConsequencesBody["currentness"]["state"]; selected?: string | null } = {},
): FindingConsequencesBody {
  const head = revisions.length ? revisions[revisions.length - 1] : null;
  const selectedId = opts.selected ?? head?.id ?? null;
  const selected = revisions.find((r) => r.id === selectedId) ?? null;
  const state = opts.state ?? "CURRENT";
  return {
    site_code: "KOBO-001",
    audit_only: null,
    finding: { id: FINDING },
    selection: { revision_id: FREV, revision_no: 2, is_latest: true },
    window: { start: "2026-10-23T06:05:00+00:00", end: "2026-10-23T08:00:00+00:00" },
    consequence_selection: {
      selected_by: opts.selected ? "EXACT_CONSEQUENCE_REVISION_ID" : "HEAD",
      consequence_revision_id: selectedId,
      head_consequence_revision_id: head?.id ?? null,
      finding_revision_id: FREV,
      finding_revision_is_latest: true,
    },
    currentness: { state, reasons: [], pending_work: [], current_amount_shown: state === "CURRENT", derived_now: null },
    consequence: selected
      ? { ...selected, is_head: selected.id === head?.id, presented_as_current: selected.id === head?.id && state === "CURRENT" }
      : null,
    history: { revisions, total: revisions.length, page: { after_revision_no: 0, limit: 50, next_after_revision_no: null } },
    exclusions: ["No total across Findings is computed."],
    links: { evidence_records: { "ev-1": "/api/sites/KOBO-001/evidence/records/ev-1" }, price_revisions: {} },
  };
}

/** S4-05b: a stored authored-demonstration provenance block (one publication, one fixture version). */
function authoredSource(consequenceRevisionId: string | null = null): SourceProvenance {
  return {
    tenant_id: "t1",
    site_id: "s1",
    finding_revision_id: FREV,
    consequence_revision_id: consequenceRevisionId,
    cited_accepted_evidence_ids: ["ev-1"],
    power_accepted_evidence_ids: consequenceRevisionId ? ["ev-2"] : null,
    state: "AUTHORED_DEMONSTRATION",
    reasons: [],
    accepted_evidence_ids: consequenceRevisionId ? ["ev-1", "ev-2"] : ["ev-1"],
    problematic_accepted_evidence_ids: [],
    publication_ids: ["pub-1"],
    source_classes: ["AUTHORED_DEMONSTRATION"],
    fixtures: [{ fixture_id: "assetops.s4-power-demo-cases", fixture_version: "1" }],
    runs: [],
    evidence: [],
  };
}

function pricedBridge(patch: Partial<FindingConsequence> = {}): FindingFinancialsBody {
  const base = bridgeBody();
  return {
    ...base,
    window: { start: "2026-10-23T06:05:00+00:00", end: "2026-10-23T08:00:00+00:00" },
    source_provenance: { finding_revision: authoredSource(), consequence_revision: authoredSource(C2) },
    consequence: {
      ...base.consequence,
      state: "PRICED",
      currentness: "CURRENT",
      quantity: { low: "0", high: "12.65", unit: "L" },
      amount: { low: "0.00", high: "16.20" },
      currency: "USD",
      price_revision_id: V4,
      consequence_revision_id: C2,
      quantity_reason: null,
      price_reason: null,
      reason: "Modelled potential fuel-cost exposure under the reviewed fuel-cost-1 assumptions.",
      ...patch,
    },
  };
}

interface Asked {
  series: SeriesQuery[];
  exact: string[];
  bridge: (string | null)[];
  consequences: ConsequencePin[];
  history: HistoryQuery[];
}

/** S4-08: the server-fixed default cutoff, with sub-millisecond digits a `Date` round trip would lose. */
const CUT = "2026-10-16T09:30:00.123456+00:00";

function historyBody(rows: ConsequenceHistoryRow[] = [], patch: Partial<ConsequenceHistoryBody> = {}): ConsequenceHistoryBody {
  return {
    site_code: "KOBO-001",
    cutoff: { recorded_at: CUT, selected_by: "SERVER_DEFAULT", clock: "DATABASE", membership: "x" },
    current_amount_shown: false,
    source_gate: { open: true, reason: null },
    classification: "x",
    rows,
    next_cursor: null,
    page: { limit: 25, shown: rows.length, is_first: true },
    zero_statement: rows.length ? null : "x",
    exclusions: [],
    ...patch,
  };
}

function fake(opts: {
  series?: FinancialReadResult<AssumptionSeriesBody>;
  exact?: FinancialReadResult<AssumptionRevisionBody>;
  bridge?: FinancialReadResult<FindingFinancialsBody>;
  consequences?: FinancialReadResult<FindingConsequencesBody> | ((pin: ConsequencePin) => FinancialReadResult<FindingConsequencesBody>);
  seriesFor?: (query: SeriesQuery) => FinancialReadResult<AssumptionSeriesBody>;
  history?: ConsequenceHistoryResult | ((query: HistoryQuery) => ConsequenceHistoryResult);
} = {}): FinancialsClient & { asked: Asked } {
  const asked: Asked = { series: [], exact: [], bridge: [], consequences: [], history: [] };
  return {
    asked,
    async getAssumptions(_site, query) {
      asked.series.push(query);
      if (opts.seriesFor) return opts.seriesFor(query);
      return opts.series ?? { status: "loaded", value: series() };
    },
    async getAssumptionRevision(_site, id) {
      asked.exact.push(id);
      return (
        opts.exact ?? {
          status: "loaded",
          value: {
            site_code: "KOBO-001",
            selection: { revision_id: id, selected_by: "EXACT_REVISION_ID" },
            revision: P1,
            assignments: [],
            recorded_by_this_publication: [],
          },
        }
      );
    },
    async getFindingFinancials(_site, _finding, rev) {
      asked.bridge.push(rev);
      return opts.bridge ?? { status: "loaded", value: bridgeBody() };
    },
    async getConsequenceHistory(_site, query) {
      asked.history.push(query);
      const h = opts.history;
      if (typeof h === "function") return h(query);
      return h ?? { status: "loaded", value: historyBody([], query.recordedAt ? { cutoff: { recorded_at: query.recordedAt, selected_by: "RECORDED_CUTOFF", clock: "DATABASE", membership: "x" } } : {}) };
    },
    async getFindingConsequences(_site, _finding, pin) {
      asked.consequences.push(pin);
      const c = opts.consequences;
      if (typeof c === "function") return c(pin);
      return c ?? { status: "loaded", value: consequencesBody([]) };
    },
  };
}

const detail: SiteDetailClient = {
  async getSite() {
    return { status: "loaded", site: { site_id: "KOBO-001", display_name: "Kobo" } } as never;
  },
} as unknown as SiteDetailClient;

function Where() {
  const location = useLocation();
  return <output data-testid="where">{location.pathname + location.search}</output>;
}

function mount(client: FinancialsClient, path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route
          path="/sites/:siteId/financials"
          element={<><SiteFinancialsFrame detail={detail} sitesPath="/sites" view="overview" financials={client} /><Where /></>}
        />
        <Route
          path="/sites/:siteId/financials/assumptions"
          element={<><SiteFinancialsFrame detail={detail} sitesPath="/sites" view="assumptions" financials={client} /><Where /></>}
        />
      </Routes>
    </MemoryRouter>,
  );
}

describe("Site > Financials > Assumptions", () => {
  it("reads the current price in plain words, with identifiers only in the closed record details", async () => {
    const client = fake();
    const { container } = mount(client, "/sites/KOBO-001/financials/assumptions");
    await settledScreen();
    // W1-F3: the price lives in the v69 panel "Financial assumptions" (was the "Site diesel price" answer card).
    expectV69Panels("assumptions");
    const panel = panelTitled("Financial assumptions");
    expect(panel).toHaveTextContent(/Diesel price, set by the system on 13 Oct 2026: 1\.25 USD per litre, from 1 Jul 2026, with no end date\./);
    expect(panel.querySelector("[data-price-selection='PRICED']")).toHaveAttribute("data-price-selected-revision", V1);
    // The ID is rendered only inside a closed disclosure.
    const id = within(panel).getAllByText(V1)[0];
    expect(id.closest("details")).not.toHaveAttribute("open");
    // S4-08 (review L-R2, deliberate change): the default view no longer reads the current price list. It reads the
    // fuel cost history first and passes that read's exact cutoff string to the price read (was `recordedAt: null`).
    expect(client.asked.history[0]).toEqual({ recordedAt: null, after: null });
    expect(client.asked.series[0]).toMatchObject({ recordedAt: CUT, afterRevisionNo: 0 });
    const { violations, scanned } = scanProductVocabulary(container, "assumptions");
    expect(scanned).toBeGreaterThan(10);
    expect(violations, describeViolations(violations)).toEqual([]);
  });

  it("shows the human edit disabled, with its reason as a catalogued gap", async () => {
    mount(fake(), "/sites/KOBO-001/financials/assumptions");
    await settledScreen();
    const button = screen.getByRole("button", { name: "Edit price" });
    expect(button).toBeDisabled();
    const reason = document.getElementById(button.getAttribute("aria-describedby") ?? "");
    const claim = reason?.querySelector("[data-gap-id]");
    expect(claim).toHaveAttribute("data-gap-id", "G-assumptions-human-edit");
    expect(claim).toHaveAttribute("data-gap-placement", "assumptions.price.human-edit");
    expect(claim).toHaveTextContent(/signed-in operator/);
  });

  it("lists the schedule with the corrected middle and both unaffected slices, and the history", async () => {
    mount(fake(), "/sites/KOBO-001/financials/assumptions");
    await settledScreen();
    const rows = within(screen.getByRole("table", { name: "Price schedule" })).getAllByRole("row").slice(1);
    expect(rows.map((r) => r.getAttribute("data-price-revision"))).toEqual([V1, V3, V1]);
    expect(rows[1]).toHaveTextContent("from 1 Jun 2026 until 1 Jul 2026");
    expect(rows[1]).toHaveTextContent("Correction");
    expect(rows[2]).toHaveAttribute("aria-current", "true");
    const history = screen.getByRole("region", { name: "Price history" });
    expect(within(history).getByRole("link", { name: "Open version 3" })).toHaveAttribute(
      "href",
      `/sites/KOBO-001/financials/assumptions?revision_id=${V3}`,
    );
    expect(within(history).getAllByRole("link", { name: "Prices as recorded then" })[0]).toHaveAttribute(
      "href",
      `/sites/KOBO-001/financials/assumptions?recorded_at=${encodeURIComponent(P1.recorded_at)}`,
    );
  });

  it("opens an exact version from the address and keeps it on reload", async () => {
    const client = fake();
    mount(client, `/sites/KOBO-001/financials/assumptions?revision_id=${V1}`);
    await settledScreen();
    expect(client.asked.exact).toEqual([V1]);
    // W1-F3 review M5: the "Selected: ... 1.25 USD per litre" eyebrow is gone; the version's own fields carry the price.
    const version = screen.getByRole("region", { name: "Price version 1" });
    expect(within(version).getByDisplayValue("1.25")).toBeInTheDocument();
    expect(version).toHaveTextContent("Diesel price · USD per litre");
    expect(version).toHaveTextContent("Version 1");
    expect(panelTitled("Financial assumptions").querySelector("[data-price-back-link]")).toHaveTextContent("Back to the current prices");
  });

  it("never substitutes the latest price for an unknown or foreign version", async () => {
    const client = fake({ exact: { status: "not_found", message: "No such price revision for this Site" } });
    mount(client, "/sites/KOBO-001/financials/assumptions?revision_id=nope");
    await settledScreen();
    // W1-F3: the refused exact version is an in-panel state inside "Financial assumptions" (was its own panel).
    expectV69Panels("assumptions");
    expect(panelTitled("Financial assumptions").querySelector("[data-price-exact-refused='not_found']")).toHaveTextContent(
      "No such price version.",
    );
    expect(screen.queryByRole("region", { name: /^Price version/ })).toBeNull();
  });

  it("reads the price list at a recorded cutoff and says so", async () => {
    const at = "2026-10-13T09:00:00+00:00";
    const client = fake({ series: { status: "loaded", value: series({ cutoff: { recorded_at: at, selected_by: "RECORDED_CUTOFF", basis: "x" } }) } });
    mount(client, `/sites/KOBO-001/financials/assumptions?recorded_at=${encodeURIComponent(at)}`);
    await settledScreen();
    expect(client.asked.series[0].recordedAt).toBe(at);
    expect(screen.getByText(/Showing the prices as they were recorded on 2026-10-13 09:00 UTC/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("link", { name: "Show the current prices" }));
    await settledScreen();
    expect(screen.getByTestId("where")).toHaveTextContent(/^\/sites\/KOBO-001\/financials\/assumptions$/);
  });

  it("states no price without a default, and store refusals as typed states", async () => {
    mount(fake({ series: { status: "loaded", value: series({ state: "NO_PRICE", selection: { state: "NO_PRICE", valid_at: "x", revision_id: null, assignment_id: null, note: "" }, timeline: [], revisions: [], revision_page: { after_revision_no: 0, limit: 200, total: 0, next_after_revision_no: null } }) } }), "/sites/KOBO-001/financials/assumptions");
    await settledScreen();
    expect(screen.getByText(/No diesel price is recorded for today at this site\. No default/)).toBeInTheDocument();
    expect(screen.queryByRole("table", { name: "Price schedule" })).toBeNull();
  });

  it.each([
    ["unavailable", "Prices unavailable"],
    ["unauthenticated", "Sign in required"],
    ["forbidden", "No access"],
  ] as const)("a %s read is its own state", async (status, heading) => {
    mount(fake({ series: { status, message: null } }), "/sites/KOBO-001/financials/assumptions");
    await settledScreen();
    // W1-F3: a page-level refusal (title in .page-refusal, was an h2 panel heading), then the three panel skeletons.
    expect(document.querySelector(`[data-page-refusal='${status}'] .page-refusal__title`)).toHaveTextContent(heading);
    expectV69Panels("assumptions");
    expect(panelTitled("Financial assumptions").querySelector("[data-price-panel-gap]")).toHaveTextContent(heading);
    expect(screen.queryByRole("button", { name: "Edit price" })).toBeNull();
  });
});

describe("Site > Financials > Overview: the Finding bridge", () => {
  it("holds the exact Finding version and shows no amount", async () => {
    const client = fake();
    const { container } = mount(client, `/sites/KOBO-001/financials?finding_id=${FINDING}&revision_id=${FREV}`);
    await settledScreen();
    expect(client.asked.bridge).toEqual([FREV]);
    const bridge = container.querySelector("[data-financials-bridge]");
    expect(bridge).toHaveAttribute("data-financials-bridge", "QUANTITY_UNAVAILABLE");
    expect(bridge).toHaveAttribute("data-finding-revision", FREV);
    expect(bridge).toHaveTextContent("Not calculated");
    expect(bridge?.textContent ?? "").not.toMatch(/USD|\$|\d+\.\d\d/);
    expect(within(bridge as HTMLElement).getByRole("link", { name: "See the evidence for this finding version" })).toHaveAttribute(
      "href",
      `/sites/KOBO-001/findings/${FINDING}/evidence?revision_id=${FREV}`,
    );
    const { violations } = scanProductVocabulary(container, "financials bridge");
    expect(violations, describeViolations(violations)).toEqual([]);
  });

  it("pins the selected version into the address when the link named none", async () => {
    mount(fake(), `/sites/KOBO-001/financials?finding_id=${FINDING}`);
    await settledScreen();
    expect(screen.getByTestId("where")).toHaveTextContent(`finding_id=${FINDING}&revision_id=${FREV}`);
  });

  it("states UNPRICED as its own typed state", async () => {
    mount(fake({ bridge: { status: "loaded", value: bridgeBody("UNPRICED") } }), `/sites/KOBO-001/financials?finding_id=${FINDING}&revision_id=${FREV}`);
    await settledScreen();
    expect(document.querySelector("[data-financials-bridge]")).toHaveAttribute("data-financials-bridge", "UNPRICED");
    // W1-UX-02 (wording moved to the shared money words): was getByText("No price for the whole window").
    // W1-F3: the state line is in "What happened → what it means in money" inside the bridge (was the answer card).
    const card = document.querySelector("[data-financials-bridge]") as HTMLElement;
    expectV69Panels("financials");
    expect(card.querySelector("[data-product-status-label]")).toHaveTextContent(/^No price recorded$/);
    expect(card.querySelector(".product-status__sentence")).toHaveTextContent(
      "No single recorded price covers the whole time, so no amount is shown. This is not zero.",
    );
    expect(card.querySelector("[data-financials-why='NO_PRICE']")).toHaveTextContent("No diesel price is recorded for this finding's time.");
  });

  it("a foreign or unknown Finding version is refused, never replaced", async () => {
    mount(fake({ bridge: { status: "not_found", message: null } }), `/sites/KOBO-001/financials?finding_id=${FINDING}&revision_id=bad`);
    await settledScreen();
    // W1-F3: the refusal title is in the page-level refusal (was an h2 panel heading); the panels keep their gaps.
    expect(document.querySelector("[data-page-refusal='not_found'] .page-refusal__title")).toHaveTextContent("No such finding version");
    expectV69Panels("financials");
    expect(document.querySelector("[data-financials-bridge]")).toBeNull();
  });

  it("marks the Financials tab and the Overview subtab current, and the subtabs omit Scenarios", async () => {
    mount(fake(), "/sites/KOBO-001/financials");
    await settledScreen();
    expect(screen.getByRole("link", { name: "Financials", current: "page" })).toBeInTheDocument();
    const sections = screen.getByRole("navigation", { name: "Financials sections" });
    expect(within(sections).getAllByRole("link").map((l) => l.textContent)).toEqual(["Overview", "Assumptions"]);
    expect(within(sections).getByRole("link", { name: "Overview" })).toHaveAttribute("aria-current", "page");
    expect(screen.queryByText(/Scenario/i)).toBeNull();
    expect(document.querySelector("[data-price-selection='PRICED']")).toHaveTextContent("1.25 USD per litre");
    // W1-F3: with no finding selected the three v69 panels still render, panel 1 stating the gap.
    expectV69Panels("financials");
    expect(panelTitled("What happened → what it means in money").querySelector("[data-financials-bridge='none']")).not.toBeNull();
    expect(document.querySelector("[data-financials-metric='operating-cost']")).toHaveTextContent("No finding selected");
  });
});

describe("financials client", () => {
  afterEach(() => vi.unstubAllGlobals());

  it.each([
    [401, "unauthenticated"],
    [403, "forbidden"],
    [404, "not_found"],
    [503, "unavailable"],
  ] as const)("maps %s to %s and names the exact address", async (code, status) => {
    const calls: string[] = [];
    vi.stubGlobal("fetch", async (path: string) => {
      calls.push(path);
      return new Response(JSON.stringify({ detail: { message: "m" } }), { status: code });
    });
    const client = createFinancialsClient("/api/sites");
    expect((await client.getAssumptionRevision("KOBO-001", "rev 1")).status).toBe(status);
    expect((await client.getFindingFinancials("KOBO-001", "f1", "r 1")).status).toBe(status);
    expect(
      (await client.getFindingConsequences("KOBO-001", "f1", { revisionId: "r 1", consequenceRevisionId: "c 1" })).status,
    ).toBe(status);
    await client.getAssumptions("KOBO-001", { validAt: "2026-10-13T00:00:00Z", recordedAt: "2026-10-13T09:00:00+00:00" });
    expect(calls).toEqual([
      "/api/sites/KOBO-001/financial-assumptions/rev%201",
      "/api/sites/KOBO-001/findings/f1/financials?revision_id=r%201",
      "/api/sites/KOBO-001/findings/f1/financial-consequences?revision_id=r+1&consequence_revision_id=c+1",
      "/api/sites/KOBO-001/financial-assumptions?key=diesel_price_per_litre&valid_at=2026-10-13T00%3A00%3A00Z&recorded_at=2026-10-13T09%3A00%3A00%2B00%3A00",
    ]);
  });
});

describe("Site > Financials > Overview: the S4-02b fuel cost", () => {
  const URL = `/sites/KOBO-001/financials?finding_id=${FINDING}&revision_id=${FREV}`;

  it("shows a current priced range from zero, its bridge steps, and the demonstration label in plain words", async () => {
    const client = fake({
      bridge: { status: "loaded", value: pricedBridge() },
      consequences: { status: "loaded", value: consequencesBody([crev(1, C1), crev(2, C2)]) },
    });
    const { container } = mount(client, URL);
    await settledScreen();
    const bridge = container.querySelector("[data-financials-bridge]") as HTMLElement;
    expect(bridge).toHaveAttribute("data-financials-bridge", "PRICED");
    expect(bridge).toHaveAttribute("data-financials-amount", "shown");
    expect(bridge).toHaveTextContent("0.00 to 16.20 USD");
    // W1-UX-02: the model version moved to the closed exact-reference disclosure (was "... under the reviewed
    // fuel-cost-1 assumptions. ..."); the version must not be in the default reading.
    // W1-F3 review M4: the "Modelled potential fuel-cost exposure" line repeated the state line; the caveat is said
    // once in the panel (the state sentence) and once in Trade-offs.
    expect(bridge).not.toHaveTextContent("Modelled potential fuel-cost exposure");
    expect(bridge.querySelector("[data-financials-state-line] .product-status__sentence")).toHaveTextContent(
      "It is not measured fuel saved, money spent or a physical maximum.",
    );
    expect(panelTitled("Trade-offs and exclusions")).toHaveTextContent("not fuel saved, not money spent, not a physical maximum");
    // W1-F3 review H2: the mock's Confidence column and Data confidence chip, as honest unknowns.
    expect(bridge.querySelector("[data-bridge-confidence]")).toHaveTextContent("Not assessed");
    expect(document.querySelector("[data-financials-statusbar] [data-chip='data-confidence']")).toHaveTextContent("Data confidence: not assessed");
    expect(bridge.querySelector("[data-source-provenance='AUTHORED_DEMONSTRATION']")).toHaveTextContent("Prepared example data");
    expect(container.textContent ?? "").not.toMatch(/simulat/i);
    expect(bridge.querySelector("[data-bridge-amount]")).toHaveAttribute("data-bridge-amount", "current");
    expect(bridge.querySelector("[data-bridge-step='fuel']")).toHaveTextContent("0 to 12.65 litres");
    expect(bridge.querySelector("[data-bridge-step='price']")).toHaveTextContent("1.28 USD per litre");
    expect(within(bridge).getByRole("link", { name: "The site price version used" })).toHaveAttribute(
      "href",
      `/sites/KOBO-001/financials/assumptions?revision_id=${V4}`,
    );
    // identifiers, the model version and enum names only inside the closed disclosure
    // W1-UX-02: the shared exact-reference disclosure ("How this was worked out", was "How this is worked out");
    // the counted readings table moved to its own closed disclosure beside the visible method.
    const details = within(bridge).getByText("How this was worked out").closest("details") as HTMLElement;
    expect(details).not.toHaveAttribute("open");
    expect(details).toHaveTextContent("MODELLED_CONDITIONAL");
    expect(details).toHaveTextContent("sfc_upper_multiplier = 1.10");
    expect(details).toHaveTextContent("fuel-cost-1");
    // W1-F3 review M5: the method and its counted readings are folded into the bridge's one closed disclosure
    // (they were two more disclosures in "Trade-offs and exclusions"); each panel has one disclosure.
    expectV69Panels("financials");
    const readings = details.querySelector("[data-consequence-reading='ev-1']") as HTMLElement;
    expect(readings).not.toBeNull();
    expect(details.querySelector("[data-consequence-method-detail]")).toHaveTextContent("The lower limit is zero.");
    expect(panelTitled("Trade-offs and exclusions").querySelectorAll("details")).toHaveLength(0);
    expect(bridge.querySelectorAll("details[data-exact-references]")).toHaveLength(1);
    const outside = bridge.cloneNode(true) as HTMLElement;
    outside.querySelectorAll("details").forEach((d) => d.remove());
    expect(outside.textContent ?? "").not.toMatch(/MODELLED_CONDITIONAL|POTENTIAL_FUEL_COST|c2000000|fuel-cost-1|ev-1/);
    const { violations } = scanProductVocabulary(container, "financials fuel cost");
    expect(violations, describeViolations(violations)).toEqual([]);
    expect(client.asked.consequences).toEqual([{ revisionId: FREV, consequenceRevisionId: null }]);
  });

  it.each([
    ["QUANTITY_UNAVAILABLE", { quantity_reason: "POWER_COVERAGE_GAP" }, "cover too little of this finding's time"],
    ["UNPRICED", { price_reason: "PRICE_SPANS_WINDOW" }, "changes part-way through this finding's time"],
  ] as const)("states %s with its specific plain reason and no amount", async (state, reasons, words) => {
    const client = fake({
      bridge: { status: "loaded", value: pricedBridge({ state, amount: null, currency: null, quantity: null, ...reasons }) },
    });
    mount(client, URL);
    await settledScreen();
    const bridge = document.querySelector("[data-financials-bridge]") as HTMLElement;
    expect(bridge).toHaveAttribute("data-financials-bridge", state);
    expect(bridge).toHaveAttribute("data-financials-amount", "none");
    expect(bridge).toHaveTextContent(words);
    expect(bridge.textContent ?? "").not.toMatch(/USD|\d+\.\d\d/);
  });

  it.each(["STALE", "PENDING", "HISTORICAL", "AUDIT_ONLY", "UNAVAILABLE"] as const)(
    "a %s fuel cost shows no amount in the money panel even when a priced version is stored",
    async (state) => {
      const client = fake({
        bridge: {
          status: "loaded",
          value: {
            ...pricedBridge({
              state,
              currentness: state === "UNAVAILABLE" ? null : state,
              amount: null,
              currency: null,
              quantity: null,
              reason: "No current cost is shown.",
            }),
            audit_only: state === "AUDIT_ONLY" ? { non_current: true, statement: "Audit material only: the source is closed." } : null,
          },
        },
        consequences: {
          status: "loaded",
          value: consequencesBody([crev(1, C1)], { state: state === "UNAVAILABLE" ? "CURRENT" : state }),
        },
      });
      mount(client, URL);
      await settledScreen();
      const bridge = document.querySelector("[data-financials-bridge]") as HTMLElement;
      expect(bridge).toHaveAttribute("data-financials-amount", "none");
      expect(bridge.querySelector("[data-financials-headline='amount']")).toBeNull();
      expect(bridge.querySelector("[data-bridge-amount]")).toBeNull();
      expect(bridge.querySelector("[data-financials-recorded-pointer]")).not.toBeNull();
      // visible text: no currency amount anywhere in the money panel
      expect(bridge.textContent ?? "").not.toMatch(/\d+\.\d\d|USD/);
      if (state === "AUDIT_ONLY") {
        // L2: the closed-source notice is shown, and no version carries an amount anywhere on the screen
        expect(bridge).toHaveTextContent("Audit material only: the source is closed.");
        expect(document.body.textContent ?? "").not.toMatch(/\d+\.\d\d USD(?! per litre)/);
      }
      // W1-F3 (was: the per-finding version row is marked not current): the version list moved to Assumptions >
      // Interpretation history, so nothing on this screen calls any version current.
      expect(document.querySelector("[data-consequence-current='true']")).toBeNull();
      expect(document.body.textContent ?? "").not.toMatch(/the current fuel cost/);
      expectV69Panels("financials");
    },
  );

  it("L4: when the bridge could not be read, no version is called the current fuel cost", async () => {
    mount(
      fake({
        bridge: { status: "loaded", value: pricedBridge({ state: "UNAVAILABLE", currentness: null, amount: null, currency: null }) },
        consequences: { status: "loaded", value: consequencesBody([crev(1, C1)]) },
      }),
      URL,
    );
    await settledScreen();
    expect(document.body.textContent ?? "").not.toMatch(/the current fuel cost/);
    // W1-F3 (was: the per-finding row marked not current): the version list moved to Interpretation history.
    expect(document.querySelector("[data-consequence-current='true']")).toBeNull();
    expect(document.querySelector("[data-bridge-amount]")).toBeNull();
  });

  it("L1: a PRICED state with a stale currentness still shows no headline amount", async () => {
    mount(fake({ bridge: { status: "loaded", value: pricedBridge({ currentness: "STALE" }) } }), URL);
    await settledScreen();
    const bridge = document.querySelector("[data-financials-bridge]") as HTMLElement;
    expect(bridge).toHaveAttribute("data-financials-amount", "none");
    expect(bridge.querySelector("[data-financials-headline='amount']")).toBeNull();
    expect(bridge.textContent ?? "").not.toMatch(/\d+\.\d\d USD/);
  });

  it("under a closed source an opened earlier version shows no amount either", async () => {
    mount(
      fake({
        bridge: {
          status: "loaded",
          value: {
            ...pricedBridge({ state: "AUDIT_ONLY", currentness: "AUDIT_ONLY", amount: null, currency: null, quantity: null }),
            audit_only: { non_current: true, statement: "Audit material only: the source is closed." },
          },
        },
        consequences: (pin) => ({
          status: "loaded",
          value: consequencesBody([crev(1, C1), crev(2, C2)], { selected: pin.consequenceRevisionId ?? null }),
        }),
      }),
      `${URL}&consequence_revision_id=${C1}`,
    );
    await settledScreen();
    expect(document.querySelector(`[data-consequence-pinned='${C1}']`)).toHaveTextContent("The source is closed");
    expect(document.body.textContent ?? "").not.toMatch(/\d+\.\d\d USD(?! per litre)/);
  });

  it("opens an earlier fuel cost version of the same finding version, labelled as kept for the record, and keeps it on reload", async () => {
    const client = fake({
      bridge: { status: "loaded", value: pricedBridge() },
      consequences: (pin) => ({
        status: "loaded",
        value: consequencesBody([crev(1, C1), crev(2, C2)], { selected: pin.consequenceRevisionId ?? null }),
      }),
    });
    const first = mount(client, URL);
    await settledScreen();
    // W1-F3 (was: the per-finding version list with "Open fuel cost version 1"): the list moved to Assumptions >
    // Interpretation history (whose row links are tested there); panel 1 links to it, and the version opens here
    // by its exact address.
    expect(document.querySelector("[data-financials-history-link]")).toHaveAttribute("href", "/sites/KOBO-001/financials/assumptions");
    expect(document.querySelector("[data-bridge-amount]")).toHaveAttribute("data-bridge-amount", "current");
    first.unmount();
    const second = mount(client, `${URL}&consequence_revision_id=${C1}`);
    await settledScreen();
    expectV69Panels("financials");
    const pinned = document.querySelector(`[data-consequence-pinned='${C1}']`) as HTMLElement;
    expect(pinned).toHaveTextContent("0.00 to 15.82 USD");
    expect(pinned).toHaveTextContent("1.25 USD per litre");
    expect(pinned.querySelector("[data-bridge-amount]")).toHaveAttribute("data-bridge-amount", "recorded");
    expect(pinned).toHaveTextContent("Its fuel amount is the same as in the latest version; only the price applied differs.");
    expect(document.querySelector("[data-financials-bridge]")).toHaveAttribute("data-finding-revision", FREV);
    expect(document.querySelectorAll("[data-bridge-amount]")).toHaveLength(1);
    second.unmount();
    mount(client, `${URL}&consequence_revision_id=${C1}`);
    await settledScreen();
    expect(document.querySelector(`[data-consequence-pinned='${C1}']`)).not.toBeNull();
    expect(client.asked.consequences.at(-1)).toEqual({ revisionId: FREV, consequenceRevisionId: C1 });
  });
});

describe("Site > Financials > Assumptions: later versions (S4-02a review L5)", () => {
  it("appends the next page of versions rather than replacing the first", async () => {
    const page1 = series({ revisions: [P1], revision_page: { after_revision_no: 0, limit: 1, total: 2, next_after_revision_no: 1 } });
    const page2 = series({ revisions: [P3], revision_page: { after_revision_no: 1, limit: 1, total: 2, next_after_revision_no: null } });
    mount(
      fake({ seriesFor: (q) => ({ status: "loaded", value: q.afterRevisionNo ? page2 : page1 }) }),
      "/sites/KOBO-001/financials/assumptions",
    );
    await settledScreen();
    fireEvent.click(screen.getByRole("button", { name: "Show later versions" }));
    await settledScreen();
    const items = document.querySelectorAll("[data-price-history-revision]");
    expect([...items].map((i) => i.getAttribute("data-price-history-revision"))).toEqual([V1, V3]);
    // W1-F3 review: with every version listed, no "Showing 2 of 2 versions." line repeats the count.
    expect(screen.queryByText(/Showing 2 of 2 versions/)).toBeNull();
    expect(screen.queryByRole("button", { name: "Show later versions" })).toBeNull();
  });
});

describe("Site > Financials > Overview: LR-01 money eligibility gate", () => {
  const URL = `/sites/KOBO-001/financials?finding_id=${FINDING}&revision_id=${FREV}`;
  const RECORDED = crev(1, C1, {
    price: { state: "PRICED", reason: null, revision_id: V1, value: "1.25", currency: "USD", unit: "currency/L", considered: [] },
    amount: { low: "0", high: "7.5625", currency: "USD", unrounded: true },
    display: { state: "ROUNDED_OUTWARD", currency: "USD", amount_low: "0.00", amount_high: "7.57" },
  } as Partial<ConsequenceRevision>);
  const LIMIT = {
    kind: "SEQUENCE_ORDER_INVERTED", role: "generator_power", start: "2026-10-23T07:05:00Z", end: "2026-10-23T08:00:00Z",
    evidence_ids: ["ev-late"], clock: "NO_ATTESTATION", attestation_refs: [], window_assessment_revision_id: "wa-1",
    analytic_run_id: "run-1", relation: "CUTS_TAIL", source: "FINDING_REVISION" as const,
  };

  let limits: (typeof LIMIT)[] = [LIMIT];

  function gate(state: "WITHHELD_GENERATOR_SERIES" | "PENDING_REASSESSMENT") {
    return {
      version: "money-eligibility-1", state, note: "", finding_id: FINDING, latest_finding_revision_id: FREV,
      pending_reasons: state === "PENDING_REASSESSMENT" ? ["LIVE_JOB: DAY 2026-10-23 j1"] : [],
      series_limits: state === "WITHHELD_GENERATOR_SERIES" ? limits : [], windows: [],
    };
  }

  function withheldBody(state: "WITHHELD_GENERATOR_SERIES" | "PENDING_REASSESSMENT", selected: string | null = null) {
    const body = consequencesBody([RECORDED], { selected });
    return {
      ...body,
      currentness: { ...body.currentness, current_amount_shown: false, money_eligibility: state },
      consequence: body.consequence ? { ...body.consequence, presented_as_current: false, historical: true } : null,
      money_eligibility: gate(state),
    };
  }

  function client(state: "WITHHELD_GENERATOR_SERIES" | "PENDING_REASSESSMENT") {
    return fake({
      bridge: {
        status: "loaded",
        value: pricedBridge({
          state, currentness: "CURRENT", amount: null, currency: null, quantity: null, consequence_revision_id: null,
          recorded_consequence_revision_id: C1, money_eligibility: gate(state),
          reason: "No current cost is shown. The earlier recorded cost stays available for the record.",
        }),
      },
      consequences: (pin) => ({ status: "loaded", value: withheldBody(state, pin.consequenceRevisionId ?? null) }),
    });
  }

  it("run 1 withheld: no current amount, the refused span in plain words, and an exact link to the recorded 7.57", async () => {
    mount(client("WITHHELD_GENERATOR_SERIES"), URL);
    await settledScreen();
    const bridge = document.querySelector("[data-financials-bridge]") as HTMLElement;
    expect(bridge).toHaveAttribute("data-financials-bridge", "WITHHELD_GENERATOR_SERIES");
    expect(bridge).toHaveAttribute("data-financials-amount", "none");
    expect(bridge.querySelector("[data-financials-headline='amount']")).toBeNull();
    expect(bridge.textContent ?? "").not.toMatch(/\d+\.\d\d USD/);
    // W1-UX-02 (shared money words): was "Withheld: the generator records are not in a proven time order".
    expect(bridge.querySelector("[data-product-status-label]")).toHaveTextContent(/^No current amount can be shown$/);
    expect(bridge).toHaveTextContent(
      "The generator records are not in a proven time order, so no current amount is shown. This is not zero.",
    );
    expect(bridge.querySelector("[data-financials-series-limit='SEQUENCE_ORDER_INVERTED']")).toHaveTextContent(
      "arrived before an earlier reading and their clock is not proven",
    );
    const link = bridge.querySelector(`[data-financials-recorded-link='${C1}']`) as HTMLAnchorElement;
    expect(link.getAttribute("href")).toContain(`consequence_revision_id=${C1}`);
    expect(document.body.textContent ?? "").not.toMatch(/the current fuel cost/);
    expect(document.querySelector("[data-consequence-current='true']")).toBeNull();
    expectV69Panels("financials");
    // W1-F3 (was: the per-finding version row "7.57 USD … kept for the record"): the list moved to Interpretation
    // history; the recorded 7.57 opens by its exact link, labelled as kept for the record, never as current.
    cleanup();
    mount(client("WITHHELD_GENERATOR_SERIES"), `${URL}&consequence_revision_id=${C1}`);
    await settledScreen();
    const recorded = document.querySelector(`[data-consequence-pinned='${C1}']`) as HTMLElement;
    expect(recorded).toHaveTextContent("7.57 USD");
    expect(recorded).toHaveTextContent("kept for the record");
    expect(recorded.querySelector("[data-bridge-amount]")).toHaveAttribute("data-bridge-amount", "recorded");
    expect(document.querySelector("[data-financials-headline='amount']")).toBeNull();
  });

  it("a non-tail limit is worded by its relation and never says the finding ends before it", async () => {
    limits = [
      { ...LIMIT, relation: "CUTS_HEAD" },
      { ...LIMIT, start: "2026-10-23T03:00:00Z", end: "2026-10-23T03:30:00Z", relation: undefined as unknown as string,
        source: "SELECTED_WINDOW" as never },
    ];
    try {
      mount(client("WITHHELD_GENERATOR_SERIES"), URL);
      await settledScreen();
      const text = (document.querySelector("[data-financials-bridge]") as HTMLElement).textContent ?? "";
      expect(text).toContain("The finding starts after them and that time is not judged.");
      expect(text).toContain("within 6 hours of this finding");
      expect(text).not.toContain("The finding ends before them");
    } finally {
      limits = [LIMIT];
    }
  });

  it("the same span from the Finding revision and the selected window is one list item, with the specific wording", async () => {
    limits = [
      { ...LIMIT, source: "SELECTED_WINDOW" as never, relation: undefined as unknown as string },
      { ...LIMIT, relation: "CUTS_TAIL" },
    ];
    try {
      mount(client("WITHHELD_GENERATOR_SERIES"), URL);
      await settledScreen();
      const items = document.querySelectorAll("[data-financials-bridge] [data-financials-series-limit]");
      expect(items).toHaveLength(1);
      expect(items[0]).toHaveTextContent("The finding ends before them and that time is not judged.");
      expect(items[0].textContent).not.toContain("within 6 hours");
    } finally {
      limits = [LIMIT];
    }
  });

  it("no span list is rendered when nothing is withheld by span", async () => {
    limits = [];
    try {
      mount(client("WITHHELD_GENERATOR_SERIES"), URL);
      await settledScreen();
      expect(document.querySelector("[data-financials-bridge] [data-financials-money-limit] ul")).toBeNull();
    } finally {
      limits = [LIMIT];
    }
  });

  it("opening the recorded head shows it as a record, never as the current cost", async () => {
    mount(client("WITHHELD_GENERATOR_SERIES"), `${URL}&consequence_revision_id=${C1}`);
    await settledScreen();
    const pinned = document.querySelector(`[data-consequence-pinned='${C1}']`) as HTMLElement;
    expect(pinned).toHaveAttribute("data-consequence-pinned-current", "false");
    expect(pinned.querySelector("[data-consequence-pinned-withheld='WITHHELD_GENERATOR_SERIES']")).not.toBeNull();
    expect(document.querySelector("[data-financials-headline='amount']")).toBeNull();
  });

  it("pending reassessment: no current amount and the pending wording", async () => {
    mount(client("PENDING_REASSESSMENT"), URL);
    await settledScreen();
    const bridge = document.querySelector("[data-financials-bridge]") as HTMLElement;
    expect(bridge).toHaveAttribute("data-financials-amount", "none");
    // W1-UX-02 (shared money words): was "Being reassessed: no current cost yet".
    expect(bridge.querySelector("[data-product-status-label]")).toHaveTextContent(/^No current amount can be shown$/);
    expect(bridge).toHaveTextContent(
      "Newer readings mean this should be checked again, so no current amount is shown yet. This is not zero.",
    );
    expect(bridge.querySelector("[data-financials-pending-reassessment='true']")).not.toBeNull();
    expect(bridge.querySelector(`[data-financials-recorded-link='${C1}']`)).not.toBeNull();
  });
});

describe("Site > Financials > Overview: S4-05b stored source gate", () => {
  const URL = `/sites/KOBO-001/financials?finding_id=${FINDING}&revision_id=${FREV}`;

  it.each(["MIXED", "UNKNOWN"] as const)(
    "a %s set withholds the current amount beside an eligible priced head, keeps the record linked and labels each version",
    async (state) => {
      const union: SourceProvenance = {
        ...authoredSource(C2),
        state,
        reasons: [{ code: state === "MIXED" ? "BOUND_AND_UNBOUND" : "NO_POSITIVE_BINDING", accepted_evidence_ids: ["ev-1"] }],
        problematic_accepted_evidence_ids: ["ev-1"],
      };
      const history = consequencesBody([crev(1, C1), crev(2, C2)]);
      const client = fake({
        bridge: {
          status: "loaded",
          value: {
            ...pricedBridge({
              state: "MIXED_OR_UNKNOWN_SOURCE", currentness: "CURRENT", amount: null, currency: null, quantity: null,
              consequence_revision_id: null, recorded_consequence_revision_id: C2,
              currentness_reasons: ["MIXED_OR_UNKNOWN_SOURCE"],
              reason: "The source of the records behind this cost is not established, so no current cost is shown.",
            }),
            source_provenance: { finding_revision: { ...authoredSource(), state }, consequence_revision: union },
          },
        },
        consequences: {
          status: "loaded",
          value: {
            ...history,
            currentness: { ...history.currentness, current_amount_shown: false },
            history: { ...history.history, revisions: history.history.revisions.map((r) => ({ ...r, source_provenance: union })) },
          },
        },
      });
      const { container } = mount(client, URL);
      await settledScreen();
      const bridge = container.querySelector("[data-financials-bridge]") as HTMLElement;
      expect(bridge).toHaveAttribute("data-financials-bridge", "MIXED_OR_UNKNOWN_SOURCE");
      expect(bridge).toHaveAttribute("data-financials-amount", "none");
      expect(bridge.textContent ?? "").not.toMatch(/\d+\.\d\d USD/);
      expect(bridge.querySelector(`[data-source-provenance='${state}']`)).toHaveTextContent("No current cost is shown.");
      expect(bridge.querySelector("[data-financials-source-withheld]")).not.toBeNull();
      expect(bridge.querySelector(`[data-financials-recorded-link='${C2}']`)).not.toBeNull();
      // W1-F3 (was: the per-finding version row, not current, with its source label): the version list and its
      // per-version source labels moved to Assumptions > Interpretation history; nothing here is called current.
      expect(document.querySelector("[data-consequence-current='true']")).toBeNull();
      expect(document.querySelector("[data-bridge-amount]")).toBeNull();
      expectV69Panels("financials");
      expect(document.body.textContent ?? "").not.toMatch(/the current fuel cost/);
      const { violations } = scanProductVocabulary(container, `financials ${state}`);
      expect(violations, describeViolations(violations)).toEqual([]);
    },
  );
});

/** S4-08: one recorded fuel cost version as the history read returns it. */
function hrow(id: string, patch: Partial<ConsequenceHistoryRow> = {}): ConsequenceHistoryRow {
  return {
    finding_id: FINDING,
    finding_revision_id: FREV,
    finding_revision_no: 2,
    finding_title: "Generator ran while the battery could have carried the load",
    finding_window: { from: "2026-10-06T08:05:00+00:00", to: "2026-10-06T08:30:00+00:00", bounds: "[from, to)" },
    consequence_revision_id: id,
    revision_no: 2,
    prior_consequence_revision_id: null,
    recorded_at: "2026-10-16T09:00:00.000321+00:00",
    window: { from: "2026-10-06T08:05:00+00:00", to: "2026-10-06T08:30:00+00:00", bounds: "[from, to)" },
    at_cutoff: "CURRENT_AT_CUTOFF",
    state: "PRICED",
    quantity: { state: "AVAILABLE", reason: null, unit: "L", high: "2.75" },
    price: { state: "LINKED", price_revision_id: V1, reason: null, value: "1.25", currency: "USD", assignments: [] },
    change_from_prior: "PRICE_ONLY",
    recorded_amount: {
      disposition: "SHOWN",
      label: "Recorded amount — historical, assumption-conditioned audit history",
      amount: { low: "0.00", high: "3.44", currency: "USD" },
      is_current_amount: false,
    },
    source_provenance: authoredSource(id),
    links: { finding: "x", finding_financials: "x", price_revision: "x", api_consequence: "x" },
    ...patch,
  };
}

const H1 = "c1000000-0000-4000-8000-000000000001";
const H2 = "c2000000-0000-4000-8000-000000000002";
const H3 = "c3000000-0000-4000-8000-000000000003";
const H4 = "c4000000-0000-4000-8000-000000000004";

function echoSeries(query: SeriesQuery): FinancialReadResult<AssumptionSeriesBody> {
  return {
    status: "loaded",
    value: series({
      cutoff: { recorded_at: query.recordedAt ?? null, selected_by: query.recordedAt ? "RECORDED_CUTOFF" : "CURRENT", basis: "x" },
    }),
  };
}

function escaped(text: string): string {
  return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

describe("Site > Financials > Assumptions > Interpretation history (S4-08)", () => {
  it("reads prices at the history's exact cutoff string on the default address, without rewriting it", async () => {
    const client = fake({ seriesFor: echoSeries });
    mount(client, "/sites/KOBO-001/financials/assumptions");
    await settledScreen();
    expect(client.asked.history).toEqual([{ recordedAt: null, after: null }]);
    // Review L-R1: the same string, microseconds included, never a `Date` round trip.
    expect(client.asked.series.map((q) => q.recordedAt)).toEqual([CUT]);
    expect(screen.getByTestId("where")).toHaveTextContent(/^\/sites\/KOBO-001\/financials\/assumptions$/);
    // Review L-R2 (deliberate change): the default price list is now read at a recorded cutoff, not CURRENT.
    expect(document.querySelector("[data-price-cutoff]")).toHaveAttribute("data-price-cutoff", "RECORDED_CUTOFF");
    expect(screen.queryByRole("link", { name: "Show the current prices" })).toBeNull();
    expect(document.querySelector("[data-history-cutoff]")).toHaveAttribute("data-history-cutoff", CUT);
  });

  it("keeps an explicit cutoff for both reads and through the next-page address", async () => {
    const at = "2026-10-15T07:00:00.000009+00:00";
    const client = fake({
      seriesFor: echoSeries,
      history: (q) => ({
        status: "loaded",
        value: historyBody([hrow(H1)], {
          cutoff: { recorded_at: q.recordedAt ?? CUT, selected_by: "RECORDED_CUTOFF", clock: "DATABASE", membership: "x" },
          next_cursor: q.after ? null : "cursor-1",
          page: { limit: 25, shown: 1, is_first: !q.after },
        }),
      }),
    });
    mount(client, `/sites/KOBO-001/financials/assumptions?recorded_at=${encodeURIComponent(at)}&history_limit=2`);
    await settledScreen();
    expect(client.asked.history[0]).toEqual({ recordedAt: at, after: null, limit: 2 });
    expect(client.asked.series[0].recordedAt).toBe(at);
    fireEvent.click(screen.getByRole("link", { name: "Show earlier versions" }));
    await settledScreen();
    // The cursor was issued for one page size, so the address keeps it.
    expect(screen.getByTestId("where")).toHaveTextContent(
      `/sites/KOBO-001/financials/assumptions?recorded_at=${encodeURIComponent(at)}&history_after=cursor-1&history_limit=2`,
    );
    expect(client.asked.history.at(-1)).toEqual({ recordedAt: at, after: "cursor-1", limit: 2 });
    expect(client.asked.series.every((q) => q.recordedAt === at)).toBe(true);
    expect(screen.getByRole("link", { name: "Back to the newest versions" })).toBeInTheDocument();
  });

  it("lists earlier and latest versions with recorded amounts only as labelled history, and exact links", async () => {
    const rows = [
      hrow(H4),
      hrow(H3, {
        at_cutoff: "HISTORICAL_AT_CUTOFF",
        revision_no: 1,
        change_from_prior: "FIRST_VERSION",
        state: "UNPRICED",
        price: { state: "NO_PRICE_LINK", price_revision_id: null, reason: "NO_PRICE", value: null, currency: null, assignments: [] },
        recorded_amount: { disposition: "UNPRICED", label: null, amount: null, is_current_amount: false },
      }),
      hrow(H2, {
        finding_id: "f0000000-0000-4000-8000-000000000009",
        source_provenance: { ...authoredSource(H2), state: "MIXED" },
        recorded_amount: { disposition: "MIXED_OR_UNKNOWN_SOURCE", label: null, amount: null, is_current_amount: false },
      }),
    ];
    const { container } = mount(
      fake({ seriesFor: echoSeries, history: { status: "loaded", value: historyBody(rows) } }),
      "/sites/KOBO-001/financials/assumptions",
    );
    await settledScreen();
    const panel = screen.getByRole("region", { name: "Interpretation history" });
    const items = Array.from(panel.querySelectorAll("[data-history-row]")) as HTMLElement[];
    expect(items.map((i) => i.getAttribute("data-history-at-cutoff"))).toEqual([
      "CURRENT_AT_CUTOFF",
      "HISTORICAL_AT_CUTOFF",
      "CURRENT_AT_CUTOFF",
    ]);
    const latest = items[0];
    expect(latest).toHaveTextContent("Latest at this moment");
    expect(latest).toHaveTextContent("The price changed; the measured result did not.");
    expect(latest).toHaveTextContent(
      "0.00 to 3.44 USD. Recorded amount — historical, assumption-conditioned audit history. Not a current cost.",
    );
    expect(latest).toHaveTextContent("Prepared example data.");
    expect(within(latest).getByRole("link", { name: "Open this fuel cost version" })).toHaveAttribute(
      "href",
      `/sites/KOBO-001/financials?finding_id=${FINDING}&revision_id=${FREV}&consequence_revision_id=${H4}`,
    );
    expect(within(latest).getByRole("link", { name: "Open the finding" })).toHaveAttribute(
      "href",
      `/sites/KOBO-001/findings/${FINDING}?revision_id=${FREV}`,
    );
    expect(within(latest).getByRole("link", { name: "The price version used" })).toHaveAttribute(
      "href",
      `/sites/KOBO-001/financials/assumptions?revision_id=${V1}`,
    );
    expect(items[1]).toHaveTextContent("Earlier version");
    expect(items[1]).toHaveTextContent("No amount. No diesel price is recorded");
    expect(items[1].querySelector("[data-history-recorded-amount]")).toBeNull();
    expect(items[2]).toHaveTextContent("Not shown: the source of the readings behind this version is not confirmed.");
    expect(items[2]).toHaveTextContent("Sources do not agree.");
    expect(panel).not.toHaveTextContent(/current amount|today.s (amount|cost)/i);
    // Exact IDs only in each closed "How this was worked out" disclosure.
    for (const id of within(panel).getAllByText(H4)) expect(id.closest("details")).not.toHaveAttribute("open");
    const { violations } = scanProductVocabulary(container, "assumptions history");
    expect(violations, describeViolations(violations)).toEqual([]);
  });

  // W1-F3 phase D (phase C risk): the S4-05b per-version source label, moved off the Financials
  // overview, must render in the Assumptions Interpretation history for both non-attested states.
  it.each([
    ["MIXED", "Sources do not agree", "different or unverified sources"],
    ["UNKNOWN", "Source unverified", "cannot establish the source"],
  ] as const)("labels a %s-source version in the Interpretation history and shows no amount for it", async (state, label, statement) => {
    const rows = [
      hrow(H2, {
        finding_id: "f0000000-0000-4000-8000-000000000009",
        source_provenance: { ...authoredSource(H2), state },
        recorded_amount: { disposition: "MIXED_OR_UNKNOWN_SOURCE", label: null, amount: null, is_current_amount: false },
      }),
    ];
    mount(
      fake({ seriesFor: echoSeries, history: { status: "loaded", value: historyBody(rows) } }),
      "/sites/KOBO-001/financials/assumptions",
    );
    await settledScreen();
    expectV69Panels("assumptions");
    const panel = panelTitled("Interpretation history");
    const row = panel.querySelector("[data-history-row]") as HTMLElement;
    const source = row.querySelector("[data-history-source]") as HTMLElement;
    expect(source).toHaveAttribute("data-history-source", state);
    expect(source).toHaveTextContent(label);
    expect(source).toHaveTextContent(statement);
    expect(visibleOutsideClosedDisclosure(source)).toBe(true);
    expect(row).toHaveTextContent("Not shown: the source of the readings behind this version is not confirmed.");
    expect(row.querySelector("[data-history-recorded-amount]")).toBeNull();
    // No recorded fuel-cost range for this version (a price per litre elsewhere in the panel is not an amount).
    expect(row).not.toHaveTextContent(/\d+\.\d{2} to \d+\.\d{2} USD/);
    expect(panel).not.toHaveTextContent(/current amount|today.s (amount|cost)/i);
  });

  it("keeps every version listed without amounts when the source is closed", async () => {
    const closed = hrow(H1, { recorded_amount: { disposition: "SOURCE_CLOSED", label: null, amount: null, is_current_amount: false } });
    mount(
      fake({
        seriesFor: echoSeries,
        history: { status: "loaded", value: historyBody([closed], { source_gate: { open: false, reason: "closed" } }) },
      }),
      "/sites/KOBO-001/financials/assumptions",
    );
    await settledScreen();
    expect(document.querySelector("[data-history-source-closed]")).toBeInTheDocument();
    expect(document.querySelector("[data-history-row]")).toHaveTextContent("Not shown: this site's source is closed");
  });

  it("states an empty history plainly", async () => {
    mount(fake({ seriesFor: echoSeries }), "/sites/KOBO-001/financials/assumptions");
    await settledScreen();
    // W1-F3 review M7: the empty fact is the panel's one state line (beside price versions, it says they are prices only).
    const empty = document.querySelector("[data-consequence-history-empty]") as HTMLElement;
    expect(empty.querySelector(".product-status__sentence")?.textContent).toMatch(/^No fuel cost version (recorded by this moment|had been recorded for this site at this moment)/);
    expect(empty).not.toHaveTextContent("Every amount here is shown as it was recorded");
  });

  it("height phase: an empty fuel cost history beside listed price versions says the prices are prices only", async () => {
    mount(fake({ seriesFor: echoSeries }), "/sites/KOBO-001/financials/assumptions");
    await settledScreen();
    expect(document.querySelectorAll("[data-price-history-revision]").length).toBeGreaterThan(0);
    expect(document.querySelector("[data-consequence-history-prices-only] .product-status__sentence")).toHaveTextContent(
      "No fuel cost version recorded by this moment; the price versions below are prices only.",
    );
    expect(document.body).not.toHaveTextContent("Every amount here is shown as it was recorded");
  });

  it("height phase: price history shows the latest 3 versions; earlier ones stay reachable, oldest first, behind 'Show all N'", async () => {
    const more = [1, 2, 3, 4, 5].map((n) => ({ ...P1, revision_id: `p-${n}`, revision_no: n }));
    mount(fake({ series: { status: "loaded", value: series({ revisions: more, revision_page: { after_revision_no: 0, limit: 200, total: 5, next_after_revision_no: null } }) } }), "/sites/KOBO-001/financials/assumptions");
    await settledScreen();
    const ids = (root: ParentNode) => Array.from(root.querySelectorAll("[data-price-history-revision]")).map((li) => li.getAttribute("data-price-history-revision"));
    expect(ids(document)).toEqual(["p-1", "p-2", "p-3", "p-4", "p-5"]);
    const showAll = document.querySelector("details[data-show-all='price-history-earlier']") as HTMLDetailsElement;
    expect(showAll.open).toBe(false);
    expect(showAll.querySelector("summary")).toHaveTextContent("Show all 5 versions (2 earlier)");
    expect(ids(showAll)).toEqual(["p-1", "p-2"]);
    expect(Array.from(document.querySelectorAll("[data-price-history-revision]")).filter((li) => visibleOutsideClosedDisclosure(li)).map((li) => li.getAttribute("data-price-history-revision"))).toEqual(["p-3", "p-4", "p-5"]);
  });

  it("height phase: the state line, price and disabled edit are visible; the strip and full schedule are reachable behind 'When each price applies'", async () => {
    mount(fake(), "/sites/KOBO-001/financials/assumptions");
    await settledScreen();
    const c = card("assumptions-price");
    const showAll = c.querySelector("details[data-show-all='price-schedule']") as HTMLDetailsElement;
    expect(showAll.open).toBe(false);
    expect(showAll.querySelector("summary")).toHaveTextContent("When each price applies (3 prices)");
    expect(showAll.querySelectorAll("tr[data-price-assignment]")).toHaveLength(3);
    expect(showAll.querySelector("[data-price-strip]")).not.toBeNull();
    for (const sel of ["[data-price-state]", "[data-price-selection]", "[data-gap-id='G-assumptions-human-edit']"]) {
      expect(visibleOutsideClosedDisclosure(c.querySelector(sel)!), sel).toBe(true);
    }
  });

  it("shows a plain refusal for the price list when the history cannot fix a moment (review L-R2)", async () => {
    const client = fake({ history: { status: "unavailable", message: null } });
    mount(client, "/sites/KOBO-001/financials/assumptions");
    await settledScreen();
    expect(client.asked.series).toEqual([]);
    expect(document.querySelector("[data-financials-read='no-cutoff']")).toBeInTheDocument();
    expect(document.querySelector("[data-consequence-history='unavailable']")).toHaveTextContent("This is not an empty history.");
    expect(screen.queryByRole("region", { name: "Site diesel price" })).toBeNull();
  });

  it("reloads page one at the same moment when the basis changed (typed 409)", async () => {
    const at = "2026-10-15T07:00:00.000009+00:00";
    const client = fake({
      seriesFor: echoSeries,
      history: (q) => (q.after ? { status: "basis_changed", message: null } : { status: "loaded", value: historyBody([hrow(H1)]) }),
    });
    mount(client, `/sites/KOBO-001/financials/assumptions?recorded_at=${encodeURIComponent(at)}&history_after=stale`);
    await settledScreen();
    expect(screen.getByTestId("where")).toHaveTextContent(
      new RegExp(`^${escaped(`/sites/KOBO-001/financials/assumptions?recorded_at=${encodeURIComponent(at)}`)}$`),
    );
    await vi.waitFor(() => expect(client.asked.history.at(-1)).toEqual({ recordedAt: at, after: null }));
    await settledScreen();
    expect(document.querySelector("[data-history-row]")).toBeInTheDocument();
  });

  it("sends the history cutoff and cursor to the documented route", async () => {
    const calls: string[] = [];
    vi.stubGlobal("fetch", async (url: string) => {
      calls.push(url);
      return new Response(JSON.stringify({ detail: { code: "CONSEQUENCE_HISTORY_BASIS_CHANGED" } }), { status: 409 });
    });
    const result = await createFinancialsClient("/api/sites").getConsequenceHistory("KOBO-001", { recordedAt: CUT, after: "abc" });
    expect(result.status).toBe("basis_changed");
    expect(calls[0]).toBe(`/api/sites/KOBO-001/financial-assumptions/consequences?recorded_at=${encodeURIComponent(CUT)}&after=abc`);
    vi.unstubAllGlobals();
  });
});

// --- W1-UX-02 (group D): Financials and Assumptions on the shared W1 presentation layer -------------------------

function mainOf(container: HTMLElement): HTMLElement {
  return container.querySelector("main") as HTMLElement;
}

/**
 * W1-F3: the former answer cards are now v69 panel content. "financials-consequence" is the bridge wrapper (the
 * money measures and "What happened → what it means in money"); "assumptions-price" is the "Financial
 * assumptions" panel. Null when absent.
 */
function card(name: "financials-consequence" | "assumptions-price"): HTMLElement {
  if (name === "financials-consequence") return document.querySelector("[data-financials-bridge]") as HTMLElement;
  return (document.querySelector("#site-price-heading")?.closest(".panel") ?? null) as HTMLElement;
}

/**
 * The closed-disclosure acceptance for a state whose read carries no instant: the state, sentence and scope are
 * present outside the closed disclosure and the bound says plainly that the time is not recorded (never "now").
 */
function expectUntimedStateLine(within: Element): string {
  const label = expectStateLineVisible(within);
  expect(within.querySelector("[data-product-status] [data-product-status-as-of]")?.textContent).toBe("As of: time not recorded");
  return label;
}

function expectW1Clean(container: HTMLElement, cardEl: HTMLElement, page: string, floor: number) {
  const w1 = scanProductVocabulary(mainOf(container), `${page} (W1)`, { set: "w1" });
  expect(w1.scanned).toBeGreaterThan(floor);
  expect(w1.violations, describeViolations(w1.violations)).toEqual([]);
  const disclosure = scanDisclosureVocabulary(cardEl, `${page} disclosure`);
  expect(disclosure.disclosures).toBeGreaterThan(0);
  expect(disclosure.scanned).toBeGreaterThan(0);
  expect(disclosure.violations, describeViolations(disclosure.violations)).toEqual([]);
}

describe("W1-UX-02: Site > Financials (financials)", () => {
  const URL = `/sites/KOBO-001/financials?finding_id=${FINDING}&revision_id=${FREV}`;

  it("W1-UX-02: while the consequences read is loading no current amount is shown", async () => {
    const base = fake({ bridge: { status: "loaded", value: pricedBridge() } });
    let release: (r: FinancialReadResult<FindingConsequencesBody>) => void = () => undefined;
    const client = {
      ...base,
      getFindingConsequences: () => new Promise<FinancialReadResult<FindingConsequencesBody>>((res) => { release = res; }),
    } as typeof base;
    mount(client, URL);
    await vi.waitFor(() => expect(document.querySelector("[data-financials-bridge-loading]")).not.toBeNull());
    expect(document.querySelector("[data-financials-headline='amount']")).toBeNull();
    expect(document.body.textContent).not.toMatch(/0\.00 to 16\.20/);
    expect(document.body.textContent).not.toContain("time not recorded");
    release({ status: "loaded", value: consequencesBody([crev(1, C1), crev(2, C2)]) });
    await settledScreen();
    expect(card("financials-consequence").querySelector("[data-financials-headline='amount']")).toHaveTextContent("0.00 to 16.20 USD");
    expectV69Panels("financials");
  });

  it("W1-UX-06 (W1-UX-02 re-review N1): when the bridge lands, no commit pairs it with the earlier empty consequences answer", async () => {
    // Before the bridge lands the consequences read answers "nothing to read" at once. When the bridge lands, the
    // pinned request changes; the amount must never be drawn (even for one commit) from that earlier answer.
    let releaseBridge: (r: FinancialReadResult<FindingFinancialsBody>) => void = () => undefined;
    const pins: ConsequencePin[] = [];
    const base = fake();
    const client = {
      ...base,
      getFindingFinancials: () => new Promise<FinancialReadResult<FindingFinancialsBody>>((res) => { releaseBridge = res; }),
      getFindingConsequences: (_s: string, _f: string, pin: ConsequencePin) => {
        pins.push(pin);
        return new Promise<FinancialReadResult<FindingConsequencesBody>>(() => undefined);
      },
    } as typeof base;
    const drawn: string[] = [];
    const observer = new MutationObserver((records) => {
      for (const r of records) {
        for (const n of Array.from(r.addedNodes)) {
          if (!(n instanceof Element)) continue;
          const hit = n.matches("[data-financials-headline='amount']") ? n : n.querySelector("[data-financials-headline='amount']");
          if (hit) drawn.push(hit.textContent ?? "");
        }
      }
    });
    observer.observe(document.body, { childList: true, subtree: true });
    try {
      mount(client, URL);
      await vi.waitFor(() => expect(screen.getByText("Loading the finding's money view.")).toBeInTheDocument());
      releaseBridge({ status: "loaded", value: pricedBridge() });
      await vi.waitFor(() => expect(document.querySelector("[data-financials-bridge-loading]")).not.toBeNull());
      await vi.waitFor(() => expect(pins.length).toBeGreaterThan(0));
      expect(drawn, "an amount was drawn before its consequences read answered").toEqual([]);
      expect(document.body.textContent).not.toContain("time not recorded");
    } finally {
      observer.disconnect();
    }
  });

  it("W1-UX-02: a current priced Finding leads with the bounded range, its bars and basis, and the W1 vocabulary", async () => {
    const client = fake({
      bridge: { status: "loaded", value: pricedBridge() },
      consequences: { status: "loaded", value: consequencesBody([crev(1, C1), crev(2, C2)]) },
    });
    const { container } = mount(client, URL);
    await settledScreen();
    const c = card("financials-consequence");
    // W1-F3: the answer card's question line is gone; the screen renders exactly the three v69 panels.
    expectV69Panels("financials");
    expect(c.querySelector("[data-financials-metric='operating-cost'] [data-financials-headline='amount']")).toHaveTextContent("0.00 to 16.20 USD");
    expect(expectStateLineVisible(c)).toBe("Modelled range, using the latest checked readings");
    // The bound is the time the shown range was worked out, as the read returned it.
    expect(c.querySelector("[data-product-status-as-of]")).toHaveTextContent(/^As of 14 Oct 2026, 10:00 UTC$/);
    // S4-05 source provenance stays beside the headline, outside the disclosure.
    const source = c.querySelector("[data-source-provenance='AUTHORED_DEMONSTRATION']") as HTMLElement;
    expect(visibleOutsideClosedDisclosure(source)).toBe(true);
    // W1-F3: the value bars and step strip are replaced by the mock's bridge table; the current amount is in its
    // consequence cell, marked current, and nowhere a gap word.
    expect(c.querySelector("[data-bridge-amount='current']")).toHaveTextContent("0.00 to 16.20 USD");
    expect(c.querySelector("[data-financials-exposure-gap]")).toBeNull();
    expect(within(c).getByRole("link", { name: "See the evidence for this finding version" })).toHaveAttribute(
      "href",
      `/sites/KOBO-001/findings/${FINDING}/evidence?revision_id=${FREV}`,
    );
    expectW1Clean(container, c, "financials", 20);
  });

  const NON_POSITIVE = [
    ["QUANTITY_UNAVAILABLE", { state: "QUANTITY_UNAVAILABLE", quantity_reason: "POWER_COVERAGE_GAP" }, "Not calculated: no fuel amount, so no cost"],
    ["UNPRICED", { state: "UNPRICED", price_reason: "PRICE_SPANS_WINDOW" }, "No price recorded"],
    ["STALE", { state: "STALE", currentness: "STALE" }, "No current amount can be shown"],
    ["PENDING", { state: "PENDING", currentness: "PENDING" }, "No current amount can be shown"],
    ["HISTORICAL", { state: "HISTORICAL", currentness: "HISTORICAL" }, "No current amount can be shown"],
    ["UNAVAILABLE", { state: "UNAVAILABLE", currentness: null }, "The cost could not be read"],
    ["PRICED but stale", { state: "PRICED", currentness: "STALE" }, "No current amount can be shown"],
    ["PRICED with no rounding rule", { state: "PRICED", currentness: "CURRENT", amount: null }, "No current amount can be shown"],
    ["an unknown state", { state: "SOMETHING_NEW" as never }, "We cannot judge this yet"],
  ] as const;

  it.each(NON_POSITIVE)(
    "W1-UX-02: %s says why there is no current amount, draws a not-known mark and keeps its state line visible",
    async (_name, patch, label) => {
      const value = pricedBridge({ amount: null, currency: null, quantity: null, reason: "No current cost is shown.", ...(patch as object) });
      if ("amount" in patch) value.consequence.currency = "USD";
      const { container } = mount(fake({ bridge: { status: "loaded", value }, consequences: { status: "loaded", value: consequencesBody([crev(1, C1)], { state: "STALE" }) } }), URL);
      await settledScreen();
      const c = card("financials-consequence");
      expect(expectUntimedStateLine(c)).toBe(label);
      expect(c.querySelector("[data-product-status]")).not.toHaveAttribute("data-product-status", "positive");
      expect(c.querySelector("[data-financials-headline='amount']")).toBeNull();
      expect(c.querySelector("[data-financials-headline='none']")).toHaveTextContent("No current amount is shown for this finding version");
      // W1-F3 review M4: the reason is said once, by the visible state sentence; a separate "Why no current amount"
      // line appears only when it adds a stored fuel-amount or price reason.
      const why = c.querySelector("[data-financials-why]");
      if (value.consequence.state === "QUANTITY_UNAVAILABLE" || value.consequence.state === "UNPRICED") {
        expect((why?.textContent ?? "").trim().length).toBeGreaterThan(0);
      } else {
        expect(why).toBeNull();
      }
      const sentence = c.querySelector("[data-financials-state-line] .product-status__sentence") as HTMLElement;
      expect((sentence.textContent ?? "").trim().length).toBeGreaterThan(20);
      expect(visibleOutsideClosedDisclosure(sentence)).toBe(true);
      // W1-F3 (was: never a zero bar, one not-known mark): the exposure card states a gap word, never a number.
      expectV69Panels("financials");
      const exposure = c.querySelector("[data-financials-metric='operating-cost'] .v69-metric__value") as HTMLElement;
      expect(exposure.querySelector("[data-financials-exposure-gap]")).not.toBeNull();
      expect(exposure.textContent ?? "").not.toMatch(/\d/);
      expect(c.textContent ?? "").not.toMatch(/\d+\.\d\d USD(?! per litre)/);
      expect(document.querySelector("[data-bridge-amount='current']")).toBeNull();
      expectW1Clean(container, c, `financials ${_name}`, 10);
    },
  );

  it.each(["WITHHELD_GENERATOR_SERIES", "PENDING_REASSESSMENT", "MIXED_OR_UNKNOWN_SOURCE"] as const)(
    "W1-UX-02: money withheld (%s) keeps the LR-01 limit, the exact link to the recorded cost and a visible state line",
    async (state) => {
      const value = pricedBridge({
        state, amount: null, currency: null, quantity: null, consequence_revision_id: null, recorded_consequence_revision_id: C1,
        money_eligibility: { version: "x", state: state === "MIXED_OR_UNKNOWN_SOURCE" ? "ELIGIBLE" : state, note: "", finding_id: FINDING,
          latest_finding_revision_id: FREV, pending_reasons: [], series_limits: [], windows: [] } as never,
        reason: "No current cost is shown.",
      });
      const { container } = mount(fake({ bridge: { status: "loaded", value } }), URL);
      await settledScreen();
      const c = card("financials-consequence");
      expect(expectUntimedStateLine(c)).toBe("No current amount can be shown");
      expect(c.querySelector(`[data-financials-money-limit='${state}']`)).not.toBeNull();
      const link = c.querySelector(`[data-financials-recorded-link='${C1}']`) as HTMLAnchorElement;
      expect(link.getAttribute("href")).toBe(`/sites/KOBO-001/financials?finding_id=${FINDING}&revision_id=${FREV}&consequence_revision_id=${C1}`);
      // W1-F3 (was: no known bar; a problem/waiting step): the exposure card states the withheld/waiting gap word.
      expect(c.querySelector(`[data-financials-exposure-gap='${state}']`)).toHaveTextContent(
        state === "PENDING_REASSESSMENT" ? "Not worked out yet" : "Withheld",
      );
      expect(c.querySelector("[data-bridge-amount]")).toBeNull();
      expectW1Clean(container, c, `financials ${state}`, 10);
    },
  );

  it("W1-UX-02: a refused Finding version read has its own state line and no money card", async () => {
    const { container } = mount(fake({ bridge: { status: "not_found", message: null } }), `/sites/KOBO-001/financials?finding_id=${FINDING}&revision_id=bad`);
    await settledScreen();
    const refused = document.querySelector("[data-financials-state='not_found']") as HTMLElement;
    expect(expectUntimedStateLine(refused)).toBe("This record was not found");
    expect(card("financials-consequence")).toBeNull();
    // W1-F3: a page-level refusal, then the three v69 panels with the gap stated in each.
    expect(refused.closest("[data-page-refusal='not_found']")).not.toBeNull();
    expectV69Panels("financials");
    expect(panelTitled("What happened → what it means in money").querySelector("[data-financials-panel-gap]")).toHaveTextContent(
      "No such finding version",
    );
    const w1 = scanProductVocabulary(mainOf(container), "financials refused (W1)", { set: "w1" });
    expect(w1.violations, describeViolations(w1.violations)).toEqual([]);
  });

  it("W1-UX-02: the exact Finding version link survives a reload at the same address", async () => {
    const client = fake({
      bridge: { status: "loaded", value: pricedBridge() },
      consequences: { status: "loaded", value: consequencesBody([crev(1, C1), crev(2, C2)]) },
    });
    const first = mount(client, URL);
    await settledScreen();
    const before = card("financials-consequence").querySelector("[data-financials-range]")?.textContent;
    first.unmount();
    mount(client, URL);
    await settledScreen();
    expect(client.asked.bridge).toEqual([FREV, FREV]);
    expect(screen.getByTestId("where")).toHaveTextContent(`finding_id=${FINDING}&revision_id=${FREV}`);
    expect(card("financials-consequence").querySelector("[data-financials-range]")?.textContent).toBe(before);
  });

  it("W1-F3 (was: the Price in use panel draws the effective-time strip): Assumptions in use lists the price in use as key values", async () => {
    // The strip stays on Assumptions (tested there); the mock's "Assumptions in use" is a key-value list.
    mount(fake(), "/sites/KOBO-001/financials");
    await settledScreen();
    expectV69Panels("financials");
    const panel = panelTitled("Assumptions in use");
    expect(panel.querySelector("[data-key-value='price']")).toHaveTextContent("1.25 USD per litre");
    expect(panel.querySelector("[data-key-value='effective']")).toHaveTextContent("from 1 Jul 2026, with no end date");
    expect(within(panel).getByRole("link", { name: "Review assumptions" })).toHaveAttribute("href", "/sites/KOBO-001/financials/assumptions");
    expect(document.querySelector("[data-price-strip]")).toBeNull();
    // Height phase: price, effective period and set-by are visible; version, currency and basis are one click away.
    for (const key of ["price", "effective", "set-by"]) {
      expect(visibleOutsideClosedDisclosure(panel.querySelector(`[data-key-value='${key}']`)!), key).toBe(true);
    }
    const detail = panel.querySelector("details[data-disclosure='financials-price-detail']") as HTMLDetailsElement;
    expect(detail.open).toBe(false);
    for (const key of ["version", "currency", "basis"]) expect(detail.querySelector(`[data-key-value='${key}']`), key).not.toBeNull();
  });

  it.each([
    ["NO_PRICE", { state: "NO_PRICE", valid_at: "x", revision_id: null, assignment_id: null, note: "" }, /no price is recorded for today/],
    ["CONFLICT", { state: "CONFLICT", valid_at: "x", revision_id: null, assignment_id: null }, /two stored prices cover today/],
  ] as const)("W1-F3: Assumptions in use on %s shows no price and no default", async (name, selection, words) => {
    mount(
      fake({
        seriesFor: () => ({
          status: "loaded",
          value: series({
            selection: selection as never,
            timeline: [],
            revisions: [],
            revision_page: { after_revision_no: 0, limit: 200, total: 0, next_after_revision_no: null },
          }),
        }),
      }),
      "/sites/KOBO-001/financials",
    );
    await settledScreen();
    expectV69Panels("financials");
    const panel = panelTitled("Assumptions in use");
    expect(panel.querySelector(`[data-price-selection='${name}']`)).not.toBeNull();
    expect(panel.querySelector("[data-price-selection='PRICED']")).toBeNull();
    expect(panel.querySelector("[data-key-value='price']")?.textContent).toMatch(words);
    expect(panel.querySelector("[data-key-value='default']")).toHaveTextContent("None is used in its place");
    expect(panel.textContent).not.toMatch(/\d+\.\d\d USD/);
  });
});

describe("W1-UX-02: Site > Financials > Assumptions (assumptions)", () => {
  const ASSUMPTIONS = "/sites/KOBO-001/financials/assumptions";

  it("W1-UX-02: leads with the price in use, its effective-time strip and the W1 vocabulary; ids only in the disclosure", async () => {
    const { container } = mount(fake({ seriesFor: echoSeries }), ASSUMPTIONS);
    await settledScreen();
    const c = card("assumptions-price");
    // W1-F3 (was the answer card's question and headline): three v69 panels; the lead line names the price in use.
    expectV69Panels("assumptions");
    expect(c.querySelector("[data-price-selection='PRICED']")).toHaveTextContent(/^In use today\. Diesel price, set by .*1\.25 USD per litre/);
    expect(expectStateLineVisible(c)).toBe("Price recorded for this site");
    expect(c.querySelector("[data-product-status-as-of]")).toHaveTextContent(/^As of 16 Oct 2026, 09:30 UTC$/);
    expect(Array.from(c.querySelectorAll("[data-price-strip-entry]")).map((e) => e.getAttribute("data-price-strip-entry"))).toEqual([
      "ended",
      "ended",
      "in-use",
    ]);
    for (const id of within(c).getAllByText(V1)) expect(visibleOutsideClosedDisclosure(id)).toBe(false);
    expect(c.querySelector("[data-gap-id='G-assumptions-human-edit']")).toHaveAttribute("data-gap-placement", "assumptions.price.human-edit");
    expectW1Clean(container, c, "assumptions", 20);
  });

  it("W1-UX-02: an earlier recorded moment is its own state, with the moment as its bound, and survives reload", async () => {
    const at = "2026-10-13T09:00:00+00:00";
    const client = fake({ seriesFor: echoSeries });
    const path = `${ASSUMPTIONS}?recorded_at=${encodeURIComponent(at)}`;
    const first = mount(client, path);
    await settledScreen();
    expect(expectStateLineVisible(card("assumptions-price"))).toBe("Prices as recorded at an earlier moment");
    expect(card("assumptions-price").querySelector("[data-product-status-as-of]")).toHaveTextContent("As of 13 Oct 2026, 09:00 UTC");
    // M1: a past-cutoff list does not prove the price is in use now, so neither phrase appears.
    const priced = card("assumptions-price");
    expect(priced).toHaveTextContent("as recorded then");
    // W1-F3 (was: the headline): the whole price line, not only a headline, never says "in use".
    expect(priced.querySelector("[data-price-selection]")?.textContent ?? "").not.toMatch(/in use/i);
    expectV69Panels("assumptions");
    expect(priced.querySelector("[data-price-strip]")?.textContent ?? "").not.toMatch(/in use/i);
    expect(priced.querySelector("[data-price-strip-entry='in-use']")).toBeNull();
    expect(priced.querySelector("[data-price-strip-entry='recorded-then']")).not.toBeNull();
    first.unmount();
    const { container } = mount(client, path);
    await settledScreen();
    expect(client.asked.series.map((q) => q.recordedAt)).toEqual([at, at]);
    expect(expectStateLineVisible(card("assumptions-price"))).toBe("Prices as recorded at an earlier moment");
    expectW1Clean(container, card("assumptions-price"), "assumptions earlier moment", 20);
  });

  it("W1-UX-02: selecting a price version opens that exact version, marks it in the schedule and survives reload", async () => {
    const exact: FinancialReadResult<AssumptionRevisionBody> = {
      status: "loaded",
      value: { site_code: "KOBO-001", selection: { revision_id: V3, selected_by: "EXACT_REVISION_ID" }, revision: P3, assignments: [], recorded_by_this_publication: [] },
    };
    const client = fake({ seriesFor: echoSeries, exact });
    const first = mount(client, ASSUMPTIONS);
    await settledScreen();
    fireEvent.click(within(screen.getByRole("table", { name: "Price schedule" })).getByRole("link", { name: "Version 3" }));
    await settledScreen();
    expect(screen.getByTestId("where")).toHaveTextContent(`${ASSUMPTIONS}?revision_id=${V3}`);
    const version = screen.getByRole("region", { name: "Price version 3" });
    // W1-F3 review M5: the eyebrow that repeated "1.19 USD per litre" is gone; the version's field holds the price.
    expect(within(version).getByDisplayValue("1.19")).toBeInTheDocument();
    // W1-F3 review M5: the selected version's references are in the panel's one closed disclosure.
    expect(within(panelTitled("Financial assumptions")).getByText(V3).closest("details")).not.toHaveAttribute("open");
    expect(panelTitled("Financial assumptions").querySelectorAll("details[data-exact-references]")).toHaveLength(1);
    expect(document.querySelector(`tr[data-price-revision='${V3}']`)).toHaveClass("is-selected");
    // The current price line still names the current price; the selected version never replaces it (W1-F3: the
    // line in "Financial assumptions", was the answer card headline).
    expect(card("assumptions-price").querySelector("[data-price-selection='PRICED']")).toHaveTextContent("In use today. Diesel price");
    expect(card("assumptions-price").querySelector("[data-price-selection='PRICED']")).toHaveTextContent("1.25 USD per litre");
    expect(version.closest(".panel")).toBe(card("assumptions-price"));
    expectV69Panels("assumptions");
    first.unmount();
    mount(client, `${ASSUMPTIONS}?revision_id=${V3}`);
    await settledScreen();
    expect(client.asked.exact).toEqual([V3, V3]);
    expect(screen.getByRole("region", { name: "Price version 3" })).toBeInTheDocument();
  });

  it.each([
    ["NO_PRICE", { state: "NO_PRICE", valid_at: "x", revision_id: null, assignment_id: null, note: "" }, "No price recorded"],
    ["CONFLICT", { state: "CONFLICT", valid_at: "x", revision_id: null, assignment_id: null }, "Two prices cover this time"],
  ] as const)("W1-UX-02: %s states no price in use, never a default, with a visible state line", async (_name, selection, label) => {
    const { container } = mount(
      fake({
        seriesFor: (q) => ({
          status: "loaded",
          value: series({
            cutoff: { recorded_at: q.recordedAt ?? null, selected_by: "RECORDED_CUTOFF", basis: "x" },
            selection: selection as never,
            timeline: [],
            revisions: [],
            revision_page: { after_revision_no: 0, limit: 200, total: 0, next_after_revision_no: null },
          }),
        }),
      }),
      ASSUMPTIONS,
    );
    await settledScreen();
    const c = card("assumptions-price");
    expect(expectStateLineVisible(c)).toBe(label);
    expect(c.querySelector("[data-product-status]")).not.toHaveAttribute("data-product-status", "positive");
    expect(c.querySelector("[data-price-strip]")).toBeNull();
    expect(c.textContent ?? "").not.toMatch(/\d+\.\d\d USD/);
    expect(c.querySelector("[data-price-selection]")).toHaveTextContent("No price published");
    expectV69Panels("assumptions");
    expectW1Clean(container, c, `assumptions ${_name}`, 10);
  });

  it.each([
    ["unavailable", "This could not be read right now"],
    ["forbidden", "This cannot be shown to you"],
  ] as const)("W1-UX-02: a %s price list read keeps its own state line", async (status, label) => {
    mount(fake({ series: { status, message: null } }), ASSUMPTIONS);
    await settledScreen();
    expect(expectUntimedStateLine(document.querySelector(`[data-financials-state='${status}']`) as HTMLElement)).toBe(label);
    // W1-F3 (was: no price card): the panel skeleton stays with its gap, and no price line is drawn.
    expectV69Panels("assumptions");
    expect(document.querySelector("[data-price-selection]")).toBeNull();
    expect(card("assumptions-price").querySelector("[data-price-panel-gap]")).not.toBeNull();
  });

  it("W1-UX-02: the Interpretation history is recorded-only, with its moment as the bound and never a current amount", async () => {
    const rows = [
      hrow(H4),
      hrow(H3, { at_cutoff: "HISTORICAL_AT_CUTOFF", recorded_amount: { disposition: "UNPRICED", label: null, amount: null, is_current_amount: false }, price: { state: "NO_PRICE_LINK", price_revision_id: null, reason: "NO_PRICE", value: null, currency: null, assignments: [] } }),
    ];
    const { container } = mount(fake({ seriesFor: echoSeries, history: { status: "loaded", value: historyBody(rows) } }), ASSUMPTIONS);
    await settledScreen();
    const panel = screen.getByRole("region", { name: "Interpretation history" });
    const state = panel.querySelector("[data-history-state='recorded']") as HTMLElement;
    expect(expectStateLineVisible(state)).toBe("Recorded versions, kept for the record");
    expect(state.querySelector("[data-product-status]")).toHaveAttribute("data-product-status", "neutral");
    expect(state.querySelector("[data-product-status-as-of]")).toHaveTextContent("As of 16 Oct 2026, 09:30 UTC");
    // The no-current-amount guarantee: a recorded amount is labelled as history, never as current.
    expect(panel.querySelector(`[data-history-row='${H4}'] [data-history-recorded-amount]`)).toHaveTextContent("Not a current cost.");
    expect(panel).not.toHaveTextContent(/current amount|today.s (amount|cost)|the current fuel cost/i);
    expect(panel.querySelector("[data-value-bar='known']")).toBeNull();
    expect(panel.querySelector("[data-product-status='positive']")).toBeNull();
    for (const row of Array.from(panel.querySelectorAll("[data-history-row]"))) {
      const refs = row.querySelector("details[data-exact-references]") as HTMLDetailsElement;
      expect(refs.open).toBe(false);
    }
    const w1 = scanProductVocabulary(mainOf(container), "assumptions history (W1)", { set: "w1" });
    expect(w1.violations, describeViolations(w1.violations)).toEqual([]);
    const disclosure = scanDisclosureVocabulary(panel, "assumptions history disclosure");
    // W1-F3 review H3: the price versions are table rows too, each with its own closed exact reference (as the
    // two fuel cost rows); 2 fuel cost rows + 2 price version rows.
    expect(disclosure.disclosures).toBe(4);
    // W1-F3: the price versions recorded at the same moment are inside this panel.
    expect(panel.querySelector("[data-price-history-part] [data-price-history='loaded']")).not.toBeNull();
    expect(disclosure.scanned).toBeGreaterThan(0);
    expect(disclosure.violations, describeViolations(disclosure.violations)).toEqual([]);
  });

  it("W1-UX-02: an unreadable history and the unfixed price moment each keep a plain state line", async () => {
    mount(fake({ history: { status: "unavailable", message: null } }), ASSUMPTIONS);
    await settledScreen();
    expect(expectUntimedStateLine(document.querySelector("[data-history-state='unavailable']") as HTMLElement)).toBe(
      "This could not be read right now",
    );
    expect(expectUntimedStateLine(document.querySelector("[data-financials-state='no-cutoff']") as HTMLElement)).toBe(
      "This could not be read right now",
    );
    // W1-F3 (was: no price card): the panel skeleton stays with its gap, and no price line is drawn.
    expectV69Panels("assumptions");
    expect(document.querySelector("[data-price-selection]")).toBeNull();
  });
});
