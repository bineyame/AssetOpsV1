import { reasonWords as sourceReasonWords } from "../sourceProvenance";
/**
 * S6-02b: the Action Plan / Evidence / Verification child views, the
 * Recommendation success panels and the Foundation change later-effect panels,
 * against S6-02a's committed wire contract
 * `backend/tests/fixtures/s6_verification_api_contract.json` (TEST-SCOPED
 * complete windows and authored source resolution). `fetch` is stubbed to serve
 * the recorded responses, so the real clients and screens read real persisted
 * shapes.
 *
 * The contract normalises identifiers to `<uuid>`; `prep` gives the ones the
 * screens link by (Action, plan, outcomes, change, event, Finding) fixed values
 * and every other `<uuid>` one shared value. Derived bodies, each marked
 * "Derived" where built:
 * 1. INEFFECTIVE with a measured GUARDRAIL_FAIL, INEFFECTIVE target-only and
 *    INCONCLUSIVE outcome reads, from the recorded current outcome read with
 *    the typed outcome, reasons and metrics changed as the evaluator writes them
 *    (`verification_rules.decide`);
 * 2. a plan read with no later selection appended, and one with no plan;
 * 3. an evidence read with one later slot's demand reading missing (GAP);
 * 4. a recommendation/change read carrying a verification block (S6-01 contract
 *    bodies plus the S6-02a `verification` field);
 * 5. the overlap recommendation with the blocking Action's origin on another
 *    Finding.
 */
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import actionContract from "../../../../backend/tests/fixtures/s6_action_api_contract.json";
import contract from "../../../../backend/tests/fixtures/s6_verification_api_contract.json";
import { SiteActionFrame, SiteFindingFrame, SiteFoundationChangeFrame } from "../../shell/SiteAnalyticsFrames";
import { describeViolations, scanDisclosureVocabulary, scanProductVocabulary } from "../../test/productVocabulary";
import { panelTitled } from "../../test/panelStructure";
import { expectStateLineVisible, visibleOutsideClosedDisclosure } from "../../test/productPresentation";
import { settledScreen } from "../../test/settled";
import type { SiteDetailClient } from "../siteDirectoryClient";
import { HYBRID_MINI_GRID_SITE } from "./sldFixtures";
import { COLD_SITE, DOMAIN_ID, SITE as COLD_CODE, detailBody, indexBody } from "./coldWorkFixtures";
import { EV_SITE } from "./evWorkFixtures";
import type { DomainActionClient, DomainDetailResult } from "../domainActionClient";
import { requirementTone, sourcePair } from "../SiteActionVerification";

type Body = any;
const R = contract.responses as unknown as Record<string, Body>;
type Case = { request: { method: string; path: string }; status: number; body: Body };
const AM = actionContract.manifest as unknown as Record<string, Record<string, Case>>;

const ACTION = "a0000000-0000-4000-8000-000000000001";
const PLAN = "a0000000-0000-4000-8000-000000000002";
const OUT1 = "a0000000-0000-4000-8000-000000000003";
const OUT2 = "a0000000-0000-4000-8000-000000000004";
const CHANGE = "a0000000-0000-4000-8000-000000000005";
const EVENT = "a0000000-0000-4000-8000-000000000006";
const FINDING = "a0000000-0000-4000-8000-000000000007";
const OTHER_FINDING = "a0000000-0000-4000-8000-000000000008";
const PLAN2 = "a0000000-0000-4000-8000-000000000009";
const ANY = "a0000000-0000-4000-8000-0000000000ff";
const CUTOFF = "2026-11-02T12:30:00+00:00";

const BY_KEY: Record<string, string> = {
  action_id: ACTION,
  plan_id: PLAN,
  verification_plan_id: PLAN,
  change_id: CHANGE,
  applied_event_id: EVENT,
  finding_id: FINDING,
};

/** Fixed IDs for linked identifiers, one shared value for the rest; `outcomes` names the outcome IDs. */
function prep<T>(value: T, outcomes: Record<string, string> = {}): T {
  const walk = (node: unknown, key: string | null): unknown => {
    if (Array.isArray(node)) return node.map((item) => walk(item, key));
    if (node && typeof node === "object") {
      const out: Record<string, unknown> = {};
      for (const [k, v] of Object.entries(node)) out[k] = walk(v, k);
      return out;
    }
    if (node === "<uuid>") {
      if (key !== null && outcomes[key]) return outcomes[key];
      if (key !== null && BY_KEY[key]) return BY_KEY[key];
      return ANY;
    }
    if (node === "ACT-<n>") return "ACT-7";
    return node;
  };
  return walk(structuredClone(value), null) as T;
}

const API = `/api/sites/KOBO-001/actions/${ACTION}`;
const V = `${API}/verification`;

function key(method: string, url: string): string {
  const [path, query = ""] = url.split("?");
  const params = query
    .split("&")
    .filter(Boolean)
    .map((pair) => pair.split("=").map(decodeURIComponent) as [string, string])
    .sort(([a], [b]) => a.localeCompare(b));
  return `${method} ${decodeURIComponent(path)}${params.length ? `?${params.map(([k, v]) => `${k}=${v}`).join("&")}` : ""}`;
}

function serve(gets: Record<string, { status: number; body: unknown }>) {
  const table = new Map<string, { status: number; body: unknown }>();
  for (const [url, value] of Object.entries(gets)) table.set(key("GET", url), value);
  const requests: string[] = [];
  vi.stubGlobal("fetch", async (url: string) => {
    const k = key("GET", url);
    requests.push(k);
    const hit = table.get(k);
    if (!hit) return new Response(JSON.stringify({ detail: { code: "TEST_UNMATCHED", message: k } }), { status: 599 });
    return new Response(JSON.stringify(hit.body), { status: hit.status });
  });
  return { requests };
}

const ok = (body: unknown) => ({ status: 200, body });

const detail: SiteDetailClient = {
  getSite: async (siteId: string) => ({ status: "loaded", site: { ...HYBRID_MINI_GRID_SITE, site_id: siteId } }),
} as SiteDetailClient;

function Where() {
  const location = useLocation();
  return <output data-testid="where">{`${location.pathname}${location.search}`}</output>;
}

function mount(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        {["/sites/:siteId/actions/:actionId", "/sites/:siteId/actions/:actionId/:actionView"].map((p) => (
          <Route key={p} path={p} element={<><SiteActionFrame detail={detail} sitesPath="/sites" /><Where /></>} />
        ))}
        {["/sites/:siteId/findings/:findingId", "/sites/:siteId/findings/:findingId/:findingView"].map((p) => (
          <Route key={p} path={p} element={<><SiteFindingFrame detail={detail} sitesPath="/sites" /><Where /></>} />
        ))}
        <Route path="/sites/:siteId/foundation/changes/:changeId" element={<><SiteFoundationChangeFrame detail={detail} sitesPath="/sites" /><Where /></>} />
      </Routes>
    </MemoryRouter>,
  );
}

const q = (selector: string) => document.body.querySelector(selector);
const qa = (selector: string) => Array.from(document.body.querySelectorAll(selector));
const where = () => screen.getByTestId("where").textContent;

function noVocabularyViolations(page: string) {
  const main = document.body.querySelector("main") as HTMLElement;
  const { violations, scanned } = scanProductVocabulary(main, page);
  expect(scanned).toBeGreaterThan(10);
  expect(violations, describeViolations(violations)).toEqual([]);
}

