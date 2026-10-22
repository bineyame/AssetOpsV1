import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import type { ColdFoundationClient, ColdFoundationRead, ColdFoundationReadModel } from "../coldFoundationClient";
import type { EvidenceRead } from "../evidenceRead";
import type { GatewayHealth, GatewayHealthClient } from "../gatewayHealthClient";
import { createSiteEvidenceClient } from "../siteEvidenceClient";
import type { SiteDetailClient, SiteDirectoryClient } from "../siteDirectoryClient";
import type { FoundationVersionsReadModel, SiteFoundationClient } from "../siteFoundationClient";
import type { SiteDetailReadModel } from "../siteReadModel";
import { EMPTY_ANALYTICS_CLIENT } from "./analyticsFixtures";
import { expectV69Panels, panelTitled, renderedPanelTitles } from "../../test/panelStructure";
import { describeViolations, scanProductVocabulary } from "../../test/productVocabulary";
import { settledScreen } from "../../test/settled";
import { coldDrawingLayout } from "../SiteSingleLineDiagram";

/*
 * W2-01 phase 2: the three Foundation routes of a COLDCHAIN Site render `cold-foundation`,
 * `cold-readiness` and `cold-sld` in the exact v69 panel structure (titles from
 * `docs/architecture/v69-rendered-panels.json` plus the approved cold title rules), in the
 * stocked (COLD-001), missing-probe/no-contact (COLD-002) and refused states.
 */

afterEach(cleanup);

const REV = "rev-cold-1";
const node = (id: string, type: string, role: string, name: string) => ({
  node_id: id,
  component_id: id,
  asset_id: `asset-${id}`,
  component_type: type,
  display_name: name,
  node_role: role,
});
const bind = (role: string, asset: string, unit: string, periodic = true) => ({
  role,
  asset_id: `asset-${asset}`,
  source_id: `source-${role}`,
  unit,
  cadence_seconds: periodic ? 300 : null,
  publication_mode: periodic ? "periodic" : "transition",
});

const BASE_NODES = [
  node("cold-room", "COLD_ROOM", "COLD_ROOM", "Vaccine cold room"),
  node("ambient-probe", "TEMPERATURE_PROBE", "SENSOR", "Ambient temperature probe"),
  node("compressor", "COMPRESSOR", "COOLING", "Refrigeration compressor"),
  node("transfer-switch", "TRANSFER_SWITCH", "SWITCH", "Automatic transfer switch"),
  node("generator", "GENERATOR", "GENERATION", "Backup generator"),
  node("backup-bus", "AC_BUS", "BUS", "Backup AC bus"),
  node("grid-meter", "METER", "METERING", "Grid supply meter"),
];
const BASE_EDGES = [
  { connection_id: "compressor-cools-room", from_node: "compressor", to_node: "cold-room", medium: "THERMAL" },
  { connection_id: "grid-to-transfer", from_node: "grid-meter", to_node: "transfer-switch", medium: "AC" },
  { connection_id: "generator-to-transfer", from_node: "generator", to_node: "transfer-switch", medium: "AC" },
  { connection_id: "transfer-to-bus", from_node: "transfer-switch", to_node: "backup-bus", medium: "AC" },
  { connection_id: "bus-to-compressor", from_node: "backup-bus", to_node: "compressor", medium: "AC" },
];
const BASE_BINDINGS = [
  bind("ambient_temperature", "ambient-probe", "degC"),
  bind("backup_bus_state", "backup-bus", "state"),
  bind("backup_start_event", "generator", "event", false),
  bind("compressor_power", "compressor", "kW"),
  bind("compressor_state", "compressor", "state"),
  bind("door_event", "cold-room", "event", false),
  bind("generator_state", "generator", "state"),
  bind("grid_power_event", "grid-meter", "event", false),
  bind("grid_state", "grid-meter", "state"),
];
const policy = { low: 2, high: 8, unit: "degC", revision_id: REV };

