/**
 * W1-F4 (`D-2026-10-17-mockup-layout-spec`): the Recommendation route renders
 * exactly the v69 `recommendation` panels, in order (Proposed intervention,
 * Declare success before evaluating, Evidence needed to verify), in its
 * stocked, accepted, held, empty and refused variants, with every unsupported
 * read stated inside its panel slot and no leading answer card.
 *
 * Bodies are the committed S6 wire contract, served through a stubbed `fetch`
 * so the real client and route render. Derived bodies: the refused reads
 * (404 and 503) are built here; no recorded refusal exists for this route.
 */
import { cleanup, render, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import contract from "../../../../backend/tests/fixtures/s6_action_api_contract.json";
import { SiteFindingFrame } from "../../shell/SiteAnalyticsFrames";
import { expectV69Panels, panelTitled } from "../../test/panelStructure";
import { expectStateLineVisible } from "../../test/productPresentation";
import { settledScreen } from "../../test/settled";
import type { SiteDetailClient } from "../siteDirectoryClient";
import { HYBRID_MINI_GRID_SITE } from "./sldFixtures";

type Case = { request: { method: string; path: string }; status: number; body: any };
const M = contract.manifest as unknown as Record<string, Record<string, Case>>;
const rec = M["recommendation:1#a"];
const FINDING = rec.pre_accept_available.body.finding_id as string;
const REV = rec.pre_accept_available.body.revision_id as string;

const detail: SiteDetailClient = {
  getSite: async (siteId: string) => ({ status: "loaded", site: { ...HYBRID_MINI_GRID_SITE, site_id: siteId } }),
} as SiteDetailClient;

/** Serve one GET (any query order) with `status` and `body`. */
function serve(path: string, status: number, body: unknown) {
  const [want] = path.split("?");
  vi.stubGlobal("fetch", async (url: string) => {
    const [got] = url.split("?");
    if (decodeURIComponent(got) !== decodeURIComponent(want)) {
      return new Response(JSON.stringify({ detail: { code: "TEST_UNMATCHED", message: url } }), { status: 599 });
    }
    return new Response(JSON.stringify(body), { status });
  });
}

function mount(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        {["/sites/:siteId/findings/:findingId", "/sites/:siteId/findings/:findingId/:findingView"].map((p) => (
          <Route key={p} path={p} element={<SiteFindingFrame detail={detail} sitesPath="/sites" />} />
        ))}
      </Routes>
    </MemoryRouter>,
  );
}

async function show(c: Case) {
  serve(c.request.path, c.status, c.body);
  mount(c.request.path.replace("/api", ""));
  await settledScreen();
}

