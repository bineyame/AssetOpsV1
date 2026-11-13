import { render, screen, within } from "@testing-library/react";
import { Route, Routes, useLocation } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { LinkedMemoryRouter as MemoryRouter } from "../../test/refLinks";
import { settledScreen } from "../../test/settled";
import { expectOneHeadline } from "../../test/headline";
import { SiteFinancialsFrame } from "../../shell/SiteAnalyticsFrames";
import { PRICES_SIGN_IN_TEXT, SitePricesFrame } from "../../shell/SitePricesFrame";
import { SITE_FINANCIAL_ASSUMPTIONS_ROUTE_PATH, SITE_PRICES_ROUTE_PATH } from "../../shell/operatorSiteRoutes";
import type { FinancialsClient } from "../financialsClient";
import { createPricePageClient, type PricePage, type PricePageClient, type PriceRowBody } from "../pricePageClient";
import type { SiteDetailClient } from "../siteDirectoryClient";

const FUTURE_NOTE = "Saving this price comes once a figure uses it.";

const DIESEL: PriceRowBody = {
  key: "diesel_price_per_litre",
  noun: "diesel price",
  label: "Diesel price",
  detail: "backup generator fuel",
  stored: true,
  state: "SET",
  not_set_text: null,
  note: null,
  current: {
    revision_id: "r3",
    value: "1.4200",
    currency: "USD",
    unit: "currency/L",
    value_text: "1.42 USD per litre",
    amount_text: "1.42",
    per_text: "USD per litre",
    basis_text: "A contract rate",
    source_reference: "Supplier contract SC-88",
    applies_from_text: "1 Sep 2026",
    applies_until_text: null,
    set_by_label: "Entered by site admin",
    recorded_text: "recorded 2 Sep 2026, 09:14",
  },
  used_by: { text: "Fuel cost", detail: "Backup running days" },
  history_title: "History of the diesel price · 2 versions",
  history: [
    {
      revision_id: "r3",
      revision_no: 2,
      change_kind: "CORRECTION",
      headline: "Correction from 1 Sep 2026",
      until_text: null,
      value_text: "1.42 USD per litre",
      basis_text: "a contract rate",
      source_reference: "Supplier contract SC-88",
      reason: "supplier contract rate replaces the estimate",
      set_by_label: "Entered by site admin",
      recorded_text: "recorded 2 Sep 2026, 09:14",
      replaced: false,
      replaced_text: null,
    },
    {
      revision_id: "r1",
      revision_no: 1,
      change_kind: "INITIAL",
      headline: "First price from 1 Aug 2026",
      until_text: null,
      value_text: "1.38 USD per litre",
      basis_text: "an estimate",
      source_reference: null,
      reason: null,
      set_by_label: "AssetOps administrator",
      recorded_text: "recorded 1 Aug 2026, 10:30",
      replaced: true,
      replaced_text: "replaced by a later correction",
    },
  ],
};

const notSet = (key: string, label: string, stored: boolean): PriceRowBody => ({
  key,
  noun: label.toLowerCase(),
  label,
  detail: "detail",
  stored,
  state: "NOT_SET",
  current: null,
  not_set_text: "Not set",
  note: stored ? null : FUTURE_NOTE,
  used_by: { text: "Used", detail: "by something" },
  history: [],
  history_title: null,
});

const PAGE: PricePage = {
  site_code: "KOBO-001",
  site_name: "Kobo",
  title: "Kobo · Prices",
  intro: "intro",
  sign_in_text: PRICES_SIGN_IN_TEXT,
  table_title: "All prices for Kobo",
  table_note: "One row per price.",
  count_text: "3 prices · 1 set",
  cutoff: { known_at: null, text: null },
  prices: [DIESEL, notSet("productive_use_price_per_kwh", "Productive-use price", true), notSet("repair_visit_cost", "Cost per visit", false)],
  need: null,
};

const detail = {
  async getSite() {
    return { status: "loaded", site: { site_id: "KOBO-001", display_name: "Kobo", site_type: "MINIGRID" } } as never;
  },
} as unknown as SiteDetailClient;

function fakeClient(page: PricePage | null = PAGE, status: "not_found" | "unavailable" = "unavailable") {
  const calls: { siteId: string; need?: string | null; knownAt?: string | null }[] = [];
  const client: PricePageClient = {
    async getPrices(siteId, query) {
      calls.push({ siteId, ...query });
      return page === null ? { status, message: null } : { status: "loaded", value: page };
    },
  };
  return { client, calls };
}

