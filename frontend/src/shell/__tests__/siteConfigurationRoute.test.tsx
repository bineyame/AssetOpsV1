import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { App } from "../../App";
import { featureFlagsWith, type FeatureFlags } from "../../config/featureFlags";
import type {
  SiteDetailClient,
  SiteDirectoryClient,
} from "../../sites/siteDirectoryClient";
import type {
  SiteDetailReadModel,
  SiteSummary,
} from "../../sites/siteReadModel";
import { settledScreen } from "../../test/settled";

/**
 * The operator route for one site's configuration.
 *
 * What this file is about is the shell's side of the slice: that the
 * configuration is addressed under a site, that it is reached from that site,
 * that it is never gated, and that the parameterless placeholder it replaces
 * is gone from the route table and from operator navigation. What the screen
 * renders from a record is the substrate's, and is covered in
 * `sites/__tests__/siteConfiguration.test.tsx` against records.
 */

const DISABLED = featureFlagsWith(false);
const ENABLED = featureFlagsWith(true);

const SITE: SiteSummary = {
  site_id: "MG-002",
  display_name: "Kalangala Mini-Grid",
  site_type: "MINIGRID",
  location: { country: "Uganda", locality: "Kalangala" },
  timezone: "Africa/Kampala",
  lifecycle_status: "PLANNED",
  origin: "USER",
  source: { mode: "SIMULATED" },
  template: { template_id: "hybrid-mini-grid-100kw", template_version: 1 },
};

const SITE_DETAIL: SiteDetailReadModel = {
  ...SITE,
  foundation: {
    version: 1,
    valid_from: "2026-09-14T09:12:00Z",
    summary: "Solar-plus-storage mini-grid with a metered distribution load.",
    components: [
      {
        component_id: "pv-array",
        component_type: "PV_ARRAY",
        display_name: "PV array",
        rating: { value: 100, unit: "kW" },
      },
      {
        component_id: "site-meter",
        component_type: "METER",
        display_name: "Site meter",
        rating: null,
      },
    ],
  },
};

/**
 * Operator navigation as T004 left it.
 *
 * Both parameterless site destinations are in this list, and both have since
 * been removed by the slice that gave each an identified replacement. It is
 * kept here as the baseline the "navigation has not grown" assertion is made
 * against: the current list must be a subset of it, so no slice between T004
 * and now can have added an item and no slice can add one by removing two and
 * putting three back.
 */
const T004_OPERATOR_NAVIGATION_LABELS = [
  "Operator home",
  "Sites",
  "Site details",
  "Site configuration",
];

/** Operator navigation after T008, in order. */
const OPERATOR_NAVIGATION_LABELS = ["Operator home", "Sites"];

function directoryWith(sites: SiteSummary[]): SiteDirectoryClient {
  return { listSites: () => Promise.resolve({ status: "loaded", sites }) };
}

/** Resolves without regard to case, as the API does. */
function detailClientFor(sites: SiteDetailReadModel[]): SiteDetailClient {
  return {
    getSite: (siteId: string) => {
      const match = sites.find(
        (site) => site.site_id.toLowerCase() === siteId.toLowerCase(),
      );

      return Promise.resolve(
        match === undefined
          ? { status: "not_found" as const }
          : { status: "loaded" as const, site: match },
      );
    },
  };
}

function renderAt(path: string, flags: FeatureFlags = DISABLED) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App
        flags={flags}
        siteDirectory={directoryWith([SITE])}
        siteDetail={detailClientFor([SITE_DETAIL])}
      />
    </MemoryRouter>,
  );
}

