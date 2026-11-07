"""DIESEL-1 K0 (ruling DIESEL-1-R3f §9f.4, tests 2-8): the operational-action bridge, L0 and L1, no database.

Kisiwa is registered in memory exactly as K1's fixture test does (`tools/demo_combined_kisiwa.py` `register_in` over
`InMemoryFoundationStore`), and run setup is the real `RunSetupService` over the real `RegisteredLabBasis`. The log
is the promoted `config/operational-actions/kisiwa-001-operational-actions-v1.yaml`, through an in-memory port over
its parsed content or the file adapter. Test 1 (byte-equal pins) and tests 9-10 live in
`host/tests/test_k0_kisiwa_actions.py`.
"""

from __future__ import annotations

import copy
import functools
import json
import sys
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
for extra in (REPO / "tools", REPO / "host", REPO / "host" / "tests"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))

from run_fixtures import FakeRuns, FakeScenarios, FakeSites  # noqa: E402

from assetops_backend.runs.adapters.yaml_operational_action_log import YamlOperationalActionLog  # noqa: E402
from assetops_backend.runs.adapters.yaml_run_store import YamlRunStore  # noqa: E402
from assetops_backend.runs.models import FrozenCause, FrozenReportingPathCondition  # noqa: E402
from assetops_backend.runs.operational_actions import freeze_operational_actions  # noqa: E402
from assetops_backend.runs.parsing import (  # noqa: E402
    parse_run_document,
    parse_run_setup_request,
    render_run_document,
)
from assetops_backend.runs.ports import OperationalActionLogSource, RunConfigurationInvalid  # noqa: E402
from assetops_backend.runs.provenance import frozen_inputs  # noqa: E402
from assetops_backend.runs.refusals import RunSetupRefused  # noqa: E402
from assetops_backend.state_refs import component_state  # noqa: E402

LOG_FILE = REPO / "config" / "operational-actions" / "kisiwa-001-operational-actions-v1.yaml"
F0_RESULT = REPO / ".agent" / "DIESEL-F0" / "probe-result.json"
ACTIONS_SHA256 = "77777c82d82298ffba77a130f8d9ea2c6bb9a80c491ba4b2ac5248c4b735b634"
KEY = {"log_id": "kisiwa-001-operational-actions", "log_version": 1}
IMPORT_AT = datetime(2026, 9, 29, 9, 0, tzinfo=timezone.utc)
INSTALL_AT = datetime(2026, 9, 29, 9, 30, tzinfo=timezone.utc)
SETUP_AT = "2026-09-29T11:00:00Z"
DELIVERY_REF = "kis-delivery-1:881d75f69365834df26000d1c9dbdb4c1216a5390da96725f744189ad53ab9f0"


def log_document() -> dict:
    return yaml.safe_load(LOG_FILE.read_text(encoding="utf-8"))


class MemoryLog:
    """An in-memory `OperationalActionLogPort` over a parsed log."""

    def __init__(self, document: dict | None = None, sha256: str = ACTIONS_SHA256) -> None:
        self.document = log_document() if document is None else document
        self.sha256 = sha256
        self.calls: list[tuple[str, int]] = []

    def read_log(self, log_id: str, log_version: int) -> OperationalActionLogSource:
        self.calls.append((log_id, log_version))
        return OperationalActionLogSource(sha256=self.sha256, document=copy.deepcopy(self.document))


@functools.lru_cache(maxsize=1)
def kisiwa():
    """KISIWA-001 registered in memory (K1's fixture path) and the real registered basis over it."""
    from foundation_fakes import InMemoryFoundationStore
    from kisiwa import KisiwaRegistered

    import demo_combined_kisiwa as kis

    store = InMemoryFoundationStore()
    kis.register_in(store, IMPORT_AT, INSTALL_AT)
    return KisiwaRegistered(store, SETUP_AT)


def probe():
    import probe_kisiwa_fuel

    return probe_kisiwa_fuel


