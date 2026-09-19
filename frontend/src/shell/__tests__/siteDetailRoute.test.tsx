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
import { spacedText } from "../../test/text";

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
  foundation: {
    version: 1,
    valid_from: "2026-09-14T09:12:00Z",
    summary:
      "Solar-plus-storage mini-grid with a diesel generator for backup and a " +
      "metered distribution load.",
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
    // This site's foundation declares none of the four sections
    // T014 added. `null` is that statement; the backend refuses an
    // empty list, so there is no other way to say it.
    topology: null,
    devices: null,
    signal_mappings: null,
    control_assumptions: null,
  },
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
 * The operator navigation list after T008. `Site details` and `Site
 * configuration` are both gone: each was a parameterless placeholder from
 * before site identity existed, and each was removed by the slice that gave it
 * an identified replacement. Nothing took either place, because a navigation
 * item cannot name which site it would open.
 */
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

/**
 * One `<main>` markup string with the Quick Actions panel removed, and nothing
 * else removed.
 *
 * The panel is found by its own heading id rather than by position or by
 * matching text, so this cannot quietly start stripping more than it was
 * written to strip. It throws when the panel is not there, because a stripper
 * that silently removes nothing would turn this comparison into a comparison
 * of two identical unstripped strings and pass for the wrong reason.
 */
const PANEL_OPEN = '<section class="panel"';

function stripQuickActions(markup: string): string {
  const panels = markup.split(PANEL_OPEN);
  const kept = panels.filter(
    (panel) => !panel.includes('id="site-detail-actions-heading"'),
  );

  if (kept.length === panels.length) {
    throw new Error(
      "No Quick Actions panel found to strip. The comparison this feeds would " +
        "have passed without comparing what it exists to compare.",
    );
  }

  return kept.join(PANEL_OPEN);
}

