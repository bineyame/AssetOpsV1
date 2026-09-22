import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import type {
  SiteDetailClient,
  SiteDirectoryClient,
} from "../../sites/siteDirectoryClient";
import type { SiteDetailReadModel } from "../../sites/siteReadModel";
import { settledScreen } from "../../test/settled";
import { spacedText, textNodes } from "../../test/text";
import type {
  ScenarioCatalogClient,
  ScenarioDetail,
  ScenarioDetailResult,
} from "../scenarioCatalogClient";
import type {
  CreateRunResult,
  RunProfilesResult,
  RunSetupClient,
  RunSetupInput,
  RunSummary,
} from "../runSetupClient";
import {
  RESOLVED_TARGET,
  SCENARIO_DETAIL,
  SCENARIO_SUMMARY,
  UNCONFIGURED_TARGET,
  OBSERVATION_SOURCE_RESOLUTIONS,
  PRIVATE_EXPECTATIONS,
} from "./scenarioFixtures";

/**
 * The run setup screen: what it freezes, what it refuses, and what it blocks.
 *
 * Every assertion is about what the screen renders from a record. The
 * scenario client, the site client and the run setup client are all injected,
 * so nothing here depends on a store, a network, or a fixture file on disk.
 *
 * The two outcomes are tested as two, deliberately. A refusal renders no
 * frozen summary at all, because no run was created and there is nothing to
 * summarise; a blocked draft renders the whole summary beside its reasons,
 * because the frozen inputs are what a reader needs in order to decide what
 * to change. A test that only checked "something was said" would pass on a
 * screen that had collapsed the two.
 */

const ENABLED = featureFlagsWith(true);

const RUN_SETUP_URL = "/simulator-lab/scenarios/fuel-loss-event/run-setup";

const EMPTY_SITE_DIRECTORY: SiteDirectoryClient = {
  listSites: () => Promise.resolve({ status: "loaded", sites: [] }),
};

const SITE: SiteDetailReadModel = {
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
    summary: "Solar-plus-storage mini-grid with a metered distribution load.",
    components: [],
    topology: null,
    devices: null,
    signal_mappings: null,
    control_assumptions: null,
  },
};

const SITE_DETAIL_CLIENT: SiteDetailClient = {
  getSite: () => Promise.resolve({ status: "loaded", site: SITE }),
};

const PROFILES: RunProfilesResult = {
  status: "loaded",
  modelProfiles: [
    {
      model_profile_id: "minimal-fuel-tank",
      model_profile_version: 1,
      display_name: "Minimal fuel tank model",
      statement: "Models the stored volume and the capacity that bounds it.",
      supported_states: [
        {
          state_key: "fuel-tank-volume",
          supported_roles: ["CAUSAL_INPUT", "REPORTED_OBSERVATION"],
          statement: "The stored volume can be caused and reported.",
        },
      ],
    },
  ],
  publicationProfiles: [
    {
      publication_profile_id: "simulator-lab-publication",
      publication_profile_version: 1,
      display_name: "Simulator Lab publication profile",
      statement: "Declares the cadence and the publication identities.",
      device_signal_cadence_minutes: 15,
      simulator_source_id: "simulator-lab-source",
      gateway_id: "simulator-lab-gateway",
    },
  ],
};

const FROZEN_INPUTS = [
  {
    identity_field: "site",
    field: "Site",
    value: "MG-001",
    answered_by: "SITE_FOUNDATION",
    answered_by_detail: "site MG-001 foundation version 1",
  },
  {
    identity_field: "interval",
    field: "Timestep",
    value: "15 minutes",
    answered_by: "RUN_INPUT",
    answered_by_detail: "supplied by this run setup request",
  },
  {
    identity_field: "observation_bindings",
    field: "Cadence for fuel-level-sensor-reading",
    value: "15 minutes",
    answered_by: "MODEL_PROFILE",
    answered_by_detail: "publication profile simulator-lab-publication version 1",
  },
  {
    identity_field: "intervention_history",
    field: "Intervention history",
    value: "empty",
    answered_by: "RUN_INPUT",
    answered_by_detail: "supplied by this run setup request",
  },
];

