/**
 * W1-F4 group B (`D-2026-10-17-mockup-layout-spec`): the `changes` and
 * `sitework` routes render exactly their v69 panels, in order, in stocked,
 * empty and refused/unavailable variants, with any unsupported read stated
 * inside its panel slot and no leading answer card.
 *
 * Both routes mount through the real `App`. `fetch` serves the committed wire
 * contracts (`s6_action_api_contract.json`, `s6_site_action_index_contract.json`);
 * derived bodies say so where they are built.
 */
import { cleanup, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import actionContract from "../../../../backend/tests/fixtures/s6_action_api_contract.json";
import indexContract from "../../../../backend/tests/fixtures/s6_site_action_index_contract.json";
import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import { expectPlantedPanelRejected, expectV69Panels, panelTitled } from "../../test/panelStructure";
import { settledScreen } from "../../test/settled";
import type { SiteDetailClient, SiteDirectoryClient } from "../siteDirectoryClient";
import { EMPTY_ANALYTICS_CLIENT } from "./analyticsFixtures";
import { HYBRID_MINI_GRID_SITE } from "./sldFixtures";
import { COLD_SITE, SITE as COLD_CODE, coldFetch, domainRow, indexBody } from "./coldWorkFixtures";
import { EV_SITE, EV_SITE_CODE, evIndexBody, evRow } from "./evWorkFixtures";

type Case = { request: { path: string }; status: number; body: any };
type Served = { status: number; body: unknown };
const M = actionContract.manifest as unknown as Record<string, Record<string, Case>>;
const changes = M["changes:1#a"];
const hi = M["action-history:1#a"];
const CHANGE = changes.change.body.change;
const CHANGE_URL = `/sites/KOBO-001/foundation/changes/${CHANGE.change_id as string}`;
const EVENTS_API = `/api/sites/KOBO-001/actions/${CHANGE.action_id as string}/events`;

const D = indexContract.d_action_records as unknown as Record<string, any>;
const WINDOW = D.positive_window as { from: string; to: string };
const ZERO_WINDOW = D.zero_window as { from: string; to: string };
const workUrl = (w: { from: string; to: string }) =>
  `/sites/KOBO-001/work?${new URLSearchParams({ from: w.from, to: w.to }).toString()}`;
const indexApi = (w: { from: string; to: string }) =>
  `/api/sites/KOBO-001/action-index?${new URLSearchParams({ from: w.from, to: w.to }).toString()}`;

function serve(gets: Record<string, Served>) {
  const requests: string[] = [];
  vi.stubGlobal("fetch", async (url: string) => {
    const path = decodeURIComponent(String(url));
    requests.push(path);
    const hit = gets[path] ?? gets[String(url)];
    if (!hit) return new Response(JSON.stringify({ detail: { code: "TEST_UNMATCHED", message: path } }), { status: 599 });
    return new Response(JSON.stringify(hit.body), { status: hit.status });
  });
  return requests;
}

const served = (c: Case): Served => ({ status: c.status, body: c.body });
const detail: SiteDetailClient = {
  getSite: async (siteId: string) => ({ status: "loaded", site: { ...HYBRID_MINI_GRID_SITE, site_id: siteId } }),
} as SiteDetailClient;
const directory: SiteDirectoryClient = {
  listSites: async () => ({ status: "loaded", sites: [HYBRID_MINI_GRID_SITE] }),
} as SiteDirectoryClient;

function mount(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App flags={featureFlagsWith(false)} siteDirectory={directory} siteDetail={detail} siteAnalytics={EMPTY_ANALYTICS_CLIENT} />
    </MemoryRouter>,
  );
}