def draft(port=None, *, k: int = 2, key: dict | None = KEY, model=None, fuel=None, runs: FakeRuns | None = None):
    """One Kisiwa day-run Draft (F0r's run k interval and scenario), with the request key when given."""
    from assetops_backend.runs.profiles import MINI_GRID_V7_MODEL, REGISTERED_KOBO_PUBLICATION_PROFILE_V5
    from assetops_backend.runs.service import RunSetupService
    from assetops_backend.scenarios.parsing import parse_scenario_document

    p, reg = probe(), kisiwa()
    document = p.day_document(p.START_SOC, p.START_FUEL if fuel is None else fuel)
    definition = parse_scenario_document(copy.deepcopy(document), source="a Kisiwa scenario", origin="SHIPPED")
    chosen = MINI_GRID_V7_MODEL if model is None else model
    profile = REGISTERED_KOBO_PUBLICATION_PROFILE_V5
    store = FakeRuns() if runs is None else runs
    setup = RunSetupService(
        store, FakeSites(()), FakeScenarios((definition,)), model_profiles=(chosen,), publication_profiles=(profile,),
        now=lambda: SETUP_AT, registered_bases=reg.basis, operational_actions=port)
    start = p._run_start(k)
    request = {
        "site_id": "KISIWA-001", "foundation_version": reg.foundation_version, "scenario_id": definition.scenario_id,
        "scenario_version": definition.version.scenario_version,
        "interval": {"start_time": p._iso(start), "end_time": p._iso(start + timedelta(days=1))},
        "timestep_minutes": 5, "seed": 20260929,
        "model_profile": {"profile_id": chosen.model_profile_id, "profile_version": chosen.model_profile_version},
        "publication_profile": {"profile_id": profile.publication_profile_id,
                                "profile_version": profile.publication_profile_version},
        "run_inputs": [],
        **({} if key is None else {"operational_actions": key}),
    }
    return setup.create_draft_run(request), store


def refused(port=None, **kwargs) -> RunSetupRefused:
    """A request that must be refused; nothing may reach the run store."""
    store = FakeRuns()
    with pytest.raises(RunSetupRefused) as raised:
        draft(port, runs=store, **kwargs)
    assert store.written == []
    return raised.value


def with_action(action_id: str, **changes) -> dict:
    document = log_document()
    for action in document["actions"]:
        if action["action_id"] == action_id:
            action.update(changes)
    return document


# --- 4: setup on the registered path ----------------------------------------------------------------------------


def test_run_2_freezes_the_delivery_as_an_operational_action_field() -> None:
    run, store = draft(MemoryLog(), k=2)
    identity = run.deterministic_identity
    actions = [c for c in identity.causes if c.origin == "OPERATIONAL_ACTION"]
    assert len(actions) == 1 and store.written == [run]
    cause = actions[0]
    assert cause.event_id == "kis-delivery-1/tank-increase" and not cause.event_id.startswith("OPERATIONAL_ACTION/")
    assert (cause.direction, cause.timing_shape, cause.offset_minutes, cause.duration_minutes) == (
        "INCREASE", "POINT", 1140, None)
    assert (cause.canonical_value, cause.canonical_unit, cause.state_ref.addressed_key) == (
        300.0, "L", "fuel-tank-volume@fuel-tank")
    assert cause.action_ref == DELIVERY_REF
    f0 = json.loads(F0_RESULT.read_text(encoding="utf-8"))
    assert list(identity.intervention_history) == ["OPERATIONAL_ACTION:" + cause.action_ref]
    assert list(identity.intervention_history) == f0["runs"][1]["intervention_history"]
    assert identity.operational_action_log.sha256 == ACTIONS_SHA256 == f0["assumptions"]["actions_sha256"]
    assert [a.action_id for a in identity.operational_action_log.actions] == ["kis-delivery-1"]
    assert identity.reporting_path_conditions == ()


