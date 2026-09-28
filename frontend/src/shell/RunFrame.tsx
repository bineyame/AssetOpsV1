import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { Badge, DataTable, Fact, FactList, PageHeader, Panel } from "../ui";
import type {
  RunDetailResult,
  RunExecutionResult,
  RunSetupClient,
} from "./runSetupClient";

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
 * There is no pause, no reset, no event injection, no truth overlay on an
 * operator screen, no staged gateway message, no commit and no bridge into the
 * operator product, and none of them appears here in any form. The rule
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
 */
export interface RunFrameProps {
  runSetup: RunSetupClient;
  runsPath: string;
  simulatorLabPath: string;
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
}: RunFrameProps) {
  const { runId } = useParams<{ runId: string }>();
  const [result, setResult] = useState<RunDetailResult | null>(null);
  const [execution, setExecution] = useState<RunExecutionResult | null>(null);
  const [pending, setPending] = useState(false);
  const [boundaries, setBoundaries] = useState("1");

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
    void runSetup.getExecution(runId).then((loaded) => {
      if (active) {
        setExecution(loaded);
      }
    });

    return () => {
      active = false;
    };
  }, [runSetup, runId]);

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
    async (act: () => Promise<RunExecutionResult>) => {
      setPending(true);
      const answer = await act();
      setExecution(answer);
      setPending(false);
    },
    [],
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
  const requested = Number.parseInt(boundaries, 10);
  const stepSize = Number.isNaN(requested) ? 0 : requested;

  return frame(
    <>
      <Panel heading="This run" headingId="run-identity-heading">
        <FactList>
          <Fact term="Run ID">{run.run_id}</Fact>
          <Fact term="Lifecycle status">{run.lifecycle_status}</Fact>
          <Fact term="Execution status">{run.execution_status}</Fact>
          <Fact term="Site">{run.site_id}</Fact>
          <Fact term="Scenario">{run.scenario_id}</Fact>
          <Fact term="Scenario version">{String(run.scenario_version)}</Fact>
          <Fact term="Set up">{run.created_at}</Fact>
        </FactList>
        <p>
          Nothing on this screen stages a gateway message, releases a source
          envelope, commits anything, or writes to any site. Executing a draft
          produces private simulator truth and the readings a configured device
          would have published from it, and both stay in this workspace.
        </p>
      </Panel>

      {run.readiness_disclosure === null ? null : (
        <Panel
          heading="What ready does not assert"
          headingId="run-disclosure-heading"
        >
          <p>{run.readiness_disclosure}</p>
        </Panel>
      )}

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

      <Panel heading="Executing this run" headingId="run-execution-heading">
        {execution === null ? (
          <p>Loading the execution of the persisted run.</p>
        ) : execution.status === "not_found" ? (
          <p>
            No execution surface answered for this run identity, so there is
            nothing to start and nothing to show.
          </p>
        ) : execution.status === "unavailable" ? (
          <p data-execution-unavailable>
            {execution.message ??
              "The execution surface could not be reached, so nothing is known about whether this draft has been executed."}
          </p>
        ) : null}

        {/*
          A refused control, in its own region and never mixed with the blocking
          reasons above. Criterion 4: a start, step or run-to-end that was refused
          is a different fact from a draft that was never eligible, and a reader
          has to be able to tell which they are looking at.
        */}
        {execution !== null && execution.status === "refused" ? (
          <p data-control-refusal>
            <strong>{execution.refusalKind ?? "Refused"}.</strong>{" "}
            {execution.message}
          </p>
        ) : null}

        {projection === null ? null : (
          <>
            <p>
              <Badge tone="lifecycle">{projection.status}</Badge>
            </p>
            {/*
              The status on an attribute as well as in the badge, so a browser
              measurement can wait for a run to reach one. A tool that waited for
              text would be matching the sentence rather than the state.
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

            {projection.failure === null ? null : (
              <p data-execution-failure>
                <strong>{projection.failure.kind}</strong> at{" "}
                {projection.failure.subject}. {projection.failure.statement}
              </p>
            )}

            {projection.notes.length === 0 ? null : (
              <ul className="cell-list">
                {projection.notes.map((note) => (
                  <li key={note}>{note}</li>
                ))}
              </ul>
            )}

            {blocked ? (
              <p className="action-list__reason">
                This draft is blocked, so there is no execution control to
                offer. The reasons above are what stands in the way; a blocked
                draft stops being blocked by setting a new one up, not by
                being executed anyway.
              </p>
            ) : (
              <ul className="action-list">
                <li className="action-list__item">
                  <button
                    type="button"
                    className="action"
                    disabled={pending || projection.status !== "NOT_STARTED"}
                    onClick={() => {
                      void control(() =>
                        runSetup.startExecution(run.run_id),
                      );
                    }}
                  >
                    Start this run
                  </button>
                </li>
                <li className="action-list__item">
                  <label htmlFor="run-step-boundaries">
                    Boundaries to advance
                  </label>{" "}
                  <input
                    id="run-step-boundaries"
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
                  <p className="action-list__reason">
                    A step advances the simulated clock by that many boundaries
                    and says which boundary it is advancing from, so the same
                    step submitted twice advances once.
                  </p>
                </li>
                <li className="action-list__item">
                  <button
                    type="button"
                    className="action"
                    disabled={pending || projection.status !== "RUNNING"}
                    onClick={() => {
                      void control(() =>
                        runSetup.runExecutionToEnd(run.run_id),
                      );
                    }}
                  >
                    Run to the end
                  </button>
                </li>
              </ul>
            )}

            {CONTROLLABLE.has(projection.status) ? null : (
              <p className="action-list__reason">
                This execution accepts no further control. A finished, failed or
                interrupted run is a record rather than a handle, and advancing
                one would mean producing a second result under the first one's
                identity.
              </p>
            )}
          </>
        )}
      </Panel>

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
                  <td>{row.value}</td>
                  <td>{row.canonical_unit}</td>
                </tr>
              ))}
            </tbody>
          </DataTable>
        </Panel>
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
                    {row.true_value === null
                      ? "not measured here"
                      : `${row.true_value} ${row.canonical_unit}`}
                  </td>
                  <td data-observation-reported>
                    {row.reported_value === null
                      ? "no reading"
                      : `${row.reported_value} ${row.canonical_unit}`}
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
                  <td>{String(signal.dropout_per_thousand)}</td>
                </tr>
              ))}
            </tbody>
          </DataTable>
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
                    {report.reported_value === null
                      ? "nothing published"
                      : `${report.reported_value} ${report.canonical_unit}`}
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

      <Panel heading="What this run is not" headingId="run-not-heading">
        <ul className="cell-list">
          <li>
            What it produced is private simulator truth and the readings a
            configured device would have published from it. Neither is evidence,
            and nothing here has entered ingestion.
          </li>
          <li>
            Nothing has been staged for a gateway, and no source envelope
            exists.
          </li>
          <li>
            It is a draft and it cannot be committed. Committing is what makes
            simulated history permanent and releases evidence from it, and no
            slice in this build can do either.
          </li>
          <li>
            No evidence has been accepted from it, and no operator surface shows
            anything because of it. Executing a draft writes to no site.
          </li>
          <li>
            No conclusion has been drawn from it. A reading a run generated is
            what a sensor would have said, not a finding about anywhere.
          </li>
        </ul>
      </Panel>
    </>,
  );
}
