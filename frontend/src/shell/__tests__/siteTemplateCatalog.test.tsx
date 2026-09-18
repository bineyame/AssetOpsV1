import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { App } from "../../App";
import { featureFlagsWith, type FeatureFlags } from "../../config/featureFlags";
import type { SiteDirectoryClient } from "../../sites/siteDirectoryClient";
import type {
  SiteTemplateCatalogClient,
  SiteTemplateDetail,
  SiteTemplateDetailResult,
  SiteTemplateListResult,
} from "../siteTemplateCatalogClient";
import { settledScreen } from "../../test/settled";

/**
 * UI tests for the gated Site Templates surfaces.
 *
 * The catalog is injected, so every assertion is about what the screen renders
 * from a template document rather than about network timing. That is also what
 * makes the value-tracing assertion meaningful: the digits on the screen are
 * compared against the digits in the document under test, so a value that
 * arrived from a mockup rather than from configuration fails here.
 */

const DISABLED = featureFlagsWith(false);
const ENABLED = featureFlagsWith(true);

const TEMPLATES_PATH = "/simulator-lab/site-templates";

const TEMPLATE: SiteTemplateDetail = {
  template_id: "test-archetype",
  template_version: 3,
  display_name: "Test Archetype (40 kW)",
  site_type: "MINIGRID",
  summary: "A template used by tests only.",
  components: [
    {
      component_id: "pv-array",
      component_type: "PV_ARRAY",
      display_name: "PV array",
      rating: { value: 40, unit: "kW" },
    },
    {
      component_id: "site-meter",
      component_type: "METER",
      display_name: "Site meter",
      rating: null,
    },
  ],
};

/**
 * Controls this slice must not offer, enabled or disabled. Nothing here can
 * produce, change, or remove a Site or a template, so a control naming one of
 * these would be a capability claim the product cannot back.
 */
const FORBIDDEN_ACTION_PATTERN =
  /\b(create|instantiate|use this|copy|duplicate|clone|upload|import|edit|save|publish|delete|remove|rename|new site|add site)\b/i;

const INTERACTIVE_SELECTOR = [
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

function catalogWith(
  list: SiteTemplateListResult,
  detail: SiteTemplateDetailResult,
): SiteTemplateCatalogClient {
  return {
    listTemplates: () => Promise.resolve(list),
    getTemplate: () => Promise.resolve(detail),
  };
}

const LOADED_CATALOG = catalogWith(
  { status: "loaded", templates: [TEMPLATE] },
  { status: "loaded", template: TEMPLATE },
);

/** No site exists in these tests: a template must never become one. */
const EMPTY_SITE_DIRECTORY: SiteDirectoryClient = {
  listSites: () => Promise.resolve({ status: "loaded", sites: [] }),
};

function renderAt(
  path: string,
  flags: FeatureFlags = ENABLED,
  catalog: SiteTemplateCatalogClient = LOADED_CATALOG,
) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App
        flags={flags}
        siteTemplateCatalog={catalog}
        siteDirectory={EMPTY_SITE_DIRECTORY}
      />
    </MemoryRouter>,
  );
}

/** Every digit run in a string, so screen values can be traced to a document. */
function digitRuns(text: string): string[] {
  return text.match(/\d+(?:\.\d+)?/g) ?? [];
}

