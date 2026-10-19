import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import type {
  EvAssessmentClient,
  EvDenominator,
  EvEnvelope,
  EvFindingDetailRead,
  EvFindingsRead,
  EvRead,
  EvSessionDetailRead,
  EvSessionItem,
  EvSessionsRead,
} from "../evAssessmentClient";
import type { SiteDetailClient, SiteDirectoryClient } from "../siteDirectoryClient";
import type { SiteDetailReadModel } from "../siteReadModel";
import { EMPTY_ANALYTICS_CLIENT } from "./analyticsFixtures";
import { expectPlantedPanelRejected, expectV69Panels, panelTitled } from "../../test/panelStructure";
import { settledScreen } from "../../test/settled";

/*
 * W2-06 commit 5 (`.agent/W2-06-build-spec.md` "Commit 5", r5 state copy, r6 commit-5 dry-read): an EV_CHARGING
 * Site's Performance/Sessions and Finding routes render `sessions` and `ev-finding` in the exact v69 panel
 * structure (`docs/architecture/v69-rendered-panels.json`) for the stocked complete, interrupted, missing-meter,
 * pending/historical, contradictory, empty/orphan, unknown and refused states. Fixture values follow the W2-05b
 * replay shapes (EV-LAB-001, Connector c1/c2), never the mock's illustrations.
 */

afterEach(cleanup);

const CODE = "EV-LAB-001";
const FROM = "2026-10-06T08:00:00.000000Z";
const TO = "2026-10-06T09:00:00.000000Z";
const KNOWN = "2026-10-06T09:00:00.000000Z";
const id = (n: number) => `00000000-0000-4000-8000-${String(n).padStart(12, "0")}`;
const FINDING = id(900);
const BASIS = "b".repeat(64);
const LINKS_NONE = { self: null, evidence: null, analysis: null, finding: null, financials: null };

function envelope(state = "CURRENT", known = KNOWN): EvEnvelope {
  return {
    site_id: id(1),
    window: { from: FROM, to: TO, known_at: known },
    currentness: {
      state,
      as_of: state === "UNKNOWN" ? null : "2026-10-06T09:00:01.000000Z",
      limitation:
        state === "PENDING_RECOMPUTE"
          ? "New evidence is being assessed. The previous result may change."
          : state === "HISTORICAL"
            ? "This result reflects records known at the selected cutoff."
            : state === "UNKNOWN"
              ? "No selected EV session assessment covers this window yet."
              : null,
    },
    source_provenance: { classification: "REGISTERED_SIMULATION", source_ids: [id(2)], evidence_ids: [id(100)], basis_sha256: BASIS },
    limitations: [],
  };
}

function counts(over: Partial<EvDenominator> = {}): EvDenominator {
  return {
    started: 1, completed: 1, observed_abort: 0, incomplete: 0, contradictory: 0, orphan: 0,
    confirmed_delivery: 1, fault_aborted: 0, as_of: "2026-10-06T09:00:01.000000Z", limitation: null, ...over,
  };
}

function session(n: number, over: Partial<EvSessionItem> = {}): EvSessionItem {
  return {
    session_id: id(n),
    external_session_id: `S-${n}`,
    charger_asset_id: id(20),
    connector_asset_id: id(21),
    connector_display_name: "Connector c1",
    revision_id: id(n + 500),
    revision_no: 1,
    basis_sha256: BASIS,
    state: "COMPLETED",
    start_at: "2026-10-06T08:01:00.000000Z",
    end_at: "2026-10-06T08:31:00.000000Z",
    start_bounds: { earliest: "2026-10-06T08:01:00.000000Z", latest: "2026-10-06T08:01:00.000000Z" },
    end_bounds: { earliest: "2026-10-06T08:31:00.000000Z", latest: "2026-10-06T08:31:00.000000Z" },
    supported_kwh: "30.000",
    energy_complete: true,
    unknown_meter_seconds: 0,
    reason_codes: [],
    fault_evidence_id: null,
    finding_id: null,
    completeness: { start: true, terminal: true, meter: true, clock: true },
    as_of: "2026-10-06T09:00:01.000000Z",
    source_provenance: envelope().source_provenance,
    links: { ...LINKS_NONE, self: `/api/sites/${CODE}/ev/sessions/${id(n)}` },
    ...over,
  };
}

