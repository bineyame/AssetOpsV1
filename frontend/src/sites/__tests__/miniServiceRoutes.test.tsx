import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import type { MiniDepthClient, MiniRead, ServiceRead, ServiceRow } from "../miniDepthClient";
import { localHourWindow, serviceWindowFromParams } from "../miniDepthClient";
import type { SiteDetailClient, SiteDirectoryClient } from "../siteDirectoryClient";
import type { SiteDetailReadModel } from "../siteReadModel";
import { EMPTY_ANALYTICS_CLIENT } from "./analyticsFixtures";
import { expectPlantedPanelRejected, expectV69Panels, panelTitled } from "../../test/panelStructure";
import { settledScreen } from "../../test/settled";

/*
 * W4-02 unit 6: a MINIGRID Site's Performance/Service route renders the v69 `service` panels from the q9 public
 * read (build spec "Run 9 rulings (q9) and pages dry-read", service row; copy ledger; Q20): Unknown is never 0,
 * every measured value carries its measured minutes, `What was needed` stays hatched, and the verification CTA
 * is an unavailable entry (q10-2 pattern).
 */

afterEach(cleanup);

const CODE = "MG-W402-001";
const TZ = "Africa/Addis_Ababa";
const id = (n: number) => `00000000-0000-4000-8000-${String(n).padStart(12, "0")}`;
const SELECTED = { classification: "REGISTERED_SIMULATION", source_ids: [id(2)], evidence_ids: [id(100)] };
const FULL = { required_seconds: 3600, observed_seconds: 3600, source_count: 1, gaps: [] };
const PART = { required_seconds: 3600, observed_seconds: 2400, source_count: 1, gaps: [{ from: "2026-10-06T09:40:00Z", to: "2026-10-06T10:00:00Z" }] };

function row(n: number, over: Partial<ServiceRow> = {}): ServiceRow {
  return {
    asset_id: id(10 + n),
    asset_code: `FDR-${n}`,
    load_label: `Feeder ${n}`,
    role: "UNCLASSIFIED",
    delivered_kw: 10 * n,
    requested_evidence_state: "ACCEPTED",
    assessment: "SUPPORTED",
    coverage: FULL,
    evidence_ids: [id(200 + n)],
    ...over,
  };
}

