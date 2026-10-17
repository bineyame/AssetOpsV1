"""W2-02 commit (3): a cold run through the Host Lab - frozen re-read, one-shot window, Stage, late release.

`D-2026-10-17-w2-02-buildspec` "Cold Lab execution and frozen re-read". A real S2 registered Draft is given the
cold pair, scenario and frozen Foundation identity; the gateway is a recording fake of
`RegisteredGatewayPublisher.publish_in_boundary_order` so the test sees exactly which v2 texts reach it, at
which instant, and that a refusal reaches it with nothing.
"""

from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path
from uuid import UUID

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend" / "tests"))

import test_s2_registered_basis as registered  # noqa: E402
from assetops_backend.scenarios.cold_parsing import observation_sha256, parse_cold_scenario_document  # noqa: E402
from assetops_backend.sites.foundation_content import content_digest  # noqa: E402
from assetops_contracts.gateway_report import parse_device_report_v2_text  # noqa: E402
from assetops_contracts.failures import HOST_STAGING_FAILURE_KINDS, OBSERVED_KINDS  # noqa: E402
from assetops_contracts.lab_projection import LabControlRefused  # noqa: E402
from cold_lab import EMPTY_COLD_SERIES_DIGEST  # noqa: E402
from lab_execution import HostLabExecution, YamlExecutionArtifacts  # noqa: E402
from publication_schedule import JsonPublicationSchedules  # noqa: E402
from source_stages import JsonSourceStages  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
REVISION_ID = "5f0c0d6e-0000-4000-8000-000000000001"
RELEASE = "2026-10-06T20:10:00Z"


def _definition(case: str):
    path = ROOT / "config" / "scenarios" / f"cold-{case}.yaml"
    return parse_cold_scenario_document(yaml.safe_load(path.read_text(encoding="utf-8")), source=str(path))


def _revision(content=None):
    if content is None:
        site = yaml.safe_load((ROOT / "backend/tests/fixtures/w2/cold-lab-001.yaml").read_text(encoding="utf-8"))
        content = site["foundation"]
    return _Row(UUID(REVISION_ID), content, content_digest(content))


class _Row:
    def __init__(self, id, content, content_sha256):
        self.id, self.content, self.content_sha256 = id, content, content_sha256


@pytest.fixture(scope="module")
def kobo_draft():
    store, _, _ = registered.converted()
    return registered.setup_service(store).create_draft_run(registered.request())


def _cold_run(kobo_draft, case: str, revision):
    definition = _definition(case)
    identity = kobo_draft.deterministic_identity
    profiles = replace(identity.profiles, model_profile_id="cold-thermal", model_profile_version=1,
                       publication_profile_id="cold-publication", publication_profile_version=1,
                       observation_profile_id="cold-observation", observation_profile_version=1,
                       observation_sha256=observation_sha256(definition))
    scenario = replace(identity.scenario, scenario_id=definition.scenario_id, scenario_version=definition.version,
                       scenario_sha256=definition.scenario_sha256)
    interval = replace(identity.interval, start_time=definition.start, end_time=definition.end, timestep_minutes=1)
    basis = replace(kobo_draft.registered_basis, foundation_revision_id=REVISION_ID,
                    foundation_content_sha256=revision.content_sha256)
    return replace(kobo_draft, run_id=f"run-cold-{case}",
                   deterministic_identity=replace(identity, profiles=profiles, scenario=scenario, interval=interval),
                   registered_basis=basis), definition


class _Inputs:
    def __init__(self, revision, definition):
        self.revision, self.definition, self.calls = revision, definition, []

    def foundation_revision(self, tenant_id, site_record_id, revision_id):
        self.calls.append(("foundation", tenant_id, site_record_id, revision_id))
        return self.revision if self.revision is not None and self.revision.id == revision_id else None

    def cold_scenario(self, scenario_id, version):
        self.calls.append(("scenario", scenario_id, version))
        d = self.definition
        return d if d is not None and (d.scenario_id, d.version) == (scenario_id, version) else None


