import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import type { MiniDepthClient, MiniHourState, MiniRead, RenewableRead, RenewableRow } from "../miniDepthClient";
import { localDaysWindow, renewableWindowFromParams } from "../miniDepthClient";
import type { SiteDetailClient, SiteDirectoryClient } from "../siteDirectoryClient";
import type { SiteDetailReadModel } from "../siteReadModel";
import { EMPTY_ANALYTICS_CLIENT } from "./analyticsFixtures";
import { expectPlantedPanelRejected, expectV69Panels, panelTitled } from "../../test/panelStructure";
import { settledScreen } from "../../test/settled";

/*
 * W4-02 unit 6: a MINIGRID Site's Performance/Renewable route renders the v69 `renewable` panels from the q9
 * public read (build spec "Run 9 rulings (q9) and pages dry-read"), with the retained-margin gap (q9-7), the
 * not-assessed day rows (q9-6), the Dispatch link or its Unavailable state (q9-8) and the refusal states.
 */

afterEach(cleanup);

const CODE = "MG-W402-001";
const TZ = "Africa/Addis_Ababa";
const id = (n: number) => `00000000-0000-4000-8000-${String(n).padStart(12, "0")}`;
const SELECTED = { classification: "REGISTERED_SIMULATION", source_ids: [id(2)], evidence_ids: [id(100)] };

function hour(day: string, selected: boolean, n = 1): MiniHourState {
  // Site-local 12:00-13:00 at UTC+03:00.
  return {
    local_day: day,
    window_start: `${day}T09:00:00Z`,
    window_end: `${day}T10:00:00Z`,
    selection_id: selected ? n : null,
    assessment_revision_id: selected ? id(500 + n) : null,
    input_sha256: selected ? "a".repeat(64) : null,
    committed_watermark: null,
    state: selected ? "CURRENT" : "UNKNOWN",
    job_state: selected ? "SETTLED" : "NONE",
  };
}

function row(day: string, over: Partial<RenewableRow> = {}): RenewableRow {
  return {
    day,
    from: `${day}T09:00:00Z`,
    to: `${day}T10:00:00Z`,
    opportunity_kwh: { low: 18, high: 20 },
    constraints: [],
    decision: "ELIGIBLE",
    coverage: { required_seconds: 3600, observed_seconds: 3600, source_count: 2, gaps: [] },
    evidence_ids: [id(100), id(101)],
    ...over,
  };
}

function read(over: Partial<RenewableRead> = {}): RenewableRead {
  return {
    schema_version: "w4-02.mini.v1",
    domain: "renewable",
    site: { id: id(1), code: CODE, timezone: TZ },
    window: { from: "2026-10-05T21:00:00Z", to: "2026-10-06T21:00:00Z", known_at: "2026-10-07T00:00:00Z", bounds: "[from,to)" },
    currentness: { state: "CURRENT", job_state: "SETTLED", windows: [hour("2026-10-06", true)] },
    source_provenance: SELECTED,
    selected_source_provenance: SELECTED,
    pending_source_provenance: null,
    status: "SUPPORTED",
    coverage: { required_seconds: 3600, observed_seconds: 3600, source_count: 2, gaps: [] },
    cards: {
      capability_kw: { low: 41, high: 43 },
      used_kw: { low: 20, high: 20 },
      headroom_kw: { low: 18, high: 20 },
      eligible_days: 1,
      assessed_days: 1,
    },
    rows: [row("2026-10-06")],
    limitations: [],
    basis: null,
    links: {
      dispatch: `/sites/${CODE}/performance/dispatch?day=2026-10-06`,
      evidence: `/sites/${CODE}/evidence`,
      financials: null,
      actions: "/actions",
    },
    ...over,
  };
}