/** COLD-001: complete, every required role bound, recent contact. */
const STOCKED: ColdFoundationReadModel = {
  foundation_revision_id: REV,
  valid_from: "2026-10-01T00:00:00Z",
  valid_to: null,
  rooms: [{ asset_id: "asset-cold-room", policy, probe_ids: ["asset-chamber-probe"], compressor_ids: ["asset-compressor"] }],
  topology: {
    nodes: [...BASE_NODES, node("chamber-probe", "TEMPERATURE_PROBE", "SENSOR", "Chamber temperature probe")],
    edges: [...BASE_EDGES, { connection_id: "room-probe", from_node: "cold-room", to_node: "chamber-probe", medium: "SIGNAL" }],
  },
  bindings: [...BASE_BINDINGS, bind("chamber_temperature", "chamber-probe", "degC"), bind("transfer_result", "transfer-switch", "event", false)],
  readiness: { state: "READY_TO_REPORT", messages: [] },
  commissioning: { state: "UNCONFIRMED", evidence_ids: [] },
  contact: { state: "RECENT", as_of: "2026-10-17T10:00:00Z", limitations: [] },
};

/** COLD-002: no chamber probe and no transfer result; the gateway has never made contact. */
const MISSING_PROBE: ColdFoundationReadModel = {
  ...STOCKED,
  rooms: [{ asset_id: "asset-cold-room", policy, probe_ids: [], compressor_ids: ["asset-compressor"] }],
  topology: { nodes: BASE_NODES, edges: BASE_EDGES },
  bindings: BASE_BINDINGS,
  readiness: {
    state: "CONFIGURATION_INCOMPLETE",
    messages: [
      { code: "PROBE_MISSING", role: "chamber_temperature", component_id: "cold-room", asset_id: "asset-cold-room", message: "Add a chamber temperature probe and bind its °C reading", blocking: true },
      { code: "TRANSFER_UNREPORTED", role: "transfer_result", component_id: null, asset_id: null, message: "Transfer position is not reported; switch state is unknown", blocking: false },
    ],
  },
  contact: { state: "NEVER", as_of: null, limitations: [] },
};

const NO_VERSION: ColdFoundationRead = {
  status: "refused",
  httpStatus: 404,
  code: "FOUNDATION_REVISION_NOT_FOUND",
  message: "No Foundation revision of COLD-001 is effective at 2026-09-01T00:00:00+00:00.",
};

const SITE = {
  site_id: "COLD-001",
  display_name: "Kobo vaccine cold store",
  site_type: "COLDCHAIN",
  location: { country: "Ethiopia", locality: "Kobo" },
  timezone: "Africa/Addis_Ababa",
  lifecycle_status: "PLANNED",
  origin: "USER",
  source: { mode: "SIMULATED" },
  template: null,
  configuration_store: "POSTGRES",
} as unknown as SiteDetailReadModel;

const detail: SiteDetailClient = { getSite: () => Promise.resolve({ status: "loaded", site: SITE }) };
const directory: SiteDirectoryClient = { listSites: () => Promise.resolve({ status: "loaded", sites: [SITE] }) };

const VERSIONS: FoundationVersionsReadModel = {
  server_now: "2026-10-17T11:00:00Z",
  current_revision_id: REV,
  revisions: [
    {
      revision_id: REV,
      version: 1,
      valid_from: "2026-10-01T00:00:00Z",
      valid_to: null,
      recorded_at: "2026-10-01T00:00:00Z",
      superseded_at: null,
      recorded_state: "CURRENT",
      period_state: "CURRENT",
      origin: "IMPORT",
      derived_from_revision_id: null,
      content_sha256: "0".repeat(64),
      change_note: null,
      battery_reserve: null,
    },
  ],
  binding_sets: [],
};

/** The generic Foundation read is not what the cold views draw from; it only lists the versions. */
const genericFoundation: SiteFoundationClient = {
  getFoundation: () => Promise.resolve({ status: "invalid", message: "not used by the cold views" }),
  listVersions: () => Promise.resolve({ status: "loaded", value: VERSIONS }),
  publishReserve: vi.fn(),
  publishBindings: vi.fn(),
  snapshotUrl: () => "",
};

