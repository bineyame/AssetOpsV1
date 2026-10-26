/**
 * W5-01a C3 (`.agent/W5-01-build-spec.md` C3 card, literal ledger and readiness pass 3): the cold depth client's
 * exact Health validation and the cold Health body (`ColdHealthDepth`) with a stubbed depth client
 * (`health_dto_rendering`, `condition_matrix`, `health_states_and_loading`).
 */
import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import type { SiteDetailClient, SiteDirectoryClient } from "../siteDirectoryClient";
import type { SiteDetailReadModel } from "../siteReadModel";
import { EMPTY_ANALYTICS_CLIENT } from "./analyticsFixtures";
import { coldSiteRoutes } from "../../shell/coldSiteRoutes";
import { settledScreen } from "../../test/settled";
import { type ColdRead, NO_WINDOW, type ColdWindowQuery } from "../coldAssessmentClient";
import { COLD_DEPTH_STATE_NOTICE, COLD_DEPTH_UNKNOWN_WITH_ROWS } from "../ColdCooling";
import {
  type ColdDepthClient,
  type ColdHealthRead,
  createColdDepthClient,
  HEALTH_ROW_LITERALS,
  isColdHealthRead,
} from "../ColdDepthClient";
import { ColdHealthDepth, HEALTH_CONDITION_NOTICE, HEALTH_EMPTY, HEALTH_LOADING } from "../ColdHealthDepth";
import { coldUiHref } from "../coldSiteViews";

const SITE_CODE = "COLD-001";
const Q = "from=2026-10-06T19%3A00%3A00Z&to=2026-10-06T20%3A05%3A00Z";
const WINDOW: ColdWindowQuery = { from: "2026-10-06T19:00:00Z", to: "2026-10-06T20:05:00Z", known_at: null };
const GEN = "0a1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d";
const CMP = "1b2c3d4e-5f60-4b7c-9d8e-0f1a2b3c4d5e";
const PROBE = "2c3d4e5f-6071-4c8d-ae9f-1a2b3c4d5e6f";
const AMBIENT = "3d4e5f60-7182-4d9e-bfa0-2b3c4d5e6f70";
const START_REQ = "4e5f6071-8293-4eaf-80b1-3c4d5e6f7081";
const START_RES = "5f607182-93a4-4fb0-91c2-4d5e6f708192";
const PROBE_EV = "60718293-a4b5-40c1-a2d3-5e6f708192a3";

type Row = ColdHealthRead["health"]["rows"][number];

const generator = (over: Partial<Row> = {}): Row => ({
  kind: "BACKUP_GENERATOR",
  label: "Backup generator",
  asset_id: GEN,
  assets: [{ asset_id: GEN, asset_code: "gen-1", display_name: "Backup generator GEN-CR-01" }],
  observation: "Automatic start failed",
  condition_state: "NEEDS_INVESTIGATION",
  limitation: "Failed automatic start observed; part not diagnosed",
  next_evidence: "Witness an automatic-start test",
  evidence_ids: [START_REQ, START_RES].sort(),
  link: `/api/sites/${SITE_CODE}/cold/backup-chain?${Q}`,
  ...over,
});
const plant = (over: Partial<Row> = {}): Row => ({
  kind: "COOLING_PLANT",
  label: "Cooling plant",
  asset_id: CMP,
  assets: [{ asset_id: CMP, asset_code: "cmp-1", display_name: null }],
  observation: "Condition unknown",
  condition_state: "UNKNOWN",
  limitation: "Comparable recovery and condition evidence absent",
  next_evidence: "Record matched loading, door and ambient context",
  evidence_ids: [],
  link: `/api/sites/${SITE_CODE}/cold/cooling?${Q}`,
  ...over,
});
const sensing = (over: Partial<Row> = {}): Row => ({
  kind: "TEMPERATURE_SENSING",
  label: "Temperature sensing",
  asset_id: PROBE,
  assets: [
    { asset_id: AMBIENT, asset_code: "ambient-1", display_name: "Ambient probe" },
    { asset_id: PROBE, asset_code: "probe-1", display_name: "Chamber probe" },
  ],
  observation: "Single-point observation",
  condition_state: "LIMITED",
  limitation: "One accepted probe does not establish room-wide coverage",
  next_evidence: "Add calibrated spatial coverage",
  evidence_ids: [PROBE_EV],
  link: `/api/sites/${SITE_CODE}/cold/evidence?${Q}`,
  ...over,
});

