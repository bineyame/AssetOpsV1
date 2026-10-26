/**
 * W5-03b E6: EV Site Financials > Scenarios (v6.9 `ev-scenarios`) from the authored E5 list
 * (`.agent/W5-03-build-spec.md` E6 card and consolidated correction; `.agent/W5-03b-ui-preflight-rulings.md` 11-16).
 */
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import type { EvSiteClient } from "../evSiteClient";
import {
  EV_SCENARIOS_MALFORMED,
  EV_SCENARIOS_UNREACHABLE,
  type EvScenarioItem,
  type EvScenariosClient,
  type EvScenariosRead,
  createEvScenariosClient,
  isEvScenariosRead,
} from "../evScenariosClient";
import {
  EV_SCENARIOS_CLOSING_NOTICE,
  EV_SCENARIOS_EMPTY_BODY,
  EV_SCENARIOS_LOADING,
  EV_SCENARIOS_PENDING,
  firstPageLine,
  utcMinute,
} from "../EvScenarios";
import type { SiteDetailClient, SiteDirectoryClient } from "../siteDirectoryClient";
import type { SiteDetailReadModel } from "../siteReadModel";
import { EMPTY_ANALYTICS_CLIENT } from "./analyticsFixtures";
import { expectPlantedPanelRejected, expectV69Panels, renderedPanelTitles } from "../../test/panelStructure";
import { settledScreen } from "../../test/settled";

const CODE = "EV-LAB-001";
const FROM = "2026-10-06T08:00:00.000000Z";
const TO = "2026-10-06T09:00:00.000000Z";
const KNOWN = "2026-10-06T09:00:00.000000Z";
const LATE = "2026-10-06T09:05:00.000000Z";
const AT = "2026-10-24T10:15:30.123456Z";
const id = (n: number) => `00000000-0000-4000-8000-${String(n).padStart(12, "0")}`;
const BLOCK = { classification: "REGISTERED_SIMULATION", state: "REGISTERED_SIMULATION", source_ids: [], evidence_ids: [], basis_sha256: null, reasons: [] };

function item(n: number, over: Partial<EvScenarioItem> = {}): EvScenarioItem {
  return {
    id: id(500 + n),
    code: `ESCN-${String(n).padStart(6, "0")}`,
    revision_id: id(600 + n),
    revision_no: 1,
    name: `Tariff what-if ${n}`,
    kind: "GROSS_TARIFF_CONTEXT",
    assumptions: { tariff_per_kwh: "0.3100", currency: "KES" },
    authored_basis: {
      from: FROM,
      to: TO,
      cutoff: KNOWN,
      assessment_revision_id: id(50),
      session_revision_ids: [id(60), id(61)],
      accepted_evidence_ids: [id(101), id(102)],
      foundation_revision_id: id(40),
      consequence_revision_id: null,
      tariff_revision_id: null,
      source_provenance: { ...BLOCK, extra_public_field: "kept" },
    },
    recorded_at: "2026-10-24T10:00:12.000000Z",
    scenario_state: "DEFINED",
    ...over,
  };
}

function read(state = "CURRENT", items: EvScenarioItem[] = [], over: Partial<EvScenariosRead> = {}): EvScenariosRead {
  return {
    schema_version: "ev-scenarios-1",
    site_id: id(1),
    window: { from: FROM, to: TO, known_at: KNOWN, committed_watermark: KNOWN },
    scenario_at: AT,
    selection: {
      state: state as EvScenariosRead["selection"]["state"],
      assessment_revision_id: id(50),
      session_revision_ids: [id(60), id(61)],
      accepted_evidence_ids: [id(101), id(102)],
      source_provenance: BLOCK,
    },
    items,
    next_cursor: null,
    ...over,
  };
}

const SITE = {
  site_id: CODE,
  display_name: "EV lab depot",
  site_type: "EV_CHARGING",
  location: { country: "Ethiopia", locality: "Addis Ababa" },
  timezone: "Africa/Addis_Ababa",
  lifecycle_status: "PLANNED",
  origin: "USER",
  source: { mode: "SIMULATED" },
  template: null,
  configuration_store: "POSTGRES",
} as unknown as SiteDetailReadModel;
const detail: SiteDetailClient = { getSite: () => Promise.resolve({ status: "loaded", site: SITE }) };
const directory: SiteDirectoryClient = { listSites: () => Promise.resolve({ status: "loaded", sites: [SITE] }) };

