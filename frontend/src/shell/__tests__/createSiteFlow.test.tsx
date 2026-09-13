import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { App } from "../../App";
import { featureFlagsWith, type FeatureFlags } from "../../config/featureFlags";
import type { SiteDirectoryClient } from "../../sites/siteDirectoryClient";
import type { SiteSummary } from "../../sites/siteReadModel";
import type {
  CreateSiteInput,
  CreateSiteResult,
  SiteCreationClient,
} from "../siteCreationClient";
import type {
  SiteTemplateCatalogClient,
  SiteTemplateDetail,
} from "../siteTemplateCatalogClient";

/**
 * UI tests for the gated create-a-site flow.
 *
 * Both clients are injected, so every assertion is about what the screen sends
 * and renders rather than about network timing. The refusal assertions matter
 * most: the backend owns the identity rules and the copy, and this screen must
 * show what it was told rather than paraphrasing it into something friendlier
 * or vaguer.
 */

const DISABLED = featureFlagsWith(false);
const ENABLED = featureFlagsWith(true);

const CREATE_SITE_PATH = "/simulator-lab/create-site";

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
  ],
};

const CREATED_SITE: SiteSummary = {
  site_id: "MG-002",
  display_name: "Kalangala Mini-Grid",
  site_type: "MINIGRID",
  location: { country: "Uganda", locality: "Kalangala" },
  timezone: "Africa/Kampala",
  lifecycle_status: "PLANNED",
  origin: "USER",
  source: { mode: "SIMULATED" },
  template: { template_id: TEMPLATE.template_id, template_version: 3 },
};

const CATALOG: SiteTemplateCatalogClient = {
  listTemplates: () =>
    Promise.resolve({ status: "loaded", templates: [TEMPLATE] }),
  getTemplate: () => Promise.resolve({ status: "loaded", template: TEMPLATE }),
};

const EMPTY_DIRECTORY: SiteDirectoryClient = {
  listSites: () => Promise.resolve({ status: "loaded", sites: [] }),
};

function creationReturning(
  result: CreateSiteResult,
): SiteCreationClient & { calls: CreateSiteInput[] } {
  const calls: CreateSiteInput[] = [];
  return {
    calls,
    createSite: (input: CreateSiteInput) => {
      calls.push(input);
      return Promise.resolve(result);
    },
  };
}

function renderCreateFlow(
  flags: FeatureFlags = ENABLED,
  creation: SiteCreationClient = creationReturning({
    status: "created",
    site: CREATED_SITE,
  }),
  catalog: SiteTemplateCatalogClient = CATALOG,
) {
  return render(
    <MemoryRouter initialEntries={[CREATE_SITE_PATH]}>
      <App
        flags={flags}
        siteTemplateCatalog={catalog}
        siteCreation={creation}
        siteDirectory={EMPTY_DIRECTORY}
      />
    </MemoryRouter>,
  );
}

async function fillIdentity(overrides: Record<string, string> = {}) {
  const values: Record<string, string> = {
    "Site ID": "MG-002",
    "Display name": "Kalangala Mini-Grid",
    Country: "Uganda",
    Locality: "Kalangala",
    "Time zone": "Africa/Kampala",
    ...overrides,
  };

  for (const [label, value] of Object.entries(values)) {
    fireEvent.change(screen.getByLabelText(label), { target: { value } });
  }
}