describe("site templates listing", () => {
  it("lists shipped templates by template identity and version", async () => {
    renderAt(TEMPLATES_PATH);

    expect(
      await screen.findByRole("link", { name: TEMPLATE.display_name }),
    ).toHaveAttribute("href", `${TEMPLATES_PATH}/${TEMPLATE.template_id}`);

    // Scoped to the listing. The site type is now also an option in the type
    // filter, which is built from the types the catalog actually contains, so
    // an unscoped query matches twice. The claim is about what the row shows.
    const listing = screen.getByRole("table");
    expect(within(listing).getByText(TEMPLATE.template_id)).toBeInTheDocument();
    expect(
      within(listing).getByText(String(TEMPLATE.template_version)),
    ).toBeInTheDocument();
    expect(within(listing).getByText(TEMPLATE.site_type)).toBeInTheDocument();
  });

  it("states that a template is not a site", async () => {
    renderAt(TEMPLATES_PATH);
    await screen.findByRole("link", { name: TEMPLATE.display_name });

    const main = screen.getByRole("main");
    expect(
      within(main).getByRole("heading", { name: /a template is not a site/i }),
    ).toBeInTheDocument();
    expect(
      within(main).getByText(/no site identity/i),
    ).toBeInTheDocument();
    expect(main.textContent).toMatch(/no lifecycle status/i);
    expect(main.textContent).toMatch(/no location/i);
    expect(main.textContent).toMatch(/no timezone bound to a real place/i);
  });

  it("states an unreadable catalog rather than showing an empty one", async () => {
    renderAt(
      TEMPLATES_PATH,
      ENABLED,
      catalogWith({ status: "unavailable" }, { status: "unavailable" }),
    );

    expect(
      await screen.findByText(/could not be read/i),
    ).toBeInTheDocument();
    expect(screen.getByRole("main").textContent).not.toMatch(
      /ships no site templates/i,
    );
  });

  it("says so plainly when the catalog is readable and empty", async () => {
    renderAt(
      TEMPLATES_PATH,
      ENABLED,
      catalogWith(
        { status: "loaded", templates: [] },
        { status: "not_found" },
      ),
    );

    expect(
      await screen.findByText(/ships no site templates/i),
    ).toBeInTheDocument();
  });
});

describe("site template inspection", () => {
  it("renders the foundation content the template document declares", async () => {
    renderAt(`${TEMPLATES_PATH}/${TEMPLATE.template_id}`);

    expect(
      await screen.findByRole("heading", {
        level: 1,
        name: TEMPLATE.display_name,
      }),
    ).toBeInTheDocument();

    const main = screen.getByRole("main");
    expect(within(main).getByText(TEMPLATE.template_id)).toBeInTheDocument();
    expect(
      within(main).getByText(String(TEMPLATE.template_version)),
    ).toBeInTheDocument();
    expect(within(main).getByText(TEMPLATE.site_type)).toBeInTheDocument();
    expect(within(main).getByText(TEMPLATE.summary)).toBeInTheDocument();

    for (const component of TEMPLATE.components) {
      expect(
        within(main).getByText(component.component_id),
      ).toBeInTheDocument();
      expect(
        within(main).getByText(component.component_type),
      ).toBeInTheDocument();
      expect(
        within(main).getByText(component.display_name),
      ).toBeInTheDocument();
    }

    expect(within(main).getByText("40 kW")).toBeInTheDocument();
    expect(within(main).getByText("Not declared")).toBeInTheDocument();
  });

  it("renders no value that the template document does not supply", async () => {
    renderAt(`${TEMPLATES_PATH}/${TEMPLATE.template_id}`);
    await screen.findByRole("heading", { level: 1, name: TEMPLATE.display_name });

    const fromDocument = new Set(digitRuns(JSON.stringify(TEMPLATE)));
    const onScreen = digitRuns(screen.getByRole("main").textContent ?? "");

    expect(onScreen.length).toBeGreaterThan(0);
    for (const value of onScreen) {
      expect(fromDocument).toContain(value);
    }
  });

  it("states that a template is not a site and has no site identity", async () => {
    renderAt(`${TEMPLATES_PATH}/${TEMPLATE.template_id}`);
    await screen.findByRole("heading", { level: 1, name: TEMPLATE.display_name });

    const main = screen.getByRole("main");
    expect(
      within(main).getByRole("heading", { name: /a template is not a site/i }),
    ).toBeInTheDocument();
    expect(main.textContent).toMatch(
      /template identity never becomes a site identity/i,
    );
    expect(main.textContent).not.toMatch(/\bsite[-_ ]?id\b/i);
    expect(main.textContent).not.toMatch(/MG-?\s*\d/i);
  });

  it("states that declared components are not evidence", async () => {
    renderAt(`${TEMPLATES_PATH}/${TEMPLATE.template_id}`);
    await screen.findByRole("heading", { level: 1, name: TEMPLATE.display_name });

    expect(screen.getByRole("main").textContent).toMatch(
      /no device exists, nothing has reported/i,
    );
  });

  it("reports an unknown template identity as no such template", async () => {
    renderAt(
      `${TEMPLATES_PATH}/absent-archetype`,
      ENABLED,
      catalogWith({ status: "loaded", templates: [] }, { status: "not_found" }),
    );

    expect(
      await screen.findByRole("heading", {
        level: 2,
        name: /no such shipped site template/i,
      }),
    ).toBeInTheDocument();
  });

  it("reports an unreadable catalog rather than an absent template", async () => {
    renderAt(
      `${TEMPLATES_PATH}/${TEMPLATE.template_id}`,
      ENABLED,
      catalogWith({ status: "unavailable" }, { status: "unavailable" }),
    );

    expect(
      await screen.findByRole("heading", {
        level: 2,
        name: /site template unavailable/i,
      }),
    ).toBeInTheDocument();
  });
});

