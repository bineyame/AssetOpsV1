/**
 * The run page's one owner of what a tick commits (T025e AC4-AC7).
 *
 * `RunFrame` holds the execution, the recorded history, whether the next
 * history read must be a full one, and the history cursor in ONE state, and
 * every answer - an auto-played step, a manual control, a late answer, a stop's
 * re-read - is committed in ONE transition with the history read it caused.
 * The four states the page keeps apart each have one owner:
 *
 * - the execution clock is `execution.boundaries_completed`, from answers;
 * - the recorded count is the held history's `boundaries_recorded`;
 * - the history cursor is `cursor`, moved only by a tick while live, or by the
 *   reader;
 * - playback state stays the scheduler's (`runPlayback.ts`) and is not here.
 *
 * Everything here is pure. The merge itself is `liveHistory.ts`'s; this module
 * only decides which read an answer needs and folds the read into the state.
 */

import { appendFrame, historyFrame, type HistoryFrame } from "./liveHistory";
import type {
  RunHistory,
  RunHistoryDeltaResult,
  RunHistoryResult,
} from "./runHistory";
import { laterExecution } from "./runPlayback";
import type { RunExecutionResult } from "./runSetupClient";

/**
 * Live follows the last recorded boundary in the clock's own commit; pinned
 * holds one boundary (by its offset, a stable identity) while play continues.
 */
export type Cursor = { mode: "live" } | { mode: "pinned"; offset: number };

export const LIVE: Cursor = { mode: "live" };

/** The held history: a `RunHistoryResult`, plus its slices when loaded. */
export type HeldHistory =
  | {
      status: "loaded";
      history: RunHistory;
      frame: HistoryFrame;
      /** Read whole (on load, a base or terminal read), not accumulated. */
      full: boolean;
    }
  | { status: "not_found" }
  | { status: "unavailable"; message: string | null };

export interface RunFrameState {
  execution: RunExecutionResult | null;
  history: HeldHistory | null;
  /**
   * A delta failed or was refused: the next history read is one full read,
   * never the same delta again. Cleared by any full read, which - if it fails
   * too - leaves the next tick to try a delta from what is held.
   */
  fullReadDue: boolean;
  cursor: Cursor;
}

export const INITIAL: RunFrameState = {
  execution: null,
  history: null,
  fullReadDue: false,
  cursor: LIVE,
};

/** What one answer needs from the history route. At most one read. */
export type HistoryRequest =
  | { kind: "none" }
  | { kind: "full" }
  | { kind: "delta"; since: number };

/** The read a committed answer carries, as it came back. */
export type HistoryAnswer =
  | { kind: "none" }
  | { kind: "full"; result: RunHistoryResult }
  | { kind: "delta"; result: RunHistoryDeltaResult };

export type RunFrameAction =
  | { type: "RESET" }
  | { type: "EXECUTION_READ"; execution: RunExecutionResult }
  | { type: "HISTORY_READ"; result: RunHistoryResult }
  | {
      type: "TICK_COMMITTED";
      execution: RunExecutionResult;
      history: HistoryAnswer;
    }
  | { type: "SELECT"; offset: number }
  | { type: "RETURN_TO_LIVE" };

/** Every other execution status is terminal: no step follows it. */
const NOT_TERMINAL = new Set(["RUNNING", "NOT_STARTED"]);

/**
 * Which history read committing `answer` needs, given what is held.
 *
 * Full reads happen only at the edges: when nothing is held (the load, or a
 * Start's base), at a terminal answer (once), and once after a delta failed
 * or was refused. Otherwise a delta from the held recorded count - or nothing
 * when the history already records the answer's boundaries, which is how a
 * late answer and the stop re-read after it reconcile the history once.
 */
export function historyRequest(
  state: RunFrameState,
  answer: RunExecutionResult,
): HistoryRequest {
  const shown = laterExecution(state.execution, answer);
  if (shown.status !== "loaded" || shown.execution.status === "NOT_STARTED") {
    return { kind: "none" };
  }
  const clock = shown.execution.boundaries_completed;
  const held = state.history;
  if (held === null || held.status !== "loaded") {
    return { kind: "full" };
  }
  const recorded = held.history.boundaries_recorded;
  if (!NOT_TERMINAL.has(shown.execution.status)) {
    return held.full && recorded >= clock ? { kind: "none" } : { kind: "full" };
  }
  if (state.fullReadDue) {
    return { kind: "full" };
  }
  if (recorded >= clock) {
    return { kind: "none" };
  }
  return { kind: "delta", since: recorded };
}