def test_run_4_freezes_the_removal_and_the_unplugged_sensor() -> None:
    run, _ = draft(MemoryLog(), k=4)
    identity = run.deterministic_identity
    (cause,) = [c for c in identity.causes if c.origin == "OPERATIONAL_ACTION"]
    (condition,) = identity.reporting_path_conditions
    assert cause.event_id == "kis-removal-1/tank-decrease"
    assert (cause.direction, cause.timing_shape, cause.offset_minutes, cause.duration_minutes,
            cause.canonical_value) == ("DECREASE", "WINDOW", 600, 45, 120.0)
    assert condition.event_id == "kis-removal-1/sensor-disconnected"
    assert condition.state_ref.addressed_key == "fuel-level-reporting-availability@fuel-tank"
    assert (condition.origin, condition.action_ref) == ("OPERATIONAL_ACTION", cause.action_ref)
    assert (condition.timing_shape, condition.offset_minutes, condition.duration_minutes) == ("WINDOW", 590, 90)
    f0 = json.loads(F0_RESULT.read_text(encoding="utf-8"))
    assert list(identity.intervention_history) == f0["runs"][3]["intervention_history"]


def test_runs_with_only_effect_free_actions_freeze_an_empty_log() -> None:
    """Run 6 holds the seal, the sensor fix and two dips: validated, nothing frozen, the log still named."""
    run, _ = draft(MemoryLog(), k=6)
    identity = run.deterministic_identity
    assert identity.operational_action_log is not None and identity.operational_action_log.actions == ()
    assert identity.intervention_history == () and all(c.origin == "SCENARIO" for c in identity.causes)
    assert render_run_document(run)["deterministic_identity"]["operational_action_log"]["actions"] == []


def test_a_run_naming_no_log_never_reads_the_port() -> None:
    port = MemoryLog()
    run, _ = draft(port, k=2, key=None)
    assert port.calls == [] and run.deterministic_identity.operational_action_log is None


# --- 2: model and parse refusals ------------------------------------------------------------------------------


def _cause(**changes) -> FrozenCause:
    base = {"event_id": "e", "state_ref": component_state("fuel-tank-volume", "fuel-tank"), "direction": "INCREASE",
            "parameter_id": "p", "canonical_value": 1.0, "canonical_unit": "L", "dimension": "VOLUME",
            "timing_shape": "POINT", "offset_minutes": 0, "duration_minutes": None}
    return FrozenCause(**{**base, **changes})


@pytest.mark.parametrize("changes", [
    {"origin": "LAB"},
    {"origin": "OPERATIONAL_ACTION"},
    {"origin": "SCENARIO", "action_ref": DELIVERY_REF},
    {"origin": "OPERATIONAL_ACTION", "action_ref": "kis-delivery-1:not-a-hash"},
])
def test_the_frozen_records_refuse_an_invalid_origin(changes) -> None:
    with pytest.raises(ValueError, match="^CAUSE_ORIGIN_INVALID: "):
        _cause(**changes)
    with pytest.raises(ValueError, match="^CAUSE_ORIGIN_INVALID: "):
        FrozenReportingPathCondition(event_id="c", state_ref=component_state("x", "fuel-tank"), timing_shape="WINDOW",
                                     offset_minutes=0, duration_minutes=5, **changes)


def _action_document(k: int = 4) -> dict:
    run, _ = draft(MemoryLog(), k=k)
    return copy.deepcopy(render_run_document(run))


def _action_cause(identity: dict) -> dict:
    return next(c for c in identity["causes"] if "origin" in c)


def _stored_scenario_origin(doc):
    doc["deterministic_identity"]["causes"].append({**_action_cause(doc["deterministic_identity"]),
                                                    "event_id": "x", "origin": "SCENARIO"})


def _ref_without_origin(doc):
    _action_cause(doc["deterministic_identity"]).pop("origin")


def _origin_without_ref(doc):
    _action_cause(doc["deterministic_identity"]).pop("action_ref")


