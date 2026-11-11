import { render, screen, within } from "@testing-library/react";
import { Route, Routes } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { outcomeWarning } from "../../test/outcomeBoardFixture";
import { LinkedMemoryRouter as MemoryRouter } from "../../test/refLinks";
import { settledScreen } from "../../test/settled";
import { PRICES_SIGN_IN_TEXT, SitePricesFrame } from "../../shell/SitePricesFrame";
import { SITE_PRICES_ROUTE_PATH, routeFor } from "../../shell/operatorSiteRoutes";
import { EarlyWarningList } from "../EarlyWarnings";
import { PriceActionLink, priceActionTarget, safeReturn, type PriceAction } from "../PriceAction";
import type { SiteDetailClient } from "../siteDirectoryClient";
import type { MillValue, MillVerification } from "../millVerificationClient";
import { MillVerificationBody } from "../SiteMillVerification";

/** PR-1 (BL-68): the server's price link on an unpriced item, and the honest target page until PR-2a. */

const SET: PriceAction = {
  kind: "SET_PRICE",
  key: "repair_visit_cost",
  label: "What pricing this needs →",
  href: "/sites/COLD-LAB-001/financials/prices?key=repair_visit_cost",
  link_ref: { kind: "PRICES", site: "COLD-LAB-001", key: "repair_visit_cost" },
};
const NEED: PriceAction = {
  kind: "NEEDS_MODEL",
  need_key: "battery_wear_model",
  text: "Battery wear is measured, not priced.",
  label: "What is needed to price this →",
  href: "/sites/KOBO-001/financials/prices?need=battery_wear_model",
  link_ref: { kind: "PRICES", site: "KOBO-001", need: "battery_wear_model" },
};

describe("PR-1 price action link", () => {
  it("routes a PRICES ref to the Site price page", () => {
    expect(routeFor(SET.link_ref)).toBe(SET.href);
    expect(routeFor(NEED.link_ref)).toBe(NEED.href);
  });

  it("adds the shared range and the way back", () => {
    const target = priceActionTarget("/sites/K/financials/prices?key=k", {
      pathname: "/portfolio",
      search: "?from=2026-10-01&to=2026-10-08&tab=x",
    });
    const url = new URL(target, "http://x");
    expect(url.pathname).toBe("/sites/K/financials/prices");
    expect(url.searchParams.get("key")).toBe("k");
    expect(url.searchParams.get("from")).toBe("2026-10-01");
    expect(url.searchParams.get("to")).toBe("2026-10-08");
    expect(url.searchParams.get("tab")).toBeNull();
    expect(url.searchParams.get("return")).toBe("/portfolio?from=2026-10-01&to=2026-10-08&tab=x");
  });

  it("accepts only a same-app return", () => {
    expect(safeReturn("/portfolio?from=a")).toBe("/portfolio?from=a");
    for (const bad of [null, "", "//evil.example", "https://evil.example", "/\\evil", "portfolio"]) expect(safeReturn(bad)).toBeNull();
  });

  it("renders the server's words and nothing without an action", () => {
    render(
      <MemoryRouter initialEntries={["/portfolio?from=2026-10-01"]}>
        <PriceActionLink action={NEED} />
        <PriceActionLink action={null} />
      </MemoryRouter>,
    );
    const links = screen.getAllByRole("link");
    expect(links).toHaveLength(1);
    expect(links[0]).toHaveTextContent("What is needed to price this →");
    expect(links[0]).toHaveAttribute("data-price-action", "NEEDS_MODEL");
    expect(links[0].getAttribute("href")).toContain("need=battery_wear_model");
    expect(links[0].getAttribute("href")).toContain("return=%2Fportfolio%3Ffrom%3D2026-10-01");
  });

  it("shows the link under an early warning that carries one, and none under one that does not", () => {
    render(
      <MemoryRouter>
        <EarlyWarningList warnings={[{ ...outcomeWarning(), price_action: SET }, { ...outcomeWarning(), key: "w-2" }]} showSite />
      </MemoryRouter>,
    );
    const items = Array.from(document.querySelectorAll("[data-early-warnings] ul > li")) as HTMLElement[];
    expect(items).toHaveLength(2);
    const set = within(items[0]).getByText("What pricing this needs →");
    expect(set.closest("a")?.getAttribute("href")).toMatch(/^\/sites\/COLD-LAB-001\/financials\/prices\?key=repair_visit_cost&return=/);
    expect(items[1].querySelector("[data-price-action]")).toBeNull();
  });
});

