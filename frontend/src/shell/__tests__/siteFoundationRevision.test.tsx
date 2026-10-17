import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { expectStateLineVisible } from "../../test/productPresentation";
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
import type { EvidenceRead } from "../../sites/evidenceRead";
import type { GatewayHealth, GatewayHealthClient, GatewayHealthEntry } from "../../sites/gatewayHealthClient";
import { createSiteEvidenceClient } from "../../sites/siteEvidenceClient";
import { EMPTY_ANALYTICS_CLIENT } from "../../sites/__tests__/analyticsFixtures";
import { HYBRID_MINI_GRID_SITE } from "../../sites/__tests__/sldFixtures";
import { describeViolations, scanDisclosureVocabulary, scanProductVocabulary } from "../../test/productVocabulary";
import { expectV69Panels, panelTitled } from "../../test/panelStructure";
import { settledScreen } from "../../test/settled";
import { UI_GAP_CATALOGUE } from "../../ui";

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
  statement: "No channel-link set is in effect for the period shown, so every role is unbound and readiness is Unknown. Operational status is not assessed here.",
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
      statement: "No channel-link set is in effect for the period shown. Every channel is unbound; the imported signal links are kept for comparison only.",
    },
    readiness: UNKNOWN_READINESS,
    acquisition_snapshot: {
      available: false,
      code: "ACQUISITION_SNAPSHOT_UNAVAILABLE",
      reason: "No channel-link set is in effect for the period shown, so no gateway snapshot exists.",
    },
    evidence: { statement: "Operational status (contact, credentials, data received, accepted evidence) is not assessed here." },
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
    statement: "These bindings are configuration. Whether any channel is reporting is not assessed here.",
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
      statement: "Set up to report means this configuration links a reading channel for every required role. It does not mean any device is connected, reporting or healthy; operational status is not assessed here.",
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
    expect(within(controls).getByRole("row", { name: /Shortest generator operation/ }).textContent).toContain("30 min");
    expect(controls.textContent).not.toMatch(/35\s?%|90\s?%/);
  });

  it("states Unknown readiness and a registered, not-connected gateway on the Readiness view", async () => {
    renderAt(`/sites/${ID}/foundation/readiness`, fakeFoundation(byAt));
    await settledScreen();
    expect(
      screen.getByText("No channel-link set is in effect for the period shown. Every channel is unbound; the imported signal links are kept for comparison only."),
    ).toBeInTheDocument();
    // W1-UX-06: the server's own no-set sentences are shown as sent (no screen-side override).
    expect(screen.getByText("No channel-link set is in effect for the period shown, so every role is unbound and readiness is Unknown. Operational status is not assessed here.")).toBeInTheDocument();
    expect(document.querySelector("[data-snapshot-available='false']")?.textContent).toBe(
      "Gateway snapshot: not available. No channel-link set is in effect for the period shown, so no gateway snapshot exists.",
    );
    expect(document.body.textContent).not.toMatch(/signal binding set/i);
    expect(document.querySelector("[data-readiness-state]")?.getAttribute("data-readiness-state")).toBe("UNKNOWN");
    expect(screen.getByText(/registered\. Registration is configuration; central contact is under Gateway status/)).toBeInTheDocument();
    expect(document.body.textContent).not.toMatch(/awaiting credentials|not sending data|no accepted evidence|no evidence has been accepted|nothing is reporting|accepted against/i);
    expect(document.body.textContent).toMatch(/Operational status is not assessed here/);
    expect(screen.getAllByRole("link", { name: "Site Evidence" }).length).toBeGreaterThan(0);
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

  it("keeps an address instant that is not a period start selected, never 'In effect now' (V-01a)", async () => {
    const inside = new Date(Date.parse(FUTURE.valid_from) + 3_600_000).toISOString();
    renderAt(`/sites/${ID}/foundation?at=${encodeURIComponent(inside)}`, fakeFoundation(byAt));
    await settledScreen();
    const picker = screen.getByRole("combobox", { name: "Foundation period" }) as HTMLSelectElement;
    expect(picker).toHaveValue(inside);
    expect(picker.selectedOptions[0].textContent).toMatch(/from the address/);
    expect(picker.selectedOptions[0].textContent).not.toMatch(/In effect now/);
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
    // W1-F1: the page-level refusal is a status line before the v69 panel slots, not an h2 panel.
    expect(refusal("no-version")).toContain("No stored version for this period");
    expect(screen.queryByRole("region", { name: "Definition" })).toBeNull();
  });

  it("labels a Site still read from its original configuration document", async () => {
    const legacy = fakeFoundation(
      () => ({ status: "migration_required", message: "legacy" }),
      { status: "migration_required", message: "legacy" },
    );
    renderAt(`/sites/${ID}/foundation`, legacy);
    await settledScreen();
    // W1-F1: the legacy notice is a page-level status, not a panel, so the
    // three v69 Foundation panels stay the only panels on the page.
    expect(refusal("legacy-record")).toContain("Original configuration record");
    expectV69Panels("foundation");
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
    // W1-F2: stated as the page-level refusal before the five v69 Overview panels, each with the gap inside.
    expect(refusal("awaiting-migration")).toContain("Awaiting evidence migration");
    expect(document.querySelector('[data-evidence-state="awaiting_migration"]')).not.toBeNull();
    expectV69Panels("mini");
  });
});

