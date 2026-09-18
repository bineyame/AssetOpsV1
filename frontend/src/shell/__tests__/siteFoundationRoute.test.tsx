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
 * The operator route for one site's Foundation.
 *
 * What this file is about is the shell's side of the slice: that the
 * Foundation is addressed under a site, that it is reached from that site's
 * tab row, that it is never gated, that the address T008 served it at still
 * resolves without becoming a second surface, and that the parameterless
 * placeholder it replaces is gone from the route table and from operator
 * navigation. What the screen renders from a record is the substrate's, and is
 * covered in `sites/__tests__/siteConfiguration.test.tsx` against records.
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
 *
 * The labels are T004's own, which is why one of them is spelled `Site
 * configuration`. This is a record of what was there, not a name the product
 * still uses.
 */
const T004_OPERATOR_NAVIGATION_LABELS = [
  "Operator home",
  "Sites",
  "Site details",
  "Site configuration",
];

/** Operator navigation after T008, in order. T011A does not change it. */
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

describe("a site's Foundation is addressed under that site", () => {
  it("renders the Foundation of the site the address names", async () => {
    renderAt("/sites/MG-002/foundation");
    await settledScreen();

    expect(
      screen.getByRole("heading", { level: 1, name: "Foundation" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("main").textContent).toMatch(/MG-002/);
    expect(screen.getByRole("main").textContent).toMatch(/PV array/);
  });

  it("resolves a case-variant address to the one canonical site", async () => {
    const { container } = renderAt("/sites/mg-002/foundation");
    await settledScreen();

    expect(container.textContent).toMatch(/MG-002/);
    expect(container.textContent).not.toMatch(/mg-002/);
  });

  it("states not found at the address of a site that is not configured", async () => {
    renderAt("/sites/MG-404/foundation");

    expect(
      await screen.findByRole("heading", { level: 2, name: "No such site" }),
    ).toBeInTheDocument();
  });

  it("is reached from the site by the Foundation tab", async () => {
    renderAt("/sites/MG-002");
    await settledScreen();

    const link = screen.getByRole("link", { name: "Foundation" });

    expect(link.getAttribute("href")).toBe("/sites/MG-002/foundation");

    fireEvent.click(link);
    await settledScreen();

    expect(
      screen.getByRole("heading", { level: 1, name: "Foundation" }),
    ).toBeInTheDocument();
  });

  it("offers a way back to the site it belongs to", async () => {
    renderAt("/sites/MG-002/foundation");
    await settledScreen();

    // T008 had a `Back to this site` link here. The Overview tab is that way
    // back now, under the name the product gives that surface, so there is one
    // link to the site rather than two a reader has to tell apart.
    const link = screen.getByRole("link", { name: "Overview" });

    expect(link.getAttribute("href")).toBe("/sites/MG-002");
    expect(screen.queryByRole("link", { name: "Back to this site" })).toBeNull();
  });

  it("renders the Foundation inside the operator landmark", async () => {
    renderAt("/sites/MG-002/foundation");
    await settledScreen();

    const main = screen.getByRole("main");

    expect(
      within(main).getByRole("heading", { level: 1, name: "Foundation" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("navigation", { name: "Operator routes" }),
    ).toBeInTheDocument();
  });

  it("names the surface Foundation and never Site configuration", async () => {
    renderAt("/sites/MG-002/foundation");
    await settledScreen();

    const main = screen.getByRole("main");

    // The domain word survives the rename: a site still has a configuration
    // origin and its configuration is still fixed at creation. What must not
    // survive is the screen being called Site configuration.
    expect(main.textContent).toMatch(/Configuration is fixed at creation/);
    expect(main.textContent).toMatch(/Configuration origin/);
    expect(main.textContent).not.toMatch(/Site configuration/i);
    expect(
      screen.queryByRole("heading", { name: /Site configuration/i }),
    ).toBeNull();
  });
});

describe("the Foundation surface is an operator capability and is never gated", () => {
  it.each([
    ["closed", DISABLED],
    ["open", ENABLED],
  ])("serves the Foundation with the gate %s", async (_name, flags) => {
    renderAt("/sites/MG-002/foundation", flags);
    await settledScreen();

    expect(
      screen.getByRole("heading", { level: 1, name: "Foundation" }),
    ).toBeInTheDocument();
  });

  it("renders identically in both gate states", async () => {
    const closed = renderAt("/sites/MG-002/foundation", DISABLED);
    await settledScreen(closed.container);
    const closedMarkup = closed.container.querySelector("main")?.innerHTML;
    closed.unmount();

    const open = renderAt("/sites/MG-002/foundation", ENABLED);
    await settledScreen(open.container);

    expect(open.container.querySelector("main")?.innerHTML).toBe(closedMarkup);
  });

  it.each([
    ["closed", DISABLED],
    ["open", ENABLED],
  ])(
    "offers no crossing into the Simulator Lab with the gate %s",
    async (_name, flags) => {
      const { container } = renderAt("/sites/MG-002/foundation", flags);
      await settledScreen();

      expect(screen.getByRole("main").textContent).not.toMatch(/simulator/i);
      for (const anchor of Array.from(container.querySelectorAll("main a"))) {
        expect(anchor.getAttribute("href")).not.toMatch(/simulat/i);
      }
    },
  );
});

describe("the address T008 served this surface at still resolves", () => {
  it("redirects to the Foundation of the same site", async () => {
    renderAt("/sites/MG-002/configuration");
    await settledScreen();

    expect(
      screen.getByRole("heading", { level: 1, name: "Foundation" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("main").textContent).toMatch(/MG-002/);
    expect(
      screen.getByRole("link", { name: "Foundation" }).getAttribute("href"),
    ).toBe("/sites/MG-002/foundation");
  });

  it("carries the identity across rather than dropping it", async () => {
    renderAt("/sites/MG-404/configuration");

    // A redirect that lost the site would land on a Foundation with no
    // subject, or on whichever site happened to be first. This one arrives at
    // MG-404's own Foundation, which then says no such site is configured.
    expect(
      await screen.findByRole("heading", { level: 2, name: "No such site" }),
    ).toBeInTheDocument();
  });

  it("carries a case-variant identity across untouched", async () => {
    const { container } = renderAt("/sites/mg-002/configuration");
    await settledScreen();

    expect(container.textContent).toMatch(/MG-002/);
    expect(container.textContent).not.toMatch(/mg-002/);
  });

  it("renders no surface of its own", async () => {
    renderAt("/sites/MG-002/configuration");
    await settledScreen();

    // One landmark, one page heading, and it is the Foundation. A redirect
    // that rendered anything of its own would be a second product surface for
    // one thing, which is what a compatibility address must not become.
    expect(screen.getAllByRole("main")).toHaveLength(1);
    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
  });

  it("is offered as a destination by nothing on either surface", async () => {
    for (const path of ["/sites/MG-002", "/sites/MG-002/foundation"]) {
      const view = renderAt(path, ENABLED);
      await settledScreen(view.container);

      const hrefs = Array.from(view.container.querySelectorAll("a")).map(
        (anchor) => anchor.getAttribute("href") ?? "",
      );

      expect(hrefs.length).toBeGreaterThan(0);
      for (const href of hrefs) {
        expect(href).not.toMatch(/\/configuration$/);
      }
      view.unmount();
    }
  });
});

describe("the parameterless Site Configuration placeholder is gone", () => {
  it.each([
    ["closed", DISABLED],
    ["open", ENABLED],
  ])(
    "serves nothing at /site-configuration with the gate %s",
    (_name, flags) => {
      renderAt("/site-configuration", flags);

      expect(
        screen.getByRole("heading", { level: 1, name: "Page not available" }),
      ).toBeInTheDocument();
      expect(
        screen.queryByRole("heading", {
          level: 2,
          name: "Site configuration unavailable",
        }),
      ).toBeNull();
    },
  );

  it("has no operator navigation item that names no site", () => {
    const { container } = renderAt("/", ENABLED);

    const navigation = within(container).getByRole("navigation", {
      name: "Operator routes",
    });
    const destinations = within(navigation)
      .getAllByRole("link")
      .map((link) => link.getAttribute("href") ?? "");

    expect(
      within(navigation)
        .getAllByRole("link")
        .map((link) => link.textContent),
    ).toEqual(OPERATOR_NAVIGATION_LABELS);
    expect(destinations).not.toContain("/site-configuration");
    expect(destinations).not.toContain("/site-details");
    expect(navigation.textContent).not.toMatch(/site configuration/i);
    expect(navigation.textContent).not.toMatch(/site details/i);

    // The rename does not put the surface into the rail under its new name
    // either: a rail item still could not say which site it would open.
    expect(navigation.textContent).not.toMatch(/foundation/i);

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
