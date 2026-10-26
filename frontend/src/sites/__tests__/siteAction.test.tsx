/**
 * S6-01b phase 1: the Action root (Overview, Application, History) and the
 * Finding Recommendation view, against S6-01a's committed wire contract
 * `backend/tests/fixtures/s6_action_api_contract.json` (`D-action-records-v1`,
 * keyed by manifest ID). `fetch` is stubbed to serve the recorded responses,
 * so the real client and the real screens read real persisted shapes; no
 * static mock value becomes product data.
 *
 * Derived bodies (phase-1 review L4), each marked "Derived" where it is built:
 * 1. "capability absent": a recorded body with the capability field removed;
 * 2. the events read at the ACCEPTED event: the recorded latest events cut
 *    through that event, with the recorded Action read's selection;
 * 3. the events read before APPLIED: the recorded latest events cut to the
 *    first two (ACCEPTED, OBSERVED), served beside the recorded pending read;
 * 4. store-unavailable 503 re-read bodies (no recorded case exists);
 * 5. a capability granted for a different command (OBSERVE renamed APPLY's
 *    slot) and a pending read whose application basis names no version.
 * 6. (reopen round) a cleared effective-time field is a UI input, not a body;
 * 7. (reopen round) the recorded accepted read with the recorded
 *    `prior_action_block` of `latest_revision_after_apply` added: the server may
 *    send a block while `state=ACCEPTED`, and the notice follows `state` only.
 * 8. (W1-F4) the verification history read beside History: the recorded
 *    `s6_verification_api_contract.json` history with its placeholder outcome
 *    and resolution IDs made distinct and its Action ID set to this Action.
 * Every other body is served exactly as recorded, including the reopen cases
 * `latest_revision_after_apply`, `latest_revision_after_apply_served_clock_stale`
 * and `accept_newer_revision_prior_action_unresolved` (D-2026-10-15-s601-reopen).
 *
 * Widths: jsdom has no layout, so the 1440 / 390 cases set the window width
 * and prove the same structure (no command control, a read-only reason) at
 * both; rendered layout at both widths is phase-2 browser evidence.
 */
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import contract from "../../../../backend/tests/fixtures/s6_action_api_contract.json";
import verificationContract from "../../../../backend/tests/fixtures/s6_verification_api_contract.json";
import { SiteActionFrame, SiteFindingFrame } from "../../shell/SiteAnalyticsFrames";
import { describeViolations, scanDisclosureVocabulary, scanProductVocabulary } from "../../test/productVocabulary";
import { expectStateLineVisible } from "../../test/productPresentation";
import { panelTitled } from "../../test/panelStructure";
import { settledScreen } from "../../test/settled";
import type { SiteDetailClient } from "../siteDirectoryClient";
import { HYBRID_MINI_GRID_SITE } from "./sldFixtures";
import { COLD_SITE, DOMAIN_ID, detailBody } from "./coldWorkFixtures";
import { EV_SITE } from "./evWorkFixtures";

type Case = { request: { method: string; path: string; body?: Record<string, unknown> }; status: number; body: any };
const M = contract.manifest as unknown as Record<string, Record<string, Case>>;
const rec = M["recommendation:1#a"];
const ov = M["action-overview:1#a"];
const ex = M["action-execution:1#a"];
const hi = M["action-history:1#a"];

const ACTION = ov.accepted_pending.body.action.id as string;
const FINDING = rec.pre_accept_available.body.finding_id as string;
const REV = rec.pre_accept_available.body.revision_id as string;
const INELIGIBLE_FINDING = rec.pre_accept_unavailable.body.finding_id as string;
const ACCEPTED_EVENT = hi.action_event_id_accepted.body.selection.event_id as string;
const OBSERVED_CUTOFF = hi.action_recorded_at_observed.body.selection.recorded_at as string;
const ACTION_API = `/api/sites/KOBO-001/actions/${ACTION}`;
const REC_API = `/api/sites/KOBO-001/findings/${FINDING}/recommendation`;

/** Method + path + sorted, decoded query: how a request is matched to a recorded case. */
function key(method: string, url: string): string {
  const [path, query = ""] = url.split("?");
  // Decoded by hand: a recorded path carries a raw "+" in an offset, which form decoding would turn into a space.
  const params = query
    .split("&")
    .filter(Boolean)
    .map((pair) => pair.split("=").map(decodeURIComponent) as [string, string])
    .sort(([a], [b]) => a.localeCompare(b));
  return `${method} ${decodeURIComponent(path)}${params.length ? `?${params.map(([k, v]) => `${k}=${v}`).join("&")}` : ""}`;
}

interface Served {
  status: number;
  body: unknown;
}

/** Stub `fetch`: GETs from a mutable table, POSTs from per-path queues; every request is recorded. */
function serve(gets: Record<string, Served>, posts: Record<string, Served[]> = {}) {
  const table = new Map<string, Served>();
  for (const [url, value] of Object.entries(gets)) table.set(key("GET", url), value);
  const queues = new Map<string, Served[]>();
  for (const [url, list] of Object.entries(posts)) queues.set(key("POST", url), [...list]);
  const requests: { method: string; url: string; body: any }[] = [];
  const unmatched: string[] = [];
  vi.stubGlobal("fetch", async (url: string, init?: RequestInit) => {
    const method = init?.method ?? "GET";
    requests.push({ method, url, body: init?.body ? JSON.parse(String(init.body)) : null });
    const k = key(method, url);
    const hit = method === "GET" ? table.get(k) : queues.get(k)?.shift();
    if (!hit) {
      unmatched.push(k);
      return new Response(JSON.stringify({ detail: { code: "TEST_UNMATCHED", message: k } }), { status: 599 });
    }
    return new Response(JSON.stringify(hit.body), { status: hit.status });
  });
  return {
    requests,
    unmatched,
    setGet(url: string, value: Served) {
      table.set(key("GET", url), value);
    },
  };
}

const served = (c: Case): Served => ({ status: c.status, body: c.body });

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
      </Routes>
    </MemoryRouter>,
  );
}

const q = (selector: string) => document.body.querySelector(selector);
const qa = (selector: string) => Array.from(document.body.querySelectorAll(selector));
const where = () => screen.getByTestId("where").textContent;

function withoutCapability<T extends { body: any }>(c: T): Served {
  // Derived: the recorded body with the capability field removed ("absent").
  const body = structuredClone(c.body);
  delete body.system_demo_capability;
  return { status: 200, body };
}

function atWidth(width: number) {
  Object.defineProperty(window, "innerWidth", { configurable: true, value: width });
  window.dispatchEvent(new Event("resize"));
}

function noVocabularyViolations(page: string) {
  const main = document.body.querySelector("main") as HTMLElement;
  const { violations, scanned } = scanProductVocabulary(main, page);
  expect(scanned).toBeGreaterThan(10);
  expect(violations, describeViolations(violations)).toEqual([]);
}

afterEach(() => {
  vi.useRealTimers();
  cleanup();
  vi.unstubAllGlobals();
  atWidth(1024);
});

