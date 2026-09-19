import { render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { App } from "../../App";
import { featureFlagsWith, type FeatureFlags } from "../../config/featureFlags";
import type {
  SiteDetailClient,
  SiteDirectoryClient,
} from "../../sites/siteDirectoryClient";
import type {
  SiteDetailReadModel,
  SiteSummary,
} from "../../sites/siteReadModel";
import { settledScreen } from "../../test/settled";
import {
  OPERATOR_SITE_TABS,
  OPERATOR_SITE_TABS_LABEL,
  labelledAspectsSentence,
  type OperatorSiteTab,
} from "../operatorSiteTabs";
import { spacedText } from "../../test/text";

/**
 * The operator Site tab row.
 *
 * Three things are under test, and the third is the one that matters most.
 *
 * 1. The row renders v6.9's operator Site tabs, all eight of them, in order.
 * 2. Overview and Foundation are destinations: links to identified routes that
 *    render truthful surfaces for the site in the address.
 * 3. The other six are labelled in place. Not links, not buttons, not
 *    disabled controls, and with no route behind them. This is the assertion
 *    that stops the row turning into eight tabs where six lead nowhere, which
 *    is the mockup's promise rather than this product's.
 *
 * The inventory is imported rather than restated here, so a label added to the
 * product without being reviewed shows up as a failure in the pinned list
 * below rather than being silently agreed to by a test that derives its
 * expectation from the code under test.
 */

const DISABLED = featureFlagsWith(false);
const ENABLED = featureFlagsWith(true);

/** v6.9 lines 464 and 615, in order. Written out, not derived. */
const V69_OPERATOR_SITE_TABS = [
  "Overview",
  "Foundation",
  "Health",
  "Performance",
  "Findings",
  "Work",
  "Financials",
  "Evidence",
];

/** The two the product can open today. */
const DESTINATION_TABS = ["Overview", "Foundation"];

/** The six that name a real aspect the product cannot show yet. */
const LABELLED_IN_PLACE_TABS = [
  "Health",
  "Performance",
  "Findings",
  "Work",
  "Financials",
  "Evidence",
];

/**
 * The mockup's Site tabs from `ScreenMockups.png` screen 2, which are the
 * Lab's run vocabulary. None of them is an operator Site tab.
 */
const LAB_RUN_TAB_VOCABULARY = [
  "Configuration",
  "Devices",
  "Gateway",
  "Ingestion",
  "Events",
  "Logs",
];

const SITE: SiteSummary = {
  site_id: "MG-002",
  display_name: "Kalangala Mini-Grid",
  site_type: "MINIGRID",
  location: { country: "Uganda", locality: "Kalangala" },
  timezone: "Africa/Kampala",
  lifecycle_status: "PLANNED",
  origin: "USER",
  source: { mode: "SIMULATED" },
  template: { template_id: "hybrid-mini-grid-100kw", template_version: 1 },
};

const SITE_DETAIL: SiteDetailReadModel = {
  ...SITE,
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

function directoryWith(sites: SiteSummary[]): SiteDirectoryClient {
  return { listSites: () => Promise.resolve({ status: "loaded", sites }) };
}

function detailClientFor(sites: SiteDetailReadModel[]): SiteDetailClient {
  return {
    getSite: (siteId: string) => {
      const match = sites.find(
        (site) => site.site_id.toLowerCase() === siteId.toLowerCase(),
      );

      return Promise.resolve(
        match === undefined
          ? { status: "not_found" as const }
          : { status: "loaded" as const, site: match },
      );
    },
  };
}

function renderAt(path: string, flags: FeatureFlags = ENABLED) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App
        flags={flags}
        siteDirectory={directoryWith([SITE])}
        siteDetail={detailClientFor([SITE_DETAIL])}
      />
    </MemoryRouter>,
  );
}

/** The tab row landmark on the surface currently rendered. */
function tabRow(): HTMLElement {
  return screen.getByRole("navigation", { name: OPERATOR_SITE_TABS_LABEL });
}

const SITE_SURFACES = [
  ["the site page", "/sites/MG-002", "Overview"],
  ["the Foundation", "/sites/MG-002/foundation", "Foundation"],
] as const;

describe("the operator Site tab inventory is defined once", () => {
  it("is v6.9's operator Site tab set, in order", () => {
    expect(OPERATOR_SITE_TABS.map((tab) => tab.label)).toEqual(
      V69_OPERATOR_SITE_TABS,
    );
  });

  it("assigns exactly two destinations and six labels", () => {
    expect(
      OPERATOR_SITE_TABS.filter((tab) => tab.kind === "destination").map(
        (tab) => tab.label,
      ),
    ).toEqual(DESTINATION_TABS);
    expect(
      OPERATOR_SITE_TABS.filter((tab) => tab.kind === "labelled_in_place").map(
        (tab) => tab.label,
      ),
    ).toEqual(LABELLED_IN_PLACE_TABS);
  });

  it("carries none of the mockup's Lab run tab vocabulary", () => {
    for (const label of LAB_RUN_TAB_VOCABULARY) {
      expect(OPERATOR_SITE_TABS.map((tab) => tab.label)).not.toContain(label);
    }
  });
});

