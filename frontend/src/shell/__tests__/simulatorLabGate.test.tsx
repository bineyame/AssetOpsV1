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
import type { RunSetupClient } from "../runSetupClient";
import type { SiteDirectoryClient } from "../../sites/siteDirectoryClient";
import { simulatorLabRoutes } from "../simulatorLabRoutes";
import { settledScreen } from "../../test/settled";
import { spacedText } from "../../test/text";

/**
 * The Sites index reads the Site store. It is injected here and empty, so a
 * gate assertion is about what the build serves rather than about what a store
 * happens to hold or how fast it answers.
 */
const EMPTY_SITE_DIRECTORY: SiteDirectoryClient = {
  listSites: () => Promise.resolve({ status: "loaded", sites: [] }),
};

/**
 * The run store, injected and holding one draft.
 *
 * Injected for a reason the gate assertions depend on. Without a client the
 * run surfaces render "the run store could not be read" - a screen with no
 * controls on it at all - and every claim below about what those screens may
 * and may not offer would be a claim about an empty set. The draft is `READY`
 * so the one disabled action exists, which is the case the allowance further
 * down is written for and the case that would hide an enabled one.
 */
const RUN_SETUP: RunSetupClient = {
  listProfiles: () => Promise.resolve({ status: "unavailable" }),
  createRun: () => Promise.resolve({ status: "unavailable", message: null }),
  listRuns: () =>
    Promise.resolve({
      status: "loaded",
      runs: [
        {
          run_id: "run-1",
          lifecycle_status: "DRAFT",
          execution_status: "READY",
          created_at: "2026-09-22T09:00:00Z",
          site_id: "MG-001",
          foundation_version: 1,
          scenario_id: "fuel-loss-event",
          scenario_version: 1,
          interval: {
            start_time: "2026-09-21T00:00:00Z",
            end_time: "2026-09-22T17:00:00Z",
            duration_minutes: 2460,
          },
          blocking_reason_count: 0,
        },
      ],
    }),
  getRun: (runId: string) =>
    Promise.resolve({
      status: "loaded",
      run: {
        run_id: runId,
        lifecycle_status: "DRAFT",
        execution_status: "READY",
        readiness_disclosure:
          "READY means every required executable input resolved and the " +
          "selected model profile declares it can consume them.",
        created_at: "2026-09-22T09:00:00Z",
        site_id: "MG-001",
        scenario_id: "fuel-loss-event",
        scenario_version: 1,
        frozen_inputs: [
          {
            identity_field: "site",
            field: "Site",
            value: "MG-001",
            answered_by: "SITE_FOUNDATION",
            answered_by_detail: "site MG-001 foundation version 1",
          },
        ],
        blocking_reasons: [],
        unsupported_optional_inputs: [],
      },
    }),
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
 * The Lab surfaces T020 added: the Runs inventory and one Draft.
 *
 * They were execution URLs until T020, because nothing served them. They are
 * reads - which runs exist, and what one froze - and they serve no execution
 * of any kind, which is why the list below keeps everything else.
 */
const RUN_SURFACE_URLS = ["/simulator-lab/runs", "/simulator-lab/runs/run-1"];

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

/**
 * The Lab surfaces T017 added. Scenarios are a developer-workspace capability,
 * so the catalog and one scenario's detail are gated and listed here. What
 * they show is product configuration in a product store; the gate covers the
 * surfaces, never the records.
 */
const SCENARIO_URLS = [
  "/simulator-lab/scenarios",
  "/simulator-lab/scenarios/fuel-loss-event",
];

/** Everything that must be unserved while the gate is closed. */
const UNSERVED_WHEN_DISABLED = [
  ...SIMULATOR_URLS,
  ...SITE_TEMPLATE_URLS,
  ...CREATE_SITE_URLS,
  ...SCENARIO_URLS,
];

/**
 * Execution URLs that no slice has implemented, in either flag state.
 *
 * T020 took the two run READ surfaces out of this set by serving them. What
 * remains is execution itself - truth comparison and the execute verb - plus
 * the ungated spellings, and none of those has ever been served.
 */
const EXECUTION_URLS = SIMULATOR_URLS.filter(
  (url) =>
    !SIMULATOR_LAB_SHELL_URLS.includes(url) &&
    !RUN_SURFACE_URLS.includes(url),
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
      <App
        flags={flags}
        siteDirectory={EMPTY_SITE_DIRECTORY}
        runSetup={RUN_SETUP}
      />
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

  it("registers no scenario route either", () => {
    const paths = simulatorLabRoutes(DISABLED).map((route) => route.path);

    expect(paths).not.toContain("/simulator-lab/scenarios");
    expect(paths).not.toContain("/simulator-lab/scenarios/:scenarioId");
  });

  it.each(OPERATOR_ROUTES)(
    "offers no way to create a site from the operator route %s",
    async (route) => {
      const { container } = renderAt(route, DISABLED);
      await screen.findByRole("main");

      expect(container.querySelectorAll("form, button, input, select")).toHaveLength(
        0,
      );
      expect(spacedText(container)).not.toMatch(/create/i);
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

      expect(spacedText(container)).not.toMatch(/simulat/i);
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
      expect(spacedText(container)).not.toMatch(/simulat/i);
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
  it("registers the Simulator Lab routes, including Site Templates, create and scenarios", () => {
    expect(simulatorLabRoutes(ENABLED).map((route) => route.path)).toEqual([
      "/simulator-lab",
      "/simulator-lab/site-templates",
      "/simulator-lab/site-templates/:templateId",
      "/simulator-lab/create-site",
      "/simulator-lab/scenarios",
      "/simulator-lab/scenarios/:scenarioId",
      "/simulator-lab/runs",
      "/simulator-lab/runs/:runId",
      "/simulator-lab/scenarios/:scenarioId/run-setup",
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
        const description = controlDescription(control);
        if (!RUN_ACTION_PATTERN.test(description)) {
          continue;
        }

        // T020 makes two truthful things match this pattern, so the ban
        // moves from "nothing may say it" to "nothing may DO it".
        //
        // A link may: a destination called Runs, and a row naming a run
        // identity, are navigation. Following one shows a record; it starts
        // nothing.
        //
        // A disabled button may, and only with a reason attached. That is
        // the third affordance state this project already uses - rendered,
        // disabled, carrying the prerequisite - and a disabled control
        // without a reason is a dead end, so it fails here too.
        //
        // Anything else still fails, and an ENABLED button saying any of
        // these words fails however it is spelled.
        const isNavigation = control.tagName === "A";
        const isDisabledWithReason =
          control.tagName === "BUTTON" &&
          (control as HTMLButtonElement).disabled &&
          control.getAttribute("aria-describedby") !== null;

        expect(
          isNavigation || isDisabledWithReason,
          `${url} offers "${description}" as something other than a ` +
            "destination or a disabled control with a reason",
        ).toBe(true);
      }
    },
  );

  it.each(RUN_SURFACE_URLS)(
    "offers no enabled control at all on the run surface %s when enabled",
    async (url) => {
      // The stronger half, stated separately so the allowance above cannot
      // be read as "the run screens may act". Nothing on them may.
      const { container } = renderAt(url, ENABLED);
      await settledScreen();

      for (const control of interactiveControls(container)) {
        if (control.tagName === "A") {
          continue;
        }
        expect(control).toBeDisabled();
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

    // Still an exact allowlist, and still closed: a third destination, or a
    // different one, fails. The first two entries are the Lab's own rail,
    // which T009 made a real component. Both name surfaces that already
    // rendered truthful content before the rail existed, so the rail surfaces
    // destinations rather than adding any: nothing here is a run, an
    // inspection, a rerun, a comparison, or a crossing into the product.
    expect(links).toEqual([
      ["/simulator-lab", "Simulator Lab"],
      ["/simulator-lab/site-templates", "Site Templates"],
      // T017 adds the rail's third destination. It is a place, not an action,
      // and it renders real scenario records; the Lab home body is unchanged,
      // so this adds a destination without adding a control.
      ["/simulator-lab/scenarios", "Scenarios"],
      // T020 adds the rail's fourth destination, and it is a place rather
      // than an action: it lists the Drafts run setup has written. The Lab
      // home body is unchanged, so this adds a destination without adding a
      // control.
      ["/simulator-lab/runs", "Runs"],
      ["/simulator-lab/site-templates", "Site Templates"],
      // T010 gives the Lab its own way into the create flow. The same path and
      // the same gate as the operator index's entry point, differing only in
      // its label, so this is still one flow behind one chokepoint and still
      // not a run, an inspection, a rerun, or a comparison.
      ["/simulator-lab/create-site", "+ Add site"],
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
