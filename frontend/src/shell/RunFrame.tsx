import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { DataTable, Fact, FactList, PageHeader, Panel } from "../ui";
import type { RunDetailResult, RunSetupClient } from "./runSetupClient";

/**
 * One Draft run: what it froze, and what it cannot do. A Simulator Lab
 * surface.
 *
 * ## The shell of a run that has never run
 *
 * This is a run detail screen for a product with no runtime, and the thing it
 * has to avoid is reading as one that is merely stopped. So there is no
 * clock, no progress, no elapsed or simulated time, no step or pause or reset
 * control, no truth overlay, no observation list, no staged message, no
 * commit affordance, no replay and no bridge into the operator product. Those
 * are absent rather than disabled: a disabled control says the capability
 * exists and is unavailable right now, which is a different and false claim.
 *
 * One control is rendered disabled, and the rule for which
 * (`D-2026-09-20-scenario-detail-affordances`) is that a disabled control
 * appears only when the action is native to the object being viewed and the
 * missing prerequisite is the next named causal capability. Running a draft
 * is native to a draft, and the prerequisite is the causal kernel. It is
 * rendered only for a `READY` draft: a blocked draft cannot be run for a
 * second, prior reason, and showing the same disabled button on both would
 * say the two are the same distance from working.
 *
 * ## What `READY` does not assert
 *
 * The disclosure comes from the run record rather than being written here.
 * It is a property of the status, so a caller reading the payload sees the
 * same sentence, and a screen that composed its own would be a second place
 * for that claim to drift.
 */
export interface RunFrameProps {
  runSetup: RunSetupClient;
  runsPath: string;
  simulatorLabPath: string;
}

export function RunFrame({
  runSetup,
  runsPath,
  simulatorLabPath,
}: RunFrameProps) {
  const { runId } = useParams<{ runId: string }>();
  const [result, setResult] = useState<RunDetailResult | null>(null);

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

    return () => {
      active = false;
    };
  }, [runSetup, runId]);

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
          This draft has not been executed. It has no state, no output, no
          staged gateway message and no accepted evidence, and nothing on this
          screen can produce any of those.
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

      <Panel
        heading="What can be done with this run"
        headingId="run-actions-heading"
      >
        <ul className="action-list">
          {blocked ? (
            <li className="action-list__item">
              <p className="action-list__reason">
                This draft is blocked, so there is no run action to offer. The
                reasons above are what stands in the way; changing the
                selected model profile or the scenario is how a draft stops
                being blocked, and that means setting a new one up.
              </p>
            </li>
          ) : (
            <li className="action-list__item">
              <button
                type="button"
                className="action"
                disabled
                aria-describedby="run-action-reason"
              >
                Run this draft
              </button>
              <p className="action-list__reason" id="run-action-reason">
                Nothing can execute a draft yet. Running one needs a causal
                kernel that initializes world state and steps it through the
                interval, and this build has none, so there is nothing for
                this control to do.
              </p>
            </li>
          )}
        </ul>
      </Panel>

      <Panel heading="What this run is not" headingId="run-not-heading">
        <ul className="cell-list">
          <li>
            It has not been executed, so there is no state trajectory, no
            simulated clock and no output of any kind.
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
            No evidence has been accepted from it, and no operator surface
            shows anything because of it.
          </li>
          <li>
            No conclusion has been drawn from it. A draft run is an intention
            to simulate, not a result.
          </li>
        </ul>
      </Panel>
    </>,
  );
}
