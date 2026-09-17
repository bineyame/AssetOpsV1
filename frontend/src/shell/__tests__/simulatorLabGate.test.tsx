import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import appConfig from "../../../../config/app-config.json";
import { App } from "../../App";
import {
  featureFlags,
  featureFlagsWith,
  type FeatureFlags,
} from "../../config/featureFlags";
import type { SiteDirectoryClient } from "../../sites/siteDirectoryClient";
import { simulatorLabRoutes } from "../simulatorLabRoutes";
import { settledScreen } from "../../test/settled";

/**
 * The Sites index reads the Site store. It is injected here and empty, so a
 * gate assertion is about what the build serves rather than about what a store
 * happens to hold or how fast it answers.
 */
const EMPTY_SITE_DIRECTORY: SiteDirectoryClient = {
  listSites: () => Promise.resolve({ status: "loaded", sites: [] }),
};

/**
 * Serving-boundary tests for `simulator_lab.enabled`.
 *
 * These tests request routes in both flag states rather than counting rendered
 * links. Hiding navigation is not the gate: the failure mode being guarded is a
 * simulator surface that stays reachable by direct URL after the feature is
 * "disabled".
 */

const DISABLED = featureFlagsWith(false);
const ENABLED = featureFlagsWith(true);

/**
 * Operator routes with no site in them.
 *
 * The identified site routes are covered in `siteDetailRoute.test.tsx` and
 * `siteConfigurationRoute.test.tsx`, each over a record and in both gate
 * states, because a real site legitimately renders the word `Simulated` as
 * source-mode provenance and the blanket text assertions here would read that
 * as a simulator reference.
 *
 * `/site-configuration` left this list when T008 removed it. It was a
 * parameterless placeholder, and what replaced it is addressed under a site,
 * so it belongs with the other identified routes rather than here.
 */
const OPERATOR_ROUTES = ["/", "/sites"];

/**
 * URLs a bookmark, a script, or a curious operator could aim at the simulator.
 * None may serve a simulator surface while the gate is closed.
 */
const SIMULATOR_URLS = [
  "/simulator-lab",
  "/simulator-lab/",
  "/simulator-lab/runs",
  "/simulator-lab/runs/run-1",
  "/simulator-lab/runs/run-1/truth",
  "/simulator-lab/execute",
  "/simulator",
  "/simulator/runs",
];

/**
 * The gated shell itself. The trailing-slash form is the same route: the router
 * normalises it, so both spellings serve the shell when the gate is open.
 */
const SIMULATOR_LAB_SHELL_URLS = ["/simulator-lab", "/simulator-lab/"];

/**
 * Lab surfaces T005 added. They are served when the gate is open, so they are
 * listed separately from the execution URLs rather than folded into
 * SIMULATOR_URLS, and the disabled assertions below are extended to cover them.
 */
const SITE_TEMPLATE_URLS = [
  "/simulator-lab/site-templates",
  "/simulator-lab/site-templates/hybrid-mini-grid-100kw",
];

/**
 * The Lab surface T006 added. Creating a site is a Lab capability, so its
 * route is gated and listed here; the site it produces is a product object in
 * the product store and is not gated at all, which the Sites index assertions
 * below cover separately.
 */
const CREATE_SITE_URLS = ["/simulator-lab/create-site"];

/** Everything that must be unserved while the gate is closed. */
const UNSERVED_WHEN_DISABLED = [
  ...SIMULATOR_URLS,
  ...SITE_TEMPLATE_URLS,
  ...CREATE_SITE_URLS,
];

/** Execution URLs that no slice has implemented, in either flag state. */
const EXECUTION_URLS = SIMULATOR_URLS.filter(
  (url) => !SIMULATOR_LAB_SHELL_URLS.includes(url),
);

/**
 * Every interactive affordance, not only buttons and links: a gate that only
 * removes buttons still leaves forms, custom controls, and editable regions.
 */
const INTERACTIVE_SELECTOR = [
  "a[href]",
  "button",
  "input",
  "select",
  "textarea",
  "form",
  "details",
  "summary",
  "[onclick]",
  "[role='button']",
  "[role='link']",
  "[role='menuitem']",
  "[role='tab']",
  "[contenteditable='true']",
].join(", ");

/** Vocabulary for run execution, inspection, rerun and truth comparison. */
const RUN_ACTION_PATTERN =
  /\b(run|runs|rerun|re-run|start|stop|execute|execution|simulate|simulation|playback|replay|compare|comparison|truth|inspect|commit|publish|stage|staging|ingest)\b/i;

