import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SiteConfiguration } from "../SiteConfiguration";
import type { SiteDetailClient } from "../siteDirectoryClient";
import type {
  SiteDetailReadModel,
  SiteDetailResult,
} from "../siteReadModel";
import {
  FOUNDATION_DEVICE_METADATA_LIMITS,
  deriveSiteConfigurationView,
} from "../siteViewModel";
import {
  AWAITING_RUNTIME_OR_EVIDENCE,
  SITE_SLD_HEADING,
} from "../SiteSingleLineDiagram";
import { SLD_UNAVAILABLE_STATEMENTS } from "../sldViewModel";
import { settledScreen } from "../../test/settled";
import { spacedText, withoutRegion } from "../../test/text";

/**
 * Tests for one site's configuration, presented from the shared substrate.
 *
 * The substrate is rendered directly here, over records, with no shell and no
 * router around it, for the same reason the site-page tests are: nothing in
 * `frontend/src/sites/` may depend on which shell is rendering it, so nothing
 * here supplies a shell, a mode, or a flag.
 *
 * Three things carry the weight. Fidelity to the document: every value on
 * screen traces to the record, and the foundation's own semantics - an
 * open-ended validity interval, a declared rating that is not a measurement -
 * are stated rather than left to be inferred. Read-only: the deferred controls
 * are absent from the DOM rather than disabled, in every state, for every
 * origin. And honesty about what the M1 foundation does not carry: devices,
 * signal mappings and control assumptions are stated as undeclared with the
 * reason, never rendered as an empty list, which would say this site has none.
 */

const USER_SIMULATED_SITE: SiteDetailReadModel = {
  site_id: "MG-002",
  display_name: "Kalangala Mini-Grid",
  site_type: "MINIGRID",
  location: { country: "Uganda", locality: "Kalangala" },
  timezone: "Africa/Kampala",
  lifecycle_status: "PLANNED",
  origin: "USER",
  source: { mode: "SIMULATED" },
  template: { template_id: "hybrid-mini-grid-100kw", template_version: 1 },
  foundation: {
    version: 1,
    valid_from: "2026-09-14T09:12:00Z",
    summary:
      "Solar-plus-storage mini-grid with a diesel generator for backup and a " +
      "metered distribution load.",
    components: [
      {
        component_id: "pv-array",
        component_type: "PV_ARRAY",
        display_name: "PV array",
        rating: { value: 100, unit: "kW" },
        properties: null,
      },
      {
        component_id: "battery",
        component_type: "BATTERY",
        display_name: "Battery energy storage",
        rating: { value: 215, unit: "kWh" },
        properties: null,
      },
      {
        component_id: "site-meter",
        component_type: "METER",
        display_name: "Site meter",
        rating: null,
        properties: null,
      },
    ],
    // This site's foundation declares none of the four sections
    // T014 added. `null` is that statement; the backend refuses an
    // empty list, so there is no other way to say it.
    topology: null,
    devices: null,
    signal_mappings: null,
    control_assumptions: null,
  },
};

/**
 * The same site with a `SHIPPED` configuration origin and no template.
 *
 * Deliberately identical in every other field, including identity. These two
 * are never in a store together; they are two records handed to one component,
 * so that the read-only assertion below can be exact: what differs on screen
 * must be the origin and the template provenance and nothing else.
 */
const SHIPPED_SITE: SiteDetailReadModel = {
  ...USER_SIMULATED_SITE,
  origin: "SHIPPED",
  template: null,
};

/**
 * The same site with the four T014 sections declared.
 *
 * Deliberately the same components and the same identity as the site above, so
 * the two can be compared directly: everything that differs on screen between
 * them is content this site's foundation declares and the other's does not.
 *
 * The meter is the case worth having. It is attached to `site-meter` and its
 * bus-voltage signal describes `battery` - a device describing a component it
 * is not attached to. A view model that took the device's component instead of
 * the mapping's would still look right on every other row.
 */
const DECLARED_SITE: SiteDetailReadModel = {
  ...USER_SIMULATED_SITE,
  foundation: {
    ...USER_SIMULATED_SITE.foundation,
    // A foundation that declares everything this screen can render, so that
    // the paired absence tests below are about a record that supplies values
    // rather than about a fixture that happens not to.
    components: USER_SIMULATED_SITE.foundation.components.map((component) =>
      component.component_id === "battery"
        ? {
            ...component,
            properties: [
              {
                property_key: "reserve-state-of-charge",
                display_name: "Reserve state of charge",
                value: 25,
                unit: "%",
                kind: "CONTROL",
                source: "TEMPLATE",
                source_version: 2,
              },
            ],
          }
        : component.component_id === "pv-array"
          ? {
              ...component,
              properties: [
                {
                  property_key: "tank-capacity",
                  display_name: "Tank capacity",
                  value: 500,
                  unit: "L",
                  kind: "PHYSICAL",
                  source: "SITE",
                  source_version: 1,
                },
              ],
            }
          : component,
    ),
    topology: {
      nodes: [
        {
          node_id: "pv-array",
          component_id: "pv-array",
          node_role: "GENERATION",
        },
        {
          node_id: "battery",
          component_id: "battery",
          node_role: "STORAGE",
        },
        {
          node_id: "site-meter",
          component_id: "site-meter",
          node_role: "METERING",
        },
      ],
      connections: [
        {
          connection_id: "array-to-meter",
          from_node: "pv-array",
          to_node: "site-meter",
          medium: "AC",
        },
        {
          connection_id: "battery-to-meter",
          from_node: "battery",
          to_node: "site-meter",
          medium: "DC",
        },
      ],
    },
    devices: [
      {
        device_id: "pv-inverter-controller",
        device_type: "CONTROLLER",
        display_name: "PV inverter controller",
        component_id: "pv-array",
        signals: [
          {
            signal_id: "ac-power",
            display_name: "AC output power",
            unit: "kW",
          },
        ],
      },
      {
        device_id: "site-meter-unit",
        device_type: "METER",
        display_name: "Site meter unit",
        component_id: "site-meter",
        signals: [
          {
            signal_id: "bus-voltage",
            display_name: "Bus voltage",
            unit: "V",
          },
        ],
      },
    ],
    signal_mappings: [
      {
        mapping_id: "pv-ac-power",
        device_id: "pv-inverter-controller",
        signal_id: "ac-power",
        component_id: "pv-array",
      },
      {
        mapping_id: "battery-bus-voltage",
        device_id: "site-meter-unit",
        signal_id: "bus-voltage",
        component_id: "battery",
      },
    ],
    control_assumptions: [
      {
        assumption_id: "solar-first-dispatch",
        display_name: "Solar is dispatched first",
        component_id: null,
        basis: "TEMPLATE",
        statement: "A declared assumption about intended operation.",
      },
      {
        assumption_id: "battery-reserve",
        display_name: "The battery holds a reserve",
        component_id: "battery",
        basis: "SITE",
        statement: "The battery retains a reserve for evening supply.",
      },
    ],
  },
};

