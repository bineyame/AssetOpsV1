import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import { ESTATE_EVIDENCE_PATH, EVIDENCE_TITLE } from "../../estate/EstateEvidence";
import type {
  EstateEvidenceBody,
  EstateEvidenceMoneyClient,
  EvidenceResult,
} from "../../estate/estateEvidenceMoneyClient";
import { POPULATED_EVIDENCE, evidenceClient } from "../../sites/__tests__/evidenceFixtures";
import { HYBRID_MINI_GRID_SITE } from "../../sites/__tests__/sldFixtures";
import type { SiteDetailClient, SiteDirectoryClient } from "../../sites/siteDirectoryClient";
import { settledScreen } from "../../test/settled";
import { EVIDENCE_PATH } from "../operatorSiteRoutes";

/**
 * W3-02 commit 2 (`.agent/W3-02-lane-a-requests.md` commit-2 items 1-3): the estate Evidence root is mounted in the
 * operator shell at `/evidence` through `EstateEvidenceFrame` (which owns `<main>`), the rail's Evidence root is
 * live, and the Site-relative `/sites/{code}/evidence` route keeps its own handler.
 */

const SITE_ID = HYBRID_MINI_GRID_SITE.site_id;
const DIRECTORY: SiteDirectoryClient = { listSites: () => Promise.resolve({ status: "loaded", sites: [] }) };
const DETAIL: SiteDetailClient = {
  getSite: () => Promise.resolve({ status: "loaded", site: HYBRID_MINI_GRID_SITE }),
};

function emptyBody(): EstateEvidenceBody {
  return {
    schema_version: "estate-evidence-1",
    scope: { tenant_id: "t", authorized_site_count: 0, covered_site_count: 0, access_basis: `sha256:${"b".repeat(64)}` },
    window: { from: "2026-10-13T00:00:00Z", to: "2026-10-20T00:00:00Z", bounds: "[from, to)", known_at: "2026-10-20T09:30:00Z" },
    status: "EMPTY_SCOPE",
    coverage: { state: "EMPTY", sites: [] },
    summary: {
      limited_site_count: 0,
      priority_gap_count: null,
      unsupported_claim_count: null,
      capability_count: 0,
      full_count: 0,
      limited_count: 0,
      none_count: 0,
      unknown_count: 0,
    },
    order: "site_code_key asc, site_id asc, capability_key asc",
    total_count: 0,
    rows: [],
    gaps: [],
    next_cursor: null,
    selection_token: `sha256:${"c".repeat(64)}`,
  } as EstateEvidenceBody;
}

function fake(): EstateEvidenceMoneyClient & { calls: unknown[] } {
  const calls: unknown[] = [];
  const result: EvidenceResult<EstateEvidenceBody> = { status: "loaded", value: emptyBody() };
  return {
    calls,
    evidence: (query) => {
      calls.push(query);
      return Promise.resolve(result);
    },
  };
}

function LocationProbe() {
  const location = useLocation();
  return <output data-location>{location.pathname}</output>;
}

function renderAt(path: string, client: EstateEvidenceMoneyClient) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App
        flags={featureFlagsWith(false)}
        siteDirectory={DIRECTORY}
        siteDetail={DETAIL}
        siteEvidence={evidenceClient({ status: "loaded", value: POPULATED_EVIDENCE })}
        estateEvidenceMoney={client}
      />
      <LocationProbe />
    </MemoryRouter>,
  );
}

const where = () => document.querySelector("[data-location]")?.textContent ?? "";
const rail = () => screen.getByRole("navigation", { name: "Operator routes" });
const railCurrent = () => rail().querySelector('[aria-current="page"]')?.textContent ?? null;

describe("W3-02 estate Evidence root in the operator shell", () => {
  it("test_estate_evidence_route_and_live_rail", async () => {
    // The shell's route constant mirrors the estate page's own path.
    expect(EVIDENCE_PATH).toBe(ESTATE_EVIDENCE_PATH);

    const client = fake();
    const view = renderAt(ESTATE_EVIDENCE_PATH, client);
    await settledScreen();
    const root = document.querySelector('[data-estate-root="evidence"]') as HTMLElement;
    expect(root).not.toBeNull();
    expect(screen.getByRole("main", { name: "Evidence" })).toContainElement(root);
    expect(screen.getByRole("heading", { level: 1, name: EVIDENCE_TITLE })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { level: 1, name: "Page not available" })).toBeNull();
    expect(client.calls).toHaveLength(1);
    expect(railCurrent()).toBe("Evidence");
    view.unmount();

    // From another root, the rail's Evidence link opens the estate root; Financials is its own live root (commit 4).
    const fromSites = fake();
    renderAt("/sites", fromSites);
    await settledScreen();
    expect(within(rail()).getByRole("link", { name: "Financials" })).toHaveAttribute("href", "/financials");
    expect(fromSites.calls).toEqual([]);
    fireEvent.click(within(rail()).getByRole("link", { name: "Evidence" }));
    await settledScreen();
    expect(where()).toBe("/evidence");
    expect(railCurrent()).toBe("Evidence");
    expect(document.querySelector('[data-estate-root="evidence"]')).not.toBeNull();
    expect(fromSites.calls).toHaveLength(1);
  });

  it("test_site_evidence_route_unchanged", async () => {
    const client = fake();
    renderAt(`/sites/${encodeURIComponent(SITE_ID)}/evidence`, client);
    await settledScreen();
    // The Site-relative suffix keeps its own handler: no estate read and no estate root.
    expect(client.calls).toEqual([]);
    expect(document.querySelector("[data-estate-root]")).toBeNull();
    expect(railCurrent()).toBe("Sites");
  });
});