def _unknown_origin(doc):
    _action_cause(doc["deterministic_identity"])["origin"] = "LAB"


def _history_mismatch(doc):
    doc["deterministic_identity"]["intervention_history"] = []


def _dangling_ref(doc):
    for item in (*doc["deterministic_identity"]["causes"], *doc["deterministic_identity"]["reporting_path_conditions"]):
        if "action_ref" in item:
            item["action_ref"] = "kis-removal-1:" + "f" * 64


def _orphan_log_action(doc):
    identity = doc["deterministic_identity"]
    identity["causes"] = [c for c in identity["causes"] if "origin" not in c]
    identity["reporting_path_conditions"] = []


def _history_without_log(doc):
    doc["deterministic_identity"].pop("operational_action_log")


def _unknown_log_key(doc):
    doc["deterministic_identity"]["operational_action_log"]["latest"] = True


@pytest.mark.parametrize("mutate", [_stored_scenario_origin, _ref_without_origin, _origin_without_ref, _unknown_origin,
                                    _history_mismatch, _dangling_ref, _orphan_log_action, _history_without_log,
                                    _unknown_log_key])
def test_the_parser_refuses_every_broken_origin(mutate) -> None:
    doc = _action_document()
    parse_run_document(copy.deepcopy(doc), source="k0")  # the unbroken document parses
    mutate(doc)
    with pytest.raises(RunConfigurationInvalid, match="^CAUSE_ORIGIN_INVALID: "):
        parse_run_document(doc, source="k0")


@pytest.mark.parametrize("value", [
    "kisiwa-001-operational-actions", {"log_id": "kisiwa-001-operational-actions"},
    {"log_id": "Kisiwa", "log_version": 1}, {"log_id": "kisiwa-001-operational-actions", "log_version": True},
    {"log_id": "kisiwa-001-operational-actions", "log_version": 0}, {**KEY, "latest": True},
])
def test_the_request_key_is_exactly_a_log_id_and_version(value) -> None:
    from run_fixtures import setup_request

    with pytest.raises(RunSetupRefused) as raised:
        parse_run_setup_request(setup_request(operational_actions=value))
    assert raised.value.kind == "REQUEST_INVALID"
    assert parse_run_setup_request(setup_request(operational_actions=KEY)).operational_actions.log_version == 1


# --- 3: round trip through every run store ------------------------------------------------------------------------


def test_round_trip_keeps_both_fields_for_an_action_and_neither_for_a_scenario(tmp_path) -> None:
    import fixtures as host_fixtures

    action_run, _ = draft(MemoryLog(), k=4)
    scenario_run, _ = draft(MemoryLog(), k=4, key=None)
    yaml_store = YamlRunStore(tmp_path)
    for run in (action_run, scenario_run):
        yaml_store.create_run(run)
        for store in (FakeRuns(), host_fixtures.FakeRuns()):
            store.create_run(run)
            assert store.get_run(run.run_id) == run
        assert yaml_store.get_run(run.run_id) == run
    stored = {path.name: path.read_text(encoding="utf-8") for path in tmp_path.rglob("*.yaml")}
    assert len(stored) == 2
    texts = sorted(stored.values(), key=lambda text: "origin:" in text)
    assert "origin:" not in texts[0] and "action_ref:" not in texts[0] and "operational_action_log" not in texts[0]
    assert texts[1].count("origin: OPERATIONAL_ACTION") == 2 and texts[1].count("action_ref:") == 2
    back = yaml_store.get_run(action_run.run_id).deterministic_identity
    assert {(c.origin, c.action_ref) for c in back.causes if c.origin != "SCENARIO"} == {
        ("OPERATIONAL_ACTION", action_run.deterministic_identity.reporting_path_conditions[0].action_ref)}


# --- 5: each setup refusal kind ---------------------------------------------------------------------------------


