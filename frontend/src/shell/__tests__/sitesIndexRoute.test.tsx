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
import { CREATE_SITE_ENTRY_POINT_LABEL } from "../simulatorLabRoutes";
import { settledScreen } from "../../test/settled";

/**
 * Route-level tests for the operator Sites index.
 *
 * The substrate's own behaviour is tested against records in
 * `src/sites/__tests__/sitesIndex.test.tsx`. What is tested here is the part
 * that belongs to the shell: that the index is an operator capability served
 * identically in both gate states, that the one action it offers is the gated
 * way into the Lab create flow, that a gate-off build offers nothing and names
 * nothing, and that neither operator navigation nor the route table grew.
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

/**
 * Operator navigation after T008. Both parameterless site destinations are
 * gone, each removed by the slice that gave it an identified replacement, and
 * neither replacement is a navigation item: a navigation item cannot name
 * which site it would open.
 */
const OPERATOR_NAVIGATION_LABELS = ["Operator home", "Sites"];

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
  },
};

function directoryWith(sites: SiteSummary[]): SiteDirectoryClient {
  return { listSites: () => Promise.resolve({ status: "loaded", sites }) };
}

/** Resolves the one site it holds, without regard to case, as the API does. */
function detailClientFor(site: SiteDetailReadModel): SiteDetailClient {
  return {
    getSite: (siteId: string) =>
      Promise.resolve(
        siteId.toLowerCase() === site.site_id.toLowerCase()
          ? { status: "loaded" as const, site }
          : { status: "not_found" as const },
      ),
  };
}

function renderSites(flags: FeatureFlags, sites: SiteSummary[] = []) {
  return render(
    <MemoryRouter initialEntries={["/sites"]}>
      <App flags={flags} siteDirectory={directoryWith(sites)} />
    </MemoryRouter>,
  );
}

describe("the Sites index is an operator capability", () => {
  it.each([
    ["gate off", DISABLED],
    ["gate on", ENABLED],
  ])("lists the same site with the %s", async (_name, flags) => {
    renderSites(flags as FeatureFlags, [SITE]);

    const row = within(await screen.findByRole("table")).getAllByRole("row")[1];

    expect(within(row).getByText("MG-002")).toBeInTheDocument();
    expect(within(row).getByText("Kalangala Mini-Grid")).toBeInTheDocument();
    expect(within(row).getByText("Simulated")).toBeInTheDocument();
    expect(within(row).getByText("User")).toBeInTheDocument();
    expect(within(row).getByText("Planned")).toBeInTheDocument();
    expect(
      within(row).getByText("hybrid-mini-grid-100kw v1"),
    ).toBeInTheDocument();
  });

  it("renders the same listing markup in both gate states", async () => {
    const enabled = renderSites(ENABLED, [SITE]);
    await within(enabled.container).findByRole("table");
    const enabledListing = enabled.container.querySelector("table")?.outerHTML;
    enabled.unmount();

    const disabled = renderSites(DISABLED, [SITE]);
    await within(disabled.container).findByRole("table");
    const disabledListing = disabled.container.querySelector("table")?.outerHTML;

    expect(disabledListing).toBe(enabledListing);
  });

  it("shows every rendered value from the record and nothing else numeric", async () => {
    renderSites(ENABLED, [SITE]);
    await screen.findByRole("table");

    const fromRecord = new Set(
      (JSON.stringify([SITE]).match(/\d+(?:\.\d+)?/g) ?? []),
    );
    const onScreen =
      screen.getByRole("table").textContent?.match(/\d+(?:\.\d+)?/g) ?? [];

    expect(onScreen.length).toBeGreaterThan(0);
    for (const value of onScreen) {
      expect(fromRecord).toContain(value);
    }
  });
});

