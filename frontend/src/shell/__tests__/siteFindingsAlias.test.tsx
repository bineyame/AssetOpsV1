import { cleanup, render, screen, within } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import type { ColdAssessmentClient } from "../../sites/coldAssessmentClient";
import type { EvAssessmentClient } from "../../sites/evAssessmentClient";
import type { SiteDetailClient, SiteDirectoryClient } from "../../sites/siteDirectoryClient";
import type { SiteDetailReadModel } from "../../sites/siteReadModel";
import { EMPTY_ANALYTICS_CLIENT } from "../../sites/__tests__/analyticsFixtures";
import { rangeless } from "../../test/rangeless";
import { settledScreen } from "../../test/settled";

/*
 * IA-P P5, D-IAP.42 (MD-IAP-15): the Findings alias per vertical. COLD and EV pass both parity layers, so
 * `/sites/:id/findings` on those Sites redirects to `/findings?scope=site:{id}` with the range kept (a type-aware
 * redirect in `SiteFindingsFrame`, not a `LEGACY_ROUTES` entry). MINI does not pass (the estate withholds a PARTIAL
 * mini Site's heads), so its index stays at its address, lit under Evidence, with "Findings" in its section line.
 */

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

beforeEach(() => {
  vi.stubGlobal("fetch", () =>
    Promise.resolve(new Response(JSON.stringify({ detail: { code: "NOT_FOUND", message: "Not found." } }), { status: 404, headers: { "Content-Type": "application/json" } })),
  );
});

function site(site_id: string, display_name: string, site_type: string): SiteDetailReadModel {
  return {
    site_id,
    display_name,
    site_type,
    location: { country: "Ethiopia", locality: "Kobo" },
    timezone: "Africa/Addis_Ababa",
    lifecycle_status: "ACTIVE",
    origin: "USER",
    source: { mode: "SIMULATED" },
    template: null,
    configuration_store: "POSTGRES",
  } as unknown as SiteDetailReadModel;
}

const SITES = [site("MG-1", "Kobo mini-grid", "MINIGRID"), site("COLD-001", "Kobo vaccine cold store", "COLDCHAIN"), site("EV-1", "Kobo charge hub", "EV_CHARGING")];
const detail: SiteDetailClient = {
  getSite: (id: string) => {
    const s = SITES.find((x) => x.site_id === id);
    return Promise.resolve(s === undefined ? { status: "not_found" } : { status: "loaded", site: s }) as ReturnType<SiteDetailClient["getSite"]>;
  },
};
const directory: SiteDirectoryClient = { listSites: () => Promise.resolve({ status: "loaded", sites: SITES }) };
const refused = { status: "refused", httpStatus: 404, code: "NOT_FOUND", message: "Not found." } as const;
const cold = { listFindings: () => Promise.resolve(refused), getFinding: () => Promise.resolve(refused), getTemperature: () => Promise.resolve(refused), getBackupChain: () => Promise.resolve(refused) } as unknown as ColdAssessmentClient;
const ev = { listFindings: () => Promise.resolve(refused), getFinding: () => Promise.resolve(refused), listSessions: () => Promise.resolve(refused), getSession: () => Promise.resolve(refused) } as unknown as EvAssessmentClient;

function LocationProbe() {
  const location = useLocation();
  return <div data-location>{`${location.pathname}${location.search}`}</div>;
}

async function renderAt(path: string) {
  render(
    <MemoryRouter initialEntries={[path]}>
      <App flags={featureFlagsWith(false)} siteDirectory={directory} siteDetail={detail} siteAnalytics={EMPTY_ANALYTICS_CLIENT} coldAssessment={cold} evAssessment={ev} />
      <LocationProbe />
    </MemoryRouter>,
  );
  await settledScreen();
}

const at = () => document.querySelector("[data-location]")!.textContent!;
const RANGE = "from=2026-10-01T00%3A00%3A00Z&to=2026-11-01T00%3A00%3A00Z";
const KNOWN = "2026-11-01T06%3A00%3A00Z";