const READY_RUN: RunSummary = {
  run_id: "run-1f0c2b7a4e5d4c8fa1b2c3d4e5f60718",
  lifecycle_status: "DRAFT",
  execution_status: "READY",
  readiness_disclosure:
    "READY means every required executable input resolved and the selected " +
    "model profile declares it can consume them. It does not mean the model " +
    "can.",
  created_at: "2026-09-21T09:00:00Z",
  site_id: "MG-001",
  scenario_id: "fuel-loss-event",
  scenario_version: 1,
  frozen_inputs: FROZEN_INPUTS,
  blocking_reasons: [],
  unsupported_optional_inputs: [],
};

const BLOCKED_RUN: RunSummary = {
  ...READY_RUN,
  run_id: "run-99aa88bb77cc66dd55ee44ff33221100",
  execution_status: "BLOCKED",
  readiness_disclosure: null,
  // Two reasons of two kinds, both about what the selected profile can do.
  // A reason about the scenario disagreeing with its own arithmetic used to
  // be here; Amendment 1's proposal (e) removed that from run setup, because
  // deciding it needs a kernel and run setup has none.
  blocking_reasons: [
    {
      kind: "CADENCE_NOT_RESOLVED",
      subject: "fuel-level-sensor-reading",
      statement:
        "The publication profile this run selected declares no cadence for " +
        "a configured device signal, and nothing else may supply one.",
    },
    {
      kind: "STATE_NOT_SUPPORTED",
      subject: "site-load-demand",
      statement:
        "The selected model profile does not model site-load-demand, which " +
        "this scenario needs as a FORCING_INPUT.",
    },
  ],
  unsupported_optional_inputs: [],
};

function scenarioClient(
  detail: ScenarioDetailResult = loadedScenario(),
): ScenarioCatalogClient {
  return {
    listScenarios: () =>
      Promise.resolve({ status: "loaded", scenarios: [SCENARIO_SUMMARY] }),
    getScenario: () => Promise.resolve(detail),
  };
}

function loadedScenario(
  targetResolution = RESOLVED_TARGET,
  scenario: ScenarioDetail = SCENARIO_DETAIL,
): ScenarioDetailResult {
  return {
    status: "loaded",
    scenario,
    targetResolution,
    observationSourceResolutions: OBSERVATION_SOURCE_RESOLUTIONS,
    privateExpectations: PRIVATE_EXPECTATIONS,
  };
}

function runClient(outcome: CreateRunResult): {
  client: RunSetupClient;
  calls: RunSetupInput[];
} {
  const calls: RunSetupInput[] = [];
  return {
    calls,
    client: {
      listProfiles: () => Promise.resolve(PROFILES),
      createRun: (input: RunSetupInput) => {
        calls.push(input);
        return Promise.resolve(outcome);
      },
      listRuns: () => Promise.resolve({ status: "loaded", runs: [] }),
      getRun: () => Promise.resolve({ status: "not_found" }),
    },
  };
}

function renderSetup(
  runSetup: RunSetupClient,
  catalog: ScenarioCatalogClient = scenarioClient(),
) {
  return render(
    <MemoryRouter initialEntries={[RUN_SETUP_URL]}>
      <App
        flags={ENABLED}
        siteDirectory={EMPTY_SITE_DIRECTORY}
        siteDetail={SITE_DETAIL_CLIENT}
        scenarioCatalog={catalog}
        runSetup={runSetup}
      />
    </MemoryRouter>,
  );
}

/**
 * Fill the form the way a person would, and submit it.
 *
 * The two profiles are chosen here rather than arriving chosen, because
 * nothing on this screen chooses them: they are components of the frozen
 * deterministic identity and the model profile decides the outcome.
 */
