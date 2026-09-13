import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { App } from "../../App";
import { featureFlagsWith, type FeatureFlags } from "../../config/featureFlags";
import type { SiteDirectoryClient } from "../../sites/siteDirectoryClient";

const operatorRoutes = ["/", "/sites", "/site-configuration"];

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
  it("renders the Sites route frame", () => {
    renderAt("/sites");

    expect(
      screen.getByRole("heading", { level: 1, name: "Sites" }),
    ).toBeInTheDocument();
  });

  it("renders the Site Configuration route frame", () => {
    renderAt("/site-configuration");

    expect(
      screen.getByRole("heading", { level: 1, name: "Site configuration" }),
    ).toBeInTheDocument();
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

  it("states that site configuration is unavailable", () => {
    renderAt("/site-configuration");

    expect(
      screen.getByRole("heading", {
        level: 2,
        name: "Site configuration unavailable",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/No site configuration exists in this build/i),
    ).toBeInTheDocument();
  });

  it.each(operatorRoutes)(
    "shows no fabricated values, charts, health, analytics, Replay, or Findings at %s",
    async (path) => {
      const { container } = renderAt(path);
      await screen.findByRole("main");

      expect(container.querySelectorAll("svg, canvas, img")).toHaveLength(0);
      expect(screen.queryAllByRole("figure")).toHaveLength(0);

      // The digit rule stands where nothing truthful renders a number: these
      // three frames describe an empty build. Where a site renders values, the
      // stronger rule replaces this one and every digit on screen must trace
      // to the record under test - see `sitesIndex.test.tsx` for the index and
      // `siteDetail.test.tsx` for a site page.
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

  it.each(["/site-configuration"])(
    "does not hard-code a site identifier at %s",
    (path) => {
      const { container } = renderAt(path);

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

    fireEvent.click(
      within(operatorNavigation).getByRole("link", {
        name: "Site configuration",
      }),
    );
    expect(
      screen.getByRole("heading", { level: 1, name: "Site configuration" }),
    ).toBeInTheDocument();
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
