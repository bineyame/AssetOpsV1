/**
 * W1-F4 (`D-2026-10-17-mockup-layout-spec`), group C1: the Action page views
 * `action-overview`, `action-execution` and `action-history` each render exactly
 * their single v69 panel (Action scope, Activity log, Action history) in
 * stocked, empty, historical-selection and refused variants, with every
 * unsupported read stated inside the panel slot and no leading answer card.
 * When the Action itself cannot be read, the shell keeps the selected view's
 * slots for every Action section, including Plan, Evidence and Verification.
 *
 * Bodies are the committed S6 wire contracts served through a stubbed `fetch`
 * (the real clients and the real route). Derived bodies, each marked where it
 * is built: an events read with no events; a verification history with no
 * outcome; a 503 store-unavailable events or verification read (no recorded
 * case exists); the recorded verification history with distinct placeholder IDs.
 */
import { cleanup, render } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import contract from "../../../../backend/tests/fixtures/s6_action_api_contract.json";
import verificationContract from "../../../../backend/tests/fixtures/s6_verification_api_contract.json";
import { SiteActionFrame } from "../../shell/SiteAnalyticsFrames";
import { expectV69Panels, panelTitled } from "../../test/panelStructure";
import { settledScreen } from "../../test/settled";
import type { SiteDetailClient } from "../siteDirectoryClient";
import { HYBRID_MINI_GRID_SITE } from "./sldFixtures";

type Case = { request: { method: string; path: string }; status: number; body: any };
type Served = { status: number; body: unknown };
const M = contract.manifest as unknown as Record<string, Record<string, Case>>;
const ov = M["action-overview:1#a"];
const hi = M["action-history:1#a"];
const ACTION = ov.accepted_pending.body.action.id as string;
const ACCEPTED_EVENT = hi.action_event_id_accepted.body.selection.event_id as string;
const API = `/api/sites/KOBO-001/actions/${ACTION}`;
const UNAVAILABLE: Served = { status: 503, body: { detail: { code: "STORE_UNAVAILABLE", message: "The store could not be read." } } };

const served = (c: Case): Served => ({ status: c.status, body: c.body });

function key(url: string): string {
  const [path, query = ""] = url.split("?");
  const params = query
    .split("&")
    .filter(Boolean)
    .map((pair) => pair.split("=").map(decodeURIComponent) as [string, string])
    .sort(([a], [b]) => a.localeCompare(b));
  return `${decodeURIComponent(path)}${params.length ? `?${params.map(([k, v]) => `${k}=${v}`).join("&")}` : ""}`;
}

function serve(gets: Record<string, Served>) {
  const table = new Map(Object.entries(gets).map(([url, value]) => [key(url), value]));
  vi.stubGlobal("fetch", async (url: string) => {
    const hit = table.get(key(url));
    if (!hit) return new Response(JSON.stringify({ detail: { code: "TEST_UNMATCHED", message: url } }), { status: 599 });
    return new Response(JSON.stringify(hit.body), { status: hit.status });
  });
}

/** Derived: the recorded verification history with distinct placeholder IDs, for this Action. */
function verificationHistory(empty = false): Served {
  const h = structuredClone((verificationContract as any).responses.history);
  h.action_id = ACTION;
  h.outcomes.forEach((o: any, i: number) => {
    o.outcome_id = `outcome-${i + 1}`;
  });
  h.resolution_events.forEach((r: any, i: number) => {
    r.id = `resolution-${i + 1}`;
    r.verification_outcome_id = "outcome-1";
  });
  if (empty) {
    h.outcomes = [];
    h.resolution_events = [];
  }
  return { status: 200, body: h };
}

function reads(action: Served, events: Served, history: Served = verificationHistory(), query = "") {
  return {
    [`${API}${query}`]: action,
    [`${API}/events${query}`]: events,
    [`${API}/verification/history`]: history,
  };
}

/** Derived: the recorded latest events read with no events in it. */
const noEvents = (): Served => ({ status: 200, body: { ...hi.events_latest.body, events: [] } });

const detail: SiteDetailClient = {
  getSite: async (siteId: string) => ({ status: "loaded", site: { ...HYBRID_MINI_GRID_SITE, site_id: siteId } }),
} as SiteDetailClient;

function mount(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        {["/sites/:siteId/actions/:actionId", "/sites/:siteId/actions/:actionId/:actionView"].map((p) => (
          <Route key={p} path={p} element={<SiteActionFrame detail={detail} sitesPath="/sites" />} />
        ))}
      </Routes>
    </MemoryRouter>,
  );
}

