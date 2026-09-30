import { describe, expect, it } from "vitest";

import {
  PlaybackScheduler,
  laterExecution,
  type PlaybackState,
  type PlaybackStopReason,
  type PlaybackTimers,
} from "../runPlayback";
import type { RunExecution, RunExecutionResult } from "../runSetupClient";
import { RUNNING_IN_THE_GAP } from "./executionFixtures";

/**
 * T025d criterion 5-6: the auto-play scheduler, driven by hand.
 *
 * Timers and responses are both manual here, so every claim is about ORDER:
 * what was sent, when the next request was allowed, and what was shown. A
 * scheduler that fired on a clock rather than on the previous answer would send
 * a second request while the first is unanswered, and `inFlightAtOnce` below
 * would catch it.
 */

function at(boundaries: number, status = "RUNNING"): RunExecution {
  return { ...RUNNING_IN_THE_GAP, status, boundaries_completed: boundaries };
}

function loaded(boundaries: number, status = "RUNNING"): RunExecutionResult {
  return { status: "loaded", execution: at(boundaries, status) };
}

interface Deferred {
  from: number;
  resolve(answer: RunExecutionResult): void;
}

class ManualTimers implements PlaybackTimers {
  private next = 1;
  readonly pending = new Map<number, { callback: () => void; ms: number }>();
  set(callback: () => void, ms: number): unknown {
    const id = this.next++;
    this.pending.set(id, { callback, ms });
    return id;
  }
  clear(handle: unknown): void {
    this.pending.delete(handle as number);
  }
  /** Fire every pending timer with this delay. */
  fire(ms: number): void {
    for (const [id, timer] of [...this.pending]) {
      if (timer.ms === ms) {
        this.pending.delete(id);
        timer.callback();
      }
    }
  }
}

const TIMEOUT = 20000;

function harness(readAnswer: RunExecutionResult = loaded(0)) {
  const timers = new ManualTimers();
  const steps: Deferred[] = [];
  const shown: RunExecutionResult[] = [];
  const states: PlaybackState[] = [];
  const stopped: PlaybackStopReason[] = [];
  let reads = 0;
  let open = 0;
  let inFlightAtOnce = 0;
  const scheduler = new PlaybackScheduler({
    step: (from) => {
      open += 1;
      inFlightAtOnce = Math.max(inFlightAtOnce, open);
      return new Promise<RunExecutionResult>((resolve) => {
        steps.push({
          from,
          resolve: (answer) => {
            open -= 1;
            resolve(answer);
          },
        });
      });
    },
    read: () => {
      reads += 1;
      return Promise.resolve(readAnswer);
    },
    show: (answer) => shown.push(answer),
    onState: (state) => states.push(state),
    onStopped: (reason) => stopped.push(reason),
    timers,
    stepTimeoutMs: TIMEOUT,
  });
  scheduler.setDelay(1000);
  return {
    scheduler,
    timers,
    steps,
    shown,
    states,
    stopped,
    reads: () => reads,
    inFlightAtOnce: () => inFlightAtOnce,
  };
}

const flush = () => new Promise<void>((resolve) => setTimeout(resolve, 0));

