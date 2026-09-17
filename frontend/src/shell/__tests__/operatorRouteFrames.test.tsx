import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { App } from "../../App";
import { featureFlagsWith, type FeatureFlags } from "../../config/featureFlags";
import type { SiteDirectoryClient } from "../../sites/siteDirectoryClient";
import { settledScreen } from "../../test/settled";

/**
 * The operator route frames that name no site.
 *
 * `/site-configuration` left this list when T008 removed the parameterless
 * placeholder. Its identified replacement is addressed under a site and is
 * covered in `siteConfigurationRoute.test.tsx`, where the assertions can be
 * made against a record rather than against an empty build.
 */
const operatorRoutes = ["/", "/sites"];

/**
 * The Sites index now reads a store, so it is injected and empty here. These
 * are route-frame tests: what a configured site renders is covered by the
 * substrate tests, against records.
 */
const EMPTY_SITE_DIRECTORY: SiteDirectoryClient = {
  listSites: () => Promise.resolve({ status: "loaded", sites: [] }),
};

/**
 * Operator frames are served in both gate states, so these tests pass flags
 * explicitly rather than inheriting whatever `config/app-config.json` currently
 * says. Flipping the shipped flag must not change any assertion here.
 */
const simulatorLabDisabled = featureFlagsWith(false);
const simulatorLabEnabled = featureFlagsWith(true);

function renderAt(path: string, flags: FeatureFlags = simulatorLabDisabled) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App flags={flags} siteDirectory={EMPTY_SITE_DIRECTORY} />
    </MemoryRouter>,
  );
}

describe("operator route frames", () => {
  it("renders the Sites route frame", async () => {
    renderAt("/sites");
    await settledScreen();

    expect(
      screen.getByRole("heading", { level: 1, name: "Sites" }),
    ).toBeInTheDocument();
  });

  it("serves nothing at the parameterless Site Configuration address", () => {
    // The frame this replaced described no site, because no site identity
    // existed when it was written. A site has one now, so the placeholder is
    // gone rather than left standing beside its identified replacement.
    renderAt("/site-configuration");

    expect(
      screen.getByRole("heading", { level: 1, name: "Page not available" }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("heading", { level: 1, name: "Site configuration" }),
    ).toBeNull();
  });
});

describe("operator route frame empty states", () => {
  it("states that no sites are configured on the Sites frame", async () => {
    renderAt("/sites");

    expect(
      await screen.findByRole("heading", {
        level: 2,
        name: "No sites configured",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        /No site has been configured, so there is nothing to list/i,
      ),
    ).toBeInTheDocument();
    expect(screen.getByRole("main").textContent).toMatch(
      /no example site stands in for one/i,
    );
  });

  it("distinguishes an unreadable store from an empty one", async () => {
    render(
      <MemoryRouter initialEntries={["/sites"]}>
        <App
          flags={simulatorLabDisabled}
          siteDirectory={{
            listSites: () => Promise.resolve({ status: "unavailable" }),
          }}
        />
      </MemoryRouter>,
    );

    expect(
      await screen.findByRole("heading", { level: 2, name: "Sites unavailable" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("main").textContent).not.toMatch(
      /No sites configured/i,
    );
  });

  it("no longer says that no site configuration exists in this build", () => {
    // That was true of the empty T002 frame and is false now: a configured
    // site has a foundation and the product renders it. The copy goes with
    // the frame rather than being left somewhere it would contradict a screen.
    renderAt("/site-configuration");

    expect(
      screen.queryByText(/No site configuration exists in this build/i),
    ).toBeNull();
    expect(
      screen.queryByRole("heading", { name: /Site configuration unavailable/i }),
    ).toBeNull();
  });

  it.each(operatorRoutes)(
    "shows no fabricated values, charts, health, analytics, Replay, or Findings at %s",
    async (path) => {
      const { container } = renderAt(path);
      await screen.findByRole("main");

      expect(container.querySelectorAll("svg, canvas, img")).toHaveLength(0);
      expect(screen.queryAllByRole("figure")).toHaveLength(0);

      // The digit rule stands where nothing truthful renders a number: these
      // frames describe an empty build. Where a site renders values, the
      // stronger rule replaces this one and every digit on screen must trace
      // to the record under test - see `sitesIndex.test.tsx` for the index,
      // `siteDetail.test.tsx` for a site page, and
      // `siteConfiguration.test.tsx` for a foundation.
      expect(
        within(screen.getByRole("main")).queryAllByText(/\d/),
      ).toHaveLength(0);
    },
  );

  it("renders no table on an empty Sites index", async () => {
    const { container } = renderAt("/sites");
    await screen.findByRole("heading", { level: 2, name: "No sites configured" });

    expect(container.querySelectorAll("table")).toHaveLength(0);
  });

  it.each(operatorRoutes)(
    "does not hard-code a site identifier at %s",
    async (path) => {
      // These frames name no site, so neither may name one. Where a frame does
      // name a site the identity comes from the address and the record, which
      // `siteDetailRoute.test.tsx` and `siteConfigurationRoute.test.tsx` pin.
      const { container } = renderAt(path);
      await settledScreen();

      expect(container.textContent).not.toMatch(/MG-?\s*\d/i);
      expect(container.textContent).not.toMatch(/\bsite[-_\s]?id\b/i);
    },
  );
});

describe("operator route navigation", () => {
  it("navigates between operator route frames", () => {
    renderAt("/");

    const operatorNavigation = screen.getByRole("navigation", {
      name: "Operator routes",
    });

    fireEvent.click(within(operatorNavigation).getByRole("link", { name: "Sites" }));
    expect(
      screen.getByRole("heading", { level: 1, name: "Sites" }),
    ).toBeInTheDocument();

    // There is no third item to navigate to. Both parameterless site
    // destinations have been removed by the slices that gave them identified
    // replacements, and neither replacement is a navigation item, because a
    // navigation item cannot name which site it would open.
    expect(
      within(operatorNavigation)
        .getAllByRole("link")
        .map((link) => link.textContent),
    ).toEqual(["Operator home", "Sites"]);
  });

  it.each(operatorRoutes)(
    "exposes no Simulator Lab entry point at %s when the gate is closed",
    async (path) => {
      const { container } = renderAt(path, simulatorLabDisabled);
      await screen.findByRole("main");

      expect(container.textContent).not.toMatch(/simulator/i);
      for (const link of Array.from(container.querySelectorAll("a"))) {
        expect(link.getAttribute("href")).not.toMatch(/simulator/i);
      }
    },
  );

  it("keeps Simulator Lab outside the operator navigation layout", () => {
    renderAt("/simulator-lab", simulatorLabEnabled);

    expect(
      screen.getByRole("heading", { level: 1, name: "Simulator Lab" }),
    ).toBeInTheDocument();
    expect(screen.queryByRole("navigation")).toBeNull();
  });
});
