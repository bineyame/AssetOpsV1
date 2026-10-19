"""W2-05b commit 4: an EV run through the Host Lab - frozen re-read, one-shot window, Stage, schema-7 artifact,
durable delayed schedule, restart and the Commit gate (`.agent/W2-05b-build-spec.md` q4 Q20-Q25).

A real EV Draft is frozen by `RunSetupService` over a fresh in-memory EV-LAB-001 install (corrected map), so the
registered basis, snapshot bytes and signal mappings are the production ones; `StoreEvInputs` re-reads the same
store and the shipped scenario documents. The gateway is a recording fake of
`RegisteredGatewayPublisher.publish_in_boundary_order` so the test sees exactly which texts reach it and when.
"""

from __future__ import annotations

import json
import sys
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from fractions import Fraction
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend" / "tests"))

from foundation_fakes import InMemoryFoundationStore  # noqa: E402
from run_fixtures import FakeRuns, FakeScenarios, FakeSites  # noqa: E402

from assetops_backend.config import DEVELOPMENT_TENANT_SLUG  # noqa: E402
from assetops_backend.runs.profiles import EV_CHARGER_MODEL, EV_PUBLICATION_PROFILE  # noqa: E402
from assetops_backend.runs.registered_basis import RegisteredLabBasis  # noqa: E402
from assetops_backend.runs.service import RunSetupService  # noqa: E402
from assetops_backend.scenarios.adapters.yaml_shipped_scenario_store import ReadOnlyYamlScenarioStore  # noqa: E402
from assetops_backend.sites.cutover import ImportedSiteRegistry  # noqa: E402
from assetops_backend.sites.ev_lab import install_ev_lab  # noqa: E402
from assetops_backend.sites.foundation_service import FoundationService  # noqa: E402
from assetops_contracts.gateway_report import parse_device_report_v2_text  # noqa: E402
from assetops_contracts.lab_projection import LabControlRefused  # noqa: E402
from assetops_gateway.ipc import GatewayUnavailable  # noqa: E402
from ev_lab import (  # noqa: E402
    EMPTY_EV_SERIES_DIGEST,
    EV_ARTIFACT_KEYS,
    EV_NOTES,
    StoreEvInputs,
    ev_delay_event_id,
)
from ev_publication import ev_parameters  # noqa: E402
from execution_adapter import FrozenRunNotReconstructible  # noqa: E402
from lab_execution import HostLabExecution, YamlExecutionArtifacts  # noqa: E402
from lab_history import HISTORY_MARKER  # noqa: E402
from publication_schedule import JsonPublicationSchedules  # noqa: E402
from source_stages import JsonSourceStages  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
NOW = datetime(2026, 10, 7, 12, 0, tzinfo=timezone.utc)
CLOSE = "2026-10-06T09:00:00Z"
RELEASE = "2026-10-06T09:05:00Z"
PINNED_COMPLETE_DIGEST = "6fc2f2a87966c869d1476cd05f0e3ac4e24d6e137cfce5780fafb46a14adab2c"
SHIPPED = ReadOnlyYamlScenarioStore(ROOT / "config" / "scenarios")


class _Repository:
    """The scenario repository port over the shipped documents (what `create_app` composes)."""

    def get_scenario(self, scenario_id):
        from assetops_backend.scenarios.ports import ScenarioNotFound

        for definition in SHIPPED.list_scenarios():
            if definition.scenario_id == scenario_id:
                return definition
        raise ScenarioNotFound(scenario_id)

    def list_scenarios(self):
        return SHIPPED.list_scenarios()


SCENARIOS = _Repository()


@pytest.fixture(scope="module")
def world():
    store = InMemoryFoundationStore()
    install_ev_lab(store, tenant_slug=DEVELOPMENT_TENANT_SLUG, clock=lambda: NOW - timedelta(hours=3))
    return store


def _definition(case: str):
    return next(s for s in SCENARIOS.list_scenarios() if s.scenario_id == f"ev-{case}")


