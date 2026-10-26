import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import type { EvAssessmentClient, EvRead } from "../evAssessmentClient";
import { type EvConsequence, type EvDepthClient, type EvEnergyRead, type ImportSample, isEvEnergyRead } from "../evDepthClient";
import { EV_CHART_H, EV_CHART_W, EvDepthPowerChart, xTicks, yMax } from "../evDepthGraphics";
import { bridgeRows, grossTariffText, utcSeconds } from "../EvEnergy";
import type { SiteDetailClient, SiteDirectoryClient } from "../siteDirectoryClient";
import type { SiteDetailReadModel } from "../siteReadModel";
import { EMPTY_ANALYTICS_CLIENT } from "./analyticsFixtures";
import { expectPlantedPanelRejected, expectV69Panels } from "../../test/panelStructure";
import { settledScreen } from "../../test/settled";

/*
 * W5-03a E3 (`.agent/W5-03-build-spec.md` E3 card, closure 2 and the pre-flight E3 ruling): an EV_CHARGING Site's
 * Performance/Energy route renders v6.9 `energy` from the selected `ev-depth-1` read, with the restored import chart
 * drawn by the registered `evDepthGraphics.tsx`. Fixture values follow the E1 producer window `[08:00, 09:00)`.
 */

afterEach(cleanup);

const CODE = "EV-LAB-001";
const FROM = "2026-10-06T08:00:00.000000Z";
const TO = "2026-10-06T09:00:00.000000Z";
const KNOWN = "2026-10-06T09:00:00.000000Z";
const id = (n: number) => `00000000-0000-4000-8000-${String(n).padStart(12, "0")}`;
const t = (hh: number, mm: number) => `2026-10-06T${String(hh).padStart(2, "0")}:${String(mm).padStart(2, "0")}:00.000000Z`;
const sample = (n: number, at: string, kw: string): ImportSample => ({ source_time: at, import_kw: kw, evidence_id: id(n) });
const SAMPLES = [sample(201, t(8, 5), "0"), sample(202, t(8, 15), "60"), sample(203, t(8, 15), "60"), sample(204, t(8, 30), "60")];
const ESTIMATED: EvConsequence = {
  revision_id: id(70), revision_no: 1, state: "ESTIMATED", reason: null, quantity_kwh: "30.000", tariff_revision_id: id(71),
  tariff_value: "0.30", currency: "USD", amount: "9.00", overlap_group: null, recorded_at: KNOWN, tariff_recorded_at: KNOWN,
  source_gate: null, session_revision_ids: [id(60)], evidence_ids: [id(101)], limitation: "Gross tariff scenario; not cash collected.",
};

function read(energy: Partial<EvEnergyRead["energy"]> = {}, state = "CURRENT"): EvEnergyRead {
  const samples = energy.import_samples ?? SAMPLES;
  return {
    schema_version: "ev-depth-1",
    site_id: id(1),
    window: { from: FROM, to: TO, known_at: KNOWN, committed_watermark: KNOWN },
    selection: {
      state: state as EvEnergyRead["selection"]["state"],
      assessment_revision_id: id(50),
      session_revision_ids: [id(60)],
      accepted_evidence_ids: [id(101)],
      source_provenance: { classification: "REGISTERED_SIMULATION" },
    },
    energy: {
      metered_complete_kwh: "30.000",
      partial_kwh: "0.000",
      unknown_seconds: 0,
      energy_limitation: null,
      import_sample_count: samples.length,
      import_samples: samples,
      observed_peak_import_kw: "60",
      peak_sample_at: t(8, 15),
      configured_import_limit_kw: "80",
      peak_below_limit: "YES",
      power_constraint_state: "UNKNOWN",
      consequence: ESTIMATED,
      ...energy,
    },
    links: {
      sessions: `/api/sites/${CODE}/ev/sessions?from=${FROM}&to=${TO}&known_at=${KNOWN}`,
      evidence_analysis: `/api/sites/${CODE}/ev/evidence/analysis?from=${FROM}&to=${TO}&known_at=${KNOWN}`,
      financials: `/api/sites/${CODE}/ev/financials?from=${FROM}&to=${TO}&known_at=${KNOWN}`,
    },
  };
}