function atWidth(width: number) {
  Object.defineProperty(window, "innerWidth", { configurable: true, value: width });
  window.dispatchEvent(new Event("resize"));
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  atWidth(1024);
});

/** The Action and its events: the recorded resolved Action read, beside the S6-01 events read. */
function actionReads(query = "") {
  const action = prep(R.action_resolved);
  action.action.id = ACTION;
  action.selection.cutoff_recorded_at = CUTOFF;
  return {
    [`${API}${query}`]: ok(action),
    [`${API}/events${query}`]: ok(AM["action-history:1#a"].events_latest.body),
  };
}

const history = () => {
  const h = prep(R.history);
  h.outcomes[0].outcome_id = OUT1;
  h.outcomes[1].outcome_id = OUT2;
  h.outcomes[1].supersedes_outcome_id = OUT1;
  h.resolution_events[0].verification_outcome_id = OUT1;
  h.resolution_events[1].verification_outcome_id = OUT1;
  return h;
};

const outcomeCurrent = () => {
  const o = prep(R.outcome_current, { outcome_id: OUT1 });
  o.current_state.outcome_id = OUT1;
  return o;
};

/** Derived (1): the recorded current outcome read with the evaluator's typed outcome, reasons and metrics changed. */
function outcomeAs(outcome: string, reasons: string[], fail: Record<string, [string, string]> = {}) {
  const o = outcomeCurrent();
  o.outcome.outcome = outcome;
  o.outcome.reasons = reasons;
  o.current_state.state = outcome;
  o.current_state.last_outcome = outcome;
  o.current_state.reasons = reasons;
  for (const m of o.metrics) {
    if (fail[m.metric_key]) {
      m.state = "FAIL";
      [m.value_text, m.threshold_text] = fail[m.metric_key];
    }
    if (outcome === "INCONCLUSIVE" && m.metric_key === "below_reserve_seconds") m.state = "UNKNOWN";
  }
  return o;
}

describe("Verification view (verification:1-3)", () => {
  it("defaults to the latest current state: a current VERIFIED outcome with target and limits, policy-trial label and withdrawable resolution", async () => {
    serve({ ...actionReads(), [`${V}/history`]: ok(history()), [`${V}/outcome`]: ok(outcomeCurrent()) });
    mount(`/sites/KOBO-001/actions/${ACTION}/verification`);
    await settledScreen();
    expect(q("[data-verification-current-state]")).toHaveAttribute("data-verification-current-state", "VERIFIED");
    expect(q("[data-verification-historical]")).toBeNull();
    const headline = q("[data-verification-outcome]");
    expect(headline).toHaveAttribute("data-verification-outcome", "VERIFIED");
    expect(headline).toHaveAttribute("data-verification-historical-outcome", "no");
    expect(headline?.textContent).toContain("Target met within every limit");
    expect(q("[data-verification-row='target_reduction']")?.textContent).toMatch(/45 min.*0 min.*At least 25% lower.*Pass/);
    expect(q("[data-verification-row='below_reserve_seconds']")?.textContent).toContain("checked every five minutes");
    expect(q("[data-verification-row='source_provenance']")?.textContent).toContain("Authored test data (test-scoped example)");
    expect(q("[data-verification-trial-label]")?.textContent).toMatch(/Policy trial.*no savings or realized benefit.*never permanent/);
    expect(q("[data-verification-resolution-kind='RESOLVED']")).not.toBeNull();
    expect(q("[data-verification-resolution-kind='RESOLUTION_WITHDRAWN']")).not.toBeNull();
    expect(q("[data-verification-resolved-withdrawable]")?.textContent).toMatch(/not permanent/);
    // Typed values only in Dig deeper; the default reading has no enum.
    expect(q("[data-disclosure='verification-outcome'] [data-verification-typed-outcome]")?.textContent).toBe("VERIFIED");
    expect(q("[data-verification-outcome]")?.textContent).not.toMatch(/VERIFIED|TARGET_AND_GUARDRAILS_PASS/);
    expect(document.body.textContent).not.toMatch(/saved|savings of|reduced cost/i);
    noVocabularyViolations("verification:1-3");
  });

  it("REASSESSMENT_PENDING is the current read state; the withdrawn outcome is only an explicit Historical link", async () => {
    const o = prep(R.outcome_reassessment_pending, { outcome_id: OUT1 });
    serve({ ...actionReads(), [`${V}/history`]: ok(history()), [`${V}/outcome`]: ok(o), [`${V}/outcome?outcome_id=${OUT2}`]: ok(prep(R.outcome_historical, { outcome_id: OUT2 })) });
    mount(`/sites/KOBO-001/actions/${ACTION}/verification`);
    await settledScreen();
    expect(q("[data-verification-current-state]")).toHaveAttribute("data-verification-current-state", "REASSESSMENT_PENDING");
    expect(q("[data-verification-state-label]")?.textContent).toBe("Being reassessed");
    expect(q("[data-verification-outcome]")).toBeNull();
    expect(q("[data-verification-no-current-outcome]")).toHaveAttribute("data-verification-no-current-outcome", "REASSESSMENT_PENDING");
    const prior = q("[data-verification-prior-outcome-link]") as HTMLAnchorElement;
    expect(prior).toHaveAttribute("href", `/sites/KOBO-001/actions/${ACTION}/verification?outcome_id=${OUT2}`);
    noVocabularyViolations("verification:reassessment");
  });

  it("an explicit historical VERIFIED is labelled Historical beside a separate current state, and is not shown as current", async () => {
    const o = prep(R.outcome_historical, { outcome_id: OUT1 });
    o.superseded_by_outcome_id = OUT2;
    serve({ ...actionReads(), [`${V}/history`]: ok(history()), [`${V}/outcome?outcome_id=${OUT1}`]: ok(o) });
    mount(`/sites/KOBO-001/actions/${ACTION}/verification?outcome_id=${OUT1}`);
    await settledScreen();
    expect(q("[data-verification-historical]")?.textContent).toMatch(/^Historical/);
    expect(q("[data-verification-current-state]")).toHaveAttribute("data-verification-current-state", "INCONCLUSIVE");
    expect(q("[data-verification-state-label]")?.textContent).toBe("Could not conclude");
    expect(q("[data-verification-outcome]")).toHaveAttribute("data-verification-outcome", "VERIFIED");
    expect(q("[data-verification-outcome]")).toHaveAttribute("data-verification-historical-outcome", "yes");
    expect(q("[data-verification-superseded-by]")).toHaveAttribute("data-verification-superseded-by", OUT2);
    // The selection survives every section link.
    for (const section of ["plan", "evidence", "verification", "history"]) {
      const link = q(`[data-action-section='${section}']`);
      expect(link?.getAttribute("href")).toContain(`outcome_id=${OUT1}`);
    }
  });

  it("shows the three interim labels with typed outcomes; GUARDRAIL_FAIL is a reason with metric, value, threshold, unit and evidence", async () => {
    const cases: [Body, string, string][] = [
      [outcomeAs("INEFFECTIVE", ["GUARDRAIL_FAIL", "GUARDRAIL:below_reserve_seconds"], { below_reserve_seconds: ["600", "0 and <= baseline"] }), "Trial missed a safety or service limit", "INEFFECTIVE"],
      [outcomeAs("INEFFECTIVE", ["TARGET_MISS"], { target_reduction: [null as unknown as string, "4 * later_seconds <= 3 * baseline_seconds"] }), "Target not met", "INEFFECTIVE"],
      [outcomeAs("INCONCLUSIVE", ["GUARDRAIL_UNKNOWN:below_reserve_seconds", "INCOMPLETE_LATER_WINDOW", "KNOWN_FAILURE:target_reduction"]), "Could not conclude", "INCONCLUSIVE"],
    ];
    for (const [body, label, typed] of cases) {
      serve({ ...actionReads(), [`${V}/history`]: ok(history()), [`${V}/outcome`]: ok(body) });
      mount(`/sites/KOBO-001/actions/${ACTION}/verification`);
      await settledScreen();
      const headline = q("[data-verification-outcome]");
      expect(headline).toHaveAttribute("data-verification-outcome", typed);
      expect(headline).toHaveAttribute("data-verification-label", label);
      expect(q("[data-verification-typed-outcome]")?.textContent).toBe(typed);
      if (label === "Trial missed a safety or service limit") {
        const failed = q("[data-verification-failed-metric='below_reserve_seconds']");
        expect(failed?.textContent).toMatch(/Time below the reserve.*600.*s.*0 and <= baseline/);
        expect(Number(failed?.querySelector("[data-verification-evidence-count]")?.getAttribute("data-verification-evidence-count"))).toBeGreaterThan(0);
        expect(qa("[data-verification-outcome]").map((e) => e.getAttribute("data-verification-outcome"))).not.toContain("GUARDRAIL_FAIL");
      }
      if (label === "Could not conclude") {
        expect(q("[data-verification-unknown-reasons]")?.textContent).toContain("The later window is missing required readings.");
        expect(q("[data-verification-known-failures]")?.textContent).toContain("Known failure");
      }
      noVocabularyViolations(`verification:${label}`);
      cleanup();
      vi.unstubAllGlobals();
    }
  });

  it("conflicting selectors are a typed error with no read and no silent preference", async () => {
    const s = serve({ ...actionReads(`?recorded_at=${encodeURIComponent(CUTOFF)}`) });
    mount(`/sites/KOBO-001/actions/${ACTION}/verification?recorded_at=${encodeURIComponent(CUTOFF)}&outcome_id=${OUT1}`);
    await settledScreen();
    expect(q("[data-verification-selector-conflict]")).toHaveAttribute("data-verification-selector-conflict", "VERIFICATION_SELECTOR_CONFLICT");
    expect(s.requests.some((r) => r.includes("/verification/"))).toBe(false);
    cleanup();
    vi.unstubAllGlobals();
    // A plan and an outcome of another plan.
    serve({ ...actionReads(), [`${V}/outcome?outcome_id=${OUT1}`]: ok(prep(R.outcome_historical, { outcome_id: OUT1 })) });
    mount(`/sites/KOBO-001/actions/${ACTION}/plan?plan_revision_id=${PLAN2}&outcome_id=${OUT1}`);
    await settledScreen();
    expect(q("[data-verification-selector-conflict]")).not.toBeNull();
    expect(q("[data-verification-plan-id]")).toBeNull();
  });

  it("a recorded cutoff is historical across child links and a reload", async () => {
    const at = encodeURIComponent(CUTOFF);
    const reads = {
      ...actionReads(`?recorded_at=${at}`),
      [`${V}/history`]: ok(history()),
      [`${V}/outcome?recorded_at=${at}`]: ok(prep(R.outcome_historical, { outcome_id: OUT1 })),
      [`${V}/plan?recorded_at=${at}`]: ok(prep(R.plan)),
    };
    serve(reads);
    const { unmount } = mount(`/sites/KOBO-001/actions/${ACTION}/verification?recorded_at=${at}`);
    await settledScreen();
    expect(q("[data-verification-historical]")?.textContent).toContain("recorded through");
    fireEvent.click(q("[data-action-section='plan']") as HTMLAnchorElement);
    await settledScreen();
    expect(where()).toBe(`/sites/KOBO-001/actions/${ACTION}/plan?recorded_at=${at}`);
    expect(q("[data-verification-plan-id]")).toHaveAttribute("data-verification-plan-id", PLAN);
    unmount();
    // Reload: the same address reads the same selection.
    mount(`/sites/KOBO-001/actions/${ACTION}/plan?recorded_at=${at}`);
    await settledScreen();
    expect(where()).toBe(`/sites/KOBO-001/actions/${ACTION}/plan?recorded_at=${at}`);
    expect(q("[data-verification-historical]")).not.toBeNull();
  });
});