const sessions = (state: string, status: string, items: EvSessionItem[], d: Partial<EvDenominator> = {}): EvSessionsRead => ({
  ...envelope(state),
  status: { state: status, claim_level: "OBSERVED", as_of: "2026-10-06T09:00:01.000000Z", limitation: null },
  denominator: counts(d),
  items,
  next_cursor: null,
});

const INTERRUPTED_ROW = session(11, {
  connector_display_name: "Connector c2",
  state: "OBSERVED_ABORT",
  end_at: "2026-10-06T08:20:00.000000Z",
  supported_kwh: "12.500",
  fault_evidence_id: id(150),
  finding_id: FINDING,
  links: { ...LINKS_NONE, self: "x", finding: `/api/sites/${CODE}/ev/findings/${FINDING}` },
});

const STATES = {
  complete: sessions("CURRENT", "OBSERVED_SESSIONS", [session(10)]),
  interrupted: sessions("CURRENT", "OBSERVED_SESSIONS", [session(10), INTERRUPTED_ROW], {
    started: 2, completed: 1, observed_abort: 1, fault_aborted: 1, confirmed_delivery: 1,
  }),
  missingMeter: sessions("CURRENT", "OBSERVED_SESSIONS", [
    session(12, { energy_complete: false, unknown_meter_seconds: 600, reason_codes: ["METER_GAP"], completeness: { start: true, terminal: true, meter: false, clock: true } }),
  ], { confirmed_delivery: 0 }),
  contradictory: sessions("CURRENT", "CONTRADICTORY", [
    session(13, { state: "CONTRADICTORY", end_at: null, energy_complete: null, unknown_meter_seconds: null, reason_codes: ["CONTRADICTORY_TERMINAL"], completeness: { start: true, terminal: false, meter: false, clock: true } }),
  ], { completed: 0, contradictory: 1, confirmed_delivery: 0 }),
  empty: sessions("CURRENT", "NO_SESSIONS_OBSERVED", [], { started: 0, completed: 0, confirmed_delivery: 0, orphan: 1 }),
  pendingLate: sessions("PENDING_RECOMPUTE", "OBSERVED_SESSIONS", [
    session(14, { state: "INCOMPLETE", end_at: null, energy_complete: false, reason_codes: ["MISSING_TERMINAL"], completeness: { start: true, terminal: false, meter: true, clock: true } }),
  ], { completed: 0, incomplete: 1, confirmed_delivery: 0 }),
  historicalLate: {
    ...sessions("HISTORICAL", "OBSERVED_SESSIONS", [
      session(14, { state: "INCOMPLETE", end_at: null, energy_complete: false, reason_codes: ["MISSING_TERMINAL"], completeness: { start: true, terminal: false, meter: true, clock: true } }),
    ], { completed: 0, incomplete: 1, confirmed_delivery: 0 }),
    window: { from: FROM, to: TO, known_at: "2026-10-06T09:00:00.000000Z" },
  },
  unknown: {
    ...sessions("UNKNOWN", "UNKNOWN", []),
    status: { state: "UNKNOWN", claim_level: "UNKNOWN", as_of: null, limitation: "No selected EV session assessment covers this window yet." },
    denominator: {
      started: null, completed: null, observed_abort: null, incomplete: null, contradictory: null, orphan: null,
      confirmed_delivery: null, fault_aborted: null, as_of: null, limitation: "No selected EV session assessment covers this window yet.",
    },
  } satisfies EvSessionsRead,
};

const FINDING_DETAIL: EvFindingDetailRead = {
  ...envelope(),
  finding_id: FINDING,
  revision_id: id(901),
  revision_no: 1,
  basis_sha256: BASIS,
  session_id: id(11),
  title: "Charging session interrupted by a connector fault",
  claim_level: "OBSERVED",
  lifecycle: "SUPPORTED",
  as_of: "2026-10-06T09:00:01.000000Z",
  links: LINKS_NONE,
  claim: {
    session_id: id(11),
    external_session_id: "S-11",
    connector_asset_id: id(21),
    start_at: "2026-10-06T08:01:00.000000Z",
    abort_at: "2026-10-06T08:20:00.000000Z",
    fault_evidence_id: id(150),
    supported_kwh: "12.500",
    energy_complete: true,
  },
  evidence: [],
  history: [{ revision_id: id(901), revision_no: 1, transition: "OPENED", lifecycle: "SUPPORTED", created_at: "2026-10-06T09:00:01.000000Z" }],
  limitations: ["A connector fault and session abort were observed; component cause and unmet demand remain unknown."],
};

