/**
 * IA-P P7 (spec §6 P7 "Scope"; D-IAP.40 Q23 to Q26): the top bar's scope switch. On a list an entry writes `scope=` and
 * keeps the facets, sort and `q`; on a Site page or a hub a Site entry opens `/sites/{code}` and a group or all keeps
 * `scope=` in the address. The pages that show every Site say so with one chip (MD-IAP-5). Each word is a literal.
 */
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import type { EstateClient, EstatePortfolioBody } from "../../estate/estateClient";
import type { PortfolioSites, PortfolioSitesClient } from "../../estate/portfolioSitesClient";
import { loaded } from "../../estate/__tests__/estateFixtures";
import PORTFOLIO from "../../estate/__tests__/fixtures/iap/portfolio.json?raw";
import SITES_OCT from "../../estate/__tests__/fixtures/iap/sites-2026-10.json?raw";
import type { SiteDetailClient, SiteDirectoryClient } from "../../sites/siteDirectoryClient";
import type { SiteSummary } from "../../sites/siteReadModel";
import { HYBRID_MINI_GRID_SITE } from "../../sites/__tests__/sldFixtures";
import { settledScreen } from "../../test/settled";

beforeEach(() => {
  window.scrollTo = vi.fn();
});
afterEach(cleanup);

const OCT = "from=2026-10-01&to=2026-10-31";
const DETAIL: SiteDetailClient = { getSite: () => Promise.resolve({ status: "loaded", site: HYBRID_MINI_GRID_SITE }) };

function site(site_id: string, display_name: string, site_type: string): SiteSummary {
  return {
    site_id,
    display_name,
    site_type,
    location: { country: "KE", region: "Nairobi", latitude: null, longitude: null },
    timezone: "Africa/Nairobi",
    lifecycle_status: "ACTIVE",
    origin: "LAB",
    source: { kind: "LAB" },
    template: null,
  } as unknown as SiteSummary;
}

/** Directory order on purpose: an EV Site first, so the domain entries are seen to follow `DOMAIN_WORD`, not it. */
const SITES = [site("EV-001", "Charge Hub", "EV_CHARGING"), site("KOBO-001", "Kobo", "MINIGRID"), site("COLD-001", "Cold Room", "COLDCHAIN")];
const directory = (): SiteDirectoryClient => ({ listSites: () => Promise.resolve({ status: "loaded", sites: SITES }) });

function estateClient(body: EstatePortfolioBody = JSON.parse(PORTFOLIO) as EstatePortfolioBody): EstateClient {
  return {
    findings: () => Promise.reject(new Error("no findings")),
    actions: () => Promise.reject(new Error("no actions")),
    scope: () => Promise.reject(new Error("no scope")),
    portfolio: () => Promise.resolve(loaded(body)),
    getOutcomeSummary: () => Promise.resolve({ status: "refused", httpStatus: 503, code: "ESTATE_STORE_UNAVAILABLE", copy: "" }),
  } as unknown as EstateClient;
}

const e1: PortfolioSitesClient = {
  fetchSites: () => Promise.resolve({ status: "loaded", body: JSON.parse(SITES_OCT) as PortfolioSites }),
};

function LocationProbe() {
  const location = useLocation();
  return <div data-location>{`${location.pathname}${location.search}`}</div>;
}

function renderAt(path: string) {
  render(
    <MemoryRouter initialEntries={[path]}>
      <App flags={featureFlagsWith(false)} siteDirectory={directory()} siteDetail={DETAIL} estateIndex={estateClient()} portfolioSites={e1} />
      <LocationProbe />
    </MemoryRouter>,
  );
}

const here = () => document.querySelector("[data-location]")!.textContent!;
const params = () => new URLSearchParams(here().split("?")[1] ?? "");
const scopeButton = () => document.querySelector<HTMLButtonElement>("[data-scope-switch] > button")!;

async function pick(word: string) {
  fireEvent.click(scopeButton());
  await settledScreen();
  const menu = screen.getByRole("menu");
  fireEvent.click(within(menu).getByRole("menuitem", { name: word }));
  await settledScreen();
}