const healthOf = (gateways: string[]): EvidenceRead<GatewayHealth> => ({
  status: "loaded",
  value: {
    site_id: "site-uuid",
    read_at: "2026-10-17T11:00:00Z",
    read_at_clock: "SERVER_REAL_UTC",
    claim_scope: "GATEWAY_OPERATIONAL_REPORT",
    gateways: gateways.map((id) => ({
      gateway_id: `gw-${id}`,
      gateway_external_id: id,
      mode: "SIMULATED",
      registration: "ENABLED",
      declared_cadence_seconds: 60,
      status: "UNKNOWN",
      status_basis: "SERVER_RECEIVED_AT",
      last_server_contact: null,
      diagnostic_id: null,
      gateway_observed_at: null,
      observed_at_clock: "GATEWAY_REAL_UTC",
      queue_count: null,
      oldest_queue_age_seconds: null,
      disk_pressure: null,
      disk_pressure_provenance: null,
      clock_offset_ms: null,
      mapping_error_count: null,
      source_contacts: [],
    })),
  },
});

function Location() {
  const location = useLocation();
  return <output data-testid="location">{location.pathname + location.search}</output>;
}

function renderCold(path: string, read: (at: string | null) => ColdFoundationRead, health: EvidenceRead<GatewayHealth> = healthOf(["edge-cold-001"])) {
  const cold: ColdFoundationClient = { getColdFoundation: vi.fn((_site: string, at: string | null) => Promise.resolve(read(at))) };
  const gatewayHealth: GatewayHealthClient = { getGatewayHealth: vi.fn(() => Promise.resolve(health)) };
  render(
    <MemoryRouter initialEntries={[path]}>
      <App
        flags={featureFlagsWith(false)}
        siteDirectory={directory}
        siteDetail={detail}
        siteAnalytics={EMPTY_ANALYTICS_CLIENT}
        siteFoundation={genericFoundation}
        coldFoundation={cold}
        siteEvidence={{ ...createSiteEvidenceClient(), gatewayHealth }}
      />
      <Location />
    </MemoryRouter>,
  );
  return cold;
}

const loaded = (value: ColdFoundationReadModel) => (): ColdFoundationRead => ({ status: "loaded", value });
const BASE = "/sites/COLD-001/foundation";
const gaps = () => Array.from(document.querySelectorAll("[data-panel-gap]"));
const main = () => document.querySelector("main") as HTMLElement;

describe("W2-01: cold Foundation routes keep the v69 panel structure", () => {
  it.each([
    ["cold-foundation", "", {}],
    ["cold-readiness", "/readiness", { gateway: "edge-cold-001" }],
    ["cold-sld", "/sld", { site: "Kobo vaccine cold store" }],
  ] as const)("stocked COLD-001: %s", async (screenId, segment, values) => {
    renderCold(`${BASE}${segment}`, loaded(STOCKED));
    await settledScreen();
    expectV69Panels(screenId, values);
    expect(document.querySelector("[data-page-refusal]")).toBeNull();
    expect(document.querySelector("[data-headline-card]")).toBeNull();
    expect(main().getAttribute("data-cold-foundation-view")).not.toBeNull();
  });

  it.each([
    ["cold-foundation", "", {}],
    ["cold-readiness", "/readiness", { gateway: "No gateway selected" }],
    ["cold-sld", "/sld", { site: "Kobo vaccine cold store" }],
  ] as const)("missing probe and no contact (COLD-002): %s", async (screenId, segment, values) => {
    renderCold(`${BASE}${segment}`, loaded(MISSING_PROBE), healthOf([]));
    await settledScreen();
    expectV69Panels(screenId, values);
    expect(document.querySelector("[data-page-refusal]")).toBeNull();
  });

  it.each([
    ["cold-foundation", "", {}, 2],
    ["cold-readiness", "/readiness", { gateway: "edge-cold-001" }, 4],
    ["cold-sld", "/sld", { site: "Kobo vaccine cold store" }, 2],
  ] as const)("no stored version at the selected time: %s keeps every slot with an in-panel gap", async (screenId, segment, values, slots) => {
    renderCold(`${BASE}${segment}?at=2026-09-01T00:00:00Z`, () => NO_VERSION);
    await settledScreen();
    expect(document.querySelector('[data-page-refusal="no-version"]')).not.toBeNull();
    expectV69Panels(screenId, values);
    expect(gaps()).toHaveLength(slots);
    for (const gap of gaps()) expect(gap.textContent).toContain("No configuration is stored for the selected time");
  });

  it.each([
    ["cold-foundation", "", {}, 2],
    ["cold-readiness", "/readiness", { gateway: "Gateway not read" }, 4],
    ["cold-sld", "/sld", { site: "Kobo vaccine cold store" }, 2],
  ] as const)("unreadable configuration: %s keeps every slot with an in-panel gap", async (screenId, segment, values, slots) => {
    renderCold(`${BASE}${segment}`, () => ({ status: "unavailable", message: null }), { status: "unavailable", message: null });
    await settledScreen();
    expect(document.querySelector('[data-page-refusal="unavailable"]')).not.toBeNull();
    expectV69Panels(screenId, values);
    expect(gaps()).toHaveLength(slots);
    for (const gap of gaps()) expect(gap.textContent).toContain("could not be read");
  });

  it("links the cold gateway panel to Health Data sources", async () => {
    renderCold(`${BASE}/readiness`, loaded(STOCKED));
    await settledScreen();
    const link = Array.from(panelTitled("Gateway status · edge-cold-001").querySelectorAll("a"))
      .find((a) => a.textContent === "Health › Data sources →");
    expect(link?.getAttribute("href")).toBe("/sites/COLD-001/health#site-health-sources-heading");
  });
});

