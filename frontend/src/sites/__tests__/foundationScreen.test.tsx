import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SiteConfiguration } from "../SiteConfiguration";
import {
  FOUNDATION_SUBTABS,
  FOUNDATION_SUBTABS_LABEL,
} from "../FoundationSubtabs";
import type { SiteDetailClient } from "../siteDirectoryClient";
import type { SiteDetailReadModel } from "../siteReadModel";
import {
  AWAITING_RUNTIME_OR_EVIDENCE,
  SITE_SLD_HEADING,
} from "../SiteSingleLineDiagram";
import {
  COLD_ROOM_TREATMENT_CANDIDATE,
  SLD_UNAVAILABLE_STATEMENTS,
  deriveSiteSldView,
  type SldCandidateTreatment,
} from "../sldViewModel";
import { HYBRID_MINI_GRID_SITE } from "./sldFixtures";
import { settledScreen } from "../../test/settled";
import { spacedText, withoutRegion } from "../../test/text";

/**
 * Canonical screen three, minus the diagram.
 *
 * Two things carry this file, and both are about what is *not* here.
 *
 * `Changes` is absent in every state. v6.9 line 2117 lists it as a Foundation
 * subtab, and lines 2149 and 2225-2228 make it an intervention and
 * change-effect capability rather than the mockup's `Version History`. No
 * configuration-change model exists, and the T008 checkpoint removed that
 * territory rather than leaving it as chrome, so it is not rendered and not
 * labelled in place either.
 *
 * The configured Single Line Diagram was absent here for seven slices, and
 * T016 is the causal step that earns it. What the bans below protected has not
 * gone away, it has moved: the diagram renders inside one named section, and
 * everywhere outside that section the diagram vocabulary is held out exactly
 * as it was. `withoutRegion` is what makes that narrowing checkable, and it
 * throws rather than passing when the section it excepts is not there.
 *
 * The region assertion changed shape rather than being dropped. "No panel body
 * is empty" was written when an empty body could only be a frame kept warm for
 * a diagram that did not exist. The diagram exists, so what still bites is
 * stronger: no panel body and no subsection is empty, and the diagram section
 * holds either a drawing with nodes in it or a refusal with a reason - never a
 * frame with neither.
 */

