/**
 * W5-01b C5 (`.agent/W5-01-build-spec.md` C5 card, readiness pass 3, closure 2 and P-C5-1..22): the cold scenario
 * client's exact validation and the cold Financials > Scenarios page (`states_loading_and_refusal`,
 * `row_disclosure_and_client`, `authored_pending_historical_basis`, the 51-row pager and the full-page W1 scan).
 */
import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import type { SiteDetailClient, SiteDirectoryClient } from "../siteDirectoryClient";
import type { SiteDetailReadModel } from "../siteReadModel";
import { EMPTY_ANALYTICS_CLIENT } from "./analyticsFixtures";
import { settledScreen } from "../../test/settled";
import { describeViolations, scanProductVocabulary } from "../../test/productVocabulary";
import type { ColdRead, ColdWindowQuery } from "../coldAssessmentClient";
import {
  type ColdScenarioItem,
  type ColdScenariosClient,
  type ColdScenariosRead,
  HttpColdScenariosClient,
  isColdScenariosRead,
} from "../coldScenariosClient";
import {
  ColdScenarios,
  SCENARIOS_CLOSING_NOTICE,
  SCENARIOS_EMPTY_BODY,
  SCENARIOS_LOADING,
  SCENARIOS_MALFORMED,
  SCENARIOS_STATE_NOTICE,
  SCENARIOS_UNREACHABLE,
} from "../ColdScenarios";
import { siteFinancialScenariosHref } from "../../shell/operatorSiteRoutes";

const SITE_CODE = "COLD-001";
const FROM = "2026-10-06T19:00:00.000000Z";
const TO = "2026-10-06T20:05:00.000000Z";
const KNOWN = "2026-10-22T08:00:00.123456Z";
const AT = "2026-10-22T09:30:00.000000Z";
const WINDOW: ColdWindowQuery = { from: FROM, to: TO, known_at: null };
const SITE_UUID = "7d1e2f30-4a5b-4c6d-8e7f-901a2b3c4d5e";
const REV_A = "4d5e6f70-8192-4d4e-bf50-6b7c8d9eafb0";
const EV_1 = "4e5f6071-8293-4eaf-80b1-3c4d5e6f7081";
const EV_2 = "5f607182-93a4-4fb0-91c2-4d5e6f708192";
const FOUNDATION = "8f9a0b1c-2d3e-4f5a-8b6c-7d8e9f0a1b2c";
const SCENARIO = "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d";
const REVISION = "b2c3d4e5-f6a7-4b8c-9d0e-1f2a3b4c5d6e";

const provenance = (classification = "REGISTERED_SIMULATION") => ({
  classification,
  state: classification,
  source_ids: [],
  evidence_ids: [EV_1, EV_2],
  basis_sha256: null,
  reasons: [],
});

const item = (over: Partial<ColdScenarioItem> = {}, n = 1): ColdScenarioItem => ({
  id: SCENARIO,
  code: `CSCN-${String(n).padStart(6, "0")}`,
  revision_id: REVISION,
  revision_no: 1,
  name: "Vaccine stock at risk",
  kind: "STOCK_VALUE_CONTEXT",
  assumptions: { stock_quantity: "1200", stock_unit: "dose", unit_value: "2.75", currency: "USD" },
  authored_basis: {
    from: FROM,
    to: TO,
    cutoff: KNOWN,
    assessment_revision_ids: [REV_A],
    accepted_evidence_ids: [EV_1, EV_2],
    foundation_revision_id: FOUNDATION,
    source_provenance: provenance(),
  },
  recorded_at: "2026-10-22T09:12:00.000000Z",
  scenario_state: "DEFINED",
  ...over,
});

function body(
  items: ColdScenarioItem[] = [item()],
  state: ColdScenariosRead["selection"]["state"] = "CURRENT",
  next: string | null = null,
  totalPages = items.length === 0 ? 0 : 1,
): ColdScenariosRead {
  return {
    schema_version: "cold-scenarios-1",
    site_id: SITE_UUID,
    window: { from: FROM, to: TO, known_at: KNOWN, committed_watermark: KNOWN },
    scenario_at: AT,
    selection: { state, assessment_revision_ids: [REV_A], accepted_evidence_ids: [EV_1, EV_2], source_provenance: provenance() },
    items,
    next_cursor: next,
    total_pages: totalPages,
  };
}

const loaded = (value: ColdScenariosRead): ColdRead<ColdScenariosRead> => ({ status: "loaded", value });

function stub(answer: (cursor: string | null) => ColdRead<ColdScenariosRead> | Promise<ColdRead<ColdScenariosRead>>) {
  const list = vi.fn(async (_site: string, _query: unknown, cursor: string | null) => answer(cursor));
  const client: ColdScenariosClient = { list };
  return { client, list };
}

async function renderBody(client: ColdScenariosClient, window: ColdWindowQuery = WINDOW, scenarioAt: string | null = null) {
  const view = render(
    <MemoryRouter>
      <main aria-labelledby="h">
        <h1 id="h">Site</h1>
        <ColdScenarios siteCode={SITE_CODE} window={window} scenarioAt={scenarioAt} client={client} />
      </main>
    </MemoryRouter>,
  );
  await waitFor(() => expect(view.container.textContent).not.toContain(SCENARIOS_LOADING));
  return view.container;
}

