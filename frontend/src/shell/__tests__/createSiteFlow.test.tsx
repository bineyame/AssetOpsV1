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
import {
  CREATE_SITE_PATH as GATED_CREATE_SITE_PATH,
  simulatorLabAddSiteEntryPoints,
  simulatorLabCreateSiteEntryPoints,
} from "../simulatorLabRoutes";
import { spacedText } from "../../test/text";

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

/**
 * Walk the flow from the template step to the review step, supplying identity
 * on the way.
 *
 * T010 made the flow stepped, so identity no longer sits on the same screen as
 * the template or the create button. The call sites are unchanged: what a test
 * cares about is that a create was attempted with these values, not which step
 * each field lives on.
 */
async function fillIdentity(overrides: Record<string, string> = {}) {
  const values: Record<string, string> = {
    "Site ID": "MG-002",
    "Display name": "Kalangala Mini-Grid",
    Country: "Uganda",
    Locality: "Kalangala",
    "Time zone": "Africa/Kampala",
    ...overrides,
  };

  // Step 1, the template, to step 2.
  fireEvent.click(screen.getByRole("button", { name: "Next" }));

  for (const [label, value] of Object.entries(values)) {
    fireEvent.change(screen.getByLabelText(label), { target: { value } });
  }

  // Step 2 to step 3, the review, which is where the create button lives.
  fireEvent.click(screen.getByRole("button", { name: "Next" }));
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

    expect(spacedText(main)).toMatch(/copied into the new site/i);
    expect(spacedText(main)).toMatch(
      /changing the template later never changes a site already created from it/i,
    );
    expect(spacedText(main)).toMatch(
      /which template and which template version it came from/i,
    );
  });

  it("states that the created site is a normal site, never published or promoted", async () => {
    renderCreateFlow();
    await screen.findByRole("heading", { level: 1, name: "Create a site" });

    const main = screen.getByRole("main");

    expect(spacedText(main)).toMatch(/normal site in the product/i);
    expect(spacedText(main)).toMatch(
      /stays there when the Simulator Lab is switched off/i,
    );
    expect(spacedText(main)).toMatch(/Nothing is published or promoted/i);
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
  /**
   * Each refusal carries the backend's own code as well as its message,
   * because the code is what places the message against a field. The two
   * duplicate-identity cases name the site ID; the other two name no field,
   * and a screen that guessed one from the message text would be keeping a
   * second copy of the identity rules.
   */
  const refusals = [
    [
      "a site ID already in use",
      "Site ID 'MG-002' is already in use by 'MG-002'. Site IDs are unique across every site store and are compared without regard to case, so the same ID in a different capitalisation is the same site. Nothing was written. Choose a different site ID.",
      "SITE_ID_IN_USE",
    ],
    [
      "a case-variant duplicate",
      "Site ID 'mg-002' is already in use by 'MG-002'. Site IDs are unique across every site store and are compared without regard to case, so the same ID in a different capitalisation is the same site. Nothing was written. Choose a different site ID.",
      "SITE_ID_IN_USE",
    ],
    [
      "a malformed site ID",
      "Site ID 'MG 002' is not a valid site ID. A site ID is 2 to 64 characters using letters, digits, hyphens, and underscores, starting and ending with a letter or a digit, for example MG-002.",
      "SITE_REQUEST_INVALID",
    ],
    [
      "a missing identity field",
      "Display name is required in the create request. Use plain text without control characters; it is stored and shown as text and is never an identifier, a file name, or part of an address.",
      "SITE_REQUEST_INVALID",
    ],
  ] as const;

  it.each(refusals)(
    "shows the reason for %s exactly as given",
    async (_name, message, code) => {
      renderCreateFlow(
        ENABLED,
        creationReturning({ status: "refused", message, code }),
      );
      await screen.findByLabelText("Template");

      await fillIdentity();
      fireEvent.click(screen.getByRole("button", { name: "Create site" }));

      // Verbatim, wherever the code places it. The backend owns this copy and
      // the T006 checkpoint settled it.
      const alert = await screen.findByRole("alert");
      expect(alert).toHaveTextContent(message);
      expect(screen.queryByRole("status")).toBeNull();
    },
  );

  it.each(refusals.filter(([, , code]) => code === "SITE_ID_IN_USE"))(
    "puts %s against the site ID field it concerns",
    async (_name, message, code) => {
      renderCreateFlow(
        ENABLED,
        creationReturning({ status: "refused", message, code }),
      );
      await screen.findByLabelText("Template");

      await fillIdentity();
      fireEvent.click(screen.getByRole("button", { name: "Create site" }));

      // The flow returns to the step that owns the field, and the message is
      // associated with the input rather than floating above the form.
      const siteId = await screen.findByLabelText("Site ID");
      expect(siteId).toHaveAttribute("aria-invalid", "true");

      const described = (siteId.getAttribute("aria-describedby") ?? "")
        .split(" ")
        .map((id) => document.getElementById(id)?.textContent ?? "")
        .join(" ");
      expect(described).toContain(message);
    },
  );

  it("leaves a refusal that names no field where the user is", async () => {
    renderCreateFlow(
      ENABLED,
      creationReturning({
        status: "refused",
        message: "Display name is required in the create request.",
        code: "SITE_REQUEST_INVALID",
      }),
    );
    await screen.findByLabelText("Template");

    await fillIdentity();
    fireEvent.click(screen.getByRole("button", { name: "Create site" }));

    // No field is marked, because the backend named none. A screen that
    // guessed one from the message text would be a second copy of the rules.
    expect(await screen.findByRole("alert")).toHaveTextContent(
      /Display name is required/i,
    );
    expect(screen.queryByLabelText("Site ID")).toBeNull();
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
      creationReturning({
        status: "refused",
        message: "Site ID is in use.",
        code: "SITE_ID_IN_USE",
      }),
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

    // Still an exact allowlist, and still closed. The first three entries are
    // the Lab's own rail, which T009 made a real component and T017 grew by
    // one; each names a surface that renders truthful content. The create flow
    // itself still leads exactly two places and nowhere else, and in
    // particular it does not acquire a way into the scenario catalog.
    expect(links).toEqual([
      ["/simulator-lab", "Simulator Lab"],
      ["/simulator-lab/site-templates", "Site Templates"],
      ["/simulator-lab/scenarios", "Scenarios"],
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

describe("the flow has a step for each stage of real input", () => {
  it("has three steps, and each one takes or shows something real", async () => {
    renderCreateFlow();
    await screen.findByLabelText("Template");

    const steps = within(screen.getByRole("list", { name: "Create a site" }))
      .getAllByRole("listitem")
      .map((step) => step.textContent);

    // Three stages, three steps. No step exists to match a mockup's step
    // count, and none reviews nothing: the template is chosen, identity is
    // supplied, and the review shows what will be created.
    expect(steps).toEqual([
      "Choose a template",
      "Site identity",
      "Review and create",
    ]);
  });

  it("marks where the user is, and moves back as well as forward", async () => {
    renderCreateFlow();
    await screen.findByLabelText("Template");

    function currentStep(): string {
      return (
        within(screen.getByRole("list", { name: "Create a site" }))
          .getAllByRole("listitem")
          .find((step) => step.getAttribute("aria-current") === "step")
          ?.textContent ?? ""
      );
    }

    expect(currentStep()).toBe("Choose a template");

    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    expect(currentStep()).toBe("Site identity");

    fireEvent.click(screen.getByRole("button", { name: "Back" }));
    expect(currentStep()).toBe("Choose a template");

    // Nothing is submitted until the last step, so no step is ever marked
    // complete and going back costs nothing.
    expect(screen.queryByRole("button", { name: "Create site" })).toBeNull();
  });

  it("offers the create button only on the review step", async () => {
    renderCreateFlow();
    await screen.findByLabelText("Template");

    expect(screen.queryByRole("button", { name: "Create site" })).toBeNull();

    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    expect(screen.queryByRole("button", { name: "Create site" })).toBeNull();

    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    expect(
      screen.getByRole("button", { name: "Create site" }),
    ).toBeInTheDocument();
  });

  it("reviews the values supplied, and predicts nothing the backend assigns", async () => {
    renderCreateFlow();
    await screen.findByLabelText("Template");

    await fillIdentity();

    // Scoped to the review itself. The explanation panel above it legitimately
    // says the created site "carries simulated source mode as provenance" -
    // that is T006 copy about what creation does, not a claim about a record.
    const review = screen.getByRole("main").querySelector(".fact-list");
    expect(review).not.toBeNull();
    const reviewed = review?.textContent ?? "";

    expect(reviewed).toContain("MG-002");
    expect(reviewed).toContain("Kalangala Mini-Grid");
    expect(reviewed).toContain("Africa/Kampala");
    expect(reviewed).toContain(TEMPLATE.template_id);

    // Source mode, configuration origin and lifecycle status are assigned by
    // the backend at creation. Reviewing them here would predict a record that
    // does not exist yet.
    expect(reviewed).not.toMatch(/simulated/i);
    expect(reviewed).not.toMatch(/planned/i);
    expect(reviewed).not.toMatch(/\borigin\b/i);
  });
});

describe("two entry points, one flow, one chokepoint", () => {
  it("declares the Lab entry point on the same gated path as the operator one", () => {
    // Both are built by the module that owns the simulator paths. A second
    // path, or a path spelled in a frame, would be the second chokepoint the
    // gate check exists to prevent.
    expect(simulatorLabAddSiteEntryPoints(ENABLED)).toEqual([
      { to: GATED_CREATE_SITE_PATH, label: "+ Add site" },
    ]);
    expect(simulatorLabCreateSiteEntryPoints(ENABLED)[0].to).toBe(
      GATED_CREATE_SITE_PATH,
    );
    expect(simulatorLabAddSiteEntryPoints(DISABLED)).toEqual([]);
  });

  it("does not deny the capability it is offering", async () => {
    render(
      <MemoryRouter initialEntries={["/simulator-lab"]}>
        <App
          flags={ENABLED}
          siteTemplateCatalog={CATALOG}
          siteDirectory={EMPTY_DIRECTORY}
        />
      </MemoryRouter>,
    );

    const main = screen.getByRole("main");

    // The screen offers `+ Add site`, so it must not also say a site cannot be
    // created. It did say exactly that until T010: true when T005 wrote it,
    // false the moment this frame grew an entry point, and invisible to every
    // other test because each was checking its own half.
    expect(screen.getByRole("link", { name: "+ Add site" })).toBeInTheDocument();
    expect(spacedText(main)).not.toMatch(/no site can be created/i);
    expect(spacedText(main)).not.toMatch(/nothing.{0,40}can produce a site/i);

    // The distinction the copy exists for is still made.
    expect(spacedText(main)).toMatch(/a template is not a site/i);
  });

  it("reaches the same create flow from the Lab as from the operator index", async () => {
    render(
      <MemoryRouter initialEntries={["/simulator-lab"]}>
        <App
          flags={ENABLED}
          siteTemplateCatalog={CATALOG}
          siteDirectory={EMPTY_DIRECTORY}
        />
      </MemoryRouter>,
    );

    fireEvent.click(screen.getByRole("link", { name: "+ Add site" }));

    expect(
      await screen.findByRole("heading", { level: 1, name: "Create a site" }),
    ).toBeInTheDocument();
  });
});
