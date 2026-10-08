import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import type {
  BindingSetSummary,
  ConfigurationReadiness,
  FoundationBindings,
  FoundationGap,
  SignalBinding,
  FoundationRead,
  FoundationReadModel,
  FoundationRevisionSummary,
  FoundationVersionsReadModel,
  SiteFoundationClient,
} from "../../sites/siteFoundationClient";
import type { SiteDetailClient, SiteDirectoryClient } from "../../sites/siteDirectoryClient";
import type { SiteOverviewClient } from "../../sites/siteOverviewClient";
import { EMPTY_ANALYTICS_CLIENT } from "../../sites/__tests__/analyticsFixtures";
import { HYBRID_MINI_GRID_SITE } from "../../sites/__tests__/sldFixtures";
import { settledScreen } from "../../test/settled";

/**
 * S1-01: the persisted Foundation version on the Foundation route - period
 * selection carried in the URL, the historical label, the one reserve change,
 * configuration gaps, the original-record label for an unimported Site, an
 * empty period that is never filled with current data, and the awaiting
 * evidence migration state on legacy surfaces.
 */

const SITE = HYBRID_MINI_GRID_SITE;
const ID = SITE.site_id;

function revision(over: Partial<FoundationRevisionSummary>): FoundationRevisionSummary {
  return {
    revision_id: "rev-1",
    version: 1,
    valid_from: "2026-09-29T11:57:49Z",
    valid_to: null,
    recorded_at: "2026-10-07T11:00:00Z",
    superseded_at: null,
    recorded_state: "CURRENT",
    period_state: "CURRENT",
    origin: "IMPORT",
    derived_from_revision_id: null,
    content_sha256: "a".repeat(64),
    change_note: null,
    battery_reserve: { value: 30, unit: "%" },
    ...over,
  };
}

const UNKNOWN_READINESS: ConfigurationReadiness = {
  role_set: "minigrid-roles-1",
  state: "UNKNOWN",
  binding_set_revision_id: null,
  foundation_revision_id: "rev-2",
  roles: [
    { role: "generator_power", label: "Generator power", required: true, canonical_unit: "kW", covered_by: "CHANNEL", status: "UNBOUND", subjects: [] },
  ],
  missing_roles: ["Generator power"],
  foundation_gaps: [],
  channels: [],
  statement: "No signal binding set is in effect for the period shown, so every role is unbound and readiness is Unknown. Nothing is reporting.",
};

function foundation(
  rev: FoundationRevisionSummary,
  over: Partial<FoundationReadModel> = {},
): FoundationReadModel {
  return {
    resolved: { at: rev.valid_from, knowledge_at: "2026-10-07T12:00:00Z", server_now: "2026-10-07T12:00:00Z" },
    site: {
      site_uuid: "site-uuid-1",
      site_code: ID,
      tenant: "demo",
      display_name: SITE.display_name,
      site_type: "MINIGRID",
      timezone: SITE.timezone,
      lifecycle_status: "PLANNED",
    },
    revision: { ...rev, is_current: rev.period_state === "CURRENT", current_revision_id: "rev-2" },
    provenance: {
      import_id: "imp-1",
      source_path: "var/sites/kobo-001.yaml",
      source_sha256: "b".repeat(64),
      imported_at: "2026-10-07T11:00:00Z",
      imported_revision_id: "rev-1",
      imported_version: 1,
    },
    detail: SITE,
    assets: [],
    gateways: [
      { gateway_id: "g1", gateway_external_id: "edge-kobo-001", mode: "SIMULATED", status: "PENDING", credential: "NOT_PROVISIONED" },
    ],
    sources: [
      { source_id: "s1", source_external_id: "generator-controller", device_kind: "CONTROLLER", display_name: "Generator controller", asset_code: "generator", status: "PENDING" },
    ],
    controls: {
      battery_reserve: { state: "CONFIGURED", editable: true, asset_code: "battery", value: rev.battery_reserve?.value ?? 30, unit: "%", authority: `Foundation v${rev.version}` },
      generator_minimum_runtime: { state: "DECLARED", editable: false, value: 30, unit: "min", authority: `Foundation v${rev.version}` },
      generator_start_stop: { state: "NOT_CONFIGURED", editable: false, message: "This Foundation declares no generator start or stop threshold." },
      source_priority: { state: "CONFIGURED", editable: false, members: ["pv-array", "battery", "generator"], authority: `Foundation v${rev.version}` },
      critical_load_priority: { state: "CONFIGURED", editable: false, members: ["load-clinic", "load-res", "load-mill"], authority: `Foundation v${rev.version}` },
    },
    bindings: {
      state: "NONE",
      binding_set: null,
      mappings: [],
      legacy_signal_mapping_count: 9,
      statement: "No signal binding set is in effect for the period shown.",
    },
    readiness: UNKNOWN_READINESS,
    acquisition_snapshot: {
      available: false,
      code: "ACQUISITION_SNAPSHOT_UNAVAILABLE",
      reason: "No signal binding set is in effect for the period shown.",
    },
    evidence: { state: "NONE", statement: "No accepted evidence is linked to this Foundation." },
    configuration_gaps: [],
    ...over,
  };
}

