/**
 * S6-03 (`sitework:1#a`): Site > Work > Actions over the recorded Site Action
 * index bodies (`backend/tests/fixtures/s6_site_action_index_contract.json`,
 * written by `test_s6_site_action_index_postgres.py` from `D-action-records`).
 *
 * Covers the positive list, the assessed zero window, the choose-window state,
 * unknown and refusal states, a changed list invalidating page two, reload of
 * the same Site/window, exact Finding-version and Action-step links, native
 * keyboard controls, recorded resolution steps without a list verdict, and
 * the 1440/390 widths (jsdom has no layout: the measured claim is the
 * layout-evidence script's).
 */
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import contract from "../../../../backend/tests/fixtures/s6_site_action_index_contract.json";
import { OPERATOR_SITE_TABS } from "../../shell/operatorSiteTabs";
import { SiteWorkFrame } from "../../shell/SiteAnalyticsFrames";
import { describeViolations, scanDisclosureVocabulary, scanProductVocabulary } from "../../test/productVocabulary";
import { expectStateLineVisible } from "../../test/productPresentation";
import { settledScreen } from "../../test/settled";
import type { ActionIndexBody } from "../actionIndexClient";
import type { SiteDetailClient } from "../siteDirectoryClient";
import { HYBRID_MINI_GRID_SITE } from "./sldFixtures";

type Served = { status: number; body: unknown };
const D = contract.d_action_records as unknown as Record<string, any>;
const R = contract.resolution as unknown as Record<string, any>;
const POSITIVE = D.positive as ActionIndexBody;
const ZERO = D.zero as ActionIndexBody;
const WINDOW = D.positive_window as { from: string; to: string };
const ZERO_WINDOW = D.zero_window as { from: string; to: string };
const PAGE1 = D.page1 as ActionIndexBody;
const PAGE2 = D.page2 as ActionIndexBody;

const workUrl = (w: { from: string; to: string }, extra: Record<string, string> = {}) =>
  `/sites/KOBO-001/work?${new URLSearchParams({ from: w.from, to: w.to, ...extra }).toString()}`;
const apiKey = (w: { from: string; to: string }, extra: Record<string, string> = {}) =>
  `/api/sites/KOBO-001/action-index?${new URLSearchParams({ from: w.from, to: w.to, ...extra }).toString()}`;

function serve(table: Record<string, Served>) {
  const requests: string[] = [];
  vi.stubGlobal("fetch", async (url: string) => {
    requests.push(url);
    const hit = table[url];
    if (!hit) return new Response(JSON.stringify({ detail: { code: "TEST_UNMATCHED", message: url } }), { status: 599 });
    return new Response(JSON.stringify(hit.body), { status: hit.status });
  });
  return { requests, table };
}

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
        <Route path="/sites/:siteId/work" element={<><SiteWorkFrame detail={detail} sitesPath="/sites" /><Where /></>} />
        <Route path="*" element={<Where />} />
      </Routes>
    </MemoryRouter>,
  );
}

const q = (selector: string) => document.body.querySelector(selector);
const qa = (selector: string) => Array.from(document.body.querySelectorAll(selector));
const where = () => screen.getByTestId("where").textContent;
const ok = (body: unknown): Served => ({ status: 200, body });