def _draft(store, case: str):
    setup = RunSetupService(
        FakeRuns(), FakeSites(()), FakeScenarios((_definition(case),)),
        model_profiles=(EV_CHARGER_MODEL,), publication_profiles=(EV_PUBLICATION_PROFILE,),
        now=lambda: "2026-10-07T12:00:00Z",
        registered_bases=RegisteredLabBasis(ImportedSiteRegistry(
            FoundationService(store, DEVELOPMENT_TENANT_SLUG, lambda: NOW))),
    )
    run = setup.create_draft_run({
        "site_id": "EV-LAB-001", "foundation_version": 1, "scenario_id": f"ev-{case}", "scenario_version": 1,
        "interval": {"start_time": "2026-10-06T08:00:00Z", "end_time": CLOSE}, "timestep_minutes": 1,
        "seed": 20517, "model_profile": {"profile_id": "ev-charger", "profile_version": 1},
        "publication_profile": {"profile_id": "ev-publication", "profile_version": 1}, "run_inputs": [],
    })
    return replace(run, run_id=f"run-ev-{case}")


class _Inputs:
    """`EvInputs` over the real store, with each answer replaceable to simulate a missing or changed record."""

    def __init__(self, store):
        self.real = StoreEvInputs(store, SCENARIOS)
        self.revision = self.binding = self.definition = "real"

    def foundation_revision(self, tenant_id, site_record_id, revision_id):
        real = self.real.foundation_revision(tenant_id, site_record_id, revision_id)
        return real if self.revision == "real" else self.revision

    def binding_revision(self, tenant_id, site_record_id, binding_set_revision_id):
        real = self.real.binding_revision(tenant_id, site_record_id, binding_set_revision_id)
        return real if self.binding == "real" else self.binding

    def ev_scenario(self, scenario_id, version):
        real = self.real.ev_scenario(scenario_id, version)
        return real if self.definition == "real" else self.definition


class _Gateway:
    """Records each boundary group; admits every text."""

    def __init__(self):
        self.groups: list[tuple[str, list[str]]] = []
        self.released: list[str] = []

    def publish_in_boundary_order(self, run_id, basis, groups, final_instant):
        done = []
        for instant, texts in groups:
            self.groups.append((instant, list(texts)))
            done.append([{"outcome": "ADMITTED", "message_id": f"m{len(self.groups)}-{i}", "sequence": i}
                         for i, _ in enumerate(texts)])
        return done, None

    def release(self, run_id):
        self.released.append(run_id)
        raise GatewayUnavailable("the test gateway has no release process")

    def texts(self) -> list[str]:
        return [t for _, texts in self.groups for t in texts]


def _host(tmp_path, inputs, gateway):
    return HostLabExecution(
        artifacts=YamlExecutionArtifacts(tmp_path / "executions"), stages=JsonSourceStages(tmp_path / "stages"),
        gateway=gateway, schedules=JsonPublicationSchedules(tmp_path / "schedules"), ev_inputs=inputs,
    )


def _artifact_path(tmp_path, run):
    return tmp_path / "executions" / f"{run.run_id}.yaml"


def _no_schedule(tmp_path) -> bool:
    return not (tmp_path / "schedules").exists() or not any((tmp_path / "schedules").iterdir())


# --- A complete run, its schema-7 artifact and restart ------------------------------------------------------