/** The Foundation subtab labels a container renders, in order. */
function subtabLabels(container: HTMLElement): string[] {
  return Array.from(container.querySelectorAll(".section-nav__list li")).map(
    (item) => item.textContent ?? "",
  );
}

/**
 * Everything that acts on the site, as opposed to everything interactive.
 *
 * T008 banned every interactive element here, which was right when the surface
 * had no links at all. T013 gives it a subtab row of same-page section links,
 * and a link that scrolls to a heading is not an action on a site. So the ban
 * on acting stays absolute and `a[href]` moves out of it, with every remaining
 * anchor pinned separately to a fragment that resolves.
 */
const ACTION_SELECTOR = [
  "button",
  "input",
  "select",
  "textarea",
  "form",
  "details",
  "summary",
  "[onclick]",
  "[role='button']",
  "[role='menuitem']",
  "[role='tab']",
  "[contenteditable='true']",
].join(", ");

/**
 * The controls the mockups show on canonical screen 3 that this slice does not
 * render in any state. Deferred by decision, so absent from the DOM rather
 * than disabled: disabled reads as "soon", and none of these is coming.
 *
 * `Version History` is the sharpest of them. It is not merely deferred - no
 * configuration-change model exists, and the eventual capability is an
 * auditable intervention record with a different name and a different meaning,
 * so rendering this label would name a real future capability wrongly.
 */
const ABSENT_CONTROL_LABELS = [
  "Edit",
  "Edit Configuration",
  "Version History",
  "Duplicate Site",
  "Delete Site",
  "Save",
  "Publish",
  "Rename",
  "Approve",
  "Diff",
  "History",
  "Rollback",
  "Change",
];

/**
 * The section that owns the configured diagram, and the block inside it that
 * asks the two questions this slice does not answer.
 *
 * T016 renders both, and both are narrow exceptions to bans that hold over the
 * rest of the screen: `diagram` is a word this surface may finally say, and
 * the control vocabulary is something the review checkpoint has to be able to
 * ask about. `withoutRegion` removes one of them and throws if it is not
 * there, so an exception that stopped existing cannot quietly widen the ban it
 * was carved out of.
 */
const SLD_REGION = "[data-sld-region]";
const REVIEW_QUESTION = "[data-review-question]";

/**
 * The control vocabulary this build must not use as a fact.
 *
 * `open` and `closed` are deliberately not in this list. The validity copy
 * says the interval is half-open, and a ban that matched it would be a ban
 * nobody could keep - which gets silenced by widening it, and a widened ban is
 * how a real one stops working.
 */
const CONTROL_VOCABULARY =
  /\b(breaker|contactor|setpoint|set point|tripped|control mode)\b/i;

/** Source health vocabulary, which must not appear where no health exists. */
const SOURCE_HEALTH_VOCABULARY = /\b(online|offline|stale|degraded|healthy)\b/i;

/** Asset and product assessment vocabulary, which has no source here either. */
const ASSESSMENT_VOCABULARY = /\b(healthy|watch|needs attention|degraded|unknown)\b/i;

function clientFor(result: SiteDetailResult): SiteDetailClient {
  return { getSite: () => Promise.resolve(result) };
}

function renderConfiguration(
  site: SiteDetailReadModel,
  siteId = site.site_id,
) {
  return render(
    <SiteConfiguration
      siteId={siteId}
      detail={clientFor({ status: "loaded", site })}
    />,
  );
}

/** Every digit run in a string, so screen values can be traced to a record. */
function digitRuns(text: string): string[] {
  return text.match(/\d+(?:\.\d+)?/g) ?? [];
}

/** The value rendered against one term in a definition list. */
function factValue(container: HTMLElement, term: string): string {
  const terms = Array.from(container.querySelectorAll("dt"));
  const match = terms.find((entry) => entry.textContent === term);

  expect(match, `no fact named ${term}`).toBeDefined();
  return (match as HTMLElement).nextElementSibling?.textContent ?? "";
}

/** Every fact on screen, as term-to-value pairs. */
function factPairs(container: HTMLElement): [string, string][] {
  return Array.from(container.querySelectorAll("dt")).map((term) => [
    term.textContent ?? "",
    term.nextElementSibling?.textContent ?? "",
  ]);
}

/** One component row, as its cell text. */
function componentRows(container: HTMLElement): string[][] {
  return Array.from(container.querySelectorAll("tbody tr")).map((row) =>
    Array.from(row.querySelectorAll("td")).map(
      (cell) => cell.textContent ?? "",
    ),
  );
}

