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
import { EMPTY_EVIDENCE_CLIENT } from "../../sites/__tests__/evidenceFixtures";
import { settledScreen } from "../../test/settled";
import {
  OPERATOR_SITE_TABS,
  OPERATOR_SITE_TABS_LABEL,
  CANONICAL_OPERATOR_SITE_TABS,
} from "../operatorSiteTabs";
import { spacedText } from "../../test/text";

/**
 * The operator Site tab row, under `D-2026-10-02-rendered-tabs-per-capability`.
 *
 * 1. One canonical inventory lists all eight aspects in v6.9's order; the
 *    RENDERED row is that inventory filtered by capability: Overview,
 *    Foundation, Evidence.
 * 2. Every rendered tab is a destination: a link to an identified route.
 * 3. No tab is labelled in place or disabled. An aspect whose capability does
 *    not exist is not rendered at all and has no route behind it.
 *
 * The expectations are written out, not derived from the code under test.
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

/** What this build renders, in order. */
const RENDERED_TABS = ["Overview", "Foundation", "Evidence"];

/** Canonical aspects with no capability in this build: not rendered. */
const UNRENDERED_TABS = ["Health", "Performance", "Findings", "Work", "Financials"];

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
    site_controls: null,
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
        siteEvidence={EMPTY_EVIDENCE_CLIENT}
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
  ["the Evidence", "/sites/MG-002/evidence", "Evidence"],
] as const;

describe("the operator Site tab inventory is defined once", () => {
  it("keeps all eight canonical aspects in v6.9's order", () => {
    expect(CANONICAL_OPERATOR_SITE_TABS.map((tab) => tab.label)).toEqual(
      V69_OPERATOR_SITE_TABS,
    );
  });

  it("renders exactly the entries whose capability exists", () => {
    expect(OPERATOR_SITE_TABS.map((tab) => tab.label)).toEqual(RENDERED_TABS);
    expect(
      CANONICAL_OPERATOR_SITE_TABS.filter((tab) => !tab.capability).map(
        (tab) => tab.label,
      ),
    ).toEqual(UNRENDERED_TABS);
  });

  it("carries none of the mockup's Lab run tab vocabulary", () => {
    for (const label of LAB_RUN_TAB_VOCABULARY) {
      expect(
        CANONICAL_OPERATOR_SITE_TABS.map((tab) => tab.label),
      ).not.toContain(label);
    }
  });
});

describe.each(SITE_SURFACES)(
  "the Site tab row on %s",
  (_name, path, currentTab) => {
    it("renders exactly Overview, Foundation, Evidence, in order", async () => {
      renderAt(path);
      await settledScreen();

      const rendered = Array.from(tabRow().querySelectorAll("li")).map(
        (item) => item.textContent,
      );

      expect(rendered).toEqual(RENDERED_TABS);
    });

    it("renders none of the mockup's Lab run tab vocabulary", async () => {
      renderAt(path);
      await settledScreen();

      const row = tabRow();
      for (const label of LAB_RUN_TAB_VOCABULARY) {
        expect(within(row).queryByText(label, { exact: true })).toBeNull();
      }
    });

    it("links every rendered tab to this site's own addresses", async () => {
      renderAt(path);
      await settledScreen();

      expect(
        within(tabRow())
          .getAllByRole("link")
          .map((link) => [link.textContent, link.getAttribute("href")]),
      ).toEqual([
        ["Overview", "/sites/MG-002"],
        ["Foundation", "/sites/MG-002/foundation"],
        ["Evidence", "/sites/MG-002/evidence"],
      ]);
    });

    it("marks the tab the reader is on, and only that one", async () => {
      renderAt(path);
      await settledScreen();

      const current = within(tabRow()).getAllByRole("link", { current: "page" });

      expect(current.map((link) => link.textContent)).toEqual([currentTab]);
    });

    it("renders no label-only tab: every list item holds a link", async () => {
      renderAt(path);
      await settledScreen();

      const items = Array.from(tabRow().querySelectorAll("li"));

      expect(items).toHaveLength(RENDERED_TABS.length);
      for (const item of items) {
        expect(item.querySelector("a")).not.toBeNull();
      }

      const linked = within(tabRow())
        .getAllByRole("link")
        .map((link) => link.textContent);
      for (const label of UNRENDERED_TABS) {
        expect(within(tabRow()).queryByText(label)).toBeNull();
        expect(linked).not.toContain(label);
      }
      expect(tabRow().querySelector(".site-tabs__label")).toBeNull();
      expect(tabRow().querySelector(".site-tabs__aspects")).toBeNull();
    });

    it("renders nothing disabled and no control", async () => {
      renderAt(path);
      await settledScreen();

      const row = tabRow();

      expect(
        row.querySelectorAll(
          "button, a[role='button'], [role='button'], [role='tab'], [role='tablist'], input, select",
        ),
      ).toHaveLength(0);
      expect(
        row.querySelectorAll(
          "[disabled], [aria-disabled], [title], [tabindex], [onclick]",
        ),
      ).toHaveLength(0);
      expect(spacedText(row)).not.toMatch(
        /\b(coming soon|not yet available|unavailable|disabled|locked|no content in this build)\b/i,
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

describe("an unrendered aspect has no route behind it", () => {
  it.each(UNRENDERED_TABS)("serves nothing under a site at %s", (label) => {
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

    expect(
      screen.queryByRole("navigation", { name: OPERATOR_SITE_TABS_LABEL }),
    ).toBeNull();
  });

  it("does not render on the Evidence route of a site that is not configured", async () => {
    renderAt("/sites/MG-404/evidence");
    await screen.findByRole("heading", { level: 2, name: "No such site" });

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
    ).toEqual(RENDERED_TABS);
  });
});

describe("the Site Evidence route", () => {
  it("renders Evidence as the current tab with a truthful empty body", async () => {
    renderAt("/sites/MG-002/evidence", DISABLED);
    await settledScreen();

    expect(
      screen.getByRole("heading", { level: 1, name: "Evidence" }),
    ).toBeInTheDocument();
    expect(
      within(tabRow()).getByRole("link", { current: "page" }),
    ).toHaveTextContent("Evidence");
    expect(
      screen.getByText(/No source batch has been accepted for this site/),
    ).toBeInTheDocument();
  });
});

describe("the landing route", () => {
  it("redirects / to the Sites index", async () => {
    renderAt("/");
    await screen.findByRole("table");

    expect(
      screen.getByRole("heading", { level: 1, name: "Sites" }),
    ).toBeInTheDocument();
    expect(
      within(screen.getByRole("navigation", { name: "Operator routes" }))
        .getAllByRole("link")
        .map((link) => link.textContent),
    ).toEqual(["Sites"]);
  });
});