describe("W2-01: in-panel honest gaps and configuration labels", () => {
  it("Foundation states undeclared parts and unconfigured context inside its panels", async () => {
    renderCold(BASE, loaded(MISSING_PROBE), healthOf([]));
    await settledScreen();
    const physical = panelTitled("Physical site");
    expect(physical.textContent).toContain("Chamber temperature probeNot declared");
    expect(physical.textContent).toContain("Night outage ruleNot configured");
    const operating = panelTitled("Operating interpretation");
    expect(operating.textContent).toContain("2–8 °C");
    expect(operating.textContent).toContain("Product or stock contextNot configured");
    expect(operating.textContent).toContain("Temperature probesNeeds a source");
    expect(operating.textContent).toContain("Door and loading observationsConfigured");
  });

  it("Readiness names the missing probe, unconfirmed commissioning, no selected gateway and unknown confidence", async () => {
    const noneSelected: ColdFoundationReadModel = {
      ...MISSING_PROBE,
      contact: { state: "NEVER", as_of: null, limitations: ["No gateway is selected for this site"] },
    };
    renderCold(`${BASE}/readiness`, loaded(noneSelected), healthOf([]));
    await settledScreen();
    const table = panelTitled("Readiness and commissioning evidence");
    const probeRow = table.querySelector('[data-cold-readiness-row="chamber"]') as HTMLElement;
    expect(probeRow.textContent).toContain("Needs a source");
    expect(probeRow.textContent).toContain("Add a chamber temperature probe and bind its °C reading");
    expect(table.querySelector('[data-cold-readiness-row="transfer"]')?.textContent).toContain("Transfer position is not reported");
    const doorRow = table.querySelector('[data-cold-readiness-row="door"]') as HTMLElement;
    expect(doorRow.textContent).toContain("Configured");
    // Review Low 3: a Configured row never also says "No source"; the optional manual log has its own row.
    expect(doorRow.textContent).not.toMatch(/No source|Manual temperature/);
    const manualRow = table.querySelector('[data-cold-readiness-row="manual"]') as HTMLElement;
    expect(manualRow.querySelector("th")?.textContent).toBe("Manual temperature log");
    expect(manualRow.textContent).toContain("Needs a source");
    expect(manualRow.textContent).toContain("Optional");
    for (const row of Array.from(table.querySelectorAll("[data-cold-readiness-row]"))) {
      if (row.textContent?.includes("Configured") && !row.textContent.includes("Not configured")) expect(row.textContent).not.toMatch(/No source/);
    }
    expect(table.querySelector('[data-cold-readiness-row="transfer"]')?.textContent).toContain("Needs a source");
    expect(table.textContent).toContain("Unconfirmed");
    expect(table.textContent).toContain("Set-up incomplete: 1 required item needs attention");
    const gateway = panelTitled("Gateway status · No gateway selected");
    // D-2026-10-17-f5-subtabs-and-contact: with no gateway selected it never says a particular gateway was not contacted.
    const status = gateway.querySelector('[data-cold-gateway-metric="status"]')?.textContent ?? "";
    expect(status).toContain("No gateway selected");
    expect(status).not.toMatch(/Never contacted|No contact received yet/);
    // Review Low 5: the mock's availability timeline is kept as an empty track that says it has no history.
    const timeline = gateway.querySelector("[data-cold-gateway-timeline]") as HTMLElement;
    expect(timeline.querySelector("[data-cold-timeline-gap]")?.textContent).toBe("No history to draw");
    expect(timeline.querySelector(".cold-gw-key--up, .cold-gw-key--part, .cold-gw-key--down")?.closest(".cold-gw-track")).toBeNull();
    expect(timeline.textContent).toContain("Short outage or missing readings");
    expect(panelTitled("Connected sources").textContent).toContain("Source contact unavailable");
    expect(panelTitled("Effect on readiness and confidence").textContent).toContain("Confidence is not assessed");
  });

  it("W2-01 re-review Low 2: the status follows the cold read, not an empty or failed frontend health read", async () => {
    // Registered gateway with no diagnostic (limitations []): the backend says no contact yet; an empty
    // /gateway-health read must not turn that into "No gateway selected".
    renderCold(`${BASE}/readiness`, loaded(MISSING_PROBE), healthOf([]));
    await settledScreen();
    const status = document.querySelector('[data-cold-gateway-metric="status"]')?.textContent ?? "";
    expect(status).toContain("No contact received yet");
    expect(status).not.toContain("No gateway selected");
    cleanup();
    renderCold(`${BASE}/readiness`, loaded(MISSING_PROBE), { status: "unavailable", message: null });
    await settledScreen();
    expect(panelTitled("Gateway status · Gateway not read")).not.toBeNull();
    const failed = document.querySelector('[data-cold-gateway-metric="status"]')?.textContent ?? "";
    expect(failed).toContain("No contact received yet");
  });

  it.each([
    ["no gateway health read (missing store)", ["No gateway health read is configured"], "No contact recorded",
      "Gateway contact is not read here, so no contact time is shown"],
    ["no diagnostic for the selected gateway (unmatched)", ["No diagnostic is recorded for the selected gateway"],
      "No contact received yet", "No gateway diagnostic has been received"],
  ] as const)("contact null closure: %s reads NEVER with no time and distinct wording", async (_case, limitations, value, note) => {
    const read = { ...STOCKED, contact: { state: "NEVER", as_of: null, limitations: [...limitations] } };
    renderCold(`${BASE}/readiness`, loaded(read));
    await settledScreen();
    const status = panelTitled("Gateway status · edge-cold-001").querySelector('[data-cold-gateway-metric="status"]') as HTMLElement;
    expect(status.textContent).toContain(value);
    expect(status.textContent).toContain(note);
    expect(status.textContent).not.toMatch(/Recent contact|Contact stale|Last contact|Never contacted|Contact unknown/);
  });

  it("the single line diagram draws only configured parts and labels the undeclared ones and the unknown function", async () => {
    renderCold(`${BASE}/sld`, loaded(MISSING_PROBE), healthOf([]));
    await settledScreen();
    const diagram = panelTitled("Kobo vaccine cold store");
    expect(diagram.querySelectorAll("[data-cold-node]")).toHaveLength(7);
    expect(diagram.querySelectorAll("[data-cold-edge]")).toHaveLength(5);
    expect(diagram.textContent).toContain("Undeclared in this version: chamber temperature probe, solar array, battery.");
    const parts = panelTitled("What each part does");
    expect(parts.querySelectorAll("[data-cold-part]")).toHaveLength(7);
    // Review M2: the unknown function is stated once, in the footnote, never per row.
    expect((parts.textContent ?? "").split("Function description not recorded")).toHaveLength(2);
    expect(parts.querySelector("tbody")?.textContent).not.toMatch(/Function description|\(configured\)/);
  });

  it("draws the bus-bar single line diagram with icons, wrapped names and the monitoring strip (review H1)", async () => {
    renderCold(`${BASE}/sld`, loaded(STOCKED), healthOf([]));
    await settledScreen();
    const diagram = panelTitled("Kobo vaccine cold store");
    expect(diagram.querySelectorAll(".sld-node__bar")).toHaveLength(1);
    const icons = Array.from(diagram.querySelectorAll("[data-component-icon]")).map((el) => el.getAttribute("data-component-icon"));
    for (const symbol of ["COLD_ROOM", "TEMPERATURE_PROBE", "COMPRESSOR", "TRANSFER_SWITCH", "GENERATOR", "METER"]) expect(icons).toContain(symbol);
    const svgText = Array.from(diagram.querySelectorAll("svg text")).map((t) => t.textContent ?? "");
    expect(svgText.join("|")).not.toContain("…");
    expect(svgText).toContain("Chamber temperatureprobe");
    expect(svgText).toContain("Automatic transferswitch");
    const monitor = diagram.querySelector("[data-cold-monitoring]") as HTMLElement;
    expect(monitor.querySelectorAll("[data-cold-monitor]")).toHaveLength(STOCKED.bindings.length);
    for (const box of Array.from(monitor.querySelectorAll("[data-cold-monitor]"))) {
      expect(box.getAttribute("title")).toBe("Reporting not assessed here");
      expect(box.querySelector(".gw-dot--none")).not.toBeNull();
    }
    expect(diagram.textContent).toContain("Reporting not assessed here");
    expect(diagram.querySelector(".gw-dot:not(.gw-dot--none)")).toBeNull();
  });

  it("places supplies and the switch left of the bus bar and the cooling chain right of it", () => {
    const layout = coldDrawingLayout(STOCKED.topology!.nodes, STOCKED.topology!.edges);
    const bus = layout.busX.get("backup-bus") as number;
    const x = (id: string) => layout.position.get(id)!.x;
    const y = (id: string) => layout.position.get(id)!.y;
    for (const id of ["grid-meter", "generator", "transfer-switch"]) expect(x(id)).toBeLessThan(bus);
    expect(x("grid-meter")).toBeLessThan(x("transfer-switch"));
    expect(bus).toBeLessThan(x("compressor"));
    expect(x("compressor")).toBeLessThan(x("cold-room"));
    expect(x("cold-room")).toBeLessThan(x("chamber-probe"));
    expect(y("compressor")).toBe(y("cold-room"));
    expect(y("cold-room")).toBe(y("chamber-probe"));
    expect(y("ambient-probe")).toBeGreaterThan(y("chamber-probe"));
    expect(y("grid-meter")).toBeLessThan(y("transfer-switch"));
    expect(y("transfer-switch")).toBeLessThan(y("generator"));
  });

  it("uses Configured and Needs a source, never Mapped or Not mapped, and keeps the W1 vocabulary on every route", async () => {
    for (const [segment, read] of [["", STOCKED], ["/readiness", MISSING_PROBE], ["/sld", STOCKED]] as const) {
      renderCold(`${BASE}${segment}`, loaded(read));
      await settledScreen();
      const text = main().textContent ?? "";
      expect(text).not.toMatch(/\bmapped\b/i);
      expect(text).toMatch(/Configured/);
      const result = scanProductVocabulary(main(), `cold${segment || "-foundation"}`, { set: "w1" });
      expect(result.scanned).toBeGreaterThan(5);
      expect(describeViolations(result.violations)).toBe("");
      cleanup();
    }
  });

  it("keeps exact IDs in contextual detail, not in the default reading", async () => {
    renderCold(`${BASE}/readiness`, loaded(STOCKED));
    await settledScreen();
    const references = Array.from(document.querySelectorAll("[data-exact-references]"));
    expect(references.length).toBeGreaterThan(0);
    for (const details of references) expect((details as HTMLDetailsElement).open).toBe(false);
    expect(references.some((d) => d.textContent?.includes(REV))).toBe(true);
    expect(renderedPanelTitles().join("|")).not.toContain(REV);
  });
});