describe("the create flow is a Simulator Lab surface", () => {
  it("is not served when the gate is closed", () => {
    renderCreateFlow(DISABLED);

    expect(
      screen.getByRole("heading", { level: 1, name: "Page not available" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("main").textContent).not.toMatch(/simulat/i);
    expect(screen.getByRole("main").textContent).not.toMatch(/create a site/i);
  });

  it("offers no form, input, or button when the gate is closed", () => {
    const { container } = renderCreateFlow(DISABLED);

    expect(
      container.querySelectorAll("form, input, select, textarea, button"),
    ).toHaveLength(0);
  });

  it("renders outside the operator shell when the gate is open", async () => {
    renderCreateFlow();
    await screen.findByRole("heading", { level: 1, name: "Create a site" });

    expect(
      screen.queryByRole("navigation", { name: "Operator routes" }),
    ).toBeNull();
    expect(
      screen.queryByRole("navigation", { name: "Workspace utilities" }),
    ).toBeNull();
    expect(screen.getByText("Developer workspace")).toBeInTheDocument();
  });
});

describe("what the create flow states about templates and sites", () => {
  it("states that the site is a copy of the template rather than a link to it", async () => {
    renderCreateFlow();
    await screen.findByRole("heading", { level: 1, name: "Create a site" });

    const main = screen.getByRole("main");

    expect(main.textContent).toMatch(/copied into the new site/i);
    expect(main.textContent).toMatch(
      /changing the template later never changes a site already created from it/i,
    );
    expect(main.textContent).toMatch(
      /which template and which template version it came from/i,
    );
  });

  it("states that the created site is a normal site, never published or promoted", async () => {
    renderCreateFlow();
    await screen.findByRole("heading", { level: 1, name: "Create a site" });

    const main = screen.getByRole("main");

    expect(main.textContent).toMatch(/normal site in the product/i);
    expect(main.textContent).toMatch(
      /stays there when the Simulator Lab is switched off/i,
    );
    expect(main.textContent).toMatch(/Nothing is published or promoted/i);
  });

  it("states that a site ID is permanent and configuration is fixed at creation", async () => {
    renderCreateFlow();
    await screen.findByRole("heading", { level: 1, name: "Create a site" });

    expect(screen.getByRole("main").textContent).toMatch(
      /cannot be edited, renamed, duplicated, or removed afterwards/i,
    );
  });

  it("lists the shipped templates to choose from", async () => {
    renderCreateFlow();

    const templateChoice = (await screen.findByLabelText(
      "Template",
    )) as HTMLSelectElement;

    expect(
      within(templateChoice).getByRole("option", {
        name: TEMPLATE.display_name,
      }),
    ).toBeInTheDocument();
    expect(templateChoice.value).toBe(TEMPLATE.template_id);
  });

  it("states an unreadable catalog rather than an empty form", async () => {
    renderCreateFlow(
      ENABLED,
      creationReturning({ status: "created", site: CREATED_SITE }),
      {
        listTemplates: () => Promise.resolve({ status: "unavailable" }),
        getTemplate: () => Promise.resolve({ status: "unavailable" }),
      },
    );

    expect(await screen.findByText(/could not be read/i)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Create site" })).toBeNull();
  });
});

describe("creating a site", () => {
  it("sends the chosen template and the supplied identity", async () => {
    const creation = creationReturning({
      status: "created",
      site: CREATED_SITE,
    });
    renderCreateFlow(ENABLED, creation);
    await screen.findByLabelText("Template");

    await fillIdentity();
    fireEvent.click(screen.getByRole("button", { name: "Create site" }));

    await waitFor(() => expect(creation.calls).toHaveLength(1));
    expect(creation.calls[0]).toEqual({
      template_id: TEMPLATE.template_id,
      site_id: "MG-002",
      display_name: "Kalangala Mini-Grid",
      location: { country: "Uganda", locality: "Kalangala" },
      timezone: "Africa/Kampala",
    });
  });

  it("sends no origin, source mode, lifecycle status, or foundation", async () => {
    const creation = creationReturning({
      status: "created",
      site: CREATED_SITE,
    });
    renderCreateFlow(ENABLED, creation);
    await screen.findByLabelText("Template");

    await fillIdentity();
    fireEvent.click(screen.getByRole("button", { name: "Create site" }));

    await waitFor(() => expect(creation.calls).toHaveLength(1));
    for (const field of [
      "origin",
      "source",
      "lifecycle_status",
      "foundation",
      "created_in_lab",
      "is_simulator_site",
    ]) {
      expect(Object.keys(creation.calls[0])).not.toContain(field);
    }
  });

  it("confirms the created site by its site ID", async () => {
    renderCreateFlow();
    await screen.findByLabelText("Template");

    await fillIdentity();
    fireEvent.click(screen.getByRole("button", { name: "Create site" }));

    expect(await screen.findByRole("status")).toHaveTextContent(
      /The site MG-002 was created/i,
    );
  });
});

describe("refusals", () => {
  const refusals = [
    [
      "a site ID already in use",
      "Site ID 'MG-002' is already in use by 'MG-002'. Site IDs are unique across every site store and are compared without regard to case, so the same ID in a different capitalisation is the same site. Nothing was written. Choose a different site ID.",
    ],
    [
      "a case-variant duplicate",
      "Site ID 'mg-002' is already in use by 'MG-002'. Site IDs are unique across every site store and are compared without regard to case, so the same ID in a different capitalisation is the same site. Nothing was written. Choose a different site ID.",
    ],
    [
      "a malformed site ID",
      "Site ID 'MG 002' is not a valid site ID. A site ID is 2 to 64 characters using letters, digits, hyphens, and underscores, starting and ending with a letter or a digit, for example MG-002.",
    ],
    [
      "a missing identity field",
      "Display name is required in the create request. Use plain text without control characters; it is stored and shown as text and is never an identifier, a file name, or part of an address.",
    ],
  ] as const;

  it.each(refusals)("shows the reason for %s exactly as given", async (_name, message) => {
    renderCreateFlow(ENABLED, creationReturning({ status: "refused", message }));
    await screen.findByLabelText("Template");

    await fillIdentity();
    fireEvent.click(screen.getByRole("button", { name: "Create site" }));

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent(message);
    expect(screen.queryByRole("status")).toBeNull();
  });

  it("reports an unreachable store without claiming anything was written", async () => {
    renderCreateFlow(ENABLED, creationReturning({ status: "unavailable" }));
    await screen.findByLabelText("Template");

    await fillIdentity();
    fireEvent.click(screen.getByRole("button", { name: "Create site" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      /Nothing was written/i,
    );
  });

  it("keeps what the user typed when a create is refused", async () => {
    renderCreateFlow(
      ENABLED,
      creationReturning({ status: "refused", message: "Site ID is in use." }),
    );
    await screen.findByLabelText("Template");

    await fillIdentity();
    fireEvent.click(screen.getByRole("button", { name: "Create site" }));
    await screen.findByRole("alert");

    expect(screen.getByLabelText("Site ID")).toHaveValue("MG-002");
    expect(screen.getByLabelText("Display name")).toHaveValue(
      "Kalangala Mini-Grid",
    );
  });
});

describe("the create flow offers no capability beyond creating", () => {
  it("exposes no edit, rename, duplicate, delete, publish, or import control", async () => {
    const { container } = renderCreateFlow();
    await screen.findByLabelText("Template");

    const controls = Array.from(
      container.querySelectorAll("button, a[href], [role='button']"),
    ).map((control) => control.textContent ?? "");

    expect(controls.length).toBeGreaterThan(0);
    for (const control of controls) {
      expect(control).not.toMatch(
        /\b(edit|rename|duplicate|clone|delete|remove|publish|promote|import|upload|save)\b/i,
      );
    }
  });

  it("renders no diagram, signal selector, run, evidence, or findings surface", async () => {
    const { container } = renderCreateFlow();
    await screen.findByLabelText("Template");

    expect(container.querySelectorAll("svg, canvas, img, table")).toHaveLength(
      0,
    );
    expect(screen.getByRole("main").textContent).not.toMatch(
      /single line diagram|signal|run |evidence|findings|analytics|replay/i,
    );
  });

  it("renders no value the templates or the created site did not supply", async () => {
    renderCreateFlow();
    await screen.findByLabelText("Template");

    const fromDocuments = new Set(
      (JSON.stringify([TEMPLATE]).match(/\d+(?:\.\d+)?/g) ?? []),
    );
    // The one number the screen states on its own is the site-ID length rule,
    // which is a rule about input rather than a value about a site.
    fromDocuments.add("2");
    fromDocuments.add("64");

    const onScreen =
      screen.getByRole("main").textContent?.match(/\d+(?:\.\d+)?/g) ?? [];

    for (const value of onScreen) {
      expect(fromDocuments).toContain(value);
    }
  });
});

describe("the create flow leads back to the operator index", () => {
  it("links to Sites and to the Simulator Lab, and nowhere else", async () => {
    const { container } = renderCreateFlow();
    await screen.findByLabelText("Template");

    const links = Array.from(container.querySelectorAll("a")).map((link) => [
      link.getAttribute("href"),
      link.textContent,
    ]);

    expect(links).toEqual([
      ["/simulator-lab", "Back to the Simulator Lab"],
      ["/sites", "Go to Sites"],
    ]);
  });

  it("does not pretend to have listed the site itself", async () => {
    const listSites = vi.fn(() =>
      Promise.resolve({ status: "loaded" as const, sites: [] }),
    );
    render(
      <MemoryRouter initialEntries={[CREATE_SITE_PATH]}>
        <App
          flags={ENABLED}
          siteTemplateCatalog={CATALOG}
          siteCreation={creationReturning({
            status: "created",
            site: CREATED_SITE,
          })}
          siteDirectory={{ listSites }}
        />
      </MemoryRouter>,
    );
    await screen.findByLabelText("Template");

    expect(listSites).not.toHaveBeenCalled();
    expect(screen.queryByRole("table")).toBeNull();
  });
});
