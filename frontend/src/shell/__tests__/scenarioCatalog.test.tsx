import { render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { App } from "../../App";
import { featureFlagsWith, type FeatureFlags } from "../../config/featureFlags";
import type { SiteDirectoryClient } from "../../sites/siteDirectoryClient";
import { settledScreen } from "../../test/settled";
import { spacedText, textNodes } from "../../test/text";
import { REVIEW_PROPOSAL_STATUS } from "../../ui";
import {
  EVENT_CATEGORY_LEGEND,
  EXECUTION_ROLE_LEGEND,
  TIMELINE_ENTRY_KIND_LEGEND,
} from "../ScenarioFrame";
import type {
  ScenarioCatalogClient,
  ScenarioDetail,
  ScenarioDetailResult,
  ScenarioListResult,
  ScenarioTargetResolution,
} from "../scenarioCatalogClient";
import {
  NOT_APPLICABLE_TARGET,
  OBSERVATION_SOURCE_RESOLUTIONS,
  PRIVATE_EXPECTATIONS,
  RESOLVED_TARGET,
  SCENARIO_DETAIL,
  SCENARIO_SUMMARY,
  SCENARIO_DETAIL_FALLBACKS,
  UNAVAILABLE_TARGET,
  UNCONFIGURED_TARGET,
  recordRenderedStrings,
} from "./scenarioFixtures";

/**
 * UI tests for the gated scenario catalog and the Fuel Loss Event detail
 * screen, including T018's execution contract and its review regions.
 *
 * Every assertion is about what the screen renders from a record. The catalog
 * client is injected, so nothing here depends on a store, a network, or a
 * fixture file on disk.
 */

const ENABLED = featureFlagsWith(true);
const DISABLED = featureFlagsWith(false);

const SCENARIOS_URL = "/simulator-lab/scenarios";
const SCENARIO_URL = "/simulator-lab/scenarios/fuel-loss-event";

const EMPTY_SITE_DIRECTORY: SiteDirectoryClient = {
  listSites: () => Promise.resolve({ status: "loaded", sites: [] }),
};

function catalogOf(
  detail: ScenarioDetailResult,
  list: ScenarioListResult = { status: "loaded", scenarios: [SCENARIO_SUMMARY] },
): ScenarioCatalogClient {
  return {
    listScenarios: () => Promise.resolve(list),
    getScenario: () => Promise.resolve(detail),
  };
}

function loadedDetail(
  targetResolution: ScenarioTargetResolution = RESOLVED_TARGET,
  scenario: ScenarioDetail = SCENARIO_DETAIL,
  privateExpectations = PRIVATE_EXPECTATIONS,
  observationSourceResolutions = OBSERVATION_SOURCE_RESOLUTIONS,
): ScenarioDetailResult {
  return {
    status: "loaded",
    scenario,
    targetResolution,
    observationSourceResolutions,
    privateExpectations,
  };
}

/**
 * A panel, by the heading that names it.
 *
 * `getByRole("region", { name })` is ambiguous on these screens: a `Panel` is a
 * labelled section and the `DataTable` inside it is a labelled scroll region,
 * so the same accessible name resolves to two elements. Naming which one a
 * test means is better than taking the first: the two are different scopes and
 * an assertion about the wrong one would be about the wrong thing.
 */
function panelNamed(name: string): HTMLElement {
  const panel = screen
    .getAllByRole("region", { name })
    .find((element) => element.classList.contains("panel"));
  if (panel === undefined) {
    throw new Error(`no panel named ${name}`);
  }
  return panel;
}

function tableNamed(name: string): HTMLElement {
  return screen.getByRole("table", { name });
}

function regionNamed(container: HTMLElement, id: string): HTMLElement {
  const region = container.querySelector(`[data-review-proposal='${id}']`);
  if (region === null) {
    throw new Error(`no review proposal region ${id}`);
  }
  return region as HTMLElement;
}

function renderAt(
  path: string,
  flags: FeatureFlags = ENABLED,
  catalog: ScenarioCatalogClient = catalogOf(loadedDetail()),
) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App
        flags={flags}
        siteDirectory={EMPTY_SITE_DIRECTORY}
        scenarioCatalog={catalog}
      />
    </MemoryRouter>,
  );
}