/** W1-F1: the text of the page-level refusal of `kind`, which must be present. */
function refusal(kind: "no-version" | "unavailable" | "not-imported" | "legacy-record" | "awaiting-migration"): string {
  const node = document.querySelector(`[data-page-refusal="${kind}"]`);
  expect(node, `page refusal ${kind}`).not.toBeNull();
  return node?.textContent ?? "";
}

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
    expect(within(readiness).getByText("Set up to report")).toBeInTheDocument();
    expect(within(panel("Role coverage")).getByRole("row", { name: /Battery state of charge/ }).textContent).toContain(
      "c-storage: d-storage-controller / state-of-charge",
    );
    expect(readiness.textContent).toContain("It does not mean any device is connected, reporting or healthy");
    const bindings = panel("Reading-channel links");
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
    expect(caption).toContain("device-to-asset links of the selected channel-link set");
    expect(caption).toMatch(/channel links v1 \(record bset-1\), aligned to Foundation v\d+/);
    expect(caption).toContain("legacy comparison data and are not shown here");
    expect(caption).not.toContain("Every row is a declaration in this site's foundation");
    const headers = within(table).getAllByRole("columnheader").map((th) => th.textContent);
    expect(headers).toContain("Link reference");
    expect(headers).not.toContain("Mapping ID");
    const ids = within(table).getAllByRole("row").slice(1).map((row) => row.lastElementChild?.textContent);
    expect(ids.sort()).toEqual(["b-battery-soc", "b-genset-power"]);
  });

  describe("V-01a round 2: configuration-only green, amber and neutral", () => {
    const toneOf = (el: Element | null | undefined) =>
      (el?.className ?? "").split(" ").find((c) => c.startsWith("badge--"));

    it("colours a complete verdict and configured roles green, with a legend and scope line", async () => {
      renderAt(`/sites/${ID}/foundation/readiness`, fakeFoundation(bound));
      await settledScreen();
      const readiness = panel("Configuration readiness");
      expect(toneOf(readiness.querySelector(".verdict__state .badge"))).toBe("badge--configured");
      const roles = Array.from(panel("Role coverage").querySelectorAll("[data-readiness-status] .badge"));
      expect(roles.map(toneOf)).toEqual(["badge--configured", "badge--configured"]);
      const legend = readiness.querySelector("[data-readiness-legend]") as HTMLElement;
      expect(Array.from(legend.querySelectorAll(".badge")).map((b) => [b.textContent, toneOf(b)])).toEqual([
        ["Configured / Set up to report", "badge--configured"],
        ["Needs configuration", "badge--config-gap"],
        ["Unknown", "badge--neutral"],
      ]);
      const scope = readiness.querySelector("[data-readiness-colour-scope]")?.textContent ?? "";
      expect(scope).toMatch(/configuration of the selected Foundation version only/);
      expect(scope).toMatch(/does not mean a device is connected, records have arrived, Evidence is accepted/);
      // PRE-S3-04 separation sentence survives (round 3: gateway contact is now a separate panel).
      expect(readiness.textContent).toContain(
        "Configuration readiness is distinct from what the readings can support, which is on Site Evidence, and from gateway contact, which is reported separately below.",
      );
      // A publication/version badge is never coloured as health.
      const version = within(panel("Reading-channel links")).getByText(/^Channel links v\d+$/);
      expect(toneOf(version)).toBe("badge--neutral");
    });

    it("colours a missing required role amber, in the verdict and its row", async () => {
      const incomplete = (): FoundationRead<FoundationReadModel> => ({
        status: "loaded",
        value: foundation(PAST, published([GENSET_POWER], ["Battery state of charge"])),
      });
      renderAt(`/sites/${ID}/foundation/readiness`, fakeFoundation(incomplete));
      await settledScreen();
      expect(toneOf(panel("Configuration readiness").querySelector(".verdict__state .badge"))).toBe("badge--config-gap");
      const soc = within(panel("Role coverage")).getByRole("row", { name: /Battery state of charge/ });
      expect(toneOf(soc.querySelector("[data-readiness-status] .badge"))).toBe("badge--config-gap");
    });

    it("keeps Unknown neutral when no binding basis resolves", async () => {
      renderAt(`/sites/${ID}/foundation/readiness`, fakeFoundation(byAt));
      await settledScreen();
      const badge = document.querySelector(".verdict__state .badge");
      expect(badge?.textContent).toBe("Unknown");
      expect(toneOf(badge)).toBe("badge--neutral");
      const rows = document.querySelectorAll("[data-readiness-status] .badge");
      expect(rows.length).toBeGreaterThan(0);
      rows.forEach((row) => expect(toneOf(row)).toBe("badge--neutral"));
    });

    it("does not colour an optional unbound role amber beside a complete verdict", async () => {
      const withOptional = (): FoundationRead<FoundationReadModel> => {
        const base = published([BATTERY_SOC, GENSET_POWER], []);
        const readiness = base.readiness!;
        return {
          status: "loaded",
          value: foundation(PAST, {
            ...base,
            readiness: {
              ...readiness,
              roles: [
                ...readiness.roles,
                { role: "pv_power", label: "PV power", required: false, canonical_unit: "kW", covered_by: "CHANNEL", status: "UNBOUND", subjects: [] },
              ],
            },
          }),
        };
      };
      renderAt(`/sites/${ID}/foundation/readiness`, fakeFoundation(withOptional));
      await settledScreen();
      expect(toneOf(panel("Configuration readiness").querySelector(".verdict__state .badge"))).toBe("badge--configured");
      const pv = within(panel("Role coverage")).getByRole("row", { name: /PV power/ });
      expect(toneOf(pv.querySelector("[data-readiness-status] .badge"))).toBe("badge--neutral");
    });
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
    // V-01a round 2: a Foundation gap alone is amber, with a configured role still green.
    expect(readiness.querySelector(".verdict__state .badge")?.className).toContain("badge--config-gap");
    const socStatus = within(panel("Role coverage"))
      .getByRole("row", { name: /Battery state of charge/ })
      .querySelector("[data-readiness-status] .badge");
    expect(socStatus?.className).toContain("badge--configured");
    expect(within(panel("Role coverage")).getByRole("row", { name: /Battery state of charge/ }).textContent).toContain(
      "c-storage: d-storage-controller / state-of-charge",
    );
  });

  it("publishes a binding removal as the remaining set from a UTC instant, then re-reads", async () => {
    const client = fakeFoundation(bound);
    renderAt(`/sites/${ID}/foundation/readiness`, client);
    await settledScreen();
    const form = screen.getByRole("form", { name: "Remove a channel link" });
    fireEvent.change(within(form).getByRole("combobox"), { target: { value: "b-battery-soc" } });
    fireEvent.change(within(form).getByLabelText("Effective from (UTC)"), { target: { value: "2026-10-05T00:00" } });
    fireEvent.click(within(form).getByRole("button", { name: "Publish channel-link change" }));
    expect(await within(form).findByRole("status")).toHaveTextContent("Published channel links v3");
    const [site, change] = client.publishBindings.mock.calls[0];
    expect(site).toBe(ID);
    expect(change.valid_from).toBe("2026-10-05T00:00:00Z");
    expect(change.bindings.map((b: { signal_id: string }) => b.signal_id)).toEqual(["ac-power"]);
    expect(change.bindings[0]).not.toHaveProperty("binding_revision_id");
    expect((client.getFoundation as ReturnType<typeof vi.fn>).mock.calls.length).toBeGreaterThan(1);
  });

  it("names the end of a binding change that a later independent change stops, and says when it has none", async () => {
    for (const [extra, expected] of [
      [{ applies_until: "2026-10-08T00:00:00Z", stopped_by_binding_version: 7 }, ["only until", "channel links v7"]],
      [{ applies_until: null, stopped_by_binding_version: null }, ["with no end"]],
    ] as const) {
      const client = fakeFoundation(bound);
      client.publishBindings.mockResolvedValue({ status: "published", binding_set: BINDING_SET_V3, ...extra });
      const view = renderAt(`/sites/${ID}/foundation/readiness`, client);
      await settledScreen();
      const form = screen.getByRole("form", { name: "Remove a channel link" });
      fireEvent.change(within(form).getByRole("combobox"), { target: { value: "b-battery-soc" } });
      fireEvent.change(within(form).getByLabelText("Effective from (UTC)"), { target: { value: "2026-10-04T00:00" } });
      fireEvent.click(within(form).getByRole("button", { name: "Publish channel-link change" }));
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
    expect(labels.some((label) => label?.startsWith("Channel links v3 · from 2026-10-05 00:00 UTC"))).toBe(true);
    expect(labels.filter((label) => label?.startsWith("Channel links v")).length).toBe(1);
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
      expect(screen.queryAllByRole("form", { name: "Remove a channel link" })).toHaveLength(binding);
      expect(screen.queryAllByRole("heading", { name: "Reading-channel links" })).toHaveLength(bindingTable);
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
      expect(refusal("not-imported")).toContain("This view needs an imported Site");
      expect(screen.queryByRole("navigation", { name: "Foundation views" })).toBeNull();
      expect(screen.queryByText(/Ready to report|Set up to report/)).toBeNull();
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
        expect(refusal("unavailable")).toContain("Stored versions unavailable");
        expect(document.querySelector('[data-page-refusal="not-imported"]')).toBeNull();
        expect(screen.queryByText("This view needs an imported Site")).toBeNull();
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
    expect(note.textContent).toMatch(/Scheduled channel-link period: you are viewing channel links v3/);
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

describe("S1-03: what each Foundation view offers and the order of its panels", () => {
  const loadedFoundation = (): FoundationRead<FoundationReadModel> => ({
    status: "loaded",
    value: foundation(PAST, published([BATTERY_SOC, GENSET_POWER], [])),
  });
  const VIEWS = ["", "/sld", "/readiness"] as const;

  /** Headings and disclosure summaries inside `main`, in document order. */
  function sectionOrder(): string[] {
    const main = screen.getByRole("main");
    return Array.from(main.querySelectorAll("h2, summary")).map((node) => (node.textContent ?? "").trim());
  }

  it.each(VIEWS)("never offers a Change & effect or Changes destination, enabled or not, on %s", async (segment) => {
    renderAt(`/sites/${ID}/foundation${segment}`, fakeFoundation(loadedFoundation));
    await settledScreen();
    const main = screen.getByRole("main");
    const forbidden = /^\s*(changes|change\s*(&|and)\s*effect)\s*$/i;
    // Visible text and the accessible name (aria-label, title) both count.
    const named = Array.from(main.querySelectorAll("a, button, [role='tab'], [role='link'], [aria-disabled]")).filter(
      (node) =>
        [node.textContent, node.getAttribute("aria-label"), node.getAttribute("title")].some((name) =>
          forbidden.test(name ?? ""),
        ),
    );
    expect(named).toHaveLength(0);
    expect(main.querySelectorAll("[aria-disabled]")).toHaveLength(0);
  });

  async function orderAt(segment: string): Promise<string[]> {
    renderAt(`/sites/${ID}/foundation${segment}`, fakeFoundation(loadedFoundation));
    await settledScreen();
    return sectionOrder();
  }
  /** `expected` must all be present and appear in this relative order. */
  function expectInOrder(actual: string[], expected: string[]): void {
    const positions = expected.map((heading) => actual.indexOf(heading));
    expect(positions.every((position) => position >= 0), `missing from ${JSON.stringify(actual)}`).toBe(true);
    expect(positions, `order in ${JSON.stringify(actual)}`).toEqual([...positions].sort((a, b) => a - b));
  }

  // W1-F1 (D-2026-10-17-mockup-layout-spec): each view renders exactly its v69 panels in order;
  // the version strip leads without a panel heading, and the former extra panels live inside
  // their owning v69 panel (Advanced disclosures included).
  const strip = () => screen.getByRole("region", { name: "Foundation version" });
  const follows = (a: Element, b: Element) => Boolean(a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING);
  const disclosure = (name: string) => document.querySelector(`details[data-disclosure="${name}"]`) as HTMLElement;

  it("Site model: strip, then topology beside identity, then the controls holding the reserve edit", async () => {
    await orderAt("");
    expectV69Panels("foundation");
    expect(follows(strip(), screen.getByRole("heading", { name: "Configured topology" }))).toBe(true);
    const controls = panelTitled("Time-valid control configuration");
    expect(controls.querySelector("form")).not.toBeNull();
    expect(controls.contains(disclosure("foundation-advanced"))).toBe(true);
    expect(sectionOrder()).toContain("Advanced details — Foundation records");
  });

  it("Readiness: verdict, then coverage, then bindings, with acquisition details last", async () => {
    await orderAt("/readiness");
    expectV69Panels("readiness", { gateway: "edge-kobo-001" });
    expect(follows(strip(), screen.getByRole("heading", { name: "Readiness and commissioning evidence" }))).toBe(true);
    const evidence = panelTitled("Readiness and commissioning evidence");
    const verdict = within(evidence).getByRole("heading", { name: "Configuration readiness", level: 3 });
    const advanced = disclosure("readiness-advanced");
    expect(evidence.contains(advanced)).toBe(true);
    expect(follows(verdict, advanced)).toBe(true);
    const inside = Array.from(advanced.querySelectorAll("h2")).map((h) => (h.textContent ?? "").trim());
    expectInOrder(inside, ["Role coverage", "Reading-channel links", "Acquisition details"]);
    expect(inside[inside.length - 1]).toBe("Acquisition details");
  });

  it("Single line diagram: diagram, then its parts, then the detail disclosure", async () => {
    await orderAt("/sld");
    expectV69Panels("sld", { site: "Kalangala Mini-Grid", topology: "Mini-grid" });
    expect(follows(strip(), screen.getByRole("heading", { name: "Kalangala Mini-Grid · Mini-grid" }))).toBe(true);
    expect(panelTitled("What each part does").contains(disclosure("sld-advanced"))).toBe(true);
  });

  it("Single line diagram: separates bound channels describing a part from unbound channels on its devices", async () => {
    const mixed = (): FoundationRead<FoundationReadModel> => {
      const base = published([GENSET_POWER], ["Battery state of charge"]);
      return { status: "loaded", value: foundation(PAST, base) };
    };
    renderAt(`/sites/${ID}/foundation/sld`, fakeFoundation(mixed));
    await settledScreen();
    // W1-F1: the parts panel also holds the Advanced disclosure; these are its own table's columns.
    const parts = panel("What each part does").querySelector("table") as HTMLElement;
    expect(within(parts).getByRole("columnheader", { name: "Channels" })).toBeInTheDocument();
    expect(within(parts).queryByRole("columnheader", { name: "Bound channels" })).toBeNull();
    // V-01a round 3: the plain table counts channels; the full split is under Advanced details.
    expect(within(parts).getByRole("row", { name: /Diesel generator/ }).textContent).toMatch(/\d+ bound; \d+ not bound/);
    expect(parts.querySelector('[data-part-channel]')).toBeNull();
    const advanced = document.querySelector('[data-disclosure="sld-part-channels"]') as HTMLElement;
    expect(advanced.closest('[data-disclosure="sld-advanced"]')).not.toBeNull();
    const caption = advanced.querySelector("caption")?.textContent ?? "";
    expect(caption).toMatch(/bound channel describes this part/i);
    expect(caption).toMatch(/unbound channel .* attached to this part/i);
    const bound = Array.from(advanced.querySelectorAll('[data-part-channel="bound"]'));
    const unbound = Array.from(advanced.querySelectorAll('[data-part-channel="unbound"]'));
    expect(bound.length).toBeGreaterThan(0);
    expect(unbound.length).toBeGreaterThan(0);
    for (const item of unbound) {
      expect(item.textContent).toMatch(/^Not bound: /);
      expect(item.className).toContain("muted");
    }
    for (const item of bound) expect(item.textContent).not.toMatch(/Not bound/);
  });

  it("Site model: the controls table names priority members instead of showing raw asset codes", async () => {
    const named = (): FoundationRead<FoundationReadModel> => {
      const base = foundation(PAST, published([BATTERY_SOC, GENSET_POWER], []));
      const asset = (code: string, name: string) => ({ asset_id: code, asset_code: code, asset_type: "LOAD", display_name: name });
      return {
        status: "loaded",
        value: {
          ...base,
          assets: [asset("load-clinic", "Health clinic"), asset("load-res", "Residential feeder"), asset("load-mill", "Grain mill")],
        },
      };
    };
    renderAt(`/sites/${ID}/foundation`, fakeFoundation(named));
    await settledScreen();
    const row = within(panel("Time-valid control configuration")).getByRole("row", { name: /Critical service order/ });
    expect(row.textContent).toContain("Health clinic → Residential feeder → Grain mill");
    expect(row.textContent).not.toMatch(/load-(clinic|res|mill)/);
  });

  it("Single line diagram: the drawing comes before its explanatory paragraphs", async () => {
    renderAt(`/sites/${ID}/foundation/sld`, fakeFoundation(loadedFoundation));
    await settledScreen();
    const region = document.querySelector("[data-sld-region]") as HTMLElement;
    const drawing = region.querySelector("svg") as Element;
    const firstParagraph = region.querySelector(":scope > p") as Element;
    expect(drawing).not.toBeNull();
    expect(drawing.compareDocumentPosition(firstParagraph) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });
});

describe("V-01a round 2: a chosen part stays chosen by component ID", () => {
  const pastAt = encodeURIComponent(PAST.valid_from);
  const futureAt = encodeURIComponent(FUTURE.valid_from);
  const withSoc = (at: string | null): FoundationRead<FoundationReadModel> =>
    at === FUTURE.valid_from
      ? { status: "loaded", value: foundation(FUTURE, published([GENSET_POWER], ["Battery state of charge"])) }
      : { status: "loaded", value: foundation(PAST, published([BATTERY_SOC, GENSET_POWER], [])) };
  const location = () => screen.getByTestId("location").textContent ?? "";
  const selectedPanel = () => document.querySelector("[data-selected-part]");

  it("selects a part from the parts list into the address, beside at, and keeps it across reload and view switches", async () => {
    const client = fakeFoundation(withSoc);
    const first = renderAt(`/sites/${ID}/foundation/sld?at=${pastAt}`, client);
    await settledScreen();
    expect(selectedPanel()).toBeNull();
    const row = document.querySelector('[data-sld-part="c-storage"]') as HTMLElement;
    fireEvent.click(within(row).getByRole("button", { name: "Battery energy storage" }));
    await settledScreen();
    expect(location()).toBe(`/sites/${ID}/foundation/sld?at=${pastAt}&component=c-storage`);
    expect(within(row).getByRole("button", { name: "Battery energy storage" }).getAttribute("aria-pressed")).toBe("true");
    expect(row.hasAttribute("data-selected")).toBe(true);
    expect(selectedPanel()?.getAttribute("data-selected-part")).toBe("c-storage");
    expect(selectedPanel()?.textContent).toContain("d-storage-controller / state-of-charge");
    const reloadedAt = location();
    first.unmount();

    // Reload: a fresh render at the same address keeps the part.
    renderAt(reloadedAt, client);
    await settledScreen();
    expect(selectedPanel()?.getAttribute("data-selected-part")).toBe("c-storage");

    // View switches carry both `at` and the part.
    const nav = screen.getByRole("navigation", { name: "Foundation views" });
    fireEvent.click(within(nav).getByRole("link", { name: /Readiness/ }));
    await settledScreen();
    expect(location()).toBe(`/sites/${ID}/foundation/readiness?at=${pastAt}&component=c-storage`);
    // V-01a round 3: Readiness keeps only a compact chip back to the part's drawing.
    expect(selectedPanel()).toBeNull();
    expect(document.querySelector("[data-selected-part-chip]")?.getAttribute("data-selected-part-chip")).toBe("c-storage");
    fireEvent.click(within(screen.getByRole("navigation", { name: "Foundation views" })).getAllByRole("link")[0]);
    await settledScreen();
    expect(location()).toBe(`/sites/${ID}/foundation?at=${pastAt}&component=c-storage`);
    expect(selectedPanel()?.getAttribute("data-selected-part")).toBe("c-storage");
    // The topology card for the part is distinguished too.
    const choice = document.querySelector('[data-part-choice="c-storage"]') as HTMLElement;
    expect(choice.getAttribute("aria-pressed")).toBe("true");
    expect(choice.closest("li")?.hasAttribute("data-selected")).toBe(true);

    // Clearing removes it from the address and leaves `at`.
    fireEvent.click(screen.getByRole("button", { name: "Clear selected part" }));
    await settledScreen();
    expect(location()).toBe(`/sites/${ID}/foundation?at=${pastAt}`);
    expect(selectedPanel()).toBeNull();
  });

  it("keeps the part across a period change while it is declared, with that period's channels", async () => {
    renderAt(`/sites/${ID}/foundation/sld?at=${pastAt}&component=c-storage`, fakeFoundation(withSoc));
    await settledScreen();
    expect(selectedPanel()?.querySelector('[data-part-channel="bound"]')?.textContent).toContain("state-of-charge");
    fireEvent.change(screen.getByRole("combobox", { name: "Foundation period" }), {
      target: { value: FUTURE.valid_from },
    });
    await settledScreen();
    expect(location()).toBe(`/sites/${ID}/foundation/sld?at=${futureAt}&component=c-storage`);
    expect(selectedPanel()?.getAttribute("data-selected-part")).toBe("c-storage");
    // The binding changed, the identity did not: no bound channel in v3.
    expect(selectedPanel()?.querySelector('[data-part-channel="bound"]')).toBeNull();
    expect(document.querySelector("[data-selected-part-missing]")).toBeNull();
  });

  it("clears a part the new period does not declare and says so, choosing no other part", async () => {
    const withoutStorage = (at: string | null): FoundationRead<FoundationReadModel> => {
      if (at !== FUTURE.valid_from) return withSoc(at);
      const detail = {
        ...SITE,
        foundation: {
          ...SITE.foundation,
          components: SITE.foundation.components.filter((c) => c.component_id !== "c-storage"),
        },
      };
      return { status: "loaded", value: foundation(FUTURE, { detail }) };
    };
    renderAt(`/sites/${ID}/foundation/sld?at=${pastAt}&component=c-storage`, fakeFoundation(withoutStorage));
    await settledScreen();
    expect(selectedPanel()?.getAttribute("data-selected-part")).toBe("c-storage");
    fireEvent.change(screen.getByRole("combobox", { name: "Foundation period" }), {
      target: { value: FUTURE.valid_from },
    });
    await settledScreen();
    expect(location()).toBe(`/sites/${ID}/foundation/sld?at=${futureAt}`);
    const notice = document.querySelector("[data-selected-part-missing]") as HTMLElement;
    expect(notice.getAttribute("data-selected-part-missing")).toBe("c-storage");
    expect(notice.textContent).toContain("Selected part is not in this Foundation period");
    expect(selectedPanel()).toBeNull();
    expect(document.querySelectorAll('[aria-pressed="true"]')).toHaveLength(0);
  });

  it("does not select an undeclared part named in the address on first load", async () => {
    renderAt(`/sites/${ID}/foundation?at=${pastAt}&component=c-nowhere`, fakeFoundation(withSoc));
    await settledScreen();
    // The address is rewritten by an effect after the read settles; wait for it rather than racing it.
    await waitFor(() => {
      expect(selectedPanel()).toBeNull();
      expect(location()).toBe(`/sites/${ID}/foundation?at=${pastAt}`);
      expect(document.querySelector("[data-selected-part-missing]")?.textContent).toContain(
        "Selected part is not in this Foundation period",
      );
    });
  });
});

describe("V-01a round 2: the configured drawing in the bus-bar grammar, with type icons", () => {
  const loadedFoundation = (): FoundationRead<FoundationReadModel> => ({
    status: "loaded",
    value: foundation(PAST, published([BATTERY_SOC, GENSET_POWER], [])),
  });
  const topology = HYBRID_MINI_GRID_SITE.foundation.topology!;
  const bus = topology.nodes.find((node) => node.node_role === "BUS")!;
  const points = (run: Element) =>
    (run.getAttribute("points") ?? "").split(" ").map((pair) => pair.split(",").map(Number) as [number, number]);

  it("draws every declared node and connection around one bus bar, labelled configured and not live", async () => {
    renderAt(`/sites/${ID}/foundation/sld`, fakeFoundation(loadedFoundation));
    await settledScreen();
    const svg = document.querySelector("[data-sld-region] svg") as SVGElement;
    expect(svg.getAttribute("data-sld-layout")).toBe("bus-bar");
    expect(document.querySelector("[data-sld-configured]")?.textContent).toContain("Configured, not live");
    expect(svg.querySelectorAll("[data-sld-node]")).toHaveLength(topology.nodes.length);
    expect(svg.querySelectorAll("[data-sld-connection]")).toHaveLength(topology.connections.length);

    // One bar, drawn by the one declared bus node.
    const bars = svg.querySelectorAll(".sld-node__bar");
    expect(bars).toHaveLength(1);
    expect(bars[0].closest("[data-sld-node]")?.getAttribute("data-sld-node")).toBe(bus.node_id);
    const barX = Number(bars[0].getAttribute("x1"));

    // Every run to or from the bus is a straight horizontal line that meets the bar.
    const busRuns = topology.connections.filter((c) => c.from_node === bus.node_id || c.to_node === bus.node_id);
    expect(busRuns.length).toBeGreaterThan(0);
    for (const connection of busRuns) {
      const run = svg.querySelector(`[data-sld-connection="${connection.connection_id}"]`) as Element;
      const vertices = points(run);
      expect(vertices).toHaveLength(2);
      expect(vertices[0][1]).toBe(vertices[1][1]);
      expect(vertices.some(([x]) => x === barX)).toBe(true);
    }

    // Nothing is drawn as text but declared names, declared ratings, the slot and a candidate mark:
    // no invented voltage, breaker, meter reading or status.
    const texts = Array.from(svg.querySelectorAll("text"));
    expect(texts.length).toBeGreaterThan(0);
    for (const text of texts) {
      expect(text.matches(".sld-node__name, .sld-node__rating, .sld-node__slot, .sld-node__candidate")).toBe(true);
    }
    for (const slot of Array.from(svg.querySelectorAll(".sld-node__slot"))) {
      expect(slot.textContent).toBe("Readings not assessed here");
    }
    expect(svg.textContent).not.toMatch(/Awaiting/);
  });

  it("makes every drawn part a keyboard toggle that chooses it by component ID", async () => {
    renderAt(`/sites/${ID}/foundation/sld`, fakeFoundation(loadedFoundation));
    await settledScreen();
    const svg = document.querySelector("[data-sld-region] svg") as SVGElement;
    // A drawing with controls in it is a named group, not an image that hides them.
    expect(svg.getAttribute("role")).toBe("group");
    const part = within(svg as unknown as HTMLElement).getByRole("button", { name: "Battery energy storage, Battery" });
    expect(part.getAttribute("tabindex")).toBe("0");
    expect(part.getAttribute("data-sld-component")).toBe("c-storage");
    expect(part.getAttribute("aria-pressed")).toBe("false");

    fireEvent.keyDown(part, { key: "Enter" });
    await settledScreen();
    expect(screen.getByTestId("location").textContent).toBe(`/sites/${ID}/foundation/sld?component=c-storage`);
    const chosen = document.querySelector('[data-sld-region] [data-sld-component="c-storage"]') as Element;
    expect(chosen.getAttribute("aria-pressed")).toBe("true");
    expect(chosen.hasAttribute("data-selected")).toBe(true);
    expect(document.querySelector("[data-selected-part]")?.getAttribute("data-selected-part")).toBe("c-storage");

    fireEvent.keyDown(chosen, { key: " " });
    await settledScreen();
    expect(screen.getByTestId("location").textContent).toBe(`/sites/${ID}/foundation/sld`);
    expect(document.querySelector("[data-selected-part]")).toBeNull();
  });

  it("puts a type icon, named by the declared type, on every part of every topology card", async () => {
    renderAt(`/sites/${ID}/foundation`, fakeFoundation(loadedFoundation));
    await settledScreen();
    const cards = Array.from(document.querySelectorAll(".plant-card"));
    expect(cards.length).toBeGreaterThan(0);
    const types = new Map(HYBRID_MINI_GRID_SITE.foundation.components.map((c) => [c.component_id, c.component_type]));
    for (const card of cards) {
      const parts = Array.from(card.querySelectorAll("[data-part-choice]")).map((p) => p.getAttribute("data-part-choice") ?? "");
      const icons = within(card as HTMLElement).getAllByRole("img");
      expect(icons).toHaveLength(parts.length);
      icons.forEach((icon, index) => {
        expect(icon.querySelector("[data-component-icon]")).not.toBeNull();
        const type = types.get(parts[index]) ?? "";
        expect(icon.getAttribute("aria-label")).toBe(
          { PV_ARRAY: "Solar array", INVERTER: "Inverter", BATTERY: "Battery", POWER_CONVERSION_SYSTEM: "Power conversion system",
            GENERATOR: "Generator", FUEL_TANK: "Fuel tank", METER: "Meter", LOAD: "Supplied users" }[type],
        );
      });
    }
  });
});

// --- V-01a round 3 (D-2026-10-12-v01a-round3-readiness-and-organization) ------------

const HEALTH_READ_AT = "2026-10-12T09:15:00Z";

function gatewayEntry(over: Partial<GatewayHealthEntry> = {}): GatewayHealthEntry {
  return {
    gateway_id: "g1",
    gateway_external_id: "edge-kobo-001",
    mode: "SIMULATED",
    registration: "ENABLED",
    declared_cadence_seconds: 60,
    status: "CURRENT",
    status_basis: "SERVER_RECEIVED_AT",
    last_server_contact: "2026-10-12T09:14:30Z",
    diagnostic_id: "diag-0001",
    gateway_observed_at: "2026-10-12T09:14:29Z",
    observed_at_clock: "GATEWAY_REAL_UTC",
    queue_count: 4,
    oldest_queue_age_seconds: 12,
    disk_pressure: "OK",
    disk_pressure_provenance: "REPORTED_SIMULATED_GATEWAY",
    clock_offset_ms: 120,
    mapping_error_count: 0,
    source_contacts: [
      { source_id: "s1", source_external_id: "generator-controller", registration: "ENABLED", last_contact: "2026-10-12T09:14:00Z", contact_provenance: "OBSERVED_SIMULATED_REPORT" },
    ],
    ...over,
  };
}

function healthOf(...gateways: GatewayHealthEntry[]): EvidenceRead<GatewayHealth> {
  return {
    status: "loaded",
    value: { site_id: "site-uuid-1", read_at: HEALTH_READ_AT, read_at_clock: "SERVER_REAL_UTC", claim_scope: "GATEWAY_OPERATIONAL_REPORT", gateways },
  };
}

function renderWithGateway(
  path: string,
  client: SiteFoundationClient,
  health: EvidenceRead<GatewayHealth> | "pending",
) {
  const gatewayHealth: GatewayHealthClient = {
    getGatewayHealth: vi.fn(() => (health === "pending" ? new Promise<never>(() => undefined) : Promise.resolve(health))),
  };
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App
        flags={featureFlagsWith(false)}
        siteDirectory={directory}
        siteDetail={detail}
        siteAnalytics={EMPTY_ANALYTICS_CLIENT}
        siteFoundation={client}
        siteEvidence={{ ...createSiteEvidenceClient(), gatewayHealth }}
      />
      <Location />
    </MemoryRouter>,
  );
}

const READY = (): FoundationRead<FoundationReadModel> => ({
  status: "loaded",
  value: foundation(PAST, published([BATTERY_SOC, GENSET_POWER], [])),
});

function withGaps(...gaps: FoundationGap[]) {
  return (): FoundationRead<FoundationReadModel> => ({
    status: "loaded",
    value: foundation(PAST, { ...published([BATTERY_SOC, GENSET_POWER], [], gaps), configuration_gaps: gaps }),
  });
}

/** W1-F1: the readiness gateway panel is titled "Gateway status · {gateway}" (approved title map, readiness:2). */
const GATEWAY_HEADING = /^Gateway status · /;
const regionNamed = (name: string | RegExp) => screen.getByRole("heading", { name }).closest("section") as HTMLElement;

describe("V-01a round 3: Readiness leads with four configuration cards", () => {
  const cardState = (key: string) =>
    document.querySelector(`[data-readiness-card="${key}"]`)?.getAttribute("data-card-state");

  it("shows Definition, Topology, Specifications and Controls in the mock's order, green when configured", async () => {
    renderWithGateway(`/sites/${ID}/foundation/readiness`, fakeFoundation(READY), healthOf(gatewayEntry()));
    await settledScreen();
    const cards = Array.from(document.querySelectorAll("[data-readiness-card]"));
    expect(cards.map((card) => card.getAttribute("data-readiness-card"))).toEqual([
      "definition",
      "topology",
      "specifications",
      "controls",
    ]);
    for (const card of cards) {
      expect(card.querySelector(".badge")?.textContent).toBe("Configured");
      expect(card.querySelector(".badge")?.className).toContain("badge--configured");
      expect(card.textContent).not.toMatch(/commissioned|healthy|online|reporting|(?<!not )field-verified/i);
    }
    expect(cards[2].textContent).toContain("declared, not field-verified");
    // W1-F1: the cards are the v69 metric row, ahead of panel 1 (evidence) and panel 2 (gateway).
    const follows = (a: Element, b: Element) => Boolean(a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING);
    const evidence = screen.getByRole("heading", { name: "Readiness and commissioning evidence" });
    const gatewayHeading = screen.getByRole("heading", { name: GATEWAY_HEADING });
    expect(follows(document.querySelector("[data-readiness-cards]") as Element, evidence)).toBe(true);
    expect(follows(evidence, gatewayHeading)).toBe(true);
  });

  it("turns only the category with a typed gap amber, by gap code", async () => {
    renderWithGateway(
      `/sites/${ID}/foundation/readiness`,
      fakeFoundation(
        withGaps(
          { code: "COMPONENT_RATING_MISSING", subject: "c-genset", message: "Diesel generator declares no rating." },
          { code: "SITE_CONTROL_MISSING", subject: "critical-load-priority", message: "The Site Control 'critical-load-priority' is not declared." },
        ),
      ),
      healthOf(gatewayEntry()),
    );
    await settledScreen();
    expect(cardState("definition")).toBe("CONFIGURED");
    expect(cardState("topology")).toBe("CONFIGURED");
    expect(cardState("specifications")).toBe("NEEDS_CONFIGURATION");
    expect(cardState("controls")).toBe("NEEDS_CONFIGURATION");
    const specifications = document.querySelector('[data-readiness-card="specifications"]') as HTMLElement;
    expect(specifications.querySelector(".badge")?.className).toContain("badge--config-gap");
    expect(specifications.textContent).toContain("Required ratings missing");
    expect(document.querySelector('[data-readiness-card="controls"]')?.textContent).toContain("Controls need configuration");
  });

  it("says Unknown, neutral, on every card when no effective Foundation version resolves", async () => {
    renderWithGateway(
      `/sites/${ID}/foundation/readiness`,
      fakeFoundation(withGaps({ code: "NO_EFFECTIVE_REVISION", subject: "foundation", message: "No Foundation revision is effective at this time." })),
      healthOf(gatewayEntry()),
    );
    await settledScreen();
    for (const key of ["definition", "topology", "specifications", "controls"]) {
      expect(cardState(key)).toBe("UNKNOWN");
      expect(document.querySelector(`[data-readiness-card="${key}"] .badge`)?.className).toContain("badge--neutral");
    }
  });
});

describe("V-01a round 3: the Readiness and commissioning evidence table", () => {
  it("has the mock's columns with Next step, one row per area, and Not recorded confirmation throughout", async () => {
    renderWithGateway(`/sites/${ID}/foundation/readiness`, fakeFoundation(READY), healthOf(gatewayEntry()));
    await settledScreen();
    // W1-F1: panel 1 also holds the verdict and the Advanced disclosure; the columns are its own table's.
    const table = regionNamed("Readiness and commissioning evidence").querySelector("table") as HTMLElement;
    expect(within(table).getAllByRole("columnheader").map((h) => h.textContent)).toEqual([
      "Area",
      "Declared",
      "Confirmed",
      "What is needed",
      "Next step",
    ]);
    expect(within(table).queryByRole("columnheader", { name: "Owner" })).toBeNull();
    const rows = Array.from(table.querySelectorAll("[data-readiness-row]"));
    expect(rows.map((row) => row.getAttribute("data-readiness-row"))).toEqual([
      "definition",
      "topology",
      "controls",
      "roles",
      "gateway",
      "commissioning",
    ]);
    for (const row of rows) {
      expect(row.querySelector("[data-confirmed]")?.textContent).toBe("Not recorded");
      expect(row.querySelector("[data-confirmed] .badge")?.className).toContain("badge--neutral");
      expect(row.textContent).toContain("Commissioning confirmation not recorded");
      for (const cell of Array.from(row.querySelectorAll("td"))) expect(cell.textContent?.trim()).not.toMatch(/^[—-]$/);
    }
    expect(rows[0].textContent).toContain("Foundation v2 published");
    expect(rows[2].textContent).toContain("Reserve 30%; priorities declared");
    expect(rows[3].textContent).toContain("2 of 2 required roles configured");
    expect(rows[4].textContent).toContain("Gateway registered (edge-kobo-001)");
    expect(rows[5].textContent).toContain("No commissioning record available");
    expect(within(rows[5] as HTMLElement).queryByRole("link")).toBeNull();
    expect(within(rows[0] as HTMLElement).getByRole("link", { name: "Site model →" })).toBeInTheDocument();
    expect(within(rows[4] as HTMLElement).getByRole("link", { name: "Site Evidence →" })).toBeInTheDocument();
  });

  it("lists the actual gaps and missing roles as what is needed", async () => {
    const gap = { code: "AC_BUS_PATH_MISSING", subject: "n-load", message: "Node 'n-load' has no path to the AC bus." };
    const incomplete = (): FoundationRead<FoundationReadModel> => ({
      status: "loaded",
      value: foundation(PAST, { ...published([GENSET_POWER], ["Battery state of charge"], [gap]), configuration_gaps: [gap] }),
    });
    renderWithGateway(`/sites/${ID}/foundation/readiness`, fakeFoundation(incomplete), healthOf(gatewayEntry()));
    await settledScreen();
    const topology = document.querySelector('[data-readiness-row="topology"]') as HTMLElement;
    expect(topology.textContent).toContain("Node 'n-load' has no path to the AC bus.");
    expect(topology.textContent).toContain("topology incomplete");
    const roles = document.querySelector('[data-readiness-row="roles"]') as HTMLElement;
    expect(roles.textContent).toContain("1 of 2 required roles configured");
    expect(roles.textContent).toContain("Not configured: Battery state of charge.");
  });

  it("keeps roles, channels and records behind one labelled Advanced disclosure, opened by Review or change channel links", async () => {
    renderWithGateway(`/sites/${ID}/foundation/readiness`, fakeFoundation(READY), healthOf(gatewayEntry()));
    await settledScreen();
    const advanced = document.querySelector('details[data-disclosure="readiness-advanced"]') as HTMLDetailsElement;
    expect(advanced.open).toBe(false);
    expect(advanced.querySelector("summary")?.textContent).toBe("Advanced details — roles, channels and records");
    for (const heading of ["Role coverage", "Reading-channel links", "Registered gateway and sources", "Acquisition details"]) {
      expect(screen.getByRole("heading", { name: heading }).closest("details")).toBe(advanced);
    }
    expect(advanced.textContent).toContain("b-battery-soc");
    expect(advanced.querySelector('form[aria-label="Remove a channel link"]')).not.toBeNull();
    // The plain layer names no binding ID.
    // W1-F1: the disclosure now sits inside panel 1, so the plain layer is that panel without it.
    const plain = regionNamed("Readiness and commissioning evidence").cloneNode(true) as HTMLElement;
    plain.querySelector('details[data-disclosure="readiness-advanced"]')?.remove();
    expect(plain.textContent).toContain("Area");
    expect(plain.textContent).not.toContain("b-battery-soc");
    fireEvent.click(screen.getByRole("button", { name: "Review or change channel links" }));
    expect(advanced.open).toBe(true);
    expect(document.activeElement).toBe(advanced.querySelector('form[aria-label="Remove a channel link"] select'));
  });
});

describe("V-01a round 3: the bounded gateway status panel", () => {
  const gateway = () => regionNamed(GATEWAY_HEADING);
  // G-02 (Architect C5): the former combined line is three catalogued claims, one element each.
  const NOT_YET = [
    "Uptime trend not available yet: no reviewed source reports a gateway's uptime over time.",
    "Expected-versus-delivered completeness not available yet: no reviewed source compares the reports a gateway should send with those received.",
    "Signal strength not available yet: no reviewed source reports a gateway's signal strength.",
  ];

  it("shows registration and central contact separately, with server times and the not-available-yet line", async () => {
    renderWithGateway(`/sites/${ID}/foundation/readiness`, fakeFoundation(READY), healthOf(gatewayEntry()));
    await settledScreen();
    const panel = gateway();
    const entry = panel.querySelector("[data-gateway-status]") as HTMLElement;
    expect(entry.getAttribute("data-gateway-status")).toBe("CURRENT");
    expect(within(entry).getByText("Enabled")).toBeInTheDocument();
    expect(entry.querySelector(".badge")?.textContent).toBe("Current");
    expect(entry.querySelector(".badge")?.className).toContain("badge--neutral");
    expect(panel.textContent).toContain("Read at 2026-10-12 09:15 UTC (server clock).");
    expect(panel.textContent).toContain("2026-10-12 09:14 UTC");
    expect(panel.textContent).toContain("not a live device connection, accepted readings or equipment condition");
    expect(panel.textContent).toContain("Device connection not established here.");
    for (const line of NOT_YET) expect(panel.textContent).toContain(line);
    expect(panel.textContent).not.toMatch(/Online|uptime \d|%|firmware v|signal strength:/i);
    expect(within(panel).getByRole("link", { name: "Site Evidence →" })).toBeInTheDocument();
    // Diagnostic records stay behind a closed Advanced disclosure.
    const records = panel.querySelector('details[data-disclosure^="gateway-diagnostic"]') as HTMLDetailsElement;
    expect(records.open).toBe(false);
    expect(records.querySelector("summary")?.textContent).toBe("Advanced details — gateway diagnostic records");
    expect(records.textContent).toContain("diag-0001");
    expect(records.textContent).toContain("120 ms");
  });

  it("says Loading while the read is in flight", async () => {
    renderWithGateway(`/sites/${ID}/foundation/readiness`, fakeFoundation(READY), "pending");
    await screen.findByRole("heading", { name: GATEWAY_HEADING });
    expect(gateway().textContent).toContain("Loading the site's gateway contact.");
  });

  it("says Gateway contact unavailable on a failed read, never falling back to registration as contact", async () => {
    renderWithGateway(`/sites/${ID}/foundation/readiness`, fakeFoundation(READY), { status: "unavailable", message: null });
    await settledScreen();
    const panel = gateway();
    expect(panel.querySelector("[data-gateway-panel-state]")?.getAttribute("data-gateway-panel-state")).toBe("unavailable");
    expect(panel.textContent).toContain("Gateway contact unavailable.");
    expect(panel.textContent).toContain("Registration is configuration and is not taken as contact.");
    expect(panel.textContent).toContain("Device connection not established here.");
    for (const line of NOT_YET) expect(panel.textContent).toContain(line);
    expect(panel.querySelector(".badge")).toBeNull();
    // W1-F1: "Connected sources" is the mandated v69 title of the nested panel (readiness:3), not a
    // contact claim; every other word of the panel is still scanned for one.
    const words = panel.cloneNode(true) as HTMLElement;
    words.querySelector("#readiness-connected-sources-heading")?.remove();
    expect(words.textContent).not.toMatch(/\bCurrent\b|Online|Connected/);
  });

  it("says no gateway is registered when the read lists none", async () => {
    renderWithGateway(`/sites/${ID}/foundation/readiness`, fakeFoundation(READY), healthOf());
    await settledScreen();
    expect(gateway().querySelector("[data-gateway-panel-state]")?.getAttribute("data-gateway-panel-state")).toBe("none");
    expect(gateway().textContent).toContain("No gateway is registered for this Site, so there is no central contact to report.");
  });

  it("says Contact unknown when no central diagnostic was received, and Stale when it is old", async () => {
    const first = renderWithGateway(
      `/sites/${ID}/foundation/readiness`,
      fakeFoundation(READY),
      healthOf(gatewayEntry({ status: "UNKNOWN", last_server_contact: null, diagnostic_id: null })),
    );
    await settledScreen();
    expect(gateway().textContent).toContain("Contact unknown — no central diagnostic received");
    expect(gateway().textContent).toContain("None received");
    first.unmount();
    renderWithGateway(`/sites/${ID}/foundation/readiness`, fakeFoundation(READY), healthOf(gatewayEntry({ status: "STALE" })));
    await settledScreen();
    expect(gateway().querySelector(".badge")?.textContent).toBe("Stale");
    expect(gateway().textContent).toContain("longer ago than two reporting intervals");
  });

  it("shows a disabled registration apart from contact", async () => {
    renderWithGateway(
      `/sites/${ID}/foundation/readiness`,
      fakeFoundation(READY),
      healthOf(gatewayEntry({ registration: "DISABLED", status: "STALE" })),
    );
    await settledScreen();
    const entry = gateway().querySelector("[data-gateway-registration]") as HTMLElement;
    expect(entry.getAttribute("data-gateway-registration")).toBe("DISABLED");
    expect(entry.textContent).toContain("Disabled — switched off for this Site");
    expect(entry.querySelector(".badge")?.textContent).toBe("Stale");
  });

  it("labels server-time contact as separate from a past or scheduled Foundation period", async () => {
    const OLD = revision({ revision_id: "rev-0", version: 1, valid_to: "2026-10-01T00:00:00Z", period_state: "PAST" });
    const old = (at: string | null): FoundationRead<FoundationReadModel> =>
      at === FUTURE.valid_from
        ? { status: "loaded", value: foundation(FUTURE, published([BATTERY_SOC, GENSET_POWER], [])) }
        : { status: "loaded", value: foundation(OLD, published([BATTERY_SOC, GENSET_POWER], [])) };
    const first = renderWithGateway(
      `/sites/${ID}/foundation/readiness?at=${encodeURIComponent(OLD.valid_from)}`,
      fakeFoundation(old),
      healthOf(gatewayEntry()),
    );
    await settledScreen();
    const note = gateway().querySelector("[data-gateway-period-note]") as HTMLElement;
    expect(note.getAttribute("data-gateway-period-note")).toBe("PAST");
    expect(note.textContent).toContain("a past Foundation period (v1");
    expect(note.textContent).toContain("checked now on the server clock; it did not occur in that period");
    first.unmount();
    renderWithGateway(
      `/sites/${ID}/foundation/readiness?at=${encodeURIComponent(FUTURE.valid_from)}`,
      fakeFoundation(old),
      healthOf(gatewayEntry()),
    );
    await settledScreen();
    expect(gateway().querySelector("[data-gateway-period-note]")?.textContent).toContain("a scheduled Foundation period (v3");
  });
});

describe("G-01: the catalogued gateway firmware missing state", () => {
  const gateway = () => regionNamed(GATEWAY_HEADING);
  const FIRMWARE = "Firmware not available yet: no reviewed source reports what firmware a gateway has installed.";
  const READINESS = `/sites/${ID}/foundation/readiness`;
  // Distinct gap IDs on the page: a per-row placement (commissioning) renders once per row.
  const gapIdsOnPage = () =>
    [...new Set([...document.querySelectorAll("[data-gap-id]")].map((el) => el.getAttribute("data-gap-id")))].sort();
  const firmwareOf = (panel: HTMLElement) =>
    panel.querySelector('[data-gap-placement="readiness.gateway.firmware"]') as HTMLElement | null;
  const expectFirmwareMissing = (panel: HTMLElement) => {
    const el = firmwareOf(panel);
    expect(el).not.toBeNull();
    expect(el?.tagName).toBe("P");
    expect(el?.getAttribute("data-gap-id")).toBe("G-readiness-gateway-firmware");
    expect(el?.getAttribute("data-gap-status")).toBe("open");
    expect(el?.textContent).toBe(FIRMWARE);
    // The gap ID is metadata only, and no firmware value is invented anywhere in the panel.
    expect(panel.textContent).not.toContain("G-readiness");
    expect(panel.textContent).not.toMatch(/firmware v|firmware:\s*\S|version \d/i);
  };
  const expectedReadinessGapIds = Object.entries(UI_GAP_CATALOGUE)
    .filter(([, entry]) => entry.placements.some((p) => p.startsWith("readiness.")))
    .map(([id]) => id)
    .sort();

  it("tags firmware with a populated central-contact read, with exact data-gap-id membership", async () => {
    renderWithGateway(READINESS, fakeFoundation(READY), healthOf(gatewayEntry()));
    await settledScreen();
    const panel = gateway();
    expect(panel.querySelector("[data-gateway-panel-state]")?.getAttribute("data-gateway-panel-state")).toBe("loaded");
    expectFirmwareMissing(panel);
    // G-02 enrolled Readiness: every catalogued Readiness gap renders, and nothing else does.
    expect(gapIdsOnPage()).toEqual(expectedReadinessGapIds);
    expect(panel.querySelectorAll('[data-gap-id="G-readiness-gateway-firmware"]')).toHaveLength(1);
  });

  it("keeps firmware explicitly missing while the contact read is loading (C6)", async () => {
    renderWithGateway(READINESS, fakeFoundation(READY), "pending");
    await screen.findByRole("heading", { name: GATEWAY_HEADING });
    const panel = gateway();
    expect(panel.textContent).toContain("Loading the site's gateway contact.");
    expectFirmwareMissing(panel);
    expect(panel.querySelectorAll('[data-gap-id="G-readiness-gateway-firmware"]')).toHaveLength(1);
    expect(gapIdsOnPage()).toContain("G-readiness-gateway-firmware");
  });

  it("keeps firmware explicitly missing when contact is unknown, unavailable, not found or empty", async () => {
    const branches: [EvidenceRead<GatewayHealth>, string][] = [
      [healthOf(gatewayEntry({ status: "UNKNOWN", last_server_contact: null, diagnostic_id: null })), "loaded"],
      [{ status: "unavailable", message: null }, "unavailable"],
      [{ status: "not_found" }, "unavailable"],
      [healthOf(), "none"],
    ];
    for (const [health, state] of branches) {
      const view = renderWithGateway(READINESS, fakeFoundation(READY), health);
      await settledScreen();
      const panel = gateway();
      expect(panel.querySelector("[data-gateway-panel-state]")?.getAttribute("data-gateway-panel-state")).toBe(state);
      expectFirmwareMissing(panel);
      expect(panel.querySelectorAll('[data-gap-id="G-readiness-gateway-firmware"]')).toHaveLength(1);
      expect(gapIdsOnPage()).toEqual(expectedReadinessGapIds);
      view.unmount();
    }
  });

  it("keeps the same tagged state after a reload of the Readiness address", async () => {
    const first = renderWithGateway(READINESS, fakeFoundation(READY), healthOf(gatewayEntry()));
    await settledScreen();
    const before = firmwareOf(gateway())?.outerHTML;
    first.unmount();
    expect(document.querySelector("[data-gap-id]")).toBeNull();
    renderWithGateway(READINESS, fakeFoundation(READY), healthOf(gatewayEntry()));
    await settledScreen();
    expect(firmwareOf(gateway())?.outerHTML).toBe(before);
    expect(gapIdsOnPage()).toEqual(expectedReadinessGapIds);
  });
});

describe("V-01a round 3: Site model obligations, policy positions and Advanced records", () => {
  it("names the first critical load, the configured loads and the missing productive-use designation", async () => {
    renderWithGateway(`/sites/${ID}/foundation`, fakeFoundation(READY), healthOf(gatewayEntry()));
    await settledScreen();
    const identity = regionNamed("Identity and operating obligations");
    expect(identity.querySelector("[data-critical-load]")?.textContent).toContain("First in critical service order: load-clinic");
    expect(identity.querySelector("[data-configured-loads]")?.textContent).toBe("Distribution load");
    expect(identity.querySelector("[data-productive-use]")?.textContent).toBe("Not declared");
    expect(identity.textContent).not.toMatch(/Productive use:\s*\w/);
    expect(identity.textContent).toContain("Financial assumptions not available here");
    // S4-02a: the only link is to the Site price read; the gap line itself stays tagged and open.
    expect(within(identity).getAllByRole("link").map((l) => l.getAttribute("href"))).toEqual([
      expect.stringMatching(/^\/sites\/[^/]+\/financials\/assumptions$/),
    ]);
    expect(identity.querySelector("[data-financial-assumptions-link] a")?.closest("[data-gap-id]")).toBeNull();
  });

  it("says Critical-load priority not configured when the control names no member", async () => {
    const none = (): FoundationRead<FoundationReadModel> => {
      const base = foundation(PAST, published([BATTERY_SOC, GENSET_POWER], []));
      return {
        status: "loaded",
        value: { ...base, controls: { ...base.controls, critical_load_priority: { state: "NOT_CONFIGURED", editable: false } } },
      };
    };
    renderWithGateway(`/sites/${ID}/foundation`, fakeFoundation(none), healthOf(gatewayEntry()));
    await settledScreen();
    expect(regionNamed("Identity and operating obligations").querySelector("[data-critical-load]")?.textContent).toBe(
      "Critical service order not configured",
    );
  });

  it("gives each control's Evidence / change position its real destination or a named missing state", async () => {
    renderWithGateway(`/sites/${ID}/foundation`, fakeFoundation(READY), healthOf(gatewayEntry()));
    await settledScreen();
    const controls = regionNamed("Time-valid control configuration");
    const cell = (row: RegExp) => within(controls).getByRole("row", { name: row }).querySelector("[data-control-link]") as HTMLElement;
    expect(cell(/Battery reserve/).textContent).toBe("Published configuration · Foundation v2");
    expect(cell(/Generator start/).textContent).toBe("No proposed-change record here");
    expect(cell(/Shortest generator operation/).textContent).toBe("No linked constraint evidence");
    const dispatch = within(cell(/Source priority/)).getByRole("link", { name: "Open Dispatch; choose an assessed day" });
    expect(dispatch.getAttribute("href")).toBe(`/sites/${ID}/performance/dispatch`);
    expect(cell(/Source priority/).textContent).toContain("not proof of this control's effect");
    expect(within(controls).getAllByRole("link")).toHaveLength(1);
  });

  it("keeps record IDs, the import path and raw tables under Advanced details — Foundation records", async () => {
    renderWithGateway(`/sites/${ID}/foundation`, fakeFoundation(READY), healthOf(gatewayEntry()));
    await settledScreen();
    const advanced = document.querySelector('details[data-disclosure="foundation-advanced"]') as HTMLDetailsElement;
    expect(advanced.open).toBe(false);
    expect(advanced.querySelector("summary")?.textContent).toBe("Advanced details — Foundation records");
    expect(advanced.textContent).toContain("var/sites/kobo-001.yaml");
    expect(advanced.querySelector('[data-disclosure="foundation-record"]')).not.toBeNull();
    expect(screen.queryByRole("heading", { name: "Record and inventory details" })).toBeNull();
  });
});

describe("V-01a round 3: the chosen part sits beside its drawing", () => {
  const strip = () => document.querySelector("[data-selected-part]") as HTMLElement | null;

  it("renders a compact strip under the topology, not a page-wide panel under the header", async () => {
    renderWithGateway(`/sites/${ID}/foundation?component=c-storage`, fakeFoundation(READY), healthOf(gatewayEntry()));
    await settledScreen();
    expect(screen.queryByRole("heading", { name: /^Selected part:/ })).toBeNull();
    const topology = regionNamed("Configured topology");
    expect(strip()?.closest("section")).toBe(topology);
    expect(strip()?.textContent).toContain("Selected: Battery energy storage");
    expect(strip()?.querySelector("[data-part-channel-counts]")?.textContent).toBe("1 bound; 0 not bound");
    const channels = strip()?.querySelector('details[data-disclosure="selected-part-channels-model"]') as HTMLDetailsElement;
    expect(channels.open).toBe(false);
    expect(channels.querySelector("summary")?.textContent).toBe("Advanced details — selected part channels");
    expect(channels.textContent).toContain("d-storage-controller / state-of-charge");
    // The strip region is polite and named by every part choice that updates it.
    const region = document.getElementById("selected-part-strip-model") as HTMLElement;
    expect(region.getAttribute("aria-live")).toBe("polite");
    expect(document.querySelector('[data-part-choice="c-storage"]')?.getAttribute("aria-controls")).toBe("selected-part-strip-model");
  });

  it("places the SLD strip in the diagram panel below the drawing, outside its scroll area, with the not-declared note", async () => {
    renderWithGateway(`/sites/${ID}/foundation/sld?component=c-storage`, fakeFoundation(READY), healthOf(gatewayEntry()));
    await settledScreen();
    expect(strip()).not.toBeNull();
    expect(strip()?.closest(".sld__scroll")).toBeNull();
    expect(strip()?.closest("[data-sld-region]")).not.toBeNull();
    const note = document.querySelector("[data-sld-missing]") as HTMLElement;
    expect(note.textContent).toContain(
      "Protection and meter positions are not declared in this Foundation topology; monitoring links and reporting status are not assessed on this diagram. See Site Evidence for reported records.",
    );
  });

  it("clears from the strip and returns focus to the part's own choice", async () => {
    renderWithGateway(`/sites/${ID}/foundation?component=c-storage`, fakeFoundation(READY), healthOf(gatewayEntry()));
    await settledScreen();
    fireEvent.click(screen.getByRole("button", { name: "Clear selected part" }));
    await settledScreen();
    expect(strip()).toBeNull();
    expect(screen.getByTestId("location").textContent).toBe(`/sites/${ID}/foundation`);
    await waitFor(() => expect(document.activeElement?.getAttribute("data-part-choice")).toBe("c-storage"));
  });
});

describe("G-02: V-01a pilot missing-state placements", () => {
  // Each catalogued element states only its own claim (Architect C5/C9): exact text per placement.
  const TEXT: Record<string, string> = {
    "readiness.commissioning.definition": "Confirmed means an independent commissioning or field record; none exists yet.",
    "readiness.commissioning.confirmed": "Not recorded",
    "readiness.commissioning.needed": "Commissioning confirmation not recorded",
    "readiness.commissioning.declared": "No commissioning record type exists in this Foundation",
    "readiness.commissioning.next-step": "No commissioning record available",
    "readiness.gateway.uptime": "Uptime trend not available yet: no reviewed source reports a gateway's uptime over time.",
    "readiness.gateway.completeness":
      "Expected-versus-delivered completeness not available yet: no reviewed source compares the reports a gateway should send with those received.",
    "readiness.gateway.signal-strength": "Signal strength not available yet: no reviewed source reports a gateway's signal strength.",
    "readiness.gateway.firmware": "Firmware not available yet: no reviewed source reports what firmware a gateway has installed.",
    "readiness.gateway.source-connection": "Device connection not established here.",
    "readiness.gateway.source-connection-registration": "Device connection not established here.",
    "readiness.sources.arrival": "whether data is arriving is not assessed here.",
    "foundation.identity.productive-use": "Not declared",
    "foundation.identity.financial-assumptions":
      "Financial assumptions not available here. Physical ratings here are not financial assumptions.",
    "foundation.controls.change-record": "No proposed-change record here",
    "foundation.controls.constraint-evidence": "No linked constraint evidence",
    "sld.diagram.protection-metering": "Protection and meter positions are not declared in this Foundation topology;",
    "sld.diagram.reporting-status": "monitoring links and reporting status are not assessed on this diagram.",
    "sld.diagram.readings-status": "Readings are not assessed in this view.",
    "sld.diagram.bus-slot": "Readings not assessed here",
    "sld.diagram.node-slot": "Readings not assessed here",
    "sld.contents.readings-slot": "Readings not assessed here",
    "sld.contents.caption": "both are empty in this build, for every component, and neither holds a reading.",
    "sld.intro.readings-status": "Whether any reading has arrived is not assessed in this view, so every value slot on it is empty.",
  };
  const COMMISSIONING = [
    "G-readiness-commissioning@readiness.commissioning.confirmed",
    "G-readiness-commissioning@readiness.commissioning.declared",
    "G-readiness-commissioning@readiness.commissioning.definition",
    "G-readiness-commissioning@readiness.commissioning.needed",
    "G-readiness-commissioning@readiness.commissioning.next-step",
  ];
  const GATEWAY_FIELDS = [
    "G-readiness-gateway-completeness@readiness.gateway.completeness",
    "G-readiness-gateway-firmware@readiness.gateway.firmware",
    "G-readiness-gateway-signal-strength@readiness.gateway.signal-strength",
    "G-readiness-gateway-uptime@readiness.gateway.uptime",
  ];
  const ARRIVAL = "G-readiness-source-contact@readiness.sources.arrival";
  const CONNECTION = "G-readiness-source-contact@readiness.gateway.source-connection";
  const CONNECTION_REGISTRATION = "G-readiness-source-contact@readiness.gateway.source-connection-registration";
  const tagged = () => [...document.querySelectorAll<HTMLElement>("[data-gap-id]")];
  const pairsOnPage = () =>
    [...new Set(tagged().map((el) => `${el.getAttribute("data-gap-id")}@${el.getAttribute("data-gap-placement")}`))].sort();
  /** Every tagged element is a known open pair, carries exactly its own claim text, and shows no gap ID. */
  const expectExactClaims = () => {
    expect(tagged().length).toBeGreaterThan(0);
    for (const el of tagged()) {
      const gapId = el.getAttribute("data-gap-id") as keyof typeof UI_GAP_CATALOGUE;
      const placement = el.getAttribute("data-gap-placement") as string;
      expect((UI_GAP_CATALOGUE[gapId].placements as readonly string[]).includes(placement)).toBe(true);
      expect(el.getAttribute("data-gap-status")).toBe("open");
      expect(el.textContent).toBe(TEXT[placement]);
      expect(el.querySelector("[data-gap-id]")).toBeNull();
    }
    expect(document.body.textContent).not.toMatch(/G-(readiness|foundation|sld|sites)-/);
  };
  const sorted = (...lists: string[][]) => lists.flat().sort();
  const byAt = (at: string | null): FoundationRead<FoundationReadModel> =>
    at === FUTURE.valid_from ? { status: "loaded", value: foundation(FUTURE, published([BATTERY_SOC, GENSET_POWER], [])) } : READY();

  it("renders Readiness placements per gateway-contact branch, each element carrying one claim", async () => {
    const branches: [EvidenceRead<GatewayHealth> | "pending", string[]][] = [
      [healthOf(gatewayEntry()), [CONNECTION]],
      [healthOf(gatewayEntry({ status: "UNKNOWN", last_server_contact: null, diagnostic_id: null })), [CONNECTION]],
      [{ status: "unavailable", message: null }, [CONNECTION_REGISTRATION]],
      [{ status: "not_found" }, [CONNECTION_REGISTRATION]],
      [healthOf(), []],
      ["pending", []],
    ];
    for (const [health, branchPairs] of branches) {
      const view = renderWithGateway(`/sites/${ID}/foundation/readiness`, fakeFoundation(READY), health);
      // A held contact read keeps its loading line, so only the Foundation read is awaited there.
      if (health !== "pending") await settledScreen();
      await screen.findByRole("heading", { name: GATEWAY_HEADING });
      if (health === "pending") expect(regionNamed(GATEWAY_HEADING).textContent).toContain("Loading the site's gateway contact.");
      expect(pairsOnPage()).toEqual(sorted(COMMISSIONING, GATEWAY_FIELDS, [ARRIVAL], branchPairs));
      expectExactClaims();
      // One rendered element per gateway field; per-row commissioning repeats once per table row.
      for (const pair of GATEWAY_FIELDS) {
        expect(document.querySelectorAll(`[data-gap-placement="${pair.split("@")[1]}"]`)).toHaveLength(1);
      }
      const rows = document.querySelectorAll("[data-readiness-row]").length;
      expect(rows).toBeGreaterThan(1);
      expect(document.querySelectorAll('[data-gap-placement="readiness.commissioning.confirmed"]')).toHaveLength(rows);
      expect(document.querySelectorAll('[data-gap-placement="readiness.commissioning.needed"]')).toHaveLength(rows);
      view.unmount();
    }
  });

  it("keeps the same Readiness placements across a date change and a part selection", async () => {
    const pairs: string[][] = [];
    for (const path of [
      `/sites/${ID}/foundation/readiness`,
      `/sites/${ID}/foundation/readiness?at=${encodeURIComponent(FUTURE.valid_from)}`,
      `/sites/${ID}/foundation/readiness?component=c-storage`,
    ]) {
      const view = renderWithGateway(path, fakeFoundation(byAt), healthOf(gatewayEntry()));
      await settledScreen();
      await screen.findByRole("heading", { name: GATEWAY_HEADING });
      expectExactClaims();
      pairs.push(pairsOnPage());
      view.unmount();
    }
    expect(document.querySelector("[data-gap-id]")).toBeNull();
    expect(pairs[0]).toEqual(sorted(COMMISSIONING, GATEWAY_FIELDS, [ARRIVAL, CONNECTION]));
    expect(pairs[1]).toEqual(pairs[0]);
    expect(pairs[2]).toEqual(pairs[0]);
  });

  it("renders the Site model placements, unchanged by a date change, selection and reload", async () => {
    const expected = [
      "G-foundation-change-record@foundation.controls.change-record",
      "G-foundation-constraint-evidence@foundation.controls.constraint-evidence",
      "G-foundation-financial-assumptions@foundation.identity.financial-assumptions",
      "G-foundation-productive-use@foundation.identity.productive-use",
    ];
    for (const path of [
      `/sites/${ID}/foundation`,
      `/sites/${ID}/foundation?at=${encodeURIComponent(FUTURE.valid_from)}`,
      `/sites/${ID}/foundation?component=c-storage`,
      `/sites/${ID}/foundation`,
    ]) {
      const view = renderWithGateway(path, fakeFoundation(byAt), healthOf(gatewayEntry()));
      await settledScreen();
      await screen.findByRole("heading", { name: "Identity and operating obligations" });
      expect(pairsOnPage()).toEqual(expected);
      expectExactClaims();
      view.unmount();
    }
  });

  it("renders the SLD placements: HTML beside the drawing, SVG text tagged on the text element, one placement per slot kind", async () => {
    const expected = [
      "G-sld-protection-metering@sld.diagram.protection-metering",
      "G-sld-reporting-status@sld.contents.caption",
      "G-sld-reporting-status@sld.contents.readings-slot",
      "G-sld-reporting-status@sld.diagram.bus-slot",
      "G-sld-reporting-status@sld.diagram.node-slot",
      "G-sld-reporting-status@sld.diagram.readings-status",
      "G-sld-reporting-status@sld.diagram.reporting-status",
      "G-sld-reporting-status@sld.intro.readings-status",
    ];
    for (const path of [`/sites/${ID}/foundation/sld`, `/sites/${ID}/foundation/sld?component=c-storage`, `/sites/${ID}/foundation/sld`]) {
      const view = renderWithGateway(path, fakeFoundation(READY), healthOf(gatewayEntry()));
      await settledScreen();
      await waitFor(() => expect(document.querySelector("[data-sld-missing]")).not.toBeNull());
      expect(pairsOnPage()).toEqual(expected);
      expectExactClaims();
      // SVG claims are SVG text elements; no tagged HTML element sits inside an SVG.
      const inSvg = tagged().filter((el) => el.closest("svg") !== null);
      expect(inSvg.length).toBeGreaterThan(0);
      for (const el of inSvg) {
        expect(["text", "tspan"]).toContain(el.localName);
        expect(el.namespaceURI).toBe("http://www.w3.org/2000/svg");
        expect(el.closest("[data-sld-node]")).not.toBeNull();
        expect(el.getAttribute("data-sld-slot")).toBe("unfilled");
        expect(el.hasAttribute("aria-hidden")).toBe(false);
      }
      for (const el of tagged().filter((e) => e.closest("svg") === null)) expect(el.namespaceURI).toBe("http://www.w3.org/1999/xhtml");
      // Every drawn node has one tagged slot; the bus uses its own placement, the rest share the node-slot kind.
      const nodes = document.querySelectorAll("[data-sld-node]").length;
      expect(document.querySelectorAll('[data-gap-placement="sld.diagram.bus-slot"]')).toHaveLength(1);
      expect(document.querySelectorAll('[data-gap-placement="sld.diagram.node-slot"]').length).toBe(nodes - 1);
      // Parts-table cells: the <td> keeps its row-slot hook and holds exactly the tagged words.
      const cells = [...document.querySelectorAll<HTMLElement>("td[data-sld-row-slot]")];
      expect(cells).toHaveLength(nodes);
      for (const cell of cells) {
        expect(cell.textContent).toBe("Readings not assessed here");
        expect(cell.querySelector('[data-gap-placement="sld.contents.readings-slot"]')).not.toBeNull();
      }
      // Pure scope statements stay untagged.
      for (const el of tagged()) expect(el.textContent).not.toMatch(/never of the site's behaviour/);
      // The note keeps its V-01a sentence; the two claims are separate elements inside it.
      const note = document.querySelector("[data-sld-missing]") as HTMLElement;
      expect(note.querySelectorAll("[data-gap-id]")).toHaveLength(2);
      view.unmount();
    }
  });
});

describe("W1-UX-05: the Foundation views use the W1 vocabulary set", () => {
  const STATES: [string, () => FoundationRead<FoundationReadModel>][] = [
    ["published channel links with a missing role", () => ({ status: "loaded", value: foundation(PAST, published([GENSET_POWER], ["Battery state of charge"])) })],
    ["the default Unknown readiness", () => ({ status: "loaded", value: foundation(PAST) })],
    ["every role bound", () => ({ status: "loaded", value: foundation(PAST, published([GENSET_POWER, BATTERY_SOC], [])) })],
  ];
  const VIEWS: [string, string][] = [
    ["model", `/sites/${ID}/foundation`],
    ["readiness", `/sites/${ID}/foundation/readiness`],
    ["sld", `/sites/${ID}/foundation/sld`],
  ];

  function expectW1(page: string) {
    const main = document.querySelector("main") as HTMLElement;
    const result = scanProductVocabulary(main, page, { set: "w1" });
    expect(result.scanned).toBeGreaterThan(5);
    expect(describeViolations(result.violations)).toBe("");
    return main;
  }

  for (const [view, path] of VIEWS) {
    it(`the ${view} view says nothing the W1 set bans, open or closed`, async () => {
      for (const [state, read] of STATES) {
        const page = `${view} (${state})`;
        const rendered = renderAt(path, fakeFoundation(read));
        await settledScreen();
        const main = expectW1(page);
        // W1-F1: the answer card is gone; its exact references are the strip's disclosure.
        expect(main.querySelector("[data-headline-card]")).toBeNull();
        const strip = screen.getByRole("region", { name: "Foundation version" });
        const disclosure = scanDisclosureVocabulary(strip, page);
        expect(disclosure.disclosures).toBe(1);
        expect(disclosure.scanned).toBeGreaterThan(2);
        expect(describeViolations(disclosure.violations)).toBe("");
        const details = [...main.querySelectorAll("details")];
        expect(details.length).toBeGreaterThan(1);
        for (const d of details) d.open = true;
        expectW1(`${page}, every disclosure open`);
        rendered.unmount();
      }
    });
  }
});

/**
 * W1-F1 (D-2026-10-17-mockup-layout-spec) removed the W1-UX-05 answer cards. Their
 * supported answer, state, scope, as-of and next steps now live in the v69 panels:
 * the version strip (state, period, as-of, gaps, exact references), the Readiness
 * panel's verdict and "What to do next", and the SLD panel's device summary. These
 * tests keep every honesty guarantee the card tests made, in those new homes.
 */
describe("W1-UX-05: the former Foundation answer-card facts answer only to the strength of the selected read", () => {
  const loaded = (value: FoundationReadModel) => fakeFoundation(() => ({ status: "loaded", value }));
  const strip = () => screen.getByRole("region", { name: "Foundation version" });
  const references = () => strip().querySelector("details[data-exact-references]") as HTMLDetailsElement;
  const verdict = () => document.querySelector("[data-readiness-state]") as HTMLElement;
  const next = () => document.querySelector("[data-readiness-next]") as HTMLElement;
  const row = (key: string) => document.querySelector(`[data-readiness-row="${key}"]`) as HTMLElement;

  it("Site model: the selected effective version and settings, with the selected time in scope", async () => {
    renderAt(`/sites/${ID}/foundation`, loaded(foundation(PAST)));
    await settledScreen();
    expect(document.querySelector("[data-headline-card]")).toBeNull();
    expect(strip().textContent).toContain("This is the configuration in effect now.");
    expect(strip().textContent).toContain("Foundation v2");
    expect(strip().querySelector("[data-strip-as-of]")?.textContent).toMatch(/^As of \d{4}-\d\d-\d\d \d\d:\d\d UTC$/);
    expect(strip().querySelector("[data-strip-gaps]")?.textContent).toBe("No configuration gap");
    expect(document.querySelector('[data-product-status="positive"]')).toBeNull();
    // The unrecorded setting is named inside the controls panel, never shown as recorded.
    const generator = within(panelTitled("Time-valid control configuration")).getByRole("row", { name: /Generator start/ });
    expect(generator.textContent).toContain("declares no generator start or stop threshold");
    expect(references().textContent).toContain("rev-2");
    expect(references().textContent).toContain("2026-09-29T11:57:49Z");
  });

  it("Site model: a scheduled period is never called in effect now; a gap makes it incomplete", async () => {
    renderAt(`/sites/${ID}/foundation?at=${FUTURE.valid_from}`, loaded(foundation(FUTURE)));
    await settledScreen();
    expect(strip().textContent).toContain("Scheduled period");
    expect(strip().textContent).toContain("This is not the configuration in effect now.");
    expect(strip().textContent).not.toContain("This is the configuration in effect now.");
    cleanup();
    const gap = { code: "COMPONENT_RATING_MISSING", subject: "battery", message: "The battery has no declared rating." };
    renderAt(`/sites/${ID}/foundation`, loaded(foundation(PAST, { configuration_gaps: [gap] })));
    await settledScreen();
    expect(strip().querySelector("[data-strip-gaps]")?.textContent).toBe("1 configuration gap");
    expect(panelTitled("Time-valid control configuration").textContent).toContain("The battery has no declared rating.");
    cleanup();
    const none = { code: "NO_EFFECTIVE_REVISION", subject: "foundation", message: "No Foundation revision is effective at this time." };
    renderAt(`/sites/${ID}/foundation`, loaded(foundation(PAST, { configuration_gaps: [none] })));
    await settledScreen();
    expect(strip().querySelector("[data-strip-gaps]")?.textContent).toBe("1 configuration gap");
    expect(panelTitled("Time-valid control configuration").textContent).toContain(
      "No Foundation revision is effective at this time.",
    );
    expect(document.querySelector('[data-product-status="positive"]')).toBeNull();
  });

  it("Readiness: missing channel links are next steps, commissioning stays unconfirmed, never a positive state", async () => {
    renderAt(`/sites/${ID}/foundation/readiness`, loaded(foundation(PAST, published([GENSET_POWER], ["Battery state of charge"]))));
    await settledScreen();
    expect(document.querySelector("[data-headline-card]")).toBeNull();
    expect(verdict().getAttribute("data-readiness-state")).toBe("INCOMPLETE");
    expect(verdict().querySelector(".badge")?.className).not.toContain("badge--configured");
    expect(next().querySelector("[data-readiness-next-steps]")?.textContent).toContain(
      "Link a reading channel for Battery state of charge.",
    );
    expect(row("roles").textContent).toContain("1 of 2 required roles configured");
    expect(row("commissioning").querySelector("[data-confirmed]")?.textContent).toBe("Not recorded");
    expect(row("gateway").textContent).toContain("Gateway registered (edge-kobo-001)");
    expect(document.body.textContent).toContain("Commissioning confirmation not recorded");
    cleanup();
    renderAt(`/sites/${ID}/foundation/readiness`, loaded(foundation(PAST, published([GENSET_POWER, BATTERY_SOC], []))));
    await settledScreen();
    expect(verdict().getAttribute("data-readiness-state")).toBe("READY_TO_REPORT");
    expect(panelTitled("Readiness and commissioning evidence").textContent).toContain(
      "does not mean any device is connected, reporting or healthy",
    );
    expect(next().textContent).toContain("Record a commissioning confirmation when one exists");
    expect(row("commissioning").querySelector("[data-confirmed]")?.textContent).toBe("Not recorded");
  });

  it("W1-UX-06: the Readiness badge says Set up to report (configured tone), with no answer-card strip", async () => {
    renderAt(`/sites/${ID}/foundation/readiness`, loaded(foundation(PAST, published([GENSET_POWER, BATTERY_SOC], []))));
    await settledScreen();
    expect(verdict().getAttribute("data-readiness-state")).toBe("READY_TO_REPORT");
    const badge = verdict().querySelector(".badge") as HTMLElement;
    expect(badge.textContent).toBe("Set up to report");
    expect(badge.className).toContain("badge--configured");
    expect(document.body.textContent).not.toMatch(/Ready to report(?! means)/);
    expect(document.body.textContent).not.toContain("From configuration to confirmed reporting");
    // Registration only; contact is reported in the gateway panel, and nothing claims confirmed reporting.
    expect(row("gateway").textContent).toContain("Gateway registered (edge-kobo-001)");
    expect(row("commissioning").querySelector("[data-confirmed]")?.textContent).toBe("Not recorded");
  });

  // W1-UX-06 phase-1 review L4: inherited object names (`constructor`, `toString`) are not recognised codes either.
  it.each(["SOMETHING_NEW", "constructor", "toString"])("W1-UX-06: an unrecognised Readiness code (%s) is limited: no positive verdict, no nothing-missing line", async (code) => {
    const base = foundation(PAST, published([GENSET_POWER, BATTERY_SOC], []));
    const model = { ...base, readiness: { ...base.readiness, state: code } } as unknown as FoundationReadModel;
    renderAt(`/sites/${ID}/foundation/readiness`, loaded(model));
    await settledScreen();
    expect(document.body.textContent).not.toContain("Nothing is missing from the set-up");
    expect(document.body.textContent).not.toContain("nothing else is missing from the set-up");
    expect(next().querySelector("[data-readiness-next-unrecognised]")?.textContent).toContain("not recognised");
    expect(document.querySelector('[data-product-status="positive"]')).toBeNull();
    // The exact code stays in the labelled disclosure; the verdict badge is neutral and named, never blank.
    expect(references().textContent).toContain(code);
    expect(verdict().textContent).toContain("The set-up state in this read is not recognised");
    const badge = verdict().querySelector(".badge") as HTMLElement;
    expect(badge.textContent).toBe("Set-up state not recognised");
    expect(badge.className).toContain("badge--neutral");
  });

  it("Readiness: Unknown with no linked set, and absent gateway facts as a next step", async () => {
    renderAt(`/sites/${ID}/foundation/readiness`, loaded(foundation(PAST, { gateways: [] })));
    await settledScreen();
    expect(verdict().getAttribute("data-readiness-state")).toBe("UNKNOWN");
    expect(verdict().querySelector(".badge")?.className).not.toContain("badge--configured");
    expect(next().querySelector("[data-readiness-next-steps]")?.textContent).toContain("Register the site's gateway.");
    expect(row("gateway").textContent).not.toContain("Gateway registered");
  });

  it("an empty selected period and an unreadable store keep a plain state line, scope and bound, with no card", async () => {
    renderAt(`/sites/${ID}/foundation?at=2020-01-01T00:00:00Z`, fakeFoundation(byAt));
    await settledScreen();
    const empty = document.querySelector('[data-page-refusal="no-version"]') as HTMLElement;
    expect(expectStateLineVisible(empty)).toBe("No configuration for this period");
    expect(empty.querySelector("[data-product-status-scope]")?.textContent).toContain("selected time 1 Jan 2020, 00:00 UTC");
    expect(document.querySelector("[data-headline-card]")).toBeNull();
    cleanup();
    const down = { status: "unavailable" as const, message: "The store is down." };
    renderAt(`/sites/${ID}/foundation/readiness`, fakeFoundation(() => down, down));
    await settledScreen();
    const unavailable = document.querySelector('[data-page-refusal="unavailable"]') as HTMLElement;
    expect(expectStateLineVisible(unavailable)).toBe("This could not be read right now");
    expect(unavailable.querySelector("[data-product-status-scope]")?.textContent).toBe(`${ID} · Foundation`);
    // No read instant exists for an unreadable store: the bound says so, never now.
    expect(unavailable.querySelector("[data-product-status-as-of]")?.textContent).toBe("As of: time not recorded");
    expect(document.querySelector("[data-headline-card]")).toBeNull();
  });

  it("SLD: linked and unlinked devices, reporting not assessed (never zero), gap tags kept", async () => {
    renderAt(`/sites/${ID}/foundation/sld`, loaded(foundation(PAST, published([GENSET_POWER], ["Battery state of charge"]))));
    await settledScreen();
    expect(document.querySelector("[data-headline-card]")).toBeNull();
    const summary = document.querySelector("[data-sld-summary]") as HTMLElement;
    expect(panelTitled("Kalangala Mini-Grid · Mini-grid").contains(summary)).toBe(true);
    expect(summary.textContent).toMatch(/^\d+ parts are drawn; 1 of \d+ devices have a linked reading channel\. /);
    expect(summary.textContent).toContain("Whether linked parts are reporting is not assessed here.");
    expect(summary.textContent).not.toMatch(/\b0 (parts|devices) (are )?reporting/);
    expect(strip().textContent).toContain("This is the configuration in effect now.");
    // The two catalogued SLD missing claims stay beside the drawing.
    expect(document.querySelectorAll("[data-sld-missing] [data-gap-id]")).toHaveLength(2);
  });
});

/**
 * W1-F1 (D-2026-10-17-mockup-layout-spec): each Foundation route renders exactly its v69
 * panels, in order, in its stocked, empty-period, refused and gateway variants, with any
 * unsupported read stated inside its panel slot.
 */
describe("W1-F1: Foundation, Readiness and SLD keep the v69 panel structure in every variant", () => {
  const SLD = { site: "Kalangala Mini-Grid", topology: "Mini-grid" };
  const stocked = () => fakeFoundation(byAt);
  const gaps = () => Array.from(document.querySelectorAll("[data-panel-gap]"));

  it.each([
    ["foundation", "", {}],
    ["readiness", "/readiness", { gateway: "edge-kobo-001" }],
    ["sld", "/sld", SLD],
  ] as const)("stocked: %s", async (screenId, segment, values) => {
    renderAt(`/sites/${ID}/foundation${segment}`, stocked());
    await settledScreen();
    expectV69Panels(screenId, values);
    expect(document.querySelector("[data-headline-card]")).toBeNull();
    expect(document.querySelector("[data-page-refusal]")).toBeNull();
  });

  it.each([
    ["foundation", "", {}, 3],
    ["readiness", "/readiness", { gateway: "No gateway selected" }, 4],
    ["sld", "/sld", { site: ID }, 2],
  ] as const)("no stored version for the selected time: %s keeps its slots with in-panel gaps", async (screenId, segment, values, slots) => {
    renderAt(`/sites/${ID}/foundation${segment}?at=2020-01-01T00:00:00Z`, stocked());
    await settledScreen();
    expect(document.querySelector('[data-page-refusal="no-version"]')).not.toBeNull();
    expectV69Panels(screenId, values);
    expect(gaps()).toHaveLength(slots);
    for (const gap of gaps()) expect(gap.textContent).toContain("No Foundation version is stored for the selected time");
  });

  it.each([
    ["readiness", "/readiness", { gateway: "No gateway selected" }, 4],
    ["sld", "/sld", { site: ID }, 2],
  ] as const)("unreadable store and not-imported site: %s keeps its slots with in-panel gaps", async (screenId, segment, values, slots) => {
    const down = { status: "unavailable" as const, message: "The store is down." };
    const view = renderAt(`/sites/${ID}/foundation${segment}`, fakeFoundation(() => down, down));
    await settledScreen();
    expect(document.querySelector('[data-page-refusal="unavailable"]')).not.toBeNull();
    expectV69Panels(screenId, values);
    expect(gaps()).toHaveLength(slots);
    for (const gap of gaps()) expect(gap.textContent).toContain("could not be read");
    view.unmount();
    const legacy = { status: "migration_required" as const, message: "legacy" };
    renderAt(`/sites/${ID}/foundation${segment}`, fakeFoundation(() => legacy, legacy));
    await settledScreen();
    expect(document.querySelector('[data-page-refusal="not-imported"]')).not.toBeNull();
    expectV69Panels(screenId, values);
    expect(gaps()).toHaveLength(slots);
    for (const gap of gaps()) expect(gap.textContent).toContain("no stored Foundation version");
  });

  it.each([
    ["contact read unavailable", { status: "unavailable" as const, message: null }],
    ["no gateway in the contact read", healthOf()],
    ["contact read in flight", "pending" as const],
  ])("readiness with the %s keeps the gateway slot titled from the selected read", async (_name, health) => {
    renderWithGateway(`/sites/${ID}/foundation/readiness`, fakeFoundation(READY), health);
    await screen.findByRole("heading", { name: GATEWAY_HEADING });
    expectV69Panels("readiness", { gateway: "edge-kobo-001" });
  });

  it("readiness with no registered gateway and no contact says No gateway selected in the title", async () => {
    renderAt(`/sites/${ID}/foundation/readiness`, fakeFoundation(() => ({ status: "loaded", value: foundation(PAST, { gateways: [] }) })));
    await settledScreen();
    expectV69Panels("readiness", { gateway: "No gateway selected" });
  });
});
