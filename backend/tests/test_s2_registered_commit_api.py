"""S2-02 phase 2: Lab Commit of a registered run is a local gateway release.

The port is a fake: these tests pin the route's behaviour (it asks the port's
`release_registered`, never seals a file Stage, writes no Evidence and holds no
network secret) and how it reports pending, partial and terminal release.
"""

from __future__ import annotations

from test_s1_cutover import ON, StagedExecution, app_for, legacy_root  # noqa: F401
from run_fixtures import FakeScenarios
from test_s2_registered_basis import SCENARIO, converted, request

from assetops_backend.runs.adapters.yaml_run_store import YamlRunStore
from assetops_contracts.lab_projection import LabControlRefused


def delivery(**overrides) -> dict:
    base = {
        "lab_run_ref": "r",
        "stage_status": "STAGED",
        "envelope_count": 4,
        "unbatched_envelope_count": 0,
        "held_report_count": 1,
        "batch_count": 2,
        "released_batch_count": 2,
        "batches_by_state": {"STAGED": 0, "READY": 2, "IN_FLIGHT": 0, "ACKED": 0, "REFUSED": 0},
        "shared_batch_ids": [],
        "decisions": {"ACCEPTED": 0, "DUPLICATE": 0, "REJECTED": 0, "CONFLICT": 0},
        "refusals": [],
        "last_upload_error": None,
        "release_state": "PENDING",
        "publication_gap": "UNKNOWN_TO_GATEWAY",
        "gateway_complete": False,
    }
    return {**base, **overrides}


def view(fully: bool, blockers: list[str], **delivery_overrides) -> dict:
    return {
        "status": "AVAILABLE",
        "detail": None,
        "execution_status": "COMPLETED",
        "delivery": delivery(**delivery_overrides),
        "released_now": 2,
        "publication_gap": "NONE",
        "publication_gap_detail": None,
        "fully_released": fully,
        "release_blockers": blockers,
    }


class ReleasingExecution(StagedExecution):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.release_answer: object = None
        self.delivery_answer: object = None

    def release_registered(self, run):
        self.calls.append(("release_registered", run.run_id))
        if isinstance(self.release_answer, Exception):
            raise self.release_answer
        return self.release_answer

    def registered_delivery(self, run):
        self.calls.append(("registered_delivery", run.run_id))
        return self.delivery_answer


def client_with_draft(tmp_path, legacy_root):
    store, _, _ = converted()
    execution = ReleasingExecution()
    client = app_for(
        store, legacy_root, flags=ON, run_repository=YamlRunStore(tmp_path / "runs"), execution=execution,
        scenario_repository=FakeScenarios((SCENARIO,)),
    )
    created = client.post("/api/simulator-lab/runs", json=request())
    assert created.status_code == 201, created.text
    return client, execution, created.json()["run"]["run_id"]


def test_commit_releases_through_the_port_and_reports_pending(tmp_path, legacy_root) -> None:
    client, execution, run_id = client_with_draft(tmp_path, legacy_root)
    execution.release_answer = view(False, ["RECEIPTS_PENDING"])
    response = client.post(f"/api/simulator-lab/runs/{run_id}/commit")
    assert response.status_code == 200, response.text
    body = response.json()
    assert execution.calls == [("release_registered", run_id)], "Commit touched the file Stage"
    assert body["commit"] == "RELEASED_TO_GATEWAY" and body["fully_released"] is False
    assert body["registered_release"]["release_blockers"] == ["RECEIPTS_PENDING"]
    assert body["release"] is None  # no in-process ingestion batch
    assert "aog1." not in response.text and "Bearer" not in response.text


def test_a_partial_or_gapped_run_is_never_claimed_fully_released(tmp_path, legacy_root) -> None:
    client, execution, run_id = client_with_draft(tmp_path, legacy_root)
    execution.release_answer = view(
        False, ["PUBLICATION_GAP", "STAGE_SEALING_REFUSED"], stage_status="SEALING_REFUSED",
        release_state="PARTIAL",
    )
    body = client.post(f"/api/simulator-lab/runs/{run_id}/commit").json()
    assert body["fully_released"] is False and "not fully released" in body["statement"]


def test_a_terminal_fully_released_run_says_so(tmp_path, legacy_root) -> None:
    client, execution, run_id = client_with_draft(tmp_path, legacy_root)
    execution.release_answer = view(True, [], release_state="TERMINAL", gateway_complete=True)
    body = client.post(f"/api/simulator-lab/runs/{run_id}/commit").json()
    assert body["fully_released"] is True and "durable central receipt" in body["statement"]


def test_a_refused_release_is_a_typed_409_with_nothing_released(tmp_path, legacy_root) -> None:
    client, execution, run_id = client_with_draft(tmp_path, legacy_root)
    for kind in ("COMMIT_NOT_READY", "GATEWAY_RELEASE_UNAVAILABLE"):
        execution.release_answer = LabControlRefused(kind, run_id, "detail")
        response = client.post(f"/api/simulator-lab/runs/{run_id}/commit")
        assert response.status_code == 409, response.text
        detail = response.json()["detail"]
        assert detail["refusal_kind"] == kind and detail["advanced"] is False


def test_the_commit_read_shows_the_delivery_state(tmp_path, legacy_root) -> None:
    client, execution, run_id = client_with_draft(tmp_path, legacy_root)
    execution.delivery_answer = view(False, ["NOT_ALL_BATCHES_RELEASED"], released_batch_count=0,
                                     release_state="NOT_RELEASED")
    response = client.get(f"/api/simulator-lab/runs/{run_id}/commit")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["commit"] == "NOT_COMMITTED" and body["fully_released"] is False
    assert execution.calls == [("registered_delivery", run_id)]
