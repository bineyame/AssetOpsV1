"""W2-05b commit 3: the EV public transform, its v2 reports, gateway admission and the registered Stage branch
(`D-2026-10-18-w2-05-buildspec` commit 3).

The six shipped `ev-scenario/1` documents run through the pure pack and `ev-publication/1`/`ev-observation/1`
against the 05a binding rows; every report reparses, carries every schema-2 key, and is offered to an
in-process `GatewayService` activated with the 05a 15-tuple binding. Host Lab dispatch, input re-read and the
schema-7 artifact are commit 4.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from assetops_backend.scenarios.ev_parsing import parse_ev_scenario_document
from assetops_contracts.gateway_report import ev_event_id, parse_device_report_v2_text
from assetops_contracts.source_envelope_v4 import V4_EV_CHANNEL_MAPPINGS, parse_canonical_envelope_v4_text
from assetops_gateway.service import GatewayReader, GatewayService
from assetops_gateway.snapshot import ClaimedReferences, Provisioning
from assetops_simulator.observation.transform import ev_decimal_text, ev_rounded_kwh
from assetops_simulator.packs.ev_charger import DEFAULT_PARAMETERS
from ev_publication import EvBindingRefused, ev_channels, ev_execution, ev_reports, ev_series_digest
from lab_execution import HostLabExecution, YamlExecutionArtifacts
from publication_schedule import PENDING, JsonPublicationSchedules
from source_stages import JsonSourceStages

ROOT = Path(__file__).resolve().parents[2]
BINDINGS = json.loads((ROOT / "backend" / "conversions" / "ev-lab-001-bindings.json").read_text("utf-8"))["bindings"]
CASES = ("complete", "interrupted", "fault", "missing-meter", "late-record", "contradictory")
SCHEMA_2_KEYS = {"schema", "report_key", "device_id", "signal_id", "source_time", "family", "measurement", "interval_start",
                 "interval_end", "value", "unit", "quality", "unavailable_reason", "record_kind", "event_id",
                 "correlation_id", "component_id", "actor", "outcome", "session_id", "connector_id"}


def _definition(case: str):
    path = ROOT / "config" / "scenarios" / f"ev-{case}.yaml"
    return parse_ev_scenario_document(yaml.safe_load(path.read_text("utf-8")), source=str(path))


def _series(case: str):
    d = _definition(case)
    return d, ev_reports(d, ev_channels(BINDINGS), ev_execution(d, DEFAULT_PARAMETERS))


def _docs(reports) -> list[dict]:
    return [json.loads(r.report_text) for r in reports]


def _events(reports) -> list[tuple[str, str, str]]:
    return [(d["source_time"][11:16], d["device_id"], d["record_kind"]) for d in _docs(reports) if d["family"] == "EVENT"]


def _energy(reports, connector: str = "c1") -> list[tuple[str, str, str]]:
    return [(d["interval_start"][11:16], d["interval_end"][11:16], d["value"]) for d in _docs(reports)
            if (d["device_id"], d["signal_id"]) == (f"{connector}-connector-meter", "energy")]


# --- the binding channel table --------------------------------------------------------------------------------


def test_channels_come_from_the_05a_binding() -> None:
    channels = ev_channels(BINDINGS)
    assert len(channels) == 15
    assert channels[("c1", "state")].device_id == "c1-connector-controller"
    assert channels[("c2", "energy")].connector_id == "c2"
    assert channels[(None, "import")].connector_id is None
    assert {(c.device_id, c.signal_id) for c in channels.values()} == set(V4_EV_CHANNEL_MAPPINGS)


@pytest.mark.parametrize("damage", ["foreign", "role", "missing", "asset", "twice"])
def test_a_binding_outside_the_closed_table_refuses(damage) -> None:
    rows = [dict(r) for r in BINDINGS]
    if damage == "foreign":
        rows[0]["device_id"] = "charger-controller"
    elif damage == "role":
        rows[2]["role"] = "ev_connector_fault"
    elif damage == "missing":
        rows.pop()
    elif damage == "asset":
        rows[5]["asset_code"] = "charger-1"
    else:
        rows.append(dict(rows[0]))
    with pytest.raises(EvBindingRefused):
        ev_channels(rows)


# --- the public series ----------------------------------------------------------------------------------------


@pytest.mark.parametrize("case", CASES)
def test_every_report_is_a_complete_schema_2_report(case) -> None:
    _, reports = _series(case)
    for r in reports:
        document = json.loads(r.report_text)
        assert set(document) == SCHEMA_2_KEYS
        assert parse_device_report_v2_text(r.report_text).report_key == r.report_key
        assert r.report_key.startswith("ev:")
        if document["family"] == "MEASUREMENT" and document["measurement"] != "INTERVAL_DELTA":
            assert (document["session_id"], document["connector_id"]) == (None, None)
    states = [d for d in _docs(reports) if d["signal_id"] == "state"]
    assert len(states) == 122  # one per connector per boundary, 61 boundaries
    assert {d["value"] for d in states} <= {"UNPLUGGED", "PLUGGED", "AUTHORIZING", "CHARGING", "FAULTED"}
    # Deterministic: a second execution gives the same bytes.
    assert ev_series_digest(_series(case)[1]) == ev_series_digest(reports)


def test_complete_session_splits_at_start_and_end() -> None:
    d, reports = _series("complete")
    assert _events(reports) == [("08:01", "c1-charger-controller", "EV_SESSION_START"),
                                ("08:31", "c1-charger-controller", "EV_SESSION_END")]
    energy = _energy(reports)
    assert energy[0] == ("08:01", "08:05", "4") and energy[-1] == ("08:30", "08:31", "1")
    assert sum(Decimal(v) for _, _, v in energy) == Decimal(30)
    assert _energy(reports, "c2") == []  # no zero deltas outside a session
    power = [(x["interval_start"][11:16], x["interval_end"][11:16], x["value"]) for x in _docs(reports)
             if (x["device_id"], x["signal_id"]) == ("c1-connector-meter", "power")]
    assert power[:2] == [("08:00", "08:01", "0"), ("08:01", "08:05", "60")]
    start = next(x for x in _docs(reports) if x["record_kind"] == "EV_SESSION_START")
    assert start["session_id"] == start["correlation_id"] and start["connector_id"] == start["component_id"] == "c1"
    assert start["actor"] == "CONTROLLER" and start["outcome"] == "STARTED"
    assert start["event_id"] == ev_event_id(scenario_sha256=d.scenario_sha256, device_id="c1-charger-controller",
                                            signal_id="session-event", transition_ordinal=1)
    assert all(r.published_at[17:] == "03Z" for r in reports)  # source time + 3 s


def test_interrupted_and_fault_cases() -> None:
    _, interrupted = _series("interrupted")
    assert _events(interrupted) == [("08:01", "c1-charger-controller", "EV_SESSION_START"),
                                    ("08:16", "c1-charger-controller", "EV_SESSION_ABORT"),
                                    ("08:16", "c1-connector-controller", "EV_CONNECTOR_FAULT")]
    assert sum(Decimal(v) for _, _, v in _energy(interrupted)) == Decimal(15)
    _, fault = _series("fault")
    assert _events(fault) == [("08:00", "c1-connector-controller", "EV_CONNECTOR_FAULT"),
                              ("08:05", "c1-connector-controller", "EV_CONNECTOR_CLEAR"),
                              ("08:11", "c2-charger-controller", "EV_SESSION_START"),
                              ("08:21", "c2-charger-controller", "EV_SESSION_END")]
    assert _energy(fault) == [] and sum(Decimal(v) for _, _, v in _energy(fault, "c2")) == Decimal(10)
    c1_states = {x["source_time"][11:16]: x["value"] for x in _docs(fault)
                 if x["device_id"] == "c1-connector-controller" and x["signal_id"] == "state"}
    assert (c1_states["08:00"], c1_states["08:04"], c1_states["08:05"]) == ("FAULTED", "FAULTED", "PLUGGED")


def test_missing_meter_drops_one_report_after_building_it() -> None:
    _, complete = _series("complete")
    _, missing = _series("missing-meter")
    assert [e for e in _energy(complete) if e not in _energy(missing)] == [("08:10", "08:15", "5")]
    assert sum(Decimal(v) for _, _, v in _energy(missing)) == Decimal(25)
    assert len(missing) == len(complete) - 1


def test_late_record_holds_the_end_with_its_identity() -> None:
    _, complete = _series("complete")
    _, late = _series("late-record")
    (held,) = [r for r in late if r.held]
    end = next(r for r in complete if json.loads(r.report_text)["record_kind"] == "EV_SESSION_END")
    assert (held.source_time, held.published_at) == ("2026-10-06T08:31:00Z", "2026-10-06T09:05:00Z")
    assert json.loads(held.report_text)["record_kind"] == "EV_SESSION_END"
    d = _definition("late-record")
    assert json.loads(held.report_text)["event_id"] == ev_event_id(
        scenario_sha256=d.scenario_sha256, device_id="c1-charger-controller", signal_id="session-event",
        transition_ordinal=2)
    # Holding changes publication only: the held text is the complete case's END re-keyed by scenario SHA alone.
    unheld = {k: v for k, v in json.loads(end.report_text).items() if k not in ("report_key", "event_id",
                                                                                 "correlation_id", "session_id")}
    assert unheld == {k: v for k, v in json.loads(held.report_text).items()
                      if k not in ("report_key", "event_id", "correlation_id", "session_id")}


def test_contradictory_adds_a_distinct_end_before_the_genuine_one() -> None:
    d, reports = _series("contradictory")
    ends = [x for x in _docs(reports) if x["record_kind"] == "EV_SESSION_END"]
    assert [e["source_time"][11:16] for e in ends] == ["08:30", "08:31"]
    assert ends[0]["session_id"] == ends[1]["session_id"] and ends[0]["event_id"] != ends[1]["event_id"]
    assert ends[0]["event_id"] == ev_event_id(scenario_sha256=d.scenario_sha256, device_id="c1-charger-controller",
                                              signal_id="session-event", transition_ordinal=3)
    assert ends[1]["event_id"] == ev_event_id(scenario_sha256=d.scenario_sha256, device_id="c1-charger-controller",
                                              signal_id="session-event", transition_ordinal=2)
    assert ends[0]["quality"] == "GOOD" and ends[0]["outcome"] == "COMPLETED"


def test_rounding_is_half_even_per_boundary_and_decimals_are_exact() -> None:
    assert ev_rounded_kwh(Fraction(1, 2000)) == Decimal("0.000")
    assert ev_rounded_kwh(Fraction(3, 2000)) == Decimal("0.002")
    assert ev_decimal_text(Fraction(5)) == "5" and ev_decimal_text(Fraction(1, 4)) == "0.25"
    with pytest.raises(ValueError):
        ev_decimal_text(Fraction(1, 3))


# --- gateway admission ------------------------------------------------------------------------------------------

TENANT = "00000000-0000-4000-8000-000000000001"
SITE = "11111111-1111-4111-8111-111111111111"
GATEWAY = "22222222-2222-4222-8222-222222222222"
SOURCE = "33333333-3333-4333-8333-333333333333"


def _canonical(document: object) -> str:
    return json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _gateway(tmp_path: Path, *, as_published: bool = False) -> tuple[GatewayService, str]:
    """An in-process gateway activated with the 05a rows. Unless `as_published`, the energy rows' 05a
    `IDENTITY_KWH` conversion is offered as `IDENTITY`, because the gateway snapshot reader supports only
    IDENTITY/ENUM (pending ruling Q17, `.agent/W2-05b-pending-rulings.md`)."""
    from datetime import datetime, timezone

    service = GatewayService(tmp_path / "gateway.sqlite3", clock=lambda: datetime(2026, 10, 8, tzinfo=timezone.utc))
    service.provision(Provisioning(tenant_id=TENANT, site_id=SITE, gateway_id=GATEWAY, source_mode="SIMULATED",
                                   permitted_source_ids=frozenset({SOURCE})), sequence_epoch="epoch-1")
    rows = []
    for b in BINDINGS:
        row = {"binding_revision_id": "ev-rev-1", "device_id": b["device_id"], "signal_id": b["signal_id"],
               "source_id": SOURCE, "gateway_id": GATEWAY, "asset_id": None, "role": b["role"],
               "source_unit": b["source_unit"], "canonical_unit": b["canonical_unit"], "conversion": b["conversion"]}
        if not as_published and b["conversion"]["kind"] == "IDENTITY_KWH":
            row["conversion"] = {"kind": "IDENTITY", "parameters": {}}
        row.update(V4_EV_CHANNEL_MAPPINGS[(b["device_id"], b["signal_id"])].metadata())
        rows.append(row)
    rows.sort(key=lambda r: (r["device_id"], r["signal_id"]))
    content = [{k: v for k, v in r.items() if k != "binding_revision_id"} for r in rows]
    window = {"valid_from": "2026-10-01T00:00:00Z", "valid_to": None}
    document = {
        "schema": "assetops.acquisition-snapshot/1", "tenant_id": TENANT,
        "site": {"site_id": SITE, "site_code": "EV-LAB-001"},
        "gateway": {"gateway_id": GATEWAY, "gateway_external_id": "GW-EV-LAB-01", "mode": "SIMULATED"},
        "foundation": {"revision_id": "f-ev-1", "version": 1, "content_sha256": "a" * 64, **window},
        "mapping": {"binding_set_id": "bs-ev", "binding_set_revision_id": "ev-rev-1", "version": 1,
                    "role_set": "ev-roles-1", **window,
                    "bindings_sha256": hashlib.sha256(_canonical({"role_set": "ev-roles-1", "bindings": content})
                                                      .encode("utf-8")).hexdigest()},
        "sources": [{"source_id": SOURCE, "source_external_id": "ext-ev"}],
        "bindings": rows,
    }
    text = _canonical(document)
    claimed = ClaimedReferences(snapshot_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
                                foundation_revision_id="f-ev-1", foundation_version=1, binding_set_id="bs-ev",
                                binding_set_revision_id="ev-rev-1", binding_set_version=1)
    service.activate(text, claimed)
    return service, claimed.snapshot_sha256


def test_the_published_energy_conversion_is_refused_at_activation_pending_q17(tmp_path) -> None:
    from assetops_gateway.snapshot import SnapshotRefused

    with pytest.raises(SnapshotRefused) as refused:
        _gateway(tmp_path, as_published=True)
    assert refused.value.kind == "UNSUPPORTED_CONVERSION"


@pytest.mark.parametrize("case", CASES)
def test_the_whole_series_admits_except_the_pending_unplugged_state(tmp_path, case) -> None:
    """Every report admits through the v4 branch except connector state `UNPLUGGED`, which the 05a ENUM map
    does not label (pending ruling Q15, `.agent/W2-05b-pending-rulings.md`)."""
    _, reports = _series(case)
    gateway, sha = _gateway(tmp_path)
    outcomes = Counter()
    for r in reports:
        admission = gateway.admit(r.report_text, snapshot_sha256=sha, lab_run_ref="lab-run-ev")
        document = json.loads(r.report_text)
        if document["signal_id"] == "state" and document["value"] == "UNPLUGGED":
            assert (admission.outcome, admission.kind) == ("HELD", "INVALID_ENUM")
        else:
            assert admission.outcome == "ADMITTED", (document, admission)
        outcomes[admission.outcome] += 1
    assert outcomes["ADMITTED"] > 0
    with GatewayReader(tmp_path / "gateway.sqlite3") as reader:
        envelopes = [parse_canonical_envelope_v4_text(e.envelope_text) for e in reader.run_stage("lab-run-ev").envelopes]
    assert len(envelopes) == outcomes["ADMITTED"]
    assert {e.source_id for e in envelopes} == {SOURCE}


# --- the registered Stage branch ------------------------------------------------------------------------------


class _Gateway:
    def __init__(self, refusal: Exception | None = None):
        self.groups: list[tuple[str, list[str]]] = []
        self.refusal = refusal

    def publish_in_boundary_order(self, run_id, basis, groups, final_instant):
        if self.refusal is not None:
            return [], self.refusal
        done = []
        for instant, texts in groups:
            self.groups.append((instant, list(texts)))
            done.append([{"outcome": "ADMITTED", "message_id": f"m-{instant}-{i}", "sequence": i}
                         for i, _ in enumerate(texts)])
        return done, None


def _host(tmp_path: Path, gateway) -> HostLabExecution:
    return HostLabExecution(
        artifacts=YamlExecutionArtifacts(tmp_path / "executions"), stages=JsonSourceStages(tmp_path / "stages"),
        gateway=gateway, schedules=JsonPublicationSchedules(tmp_path / "schedules"),
    )


def _run():
    return SimpleNamespace(
        run_id="lab-run-ev-late", registered_basis=SimpleNamespace(snapshot_sha256="s" * 64),
        deterministic_identity=SimpleNamespace(interval=SimpleNamespace(end_time="2026-10-06T09:00:00Z")),
    )


def test_stage_publishes_in_boundary_order_and_holds_the_late_end(tmp_path) -> None:
    _, reports = _series("late-record")
    gateway = _Gateway()
    host = _host(tmp_path, gateway)
    assert host._stage_registered_virtual_ev(_run(), reports) is None
    instants = [instant for instant, _ in gateway.groups]
    assert instants == sorted(instants) and instants[-1] == "2026-10-06T09:00:03Z"
    staged = [t for _, texts in gateway.groups for t in texts]
    assert staged == [r.report_text for r in reports if not r.held]
    schedule = JsonPublicationSchedules(tmp_path / "schedules").read("lab-run-ev-late")
    (delayed,) = schedule.delayed
    (held,) = [r for r in reports if r.held]
    assert (delayed.report_key, delayed.report_text, delayed.source_time) == (held.report_key, held.report_text,
                                                                              "2026-10-06T08:31:00Z")
    assert (delayed.scheduled_release_at, delayed.state) == ("2026-10-06T09:05:00Z", PENDING)
    # A second Stage of the same run refuses rather than publishing twice.
    assert "already exists" in host._stage_registered_virtual_ev(_run(), reports)


def test_stage_refusal_is_returned_for_publication_refused(tmp_path) -> None:
    _, reports = _series("complete")
    refused = _host(tmp_path, _Gateway(RuntimeError("INVALID_ENUM at ordinal 1")))._stage_registered_virtual_ev(
        _run(), reports)
    assert refused is not None and "INVALID_ENUM" in refused
    assert "no gateway" in _host(tmp_path / "none", None)._stage_registered_virtual_ev(_run(), reports)