function read(over: Partial<ServiceRead> = {}): ServiceRead {
  return {
    schema_version: "w4-02.mini.v1",
    domain: "service",
    site: { id: id(1), code: CODE, timezone: TZ },
    window: { from: "2026-10-06T09:00:00Z", to: "2026-10-06T10:00:00Z", known_at: null, bounds: "[from,to)" },
    currentness: {
      state: "CURRENT",
      job_state: "SETTLED",
      windows: [
        {
          local_day: "2026-10-06",
          window_start: "2026-10-06T09:00:00Z",
          window_end: "2026-10-06T10:00:00Z",
          selection_id: 1,
          assessment_revision_id: id(501),
          input_sha256: "a".repeat(64),
          committed_watermark: null,
          state: "CURRENT",
          job_state: "SETTLED",
        },
      ],
    },
    source_provenance: SELECTED,
    selected_source_provenance: SELECTED,
    pending_source_provenance: null,
    status: "SUPPORTED",
    coverage: FULL,
    cards: { delivered_load_kw: 34, interruptions_seen: 0, critical_delivered_kw: 4, unserved_kwh: 0 },
    rows: [row(0, { load_label: "Health post", asset_code: "CRIT-1", role: "CRITICAL", delivered_kw: 4 }), row(1), row(2)],
    limitations: [],
    basis: {},
    links: { dispatch: null, evidence: `/sites/${CODE}/evidence`, financials: null, actions: "/actions" },
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

function renderService(answers: MiniRead<ServiceRead>[], path = `/sites/${CODE}/performance/service?date=2026-10-06`) {
  const queue = [...answers];
  const client: MiniDepthClient = {
    getCapabilities: vi.fn(() => Promise.resolve({ status: "loaded" as const, value: CAPS })),
    getRenewable: vi.fn(() => Promise.resolve({ status: "unavailable" as const, message: null })),
    getService: vi.fn(() => Promise.resolve(queue.length > 1 ? queue.shift()! : queue[0])),
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

const ok = (value: ServiceRead): MiniRead<ServiceRead> => ({ status: "loaded", value });
const main = () => document.querySelector("main") as HTMLElement;
const strip = () => (document.querySelector(".status-strip") as HTMLElement).textContent ?? "";
const cardValues = () => Array.from(document.querySelectorAll("[data-mini-cards] .v69-metric__value")).map((x) => x.textContent);
const subtabs = () =>
  Array.from(document.querySelectorAll('nav[aria-label="Performance sections"] li')).map((li) => [
    li.textContent,
    li.querySelector("a")?.getAttribute("aria-current") ?? null,
  ]);
const bodyRows = () =>
  Array.from(document.querySelectorAll("tbody tr")).map((tr) => Array.from(tr.querySelectorAll("td")).map((td) => td.textContent));

describe("W4-02 unit 6: service keeps the v69 panels, strip, cards and addressed-load table", () => {
  it("supported hour: exact cards with measured minutes, critical first, tab order and the local noon hour", async () => {
    const client = renderService([ok(read())]);
    await settledScreen();
    await screen.findByText("Service assessment: Supported");
    expectV69Panels("service");
    expectPlantedPanelRejected("service");
    expect(subtabs()).toEqual([
      ["Service", "page"],
      ["Dispatch", null],
      ["Fuel", null],
      ["Renewable", null],
      ["Backup", null],
    ]);
    // Q5 / handoff Run 15: the local 12:00-13:00 hour of the local date of the shell's UTC day.
    expect(client.getService).toHaveBeenCalledWith(CODE, {
      from: "2026-10-06T09:00:00.000Z",
      to: "2026-10-06T10:00:00.000Z",
      known_at: null,
    });
    expect(main().textContent).toContain("See delivered power and where requested service remains unknown.");
    expect(strip()).toContain("Selected sources: Generated test data, not field readings");
    expect(strip()).not.toContain("requested-service baseline is incomplete");
    expect(cardValues()).toEqual(["34 kW", "None seen in measured intervals", "4 kW", "0 kWh"]);
    expect(document.querySelector("[data-mini-cards]")?.textContent).toContain("Health post (critical)");
    expect(document.querySelector("[data-mini-cards]")?.textContent).toContain("Measured 60 of 60 minutes");
    const power = panelTitled("Where the power went");
    expect(power.textContent).toContain("Delivered and requested power use the same accepted hour");
    expect(power.querySelector('[data-value-bar-key="needed"]')?.getAttribute("data-value-bar")).toBe("not-known");
    expect(bodyRows()[0]).toEqual([
      "Health post · CRIT-1",
      "Critical service",
      "4 kW · measured 60 of 60 minutes",
      "Accepted requested-power record · 1 cited record · Evidence",
      "Supported",
    ]);
    expect(panelTitled("What is supported").textContent).toContain(
      "These readings show delivered power where measured. They do not establish what customers required.",
    );
    const unlock = panelTitled("What unlocks a service conclusion");
    expect(unlock.textContent).toContain("No further evidence is listed for this hour.");
    expect(unlock.querySelector('[data-link-unavailable="See effect on verification"]')?.textContent).toBe(
      "See effect on verification · Not available yet",
    );
    expect(unlock.querySelector("a")).toBeNull();
    expect(main().textContent).not.toMatch(/grain mill|residential|clinic|18 kW|30 kW/i);
  });

  it("request missing and a partial hour: Limited/Unknown, Unknown cards never 0, missing request roles named", async () => {
    const limited = read({
      status: "LIMITED",
      coverage: PART,
      cards: { delivered_load_kw: null, interruptions_seen: null, critical_delivered_kw: 4, unserved_kwh: null },
      rows: [
        row(0, { load_label: "Health post", asset_code: "CRIT-1", role: "CRITICAL", delivered_kw: 4, requested_evidence_state: "MISSING", assessment: "UNKNOWN" }),
        row(1, { coverage: PART, assessment: "LIMITED", delivered_kw: 9.5 }),
      ],
      limitations: [
        { code: "COVERAGE_GAP", evidence_ids: [id(201)] },
        { code: "REQUEST_BASELINE_MISSING", evidence_ids: [] },
      ],
    });
    renderService([ok(limited)], `/sites/${CODE}/performance/service?from=2026-10-06T09:00:00Z&to=2026-10-06T10:00:00Z`);
    await settledScreen();
    await screen.findByText("Service assessment: Limited");
    expectV69Panels("service");
    expect(strip()).toContain("Delivered power is observed; requested-service baseline is incomplete");
    // q12-7: the ordered limitations sit behind the closed strip disclosure (count line visible).
    expect(document.querySelector("[data-mini-limitations]")).not.toHaveAttribute("open");
    expect(document.querySelector("[data-mini-limitations] summary")?.textContent).toMatch(/^(Limited by \d+ conditions?|Outage-chain assessment: evidence limited)$/);
    expect(Array.from(document.querySelectorAll("[data-mini-limitations] li"), (li) => li.textContent).join("; ")).toContain("Incomplete hour; Requested-service baseline missing");
    expect(cardValues()).toEqual(["Unknown", "Unknown", "4 kW", "Unknown"]);
    expect(document.querySelector("[data-mini-cards]")?.textContent).toContain("Needs demand or request evidence");
    expect(panelTitled("Where the power went").textContent).toContain("Delivered is measured · needed is not");
    expect(panelTitled("Where the power went").textContent).toContain("Measured 40 of 60 minutes");
    const rows = bodyRows();
    expect(rows[0][3]).toContain("No accepted requested-power record");
    expect(rows[0][4]).toBe("Unknown");
    expect(rows[1][2]).toBe("9.5 kW · measured 40 of 60 minutes");
    expect(rows[1][4]).toBe("Limited");
    const unlock = panelTitled("What unlocks a service conclusion").textContent ?? "";
    expect(unlock).toContain("Health post (critical): an accepted requested-power record for the same hour");
    expect(unlock).toContain("Readings that cover the whole hour");
    expect(document.querySelector("[data-mini-local-period]")?.textContent).toBe(`Site-local hour 2026-10-06 12:00–13:00 (${TZ})`);
  });

  it("no selected revision keeps the page shell: Unknown cards and the empty addressed-load copy", async () => {
    const empty = read({
      status: "UNKNOWN",
      currentness: { state: "UNKNOWN", job_state: "NONE", windows: [] },
      selected_source_provenance: null,
      source_provenance: null,
      coverage: null,
      cards: null,
      rows: [],
      limitations: [],
      basis: null,
    });
    renderService([ok(empty)]);
    await settledScreen();
    await screen.findByText("Service assessment: Unknown");
    expectV69Panels("service");
    expect(cardValues()).toEqual(["Unknown", "Unknown", "Unknown", "Unknown"]);
    expect(panelTitled("Delivered power by addressed load").textContent).toContain(
      "No addressed-load readings were accepted for this period.",
    );
    expect(panelTitled("Where the power went").textContent).toContain("Measured minutes: Unknown");
    expect(strip()).toContain("No selected assessment");
  });

  it("503 shows the retry copy and retries; 422 shows the API message with the hour bar editable", async () => {
    const unavailable: MiniRead<ServiceRead> = { status: "refused", httpStatus: 503, code: "MINI_DEPTH_STORE_UNAVAILABLE", message: "x" };
    const client = renderService([unavailable, ok(read())]);
    await settledScreen();
    expect(await screen.findByText("Mini-grid evidence is unavailable right now. Try again.")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    await screen.findByText("Service assessment: Supported");
    expect(client.getService).toHaveBeenCalledTimes(2);
    cleanup();
    const message = "Select a valid complete site-local hour or one to five site-local days.";
    renderService([{ status: "refused", httpStatus: 422, code: "INVALID_WINDOW", message }], `/sites/${CODE}/performance/service?from=a&to=b`);
    await settledScreen();
    expect(await screen.findByText(message)).toBeTruthy();
    expect(document.querySelector("[data-mini-period] select")).not.toBeNull();
  });

  it("the hour bar sends one site-local clock hour as UTC bounds", () => {
    expect(localHourWindow(TZ, "2026-10-06", 0)).toEqual({ from: "2026-10-05T21:00:00.000Z", to: "2026-10-05T22:00:00.000Z" });
    expect(serviceWindowFromParams(new URLSearchParams("date=2026-10-06"), "America/New_York")).toEqual({
      from: "2026-10-05T16:00:00.000Z",
      to: "2026-10-05T17:00:00.000Z",
      known_at: null,
    });
    const params = new URLSearchParams("from=2026-10-06T09:00:00Z&to=2026-10-06T10:00:00Z&known_at=2026-10-07T00:00:00Z");
    expect(serviceWindowFromParams(params, TZ)).toEqual({
      from: "2026-10-06T09:00:00Z",
      to: "2026-10-06T10:00:00Z",
      known_at: "2026-10-07T00:00:00Z",
    });
  });
});