function bindingSet(over: Partial<BindingSetSummary> = {}): BindingSetSummary {
  return {
    binding_set_id: "set-1",
    binding_set_revision_id: "bset-1",
    version: 1,
    role_set: "minigrid-roles-1",
    valid_from: "2026-09-29T11:57:49Z",
    valid_to: null,
    recorded_at: "2026-10-07T11:30:00Z",
    superseded_at: null,
    recorded_state: "CURRENT",
    period_state: "CURRENT",
    origin: "CONVERSION",
    derived_from_revision_id: null,
    bindings_sha256: "c".repeat(64),
    foundation_revision_id: "rev-2",
    gateway_id: "g1",
    snapshot_schema: "assetops.acquisition-snapshot/1",
    snapshot_sha256: "d".repeat(64),
    binding_count: 2,
    change_note: null,
    ...over,
  };
}

const BINDING_SET_V3 = bindingSet({ binding_set_revision_id: "bset-3", version: 3, valid_from: "2026-10-05T00:00:00Z", origin: "PUBLISH" });

function binding(over: Partial<SignalBinding>): SignalBinding {
  return {
    binding_revision_id: "b-genset-power",
    binding_set_revision_id: "bset-1",
    device_id: "d-genset-controller",
    signal_id: "ac-power",
    source_id: "s1",
    source_external_id: "d-genset-controller",
    gateway_id: "g1",
    gateway_external_id: "edge-kobo-001",
    asset_id: "asset-genset",
    asset_code: "c-genset",
    role: "generator_power",
    role_label: "Generator power",
    source_unit: "kW",
    canonical_unit: "kW",
    conversion: { kind: "IDENTITY", parameters: {} },
    ...over,
  };
}

const GENSET_POWER = binding({});
const BATTERY_SOC = binding({
  binding_revision_id: "b-battery-soc",
  device_id: "d-storage-controller",
  signal_id: "state-of-charge",
  source_external_id: "d-storage-controller",
  asset_id: "asset-storage",
  asset_code: "c-storage",
  role: "battery_soc",
  role_label: "Battery state of charge",
  source_unit: "%",
  canonical_unit: "%",
});

function published(
  mappings: SignalBinding[],
  missing: string[],
  gaps: FoundationGap[] = [],
): Partial<FoundationReadModel> {
  const bindings: FoundationBindings = {
    state: "PUBLISHED",
    binding_set: bindingSet(),
    mappings,
    legacy_signal_mapping_count: 9,
    statement: "These bindings are configuration. No evidence has been accepted against them.",
  };
  const soc = mappings.includes(BATTERY_SOC);
  return {
    bindings,
    readiness: {
      role_set: "minigrid-roles-1",
      state: missing.length === 0 && gaps.length === 0 ? "READY_TO_REPORT" : "INCOMPLETE",
      binding_set_revision_id: "bset-1",
      foundation_revision_id: "rev-2",
      roles: [
        { role: "generator_power", label: "Generator power", required: true, canonical_unit: "kW", covered_by: "CHANNEL", status: "CONFIGURED",
          subjects: [{ asset_id: "asset-genset", asset_code: "c-genset", status: "CONFIGURED", binding_revision_ids: ["b-genset-power"] }] },
        { role: "battery_soc", label: "Battery state of charge", required: true, canonical_unit: "%", covered_by: "CHANNEL",
          status: soc ? "CONFIGURED" : "UNBOUND",
          subjects: soc ? [{ asset_id: "asset-storage", asset_code: "c-storage", status: "CONFIGURED", binding_revision_ids: ["b-battery-soc"] }] : [] },
      ],
      missing_roles: missing,
      foundation_gaps: gaps,
      channels: [
        { device_id: "d-genset-controller", signal_id: "ac-power", display_name: "Generator output power", unit: "kW", source_id: "s1", status: "BOUND", binding_revision_id: "b-genset-power", role: "generator_power" },
        { device_id: "d-genset-controller", signal_id: "output-voltage", display_name: "Generator output voltage", unit: "V", source_id: "s1", status: "UNBOUND", binding_revision_id: null, role: null },
      ],
      statement: "Ready to report means this configuration names a bound channel for every required role. It does not mean any device is connected, reporting or healthy: no evidence has been accepted for this Site.",
    },
    acquisition_snapshot: {
      available: true,
      sha256: "d".repeat(64),
      schema: "assetops.acquisition-snapshot/1",
      access: "Development configuration download, scoped to the fixed development tenant. Gateway authentication is pending (S2); this is not authenticated gateway access.",
      foundation_revision_id: "rev-2",
      binding_set_revision_id: "bset-1",
      valid_from: "2026-09-29T11:57:49Z",
      valid_to: null,
      byte_length: 2048,
    },
  };
}

const PAST = revision({ revision_id: "rev-2", version: 2, origin: "SPLIT", valid_to: "2026-10-10T00:00:00Z", period_state: "CURRENT" });
const FUTURE = revision({ revision_id: "rev-3", version: 3, origin: "PUBLISH", valid_from: "2026-10-10T00:00:00Z", period_state: "FUTURE", battery_reserve: { value: 25, unit: "%" } });
const VERSIONS: FoundationVersionsReadModel = {
  server_now: "2026-10-07T12:00:00Z",
  current_revision_id: "rev-2",
  revisions: [revision({ recorded_state: "SUPERSEDED", superseded_at: "2026-10-07T12:00:00Z" }), PAST, FUTURE],
  binding_sets: [],
};

