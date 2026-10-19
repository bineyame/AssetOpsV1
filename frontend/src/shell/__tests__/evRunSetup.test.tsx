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
  EvScenarioChoice,
  EvScenarioChoiceClient,
  EvScenarioChoicesResult,
} from "../evScenarioChoiceClient";
import type {
  CreateRunResult,
  RunSetupClient,
  RunSetupInput,
} from "../runSetupClient";
import {
  EV_CHOOSE_SITE_COPY,
  EV_EMPTY_COPY,
  EV_FORBIDDEN_COPY,
  EV_LOADING_COPY,
  EV_NO_SELECTION_COPY,
  EV_NOT_FOUND_COPY,
  EV_UNAVAILABLE_COPY,
} from "../EvRunSetupFrame";
import { executionMethods } from "./executionFixtures";

/**
 * W2-05b: the EV charging run setup (`.agent/W2-05b-build-spec.md` Q8-Q11).
 * Site first; only an EV_CHARGING Site reads the EV choices for that exact
 * Site; a row writes nothing; Create sends the document's own values.
 */

const ENABLED = featureFlagsWith(true);
const EV_URL = "/simulator-lab/ev-run-setup";

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
const EV_SITE = {
  ...BASE_SITE,
  site_id: "EV-LAB-001",
  display_name: "EV Lab Depot",
  site_type: "EV_CHARGING",
  configuration_store: "POSTGRES",
} as SiteDetailReadModel;
const EV_SITE_2 = {
  ...EV_SITE,
  site_id: "EV-LAB-002",
  display_name: "Second EV Depot",
} as SiteDetailReadModel;
const OTHER_SITE = { ...BASE_SITE, configuration_store: "LEGACY_FILE" } as SiteDetailReadModel;
const EV_CHOICE_LABEL = "EV Lab Depot (EV-LAB-001)";
const EV_2_CHOICE_LABEL = "Second EV Depot (EV-LAB-002)";
const OTHER_CHOICE_LABEL = "Kalangala Mini-Grid (MG-001)";
const SITES = [EV_SITE, EV_SITE_2, OTHER_SITE];

const directory: SiteDirectoryClient = {
  listSites: () => Promise.resolve({ status: "loaded", sites: SITES }),
};
const detail: SiteDetailClient = {
  getSite: (id: string) =>
    Promise.resolve({
      status: "loaded",
      site: SITES.find((site) => site.site_id === id) ?? OTHER_SITE,
    }),
};

const WINDOW = {
  start: "2026-10-06T08:00:00Z",
  end: "2026-10-06T09:00:00Z",
  end_exclusive: true,
};
const COMPLETE: EvScenarioChoice = {
  scenario_id: "ev-complete",
  scenario_version: 1,
  display_name: "Complete session",
  schema: "ev-scenario/1",
  model_profile: "ev-charger/1",
  publication_profile: "ev-publication/1",
  observation_profile: "ev-observation/1",
  window: WINDOW,
  seed: 20517,
  site_code: "EV-LAB-001",
};
const FAULT: EvScenarioChoice = {
  ...COMPLETE,
  scenario_id: "ev-fault",
  display_name: "Fault before charging",
};

function loaded(siteId: string, scenarios: EvScenarioChoice[]): EvScenarioChoicesResult {
  return { status: "loaded", siteId, scenarios };
}

/** Answers by Site, like the backend: the choices for EV-LAB-001 only. */
function evClient(
  answers: (siteId: string, call: number) => Promise<EvScenarioChoicesResult> = (siteId) =>
    Promise.resolve(loaded(siteId, siteId === EV_SITE.site_id ? [COMPLETE, FAULT] : [])),
): { client: EvScenarioChoiceClient; calls: string[] } {
  const calls: string[] = [];
  return {
    calls,
    client: {
      listEvScenarios: (siteId: string) => {
        calls.push(siteId);
        return answers(siteId, calls.length);
      },
    },
  };
}