const SESSION_DETAIL: EvSessionDetailRead = {
  ...envelope(),
  ...INTERRUPTED_ROW,
  status: STATES.interrupted.status,
  denominator: STATES.interrupted.denominator,
  evidence: [],
  meter_intervals: [],
  history: [],
};

const ok = <T,>(value: T): EvRead<T> => ({ status: "loaded", value });
const refused = (httpStatus: number, code: string): EvRead<never> => ({ status: "refused", httpStatus, code, message: "refused" });
const EMPTY_FINDINGS: EvFindingsRead = { ...envelope(), items: [], next_cursor: null };

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

function renderEv(path: string, list: EvRead<EvSessionsRead>, finding: EvRead<EvFindingDetailRead> = ok(FINDING_DETAIL)) {
  const client: EvAssessmentClient = {
    listSessions: vi.fn(() => Promise.resolve(list)),
    getSession: vi.fn(() => Promise.resolve(ok(SESSION_DETAIL))),
    listFindings: vi.fn(() => Promise.resolve(ok(EMPTY_FINDINGS))),
    getFinding: vi.fn(() => Promise.resolve(finding)),
  };
  render(
    <MemoryRouter initialEntries={[path]}>
      <App flags={featureFlagsWith(false)} siteDirectory={directory} siteDetail={detail} siteAnalytics={EMPTY_ANALYTICS_CLIENT} evAssessment={client} />
    </MemoryRouter>,
  );
  return client;
}

const SESSIONS = `/sites/${CODE}/performance/sessions`;
const FINDING_PATH = `/sites/${CODE}/findings/${FINDING}?from=${FROM}&to=${TO}&known_at=${KNOWN}`;
const main = () => document.querySelector("main") as HTMLElement;
const strip = () => (document.querySelector(".status-strip") as HTMLElement).textContent ?? "";
const cardValues = () => Array.from(document.querySelectorAll("[data-ev-card] .v69-metric__value")).map((x) => x.textContent);
const rowCells = (n = 0) => Array.from(document.querySelectorAll("tbody tr")[n].querySelectorAll("td")).map((td) => td.textContent);
const subtabs = (label: string) =>
  Array.from(document.querySelectorAll(`nav[aria-label="${label}"] li`)).map((li) => [
    li.getAttribute("data-tab-unavailable") ?? (li.textContent ?? "").trim(),
    li.hasAttribute("data-tab-unavailable"),
  ]);
const expectInert = (label: string) => {
  const li = document.querySelector(`[data-tab-unavailable="${label}"]`) as HTMLElement;
  expect(li.textContent).toBe(`${label} · Not available yet`);
  expect(li.querySelector("a, button, [tabindex]")).toBeNull();
  expect(li.hasAttribute("tabindex")).toBe(false);
};
const outcomeBadge = (n = 0) => document.querySelectorAll("tbody tr")[n].querySelectorAll("td")[3].querySelector(".badge") as HTMLElement;