describe("PR-1 mill verification value without a price", () => {
  it("shows the productive-use price link under the unpriced line, and none when priced", () => {
    const unpriced: MillValue = {
      state: "UNPRICED", reason: "NO_PRICE", basis: "ESTIMATED_SALES_AT_DECLARED_PRICE", per_day: null,
      before_per_day: null, after_per_day: null, currency: null, price: null,
      text: "No sales estimate: no price per kWh is declared for productive users",
      cost_text: "No cost is recorded for this change",
      price_action: {
        kind: "SET_PRICE", key: "productive_use_price_per_kwh", label: "Set a productive-use price for this site →",
        href: "/sites/KOBO-001/financials/prices?key=productive_use_price_per_kwh",
        link_ref: { kind: "PRICES", site: "KOBO-001", key: "productive_use_price_per_kwh" },
      },
    };
    const body = { metrics: [], line: null, sentence: null, value: unpriced } as unknown as MillVerification;
    const { unmount } = render(
      <MemoryRouter>
        <MillVerificationBody state={{ status: "loaded", body }} />
      </MemoryRouter>,
    );
    const link = screen.getByRole("link", { name: "Set a productive-use price for this site →" });
    expect(link.getAttribute("href")).toMatch(/^\/sites\/KOBO-001\/financials\/prices\?key=productive_use_price_per_kwh&return=/);
    unmount();
    const priced = { ...body, value: { ...unpriced, state: "PRICED", price_action: undefined } } as unknown as MillVerification;
    render(
      <MemoryRouter>
        <MillVerificationBody state={{ status: "loaded", body: priced }} />
      </MemoryRouter>,
    );
    expect(document.querySelector("[data-price-action]")).toBeNull();
  });
});

const detail = {
  async getSite() {
    return { status: "loaded", site: { site_id: "KOBO-001", display_name: "Kobo" } } as never;
  },
} as unknown as SiteDetailClient;

function renderPrices(entry: string) {
  return render(
    <MemoryRouter initialEntries={[entry]}>
      <Routes>
        <Route path={SITE_PRICES_ROUTE_PATH} element={<SitePricesFrame detail={detail} />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("PR-1 price page target (until PR-2a)", () => {
  it("says plainly the page is not available yet, who sets prices, and offers the way back", async () => {
    renderPrices("/sites/KOBO-001/financials/prices?key=diesel_price_per_litre&return=%2Fportfolio%3Ffrom%3Da");
    await settledScreen();
    expect(screen.getByRole("heading", { level: 1, name: "Kobo · Prices" })).toBeInTheDocument();
    expect(screen.getByText(/Not available yet/)).toBeInTheDocument();
    expect(document.querySelector("[data-prices-sign-in]")).toHaveTextContent(PRICES_SIGN_IN_TEXT);
    expect(screen.getByRole("link", { name: "← Back to where you were" })).toHaveAttribute("href", "/portfolio?from=a");
    // No write path: no form, no input, no Save.
    expect(document.querySelector("form, input, button[type='submit']")).toBeNull();
    expect(screen.queryByRole("button", { name: /save/i })).toBeNull();
  });

  it("offers no way back for a foreign return", async () => {
    renderPrices("/sites/KOBO-001/financials/prices?return=%2F%2Fevil.example");
    await settledScreen();
    expect(screen.getByRole("heading", { level: 1, name: "Kobo · Prices" })).toBeInTheDocument();
    expect(document.querySelector("[data-price-return]")).toBeNull();
  });
});
