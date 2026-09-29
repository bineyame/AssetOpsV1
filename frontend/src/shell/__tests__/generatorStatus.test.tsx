import { render } from "@testing-library/react";
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
import runningPayload from "./kobo-mini-grid-running-execution.json";
import stopSixtyPayload from "./kobo-mini-grid-stop-60-execution.json";

/**
 * T025b: a `mini-grid` v2 run under publication profile 4 on the run screen.
 *
 * `kobo-mini-grid-stop-60-execution.json` was produced by the real backend:
 * `execution_payload` over the host Lab port, for a Draft of the shipped
 * `kobo-mini-grid-stop-60` scenario frozen by the real run setup service
 * (`host/tests/test_generator_observation.py` `draft()`: mini-grid v2,
 * profile 4, 03:00Z-11:00Z at 5-minute steps), stepped to offset 250. That is
 * the boundary the overridden 60 % stop threshold is met: the request is STOP,
 * the state at T is RUNNING, the state over the step is STOPPED - and the
 * newest status reading is the 07:00Z sample, a STALE "RUNNING". The two
 * effective controls are the baseline reserve and the overridden stop
 * threshold.
 */

const RUN_ID = "run-kobo-mini-grid-stop-60";
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
  scenario_id: "kobo-mini-grid-stop-60",
  scenario_version: 1,
  frozen_inputs: [],
  blocking_reasons: [],
  unsupported_optional_inputs: [],
};

type Row = Record<string, unknown>;

function payload(): Row {
  return structuredClone(stopSixtyPayload) as Row;
}