describe("W2-06: sessions keeps the v69 panels, strip, cards and six columns", () => {
  it("stocked complete: exact copy, tones and structure", async () => {
    renderEv(SESSIONS, ok(STATES.complete));
    await settledScreen();
    expect(main().getAttribute("data-ev-view")).toBe("sessions");
    expectV69Panels("sessions");
    expectPlantedPanelRejected("sessions");
    expect(strip()).toContain("Sessions observed");
    expect(strip()).toContain("Generated test data");
    expect(strip()).toContain("These records came from a registered simulation, not a live charger.");
    expect(Array.from(document.querySelectorAll("[data-ev-card] .v69-metric__label")).map((x) => x.textContent)).toEqual([
      "Attempts", "Confirmed delivery", "Fault-aborted", "Incomplete",
    ]);
    expect(Array.from(document.querySelectorAll("[data-ev-card] .v69-metric__note")).map((x) => x.textContent)).toEqual([
      "Accepted starts", "Completed with full meter coverage", "Observed abort with fault record", "End record missing",
    ]);
    expect(cardValues()).toEqual(["1", "1", "0", "0"]);
    expect(Array.from(document.querySelectorAll("thead th")).map((th) => th.textContent)).toEqual([
      "Session / connector", "Period", "Energy", "Outcome", "Evidence completeness", "Next step",
    ]);
    expect(rowCells()).toEqual([
      "Session S-10 · Connector c1", "08:01 UTC – 08:31 UTC", "30.000 kWh · complete", "Delivered", "StartTerminalMeterClock", "Not available yet",
    ]);
    expect(outcomeBadge().className).toContain("ev-tone--green");
    const denominator = panelTitled("How to read the denominator").textContent ?? "";
    expect(denominator).toContain("1 accepted starts · 1 completed · 0 observed aborts · 0 incomplete · 0 contradictory");
    expect(denominator).toContain("Orphan end records: 0");
    expect(denominator).toContain("Unknown is separate from failure.");
    const cause = panelTitled("Cause remains bounded").textContent ?? "";
    expect(cause).toContain("Cause not established from accepted records.");
    expect(cause).toContain("Requested power, allocated limit, site import and charger diagnostics are needed to test competing explanations.");
    expect(document.querySelectorAll("[data-tab-unavailable]")).toHaveLength(2);
    // r7 P8: exact tab order, live Sessions then the two unbuilt EV entries, noninteractive.
    expect(subtabs("Performance sections")).toEqual([["Sessions", false], ["Availability", true], ["Energy / site power", true]]);
    expectInert("Availability");
    expectInert("Energy / site power");
    for (const panel of Array.from(main().querySelectorAll("section.panel"))) {
      expect(panel.querySelectorAll("details").length).toBeLessThanOrEqual(1);
    }
    for (const text of ["SES-", "F-130", "ACT-061", "CHG-002", "$36", "12 attempts"]) expect(main().textContent).not.toContain(text);
  });

  it("interrupted: Fault-aborted row with a proved Finding link at the same window", async () => {
    renderEv(`${SESSIONS}?from=${FROM}&to=${TO}&known_at=${KNOWN}`, ok(STATES.interrupted));
    await settledScreen();
    expectV69Panels("sessions");
    expect(cardValues()).toEqual(["2", "1", "1", "0"]);
    expect(rowCells(1)[3]).toBe("Fault-aborted");
    expect(outcomeBadge(1).className).toContain("ev-tone--amber");
    const link = screen.getByRole("link", { name: "Open Finding →" });
    expect(link.getAttribute("href")).toBe(`/sites/${CODE}/findings/${FINDING}?from=${encodeURIComponent(FROM)}&to=${encodeURIComponent(TO)}&known_at=${encodeURIComponent(KNOWN)}`);
    expect(rowCells(0)[5]).toBe("Not available yet");
    expect(panelTitled("Cause remains bounded").textContent).toContain("A fault record and abort establish an interruption, not its component cause.");
  });

  it("missing meter: partial energy, meter gap, amber partial outcome", async () => {
    renderEv(SESSIONS, ok(STATES.missingMeter));
    await settledScreen();
    expectV69Panels("sessions");
    const cells = rowCells();
    expect(cells[2]).toBe("30.000 kWh · partial");
    expect(cells[3]).toBe("Completed · energy partial");
    expect(cells[4]).toBe("StartTerminalClockMeter gap: 600 s");
    expect(outcomeBadge().className).toContain("ev-tone--amber");
  });

  it("contradictory: Records disagree, competing end, red tone and the r5 copy", async () => {
    renderEv(SESSIONS, ok(STATES.contradictory));
    await settledScreen();
    expectV69Panels("sessions");
    expect(strip()).toContain("Records disagree");
    expect(strip()).toContain("Accepted terminal records conflict, so a completed outcome is not claimed.");
    const cells = rowCells();
    expect(cells[1]).toBe("08:01 UTC – Competing end records");
    expect(cells[2]).toBe("30.000 kWh · partial");
    expect(cells[3]).toBe("Contradictory");
    expect(cells[4]).toContain("Meter coverage unknown");
    expect(outcomeBadge().className).toContain("ev-tone--red");
  });

  it("contradictory_row_has_no_terminal_chip", async () => {
    renderEv(SESSIONS, ok(STATES.contradictory));
    await settledScreen();
    const chips = Array.from(document.querySelectorAll("tbody tr")[0].querySelectorAll("td")[4].querySelectorAll(".ev-chip")).map((x) => x.textContent);
    expect(chips).toEqual(["Start", "Clock", "Competing end records", "Meter coverage unknown"]);
    expect(chips).not.toContain("Terminal");
    expect(chips).not.toContain("No end record");
  });

  it("empty and orphan: settled zero starts says so, with the orphan context", async () => {
    renderEv(SESSIONS, ok(STATES.empty));
    await settledScreen();
    expectV69Panels("sessions");
    expect(strip()).toContain("No sessions observed");
    const records = panelTitled("Session service records").textContent ?? "";
    expect(records).toContain("No charging sessions were observed in this window.");
    expect(records).toContain("A terminal record has no qualifying start in this window; it is not counted as an attempt.");
    expect(cardValues()).toEqual(["0", "0", "0", "0"]);
    expect(document.querySelector("tbody")).toBeNull();
  });

  it("pending_and_historical_currentness", async () => {
    renderEv(SESSIONS, ok(STATES.pendingLate));
    await settledScreen();
    expectV69Panels("sessions");
    expect(strip()).toContain("Evidence pending");
    expect(strip()).toContain("New evidence is being assessed. The previous result may change.");
    expect(strip()).not.toContain("Sessions observed");
    expect(cardValues()).toEqual(["Pending recompute", "Pending recompute", "Pending recompute", "Pending recompute"]);
    expect(rowCells()[1]).toBe("08:01 UTC – End not recorded");
    expect(rowCells()[4]).toBe("StartMeterClockNo end record");
    cleanup();

    // r7 P7: a pending row with a nonnull Finding link stays visible but offers no Finding anchor.
    const pendingLinked = sessions("PENDING_RECOMPUTE", "OBSERVED_SESSIONS", [INTERRUPTED_ROW], {
      started: 1, completed: 0, observed_abort: 1, fault_aborted: 1, confirmed_delivery: 0,
    });
    renderEv(`${SESSIONS}?from=${FROM}&to=${TO}&known_at=${KNOWN}`, ok(pendingLinked));
    await settledScreen();
    expect(document.querySelectorAll("tbody tr")).toHaveLength(1);
    expect(rowCells()[0]).toContain("S-11");
    expect(rowCells()[5]).toBe("Open Finding · Not available yet");
    expect(document.querySelector("tbody a")).toBeNull();
    expect(screen.queryByRole("link", { name: "Open Finding →" })).toBeNull();
    expect(strip()).toContain("Evidence pending");
    expect(strip()).toContain("New evidence is being assessed. The previous result may change.");
    expect(cardValues()).toEqual(["Pending recompute", "Pending recompute", "Pending recompute", "Pending recompute"]);
    cleanup();

    // A settled current response with the proved link renders it.
    renderEv(`${SESSIONS}?from=${FROM}&to=${TO}&known_at=${KNOWN}`, ok({ ...pendingLinked, ...envelope("CURRENT") }));
    await settledScreen();
    expect(screen.getByRole("link", { name: "Open Finding →" })).not.toBeNull();
    cleanup();

    // A historical response follows only its own selected links.finding.
    const historicalRows = (finding: string | null) => ({
      ...pendingLinked,
      ...envelope("HISTORICAL"),
      items: [{ ...INTERRUPTED_ROW, links: { ...INTERRUPTED_ROW.links, finding } }],
    });
    renderEv(`${SESSIONS}?from=${FROM}&to=${TO}&known_at=${KNOWN}`, ok(historicalRows(INTERRUPTED_ROW.links.finding)));
    await settledScreen();
    expect(screen.getByRole("link", { name: "Open Finding →" })).not.toBeNull();
    cleanup();
    renderEv(`${SESSIONS}?from=${FROM}&to=${TO}&known_at=${KNOWN}`, ok(historicalRows(null)));
    await settledScreen();
    expect(document.querySelector("tbody a")).toBeNull();
    expect(rowCells()[5]).toBe("Not available yet");
    cleanup();

    renderEv(`${SESSIONS}?from=${FROM}&to=${TO}&known_at=${KNOWN}`, ok(STATES.historicalLate));
    await settledScreen();
    expectV69Panels("sessions");
    expect(strip()).toContain("This result reflects records known at the selected cutoff.");
    expect(strip()).toContain("Historical assessment · 6 Oct 09:00 UTC");
    expect(cardValues()).toEqual(["1", "0", "0", "1"]);
    expect(rowCells()[3]).toBe("Incomplete");
    cleanup();

    renderEv(FINDING_PATH, ok(STATES.complete), ok({ ...FINDING_DETAIL, ...envelope("PENDING_RECOMPUTE") }));
    await settledScreen();
    expectV69Panels("ev-finding");
    expect(strip()).toContain("Evidence pending");
    expect(strip()).not.toContain("Observed interruption");
    expect(strip()).toContain("New evidence is being assessed. The previous result may change.");
  });

  it("unknown_selection_has_no_zero_counts", async () => {
    renderEv(SESSIONS, ok(STATES.unknown));
    await settledScreen();
    expectV69Panels("sessions");
    expect(strip()).toContain("Unknown");
    expect(cardValues()).toEqual(["Unknown", "Unknown", "Unknown", "Unknown"]);
    expect(main().textContent).not.toContain("No charging sessions were observed in this window.");
    expect(panelTitled("How to read the denominator").textContent).not.toMatch(/\b0\b/);
    expect(document.querySelector("tbody")).toBeNull();
  });

  it("shows four real rows, then Show all", async () => {
    const many = sessions("CURRENT", "OBSERVED_SESSIONS", [10, 11, 12, 13, 14, 15].map((n) => session(n)), { started: 6, completed: 6, confirmed_delivery: 6 });
    renderEv(SESSIONS, ok(many));
    await settledScreen();
    expect(document.querySelectorAll("tbody tr")).toHaveLength(4);
    fireEvent.click(screen.getByRole("button", { name: "Show all" }));
    expect(document.querySelectorAll("tbody tr")).toHaveLength(6);
  });

  it.each([
    [401, "UNAUTHENTICATED", "Sign in to view EV evidence."],
    [403, "SITE_SCOPE_FORBIDDEN", "You do not have access to this EV evidence."],
    [404, "SITE_NOT_FOUND", "This EV Site or record was not found."],
    [409, "EV_CURSOR_BASIS_CHANGED", "Selection changed. Reload this view."],
    [422, "EV_PARAMETER_UNKNOWN", "Choose a valid UTC start and end, up to 31 days."],
    [503, "EV_READ_UNAVAILABLE", "EV evidence is temporarily unavailable. Retry."],
  ] as const)("refused %s keeps every panel shell", async (status, code, copy) => {
    renderEv(SESSIONS, refused(status, code));
    await settledScreen();
    expectV69Panels("sessions");
    expect(strip()).toContain(copy);
    expect(cardValues()).toEqual(["Unknown", "Unknown", "Unknown", "Unknown"]);
    expect(document.querySelectorAll("[data-panel-gap]")).toHaveLength(3);
    expect(main().textContent).not.toContain("No charging sessions were observed in this window.");
  });

  it("malformed or network failure reads as unavailable", async () => {
    renderEv(SESSIONS, { status: "unavailable", message: null });
    await settledScreen();
    expectV69Panels("sessions");
    expect(strip()).toContain("EV evidence is temporarily unavailable. Retry.");
  });
});