describe("a site is opened from a Sites row", () => {
  it("renders the site the row addresses", async () => {
    renderAt("/sites", ENABLED);
    await screen.findByRole("table");

    fireEvent.click(screen.getByRole("link", { name: SITE.display_name }));

    expect(
      await screen.findByRole("heading", {
        level: 1,
        name: "MG-002",
      }),
    ).toBeInTheDocument();
    expect(screen.getByRole("main")).toBeInTheDocument();
  });

  it("resolves a case-variant address to one canonical site", async () => {
    renderAt("/sites/mg-002", ENABLED);

    expect(
      await screen.findByRole("heading", {
        level: 1,
        name: "MG-002",
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

  it("offers the Site tab destinations and the Sites index, and nothing else", async () => {
    const { container } = renderAt("/sites/MG-002", ENABLED);
    await screen.findByRole("heading", { level: 1, name: "MG-002" });

    const main = within(container).getByRole("main");

    // T008 pinned this exactly rather than loosening it into "contains Back to
    // Sites", and it stays pinned: the point of the assertion is that the site
    // page grows destinations one reviewed slice at a time. T011A replaces
    // T008's plain `Site configuration` link with the canonical Site tab row,
    // so the destinations are now Overview and Foundation. All of it is
    // navigation, none of it is an action on the site, and the six
    // labelled-in-place tabs add nothing here because they are not links.
    expect(
      within(main)
        .getAllByRole("link")
        .map((link) => [link.getAttribute("href"), link.textContent]),
    ).toEqual([
      ["/sites", "Sites"],
      ["/sites/MG-002", "Overview"],
      ["/sites/MG-002/foundation", "Foundation"],
    ]);
  });

  it("offers no enabled control on the site page", async () => {
    const { container } = renderAt("/sites/MG-002", ENABLED);
    await screen.findByRole("heading", { level: 1, name: "MG-002" });

    const main = within(container).getByRole("main");

    // T007 asserted no control at all. T012 adds the Quick Actions panel, and
    // every control in it is disabled with its reason, so what stays absolute
    // is the claim underneath: nothing on this page can be operated. An
    // enabled control here would be a capability the product does not have.
    const controls = Array.from(
      main.querySelectorAll(
        "button, input, select, textarea, form, [role='button'], [role='tab'], [contenteditable='true']",
      ),
    );

    expect(controls.length).toBeGreaterThan(0);
    expect(main.querySelectorAll("input, select, textarea, form")).toHaveLength(0);
    for (const control of controls) {
      expect(control.tagName).toBe("BUTTON");
      expect((control as HTMLButtonElement).disabled).toBe(true);
    }
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
        name: "MG-002",
      }),
    ).toBeInTheDocument();
  });

  it("renders identical Site facts in both gate states", async () => {
    const enabled = renderAt("/sites/MG-002", ENABLED);
    await within(enabled.container).findByRole("heading", {
      level: 1,
      name: "MG-002",
    });
    const enabledMarkup = within(enabled.container).getByRole("main").outerHTML;
    enabled.unmount();

    const disabled = renderAt("/sites/MG-002", DISABLED);
    await within(disabled.container).findByRole("heading", {
      level: 1,
      name: "MG-002",
    });

    // Everything except the Quick Actions panel, which T012 makes differ on
    // purpose: the gated actions are absent with the gate off and rendered
    // disabled with it open. That is the gate rule doing its job rather than
    // the gate leaking into Site semantics, so what must not vary is every
    // fact about the site, and the panel is removed from both sides.
    expect(
      stripQuickActions(within(disabled.container).getByRole("main").outerHTML),
    ).toBe(stripQuickActions(enabledMarkup));
  });

  it("names no simulator surface at all with the gate off", async () => {
    const { container } = renderAt("/sites/MG-003", DISABLED, [
      LIVE_SITE_DETAIL,
    ]);
    await screen.findByRole("heading", { level: 1, name: "MG-003" });

    const main = within(container).getByRole("main");

    // Scoped to the site page. The workspace utility chrome above the operator
    // shell carries the gated `Open Simulator Lab` entry point when the gate
    // is open, which is T004's chokepoint and not this route's.
    //
    // With the gate closed this page says nothing about a Simulator Lab at
    // all: not a control, not a label, not a greyed-out hint that a developer
    // workspace exists. That is the gate rule, and it is stricter than the
    // sequencing rule below.
    expect(spacedText(main)).not.toMatch(/simulat/i);
    for (const anchor of Array.from(main.querySelectorAll("a"))) {
      expect(anchor.getAttribute("href")).not.toMatch(/simulat/i);
    }
  });

  it.each([
    ["gate off", DISABLED],
    ["gate on", ENABLED],
  ])("reaches no simulator surface with the %s", async (_name, flags) => {
    const { container } = renderAt("/sites/MG-003", flags as FeatureFlags, [
      LIVE_SITE_DETAIL,
    ]);
    await screen.findByRole("heading", { level: 1, name: "MG-003" });

    const main = within(container).getByRole("main");

    // This half of the claim is absolute in both states and is the one that
    // matters. With the gate open T012 names two Lab actions, disabled, with
    // their prerequisites. Naming is not reaching: there is no link, no href,
    // and nothing a click can follow.
    for (const anchor of Array.from(main.querySelectorAll("a"))) {
      expect(anchor.getAttribute("href")).not.toMatch(/simulat/i);
    }
    expect(main.innerHTML).not.toMatch(/href="[^"]*simulat/i);
  });

  it("names the two Lab actions with the gate on, disabled and inert", async () => {
    const { container } = renderAt("/sites/MG-003", ENABLED, [
      LIVE_SITE_DETAIL,
    ]);
    await screen.findByRole("heading", { level: 1, name: "MG-003" });

    const main = within(container).getByRole("main");

    // The sequencing rule, as opposed to the gate rule above. The capability
    // is one the map can sequence and cannot yet perform, so it is rendered
    // and disabled with the step that would make it work named beside it.
    for (const label of ["Open in Simulator Lab", "Start Simulation"]) {
      const action = within(main).getByRole("button", { name: label });

      expect((action as HTMLButtonElement).disabled).toBe(true);

      const reason = main.querySelector(
        "#" + action.getAttribute("aria-describedby"),
      );

      expect(reason?.textContent ?? "").not.toBe("");
    }

    const before = main.innerHTML;
    fireEvent.click(within(main).getByRole("button", { name: "Start Simulation" }));

    expect(main.innerHTML).toBe(before);
  });
});

describe("operator navigation lost an item and gained none", () => {
  it.each([
    ["gate off", DISABLED],
    ["gate on", ENABLED],
  ])("lists the same two operator items with the %s", (_name, flags) => {
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
     * renders a truthful surface, and a link that names no site is not a
     * destination.
     *
     * Both parameterless placeholders are gone now, so both are asserted away
     * here. What is still pinned alongside them is the site-page destination:
     * no navigation item leads to a site page either, because none could say
     * which site it would open.
     */
    const { container } = renderAt("/", ENABLED);

    const navigation = within(container).getByRole("navigation", {
      name: "Operator routes",
    });
    const destinations = within(navigation)
      .getAllByRole("link")
      .map((link) => link.getAttribute("href") ?? "");

    expect(destinations).not.toContain("/site-details");
    expect(destinations).not.toContain("/site-configuration");
    expect(destinations.filter((href) => /^\/sites\/./.test(href))).toEqual([]);
    expect(spacedText(navigation)).not.toMatch(/site details/i);
    expect(spacedText(navigation)).not.toMatch(/site configuration/i);
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
