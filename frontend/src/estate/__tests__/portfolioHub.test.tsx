/**
 * IA-P P3b (spec §3, §6 P3b; handshake I1, I3, R2): the Portfolio hub on the top-bar range. The Overview reads E2
 * (`/api/portfolio/period`) for the address's range and renders by mode; the three tabs keep the range; the old
 * `/portfolio/month?month=` address is an alias to the month's days. E2 bodies are the committed IA-P fixtures
 * (written by `backend/tests/test_iap_portfolio_period.py` test 10), never by hand.
 */
import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";
import { beforeEach, describe, expect, it } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import type { SiteDetailClient, SiteDirectoryClient } from "../../sites/siteDirectoryClient";
import { HYBRID_MINI_GRID_SITE } from "../../sites/__tests__/sldFixtures";
import { settledScreen } from "../../test/settled";
import { entryRange, presetRange, readSharedRange } from "../../ui/sharedRange";
import type { DeepDiveMonthBody, DeepDiveMonthClient } from "../deepDiveMonthClient";
import type { EstateClient, EstatePortfolioRow } from "../estateClient";
import type { PeriodResult, PortfolioPeriod, PortfolioPeriodClient } from "../portfolioPeriodClient";
import { PORTFOLIO_TABS } from "../portfolioWords";
import { loaded } from "./estateFixtures";
import { portfolioBody, row } from "./portfolioFixtures";
import WORLD_A from "../../../../backend/tests/fixtures/5c/deep_dive_lakeside_2026-10.json?raw";
import MONTH_G from "./fixtures/iap/month-g-2026-10.json?raw";
import PERIOD_MONTH from "./fixtures/iap/period-month-2026-10.json?raw";
import PERIOD_MONTH_G from "./fixtures/iap/period-month-g-2026-10.json?raw";
import PERIOD_NONE from "./fixtures/iap/period-none-2026-11.json?raw";
import PERIOD_PERIOD from "./fixtures/iap/period-period-2026-09-10.json?raw";
import PERIOD_PERIOD_G from "./fixtures/iap/period-period-g-2026-09-10.json?raw";

const DIRECTORY: SiteDirectoryClient = { listSites: () => Promise.resolve({ status: "loaded", sites: [] }) };
const DETAIL: SiteDetailClient = { getSite: () => Promise.resolve({ status: "loaded", site: HYBRID_MINI_GRID_SITE }) };

const parse = <T,>(text: string): T => JSON.parse(text) as T;

beforeEach(() => {
  window.sessionStorage.clear();
});

function periodClient(body: PortfolioPeriod): PortfolioPeriodClient & { calls: [string, string][] } {
  const calls: [string, string][] = [];
  return {
    calls,
    fetchPeriod: (from, to) => {
      calls.push([from, to]);
      return Promise.resolve<PeriodResult>({ status: "loaded", body });
    },
  };
}

function monthClient(body: DeepDiveMonthBody = parse(WORLD_A)): DeepDiveMonthClient & { calls: (string | undefined)[] } {
  const calls: (string | undefined)[] = [];
  return {
    calls,
    fetchDeepDiveMonth: (month?: string) => {
      calls.push(month);
      return Promise.resolve({ status: "loaded", body });
    },
  };
}

function decisionRows(n: number): EstatePortfolioRow[] {
  return Array.from({ length: n }, (_, k) => {
    const id = `f1f1f1f1-0000-4000-8000-${String(k + 1).padStart(12, "0")}`;
    return row({ finding_id: id, finding_revision_id: id.replace("f1f1f1f1", "e1e1e1e1"), title: `Decision ${k + 1}` });
  });
}

function estateClient(n = 9): EstateClient & { calls: { from: string; to: string }[] } {
  const calls: { from: string; to: string }[] = [];
  const rows = decisionRows(n);
  return {
    calls,
    findings: () => Promise.reject(new Error("no findings")),
    actions: () => Promise.reject(new Error("no actions")),
    scope: () => Promise.reject(new Error("no scope")),
    portfolio: (query) => {
      calls.push({ from: query.from, to: query.to });
      return Promise.resolve(loaded(portfolioBody({ rows, total_count: rows.length, next_cursor: null })));
    },
  };
}

function LocationProbe() {
  const location = useLocation();
  return <div data-location>{`${location.pathname}${location.search}`}</div>;
}

function renderAt(path: string, period: PortfolioPeriod, month = monthClient(), estate = estateClient()) {
  const e2 = periodClient(period);
  render(
    <MemoryRouter initialEntries={[path]}>
      <App flags={featureFlagsWith(false)} siteDirectory={DIRECTORY} siteDetail={DETAIL} estateIndex={estate} deepDive={month} portfolioPeriod={e2} />
      <LocationProbe />
    </MemoryRouter>,
  );
  return { e2, month, estate };
}

