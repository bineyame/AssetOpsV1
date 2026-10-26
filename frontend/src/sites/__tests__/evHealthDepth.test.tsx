/**
 * W5-03b E4: EV Site Health (v6.9 `ev-health`) from the selected `/ev/health` depth read
 * (`.agent/W5-03-build-spec.md` E4 card and pre-flight E4 correction; `.agent/W5-03b-ui-preflight-rulings.md` 2-8).
 */
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import type { EvAssessmentClient, EvRead } from "../evAssessmentClient";
import { EV_DEPTH_MALFORMED, EV_HEALTH_TUPLES, type EvDepthClient, type EvHealthRead, type EvHealthRow, isEvHealthRead } from "../evDepthClient";
import { HEALTH_CONDITION_NOTICE, HEALTH_EMPTY, HEALTH_LOADING, conditionRows, faultNote } from "../EvHealthDepth";
import type { SiteDetailClient, SiteDirectoryClient } from "../siteDirectoryClient";
import type { SiteDetailReadModel } from "../siteReadModel";
import { EMPTY_ANALYTICS_CLIENT } from "./analyticsFixtures";
import { expectPlantedPanelRejected, expectV69Panels, renderedPanelTitles } from "../../test/panelStructure";
import { settledScreen } from "../../test/settled";

const NODE_FS = (await import(/* @vite-ignore */ `node:${"fs"}`)) as { readFileSync: (p: string, e: string) => string };
const CODE = "EV-LAB-001";
const FROM = "2026-10-06T08:00:00.000000Z";
const TO = "2026-10-06T09:00:00.000000Z";
const KNOWN = "2026-10-06T09:00:00.000000Z";
const id = (n: number) => `00000000-0000-4000-8000-${String(n).padStart(12, "0")}`;
const BLOCK = { classification: "REGISTERED_SIMULATION", state: "REGISTERED_SIMULATION", source_ids: [], evidence_ids: [], basis_sha256: null, reasons: [] };
const BATTERY = { condition_state: "UNKNOWN" as const, limitation: "Battery configuration is not established by this Foundation." };
const tuple = (n: number) => {
  const [kind, condition_state, observation, limitation, next_evidence] = EV_HEALTH_TUPLES[n];
  return { kind, condition_state, observation, limitation, next_evidence };
};
const row = (n: number, label: string, asset: number, extra: Partial<EvHealthRow> = {}): EvHealthRow => ({
  ...tuple(n),
  label,
  asset_id: id(asset),
  asset_code: label.toLowerCase().replace(/ /g, "-"),
  session_id: null,
  evidence_ids: [],
  ...extra,
});
const C1 = row(1, "Connector c1", 7);
const C2 = row(0, "Connector c2", 8, { session_id: id(70), evidence_ids: [id(201), id(202)] });
const METER = row(2, "Site meter", 9, { evidence_ids: [id(301)] });
const ROGUE = row(3, "Feeder meter", 10);