describe("the scenario catalog is gated", () => {
  it.each([SCENARIOS_URL, SCENARIO_URL])(
    "serves no scenario surface at %s when the gate is closed",
    async (url) => {
      const { container } = renderAt(url, DISABLED);
      await settledScreen();

      expect(
        screen.getByRole("heading", { level: 1, name: "Page not available" }),
      ).toBeInTheDocument();
      expect(spacedText(container)).not.toMatch(/\bscenario/i);
    },
  );

  it("renders the catalog when the gate is open", async () => {
    renderAt(SCENARIOS_URL);
    await settledScreen();

    expect(
      screen.getByRole("heading", { level: 1, name: "Scenarios" }),
    ).toBeInTheDocument();
  });
});

describe("the scenario catalog renders records", () => {
  it("lists the saved scenario with its identity, version and declared target", async () => {
    renderAt(SCENARIOS_URL);
    await settledScreen();

    const row = within(tableNamed("Saved scenarios")).getByRole("row", {
      name: /Fuel Loss Event/,
    });

    expect(
      within(row).getByRole("link", { name: "Fuel Loss Event" }),
    ).toHaveAttribute("href", SCENARIO_URL);
    expect(within(row).getByText("fuel-loss-event")).toBeInTheDocument();
    expect(within(row).getByText("SHIPPED")).toBeInTheDocument();
    expect(within(row).getByText("MG-001")).toBeInTheDocument();
  });

  it("states an unreadable store rather than an empty catalog", async () => {
    renderAt(
      SCENARIOS_URL,
      ENABLED,
      catalogOf(loadedDetail(), { status: "unavailable" }),
    );
    await settledScreen();

    expect(
      screen.getByText(/scenario store could not be read/i),
    ).toBeInTheDocument();
    expect(screen.queryByText("No scenario is saved.")).toBeNull();
  });

  it("states an empty catalog as a real answer", async () => {
    renderAt(
      SCENARIOS_URL,
      ENABLED,
      catalogOf(loadedDetail(), { status: "loaded", scenarios: [] }),
    );
    await settledScreen();

    expect(screen.getByText("No scenario is saved.")).toBeInTheDocument();
  });

  it("offers no control that would create, edit, run, or remove a scenario", async () => {
    const { container } = renderAt(SCENARIOS_URL);
    await settledScreen();

    expect(
      container.querySelectorAll(
        "button, input, select, textarea, form, [role='button'], [contenteditable='true']",
      ),
    ).toHaveLength(0);
  });
});