describe("Plan view (action-plan:1)", () => {
  it("shows frozen criteria, half-open windows, day selections, applied change and new-reserve classification", async () => {
    serve({ ...actionReads(), [`${V}/plan`]: ok(prep(R.plan)) });
    mount(`/sites/KOBO-001/actions/${ACTION}/plan`);
    await settledScreen();
    expect(q("[data-verification-plan-id]")).toHaveAttribute("data-verification-plan-current", "yes");
    expect(q("[data-verification-criterion='target']")?.textContent).toMatch(/At least 25% lower.*times 4.*times 3.*whole seconds.*45 min/);
    expect(q("[data-verification-criterion='comparability']")?.textContent).toMatch(/within 10%.*within 2 points.*inclusive/);
    expect(q("[data-verification-window='baseline']")?.textContent).toContain("2026-10-06");
    expect(q("[data-verification-window='later']")).toHaveAttribute("data-verification-later-bound", "yes");
    expect(document.body.textContent).toMatch(/new, lower reserve/);
    expect(document.body.textContent).toMatch(/not proof of cause/);
    expect(q("[data-verification-plan-change-link]")).toHaveAttribute("href", `/sites/KOBO-001/foundation/changes/${CHANGE}`);
    expect(q("[data-verification-plan-version]")?.textContent).toBe("reserve-trial-verification-1");
    noVocabularyViolations("action-plan:1");
  });

  it("before the later selection is appended the later window is pending with the missing day; before a plan, says why", async () => {
    const plan = prep(R.plan);
    plan.selection_bindings = []; // Derived (2)
    serve({ ...actionReads(), [`${V}/plan`]: ok(plan) });
    mount(`/sites/KOBO-001/actions/${ACTION}/plan`);
    await settledScreen();
    expect(q("[data-verification-later-pending]")?.textContent).toContain("2026-11-02");
    cleanup();
    vi.unstubAllGlobals();
    const none = prep(R.plan);
    none.plan = null; // Derived (2)
    none.verification_state = { state: "NO_PLAN", reasons: [], plan_id: null, outcome_id: null, statement: "" };
    serve({ ...actionReads(), [`${V}/plan`]: ok(none) });
    mount(`/sites/KOBO-001/actions/${ACTION}/plan`);
    await settledScreen();
    expect(q("[data-verification-plan='none']")?.textContent).toMatch(/No verification plan exists/);
    expect(q("[data-verification-state-label]")?.textContent).toBe("No verification plan yet");
  });
});