def test_complete_run_executes_once_and_persists_one_schema_7_document(tmp_path, world) -> None:
    run = _draft(world, "complete")
    gateway = _Gateway()
    host = _host(tmp_path, _Inputs(world), gateway)

    draft = host.projection(run)
    assert (draft.status, draft.boundaries_completed, draft.content_digest) == ("NOT_STARTED", 0, None)
    assert draft.observation_series_digest == EMPTY_EV_SERIES_DIGEST and draft.notes == EV_NOTES
    for early in (lambda: host.step(run, boundaries=1, from_boundary=0), lambda: host.run_to_end(run)):
        with pytest.raises(LabControlRefused) as before:
            early()
        assert before.value.kind == "NOT_STARTED"

    projection = host.start(run)
    assert projection.status == "COMPLETED" and projection.failure is None
    assert (projection.boundaries_completed, projection.boundaries_total, projection.offset_minutes) == (61, 61, 60)
    assert (projection.interval_start_time, projection.simulation_time) == ("2026-10-06T08:00:00Z", CLOSE)
    assert projection.private_state == projection.observations == projection.signals == ()
    assert projection.content_digest == PINNED_COMPLETE_DIGEST
    assert projection.notes == EV_NOTES
    assert projection.reported_count == len(gateway.texts())  # the complete case holds nothing
    assert [g[0] for g in gateway.groups] == sorted(g[0] for g in gateway.groups)
    first = [parse_device_report_v2_text(t) for t in gateway.groups[0][1]]
    assert gateway.groups[0][0] == "2026-10-06T08:00:03Z"
    # The two initial 08:00 state reports, under the corrected seven-label map (q3 Q15 / q4 Q19).
    assert [(r.device_id, r.signal_id, r.source_time, r.value) for r in first] == [
        ("c1-connector-controller", "state", "2026-10-06T08:00:00Z", "AUTHORIZING"),
        ("c2-connector-controller", "state", "2026-10-06T08:00:00Z", "UNPLUGGED")]

    text = _artifact_path(tmp_path, run).read_text(encoding="utf-8")
    assert HISTORY_MARKER not in text
    documents = list(yaml.safe_load_all(text))
    assert len(documents) == 1
    document = documents[0]
    assert tuple(document) == EV_ARTIFACT_KEYS
    assert (document["artifact_schema_version"], document["execution_kind"]) == (7, "EV")
    basis = run.registered_basis
    assert (document["foundation_revision_id"], document["foundation_content_sha256"],
            document["binding_set_revision_id"], document["snapshot_sha256"]) == (
        basis.foundation_revision_id, basis.foundation_content_sha256, basis.binding_set_revision_id,
        basis.snapshot_sha256)
    assert [r["report_text"] for r in document["public_reports"]] == gateway.texts()
    assert all(tuple(r) == ("report_key", "report_text") for r in document["public_reports"])
    for private in ("session-1", "REQUEST_KW", "LATCH", "minute_records", "forcing"):
        assert private not in text

    # Restart: a fresh host reads COMPLETED from the artifact, never re-runs the pack or re-admits.
    admitted = len(gateway.texts())
    restarted = _host(tmp_path, None, gateway)
    assert restarted.projection(run) == projection
    assert restarted._execution_status(run) == "COMPLETED"
    assert restarted.history(run).source == "HISTORY_UNAVAILABLE"
    for refused in (lambda: restarted.step(run, boundaries=1, from_boundary=61),
                    lambda: restarted.run_to_end(run), lambda: restarted.start(run)):
        with pytest.raises(LabControlRefused) as terminal:
            refused()
        assert terminal.value.kind == "ALREADY_TERMINAL"
    assert len(gateway.texts()) == admitted

    # Commit: a COMPLETED run passes the readiness gate and reaches the gateway release.
    with pytest.raises(LabControlRefused) as commit:
        restarted.release_registered(run)
    assert commit.value.kind == "GATEWAY_RELEASE_UNAVAILABLE" and gateway.released == [run.run_id]


def test_the_late_end_is_pending_at_nine_and_released_once_at_nine_oh_five(tmp_path, world) -> None:
    run = _draft(world, "late-record")
    gateway = _Gateway()
    host = _host(tmp_path, _Inputs(world), gateway)
    projection = host.start(run)
    assert projection.status == "COMPLETED"
    assert projection.reported_count == len(gateway.texts()) + 1  # the held END is counted
    assert all(instant <= "2026-10-06T09:00:03Z" for instant, _ in gateway.groups)

    restarted = _host(tmp_path, None, gateway)
    assert restarted._execution_status(run) == "COMPLETED"
    schedule = restarted.publication_schedule(run)
    [held] = schedule.delayed
    assert held.state == "PENDING" and held.scheduled_release_at == RELEASE
    assert held.source_time == "2026-10-06T08:31:00Z"
    assert held.delay_event_id == ev_delay_event_id(held.report_key) and held.delay_event_id.startswith("ev-delay-")
    stored = yaml.safe_load(_artifact_path(tmp_path, run).read_text(encoding="utf-8"))
    assert {"report_key": held.report_key, "report_text": held.report_text} in stored["public_reports"]
    assert "ev-delay-" not in held.report_text

    answer = restarted.advance_publication(run, RELEASE)
    assert answer["publication_refused"] is None and answer["release_basis"] == "STORED_SCHEDULE_ONLY"
    instant, texts = gateway.groups[-1]
    assert instant == RELEASE and texts == [held.report_text]
    late = parse_device_report_v2_text(texts[0])
    assert (late.source_time, late.report_key, late.record_kind) == (
        "2026-10-06T08:31:00Z", held.report_key, "EV_SESSION_END")
    [released] = restarted.publication_schedule(run).delayed
    assert released.state == "RELEASED" and released.message_id is not None

    count = len(gateway.texts())
    again = _host(tmp_path, None, gateway).advance_publication(run, RELEASE)
    assert again["publication_refused"] is None and len(gateway.texts()) == count


