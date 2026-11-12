/**
 * SR-4c (D-SR.6, architect rev 8 §8.2 table and §8.3 "the tag and spoken name per row"): with a range in the address,
 * the date-range bar says what each Site page does with it, for each Site type: a page that follows the range says
 * "All pages"; a page that shows part of the range names the days it shows; a point-in-time page says the range is
 * not used and what it shows instead. Also the EV generic Financials redirect. Whole App in a memory router; every
 * read but the Site detail answers 503 (the tag does not depend on the page's data).
 */
import { render, screen } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import { settledScreen } from "../../test/settled";
import { COLD_SITE } from "../../sites/__tests__/coldWorkFixtures";
import { EV_SITE } from "../../sites/__tests__/evWorkFixtures";
import { HYBRID_MINI_GRID_SITE } from "../../sites/__tests__/sldFixtures";
import type { SiteDetailClient, SiteDirectoryClient } from "../../sites/siteDirectoryClient";
import type { SiteDetailReadModel } from "../../sites/siteReadModel";

const RANGE = "from=2026-11-03T00%3A00%3A00Z&to=2026-11-10T00%3A00%3A00Z";

const as = (site: SiteDetailReadModel, code: string): SiteDetailReadModel => ({ ...site, site_id: code }) as SiteDetailReadModel;
const SITES: Record<string, SiteDetailReadModel> = {
  "KOBO-001": as(HYBRID_MINI_GRID_SITE, "KOBO-001"),
  "KISIWA-001": as(HYBRID_MINI_GRID_SITE, "KISIWA-001"),
  "COLD-LAB-001": as(COLD_SITE as SiteDetailReadModel, "COLD-LAB-001"),
  "EV-LAB-001": as(EV_SITE as SiteDetailReadModel, "EV-LAB-001"),
};
const DETAIL: SiteDetailClient = {
  getSite: (code: string) => Promise.resolve(SITES[code] ? { status: "loaded", site: SITES[code] } : { status: "not_found" }),
} as SiteDetailClient;
const DIRECTORY: SiteDirectoryClient = {
  listSites: () => Promise.resolve({ status: "loaded", sites: Object.values(SITES) }),
} as SiteDirectoryClient;

let where = "";
function Probe() {
  const location = useLocation();
  where = `${location.pathname}${location.search}`;
  return null;
}

beforeEach(() => {
  where = "";
  window.sessionStorage.clear();
  vi.stubGlobal(
    "fetch",
    vi.fn(() => Promise.resolve(new Response("{}", { status: 503, headers: { "Content-Type": "application/json" } }))),
  );
});

afterEach(() => {
  vi.unstubAllGlobals();
});

async function open(path: string) {
  const view = render(
    <MemoryRouter initialEntries={[path]}>
      <App flags={featureFlagsWith(false)} siteDetail={DETAIL} siteDirectory={DIRECTORY} />
      <Probe />
    </MemoryRouter>,
  );
  await settledScreen();
  return view;
}

const button = () => screen.getByRole("button", { name: /^Date range for (every page|the other pages):/ });
const tag = () => button().querySelector(".shared-range__tag");

async function expectTag(path: string, text: string, focus: string | null, spoken: RegExp) {
  const view = await open(`${path}?${RANGE}`);
  expect(tag()?.textContent, path).toBe(text);
  expect(tag()?.getAttribute("data-shared-range-focus") ?? null, path).toBe(focus);
  expect(button().getAttribute("aria-label"), path).toMatch(spoken);
  view.unmount();
}

const FOLLOWS = /^Date range for every page: Custom, .*\. Change$/;
const NOW = (spokenNote: string) =>
  new RegExp(`^Date range for the other pages: .*\\. This page shows ${spokenNote}; the range is not used here\\. Change$`);

