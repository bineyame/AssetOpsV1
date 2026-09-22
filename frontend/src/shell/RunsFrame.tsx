import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { DataTable, PageHeader, Panel } from "../ui";
import type { RunListResult, RunSetupClient } from "./runSetupClient";

/**
 * The Runs inventory: which Draft runs exist. A Simulator Lab surface.
 *
 * ## What a row says, and what it refuses to say
 *
 * A row says which run it is, which Site and Foundation version it is bound
 * to, which scenario version it froze, the interval it covers, and the two
 * statuses. Every value comes from the run record.
 *
 * It says nothing about what a run has done, because no run has done
 * anything. There is no progress column, no elapsed time, no source health,
 * no observation count and no evidence state - and the reason those are
 * absent rather than empty is that an empty one is not empty: a column of
 * zeroes is a measurement, and a dash is a claim that the thing exists and
 * has no value yet.
 *
 * ## What `READY` and `BLOCKED` mean here
 *
 * `Draft` is where a run is in its own life. `READY` and `BLOCKED` say
 * whether the selected model profile can execute what the scenario needs.
 * Neither says a run has run, been committed, produced evidence, or been
 * looked at by anything. The screen says so in words rather than leaving the
 * inventory to imply it.
 */
export interface RunsFrameProps {
  runSetup: RunSetupClient;
  runHref: (runId: string) => string;
  simulatorLabPath: string;
  scenariosPath: string;
}

export function RunsFrame({
  runSetup,
  runHref,
  simulatorLabPath,
  scenariosPath,
}: RunsFrameProps) {
  const [result, setResult] = useState<RunListResult | null>(null);

  useEffect(() => {
    let active = true;

    void runSetup.listRuns().then((loaded) => {
      if (active) {
        setResult(loaded);
      }
    });

    return () => {
      active = false;
    };
  }, [runSetup]);

  const backLinks = (
    <p>
      <Link to={simulatorLabPath}>Back to the Simulator Lab</Link>{" "}
      <Link to={scenariosPath}>Go to Scenarios</Link>
    </p>
  );

  return (
    <main aria-labelledby="runs-heading">
      <PageHeader
        title="Runs"
        headingId="runs-heading"
        subtitle="Developer workspace"
      />

      <Panel heading="What a draft run is" headingId="runs-explanation-heading">
        <p>
          Each of these is a draft: a set of frozen inputs a simulation would
          consume, recorded when somebody set the run up. Nothing here has
          been executed. There is no simulation output, no accepted evidence
          and no conclusion attached to any of them, because no causal runtime
          exists in this build.
        </p>
        <p>
          Ready and blocked describe whether the selected model profile can
          execute what the scenario needs. A blocked draft is a complete,
          inspectable record of a valid setup, not a failed one: open it to
          see what it froze and which reasons stand in the way.
        </p>
      </Panel>

      {result === null ? <p>Loading the persisted runs.</p> : null}

      {result?.status === "unavailable" ? (
        <Panel heading="Runs unavailable" headingId="runs-unavailable-heading">
          <p>
            The run store could not be read, so which runs exist is unknown.
            This is a statement about the store, not a statement that no run
            has been set up.
          </p>
        </Panel>
      ) : null}

      {result?.status === "loaded" && result.runs.length === 0 ? (
        <Panel heading="No draft runs yet" headingId="runs-empty-heading">
          <p>
            No run has been set up on this installation. A draft is created
            from a saved scenario, on that scenario&apos;s own page.
          </p>
        </Panel>
      ) : null}

      {result?.status === "loaded" && result.runs.length > 0 ? (
        <Panel heading="Draft runs" headingId="runs-table-heading" flush>
          <DataTable labelledBy="runs-table-heading">
            <thead>
              <tr>
                <th scope="col">Run</th>
                <th scope="col">Site</th>
                <th scope="col">Foundation</th>
                <th scope="col">Scenario</th>
                <th scope="col">Scenario version</th>
                <th scope="col">Lifecycle</th>
                <th scope="col">Execution</th>
                <th scope="col">Interval start</th>
                <th scope="col">Interval end</th>
                <th scope="col">Set up</th>
              </tr>
            </thead>
            <tbody>
              {result.runs.map((run) => (
                <tr key={run.run_id}>
                  <th scope="row">
                    <Link to={runHref(run.run_id)}>{run.run_id}</Link>
                  </th>
                  <td>{run.site_id}</td>
                  <td>{String(run.foundation_version)}</td>
                  <td>{run.scenario_id}</td>
                  <td>{String(run.scenario_version)}</td>
                  <td>{run.lifecycle_status}</td>
                  <td>{run.execution_status}</td>
                  <td>{run.interval.start_time}</td>
                  <td>{run.interval.end_time}</td>
                  <td className="cell-secondary">{run.created_at}</td>
                </tr>
              ))}
            </tbody>
          </DataTable>
        </Panel>
      ) : null}

      {backLinks}
    </main>
  );
}
