import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import type {
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
    bindings: { state: "INCOMPLETE", legacy_signal_mapping_count: 9, statement: "Signal roles are not bound yet." },
    acquisition_snapshot: { available: false, reason: "No signal binding set is published." },
    evidence: { state: "NONE", statement: "No accepted evidence is linked to this Foundation." },
    configuration_gaps: [],
    ...over,
  };
}

const PAST = revision({ revision_id: "rev-2", version: 2, origin: "SPLIT", valid_to: "2026-10-10T00:00:00Z", period_state: "CURRENT" });
const FUTURE = revision({ revision_id: "rev-3", version: 3, origin: "PUBLISH", valid_from: "2026-10-10T00:00:00Z", period_state: "FUTURE", battery_reserve: { value: 25, unit: "%" } });
const VERSIONS: FoundationVersionsReadModel = {
  server_now: "2026-10-07T12:00:00Z",
  current_revision_id: "rev-2",
  revisions: [revision({ recorded_state: "SUPERSEDED", superseded_at: "2026-10-07T12:00:00Z" }), PAST, FUTURE],
};

function fakeFoundation(
  byAt: (at: string | null) => FoundationRead<FoundationReadModel>,
  versions: FoundationRead<FoundationVersionsReadModel> = { status: "loaded", value: VERSIONS },
) {
  const client: SiteFoundationClient & { publishReserve: ReturnType<typeof vi.fn> } = {
    getFoundation: vi.fn((_site: string, at: string | null) => Promise.resolve(byAt(at))),
    listVersions: () => Promise.resolve(versions),
    publishReserve: vi.fn(() => Promise.resolve({ status: "published" as const, revision: FUTURE })),
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
    expect(panel.textContent).toContain("rev-2");
    expect(panel.textContent).toContain("a".repeat(64));
    expect(panel.textContent).toContain("var/sites/kobo-001.yaml");
    expect(panel.textContent).toContain("This is the configuration in effect now.");
    const controls = screen
      .getByRole("heading", { name: "Time-valid control configuration" })
      .closest("section") as HTMLElement;
    expect(within(controls).getByRole("row", { name: /Battery reserve/ }).textContent).toContain("30 %");
    expect(within(controls).getByRole("row", { name: /Generator start/ }).textContent).toContain("declares no generator start");
    expect(within(controls).getByRole("row", { name: /Minimum generator runtime/ }).textContent).toContain("30 min");
    expect(controls.textContent).not.toMatch(/35\s?%|90\s?%/);
    expect(screen.getByText(/Signal bindings: incomplete/)).toBeInTheDocument();
    expect(screen.getByText(/awaiting credentials, not sending data/)).toBeInTheDocument();
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