const gaps = () => Array.from(document.querySelectorAll("[data-panel-gap]"));
const PROPOSED = "Proposed intervention";
const SUCCESS = "Declare success before evaluating";
const EVIDENCE = "Evidence needed to verify";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("W1-F4: Recommendation keeps the v69 panel structure in every variant", () => {
  it("stocked (trial proposed): the proposal, limits, accept control and money link sit in panel 1; 2 and 3 state their gaps", async () => {
    await show(rec.pre_accept_available);
    expectV69Panels("recommendation");
    expect(document.querySelector("[data-headline-card]")).toBeNull();
    expect(document.querySelector("[data-page-refusal]")).toBeNull();
    // The former answer card's state line is the strip's lead, never a card.
    const strip = document.querySelector(".status-strip") as HTMLElement;
    expect(strip.hasAttribute("data-product-status")).toBe(true);
    expect(expectStateLineVisible(strip.parentElement as HTMLElement)).toBe("Trial proposed; not accepted");
    const proposed = panelTitled(PROPOSED);
    expect(proposed.querySelector("[data-recommendation-proposal]")?.textContent).toMatch(/20%.*to.*15%/);
    expect(proposed.querySelector("[data-action-limitation]")).not.toBeNull();
    expect(proposed.querySelector("[data-source-provenance-subject='recommendation']")).not.toBeNull();
    expect(within(proposed).getByRole("button", { name: "Accept trial (SYSTEM demonstration)" })).toHaveClass("button", "primary");
    expect(proposed.querySelector("[data-recommendation-money-link] a")?.getAttribute("href")).toBe(
      `/sites/KOBO-001/financials?finding_id=${FINDING}&revision_id=${REV}`,
    );
    // The frame's own money line is not repeated above panel 1.
    expect(document.querySelector("[data-finding-financials-link]")).toBeNull();
    expect(panelTitled(SUCCESS).querySelector("[data-panel-gap]")?.textContent).toBe("No success criteria recorded.");
    expect(panelTitled(EVIDENCE).querySelector("[data-panel-gap]")?.textContent).toBe("Requirements not recorded.");
    // The acceptance-limit notice sits between the pair and panel 3.
    const notice = document.querySelector("[data-recommendation-accept-limit]") as HTMLElement;
    expect(notice.previousElementSibling).toHaveClass("panel-pair");
    expect(notice.nextElementSibling).toBe(panelTitled(EVIDENCE));
    expect(notice.textContent).toMatch(/does not close the Finding, verify the change or send a real controller command/);
  });

  it("accepted: the accepted proposal and live recomputation in panel 1; criteria and evidence requirements fill 2 and 3", async () => {
    await show(rec.accepted_snapshot_live_status);
    expectV69Panels("recommendation");
    expect(document.querySelector("[data-headline-card]")).toBeNull();
    const proposed = panelTitled(PROPOSED);
    expect(proposed.querySelector("[data-recommendation-accepted]")?.textContent).toMatch(/20%.*to.*15%/);
    expect(proposed.querySelector("[data-recommendation-live]")).not.toBeNull();
    expect(proposed.querySelector("[data-recommendation-prior-action]")).not.toBeNull();
    expect(within(panelTitled(SUCCESS)).getByRole("columnheader", { name: "Criterion" })).toBeInTheDocument();
    expect(panelTitled(EVIDENCE).querySelectorAll("[data-attention-item]")).toHaveLength(3);
    expect(gaps().filter((g) => g.closest(".panel") !== proposed)).toEqual([]);
  });

  it("held (an earlier trial is open): the hold and disabled Accept sit in panel 1; 2 and 3 state their gaps", async () => {
    await show(rec.latest_revision_after_apply);
    expectV69Panels("recommendation");
    const proposed = panelTitled(PROPOSED);
    expect(proposed.querySelector("[data-recommendation-held='PRIOR_ACTION_UNRESOLVED']")).not.toBeNull();
    expect(proposed.querySelector("[data-recommendation-prior-block-link]")).not.toBeNull();
    expect(within(proposed).getByRole("button", { name: /Accept trial/ })).toBeDisabled();
    expect(panelTitled(SUCCESS).textContent).toContain("No success criteria recorded.");
    expect(panelTitled(EVIDENCE).textContent).toContain("Requirements not recorded.");
  });

  it("empty (no trial proposed): panel 1 states the typed reason; 2 and 3 state their gaps", async () => {
    await show(rec.pre_accept_unavailable);
    expectV69Panels("recommendation");
    expect(document.querySelector("[data-headline-card]")).toBeNull();
    const proposed = panelTitled(PROPOSED);
    expect(proposed.querySelector("[data-recommendation-unavailable='SOC_NOT_ABOVE_HEADROOM']")?.textContent).toMatch(
      /proposes no reserve trial/,
    );
    expect(proposed.querySelector("[data-panel-gap='site-recommendation-change']")?.textContent).toBe("None proposed");
    expect(panelTitled(SUCCESS).querySelector("[data-panel-gap]")?.textContent).toBe("No success criteria recorded.");
    expect(panelTitled(EVIDENCE).querySelector("[data-panel-gap]")?.textContent).toBe("Requirements not recorded.");
  });

  it.each([
    ["not found", 404, "RECOMMENDATION_NOT_FOUND", "Recommendation not found"],
    ["store unavailable", 503, "STORE_UNAVAILABLE", "Recommendation unavailable"],
  ] as const)("refused (%s): a page-level refusal line, then the three slots with the gap inside each", async (_n, http, code, title) => {
    // Derived: a refused read of the recorded request path.
    serve(rec.pre_accept_available.request.path, http, { detail: { code, message: "refused for the test" } });
    mount(`/sites/KOBO-001/findings/${FINDING}/recommendation?revision_id=${REV}`);
    await settledScreen();
    const refusal = document.querySelector("[data-page-refusal='refused']") as HTMLElement;
    expect(refusal.querySelector(".page-refusal__title")?.textContent).toBe(title);
    expect(refusal.querySelector("[data-action-read='refused']")?.getAttribute("data-action-code")).toBe(code);
    expectV69Panels("recommendation");
    expect(gaps()).toHaveLength(3);
    for (const gap of gaps()) expect(gap.textContent).toContain("could not be read");
    expect(document.querySelector("[data-headline-card]")).toBeNull();
    expect(document.querySelector("button")).toBeNull();
  });
});