function fakeFoundation(
  byAt: (at: string | null) => FoundationRead<FoundationReadModel>,
  versions: FoundationRead<FoundationVersionsReadModel> = { status: "loaded", value: VERSIONS },
) {
  const client: SiteFoundationClient & {
    publishReserve: ReturnType<typeof vi.fn>;
    publishBindings: ReturnType<typeof vi.fn>;
  } = {
    getFoundation: vi.fn((_site: string, at: string | null) => Promise.resolve(byAt(at))),
    listVersions: () => Promise.resolve(versions),
    publishReserve: vi.fn(() => Promise.resolve({ status: "published" as const, revision: FUTURE })),
    publishBindings: vi.fn(() => Promise.resolve({ status: "published" as const, binding_set: BINDING_SET_V3 })),
    snapshotUrl: (site: string, at: string) => `/api/sites/${site}/foundation/snapshot?at=${at}`,
  };
  return client;
}

const detail: SiteDetailClient = { getSite: () => Promise.resolve({ status: "loaded", site: SITE }) };
const directory: SiteDirectoryClient = { listSites: () => Promise.resolve({ status: "loaded", sites: [SITE] }) };

function Location() {
  const location = useLocation();
  return <output data-testid="location">{location.pathname + location.search}</output>;
}

function renderAt(path: string, client: SiteFoundationClient, overview?: SiteOverviewClient) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App
        flags={featureFlagsWith(false)}
        siteDirectory={directory}
        siteDetail={detail}
        siteAnalytics={EMPTY_ANALYTICS_CLIENT}
        siteFoundation={client}
        {...(overview === undefined ? {} : { siteOverview: overview })}
      />
      <Location />
    </MemoryRouter>,
  );
}

const byAt = (at: string | null): FoundationRead<FoundationReadModel> =>
  at === FUTURE.valid_from
    ? { status: "loaded", value: foundation(FUTURE) }
    : at === "2020-01-01T00:00:00Z"
      ? { status: "not_found", message: "No Foundation revision is effective at 2020-01-01." }
      : { status: "loaded", value: foundation(PAST) };

