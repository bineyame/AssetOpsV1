import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import { ESTATE_ACTIONS_PATH } from "../../estate/actionIndex";
import { ESTATE_API_PATH, type EstateClient } from "../../estate/estateClient";
import { ESTATE_FINDING_LENS_PATHS } from "../../estate/findingIndex";
import { fakeClient, findingsBody, loaded } from "../../estate/__tests__/estateFixtures";
import { CANDIDATE_ID, analyticsClient } from "../../sites/__tests__/analyticsFixtures";
import { POPULATED_EVIDENCE, evidenceClient } from "../../sites/__tests__/evidenceFixtures";
import { indexBody, indexClient } from "../../sites/__tests__/findingIndexFixtures";
import { HYBRID_MINI_GRID_SITE } from "../../sites/__tests__/sldFixtures";
import { FINDINGS_API_PATH, type SiteAnalyticsClient } from "../../sites/siteAnalyticsClient";
import type { FindingIndexClient } from "../../sites/findingIndexClient";
import type { SiteDetailClient, SiteDirectoryClient } from "../../sites/siteDirectoryClient";
import { settledScreen } from "../../test/settled";
import { expectUnavailableEntry } from "../../test/unavailableEntry";
import {
  ACTIONS_PATH,
  FINDINGS_COST_PATH,
  FINDINGS_OPPORTUNITIES_PATH,
  FINDINGS_PATH,
  FINDINGS_RISKS_PATH,
} from "../operatorSiteRoutes";

/**
 * W3-01 commit 3 (build spec Review closure B1/B2; `.agent/W3-01-lane-a-requests.md` commit-3 items 1-6): the
 * estate Finding lens roots and the Actions root are mounted in the operator shell ahead of the legacy Finding
 * patterns, the rail's Actions root is live, and the legacy Finding routes, `/api/findings` and the Site Findings
 * lens chips are unchanged.
 */

const SITE_ID = HYBRID_MINI_GRID_SITE.site_id;
const DIRECTORY: SiteDirectoryClient = { listSites: () => Promise.resolve({ status: "loaded", sites: [] }) };
const DETAIL: SiteDetailClient = {
  getSite: () => Promise.resolve({ status: "loaded", site: HYBRID_MINI_GRID_SITE }),
};

function LocationProbe() {
  const location = useLocation();
  return <output data-location>{location.pathname}</output>;
}

function renderAt(
  path: string,
  options: { estate: EstateClient; analytics?: SiteAnalyticsClient; index?: FindingIndexClient },
) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App
        flags={featureFlagsWith(false)}
        siteDirectory={DIRECTORY}
        siteDetail={DETAIL}
        siteEvidence={evidenceClient({ status: "loaded", value: POPULATED_EVIDENCE })}
        siteAnalytics={options.analytics ?? analyticsClient(SITE_ID)}
        siteFindingIndex={options.index}
        estateIndex={options.estate}
      />
      <LocationProbe />
    </MemoryRouter>,
  );
}

const where = () => document.querySelector("[data-location]")?.textContent ?? "";
const rail = () => screen.getByRole("navigation", { name: "Operator routes" });
const railCurrent = () => rail().querySelector('[aria-current="page"]')?.textContent ?? null;

/** The legacy analytics client, with every read counted. */
function countedAnalytics() {
  const base = analyticsClient(SITE_ID);
  const counted: SiteAnalyticsClient = {
    getDeclaration: vi.fn(base.getDeclaration),
    getDispatch: vi.fn(base.getDispatch),
    getSiteFindings: vi.fn(base.getSiteFindings),
    getAssessment: vi.fn(base.getAssessment),
    getFindings: vi.fn(base.getFindings),
  };
  return counted;
}