describe("the scenario detail screen renders the record", () => {
  it("renders version identity from the record", async () => {
    renderAt(SCENARIO_URL);
    await settledScreen();

    const panel = panelNamed("Scenario identity and version");

    expect(within(panel).getByText("fuel-loss-event")).toBeInTheDocument();
    expect(within(panel).getByText("3")).toBeInTheDocument();
    expect(
      within(panel).getByText("2026-09-20T00:00:00Z"),
    ).toBeInTheDocument();
    expect(within(panel).getByText("2")).toBeInTheDocument();
  });

  it("renders the timeline in authored order with its backed columns", async () => {
    renderAt(SCENARIO_URL);
    await settledScreen();

    const rows = within(tableNamed("Event and intervention timeline"))
      .getAllByRole("row")
      .slice(1);

    expect(rows).toHaveLength(SCENARIO_DETAIL.timeline.length);

    rows.forEach((row, index) => {
      const entry = SCENARIO_DETAIL.timeline[index];
      const cells = within(row)
        .getAllByRole("cell")
        .map((cell) => cell.textContent ?? "");

      expect(cells[0]).toBe(String(entry.sequence));
      expect(cells[1]).toBe(String(entry.offset_minutes));
      expect(cells[2]).toContain(entry.timing.shape);
      expect(cells[3]).toBe(entry.entry_kind);
      expect(cells[4]).toBe(entry.category);
      expect(cells[5]).toContain(entry.execution_role);
      expect(cells[6]).toContain(entry.description);
      expect(cells[6]).toContain(entry.event_id);
    });
  });

  it("renders a numeric parameter with its unit and a text parameter without one", async () => {
    renderAt(SCENARIO_URL);
    await settledScreen();

    const region = tableNamed("Scenario-level authoring parameters");

    // Twice, and both are correct: the authored quantity and the same
    // quantity in canonical terms, which happen to read the same for litres.
    expect(within(region).getAllByText("500 L")).toHaveLength(2);
    expect(
      within(region).getByText(
        "fuel-level, from the fuel level sensor on the fuel tank",
      ),
    ).toBeInTheDocument();
  });

  it("separates the private expectations into their own region", async () => {
    const { container } = renderAt(SCENARIO_URL);
    await settledScreen();

    const region = container.querySelector(
      "[data-private-region='expectations']",
    );
    expect(region).not.toBeNull();

    const text = spacedText(region as HTMLElement);
    expect(text).toMatch(/developer metadata, not product content/i);
    expect(text).toContain(PRIVATE_EXPECTATIONS[0].statement);

    // And the statement is nowhere else on the screen: the boundary is a
    // region, not a styling choice applied to content that also appears above.
    const outside = container.cloneNode(true) as HTMLElement;
    outside
      .querySelectorAll("[data-private-region='expectations']")
      .forEach((node) => node.remove());
    expect(spacedText(outside)).not.toContain(
      PRIVATE_EXPECTATIONS[0].statement,
    );
  });

  it("says a scenario and a foundation answer different questions", async () => {
    renderAt(SCENARIO_URL);
    await settledScreen();

    expect(
      spacedText(screen.getByRole("main")),
    ).toMatch(
      /A scenario definition answers what happens during the simulated interval\. A site's Foundation answers what the site is\./,
    );
  });

  it("states that the scenario is not saved rather than rendering an empty one", async () => {
    renderAt(SCENARIO_URL, ENABLED, catalogOf({ status: "not_found" }));
    await settledScreen();

    expect(
      screen.getByRole("heading", { level: 2, name: "No such saved scenario" }),
    ).toBeInTheDocument();
  });

  it("states an unreadable store rather than a half-rendered scenario", async () => {
    renderAt(SCENARIO_URL, ENABLED, catalogOf({ status: "unavailable" }));
    await settledScreen();

    expect(
      screen.getByRole("heading", { level: 2, name: "Scenario unavailable" }),
    ).toBeInTheDocument();
    expect(screen.queryByRole("table")).toBeNull();
  });
});