describe("the gated way into the create flow", () => {
  it("offers exactly one action on the first-run empty state when the gate is open", async () => {
    const { container } = renderSites(ENABLED);
    await screen.findByRole("heading", { level: 2, name: "No sites configured" });

    const main = screen.getByRole("main");
    const links = within(main).getAllByRole("link");

    expect(links).toHaveLength(1);
    expect(links[0]).toHaveTextContent(CREATE_SITE_ENTRY_POINT_LABEL);
    expect(links[0]).toHaveAttribute("href", "/simulator-lab/create-site");
    expect(
      container.querySelectorAll("button, input, select, textarea, form"),
    ).toHaveLength(0);
  });

  it("opens the create flow from the Sites index", async () => {
    renderSites(ENABLED);
    await screen.findByRole("heading", { level: 2, name: "No sites configured" });

    fireEvent.click(
      screen.getByRole("link", { name: CREATE_SITE_ENTRY_POINT_LABEL }),
    );

    expect(
      screen.getByRole("heading", { level: 1, name: "Create a site" }),
    ).toBeInTheDocument();

    // The create flow reads the template catalog on mount. Settling it here
    // keeps that read inside the test rather than resolving after it.
    await settledScreen();
  });

  it("offers no way to add a site, and names no Simulator Lab, when the gate is closed", async () => {
    const { container } = renderSites(DISABLED);
    await screen.findByRole("heading", { level: 2, name: "No sites configured" });

    const main = screen.getByRole("main");

    expect(within(main).queryAllByRole("link")).toHaveLength(0);
    expect(
      container.querySelectorAll("button, input, select, textarea, form"),
    ).toHaveLength(0);
    expect(main.textContent).not.toMatch(/simulat/i);
    expect(main.textContent).not.toMatch(/create/i);
    expect(main.textContent).not.toMatch(/add a site/i);
  });

  it("still offers the create action once a site exists", async () => {
    renderSites(ENABLED, [SITE]);
    await screen.findByRole("table");

    expect(
      screen.getByRole("link", { name: CREATE_SITE_ENTRY_POINT_LABEL }),
    ).toHaveAttribute("href", "/simulator-lab/create-site");
  });

  it("puts the create action in the page header, not in the listing", async () => {
    render(
      <MemoryRouter initialEntries={["/sites"]}>
        <App flags={ENABLED} siteDirectory={directoryWith([SITE])} />
      </MemoryRouter>,
    );
    await settledScreen();

    const action = screen.getByRole("link", {
      name: CREATE_SITE_ENTRY_POINT_LABEL,
    });

    // Canonical screen 1 puts it beside the title. It is still the same gated
    // entry point from the same module, in the same two flag states, with the
    // label the T006 checkpoint settled: T011 moved where it sits and nothing
    // about when it exists or what it says.
    const header = screen.getByRole("heading", { level: 1, name: "Sites" })
      .closest("header");
    expect(header).not.toBeNull();
    expect(header?.contains(action)).toBe(true);

    // And not inside the listing, where it would read as a row action.
    expect(screen.getByRole("table").contains(action)).toBe(false);
  });

  it("is identical in both gate states apart from that one action", async () => {
    function markupWithout(html: string): string {
      // Everything except the header's action area, which is the one thing the
      // gate is allowed to change on this screen.
      return html.replace(
        /<div class="page-header__actions">[\s\S]*?<\/div>/,
        "",
      );
    }

    const enabled = render(
      <MemoryRouter initialEntries={["/sites"]}>
        <App flags={ENABLED} siteDirectory={directoryWith([SITE])} />
      </MemoryRouter>,
    );
    await settledScreen();
    const enabledMarkup = markupWithout(
      within(enabled.container).getByRole("main").innerHTML,
    );
    enabled.unmount();

    const disabled = render(
      <MemoryRouter initialEntries={["/sites"]}>
        <App flags={DISABLED} siteDirectory={directoryWith([SITE])} />
      </MemoryRouter>,
    );
    await settledScreen();
    const disabledMarkup = markupWithout(
      within(disabled.container).getByRole("main").innerHTML,
    );

    // The Sites index is an operator capability. The gate covers Lab surfaces
    // and execution, never a Site, so every column, badge, filter and value on
    // this screen must be byte-identical with the gate shut.
    expect(disabledMarkup).toBe(enabledMarkup);
  });

  it("keeps the action out of operator navigation in both gate states", async () => {
    for (const flags of [DISABLED, ENABLED]) {
      const view = renderSites(flags, [SITE]);
      await within(view.container).findByRole("table");

      const navigation = within(view.container).getByRole("navigation", {
        name: "Operator routes",
      });

      expect(
        within(navigation).getAllByRole("link").map((link) => link.textContent),
      ).toEqual(OPERATOR_NAVIGATION_LABELS);
      expect(navigation.textContent).not.toMatch(/simulat/i);
      expect(navigation.textContent).not.toMatch(/create/i);

      view.unmount();
    }
  });
});