const SITE = {
  site_id: CODE, display_name: "EV lab depot", site_type: "EV_CHARGING", location: { country: "Ethiopia", locality: "Addis Ababa" },
  timezone: "Africa/Addis_Ababa", lifecycle_status: "PLANNED", origin: "USER", source: { mode: "SIMULATED" }, template: null,
  configuration_store: "POSTGRES",
} as unknown as SiteDetailReadModel;
const detail: SiteDetailClient = { getSite: () => Promise.resolve({ status: "loaded", site: SITE }) };
const directory: SiteDirectoryClient = { listSites: () => Promise.resolve({ status: "loaded", sites: [SITE] }) };
const never = <T,>(): Promise<EvRead<T>> => new Promise(() => undefined);
const evAssessment: EvAssessmentClient = { listSessions: never, getSession: never, listFindings: never, getFinding: never };
type Answer = Awaited<ReturnType<EvDepthClient["getEnergy"]>>;

function renderEnergy(answer: Answer | (() => Promise<Answer>), query = `?from=${FROM}&to=${TO}`) {
  const getEnergy = vi.fn(typeof answer === "function" ? answer : () => Promise.resolve(answer));
  const depth: EvDepthClient = { getAvailability: vi.fn(), getEnergy, getHealth: vi.fn() };
  render(
    <MemoryRouter initialEntries={[`/sites/${CODE}/performance/energy${query}`]}>
      <App flags={featureFlagsWith(false)} siteDirectory={directory} siteDetail={detail} siteAnalytics={EMPTY_ANALYTICS_CLIENT} evAssessment={evAssessment} evDepth={depth} />
    </MemoryRouter>,
  );
  return getEnergy;
}

const loaded = (value: EvEnergyRead): Answer => ({ status: "loaded", value });
const main = () => document.querySelector("main") as HTMLElement;
const text = (selector: string) => document.querySelector(selector)?.textContent ?? null;
const cards = () => Array.from(document.querySelectorAll("[data-ev-energy-card]")).map((c) => [
  c.querySelector(".v69-metric__label")?.textContent,
  c.querySelector(".v69-metric__value")?.textContent,
  c.querySelector(".v69-metric__note")?.textContent,
]);
const conclusions = () => Array.from(document.querySelectorAll("[data-key-value]")).map((r) => [r.querySelector("dt")?.textContent, r.querySelector("dd")?.textContent]);
const bridge = () => Array.from(document.querySelectorAll("[data-ev-bridge-row]")).map((r) => Array.from(r.children).map((c) => c.textContent));
const marks = () => Array.from(document.querySelectorAll("[data-ev-mark]"));