describe.each(SITE_SURFACES)(
  "the Site tab row on %s",
  (_name, path, currentTab) => {
    it("renders exactly the inventory, in order", async () => {
      renderAt(path);
      await settledScreen();

      const rendered = Array.from(tabRow().querySelectorAll("li")).map(
        (item) => item.textContent,
      );

      expect(rendered).toEqual(V69_OPERATOR_SITE_TABS);
      expect(rendered).toEqual(OPERATOR_SITE_TABS.map((tab) => tab.label));
    });

    it("renders none of the mockup's Lab run tab vocabulary", async () => {
      renderAt(path);
      await settledScreen();

      const row = tabRow();
      for (const label of LAB_RUN_TAB_VOCABULARY) {
        expect(
          within(row).queryByText(label, { exact: true }),
        ).toBeNull();
      }
    });

    it("links Overview and Foundation to this site's own addresses", async () => {
      renderAt(path);
      await settledScreen();

      expect(
        within(tabRow())
          .getAllByRole("link")
          .map((link) => [link.textContent, link.getAttribute("href")]),
      ).toEqual([
        ["Overview", "/sites/MG-002"],
        ["Foundation", "/sites/MG-002/foundation"],
      ]);
    });

    it("marks the tab the reader is on, and only that one", async () => {
      renderAt(path);
      await settledScreen();

      const current = within(tabRow()).getAllByRole("link", { current: "page" });

      expect(current.map((link) => link.textContent)).toEqual([currentTab]);
    });

    it("gives the six labelled tabs no link, button, or control", async () => {
      renderAt(path);
      await settledScreen();

      const row = tabRow();
      const linked = within(row)
        .getAllByRole("link")
        .map((link) => link.textContent);

      for (const label of LABELLED_IN_PLACE_TABS) {
        expect(linked).not.toContain(label);
      }

      expect(
        row.querySelectorAll(
          "button, a[role='button'], [role='button'], [role='tab'], [role='tablist'], input, select",
        ),
      ).toHaveLength(0);
      expect(within(row).queryAllByRole("button")).toHaveLength(0);
    });

    it("gives them no disabled affordance either", async () => {
      renderAt(path);
      await settledScreen();

      // The third state this row refuses. Disabled says the capability exists
      // and is unavailable right now; these are not switched off, they are not
      // built, and the label alone is the honest way to say so.
      const row = tabRow();

      expect(
        row.querySelectorAll(
          "[disabled], [aria-disabled], [title], [tabindex], [onclick]",
        ),
      ).toHaveLength(0);
      expect(spacedText(row)).not.toMatch(
        /\b(coming soon|not yet available|unavailable|disabled|locked)\b/i,
      );
    });

    it("is its own landmark and not the operator rail", async () => {
      renderAt(path);
      await settledScreen();

      const rail = screen.getByRole("navigation", { name: "Operator routes" });

      expect(tabRow()).not.toBe(rail);
      expect(spacedText(rail)).not.toMatch(/foundation/i);
      expect(rail.contains(tabRow())).toBe(false);
    });
  },
);

describe("a labelled tab has no route behind it", () => {
  it.each(LABELLED_IN_PLACE_TABS)("serves nothing under a site at %s", (label) => {
    renderAt(`/sites/MG-002/${label.toLowerCase()}`);

    expect(
      screen.getByRole("heading", { level: 1, name: "Page not available" }),
    ).toBeInTheDocument();
  });
});

describe("the tab row belongs to a site", () => {
  it("does not render for a site that is not configured", async () => {
    renderAt("/sites/MG-404");
    await screen.findByRole("heading", { level: 2, name: "No such site" });

    // The row would otherwise offer tabs to the aspects of a site that does
    // not exist, and its Overview tab would point back at the address that
    // just refused.
    expect(
      screen.queryByRole("navigation", { name: OPERATOR_SITE_TABS_LABEL }),
    ).toBeNull();
  });

  it("does not render on the Sites index", async () => {
    renderAt("/sites");
    await screen.findByRole("table");

    expect(
      screen.queryByRole("navigation", { name: OPERATOR_SITE_TABS_LABEL }),
    ).toBeNull();
  });
});

describe("the tab row is an operator capability and is never gated", () => {
  it.each([
    ["closed", DISABLED],
    ["open", ENABLED],
  ])("renders the same row with the gate %s", async (_name, flags) => {
    renderAt("/sites/MG-002", flags);
    await settledScreen();

    expect(
      Array.from(tabRow().querySelectorAll("li")).map((item) => item.textContent),
    ).toEqual(V69_OPERATOR_SITE_TABS);
  });
});