describe("template surfaces offer no capability the product lacks", () => {
  it.each([TEMPLATES_PATH, `${TEMPLATES_PATH}/test-archetype`])(
    "offers no create, instantiate, upload, import, edit, save, publish, delete, or rename control at %s",
    async (path) => {
      const { container } = renderAt(path);
      // The landmark renders while the read is still in flight, so it is not a
      // settle point. These are absence assertions: made against a loading
      // screen they would pass because nothing has rendered yet.
      await settledScreen();

      // Not merely "no enabled control": deferred-by-decision capabilities are
      // absent from the DOM rather than rendered disabled.
      //
      // This counted zero interactive elements, which held while these screens
      // had no controls at all. T010 gives the catalog a search field and a
      // type filter, both of which only narrow what is already listed. So the
      // interactive elements are now named rather than forbidden: anything
      // that is not one of these two still fails, which is stronger than a
      // count because it also fails for a *different* control that happens to
      // keep the total the same.
      const interactive = Array.from(
        container.querySelectorAll(INTERACTIVE_SELECTOR),
      ).map((element) => [
        element.tagName.toLowerCase(),
        element.getAttribute("id"),
      ]);

      expect(interactive).toEqual(
        path === TEMPLATES_PATH
          ? [
              ["input", "site-templates-search"],
              ["select", "site-templates-type"],
            ]
          : [],
      );

      for (const link of Array.from(container.querySelectorAll("a"))) {
        expect(link.textContent ?? "").not.toMatch(FORBIDDEN_ACTION_PATTERN);
        expect(link.getAttribute("href") ?? "").not.toMatch(
          FORBIDDEN_ACTION_PATTERN,
        );
      }
    },
  );

  it.each([TEMPLATES_PATH, `${TEMPLATES_PATH}/test-archetype`])(
    "shows no operational value, source mode, health, analytics, Replay, or Findings at %s",
    async (path) => {
      const { container } = renderAt(path);
      await settledScreen();

      expect(container.querySelectorAll("svg, canvas, img")).toHaveLength(0);
      expect(screen.queryAllByRole("figure")).toHaveLength(0);

      // Labelled fields and column headers are where an operational claim
      // would actually be made. A sentence saying a template has no source is
      // the opposite of such a claim, so the assertion reads the labels the
      // screen renders values against rather than sweeping prose for words.
      const labels = Array.from(
        container.querySelectorAll("dt, th, caption"),
      ).map((element) => (element.textContent ?? "").trim());

      expect(labels.length).toBeGreaterThan(0);
      for (const label of labels) {
        expect(label).not.toMatch(
          /\b(mode|status|health|source|last data|last analysed|evidence|findings?|replay|telemetry|quality)\b/i,
        );
      }
    },
  );

  it.each([TEMPLATES_PATH, `${TEMPLATES_PATH}/test-archetype`])(
    "renders no single line diagram, diagram frame, or signal selector at %s",
    async (path) => {
      const { container } = renderAt(path);
      await settledScreen();

      expect(container.querySelectorAll("svg, canvas")).toHaveLength(0);

      // This banned every `select` and every combobox, as a proxy for the
      // signal selector that sits above a single line diagram. The proxy held
      // while these screens had no controls; it stops being about diagrams the
      // moment a screen has a legitimate filter, and T010 gives the catalog a
      // site-type filter.
      //
      // So the combobox is identified instead of forbidden. A signal selector
      // would be a second combobox, or this one renamed, and either fails.
      const comboboxes = screen.queryAllByRole("combobox");
      expect(comboboxes.map((element) => element.getAttribute("id"))).toEqual(
        path === TEMPLATES_PATH ? ["site-templates-type"] : [],
      );
      expect(
        comboboxes.every(
          (element) => (element.getAttribute("aria-label") ?? "") === "",
        ),
      ).toBe(true);

      // The vocabulary rule is untouched and is what actually names the
      // deferred capability.
      expect(screen.getByRole("main").textContent).not.toMatch(
        /single line diagram|diagram|signal/i,
      );
    },
  );

  it.each([TEMPLATES_PATH, `${TEMPLATES_PATH}/test-archetype`])(
    "renders outside the operator shell at %s",
    async (path) => {
      renderAt(path);
      await settledScreen();

      expect(
        screen.queryByRole("navigation", { name: "Operator routes" }),
      ).toBeNull();
      expect(
        screen.queryByRole("navigation", { name: "Workspace utilities" }),
      ).toBeNull();
    },
  );
});