describe("a configuration is rendered from its foundation document", () => {
  it("shows the foundation the record carries", async () => {
    const { container } = renderConfiguration(USER_SIMULATED_SITE);
    await settledScreen();

    expect(factValue(container, "Site ID")).toBe("MG-002");
    expect(factValue(container, "Timezone")).toBe("Africa/Kampala");
    expect(factValue(container, "Foundation version")).toBe("1");
    expect(factValue(container, "Valid from")).toBe("2026-09-14T09:12:00Z");
    expect(factValue(container, "Summary")).toBe(
      USER_SIMULATED_SITE.foundation.summary,
    );
  });

  it("renders every declared component with its declared rating", async () => {
    const { container } = renderConfiguration(USER_SIMULATED_SITE);
    await settledScreen();

    expect(componentRows(container)).toEqual([
      ["PV array", "PV array", "100 kW", "pv-array"],
      ["Battery energy storage", "Battery", "215 kWh", "battery"],
      ["Site meter", "Meter", "No rating declared", "site-meter"],
    ]);
  });

  it("says a component declares no rating rather than rating it zero", async () => {
    const { container } = renderConfiguration(USER_SIMULATED_SITE);
    await settledScreen();

    // No rating and a rating of zero are different facts, and the document
    // states only the first. A `0` here would be a nameplate claim.
    const meterRow = componentRows(container).find(
      (row) => row[3] === "site-meter",
    );

    expect(meterRow?.[2]).toBe("No rating declared");
    expect(meterRow?.[2]).not.toMatch(/\d/);
  });

  it("states what the validity interval means rather than leaving it inferred", async () => {
    const { container } = renderConfiguration(USER_SIMULATED_SITE);
    await settledScreen();

    // A start date on its own leaves a reader to guess whether the
    // configuration has since stopped applying.
    expect(spacedText(container)).toMatch(/half-open/i);
    expect(spacedText(container)).toMatch(/has no recorded end/i);

    // And it is not a configuration history, which is a different thing the
    // product does not have.
    expect(spacedText(container)).toMatch(/not a configuration history/i);
  });

  it("renders no digit the record does not supply", async () => {
    const { container } = renderConfiguration(USER_SIMULATED_SITE);
    await settledScreen();

    const fromRecord = new Set(digitRuns(JSON.stringify(USER_SIMULATED_SITE)));
    const onScreen = digitRuns(container.textContent ?? "");

    expect(onScreen.length).toBeGreaterThan(0);
    for (const value of onScreen) {
      expect(fromRecord).toContain(value);
    }
  });

  it("renders the site's own timestamp verbatim and invents no other", async () => {
    const { container } = renderConfiguration(USER_SIMULATED_SITE);
    await settledScreen();

    const timestamps =
      (container.textContent ?? "").match(
        /\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}(?::\d{2})?Z?)?/g,
      ) ?? [];

    expect(timestamps).toEqual(["2026-09-14T09:12:00Z"]);
  });

  it("renders the stored canonical site ID, not the one in the address", async () => {
    const { container } = renderConfiguration(USER_SIMULATED_SITE, "mg-002");
    await settledScreen();

    expect(factValue(container, "Site ID")).toBe("MG-002");
    expect(spacedText(container)).not.toMatch(/mg-002/);
  });
});

describe("configuration is fixed at creation", () => {
  it("states it plainly", async () => {
    const { container } = renderConfiguration(USER_SIMULATED_SITE);
    await settledScreen();

    expect(
      screen.getByRole("heading", {
        level: 2,
        name: "Configuration is fixed at creation",
      }),
    ).toBeInTheDocument();
    expect(spacedText(container)).toMatch(
      /Configuration is fixed at creation in M1/,
    );
    expect(spacedText(container)).toMatch(
      /AssetOps does not edit a site's foundation in this milestone/i,
    );
  });

  it("does not describe the present arrangement as temporary", async () => {
    const { container } = renderConfiguration(USER_SIMULATED_SITE);
    await settledScreen();

    // The statement says what M1 does and does not do. Anything that reads as
    // "not yet" turns a decision into a promise the product has not made.
    const statement = deriveSiteConfigurationView(USER_SIMULATED_SITE)
      .configurationFixedAtCreation;

    expect(statement).not.toMatch(
      /\b(not yet|for now|at present|currently|soon|coming|future|will be able|planned)\b/i,
    );
    expect(spacedText(container)).not.toMatch(
      /\b(coming soon|not yet available|will be editable|future release)\b/i,
    );
  });

  it("names no editing workflow anywhere on the screen", async () => {
    const { container } = renderConfiguration(USER_SIMULATED_SITE);
    await settledScreen();

    // `Version History` is the one to watch: the eventual capability in that
    // territory is an auditable intervention record, so this label would name
    // a real future capability by the wrong name.
    expect(spacedText(container)).not.toMatch(/version history/i);
    expect(spacedText(container)).not.toMatch(/edit configuration/i);
    expect(spacedText(container)).not.toMatch(/\brollback\b/i);
    expect(spacedText(container)).not.toMatch(/\bapproval\b/i);
  });
});

describe("no action control renders, in any state", () => {
  it.each([
    ["a configured site", { status: "loaded", site: USER_SIMULATED_SITE }],
    ["a site that is not found", { status: "not_found" }],
    ["an unreadable store", { status: "unavailable" }],
  ])("offers no control at all for %s", async (_name, result) => {
    const { container } = render(
      <SiteConfiguration
        siteId="MG-002"
        detail={clientFor(result as SiteDetailResult)}
      />,
    );
    await settledScreen();

    // Absence, not disablement: nothing here is rendered and then greyed out,
    // so there is no control to check `disabled` or `aria-disabled` on.
    //
    // T013 adds the Foundation subtab row, whose section links are the only
    // interactive elements this surface has. They are navigation within one
    // page, not actions on the site, so the claim narrows from "nothing is
    // interactive" to "nothing acts" - and gains the stricter half below,
    // which pins every link to a fragment resolving to a section that is
    // actually on the page.
    expect(container.querySelectorAll(ACTION_SELECTOR)).toHaveLength(0);
    expect(container.querySelectorAll("[disabled]")).toHaveLength(0);
    expect(container.querySelectorAll("[aria-disabled]")).toHaveLength(0);

    for (const anchor of Array.from(container.querySelectorAll("a[href]"))) {
      const href = anchor.getAttribute("href") ?? "";

      expect(href.startsWith("#")).toBe(true);
      expect(container.querySelector(href)).not.toBeNull();
    }
  });

  it.each(ABSENT_CONTROL_LABELS)("does not render %s as a control", async (label) => {
    renderConfiguration(USER_SIMULATED_SITE);
    await settledScreen();

    expect(screen.queryByRole("button", { name: label })).toBeNull();
    expect(screen.queryByRole("link", { name: label })).toBeNull();
    expect(screen.queryByText(label)).toBeNull();
  });

  it("offers no crossing into the Simulator Lab", async () => {
    const { container } = renderConfiguration(USER_SIMULATED_SITE);
    await settledScreen();

    expect(spacedText(container)).not.toMatch(/simulator/i);
    for (const anchor of Array.from(container.querySelectorAll("a"))) {
      expect(anchor.getAttribute("href")).not.toMatch(/simulat/i);
    }
  });
});