describe("a Sites row is the way into a site", () => {
  it("opens the site the row names", async () => {
    render(
      <MemoryRouter initialEntries={["/sites"]}>
        <App
          flags={ENABLED}
          siteDirectory={directoryWith([SITE])}
          siteDetail={detailClientFor(SITE_DETAIL)}
        />
      </MemoryRouter>,
    );
    await screen.findByRole("table");

    // T011 puts the name and the identity in one cell, so the row link is
    // named for the site rather than for its ID. The address is unchanged and
    // is still built from `site_id`, which the substrate test pins.
    fireEvent.click(
      screen.getByRole("link", { name: SITE.display_name }),
    );

    expect(
      await screen.findByRole("heading", {
        level: 1,
        name: "Kalangala Mini-Grid",
      }),
    ).toBeInTheDocument();
  });

  it("adds exactly one destination and no navigation item", async () => {
    /**
     * T006 asserted that no per-site destination existed. It exists now, so
     * the assertion is replaced rather than dropped, and the replacement is
     * the stronger half: the index offers the site row link and the gated
     * create action and nothing else, and operator navigation still gained
     * nothing.
     */
    const view = render(
      <MemoryRouter initialEntries={["/sites"]}>
        <App
          flags={ENABLED}
          siteDirectory={directoryWith([SITE])}
          siteDetail={detailClientFor(SITE_DETAIL)}
        />
      </MemoryRouter>,
    );
    await screen.findByRole("table");

    const main = within(view.container).getByRole("main");

    // The row now offers the name and a `View` action, both resolving to the
    // same site. The claim is unchanged - the index adds one destination per
    // site and the gated create action, and nothing else - so it is asserted
    // on the set of destinations rather than on the number of anchors.
    const hrefs = within(main)
      .getAllByRole("link")
      .map((link) => link.getAttribute("href"));

    expect(hrefs).toEqual([
      "/simulator-lab/create-site",
      "/sites/MG-002",
      "/sites/MG-002",
    ]);
    expect(new Set(hrefs)).toEqual(
      new Set(["/sites/MG-002", "/simulator-lab/create-site"]),
    );

    const navigation = within(view.container).getByRole("navigation", {
      name: "Operator routes",
    });

    expect(
      within(navigation).getAllByRole("link").map((link) => link.textContent),
    ).toEqual(OPERATOR_NAVIGATION_LABELS);
  });

  it.each(["/sites/MG-002/devices", "/sites/MG-002/gateway"])(
    "still serves nothing under a site at %s",
    (path) => {
      // T007 listed `/sites/MG-002/configuration` here too. T008 makes that
      // one real, so it moves out of this list rather than the list being
      // dropped: what is pinned is that a site grows addressable aspects one
      // reviewed slice at a time, and devices is causal step 4's to make true.
      render(
        <MemoryRouter initialEntries={[path]}>
          <App
            flags={ENABLED}
            siteDirectory={directoryWith([SITE])}
            siteDetail={detailClientFor(SITE_DETAIL)}
          />
        </MemoryRouter>,
      );

      expect(
        screen.getByRole("heading", { level: 1, name: "Page not available" }),
      ).toBeInTheDocument();
    },
  );

  it("no longer serves the parameterless Site Details frame", () => {
    // T007 removed the placeholder its identified route replaced, and T008
    // removed `/site-configuration` the same way. Neither is served now.
    render(
      <MemoryRouter initialEntries={["/site-details"]}>
        <App flags={ENABLED} siteDirectory={directoryWith([SITE])} />
      </MemoryRouter>,
    );

    expect(
      screen.getByRole("heading", { level: 1, name: "Page not available" }),
    ).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Site details" })).toBeNull();
  });

  it("no longer serves the parameterless Site Configuration frame", () => {
    render(
      <MemoryRouter initialEntries={["/site-configuration"]}>
        <App flags={ENABLED} siteDirectory={directoryWith([SITE])} />
      </MemoryRouter>,
    );

    expect(
      screen.getByRole("heading", { level: 1, name: "Page not available" }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("heading", { name: "Site configuration" }),
    ).toBeNull();
  });

  it("reaches a site's configuration from that site, not from the index", async () => {
    render(
      <MemoryRouter initialEntries={["/sites"]}>
        <App
          flags={ENABLED}
          siteDirectory={directoryWith([SITE])}
          siteDetail={detailClientFor(SITE_DETAIL)}
        />
      </MemoryRouter>,
    );
    await screen.findByRole("table");

    // The index offers one destination per site, and that destination is the
    // site. A configuration link on a row would be a second way in, addressed
    // by the same identity, which is how two ways into one thing start to
    // disagree about what it is.
    const main = screen.getByRole("main");

    expect(
      within(main)
        .getAllByRole("link")
        .map((link) => link.getAttribute("href")),
    ).not.toContain("/sites/MG-002/configuration");
  });
});