type Answer = Awaited<ReturnType<EvScenariosClient["list"]>>;
const loaded = (value: EvScenariosRead): Answer => ({ status: "loaded", value });
const Q = `?from=${encodeURIComponent(FROM)}&to=${encodeURIComponent(TO)}&known_at=${encodeURIComponent(KNOWN)}`;

function renderScenarios(answer: Answer | (() => Promise<Answer>), query = `${Q}&scenario_at=${encodeURIComponent(AT)}`) {
  const list = vi.fn(typeof answer === "function" ? answer : () => Promise.resolve(answer));
  const evSiteRead = vi.fn(() => new Promise(() => undefined));
  const evSite = new Proxy({}, { get: () => evSiteRead }) as unknown as EvSiteClient;
  render(
    <MemoryRouter initialEntries={[`/sites/${CODE}/ev/financials/scenarios${query}`]}>
      <App flags={featureFlagsWith(false)} siteDirectory={directory} siteDetail={detail} siteAnalytics={EMPTY_ANALYTICS_CLIENT} evSite={evSite} evScenarioList={{ list }} />
    </MemoryRouter>,
  );
  return { list, evSiteRead };
}

const main = () => document.querySelector("main") as HTMLElement;
const text = (el: Element | null) => (el?.textContent ?? "").replace(/\s+/g, " ").trim();
const panel = () => document.querySelector("section.panel") as HTMLElement;

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("W5-03b E6: EV Scenarios", () => {
  it("routes_states_loading: frame, tabs, loading, empty, unknown, refusal and unavailable states", async () => {
    const pending = renderScenarios(() => new Promise(() => undefined));
    expect(await screen.findByText(EV_SCENARIOS_LOADING)).toBeTruthy();
    await vi.waitFor(() => expect(pending.list).toHaveBeenCalledWith(CODE, { from: FROM, to: TO, known_at: KNOWN, scenario_at: AT }));
    cleanup();

    const { evSiteRead } = renderScenarios(loaded(read()));
    await settledScreen();
    expect(evSiteRead).not.toHaveBeenCalled();
    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("EV lab depot");
    expect(text(main())).toContain("Financials · scenarios (placeholder)");
    expect(Array.from(document.querySelectorAll("nav.breadcrumbs li, .breadcrumbs li")).map(text).join(" › ")).toContain("EV lab depot › Financials › Scenarios");
    const tabs = Array.from(document.querySelectorAll('nav[aria-label="Financials sections"] a')).map((a) => [text(a), a.getAttribute("href"), a.getAttribute("aria-current")]);
    expect(tabs).toEqual([
      ["Overview", `/sites/${CODE}/ev/financials${Q}`, null],
      ["Assumptions", `/sites/${CODE}/ev/financial-assumptions${Q}`, null],
      ["Scenarios", `/sites/${CODE}/ev/financials/scenarios${Q}&scenario_at=${encodeURIComponent(AT)}`, "page"],
    ]);
    expect(document.querySelector('[aria-current="page"][href*="/ev"]')).not.toBeNull();
    // CURRENT empty: the exact mock panel, empty block and blue notice.
    expectV69Panels("ev-scenarios");
    expectPlantedPanelRejected("ev-scenarios");
    expect(text(panel().querySelector("h2"))).toBe("Financial scenarios");
    expect(text(panel())).toContain("Placeholder · to be designed with the owner");
    expect(text(panel().querySelector("[data-ev-scenarios-empty] h3"))).toBe("No scenario defined yet");
    expect(text(panel().querySelector("[data-ev-scenarios-empty] p"))).toBe(EV_SCENARIOS_EMPTY_BODY);
    expect(panel().nextElementSibling?.matches("[data-ev-scenarios-closing-notice]")).toBe(true);
    expect(text(panel().nextElementSibling)).toBe(EV_SCENARIOS_CLOSING_NOTICE);
    expect(document.querySelector("[data-ev-scenarios-state-notice]")).toBeNull();
    expect(main().querySelector("form, input, textarea, select")).toBeNull();
    expect(text(main())).not.toMatch(/Create|New scenario|Add scenario/);
    cleanup();

    // Ruling 11: a valid no-selection with null window renders the empty block after the R15 UNKNOWN sentence.
    renderScenarios(
      loaded(read("UNKNOWN", [], {
        window: { from: null, to: null, known_at: null, committed_watermark: null },
        selection: { state: "UNKNOWN", assessment_revision_id: null, session_revision_ids: [], accepted_evidence_ids: [], source_provenance: BLOCK },
      })),
      "",
    );
    await settledScreen();
    const unknown = document.querySelector("[data-ev-scenarios-state-notice]")!;
    expect(text(unknown)).toBe("No selected EV session assessment covers this window yet.");
    expect(unknown.nextElementSibling).toBe(panel());
    expect(renderedPanelTitles()).toEqual(["Financial scenarios"]);
    expect(text(panel().querySelector("[data-ev-scenarios-empty] h3"))).toBe("No scenario defined yet");
    expect(panel().nextElementSibling?.matches("[data-ev-scenarios-closing-notice]")).toBe(true);
    expect(text(main())).not.toContain("EV scenarios unavailable");
    cleanup();

    const refused: Answer = { status: "refused", httpStatus: 422, code: "EV_WINDOW_INVALID", message: "'from' must be earlier than 'to'." };
    renderScenarios(refused, `?from=${TO}&to=${FROM}`);
    await settledScreen();
    expect(text(document.querySelector("[data-panel-gap='ev-depth-refusal']"))).toBe("The selected window needs both a start and an end, with the start before the end.");
    expect(renderedPanelTitles()).toEqual(["Financial scenarios"]);
    expect(text(main())).not.toContain("EV_WINDOW_INVALID 'from'");
    expect(text(main())).not.toContain("No scenario defined yet");
    expect(document.querySelector("[data-ev-depth-correction]")?.textContent).toBe("Read without a selected window");
    expect(screen.queryByRole("button", { name: /Retry|Reload/ })).toBeNull();
    cleanup();
    const r = renderScenarios({ status: "refused", httpStatus: 503, code: "EV_UNAVAILABLE", message: null });
    await settledScreen();
    fireEvent.click(screen.getByRole("button", { name: "Reload" }));
    await settledScreen();
    expect(r.list).toHaveBeenCalledTimes(2);
    expect(r.list.mock.calls[1]).toEqual(r.list.mock.calls[0]);
    cleanup();

    for (const message of [EV_SCENARIOS_MALFORMED, EV_SCENARIOS_UNREACHABLE]) {
      renderScenarios({ status: "unavailable", message });
      await settledScreen();
      expect(text(document.querySelector("[data-panel-gap='ev-depth-refusal']"))).toBe("EV evidence is temporarily unavailable. Retry.");
      expect(message.length).toBeGreaterThan(0);
      expect(text(main())).not.toContain("No scenario defined yet");
      cleanup();
    }
  });

  it("row_disclosure_and_client: authored row, exact basis disclosure and exact client validation", async () => {
    const one = item(1);
    renderScenarios(loaded(read("CURRENT", [one])));
    await settledScreen();
    expectV69Panels("ev-scenarios");
    expect(panel().querySelector("[data-ev-scenarios-empty]")).toBeNull();
    const row = document.querySelector(`[data-ev-scenario-row="${one.id}"]`)!;
    expect(Array.from(row.children).map(text)).toEqual([
      "Tariff what-if 1ESCN-000001 revision 1",
      "0.3100 KES/kWh gross tariff",
      "Selected evidence through 2026-10-06 09:00 UTCReview assumptions →",
      "2026-10-24 10:00 UTC",
      "Defined",
    ]);
    const review = screen.getByRole("button", { name: "Review assumptions →" });
    expect(review.getAttribute("aria-expanded")).toBe("false");
    expect(document.querySelector("[data-ev-scenario-basis]")).toBeNull();
    fireEvent.click(review);
    expect(review.getAttribute("aria-expanded")).toBe("true");
    const expansion = document.querySelector(`[data-ev-scenario-expansion="${one.id}"]`)!;
    expect(expansion.previousElementSibling).toBe(row);
    expect(expansion.querySelector("td")!.getAttribute("colspan")).toBe("5");
    const dl = expansion.querySelector("dl")!;
    const ddText = (dd: Element | null) => (dd !== null && dd.children.length > 0 ? Array.from(dd.children).map(text).join(" ") : text(dd));
    const pairs = Array.from(dl.querySelectorAll("dt")).map((dt) => [text(dt), ddText(dt.nextElementSibling)]);
    expect(pairs).toEqual([
      ["Kind", "GROSS_TARIFF_CONTEXT"],
      ["Assumptions", "tariff_per_kwh: 0.3100 currency: KES"],
      ["Window", `${FROM} – ${TO}`],
      ["Evidence cutoff", KNOWN],
      ["Assessment revision", id(50)],
      ["Session revisions", `${id(60)} ${id(61)}`],
      ["Accepted evidence", `2 records ${id(101)} ${id(102)}`],
      ["Foundation revision", id(40)],
      ["Consequence revision", "None"],
      ["Tariff revision", "None"],
      ["Source classification", "REGISTERED_SIMULATION"],
      ["Revision", one.revision_id],
    ]);
    // Every ID sits in its own source-reference span (one per line).
    const refs = Array.from(dl.querySelectorAll('[data-vocabulary-exempt="source-reference"]')).map(text);
    for (const value of [id(50), id(60), id(61), id(101), id(102), id(40), one.revision_id]) expect(refs).toContain(value);
    expect(text(main())).not.toMatch(/outcome|saved|lost|collected/i);

    // Ruling 20: a single accepted evidence record is `1 record`; the plural stays `{n} records`.
    cleanup();
    const solo = item(2, { authored_basis: { ...one.authored_basis, accepted_evidence_ids: [id(101)] } });
    renderScenarios(loaded(read("CURRENT", [solo])));
    await settledScreen();
    fireEvent.click(screen.getByRole("button", { name: "Review assumptions →" }));
    const soloDt = Array.from(document.querySelectorAll("[data-ev-scenario-expansion] dt")).find((dt) => text(dt) === "Accepted evidence")!;
    expect(text(soloDt.nextElementSibling!.children[0])).toBe("1 record");
    cleanup();

    // Client: exact keys, nullable window/selection (ruling 11), provenance with extra fields (ruling 13).
    const good = read("CURRENT", [one]);
    expect(isEvScenariosRead(good)).toBe(true);
    expect(isEvScenariosRead({ ...good, window: { from: null, to: null, known_at: null, committed_watermark: null } })).toBe(true);
    expect(isEvScenariosRead({ ...good, selection: { ...good.selection, assessment_revision_id: null } })).toBe(true);
    expect(isEvScenariosRead({ ...good, extra: 1 })).toBe(false);
    expect(isEvScenariosRead({ ...good, total_pages: 1 })).toBe(false);
    expect(isEvScenariosRead({ ...good, schema_version: "cold-scenarios-1" })).toBe(false);
    expect(isEvScenariosRead({ ...good, selection: { ...good.selection, state: "FRESH" } })).toBe(false);
    expect(isEvScenariosRead({ ...good, selection: { ...good.selection, source_provenance: { state: "X" } } })).toBe(false);
    expect(isEvScenariosRead({ ...good, selection: { ...good.selection, source_provenance: [] } })).toBe(false);
    const bad = (over: Partial<EvScenarioItem>) => isEvScenariosRead(read("CURRENT", [{ ...one, ...over }]));
    expect(bad({ code: "ESCN-1" })).toBe(false);
    expect(bad({ revision_no: 0 })).toBe(false);
    expect(bad({ name: "" })).toBe(false);
    expect(bad({ name: "x".repeat(161) })).toBe(false);
    expect(bad({ kind: "STOCK_VALUE_CONTEXT" as never })).toBe(false);
    expect(bad({ assumptions: { tariff_per_kwh: "0.31", currency: "kes" } })).toBe(false);
    expect(bad({ scenario_state: "CURRENT" as never })).toBe(false);
    expect(bad({ authored_basis: { ...one.authored_basis, source_provenance: { classification: 3 } as never } })).toBe(false);
    expect(bad({ authored_basis: { ...one.authored_basis, extra: 1 } as never })).toBe(false);

    const calls: string[] = [];
    vi.stubGlobal("fetch", vi.fn((url: string) => {
      calls.push(url);
      return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({ ...good, items: [{ ...one, outcome: "saved" }] }) });
    }));
    const client = createEvScenariosClient("/api/sites");
    expect(await client.list(CODE, { from: FROM, to: TO, known_at: null, scenario_at: AT })).toEqual({ status: "unavailable", message: EV_SCENARIOS_MALFORMED });
    expect(calls[0]).toBe(`/api/sites/${CODE}/ev/financials/scenarios?from=${encodeURIComponent(FROM)}&to=${encodeURIComponent(TO)}&scenario_at=${encodeURIComponent(AT)}`);
    expect(calls[0]).not.toMatch(/limit|cursor/);
    vi.stubGlobal("fetch", vi.fn(() => Promise.reject(new Error("down"))));
    expect(await client.list(CODE, { from: null, to: null, known_at: null, scenario_at: null })).toEqual({ status: "unavailable", message: EV_SCENARIOS_UNREACHABLE });
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve({ ok: false, status: 422, json: () => Promise.resolve({ error: { code: "EV_WINDOW_INVALID", message: "No" } }) })));
    expect(await client.list(CODE, { from: TO, to: FROM, known_at: null, scenario_at: null })).toEqual({ status: "refused", httpStatus: 422, code: "EV_WINDOW_INVALID", message: "No" });
    expect(utcMinute("2026-10-06T09:05:59.999999Z")).toBe("2026-10-06 09:05 UTC");
  });

  it("basis_disclosure_and_pending_historical: pending, historical and first-page notices", async () => {
    // PENDING_RECOMPUTE keeps the E6 pending notice; the earlier authored row stays listed.
    renderScenarios(loaded(read("PENDING_RECOMPUTE", [item(1)], { window: { from: FROM, to: TO, known_at: LATE, committed_watermark: LATE } })));
    await settledScreen();
    const pend = document.querySelector("[data-ev-scenarios-state-notice]")!;
    expect(text(pend)).toBe(EV_SCENARIOS_PENDING);
    expect(pend.nextElementSibling).toBe(panel());
    expect(renderedPanelTitles()).toEqual(["Financial scenarios"]);
    expect(panel().nextElementSibling?.matches("[data-ev-scenarios-closing-notice]")).toBe(true);
    expect(document.querySelectorAll("[data-ev-scenario-row]")).toHaveLength(1);
    cleanup();

    // Ruling 16: an earlier known_at than the committed watermark marks an unsuperseded row Historical, with R15.
    const historical = item(2, { scenario_state: "HISTORICAL" });
    renderScenarios(loaded(read("HISTORICAL", [historical], { window: { from: FROM, to: TO, known_at: KNOWN, committed_watermark: LATE } })));
    await settledScreen();
    const notice = document.querySelector("[data-ev-scenarios-state-notice]")!;
    expect(text(notice)).toBe("This result reflects records known at the selected cutoff.");
    expect(notice.nextElementSibling).toBe(panel());
    expect(text(document.querySelector(`[data-ev-scenario-row="${historical.id}"] td:last-child`))).toBe("Historical");
    expect(document.querySelector("[data-ev-scenarios-first-page]")).toBeNull();
    cleanup();

    // Ruling 12 (R98): a further page is disclosed below the table; there is no pager.
    const items = Array.from({ length: 50 }, (_, n) => item(n + 10));
    renderScenarios(loaded(read("CURRENT", items, { next_cursor: "opaque-cursor" })));
    await settledScreen();
    expect(document.querySelectorAll("[data-ev-scenario-row]")).toHaveLength(50);
    const line = panel().querySelector("[data-ev-scenarios-first-page]")!;
    expect(text(line)).toBe(firstPageLine(50));
    expect(text(line)).toBe("Showing first 50 authored scenarios. More exist; later pages are not available in this view.");
    // E6-L2: the R98 line sits immediately below the authored DataTable's scroller (no fallback).
    const above = line.previousElementSibling!;
    expect(above.matches(".data-table__scroll")).toBe(true);
    expect(above.querySelector("table.data-table")).not.toBeNull();
    expect(panel().querySelector("nav, [data-scenarios-pages]")).toBeNull();
    expect(screen.queryByRole("button", { name: /Next|First page/ })).toBeNull();
    expectV69Panels("ev-scenarios");
  });
});