describe("the screen is read-only whatever the configuration origin is", () => {
  it("renders a SHIPPED-origin site and a USER-origin site the same way", async () => {
    const user = renderConfiguration(USER_SIMULATED_SITE);
    await settledScreen(user.container);
    const userFacts = factPairs(user.container);
    const userComponents = componentRows(user.container);
    const userSubtabs = subtabLabels(user.container);
    user.unmount();

    const shipped = renderConfiguration(SHIPPED_SITE);
    await settledScreen(shipped.container);

    // Only the two facts that differ in the records differ on screen.
    const differing = factPairs(shipped.container)
      .filter(([term, value], index) => {
        const [userTerm, userValue] = userFacts[index];
        return term !== userTerm || value !== userValue;
      })
      .map(([term]) => term);

    expect(differing).toEqual(["Configuration origin", "Created from template"]);
    expect(factValue(shipped.container, "Configuration origin")).toBe("Shipped");
    expect(factValue(shipped.container, "Created from template")).toBe(
      "Not created from a template",
    );
    expect(componentRows(shipped.container)).toEqual(userComponents);

    // And it is read-only in both: origin is not a permission.
    expect(shipped.container.querySelectorAll(ACTION_SELECTOR)).toHaveLength(0);

    // The subtab row is identical too, so origin does not change which
    // sections of a foundation the product says exist. Captured before the
    // first render was unmounted, because a list read off an unmounted
    // container is empty and would have compared two nothings.
    expect(subtabLabels(shipped.container)).toEqual(userSubtabs);
    expect(userSubtabs.length).toBeGreaterThan(0);
  });
});

describe("the six provenance and status concepts stay six here too", () => {
  it("renders each of the six separately", async () => {
    const { container } = renderConfiguration(USER_SIMULATED_SITE);
    await settledScreen();

    expect(factValue(container, "Configuration origin")).toBe("User");
    expect(factValue(container, "Mode")).toBe("Simulated");
    expect(factValue(container, "Lifecycle status")).toBe("Planned");
    expect(factValue(container, "Integration readiness")).toMatch(
      /^Not recorded\./,
    );
    expect(factValue(container, "Evidence availability")).toMatch(
      /^No evidence\./,
    );
    expect(factValue(container, "Source health")).toMatch(/^Not recorded\./);
  });

  it("keeps mode out of lifecycle status and lifecycle status out of mode", async () => {
    const { container } = renderConfiguration(USER_SIMULATED_SITE);
    await settledScreen();

    expect(factValue(container, "Lifecycle status")).not.toMatch(/simulated/i);
    expect(factValue(container, "Mode")).not.toMatch(/planned/i);

    const terms = Array.from(container.querySelectorAll("dt")).map(
      (term) => term.textContent,
    );

    expect(terms).not.toContain("Status");
  });
});

describe("what this site's foundation does not declare is stated, not implied", () => {
  it.each([
    ["Topology", /declares no topology/i],
    ["Devices", /declares no device/i],
    ["Signal mappings", /declares no device-to-signal mapping/i],
    ["Control assumptions", /declares no control assumption/i],
  ])("states %s as undeclared, with the reason", async (term, reason) => {
    const { container } = renderConfiguration(USER_SIMULATED_SITE);
    await settledScreen();

    expect(factValue(container, term)).toMatch(/^Not declared\./);
    expect(factValue(container, term)).toMatch(reason);
  });

  it("says the absence is about this document, not about what a schema can hold", async () => {
    const { container } = renderConfiguration(USER_SIMULATED_SITE);
    await settledScreen();

    // T008's reason was that the M1 schema had nowhere to put a device. T014
    // gives it somewhere, so that reason became untrue the moment this slice
    // landed, and a reason that is no longer true is worse than none: it
    // explains an absence by a constraint the product no longer has.
    expect(spacedText(container)).not.toMatch(
      /nothing below them|the M1 site foundation (?:declares|carries)/i,
    );
    expect(factValue(container, "Devices")).toMatch(
      /this site's foundation document declares no device/i,
    );
  });

  it("says the absence is about the document, not about the site", async () => {
    const { container } = renderConfiguration(USER_SIMULATED_SITE);
    await settledScreen();

    // "No devices" would be a claim about this site. What is true is narrower:
    // this milestone's configuration document has nowhere to put one.
    expect(factValue(container, "Devices")).toMatch(
      /not a statement that this site has no devices/i,
    );
    expect(spacedText(container)).not.toMatch(/\bno devices are configured\b/i);
  });

  it("renders no empty list, table, or count standing in for them", async () => {
    const { container } = renderConfiguration(USER_SIMULATED_SITE);
    await settledScreen();

    // One table on this screen, and it is the components table, which has
    // rows. An empty devices table would state that this site has no devices.
    const tables = Array.from(container.querySelectorAll("table"));

    expect(tables).toHaveLength(1);
    expect(tables[0].querySelectorAll("tbody tr").length).toBeGreaterThan(0);
    expect(container.querySelectorAll("meter, progress")).toHaveLength(0);
  });
});

