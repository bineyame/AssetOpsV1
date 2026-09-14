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

/**
 * Route-level tests for one site, addressed by `site_id`.
 *
 * What a site renders from a record is tested in the substrate's own tests.
 * What is tested here is the part that belongs to the shell: that the route
 * exists and is reached from a Sites row, that it is an operator capability
 * served identically in both gate states, that an unknown site produces an
 * explicit not-found surface rather than an empty site, and that operator
 * navigation lost the parameterless placeholder and gained nothing.
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
  foundation: { version: 1, valid_from: "2026-09-14T09:12:00Z" },
};

/**
 * A site with no simulated provenance, for the gate assertions that scan text.
 * `Simulated` is legitimate source-mode provenance on a site page, so a scan
 * for the word only means something over a site that does not carry it.
 */
const LIVE_SITE_DETAIL: SiteDetailReadModel = {
  ...SITE_DETAIL,
  site_id: "MG-003",
  display_name: "Buvuma Mini-Grid",
  lifecycle_status: "ACTIVE",
  source: { mode: "LIVE" },
};

/**
 * The operator navigation list after T007. `Site details` is gone: it was a
 * parameterless placeholder from before site identity existed. Nothing took
 * its place, because a navigation item cannot name which site it would open.
 * `Site configuration` is still parameterless and is T008's to remove.
 */
const OPERATOR_NAVIGATION_LABELS = [
  "Operator home",
  "Sites",
  "Site configuration",
];

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

function renderAt(
  path: string,
  flags: FeatureFlags,
  sites: SiteDetailReadModel[] = [SITE_DETAIL],
) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App
        flags={flags}
        siteDirectory={directoryWith(sites)}
        siteDetail={detailClientFor(sites)}
      />
    </MemoryRouter>,
  );
}

describe("a site is opened from a Sites row", () => {
  it("renders the site the row addresses", async () => {
    renderAt("/sites", ENABLED);
    await screen.findByRole("table");

    fireEvent.click(screen.getByRole("link", { name: "MG-002" }));

    expect(
      await screen.findByRole("heading", {
        level: 1,
        name: "Kalangala Mini-Grid",
      }),
    ).toBeInTheDocument();
    expect(screen.getByRole("main")).toBeInTheDocument();
  });

  it("resolves a case-variant address to one canonical site", async () => {
    renderAt("/sites/mg-002", ENABLED);

    expect(
      await screen.findByRole("heading", {
        level: 1,
        name: "Kalangala Mini-Grid",
      }),
    ).toBeInTheDocument();
    expect(screen.getByRole("main").textContent).toMatch(/MG-002/);
    expect(screen.getByRole("main").textContent).not.toMatch(/mg-002/);
  });

  it("states not found for a site that is not configured", async () => {
    renderAt("/sites/MG-404", ENABLED);

    expect(
      await screen.findByRole("heading", { level: 2, name: "No such site" }),
    ).toBeInTheDocument();
    // An unknown site is a not-found surface on the site route, not the
    // catch-all: the address is served, the site is what is missing.
    expect(screen.queryByRole("heading", { name: "Page not available" })).toBeNull();
  });

  it("offers a way back to the Sites index and no other destination", async () => {
    const { container } = renderAt("/sites/MG-002", ENABLED);
    await screen.findByRole("heading", { level: 1, name: "Kalangala Mini-Grid" });

    const main = within(container).getByRole("main");

    expect(
      within(main)
        .getAllByRole("link")
        .map((link) => [link.getAttribute("href"), link.textContent]),
    ).toEqual([["/sites", "Back to Sites"]]);
  });

  it("offers no control on the site page beyond that one link", async () => {
    const { container } = renderAt("/sites/MG-002", ENABLED);
    await screen.findByRole("heading", { level: 1, name: "Kalangala Mini-Grid" });

    const main = within(container).getByRole("main");

    expect(
      main.querySelectorAll(
        "button, input, select, textarea, form, [role='button'], [role='tab'], [contenteditable='true']",
      ),
    ).toHaveLength(0);
    expect(main.querySelectorAll("[disabled], [aria-disabled]")).toHaveLength(0);
  });
});

