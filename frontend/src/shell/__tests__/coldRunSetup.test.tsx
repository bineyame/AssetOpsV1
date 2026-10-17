import { act, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import type {
  SiteDetailClient,
  SiteDirectoryClient,
} from "../../sites/siteDirectoryClient";
import type { SiteDetailReadModel } from "../../sites/siteReadModel";
import type {
  FoundationRead,
  FoundationReadModel,
  SiteFoundationClient,
} from "../../sites/siteFoundationClient";
import { settledScreen } from "../../test/settled";
import type {
  ColdScenarioChoice,
  ColdScenarioChoiceClient,
  ColdScenarioChoicesResult,
} from "../coldScenarioChoiceClient";
import type { ScenarioCatalogClient } from "../scenarioCatalogClient";
import type {
  CreateRunResult,
  RunSetupClient,
  RunSetupInput,
} from "../runSetupClient";
import {
  COLD_CHOOSE_SITE_COPY,
  COLD_EMPTY_COPY,
  COLD_UNAVAILABLE_COPY,
} from "../ColdRunSetupFrame";
import { executionMethods } from "./executionFixtures";

/**
 * W2-02: the cold-chain run setup. Site first, then the cold choices for that
 * exact Site; a row writes nothing; Create sends the document's own values.
 */

const ENABLED = featureFlagsWith(true);
const COLD_URL = "/simulator-lab/cold-run-setup";

const BASE_SITE: SiteDetailReadModel = {
  site_id: "MG-001",
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
    valid_from: "2026-09-19T18:36:34Z",
    summary: "Solar-plus-storage mini-grid.",
    components: [],
    topology: null,
    devices: null,
    signal_mappings: null,
    control_assumptions: null,
    site_controls: null,
  },
};
const COLD_SITE = {
  ...BASE_SITE,
  site_id: "COLD-LAB-001",
  display_name: "Cold Lab",
  configuration_store: "POSTGRES",
} as SiteDetailReadModel;
const OTHER_SITE = { ...BASE_SITE, configuration_store: "LEGACY_FILE" } as SiteDetailReadModel;
const COLD_CHOICE_LABEL = "Cold Lab (COLD-LAB-001)";
const OTHER_CHOICE_LABEL = "Kalangala Mini-Grid (MG-001)";

const directory: SiteDirectoryClient = {
  listSites: () =>
    Promise.resolve({ status: "loaded", sites: [COLD_SITE, OTHER_SITE] }),
};
const detail: SiteDetailClient = {
  getSite: (id: string) =>
    Promise.resolve({
      status: "loaded",
      site: id === COLD_SITE.site_id ? COLD_SITE : OTHER_SITE,
    }),
};

const NORMAL: ColdScenarioChoice = {
  scenario_id: "cold-normal",
  scenario_version: 1,
  display_name: "Normal",
  schema: "cold-scenario/1",
  model_profile: "cold-thermal/1",
  publication_profile: "cold-publication/1",
  observation_profile: "cold-observation/1",
  start: "2026-10-01T00:00:00Z",
  end: "2026-10-01T06:00:00Z",
  seed: 4242,
};
const EXCURSION: ColdScenarioChoice = {
  ...NORMAL,
  scenario_id: "cold-excursion",
  display_name: "Excursion",
  seed: 7,
};

function loaded(siteId: string, scenarios: ColdScenarioChoice[]): ColdScenarioChoicesResult {
  return { status: "loaded", siteId, scenarios };
}

/** Answers by Site, like the backend: the choices for COLD-LAB-001 only. */
function coldClient(
  answers: (siteId: string, call: number) => Promise<ColdScenarioChoicesResult> = (siteId) =>
    Promise.resolve(
      loaded(siteId, siteId === COLD_SITE.site_id ? [EXCURSION, NORMAL] : []),
    ),
): { client: ColdScenarioChoiceClient; calls: string[] } {
  const calls: string[] = [];
  return {
    calls,
    client: {
      listColdScenarios: (siteId: string) => {
        calls.push(siteId);
        return answers(siteId, calls.length);
      },
    },
  };
}