describe("W2-06: ev-finding keeps the v69 panels and the disabled Recommendation slot", () => {
  it("stocked interrupted Finding: exact copy", async () => {
    const client = renderEv(FINDING_PATH, ok(STATES.interrupted));
    await settledScreen();
    expect(main().getAttribute("data-ev-view")).toBe("ev-finding");
    expectV69Panels("ev-finding");
    expectPlantedPanelRejected("ev-finding");
    expect(client.getSession).toHaveBeenCalledWith(CODE, id(11), { from: FROM, to: TO, known_at: KNOWN });
    expect(strip()).toContain(`Finding ${FINDING.slice(0, 8)}`);
    expect(strip()).toContain("Observed interruption");
    const conclusion = panelTitled("Bounded conclusion").textContent ?? "";
    expect(conclusion).toContain("A connector fault and session abort were observed; component cause and unmet demand remain unknown.");
    expect(conclusion).toContain("12.500 kWh delivered before abort · complete meter coverage");
    expect(conclusion).toContain("The records do not establish charger hardware failure, vehicle fault or lost revenue.");
    expect(conclusion).toContain(`Record ${id(150).slice(0, 8)}`);
    expect(conclusion).toContain("No analysis link");
    expect(conclusion).toContain("Analysis view not available for this EV record");
    expect(screen.queryByText("Inspect claim evidence")).toBeNull();
    const context = Array.from(panelTitled("Operational context").querySelectorAll("[data-key-value]")).map((x) => [
      x.querySelector("dt")?.textContent, x.querySelector("dd")?.textContent,
    ]);
    expect(context).toEqual([["Session", "S-11"], ["Connector", "Connector c2"], ["Energy delta", "12.500 kWh"], ["Outcome", "Observed abort"]]);
    const next = panelTitled("Recommended next step");
    expect(next.textContent).toContain("Retrieve charger diagnostics and witness a complete session with start, end and meter records.");
    expect(next.querySelector('[data-link-unavailable="Review recommendation"]')?.textContent).toBe("Review recommendation · Not available yet");
    expect(next.querySelector("a, button")).toBeNull();
    expect(document.querySelector('[data-tab-unavailable="Recommendation"]')).not.toBeNull();
    // r7 P8: live Overview, then the unbuilt Recommendation entry.
    expect(subtabs("Finding sections")).toEqual([["Overview", false], ["Recommendation", true]]);
    expectInert("Recommendation");
    for (const text of ["F-130", "ACT-061", "CHG-002", "$36", "SES-011"]) expect(main().textContent).not.toContain(text);
  });

  it("withdrawn Finding is history, not a supported claim", async () => {
    renderEv(FINDING_PATH, ok(STATES.complete), ok({
      ...FINDING_DETAIL,
      lifecycle: "NO_LONGER_SUPPORTED",
      claim: { ...FINDING_DETAIL.claim, fault_evidence_id: null },
    }));
    await settledScreen();
    expectV69Panels("ev-finding");
    expect(strip()).not.toContain("Observed interruption");
    expect(panelTitled("Bounded conclusion").querySelector("[data-ev-conclusion]")?.getAttribute("data-ev-conclusion")).toBe("limited");
    // r7 P5: the exact withdrawn literal, never the supported claim; the stored limitation stays in details.
    const conclusion = panelTitled("Bounded conclusion");
    expect(conclusion.querySelector("[data-ev-conclusion]")?.textContent).toBe("This finding is no longer supported by the selected evidence.");
    const details = conclusion.querySelector("details") as HTMLElement;
    expect(details.textContent).toContain(FINDING_DETAIL.limitations[0]);
    expect(details.textContent).toContain("NO_LONGER_SUPPORTED");
    expect(details.textContent).toContain(KNOWN);
    expect(conclusion.querySelector("[data-ev-conclusion]")?.textContent).not.toContain("A connector fault and session abort were observed");
  });

  it("supported Finding without the exact START/FAULT/ABORT claim is not an interruption conclusion", async () => {
    renderEv(FINDING_PATH, ok(STATES.complete), ok({
      ...FINDING_DETAIL,
      claim: { ...FINDING_DETAIL.claim, abort_at: null },
      limitations: ["Abort record not selected."],
    }));
    await settledScreen();
    expectV69Panels("ev-finding");
    const claim = panelTitled("Bounded conclusion").querySelector("[data-ev-conclusion]");
    expect(claim?.textContent).toBe("The selected records do not support an interruption conclusion.");
    expect(claim?.getAttribute("data-ev-conclusion")).toBe("limited");
    expect(panelTitled("Bounded conclusion").querySelector("details")?.textContent).toContain("Abort record not selected.");
  });

  it.each([
    [404, "EV_RECORD_NOT_FOUND", "This EV Site or record was not found."],
    [409, "EV_CURSOR_BASIS_CHANGED", "Selection changed. Reload this view."],
    [503, "EV_READ_UNAVAILABLE", "EV evidence is temporarily unavailable. Retry."],
  ] as const)("refused %s keeps the three shells", async (status, code, copy) => {
    renderEv(FINDING_PATH, ok(STATES.complete), refused(status, code));
    await settledScreen();
    expectV69Panels("ev-finding");
    expect(strip()).toContain(copy);
    expect(document.querySelectorAll("[data-panel-gap]")).toHaveLength(3);
  });
});