function read(state = "CURRENT", rows: EvHealthRow[] = [C1, C2, METER], over: Partial<EvHealthRead> = {}): EvHealthRead {
  return {
    schema_version: "ev-depth-1",
    site_id: id(1),
    window: { from: FROM, to: TO, known_at: KNOWN, committed_watermark: KNOWN },
    selection: {
      state: state as EvHealthRead["selection"]["state"],
      assessment_revision_id: id(50),
      session_revision_ids: [id(60)],
      accepted_evidence_ids: [id(201), id(202), id(301)],
      source_provenance: BLOCK,
    },
    health: { foundation_revision_id: id(40), rows, battery: BATTERY },
    links: {
      sessions: `/api/sites/${CODE}/ev/sessions?from=${FROM}&to=${TO}&known_at=${KNOWN}`,
      evidence_analysis: `/api/sites/${CODE}/ev/evidence/analysis?from=${FROM}&to=${TO}&known_at=${KNOWN}`,
      financials: `/api/sites/${CODE}/ev/financials?from=${FROM}&to=${TO}&known_at=${KNOWN}`,
    },
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
const never = <T,>(): Promise<EvRead<T>> => new Promise(() => undefined);
const evAssessment: EvAssessmentClient = { listSessions: never, getSession: never, listFindings: never, getFinding: never };

type Answer = Awaited<ReturnType<EvDepthClient["getHealth"]>>;
const loaded = (value: EvHealthRead): Answer => ({ status: "loaded", value });

function renderHealth(answer: Answer | (() => Promise<Answer>), query = `?from=${FROM}&to=${TO}`) {
  const requests: string[] = [];
  vi.stubGlobal("fetch", vi.fn((url: string) => {
    requests.push(url);
    return new Promise(() => undefined);
  }));
  const getHealth = vi.fn(typeof answer === "function" ? answer : () => Promise.resolve(answer));
  const depth: EvDepthClient = { getAvailability: vi.fn(), getEnergy: vi.fn(), getHealth };
  render(
    <MemoryRouter initialEntries={[`/sites/${CODE}/health${query}`]}>
      <App flags={featureFlagsWith(false)} siteDirectory={directory} siteDetail={detail} siteAnalytics={EMPTY_ANALYTICS_CLIENT} evAssessment={evAssessment} evDepth={depth} />
    </MemoryRouter>,
  );
  return { getHealth, requests };
}

const main = () => document.querySelector("main") as HTMLElement;
const text = (el: Element | null) => (el?.textContent ?? "").replace(/\s+/g, " ").trim();
const cards = () =>
  Array.from(document.querySelectorAll("[data-ev-health-card]")).map((c) => [
    text(c.querySelector(".v69-metric__label")),
    text(c.querySelector(".v69-metric__value")),
    text(c.querySelector(".v69-metric__note")),
    c.className.includes("v69-metric--amber") ? "amber" : c.className.includes("v69-metric--muted") ? "gray" : "",
  ]);
const tableRows = () => Array.from(document.querySelectorAll("[data-ev-health-row]")).map((r) => Array.from(r.children).map(text));
const SESSIONS = `/sites/${CODE}/performance/sessions?from=${encodeURIComponent(FROM)}&to=${encodeURIComponent(TO)}&known_at=${encodeURIComponent(KNOWN)}`;

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("W5-03b E4: EV Health", () => {
  it("health_copy_and_sessions_destination: cards, condition rows, notices and exact Sessions destinations", async () => {
    const { getHealth, requests } = renderHealth(loaded(read()));
    await settledScreen();
    expect(getHealth).toHaveBeenCalledWith(CODE, { from: FROM, to: TO, known_at: null });
    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("EV lab depot");
    // Ruling 5 (R95/R96/R57): one card per selected connector in DTO order with its label, then the battery (R56).
    expect(cards()).toEqual([
      ["Connector c1", "Unknown", "No charger condition assessment", "gray"],
      ["Connector c2", "Needs attention", faultNote(2), "amber"],
      ["Stationary battery", "Unknown", "Battery configuration is not established by this Foundation.", "gray"],
    ]);
    expect(faultNote(2)).toBe("2 selected fault records; cause not diagnosed");
    // Ruling 20: singular and zero.
    expect(faultNote(1)).toBe("1 selected fault record; cause not diagnosed");
    expect(faultNote(0)).toBe("0 selected fault records; cause not diagnosed");
    const cardLinks = Array.from(document.querySelectorAll("[data-ev-health-card] a"));
    expect(cardLinks.map((a) => [text(a), a.getAttribute("href")])).toEqual([
      ["View detail →", SESSIONS],
      ["View detail →", SESSIONS],
    ]);
    // Ruling 7: fault connector, then Site meter (R59), then the non-fault connector (R58).
    expect(tableRows()).toEqual([
      [`Connector c2${id(8)}`, `Session interruption; hardware fault not establishedSession ${id(70)} Open Sessions →`, "Diagnostic event + witnessed session"],
      [`Site meter${id(9)}`, "Power limit not assessed from selected samples", "Continuous coverage for interval-wide claims"],
      [`Connector c1${id(7)}`, "No connector condition assessment", "Diagnostic event + witnessed session"],
    ]);
    // Ruling 21: the session reference sits in the `Supported assessment` (second) cell of the fault row.
    const faultRow = document.querySelector("tbody tr")!;
    expect(faultRow.children[1].contains(document.querySelector("[data-ev-health-session]"))).toBe(true);
    expect(faultRow.children[1].contains(document.querySelector("[data-ev-health-open-sessions]"))).toBe(true);
    expect(faultRow.children[0].querySelector("[data-ev-health-session]")).toBeNull();
    const open = document.querySelector("[data-ev-health-open-sessions]")!;
    expect(open.getAttribute("href")).toBe(SESSIONS);
    expect(document.querySelector("[data-ev-health-session]")!.getAttribute("data-vocabulary-exempt")).toBe("source-reference");
    expect(document.querySelectorAll('[data-ev-health-asset-id][data-vocabulary-exempt="source-reference"]')).toHaveLength(3);
    // Sole mock panel, R16 directly after it, no currentness notice when CURRENT.
    expectV69Panels("ev-health");
    expectPlantedPanelRejected("ev-health");
    const panel = document.querySelector("section.panel")!;
    expect(panel.nextElementSibling?.matches("[data-ev-health-condition-notice]")).toBe(true);
    expect(text(panel.nextElementSibling)).toBe(HEALTH_CONDITION_NOTICE);
    expect(document.querySelector("[data-ev-depth-state-notice]")).toBeNull();
    // No completed session proves hardware health; no positive limit claim; no S7 panel or request (R60 withdrawn).
    const body = text(main());
    for (const banned of ["Healthy", "Operating normally", "Not applicable", "None installed", "Power limit respected", "Data sources"]) {
      expect(body).not.toContain(banned);
    }
    expect(requests.some((url) => url.includes("/source-health") || url.includes("/battery"))).toBe(false);
    expect(document.querySelector("#site-health-sources-heading")).toBeNull();
    expect(document.querySelector("[data-ev-health-empty]")).toBeNull();
  });

  it("health_states_loading: loading, currentness notices, refusal, malformed and empty states", async () => {
    renderHealth(() => new Promise(() => undefined));
    expect(await screen.findByText(HEALTH_LOADING)).toBeTruthy();
    cleanup();

    const notices: [string, string][] = [
      ["PENDING_RECOMPUTE", "New evidence is being assessed. Earlier selected results may change."],
      ["HISTORICAL", "This result reflects records known at the selected cutoff."],
      ["STALE_SOURCE", "Selected source records are stale for this window."],
      ["UNKNOWN", "No selected EV session assessment covers this window yet."],
    ];
    for (const [state, sentence] of notices) {
      renderHealth(loaded(read(state)));
      await settledScreen();
      const notice = document.querySelector("[data-ev-depth-state-notice]")!;
      expect(text(notice), state).toBe(sentence);
      // R15 immediately before the cards; R16 immediately after the sole panel.
      expect(notice.nextElementSibling?.matches(".v69-cards"), state).toBe(true);
      expect(renderedPanelTitles(), state).toEqual(["Condition and evidence"]);
      const panel = document.querySelector("section.panel")!;
      expect(panel.nextElementSibling?.matches("[data-ev-health-condition-notice]"), state).toBe(true);
      cleanup();
    }

    // Ruling 2: the server's typed refusal, never a fabricated one; Retry repeats the same read.
    const refused: Answer = { status: "refused", httpStatus: 422, code: "EV_WINDOW_INVALID", message: "'from' must be earlier than 'to'." };
    renderHealth(refused, `?from=${TO}&to=${FROM}`);
    await settledScreen();
    expect(text(document.querySelector("[data-panel-gap='ev-depth-refusal']"))).toBe("The selected window needs both a start and an end, with the start before the end.");
    expect(main().textContent).not.toContain("EV_WINDOW_INVALID 'from'");
    expect(document.querySelector("[data-ev-health-card]")).toBeNull();
    expect(document.querySelector("[data-ev-depth-correction]")?.textContent).toBe("Read without a selected window");
    expect(screen.queryByRole("button", { name: /Retry|Reload/ })).toBeNull();
    cleanup();
    // A 503 reloads the same read (R244).
    const unavailable = renderHealth({ status: "refused", httpStatus: 503, code: "EV_UNAVAILABLE", message: null });
    await settledScreen();
    fireEvent.click(screen.getByRole("button", { name: "Reload" }));
    await settledScreen();
    expect(unavailable.getHealth).toHaveBeenCalledTimes(2);
    expect(unavailable.getHealth.mock.calls[1]).toEqual(unavailable.getHealth.mock.calls[0]);
    cleanup();

    renderHealth({ status: "unavailable", message: EV_DEPTH_MALFORMED });
    await settledScreen();
    expect(text(document.querySelector("[data-panel-gap='ev-depth-refusal']"))).toBe("EV evidence is temporarily unavailable. Retry.");
    expect(text(main())).not.toContain("No records");
    cleanup();

    // Zero connectors, and no Foundation: the empty sentence and the battery card, never a refusal.
    for (const value of [read("CURRENT", [METER]), read("UNKNOWN", [], { health: { foundation_revision_id: null, rows: [], battery: BATTERY } })]) {
      renderHealth(loaded(value));
      await settledScreen();
      expect(text(document.querySelector("[data-ev-health-empty]"))).toBe(HEALTH_EMPTY);
      expect(cards().map((c) => c[0])).toEqual(["Stationary battery"]);
      expect(document.querySelector(".page-refusal")).toBeNull();
      cleanup();
    }

    // R97: an UNKNOWN-kind meter has no card and no row; it is never relabelled a Site meter.
    renderHealth(loaded(read("CURRENT", [C1, ROGUE])));
    await settledScreen();
    expect(tableRows().map((r) => r[0])).toEqual([`Connector c1${id(7)}`]);
    expect(text(main())).not.toContain("Feeder meter");
    cleanup();

    // Ruling 2: a bare route reads with no window; without a returned pair no Sessions link is offered.
    const bare = renderHealth(loaded(read("UNKNOWN", [C1, C2], { window: { from: null, to: null, known_at: null, committed_watermark: null } })), "");
    await settledScreen();
    expect(bare.getHealth).toHaveBeenCalledWith(CODE, { from: null, to: null, known_at: null });
    expect(document.querySelectorAll("[data-ev-health-card] a")).toHaveLength(0);
    expect(document.querySelector("[data-ev-health-open-sessions]")).toBeNull();
    expect(text(document.querySelector("[data-ev-health-session]"))).toBe(`Session ${id(70)}`);
  });

  it("orders more than two connectors and keeps every selected row (R96/R58)", () => {
    const c3 = row(0, "Connector c3", 11, { session_id: id(71), evidence_ids: [id(203)] });
    expect(conditionRows([C1, C2, c3, METER, ROGUE]).map((r) => r.label)).toEqual(["Connector c2", "Connector c3", "Site meter", "Connector c1"]);
  });

  it("E4-L3: the four E1b tuple strings are identical in the backend source and the frontend table", () => {
    // Independent literals: neither EV_HEALTH_TUPLES nor the Python constants feed this expectation.
    const expected = {
      CONNECTOR_FAULT: ["NEEDS_INVESTIGATION", "Session interruption observed", "Fault-stopped session observed; cause not diagnosed", "Retrieve diagnostic log and witness a complete session"],
      CONNECTOR_UNKNOWN: ["UNKNOWN", "Condition unknown", "No charger condition assessment", "Record diagnostic and covered operation"],
      SITE_METER: ["UNKNOWN", "Sampled import only", null, "Record continuous import and request/limit evidence"],
      METER_UNKNOWN: ["UNKNOWN", "Meter role not established", "No selected Site-import binding for this meter", "Confirm meter topology and source binding"],
    } as const;
    const fs = (globalThis as unknown as { process: { cwd: () => string } }).process;
    const source = NODE_FS.readFileSync(`${fs.cwd()}/../backend/assetops_backend/analytics/ev_depth.py`, "utf8");
    for (const [name, parts] of Object.entries(expected)) {
      const literal = parts.map((p) => (p === null ? "None" : `"${p}"`)).join(String.raw`,\s*`);
      expect(new RegExp(String.raw`${name} = \(\s*${literal}\)`).test(source), name).toBe(true);
    }
    const kinds = ["CONNECTOR", "CONNECTOR", "SITE_METER", "UNKNOWN"];
    const names = Object.values(expected);
    EV_HEALTH_TUPLES.forEach(([kind, state, observation, limitation, next], n) => {
      expect([kind, state, observation, limitation, next]).toEqual([kinds[n], names[n][0], names[n][1], names[n][2], names[n][3]]);
    });
    expect(EV_HEALTH_TUPLES).toHaveLength(4);
  });

  it("evDepthClient refuses a Health row outside the E1b tuple table", () => {
    const good = read();
    expect(isEvHealthRead(good)).toBe(true);
    const bad = (patch: Partial<EvHealthRow>) => read("CURRENT", [{ ...C1, ...patch }]);
    expect(isEvHealthRead(bad({ condition_state: "NEEDS_INVESTIGATION" }))).toBe(false);
    expect(isEvHealthRead(bad({ observation: "Healthy" }))).toBe(false);
    expect(isEvHealthRead(bad({ limitation: null }))).toBe(false);
    expect(isEvHealthRead(bad({ kind: "SITE_METER" }))).toBe(false);
    expect(isEvHealthRead(read("CURRENT", [{ ...METER, next_evidence: "Continuous coverage for interval-wide claims" }]))).toBe(false);
    expect(isEvHealthRead(read("CURRENT", [ROGUE]))).toBe(true);
  });
});
