import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

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
import type { RunHistory, RunHistoryDeltaResult, RunHistoryResult } from "../runHistory";
import {
  INTERRUPTED,
  NOT_RECORDED,
  RUNNING_IN_THE_GAP,
  executionMethods,
} from "./executionFixtures";

/**
 * T025e AC11: every render of the run-bound drawing binds its Site once, so
 * counting `bindDrawing` counts the drawing's renders - a memo hit calls
 * nothing. The real function still answers.
 */
const drawingRenders = vi.hoisted(() => ({ count: 0 }));
vi.mock("../intervalDrawingModel", async (importOriginal) => {
  const real = await importOriginal<typeof import("../intervalDrawingModel")>();
  return {
    ...real,
    bindDrawing: (...args: Parameters<typeof real.bindDrawing>) => {
      drawingRenders.count += 1;
      return real.bindDrawing(...args);
    },
  };
});

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

/**
 * T025e: the history a live session has recorded after `count` boundaries -
 * one boundary per completed step, as the host records it. `since` narrows it
 * to a delta exactly as the route does.
 */
function recordedHistory(
  start: RunExecution,
  count: number,
  status: string,
  since = 0,
): RunHistory {
  const step = start.timestep_minutes;
  const boundaries = Array.from({ length: count - since }, (_, i) => ({
    step_index: since + i,
    offset_minutes: (since + i) * step,
    simulation_time: `boundary ${since + i}`,
    has_preceding_interval: since + i > 0,
  }));
  return {
    ...NOT_RECORDED,
    run_id: start.run_id,
    inputs_identity: start.inputs_identity,
    status,
    source: "LIVE_SESSION",
    statement: "Recorded by the live session.",
    boundaries_total: TOTAL,
    boundaries_recorded: count,
    recorded_through_offset_minutes: count === 0 ? null : (count - 1) * step,
    boundaries,
  };
}

