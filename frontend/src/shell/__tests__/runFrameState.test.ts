import { describe, expect, it } from "vitest";

import { APPEND_FAMILY_KEYS } from "../liveHistory";
import type {
  RunHistory,
  RunHistoryDeltaEnvelope,
  RunHistoryResult,
} from "../runHistory";
import {
  INITIAL,
  LIVE,
  boundariesBehindLive,
  historyLag,
  historyRequest,
  runFrameReducer,
  selectedOffset,
  type RunFrameAction,
  type RunFrameState,
} from "../runFrameState";
import type { RunExecution, RunExecutionResult } from "../runSetupClient";
import { RUNNING_IN_THE_GAP } from "./executionFixtures";
import wire from "./kobo-mini-grid-history-deltas.json";

/**
 * T025e AC4-AC7: the run page's one owner of a tick's commit, driven by the
 * backend's own live-follow answers (`kobo-mini-grid-history-deltas.json`:
 * the base after start, seven one-boundary deltas, and the full read at 7).
 */

interface DeltaRead {
  history: RunHistory;
  delta: RunHistoryDeltaEnvelope;
}

const fixture = wire as unknown as {
  base: RunHistory;
  deltas: DeltaRead[];
  jump: DeltaRead;
  full: RunHistory;
};

const copy = <T,>(value: T): T => JSON.parse(JSON.stringify(value)) as T;

function execution(boundaries: number, status = "RUNNING"): RunExecutionResult {
  const projection: RunExecution = {
    ...RUNNING_IN_THE_GAP,
    run_id: fixture.base.run_id,
    inputs_identity: fixture.base.inputs_identity,
    status,
    boundaries_completed: boundaries,
  };
  return { status: "loaded", execution: projection };
}

function reduce(state: RunFrameState, ...actions: RunFrameAction[]): RunFrameState {
  return actions.reduce(runFrameReducer, state);
}

const loaded = (history: RunHistory): RunHistoryResult => ({
  status: "loaded",
  history: copy(history),
});

/** The page after load at the base, then k auto-played ticks with deltas. */
function followed(k: number): RunFrameState {
  let state = reduce(
    INITIAL,
    { type: "EXECUTION_READ", execution: execution(0) },
    { type: "HISTORY_READ", result: loaded(fixture.base) },
  );
  for (let i = 0; i < k; i += 1) {
    const read = copy(fixture.deltas[i]);
    state = runFrameReducer(state, {
      type: "TICK_COMMITTED",
      execution: execution(i + 1),
      history: {
        kind: "delta",
        result: { status: "loaded", history: read.history, delta: read.delta },
      },
    });
  }
  return state;
}

function recorded(state: RunFrameState): number {
  const held = state.history;
  if (held === null || held.status !== "loaded") {
    throw new Error("no history held");
  }
  return held.history.boundaries_recorded;
}

function clock(state: RunFrameState): number {
  const shown = state.execution;
  if (shown === null || shown.status !== "loaded") {
    throw new Error("no execution held");
  }
  return shown.execution.boundaries_completed;
}

describe("one commit per tick holds execution and history together", () => {
  it("asks for a delta from what is held, and commits clock and history at once", () => {
    let state = followed(3);
    expect(historyRequest(state, execution(4))).toEqual({ kind: "delta", since: 3 });
    const read = copy(fixture.deltas[3]);
    state = runFrameReducer(state, {
      type: "TICK_COMMITTED",
      execution: execution(4),
      history: { kind: "delta", result: { status: "loaded", ...read } },
    });
    expect(clock(state)).toBe(4);
    expect(recorded(state)).toBe(4);
    expect(historyLag(state)).toBeNull();
  });

  it("asks for nothing when the history already records the answer (a late answer applies once)", () => {
    const state = followed(5);
    // A late step answer at 5 and the stop's re-read at 5 need no read.
    expect(historyRequest(state, execution(5))).toEqual({ kind: "none" });
    expect(historyRequest(state, execution(4))).toEqual({ kind: "none" });
    const again = runFrameReducer(state, {
      type: "TICK_COMMITTED",
      execution: execution(4),
      history: { kind: "none" },
    });
    // Never backwards, and the history is the same object.
    expect(clock(again)).toBe(5);
    expect(again.history).toBe(state.history);
  });

  it("makes a whole read when nothing is held, and none for a refusal answer", () => {
    expect(historyRequest(INITIAL, execution(2))).toEqual({ kind: "full" });
    expect(
      historyRequest(followed(2), {
        status: "refused",
        code: "STEP_ALREADY_APPLIED",
        refusalKind: "STEP_ALREADY_APPLIED",
        message: "m",
      }),
    ).toEqual({ kind: "none" });
  });
});