class _Gateway:
    """Records each boundary group; admits every text."""

    def __init__(self):
        self.groups: list[tuple[str, list[str]]] = []
        self.finals: list[str] = []

    def publish_in_boundary_order(self, run_id, basis, groups, final_instant):
        done = []
        for instant, texts in groups:
            self.groups.append((instant, list(texts)))
            done.append([{"outcome": "ADMITTED", "message_id": f"m{len(self.groups)}-{i}", "sequence": i}
                         for i, _ in enumerate(texts)])
        self.finals.append(final_instant)
        return done, None

    def texts(self) -> list[str]:
        return [t for _, texts in self.groups for t in texts]


def _host(tmp_path, inputs, gateway):
    return HostLabExecution(
        artifacts=YamlExecutionArtifacts(tmp_path / "executions"), stages=JsonSourceStages(tmp_path / "stages"),
        gateway=gateway, schedules=JsonPublicationSchedules(tmp_path / "schedules"), cold_inputs=inputs,
    )


def _chamber_points(texts) -> list:
    parsed = [parse_device_report_v2_text(t) for t in texts]
    return [p for p in parsed if (p.device_id, p.signal_id) == ("chamber-probe", "temperature")]


def test_late_reading_stages_twelve_then_releases_the_thirteenth(tmp_path, kobo_draft) -> None:
    revision = _revision()
    run, definition = _cold_run(kobo_draft, "late-reading", revision)
    gateway = _Gateway()
    host = _host(tmp_path, _Inputs(revision, definition), gateway)

    draft = host.projection(run)
    assert (draft.status, draft.boundaries_completed, draft.content_digest) == ("NOT_STARTED", 0, None)
    assert draft.observation_series_digest == EMPTY_COLD_SERIES_DIGEST
    with pytest.raises(LabControlRefused) as before:
        host.step(run, boundaries=1, from_boundary=0)
    assert before.value.kind == "NOT_STARTED"

    projection = host.start(run)
    assert projection.status == "COMPLETED"
    assert (projection.boundaries_completed, projection.boundaries_total, projection.offset_minutes) == (61, 61, 60)
    assert (projection.interval_start_time, projection.simulation_time) == (definition.start, definition.end)
    assert projection.private_state == projection.observations == projection.signals == ()
    assert projection.content_digest and projection.observation_series_digest != EMPTY_COLD_SERIES_DIGEST
    # The world executed once and ordinary admission stopped at the last ordinary instant.
    assert gateway.groups[-1][0] == "2026-10-06T20:00:03Z"
    assert [g[0] for g in gateway.groups] == sorted(g[0] for g in gateway.groups)
    assert len(_chamber_points(gateway.texts())) == 12
    assert projection.reported_count == len(gateway.texts()) + 1  # the held report is counted

    # Persisted: a fresh host reads COMPLETED from the schema-6 artifact, not from a live handle.
    restarted = _host(tmp_path, None, gateway)
    assert restarted.projection(run) == projection
    assert restarted._execution_status(run) == "COMPLETED"
    assert restarted.history(run).source == "HISTORY_UNAVAILABLE"
    head = (tmp_path / "executions" / f"{run.run_id}.yaml").read_text(encoding="utf-8")
    document = next(yaml.safe_load_all(head))
    assert document["artifact_schema_version"] == 6 and document["execution_kind"] == "COLD"
    for refused in (lambda: restarted.step(run, boundaries=1, from_boundary=61),
                    lambda: restarted.run_to_end(run), lambda: restarted.start(run)):
        with pytest.raises(LabControlRefused) as terminal:
            refused()
        assert terminal.value.kind == "ALREADY_TERMINAL"

    # The held 19:20 reading waits for the publication clock, keeps its source time, and is released once.
    answer = restarted.advance_publication(run, RELEASE)
    assert answer["publication_refused"] is None
    instant, texts = gateway.groups[-1]
    assert instant == RELEASE and len(texts) == 1
    late = parse_device_report_v2_text(texts[0])
    assert late.source_time == "2026-10-06T19:20:00Z"
    assert len(_chamber_points(gateway.texts())) == 13
    again = restarted.advance_publication(run, RELEASE)
    assert again["publication_refused"] is None
    assert len(_chamber_points(gateway.texts())) == 13


