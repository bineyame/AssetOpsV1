"""The gated Commit routes (T027, D4), against a stage port that answers what it is told.

The composing proof - a real kernel, gateway and stage behind these routes - is
`host/tests/test_t027_commit_ingestion.py`. This is the product half: Commit
seals only an eligible stage, files the artifact once and never rewrites it,
releases through `IngestionService.ingest`, reports commit and release
separately, and is absent with the gate closed while accepted evidence stays.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from fastapi.testclient import TestClient
from run_fixtures import FakeRuns, FakeScenarios, FakeSites, scenario, setup_request, site
from test_t027_ingestion import GATEWAY, SITE_ID, SOURCE, a_site, envelope, mapping

import run_fixtures as profiles
from assetops_backend.config import FeatureFlags
from assetops_backend.evidence.adapters.json_evidence_store import JsonEvidenceStore
from assetops_backend.evidence.service import IngestionService
from assetops_backend.main import create_app
from assetops_backend.runs.adapters.json_commit_store import JsonCommitStore
from assetops_backend.runs.models import SimulationRun
from assetops_backend.runs.service import RunSetupService
from assetops_contracts.source_stage import (
    SOURCE_STAGE_STATUS_STATEMENTS,
    SourceStage,
    SourceStageView,
    release_blockers,
)

ENABLED = FeatureFlags(simulator_lab_enabled=True)
DISABLED = FeatureFlags(simulator_lab_enabled=False)
RUNS = "/api/simulator-lab/runs"
ENVELOPES = 5


class FakeStagePort:
    """Answers a stage view built from `execution_status` and `digest`."""

    def __init__(self) -> None:
        self.execution_status = "COMPLETED"
        self.digest = "c" * 64

    def staged_envelopes(self, run: SimulationRun) -> SourceStageView:
        stage = SourceStage(
            run_id=run.run_id,
            site_id=SITE_ID,
            source_id=SOURCE,
            gateway_id=GATEWAY,
            mapping=mapping(),
            envelopes=tuple(envelope(minute + 1) for minute in range(ENVELOPES)),
            boundaries_total=ENVELOPES,
            published_through=ENVELOPES,
        )
        return SourceStageView(
            run_id=run.run_id,
            status="STAGED",
            statement=SOURCE_STAGE_STATUS_STATEMENTS["STAGED"],
            execution_status=self.execution_status,
            release_blockers=release_blockers("STAGED", self.execution_status, stage),
            stage=stage,
            integrity_digest=self.digest,
        )


class World:
    def __init__(self, tmp_path: Path) -> None:
        self.runs = FakeRuns()
        self.record = RunSetupService(
            self.runs,
            FakeSites((site(),)),
            FakeScenarios((scenario(),)),
            model_profiles=(profiles.model_profile(),),
            publication_profiles=(profiles.publication_profile(),),
            now=lambda: "2026-09-21T09:00:00Z",
        ).create_draft_run(setup_request())
        self.sites = FakeSites((a_site(),))
        self.evidence_root = tmp_path / "evidence"
        self.commit_root = tmp_path / "commits"
        self.port = FakeStagePort()

    def app(self, flags: FeatureFlags = ENABLED):
        return create_app(
            flags,
            site_repository=self.sites,
            run_repository=self.runs,
            execution=self.port,
            evidence_store=JsonEvidenceStore(self.evidence_root),
            commit_store=JsonCommitStore(self.commit_root),
        )

    def client(self, flags: FeatureFlags = ENABLED) -> TestClient:
        return TestClient(self.app(flags))

    @property
    def path(self) -> str:
        return f"{RUNS}/{self.record.run_id}/commit"

    def artifact_files(self) -> list[Path]:
        return sorted(self.commit_root.glob("*.json")) if self.commit_root.exists() else []


def test_commit_seals_once_releases_and_reports_commit_and_release_separately(tmp_path):
    world = World(tmp_path)
    client = world.client()

    before = client.get(world.path)
    assert before.status_code == 200
    assert before.json() == {
        "commit": "NOT_COMMITTED",
        "release": None,
        "open_in_assetops": None,
    }

    first = client.post(world.path)
    assert first.status_code == 200, first.text
    body = first.json()
    commit = body["commit"]
    assert commit["run_id"] == world.record.run_id
    assert commit["site_id"] == SITE_ID
    assert commit["envelope_count"] == ENVELOPES
    assert set(commit) == {
        "artifact_id", "integrity_digest", "envelope_count", "sealed_at", "run_id", "site_id",
    }
    release = body["release"]
    assert release["batch_id"] == commit["artifact_id"]
    assert release["status"] == "COMPLETED"
    assert (release["total"], release["processed"], release["accepted"]) == (5, 5, 5)
    assert body["release_error"] is None
    target = body["open_in_assetops"]
    assert target == {
        "site_id": SITE_ID,
        "window_start": release["window_start"],
        "window_end": release["window_end"],
        "batch_id": commit["artifact_id"],
        "href": (
            f"/sites/{SITE_ID}/evidence?from={release['window_start']}"
            f"&to={release['window_end']}&batch={commit['artifact_id']}"
        ),
    }
    assert release["window_start"] == "2026-09-22T00:01:00Z"
    assert release["window_end"] == "2026-09-22T00:05:00Z"

    [filed] = world.artifact_files()
    filed_bytes = filed.read_bytes()

    # A second Commit reuses the artifact (same id, same sealed_at, same bytes)
    # and the release is idempotent: nothing is counted twice.
    second = client.post(world.path).json()
    assert second["commit"] == commit
    assert second["release"]["accepted"] == 5
    assert filed.read_bytes() == filed_bytes
    assert world.artifact_files() == [filed]

    read = client.get(world.path).json()
    assert read["commit"] == commit
    assert read["release"]["status"] == "COMPLETED"
    assert read["open_in_assetops"] == target

    records = client.get(f"/api/sites/{SITE_ID}/evidence/records?limit=100").json()
    assert records["total"] == 5


def test_an_ineligible_stage_is_refused_with_its_blockers_and_nothing_is_written(tmp_path):
    world = World(tmp_path)
    world.port.execution_status = "RUNNING"
    client = world.client()

    refused = client.post(world.path)
    assert refused.status_code == 409
    detail = refused.json()["detail"]
    assert detail["code"] == "COMMIT_REFUSED"
    assert [b["kind"] for b in detail["release_blockers"]] == ["EXECUTION_NOT_COMPLETED"]
    assert all(b["statement"] for b in detail["release_blockers"])

    assert world.artifact_files() == []
    assert client.get(world.path).json()["commit"] == "NOT_COMMITTED"
    assert client.get(f"/api/sites/{SITE_ID}/evidence/records").json()["total"] == 0


def test_a_filed_artifact_is_never_rewritten_and_a_changed_stage_is_refused(tmp_path):
    world = World(tmp_path)
    client = world.client()
    commit = client.post(world.path).json()["commit"]
    [filed] = world.artifact_files()
    filed_bytes = filed.read_bytes()

    world.port.digest = "d" * 64
    changed = client.post(world.path)
    assert changed.status_code == 409
    assert changed.json()["detail"]["code"] == "COMMIT_STAGE_CHANGED"
    assert changed.json()["detail"]["commit"] == commit
    assert filed.read_bytes() == filed_bytes

    # A restarted app over the same stores reads the same artifact back.
    restarted = world.client()
    assert restarted.get(world.path).json()["commit"] == commit


def test_a_tampered_artifact_is_answered_as_unreadable(tmp_path):
    world = World(tmp_path)
    client = world.client()
    client.post(world.path)
    [filed] = world.artifact_files()
    document = json.loads(filed.read_text(encoding="utf-8"))
    document["sealed_at"] = "2030-01-01T00:00:00Z"
    filed.write_text(json.dumps(document), encoding="utf-8")

    read = client.get(world.path)
    assert read.status_code == 409
    assert read.json()["detail"]["code"] == "COMMIT_ARTIFACT_UNREADABLE"


def test_an_interrupted_release_reports_progress_and_a_retry_resumes(tmp_path):
    world = World(tmp_path)
    app = world.app()
    store = app.state.ingestion.store
    app.state.ingestion = IngestionService(store, world.sites, chunk_size=1, fail_after=2)
    client = TestClient(app)

    interrupted = client.post(world.path)
    assert interrupted.status_code == 200, interrupted.text
    body = interrupted.json()
    assert body["release"]["status"] == "IN_PROGRESS"
    assert (body["release"]["processed"], body["release"]["total"]) == (2, 5)
    assert body["release"]["accepted"] == 2
    assert body["release_error"].startswith("IngestionInterrupted")
    assert client.get(world.path).json()["release"]["status"] == "IN_PROGRESS"

    app.state.ingestion = IngestionService(store, world.sites, chunk_size=1)
    resumed = client.post(world.path).json()
    assert resumed["commit"] == body["commit"]
    assert resumed["release"]["status"] == "COMPLETED"
    assert (resumed["release"]["processed"], resumed["release"]["accepted"]) == (5, 5)
    assert resumed["release"]["duplicates"] == 0
    assert client.get(f"/api/sites/{SITE_ID}/evidence/records?limit=100").json()["total"] == 5


def test_gate_closed_has_no_commit_routes_and_still_serves_accepted_evidence(tmp_path):
    world = World(tmp_path)
    world.client().post(world.path)

    closed = world.client(DISABLED)
    assert closed.get(world.path).status_code == 404
    assert closed.post(world.path).status_code == 404
    evidence = closed.get(f"/api/sites/{SITE_ID}/evidence")
    assert evidence.status_code == 200
    assert closed.get(f"/api/sites/{SITE_ID}/evidence/records").json()["total"] == 5


def test_a_closed_build_never_builds_the_commit_store(tmp_path, monkeypatch):
    import assetops_backend.main as main

    def refuse() -> None:
        raise AssertionError("the commit store was built with the gate closed")

    monkeypatch.setattr(main, "build_commit_store", refuse)
    world = World(tmp_path)
    create_app(
        DISABLED,
        site_repository=world.sites,
        evidence_store=JsonEvidenceStore(world.evidence_root),
    )


class PartlyBadStagePort(FakeStagePort):
    """The eligible stage plus one envelope the Site's Foundation does not declare."""

    def staged_envelopes(self, run: SimulationRun) -> SourceStageView:
        view = super().staged_envelopes(run)
        assert view.stage is not None
        stray = envelope(30, device="mystery-device", signal="mystery", unit="kW")
        stage = replace(view.stage, envelopes=view.stage.envelopes + (stray,))
        return replace(view, stage=stage)


def test_partial_rejection_is_reported_and_open_in_assetops_uses_the_accepted_window(tmp_path):
    world = World(tmp_path)
    world.port = PartlyBadStagePort()
    body = world.client().post(world.path).json()
    release = body["release"]
    assert body["commit"]["envelope_count"] == 6
    assert release["status"] == "COMPLETED"
    assert (release["total"], release["accepted"], release["rejected"]) == (6, 5, 1)
    # The rejected envelope (00:30) does not widen the accepted window.
    assert body["open_in_assetops"]["window_end"] == "2026-09-22T00:05:00Z"
