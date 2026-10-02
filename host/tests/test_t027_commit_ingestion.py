"""T027 phase 1: Commit through normal ingestion, with the real kernel and gateway.

One degraded-evidence Kobo Draft (`kobo-mini-grid-degraded-evidence`, mini-grid
v3, publication profile 5) is executed once to the end and staged. Commit seals
the stage and releases it through `IngestionService.ingest`; everything after
that reads accepted evidence only.

Criteria: AC1, AC2, AC5, AC6, AC7, AC13, AC14, AC15, AC17, AC18, AC19. Proof rows:
stage without Commit, valid Commit, duplicate release after restart, delayed
publication, disable Lab, remove private artifacts and rebuild, change current
configuration, Commit with partial rejection then Open in AssetOps.
"""

from __future__ import annotations

import copy
import shutil
from dataclasses import replace
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

import pytest
from fastapi.testclient import TestClient

from assetops_backend.config import FeatureFlags
from assetops_backend.evidence.adapters.json_evidence_store import JsonEvidenceStore
from assetops_backend.main import create_app
from assetops_backend.runs.adapters.json_commit_store import JsonCommitStore
from assetops_contracts.committed_artifact import ingestion_batch, parse_artifact_text
from fixtures import FakeRuns, FakeSites
from kobo import KOBO_SITE_ID, kobo_draft, kobo_site
from lab_execution import HostLabExecution, YamlExecutionArtifacts
from source_stages import JsonSourceStages

DEGRADED = "kobo-mini-grid-degraded-evidence"
# The whole scenario (it refuses a shorter interval), including the 07:00
# state-of-charge publication held until 07:10 (T026).
WINDOW = dict(start_time="2026-09-22T03:00:00Z", end_time="2026-09-22T11:00:00Z")
RECEIVED = "2026-09-29T12:00:00Z"
ENABLED = FeatureFlags(simulator_lab_enabled=True)
DISABLED = FeatureFlags(simulator_lab_enabled=False)
EVIDENCE = f"/api/sites/{KOBO_SITE_ID}/evidence"
#: Receipt and audit times are explicitly nondeterministic (AC14).
AUDIT_TIMES = {"received_at", "started_at", "completed_at", "last_received_at", "registered_at"}


def without_audit_times(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: without_audit_times(v) for k, v in value.items() if k not in AUDIT_TIMES}
    if isinstance(value, list):
        return [without_audit_times(v) for v in value]
    return value


