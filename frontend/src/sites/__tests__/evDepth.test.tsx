import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import type { EvAssessmentClient, EvRead } from "../evAssessmentClient";
import {
  type AvailabilityConnector,
  type EvAvailabilityRead,
  type EvDepthClient,
  EV_DEPTH_MALFORMED,
  EV_DEPTH_UNREACHABLE,
  createEvDepthClient,
  durationText,
  isEvAvailabilityRead,
} from "../evDepthClient";
import { boundText, connectorHoursText, knownTimeNote, knownTimeText, segmentsOf, instantMs } from "../EvAvailability";
import type { SiteDetailClient, SiteDirectoryClient } from "../siteDirectoryClient";
import type { SiteDetailReadModel } from "../siteReadModel";
import { EMPTY_ANALYTICS_CLIENT } from "./analyticsFixtures";
import { expectPlantedPanelRejected, expectV69Panels } from "../../test/panelStructure";
import { settledScreen } from "../../test/settled";

/*
 * W5-03a E2 (`.agent/W5-03-build-spec.md` E2 card, closure 2 and the pre-flight E2 ruling): an EV_CHARGING Site's
 * Performance/Availability route renders v6.9 `availability` from the selected `ev-depth-1` read. Fixture values
 * follow the E1a producer window `[08:00, 09:00)` (EV-LAB-001, Connector c1/c2), never the mock's illustrations.
 */

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

const CODE = "EV-LAB-001";
const FROM = "2026-10-06T08:00:00.000000Z";
const TO = "2026-10-06T09:00:00.000000Z";
const KNOWN = "2026-10-06T09:00:00.000000Z";
const id = (n: number) => `00000000-0000-4000-8000-${String(n).padStart(12, "0")}`;
const t = (hh: number, mm: number) => `2026-10-06T${String(hh).padStart(2, "0")}:${String(mm).padStart(2, "0")}:00.000000Z`;
const BLOCK = { classification: "REGISTERED_SIMULATION", state: "REGISTERED_SIMULATION", source_ids: [], evidence_ids: [], basis_sha256: null, reasons: [] };

function connector(label: string, asset: number, spans: AvailabilityConnector["spans"]): AvailabilityConnector {
  const sum = (state: string) =>
    spans.filter((s) => s.state === state).reduce((n, s) => n + (instantMs(s.to) - instantMs(s.from)) / 1000, 0);
  const scheduled = spans.reduce((n, s) => n + (instantMs(s.to) - instantMs(s.from)) / 1000, 0);
  return {
    asset_id: id(asset),
    label,
    scheduled_seconds: scheduled,
    known_available_seconds: sum("AVAILABLE"),
    known_unavailable_seconds: sum("UNAVAILABLE"),
    unknown_seconds: sum("UNKNOWN"),
    spans,
  };
}

const C1 = connector("Connector c1", 7, [
  { from: t(8, 0), to: t(8, 20), state: "AVAILABLE", evidence_ids: [id(101)] },
  { from: t(8, 20), to: t(8, 25), state: "UNKNOWN", evidence_ids: [] },
  { from: t(8, 25), to: t(8, 40), state: "UNAVAILABLE", evidence_ids: [id(102)] },
  { from: t(8, 40), to: t(9, 0), state: "AVAILABLE", evidence_ids: [id(103)] },
]);
// Scheduled 08:30-09:00 only: the earlier half hour is outside the denominator and blank.
const C2 = connector("Connector c2", 8, [{ from: t(8, 30), to: t(9, 0), state: "AVAILABLE", evidence_ids: [id(104)] }]);

