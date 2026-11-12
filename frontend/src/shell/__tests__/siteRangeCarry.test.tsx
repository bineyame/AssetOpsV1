/**
 * SR-4a (D-SR.2, D-SR.3; architect rev 8 §8.3): the runtime guard. The whole App in a memory router, real clients over
 * a stub fetch (every read but the Site detail answers 503: this test is about links), Site-detail fixtures for the
 * four demo Sites. Every Site href on every Site tab carries the shared range, every tab click keeps it, and the
 * shell's safety net completes a Site content address that has none.
 */
import { fireEvent, render, screen, within } from "@testing-library/react";
import { useEffect } from "react";
import { MemoryRouter, useLocation, useNavigate, type NavigateFunction } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import { settledScreen } from "../../test/settled";
import { COLD_SITE } from "../../sites/__tests__/coldWorkFixtures";
import { EV_SITE } from "../../sites/__tests__/evWorkFixtures";
import { HYBRID_MINI_GRID_SITE } from "../../sites/__tests__/sldFixtures";
import type { SiteDetailClient, SiteDirectoryClient } from "../../sites/siteDirectoryClient";
import type { SiteDetailReadModel } from "../../sites/siteReadModel";
import { SITE_PATH, entryRange } from "../../ui/sharedRange";
import { OPERATOR_SITE_TABS_LABEL } from "../operatorSiteTabs";

const FROM = "2026-11-03T00:00:00Z";
const TO = "2026-11-10T00:00:00Z";
const RANGE = `from=${FROM}&to=${TO}`;

const as = (site: SiteDetailReadModel, code: string): SiteDetailReadModel => ({ ...site, site_id: code }) as SiteDetailReadModel;
const SITES: Record<string, SiteDetailReadModel> = {
  "KOBO-001": as(HYBRID_MINI_GRID_SITE, "KOBO-001"),
  // SR-4ab L-3: Kisiwa's own fixture (its zone, and a mini capabilities read with Fuel below), not Kobo's.
  "KISIWA-001": { ...as(HYBRID_MINI_GRID_SITE, "KISIWA-001"), display_name: "Kisiwa", timezone: "Africa/Nairobi" } as SiteDetailReadModel,
  "COLD-LAB-001": as(COLD_SITE as SiteDetailReadModel, "COLD-LAB-001"),
  "EV-LAB-001": as(EV_SITE as SiteDetailReadModel, "EV-LAB-001"),
};
const DETAIL: SiteDetailClient = {
  getSite: (code: string) => Promise.resolve(SITES[code] ? { status: "loaded", site: SITES[code] } : { status: "not_found" }),
} as SiteDetailClient;
const DIRECTORY: SiteDirectoryClient = {
  listSites: () => Promise.resolve({ status: "loaded", sites: Object.values(SITES) }),
} as SiteDirectoryClient;

const KISIWA_CAPS = [
  { id: "service", display_name: "Service" },
  { id: "fuel", display_name: "Fuel" },
  { id: "renewable", display_name: "Renewable" },
  { id: "backup", display_name: "Backup" },
];

let where = "";
let go: NavigateFunction | null = null;
function Probe() {
  const location = useLocation();
  const navigate = useNavigate();
  useEffect(() => {
    go = navigate;
  }, [navigate]);
  where = `${location.pathname}${location.search}`;
  return null;
}