// The stylesheet as text (estate/mini pattern); Node's fs is untyped here, paths relative to `frontend/`.
const NODE_FS = (await import(/* @vite-ignore */ `node:${"fs"}`)) as { readFileSync: (p: string, e: string) => string };
const FRONTEND_CWD = (globalThis as unknown as { process: { cwd: () => string } }).process.cwd();
const SCENARIOS_CSS = NODE_FS.readFileSync(`${FRONTEND_CWD}/src/sites/coldScenarios.css`, "utf8");

const clone = <T,>(value: T): T => JSON.parse(JSON.stringify(value)) as T;

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

/* ---------- client validation, one case per type ---------- */

describe("coldScenariosClient: exact cold-scenarios-1 validation", () => {
  it("accepts the documented shape, an empty list and a null-cutoff unavailable selection", () => {
    expect(isColdScenariosRead(body())).toBe(true);
    expect(isColdScenariosRead(body([]))).toBe(true);
    const unknown = body([], "UNKNOWN");
    unknown.window.known_at = null;
    expect(isColdScenariosRead(unknown)).toBe(true);
    const withDetail = body();
    (withDetail.selection.source_provenance as unknown as Record<string, unknown>).detail = { state: "UNKNOWN" };
    expect(isColdScenariosRead(withDetail)).toBe(true);
  });

  const top: [string, (b: Record<string, unknown>) => void][] = [
    ["an extra top-level key", (b) => (b.total = 1)],
    ["a missing top-level key", (b) => delete b.next_cursor],
    ["another schema version", (b) => (b.schema_version = "cold-scenarios-2")],
    ["an uppercase Site UUID", (b) => (b.site_id = SITE_UUID.toUpperCase())],
    ["a non-UTC scenario_at", (b) => (b.scenario_at = "2026-10-22T12:30:00+03:00")],
    ["a numeric cursor", (b) => (b.next_cursor = 2)],
    ["items not an array", (b) => (b.items = {})],
    ["a missing total_pages", (b) => delete b.total_pages],
    ["a null total_pages", (b) => (b.total_pages = null)],
    ["a string total_pages", (b) => (b.total_pages = "2")],
    ["a fractional total_pages", (b) => (b.total_pages = 1.5)],
    ["a negative total_pages", (b) => (b.total_pages = -1)],
  ];
  const window: [string, (w: Record<string, unknown>) => void][] = [
    ["an extra window key", (w) => (w.cutoff = KNOWN)],
    ["a non-UTC window start", (w) => (w.from = "2026-10-06 19:00")],
    ["a half window", (w) => (w.to = null)],
    ["a null known_at on a current selection", (w) => (w.known_at = null)],
    ["a non-instant watermark", (w) => (w.committed_watermark = "yesterday")],
  ];
  const selection: [string, (s: Record<string, unknown>) => void][] = [
    ["an unknown selection state", (s) => (s.state = "DEFINED")],
    ["an extra selection key", (s) => (s.extra = [])],
    ["an unsorted evidence set", (s) => (s.accepted_evidence_ids = [EV_2, EV_1])],
    ["a repeated evidence ID", (s) => (s.accepted_evidence_ids = [EV_1, EV_1])],
    ["an uppercase assessment revision", (s) => (s.assessment_revision_ids = [REV_A.toUpperCase()])],
    ["provenance without its classification", (s) => delete (s.source_provenance as Record<string, unknown>).classification],
    ["provenance with an extra key", (s) => ((s.source_provenance as Record<string, unknown>).run_mode = "x")],
    ["a non-string classification", (s) => ((s.source_provenance as Record<string, unknown>).classification = 3)],
  ];
  const row: [string, (i: Record<string, unknown>) => void][] = [
    ["an extra item key", (i) => (i.amount = "3300")],
    ["a malformed scenario code", (i) => (i.code = "SCN-000001")],
    ["a short scenario code", (i) => (i.code = "CSCN-12345")],
    ["an uppercase item ID", (i) => (i.id = SCENARIO.toUpperCase())],
    ["a non-UUID revision", (i) => (i.revision_id = "rev-1")],
    ["revision number zero", (i) => (i.revision_no = 0)],
    ["a fractional revision number", (i) => (i.revision_no = 1.5)],
    ["an empty name", (i) => (i.name = "")],
    ["a 161-character name", (i) => (i.name = "x".repeat(161))],
    ["another kind", (i) => (i.kind = "LOSS_ESTIMATE")],
    ["an extra assumption", (i) => ((i.assumptions as Record<string, unknown>).loss = "1")],
    ["a numeric assumption", (i) => ((i.assumptions as Record<string, unknown>).unit_value = 2.75)],
    ["a lowercase currency", (i) => ((i.assumptions as Record<string, unknown>).currency = "usd")],
    ["an extra basis key", (i) => ((i.authored_basis as Record<string, unknown>).run = "x")],
    ["a null cutoff on a current selection", (i) => ((i.authored_basis as Record<string, unknown>).cutoff = null)],
    ["an uppercase Foundation revision", (i) => ((i.authored_basis as Record<string, unknown>).foundation_revision_id = FOUNDATION.toUpperCase())],
    ["an unsorted basis revision set", (i) => ((i.authored_basis as Record<string, unknown>).accepted_evidence_ids = [EV_2, EV_1])],
    ["a basis provenance without reasons", (i) => delete ((i.authored_basis as Record<string, unknown>).source_provenance as Record<string, unknown>).reasons],
    ["a non-UTC recorded_at", (i) => (i.recorded_at = "2026-10-22T09:12:00")],
    ["an outcome state", (i) => (i.scenario_state = "OBSERVED")],
  ];

  it.each(top)("refuses %s", (_name, mutate) => {
    const b = clone(body()) as unknown as Record<string, unknown>;
    mutate(b);
    expect(isColdScenariosRead(b)).toBe(false);
  });
  it.each(window)("refuses %s", (_name, mutate) => {
    const b = clone(body()) as unknown as Record<string, unknown>;
    mutate(b.window as Record<string, unknown>);
    expect(isColdScenariosRead(b)).toBe(false);
  });
  it.each(selection)("refuses %s", (_name, mutate) => {
    const b = clone(body()) as unknown as Record<string, unknown>;
    mutate(b.selection as Record<string, unknown>);
    expect(isColdScenariosRead(b)).toBe(false);
  });
  it.each(row)("refuses %s", (_name, mutate) => {
    const b = clone(body()) as unknown as Record<string, unknown>;
    mutate((b.items as Record<string, unknown>[])[0]);
    expect(isColdScenariosRead(b)).toBe(false);
  });

  it("reads the Site-scoped route, maps refusals, network loss and a malformed 200", async () => {
    const urls: string[] = [];
    const answers: (() => Response | Promise<Response>)[] = [
      () => new Response(JSON.stringify(body()), { status: 200 }),
      () => new Response(JSON.stringify(body()), { status: 200 }),
      () => new Response(JSON.stringify({ error: { code: "COLD_WINDOW_INVALID", message: "'from' must be before 'to'." } }), { status: 422 }),
      () => new Response(JSON.stringify({ ...body(), items: [{ id: "x" }] }), { status: 200 }),
      () => Promise.reject(new TypeError("offline")),
    ];
    vi.stubGlobal("fetch", (url: string) => {
      urls.push(url);
      return answers[urls.length - 1]();
    });
    const client = new HttpColdScenariosClient("/api/sites");
    const q = { from: FROM, to: TO, known_at: null, scenario_at: AT };
    expect((await client.list(SITE_CODE, q, null)).status).toBe("loaded");
    expect((await client.list(SITE_CODE, q, "c-1")).status).toBe("loaded");
    expect(await client.list(SITE_CODE, q, null)).toEqual({
      status: "refused",
      httpStatus: 422,
      code: "COLD_WINDOW_INVALID",
      message: "'from' must be before 'to'.",
    });
    expect(await client.list(SITE_CODE, q, null)).toEqual({ status: "unavailable", message: SCENARIOS_MALFORMED });
    expect(await client.list(SITE_CODE, q, null)).toEqual({ status: "unavailable", message: null });
    expect(urls[0]).toBe(
      `/api/sites/${SITE_CODE}/cold/financials/scenarios?from=${encodeURIComponent(FROM)}&to=${encodeURIComponent(TO)}&scenario_at=${encodeURIComponent(AT)}`,
    );
    // A later page carries only its cursor: the cursor binds page one's window and clocks.
    expect(urls[1]).toBe(`/api/sites/${SITE_CODE}/cold/financials/scenarios?cursor=c-1`);
  });
});