describe("the persisted Foundation version", () => {
  it("states the stored version, its identifiers and the configured controls", async () => {
    renderAt(`/sites/${ID}/foundation`, fakeFoundation(byAt));
    await settledScreen();
    const panel = screen.getByRole("region", { name: "Foundation version" });
    expect(panel.textContent).toContain("Foundation v2");
    expect(panel.textContent).toContain("This is the configuration in effect now.");
    // S1-03: long audit identifiers are on the Site model, behind a named disclosure.
    const record = document.querySelector('[data-disclosure="foundation-record"]') as HTMLElement;
    expect(record.textContent).toContain("rev-2");
    expect(record.textContent).toContain("a".repeat(64));
    expect(record.textContent).toContain("var/sites/kobo-001.yaml");
    expect(panel.textContent).not.toContain("a".repeat(64));
    const controls = screen
      .getByRole("heading", { name: "Time-valid control configuration" })
      .closest("section") as HTMLElement;
    expect(within(controls).getByRole("row", { name: /Battery reserve/ }).textContent).toContain("30 %");
    expect(within(controls).getByRole("row", { name: /Generator start/ }).textContent).toContain("declares no generator start");
    expect(within(controls).getByRole("row", { name: /Minimum generator runtime/ }).textContent).toContain("30 min");
    expect(controls.textContent).not.toMatch(/35\s?%|90\s?%/);
  });

  it("states Unknown readiness and a registered, not-connected gateway on the Readiness view", async () => {
    renderAt(`/sites/${ID}/foundation/readiness`, fakeFoundation(byAt));
    await settledScreen();
    expect(screen.getByText("No signal binding set is in effect for the period shown.")).toBeInTheDocument();
    expect(document.querySelector("[data-readiness-state]")?.getAttribute("data-readiness-state")).toBe("UNKNOWN");
    expect(screen.getByText(/awaiting credentials, not sending data/)).toBeInTheDocument();
    expect(screen.queryByText(/^(Online|Connected|Reporting|Healthy)$/)).toBeNull();
  });

  it("carries the selected period in the URL and labels a non-current period", async () => {
    const client = fakeFoundation(byAt);
    renderAt(`/sites/${ID}/foundation`, client);
    await settledScreen();
    fireEvent.change(screen.getByRole("combobox", { name: "Foundation period" }), {
      target: { value: FUTURE.valid_from },
    });
    await settledScreen();
    expect(screen.getByTestId("location").textContent).toBe(
      `/sites/${ID}/foundation?at=${encodeURIComponent(FUTURE.valid_from)}`,
    );
    expect(screen.getByRole("note").textContent).toMatch(/Scheduled period: you are viewing Foundation v3/);
    expect(client.getFoundation).toHaveBeenLastCalledWith(ID, FUTURE.valid_from);
  });

  it("reopens a shared URL on the same period", async () => {
    renderAt(`/sites/${ID}/foundation?at=${encodeURIComponent(FUTURE.valid_from)}`, fakeFoundation(byAt));
    await settledScreen();
    expect(screen.getByRole("note").textContent).toMatch(/not the configuration in effect now/);
    expect(screen.getByRole("combobox", { name: "Foundation period" })).toHaveValue(FUTURE.valid_from);
  });

  it("publishes a reserve change and re-reads the versions", async () => {
    const client = fakeFoundation(byAt);
    renderAt(`/sites/${ID}/foundation`, client);
    await settledScreen();
    const form = screen.getByRole("form", { name: "Change battery reserve" });
    fireEvent.change(within(form).getByLabelText(/New reserve/), { target: { value: "25" } });
    fireEvent.change(within(form).getByLabelText(/Effective from/), { target: { value: "2026-10-10T00:00" } });
    fireEvent.click(within(form).getByRole("button", { name: "Publish reserve change" }));
    await settledScreen();
    expect(client.publishReserve).toHaveBeenCalledWith(ID, {
      asset_code: "battery",
      value: 25,
      valid_from: "2026-10-10T00:00:00Z",
    });
    expect(client.getFoundation).toHaveBeenCalledTimes(2);
  });

  it("shows a bounded resulting period for a change inside a period that ends", async () => {
    renderAt(`/sites/${ID}/foundation`, fakeFoundation(byAt));
    await settledScreen();
    const form = screen.getByRole("form", { name: "Change battery reserve" });
    fireEvent.change(within(form).getByLabelText(/Effective from/), { target: { value: "2026-10-08T00:00" } });
    const preview = form.querySelector("[data-resulting-period]") as HTMLElement;
    expect(preview.dataset.resultingPeriod).toBe("bounded");
    expect(preview.textContent).toBe(
      "Resulting period: from 2026-10-08 00:00 UTC until 2026-10-10 00:00 UTC, when the v2 period ends. The value after that is unchanged.",
    );
  });

  it("shows an open-ended resulting period for a change inside the open period", async () => {
    renderAt(`/sites/${ID}/foundation`, fakeFoundation(byAt));
    await settledScreen();
    const form = screen.getByRole("form", { name: "Change battery reserve" });
    fireEvent.change(within(form).getByLabelText(/Effective from/), { target: { value: "2026-10-12T00:00" } });
    const preview = form.querySelector("[data-resulting-period]") as HTMLElement;
    expect(preview.dataset.resultingPeriod).toBe("open");
    expect(preview.textContent).toMatch(/from 2026-10-12 00:00 UTC, with no end/);
  });

  it("keeps the published period, start and end, on screen after the re-read", async () => {
    const client = fakeFoundation(byAt);
    const bounded = revision({ revision_id: "rev-5", version: 5, origin: "PUBLISH", valid_from: "2026-10-08T00:00:00Z", valid_to: "2026-10-10T00:00:00Z" });
    client.publishReserve.mockResolvedValueOnce({ status: "published", revision: bounded });
    renderAt(`/sites/${ID}/foundation`, client);
    await settledScreen();
    const form = screen.getByRole("form", { name: "Change battery reserve" });
    fireEvent.change(within(form).getByLabelText(/New reserve/), { target: { value: "40" } });
    fireEvent.change(within(form).getByLabelText(/Effective from/), { target: { value: "2026-10-08T00:00" } });
    fireEvent.click(within(form).getByRole("button", { name: "Publish reserve change" }));
    const published = "Published Foundation v5, effective 2026-10-08 00:00 UTC to 2026-10-10 00:00 UTC.";
    expect(await within(form).findByText(published)).toBeInTheDocument();
    await settledScreen();
    expect(screen.getByText(published)).toBeInTheDocument();
    expect(client.getFoundation).toHaveBeenCalledTimes(2);
  });

  it("words the reserve by the period shown, not as current, for a scheduled period", async () => {
    renderAt(`/sites/${ID}/foundation?at=${encodeURIComponent(FUTURE.valid_from)}`, fakeFoundation(byAt));
    await settledScreen();
    const form = screen.getByRole("form", { name: "Change battery reserve" });
    expect(form.textContent).toContain("In the period shown, the reserve is 25%");
    expect(form.textContent).not.toContain("In effect now");
  });

  it("accepts an effective time with seconds", async () => {
    const client = fakeFoundation(byAt);
    renderAt(`/sites/${ID}/foundation`, client);
    await settledScreen();
    const form = screen.getByRole("form", { name: "Change battery reserve" });
    expect(form.textContent).toContain("In effect now, the reserve is 30%");
    fireEvent.change(within(form).getByLabelText(/New reserve/), { target: { value: "25" } });
    fireEvent.change(within(form).getByLabelText(/Effective from/), { target: { value: "2026-10-08T00:00:30" } });
    expect((form.querySelector("[data-resulting-period]") as HTMLElement).dataset.resultingPeriod).toBe("bounded");
    fireEvent.click(within(form).getByRole("button", { name: "Publish reserve change" }));
    await settledScreen();
    expect(client.publishReserve).toHaveBeenCalledWith(ID, {
      asset_code: "battery",
      value: 25,
      valid_from: "2026-10-08T00:00:30Z",
    });
  });

  it("takes the battery from the registered assets when no reserve is configured", async () => {
    const unconfigured = (assets: FoundationReadModel["assets"]) => (): FoundationRead<FoundationReadModel> => {
      const base = foundation(PAST, { assets });
      return {
        status: "loaded",
        value: { ...base, controls: { ...base.controls, battery_reserve: { state: "NOT_CONFIGURED", editable: true } } },
      };
    };
    const client = fakeFoundation(unconfigured([{ asset_id: "a1", asset_code: "bess-1", asset_type: "BATTERY", display_name: "Battery" }]));
    renderAt(`/sites/${ID}/foundation`, client);
    await settledScreen();
    const form = screen.getByRole("form", { name: "Change battery reserve" });
    expect(form.textContent).toContain("(bess-1)");
    expect(form.textContent).toContain("is not configured");
  });

  it("states that there is no reserve to change when no battery is registered", async () => {
    const none = (): FoundationRead<FoundationReadModel> => {
      const base = foundation(PAST, { assets: [] });
      return {
        status: "loaded",
        value: { ...base, controls: { ...base.controls, battery_reserve: { state: "NOT_CONFIGURED", editable: true } } },
      };
    };
    renderAt(`/sites/${ID}/foundation`, fakeFoundation(none));
    await settledScreen();
    expect(screen.queryByRole("form", { name: "Change battery reserve" })).toBeNull();
    expect(screen.getByText("No battery is registered for this Site, so there is no reserve to change.")).toBeInTheDocument();
  });

  it("names configuration gaps", async () => {
    const gapped = (): FoundationRead<FoundationReadModel> => ({
      status: "loaded",
      value: foundation(PAST, {
        configuration_gaps: [
          { code: "BATTERY_RESERVE_MISSING", subject: "battery", message: "The battery declares no reserve state of charge." },
        ],
      }),
    });
    renderAt(`/sites/${ID}/foundation`, fakeFoundation(gapped));
    await settledScreen();
    expect(screen.getByText("The battery declares no reserve state of charge.")).toBeInTheDocument();
  });

  it("states an empty period instead of showing current data", async () => {
    renderAt(`/sites/${ID}/foundation?at=2020-01-01T00:00:00Z`, fakeFoundation(byAt));
    await settledScreen();
    expect(screen.getByRole("heading", { name: "No stored version for this period" })).toBeInTheDocument();
    expect(screen.queryByRole("region", { name: "Definition" })).toBeNull();
  });

  it("labels a Site still read from its original configuration document", async () => {
    const legacy = fakeFoundation(
      () => ({ status: "migration_required", message: "legacy" }),
      { status: "migration_required", message: "legacy" },
    );
    renderAt(`/sites/${ID}/foundation`, legacy);
    await settledScreen();
    expect(screen.getByRole("heading", { name: "Original configuration record" })).toBeInTheDocument();
    expect(screen.queryByRole("combobox", { name: "Foundation period" })).toBeNull();
    expect(screen.queryByRole("form", { name: "Change battery reserve" })).toBeNull();
  });
});