const NOT_CONFIGURED: Record<Row["kind"], Partial<Row>> = {
  BACKUP_GENERATOR: { asset_id: null, assets: [], observation: "Not configured", condition_state: "NOT_CONFIGURED", limitation: "No backup generator is declared in the selected Foundation", evidence_ids: [], link: null },
  COOLING_PLANT: { asset_id: null, assets: [], observation: "Not configured", condition_state: "NOT_CONFIGURED", limitation: "No cooling plant is declared in the selected Foundation", evidence_ids: [], link: null },
  TEMPERATURE_SENSING: { asset_id: null, assets: [], observation: "Not configured", condition_state: "NOT_CONFIGURED", limitation: "No temperature probe is declared in the selected Foundation", evidence_ids: [], link: null },
};

/** A C1 backup-failed shaped `/cold/health` answer (exact keys of the C1 "Health read" tables). */
function healthBody(rows: Row[] = [generator(), plant(), sensing()], state = "CURRENT"): ColdHealthRead {
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
      state: state as ColdHealthRead["selection"]["state"],
      assessment_revision_ids: ["4d5e6f70-8192-4d4e-bf50-6b7c8d9eafb0"],
      accepted_evidence_ids: [START_REQ, START_RES, PROBE_EV].sort(),
      source_provenance: { classification: "SIMULATED_REPLAY", source_ids: [], evidence_ids: [], basis_sha256: null },
    },
    health: { foundation_revision_id: "8f9a0b1c-2d3e-4f5a-8b6c-7d8e9f0a1b2c", rows },
    links: {
      temperature: `/api/sites/${SITE_CODE}/cold/temperature?${Q}`,
      backup: `/api/sites/${SITE_CODE}/cold/backup-chain?${Q}`,
      evidence: `/api/sites/${SITE_CODE}/cold/evidence?${Q}`,
      health: `/api/sites/${SITE_CODE}/cold/health?${Q}`,
    },
  };
}

function stub(answer: () => ColdRead<ColdHealthRead> | Promise<ColdRead<ColdHealthRead>>) {
  const getHealth = vi.fn(async () => answer());
  const client: ColdDepthClient = { getCooling: vi.fn(), getHealth };
  return { client, getHealth };
}

async function renderHealth(answer: () => ColdRead<ColdHealthRead> | Promise<ColdRead<ColdHealthRead>>, window: ColdWindowQuery = WINDOW) {
  const { client, getHealth } = stub(answer);
  const view = render(
    <MemoryRouter>
      <main aria-labelledby="h">
        <h1 id="h">Health</h1>
        <ColdHealthDepth siteCode={SITE_CODE} window={window} client={client} routes={coldSiteRoutes(SITE_CODE)} />
      </main>
    </MemoryRouter>,
  );
  await settledScreen();
  await waitFor(() => expect(view.container.textContent).not.toContain(HEALTH_LOADING));
  return { container: view.container, getHealth };
}

