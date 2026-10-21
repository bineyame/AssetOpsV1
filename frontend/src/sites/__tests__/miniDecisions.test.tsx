import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import { FinancialsSections } from "../../shell/SiteAnalyticsFrames";
import type { DecisionRead, MiniDecisionsClient, ScenarioListBody, ScenarioRow } from "../miniDecisionsClient";
import { microsecondBefore } from "../miniDecisionsClient";
import { scenarioMoney } from "../MiniScenarios";
import type { SiteDetailClient, SiteDirectoryClient } from "../siteDirectoryClient";
import type { SiteDetailReadModel } from "../siteReadModel";
import { EMPTY_ANALYTICS_CLIENT } from "./analyticsFixtures";
import { settledScreen } from "../../test/settled";

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

function Where() {
  const location = useLocation();
  return <output data-location>{location.pathname + location.search}</output>;
}

function renderAt(path: string, answers: DecisionRead<ScenarioListBody>[], siteType = "MINIGRID", code = CODE) {
  const queue = [...answers];
  const client: MiniDecisionsClient = {
    getScenarios: vi.fn(() => Promise.resolve(queue.length > 1 ? queue.shift()! : queue[0])),
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

describe("W4-03 unit 6a: mini Financials > Scenarios", () => {
  it("scenario_empty_populated_and_refused", async () => {
    renderAt(`/sites/${CODE}/financials/scenarios`, [ok(list([]))]);
    await settledScreen();
    await screen.findByText("No scenario defined yet");
    expect(main().textContent).toContain(
      "A scenario compares a declared what-if with the measured case. None has been defined for this site.",
    );
    expect(main().textContent).toContain(
      "For example, a different stop setting, stock value or tariff may be declared when an authorized authoring path is available.",
    );
    expect(main().textContent).toContain("No authored what-if at this site and cutoff.");
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
    expect(first[2]).toBe(`${id(21)}${id(22)}`);
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