def _direct(identity_change, document=None) -> RunSetupRefused:
    """For the two kinds no request can reach on the shipped model and scenario: the loader, called directly."""
    from assetops_backend.runs.parsing import OperationalActionsRequest, RunSetupRequest
    from assetops_backend.runs.profiles import MINI_GRID_V7_MODEL

    run, _ = draft(MemoryLog(), k=2, key=None)
    p = probe()
    start = p._run_start(2)
    request = RunSetupRequest(
        site_id="KISIWA-001", foundation_version=1, scenario_id="s", scenario_version=1, start_time=p._iso(start),
        end_time=p._iso(start + timedelta(days=1)), duration_minutes=1440, timestep_minutes=5, seed=1,
        model_profile_id="mini-grid", model_profile_version=7, publication_profile_id="p",
        publication_profile_version=1, run_inputs=(), operational_actions=OperationalActionsRequest(**KEY))
    with pytest.raises(RunSetupRefused) as raised:
        freeze_operational_actions(
            request, identity_change(run.deterministic_identity),
            OperationalActionLogSource(ACTIONS_SHA256, document or log_document()), model=MINI_GRID_V7_MODEL,
            start=request.start_time, end=request.end_time, component_ids=frozenset({"fuel-tank"}))
    return raised.value


def _not_litres(identity):
    return replace(identity, initialization_inputs=tuple(
        replace(i, canonical_unit="m3") if i.state_ref.addressed_key == "fuel-tank-volume@fuel-tank" else i
        for i in identity.initialization_inputs))


def _clashing_event(identity):
    return replace(identity, causes=identity.causes + (
        replace(_cause(event_id="kis-delivery-1/tank-increase")),))


def operational_action_refusals() -> set[str]:
    """Each of the eleven K0 setup refusal kinds, produced, with nothing written. `test_run_setup.py` adds these to
    its produced set."""
    from run_fixtures import site, model_profile, publication_profile, scenario, setup_request

    from assetops_backend.runs.profiles import DAYTIME_MINI_GRID_MODEL
    from assetops_backend.runs.service import RunSetupService

    kinds: dict[str, RunSetupRefused] = {}
    legacy_store = FakeRuns()
    legacy = RunSetupService(legacy_store, FakeSites((site(),)), FakeScenarios((scenario(),)),
                             model_profiles=(model_profile(),), publication_profiles=(publication_profile(),),
                             operational_actions=MemoryLog())
    with pytest.raises(RunSetupRefused) as raised:
        legacy.create_draft_run(setup_request(operational_actions=KEY))
    assert legacy_store.written == []
    kinds["OPERATIONAL_ACTIONS_UNSUPPORTED_PATH"] = raised.value
    kinds["OPERATIONAL_ACTION_LOG_UNAVAILABLE"] = refused(None, k=2)
    kinds["OPERATIONAL_ACTION_LOG_INVALID"] = refused(MemoryLog({**log_document(), "latest": True}), k=2)
    kinds["OPERATIONAL_ACTION_LOG_MISMATCH"] = refused(MemoryLog({**log_document(), "log_version": 2}), k=2)
    kinds["OPERATIONAL_ACTION_COMPONENT_UNKNOWN"] = refused(
        MemoryLog(with_action("kis-delivery-1", component_id="day-tank")), k=2)
    # The shipped daytime model has no fuel stock at all: the Draft would be BLOCKED, and the action refuses first.
    kinds["OPERATIONAL_ACTION_STATE_NOT_CAUSAL"] = refused(MemoryLog(), k=2, model=DAYTIME_MINI_GRID_MODEL)
    kinds["OPERATIONAL_ACTION_UNIT"] = _direct(_not_litres)
    kinds["OPERATIONAL_ACTION_SPAN_OUTSIDE_RUN"] = refused(
        MemoryLog(with_action("kis-removal-1", duration_minutes=900)), k=4)
    kinds["OPERATIONAL_ACTION_OVER_CAPACITY"] = refused(MemoryLog(with_action("kis-delivery-1", volume_l=301)), k=2)
    kinds["OPERATIONAL_ACTION_OVER_STOCK"] = refused(MemoryLog(with_action("kis-removal-1", volume_l=701)), k=4)
    kinds["OPERATIONAL_ACTION_EVENT_ID_CONFLICT"] = _direct(_clashing_event)
    for kind, error in kinds.items():
        assert error.kind == kind, (kind, error.kind, str(error))
    return set(kinds)


