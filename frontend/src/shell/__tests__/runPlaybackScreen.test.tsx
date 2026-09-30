import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { App } from "../../App";
import { featureFlagsWith } from "../../config/featureFlags";
import type { SiteDirectoryClient } from "../../sites/siteDirectoryClient";
import { settledScreen } from "../../test/settled";
import type {
  RunExecution,
  RunExecutionResult,
  RunSetupClient,
  RunStepRequest,
  RunSummary,
} from "../runSetupClient";
import {
  INTERRUPTED,
  RUNNING_IN_THE_GAP,
  executionMethods,
} from "./executionFixtures";

/**
 * T025d criteria 5-7 on the run screen: auto-play composed over the real
 * guarded Step, against a fake host that keeps a position and refuses a step
 * from the wrong boundary exactly as the port does.
 */

const RUN_ID = "run-1f0c2b7a4e5d4c8fa1b2c3d4e5f60718";
const URL = `/simulator-lab/runs/${RUN_ID}`;
const ENABLED = featureFlagsWith(true);
const EMPTY_SITE_DIRECTORY: SiteDirectoryClient = {
  listSites: () => Promise.resolve({ status: "loaded", sites: [] }),
};

const READY_RUN: RunSummary = {
  run_id: RUN_ID,
  lifecycle_status: "DRAFT",
  execution_status: "READY",
  readiness_disclosure: null,
  created_at: "2026-09-22T09:00:00Z",
  site_id: "MG-001",
  scenario_id: "fuel-loss-event",
  scenario_version: 1,
  frozen_inputs: [],
  blocking_reasons: [],
  unsupported_optional_inputs: [],
};

const TOTAL = 107;

/** A host with one live execution, stepped only from where it is. */
function host(start: RunExecution = RUNNING_IN_THE_GAP) {
  let position = start.boundaries_completed;
  let status = start.status;
  const log = { steps: [] as number[], historyReads: 0, stageReads: 0 };
  const now = (): RunExecutionResult => ({
    status: "loaded",
    execution: {
      ...start,
      status,
      boundaries_total: TOTAL,
      boundaries_completed: position,
      offset_minutes: position * start.timestep_minutes,
    },
  });
  const base = executionMethods();
  const client: RunSetupClient = {
    listProfiles: () => Promise.resolve({ status: "unavailable" }),
    createRun: () => Promise.resolve({ status: "unavailable", message: null }),
    listRuns: () => Promise.resolve({ status: "loaded", runs: [] }),
    getRun: () => Promise.resolve({ status: "loaded", run: READY_RUN }),
    ...base,
    getExecution: () => Promise.resolve(now()),
    stepExecution: (_runId: string, request: RunStepRequest) => {
      log.steps.push(request.fromBoundary);
      if (status !== "RUNNING") {
        return Promise.resolve({
          status: "refused",
          code: "ALREADY_TERMINAL",
          refusalKind: "ALREADY_TERMINAL",
          message: "This execution accepts no further step.",
        });
      }
      if (request.fromBoundary !== position) {
        return Promise.resolve({
          status: "refused",
          code: "STEP_ALREADY_APPLIED",
          refusalKind: "STEP_ALREADY_APPLIED",
          message: `The run is at boundary ${position}, not ${request.fromBoundary}.`,
        });
      }
      position += request.boundaries;
      if (position >= TOTAL) {
        position = TOTAL;
        status = "COMPLETED";
      }
      return Promise.resolve(now());
    },
    getStage: (runId) => {
      log.stageReads += 1;
      return base.getStage(runId);
    },
    getExecutionHistory: (runId) => {
      log.historyReads += 1;
      return base.getExecutionHistory(runId);
    },
  };
  return {
    client,
    log,
    /** Another tab steps the run. */
    advanceElsewhere: () => {
      position += 1;
    },
  };
}

function renderAt(runSetup: RunSetupClient) {
  return render(
    <MemoryRouter initialEntries={[URL]}>
      <App
        flags={ENABLED}
        siteDirectory={EMPTY_SITE_DIRECTORY}
        runSetup={runSetup}
      />
    </MemoryRouter>,
  );
}

function playback(): HTMLElement {
  const found = document.querySelector("[data-playback-state]");
  if (found === null) {
    throw new Error("no playback region");
  }
  return found as HTMLElement;
}

function executionStatus(): string | null {
  return (
    document
      .querySelector("[data-execution-statement]")
      ?.getAttribute("data-execution-status") ?? null
  );
}

async function settled() {
  await settledScreen();
  await waitFor(() => expect(executionStatus()).not.toBeNull());
}

function fastest() {
  fireEvent.change(screen.getByLabelText("Wall delay between steps"), {
    target: { value: "250" },
  });
}

