/**
 * IA-P P4b (spec §5.2 "sites", §6 P4b; handshake R3, R6, R8; pre-flight Q1 to Q9): the Sites list and the Portfolio's
 * Outcomes tab on E1 (`GET /api/portfolio/sites`). The E1 bodies are the committed IA-P fixtures written by
 * `backend/tests/test_iap_portfolio_sites.py` test 9, never by hand; every expected figure here is a spec literal.
 */
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import type { SiteDetailClient, SiteDirectoryClient } from "../../sites/siteDirectoryClient";
import type { SiteSummary } from "../../sites/siteReadModel";
import { HYBRID_MINI_GRID_SITE } from "../../sites/__tests__/sldFixtures";
import { settledScreen } from "../../test/settled";
import type { EstateClient, EstatePortfolioBody } from "../estateClient";
import { fetchPortfolioSites, type PortfolioSites, type PortfolioSitesClient, type PortfolioSitesResult } from "../portfolioSitesClient";
import { readSharedRange } from "../../ui/sharedRange";
import { loaded } from "./estateFixtures";
import WORLD_A_MONTH from "../../../../backend/tests/fixtures/5c/deep_dive_lakeside_2026-10.json?raw";
import PERIOD_PERIOD from "./fixtures/iap/period-period-2026-09-10.json?raw";
import PORTFOLIO from "./fixtures/iap/portfolio.json?raw";
import SITES_OCT from "./fixtures/iap/sites-2026-10.json?raw";
import SITES_P from "./fixtures/iap/sites-2026-09-10.json?raw";
import SITES_NONE from "./fixtures/iap/sites-none-2026-11.json?raw";

const parse = <T,>(text: string): T => JSON.parse(text) as T;
const DETAIL: SiteDetailClient = { getSite: () => Promise.resolve({ status: "loaded", site: HYBRID_MINI_GRID_SITE }) };
const OCT = "from=2026-10-01&to=2026-10-31";
const SEP_OCT = "from=2026-09-01&to=2026-10-31";

beforeEach(() => {
  window.sessionStorage.clear();
  window.scrollTo = vi.fn();
});
afterEach(cleanup);

function directory(sites: SiteSummary[] = []): SiteDirectoryClient {
  return { listSites: () => Promise.resolve({ status: "loaded", sites }) };
}

function labSite(site_id: string, display_name: string, site_type = "MINIGRID", lifecycle_status = "ACTIVE"): SiteSummary {
  return {
    site_id,
    display_name,
    site_type,
    location: { country: "KE", region: "Nairobi", latitude: null, longitude: null },
    timezone: "Africa/Nairobi",
    lifecycle_status,
    origin: "LAB",
    source: { kind: "LAB" },
    template: null,
  } as unknown as SiteSummary;
}

function sitesClient(byRange: Record<string, PortfolioSites | PortfolioSitesResult>): PortfolioSitesClient & { calls: [string, string][] } {
  const calls: [string, string][] = [];
  return {
    calls,
    fetchSites: (from, to) => {
      calls.push([from, to]);
      const got = byRange[`${from}|${to}`];
      if (got === undefined) return Promise.resolve({ status: "refused", httpStatus: 404, code: null, text: null });
      return Promise.resolve("status" in got ? got : { status: "loaded", body: got });
    },
  };
}

function estateClient(body: EstatePortfolioBody = parse(PORTFOLIO)): EstateClient {
  return {
    findings: () => Promise.reject(new Error("no findings")),
    actions: () => Promise.reject(new Error("no actions")),
    scope: () => Promise.reject(new Error("no scope")),
    portfolio: () => Promise.resolve(loaded(body)),
    getOutcomeSummary: () => Promise.resolve({ status: "refused", httpStatus: 503, code: "ESTATE_STORE_UNAVAILABLE", copy: "" }),
  } as unknown as EstateClient;
}

function LocationProbe() {
  const location = useLocation();
  return <div data-location>{`${location.pathname}${location.search}`}</div>;
}

const BY_RANGE = {
  "2026-10-01|2026-10-31": parse<PortfolioSites>(SITES_OCT),
  "2026-09-01|2026-10-31": parse<PortfolioSites>(SITES_P),
  "2026-11-15|2026-11-21": parse<PortfolioSites>(SITES_NONE),
};

function renderAt(path: string, e1: PortfolioSitesClient = sitesClient(BY_RANGE), estate = estateClient(), dir = directory()) {
  render(
    <MemoryRouter initialEntries={[path]}>
      <App flags={featureFlagsWith(false)} siteDirectory={dir} siteDetail={DETAIL} estateIndex={estate} portfolioSites={e1} />
      <LocationProbe />
    </MemoryRouter>,
  );
  return { e1 };
}