const SITE = {
  site_id: CODE,
  display_name: "W4-02 mini-grid",
  site_type: "MINIGRID",
  location: { country: "Ethiopia", locality: "Addis Ababa" },
  timezone: TZ,
  lifecycle_status: "PLANNED",
  origin: "USER",
  source: { mode: "SIMULATED" },
  template: null,
  configuration_store: "POSTGRES",
} as unknown as SiteDetailReadModel;
const detail: SiteDetailClient = { getSite: () => Promise.resolve({ status: "loaded", site: SITE }) };
const directory: SiteDirectoryClient = { listSites: () => Promise.resolve({ status: "loaded", sites: [SITE] }) };

const CAPS = [
  { id: "service", display_name: "Service" },
  { id: "fuel", display_name: "Fuel" },
  { id: "renewable", display_name: "Renewable" },
  { id: "backup", display_name: "Backup" },
];

function renderRenewable(answers: MiniRead<RenewableRead>[], path = `/sites/${CODE}/performance/renewable?date=2026-10-06`) {
  const queue = [...answers];
  const client: MiniDepthClient = {
    getCapabilities: vi.fn(() => Promise.resolve({ status: "loaded" as const, value: CAPS })),
    getRenewable: vi.fn(() => Promise.resolve(queue.length > 1 ? queue.shift()! : queue[0])),
    getService: vi.fn(() => Promise.resolve({ status: "unavailable" as const, message: null })),
    getFuel: vi.fn(() => Promise.resolve({ status: "unavailable" as const, message: null })),
    getBackup: vi.fn(() => Promise.resolve({ status: "unavailable" as const, message: null })),
  };
  render(
    <MemoryRouter initialEntries={[path]}>
      <App flags={featureFlagsWith(false)} siteDirectory={directory} siteDetail={detail} siteAnalytics={EMPTY_ANALYTICS_CLIENT} miniDepth={client} />
    </MemoryRouter>,
  );
  return client;
}

const ok = (value: RenewableRead): MiniRead<RenewableRead> => ({ status: "loaded", value });
const main = () => document.querySelector("main") as HTMLElement;
const strip = () => (document.querySelector(".status-strip") as HTMLElement).textContent ?? "";
const cardValues = () => Array.from(document.querySelectorAll("[data-mini-cards] .v69-metric__value")).map((x) => x.textContent);
const subtabs = () =>
  Array.from(document.querySelectorAll('nav[aria-label="Performance sections"] li')).map((li) => [
    li.textContent,
    li.querySelector("a")?.getAttribute("aria-current") ?? (li.querySelector("a") === null ? "inert" : null),
  ]);