function foundationClient() {
  const reads: [string, string | null][] = [];
  const client = {
    getFoundation: (siteId: string, at: string | null) => {
      reads.push([siteId, at]);
      return Promise.resolve<FoundationRead<FoundationReadModel>>({
        status: "loaded",
        value: {
          revision: { version: 5, valid_from: "2026-10-01T00:00:00Z", valid_to: null },
          bindings: {
            binding_set: { version: 2, valid_from: "2026-10-01T00:01:00Z", valid_to: null },
          },
          acquisition_snapshot: {
            available: true,
            sha256: "c".repeat(64),
            schema: "assetops.acquisition-snapshot/1",
          },
        } as unknown as FoundationReadModel,
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
  ev: EvScenarioChoiceClient,
  runSetup: RunSetupClient = runClient().client,
  foundation: SiteFoundationClient = foundationClient().client,
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
        evScenarios={ev}
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
  return Array.from(document.querySelectorAll("[data-ev-choice-row]")).map(
    (row) => row.getAttribute("data-ev-choice-row") ?? "",
  );
}

function panelState(kind: string): string | null | undefined {
  return document.querySelector(`[data-ev-choice-state="${kind}"]`)?.textContent;
}

describe("EV run setup (W2-05b)", () => {
  it("links from the Lab beside the cold-chain setup", async () => {
    renderAt("/simulator-lab", evClient().client);
    await settledScreen();

    const link = screen.getByRole("link", { name: "Set up an EV charging run" });
    expect(link.getAttribute("href")).toBe(EV_URL);
    expect(screen.getByRole("link", { name: "Set up a cold-chain run" })).toBeInTheDocument();
  });

  it("asks for a Site first with the ruled headings, reads nothing, and keeps Create disabled", async () => {
    const ev = evClient();
    renderAt(EV_URL, ev.client);
    await settledScreen();

    expect(
      screen.getByRole("heading", { level: 1, name: "Set up an EV charging draft run" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "EV test runs" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Create the draft run" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Back to the Simulator Lab" })).toBeInTheDocument();
    expect(panelState("choose-site")).toBe(EV_CHOOSE_SITE_COPY);
    expect(ev.calls).toEqual([]);
    expect(createButton().disabled).toBe(true);
  });

  it("renders only the choices returned for the selected EV Site, by display name", async () => {
    const ev = evClient();
    renderAt(EV_URL, ev.client);
    await settledScreen();

    chooseSite(EV_CHOICE_LABEL);
    await settledScreen();

    expect(ev.calls).toEqual(["EV-LAB-001"]);
    expect(choiceRows()).toEqual(["ev-complete", "ev-fault"]);
    expect(screen.getByRole("group", { name: "EV test run" })).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: "Complete session" })).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: "Fault before charging" })).toBeInTheDocument();
    expect(screen.getByText(EV_NO_SELECTION_COPY)).toBeInTheDocument();
    expect(createButton().disabled).toBe(true);
  });

  it("does not read choices for a non-EV Site and states the empty copy", async () => {
    const ev = evClient();
    renderAt(EV_URL, ev.client);
    await settledScreen();

    chooseSite(OTHER_CHOICE_LABEL);
    await settledScreen();

    expect(ev.calls).toEqual([]);
    expect(panelState("empty")).toBe(EV_EMPTY_COPY);
    expect(choiceRows()).toEqual([]);
    expect(createButton().disabled).toBe(true);
  });

  it.each([
    ["forbidden", { status: "forbidden" } as EvScenarioChoicesResult, EV_FORBIDDEN_COPY],
    ["not-found", { status: "not_found" } as EvScenarioChoicesResult, EV_NOT_FOUND_COPY],
    ["empty", loaded("EV-LAB-001", []), EV_EMPTY_COPY],
  ])("states the %s copy once, with no rows and Create disabled", async (kind, answer, copy) => {
    renderAt(EV_URL, evClient(() => Promise.resolve(answer)).client);
    await settledScreen();
    chooseSite(EV_CHOICE_LABEL);
    await settledScreen();

    expect(panelState(kind)).toBe(copy);
    expect(screen.getAllByText(copy)).toHaveLength(1);
    expect(choiceRows()).toEqual([]);
    expect(screen.queryByRole("button", { name: "Retry" })).toBeNull();
    expect(createButton().disabled).toBe(true);
  });

  it("states the unavailable copy, never the empty claim, and Retry keeps the Site", async () => {
    const ev = evClient((siteId, call) =>
      Promise.resolve(call === 1 ? { status: "unavailable" } : loaded(siteId, [COMPLETE])),
    );
    renderAt(EV_URL, ev.client);
    await settledScreen();

    chooseSite(EV_CHOICE_LABEL);
    await settledScreen();

    expect(panelState("unavailable")).toBe(EV_UNAVAILABLE_COPY);
    expect(screen.getAllByText(EV_UNAVAILABLE_COPY)).toHaveLength(1);
    expect(panelState("empty")).toBeUndefined();
    expect(createButton().disabled).toBe(true);

    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    await settledScreen();

    expect(ev.calls).toEqual(["EV-LAB-001", "EV-LAB-001"]);
    expect(
      (screen.getByRole("radio", { name: EV_CHOICE_LABEL }) as HTMLInputElement).checked,
    ).toBe(true);
    expect(choiceRows()).toEqual(["ev-complete"]);
    expect(panelState("unavailable")).toBeUndefined();
  });

  it("states the loading copy while the choice read is pending", async () => {
    renderAt(EV_URL, evClient(() => new Promise(() => {})).client);
    await settledScreen();
    chooseSite(EV_CHOICE_LABEL);
    // The choice read is held pending on purpose, so this asserts the loading state itself.
    await screen.findByText(EV_LOADING_COPY);
    expect(screen.getAllByText(EV_LOADING_COPY)).toHaveLength(1);
    expect(createButton().disabled).toBe(true);
  });

  it("ignores an older response for a prior Site", async () => {
    let resolveFirst: (value: EvScenarioChoicesResult) => void = () => {};
    const ev = evClient((siteId) =>
      siteId === EV_SITE.site_id
        ? new Promise((resolve) => {
            resolveFirst = resolve;
          })
        : Promise.resolve(loaded(siteId, [])),
    );
    renderAt(EV_URL, ev.client);
    await settledScreen();

    chooseSite(EV_CHOICE_LABEL);
    chooseSite(EV_2_CHOICE_LABEL);
    await settledScreen();
    expect(panelState("empty")).toBe(EV_EMPTY_COPY);

    await act(async () => {
      resolveFirst(loaded("EV-LAB-001", [COMPLETE]));
      await Promise.resolve();
    });

    expect(choiceRows()).toEqual([]);
    expect(panelState("empty")).toBe(EV_EMPTY_COPY);
    expect(ev.calls).toEqual(["EV-LAB-001", "EV-LAB-002"]);
  });

  it("shows the chosen row's read-only facts and basis without writing", async () => {
    const run = runClient();
    const foundation = foundationClient();
    renderAt(EV_URL, evClient().client, run.client, foundation.client);
    await settledScreen();
    chooseSite(EV_CHOICE_LABEL);
    await settledScreen();

    fireEvent.click(screen.getByRole("radio", { name: "Complete session" }));
    await settledScreen();

    expect(run.calls).toEqual([]);
    expect(foundation.reads).toEqual([["EV-LAB-001", "2026-10-06T08:00:00Z"]]);
    expect(screen.getByRole("heading", { name: "What the EV test run fixes" })).toBeInTheDocument();
    for (const [term, value] of [
      ["Scenario", "ev-complete"],
      ["Interval start", "2026-10-06T08:00:00Z"],
      ["Interval end", "2026-10-06T09:00:00Z"],
      ["Seed", "20517"],
      ["Timestep", "1 minute"],
      ["Model profile", "ev-charger/1"],
      ["Publication profile", "ev-publication/1"],
      ["Observation profile", "ev-observation/1"],
      ["Foundation version", "5"],
    ]) {
      expect(screen.getByText(term).nextElementSibling?.textContent).toBe(value);
    }
    expect(document.querySelector("[data-setup-registered-basis]")).not.toBeNull();
    expect(createButton().disabled).toBe(false);
  });

  it("Create draft run sends exactly the chosen document's request", async () => {
    const run = runClient();
    renderAt(EV_URL, evClient().client, run.client);
    await settledScreen();
    chooseSite(EV_CHOICE_LABEL);
    await settledScreen();
    fireEvent.click(screen.getByRole("radio", { name: "Complete session" }));
    await settledScreen();

    fireEvent.click(createButton());
    await screen.findByRole("alert");

    expect(run.calls).toEqual([
      {
        site_id: "EV-LAB-001",
        foundation_version: 5,
        scenario_id: "ev-complete",
        scenario_version: 1,
        interval: { start_time: "2026-10-06T08:00:00Z", end_time: "2026-10-06T09:00:00Z" },
        timestep_minutes: 1,
        seed: 20517,
        model_profile: { profile_id: "ev-charger", profile_version: 1 },
        publication_profile: { profile_id: "ev-publication", profile_version: 1 },
        run_inputs: [],
      },
    ]);
    expect(screen.getByRole("alert").textContent).toMatch(
      /The request was refused\. No draft run was created/,
    );
  });

  it("clears the selection and result when the Site changes", async () => {
    const run = runClient();
    renderAt(EV_URL, evClient().client, run.client);
    await settledScreen();
    chooseSite(EV_CHOICE_LABEL);
    await settledScreen();
    fireEvent.click(screen.getByRole("radio", { name: "Complete session" }));
    await settledScreen();
    fireEvent.click(createButton());
    await screen.findByRole("alert");

    chooseSite(OTHER_CHOICE_LABEL);
    await settledScreen();

    expect(screen.queryByRole("alert")).toBeNull();
    expect(screen.queryByText("ev-charger/1")).toBeNull();
    expect(createButton().disabled).toBe(true);
  });
});