const q = (selector: string) => document.querySelector(selector);
const gaps = () => Array.from(document.querySelectorAll("[data-panel-gap]"));

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("W1-F4: changes keeps the v69 panel structure in every variant", () => {
  it("stocked (applied change, no plan yet): Change and effect | Decision path, no answer card", async () => {
    serve({ [changes.change.request.path]: served(changes.change), [EVENTS_API]: served(hi.events_latest) });
    mount(CHANGE_URL);
    await settledScreen();
    expectV69Panels("changes");
    expect(q("[data-headline-card]")).toBeNull();
    expect(q("[data-page-refusal]")).toBeNull();
    // The mock's leading patterns: one status strip and four metric cards from the real read.
    expect(document.querySelectorAll("main .status-strip")).toHaveLength(1);
    expect(document.querySelectorAll("[data-change-metric]")).toHaveLength(4);
    expect(panelTitled("Change and effect").querySelector("[data-change-values]")).not.toBeNull();
    expect(panelTitled("Change and effect").querySelector("[data-change-attempts]")).not.toBeNull();
    // No plan and no outcome: the Decision path says so inside its own slot.
    const path = panelTitled("Decision path");
    expect(path.querySelectorAll("[data-change-decision-path] > li")).toHaveLength(3);
    expect(path.textContent).toContain("Not recorded yet.");
    expect(path.querySelector("[data-change-plan-link]")).toBeNull();
  });

  it("empty (an older server sends no verification block): the outcome is a stated gap, never pending-as-success", async () => {
    const body = structuredClone(changes.change.body); // Derived: the verification block removed.
    delete body.verification;
    serve({ [changes.change.request.path]: { status: 200, body }, [EVENTS_API]: served(hi.events_latest) });
    mount(CHANGE_URL);
    await settledScreen();
    expectV69Panels("changes");
    expect(q("[data-change-metric='outcome']")?.textContent).toMatch(/Not available/);
    expect(panelTitled("Decision path").querySelector("[data-trial-verification-state='UNAVAILABLE']")).not.toBeNull();
    expect(panelTitled("Decision path").textContent).toContain("Not recorded yet.");
  });

  it("attempts read refused: the gap stays inside Change and effect; no extra refusal panel", async () => {
    serve({
      [changes.change.request.path]: served(changes.change),
      [EVENTS_API]: { status: 503, body: { detail: { code: "ACTION_STORE_UNAVAILABLE", message: "down" } } }, // Derived.
    });
    mount(CHANGE_URL);
    await settledScreen();
    expectV69Panels("changes");
    expect(panelTitled("Change and effect").querySelector("[data-action-code='ACTION_STORE_UNAVAILABLE']")).not.toBeNull();
  });

  it("refused (wrong-Site change, 404): a page-level refusal, then both slots with the gap inside", async () => {
    serve({ [changes.wrong_site_404.request.path]: served(changes.wrong_site_404) });
    mount(`/sites/OTHER-001/foundation/changes/${CHANGE.change_id as string}`);
    await settledScreen();
    expect(q('[data-page-refusal="not-found"]')).not.toBeNull();
    expectV69Panels("changes");
    expect(gaps()).toHaveLength(2);
    for (const gap of gaps()) expect(gap.textContent).toContain("No change with this address is recorded for this site.");
    expect(q("[data-headline-card]")).toBeNull();
  });
});