describe("W3-01 estate roots in the operator shell", () => {
  it("test_existing_findings_api_and_legacy_routes_unchanged", async () => {
    // The estate API is additive at `/api/estate/*`; the legacy Finding reads keep `/api/findings`.
    expect(FINDINGS_API_PATH).toBe("/api/findings");
    expect(ESTATE_API_PATH).toBe("/api/estate");

    for (const path of [`/findings/${SITE_ID}/${CANDIDATE_ID}`, `/findings/${SITE_ID}/${CANDIDATE_ID}/analysis`]) {
      const estate = fakeClient(() => loaded(findingsBody("all")));
      const analytics = countedAnalytics();
      const view = renderAt(path, { estate, analytics });
      await settledScreen();

      // The legacy pattern keeps its handler: the Finding frame reads the assessment through the legacy client,
      // the estate client is never asked, and no estate root renders.
      expect(where()).toBe(path);
      expect(analytics.getAssessment).toHaveBeenCalledWith(SITE_ID, CANDIDATE_ID);
      expect(estate.calls).toEqual([]);
      expect(document.querySelector("[data-estate-root]")).toBeNull();
      expect(screen.queryByRole("heading", { level: 1, name: "Page not available" })).toBeNull();
      expect(railCurrent()).toBe("Findings");
      view.unmount();
    }
  });

  it("test_site_lens_chips_remain_unavailable", async () => {
    const estate = fakeClient(() => loaded(findingsBody("all")));
    const { client, getFindingIndex } = indexClient(() => ({ status: "loaded", value: indexBody() }));
    renderAt(
      `/sites/${SITE_ID}/findings?from=2026-10-25T00%3A00%3A00Z&to=2026-10-26T00%3A00%3A00Z&domain=mini-grid-dispatch`,
      { estate, index: client },
    );
    await settledScreen();
    expect(getFindingIndex).toHaveBeenCalled();

    // The Site lens row keeps exactly its three "Not available yet" chips; the estate lens tabs are not here.
    const lenses = document.querySelector("[data-site-findings-lenses]") as HTMLElement;
    expect(lenses).not.toBeNull();
    for (const label of ["Cost", "Risks", "Opportunities"]) expectUnavailableEntry(lenses, label);
    expect(Array.from(lenses.querySelectorAll("[data-chip-unavailable]")).map((chip) =>
      chip.getAttribute("data-chip-unavailable"))).toEqual(["Cost", "Risks", "Opportunities"]);
    expect(within(lenses).queryAllByRole("link")).toEqual([]);
    expect(document.querySelector("[data-estate-lenses]")).toBeNull();
    expect(document.querySelector("[data-estate-root]")).toBeNull();
    expect(estate.calls).toEqual([]);
  });

  it("test_estate_route_precedence_and_actions_rail", async () => {
    // The shell's route constants mirror the estate pages' own paths.
    expect([FINDINGS_PATH, FINDINGS_COST_PATH, FINDINGS_RISKS_PATH, FINDINGS_OPPORTUNITIES_PATH]).toEqual([
      ESTATE_FINDING_LENS_PATHS.all,
      ESTATE_FINDING_LENS_PATHS.cost,
      ESTATE_FINDING_LENS_PATHS.risks,
      ESTATE_FINDING_LENS_PATHS.opportunities,
    ]);
    expect(ACTIONS_PATH).toBe(ESTATE_ACTIONS_PATH);

    // Each lens path renders its estate root, not the legacy Finding frame, and reads its own lens.
    for (const lens of ["all", "cost", "risks", "opportunities"] as const) {
      const estate = fakeClient((asked) => loaded(findingsBody(asked)));
      const analytics = countedAnalytics();
      const view = renderAt(ESTATE_FINDING_LENS_PATHS[lens], { estate, analytics });
      await settledScreen();
      expect(document.querySelector(`[data-estate-root="${lens}"]`), lens).not.toBeNull();
      expect(screen.getByRole("main")).toContainElement(document.querySelector(`[data-estate-root="${lens}"]`) as HTMLElement);
      expect(screen.getByRole("heading", { level: 1, name: "Findings" })).toBeInTheDocument();
      // One Findings read for the lens, plus the post-W6 W3-estate Q7 scope read (Site names for the cause copy).
      expect(estate.calls).toHaveLength(2);
      expect(estate.calls.filter((call) => (call as { kind: string }).kind === "findings")).toEqual([
        expect.objectContaining({ kind: "findings", lens }),
      ]);
      expect(estate.calls.filter((call) => (call as { kind: string }).kind === "scope")).toHaveLength(1);
      expect(analytics.getAssessment).not.toHaveBeenCalled();
      expect(railCurrent()).toBe("Findings");
      view.unmount();
    }

    // The rail's Actions root is a live link to the estate Actions root; Incidents (W6-01a), Maintenance (W6-01b) and
    // Operational records (W6-01e) are live.
    const estate = fakeClient(() => loaded(findingsBody("all")));
    renderAt("/sites", { estate });
    await settledScreen();
    expect(within(rail()).getAllByRole("link").map((link) => [link.textContent, link.getAttribute("href")])).toEqual([
      ["Portfolio", "/portfolio"],
      ["Sites", "/sites"],
      ["Findings", "/findings"],
      ["Actions", "/actions"],
      ["Incidents", "/incidents"],
      ["Maintenance", "/maintenance"],
      ["Operational records", "/operational-records"],
      ["Evidence", "/evidence"],
      ["Financials", "/financials"],
    ]);
    fireEvent.click(within(rail()).getByRole("link", { name: "Actions" }));
    await settledScreen();
    expect(where()).toBe("/actions");
    expect(railCurrent()).toBe("Actions");
    expect(document.querySelector('[data-estate-root="actions"]')).not.toBeNull();
    expect(screen.getByRole("heading", { level: 1, name: "Actions" })).toBeInTheDocument();
    expect(estate.calls).toHaveLength(1);
    expect(estate.calls[0]).toMatchObject({ kind: "actions" });
  });
});