describe("templates never appear as sites", () => {
  it.each(["/sites", "/site-configuration"])(
    "keeps every template out of the operator route %s when the gate is open",
    async (route) => {
      const { container } = renderAt(route);
      await settledScreen();

      expect(container.textContent).not.toMatch(/template/i);
      expect(container.textContent).not.toMatch(TEMPLATE.display_name);
      expect(container.textContent).not.toMatch(TEMPLATE.template_id);
    },
  );

  it("still renders the first-run empty Sites index when the gate is open", async () => {
    renderAt("/sites");

    expect(
      await screen.findByRole("heading", {
        level: 2,
        name: "No sites configured",
      }),
    ).toBeInTheDocument();
  });

  it.each([TEMPLATES_PATH, `${TEMPLATES_PATH}/test-archetype`])(
    "serves nothing at %s when the gate is closed",
    (path) => {
      renderAt(path, DISABLED);

      expect(
        screen.getByRole("heading", { level: 1, name: "Page not available" }),
      ).toBeInTheDocument();
      expect(screen.getByRole("main").textContent).not.toMatch(/template/i);
    },
  );
});

describe("the catalog filters over the records it actually has", () => {
  /**
   * A second and third template so the filter has something to discriminate.
   * Two MINIGRID, one COLDCHAIN: enough to prove the type filter narrows, and
   * that its options come from the catalog rather than from the site-type
   * enum.
   */
  const COLD_CHAIN: SiteTemplateDetail = {
    ...TEMPLATE,
    template_id: "cold-chain-archetype",
    template_version: 1,
    display_name: "Cold Chain Archetype",
    site_type: "COLDCHAIN",
    summary: "A cold chain template used by tests only.",
  };

  const SECOND_MINIGRID: SiteTemplateDetail = {
    ...TEMPLATE,
    template_id: "mini-grid-large",
    template_version: 2,
    display_name: "Large Mini-Grid",
    summary: "A second mini-grid template used by tests only.",
  };

  const THREE: SiteTemplateCatalogClient = {
    listTemplates: () =>
      Promise.resolve({
        status: "loaded",
        templates: [TEMPLATE, COLD_CHAIN, SECOND_MINIGRID],
      }),
    getTemplate: () => Promise.resolve({ status: "loaded", template: TEMPLATE }),
  };

  function rowNames(): string[] {
    return within(screen.getByRole("table"))
      .getAllByRole("row")
      .slice(1)
      .map((row) => within(row).getAllByRole("cell")[0].textContent ?? "");
  }

  it("offers only the site types the shipped catalog contains", async () => {
    renderAt(TEMPLATES_PATH, ENABLED, THREE);
    await settledScreen();

    const options = within(screen.getByRole("combobox"))
      .getAllByRole("option")
      .map((option) => option.textContent);

    // No PV, no TELECOM, no C&I: a filter value nothing matches would teach a
    // catalog this build does not ship.
    expect(options).toEqual(["All types", "COLDCHAIN", "MINIGRID"]);
  });

  it("offers no filter at all when the catalog ships nothing", async () => {
    renderAt(TEMPLATES_PATH, ENABLED, {
      listTemplates: () => Promise.resolve({ status: "loaded", templates: [] }),
      getTemplate: () => Promise.resolve({ status: "not_found" }),
    });
    await settledScreen();

    // Filtering nothing is not a capability. The empty-state wording the T006
    // checkpoint settled is what the screen says instead.
    expect(screen.queryByRole("combobox")).toBeNull();
    expect(screen.queryByRole("searchbox")).toBeNull();
    expect(
      screen.getByText("This build ships no site templates."),
    ).toBeInTheDocument();
  });

  it("narrows the listing by site type", async () => {
    renderAt(TEMPLATES_PATH, ENABLED, THREE);
    await settledScreen();

    fireEvent.change(screen.getByRole("combobox"), {
      target: { value: "COLDCHAIN" },
    });

    expect(rowNames()).toEqual([COLD_CHAIN.display_name]);
  });

  it("searches over the name and the template identity, not the summary", async () => {
    renderAt(TEMPLATES_PATH, ENABLED, THREE);
    await settledScreen();

    const search = screen.getByRole("searchbox");

    fireEvent.change(search, { target: { value: "large" } });
    expect(rowNames()).toEqual([SECOND_MINIGRID.display_name]);

    // By identity too, because that is how a template is addressed.
    fireEvent.change(search, { target: { value: "cold-chain-archetype" } });
    expect(rowNames()).toEqual([COLD_CHAIN.display_name]);
  });

  it("combines the search and the filter rather than replacing one with the other", async () => {
    renderAt(TEMPLATES_PATH, ENABLED, THREE);
    await settledScreen();

    fireEvent.change(screen.getByRole("combobox"), {
      target: { value: "MINIGRID" },
    });
    fireEvent.change(screen.getByRole("searchbox"), {
      target: { value: "large" },
    });

    expect(rowNames()).toEqual([SECOND_MINIGRID.display_name]);
  });

  it("says an empty result is about the filter, never about what ships", async () => {
    renderAt(TEMPLATES_PATH, ENABLED, THREE);
    await settledScreen();

    fireEvent.change(screen.getByRole("searchbox"), {
      target: { value: "no-such-template" },
    });

    expect(screen.queryByRole("table")).toBeNull();

    // The distinction the catalog has kept since T005: what the build ships
    // and what a filter matched are different facts.
    const main = screen.getByRole("main");
    expect(main.textContent).toMatch(/statement about the filter/i);
    expect(main.textContent).toMatch(/3 templates ship/);
    expect(main.textContent).not.toMatch(
      /This build ships no site templates\./,
    );
  });

  it("renders every column from the template document and nothing else", async () => {
    renderAt(TEMPLATES_PATH, ENABLED, THREE);
    await settledScreen();

    const table = screen.getByRole("table");

    expect(
      within(table)
        .getAllByRole("columnheader")
        .map((header) => header.textContent),
    ).toEqual(["Name", "Template ID", "Version", "Site type", "Summary"]);

    // Every cell traces to a field of the document under test. No last-used,
    // no site count, no status: a template document carries none of those.
    const row = within(table).getAllByRole("row")[1];
    expect(
      within(row)
        .getAllByRole("cell")
        .map((cell) => cell.textContent),
    ).toEqual([
      TEMPLATE.display_name,
      TEMPLATE.template_id,
      String(TEMPLATE.template_version),
      TEMPLATE.site_type,
      TEMPLATE.summary,
    ]);
  });
});