describe("W1-F4: sitework keeps the v69 panel structure in every variant", () => {
  it("stocked: one Actions at this site panel with the table, no top card", async () => {
    serve({ [indexApi(WINDOW)]: { status: 200, body: D.positive } });
    mount(workUrl(WINDOW));
    await settledScreen();
    expectV69Panels("sitework");
    expect(q("[data-headline-card]")).toBeNull();
    const panel = panelTitled("Actions at this site");
    expect(panel.querySelectorAll("[data-site-work-row]").length).toBe(D.positive.rows.length);
    expect(Array.from(panel.querySelectorAll("thead th")).slice(0, 6).map((th) => th.textContent)).toEqual(["Action", "Source", "Owner", "Due", "State", "Success criterion"]);
    for (const row of Array.from(panel.querySelectorAll("[data-site-work-row]"))) expect(row.querySelector(".w1f4-action-badge")).not.toBeNull();
    // The window controls are chip-sized controls inside the one panel.
    expect(panel.querySelector("form.v69-chips[data-site-work-window]")).not.toBeNull();
    expect(panel.querySelector("[data-site-work-not-included]")).not.toBeNull();
    expect(q("[data-site-work] .status-strip [data-site-work-scope]")?.textContent).toContain(
      `Scoped to ${HYBRID_MINI_GRID_SITE.display_name}`,
    );
    // post-W6 W1-b Q36 / R230: the mini strip links the mounted global Actions list.
    const strip = q("[data-site-work] .status-strip") as HTMLElement;
    const manage = strip.querySelector("[data-site-work-manage]") as HTMLAnchorElement;
    expect(manage.textContent).toBe("Manage in Actions →");
    expect(manage.getAttribute("href")).toBe("/actions");
    expect(document.querySelectorAll("[data-site-work-manage]")).toHaveLength(1);
  });

  it("W4-01: the Work row is the mock's Actions | Incidents | Maintenance, all three live, Actions current", async () => {
    serve({ [indexApi(WINDOW)]: { status: 200, body: D.positive } });
    mount(workUrl(WINDOW));
    await settledScreen();
    const row = screen.getByRole("navigation", { name: "Work lists" });
    // H1: each label carries its count slot; this fixture serves no count read, so each is unknown (a dash, not 0).
    expect(within(row).getAllByRole("link").map((l) => l.textContent)).toEqual(["Actions (—)", "Incidents (—)", "Maintenance (—)"]);
    const links = within(row).getAllByRole("link");
    expect(links.map((l) => [l.textContent?.replace(/ \(.*\)$/, ""), l.getAttribute("href"), l.getAttribute("aria-current")])).toEqual([
      ["Actions", "/sites/KOBO-001/work", "page"],
      ["Incidents", "/sites/KOBO-001/work/incidents", null],
      ["Maintenance", "/sites/KOBO-001/work/maintenance", null],
    ]);
    expect(row.querySelectorAll("[data-tab-unavailable]")).toHaveLength(0);
    // W1-F5b carry 11: the breadcrumb names the site, not its raw code.
    const trail = screen.getByRole("navigation", { name: "Breadcrumb" });
    expect(within(trail).getByRole("link", { name: HYBRID_MINI_GRID_SITE.display_name })).toHaveAttribute("href", "/sites/KOBO-001");
    expect(trail.textContent).not.toContain("KOBO-001");
  });

  it("empty (proved zero): the same slot states the checked zero with its read time", async () => {
    serve({ [indexApi(ZERO_WINDOW)]: { status: 200, body: D.zero } });
    mount(workUrl(ZERO_WINDOW));
    await settledScreen();
    expectV69Panels("sitework");
    const panel = panelTitled("Actions at this site");
    expect(panel.querySelector("[data-site-work-proved-zero]")?.getAttribute("data-site-work-proved-zero")).toBe(D.zero.read_at);
    expect(panel.querySelector("[data-panel-gap]")).toBeNull();
  });

  it("no window chosen: the slot asks for a window and nothing is read", async () => {
    const requests = serve({});
    mount("/sites/KOBO-001/work");
    await settledScreen();
    expectV69Panels("sitework");
    expect(panelTitled("Actions at this site").querySelector("[data-panel-gap]")?.textContent).toContain("Choose a window");
    expect(requests.filter((r) => r.includes("action-index"))).toEqual([]);
  });

  it.each([
    ["unavailable", { status: 500, body: { detail: "boom" } }, "Actions not known right now"],
    ["forbidden", { status: 403, body: { detail: { code: "SITE_SCOPE_FORBIDDEN", message: "No access." } } }, "No access to this site's Actions"],
    ["basis-changed", D.basis_changed as Served, "This list changed"],
  ])("refused (%s): the gap is inside the slot, distinct from zero", async (state, response, title) => {
    serve({ [indexApi(WINDOW)]: response });
    mount(workUrl(WINDOW));
    await settledScreen();
    expectV69Panels("sitework");
    const gap = panelTitled("Actions at this site").querySelector("[data-panel-gap]") as HTMLElement;
    expect(gap.getAttribute("data-site-work-state")).toBe(state);
    expect(gap.textContent).toContain(title);
    expect(document.body.textContent).not.toMatch(/No Actions created|Showing \d/);
  });
});

describe("W1-F4: the guard is not vacuous on changes and sitework", () => {
  it("changes: a planted extra panel before panel 1 fails", async () => {
    serve({ [changes.change.request.path]: served(changes.change), [EVENTS_API]: served(hi.events_latest) });
    mount(CHANGE_URL);
    await settledScreen();
    expectPlantedPanelRejected("changes");
  });

  it("sitework: a planted extra panel before panel 1 fails", async () => {
    serve({ [indexApi(WINDOW)]: { status: 200, body: D.positive } });
    mount(workUrl(WINDOW));
    await settledScreen();
    expectPlantedPanelRejected("sitework");
  });
});

