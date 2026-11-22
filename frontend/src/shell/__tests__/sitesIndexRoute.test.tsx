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
import { spacedText } from "../../test/text";
import { estateE0, sitesE1 } from "../../test/sitesE1";
import type { PortfolioSites } from "../../estate/portfolioSitesClient";
import SITES_OCT from "../../estate/__tests__/fixtures/iap/sites-2026-10.json?raw";

/**
 * IA-P P4b (spec §6 P4b): `/sites` is the Sites list on the one list component; the directory table ("Site inventory")
 * and the v69 "In setup" panel are gone. These tests read the list. E1 serves no rows unless a test says so, so the
 * directory's Sites are the rows (D-IAP.35 Q1).
 */
const sitesList = () => document.querySelector<HTMLElement>('[data-home-list="sites"]');
async function findList(): Promise<HTMLElement> {
  await settledScreen();
  const list = sitesList();
  expect(list).not.toBeNull();
  return list!;
}
/** The list's empty sentence (HomeList `def.none`). */
const NO_SITES = "No Sites in this scope.";
const pathOf = (href: string | null) => (href ?? "").split("?")[0];

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
 *
 * T028 adds Findings (`D-2026-10-02-grammar-ownership-test`): the INTELLIGENCE
 * rail root, which owns the global Findings index and names no site. Neither
 * the site row nor the gated create action is a navigation item.
 */
// W6-01e: Operational records rail root is live.
const OPERATOR_NAVIGATION_LABELS = ["Portfolio", "Sites", "Findings", "Decisions", "Actions", "Incidents", "Maintenance", "Results", "Evidence & records", "Financials"];

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
        properties: null,
      },
      {
        component_id: "site-meter",
        component_type: "METER",
        display_name: "Site meter",
        rating: null,
        properties: null,
      },
    ],
    // This site's foundation declares none of the four sections
    // T014 added. `null` is that statement; the backend refuses an
    // empty list, so there is no other way to say it.
    topology: null,
    devices: null,
    signal_mappings: null,
    control_assumptions: null,
    site_controls: null,
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

function renderSites(flags: FeatureFlags, sites: SiteSummary[] = [], waiting: Record<string, number> = {}) {
  return render(
    <MemoryRouter initialEntries={["/sites"]}>
      <App flags={flags} siteDirectory={directoryWith(sites)} portfolioSites={sitesE1()} estateIndex={estateE0(waiting)} />
    </MemoryRouter>,
  );
}

describe("the Sites index is an operator capability", () => {
  it.each([
    ["gate off", DISABLED],
    ["gate on", ENABLED],
  ])("lists the same site with the %s", async (_name, flags) => {
    renderSites(flags as FeatureFlags, [SITE]);

    // IA-P P4b (§6 P4b, D-IAP.35 Q1): the row is the list's; the directory's ID, source, origin, lifecycle and template
    // cells left with the directory table. The Site's name links to it, its Group comes from `site_type`.
    const row = (await findList()).querySelector<HTMLElement>('tbody tr[data-row="MG-002"]')!;
    expect(within(row).getByRole("link", { name: "Kalangala Mini-Grid" })).toBeInTheDocument();
    expect(row.querySelector('[data-label="Group"]')?.textContent).toBe("Mini-grid");
    expect(row.querySelector('[data-label="Waiting for a choice"]')?.textContent).toBe("0");
  });

  it("shows the app-wide demonstration note with the client-facing wording (OWN-G3b R2-G3b 16)", async () => {
    renderSites(ENABLED, [SITE]);
    await findList();

    expect(screen.getByRole("note")).toHaveTextContent(/^Demonstration · example sites and records$/);
  });

  it("renders the same listing markup in both gate states", async () => {
    const enabled = renderSites(ENABLED, [SITE]);
    const enabledListing = (await findList()).outerHTML;
    enabled.unmount();

    renderSites(DISABLED, [SITE]);
    const disabledListing = (await findList()).outerHTML;

    expect(disabledListing).toContain("Kalangala Mini-Grid");
    expect(disabledListing).toBe(enabledListing);
  });

  it("shows every rendered value from the record and nothing else numeric", async () => {
    // IA-P P4b: a directory-only row's one figure is E0's waiting count (D-IAP.35 Q1), so E0 is a record here too.
    const waiting = { "MG-002": 7 };
    renderSites(ENABLED, [SITE], waiting);
    const list = await findList();

    const fromRecord = new Set(
      (JSON.stringify([SITE, waiting]).match(/\d+(?:\.\d+)?/g) ?? []),
    );
    const onScreen = list.querySelector("table")?.textContent?.match(/\d+(?:\.\d+)?/g) ?? [];

    expect(onScreen.length).toBeGreaterThan(0);
    for (const value of onScreen) {
      expect(fromRecord).toContain(value);
    }
  });
});

