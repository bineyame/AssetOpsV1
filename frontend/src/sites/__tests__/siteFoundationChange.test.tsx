/**
 * S6-01b phase 2: the Foundation change deep route (`changes:1#a`) and the
 * bare `/foundation/changes` unavailable state, mounted through the real `App`
 * routes so the static `changes` segments are proven to outrank the
 * `:foundationView` route. `fetch` serves S6-01a's committed wire contract
 * `backend/tests/fixtures/s6_action_api_contract.json` exactly as recorded;
 * the one derived body (a refused events read) says so where it is built.
 */
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import contract from "../../../../backend/tests/fixtures/s6_action_api_contract.json";
import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import { describeViolations, scanDisclosureVocabulary, scanProductVocabulary } from "../../test/productVocabulary";
import { settledScreen } from "../../test/settled";
import { foundationViewFor } from "../FoundationSubtabs";
import type { SiteDetailClient, SiteDirectoryClient } from "../siteDirectoryClient";
import { EMPTY_ANALYTICS_CLIENT } from "./analyticsFixtures";
import { HYBRID_MINI_GRID_SITE } from "./sldFixtures";

type Case = { request: { path: string }; status: number; body: any };
const M = contract.manifest as unknown as Record<string, Record<string, Case>>;
const changes = M["changes:1#a"];
const ov = M["action-overview:1#a"];
const hi = M["action-history:1#a"];
const CHANGE = changes.change.body.change;
const CHANGE_ID = CHANGE.change_id as string;
const ACTION = CHANGE.action_id as string;
const CHANGE_URL = `/sites/KOBO-001/foundation/changes/${CHANGE_ID}`;
const ACTION_API = `/api/sites/KOBO-001/actions/${ACTION}`;

interface Served {
  status: number;
  body: unknown;
}

function serve(gets: Record<string, Served>) {
  const requests: string[] = [];
  vi.stubGlobal("fetch", async (url: string) => {
    const path = decodeURIComponent(String(url));
    requests.push(path);
    const hit = gets[path];
    if (!hit) return new Response(JSON.stringify({ detail: { code: "TEST_UNMATCHED", message: path } }), { status: 599 });
    return new Response(JSON.stringify(hit.body), { status: hit.status });
  });
  return requests;
}

const served = (c: Case): Served => ({ status: c.status, body: c.body });
const changeReads = (): Record<string, Served> => ({
  [changes.change.request.path]: served(changes.change),
  [`${ACTION_API}/events`]: served(hi.events_latest),
});

const detail: SiteDetailClient = {
  getSite: async (siteId: string) => ({ status: "loaded", site: { ...HYBRID_MINI_GRID_SITE, site_id: siteId } }),
} as SiteDetailClient;
const directory: SiteDirectoryClient = {
  listSites: async () => ({ status: "loaded", sites: [HYBRID_MINI_GRID_SITE] }),
} as SiteDirectoryClient;

function Where() {
  const location = useLocation();
  return <output data-testid="where">{`${location.pathname}${location.search}`}</output>;
}

function mount(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App
        flags={featureFlagsWith(false)}
        siteDirectory={directory}
        siteDetail={detail}
        siteAnalytics={EMPTY_ANALYTICS_CLIENT}
      />
      <Where />
    </MemoryRouter>,
  );
}

const q = (selector: string) => document.body.querySelector(selector);
const qa = (selector: string) => Array.from(document.body.querySelectorAll(selector));

function atWidth(width: number) {
  Object.defineProperty(window, "innerWidth", { configurable: true, value: width });
  window.dispatchEvent(new Event("resize"));
}

function noVocabularyViolations(page: string) {
  const main = document.body.querySelector("main") as HTMLElement;
  const { violations, scanned } = scanProductVocabulary(main, page);
  expect(scanned).toBeGreaterThan(5);
  expect(violations, describeViolations(violations)).toEqual([]);
}