describe("a configuration-only site fabricates nothing", () => {
  it("states what this build records, never what the site has", async () => {
    const { container } = renderConfiguration(USER_SIMULATED_SITE);
    await settledScreen();

    // The record carries no integration field and no source-health field, so
    // neither fact may describe this site's integration or its source. A site
    // registered against a real integration arrives with exactly these fields,
    // and copy saying no integration is configured would describe it wrongly.
    const readiness = factValue(container, "Integration readiness");
    const health = factValue(container, "Source health");

    expect(readiness).toMatch(/this build records no integration readiness/i);
    expect(health).toMatch(/this build records no source health/i);
    expect(readiness).not.toMatch(/no integration is configured/i);
    expect(health).not.toMatch(/expected to report|has no health state/i);
  });

  it("renders no chart, image, figure, or diagram surface", async () => {
    const { container } = renderConfiguration(USER_SIMULATED_SITE);
    await settledScreen();

    expect(
      container.querySelectorAll("svg, canvas, img, picture, figure, iframe"),
    ).toHaveLength(0);
    expect(screen.queryAllByRole("figure")).toHaveLength(0);
    expect(screen.queryAllByRole("img")).toHaveLength(0);
  });

  it("keeps diagram vocabulary inside the diagram section, and renders no signal selector", async () => {
    const { container } = renderConfiguration(USER_SIMULATED_SITE);
    await settledScreen();

    // T016 inverted the first half of this. The configured diagram renders
    // now, so a screen-wide ban on the word would be a ban on the content the
    // task requires - and dropping it would leave the rest of the surface with
    // nothing holding diagram vocabulary out of it.
    //
    // So the ban narrows to everywhere outside the section that owns the
    // diagram, and holds there exactly as it did. This site's foundation
    // declares no topology, so what that section holds is the refusal rather
    // than a drawing; the ban outside it is the same either way.
    //
    // `spacedText` rather than `textContent`, and the difference is not
    // cosmetic. `textContent` glues adjacent elements together, so a banned
    // word sitting next to its neighbour has no word boundary and the ban
    // cannot match it. This assertion passed that way while matching nothing
    // at all.
    //
    // `topology` left the list. T013 renders a Topology subtab and panel by
    // requirement, so banning the word here would ask a later slice to hide
    // content the task demands.
    const elsewhere = withoutRegion(container, SLD_REGION);

    expect(spacedText(elsewhere)).not.toMatch(
      /single line diagram|one-line diagram|\bdiagram\b|\bschematic\b/i,
    );

    const headings = Array.from(
      elsewhere.querySelectorAll("h1, h2, h3, h4, h5, h6"),
    ).map((heading) => heading.textContent ?? "");

    expect(headings.length).toBeGreaterThan(0);
    for (const heading of headings) {
      expect(heading).not.toMatch(/diagram|signal selector|select a signal/i);
    }

    // The exception is one section, named once, and it is where the diagram
    // heading lives. Two of them would mean the surface had grown a second
    // home for this content.
    expect(container.querySelectorAll(SLD_REGION)).toHaveLength(1);
    expect(
      Array.from(container.querySelectorAll("h3")).map(
        (heading) => heading.textContent,
      ),
    ).toContain(SITE_SLD_HEADING);

    // `Signal mappings` appears, as a stated absence with its reason. A
    // selector is a control, and there is none: no combobox, no listbox, no
    // select element of any kind. This half is unchanged - the signal selector
    // is still absent, because there is still nothing to show for the signal a
    // reader would have picked.
    expect(screen.queryByRole("combobox")).toBeNull();
    expect(screen.queryByRole("listbox")).toBeNull();
    expect(container.querySelectorAll("select, datalist")).toHaveLength(0);
  });

  it("renders no evidence-derived value, count, or column", async () => {
    const { container } = renderConfiguration(USER_SIMULATED_SITE);
    await settledScreen();

    const terms = Array.from(container.querySelectorAll("dt")).map(
      (term) => term.textContent ?? "",
    );
    const columns = Array.from(container.querySelectorAll("th")).map(
      (column) => column.textContent ?? "",
    );

    expect(terms.length).toBeGreaterThan(0);
    expect(columns.length).toBeGreaterThan(0);
    for (const heading of [...terms, ...columns]) {
      expect(heading).not.toMatch(
        /\b(last data|last analysed|last seen|telemetry|analytics|replay|findings?|uptime|availability %|gateway)\b/i,
      );
    }
  });

  it("uses no source-health or assessment vocabulary", async () => {
    const { container } = renderConfiguration(USER_SIMULATED_SITE);
    await settledScreen();

    expect(spacedText(container)).not.toMatch(SOURCE_HEALTH_VOCABULARY);
    expect(spacedText(container)).not.toMatch(ASSESSMENT_VOCABULARY);
  });

  it("labels a declared rating as declared, never as a measurement", async () => {
    const { container } = renderConfiguration(USER_SIMULATED_SITE);
    await settledScreen();

    const columns = Array.from(container.querySelectorAll("th")).map(
      (column) => column.textContent ?? "",
    );

    expect(columns).toContain("Declared rating");
    expect(spacedText(container)).toMatch(
      /These are configuration, not measurements/i,
    );
  });
});