describe("Evidence view (action-evidence:1)", () => {
  it("shows both windows' twelve five-minute slots, sampled reserve, source per window and comparability", async () => {
    serve({ ...actionReads(), [`${V}/evidence`]: ok(prep(R.evidence)), [`${V}/plan?plan_id=${PLAN}`]: ok(prep(R.plan)) });
    mount(`/sites/KOBO-001/actions/${ACTION}/evidence`);
    await settledScreen();
    for (const name of ["baseline", "later"]) {
      const win = q(`[data-verification-evidence-window='${name}']`);
      expect(win).toHaveAttribute("data-verification-window-complete", "yes");
      expect(win?.querySelectorAll("[data-verification-slot]").length).toBe(12);
      expect(win?.querySelector("[data-verification-window-source]")?.textContent).toBe("Authored test data (test-scoped example)");
    }
    expect(q("[data-verification-comparability='feeder_demand_energy']")).toHaveAttribute("data-verification-comparability-state", "PASS");
    expect(document.body.textContent).toMatch(/five-minute sample, not continuous/);
    expect(q("[data-verification-requirement='target']")?.textContent).toMatch(/45 min to 0 min/);
    noVocabularyViolations("action-evidence:1");
  });

  it("names a gap explicitly and, for an exact outcome, reads the evidence as known when it was recorded", async () => {
    const ev = prep(R.evidence);
    const slot = ev.windows.later.slots[3]; // Derived (3)
    const load = Object.keys(slot.feeder_demand)[0];
    slot.feeder_demand[load] = { ...slot.feeder_demand[load], state: "MISSING", kwh: null, evidence_ids: [], problems: [{ code: "GAP", detail: "no interval reading covers the slot" }] };
    slot.complete = false;
    ev.windows.later.complete = false;
    const o = prep(R.outcome_historical, { outcome_id: OUT1 });
    serve({
      ...actionReads(),
      [`${V}/outcome?outcome_id=${OUT1}`]: ok(o),
      [`${V}/evidence?recorded_at=${o.outcome.recorded_at}`]: ok(ev),
      [`${V}/history`]: ok(history()),
      [`${V}/plan?plan_id=${PLAN}`]: ok(prep(R.plan)),
    });
    mount(`/sites/KOBO-001/actions/${ACTION}/evidence?outcome_id=${OUT1}`);
    await settledScreen();
    expect(q("[data-verification-evidence-window='later']")).toHaveAttribute("data-verification-window-complete", "no");
    expect(q("[data-verification-problem='GAP']")?.textContent).toMatch(/^Gap/);
    expect(q("[data-verification-requirement='later']")).toHaveAttribute("data-verification-requirement-ok", "no");
    expect(q("[data-verification-knowledge-cutoff]")?.textContent).toContain("when the selected outcome was recorded");
    expect(q("[data-verification-historical]")).not.toBeNull();
  });

  it("keeps the same structure at 1440 and 390 (layout is browser evidence)", async () => {
    for (const width of [1440, 390]) {
      atWidth(width);
      serve({ ...actionReads(), [`${V}/evidence`]: ok(prep(R.evidence)), [`${V}/plan?plan_id=${PLAN}`]: ok(prep(R.plan)) });
      mount(`/sites/KOBO-001/actions/${ACTION}/evidence`);
      await settledScreen();
      expect(qa("[data-verification-slot]").length).toBe(24);
      expect(q(".data-table__scroll")).not.toBeNull();
      cleanup();
      vi.unstubAllGlobals();
    }
  });
});

describe("Historical views beside the actual current state, and window lineage (S6-02b fix round 1)", () => {
  const at = encodeURIComponent(CUTOFF);
  const withdrawn = () => {
    const h = history();
    h.current_state = { ...h.current_state, state: "INCONCLUSIVE", reasons: [], outcome_id: OUT1 };
    return h;
  };

  it("F1: an evidence view selected by cutoff shows the actual current state beside the historical VERIFIED", async () => {
    const ev = prep(R.evidence);
    ev.verification_state = { ...ev.verification_state, state: "VERIFIED", reasons: [], historical: true };
    serve({
      ...actionReads(`?recorded_at=${at}`),
      [`${V}/evidence?recorded_at=${at}`]: ok(ev),
      [`${V}/plan?plan_id=${PLAN}`]: ok(prep(R.plan)),
      [`${V}/history`]: ok(withdrawn()),
    });
    mount(`/sites/KOBO-001/actions/${ACTION}/evidence?recorded_at=${at}`);
    await settledScreen();
    expect(q("[data-verification-current-state]")).toHaveAttribute("data-verification-current-state", "VERIFIED");
    expect(document.body.textContent).toContain("State at the selected time");
    expect(q("[data-verification-actual-current]")).toHaveAttribute("data-verification-actual-current", "INCONCLUSIVE");
    expect(q("[data-verification-actual-state-label]")?.textContent).toBe("Could not conclude");
    expect(q("[data-verification-historical]")?.textContent).toContain("actual current state is shown below");
  });

  it("F1: a plan view selected by cutoff does the same; an unreadable current state is stated, never implied", async () => {
    const plan = prep(R.plan);
    plan.verification_state = { ...plan.verification_state, state: "VERIFIED", reasons: [], historical: true };
    serve({ ...actionReads(`?recorded_at=${at}`), [`${V}/plan?recorded_at=${at}`]: ok(plan), [`${V}/history`]: ok(withdrawn()) });
    mount(`/sites/KOBO-001/actions/${ACTION}/plan?recorded_at=${at}`);
    await settledScreen();
    expect(q("[data-verification-actual-current]")).toHaveAttribute("data-verification-actual-current", "INCONCLUSIVE");
    cleanup();
    serve({ ...actionReads(`?recorded_at=${at}`), [`${V}/plan?recorded_at=${at}`]: ok(plan) });
    mount(`/sites/KOBO-001/actions/${ACTION}/plan?recorded_at=${at}`);
    await settledScreen();
    await vi.waitFor(() => expect(q("[data-verification-actual-current-unavailable]")).not.toBeNull());
    expect(q("[data-verification-actual-current]")).toBeNull();
    expect(q("[data-verification-historical]")?.textContent).toContain("could not be read");
  });

  it("F5: an unrecognised source state is never read as field readings", async () => {
    const { sourceWords } = await import("../verificationWords");
    expect(sourceWords("SOMETHING_NEW")).toMatch(/not recognised/);
    expect(sourceWords("SOMETHING_NEW")).not.toMatch(/Field readings/);
    expect(sourceWords("MIXED")).toBe("Mixed sources");
  });

  it("F3: the evidence view gives a plain lineage summary and the exact IDs in Dig deeper", async () => {
    const ev = prep(R.evidence);
    serve({ ...actionReads(), [`${V}/evidence`]: ok(ev), [`${V}/plan?plan_id=${PLAN}`]: ok(prep(R.plan)) });
    mount(`/sites/KOBO-001/actions/${ACTION}/evidence`);
    await settledScreen();
    await vi.waitFor(() => expect(q("[data-verification-origin-finding-revision]")).not.toBeNull());
    const plan = prep(R.plan).plan;
    for (const name of ["baseline", "later"]) {
      expect(q(`[data-verification-lineage-summary='${name}']`)?.textContent).toMatch(/assessed days? selected/);
    }
    expect(q("[data-verification-origin-finding-revision]")?.textContent).toBe(plan.origin_finding_revision_id);
    expect(qa("[data-verification-assessment-revision]").length).toBe(
      ev.target.baseline.assessment_revision_ids.length + (ev.target.later.assessment_revision_ids ?? []).length,
    );
    expect(qa("[data-verification-lineage-day]").length).toBeGreaterThan(0);
    const win = q("[data-verification-evidence-window='baseline']");
    expect(win?.querySelector("[data-verification-lineage-day]")?.textContent).toMatch(/SELECTED_UNIQUE/);
    noVocabularyViolations("action-evidence:lineage");
  });

  it("W1-UX-06: source reasons sent as objects ({code, accepted_evidence_ids}) render their exact code, not a crash", async () => {
    // Found by the final served capture (s602b inconclusive case): the Evidence page went blank on these objects.
    const ev = prep(R.evidence);
    ev.source_resolution.later = {
      ...ev.source_resolution.later,
      state: "UNKNOWN",
      reasons: [{ code: "SOURCE_NOT_ESTABLISHED", accepted_evidence_ids: ["ev-1"] }, "PLAIN_CODE"],
    };
    serve({ ...actionReads(), [`${V}/evidence`]: ok(ev), [`${V}/plan?plan_id=${PLAN}`]: ok(prep(R.plan)) });
    mount(`/sites/KOBO-001/actions/${ACTION}/evidence`);
    await settledScreen();
    await vi.waitFor(() => expect(q("[data-verification-evidence-window='later']")).not.toBeNull());
    expect(qa("[data-verification-source-reason]").map((e) => e.textContent)).toEqual(["SOURCE_NOT_ESTABLISHED", "PLAIN_CODE"]);
    // Review L4: each reason also reads in plain words beside its code.
    expect(qa("[data-verification-source-reason-words]").map((e) => e.textContent)).toEqual([sourceReasonWords("SOURCE_NOT_ESTABLISHED"), sourceReasonWords("PLAIN_CODE")]);
  });
});