describe("Recommendation (recommendation:1#a)", () => {
  it("shows the eligible trial, its pinned inputs, the limitation and a labelled SYSTEM accept control", async () => {
    const s = serve({ [`${REC_API}?revision_id=${REV}`]: served(rec.pre_accept_available) });
    mount(`/sites/KOBO-001/findings/${FINDING}/recommendation?revision_id=${REV}`);
    await settledScreen();
    const proposal = rec.pre_accept_available.body.proposal;
    expect(q("[data-recommendation-state]")?.getAttribute("data-recommendation-state")).toBe("AVAILABLE");
    expect(q("[data-recommendation-proposal]")?.textContent).toMatch(/20%.*to.*15%/);
    expect(q("[data-recommendation-rule]")?.textContent).toBe("reserve-trial-1 v1");
    // S4-05b phase 2: the recorded walkthrough is unpublished, so the stored source reads Source unverified.
    expect(q("[data-source-provenance-subject='recommendation']")?.getAttribute("data-source-provenance")).toBe("UNKNOWN");
    expect(q("[data-source-provenance-subject='recommendation']")?.textContent).toContain("Source unverified.");
    expect(q("[data-pinned-finding-revision]")?.textContent).toBe(proposal.finding_revision_id);
    expect(q("[data-pinned-foundation-revision]")?.textContent).toBe(proposal.foundation_revision_id);
    expect(Number(q("[data-recommendation-input-count]")?.getAttribute("data-recommendation-input-count"))).toBeGreaterThan(0);
    expect(q("[data-action-limitation='POLICY_SENSITIVITY_TRIAL_ONLY']")?.textContent).toMatch(/does not predict less generator time, any saving or any safety effect/);
    const button = screen.getByRole("button", { name: "Accept trial (SYSTEM demonstration)" });
    expect(button).toBeInTheDocument();
    // Money is a labelled link to the Finding's own stored figure, never an amount here.
    const money = q("[data-recommendation-money-link] a");
    expect(money?.getAttribute("href")).toBe(`/sites/KOBO-001/financials?finding_id=${FINDING}&revision_id=${REV}`);
    expect(q("[data-recommendation-money-link]")?.textContent).toMatch(/predicts no saving/);
    expect(document.body.textContent).not.toMatch(/approv/i);
    // W4-03 u6b ruling 6: this stub does not serve the shell's W1 selection, so no sibling carries the raw revision;
    // the Recommendation slot is noninteractive text.
    expect(q("[data-finding-section='recommendation']")).toBeNull();
    expect(q("[data-finding-section-gap='recommendation']")).toHaveTextContent("Recommendation");
    noVocabularyViolations("recommendation:1#a available");
    // W4-03 unit 6b (u6 ruling 5): the canonical mini shell's own W1 Finding read (this stub does not serve it, so the
    // Alternatives slot stays the noninteractive gap) is the one expected extra request.
    expect(s.unmatched).toEqual([`GET /api/sites/KOBO-001/findings/${FINDING}?revision_id=${REV}`]);
  });

  it("shows the typed unavailable reason and no control when the rule proposes nothing", async () => {
    serve({ [`/api/sites/KOBO-001/findings/${INELIGIBLE_FINDING}/recommendation`]: served(rec.pre_accept_unavailable) });
    mount(`/sites/KOBO-001/findings/${INELIGIBLE_FINDING}/recommendation`);
    await settledScreen();
    expect(q("[data-recommendation-unavailable]")?.getAttribute("data-recommendation-unavailable")).toBe("SOC_NOT_ABOVE_HEADROOM");
    expect(document.body.textContent).toMatch(/not above the reserve plus the 10-point headroom/);
    expect(screen.queryByRole("button")).toBeNull();
  });

  it("keeps the accepted snapshot and Action link beside a separately labelled live recomputation", async () => {
    serve({ [`${REC_API}?revision_id=${REV}`]: served(rec.accepted_snapshot_live_status) });
    mount(`/sites/KOBO-001/findings/${FINDING}/recommendation?revision_id=${REV}`);
    await settledScreen();
    expect(q("[data-recommendation-accepted]")?.textContent).toMatch(/20%.*to.*15%/);
    expect(q("[data-recommendation-action-link]")?.getAttribute("href")).toBe(`/sites/KOBO-001/actions/${ACTION}`);
    expect(q("[data-recommendation-live]")?.getAttribute("data-recommendation-live")).toBe("UNAVAILABLE");
    expect(q("[data-recommendation-live]")?.textContent).toMatch(/FINDING_REVISION_NOT_LATEST/);
    expect(screen.getByText(/This is not the accepted proposal/)).toBeInTheDocument();
    expect(q("[data-recommendation-newer-revision]")?.getAttribute("data-recommendation-newer-revision")).toBe(
      rec.accepted_snapshot_live_status.body.latest_revision_id,
    );
    expect(screen.queryByRole("button")).toBeNull();
    noVocabularyViolations("recommendation:1#a accepted");
  });

  it("accepts through the SYSTEM command with a fresh key, then reloads to the accepted snapshot", async () => {
    const url = `${REC_API}?revision_id=${REV}`;
    const s = serve({ [url]: served(rec.pre_accept_available) }, { [`${REC_API}/accept`]: [served(rec.accept_created)] });
    mount(`/sites/KOBO-001/findings/${FINDING}/recommendation?revision_id=${REV}`);
    await settledScreen();
    s.setGet(url, served(rec.accepted_snapshot_live_status));
    fireEvent.click(screen.getByRole("button", { name: /Accept trial/ }));
    await waitFor(() => expect(q("[data-action-command-done='created']")).not.toBeNull());
    await settledScreen();
    const post = s.requests.find((r) => r.method === "POST");
    const recorded = rec.accept_created.request.body as Record<string, unknown>;
    expect(post?.body).toMatchObject({
      revision_id: recorded.revision_id,
      foundation_revision_id: recorded.foundation_revision_id,
      recommendation_key: recorded.recommendation_key,
      proposed_value: "15",
    });
    expect(post?.body.idempotency_key).toMatch(/^ui-/);
    expect(Object.keys(post?.body ?? {}).sort()).toEqual(
      ["foundation_revision_id", "idempotency_key", "proposed_value", "recommendation_key", "revision_id"],
    );
    expect(q("[data-action-command-done] a")?.getAttribute("href")).toBe(`/sites/KOBO-001/actions/${ACTION}`);
    expect(q("[data-recommendation-accepted-action]")?.getAttribute("data-recommendation-accepted-action")).toBe(ACTION);
  });

  it("an identical accept replay says it was already recorded and links the same Action (accept_replayed)", async () => {
    serve(
      { [`${REC_API}?revision_id=${REV}`]: served(rec.pre_accept_available) },
      { [`${REC_API}/accept`]: [served(rec.accept_replayed)] },
    );
    mount(`/sites/KOBO-001/findings/${FINDING}/recommendation?revision_id=${REV}`);
    await settledScreen();
    fireEvent.click(screen.getByRole("button", { name: /Accept trial/ }));
    await waitFor(() => expect(q("[data-action-command-done='replayed']")).not.toBeNull());
    expect(q("[data-action-command-done]")?.textContent).toMatch(/already recorded/);
    expect(q("[data-action-command-done] a")?.getAttribute("href")).toBe(`/sites/KOBO-001/actions/${ACTION}`);
  });

  for (const [name, width] of [
    ["latest_revision_after_apply", 1440],
    ["latest_revision_after_apply_served_clock_stale", 390],
  ] as const) {
    it(`the newer Finding version names and links the unresolved earlier Action, with Accept disabled (${name}, ${width})`, async () => {
      atWidth(width);
      const latest = rec[name];
      const block = latest.body.prior_action_block;
      serve({ [latest.request.path]: served(latest) });
      mount(`/sites/KOBO-001/findings/${FINDING}/recommendation`);
      await settledScreen();
      expect(q("[data-recommendation-state]")?.getAttribute("data-recommendation-state")).toBe("PRIOR_ACTION_UNRESOLVED");
      // The notice names and links the blocking Action and its own (earlier) origin version.
      expect(q("[data-recommendation-prior-block]")?.getAttribute("data-recommendation-prior-block")).toBe(block.blocking_action_id);
      expect(q("[data-recommendation-prior-block-link]")?.textContent).toBe(block.blocking_action_code);
      expect(q("[data-recommendation-prior-block-link]")?.getAttribute("href")).toBe(block.links.action);
      expect(q("[data-recommendation-prior-block-origin]")?.getAttribute("href")).toBe(
        `/sites/KOBO-001/findings/${FINDING}?revision_id=${block.origin_finding_revision_id}`,
      );
      expect(q("[data-recommendation-prior-block-origin]")?.textContent).toBe(`Finding version ${block.origin_revision_no}`);
      expect(block.origin_finding_revision_id).not.toBe(latest.body.revision_id);
      expect(q("[data-recommendation-prior-block]")?.textContent).toMatch(/not on the version shown on this page/);
      expect(q("[data-recommendation-prior-block-state]")?.textContent).toMatch(/Applied to the Site Foundation.*Pending/);
      // The live reason is separate: AVAILABLE on the recorded clock, FOUNDATION_BASIS_STALE on the served clock.
      const live = latest.body.live_status;
      expect(q("[data-recommendation-live]")?.getAttribute("data-recommendation-live")).toBe(live.state);
      if (live.unavailable) expect(q("[data-recommendation-live]")?.textContent).toContain(live.unavailable.code);
      expect(screen.getByText(/This is a separate reason/)).toBeInTheDocument();
      // No proposal is offered for acceptance: Accept is disabled with the reason stated.
      expect(q("[data-recommendation-proposal]")).toBeNull();
      const button = screen.getByRole("button", { name: /Accept trial/ });
      expect(button).toBeDisabled();
      expect(button.getAttribute("aria-describedby")).toBe("site-recommendation-accept-held");
      expect(q("[data-action-command-unavailable='PRIOR_ACTION_UNRESOLVED']")?.textContent).toMatch(
        new RegExp(`earlier trial on this Finding \\(${block.blocking_action_code}\\) is still open`),
      );
      // The earlier Action is listed with its own origin version, never relabelled as this one.
      const item = q(`[data-recommendation-prior-action='${block.blocking_action_id}']`);
      expect(item?.getAttribute("data-prior-action-selected-revision")).toBe("no");
      expect(item?.textContent).toMatch(/not the version on this page/);
      expect(item?.querySelector("[data-prior-action-application]")?.getAttribute("data-prior-action-application")).toBe("APPLIED");
      expect(item?.querySelector("[data-prior-action-outcome]")?.getAttribute("data-prior-action-outcome")).toBe("PENDING");
      expect(item?.querySelector("[data-recommendation-prior-action-link]")?.getAttribute("href")).toBe(block.links.action);
      expect(q("[data-recommendation-accepted-action]")).toBeNull();
      noVocabularyViolations(`recommendation ${name}`);
    });
  }

  it("lists the Action on the selected version as this version beside the accepted snapshot", async () => {
    serve({ [`${REC_API}?revision_id=${REV}`]: served(rec.accepted_snapshot_live_status) });
    mount(`/sites/KOBO-001/findings/${FINDING}/recommendation?revision_id=${REV}`);
    await settledScreen();
    const item = q(`[data-recommendation-prior-action='${ACTION}']`);
    expect(item?.getAttribute("data-prior-action-selected-revision")).toBe("yes");
    expect(item?.textContent).toMatch(/\(this version\)/);
    expect(q("[data-recommendation-prior-block]")).toBeNull();
  });

  it("shows no held notice when state is ACCEPTED, even if a prior_action_block is present", async () => {
    // Derived (7): the selected version has its own Action; the block alone never decides the notice.
    const body = { ...rec.accepted_snapshot_live_status.body, prior_action_block: rec.latest_revision_after_apply.body.prior_action_block };
    serve({ [`${REC_API}?revision_id=${REV}`]: { status: 200, body } });
    mount(`/sites/KOBO-001/findings/${FINDING}/recommendation?revision_id=${REV}`);
    await settledScreen();
    expect(q("[data-recommendation-state]")?.getAttribute("data-recommendation-state")).toBe("ACCEPTED");
    expect(q("[data-recommendation-prior-block]")).toBeNull();
    expect(q("[data-action-command-held]")).toBeNull();
    expect(q("[data-recommendation-accepted]")?.textContent).toMatch(/20%.*to.*15%/);
    expect(q("[data-recommendation-accepted-action]")?.getAttribute("data-recommendation-accepted-action")).toBe(ACTION);
  });

  it("a 409 PRIOR_ACTION_UNRESOLVED on accept names and links the earlier Action, with the live reason separate", async () => {
    const url = `${REC_API}?revision_id=${REV}`;
    const held = rec.accept_newer_revision_prior_action_unresolved;
    const s = serve({ [url]: served(rec.pre_accept_available) }, { [`${REC_API}/accept`]: [served(held)] });
    mount(`/sites/KOBO-001/findings/${FINDING}/recommendation?revision_id=${REV}`);
    await settledScreen();
    fireEvent.click(screen.getByRole("button", { name: /Accept trial/ }));
    await waitFor(() => expect(q("[data-action-command-refused='PRIOR_ACTION_UNRESOLVED']")).not.toBeNull());
    await settledScreen();
    const refused = q("[data-action-command-refused='PRIOR_ACTION_UNRESOLVED']");
    expect(refused?.textContent).toMatch(/Not accepted: an earlier trial on this Finding is still open, so no new Action was recorded/);
    expect(refused?.textContent).toMatch(new RegExp(`accepted on Finding version ${held.body.detail.origin_revision_no}`));
    expect(q("[data-accept-held-action-link]")?.getAttribute("href")).toBe(held.body.detail.links.action);
    expect(q("[data-accept-held-action-link]")?.textContent).toBe(`Open ${held.body.detail.blocking_action_code}`);
    expect(q("[data-accept-held-live]")?.getAttribute("data-accept-held-live")).toBe(held.body.detail.live_status.state);
    expect(q("[data-action-command-done]")).toBeNull();
    expect(s.requests.filter((r) => r.method === "POST")).toHaveLength(1);
    noVocabularyViolations("recommendation accept held");
  });

  it("treats ACTION_ACCEPTANCE_CONFLICT as already accepted and follows its action_id", async () => {
    serve(
      { [`${REC_API}?revision_id=${REV}`]: served(rec.pre_accept_available) },
      { [`${REC_API}/accept`]: [served(rec.accept_conflict_already_accepted)] },
    );
    mount(`/sites/KOBO-001/findings/${FINDING}/recommendation?revision_id=${REV}`);
    await settledScreen();
    fireEvent.click(screen.getByRole("button", { name: /Accept trial/ }));
    await waitFor(() => expect(q("[data-action-command-done='already-accepted']")).not.toBeNull());
    expect(q("[data-action-command-done='already-accepted'] a")?.getAttribute("href")).toBe(`/sites/KOBO-001/actions/${ACTION}`);
  });

  it("shows the server refusal when a command is attempted without the capability, keeping the proposal", async () => {
    serve(
      { [`${REC_API}?revision_id=${REV}`]: served(rec.pre_accept_available) },
      { [`${REC_API}/accept`]: [served(rec.accept_capability_denied)] },
    );
    mount(`/sites/KOBO-001/findings/${FINDING}/recommendation?revision_id=${REV}`);
    await settledScreen();
    fireEvent.click(screen.getByRole("button", { name: /Accept trial/ }));
    await waitFor(() => expect(q("[data-action-command-refused='SYSTEM_DEMO_CAPABILITY_DENIED']")).not.toBeNull());
    await settledScreen();
    expect(q("[data-recommendation-proposal]")?.textContent).toMatch(/15%/);
  });

  for (const width of [1440, 390]) {
    it(`is read-only with a reason when the capability is denied or absent (${width})`, async () => {
      atWidth(width);
      const url = `${REC_API}?revision_id=${REV}`;
      serve({ [url]: served(rec.capability_denied) });
      mount(`/sites/KOBO-001/findings/${FINDING}/recommendation?revision_id=${REV}`);
      await settledScreen();
      expect(screen.queryByRole("button")).toBeNull();
      expect(q("[data-action-command-unavailable='ACCEPT']")?.textContent).toMatch(
        /read-only here.*No SYSTEM demonstration capability is configured on this server/,
      );
      expect(q("[data-recommendation-proposal]")).not.toBeNull();
      cleanup();
      vi.unstubAllGlobals();
      serve({ [url]: withoutCapability(rec.pre_accept_available) });
      mount(`/sites/KOBO-001/findings/${FINDING}/recommendation?revision_id=${REV}`);
      await settledScreen();
      expect(screen.queryByRole("button")).toBeNull();
      expect(q("[data-action-command-unavailable='UNKNOWN']")?.textContent).toMatch(/read-only here/);
    });
  }
});

