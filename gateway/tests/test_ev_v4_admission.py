"""W2-05b commit 3: the gateway's v4 branch over the closed `simulator-lab-gateway-ev/1` table
(`D-2026-10-18-w2-05-buildspec` commit 3 and the Run 8 correlation handoff).

The gateway imports contracts only, so reports here are built by hand, one per EV tuple, with the producer's
`ev-` identifier and `ev:` report-key helpers. The whole six-case public series is admitted in
`host/tests/test_ev_publication.py`.
"""

from __future__ import annotations

import re
from dataclasses import replace

import pytest

from assetops_contracts.gateway_report import (
    DeviceReportV2,
    cold_report_key,
    device_report_v2_text,
    ev_event_id,
    ev_report_key,
)
from assetops_contracts.source_envelope_v4 import (
    V4_CHANNEL_MAPPINGS,
    V4_EV_CHANNEL_MAPPINGS,
    parse_canonical_envelope_v4_text,
)
from assetops_gateway.service import GatewayReader, GatewayService

from conftest import GATEWAY, SRC_GEN, snapshot

SCENARIO = "e" * 64
RUN = "lab-run-ev-1"
AT = "2026-10-06T08:05:00Z"
START = "2026-10-06T08:00:00Z"
SESSION = "ev-" + "5" * 64
#: The 05a `ev-lab-001-bindings.json` state labels (`sites/binding_roles.py` `EV_CONNECTOR_STATES`).
ENUM_LABELS = ("AVAILABLE", "PLUGGED", "AUTHORIZING", "CHARGING", "FAULTED", "DISABLED")
_V4_ID = re.compile(r"[A-Za-z0-9._-]+")


def _unit(device: str, signal: str) -> str:
    entry = V4_EV_CHANNEL_MAPPINGS[(device, signal)]
    if entry.family == "EVENT":
        return "event"
    return entry.allowed_units[0]


def _row(device: str, signal: str, *, role: str | None = None) -> dict:
    entry = V4_EV_CHANNEL_MAPPINGS[(device, signal)]
    unit = _unit(device, signal)
    conversion = {"kind": "IDENTITY", "parameters": {}}
    if signal == "state":
        conversion = {"kind": "ENUM", "parameters": {"map": {label: label for label in ENUM_LABELS}}}
    row = {
        "binding_revision_id": f"ev-{device}-{signal}", "device_id": device, "signal_id": signal,
        "source_id": SRC_GEN, "gateway_id": GATEWAY, "asset_id": None, "role": role or entry.role,
        "source_unit": unit, "canonical_unit": unit, "conversion": conversion,
    }
    row.update(entry.metadata())
    return row


def _activate(gateway: GatewayService, rows: list[dict] | None = None) -> str:
    rows = rows if rows is not None else [_row(d, s) for d, s in sorted(V4_EV_CHANNEL_MAPPINGS)]
    text, claimed = snapshot(rows=rows)
    gateway.activate(text, claimed)
    return claimed.snapshot_sha256


def _measurement(device: str, signal: str, value: str, *, session: str | None = None,
                 connector: str | None = None) -> DeviceReportV2:
    entry = V4_EV_CHANNEL_MAPPINGS[(device, signal)]
    interval = None if entry.measurement == "STATE_AT_INSTANT" else START
    return DeviceReportV2(
        report_key=ev_report_key(scenario_sha256=SCENARIO, device_id=device, signal_id=signal, source_time=AT,
                                 record_kind=None, event_id=None, interval_start=interval),
        device_id=device, signal_id=signal, source_time=AT, family="MEASUREMENT", measurement=entry.measurement,
        interval_start=interval, interval_end=None if interval is None else AT, value=value,
        unit=_unit(device, signal), quality="GOOD", unavailable_reason=None, record_kind=None, event_id=None,
        correlation_id=None, component_id=None, actor=None, outcome=None, session_id=session,
        connector_id=connector,
    )


