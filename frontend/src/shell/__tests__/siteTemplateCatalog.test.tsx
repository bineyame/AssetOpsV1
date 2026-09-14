import { render, screen, within } from "@testing-library/react";
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

    const main = screen.getByRole("main");
    expect(within(main).getByText(TEMPLATE.template_id)).toBeInTheDocument();
    expect(
      within(main).getByText(String(TEMPLATE.template_version)),
    ).toBeInTheDocument();
    expect(within(main).getByText(TEMPLATE.site_type)).toBeInTheDocument();
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
      expect(container.querySelectorAll(INTERACTIVE_SELECTOR)).toHaveLength(0);

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
      expect(container.querySelectorAll("select")).toHaveLength(0);
      expect(screen.queryByRole("combobox")).toBeNull();
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
