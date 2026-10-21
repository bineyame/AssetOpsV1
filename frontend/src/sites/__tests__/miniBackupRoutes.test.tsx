import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import type { BackupRead, BackupRow, BackupStep, MiniDepthClient, MiniRead } from "../miniDepthClient";
import type { SiteDetailClient, SiteDirectoryClient } from "../siteDirectoryClient";
import type { SiteDetailReadModel } from "../siteReadModel";
import { EMPTY_ANALYTICS_CLIENT } from "./analyticsFixtures";
import { expectPlantedPanelRejected, expectV69Panels, panelTitled } from "../../test/panelStructure";
import { settledScreen } from "../../test/settled";

/*
 * W4-02 unit 6: a MINIGRID Site's Performance/Backup route renders the v69 `backup` panels from the q9 public read
 * (Q22, q3-8, q5-2/3/4, "Run 9 rulings (q9) and pages dry-read" backup row): the heading is always
 * `Backup readiness: Unknown`, a null outage count reads Unknown (never `0`), the empty chain table keeps one UI-only
 * `No event` row with `No complete outage chain can be assessed`, a real chain shows its own PASS/FAIL/INCOMPLETE,
 * and the four fixed readiness rows cite the accepted step IDs or read `No accepted record`.
 */

afterEach(cleanup);

const CODE = "MG-W402-001";
const TZ = "Africa/Addis_Ababa";
const id = (n: number) => `00000000-0000-4000-8000-${String(n).padStart(12, "0")}`;
const SELECTED = { classification: "REGISTERED_SIMULATION", source_ids: [id(2)], evidence_ids: [id(100)] };
const CRIT = { required_seconds: 3000, observed_seconds: 3000, source_count: 2, gaps: [] };

const step = (code: string, at: string | null, ids: string[], state = "OBSERVED"): BackupStep => ({ code, state, at, evidence_ids: ids });

function chain(over: Partial<BackupRow> = {}): BackupRow {
  return {
    chain_id: "chain-1",
    outage_start: "2026-10-06T09:10:00Z",
    steps: [
      step("LOSS", "2026-10-06T09:10:00Z", [id(400)]),
      step("REQUEST", "2026-10-06T09:10:05Z", [id(401)]),
      step("START", "2026-10-06T09:10:20Z", [id(402)]),
      step("POWER", "2026-10-06T09:10:40Z", [id(403), id(404)]),
      step("LOAD", "2026-10-06T09:11:00Z", [id(405)]),
      step("SERVICE", "2026-10-06T09:12:00Z", [id(405), id(406)]),
    ],
    service_outcome: "RECOVERED",
    result: "PASS",
    critical_recovery: { seconds: 120, target_seconds: 300 },
    coverage: CRIT,
    evidence_ids: [id(400), id(401), id(402), id(403), id(404), id(405), id(406)],
    ...over,
  };
}