describe("W5-03a E3: EV Energy", () => {
  it("energy_states_table_loading", async () => {
    let resolve: (value: Answer) => void = () => undefined;
    renderEnergy(() => new Promise<Answer>((r) => (resolve = r)));
    const loading = await screen.findByText("Loading the site's charging energy.");
    expect(loading.className).toBe("prose");
    resolve(loaded(read()));
    await settledScreen();
    expect(main().getAttribute("data-ev-view")).toBe("energy");
    expectV69Panels("energy");
    expectPlantedPanelRejected("energy");
    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("EV lab depot");
    expect(main().textContent).toContain("Performance · charging energy and site-power context");
    expect(document.querySelector('[data-performance-subtab="energy"]')?.getAttribute("aria-current")).toBe("page");
    expect(document.querySelectorAll("[data-tab-unavailable]")).toHaveLength(0);
    // Status: measured basis only on complete evidence; the meter-basis action stays in the status line.
    expect(text(".status-strip")).toContain("Energy basis: measured");
    expect(text("[data-ev-energy-status]")).toBe("Complete session meter records · incomplete session energy excluded");
    expect(document.querySelector(".status-strip [data-ev-meter-basis]")?.getAttribute("href")).toBe(
      `/sites/${CODE}/ev/evidence/analysis?from=${encodeURIComponent(FROM)}&to=${encodeURIComponent(TO)}&known_at=${encodeURIComponent(KNOWN)}`,
    );
    expect(cards()).toEqual([
      ["Metered session energy", "30.000 kWh", "Complete metered sessions only"],
      ["Observed peak import", "60 kW", "Selected 1-hour window"],
      ["Declared site limit", "80 kW", "Time-valid configuration"],
      ["Gross tariff estimate", "9.00 USD", "Scenario tariff: 0.30 USD/kWh"],
    ]);
    expect(document.querySelectorAll("[data-ev-energy-disclosure]")).toHaveLength(0);
    // Chart: one mark per accepted sample (equal-time marks separate), no connecting path, dashed declared limit.
    expect(marks().map((m) => m.getAttribute("data-ev-mark"))).toEqual([id(201), id(202), id(203), id(204)]);
    expect(marks().every((m) => m.getAttribute("r") === "5")).toBe(true);
    expect(marks()[1].getAttribute("cx")).toBe(marks()[2].getAttribute("cx"));
    const svg = document.querySelector(".ev-depth-graphic__scroll svg") as SVGElement;
    expect(svg.getAttribute("viewBox")).toBe(`0 0 ${EV_CHART_W} ${EV_CHART_H}`);
    expect(svg.getAttribute("aria-label")).toBe("Site import and power limit");
    expect(svg.querySelectorAll("path, polyline")).toHaveLength(0);
    expect(document.querySelector("[data-ev-limit-line] line")?.getAttribute("stroke-dasharray")).toBe("6 4");
    expect(Array.from(document.querySelectorAll("[data-ev-x-tick]")).map((x) => x.textContent)).toEqual(["08:00", "08:10", "08:20", "08:30", "08:40", "08:50", "09:00"]);
    expect(Array.from(document.querySelectorAll("[data-ev-y-tick] text")).map((x) => x.textContent)).toEqual(["0", "25", "50", "75", "100"]);
    expect(text("[data-ev-y-unit]")).toBe("kW");
    expect(text("[data-ev-limit-line] text")).toBe("80 kW limit");
    expect(marks()[0].querySelector("title")?.textContent).toBe("Site import 0 kW · 08:05:00 UTC");
    // H3/plot frame: legend follows the svg; no frame rectangle when marks exist.
    expect(document.querySelector(".ev-depth-graphic__scroll")?.nextElementSibling?.classList.contains("ev-depth-graphic__legend")).toBe(true);
    expect(document.querySelector(".ev-depth-graphic__frame")).toBeNull();
    expect(Array.from(document.querySelectorAll(".ev-depth-graphic__legend .legend-item")).map((x) => x.textContent)).toEqual(["Site import", "Site power limit"]);
    // H4: the sentence is the panel description under the heading, not a chart note below the figure.
    expect(text(".panel__description")).toBe("Observed import is not proof of vehicle-requested power");
    expect(document.querySelector("[data-ev-import-note]")).toBeNull();
    expect(document.querySelector(".ev-depth-graphic")?.parentElement?.querySelector(".chart-note, .v69-chart-note")).toBeNull();
    // M3: number and small unit are separate; H1: the conclusion note uses the global chart-note class.
    expect(document.querySelector('[data-ev-energy-card="energy"] .v69-metric__value small')?.textContent).toBe("kWh");
    expect(document.querySelector('[data-ev-energy-card="peak"] .v69-metric__value small')?.textContent).toBe("kW");
    expect(document.querySelector("[data-ev-conclusion-note]")?.classList.contains("v69-chart-note")).toBe(true);
    // L7: bridge first-column cells are regular weight but stay row headers.
    expect(document.querySelector("[data-ev-bridge-row] th[scope='row']")?.classList.contains("ev-bridge-rowhead")).toBe(true);
    expect(document.querySelector("[data-ev-samples-empty]")).toBeNull();
    // Measure/Value detail stays in a closed disclosure with the exact sample facts.
    const details = document.querySelector("details") as HTMLDetailsElement;
    expect(details.open).toBe(false);
    expect(text('[data-ev-measure="peak-time"] td')).toBe("08:15:00 UTC");
    expect(document.querySelectorAll('[data-ev-measure="sample"]')).toHaveLength(4);
    // Conclusions: the five mock key-value labels; Yes green, Not established amber; battery Unknown with its gap.
    expect(conclusions()).toEqual([
      ["Observed peak below limit", "Yes"],
      ["Site limit caused interruption", "Not established"],
      ["Requested vehicle power", "Incomplete evidence"],
      ["Stationary battery", "Unknown Battery configuration is not established by this Foundation."],
      ["Billing settlement", "Not connected"],
    ]);
    expect(document.querySelector('[data-key-value="below"] .badge')?.className).toContain("ev-tone--green");
    expect(document.querySelector('[data-key-value="interruption"] .badge')?.className).toContain("ev-tone--amber");
    expect(text("[data-ev-conclusion-note]")).toBe("Revenue is an estimate from metered kWh and the declared tariff, not payment evidence.");
    expect(bridge()).toEqual([
      ["30.000 kWh complete-record delivery", "0.30 USD/kWh gross tariff scenario", "9.00 USD gross estimate", "Gross tariff scenario; not cash collected."],
      ["Incomplete session", "No complete meter interval", "Unavailable", "No extrapolated energy silently added"],
      ["Interrupted service", "No demand/sales baseline", "Unpriced exposure", "No invented lost revenue"],
    ]);
    expect(Array.from(document.querySelectorAll(".data-table__scroll--sticky")).length).toBe(2);
    for (const literal of ["76", "120 kWh", "$36", "Not configured", "Not applicable", "16:00"]) expect(main().textContent).not.toContain(literal);
  });

  it("partial energy keeps complete and partial separate and never prices the partial amount", async () => {
    renderEnergy(loaded(read({ metered_complete_kwh: null, partial_kwh: "25.000", unknown_seconds: 300, consequence: null, configured_import_limit_kw: null, peak_below_limit: "UNKNOWN" })));
    await settledScreen();
    expect(text(".status-strip")).toContain("Energy basis: limited");
    expect(text("[data-ev-energy-status]")).toBe("Complete session meter records not established · incomplete session energy kept separate");
    expect(cards().map((c) => c.slice(1))).toEqual([
      ["Unknown", "Complete metered sessions only"],
      ["60 kW", "Selected 1-hour window"],
      ["Unknown", "No time-valid site limit declared"],
      ["Unknown", "Scenario tariff not established"],
    ]);
    expect(Array.from(document.querySelectorAll("[data-ev-energy-disclosure]")).map((p) => p.textContent)).toEqual([
      "25.000 kWh from incomplete sessions is shown separately and not included.",
      "Meter coverage is unknown for 5 min of session time.",
    ]);
    expect(text("[data-ev-energy-empty]")).toBe("No complete metered delivery is established for this window.");
    // No limit: no dashed line, both legend labels remain (muted limit swatch); a sub-limit peak never exonerates the limit.
    expect(document.querySelector("[data-ev-limit-line]")).toBeNull();
    expect(Array.from(document.querySelectorAll(".ev-depth-graphic__legend .legend-item")).map((x) => x.textContent)).toEqual(["Site import", "Site power limit"]);
    expect(document.querySelector("[data-ev-legend-limit]")?.getAttribute("data-ev-legend-limit")).toBe("none");
    expect(conclusions()[0]).toEqual(["Observed peak below limit", "Unknown"]);
    expect(conclusions()[1]).toEqual(["Site limit caused interruption", "Not established"]);
    expect(text("[data-ev-conclusion-note]")).toBe("No eligible revenue estimate is established; no payment evidence is connected");
    expect(bridge()).toEqual([
      ["Unknown", "No eligible gross tariff scenario.", "Unpriced", "No collections or profit claim"],
      ["25.000 kWh incomplete-session delivery", "No complete meter interval", "Not priced", "No extrapolated energy silently added"],
      ["Interrupted service", "No demand/sales baseline", "Unpriced exposure", "No invented lost revenue"],
    ]);
  });

  it("unpriced and withheld consequences are Unpriced, never zero or cash", async () => {
    for (const state of ["UNPRICED", "WITHHELD"]) {
      const c = { ...ESTIMATED, state, amount: null, tariff_value: null, currency: null, limitation: null };
      expect(grossTariffText(c)).toBe("Unpriced");
      expect(bridgeRows(read({ consequence: c }))[0]).toEqual(["30.000 kWh complete-record delivery", "No eligible tariff applied", "Unpriced", "No collections or profit claim"]);
    }
    expect(grossTariffText(null)).toBe("Unknown");
    renderEnergy(loaded(read({ consequence: { ...ESTIMATED, state: "UNPRICED", amount: null } })));
    await settledScreen();
    expect(cards()[3]).toEqual(["Gross tariff estimate", "Unpriced", "Scenario tariff not established"]);
    expect(main().textContent).not.toContain("0.00 USD");
  });

  it("R346: a read-guard consequence shows the card's metered quantity; a stored null stays Unknown; R06 is labelled", async () => {
    const guard = { ...ESTIMATED, state: "WITHHELD", quantity_kwh: null, amount: null, tariff_value: null, currency: null, limitation: "No stored gross tariff estimate matches the current evidence." };
    expect(bridgeRows(read({ metered_complete_kwh: "15.000", consequence: guard }))[0]).toEqual([
      "15.000 kWh complete-record delivery",
      "No eligible tariff applied",
      "Unpriced",
      "No stored gross tariff estimate matches the current evidence.",
    ]);
    // A stored (non-withheld) consequence with no quantity is a stored unknown.
    expect(bridgeRows(read({ metered_complete_kwh: "15.000", consequence: { ...guard, state: "UNPRICED" } }))[0][0]).toBe("Unknown");
    renderEnergy(loaded(read({ metered_complete_kwh: "15.000", consequence: guard })));
    await settledScreen();
    expect(cards()[0][1]).toContain("15");
    expect(main().textContent).toContain("15.000 kWh complete-record delivery");
    const label = document.querySelector('[data-mock-deviation="R06"]') as HTMLElement;
    expect(label.textContent).toBe("MOCK DEVIATION D1 (R06)");
    expect(label.previousElementSibling?.tagName.toLowerCase()).toBe("figure");
  });

  it("the below-limit answer is red No at or above the limit, green Yes below, neutral Unknown", async () => {
    const tone = (word: string) => document.querySelector('[data-key-value="below"] .badge')?.className.includes(word);
    renderEnergy(loaded(read({ peak_below_limit: "NO" })));
    await settledScreen();
    expect(conclusions()[0]).toEqual(["Observed peak below limit", "No"]);
    expect(tone("ev-tone--red")).toBe(true);
    expect(tone("ev-tone--amber")).toBe(false);
    cleanup();
    renderEnergy(loaded(read({ peak_below_limit: "UNKNOWN" })));
    await settledScreen();
    expect(tone("ev-tone--red") || tone("ev-tone--green") || tone("ev-tone--amber")).toBe(false);
  });

  it("empty samples keep the axes and an empty frame with the honest sentence", async () => {
    renderEnergy(loaded(read({ import_samples: [], import_sample_count: 0, observed_peak_import_kw: null, peak_sample_at: null, peak_below_limit: "UNKNOWN" })));
    await settledScreen();
    expect(document.querySelector("[data-ev-chart]")?.getAttribute("data-ev-chart")).toBe("empty");
    expect(marks()).toHaveLength(0);
    expect(document.querySelector(".ev-depth-graphic__frame")).not.toBeNull();
    expect(document.querySelectorAll("[data-ev-x-tick]")).toHaveLength(7);
    expect(text("[data-ev-samples-empty]")).toBe("No accepted site-import samples in this window.");
    expect(text('[data-ev-measure="peak-time"] td')).toBe("Unknown");
  });

  it.each([
    ["PENDING_RECOMPUTE", "New evidence is being assessed. Earlier selected results may change."],
    ["HISTORICAL", "This result reflects records known at the selected cutoff."],
  ])("%s renders the shared notice below the status line", async (state, sentence) => {
    renderEnergy(loaded(read({}, state)), `?from=${FROM}&to=${TO}&known_at=${KNOWN}`);
    await settledScreen();
    const notice = document.querySelector(`[data-ev-depth-state-notice="${state}"]`) as HTMLElement;
    expect(notice.textContent).toBe(sentence);
    expect(notice.previousElementSibling?.classList.contains("status-strip")).toBe(true);
  });

  it("R244: refusals are plain, keep the strip and tiles, correct a window by link and reload only a 503", async () => {
    renderEnergy({ status: "refused", httpStatus: 422, code: "EV_WINDOW_INVALID", message: "'from' must be before 'to'." }, `?from=${TO}&to=${FROM}`);
    await settledScreen();
    expect(text("[data-panel-gap='ev-depth-refusal']")).toBe("The selected window needs both a start and an end, with the start before the end.");
    expect(main().textContent).not.toContain("EV_WINDOW_INVALID 'from'");
    expect(main().textContent).not.toContain("EV depth unavailable");
    expect(main().textContent).not.toContain("No complete metered delivery");
    expect(Array.from(document.querySelectorAll("[data-ev-refused-card]")).map((n) => n.getAttribute("data-ev-refused-card"))).toEqual([
      "Metered session energy",
      "Observed peak import",
      "Declared site limit",
      "Gross tariff estimate",
    ]);
    expect(document.querySelector("[data-ev-depth-correction]")?.textContent).toBe("Read without a selected window");
    expect(screen.queryByRole("button", { name: /Retry|Reload/ })).toBeNull();
    cleanup();
    const getEnergy = renderEnergy({ status: "refused", httpStatus: 503, code: "EV_UNAVAILABLE", message: null });
    await settledScreen();
    expect(text("[data-ev-strip='refused']")).toContain("Unknown");
    fireEvent.click(screen.getByRole("button", { name: "Reload" }));
    expect(getEnergy).toHaveBeenCalledTimes(2);
    cleanup();
    renderEnergy({ status: "refused", httpStatus: 403, code: "EV_SITE_FORBIDDEN", message: null });
    await settledScreen();
    expect(text("[data-panel-gap='ev-depth-refusal']")).toBe("You do not have access to this EV evidence.");
    expect(screen.queryByRole("button", { name: /Retry|Reload/ })).toBeNull();
  });

  it("R347: the Site tabs open the EV pages and carry the loaded read's own window; a refused read carries none", async () => {
    const tabs = () => Object.fromEntries(Array.from(document.querySelectorAll('nav[aria-label="Site sections"] a')).map((a) => [(a.textContent ?? "").trim(), a.getAttribute("href") ?? ""]));
    renderEnergy(loaded(read({})), `?from=${FROM}&to=${TO}`);
    await settledScreen();
    // The address has no cutoff; the loaded read's `known_at` is the one the tabs carry.
    const carried = `?${new URLSearchParams({ from: FROM, to: TO, known_at: KNOWN }).toString()}`;
    expect(tabs().Overview).toBe(`/sites/${CODE}/ev${carried}`);
    expect(tabs().Evidence).toBe(`/sites/${CODE}/ev/evidence${carried}`);
    expect(tabs().Financials).toBe(`/sites/${CODE}/ev/financials${carried}`);
    cleanup();
    renderEnergy({ status: "refused", httpStatus: 503, code: "EV_UNAVAILABLE", message: null }, `?from=${FROM}&to=${TO}`);
    await settledScreen();
    expect(tabs().Overview).toBe(`/sites/${CODE}/ev`);
    expect(tabs().Evidence).toBe(`/sites/${CODE}/ev/evidence`);
  });

});