describe("Recommendation and Change panels (recommendation:2-3, changes:1#b, changes:2)", () => {
  it("an accepted recommendation links the frozen plan and keeps the accepted snapshot", async () => {
    const c = AM["recommendation:1#a"].accepted_snapshot_live_status;
    const body = structuredClone(c.body); // Derived (4)
    const actionId = body.accepted[0].action_id as string;
    body.verification = { [actionId]: { state: "VERIFIED", reasons: ["TARGET_AND_GUARDRAILS_PASS"], plan_id: PLAN, outcome_id: OUT1, statement: "" } };
    const path = new URL(`http://x${c.request.path}`);
    serve({ [`${path.pathname}${path.search}`]: ok(body) });
    mount(`/sites/KOBO-001/findings/${body.finding_id}/recommendation?revision_id=${body.revision_id}`);
    await settledScreen();
    expect(q("[data-recommendation-accepted]")).not.toBeNull();
    expect(q("[data-recommendation-plan-link] a")).toHaveAttribute("href", `/sites/KOBO-001/actions/${actionId}/plan?plan_revision_id=${PLAN}`);
    expect(q("[data-trial-verification-state]")).toHaveAttribute("data-trial-verification-state", "VERIFIED");
    expect(q("[data-recommendation-verification-link]")).toHaveAttribute("href", `/sites/KOBO-001/actions/${actionId}/verification`);
    noVocabularyViolations("recommendation:2-3");
  });

  it("a different-Finding overlap hold shows its typed block and links the Action and the withdrawn outcome", async () => {
    const body = prep(R.recommendation_overlap); // Derived (5)
    body.prior_action_block.blocking_actions[0].origin.finding_id = OTHER_FINDING;
    body.prior_action_block.overlaps[0].withdrawn_outcome_id = OUT1;
    body.prior_action_block.overlaps[0].closure_action_id = ACTION;
    body.prior_action_block.blocking_action_id = ACTION;
    body.prior_action_block.blocking_actions[0].action_id = ACTION;
    serve({ [`/api/sites/KOBO-001/findings/${FINDING}/recommendation?revision_id=${body.revision_id}`]: ok(body) });
    mount(`/sites/KOBO-001/findings/${FINDING}/recommendation?revision_id=${body.revision_id}`);
    await settledScreen();
    expect(q("[data-recommendation-state]")).toHaveAttribute("data-recommendation-state", "PRIOR_TRIAL_REASSESSMENT_OVERLAP");
    expect(q("[data-recommendation-prior-block-code]")).toHaveAttribute("data-recommendation-prior-block-code", "PRIOR_TRIAL_REASSESSMENT_OVERLAP");
    expect(q("[data-recommendation-prior-block-other-finding]")).toHaveAttribute("data-recommendation-prior-block-other-finding", OTHER_FINDING);
    expect(q("[data-recommendation-prior-block-withdrawn]")).toHaveAttribute("href", `/sites/KOBO-001/actions/${ACTION}/verification?outcome_id=${OUT1}`);
    expect(q("[data-recommendation-prior-block-link]")).toHaveAttribute("href", `/sites/KOBO-001/actions/${ACTION}`);
    expect(q("[data-action-command-held]")).toHaveAttribute("data-action-command-held", "PRIOR_TRIAL_REASSESSMENT_OVERLAP");
    expect(screen.getByRole("button", { name: /Accept trial/ })).toBeDisabled();
    noVocabularyViolations("recommendation:hold");
  });

  it("the change page shows the later effect from the verification block, never APPLIED as success", async () => {
    const c = AM["changes:1#a"].change;
    const body = structuredClone(c.body); // Derived (4)
    body.verification = { state: "REASSESSMENT_PENDING", reasons: ["FOUNDATION_CHANGED"], plan_id: PLAN, outcome_id: OUT1, statement: "" };
    serve({
      [c.request.path]: ok(body),
      [`/api/sites/KOBO-001/actions/${body.change.action_id}/events`]: ok(AM["action-history:1#a"].events_latest.body),
    });
    mount(c.request.path.replace("/api", ""));
    await settledScreen();
    expect(q("[data-trial-verification-state]")).toHaveAttribute("data-trial-verification-state", "REASSESSMENT_PENDING");
    expect(q("[data-change-outcome-link]")).toHaveAttribute("href", `/sites/KOBO-001/actions/${body.change.action_id}/verification?outcome_id=${OUT1}`);
    expect(q("[data-change-plan-link]")).toHaveAttribute("href", `/sites/KOBO-001/actions/${body.change.action_id}/plan?plan_revision_id=${PLAN}`);
    expect(q("[data-change-decision-path]")?.querySelectorAll("li").length).toBe(3);
    expect(document.body.textContent).toMatch(/being applied is not success/);
    noVocabularyViolations("changes:1#b-2");
  });
});