describe("W4-02 unit 6: renewable keeps the v69 panels, strip, cards and table", () => {
  it("supported positive headroom: Watch, exact cards, margin gap, Dispatch link and tab order", async () => {
    const client = renderRenewable([ok(read())]);
    await settledScreen();
    await screen.findByText("Watch");
    expectV69Panels("renewable");
    expectPlantedPanelRejected("renewable");
    expect(subtabs()).toEqual([
      // S6 order over the built pages; backup joins when its page lands.
      ["Service", null],
      ["Dispatch", null],
      ["Fuel", null],
      ["Renewable", "page"],
      ["Backup", null],
    ]);
    // Q5: the local date of the shell's UTC day, sent as site-local midnight bounds in UTC.
    expect(client.getRenewable).toHaveBeenCalledWith(CODE, {
      from: "2026-10-05T21:00:00.000Z",
      to: "2026-10-06T21:00:00.000Z",
      known_at: null,
    });
    expect(main().textContent).toContain("Assess measured solar headroom and its limits.");
    expect(strip()).toContain("Lens: Opportunity");
    expect(strip()).toContain("Selected sources: Generated test data, not field readings");
    // post-W6 W4 R312: one assessed day does not establish recurrence (five completely assessed days are needed).
    expect(strip()).toContain("Recurrence is not established for this selection.");
    const dispatch = document.querySelector("[data-mini-dispatch-link] a") as HTMLAnchorElement;
    expect(dispatch.getAttribute("href")).toBe(`/sites/${CODE}/performance/dispatch?day=2026-10-06`);
    expect(cardValues()).toEqual(["41–43 kW", "20 kW", "18–20 kW", "Not established"]);
    expect(main().textContent).toContain("Accepted power over 60/60 min");
    const headroom = panelTitled("From physical headroom to an opportunity");
    expect(headroom.textContent).toContain("Actual accepted interval means cover each eligible one-hour window");
    expect(headroom.textContent).toContain(
      "Retained margin: Unknown. The retained-margin value is not available in this read; inspect the pinned Foundation basis before using this breakdown.",
    );
    expect(headroom.querySelector('[data-value-bar-key="margin"]')?.getAttribute("data-value-bar")).toBe("not-known");
    // Final review L1: the hatched Retained margin bar says `Unknown`, never "not known".
    expect(headroom.querySelector('[data-value-bar-key="margin"] .value-bars__value')?.textContent).toBe("Unknown");
    expect(headroom.textContent).toContain("Maximum sources in one assessed hour: 2");
    expect(headroom.textContent).not.toMatch(/(?<![\d.])3 kW/);
    const productive = panelTitled("Productive-use evaluation");
    expect(productive.textContent).toContain("No productive-use scenario has been assessed.");
    expect(productive.textContent).toContain("Electrical capacity does not establish customer demand.");
    // W4-03 unit 7 (S14): a one-day selection makes no opportunity lookup and states the shorter-study copy.
    expect(productive.querySelector('[data-opportunity-decision="short"]')?.textContent).toBe(
      "Opportunity decision unavailable for fewer than five assessed days.",
    );
    const cells = Array.from(document.querySelectorAll("tbody tr")[0].querySelectorAll("td")).map((td) => td.textContent);
    expect(cells[0]).toBe("2026-10-06 · 12:00–13:00");
    expect(cells[1]).toBe("18–20 kWh");
    expect(cells[2]).toContain("All required evidence present");
    expect(cells[3]).toBe("Eligible");
    expect(main().textContent).toContain("Recurrence is not established for this selection.");
    expect(document.querySelector("[data-mini-notice]")?.textContent).toContain("Opportunity is an evidence-backed capacity estimate.");
    expect(main().textContent).not.toMatch(/grain mill|\$|tariff of/i);
  });

  it("missing middle day and a limited hour: Evidence limited, a Not assessed row and no Dispatch link", async () => {
    const limited = read({
      status: "LIMITED",
      window: { from: "2026-10-05T21:00:00Z", to: "2026-10-08T21:00:00Z", known_at: null, bounds: "[from,to)" },
      currentness: {
        state: "UNKNOWN",
        job_state: "NONE",
        windows: [hour("2026-10-06", true, 1), hour("2026-10-07", false), hour("2026-10-08", true, 3)],
      },
      coverage: { required_seconds: 10800, observed_seconds: 5400, source_count: 2, gaps: [{ from: "2026-10-07T09:00:00Z", to: "2026-10-07T10:00:00Z" }] },
      cards: { capability_kw: null, used_kw: null, headroom_kw: { low: 18, high: 20 }, eligible_days: 1, assessed_days: 1 },
      rows: [
        row("2026-10-06"),
        row("2026-10-08", { decision: "LIMITED", opportunity_kwh: null, constraints: ["CRITICAL_SERVICE_MISSING"], evidence_ids: [id(102)] }),
      ],
      limitations: [{ code: "CRITICAL_SERVICE_MISSING", evidence_ids: [id(102)] }],
      links: { dispatch: null, evidence: `/sites/${CODE}/evidence`, financials: null, actions: "/actions" },
    });
    renderRenewable([ok(limited)], `/sites/${CODE}/performance/renewable?from=2026-10-05T21:00:00Z&to=2026-10-08T21:00:00Z`);
    await settledScreen();
    await screen.findByText("Evidence limited");
    expectV69Panels("renewable");
    // q12-7: the ordered limitations sit behind the closed strip disclosure (count line visible).
    expect(document.querySelector("[data-mini-limitations]")).not.toHaveAttribute("open");
    expect(document.querySelector("[data-mini-limitations] summary")?.textContent).toMatch(/^(Limited by \d+ conditions?|Outage-chain assessment: evidence limited)$/);
    expect(Array.from(document.querySelectorAll("[data-mini-limitations] li"), (li) => li.textContent).join("; ")).toContain("Critical service not established");
    expect(strip()).toContain("Compare with Dispatch evidence · Not available yet");
    expect(document.querySelector("[data-mini-dispatch-link] a")).toBeNull();
    expect(cardValues()).toEqual(["Unknown", "Unknown", "18–20 kW", "Not established"]);
    expect(panelTitled("From physical headroom to an opportunity").textContent).toContain("Accepted coverage is incomplete");
    expect(Array.from(document.querySelectorAll("tbody tr")).map((tr) => tr.getAttribute("data-mini-row"))).toEqual([
      "assessed",
      "not-assessed",
      "assessed",
    ]);
    const missing = Array.from(document.querySelectorAll("tbody tr")[1].querySelectorAll("td")).map((td) => td.textContent);
    expect(missing).toEqual(["2026-10-07 · 12:00–13:00", "—", "No selected assessment for this hour", "Not assessed"]);
    const third = Array.from(document.querySelectorAll("tbody tr")[2].querySelectorAll("td")).map((td) => td.textContent);
    expect(third[2]).toContain("Critical service not established");
    expect(third[3]).toBe("Limited");
    expect(document.querySelector("[data-mini-local-period]")?.textContent).toBe(`Site-local days 2026-10-06 to 2026-10-08 (${TZ})`);
  });

  it("no selected revision keeps the page shell: Not assessed, Unknown cards and the empty-table copy", async () => {
    const empty = read({
      status: "UNKNOWN",
      currentness: { state: "UNKNOWN", job_state: "NONE", windows: [] },
      selected_source_provenance: null,
      source_provenance: null,
      coverage: null,
      cards: { capability_kw: null, used_kw: null, headroom_kw: null, eligible_days: null, assessed_days: null },
      rows: [],
      links: { dispatch: null, evidence: `/sites/${CODE}/evidence`, financials: null, actions: "/actions" },
    });
    renderRenewable([ok(empty)]);
    await settledScreen();
    await screen.findByText("Not assessed");
    expectV69Panels("renewable");
    expect(cardValues()).toEqual(["Unknown", "Unknown", "Unknown", "Not established"]);
    expect(panelTitled("Eligible and excluded windows").textContent).toContain("No renewable window has been assessed for this period.");
  });

  it("q10-3: a supported assessment with no positive headroom reads No usable headroom", async () => {
    const cards = { capability_kw: { low: 20, high: 22 }, used_kw: { low: 20, high: 22 }, headroom_kw: { low: 0, high: 2 }, eligible_days: 0, assessed_days: 1 };
    renderRenewable([ok(read({ cards }))]);
    await settledScreen();
    await screen.findByText("No usable headroom");
    expect(strip()).not.toContain("Watch");
    // The status word is not `Not assessed`; the separate confidence chip (R310) always is.
    expect(strip().replace("Confidence: Not assessed", "")).not.toContain("Not assessed");
  });

  it("q10-3: pending recompute or unknown provenance never gets Watch", async () => {
    renderRenewable([ok(read({ currentness: { state: "PENDING_RECOMPUTE", job_state: "PENDING", windows: [hour("2026-10-06", true)] } }))]);
    await settledScreen();
    await screen.findByText("Recompute pending");
    expect(strip()).not.toContain("Watch");
    cleanup();
    const unknown = { classification: "UNKNOWN", source_ids: [id(2)], evidence_ids: [id(100)] };
    renderRenewable([ok(read({ selected_source_provenance: unknown, source_provenance: unknown }))]);
    await settledScreen();
    await screen.findByText("Selected sources: Where these readings came from is not established");
    expect(strip()).not.toContain("Watch");
    expect(strip()).toContain("Evidence limited");
    cleanup();
    // q11-1: a MIXED pending provenance downgrades even when the selected one is registered.
    const mixed = { classification: "MIXED", source_ids: [id(2), id(3)], evidence_ids: [id(100)] };
    renderRenewable([ok(read({ pending_source_provenance: mixed }))]);
    await settledScreen();
    await screen.findByText("Evidence limited");
    expect(strip()).not.toContain("Watch");
    expect(strip()).toContain("Pending sources: Where these readings came from is not established");
    expect(strip()).not.toMatch(/mixed|registered_simulation|authored_demonstration/);
    cleanup();
    // H2: authored selected provenance renders the shared plain words, never the enum.
    const authored = { classification: "AUTHORED_DEMONSTRATION", source_ids: [id(2)], evidence_ids: [id(100)] };
    renderRenewable([ok(read({ selected_source_provenance: authored, source_provenance: authored }))]);
    await settledScreen();
    await screen.findByText("Selected sources: Prepared example data, not field readings");
    expect(strip()).not.toMatch(/authored_demonstration/i);
  });

  it("historical selection says so and keeps the frozen status", async () => {
    renderRenewable([ok(read({ currentness: { state: "HISTORICAL", job_state: "SETTLED", windows: [{ ...hour("2026-10-06", true), state: "HISTORICAL" }] } }))]);
    await settledScreen();
    await screen.findByText("Historical selection");
    expect(strip()).toContain("Historical selection; job state reflects the retained job record");
  });

  it("the opportunity drawer cites the selected rows and says Not assessed for demand, sale and tariff", async () => {
    renderRenewable([ok(read())]);
    await settledScreen();
    fireEvent.click(await screen.findByRole("button", { name: "Inspect opportunity constraints" }));
    const drawer = document.querySelector('[data-mini-drawer="opportunity"]') as HTMLElement;
    expect(drawer.textContent).toContain("Productive-use opportunity evidence");
    expect(drawer.textContent).toContain("Eligible-window basis");
    expect(drawer.textContent).toContain(id(100));
    expect(drawer.textContent).toContain("Customer demand: Not assessed");
    expect(drawer.textContent).toContain("Tariff: Not assessed");
    expect(drawer.textContent).not.toMatch(/10 kW|\$0\.25|\$2\.50/);
    expectV69Panels("renewable");
  });

  it("503 shows the retry copy and retries; 422 keeps the frame with client copy, never the API message, and the period bar editable", async () => {
    const unavailable: MiniRead<RenewableRead> = { status: "refused", httpStatus: 503, code: "MINI_DEPTH_STORE_UNAVAILABLE", message: "x" };
    const client = renderRenewable([unavailable, ok(read())]);
    await settledScreen();
    expect(await screen.findByText("Mini-grid evidence is unavailable right now. Try again.")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    await screen.findByText("Watch");
    expect(client.getRenewable).toHaveBeenCalledTimes(2);
    cleanup();
    const message = "Select a valid complete site-local hour or one to five site-local days.";
    renderRenewable([{ status: "refused", httpStatus: 422, code: "INVALID_WINDOW", message }], `/sites/${CODE}/performance/renewable?from=a&to=b`);
    await settledScreen();
    expect(await screen.findByText("Choose a valid Site-local window.")).toBeTruthy();
    expect(main().textContent).not.toContain(message);
    expect(document.querySelector("[data-mini-period] select")).not.toBeNull();
  });

  it("the period bar sends one to five site-local days as UTC bounds", () => {
    expect(localDaysWindow(TZ, "2026-10-06", 5)).toEqual({ from: "2026-10-05T21:00:00.000Z", to: "2026-10-10T21:00:00.000Z" });
    const params = new URLSearchParams("from=2026-10-05T21:00:00Z&to=2026-10-06T21:00:00Z&known_at=2026-10-07T00:00:00Z");
    expect(renewableWindowFromParams(params, TZ)).toEqual({
      from: "2026-10-05T21:00:00Z",
      to: "2026-10-06T21:00:00Z",
      known_at: "2026-10-07T00:00:00Z",
    });
    // A zone behind UTC: the UTC day start is the previous local date.
    expect(renewableWindowFromParams(new URLSearchParams("date=2026-10-06"), "America/New_York")).toEqual({
      from: "2026-10-05T04:00:00.000Z",
      to: "2026-10-06T04:00:00.000Z",
      known_at: null,
    });
  });
});

describe("post-W6 W4 R309/R310/R312/R313: renewable tones, confidence, recurrence and the refused frame", () => {
  const five = ["2026-10-06", "2026-10-07", "2026-10-08", "2026-10-09", "2026-10-10"];
  const badge = (text: string) => screen.getAllByText(text).find((el) => el.classList.contains("badge")) as HTMLElement;

  it("R309: chips take tones from stored enums only (Watch amber, Lens neutral, Eligible green, Limited amber, Excluded neutral) and series fills keep their identity", async () => {
    const rows = [row("2026-10-06"), row("2026-10-07", { decision: "EXCLUDED", opportunity_kwh: null }), row("2026-10-08", { decision: "LIMITED", opportunity_kwh: null })];
    const windows = [hour("2026-10-06", true, 1), hour("2026-10-07", true, 2), hour("2026-10-08", true, 3)];
    renderRenewable([ok(read({ rows, currentness: { state: "CURRENT", job_state: "SETTLED", windows } }))], `/sites/${CODE}/performance/renewable?from=2026-10-05T21:00:00Z&to=2026-10-08T21:00:00Z`);
    await settledScreen();
    await screen.findByText("Watch");
    expect(badge("Watch").className).toContain("status-tone--amber");
    // build ruling 3 / D1 R454: the fixed page lens is neutral, never green, with its visible deviation label
    expect(badge("Lens: Opportunity").className).toContain("status-tone--neutral");
    expect(badge("Lens: Opportunity").className).not.toContain("status-tone--green");
    expect(badge("Lens: Opportunity").parentElement?.querySelector("[data-mock-deviation='R454']")?.textContent?.trim()).toBe("MOCK DEVIATION D1 (R454)");
    expect(badge("Eligible").className).toContain("status-tone--green");
    expect(badge("Excluded").className).toContain("status-tone--neutral");
    expect(badge("Limited").className).toContain("status-tone--amber");
    const tones = Array.from(document.querySelectorAll("[data-value-bar-tone]"), (el) => el.getAttribute("data-value-bar-tone"));
    expect(tones).toEqual(["pv", "headroom"]);
    // the retained margin is unknown: hatched, never coloured as assessed
    expect(document.querySelector('[data-value-bar-key="margin"] [data-value-bar-mark="not-known"]')).not.toBeNull();
  });

  it("R310 / D1 R451: Confidence: Not assessed sits in the strip with its visible deviation label", async () => {
    renderRenewable([ok(read())]);
    await settledScreen();
    await screen.findByText("Watch");
    const chip = document.querySelector("[data-mini-confidence]") as HTMLElement;
    expect(chip.querySelector(".badge")?.textContent).toBe("Confidence: Not assessed");
    expect(chip.querySelector("[data-mock-deviation='R451']")?.textContent?.trim()).toBe("MOCK DEVIATION D1 (R451)");
  });

  it("R312: 3 of 3 assessed days do not establish recurrence in strip, card or chart note", async () => {
    const windows = five.slice(0, 3).map((day, i) => hour(day, true, i + 1));
    const cards = { capability_kw: { low: 41, high: 43 }, used_kw: { low: 20, high: 20 }, headroom_kw: { low: 18, high: 20 }, eligible_days: 3, assessed_days: 3 };
    renderRenewable([ok(read({ cards, rows: five.slice(0, 3).map((d) => row(d)), currentness: { state: "CURRENT", job_state: "SETTLED", windows } }))]);
    await settledScreen();
    await screen.findByText("Watch");
    expect(strip()).toContain("Recurrence is not established for this selection.");
    expect(strip()).not.toContain("3 of 3");
    expect(cardValues()[3]).toBe("Not established");
    expect(main().textContent).toContain("Needs five completely assessed days.");
    expect(document.querySelector("[data-mini-recurrence]")?.textContent).toBe("Recurrence is not established for this selection.");
  });

  it("R312: 5 of 5 completely assessed days establish recurrence at every level", async () => {
    const windows = five.map((day, i) => hour(day, true, i + 1));
    const cards = { capability_kw: { low: 41, high: 43 }, used_kw: { low: 20, high: 20 }, headroom_kw: { low: 18, high: 20 }, eligible_days: 3, assessed_days: 5 };
    renderRenewable([ok(read({ cards, rows: five.map((d) => row(d)), currentness: { state: "CURRENT", job_state: "SETTLED", windows } }))]);
    await settledScreen();
    await screen.findByText("Watch");
    expect(strip()).toContain("Solar headroom on 3 of 5 completely assessed days");
    expect(cardValues()[3]).toBe("3 / 5 days");
    expect(document.querySelector("[data-mini-recurrence]")?.textContent).toBe("Usable headroom recurred on 3 of 5 completely assessed days.");
  });

  it("R312: a gap-limited five-day selection is not established, and selected rows never sit beside `No selected assessment`", async () => {
    const windows = five.map((day, i) => hour(day, i !== 2, i + 1));
    const cards = { capability_kw: { low: 41, high: 43 }, used_kw: { low: 20, high: 20 }, headroom_kw: { low: 18, high: 20 }, eligible_days: 3, assessed_days: 4 };
    renderRenewable([ok(read({ cards, rows: [row(five[0])], currentness: { state: "UNKNOWN", job_state: "NONE", windows } }))]);
    await settledScreen();
    await screen.findAllByText("Recurrence is not established for this selection.");
    expect(strip()).toContain("Recurrence is not established for this selection.");
    expect(cardValues()[3]).toBe("Not established");
    expect(strip()).not.toContain("No selected assessment");
    expect(document.querySelector("[data-mini-currentness]")).toBeNull();
  });

  it.each([
    ["six days", "from=2026-10-05T21:00:00Z&to=2026-10-11T21:00:00Z", "Choose one to five complete Site-local days."],
    ["a reversed range", "from=2026-10-08T21:00:00Z&to=2026-10-05T21:00:00Z", "The end must be after the start."],
    ["an unprovable cause", "from=2026-10-05T21:00:00Z&to=2026-10-06T22:00:00Z", "Choose a valid Site-local window."],
  ])("R313: a refused window (%s) keeps strip, muted tiles and the named panels with one client reason", async (_name, query, reason) => {
    const message = "SERVER MESSAGE `INVALID_WINDOW` must not show";
    renderRenewable([{ status: "refused", httpStatus: 422, code: "INVALID_WINDOW", message }], `/sites/${CODE}/performance/renewable?${query}`);
    await settledScreen();
    expect(await screen.findByText(reason)).toBeTruthy();
    expect(main().textContent).not.toContain("SERVER MESSAGE");
    expect(main().textContent).not.toContain("INVALID_WINDOW");
    expect(strip()).toContain("Window cannot be read");
    expect(strip()).toContain("Confidence: Not assessed");
    expect(cardValues()).toEqual(["Not assessed", "Not assessed", "Not assessed", "Not assessed"]);
    expect(panelTitled("From physical headroom to an opportunity").textContent).toContain(reason);
    expect(panelTitled("Productive-use evaluation").textContent).toContain("Not assessed");
    expect(panelTitled("Eligible and excluded windows").textContent).toContain("Not assessed");
    expect(screen.getAllByText(reason)).toHaveLength(1);
    expect(document.querySelector("[data-mini-period] select")).not.toBeNull();
  });
});