/** A host with one live execution, stepped only from where it is. */
function host(start: RunExecution = RUNNING_IN_THE_GAP) {
  let position = start.boundaries_completed;
  let status = start.status;
  const log = {
    steps: [] as number[],
    historyReads: 0,
    deltaReads: [] as number[],
    stageReads: 0,
  };
  /** Delta reads (by their since count) that answer as unavailable. */
  const failDeltasFrom = new Set<number>();
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
    getExecutionHistory: (): Promise<RunHistoryResult> => {
      log.historyReads += 1;
      return Promise.resolve({
        status: "loaded",
        history: recordedHistory(start, position, status),
      });
    },
    getExecutionHistorySince: (_runId: string, since: number): Promise<RunHistoryDeltaResult> => {
      log.deltaReads.push(since);
      if (failDeltasFrom.has(since)) {
        return Promise.resolve({ status: "unavailable", message: null });
      }
      return Promise.resolve({
        status: "loaded",
        history: {
          ...recordedHistory(start, position, status, since),
          coverage: NOT_RECORDED.coverage,
        },
        delta: { since_boundary: since, through_boundary: position },
      });
    },
  };
  return {
    client,
    log,
    /** Another tab steps the run. */
    advanceElsewhere: () => {
      position += 1;
    },
    failDeltasFrom,
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

  it("plays one guarded step at a time to the end, following the history by deltas and one terminal read", async () => {
    const h = host();
    renderAt(h.client);
    await settled();
    // The one full read on load.
    await waitFor(() => expect(h.log.historyReads).toBe(1));
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
    // T025e: a delta per RUNNING answer, and one full read at the terminal
    // answer - none between the first step and the terminal.
    expect(h.log.deltaReads).toEqual([104, 105]);
    expect(h.log.historyReads).toBe(2);
    expect(document.querySelector("[data-history-recorded]")?.textContent).toBe(
      "107 of 107",
    );
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

function recordedCount(): string | null {
  return document.querySelector("[data-history-recorded]")?.textContent ?? null;
}

function lag(): HTMLElement {
  const found = document.querySelector<HTMLElement>("[data-history-lag]");
  if (found === null) {
    throw new Error("no lag slot");
  }
  return found;
}

describe("live follow on the run screen (T025e AC4-AC7)", () => {
  it("each auto-played step commits its history with it, and a failed read never stops play", async () => {
    const h = host({ ...RUNNING_IN_THE_GAP, boundaries_completed: 100 });
    h.failDeltasFrom.add(101);
    renderAt(h.client);
    await settled();
    await waitFor(() => expect(recordedCount()).toBe("100 of 107"));
    fastest();
    fireEvent.click(screen.getByRole("button", { name: "Play" }));
    // The delta after 101 fails: the last frame stays, and the lag is stated.
    await waitFor(() =>
      expect(lag().textContent).toBe(
        "History recorded through boundary 101; execution at 102.",
      ),
    );
    expect(recordedCount()).toBe("101 of 107");
    // Play went on, and the next tick made one full read, not the same delta.
    await waitFor(
      () => expect(playback().getAttribute("data-playback-reason")).toBe("TERMINAL"),
      { timeout: 4000 },
    );
    expect(h.log.steps).toEqual([100, 101, 102, 103, 104, 105, 106]);
    expect(h.log.deltaReads).toEqual([100, 101, 103, 104, 105]);
    // Load, the recovery after the failed delta, and the terminal read.
    expect(h.log.historyReads).toBe(3);
    expect(recordedCount()).toBe("107 of 107");
    expect(lag().getAttribute("data-history-lag")).toBe("none");
  });

  it("a pinned cursor holds while play continues, and Return to live resumes following", async () => {
    const h = host({ ...RUNNING_IN_THE_GAP, boundaries_completed: 100 });
    renderAt(h.client);
    await settled();
    await waitFor(() => expect(recordedCount()).toBe("100 of 107"));
    const range = document.getElementById("history-cursor-range") as HTMLInputElement;
    // Pin boundary 97 (offset 97 x 15 min).
    fireEvent.change(range, { target: { value: "97" } });
    const pinned = String(97 * RUNNING_IN_THE_GAP.timestep_minutes);
    expect(document.querySelector("[data-cursor-offset]")?.getAttribute("data-cursor-offset")).toBe(pinned);
    expect(screen.getByRole("button", { name: /Return to live \(2 boundaries behind live\)/ })).toBeEnabled();

    fastest();
    fireEvent.click(screen.getByRole("button", { name: "Play" }));
    await waitFor(() => expect(recordedCount()).toBe("103 of 107"), { timeout: 3000 });
    fireEvent.click(screen.getByRole("button", { name: "Pause" }));
    await waitFor(() =>
      expect(playback().getAttribute("data-playback-reason")).toBe("PAUSED"),
    );
    // Neither the ticks nor the pause moved the pinned cursor, on any view.
    expect(document.querySelector("[data-cursor-offset]")?.getAttribute("data-cursor-offset")).toBe(pinned);
    expect(document.querySelector("[data-history-selected]")?.getAttribute("data-history-selected")).toBe(pinned);
    const recorded = Number(recordedCount()?.split(" ")[0]);
    expect(
      screen.getByRole("button", {
        name: `Return to live (${recorded - 98} boundaries behind live)`,
      }),
    ).toBeEnabled();

    fireEvent.click(screen.getByRole("button", { name: /Return to live/ }));
    const live = String((recorded - 1) * RUNNING_IN_THE_GAP.timestep_minutes);
    expect(document.querySelector("[data-cursor-offset]")?.getAttribute("data-cursor-offset")).toBe(live);
    expect(document.querySelector("[data-history-cursor]")?.getAttribute("data-history-cursor")).toBe("live");
    expect(screen.queryByRole("button", { name: /Return to live/ })).toBeNull();
  });

  it("a manual Step commits the same way: one delta, no full read", async () => {
    const h = host({ ...RUNNING_IN_THE_GAP, boundaries_completed: 100 });
    renderAt(h.client);
    await settled();
    await waitFor(() => expect(recordedCount()).toBe("100 of 107"));
    fireEvent.click(screen.getByRole("button", { name: "Step" }));
    await waitFor(() => expect(recordedCount()).toBe("101 of 107"));
    expect(h.log.deltaReads).toEqual([100]);
    expect(h.log.historyReads).toBe(1);
    expect(document.querySelector("[data-history-cursor]")?.getAttribute("data-history-cursor")).toBe("live");
  });
});

describe("no intermediate frames (T025e AC11)", () => {
  it("a pinned cursor re-renders no drawing across ticks; a live one re-renders it each tick", async () => {
    const h = host({ ...RUNNING_IN_THE_GAP, boundaries_completed: 100 });
    renderAt(h.client);
    await settled();
    await waitFor(() => expect(recordedCount()).toBe("100 of 107"));
    const range = document.getElementById("history-cursor-range") as HTMLInputElement;
    fireEvent.change(range, { target: { value: "97" } });
    const drawing = document.querySelector("[data-drawing-boundary]") as HTMLElement;

    const pinnedFrom = drawingRenders.count;
    fastest();
    fireEvent.click(screen.getByRole("button", { name: "Play" }));
    await waitFor(() => expect(recordedCount()).toBe("103 of 107"), { timeout: 3000 });
    // Three ticks committed history, and the pinned drawing did not render.
    expect(drawingRenders.count).toBe(pinnedFrom);
    // Nor was it replaced: the same node, at the same boundary.
    expect(document.querySelector("[data-drawing-boundary]")).toBe(drawing);

    fireEvent.click(screen.getByRole("button", { name: /Return to live/ }));
    const liveFrom = drawingRenders.count;
    await waitFor(() => expect(recordedCount()).toBe("105 of 107"), { timeout: 3000 });
    // Live, the drawing follows: it rendered at least once per tick.
    expect(drawingRenders.count - liveFrom).toBeGreaterThanOrEqual(2);
    expect(document.querySelector("[data-drawing-boundary]")).toBe(drawing);
  });

  it("plays under one stable status sentence; in flight is an attribute, not a second text", async () => {
    const h = host({ ...RUNNING_IN_THE_GAP, boundaries_completed: 100 });
    renderAt(h.client);
    await settled();
    const status = document.querySelector("[data-playback-statement]") as HTMLElement;
    const texts = new Set<string>();
    const inFlight = new Set<string>();
    const observer = new MutationObserver(() => {
      texts.add(status.textContent ?? "");
      inFlight.add(status.getAttribute("data-playback-in-flight") ?? "");
    });
    observer.observe(status, { attributes: true, childList: true, characterData: true, subtree: true });
    fastest();
    fireEvent.click(screen.getByRole("button", { name: "Play" }));
    await waitFor(() => expect(recordedCount()).toBe("104 of 107"), { timeout: 3000 });
    fireEvent.click(screen.getByRole("button", { name: "Pause" }));
    await waitFor(() =>
      expect(playback().getAttribute("data-playback-reason")).toBe("PAUSED"),
    );
    observer.disconnect();
    const playing = [...texts].filter((t) => t.includes("Playing"));
    expect(playing).toEqual(["Playback: Playing: one step, its record, then the wall delay."]);
    // The attribute did flip, so the observer saw the ticks.
    expect(inFlight).toContain("yes");
    expect(inFlight).toContain("no");
    // The same node throughout: nothing remounted.
    expect(document.querySelector("[data-playback-statement]")).toBe(status);
  });
});