describe("legacy surfaces of an imported Site", () => {
  it("say the overview is awaiting evidence migration", async () => {
    const overview: SiteOverviewClient = {
      getOverview: () =>
        Promise.resolve({
          status: "unavailable",
          message: "moved",
          transition: "AWAITING_EVIDENCE_MIGRATION",
        }),
    } as unknown as SiteOverviewClient;
    renderAt(`/sites/${ID}`, fakeFoundation(byAt), overview);
    await settledScreen();
    expect(screen.getByRole("heading", { name: "Awaiting evidence migration" })).toBeInTheDocument();
  });
});

/** The Panel section under a heading (its table is a region of the same name). */
function panel(name: string): HTMLElement {
  return screen.getByRole("heading", { name }).closest("section") as HTMLElement;
}

describe("S1-02 bindings, Readiness and the configured SLD", () => {
  const bound = (): FoundationRead<FoundationReadModel> => ({
    status: "loaded",
    value: foundation(PAST, published([BATTERY_SOC, GENSET_POWER], [])),
  });

  it("traces each bound channel to its source, equipment, role and binding ID, and offers the snapshot", async () => {
    renderAt(`/sites/${ID}/foundation/readiness`, fakeFoundation(bound));
    await settledScreen();
    const readiness = panel("Configuration readiness");
    expect(within(readiness).getByText("Ready to report")).toBeInTheDocument();
    expect(within(panel("Role coverage")).getByRole("row", { name: /Battery state of charge/ }).textContent).toContain(
      "c-storage: d-storage-controller / state-of-charge",
    );
    expect(readiness.textContent).toContain("It does not mean any device is connected, reporting or healthy");
    const bindings = panel("Signal bindings");
    const soc = within(bindings).getByRole("row", { name: /d-storage-controller \/ state-of-charge/ });
    expect(soc.textContent).toContain("c-storage");
    expect(soc.textContent).toContain("Battery state of charge");
    expect(soc.textContent).toContain("% → %");
    expect(soc.textContent).toContain("b-battery-soc");
    expect(within(bindings).getByText(/not bound/).closest("li")?.textContent).toContain("output-voltage");
    const acquisition = panel("Acquisition details");
    const download = within(acquisition).getByRole("link", { name: "Download snapshot" });
    expect(download.getAttribute("href")).toBe(`/api/sites/${ID}/foundation/snapshot?at=${PAST.valid_from}`);
    expect(acquisition.textContent).toContain("d".repeat(64));
    expect(acquisition.textContent).toContain("Gateway authentication is pending");
  });

  it("draws only bound signals on the SLD and marks devices with no bound channel", async () => {
    renderAt(`/sites/${ID}/foundation/sld`, fakeFoundation(bound));
    await settledScreen();
    expect(document.querySelector("[data-sld-bindings]")).not.toBeNull();
    const genset = document.querySelector('[data-sld-row="n-genset"]') as HTMLElement | null;
    const rows = Array.from(document.querySelectorAll("[data-sld-row]"));
    const gensetRow = genset ?? (rows.find((row) => row.textContent?.includes("Generator controller")) as HTMLElement);
    expect(gensetRow.textContent).toContain("Generator output power");
    expect(gensetRow.textContent).not.toContain("Generator output voltage");
    const unbound = Array.from(document.querySelectorAll('[data-sld-device-binding="unbound"]')).map((li) => li.textContent);
    expect(unbound.length).toBeGreaterThan(0);
    expect(unbound.every((text) => text?.endsWith("- no bound channel"))).toBe(true);
    const boundNames = Array.from(document.querySelectorAll('[data-sld-device-binding="bound"]')).map((li) => li.textContent);
    expect(boundNames.sort()).toEqual(["Battery PCS controller", "Generator controller"]);
  });

  it("labels the shared mapping table as the binding set's links, with Binding IDs (ruling D5)", async () => {
    renderAt(`/sites/${ID}/foundation/sld`, fakeFoundation(bound));
    await settledScreen();
    const table = screen.getByRole("table", { name: "Signal mappings" });
    const caption = table.querySelector("caption")?.textContent ?? "";
    expect(caption).toContain("device-to-asset links of the selected signal binding set");
    expect(caption).toMatch(/binding v1 \(record bset-1\), aligned to Foundation v\d+/);
    expect(caption).toContain("legacy comparison data and are not shown here");
    expect(caption).not.toContain("Every row is a declaration in this site's foundation");
    const headers = within(table).getAllByRole("columnheader").map((th) => th.textContent);
    expect(headers).toContain("Binding ID");
    expect(headers).not.toContain("Mapping ID");
    const ids = within(table).getAllByRole("row").slice(1).map((row) => row.lastElementChild?.textContent);
    expect(ids.sort()).toEqual(["b-battery-soc", "b-genset-power"]);
  });

  it("names a missing required role as not bound", async () => {
    const incomplete = (): FoundationRead<FoundationReadModel> => ({
      status: "loaded",
      value: foundation(PAST, published([GENSET_POWER], ["Battery state of charge"])),
    });
    renderAt(`/sites/${ID}/foundation/readiness`, fakeFoundation(incomplete));
    await settledScreen();
    const readiness = panel("Configuration readiness");
    expect(within(readiness).getByText("Incomplete")).toBeInTheDocument();
    expect(readiness.textContent).toContain("Not bound: Battery state of charge.");
    expect(readiness.querySelector('[data-readiness-missing-role]')).not.toBeNull();
    expect(within(panel("Role coverage")).getByRole("row", { name: /Battery state of charge/ }).textContent).toContain("Not bound");
  });

  it("keeps readiness incomplete for a Foundation gap and names it apart from roles", async () => {
    const gap: FoundationGap = {
      code: "COMPONENT_RATING_MISSING",
      subject: "c-genset",
      message: "Diesel generator declares no rating.",
    };
    const gapped = (): FoundationRead<FoundationReadModel> => ({
      status: "loaded",
      value: foundation(PAST, published([BATTERY_SOC, GENSET_POWER], [], [gap])),
    });
    renderAt(`/sites/${ID}/foundation/readiness`, fakeFoundation(gapped));
    await settledScreen();
    const readiness = panel("Configuration readiness");
    expect(within(readiness).getByText("Incomplete")).toBeInTheDocument();
    expect(readiness.textContent).not.toContain("Not bound:");
    expect(readiness.textContent).toContain("but this Foundation has configuration gaps");
    const listed = readiness.querySelector('[data-readiness-gap="COMPONENT_RATING_MISSING"]');
    expect(listed?.textContent).toBe("Diesel generator declares no rating.");
    expect(within(panel("Role coverage")).getByRole("row", { name: /Battery state of charge/ }).textContent).toContain(
      "c-storage: d-storage-controller / state-of-charge",
    );
  });

  it("publishes a binding removal as the remaining set from a UTC instant, then re-reads", async () => {
    const client = fakeFoundation(bound);
    renderAt(`/sites/${ID}/foundation/readiness`, client);
    await settledScreen();
    const form = screen.getByRole("form", { name: "Remove a binding" });
    fireEvent.change(within(form).getByRole("combobox"), { target: { value: "b-battery-soc" } });
    fireEvent.change(within(form).getByLabelText("Effective from (UTC)"), { target: { value: "2026-10-05T00:00" } });
    fireEvent.click(within(form).getByRole("button", { name: "Publish binding change" }));
    expect(await within(form).findByRole("status")).toHaveTextContent("Published binding v3");
    const [site, change] = client.publishBindings.mock.calls[0];
    expect(site).toBe(ID);
    expect(change.valid_from).toBe("2026-10-05T00:00:00Z");
    expect(change.bindings.map((b: { signal_id: string }) => b.signal_id)).toEqual(["ac-power"]);
    expect(change.bindings[0]).not.toHaveProperty("binding_revision_id");
    expect((client.getFoundation as ReturnType<typeof vi.fn>).mock.calls.length).toBeGreaterThan(1);
  });

  it("names the end of a binding change that a later independent change stops, and says when it has none", async () => {
    for (const [extra, expected] of [
      [{ applies_until: "2026-10-08T00:00:00Z", stopped_by_binding_version: 7 }, ["only until", "binding v7"]],
      [{ applies_until: null, stopped_by_binding_version: null }, ["with no end"]],
    ] as const) {
      const client = fakeFoundation(bound);
      client.publishBindings.mockResolvedValue({ status: "published", binding_set: BINDING_SET_V3, ...extra });
      const view = renderAt(`/sites/${ID}/foundation/readiness`, client);
      await settledScreen();
      const form = screen.getByRole("form", { name: "Remove a binding" });
      fireEvent.change(within(form).getByRole("combobox"), { target: { value: "b-battery-soc" } });
      fireEvent.change(within(form).getByLabelText("Effective from (UTC)"), { target: { value: "2026-10-04T00:00" } });
      fireEvent.click(within(form).getByRole("button", { name: "Publish binding change" }));
      const status = await within(form).findByRole("status");
      for (const text of expected) expect(status).toHaveTextContent(text);
      view.unmount();
    }
  });

  it("offers binding periods in the period selector and carries one in the URL", async () => {
    const withBindingPeriods = {
      ...VERSIONS,
      binding_sets: [
        bindingSet({ recorded_state: "SUPERSEDED", superseded_at: "2026-10-07T12:00:00Z" }),
        bindingSet({ binding_set_revision_id: "bset-2", version: 2, origin: "SPLIT", valid_to: "2026-10-05T00:00:00Z" }),
        BINDING_SET_V3,
      ],
    };
    renderAt(`/sites/${ID}/foundation`, fakeFoundation(bound, { status: "loaded", value: withBindingPeriods }));
    await settledScreen();
    const picker = screen.getByRole("combobox", { name: "Foundation period" });
    const labels = within(picker).getAllByRole("option").map((option) => option.textContent);
    expect(labels.some((label) => label?.startsWith("Binding v3 · from 2026-10-05 00:00 UTC"))).toBe(true);
    expect(labels.filter((label) => label?.startsWith("Binding v")).length).toBe(1);
    fireEvent.change(picker, { target: { value: "2026-10-05T00:00:00Z" } });
    expect(screen.getByTestId("location").textContent).toContain("at=2026-10-05T00%3A00%3A00Z");
  });
});