describe("the detail screen shows how each authored value executes", () => {
  it("gives every parameter and every timeline row an execution role", async () => {
    renderAt(SCENARIO_URL);
    await settledScreen();

    const parameters = within(
      tableNamed("Scenario-level authoring parameters"),
    )
      .getAllByRole("row")
      .slice(1);

    parameters.forEach((row, index) => {
      const parameter = SCENARIO_DETAIL.public_parameters[index];
      expect(
        within(row).getByText(parameter.execution_role),
      ).toBeInTheDocument();
    });

    const legend = spacedText(panelNamed("How each authored value executes"));
    for (const [value] of EXECUTION_ROLE_LEGEND) {
      expect(legend).toContain(value);
    }
  });

  it("proposes a role legend that covers every role the record uses", async () => {
    renderAt(SCENARIO_URL);
    await settledScreen();

    const used = new Set<string>();
    for (const parameter of SCENARIO_DETAIL.public_parameters) {
      used.add(parameter.execution_role);
    }
    for (const entry of SCENARIO_DETAIL.timeline) {
      used.add(entry.execution_role);
      for (const parameter of entry.parameters) {
        used.add(parameter.execution_role);
      }
    }

    // Non-vacuous by construction: the fixture uses the whole role
    // vocabulary, so a legend covering only part of it fails here.
    expect(used.size).toBe(EXECUTION_ROLE_LEGEND.length);

    const legend = spacedText(panelNamed("How each authored value executes"));
    for (const value of used) {
      expect(legend).toContain(value);
    }
  });

  it("says a reported value owns nothing rather than leaving the cell blank", async () => {
    renderAt(SCENARIO_URL);
    await settledScreen();

    const timeline = panelNamed("Event and intervention timeline");
    const reading = within(timeline).getByRole("row", {
      name: /fuel-level-after-the-gap/,
    });

    // The reading names the source it arrived through, and names no state it
    // changes: the row that used to be able to mean both.
    expect(
      within(reading).getByText(
        /reported through fuel-level-sensor-reading/,
      ),
    ).toBeInTheDocument();

    const parameters = panelNamed("Scenario-level authoring parameters");
    expect(
      within(parameters).getByText("Not consumed, so it owns nothing"),
    ).toBeInTheDocument();
  });

  it("names one owner for each initial world value", async () => {
    renderAt(SCENARIO_URL);
    await settledScreen();

    const rows = within(tableNamed("Initial world values and who owns them"))
      .getAllByRole("row")
      .slice(1);

    const inputs = SCENARIO_DETAIL.execution_contract.initialization_inputs;
    expect(rows).toHaveLength(inputs.length);
    expect(inputs.length).toBeGreaterThan(1);

    rows.forEach((row, index) => {
      const input = inputs[index];
      expect(within(row).getByText(input.state_key)).toBeInTheDocument();
      expect(within(row).getByText(input.owner)).toBeInTheDocument();
    });
  });

  it("shows a quantity in canonical terms beside the authored one", async () => {
    renderAt(SCENARIO_URL);
    await settledScreen();

    const parameters = tableNamed("Scenario-level authoring parameters");

    // A rate reads differently in canonical terms than as authored, which is
    // the case where the column earns its place.
    const rate = within(parameters).getByRole("row", {
      name: /generator-fuel-rate/,
    });
    expect(within(rate).getByText("14 L/h")).toBeInTheDocument();
    expect(
      within(rate).getByText("0.23333333333333334 L/min"),
    ).toBeInTheDocument();

    // And a phrase says so rather than rendering a blank cell.
    expect(within(parameters).getByText("Not a quantity")).toBeInTheDocument();
  });

  it("distinguishes a point from a window in the timeline", async () => {
    renderAt(SCENARIO_URL);
    await settledScreen();

    const timeline = panelNamed("Event and intervention timeline");
    const text = spacedText(timeline);

    expect(text).toContain("POINT");
    expect(text).toContain("WINDOW");
    expect(text).toContain("INTERVAL_WIDE");
    expect(text).toContain("240 min");
  });

  it("states a bound policy for every declared case", async () => {
    renderAt(SCENARIO_URL);
    await settledScreen();

    const rows = within(tableNamed("What a later run does at a bound"))
      .getAllByRole("row")
      .slice(1);

    const cases = SCENARIO_DETAIL.execution_contract.bound_cases;
    expect(rows).toHaveLength(cases.length);
    expect(cases.length).toBeGreaterThan(2);

    rows.forEach((row, index) => {
      expect(within(row).getByText(cases[index].policy)).toBeInTheDocument();
    });
  });
});

describe("the detail screen says where each reading comes from", () => {
  it("names the configured device and signal a device source reports through", async () => {
    renderAt(SCENARIO_URL);
    await settledScreen();

    const row = within(tableNamed("Where each reading comes from")).getByRole(
      "row",
      { name: /fuel-level-sensor-reading/ },
    );

    expect(within(row).getByText("DEVICE_SIGNAL")).toBeInTheDocument();
    expect(
      within(row).getByText("fuel-level-sensor, Fuel level sensor"),
    ).toBeInTheDocument();
    expect(
      within(row).getByText("fuel-level, Fuel level"),
    ).toBeInTheDocument();
  });

  it("gives the hand-recorded source an identity and no device", async () => {
    renderAt(SCENARIO_URL);
    await settledScreen();

    const row = within(tableNamed("Where each reading comes from")).getByRole(
      "row",
      { name: /operator-hand-record/ },
    );

    expect(within(row).getByText("OPERATOR_RECORD")).toBeInTheDocument();
    expect(within(row).getByText("No device")).toBeInTheDocument();
    expect(within(row).getByText("No signal")).toBeInTheDocument();
  });

  it("states who owns a cadence and never states one", async () => {
    renderAt(SCENARIO_URL);
    await settledScreen();

    const sources = panelNamed("Where each reading comes from");
    const text = spacedText(sources);

    expect(text).toContain("NOT_DECLARED");
    expect(text).toContain("NOT_APPLICABLE");

    // A cadence is a number. Every digit in this panel has to be one the
    // record supplies, and none of the cadence statements supplies one.
    for (const resolution of OBSERVATION_SOURCE_RESOLUTIONS) {
      expect(resolution.cadence_statement).not.toMatch(/\d/);
      expect(text).toContain(resolution.cadence_statement);
    }
  });
});