async function settled() {
  await settledScreen();
  expect(document.body.textContent).not.toContain("Preparing the figures…");
  expect(document.body.textContent).not.toContain("Preparing the month…");
}

const location = () => document.querySelector("[data-location]")!.textContent;
const tabs = () => document.querySelector<HTMLElement>('[data-section-tabs="Portfolio sections"]')!;
const OCT = "from=2026-10-01&to=2026-10-31";
/** An address as its path and the range's days (the tab links write the range's instant form). */
function daysOf(href: string): [string, string, string] | string {
  const [path, search = ""] = href.split("?");
  const state = readSharedRange(new URLSearchParams(search));
  return state.status === "set" ? [path, state.from, state.to] : state.status;
}

describe("IA-P P3b: the Portfolio hub", () => {
  it("shows exactly three tabs in order, each keeping the address's range", async () => {
    renderAt(`/portfolio?${OCT}`, parse(PERIOD_MONTH));
    await settled();
    const links = within(tabs()).getAllByRole("link");
    expect(links.map((a) => a.textContent)).toEqual(["Overview", "Outcomes", "Demand & capacity"]);
    expect(links.map((a) => daysOf(a.getAttribute("href")!))).toEqual([
      ["/portfolio", "2026-10-01", "2026-10-31"],
      ["/portfolio/outcomes", "2026-10-01", "2026-10-31"],
      ["/portfolio/demand-and-capacity", "2026-10-01", "2026-10-31"],
    ]);
    expect(within(tabs()).getByRole("link", { name: "Overview" }).getAttribute("aria-current")).toBe("page");
    expect(PORTFOLIO_TABS).toHaveLength(3);
  });

  it("mode month reads the month read for E2's served month, not for the range's last month", async () => {
    const { e2, month } = renderAt("/portfolio?from=2026-10-01&to=2026-11-21", parse(PERIOD_MONTH));
    await settled();
    expect(e2.calls).toEqual([["2026-10-01", "2026-11-21"]]);
    expect(month.calls).toEqual(["2026-10"]);
    expect(document.querySelector('[data-level="L1"] .dd-kpis')).not.toBeNull();
  });

  it("the ‹ › links are E2's nav days; with next null no next control is drawn", async () => {
    renderAt(`/portfolio?${OCT}&known_at=2026-11-20T08:00:00Z`, parse(PERIOD_MONTH));
    await settled();
    const nav = screen.getByRole("navigation", { name: "Month" });
    const links = within(nav).getAllByRole("link");
    expect(links.map((a) => [a.textContent, a.getAttribute("href")])).toEqual([
      ["‹ September 2026", "/portfolio?from=2026-09-01&to=2026-09-30&known_at=2026-11-20T08%3A00%3A00Z"],
    ]);
    expect(within(nav).queryByRole("button")).toBeNull();
    expect(document.querySelector(".dd-head [role=note]")!.textContent).toBe("No figures are served for September, so it is not in these figures.");
  });

  it("mode period renders one link per month row and no old category card", async () => {
    renderAt("/portfolio?from=2026-09-01&to=2026-10-31", parse(PERIOD_PERIOD));
    await settled();
    const table = document.querySelector<HTMLElement>("[data-period-months]")!;
    const rows = table.querySelectorAll("tbody tr");
    expect(rows).toHaveLength(2);
    for (const r of rows) expect(r.querySelectorAll("a")).toHaveLength(1);
    expect([...rows].map((r) => r.querySelector("a")!.getAttribute("href"))).toEqual([
      "/portfolio?from=2026-09-01&to=2026-09-30",
      "/portfolio?from=2026-10-01&to=2026-10-31",
    ]);
    expect(document.querySelector("[data-portfolio-card-value]")).toBeNull();
    expect(document.querySelector(".dd-headline")!.textContent).toContain("across September and October");
  });

  it("mode none renders the notes and the suggest link, and no L1 or L3", async () => {
    renderAt("/portfolio?from=2026-11-15&to=2026-11-21", parse(PERIOD_NONE));
    await settled();
    const notes = [...document.querySelectorAll(".dd-head [role=note]")].map((n) => n.textContent);
    expect(notes).toEqual(parse<PortfolioPeriod>(PERIOD_NONE).notes);
    const suggest = screen.getByRole("link", { name: "Show October 2026" });
    expect(suggest.getAttribute("href")).toBe(`/portfolio?${OCT}`);
    expect(document.querySelector('[data-level="L1"]')).toBeNull();
    expect(document.querySelector('[data-level="L3"]')).toBeNull();
    expect(document.querySelector('[data-level="L2"] [data-overview-decisions]')).not.toBeNull();
  });

  it("the L2 rows are the Decisions rows for the range, at most six, then View all {n}", async () => {
    const { estate } = renderAt(`/portfolio?${OCT}`, parse(PERIOD_MONTH));
    await settled();
    const panel = document.querySelector<HTMLElement>("[data-overview-decisions]")!;
    expect(panel.querySelectorAll("tbody tr")).toHaveLength(6);
    const all = within(panel).getByRole("link", { name: "View all 9" });
    expect(all.getAttribute("href")).toBe(`/decisions?${OCT}`);
    expect(estate.calls[0]).toEqual({ from: "2026-10-01T00:00:00Z", to: "2026-11-01T00:00:00Z" });
    expect(panel.querySelector("[data-home-list] .hl-tiles")).toBeNull();
  });

  it("/portfolio/month?month=2026-10 lands on October's days, also when the address held another range", async () => {
    renderAt("/portfolio/month?month=2026-10", parse(PERIOD_MONTH));
    await settled();
    expect(location()).toBe(`/portfolio?${OCT}`);
  });

  it("/portfolio/month?month= over another range: the month's days win and month is dropped", async () => {
    const { e2 } = renderAt("/portfolio/month?month=2026-10&from=2026-11-15&to=2026-11-21&known_at=2026-11-20T08:00:00Z", parse(PERIOD_MONTH));
    await settled();
    expect(location()).toBe(`/portfolio?${OCT}&known_at=2026-11-20T08%3A00%3A00Z`);
    expect(e2.calls).toEqual([["2026-10-01", "2026-10-31"]]);
  });

  it("declares E2's shown span exactly when shown is not null", async () => {
    renderAt("/portfolio?from=2026-10-01&to=2026-11-21", parse(PERIOD_MONTH));
    await settled();
    expect(document.querySelector('[data-shared-range-focus="inside"]')).not.toBeNull();
  });

  it("declares nothing when shown is null (mode period and mode none)", async () => {
    renderAt("/portfolio?from=2026-09-01&to=2026-10-31", parse(PERIOD_PERIOD));
    await settled();
    expect(document.querySelector("[data-shared-range-focus]")).toBeNull();
    expect(document.body.textContent).toContain("All pages");
  });

  it("entryRange('/portfolio') with an empty session is last month; entryRange('/findings') is 7 days", () => {
    const now = Date.parse("2026-11-22T10:00:00Z");
    const days = (params: URLSearchParams) => {
      const state = readSharedRange(params, now);
      return state.status === "set" ? [state.from, state.to] : state.status;
    };
    expect(days(entryRange("/portfolio", now))).toEqual(["2026-10-01", "2026-10-31"]);
    expect(days(entryRange("/findings", now))).toEqual(["2026-11-15", "2026-11-21"]);
    expect(days(entryRange(undefined, now))).toEqual(["2026-11-15", "2026-11-21"]);
  });

  it("/ lands on the Overview at last month", async () => {
    const { e2 } = renderAt("/", parse(PERIOD_MONTH));
    await settled();
    const last = presetRange("lastmonth");
    const [path, search] = location()!.split("?");
    const state = readSharedRange(new URLSearchParams(search));
    expect([path, state.status === "set" ? [state.from, state.to] : state.status]).toEqual(["/portfolio", [last.from, last.to]]);
    expect(e2.calls).toEqual([[last.from, last.to]]);
  });
});