/** Overview/Application/History read both the Action and its events with the same selector. */
/** Derived (8): the recorded verification history, with distinct placeholder IDs, for this Action. */
function verificationHistory(): Served {
  const h = structuredClone((verificationContract as any).responses.history);
  h.action_id = ACTION;
  h.outcomes.forEach((o: any, i: number) => {
    o.outcome_id = `outcome-${i + 1}`;
    o.action_id = ACTION;
  });
  h.resolution_events.forEach((r: any, i: number) => {
    r.id = `resolution-${i + 1}`;
    r.verification_outcome_id = "outcome-1";
  });
  return { status: 200, body: h };
}

/** W1-F4 trim: opens the in-place "Show all" toggle of the Action history. */
function showAllHistory() {
  fireEvent.click(q("[data-action-history-show-all]") as HTMLElement);
}

/** W1-F4 trim: an exact reference's value in a closed disclosure, by its label. */
function exactReference(name: string, label: string): string | null {
  const rows = qa(`[data-disclosure='${name}'] .exact-references__row`);
  const row = rows.find((r) => r.querySelector("dt")?.textContent === label);
  return row?.querySelector("dd")?.textContent ?? null;
}

function actionReads(action: Case | Served, events: Case | Served, query = "") {
  return {
    [`${ACTION_API}${query}`]: "request" in action ? served(action) : action,
    [`${ACTION_API}/events${query}`]: "request" in events ? served(events) : events,
    // W1-F4: History also reads the verification outcome history; it takes no event selector.
    [`${ACTION_API}/verification/history`]: verificationHistory(),
  };
}