describe("S1-03: three Foundation views at one selected period", () => {
  const futureAt = encodeURIComponent(FUTURE.valid_from);

  it("renders the view row in the mock's order, marking the current view", async () => {
    renderAt(`/sites/${ID}/foundation/sld?at=${futureAt}`, fakeFoundation(byAt));
    await settledScreen();
    const row = screen.getByRole("navigation", { name: "Foundation views" });
    const links = within(row).getAllByRole("link");
    expect(links.map((link) => link.textContent)).toEqual(["Site model", "Single line diagram", "Readiness"]);
    expect(links.map((link) => link.getAttribute("aria-current"))).toEqual([null, "page", null]);
    expect(links.map((link) => link.getAttribute("href"))).toEqual([
      `/sites/${ID}/foundation?at=${futureAt}`,
      `/sites/${ID}/foundation/sld?at=${futureAt}`,
      `/sites/${ID}/foundation/readiness?at=${futureAt}`,
    ]);
    expect(screen.queryByRole("navigation", { name: "Foundation sections" })).toBeNull();
  });

  it("keeps the selected period and its historical label when moving across views", async () => {
    const client = fakeFoundation(byAt);
    renderAt(`/sites/${ID}/foundation?at=${futureAt}`, client);
    await settledScreen();
    for (const [label, path] of [
      ["Single line diagram", `/sites/${ID}/foundation/sld`],
      ["Readiness", `/sites/${ID}/foundation/readiness`],
      ["Site model", `/sites/${ID}/foundation`],
    ] as const) {
      fireEvent.click(within(screen.getByRole("navigation", { name: "Foundation views" })).getByRole("link", { name: label }));
      await settledScreen();
      expect(screen.getByTestId("location").textContent).toBe(`${path}?at=${futureAt}`);
      expect(screen.getByRole("note").textContent).toMatch(/Scheduled period: you are viewing Foundation v3/);
      expect(screen.getByRole("combobox", { name: "Foundation period" })).toHaveValue(FUTURE.valid_from);
    }
    expect(client.getFoundation).toHaveBeenLastCalledWith(ID, FUTURE.valid_from);
  });

  it("changes the period from any view and stays on that view", async () => {
    renderAt(`/sites/${ID}/foundation/readiness`, fakeFoundation(byAt));
    await settledScreen();
    fireEvent.change(screen.getByRole("combobox", { name: "Foundation period" }), {
      target: { value: FUTURE.valid_from },
    });
    await settledScreen();
    expect(screen.getByTestId("location").textContent).toBe(`/sites/${ID}/foundation/readiness?at=${futureAt}`);
  });

  it("places each action on its own view and repeats no binding table", async () => {
    const bound = (): FoundationRead<FoundationReadModel> => ({
      status: "loaded",
      value: foundation(PAST, published([BATTERY_SOC, GENSET_POWER], [])),
    });
    for (const [path, reserve, binding, bindingTable] of [
      [`/sites/${ID}/foundation`, 1, 0, 0],
      [`/sites/${ID}/foundation/sld`, 0, 0, 0],
      [`/sites/${ID}/foundation/readiness`, 0, 1, 1],
    ] as const) {
      const view = renderAt(path, fakeFoundation(bound));
      await settledScreen();
      expect(screen.queryAllByRole("form", { name: "Change battery reserve" })).toHaveLength(reserve);
      expect(screen.queryAllByRole("form", { name: "Remove a binding" })).toHaveLength(binding);
      expect(screen.queryAllByRole("heading", { name: "Signal bindings" })).toHaveLength(bindingTable);
      view.unmount();
    }
  });

  it("refuses a Foundation view that does not exist, such as Changes", async () => {
    renderAt(`/sites/${ID}/foundation/changes`, fakeFoundation(byAt));
    await settledScreen();
    expect(screen.queryByRole("navigation", { name: "Foundation views" })).toBeNull();
    expect(screen.queryByRole("heading", { name: "Configuration readiness" })).toBeNull();
  });

  it("states that a legacy Site has no Readiness or SLD view, and offers no view row", async () => {
    const legacy = fakeFoundation(
      () => ({ status: "migration_required", message: "legacy" }),
      { status: "migration_required", message: "legacy" },
    );
    for (const path of [`/sites/${ID}/foundation/readiness`, `/sites/${ID}/foundation/sld`]) {
      const view = renderAt(path, legacy);
      await settledScreen();
      expect(screen.getByRole("heading", { name: "This view needs an imported Site" })).toBeInTheDocument();
      expect(screen.queryByRole("navigation", { name: "Foundation views" })).toBeNull();
      expect(screen.queryByText(/Ready to report/)).toBeNull();
      view.unmount();
    }
    renderAt(`/sites/${ID}/foundation`, legacy);
    await settledScreen();
    expect(screen.queryByRole("navigation", { name: "Foundation views" })).toBeNull();
  });
});