@pytest.mark.parametrize("damage", ["no_port", "revision_missing", "revision_changed", "scenario_missing",
                                    "scenario_changed"])
def test_unreconstructible_inputs_refuse_before_any_stage(tmp_path, kobo_draft, damage) -> None:
    revision = _revision()
    run, definition = _cold_run(kobo_draft, "normal", revision)
    inputs = _Inputs(revision, definition)
    if damage == "no_port":
        inputs = None
    elif damage == "revision_missing":
        inputs.revision = None
    elif damage == "revision_changed":
        content = json.loads(json.dumps(revision.content))
        content["changed_by_test"] = True
        inputs.revision = _Row(revision.id, content, content_digest(content))
    elif damage == "scenario_missing":
        inputs.definition = None
    else:
        inputs.definition = _definition("excursion")
        inputs.definition = replace(inputs.definition, scenario_id=definition.scenario_id)
    gateway = _Gateway()
    host = _host(tmp_path, inputs, gateway)
    with pytest.raises(LabControlRefused) as refused:
        host.start(run)
    assert refused.value.kind == "FROZEN_RUN_NOT_RECONSTRUCTIBLE"
    assert gateway.groups == []
    assert not (tmp_path / "schedules").exists() or not any((tmp_path / "schedules").iterdir())
    assert host.projection(run).status == "NOT_STARTED"


def test_publication_refusal_persists_failed(tmp_path, kobo_draft) -> None:
    revision = _revision()
    run, definition = _cold_run(kobo_draft, "normal", revision)

    class _Refusing(_Gateway):
        def publish_in_boundary_order(self, run_id, basis, groups, final_instant):
            return [], RuntimeError("gateway refused")

    host = _host(tmp_path, _Inputs(revision, definition), _Refusing())
    projection = host.start(run)
    assert projection.status == "FAILED" and projection.failure.kind == "PUBLICATION_REFUSED"
    assert HOST_STAGING_FAILURE_KINDS <= OBSERVED_KINDS  # the host-only kind is reached here
    assert projection.content_digest
    restarted = _host(tmp_path, None, _Gateway())
    assert restarted._execution_status(run) == "FAILED"
    with pytest.raises(LabControlRefused) as again:
        restarted.start(run)
    assert again.value.kind == "ALREADY_TERMINAL"


@pytest.mark.parametrize("damage", ["digest", "future", "extra_key"])
def test_damaged_or_future_cold_artifact_reads_unreadable(tmp_path, kobo_draft, damage) -> None:
    revision = _revision()
    run, definition = _cold_run(kobo_draft, "normal", revision)
    _host(tmp_path, _Inputs(revision, definition), _Gateway()).start(run)
    path = tmp_path / "executions" / f"{run.run_id}.yaml"
    head, marker, tail = path.read_text(encoding="utf-8").partition("--- # assetops-lab-history\n")
    document = yaml.safe_load(head)
    if damage == "digest":
        document["content_digest"] = "not-a-digest"
    elif damage == "future":
        document["artifact_schema_version"] = 7
    else:
        document["world"] = "private"
    path.write_text(yaml.safe_dump(document, sort_keys=False) + marker + tail, encoding="utf-8")
    restarted = _host(tmp_path, None, _Gateway())
    assert restarted.projection(run).status == "ARTIFACT_UNREADABLE"
    assert restarted._execution_status(run) == "ARTIFACT_UNREADABLE"
    with pytest.raises(LabControlRefused) as refused:
        restarted.start(run)
    assert refused.value.kind == "ARTIFACT_UNREADABLE"