describe("the detail screen reconciles the readings it renders", () => {
  it("renders the reported value, the declared value and the difference", async () => {
    renderAt(SCENARIO_URL);
    await settledScreen();

    const table = tableNamed(
      "The readings, against the causes declared before them",
    );
    const rows = within(table).getAllByRole("row").slice(1);

    const results =
      SCENARIO_DETAIL.execution_contract.observation_reconciliation;
    expect(rows).toHaveLength(results.length);
    expect(results.length).toBeGreaterThan(1);

    rows.forEach((row, index) => {
      const result = results[index];
      expect(
        within(row).getByText(`${result.reported_value} ${result.unit}`),
      ).toBeInTheDocument();
      expect(
        within(row).getByText(`${result.declared_value} ${result.unit}`),
      ).toBeInTheDocument();
      expect(
        within(row).getByText(`${result.difference} ${result.unit}`),
      ).toBeInTheDocument();
      expect(within(row).getByText(result.state)).toBeInTheDocument();
    });
  });

  it("says which answer each reading got, and why", async () => {
    renderAt(SCENARIO_URL);
    await settledScreen();

    const table = tableNamed(
      "The readings, against the causes declared before them",
    );

    // A NOT_RECONCILABLE with no reason would be three different facts
    // wearing one name, so the reason is rendered beside the result.
    for (const result of SCENARIO_DETAIL.execution_contract
      .observation_reconciliation) {
      expect(within(table).getAllByText(result.reason).length).toBeGreaterThan(
        0,
      );
    }
  });

  it("names the version of the semantics being accepted", async () => {
    renderAt(SCENARIO_URL);
    await settledScreen();

    const panel = panelNamed(
      "How an entry is dispatched, and what happens at a bound",
    );

    expect(
      within(panel).getByText("Execution contract version"),
    ).toBeInTheDocument();
    expect(
      within(panel).getByText(
        String(SCENARIO_DETAIL.execution_contract.contract_version),
      ),
    ).toBeInTheDocument();
  });

  it("says the difference is unresolved rather than resolving it here", async () => {
    const { container } = renderAt(SCENARIO_URL);
    await settledScreen();

    const region = regionNamed(
      container,
      "scenario-observation-reconciliation",
    );
    const text = spacedText(region);

    expect(text).toMatch(/do not reach either of them/i);
    expect(text).toMatch(/three honest ways out/i);
    expect(text).not.toMatch(/\d/);
  });
});