describe("S1-03: an unreadable store is not reported as a Site without records", () => {
  it("says stored versions are unavailable, not that the Site needs importing, on SLD and Readiness", async () => {
    for (const unreadable of [
      { status: "unavailable" as const, message: "The store is down." },
      { status: "unavailable" as const, message: null },
      { status: "not_found" as const, message: "No version." },
      { status: "invalid" as const, message: "Bad answer." },
    ]) {
      const client = fakeFoundation(() => unreadable, unreadable);
      for (const path of [`/sites/${ID}/foundation/readiness`, `/sites/${ID}/foundation/sld`]) {
        const view = renderAt(path, client);
        await settledScreen();
        expect(screen.getByRole("heading", { name: "Stored versions unavailable" })).toBeInTheDocument();
        expect(screen.queryByRole("heading", { name: "This view needs an imported Site" })).toBeNull();
        expect(screen.queryByText(/has no stored Foundation version/)).toBeNull();
        view.unmount();
      }
    }
  });
});

describe("S1-03: a scheduled binding period is never called the configuration in effect now", () => {
  it("labels a future binding set shown with the current Foundation version", async () => {
    const scheduled = (): FoundationRead<FoundationReadModel> => {
      const base = published([GENSET_POWER], ["Battery state of charge"]);
      return {
        status: "loaded",
        value: foundation(PAST, {
          ...base,
          bindings: { ...base.bindings!, binding_set: BINDING_SET_V3_FUTURE },
        }),
      };
    };
    renderAt(`/sites/${ID}/foundation/readiness?at=2026-10-05T00:00:00Z`, fakeFoundation(scheduled));
    await settledScreen();
    const note = screen.getByRole("note");
    expect(note.textContent).toMatch(/Scheduled binding period: you are viewing binding v3/);
    expect(note.textContent).toContain("not the ones in effect now");
    expect(screen.queryByText("This is the configuration in effect now.")).toBeNull();
  });
});