describe("IA-P P5: the Site Findings alias per vertical (D-IAP.42)", () => {
  it.each([
    ["COLD", "COLD-001"],
    ["EV", "EV-1"],
  ])("%s: /sites/:id/findings redirects to /findings?scope=site:{id}, the range kept", async (_v, id) => {
    await renderAt(`/sites/${id}/findings?${RANGE}&known_at=${KNOWN}&domain=x`);
    const url = new URL(at(), "http://x");
    expect(url.pathname).toBe("/findings");
    expect(url.searchParams.get("scope")).toBe(`site:${id}`);
    expect(url.searchParams.get("from")).toBe("2026-10-01T00:00:00Z");
    expect(url.searchParams.get("to")).toBe("2026-11-01T00:00:00Z");
    expect(url.searchParams.get("known_at")).toBe("2026-11-01T06:00:00Z");
    expect(url.searchParams.get("domain")).toBeNull();
  });

  it("MINI: the index stays (MD-IAP-15), lit under Evidence, with Findings current in its section line", async () => {
    await renderAt(`/sites/MG-1/findings?${RANGE}&known_at=${KNOWN}`);
    expect(new URL(at(), "http://x").pathname).toBe("/sites/MG-1/findings");
    // moved from coldFindingIndex (D-IAP.47, SR-4): a valid address `known_at` travels on every main tab of the kept mini index
    const tabs = Array.from(document.querySelectorAll("nav.site-tabs:not(.site-subtabs) a.site-tabs__link"));
    expect(tabs.length).toBeGreaterThan(0);
    for (const a of tabs) expect(new URLSearchParams((a.getAttribute("href") ?? "").split("?")[1] ?? "").get("known_at")).toBe("2026-11-01T06:00:00Z");
    const row = screen.getByRole("navigation", { name: "Site sections" });
    expect(within(row).queryByRole("link", { name: "Findings" })).toBeNull();
    expect(within(row).getByRole("link", { name: "Evidence" })).toHaveAttribute("aria-current", "page");
    const lines = screen.getAllByRole("navigation", { name: "Evidence sections" });
    expect(lines).toHaveLength(1);
    const links = within(lines[0]).getAllByRole("link").map((a) => [a.textContent, rangeless(a.getAttribute("href")), a.getAttribute("aria-current")]);
    expect(links).toEqual([
      ["Records", "/sites/MG-1/evidence", null],
      ["Uploads", "/sites/MG-1/uploads", null],
      ["Findings", "/sites/MG-1/findings", "page"],
    ]);
  });

  it("MINI: the Evidence page's line carries Findings too (the index is reachable without the tab)", async () => {
    await renderAt(`/sites/MG-1/evidence?${RANGE}`);
    const line = screen.getAllByRole("navigation", { name: "Evidence sections" });
    expect(line).toHaveLength(1);
    expect(within(line[0]).getAllByRole("link").map((a) => a.textContent)).toEqual(["Records", "Uploads", "Findings"]);
  });

  it.each([
    ["COLD", "COLD-001", "/sites/COLD-001/evidence"],
    ["EV", "EV-1", "/sites/EV-1/ev/evidence"],
  ])("%s: Uploads draws the one Evidence line, Records · Analysis · Uploads, with no Findings link", async (_v, id, records) => {
    await renderAt(`/sites/${id}/uploads?${RANGE}`);
    const line = screen.getAllByRole("navigation", { name: "Evidence sections" });
    expect(line).toHaveLength(1);
    const links = within(line[0]).getAllByRole("link").map((a) => [a.textContent, rangeless(a.getAttribute("href"))?.split("?")[0], a.getAttribute("aria-current")]);
    expect(links.map((l) => l[0])).toEqual(["Records", "Analysis", "Uploads"]);
    expect(links[0][1]).toBe(records);
    expect(links[2][2]).toBe("page");
  });
});