describe("the gated way into the create flow", () => {
  it("offers exactly one action on the first-run empty state when the gate is open", async () => {
    const { container } = renderSites(ENABLED);
    await screen.findByText(NO_SITES);

    const main = screen.getByRole("main");
    const links = within(main).getAllByRole("link");

    expect(links).toHaveLength(1);
    expect(links[0]).toHaveTextContent(CREATE_SITE_ENTRY_POINT_LABEL);
    expect(links[0]).toHaveAttribute("href", "/simulator-lab/create-site");
    expect(
      container.querySelectorAll(
        "button:not([data-shared-range-button]):not([data-shell-control]), input, select, textarea, form",
      ),
    ).toHaveLength(0);
  });

  it("opens the create flow from the Sites index", async () => {
    renderSites(ENABLED);
    await screen.findByText(NO_SITES);

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
    await screen.findByText(NO_SITES);

    const main = screen.getByRole("main");

    expect(within(main).queryAllByRole("link")).toHaveLength(0);
    expect(
      container.querySelectorAll(
        "button:not([data-shared-range-button]):not([data-shell-control]), input, select, textarea, form",
      ),
    ).toHaveLength(0);
    expect(spacedText(main)).not.toMatch(/simulat/i);
    expect(spacedText(main)).not.toMatch(/create/i);
    expect(spacedText(main)).not.toMatch(/add a site/i);
  });

  it("still offers the create action once a site exists", async () => {
    renderSites(ENABLED, [SITE]);
    await findList();

    expect(
      screen.getByRole("link", { name: CREATE_SITE_ENTRY_POINT_LABEL }),
    ).toHaveAttribute("href", "/simulator-lab/create-site");
  });

  it("puts the create action in the page header, not in the listing", async () => {
    render(
      <MemoryRouter initialEntries={["/sites"]}>
        <App flags={ENABLED} siteDirectory={directoryWith([SITE])} portfolioSites={sitesE1()} estateIndex={estateE0({})} />
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
    expect(sitesList()!.contains(action)).toBe(false);
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
        <App flags={ENABLED} siteDirectory={directoryWith([SITE])} portfolioSites={sitesE1()} estateIndex={estateE0({})} />
      </MemoryRouter>,
    );
    await settledScreen();
    const enabledMarkup = markupWithout(
      within(enabled.container).getByRole("main").innerHTML,
    );
    enabled.unmount();

    const disabled = render(
      <MemoryRouter initialEntries={["/sites"]}>
        <App flags={DISABLED} siteDirectory={directoryWith([SITE])} portfolioSites={sitesE1()} estateIndex={estateE0({})} />
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
      await findList();

      const navigation = within(view.container).getByRole("navigation", {
        name: "Operator routes",
      });

      expect(
        within(navigation).getAllByRole("link").map((link) => link.textContent),
      ).toEqual(OPERATOR_NAVIGATION_LABELS);
      expect(spacedText(navigation)).not.toMatch(/simulat/i);
      expect(spacedText(navigation)).not.toMatch(/create/i);

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
          portfolioSites={sitesE1()}
          estateIndex={estateE0({})}
        />
      </MemoryRouter>,
    );
    await findList();

    // T011 puts the name and the identity in one cell, so the row link is
    // named for the site rather than for its ID. The address is unchanged and
    // is still built from `site_id`, which the substrate test pins.
    fireEvent.click(
      screen.getByRole("link", { name: SITE.display_name }),
    );

    // The row leads to the right site. W1-F2 (v69 Site page heading) titles the page with the display name and
    // carries the record's `site_id` in the provenance badge beside it; both are pinned here.
    expect(
      await screen.findByRole("heading", { level: 1, name: SITE.display_name }),
    ).toBeInTheDocument();
    expect(document.querySelector("header.page-header [data-site-provenance]")?.textContent).toContain("Example data");
  });

  it("adds exactly one destination and no navigation item", async () => {
    /**
     * T006 asserted that no per-site destination existed. It exists now, so
     * the assertion is replaced rather than dropped, and the replacement is
     * the stronger half: the index offers the site row link and the gated
     * create action and nothing else, and operator navigation gained
     * nothing from it: the only item added since is T028's Findings rail
     * root, which is not a per-site destination.
     */
    const view = render(
      <MemoryRouter initialEntries={["/sites"]}>
        <App
          flags={ENABLED}
          siteDirectory={directoryWith([SITE])}
          siteDetail={detailClientFor(SITE_DETAIL)}
          portfolioSites={sitesE1()}
          estateIndex={estateE0({})}
        />
      </MemoryRouter>,
    );
    await findList();

    const main = within(view.container).getByRole("main");

    // IA-P P4b (D-IAP.6): one target per row, the Site's name; the `View` action left with the directory table. The
    // claim is unchanged - one destination per site and the gated create action, nothing else. A list link carries
    // the range (spec §6 "Range pages"), so the destinations are compared by path.
    const hrefs = within(main)
      .getAllByRole("link")
      .map((link) => pathOf(link.getAttribute("href")));

    expect(hrefs).toEqual([
      "/simulator-lab/create-site",
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
      // T007 listed `/sites/MG-002/configuration` here too. T008 made that one
      // real and T011A renamed it to `/foundation`, so it moves out of this
      // list rather than the list being dropped: what is pinned is that a site
      // grows addressable aspects one reviewed slice at a time, and devices is
      // causal step 4's to make true.
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

  it("reaches a site's Foundation from that site, not from the index", async () => {
    render(
      <MemoryRouter initialEntries={["/sites"]}>
        <App
          flags={ENABLED}
          siteDirectory={directoryWith([SITE])}
          siteDetail={detailClientFor(SITE_DETAIL)}
          portfolioSites={sitesE1()}
          estateIndex={estateE0({})}
        />
      </MemoryRouter>,
    );
    await findList();

    // The index offers one destination per site, and that destination is the
    // site. A Foundation link on a row would be a second way in, addressed by
    // the same identity, which is how two ways into one thing start to
    // disagree about what it is.
    const main = screen.getByRole("main");
    const hrefs = within(main)
      .getAllByRole("link")
      .map((link) => pathOf(link.getAttribute("href")));

    expect(hrefs).toContain("/sites/MG-002");
    expect(hrefs).not.toContain("/sites/MG-002/foundation");
    expect(hrefs).not.toContain("/sites/MG-002/configuration");
  });
});

/**
 * W1-F1 pinned the v69 `sites` panels (Site inventory, then In setup). IA-P P4b replaces them with the Sites list (spec
 * §6 P4b; "In setup" is a known deviation in packet-IA-P3). What stays pinned: the page renders the one list whether the
 * directory is stocked, empty or unreadable, and a refused directory read leaves E1's rows alone (D-IAP.35 Q1).
 */
describe("IA-P P4b: the Sites route renders the one list in every directory state", () => {
  const unavailable: SiteDirectoryClient = { listSites: () => Promise.resolve({ status: "unavailable" as const }) };
  const kobo = (JSON.parse(SITES_OCT) as PortfolioSites).rows[0];
  const variants: [string, SiteDirectoryClient, string[]][] = [
    ["stocked", directoryWith([SITE]), [kobo.site, SITE.display_name]],
    ["empty", directoryWith([]), [kobo.site]],
    ["unreadable", unavailable, [kobo.site]],
  ];

  it.each(variants)("lists E1's rows, then the directory's (%s)", async (_name, directory, titles) => {
    render(
      <MemoryRouter initialEntries={["/sites"]}>
        <App flags={DISABLED} siteDirectory={directory} portfolioSites={sitesE1([kobo])} estateIndex={estateE0({})} />
      </MemoryRouter>,
    );
    const list = await findList();
    expect([...list.querySelectorAll("tbody th[scope=row]")].map((th) => th.querySelector("a,span")?.textContent)).toEqual(titles);
    expect(document.querySelectorAll("[data-home-list]")).toHaveLength(1);
    expect(document.querySelector("[data-headline-card]")).toBeNull();
  });
});

describe("IA-P P4b: the Sites list header and empty state", () => {
  it("is a list page: the title alone, no root crumb, and the list's empty sentence (spec §5.3)", async () => {
    renderSites(ENABLED);
    await screen.findByText(NO_SITES);
    // R127/R120 pinned a root "Sites" crumb on the directory page; §5.3 gives every list a PageHeader with the menu
    // label as its title, and the rail lights Sites, so the one-part crumb is gone.
    expect(screen.queryByRole("navigation", { name: "Breadcrumb" })).toBeNull();
    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("Sites");
    expect(screen.getByText(NO_SITES).getAttribute("role")).toBe("status");
  });
});