const loaded = (rows?: Row[], state?: string) => () => ({ status: "loaded" as const, value: healthBody(rows, state) });
const card = (root: HTMLElement, kind: string) => root.querySelector(`[data-health-card="${kind}"]`) as HTMLElement;
const row = (root: HTMLElement, kind: string) => root.querySelector(`[data-health-row="${kind}"]`) as HTMLElement;
const cells = (tr: HTMLElement) => Array.from(tr.querySelectorAll("th, td")).map((cell) => cell.textContent);

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("health_dto_rendering", () => {
  it("accepts the exact C1 Health key sets in any order, and every literal tuple of the C1 table", () => {
    const body = healthBody();
    expect(isColdHealthRead(body)).toBe(true);
    const reordered = Object.fromEntries(Object.entries(body).reverse()) as unknown as ColdHealthRead;
    reordered.health = { rows: body.health.rows.map((r) => Object.fromEntries(Object.entries(r).reverse()) as unknown as Row), foundation_revision_id: null };
    expect(isColdHealthRead(reordered)).toBe(true);
    const makers = { BACKUP_GENERATOR: generator, COOLING_PLANT: plant, TEMPERATURE_SENSING: sensing };
    for (const [kind, literals] of Object.entries(HEALTH_ROW_LITERALS) as [Row["kind"], (typeof HEALTH_ROW_LITERALS)[Row["kind"]]][]) {
      for (const tuple of literals.tuples) {
        const rows = [generator(), plant(), sensing()].map((r) => (r.kind === kind ? makers[kind](tuple) : r));
        expect(isColdHealthRead(healthBody(rows)), `${kind} ${tuple.observation}`).toBe(true);
      }
    }
  });

  it("refuses a missing, extra, ill-typed, reordered or off-table value as malformed", () => {
    const body = healthBody();
    const g = generator();
    const bad: unknown[] = [
      { ...body, health: { rows: body.health.rows } },
      { ...body, health: { ...body.health, extra: 1 } },
      { ...body, health: { ...body.health, foundation_revision_id: 3 } },
      healthBody([plant(), generator(), sensing()]),
      healthBody([generator(), plant()]),
      healthBody([generator({ observation: "Generator healthy" }), plant(), sensing()]),
      healthBody([generator({ condition_state: "LIMITED" }), plant(), sensing()]),
      healthBody([generator({ limitation: "Failed start observed" }), plant(), sensing()]),
      healthBody([generator({ next_evidence: "Witnessed automatic-start test" }), plant(), sensing()]),
      healthBody([generator(), plant({ observation: "Single-point observation", condition_state: "LIMITED", limitation: "One accepted probe does not establish room-wide coverage" }), sensing()]),
      healthBody([{ ...g, extra: 1 } as Row, plant(), sensing()]),
      healthBody([{ ...g, assets: [{ asset_id: GEN, asset_code: "gen-1" }] } as unknown as Row, plant(), sensing()]),
      healthBody([generator({ evidence_ids: [7] as unknown as string[] }), plant(), sensing()]),
      healthBody([generator({ link: 4 as unknown as string }), plant(), sensing()]),
    ];
    for (const value of bad) expect(isColdHealthRead(value)).toBe(false);
  });

  it("returns a malformed 200 as unavailable, never as an empty read", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify(healthBody([generator(), plant()])), { status: 200 })));
    const result = await createColdDepthClient().getHealth(SITE_CODE, WINDOW);
    expect(result).toEqual({ status: "unavailable", message: "The cold depth read answered in an unexpected shape." });
  });

  it("renders every server string verbatim: card label and note, observation and next evidence", async () => {
    const { container } = await renderHealth(loaded());
    const kinds = ["BACKUP_GENERATOR", "COOLING_PLANT", "TEMPERATURE_SENSING"];
    expect(Array.from(container.querySelectorAll("[data-health-card]")).map((c) => c.getAttribute("data-health-card"))).toEqual(kinds);
    expect(Array.from(container.querySelectorAll("[data-health-row]")).map((r) => r.getAttribute("data-health-row"))).toEqual(kinds);
    for (const r of healthBody().health.rows) {
      const c = card(container, r.kind);
      expect(c.querySelector(".v69-metric__label")?.textContent).toBe(r.label);
      expect(c.querySelector(".v69-metric__note")?.textContent).toBe(r.limitation);
      const [, observation, next] = cells(row(container, r.kind));
      expect(observation).toBe(r.observation);
      expect(next).toBe(r.next_evidence);
    }
    const headers = Array.from(container.querySelectorAll("thead th")).map((h) => h.textContent);
    expect(headers).toEqual(["Asset", "Supported assessment", "Next evidence"]);
  });

  it("Asset cell: matching asset name and ID (mobile: selected code + Full ID); missing match: the ID; else every asset name; else the row label", async () => {
    const { container } = await renderHealth(
      loaded([
        generator(),
        plant({ asset_id: null, assets: [{ asset_id: CMP, asset_code: "cmp-1", display_name: null }, { asset_id: AMBIENT, asset_code: "cmp-2", display_name: "Second compressor" }] }),
        sensing({ asset_id: null, assets: [] }),
      ]),
    );
    const gen = row(container, "BACKUP_GENERATOR").querySelector("th") as HTMLElement;
    expect(gen.querySelector(".cold-health-asset__desktop")?.textContent).toBe(`Backup generator GEN-CR-01 ${GEN}`);
    const mobile = gen.querySelector(".cold-health-asset__mobile") as HTMLElement;
    expect(mobile.querySelector("[data-health-asset-code]")?.textContent).toBe("gen-1");
    // Both full-ID copies are the complete source-reference UUID.
    const ids = Array.from(gen.querySelectorAll('code[data-vocabulary-exempt="source-reference"][data-health-asset-id]'));
    expect(ids.map((c) => c.textContent)).toEqual([GEN, GEN]);
    const details = mobile.querySelector("details") as HTMLDetailsElement;
    expect(details.open).toBe(false);
    expect(details.querySelector("summary")?.textContent).toBe("Full ID");
    fireEvent.click(details.querySelector("summary") as HTMLElement);
    expect(details.open).toBe(true);
    expect(details.querySelector("code")?.textContent).toBe(GEN);
    expect(gen.closest(".panel")?.classList.contains("cold-health-condition")).toBe(true);
    expect(cells(row(container, "COOLING_PLANT"))[0]).toBe("cmp-1, Second compressor");
    expect(cells(row(container, "TEMPERATURE_SENSING"))[0]).toBe("Temperature sensing");
    cleanup();
    const second = await renderHealth(loaded([generator(), plant(), sensing()]));
    expect(row(second.container, "COOLING_PLANT").querySelector(".cold-health-asset__desktop")?.textContent).toBe(`cmp-1 ${CMP}`);
    expect(row(second.container, "COOLING_PLANT").querySelector("[data-health-asset-code]")?.textContent).toBe("cmp-1");
    expect(row(second.container, "TEMPERATURE_SENSING").querySelector(".cold-health-asset__desktop")?.textContent).toBe(`Chamber probe ${PROBE}`);
    expect(row(second.container, "TEMPERATURE_SENSING").querySelector("[data-health-asset-code]")?.textContent).toBe("probe-1");
    cleanup();
    // Missing match: the full ID is the primary text (no inferred code, no disclosure).
    const third = await renderHealth(loaded([generator({ asset_id: AMBIENT }), plant(), sensing()]));
    const missing = row(third.container, "BACKUP_GENERATOR").querySelector("th") as HTMLElement;
    expect(missing.textContent).toBe(AMBIENT);
    expect(missing.querySelector("[data-health-asset-code]")).toBeNull();
    expect(missing.querySelector("details")).toBeNull();
  });

  it("the 390 rule fits the table: no 840/240 px sticky rule remains in primitives.css", async () => {
    const fs = (await import(/* @vite-ignore */ `node:${"fs"}`)) as { readFileSync: (p: string, e: string) => string };
    const cwd = (globalThis as unknown as { process: { cwd: () => string } }).process.cwd();
    const css = fs.readFileSync(`${cwd}/src/ui/primitives.css`, "utf8");
    const block = css.slice(css.indexOf(".cold-health-asset__mobile { display: none; }"));
    expect(block.length).toBeGreaterThan(0);
    expect(css).not.toMatch(/\.cold-health-condition[^{]*\{[^}]*min-width:\s*840px/);
    expect(css).not.toMatch(/\.cold-health-condition[^{]*\{[^}]*min-width:\s*240px/);
    expect(css).toContain(".cold-health-condition .data-table { min-width: 0; width: 100%; table-layout: fixed; }");
  });

  it("each card has a plain label and a separate View detail → link through coldUiHref; a null link renders none", async () => {
    const routes = coldSiteRoutes(SITE_CODE);
    expect(coldUiHref(`/api/sites/${SITE_CODE}/cold/health?${Q}`, routes)).toBe(`/sites/${SITE_CODE}/health?${Q}`);
    const { container } = await renderHealth(loaded([generator(), plant(), sensing({ ...NOT_CONFIGURED.TEMPERATURE_SENSING })]));
    const detail = (kind: string) => card(container, kind).querySelector(".v69-metric__link a");
    const href = (kind: string) => detail(kind)?.getAttribute("href") ?? null;
    for (const kind of ["BACKUP_GENERATOR", "COOLING_PLANT", "TEMPERATURE_SENSING"]) {
      expect(card(container, kind).querySelector(".v69-metric__label a")).toBeNull();
    }
    expect(detail("BACKUP_GENERATOR")?.textContent).toBe("View detail →");
    expect(card(container, "TEMPERATURE_SENSING").querySelector(".v69-metric__link")).toBeNull();
    expect(card(container, "TEMPERATURE_SENSING").querySelector("a")).toBeNull();
    expect(href("BACKUP_GENERATOR")).toBe(`/sites/${SITE_CODE}/performance/backup?${Q}`);
    expect(href("COOLING_PLANT")).toBe(`/sites/${SITE_CODE}/performance/cooling?${Q}`);
    expect(href("TEMPERATURE_SENSING")).toBeNull();
    expect(card(container, "TEMPERATURE_SENSING").querySelector(".v69-metric__label")?.textContent).toBe("Temperature sensing");
  });
});