beforeEach(() => {
  where = "";
  go = null;
  window.sessionStorage.clear();
  vi.stubGlobal(
    "fetch",
    vi.fn((input: RequestInfo | URL) => {
      const url = typeof input === "string" ? input : input instanceof URL ? input.toString() : input.url;
      if (url === "/api/sites/KISIWA-001/performance/mini/capabilities") {
        return Promise.resolve(new Response(JSON.stringify(KISIWA_CAPS), { status: 200, headers: { "Content-Type": "application/json" } }));
      }
      return Promise.resolve(new Response("{}", { status: 503, headers: { "Content-Type": "application/json" } }));
    }),
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

const paramsOf = (href: string) => new URL(href, "http://x").searchParams;
const pathOf = (href: string) => new URL(href, "http://x").pathname;

/** Every in-app Site href on the page that does not carry a from/to. */
function bareSiteHrefs(): string[] {
  return Array.from(document.querySelectorAll<HTMLAnchorElement>("a[href]"))
    .map((a) => a.getAttribute("href") ?? "")
    .filter((href) => href.startsWith("/") && SITE_PATH.test(pathOf(href)))
    .filter((href) => !(paramsOf(href).has("from") && paramsOf(href).has("to")));
}

function tabHrefs(): string[] {
  const nav = screen.getByRole("navigation", { name: OPERATOR_SITE_TABS_LABEL });
  return within(nav)
    .getAllByRole("link")
    .map((a) => a.getAttribute("href") ?? "");
}

describe("SR-4a the Sites index carries the range", () => {
  it("every Site card opened from the rail carries the range", async () => {
    const view = await open(`/portfolio?${RANGE}`);
    const rail = screen.getAllByRole("link").find((a) => pathOf(a.getAttribute("href") ?? "") === "/sites");
    expect(rail).toBeDefined();
    fireEvent.click(rail as HTMLElement);
    await settledScreen();
    expect(pathOf(where)).toBe("/sites");
    const cards = Array.from(document.querySelectorAll<HTMLAnchorElement>("a[href]"))
      .map((a) => a.getAttribute("href") ?? "")
      .filter((href) => /^\/sites\/[^/?]+/.test(href));
    // Non-vacuous: the four Sites are listed.
    for (const code of Object.keys(SITES)) expect(cards.some((href) => pathOf(href) === `/sites/${code}`)).toBe(true);
    expect(bareSiteHrefs()).toEqual([]);
    view.unmount();
  });
});

// The EV Site root shows its own board without the tab row when its EV read fails (503 here); its Work page has the row.
const START: Record<string, string> = { "EV-LAB-001": "/work" };

describe.each(Object.keys(SITES))("SR-4a %s: every Site link on every tab carries the range", (code) => {
  it("the tab row, each tab's page and each tab click keep the range", async () => {
    const start = `/sites/${code}${START[code] ?? ""}?${RANGE}`;
    let view = await open(start);
    const tabs = tabHrefs();
    expect(tabs.length).toBeGreaterThan(1);
    for (const href of tabs) expect(paramsOf(href).has("from") && paramsOf(href).has("to")).toBe(true);
    view.unmount();
    for (const href of tabs) {
      view = await open(start);
      const link = within(screen.getByRole("navigation", { name: OPERATOR_SITE_TABS_LABEL }))
        .getAllByRole("link")
        .find((a) => a.getAttribute("href") === href);
      fireEvent.click(link as HTMLElement);
      await settledScreen();
      const at = paramsOf(where);
      expect([href, at.has("from") && at.has("to")]).toEqual([href, true]);
      expect([href, bareSiteHrefs()]).toEqual([href, []]);
      view.unmount();
    }
  });
});

describe("SR-4a the safety net completes a Site content address with no range", () => {
  it("a fresh /sites/KOBO-001 gets the 7-day entry range", async () => {
    const view = await open("/sites/KOBO-001");
    const expected = entryRange();
    const at = paramsOf(where);
    expect(pathOf(where)).toBe("/sites/KOBO-001");
    expect([at.get("from"), at.get("to")]).toEqual([expected.get("from"), expected.get("to")]);
    view.unmount();
  });

  it("/sites/KOBO-001?day=2026-10-24 gets 18-24 Oct and keeps day", async () => {
    const view = await open("/sites/KOBO-001?day=2026-10-24");
    const at = paramsOf(where);
    expect([at.get("from"), at.get("to"), at.get("day")]).toEqual(["2026-10-18T00:00:00Z", "2026-10-25T00:00:00Z", "2026-10-24"]);
    view.unmount();
  });

  it("navigate() from a ranged page carries the previous range", async () => {
    const view = await open(`/sites/KOBO-001?${RANGE}`);
    expect(go).not.toBeNull();
    (go as NavigateFunction)("/sites/KISIWA-001/performance");
    await settledScreen();
    const at = paramsOf(where);
    expect(pathOf(where)).toBe("/sites/KISIWA-001/performance");
    expect([at.get("from"), at.get("to")]).toEqual([FROM, TO]);
    view.unmount();
  });

  it("SR-4ab L-3: the previous range wins over the address's day; day is kept", async () => {
    const view = await open(`/sites/KOBO-001?${RANGE}`);
    (go as NavigateFunction)("/sites/KISIWA-001/performance?day=2026-10-24");
    await settledScreen();
    const at = paramsOf(where);
    expect([at.get("from"), at.get("to"), at.get("day")]).toEqual([FROM, TO, "2026-10-24"]);
    view.unmount();
  });

  it("D-SR.59 L-1: per key, the address's own known_at wins over the previous range's; never two", async () => {
    const view = await open(`/sites/KOBO-001?${RANGE}&known_at=2026-11-05T00:00:00Z`);
    (go as NavigateFunction)("/sites/KISIWA-001/performance?known_at=2026-11-07T12:00:00Z");
    await settledScreen();
    const at = paramsOf(where);
    expect([at.get("from"), at.get("to")]).toEqual([FROM, TO]);
    expect(at.getAll("known_at")).toEqual(["2026-11-07T12:00:00Z"]);
    view.unmount();
  });

  it("an invalid range is left alone", async () => {
    const view = await open(`/sites/KOBO-001?from=${TO}&to=${FROM}`);
    const at = paramsOf(where);
    expect([at.get("from"), at.get("to")]).toEqual([TO, FROM]);
    view.unmount();
  });

  it("the Foundation and the Sites index are not filled", async () => {
    let view = await open("/sites/KOBO-001/foundation");
    expect(where).toBe("/sites/KOBO-001/foundation");
    view.unmount();
    view = await open("/sites");
    expect(where).toBe("/sites");
    view.unmount();
  });
});

describe("SR-4ab L-3: Kisiwa's own Performance tab row (Fuel) carries the range", () => {
  it("the Fuel subtab link carries the range and a click on it keeps it", async () => {
    const view = await open(`/sites/KISIWA-001/performance/service?${RANGE}`);
    const fuel = Array.from(document.querySelectorAll<HTMLAnchorElement>("a[href]")).filter(
      (a) => pathOf(a.getAttribute("href") ?? "") === "/sites/KISIWA-001/performance/fuel",
    );
    // Non-vacuous: Kisiwa's capabilities read gives a Fuel subtab.
    expect(fuel.length).toBeGreaterThan(0);
    for (const a of fuel) expect([paramsOf(a.getAttribute("href") ?? "").get("from"), paramsOf(a.getAttribute("href") ?? "").get("to")]).toEqual([FROM, TO]);
    expect(bareSiteHrefs()).toEqual([]);
    fireEvent.click(fuel[0]);
    await settledScreen();
    expect(pathOf(where)).toBe("/sites/KISIWA-001/performance/fuel");
    expect([paramsOf(where).get("from"), paramsOf(where).get("to")]).toEqual([FROM, TO]);
    expect(bareSiteHrefs()).toEqual([]);
    view.unmount();
  });
});
