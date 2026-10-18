import { cleanup, render, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import type { EvFoundationClient, EvFoundationRead, EvFoundationReadModel } from "../evFoundationClient";
import type { EvidenceRead } from "../evidenceRead";
import type { GatewayHealth, GatewayHealthClient } from "../gatewayHealthClient";
import { createSiteEvidenceClient } from "../siteEvidenceClient";
import { isSiteDetail, type SiteDetailClient, type SiteDirectoryClient } from "../siteDirectoryClient";
import type { FoundationVersionsReadModel, SiteFoundationClient } from "../siteFoundationClient";
import type { SiteDetailReadModel } from "../siteReadModel";
import { EMPTY_ANALYTICS_CLIENT } from "./analyticsFixtures";
import { expectPlantedPanelRejected, expectV69Panels, panelTitled, renderedPanelTitles } from "../../test/panelStructure";
import { describeViolations, scanProductVocabulary } from "../../test/productVocabulary";
import { settledScreen } from "../../test/settled";
import { expectUnavailableEntry } from "../../test/unavailableEntry";

/*
 * W2-05a commit 4: the three Foundation routes of an EV_CHARGING Site render `ev-foundation`, `ev-readiness`
 * and `ev-sld` in the exact v69 panel structure (titles from `docs/architecture/v69-rendered-panels.json` plus
 * the approved EV title rules), in the stocked (EV-LAB-001 shape), missing-role, empty-selection, 403 and 503
 * states. Values follow the selected read (`GET /api/sites/{code}/ev/foundation`), never mock fixture numbers.
 */

afterEach(cleanup);

const REV = "rev-ev-1";
const BREV = "bind-ev-1";
const GW = "gw-uuid-1";
const node = (id: string, type: string, role: string, name: string) => ({
  node_id: `n-${id}`,
  component_id: id,
  asset_id: `asset-${id}`,
  component_type: type,
  display_name: name,
  node_role: role,
});
const bind = (role: string, asset: string, device: string, signal: string, unit: string, cadence: number | null) => ({
  role,
  asset_id: `asset-${asset}`,
  source_id: `source-${device}`,
  device_id: device,
  signal_id: signal,
  unit,
  cadence_seconds: cadence,
  effective_from: "2026-10-01T00:00:00Z",
  effective_to: null,
});
const schedule = (enabled: boolean, weekly = [{ weekday: "TUESDAY", local_start: "08:00", local_end: "16:00", utc_offset_minutes: 0 }]) => ({
  enabled,
  time_zone: "Etc/UTC",
  weekly: enabled ? weekly : [],
});
const connector = (id: string, clock = "30") => ({
  asset_id: `asset-${id}`,
  max_kw: "60",
  enabled_schedule: schedule(true),
  meter_resolution_kwh: "0.001",
  meter_error_bound_kwh: "0.001",
  clock_error_bound_seconds: clock,
});
const connectorBindings = (c: string) => [
  bind("ev_session_event", c, `${c}-charger-controller`, "session-event", "event", null),
  bind("ev_connector_fault", c, `${c}-connector-controller`, "fault-event", "event", null),
  bind("ev_connector_state", c, `${c}-connector-controller`, "state", "state", 60),
  bind("ev_connector_energy", c, `${c}-connector-meter`, "energy", "kWh", 300),
  bind("ev_connector_power", c, `${c}-connector-meter`, "power", "kW", 300),
];

const STOCKED: EvFoundationReadModel = {
  site_id: "site-uuid",
  site_code: "EV-LAB-001",
  site_type: "EV_CHARGING",
  selected_at: "2026-10-06T12:00:00Z",
  foundation_revision_id: REV,
  binding_revision_id: BREV,
  feed: { asset_id: "asset-feed-1", limit_kw: "80", meter_asset_id: "asset-site-meter-1" },
  chargers: [{ asset_id: "asset-charger-1", max_kw: "60", connectors: [connector("c1"), connector("c2")] }],
  topology: {
    nodes: [
      node("feed-1", "AC_BUS", "BUS", "Site feed"),
      node("site-meter-1", "METER", "METERING", "Site import meter"),
      node("charger-1", "EV_CHARGER", "CHARGER", "Charger 1"),
      node("c1", "EV_CONNECTOR", "CONNECTOR", "Connector c1"),
      node("c2", "EV_CONNECTOR", "CONNECTOR", "Connector c2"),
    ],
    edges: [
      { connection_id: "feed-meter", from_node: "n-feed-1", to_node: "n-site-meter-1", medium: "AC" },
      { connection_id: "meter-charger", from_node: "n-site-meter-1", to_node: "n-charger-1", medium: "AC" },
      { connection_id: "charger-c1", from_node: "n-charger-1", to_node: "n-c1", medium: "SIGNAL" },
      { connection_id: "charger-c2", from_node: "n-charger-1", to_node: "n-c2", medium: "SIGNAL" },
    ],
  },
  bindings: [...connectorBindings("c1"), ...connectorBindings("c2"), bind("ev_site_import", "site-meter-1", "site-meter", "import", "kW", 300)],
  readiness: {
    state: "READY_TO_REPORT",
    messages: [{ code: "COMMISSIONING_UNCONFIRMED", role: null, component_id: null, asset_id: null, message: "Commissioning unconfirmed.", blocking: false }],
  },
  contact: { state: "RECENT", as_of: "2026-10-17T11:55:00Z", checked_at: "2026-10-17T12:00:00Z", gateway_id: GW, reason: null },
  commissioning: { state: "UNCONFIRMED", evidence_ids: [] },
};

/** A later binding revision without c2's status channel, no Site import, no limit, and no gateway contact. */
const MISSING_ROLE: EvFoundationReadModel = {
  ...STOCKED,
  feed: { ...STOCKED.feed, limit_kw: null },
  bindings: STOCKED.bindings.filter((b) => !(b.role === "ev_connector_state" && b.asset_id === "asset-c2") && b.role !== "ev_site_import"),
  readiness: {
    state: "CONFIGURATION_INCOMPLETE",
    messages: [
      { code: "FEED_OR_LIMIT_MISSING", role: null, component_id: "feed-1", asset_id: "asset-feed-1", message: "Site import limit not declared.", blocking: true },
      { code: "STATUS_NOT_BOUND", role: "ev_connector_state", component_id: "c2", asset_id: "asset-c2", message: "Connector c2 has no ev_connector_state binding.", blocking: true },
      { code: "SITE_IMPORT_NOT_BOUND", role: "ev_site_import", component_id: null, asset_id: null, message: "Site import is not bound; site power comparison is unavailable.", blocking: false },
      { code: "SOURCE_NOT_CONTACTED", role: null, component_id: null, asset_id: null, message: "No gateway contact recorded.", blocking: false },
      { code: "COMMISSIONING_UNCONFIRMED", role: null, component_id: null, asset_id: null, message: "Commissioning unconfirmed.", blocking: false },
    ],
  },
  contact: { state: "NEVER", as_of: null, checked_at: "2026-10-17T12:00:00Z", gateway_id: GW, reason: "No diagnostic is recorded for the selected gateway" },
};

const NO_VERSION: EvFoundationRead = { status: "refused", httpStatus: 404, code: "FOUNDATION_REVISION_NOT_FOUND", message: "No Foundation revision." };
const FORBIDDEN_READ: EvFoundationRead = { status: "refused", httpStatus: 403, code: "SITE_SCOPE_FORBIDDEN", message: "No access to Site 'EV-LAB-001'." };
const UNAVAILABLE_READ: EvFoundationRead = { status: "refused", httpStatus: 503, code: "EV_FOUNDATION_UNAVAILABLE", message: "store down" };

const SITE = {
  site_id: "EV-LAB-001",
  display_name: "EV charging lab",
  site_type: "EV_CHARGING",
  location: { country: "Ethiopia", locality: "Addis Ababa" },
  timezone: "Etc/UTC",
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

const genericFoundation: SiteFoundationClient = {
  getFoundation: () => Promise.resolve({ status: "invalid", message: "not used by the EV views" }),
  listVersions: () => Promise.resolve({ status: "loaded", value: VERSIONS }),
  publishReserve: vi.fn(),
  publishBindings: vi.fn(),
  snapshotUrl: () => "",
};

const HEALTH: EvidenceRead<GatewayHealth> = {
  status: "loaded",
  value: {
    site_id: "site-uuid",
    read_at: "2026-10-17T12:00:00Z",
    read_at_clock: "SERVER_REAL_UTC",
    claim_scope: "GATEWAY_OPERATIONAL_REPORT",
    gateways: [
      {
        gateway_id: GW,
        gateway_external_id: "edge-ev-001",
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
      },
    ],
  },
} as unknown as EvidenceRead<GatewayHealth>;

function renderEv(path: string, read: (at: string | null) => EvFoundationRead, health: EvidenceRead<GatewayHealth> = HEALTH) {
  const ev: EvFoundationClient = { getEvFoundation: vi.fn((_site: string, at: string | null) => Promise.resolve(read(at))) };
  const gatewayHealth: GatewayHealthClient = { getGatewayHealth: vi.fn(() => Promise.resolve(health)) };
  render(
    <MemoryRouter initialEntries={[path]}>
      <App
        flags={featureFlagsWith(false)}
        siteDirectory={directory}
        siteDetail={detail}
        siteAnalytics={EMPTY_ANALYTICS_CLIENT}
        siteFoundation={genericFoundation}
        evFoundation={ev}
        siteEvidence={{ ...createSiteEvidenceClient(), gatewayHealth }}
      />
    </MemoryRouter>,
  );
  return ev;
}

const loaded = (value: EvFoundationReadModel) => (): EvFoundationRead => ({ status: "loaded", value });
const BASE = "/sites/EV-LAB-001/foundation";
const SITE_NAME = "EV charging lab";
const gaps = () => Array.from(document.querySelectorAll("[data-panel-gap]"));
const main = () => document.querySelector("main") as HTMLElement;
/** Visible reading text: closed exact-reference disclosures are contextual detail, not the default reading. */
const text = (el: Element) => {
  const copy = el.cloneNode(true) as Element;
  copy.querySelectorAll("[data-exact-references]").forEach((d) => d.remove());
  return (copy.textContent ?? "").replace(/\s+/g, " ");
};

/** `expectPlantedPanelRejected` for a route with a dynamic title: a planted panel before panel 1 must fail. */
function expectPlantRejected(screenId: string, values: Record<string, string>) {
  const first = document.querySelector("main section.panel");
  expect(first).not.toBeNull();
  const plant = document.createElement("section");
  plant.className = "panel";
  plant.innerHTML = "<h2>Planted extra panel</h2>";
  first!.parentElement!.insertBefore(plant, first);
  try {
    expect(() => expectV69Panels(screenId, values)).toThrow();
  } finally {
    plant.remove();
  }
  expectV69Panels(screenId, values);
}

const ROUTES = [
  ["ev-foundation", "", {}],
  ["ev-readiness", "/readiness", { gateway: "edge-ev-001" }],
  ["ev-sld", "/sld", { site: SITE_NAME }],
] as const;

describe("W2-05a: EV Foundation routes keep the v69 panel structure", () => {
  it.each(ROUTES)("stocked: %s, and a planted extra panel is rejected", async (screenId, segment, values) => {
    renderEv(`${BASE}${segment}`, loaded(STOCKED));
    await settledScreen();
    expectV69Panels(screenId, values);
    expect(document.querySelector("[data-page-refusal]")).toBeNull();
    expect(main().getAttribute("data-ev-foundation-view")).not.toBeNull();
    if (screenId === "ev-foundation") expectPlantedPanelRejected(screenId);
    else expectPlantRejected(screenId, values);
  });

  it.each([
    ["ev-foundation", "", {}],
    ["ev-readiness", "/readiness", { gateway: "edge-ev-001" }],
    ["ev-sld", "/sld", { site: SITE_NAME }],
  ] as const)("missing role, limit and contact: %s", async (screenId, segment, values) => {
    renderEv(`${BASE}${segment}`, loaded(MISSING_ROLE));
    await settledScreen();
    expectV69Panels(screenId, values);
    expect(document.querySelector("[data-page-refusal]")).toBeNull();
  });

  it.each([
    ["empty", () => NO_VERSION, "No EV Foundation for this selection"],
    ["forbidden", () => FORBIDDEN_READ, "Source details are not available for this Site"],
    ["unavailable", () => UNAVAILABLE_READ, "EV Foundation is temporarily unavailable"],
  ] as const)("%s read keeps every slot of every route with an in-panel gap", async (kind, read, copy) => {
    for (const [screenId, segment, values, slots] of [
      ["ev-foundation", "", {}, 2],
      ["ev-readiness", "/readiness", { gateway: "Gateway not read" }, 4],
      ["ev-sld", "/sld", { site: SITE_NAME }, 2],
    ] as const) {
      renderEv(`${BASE}${segment}?at=2026-09-01T00:00:00Z`, read);
      await settledScreen();
      expect(document.querySelector(`[data-page-refusal="${kind}"]`)).not.toBeNull();
      expect(text(main())).toContain(copy);
      expectV69Panels(screenId, values);
      expect(gaps()).toHaveLength(slots);
      for (const gap of gaps()) expect(gap.textContent).toContain(copy);
      cleanup();
    }
  });

  it("403 shows no identifiers; 503 offers a retry and never looks like an empty configuration", async () => {
    renderEv(`${BASE}/readiness`, () => FORBIDDEN_READ);
    await settledScreen();
    expect(text(main())).not.toContain("SITE_SCOPE_FORBIDDEN");
    expect(document.querySelector("[data-exact-references]")).toBeNull();
    cleanup();
    const ev = renderEv(`${BASE}`, () => UNAVAILABLE_READ);
    await settledScreen();
    expect(text(main())).not.toContain("No EV Foundation for this selection");
    const retry = within(main()).getByRole("button", { name: "Try again" });
    retry.click();
    await settledScreen();
    expect(ev.getEvFoundation).toHaveBeenCalledTimes(2);
  });
});

describe("W2-05a: every mock row, column and chip is bound or shows its honest gap", () => {
  it("ev-foundation keeps the mock rows with selected values and supporting detail", async () => {
    renderEv(BASE, loaded(STOCKED));
    await settledScreen();
    const physical = panelTitled("Physical site");
    const rows = Array.from(physical.querySelectorAll(".v69-key-values dt")).map((dt) => dt.textContent);
    expect(rows).toEqual(["Site ID", "Connectors", "Site import limit", "Stationary storage", "Session source"]);
    expect(text(physical)).toContain("EV-LAB-001");
    expect(text(physical)).toContain("2 × 60 kW");
    expect(text(physical)).toContain("80 kW");
    expect(text(physical)).toContain("Not declared");
    expect(text(physical)).toContain("Charger session events · 2 of 2 connectors");
    expect(text(physical)).toContain("Site feed → Site import meter → Charger 1 60 kW → 2 connectors");
    expect(text(physical)).toContain("Tuesday 08:00–16:00 (Etc/UTC); a service window is not observed availability");
    const operating = panelTitled("Operating interpretation");
    expect(Array.from(operating.querySelectorAll(".v69-key-values dt")).map((dt) => dt.textContent)).toEqual([
      "Session identity mapping",
      "Transaction completeness",
      "Connector status",
      "Revenue assumption",
    ]);
    expect(text(operating)).toContain("Not assessed");
    expect(text(operating)).toContain("Mapped");
    expect(text(operating)).toContain("Configured clock error bound: 30 s; not an observed clock check");
    expect(text(operating)).toContain("No tariff set for estimates");
    // No mock fixture numbers.
    expect(text(main())).not.toMatch(/EV-DEMO-01|\$0\.30|GW-EV-01/);
  });

  it("ev-foundation states the missing limit and the missing session source in their own rows", async () => {
    const noSessions: EvFoundationReadModel = { ...MISSING_ROLE, bindings: MISSING_ROLE.bindings.filter((b) => b.role !== "ev_session_event") };
    renderEv(BASE, loaded(noSessions));
    await settledScreen();
    const physical = panelTitled("Physical site");
    expect(text(physical)).toContain("Site import limit not declared");
    expect(text(physical)).toContain("Session sourceNeeds a source");
    expect(text(panelTitled("Operating interpretation"))).toContain("Needs a source");
  });

  it("ev-readiness keeps the five columns, the four mock rows and the gateway, source and attention slots", async () => {
    renderEv(`${BASE}/readiness`, loaded(STOCKED));
    await settledScreen();
    const table = panelTitled("Readiness and commissioning evidence");
    expect(Array.from(table.querySelectorAll("thead th")).map((th) => th.textContent)).toEqual(["Area", "Declared", "Confirmed", "What is needed", "Next step"]);
    expect(Array.from(table.querySelectorAll("tbody th")).map((th) => th.textContent)).toEqual([
      "Connectors and site limit",
      "Connector status points",
      "Billing integration",
      "Tariff",
    ]);
    expect(text(table)).toContain("2 × 60 kW · 80 kW");
    expect(text(table)).toContain("Mapped");
    expect(text(table)).toContain("Unconfirmed");
    expect(text(table)).toContain("Commissioning unconfirmed");
    expect(text(table)).toContain("Not connected");
    expect(text(table)).toContain("No tariff set for estimates");
    const gateway = panelTitled("Gateway status · edge-ev-001");
    const metrics = Array.from(gateway.querySelectorAll("[data-ev-gateway-metric]")).map((m) => m.getAttribute("data-ev-gateway-metric"));
    expect(metrics).toEqual(["status", "availability", "completeness", "clock"]);
    expect(text(gateway)).toContain("Recent contact");
    expect(text(gateway)).toContain("Contact checked 2026-10-17 12:00 UTC");
    expect(text(gateway)).toContain("configuration selected 2026-10-06 12:00 UTC");
    expect(text(gateway)).toContain("Configured clock error bound: 30 s");
    expect(text(gateway)).toContain("observed sync and delivery speed not assessed");
    expect(text(gateway)).not.toContain("No gateway contact recorded");
    expect(gateway.querySelector("[data-ev-timeline-gap]")).not.toBeNull();
    const sources = panelTitled("Connected sources");
    expect(sources.querySelectorAll("[data-ev-source]")).toHaveLength(STOCKED.bindings.length + 1);
    expect(text(sources)).toContain("Billing system · Not connected");
    expect(text(sources)).toContain("Source contact unavailable");
    expect(text(sources)).toContain("firmware not assessed");
    expect(sources.querySelector(".gw-dot--good, .gw-dot--gap")).toBeNull();
    const effect = panelTitled("Effect on readiness and confidence");
    const items = effect.querySelectorAll("[data-attention-item]");
    expect(items).toHaveLength(2);
    for (const item of Array.from(items)) expect(text(item)).toContain("Not assessed");
    expectUnavailableEntry(items[1] as HTMLElement, "Investigation action");
    expect(text(main())).not.toMatch(/SES-012|connector 2 went silent/i);
  });

  it("ev-readiness names missing roles in plain words and keeps the never-contacted notice nonblocking", async () => {
    renderEv(`${BASE}/readiness`, loaded(MISSING_ROLE));
    await settledScreen();
    const table = panelTitled("Readiness and commissioning evidence");
    expect(text(table)).toContain("Site import limit not declared");
    expect(text(table)).toContain("Needs a source: connector status for Connector c2");
    expect(text(table)).toContain("Needs a source: site import power (optional)");
    // QO: exactly the four mock rows; gaps are supporting detail in rows 1 and 2.
    const rows = Array.from(table.querySelectorAll("tbody tr"));
    expect(rows.map((r) => r.querySelector("th")?.textContent)).toEqual(["Connectors and site limit", "Connector status points", "Billing integration", "Tariff"]);
    expect(text(rows[0] as Element)).toContain("Needs a source: site import power (optional)");
    expect(text(rows[1] as Element)).toContain("Needs a source: connector status for Connector c2");
    expect(text(table)).not.toMatch(/ev_connector_state|STATUS_NOT_BOUND/);
    const gateway = panelTitled("Gateway status · edge-ev-001");
    expect(text(gateway)).toContain("No gateway contact recorded");
    expect(text(gateway)).toContain("This does not block set-up to report");
    expect(document.querySelector("[data-ev-strip]")?.textContent).toContain("Set-up incomplete");
  });

  it("stale contact is labelled stale, without the never-contacted notice", async () => {
    renderEv(`${BASE}/readiness`, loaded({ ...STOCKED, contact: { ...STOCKED.contact, state: "STALE", as_of: "2026-10-17T10:00:00Z" } }));
    await settledScreen();
    const gateway = panelTitled("Gateway status · edge-ev-001");
    expect(text(gateway)).toContain("Stale contact");
    expect(text(gateway)).toContain("That is not a charger failure");
    expect(text(gateway)).not.toContain("No gateway contact recorded");
  });

  it("no selected gateway is stated in the dynamic title; per-connector clock bounds differ", async () => {
    const differing: EvFoundationReadModel = {
      ...STOCKED,
      chargers: [{ ...STOCKED.chargers[0]!, connectors: [connector("c1"), connector("c2", "45")] }],
      contact: { ...STOCKED.contact, gateway_id: null },
    };
    renderEv(`${BASE}/readiness`, loaded(differing));
    await settledScreen();
    expectV69Panels("ev-readiness", { gateway: "No gateway selected" });
    expect(text(main())).toContain("Configured clock error bound: Connector c1 30 s, Connector c2 45 s");
  });

  it("ev-sld keeps the diagram slots, unknown dots and the parts table, with no live flow", async () => {
    renderEv(`${BASE}/sld`, loaded(STOCKED));
    await settledScreen();
    const diagram = panelTitled(SITE_NAME);
    expect(text(diagram)).toContain("Live power flow is not observed here");
    for (const slot of ["bus", "grid", "load-manager", "feeder", "meter", "connector", "auxiliary"]) {
      expect(diagram.querySelector(`[data-ev-slot="${slot}"]`), slot).not.toBeNull();
    }
    expect(diagram.querySelectorAll('[data-ev-breaker="not-declared"]')).toHaveLength(3);
    expect(diagram.querySelectorAll('[data-ev-edge="signal"]')).toHaveLength(1);
    expect(Array.from(diagram.querySelectorAll("[data-ev-dot]")).every((d) => d.getAttribute("data-ev-dot") === "unknown")).toBe(true);
    expect(text(diagram)).toContain("SITE FEED");
    expect(text(diagram)).toContain("Import limit 80 kW");
    expect(text(diagram)).toContain("Site import meter");
    // QN: the direct import meter sits in the source-side box (before the bus), with the load manager function not declared.
    const source = diagram.querySelector('[data-ev-slot="load-manager"]') as Element;
    expect(text(source)).toContain("Site meter & load manager");
    expect(text(source)).toContain("Site import meter · 80 kW");
    expect(text(source)).toContain("Load manager · Not declared");
    // Feeder kWh slots stay in their mock positions and are not declared; no declared AC line is dashed.
    const feederMeters = Array.from(diagram.querySelectorAll('[data-ev-slot="meter"]'));
    expect(feederMeters).toHaveLength(1);
    for (const m of feederMeters) expect(m.getAttribute("class")).toContain("ev-sld__box--missing");
    expect(diagram.querySelectorAll(".ev-sld__ac--missing")).toHaveLength(1);
    expect(diagram.querySelectorAll('[data-ev-monitor="part"]')).toHaveLength(3);
    expect(diagram.querySelector('[data-ev-monitor="billing"]')).not.toBeNull();
    const parts = panelTitled("What each part does");
    expect(Array.from(parts.querySelectorAll("thead th")).map((th) => th.textContent)).toEqual(["Part", "Role at this site", "What it reports"]);
    expect(Array.from(parts.querySelectorAll("tbody th")).map((th) => th.textContent)).toEqual([
      "Grid supply + load manager",
      "Charger 1",
      "Not declared",
      "Depot auxiliary",
    ]);
    expect(text(parts)).toContain("Site import limit 80 kW; power sharing: Not declared");
    // Compact closed lines; the connector facts sit in a closed in-cell disclosure labelled as configuration.
    const chargerRow = parts.querySelector('tr[data-ev-part="charger"]') as Element;
    expect(text(chargerRow.querySelector("[data-ev-charger-summary]") as Element)).toBe("Charger 1 · 60 kW");
    expect(text(chargerRow)).toContain("2 connectors · service hours set · 5 mapped source roles");
    const disclosure = chargerRow.querySelector("details[data-ev-connector-details]") as HTMLDetailsElement;
    expect(disclosure.open).toBe(false);
    expect(text(disclosure.querySelector("summary") as Element)).toBe("Connector details");
    expect(text(disclosure)).toContain("Configured source roles: session events, fault events, connector status, energy metering, connector power");
    expect(text(disclosure)).toContain("clock bound");
    expect(text(parts)).not.toContain("Reporting");
    expect(text(parts)).toContain("A mapped channel is configuration, not proof of reporting");
  });

  it("ev-sld keeps four part rows: a missing second charger is Not declared and extra chargers join the second charger row", async () => {
    renderEv(`${BASE}/sld`, loaded(STOCKED));
    await settledScreen();
    const rows = Array.from(panelTitled("What each part does").querySelectorAll("tbody tr"));
    expect(rows).toHaveLength(4);
    expect(text(rows[2] as Element)).toBe("Not declaredNot declaredNot declared");
    expect((rows[2] as Element).querySelector("details")).toBeNull();
    cleanup();
    const three: EvFoundationReadModel = {
      ...STOCKED,
      chargers: [STOCKED.chargers[0]!, { ...STOCKED.chargers[0]!, asset_id: "asset-chg-b", connectors: [] }, { ...STOCKED.chargers[0]!, asset_id: "asset-chg-c", connectors: [] }],
    };
    renderEv(`${BASE}/sld`, loaded(three));
    await settledScreen();
    const rows3 = Array.from(panelTitled("What each part does").querySelectorAll("tbody tr"));
    expect(rows3).toHaveLength(4);
    expect(text(rows3[2] as Element)).toContain("2 additional chargers");
    expect((rows3[2] as Element).querySelectorAll("[data-ev-charger-detail]")).toHaveLength(2);
  });

  it("ev-sld states the five schedule words and the configured-role cell exactly", async () => {
    const c0 = STOCKED.chargers[0]!;
    const con = (enabled: boolean, weekly?: never[]) => ({ ...c0.connectors[0]!, enabled_schedule: { ...schedule(enabled), ...(weekly ? { weekly } : {}) } });
    const cases: Array<[string, EvFoundationReadModel["chargers"][number]["connectors"]]> = [
      ["disabled", [con(false), con(false)]],
      ["no service hours", [con(true, []), con(true, [])]],
      ["service hours set", [con(true), con(true)]],
      ["mixed schedules", [con(true), con(false)]],
      ["no schedule declared", []],
    ];
    for (const [word, connectors] of cases) {
      renderEv(`${BASE}/sld`, loaded({ ...STOCKED, chargers: [{ ...c0, connectors }] }));
      await settledScreen();
      const row = panelTitled("What each part does").querySelector('tr[data-ev-part="charger"]') as Element;
      expect(text(row.querySelector("div.muted") as Element)).toContain(` · ${word} · `);
      cleanup();
    }
    renderEv(`${BASE}/sld`, loaded(STOCKED));
    await settledScreen();
    const stocked = panelTitled("What each part does").querySelector('tr[data-ev-part="charger"]') as Element;
    expect(text(stocked.querySelectorAll("td")[1] as Element)).toBe("5 configured source roles");
    cleanup();
    renderEv(`${BASE}/sld`, loaded({ ...STOCKED, bindings: [] }));
    await settledScreen();
    const none = panelTitled("What each part does").querySelector('tr[data-ev-part="charger"]') as Element;
    expect(text(none.querySelectorAll("td")[1] as Element)).toBe("No configured source roles");
    expect(text(none)).toContain("No mapped source roles");
  });

  it("ev-sld leaves a missing feed and import meter in their slots while chargers and connectors stay visible", async () => {
    const noFeed: EvFoundationReadModel = {
      ...MISSING_ROLE,
      feed: { asset_id: null, limit_kw: null, meter_asset_id: null },
      topology: {
        nodes: STOCKED.topology!.nodes.filter((n) => n.component_id !== "feed-1"),
        edges: STOCKED.topology!.edges.filter((e) => e.from_node !== "n-feed-1"),
      },
    };
    renderEv(`${BASE}/sld`, loaded(noFeed));
    await settledScreen();
    const diagram = panelTitled(SITE_NAME);
    expect(text(diagram)).toContain("AC FEED · NOT DECLARED");
    expect(text(diagram.querySelector('[data-ev-slot="load-manager"]') as Element)).toContain("Import meter · Not declared");
    expect(text(diagram)).toContain("Charger 1");
    expect(diagram.querySelectorAll('[data-ev-slot="connector"]')).toHaveLength(2);
    expect(text(panelTitled("What each part does"))).toContain("Grid supply + load manager");
    expect(Array.from(panelTitled("What each part does").querySelectorAll("tbody tr"))).toHaveLength(4);
  });

  it("keeps the W1 vocabulary on every route and exact IDs only in closed contextual detail", async () => {
    for (const [segment, read] of [["", STOCKED], ["/readiness", MISSING_ROLE], ["/sld", STOCKED]] as const) {
      renderEv(`${BASE}${segment}`, loaded(read));
      await settledScreen();
      const result = scanProductVocabulary(main(), `ev${segment || "-foundation"}`, { set: "w1" });
      expect(result.scanned).toBeGreaterThan(5);
      expect(describeViolations(result.violations)).toBe("");
      const references = Array.from(document.querySelectorAll("[data-exact-references]"));
      expect(references.length).toBeGreaterThan(0);
      for (const details of references) expect((details as HTMLDetailsElement).open).toBe(false);
      expect(renderedPanelTitles().join("|")).not.toContain(REV);
      cleanup();
    }
  });
});

describe("W2-05a: the Site record accepts the one state-valued property", () => {
  const prop = (value: unknown, unit: string) => ({ property_key: "ev-connector-enabled", display_name: "Connector enabled", value, unit, kind: "CONTROL", source: "site", source_version: 1 });
  const detailWith = (value: unknown, unit: string) => ({
    ...SITE,
    foundation: {
      version: 1,
      valid_from: "2026-10-01T00:00:00Z",
      summary: "EV lab",
      components: [{ component_id: "c1", component_type: "EV_CONNECTOR", display_name: "Connector c1", rating: null, properties: [prop(value, unit)] }],
      topology: null,
      devices: null,
      signal_mappings: null,
      control_assumptions: null,
      site_controls: null,
    },
  });
  it("an EV Site record with ENABLED/state is a valid detail, so the Site-type switch can pick the EV views", () => {
    expect(isSiteDetail(detailWith("ENABLED", "state"))).toBe(true);
    expect(isSiteDetail(detailWith(60, "kW"))).toBe(true);
    expect(isSiteDetail(detailWith("60", "kW"))).toBe(false);
  });
});
