import { render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { App } from "../../App";
import { featureFlagsWith, type FeatureFlags } from "../../config/featureFlags";
import { OPERATOR_SITE_TABS_LABEL } from "../../shell/operatorSiteTabs";
import type {
  SiteTemplateCatalogClient,
  SiteTemplateDetail,
} from "../../shell/siteTemplateCatalogClient";
import type {
  SiteDetailClient,
  SiteDirectoryClient,
} from "../../sites/siteDirectoryClient";
import type {
  SiteDetailReadModel,
  SiteSummary,
} from "../../sites/siteReadModel";
import { settledScreen } from "../../test/settled";
import { spacedText } from "../../test/text";

/**
 * What T011B can assert in a test, and what it deliberately cannot.
 *
 * jsdom has no layout. Every box is zero by zero, nothing overflows anything,
 * and no scrollbar exists to find. So nothing here claims the page does not
 * scroll sideways - that is browser evidence, and the task says so.
 *
 * What a test can hold is the structure the fix depends on and the inventory
 * the fix must not quietly buy its space with. The region that owns a table's
 * overflow either wraps that table or it does not. The nine Sites index
 * columns and the eight Site tabs are either all there or they are not. Those
 * are the assertions that would catch the two ways this correction could go
 * wrong later: a screen rendering a bare table, or someone making the table
 * fit by dropping a column.
 *
 * The stylesheet half - that the region contains the inline axis, that the
 * frame is full height standalone and not nested, and that nobody hides page
 * overflow instead of containing it - is held by
 * `tools/checks/shell-overflow.ps1`, because those are facts about CSS text
 * rather than about rendered DOM.
 */

const DISABLED = featureFlagsWith(false);
const ENABLED = featureFlagsWith(true);

/** T011's nine columns, written out rather than imported. */
const SITES_INDEX_COLUMNS = [
  "Name",
  "Type",
  "Location",
  "Mode",
  "Lifecycle",
  "Configuration origin",
  "Created from template",
  "Last analysed",
  "Actions",
];

/** T011A's eight tabs, written out rather than imported. */
const OPERATOR_SITE_TABS = [
  "Overview",
  "Foundation",
  "Health",
  "Performance",
  "Findings",
  "Work",
  "Financials",
  "Evidence",
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

const TEMPLATE: SiteTemplateDetail = {
  template_id: "hybrid-mini-grid-100kw",
  template_version: 1,
  display_name: "Hybrid mini-grid, 100 kW",
  site_type: "MINIGRID",
  summary: "Solar-plus-storage mini-grid with a metered distribution load.",
  components: [
    {
      component_id: "pv-array",
      component_type: "PV_ARRAY",
      display_name: "PV array",
      rating: { value: 100, unit: "kW" },
    },
  ],
};

const CATALOG: SiteTemplateCatalogClient = {
  listTemplates: () =>
    Promise.resolve({ status: "loaded", templates: [TEMPLATE] }),
  getTemplate: (templateId: string) =>
    Promise.resolve(
      templateId === TEMPLATE.template_id
        ? { status: "loaded" as const, template: TEMPLATE }
        : { status: "not_found" as const },
    ),
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
        siteTemplateCatalog={CATALOG}
      />
    </MemoryRouter>,
  );
}

/** Every surface in the product that renders a table. */
const SURFACES_WITH_A_TABLE = [
  ["the Sites index", "/sites"],
  ["a site's Foundation", "/sites/MG-002/foundation"],
  ["the Lab template catalog", "/simulator-lab/site-templates"],
] as const;

describe.each(SURFACES_WITH_A_TABLE)(
  "every table on %s owns its overflow",
  (_name, path) => {
    it("sits inside a scroll-owning region", async () => {
      const { container } = renderAt(path);
      await settledScreen();

      const tables = Array.from(container.querySelectorAll("table"));

      expect(tables.length).toBeGreaterThan(0);
      for (const table of tables) {
        expect(table.parentElement).not.toBeNull();
        expect(table.parentElement?.className).toBe("data-table__scroll");
      }
    });

    it("keeps the region reachable by keyboard, and named", async () => {
      const { container } = renderAt(path);
      await settledScreen();

      // A region only a mouse can scroll hides its far side from a keyboard.
      // The name is the heading the table already answers to, so the focus
      // stop announces something rather than an anonymous group.
      for (const table of Array.from(container.querySelectorAll("table"))) {
        const region = table.parentElement;

        expect(region?.getAttribute("tabindex")).toBe("0");
        expect(region?.getAttribute("role")).toBe("region");
        expect(region?.getAttribute("aria-labelledby")).toBe(
          table.getAttribute("aria-labelledby"),
        );
        expect(region?.getAttribute("aria-labelledby")).toBeTruthy();
      }
    });

    it("keeps its table semantics inside the region", async () => {
      const { container } = renderAt(path);
      await settledScreen();

      // The region is a div, and a div between a table and its context is
      // exactly the shape that can break the accessibility tree if it is put
      // in the wrong place. The table is still a table, still named, and still
      // has header cells and body rows.
      const tables = within(container).getAllByRole("table");

      for (const table of tables) {
        expect(table.tagName).toBe("TABLE");
        expect(within(table).getAllByRole("columnheader").length).toBeGreaterThan(0);
        expect(within(table).getAllByRole("row").length).toBeGreaterThan(1);
      }
    });
  },
);

describe("the correction buys no space from the inventories", () => {
  it("leaves the Sites index with all nine columns", async () => {
    renderAt("/sites");
    await screen.findByRole("table");

    // The M1 viewport policy is explicit that a column is never dropped
    // because the viewport is narrow: that would be a fourth state beside not
    // rendered, labelled in place and disabled, and these nine were settled at
    // the T006 user-review checkpoint. Containing the overflow is the layout
    // change; losing a column would have been a product change.
    expect(
      within(screen.getByRole("table"))
        .getAllByRole("columnheader")
        .map((header) => header.textContent),
    ).toEqual(SITES_INDEX_COLUMNS);
  });

  it("leaves the operator Site tab row with all eight labels", async () => {
    renderAt("/sites/MG-002");
    await settledScreen();

    const row = screen.getByRole("navigation", {
      name: OPERATOR_SITE_TABS_LABEL,
    });

    expect(
      Array.from(row.querySelectorAll("li")).map((item) => item.textContent),
    ).toEqual(OPERATOR_SITE_TABS);
  });

  it("puts no tab behind a menu, a toggle, or a disabled control", async () => {
    renderAt("/sites/MG-002");
    await settledScreen();

    // The fit-it-by-hiding-things failure modes the policy names, asserted
    // where they would appear.
    const row = screen.getByRole("navigation", {
      name: OPERATOR_SITE_TABS_LABEL,
    });

    expect(
      row.querySelectorAll(
        "button, select, [role='button'], [role='menu'], [aria-haspopup], [aria-expanded], [hidden]",
      ),
    ).toHaveLength(0);
    expect(spacedText(row)).not.toMatch(/\bmore\b|…|\.\.\./i);
  });
});

describe("the shell keeps its shape in both gate states", () => {
  it.each([
    ["closed", DISABLED],
    ["open", ENABLED],
  ])("renders one frame inside the shell with the gate %s", async (_name, flags) => {
    const { container } = renderAt("/sites", flags);
    await settledScreen();

    // The vertical double-count came from the frame being nested in the shell
    // while both claimed the viewport. The nesting itself is the shape the CSS
    // fix keys on, so it is asserted here; that the override exists is the
    // guard's half.
    const shell = container.querySelector(".app-shell");
    const frames = container.querySelectorAll(".app-frame");

    expect(shell).not.toBeNull();
    expect(frames).toHaveLength(1);
    expect(shell?.contains(frames[0])).toBe(true);
    expect(frames[0].parentElement).toBe(shell);
  });

  it("renders the Lab frame standalone, outside the shell", async () => {
    const { container } = renderAt("/simulator-lab", ENABLED);
    await settledScreen();

    // The other half of the same fix. SimulatorLabShell deliberately sits
    // outside `.app-shell`, which is why `.app-frame` keeps a full-height rule
    // of its own and only the nested case overrides it.
    const frame = container.querySelector(".app-frame");

    expect(frame).not.toBeNull();
    expect(container.querySelector(".app-shell")).toBeNull();
    expect(frame?.closest(".app-shell")).toBeNull();
  });
});
