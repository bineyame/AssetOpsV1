import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { act } from "react";
import { MemoryRouter, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import {
  ANALYSIS_HELPER_ALTERNATIVES,
  ANALYSIS_HELPER_SECTION,
  FinancialsSections,
  SiteFindingFrame,
} from "../../shell/SiteAnalyticsFrames";
import { siteFindingAlternativesHref, siteOpportunityHref } from "../../shell/operatorSiteRoutes";
import type { FindingClient, FindingDetailBody, FindingReadResult } from "../findingClient";
import { useResolvedAlternativesHref } from "../SitePerformance";
import type {
  AlternativeListBody,
  AlternativeRow,
  DecisionRead,
  AlternativesPage,
  MiniDecisionsClient,
  OpportunityDetailBody,
  OpportunityListBody,
  OpportunityObject,
  ScenarioListBody,
  ScenarioRow,
} from "../miniDecisionsClient";
import { createMiniDecisionsClient, microsecondBefore } from "../miniDecisionsClient";
import { scenarioMoney } from "../MiniScenarios";
import { OpportunityDecisionEntry } from "../MiniOpportunity";
import { SiteFindingIndex } from "../SiteFindingIndex";
import type { FindingIndexClient } from "../findingIndexClient";
import type { SiteDetailClient, SiteDirectoryClient } from "../siteDirectoryClient";
import type { SiteDetailReadModel } from "../siteReadModel";
import { EMPTY_ANALYTICS_CLIENT } from "./analyticsFixtures";
import { settledScreen } from "../../test/settled";
import { expectPlantedPanelRejected, expectV69Panels, panelTitled } from "../../test/panelStructure";

/*
 * W4-03 unit 6a ("Unit-5..12 rulings (u5)" Units 6a-6b; closure 1 Scenarios UI; closure 4 S13/S15): mini
 * Financials > Scenarios reads `mini-scenarios-1` read-only. The first GET omits both bounds; the page shows
 * `Scenarios created through {window.to - 1 us}` and reuses the returned bounds and cutoff for cursor pages and
 * reload. Cold keeps the one unavailable Scenarios subtab; EV has none; neither reads scenarios.
 */

afterEach(cleanup);

const CODE = "MG-W403-001";
const id = (n: number) => `00000000-0000-4000-8000-${String(n).padStart(12, "0")}`;
const NOTICE =
  "Scenarios never change measured results or the consequence lines on Overview. They are labelled what-ifs, kept separate from evidence.";
const FROM = "1970-01-01T00:00:00.000000Z";
const TO = "2026-10-21T08:00:00.000000Z";
const KNOWN = "2026-10-21T07:59:59.999999Z";

function site(code: string, siteType: string): SiteDetailReadModel {
  return {
    site_id: code,
    display_name: `${siteType} site`,
    site_type: siteType,
    location: { country: "Kenya", locality: "Nairobi" },
    timezone: "Africa/Nairobi",
    lifecycle_status: "PLANNED",
    origin: "USER",
    source: { mode: "SIMULATED" },
    template: null,
    configuration_store: "POSTGRES",
  } as unknown as SiteDetailReadModel;
}

function row(over: Partial<ScenarioRow> = {}): ScenarioRow {
  return {
    id: id(10),
    code: "SCN-000004",
    revision_id: id(11),
    name: "Grain mill one-hour trial",
    kind: "PRODUCTIVE_LOAD",
    narrative: "Illustrative productive-load trial.",
    authored_at: "2026-10-20T10:00:00.000000Z",
    actor_id: "service:w403-fixture",
    assumptions: [
      { key: "proposed_kw", value: "10", unit: "kW", source: "Authored trial" },
      { key: "duration_hours", value: "1", unit: "h", source: "Authored trial" },
      { key: "tariff_per_kwh", value: "0.25", unit: "USD/kWh", source: "Authored" },
    ],
    pinned_mini_revision_ids: [id(21), id(22)],
    scenario_state: "DEFINED",
    calculation_state: "GROSS_SCENARIO",
    energy_kwh: "10",
    gross_sales: { amount: "2.5", currency: "USD", basis: "SCENARIO" },
    limitations: [],
    url: null,
    ...over,
  };
}

function list(rows: ScenarioRow[], over: Partial<ScenarioListBody> = {}): ScenarioListBody {
  return {
    schema_version: "mini-scenarios-1",
    window: { from: FROM, to: TO, known_at: KNOWN },
    status: "UNKNOWN",
    currentness: { state: "UNKNOWN", job_state: "NONE" },
    total_count: rows.length,
    rows,
    next_cursor: null,
    selection_token: "sha256:" + "a".repeat(64),
    ...over,
  };
}

const ok = (value: ScenarioListBody): DecisionRead<ScenarioListBody> => ({ status: "loaded", value });

/** A test-only in-app navigation (an identity change within one mounted frame, u6b ruling 8). */
let goTo: ((path: string) => void) | null = null;
function Go() {
  const navigate = useNavigate();
  goTo = (path) => navigate(path);
  return null;
}

function Where() {
  const location = useLocation();
  return <output data-location>{location.pathname + location.search}</output>;
}

function renderAt(path: string, answers: DecisionRead<ScenarioListBody>[], siteType = "MINIGRID", code = CODE) {
  const queue = [...answers];
  const client: MiniDecisionsClient = {
    getScenarios: vi.fn(() => Promise.resolve(queue.length > 1 ? queue.shift()! : queue[0])),
    getAlternatives: vi.fn(() => Promise.resolve({ status: "unavailable" as const, message: null })),
    getOpportunity: vi.fn(() => Promise.resolve({ status: "unavailable" as const, message: null })),
    listOpportunities: vi.fn(() => Promise.resolve({ status: "unavailable" as const, message: null })),
    getWorkContexts: vi.fn(() => Promise.resolve({ status: "unavailable" as const, message: null })),
  };
  const s = site(code, siteType);
  const detail: SiteDetailClient = { getSite: () => Promise.resolve({ status: "loaded", site: s }) };
  const directory: SiteDirectoryClient = { listSites: () => Promise.resolve({ status: "loaded", sites: [s] }) };
  render(
    <MemoryRouter initialEntries={[path]}>
      <App flags={featureFlagsWith(false)} siteDirectory={directory} siteDetail={detail} siteAnalytics={EMPTY_ANALYTICS_CLIENT} miniDecisions={client} />
      <Where />
    </MemoryRouter>,
  );
  return client;
}

const main = () => document.querySelector("main") as HTMLElement;
const location = () => document.querySelector("[data-location]")?.textContent ?? "";
const subtabs = () =>
  Array.from(document.querySelectorAll('nav[aria-label="Financials sections"] li')).map((li) => [
    li.textContent,
    li.querySelector("a")?.getAttribute("aria-current") ?? null,
  ]);
const cells = () =>
  Array.from(document.querySelectorAll("[data-scenarios-table] tbody tr")).map((tr) =>
    Array.from(tr.querySelectorAll("th, td")).map((c) => c.textContent),
  );
const noControl = (el: Element | null) => {
  expect(el).not.toBeNull();
  expect(el!.closest("a, button")).toBeNull();
  expect(el!.querySelector("a, button")).toBeNull();
  expect(el!.getAttribute("href")).toBeNull();
  expect(el!.getAttribute("tabindex")).toBeNull();
};

/** u9b: every link in the screen content resolves to an exact in-app route; no dead or placeholder control. */
const noDeadCta = (scope: HTMLElement) => {
  for (const a of Array.from(scope.querySelectorAll("a"))) {
    const href = a.getAttribute("href") ?? "";
    expect(href, `link "${a.textContent}"`).toMatch(/^\/[a-z]/);
    expect(href, `link "${a.textContent}"`).not.toMatch(/undefined|null|#$|\/\/|\s/);
  }
  for (const b of Array.from(scope.querySelectorAll("button"))) {
    expect(b.hasAttribute("disabled"), `button "${b.textContent}"`).toBe(false);
    expect(b.getAttribute("aria-disabled"), `button "${b.textContent}"`).not.toBe("true");
  }
  expect(scope.querySelector('[href="#"], [data-placeholder], [data-mock-only]')).toBeNull();
};
/** u9b: the narrow viewport the mock budgets were measured at. */
const atWidth = (w: number) => {
  Object.defineProperty(window, "innerWidth", { configurable: true, writable: true, value: w });
  window.dispatchEvent(new Event("resize"));
};
// The stylesheet as text (jsdom has no layout); Node's fs is untyped here, paths relative to `frontend/` (estate pattern).
const NODE_FS = (await import(/* @vite-ignore */ `node:${"fs"}`)) as { readFileSync: (p: string, e: string) => string };
const FRONTEND_CWD = (globalThis as unknown as { process: { cwd: () => string } }).process.cwd();
const MINI_CSS = NODE_FS.readFileSync(`${FRONTEND_CWD}/src/sites/w4-mini-decisions.css`, "utf8").replace(/\s+/g, " ");

describe("W4-03 unit 6a: mini Financials > Scenarios", () => {
  it("scenario_empty_populated_and_refused", async () => {
    renderAt(`/sites/${CODE}/financials/scenarios`, [ok(list([]))]);
    await settledScreen();
    await screen.findByText("No scenario defined yet");
    expect(main().textContent).toContain(
      "A scenario compares a declared what-if with the measured case. None has been defined for this site.",
    );
    // PR-12.1: the mock's single explanatory sentence only; no secondary example and no foot line.
    expect(main().textContent).not.toContain("For example, a different stop setting");
    expect(main().textContent).not.toContain("No authored what-if at this site and cutoff.");
    expect(document.querySelectorAll("[data-scenarios-empty] p")).toHaveLength(1);
    expect(document.querySelector("[data-scenario-creation-unavailable]")?.textContent).toBe("Scenario creation unavailable");
    expect(main().textContent).toContain("Declared scenarios are separate from measured results.");
    expect(main().textContent).not.toMatch(/Placeholder|to be designed/);
    expect(document.querySelector("[data-scenarios-table]")).toBeNull(); // no invented row
    expect(document.querySelector("[data-scenarios-notice]")?.textContent).toBe(NOTICE);
    cleanup();

    renderAt(`/sites/${CODE}/financials/scenarios`, [
      ok(
        list([
          row(),
          row({
            id: id(30),
            code: "SCN-1234567",
            revision_id: id(31),
            name: "Tariff check",
            kind: "TARIFF_ONLY",
            assumptions: [{ key: "tariff_per_kwh", value: "30", unit: "KES/kWh", source: "Authored" }],
            pinned_mini_revision_ids: [],
            calculation_state: "NO_CALCULATION",
            energy_kwh: null,
            gross_sales: null,
          }),
        ]),
      ),
    ]);
    await settledScreen();
    await screen.findByText("Grain mill one-hour trial");
    const head = Array.from(document.querySelectorAll("[data-scenarios-table] thead th"), (th) => th.textContent);
    expect(head).toEqual(["Scenario", "Declared change", "Physical basis", "Illustrative result", "State"]);
    const widths = Array.from(document.querySelectorAll("[data-scenarios-table] col"), (c) => (c as HTMLElement).style.width);
    expect(widths).toEqual(["20%", "24%", "20%", "22%", "14%"]);
    const [first, second] = cells();
    expect(first[0]).toBe("Grain mill one-hour trial · Productive load · SCN-000004Scenario detail unavailable");
    expect(first[1]).toBe("proposed_kw 10 kW; duration_hours 1 h; tariff_per_kwh 0.25 USD/kWh");
    expect(first[2]).toBe("2 pinned renewable revisions Inspect pinned revisions");
    expect(first[3]).toBe("$2.50 gross sales scenario per eligible window, before costs");
    expect(first[4]).toBe("Defined · Gross scenario");
    expect(second[0]).toContain("SCN-1234567"); // never truncated above 999999
    expect(second.slice(1)).toEqual([
      "tariff_per_kwh 30 KES/kWh",
      "No measured basis pinned",
      "Cannot calculate from the selected evidence",
      "Defined · No calculation",
    ]);
    expect(document.querySelector("[data-scenarios-notice]")?.textContent).toBe(NOTICE);
    cleanup();

    // A store failure is the refusal copy, never the empty block.
    renderAt(`/sites/${CODE}/financials/scenarios`, [
      { status: "refused", httpStatus: 503, code: "DECISION_STORE_UNAVAILABLE", message: "The decision store is unavailable." },
    ]);
    await settledScreen();
    await screen.findByText("The decision store is unavailable.");
    expect(document.querySelector("[data-scenarios-refused]")).toHaveAttribute("data-scenarios-refused", "DECISION_STORE_UNAVAILABLE");
    expect(main().textContent).not.toContain("No scenario defined yet");
    expect(document.querySelector("[data-scenarios-notice]")?.textContent).toBe(NOTICE);
    // Exact decimal money: half-even to minor units; a non-USD code is written out.
    expect([scenarioMoney("2.5", "USD"), scenarioMoney("2.505", "USD"), scenarioMoney("2.515", "USD"), scenarioMoney("2.5051", "KES")]).toEqual([
      "$2.50",
      "$2.50",
      "$2.52",
      "KES 2.51",
    ]);
  });

  it("scenario_creation_time_bounds_and_null_destinations", async () => {
    const pageTwo = list([row({ id: id(40), revision_id: id(41), name: "Second", scenario_state: "HISTORICAL" })], {
      total_count: 2,
    });
    const client = renderAt(`/sites/${CODE}/financials/scenarios`, [
      ok(list([row()], { total_count: 2, next_cursor: "cursor-2" })),
      ok(pageTwo),
    ]);
    await settledScreen();
    await screen.findByText("Grain mill one-hour trial");
    // The first GET omits both bounds and the cutoff; the page states the effective creation-time end.
    expect(client.getScenarios).toHaveBeenNthCalledWith(1, CODE, { from: null, to: null, known_at: null, cursor: null });
    expect(document.querySelector("[data-scenarios-through]")?.textContent).toBe(
      "Scenarios created through 2026-10-21T07:59:59.999999Z",
    );
    expect(microsecondBefore("2026-10-21T08:00:00.000000Z")).toBe("2026-10-21T07:59:59.999999Z");
    expect(microsecondBefore("2026-10-21T08:00:00.000123Z")).toBe("2026-10-21T08:00:00.000122Z");
    // The returned bounds and cutoff go into the address (reload reads the same set) without a second read.
    expect(location()).toBe(
      `/sites/${CODE}/financials/scenarios?from=${encodeURIComponent(FROM)}&to=${encodeURIComponent(TO)}&known_at=${encodeURIComponent(KNOWN)}`,
    );
    expect(client.getScenarios).toHaveBeenCalledTimes(1);
    // Null destinations are plain text: no link, button or focus stop.
    noControl(document.querySelector("[data-scenario-detail-unavailable]"));
    expect(document.querySelector("[data-scenario-detail-unavailable]")?.textContent).toBe("Scenario detail unavailable");
    noControl(document.querySelector("[data-scenario-creation-unavailable]"));
    expect(document.querySelector("[data-scenario-creation-unavailable]")?.textContent).toBe("Scenario creation unavailable");
    expect(main().querySelector("form, input, textarea")).toBeNull();
    // A cursor page reuses the returned bounds and cutoff, never the browser clock or a renewable window.
    fireEvent.click(document.querySelector("[data-scenarios-next]")!);
    await screen.findByText("Second");
    expect(client.getScenarios).toHaveBeenNthCalledWith(2, CODE, { from: FROM, to: TO, known_at: KNOWN, cursor: "cursor-2" });
    expect(cells()[0][4]).toBe("Historical basis · Gross scenario");
    cleanup();

    // Reload of that address reads the same explicit set.
    const reload = renderAt(
      `/sites/${CODE}/financials/scenarios?from=${encodeURIComponent(FROM)}&to=${encodeURIComponent(TO)}&known_at=${encodeURIComponent(KNOWN)}`,
      [ok(list([row()]))],
    );
    await settledScreen();
    await screen.findByText("Grain mill one-hour trial");
    expect(reload.getScenarios).toHaveBeenCalledTimes(1);
    expect(reload.getScenarios).toHaveBeenCalledWith(CODE, { from: FROM, to: TO, known_at: KNOWN, cursor: null });
  });

  it("u9b_pinned_revisions_disclosure_keyboard_reachable", async () => {
    const pins = [41, 42, 43, 44, 45].map((n) => id(n));
    renderAt(`/sites/${CODE}/financials/scenarios`, [ok(list([row({ pinned_mini_revision_ids: pins }), row({ id: id(50), revision_id: id(51), code: "SCN-000005" })]))]);
    await settledScreen();
    await waitFor(() => expect(cells()).toHaveLength(2));
    // The cell states the count; no exact ID is inside the row layout.
    expect(cells()[0][2]).toBe("5 pinned renewable revisions Inspect pinned revisions");
    const table = document.querySelector("[data-scenarios-table] table") as HTMLElement;
    for (const pin of pins) expect(table.textContent).not.toContain(pin);
    const region = document.getElementById("mini-scenarios-pinned") as HTMLElement;
    expect(region.hidden).toBe(true); // closed: no rendered height
    expect(region.textContent).toBe("");
    expect(region.closest("table")).toBeNull(); // outside the row layout
    const button = document.querySelector(`[data-scenario-inspect="${id(10)}"]`) as HTMLButtonElement;
    expect(button.tagName).toBe("BUTTON"); // native button: Enter and Space operate it
    expect(button.type).toBe("button");
    expect(button).toHaveAttribute("aria-controls", "mini-scenarios-pinned");
    expect(button).toHaveAttribute("aria-expanded", "false");
    button.focus();
    expect(document.activeElement).toBe(button);
    fireEvent.click(button);
    expect(button).toHaveAttribute("aria-expanded", "true");
    expect(region.hidden).toBe(false);
    expect(region.tabIndex).toBe(0); // the bounded list scrolls by keyboard
    expect(Array.from(region.querySelectorAll("code"), (c) => c.textContent)).toEqual(pins); // exact, untruncated
    // Another row's control switches the one disclosure; pressing again closes it.
    const other = document.querySelector(`[data-scenario-inspect="${id(50)}"]`) as HTMLButtonElement;
    fireEvent.click(other);
    expect(button).toHaveAttribute("aria-expanded", "false");
    expect(Array.from(region.querySelectorAll("code"), (c) => c.textContent)).toEqual([id(21), id(22)]);
    fireEvent.click(other);
    expect(region.hidden).toBe(true);
    expect(MINI_CSS).toContain(".mini-scenarios-pinned { max-height: 96px; overflow-y: auto;");
  });

  it("scenario_v69_panels_and_planted_rejection", async () => {
    const refused: DecisionRead<ScenarioListBody> = {
      status: "refused",
      httpStatus: 422,
      code: "INVALID_WINDOW",
      message: "The window end is before its start.",
    };
    for (const answer of [ok(list([row()])), ok(list([])), refused]) {
      cleanup();
      renderAt(`/sites/${CODE}/financials/scenarios`, [answer]);
      await settledScreen();
      await waitFor(() => expect(document.querySelector("[data-scenarios-notice]")).not.toBeNull());
      expectV69Panels("scenarios");
      expectPlantedPanelRejected("scenarios");
    }
  });

  it("narrow_mock_panel_budgets", async () => {
    atWidth(390);
    try {
      // u9c: the captured populated read has two authored rows; both stay in the scroll box.
      const rows = [1, 2].map((n) => row({ id: id(60 + n), revision_id: id(70 + n), code: `SCN-00000${n}` }));
      renderAt(`/sites/${CODE}/financials/scenarios`, [ok(list(rows))]);
      await settledScreen();
      await waitFor(() => expect(cells()).toHaveLength(2));
      // The grid scrolls inside its panel: the table sits in the shared scroll box under the scenarios wrapper.
      const scroll = document.querySelector(".mini-scenarios-table .data-table__scroll");
      expect(scroll?.querySelector("table")).not.toBeNull();
      expect(scroll?.closest(".panel")?.querySelector("h2")?.textContent).toBe("Financial scenarios");
      // u9c: exactly 144 px at desktop (before the narrow block) and 188 px at <=600 px (inside it).
      const narrow = MINI_CSS.indexOf("@media (max-width: 600px)");
      const desktopRule = ".mini-scenarios-table .data-table__scroll { max-height: 144px; overflow: auto; }";
      const narrowRule = "@media (max-width: 600px) { .mini-scenarios-table .data-table__scroll { max-height: 188px; overflow: auto; }";
      expect(MINI_CSS).toContain(desktopRule);
      expect(MINI_CSS.indexOf(desktopRule)).toBeLessThan(narrow);
      expect(MINI_CSS).toContain(narrowRule);
      expect(MINI_CSS).not.toContain("calc(36px + 3 * 72px)");
      expect(MINI_CSS.match(/\.mini-scenarios-table \.data-table__scroll \{ max-height: [^;]+;/g)).toEqual([
        ".mini-scenarios-table .data-table__scroll { max-height: 144px;",
        ".mini-scenarios-table .data-table__scroll { max-height: 188px;",
      ]);
      // Sticky header at every width; 720 px grid and sticky 144 px Scenario column at 390.
      expect(MINI_CSS).toContain(".mini-scenarios-table thead th { position: sticky; top: 0;");
      expect(MINI_CSS.indexOf("thead th { position: sticky")).toBeLessThan(narrow);
      expect(MINI_CSS).toContain("padding: 20px 20px;");
      expect(MINI_CSS).toContain(".mini-scenarios-table .data-table { min-width: 720px; }");
      expect(MINI_CSS).toContain(".mini-scenarios-table col:first-child { width: 144px !important; }");
      expect(MINI_CSS).toContain(".mini-scenarios-table td:first-child { position: sticky; left: 0;");
      // Two rows, the count and the exact-pin disclosure (closed, outside the table) all remain.
      expect(document.querySelectorAll("[data-scenarios-table] tbody th[scope='row']")).toHaveLength(2);
      expect(document.querySelector("[data-scenarios-count]")?.textContent).toBe("2 of 2");
      expect(document.querySelectorAll("[data-scenario-pinned-count]")).toHaveLength(2);
      expect(document.querySelectorAll("button[data-scenario-inspect]")).toHaveLength(2);
      const disclosure = document.getElementById("mini-scenarios-pinned");
      expect(disclosure?.hidden).toBe(true);
      expect(disclosure?.closest("table")).toBeNull();
    } finally {
      atWidth(1024);
    }
  });

  it("exact_routes_no_dead_cta", async () => {
    renderAt(`/sites/${CODE}/financials/scenarios`, [ok(list([row()]))]);
    await settledScreen();
    await waitFor(() => expect(cells()).toHaveLength(1));
    expect(location()).toMatch(new RegExp(`^/sites/${CODE}/financials/scenarios([?]|$)`));
    const panel = panelTitled("Financial scenarios");
    noDeadCta(panel);
    // A row with url:null has no Scenario route: plain text, no control.
    const plain = Array.from(panel.querySelectorAll("tbody th *")).find((el) => el.textContent === "Scenario detail unavailable");
    noControl(plain ?? null);
  });

  it("scenario_site_type_tabs_and_no_cold_ev_promotion", async () => {
    // Mini: Overview, Assumptions, live Scenarios (selected); subtitle `Financials · scenarios`.
    const mini = renderAt(`/sites/${CODE}/financials/scenarios`, [ok(list([]))]);
    await settledScreen();
    await screen.findByText("No scenario defined yet");
    expect(subtabs()).toEqual([
      ["Overview", null],
      ["Assumptions", null],
      ["Scenarios", "page"],
    ]);
    expect(document.querySelector('[data-financials-section="scenarios"]')).toHaveAttribute(
      "href",
      `/sites/${CODE}/financials/scenarios`,
    );
    expect(document.querySelector("[data-tab-unavailable]")).toBeNull();
    expect(main().textContent).toContain("Financials · scenarios");
    expect(main().textContent).not.toContain("(placeholder)");
    expect(mini.getScenarios).toHaveBeenCalledTimes(1);
    cleanup();

    // Cold: the one unavailable Scenarios occurrence; no scenario read.
    render(
      <MemoryRouter>
        <FinancialsSections siteId="COLD-1" view="overview" />
      </MemoryRouter>,
    );
    expect(subtabs()).toEqual([
      ["Overview", "page"],
      ["Assumptions", null],
      ["Scenarios · Not available yet", null],
    ]);
    expect(document.querySelector('[data-financials-section="scenarios"]')).toBeNull();
    cleanup();
    for (const siteType of ["COLDCHAIN", "EV_CHARGING"]) {
      const other = renderAt(`/sites/OTHER-1/financials/scenarios`, [ok(list([]))], siteType, "OTHER-1");
      await settledScreen();
      await screen.findByText("Scenarios are read for mini-grid sites only.");
      expect(subtabs().map(([label]) => label)).toEqual(["Overview", "Assumptions", "Scenarios · Not available yet"]);
      expect(document.querySelector('[data-financials-section="scenarios"]')).toBeNull();
      expect(other.getScenarios).not.toHaveBeenCalled();
      expect(main().textContent).not.toContain("No scenario defined yet");
      cleanup();
    }
  });
});

/*
 * W4-03 unit 6b ("Unit-5..12 rulings (u5)" 6b; "Unit-6 rulings (u6)" 1-6): the canonical mini Finding row is
 * `Overview | Analysis (unavailable) | Evidence | Alternatives | Recommendation | History`; one W1 Finding read
 * resolves the exact revision before any Alternatives href or GET; the global breadcrumb is
 * `Findings › Finding code unavailable › {section} · site: {Site}`. Cold/EV child addresses are a section gap.
 */
describe("W4-03 unit 6b: canonical mini Alternatives", () => {
  const F = "49281b7c-96ac-456d-ab6b-040bb0760444";
  const REV = id(31);
  const LATEST = id(32);
  const TITLE = "Generator support merits review";

  function w1(siteCode: string, revisionId: string, findingId = F): FindingReadResult<FindingDetailBody> {
    return {
      status: "loaded",
      value: {
        site_code: siteCode,
        finding: { id: findingId, finding_key: "mini:dispatch:key" },
        selection: { revision_id: revisionId, latest_revision_id: revisionId },
        revision: { title: TITLE },
      } as unknown as FindingDetailBody,
    };
  }

  function findingsClient(answer: (revisionId: string | null) => FindingReadResult<FindingDetailBody>) {
    const asked: (string | null)[] = [];
    const client: FindingClient & { asked: (string | null)[] } = {
      asked,
      getFinding: async (_site, _id, revisionId) => {
        asked.push(revisionId);
        return answer(revisionId);
      },
      getFindingWindow: async () => ({ status: "not_found", message: null }),
      getFindingEvidence: async () => ({ status: "not_found", message: null }),
      getFindingHistory: async () => ({ status: "not_found", message: null }),
    } as FindingClient & { asked: (string | null)[] };
    return client;
  }

  function alternative(over: Partial<AlternativeRow> = {}): AlternativeRow {
    return {
      id: id(40),
      revision_id: id(41),
      finding_revision_id: REV,
      explanation: "Authored stop-threshold explanation",
      evidence_summary: "Authored evidence summary",
      cited_accepted_evidence_ids: [id(50)],
      missing_evidence_reason: null,
      disposition: "PLAUSIBLE",
      reason: "Authored reason",
      review_state: "CURRENT",
      ...over,
    };
  }

  function alternatives(rows: AlternativeRow[], state = "CURRENT"): DecisionRead<AlternativeListBody> {
    return {
      status: "loaded",
      value: {
        schema_version: "mini-alternatives-1",
        window: { from: null, to: null, known_at: KNOWN },
        status: "UNKNOWN",
        currentness: { state, job_state: "NONE" },
        total_count: rows.length,
        rows,
        next_cursor: null,
        selection_token: "sha256:" + "b".repeat(64),
      },
    };
  }

  function frameAt(
    path: string,
    findings: FindingClient,
    answer:
      | DecisionRead<AlternativeListBody>
      | ((page: AlternativesPage | undefined) => DecisionRead<AlternativeListBody>) = alternatives([]),
    siteType = "MINIGRID",
    code = CODE,
  ) {
    const decisions: MiniDecisionsClient = {
      getScenarios: vi.fn(() => Promise.resolve({ status: "unavailable" as const, message: null })),
      getAlternatives: vi.fn((_c: string, _f: string, _r: string, page?: AlternativesPage) =>
        Promise.resolve(typeof answer === "function" ? answer(page) : answer),
      ),
      getOpportunity: vi.fn(() => Promise.resolve({ status: "unavailable" as const, message: null })),
      listOpportunities: vi.fn(() => Promise.resolve({ status: "unavailable" as const, message: null })),
      getWorkContexts: vi.fn(() => Promise.resolve({ status: "unavailable" as const, message: null })),
    };
    const detail: SiteDetailClient = { getSite: () => Promise.resolve({ status: "loaded", site: site(code, siteType) }) };
    render(
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          {["/sites/:siteId/findings/:findingId", "/sites/:siteId/findings/:findingId/:findingView"].map((p) => (
            <Route
              key={p}
              path={p}
              element={
                <>
                  <SiteFindingFrame detail={detail} sitesPath="/sites" findings={findings} miniDecisions={decisions} />
                  <Where />
                  <Go />
                </>
              }
            />
          ))}
        </Routes>
      </MemoryRouter>,
    );
    return decisions;
  }

  const sectionRow = () =>
    Array.from(document.querySelectorAll('nav[aria-label="Finding sections"] li')).map((li) => li.textContent);
  const crumbs = () => document.querySelector("[data-mini-finding-crumbs]") as HTMLElement;
  const tableCells = () =>
    Array.from(document.querySelectorAll("[data-alternatives-table] tbody tr")).map((tr) =>
      Array.from(tr.querySelectorAll("td")).map((c) => c.textContent),
    );

  it("alternative_cells_and_revision_state", async () => {
    const findings = findingsClient(() => w1(CODE, REV));
    const decisions = frameAt(
      `/sites/${CODE}/findings/${F}/alternatives?revision_id=${REV}`,
      findings,
      alternatives([
        alternative(),
        alternative({
          id: id(42),
          revision_id: id(43),
          explanation: "Authored uncertainty explanation",
          evidence_summary: "No record",
          cited_accepted_evidence_ids: [],
          disposition: "RULED_OUT",
          review_state: "NEEDS_REVIEW",
        }),
      ]),
    );
    await settledScreen();
    await screen.findByText("Authored stop-threshold explanation");
    expect(decisions.getAlternatives).toHaveBeenCalledWith(CODE, F, REV, undefined);
    expect(screen.getByRole("heading", { name: "Alternatives to investigate" })).toBeInTheDocument();
    expect(Array.from(document.querySelectorAll("[data-alternatives-table] thead th")).map((th) => th.textContent)).toEqual([
      "Explanation",
      "Evidence",
      "Disposition",
    ]);
    expect(tableCells()).toEqual([
      ["Authored stop-threshold explanation", `Authored evidence summary${id(50)}`, "Plausible policy explanation"],
      [
        "Authored uncertainty explanation",
        "No recordNo accepted record supports or excludes this explanation.",
        "Needs review for this revision",
      ],
    ]);
    // The stored disposition stays in the data under the NEEDS_REVIEW words.
    expect(document.querySelector(`[data-alternative-row="${id(42)}"]`)).toHaveAttribute("data-disposition", "RULED_OUT");
    expect(document.querySelector(`[data-alternative-cited="${id(50)}"]`)).toHaveAttribute(
      "href",
      `/sites/${CODE}/evidence?view=analysis&record=${id(50)}`,
    );
    expect(main().textContent).toContain(
      "Candidate runtime is not proof that stopping the generator would have preserved service.",
    );
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(TITLE);
    cleanup();

    // Empty: the exact empty copy, the notice still shown; a historical read says so.
    frameAt(`/sites/${CODE}/findings/${F}/alternatives?revision_id=${REV}`, findingsClient(() => w1(CODE, REV)), alternatives([], "HISTORICAL"));
    await settledScreen();
    await screen.findByText("No alternatives recorded for this Finding revision.");
    expect(document.querySelector("[data-alternatives-historical]")).toHaveTextContent("Historical basis");
    expect(document.querySelector("[data-alternatives-notice]")).not.toBeNull();
    cleanup();

    // An absent revision_id: resolved by the W1 read, then the address is replaced; the GET uses the resolved revision.
    const unpinned = findingsClient((rev) => w1(CODE, rev ?? LATEST));
    const later = frameAt(`/sites/${CODE}/findings/${F}/alternatives`, unpinned);
    await settledScreen();
    await screen.findByText("No alternatives recorded for this Finding revision.");
    expect(unpinned.asked[0]).toBeNull();
    expect(location()).toBe(`/sites/${CODE}/findings/${F}/alternatives?revision_id=${LATEST}`);
    expect(later.getAlternatives).toHaveBeenCalledTimes(1);
    expect(later.getAlternatives).toHaveBeenCalledWith(CODE, F, LATEST, undefined);
    cleanup();

    // A refused W1 read: the noninteractive gap, no Alternatives GET, no Alternatives link.
    const refused = frameAt(
      `/sites/${CODE}/findings/${F}/alternatives`,
      findingsClient(() => ({ status: "forbidden", message: null })),
    );
    await settledScreen();
    await screen.findAllByText("Alternatives for this Finding unavailable");
    expect(refused.getAlternatives).not.toHaveBeenCalled();
    expect(document.querySelector('a[href*="/alternatives"]')).toBeNull();
    noControl(document.querySelector('[data-finding-section-gap="alternatives"]'));
    expect(document.querySelector("[data-finding-code-gap]")).toBeNull();
    expect(location()).toBe(`/sites/${CODE}/findings/${F}/alternatives`);
  });

  it("canonical_mini_tabs_breadcrumb_and_analytic_cta", async () => {
    const findings = findingsClient(() => w1(CODE, REV));
    frameAt(`/sites/${CODE}/findings/${F}/alternatives?revision_id=${REV}`, findings);
    await settledScreen();
    await screen.findByText("No alternatives recorded for this Finding revision.");
    expect(sectionRow()).toEqual([
      "Overview",
      "Analysis · Not available yet",
      "Evidence",
      "Alternatives",
      "Recommendation",
      "History",
    ]);
    const q = `?revision_id=${REV}`;
    expect(document.querySelector('[data-finding-section="finding"]')).toHaveAttribute("href", `/sites/${CODE}/findings/${F}${q}`);
    expect(document.querySelector('[data-finding-section="alternatives"]')).toHaveAttribute(
      "href",
      `/sites/${CODE}/findings/${F}/alternatives${q}`,
    );
    expect(document.querySelector('[data-finding-section="alternatives"]')).toHaveAttribute("aria-current", "page");
    for (const view of ["evidence", "recommendation", "history"]) {
      expect(document.querySelector(`[data-finding-section="${view}"]`)).toHaveAttribute(
        "href",
        `/sites/${CODE}/findings/${F}/${view}${q}`,
      );
    }
    noControl(document.querySelector('[data-tab-unavailable="Analysis"]'));
    expect(document.querySelector("[data-analysis-helper]")).toHaveTextContent(
      /^Analysis unavailable for this authored alternative; use the Finding overview and evidence\.$/,
    );
    noControl(document.querySelector("[data-analysis-helper]"));
    // Global breadcrumb: Findings › Finding code unavailable › Alternatives · site: {Site}.
    expect(crumbs().textContent).toBe("FindingsFinding code unavailableAlternatives· site: MINIGRID site");
    expect(crumbs().querySelector('a[href="/findings"]')).toHaveTextContent("Findings");
    expect(crumbs().querySelector("[data-mini-finding-site] a")).toHaveAttribute("href", `/sites/${CODE}`);
    noControl(crumbs().querySelector("[data-finding-code-gap]"));
    expect(crumbs().textContent).not.toMatch(/F-104|mini:dispatch:key/);
    expect(crumbs().textContent).not.toContain(F);
    // H3 (final review; ledger l.186): the v69 `Open site` header action resolves the authorized Site Overview.
    const openSite = document.querySelector(".page-header__actions [data-alternatives-open-site]");
    expect(openSite).toHaveTextContent(/^Open site$/);
    expect(openSite).toHaveAttribute("href", `/sites/${CODE}`);
    cleanup();

    // Another mini child: the section helper; the sibling tabs are pinned to the W1 read's resolved revision.
    frameAt(`/sites/${CODE}/findings/${F}/history`, findingsClient(() => w1(CODE, LATEST)));
    await settledScreen();
    await waitFor(() =>
      expect(document.querySelector('[data-finding-section="alternatives"]')).toHaveAttribute(
        "href",
        `/sites/${CODE}/findings/${F}/alternatives?revision_id=${LATEST}`,
      ),
    );
    expect(document.querySelector('[data-finding-section="evidence"]')).toHaveAttribute(
      "href",
      `/sites/${CODE}/findings/${F}/evidence?revision_id=${LATEST}`,
    );
    expect(document.querySelector("[data-analysis-helper]")).toHaveTextContent(
      /^Analysis unavailable for this Finding section; use the Finding overview and evidence\.$/,
    );
    expect(crumbs().textContent).toBe("FindingsFinding code unavailableHistory· site: MINIGRID site");
    // H3 is the Alternatives action only; the W1 sibling sections keep their header unchanged.
    expect(document.querySelector("[data-alternatives-open-site]")).toBeNull();
    expect(document.querySelectorAll("[data-tab-unavailable]")).toHaveLength(1);
    cleanup();

    // The analytic CTA links only after a same-Site W1 read resolves this exact Finding; otherwise it is null.
    const probe = async (client: FindingClient | undefined, siteCode = CODE, findingId: string | null = F) => {
      let seen: string | null = "unset";
      function Probe() {
        seen = useResolvedAlternativesHref(client, siteCode, findingId, (fid, rev) =>
          siteFindingAlternativesHref(siteCode, fid, rev),
        );
        return <output data-probe>{seen ?? "none"}</output>;
      }
      render(<Probe />);
      await waitFor(() => expect(document.querySelector("[data-probe]")).not.toBeNull());
      await new Promise((resolve) => setTimeout(resolve, 0));
      const text = document.querySelector("[data-probe]")?.textContent;
      cleanup();
      return text;
    };
    expect(await probe(findingsClient(() => w1(CODE, REV)))).toBe(`/sites/${CODE}/findings/${F}/alternatives?revision_id=${REV}`);
    expect(await probe(findingsClient(() => w1("MG-OTHER", REV)))).toBe("none");
    expect(await probe(findingsClient(() => w1(CODE, REV, id(99))))).toBe("none");
    expect(await probe(findingsClient(() => ({ status: "unavailable", message: null })))).toBe("none");
    expect(await probe(undefined)).toBe("none");
    expect(await probe(findingsClient(() => w1(CODE, REV)), CODE, null)).toBe("none");
  });

  it("alternative_v69_panels_and_planted_rejection", async () => {
    const findings = findingsClient(() => w1(CODE, REV));
    const refused: DecisionRead<AlternativeListBody> = {
      status: "refused",
      httpStatus: 503,
      code: "DECISION_STORE_UNAVAILABLE",
      message: "The decision store is unavailable.",
    };
    for (const answer of [alternatives([alternative()]), alternatives([]), refused]) {
      cleanup();
      frameAt(`/sites/${CODE}/findings/${F}/alternatives?revision_id=${REV}`, findings, answer);
      await settledScreen();
      await waitFor(() => expect(screen.getByRole("heading", { level: 2, name: "Alternatives to investigate" })).toBeTruthy());
      expectV69Panels("alternatives");
      expectPlantedPanelRejected("alternatives");
    }
  });

  it("narrow_mock_panel_budgets", async () => {
    atWidth(390);
    try {
      const findings = findingsClient(() => w1(CODE, REV));
      frameAt(
        `/sites/${CODE}/findings/${F}/alternatives?revision_id=${REV}`,
        findings,
        alternatives([alternative(), alternative({ id: id(44), revision_id: id(45) })]),
      );
      await settledScreen();
      await waitFor(() => expect(tableCells()).toHaveLength(2));
      // All three columns are kept at 390 (no column dropped); the table scrolls inside its panel.
      expect(Array.from(document.querySelectorAll("[data-alternatives-table] thead th"), (th) => th.textContent)).toHaveLength(3);
      for (const r of tableCells()) expect(r).toHaveLength(3);
      const scroll = document.querySelector(".mini-alternatives-table .data-table__scroll");
      expect(scroll?.querySelector("table")).not.toBeNull();
      expect(scroll?.closest(".panel")?.querySelector("h2")?.textContent).toBe("Alternatives to investigate");
      expect(MINI_CSS).toContain(".mini-alternatives-table .data-table { table-layout: fixed; }");
    } finally {
      atWidth(1024);
    }
  });

  it("exact_routes_no_dead_cta", async () => {
    const findings = findingsClient(() => w1(CODE, REV));
    frameAt(`/sites/${CODE}/findings/${F}/alternatives?revision_id=${REV}`, findings, alternatives([alternative()]));
    await settledScreen();
    await waitFor(() => expect(tableCells()).toHaveLength(1));
    expect(location()).toBe(`/sites/${CODE}/findings/${F}/alternatives?revision_id=${REV}`);
    noDeadCta(panelTitled("Alternatives to investigate"));
    // Section links stay on this Site and carry the exact selected revision; none is a dead control.
    const sections = Array.from(document.querySelectorAll('nav[aria-label="Finding sections"] a'), (a) => a.getAttribute("href") ?? "");
    expect(sections.length).toBeGreaterThan(0);
    for (const href of sections) {
      expect(href).toMatch(new RegExp(`^/sites/${CODE}/`));
      expect(href).toContain(REV);
    }
  });

  it("cold_ev_alternatives_absent", async () => {
    for (const siteType of ["COLDCHAIN", "EV_CHARGING"]) {
      for (const view of ["alternatives", "evidence", "history"]) {
        const findings = findingsClient(() => w1("OTHER-1", REV));
        const decisions = frameAt(`/sites/OTHER-1/findings/${F}/${view}`, findings, alternatives([]), siteType, "OTHER-1");
        await settledScreen();
        await screen.findByText(/Finding section unavailable for this site\./);
        const link = screen.getByRole("link", { name: "Open Finding overview" });
        expect(link).toHaveAttribute("href", `/sites/OTHER-1/findings/${F}`);
        expect(decisions.getAlternatives).not.toHaveBeenCalled();
        expect(document.querySelector('nav[aria-label="Finding sections"]')).toBeNull();
        expect(document.querySelector("[data-tab-unavailable]")).toBeNull();
        expect(document.querySelector('a[href*="/alternatives"]')).toBeNull();
        expect(main().textContent).not.toContain("Alternatives to investigate");
        cleanup();
      }
    }
  });
  /* ---------- u6b builder rulings ---------- */

  const rowHrefs = () =>
    Array.from(document.querySelectorAll('nav[aria-label="Finding sections"] a')).map((a) => a.getAttribute("href") ?? "");

  it("u6b_helper_after_row_and_sibling_predicate", async () => {
    // Root: no helper (the root body's own W1 read is out of scope here, so the selection refuses).
    frameAt(`/sites/${CODE}/findings/${F}?revision_id=${REV}`, findingsClient(() => ({ status: "unavailable", message: null })));
    await waitFor(() => expect(document.querySelector("[data-finding-section-gap='finding']")).not.toBeNull());
    expect(document.querySelector("[data-analysis-helper]")).toBeNull();
    cleanup();

    // Child views: the helper is the section row's noninteractive next sibling, outside the navigation.
    for (const [view, text] of [
      ["alternatives", ANALYSIS_HELPER_ALTERNATIVES],
      ["evidence", ANALYSIS_HELPER_SECTION],
      ["history", ANALYSIS_HELPER_SECTION],
    ]) {
      frameAt(`/sites/${CODE}/findings/${F}/${view}?revision_id=${REV}`, findingsClient(() => w1(CODE, REV)));
      await settledScreen();
      const helper = await waitFor(() => {
        const h = document.querySelector("[data-analysis-helper]");
        expect(h).not.toBeNull();
        return h!;
      });
      expect(helper.textContent).toBe(text);
      expect(helper.closest("nav")).toBeNull();
      expect(helper.previousElementSibling?.matches('nav[aria-label="Finding sections"]')).toBe(true);
      noControl(helper);
      expect(document.querySelectorAll("[data-analysis-helper]")).toHaveLength(1);
      // Loaded: Overview, every live sibling and the money link (6 links) carry the same W1-selected revision.
      expect(rowHrefs()).toHaveLength(6);
      for (const href of rowHrefs()) expect(href).toContain(`revision_id=${REV}`);
      expect(document.querySelector("[data-finding-financials-link] a")?.getAttribute("href")).toContain(REV);
      cleanup();
    }

    // A stale supplied UUID (W1 selects another revision), a refusal, and a read still loading: no sibling, Overview
    // or money href carries the raw token, and no W4-03 GET is made.
    const RAW = id(77);
    const loading: FindingClient = { ...findingsClient(() => w1(CODE, RAW)), getFinding: () => new Promise(() => undefined) };
    for (const findings of [
      findingsClient(() => w1(CODE, LATEST)),
      findingsClient(() => ({ status: "unavailable", message: null })),
      loading,
    ]) {
      const decisions = frameAt(`/sites/${CODE}/findings/${F}/evidence?revision_id=${RAW}`, findings);
      await waitFor(() => expect(document.querySelector("[data-finding-section-gap='evidence']")).not.toBeNull());
      await new Promise((resolve) => setTimeout(resolve, 0));
      expect(rowHrefs()).toEqual([]);
      for (const gap of ["finding", "evidence", "alternatives", "recommendation", "history"]) {
        noControl(document.querySelector(`[data-finding-section-gap='${gap}']`));
      }
      expect(document.querySelector("[data-finding-financials-link]")).toBeNull();
      expect(document.querySelectorAll(`nav a[href*="${RAW}"]`)).toHaveLength(0);
      expect(decisions.getAlternatives).not.toHaveBeenCalled();
      cleanup();
    }
  });

  it("u6b_same_site_identity_and_replace_reread", async () => {
    const F2 = "59281b7c-96ac-456d-ab6b-040bb0760555";
    const asked: string[] = [];
    const findings = {
      ...findingsClient(() => w1(CODE, REV)),
      getFinding: async (_siteCode: string, findingId: string, revisionId: string | null) => {
        asked.push(`${findingId}|${revisionId}`);
        return w1(CODE, revisionId ?? REV, findingId);
      },
    } as FindingClient;
    // One GET across the absent-revision replace.
    const decisions = frameAt(`/sites/${CODE}/findings/${F}/alternatives`, findings);
    await settledScreen();
    await waitFor(() => expect(location()).toBe(`/sites/${CODE}/findings/${F}/alternatives?revision_id=${REV}`));
    await waitFor(() => expect(decisions.getAlternatives).toHaveBeenCalledTimes(1));
    expect(asked).toEqual([`${F}|null`]);
    // A changed revision, then a changed Finding, each issue a new W1 read.
    act(() => goTo!(`/sites/${CODE}/findings/${F}/alternatives?revision_id=${LATEST}`));
    await waitFor(() => expect(asked).toHaveLength(2));
    act(() => goTo!(`/sites/${CODE}/findings/${F2}/alternatives?revision_id=${LATEST}`));
    await waitFor(() => expect(asked).toHaveLength(3));
    expect(asked.slice(1)).toEqual([`${F}|${LATEST}`, `${F2}|${LATEST}`]);
    cleanup();

    // Same-Site exact: wrong Site code or wrong Finding refuse; a UUID case variation is the same Finding.
    for (const [answer, live] of [
      [w1("MG-OTHER", REV), false],
      [w1(CODE, REV, id(99)), false],
      [w1(CODE, REV, F.toUpperCase()), true],
    ] as [FindingReadResult<FindingDetailBody>, boolean][]) {
      const d = frameAt(`/sites/${CODE}/findings/${F}/alternatives?revision_id=${REV}`, findingsClient(() => answer));
      await settledScreen();
      await new Promise((resolve) => setTimeout(resolve, 0));
      if (live) {
        await waitFor(() => expect(d.getAlternatives).toHaveBeenCalledTimes(1));
        expect(document.querySelector("[data-finding-section='alternatives']")).not.toBeNull();
      } else {
        expect(d.getAlternatives).not.toHaveBeenCalled();
        expect(document.querySelector("[data-finding-section='alternatives']")).toBeNull();
        expect(document.querySelector("[data-finding-section-gap='alternatives']")?.textContent).toBe(
          "Alternatives for this Finding unavailable",
        );
      }
      cleanup();
    }
  });

  it("u6b_alternatives_refusal_copy_reason_and_paging", async () => {
    const path = `/sites/${CODE}/findings/${F}/alternatives?revision_id=${REV}`;
    // Refusals by code: no authored rows and no positive state.
    for (const [read, copy] of [
      [{ status: "refused", httpStatus: 401, code: "UNAUTHENTICATED", message: null }, "Sign in to see this page."],
      [{ status: "refused", httpStatus: 403, code: "SITE_ACCESS_DENIED", message: null }, "You do not have access to this site."],
      [{ status: "refused", httpStatus: 404, code: "DECISION_NOT_FOUND", message: null }, "This decision was not found at this site."],
      [{ status: "refused", httpStatus: 409, code: "DECISION_BASIS_CHANGED", message: null }, "The evidence changed. Reload this page."],
      [{ status: "refused", httpStatus: 503, code: "DECISION_STORE_UNAVAILABLE", message: null }, "Decisions are unavailable right now. Try again."],
      [{ status: "unavailable", message: null }, "Decisions are unavailable right now. Try again."],
    ] as [DecisionRead<AlternativeListBody>, string][]) {
      frameAt(path, findingsClient(() => w1(CODE, REV)), read);
      await settledScreen();
      await waitFor(() => expect(document.querySelector("[data-alternatives-refused]")?.textContent).toBe(copy));
      // The panel-level `Alternatives unavailable` label belongs to the 503 (and transport) state only.
      const label = document.querySelector("[data-alternatives-unavailable]")?.textContent ?? null;
      expect(label).toBe(read.status === "unavailable" || (read.status === "refused" && read.httpStatus === 503) ? "Alternatives unavailable" : null);
      expect(document.querySelector("[data-alternatives-table]")).toBeNull();
      expect(document.querySelector("[data-alternatives-empty]")).toBeNull();
      cleanup();
    }

    // Authored missing-evidence context shows with and without citations; an empty citation set keeps its copy.
    frameAt(
      path,
      findingsClient(() => w1(CODE, REV)),
      alternatives([
        alternative({ id: id(60), missing_evidence_reason: "Logger offline for part of the window" }),
        alternative({ id: id(61), cited_accepted_evidence_ids: [], missing_evidence_reason: "No fuel record was kept" }),
        alternative({ id: id(62), cited_accepted_evidence_ids: [] }),
      ]),
    );
    await settledScreen();
    await waitFor(() => expect(document.querySelectorAll("[data-alternative-row]")).toHaveLength(3));
    const rows = Array.from(document.querySelectorAll("[data-alternative-row]"));
    expect(rows[0].querySelector("[data-alternative-missing-reason]")?.textContent).toBe("Logger offline for part of the window");
    expect(rows[0].querySelector("[data-alternative-cited]")?.getAttribute("href")).toContain(id(50));
    expect(rows[1].querySelector("[data-alternative-missing-reason]")?.textContent).toBe("No fuel record was kept");
    expect(rows[1].querySelector("[data-alternative-no-evidence]")).not.toBeNull();
    expect(rows[2].querySelector("[data-alternative-missing-reason]")).toBeNull();
    expect(rows[2].querySelector("[data-alternative-cited]")).toBeNull();
    cleanup();

    // Four keys over two pages: Next sends the returned cutoff and cursor; no duplicate or skipped row.
    const page = (ids: number[], next: string | null): DecisionRead<AlternativeListBody> => {
      const read = alternatives(ids.map((n) => alternative({ id: id(n), explanation: `Explanation ${n}` })));
      if (read.status === "loaded") read.value = { ...read.value, total_count: 4, next_cursor: next };
      return read;
    };
    const seen: (AlternativesPage | undefined)[] = [];
    const paged = frameAt(path, findingsClient(() => w1(CODE, REV)), (p) => {
      seen.push(p);
      return p === undefined ? page([71, 72], "cursor-1") : page([73, 74], null);
    });
    await settledScreen();
    await waitFor(() => expect(document.querySelectorAll("[data-alternative-row]")).toHaveLength(2));
    const first = tableCells().map((r) => r[0]);
    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    await waitFor(() => expect(tableCells().map((r) => r[0])).toEqual(["Explanation 73", "Explanation 74"]));
    expect(first).toEqual(["Explanation 71", "Explanation 72"]);
    expect(seen).toEqual([undefined, { known_at: KNOWN, cursor: "cursor-1" }]);
    expect(paged.getAlternatives).toHaveBeenLastCalledWith(CODE, F, REV, { known_at: KNOWN, cursor: "cursor-1" });
    expect(screen.queryByRole("button", { name: "Next" })).toBeNull();
    cleanup();

    // A cursor whose basis changed is the 409 copy, with no rows kept as current.
    frameAt(path, findingsClient(() => w1(CODE, REV)), (p) =>
      p === undefined
        ? page([71, 72], "cursor-1")
        : { status: "refused", httpStatus: 409, code: "DECISION_BASIS_CHANGED", message: null },
    );
    await settledScreen();
    await waitFor(() => expect(document.querySelectorAll("[data-alternative-row]")).toHaveLength(2));
    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    await waitFor(() =>
      expect(document.querySelector("[data-alternatives-refused]")?.textContent).toBe("The evidence changed. Reload this page."),
    );
    expect(document.querySelector("[data-alternatives-table]")).toBeNull();
  });

  it("u6b_cold_ev_recommendation_stays_in_domain_row", async () => {
    const pending = new Proxy({}, { get: () => () => new Promise(() => undefined) });
    for (const siteType of ["COLDCHAIN", "EV_CHARGING"]) {
      // `/recommendation` with the domain client: the domain frame's Overview | Recommendation row, no section gap.
      const findings = findingsClient(() => w1("OTHER-1", REV));
      const decisions: MiniDecisionsClient = {
        getScenarios: vi.fn(() => Promise.resolve({ status: "unavailable" as const, message: null })),
        getAlternatives: vi.fn(() => Promise.resolve({ status: "unavailable" as const, message: null })),
        getOpportunity: vi.fn(() => Promise.resolve({ status: "unavailable" as const, message: null })),
        listOpportunities: vi.fn(() => Promise.resolve({ status: "unavailable" as const, message: null })),
        getWorkContexts: vi.fn(() => Promise.resolve({ status: "unavailable" as const, message: null })),
      };
      const detail: SiteDetailClient = { getSite: () => Promise.resolve({ status: "loaded", site: site("OTHER-1", siteType) }) };
      for (const withClient of [true, false]) {
        for (const tail of ["", "/recommendation"]) {
          render(
            <MemoryRouter initialEntries={[`/sites/OTHER-1/findings/${F}${tail}?from=2026-10-01T00:00:00Z&to=2026-10-02T00:00:00Z`]}>
              <Routes>
                {["/sites/:siteId/findings/:findingId", "/sites/:siteId/findings/:findingId/:findingView"].map((p) => (
                  <Route
                    key={p}
                    path={p}
                    element={
                      <SiteFindingFrame
                        detail={detail}
                        sitesPath="/sites"
                        findings={findings}
                        miniDecisions={decisions}
                        coldAssessment={withClient && siteType === "COLDCHAIN" ? (pending as never) : undefined}
                        evAssessment={withClient && siteType === "EV_CHARGING" ? (pending as never) : undefined}
                      />
                    }
                  />
                ))}
              </Routes>
            </MemoryRouter>,
          );
          await waitFor(() => expect(document.querySelector("main h1")).not.toBeNull());
          await new Promise((resolve) => setTimeout(resolve, 0));
          expect(main().textContent).not.toContain("Finding section unavailable for this site.");
          if (withClient) {
            const row = Array.from(document.querySelectorAll('nav[aria-label="Finding sections"] li'));
            expect(row).toHaveLength(2);
            expect(row[0].textContent).toBe("Overview");
            expect(row[1].textContent).toContain("Recommendation");
            expect(document.querySelectorAll('nav[aria-label="Finding sections"] [data-tab-unavailable]')).toHaveLength(1);
          } else {
            expect(document.querySelector("[data-finding-domain-unavailable]")?.textContent).toBe(
              "This site's Finding view is unavailable.",
            );
          }
          expect(findings.asked).toEqual([]);
          expect(decisions.getAlternatives).not.toHaveBeenCalled();
          cleanup();
        }
      }
      // A direct unsupported child keeps the exact gap and its window query on the Overview link.
      render(
        <MemoryRouter initialEntries={[`/sites/OTHER-1/findings/${F}/history?from=2026-10-01T00:00:00Z&to=2026-10-02T00:00:00Z`]}>
          <Routes>
            <Route
              path="/sites/:siteId/findings/:findingId/:findingView"
              element={<SiteFindingFrame detail={detail} sitesPath="/sites" findings={findings} miniDecisions={decisions} />}
            />
          </Routes>
        </MemoryRouter>,
      );
      await screen.findByText(/Finding section unavailable for this site\./);
      expect(screen.getByRole("link", { name: "Open Finding overview" }).getAttribute("href")).toBe(
        `/sites/OTHER-1/findings/${F}?from=2026-10-01T00%3A00%3A00Z&to=2026-10-02T00%3A00%3A00Z`,
      );
      cleanup();
    }
  });
});

describe("W4-03 unit 7: typed Opportunity detail and the exact renewable CTA", () => {
  const OPP = id(700);
  const SITE_UUID = "11111111-2222-4333-8444-555555555555";
  const EV1 = id(901);
  const EV2 = id(902);
  // The stored study 6-10 Oct 2026, Nairobi midnights (closure 1 Q12-Q16 example).
  const S_FROM = "2026-10-05T21:00:00.000000Z";
  const S_TO = "2026-10-10T21:00:00.000000Z";
  const S_KNOWN = "2026-10-11T06:00:00.000000Z";
  const MOCK_LITERALS = ["F-109", "Medium", "18–20", "3 / 5", "10 kW × 1 h", "$0.25", "3 kW", "Grain-mill"];

  const dayRow = (day: string, decision: string | null, low: string | null, high: string | null, ids: string[]) => ({
    local_day: day,
    decision,
    opportunity_kwh: low === null || high === null ? null : { low, high },
    constraints: [],
    evidence_ids: ids,
    selection_seq: decision === null ? null : 1,
    mini_revision_id: decision === null ? null : id(800),
  });

  function body(over: Partial<OpportunityDetailBody> = {}, opp: Partial<OpportunityObject> = {}): OpportunityDetailBody {
    return {
      schema_version: "mini-opportunity-detail-1",
      opportunity: {
        id: OPP,
        code: "OPP-000001",
        revision_id: id(710),
        revision_no: 1,
        first_day: "2026-10-06",
        last_day: "2026-10-10",
        model_version: "mini-opportunity/1",
        study_days: 5,
        eligible_days: 2,
        assessed_days: 5,
        headroom_kw: { low: "12", high: "15" },
        proposed_load_kw: "10",
        gross_sales_scenario: { amount: "2.5", currency: "USD", basis: "SCENARIO" },
        demand_state: "UNVERIFIED",
        collection_state: "UNVERIFIED",
        scenario_id: id(720),
        day_rows: [
          dayRow("2026-10-06", "ELIGIBLE", "18", "20", [EV2]),
          dayRow("2026-10-07", "EXCLUDED", null, null, []),
          dayRow("2026-10-08", "ELIGIBLE", "12", "15", [EV1, EV2]),
          dayRow("2026-10-09", "EXCLUDED", null, null, []),
          dayRow("2026-10-10", "EXCLUDED", null, null, []),
        ],
        ...opp,
      },
      status: "SUPPORTED",
      currentness: { state: "CURRENT", job_state: "SETTLED" },
      selected_source_provenance: { classification: "AUTHORED_DEMONSTRATION" },
      pending_source_provenance: null,
      limitations: [],
      history: [],
      scenario_links: [],
      links: {
        renewable: `/sites/${SITE_UUID}/performance/renewable?from=${S_FROM}&to=${S_TO}&known_at=${S_KNOWN}`,
        site_work: null,
        scenario: null,
      },
      ...over,
    };
  }

  function openAt(answer: DecisionRead<OpportunityDetailBody>, siteType = "MINIGRID", query = "") {
    const decisions: MiniDecisionsClient = {
      getScenarios: vi.fn(() => Promise.resolve({ status: "unavailable" as const, message: null })),
      getAlternatives: vi.fn(() => Promise.resolve({ status: "unavailable" as const, message: null })),
      getOpportunity: vi.fn(() => Promise.resolve(answer)),
      listOpportunities: vi.fn(() => Promise.resolve({ status: "unavailable" as const, message: null })),
      getWorkContexts: vi.fn(() => Promise.resolve({ status: "unavailable" as const, message: null })),
    };
    const s = site(CODE, siteType);
    const detail: SiteDetailClient = { getSite: () => Promise.resolve({ status: "loaded", site: s }) };
    const directory: SiteDirectoryClient = { listSites: () => Promise.resolve({ status: "loaded", sites: [s] }) };
    render(
      <MemoryRouter initialEntries={[`/sites/${CODE}/opportunities/${OPP}${query}`]}>
        <App flags={featureFlagsWith(false)} siteDirectory={directory} siteDetail={detail} siteAnalytics={EMPTY_ANALYTICS_CLIENT} miniDecisions={decisions} />
        <Where />
      </MemoryRouter>,
    );
    return decisions;
  }

  const loaded = (b: OpportunityDetailBody): DecisionRead<OpportunityDetailBody> => ({ status: "loaded", value: b });
  const chip = () => document.querySelector("[data-opportunity-chip]");
  const cards = () =>
    Array.from(document.querySelectorAll("[data-opportunity-cards] > li")).map((li) =>
      Array.from(li.children).map((c) => c.textContent),
    );
  const basis = () =>
    Array.from(document.querySelectorAll(".v69-key-values > div")).map((d) => [
      d.querySelector("dt")?.textContent,
      d.querySelector("dd")?.textContent,
    ]);
  const words = () =>
    Array.from(document.querySelectorAll("[data-opportunity-cards] > li"), (li) => li.classList.contains("v69-metric--word"));
  const claim = () => document.querySelector("[data-opportunity-claim]")?.textContent;
  const secondary = () => document.querySelector("[data-opportunity-secondary]")?.textContent;
  const noMock = () => {
    for (const literal of MOCK_LITERALS) expect(main().textContent).not.toContain(literal);
  };

  async function show(b: OpportunityDetailBody) {
    cleanup();
    openAt(loaded(b));
    await settledScreen();
    await waitFor(() => expect(document.querySelector("[data-opportunity-page]")).not.toBeNull());
  }

  it("opportunity_supported_limited_pending_and_null_money", async () => {
    // Supported, current, resolved selected class: the only green state (u5 ruling 1 positive gate).
    await show(body());
    expect(chip()?.getAttribute("data-opportunity-chip")).toBe("green");
    expect(chip()?.textContent).toBe("OPP-000001 · Opportunity");
    expect(document.querySelector("[data-opportunity-confidence]")?.textContent).toBe("Confidence: Not assessed");
    expect(secondary()).toBe("Recommendation · demand unverified");
    expect(cards()).toEqual([
      ["Usable headroom", "12–15 kW", "After the selected retained margin"],
      ["Eligible days", "2 / 5", "Separate five-day study"],
      ["Proposed load", "10 kW", "Linked scenario (name unavailable)"],
      ["Gross sales scenario", "$2.50", "Before costs; collections unverified"],
    ]);
    // PR-12.2: numeric and monetary values keep the large numeric value; no card is a word value here.
    expect(words()).toEqual([false, false, false, false]);
    expect(claim()).toBe("Renewable capacity appears available for a one-hour productive load in 2 adequately observed windows.");
    // H2 (final review): the claim is the shared v69 big-claim headline, not an unstyled paragraph.
    expect(document.querySelector("[data-opportunity-claim]")).toHaveClass("v69-big-claim");
    expect(main().textContent).toContain(
      "Electrical feasibility does not establish customer demand, collections or a realised financial benefit.",
    );
    expect(main().textContent).toContain(
      "Validate local demand, schedule any proposed load, and check critical service and storage guardrails before a trial.",
    );
    expect(basis()).toEqual([
      ["Technical quantity", "12–15 kW usable headroom"],
      ["Scenario energy", "Unavailable in this read"],
      ["Tariff", "Unavailable in this read"],
      ["Gross sales", "$2.50 · scenario"],
      ["Managed Action", "Not yet accepted"],
    ]);
    noMock();

    // A proposal above one eligible day's lower bound is not claimed to fit every counted hour.
    await show(body({}, { proposed_load_kw: "13" }));
    expect(claim()).toBe("Measured renewable headroom is available in 2 of 5 assessed windows; no added load has been validated.");

    // The u4b gated read: a stored SUPPORTED result read while W4-02 is pending or stale keeps its frozen values,
    // withholds money and never renders the positive chip or claim.
    for (const state of ["PENDING_RECOMPUTE", "STALE_SOURCE"]) {
      await show(
        body({ currentness: { state, job_state: state === "PENDING_RECOMPUTE" ? "PENDING" : "SETTLED" } }, { gross_sales_scenario: null }),
      );
      expect(chip()?.getAttribute("data-opportunity-chip")).toBe("amber");
      expect(secondary()).toBe("Decision pending · evidence limited");
      expect(cards()[0][1]).toBe("12–15 kW");
      expect(cards()[3][1]).toBe("Withheld pending evidence");
      expect(words()).toEqual([false, false, false, true]); // a withheld value is a state word, never zero
      expect(basis()[3]).toEqual(["Gross sales", "Withheld pending evidence"]);
      expect(claim()).toBe("The selected evidence does not establish a recurring productive-use opportunity.");
      expect(main().textContent).not.toContain("appears available");
    }

    // MIXED or UNKNOWN selected class: no green chip even when current and SUPPORTED.
    for (const classification of ["MIXED", "UNKNOWN"]) {
      await show(body({ selected_source_provenance: { classification } }));
      expect(chip()?.getAttribute("data-opportunity-chip")).not.toBe("green");
    }

    // Supported with zero eligible days: counts shown, no positive chip, no headroom.
    await show(body({}, { eligible_days: 0, headroom_kw: null, proposed_load_kw: null, scenario_id: null, gross_sales_scenario: null }));
    expect(chip()?.getAttribute("data-opportunity-chip")).toBe("gray");
    expect(cards()[1][1]).toBe("0 / 5");
    expect(cards()[0][1]).toBe("Unknown");

    // LIMITED: amber, Unknown headroom, the limited claim and the missing-evidence next decision.
    await show(body({ status: "LIMITED" }, { headroom_kw: null, eligible_days: 1 }));
    expect(chip()?.getAttribute("data-opportunity-chip")).toBe("amber");
    expect(cards()[0][1]).toBe("Unknown");
    expect(claim()).toBe("The selected evidence does not establish a recurring productive-use opportunity.");
    expect(main().textContent).toContain("Complete the missing renewable and service evidence before a load decision.");

    // UNKNOWN incomplete study without a scenario: every authored slot states its own gap; money is null.
    await show(
      body(
        { status: "UNKNOWN", currentness: { state: "UNKNOWN", job_state: "NONE" }, selected_source_provenance: null },
        { assessed_days: 3, eligible_days: 1, headroom_kw: null, proposed_load_kw: null, scenario_id: null, gross_sales_scenario: null },
      ),
    );
    expect(chip()?.getAttribute("data-opportunity-chip")).toBe("gray");
    expect(cards()).toEqual([
      ["Usable headroom", "Unknown", "After the selected retained margin"],
      ["Eligible days", "Not established", "Five-day study incomplete"],
      ["Proposed load", "No load proposed", "No scenario linked"],
      ["Gross sales scenario", "Not calculated", "Before costs; collections unverified"],
    ]);
    expect(words()).toEqual([true, true, true, true]);
    expect(basis()).toEqual([
      ["Technical quantity", "Unknown"],
      ["Scenario energy", "No load scenario"],
      ["Tariff", "No tariff declared"],
      ["Gross sales", "Not calculated"],
      ["Managed Action", "Not yet accepted"],
    ]);
    noMock();
  });

  it("u9b_detail_known_at_address_and_wire", async () => {
    // No query: current-time semantics, no cutoff sent; the Overview tab keeps the bare address.
    cleanup();
    let client = openAt(loaded(body()));
    await settledScreen();
    await waitFor(() => expect(document.querySelector("[data-opportunity-page]")).not.toBeNull());
    expect(client.getOpportunity).toHaveBeenCalledWith(CODE, OPP, []);
    expect(document.querySelector("[data-opportunity-tabs] a")?.getAttribute("href")).toBe(`/sites/${CODE}/opportunities/${OPP}`);

    // An explicit historical cutoff is parsed, sent and preserved; it never makes the read current.
    const k = "2026-10-14T09:30:00.123456Z";
    const historical = body({ currentness: { state: "HISTORICAL", job_state: "SETTLED" } });
    cleanup();
    client = openAt(loaded(historical), "MINIGRID", `?${new URLSearchParams({ known_at: k })}`);
    await settledScreen();
    await waitFor(() => expect(document.querySelector("[data-opportunity-page]")).not.toBeNull());
    expect(client.getOpportunity).toHaveBeenCalledTimes(1);
    expect(client.getOpportunity).toHaveBeenCalledWith(CODE, OPP, [k]);
    expect(document.querySelector("[data-opportunity-tabs] a")?.getAttribute("href")).toBe(
      `/sites/${CODE}/opportunities/${OPP}?${new URLSearchParams({ known_at: k })}`,
    );
    expect(chip()?.getAttribute("data-opportunity-chip")).toBe("blue");

    // A duplicate or refused cutoff reaches the server unchanged; its refusal shows, with no positive badge.
    for (const [query, code] of [
      [`?known_at=${encodeURIComponent(k)}&known_at=${encodeURIComponent(k)}`, "INVALID_KNOWN_AT"],
      ["?known_at=2099-01-01T00:00:00.000000Z", "INVALID_KNOWN_AT"],
      ["?known_at=yesterday", "INVALID_KNOWN_AT"],
    ] as const) {
      cleanup();
      client = openAt({ status: "refused", httpStatus: 422, code, message: "The cutoff is not valid." }, "MINIGRID", query);
      await settledScreen();
      await waitFor(() => expect(document.querySelector("[data-opportunity-refusal]")).not.toBeNull());
      expect(client.getOpportunity).toHaveBeenCalledWith(CODE, OPP, new URLSearchParams(query).getAll("known_at"));
      expect(document.querySelector("[data-opportunity-refusal]")?.getAttribute("data-opportunity-refusal")).toBe(code);
      expect(chip()).toBeNull();
      expect(document.querySelector("[data-opportunity-cards]")).toBeNull();
    }

    // The production client puts every given cutoff on the detail GET, and none when omitted.
    const fetchMock = vi.fn((_url: string) => Promise.resolve(new Response("{}", { status: 503 })));
    vi.stubGlobal("fetch", fetchMock);
    try {
      const real = createMiniDecisionsClient("/api/sites");
      await real.getOpportunity(CODE, OPP);
      await real.getOpportunity(CODE, OPP, k);
      await real.getOpportunity(CODE, OPP, [k, k]);
      expect(fetchMock.mock.calls.map((c) => c[0])).toEqual([
        `/api/sites/${CODE}/opportunities/${OPP}`,
        `/api/sites/${CODE}/opportunities/${OPP}?${new URLSearchParams({ known_at: k })}`,
        `/api/sites/${CODE}/opportunities/${OPP}?${new URLSearchParams([["known_at", k], ["known_at", k]])}`,
      ]);
    } finally {
      vi.unstubAllGlobals();
    }
  });

  it("opportunity_history_and_exact_renewable_cta", async () => {
    // Historical basis is blue, never green, and keeps the frozen values.
    await show(body({ currentness: { state: "HISTORICAL", job_state: "SETTLED" } }));
    expect(chip()?.getAttribute("data-opportunity-chip")).toBe("blue");
    expect(document.querySelector("[data-opportunity-currentness]")?.textContent).toBe("Historical basis");

    // Open renewable evaluation: the public Site code plus the stored study bounds and cutoff, never the UUID.
    await show(body());
    const expected = `/sites/${CODE}/performance/renewable?${new URLSearchParams({ from: S_FROM, to: S_TO, known_at: S_KNOWN })}`;
    const cta = screen.getByRole("link", { name: "Open renewable evaluation" });
    expect(cta.getAttribute("href")).toBe(expected);
    expect(main().innerHTML).not.toContain(SITE_UUID);

    // Header, description, Open site, one selected Overview tab and the disabled Findings root.
    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("Productive-use headroom at MINIGRID site");
    expect(main().textContent).toContain(
      "Five-day renewable headroom and an explicitly authored scenario, with evidence and demand limits.",
    );
    expect(screen.getByRole("link", { name: "Open site" }).getAttribute("href")).toBe(`/sites/${CODE}`);
    const tabs = Array.from(document.querySelectorAll("[data-opportunity-tabs] li"));
    expect(tabs.map((li) => li.textContent)).toEqual(["Overview"]);
    expect(tabs[0].querySelector("a")?.getAttribute("aria-current")).toBe("page");
    // u7 PR-9 (1): exactly `Findings › {OPP code} › Overview · site: {Site}`, the same DOM at 1440 and 390.
    for (const width of [1440, 390]) {
      Object.defineProperty(window, "innerWidth", { configurable: true, value: width });
      window.dispatchEvent(new Event("resize"));
      await show(body());
      const nav = document.querySelector("[data-opportunity-crumbs]") as HTMLElement;
      expect(Array.from(nav.querySelectorAll("li")).map((li) => li.textContent)).toEqual([
        "Global Findings unavailable; this opportunity is reached from Renewable evaluation.",
        "OPP-000001",
        "Overview",
      ]);
      expect(nav.querySelector("[data-opportunity-crumb-site]")?.textContent).toBe("· site: MINIGRID site");
      // Only the Site suffix links (authorized Site Overview); root, code and Overview are text.
      expect(Array.from(nav.querySelectorAll("a")).map((a) => [a.textContent, a.getAttribute("href")])).toEqual([
        ["MINIGRID site", `/sites/${CODE}`],
      ]);
      noControl(nav.querySelector("[data-opportunity-root]"));
      expect(nav.textContent).not.toMatch(/Sites|Renewable evaluation ›|F-109/);
    }

    // Evidence inspection: the exact accepted-ID union of the five day rows.
    fireEvent.click(screen.getByRole("button", { name: "Inspect opportunity evidence" }));
    const cited = Array.from(document.querySelectorAll("[data-opportunity-cited]"));
    expect(cited.map((a) => a.getAttribute("data-opportunity-cited"))).toEqual([EV1, EV2]);
    expect(cited[0].getAttribute("href")).toContain(`/sites/${CODE}/evidence`);

    // No renewable link and no evidence: noninteractive gaps.
    await show(
      body({ links: { renewable: null, site_work: null, scenario: null } }, {
        day_rows: body().opportunity!.day_rows.map((r) => ({ ...r, evidence_ids: [] })),
      }),
    );
    const gap = screen.getByText("Renewable evaluation unavailable");
    noControl(gap);
    expect(screen.queryByRole("link", { name: "Open renewable evaluation" })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Inspect opportunity evidence" }));
    expect(document.querySelector("[data-opportunity-evidence]")?.textContent).toBe("No selected opportunity evidence");

    // Refusals keep the shell and state the code's copy; no authored or positive state.
    for (const [read, copy] of [
      [{ status: "refused", httpStatus: 404, code: "DECISION_NOT_FOUND", message: null }, "This decision was not found at this site."],
      [{ status: "refused", httpStatus: 503, code: "DECISION_STORE_UNAVAILABLE", message: null }, "Decisions are unavailable right now. Try again."],
      [{ status: "unavailable", message: null }, "Decisions are unavailable right now. Try again."],
    ] as [DecisionRead<OpportunityDetailBody>, string][]) {
      cleanup();
      openAt(read);
      await settledScreen();
      await waitFor(() => expect(document.querySelector("[data-opportunity-refusal]")?.textContent).toBe(copy));
      expect(document.querySelector("[data-opportunity-chip]")).toBeNull();
      expect(document.querySelector("[data-opportunity-code]")).toBeNull();
    }

    // A non-mini Site makes no read.
    cleanup();
    const client = openAt(loaded(body()), "COLDCHAIN");
    await settledScreen();
    expect(document.querySelector("[data-opportunity-site-type-unsupported]")).not.toBeNull();
    expect(client.getOpportunity).not.toHaveBeenCalled();
  });

  it("opportunity_zero_multiple_and_short_study", async () => {
    const TZ = "Africa/Nairobi";
    const listRow = (oid: string, first: string, last: string, model = "mini-opportunity/1") => ({
      ...body(),
      opportunity: { ...body().opportunity!, id: oid, first_day: first, last_day: last, model_version: model },
    });
    const list = (rows: ReturnType<typeof listRow>[]): DecisionRead<OpportunityListBody> => ({
      status: "loaded",
      value: { schema_version: "mini-opportunities-1", window: { from: S_FROM, to: S_TO, known_at: S_KNOWN }, total_count: rows.length, rows, next_cursor: null },
    });
    async function entry(answer: DecisionRead<OpportunityListBody>, from: string, to: string) {
      cleanup();
      const client: MiniDecisionsClient = {
        getScenarios: vi.fn(() => Promise.resolve({ status: "unavailable" as const, message: null })),
        getAlternatives: vi.fn(() => Promise.resolve({ status: "unavailable" as const, message: null })),
        getOpportunity: vi.fn(() => Promise.resolve({ status: "unavailable" as const, message: null })),
        listOpportunities: vi.fn(() => Promise.resolve(answer)),
        getWorkContexts: vi.fn(() => Promise.resolve({ status: "unavailable" as const, message: null })),
      };
      render(
        <MemoryRouter>
          <OpportunityDecisionEntry
            client={client}
            siteCode={CODE}
            timeZone={TZ}
            window={{ from, to, known_at: S_KNOWN }}
            detailHref={(oid, k) => siteOpportunityHref(CODE, oid, k)}
          />
        </MemoryRouter>,
      );
      await waitFor(() => expect(document.querySelector('[data-opportunity-decision="loading"]')).toBeNull());
      return client;
    }
    const decision = () => document.querySelector("[data-opportunity-decision]");

    // Exactly one study with both days and the model: its typed detail link; one scoped list read.
    let client = await entry(
      list([listRow(OPP, "2026-10-06", "2026-10-10"), listRow(id(701), "2026-10-05", "2026-10-09"), listRow(id(702), "2026-10-06", "2026-10-10", "other/1")]),
      S_FROM,
      S_TO,
    );
    expect(client.listOpportunities).toHaveBeenCalledTimes(1);
    expect(client.listOpportunities).toHaveBeenCalledWith(CODE, { from: S_FROM, to: S_TO, known_at: S_KNOWN });
    expect(decision()?.getAttribute("data-opportunity-decision")).toBe("one");
    // PR-12.6: the exact CTA carries the selection's cutoff into the detail address.
    expect(decision()?.querySelector("a")?.getAttribute("href")).toBe(
      `/sites/${CODE}/opportunities/${OPP}?${new URLSearchParams({ known_at: S_KNOWN })}`,
    );

    // Zero exact matches (intersection alone never selects).
    await entry(list([listRow(id(701), "2026-10-05", "2026-10-09"), listRow(id(703), "2026-10-06", "2026-10-11")]), S_FROM, S_TO);
    expect(decision()?.textContent).toBe("Opportunity decision unavailable for this selected five-day study.");
    noControl(decision()!.querySelector("span"));

    // More than one exact root: the 503 integrity state, never a chosen row.
    await entry(list([listRow(OPP, "2026-10-06", "2026-10-10"), listRow(id(704), "2026-10-06", "2026-10-10")]), S_FROM, S_TO);
    expect(decision()?.getAttribute("data-opportunity-decision")).toBe("refused");
    expect(decision()?.textContent).toBe("Decisions are unavailable right now. Try again.");
    expect(decision()?.querySelector("a")).toBeNull();

    // A refused list read states its code's copy.
    await entry({ status: "refused", httpStatus: 403, code: "SITE_ACCESS_DENIED", message: null }, S_FROM, S_TO);
    expect(decision()?.textContent).toBe("You do not have access to this site.");

    // One to four complete local days: the shorter-study copy without a lookup.
    for (const to of ["2026-10-06T21:00:00.000000Z", "2026-10-09T21:00:00.000000Z"]) {
      client = await entry(list([listRow(OPP, "2026-10-06", "2026-10-10")]), S_FROM, to);
      expect(decision()?.textContent).toBe("Opportunity decision unavailable for fewer than five assessed days.");
      expect(client.listOpportunities).not.toHaveBeenCalled();
    }
  });

  it("opportunity_panel_order_and_narrow_budget", async () => {
    await show(body());
    const page = document.querySelector("[data-opportunity-page]")!;
    // Mock order: status bar, four cards, Bounded opportunity, then the Next decision | Consequence basis pair.
    const pieces = Array.from(page.querySelectorAll("[data-opportunity-status], [data-opportunity-cards], .panel h2, .panel h3"));
    expect(pieces.map((el) => (el.matches("[data-opportunity-status]") ? "status" : el.matches("[data-opportunity-cards]") ? "cards" : el.textContent))).toEqual([
      "status",
      "cards",
      "Bounded opportunity",
      "Next decision",
      "Consequence basis",
    ]);
    expect(page.querySelectorAll("[data-opportunity-cards] > li")).toHaveLength(4);
    // PR-12.2: compact spacing scoped to this card row; the shared grid rules are not overridden here.
    expect(MINI_CSS).toContain(".v69-cards[data-opportunity-cards] .v69-metric { padding: 10px 12px; }");
    expect(MINI_CSS).toContain(".v69-cards[data-opportunity-cards] .v69-metric--word .v69-metric__value { margin: 5px 0 4px; }");
    expect(MINI_CSS).not.toMatch(/data-opportunity-cards\][^{]*\{[^}]*grid-template-columns/);
    const pair = page.querySelector(".panel-pair")!;
    expect(Array.from(pair.querySelectorAll(".panel h2, .panel h3")).map((h) => h.textContent)).toEqual(["Next decision", "Consequence basis"]);
    // The evidence list scrolls inside its panel (bounded drawer) so the panel keeps its measured cap.
    fireEvent.click(screen.getByRole("button", { name: "Inspect opportunity evidence" }));
    expect(document.querySelector("[data-opportunity-evidence]")?.className).toContain("mini-opportunity-drawer");
    // Discovery stays as ruled: no Site/estate Opportunity index row or route is promoted (closure 4 S11/S21).
    expect(document.querySelector('a[href*="/findings/opportunities"]')).toBeNull();
  });

  it("opportunity_v69_panels_and_planted_rejection", async () => {
    await show(body());
    expectV69Panels("opportunity-finding");
    expectPlantedPanelRejected("opportunity-finding");
    const page = document.querySelector("[data-opportunity-page]")!;
    expect(page.querySelector("[data-opportunity-status]")).not.toBeNull();
    expect(page.querySelectorAll("[data-opportunity-cards] > li")).toHaveLength(4);
  });

  it("narrow_mock_panel_budgets", async () => {
    atWidth(390);
    try {
      await show(body());
      expectV69Panels("opportunity-finding");
      fireEvent.click(screen.getByRole("button", { name: "Inspect opportunity evidence" }));
      const drawer = document.querySelector("[data-opportunity-evidence]")!;
      expect(drawer.className).toContain("mini-opportunity-drawer");
      expect(drawer.closest(".panel")?.querySelector("h2")?.textContent).toBe("Bounded opportunity");
      // Evidence list: at most 96 px high with inner scroll.
      expect(MINI_CSS).toContain(".mini-opportunity-drawer { max-height: 96px; overflow-y: auto; }");
    } finally {
      atWidth(1024);
    }
  });

  it("exact_routes_no_dead_cta", async () => {
    await show(body());
    expect(location()).toBe(`/sites/${CODE}/opportunities/${OPP}`);
    noDeadCta(document.querySelector("[data-opportunity-page]") as HTMLElement);
    expect(document.querySelector('a[href*="/findings/opportunities"]')).toBeNull();
  });

  it("final_review_chip_tone_and_crumb_row_css", async () => {
    // Read from disk: vitest serves imported CSS as empty text (the estateRoots pattern). jsdom has no cascade, so the
    // rendered colour is asserted by the capture; this pins the selector shape that makes it win.
    const fs = (await import(/* @vite-ignore */ `node:${"fs"}`)) as { readFileSync: (p: string, e: string) => string };
    const cwd = (globalThis as unknown as { process: { cwd: () => string } }).process.cwd();
    const css = fs.readFileSync(`${cwd}/src/sites/w4-mini-decisions.css`, "utf8");
    // H1: `.badge--neutral` loads later at equal specificity, so each tone must be the compound `.badge.` selector.
    for (const tone of ["green", "amber", "blue", "gray"]) {
      expect(css).toMatch(new RegExp(`(^|\\n)\\.badge\\.mini-opportunity-tone--${tone} \\{[^}]*background:`));
      expect(css).not.toMatch(new RegExp(`(^|\\n)\\.mini-opportunity-tone--${tone} \\{`));
    }
    // M7: the crumb row is one wrapping flex line (v69 `.breadcrumbs`), so the Site suffix stays inline.
    expect(css).toMatch(/nav\.mini-finding-crumbs \{[^}]*display: flex;[^}]*flex-wrap: wrap/s);
    expect(css).toMatch(/:has\(> \.mini-opportunity-crumbs__root\) \+ \.breadcrumbs__item::before \{\s*content: none/s);
  });

  it("opportunity_chip_and_estate_lens_stay_unavailable", async () => {
    const findingIndex: FindingIndexClient = {
      getFindingIndex: vi.fn(() => Promise.resolve({ status: "forbidden" as const, message: null })),
    };
    for (const helper of [true, false]) {
      cleanup();
      render(
        <MemoryRouter>
          <SiteFindingIndex
            siteId={CODE}
            client={findingIndex}
            scope={{ domain: "all", from: S_FROM, to: S_TO }}
            links={{ scope: () => "/x", finding: () => "/y" }}
            onScope={() => undefined}
            fallback={null}
            opportunityHelper={helper}
          />
        </MemoryRouter>,
      );
      await settledScreen();
      const chipEl = document.querySelector('[data-site-findings-lenses] [data-chip-unavailable="Opportunities"], [data-site-findings-lenses] li:last-child');
      expect(chipEl?.textContent).toContain("Opportunities");
      expect(chipEl?.querySelector("a")).toBeNull();
      const note = document.querySelector("[data-opportunity-index-helper]");
      if (helper) {
        expect(note?.textContent).toBe("Opportunity index unavailable; open the renewable evaluation for this site's five-day study.");
        noControl(note);
      } else {
        expect(note).toBeNull();
      }
    }
  });
});
