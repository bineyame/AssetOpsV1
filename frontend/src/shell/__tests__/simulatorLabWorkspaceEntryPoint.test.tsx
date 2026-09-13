import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { App } from "../../App";
import { featureFlagsWith, type FeatureFlags } from "../../config/featureFlags";
import type { SiteDirectoryClient } from "../../sites/siteDirectoryClient";
import {
  SIMULATOR_LAB_ENTRY_POINT_LABEL,
  SIMULATOR_LAB_PATH,
  simulatorLabWorkspaceEntryPoints,
} from "../simulatorLabRoutes";

/**
 * Shell-hierarchy tests for the Simulator Lab entry point.
 *
 * The failure mode guarded here is not reachability, which the gate tests in
 * `simulatorLabGate.test.tsx` already own. It is placement: Simulator Lab is a
 * separate developer workspace, so its entry point must sit in workspace-level
 * chrome and must never regress into an operator left-nav item, and operator
 * navigation must look identical whichever way the gate is set.
 */

const DISABLED = featureFlagsWith(false);
const ENABLED = featureFlagsWith(true);

const OPERATOR_ROUTES = ["/", "/sites", "/site-details", "/site-configuration"];

/** The operator route list, which the gate must never change. */
const OPERATOR_NAVIGATION_LABELS = [
  "Operator home",
  "Sites",
  "Site details",
  "Site configuration",
];

/** Injected and empty: placement assertions must not depend on a store. */
const EMPTY_SITE_DIRECTORY: SiteDirectoryClient = {
  listSites: () => Promise.resolve({ status: "loaded", sites: [] }),
};

function renderAt(path: string, flags: FeatureFlags) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App flags={flags} siteDirectory={EMPTY_SITE_DIRECTORY} />
    </MemoryRouter>,
  );
}

/**
 * Render, read the operator navigation labels, and unmount again, so both flag
 * states can be compared inside one test without two documents colliding.
 */
function operatorNavigationLabelsAt(
  path: string,
  flags: FeatureFlags,
): string[] {
  const { container, unmount } = renderAt(path, flags);

  const navigation = within(container).getByRole("navigation", {
    name: "Operator routes",
  });
  const labels = within(navigation)
    .getAllByRole("link")
    .map((link) => link.textContent ?? "");

  unmount();

  return labels;
}

describe("operator navigation does not change with the gate", () => {
  it.each(OPERATOR_ROUTES)(
    "lists the same operator entries in both flag states at %s",
    (route) => {
      const enabledLabels = operatorNavigationLabelsAt(route, ENABLED);

      expect(enabledLabels).toEqual(OPERATOR_NAVIGATION_LABELS);
      expect(enabledLabels).toEqual(
        operatorNavigationLabelsAt(route, DISABLED),
      );
    },
  );

  it.each(OPERATOR_ROUTES)(
    "keeps Simulator Lab out of operator navigation when enabled at %s",
    (route) => {
      renderAt(route, ENABLED);

      const navigation = screen.getByRole("navigation", {
        name: "Operator routes",
      });

      expect(
        within(navigation).queryByRole("link", { name: /simulator/i }),
      ).toBeNull();
      expect(navigation.textContent).not.toMatch(/simulat/i);
      for (const link of Array.from(navigation.querySelectorAll("a"))) {
        expect(link.getAttribute("href")).not.toMatch(/simulat/i);
      }
    },
  );
});

describe("workspace entry point: disabled", () => {
  it("offers no workspace entry point at all when the gate is closed", () => {
    expect(simulatorLabWorkspaceEntryPoints(DISABLED)).toEqual([]);
  });

  it.each(OPERATOR_ROUTES)(
    "renders no workspace chrome, entry point, or hint at %s",
    async (route) => {
      const { container } = renderAt(route, DISABLED);
      await screen.findByRole("main");

      expect(
        screen.queryByRole("navigation", { name: "Workspace utilities" }),
      ).toBeNull();
      expect(screen.getAllByRole("navigation")).toHaveLength(1);
      expect(
        screen.queryByRole("link", { name: SIMULATOR_LAB_ENTRY_POINT_LABEL }),
      ).toBeNull();
      expect(container.textContent).not.toMatch(/simulat/i);
      expect(container.textContent).not.toMatch(/workspace/i);
    },
  );
});

