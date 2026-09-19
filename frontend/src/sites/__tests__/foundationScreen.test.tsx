import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SiteConfiguration } from "../SiteConfiguration";
import {
  FOUNDATION_SUBTABS,
  FOUNDATION_SUBTABS_LABEL,
} from "../FoundationSubtabs";
import type { SiteDetailClient } from "../siteDirectoryClient";
import type { SiteDetailReadModel } from "../siteReadModel";
import { settledScreen } from "../../test/settled";
import { spacedText } from "../../test/text";

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
 * The configured Single Line Diagram is absent, and so is any space kept warm
 * for it. That is causal step 4 and needs topology, ratings and signal
 * mappings validated against an archetype before anything can be drawn. An
 * empty frame labelled for a future diagram is the layout form of a fabricated
 * value, which is why the absence of a *reserved region* is asserted and not
 * only the absence of a diagram.
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
      },
      {
        component_id: "battery",
        component_type: "BATTERY",
        display_name: "Battery",
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
      },
    ],
  },
};

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

describe("the configured diagram is absent, and so is the space for it", () => {
  it("renders no diagram, no diagram heading, and no signal selector", async () => {
    const { container } = renderFoundation();
    await settledScreen();

    expect(
      container.querySelectorAll("svg, canvas, img, figure, picture"),
    ).toHaveLength(0);
    // `spacedText`, not `textContent`: the latter glues adjacent elements
    // together, leaving a banned word with no boundary to match against, so
    // this absence would pass without checking anything.
    expect(spacedText(container)).not.toMatch(
      /\b(single line diagram|one-line|schematic|diagram|signal selector|real power)\b/i,
    );
    expect(
      container.querySelectorAll("select, [role='combobox'], [role='listbox']"),
    ).toHaveLength(0);
  });

  it("keeps no region warm for a diagram that does not exist", async () => {
    const { container } = renderFoundation();
    await settledScreen();

    // Every panel on this screen has content. A panel with an empty body, or
    // one holding only whitespace, would be the reserved region this slice
    // must not leave behind.
    const panels = Array.from(container.querySelectorAll("section.panel"));

    expect(panels.length).toBeGreaterThan(0);
    for (const panel of panels) {
      const body = panel.querySelector(".panel__body");

      expect((body?.textContent ?? "").trim().length).toBeGreaterThan(0);
    }
  });
});