# --- Refusals before Stage (q4 Q22/Q23) ------------------------------------------------------------------------

@pytest.mark.parametrize("damage", ["no_port", "revision_missing", "revision_changed", "binding_missing",
                                    "binding_bytes_changed", "binding_row_changed", "scenario_missing",
                                    "scenario_changed", "mapping_missing", "mapping_wrong_type",
                                    "store_unreadable"])
def test_unreconstructible_inputs_refuse_before_any_stage(tmp_path, world, damage) -> None:
    from assetops_backend.sites.foundation_content import content_digest

    run = _draft(world, "complete")
    inputs = _Inputs(world)
    basis = run.registered_basis
    real_revision = next(r for r in world.revisions(*_ids(world)) if str(r.id) == basis.foundation_revision_id)
    real_binding = next(b for b in world.binding_sets(*_ids(world)) if str(b.id) == basis.binding_set_revision_id)
    if damage == "no_port":
        inputs = None
    elif damage == "revision_missing":
        inputs.revision = None
    elif damage == "revision_changed":
        content = json.loads(json.dumps(real_revision.content))
        content["summary"] = "changed by test"
        inputs.revision = replace(real_revision, content=content, content_sha256=content_digest(content))
    elif damage == "binding_missing":
        inputs.binding = None
    elif damage == "binding_bytes_changed":
        inputs.binding = replace(real_binding, snapshot_canonical=real_binding.snapshot_canonical + b" ")
    elif damage == "binding_row_changed":
        rows = tuple(replace(b, signal_id="power") if b.signal_id == "requested-power" and
                     b.device_id.startswith("c1") else b for b in real_binding.bindings)
        inputs.binding = replace(real_binding, bindings=rows)
    elif damage == "scenario_missing":
        inputs.definition = None
    elif damage == "scenario_changed":
        inputs.definition = replace(_definition("fault"), scenario_id="ev-complete")
    elif damage == "mapping_missing":
        identity = run.deterministic_identity
        run = replace(run, deterministic_identity=replace(identity, signal_mappings=identity.signal_mappings[1:]))
    elif damage == "mapping_wrong_type":
        identity = run.deterministic_identity
        moved = tuple(replace(m, component_id="c1") if m.component_id == "site-meter-1" else m
                      for m in identity.signal_mappings)
        run = replace(run, deterministic_identity=replace(identity, signal_mappings=moved))
    else:
        class _Broken(_Inputs):
            def binding_revision(self, *args):
                raise OSError("store offline")
        inputs = _Broken(world)
    gateway = _Gateway()
    host = _host(tmp_path, inputs, gateway)
    with pytest.raises(LabControlRefused) as refused:
        host.start(run)
    assert refused.value.kind == "FROZEN_RUN_NOT_RECONSTRUCTIBLE"
    assert gateway.groups == [] and _no_schedule(tmp_path)
    assert host.projection(run).status == "NOT_STARTED"


def _ids(store):
    tenant = store.resolve_tenant(DEVELOPMENT_TENANT_SLUG)
    site = store.find_site(tenant.id, "EV-LAB-001")
    return tenant.id, site.id


def _content(world):
    return json.loads(json.dumps(world.revisions(*_ids(world))[0].content))


def test_the_frozen_foundation_maps_exactly_to_the_closed_parameters(world) -> None:
    parameters = ev_parameters(_content(world), window_start="2026-10-06T08:00:00Z", window_end=CLOSE)
    assert (parameters.site_limit_kw, parameters.charger_rating_kw, parameters.connector_rating_kw,
            parameters.base_load_kw) == (Fraction(80), Fraction(60), Fraction(60), Fraction(0))
    assert (str(parameters.enabled_from), str(parameters.enabled_to)) == ("08:00:00", "16:00:00")


def _property(content, component_id, key):
    component = next(c for c in content["components"] if c["component_id"] == component_id)
    return next(p for p in component["properties"] if p["property_key"] == key)


def _unequal(c):
    _property(c, "c2", "ev-connector-max-power")["value"] = 50.0