describe("SR-4c: the bar tag and spoken name per page and Site type (rev 8 §8.2)", () => {
  it("mini-grid: Health shows now, Financials and Prices the prices valid now, Foundation the current settings", async () => {
    await expectTag("/sites/KOBO-001/health", "Range not used · shows now", "now", NOW("the present state"));
    await expectTag("/sites/KOBO-001/financials", "Range not used · prices valid now", "now", NOW("the prices valid now"));
    await expectTag("/sites/KOBO-001/financials/assumptions", "Range not used · prices valid now", "now", NOW("the prices valid now"));
    await expectTag("/sites/KOBO-001/financials/prices", "Range not used · prices valid now", "now", NOW("the prices valid now"));
    await expectTag("/sites/KOBO-001/foundation", "Range not used · current settings", "now", NOW("the current settings"));
    await expectTag("/sites/KOBO-001/foundation/changes", "Range not used · current settings", "now", NOW("the current settings"));
  });

  it("D-SR.43: the Assets list and the battery page are configuration on every Site type: range not used, current settings", async () => {
    for (const code of ["KOBO-001", "COLD-LAB-001", "EV-LAB-001"]) {
      await expectTag(`/sites/${code}/assets`, "Range not used · current settings", "now", NOW("the current settings"));
      await expectTag(`/sites/${code}/assets/BAT-1`, "Range not used · current settings", "now", NOW("the current settings"));
    }
  });

  it("D-SR.66 (corrects D-SR.44): Cold and EV financial assumptions declare what their Financials declare", async () => {
    await expectTag("/sites/COLD-LAB-001/financials/assumptions", "All pages", null, FOLLOWS);
    await expectTag("/sites/COLD-LAB-001/financials", "All pages", null, FOLLOWS);
    await expectTag("/sites/EV-LAB-001/ev/financial-assumptions", "All pages", null, FOLLOWS);
    await expectTag("/sites/EV-LAB-001/ev/financials", "All pages", null, FOLLOWS);
  });

  it("D-SR.64: Finding detail on every Site type says the range is not used: the record's own period", async () => {
    for (const code of ["KOBO-001", "KISIWA-001", "COLD-LAB-001", "EV-LAB-001"]) {
      await expectTag(
        `/sites/${code}/findings/7601a982-0000-4000-8000-000000000001`,
        "Range not used · this record's own period",
        "now",
        NOW("this record's own period"),
      );
    }
  });

  it("D-SR.65: Kisiwa's Fuel nights view names the night it shows, never All pages", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const nights = String(input).endsWith("/fuel-balance/nights");
        const body = nights
          ? { site_code: "KISIWA-001", mode: "NIGHTS", time_zone: "Africa/Dar_es_Salaam", known_at: "2026-11-11T00:00:00Z", provenance: null,
              nights: [{ night_date: "2026-11-10", label: "Night of 10 Nov · 6 pm to noon", state: "WITHIN_MARGIN", status: "Fuel balance: accounted for within the margin", tone: "neutral", revision: 1 }] }
          : {};
        return Promise.resolve(new Response(JSON.stringify(body), { status: nights ? 200 : 503, headers: { "Content-Type": "application/json" } }));
      }),
    );
    // Range B (1-5 Nov): the night shown, 10 Nov, lies outside it.
    const view = await open("/sites/KISIWA-001/performance/fuel?from=2026-11-01T00%3A00%3A00Z&to=2026-11-06T00%3A00%3A00Z");
    expect(screen.getByText("Night of 10 Nov · 6 pm to noon", { exact: false })).toBeTruthy();
    expect(tag()?.textContent).toBe("Showing 10 Nov · range not used");
    expect(tag()?.getAttribute("data-shared-range-focus")).toBe("outside");
    view.unmount();
  });

  it("mini-grid: Service shows one day of the range, Renewable over 5 days its last 5 days", async () => {
    await expectTag(
      "/sites/KOBO-001/performance/service",
      "Showing 9 Nov of the range",
      "inside",
      /\. This page shows one day of it: 9 Nov 2026\. Change$/,
    );
    await expectTag(
      "/sites/KOBO-001/performance/renewable",
      "Showing 5–9 Nov of the range",
      "inside",
      /\. This page shows part of it: 5 Nov 2026 to 9 Nov 2026\. Change$/,
    );
  });

  it("mini-grid: a Renewable range of at most 5 days is read whole, so the page follows the range", async () => {
    const view = await open("/sites/KOBO-001/performance/renewable?from=2026-11-06T00%3A00%3A00Z&to=2026-11-09T00%3A00%3A00Z");
    expect(tag()?.textContent).not.toMatch(/^Showing/);
    view.unmount();
  });

  it("cold chain: Overview, Performance, Health and Financials follow the range; Prices and Foundation do not", async () => {
    await expectTag("/sites/COLD-LAB-001", "All pages", null, FOLLOWS);
    await expectTag("/sites/COLD-LAB-001/performance", "All pages", null, FOLLOWS);
    await expectTag("/sites/COLD-LAB-001/health", "All pages", null, FOLLOWS);
    await expectTag("/sites/COLD-LAB-001/financials", "All pages", null, FOLLOWS);
    await expectTag("/sites/COLD-LAB-001/financials/prices", "Range not used · prices valid now", "now", NOW("the prices valid now"));
    await expectTag("/sites/COLD-LAB-001/foundation", "Range not used · current settings", "now", NOW("the current settings"));
  });

  it("EV: Overview, Health and Financials follow the range; Prices and Foundation do not", async () => {
    await expectTag("/sites/EV-LAB-001/ev", "All pages", null, FOLLOWS);
    await expectTag("/sites/EV-LAB-001/health", "All pages", null, FOLLOWS);
    await expectTag("/sites/EV-LAB-001/ev/financials", "All pages", null, FOLLOWS);
    await expectTag("/sites/EV-LAB-001/financials/prices", "Range not used · prices valid now", "now", NOW("the prices valid now"));
    await expectTag("/sites/EV-LAB-001/foundation", "Range not used · current settings", "now", NOW("the current settings"));
  });
});

describe("SR-4c: EV on the generic Financials path (rev 8 §8.2)", () => {
  it("/sites/<EV>/financials forwards to the EV financials route and keeps the query", async () => {
    const view = await open(`/sites/EV-LAB-001/financials?${RANGE}&known_at=2026-11-09T12%3A00%3A00Z`);
    expect(where).toBe(`/sites/EV-LAB-001/ev/financials?${RANGE}&known_at=2026-11-09T12%3A00%3A00Z`);
    expect(tag()?.textContent).toBe("All pages");
    view.unmount();
  });

  it("a mini-grid's generic Financials does not forward", async () => {
    const view = await open(`/sites/KOBO-001/financials?${RANGE}`);
    expect(where).toBe(`/sites/KOBO-001/financials?${RANGE}`);
    view.unmount();
  });
});
