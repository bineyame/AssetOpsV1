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
import { settledScreen } from "../../test/settled";

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

/**
 * Operator routes with no site in them. `/site-configuration` left this list
 * when T008 removed the parameterless placeholder; its identified replacement
 * is addressed under a site and is covered in `siteConfigurationRoute.test.tsx`
 * in both gate states.
 */
const OPERATOR_ROUTES = ["/", "/sites"];

/**
 * The operator route list, which the gate must never change.
 *
 * T007 removed `Site details` and T008 removed `Site configuration`: both were
 * parameterless placeholders from before site identity existed, and a site
 * page and its configuration are now reached from a Sites row and from the
 * site. The gate assertion is unchanged in strength - the list is still pinned
 * exactly, and it is still the same list in both flag states.
 */
const OPERATOR_NAVIGATION_LABELS = ["Operator home", "Sites"];

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
    async (route) => {
      renderAt(route, ENABLED);
      await settledScreen();

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
    async (route) => {
      renderAt(route, ENABLED);
      await settledScreen();

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

    // This counted zero navigation landmarks, which held only because the Lab
    // had no rail of its own until T009 gave it one. The claim is that neither
    // operator navigation nor workspace chrome follows a developer in here, so
    // it now names the one rail that may be present rather than counting to
    // zero: a stray operator or workspace landmark still fails, and so does a
    // second rail.
    const navigation = screen.getAllByRole("navigation");
    expect(navigation).toHaveLength(1);
    expect(navigation[0]).toHaveAccessibleName("Simulator Lab routes");
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
    // further destination or a different one still fails here. The first two
    // entries are the Lab's own rail from T009; both name surfaces that
    // already rendered truthful content before the rail existed, so the rail
    // surfaces destinations rather than adding any.
    const links = Array.from(container.querySelectorAll("a")).map((link) => [
      link.getAttribute("href"),
      link.textContent,
    ]);
    expect(links).toEqual([
      ["/simulator-lab", "Simulator Lab"],
      ["/simulator-lab/site-templates", "Site Templates"],
      ["/simulator-lab/site-templates", "Site Templates"],
      // T010 gives the Lab its own entry into the create flow, on the same
      // path and behind the same gate as the operator index's.
      ["/simulator-lab/create-site", "+ Add site"],
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