function foundationTabCurrent() {
  const current = qa('[aria-current="page"]').map((el) => el.textContent);
  expect(current).toContain("Foundation");
  // W1-F5b (D-2026-10-17-f5-subtabs-and-contact): the Foundation row shows here with Change & effect current,
  // linking to this Changes route; the three period views link to their own addresses.
  const row = screen.getByRole("navigation", { name: "Foundation views" });
  const links = within(row).getAllByRole("link");
  expect(links.map((l) => l.textContent)).toEqual(["Site model", "Single line diagram", "Readiness", "Change & effect"]);
  expect(links.map((l) => l.getAttribute("aria-current"))).toEqual([null, null, null, "page"]);
  expect(links.map((l) => l.getAttribute("href"))).toEqual([
    "/sites/KOBO-001/foundation",
    "/sites/KOBO-001/foundation/sld",
    "/sites/KOBO-001/foundation/readiness",
    "/sites/KOBO-001/foundation/changes",
  ]);
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  atWidth(1024);
});

describe("Foundation change (changes:1#a)", () => {
  it("shows old/new reserve, unit, asset, times, every named version, the Action and its application event, and a pending outcome", async () => {
    serve(changeReads());
    mount(CHANGE_URL);
    await settledScreen();
    // W1-F4: the v69 page heading is the site; the change itself leads the status strip.
    expect(screen.getByRole("heading", { level: 1, name: HYBRID_MINI_GRID_SITE.display_name })).toBeInTheDocument();
    expect(q("[data-change-status] .status-strip__lead")?.textContent).toBe("Battery reserve change · Applied");
    expect(q("[data-change-old]")?.textContent).toBe("20%");
    expect(q("[data-change-new]")?.textContent).toBe("15%");
    expect(q("[data-change-asset]")?.textContent).toBe(CHANGE.asset_id);
    expect(q("[data-change-effective]")?.getAttribute("data-change-effective")).toBe(CHANGE.effective_from);
    expect(q("[data-change-recorded]")?.getAttribute("data-change-recorded")).toBe(CHANGE.recorded_at);
    expect(qa("[data-change-revision]").map((r) => r.getAttribute("data-change-revision-origin"))).toEqual([
      "PUBLISH",
      "SPLIT",
      "PUBLISH",
    ]);
    expect(qa("[data-change-revision]").map((r) => r.getAttribute("data-change-revision"))).toEqual(
      [...CHANGE.foundation_revisions].sort((a: any, b: any) => a.version - b.version).map((r: any) => r.id),
    );
    expect(q(`[data-change-revision="${CHANGE.split_foundation_revision_id}"]`)?.textContent).toMatch(/split/);
    expect(q(`[data-change-revision="${CHANGE.new_foundation_revision_id}"]`)?.textContent).toMatch(/New version/);
    expect(q("[data-change-expected]")?.textContent).toBe(CHANGE.expected_foundation_revision_id);
    expect(qa("[data-change-binding='superseded']").map((r) => r.textContent)).toEqual(
      CHANGE.binding_set_revisions.superseded.map((id: string) => `Replaced${id}`),
    );
    expect(qa("[data-change-binding='inserted']")).toHaveLength(CHANGE.binding_set_revisions.inserted.length);
    expect(q("[data-change-action-link]")).toHaveAttribute("href", `/sites/KOBO-001/actions/${ACTION}`);
    expect(q("[data-change-applied-event-link]")).toHaveAttribute(
      "href",
      `/sites/KOBO-001/actions/${ACTION}/history?event_id=${CHANGE.applied_event_id}`,
    );
    expect(q("[data-change-id]")).toHaveAttribute("data-change-outcome", "PENDING");
    // S6-02b (F5): the apply-time outcome stays on the record; the words read the verification block.
    expect(q("[data-change-outcome-words]")?.textContent).toBe("Verification: No verification plan yet.");
    expect(document.body.textContent).toMatch(/SYSTEM demonstration/);
    // No measured-effect verdict, saving or approval.
    const main = (q("main")?.textContent ?? "").replace(/no effect or saving is claimed/g, "");
    expect(main).not.toMatch(/saved|savings|improved|reduced|effective change|approved|verified\b(?! yet)/i);
    expect(screen.queryByRole("button")).toBeNull();
    foundationTabCurrent();
    noVocabularyViolations("changes:1#a");
  });

  it("lists the Action's failed application attempts beside the change, each linked to its exact event", async () => {
    serve(changeReads());
    mount(CHANGE_URL);
    await settledScreen();
    const failed = (hi.events_latest.body.events as { id: string; kind: string }[]).filter((e) => e.kind === "FAILED");
    expect(failed.length).toBeGreaterThan(0);
    expect(q("[data-change-attempts]")).toHaveAttribute("data-change-attempts", String(failed.length));
    // Review L2: the codes sit in the no-wrap list variant.
    expect(document.body.querySelector("[data-change-failed-attempt]")?.closest("ul")?.classList.contains("action-list--codes")).toBe(true);
    expect(qa("[data-change-failed-attempt] a").map((a) => a.getAttribute("href"))).toEqual(
      failed.map((e) => `/sites/KOBO-001/actions/${ACTION}/history?event_id=${e.id}`),
    );
  });

  it("keeps the change when the attempts read is refused, and says so", async () => {
    // Derived: the events read refused with a 503 instead of the recorded events.
    serve({ ...changeReads(), [`${ACTION_API}/events`]: { status: 503, body: { detail: { code: "ACTION_STORE_UNAVAILABLE", message: "down" } } } });
    mount(CHANGE_URL);
    await settledScreen();
    expect(q("[data-change-new]")?.textContent).toBe("15%");
    expect(q("[data-action-code='ACTION_STORE_UNAVAILABLE']")).not.toBeNull();
    expect(q("[data-change-attempts]")).toBeNull();
  });

  it("a wrong-Site change is not found, with a link back to the Foundation and no events read", async () => {
    const requests = serve({ [changes.wrong_site_404.request.path]: served(changes.wrong_site_404) });
    mount(`/sites/OTHER-001/foundation/changes/${CHANGE_ID}`);
    await settledScreen();
    // W1-F4: a page-level refusal (never an h2), then the v69 slots with the gap inside.
    expect(q("[data-page-refusal] .page-refusal__title")?.textContent).toBe("Foundation change not found");
    expect(q("[data-action-http='404']")).not.toBeNull();
    expect(screen.getByRole("link", { name: "Back to the Foundation" })).toHaveAttribute("href", "/sites/OTHER-001/foundation");
    expect(requests.some((r) => r.includes("/events"))).toBe(false);
    expect(q("[data-change-id]")).toBeNull();
  });

  for (const width of [1440, 390]) {
    it(`renders the same read-only structure at ${width}`, async () => {
      atWidth(width);
      serve(changeReads());
      mount(CHANGE_URL);
      await settledScreen();
      expect(q("[data-change-values]")).not.toBeNull();
      expect(qa("[data-change-revision]")).toHaveLength(3);
      expect(screen.queryByRole("button")).toBeNull();
      foundationTabCurrent();
    });
  }
});