describe("the scenario detail screen states no product outcome", () => {
  /**
   * Vocabulary that would say AssetOps has observed, judged, or acted on
   * something. No run exists in this build, so none of it can be true here.
   *
   * `\b` boundaries matter, which is why this reads `spacedText` rather than
   * `textContent`: the latter glues adjacent elements together and a word
   * boundary ban silently stops matching.
   */
  const BANNED =
    /\b(finding|findings|assessment|severity|confidence|health|incident|verification|verified|commit|committed|ingestion|ingested|replay|anomaly|alert|conclusion)\b/i;

  it("uses none of the product-outcome vocabulary", async () => {
    renderAt(SCENARIO_URL);
    await settledScreen();

    expect(spacedText(screen.getByRole("main"))).not.toMatch(BANNED);
  });

  it("renders no enabled control except the resolved target site link", async () => {
    renderAt(SCENARIO_URL);
    await settledScreen();

    const main = screen.getByRole("main");

    for (const button of within(main).getAllByRole("button", {
      hidden: true,
    })) {
      expect(button).toBeDisabled();
    }
    expect(
      within(main).queryByRole("button", { name: /commit|ingest|replay|run now/i }),
    ).toBeNull();
  });

  it("renders no digit that is not a record value, leaf by leaf", async () => {
    renderAt(SCENARIO_URL);
    await settledScreen();

    // The acceptance criterion is that no digit appears unless the record
    // supplies it. Two weaker forms of this were tried and both were rejected
    // in review, for reasons worth keeping:
    //
    // - comparing digit RUNS against the runs the record contains passes for
    //   an invented `7` as soon as any sequence number is 7;
    // - removing the containers that hold record values and banning digits in
    //   what is left carves out authored text too, because a table has
    //   headings, a fact value has a fallback and an action reason is prose.
    //
    // The checkable claim is at leaf level. Every text node is either exactly
    // a string the record supplies, or it carries no digit at all.
    const main = screen.getByRole("main");
    const expected = new Set(
      recordRenderedStrings(SCENARIO_DETAIL, RESOLVED_TARGET),
    );
    const leaves = textNodes(main);
    const withDigits = leaves.filter((leaf) => /\d/.test(leaf));

    // Non-vacuous: this screen really does render digits, so the loop below
    // is not iterating over nothing.
    expect(withDigits.length).toBeGreaterThan(15);

    for (const leaf of withDigits) {
      expect(expected).toContain(leaf);
    }

    // And the other direction, so the expectation cannot be padded into
    // uselessness: every digit-bearing string the record is supposed to put on
    // this screen is actually on it. Adding a junk entry to make a violation
    // pass would fail here.
    const rendered = new Set(leaves);
    const expectedWithDigits = [...expected].filter((value) =>
      /\d/.test(value),
    );
    expect(expectedWithDigits.length).toBeGreaterThan(15);
    for (const value of expectedWithDigits) {
      expect(rendered).toContain(value);
    }
  });

  it("renders no digit in the authored fallbacks either", async () => {
    // The loaded record takes none of the fallback branches - it has a
    // superseded version, a declared site, parameters on most rows, sources
    // and readings - so the strings the screen falls back to are dead code in
    // the test above. That was proved: a deliberate digit inserted into "No
    // earlier version" passed, because that branch never rendered.
    //
    // This record takes those branches. Every digit-bearing leaf it renders
    // still has to be one the record supplies.
    renderAt(
      SCENARIO_URL,
      ENABLED,
      catalogOf(
        loadedDetail(NOT_APPLICABLE_TARGET, SCENARIO_DETAIL_FALLBACKS, [], []),
      ),
    );
    await settledScreen();

    const main = screen.getByRole("main");
    const expected = new Set(
      recordRenderedStrings(
        SCENARIO_DETAIL_FALLBACKS,
        NOT_APPLICABLE_TARGET,
        [],
        [],
      ),
    );
    const leaves = textNodes(main);

    // The digit rule first, so that a fallback which grew a digit fails on the
    // rule it breaks rather than on the presence check below it.
    for (const leaf of leaves.filter((value) => /\d/.test(value))) {
      expect(expected).toContain(leaf);
    }

    // And the fallbacks really are on screen, so this is not a second run over
    // the branches the loaded record already takes. A fallback that vanished
    // would leave the loop above passing over nothing.
    expect(leaves).toContain("No earlier version");
    expect(leaves).toContain("None declared");
    expect(leaves).toContain(
      "This scenario declares no scenario-level parameter.",
    );
    expect(leaves).toContain("This scenario declares no expectation.");
    expect(leaves).toContain("This scenario declares no observation source.");
    expect(leaves).toContain("This scenario declares no initial world value.");
    expect(leaves).toContain("This scenario authors no reading to reconcile.");
  });
});