/** An address as its path, the range's days (links write the range's instant form) and its other parameters. */
function daysOf(href: string): [string, string, string, string] | string {
  const [path, search = ""] = href.split("?");
  const params = new URLSearchParams(search);
  const state = readSharedRange(params);
  params.delete("from");
  params.delete("to");
  return state.status === "set" ? [path, state.from, state.to, params.toString()] : state.status;
}

const list = () => document.querySelector<HTMLElement>('[data-home-list="sites"]')!;
const titles = () => [...list().querySelectorAll("tbody th")].map((th) => th.querySelector("a, span")!.textContent);
function tile(label: string): { value: string; note: string | null } {
  const t = [...list().querySelectorAll<HTMLElement>(".hl-tile")].find((x) => x.querySelector(".hl-tile__label")!.textContent === label)!;
  return { value: t.querySelector(".hl-tile__value")!.textContent!, note: t.querySelector("small")?.textContent ?? null };
}
function cells(title: string): Record<string, string> {
  const tr = [...list().querySelectorAll("tbody tr")].find((r) => r.querySelector("th a, th span")!.textContent === title)!;
  return Object.fromEntries([...tr.querySelectorAll("td")].map((td) => [td.getAttribute("data-label"), td.textContent]));
}

describe("IA-P P4b: the Sites list on E1", () => {
  it("World A, October: the rows in E1's order, the tiles, and the gap tile equals the Overview's tile 2", async () => {
    const e1 = sitesClient(BY_RANGE);
    renderAt(`/sites?${OCT}`, e1);
    await settledScreen();
    expect(e1.calls).toEqual([["2026-10-01", "2026-10-31"]]);
    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("Sites");
    expect(titles()).toEqual(["Kobo", "Mto", "Kisiwa", "Cold Room", "Charge Hub"]);
    expect(tile("Sites").value).toBe("5");
    expect(tile("Below target").value).toBe("0");
    expect(tile("Gap to target")).toEqual({ value: "+$2,136.60", note: "2 Sites without a target are not in this figure" });
    // One figure: the Overview's tile 2 for October (5c's World A month), string for string.
    expect(tile("Gap to target").value).toBe(parse<{ tiles: { value: string }[] }>(WORLD_A_MONTH).tiles[1].value);
    expect(cells("Kobo")).toEqual({
      Group: "Mini-grid",
      Contribution: "$1,565.50 against a target of $1,445.00",
      "Gap to target": "+$120.50Modelled, not yet reconciled",
      "Largest driver against target": "No driver widens the gap",
      "Waiting for a choice": "3",
    });
    expect(cells("Mto")["Largest driver against target"]).toBe("Revenue −$80.00Grow revenue");
    expect(cells("Kisiwa")["Waiting for a choice"]).toBe("0");
    expect(cells("Cold Room")).toEqual({
      Group: "Cold-chain",
      Contribution: "No monthly figures for cold-chain Sites yet",
      "Gap to target": "Not available yet",
      "Largest driver against target": "Not available yet",
      "Waiting for a choice": "2",
    });
    const kobo = within(list()).getByRole("link", { name: "Kobo" });
    expect(daysOf(kobo.getAttribute("href")!)).toEqual(["/sites/KOBO-001", "2026-10-01", "2026-10-31", ""]);
    // One target per row; no directory table and no Lifecycle column.
    for (const tr of list().querySelectorAll("tbody tr")) expect(tr.querySelectorAll("a").length).toBeLessThanOrEqual(1);
    expect(document.body.textContent).not.toContain("Lifecycle");
  });

  it("the rows are E1's order, never sorted by gap in the browser; Name sorts by name", async () => {
    const body = parse<PortfolioSites>(SITES_OCT);
    const swapped = { ...body, rows: [body.rows[2], body.rows[0], body.rows[1], ...body.rows.slice(3)] };
    renderAt(`/sites?${OCT}`, sitesClient({ "2026-10-01|2026-10-31": swapped }));
    await settledScreen();
    expect(titles()).toEqual(["Kisiwa", "Kobo", "Mto", "Cold Room", "Charge Hub"]);
    cleanup();
    renderAt(`/sites?${OCT}&sort=name`);
    await settledScreen();
    expect(titles()).toEqual(["Charge Hub", "Cold Room", "Kisiwa", "Kobo", "Mto"]);
  });

  it("the target facet: Below target keeps the compared rows below; the gap tile is the server's only unfiltered (R6)", async () => {
    // World A's Sites are all on or above target; Kobo and Mto are put below here, as the server's `below` states it.
    const body = parse<PortfolioSites>(SITES_OCT);
    const below = { ...body, rows: body.rows.map((r) => ({ ...r, below: r.site === "Kobo" || r.site === "Mto" })) };
    const some = () => sitesClient({ "2026-10-01|2026-10-31": below });
    renderAt(`/sites?${OCT}&target=below`, some());
    await settledScreen();
    expect(titles()).toEqual(["Kobo", "Mto"]);
    expect(tile("Sites").value).toBe("2");
    expect(tile("Below target").value).toBe("2");
    expect(tile("Gap to target")).toEqual({ value: "Not available yet", note: "For every Site only" });
    expect(within(list()).getByLabelText("In this view").textContent).toContain("Below target · Above and below target");
    cleanup();
    renderAt(`/sites?${OCT}&target=on`, some());
    await settledScreen();
    expect(titles()).toEqual(["Kisiwa"]);
    cleanup();
    renderAt(`/sites?${OCT}&target=below`); // World A as served: none is below
    await settledScreen();
    expect(screen.getByText("Nothing matches these filters.")).toBeTruthy();
  });

  it("under a scope or a search the gap tile is not the portfolio total (plant scopetile)", async () => {
    renderAt(`/sites?${OCT}&scope=group:COLDCHAIN`);
    await settledScreen();
    expect(titles()).toEqual(["Cold Room"]);
    expect(tile("Gap to target")).toEqual({ value: "Not available yet", note: "For every Site only" });
    cleanup();
    renderAt(`/sites?${OCT}&q=kobo`);
    await settledScreen();
    expect(titles()).toEqual(["Kobo"]);
    expect(tile("Gap to target").value).toBe("Not available yet");
  });

  it("World P, September and October: the gap tile is the period's tile 2", async () => {
    const e1 = sitesClient(BY_RANGE);
    renderAt(`/sites?${SEP_OCT}`, e1);
    await settledScreen();
    expect(e1.calls).toEqual([["2026-09-01", "2026-10-31"]]);
    expect(tile("Gap to target").value).toBe("+$4,273.20");
    expect(tile("Gap to target").value).toBe(parse<{ body: { tiles: { value: string }[] } }>(PERIOD_PERIOD).body.tiles[1].value);
    expect(cells("Kobo").Contribution).toBe("$3,131.00 against a target of $2,890.00");
  });

  it("mode none: the notes under the header, two tiles Not available yet, and no target facet", async () => {
    renderAt("/sites?from=2026-11-15&to=2026-11-21&target=below");
    await settledScreen();
    const notes = [...document.querySelectorAll("[data-sites-notes] [role=note]")].map((n) => n.textContent);
    expect(notes).toEqual(parse<PortfolioSites>(SITES_NONE).notes);
    expect(tile("Below target").value).toBe("Not available yet");
    expect(tile("Gap to target").value).toBe("Not available yet");
    expect(titles()).toEqual(["Kobo", "Kisiwa", "Mto", "Cold Room", "Charge Hub"]);
    expect(within(list()).queryByLabelText("In this view")).toBeNull();
  });

  it("a waiting count read without E0 reads Not available yet", async () => {
    const body = parse<EstatePortfolioBody>(PORTFOLIO);
    const { waiting_by_site: _w, ...summary } = body.summary;
    renderAt(`/sites?${OCT}`, sitesClient(BY_RANGE), estateClient({ ...body, summary } as EstatePortfolioBody));
    await settledScreen();
    expect(cells("Kobo")["Waiting for a choice"]).toBe("Not available yet");
  });

  it("a directory Site that E1 does not hold is listed after E1's rows: Group from site_type, waiting from E0 (D-IAP.35 Q1)", async () => {
    const body = parse<EstatePortfolioBody>(PORTFOLIO);
    const withLab = { ...body, summary: { ...body.summary, waiting_by_site: { ...body.summary.waiting_by_site, "LAB-SITE-9": 2 } } } as EstatePortfolioBody;
    renderAt(
      `/sites?${OCT}`,
      sitesClient(BY_RANGE),
      estateClient(withLab),
      directory([labSite("kobo-001", "Kobo"), labSite("LAB-SITE-9", "Lab Site", "COLDCHAIN"), labSite("LAB-SITE-10", "Lab Ten", "EV_CHARGING"), labSite("LAB-X", "Lab Odd", "SOLAR_PUMP")]),
    );
    await settledScreen();
    expect(titles()).toEqual(["Kobo", "Mto", "Kisiwa", "Cold Room", "Charge Hub", "Lab Site", "Lab Ten", "Lab Odd"]);
    expect(cells("Lab Site")).toEqual({
      Group: "Cold-chain",
      Contribution: "Not available yet",
      "Gap to target": "Not available yet",
      "Largest driver against target": "Not available yet",
      "Waiting for a choice": "2",
    });
    // Absent from waiting_by_site: 0, like any row; an unmapped site_type: "Not available yet".
    expect(cells("Lab Ten")).toMatchObject({ Group: "EV charging", "Waiting for a choice": "0" });
    expect(cells("Lab Odd")).toMatchObject({ Group: "Not available yet", "Waiting for a choice": "0" });
    expect(daysOf(within(list()).getByRole("link", { name: "Lab Site" }).getAttribute("href")!)).toEqual(["/sites/LAB-SITE-9", "2026-10-01", "2026-10-31", ""]);
  });

  it("a Site that is not Active carries its lifecycle word under its title; an Active one none (D-IAP.44, plant nolife)", async () => {
    renderAt(
      `/sites?${OCT}`,
      sitesClient(BY_RANGE),
      estateClient(),
      directory([labSite("kobo-001", "Kobo", "MINIGRID", "PLANNED"), labSite("LAB-SITE-9", "Lab Site", "COLDCHAIN", "COMMISSIONED"), labSite("LAB-SITE-10", "Lab Ten", "EV_CHARGING")]),
    );
    await settledScreen();
    const word = (title: string) => {
      const tr = [...list().querySelectorAll("tbody tr")].find((r) => r.querySelector("th a, th span")!.textContent === title)!;
      return tr.querySelector("th small[data-lifecycle]")?.textContent ?? null;
    };
    expect(word("Kobo")).toBe("Planned");
    expect(word("Lab Site")).toBe("Commissioned");
    expect(word("Lab Ten")).toBeNull();
    expect(word("Kisiwa")).toBeNull();
  });

  it("a refused directory read shows no lifecycle word, and the rows stand (D-IAP.44)", async () => {
    const refused: SiteDirectoryClient = { listSites: () => Promise.resolve({ status: "refused", httpStatus: 503 } as never) };
    renderAt(`/sites?${OCT}`, sitesClient(BY_RANGE), estateClient(), refused);
    await settledScreen();
    expect(titles()).toEqual(["Kobo", "Mto", "Kisiwa", "Cold Room", "Charge Hub"]);
    expect(list().querySelector("th small[data-lifecycle]")).toBeNull();
  });

  it("a refused E1 shows the served text and Try again, which reads again", async () => {
    let n = 0;
    const e1: PortfolioSitesClient = {
      fetchSites: () => {
        n += 1;
        return Promise.resolve(
          n === 1 ? { status: "refused", httpStatus: 503, code: "DEEP_DIVE_UNAVAILABLE", text: "The figures cannot be read right now." } : { status: "loaded", body: parse<PortfolioSites>(SITES_OCT) },
        );
      },
    };
    renderAt(`/sites?${OCT}`, e1);
    await settledScreen();
    expect(screen.getByText("The figures cannot be read right now.")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    await settledScreen();
    expect(titles()).toEqual(["Kobo", "Mto", "Kisiwa", "Cold Room", "Charge Hub"]);
  });

  it("the client refuses a body of another schema", async () => {
    vi.stubGlobal("fetch", async () => new Response(JSON.stringify({ ...parse<PortfolioSites>(SITES_OCT), schema: "portfolio-sites-0" }), { status: 200 }));
    try {
      expect((await fetchPortfolioSites("2026-10-01", "2026-10-31")).status).toBe("refused");
    } finally {
      vi.unstubAllGlobals();
    }
  });

  it("/sites follows the range: the bar says All pages", async () => {
    renderAt(`/sites?${OCT}`);
    await settledScreen();
    const bar = document.querySelector<HTMLElement>("[data-shared-range-topbar]")!;
    expect(bar.textContent).toContain("All pages");
  });
});

describe("IA-P P4b: the Outcomes tab", () => {
  it("L1 is E1's headline, L2 the Sites rows with no tools or tiles, L3 the cards then the objectives in a disclosure", async () => {
    renderAt(`/portfolio/outcomes?${OCT}`);
    await settledScreen();
    const l1 = document.querySelector<HTMLElement>('[data-portfolio-tab-panel="outcomes"] [data-level="L1"]')!;
    expect(l1.querySelector("[data-sites-headline]")!.textContent).toContain("Every Site is on or above target in October");
    expect(l1.textContent).toContain("2 Sites without a target are not in this figure");
    expect(titles()).toEqual(["Kobo", "Mto", "Kisiwa", "Cold Room", "Charge Hub"]);
    expect(list().querySelector(".hl-tiles")).toBeNull();
    expect(list().querySelector("form")).toBeNull();
    const l3 = document.querySelector<HTMLElement>('[data-portfolio-tab-panel="outcomes"] [data-level="L3"]')!;
    const cards = l3.querySelector("[data-portfolio-cards], .portfolio-cards, [data-portfolio-card]");
    const objectives = l3.querySelector('[data-portfolio-panel="objectives"]')!;
    expect(cards).not.toBeNull();
    expect(objectives.closest("details")!.querySelector("summary")!.textContent).toContain("Each Site's objectives");
    expect(cards!.compareDocumentPosition(objectives) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it("an Outcomes L2 row whose Site is not Active carries its lifecycle word; L2 lists a directory-only Site after E1's rows, as /sites does (D-IAP.44, D-IAP.51)", async () => {
    renderAt(`/portfolio/outcomes?${OCT}`, sitesClient(BY_RANGE), estateClient(), directory([labSite("KOBO-001", "Kobo", "MINIGRID", "DECOMMISSIONED"), labSite("LAB-SITE-9", "Lab Site", "COLDCHAIN", "PLANNED")]));
    await settledScreen();
    expect(titles()).toEqual(["Kobo", "Mto", "Kisiwa", "Cold Room", "Charge Hub", "Lab Site"]);
    const kobo = [...list().querySelectorAll("tbody tr")].find((r) => r.querySelector("th a, th span")!.textContent === "Kobo")!;
    expect(kobo.querySelector("th small[data-lifecycle]")!.textContent).toBe("Decommissioned");
  });

  it("the Outcomes rows are the Sites list rows, a directory-only Site included (D-IAP.51)", async () => {
    const dirOnly = () => directory([labSite("LAB-SITE-9", "Lab Site", "COLDCHAIN", "ACTIVE")]);
    renderAt(`/portfolio/outcomes?${SEP_OCT}`, sitesClient(BY_RANGE), estateClient(), dirOnly());
    await settledScreen();
    const outcomes = titles();
    expect(outcomes).toContain("Lab Site");
    const kobo = cells("Kobo");
    cleanup();
    renderAt(`/sites?${SEP_OCT}`, sitesClient(BY_RANGE), estateClient(), dirOnly());
    await settledScreen();
    expect(titles()).toEqual(outcomes);
    expect(cells("Kobo")).toEqual(kobo);
  });

  it("mode none: E1's notes in L1's place", async () => {
    renderAt("/portfolio/outcomes?from=2026-11-15&to=2026-11-21");
    await settledScreen();
    const l1 = document.querySelector<HTMLElement>('[data-portfolio-tab-panel="outcomes"] [data-level="L1"]')!;
    expect(l1.querySelector("[data-sites-headline]")).toBeNull();
    expect([...l1.querySelectorAll("[role=note]")].map((n) => n.textContent)).toEqual(parse<PortfolioSites>(SITES_NONE).notes);
  });

  it("eleven Sites: the singular More line (D-IAP.35 Q5)", async () => {
    const body = parse<PortfolioSites>(SITES_OCT);
    const extra = Array.from({ length: 6 }, (_, k) => ({ ...body.rows[4], site_code: `EV-1${k}`, site: `Depot ${k}` }));
    renderAt(`/portfolio/outcomes?${OCT}`, sitesClient({ "2026-10-01|2026-10-31": { ...body, rows: [...body.rows, ...extra] } }));
    await settledScreen();
    expect(list().querySelectorAll("tbody tr")).toHaveLength(10);
    expect(list().querySelector(".hl-more")!.textContent).toBe("Not shown: 1 Site. Show all 11");
  });

  it("more than ten Sites: Show all links to /sites?show=all with the range", async () => {
    const body = parse<PortfolioSites>(SITES_OCT);
    const extra = Array.from({ length: 8 }, (_, k) => ({ ...body.rows[4], site_code: `EV-1${k}`, site: `Depot ${k}` }));
    renderAt(`/portfolio/outcomes?${OCT}`, sitesClient({ "2026-10-01|2026-10-31": { ...body, rows: [...body.rows, ...extra] } }));
    await settledScreen();
    expect(list().querySelectorAll("tbody tr")).toHaveLength(10);
    expect(list().querySelector(".hl-more")!.textContent).toBe("Not shown: 3 Sites. Show all 13");
    expect(daysOf(within(list()).getByRole("link", { name: "Show all 13" }).getAttribute("href")!)).toEqual(["/sites", "2026-10-01", "2026-10-31", "show=all"]);
  });
});