class Lab:
    """One executed Draft and the stores a composed application runs over."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.run = kobo_draft(
            DEGRADED,
            model_profile="mini-grid",
            model_profile_version=3,
            timestep_minutes=5,
            publication_profile_version=5,
            **WINDOW,
        )
        self.site = kobo_site()
        self.runs = FakeRuns()
        self.runs.create_run(self.run)
        execution = self.execution()
        execution.start(self.run)
        execution.run_to_end(self.run)

    def execution(self, root: Path | None = None) -> HostLabExecution:
        base = self.root if root is None else root
        return HostLabExecution(
            artifacts=YamlExecutionArtifacts(base / "executions"),
            stages=JsonSourceStages(base / "stages"),
        )

    def client(
        self,
        flags: FeatureFlags = ENABLED,
        *,
        root: Path | None = None,
        site=None,
    ) -> TestClient:
        base = self.root if root is None else root
        return TestClient(
            create_app(
                flags,
                site_repository=FakeSites((self.site if site is None else site,)),
                run_repository=self.runs,
                execution=self.execution() if flags.simulator_lab_enabled else None,
                evidence_store=JsonEvidenceStore(base / "evidence"),
                commit_store=JsonCommitStore(base / "commits"),
                clock=lambda: RECEIVED,
            )
        )

    @property
    def commit_path(self) -> str:
        return f"/api/simulator-lab/runs/{self.run.run_id}/commit"


@pytest.fixture(scope="module")
def committed(tmp_path_factory):
    lab = Lab(tmp_path_factory.mktemp("t027-commit"))
    client = lab.client()
    before = {
        "commit": client.get(lab.commit_path).json(),
        "records": client.get(f"{EVIDENCE}/records").json(),
        "stage": client.get(f"/api/simulator-lab/runs/{lab.run.run_id}/stage").json(),
    }
    response = client.post(lab.commit_path)
    assert response.status_code == 200, response.text
    return lab, before, response.json()


def test_stage_without_commit_changes_no_accepted_history(committed) -> None:
    _, before, _ = committed
    assert before["stage"]["stage"]["release_eligible"] is True
    assert before["commit"] == {"commit": "NOT_COMMITTED", "release": None, "open_in_assetops": None}
    assert before["records"]["total"] == 0


def test_commit_accepts_evidence_for_the_selected_site_window(committed) -> None:
    lab, _, body = committed
    commit, release = body["commit"], body["release"]
    assert commit["site_id"] == KOBO_SITE_ID
    assert release["batch_id"] == commit["artifact_id"]
    assert release["status"] == "COMPLETED"
    assert release["total"] == commit["envelope_count"] == release["processed"]
    assert release["accepted"] > 0
    assert release["accepted"] + release["rejected"] + release["duplicates"] + release[
        "conflicts"
    ] == release["total"]

    target = body["open_in_assetops"]
    assert target["site_id"] == KOBO_SITE_ID
    href = urlsplit(target["href"])
    assert href.path == f"/sites/{KOBO_SITE_ID}/evidence"
    query = {k: v[0] for k, v in parse_qs(href.query).items()}
    assert query == {
        "from": release["window_start"],
        "to": release["window_end"],
        "batch": commit["artifact_id"],
    }
    assert WINDOW["start_time"] <= release["window_start"] <= release["window_end"]

    client = lab.client()
    view = client.get(EVIDENCE, params={"from": query["from"], "to": query["to"]}).json()
    assert view["window"]["start"] == release["window_start"]
    assert sum(s["accepted_in_window"] for s in view["sources"]) == release["accepted"]
    assert client.get(f"{EVIDENCE}/records").json()["total"] == release["accepted"]


def test_delayed_publication_shows_three_distinct_timestamps(committed) -> None:
    lab, _, body = committed
    artifact = JsonCommitStore(lab.root / "commits").get(lab.run.run_id)
    assert artifact is not None and artifact.artifact_id == body["commit"]["artifact_id"]
    held = next(
        e
        for e in artifact.envelopes
        if (e.device_id, e.signal_id, e.source_time)
        == ("battery-pcs-controller", "state-of-charge", "2026-09-22T07:00:00Z")
    )
    record = lab.client().get(f"{EVIDENCE}/records/{held.message_id}").json()
    assert record["source_time"] == "2026-09-22T07:00:00Z"
    assert record["published_at"] == "2026-09-22T07:10:03Z"
    assert record["received_at"] == RECEIVED
    assert len({record["source_time"], record["published_at"], record["received_at"]}) == 3


def test_duplicate_release_after_restart_counts_nothing_twice(committed) -> None:
    lab, _, body = committed
    first = lab.client()
    evidence_before = first.get(EVIDENCE).json()
    records_before = first.get(f"{EVIDENCE}/records", params={"limit": 1000}).json()

    restarted = lab.client()  # new application, new port, same stores
    again = restarted.post(lab.commit_path).json()
    assert again["commit"] == body["commit"]
    assert again["release"]["accepted"] == body["release"]["accepted"]
    assert restarted.get(EVIDENCE).json() == evidence_before
    assert restarted.get(f"{EVIDENCE}/records", params={"limit": 1000}).json() == records_before
    assert [p.name for p in (lab.root / "commits").glob("*.json")] == [
        f"{lab.run.run_id}.json"
    ]


def test_rebuild_from_committed_artifact_text_alone_matches(committed, tmp_path) -> None:
    """AC14/AC15: only the artifact text, an empty store, no execution port."""
    lab, _, _ = committed
    fresh = tmp_path / "rebuild"
    (fresh / "commits").mkdir(parents=True)
    shutil.copy2(lab.root / "commits" / f"{lab.run.run_id}.json", fresh / "commits")
    assert not (fresh / "executions").exists() and not (fresh / "stages").exists()

    app = create_app(
        DISABLED,
        site_repository=FakeSites((lab.site,)),
        evidence_store=JsonEvidenceStore(fresh / "evidence"),
        clock=lambda: "2030-01-01T00:00:00Z",
    )
    for path in sorted((fresh / "commits").glob("*.json")):
        app.state.ingestion.ingest(
            ingestion_batch(parse_artifact_text(path.read_text(encoding="utf-8")))
        )
    rebuilt, original = TestClient(app), lab.client(DISABLED)

    assert without_audit_times(rebuilt.get(EVIDENCE).json()) == without_audit_times(
        original.get(EVIDENCE).json()
    )
    params = {"limit": 1000}
    rebuilt_records = rebuilt.get(f"{EVIDENCE}/records", params=params).json()
    assert without_audit_times(rebuilt_records) == without_audit_times(
        original.get(f"{EVIDENCE}/records", params=params).json()
    )
    sample = rebuilt_records["records"][0]["message_id"]
    assert without_audit_times(
        rebuilt.get(f"{EVIDENCE}/records/{sample}").json()
    ) == without_audit_times(original.get(f"{EVIDENCE}/records/{sample}").json())


def test_gate_closed_serves_the_same_accepted_evidence_and_no_lab(committed) -> None:
    lab, _, body = committed
    open_gate, closed = lab.client(), lab.client(DISABLED)
    run = lab.run.run_id
    for path in (
        lab.commit_path,
        f"/api/simulator-lab/runs/{run}/stage",
        f"/api/simulator-lab/runs/{run}/execution",
        f"/api/simulator-lab/runs/{run}/execution/history",
    ):
        assert closed.get(path).status_code == 404, path
    assert closed.post(lab.commit_path).status_code == 404
    assert closed.get(EVIDENCE).json() == open_gate.get(EVIDENCE).json()
    batch = closed.get(f"/api/ingestion/batches/{body['commit']['artifact_id']}")
    assert batch.status_code == 200 and batch.json()["status"] == "COMPLETED"


def test_changing_the_current_foundation_leaves_the_accepted_basis(committed) -> None:
    lab, _, _ = committed
    original = lab.site.foundation
    edited = replace(
        lab.site,
        foundation=replace(
            original, version=original.version + 1, valid_from="2026-10-01T00:00:00Z"
        ),
    )
    client = lab.client(DISABLED, site=edited)
    view = client.get(EVIDENCE).json()
    assert view["basis"]["current_foundation"]["foundation_version"] == original.version + 1
    assert [c["foundation_version"] for c in view["basis"]["configurations"]] == [
        original.version
    ]
    sample = client.get(f"{EVIDENCE}/records").json()["records"][0]["message_id"]
    record = client.get(f"{EVIDENCE}/records/{sample}").json()
    assert record["configuration"]["foundation_version"] == original.version
    assert record["configuration"]["foundation_valid_from"] == original.valid_from


def residential_meter_in_kwh(document: dict[str, Any]) -> None:
    for device in document["foundation"]["devices"]:
        for signal in device.get("signals", []):
            if (device["device_id"], signal["signal_id"]) == ("residential-meter", "active-power"):
                signal["unit"] = "kWh"


def test_partial_rejection_then_open_in_assetops_shows_actual_coverage(
    committed, tmp_path
) -> None:
    """Built at the ingestion layer: the stage cannot be tampered, so the Site's
    Foundation (same version) declares another unit for one signal and ingestion
    rejects exactly that signal's envelopes."""
    lab, _, body = committed
    for name in ("executions", "stages", "commits"):
        shutil.copytree(lab.root / name, tmp_path / name)
    site = kobo_site(residential_meter_in_kwh)
    assert site.foundation.version == lab.site.foundation.version
    client = lab.client(root=tmp_path, site=site)

    partial = client.post(lab.commit_path).json()
    release = partial["release"]
    assert partial["commit"] == body["commit"]
    assert release["status"] == "COMPLETED"
    assert 0 < release["rejected"] < release["total"]
    assert release["accepted"] == body["release"]["accepted"] - release["rejected"]

    target = partial["open_in_assetops"]
    assert target["site_id"] == KOBO_SITE_ID
    view = client.get(
        EVIDENCE, params={"from": target["window_start"], "to": target["window_end"]}
    ).json()
    assert sum(s["accepted_in_window"] for s in view["sources"]) == release["accepted"]
    meter = [
        c for c in view["coverage"] if (c["device_id"], c["signal_id"]) == ("residential-meter", "active-power")
    ]
    assert meter and all(c["records"] == 0 for c in meter)
    rejections = client.get(
        f"{EVIDENCE}/rejections", params={"batch": release["batch_id"]}
    ).json()
    assert rejections["total"] == release["rejected"]
    assert {r["kind"] for r in rejections["rejections"]} == {"UNIT_INCOMPATIBLE"}