describe("Action root (action-overview / action-execution / action-history :1#a)", () => {
  it("Overview shows code, origin beside the latest Finding version, pinned basis and a pending outcome", async () => {
    serve(actionReads(ov.applied_pending_newer_revision, hi.events_latest));
    mount(`/sites/KOBO-001/actions/${ACTION}`);
    await settledScreen();
    const body = ov.applied_pending_newer_revision.body;
    await waitFor(() =>
      expect(screen.getByRole("heading", { level: 1 }).textContent).toBe(`${body.action.action_code} · Battery reserve trial`),
    );
    expect(q("[data-action-origin-link]")?.getAttribute("href")).toBe(
      `/sites/KOBO-001/findings/${body.origin.finding_id}?revision_id=${body.origin.finding_revision_id}`,
    );
    expect(q("[data-action-newer-revision]")?.getAttribute("data-action-newer-revision")).toBe(body.newer_revision_notice.latest_revision_id);
    expect(body.newer_revision_notice.latest_revision_id).not.toBe(body.origin.finding_revision_id);
    // W1-F4 trim: the exact configuration versions moved from key-value rows into the closed disclosure.
    expect(exactReference("action-state-references", "Configuration basis")).toBe(body.basis.foundation_revision_id);
    // S6-02b (F5): the Overview reads the verification block, not `state.outcome`.
    expect(q("[data-action-verification-state]")).toHaveAttribute("data-action-verification-state", body.verification.state);
    // W1-F4 fix: the no-plan sentence appears once (re-pointed from the duplicate label span to the line's sentence).
    expect(q("[data-action-outcome-line]")?.textContent).toMatch(/^No verification plan exists for this work/);
    expect(q("[data-action-outcome-line]")?.textContent).not.toMatch(/No verification plan yet/);
    expect(exactReference("action-state-references", "New configuration version")).toBe(body.change.new_foundation_revision_id);
    expect(q("[data-action-applied-event-link]")?.getAttribute("href")).toBe(
      `/sites/KOBO-001/actions/${ACTION}/history?event_id=${body.change.applied_event_id}`,
    );
    // S6-02b: the mock's section order, with the verification children.
    expect(qa("[data-action-section]").map((a) => a.textContent)).toEqual([
      "Overview",
      "Plan",
      "Application",
      "Evidence",
      "Verification",
      "History",
    ]);
    expect(document.body.textContent).not.toMatch(/saving (?:of|was|is achieved)|reduced generator|approv/i);
    noVocabularyViolations("action-overview:1#a");
  });

  it("W1-UX-01: the Action card uses the W1 set and the narrower disclosure list; its state line stays visible", async () => {
    for (const [fixture, label] of [
      [ov.applied_pending_newer_revision, "No trial plan yet"],
      [ov.accepted_pending, null],
    ] as const) {
      serve(actionReads(fixture, hi.events_latest));
      const view = mount(`/sites/KOBO-001/actions/${ACTION}`);
      await settledScreen();
      const main = document.body.querySelector("main") as HTMLElement;
      const w1 = scanProductVocabulary(main, "action-overview (W1)", { set: "w1" });
      expect(w1.scanned).toBeGreaterThan(10);
      expect(w1.violations, describeViolations(w1.violations)).toEqual([]);
      // W1-F4: the former answer card is merged into the single "Action scope" panel.
      const card = panelTitled("Action scope");
      const disclosure = scanDisclosureVocabulary(card, "action-overview disclosure");
      expect(disclosure.disclosures).toBe(1);
      expect(disclosure.scanned).toBeGreaterThan(4);
      expect(disclosure.violations, describeViolations(disclosure.violations)).toEqual([]);
      const shown = expectStateLineVisible(card);
      if (label !== null) expect(shown).toBe(label);
      expect(card.querySelector("[data-product-status]")?.getAttribute("data-product-status")).not.toBe("positive");
      // W1-F4: the three-step strip became the Action (accepted time), Application and Outcome key values.
      expect(card.querySelector("[data-key-value='action']")?.textContent).toMatch(/accepted \d/);
      expect(card.querySelector("[data-key-value='application'] [data-action-application-words]")).not.toBeNull();
      expect(card.querySelector("[data-key-value='outcome'] [data-product-status-label]")?.textContent).toBe(shown);
      view.unmount();
    }
  });

  it("W1-UX-01: a verified summary without a source is not shown as positive and points to Verification for source and limits", async () => {
    const base = ov.applied_pending_newer_revision;
    const verified = { ...base, body: { ...base.body, verification: { ...base.body.verification, state: "VERIFIED", reasons: [] } } };
    serve(actionReads(verified as typeof base, hi.events_latest));
    mount(`/sites/KOBO-001/actions/${ACTION}`);
    await settledScreen();
    const card = panelTitled("Action scope");
    expect(expectStateLineVisible(card)).toBe("Target met within the sampled limits");
    expect(card.querySelector("[data-product-status]")?.getAttribute("data-product-status")).toBe("limited");
    expect(card.querySelector("[data-action-outcome-source-note]")?.textContent).toMatch(/no savings or realized benefit is\s+claimed/);
    expect(card.querySelector("[data-action-verification-link]")?.getAttribute("href")).toContain("/verification");
    // W1-F4: the step strip's done step is now the outcome badge, in the limited (amber) tone, never green.
    expect(card.querySelector("[data-key-value='outcome'] .w1f4-action-badge--amber")).not.toBeNull();
  });

  it("Application lists ACCEPTED, OBSERVED, FAILED and APPLIED with actor, provenance, effective revision and change record", async () => {
    serve(actionReads(ov.applied_pending_newer_revision, hi.events_latest));
    mount(`/sites/KOBO-001/actions/${ACTION}/execution`);
    await settledScreen();
    const events = hi.events_latest.body.events as { id: string; kind: string }[];
    // W1-F4 trim: the Activity log shows the latest three steps, as the mock does, and links the full list on History.
    expect(qa("[data-action-event-kind]").map((r) => r.getAttribute("data-action-event-kind"))).toEqual(events.slice(-3).map((e) => e.kind));
    expect(qa("[data-action-event-failure]").map((e) => e.getAttribute("data-action-event-failure"))).toEqual([
      "ACTION_VALUE_INVALID",
      "ACTION_EFFECTIVE_TIME_INVALID",
    ]);
    const all = q("[data-action-work-history-link]");
    expect(all?.textContent).toBe(`Show all ${events.length} steps`);
    expect(all?.getAttribute("href")).toBe(`/sites/KOBO-001/actions/${ACTION}/history`);
    const change = ov.applied_pending_newer_revision.body.change;
    expect(q("[data-action-event-change-link]")?.getAttribute("href")).toContain(change.change_id);
    // The recording service is an exact reference, kept in the closed disclosure.
    expect(document.body.textContent).toMatch(/assetops-backend\/action-api/);
    // W1-F4: the actor is its own named cell in the Activity log (Record | State | Evidence | Recorded | Acted by).
    expect(qa("[data-action-event-kind] [data-action-event-actor]")).toHaveLength(3);
    expect(qa("[data-action-event-kind] [data-action-event-actor]").every((td) => /SYSTEM demonstration/.test(td.textContent ?? ""))).toBe(true);
    expect(q("[data-action-already-applied]")).not.toBeNull();
    expect(screen.queryByRole("button")).toBeNull();
    expect(q("[data-action-section='execution']")).toHaveAttribute("aria-current", "page");
    noVocabularyViolations("action-execution:1#a");
    // The full list, with every failure code, the exact versions and the change record, is reachable on History.
    cleanup();
    vi.unstubAllGlobals();
    serve(actionReads(ov.applied_pending_newer_revision, hi.events_latest));
    mount(`/sites/KOBO-001/actions/${ACTION}/history`);
    await settledScreen();
    showAllHistory();
    expect(qa("[data-action-event-kind]").map((r) => r.getAttribute("data-action-event-kind"))).toEqual(events.map((e) => e.kind));
    for (const code of ["ACTION_FOUNDATION_STALE", "ACTION_VALUE_INVALID", "ACTION_EFFECTIVE_TIME_INVALID"]) {
      expect(q(`[data-action-event-failure='${code}']`)?.textContent).toContain(code);
    }
    expect(q("[data-action-event-change]")?.textContent).toBe(change.change_id);
    expect(q("[data-action-event-effective-revision]")?.textContent).toBe(change.new_foundation_revision_id);
  });

  it("applies with a fresh key per attempt: a stale FAILED keeps it pending, a replay says so, then APPLIED", async () => {
    // The clock is pinned before the recorded read time, so the default is the read time's next midnight.
    vi.useFakeTimers({ toFake: ["Date"] });
    vi.setSystemTime(new Date("2026-11-01T00:30:00Z"));
    // Derived (3): the recorded latest events cut to ACCEPTED and OBSERVED.
    const s = serve(actionReads(ov.accepted_pending, { status: 200, body: { ...hi.events_latest.body, events: hi.events_latest.body.events.slice(0, 2) } }), {
      [`${ACTION_API}/apply`]: [served(ex.apply_stale_failed), served(ex.apply_stale_retry_same_key), served(ex.apply_applied)],
    });
    mount(`/sites/KOBO-001/actions/${ACTION}/execution`);
    await settledScreen();
    // W1-F4: the Activity log states the application on its state word (the Overview keeps data-action-application-words).
    expect(q("[data-action-work-headline]")?.textContent).toBe("Not applied yet");
    const apply = () => fireEvent.click(screen.getByRole("button", { name: "Apply trial (SYSTEM demonstration)" }));

    apply();
    await waitFor(() => expect(q("[data-action-command-refused='ACTION_FOUNDATION_STALE']")).not.toBeNull());
    expect(q("[data-action-failed-event]")?.textContent).toMatch(/A failed attempt was recorded\. The application is still pending/);
    expect(q("[data-action-failed-event] a")?.getAttribute("href")).toBe(
      `/sites/KOBO-001/actions/${ACTION}/history?event_id=${ex.apply_stale_failed.body.detail.event.id}`,
    );
    await settledScreen();

    apply();
    await waitFor(() => expect(q("[data-action-failed-event]")?.textContent).toMatch(/repeats an earlier attempt/));
    await settledScreen();

    s.setGet(ACTION_API, served(ov.applied_pending_newer_revision));
    s.setGet(`${ACTION_API}/events`, served(hi.events_latest));
    apply();
    await waitFor(() => expect(q("[data-action-command-done='applied']")).not.toBeNull());
    await settledScreen();
    expect(q("[data-action-work-headline]")?.textContent).toBe("Applied; effect not yet measured");

    const posts = s.requests.filter((r) => r.method === "POST");
    expect(posts).toHaveLength(3);
    const basis = ov.accepted_pending.body.application_basis;
    for (const post of posts) {
      expect(post.body).toMatchObject({ value: "15", expected_foundation_revision_id: basis.current_foundation_revision_id });
      expect(post.body.effective_from).toMatch(/^\d{4}-\d{2}-\d{2}T00:00:00\+00:00$/);
      expect(Object.keys(post.body).sort()).toEqual(["effective_from", "expected_foundation_revision_id", "idempotency_key", "value"]);
    }
    expect(new Set(posts.map((p) => p.body.idempotency_key)).size).toBe(3);
    // L1: the default is exactly the next UTC midnight after the read time (the clock is before it).
    expect(posts.map((p) => p.body.effective_from)).toEqual(Array(3).fill("2026-11-02T00:00:00+00:00"));
    vi.useRealTimers();
  });

  it("re-derives an untouched default effective time at click, so a page left open past midnight sends no past instant", async () => {
    vi.useFakeTimers({ toFake: ["Date"] });
    vi.setSystemTime(new Date("2026-11-01T01:00:00Z"));
    try {
      const s = serve(actionReads(ov.accepted_pending, hi.events_latest), {
        [`${ACTION_API}/apply`]: [served(ex.apply_stale_failed), served(ex.apply_stale_failed)],
      });
      mount(`/sites/KOBO-001/actions/${ACTION}/execution`);
      await settledScreen();
      const field = q("[data-action-effective-from]") as HTMLInputElement;
      expect(field.value).toBe("2026-11-02T00:00");
      vi.setSystemTime(new Date("2026-11-03T05:00:00Z"));
      fireEvent.click(screen.getByRole("button", { name: /Apply trial/ }));
      await waitFor(() => expect(s.requests.filter((r) => r.method === "POST")).toHaveLength(1));
      expect(s.requests.find((r) => r.method === "POST")?.body.effective_from).toBe("2026-11-04T00:00:00+00:00");
      await settledScreen();
      // An edited value is the operator's own and is sent as typed.
      fireEvent.change(q("[data-action-effective-from]") as HTMLInputElement, { target: { value: "2026-11-05T06:00" } });
      fireEvent.click(screen.getByRole("button", { name: /Apply trial/ }));
      await waitFor(() => expect(s.requests.filter((r) => r.method === "POST")).toHaveLength(2));
      expect(s.requests.filter((r) => r.method === "POST")[1].body.effective_from).toBe("2026-11-05T06:00:00+00:00");
    } finally {
      vi.useRealTimers();
    }
  });

  it("disables Apply while the effective-time field is cleared, and sends nothing (review L3)", async () => {
    const s = serve(actionReads(ov.accepted_pending, hi.events_latest), {
      [`${ACTION_API}/apply`]: [served(ex.apply_stale_failed)],
    });
    mount(`/sites/KOBO-001/actions/${ACTION}/execution`);
    await settledScreen();
    fireEvent.change(q("[data-action-effective-from]") as HTMLInputElement, { target: { value: "" } });
    const button = screen.getByRole("button", { name: /Apply trial/ });
    expect(button).toBeDisabled();
    expect(q("[data-action-apply-no-time]")?.textContent).toBe("Enter the effective time to apply.");
    fireEvent.click(button);
    expect(s.requests.filter((r) => r.method === "POST")).toHaveLength(0);
    fireEvent.change(q("[data-action-effective-from]") as HTMLInputElement, { target: { value: "2026-11-05T06:00" } });
    expect(screen.getByRole("button", { name: /Apply trial/ })).not.toBeDisabled();
    expect(q("[data-action-apply-no-time]")).toBeNull();
  });

  it("offers no Apply when the capability names a different command (granted() checks the exact command)", async () => {
    // Derived (5): APPLY's slot carries the recorded allowed OBSERVE capability.
    const body = structuredClone(ov.accepted_pending.body);
    body.system_demo_capability.apply = body.system_demo_capability.observe;
    expect(body.system_demo_capability.apply.allowed).toBe(true);
    serve(actionReads({ status: 200, body }, hi.events_latest));
    mount(`/sites/KOBO-001/actions/${ACTION}/execution`);
    await settledScreen();
    expect(screen.queryByRole("button", { name: /Apply trial/ })).toBeNull();
    expect(q("[data-action-command-unavailable]")).not.toBeNull();
  });

  it("offers no Apply, with a stated reason, when the read names no current Foundation version", async () => {
    // Derived (5): the recorded pending read with no current version in its application basis.
    const body = structuredClone(ov.accepted_pending.body);
    body.application_basis.current_foundation_revision_id = null;
    serve(actionReads({ status: 200, body }, hi.events_latest));
    mount(`/sites/KOBO-001/actions/${ACTION}/execution`);
    await settledScreen();
    expect(screen.queryByRole("button", { name: /Apply trial/ })).toBeNull();
    expect(q("[data-action-apply-no-basis]")?.textContent).toMatch(/did not state the current Foundation version/);
  });

  it("shows each recorded 422 FAILED variant typed and still pending", async () => {
    for (const name of ["apply_invalid_value_failed", "apply_backdate_failed", "apply_no_change_failed"]) {
      serve(actionReads(ov.accepted_pending, hi.events_latest), { [`${ACTION_API}/apply`]: [served(ex[name])] });
      mount(`/sites/KOBO-001/actions/${ACTION}/execution`);
      await settledScreen();
      fireEvent.click(screen.getByRole("button", { name: /Apply trial/ }));
      const code = ex[name].body.detail.code as string;
      await waitFor(() => expect(q(`[data-action-command-refused='${code}']`)).not.toBeNull());
      expect(ex[name].status).toBe(422);
      expect(q("[data-action-failed-event]")?.textContent).toMatch(/still pending/);
      cleanup();
      vi.unstubAllGlobals();
    }
  });

  it("a wrong-Site apply is refused not found (apply_wrong_site_404)", async () => {
    serve(actionReads(ov.accepted_pending, hi.events_latest), { [`${ACTION_API}/apply`]: [served(ex.apply_wrong_site_404)] });
    mount(`/sites/KOBO-001/actions/${ACTION}/execution`);
    await settledScreen();
    fireEvent.click(screen.getByRole("button", { name: /Apply trial/ }));
    await waitFor(() => expect(q("[data-action-command-refused='ACTION_NOT_FOUND']")).not.toBeNull());
    expect(q("[data-action-command-refused]")?.textContent).toMatch(/HTTP 404/);
  });

  it("says ACTION_ALREADY_APPLIED attempted nothing, and keeps the prior read when the re-read fails", async () => {
    const s = serve(actionReads(ov.accepted_pending, hi.events_latest), { [`${ACTION_API}/apply`]: [served(ex.apply_new_key_already_applied)] });
    mount(`/sites/KOBO-001/actions/${ACTION}/execution`);
    await settledScreen();
    // Derived (4): no recorded store-unavailable case exists.
    s.setGet(ACTION_API, { status: 503, body: { detail: { code: "STORE_UNAVAILABLE", message: "The store could not be read." } } });
    fireEvent.click(screen.getByRole("button", { name: /Apply trial/ }));
    await waitFor(() => expect(q("[data-action-already-applied-event]")).not.toBeNull());
    await settledScreen();
    expect(q("[data-action-already-applied-event]")?.textContent).toMatch(/nothing was attempted/);
    expect(q("[data-action-read='refused'][data-action-code='STORE_UNAVAILABLE']")).not.toBeNull();
    expect(screen.getByText("The last successful read is still shown below.")).toBeInTheDocument();
    expect(q("[data-action-id]")?.getAttribute("data-action-id")).toBe(ACTION);
  });

  it("server refusal of an apply attempted without the capability is shown typed", async () => {
    serve(actionReads(ov.accepted_pending, hi.events_latest), { [`${ACTION_API}/apply`]: [served(ex.apply_capability_denied)] });
    mount(`/sites/KOBO-001/actions/${ACTION}/execution`);
    await settledScreen();
    fireEvent.click(screen.getByRole("button", { name: /Apply trial/ }));
    await waitFor(() => expect(q("[data-action-command-refused='SYSTEM_DEMO_CAPABILITY_DENIED']")).not.toBeNull());
  });

  for (const width of [1440, 390]) {
    it(`Application is read-only with a reason when the capability is denied or absent (${width})`, async () => {
      atWidth(width);
      // The recorded denied read (a pending Action, latest record) is served as recorded.
      expect(ov.capability_denied.body.state.application).toBe("PENDING");
      serve(actionReads(ov.capability_denied, hi.events_latest));
      mount(`/sites/KOBO-001/actions/${ACTION}/execution`);
      await settledScreen();
      expect(screen.queryByRole("button")).toBeNull();
      expect(q("[data-action-command-unavailable='APPLY']")?.textContent).toMatch(
        /read-only here.*No SYSTEM demonstration capability is configured on this server/,
      );
      cleanup();
      vi.unstubAllGlobals();
      serve(actionReads(withoutCapability(ov.accepted_pending), hi.events_latest));
      mount(`/sites/KOBO-001/actions/${ACTION}/execution`);
      await settledScreen();
      expect(screen.queryByRole("button")).toBeNull();
      expect(q("[data-action-command-unavailable]")?.textContent).toMatch(/read-only here/);
    });
  }

  it("History lists events in server order with both times on the backdated observation and no invented revision", async () => {
    serve(actionReads(ov.applied_pending_newer_revision, hi.events_latest));
    mount(`/sites/KOBO-001/actions/${ACTION}/history`);
    await settledScreen();
    const events = hi.events_latest.body.events as { id: string; recorded_at: string; occurred_at: string; kind: string }[];
    // W1-F4 trim: the latest three rows (here the verification rows, recorded last) show by default; the toggle shows all.
    expect(qa("[data-action-event], [data-action-history-outcome], [data-action-history-resolution]")).toHaveLength(3);
    expect(q("[data-action-history-show-all]")?.textContent).toBe(`Show all ${events.length + 4} entries`);
    showAllHistory();
    expect(qa("[data-action-event]").map((r) => r.getAttribute("data-action-event"))).toEqual(events.map((e) => e.id));
    const observed = events.find((e) => e.kind === "OBSERVED")!;
    const row = q(`[data-action-event='${observed.id}']`)!;
    expect(row.querySelector("[data-action-recorded-at]")?.getAttribute("data-action-recorded-at")).toBe(observed.recorded_at);
    expect(row.querySelector("[data-action-occurred-at]")?.getAttribute("data-action-occurred-at")).toBe(observed.occurred_at);
    expect(row.textContent).toMatch(/recorded later than it happened/);
    expect(row.textContent).toMatch(/changes no application or outcome state/);
    expect(document.body.textContent).not.toMatch(/Action revision|revision \d+ of this Action/i);
    noVocabularyViolations("action-history:1#a");
  });

  it("selects an exact event_id from the URL, keeps it across sections and on reload", async () => {
    // Derived events read: the recorded latest events through the ACCEPTED event, with the recorded selection.
    const selection = hi.action_event_id_accepted.body.selection;
    const events = { status: 200, body: { ...hi.events_latest.body, selection, events: hi.events_latest.body.events.slice(0, 1) } };
    const query = `?event_id=${ACCEPTED_EVENT}`;
    const s = serve(actionReads(hi.action_event_id_accepted, events, query));
    const path = `/sites/KOBO-001/actions/${ACTION}/history${query}`;
    mount(path);
    await settledScreen();
    expect(q("[data-action-selection-notice='EVENT_ID']")?.getAttribute("data-action-cutoff-event")).toBe(ACCEPTED_EVENT);
    expect(q(`[data-action-event='${ACCEPTED_EVENT}']`)).toHaveAttribute("aria-current", "true");
    expect(qa("[data-action-event]")).toHaveLength(1);
    expect(q("[data-action-section='overview']")?.getAttribute("href")).toBe(`/sites/KOBO-001/actions/${ACTION}${query}`);
    expect(q("[data-action-section='execution']")?.getAttribute("href")).toBe(`/sites/KOBO-001/actions/${ACTION}/execution${query}`);
    fireEvent.click(q("[data-action-section='overview']") as HTMLElement);
    await settledScreen();
    expect(where()).toBe(`/sites/KOBO-001/actions/${ACTION}${query}`);
    expect(q("[data-action-application-words]")?.textContent).toBe("Not applied yet");
    expect(q("[data-action-latest-link]")?.getAttribute("href")).toBe(`/sites/KOBO-001/actions/${ACTION}`);
    // Reload: a fresh mount at the same address reads the same selection.
    cleanup();
    mount(path);
    await settledScreen();
    expect(q("[data-action-selection-notice='EVENT_ID']")).not.toBeNull();
    // W1-F4: the verification history read is unselected (never cut to the event); every Action read keeps the selector.
    const gets = s.requests.filter((r) => r.method === "GET" && !r.url.includes("/verification/")).map((r) => r.url);
    expect(gets.length).toBeGreaterThan(0);
    expect(gets.every((url) => url.includes(`event_id=${ACCEPTED_EVENT}`) && !url.includes("recorded_at"))).toBe(true);
    expect(s.unmatched).toEqual([]);
  });

  it("selects a recorded_at cutoff from the URL, keeps it across sections and on reload", async () => {
    const query = `?recorded_at=${encodeURIComponent(OBSERVED_CUTOFF)}`;
    const s = serve(actionReads(hi.action_recorded_at_observed, hi.events_recorded_at_observed, `?recorded_at=${OBSERVED_CUTOFF}`));
    const path = `/sites/KOBO-001/actions/${ACTION}/history${query}`;
    mount(path);
    await settledScreen();
    expect(q("[data-action-selection-notice='RECORDED_AT']")).not.toBeNull();
    expect(qa("[data-action-event-kind]").map((r) => r.getAttribute("data-action-event-kind"))).toEqual(["ACCEPTED", "OBSERVED"]);
    expect(q("[data-action-section='execution']")?.getAttribute("href")).toBe(`/sites/KOBO-001/actions/${ACTION}/execution${query}`);
    fireEvent.click(q("[data-action-section='execution']") as HTMLElement);
    await settledScreen();
    expect(where()).toBe(`/sites/KOBO-001/actions/${ACTION}/execution${query}`);
    expect(screen.queryByRole("button")).toBeNull();
    expect(screen.getByText("Commands are offered on the latest record only.")).toBeInTheDocument();
    cleanup();
    mount(path);
    await settledScreen();
    expect(q("[data-action-selection-notice='RECORDED_AT']")).not.toBeNull();
    // W1-F4: as above, the unselected verification history read is excluded; every Action read keeps the cutoff.
    const gets = s.requests.filter((r) => r.method === "GET" && !r.url.includes("/verification/")).map((r) => decodeURIComponent(r.url));
    expect(gets.length).toBeGreaterThan(0);
    expect(gets.every((url) => url.includes(`recorded_at=${OBSERVED_CUTOFF}`) && !url.includes("event_id"))).toBe(true);
    expect(s.unmatched).toEqual([]);
  });

  it("History row links select an exact event or a recorded cutoff", async () => {
    serve(actionReads(ov.applied_pending_newer_revision, hi.events_latest));
    mount(`/sites/KOBO-001/actions/${ACTION}/history`);
    await settledScreen();
    // W1-F4 trim: the earlier rows are behind the in-place "Show all" toggle.
    showAllHistory();
    const observed = (hi.events_latest.body.events as { id: string; kind: string; recorded_at: string }[]).find((e) => e.kind === "OBSERVED")!;
    expect(q(`[data-action-select-event='${observed.id}']`)?.getAttribute("href")).toBe(
      `/sites/KOBO-001/actions/${ACTION}/history?event_id=${observed.id}`,
    );
    expect(q(`[data-action-select-recorded='${observed.recorded_at}']`)?.getAttribute("href")).toBe(
      `/sites/KOBO-001/actions/${ACTION}/history?recorded_at=${encodeURIComponent(observed.recorded_at)}`,
    );
  });

  it("both selectors together show the typed ACTION_SELECTOR_CONFLICT with no silent preference", async () => {
    const conflict = hi.action_selector_conflict.request.path.split("?")[1];
    serve(actionReads(hi.action_selector_conflict, hi.events_selector_conflict, `?${conflict}`));
    mount(`/sites/KOBO-001/actions/${ACTION}/history?${conflict}`);
    await settledScreen();
    expect(q("[data-action-read='refused']")?.getAttribute("data-action-code")).toBe("ACTION_SELECTOR_CONFLICT");
    expect(q("[data-action-read='refused']")?.getAttribute("data-action-http")).toBe("422");
    expect(qa("[data-action-event]")).toHaveLength(0);
    const links = qa("[data-action-selector-conflict] a").map((a) => a.getAttribute("href") ?? "");
    expect(links).toHaveLength(2);
    expect(links[0]).toMatch(/\?event_id=[^&]+$/);
    expect(links[1]).toMatch(/\?recorded_at=[^&]+$/);
  });

  it("an unknown or wrong-Site Action is not found, with no events shown", async () => {
    const wrong = ov.wrong_site_404;
    serve({
      [wrong.request.path]: served(wrong),
      [`${wrong.request.path}/events`]: served(wrong),
    });
    mount(`/sites/OTHER-001/actions/${ACTION}`);
    await settledScreen();
    // W1-F4: a page-level refusal (not a heading or panel) before the view's panel slot, which keeps its gap.
    expect(q("[data-page-refusal='action'] .page-refusal__title")?.textContent).toBe("Action not found");
    expect(q("[data-action-read='refused']")?.getAttribute("data-action-http")).toBe("404");
    expect(q("[data-panel-gap='action-unread']")?.closest("section.panel")?.querySelector("h2")?.textContent).toBe("Action scope");
    expect(qa("[data-action-event]")).toHaveLength(0);
  });

  it("an unknown event_id is the selection not found, not the Action, with a link to the latest record (M1)", async () => {
    const unknown = hi.unknown_event_404;
    const query = "?event_id=00000000-0000-4000-8000-000000000000";
    expect(unknown.request.path).toBe(`${ACTION_API}${query}`);
    serve({ [unknown.request.path]: served(unknown), [`${ACTION_API}/events${query}`]: served(unknown), ...actionReads(ov.accepted_pending, hi.events_latest) });
    mount(`/sites/KOBO-001/actions/${ACTION}/history${query}`);
    await settledScreen();
    // W1-F4: a page-level refusal title, not a heading; the Action-not-found refusal is absent.
    expect(q("[data-page-refusal='selection-not-found'] .page-refusal__title")?.textContent).toBe("Selected event not found");
    expect(q("[data-page-refusal='action']")).toBeNull();
    expect(document.body.textContent).not.toMatch(/Action not found/);
    expect(document.body.textContent).not.toMatch(/no such action/i);
    expect(q("[data-action-read='selection-not-found']")?.getAttribute("data-action-code")).toBe("ACTION_EVENT_NOT_FOUND");
    const latest = q("[data-action-open-latest]") as HTMLAnchorElement;
    expect(latest).toHaveAttribute("href", `/sites/KOBO-001/actions/${ACTION}/history`);
    fireEvent.click(latest);
    await settledScreen();
    expect(where()).toBe(`/sites/KOBO-001/actions/${ACTION}/history`);
    expect(q("[data-action-id]")?.getAttribute("data-action-id")).toBe(ACTION);
  });

  it("an unknown Action section is refused", async () => {
    serve(actionReads(ov.accepted_pending, hi.events_latest));
    mount(`/sites/KOBO-001/actions/${ACTION}/forecast`);
    await settledScreen();
    expect(q("[data-action-read='section-not-found']")).not.toBeNull();
  });
});