describe("the auto-play scheduler", () => {
  it("sends one guarded step at a time and the next only after the answer and the delay", async () => {
    const h = harness();
    expect(h.scheduler.play(at(10))).toBe(true);
    expect(h.steps.map((s) => s.from)).toEqual([10]);
    // No answer yet: the delay timer is not even set, only the timeout.
    h.timers.fire(1000);
    expect(h.steps).toHaveLength(1);

    h.steps[0].resolve(loaded(11));
    await flush();
    expect(h.shown).toEqual([loaded(11)]);
    expect(h.steps).toHaveLength(1);
    h.timers.fire(1000);
    expect(h.steps.map((s) => s.from)).toEqual([10, 11]);
    h.steps[1].resolve(loaded(12));
    await flush();
    h.timers.fire(1000);
    expect(h.steps.map((s) => s.from)).toEqual([10, 11, 12]);
    expect(h.inFlightAtOnce()).toBe(1);
  });

  it("refuses to start from anything but a RUNNING execution", () => {
    const h = harness();
    expect(h.scheduler.play(at(0, "NOT_STARTED"))).toBe(false);
    expect(h.scheduler.play(at(97, "COMPLETED"))).toBe(false);
    expect(h.scheduler.play(at(4, "INTERRUPTED"))).toBe(false);
    expect(h.scheduler.play(null)).toBe(false);
    expect(h.steps).toHaveLength(0);
  });

  it("pause cancels the next request but shows the step already sent", async () => {
    const h = harness();
    h.scheduler.play(at(10));
    h.scheduler.pause();
    expect(h.scheduler.current()).toEqual({ kind: "pausing" });
    h.steps[0].resolve(loaded(11));
    await flush();
    expect(h.shown).toEqual([loaded(11)]);
    expect(h.scheduler.current()).toMatchObject({
      kind: "stopped",
      reason: "PAUSED",
    });
    h.timers.fire(1000);
    h.timers.fire(TIMEOUT);
    expect(h.steps).toHaveLength(1);
    // A pause is not an error: nothing is re-read.
    expect(h.reads()).toBe(0);
    expect(h.stopped).toEqual(["PAUSED"]);
  });

  it("pause during the wall delay sends nothing further", async () => {
    const h = harness();
    h.scheduler.play(at(10));
    h.steps[0].resolve(loaded(11));
    await flush();
    h.scheduler.pause();
    h.timers.fire(1000);
    expect(h.steps).toHaveLength(1);
    expect(h.scheduler.current()).toMatchObject({ reason: "PAUSED" });
  });

  it("stops at a terminal status", async () => {
    const h = harness();
    h.scheduler.play(at(96));
    h.steps[0].resolve(loaded(97, "COMPLETED"));
    await flush();
    h.timers.fire(1000);
    expect(h.steps).toHaveLength(1);
    expect(h.scheduler.current()).toMatchObject({ reason: "TERMINAL" });
  });

  it.each([
    [
      "STEP_ALREADY_APPLIED",
      {
        status: "refused",
        code: "STEP_ALREADY_APPLIED",
        refusalKind: "STEP_ALREADY_APPLIED",
        message: "The run is not at boundary 10.",
      },
    ],
    [
      "REFUSED",
      {
        status: "refused",
        code: "INTERRUPTED",
        refusalKind: "INTERRUPTED",
        message: "This execution was interrupted.",
      },
    ],
    ["NOT_FOUND", { status: "not_found" }],
    ["NETWORK", { status: "unavailable", message: null }],
  ] as [PlaybackStopReason, RunExecutionResult][])(
    "stops on %s, re-reads the authoritative position and does not retry",
    async (reason, answer) => {
      const h = harness(loaded(12));
      h.scheduler.play(at(10));
      h.steps[0].resolve(answer);
      await flush();
      expect(h.scheduler.current()).toMatchObject({ kind: "stopped", reason });
      expect(h.reads()).toBe(1);
      // The refusal itself is not shown as the execution; the re-read is.
      expect(h.shown).toEqual([loaded(12)]);
      expect(h.stopped).toEqual([reason]);
      h.timers.fire(1000);
      h.timers.fire(TIMEOUT);
      expect(h.steps).toHaveLength(1);
      // Resuming is explicit, and from the re-read position.
      expect(h.scheduler.play(at(12))).toBe(true);
      expect(h.steps.map((s) => s.from)).toEqual([10, 12]);
    },
  );

  it("a timeout stops, re-reads, and shows a late accepted answer without scheduling from it", async () => {
    const h = harness(loaded(10));
    h.scheduler.play(at(10));
    h.timers.fire(TIMEOUT);
    await flush();
    expect(h.scheduler.current()).toMatchObject({ reason: "TIMEOUT" });
    expect(h.reads()).toBe(1);
    // The step answers late: it was accepted, so it is shown ...
    h.steps[0].resolve(loaded(11));
    await flush();
    expect(h.shown).toEqual([loaded(10), loaded(11)]);
    // ... and nothing is scheduled from it: no catch-up burst.
    h.timers.fire(1000);
    h.timers.fire(TIMEOUT);
    expect(h.steps).toHaveLength(1);
    expect(h.scheduler.current()).toMatchObject({ reason: "TIMEOUT" });
  });

  it("a hidden tab stops scheduling but still shows the step in flight", async () => {
    const h = harness();
    h.scheduler.play(at(10));
    h.scheduler.hidden();
    h.steps[0].resolve(loaded(11));
    await flush();
    expect(h.shown).toEqual([loaded(11)]);
    expect(h.scheduler.current()).toMatchObject({ reason: "HIDDEN" });
    h.timers.fire(1000);
    expect(h.steps).toHaveLength(1);
  });

  it("leaving the page stops scheduling and shows nothing further", async () => {
    const h = harness();
    h.scheduler.play(at(10));
    h.scheduler.dispose();
    h.steps[0].resolve(loaded(11));
    await flush();
    h.timers.fire(1000);
    expect(h.shown).toEqual([]);
    expect(h.steps).toHaveLength(1);
    expect(h.scheduler.play(at(11))).toBe(false);
  });

  it("changing the pacing changes the wall delay and nothing in the request", async () => {
    const h = harness();
    h.scheduler.setDelay(5000);
    h.scheduler.play(at(10));
    h.steps[0].resolve(loaded(11));
    await flush();
    h.timers.fire(1000);
    expect(h.steps).toHaveLength(1);
    h.timers.fire(5000);
    expect(h.steps.map((s) => s.from)).toEqual([10, 11]);
  });
});

describe("which execution answer is displayed", () => {
  it("never moves the displayed position backwards", () => {
    expect(laterExecution(loaded(12), loaded(11))).toEqual(loaded(12));
    expect(laterExecution(loaded(11), loaded(12))).toEqual(loaded(12));
    expect(laterExecution(null, loaded(3))).toEqual(loaded(3));
  });

  it("shows news that is not a position as it is", () => {
    const refused: RunExecutionResult = {
      status: "refused",
      code: "X",
      refusalKind: "X",
      message: "m",
    };
    expect(laterExecution(loaded(12), refused)).toEqual(refused);
  });
});
