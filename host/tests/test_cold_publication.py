"""W2-02: a cold run's frozen-input verification and public v2 series (`D-2026-10-17-w2-02-buildspec`)."""

from __future__ import annotations

import copy
import json
import re
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml
from fixtures import draft

from assetops_backend.scenarios.cold_parsing import observation_sha256, parse_cold_scenario_document
from assetops_backend.sites.foundation_content import content_digest
from assetops_contracts.gateway_report import parse_device_report_v2_text
from cold_publication import cold_reports, verify_cold_inputs
from execution_adapter import FrozenRunNotReconstructible

ROOT = Path(__file__).resolve().parents[2]
REVISION_ID = "5f0c0d6e-0000-4000-8000-000000000001"


def _definition(case: str):
    path = ROOT / "config" / "scenarios" / f"cold-{case}.yaml"
    return parse_cold_scenario_document(yaml.safe_load(path.read_text(encoding="utf-8")), source=str(path))


def _revision(content=None):
    if content is None:
        site = yaml.safe_load((ROOT / "backend/tests/fixtures/w2/cold-lab-001.yaml").read_text(encoding="utf-8"))
        content = site["foundation"]
    return SimpleNamespace(id=REVISION_ID, content=content, content_sha256=content_digest(content))


def _cold_run(definition, revision):
    run = draft()
    identity = run.deterministic_identity
    profiles = replace(identity.profiles, model_profile_id="cold-thermal", model_profile_version=1,
                       publication_profile_id="cold-publication", publication_profile_version=1,
                       observation_profile_id="cold-observation", observation_profile_version=1,
                       observation_sha256=observation_sha256(definition))
    scenario = replace(identity.scenario, scenario_id=definition.scenario_id, scenario_version=definition.version,
                       scenario_sha256=definition.scenario_sha256)
    basis = SimpleNamespace(foundation_revision_id=REVISION_ID, foundation_content_sha256=revision.content_sha256)
    return replace(run, deterministic_identity=replace(identity, profiles=profiles, scenario=scenario),
                   registered_basis=basis)


def _series(case: str):
    definition, revision = _definition(case), _revision()
    reports = cold_reports(verify_cold_inputs(_cold_run(definition, revision), revision, definition))
    return [(r, parse_device_report_v2_text(r.report_text)) for r in reports]


def _probe_points(series) -> list:
    return [p for _, p in series if (p.device_id, p.signal_id) == ("chamber-probe", "temperature")]


def test_verified_inputs_produce_the_public_v2_series() -> None:
    normal = _series("normal")
    assert len(_probe_points(normal)) == 13
    starts = [(p.source_time, p.outcome) for _, p in normal if p.record_kind == "START_RESULT"]
    assert starts == [("2026-10-06T19:07:00Z", "SUCCEEDED")]
    transfers = [p.source_time for _, p in normal if p.record_kind == "TRANSFER_RESULT"]
    assert transfers[0] == "2026-10-06T19:08:00Z"
    for report, parsed in normal:
        assert report.report_key == parsed.report_key and report.report_key.startswith("cold:")
        assert report.published_at > report.source_time  # +3 s publication latency
        assert "run" not in json.loads(report.report_text)
    # The series is deterministic: a second execution gives identical bytes.
    assert [r.report_text for r, _ in normal] == [r.report_text for r, _ in _series("normal")]


def test_observation_faults_reach_the_series() -> None:
    assert len(_probe_points(_series("missing-probe"))) == 7
    late = [r for r, _ in _series("late-reading") if r.held]
    assert [(r.source_time, r.published_at) for r in late] == [("2026-10-06T19:20:00Z", "2026-10-06T20:10:00Z")]
    failed = [(p.source_time, p.outcome) for _, p in _series("excursion") if p.record_kind == "START_RESULT"]
    assert failed == [("2026-10-06T19:05:00Z", "FAILED")]
    contradictory = [p for _, p in _series("contradictory") if p.record_kind == "START_RESULT"]
    assert sorted(p.outcome for p in contradictory) == ["FAILED", "SUCCEEDED"]
    assert len({p.event_id for p in contradictory}) == 2
    assert len({p.correlation_id for p in contradictory}) == 1
    # Ruled form: `cold-` + 64 hex, inside the unchanged V4 identifier grammar.
    v4_identifier = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9._-]{0,126}[A-Za-z0-9])?")
    for p in contradictory:
        for identifier in (p.event_id, p.correlation_id):
            assert re.fullmatch(r"cold-[0-9a-f]{64}", identifier) and v4_identifier.fullmatch(identifier)


def test_mismatched_frozen_inputs_refuse_before_any_report() -> None:
    definition, revision = _definition("normal"), _revision()
    run = _cold_run(definition, revision)
    other = _definition("excursion")
    changed = copy.deepcopy(revision.content)
    changed["components"][0]["properties"][0]["value"] = 9.9
    missing = copy.deepcopy(revision.content)
    missing["components"][0]["properties"] = missing["components"][0]["properties"][1:]
    for bad_revision, bad_definition in (
        (None, definition),
        (SimpleNamespace(id="another-revision", content=revision.content, content_sha256=revision.content_sha256),
         definition),
        (SimpleNamespace(id=REVISION_ID, content=changed, content_sha256=revision.content_sha256), definition),
        (revision, None),
        (revision, replace(definition, scenario_sha256=other.scenario_sha256)),
        (revision, replace(definition, observations=_definition("missing-probe").observations)),
    ):
        with pytest.raises(FrozenRunNotReconstructible):
            verify_cold_inputs(run, bad_revision, bad_definition)
    # A revision without all thirteen values refuses; nothing falls back to fixture numbers.
    short = _revision(missing)
    with pytest.raises(FrozenRunNotReconstructible):
        verify_cold_inputs(_cold_run(definition, short), short, definition)
