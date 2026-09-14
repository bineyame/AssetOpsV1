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

const OPERATOR_NAVIGATION_LABELS = [
  "Operator home",
  "Sites",
  "Site configuration",
];

const SITE_DETAIL: SiteDetailReadModel = {
  ...SITE,
  foundation: { version: 1, valid_from: "2026-09-14T09:12:00Z" },
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

    fireEvent.click(screen.getByRole("link", { name: "MG-002" }));

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

    expect(
      within(main)
        .getAllByRole("link")
        .map((link) => link.getAttribute("href")),
    ).toEqual(["/sites/MG-002", "/simulator-lab/create-site"]);

    const navigation = within(view.container).getByRole("navigation", {
      name: "Operator routes",
    });

    expect(
      within(navigation).getAllByRole("link").map((link) => link.textContent),
    ).toEqual(OPERATOR_NAVIGATION_LABELS);
  });

  it.each(["/sites/MG-002/configuration", "/sites/MG-002/devices"])(
    "still serves nothing under a site at %s",
    (path) => {
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
    // T007 removes the placeholder the identified route replaces. T008 removes
    // `/site-configuration` the same way; it is deliberately still here.
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

  it("still serves the parameterless Site Configuration frame", () => {
    render(
      <MemoryRouter initialEntries={["/site-configuration"]}>
        <App flags={ENABLED} siteDirectory={directoryWith([SITE])} />
      </MemoryRouter>,
    );

    expect(
      screen.getByRole("heading", { level: 1, name: "Site configuration" }),
    ).toBeInTheDocument();
  });
});