/* ---------- page states ---------- */

describe("cold Scenarios page states", () => {
  it("states_loading_and_refusal", async () => {
    // Loading: the prose line while the read is pending.
    const pending = stub(() => new Promise(() => undefined));
    const loadingView = render(
      <MemoryRouter>
        <ColdScenarios siteCode={SITE_CODE} window={WINDOW} scenarioAt={null} client={pending.client} />
      </MemoryRouter>,
    );
    expect(loadingView.container.querySelector("p.prose")?.textContent).toBe(SCENARIOS_LOADING);
    cleanup();

    // 422: heading, exact code and message, a Retry button that refetches the same read; no window line.
    const invalid = stub(() => ({ status: "refused", httpStatus: 422, code: "COLD_WINDOW_INVALID", message: "'from' must be before 'to'." }));
    let root = await renderBody(invalid.client, WINDOW, AT);
    const refusal = root.querySelector('[data-page-refusal="cold-depth"]') as HTMLElement;
    expect(refusal.querySelector("[data-cold-depth-error]")?.textContent).toBe("The selected window needs both a start and an end, with the start before the end.");
    expect(root.querySelector("[data-cold-date-bar]")).toBeNull();
    expect(root.querySelector("[data-scenarios-empty]")).toBeNull();
    expect(root.textContent).not.toContain("No scenario defined yet");
    // F2: no dead Retry for a window refusal; the correcting link and the panel frame stay.
    expect(refusal.querySelector("button[data-cold-retry]")).toBeNull();
    expect(refusal.querySelector("a[data-cold-depth-correction]")?.textContent).toBe("Read without a selected window");
    expect(root.querySelectorAll("section.panel")).toHaveLength(1);
    expect(invalid.list.mock.calls[0]).toEqual([SITE_CODE, { ...WINDOW, scenario_at: AT }, null]);
    cleanup();

    // 503: the requested window line stays, with the server message.
    const down = stub(() => ({ status: "refused", httpStatus: 503, code: "COLD_READ_UNAVAILABLE", message: "store down" }));
    root = await renderBody(down.client);
    expect(root.querySelector("[data-cold-date-bar-requested]")).not.toBeNull();
    expect(root.querySelector("[data-cold-depth-error]")?.textContent).toBe("The cold-chain assessment could not be read. Nothing is shown as assessed until it can be.");
    const reload = root.querySelector("button[data-cold-retry]") as HTMLButtonElement;
    expect(reload.textContent).toBe("Reload");
    fireEvent.click(reload);
    await waitFor(() => expect(down.list).toHaveBeenCalledTimes(2));
    cleanup();

    // Network loss and a malformed 200: the unavailable copy, never an empty list.
    root = await renderBody(stub(() => ({ status: "unavailable", message: null })).client);
    expect(root.querySelector("[data-cold-depth-error]")?.textContent).toBe(SCENARIOS_UNREACHABLE);
    expect(root.querySelector("[data-scenarios-empty]")).toBeNull();
    cleanup();
    root = await renderBody(stub(() => ({ status: "unavailable", message: SCENARIOS_MALFORMED })).client);
    expect(root.querySelector("[data-cold-depth-error]")?.textContent).toBe(SCENARIOS_MALFORMED);
    cleanup();

    // Currentness: one amber notice above the panel per non-current state; none when current.
    for (const state of ["PENDING_RECOMPUTE", "HISTORICAL", "STALE_SOURCE", "UNKNOWN"] as const) {
      root = await renderBody(stub(() => loaded(body([], state))).client);
      const notice = root.querySelector("[data-scenarios-state-notice]") as HTMLElement;
      // post-W6 R337: pending with zero scenarios says none exists for this window.
      expect(notice.textContent).toBe(state === "PENDING_RECOMPUTE" ? "Underlying evidence is being reassessed. No authored scenario exists for this window." : SCENARIOS_STATE_NOTICE[state]);
      expect(notice.className).not.toContain("blue");
      const panel = root.querySelector("#cold-scenarios-heading")?.closest(".panel") as HTMLElement;
      expect(notice.compareDocumentPosition(panel) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
      cleanup();
    }
    root = await renderBody(stub(() => loaded(body([]))).client);
    expect(root.querySelector("[data-scenarios-state-notice]")).toBeNull();
  });

  it("row_disclosure_and_client", async () => {
    const { client, list } = stub(() => loaded(body([item({ authored_basis: { ...item().authored_basis, foundation_revision_id: null, accepted_evidence_ids: [EV_1] } })])));
    const root = await renderBody(client, WINDOW, AT);
    expect(list).toHaveBeenCalledWith(SITE_CODE, { ...WINDOW, scenario_at: AT }, null);
    const headers = Array.from(root.querySelectorAll("thead th")).map((th) => th.textContent);
    expect(headers).toEqual(["Authored scenario", "Assumptions", "Basis", "Defined at", "State"]);
    const row = root.querySelector(`[data-scenario-row="${SCENARIO}"]`) as HTMLElement;
    const cells = Array.from(row.children) as HTMLElement[];
    expect(cells[0].textContent).toBe("Vaccine stock at risk" + "CSCN-000001 revision 1");
    expect(cells[0].querySelector('[data-vocabulary-exempt="source-reference"]')?.textContent).toBe("CSCN-000001");
    expect(cells[1].textContent).toBe("1200 dose at 2.75 USD per dose");
    expect(cells[2].textContent).toBe("Selected evidence through 22 Oct 08:00 UTC" + "Review assumptions →");
    expect(cells[3].textContent).toBe("22 Oct 09:12 UTC");
    expect(cells[4].textContent).toBe("Defined");
    // No observed outcome and no create control.
    expect(root.textContent).not.toMatch(/loss|observed outcome|spoiled/i);
    expect(Array.from(root.querySelectorAll("button")).map((b) => b.textContent)).not.toContain("Create scenario");
    expect(root.querySelector("form, input")).toBeNull();

    const review = cells[2].querySelector("button") as HTMLButtonElement;
    expect(review.getAttribute("type")).toBe("button");
    expect(review.getAttribute("aria-expanded")).toBe("false");
    expect(root.querySelector("[data-scenario-expansion]")).toBeNull();
    fireEvent.click(review);
    expect(review.getAttribute("aria-expanded")).toBe("true");
    const expansion = root.querySelector(`[data-scenario-expansion="${SCENARIO}"]`) as HTMLElement;
    // Directly below its item, one full-width cell.
    expect(row.nextElementSibling).toBe(expansion);
    expect(expansion.querySelector("td")?.getAttribute("colspan")).toBe("5");
    const terms = Array.from(expansion.querySelectorAll("dt")).map((dt) => dt.textContent);
    expect(terms).toEqual([
      "Kind",
      "Assumptions",
      "Window",
      "Evidence cutoff",
      "Assessment revisions",
      "Accepted evidence",
      "Foundation revision",
      "Source classification",
      "Revision",
    ]);
    const values = Array.from(expansion.querySelectorAll("dd")) as HTMLElement[];
    expect(values[0].textContent).toBe("Stock value context");
    expect(Array.from(values[1].querySelectorAll("[data-scenario-assumption]")).map((n) => n.textContent)).toEqual([
      "Stock quantity: 1200",
      "Stock unit: dose",
      "Unit value: 2.75",
      "Currency: USD",
    ]);
    expect(values[2].textContent).toBe("6 Oct 2026 19:00–20:05 UTC");
    expect(values[3].textContent).toBe("22 Oct 08:00 UTC");
    expect(values[4].textContent).toBe(REV_A);
    expect(values[5].querySelector("[data-scenario-evidence-count]")?.textContent).toBe("1 record");
    expect(values[5].textContent).toBe(`1 record${EV_1}`);
    expect(values[6].textContent).toBe("None");
    expect(values[7].textContent).toBe("Generated test data");
    expect(values[8].textContent).toBe(REVISION);
    // Every ID is its own exempt reference value.
    const refs = Array.from(expansion.querySelectorAll('[data-vocabulary-exempt="source-reference"]')).map((n) => n.textContent);
    expect(refs).toEqual([REV_A, EV_1, REVISION]);
    expect(expansion.querySelector(".cold-scenarios-basis")).not.toBeNull();
    fireEvent.click(review);
    expect(root.querySelector("[data-scenario-expansion]")).toBeNull();
    cleanup();

    // W5-01b review L2: the row and the shared selected-window bar use one date style, seconds only when present.
    const SEC = "2026-10-22T08:00:37Z";
    const secBody = body([item({ authored_basis: { ...item().authored_basis, cutoff: SEC } })]);
    secBody.window = { ...secBody.window, known_at: SEC, committed_watermark: SEC };
    const secRoot = await renderBody(stub(() => loaded(secBody)).client);
    const secCells = Array.from((secRoot.querySelector(`[data-scenario-row="${SCENARIO}"]`) as HTMLElement).children) as HTMLElement[];
    expect(secCells[2].textContent).toBe("Selected evidence through 22 Oct 08:00:37 UTC" + "Review assumptions →");
    expect(secRoot.querySelector("[data-cold-date-bar]")?.textContent).toContain("22 Oct 08:00:37 UTC");
    cleanup();

    // Q-C5b-4: a 95-ID basis is one keyboard-reachable region with every full ID in order, bounded at 360px.
    const many = Array.from({ length: 95 }, (_, n) => `4e5f6071-8293-4eaf-80b1-${String(n).padStart(12, "0")}`);
    const style = document.createElement("style");
    style.textContent = SCENARIOS_CSS;
    document.head.appendChild(style);
    try {
      const big = await renderBody(stub(() => loaded(body([item({ authored_basis: { ...item().authored_basis, accepted_evidence_ids: many } })]))).client);
      fireEvent.click(big.querySelector("[data-scenario-review]") as HTMLButtonElement);
      const region = big.querySelector(`[data-scenario-basis="${SCENARIO}"]`) as HTMLElement;
      expect(region.tagName).toBe("DIV");
      expect(region.className).toBe("cold-scenarios-basis");
      expect(region.getAttribute("role")).toBe("region");
      expect(region.getAttribute("aria-label")).toBe("Authored scenario basis");
      expect(region.tabIndex).toBe(0);
      const ids = Array.from(region.querySelectorAll('[data-vocabulary-exempt="source-reference"]')).map((n) => n.textContent);
      expect(ids.filter((value) => value !== null && value.startsWith("4e5f6071-8293-4eaf-80b1-"))).toEqual(many);
      // jsdom applies no media queries, so it computes the desktop rule; the 390 computed 220px is the browser
      // layout assertion in `.agent/W5-01b-C5-evidence/capture.mjs` (Q-C5c-2).
      const computed = window.getComputedStyle(region);
      expect(computed.maxHeight).toBe("360px");
      expect(computed.overflowY).toBe("auto");
    } finally {
      style.remove();
    }
    // The 360px rule sits outside the phone media query; the Q-C5c-2 phone rule shortens it to 220px and gives the
    // Basis column a readable width inside the DataTable scroller.
    const flat = SCENARIOS_CSS.replace(/\s+/g, " ");
    const rule = ".cold-scenarios-basis { max-height: 360px; overflow-y: auto; }";
    const phoneRule = "@media (max-width: 640px) { .cold-scenarios-panel .data-table { min-width: 820px; } " +
      ".cold-scenarios-panel .data-table tr > :nth-child(3) { min-width: 190px; } .cold-scenarios-basis { max-height: 220px; } }";
    expect(flat.indexOf(rule)).toBeGreaterThan(-1);
    expect(flat.indexOf(phoneRule)).toBeGreaterThan(flat.indexOf(rule));
    cleanup();

    // Two records read `2 records`; the Scenarios address keeps the four keys in order and drops unset ones.
    const two = await renderBody(stub(() => loaded(body())).client);
    fireEvent.click(two.querySelector("[data-scenario-review]") as HTMLButtonElement);
    expect(two.querySelector("[data-scenario-evidence-count]")?.textContent).toBe("2 records");
    expect(siteFinancialScenariosHref(SITE_CODE, { from: FROM, to: TO, known_at: KNOWN, scenario_at: AT })).toBe(
      `/sites/${SITE_CODE}/financials/scenarios?from=${encodeURIComponent(FROM)}&to=${encodeURIComponent(TO)}&known_at=${encodeURIComponent(KNOWN)}&scenario_at=${encodeURIComponent(AT)}`,
    );
    expect(siteFinancialScenariosHref(SITE_CODE, { from: null, to: null, known_at: null })).toBe(`/sites/${SITE_CODE}/financials/scenarios`);
    expect(siteFinancialScenariosHref(SITE_CODE)).toBe(`/sites/${SITE_CODE}/financials/scenarios`);
  });

  it("pages 51 authored rows: Next follows the cursor, First page clears it", async () => {
    const rows = Array.from({ length: 51 }, (_, n) =>
      item({ id: `a1b2c3d4-e5f6-4a7b-8c9d-${String(n).padStart(12, "0")}`, revision_id: `b2c3d4e5-f6a7-4b8c-9d0e-${String(n).padStart(12, "0")}` }, n + 1),
    );
    const { client, list } = stub((cursor) =>
      cursor === null ? loaded(body(rows.slice(0, 50), "CURRENT", "page-2", 2)) : loaded(body(rows.slice(50), "CURRENT", null, 2)),
    );
    const root = await renderBody(client);
    expect(root.querySelectorAll("[data-scenario-row]")).toHaveLength(50);
    const nav = root.querySelector('nav[aria-label="Scenario pages"]') as HTMLElement;
    const table = root.querySelector("table") as HTMLElement;
    expect(table.compareDocumentPosition(nav) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    const first = () => root.querySelector("[data-scenarios-first]") as HTMLButtonElement;
    const next = () => root.querySelector("[data-scenarios-next]") as HTMLButtonElement;
    expect(first().textContent).toBe("First page");
    expect(next().textContent).toBe("Next");
    // Q-C5b-2: the counter follows `Next` inside the pager nav and states the C4 total.
    const count = () => root.querySelector('nav[aria-label="Scenario pages"] [data-scenarios-page-count]') as HTMLElement;
    expect(count().tagName).toBe("SPAN");
    expect(next().nextElementSibling).toBe(count());
    expect(count().textContent).toBe("1 of 2");
    expect(first().disabled).toBe(true);
    expect(next().disabled).toBe(false);
    fireEvent.click(next());
    await waitFor(() => expect(root.querySelectorAll("[data-scenario-row]")).toHaveLength(1));
    expect(list.mock.calls[1][2]).toBe("page-2");
    expect(root.textContent).toContain("CSCN-000051");
    expect(count().textContent).toBe("2 of 2");
    expect(next().disabled).toBe(true);
    expect(first().disabled).toBe(false);
    fireEvent.click(first());
    await waitFor(() => expect(root.querySelectorAll("[data-scenario-row]")).toHaveLength(50));
    expect(list.mock.calls[list.mock.calls.length - 1][2]).toBeNull();
  });

  it("restarts at page 1 when Retry follows a changed-basis page cursor", async () => {
    const rows = Array.from({ length: 51 }, (_, n) =>
      item({ id: `a1b2c3d4-e5f6-4a7b-8c9d-${String(n).padStart(12, "0")}`, revision_id: `b2c3d4e5-f6a7-4b8c-9d0e-${String(n).padStart(12, "0")}` }, n + 1),
    );
    const { client, list } = stub((cursor) =>
      cursor === null
        ? loaded(body(rows.slice(0, 50), "CURRENT", "page-2", 2))
        : {
            status: "refused",
            httpStatus: 409,
            code: "COLD_SCENARIO_CURSOR_BASIS_CHANGED",
            message: "The selected cold scenario basis changed. Start at the first page.",
          },
    );
    const root = await renderBody(client);
    fireEvent.click(root.querySelector("[data-scenarios-next]") as HTMLButtonElement);
    await waitFor(() => expect(root.querySelector("button[data-cold-retry]")).not.toBeNull());
    const retry = root.querySelector("button[data-cold-retry]") as HTMLButtonElement;
    expect(root.textContent).toContain("The selected cold scenario basis changed. Start at the first page.");
    fireEvent.click(retry);
    await waitFor(() => expect(root.querySelectorAll("[data-scenario-row]")).toHaveLength(50));
    expect(list.mock.calls.map((call) => call[2])).toEqual([null, "page-2", null]);
    expect(list.mock.calls[2][0]).toBe(list.mock.calls[0][0]);
    expect(list.mock.calls[2][1]).toEqual(list.mock.calls[0][1]);
    expect(root.querySelector("[data-scenarios-page-count]")?.textContent).toBe("1 of 2");
    expect((root.querySelector("[data-scenarios-first]") as HTMLButtonElement).disabled).toBe(true);
  });
});

/* ---------- the composed page, through the real App route ---------- */

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

async function renderPage(client: ColdScenariosClient, search = `?from=${encodeURIComponent(FROM)}&to=${encodeURIComponent(TO)}&known_at=${encodeURIComponent(KNOWN)}&scenario_at=${encodeURIComponent(AT)}`) {
  vi.stubGlobal("fetch", () => new Promise(() => undefined));
  const detail: SiteDetailClient = { getSite: () => Promise.resolve({ status: "loaded", site: SITE }) };
  const directory: SiteDirectoryClient = { listSites: () => Promise.resolve({ status: "loaded", sites: [SITE] }) };
  render(
    <MemoryRouter initialEntries={[`/sites/${SITE_CODE}/financials/scenarios${search}`]}>
      <App flags={featureFlagsWith(false)} siteDirectory={directory} siteDetail={detail} siteAnalytics={EMPTY_ANALYTICS_CLIENT} coldScenarioList={client} />
    </MemoryRouter>,
  );
  await settledScreen();
  await waitFor(() => expect(document.body.textContent).not.toContain(SCENARIOS_LOADING));
  return document.querySelector("main") as HTMLElement;
}

describe("authored, pending and historical cold Scenarios", () => {
  it("authored_pending_historical_basis", async () => {
    // Empty: the Site-name heading, mock subtitle, live Scenarios tab, the mock empty block and the blue notice.
    // Q-C5b-1: a COLDCHAIN Site owns the live cold Scenarios destination and reads the C4 list.
    const emptyRead = stub(() => loaded(body([])));
    let main = await renderPage(emptyRead.client);
    expect(emptyRead.list).toHaveBeenCalled();
    expect(main.querySelector("[data-scenarios-site-type-unsupported]")).toBeNull();
    expect(main.querySelector("h1")?.textContent).toContain("Kobo vaccine cold store");
    expect(main.querySelector("h1")?.textContent).not.toBe("Scenarios");
    expect(main.textContent).toContain("Financials · scenarios (placeholder)");
    const crumbs = Array.from(document.querySelectorAll('nav[aria-label="Breadcrumb"] li, .breadcrumbs li')).map((li) => li.textContent?.trim());
    expect(crumbs.slice(-2)).toEqual(["Financials", "Scenarios"]);
    const live = main.querySelector('[data-financials-section="scenarios"]') as HTMLAnchorElement;
    expect(live.getAttribute("aria-current")).toBe("page");
    expect(live.getAttribute("href")).toBe(siteFinancialScenariosHref(SITE_CODE, { from: FROM, to: TO, known_at: KNOWN, scenario_at: AT }));
    // Back-links carry the window and drop the authored-only scenario_at.
    expect((main.querySelector('[data-financials-section="overview"]') as HTMLAnchorElement).getAttribute("href")).toBe(
      `/sites/${SITE_CODE}/financials?from=${encodeURIComponent(FROM)}&to=${encodeURIComponent(TO)}&known_at=${encodeURIComponent(KNOWN)}`,
    );
    expect(main.querySelector("[data-tab-unavailable]")).toBeNull();
    const panel = main.querySelector("#cold-scenarios-heading")?.closest(".panel") as HTMLElement;
    expect(panel.querySelector("#cold-scenarios-heading")?.textContent).toBe("Financial scenarios");
    // post-W6 R337 (R25 D4): the built page states what the panel holds; no working-note literal remains.
    expect(panel.querySelector(".panel__description")?.textContent).toBe("Labelled what-ifs authored for this site; never measured results.");
    expect(main.textContent).not.toContain("Placeholder");
    expect(main.textContent).not.toContain("to be designed");
    const empty = panel.querySelector("[data-scenarios-empty]") as HTMLElement;
    expect(empty.querySelector("h3")?.textContent).toBe("No scenario defined yet");
    expect(empty.querySelector("p")?.textContent).toBe(SCENARIOS_EMPTY_BODY);
    expect(panel.querySelector("table")).toBeNull();
    expect(main.querySelector('nav[aria-label="Scenario pages"]')).toBeNull();
    const closing = main.querySelector("[data-scenarios-closing-notice]") as HTMLElement;
    expect(closing.textContent).toBe(SCENARIOS_CLOSING_NOTICE);
    expect(closing.className).toContain("v69-notice--blue");
    // Q-C5c-1: the mock `info` icon through RailIcon, then the closing paragraph.
    const icon = closing.firstElementChild as Element;
    expect(icon.matches('svg[data-rail-icon="info"]')).toBe(true);
    expect(icon.querySelector("path")?.getAttribute("d")).toBe("M12 3a9 9 0 1 0 0 18a9 9 0 1 0 0-18 M12 10v7 M12 7v1");
    expect(icon.nextElementSibling?.tagName).toBe("P");
    expect(icon.nextElementSibling?.textContent).toBe(SCENARIOS_CLOSING_NOTICE);
    expect(panel.compareDocumentPosition(closing) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(main.querySelector("[data-cold-date-bar]")?.textContent).toContain("Selected window");
    // W5-01b review H1: no standalone authored-clock line; the mock empty block and closing notice keep their copy.
    expect(main.querySelector("[data-scenarios-through]")).toBeNull();
    cleanup();

    // Authored, current: the full page passes the W1 scan with the open disclosure and the pager.
    main = await renderPage(stub(() => loaded(body())).client);
    fireEvent.click(main.querySelector("[data-scenario-review]") as HTMLButtonElement);
    expect(main.querySelector("[data-scenarios-state-notice]")).toBeNull();
    expect(main.querySelector("[data-scenarios-empty]")).toBeNull();
    expect(main.querySelector("[data-scenarios-through]")).toBeNull();
    const scan = scanProductVocabulary(main, "cold-scenarios", { set: "w1", screen: "cold-scenarios" });
    expect(scan.scanned).toBeGreaterThan(20);
    expect(describeViolations(scan.violations)).toBe("");
    // The glossary is per screen and exact: unglossed, the same page fails.
    expect(scanProductVocabulary(main, "cold-scenarios", { set: "w1" }).violations.length).toBeGreaterThan(0);
    cleanup();

    // Pending: amber notice above the panel; the row pill stays Defined.
    main = await renderPage(stub(() => loaded(body([item()], "PENDING_RECOMPUTE"))).client);
    const pendingNotice = main.querySelector("[data-scenarios-state-notice]") as HTMLElement;
    expect(pendingNotice.textContent).toBe("Underlying evidence is being reassessed; the authored scenario remains separate.");
    expect(pendingNotice.className).not.toContain("blue");
    cleanup();
    // post-W6 R337: two or more authored scenarios (here a second page exists) pluralise the pending sentence.
    main = await renderPage(stub(() => loaded(body([item()], "PENDING_RECOMPUTE", "c2", 2))).client);
    expect(main.querySelector("[data-scenarios-state-notice]")?.textContent).toBe("Underlying evidence is being reassessed; the authored scenarios remain separate.");
    cleanup();
    main = await renderPage(stub(() => loaded(body([item()], "PENDING_RECOMPUTE"))).client);
    expect(main.querySelector(`[data-scenario-row="${SCENARIO}"] .badge, [data-scenario-row="${SCENARIO}"] [class*="badge"]`)?.textContent).toBe("Defined");
    const pendingScan = scanProductVocabulary(main, "cold-scenarios", { set: "w1", screen: "cold-scenarios" });
    expect(describeViolations(pendingScan.violations)).toBe("");
    cleanup();

    // Historical: a superseded revision reads Historical with the historical selection notice.
    main = await renderPage(stub(() => loaded(body([item({ scenario_state: "HISTORICAL", revision_no: 1 })], "HISTORICAL"))).client);
    expect(main.querySelector("[data-scenarios-state-notice]")?.textContent).toBe("Read at an earlier evidence cutoff; newer evidence exists.");
    expect(main.querySelector(`[data-scenario-row="${SCENARIO}"]`)?.lastElementChild?.textContent).toBe("Historical");
    expect(main.textContent).not.toMatch(/\bCURRENT\b|\bHISTORICAL\b|STOCK_VALUE_CONTEXT/);
    fireEvent.click(main.querySelector("[data-scenario-review]") as HTMLButtonElement);
    const historicalScan = scanProductVocabulary(main, "cold-scenarios", { set: "w1", screen: "cold-scenarios" });
    expect(historicalScan.scanned).toBeGreaterThan(20);
    expect(describeViolations(historicalScan.violations)).toBe("");
  });

  it("keeps the mini-grid-only panel for a Site that is neither cold nor mini-grid", async () => {
    vi.stubGlobal("fetch", () => new Promise(() => undefined));
    const ev = { ...SITE, site_id: "EV-001", site_type: "EV_CHARGING" } as unknown as SiteDetailReadModel;
    const { client, list } = stub(() => loaded(body()));
    const detail: SiteDetailClient = { getSite: () => Promise.resolve({ status: "loaded", site: ev }) };
    const directory: SiteDirectoryClient = { listSites: () => Promise.resolve({ status: "loaded", sites: [ev] }) };
    render(
      <MemoryRouter initialEntries={["/sites/EV-001/financials/scenarios"]}>
        <App flags={featureFlagsWith(false)} siteDirectory={directory} siteDetail={detail} siteAnalytics={EMPTY_ANALYTICS_CLIENT} coldScenarioList={client} />
      </MemoryRouter>,
    );
    await settledScreen();
    await waitFor(() => expect(document.querySelector("[data-scenarios-site-type-unsupported]")).not.toBeNull());
    expect(document.querySelector("[data-tab-unavailable]")?.textContent).toContain("Scenarios");
    expect(document.body.textContent).toContain("Financials · scenarios");
    expect(document.body.textContent).not.toContain("(placeholder)");
    expect(list).not.toHaveBeenCalled();
  });
});

describe("post-W6 final-fix L4/L5: the cold Scenarios Site tab row", () => {
  const tabHrefs = () =>
    Array.from(document.querySelectorAll('nav[aria-label="Site sections"] a')).map((a) => a.getAttribute("href") ?? "");

  it("carries the validated window and cutoff, like the breadcrumb", async () => {
    await renderPage(stub(() => loaded(body([]))).client);
    const overview = tabHrefs().find((h) => h.startsWith(`/sites/${SITE_CODE}?`)) ?? "";
    expect(overview).toContain(`from=${encodeURIComponent(FROM)}`);
    expect(overview).toContain(`to=${encodeURIComponent(TO)}`);
    expect(overview).toContain(`known_at=${encodeURIComponent(KNOWN)}`);
    expect(overview).not.toContain("scenario_at");
  });

  it("drops a one-sided window from the tab row but keeps a valid cutoff", async () => {
    await renderPage(stub(() => loaded(body([]))).client, `?from=${encodeURIComponent(FROM)}&known_at=${encodeURIComponent(KNOWN)}`);
    const all = tabHrefs().join(" ");
    expect(all).not.toContain("from=");
    expect(all).toContain(`known_at=${encodeURIComponent(KNOWN)}`);
  });

  it("propagates nothing when the address has no selection", async () => {
    await renderPage(stub(() => loaded(body([]))).client, "");
    expect(tabHrefs().join(" ")).not.toContain("?");
  });
});