describe("the scenario detail screen's next-step controls", () => {
  it("renders Create Draft Run disabled, with the missing prerequisite named", async () => {
    renderAt(SCENARIO_URL);
    await settledScreen();

    const control = screen.getByRole("button", { name: "Create Draft Run" });

    expect(control).toBeDisabled();

    const reasonId = control.getAttribute("aria-describedby");
    expect(reasonId).not.toBeNull();
    const reason = document.getElementById(reasonId as string);
    expect(reason?.textContent).toMatch(/run setup does not exist yet/i);
    expect(reason?.textContent).toMatch(/draft simulation run/i);
  });

  it("opens the target site when the declared target resolves", async () => {
    renderAt(SCENARIO_URL);
    await settledScreen();

    expect(
      screen.getByRole("link", { name: "Open target site" }),
    ).toHaveAttribute("href", "/sites/MG-001");
  });

  it.each([
    ["an unconfigured target", UNCONFIGURED_TARGET],
    ["an unreadable site store", UNAVAILABLE_TARGET],
    ["a template-derived target", NOT_APPLICABLE_TARGET],
  ])(
    "disables the target site control for %s, with an accessible reason",
    async (_label, resolution) => {
      renderAt(SCENARIO_URL, ENABLED, catalogOf(loadedDetail(resolution)));
      await settledScreen();

      expect(screen.queryByRole("link", { name: "Open target site" })).toBeNull();

      const control = screen.getByRole("button", { name: "Open target site" });
      expect(control).toBeDisabled();

      const reasonId = control.getAttribute("aria-describedby");
      const reason = document.getElementById(reasonId as string);
      expect(reason?.textContent).toBe(resolution.reason);
    },
  );
});

describe("the accepted T017 semantics are no longer marked provisional", () => {
  const RETIRED = [
    "scenario-versioning",
    "scenario-event-taxonomy",
    "scenario-public-private-boundary",
  ];

  it.each(RETIRED)("has retired the %s region", async (id) => {
    const { container } = renderAt(SCENARIO_URL);
    await settledScreen();

    // Non-vacuous: the selector still finds this slice's own regions, so an
    // absent region below is an absence rather than a broken query.
    expect(
      container.querySelectorAll("[data-review-proposal]").length,
    ).toBeGreaterThan(0);

    expect(
      container.querySelector(`[data-review-proposal='${id}']`),
    ).toBeNull();
  });

  it("keeps the accepted vocabularies on screen as settled values", async () => {
    renderAt(SCENARIO_URL);
    await settledScreen();

    // The version fields, unchanged, and no longer inside a proposal.
    const versions = panelNamed("Scenario identity and version");
    for (const term of [
      "Scenario ID",
      "Scenario version",
      "Version valid from",
      "Supersedes",
    ]) {
      expect(within(versions).getByText(term)).toBeInTheDocument();
    }
    expect(
      versions.querySelector("[data-review-proposal]"),
    ).toBeNull();

    // The taxonomy legend, unchanged, and no longer inside a proposal.
    const timeline = panelNamed("Event and intervention timeline");
    const legendText = spacedText(timeline);
    for (const [value] of [
      ...EVENT_CATEGORY_LEGEND,
      ...TIMELINE_ENTRY_KIND_LEGEND,
    ]) {
      expect(legendText).toContain(value);
    }
    expect(timeline.querySelector("[data-review-proposal]")).toBeNull();

    // The private region, unchanged, and no longer inside a proposal.
    const privatePanel = panelNamed("Private test-oracle expectations");
    expect(
      privatePanel.querySelector("[data-private-region='expectations']"),
    ).not.toBeNull();
    expect(privatePanel.querySelector("[data-review-proposal]")).toBeNull();
  });

  it("still covers every taxonomy value the record uses", async () => {
    renderAt(SCENARIO_URL);
    await settledScreen();

    const categories = new Set(
      SCENARIO_DETAIL.timeline.map((entry) => entry.category),
    );
    const kinds = new Set(
      SCENARIO_DETAIL.timeline.map((entry) => entry.entry_kind),
    );

    // Non-vacuous by construction: the fixture uses the whole taxonomy, so a
    // legend that covered only part of it fails here.
    expect(categories.size).toBe(EVENT_CATEGORY_LEGEND.length);
    expect(kinds.size).toBe(TIMELINE_ENTRY_KIND_LEGEND.length);

    const legendText = spacedText(
      panelNamed("Event and intervention timeline"),
    );
    for (const value of [...categories, ...kinds]) {
      expect(legendText).toContain(value);
    }
  });

  it("keeps breaker position and control mode out of every vocabulary on screen", async () => {
    renderAt(SCENARIO_URL);
    await settledScreen();

    for (const [value] of [
      ...EVENT_CATEGORY_LEGEND,
      ...TIMELINE_ENTRY_KIND_LEGEND,
      ...EXECUTION_ROLE_LEGEND,
    ]) {
      expect(value).not.toMatch(
        /\b(OPEN|CLOSED|TRIPPED|AUTO|MANUAL|BREAKER)\b/,
      );
    }
  });
});

