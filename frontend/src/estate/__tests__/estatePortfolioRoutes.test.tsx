/**
 * W3-03 run 2 (Lane A integration): the `/portfolio` shell route and rail item (`.agent/W3-03-build-spec.md`
 * closure 1 navigation, closure 4 S17/N9). Portfolio becomes the first live OPERATIONS root; the remaining
 * unavailable roots keep their closed multiset, and the estate Findings risk root still owns `/findings/risks`.
 */
import { render, screen, within } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import { PORTFOLIO_ROOT_PATH } from "../../shell/operatorSiteRoutes";
import type { SiteDetailClient, SiteDirectoryClient } from "../../sites/siteDirectoryClient";
import { HYBRID_MINI_GRID_SITE } from "../../sites/__tests__/sldFixtures";
import { settledScreen } from "../../test/settled";
import type { EstateClient } from "../estateClient";
import { PORTFOLIO_PATH } from "../portfolioWords";
import { fakeClient, findingsBody, loaded } from "./estateFixtures";
import { loadedPortfolio, portfolioBody } from "./portfolioFixtures";

const DIRECTORY: SiteDirectoryClient = { listSites: () => Promise.resolve({ status: "loaded", sites: [] }) };
const DETAIL: SiteDetailClient = { getSite: () => Promise.resolve({ status: "loaded", site: HYBRID_MINI_GRID_SITE }) };

function LocationProbe() {
  return <output data-location>{useLocation().pathname}</output>;
}

function estate(): EstateClient & { portfolioCalls: number } {
  const base = fakeClient((lens) => loaded(findingsBody(lens)));
  const client = {
    ...base,
    portfolioCalls: 0,
    portfolio: () => {
      client.portfolioCalls += 1;
      return Promise.resolve(loadedPortfolio(portfolioBody()));
    },
  };
  return client;
}

function renderAt(path: string, client: EstateClient) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App flags={featureFlagsWith(false)} siteDirectory={DIRECTORY} siteDetail={DETAIL} estateIndex={client} />
      <LocationProbe />
    </MemoryRouter>,
  );
}

describe("W3-03 Portfolio shell route", () => {
  it("test_w303_global_route_precedence_and_unavailable_multiset", async () => {
    expect(PORTFOLIO_ROOT_PATH).toBe(PORTFOLIO_PATH);
    const client = estate();
    const view = renderAt("/portfolio", client);
    await settledScreen();
    expect(screen.getByRole("main", { name: "Portfolio" })).toBeTruthy();
    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("Portfolio Value & Operations");
    expect(client.portfolioCalls).toBe(1);
    const rail = screen.getByRole("navigation", { name: "Operator routes" });
    const portfolio = within(rail).getByRole("link", { name: "Portfolio" });
    expect(portfolio.getAttribute("href")).toBe("/portfolio");
    expect(portfolio.getAttribute("aria-current")).toBe("page");
    const unavailable = Array.from(rail.querySelectorAll("li"))
      .filter((li) => li.querySelector("a") === null && li.querySelector(".nav-rail__label") !== null)
      .map((li) => li.querySelector(".nav-rail__label")?.textContent);
    // W6-01e: Operational records rail root is live.
    expect(unavailable).toEqual(["Assets", "Settings"]);
    view.unmount();

    // The risk root stays the estate Findings risk lens; it is not the Portfolio and not `/findings`.
    const second = estate();
    renderAt("/findings/risks", second);
    await settledScreen();
    expect(document.querySelector("[data-location]")?.textContent).toBe("/findings/risks");
    expect(screen.queryByRole("main", { name: "Portfolio" })).toBeNull();
    expect(second.portfolioCalls).toBe(0);
  });
});