describe("bare /foundation/changes", () => {
  it("is an explicit unavailable state with a link back, and adds no Foundation view", async () => {
    const requests = serve({});
    mount("/sites/KOBO-001/foundation/changes");
    await settledScreen();
    expect(q("[data-change-index='unavailable']")).not.toBeNull();
    const panel = screen.getByRole("heading", { name: "No list of changes yet" }).closest("section") ?? document.body;
    expect(within(panel as HTMLElement).getByRole("link", { name: "Back to the Foundation" })).toHaveAttribute(
      "href",
      "/sites/KOBO-001/foundation",
    );
    expect(requests.filter((r) => r.includes("/changes"))).toEqual([]);
    expect(foundationViewFor("changes")).toBeNull();
    foundationTabCurrent();
    noVocabularyViolations("changes index unavailable");
  });
});

describe("Action links to its Foundation change", () => {
  it("Overview and Application link the change by ID, and following the link opens it", async () => {
    serve({
      [ACTION_API]: served(ov.applied_pending_newer_revision),
      [`${ACTION_API}/events`]: served(hi.events_latest),
      [changes.change.request.path]: served(changes.change),
    });
    mount(`/sites/KOBO-001/actions/${ACTION}`);
    await settledScreen();
    expect(q("[data-action-change-link]")).toHaveAttribute("href", CHANGE_URL);
    cleanup();
    mount(`/sites/KOBO-001/actions/${ACTION}/execution`);
    await settledScreen();
    const link = q("[data-action-event-change-link]") as HTMLAnchorElement;
    expect(link).toHaveAttribute("href", CHANGE_URL);
    fireEvent.click(link);
    await settledScreen();
    expect(screen.getByTestId("where").textContent).toBe(CHANGE_URL);
    expect(q("[data-change-new]")?.textContent).toBe("15%");
  });
});