/* W5-02 K2a: the COLDCHAIN Actions tab keeps the v69 `cold-work` structure (strip, one panel, notice). */
describe("W5-02 K2a: cold-work keeps the v69 panel structure", () => {
  function mountCold(path: string) {
    const cold: SiteDetailClient = { getSite: () => Promise.resolve({ status: "loaded", site: COLD_SITE }) };
    const dir: SiteDirectoryClient = { listSites: () => Promise.resolve({ status: "loaded", sites: [COLD_SITE] }) };
    return render(
      <MemoryRouter initialEntries={[path]}>
        <App flags={featureFlagsWith(false)} siteDirectory={dir} siteDetail={cold} siteAnalytics={EMPTY_ANALYTICS_CLIENT} />
      </MemoryRouter>,
    );
  }

  for (const [name, body] of [
    ["stocked", indexBody([domainRow()])],
    ["complete zero", indexBody([])],
  ] as const) {
    it(`${name}: one Actions at this site panel; the strip holds only one-line parts; a planted panel is rejected`, async () => {
      vi.stubGlobal("fetch", coldFetch(body).fetchStub);
      mountCold(`/sites/${COLD_CODE}/work`);
      await settledScreen();
      expectV69Panels("cold-work");
      expectPlantedPanelRejected("cold-work");
      expect(q("[data-headline-card]")).toBeNull();
      expect(panelTitled("Actions at this site").querySelector("form")).toBeNull();
    });
  }

  it("refused: the refusal sits inside the one panel, never as a zero", async () => {
    vi.stubGlobal("fetch", async () => new Response(JSON.stringify({ detail: { code: "WORK_STORE_UNAVAILABLE", message: "Unavailable." } }), { status: 503 }));
    mountCold(`/sites/${COLD_CODE}/work`);
    await settledScreen();
    expectV69Panels("cold-work");
    expect(panelTitled("Actions at this site").querySelector("[data-cold-work-refusal]")).not.toBeNull();
    expect(q("[data-cold-work-empty]")).toBeNull();
  });
});

/* W5-04 V2a: the EV_CHARGING Actions tab keeps the v69 `ev-work` structure through the App routes (pure fixtures). */
describe("W5-04 V2a: ev-work keeps the v69 panel structure", () => {
  function mountEv(path: string) {
    const ev: SiteDetailClient = { getSite: () => Promise.resolve({ status: "loaded", site: EV_SITE }) };
    const dir: SiteDirectoryClient = { listSites: () => Promise.resolve({ status: "loaded", sites: [EV_SITE] }) };
    return render(
      <MemoryRouter initialEntries={[path]}>
        <App flags={featureFlagsWith(false)} siteDirectory={dir} siteDetail={ev} siteAnalytics={EMPTY_ANALYTICS_CLIENT} />
      </MemoryRouter>,
    );
  }
  const evFetch = (status: number, body: unknown) => async (url: string) =>
    url.split("?")[0] === `/api/sites/${EV_SITE_CODE}/domain-work/action-index`
      ? new Response(JSON.stringify(body), { status })
      : new Response(JSON.stringify({ detail: { code: "WORK_STORE_UNAVAILABLE", message: "Unavailable in this test." } }), { status: 503 });

  for (const [name, body] of [
    ["positive", evIndexBody([evRow()])],
    ["complete zero", evIndexBody([])],
  ] as const) {
    it(`${name}: one Actions at this site panel; a planted panel is rejected; the EV code links only to its detail (V4a, R113)`, async () => {
      vi.stubGlobal("fetch", evFetch(200, body));
      mountEv(`/sites/${EV_SITE_CODE}/work`);
      await settledScreen();
      expectV69Panels("ev-work");
      expectPlantedPanelRejected("ev-work");
      expect(panelTitled("Actions at this site").querySelector("form")).toBeNull();
      expect(q("[data-cold-work]")).toBeNull();
      // W5-04 V4a closes R113: the one live EV detail link is the selected row's own `/verification` href.
      // Ruling 67: the href also carries the selected window (`from,to`), never a cursor.
      expect(Array.from(document.querySelectorAll("main a[href*='/verification']")).map((a) => (a.getAttribute("href") ?? "").split("?")[0])).toEqual(
        body.rows.length === 0 ? [] : [`/sites/${EV_SITE_CODE}/actions/${body.rows[0].action_id}/verification`],
      );
    });
  }

  it("refused: the EV refusal sits inside the one panel, never as a zero", async () => {
    vi.stubGlobal("fetch", evFetch(503, { detail: { code: "WORK_STORE_UNAVAILABLE", message: "Unavailable." } }));
    mountEv(`/sites/${EV_SITE_CODE}/work`);
    await settledScreen();
    expectV69Panels("ev-work");
    const refusal = panelTitled("Actions at this site").querySelector("[data-domain-work-refusal]");
    expect(refusal?.textContent).toContain("EV work unavailable");
    expect(q("[data-domain-work-empty]")).toBeNull();
  });
});