describe("the row says which aspects it cannot open, and says it in words", () => {
  /**
   * T011A relied on colour alone, and the two colours were about five percent
   * apart: `--text-secondary` for a destination against `--text-muted` for a
   * label. The user read the six as disabled controls, which is the one thing
   * the row exists not to say. T011C adds a second signal that does not depend
   * on seeing a difference between two greys.
   */
  it("counts exactly the tabs it cannot open", async () => {
    renderAt("/sites/MG-002");
    await settledScreen();

    const sentence = within(tabRow()).getByText(/no content in this build yet/);

    // It counts rather than names, because the names are one line above it.
    // What has to stay true is that the count is the number of labelled tabs
    // and not a number somebody typed.
    expect(sentence.textContent).toBe(
      "Six aspects of a Site have no content in this build yet.",
    );
    expect(LABELLED_IN_PLACE_TABS).toHaveLength(6);

    // And the row above still names them, so nothing was lost by shortening
    // the sentence.
    for (const label of LABELLED_IN_PLACE_TABS) {
      expect(within(tabRow()).getByText(label, { exact: true })).toBeInTheDocument();
    }
  });

  it("says nothing about the site it is rendered for", async () => {
    renderAt("/sites/MG-002");
    await settledScreen();

    // `of a Site`, not `of this Site`. No aspect is missing content because of
    // anything about MG-002; the product has no content model for any of them.
    // A sentence that read as a fact about this site would be the wrong claim.
    const sentence = within(tabRow()).getByText(/no content in this build yet/);

    expect(spacedText(sentence)).not.toMatch(/this site/i);
    expect(spacedText(sentence)).not.toMatch(/MG-002|Kalangala/);
  });

  it("separates the two groups with something other than colour", async () => {
    renderAt("/sites/MG-002");
    await settledScreen();

    // The divider hangs off the first labelled tab, so it moves when an aspect
    // becomes a destination rather than being pinned to a count.
    const items = Array.from(tabRow().querySelectorAll("li"));
    const marked = items.filter((item) =>
      item.className.includes("site-tabs__item--group-start"),
    );

    expect(marked).toHaveLength(1);
    expect(marked[0].textContent).toBe(LABELLED_IN_PLACE_TABS[0]);
  });

  it("promises nothing about when the content arrives", async () => {
    renderAt("/sites/MG-002");
    await settledScreen();

    // The sentence describes this build. A sentence about a later one would be
    // a promise nobody has made, and `coming soon` is banned in the guard for
    // the same reason.
    expect(spacedText(tabRow())).not.toMatch(
      /\b(coming soon|soon|shortly|in a future|will be|planned for|roadmap)\b/i,
    );
  });

  it("keeps the labelled tabs out of the tab stops", async () => {
    renderAt("/sites/MG-002");
    await settledScreen();

    // Making them legible must not make them reachable: a focus stop that goes
    // nowhere is the disabled control this row refuses, wearing a keyboard.
    const row = tabRow();

    expect(row.querySelectorAll("[tabindex]")).toHaveLength(0);
    expect(within(row).getAllByRole("link")).toHaveLength(
      DESTINATION_TABS.length,
    );
  });
});

describe("the sentence is derived from the inventory, not written out", () => {
  /**
   * The reason this matters: a written-out list goes stale the first time an
   * aspect gets content, and then the screen says something has no content
   * while the tab beside it opens that content. These pass inventories this
   * product does not have yet.
   */
  const destination: OperatorSiteTab = {
    label: "Overview",
    kind: "destination",
    href: (siteId: string) => `/sites/${siteId}`,
  };

  it("drops an aspect from the sentence when it becomes a destination", () => {
    const before = labelledAspectsSentence([
      destination,
      { label: "Health", kind: "labelled_in_place" },
      { label: "Work", kind: "labelled_in_place" },
    ]);
    const after = labelledAspectsSentence([
      destination,
      { label: "Health", kind: "destination", href: () => "/health" },
      { label: "Work", kind: "labelled_in_place" },
    ]);

    expect(before).toBe(
      "Two aspects of a Site have no content in this build yet.",
    );
    expect(after).toBe("One aspect of a Site has no content in this build yet.");
  });

  it("reads grammatically with one aspect left", () => {
    expect(
      labelledAspectsSentence([
        destination,
        { label: "Evidence", kind: "labelled_in_place" },
      ]),
    ).toBe("One aspect of a Site has no content in this build yet.");
  });

  it("says nothing at all when every aspect has content", () => {
    expect(labelledAspectsSentence([destination])).toBeNull();
    expect(labelledAspectsSentence([])).toBeNull();
  });

  it("matches what the real inventory renders", () => {
    expect(labelledAspectsSentence()).toBe(
      "Six aspects of a Site have no content in this build yet.",
    );
  });
});
