import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { SiteFinancialsFrame } from "../../shell/SiteAnalyticsFrames";
import { settledScreen } from "../../test/settled";
import { describeViolations, scanProductVocabulary } from "../../test/productVocabulary";
import {
  createFinancialsClient,
  type AssumptionRevisionBody,
  type AssumptionSeriesBody,
  type FinancialReadResult,
  type ConsequencePin,
  type ConsequenceRevision,
  type FinancialsClient,
  type FindingConsequence,
  type FindingConsequencesBody,
  type FindingFinancialsBody,
  type PriceRevision,
  type SeriesQuery,
} from "../financialsClient";
import type { SiteDetailClient } from "../siteDirectoryClient";

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

function pricedBridge(patch: Partial<FindingConsequence> = {}): FindingFinancialsBody {
  const base = bridgeBody();
  return {
    ...base,
    window: { start: "2026-10-23T06:05:00+00:00", end: "2026-10-23T08:00:00+00:00" },
    demonstration: {
      label: "Demonstration data",
      statement:
        "This finding comes from demonstration readings written by the AssetOps team to show a complete fuel-cost calculation. They are not measurements from a working generator.",
      case_id: "P01-power",
      spec: "s4-power-demo-cases-v1",
    },
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
}

function fake(opts: {
  series?: FinancialReadResult<AssumptionSeriesBody>;
  exact?: FinancialReadResult<AssumptionRevisionBody>;
  bridge?: FinancialReadResult<FindingFinancialsBody>;
  consequences?: FinancialReadResult<FindingConsequencesBody> | ((pin: ConsequencePin) => FinancialReadResult<FindingConsequencesBody>);
  seriesFor?: (query: SeriesQuery) => FinancialReadResult<AssumptionSeriesBody>;
} = {}): FinancialsClient & { asked: Asked } {
  const asked: Asked = { series: [], exact: [], bridge: [], consequences: [] };
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
    const panel = screen.getByRole("region", { name: "Site diesel price" });
    expect(panel).toHaveTextContent(/Diesel price, set by the system on 13 Oct 2026: 1\.25 USD per litre, from 1 Jul 2026, with no end date\./);
    expect(panel.querySelector("[data-price-selection='PRICED']")).toHaveAttribute("data-price-selected-revision", V1);
    // The ID is rendered only inside a closed disclosure.
    const id = within(panel).getAllByText(V1)[0];
    expect(id.closest("details")).not.toHaveAttribute("open");
    expect(client.asked.series[0]).toMatchObject({ recordedAt: null, afterRevisionNo: 0 });
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
    expect(screen.getByRole("region", { name: "Price version 1" })).toHaveTextContent("1.25 USD per litre");
  });

  it("never substitutes the latest price for an unknown or foreign version", async () => {
    const client = fake({ exact: { status: "not_found", message: "No such price revision for this Site" } });
    mount(client, "/sites/KOBO-001/financials/assumptions?revision_id=nope");
    await settledScreen();
    expect(screen.getByRole("region", { name: "No such price version" })).toBeInTheDocument();
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
    expect(screen.getByRole("heading", { name: heading })).toBeInTheDocument();
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
    expect(screen.getByText("No price for the whole window")).toBeInTheDocument();
  });

  it("a foreign or unknown Finding version is refused, never replaced", async () => {
    mount(fake({ bridge: { status: "not_found", message: null } }), `/sites/KOBO-001/financials?finding_id=${FINDING}&revision_id=bad`);
    await settledScreen();
    expect(screen.getByRole("heading", { name: "No such finding version" })).toBeInTheDocument();
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
    expect(bridge).toHaveTextContent(
      "Modelled potential fuel-cost exposure: 0.00 to 16.20 USD, under the reviewed fuel-cost-1 assumptions. This is not measured fuel saved or a physical maximum.",
    );
    expect(bridge.querySelector("[data-financials-demonstration='P01-power']")).toHaveTextContent("Demonstration data");
    expect(container.textContent ?? "").not.toMatch(/simulat/i);
    expect(bridge.querySelector("[data-bridge-amount]")).toHaveAttribute("data-bridge-amount", "current");
    expect(bridge.querySelector("[data-bridge-step='fuel']")).toHaveTextContent("0 to 12.65 litres");
    expect(bridge.querySelector("[data-bridge-step='price']")).toHaveTextContent("1.28 USD per litre");
    expect(within(bridge).getByRole("link", { name: "The site price version used" })).toHaveAttribute(
      "href",
      `/sites/KOBO-001/financials/assumptions?revision_id=${V4}`,
    );
    // identifiers, the model version and enum names only inside the closed disclosure
    const details = within(bridge).getByText("How this is worked out").closest("details") as HTMLElement;
    expect(details).not.toHaveAttribute("open");
    expect(details).toHaveTextContent("MODELLED_CONDITIONAL");
    expect(details).toHaveTextContent("sfc_upper_multiplier = 1.10");
    expect(details.querySelector("[data-consequence-reading='ev-1']")).not.toBeNull();
    const outside = bridge.cloneNode(true) as HTMLElement;
    outside.querySelectorAll("details").forEach((d) => d.remove());
    expect(outside.textContent ?? "").not.toMatch(/MODELLED_CONDITIONAL|POTENTIAL_FUEL_COST|c2000000/);
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
      expect(document.querySelector(`[data-consequence-revision='${C1}']`)).toHaveAttribute(
        "data-consequence-current",
        "false",
      );
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
    expect(document.querySelector(`[data-consequence-revision='${C1}']`)).toHaveAttribute("data-consequence-current", "false");
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
    const history = document.querySelector("[data-consequence-history='loaded']") as HTMLElement;
    expect(history.querySelectorAll("[data-consequence-revision]")).toHaveLength(2);
    expect(history.querySelector(`[data-consequence-revision='${C2}']`)).toHaveAttribute("data-consequence-current", "true");
    expect(history.querySelector(`[data-consequence-revision='${C1}']`)).toHaveTextContent("kept for the record");
    expect(screen.getByText(/The fuel amount is the same in every version shown/)).toBeInTheDocument();
    fireEvent.click(within(history).getByRole("link", { name: "Open fuel cost version 1" }));
    await settledScreen();
    expect(screen.getByTestId("where")).toHaveTextContent(`consequence_revision_id=${C1}`);
    const pinned = document.querySelector(`[data-consequence-pinned='${C1}']`) as HTMLElement;
    expect(pinned).toHaveTextContent("0.00 to 15.82 USD");
    expect(pinned).toHaveTextContent("1.25 USD per litre");
    expect(pinned.querySelector("[data-bridge-amount]")).toHaveAttribute("data-bridge-amount", "recorded");
    expect(pinned).toHaveTextContent("Its fuel amount is the same as in the latest version; only the price applied differs.");
    expect(document.querySelector("[data-financials-bridge]")).toHaveAttribute("data-finding-revision", FREV);
    first.unmount();
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
    expect(screen.getByText(/Showing 2 of 2 versions/)).toBeInTheDocument();
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

  function gate(state: "WITHHELD_GENERATOR_SERIES" | "PENDING_REASSESSMENT") {
    return {
      version: "money-eligibility-1", state, note: "", finding_id: FINDING, latest_finding_revision_id: FREV,
      pending_reasons: state === "PENDING_REASSESSMENT" ? ["LIVE_JOB: DAY 2026-10-23 j1"] : [],
      series_limits: state === "WITHHELD_GENERATOR_SERIES" ? [LIMIT] : [], windows: [],
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
    expect(bridge).toHaveTextContent("Withheld: the generator records are not in a proven time order");
    expect(bridge.querySelector("[data-financials-series-limit='SEQUENCE_ORDER_INVERTED']")).toHaveTextContent(
      "arrived out of order and their clock is not proven",
    );
    const link = bridge.querySelector(`[data-financials-recorded-link='${C1}']`) as HTMLAnchorElement;
    expect(link.getAttribute("href")).toContain(`consequence_revision_id=${C1}`);
    const row = document.querySelector(`[data-consequence-revision='${C1}']`) as HTMLElement;
    expect(row).toHaveAttribute("data-consequence-current", "false");
    expect(row).toHaveTextContent("7.57 USD");
    expect(row).toHaveTextContent("kept for the record");
    expect(document.body.textContent ?? "").not.toMatch(/the current fuel cost/);
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
    expect(bridge).toHaveTextContent("Being reassessed: no current cost yet");
    expect(bridge.querySelector("[data-financials-pending-reassessment='true']")).not.toBeNull();
    expect(bridge.querySelector(`[data-financials-recorded-link='${C1}']`)).not.toBeNull();
  });
});
