import type { RunExecution, RunExecutionResult } from "./runSetupClient";

/**
 * Browser auto-play for one Draft run (T025d, `D-2026-09-30-lab-cockpit-presentation`).
 *
 * Auto-play is nothing but a scheduler of the existing guarded Step. It sends
 * ONE step of one boundary, waits for that step's answer, and only then may
 * schedule the next one after a wall delay. The delay is the only thing pacing
 * changes: the step request is byte-for-byte the manual Step a reader could have
 * sent, so the frozen timestep, seed, physics and ordering cannot depend on it,
 * and nothing about pacing reaches the server or the run's identity.
 *
 * Stopping is the rule, resuming is an explicit act:
 *
 * - Pause cancels the NEXT request. A step already sent may be accepted, and its
 *   answer is still displayed, because it happened.
 * - A terminal status, a refusal (`STEP_ALREADY_APPLIED` among them), a missing
 *   surface (a closed gate answers 404), a network error or a response that did
 *   not arrive within the timeout stops scheduling and re-reads the
 *   authoritative position. The reader resumes explicitly; there is no retry
 *   and no catch-up burst.
 * - A hidden tab and leaving the page stop scheduling.
 *
 * The scheduler holds no clock of the run. Its only notion of position is the
 * `boundaries_completed` of the last execution it was shown, which is what the
 * guarded Step names as `from_boundary`.
 */

/** Why auto-play is not running. `null`: it has not been started here. */
export type PlaybackStopReason =
  | "PAUSED"
  | "TERMINAL"
  | "REFUSED"
  | "STEP_ALREADY_APPLIED"
  | "TIMEOUT"
  | "NETWORK"
  | "NOT_FOUND"
  | "HIDDEN";

export type PlaybackState =
  | { kind: "stopped"; reason: PlaybackStopReason | null; message: string | null }
  /** Scheduling: a step is in flight or the next one is waiting on the delay. */
  | { kind: "playing"; inFlight: boolean }
  /** Pause was asked for while a step was in flight; its answer is awaited. */
  | { kind: "pausing" };

/** The wall delays a reader can choose between steps, in milliseconds. */
export const PLAYBACK_DELAYS_MS = [250, 1000, 2000, 5000] as const;
export const DEFAULT_PLAYBACK_DELAY_MS = 1000;
/** How long one step may take before auto-play stops and re-reads. */
export const DEFAULT_STEP_TIMEOUT_MS = 20000;

export interface PlaybackTimers {
  set(callback: () => void, ms: number): unknown;
  clear(handle: unknown): void;
}

export interface PlaybackDeps {
  /** The guarded Step, one boundary from `fromBoundary`. */
  step(fromBoundary: number): Promise<RunExecutionResult>;
  /** A read of the authoritative position; executes nothing. */
  read(): Promise<RunExecutionResult>;
  /** Show an execution answer (a step's, or a re-read's). */
  show(result: RunExecutionResult): void;
  /** Called whenever the playback state changes. */
  onState(state: PlaybackState): void;
  /** Called once each time scheduling stops, after any re-read. */
  onStopped?(reason: PlaybackStopReason): void;
  timers?: PlaybackTimers;
  stepTimeoutMs?: number;
}

const WINDOW_TIMERS: PlaybackTimers = {
  set: (callback, ms) => setTimeout(callback, ms),
  clear: (handle) => clearTimeout(handle as ReturnType<typeof setTimeout>),
};

/** The statuses from which a step can be sent at all. */
export function canAutoPlay(execution: RunExecution | null): boolean {
  return execution !== null && execution.status === "RUNNING";
}

/**
 * Which of two execution answers to display.
 *
 * A late answer - a step that came back after a timeout's re-read, say - must
 * not move the displayed position backwards. Anything that is not a loaded
 * execution is shown as it is: it is news, not a position.
 */
export function laterExecution(
  previous: RunExecutionResult | null,
  next: RunExecutionResult,
): RunExecutionResult {
  if (
    previous !== null &&
    previous.status === "loaded" &&
    next.status === "loaded" &&
    next.execution.run_id === previous.execution.run_id &&
    next.execution.boundaries_completed <
      previous.execution.boundaries_completed
  ) {
    return previous;
  }
  return next;
}

export class PlaybackScheduler {
  private readonly deps: PlaybackDeps;
  private readonly timers: PlaybackTimers;
  private readonly stepTimeoutMs: number;
  private state: PlaybackState = { kind: "stopped", reason: null, message: null };
  private delayMs = DEFAULT_PLAYBACK_DELAY_MS;
  private position = 0;
  /** Bumped by every stop, so an older loop's continuations do nothing. */
  private generation = 0;
  private pending: unknown = null;
  private disposed = false;
  /** The tab was hidden while a step was in flight: stop as HIDDEN, not PAUSED. */
  private hiddenWhileInFlight = false;