def _event(device: str, kind: str, outcome: str, connector: str, *, ordinal: int = 1,
           session: str | None = SESSION) -> DeviceReportV2:
    signal = "session-event" if kind.startswith("EV_SESSION") else "fault-event"
    event_id = ev_event_id(scenario_sha256=SCENARIO, device_id=device, signal_id=signal, transition_ordinal=ordinal)
    return DeviceReportV2(
        report_key=ev_report_key(scenario_sha256=SCENARIO, device_id=device, signal_id=signal, source_time=AT,
                                 record_kind=kind, event_id=event_id, interval_start=None),
        device_id=device, signal_id=signal, source_time=AT, family="EVENT", measurement=None, interval_start=None,
        interval_end=None, value=None, unit=None, quality="GOOD", unavailable_reason=None, record_kind=kind,
        event_id=event_id, correlation_id=session, component_id=connector, actor="CONTROLLER", outcome=outcome,
        session_id=session, connector_id=connector,
    )


def _one_per_tuple() -> list[DeviceReportV2]:
    out: list[DeviceReportV2] = []
    for c in ("c1", "c2"):
        out += [
            _event(f"{c}-charger-controller", "EV_SESSION_START", "STARTED", c),
            _event(f"{c}-connector-controller", "EV_CONNECTOR_FAULT", "FAULTED", c),
            _measurement(f"{c}-connector-controller", "state", "CHARGING"),
            _measurement(f"{c}-connector-controller", "requested-power", "60"),
            _measurement(f"{c}-connector-controller", "allocated-limit", "60"),
            _measurement(f"{c}-connector-meter", "energy", "5", session=SESSION, connector=c),
            _measurement(f"{c}-connector-meter", "power", "60"),
        ]
    out.append(_measurement("site-meter", "import", "60"))
    return out


def _stage(db_path) -> list:
    with GatewayReader(db_path) as reader:
        return list(reader.run_stage(RUN).envelopes)


def test_every_ev_tuple_admits_through_the_v4_branch(gateway: GatewayService, db_path) -> None:
    sha = _activate(gateway)
    reports = _one_per_tuple()
    assert {(r.device_id, r.signal_id) for r in reports} == set(V4_EV_CHANNEL_MAPPINGS)
    admitted = [gateway.admit(device_report_v2_text(r), snapshot_sha256=sha, lab_run_ref=RUN) for r in reports]
    assert [a.outcome for a in admitted] == ["ADMITTED"] * 15
    assert [a.sequence for a in admitted] == list(range(1, 16))
    envelopes = {e.sequence: parse_canonical_envelope_v4_text(e.envelope_text) for e in _stage(db_path)}
    for admission, r in zip(admitted, reports):
        envelope = envelopes[admission.sequence]
        assert (envelope.device_id, envelope.signal_id, envelope.source_id) == (r.device_id, r.signal_id, SRC_GEN)
        assert (envelope.session_id, envelope.connector_id) == (r.session_id, r.connector_id)
        if envelope.family == "MEASUREMENT" and envelope.measurement != "INTERVAL_DELTA":
            assert (envelope.session_id, envelope.connector_id) == (None, None)
        for value in (envelope.event_id, envelope.correlation_id, envelope.session_id):
            assert value is None or _V4_ID.fullmatch(value)


def test_ev_identifiers_and_report_keys() -> None:
    event_id = ev_event_id(scenario_sha256=SCENARIO, device_id="c1-charger-controller",
                           signal_id="session-event", transition_ordinal=2)
    assert re.fullmatch(r"ev-[0-9a-f]{64}", event_id) and ":" not in event_id
    key = ev_report_key(scenario_sha256=SCENARIO, device_id="c1-connector-meter", signal_id="energy",
                        source_time=AT, record_kind=None, event_id=None, interval_start=START)
    assert re.fullmatch(r"ev:[0-9a-f]{64}", key)
    assert key == ev_report_key(scenario_sha256=SCENARIO, device_id="c1-connector-meter", signal_id="energy",
                                source_time=AT, record_kind=None, event_id=None, interval_start=START)
    # The same identity inputs in the cold namespace give a different key: the namespaces never collide.
    assert key[3:] == cold_report_key(scenario_sha256=SCENARIO, device_id="c1-connector-meter",
                                      signal_id="energy", source_time=AT, record_kind=None, event_id=None,
                                      interval_start=START)[5:]


