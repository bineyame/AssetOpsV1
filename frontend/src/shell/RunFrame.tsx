import { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { Badge, DataTable, Disclosure, Fact, FactList, PageHeader, Panel } from "../ui";
import { ElectricalPanels, ExactQuantity } from "./ElectricalPanels";
import {
  HistoryCockpit,
  HistoryFacts,
  HistoryRecordsAtCursor,
  stagedSignal,
  unavailableArrival,
} from "./HistoryInspector";
import { GatewayLedgerView } from "./GatewayLedgerView";
import { GatewayDiagnosticsPanel, PublicationSchedulePanel } from "./GatewayPublicationPanels";
import { RunCommitPanel } from "./RunCommitPanel";
import { RunHeader } from "./RunHeader";
import {
  DEFAULT_PLAYBACK_DELAY_MS,
  DEFAULT_STEP_TIMEOUT_MS,
  PLAYBACK_DELAYS_MS,
  PlaybackScheduler,
  type PlaybackState,
  type PlaybackStopReason,
} from "./runPlayback";
import type { SiteDetailClient } from "../sites/siteDirectoryClient";
import type { SiteDetailResult } from "../sites/siteReadModel";
import {
  INITIAL,
  boundariesBehindLive,
  historyLag,
  historyRequest,
  selectedOffset,
  runFrameReducer,
  type HistoryAnswer,
  type RunFrameAction,
  type RunFrameState,
} from "./runFrameState";
import type {
  RunConfigurationBasis,
  RunDetailResult,
  RunExecutionResult,
  RunSetupClient,
  RunStageMappingEntry,
  RunStageResult,
  RunStagedEnvelope,
} from "./runSetupClient";
import type { RunHistoryPublication } from "./runHistory";

/**
 * One Draft run: what it froze, what executing it produced, and what it is not.
 * A Simulator Lab surface.
 *
 * ## Until T022 this was the shell of a run that had never run
 *
 * It said so, at length, because the thing a run detail screen with no runtime
 * has to avoid is reading as one that is merely stopped. That is over: a Draft
 * here can be started, stepped and run to the end, and the screen shows the
 * simulated clock, the world at the instant it has reached, and what each
 * configured device reported about that world.
 *
 * The absences that remain are still absences rather than disabled controls.
 * There is no reset, no event injection, no truth overlay on an operator
 * screen, no commit, no release and no bridge into the operator product, and
 * none of them appears here in any form. Since T025d there is auto-play and a
 * pause, but only of the browser's own scheduling of the guarded Step
 * (`runPlayback.ts`): pausing stops the next request and does nothing to the
 * run, and there is still no server clock, speed field or jump. The rule
 * (`D-2026-09-20-scenario-detail-affordances`) is that a disabled control appears
 * only when the action is native to the object and the missing prerequisite is the
 * next named causal capability - and none of those is.
 *
 * ## The three columns this screen exists for
 *
 * `true_value`, `reported_value` and `reported_source_time` sit in three separate
 * cells of one row, and keeping them apart IS the slice. The tank loses a hundred
 * and twenty litres inside the shipped reporting gap; the true column moves, the
 * reported column does not, and the source time says the reading a reader is
 * looking at was taken before the gap opened. A screen that showed one number
 * called "fuel level" would have hidden exactly the thing the scenario was
 * authored to demonstrate.
 *
 * Every statement on this screen - a status, a reading quality, why a sample
 * published nothing - is placed from the payload rather than written here. They
 * are properties of the contract's own vocabularies, and a screen composing its
 * own sentence would be a second copy of a rule.
 *
 * ## The stage inspector, since T023
 *
 * Executing a Draft now also publishes, through the simulated gateway, the
 * canonical source envelopes a later Commit would release. The inspector below
 * the readings shows them exactly as persisted - each envelope's canonical text,
 * with its identity, mapping and the two times split out beside it - and it is
 * read from the persisted stage rather than from the live run, so reloading the
 * page after the process that ran it is gone shows the same bytes. It is
 * deliberately utilitarian and it is read-only: a staged record cannot be edited
 * here, and nothing here releases or commits one.
 */
/** T025e AC12: the tick commit timing the layout evidence reads. */
const TICK_MARK = "run-frame-tick";
let tickMarked = false;

function markTick(): void {
  if (typeof performance === "undefined" || typeof performance.mark !== "function") {
    return;
  }
  performance.mark(TICK_MARK);
  tickMarked = true;
}

function measureTick(): void {
  if (!tickMarked || typeof performance.measure !== "function") {
    return;
  }
  tickMarked = false;
  try {
    performance.measure("run-frame-commit", TICK_MARK);
  } catch {
    // A measurement is evidence, never a reason for the page to fail.
  }
}

export interface RunFrameProps {
  runSetup: RunSetupClient;
  runsPath: string;
  simulatorLabPath: string;
  /**
   * T025d: reads the Site the run froze, so its recorded values can be drawn
   * on that Site's configured diagram once the Foundation version is checked.
   * Absent, the drawing states it is unavailable and the rest is unchanged.
   */
  siteDetail?: SiteDetailClient;
  /** T025d: how long one auto-play step may take. Tests shorten it. */
  playbackStepTimeoutMs?: number;
  /** R1 finding 2: how long a history read may take before it counts as failed. */
  historyTimeoutMs?: number;
}

/** A history read is a read on the same host lock a step takes: same bound. */
const DEFAULT_HISTORY_TIMEOUT_MS = DEFAULT_STEP_TIMEOUT_MS;

/**
 * `read`, or `expired` when it has not settled within `ms`. The late answer is
 * ignored: the caller commits the failure path and reads again at the next tick.
 */
function withinTimeout<T>(read: Promise<T>, ms: number, expired: T): Promise<T> {
  return new Promise<T>((resolve) => {
    const timer = setTimeout(() => resolve(expired), ms);
    read.then(
      (value) => {
        clearTimeout(timer);
        resolve(value);
      },
      () => {
        clearTimeout(timer);
        resolve(expired);
      },
    );
  });
}

/**
 * The two statuses that admit a control at all.
 *
 * Read off the status rather than tracked separately, so there is no state in
 * which the screen believes a run can be advanced and the port disagrees.
 */
const CONTROLLABLE = new Set(["NOT_STARTED", "RUNNING"]);

export function RunFrame({
  runSetup,
  runsPath,
  simulatorLabPath,
  siteDetail,
  playbackStepTimeoutMs,
  historyTimeoutMs = DEFAULT_HISTORY_TIMEOUT_MS,
}: RunFrameProps) {
  const { runId } = useParams<{ runId: string }>();
  const [result, setResult] = useState<RunDetailResult | null>(null);
  // T025e: execution, history, the full-read flag and the history cursor are
  // one state, and every answer is one commit (`runFrameState.ts`). The ref
  // mirrors it so an answer arriving later decides its read from what is held
  // now, not from the render that sent it.
  const [frameState, setFrameState] = useState<RunFrameState>(INITIAL);
  const held = useRef<RunFrameState>(INITIAL);
  const dispatch = useCallback((action: RunFrameAction) => {
    held.current = runFrameReducer(held.current, action);
    if (action.type === "TICK_COMMITTED") {
      // T025e AC12: the tick's commit is measured from this dispatch to the
      // layout effect below, in the production build, by the layout evidence.
      markTick();
    }
    setFrameState(held.current);
  }, []);
  useLayoutEffect(() => {
    measureTick();
  }, [frameState]);
  const execution = frameState.execution;
  // The one history cursor (T025e AC7): the reader pins or returns to live.
  const select = useCallback(
    (offset: number) => dispatch({ type: "SELECT", offset }),
    [dispatch],
  );
  const returnToLive = useCallback(
    () => dispatch({ type: "RETURN_TO_LIVE" }),
    [dispatch],
  );
  const [pending, setPending] = useState(false);
  const [boundaries, setBoundaries] = useState("1");
  const [stage, setStage] = useState<RunStageResult | null>(null);
  const history = frameState.history;
  const [selectedMessage, setSelectedMessage] = useState<string | null>(null);
  const [drawingSite, setDrawingSite] = useState<SiteDetailResult | null>(null);
  const [playback, setPlayback] = useState<PlaybackState>({
    kind: "stopped",
    reason: null,
    message: null,
  });
  const [delayMs, setDelayMs] = useState<number>(DEFAULT_PLAYBACK_DELAY_MS);
  const scheduler = useRef<PlaybackScheduler | null>(null);
  // T025e AC11: the status line whose `data-playback-in-flight` attribute the
  // scheduler's in-flight changes write, so they cost no render.
  const statusRef = useRef<HTMLParagraphElement>(null);
  const onPlaybackState = useCallback((next: PlaybackState) => {
    statusRef.current?.setAttribute(
      "data-playback-in-flight",
      next.kind === "playing" && next.inFlight ? "yes" : "no",
    );
    setPlayback((previous) => shownPlayback(previous, next));
  }, []);
  const delayRef = useRef<number>(DEFAULT_PLAYBACK_DELAY_MS);

  // The stage is re-read after a control and whenever auto-play stops, never
  // per auto-played step. T025e: the history is no longer re-read on stop; it
  // follows each answer through `commit` below.
  const rereadStage = useCallback(async () => {
    if (runId === undefined) {
      return;
    }
    setStage(await runSetup.getStage(runId));
  }, [runSetup, runId]);

  // One history request at a time, never two in parallel: each commit waits
  // for the one before it, then decides its read from what that one left.
  const commits = useRef<Promise<void>>(Promise.resolve());
  /**
   * Commit one execution answer with the history read it needs, in one
   * transition. `base` forces a whole read (a Start: the live session's first
   * record). Resolves after the commit; never rejects - a history failure is
   * not a step failure, it only leaves the history behind the clock.
   */
  const commit = useCallback(
    (answer: RunExecutionResult, base = false): Promise<void> => {
      const next = commits.current.then(async () => {
        if (runId === undefined) {
          return;
        }
        const request = base ? { kind: "full" as const } : historyRequest(held.current, answer);
        let read: HistoryAnswer = { kind: "none" };
        const failed = { status: "unavailable" as const, message: null };
        if (request.kind === "full") {
          read = {
            kind: "full",
            result: await withinTimeout(
              runSetup.getExecutionHistory(runId),
              historyTimeoutMs,
              failed,
            ),
          };
        } else if (request.kind === "delta") {
          read = {
            kind: "delta",
            result: await withinTimeout(
              runSetup.getExecutionHistorySince(runId, request.since),
              historyTimeoutMs,
              failed,
            ),
          };
        }
        dispatch({ type: "TICK_COMMITTED", execution: answer, history: read });
      });
      commits.current = next.catch(() => undefined);
      return commits.current;
    },
    [runSetup, runId, dispatch, historyTimeoutMs],
  );

  // One scheduler per run page. Leaving the page (or changing run) disposes
  // it, which stops scheduling and shows nothing further; a reload builds a
  // new one that starts stopped.
  useEffect(() => {
    if (runId === undefined) {
      return undefined;
    }
    const created = new PlaybackScheduler({
      step: (fromBoundary) =>
        runSetup.stepExecution(runId, { boundaries: 1, fromBoundary }),
      read: () => runSetup.getExecution(runId),
      show: (answer) => commit(answer),
      onState: onPlaybackState,
      onStopped: () => {
        void rereadStage();
      },
      stepTimeoutMs: playbackStepTimeoutMs,
    });
    created.setDelay(delayRef.current);
    scheduler.current = created;
    onPlaybackState(created.current());
    const onVisibility = () => {
      if (document.visibilityState === "hidden") {
        created.hidden();
      }
    };
    document.addEventListener("visibilitychange", onVisibility);
    return () => {
      document.removeEventListener("visibilitychange", onVisibility);
      created.dispose();
      if (scheduler.current === created) {
        scheduler.current = null;
      }
    };
  }, [runSetup, runId, rereadStage, commit, playbackStepTimeoutMs, onPlaybackState]);

  useEffect(() => {
    delayRef.current = delayMs;
    scheduler.current?.setDelay(delayMs);
  }, [delayMs]);

  // T025d: read the Site the history's drawing context names, once per Site.
  // The binding check itself is `bindDrawing`'s; this only fetches.
  const drawingSiteId =
    history !== null &&
    history.status === "loaded" &&
    history.history.drawing_context !== null &&
    history.history.drawing_context.status === "VERIFIED"
      ? history.history.drawing_context.site_id
      : null;
  useEffect(() => {
    let active = true;
    if (drawingSiteId === null) {
      return undefined;
    }
    if (siteDetail === undefined) {
      setDrawingSite({ status: "unavailable" });
      return undefined;
    }
    void siteDetail.getSite(drawingSiteId).then((loaded) => {
      if (active) {
        setDrawingSite(loaded);
      }
    });
    return () => {
      active = false;
    };
  }, [siteDetail, drawingSiteId]);

  useEffect(() => {
    let active = true;

    if (runId === undefined) {
      setResult({ status: "not_found" });
      return undefined;
    }

    void runSetup.getRun(runId).then((loaded) => {
      if (active) {
        setResult(loaded);
      }
    });
    dispatch({ type: "RESET" });
    void runSetup.getStage(runId).then((loaded) => {
      if (active) {
        setStage(loaded);
      }
    });
    // The load's execution and whole history reads take their place in the
    // commit chain, so they never run beside a commit's history read, and
    // the reducer keeps whatever a newer commit already holds (R1 finding 4).
    // Reload starts live at the last recorded boundary; the cursor is not
    // persisted.
    const loading = commits.current.then(async () => {
      if (!active) {
        return;
      }
      const failed = { status: "unavailable" as const, message: null };
      void runSetup.getExecution(runId).then((loaded) => {
        if (active) {
          dispatch({ type: "EXECUTION_READ", execution: loaded });
        }
      });
      const history = await withinTimeout(
        runSetup.getExecutionHistory(runId),
        historyTimeoutMs,
        failed,
      );
      if (active) {
        dispatch({ type: "HISTORY_READ", result: history });
      }
    });
    commits.current = loading.catch(() => undefined);

    return () => {
      active = false;
    };
  }, [runSetup, runId, dispatch, historyTimeoutMs]);

  /**
   * Run one control and replace the execution with what came back.
   *
   * `pending` disables every control while one is in flight, which is the first
   * half of not stepping twice. The second half is on the wire and is the half
   * that matters: the step request names the boundary it expects to advance from,
   * so a request that arrives anyway - a second tab, a retry, a browser replaying
   * a POST - advances nothing. A screen-only guard would be a guard one keystroke
   * from being bypassed.
   */
  const control = useCallback(
    async (act: () => Promise<RunExecutionResult>, base = false) => {
      setPending(true);
      const answer = await act();
      // T025e: the same commit path as auto-play - the answer with its
      // history read (a Start's is the whole base the live session starts
      // from; a Step's a delta; a terminal answer's the one full read).
      await commit(answer, base);
      // A control may have staged envelopes, so the stage is re-read from
      // persistence after it rather than patched from the control's answer.
      await rereadStage();
      setPending(false);
    },
    [commit, rereadStage],
  );

  const backLinks = (
    <p>
      <Link to={runsPath}>Back to Runs</Link>{" "}
      <Link to={simulatorLabPath}>Back to the Simulator Lab</Link>
    </p>
  );

  function frame(children: React.ReactNode) {
    return (
      <main aria-labelledby="run-heading">
        <PageHeader
          title="Draft run"
          headingId="run-heading"
          subtitle="Developer workspace"
        />
        {children}
        {backLinks}
      </main>
    );
  }

  if (result === null) {
    return frame(<p>Loading the persisted run.</p>);
  }

  if (result.status === "not_found") {
    return frame(
      <Panel heading="No such run" headingId="run-missing-heading">
        <p>
          No run with that run identity is persisted. A run identity is
          allocated when a draft is created; it is not a site identity and not
          a scenario identity, and nothing here falls back to a different run.
        </p>
      </Panel>,
    );
  }

  if (result.status === "unavailable") {
    return frame(
      <Panel heading="Run unavailable" headingId="run-unavailable-heading">
        <p>
          The run store could not be read, so this run cannot be shown.
          Nothing is known about what it froze.
        </p>
      </Panel>,
    );
  }

  const run = result.run;
  const blocked = run.execution_status === "BLOCKED";
  const projection =
    execution !== null && execution.status === "loaded"
      ? execution.execution
      : null;
  // S2-01b: some signal's simulated device rounds what it publishes.
  const quantized =
    projection !== null &&
    projection.signals.some((signal) => typeof signal.resolution === "string");
  // Manual Step and Run to the end cannot race auto-play: while it schedules
  // (or awaits a step it already sent) they are unavailable, and while a
  // manual control is in flight Play is.
  const autoPlaying = playback.kind !== "stopped";
  const requested = Number.parseInt(boundaries, 10);
  const stepSize = Number.isNaN(requested) ? 0 : requested;

  return frame(
    <>
      {blocked ? (
        <Panel
          heading="Why this draft cannot be executed"
          headingId="run-blocked-heading"
          flush
        >
          <DataTable labelledBy="run-blocked-heading">
            <thead>
              <tr>
                <th scope="col">Reason</th>
                <th scope="col">What it is about</th>
                <th scope="col">Why</th>
              </tr>
            </thead>
            <tbody>
              {run.blocking_reasons.map((reason) => (
                <tr key={`${reason.kind}-${reason.subject}`}>
                  <th scope="row">{reason.kind}</th>
                  <td>{reason.subject}</td>
                  <td className="cell-secondary">{reason.statement}</td>
                </tr>
              ))}
            </tbody>
          </DataTable>
        </Panel>
      ) : null}
      {/*
        T025e AC9: the cockpit. The control strip on the execution clock, then
        the record at the history cursor. Nothing above it grows per tick, and
        nothing inside it changes size with a tick: every region is reserved.
      */}
      <div className="run-cockpit" data-cockpit>
        <section
          className="control-strip"
          aria-labelledby="run-execution-heading"
          data-control-strip
        >
          <h2 id="run-execution-heading" className="control-strip__heading">
            Executing this run
          </h2>
          {execution === null ? (
            <p className="control-strip__slot">Loading the execution of the persisted run.</p>
          ) : execution.status === "not_found" ? (
            <p className="control-strip__slot">
              No execution surface answered for this run identity, so there is
              nothing to start and nothing to show.
            </p>
          ) : execution.status === "unavailable" ? (
            <p className="control-strip__slot" data-execution-unavailable>
              {execution.message ??
                "The execution surface could not be reached, so nothing is known about whether this draft has been executed."}
            </p>
          ) : null}

          {projection === null ? null : (
            <>
              <div className="control-strip__row">
                <Badge tone="lifecycle">{projection.status}</Badge>
                <span
                  className="control-strip__clock"
                  data-execution-clock={projection.boundaries_completed}
                >
                  {`Execution clock: boundary ${projection.boundaries_completed} of ${projection.boundaries_total}, ${projection.simulation_time}`}
                </span>
              </div>
              {blocked ? null : (
                <div className="control-strip__row control-strip__controls">
                  <button
                    type="button"
                    className="action"
                    disabled={
                      pending ||
                      autoPlaying ||
                      projection.status !== "NOT_STARTED"
                    }
                    onClick={() => {
                      void control(
                        () => runSetup.startExecution(run.run_id),
                        true,
                      );
                    }}
                  >
                    Start this run
                  </button>
                  <span className="control-strip__group">
                    <label htmlFor="run-step-boundaries">
                      Boundaries to advance
                    </label>{" "}
                    <input
                      id="run-step-boundaries"
                      className="control-strip__count"
                      type="number"
                      min={1}
                      value={boundaries}
                      onChange={(event) => setBoundaries(event.target.value)}
                    />{" "}
                    <button
                      type="button"
                      className="action"
                      disabled={
                        pending ||
                        autoPlaying ||
                        projection.status !== "RUNNING" ||
                        stepSize < 1
                      }
                      onClick={() => {
                        void control(() =>
                          runSetup.stepExecution(run.run_id, {
                            boundaries: stepSize,
                            fromBoundary: projection.boundaries_completed,
                          }),
                        );
                      }}
                    >
                      Step
                    </button>
                  </span>
                  <button
                    type="button"
                    className="action"
                    disabled={
                      pending ||
                      autoPlaying ||
                      projection.status !== "RUNNING"
                    }
                    onClick={() => {
                      void control(() =>
                        runSetup.runExecutionToEnd(run.run_id),
                      );
                    }}
                  >
                    Run to the end
                  </button>
                  <PlaybackControls
                    state={playback}
                    delayMs={delayMs}
                    canPlay={
                      !pending &&
                      !autoPlaying &&
                      projection.status === "RUNNING"
                    }
                    onDelay={setDelayMs}
                    onPlay={() => {
                      scheduler.current?.play(projection);
                    }}
                    onPause={() => {
                      scheduler.current?.pause();
                    }}
                    statusRef={statusRef}
                    executionStatus={projection.status}
                  />
                </div>
              )}
              <Disclosure name="how-playback-works" summary="How playback works">
                <p className="action-list__reason">
                  A step advances the simulated clock by that many boundaries
                  and says which boundary it is advancing from, so the same
                  step submitted twice advances once.
                </p>
                <p className="action-list__reason">
                  {`Auto-play sends one guarded Step of one boundary (${projection.timestep_minutes} simulated minutes, the run's frozen timestep), waits for its answer and its recorded history, then waits the wall delay before the next. The delay changes wall time only: every step is the same request as the Step button, so the run's physics, seed and ordering do not depend on it. Pausing stops the next request and does nothing to the run. Staged envelopes are re-read when auto-play stops, not per step.`}
                </p>
                <p className="action-list__reason">
                  The execution clock is where the run is. The history cursor
                  below is which recorded boundary the cockpit shows: it
                  follows live, or holds a boundary you pin, and moving it
                  reads the record and executes nothing.
                </p>
              </Disclosure>
            </>
          )}
          {/*
            One reserved slot for the one message a control can leave: a
            refusal (criterion 4: never mixed with the blocking reasons), a
            failure, or the contract's own statement for a run that accepts no
            further control.
          */}
          <p className="control-strip__slot" data-control-message>
            {execution !== null && execution.status === "refused" ? (
              <span data-control-refusal>
                <strong>
                  {execution.refusalKind ?? execution.code ?? "Refused"}.
                </strong>{" "}
                {execution.message}
              </span>
            ) : projection === null ? (
              ""
            ) : projection.failure !== null ? (
              <span data-execution-failure>
                <strong>{projection.failure.kind}</strong> at{" "}
                {projection.failure.subject}. {projection.failure.statement}
              </span>
            ) : blocked ? (
              "This draft is blocked, so there is no execution control to offer; the reasons are above."
            ) : CONTROLLABLE.has(projection.status) ? (
              ""
            ) : projection.status === "COMPLETED" ? (
              "This execution accepts no further control: a finished run is a record, not a handle."
            ) : (
              [projection.statement, ...projection.notes].join(" ")
            )}
          </p>
        </section>

        <HistoryCockpit
          held={history}
          selected={selectedOffset(frameState)}
          behindLive={boundariesBehindLive(frameState)}
          lag={historyLag(frameState)}
          onSelect={select}
          onReturnToLive={returnToLive}
          timestepMinutes={projection?.timestep_minutes ?? null}
          site={drawingSite}
        />
      </div>

      <p className="run-not-line" data-run-not-line>
        What this run is not: evidence. It is a draft of private simulator
        truth and staged envelopes; only a Commit releases them, through
        ingestion, and only what ingestion accepts reaches a site.
      </p>

      <Disclosure
        name="run-identity"
        summary={<span id="run-identity-heading">Run identity and frozen inputs</span>}
      >
        <RunHeader
          run={run}
          execution={execution}
          history={history}
          stage={stage}
        />
        {run.readiness_disclosure === null ? null : (
          <Panel
            heading="What ready does not assert"
            headingId="run-disclosure-heading"
          >
            <p>{run.readiness_disclosure}</p>
          </Panel>
        )}
        <ConfigurationBasisPanel basis={run.configuration_basis} />
        <Panel heading="The frozen inputs" headingId="run-frozen-heading" flush>
          <DataTable labelledBy="run-frozen-heading">
            <thead>
              <tr>
                <th scope="col">Input</th>
                <th scope="col">Frozen value</th>
                <th scope="col">Answered by</th>
                <th scope="col">Which record answered</th>
              </tr>
            </thead>
            <tbody>
              {run.frozen_inputs.map((row) => (
                <tr key={`${row.identity_field}-${row.field}`}>
                  <th scope="row">{row.field}</th>
                  <td>{row.value}</td>
                  <td>{row.answered_by}</td>
                  <td className="cell-secondary">
                    {row.answered_by_detail}
                    {/*
                      Beside the value it is about, not only in the table
                      below. Two same-type assets make two rows that differ by
                      a component id and two reasons that differ the same way,
                      and pairing them by eye across two tables is the work
                      this saves.
                    */}
                    {row.blocking_statement === null ? null : (
                      <span className="cell-note">{row.blocking_statement}</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </DataTable>
        </Panel>
        {run.unsupported_optional_inputs.length === 0 ? null : (
          <Panel
            heading="Optional inputs this profile does not support"
            headingId="run-optional-heading"
          >
            <ul className="cell-list">
              {run.unsupported_optional_inputs.map((item) => (
                <li key={`${item.state_key}-${item.execution_role}`}>
                  {item.statement}
                </li>
              ))}
            </ul>
          </Panel>
        )}
      </Disclosure>

      <Disclosure name="execution-provenance" summary="Execution provenance">
        {projection === null ? (
          <p>No execution is loaded.</p>
        ) : (
          <>
            {/*
              The status on an attribute as well as in the badge, so a browser
              measurement can wait for a run to reach one.
            */}
            <p
              data-execution-statement
              data-execution-status={projection.status}
              data-execution-simulation-time={projection.simulation_time}
            >
              {projection.statement}
            </p>
            <FactList>
              <Fact term="Simulated time">{projection.simulation_time}</Fact>
              <Fact term="Offset from the interval start">
                {`${projection.offset_minutes} minutes`}
              </Fact>
              <Fact term="Boundaries covered">
                {`${projection.boundaries_completed} of ${projection.boundaries_total}`}
              </Fact>
              <Fact term="Timestep">
                {`${projection.timestep_minutes} minutes`}
              </Fact>
              <Fact term="Seed">{String(projection.seed)}</Fact>
              <Fact term="Kernel version">
                {String(projection.kernel_version)}
              </Fact>
              <Fact term="Model profile">
                {`${projection.model_profile_id} v${projection.model_profile_version}`}
              </Fact>
              <Fact term="Publication profile">
                {`${projection.publication_profile_id} v${projection.publication_profile_version}`}
              </Fact>
              <Fact term="Numeric policy">
                {`${projection.numeric_policy} v${projection.numeric_policy_version}`}
              </Fact>
              <Fact term="Execution contract">
                {`v${projection.execution_contract_version}`}
              </Fact>
              <Fact term="Frozen inputs identity">
                {projection.inputs_identity === ""
                  ? "not computed until this run is started"
                  : projection.inputs_identity}
              </Fact>
              {/*
                Two digests, not one. The world's identity excludes the reporting
                path deliberately, so a trajectory digest alone is identical for
                two runs whose readings differ - correct about the world and
                useless for checking the transform.
              */}
              <Fact term="Trajectory digest">
                {projection.content_digest ??
                  "not computed until this run reaches an outcome"}
              </Fact>
              <Fact term="Reading series digest">
                {projection.observation_series_digest}
              </Fact>
              <Fact term="Readings published">
                {String(projection.reported_count)}
              </Fact>
              <Fact term="Samples suppressed by a reporting gap">
                {String(projection.suppressed_by_gap_count)}
              </Fact>
              <Fact term="Publications dropped">
                {String(projection.dropped_count)}
              </Fact>
            </FactList>
            {projection.notes.length === 0 ? null : (
              <ul className="cell-list">
                {projection.notes.map((note) => (
                  <li key={note}>{note}</li>
                ))}
              </ul>
            )}
          </>
        )}
      </Disclosure>

      <Disclosure
        name="latest-step"
        summary="Latest step on the execution clock: the world, electrical and generator panels, readings"
      >
        {projection === null || projection.private_state.length === 0 ? null : (
          <Panel
            heading="What the world holds"
            headingId="run-private-heading"
            flush
          >
            <DataTable labelledBy="run-private-heading">
              <thead>
                <tr>
                  <th scope="col">State</th>
                  <th scope="col">True value</th>
                  <th scope="col">Unit</th>
                </tr>
              </thead>
              <tbody>
                {projection.private_state.map((row) => (
                  <tr key={row.address} data-private-state={row.address}>
                    <th scope="row">{row.address}</th>
                    <td>
                      <ExactQuantity value={row.value} />
                    </td>
                    <td>{row.canonical_unit}</td>
                  </tr>
                ))}
              </tbody>
            </DataTable>
          </Panel>
        )}
        {projection === null || projection.electrical === null ? null : (
          <ElectricalPanels electrical={projection.electrical} />
        )}
        {projection === null || projection.observations.length === 0 ? null : (
          <Panel
            heading="What each device reported"
            headingId="run-observations-heading"
            flush
          >
            <DataTable labelledBy="run-observations-heading">
              <thead>
                <tr>
                  <th scope="col">Device and signal</th>
                  <th scope="col">State</th>
                  <th scope="col">True value</th>
                  <th scope="col">Reported value</th>
                  <th scope="col">Source sample time</th>
                  <th scope="col">Quality</th>
                  <th scope="col">This instant</th>
                </tr>
              </thead>
              <tbody>
                {projection.observations.map((row) => (
                  <tr
                    key={`${row.device_id}-${row.signal_id}`}
                    data-observation={`${row.device_id}:${row.signal_id}`}
                  >
                    <th scope="row">{`${row.device_id} / ${row.signal_id}`}</th>
                    <td>{row.address}</td>
                    <td data-observation-true>
                      {row.true_value === null ? (
                        "not measured here"
                      ) : (
                        <ExactQuantity
                          value={row.true_value}
                          unit={row.canonical_unit}
                        />
                      )}
                    </td>
                    <td data-observation-reported>
                      {row.reported_value === null ? (
                        "no reading"
                      ) : (
                        <ExactQuantity
                          value={row.reported_value}
                          unit={row.canonical_unit}
                        />
                      )}
                    </td>
                    <td data-observation-source-time>
                      {row.reported_source_time ?? "no reading"}
                    </td>
                    <td data-observation-quality={row.quality}>{row.quality}</td>
                    <td
                      className="cell-secondary"
                      data-observation-outcome={
                        row.due ? row.outcome ?? "DUE" : "NOT_DUE"
                      }
                    >
                      {row.due ? row.outcome ?? "due" : "not due"}
                      {row.suppression_reason === null ? null : (
                        <span className="cell-note">
                          {row.suppression_reason}
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </DataTable>
          </Panel>
        )}
        {projection === null ||
        projection.recent_reports.length === 0 ? null : (
          <Panel
            heading="The newest sample attempts"
            headingId="run-reports-heading"
            flush
          >
            <DataTable labelledBy="run-reports-heading">
              <thead>
                <tr>
                  <th scope="col">Taken at</th>
                  <th scope="col">Device and signal</th>
                  <th scope="col">Outcome</th>
                  <th scope="col">Reported value</th>
                  <th scope="col">Why not</th>
                </tr>
              </thead>
              <tbody>
                {projection.recent_reports.map((report) => (
                  <tr
                    key={`${report.device_id}-${report.signal_id}-${report.at_offset_minutes}`}
                    data-sample-attempt={`${report.device_id}:${report.signal_id}:${report.at_offset_minutes}`}
                  >
                    <th scope="row">{report.source_sample_time}</th>
                    <td>{`${report.device_id} / ${report.signal_id}`}</td>
                    <td>{report.outcome}</td>
                    <td>
                      {report.reported_value === null ? (
                        "nothing published"
                      ) : report.canonical_unit === "state" ? (
                        // T025b: a status member is text, never "RUNNING state".
                        <ExactQuantity
                          value={report.reported_value}
                          unit={report.canonical_unit}
                        />
                      ) : (
                        `${report.reported_value} ${report.canonical_unit}`
                      )}
                    </td>
                    <td className="cell-secondary">
                      {report.suppression_reason ?? ""}
                    </td>
                  </tr>
                ))}
              </tbody>
            </DataTable>
          </Panel>
        )}
      </Disclosure>

      <Disclosure name="reporting-paths" summary="Reporting paths and declared gaps">
        {projection === null || projection.signals.length === 0 ? null : (
          <Panel
            heading="The configured reporting paths"
            headingId="run-signals-heading"
            flush
          >
            <DataTable labelledBy="run-signals-heading">
              <thead>
                <tr>
                  <th scope="col">Device and signal</th>
                  <th scope="col">Reads</th>
                  <th scope="col">Publishes every</th>
                  <th scope="col">Bias</th>
                  {quantized ? <th scope="col">Published to the nearest</th> : null}
                  <th scope="col">Samples lost per thousand</th>
                </tr>
              </thead>
              <tbody>
                {projection.signals.map((signal) => (
                  <tr
                    key={`${signal.device_id}-${signal.signal_id}`}
                    data-signal={`${signal.device_id}:${signal.signal_id}`}
                  >
                    <th scope="row">
                      {`${signal.device_id} / ${signal.signal_id}`}
                    </th>
                    <td>
                      {`${signal.address} (${signal.reading_class})`}
                    </td>
                    <td>{`${signal.cadence_minutes} minutes`}</td>
                    <td>{`${signal.bias} ${signal.canonical_unit}`}</td>
                    {quantized ? (
                      <td data-signal-resolution={signal.resolution ?? "EXACT"}>
                        {signal.resolution === null || signal.resolution === undefined
                          ? "exact (not rounded)"
                          : `${signal.resolution} ${signal.canonical_unit}`}
                      </td>
                    ) : null}
                    <td>{String(signal.dropout_per_thousand)}</td>
                  </tr>
                ))}
              </tbody>
            </DataTable>
            {quantized ? (
              <p className="note" data-signal-resolution-note>
                Each simulated device adds its bias, then rounds the reading
                half-to-even to the step shown before publishing it. Subtracting
                the bias from a reported value therefore gives the true value at
                that reading&apos;s own time only to within half a step, and a
                reading kept across a reporting gap still describes its own
                earlier time, not the value the gap hid.
              </p>
            ) : null}
          </Panel>
        )}
        {projection === null ||
        projection.reporting_gaps.length === 0 ? null : (
          <Panel
            heading="Declared reporting gaps"
            headingId="run-gaps-heading"
            flush
          >
            <DataTable labelledBy="run-gaps-heading">
              <thead>
                <tr>
                  <th scope="col">Declared by</th>
                  <th scope="col">Silences</th>
                  <th scope="col">Declared as</th>
                  <th scope="col">Declared at offset</th>
                  <th scope="col">Covers from offset</th>
                  <th scope="col">Up to offset</th>
                </tr>
              </thead>
              <tbody>
                {projection.reporting_gaps.map((gap) => (
                  <tr
                    key={`${gap.event_id}-${gap.device_id}-${gap.signal_id}`}
                    data-reporting-gap={gap.event_id}
                  >
                    <th scope="row">{gap.event_id}</th>
                    <td>{`${gap.device_id} / ${gap.signal_id}`}</td>
                    {/*
                      The shape the document declared, the instant it declared,
                      and the span that instant resolved to - three columns,
                      because for a POINT the declared instant is not where the
                      outage starts. One column showing the resolved start under
                      the heading "From offset" read as the authored number and
                      was not it.
                    */}
                    <td data-reporting-gap-shape={gap.timing_shape}>
                      {gap.timing_shape}
                    </td>
                    <td data-reporting-gap-declared-at>
                      {String(gap.declared_offset_minutes)}
                    </td>
                    <td>{String(gap.start_offset_minutes)}</td>
                    <td>{String(gap.end_offset_minutes)}</td>
                  </tr>
                ))}
              </tbody>
            </DataTable>
          </Panel>
        )}
      </Disclosure>

      <Disclosure name="history-facts" summary="Recorded history: source, digest and coverage">
        <HistoryFacts held={history} />
      </Disclosure>

      <Disclosure name="raw-records" summary="Raw records at the history cursor">
        <HistoryRecordsAtCursor
          held={history}
          selected={selectedOffset(frameState)}
          mapping={stage !== null && stage.status === "loaded" ? stage.stage.mapping : null}
        />
      </Disclosure>

      <Disclosure name="stage" summary="Stage and staged envelopes">
        <Panel
          heading="Staged source envelopes"
          headingId="run-stage-heading"
        >
          {/* T025b, narrowed by T026 AC14: a typed status the run observes is
              named here only when the mapping this stage froze leaves it out,
              so the stage is not read as the whole of what the run reports.
              A mapping that stages it says nothing of the kind, and nothing
              here claims Commit or acceptance: those are the Commit panel's
              facts (T027), read from the Commit and from ingestion. */}
          {projection === null ||
          stage === null ||
          stage.status !== "loaded" ||
          stage.stage.mapping === null
            ? null
            : projection.signals
                .filter(
                  (signal) =>
                    signal.canonical_unit === "state" &&
                    !stagedSignal(stage.stage.mapping, signal),
                )
                .map((signal) => (
                  <p
                    key={`${signal.device_id}-${signal.signal_id}`}
                    className="note"
                    data-stage-unstaged-signal={`${signal.device_id}:${signal.signal_id}`}
                  >
                    <strong>{`${signal.device_id} / ${signal.signal_id} is observed, not staged.`}</strong>{" "}
                    {signal.statement}
                  </p>
                ))}
          {stage === null ? (
            <p>Loading the staged source envelopes.</p>
          ) : stage.status === "not_found" ? (
            <p>No stage surface answered for this run identity.</p>
          ) : stage.status === "unavailable" ? (
            <p data-stage-unavailable>
              {stage.message ??
                "The stage could not be read, so nothing is known about what was staged."}
            </p>
          ) : stage.status === "gateway" ? (
            <>
              <GatewayLedgerView stage={stage.stage} frozenBasis={stage.frozenBasis} />
              {runId === undefined ? null : (
                <PublicationSchedulePanel
                  runId={runId}
                  runSetup={runSetup}
                  refreshKey={stage}
                  onAdvanced={() => void rereadStage()}
                />
              )}
              <GatewayDiagnosticsPanel runSetup={runSetup} refreshKey={stage} />
            </>
          ) : (
            <>
              <p
                data-stage-statement
                data-stage-status={stage.stage.status}
                data-stage-count={stage.stage.envelopes.length}
                data-stage-execution={stage.stage.execution_status}
              >
                {stage.stage.statement}
              </p>
              {stage.frozenBasis ? (
                <p
                  data-stage-basis={stage.frozenBasis.configuration_store}
                  data-stage-can-release={String(stage.frozenBasis.can_release)}
                >
                  <strong>
                    {stage.frozenBasis.configuration_store === "REGISTERED"
                      ? "Registered configuration."
                      : "Legacy Site file."}
                  </strong>{" "}
                  {stage.frozenBasis.statement}
                </p>
              ) : null}
              {stage.stage.unreadable_detail === null ? null : (
                <p data-stage-unreadable>
                  <strong>Integrity check failed.</strong>{" "}
                  {stage.stage.unreadable_detail}
                </p>
              )}
              <FactList>
                <Fact term="Stage status">{stage.stage.status}</Fact>
                <Fact term="Release eligibility">
                  <span
                    data-stage-release={
                      stage.stage.release_eligible ? "ELIGIBLE" : "NOT_ELIGIBLE"
                    }
                  >
                    {stage.stage.release_eligible
                      ? "Eligible. Commit seals this stage and releases it through ingestion; see Commit and release."
                      : "Not eligible"}
                  </span>
                </Fact>
                <Fact term="Envelope schema">
                  {`${stage.stage.envelope_schema_id} v${stage.stage.envelope_schema_version}`}
                </Fact>
                <Fact term="Stage schema">
                  {`v${stage.stage.stage_schema_version}`}
                </Fact>
                {stage.stage.mapping === null ? null : (
                  <>
                    <Fact term="Frozen mapping">
                      {`${stage.stage.mapping.mapping_set_id} v${stage.stage.mapping.mapping_version}`}
                    </Fact>
                    <Fact term="Publication latency">
                      {`${stage.stage.mapping.publication_latency_seconds} seconds after the sample`}
                    </Fact>
                  </>
                )}
                {stage.stage.site_id === null ? null : (
                  <Fact term="Site, source and gateway">
                    {`${stage.stage.site_id} / ${stage.stage.source_id ?? ""} / ${stage.stage.gateway_id ?? ""}`}
                  </Fact>
                )}
                {stage.stage.published_through === null ? null : (
                  <Fact term="Published through">
                    <span data-stage-published-through>
                      {`boundary ${stage.stage.published_through} of ${stage.stage.boundaries_total ?? "?"}`}
                    </span>
                  </Fact>
                )}
                <Fact term="Envelopes staged">
                  {String(stage.stage.envelopes.length)}
                </Fact>
                <Fact term="Integrity digest">
                  {stage.stage.integrity_digest ?? "none"}
                </Fact>
              </FactList>
              {stage.stage.release_blockers.length === 0 ? null : (
                <ul className="cell-list" data-stage-blockers>
                  {stage.stage.release_blockers.map((blocker) => (
                    <li key={blocker.kind} data-stage-blocker={blocker.kind}>
                      <strong>{blocker.kind}.</strong> {blocker.statement}
                    </li>
                  ))}
                </ul>
              )}
              {stage.stage.refused_publications.length === 0 ? null : (
                <ul className="cell-list">
                  {stage.stage.refused_publications.map((item) => (
                    <li key={item.message_id}>
                      {`${item.kind}: ${item.message_id}`}
                    </li>
                  ))}
                </ul>
              )}
            </>
          )}
        </Panel>

        {stage === null ||
        stage.status !== "loaded" ||
        stage.stage.mapping === null ? null : (
          <Panel
            heading="The allowlist this stage froze"
            headingId="run-stage-mapping-heading"
            flush
          >
            <DataTable labelledBy="run-stage-mapping-heading">
              <thead>
                <tr>
                  <th scope="col">Device and signal</th>
                  <th scope="col">Published as</th>
                  <th scope="col">Unit</th>
                  <th scope="col">Publishes unavailability</th>
                </tr>
              </thead>
              <tbody>
                {stage.stage.mapping.entries.map((entry) => (
                  <tr key={`${entry.device_id}-${entry.signal_id}`}>
                    <th scope="row">{`${entry.device_id} / ${entry.signal_id}`}</th>
                    <td data-stage-mapping-family={entry.family ?? "MEASUREMENT"}>
                      {publishedAs(entry)}
                    </td>
                    <td>{entry.unit}</td>
                    <td>{entry.publishes_unavailable ? "yes" : "no"}</td>
                  </tr>
                ))}
              </tbody>
            </DataTable>
          </Panel>
        )}

        {stage === null ||
        stage.status !== "loaded" ||
        stage.stage.envelopes.length === 0 ? null : (
          <StagedEnvelopes
            envelopes={stage.stage.envelopes}
            publications={
              history !== null && history.status === "loaded"
                ? history.history.publications
                : null
            }
            selected={selectedMessage}
            onSelect={setSelectedMessage}
          />
        )}
      </Disclosure>

      {runId === undefined ? null : (
        <RunCommitPanel runId={runId} runSetup={runSetup} stage={stage} />
      )}

      <Disclosure name="run-not" summary="What this run is not, in full">
        <Panel heading="What this run is not" headingId="run-not-heading">
          <ul className="cell-list">
            <li>
              What it produced is private simulator truth and the readings a
              configured device would have published from it. Neither is evidence,
              and none of the private truth ever enters ingestion.
            </li>
            <li>
              Its staged source envelopes are staged and nothing more. Staging
              releases nothing, and a staged envelope is not evidence about
              anywhere.
            </li>
            <li>
              Only a Commit releases them: it seals the eligible stage as an
              immutable artifact and sends it through ingestion. Whether this
              draft was committed, and what ingestion accepted, rejected or
              found duplicate, is reported under Commit and release, separately.
            </li>
            <li>
              Executing a draft writes to no site. An operator surface shows
              only what ingestion accepted from a Commit, never the stage or
              the run.
            </li>
            <li>
              No conclusion has been drawn from it. A reading a run generated is
              what a sensor would have said, not a finding about anywhere.
            </li>
          </ul>
        </Panel>
      </Disclosure>
    </>,
  );
}

/**
 * The staged envelopes: one row of metadata each, and one exact text on demand.
 *
 * The row splits out what a reader compares - identity, source time,
 * publication time, value and quality - and the selected envelope is shown as
 * its canonical text, exactly as persisted, beside its metadata. The newest is
 * selected until a reader chooses another, because the newest is what a reader
 * stepping a run has just caused.
 */
function StagedEnvelopes({
  envelopes,
  publications,
  selected,
  onSelect,
}: {
  envelopes: RunStagedEnvelope[];
  /** The held history's publication rows; null while no history is held. */
  publications: RunHistoryPublication[] | null;
  selected: string | null;
  onSelect: (messageId: string) => void;
}) {
  const shown =
    envelopes.find((item) => item.message_id === selected) ??
    envelopes[envelopes.length - 1];
  const arrival = envelopeArrival(shown, publications);

  return (
    <>
      <Panel
        heading="The selected envelope, exactly as staged"
        headingId="run-stage-selected-heading"
      >
        <FactList>
          <Fact term="Message ID">{shown.message_id}</Fact>
          <Fact term="Sequence">{String(shown.sequence)}</Fact>
          <Fact term="Device and signal">
            {`${shown.device_id} / ${shown.signal_id}`}
          </Fact>
          <Fact term="Mapping">
            {`${shown.mapping_set_id} v${shown.mapping_version}`}
          </Fact>
          <Fact term="Envelope schema">{`v${shown.schema_version}`}</Fact>
          <Fact term="Source time">
            <span data-stage-selected-source-time>{shown.source_time}</span>
          </Fact>
          <Fact term="Published at">
            <span data-stage-selected-published-at>{shown.published_at}</span>
          </Fact>
          <Fact term="Arrival">
            <span data-stage-selected-arrival={arrival.kind}>{arrival.text}</span>
          </Fact>
          <Fact term={isRecord(shown) ? "Record" : "Measurement"}>
            {isRecord(shown)
              ? `${shown.family} record: present, so it has no quality`
              : shown.interval_start === null
                ? shown.measurement
                : `${shown.measurement} over ${shown.interval_start} to ${shown.interval_end ?? ""}`}
          </Fact>
        </FactList>
        <pre
          className="canonical-text"
          data-stage-canonical={shown.message_id}
        >
          {shown.canonical}
        </pre>
      </Panel>
      <Panel
        heading="Every staged envelope"
        headingId="run-stage-envelopes-heading"
        flush
      >
        <DataTable labelledBy="run-stage-envelopes-heading">
          <thead>
            <tr>
              <th scope="col">Sequence</th>
              <th scope="col">Device and signal</th>
              <th scope="col">Source time</th>
              <th scope="col">Published at</th>
              <th scope="col">Value</th>
              <th scope="col">Quality</th>
              <th scope="col">Exact envelope</th>
            </tr>
          </thead>
          <tbody>
            {envelopes.map((item) => (
              <tr key={item.message_id} data-staged-envelope={item.message_id}>
                <th scope="row">{String(item.sequence)}</th>
                <td>{`${item.device_id} / ${item.signal_id}`}</td>
                <td data-staged-source-time>{item.source_time}</td>
                <td data-staged-published-at>{item.published_at}</td>
                <td data-staged-value>
                  {item.value === null
                    ? `no value (${item.unavailable_reason ?? "unavailable"})`
                    : `${item.value} ${item.unit}`}
                </td>
                <td data-staged-quality={isRecord(item) ? "RECORD" : item.quality}>
                  {isRecord(item) ? `${item.family} record` : item.quality}
                </td>
                <td>
                  <button
                    type="button"
                    className="action"
                    aria-pressed={item.message_id === shown.message_id}
                    onClick={() => onSelect(item.message_id)}
                  >
                    {`Show envelope ${item.sequence}`}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </DataTable>
      </Panel>
    </>
  );
}

/** T026: a policy or operational record, which has no measurement or quality. */
function isRecord(envelope: RunStagedEnvelope): boolean {
  return envelope.family !== undefined && envelope.family !== "MEASUREMENT";
}

/** What a mapping entry publishes, in words: a measurement class, an enum, a record. */
function publishedAs(entry: RunStageMappingEntry): string {
  if (entry.family !== undefined && entry.family !== "MEASUREMENT") {
    return `${entry.family} record`;
  }
  if (entry.members !== undefined && entry.members !== null) {
    return `${entry.measurement}, one of ${entry.members.join(", ")}`;
  }
  return entry.measurement;
}

/**
 * T026 AC10: how the selected envelope arrived, told apart from a sensor gap.
 *
 * A publication delay is read from the history's held row for this envelope
 * (same device, signal and source time), whose `held_minutes` is the host's;
 * nothing here subtracts times. An `UNAVAILABLE` envelope says its reason
 * (`unavailableArrival`, shared with the inspector): only a reporting-path
 * outage is a sensor gap.
 */
function envelopeArrival(
  envelope: RunStagedEnvelope,
  publications: RunHistoryPublication[] | null,
): { kind: string; text: string } {
  const held =
    publications?.find(
      (p) =>
        p.device_id === envelope.device_id &&
        p.signal_id === envelope.signal_id &&
        p.source_time === envelope.source_time,
    ) ?? null;
  if (held !== null) {
    return {
      kind: "DELAYED",
      text:
        `Publication delay: held ${held.held_minutes} min by ${held.delay_event_id}. ` +
        "The source time is unchanged; only the publication time is later. Not a sensor gap.",
    };
  }
  if (envelope.quality === "UNAVAILABLE") {
    return unavailableArrival(envelope.unavailable_reason ?? null);
  }
  if (publications === null) {
    return {
      kind: "UNKNOWN",
      text: "No history is held, so whether a delay held it is not shown.",
    };
  }
  return { kind: "ON_TIME", text: "No publication delay is recorded for it." };
}

/** What each stop reason says. The reason is also on an attribute. */
const STOP_STATEMENTS: Record<PlaybackStopReason, string> = {
  PAUSED:
    "Paused. No further step is sent; a step already sent was allowed to finish and is shown.",
  TERMINAL: "Stopped: the run reached a status that accepts no further step.",
  REFUSED:
    "Stopped: the host refused the step. The position was re-read; resume explicitly.",
  STEP_ALREADY_APPLIED:
    "Stopped: the run was no longer where this page believed (another tab or a late step moved it). The position was re-read; resume explicitly.",
  TIMEOUT:
    "Stopped: a step did not answer in time. The position was re-read; resume explicitly. Nothing was retried.",
  NETWORK:
    "Stopped: a step request did not complete. The position was re-read; resume explicitly. Nothing was retried.",
  NOT_FOUND:
    "Stopped: the execution surface did not answer for this run (the Lab may have been disabled).",
  HIDDEN: "Paused because this tab was hidden. Resume explicitly.",
};

function playbackStatement(state: PlaybackState): string {
  if (state.kind === "playing") {
    // T025e AC11: one stable sentence for the whole of play. Whether a step
    // is in flight is an attribute on this line, not a second text per tick.
    return "Playing: one step, its record, then the wall delay.";
  }
  if (state.kind === "pausing") {
    return "Pausing: the step already sent is awaited and will be shown.";
  }
  if (state.reason === null) {
    return "Paused. Auto-play has not been started on this page; a reload always starts paused.";
  }
  return STOP_STATEMENTS[state.reason];
}

/**
 * The playback state as the page renders it. Whether a step is in flight is
 * dropped: it changes twice per tick and is written onto the status line's
 * `data-playback-in-flight` attribute directly, so it costs no render.
 */
export function shownPlayback(
  previous: PlaybackState,
  next: PlaybackState,
): PlaybackState {
  if (next.kind === "playing") {
    return previous.kind === "playing" && !previous.inFlight
      ? previous
      : { kind: "playing", inFlight: false };
  }
  if (
    next.kind === previous.kind &&
    (next.kind === "pausing" ||
      (previous.kind === "stopped" &&
        next.kind === "stopped" &&
        next.reason === previous.reason &&
        next.message === previous.message))
  ) {
    return previous;
  }
  return next;
}

/**
 * T025d: auto-play of the guarded Step, and nothing else.
 *
 * Playback state is its own fact, kept apart from the execution status above,
 * the selected history cursor below and the stage: a paused page over a
 * RUNNING execution is the ordinary case, and a run that stops being RUNNING
 * stops auto-play rather than the other way round. T025e: compact, in the
 * control strip; its status sentence sits in a fixed slot.
 */
function PlaybackControls({
  state,
  delayMs,
  canPlay,
  onDelay,
  onPlay,
  onPause,
  statusRef,
  executionStatus,
}: {
  state: PlaybackState;
  delayMs: number;
  canPlay: boolean;
  onDelay: (ms: number) => void;
  onPlay: () => void;
  onPause: () => void;
  statusRef: React.RefObject<HTMLParagraphElement>;
  executionStatus: string;
}) {
  const reason = state.kind === "stopped" ? state.reason : null;
  return (
    <section
      className="control-strip__playback"
      aria-labelledby="run-playback-heading"
      data-playback-state={state.kind}
      data-playback-reason={reason ?? ""}
    >
      <h3 id="run-playback-heading" className="control-strip__subheading">
        Auto-play
      </h3>
      <label htmlFor="run-playback-delay">Wall delay between steps</label>{" "}
      <select
        id="run-playback-delay"
        value={String(delayMs)}
        onChange={(event) => onDelay(Number(event.target.value))}
      >
        {PLAYBACK_DELAYS_MS.map((ms) => (
          <option key={ms} value={String(ms)}>
            {`${ms / 1000} s`}
          </option>
        ))}
      </select>{" "}
      <button
        type="button"
        className="action"
        disabled={!canPlay}
        onClick={onPlay}
      >
        {reason === null ? "Play" : "Resume"}
      </button>{" "}
      <button
        type="button"
        className="action"
        disabled={state.kind !== "playing"}
        onClick={onPause}
      >
        Pause
      </button>
      <p
        ref={statusRef}
        className="control-strip__status"
        data-playback-statement
        role="status"
      >
        <strong>Playback:</strong> {playbackStatement(state)}
        {state.kind === "stopped" && state.message !== null
          ? ` ${state.message}`
          : ""}
        {executionStatus === "RUNNING" || state.kind !== "stopped"
          ? ""
          : ` Auto-play needs a RUNNING execution this host still holds; this one is ${executionStatus}.`}
      </p>
    </section>
  );
}

/**
 * The configuration this run was set up from (S2-01a).
 *
 * A registered basis names the exact Foundation and binding revisions, the
 * snapshot hash and the two instants that selected them. The Site's name, time
 * zone and type are labelled for what they are: the Site's current record as
 * read at setup and frozen on this Draft, not facts selected by the knowledge
 * time.
 */
export function ConfigurationBasisPanel({
  basis,
}: {
  basis: RunConfigurationBasis | undefined;
}) {
  return (
    <Panel heading="Configuration basis" headingId="run-basis-heading">
      {basis === undefined ? (
        <p data-run-basis="UNREPORTED">
          This run's configuration basis was not reported.
        </p>
      ) : basis.store === "LEGACY_FILE" ? (
        <p data-run-basis="LEGACY_FILE">
          Set up from the legacy Site file (LEGACY_FILE). It is read as frozen
          history and is never reinterpreted under a later registration.
        </p>
      ) : (
        <>
          <p data-run-basis="REGISTERED">
            Set up from the registered Site configuration below, frozen when
            this draft was created. It is configuration, not accepted evidence.
          </p>
          <FactList>
            <Fact term="Foundation revision">
              {`Version ${basis.foundation_version}, valid from ${basis.foundation_valid_from}` +
                (basis.foundation_valid_to === null ? "" : ` to ${basis.foundation_valid_to}`)}
              <span className="cell-secondary"> <code>{basis.foundation_revision_id}</code></span>
            </Fact>
            <Fact term="Signal bindings">
              {`Version ${basis.binding_set_version}, valid from ${basis.binding_valid_from}` +
                (basis.binding_valid_to === null ? "" : ` to ${basis.binding_valid_to}`)}
              <span className="cell-secondary"> <code>{basis.binding_set_revision_id}</code></span>
            </Fact>
            <Fact term="Configuration snapshot">
              <code data-run-basis-sha256>{basis.snapshot_sha256}</code>{" "}
              ({basis.snapshot_schema}, {basis.snapshot_byte_length} bytes)
            </Fact>
            <Fact term="Selected for">
              {`Source time ${basis.source_start}, as known at ${basis.knowledge_at}`}
              {basis.selection === "HISTORICAL"
                ? " (an earlier configuration, since replaced or ended)"
                : ""}
            </Fact>
            {basis.current_registration_gaps.length === 0 ? null : (
              <Fact term="Current registration gaps">
                {basis.current_registration_gaps.join(", ")}
              </Fact>
            )}
            <Fact term="Site name and time zone">
              <span data-run-basis-site-metadata={basis.site_metadata.source}>
                {`${basis.site_metadata.display_name}, ${basis.site_metadata.timezone}`}
              </span>
              <span className="cell-secondary">
                {" "}
                The Site's current record as read when this draft was created,
                frozen here. Not chosen by the knowledge time.
              </span>
            </Fact>
          </FactList>
        </>
      )}
    </Panel>
  );
}