describe("the configuration is addressed by site ID and nothing else", () => {
  it("states not found for a site that is not configured", async () => {
    render(
      <SiteConfiguration
        siteId="MG-404"
        detail={clientFor({ status: "not_found" })}
      />,
    );

    expect(
      await screen.findByRole("heading", { level: 2, name: "No such site" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/No site with that site ID is configured/i),
    ).toBeInTheDocument();
  });

  it("renders no configuration at all when the site is not found", async () => {
    const { container } = render(
      <SiteConfiguration
        siteId="MG-404"
        detail={clientFor({ status: "not_found" })}
      />,
    );
    await screen.findByRole("heading", { level: 2, name: "No such site" });

    // Not found is a refusal, never a site with an empty foundation.
    expect(container.querySelectorAll("dl, table")).toHaveLength(0);
    expect(spacedText(container)).not.toMatch(/Foundation version/i);
  });

  it("names no site when the address identifies none", async () => {
    render(
      <SiteConfiguration
        siteId={undefined}
        detail={clientFor({ status: "loaded", site: USER_SIMULATED_SITE })}
      />,
    );

    expect(
      await screen.findByRole("heading", { level: 2, name: "No such site" }),
    ).toBeInTheDocument();
  });

  it("states an unreadable store rather than an absent configuration", async () => {
    render(
      <SiteConfiguration
        siteId="MG-002"
        detail={clientFor({ status: "unavailable" })}
      />,
    );

    expect(
      await screen.findByRole("heading", { level: 2, name: "Site unavailable" }),
    ).toBeInTheDocument();
    expect(screen.queryByText(/No such site/i)).toBeNull();
  });

  it("drops the configuration on screen the moment the address names another", async () => {
    // The same rule the site page follows, and the same shared read behind it.
    // A foundation still standing under a new address is the wrong site's
    // configuration presented as the right one.
    let answerSecond: (result: SiteDetailResult) => void = () => {};
    const detail: SiteDetailClient = {
      getSite: (siteId) =>
        siteId === USER_SIMULATED_SITE.site_id
          ? Promise.resolve<SiteDetailResult>({
              status: "loaded",
              site: USER_SIMULATED_SITE,
            })
          : new Promise<SiteDetailResult>((resolve) => {
              answerSecond = resolve;
            }),
    };

    const { container, rerender } = render(
      <SiteConfiguration siteId="MG-002" detail={detail} />,
    );
    await settledScreen();
    expect(factValue(container, "Site ID")).toBe("MG-002");

    rerender(<SiteConfiguration siteId="MG-404" detail={detail} />);

    expect(spacedText(container)).not.toMatch(/MG-002|Kalangala|pv-array/);
    expect(container.querySelectorAll("dl, table")).toHaveLength(0);

    answerSecond({ status: "not_found" });

    expect(
      await screen.findByRole("heading", { level: 2, name: "No such site" }),
    ).toBeInTheDocument();
  });
});

/** Every row of the table named by a subsection heading, as cell text. */
function tableRows(container: HTMLElement, headingId: string): string[][] {
  const table = container.querySelector(`table[aria-labelledby="${headingId}"]`);

  expect(table, `no table named by ${headingId}`).not.toBeNull();
  return Array.from((table as HTMLElement).querySelectorAll("tbody tr")).map(
    (row) =>
      Array.from(row.querySelectorAll("td")).map(
        (cell) => cell.textContent ?? "",
      ),
  );
}

/** The column headers of the table named by a subsection heading. */
function tableColumns(container: HTMLElement, headingId: string): string[] {
  const table = container.querySelector(`table[aria-labelledby="${headingId}"]`);

  expect(table, `no table named by ${headingId}`).not.toBeNull();
  return Array.from((table as HTMLElement).querySelectorAll("thead th")).map(
    (column) => column.textContent ?? "",
  );
}

const TOPOLOGY_NODES_ID = "foundation-topology-nodes-heading";
const CONNECTIONS_ID = "foundation-topology-connections-heading";
const DEVICES_ID = "foundation-devices-heading";
const MAPPINGS_ID = "foundation-signal-mappings-heading";
const ASSUMPTIONS_ID = "foundation-control-assumptions-heading";

describe("a declared topology renders as configuration read back", () => {
  it("renders one row per declared topology node, named by its component", async () => {
    const { container } = renderConfiguration(DECLARED_SITE);
    await settledScreen();

    expect(tableRows(container, TOPOLOGY_NODES_ID)).toEqual([
      ["PV array", "Generation", "pv-array", "pv-array"],
      ["Battery energy storage", "Storage", "battery", "battery"],
      ["Site meter", "Metering", "site-meter", "site-meter"],
    ]);
  });

  it("renders each connection by the components at its ends", async () => {
    const { container } = renderConfiguration(DECLARED_SITE);
    await settledScreen();

    // Named by component rather than by node identity: a reader following a
    // connection is following two components, and resolving two node ids to
    // see that is work the view model should have done.
    expect(tableRows(container, CONNECTIONS_ID)).toEqual([
      ["PV array", "Site meter", "AC", "array-to-meter"],
      ["Battery energy storage", "Site meter", "DC", "battery-to-meter"],
    ]);
  });

  it("renders each device with the component it is attached to and what it can report", async () => {
    const { container } = renderConfiguration(DECLARED_SITE);
    await settledScreen();

    expect(tableRows(container, DEVICES_ID)).toEqual([
      [
        "PV inverter controller",
        "Controller",
        "PV array",
        "AC output power (kW)",
        "pv-inverter-controller",
      ],
      [
        "Site meter unit",
        "Meter",
        "Site meter",
        "Bus voltage (V)",
        "site-meter-unit",
      ],
    ]);
  });

  it("renders a mapping against the component the mapping declares", async () => {
    const { container } = renderConfiguration(DECLARED_SITE);
    await settledScreen();

    // The meter is attached to `site-meter` and this signal describes
    // `battery`. Taking the device's component instead of the mapping's would
    // read as `Site meter` here and would be wrong in exactly the way a whole
    // class of real mapping is: a meter reports for what it measures, not for
    // where it is bolted.
    expect(tableRows(container, MAPPINGS_ID)).toEqual([
      [
        "AC output power",
        "ac-power",
        "kW",
        "PV inverter controller",
        "PV array",
        "pv-ac-power",
      ],
      [
        "Bus voltage",
        "bus-voltage",
        "V",
        "Site meter unit",
        "Battery energy storage",
        "battery-bus-voltage",
      ],
    ]);
  });

  it("renders a control assumption about the site without naming a component", async () => {
    const { container } = renderConfiguration(DECLARED_SITE);
    await settledScreen();

    expect(tableRows(container, ASSUMPTIONS_ID)).toEqual([
      [
        "Solar is dispatched first",
        "The whole site",
        "Template",
        "A declared assumption about intended operation.",
      ],
      [
        "The battery holds a reserve",
        "Battery energy storage",
        "Site",
        "The battery retains a reserve for evening supply.",
      ],
    ]);
  });

  it("stops stating the absences the record now supplies", async () => {
    const { container } = renderConfiguration(DECLARED_SITE);
    await settledScreen();

    // The T008 absences disappear only where the record supplies values, which
    // is what the paired test below holds the other half of.
    const terms = Array.from(container.querySelectorAll("dt")).map(
      (term) => term.textContent,
    );

    expect(terms).not.toContain("Devices");
    expect(terms).not.toContain("Signal mappings");
    expect(terms).not.toContain("Control assumptions");
    expect(terms).not.toContain("Topology");
    expect(spacedText(container)).not.toMatch(/Not declared/);
  });

  it("still states them for a site whose foundation declares none", async () => {
    const { container } = renderConfiguration(USER_SIMULATED_SITE);
    await settledScreen();

    // The same screen, the same schema, a document that declares nothing. A
    // site with no declared devices must say so in words: an empty table would
    // state that this site has none.
    expect(container.querySelector(`#${DEVICES_ID}`)).not.toBeNull();
    expect(
      container.querySelector(`table[aria-labelledby="${DEVICES_ID}"]`),
    ).toBeNull();
    expect(factValue(container, "Devices")).toMatch(/^Not declared\./);
  });

  it("renders no digit the declared record does not supply", async () => {
    const { container } = renderConfiguration(DECLARED_SITE);
    await settledScreen();

    const fromRecord = new Set(digitRuns(JSON.stringify(DECLARED_SITE)));
    const onScreen = digitRuns(container.textContent ?? "");

    expect(onScreen.length).toBeGreaterThan(0);
    for (const value of onScreen) {
      expect(fromRecord).toContain(value);
    }
  });
});

/**
 * A diagram incompatibility is a fact about the drawing, and nothing else.
 *
 * `DECLARED_SITE` declares three topology nodes and no bus, which is exactly
 * what the hybrid mini-grid archetype cannot arrange - so this file's main
 * fixture is already the interesting case. It has valid devices and valid
 * mappings, and a screen that stopped rendering them because the archetype had
 * no lane for its topology would be treating "we cannot draw this" as "there
 * is nothing here".
 */
describe("an undrawable topology hides nothing the document declares", () => {
  it("states the refusal where the drawing would have been", async () => {
    const { container } = renderConfiguration(DECLARED_SITE);
    await settledScreen();

    const region = container.querySelector(SLD_REGION) as HTMLElement;

    expect(region).not.toBeNull();
    expect(region.querySelector("[data-sld-unavailable]")).not.toBeNull();
    // The refusal is the view model's own, word for word. Two surfaces
    // explaining one refusal differently is how a stable reason stops being
    // one.
    expect(spacedText(region)).toContain(
      SLD_UNAVAILABLE_STATEMENTS.BUS_CARDINALITY_UNSUPPORTED,
    );
    // And not a partial drawing of the part the archetype did understand.
    expect(region.querySelectorAll("svg")).toHaveLength(0);
    expect(region.querySelectorAll("[data-sld-node]")).toHaveLength(0);
  });

  it("says the refusal is about the drawing and not about the site", async () => {
    const { container } = renderConfiguration(DECLARED_SITE);
    await settledScreen();

    const region = container.querySelector(SLD_REGION) as HTMLElement;

    expect(spacedText(region)).toMatch(
      /statement about the drawing, not about the site/i,
    );
    expect(spacedText(region)).toMatch(/Nothing is hidden/i);
  });

  it("still renders every device and mapping the document declares", async () => {
    const { container } = renderConfiguration(DECLARED_SITE);
    await settledScreen();

    // The whole point. The archetype refused the topology; the devices and the
    // mappings are unaffected, because neither was what it refused.
    expect(tableRows(container, DEVICES_ID)).toHaveLength(
      DECLARED_SITE.foundation.devices?.length ?? 0,
    );
    expect(tableRows(container, MAPPINGS_ID)).toHaveLength(
      DECLARED_SITE.foundation.signal_mappings?.length ?? 0,
    );
    expect(tableRows(container, TOPOLOGY_NODES_ID)).toHaveLength(
      DECLARED_SITE.foundation.topology?.nodes.length ?? 0,
    );

    // Stated as declared content, not as an absence. A screen that answered a
    // diagram refusal by saying the document declares no device would be
    // making a claim about the site out of a limit of the archetype.
    expect(factPairs(container).map(([term]) => term)).not.toContain("Devices");
  });

  it("puts no value slot on a screen with no drawing to hang one on", async () => {
    const { container } = renderConfiguration(DECLARED_SITE);
    await settledScreen();

    // The slot belongs to a drawn node. With no drawing there is no node, so
    // there is nothing for the words to be about, and printing them anyway
    // would be chrome claiming content.
    expect(spacedText(container)).not.toContain(AWAITING_RUNTIME_OR_EVIDENCE);
  });

  it("states the two device facts this build's schema cannot carry", async () => {
    const { container } = renderConfiguration(DECLARED_SITE);
    await settledScreen();

    // In words, once, rather than as two columns of dashes. A dash under
    // `Protocol` would say the product looked at this device and found none,
    // which is a claim about the device instead of about the schema.
    expect(spacedText(container)).toContain(FOUNDATION_DEVICE_METADATA_LIMITS);

    const columns = Array.from(container.querySelectorAll("th")).map(
      (column) => column.textContent ?? "",
    );

    expect(columns.length).toBeGreaterThan(0);
    for (const column of columns) {
      expect(column).not.toMatch(/\b(protocol|cadence|sample rate|interval)\b/i);
    }
  });
});

describe("declared topology content states nothing operational", () => {
  it("renders no runtime, evidence, or condition column", async () => {
    const { container } = renderConfiguration(DECLARED_SITE);
    await settledScreen();

    const columns = Array.from(container.querySelectorAll("th")).map(
      (column) => column.textContent ?? "",
    );

    expect(columns.length).toBeGreaterThan(0);
    for (const column of columns) {
      expect(column).not.toMatch(
        /\b(status|state|health|last (?:data|seen|reading)|value|reading|telemetry|condition|cadence)\b/i,
      );
    }
  });

  it("uses no source-health or assessment vocabulary about a device", async () => {
    const { container } = renderConfiguration(DECLARED_SITE);
    await settledScreen();

    expect(spacedText(container)).not.toMatch(SOURCE_HEALTH_VOCABULARY);
    expect(spacedText(container)).not.toMatch(ASSESSMENT_VOCABULARY);
  });

  it("says devices are configured and awaiting runtime, not operating", async () => {
    const { container } = renderConfiguration(DECLARED_SITE);
    await settledScreen();

    expect(spacedText(container)).toMatch(
      /configured assets awaiting runtime and evidence/i,
    );
    expect(spacedText(container)).toMatch(/none has reported/i);
  });

  it("names no control state, setpoint, or breaker position outside the question that asks for one", async () => {
    const { container } = renderConfiguration(DECLARED_SITE);
    await settledScreen();

    // T016 is the checkpoint that settles this vocabulary, and a checkpoint
    // that cannot name the candidates is not a question anyone can answer. So
    // the ban narrows to everywhere outside the block that asks, where it
    // holds exactly as it did, and gains a second half that is stricter than
    // the first ever was.
    expect(
      spacedText(withoutRegion(container, REVIEW_QUESTION)),
    ).not.toMatch(CONTROL_VOCABULARY);

    const asked = container.querySelector(REVIEW_QUESTION) as HTMLElement;

    expect(asked).not.toBeNull();
    // The exception is real: the block does use the vocabulary, so the ban
    // above is narrowed around something rather than around nothing.
    expect(spacedText(asked)).toMatch(CONTROL_VOCABULARY);
    // And it uses it as a question. A block that named the candidates without
    // saying they are undecided would have settled the vocabulary in the one
    // place this slice is allowed to speak it.
    expect(spacedText(asked)).toMatch(/is not decided|has not been decided/i);
    expect(spacedText(asked)).toMatch(/not chosen|neither has been given/i);

    // The vocabulary may be spoken in prose, in the block that asks, and
    // nowhere in any form that presents it as a fact about this site. A column
    // heading, a cell, a badge or a label on the drawing would each be this
    // slice answering its own question.
    expect(
      asked.querySelectorAll("table, th, td, .badge, svg, [data-sld-node]"),
    ).toHaveLength(0);
  });

  it("renders no action control, in the declared state either", async () => {
    const { container } = renderConfiguration(DECLARED_SITE);
    await settledScreen();

    expect(container.querySelectorAll(ACTION_SELECTOR)).toHaveLength(0);
    expect(container.querySelectorAll("[disabled]")).toHaveLength(0);
    expect(container.querySelectorAll("[aria-disabled]")).toHaveLength(0);
  });
});

describe("every dense relationship table owns its own overflow", () => {
  it("renders every table through the shared region, with a name", async () => {
    const { container } = renderConfiguration(DECLARED_SITE);
    await settledScreen();

    const tables = Array.from(container.querySelectorAll("table"));

    // Five relationship tables plus the components table. Asserted as a
    // minimum rather than exactly, so adding a declared section does not have
    // to touch this, but not as "more than zero", which would pass on a screen
    // that rendered one.
    expect(tables.length).toBeGreaterThanOrEqual(6);

    for (const table of tables) {
      const region = table.closest(".data-table__scroll");

      // The region is what keeps a wide table from pushing the rail and the
      // workspace bar sideways. A table with nothing between it and the
      // document is the T011B defect, one screen at a time.
      expect(region).not.toBeNull();
      expect((region as HTMLElement).getAttribute("role")).toBe("region");
      expect((region as HTMLElement).getAttribute("tabindex")).toBe("0");

      const labelledBy = table.getAttribute("aria-labelledby") ?? "";
      expect(container.querySelector(`#${labelledBy}`)).not.toBeNull();
    }
  });

  it("keeps every configured column, with no column dropped or collapsed", async () => {
    const { container } = renderConfiguration(DECLARED_SITE);
    await settledScreen();

    // The M1 viewport policy is explicit that a column is never dropped
    // because the viewport is narrow. jsdom has no layout, so what is asserted
    // here is that the columns are rendered at all; the measured evidence that
    // they stay inside their region is `tools/layout-evidence.mjs`.
    expect(tableColumns(container, TOPOLOGY_NODES_ID)).toEqual([
      "Component",
      "Role in topology",
      "Component ID",
      "Node ID",
    ]);
    expect(tableColumns(container, CONNECTIONS_ID)).toEqual([
      "From",
      "To",
      "Carries",
      "Connection ID",
    ]);
    expect(tableColumns(container, DEVICES_ID)).toEqual([
      "Device",
      "Type",
      "Attached to",
      "Signals it can report",
      "Device ID",
    ]);
    expect(tableColumns(container, MAPPINGS_ID)).toEqual([
      "Signal",
      // T016 adds the identity the document binds by. A signal id is unique
      // within its device only, so the row carries the id and the device that
      // declares it, and neither alone would identify the signal.
      "Signal ID",
      "Unit",
      "Reported by",
      "Describes",
      "Mapping ID",
    ]);
    expect(tableColumns(container, ASSUMPTIONS_ID)).toEqual([
      "Assumption",
      "Applies to",
      "Declared by",
      "What it assumes",
    ]);
  });

  it("renders no table with a header row and no rows", async () => {
    const { container } = renderConfiguration(DECLARED_SITE);
    await settledScreen();

    const tables = Array.from(container.querySelectorAll("table"));

    expect(tables.length).toBeGreaterThan(0);
    for (const table of tables) {
      expect(table.querySelectorAll("tbody tr").length).toBeGreaterThan(0);
    }
  });
});

const PHYSICAL_PROPERTIES_ID = "foundation-physical-properties-heading";
const CONTROL_PROPERTIES_ID = "foundation-control-properties-heading";

describe("typed component properties read back as declared configuration", () => {
  it("renders one row per declared property, with its unit and provenance", async () => {
    const { container } = renderConfiguration(DECLARED_SITE);
    await settledScreen();

    expect(tableRows(container, PHYSICAL_PROPERTIES_ID)).toEqual([
      ["PV array", "Tank capacity", "500 L", "This site version 1"],
    ]);
    expect(tableRows(container, CONTROL_PROPERTIES_ID)).toEqual([
      [
        "Battery energy storage",
        "Reserve state of charge",
        "25 %",
        "Template version 2",
      ],
    ]);
  });

  it("puts several properties on one component in several rows", async () => {
    const generator: SiteDetailReadModel = {
      ...DECLARED_SITE,
      foundation: {
        ...DECLARED_SITE.foundation,
        components: DECLARED_SITE.foundation.components.map((component) =>
          component.component_id === "battery"
            ? {
                ...component,
                properties: [
                  {
                    property_key: "specific-fuel-consumption",
                    display_name: "Specific fuel consumption",
                    value: 0.311,
                    unit: "L/kWh",
                    kind: "PHYSICAL",
                    source: "TEMPLATE",
                    source_version: 2,
                  },
                  {
                    property_key: "minimum-runtime",
                    display_name: "Minimum runtime",
                    value: 30,
                    unit: "min",
                    kind: "CONTROL",
                    source: "TEMPLATE",
                    source_version: 2,
                  },
                ],
              }
            : component,
        ),
      },
    };

    const { container } = renderConfiguration(generator);
    await settledScreen();

    // One component, two properties, two kinds, two tables. This is what
    // makes it a property carrier rather than a second rating field.
    expect(tableRows(container, PHYSICAL_PROPERTIES_ID)).toContainEqual([
      "Battery energy storage",
      "Specific fuel consumption",
      "0.311 L/kWh",
      "Template version 2",
    ]);
    expect(tableRows(container, CONTROL_PROPERTIES_ID)).toEqual([
      [
        "Battery energy storage",
        "Minimum runtime",
        "30 min",
        "Template version 2",
      ],
    ]);
  });

  it("states the absence with its reason when the document declares none", async () => {
    // The compatibility case on the screen: a site created before typed
    // properties existed declares none, and the screen says so as a statement
    // about the document rather than about the site.
    const { container } = renderConfiguration(USER_SIMULATED_SITE);
    await settledScreen();

    const text = spacedText(container);
    expect(text).toMatch(/declares no typed physical property on any component/i);
    expect(text).toMatch(/declares no typed control property on any component/i);
    expect(text).toMatch(
      /not a statement that these components have no such properties/i,
    );
  });

  it("says the control properties are not controls, where they are rendered", async () => {
    const { container } = renderConfiguration(DECLARED_SITE);
    await settledScreen();

    expect(spacedText(container)).toMatch(
      /These are declared configuration values, not controls\./i,
    );
    expect(spacedText(container)).toMatch(
      /nothing in this build writes one of these values to a machine/i,
    );
  });

  it("renders a declared physical property as a key parameter", async () => {
    const { container } = renderConfiguration(DECLARED_SITE);
    await settledScreen();

    const terms = Array.from(container.querySelectorAll("dt")).map(
      (term) => term.textContent,
    );

    expect(terms).toContain("PV array tank capacity");
    // The rating is still its own row: a property and a rating are two facts
    // about one component and neither stands for the other.
    expect(terms).toContain("PV array");
  });
});
