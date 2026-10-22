/**
 * W5-01a C2 (`.agent/W5-01-build-spec.md` C2, literal ledger and readiness pass 3): the cold depth client's exact
 * Cooling validation and labels, and the Cooling page through the real App route with a stubbed depth client
 * (`cooling_dto_and_labels`, `cooling_state_copy`, `cooling_panels`, `cooling_nav_and_routes`).
 */
import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import { expectV69Panels } from "../../test/panelStructure";
import { settledScreen } from "../../test/settled";
import { type ColdAssessmentClient, type ColdRead, NO_WINDOW } from "../coldAssessmentClient";
import {
  type ColdCoolingRead,
  type ColdDepthClient,
  COOLING_CONTEXT_LABELS,
  coolingCardLabels,
  createColdDepthClient,
  isColdCoolingRead,
} from "../ColdDepthClient";
import { COOLING_LOADING } from "../ColdCooling";
import { coldUiHref } from "../coldSiteViews";
import { coldSiteRoutes } from "../../shell/coldSiteRoutes";
import type { SiteDetailClient, SiteDirectoryClient } from "../siteDirectoryClient";
import type { SiteDetailReadModel } from "../siteReadModel";
import { EMPTY_ANALYTICS_CLIENT } from "./analyticsFixtures";

const SITE_CODE = "COLD-001";

const DOOR_OPEN = "0f6c1a52-6f1d-4c6b-9a43-0d9d3b6d2a10";
const DOOR_CLOSE = "1a2b3c4d-5e6f-4a1b-8c2d-3e4f5a6b7c8d";
const GRID = "2b3c4d5e-6f70-4b2c-9d3e-4f5a6b7c8d9e";
const PROBE = "3c4d5e6f-7081-4c3d-ae4f-5a6b7c8d9eaf";
const Q = "from=2026-10-06T19%3A00%3A00Z&to=2026-10-06T20%3A05%3A00Z";

/** A C1 backup-failed shaped `/cold/cooling` answer (exact keys of the C1 "Cooling payload" table). */
function coolingBody(overrides: Record<string, unknown> = {}, cooling: Record<string, unknown> = {}) {
  return {
    schema_version: "cold-depth-1",
    site_id: "7d1e2f30-4a5b-4c6d-8e7f-901a2b3c4d5e",
    window: {
      from: "2026-10-06T19:00:00Z",
      to: "2026-10-06T20:05:00Z",
      known_at: "2026-10-22T08:00:00.123456Z",
      committed_watermark: "2026-10-22T08:00:00.123456Z",
    },
    selection: {
      state: "CURRENT",
      assessment_revision_ids: ["4d5e6f70-8192-4d4e-bf50-6b7c8d9eafb0"],
      accepted_evidence_ids: [DOOR_OPEN, DOOR_CLOSE, GRID, PROBE].sort(),
      source_provenance: { classification: "SIMULATED_REPLAY", source_ids: [], evidence_ids: [], basis_sha256: null },
    },
    cooling: {
      recovery_state: "LIMITED",
      policy_high_deg_c: "4",
      selected_points: [{ role: "chamber_temperature", source_time: "2026-10-06T19:20:00Z", evidence_ids: [PROBE] }],
      observed_restart_at: null,
      observed_return_to_policy_at: null,
      duration_lower_seconds: null,
      duration_upper_seconds: null,
      comparison_state: "CONTEXT_MISSING",
      context: [
        { label: "Ambient temperature", state: "Unknown", evidence_ids: [], duration_seconds: null },
        { label: "Power availability", state: "Observed", evidence_ids: [GRID], duration_seconds: null },
        { label: "Door-open duration", state: "Observed", evidence_ids: [DOOR_OPEN, DOOR_CLOSE].sort(), duration_seconds: 60 },
        { label: "Loading / batch", state: "Unknown", evidence_ids: [], duration_seconds: null },
        { label: "Defrost", state: "Unknown", evidence_ids: [], duration_seconds: null },
      ],
      ...cooling,
    },
    links: {
      temperature: `/api/sites/COLD-001/cold/temperature?${Q}`,
      backup: `/api/sites/COLD-001/cold/backup-chain?${Q}`,
      evidence: `/api/sites/COLD-001/cold/evidence?${Q}`,
      health: `/api/sites/COLD-001/cold/health?${Q}`,
    },
    ...overrides,
  };
}