function renderAt(path: string, flags: FeatureFlags) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App flags={flags} siteDirectory={EMPTY_SITE_DIRECTORY} />
    </MemoryRouter>,
  );
}

function interactiveControls(container: HTMLElement): HTMLElement[] {
  return Array.from(container.querySelectorAll<HTMLElement>(INTERACTIVE_SELECTOR));
}

function controlDescription(control: HTMLElement): string {
  return [
    control.textContent ?? "",
    control.getAttribute("aria-label") ?? "",
    control.getAttribute("href") ?? "",
    control.getAttribute("value") ?? "",
    control.getAttribute("name") ?? "",
    control.getAttribute("formaction") ?? "",
  ].join(" ");
}

describe("simulator lab gate: configuration", () => {
  it("takes the shipped flag from the shared configuration file, not a hardcoded default", () => {
    expect(featureFlags.simulatorLab.enabled).toBe(
      appConfig.simulator_lab.enabled,
    );
    expect(typeof appConfig.simulator_lab.enabled).toBe("boolean");
  });
});

describe("simulator lab gate: disabled", () => {
  it("registers no Simulator Lab route at all", () => {
    expect(simulatorLabRoutes(DISABLED)).toEqual([]);
  });

  it("registers no Site Templates route either", () => {
    expect(
      simulatorLabRoutes(DISABLED).map((route) => route.path),
    ).not.toContain("/simulator-lab/site-templates");
  });

  it("registers no create-a-site route either", () => {
    expect(
      simulatorLabRoutes(DISABLED).map((route) => route.path),
    ).not.toContain("/simulator-lab/create-site");
  });

  it.each(OPERATOR_ROUTES)(
    "offers no way to create a site from the operator route %s",
    async (route) => {
      const { container } = renderAt(route, DISABLED);
      await screen.findByRole("main");

      expect(container.querySelectorAll("form, button, input, select")).toHaveLength(
        0,
      );
      expect(container.textContent).not.toMatch(/create/i);
    },
  );

  it("still serves the Sites index when the gate is closed", async () => {
    renderAt("/sites", DISABLED);

    expect(
      await screen.findByRole("heading", { level: 2, name: "No sites configured" }),
    ).toBeInTheDocument();
  });

  it.each(UNSERVED_WHEN_DISABLED)(
    "does not serve a simulator surface at %s",
    (url) => {
      renderAt(url, DISABLED);

      expect(
        screen.getByRole("heading", { level: 1, name: "Page not available" }),
      ).toBeInTheDocument();
      expect(screen.queryByRole("heading", { name: /simulator/i })).toBeNull();
    },
  );

  it.each(UNSERVED_WHEN_DISABLED)(
    "renders no simulator content, reference, or hint at %s",
    (url) => {
      const { container } = renderAt(url, DISABLED);

      expect(container.textContent).not.toMatch(/simulat/i);
    },
  );

  it.each(UNSERVED_WHEN_DISABLED)(
    "offers no interactive control of any kind at %s",
    (url) => {
      const { container } = renderAt(url, DISABLED);

      expect(interactiveControls(container)).toHaveLength(0);
    },
  );

  it.each(OPERATOR_ROUTES)(
    "serves no URL that reaches a simulator surface from %s",
    async (route) => {
      const { container } = renderAt(route, DISABLED);
      await settledScreen();

      const hrefs = Array.from(container.querySelectorAll("a")).map((anchor) =>
        anchor.getAttribute("href"),
      );

      expect(hrefs.length).toBeGreaterThan(0);
      for (const href of hrefs) {
        expect(href).not.toMatch(/simulat/i);
      }
      expect(container.textContent).not.toMatch(/simulat/i);
    },
  );

  it("exposes no Simulator Lab entry point in operator navigation", () => {
    renderAt("/", DISABLED);

    const navigation = screen.getByRole("navigation", {
      name: "Operator routes",
    });

    expect(
      within(navigation).queryByRole("link", { name: /simulator/i }),
    ).toBeNull();
  });

  it.each(OPERATOR_ROUTES)("still renders the operator route %s", async (route) => {
    renderAt(route, DISABLED);
    await settledScreen();

    expect(screen.getByRole("main")).toBeInTheDocument();
    expect(
      screen.getByRole("navigation", { name: "Operator routes" }),
    ).toBeInTheDocument();
  });
});

