import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import type { SiteDirectoryClient } from "../../sites/siteDirectoryClient";
import { settledScreen } from "../../test/settled";
import {
  isRunExecution,
  isRunGenerator,
  type RunExecution,
  type RunSetupClient,
  type RunSummary,
} from "../runSetupClient";
import { executionMethods } from "./executionFixtures";
import overcastPayload from "./kobo-overcast-execution.json";
import runningPayload from "./kobo-mini-grid-running-execution.json";
import startingPayload from "./kobo-mini-grid-starting-execution.json";

/**
 * T025a: the generator of a `mini-grid` run on the Draft run screen.
 *
 * Both payloads were produced by the real backend, not written by hand:
 * `execution_payload` over a projection from the composed execution port, for
 * a Draft of the shipped `kobo-mini-grid-evening` scenario frozen by the real
 * run setup service from the shipped template, 5-minute steps.
 * `kobo-mini-grid-starting-execution.json` is stepped to offset 195, the
 * boundary the Site's start threshold is reached: the request is RUN, the
 * state at T is STOPPED, the state over the step is STARTING and nothing is
 * delivered. `kobo-mini-grid-running-execution.json` is stepped to offset
 * 390, with the generator RUNNING at its 40 kW rating.
 */

const RUN_ID = "run-kobo-mini-grid";
const ENABLED = featureFlagsWith(true);

const EMPTY_SITE_DIRECTORY: SiteDirectoryClient = {
  listSites: () => Promise.resolve({ status: "loaded", sites: [] }),
};

const READY_RUN: RunSummary = {
  run_id: RUN_ID,
  lifecycle_status: "DRAFT",
  execution_status: "READY",
  readiness_disclosure: "READY",
  created_at: "2026-09-29T09:00:00Z",
  site_id: "KOBO-001",
  scenario_id: "kobo-mini-grid-evening",
  scenario_version: 1,
  frozen_inputs: [],
  blocking_reasons: [],
  unsupported_optional_inputs: [],
};

function asExecution(payload: unknown): RunExecution {
  if (!isRunExecution(payload)) {
    throw new Error("the recorded payload no longer matches the client guard");
  }
  return payload;
}

function renderWith(execution: RunExecution) {
  const runSetup: RunSetupClient = {
    listProfiles: () => Promise.resolve({ status: "unavailable" }),
    createRun: () => Promise.resolve({ status: "unavailable", message: null }),
    listRuns: () => Promise.resolve({ status: "loaded", runs: [] }),
    getRun: () => Promise.resolve({ status: "loaded", run: READY_RUN }),
    ...executionMethods({ status: "loaded", execution }),
  };
  return render(
    <MemoryRouter initialEntries={[`/simulator-lab/runs/${RUN_ID}`]}>
      <App
        flags={ENABLED}
        siteDirectory={EMPTY_SITE_DIRECTORY}
        runSetup={runSetup}
      />
    </MemoryRouter>,
  );
}

function text(selector: string): string {
  const found = document.querySelector(selector);
  if (found === null) {
    throw new Error(`nothing matches ${selector}`);
  }
  return found.textContent ?? "";
}

describe("the generator on the Draft run screen", () => {
  it("accepts both recorded backend payloads through the client guard", () => {
    expect(isRunExecution(startingPayload)).toBe(true);
    expect(isRunExecution(runningPayload)).toBe(true);
  });

  it("keeps the request, the state at T, the state over the step and the output apart", async () => {
    renderWith(asExecution(startingPayload));
    await settledScreen();

    expect(
      screen.getByRole("heading", { name: "The generator at this step" }),
    ).toBeTruthy();
    expect(text("[data-generator-request]")).toBe("RUN");
    expect(text("[data-generator-state-at-t]")).toBe("STOPPED");
    expect(text("[data-generator-state-for-step]")).toBe("STARTING");
    expect(text("[data-generator-output]")).toBe("0 kW");
    const transitions = document.querySelectorAll(
      "[data-generator-transition]",
    );
    expect(transitions.length).toBe(1);
    expect(transitions[0]?.textContent).toContain("physical-acceptance");
  });

  it("shows a running generator's output, fuel and transitions", async () => {
    renderWith(asExecution(runningPayload));
    await settledScreen();

    expect(text("[data-generator-state-for-step]")).toBe("RUNNING");
    expect(text("[data-generator-output]")).toBe("40 kW");
    expect(
      document.querySelector('[data-generator-transition="RUNNING"]')
        ?.textContent,
    ).toContain("apply-events");
    expect(text("[data-generator-fuel-end]")).toMatch(/L$/);
    expect(document.querySelectorAll("[data-generator-step]").length).toBe(
      runningPayload.electrical.generator.steps.length,
    );
  });

  it("says the reported status is pending rather than leaving it out", async () => {
    renderWith(asExecution(runningPayload));
    await settledScreen();

    expect(text("[data-generator-reported-status]")).toContain("pending T025b");
  });

  it("shows no generator panels for a daytime run", async () => {
    renderWith(asExecution(overcastPayload));
    await settledScreen();

    expect(
      screen.queryByRole("heading", { name: "The generator at this step" }),
    ).toBeNull();
    expect(document.body.textContent).toContain(
      "This model does not run the generator; the mini-grid model does.",
    );
  });
});

describe("the generator guard keeps closed, typed enums", () => {
  function generator(): Record<string, unknown> {
    return structuredClone(
      (runningPayload as { electrical: { generator: Record<string, unknown> } })
        .electrical.generator,
    );
  }
  type Row = Record<string, unknown>;
  const slots: Array<[string, (g: Record<string, unknown>) => Row, string]> = [
    ["state_at_t", (g) => (g.steps as Row[])[0], "state_at_t"],
    ["state_for_step", (g) => (g.steps as Row[])[0], "state_for_step"],
    ["step request", (g) => (g.steps as Row[])[0], "requested"],
    ["transition previous", (g) => (g.transitions as Row[])[0], "previous"],
    ["transition next", (g) => (g.transitions as Row[])[0], "next"],
  ];

  it("accepts the recorded generator", () => {
    expect(isRunGenerator(generator())).toBe(true);
  });

  it.each(slots)("refuses an unknown or numeric %s", (_name, locate, key) => {
    for (const bad of ["BANANA", 1]) {
      const g = generator();
      locate(g)[key] = bad;
      expect(isRunGenerator(g)).toBe(false);
    }
  });

  it("keeps the request vocabulary apart from the lifecycle", () => {
    const g = generator();
    (g.steps as Row[])[0].requested = "RUNNING";
    expect(isRunGenerator(g)).toBe(false);
    const h = generator();
    (h.steps as Row[])[0].state_at_t = "RUN";
    expect(isRunGenerator(h)).toBe(false);
  });
});