function wholeRead(state: RunFrameState, result: RunHistoryResult): RunFrameState {
  if (result.status === "loaded") {
    return {
      ...state,
      history: {
        status: "loaded",
        history: result.history,
        frame: historyFrame(result.history),
        full: true,
      },
      fullReadDue: false,
    };
  }
  // A failed full read never blanks a frame already held: the last good one
  // stays, and the next tick tries a delta from it again.
  if (state.history !== null && state.history.status === "loaded") {
    return { ...state, fullReadDue: false };
  }
  return { ...state, history: result, fullReadDue: false };
}

function deltaRead(state: RunFrameState, result: RunHistoryDeltaResult): RunFrameState {
  const held = state.history;
  if (held === null || held.status !== "loaded") {
    return { ...state, fullReadDue: true };
  }
  if (result.status !== "loaded") {
    return { ...state, fullReadDue: true };
  }
  const appended = appendFrame(held.frame, result.history, result.delta);
  if ("refused" in appended) {
    // Never patched, never retried: one full read at the next tick.
    return { ...state, fullReadDue: true };
  }
  return {
    ...state,
    history: {
      status: "loaded",
      history: appended.ok.history,
      frame: appended.ok,
      full: false,
    },
    fullReadDue: false,
  };
}

export function runFrameReducer(
  state: RunFrameState,
  action: RunFrameAction,
): RunFrameState {
  switch (action.type) {
    case "RESET":
      return INITIAL;
    case "EXECUTION_READ":
      return { ...state, execution: action.execution };
    case "HISTORY_READ":
      return wholeRead(state, action.result);
    case "TICK_COMMITTED": {
      const withExecution: RunFrameState = {
        ...state,
        execution: laterExecution(state.execution, action.execution),
      };
      if (action.history.kind === "full") {
        return wholeRead(withExecution, action.history.result);
      }
      if (action.history.kind === "delta") {
        return deltaRead(withExecution, action.history.result);
      }
      return withExecution;
    }
    case "SELECT": {
      const held = state.history;
      const boundaries =
        held !== null && held.status === "loaded" ? held.history.boundaries : [];
      const last = boundaries[boundaries.length - 1];
      if (last === undefined || action.offset === last.offset_minutes) {
        return state.cursor.mode === "live" ? state : { ...state, cursor: LIVE };
      }
      if (!boundaries.some((b) => b.offset_minutes === action.offset)) {
        return state;
      }
      return { ...state, cursor: { mode: "pinned", offset: action.offset } };
    }
    case "RETURN_TO_LIVE":
      return state.cursor.mode === "live" ? state : { ...state, cursor: LIVE };
  }
}

/** The boundary the cursor selects, or null when none is recorded. */
export function selectedOffset(state: RunFrameState): number | null {
  const held = state.history;
  if (held === null || held.status !== "loaded") {
    return null;
  }
  const boundaries = held.history.boundaries;
  const last = boundaries[boundaries.length - 1];
  if (last === undefined) {
    return null;
  }
  const cursor = state.cursor;
  if (
    cursor.mode === "pinned" &&
    boundaries.some((b) => b.offset_minutes === cursor.offset)
  ) {
    return cursor.offset;
  }
  return last.offset_minutes;
}

/** How many recorded boundaries lie after a pinned cursor; 0 while live. */
export function boundariesBehindLive(state: RunFrameState): number {
  const held = state.history;
  const cursor = state.cursor;
  if (cursor.mode === "live" || held === null || held.status !== "loaded") {
    return 0;
  }
  return held.history.boundaries.filter((b) => b.offset_minutes > cursor.offset)
    .length;
}

/**
 * The recorded count and the execution clock when the history lags it - the
 * honest statement after a failed read - or null when it does not.
 */
export function historyLag(
  state: RunFrameState,
): { recorded: number; clock: number } | null {
  const held = state.history;
  const execution = state.execution;
  if (
    held === null ||
    held.status !== "loaded" ||
    execution === null ||
    execution.status !== "loaded"
  ) {
    return null;
  }
  const recorded = held.history.boundaries_recorded;
  const clock = execution.execution.boundaries_completed;
  return recorded < clock ? { recorded, clock } : null;
}