function foundationModel(): FoundationReadModel {
  return {
    revision: { version: 5, valid_from: "2026-09-01T00:00:00Z", valid_to: null },
    bindings: {
      binding_set: { version: 2, valid_from: "2026-09-01T00:00:00Z", valid_to: null },
    },
    acquisition_snapshot: {
      available: true,
      sha256: "c".repeat(64),
      schema: "assetops.acquisition-snapshot/1",
    },
  } as unknown as FoundationReadModel;
}

function foundationClient() {
  const reads: [string, string | null][] = [];
  const client = {
    getFoundation: (siteId: string, at: string | null) => {
      reads.push([siteId, at]);
      return Promise.resolve<FoundationRead<FoundationReadModel>>({
        status: "loaded",
        value: foundationModel(),
      });
    },
  } as unknown as SiteFoundationClient;
  return { client, reads };
}

const REFUSED: CreateRunResult = {
  status: "refused",
  code: "RUN_SETUP_REFUSED",
  refusalKind: null,
  message: "The request was refused.",
};

function runClient(outcome: CreateRunResult = REFUSED) {
  const calls: RunSetupInput[] = [];
  const client: RunSetupClient = {
    listProfiles: () =>
      Promise.resolve({ status: "loaded", modelProfiles: [], publicationProfiles: [] }),
    createRun: (input: RunSetupInput) => {
      calls.push(input);
      return Promise.resolve(outcome);
    },
    listRuns: () => Promise.resolve({ status: "loaded", runs: [] }),
    getRun: () => Promise.resolve({ status: "not_found" }),
    ...executionMethods(),
  };
  return { client, calls };
}

function renderAt(
  url: string,
  cold: ColdScenarioChoiceClient,
  runSetup: RunSetupClient = runClient().client,
  foundation: SiteFoundationClient = foundationClient().client,
  catalog?: ScenarioCatalogClient,
) {
  return render(
    <MemoryRouter initialEntries={[url]}>
      <App
        flags={ENABLED}
        siteDirectory={directory}
        siteDetail={detail}
        siteTemplateLineage={{
          listLineage: () => Promise.resolve({ status: "loaded", sites: [] }),
        }}
        runSetup={runSetup}
        siteFoundation={foundation}
        coldScenarios={cold}
        {...(catalog === undefined ? {} : { scenarioCatalog: catalog })}
      />
    </MemoryRouter>,
  );
}

function createButton(): HTMLButtonElement {
  return screen.getByRole("button", { name: "Create draft run" }) as HTMLButtonElement;
}

function chooseSite(label: string): void {
  fireEvent.click(screen.getByRole("radio", { name: label }));
}

function choiceRows(): string[] {
  return Array.from(document.querySelectorAll("[data-cold-choice-row]")).map(
    (row) => row.getAttribute("data-cold-choice-row") ?? "",
  );
}

