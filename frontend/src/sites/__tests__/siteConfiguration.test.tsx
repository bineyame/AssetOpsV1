import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SiteConfiguration } from "../SiteConfiguration";
import type { SiteDetailClient } from "../siteDirectoryClient";
import type {
  SiteDetailReadModel,
  SiteDetailResult,
} from "../siteReadModel";
import { deriveSiteConfigurationView } from "../siteViewModel";
import { settledScreen } from "../../test/settled";

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
      },
      {
        component_id: "battery",
        component_type: "BATTERY",
        display_name: "Battery energy storage",
        rating: { value: 215, unit: "kWh" },
      },
      {
        component_id: "site-meter",
        component_type: "METER",
        display_name: "Site meter",
        rating: null,
      },
    ],
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
 * Everything that acts on the site, as opposed to everything interactive.
 *
 * T008 banned every interactive element here, which was right when the surface
 * had no links at all. T013 gives it a subtab row of same-page section links,
 * and a link that scrolls to a heading is not an action on a site. So the ban
 * on acting stays absolute and `a[href]` moves out of it, with every remaining
 * anchor pinned separately to a fragment that resolves.
 */
/** The Foundation subtab labels a container renders, in order. */
function subtabLabels(container: HTMLElement): string[] {
  return Array.from(container.querySelectorAll(".site-tabs__list li")).map(
    (item) => item.textContent ?? "",
  );
}

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
    expect(container.textContent ?? "").toMatch(/half-open/i);
    expect(container.textContent ?? "").toMatch(/has no recorded end/i);

    // And it is not a configuration history, which is a different thing the
    // product does not have.
    expect(container.textContent ?? "").toMatch(/not a configuration history/i);
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
    expect(container.textContent).not.toMatch(/mg-002/);
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
    expect(container.textContent ?? "").toMatch(
      /Configuration is fixed at creation in M1/,
    );
    expect(container.textContent ?? "").toMatch(
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
    expect(container.textContent ?? "").not.toMatch(
      /\b(coming soon|not yet available|will be editable|future release)\b/i,
    );
  });

  it("names no editing workflow anywhere on the screen", async () => {
    const { container } = renderConfiguration(USER_SIMULATED_SITE);
    await settledScreen();

    // `Version History` is the one to watch: the eventual capability in that
    // territory is an auditable intervention record, so this label would name
    // a real future capability by the wrong name.
    expect(container.textContent ?? "").not.toMatch(/version history/i);
    expect(container.textContent ?? "").not.toMatch(/edit configuration/i);
    expect(container.textContent ?? "").not.toMatch(/\brollback\b/i);
    expect(container.textContent ?? "").not.toMatch(/\bapproval\b/i);
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

    expect(container.textContent ?? "").not.toMatch(/simulator/i);
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

describe("what the M1 foundation does not declare is stated, not implied", () => {
  it.each([
    ["Devices", /declares components and nothing below them/i],
    ["Signal mappings", /no mapping can be declared while no device is/i],
    ["Control assumptions", /declares no control assumptions/i],
  ])("states %s as undeclared, with the reason", async (term, reason) => {
    const { container } = renderConfiguration(USER_SIMULATED_SITE);
    await settledScreen();

    expect(factValue(container, term)).toMatch(/^Not declared\./);
    expect(factValue(container, term)).toMatch(reason);
  });

  it("says the absence is about the document, not about the site", async () => {
    const { container } = renderConfiguration(USER_SIMULATED_SITE);
    await settledScreen();

    // "No devices" would be a claim about this site. What is true is narrower:
    // this milestone's configuration document has nowhere to put one.
    expect(factValue(container, "Devices")).toMatch(
      /not a statement that this site has no devices/i,
    );
    expect(container.textContent ?? "").not.toMatch(/\bno devices are configured\b/i);
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

  it("renders no single line diagram, no frame for one, and no signal selector", async () => {
    const { container } = renderConfiguration(USER_SIMULATED_SITE);
    await settledScreen();

    // The layout closes over that space rather than leaving a hole labelled
    // for a future diagram.
    expect(container.textContent ?? "").not.toMatch(
      /single line diagram|one-line diagram|\bdiagram\b|\btopology\b/i,
    );

    const headings = Array.from(
      container.querySelectorAll("h1, h2, h3, h4, h5, h6"),
    ).map((heading) => heading.textContent ?? "");
    for (const heading of headings) {
      expect(heading).not.toMatch(/diagram|signal selector|select a signal/i);
    }

    // `Signal mappings` appears, as a stated absence with its reason. A
    // selector is a control, and there is none: no combobox, no listbox, no
    // select element of any kind.
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

    expect(container.textContent ?? "").not.toMatch(SOURCE_HEALTH_VOCABULARY);
    expect(container.textContent ?? "").not.toMatch(ASSESSMENT_VOCABULARY);
  });

  it("labels a declared rating as declared, never as a measurement", async () => {
    const { container } = renderConfiguration(USER_SIMULATED_SITE);
    await settledScreen();

    const columns = Array.from(container.querySelectorAll("th")).map(
      (column) => column.textContent ?? "",
    );

    expect(columns).toContain("Declared rating");
    expect(container.textContent ?? "").toMatch(
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
    expect(container.textContent).not.toMatch(/Foundation version/i);
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

    expect(container.textContent ?? "").not.toMatch(/MG-002|Kalangala|pv-array/);
    expect(container.querySelectorAll("dl, table")).toHaveLength(0);

    answerSecond({ status: "not_found" });

    expect(
      await screen.findByRole("heading", { level: 2, name: "No such site" }),
    ).toBeInTheDocument();
  });
});