function read(overrides: Partial<EvAvailabilityRead["availability"]> = {}, state = "CURRENT", rows = [C1, C2]): EvAvailabilityRead {
  const total = (key: keyof AvailabilityConnector) => rows.reduce((n, r) => n + (r[key] as number), 0);
  const available = total("known_available_seconds");
  const unavailable = total("known_unavailable_seconds");
  const unknown = total("unknown_seconds");
  const scheduled = total("scheduled_seconds");
  const r6 = (x: number) => x.toFixed(6);
  return {
    schema_version: "ev-depth-1",
    site_id: id(1),
    window: { from: FROM, to: TO, known_at: KNOWN, committed_watermark: KNOWN },
    selection: {
      state: state as EvAvailabilityRead["selection"]["state"],
      assessment_revision_id: id(50),
      session_revision_ids: [id(60)],
      accepted_evidence_ids: [id(101), id(102), id(103), id(104)],
      source_provenance: BLOCK,
    },
    availability: {
      calculation_version: "ev-availability/1",
      schedule_state: "SCHEDULED",
      scheduled_seconds: scheduled,
      known_available_seconds: available,
      known_unavailable_seconds: unavailable,
      unknown_seconds: unknown,
      known_time_ratio: available + unavailable > 0 ? r6(available / (available + unavailable)) : null,
      full_lower: scheduled > 0 ? r6(available / scheduled) : null,
      full_upper: scheduled > 0 ? r6((available + unknown) / scheduled) : null,
      connectors: rows,
      ...overrides,
    },
    links: {
      sessions: `/api/sites/${CODE}/ev/sessions?from=${FROM}&to=${TO}&known_at=${KNOWN}`,
      evidence_analysis: `/api/sites/${CODE}/ev/evidence/analysis?from=${FROM}&to=${TO}&known_at=${KNOWN}`,
      financials: `/api/sites/${CODE}/ev/financials?from=${FROM}&to=${TO}&known_at=${KNOWN}`,
    },
  };
}

const NULLS = {
  schedule_state: "NOT_ESTABLISHED" as const,
  scheduled_seconds: null,
  known_available_seconds: null,
  known_unavailable_seconds: null,
  unknown_seconds: null,
  known_time_ratio: null,
  full_lower: null,
  full_upper: null,
};

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
const never = <T,>(): Promise<EvRead<T>> => new Promise(() => undefined);
const evAssessment: EvAssessmentClient = { listSessions: never, getSession: never, listFindings: never, getFinding: never };

type Answer = Awaited<ReturnType<EvDepthClient["getAvailability"]>>;

function renderAvailability(answer: Answer | (() => Promise<Answer>), query = `?from=${FROM}&to=${TO}`) {
  const getAvailability = vi.fn(typeof answer === "function" ? answer : () => Promise.resolve(answer));
  const depth: EvDepthClient = { getAvailability, getEnergy: vi.fn(), getHealth: vi.fn() };
  render(
    <MemoryRouter initialEntries={[`/sites/${CODE}/performance/availability${query}`]}>
      <App flags={featureFlagsWith(false)} siteDirectory={directory} siteDetail={detail} siteAnalytics={EMPTY_ANALYTICS_CLIENT} evAssessment={evAssessment} evDepth={depth} />
    </MemoryRouter>,
  );
  return getAvailability;
}

const loaded = (value: EvAvailabilityRead): Answer => ({ status: "loaded", value });
const main = () => document.querySelector("main") as HTMLElement;
const cards = () => Array.from(document.querySelectorAll("[data-ev-availability-card]")).map((c) => [
  c.querySelector(".v69-metric__label")?.textContent,
  c.querySelector(".v69-metric__value")?.textContent,
  c.querySelector(".v69-metric__note")?.textContent,
]);
const segments = (asset: number) =>
  Array.from(document.querySelectorAll(`[data-ev-bar-row="${id(asset)}"] [data-ev-segment]`)).map((s) => [
    s.getAttribute("data-ev-segment"),
    (s as HTMLElement).style.width,
  ]);
const text = (selector: string) => document.querySelector(selector)?.textContent ?? null;