describe("honest lag and bounded requests (AC5)", () => {
  it("a failed delta keeps the last frame, states the lag, and makes one full read next", () => {
    const before = followed(3);
    const failed = runFrameReducer(before, {
      type: "TICK_COMMITTED",
      execution: execution(4),
      history: { kind: "delta", result: { status: "unavailable", message: null } },
    });
    expect(failed.history).toBe(before.history);
    expect(historyLag(failed)).toEqual({ recorded: 3, clock: 4 });
    // Never the same delta again: one full read at the next tick.
    expect(historyRequest(failed, execution(5))).toEqual({ kind: "full" });
  });

  it("a refused merge is never retried: the next read is a full one", () => {
    const before = followed(3);
    // A delta read from the wrong count: the merge refuses it.
    const stale = copy(fixture.deltas[1]);
    const refused = runFrameReducer(before, {
      type: "TICK_COMMITTED",
      execution: execution(4),
      history: { kind: "delta", result: { status: "loaded", ...stale } },
    });
    expect(refused.history).toBe(before.history);
    expect(historyRequest(refused, execution(5))).toEqual({ kind: "full" });
  });

  it("a failed full read leaves the next tick to try a delta from k again", () => {
    let state = followed(3);
    state = runFrameReducer(state, {
      type: "TICK_COMMITTED",
      execution: execution(4),
      history: { kind: "delta", result: { status: "unavailable", message: null } },
    });
    state = runFrameReducer(state, {
      type: "TICK_COMMITTED",
      execution: execution(5),
      history: { kind: "full", result: { status: "unavailable", message: null } },
    });
    expect(recorded(state)).toBe(3);
    expect(historyLag(state)).toEqual({ recorded: 3, clock: 5 });
    expect(historyRequest(state, execution(6))).toEqual({ kind: "delta", since: 3 });
  });

  it("catches up several boundaries in one commit", () => {
    let state = reduce(
      INITIAL,
      { type: "EXECUTION_READ", execution: execution(0) },
      { type: "HISTORY_READ", result: loaded(fixture.base) },
    );
    const jump = copy(fixture.jump);
    state = runFrameReducer(state, {
      type: "TICK_COMMITTED",
      execution: execution(7),
      history: { kind: "delta", result: { status: "loaded", ...jump } },
    });
    expect(recorded(state)).toBe(7);
    expect(clock(state)).toBe(7);
  });
});

describe("full reads only at the edges (AC6)", () => {
  it("a terminal answer makes one full read, which replaces the accumulated history", () => {
    const accumulated = followed(7);
    expect(historyRequest(accumulated, execution(7, "COMPLETED"))).toEqual({ kind: "full" });
    const terminal = runFrameReducer(accumulated, {
      type: "TICK_COMMITTED",
      execution: execution(7, "COMPLETED"),
      history: { kind: "full", result: loaded(fixture.full) },
    });
    const held = terminal.history;
    const before = accumulated.history;
    if (held?.status !== "loaded" || before?.status !== "loaded") {
      throw new Error("not loaded");
    }
    expect(held.full).toBe(true);
    expect(held.history).not.toBe(before.history);
    // Equal family by family; the digest is the whole document's alone.
    for (const family of Object.keys(APPEND_FAMILY_KEYS) as (keyof typeof APPEND_FAMILY_KEYS)[]) {
      expect(held.history[family], family).toEqual(before.history[family]);
    }
    for (const family of ["boundaries", "samples", "intervals", "attempts", "exposures"] as const) {
      expect(held.history[family].length, family).toBeGreaterThan(0);
    }
    // Once: the terminal read is not repeated for the same answer.
    expect(historyRequest(terminal, execution(7, "COMPLETED"))).toEqual({ kind: "none" });
  });
});

describe("one cursor, live or pinned (AC7)", () => {
  it("live follows the last recorded boundary in the clock's commit", () => {
    expect(selectedOffset(followed(3))).toBe(fixture.deltas[2].history.boundaries[0].offset_minutes);
    expect(selectedOffset(followed(6))).toBe(fixture.deltas[5].history.boundaries[0].offset_minutes);
  });

  it("a pinned cursor holds through ticks, failures and the terminal read", () => {
    const pinnedAt = fixture.deltas[1].history.boundaries[0].offset_minutes;
    let state = runFrameReducer(followed(3), { type: "SELECT", offset: pinnedAt });
    expect(state.cursor).toEqual({ mode: "pinned", offset: pinnedAt });
    for (let i = 3; i < 7; i += 1) {
      const read = copy(fixture.deltas[i]);
      state = runFrameReducer(state, {
        type: "TICK_COMMITTED",
        execution: execution(i + 1),
        history: { kind: "delta", result: { status: "loaded", ...read } },
      });
      expect(selectedOffset(state)).toBe(pinnedAt);
    }
    expect(boundariesBehindLive(state)).toBe(5);
    state = runFrameReducer(state, {
      type: "TICK_COMMITTED",
      execution: execution(7, "COMPLETED"),
      history: { kind: "full", result: loaded(fixture.full) },
    });
    expect(selectedOffset(state)).toBe(pinnedAt);
    state = runFrameReducer(state, { type: "RETURN_TO_LIVE" });
    expect(state.cursor).toBe(LIVE);
    expect(boundariesBehindLive(state)).toBe(0);
  });

  it("selecting the last boundary resumes live", () => {
    const state = followed(4);
    const last = fixture.deltas[3].history.boundaries[0].offset_minutes;
    const pinned = runFrameReducer(state, { type: "SELECT", offset: 0 });
    expect(pinned.cursor.mode).toBe("pinned");
    expect(runFrameReducer(pinned, { type: "SELECT", offset: last }).cursor).toBe(LIVE);
  });

  it("keeps cursor <= recorded <= clock", () => {
    let state = runFrameReducer(followed(4), { type: "SELECT", offset: 5 });
    state = runFrameReducer(state, {
      type: "TICK_COMMITTED",
      execution: execution(5),
      history: { kind: "delta", result: { status: "not_found" } },
    });
    const held = state.history;
    if (held?.status !== "loaded") {
      throw new Error("not loaded");
    }
    const last = held.history.boundaries[held.history.boundaries.length - 1];
    expect(selectedOffset(state)).toBeLessThanOrEqual(last.offset_minutes);
    expect(recorded(state)).toBeLessThanOrEqual(clock(state));
  });
});
