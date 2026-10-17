/**
 * W1-F4 (D-2026-10-17-mockup-layout-spec), group C2: the Action Plan, Evidence
 * and Verification routes render exactly their v69 panels, in order, in a
 * stocked, an empty and a refused variant, with the unsupported read stated
 * inside its panel slot and no leading answer card. Reads are the S6-02a
 * committed wire contract served through a stubbed `fetch`, as in
 * `siteActionVerification.test.tsx`.
 */
import { cleanup, render } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import actionContract from "../../../../backend/tests/fixtures/s6_action_api_contract.json";
import contract from "../../../../backend/tests/fixtures/s6_verification_api_contract.json";
import { SiteActionFrame } from "../../shell/SiteAnalyticsFrames";
import { expectV69Panels, panelTitled } from "../../test/panelStructure";
import { settledScreen } from "../../test/settled";
import type { SiteDetailClient } from "../siteDirectoryClient";
import { HYBRID_MINI_GRID_SITE } from "./sldFixtures";

type Body = any;
const R = contract.responses as unknown as Record<string, Body>;
const AM = actionContract.manifest as unknown as Record<string, Record<string, { body: Body }>>;

const ACTION = "a0000000-0000-4000-8000-000000000001";
const PLAN = "a0000000-0000-4000-8000-000000000002";
const OUT1 = "a0000000-0000-4000-8000-000000000003";
const OUT2 = "a0000000-0000-4000-8000-000000000004";
const CUTOFF = "2026-11-02T12:30:00+00:00";
const BY_KEY: Record<string, string> = { action_id: ACTION, plan_id: PLAN, verification_plan_id: PLAN };

function prep<T>(value: T, outcomes: Record<string, string> = {}): T {
  const walk = (node: unknown, key: string | null): unknown => {
    if (Array.isArray(node)) return node.map((item) => walk(item, key));
    if (node && typeof node === "object") return Object.fromEntries(Object.entries(node).map(([k, v]) => [k, walk(v, k)]));
    if (node === "<uuid>") return (key !== null && (outcomes[key] ?? BY_KEY[key])) || "a0000000-0000-4000-8000-0000000000ff";
    if (node === "ACT-<n>") return "ACT-7";
    return node;
  };
  return walk(structuredClone(value), null) as T;
}

const API = `/api/sites/KOBO-001/actions/${ACTION}`;
const V = `${API}/verification`;
const ok = (body: unknown) => ({ status: 200, body });
const down = { status: 503, body: { detail: { code: "STORE_UNAVAILABLE", message: "The store is down." } } };

function key(url: string): string {
  const [path, query = ""] = url.split("?");
  const params = query.split("&").filter(Boolean).map((p) => p.split("=").map(decodeURIComponent)).sort(([a], [b]) => a.localeCompare(b));
  return `${decodeURIComponent(path)}${params.length ? `?${params.map(([k, v]) => `${k}=${v}`).join("&")}` : ""}`;
}

function serve(gets: Record<string, { status: number; body: unknown }>) {
  const table = new Map(Object.entries(gets).map(([url, value]) => [key(url), value]));
  vi.stubGlobal("fetch", async (url: string) => {
    const hit = table.get(key(url));
    if (!hit) return new Response(JSON.stringify({ detail: { code: "TEST_UNMATCHED", message: key(url) } }), { status: 599 });
    return new Response(JSON.stringify(hit.body), { status: hit.status });
  });
}

const detail = { getSite: async (siteId: string) => ({ status: "loaded", site: { ...HYBRID_MINI_GRID_SITE, site_id: siteId } }) } as unknown as SiteDetailClient;

function mount(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/sites/:siteId/actions/:actionId/:actionView" element={<SiteActionFrame detail={detail} sitesPath="/sites" />} />
      </Routes>
    </MemoryRouter>,
  );
}

function actionReads(query = "") {
  const action = prep(R.action_resolved);
  action.action.id = ACTION;
  action.selection.cutoff_recorded_at = CUTOFF;
  return { [`${API}${query}`]: ok(action), [`${API}/events${query}`]: ok(AM["action-history:1#a"].events_latest.body) };
}

const history = () => {
  const h = prep(R.history);
  h.outcomes[0].outcome_id = OUT1;
  h.outcomes[1].outcome_id = OUT2;
  h.resolution_events[0].verification_outcome_id = OUT1;
  h.resolution_events[1].verification_outcome_id = OUT1;
  return h;
};