describe("W1-UX-04 phase 1 (W1-F4: merged into the v69 panels): Application and History state", () => {
  function w1Scan(page: string) {
    const main = document.body.querySelector("main") as HTMLElement;
    const w1 = scanProductVocabulary(main, page, { set: "w1" });
    expect(w1.scanned).toBeGreaterThan(10);
    expect(w1.violations, describeViolations(w1.violations)).toEqual([]);
  }

  it("Application: pending and applied are never positive; the state line, scope and as-of stay outside the closed disclosure", async () => {
    for (const [fixture, label, tone] of [
      [ov.accepted_pending, "Not applied yet", "waiting"],
      [ov.applied_pending_newer_revision, "Applied; effect not yet measured", "limited"],
    ] as const) {
      serve(actionReads(fixture, hi.events_latest));
      const view = mount(`/sites/KOBO-001/actions/${ACTION}/execution`);
      await settledScreen();
      w1Scan(`action-execution (W1) ${label}`);
      // W1-F4: the former "Work done" card is merged into the single "Activity log" panel.
      const card = panelTitled("Activity log");
      expect(expectStateLineVisible(card)).toBe(label);
      expect(card.querySelector("[data-product-status]")?.getAttribute("data-product-status")).toBe(tone);
      const disclosure = scanDisclosureVocabulary(card, "action-execution disclosure");
      expect(disclosure.disclosures).toBe(1);
      expect(disclosure.violations, describeViolations(disclosure.violations)).toEqual([]);
      // W1-F4: the four-step strip became the Application, Attempts and Trial outcome key values.
      expect(card.querySelector("[data-key-value='attempts']")?.textContent).toMatch(/\d+ recorded, \d+ failed/);
      expect(card.querySelector("[data-key-value='trial']")).not.toBeNull();
      expect(card.querySelector("[data-action-work-verification-link]")?.getAttribute("href")).toContain("/verification");
      expect(card.textContent).not.toMatch(/saving (?:of|was|is achieved)|reduced generator|verified/i);
      view.unmount();
    }
  });

  it("History: latest record and an earlier selected event; the historical state is never current", async () => {
    serve(actionReads(ov.applied_pending_newer_revision, hi.events_latest));
    let view = mount(`/sites/KOBO-001/actions/${ACTION}/history`);
    await settledScreen();
    w1Scan("action-history (W1) latest");
    // W1-F4: the former History card is merged into the single "Action history" panel; its step strip is the table.
    let card = panelTitled("Action history");
    expect(expectStateLineVisible(card)).toBe("Every recorded event");
    // W1-F4 trim: every event is one click away, on the in-place toggle.
    showAllHistory();
    expect(card.querySelectorAll("[data-action-event]").length).toBe((hi.events_latest.body.events as unknown[]).length);
    view.unmount();

    // Derived events read, as in the exact event_id test above: the latest events through the ACCEPTED event.
    const selection = hi.action_event_id_accepted.body.selection;
    const events = { status: 200, body: { ...hi.events_latest.body, selection, events: hi.events_latest.body.events.slice(0, 1) } };
    serve(actionReads(hi.action_event_id_accepted, events, `?event_id=${ACCEPTED_EVENT}`));
    view = mount(`/sites/KOBO-001/actions/${ACTION}/history?event_id=${ACCEPTED_EVENT}`);
    await settledScreen();
    card = panelTitled("Action history");
    const shown = expectStateLineVisible(card);
    expect(card.querySelector("[data-product-status]")?.getAttribute("data-product-status")).not.toBe("positive");
    expect(shown).not.toMatch(/current/i);
    expect(card.querySelector("[data-action-history-latest-link]")).not.toBeNull();
    expect(where()).toContain(`event_id=${ACCEPTED_EVENT}`);
    view.unmount();
  });
});