const without = (value: Record<string, unknown>, key: string) => {
  const copy = { ...value };
  delete copy[key];
  return copy;
};

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("cooling_dto_and_labels", () => {
  it("accepts the exact C1 key sets in any order", () => {
    const body = coolingBody();
    expect(isColdCoolingRead(body)).toBe(true);
    const reordered: Record<string, unknown> = Object.fromEntries(Object.entries(body).reverse());
    reordered.cooling = Object.fromEntries(Object.entries(body.cooling).reverse());
    expect(isColdCoolingRead(reordered)).toBe(true);
    expect(isColdCoolingRead(coolingBody({}, { recovery_state: "CONTRADICTORY", policy_high_deg_c: null, selected_points: [] }))).toBe(true);
  });

  it("refuses a missing, extra or ill-typed key at every level as malformed", () => {
    const body = coolingBody();
    const bad: unknown[] = [
      without(body, "links"),
      { ...body, extra: 1 },
      { ...body, schema_version: "cold-depth-2" },
      { ...body, window: { ...body.window, committed_watermark: 7 } },
      { ...body, window: without(body.window, "known_at") },
      { ...body, selection: { ...body.selection, state: "SELECTED" } },
      { ...body, selection: { ...body.selection, accepted_evidence_ids: null } },
      { ...body, selection: { ...body.selection, source_provenance: null } },
      { ...body, links: { ...body.links, cooling: null } },
      { ...body, links: { ...body.links, health: 3 } },
      coolingBody({}, { recovery_state: "CURRENT" }),
      coolingBody({}, { policy_high_deg_c: 4 }),
      coolingBody({}, { observed_restart_at: "2026-10-06T19:30:00Z" }),
      coolingBody({}, { duration_lower_seconds: 0 }),
      coolingBody({}, { duration_upper_seconds: 2520 }),
      coolingBody({}, { comparison_state: "MATCHED" }),
      coolingBody({}, { extra: null }),
      coolingBody({}, { selected_points: [{ role: "x", source_time: "t" }] }),
      coolingBody({}, { context: body.cooling.context.slice(0, 4) }),
      coolingBody({}, { context: [...body.cooling.context].reverse() }),
      coolingBody({}, { context: body.cooling.context.map((r) => ({ ...r, state: r.state === "Observed" ? "Matched" : r.state })) }),
      coolingBody({}, { context: body.cooling.context.map((r, i) => (i === 0 ? { ...r, duration_seconds: 0 } : r)) }),
      coolingBody({}, { context: body.cooling.context.map((r, i) => (i === 2 ? { ...r, duration_seconds: 60.5 } : r)) }),
      coolingBody({}, { context: body.cooling.context.map((r, i) => (i === 0 ? { ...r, evidence_ids: [GRID] } : r)) }),
      coolingBody({}, { context: body.cooling.context.map((r, i) => (i === 1 ? without(r, "duration_seconds") : r)) }),
      [],
      null,
    ];
    for (const value of bad) expect(isColdCoolingRead(value)).toBe(false);
    expect(COOLING_CONTEXT_LABELS).toEqual(["Ambient temperature", "Power availability", "Door-open duration", "Loading / batch", "Defrost"]);
  });

  it("reads through the live route address and names a malformed 200 and a refusal", async () => {
    const calls: string[] = [];
    let answer: { body: unknown; status: number } = { body: coolingBody(), status: 200 };
    vi.stubGlobal("fetch", async (path: string) => {
      calls.push(path);
      return new Response(JSON.stringify(answer.body), { status: answer.status });
    });
    const client = createColdDepthClient();
    const window = { from: "2026-10-06T19:00:00Z", to: "2026-10-06T20:05:00Z", known_at: "2026-10-22T08:00:00Z" };
    expect((await client.getCooling("COLD LAB/1", window)).status).toBe("loaded");
    expect(calls[0]).toBe(
      "/api/sites/COLD%20LAB%2F1/cold/cooling?from=2026-10-06T19%3A00%3A00Z&to=2026-10-06T20%3A05%3A00Z&known_at=2026-10-22T08%3A00%3A00Z",
    );
    answer = { body: coolingBody({}, { context: [] }), status: 200 };
    expect(await client.getCooling("COLD-LAB-001", NO_WINDOW)).toEqual({
      status: "unavailable",
      message: "The cold depth read answered in an unexpected shape.",
    });
    expect(calls[1]).toBe("/api/sites/COLD-LAB-001/cold/cooling");
    answer = { body: { error: { code: "COLD_SOURCE_DISCLOSURE_FORBIDDEN", message: "Source disclosure is not permitted." } }, status: 403 };
    expect(await client.getCooling("COLD-LAB-001", NO_WINDOW)).toEqual({
      status: "refused",
      httpStatus: 403,
      code: "COLD_SOURCE_DISCLOSURE_FORBIDDEN",
      message: "Source disclosure is not permitted.",
    });
  });

  it("labels the first two cards from policy_high_deg_c verbatim, or back to policy when null", () => {
    expect(coolingCardLabels("4")).toEqual({ usual: "Usual time back to 4°C", current: "This time back to 4°C" });
    expect(coolingCardLabels("3.5")).toEqual({ usual: "Usual time back to 3.5°C", current: "This time back to 3.5°C" });
    expect(coolingCardLabels(null)).toEqual({ usual: "Usual time back to policy", current: "This time back to policy" });
  });
});