describe("the site route is an operator capability", () => {
  it.each([
    ["gate off", DISABLED],
    ["gate on", ENABLED],
  ])("serves the site with the %s", async (_name, flags) => {
    renderAt("/sites/MG-002", flags as FeatureFlags);

    expect(
      await screen.findByRole("heading", {
        level: 1,
        name: "Kalangala Mini-Grid",
      }),
    ).toBeInTheDocument();
  });

  it("renders identical markup in both gate states", async () => {
    const enabled = renderAt("/sites/MG-002", ENABLED);
    await within(enabled.container).findByRole("heading", {
      level: 1,
      name: "Kalangala Mini-Grid",
    });
    const enabledMarkup = within(enabled.container).getByRole("main").outerHTML;
    enabled.unmount();

    const disabled = renderAt("/sites/MG-002", DISABLED);
    await within(disabled.container).findByRole("heading", {
      level: 1,
      name: "Kalangala Mini-Grid",
    });

    expect(within(disabled.container).getByRole("main").outerHTML).toBe(
      enabledMarkup,
    );
  });

  it.each([
    ["gate off", DISABLED],
    ["gate on", ENABLED],
  ])("names and reaches no simulator surface with the %s", async (_name, flags) => {
    const { container } = renderAt("/sites/MG-003", flags as FeatureFlags, [
      LIVE_SITE_DETAIL,
    ]);
    await screen.findByRole("heading", { level: 1, name: "Buvuma Mini-Grid" });

    const main = within(container).getByRole("main");

    // Scoped to the site page. The workspace utility chrome above the
    // operator shell carries the gated `Open Simulator Lab` entry point when
    // the gate is open, which is T004's chokepoint and not this route's; what
    // this slice must not add is a crossing from the site page itself.
    expect(main.textContent).not.toMatch(/simulat/i);
    for (const anchor of Array.from(main.querySelectorAll("a"))) {
      expect(anchor.getAttribute("href")).not.toMatch(/simulat/i);
    }
  });
});

describe("operator navigation lost an item and gained none", () => {
  it.each([
    ["gate off", DISABLED],
    ["gate on", ENABLED],
  ])("lists the same three operator items with the %s", (_name, flags) => {
    const { container, unmount } = renderAt("/", flags as FeatureFlags);

    const navigation = within(container).getByRole("navigation", {
      name: "Operator routes",
    });

    expect(
      within(navigation).getAllByRole("link").map((link) => link.textContent),
    ).toEqual(OPERATOR_NAVIGATION_LABELS);

    unmount();
  });

  it("has no navigation item that would open a site without naming one", () => {
    /**
     * The rule: a navigation destination appears only when the route behind it
     * renders a truthful surface, and a Site Details link that names no site
     * is not a destination.
     *
     * `Site configuration` is still in the list and is still parameterless.
     * That is deliberate and is T008's to remove, by the slice that makes its
     * identified replacement real; asserting it away here would either delete
     * a route this slice does not replace or weaken this assertion into
     * nothing. So what is pinned here is the site-page destination: no
     * navigation item leads to a site page, because none could say which site.
     */
    const { container } = renderAt("/", ENABLED);

    const navigation = within(container).getByRole("navigation", {
      name: "Operator routes",
    });
    const destinations = within(navigation)
      .getAllByRole("link")
      .map((link) => link.getAttribute("href") ?? "");

    expect(destinations).not.toContain("/site-details");
    expect(destinations.filter((href) => /^\/sites\/./.test(href))).toEqual([]);
    expect(navigation.textContent).not.toMatch(/site details/i);
  });

  it("serves nothing at the parameterless Site Details address", () => {
    renderAt("/site-details", ENABLED);

    expect(
      screen.getByRole("heading", { level: 1, name: "Page not available" }),
    ).toBeInTheDocument();
  });

  it("resolves every operator navigation item to a real surface", () => {
    const { container, unmount } = renderAt("/", ENABLED);
    const destinations = within(container)
      .getByRole("navigation", { name: "Operator routes" })
      .querySelectorAll("a");
    const hrefs = Array.from(destinations).map(
      (link) => link.getAttribute("href") ?? "",
    );
    unmount();

    expect(hrefs).toHaveLength(OPERATOR_NAVIGATION_LABELS.length);
    for (const href of hrefs) {
      const view = renderAt(href, ENABLED);

      expect(
        within(view.container).queryByRole("heading", {
          name: "Page not available",
        }),
        `${href} is a navigation item with no surface behind it`,
      ).toBeNull();

      view.unmount();
    }
  });
});