describe("condition_matrix", () => {
  const value = (root: HTMLElement, kind: string) => card(root, kind).querySelector(".v69-metric__value")?.textContent;

  it("backup-failed: Needs attention (amber), Unknown, Limited; then the panel, then the condition notice", async () => {
    const { container } = await renderHealth(loaded());
    expect(value(container, "BACKUP_GENERATOR")).toBe("Needs attention");
    expect(card(container, "BACKUP_GENERATOR").className).toContain("v69-metric--amber");
    expect(value(container, "COOLING_PLANT")).toBe("Unknown");
    expect(value(container, "TEMPERATURE_SENSING")).toBe("Limited");
    expect(card(container, "COOLING_PLANT").className).not.toMatch(/v69-metric--(green|amber|red)/);
    // Q-C3-6 H1: only the NEEDS_INVESTIGATION card is a mock assessment metric (3 px amber border, 17 px word);
    // the plain cards keep the 27 px value with no border or tone.
    for (const kind of ["BACKUP_GENERATOR", "COOLING_PLANT", "TEMPERATURE_SENSING"]) {
      expect(card(container, kind).getAttribute("style")).toBeNull();
      expect(card(container, kind).classList.contains("v69-metric--word")).toBe(kind === "BACKUP_GENERATOR");
    }
    expect(card(container, "BACKUP_GENERATOR").className).toContain("v69-metric--assessment v69-metric--amber");
    for (const kind of ["COOLING_PLANT", "TEMPERATURE_SENSING"]) {
      expect(card(container, kind).classList.contains("v69-metric--assessment")).toBe(false);
      expect(card(container, kind).className).not.toMatch(/v69-metric--(green|amber|red|muted)/);
    }
    const notice = container.querySelector("[data-health-condition-notice]") as HTMLElement;
    expect(notice.textContent).toBe(HEALTH_CONDITION_NOTICE);
    expect(HEALTH_CONDITION_NOTICE).toBe(
      "These records show what was observed at the selected assets. They do not establish physical equipment condition or diagnose a failed part.",
    );
    // Order: cards, Condition and evidence, the condition notice.
    const cards = container.querySelector("ul.v69-cards") as HTMLElement;
    const panel = container.querySelector("#cold-health-condition-heading")?.closest("section, .panel, div") as HTMLElement;
    expect(panel.textContent).toContain("Condition and evidence");
    expect(cards.compareDocumentPosition(panel) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(panel.compareDocumentPosition(notice) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(container.querySelector("[data-health-empty]")).toBeNull();
  });

  it("every state maps to its card word; no other positive condition value appears", async () => {
    const cases: [Row[], string[]][] = [
      [[generator(HEALTH_ROW_LITERALS.BACKUP_GENERATOR.tuples[4]), plant(), sensing(HEALTH_ROW_LITERALS.TEMPERATURE_SENSING.tuples[2])], ["Unknown", "Unknown", "Unknown"]],
      [[generator(HEALTH_ROW_LITERALS.BACKUP_GENERATOR.tuples[1]), plant(), sensing(HEALTH_ROW_LITERALS.TEMPERATURE_SENSING.tuples[3])], ["Unknown", "Unknown", "Unknown"]],
      [[generator(HEALTH_ROW_LITERALS.BACKUP_GENERATOR.tuples[3]), plant(), sensing()], ["Unknown", "Unknown", "Limited"]],
      [[generator(NOT_CONFIGURED.BACKUP_GENERATOR), plant(NOT_CONFIGURED.COOLING_PLANT), sensing(NOT_CONFIGURED.TEMPERATURE_SENSING)], ["Not configured", "Not configured", "Not configured"]],
    ];
    for (const [rows, words] of cases) {
      const { container } = await renderHealth(loaded(rows));
      expect(["BACKUP_GENERATOR", "COOLING_PLANT", "TEMPERATURE_SENSING"].map((k) => value(container, k))).toEqual(words);
      // Assessment styling follows the state: no row here is NEEDS_INVESTIGATION.
      expect(container.querySelector(".v69-metric--assessment")).toBeNull();
      expect(container.textContent).not.toMatch(/\b(Healthy|Good|Normal|OK|Operating normally)\b/);
      expect(container.querySelector(".v69-metric--green")).toBeNull();
      cleanup();
    }
  });

  it("one versus two selected probes: Limited single-point, Unknown multiple", async () => {
    const one = await renderHealth(loaded());
    expect(value(one.container, "TEMPERATURE_SENSING")).toBe("Limited");
    expect(cells(row(one.container, "TEMPERATURE_SENSING"))[1]).toBe("Single-point observation");
    cleanup();
    const two = await renderHealth(loaded([generator(), plant(), sensing({ ...HEALTH_ROW_LITERALS.TEMPERATURE_SENSING.tuples[3], evidence_ids: [PROBE_EV, START_REQ].sort() })]));
    expect(value(two.container, "TEMPERATURE_SENSING")).toBe("Unknown");
    expect(cells(row(two.container, "TEMPERATURE_SENSING"))[1]).toBe("Multiple probe observations");
    expect(card(two.container, "TEMPERATURE_SENSING").querySelector(".v69-metric__note")?.textContent).toBe("Multiple selected probes do not establish room-wide condition");
  });

  it("the empty sentence shows only when no row cites evidence and none is Not configured", async () => {
    const empty = [generator(HEALTH_ROW_LITERALS.BACKUP_GENERATOR.tuples[4]), plant(), sensing(HEALTH_ROW_LITERALS.TEMPERATURE_SENSING.tuples[2])].map((r) => ({ ...r, evidence_ids: [] }));
    const a = await renderHealth(loaded(empty, "UNKNOWN"));
    const sentence = a.container.querySelector("[data-health-empty]") as HTMLElement;
    expect(sentence.textContent).toBe(HEALTH_EMPTY);
    expect(sentence.compareDocumentPosition(a.container.querySelector("table") as HTMLElement) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    // post-W6 R336: no row cites evidence, so the UNKNOWN notice keeps the plain ledger sentence.
    expect(a.container.querySelector("[data-health-state-notice]")?.textContent).toBe("No selected cold assessment covers this window yet.");
    cleanup();
    const b = await renderHealth(loaded([empty[0], empty[1], sensing(NOT_CONFIGURED.TEMPERATURE_SENSING)], "UNKNOWN"));
    expect(b.container.querySelector("[data-health-empty]")).toBeNull();
    // A Not configured row cites no accepted record either: still the plain sentence.
    expect(b.container.querySelector("[data-health-state-notice]")?.textContent).toBe("No selected cold assessment covers this window yet.");
  });
});

describe("health_states_and_loading", () => {
  it("styling follows the state: a NEEDS_INVESTIGATION row is an assessment card whichever card it is", async () => {
    const { container } = await renderHealth(loaded());
    const assessed = Array.from(container.querySelectorAll(".v69-metric--assessment")).map((c) => c.getAttribute("data-health-card"));
    expect(assessed).toEqual(["BACKUP_GENERATOR"]);
  });


  it("shows the loading sentence while the read is pending", async () => {
    const { client } = stub(() => new Promise(() => undefined));
    const view = render(
      <MemoryRouter>
        <ColdHealthDepth siteCode={SITE_CODE} window={WINDOW} client={client} routes={coldSiteRoutes(SITE_CODE)} />
      </MemoryRouter>,
    );
    const p = view.container.querySelector("p.prose") as HTMLElement;
    expect(p.textContent).toBe(HEALTH_LOADING);
    expect(HEALTH_LOADING).toBe("Loading the site's equipment condition read.");
  });

  it("CURRENT renders no state notice; every other state renders its sentence directly above the cards", async () => {
    const current = await renderHealth(loaded());
    expect(current.container.querySelector("[data-health-state-notice]")).toBeNull();
    cleanup();
    for (const state of ["PENDING_RECOMPUTE", "HISTORICAL", "STALE_SOURCE", "UNKNOWN"] as const) {
      const { container } = await renderHealth(loaded(undefined, state));
      const notice = container.querySelector("[data-health-state-notice]") as HTMLElement;
      // post-W6 R336: the default rows cite evidence, so UNKNOWN says the rows are accepted records only.
      expect(notice.textContent).toBe(state === "UNKNOWN" ? COLD_DEPTH_UNKNOWN_WITH_ROWS : COLD_DEPTH_STATE_NOTICE[state]);
      const bar = container.querySelector("[data-cold-date-bar]") as HTMLElement;
      expect(bar.nextElementSibling).toBe(notice);
      expect(notice.nextElementSibling?.matches("ul.v69-cards")).toBe(true);
      // The selected values stay; no current positive condition label is added.
      expect(card(container, "BACKUP_GENERATOR").querySelector(".v69-metric__value")?.textContent).toBe("Needs attention");
      cleanup();
    }
  });

  it("a refusal shows its code and message under the heading, and Retry re-reads the same window", async () => {
    let calls = 0;
    const { container, getHealth } = await renderHealth(() => {
      calls += 1;
      return { status: "refused", httpStatus: 422, code: "COLD_WINDOW_INVALID", message: "from must be before to." };
    });
    expect(container.querySelector(".page-refusal__title")?.textContent).toBe("Cold depth unavailable");
    expect(container.querySelector("[data-cold-depth-error]")?.textContent).toBe("COLD_WINDOW_INVALID from must be before to.");
    expect(container.querySelector("[data-cold-date-bar]")).toBeNull();
    expect(container.querySelector("[data-health-card]")).toBeNull();
    fireEvent.click(container.querySelector("[data-cold-retry]") as HTMLElement);
    await waitFor(() => expect(calls).toBe(2));
    expect(getHealth.mock.calls[1]).toEqual([SITE_CODE, WINDOW]);
  });

  it("unreachable and malformed reads use their exact sentences; a 403 keeps the requested window bar", async () => {
    const unreachable = await renderHealth(() => ({ status: "unavailable", message: null }));
    expect(unreachable.container.querySelector("[data-cold-depth-error]")?.textContent).toBe("The cold depth read could not be reached.");
    cleanup();
    const malformed = await renderHealth(() => ({ status: "unavailable", message: "The cold depth read answered in an unexpected shape." }));
    expect(malformed.container.querySelector("[data-cold-depth-error]")?.textContent).toBe("The cold depth read answered in an unexpected shape.");
    cleanup();
    const denied = await renderHealth(() => ({ status: "refused", httpStatus: 403, code: "COLD_SOURCE_DISCLOSURE_FORBIDDEN", message: null }));
    expect(denied.container.querySelector("[data-cold-depth-error]")?.textContent).toBe("COLD_SOURCE_DISCLOSURE_FORBIDDEN");
    expect(denied.container.querySelector("[data-cold-date-bar-requested]")).not.toBeNull();
  });

  it("no window still reads (the server resolves the default)", async () => {
    const { getHealth } = await renderHealth(loaded(), NO_WINDOW);
    expect(getHealth).toHaveBeenCalledWith(SITE_CODE, NO_WINDOW);
  });
});

/* ---------- the composed page, through the real App route (Q-C3-1, Q-C3-2) ---------- */

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

describe("condition_matrix: the composed cold Health page", () => {
  // W5-F1 F1-1 (R22): v69 cold-health ends at Condition and evidence; the S7 Data sources panel is not mounted.
  async function renderPage(answer: () => ColdRead<ColdHealthRead>) {
    const requests: string[] = [];
    vi.stubGlobal("fetch", async (url: string) => {
      requests.push(url);
      return new Response(JSON.stringify({ detail: { code: "SOURCE_HEALTH_UNAVAILABLE", message: "down" } }), { status: 503 });
    });
    const { client, getHealth } = stub(answer);
    const detail: SiteDetailClient = { getSite: () => Promise.resolve({ status: "loaded", site: SITE }) };
    const directory: SiteDirectoryClient = { listSites: () => Promise.resolve({ status: "loaded", sites: [SITE] }) };
    render(
      <MemoryRouter initialEntries={[`/sites/${SITE_CODE}/health?${Q}`]}>
        <App flags={featureFlagsWith(false)} siteDirectory={directory} siteDetail={detail} siteAnalytics={EMPTY_ANALYTICS_CLIENT} coldDepth={client} />
      </MemoryRouter>,
    );
    await settledScreen();
    await waitFor(() => {
      if ((document.body.textContent ?? "").includes(HEALTH_LOADING)) throw new Error("the Health read has not settled");
    });
    const main = document.querySelector("main") as HTMLElement;
    const titles = Array.from(main.querySelectorAll(".panel__heading")).map((h) => h.textContent);
    return { main, requests, getHealth, titles };
  }

  function expectNoSourcePanel(main: HTMLElement, requests: string[]) {
    expect(main.querySelector("#site-health-sources-heading")).toBeNull();
    expect(main.textContent).not.toContain("Data sources · data quality, not equipment condition");
    expect(requests.some((url) => url.endsWith("/source-health"))).toBe(false);
    expect(requests.some((url) => url.endsWith("/battery"))).toBe(false);
    expect(main.textContent).not.toContain("Physical asset condition");
    expect(main.querySelector("#site-health-condition-heading")).toBeNull();
    expect(main.querySelector(".v69-notice--blue")).toBeNull();
    expect(main.querySelector("[data-health-site]")).toBeNull();
  }

  for (const state of ["CURRENT", "UNKNOWN"]) {
    it(`${state}: Site-name h1, then cards, Condition and evidence and the condition notice; Condition and evidence is the only panel`, async () => {
      const { main, requests, getHealth, titles } = await renderPage(loaded(undefined, state));
      expect(getHealth).toHaveBeenCalledWith(SITE_CODE, WINDOW);
      expect(main.querySelector("h1")?.textContent).toContain("Kobo vaccine cold store");
      expect(main.querySelector('nav[aria-label] a[aria-current="page"]')?.textContent).toBe("Health");
      expect(titles).toEqual(["Condition and evidence"]);
      const order = [
        main.querySelector("ul.v69-cards"),
        main.querySelector("#cold-health-condition-heading"),
        main.querySelector("[data-health-condition-notice]"),
      ] as HTMLElement[];
      order.forEach((node) => expect(node).not.toBeNull());
      for (let i = 1; i < order.length; i += 1) {
        expect(order[i - 1].compareDocumentPosition(order[i]) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
      }
      // Nothing follows the condition notice inside main: the page ends at Condition and evidence.
      const notice = order[2];
      const tail = Array.from(main.querySelectorAll("*")).filter(
        (el) => notice.compareDocumentPosition(el) & Node.DOCUMENT_POSITION_FOLLOWING && !notice.contains(el),
      );
      expect(tail.some((el) => el.classList.contains("panel"))).toBe(false);
      expectNoSourcePanel(main, requests);
    });
  }

  it("refused: the honest refusal alone; no Data sources panel and no source read", async () => {
    const { main, requests, titles } = await renderPage(() => ({
      status: "refused",
      httpStatus: 422,
      code: "COLD_WINDOW_INVALID",
      message: "from must be before to.",
    }));
    expect(main.querySelector("[data-cold-depth-error]")?.textContent).toBe("COLD_WINDOW_INVALID from must be before to.");
    expect(main.querySelector("[data-health-card]")).toBeNull();
    expect(titles).not.toContain("Data sources · data quality, not equipment condition");
    expectNoSourcePanel(main, requests);
  });
});