const SITE: SiteDetailReadModel = {
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
    summary: "Solar-plus-storage mini-grid with a metered distribution load.",
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
        display_name: "Battery",
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
 * The same site with topology, devices, mappings and control assumptions.
 *
 * Every assertion in this file that is about an absence is repeated against
 * this record. That is the point: T013's bans were written on a screen with
 * one table and three stated absences, and a slice that fills the screen with
 * relationship tables is exactly when a ban stops being exercised by the case
 * it was written for.
 */
const DECLARED_SITE: SiteDetailReadModel = {
  ...SITE,
  foundation: {
    ...SITE.foundation,
    topology: {
      nodes: [
        {
          node_id: "pv-array",
          component_id: "pv-array",
          node_role: "GENERATION",
        },
        { node_id: "battery", component_id: "battery", node_role: "STORAGE" },
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
    ],
    signal_mappings: [
      {
        mapping_id: "pv-ac-power",
        device_id: "pv-inverter-controller",
        signal_id: "ac-power",
        component_id: "pv-array",
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
    ],
  },
};

/** A foundation where nothing declares a rating. */
const UNRATED_SITE: SiteDetailReadModel = {
  ...SITE,
  foundation: {
    ...SITE.foundation,
    components: [
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

/** The section that owns the configured diagram. */
const SLD_REGION = "[data-sld-region]";

/** The block inside it that asks what this slice does not answer. */
const REVIEW_QUESTION = "[data-review-question]";

/**
 * Cold-chain vocabulary this build has no record behind.
 *
 * A cold room on a single line is a configured load. It is not a claim that
 * the product knows a temperature, a door state, or whether anything in the
 * room is still good, and there is no field anywhere in this build that could
 * back one.
 */
const COLD_CHAIN_CLAIMS =
  /\b(cold chain status|temperature (?:reading|compliance)|product health|refrigeration performance|door open|setpoint)\b/i;

/** The tables the Topology section renders, by the heading that names each. */
const TOPOLOGY_NODES_ID = "foundation-topology-nodes-heading";
const DEVICES_ID = "foundation-devices-heading";
const MAPPINGS_ID = "foundation-signal-mappings-heading";
const DIAGRAM_CONTENTS_ID = "foundation-diagram-contents-heading";

/** Every row of one named table, as its cell text. */
function tableRows(container: HTMLElement, headingId: string): string[][] {
  const table = container.querySelector(`table[aria-labelledby="${headingId}"]`);

  expect(table, `no table named by ${headingId}`).not.toBeNull();
  return Array.from((table as HTMLElement).querySelectorAll("tbody tr")).map(
    (row) => Array.from(row.querySelectorAll("td")).map((cell) => cell.textContent ?? ""),
  );
}

/** One row of the diagram-contents table, by the node it is about. */
function contentsRow(container: HTMLElement, nodeId: string): string {
  const row = container.querySelector(`[data-sld-row="${nodeId}"]`);

  expect(row, `no diagram-contents row for ${nodeId}`).not.toBeNull();
  return spacedText(row as HTMLElement);
}

/** The compatible diagram for a record, or a failure saying it is not one. */
function drawableDiagram(site: SiteDetailReadModel) {
  const result = deriveSiteSldView(site);

  expect(result.status).toBe("compatible");
  if (result.status !== "compatible") {
    throw new Error(`expected a drawable record, got ${result.status}`);
  }
  return result.diagram;
}

/** v6.9 line 2117, filtered by the T008 checkpoint. Written out, not derived. */
const V69_FOUNDATION_SUBTABS = [
  "Definition",
  "Topology",
  "Controls",
  "Readiness",
];

/** The mockup-derived names T013 replaced. */
const SUPERSEDED_SUBTABS = ["Summary", "Components", "Control Logic", "Settings"];

function clientFor(site: SiteDetailReadModel): SiteDetailClient {
  return { getSite: () => Promise.resolve({ status: "loaded", site }) };
}

function renderFoundation(site: SiteDetailReadModel = SITE) {
  return render(
    <SiteConfiguration siteId={site.site_id} detail={clientFor(site)} />,
  );
}

function subtabRow(): HTMLElement {
  return screen.getByRole("navigation", { name: FOUNDATION_SUBTABS_LABEL });
}

describe("the Foundation subtab row is v6.9's, filtered", () => {
  it("renders Definition, Topology, Controls and Readiness in that order", async () => {
    renderFoundation();
    await settledScreen();

    expect(
      Array.from(subtabRow().querySelectorAll("li")).map(
        (item) => item.textContent,
      ),
    ).toEqual(V69_FOUNDATION_SUBTABS);
    expect(FOUNDATION_SUBTABS.map((subtab) => subtab.label)).toEqual(
      V69_FOUNDATION_SUBTABS,
    );
  });

  it("never renders Changes, in the row or anywhere on the screen", async () => {
    const { container } = renderFoundation();
    await settledScreen();

    expect(
      Array.from(subtabRow().querySelectorAll("li")).map(
        (item) => item.textContent,
      ),
    ).not.toContain("Changes");
    expect(FOUNDATION_SUBTABS.map((subtab) => subtab.label)).not.toContain(
      "Changes",
    );
    // `spacedText`, not `textContent`: the latter glues adjacent elements
    // together, leaving a banned word with no boundary to match against, so
    // this absence would pass without checking anything.
    expect(spacedText(container)).not.toMatch(
      /\b(changes|change history|version history|revision)\b/i,
    );
  });

  it.each(SUPERSEDED_SUBTABS)("does not render %s as a subtab", async (label) => {
    renderFoundation();
    await settledScreen();

    expect(
      Array.from(subtabRow().querySelectorAll("li")).map(
        (item) => item.textContent,
      ),
    ).not.toContain(label);
  });

  it("links the three that have content to sections that exist", async () => {
    const { container } = renderFoundation();
    await settledScreen();

    const links = within(subtabRow()).getAllByRole("link");

    expect(links.map((link) => link.textContent)).toEqual([
      "Definition",
      "Topology",
      "Controls",
    ]);

    // A link to a fragment that resolves to nothing is a destination that does
    // not exist, which is the same lie as a route that renders nothing.
    for (const link of links) {
      const href = link.getAttribute("href") ?? "";

      expect(href.startsWith("#")).toBe(true);
      expect(container.querySelector(href)).not.toBeNull();
      expect(container.querySelector(href)?.textContent).toBe(
        link.textContent,
      );
    }
  });

  it("keeps no unlinked panel between the sections it names", async () => {
    const { container } = renderFoundation();
    await settledScreen();

    // The row names Topology and Controls and does not name the components
    // table. An unnamed panel wedged between two named ones makes the row
    // misleading about where a section ends - and it had a measurable cost:
    // with the table above it, Controls could only be reached by the document
    // clamping at the bottom, so its link landed somewhere different from
    // every other link in the row.
    const headings = Array.from(
      container.querySelectorAll("section.panel h2"),
    ).map((heading) => heading.textContent ?? "");

    const linked = ["Definition", "Topology", "Controls"];
    const positions = linked.map((label) => headings.indexOf(label));

    for (const position of positions) {
      expect(position).toBeGreaterThanOrEqual(0);
    }

    // In row order, and with nothing unnamed between Topology and Controls.
    expect(positions).toEqual([...positions].sort((a, b) => a - b));
    expect(headings.slice(positions[1] + 1, positions[2])).toEqual([]);
  });

  it("does not borrow the Site tab row's treatment", async () => {
    renderFoundation();
    await settledScreen();

    // The Architect's UI/UX ruling: two stacked rows may share vocabulary, but
    // they must not ask a reader to infer two different behaviours from one
    // treatment. The Site tab row swaps what you are looking at; this locates
    // a section on the page you are already on.
    const row = subtabRow();

    expect(row.className).toContain("section-nav");
    expect(row.className).not.toContain("site-tabs");
    expect(row.querySelectorAll(".site-tabs__link, .site-tabs__label")).toHaveLength(
      0,
    );

    // And it carries no active state, because nothing is current when every
    // section is on the page at once.
    expect(row.querySelectorAll('[aria-current]')).toHaveLength(0);
  });

  it("gives Readiness no link, no control, and no section to point at", async () => {
    const { container } = renderFoundation();
    await settledScreen();

    const row = subtabRow();

    expect(
      within(row).queryByRole("link", { name: "Readiness" }),
    ).toBeNull();
    expect(within(row).queryAllByRole("button")).toHaveLength(0);
    expect(
      row.querySelectorAll("[disabled], [aria-disabled], [title], [tabindex]"),
    ).toHaveLength(0);

    // And no empty panel kept warm for it. A heading with nothing under it is
    // the layout form of a fabricated value.
    const headings = Array.from(container.querySelectorAll("h2, h3")).map(
      (heading) => heading.textContent,
    );

    expect(headings).not.toContain("Readiness");
  });
});

describe("the Foundation-under-Foundation heading is gone", () => {
  it("names the content area Definition instead", async () => {
    const { container } = renderFoundation();
    await settledScreen();

    // T011A left this deliberately and named T013 as its owner: a panel headed
    // `Foundation` sitting directly under a page titled `Foundation`.
    const panelHeadings = Array.from(
      container.querySelectorAll("section.panel h2"),
    ).map((heading) => heading.textContent);

    expect(panelHeadings).not.toContain("Foundation");
    expect(panelHeadings).toContain("Definition");
    expect(
      screen.getByRole("heading", { level: 1, name: "Foundation" }),
    ).toBeInTheDocument();
  });

  it("says whose foundation this is", async () => {
    renderFoundation();
    await settledScreen();

    // The page heading stays `Foundation`, which T011A settled. What it gained
    // is a subtitle, because a reader arriving from a bookmark had no way to
    // tell which site's foundation they were looking at.
    expect(
      screen.getByText("Kalangala Mini-Grid · MG-002", { selector: "p" }),
    ).toBeInTheDocument();
  });
});

describe("Key parameters renders only what the foundation declares", () => {
  it("renders a parameter for each rated component and no others", async () => {
    const { container } = renderFoundation();
    await settledScreen();

    const panel = container
      .querySelector("#site-configuration-key-parameters-heading")
      ?.closest("section");

    expect(panel).not.toBeNull();

    const terms = Array.from(
      (panel as HTMLElement).querySelectorAll("dt"),
    ).map((term) => term.textContent);

    // Three components, two rated. The meter declares no rating, so it
    // produces no parameter at all.
    expect(terms).toEqual(["PV array", "Battery"]);
    expect(terms).not.toContain("Site meter");
  });

  it("renders the declared value with the unit the record carries", async () => {
    const { container } = renderFoundation();
    await settledScreen();

    const panel = container
      .querySelector("#site-configuration-key-parameters-heading")
      ?.closest("section") as HTMLElement;

    expect(panel.textContent).toContain("100 kW");
    expect(panel.textContent).toContain("215 kWh");
  });

  it("renders no placeholder, dash, or zero for an undeclared parameter", async () => {
    const { container } = renderFoundation();
    await settledScreen();

    const panel = container
      .querySelector("#site-configuration-key-parameters-heading")
      ?.closest("section") as HTMLElement;

    expect(spacedText(panel)).not.toMatch(/--|—|\bN\/A\b|\bnone\b|\b0\b/i);
  });

  it("renders no panel at all when nothing declares a rating", async () => {
    const { container } = renderFoundation(UNRATED_SITE);
    await settledScreen();

    // An empty card headed `Key parameters` would be chrome claiming content.
    expect(
      container.querySelector("#site-configuration-key-parameters-heading"),
    ).toBeNull();
    // `spacedText`, not `textContent`: the latter glues adjacent elements
    // together, leaving a banned word with no boundary to match against, so
    // this absence would pass without checking anything.
    expect(spacedText(container)).not.toMatch(/Key parameters/);
  });
});

describe("a foundation with no topology gets no drawing and is told why", () => {
  it("draws nothing at all, and says so where the drawing would be", async () => {
    const { container } = renderFoundation();
    await settledScreen();

    // Nothing is drawn: this foundation declares no topology, so there is no
    // arrangement to draw and no part of one either.
    expect(
      container.querySelectorAll("svg, canvas, img, figure, picture"),
    ).toHaveLength(0);
    expect(container.querySelectorAll("[data-sld-node]")).toHaveLength(0);

    // And the reason is the view model's own, stated where the drawing would
    // have been rather than left to be inferred from a blank.
    const region = container.querySelector(SLD_REGION) as HTMLElement;

    expect(region).not.toBeNull();
    expect(region.querySelector("[data-sld-unavailable]")).not.toBeNull();
    expect(spacedText(region)).toContain(
      SLD_UNAVAILABLE_STATEMENTS.NO_TOPOLOGY_DECLARED,
    );
  });

  it("keeps the diagram vocabulary inside the section that owns it", async () => {
    const { container } = renderFoundation();
    await settledScreen();

    // T016 narrowed this ban rather than dropping it. The section that holds
    // the diagram may say `diagram`; the rest of the surface may not, exactly
    // as before. `real power` stays banned everywhere, because the mockup's
    // real-power signal selector is still not built.
    //
    // `spacedText`, not `textContent`: the latter glues adjacent elements
    // together, leaving a banned word with no boundary to match against, so
    // this absence would pass without checking anything.
    expect(spacedText(withoutRegion(container, SLD_REGION))).not.toMatch(
      /\b(single line diagram|one-line|schematic|diagram|signal selector|real power)\b/i,
    );
    expect(spacedText(container)).not.toMatch(/\breal power\b/i);
    expect(
      container.querySelectorAll("select, [role='combobox'], [role='listbox']"),
    ).toHaveLength(0);
  });

  it("keeps no region warm, and none of them is a frame with nothing in it", async () => {
    const { container } = renderFoundation();
    await settledScreen();

    // This assertion used to be "no panel body is empty", which was written
    // when an empty body could only be a region kept warm for a diagram that
    // did not exist. The diagram exists now, so that purpose has expired and
    // the assertion is replaced by a stronger one rather than dropped:
    // subsections are checked too, and the diagram section specifically has to
    // hold either a drawing with nodes in it or a refusal with a reason.
    const regions = [
      ...Array.from(container.querySelectorAll("section.panel .panel__body")),
      ...Array.from(container.querySelectorAll(".subsection")),
    ];

    expect(regions.length).toBeGreaterThan(0);
    for (const region of regions) {
      expect((region.textContent ?? "").trim().length).toBeGreaterThan(0);
    }

    const sld = container.querySelector(SLD_REGION) as HTMLElement;
    const drawn = sld.querySelectorAll("[data-sld-node]").length;
    const refused = sld.querySelectorAll("[data-sld-unavailable]").length;

    // Exactly one of the two, never neither and never both. Neither is the
    // empty frame; both would be a refusal with a drawing under it. Spelled
    // out rather than compared as two booleans, so the failure says which of
    // the four states the screen was in.
    const state = `${drawn > 0 ? "drawing" : "no drawing"}, ${
      refused > 0 ? "refusal" : "no refusal"
    }`;

    expect(state).toMatch(/^(drawing, no refusal|no drawing, refusal)$/);
  });
});

describe("a declared topology the archetype cannot arrange", () => {
  it("draws no part of it, and states which part it choked on", async () => {
    const { container } = renderFoundation(DECLARED_SITE);
    await settledScreen();

    // This record declares three nodes and no bus, so the hybrid mini-grid
    // arrangement does not apply to it. The tempting failure is to draw the
    // three it understood; a partial drawing presented as the site is wrong
    // and looks right, which is worse than no drawing at all.
    expect(
      container.querySelectorAll("svg, canvas, img, figure, picture"),
    ).toHaveLength(0);
    expect(container.querySelectorAll("[data-sld-node]")).toHaveLength(0);

    const region = container.querySelector(SLD_REGION) as HTMLElement;

    expect(spacedText(region)).toContain(
      SLD_UNAVAILABLE_STATEMENTS.BUS_CARDINALITY_UNSUPPORTED,
    );
    // The detail names what in this document produced the refusal. A reason
    // that does not say which part it choked on leaves a reader nothing to act
    // on.
    expect(spacedText(region)).toMatch(/no node in the BUS role/i);

    // Narrowed exactly as above, and still holding everywhere else.
    expect(spacedText(withoutRegion(container, SLD_REGION))).not.toMatch(
      /\b(single line diagram|one-line|schematic|diagram|signal selector|real power)\b/i,
    );
    expect(
      container.querySelectorAll("select, [role='combobox'], [role='listbox']"),
    ).toHaveLength(0);
  });

  it("still renders every device and mapping the document declares", async () => {
    const { container } = renderFoundation(DECLARED_SITE);
    await settledScreen();

    // A diagram incompatibility is a fact about the drawing. It is not
    // evidence that the site has no devices, and a screen that answered one
    // with the other would be making a claim about the site out of a limit of
    // the archetype.
    expect(tableRows(container, DEVICES_ID)).toHaveLength(
      DECLARED_SITE.foundation.devices?.length ?? 0,
    );
    expect(tableRows(container, MAPPINGS_ID)).toHaveLength(
      DECLARED_SITE.foundation.signal_mappings?.length ?? 0,
    );
    expect(tableRows(container, TOPOLOGY_NODES_ID)).toHaveLength(
      DECLARED_SITE.foundation.topology?.nodes.length ?? 0,
    );
  });

  it("offers no way to choose a signal", async () => {
    const { container } = renderFoundation(DECLARED_SITE);
    await settledScreen();

    // Signals are declared and listed. A control that picks one is the signal
    // selector, and it belongs to the slice that has something to show for the
    // signal a reader picked.
    expect(container.querySelectorAll("input, select, [role='radio']")).toHaveLength(
      0,
    );
    expect(spacedText(container)).not.toMatch(/select a signal|choose a signal/i);
  });

  it("keeps no unlinked panel between the sections the row names", async () => {
    const { container } = renderFoundation(DECLARED_SITE);
    await settledScreen();

    // T013's rule, re-asserted against the record that would have broken it.
    // The topology, device and mapping tables are subsections of Topology
    // rather than panels of their own precisely because a panel between
    // Topology and Controls would make the row misleading about where a
    // section ends.
    const headings = Array.from(
      container.querySelectorAll("section.panel h2"),
    ).map((heading) => heading.textContent ?? "");

    const positions = ["Definition", "Topology", "Controls"].map((label) =>
      headings.indexOf(label),
    );

    for (const position of positions) {
      expect(position).toBeGreaterThanOrEqual(0);
    }
    expect(positions).toEqual([...positions].sort((a, b) => a - b));
    expect(headings.slice(positions[1] + 1, positions[2])).toEqual([]);
  });

  it("keeps every subtab link pointing at a section that is still there", async () => {
    const { container } = renderFoundation(DECLARED_SITE);
    await settledScreen();

    const links = within(subtabRow()).getAllByRole("link");

    expect(links).toHaveLength(3);
    for (const link of links) {
      const href = link.getAttribute("href") ?? "";

      expect(href.startsWith("#")).toBe(true);
      expect(container.querySelector(href)).not.toBeNull();
      expect(container.querySelector(href)?.textContent).toBe(link.textContent);
    }
  });

  it("puts the topology content under the section the row names", async () => {
    const { container } = renderFoundation(DECLARED_SITE);
    await settledScreen();

    // The row says Topology locates the topology. If the tables sat in a panel
    // of their own, the link would land somewhere that did not contain them
    // and the row would be telling a reader the wrong thing.
    const panel = container
      .querySelector("#foundation-topology-heading")
      ?.closest("section");

    expect(panel).not.toBeNull();
    for (const headingId of [
      // The diagram is a subsection of Topology and not a panel of its own.
      // T013's rule is that no unlinked panel may sit between the sections the
      // row names, and a panel for the diagram between Topology and Controls
      // would make the row misleading about where Topology ends.
      "foundation-single-line-diagram-heading",
      "foundation-topology-nodes-heading",
      "foundation-topology-connections-heading",
      "foundation-devices-heading",
      "foundation-signal-mappings-heading",
    ]) {
      expect((panel as HTMLElement).querySelector(`#${headingId}`)).not.toBeNull();
    }

    const controls = container
      .querySelector("#foundation-controls-heading")
      ?.closest("section");

    expect(controls).not.toBeNull();
    expect(
      (controls as HTMLElement).querySelector(
        "#foundation-control-assumptions-heading",
      ),
    ).not.toBeNull();
  });

  it("gives Readiness no section, even with the page full of content", async () => {
    const { container } = renderFoundation(DECLARED_SITE);
    await settledScreen();

    const headings = Array.from(container.querySelectorAll("h2, h3")).map(
      (heading) => heading.textContent,
    );

    expect(headings.length).toBeGreaterThan(0);
    expect(headings).not.toContain("Readiness");
    expect(headings).not.toContain("Changes");
  });

  it("keeps every panel body and every subsection non-empty", async () => {
    const { container } = renderFoundation(DECLARED_SITE);
    await settledScreen();

    // Same replacement as above, against the record that fills the screen.
    const regions = [
      ...Array.from(container.querySelectorAll("section.panel .panel__body")),
      ...Array.from(container.querySelectorAll(".subsection")),
    ];

    expect(regions.length).toBeGreaterThan(0);
    for (const region of regions) {
      expect((region.textContent ?? "").trim().length).toBeGreaterThan(0);
    }
  });
});

/**
 * T016 renders the view model T015 built, and nothing else.
 *
 * The first test here is still the anti-vacuity anchor, and it matters more
 * now than it did: if this record stopped being drawable, the assertions below
 * would be about a screen showing a refusal while claiming to be about a
 * screen showing a diagram, and every one of them would pass.
 *
 * What is asserted is agreement rather than appearance. The diagram's labels
 * and the device and signal rows are compared to each other and to the record,
 * from one fixture, so neither can drift without the other. No expected string
 * is written out twice.
 */
describe("the SLD view model reaches the screen, and nothing else does", () => {
  const SLD_PRESENTATION_TOKENS = (site: SiteDetailReadModel): string[] => {
    const result = deriveSiteSldView(site);
    if (result.status !== "compatible") return [];

    const tokens = new Set<string>();
    for (const node of result.diagram.nodes) {
      tokens.add(node.symbol);
      tokens.add(node.visualRole);
    }
    for (const connection of result.diagram.connections) {
      tokens.add(connection.route.stroke);
      tokens.add(connection.route.turn);
    }
    return [...tokens];
  };

  it("draws this record, so the bans below are about a real temptation", () => {
    const result = deriveSiteSldView(HYBRID_MINI_GRID_SITE);

    expect(result.status).toBe("compatible");
    if (result.status !== "compatible") return;
    expect(result.diagram.nodes.length).toBeGreaterThan(0);
    expect(result.diagram.connections.length).toBeGreaterThan(0);
    expect(SLD_PRESENTATION_TOKENS(HYBRID_MINI_GRID_SITE).length).toBeGreaterThan(
      0,
    );
  });

  it("draws it, in one section, with no signal selector anywhere", async () => {
    const { container } = renderFoundation(HYBRID_MINI_GRID_SITE);
    await settledScreen();

    // The inversion. This assertion was `toHaveLength(0)` for seven slices;
    // what it protected has not been dropped, it has been narrowed to one
    // section and made exact. One drawing, inside the section that owns it,
    // and still no raster image, no canvas and no picture anywhere.
    const region = container.querySelector(SLD_REGION) as HTMLElement;

    expect(region).not.toBeNull();
    expect(container.querySelectorAll("svg")).toHaveLength(1);
    expect(region.querySelectorAll("svg")).toHaveLength(1);
    expect(
      container.querySelectorAll("canvas, img, figure, picture, iframe"),
    ).toHaveLength(0);

    // And the vocabulary ban holds everywhere outside that section, including
    // `real power`, which stays banned on the whole screen: the mockup's
    // real-power signal selector is still not built.
    expect(spacedText(withoutRegion(container, SLD_REGION))).not.toMatch(
      /\b(single line diagram|one-line|schematic|diagram|signal selector|real power)\b/i,
    );
    expect(spacedText(container)).not.toMatch(/\breal power\b/i);

    // The signal selector is absent, not disabled. There is still nothing to
    // show for the signal a reader would have picked.
    expect(
      container.querySelectorAll(
        "select, input, datalist, [role='combobox'], [role='listbox'], [role='radio']",
      ),
    ).toHaveLength(0);

    const regions = [
      ...Array.from(container.querySelectorAll("section.panel .panel__body")),
      ...Array.from(container.querySelectorAll(".subsection")),
    ];

    expect(regions.length).toBeGreaterThan(0);
    for (const body of regions) {
      expect((body.textContent ?? "").trim().length).toBeGreaterThan(0);
    }
  });

  it("draws exactly the nodes and connections the view model produces", async () => {
    const { container } = renderFoundation(HYBRID_MINI_GRID_SITE);
    await settledScreen();

    const diagram = drawableDiagram(HYBRID_MINI_GRID_SITE);
    const drawnNodes = Array.from(
      container.querySelectorAll("[data-sld-node]"),
    ).map((node) => node.getAttribute("data-sld-node"));
    const drawnRuns = Array.from(
      container.querySelectorAll("[data-sld-connection]"),
    ).map((run) => run.getAttribute("data-sld-connection"));

    // Exact set equality in both directions. A renderer that dropped one node
    // would be a second topology model with one thing missing; a renderer that
    // added one would be a second topology model with one thing invented.
    expect([...drawnNodes].sort()).toEqual(
      diagram.nodes.map((node) => node.nodeId).sort(),
    );
    expect([...drawnRuns].sort()).toEqual(
      diagram.connections.map((run) => run.connectionId).sort(),
    );
  });

  it("draws component identities the Foundation declares and no others", async () => {
    const { container } = renderFoundation(HYBRID_MINI_GRID_SITE);
    await settledScreen();

    const declared = new Set(
      HYBRID_MINI_GRID_SITE.foundation.components.map(
        (component) => component.component_id,
      ),
    );
    const drawn = Array.from(
      container.querySelectorAll("[data-sld-component]"),
    ).map((node) => node.getAttribute("data-sld-component") ?? "");

    expect(drawn.length).toBeGreaterThan(0);
    for (const componentId of drawn) {
      expect(declared.has(componentId)).toBe(true);
    }

    // Every node the topology positions is drawn, so nothing positioned is
    // quietly left off the picture.
    const positioned = (
      HYBRID_MINI_GRID_SITE.foundation.topology?.nodes ?? []
    ).map((node) => node.component_id);

    expect([...drawn].sort()).toEqual([...positioned].sort());
  });

  it("agrees with the device and signal rows, from one fixture", async () => {
    const { container } = renderFoundation(HYBRID_MINI_GRID_SITE);
    await settledScreen();

    const diagram = drawableDiagram(HYBRID_MINI_GRID_SITE);
    const drawing = container.querySelector("svg") as SVGElement;
    // Reassembled from its `tspan` lines, joined by the space the wrap
    // consumed. `textContent` would glue the lines together and give
    // `Generator fueltank`, which is the same failure `spacedText` exists for,
    // inside one element instead of between two. Reassembling it means a
    // dropped or invented word fails here.
    const drawnLabels = Array.from(
      drawing.querySelectorAll(".sld-node__name"),
    ).map((text) =>
      Array.from(text.querySelectorAll("tspan"))
        .map((line) => line.textContent ?? "")
        .join(" ")
        .trim(),
    );
    const drawnRatings = Array.from(
      drawing.querySelectorAll(".sld-node__rating"),
    ).map((text) => text.textContent ?? "");

    const nodeRows = tableRows(container, TOPOLOGY_NODES_ID).map((row) => row.join(" "));
    const deviceRows = tableRows(container, DEVICES_ID).map((row) => row.join(" "));
    const mappingRows = tableRows(container, MAPPINGS_ID).map((row) => row.join(" "));

    expect(diagram.nodes.length).toBeGreaterThan(0);
    for (const node of diagram.nodes) {
      // The label on the drawing, the row in the diagram's own contents table
      // and the row in the topology table are the same string. Nothing here is
      // an expected literal: they are compared to each other.
      const rating =
        node.rating === null
          ? "No rating declared"
          : `${node.rating.value} ${node.rating.unit}`;
      const row = contentsRow(container, node.nodeId);

      expect(drawnLabels).toContain(node.displayName);
      expect(drawnRatings).toContain(rating);
      expect(row).toContain(node.displayName);
      expect(row).toContain(rating);
      expect(nodeRows.some((entry) => entry.includes(node.displayName))).toBe(true);

      for (const device of node.attachedDevices) {
        expect(row).toContain(device.displayName);
        expect(deviceRows.some((entry) => entry.includes(device.displayName))).toBe(
          true,
        );
      }

      for (const signal of node.availableSignals) {
        // `spacedText` joins text nodes with a space, so a signal rendered as
        // `<name> (<unit>)` across three nodes comes back as `name ( unit )`.
        // Normalised here rather than asserted loosely: a match on the name
        // alone would pass on a row that had lost the unit.
        const flat = row
          .replace(/\s*\(\s*/g, " (")
          .replace(/\s*\)/g, ")");

        expect(flat).toContain(`${signal.signalName} (${signal.unit})`);
        expect(
          mappingRows.some(
            (entry) =>
              entry.includes(signal.signalName) &&
              entry.includes(signal.unit) &&
              entry.includes(signal.mappingId),
          ),
        ).toBe(true);
      }
    }

    // Every declared mapping reaches the drawing's contents exactly once, so a
    // signal cannot be dropped from the diagram while staying in the table.
    const declaredMappings = (
      HYBRID_MINI_GRID_SITE.foundation.signal_mappings ?? []
    ).map((mapping) => mapping.mapping_id);
    const drawnMappings = diagram.nodes.flatMap((node) =>
      node.availableSignals.map((signal) => signal.mappingId),
    );

    expect([...drawnMappings].sort()).toEqual([...declaredMappings].sort());
  });

  it("carries a named, reachable overflow region around the drawing", async () => {
    const { container } = renderFoundation(HYBRID_MINI_GRID_SITE);
    await settledScreen();

    // The archetype has five lanes, so the drawing has an intrinsic width the
    // content column does not always have. The M1 viewport policy is that
    // dense content owns its overflow; a scroller only a mouse can drive hides
    // content from a keyboard, so the region is a focus stop with a name.
    const scroll = container.querySelector(".sld__scroll") as HTMLElement;

    expect(scroll).not.toBeNull();
    expect(scroll.getAttribute("role")).toBe("region");
    expect(scroll.getAttribute("tabindex")).toBe("0");
    expect(
      container.querySelector(`#${scroll.getAttribute("aria-labelledby")}`)
        ?.textContent,
    ).toBe(SITE_SLD_HEADING);

    // The drawing itself is named, because its shapes carry meaning no screen
    // reader can take from them.
    const drawing = scroll.querySelector("svg") as SVGElement;

    expect(drawing.getAttribute("role")).toBe("img");
    for (const id of (drawing.getAttribute("aria-labelledby") ?? "").split(" ")) {
      expect(container.querySelector(`#${id}`)).not.toBeNull();
      expect(
        (container.querySelector(`#${id}`)?.textContent ?? "").trim().length,
      ).toBeGreaterThan(0);
    }
  });

  it("renders one empty slot per drawn node and puts nothing in it", async () => {
    const { container } = renderFoundation(HYBRID_MINI_GRID_SITE);
    await settledScreen();

    const diagram = drawableDiagram(HYBRID_MINI_GRID_SITE);
    const slots = Array.from(container.querySelectorAll(".sld-node__slot")).map(
      (slot) => slot.textContent ?? "",
    );

    expect(slots).toHaveLength(diagram.nodes.length);
    for (const slot of slots) {
      // The whole of what a slot says. Not a value, not a dash, not a zero,
      // not an instant, and not a hyphen standing in for one.
      expect(slot).toBe(AWAITING_RUNTIME_OR_EVIDENCE);
    }

    // And the contents table says the same thing in the same words, once per
    // drawn node, so the two surfaces cannot come to mean different things.
    const slotCells = tableRows(container, DIAGRAM_CONTENTS_ID).map(
      (row) => row[5],
    );

    expect(slotCells).toHaveLength(diagram.nodes.length);
    for (const cell of slotCells) {
      expect(cell).toBe(AWAITING_RUNTIME_OR_EVIDENCE);
    }
  });

  it("puts no digit on the screen the drawn record does not supply", async () => {
    const { container } = renderFoundation(HYBRID_MINI_GRID_SITE);
    await settledScreen();

    // The lattice is measured in pixels and the pixels are attributes, never
    // text. A coordinate that reached a text node would be a number on a
    // diagram that has none.
    const fromRecord = new Set(
      (JSON.stringify(HYBRID_MINI_GRID_SITE).match(/\d+(?:\.\d+)?/g) ?? []),
    );
    const onScreen = (container.textContent ?? "").match(/\d+(?:\.\d+)?/g) ?? [];

    expect(onScreen.length).toBeGreaterThan(0);
    for (const value of onScreen) {
      expect(fromRecord).toContain(value);
    }
  });

  it("puts none of the archetype's own vocabulary on the screen", async () => {
    const { container } = renderFoundation(HYBRID_MINI_GRID_SITE);
    await settledScreen();

    const text = spacedText(container);

    // Symbols, visual roles, strokes and turns are the archetype's, not the
    // document's. A screen showing one of them is a screen rendering the view
    // model, whatever it looks like.
    for (const token of SLD_PRESENTATION_TOKENS(HYBRID_MINI_GRID_SITE)) {
      // `\\b`, not `\b`. Inside a template string `\b` is a backspace
      // character, U+0008, not a word-boundary escape - so this looked for
      // backspaces around the token and could not match anything. It passed
      // on a screen rendering BUSBAR exactly as readily as on one that did
      // not, which is the whole failure: an anti-vacuity anchor that was
      // itself vacuous.
      //
      // The token is escaped too. These strings come from the archetype, and
      // one carrying a regex metacharacter would quietly change what is being
      // searched for.
      const escaped = token.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

      expect(text).not.toMatch(new RegExp(`\\b${escaped}\\b`));
    }
  });

  it("states no incompatible-topology refusal either", async () => {
    const { container } = renderFoundation(HYBRID_MINI_GRID_SITE);
    await settledScreen();

    const text = spacedText(container);

    // The unavailable copy is T016's user-review checkpoint. It has not been
    // in front of the user, so it is not in front of anyone.
    expect(Object.values(SLD_UNAVAILABLE_STATEMENTS).length).toBeGreaterThan(0);
    for (const statement of Object.values(SLD_UNAVAILABLE_STATEMENTS)) {
      expect(text).not.toContain(statement);
    }
    // Not `archetype`: the shipped template's own control assumptions use the
    // word in their declared statements, and banning it would be banning a
    // document's words rather than this slice's vocabulary.
    expect(text).not.toMatch(
      /\b(incompatible|unsupported topology|cannot be drawn|no drawing)\b/i,
    );
  });

  it("renders no runtime value, evidence value, or health term for it", async () => {
    const { container } = renderFoundation(HYBRID_MINI_GRID_SITE);
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

    expect(spacedText(container)).not.toMatch(
      /\b(online|offline|stale|degraded|healthy|watch|needs attention)\b/i,
    );
  });
});


/**
 * A mini-grid whose foundation declares a cold room.
 *
 * The shipped hybrid mini-grid template declares none, so without this record
 * the cold-room proposal could not be looked at - and a review checkpoint
 * about a treatment nobody can see is not a checkpoint. The cold room takes
 * the LOAD role, which is the lane the archetype's own rule puts it in, and
 * that placement is the proposal on offer rather than a decision.
 */
const COLD_ROOM_SITE: SiteDetailReadModel = {
  ...HYBRID_MINI_GRID_SITE,
  foundation: {
    ...HYBRID_MINI_GRID_SITE.foundation,
    components: [
      ...HYBRID_MINI_GRID_SITE.foundation.components,
      {
        component_id: "c-cold-room",
        component_type: "COLD_ROOM",
        display_name: "Cold store",
        rating: { value: 18, unit: "kW" },
        properties: null,
      },
    ],
    topology: {
      nodes: [
        ...(HYBRID_MINI_GRID_SITE.foundation.topology?.nodes ?? []),
        {
          node_id: "n-cold-room",
          component_id: "c-cold-room",
          node_role: "LOAD",
        },
      ],
      connections: [
        ...(HYBRID_MINI_GRID_SITE.foundation.topology?.connections ?? []),
        {
          connection_id: "k-meter-cold-room",
          from_node: "n-meter",
          to_node: "n-cold-room",
          medium: "AC",
        },
      ],
    },
  },
};

/**
 * The M1A checkpoint, rendered.
 *
 * Two semantics were deliberately left undecided across T014 and T015, and
 * this slice presents them rather than answering them. The assertions here are
 * about that presentation: that both questions are on the screen, that both
 * say they are undecided, and that neither is quietly answered somewhere else
 * on the same page.
 */
describe("the screen asks the two questions it does not answer", () => {
  it("asks both, in the section that would answer them", async () => {
    const { container } = renderFoundation(HYBRID_MINI_GRID_SITE);
    await settledScreen();

    const asked = container.querySelector("[data-review-question]") as HTMLElement;

    expect(asked).not.toBeNull();
    expect(container.querySelector(SLD_REGION)?.contains(asked)).toBe(true);

    const text = spacedText(asked);

    expect(text).toMatch(/breaker/i);
    expect(text).toMatch(/cold room/i);
    expect(text).toMatch(/is not decided|has not been decided/i);
  });

  it("claims nothing about cold-chain conditions while asking", async () => {
    const { container } = renderFoundation(COLD_ROOM_SITE);
    await settledScreen();

    // The proposal is a placement and a shape. It is not a claim that this
    // build knows anything about refrigeration, and there is no record behind
    // one if it were.
    expect(
      spacedText(withoutRegion(container, REVIEW_QUESTION)),
    ).not.toMatch(COLD_CHAIN_CLAIMS);

    // The question block is the one place the vocabulary may appear, and it
    // may appear there only as a denial. Strike the denial out and the ban
    // holds inside the block too - which is what stops "we claim nothing
    // about X" from becoming cover for saying X somewhere else in it.
    const asked = container.querySelector(REVIEW_QUESTION) as HTMLElement;
    const claim =
      /It claims nothing about refrigeration performance, temperature, cold-chain compliance or product condition/i;

    expect(spacedText(asked)).toMatch(claim);
    expect(spacedText(asked).replace(claim, "")).not.toMatch(COLD_CHAIN_CLAIMS);
  });

  it("marks the drawn cold room as a proposal rather than settled practice", async () => {
    const { container } = renderFoundation(COLD_ROOM_SITE);
    await settledScreen();

    const drawn = container.querySelector(
      '[data-sld-component="c-cold-room"]',
    ) as HTMLElement;

    expect(drawn).not.toBeNull();
    // The marking travels with the drawing. A shape chosen quietly would have
    // settled how a process asset relates to an electrical single line, which
    // is the decision this checkpoint exists to put in front of someone.
    expect(drawn.getAttribute("data-sld-candidate")).toBe("unsettled");
    expect(spacedText(drawn)).toContain("Cold store");
    expect(spacedText(drawn)).toMatch(/Proposed treatment/i);

    // And the question the archetype carries with the treatment is on screen,
    // next to the drawing, in the view model's own words.
    const asked = container.querySelector("[data-review-question]") as HTMLElement;

    expect(spacedText(asked)).toContain(COLD_ROOM_TREATMENT_CANDIDATE.question);
    expect(spacedText(asked)).toContain("Cold store");
  });

  it("marks nothing else on the drawing as a proposal", async () => {
    const { container } = renderFoundation(COLD_ROOM_SITE);
    await settledScreen();

    const marked = Array.from(
      container.querySelectorAll("[data-sld-candidate]"),
    ).map((node) => node.getAttribute("data-sld-component"));

    // Exactly the one the archetype carries a question for. A screen that
    // marked everything would be saying nothing.
    expect(marked).toEqual(["c-cold-room"]);
  });

  it("says where the proposal can be seen when this site declares no cold room", async () => {
    const { container } = renderFoundation(HYBRID_MINI_GRID_SITE);
    await settledScreen();

    const asked = container.querySelector("[data-review-question]") as HTMLElement;

    // This record declares none, and the question says so rather than
    // describing a shape the reader cannot find on the page in front of them.
    expect(spacedText(asked)).toMatch(/declares no cold room, so none is drawn/i);
    expect(container.querySelectorAll("[data-sld-candidate]")).toHaveLength(0);
  });

  it("cannot mark the proposed treatment settled, even in a test", () => {
    // The claim is enforced by a type, so the type is what is tested. Every
    // runtime assertion in this file would survive `settled` being widened to
    // `boolean` - the values this build produces are still `false` - and what
    // would have changed is the contract: the model would then say a treatment
    // may be marked settled, which is the claim this checkpoint exists to
    // withhold.
    const claimed: SldCandidateTreatment = {
      question: "whatever is proposed",
      // @ts-expect-error `settled` is the literal `false`. Widening it makes
      // this directive unused and `tsc --noEmit` fails on it.
      settled: true,
    };

    expect(claimed.question.length).toBeGreaterThan(0);
  });
});