const SCREENS = [
  ["action-overview", "", "Action scope"],
  ["action-execution", "/execution", "Activity log"],
  ["action-history", "/history", "Action history"],
] as const;

const q = (selector: string) => document.body.querySelector(selector);
const noCard = () => expect(q("[data-headline-card]")).toBeNull();

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("W1-F4 C1: the Action views keep their single v69 panel in every variant", () => {
  it.each(SCREENS)("stocked: %s", async (screenId, segment, title) => {
    serve(reads(served(ov.applied_pending_newer_revision), served(hi.events_latest)));
    mount(`/sites/KOBO-001/actions/${ACTION}${segment}`);
    await settledScreen();
    expectV69Panels(screenId);
    noCard();
    expect(q("[data-page-refusal]")).toBeNull();
    const panel = panelTitled(title);
    expect(panel.querySelector("[data-product-status-label]")).not.toBeNull();
    expect(panel.querySelector("[data-action-selection-notice='LATEST']")).not.toBeNull();
  });

  it("stocked overview: the mock's key values, with the absent owner stated in its row", async () => {
    serve(reads(served(ov.applied_pending_newer_revision), served(hi.events_latest)));
    mount(`/sites/KOBO-001/actions/${ACTION}`);
    await settledScreen();
    const panel = panelTitled("Action scope");
    const terms = Array.from(panel.querySelectorAll(".v69-key-values dt")).map((dt) => dt.textContent);
    for (const term of ["Action", "Source", "Owner", "Intervention", "Outcome"]) expect(terms).toContain(term);
    expect(panel.querySelector("[data-key-value='owner'] [data-panel-gap='owner']")?.textContent).toBe("Not recorded");
    expect(panel.querySelectorAll("details[data-exact-references]")).toHaveLength(1);
  });

  it("stocked execution: the log is Record | State | Evidence with the application state and command context in the panel", async () => {
    serve(reads(served(ov.capability_denied), served(hi.events_latest)));
    mount(`/sites/KOBO-001/actions/${ACTION}/execution`);
    await settledScreen();
    expectV69Panels("action-execution");
    const panel = panelTitled("Activity log");
    expect(Array.from(panel.querySelectorAll("thead th")).map((th) => th.textContent).slice(0, 3)).toEqual(["Record", "State", "Evidence"]);
    expect(panel.querySelector("[data-action-command-unavailable]")).not.toBeNull();
    expect(panel.querySelector("[data-action-work-headline]")).not.toBeNull();
  });

  it("stocked history: Event | Meaning, exact selection links, and earlier/current outcome rows with the withdrawable resolution", async () => {
    serve(reads(served(ov.applied_pending_newer_revision), served(hi.events_latest)));
    mount(`/sites/KOBO-001/actions/${ACTION}/history`);
    await settledScreen();
    const panel = panelTitled("Action history");
    expect(Array.from(panel.querySelectorAll("thead th")).map((th) => th.textContent).slice(0, 2)).toEqual(["Event", "Meaning"]);
    expect(panel.querySelectorAll("[data-action-select-event]").length).toBe((hi.events_latest.body.events as unknown[]).length);
    const labels = Array.from(panel.querySelectorAll("[data-action-history-outcome-label]")).map((b) => b.getAttribute("data-action-history-outcome-label"));
    expect(labels).toEqual(["earlier", "current"]);
    expect(panel.querySelector("[data-action-history-resolution='RESOLUTION_WITHDRAWN']")?.textContent).toMatch(/not permanent/);
    expect(panel.querySelector("[data-action-history-outcomes='listed']")?.textContent).toMatch(/later evidence can withdraw it/);
  });

  it.each([
    ["action-execution", "/execution", "Activity log"],
    ["action-history", "/history", "Action history"],
  ] as const)("empty: %s states no activity inside its panel", async (screenId, segment, title) => {
    serve(reads(served(ov.accepted_pending), noEvents(), verificationHistory(true)));
    mount(`/sites/KOBO-001/actions/${ACTION}${segment}`);
    await settledScreen();
    expectV69Panels(screenId);
    noCard();
    const panel = panelTitled(title);
    expect(panel.querySelector("[data-action-events='none']")?.textContent).toBe("No activity recorded.");
    if (screenId === "action-history") {
      expect(panel.querySelector("[data-action-history-outcomes='none']")?.textContent).toBe("No trial outcome recorded yet.");
    }
  });

  it("empty: action-overview with no change and no plan keeps the pending outcome and the owner gap in its panel", async () => {
    serve(reads(served(ov.accepted_pending), noEvents()));
    mount(`/sites/KOBO-001/actions/${ACTION}`);
    await settledScreen();
    expectV69Panels("action-overview");
    noCard();
    const panel = panelTitled("Action scope");
    expect(panel.querySelector("[data-key-value='change']")).toBeNull();
    expect(panel.querySelector("[data-panel-gap='owner']")).not.toBeNull();
    expect(panel.querySelector("[data-product-status]")?.getAttribute("data-product-status")).not.toBe("positive");
  });

  it.each(SCREENS)("historical event selection: %s states the earlier record inside its panel, not as a panel", async (screenId, segment, title) => {
    const query = `?event_id=${ACCEPTED_EVENT}`;
    const selection = hi.action_event_id_accepted.body.selection;
    // Derived: the recorded latest events through the ACCEPTED event, with the recorded selection.
    const events = { status: 200, body: { ...hi.events_latest.body, selection, events: hi.events_latest.body.events.slice(0, 1) } };
    serve(reads(served(hi.action_event_id_accepted), events, verificationHistory(), query));
    mount(`/sites/KOBO-001/actions/${ACTION}${segment}${query}`);
    await settledScreen();
    expectV69Panels(screenId);
    noCard();
    expect(panelTitled(title).querySelector("[data-action-selection-notice='EVENT_ID']")).not.toBeNull();
  });

  it.each(SCREENS)("events read refused: %s keeps the panel with the gap inside and a page-level refusal", async (screenId, segment, title) => {
    serve(reads(served(ov.accepted_pending), UNAVAILABLE));
    mount(`/sites/KOBO-001/actions/${ACTION}${segment}`);
    await settledScreen();
    expect(q("[data-page-refusal='action-events'] [data-action-code='STORE_UNAVAILABLE']")).not.toBeNull();
    expectV69Panels(screenId);
    noCard();
    if (screenId !== "action-overview") {
      expect(panelTitled(title).querySelector("[data-panel-gap='action-events']")?.textContent).toMatch(/could not be read/);
    }
  });

  it("verification history refused: action-history states it inside its panel", async () => {
    serve(reads(served(ov.applied_pending_newer_revision), served(hi.events_latest), UNAVAILABLE));
    mount(`/sites/KOBO-001/actions/${ACTION}/history`);
    await settledScreen();
    expectV69Panels("action-history");
    const gap = panelTitled("Action history").querySelector("[data-panel-gap='verification-history']");
    expect(gap?.textContent).toMatch(/could not be read/);
    expect(gap?.getAttribute("data-action-http")).toBe("503");
  });

  it.each([
    ...SCREENS.map(([id, segment]) => [id, segment] as const),
    ["action-plan", "/plan"] as const,
    ["action-evidence", "/evidence"] as const,
    ["verification", "/verification"] as const,
  ])("Action not found: %s keeps its slots with the gap inside, after a page-level refusal", async (screenId, segment) => {
    const wrong = ov.wrong_site_404;
    serve({ [wrong.request.path]: served(wrong), [`${wrong.request.path}/events`]: served(wrong) });
    mount(`/sites/OTHER-001/actions/${ACTION}${segment}`);
    await settledScreen();
    expect(q("[data-page-refusal='action'] [data-action-http='404']")).not.toBeNull();
    expectV69Panels(screenId);
    noCard();
    const gaps = Array.from(document.querySelectorAll("[data-panel-gap='action-unread']"));
    expect(gaps.length).toBe(screenId === "verification" ? 3 : 1);
    for (const gap of gaps) expect(gap.closest("section.panel")).not.toBeNull();
  });

  it.each(SCREENS)("selected event not found: %s keeps its slot after the selection refusal", async (screenId, segment) => {
    const unknown = hi.unknown_event_404;
    const query = "?event_id=00000000-0000-4000-8000-000000000000";
    serve({ [unknown.request.path]: served(unknown), [`${API}/events${query}`]: served(unknown) });
    mount(`/sites/KOBO-001/actions/${ACTION}${segment}${query}`);
    await settledScreen();
    expect(q("[data-page-refusal='selection-not-found'] [data-action-open-latest]")).not.toBeNull();
    expectV69Panels(screenId);
    noCard();
  });
});