function renderPrices(entry: string, client: PricePageClient = fakeClient().client) {
  return render(
    <MemoryRouter initialEntries={[entry]}>
      <Routes>
        <Route path={SITE_PRICES_ROUTE_PATH} element={<SitePricesFrame detail={detail} client={client} />} />
      </Routes>
    </MemoryRouter>,
  );
}

const row = (key: string) => document.querySelector(`[data-price-row="${key}"]`) as HTMLElement;

describe("PR-2a Site price page", () => {
  it("shows the server's intro as the subtitle, and a capped History says so (review L2, L4)", async () => {
    const capped = { ...DIESEL, history_capped_text: "Only the newest 200 versions are shown." };
    const { client } = fakeClient({ ...PAGE, intro: "The server's own intro.", prices: [capped, ...PAGE.prices.slice(1)] });
    renderPrices("/sites/KOBO-001/financials/prices", client);
    await settledScreen();
    expect(screen.getByText("The server's own intro.")).toBeInTheDocument();
    expect(document.querySelector("[data-price-history-capped]")).toHaveTextContent("Only the newest 200 versions are shown.");
  });

  it("a 422 does not read as a missing site (review L1)", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response(JSON.stringify({ detail: { code: "INSTANT_NOT_ZONED", message: "known_at must carry a timezone offset." } }), { status: 422 })),
    );
    renderPrices("/sites/KOBO-001/financials/prices?known_at=2026-10-01T00:00:00", createPricePageClient());
    await settledScreen();
    const refused = document.querySelector("[data-prices-refused]") as HTMLElement;
    expect(refused).toHaveAttribute("data-prices-refused", "invalid");
    expect(refused).toHaveTextContent("known_at must carry a timezone offset.");
    expect(refused).not.toHaveTextContent("No prices can be read for this site.");
    vi.unstubAllGlobals();
  });

  it("lists every price with the server's words, the sign-in line, and no form or Save", async () => {
    renderPrices("/sites/KOBO-001/financials/prices");
    await settledScreen();
    expect(screen.getByRole("heading", { level: 1, name: "Kobo · Prices" })).toBeInTheDocument();
    // UQ-FI-2 (rev 6 6.1 P8): one h1, the page title, first in its header (tokens only on this page).
    expectOneHeadline("Kobo · Prices");
    expect(screen.getByRole("heading", { name: "All prices for Kobo" })).toBeInTheDocument();
    expect(screen.getByText("3 prices · 1 set")).toBeInTheDocument();
    expect(document.querySelector("[data-prices-sign-in]")).toHaveTextContent(PRICES_SIGN_IN_TEXT);
    const headers = screen.getAllByRole("columnheader").map((h) => h.textContent);
    expect(headers).toEqual(["Price", "Current value", "Basis", "Applies from", "Set by", "Used by"]);
    const diesel = row("diesel_price_per_litre");
    expect(diesel).toHaveTextContent("1.42 USD per litre");
    expect(diesel).toHaveTextContent("A contract rate");
    expect(diesel).toHaveTextContent("Supplier contract SC-88");
    expect(diesel).toHaveTextContent("1 Sep 2026");
    expect(diesel).toHaveTextContent("Entered by site admin");
    expect(diesel).toHaveTextContent("Fuel cost");
    // No write path in PR-2a: no form, no input, no button, no slot row.
    expect(document.querySelector("form, input, select, textarea, button")).toBeNull();
    expect(document.querySelector("[data-price-slot]")).toBeNull();
    expect(screen.queryByText(/not available yet/i)).toBeNull();
  });

  it("shows History newest first with change kinds, reasons, Set by and replaced versions", async () => {
    renderPrices("/sites/KOBO-001/financials/prices");
    await settledScreen();
    const history = document.querySelector('[data-price-history="diesel_price_per_litre"]') as HTMLElement;
    expect(within(history).getByText("History of the diesel price · 2 versions")).toBeInTheDocument();
    const items = within(history).getAllByRole("listitem");
    expect(items[0]).toHaveTextContent('Correction from 1 Sep 2026: 1.42 USD per litre, a contract rate. Reason: "supplier contract rate replaces the estimate"');
    expect(items[0]).toHaveTextContent("Entered by site admin");
    expect(items[1]).toHaveTextContent("First price from 1 Aug 2026: 1.38 USD per litre, an estimate");
    expect(items[1]).toHaveTextContent("AssetOps administrator · recorded 1 Aug 2026, 10:30 · replaced by a later correction");
    expect(document.querySelector('[data-price-history="repair_visit_cost"]')).toBeNull();
  });

  it("shows a stored key that is not set as Not set, and a future key with its sentence and no button", async () => {
    renderPrices("/sites/KOBO-001/financials/prices");
    await settledScreen();
    const stored = row("productive_use_price_per_kwh");
    expect(stored).toHaveTextContent("Not set");
    expect(stored).not.toHaveTextContent(FUTURE_NOTE);
    const future = row("repair_visit_cost");
    expect(future).toHaveTextContent("Not set");
    expect(future).toHaveTextContent(FUTURE_NOTE);
    expect(within(future).queryByRole("button")).toBeNull();
    expect(within(future).queryByRole("link")).toBeNull();
  });

  it("highlights the row the reader came to price and keeps the way back and the range", async () => {
    const { client, calls } = fakeClient();
    renderPrices(
      "/sites/KOBO-001/financials/prices?key=repair_visit_cost&from=2026-10-01&to=2026-10-07&known_at=2026-10-08T00%3A00%3A00Z&return=%2Fportfolio%3Ffrom%3Da",
      client,
    );
    await settledScreen();
    expect(row("repair_visit_cost")).toHaveAttribute("data-price-focused");
    expect(row("diesel_price_per_litre")).not.toHaveAttribute("data-price-focused");
    expect(screen.getByRole("link", { name: "← Back to where you were" })).toHaveAttribute("href", "/portfolio?from=a");
    expect(screen.getByText("Your date range is kept.")).toBeInTheDocument();
    expect(calls).toEqual([{ siteId: "KOBO-001", need: null, knownAt: "2026-10-08T00:00:00Z" }]);
    const subtabs = screen.getByRole("navigation", { name: "Financials sections" });
    const links = within(subtabs).getAllByRole("link");
    expect(links.map((l) => l.textContent)).toEqual(["Overview", "Prices", "Scenarios"]);
    expect(links[1]).toHaveAttribute("aria-current", "page");
    expect(links[0].getAttribute("href")).toContain("from=2026-10-01");
  });

  it("offers no way back for a foreign return", async () => {
    renderPrices("/sites/KOBO-001/financials/prices?return=%2F%2Fevil.example");
    await settledScreen();
    expect(screen.getByRole("heading", { level: 1, name: "Kobo · Prices" })).toBeInTheDocument();
    expect(document.querySelector("[data-price-return]")).toBeNull();
  });

  it("opens Part C for a need, with the server's words and no 'Tell your contact'", async () => {
    const need = {
      need_key: "battery_wear_model",
      title: "What is needed to price this",
      text: "Battery wear is measured, not priced.",
      meanwhile: "What AssetOps shows meanwhile: the measurements, never an amount, a range or \"≈\".",
      link_label: "What is needed to price this →",
    };
    const { client, calls } = fakeClient({ ...PAGE, need });
    renderPrices("/sites/KOBO-001/financials/prices?need=battery_wear_model", client);
    await settledScreen();
    expect(calls[0].need).toBe("battery_wear_model");
    const block = document.querySelector('[data-price-need="battery_wear_model"]') as HTMLElement;
    expect(within(block).getByRole("heading", { name: "What is needed to price this" })).toBeInTheDocument();
    expect(block).toHaveTextContent("Battery wear is measured, not priced.");
    expect(screen.queryByText(/tell your/i)).toBeNull();
  });

  it("says the cutoff when the page reads prices as known at a time", async () => {
    const { client } = fakeClient({ ...PAGE, cutoff: { known_at: "2026-10-08T00:00:00Z", text: "Prices as known at 8 Oct 2026, 03:00." } });
    renderPrices("/sites/KOBO-001/financials/prices?known_at=2026-10-08T00%3A00%3A00Z", client);
    await settledScreen();
    expect(document.querySelector("[data-prices-cutoff]")).toHaveTextContent("Prices as known at 8 Oct 2026, 03:00.");
  });

  it("states a refused or failed read plainly", async () => {
    renderPrices("/sites/KOBO-001/financials/prices", fakeClient(null, "unavailable").client);
    await settledScreen();
    expect(document.querySelector('[data-prices-refused="unavailable"]')).toHaveTextContent("The prices cannot be read right now.");
    expect(document.querySelector("[data-price-row]")).toBeNull();
  });

  it("hosts PR-3's inline content under one row through the renderBelow seam", async () => {
    render(
      <MemoryRouter initialEntries={["/sites/KOBO-001/financials/prices"]}>
        <Routes>
          <Route
            path={SITE_PRICES_ROUTE_PATH}
            element={
              <SitePricesFrame
                detail={detail}
                client={fakeClient().client}
                renderBelow={(r) => (r.stored ? <span data-test-slot={r.key}>slot</span> : null)}
              />
            }
          />
        </Routes>
      </MemoryRouter>,
    );
    await settledScreen();
    const slots = Array.from(document.querySelectorAll("[data-price-slot]")).map((s) => s.getAttribute("data-price-slot"));
    expect(slots).toEqual(["diesel_price_per_litre", "productive_use_price_per_kwh"]);
    // The slot row sits directly under its price row, before the History row.
    const dieselRow = row("diesel_price_per_litre");
    expect(dieselRow.nextElementSibling).toHaveAttribute("data-price-slot", "diesel_price_per_litre");
    expect(dieselRow.nextElementSibling?.nextElementSibling).toHaveAttribute("data-price-history", "diesel_price_per_litre");
  });
});