const BINDING_SET_V3_FUTURE = bindingSet({
  binding_set_revision_id: "bset-3",
  version: 3,
  valid_from: "2026-10-05T00:00:00Z",
  origin: "PUBLISH",
  period_state: "FUTURE",
});

describe("S1-03: the verdict names a missing Foundation control apart from unbound channels", () => {
  it("says Not configured for the battery reserve, not Not bound", async () => {
    const reserveMissing = (): FoundationRead<FoundationReadModel> => {
      const base = foundation(PAST, published([GENSET_POWER], ["Battery state of charge", "Battery reserve"]));
      return {
        status: "loaded",
        value: {
          ...base,
          readiness: {
            ...base.readiness,
            roles: [
              ...base.readiness.roles,
              {
                role: "battery_reserve",
                label: "Battery reserve",
                required: true,
                canonical_unit: "%",
                covered_by: "FOUNDATION_CONTROL",
                status: "NOT_CONFIGURED",
                subjects: [],
              },
            ],
          },
        },
      };
    };
    renderAt(`/sites/${ID}/foundation/readiness`, fakeFoundation(reserveMissing));
    await settledScreen();
    const verdict = document.querySelector(".verdict__sentence")?.textContent ?? "";
    expect(verdict).toBe("Not bound: Battery state of charge. Not configured: Battery reserve.");
  });
});