describe("W5-03a E2: EV Availability", () => {
  it("availability_states_bars_loading", async () => {
    let resolve: (value: Answer) => void = () => undefined;
    renderAvailability(() => new Promise<Answer>((r) => (resolve = r)));
    expect(await screen.findByText("Loading the site's connector availability.")).toBeTruthy();
    expect((await screen.findByText("Loading the site's connector availability.")).className).toBe("prose");
    resolve(loaded(read()));
    await settledScreen();
    expect(main().getAttribute("data-ev-view")).toBe("availability");
    expectV69Panels("availability");
    expectPlantedPanelRejected("availability");
    // Heading = Site name; breadcrumb Sites › Site › Performance (linked); subtitle from SITE_SCREEN_DESCRIPTIONS.
    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("EV lab depot");
    const crumbs = Array.from(document.querySelectorAll(".breadcrumbs a, nav[aria-label='Breadcrumb'] a")).map((a) => [a.textContent, a.getAttribute("href")]);
    expect(crumbs).toContainEqual(["Performance", `/sites/${CODE}/performance`]);
    expect(main().textContent).toContain("Performance · connector availability and unknown time");
    // Subtabs: Availability selected and live (E3 also made Energy / site power live: no inert entry remains).
    const tab = document.querySelector('[data-performance-subtab="availability"]') as HTMLElement;
    expect(tab.getAttribute("aria-current")).toBe("page");
    expect(document.querySelector('[data-performance-subtab="sessions"]')?.hasAttribute("aria-current")).toBe(false);
    expect(document.querySelector('[data-performance-subtab="energy"]')?.hasAttribute("aria-current")).toBe(false);
    expect(document.querySelectorAll("[data-tab-unavailable]")).toHaveLength(0);
    expect(document.querySelector('[data-tab-unavailable="Availability"]')).toBeNull();
    // Status always Evidence limited; muted text from the selected (differing) schedules.
    expect(text(".status-strip")).toContain("Evidence limited");
    expect(text("[data-ev-connector-hours]")).toBe("1.5 scheduled connector-hours across 2 connectors");
    expect(document.querySelector("[data-ev-depth-state-notice]")).toBeNull();
    // Cards: the four mock labels and notes, durations `{h} h {m} min`, known-time one decimal.
    expect(cards()).toEqual([
      ["Known available", "1.17 connector-h", "State-supported service time"],
      ["Known unavailable", "0.25 connector-h", "Faulted or unavailable state evidenced"],
      ["Unknown", "0.08 connector-h", "No trustworthy state coverage"],
      ["Known-time availability", "82.4%", "1.17 / 1.42 known hours; coverage 94.44%"],
    ]);
    // R345: the exact `X h Y min` stays in the card's title.
    expect(Array.from(document.querySelectorAll("[data-ev-connector-h]")).map((n) => n.getAttribute("title"))).toEqual(["1 h 10 min", "15 min", "5 min"]);
    // Bars: one segment per ordered span, window aligned, blank outside the schedule, never collapsed.
    expect(segments(7)).toEqual([
      ["AVAILABLE", `${(20 / 60) * 100}%`],
      ["UNKNOWN", `${(5 / 60) * 100}%`],
      ["UNAVAILABLE", `${(15 / 60) * 100}%`],
      ["AVAILABLE", `${(20 / 60) * 100}%`],
    ]);
    expect(segments(8)).toEqual([["OUTSIDE", "50%"], ["AVAILABLE", "50%"]]);
    const blank = document.querySelector(`[data-ev-bar-row="${id(8)}"] [data-ev-segment="OUTSIDE"]`) as HTMLElement;
    expect(blank.getAttribute("aria-label")).toBe("Outside scheduled service hours");
    expect(Array.from(document.querySelectorAll("[data-ev-bar-times] span")).map((s) => s.textContent)).toEqual(["08:00 UTC", "08:30 UTC", "09:00 UTC"]);
    expect(Array.from(document.querySelectorAll(".ev-depth-bars__period")).map((s) => s.textContent)).toEqual(["08:00–09:00 UTC", "08:30–09:00 UTC"]);
    // H1/H2: global chart-note and panel-value classes; labels use the selected name verbatim.
    expect(document.querySelector(`[data-ev-chart-note="${id(7)}"]`)?.classList.contains("v69-chart-note")).toBe(true);
    expect(document.querySelector("[data-ev-bound]")?.classList.contains("v69-panel-value")).toBe(true);
    expect(Array.from(document.querySelectorAll(".ev-depth-bars__label")).map((s) => s.textContent)).toEqual(["Connector c1", "Connector c2"]);
    expect(Array.from(document.querySelectorAll(".ev-depth-legend .badge")).map((b) => b.textContent)).toEqual(["Available", "Unavailable", "Unknown"]);
    expect(text(`[data-ev-span-summary="${id(7)}"]`)).toContain("08:20–08:25 UTC Unknown");
    expect(text(`[data-ev-chart-note="${id(7)}"]`)).toBe(
      "Connector c1: 0.67 h available, 0.25 h observed unavailable and 0.08 h unknown. Spans use accepted transition timestamps.",
    );
    // Bound: two decimals; prose uses selected durations.
    expect(text("[data-ev-bound]")).toBe("77.78–83.33%");
    expect(text("[data-ev-bound-prose]")).toBe(
      "Lower bound: 1.17 / 1.5 hours. Upper bound: (1.17 + 0.08 unknown) / 1.5. Unknown time is not silently included as available.",
    );
    expect(text("[data-ev-next-evidence]")).toBe(
      "Recover the connector status/heartbeat history for the missing 0.08 hours. A telemetry outage does not prove the charging connector was physically unavailable.",
    );
    // Lineage link: the EV Evidence Analysis UI path with the read window; no dead link anywhere.
    expect(document.querySelector("[data-ev-lineage]")?.getAttribute("href")).toBe(
      `/sites/${CODE}/ev/evidence/analysis?from=${encodeURIComponent(FROM)}&to=${encodeURIComponent(TO)}&known_at=${encodeURIComponent(KNOWN)}`,
    );
    for (const a of Array.from(main().querySelectorAll("a"))) expect(a.getAttribute("href")).toMatch(/^\/sites(\/|$)/);
    for (const literal of ["93.75", "16 connector-hours", "08:00–16:00", "12:00"]) expect(main().textContent).not.toContain(literal);
  });

  it("schedule only never shows a ratio; session-only selection never proves availability", async () => {
    const unknownOnly = connector("Connector c1", 7, [{ from: t(8, 0), to: t(9, 0), state: "UNKNOWN", evidence_ids: [] }]);
    renderAvailability(loaded(read({}, "CURRENT", [unknownOnly])));
    await settledScreen();
    expect(cards().map((c) => c[1])).toEqual(["0 connector-h", "0 connector-h", "1 connector-h", "Unknown"]);
    expect(text("[data-ev-availability-empty]")).toBe("No trustworthy connector-state spans in the selected schedule.");
    expect(text("[data-ev-bound]")).toBe("0.00–100.00%");
    // Ruling 2: exactly one hour is singular, and the prose bounds are hour numbers.
    expect(text("[data-ev-next-evidence]")).toContain("for the missing 1 hour. A telemetry");
    expect(text("[data-ev-bound-prose]")).toBe("Lower bound: 0 / 1 hours. Upper bound: (0 + 1 unknown) / 1. Unknown time is not silently included as available.");
    cleanup();
    // Ruling 1: a scheduled window with no unknown time shows only the telemetry sentence.
    const known = connector("Connector c1", 7, [{ from: t(8, 0), to: t(9, 0), state: "AVAILABLE", evidence_ids: [id(101)] }]);
    renderAvailability(loaded(read({}, "CURRENT", [known])));
    await settledScreen();
    expect(text("[data-ev-next-evidence]")).toBe("A telemetry outage does not prove the charging connector was physically unavailable.");
    expect(main().textContent).not.toContain("Recover the connector");
    expect(text("[data-ev-connector-hours]")).toBe("1 connector × 1 scheduled hour = 1 connector-hour");
  });

  it("not established and declared-empty schedules draw no bars and no rates", async () => {
    renderAvailability(loaded(read({ ...NULLS, connectors: [] })));
    await settledScreen();
    expect(text("[data-ev-schedule-state]")).toBe("Service schedule not established for this window.");
    expect(document.querySelector("[data-ev-bars]")).toBeNull();
    expect(cards().map((c) => c[1])).toEqual(["Unknown", "Unknown", "Unknown", "Unknown"]);
    expect(text("[data-ev-bound]")).toBe("Unknown");
    expect(document.querySelector("[data-ev-bound]")?.classList.contains("v69-panel-value")).toBe(true);
    expect(text("[data-ev-bound-prose]")).toBe("Lower bound: Unknown. Upper bound: Unknown. Unknown time is not silently included as available.");
    expect(text("[data-ev-next-evidence]")).toBe(
      "Establish the connector service schedule before assessing availability. A telemetry outage does not prove the charging connector was physically unavailable.",
    );
    expect(cards()[3][2]).toBe("Known hours and coverage unknown");
    expect(text("[data-ev-connector-hours]")).toBe("Scheduled connector-hours unknown");
    cleanup();
    const empty = (label: string, asset: number) => ({ ...connector(label, asset, []), scheduled_seconds: 0 });
    renderAvailability(
      loaded(read({ schedule_state: "DECLARED_EMPTY", known_time_ratio: null, full_lower: null, full_upper: null }, "CURRENT", [empty("Connector c1", 7), empty("Connector c2", 8)])),
    );
    await settledScreen();
    expect(text("[data-ev-schedule-state]")).toBe("No service hours are declared in this window.");
    expect(document.querySelector("[data-ev-bars]")).toBeNull();
    expect(cards().map((c) => c[1])).toEqual(["0 connector-h", "0 connector-h", "0 connector-h", "Unknown"]);
    expect(text("[data-ev-bound]")).toBe("Unknown");
    expect(cards()[3][2]).toBe("0 / 0 known hours; coverage not applicable");
    expect(text("[data-ev-next-evidence]")).toBe(
      "Declare service hours before assessing connector availability. A telemetry outage does not prove the charging connector was physically unavailable.",
    );
    expect(main().textContent).not.toContain("any unknown scheduled time");
    cleanup();
    // A scheduled window with no selected connector gives the muted no-data chart note; a bare label gains the prefix once.
    renderAvailability(loaded(read({ schedule_state: "SCHEDULED", scheduled_seconds: 3600, known_available_seconds: 0, known_unavailable_seconds: 0, unknown_seconds: 3600 }, "CURRENT", [])));
    await settledScreen();
    expect(text("[data-ev-no-connector]")).toBe("No selected connector has a service schedule in this window.");
    expect(document.querySelector("[data-ev-no-connector]")?.classList.contains("v69-chart-note")).toBe(true);
    cleanup();
    const bare = connector("1", 9, [{ from: t(8, 0), to: t(9, 0), state: "AVAILABLE", evidence_ids: [id(105)] }]);
    renderAvailability(loaded(read({}, "CURRENT", [bare])));
    await settledScreen();
    expect(text(".ev-depth-bars__label")).toBe("Connector 1");
    expect(text(`[data-ev-chart-note="${id(9)}"]`)).toContain("Connector 1: ");
  });

  it.each([
    ["PENDING_RECOMPUTE", "New evidence is being assessed. Earlier selected results may change."],
    ["HISTORICAL", "This result reflects records known at the selected cutoff."],
    ["STALE_SOURCE", "Selected source records are stale for this window."],
    ["UNKNOWN", "No selected EV session assessment covers this window yet."],
  ])("%s renders the shared amber notice below the status line", async (state, sentence) => {
    renderAvailability(loaded(read({}, state)), `?from=${FROM}&to=${TO}&known_at=${KNOWN}`);
    await settledScreen();
    const notice = document.querySelector(`[data-ev-depth-state-notice="${state}"]`) as HTMLElement;
    expect(notice.textContent).toBe(sentence);
    expect(notice.previousElementSibling?.classList.contains("status-strip")).toBe(true);
    expect(text(".status-strip")).toContain("Evidence limited");
  });

  it.each([
    ["EV_WINDOW_INVALID", 422, "The selected window needs both a start and an end, with the start before the end.", true],
    ["EV_WINDOW_TOO_LONG", 422, "The selected window is longer than 31 days.", true],
    ["EV_SITE_FORBIDDEN", 403, "You do not have access to this EV evidence.", false],
    ["EV_SITE_NOT_FOUND", 404, "This EV Site or record was not found.", false],
    ["EV_UNAVAILABLE", 503, "EV evidence is temporarily unavailable. Retry.", false],
  ])("R244: %s (%i) is plain, keeps the strip and tiles, and offers only what applies", async (code, httpStatus, sentence, windowRefusal) => {
    renderAvailability({ status: "refused", httpStatus, code, message: "raw server text" }, `?from=${TO}&to=${FROM}&known_at=${KNOWN}`);
    await settledScreen();
    expect(text("[data-panel-gap='ev-depth-refusal']")).toBe(sentence);
    expect(document.querySelectorAll("[role='alert']")).toHaveLength(1);
    expect(main().textContent).not.toContain(code === "EV_WINDOW_INVALID" ? "raw server text" : "EV depth unavailable");
    expect(document.querySelector("[data-page-refusal] .page-refusal__title")).toBeNull();
    expect(text("[data-ev-strip='refused']")).toContain(windowRefusal ? "Window cannot be read" : "Unknown");
    expect(Array.from(document.querySelectorAll("[data-ev-refused-card]")).map((n) => n.getAttribute("data-ev-refused-card"))).toEqual([
      "Known available",
      "Known unavailable",
      "Unknown",
      "Known-time availability",
    ]);
    expect(document.querySelector("[data-ev-window-requested]") !== null).toBe(!windowRefusal);
    const link = document.querySelector("[data-ev-depth-correction]");
    expect(link === null).toBe(!windowRefusal);
    if (link !== null) {
      expect(link.textContent).toBe("Read without a selected window");
      expect(link.getAttribute("href")).toBe(`/sites/${CODE}/performance/availability?known_at=${encodeURIComponent(KNOWN)}`);
    }
    expect(screen.queryByRole("button", { name: "Retry" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Reload" }) !== null).toBe(httpStatus === 503);
    // The raw code lives only in the technical disclosure.
    expect(document.querySelector("[data-disclosure='ev-refusal-detail']")?.textContent ?? "").toContain(code);
  });

  it("R244: a one-sided window is a window refusal; Reload repeats the same read; an unreachable read reloads", async () => {
    const getAvailability = renderAvailability({ status: "refused", httpStatus: 503, code: "EV_UNAVAILABLE", message: null }, `?from=${FROM}`);
    await settledScreen();
    fireEvent.click(screen.getByRole("button", { name: "Reload" }));
    expect(getAvailability).toHaveBeenCalledTimes(2);
    expect(getAvailability.mock.calls[1]).toEqual(getAvailability.mock.calls[0]);
    cleanup();
    renderAvailability({ status: "refused", httpStatus: 422, code: "EV_WINDOW_INVALID", message: null }, `?from=${FROM}`);
    await settledScreen();
    expect(document.querySelector("[data-ev-depth-correction]")?.getAttribute("href")).toBe(`/sites/${CODE}/performance/availability`);
    cleanup();
    renderAvailability({ status: "unavailable", message: EV_DEPTH_MALFORMED });
    await settledScreen();
    expect(text("[data-panel-gap='ev-depth-refusal']")).toBe("EV evidence is temporarily unavailable. Retry.");
    expect(screen.getByRole("button", { name: "Reload" })).toBeTruthy();
  });
});

describe("W5-03a E2: evDepthClient", () => {
  it("validates the exact ev-depth-1 availability shape and refuses malformed 200s", async () => {
    const good = read();
    expect(isEvAvailabilityRead(good)).toBe(true);
    expect(isEvAvailabilityRead({ ...good, extra: 1 })).toBe(false);
    expect(isEvAvailabilityRead({ ...good, schema_version: "ev-depth-2" })).toBe(false);
    expect(isEvAvailabilityRead({ ...good, availability: { ...good.availability, schedule_state: "SOMETIMES" } })).toBe(false);
    expect(isEvAvailabilityRead({ ...good, availability: { ...good.availability, known_time_ratio: 0.5 } })).toBe(false);
    const badSpan = { ...C1, spans: [{ ...C1.spans[0], state: "HEALTHY" }] };
    expect(isEvAvailabilityRead({ ...good, availability: { ...good.availability, connectors: [badSpan] } })).toBe(false);
    expect(isEvAvailabilityRead({ ...good, selection: { ...good.selection, state: "FRESH" } })).toBe(false);
    const calls: string[] = [];
    vi.stubGlobal("fetch", vi.fn((url: string) => {
      calls.push(url);
      return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({ ...good, links: {} }) });
    }));
    const client = createEvDepthClient("/api/sites");
    expect(await client.getAvailability(CODE, { from: FROM, to: TO, known_at: null })).toEqual({ status: "unavailable", message: EV_DEPTH_MALFORMED });
    expect(calls[0]).toBe(`/api/sites/${CODE}/ev/availability?from=${encodeURIComponent(FROM)}&to=${encodeURIComponent(TO)}`);
    vi.stubGlobal("fetch", vi.fn(() => Promise.reject(new Error("down"))));
    expect(await client.getAvailability(CODE, { from: null, to: null, known_at: null })).toEqual({ status: "unavailable", message: EV_DEPTH_UNREACHABLE });
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve({ ok: false, status: 403, json: () => Promise.resolve({ error: { code: "SITE_SCOPE_FORBIDDEN", message: "No" } }) })));
    expect(await client.getAvailability(CODE, { from: null, to: null, known_at: null })).toEqual({ status: "refused", httpStatus: 403, code: "SITE_SCOPE_FORBIDDEN", message: "No" });
  });

  it("formats durations, percentages and segments exactly", () => {
    expect([0, 59, 60, 3599, 3600, 5400, 7261].map(durationText)).toEqual(["0 min", "0 min", "1 min", "59 min", "1 h 0 min", "1 h 30 min", "2 h 1 min"]);
    expect(knownTimeText("0.933333")).toBe("93.3%");
    expect(knownTimeText(null)).toBe("Unknown");
    expect(boundText("0.875000", "0.937500")).toBe("87.50–93.75%");
    expect(boundText(null, "0.5")).toBe("Unknown");
    const r = read();
    expect(knownTimeNote(r)).toBe("1.17 / 1.42 known hours; coverage 94.44%");
    expect(connectorHoursText(read({}, "CURRENT", [C1, { ...C1, asset_id: id(9) }]))).toBe("2 connectors × 1 scheduled hour = 2 connector-hours");
    // R345: counts and units agree for 0/1/2 connectors and for 1 vs 1.5 vs 8 hours.
    expect(connectorHoursText(read({}, "CURRENT", [C1]))).toBe("1 connector × 1 scheduled hour = 1 connector-hour");
    expect(connectorHoursText(read({}, "CURRENT", []))).toMatch(/^0 connectors|across 0 connectors$/);
    expect(connectorHoursText(read({ scheduled_seconds: 5400 }, "CURRENT", [C1, { ...C1, asset_id: id(9), scheduled_seconds: 1800 }]))).toBe("1.5 scheduled connector-hours across 2 connectors");
    expect(connectorHoursText(read({ scheduled_seconds: 3600 }, "CURRENT", [C1, { ...C1, asset_id: id(9), scheduled_seconds: 0 }]))).toBe("1 scheduled connector-hour across 2 connectors");
    const seg = segmentsOf(C2, instantMs(FROM), instantMs(TO));
    expect(seg.map((s) => [s.state, s.width])).toEqual([["OUTSIDE", 50], ["AVAILABLE", 50]]);
    // Conservation: the three totals equal the scheduled seconds at connector and Site level.
    for (const row of r.availability.connectors) {
      expect((row.known_available_seconds ?? 0) + (row.known_unavailable_seconds ?? 0) + (row.unknown_seconds ?? 0)).toBe(row.scheduled_seconds);
    }
    const a = r.availability;
    expect((a.known_available_seconds ?? 0) + (a.known_unavailable_seconds ?? 0) + (a.unknown_seconds ?? 0)).toBe(a.scheduled_seconds);
  });
});

describe("W5-03a E2: DataTable stickyFirstColumn", () => {
  it("is opt-in and keeps the named region keyboard scrollable", async () => {
    const { DataTable } = await import("../../ui/DataTable");
    render(
      <>
        <h2 id="t-sticky">Sticky</h2>
        <DataTable labelledBy="t-sticky" stickyFirstColumn>
          <tbody><tr><th scope="row">A</th><td>B</td></tr></tbody>
        </DataTable>
        <h2 id="t-plain">Plain</h2>
        <DataTable labelledBy="t-plain">
          <tbody><tr><th scope="row">A</th><td>B</td></tr></tbody>
        </DataTable>
      </>,
    );
    const [sticky, plain] = Array.from(document.querySelectorAll(".data-table__scroll")) as HTMLElement[];
    expect(sticky.className).toBe("data-table__scroll data-table__scroll--sticky");
    expect(plain.className).toBe("data-table__scroll");
    for (const region of [sticky, plain]) {
      expect(region.getAttribute("role")).toBe("region");
      expect(region.tabIndex).toBe(0);
      region.focus();
      expect(document.activeElement).toBe(region);
    }
  });
});
