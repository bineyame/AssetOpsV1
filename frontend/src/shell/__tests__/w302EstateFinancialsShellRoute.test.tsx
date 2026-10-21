import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import { ESTATE_FINANCIALS_PATH, FINANCIALS_TITLE } from "../../estate/EstateFinancials";
import type {
  EstateFinancialsBody,
  EstateFinancialsClient,
  EvidenceResult,
} from "../../estate/estateEvidenceMoneyClient";
import { HYBRID_MINI_GRID_SITE } from "../../sites/__tests__/sldFixtures";
import type { SiteDetailClient, SiteDirectoryClient } from "../../sites/siteDirectoryClient";
import { settledScreen } from "../../test/settled";
import { FINANCIALS_PATH } from "../operatorSiteRoutes";

/**
 * W3-02 commit 4 (`.agent/W3-02-lane-a-requests.md` commit-4 items 1-3): the estate Financials root is mounted in
 * the operator shell at `/financials` through `EstateFinancialsFrame` (which owns `<main>`), the rail's Financials
 * root is live, and the Site-relative `/sites/{code}/financials` route keeps its own handler.
 */

const SITE_ID = HYBRID_MINI_GRID_SITE.site_id;
const DIRECTORY: SiteDirectoryClient = { listSites: () => Promise.resolve({ status: "loaded", sites: [] }) };
const DETAIL: SiteDetailClient = {
  getSite: () => Promise.resolve({ status: "loaded", site: HYBRID_MINI_GRID_SITE }),
};

function emptyBody(): EstateFinancialsBody {
  return {
    schema_version: "estate-financials-1",
    scope: { tenant_id: "t", authorized_site_count: 0, covered_site_count: 0, access_basis: `sha256:${"b".repeat(64)}` },
    window: { from: "2026-10-13T00:00:00Z", to: "2026-10-20T00:00:00Z", bounds: "[from, to)", known_at: "2026-10-20T09:30:00Z" },
    status: "EMPTY_SCOPE",
    coverage: { state: "EMPTY", sites: [] },
    summary: { eligible_line_count: 0, unpriced_line_count: 0, withheld_line_count: 0, estate_total: null, estate_total_state: "NO_ESTATE_TOTAL" },
    order: "window_start desc nulls last, site_code_key asc, site_id asc, category asc, line_key asc",
    total_count: 0,
    rows: [],
    groups: [],
    exclusions: [],
    diagnostics: [],
    next_cursor: null,
    selection_token: `sha256:${"c".repeat(64)}`,
  } as EstateFinancialsBody;
}

function fake(): EstateFinancialsClient & { calls: unknown[] } {
  const calls: unknown[] = [];
  const result: EvidenceResult<EstateFinancialsBody> = { status: "loaded", value: emptyBody() };
  return {
    calls,
    financials: (query) => {
      calls.push(query);
      return Promise.resolve(result);
    },
  };
}

function LocationProbe() {
  const location = useLocation();
  return <output data-location>{location.pathname}</output>;
}

function renderAt(path: string, client: EstateFinancialsClient) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App flags={featureFlagsWith(false)} siteDirectory={DIRECTORY} siteDetail={DETAIL} estateFinancials={client} />
      <LocationProbe />
    </MemoryRouter>,
  );
}

const where = () => document.querySelector("[data-location]")?.textContent ?? "";
const rail = () => screen.getByRole("navigation", { name: "Operator routes" });
const railCurrent = () => rail().querySelector('[aria-current="page"]')?.textContent ?? null;

describe("W3-02 estate Financials root in the operator shell", () => {
  it("test_estate_financials_route_and_live_rail", async () => {
    // The shell's route constant mirrors the estate page's own path.
    expect(FINANCIALS_PATH).toBe(ESTATE_FINANCIALS_PATH);

    const client = fake();
    const view = renderAt(ESTATE_FINANCIALS_PATH, client);
    await settledScreen();
    const root = document.querySelector('[data-estate-root="financials"]') as HTMLElement;
    expect(root).not.toBeNull();
    expect(screen.getByRole("main", { name: "Financials" })).toContainElement(root);
    expect(screen.getByRole("heading", { level: 1, name: FINANCIALS_TITLE })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { level: 1, name: "Page not available" })).toBeNull();
    expect(client.calls).toHaveLength(1);
    expect(railCurrent()).toBe("Financials");
    view.unmount();

    // From another root, the rail's Financials link opens the estate root.
    const fromSites = fake();
    renderAt("/sites", fromSites);
    await settledScreen();
    expect(fromSites.calls).toEqual([]);
    fireEvent.click(within(rail()).getByRole("link", { name: "Financials" }));
    await settledScreen();
    expect(where()).toBe("/financials");
    expect(railCurrent()).toBe("Financials");
    expect(document.querySelector('[data-estate-root="financials"]')).not.toBeNull();
    expect(fromSites.calls).toHaveLength(1);
  });

  it("test_site_financials_route_unchanged", async () => {
    const client = fake();
    renderAt(`/sites/${encodeURIComponent(SITE_ID)}/financials`, client);
    await settledScreen();
    // The Site-relative suffix keeps its own handler: no estate read and no estate root.
    expect(client.calls).toEqual([]);
    expect(document.querySelector("[data-estate-root]")).toBeNull();
    expect(railCurrent()).toBe("Sites");
  });
});