describe("W1-F4: the former Change answer card, merged into the strip and panel 1", () => {
  it("the change is never positive; the state, scope and as-of stay visible outside closed disclosures", async () => {
    serve(changeReads());
    mount(CHANGE_URL);
    await settledScreen();
    const main = document.body.querySelector("main") as HTMLElement;
    const w1 = scanProductVocabulary(main, "changes (W1)", { set: "w1" });
    expect(w1.scanned).toBeGreaterThan(10);
    expect(w1.violations, describeViolations(w1.violations)).toEqual([]);
    expect(q("[data-headline-card]")).toBeNull();
    const strip = q("[data-change-status]") as HTMLElement;
    expect(strip.querySelector(".status-strip__state")?.textContent).toBe("Setting changed; being applied is not success, effect judged separately");
    // Scope (the battery) and as-of (the recorded time) are visible in panel 1, outside any closed disclosure.
    for (const selector of ["[data-change-asset]", "[data-change-recorded]", "[data-change-outcome-words]"]) {
      expect(q(selector)?.closest("details:not([open])"), selector).toBeNull();
    }
    // The Outcome card reads the verification block and is never positive for a pending trial.
    const outcome = q("[data-change-metric='outcome']") as HTMLElement;
    expect(outcome.className).not.toMatch(/v69-metric--green/);
    expect(outcome.textContent).toMatch(/No verification plan yet/);
    expect(q("[data-change-metric='change']")?.textContent).toMatch(/20% → 15%/);
    expect(q("[data-change-metric='target']")?.textContent).toMatch(/Not recorded yet/);
    const disclosure = scanDisclosureVocabulary(strip, "changes disclosure");
    expect(disclosure.disclosures).toBe(1);
    expect(disclosure.violations, describeViolations(disclosure.violations)).toEqual([]);
    expect((strip.querySelector("details") as HTMLDetailsElement).open).toBe(false);
    expect(q("[data-change-applied-event-link]")).toHaveAttribute(
      "href",
      `/sites/KOBO-001/actions/${ACTION}/history?event_id=${CHANGE.applied_event_id}`,
    );
    expect(q("[data-change-card-action-link]")).toHaveAttribute("href", `/sites/KOBO-001/actions/${ACTION}`);
    expect(main.textContent).not.toMatch(/saving (?:of|was|is achieved)|reduced generator/i);
  });

  it("failed attempts are not known, never zero, while the Action's events cannot be read", async () => {
    serve({ [changes.change.request.path]: served(changes.change) });
    mount(CHANGE_URL);
    await settledScreen();
    const gap = q("[data-change-attempts-refused]") as HTMLElement;
    expect(gap.textContent).toMatch(/Failed attempts are not known/);
    expect(q("[data-change-attempts]")).toBeNull();
    expect(document.body.textContent).not.toMatch(/0 recorded|No failed application attempts/);
  });
});