  constructor(deps: PlaybackDeps) {
    this.deps = deps;
    this.timers = deps.timers ?? WINDOW_TIMERS;
    this.stepTimeoutMs = deps.stepTimeoutMs ?? DEFAULT_STEP_TIMEOUT_MS;
  }

  current(): PlaybackState {
    return this.state;
  }

  setDelay(ms: number): void {
    // Wall delay only. Nothing else about a step depends on it.
    this.delayMs = ms;
  }

  /** Start scheduling from the displayed execution. Refuses unless RUNNING. */
  play(execution: RunExecution | null): boolean {
    if (this.disposed || this.state.kind !== "stopped" || !canAutoPlay(execution)) {
      return false;
    }
    this.position = (execution as RunExecution).boundaries_completed;
    this.generation += 1;
    this.setState({ kind: "playing", inFlight: false });
    this.tick(this.generation);
    return true;
  }

  /** Cancel future requests. A step in flight finishes and is displayed. */
  pause(): void {
    if (this.state.kind !== "playing") {
      return;
    }
    this.clearPending();
    if (this.state.inFlight) {
      this.setState({ kind: "pausing" });
      return;
    }
    this.stop("PAUSED", null, false);
  }

  /** The tab was hidden: stop scheduling, keep whatever is in flight. */
  hidden(): void {
    if (this.state.kind === "playing" || this.state.kind === "pausing") {
      this.clearPending();
      const inFlight = this.state.kind === "pausing" || this.state.inFlight;
      if (inFlight) {
        this.setState({ kind: "pausing" });
        this.hiddenWhileInFlight = true;
        return;
      }
      this.stop("HIDDEN", null, false);
    }
  }

  /** Navigation: stop scheduling and show nothing further. */
  dispose(): void {
    this.disposed = true;
    this.generation += 1;
    this.clearPending();
  }

  private setState(next: PlaybackState): void {
    this.state = next;
    if (!this.disposed) {
      this.deps.onState(next);
    }
  }

  private clearPending(): void {
    if (this.pending !== null) {
      this.timers.clear(this.pending);
      this.pending = null;
    }
  }

  private tick(generation: number): void {
    if (this.disposed || generation !== this.generation) {
      return;
    }
    if (this.state.kind !== "playing") {
      return;
    }
    this.setState({ kind: "playing", inFlight: true });
    let settled = false;
    const timeout = this.timers.set(() => {
      if (settled || generation !== this.generation) {
        return;
      }
      settled = true;
      // The answer may still arrive. It is shown if it moves the position
      // forward, but nothing is scheduled from it.
      this.stop(
        "TIMEOUT",
        "The step did not answer in time. Its position has been re-read; resume explicitly.",
        true,
      );
    }, this.stepTimeoutMs);

    void this.deps.step(this.position).then((answer) => {
      if (this.disposed) {
        return;
      }
      if (settled || generation !== this.generation) {
        // Late: a timeout already stopped this loop. An accepted step is
        // still a fact, so it is shown; `laterExecution` keeps it from
        // moving the display backwards.
        if (answer.status === "loaded") {
          this.deps.show(answer);
        }
        return;
      }
      settled = true;
      this.timers.clear(timeout);
      this.handle(answer, generation);
    });
  }

  private handle(answer: RunExecutionResult, generation: number): void {
    if (answer.status === "loaded") {
      this.deps.show(answer);
      this.position = answer.execution.boundaries_completed;
      if (answer.execution.status !== "RUNNING") {
        this.stop("TERMINAL", null, false);
        return;
      }
      if (this.state.kind === "pausing") {
        const reason = this.hiddenWhileInFlight ? "HIDDEN" : "PAUSED";
        this.stop(reason, null, false);
        return;
      }
      this.setState({ kind: "playing", inFlight: false });
      this.pending = this.timers.set(() => {
        this.pending = null;
        this.tick(generation);
      }, this.delayMs);
      return;
    }
    if (answer.status === "refused") {
      this.stop(
        answer.code === "STEP_ALREADY_APPLIED" ? "STEP_ALREADY_APPLIED" : "REFUSED",
        answer.message,
        true,
      );
      return;
    }
    if (answer.status === "not_found") {
      this.stop(
        "NOT_FOUND",
        "The execution surface did not answer for this run; the Lab may no longer be enabled.",
        true,
      );
      return;
    }
    this.stop(
      "NETWORK",
      answer.message ?? "The step request did not complete, so whether it applied is not known until the position is re-read.",
      true,
    );
  }

  private stop(
    reason: PlaybackStopReason,
    message: string | null,
    reread: boolean,
  ): void {
    this.generation += 1;
    this.clearPending();
    this.hiddenWhileInFlight = false;
    this.setState({ kind: "stopped", reason, message });
    if (!reread) {
      this.deps.onStopped?.(reason);
      return;
    }
    void this.deps.read().then((position) => {
      if (this.disposed) {
        return;
      }
      this.deps.show(position);
      if (position.status === "loaded") {
        this.position = position.execution.boundaries_completed;
      }
      this.deps.onStopped?.(reason);
    });
  }
}