describe("W1-F4: Recommendation state line (was the W1-UX-04 answer card, now the v69 strip and panel 1)", () => {
  function w1Scan(page: string) {
    const main = document.body.querySelector("main") as HTMLElement;
    const w1 = scanProductVocabulary(main, page, { set: "w1" });
    expect(w1.scanned).toBeGreaterThan(10);
    expect(w1.violations, describeViolations(w1.violations)).toEqual([]);
  }

  for (const [name, label, tone, change] of [
    ["pre_accept_available", "Trial proposed; not accepted", "waiting", true],
    ["pre_accept_unavailable", "No trial proposed", "limited", false],
    ["accepted_snapshot_live_status", "Accepted; result not yet known", "limited", true],
    ["latest_revision_after_apply", "Held: an earlier trial is still open", "waiting", false],
  ] as const) {
    it(`${name}: the state line, scope and as-of stay outside the closed disclosure; never positive`, async () => {
      const fixture = rec[name];
      serve({ [fixture.request.path]: served(fixture) });
      mount(fixture.request.path.replace("/api", ""));
      await settledScreen();
      w1Scan(`recommendation (W1) ${name}`);
      expect(q("[data-headline-card]")).toBeNull();
      const strip = q(".status-strip[data-product-status]") as HTMLElement;
      expect(expectStateLineVisible(strip.parentElement as HTMLElement)).toBe(label);
      expect(strip.getAttribute("data-product-status")).toBe(tone);
      const claim = q("#site-recommendation-heading")?.closest(".panel")?.querySelector(".w1f4-recommendation__claim") as HTMLElement;
      if (change) expect(claim.textContent).toMatch(/20%.*to.*15%/);
      else expect(claim.textContent).not.toMatch(/to.*15%/);
      expect(q("[data-recommendation-next]")?.textContent?.length).toBeGreaterThan(10);
      const disclosure = scanDisclosureVocabulary(strip, `recommendation disclosure ${name}`);
      expect(disclosure.disclosures).toBe(1);
      expect(disclosure.violations, describeViolations(disclosure.violations)).toEqual([]);
      for (const el of [strip, claim, q("[data-recommendation-next]") as HTMLElement]) {
        expect(el.textContent).not.toMatch(/saving (?:of|was|is achieved)|verified/i);
      }
      expect(document.body.textContent).not.toMatch(/Input digest/);
    });
  }
});