function read(over: Partial<BackupRead> = {}): BackupRead {
  return {
    schema_version: "w4-02.mini.v1",
    domain: "backup",
    site: { id: id(1), code: CODE, timezone: TZ },
    window: { from: "2026-10-06T09:00:00Z", to: "2026-10-06T10:00:00Z", known_at: "2026-10-07T00:00:00Z", bounds: "[from,to)" },
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
    status: "UNKNOWN",
    coverage: { required_seconds: 3600, observed_seconds: 0, source_count: 0, gaps: [] },
    cards: { outage_count: null, start_success_count: null, last_witnessed_test_at: null, critical_recovery: null },
    rows: [],
    limitations: [{ code: "BACKUP_CHAIN_INCOMPLETE", evidence_ids: [] }],
    basis: null,
    links: { dispatch: null, evidence: `/sites/${CODE}/evidence`, financials: null, actions: "/actions" },
    ...over,
  } as BackupRead;
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

function renderBackup(answers: MiniRead<BackupRead>[], path = `/sites/${CODE}/performance/backup?date=2026-10-06`) {
  const queue = [...answers];
  const unavailable = () => Promise.resolve({ status: "unavailable" as const, message: null });
  const client: MiniDepthClient = {
    getCapabilities: vi.fn(() => Promise.resolve({ status: "loaded" as const, value: CAPS })),
    getRenewable: vi.fn(unavailable),
    getService: vi.fn(unavailable),
    getFuel: vi.fn(unavailable),
    getBackup: vi.fn(() => Promise.resolve(queue.length > 1 ? queue.shift()! : queue[0])),
  };
  render(
    <MemoryRouter initialEntries={[path]}>
      <App flags={featureFlagsWith(false)} siteDirectory={directory} siteDetail={detail} siteAnalytics={EMPTY_ANALYTICS_CLIENT} miniDepth={client} />
    </MemoryRouter>,
  );
  return client;
}

const ok = (value: BackupRead): MiniRead<BackupRead> => ({ status: "loaded", value });
const main = () => document.querySelector("main") as HTMLElement;
const strip = () => (document.querySelector(".status-strip") as HTMLElement).textContent ?? "";
const cardValues = () => Array.from(document.querySelectorAll("[data-mini-cards] .v69-metric__value")).map((x) => x.textContent);
const subtabs = () =>
  Array.from(document.querySelectorAll('nav[aria-label="Performance sections"] li')).map((li) => [
    li.textContent,
    li.querySelector("a")?.getAttribute("aria-current") ?? null,
  ]);
const rowsOf = (title: string) =>
  Array.from(panelTitled(title).querySelectorAll("tbody tr")).map((tr) => Array.from(tr.querySelectorAll("td")).map((td) => td.textContent));

describe("W4-02 unit 6: backup keeps the v69 strip, cards, chains, readiness, operating and next panels", () => {
  it("no chain: readiness Unknown, Unknown outage count, one No event row with the honest copy, all five tabs", async () => {
    const client = renderBackup([ok(read())]);
    await settledScreen();
    await screen.findByText("Backup readiness: Unknown");
    expectV69Panels("backup");
    expectPlantedPanelRejected("backup");
    expect(subtabs()).toEqual([
      ["Service", null],
      ["Dispatch", null],
      ["Fuel", null],
      ["Renewable", null],
      ["Backup", "page"],
    ]);
    expect(client.getBackup).toHaveBeenCalledWith(CODE, {
      from: "2026-10-06T09:00:00.000Z",
      to: "2026-10-06T10:00:00.000Z",
      known_at: null,
    });
    expect(main().textContent).toContain("Performance · backup start and service recovery");
    expect(strip()).toContain("Generator operation alone is not a witnessed start-and-recovery test");
    // q12-7: the ordered limitations sit behind the closed strip disclosure (count line visible).
    expect(document.querySelector("[data-mini-limitations]")).not.toHaveAttribute("open");
    expect(document.querySelector("[data-mini-limitations] summary")?.textContent).toMatch(/^(Limited by \d+ conditions?|Outage-chain assessment: evidence limited)$/);
    expect(Array.from(document.querySelectorAll("[data-mini-limitations] li"), (li) => li.textContent).join("; ")).toContain("No complete outage chain");
    expect(strip()).not.toContain("evidence limited");
    expect(strip()).toContain("Selected sources: Generated test data, not field readings");
    expect(strip()).not.toMatch(/registered_simulation/i);
    expect(cardValues()).toEqual(["Unknown", "Unknown", "No record", "Unknown"]);
    expect(rowsOf("Backup event chains")).toEqual([
      ["No complete outage chain can be assessed", "—", "—", "—", "—", "—", "—", "No event"],
    ]);
    expect(main().textContent).not.toContain("No outage in the selected hour");
    expect(rowsOf("Backup readiness evidence")).toEqual([
      ["Supply interruption", "No accepted record", "No outage-chain assessment"],
      ["Start command and state", "No accepted record", "No outage-chain assessment"],
      ["Power restored to critical service", "No accepted record", "No outage-chain assessment"],
      ["Witnessed outcome", "No accepted record", "Readiness remains unverified"],
    ]);
    const operating = panelTitled("Operating evidence");
    expect(operating.textContent).toContain(
      "Generator operation supports runtime reconstruction. It does not establish automatic backup readiness.",
    );
    expect(operating.querySelector("a")).toBeNull();
    expect(operating.querySelector('[data-link-unavailable="Open Dispatch"]')).not.toBeNull();
    const next = panelTitled("Next evidence");
    expect(next.textContent).toContain(
      "Record a witnessed start-to-service test with command, state, power path and critical-service observations.",
    );
    expect(next.querySelector("a")?.getAttribute("href")).toBe("/actions");
    expect(next.querySelector("a")?.textContent).toBe("Browse Actions →");
    expect(main().textContent).not.toMatch(/Outages in window\s*0|Backup readiness: (Supported|Ready)/);
  });

  it("a PASS chain and an INCOMPLETE chain: ordered step cells, own results, cited readiness IDs", async () => {
    const incomplete = chain({
      chain_id: "chain-2",
      outage_start: "2026-10-06T09:40:00Z",
      steps: [
        step("LOSS", "2026-10-06T09:40:00Z", [id(410)]),
        step("REQUEST", null, [], "MISSING"),
        step("START", "2026-10-06T09:40:30Z", [id(412), id(413)], "CONFLICT"),
        step("POWER", null, [], "MISSING"),
        step("LOAD", null, [], "MISSING"),
        step("SERVICE", null, [], "MISSING"),
      ],
      service_outcome: "UNKNOWN",
      result: "INCOMPLETE",
      critical_recovery: null,
    });
    renderBackup([
      ok(read({
        status: "LIMITED",
        rows: [chain(), incomplete],
        cards: { outage_count: null, start_success_count: 1, last_witnessed_test_at: null, critical_recovery: { seconds: 120, target_seconds: 300 } },
        limitations: [{ code: "CONFLICT", evidence_ids: [id(412), id(413)] }],
        links: { dispatch: `/sites/${CODE}/performance/dispatch`, evidence: null, financials: null, actions: "/actions" },
      })),
    ]);
    await settledScreen();
    await screen.findByText("Backup readiness: Unknown");
    expectV69Panels("backup");
    expect(strip()).toContain("Outage-chain assessment: evidence limited");
    // q12-7: the ordered limitations sit behind the closed strip disclosure (count line visible).
    expect(document.querySelector("[data-mini-limitations]")).not.toHaveAttribute("open");
    expect(document.querySelector("[data-mini-limitations] summary")?.textContent).toMatch(/^(Limited by \d+ conditions?|Outage-chain assessment: evidence limited)$/);
    expect(Array.from(document.querySelectorAll("[data-mini-limitations] li"), (li) => li.textContent).join("; ")).toContain("Conflicting evidence");
    expect(cardValues()).toEqual(["Unknown", "1 witnessed success", "No record", "2 min"]);
    const cards = document.querySelector("[data-mini-cards]")?.textContent ?? "";
    // q11-3(a): only chain-1 has both REQUEST and START OBSERVED; chain-2's conflicting START is not a pair.
    expect(cards).toContain("Of 1 witnessed request/result pair in shown chains");
    expect(cards).toContain("Target 5 min · latest valid chain");
    expect(rowsOf("Backup event chains")).toEqual([
      ["2026-10-06 12:10", "Observed 12:10", "Observed 12:10", "Observed 12:10", "Observed 12:10", "Observed 12:11", "Observed 12:12 · Recovered", "Pass"],
      ["2026-10-06 12:40", "Observed 12:40", "No accepted record", "Conflicting records 12:40", "No accepted record", "No accepted record", "No accepted record · Unknown", "Incomplete"],
    ]);
    // q12-7: each evidence cell is a count plus a closed `Inspect IDs` disclosure holding the full distinct ordered list.
    const readiness = rowsOf("Backup readiness evidence");
    expect(readiness.map((r) => [r[0], r[2]])).toEqual([
      ["Supply interruption", "Observed · chain result Incomplete"],
      ["Start command and state", "Conflicting records · chain result Incomplete"],
      ["Power restored to critical service", "No accepted record · chain result Incomplete"],
      ["Witnessed outcome", "Readiness remains unverified"],
    ]);
    expect(readiness.map((r) => /^(\d+ cited records?|No accepted record)/.exec(r[1])?.[0])).toEqual([
      "2 cited records",
      "4 cited records",
      "4 cited records",
      "No accepted record",
    ]);
    const ids = (label: string) => Array.from(document.querySelectorAll(`[data-mini-ids="${label}"] li`), (li) => li.textContent);
    expect(ids("Supply interruption")).toEqual([id(400), id(410)]);
    expect(ids("Start command and state")).toEqual([id(401), id(402), id(412), id(413)]);
    expect(ids("Power restored to critical service")).toEqual([id(403), id(404), id(405), id(406)]);
    document.querySelectorAll("[data-mini-ids]").forEach((d) => expect(d).not.toHaveAttribute("open"));
    // Final review H4: the count and its `Inspect IDs` disclosure share one line (one inline wrapper per row).
    const count = document.querySelector('[data-mini-readiness-count="Supply interruption"]') as HTMLElement;
    expect(count.querySelector("summary")?.textContent).toBe("Inspect IDs");
    expect(count.firstChild?.textContent).toBe("2 cited records · ");
    expect(count.querySelector('[data-mini-ids="Supply interruption"]')).not.toBeNull();
    expect(panelTitled("Operating evidence").querySelector("a")?.getAttribute("href")).toBe(`/sites/${CODE}/performance/dispatch`);
  });

  it("no selected revision keeps the page shell: Unknown cards, the No event row and the readiness gaps", async () => {
    renderBackup([
      ok(read({
        currentness: { state: "UNKNOWN", job_state: "NONE", windows: [] },
        selected_source_provenance: null,
        source_provenance: null,
        coverage: null,
        cards: null,
        limitations: [],
      })),
    ]);
    await settledScreen();
    await screen.findByText("Backup readiness: Unknown");
    expectV69Panels("backup");
    expect(cardValues()).toEqual(["Unknown", "Unknown", "No record", "Unknown"]);
    expect(rowsOf("Backup event chains")[0][0]).toBe("No complete outage chain can be assessed");
    expect(strip()).toContain("No selected assessment");
    expect(document.querySelector("[data-mini-cards]")?.textContent ?? "").toContain("No witnessed start request and result");
  });

  it("q11-3/q11-4: a count above the witnessed pairs has no `Of N`; the latest chain is chosen by outage start", async () => {
    const earlier = chain({ chain_id: "chain-0", outage_start: "2026-10-06T09:05:00Z" });
    const later = chain({
      chain_id: "chain-9",
      outage_start: "2026-10-06T09:50:00Z",
      steps: [
        step("LOSS", "2026-10-06T09:50:00Z", [id(420)]),
        step("REQUEST", null, [], "MISSING"),
        step("START", null, [], "MISSING"),
        step("POWER", null, [], "MISSING"),
        step("LOAD", null, [], "MISSING"),
        step("SERVICE", null, [], "MISSING"),
      ],
      service_outcome: "UNKNOWN",
      result: "INCOMPLETE",
      critical_recovery: null,
    });
    renderBackup([
      ok(read({
        rows: [later, earlier],
        cards: { outage_count: null, start_success_count: 2, last_witnessed_test_at: null, critical_recovery: null },
      })),
    ]);
    await settledScreen();
    await screen.findByText("Backup readiness: Unknown");
    const cards = document.querySelector("[data-mini-cards]")?.textContent ?? "";
    expect(cards).toContain("2 witnessed successes");
    expect(cards).toContain("Witnessed pair count unavailable");
    expect(cards).not.toContain("Of ");
    expect(screen.getByRole("columnheader", { name: "Current claim (latest observed outage chain)" })).toBeTruthy();
    const readiness = rowsOf("Backup readiness evidence");
    expect(readiness[0][2]).toBe("Observed · chain result Incomplete");
    expect(readiness[1][2]).toBe("No accepted record · chain result Incomplete");
    expect(readiness[3]).toEqual(["Witnessed outcome", "No accepted record", "Readiness remains unverified"]);
  });

  it("503 shows the retry copy and retries", async () => {
    const unavailable: MiniRead<BackupRead> = { status: "refused", httpStatus: 503, code: "MINI_DEPTH_STORE_UNAVAILABLE", message: "x" };
    const client = renderBackup([unavailable, ok(read())]);
    await settledScreen();
    expect(await screen.findByText("Mini-grid evidence is unavailable right now. Try again.")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    await screen.findByText("Backup readiness: Unknown");
    expect(client.getBackup).toHaveBeenCalledTimes(2);
  });
});