def _disabled(c):
    _property(c, "c1", "ev-connector-enabled")["value"] = "DISABLED"


def _base_load(c):
    next(x for x in c["components"] if x["component_id"] == "feed-1")["properties"].append(
        {"property_key": "ev-base-load", "value": 5.0, "unit": "kW", "source": "SITE", "source_version": 1})


def _missing_limit(c):
    next(x for x in c["components"] if x["component_id"] == "feed-1")["properties"] = []


def _schedule_differs(c):
    c["connector_enable_schedules"][1]["weekly"][0]["local_end"] = "15:00"


def _wednesday(c):
    for s in c["connector_enable_schedules"]:
        s["weekly"][0]["weekday"] = "WEDNESDAY"


def _other_zone(c):
    for s in c["connector_enable_schedules"]:
        s["time_zone"] = "Europe/Berlin"


def _negative(c):
    _property(c, "charger-1", "ev-charger-max-power")["value"] = -1.0


def _infinite(c):
    _property(c, "feed-1", "ev-site-import-limit")["value"] = float("inf")


@pytest.mark.parametrize("change", [_unequal, _disabled, _base_load, _missing_limit, _schedule_differs, _wednesday,
                                    _other_zone, _negative, _infinite])
def test_a_foundation_outside_the_closed_model_refuses(world, change) -> None:
    content = _content(world)
    change(content)
    with pytest.raises(FrozenRunNotReconstructible):
        ev_parameters(content, window_start="2026-10-06T08:00:00Z", window_end=CLOSE)


def test_tuesday_hours_are_never_applied_to_another_day(world) -> None:
    with pytest.raises(FrozenRunNotReconstructible, match="not within one TUESDAY"):
        ev_parameters(_content(world), window_start="2026-10-07T08:00:00Z", window_end="2026-10-07T09:00:00Z")


# --- Stage refusal, artifact damage and schedule loss -----------------------------------------------------------

def test_publication_refusal_persists_failed_and_cannot_commit(tmp_path, world) -> None:
    run = _draft(world, "complete")

    class _Refusing(_Gateway):
        def publish_in_boundary_order(self, run_id, basis, groups, final_instant):
            return [], RuntimeError("gateway refused")

    host = _host(tmp_path, _Inputs(world), _Refusing())
    projection = host.start(run)
    assert projection.status == "FAILED" and projection.failure.kind == "PUBLICATION_REFUSED"
    assert projection.content_digest == PINNED_COMPLETE_DIGEST
    restarted = _host(tmp_path, None, _Gateway())
    assert restarted._execution_status(run) == "FAILED"
    with pytest.raises(LabControlRefused) as again:
        restarted.start(run)
    assert again.value.kind == "ALREADY_TERMINAL"
    with pytest.raises(LabControlRefused) as commit:
        restarted.release_registered(run)
    assert commit.value.kind == "COMMIT_NOT_READY"


def _rewrite(path, change):
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    change(document)
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")


def _swap_text(d):
    d["public_reports"][0]["report_text"] = d["public_reports"][1]["report_text"]


def _drop_report(d):
    d["public_reports"].pop()


def _extra_key(d):
    d["world"] = "private"


def _missing_key(d):
    del d["public_reports"]


def _digest(d):
    d["content_digest"] = "not-a-digest"


def _foreign_revision(d):
    d["binding_set_revision_id"] = "00000000-0000-4000-8000-000000000000"


def _not_complete(d):
    d["boundaries_completed"] = 60


def _failure_mismatch(d):
    d["status"] = "FAILED"


def _report_key_order(d):
    d["public_reports"][0] = {"report_text": d["public_reports"][0]["report_text"],
                              "report_key": d["public_reports"][0]["report_key"]}


@pytest.mark.parametrize("damage", [_swap_text, _drop_report, _extra_key, _missing_key, _digest, _foreign_revision,
                                    _not_complete, _failure_mismatch, _report_key_order, "history", "garbage"])