/* W5-02 K2a (P-K2a-34/36, U1): both Action kinds on one COLDCHAIN Site, by route form plus the validated domain read. */
describe("W1 and domain Action IDs on one cold Site", () => {
  const coldDetail: SiteDetailClient = {
    getSite: async (siteId: string) => ({ status: "loaded", site: { ...COLD_SITE, site_id: siteId } }),
  } as SiteDetailClient;
  const DOMAIN_API = `/api/sites/KOBO-001/domain-work/actions/${DOMAIN_ID}`;
  const W1_ON_DOMAIN_API = `/api/sites/KOBO-001/domain-work/actions/${ACTION}`;
  const notFound: Served = { status: 404, body: { detail: { code: "ACTION_NOT_FOUND", message: "Action was not found at this site.", intent: null, results: null } } };
  const domainLoaded: Served = { status: 200, body: detailBody({ site_code: "KOBO-001" }) };

  function mountCold(path: string) {
    return render(
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          {["/sites/:siteId/actions/:actionId", "/sites/:siteId/actions/:actionId/:actionView"].map((p) => (
            <Route key={p} path={p} element={<><SiteActionFrame detail={coldDetail} sitesPath="/sites" /><Where /></>} />
          ))}
        </Routes>
      </MemoryRouter>,
    );
  }

  it("a W1 ID at its bare address keeps the W1 battery detail and its six sections", async () => {
    const s = serve({ ...actionReads(ov.applied_pending_newer_revision, hi.events_latest), [W1_ON_DOMAIN_API]: notFound });
    mountCold(`/sites/KOBO-001/actions/${ACTION}`);
    await settledScreen();
    await waitFor(() => expect(screen.getByRole("heading", { level: 1 }).textContent).toContain("Battery reserve trial"));
    expect(qa("[data-action-section]").map((a) => a.textContent)).toHaveLength(6);
    expect(q("[data-domain-action-shell]")).toBeNull();
    expect(where()).toBe(`/sites/KOBO-001/actions/${ACTION}`);
    expect(s.unmatched).toEqual([]);
  });

  it("a domain ID at its bare address redirects to /verification and renders the domain shell (direct reload)", async () => {
    const s = serve({ [DOMAIN_API]: domainLoaded });
    mountCold(`/sites/KOBO-001/actions/${DOMAIN_ID}`);
    await waitFor(() => expect(where()).toBe(`/sites/KOBO-001/actions/${DOMAIN_ID}/verification`));
    await settledScreen();
    expect(q('[data-domain-action-shell="loaded"]')).not.toBeNull();
    expect(s.requests.every((r) => !r.url.startsWith(`/api/sites/KOBO-001/actions/`))).toBe(true);
  });

  it("a W1 ID on /verification of a cold Site is not found and never falls back to the W1 read", async () => {
    const s = serve({ [W1_ON_DOMAIN_API]: notFound });
    mountCold(`/sites/KOBO-001/actions/${ACTION}/verification`);
    await settledScreen();
    expect(q('[data-domain-action-panel="not-found"]')?.textContent).toBe("Action was not found at this site.");
    expect(s.requests.map((r) => r.url)).toEqual([W1_ON_DOMAIN_API]);
  });

  it("a mini-grid Site never requests the domain Action read", async () => {
    const s = serve(actionReads(ov.applied_pending_newer_revision, hi.events_latest));
    mount(`/sites/KOBO-001/actions/${ACTION}`);
    await settledScreen();
    expect(s.requests.some((r) => r.url.includes("/domain-work/"))).toBe(false);
  });
});

/* W5-04 V4a (readiness rulings 42, 43): an EV_CHARGING Site dispatches a domain Action ID to the domain read only. */
describe("W1 and EV domain Action IDs on one EV Site", () => {
  const evDetail: SiteDetailClient = {
    getSite: async (siteId: string) => ({ status: "loaded", site: { ...EV_SITE, site_id: siteId } }),
  } as SiteDetailClient;
  const DOMAIN_API = `/api/sites/KOBO-001/domain-work/actions/${DOMAIN_ID}`;
  const W1_ON_DOMAIN_API = `/api/sites/KOBO-001/domain-work/actions/${ACTION}`;
  const notFound: Served = { status: 404, body: { detail: { code: "ACTION_NOT_FOUND", message: "Action was not found at this site.", intent: null, results: null } } };
  const evLoaded: Served = { status: 200, body: detailBody({ site_code: "KOBO-001", action: { ...detailBody().action, domain: "EV_CHARGING" } }) };

  function mountEv(path: string) {
    return render(
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          {["/sites/:siteId/actions/:actionId", "/sites/:siteId/actions/:actionId/:actionView"].map((p) => (
            <Route key={p} path={p} element={<><SiteActionFrame detail={evDetail} sitesPath="/sites" /><Where /></>} />
          ))}
        </Routes>
      </MemoryRouter>,
    );
  }

  it.each(["", "/verification"])("an EV domain ID at `%s` makes no W1 battery request", async (section) => {
    const s = serve({ [DOMAIN_API]: evLoaded });
    mountEv(`/sites/KOBO-001/actions/${DOMAIN_ID}${section}`);
    await waitFor(() => expect(where()).toBe(`/sites/KOBO-001/actions/${DOMAIN_ID}/verification`));
    await settledScreen();
    expect(q('[data-domain-action-shell="loaded"]')).not.toBeNull();
    expect(s.requests.length).toBeGreaterThan(0);
    expect(s.requests.every((r) => r.url.split("?")[0] === DOMAIN_API)).toBe(true);
    expect(s.requests.some((r) => r.url.startsWith(`/api/sites/KOBO-001/actions/`))).toBe(false);
  });

  it("an EV domain ID at `/plan` is not served: no redirect, no Action read (post-W6 W5-EV R350)", async () => {
    const s = serve({ [DOMAIN_API]: evLoaded });
    mountEv(`/sites/KOBO-001/actions/${DOMAIN_ID}/plan`);
    await settledScreen();
    expect(where()).toBe(`/sites/KOBO-001/actions/${DOMAIN_ID}/plan`);
    expect(q("[data-action-unknown-section]")).not.toBeNull();
    expect(s.requests).toHaveLength(0);
  });

  it("a W1 ID at its bare address on an EV Site keeps the W1 battery detail (ruling 43 fallback)", async () => {
    const s = serve({ ...actionReads(ov.applied_pending_newer_revision, hi.events_latest), [W1_ON_DOMAIN_API]: notFound });
    mountEv(`/sites/KOBO-001/actions/${ACTION}`);
    await settledScreen();
    await waitFor(() => expect(screen.getByRole("heading", { level: 1 }).textContent).toContain("Battery reserve trial"));
    expect(q("[data-domain-action-shell]")).toBeNull();
    expect(s.unmatched).toEqual([]);
  });
});

describe("post-W6 shell R203: the W1 Action breadcrumb is Action-rooted", () => {
  const sections = [
    ["", "Overview"],
    ["/plan", "Plan"],
    ["/execution", "Application"],
    ["/evidence", "Evidence"],
    ["/history", "History"],
    ["/verification", "Verification"],
  ] as const;

  it.each(sections)("reads Actions › code › section · site for %s", async (segment, label) => {
    serve(actionReads(ov.applied_pending_newer_revision, hi.events_latest));
    mount(`/sites/KOBO-001/actions/${ACTION}${segment}`);
    await settledScreen();
    await waitFor(() => expect(q("[data-action-crumb-code]")).not.toBeNull());
    const crumbs = screen.getByRole("navigation", { name: "Breadcrumb" });
    const items = Array.from(crumbs.querySelectorAll("li")).map((li) => li.textContent);
    expect(items).toEqual(["Actions", ov.applied_pending_newer_revision.body.action.action_code, label]);
    expect(crumbs.querySelector("li a")?.getAttribute("href")).toBe("/actions");
    expect(crumbs.querySelector('[aria-current="page"]')?.textContent).toBe(label);
    expect(crumbs.querySelector("[data-action-crumb-site]")?.textContent).toBe(`· site: ${HYBRID_MINI_GRID_SITE.display_name}`);
    expect(crumbs.querySelector("[data-action-crumb-site] a")?.getAttribute("href")).toBe("/sites/KOBO-001");
    expect(crumbs.textContent).not.toContain("Findings");
  });

  it("shows no code crumb while the Action read is pending", async () => {
    vi.stubGlobal("fetch", () => new Promise<Response>(() => undefined));
    mount(`/sites/KOBO-001/actions/${ACTION}/plan`);
    await waitFor(() => expect(screen.getByRole("navigation", { name: "Breadcrumb" })).toBeTruthy());
    const crumbs = screen.getByRole("navigation", { name: "Breadcrumb" });
    expect(q("[data-action-crumb-code]")).toBeNull();
    expect(Array.from(crumbs.querySelectorAll("li")).map((li) => li.textContent)).toEqual(["Actions", "Plan"]);
  });
});

// --- post-W6 W1-b Q26/Q27/Q33/Q35 (R204/R205/R222/R229) and Q26 retained Finding tabs (R383) ------------------------

describe("post-W6 W1-b: Action and Finding frame chrome", () => {
  const SITE = HYBRID_MINI_GRID_SITE.display_name;
  const siteTabs = () => screen.queryAllByRole("navigation", { name: "Site sections" });
  const sectionRow = () => screen.getByRole("navigation", { name: "Action sections" });
  const subtitle = () => document.querySelector(".page-header__subtitle")?.textContent;

  it.each(["", "/plan", "/execution", "/evidence", "/history"])(
    "the Action view '%s' has no Site tab row, an Open site header action and the loaded subtitle",
    async (section) => {
      serve(actionReads(ov.accepted_pending, hi.events_latest));
      mount(`/sites/KOBO-001/actions/${ACTION}${section}`);
      await settledScreen();
      await waitFor(() => expect(q("[data-action-crumb-code]")).not.toBeNull());
      expect(siteTabs()).toHaveLength(0);
      expect(q("[data-mock-deviation]")).toBeNull();
      const open = within(document.querySelector(".page-header__actions") as HTMLElement).getByRole("link", { name: "Open site" });
      expect(open).toHaveAttribute("href", "/sites/KOBO-001");
      expect(subtitle()).toBe(`${SITE} · an action raised from a finding`);
    },
  );

  it("a pending Action read shows only the Site in the subtitle", async () => {
    serve({});
    mount(`/sites/KOBO-001/actions/${ACTION}`);
    await waitFor(() => expect(document.querySelector("h1")).not.toBeNull());
    expect(q("[data-action-crumb-code]")).toBeNull();
    expect(subtitle()).toBe(SITE);
  });

  it("/overview is an alias of the bare Action route, with Overview selected", async () => {
    serve(actionReads(ov.accepted_pending, hi.events_latest));
    mount(`/sites/KOBO-001/actions/${ACTION}/overview`);
    await settledScreen();
    expect(q("[data-action-read='section-not-found']")).toBeNull();
    expect(within(sectionRow()).getByRole("link", { current: "page" })).toHaveTextContent("Overview");
  });

  it("an unknown section keeps the Action h1 and section row, states the segment as text and links the overview", async () => {
    serve(actionReads(ov.accepted_pending, hi.events_latest));
    const segment = "<b>forecast</b>";
    mount(`/sites/KOBO-001/actions/${ACTION}/${encodeURIComponent(segment)}`);
    await settledScreen();
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Action");
    expect(within(sectionRow()).queryByRole("link", { current: "page" })).toBeNull();
    expect(within(sectionRow()).getAllByRole("link")).toHaveLength(6);
    const body = q("[data-action-read='section-not-found']") as HTMLElement;
    expect(body.textContent).toBe(`This Action has no section called '${segment}'. Open the Action overview.`);
    expect(body.querySelector("b")).toBeNull();
    expect(screen.getByRole("link", { name: "Open Action overview" })).toHaveAttribute("href", `/sites/KOBO-001/actions/${ACTION}`);
    expect(subtitle()).toBe(SITE);
    expect(siteTabs()).toHaveLength(0);
  });

  it.each([
    ["overview", "", true],
    ["Analysis", "?view=analysis", true],
    ["evidence", "/evidence", true],
    ["history", "/history", true],
    ["alternatives", "/alternatives", false],
    ["recommendation", "/recommendation", false],
  ])("the Finding %s keeps its Site tabs with one R383 label only where the row is retained", async (_name, suffix, retained) => {
    serve({});
    const [path, search] = suffix.startsWith("?") ? ["", suffix] : [suffix, ""];
    mount(`/sites/KOBO-001/findings/f0000000-0000-4000-8000-000000000001${path}${search}`);
    await waitFor(() => expect(document.querySelector("main")).not.toBeNull());
    await settledScreen();
    expect(siteTabs()).toHaveLength(retained ? 1 : 0);
    // post-W6 W4 R453: the shared Site tab row carries its own wrap label inside the row; count the others.
    const labels = qa("[data-mock-deviation]:not([data-mock-deviation='R453'])");
    expect(labels).toHaveLength(retained ? 1 : 0);
    expect(qa("[data-mock-deviation='R453']")).toHaveLength(retained ? 1 : 0);
    if (retained) {
      expect(siteTabs()[0].querySelector("[data-mock-deviation='R453']")).not.toBeNull();
      expect(labels[0]).toHaveAttribute("data-mock-deviation", "R383");
      expect(labels[0].textContent).toBe("MOCK DEVIATION D2 (R383)");
      expect(siteTabs()[0].nextElementSibling).toBe(labels[0]);
    }
  });
});

