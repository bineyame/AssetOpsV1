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
  PROPOSED_EVENT_CATEGORIES,
  PROPOSED_TIMELINE_ENTRY_KINDS,
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
 * screen, including the M1B checkpoint regions.
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
): ScenarioDetailResult {
  return {
    status: "loaded",
    scenario,
    targetResolution,
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
      expect(cells[2]).toBe(entry.entry_kind);
      expect(cells[3]).toBe(entry.category);
      expect(cells[4]).toContain(entry.description);
      expect(cells[4]).toContain(entry.event_id);
    });
  });

  it("renders a numeric parameter with its unit and a text parameter without one", async () => {
    renderAt(SCENARIO_URL);
    await settledScreen();

    const region = tableNamed("Public authoring parameters");

    expect(within(region).getByText("500 L")).toBeInTheDocument();
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

describe("the scenario detail screen states no product conclusion", () => {
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

  it("uses none of the product-conclusion vocabulary", async () => {
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
    // superseded version, a declared site, parameters on most rows - so the
    // strings the screen falls back to are dead code in the test above. That
    // was proved: a deliberate digit inserted into "No earlier version" passed,
    // because that branch never rendered.
    //
    // This record takes those branches. It carries no digit of its own, so
    // every digit-bearing leaf here would be one the screen invented.
    renderAt(
      SCENARIO_URL,
      ENABLED,
      catalogOf(loadedDetail(NOT_APPLICABLE_TARGET, SCENARIO_DETAIL_FALLBACKS, [])),
    );
    await settledScreen();

    const main = screen.getByRole("main");
    const expected = new Set(
      recordRenderedStrings(SCENARIO_DETAIL_FALLBACKS, NOT_APPLICABLE_TARGET, []),
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

describe("the M1B checkpoint puts a proposal on screen, not a menu", () => {
  const REGIONS = [
    "scenario-versioning",
    "scenario-event-taxonomy",
    "scenario-public-private-boundary",
  ];

  it.each(REGIONS)("marks the %s region visibly provisional", async (id) => {
    const { container } = renderAt(SCENARIO_URL);
    await settledScreen();

    const region = container.querySelector(`[data-review-proposal='${id}']`);
    expect(region).not.toBeNull();

    const text = spacedText(region as HTMLElement);
    expect(text).toContain(REVIEW_PROPOSAL_STATUS);
    expect(text).toMatch(/Proposed:/);
    expect(text).toMatch(/Accepting this screen adopts/i);
    expect(text).toMatch(/Redirecting it would mean/i);
    expect(text).toMatch(/Already settled/i);
  });

  it("proposes the version fields the screen renders", async () => {
    const { container } = renderAt(SCENARIO_URL);
    await settledScreen();

    const region = container.querySelector(
      "[data-review-proposal='scenario-versioning']",
    ) as HTMLElement;

    expect(spacedText(region)).toMatch(
      /Proposed: the four above/i,
    );
    // The fields the proposal points at are rendered directly above it, from
    // the record, so "the four above" names something the reader can see.
    const panel = panelNamed("Scenario identity and version");
    for (const term of [
      "Scenario ID",
      "Scenario version",
      "Version valid from",
      "Supersedes",
    ]) {
      expect(within(panel).getByText(term)).toBeInTheDocument();
    }
  });

  it("proposes a taxonomy that covers every value the record uses", async () => {
    renderAt(SCENARIO_URL);
    await settledScreen();

    const legendText = spacedText(
      panelNamed("Event and intervention timeline"),
    );

    const categories = new Set(
      SCENARIO_DETAIL.timeline.map((entry) => entry.category),
    );
    const kinds = new Set(
      SCENARIO_DETAIL.timeline.map((entry) => entry.entry_kind),
    );

    // Non-vacuous by construction: the fixture uses the whole taxonomy, so a
    // legend that covered only part of it fails here.
    expect(categories.size).toBe(PROPOSED_EVENT_CATEGORIES.length);
    expect(kinds.size).toBe(PROPOSED_TIMELINE_ENTRY_KINDS.length);

    for (const [value] of [
      ...PROPOSED_EVENT_CATEGORIES,
      ...PROPOSED_TIMELINE_ENTRY_KINDS,
    ]) {
      expect(legendText).toContain(value);
    }
    for (const value of [...categories, ...kinds]) {
      expect(
        [...PROPOSED_EVENT_CATEGORIES, ...PROPOSED_TIMELINE_ENTRY_KINDS].some(
          ([proposed]) => proposed === value,
        ),
      ).toBe(true);
    }
  });

  it("keeps breaker position and control mode out of the proposed taxonomy", async () => {
    renderAt(SCENARIO_URL);
    await settledScreen();

    const legend = panelNamed("Event and intervention timeline");

    for (const [value] of [
      ...PROPOSED_EVENT_CATEGORIES,
      ...PROPOSED_TIMELINE_ENTRY_KINDS,
    ]) {
      expect(value).not.toMatch(
        /\b(OPEN|CLOSED|TRIPPED|AUTO|MANUAL|BREAKER)\b/,
      );
    }

    expect(spacedText(legend)).toMatch(
      /breaker position and control mode/i,
    );
  });

  it("points the public/private proposal at both regions it separates", async () => {
    const { container } = renderAt(SCENARIO_URL);
    await settledScreen();

    const region = container.querySelector(
      "[data-review-proposal='scenario-public-private-boundary']",
    ) as HTMLElement;
    const text = spacedText(region);

    expect(text).toMatch(/public authoring data/i);
    expect(text).toMatch(/private expectation/i);
    expect(text).toMatch(/separate parsed fields/i);

    // Both halves are on the screen the question is asked on, so a reader can
    // answer it by looking rather than by imagining.
    expect(panelNamed("Public authoring parameters")).toBeInTheDocument();
    expect(
      container.querySelector("[data-private-region='expectations']"),
    ).not.toBeNull();
  });

  it("renders no control inside a proposal region", async () => {
    const { container } = renderAt(SCENARIO_URL);
    await settledScreen();

    for (const id of REGIONS) {
      const region = container.querySelector(
        `[data-review-proposal='${id}']`,
      ) as HTMLElement;
      expect(
        region.querySelectorAll(
          "button, input, select, textarea, form, a[href], [role='button']",
        ),
      ).toHaveLength(0);
    }
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