function noVocabularyViolations(page: string) {
  const main = document.body.querySelector("main") as HTMLElement;
  const { violations, scanned } = scanProductVocabulary(main, page);
  expect(scanned).toBeGreaterThan(10);
  expect(violations, describeViolations(violations)).toEqual([]);
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("Site Work tab", () => {
  it("is a rendered Site tab that opens /sites/{site}/work", () => {
    const work = OPERATOR_SITE_TABS.find((tab) => tab.label === "Work");
    expect(work?.href("KOBO-001")).toBe("/sites/KOBO-001/work");
  });
});

describe("Site Work Actions list", () => {
  it("lists persisted Actions newest-created first with exact Finding-version and step links", async () => {
    serve({ [apiKey(WINDOW)]: ok(POSITIVE) });
    mount(workUrl(WINDOW));
    await settledScreen();
    expect(q("[data-site-work-state]")?.getAttribute("data-site-work-state")).toBe("current-rows");
    expect(screen.getByRole("link", { name: "Work" }).getAttribute("aria-current")).toBe("page");
    expect(q("[data-site-work-scope]")?.textContent).toContain(`${POSITIVE.total_count} Actions created`);
    const rows = qa("[data-site-work-row]");
    expect(rows.map((r) => r.getAttribute("data-site-work-row"))).toEqual(POSITIVE.rows.map((r) => r.action_id));
    expect(POSITIVE.rows[0].created_at > POSITIVE.rows[1].created_at).toBe(true);
    POSITIVE.rows.forEach((row, i) => {
      const tr = rows[i];
      expect(tr.getAttribute("data-site-work-event")).toBe(row.selected_event.id);
      expect(tr.querySelector("[data-site-work-action-link]")?.getAttribute("href")).toBe(
        `/sites/KOBO-001/actions/${row.action_id}`,
      );
      expect(tr.querySelector("[data-site-work-finding-link]")?.getAttribute("href")).toBe(row.links.origin_finding);
      expect(tr.querySelector("[data-site-work-event-link]")?.getAttribute("href")).toBe(row.links.history_at_event);
      expect(tr.textContent).toContain(row.action_code);
    });
    // Same lifecycle words as recorded state, never a verdict, owner or due date.
    expect(rows[0].textContent).toContain("Accepted · not applied (1 failed attempt)");
    expect(rows[1].textContent).toContain("Applied · result not checked yet");
    const headers = qa("main table thead th").map((th) => th.textContent);
    expect(headers.slice(0, 5)).toEqual(["Action", "Source", "Created", "State", "Latest step"]);
    expect(document.body.textContent).not.toMatch(/\bVerified\b|\bOwner\b|\bDue\b|Priority/);
    // IDs and the fence sit in the disclosure, not the default reading.
    // W1-UX-04: the answer card's exact-reference disclosure now comes first; select the list's own basis by name.
    const basis = q("[data-disclosure='site-work-basis']");
    expect(basis?.hasAttribute("open")).toBe(false);
    expect(basis?.querySelector("[data-site-work-fence]")?.textContent).toBe(POSITIVE.fence.token);
    expect(basis?.textContent).toContain(POSITIVE.rows[0].origin.finding_revision_id);
    noVocabularyViolations("site work actions");
  });

  it("shows a backdated observation as the latest recorded step without moving the row", async () => {
    const after = D.after_backdated_observation as ActionIndexBody;
    serve({ [apiKey(WINDOW)]: ok(after) });
    mount(workUrl(WINDOW));
    await settledScreen();
    const observed = after.rows[1];
    expect(observed.selected_event.occurred_before_recorded).toBe(true);
    const tr = q(`[data-site-work-row="${observed.action_id}"]`) as HTMLElement;
    expect(tr.textContent).toContain("Review note added");
    expect(tr.textContent).toContain("Applied · result not checked yet");
    expect(qa("[data-site-work-row]").map((r) => r.getAttribute("data-site-work-row"))).toEqual(
      POSITIVE.rows.map((r) => r.action_id),
    );
  });

  it("states an assessed zero window as no Actions created, with its explicit zero fence", async () => {
    serve({ [apiKey(ZERO_WINDOW)]: ok(ZERO) });
    mount(workUrl(ZERO_WINDOW));
    await settledScreen();
    expect(q("[data-site-work-state]")?.getAttribute("data-site-work-state")).toBe("current-empty");
    expect(screen.getByRole("heading", { name: "No Actions created at this site in this window" })).toBeTruthy();
    expect(qa("[data-site-work-row]")).toHaveLength(0);
    expect(q("[data-site-work-fence-counts]")?.textContent).toContain("0 Actions, 0 recorded steps (an explicit zero)");
    noVocabularyViolations("site work zero");
  });

  it("asks for a window and reads nothing until one is chosen; the chosen window lands in the URL", async () => {
    const { requests } = serve({});
    mount("/sites/KOBO-001/work");
    await settledScreen();
    expect(q("[data-site-work-state]")?.getAttribute("data-site-work-state")).toBe("choose-window");
    expect(requests.filter((u) => u.includes("action-index"))).toEqual([]);
    expect(document.body.textContent).not.toMatch(/No Actions created/);
    const [first, last] = qa("[data-site-work-window] input") as HTMLInputElement[];
    fireEvent.change(first, { target: { value: "2026-11-01" } });
    fireEvent.change(last, { target: { value: "2026-11-01" } });
    serve({ [apiKey(WINDOW)]: ok(POSITIVE) });
    fireEvent.click(screen.getByRole("button", { name: "Show Actions" }));
    await waitFor(() => expect(qa("[data-site-work-row]")).toHaveLength(POSITIVE.rows.length));
    expect(where()).toBe(workUrl(WINDOW));
  });

  it("reopens the same Site and window on reload with the same rows and fence", async () => {
    serve({ [apiKey(WINDOW)]: ok(POSITIVE) });
    mount(workUrl(WINDOW));
    await settledScreen();
    const before = qa("[data-site-work-row]").map((r) => r.outerHTML);
    cleanup();
    mount(workUrl(WINDOW));
    await settledScreen();
    expect(qa("[data-site-work-row]").map((r) => r.outerHTML)).toEqual(before);
    expect(q("[data-site-work-fence]")?.textContent).toBe(POSITIVE.fence.token);
  });

  it("pages on one fence, and a changed list refuses page two and restarts from page one", async () => {
    serve({
      [apiKey(WINDOW, { limit: "1" })]: ok(PAGE1),
      [apiKey(WINDOW, { limit: "1", cursor: PAGE1.next_cursor as string })]: ok(PAGE2),
    });
    mount(workUrl(WINDOW, { limit: "1" }));
    await settledScreen();
    expect(q("[data-site-work-pages]")?.textContent).toContain(`Showing 1 of ${PAGE1.total_count}`);
    fireEvent.click(q("[data-site-work-next]") as HTMLElement);
    await waitFor(() => expect(where()).toContain("cursor="));
    await settledScreen();
    expect(qa("[data-site-work-row]").map((r) => r.getAttribute("data-site-work-row"))).toEqual(
      PAGE2.rows.map((r) => r.action_id),
    );
    expect(q("[data-site-work-first]")).not.toBeNull();

    cleanup();
    const changed = D.basis_changed as Served;
    serve({
      [apiKey(WINDOW, { limit: "1" })]: ok(PAGE1),
      [apiKey(WINDOW, { limit: "1", cursor: PAGE1.next_cursor as string })]: changed,
    });
    mount(workUrl(WINDOW, { limit: "1", cursor: PAGE1.next_cursor as string }));
    await settledScreen();
    expect(q("[data-site-work-state]")?.getAttribute("data-site-work-state")).toBe("basis-changed");
    expect(q("[data-site-work-reason]")?.getAttribute("data-site-work-reason")).toBe("FENCE_CHANGED");
    expect(qa("[data-site-work-row]")).toHaveLength(0);
    expect(document.body.textContent).not.toMatch(/Showing \d/);
    fireEvent.click(q("[data-site-work-restart]") as HTMLElement);
    await waitFor(() => expect(where()).toBe(workUrl(WINDOW, { limit: "1" })));
    await settledScreen();
    expect(qa("[data-site-work-row]")).toHaveLength(1);
  });

  it.each([
    ["refused_invalid_window", "invalid"],
    ["refused_window_required", "invalid"],
    ["store_unavailable", "unavailable"],
  ])("shows the recorded %s refusal as its own state, with no rows or count", async (name, state) => {
    serve({ [apiKey(WINDOW)]: D[name] as Served });
    mount(workUrl(WINDOW));
    await settledScreen();
    expect(q("[data-site-work-state]")?.getAttribute("data-site-work-state")).toBe(state);
    expect(qa("[data-site-work-row]")).toHaveLength(0);
    expect(document.body.textContent).not.toMatch(/No Actions created|Showing \d/);
  });

  it.each([
    [401, { detail: { code: "UNAUTHENTICATED", message: "Sign in to read Actions." } }, "unauthenticated"],
    [403, { detail: { code: "SITE_SCOPE_FORBIDDEN", message: "No access." } }, "forbidden"],
    [404, { detail: "No imported Site 'KOBO-001' in this tenant." }, "not-found"],
    [409, { detail: { code: "ACTION_INDEX_INCONSISTENT", message: "x", rows: null } }, "inconsistent"],
    [500, { detail: "boom" }, "unavailable"],
  ])("keeps HTTP %s distinct from zero", async (status, body, state) => {
    serve({ [apiKey(WINDOW)]: { status, body } });
    mount(workUrl(WINDOW));
    await settledScreen();
    expect(q("[data-site-work-state]")?.getAttribute("data-site-work-state")).toBe(state);
    expect(document.body.textContent).not.toMatch(/No Actions created|Showing \d/);
  });

  it("shows unknown, not zero, when the network fails", async () => {
    vi.stubGlobal("fetch", async () => {
      throw new TypeError("offline");
    });
    mount(workUrl(WINDOW));
    await settledScreen();
    expect(screen.getByRole("heading", { name: "Actions not known right now" })).toBeTruthy();
    expect(document.body.textContent).toContain("This is not a statement that the site has no Actions.");
  });

  it("lists recorded resolution steps with Action detail's lifecycle and no list-made verdict", async () => {
    const resolved = R.resolved as ActionIndexBody;
    const withdrawn = R.withdrawn as ActionIndexBody;
    const w = R.window as { from: string; to: string };
    serve({ [apiKey(w)]: ok(resolved) });
    mount(workUrl(w));
    await settledScreen();
    const row = resolved.rows.find((r) => r.selected_event.kind === "RESOLVED");
    expect(row).toBeTruthy();
    let tr = q(`[data-site-work-row="${row?.action_id}"]`) as HTMLElement;
    expect(tr.textContent).toContain("Trial closed by the verification check");
    expect(tr.textContent).not.toMatch(/VERIFIED|Verified/);
    cleanup();
    serve({ [apiKey(w)]: ok(withdrawn) });
    mount(workUrl(w));
    await settledScreen();
    tr = q(`[data-site-work-row="${row?.action_id}"]`) as HTMLElement;
    expect(tr.textContent).toContain("Trial closure withdrawn; being checked again");
    expect(tr.textContent).toContain("Being checked again");
  });

  it("uses native keyboard controls: real links, a labelled form and a submit button", async () => {
    serve({ [apiKey(WINDOW, { limit: "1" })]: ok(PAGE1) });
    mount(workUrl(WINDOW, { limit: "1" }));
    await settledScreen();
    for (const link of qa("main table a, [data-site-work-pages] a")) {
      expect(link.tagName).toBe("A");
      expect(link.getAttribute("href")).toMatch(/^\/sites\/KOBO-001\//);
      expect(link.getAttribute("tabindex")).toBeNull();
    }
    const form = screen.getByRole("form", { name: "Actions window" });
    expect(form.querySelectorAll("input[type=date]")).toHaveLength(2);
    expect(screen.getByLabelText(/Created from/)).toBeTruthy();
    expect(screen.getByRole("button", { name: "Show Actions" }).getAttribute("type")).toBe("submit");
    expect(screen.getByRole("navigation", { name: "Actions pages" })).toBeTruthy();
  });

  it.each([1440, 390])("renders the same rows and links at %ipx", async (width) => {
    Object.defineProperty(window, "innerWidth", { configurable: true, value: width });
    window.dispatchEvent(new Event("resize"));
    serve({ [apiKey(WINDOW)]: ok(POSITIVE) });
    mount(workUrl(WINDOW));
    await settledScreen();
    expect(qa("[data-site-work-row]")).toHaveLength(POSITIVE.rows.length);
    expect(qa("[data-site-work-event-link]")).toHaveLength(POSITIVE.rows.length);
  });
});

describe("W1-UX-04 phase 1: Site Work answer card", () => {
  function w1Scan(page: string) {
    const main = document.body.querySelector("main") as HTMLElement;
    const w1 = scanProductVocabulary(main, page, { set: "w1" });
    expect(w1.scanned).toBeGreaterThan(10);
    expect(w1.violations, describeViolations(w1.violations)).toEqual([]);
  }

  it("rows: the state line, scope and read time stay outside the closed disclosure; no verdict is derived", async () => {
    serve({ [apiKey(WINDOW)]: ok(POSITIVE) });
    mount(workUrl(WINDOW));
    await settledScreen();
    w1Scan("sitework (W1) rows");
    const card = q("[data-headline-card='site-work']") as HTMLElement;
    expect(expectStateLineVisible(card)).toBe("Every Action created here in this window");
    expect(card.querySelector("[data-product-status]")?.getAttribute("data-product-status")).not.toBe("positive");
    const bars = Array.from(card.querySelectorAll("[data-value-bar-key]"));
    expect(bars.length).toBeGreaterThanOrEqual(4);
    const disclosure = scanDisclosureVocabulary(card, "sitework disclosure");
    expect(disclosure.disclosures).toBe(1);
    expect(disclosure.violations, describeViolations(disclosure.violations)).toEqual([]);
    expect(disclosure.violations, describeViolations(disclosure.violations)).toEqual([]);
    expect(card.textContent).not.toMatch(/verified|met its goal(?! is)|saving (?:of|was)/i);
  });

  it("proved zero: only after a successful bounded read, with its read time beside it", async () => {
    serve({ [apiKey(ZERO_WINDOW)]: ok(ZERO) });
    mount(workUrl(ZERO_WINDOW));
    await settledScreen();
    w1Scan("sitework (W1) zero");
    const card = q("[data-headline-card='site-work']") as HTMLElement;
    expect(expectStateLineVisible(card)).toBe("Checked: nothing to report");
    expect(card.querySelector("[data-site-work-proved-zero]")?.getAttribute("data-site-work-proved-zero")).toBe(ZERO.read_at);
    expect(card.querySelector("[data-product-status-as-of]")?.textContent).not.toMatch(/time not recorded/);
  });

  it("an unread list is never a zero and claims no read time", async () => {
    vi.stubGlobal("fetch", async () => {
      throw new TypeError("offline");
    });
    mount(workUrl(WINDOW));
    await settledScreen();
    const card = q("[data-headline-card='site-work']") as HTMLElement;
    // The read returned no instant, so the as-of line says so instead of "As of <time>" (never now).
    expect(expectStateLineVisible(card)).toBe("This could not be read right now");
    expect(card.querySelector("[data-product-status-scope]")?.textContent).toMatch(/KOBO|Actions/);
    expect(card.querySelector("[data-product-status-as-of]")?.textContent).toBe("As of: time not recorded");
    expect(card.querySelector("[data-site-work-proved-zero]")).toBeNull();
    expect(card.querySelector("[data-value-bar-key]")).toBeNull();
    expect(card.textContent).not.toMatch(/0 Actions|No Actions were created/);
  });
});