describe("the T018 checkpoint puts proposals on screen, not menus", () => {
  const REGIONS = [
    "scenario-execution-roles",
    "scenario-input-ownership",
    "scenario-timing-and-bounds",
    "scenario-observation-reconciliation",
  ];

  it.each(REGIONS)("marks the %s region visibly provisional", async (id) => {
    const { container } = renderAt(SCENARIO_URL);
    await settledScreen();

    const text = spacedText(regionNamed(container, id));

    expect(text).toContain(REVIEW_PROPOSAL_STATUS);
    expect(text).toMatch(/Proposed/);
    expect(text).toMatch(/Accepting this screen adopts/i);
    expect(text).toMatch(/Redirecting it would mean/i);
    expect(text).toMatch(/Already settled/i);
  });

  it.each(REGIONS)("renders no control inside the %s region", async (id) => {
    const { container } = renderAt(SCENARIO_URL);
    await settledScreen();

    expect(
      regionNamed(container, id).querySelectorAll(
        "button, input, select, textarea, form, a[href], [role='button']",
      ),
    ).toHaveLength(0);
  });

  it("asks each question beside the values it is about", async () => {
    const { container } = renderAt(SCENARIO_URL);
    await settledScreen();

    // Each region sits in the panel whose table a reader would look at to
    // answer it. A proposal about ownership placed away from the ownership
    // tables would be a question a reader has to imagine the answer to.
    expect(
      panelNamed("How each authored value executes").querySelector(
        "[data-review-proposal='scenario-execution-roles']",
      ),
    ).not.toBeNull();
    expect(
      panelNamed("Where each reading comes from").querySelector(
        "[data-review-proposal='scenario-input-ownership']",
      ),
    ).not.toBeNull();
    expect(
      panelNamed(
        "How an entry is dispatched, and what happens at a bound",
      ).querySelector("[data-review-proposal='scenario-timing-and-bounds']"),
    ).not.toBeNull();
    expect(
      panelNamed(
        "The readings, against the causes declared before them",
      ).querySelector(
        "[data-review-proposal='scenario-observation-reconciliation']",
      ),
    ).not.toBeNull();

    // And the tables those questions are about are all on the same screen.
    for (const name of [
      "Scenario-level authoring parameters",
      "Initial world values and who owns them",
      "Where each reading comes from",
      "What a later run does at a bound",
      "The readings, against the causes declared before them",
    ]) {
      expect(tableNamed(name)).toBeInTheDocument();
    }

    expect(container.querySelectorAll("[data-review-proposal]")).toHaveLength(
      REGIONS.length,
    );
  });
});

describe("the scenario surfaces do not grow operator navigation", () => {
  it("adds no operator navigation item and no operator Site tab", async () => {
    renderAt("/sites", ENABLED);
    await settledScreen();

    const navigation = screen.getByRole("navigation", {
      name: "Operator routes",
    });

    expect(spacedText(navigation)).not.toMatch(/scenario/i);
    expect(
      within(navigation).queryByRole("link", { name: /scenario/i }),
    ).toBeNull();
  });

  it("keeps the scenario surfaces inside the Lab's own shell", async () => {
    renderAt(SCENARIO_URL);
    await settledScreen();

    const navigation = screen.getAllByRole("navigation");
    expect(navigation).toHaveLength(1);
    expect(navigation[0]).toHaveAccessibleName("Simulator Lab routes");
  });
});