describe("auto-play on the run screen", () => {
  it("a reload starts paused and sends nothing until Play", async () => {
    const h = host();
    renderAt(h.client);
    await settled();
    expect(playback().getAttribute("data-playback-state")).toBe("stopped");
    expect(playback().textContent).toContain("a reload always starts paused");
    expect(screen.getByRole("button", { name: "Play" })).toBeEnabled();
    await new Promise((resolve) => setTimeout(resolve, 50));
    expect(h.log.steps).toEqual([]);
  });

  it("plays one guarded step at a time to the end, then stops and re-reads the records once", async () => {
    const h = host();
    renderAt(h.client);
    await settled();
    const readsBefore = h.log.historyReads;
    fastest();
    fireEvent.click(screen.getByRole("button", { name: "Play" }));
    // Manual controls cannot race it.
    expect(screen.getByRole("button", { name: "Step" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Run to the end" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Pause" })).toBeEnabled();
    await waitFor(
      () => expect(playback().getAttribute("data-playback-reason")).toBe("TERMINAL"),
      { timeout: 3000 },
    );
    expect(h.log.steps).toEqual([104, 105, 106]);
    expect(executionStatus()).toBe("COMPLETED");
    // The history was not read per step: once, after auto-play stopped.
    await waitFor(() => expect(h.log.historyReads).toBe(readsBefore + 1));
    expect(screen.queryByRole("button", { name: /Play|Resume/ })).toBeDisabled();
  });

  it("pause stops scheduling and keeps playback distinct from the execution status", async () => {
    const h = host();
    renderAt(h.client);
    await settled();
    fastest();
    fireEvent.click(screen.getByRole("button", { name: "Play" }));
    await waitFor(() => expect(h.log.steps.length).toBeGreaterThanOrEqual(1));
    fireEvent.click(screen.getByRole("button", { name: "Pause" }));
    await waitFor(() =>
      expect(playback().getAttribute("data-playback-reason")).toBe("PAUSED"),
    );
    const sent = h.log.steps.length;
    await new Promise((resolve) => setTimeout(resolve, 600));
    expect(h.log.steps).toHaveLength(sent);
    // Paused playback over a RUNNING execution: two facts, two places.
    expect(executionStatus()).toBe("RUNNING");
    expect(playback().getAttribute("data-playback-state")).toBe("stopped");
    expect(screen.getByRole("button", { name: "Step" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "Resume" })).toBeEnabled();
  });

  it("a second tab's step stops auto-play on STEP_ALREADY_APPLIED and requires explicit resume", async () => {
    const h = host();
    renderAt(h.client);
    await settled();
    h.advanceElsewhere();
    fireEvent.click(screen.getByRole("button", { name: "Play" }));
    await waitFor(() =>
      expect(playback().getAttribute("data-playback-reason")).toBe(
        "STEP_ALREADY_APPLIED",
      ),
    );
    expect(h.log.steps).toEqual([104]);
    // The authoritative position was re-read.
    await waitFor(() =>
      expect(document.body.textContent).toContain("105 of 107"),
    );
    expect(playback().textContent).toContain("resume explicitly");
    await new Promise((resolve) => setTimeout(resolve, 300));
    expect(h.log.steps).toEqual([104]);
  });

  it("an execution this host no longer holds cannot be played", async () => {
    const h = host(INTERRUPTED);
    renderAt(h.client);
    await settled();
    expect(screen.getByRole("button", { name: "Play" })).toBeDisabled();
    expect(playback().textContent).toContain(
      "Auto-play needs a RUNNING execution this host still holds",
    );
  });

  it("leaving the page stops scheduling", async () => {
    const h = host();
    const view = renderAt(h.client);
    await settled();
    fastest();
    fireEvent.click(screen.getByRole("button", { name: "Play" }));
    await waitFor(() => expect(h.log.steps.length).toBeGreaterThanOrEqual(1));
    view.unmount();
    const sent = h.log.steps.length;
    await new Promise((resolve) => setTimeout(resolve, 600));
    expect(h.log.steps).toHaveLength(sent);
  });

  it("a hidden tab pauses auto-play", async () => {
    const h = host();
    renderAt(h.client);
    await settled();
    fastest();
    fireEvent.click(screen.getByRole("button", { name: "Play" }));
    await waitFor(() => expect(h.log.steps.length).toBeGreaterThanOrEqual(1));
    const visibility = Object.getOwnPropertyDescriptor(
      Document.prototype,
      "visibilityState",
    );
    Object.defineProperty(document, "visibilityState", {
      configurable: true,
      get: () => "hidden",
    });
    try {
      act(() => {
        document.dispatchEvent(new Event("visibilitychange"));
      });
      await waitFor(() =>
        expect(playback().getAttribute("data-playback-reason")).toBe("HIDDEN"),
      );
    } finally {
      delete (document as unknown as Record<string, unknown>).visibilityState;
      if (visibility !== undefined) {
        Object.defineProperty(Document.prototype, "visibilityState", visibility);
      }
    }
    const sent = h.log.steps.length;
    await new Promise((resolve) => setTimeout(resolve, 600));
    expect(h.log.steps).toHaveLength(sent);
  });
});