describe("simulator lab gate: enabled", () => {
  it("registers the Simulator Lab routes, including Site Templates and create", () => {
    expect(simulatorLabRoutes(ENABLED).map((route) => route.path)).toEqual([
      "/simulator-lab",
      "/simulator-lab/site-templates",
      "/simulator-lab/site-templates/:templateId",
      "/simulator-lab/create-site",
    ]);
  });

  it("serves the same Sites index it serves with the gate closed", async () => {
    renderAt("/sites", ENABLED);

    expect(
      await screen.findByRole("heading", { level: 2, name: "No sites configured" }),
    ).toBeInTheDocument();
  });

  it.each(SIMULATOR_LAB_SHELL_URLS)("serves an empty Simulator Lab shell at %s", (url) => {
    renderAt(url, ENABLED);

    expect(
      screen.getByRole("heading", { level: 1, name: "Simulator Lab" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { level: 2, name: "No simulator run exists" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/run execution is not implemented yet/i),
    ).toBeInTheDocument();
  });

  /**
   * T004 moved the enabled entry point out of operator navigation: Simulator
   * Lab is a separate developer workspace, not an operator route. The
   * reachability half of this T003 test is unchanged; the assertion that the
   * entry point is absent from operator navigation is new, so this is stricter
   * than the version it replaces, not looser.
   */
  it("reaches the Simulator Lab through a gated entry point outside operator navigation", () => {
    renderAt("/", ENABLED);

    const navigation = screen.getByRole("navigation", {
      name: "Operator routes",
    });

    expect(
      within(navigation).queryByRole("link", { name: /simulator/i }),
    ).toBeNull();

    const entryPoint = screen.getByRole("link", { name: /simulator lab/i });

    expect(navigation.contains(entryPoint)).toBe(false);
    expect(entryPoint).toHaveAttribute("href", "/simulator-lab");

    fireEvent.click(entryPoint);

    expect(
      screen.getByRole("heading", { level: 1, name: "Simulator Lab" }),
    ).toBeInTheDocument();
  });

  it.each(EXECUTION_URLS)(
    "still does not serve the execution URL %s",
    (url) => {
      renderAt(url, ENABLED);

      expect(
        screen.getByRole("heading", { level: 1, name: "Page not available" }),
      ).toBeInTheDocument();
    },
  );

  it.each(OPERATOR_ROUTES)("still renders the operator route %s", async (route) => {
    renderAt(route, ENABLED);
    await settledScreen();

    expect(screen.getByRole("main")).toBeInTheDocument();
  });
});

describe("simulator lab gate: runs are unavailable in both states", () => {
  it.each([...UNSERVED_WHEN_DISABLED, ...OPERATOR_ROUTES])(
    "exposes no run start, inspect, rerun, or truth comparison control at %s when disabled",
    async (url) => {
      const { container } = renderAt(url, DISABLED);
      await settledScreen();

      for (const control of interactiveControls(container)) {
        expect(controlDescription(control)).not.toMatch(RUN_ACTION_PATTERN);
      }
    },
  );

  it.each([...SIMULATOR_URLS, ...OPERATOR_ROUTES])(
    "exposes no run start, inspect, rerun, or truth comparison control at %s when enabled",
    async (url) => {
      const { container } = renderAt(url, ENABLED);
      await settledScreen();

      for (const control of interactiveControls(container)) {
        expect(controlDescription(control)).not.toMatch(RUN_ACTION_PATTERN);
      }
    },
  );

  /**
   * T005 gives the Lab its first destination, so the shell has two links
   * rather than one. The assertion is an exact allowlist of href and text
   * rather than a count: a third link, or a different destination, still
   * fails, and no control of any other kind is permitted at all.
   */
  it("gives the enabled Simulator Lab shell no control except its one destination and a way back", () => {
    const { container } = renderAt("/simulator-lab", ENABLED);

    expect(
      container.querySelectorAll(
        "button, input, select, textarea, form, [role='button'], [contenteditable='true']",
      ),
    ).toHaveLength(0);

    const links = Array.from(container.querySelectorAll("a")).map((link) => [
      link.getAttribute("href"),
      link.textContent,
    ]);

    expect(links).toEqual([
      ["/simulator-lab/site-templates", "Site Templates"],
      ["/", "Back to the operator shell"],
    ]);
  });

  it("renders no simulator truth, findings, health, or analytics output when enabled", () => {
    const { container } = renderAt("/simulator-lab", ENABLED);
    const main = screen.getByRole("main");

    expect(container.querySelectorAll("table, svg, canvas, img")).toHaveLength(
      0,
    );
    expect(within(main).queryAllByRole("figure")).toHaveLength(0);
    expect(within(main).queryAllByText(/\d/)).toHaveLength(0);
  });
});
