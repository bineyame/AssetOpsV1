import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import type { ColdAssessmentClient } from "../../sites/coldAssessmentClient";
import type { SiteDetailClient, SiteDirectoryClient } from "../../sites/siteDirectoryClient";
import type { SiteDetailReadModel } from "../../sites/siteReadModel";
import { EMPTY_ANALYTICS_CLIENT } from "../../sites/__tests__/analyticsFixtures";
import { rangeless } from "../../test/rangeless";
import { settledScreen } from "../../test/settled";

/*
 * IA-P P5 (spec "Object pages", D-IAP.38 Q20; closes R383): a Finding detail, the fuel Finding, the domain-action
 * verifications and a Site Action detail are object pages. They draw no Site tab row, and their breadcrumb is the
 * shared `ui/Breadcrumbs` with exactly three parts: `[home list] › [Site name] › [title]`. The home list is Decisions
 * on `recommendation`/`alternatives`, Findings on every other Finding view, Actions on an Action.
 */

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

beforeEach(() => {
  // Every store read the default module clients make is refused (404): the frame, not the body, is the subject.
  vi.stubGlobal("fetch", () =>
    Promise.resolve(new Response(JSON.stringify({ detail: { code: "NOT_FOUND", message: "Not found." } }), { status: 404, headers: { "Content-Type": "application/json" } })),
  );
});

const F = "00000000-0000-4000-8000-000000000901";
const A = "00000000-0000-4000-8000-000000000501";

function site(site_id: string, display_name: string, site_type: string): SiteDetailReadModel {
  return {
    site_id,
    display_name,
    site_type,
    location: { country: "Ethiopia", locality: "Kobo" },
    timezone: "Africa/Addis_Ababa",
    lifecycle_status: "PLANNED",
    origin: "USER",
    source: { mode: "SIMULATED" },
    template: null,
    configuration_store: "POSTGRES",
  } as unknown as SiteDetailReadModel;
}

const SITES = [site("MG-1", "Kobo mini-grid", "MINIGRID"), site("COLD-001", "Kobo vaccine cold store", "COLDCHAIN")];
const detail: SiteDetailClient = {
  getSite: (id: string) => {
    const s = SITES.find((x) => x.site_id === id);
    return Promise.resolve(s === undefined ? { status: "not_found" } : { status: "loaded", site: s }) as ReturnType<SiteDetailClient["getSite"]>;
  },
};
const directory: SiteDirectoryClient = { listSites: () => Promise.resolve({ status: "loaded", sites: SITES }) };
const refused = { status: "refused", httpStatus: 404, code: "COLD_FINDING_NOT_FOUND", message: "No such cold Finding." } as const;
const cold: ColdAssessmentClient = {
  getTemperature: () => Promise.resolve(refused),
  getBackupChain: () => Promise.resolve(refused),
  listFindings: () => Promise.resolve(refused),
  getFinding: () => Promise.resolve(refused),
} as unknown as ColdAssessmentClient;

async function renderAt(path: string) {
  render(
    <MemoryRouter initialEntries={[path]}>
      <App flags={featureFlagsWith(false)} siteDirectory={directory} siteDetail={detail} siteAnalytics={EMPTY_ANALYTICS_CLIENT} coldAssessment={cold} />
    </MemoryRouter>,
  );
  await settledScreen();
}

function crumbs() {
  const navs = screen.getAllByRole("navigation", { name: "Breadcrumb" });
  expect(navs).toHaveLength(1);
  return Array.from(navs[0].querySelectorAll("li")).map((li) => {
    const a = li.querySelector("a");
    return { label: li.textContent?.trim() ?? "", href: a === null ? null : rangeless(a.getAttribute("href")), current: li.querySelector('[aria-current="page"]') !== null };
  });
}

const CASES = [
  ["mini Finding overview", `/sites/MG-1/findings/${F}`, "Findings", "/findings", "MG-1", "Kobo mini-grid", "Finding"],
  ["mini Finding evidence", `/sites/MG-1/findings/${F}/evidence`, "Findings", "/findings", "MG-1", "Kobo mini-grid", "Finding"],
  ["mini Finding history", `/sites/MG-1/findings/${F}/history`, "Findings", "/findings", "MG-1", "Kobo mini-grid", "Finding"],
  ["mini Finding recommendation", `/sites/MG-1/findings/${F}/recommendation`, "Decisions", "/decisions", "MG-1", "Kobo mini-grid", "Finding"],
  ["mini Finding alternatives", `/sites/MG-1/findings/${F}/alternatives`, "Decisions", "/decisions", "MG-1", "Kobo mini-grid", "Finding"],
  ["cold Finding (domain frame)", `/sites/COLD-001/findings/${F}`, "Findings", "/findings", "COLD-001", "Kobo vaccine cold store", "Finding"],
  ["cold Finding evidence (generic frame)", `/sites/COLD-001/findings/${F}/evidence`, "Findings", "/findings", "COLD-001", "Kobo vaccine cold store", "Finding"],
  ["mini Site Action", `/sites/MG-1/actions/${A}`, "Actions", "/actions", "MG-1", "Kobo mini-grid", "Action"],
  ["mini Site Action verification", `/sites/MG-1/actions/${A}/verification`, "Actions", "/actions", "MG-1", "Kobo mini-grid", "Action"],
  ["cold domain Action", `/sites/COLD-001/actions/${A}`, "Actions", "/actions", "COLD-001", "Kobo vaccine cold store", "Action"],
] as const;

describe("IA-P P5: object pages draw no Site tab row and a three-part breadcrumb", () => {
  it.each(CASES)("%s", async (_name, path, home, homeHref, siteId, siteName, title) => {
    await renderAt(path);
    expect(screen.queryByRole("navigation", { name: "Site sections" })).toBeNull();
    expect(document.querySelector("[data-mock-deviation='R383']")).toBeNull();
    const trail = crumbs();
    expect(trail.map((c) => c.label)).toEqual([home, siteName, title]);
    expect(trail[0].href).toBe(homeHref);
    expect(trail[1].href).toBe(`/sites/${siteId}`);
    expect(trail[2]).toMatchObject({ href: null, current: true });
  });
});