def test_identical_retransmission_preserves_key_and_allocates_nothing(gateway: GatewayService, db_path) -> None:
    sha = _activate(gateway)
    text = device_report_v2_text(_event("c1-charger-controller", "EV_SESSION_END", "COMPLETED", "c1"))
    first = gateway.admit(text, snapshot_sha256=sha, lab_run_ref=RUN)
    again = gateway.admit(text, snapshot_sha256=sha, lab_run_ref=RUN)
    assert (again.outcome, again.message_id, again.sequence) == ("ALREADY_ADMITTED", first.message_id, 1)
    assert len(_stage(db_path)) == 1


@pytest.mark.parametrize("field", ["session_id", "connector_id"])
@pytest.mark.parametrize("channel", [("c1-connector-meter", "power"), ("c1-connector-controller", "requested-power"),
                                     ("c1-connector-controller", "allocated-limit"), ("site-meter", "import")])
def test_either_nonnull_id_on_a_mean_is_held(gateway: GatewayService, channel, field) -> None:
    sha = _activate(gateway)
    report = replace(_measurement(*channel, "60"), **{field: "c1" if field == "connector_id" else SESSION})
    held = gateway.admit(device_report_v2_text(report), snapshot_sha256=sha, lab_run_ref=RUN)
    assert (held.outcome, held.kind) == ("HELD", "CORRELATION_INVALID")


def test_wrong_tuple_role_and_correlation_are_held(gateway: GatewayService) -> None:
    rows = [_row(d, s) for d, s in sorted(V4_EV_CHANNEL_MAPPINGS) if (d, s) != ("c2-connector-meter", "power")]
    rows.append(_row("c2-connector-meter", "power") | {"allowed_units": ["kWh"]})
    sha = _activate(gateway, rows)
    mismatched = gateway.admit(device_report_v2_text(_measurement("c2-connector-meter", "power", "1")),
                               snapshot_sha256=sha, lab_run_ref=RUN)
    assert (mismatched.outcome, mismatched.kind, mismatched.field) == ("HELD", "MAPPING_INCOMPATIBLE", "mapping")
    unbound = gateway.admit(device_report_v2_text(replace(_measurement("c1-connector-meter", "power", "1"),
                                                          device_id="charger-1-meter")),
                            snapshot_sha256=sha, lab_run_ref=RUN)
    assert unbound.outcome == "HELD"
    wrong_correlation = gateway.admit(device_report_v2_text(replace(
        _event("c1-charger-controller", "EV_SESSION_START", "STARTED", "c1"), correlation_id="ev-other")),
        snapshot_sha256=sha, lab_run_ref=RUN)
    assert (wrong_correlation.outcome, wrong_correlation.kind) == ("HELD", "CORRELATION_INVALID")
    energy_without_session = gateway.admit(device_report_v2_text(
        _measurement("c1-connector-meter", "energy", "5", connector="c1")), snapshot_sha256=sha, lab_run_ref=RUN)
    assert (energy_without_session.outcome, energy_without_session.kind) == ("HELD", "CORRELATION_INVALID")
    wrong_kind = gateway.admit(device_report_v2_text(
        _event("c1-connector-controller", "EV_SESSION_START", "STARTED", "c1") ), snapshot_sha256=sha,
        lab_run_ref=RUN)
    assert wrong_kind.outcome == "HELD"


def test_unplugged_state_is_not_an_enum_label_pending_q15(gateway: GatewayService) -> None:
    """Pending ruling Q15: the pack's public `UNPLUGGED` is not a label of the 05a state ENUM map."""
    sha = _activate(gateway)
    held = gateway.admit(device_report_v2_text(_measurement("c1-connector-controller", "state", "UNPLUGGED")),
                         snapshot_sha256=sha, lab_run_ref=RUN)
    assert (held.outcome, held.kind) == ("HELD", "INVALID_ENUM")


def test_unsuffixed_compatibility_tuples_are_not_in_the_ev_table() -> None:
    assert ("charger-controller", "session-event") in V4_CHANNEL_MAPPINGS
    assert ("charger-controller", "session-event") not in V4_EV_CHANNEL_MAPPINGS
    assert ("connector-controller", "fault-event") not in V4_EV_CHANNEL_MAPPINGS
    assert len(V4_EV_CHANNEL_MAPPINGS) == 15