const outcomeCurrent = () => {
  const o = prep(R.outcome_current, { outcome_id: OUT1 });
  o.current_state.outcome_id = OUT1;
  return o;
};

const q = (selector: string) => document.body.querySelector(selector);

async function structure(screenId: string) {
  await settledScreen();
  expectV69Panels(screenId);
  expect(q("[data-headline-card]"), "no leading answer card").toBeNull();
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("W1-F4 C2: Action Plan keeps the v69 panel structure (action-plan)", () => {
  it("stocked: one Success criteria panel holds the criteria and both windows", async () => {
    serve({ ...actionReads(), [`${V}/plan`]: ok(prep(R.plan)) });
    mount(`/sites/KOBO-001/actions/${ACTION}/plan`);
    await structure("action-plan");
    const panel = panelTitled("Success criteria");
    expect(panel.querySelectorAll("[data-verification-criterion]").length).toBe(6);
    expect(panel.querySelectorAll("[data-verification-window]").length).toBe(2);
    expect(q("[data-page-refusal]")).toBeNull();
  });

  it("empty: no plan says No success criteria recorded inside the panel", async () => {
    const none = prep(R.plan);
    none.plan = null;
    none.verification_state = { state: "NO_PLAN", reasons: [], plan_id: null, outcome_id: null, statement: "" };
    serve({ ...actionReads(), [`${V}/plan`]: ok(none) });
    mount(`/sites/KOBO-001/actions/${ACTION}/plan`);
    await structure("action-plan");
    expect(panelTitled("Success criteria").querySelector("[data-panel-gap='no-plan']")?.textContent).toMatch(/^No success criteria recorded\./);
  });

  it("refused: the refusal is stated before the panel, which keeps its slot with the gap inside", async () => {
    serve({ ...actionReads(), [`${V}/plan`]: down });
    mount(`/sites/KOBO-001/actions/${ACTION}/plan`);
    await structure("action-plan");
    expect(q("[data-page-refusal='refused']")).not.toBeNull();
    expect(panelTitled("Success criteria").querySelector("[data-panel-gap='refused']")?.textContent).toContain("could not be read");
  });

  it("selector conflict: stated before the panel, nothing chosen inside it", async () => {
    serve({ ...actionReads(`?recorded_at=${encodeURIComponent(CUTOFF)}`) });
    mount(`/sites/KOBO-001/actions/${ACTION}/plan?recorded_at=${encodeURIComponent(CUTOFF)}&plan_revision_id=${PLAN}`);
    await structure("action-plan");
    expect(q("[data-page-refusal='selector-conflict']")).not.toBeNull();
    expect(panelTitled("Success criteria").querySelector("[data-panel-gap='conflict']")).not.toBeNull();
    expect(q("[data-verification-plan-id]")).toBeNull();
  });
});

describe("W1-F4 C2: Action Evidence keeps the v69 panel structure (action-evidence)", () => {
  it("stocked: one Evidence requirements panel; the per-window readings sit in its closed disclosure", async () => {
    serve({ ...actionReads(), [`${V}/evidence`]: ok(prep(R.evidence)), [`${V}/plan?plan_id=${PLAN}`]: ok(prep(R.plan)) });
    mount(`/sites/KOBO-001/actions/${ACTION}/evidence`);
    await structure("action-evidence");
    const panel = panelTitled("Evidence requirements");
    expect(panel.querySelectorAll("[data-verification-requirement]").length).toBe(5);
    expect(panel.querySelectorAll("[data-verification-evidence-window]").length).toBe(2);
    expect(panel.querySelector("[data-disclosure='verification-evidence-detail']")).not.toBeNull();
  });

  it("missing readings: the gap is named inside the panel, never as complete", async () => {
    const ev = prep(R.evidence);
    const slot = ev.windows.later.slots[3];
    const load = Object.keys(slot.feeder_demand)[0];
    slot.feeder_demand[load] = { ...slot.feeder_demand[load], state: "MISSING", kwh: null, evidence_ids: [], problems: [{ code: "GAP", detail: "no interval reading covers the slot" }] };
    slot.complete = false;
    ev.windows.later.complete = false;
    serve({ ...actionReads(), [`${V}/evidence`]: ok(ev), [`${V}/plan?plan_id=${PLAN}`]: ok(prep(R.plan)) });
    mount(`/sites/KOBO-001/actions/${ACTION}/evidence`);
    await structure("action-evidence");
    const panel = panelTitled("Evidence requirements");
    expect(panel.querySelector("[data-verification-requirement='later']")).toHaveAttribute("data-verification-requirement-ok", "no");
    expect(panel.querySelector("[data-verification-window-problems='later']")?.textContent).toMatch(/^Gap/);
  });

  it("refused: the refusal is stated before the panel, which keeps its slot with the gap inside", async () => {
    serve({ ...actionReads(), [`${V}/evidence`]: down });
    mount(`/sites/KOBO-001/actions/${ACTION}/evidence`);
    await structure("action-evidence");
    expect(q("[data-page-refusal='refused']")).not.toBeNull();
    expect(panelTitled("Evidence requirements").querySelector("[data-panel-gap='refused']")?.textContent).toContain("could not be read");
  });
});

describe("W1-F4 C2: Verification keeps the v69 panel structure (verification)", () => {
  it("stocked: strip, four cards from the read, panel 1 full width, then Activity and Outcome evidence side by side", async () => {
    serve({ ...actionReads(), [`${V}/history`]: ok(history()), [`${V}/outcome`]: ok(outcomeCurrent()) });
    mount(`/sites/KOBO-001/actions/${ACTION}/verification`);
    await structure("verification");
    expect(q(".status-strip--line[data-verification-current-state='VERIFIED']")).not.toBeNull();
    expect(document.querySelectorAll(".v69-cards [data-verification-card]").length).toBe(4);
    const pair = q(".panel-pair");
    expect(pair?.querySelectorAll(":scope > .panel").length).toBe(2);
    expect(panelTitled("Target and guardrails evaluated together").querySelector("[data-verification-row='target_reduction']")).not.toBeNull();
    expect(panelTitled("Outcome evidence").querySelector("[data-verification-comparison='comparable']")).not.toBeNull();
    expect(panelTitled("Activity evidence").textContent).toContain("Completed work is evidence of activity, not resolution.");
  });

  it("empty: a withdrawn outcome (reassessment pending) leaves every slot with a pending gap, no result", async () => {
    serve({ ...actionReads(), [`${V}/history`]: ok(history()), [`${V}/outcome`]: ok(prep(R.outcome_reassessment_pending, { outcome_id: OUT1 })) });
    mount(`/sites/KOBO-001/actions/${ACTION}/verification`);
    await structure("verification");
    expect(panelTitled("Target and guardrails evaluated together").querySelector("[data-panel-gap='pending']")).not.toBeNull();
    expect(panelTitled("Outcome evidence").querySelector("[data-panel-gap='pending']")?.textContent).toContain("pending");
    expect(q("[data-verification-outcome]")).toBeNull();
    for (const card of Array.from(document.querySelectorAll("[data-verification-card]"))) expect(card.textContent).toContain("Pending");
  });

  it("refused: the outcome refusal is stated before the slots; cards read Not available and panels state the gap", async () => {
    serve({ ...actionReads(), [`${V}/history`]: ok(history()), [`${V}/outcome`]: down });
    mount(`/sites/KOBO-001/actions/${ACTION}/verification`);
    await structure("verification");
    expect(q("[data-page-refusal='refused']")).not.toBeNull();
    expect(panelTitled("Target and guardrails evaluated together").querySelector("[data-panel-gap='refused']")).not.toBeNull();
    expect(panelTitled("Outcome evidence").querySelector("[data-panel-gap='refused']")).not.toBeNull();
    for (const card of Array.from(document.querySelectorAll("[data-verification-card]"))) expect(card.textContent).toContain("Not available");
  });

  it("historical selection: the exact earlier outcome keeps the same three panels", async () => {
    const o = prep(R.outcome_historical, { outcome_id: OUT1 });
    o.superseded_by_outcome_id = OUT2;
    serve({ ...actionReads(), [`${V}/history`]: ok(history()), [`${V}/outcome?outcome_id=${OUT1}`]: ok(o) });
    mount(`/sites/KOBO-001/actions/${ACTION}/verification?outcome_id=${OUT1}`);
    await structure("verification");
    expect(q("[data-verification-historical]")?.textContent).toMatch(/^Historical/);
  });
});
