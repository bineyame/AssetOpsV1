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
  type FinancialsClient,
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
      quantity_source: "fuel-cost-1",
      amount: null,
      currency: null,
      price_revision_id: null,
      reason: "No fuel quantity has been calculated for this finding yet, so no diesel price is applied and no cost is shown.",
    },
  };
}

interface Asked {
  series: SeriesQuery[];
  exact: string[];
  bridge: (string | null)[];
}

function fake(opts: {
  series?: FinancialReadResult<AssumptionSeriesBody>;
  exact?: FinancialReadResult<AssumptionRevisionBody>;
  bridge?: FinancialReadResult<FindingFinancialsBody>;
} = {}): FinancialsClient & { asked: Asked } {
  const asked: Asked = { series: [], exact: [], bridge: [] };
  return {
    asked,
    async getAssumptions(_site, query) {
      asked.series.push(query);
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
    await client.getAssumptions("KOBO-001", { validAt: "2026-10-13T00:00:00Z", recordedAt: "2026-10-13T09:00:00+00:00" });
    expect(calls).toEqual([
      "/api/sites/KOBO-001/financial-assumptions/rev%201",
      "/api/sites/KOBO-001/findings/f1/financials?revision_id=r%201",
      "/api/sites/KOBO-001/financial-assumptions?key=diesel_price_per_litre&valid_at=2026-10-13T00%3A00%3A00Z&recorded_at=2026-10-13T09%3A00%3A00%2B00%3A00",
    ]);
  });
});