describe("W1-UX-04 phase 2 / W1-F4: Verification, Plan and Evidence state lines (cards folded into the v69 strip and panels)", () => {

  // W1-F4: the W1-UX-04 answer cards of the Verification, Plan and Evidence views are gone. Their state line
  // now leads the v69 status strip, and their failed limits, known failures and gaps sit in the owning panel.
  // Each guarantee below is the card test's guarantee, asserted where the content now lives.
  function w1View(page: string): HTMLElement {
    const main = document.body.querySelector("main") as HTMLElement;
    const w1 = scanProductVocabulary(main, page, { set: "w1" });
    expect(w1.scanned).toBeGreaterThan(10);
    expect(w1.violations, describeViolations(w1.violations)).toEqual([]);
    expect(q("[data-headline-card]"), "no leading answer card").toBeNull();
    const strip = q(".w1f4-verification-strip") as HTMLElement;
    expect(strip, `${page} status strip`).not.toBeNull();
    const disclosure = scanDisclosureVocabulary(strip, `${page} disclosure`);
    expect(disclosure.disclosures).toBe(1);
    expect(disclosure.violations, describeViolations(disclosure.violations)).toEqual([]);
    return q(".site-verification") as HTMLElement;
  }
  const stripTone = () => q(".w1f4-verification-strip")?.getAttribute("data-product-status");
  const visible = (selector: string, within: Element) => {
    const el = within.querySelector(selector);
    expect(el, selector).not.toBeNull();
    expect(visibleOutsideClosedDisclosure(el!), `${selector} is outside the closed disclosure`).toBe(true);
    return el as HTMLElement;
  };

  it("current VERIFIED: the outcome, scope and as-of lead the strip outside the closed disclosure; the metric cards come from the read", async () => {
    serve({ ...actionReads(), [`${V}/history`]: ok(history()), [`${V}/outcome`]: ok(outcomeCurrent()) });
    mount(`/sites/KOBO-001/actions/${ACTION}/verification`);
    await settledScreen();
    const view = w1View("verification (W1) verified");
    const label = expectStateLineVisible(view);
    expect(label).not.toMatch(/historical|earlier/i);
    expect(visible("[data-product-outcome-source]", view).textContent).toMatch(/^Source: .+/);
    expect(q("[data-verification-card='target']")?.textContent).toMatch(/45 min → 0 min/);
    expect(view.textContent).not.toMatch(/saved|savings of|reduced cost/i);
  });

  it("guardrail miss and target miss stay prominent with measured value, limit and unit; INCONCLUSIVE keeps known failures", async () => {
    const inconclusive = outcomeAs("INCONCLUSIVE", ["GUARDRAIL_UNKNOWN:terminal_soc", "INCOMPLETE_LATER_WINDOW", "KNOWN_FAILURE:below_reserve_seconds"]);
    for (const m of inconclusive.metrics) {
      if (m.metric_key === "below_reserve_seconds") {
        m.state = "FAIL";
        m.value_text = "3600";
        m.threshold_text = "0 and <= baseline";
      }
    }
    const cases: [Body, RegExp][] = [
      [outcomeAs("INEFFECTIVE", ["GUARDRAIL_FAIL", "GUARDRAIL:below_reserve_seconds"], { below_reserve_seconds: ["600", "0 and <= baseline"] }), /safety or service limit/],
      [outcomeAs("INEFFECTIVE", ["TARGET_MISS"], { target_reduction: [null as unknown as string, "4 * later_seconds <= 3 * baseline_seconds"] }), /Target not met/],
      [inconclusive, /./],
    ];
    for (const [body, label] of cases) {
      serve({ ...actionReads(), [`${V}/history`]: ok(history()), [`${V}/outcome`]: ok(body) });
      const view = mount(`/sites/KOBO-001/actions/${ACTION}/verification`);
      await settledScreen();
      const scope = w1View(`verification (W1) ${body.outcome.outcome} ${body.outcome.reasons[0]}`);
      expect(expectStateLineVisible(scope)).toMatch(label);
      expect(stripTone()).not.toBe("positive");
      const panel = panelTitled("Target and guardrails evaluated together");
      if (body.outcome.reasons.includes("GUARDRAIL_FAIL")) {
        // The failed limit is in the default reading of panel 1, outside the closed disclosure.
        // 600 seconds read, shown in plain minutes against its limit.
        expect(visible("[data-product-outcome-failed-limits]", panel).textContent).toContain("measured 10 min, limit 0 min");
      }
      if (body.outcome.outcome === "INCONCLUSIVE") {
        expect(q(".w1f4-verification-strip")?.textContent).toMatch(/cannot tell|could not conclude/i);
        const known = visible("[data-product-outcome-known-failures]", panel);
        expect(known.textContent).toMatch(/^Known failure: /);
        expect(known.textContent).not.toMatch(/Known failure: Known failure/);
        expect(known.textContent).toMatch(/reserve/i);
        expect(visible("[data-product-outcome-failed-limits]", panel).textContent).toContain("measured 60 min, limit 0 min");
      }
      view.unmount();
      vi.unstubAllGlobals();
    }
  });

  it("REASSESSMENT_PENDING: no current result is claimed; a selected withdrawn outcome is Historical beside the current state", async () => {
    const o = prep(R.outcome_reassessment_pending, { outcome_id: OUT1 });
    serve({ ...actionReads(), [`${V}/history`]: ok(history()), [`${V}/outcome`]: ok(o), [`${V}/outcome?outcome_id=${OUT2}`]: ok(prep(R.outcome_historical, { outcome_id: OUT2 })) });
    let view = mount(`/sites/KOBO-001/actions/${ACTION}/verification`);
    await settledScreen();
    let scope = w1View("verification (W1) reassessment");
    expect(expectStateLineVisible(scope)).not.toMatch(/verified|met/i);
    expect(stripTone()).not.toBe("positive");
    // No measured value from the withdrawn outcome: every card is a gap word.
    expect(q("[data-verification-cards]")).toHaveAttribute("data-verification-cards", "gap");
    for (const card of qa("[data-verification-card]")) expect(card.textContent).toMatch(/Pending/);
    view.unmount();

    view = mount(`/sites/KOBO-001/actions/${ACTION}/verification?outcome_id=${OUT2}`);
    await settledScreen();
    scope = w1View("verification (W1) historical");
    const shown = expectStateLineVisible(scope);
    expect(shown).not.toMatch(/current/i);
    expect(stripTone()).not.toBe("positive");
    expect(visible("[data-verification-historical]", scope).textContent).toMatch(/^Historical/);
    expect(visible("[data-verification-state-label]", scope).textContent).not.toBe("");
    expect(visible("[data-product-outcome-source]", scope).textContent).toMatch(/^Source: .+/);
    expect(visible("[data-product-outcome-demonstration]", scope).textContent).toMatch(/policy|no saving|not a saving/i);
    expect(panelTitled("Target and guardrails evaluated together").querySelector("[data-verification-outcome]")).toHaveAttribute("data-verification-historical-outcome", "yes");
    expect(where()).toContain(`outcome_id=${OUT2}`);
    view.unmount();
  });

  it("Plan: a fixed plan and NO_PLAN each keep the state line, scope and as-of outside the closed disclosure", async () => {
    serve({ ...actionReads(), [`${V}/plan`]: ok(prep(R.plan)) });
    let view = mount(`/sites/KOBO-001/actions/${ACTION}/plan`);
    await settledScreen();
    let scope = w1View("action-plan (W1)");
    expect(expectStateLineVisible(scope)).toBe("Plan fixed before the later readings");
    const panel = panelTitled("Success criteria");
    expect(panel.querySelectorAll("[data-verification-window]")).toHaveLength(2);
    expect(panel.textContent).toMatch(/25% lower/);
    view.unmount();
    vi.unstubAllGlobals();

    const none = prep(R.plan);
    none.plan = null;
    none.verification_state = { state: "NO_PLAN", reasons: [], plan_id: null, outcome_id: null, statement: "" };
    serve({ ...actionReads(), [`${V}/plan`]: ok(none) });
    view = mount(`/sites/KOBO-001/actions/${ACTION}/plan`);
    await settledScreen();
    scope = w1View("action-plan (W1) no plan");
    expect(expectStateLineVisible(scope)).not.toBe("");
    expect(stripTone()).not.toBe("positive");
    expect(q("[data-verification-window]")).toBeNull();
    expect(panelTitled("Success criteria").querySelector("[data-panel-gap]")?.textContent).toMatch(/^No success criteria recorded\./);
    view.unmount();
  });

  it("Evidence: complete windows, then a gap that reads as missing readings, never as complete", async () => {
    serve({ ...actionReads(), [`${V}/evidence`]: ok(prep(R.evidence)), [`${V}/plan?plan_id=${PLAN}`]: ok(prep(R.plan)) });
    let view = mount(`/sites/KOBO-001/actions/${ACTION}/evidence`);
    await settledScreen();
    let scope = w1View("action-evidence (W1)");
    expect(expectStateLineVisible(scope)).toBe("Both windows have their readings");
    expect(visible("[data-verification-requirement='later']", scope).textContent).toMatch(/12\/12 slots complete/);
    view.unmount();
    vi.unstubAllGlobals();

    const ev = prep(R.evidence);
    const slot = ev.windows.later.slots[3];
    const load = Object.keys(slot.feeder_demand)[0];
    slot.feeder_demand[load] = { ...slot.feeder_demand[load], state: "MISSING", kwh: null, evidence_ids: [], problems: [{ code: "GAP", detail: "no interval reading covers the slot" }] };
    slot.complete = false;
    ev.windows.later.complete = false;
    serve({ ...actionReads(), [`${V}/evidence`]: ok(ev), [`${V}/plan?plan_id=${PLAN}`]: ok(prep(R.plan)) });
    view = mount(`/sites/KOBO-001/actions/${ACTION}/evidence`);
    await settledScreen();
    scope = w1View("action-evidence (W1) gap");
    expect(expectStateLineVisible(scope)).toBe("Some readings are missing");
    expect(stripTone()).not.toBe("positive");
    const later = visible("[data-verification-requirement='later']", scope);
    expect(later.textContent).toMatch(/11\/12 slots complete/);
    expect(later).toHaveAttribute("data-verification-requirement-ok", "no");
    // The gap itself is in the panel's default reading, not only in the closed readings disclosure.
    expect(visible("[data-verification-window-problems='later'] [data-verification-problem='GAP']", scope).textContent).toMatch(/^Gap/);
    view.unmount();
  });

  it("Recommendation hold on a different Finding: the held state line keeps the blocking Action's latest recorded step as its as-of", async () => {
    const body = prep(R.recommendation_overlap);
    body.prior_action_block.blocking_actions[0].origin.finding_id = OTHER_FINDING;
    body.prior_action_block.blocking_action_id = ACTION;
    body.prior_action_block.blocking_actions[0].action_id = ACTION;
    serve({ [`/api/sites/KOBO-001/findings/${FINDING}/recommendation?revision_id=${body.revision_id}`]: ok(body) });
    mount(`/sites/KOBO-001/findings/${FINDING}/recommendation?revision_id=${body.revision_id}`);
    await settledScreen();
    // W1-F4: the former answer card is the v69 status strip; the same state line, tone, as-of and held link.
    const main = document.body.querySelector("main") as HTMLElement;
    const w1 = scanProductVocabulary(main, "recommendation (W1) overlap hold", { set: "w1" });
    expect(w1.scanned).toBeGreaterThan(10);
    expect(w1.violations, describeViolations(w1.violations)).toEqual([]);
    expect(q("[data-headline-card]")).toBeNull();
    const strip = q(".status-strip[data-product-status]") as HTMLElement;
    const disclosure = scanDisclosureVocabulary(strip, "recommendation (W1) overlap hold disclosure");
    expect(disclosure.disclosures).toBe(1);
    expect(disclosure.violations, describeViolations(disclosure.violations)).toEqual([]);
    expect(expectStateLineVisible(strip.parentElement as HTMLElement)).toBe("Held: late evidence withdrew an earlier trial's result");
    expect(strip.getAttribute("data-product-status")).toBe("problem");
    expect(strip.querySelector("[data-recommendation-card-held-link]")).toHaveAttribute("href", `/sites/KOBO-001/actions/${ACTION}`);
    expect(screen.getByRole("button", { name: /Accept trial/ })).toBeDisabled();
  });
});