describe("workspace entry point: enabled", () => {
  it("declares one workspace entry point aimed at the gated path", () => {
    expect(simulatorLabWorkspaceEntryPoints(ENABLED)).toEqual([
      { to: SIMULATOR_LAB_PATH, label: SIMULATOR_LAB_ENTRY_POINT_LABEL },
    ]);
  });

  it.each(OPERATOR_ROUTES)(
    "places the entry point outside the operator navigation landmark at %s",
    (route) => {
      renderAt(route, ENABLED);

      const operatorNavigation = screen.getByRole("navigation", {
        name: "Operator routes",
      });
      const workspaceUtilities = screen.getByRole("navigation", {
        name: "Workspace utilities",
      });
      const entryPoint = screen.getByRole("link", {
        name: SIMULATOR_LAB_ENTRY_POINT_LABEL,
      });

      expect(workspaceUtilities).not.toBe(operatorNavigation);
      expect(workspaceUtilities.contains(entryPoint)).toBe(true);
      expect(operatorNavigation.contains(entryPoint)).toBe(false);
      expect(operatorNavigation.contains(workspaceUtilities)).toBe(false);
      expect(entryPoint.closest("nav")).toBe(workspaceUtilities);

      // Nor smuggled into the operator page content instead of its navigation.
      expect(screen.getByRole("main").contains(entryPoint)).toBe(false);

      expect(entryPoint).toHaveAttribute("href", SIMULATOR_LAB_PATH);
    },
  );

  it("opens the empty Simulator Lab shell outside the operator route layout", () => {
    const { container } = renderAt("/", ENABLED);

    fireEvent.click(
      screen.getByRole("link", { name: SIMULATOR_LAB_ENTRY_POINT_LABEL }),
    );

    expect(
      screen.getByRole("heading", { level: 1, name: "Simulator Lab" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { level: 2, name: "No simulator run exists" }),
    ).toBeInTheDocument();

    // The operator shell, its navigation, and the workspace chrome are gone:
    // this is a separate workspace, not an operator route inside the shell.
    expect(
      screen.queryByRole("navigation", { name: "Operator routes" }),
    ).toBeNull();
    expect(
      screen.queryByRole("navigation", { name: "Workspace utilities" }),
    ).toBeNull();
    expect(screen.queryAllByRole("navigation")).toHaveLength(0);
    expect(
      screen.queryByRole("link", { name: SIMULATOR_LAB_ENTRY_POINT_LABEL }),
    ).toBeNull();

    // Following the entry point must not hand the developer any run,
    // execution, truth, ingestion, analytics, Replay, or Findings surface.
    expect(
      container.querySelectorAll(
        "button, input, select, textarea, form, [role='button'], [contenteditable='true']",
      ),
    ).toHaveLength(0);

    // T005 gives the Lab its first destination. The allowlist is exact, so a
    // further destination or a different one still fails here.
    const links = Array.from(container.querySelectorAll("a")).map((link) => [
      link.getAttribute("href"),
      link.textContent,
    ]);
    expect(links).toEqual([
      ["/simulator-lab/site-templates", "Site Templates"],
      ["/", "Back to the operator shell"],
    ]);
  });

  it("presents the Simulator Lab shell as a developer workspace, not an operator page", () => {
    renderAt(SIMULATOR_LAB_PATH, ENABLED);

    const main = screen.getByRole("main");

    expect(within(main).getByText("Developer workspace")).toBeInTheDocument();
    expect(
      within(main).getByText(
        /separate from the operator product shell/i,
      ),
    ).toBeInTheDocument();
    expect(
      within(main).getByText(/not part of operator navigation/i),
    ).toBeInTheDocument();
    expect(
      within(main).getByText(/Simulator truth is never product evidence/i),
    ).toBeInTheDocument();
  });
});