function asExecution(value: unknown): RunExecution {
  if (!isRunExecution(value)) {
    throw new Error("the recorded payload no longer matches the client guard");
  }
  return value;
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
      <App flags={ENABLED} siteDirectory={EMPTY_SITE_DIRECTORY} runSetup={runSetup} />
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

function steps(value: Row): Row[] {
  return ((value.electrical as Row).generator as Row).steps as Row[];
}

function statusRow(value: Row, collection: string): Row {
  const found = (value[collection] as Row[]).find(
    (row) => row.device_id === "generator-controller" && row.signal_id === "status",
  );
  if (found === undefined) {
    throw new Error(`no status row in ${collection}`);
  }
  return found;
}

describe("a profile-4 generator run on the Draft run screen", () => {
  it("accepts the recorded backend payload through the client guard", () => {
    expect(isRunExecution(stopSixtyPayload)).toBe(true);
    expect(stopSixtyPayload.publication_profile_version).toBe(4);
    expect(stopSixtyPayload.model_profile_version).toBe(2);
  });

  it("shows the reported status beside the physical state, never in its place", async () => {
    renderWith(asExecution(stopSixtyPayload));
    await settledScreen();

    expect(text("[data-generator-request]")).toBe("STOP");
    expect(text("[data-generator-state-at-t]")).toBe("RUNNING");
    expect(text("[data-generator-state-for-step]")).toBe("STOPPED");
    expect(text("[data-generator-reported-state]")).toBe("RUNNING (STALE)");
    const disclosure = text("[data-generator-reported-status]");
    expect(disclosure).toContain("publication profile 4");
    expect(disclosure).toContain("not yet staged");
  });

  it("puts a reported-status column in the series, with GOOD and STALE both present", async () => {
    renderWith(asExecution(stopSixtyPayload));
    await settledScreen();

    const cells = Array.from(
      document.querySelectorAll("[data-generator-step-reported]"),
    );
    expect(cells.length).toBe(steps(payload()).length);
    const qualities = new Set(
      cells.map((cell) => cell.getAttribute("data-generator-step-reported")),
    );
    expect(qualities.has("GOOD")).toBe(true);
    expect(qualities.has("STALE")).toBe(true);
    const last = document.querySelector('[data-generator-step="250"]');
    expect(last?.textContent).toContain("RUNNING (STALE)");
    expect(last?.textContent).toContain("STOPPED");
  });

  it("names both controls in effect by address: the reserve and the stop threshold", async () => {
    renderWith(asExecution(stopSixtyPayload));
    await settledScreen();

    const rows = Array.from(
      document.querySelectorAll("[data-effective-control-address]"),
    );
    expect(rows.map((row) => row.getAttribute("data-effective-control-address"))).toEqual([
      "battery-reserve-state-of-charge@battery",
      "generator-stop-soc-threshold@generator",
    ]);
    const stop = rows[1];
    expect(stop?.getAttribute("data-effective-control")).toBe("OVERRIDE");
    expect(stop?.textContent).toContain("generator-stop-soc-threshold in effect");
    expect(stop?.textContent).toContain("60 %");
    expect(stop?.textContent).toContain("scenario override stop-threshold-override");
    expect(rows[0]?.textContent).not.toContain("stop");
  });

  it("shows the status reading as a member, not a number with a unit", async () => {
    renderWith(asExecution(stopSixtyPayload));
    await settledScreen();

    const observed = document.querySelector(
      '[data-observation="generator-controller:status"]',
    );
    expect(observed?.querySelector("[data-observation-true]")?.textContent).toBe(
      "RUNNING",
    );
    expect(observed?.querySelector("[data-observation-quality]")?.textContent).toBe(
      "STALE",
    );
    const attempts = Array.from(
      document.querySelectorAll('[data-sample-attempt^="generator-controller:status:"]'),
    );
    expect(attempts.length).toBeGreaterThan(0);
    for (const attempt of attempts) {
      expect(attempt.textContent).not.toMatch(/ state\b/);
    }
  });

  it("says in the stage panel that the status is observed and not staged", async () => {
    renderWith(asExecution(stopSixtyPayload));
    await settledScreen();

    const unstaged = document.querySelectorAll("[data-stage-unstaged-signal]");
    expect(Array.from(unstaged, (item) => item.getAttribute("data-stage-unstaged-signal"))).toEqual([
      "generator-controller:status",
    ]);
    expect(unstaged[0]?.textContent).toContain("T026");
  });

  it("keeps a profile-3 run's table and says it publishes no status", async () => {
    renderWith(asExecution(runningPayload));
    await settledScreen();

    expect(document.querySelectorAll("[data-generator-step-reported]").length).toBe(0);
    expect(text("[data-generator-reported-state]")).toBe("not published by this run");
    expect(document.querySelectorAll("[data-stage-unstaged-signal]").length).toBe(0);
  });
});

describe("the guards keep a reported status typed", () => {
  it.each([
    ["an unknown member", { reported_state: "BANANA" }],
    ["a numeric member", { reported_state: 1 }],
    ["an unknown quality", { reported_quality: "FRESH" }],
    ["a member with no quality", { reported_quality: null }],
    ["a missing member field", { reported_state: undefined }],
  ])("refuses a generator step with %s", (_name, change) => {
    const value = payload();
    const generator = (value.electrical as Row).generator as Row;
    Object.assign(steps(value)[0] as Row, change);
    expect(isRunGenerator(generator)).toBe(false);
    expect(isRunExecution(value)).toBe(false);
  });

  it("accepts UNAVAILABLE with no member, and no status at all", () => {
    for (const change of [
      { reported_state: null, reported_quality: "UNAVAILABLE" },
      { reported_state: null, reported_quality: null },
    ]) {
      const value = payload();
      Object.assign(steps(value)[0] as Row, change);
      expect(isRunExecution(value)).toBe(true);
    }
  });

  it.each([
    ["observations", "true_value", "1"],
    ["observations", "reported_value", "0.5"],
    ["observations", "bias", "0.5"],
    ["recent_reports", "reported_value", "1"],
    ["signals", "bias", "1"],
  ])("refuses a status disguised as a number in %s.%s", (collection, key, bad) => {
    const value = payload();
    statusRow(value, collection)[key] = bad;
    expect(isRunExecution(value)).toBe(false);
  });
});