/* W5-02 K2a (U2, P-K2a-45/46): the COLDCHAIN domain Action placeholder shell beside the unchanged W1 frame. */
const coldActionDetail = {
  getSite: async (siteId: string) => ({ status: "loaded", site: { ...COLD_SITE, site_id: siteId } }),
} as unknown as SiteDetailClient;

function coldDomain(result: DomainDetailResult = { status: "loaded", value: detailBody() }): DomainActionClient & { calls: string[] } {
  const calls: string[] = [];
  return {
    calls,
    getIndex: async () => ({ status: "loaded", value: indexBody([]) }),
    getDetail: async (_site: string, id: string) => {
      calls.push(id);
      return result;
    },
  };
}

async function mountColdAction(path: string, domain: DomainActionClient, site: SiteDetailClient = coldActionDetail) {
  render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        {["/sites/:siteId/actions/:actionId", "/sites/:siteId/actions/:actionId/:actionView"].map((p) => (
          <Route key={p} path={p} element={<SiteActionFrame detail={site} sitesPath="/sites" domainActions={domain} />} />
        ))}
      </Routes>
    </MemoryRouter>,
  );
  await settledScreen();
}

describe("W5-02 K2a: cold /verification dispatch", () => {
  it("a domain Action renders the domain panels, not the W1 verification read or its panels", async () => {
    const urls: string[] = [];
    vi.stubGlobal("fetch", async (url: string) => {
      urls.push(url);
      return new Response("{}", { status: 599 });
    });
    await mountColdAction(`/sites/${COLD_CODE}/actions/${DOMAIN_ID}/verification`, coldDomain());
    expect(screen.getByRole("heading", { level: 2, name: "Declared outcome criteria" })).toBeInTheDocument();
    expect(urls).toEqual([]);
    expect(document.body.textContent).not.toContain("Target and guardrails");
  });

  it("a mini-grid /verification never reads the domain Action", async () => {
    vi.stubGlobal("fetch", async () => new Response("{}", { status: 599 }));
    const domain = coldDomain();
    await mountColdAction(`/sites/KOBO-001/actions/${DOMAIN_ID}/verification`, domain, {
      getSite: async (siteId: string) => ({ status: "loaded", site: { ...HYBRID_MINI_GRID_SITE, site_id: siteId } }),
    } as unknown as SiteDetailClient);
    expect(domain.calls).toEqual([]);
    expect(document.querySelector("[data-domain-action-shell]")).toBeNull();
  });
});