describe("the scope button and its menu", () => {
  it("reads All sites, a domain word, or a Site name", async () => {
    renderAt(`/decisions?${OCT}`);
    await settledScreen();
    expect(scopeButton().textContent).toBe("All sites ▾");
    cleanup();
    renderAt(`/decisions?${OCT}&scope=group:COLDCHAIN`);
    await settledScreen();
    expect(scopeButton().textContent).toBe("Cold-chain ▾");
    cleanup();
    renderAt(`/decisions?${OCT}&scope=site:KOBO-001`);
    await settledScreen();
    expect(scopeButton().textContent).toBe("Kobo ▾");
  });

  it("lists All sites, each domain present in DOMAIN_WORD order, then the Sites in directory order", async () => {
    renderAt(`/decisions?${OCT}`);
    await settledScreen();
    fireEvent.click(scopeButton());
    await settledScreen();
    const words = within(screen.getByRole("menu"))
      .getAllByRole("menuitem")
      .map((b) => b.textContent);
    expect(words).toEqual(["All sites", "Mini-grid", "Cold-chain", "EV charging", "Charge Hub", "Kobo", "Cold Room"]);
  });

  it("Escape closes the menu and returns focus to the button", async () => {
    renderAt(`/decisions?${OCT}`);
    await settledScreen();
    fireEvent.click(scopeButton());
    await settledScreen();
    fireEvent.keyDown(screen.getByRole("menu"), { key: "Escape" });
    expect(screen.queryByRole("menu")).toBeNull();
    expect(document.activeElement).toBe(scopeButton());
  });
});

describe("on a list (plant scopedrop)", () => {
  it("a group entry writes scope= and keeps the facets, sort and q", async () => {
    renderAt(`/decisions?${OCT}&state=waiting&sort=site&q=decision`);
    await settledScreen();
    await pick("Cold-chain");
    expect(params().get("scope")).toBe("group:COLDCHAIN");
    expect(params().get("state")).toBe("waiting");
    expect(params().get("sort")).toBe("site");
    expect(params().get("q")).toBe("decision");
    expect(params().get("from")).toBe("2026-10-01");
    expect(here().startsWith("/decisions?")).toBe(true);
  });

  it("a Site entry scopes the list to that Site; All sites removes the scope, the facets kept", async () => {
    renderAt(`/decisions?${OCT}&state=waiting`);
    await settledScreen();
    await pick("Kobo");
    expect(here().startsWith("/decisions?")).toBe(true);
    expect(params().get("scope")).toBe("site:KOBO-001");
    expect(params().get("state")).toBe("waiting");
    const rows = [...document.querySelectorAll('[data-home-list="decisions"] tbody th')].map((th) => th.textContent ?? "");
    expect(rows.length).toBeGreaterThan(0);
    expect(rows.every((t) => !t.includes("Decision 3") && !t.includes("Decision 5"))).toBe(true);
    await pick("All sites");
    expect(params().has("scope")).toBe(false);
    expect(params().get("state")).toBe("waiting");
  });
});

describe("on a hub or a Site page", () => {
  it("a Site entry opens the Site page with the range", async () => {
    renderAt(`/portfolio/outcomes?${OCT}`);
    await settledScreen();
    await pick("Kobo");
    expect(here().startsWith("/sites/KOBO-001")).toBe(true);
    expect(params().get("from")).not.toBeNull();
  });

  it("a group entry keeps scope= in the address of the same page", async () => {
    renderAt(`/results?${OCT}`);
    await settledScreen();
    await pick("Mini-grid");
    expect(here().startsWith("/results?")).toBe(true);
    expect(params().get("scope")).toBe("group:MINIGRID");
  });
});

describe('the chip "This page shows every Site" (MD-IAP-5; D-IAP.40)', () => {
  const CHIP = "This page shows every Site";
  it.each([`/portfolio?${OCT}`, `/portfolio/demand-and-capacity?${OCT}`, `/portfolio/outcomes?${OCT}`, `/results?${OCT}`, `/evidence?${OCT}`])(
    "%s with a scope shows it",
    async (path) => {
      renderAt(`${path}&scope=group:MINIGRID`);
      await settledScreen();
      expect(screen.getAllByText(CHIP)).toHaveLength(1);
    },
  );

  it.each([`/portfolio?${OCT}`, `/decisions?${OCT}&scope=group:MINIGRID`, `/sites/KOBO-001?${OCT}&scope=site:KOBO-001`])("%s does not", async (path) => {
    renderAt(path);
    await settledScreen();
    expect(screen.queryByText(CHIP)).toBeNull();
  });

  it("Outcomes L2 follows the scope; its rows are the scoped Sites", async () => {
    renderAt(`/portfolio/outcomes?${OCT}&scope=group:COLDCHAIN`);
    await settledScreen();
    const l2 = document.querySelector<HTMLElement>('[data-level="L2"] [data-home-list="sites"]')!;
    expect([...l2.querySelectorAll("tbody th")].map((th) => th.querySelector("a, span")!.textContent)).toEqual(["Cold Room"]);
  });
});