describe("W2-01: the selected time drives the read and survives reload", () => {
  it("asks for the selected time and returns to the version in effect now", async () => {
    const cold = renderCold(`${BASE}?at=2026-09-01T00:00:00Z`, (at) => (at === null ? { status: "loaded", value: STOCKED } : NO_VERSION));
    await settledScreen();
    expect(cold.getColdFoundation).toHaveBeenLastCalledWith("COLD-001", "2026-09-01T00:00:00Z");
    fireEvent.click(screen.getByRole("button", { name: "Show the version in effect now" }));
    await settledScreen();
    expect(cold.getColdFoundation).toHaveBeenLastCalledWith("COLD-001", null);
    expect(screen.getByTestId("location").textContent).toBe(BASE);
    expectV69Panels("cold-foundation");
  });

  it("a MINIGRID-typed Site never reaches the cold views", async () => {
    const minigrid = { ...SITE, site_type: "MINIGRID" } as SiteDetailReadModel;
    const cold: ColdFoundationClient = { getColdFoundation: vi.fn() };
    render(
      <MemoryRouter initialEntries={[`${BASE}/sld`]}>
        <App
          flags={featureFlagsWith(false)}
          siteDirectory={directory}
          siteDetail={{ getSite: () => Promise.resolve({ status: "loaded", site: minigrid }) }}
          siteAnalytics={EMPTY_ANALYTICS_CLIENT}
          siteFoundation={genericFoundation}
          coldFoundation={cold}
        />
      </MemoryRouter>,
    );
    await settledScreen();
    expect(cold.getColdFoundation).not.toHaveBeenCalled();
    expect(document.querySelector("[data-cold-foundation-view]")).toBeNull();
  });
});