def test_a_damaged_schema_7_artifact_reads_unreadable(tmp_path, world, damage) -> None:
    run = _draft(world, "complete")
    _host(tmp_path, _Inputs(world), _Gateway()).start(run)
    path = _artifact_path(tmp_path, run)
    if damage == "history":
        path.write_text(path.read_text(encoding="utf-8") + HISTORY_MARKER + "{}\n", encoding="utf-8")
    elif damage == "garbage":
        path.write_text("artifact_schema_version: 7\n: [\n", encoding="utf-8")
    else:
        _rewrite(path, damage)
    restarted = _host(tmp_path, None, _Gateway())
    projection = restarted.projection(run)
    assert projection.status == "ARTIFACT_UNREADABLE"
    assert projection.notes[0] == EV_NOTES[0] and len(projection.notes) == 2
    assert restarted._execution_status(run) == "ARTIFACT_UNREADABLE"
    with pytest.raises(LabControlRefused) as refused:
        restarted.start(run)
    assert refused.value.kind == "ARTIFACT_UNREADABLE"


def test_a_missing_or_mismatched_schedule_refuses_closed_after_restart(tmp_path, world) -> None:
    run = _draft(world, "late-record")
    gateway = _Gateway()
    _host(tmp_path, _Inputs(world), gateway).start(run)
    schedule_path = tmp_path / "schedules" / f"{run.run_id}.json"
    original = schedule_path.read_text(encoding="utf-8")

    document = json.loads(original)
    held = next(d for d in document["delayed"])
    held["report_text"] = held["report_text"].replace("08:31:00Z", "08:32:00Z")
    schedule_path.write_text(json.dumps(document), encoding="utf-8")
    count = len(gateway.texts())
    with pytest.raises(LabControlRefused) as mismatch:
        _host(tmp_path, None, gateway).advance_publication(run, RELEASE)
    assert mismatch.value.kind == "PUBLICATION_SCHEDULE_UNREADABLE" and len(gateway.texts()) == count

    document = json.loads(original)
    document["snapshot_sha256"] = "0" * 64
    schedule_path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(LabControlRefused) as foreign:
        _host(tmp_path, None, gateway).advance_publication(run, RELEASE)
    assert foreign.value.kind == "PUBLICATION_SCHEDULE_UNREADABLE"

    schedule_path.write_text("{not json", encoding="utf-8")
    with pytest.raises(LabControlRefused) as unreadable:
        _host(tmp_path, None, gateway).advance_publication(run, RELEASE)
    assert unreadable.value.kind == "PUBLICATION_SCHEDULE_UNREADABLE"

    schedule_path.unlink()
    restarted = _host(tmp_path, None, gateway)
    for read in (lambda: restarted.advance_publication(run, RELEASE), lambda: restarted.publication_schedule(run)):
        with pytest.raises(LabControlRefused) as missing:
            read()
        assert missing.value.kind == "PUBLICATION_SCHEDULE_MISSING"
    assert len(gateway.texts()) == count


def test_the_ev_delay_id_is_stable_and_distinct_from_cold() -> None:
    from cold_lab import delay_event_id

    key = "ev:some-report-key"
    assert ev_delay_event_id(key) == ev_delay_event_id(key)
    assert ev_delay_event_id(key).startswith("ev-delay-") and len(ev_delay_event_id(key)) == len("ev-delay-") + 64
    assert delay_event_id(key).startswith("cold-delay-")
    assert ev_delay_event_id(key)[len("ev-delay-"):] == delay_event_id(key)[len("cold-delay-"):]


# --- Dispatch by the exact EV pair --------------------------------------------------------------------------

def test_the_ev_pair_dispatches_to_ev_and_never_resolves_a_model_spec(world) -> None:
    from execution_adapter import execution_path, model_for

    run = _draft(world, "complete")
    assert execution_path(run) == "EV"
    with pytest.raises(FrozenRunNotReconstructible, match="EV pair"):
        model_for(run)


@pytest.mark.parametrize("model, publication", [
    (("ev-charger", 1), ("cold-publication", 1)),
    (("ev-charger", 2), ("ev-publication", 1)),
    (("minimal-fuel-tank", 1), ("ev-publication", 1)),
])
def test_a_half_ev_pair_is_refused(world, model, publication) -> None:
    from execution_adapter import execution_path

    run = _draft(world, "complete")
    identity = run.deterministic_identity
    profiles = replace(identity.profiles, model_profile_id=model[0], model_profile_version=model[1],
                       publication_profile_id=publication[0], publication_profile_version=publication[1])
    with pytest.raises(FrozenRunNotReconstructible):
        execution_path(replace(run, deterministic_identity=replace(identity, profiles=profiles)))
