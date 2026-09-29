"""One frozen Draft, executed the way the product executes it, reduced to what
the contract-9 merge gate compares. Shared by `capture.py` (pre-change) and
`test_contract9_gate.py` (post-change) so both sides measure the same thing."""

from __future__ import annotations

from pathlib import Path

from assetops_contracts.observation import observation_series_digest
from assetops_simulator.observation.transform import generate_observations

from execution_adapter import model_for, reporting_inputs, run_to_end
from lab_execution import HostLabExecution, YamlExecutionArtifacts
from source_stages import JsonSourceStages


def execute_through_the_lab(run, scratch: Path) -> dict:
    """Headless trajectory plus the Lab's own start/run-to-end/persist path.

    A BLOCKED Draft is reduced to its refusal, which must stay the same too."""
    if run.execution_status != "READY":
        return {
            "status": run.execution_status,
            "blocking": sorted(
                f"{reason.kind} {reason.subject}" for reason in run.blocking_reasons
            ),
            "artifact_text": "",
        }
    model = model_for(run)
    headless = run_to_end(run, model)
    trajectory = headless.trajectory
    observations = generate_observations(
        trajectory.boundaries, reporting_inputs(run, model=model)
    )

    lab = HostLabExecution(
        artifacts=YamlExecutionArtifacts(scratch / "executions"),
        stages=JsonSourceStages(scratch / "stages"),
    )
    projection = lab.start(run)
    if not projection.is_terminal:
        projection = lab.run_to_end(run)
    artifact = (scratch / "executions" / f"{run.run_id}.yaml").read_text(
        encoding="utf-8"
    )
    return {
        "model_profile": f"{trajectory.model_profile_id} v{trajectory.model_profile_version}",
        "execution_contract_version": run.deterministic_identity.profiles.execution_contract_version,
        "outcome": trajectory.outcome,
        "failure": None if trajectory.failure is None else f"{trajectory.failure.kind} {trajectory.failure.subject}",
        "boundaries": len(trajectory.boundaries),
        "inputs_identity": trajectory.inputs_identity,
        "content_digest": trajectory.content_digest,
        "observation_count": len(observations),
        "observation_series_digest": observation_series_digest(observations),
        "lab_content_digest": projection.content_digest,
        "lab_observation_series_digest": projection.observation_series_digest,
        "artifact_text": artifact,
    }