def test_each_setup_refusal_kind_is_produced_with_nothing_written() -> None:
    from assetops_backend.runs.refusals import RUN_SETUP_REFUSAL_KINDS

    produced = operational_action_refusals()
    assert len(produced) == 11 and produced <= RUN_SETUP_REFUSAL_KINDS


def test_the_capacity_and_stock_bounds_are_exact_at_their_edges() -> None:
    """700 L + 300 L = 1000 L capacity is accepted; 301 L is refused (above). 700 L removed from 700 L is accepted."""
    draft(MemoryLog(), k=2)
    draft(MemoryLog(with_action("kis-removal-1", volume_l=700)), k=4)
    assert refused(MemoryLog(with_action("kis-delivery-1", volume_l=300.5)), k=2).kind == (
        "OPERATIONAL_ACTION_OVER_CAPACITY")


@pytest.mark.parametrize("change", [
    {"at": "2026-10-04T22:00:30Z"},
    {"sensor_disconnected": {"at": "2026-10-04T11:55:00Z", "duration_minutes": 90}},
    {"sensor_disconnected": {"at": "2026-10-05T11:00:00Z", "duration_minutes": 90}},
])
def test_spans_outside_the_run_or_off_the_minute_are_refused_never_clipped(change) -> None:
    error = refused(MemoryLog(with_action("kis-removal-1", **change)), k=4)
    assert error.kind == "OPERATIONAL_ACTION_SPAN_OUTSIDE_RUN"


def test_a_cold_or_ev_document_run_cannot_name_a_log() -> None:
    from test_w202_cold_run_identity import cold_request, cold_service
    from test_w205b_ev_scenarios import ev_request, ev_service

    for (setup, store), request in ((cold_service(), cold_request()), (ev_service(), ev_request())):
        with pytest.raises(RunSetupRefused) as raised:
            setup.create_draft_run({**request, "operational_actions": KEY})
        assert raised.value.kind == "OPERATIONAL_ACTIONS_UNSUPPORTED_PATH" and store.written == []


# --- 6: provenance --------------------------------------------------------------------------------------------


def test_provenance_names_the_operational_action_and_the_log() -> None:
    run, _ = draft(MemoryLog(), k=4)
    rows = frozen_inputs(run.deterministic_identity)
    detail = ("Operational action kis-removal-1 (FUEL_REMOVAL_UNRECORDED, by Unidentified), "
              "log kisiwa-001-operational-actions v1")
    cause = next(r for r in rows if r.field == "Cause kis-removal-1/tank-decrease")
    condition = next(r for r in rows if r.field == "Reporting path kis-removal-1/sensor-disconnected")
    log = next(r for r in rows if r.identity_field == "operational_action_log")
    assert (cause.answered_by, cause.answered_by_detail) == ("OPERATIONAL_ACTION", detail)
    assert (condition.answered_by, condition.answered_by_detail) == ("OPERATIONAL_ACTION", detail)
    assert log.value == f"kisiwa-001-operational-actions v1, sha256 {ACTIONS_SHA256}"
    log_detail = "1 actions with a physical effect in this run"
    assert (log.answered_by, log.answered_by_detail) == ("OPERATIONAL_ACTION", log_detail)
    # Every other row is byte-equal to the same run without the log (Kisiwa's scenario declares no cause or
    # condition, so those two collections are compared in the pinned fuel-loss-event run of test 1).
    plain, _ = draft(MemoryLog(), k=4, key=None)
    plain_rows = frozen_inputs(plain.deterministic_identity)
    moved = {"causes", "reporting_path_conditions", "intervention_history", "operational_action_log"}
    assert [r for r in rows if r.identity_field not in moved] == [r for r in plain_rows if r.identity_field not in moved]
    assert all(r.identity_field != "operational_action_log" for r in plain_rows)
    assert all(r.answered_by == "SCENARIO" for r in plain_rows if r.identity_field in ("causes",
                                                                                    "reporting_path_conditions"))


