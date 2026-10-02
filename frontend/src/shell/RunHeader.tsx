import { Fact, FactList, Panel } from "../ui";
import type { RunHistoryResult } from "./runHistory";
import {
  templateLineageText,
  type RunExecutionResult,
  type RunStageResult,
  type RunSummary,
} from "./runSetupClient";

/**
 * The run header (T025c, criterion 6): what this run is, where it stands, and
 * what of it is recorded - each as its own fact.
 *
 * Four statuses are kept apart on purpose, because they answer different
 * questions and one can be complete while another is not: the execution
 * outcome (the port's), the recorded history's coverage (the artifact's), the
 * stage (staged envelopes and release eligibility) and the selection (which is
 * the charts', and moves nothing). Boundary counts are the port's own; nothing
 * here counts samples to guess a position.
 *
 * Every fact is read from the persisted run, the execution projection, the
 * history read and the stage read, so a completed run's header reloads from
 * its artifact with no live kernel and no host session.
 */
export function RunHeader({
  run,
  execution,
  history,
  stage,
}: {
  run: RunSummary;
  execution: RunExecutionResult | null;
  history: RunHistoryResult | null;
  stage: RunStageResult | null;
}) {
  const projection =
    execution !== null && execution.status === "loaded"
      ? execution.execution
      : null;
  const recorded =
    history !== null && history.status === "loaded" ? history.history : null;
  const answered = new Map<string, number>();
  for (const row of run.frozen_inputs) {
    answered.set(row.answered_by, (answered.get(row.answered_by) ?? 0) + 1);
  }
  const provenance =
    run.frozen_inputs.length === 0
      ? "no frozen input rows"
      : `${run.frozen_inputs.length} frozen inputs, answered by ${[...answered]
          .map(([by, count]) => `${by} (${count})`)
          .join(", ")}`;

  return (
    <Panel heading="Run header" headingId="run-header-heading">
      <FactList>
        <Fact term="Run and Site">
          <span data-header-run>{`${run.run_id} on Site ${run.site_id}`}</span>
          {`, scenario ${run.scenario_id} v${run.scenario_version}`}
        </Fact>
        {/* T025g AC9: frozen at setup; never re-read from the site. */}
        <Fact term="Site template lineage">
          <span data-header-template-lineage={run.template_lineage.state}>
            {templateLineageText(run.template_lineage)}
          </span>
        </Fact>
        {/* T025e AC10: "This run" merged here, each fact once. */}
        <Fact term="Lifecycle and readiness">
          <span data-header-lifecycle={run.lifecycle_status}>
            {`${run.lifecycle_status}; ${run.execution_status}; set up ${run.created_at}`}
          </span>
        </Fact>
        <Fact term="Frozen inputs">
          <span data-header-provenance>{provenance}</span>
          {projection === null || projection.inputs_identity === ""
            ? ""
            : `; identity ${projection.inputs_identity}`}
        </Fact>
        {projection === null ? (
          <Fact term="Execution">
            <span data-header-execution="">
              {execution === null
                ? "being read"
                : "not available from the execution port"}
            </span>
          </Fact>
        ) : (
          <>
            <Fact term="Window">
              <span data-header-window>
                {`${projection.interval_start_time} to ${projection.interval_end_time}`}
              </span>
            </Fact>
            <Fact term="Timestep">
              <span data-header-timestep={projection.timestep_minutes}>
                {`${projection.timestep_minutes} min, frozen for this run`}
              </span>
            </Fact>
            <Fact term="Simulated position">
              {`${projection.simulation_time}, offset ${projection.offset_minutes} min`}
            </Fact>
            <Fact term="Boundaries (port)">
              <span data-header-boundaries>
                {`${projection.boundaries_completed} of ${projection.boundaries_total} completed`}
              </span>
            </Fact>
            <Fact term="Seed">{String(projection.seed)}</Fact>
            <Fact term="Versions">
              {`kernel ${projection.kernel_version}; model ${projection.model_profile_id} v${projection.model_profile_version}; publication ${projection.publication_profile_id} v${projection.publication_profile_version}; numeric ${projection.numeric_policy} v${projection.numeric_policy_version}; execution contract v${projection.execution_contract_version}`}
            </Fact>
            <Fact term="Execution outcome">
              <span data-header-execution={projection.status}>
                {projection.status}
              </span>
              {projection.failure === null
                ? ""
                : `: ${projection.failure.kind} at ${projection.failure.subject}`}
            </Fact>
          </>
        )}
        <Fact term="Recorded history">
          {history === null ? (
            "being read"
          ) : recorded === null ? (
            <span data-header-history="UNREADABLE">
              the history could not be read
            </span>
          ) : (
            <span data-header-history={recorded.source}>
              {`${recorded.source}: ${recorded.boundaries_recorded} of ${recorded.boundaries_total} boundaries recorded`}
              {recorded.recorded_through_offset_minutes === null
                ? ""
                : ` through offset ${recorded.recorded_through_offset_minutes} min`}
              {/* T026: a family the run's mapping has no channel for (records
                  under a profile without one) is not applicable, not missing. */}
              {`; families recorded ${
                recorded.coverage.filter((c) => c.availability === "RECORDED")
                  .length
              } of ${
                recorded.coverage.filter((c) => c.availability !== "NOT_APPLICABLE")
                  .length
              }`}
              {recorded.coverage.some((c) => c.availability === "NOT_APPLICABLE")
                ? ` (${
                    recorded.coverage.filter((c) => c.availability === "NOT_APPLICABLE")
                      .length
                  } not applicable)`
                : ""}
              {recorded.source === "PERSISTED" && recorded.history_digest !== null
                ? `; verified artifact, history digest ${recorded.history_digest}`
                : recorded.source === "LIVE_SESSION"
                  ? "; read from the live session, so no persisted digest is claimed"
                  : "; not a verified durable record"}
            </span>
          )}
        </Fact>
        <Fact term="Stage">
          {stage === null ? (
            "being read"
          ) : stage.status !== "loaded" ? (
            <span data-header-stage="UNAVAILABLE">
              the stage could not be read
            </span>
          ) : (
            <span data-header-stage={stage.stage.status}>
              {`${stage.stage.status}; ${
                stage.stage.release_eligible
                  ? "release eligible"
                  : "not release eligible"
              }`}
            </span>
          )}
        </Fact>
      </FactList>
    </Panel>
  );
}
