/**
 * W3-03 run 2 (Lane A integration): the `/portfolio` shell route and rail item (`.agent/W3-03-build-spec.md`
 * closure 1 navigation, closure 4 S17/N9). Portfolio becomes the first live OPERATIONS root; the remaining
 * unavailable roots keep their closed multiset, and the estate Findings risk root still owns `/findings/risks`.
 */
import { fireEvent, render, screen, within } from "@testing-library/react";
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
  const location = useLocation();
  return <output data-location>{`${location.pathname}${location.search}`}</output>;
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
    // SR-1: the shell filled the empty address with the default range, and the rail carries it.
    expect(portfolio.getAttribute("href")).toBe(`/portfolio${document.querySelector("[data-location]")?.textContent?.slice("/portfolio".length)}`);
    expect(document.querySelector("[data-location]")?.textContent).toMatch(/^\/portfolio\?from=\d{4}-\d{2}-\d{2}T00%3A00%3A00Z&to=\d{4}-\d{2}-\d{2}T00%3A00%3A00Z$/);
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
    // SR-1: the shell fills the empty estate address with the shared range; the path is unchanged.
    expect(document.querySelector("[data-location]")?.textContent).toMatch(/^\/findings\/risks\?from=[^&]+&to=[^&]+$/);
    expect(screen.queryByRole("main", { name: "Portfolio" })).toBeNull();
    expect(second.portfolioCalls).toBe(0);
  });
});

/** PF-T: one mounted route `/portfolio/:tab?`, the old lens address and an unknown tab. */
describe("PF-T Portfolio tab routes", () => {
  const WINDOW = "from=2026-10-06T00%3A00%3A00Z&to=2026-10-07T00%3A00%3A00Z";
  const where = () => document.querySelector("[data-location]")?.textContent;
  const tabRow = () => screen.getByRole("navigation", { name: "Portfolio sections" });

  it("a tab switch stays on the one mounted route and does not read again", async () => {
    const client = estate();
    renderAt(`/portfolio?${WINDOW}`, client);
    await settledScreen();
    const main = screen.getByRole("main", { name: "Portfolio" });
    fireEvent.click(within(tabRow()).getByRole("link", { name: /^What changed/ }));
    await settledScreen();
    expect(where()).toBe(`/portfolio/changes?${WINDOW}`);
    expect(screen.getByRole("main", { name: "Portfolio" })).toBe(main);
    expect(client.portfolioCalls).toBe(1);
  });

  it("an old /portfolio?lens=X address redirects to /portfolio/act-first?lens=X", async () => {
    const client = estate();
    renderAt(`/portfolio?${WINDOW}&lens=risks`, client);
    await settledScreen();
    expect(where()).toBe(`/portfolio/act-first?${WINDOW}&lens=risks`);
    expect(client.portfolioCalls).toBe(1);
  });

  it("an unknown tab redirects to Overview", async () => {
    renderAt(`/portfolio/nonsense?${WINDOW}`, estate());
    await settledScreen();
    expect(where()).toBe(`/portfolio?${WINDOW}`);
    expect(within(tabRow()).getByRole("link", { current: "page" }).querySelector("[data-pf-tab-label]")?.textContent).toBe("Overview");
  });
});