describe("IA-P R2 (D-IAP.25): the page by Site-type matrix on the Overview", () => {
  it("one month (World G): the Overview names Thika, the Site not compared (5c's out reason, in the step drawer)", async () => {
    renderAt(`/portfolio?${OCT}`, parse(PERIOD_MONTH_G), monthClient(parse(MONTH_G)));
    await settled();
    fireEvent.click(document.querySelector<HTMLElement>('[data-level="L3"] button[aria-haspopup="dialog"]')!);
    expect(screen.getByRole("dialog").textContent).toContain("Thika: not a mini-grid Site, not included.");
    expect(document.querySelector(".dd-headline")!.textContent).toContain("Compared for 3 of 4 Sites.");
  });

  it("two months (World G): the headline, tile 1 and every month row state 3 of 4 Sites as served", async () => {
    renderAt("/portfolio?from=2026-09-01&to=2026-10-31", parse(PERIOD_PERIOD_G));
    await settled();
    expect(document.querySelector(".dd-headline")!.textContent).toContain("Compared for 3 of 4 Sites.");
    expect(document.querySelector('[data-dd-tile="contribution"]')!.textContent).toContain("3 of 4 Sites");
    const rows = [...document.querySelectorAll("[data-period-months] tbody tr")];
    expect(rows.map((r) => r.querySelector("th small")!.textContent)).toEqual(["3 of 4 Sites", "3 of 4 Sites"]);
  });
});
