import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { App } from "../../App";
import { featureFlagsWith, type FeatureFlags } from "../../config/featureFlags";
import type { SiteDirectoryClient } from "../../sites/siteDirectoryClient";
import type { SiteSummary } from "../../sites/siteReadModel";
import { CREATE_SITE_ENTRY_POINT_LABEL } from "../simulatorLabRoutes";

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
  "Site details",
  "Site configuration",
];

function directoryWith(sites: SiteSummary[]): SiteDirectoryClient {
  return { listSites: () => Promise.resolve({ status: "loaded", sites }) };
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

describe("no per-site destination exists yet", () => {
  it.each(["/sites/MG-002", "/sites/MG-002/configuration", "/sites/mg-002"])(
    "serves nothing at %s",
    (path) => {
      render(
        <MemoryRouter initialEntries={[path]}>
          <App flags={ENABLED} siteDirectory={directoryWith([SITE])} />
        </MemoryRouter>,
      );

      expect(
        screen.getByRole("heading", { level: 1, name: "Page not available" }),
      ).toBeInTheDocument();
    },
  );

  it("leaves the parameterless Site Details and Site Configuration frames in place", () => {
    // T007 and T008 each remove the placeholder their own route replaces. No
    // slice leaves a parameterless site destination standing once its
    // identified route exists, and neither identified route exists yet.
    render(
      <MemoryRouter initialEntries={["/site-details"]}>
        <App flags={ENABLED} siteDirectory={directoryWith([SITE])} />
      </MemoryRouter>,
    );

    expect(
      screen.getByRole("heading", { level: 1, name: "Site details" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("main").textContent).not.toMatch(/MG-?\s*\d/i);
  });
});