describe("a site's configuration is addressed under that site", () => {
  it("renders the configuration of the site the address names", async () => {
    renderAt("/sites/MG-002/configuration");
    await settledScreen();

    expect(
      screen.getByRole("heading", { level: 1, name: "Site configuration" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("main").textContent).toMatch(/MG-002/);
    expect(screen.getByRole("main").textContent).toMatch(/PV array/);
  });

  it("resolves a case-variant address to the one canonical site", async () => {
    const { container } = renderAt("/sites/mg-002/configuration");
    await settledScreen();

    expect(container.textContent).toMatch(/MG-002/);
    expect(container.textContent).not.toMatch(/mg-002/);
  });

  it("states not found at the address of a site that is not configured", async () => {
    renderAt("/sites/MG-404/configuration");

    expect(
      await screen.findByRole("heading", { level: 2, name: "No such site" }),
    ).toBeInTheDocument();
  });

  it("is reached from the site by a plain link", async () => {
    renderAt("/sites/MG-002");
    await settledScreen();

    const link = screen.getByRole("link", { name: "Site configuration" });

    expect(link.getAttribute("href")).toBe("/sites/MG-002/configuration");

    fireEvent.click(link);
    await settledScreen();

    expect(
      screen.getByRole("heading", { level: 1, name: "Site configuration" }),
    ).toBeInTheDocument();
  });

  it("offers a way back to the site it belongs to", async () => {
    renderAt("/sites/MG-002/configuration");
    await settledScreen();

    const link = screen.getByRole("link", { name: "Back to this site" });

    expect(link.getAttribute("href")).toBe("/sites/MG-002");
  });

  it("renders the configuration inside the operator landmark", async () => {
    renderAt("/sites/MG-002/configuration");
    await settledScreen();

    const main = screen.getByRole("main");

    expect(
      within(main).getByRole("heading", { level: 1, name: "Site configuration" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("navigation", { name: "Operator routes" }),
    ).toBeInTheDocument();
  });
});

describe("site configuration is an operator capability and is never gated", () => {
  it.each([
    ["closed", DISABLED],
    ["open", ENABLED],
  ])("serves the configuration with the gate %s", async (_name, flags) => {
    renderAt("/sites/MG-002/configuration", flags);
    await settledScreen();

    expect(
      screen.getByRole("heading", { level: 1, name: "Site configuration" }),
    ).toBeInTheDocument();
  });

  it("renders identically in both gate states", async () => {
    const closed = renderAt("/sites/MG-002/configuration", DISABLED);
    await settledScreen(closed.container);
    const closedMarkup = closed.container.querySelector("main")?.innerHTML;
    closed.unmount();

    const open = renderAt("/sites/MG-002/configuration", ENABLED);
    await settledScreen(open.container);

    expect(open.container.querySelector("main")?.innerHTML).toBe(closedMarkup);
  });

  it.each([
    ["closed", DISABLED],
    ["open", ENABLED],
  ])("offers no crossing into the Simulator Lab with the gate %s", async (_name, flags) => {
    const { container } = renderAt("/sites/MG-002/configuration", flags);
    await settledScreen();

    expect(screen.getByRole("main").textContent).not.toMatch(/simulator/i);
    for (const anchor of Array.from(container.querySelectorAll("main a"))) {
      expect(anchor.getAttribute("href")).not.toMatch(/simulat/i);
    }
  });
});

describe("the parameterless Site Configuration placeholder is gone", () => {
  it.each([
    ["closed", DISABLED],
    ["open", ENABLED],
  ])("serves nothing at /site-configuration with the gate %s", (_name, flags) => {
    renderAt("/site-configuration", flags);

    expect(
      screen.getByRole("heading", { level: 1, name: "Page not available" }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("heading", { level: 2, name: "Site configuration unavailable" }),
    ).toBeNull();
  });

  it("has no operator navigation item that names no site", () => {
    const { container } = renderAt("/", ENABLED);

    const navigation = within(container).getByRole("navigation", {
      name: "Operator routes",
    });
    const destinations = within(navigation)
      .getAllByRole("link")
      .map((link) => link.getAttribute("href") ?? "");

    expect(
      within(navigation).getAllByRole("link").map((link) => link.textContent),
    ).toEqual(OPERATOR_NAVIGATION_LABELS);
    expect(destinations).not.toContain("/site-configuration");
    expect(destinations).not.toContain("/site-details");
    expect(navigation.textContent).not.toMatch(/site configuration/i);
    expect(navigation.textContent).not.toMatch(/site details/i);

    // Nor one that names a site: no navigation item could say which.
    expect(destinations.filter((href) => /^\/sites\/./.test(href))).toEqual([]);
  });

  it("has not gained a navigation item at any point since T004", () => {
    const { container } = renderAt("/", ENABLED);

    const labels = within(container)
      .getByRole("navigation", { name: "Operator routes" })
      .querySelectorAll("a");
    const rendered = Array.from(labels).map((link) => link.textContent ?? "");

    expect(rendered.length).toBeLessThanOrEqual(
      T004_OPERATOR_NAVIGATION_LABELS.length,
    );
    for (const label of rendered) {
      expect(T004_OPERATOR_NAVIGATION_LABELS).toContain(label);
    }
  });

  it("resolves every operator navigation item to a real surface", async () => {
    const { container, unmount } = renderAt("/", ENABLED);
    const hrefs = Array.from(
      within(container)
        .getByRole("navigation", { name: "Operator routes" })
        .querySelectorAll("a"),
    ).map((link) => link.getAttribute("href") ?? "");
    unmount();

    expect(hrefs).toHaveLength(OPERATOR_NAVIGATION_LABELS.length);
    for (const href of hrefs) {
      const view = renderAt(href, ENABLED);
      await settledScreen(view.container);

      expect(
        within(view.container).queryByRole("heading", {
          level: 1,
          name: "Page not available",
        }),
      ).toBeNull();
      view.unmount();
    }
  });
});