async function fillAndSubmit(): Promise<void> {
  fireEvent.change(screen.getByLabelText("Interval start"), {
    target: { value: "2026-09-21T00:00:00Z" },
  });
  fireEvent.change(screen.getByLabelText("Interval end"), {
    target: { value: "2026-09-22T17:00:00Z" },
  });
  fireEvent.change(screen.getByLabelText("Timestep in minutes"), {
    target: { value: "15" },
  });
  fireEvent.change(screen.getByLabelText("Seed"), {
    target: { value: "20260921" },
  });
  fireEvent.change(screen.getByLabelText("Model profile"), {
    target: { value: "minimal-fuel-tank@1" },
  });
  fireEvent.change(screen.getByLabelText("Publication profile"), {
    target: { value: "simulator-lab-publication@1" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Create draft run" }));
}

describe("the run setup screen before anything is submitted", () => {
  it("states that setting a run up executes nothing", async () => {
    renderSetup(runClient({ status: "created", run: READY_RUN }).client);
    await settledScreen();

    const main = screen.getByRole("main");

    expect(spacedText(main)).toMatch(/It does not run anything/i);
    expect(spacedText(main)).toMatch(/no accepted evidence/i);
  });

  it("shows the versions the scenario and the site already fix", async () => {
    renderSetup(runClient({ status: "created", run: READY_RUN }).client);
    await settledScreen();

    const facts = screen.getByRole("main");

    expect(within(facts).getByText("Scenario version")).toBeInTheDocument();
    // The foundation version is read from the site record rather than typed:
    // a run freezes the exact version it was set up against, and offering it
    // as a field would let a person name one the site does not have.
    expect(within(facts).getByText("Foundation version")).toBeInTheDocument();
    expect(
      screen.queryByLabelText("Foundation version"),
    ).toBeNull();
  });

  it("prefills no interval, no timestep and no seed", async () => {
    // A prefilled number would be a digit on this screen that no record
    // supplies, and run setup quietly choosing part of a deterministic
    // identity.
    renderSetup(runClient({ status: "created", run: READY_RUN }).client);
    await settledScreen();

    expect(screen.getByLabelText("Interval start")).toHaveValue("");
    expect(screen.getByLabelText("Interval end")).toHaveValue("");
    expect(screen.getByLabelText("Timestep in minutes")).toHaveValue("");
    expect(screen.getByLabelText("Seed")).toHaveValue("");
  });

  it("says the scenario declares no value the run owns", async () => {
    renderSetup(runClient({ status: "created", run: READY_RUN }).client);
    await settledScreen();

    expect(
      screen.getByText(/declares no value the run owns/i),
    ).toBeInTheDocument();
  });

  it("asks for a value the scenario says the run owns", async () => {
    const scenario: ScenarioDetail = {
      ...SCENARIO_DETAIL,
      public_parameters: SCENARIO_DETAIL.public_parameters.map((parameter) =>
        parameter.parameter_id === "starting-fuel-level"
          ? {
              ...parameter,
              ownership: { owner: "RUN_OVERRIDE", initializes: true },
            }
          : parameter,
      ),
    };

    renderSetup(
      runClient({ status: "created", run: READY_RUN }).client,
      scenarioClient(loadedScenario(RESOLVED_TARGET, scenario)),
    );
    await settledScreen();

    expect(
      screen.getByLabelText(/Fuel level at the start of the interval in L/),
    ).toHaveValue("");
  });

  it("sends the typed values and the record's versions", async () => {
    const { client, calls } = runClient({
      status: "created",
      run: READY_RUN,
    });
    renderSetup(client);
    await settledScreen();

    await fillAndSubmit();
    await screen.findByText("Run ID");

    expect(calls).toHaveLength(1);
    expect(calls[0]).toEqual({
      site_id: "MG-001",
      foundation_version: 1,
      scenario_id: "fuel-loss-event",
      scenario_version: SCENARIO_DETAIL.version.scenario_version,
      interval: {
        start_time: "2026-09-21T00:00:00Z",
        end_time: "2026-09-22T17:00:00Z",
      },
      timestep_minutes: 15,
      seed: 20260921,
      model_profile: {
        profile_id: "minimal-fuel-tank",
        profile_version: 1,
      },
      publication_profile: {
        profile_id: "simulator-lab-publication",
        profile_version: 1,
      },
      run_inputs: [],
    });
  });
});

describe("nothing on this screen is chosen for the person", () => {
  it("chooses neither profile", async () => {
    // Both are components of the frozen deterministic identity, and the
    // model profile is what decides READY against BLOCKED. An earlier
    // version selected the first of each, so the screen chose the outcome.
    renderSetup(runClient({ status: "created", run: READY_RUN }).client);
    await settledScreen();

    expect(screen.getByLabelText("Model profile")).toHaveValue("");
    expect(screen.getByLabelText("Publication profile")).toHaveValue("");
  });

  it("offers an empty option on each profile select", async () => {
    renderSetup(runClient({ status: "created", run: READY_RUN }).client);
    await settledScreen();

    expect(
      within(screen.getByLabelText("Model profile") as HTMLSelectElement)
        .getAllByRole("option")
        .map((option) => (option as HTMLOptionElement).value),
    ).toEqual(["", "minimal-fuel-tank@1"]);
  });

  it("sends the empty choice and lets the backend refuse it", async () => {
    // The same division of labour as every other field: the screen does not
    // refuse a value before the rule that owns it has seen it.
    const { client, calls } = runClient({
      status: "refused",
      code: "RUN_REQUEST_INVALID",
      refusalKind: "REQUEST_INVALID",
      message: "'model_profile'.profile_id '' is not a profile identity.",
    });
    renderSetup(client);
    await settledScreen();

    fireEvent.change(screen.getByLabelText("Interval start"), {
      target: { value: "2026-09-21T00:00:00Z" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Create draft run" }));

    const alert = await screen.findByRole("alert");
    expect(calls[0].model_profile).toEqual({
      profile_id: "",
      profile_version: Number.NaN,
    });
    expect(alert.textContent).toContain("is not a profile identity");
  });

  it("sends a decimal run input as the decimal it is", async () => {
    // Parsing every field as a whole number turned a typed 812.5 into NaN,
    // which arrived as null and came back refused as MISSING - a refusal
    // about a field the person had filled in, invented by this screen.
    const scenario: ScenarioDetail = {
      ...SCENARIO_DETAIL,
      public_parameters: SCENARIO_DETAIL.public_parameters.map((parameter) =>
        parameter.parameter_id === "starting-fuel-level"
          ? {
              ...parameter,
              ownership: { owner: "RUN_OVERRIDE", initializes: true },
            }
          : parameter,
      ),
    };
    const { client, calls } = runClient({
      status: "created",
      run: READY_RUN,
    });

    renderSetup(client, scenarioClient(loadedScenario(RESOLVED_TARGET, scenario)));
    await settledScreen();

    fireEvent.change(
      screen.getByLabelText(/Fuel level at the start of the interval in L/),
      { target: { value: "812.5" } },
    );
    await fillAndSubmit();
    await screen.findByText("Run ID");

    expect(calls[0].run_inputs).toEqual([
      { parameter_id: "starting-fuel-level", value: 812.5, unit: "L" },
    ]);
  });

  it("still sends a whole timestep and a whole seed", async () => {
    // The two fields the contract really does require a whole number for.
    const { client, calls } = runClient({
      status: "created",
      run: READY_RUN,
    });
    renderSetup(client);
    await settledScreen();
    await fillAndSubmit();
    await screen.findByText("Run ID");

    expect(calls[0].timestep_minutes).toBe(15);
    expect(calls[0].seed).toBe(20260921);
  });
});

describe("when a read the screen depends on fails", () => {
  const FAILING_SITE: SiteDetailClient = {
    getSite: () => Promise.resolve({ status: "unavailable" }),
  };

  it("does not offer to create a run it cannot fill in", async () => {
    // An earlier version left "Reading the configured site." on screen for
    // ever, kept submit enabled, and sent a foundation version of NaN.
    const { client, calls } = runClient({
      status: "created",
      run: READY_RUN,
    });
    render(
      <MemoryRouter initialEntries={[RUN_SETUP_URL]}>
        <App
          flags={ENABLED}
          siteDirectory={EMPTY_SITE_DIRECTORY}
          siteDetail={FAILING_SITE}
          scenarioCatalog={scenarioClient()}
          runSetup={client}
        />
      </MemoryRouter>,
    );
    await settledScreen();

    const submit = screen.getByRole("button", { name: "Create draft run" });
    expect(submit).toBeDisabled();
    expect(spacedText(screen.getByRole("main"))).toMatch(
      /the site store could not be read/i,
    );
    expect(calls).toEqual([]);
  });

  it("says so when the versioned profiles could not be read", async () => {
    const client: RunSetupClient = {
      listProfiles: () => Promise.resolve({ status: "unavailable" }),
      createRun: () => Promise.resolve({ status: "created", run: READY_RUN }),
      listRuns: () => Promise.resolve({ status: "loaded", runs: [] }),
      getRun: () => Promise.resolve({ status: "not_found" }),
    };
    renderSetup(client);
    await settledScreen();

    expect(spacedText(screen.getByRole("main"))).toMatch(
      /versioned profiles could not be read/i,
    );
  });
});

describe("a request that did not complete", () => {
  it("renders the backend's own message rather than a generic one", async () => {
    // A 503 carries product copy naming the store that could not be reached.
    // Discarding it to show a generic sentence is the screen writing a
    // second, worse version of the same fact.
    //
    // The fixture is the whole message the endpoint sends, closing sentence
    // included. It used to be the store's raw string without it - a message
    // the wire cannot produce - so the test passed while the screen printed
    // "Nothing was written." twice on a real failure. An assertion held
    // against a value the product cannot make is the shape this slice has
    // now paid for three times.
    renderSetup(
      runClient({
        status: "unavailable",
        message:
          "The run store could not be written: var/runs. Nothing was written.",
      }).client,
    );
    await settledScreen();
    await fillAndSubmit();

    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toContain("The run store could not be written");
    expect(alert.textContent?.match(/nothing was written/gi)).toHaveLength(1);
  });

  it("says it once when there is no message to say it", async () => {
    renderSetup(runClient({ status: "unavailable", message: null }).client);
    await settledScreen();
    await fillAndSubmit();

    const alert = await screen.findByRole("alert");
    expect(alert.textContent?.match(/nothing was written/gi)).toHaveLength(1);
  });

  it("never says nothing was written over a run that was", async () => {
    // A 201 whose body cannot be read is a run that exists. Saying nothing
    // was written there is the worst sentence this surface could say.
    renderSetup(runClient({ status: "created_but_unreadable" }).client);
    await settledScreen();
    await fillAndSubmit();

    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toMatch(/was created and persisted/i);
    expect(alert.textContent).not.toMatch(/nothing was written/i);
    expect(screen.queryByText("Run ID")).toBeNull();
  });
});

describe("a ready draft", () => {
  it("renders the run, its status and its frozen inputs", async () => {
    renderSetup(runClient({ status: "created", run: READY_RUN }).client);
    await settledScreen();
    await fillAndSubmit();

    expect(await screen.findByText(READY_RUN.run_id)).toBeInTheDocument();
    expect(screen.getByText("READY")).toBeInTheDocument();
    expect(screen.getByText("DRAFT")).toBeInTheDocument();

    const table = screen.getByRole("table", { name: "The frozen inputs" });
    for (const row of FROZEN_INPUTS) {
      expect(within(table).getByText(row.field)).toBeInTheDocument();
      // `getAllByText`, because two values can honestly share an answerer:
      // the seed and the interval are both supplied by the same request.
      expect(
        within(table).getAllByText(row.answered_by_detail).length,
      ).toBeGreaterThan(0);
    }
  });

  it("says ready means executable, not executed", async () => {
    renderSetup(runClient({ status: "created", run: READY_RUN }).client);
    await settledScreen();
    await fillAndSubmit();

    await screen.findByText(READY_RUN.run_id);

    expect(spacedText(screen.getByRole("main"))).toMatch(
      /it does not mean anything has been/i,
    );
  });

  it("renders every frozen value with the answerer the record supplies", async () => {
    renderSetup(runClient({ status: "created", run: READY_RUN }).client);
    await settledScreen();
    await fillAndSubmit();
    await screen.findByText(READY_RUN.run_id);

    const table = screen.getByRole("table", { name: "The frozen inputs" });
    const rows = within(table).getAllByRole("row").slice(1);

    expect(rows).toHaveLength(FROZEN_INPUTS.length);
    rows.forEach((row, index) => {
      expect(row.textContent).toContain(FROZEN_INPUTS[index].answered_by);
    });
  });
});

describe("a blocked draft", () => {
  it("is created, and says why it cannot be executed", async () => {
    renderSetup(runClient({ status: "created", run: BLOCKED_RUN }).client);
    await settledScreen();
    await fillAndSubmit();

    expect(await screen.findByText(BLOCKED_RUN.run_id)).toBeInTheDocument();
    expect(screen.getByText("BLOCKED")).toBeInTheDocument();

    const reasons = screen.getByRole("table", {
      name: "Why this draft cannot be executed",
    });
    for (const reason of BLOCKED_RUN.blocking_reasons) {
      expect(within(reasons).getByText(reason.kind)).toBeInTheDocument();
      expect(within(reasons).getByText(reason.subject)).toBeInTheDocument();
      expect(within(reasons).getByText(reason.statement)).toBeInTheDocument();
    }
  });

  it("still renders the whole frozen summary", async () => {
    // The distinction the slice carries: a blocked draft exists and is
    // persisted, so what it froze is inspectable. A screen that hid the
    // summary when a run was blocked would be treating it as a failure.
    renderSetup(runClient({ status: "created", run: BLOCKED_RUN }).client);
    await settledScreen();
    await fillAndSubmit();
    await screen.findByText(BLOCKED_RUN.run_id);

    const table = screen.getByRole("table", { name: "The frozen inputs" });

    expect(within(table).getAllByRole("row")).toHaveLength(
      FROZEN_INPUTS.length + 1,
    );
  });

  it("does not claim the draft is ready", async () => {
    renderSetup(runClient({ status: "created", run: BLOCKED_RUN }).client);
    await settledScreen();
    await fillAndSubmit();
    await screen.findByText(BLOCKED_RUN.run_id);

    expect(screen.queryByText("This draft is ready")).toBeNull();
  });
});

describe("a refusal", () => {
  const REFUSED: CreateRunResult = {
    status: "refused",
    code: "RUN_INTERVAL_INVALID",
    refusalKind: "INTERVAL_INVALID",
    message:
      "Entry generator-run-window runs until a point past the end of the " +
      "interval. Choose an interval that covers the whole scenario.",
  };

  it("renders the backend's own copy and says nothing was created", async () => {
    renderSetup(runClient(REFUSED).client);
    await settledScreen();
    await fillAndSubmit();

    const alert = await screen.findByRole("alert");

    expect(alert.textContent).toContain(REFUSED.message);
    expect(alert.textContent).toMatch(/no draft run was created/i);
  });

  it("renders no frozen summary at all", async () => {
    // No run was created, so there is nothing to summarise. A screen that
    // rendered an empty summary here would imply a run exists.
    renderSetup(runClient(REFUSED).client);
    await settledScreen();
    await fillAndSubmit();
    await screen.findByRole("alert");

    expect(screen.queryByText("Run ID")).toBeNull();
    expect(
      screen.queryByRole("region", { name: "The frozen inputs" }),
    ).toBeNull();
  });
});

describe("the run setup screen makes no downstream claim", () => {
  it("offers no control belonging to a later step", async () => {
    renderSetup(runClient({ status: "created", run: READY_RUN }).client);
    await settledScreen();
    await fillAndSubmit();
    await screen.findByText(READY_RUN.run_id);

    const main = screen.getByRole("main");

    // The one control on this screen is the one that creates the draft.
    expect(
      within(main)
        .getAllByRole("button")
        .map((button) => button.textContent),
    ).toEqual(["Create draft run"]);

    for (const banned of [
      /commit/i,
      /replay/i,
      /ingest/i,
      /open in assetops/i,
      /rerun/i,
      /finding/i,
    ]) {
      expect(
        within(main).queryByRole("button", { name: banned }),
      ).toBeNull();
      expect(within(main).queryByRole("link", { name: banned })).toBeNull();
    }
  });

  it("states what the draft is not, and names nothing it has no use for", async () => {
    renderSetup(runClient({ status: "created", run: READY_RUN }).client);
    await settledScreen();
    await fillAndSubmit();
    await screen.findByText(READY_RUN.run_id);

    const words = spacedText(screen.getByRole("main"));

    // The positive half first, and it is the half that matters. The screen
    // says what does not exist rather than being quiet about it, and these
    // are the sentences a reader gets.
    expect(words).toMatch(/It has not been executed/i);
    expect(words).toMatch(/Nothing has been staged for a gateway/i);
    expect(words).toMatch(/it cannot be committed/i);
    expect(words).toMatch(/No evidence has been accepted/i);
    expect(words).toMatch(/No conclusion has been drawn/i);

    // The negative half is deliberately narrow. Banning "evidence",
    // "committed" or "finding" outright would ban the sentences above, and
    // copy bent to satisfy its own guard is the failure shape T018's review
    // named. What is banned is the vocabulary this screen has no honest use
    // for in any sentence.
    for (const banned of [
      /\breplay\b/i,
      /\bingest(ed|ion|s)?\b/i,
      /\bgolden\b/i,
      /\brerun\b/i,
      /open in assetops/i,
    ]) {
      expect(words).not.toMatch(banned);
    }
  });

  it("renders no digit that is not a record value or a typed value", async () => {
    renderSetup(runClient({ status: "created", run: READY_RUN }).client);
    await settledScreen();
    await fillAndSubmit();
    await screen.findByText(READY_RUN.run_id);

    // Every digit on this screen traces to the run record, to the scenario
    // record, to the site record, or to what was just typed into the form.
    const expected = new Set<string>([
      READY_RUN.run_id,
      READY_RUN.created_at,
      String(SCENARIO_DETAIL.version.scenario_version),
      String(SITE.foundation.version),
      SITE.site_id,
      "2026-09-21T00:00:00Z",
      "2026-09-22T17:00:00Z",
      "15",
      "20260921",
      ...FROZEN_INPUTS.map((row) => row.field),
      ...FROZEN_INPUTS.map((row) => row.value),
      ...FROZEN_INPUTS.map((row) => row.answered_by_detail),
    ]);

    const leaves = textNodes(screen.getByRole("main"));
    const withDigits = leaves.filter((leaf) => /\d/.test(leaf));

    expect(withDigits.length).toBeGreaterThan(0);
    for (const leaf of withDigits) {
      expect(expected).toContain(leaf);
    }
  });
});

describe("the run setup screen without a configured site", () => {
  it("offers no form and says why", async () => {
    const { client, calls } = runClient({
      status: "created",
      run: READY_RUN,
    });
    renderSetup(client, scenarioClient(loadedScenario(UNCONFIGURED_TARGET)));
    await settledScreen();

    expect(
      screen.getByRole("heading", {
        name: "No configured site to bind this run to",
      }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Create draft run" }),
    ).toBeNull();
    expect(calls).toEqual([]);
    expect(spacedText(screen.getByRole("main"))).toContain(
      UNCONFIGURED_TARGET.reason,
    );
  });

  it("says so for an unsaved scenario too", async () => {
    renderSetup(
      runClient({ status: "created", run: READY_RUN }).client,
      scenarioClient({ status: "not_found" }),
    );
    await settledScreen();

    expect(
      screen.getByRole("heading", { name: "No such saved scenario" }),
    ).toBeInTheDocument();
  });
});

describe("the run setup surface is gated", () => {
  it("is not served when the gate is closed", async () => {
    render(
      <MemoryRouter initialEntries={[RUN_SETUP_URL]}>
        <App
          flags={featureFlagsWith(false)}
          siteDirectory={EMPTY_SITE_DIRECTORY}
          siteDetail={SITE_DETAIL_CLIENT}
          scenarioCatalog={scenarioClient()}
          runSetup={runClient({ status: "created", run: READY_RUN }).client}
        />
      </MemoryRouter>,
    );
    await settledScreen();

    expect(
      screen.getByRole("heading", { level: 1, name: "Page not available" }),
    ).toBeInTheDocument();
  });

  it("reaches no run API when the gate is closed", async () => {
    const fetched = vi.fn();
    vi.stubGlobal("fetch", fetched);

    render(
      <MemoryRouter initialEntries={[RUN_SETUP_URL]}>
        <App flags={featureFlagsWith(false)} />
      </MemoryRouter>,
    );
    await settledScreen();

    expect(fetched).not.toHaveBeenCalled();
    vi.unstubAllGlobals();
  });
});
