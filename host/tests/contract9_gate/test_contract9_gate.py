"""T025a criterion 10: the contract-9 merge gate.

The fixtures are GENERATED stand-ins, not copies of the owner's data (owner
decision 2026-09-29). `capture.py` built them on the code before any T025a
change (96618d9) from the shipped templates and scenarios, through the
product's own setup and Lab execution: fuel and daytime Drafts that are READY,
BLOCKED, and (daytime) FAILED, and daytime Drafts with a reserve window whose
boundaries fall inside a step. Each must still parse, execute under its
frozen profile, keep its deterministic identity and reproduce its trajectory
digest, observation series digest and rendered execution artifact byte for
byte. `expected.json` and `pre-change-artifacts/` are that baseline.

Stored artifacts (`stored-executions/`, written by the pre-change Lab, schema
3 - the only layout that code wrote) must read back and render to the same
document, and a COMPLETED or FAILED one is byte-equal to the re-execution of
its Draft. A RUNNING one is a mid-run record and is held to its own status.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from assetops_backend.runs.adapters.yaml_run_documents import read_run_record

from gate import execute_through_the_lab
from lab_execution import YamlExecutionArtifacts, render_projection

HERE = Path(__file__).resolve().parent
EXPECTED = json.loads((HERE / "expected.json").read_text(encoding="utf-8"))
RUNS = sorted((HERE / "runs").glob("*.yaml"))
STORED = sorted((HERE / "stored-executions").glob("*.yaml"))

STORED_EXPECTED = json.loads(
    (HERE / "stored_expected.json").read_text(encoding="utf-8")
)
WITHIN_STEP = ("run-c9000000000000000000000000000206", "run-c9000000000000000000000000000207")


def test_the_gate_covers_fuel_daytime_blocked_and_within_step_cases() -> None:
    profiles = {entry.get("model_profile") for entry in EXPECTED.values()}
    assert {"minimal-fuel-tank v1", "daytime-mini-grid v1"} <= profiles
    assert any(entry.get("status") == "BLOCKED" for entry in EXPECTED.values())
    assert any(entry.get("outcome") == "FAILED" for entry in EXPECTED.values())
    assert set(WITHIN_STEP) <= set(EXPECTED)
    assert len(RUNS) == len(EXPECTED) == 15
    assert len(STORED) == len(STORED_EXPECTED) == 7
    assert {v["status"] for v in STORED_EXPECTED.values()} == {
        "COMPLETED",
        "FAILED",
        "RUNNING",
    }


@pytest.mark.parametrize("path", RUNS, ids=lambda path: path.stem)
def test_a_pre_change_draft_reproduces_exactly(path: Path, tmp_path: Path) -> None:
    run = read_run_record(path)
    result = execute_through_the_lab(run, tmp_path)
    artifact = result.pop("artifact_text")
    assert result == EXPECTED[run.run_id]
    assert artifact == (HERE / "pre-change-artifacts" / path.name).read_text(
        encoding="utf-8"
    )


@pytest.mark.parametrize("path", STORED, ids=lambda path: path.stem)
def test_a_stored_artifact_reads_back_and_renders_the_same(path: Path) -> None:
    projection = YamlExecutionArtifacts(path.parent).read(path.stem)
    assert projection is not None
    assert render_projection(projection) == yaml.safe_load(
        path.read_text(encoding="utf-8")
    )
    assert projection.status == STORED_EXPECTED[path.stem]["status"]
    if projection.status != "RUNNING":
        assert path.read_text(encoding="utf-8") == (
            HERE / "pre-change-artifacts" / path.name
        ).read_text(encoding="utf-8")
        assert projection.content_digest == EXPECTED[path.stem]["lab_content_digest"]