describe("cold run setup (W2-02)", () => {
  it("asks for a Site first, reads nothing, and keeps Create disabled", async () => {
    const cold = coldClient();
    renderAt(COLD_URL, cold.client);
    await settledScreen();

    expect(
      document.querySelector('[data-cold-choice-state="choose-site"]')?.textContent,
    ).toBe(COLD_CHOOSE_SITE_COPY);
    expect(cold.calls).toEqual([]);
    expect(createButton().disabled).toBe(true);
  });

  it("renders only the choices returned for the selected Site", async () => {
    const cold = coldClient();
    renderAt(COLD_URL, cold.client);
    await settledScreen();

    chooseSite(COLD_CHOICE_LABEL);
    await settledScreen();

    expect(cold.calls).toEqual(["COLD-LAB-001"]);
    expect(choiceRows()).toEqual(["cold-excursion", "cold-normal"]);
    expect(screen.getByRole("radio", { name: "Normal" })).toBeInTheDocument();
  });

  it("states the empty copy for a Site with no cold scenarios and keeps Create disabled", async () => {
    const cold = coldClient();
    renderAt(COLD_URL, cold.client);
    await settledScreen();

    chooseSite(OTHER_CHOICE_LABEL);
    await settledScreen();

    expect(cold.calls).toEqual(["MG-001"]);
    expect(
      document.querySelector('[data-cold-choice-state="empty"]')?.textContent,
    ).toBe(COLD_EMPTY_COPY);
    expect(choiceRows()).toEqual([]);
    expect(createButton().disabled).toBe(true);
  });

  it("states the unavailable copy, never the empty claim, and Retry keeps the Site", async () => {
    const cold = coldClient((siteId, call) =>
      Promise.resolve(
        call === 1 ? { status: "unavailable" } : loaded(siteId, [NORMAL]),
      ),
    );
    renderAt(COLD_URL, cold.client);
    await settledScreen();

    chooseSite(COLD_CHOICE_LABEL);
    await settledScreen();

    expect(
      document.querySelector('[data-cold-choice-state="unavailable"]')?.textContent,
    ).toBe(COLD_UNAVAILABLE_COPY);
    expect(document.querySelector('[data-cold-choice-state="empty"]')).toBeNull();
    expect(createButton().disabled).toBe(true);

    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    await settledScreen();

    expect(cold.calls).toEqual(["COLD-LAB-001", "COLD-LAB-001"]);
    expect(
      (screen.getByRole("radio", { name: COLD_CHOICE_LABEL }) as HTMLInputElement).checked,
    ).toBe(true);
    expect(choiceRows()).toEqual(["cold-normal"]);
    expect(document.querySelector('[data-cold-choice-state="unavailable"]')).toBeNull();
  });

  it("states each setup message exactly once", async () => {
    const once = (text: string) => expect(screen.getAllByText(text)).toHaveLength(1);

    const first = renderAt(COLD_URL, coldClient().client);
    await settledScreen();
    once(COLD_CHOOSE_SITE_COPY);
    chooseSite(OTHER_CHOICE_LABEL);
    await settledScreen();
    once(COLD_EMPTY_COPY);
    expect(createButton().disabled).toBe(true);
    first.unmount();

    const second = renderAt(
      COLD_URL,
      coldClient(() => Promise.resolve({ status: "unavailable" })).client,
    );
    await settledScreen();
    chooseSite(COLD_CHOICE_LABEL);
    await settledScreen();
    once(COLD_UNAVAILABLE_COPY);
    expect(createButton().disabled).toBe(true);
    second.unmount();

    const pending = {
      getFoundation: () => new Promise<FoundationRead<FoundationReadModel>>(() => {}),
    } as unknown as SiteFoundationClient;
    renderAt(COLD_URL, coldClient().client, runClient().client, pending);
    await settledScreen();
    chooseSite(COLD_CHOICE_LABEL);
    await settledScreen();
    fireEvent.click(screen.getByRole("radio", { name: "Normal" }));
    // The basis read is held pending on purpose, so this asserts the loading state itself.
    await screen.findByText("Loading the registered configuration for the scenario start.");
    once("Loading the registered configuration for the scenario start.");
    const fact = screen.getByText("Foundation version").nextElementSibling;
    expect(fact?.textContent).toBe("Not available");
    expect(createButton().disabled).toBe(true);
  });

  it("ignores an older response for a prior Site", async () => {
    let resolveCold: (value: ColdScenarioChoicesResult) => void = () => {};
    const cold = coldClient((siteId) =>
      siteId === COLD_SITE.site_id
        ? new Promise((resolve) => {
            resolveCold = resolve;
          })
        : Promise.resolve(loaded(siteId, [])),
    );
    renderAt(COLD_URL, cold.client);
    await settledScreen();

    chooseSite(COLD_CHOICE_LABEL);
    chooseSite(OTHER_CHOICE_LABEL);
    await settledScreen();
    expect(
      document.querySelector('[data-cold-choice-state="empty"]')?.textContent,
    ).toBe(COLD_EMPTY_COPY);

    // The cold Site's answer arrives late, after the Site changed.
    await act(async () => {
      resolveCold(loaded("COLD-LAB-001", [NORMAL]));
      await Promise.resolve();
    });

    expect(choiceRows()).toEqual([]);
    expect(
      document.querySelector('[data-cold-choice-state="empty"]')?.textContent,
    ).toBe(COLD_EMPTY_COPY);
    expect(cold.calls).toEqual(["COLD-LAB-001", "MG-001"]);
  });

  it("shows the chosen row's facts and basis without writing", async () => {
    const run = runClient();
    const foundation = foundationClient();
    renderAt(COLD_URL, coldClient().client, run.client, foundation.client);
    await settledScreen();
    chooseSite(COLD_CHOICE_LABEL);
    await settledScreen();

    fireEvent.click(screen.getByRole("radio", { name: "Normal" }));
    await settledScreen();

    expect(run.calls).toEqual([]);
    expect(foundation.reads).toEqual([["COLD-LAB-001", "2026-10-01T00:00:00Z"]]);
    for (const text of [
      "2026-10-01T00:00:00Z",
      "2026-10-01T06:00:00Z",
      "4242",
      "1 minute",
      "cold-thermal/1",
      "cold-publication/1",
      "cold-observation/1",
      "c".repeat(64),
    ]) {
      expect(screen.getByText(text)).toBeInTheDocument();
    }
    expect(document.querySelector("[data-setup-registered-basis]")).not.toBeNull();
    expect(createButton().disabled).toBe(false);
  });

  it("Create draft run sends exactly the chosen document's request", async () => {
    const run = runClient();
    renderAt(COLD_URL, coldClient().client, run.client);
    await settledScreen();
    chooseSite(COLD_CHOICE_LABEL);
    await settledScreen();
    fireEvent.click(screen.getByRole("radio", { name: "Normal" }));
    await settledScreen();

    fireEvent.click(createButton());
    await screen.findByRole("alert");

    expect(run.calls).toEqual([
      {
        site_id: "COLD-LAB-001",
        foundation_version: 5,
        scenario_id: "cold-normal",
        scenario_version: 1,
        interval: {
          start_time: "2026-10-01T00:00:00Z",
          end_time: "2026-10-01T06:00:00Z",
        },
        timestep_minutes: 1,
        seed: 4242,
        model_profile: { profile_id: "cold-thermal", profile_version: 1 },
        publication_profile: { profile_id: "cold-publication", profile_version: 1 },
        run_inputs: [],
      },
    ]);
    expect(screen.getByRole("alert").textContent).toMatch(
      /The request was refused\. No draft run was created/,
    );
  });

  it("clears the selection and result when the Site changes", async () => {
    const run = runClient();
    renderAt(COLD_URL, coldClient().client, run.client);
    await settledScreen();
    chooseSite(COLD_CHOICE_LABEL);
    await settledScreen();
    fireEvent.click(screen.getByRole("radio", { name: "Normal" }));
    await settledScreen();
    fireEvent.click(createButton());
    await screen.findByRole("alert");

    chooseSite(OTHER_CHOICE_LABEL);
    await settledScreen();

    expect(screen.queryByRole("alert")).toBeNull();
    expect(screen.queryByText("cold-thermal/1")).toBeNull();
    expect(createButton().disabled).toBe(true);
  });

  it("leaves the legacy run setup route on the legacy screen", async () => {
    const cold = coldClient();
    const catalog: ScenarioCatalogClient = {
      listScenarios: () => Promise.resolve({ status: "loaded", scenarios: [] }),
      getScenario: () => Promise.resolve({ status: "not_found" }),
    };
    renderAt(
      "/simulator-lab/scenarios/cold-normal/run-setup",
      cold.client,
      runClient().client,
      foundationClient().client,
      catalog,
    );
    await settledScreen();

    expect(
      screen.getByRole("heading", { level: 1, name: "Set up a draft run" }),
    ).toBeInTheDocument();
    expect(screen.getByText("No such saved scenario")).toBeInTheDocument();
    expect(cold.calls).toEqual([]);
  });
});