def test_a_run_naming_a_log_covers_every_identity_field_with_no_exclusion() -> None:
    """DIESEL-1-R3i deviation 4: the exclusion in test_run_setup's coverage test is conditional on no log named."""
    from dataclasses import fields

    from assetops_backend.runs.models import DeterministicIdentity

    run, _ = draft(MemoryLog(), k=4)
    rows = frozen_inputs(run.deterministic_identity)
    assert rows
    assert {row.identity_field for row in rows} == {field.name for field in fields(DeterministicIdentity)}


# --- 7: the product never reads the log --------------------------------------------------------------------------


def test_no_product_module_names_the_operational_action_directory() -> None:
    adapter = REPO / "backend" / "assetops_backend" / "runs" / "adapters" / "yaml_operational_action_log.py"
    backend = [p for p in (REPO / "backend" / "assetops_backend").rglob("*.py")
               if "operational-actions" in p.read_text(encoding="utf-8")]
    assert backend == [adapter]
    frontend = [p for p in (REPO / "frontend" / "src").rglob("*")
                if p.is_file() and p.suffix in {".ts", ".tsx", ".js", ".jsx", ".json", ".css"}
                and "operational-actions" in p.read_text(encoding="utf-8", errors="replace")]
    assert frontend == []
    roots = [p for p in (REPO / "backend" / "assetops_backend").rglob("*.py")
             if "config/operational-actions" in p.read_text(encoding="utf-8")
             or '"config" / "operational-actions"' in p.read_text(encoding="utf-8")]
    assert roots == [adapter]
    assert "config/operational-actions/* text eol=lf" in (REPO / ".gitattributes").read_text(encoding="utf-8")


# --- 8: the file adapter -------------------------------------------------------------------------------------


def test_the_adapter_hashes_lf_and_crlf_alike(tmp_path) -> None:
    lf = LOG_FILE.read_bytes().replace(b"\r\n", b"\n")
    assert b"\r" not in lf
    (tmp_path / "lf").mkdir()
    (tmp_path / "crlf").mkdir()
    (tmp_path / "lf" / LOG_FILE.name).write_bytes(lf)
    (tmp_path / "crlf" / LOG_FILE.name).write_bytes(lf.replace(b"\n", b"\r\n"))
    a = YamlOperationalActionLog(tmp_path / "lf").read_log(**KEY)
    b = YamlOperationalActionLog(tmp_path / "crlf").read_log(**KEY)
    assert a.sha256 == b.sha256 == ACTIONS_SHA256
    assert a.document == b.document == log_document()
    assert YamlOperationalActionLog().read_log(**KEY).sha256 == ACTIONS_SHA256


def test_a_wrong_file_name_is_a_mismatch_and_a_missing_file_unavailable(tmp_path) -> None:
    (tmp_path / "kisiwa-001-operational-actions-v2.yaml").write_bytes(LOG_FILE.read_bytes())
    port = YamlOperationalActionLog(tmp_path)
    assert refused(port, k=2, key={**KEY, "log_version": 2}).kind == "OPERATIONAL_ACTION_LOG_MISMATCH"
    assert refused(port, k=2, key=KEY).kind == "OPERATIONAL_ACTION_LOG_UNAVAILABLE"
    run, _ = draft(YamlOperationalActionLog(), k=2)
    assert run.deterministic_identity.operational_action_log.sha256 == ACTIONS_SHA256
