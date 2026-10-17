"""W2-02 strict `cold-scenario/1` documents (`D-2026-10-17-w2-02-buildspec`, technical design section 4)."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest
import yaml

from assetops_backend.scenarios.cold_parsing import (
    ColdScenarioDefinition,
    parse_cold_scenario_document,
)
from assetops_backend.scenarios.parsing import parse_scenario_document
from assetops_backend.scenarios.ports import ScenarioConfigurationInvalid

SCENARIOS = Path(__file__).resolve().parents[2] / "config" / "scenarios"
CASES = ("normal", "excursion", "backup-failed", "missing-probe", "late-reading", "contradictory")


def load(case: str) -> dict:
    return yaml.safe_load((SCENARIOS / f"cold-{case}.yaml").read_text(encoding="utf-8"))


def at(hhmm: str) -> str:
    return f"2026-10-06T{hhmm}:00Z"


def test_six_strict_documents() -> None:
    parsed = {case: parse_cold_scenario_document(load(case)) for case in CASES}
    for case, scenario in parsed.items():
        assert isinstance(scenario, ColdScenarioDefinition)
        assert scenario.scenario_id == f"cold-{case}" and scenario.seed == 20417
        assert (scenario.start, scenario.end) == (at("19:00"), at("20:00"))
        assert scenario.site_code == "COLD-LAB-001" and scenario.backup_enabled is True
        assert (scenario.model_profile, scenario.publication_profile, scenario.observation_profile) == (
            "cold-thermal/1", "cold-publication/1", "cold-observation/1")
        assert len(scenario.scenario_sha256) == 64
    assert len({s.scenario_sha256 for s in parsed.values()}) == 6
    normal = parsed["normal"]
    assert (normal.initial_temperature_deg_c, normal.ambient_deg_c) == ("3", "10")
    assert [(f.at, f.kind, f.asset, f.value) for f in normal.forcings] == [
        (at("19:05"), "GRID_LOSS", "grid-1", "LOST"), (at("19:35"), "GRID_RESTORE", "grid-1", "AVAILABLE")]
    failure = [(at("19:00"), "GENERATOR_FAILURE", "generator-1", "FAILED"), (at("19:00"), "GRID_LOSS", "grid-1", "LOST")]
    for case in CASES[1:]:
        s = parsed[case]
        assert (s.initial_temperature_deg_c, s.ambient_deg_c) == ("3.8", "20")
        assert [(f.at, f.kind, f.asset, f.value) for f in s.forcings][:2] == failure
    assert [(f.at, f.kind) for f in parsed["backup-failed"].forcings][2:] == [
        (at("19:10"), "DOOR_OPEN"), (at("19:11"), "DOOR_CLOSE")]
    assert [(o.at, o.action) for o in parsed["missing-probe"].observations] == [
        (at(t), "DROP") for t in ("19:15", "19:20", "19:25", "19:30", "19:35", "19:40")]
    [hold] = parsed["late-reading"].observations
    assert (hold.at, hold.action, hold.release_at) == (at("19:20"), "HOLD", at("20:10"))
    [add] = parsed["contradictory"].observations
    assert (add.at, add.kind, add.action, add.outcome) == (at("19:05"), "START_RESULT", "ADD", "SUCCEEDED")
    for case in ("normal", "excursion", "backup-failed"):
        assert parsed[case].observations == ()
    # The legacy timeline parser accepts none of the cold keys.
    with pytest.raises(ScenarioConfigurationInvalid):
        parse_scenario_document(load("normal"), source="test", origin="SHIPPED")


def test_digest_ignores_yaml_format() -> None:
    text = (SCENARIOS / "cold-excursion.yaml").read_text(encoding="utf-8")
    reformatted = yaml.safe_dump(yaml.safe_load(text), sort_keys=True, default_flow_style=True)
    commented = "# a different comment\n" + text.replace("\n", "  # trailing\n", 3)
    digests = {parse_cold_scenario_document(yaml.safe_load(t)).scenario_sha256 for t in (text, reformatted, commented)}
    assert len(digests) == 1
    changed = load("excursion")
    changed["ambient_deg_c"] = "21"
    assert parse_cold_scenario_document(changed).scenario_sha256 not in digests


def _refused(mutate) -> None:
    document = copy.deepcopy(load("contradictory"))
    mutate(document)
    with pytest.raises(ScenarioConfigurationInvalid):
        parse_cold_scenario_document(document)


def test_wrong_asset_or_observation_refused() -> None:
    _refused(lambda d: d["forcings"][1].update(asset="grid-2"))
    _refused(lambda d: d["forcings"][0].update(value="LOST"))
    _refused(lambda d: d["forcings"].reverse())
    _refused(lambda d: d["forcings"].append(dict(d["forcings"][1])))
    _refused(lambda d: d["forcings"].append({"at": at("20:00"), "kind": "GRID_RESTORE", "asset": "grid-1",
                                             "value": "AVAILABLE"}))
    _refused(lambda d: d["forcings"][0].update(extra=1))
    _refused(lambda d: d.update(surprise=True))
    _refused(lambda d: d.pop("observations"))
    _refused(lambda d: d.update(initial_temperature_deg_c="3.80"))
    _refused(lambda d: d.update(ambient_deg_c=20))
    _refused(lambda d: d.update(site_code="COLD-001"))
    _refused(lambda d: d.update(observation_profile="cold-observation/2"))
    _refused(lambda d: d["observations"][0].update(device_id="probe-1"))
    _refused(lambda d: d["observations"][0].update(action="DROP"))
    _refused(lambda d: d["observations"][0].update(outcome="FAILED"))
    _refused(lambda d: d["observations"][0].update(release_at=at("19:30")))
    _refused(lambda d: d["observations"].append({"at": at("19:20"), "kind": "PROBE_REPORT", "device_id": "probe-1",
                                                 "action": "HOLD", "outcome": None, "release_at": None}))
    _refused(lambda d: d["observations"].append({"at": at("19:20"), "kind": "PROBE_REPORT", "device_id": "probe-1",
                                                 "action": "DROP", "outcome": "SUCCEEDED", "release_at": None}))
    _refused(lambda d: d["observations"][0].update(at="2026-10-06T19:05:00+00:00"))