/* W5-04 V4a (readiness rulings 15, 43): an EV_CHARGING /verification renders the EV plan, never the W1 verification. */
describe("W5-04 V4a: EV /verification dispatch", () => {
  const evActionDetail = {
    getSite: async (siteId: string) => ({ status: "loaded", site: { ...EV_SITE, site_id: siteId } }),
  } as unknown as SiteDetailClient;
  const pending = ["WITNESSED_SESSION", "NO_FAULT_RECURRENCE", "NO_SERVICE_REDUCTION"];
  const evBody = detailBody({
    action: { ...detailBody().action, domain: "EV_CHARGING" },
    intent: {
      ...(detailBody().intent as NonNullable<ReturnType<typeof detailBody>["intent"]>),
      criteria: pending.map((key) => ({ key, label: key, required_evidence: key })),
    },
    results: pending.map((key) => ({ key, result: "PENDING", evidence_ids: [] })),
  });

  it("an EV domain Action renders only the Declared verification plan with Pending results and no W1 verification read", async () => {
    const urls: string[] = [];
    vi.stubGlobal("fetch", async (url: string) => {
      urls.push(url);
      return new Response("{}", { status: 599 });
    });
    const domain = coldDomain({ status: "loaded", value: evBody });
    await mountColdAction(`/sites/${COLD_CODE}/actions/${DOMAIN_ID}/verification`, domain, evActionDetail);
    expect(domain.calls).toEqual([DOMAIN_ID]);
    expect(screen.getByRole("heading", { level: 2, name: "Declared verification plan" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { level: 2, name: "Declared outcome criteria" })).toBeNull();
    expect(screen.queryByRole("heading", { level: 2, name: "Related activity" })).toBeNull();
    expect(Array.from(document.querySelectorAll("[data-domain-action-result]")).map((c) => c.textContent)).toEqual(["Pending", "Pending", "Pending"]);
    expect(urls).toEqual([]);
    expect(document.body.textContent).not.toContain("Target and guardrails");
  });
});

// --- post-W6 W1-b Q31/Q32/Q34 (R220/R221/R228) ---------------------------------------------------------------------

describe("post-W6 W1-b: verification tones, sources, plan row headings and conflict copy", () => {
  const CONFLICT_TEXT = "Nothing is shown here: the address names selections that conflict.";

  it("Q34: a selector conflict prints its sentence once per panel and the cards say no read was made", async () => {
    serve({ ...actionReads(`?recorded_at=${encodeURIComponent(CUTOFF)}`) });
    mount(`/sites/KOBO-001/actions/${ACTION}/verification?recorded_at=${encodeURIComponent(CUTOFF)}&outcome_id=${OUT1}`);
    await settledScreen();
    const panels = Array.from(document.querySelectorAll("section.panel")) as HTMLElement[];
    expect(panels.length).toBeGreaterThan(0);
    for (const panel of panels) {
      const count = (panel.textContent ?? "").split(CONFLICT_TEXT).length - 1;
      expect(count, panel.querySelector("h2")?.textContent ?? "panel").toBeLessThanOrEqual(1);
    }
    expect(panels.some((p) => (p.textContent ?? "").includes(CONFLICT_TEXT))).toBe(true);
    const cards = Array.from(document.querySelectorAll("[data-verification-card]"));
    expect(cards.length).toBe(4);
    for (const card of cards) {
      expect(card.textContent).toContain("Not read: the address names conflicting selections.");
      expect(card.textContent).not.toContain("The verification read failed");
    }
  });

  it("Q34: a true read failure keeps the failure wording on the cards", async () => {
    serve({ ...actionReads() });
    mount(`/sites/KOBO-001/actions/${ACTION}/verification`);
    await settledScreen();
    const cards = Array.from(document.querySelectorAll("[data-verification-card]"));
    expect(cards.length).toBe(4);
    expect(cards.some((c) => (c.textContent ?? "").includes("The verification read failed"))).toBe(true);
    expect(document.body.textContent).not.toContain("Not read: the address names conflicting selections.");
  });

  it("Q32: every Available requirement chip is blue (info) and a shared source is named once", async () => {
    const ev = prep(R.evidence);
    ev.source_resolution.baseline.state = "REGISTERED_SIMULATION";
    ev.source_resolution.later.state = "REGISTERED_SIMULATION";
    serve({ ...actionReads(), [`${V}/evidence`]: ok(ev), [`${V}/plan?plan_id=${PLAN}`]: ok(prep(R.plan)) });
    mount(`/sites/KOBO-001/actions/${ACTION}/evidence`);
    await settledScreen();
    const chips = Array.from(document.querySelectorAll(".verify-chip")).filter((c) => c.textContent === "Available");
    expect(chips.length).toBeGreaterThan(0);
    for (const chip of chips) {
      expect(chip.classList.contains("verify-chip--info")).toBe(true);
      expect(chip.classList.contains("verify-chip--pass")).toBe(false);
    }
    expect(requirementTone(true)).toBe("info");
    // The blue chip is defined in the scoped verification stylesheet (ui/primitives.css is unchanged).
    expect(await readVerificationCss()).toMatch(/\.verify-chip--info \{[^}]*background: #e9f0fd;[^}]*color: #275ba8;/);
    expect(requirementTone(false)).toBe("fail");
    expect(requirementTone(null)).toBe("unknown");
    // Q46 (W1 ruling 57): one visible R385 label immediately below the Evidence requirements table.
    const r385 = document.querySelectorAll("[data-mock-deviation='R385']");
    expect(r385).toHaveLength(1);
    expect(r385[0].textContent).toBe("MOCK DEVIATION D2 (R385)");
    expect(r385[0].previousElementSibling?.querySelector("[data-verification-requirement-pair='conditions']")).not.toBeNull();
    const sourceCell = document.querySelector("[data-verification-requirement-pair='conditions'] td") as HTMLElement;
    expect(sourceCell.textContent?.split("Registered Lab trial data").length).toBe(2);
    expect(sourcePair("REGISTERED_SIMULATION", "REGISTERED_SIMULATION")).toBe("Registered Lab trial data");
    expect(sourcePair("REGISTERED_SIMULATION", "MIXED")).toBe("Registered Lab trial data / Mixed sources");
  });

  it("Q31: Success criteria keep <th scope=row> and the scoped CSS gives them normal weight and table line height", async () => {
    serve({ ...actionReads(), [`${V}/plan`]: ok(prep(R.plan)) });
    mount(`/sites/KOBO-001/actions/${ACTION}/plan`);
    await settledScreen();
    const panel = panelTitled("Success criteria");
    expect(panel.closest(".panel")?.classList.contains("w1f4-verification-plan")).toBe(true);
    // Q46 (W1 ruling 57): one visible R384 label immediately below the Success criteria table.
    const r384 = panel.querySelectorAll("[data-mock-deviation='R384']");
    expect(r384).toHaveLength(1);
    expect(r384[0].textContent).toBe("MOCK DEVIATION D2 (R384)");
    expect(r384[0].previousElementSibling?.querySelector("[data-verification-rule='target']")).not.toBeNull();
    const rowHeads = panel.querySelectorAll("tbody th[scope='row']");
    expect(rowHeads.length).toBeGreaterThan(0);
    const css = await readVerificationCss();
    expect(css).toMatch(/\.w1f4-verification-plan \.data-table tbody th\[scope="row"\] \{\s*font-weight: normal;\s*line-height: inherit;\s*\}/);
  });
});

/** The scoped verification stylesheet from disk (the estate tests' readDisk pattern; jsdom has no layout). */
async function readVerificationCss(): Promise<string> {
  const fs = (await import(/* @vite-ignore */ `node:${"fs"}`)) as { readFileSync: (p: string, e: string) => string };
  const cwd = (globalThis as unknown as { process: { cwd: () => string } }).process.cwd();
  return fs.readFileSync(`${cwd}/src/sites/w1f4-verification.css`, "utf8");
}