// --- post-W6 W1-b Q29/Q30 (R218/R219): resolution events and history counts ------------------------------------------

describe("post-W6 W1-b: Action history resolution rows and counts", () => {
  const base = () => structuredClone(hi.events_latest.body) as any;
  const ev = (id: string, kind: string, at: string) => ({
    ...structuredClone(base().events[0]),
    id,
    kind,
    recorded_at: at,
    occurred_at: at,
    occurred_before_recorded: false,
  });
  const res = (id: string, kind: string, at: string) => ({
    id,
    kind,
    recorded_at: at,
    verification_plan_id: null,
    verification_outcome_id: null,
    triggering_job: null,
    payload: {},
  });
  function reads(events: any[], resolutions: any[] = []) {
    const body = base();
    body.events = events;
    const h = structuredClone((verificationContract as any).responses.history);
    h.action_id = ACTION;
    h.outcomes = [];
    h.resolution_events = resolutions;
    return {
      ...actionReads(ov.applied_pending_newer_revision, { status: 200, body }),
      [`${ACTION_API}/verification/history`]: { status: 200, body: h } as Served,
    };
  }
  const at = (n: number) => `2026-10-0${n}T08:00:00Z`;
  const rows = () => qa("[data-action-event], [data-action-history-outcome], [data-action-history-resolution]");

  it("shows a resolution once, as its detailed row, with the ruled meanings and no duplicate-key warning", async () => {
    const errors = vi.spyOn(console, "error").mockImplementation(() => undefined);
    serve(
      reads(
        [ev("e-accepted", "ACCEPTED", at(1)), ev("r-1", "RESOLVED", at(2)), ev("r-2", "RESOLUTION_WITHDRAWN", at(3))],
        [res("r-1", "RESOLVED", at(2)), res("r-2", "RESOLUTION_WITHDRAWN", at(3))],
      ),
    );
    mount(`/sites/KOBO-001/actions/${ACTION}/history`);
    await settledScreen();
    await waitFor(() => expect(q("[data-action-history-resolution-id='r-1']")).not.toBeNull());
    expect(rows()).toHaveLength(3);
    expect(q("[data-action-event='r-1']")).toBeNull();
    expect(q("[data-action-event='r-2']")).toBeNull();
    expect(q("[data-action-history-resolution-id='r-1']")?.textContent).toContain("Resolved");
    expect(q("[data-action-history-resolution-id='r-1']")?.textContent).toContain("The evaluator settled the outcome for this Action.");
    expect(q("[data-action-history-resolution-id='r-2']")?.textContent).toContain("Resolution withdrawn");
    expect(q("[data-action-history-resolution-id='r-2']")?.textContent).toContain(
      "The evaluator withdrew an earlier outcome; the Action is open for a new outcome.",
    );
    // Three de-duplicated entries: no truncation sentence and no toggle.
    expect(q("[data-action-history-truncated]")).toBeNull();
    expect(q("[data-action-history-show-all]")).toBeNull();
    expect(errors.mock.calls.filter((c) => String(c[0]).includes("same key"))).toEqual([]);
    errors.mockRestore();
  });

  it("an Action-only resolution or unknown event has its own meaning and never reads as accepted", async () => {
    serve(reads([ev("r-9", "RESOLVED", at(1)), ev("x-1", "SOMETHING_NEW", at(2))]));
    mount(`/sites/KOBO-001/actions/${ACTION}/history`);
    await settledScreen();
    await waitFor(() => expect(q("[data-action-event='x-1']")).not.toBeNull());
    const resolved = q("[data-action-event='r-9']") as HTMLElement;
    expect(resolved.textContent).toContain("Resolved");
    expect(resolved.textContent).toContain("The evaluator settled the outcome for this Action.");
    const unknown = q("[data-action-event='x-1']") as HTMLElement;
    expect(unknown.textContent).toContain("Recorded event; its meaning is not shown in this build.");
    expect(unknown.textContent).not.toMatch(/accepted/i);
    expect(unknown.textContent).not.toContain("SOMETHING_NEW");
  });

  it.each([
    ["zero", 0],
    ["three", 3],
  ])("with %s entries every entry shows, with the chip and no truncation sentence or toggle", async (_name, n) => {
    serve(reads(Array.from({ length: n }, (_, i) => ev(`e-${i}`, "OBSERVED", at(i + 1)))));
    mount(`/sites/KOBO-001/actions/${ACTION}/history`);
    await settledScreen();
    await waitFor(() => expect(q("[data-action-history-latest]")).not.toBeNull());
    expect(q("[data-action-history-latest]")?.textContent).toBe("Latest at read time");
    expect(qa("[data-action-event]")).toHaveLength(n);
    expect(q("[data-action-history-truncated]")).toBeNull();
    expect(q("[data-action-history-show-all]")).toBeNull();
    expect(document.body.textContent).not.toMatch(/Latest at read time: \d+ of \d+ events/);
  });

  it("with exactly four de-duplicated entries it states the truncation, offers Show all, and Show the latest 3 when expanded", async () => {
    serve(
      reads(
        [ev("e-1", "OBSERVED", at(1)), ev("e-2", "OBSERVED", at(2)), ev("e-3", "OBSERVED", at(3)), ev("r-1", "RESOLVED", at(4))],
        [res("r-1", "RESOLVED", at(4))],
      ),
    );
    mount(`/sites/KOBO-001/actions/${ACTION}/history`);
    await settledScreen();
    await waitFor(() => expect(q("[data-action-history-show-all]")).not.toBeNull());
    expect(q("[data-action-history-truncated]")?.textContent?.trim()).toBe(
      "Showing the latest 3 of 4 recorded entries; show all to see every entry.",
    );
    expect(q("[data-action-history-show-all]")?.textContent).toBe("Show all 4 entries");
    expect(rows()).toHaveLength(3);
    showAllHistory();
    expect(rows()).toHaveLength(4);
    expect(q("[data-action-history-show-all]")?.textContent).toBe("Show the latest 3");
    expect(q("[data-action-history-truncated]")).toBeNull();
  });

  describe("Action history entries scroll region (caps ruling 2)", () => {
    const stubSizes = (scrollHeight: number, clientHeight: number) => {
      Object.defineProperty(HTMLElement.prototype, "scrollHeight", { configurable: true, get: () => scrollHeight });
      Object.defineProperty(HTMLElement.prototype, "clientHeight", { configurable: true, get: () => clientHeight });
    };
    afterEach(() => {
      delete (HTMLElement.prototype as unknown as Record<string, unknown>).scrollHeight;
      delete (HTMLElement.prototype as unknown as Record<string, unknown>).clientHeight;
      vi.unstubAllGlobals();
    });

    it("holds the header and every row in one focusable region; the toggle and count stay outside; the cue is hidden when it fits", async () => {
      serve(reads([ev("e-1", "OBSERVED", at(1)), ev("e-2", "OBSERVED", at(2)), ev("e-3", "OBSERVED", at(3)), ev("e-4", "OBSERVED", at(4))], []));
      mount(`/sites/KOBO-001/actions/${ACTION}/history`);
      await settledScreen();
      const region = screen.getByRole("region", { name: "Action history entries" });
      expect(region.getAttribute("tabindex")).toBe("0");
      expect(region.querySelector("thead")).not.toBeNull();
      expect(region.querySelectorAll("tbody tr").length).toBe(3);
      expect(region.contains(q("[data-action-history-show-all]"))).toBe(false);
      expect(region.contains(q("[data-action-history-truncated]"))).toBe(false);
      expect(q("[data-action-history-scroll-cue]")?.hasAttribute("hidden")).toBe(true);
      showAllHistory();
      expect(region.querySelectorAll("tbody tr").length).toBe(4);
    });

    it("shows the cue only when the region overflows, re-measured by the ResizeObserver", async () => {
      const callbacks: Array<() => void> = [];
      class FakeObserver {
        constructor(cb: () => void) {
          callbacks.push(cb);
        }
        observe() {}
        disconnect() {}
      }
      vi.stubGlobal("ResizeObserver", FakeObserver);
      stubSizes(300, 300);
      serve(reads([ev("e-1", "OBSERVED", at(1)), ev("e-2", "OBSERVED", at(2))], []));
      mount(`/sites/KOBO-001/actions/${ACTION}/history`);
      await settledScreen();
      const cue = () => q("[data-action-history-scroll-cue]");
      expect(cue()?.hasAttribute("hidden")).toBe(true);
      stubSizes(900, 500);
      act(() => callbacks.forEach((cb) => cb()));
      expect(cue()?.hasAttribute("hidden")).toBe(false);
      expect(cue()?.textContent).toBe("Scroll history to see every entry");
      stubSizes(300, 300);
      act(() => callbacks.forEach((cb) => cb()));
      expect(cue()?.hasAttribute("hidden")).toBe(true);
    });
  });
});