function Probe() {
  const location = useLocation();
  return <p data-probe={`${location.pathname}${location.search}`}>probe</p>;
}

describe("PR-2a old Assumptions address (default 2)", () => {
  const financials = new Proxy({}, { get: () => async () => ({ status: "unavailable", message: null }) }) as unknown as FinancialsClient;
  function mountAt(entry: string) {
    return render(
      <MemoryRouter initialEntries={[entry]}>
        <Routes>
          <Route
            path={SITE_FINANCIAL_ASSUMPTIONS_ROUTE_PATH}
            element={<SiteFinancialsFrame detail={detail} sitesPath="/sites" view="assumptions" financials={financials} forwardBareAssumptions />}
          />
          <Route path={SITE_PRICES_ROUTE_PATH} element={<Probe />} />
        </Routes>
      </MemoryRouter>,
    );
  }

  it("forwards the bare address to the price page and keeps the shared range", async () => {
    mountAt("/sites/KOBO-001/financials/assumptions?from=2026-10-01&to=2026-10-07&known_at=2026-10-08T00%3A00%3A00Z");
    const probe = await screen.findByText("probe");
    expect(probe).toHaveAttribute(
      "data-probe",
      "/sites/KOBO-001/financials/prices?from=2026-10-01&to=2026-10-07&known_at=2026-10-08T00%3A00%3A00Z",
    );
  });

  it("keeps a pinned price version (the money 'Why?' target) on its own screen, under the Prices subtab", async () => {
    mountAt("/sites/KOBO-001/financials/assumptions?revision_id=r1");
    await settledScreen();
    expect(document.querySelector("[data-probe]")).toBeNull();
    const sections = screen.getByRole("navigation", { name: "Financials sections" });
    expect(within(sections).getByRole("link", { name: "Prices" })).toHaveAttribute("aria-current", "page");
  });
});

describe("PR-2a price page client", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("reads /api/sites/{site}/prices with need and known_at, and maps refusals", async () => {
    const fetchMock = vi.fn(async () => new Response(JSON.stringify(PAGE), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    const result = await createPricePageClient().getPrices("KOBO-001", { need: "bus_roster", knownAt: "2026-10-08T00:00:00Z" });
    expect(result.status).toBe("loaded");
    expect(fetchMock).toHaveBeenCalledWith("/api/sites/KOBO-001/prices?need=bus_roster&known_at=2026-10-08T00%3A00%3A00Z");
    for (const [status, mapped] of [
      [403, "forbidden"],
      [404, "not_found"],
      [503, "unavailable"],
    ] as const) {
      vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify({ detail: { message: "m" } }), { status })));
      expect((await createPricePageClient().getPrices("KOBO-001", {})).status).toBe(mapped);
    }
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify({ bogus: true }), { status: 200 })));
    expect((await createPricePageClient().getPrices("KOBO-001", {})).status).toBe("unavailable");
  });
});
