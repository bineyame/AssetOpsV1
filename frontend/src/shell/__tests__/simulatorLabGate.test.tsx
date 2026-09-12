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
import { simulatorLabRoutes } from "../simulatorLabRoutes";

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

const OPERATOR_ROUTES = ["/", "/sites", "/site-details", "/site-configuration"];

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
      <App flags={flags} />
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

  it.each(SIMULATOR_URLS)(
    "does not serve a simulator surface at %s",
    (url) => {
      renderAt(url, DISABLED);

      expect(
        screen.getByRole("heading", { level: 1, name: "Page not available" }),
      ).toBeInTheDocument();
      expect(screen.queryByRole("heading", { name: /simulator/i })).toBeNull();
    },
  );

  it.each(SIMULATOR_URLS)(
    "renders no simulator content, reference, or hint at %s",
    (url) => {
      const { container } = renderAt(url, DISABLED);

      expect(container.textContent).not.toMatch(/simulat/i);
    },
  );

  it.each(SIMULATOR_URLS)(
    "offers no interactive control of any kind at %s",
    (url) => {
      const { container } = renderAt(url, DISABLED);

      expect(interactiveControls(container)).toHaveLength(0);
    },
  );

  it.each(OPERATOR_ROUTES)(
    "serves no URL that reaches a simulator surface from %s",
    (route) => {
      const { container } = renderAt(route, DISABLED);

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

  it.each(OPERATOR_ROUTES)("still renders the operator route %s", (route) => {
    renderAt(route, DISABLED);

    expect(screen.getByRole("main")).toBeInTheDocument();
    expect(
      screen.getByRole("navigation", { name: "Operator routes" }),
    ).toBeInTheDocument();
  });
});

describe("simulator lab gate: enabled", () => {
  it("registers the Simulator Lab route", () => {
    expect(simulatorLabRoutes(ENABLED).map((route) => route.path)).toEqual([
      "/simulator-lab",
    ]);
  });

  it.each(SIMULATOR_LAB_SHELL_URLS)("serves an empty Simulator Lab shell at %s", (url) => {
    renderAt(url, ENABLED);

    expect(
      screen.getByRole("heading", { level: 1, name: "Simulator Lab" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { level: 2, name: "Simulator Lab is empty" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/run execution is not implemented yet/i),
    ).toBeInTheDocument();
  });

  it("reaches the Simulator Lab through the gated operator entry point", () => {
    renderAt("/", ENABLED);

    const navigation = screen.getByRole("navigation", {
      name: "Operator routes",
    });
    const entryPoint = within(navigation).getByRole("link", {
      name: "Simulator Lab",
    });

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

  it.each(OPERATOR_ROUTES)("still renders the operator route %s", (route) => {
    renderAt(route, ENABLED);

    expect(screen.getByRole("main")).toBeInTheDocument();
  });
});

describe("simulator lab gate: runs are unavailable in both states", () => {
  it.each([...SIMULATOR_URLS, ...OPERATOR_ROUTES])(
    "exposes no run start, inspect, rerun, or truth comparison control at %s when disabled",
    (url) => {
      const { container } = renderAt(url, DISABLED);

      for (const control of interactiveControls(container)) {
        expect(controlDescription(control)).not.toMatch(RUN_ACTION_PATTERN);
      }
    },
  );

  it.each([...SIMULATOR_URLS, ...OPERATOR_ROUTES])(
    "exposes no run start, inspect, rerun, or truth comparison control at %s when enabled",
    (url) => {
      const { container } = renderAt(url, ENABLED);

      for (const control of interactiveControls(container)) {
        expect(controlDescription(control)).not.toMatch(RUN_ACTION_PATTERN);
      }
    },
  );

  it("gives the enabled Simulator Lab shell no control except a way back", () => {
    const { container } = renderAt("/simulator-lab", ENABLED);

    expect(
      container.querySelectorAll(
        "button, input, select, textarea, form, [role='button'], [contenteditable='true']",
      ),
    ).toHaveLength(0);

    const links = Array.from(container.querySelectorAll("a"));
    expect(links).toHaveLength(1);
    expect(links[0]).toHaveAttribute("href", "/");
    expect(links[0].textContent).toBe("Back to the operator shell");
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