/*
 * W2-F unit 3 (`.agent/W2-F-build-spec.md` ledger M2, closure N3): What is needed lists the selected readiness message
 * first, then `Commissioning record` while no commissioning evidence is stored; `Nothing further recorded` only for a
 * configured row with nothing left.
 */
describe("W2-F: cold readiness What is needed", () => {
  const needed = (key: string) => {
    const cell = panelTitled("Readiness and commissioning evidence").querySelector(`[data-cold-readiness-row="${key}"]`)!.querySelectorAll("td")[2] as Element;
    const items = Array.from(cell.querySelectorAll("li")).map((li) => li.textContent);
    return items.length === 0 ? cell.textContent : items;
  };
  const CONFIRMED = { state: "CONFIRMED", evidence_ids: ["commissioning-cold-1"] } as unknown as ColdFoundationReadModel["commissioning"];

  it("w2f_unconfirmed_needs_commissioning", async () => {
    renderCold(`${BASE}/readiness`, loaded(STOCKED));
    await settledScreen();
    const keys = Array.from(document.querySelectorAll("[data-cold-readiness-row]")).map((r) => r.getAttribute("data-cold-readiness-row")!);
    expect(keys.length).toBeGreaterThan(5);
    for (const key of keys) expect(needed(key)).toEqual(["Commissioning record"]);
    cleanup();
    renderCold(`${BASE}/readiness`, loaded(MISSING_PROBE));
    await settledScreen();
    const chamber = needed("chamber") as string[];
    expect(chamber[0]).toContain("Add a chamber temperature probe");
    expect(chamber.at(-1)).toBe("Commissioning record");
    expect(chamber).toHaveLength(2);
    cleanup();
    renderCold(`${BASE}/readiness`, loaded({ ...MISSING_PROBE, commissioning: CONFIRMED }));
    await settledScreen();
    expect(needed("chamber")).toEqual([chamber[0]]);
    cleanup();
    renderCold(`${BASE}/readiness`, loaded({ ...STOCKED, commissioning: CONFIRMED }));
    await settledScreen();
    expect(needed("chamber")).toBe("Nothing further recorded");
    expect(needed("definition")).toBe("Nothing further recorded");
    // An unconfigured optional reading is not called complete.
    expect(needed("manual")).toBe("—");
  });
});