describe("W5-03a E3: chart geometry and validator", () => {
  it("derives the Y scale, seven X ticks and 0/1/many marks", () => {
    expect(yMax([], null)).toBe(100);
    expect(yMax([sample(1, t(8, 0), "60")], "80")).toBe(100);
    expect(yMax([sample(1, t(8, 0), "130")], "80")).toBe(150);
    expect(yMax([], "101")).toBe(125);
    const a = Date.parse("2026-10-06T08:00:00.000Z");
    expect(xTicks(a, a + 3_600_000).map((x) => (x - a) / 60_000)).toEqual([0, 10, 20, 30, 40, 50, 60]);
    for (const set of [[], [SAMPLES[1]], SAMPLES]) {
      render(<EvDepthPowerChart from={FROM} to={TO} samples={set} limitKw="80" />);
      expect(marks()).toHaveLength(set.length);
      cleanup();
    }
    render(<EvDepthPowerChart from={FROM} to={TO} samples={[sample(9, t(8, 0), "130")]} limitKw={null} />);
    expect(Array.from(document.querySelectorAll("[data-ev-y-tick] text")).map((x) => x.textContent)).toEqual(["0", "37.5", "75", "112.5", "150"]);
    expect(utcSeconds(null)).toBe("Unknown");
  });

  it("validates the energy DTO including import_samples", () => {
    const good = read();
    expect(isEvEnergyRead(good)).toBe(true);
    expect(isEvEnergyRead({ ...good, energy: { ...good.energy, import_sample_count: 3 } })).toBe(false);
    expect(isEvEnergyRead({ ...good, energy: { ...good.energy, import_samples: [{ ...SAMPLES[0], import_kw: 5 }] } })).toBe(false);
    expect(isEvEnergyRead({ ...good, energy: { ...good.energy, power_constraint_state: "LIMITED" } })).toBe(false);
    expect(isEvEnergyRead({ ...good, energy: { ...good.energy, extra: true } })).toBe(false);
    const { import_samples: _drop, ...without } = good.energy;
    void _drop;
    expect(isEvEnergyRead({ ...good, energy: without })).toBe(false);
  });
});