/* ---------- the page, through the real App route ---------- */

const SITE = {
  site_id: SITE_CODE,
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
const never = () => new Promise<never>(() => undefined);
const down = () => Promise.resolve({ status: "unavailable" as const, message: null });
const COOLING_PATH = `/sites/${SITE_CODE}/performance/cooling?${Q}`;
const loaded = (body: unknown): ColdRead<ColdCoolingRead> => ({ status: "loaded", value: body as ColdCoolingRead });

function renderCooling(path: string, answer: () => Promise<ColdRead<ColdCoolingRead>>, depth?: ColdDepthClient) {
  const coldAssessment: ColdAssessmentClient = {
    getTemperature: vi.fn(down),
    getBackupChain: vi.fn(down),
    listFindings: vi.fn(down),
    getFinding: vi.fn(down),
  };
  const client: ColdDepthClient = depth ?? { getCooling: vi.fn(answer), getHealth: vi.fn(never) };
  render(
    <MemoryRouter initialEntries={[path]}>
      <App
        flags={featureFlagsWith(false)}
        siteDirectory={directory}
        siteDetail={detail}
        siteAnalytics={EMPTY_ANALYTICS_CLIENT}
        coldAssessment={coldAssessment}
        coldDepth={client}
      />
    </MemoryRouter>,
  );
  return { client, coldAssessment };
}

const main = () => document.querySelector("main") as HTMLElement;

/** `settledScreen`, then the Cooling read itself (its loading sentence is page-local). */
async function settledCooling() {
  await settledScreen();
  await waitFor(() => {
    const text = document.body.textContent ?? "";
    if (text.includes(COOLING_LOADING) || document.querySelector("main") === null) throw new Error("the cooling read has not settled");
  });
}

const statusLine = () => main().querySelector('.status-strip[aria-label="Cooling comparison"]') as HTMLElement;
const cards = () =>
  Array.from(main().querySelectorAll("[data-cooling-card]")).map((card) => Array.from(card.children).map((c) => c.textContent));
const notice = () => main().querySelector("[data-cooling-state-notice]");
const rowsOf = (table: HTMLElement) =>
  Array.from(table.querySelectorAll("tbody tr")).map((tr) => Array.from(tr.children).map((c) => c.textContent));
const crumbs = () =>
  Array.from(document.querySelectorAll('nav[aria-label="Breadcrumb"] li')).map((li) => li.textContent?.replace(/›/g, "").trim());

describe("cooling_dto_and_labels (page)", () => {
  it("renders the policy labels verbatim and back to policy when null", async () => {
    renderCooling(COOLING_PATH, () => Promise.resolve(loaded(coolingBody())));
    await settledCooling();
    expect(cards().map((c) => c[0])).toEqual(["Usual time back to 4°C", "This time back to 4°C", "Difference", "Comparable?"]);
    cleanup();
    renderCooling(COOLING_PATH, () => Promise.resolve(loaded(coolingBody({}, { policy_high_deg_c: "3.5" }))));
    await settledCooling();
    expect(cards().map((c) => c[0]).slice(0, 2)).toEqual(["Usual time back to 3.5°C", "This time back to 3.5°C"]);
    cleanup();
    renderCooling(COOLING_PATH, () => Promise.resolve(loaded(coolingBody({}, { policy_high_deg_c: null }))));
    await settledCooling();
    expect(cards().map((c) => c[0]).slice(0, 2)).toEqual(["Usual time back to policy", "This time back to policy"]);
  });

  it("a malformed 200 through the real client renders the Cold depth unavailable refusal, not an empty page", async () => {
    vi.stubGlobal("fetch", async () => new Response(JSON.stringify(coolingBody({}, { context: [] })), { status: 200 }));
    renderCooling(COOLING_PATH, never, createColdDepthClient());
    await settledCooling();
    const refusal = main().querySelector('[data-page-refusal="cold-depth"]') as HTMLElement;
    expect(refusal.querySelector(".page-refusal__title")?.textContent).toBe("Cold depth unavailable");
    expect(refusal.querySelector("[data-cold-depth-error]")?.textContent).toBe("The cold depth read answered in an unexpected shape.");
    expect(main().querySelector("[data-cooling-card]")).toBeNull();
    expect(main().querySelector("section.panel")).toBeNull();
  });

  it("links Inspect recovery basis and Open Backup through coldUiHref with the exact query; null renders text", async () => {
    renderCooling(COOLING_PATH, () => Promise.resolve(loaded(coolingBody())));
    await settledCooling();
    expect(main().querySelector("a[data-cooling-basis]")?.getAttribute("href")).toBe(`/sites/${SITE_CODE}/performance/temperature?${Q}`);
    expect(main().querySelector("a[data-cooling-basis]")?.textContent).toBe("Inspect recovery basis →");
    expect(main().querySelector("a[data-cooling-backup]")?.getAttribute("href")).toBe(`/sites/${SITE_CODE}/performance/backup?${Q}`);
    expect(main().querySelector("a[data-cooling-backup]")?.textContent).toBe("Open Backup →");
    cleanup();
    const nulls = coolingBody({ links: { temperature: null, backup: null, evidence: null, health: null } });
    renderCooling(COOLING_PATH, () => Promise.resolve(loaded(nulls)));
    await settledCooling();
    expect(main().querySelector("a[data-cooling-basis], a[data-cooling-backup]")).toBeNull();
    expect(main().querySelector("[data-cooling-basis]")?.textContent).toBe("Inspect recovery basis →");
    expect(main().querySelector("[data-cooling-backup]")?.textContent).toBe("Open Backup →");
  });

  it("never shows the mock's 36/42 minutes or +17% as measured, and the W2 comparison stays unmeasured", async () => {
    renderCooling(COOLING_PATH, () => Promise.resolve(loaded(coolingBody())));
    await settledCooling();
    const text = main().textContent ?? "";
    expect(text).not.toMatch(/\b(36|42)\s*min/);
    expect(text).not.toContain("+17%");
    expect(cards().map((c) => c[1])).toEqual(["Unknown", "Not established", "Unknown", "Not yet"]);
  });
});

describe("cooling_state_copy", () => {
  it.each([
    ["LIMITED", "Comparison limited", "Confidence: Low", "Observed cooling response is incomplete; ambient, loading and defrost context is missing.", "Ambient, loading and defrost records missing"],
    ["CONTRADICTORY", "Comparison contradictory", "Confidence: Unknown", "Selected cooling observations conflict; no recovery comparison is supported.", "Conflicting selected observations prevent a comparison"],
    ["UNKNOWN", "Comparison unknown", "Confidence: Unknown", "No selected cooling assessment establishes a recovery comparison for this window.", "No selected comparison basis"],
  ] as const)("%s: status, confidence, subtitle and the fourth note", async (state, status, confidence, subtitle, note) => {
    renderCooling(COOLING_PATH, () => Promise.resolve(loaded(coolingBody({}, { recovery_state: state }))));
    await settledCooling();
    const line = statusLine();
    expect(Array.from(line.querySelectorAll(".badge")).map((b) => b.textContent)).toEqual([status, confidence]);
    expect(line.textContent).toContain(subtitle);
    expect(cards()).toEqual([
      ["Usual time back to 4°C", "Unknown", "No matched earlier window"],
      ["This time back to 4°C", "Not established", "No ordered compressor-to-policy recovery assessment"],
      ["Difference", "Unknown", "A comparison is not supported"],
      ["Comparable?", "Not yet", note],
    ]);
  });

  it.each([
    ["CURRENT", null],
    ["PENDING_RECOMPUTE", "New evidence is waiting to be assessed. Earlier selected observations are shown, not a current conclusion."],
    ["HISTORICAL", "Read at an earlier evidence cutoff; newer committed evidence exists."],
    ["STALE_SOURCE", "The selected source is stale for this window."],
    ["UNKNOWN", "No selected cold assessment covers this window yet."],
  ] as const)("selection %s: the matrix status stays and the amber notice sits directly below the status line", async (state, sentence) => {
    const body = coolingBody();
    renderCooling(COOLING_PATH, () => Promise.resolve(loaded({ ...body, selection: { ...body.selection, state } })));
    await settledCooling();
    expect(Array.from(statusLine().querySelectorAll(".badge")).map((b) => b.textContent)).toEqual(["Comparison limited", "Confidence: Low"]);
    if (sentence === null) {
      expect(notice()).toBeNull();
    } else {
      expect(notice()?.textContent).toBe(sentence);
      expect(notice()?.className).toBe("notice v69-notice");
      expect(statusLine().nextElementSibling).toBe(notice());
    }
  });

  it("the backup-failed door pair is observed, so nothing says door context is missing", async () => {
    renderCooling(COOLING_PATH, () => Promise.resolve(loaded(coolingBody())));
    await settledCooling();
    expect(main().textContent).not.toMatch(/door[^.]*missing|missing[^.]*door/i);
    expect(main().querySelector("[data-cooling-notice]")?.textContent).toBe(
      "These records do not establish cooling degradation or compressor failure. Record loading and door activity and compare a later recovery under similar conditions.",
    );
  });

  it("a server refusal shows the heading, the exact code and message, and Retry re-reads the same window", async () => {
    const answer = () =>
      Promise.resolve<ColdRead<ColdCoolingRead>>({ status: "refused", httpStatus: 403, code: "COLD_SOURCE_DISCLOSURE_FORBIDDEN", message: "Source disclosure is not permitted." });
    const { client } = renderCooling(COOLING_PATH, answer);
    await settledCooling();
    const refusal = main().querySelector('[data-page-refusal="cold-depth"]') as HTMLElement;
    expect(refusal.querySelector(".page-refusal__title")?.textContent).toBe("Cold depth unavailable");
    expect(refusal.querySelector("[data-cold-depth-error]")?.textContent).toBe("COLD_SOURCE_DISCLOSURE_FORBIDDEN Source disclosure is not permitted.");
    expect(main().querySelector("[data-cold-date-bar-requested]")).not.toBeNull();
    expect(refusal.querySelector("button[data-cold-retry]")?.textContent).toBe("Retry");
    fireEvent.click(refusal.querySelector("button[data-cold-retry]") as HTMLElement);
    await waitFor(() => expect(client.getCooling).toHaveBeenCalledTimes(2));
    const calls = vi.mocked(client.getCooling).mock.calls;
    expect(calls[1]).toEqual(calls[0]);
    expect(calls[0]).toEqual([SITE_CODE, { from: "2026-10-06T19:00:00Z", to: "2026-10-06T20:05:00Z", known_at: null }]);
  });

  it("a 422 invalid window hides the requested date line; an unreachable read says so", async () => {
    renderCooling(COOLING_PATH, () =>
      Promise.resolve<ColdRead<ColdCoolingRead>>({ status: "refused", httpStatus: 422, code: "COLD_WINDOW_INVALID", message: "from must be before to" }),
    );
    await settledCooling();
    expect(main().querySelector("[data-cold-date-bar]")).toBeNull();
    expect(main().querySelector("[data-cold-depth-error]")?.textContent).toBe("COLD_WINDOW_INVALID from must be before to");
    cleanup();
    renderCooling(COOLING_PATH, () => Promise.resolve<ColdRead<ColdCoolingRead>>({ status: "unavailable", message: null }));
    await settledCooling();
    expect(main().querySelector("[data-cold-depth-error]")?.textContent).toBe("The cold depth read could not be reached.");
  });

  it("shows the loading sentence while the read is pending", async () => {
    renderCooling(COOLING_PATH, never);
    await settledScreen();
    await waitFor(() => expect(main().querySelector("p.prose")?.textContent).toBe(COOLING_LOADING));
  });
});

describe("cooling_panels", () => {
  it("keeps the v69 panel titles and order, the four cards and the five context rows exactly", async () => {
    renderCooling(COOLING_PATH, () => Promise.resolve(loaded(coolingBody())));
    await settledCooling();
    expectV69Panels("cooling");
    // Codex retrospective Q-C2-3: one graphic, its svg inside the registered region, selected marks only.
    const graphic = main().querySelector('[aria-labelledby="cold-cooling-recovery-heading"] figure[data-cooling-graphic="marks"]') as HTMLElement;
    expect(main().querySelectorAll("svg")).toHaveLength(1);
    expect(graphic.querySelector(".cold-depth-graphic__scroll > svg")).not.toBeNull();
    expect(Array.from(graphic.querySelectorAll("[data-cooling-lane] text")).map((t) => t.textContent)).toEqual(["Compressor running", "Chamber temperature"]);
    expect(Array.from(graphic.querySelectorAll("[data-cooling-mark]")).map((m) => [m.getAttribute("data-cooling-mark"), m.querySelector("text")?.textContent, m.querySelector("title")?.textContent])).toEqual([
      ["chamber_temperature", "19:20:00", "Chamber temperature · 19:20:00 UTC"],
    ]);
    expect(graphic.querySelectorAll("path, polyline, polygon")).toHaveLength(0);
    expect(graphic.textContent).not.toMatch(/°C|\b(36|42)\s*min|\+17%/);
    expect(main().querySelector("[data-cooling-empty]")?.textContent).toBe("No accepted recovery sequence in this window.");
    const context = main().querySelector('[aria-labelledby="cold-cooling-context-heading"] table') as HTMLElement;
    // Codex retrospective Q-C2-2: the mock's `Match` heading; with CONTEXT_MISSING every cell is `Not established`.
    expect(Array.from(context.querySelectorAll("thead th")).map((th) => th.textContent)).toEqual(["Factor", "Evidence", "Match"]);
    expect(rowsOf(context)).toEqual([
      ["Ambient temperature", "Not selected by the cooling assessment", "Not established"],
      ["Power availability", "1 accepted grid power record", "Not established"],
      ["Door-open duration", "Door open for 1 min", "Not established"],
      ["Loading / batch", "No loading record role", "Not established"],
      ["Defrost", "No defrost record role", "Not established"],
    ]);
    expect(main().textContent).not.toMatch(/\bMatched\b/);
    expect(context.textContent).not.toContain(GRID);
    const points = main().querySelector('[aria-labelledby="cold-cooling-recovery-heading"] table') as HTMLElement;
    expect(Array.from(points.querySelectorAll("thead th")).map((th) => th.textContent)).toEqual(["Step", "Time (UTC)", "Evidence"]);
    expect(rowsOf(points)).toEqual([["Chamber temperature", "19:20:00", PROBE]]);
    expect(main().textContent).toContain("Selected first observations only; not a recovery curve.");
    const next = Array.from(main().querySelectorAll("[data-attention-item]"));
    expect(next.map((item) => item.querySelector("h3")?.textContent)).toEqual(["Record a comparable recovery", "Inspect the backup sequence"]);
    expect(next[0].textContent).toContain("Keep load, door, ambient, defrost and cooling-energy records.");
    expect(next[0].querySelector("a")).toBeNull();
  });

  it("the other context evidence wordings and the empty recovery sentence", async () => {
    const base = coolingBody().cooling.context;
    const evidenceCells = () => Array.from(main().querySelectorAll("[data-cooling-context] td:first-of-type")).map((td) => td.textContent);
    const two = base.map((row) =>
      row.label === "Power availability" ? { ...row, evidence_ids: [GRID, DOOR_OPEN].sort() } : row.label === "Door-open duration" ? { ...row, duration_seconds: 125 } : row,
    );
    renderCooling(COOLING_PATH, () => Promise.resolve(loaded(coolingBody({}, { context: two, selected_points: [] }))));
    await settledCooling();
    expect(evidenceCells()[1]).toBe("2 accepted grid power records");
    expect(evidenceCells()[2]).toBe("Door open for 2 min 5 s");
    expect(main().querySelector("[data-cooling-empty]")?.textContent).toBe("No accepted recovery sequence in this window.");
    // No selected point: the graphic frame is drawn empty and the evidence table is absent.
    expect(main().querySelector('figure[data-cooling-graphic="empty"] svg')).not.toBeNull();
    expect(main().querySelectorAll("[data-cooling-mark]")).toHaveLength(0);
    expect(main().querySelector('[aria-labelledby="cold-cooling-recovery-heading"] table')).toBeNull();
    expect(Array.from(main().querySelectorAll("[data-cooling-context] td:last-child")).map((td) => td.textContent)).toEqual(Array(5).fill("Not established"));
    cleanup();
    const unknown = base.map((row) => ({ ...row, state: "Unknown", evidence_ids: [], duration_seconds: null }));
    renderCooling(COOLING_PATH, () => Promise.resolve(loaded(coolingBody({}, { context: unknown }))));
    await settledCooling();
    expect(evidenceCells()[1]).toBe("No accepted grid power record");
    expect(evidenceCells()[2]).toBe("No matched door open/close pair");
    cleanup();
    const short = base.map((row) => (row.label === "Door-open duration" ? { ...row, duration_seconds: 45 } : row));
    renderCooling(COOLING_PATH, () => Promise.resolve(loaded(coolingBody({}, { context: short }))));
    await settledCooling();
    expect(evidenceCells()[2]).toBe("Door open for 45 s");
  });
});

describe("cooling_nav_and_routes", () => {
  const subtabs = () => main().querySelector('nav[aria-label="Performance sections"]') as HTMLElement;

  it("Cooling is a live subtab between Temperature and Backup, keeping the window; the breadcrumb ends Performance › Cooling", async () => {
    const { coldAssessment } = renderCooling(COOLING_PATH, () => Promise.resolve(loaded(coolingBody())));
    await settledCooling();
    expect(Array.from(subtabs().querySelectorAll("li")).map((li) => li.textContent)).toEqual(["Temperature", "Cooling", "Backup"]);
    const cooling = subtabs().querySelector('a[data-performance-subtab="cooling"]') as HTMLElement;
    expect(cooling.getAttribute("href")).toBe(`/sites/${SITE_CODE}/performance/cooling?${Q}`);
    expect(cooling.getAttribute("aria-current")).toBe("page");
    expect(subtabs().querySelector("[data-tab-unavailable]")).toBeNull();
    expect(crumbs().slice(-2)).toEqual(["Performance", "Cooling"]);
    expect(main().getAttribute("data-cold-view")).toBe("cooling");
    expect(main().textContent).toContain("Performance · recovery under comparable conditions");
    expect(coldAssessment.getTemperature).not.toHaveBeenCalled();
    expect(coldAssessment.getBackupChain).not.toHaveBeenCalled();
  });

  it("the Temperature page links to the live Cooling page and its breadcrumb stays at Performance", async () => {
    const { client } = renderCooling(`/sites/${SITE_CODE}/performance/temperature?${Q}`, () => Promise.resolve(loaded(coolingBody())));
    await settledScreen();
    await waitFor(() => expect(document.querySelector('nav[aria-label="Performance sections"]')).not.toBeNull());
    const cooling = subtabs().querySelector('a[data-performance-subtab="cooling"]') as HTMLElement;
    expect(cooling.getAttribute("href")).toBe(`/sites/${SITE_CODE}/performance/cooling?${Q}`);
    expect(cooling.getAttribute("aria-current")).toBeNull();
    expect(crumbs()[crumbs().length - 1]).toBe("Performance");
    expect(client.getCooling).not.toHaveBeenCalled();
  });

  it("coldUiHref maps the cooling API link with its exact query (and health, which C3 mapped)", () => {
    const routes = coldSiteRoutes(SITE_CODE);
    expect(routes.cooling).toBe(`/sites/${SITE_CODE}/performance/cooling`);
    const query = `${Q}&known_at=2026-10-22T08%3A00%3A00Z`;
    expect(coldUiHref(`/api/sites/${SITE_CODE}/cold/cooling?${query}`, routes)).toBe(`/sites/${SITE_CODE}/performance/cooling?${query}`);
    expect(coldUiHref(`/api/sites/${SITE_CODE}/cold/health?${Q}`, routes)).toBe(`/sites/${SITE_CODE}/health?${Q}`);
  });
});
