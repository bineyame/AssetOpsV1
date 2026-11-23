"""DD5a unit 2 (D-DD.139, D-DD.91): `evidence/world_seal.seal_readings` mirrors the gateway's envelopes and Batch V2
sealing (the gateway parity is `host/tests/test_dd5a_world_seal_parity.py`; the backend may not import the
gateway), splits a source-day at 256 envelopes and runs one sequence per source over the span. Pure; no database."""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone

import pytest

from assetops_backend.evidence import world_seal
from assetops_backend.evidence.world_seal import SealContext, seal_readings
from assetops_contracts.ingestion_batch_v2 import MAX_BATCH_ENVELOPES, parse_canonical_batch_v2_text

SITE = "11111111-1111-4111-8111-111111111111"
GATEWAY = "22222222-2222-4222-8222-222222222222"
SET = "33333333-3333-4333-8333-333333333333"
SHA = "a" * 64
FOUNDATION_DIGEST = "b" * 64
SOURCES = {"meter": "44444444-4444-4444-8444-444444444444", "door": "55555555-5555-4555-8555-555555555555",
           "ev": "66666666-6666-4666-8666-666666666666"}
CHANNELS = {
    ("generator-meter", "output-power"): ("meter", "generator_power"),
    ("chamber-probe", "temperature"): ("meter", "chamber_temperature"),
    ("door-sensor", "event"): ("door", "door_event"),
    ("ch-k1-c1-connector-meter", "energy"): ("ev", "ev_connector_energy"),
    ("ch-k1-c1-connector-controller", "power"): ("ev", "ev_power"),
    ("ch-k1-c1-charger-controller", "session-event"): ("ev", "ev_session_event"),
    ("ch-k1-c1-connector-controller", "fault-event"): ("ev", "ev_connector_fault"),
}
#: The pack's id for one session (DD4b's writer, `scoped_session_id`): carried, never formed at sealing (D-DD.161).
PACK_SESSION = "ev-" + "c" * 64


def _context(**change) -> SealContext:
    bindings = {k: {"device_id": k[0], "signal_id": k[1], "source_id": SOURCES[s], "gateway_id": GATEWAY, "role": r}
                for k, (s, r) in CHANNELS.items()}
    base = dict(site_code="COLD-X", site_id=SITE, gateway_id=GATEWAY, source_mode="SIMULATED", foundation_version=1,
                foundation_valid_from="2026-06-30T21:00:00Z", binding_set_id=SET, binding_version=1,
                snapshot_sha256=SHA, foundation_digest=FOUNDATION_DIGEST, v4=True, bindings=bindings)
    return SealContext(**{**base, **change})


def _only_envelope(batches) -> str:
    (batch,) = batches
    (text,) = json.loads(batch.text)["envelopes"]
    return text


def _day(rows, day=date(2026, 10, 12)):
    return (day, rows)


def _five_minute_day(day: date) -> list[dict]:
    midnight = datetime(day.year, day.month, day.day, tzinfo=timezone(timedelta(hours=3)))
    return [{"source_id": "chamber-probe", "signal_id": "temperature",
             "start": (midnight + timedelta(minutes=5 * i)).isoformat(),
             "end": (midnight + timedelta(minutes=5 * i)).isoformat(), "value": "4.000", "unit": "degC"}
            for i in range(288)]


def test_a_288_row_source_day_gives_two_batches_and_sequences_run_across_days() -> None:
    days = [date(2026, 10, 12), date(2026, 10, 13)]
    batches = seal_readings(_context(), [(d, _five_minute_day(d)) for d in days])
    assert [b.name for b in batches] == [
        f"COLD-X.{SOURCES['meter']}.2026-10-12.1.batch.json", f"COLD-X.{SOURCES['meter']}.2026-10-12.2.batch.json",
        f"COLD-X.{SOURCES['meter']}.2026-10-13.1.batch.json", f"COLD-X.{SOURCES['meter']}.2026-10-13.2.batch.json"]
    assert [b.count for b in batches] == [MAX_BATCH_ENVELOPES, 32, MAX_BATCH_ENVELOPES, 32]
    sequences = [json.loads(t)["message"]["sequence"] for b in batches for t in json.loads(b.text)["envelopes"]]
    assert sequences == list(range(1, 577))
    ids = [json.loads(t)["message"]["message_id"] for b in batches for t in json.loads(b.text)["envelopes"]]
    assert len(set(ids)) == len(ids)
    for b in batches:
        assert len(parse_canonical_batch_v2_text(b.text).envelopes) == b.count


def test_an_unbound_channel_refuses() -> None:
    row = {"source_id": "ghost", "signal_id": "x", "start": "2026-10-12T09:30:00+03:00",
           "end": "2026-10-12T09:30:00+03:00", "value": "1", "unit": "kW"}
    with pytest.raises(world_seal.WorldSealRefused) as raised:
        seal_readings(_context(), [_day([row])])
    assert raised.value.code == "WORLD_TELEMETRY_UNRESOLVED"


def test_a_millesimal_reading_seals_in_canonical_spelling() -> None:
    assert [world_seal._value(v) for v in ("4.000", "12.500", "0.000", "-1.250", "100", "ON", None)] == [
        "4", "12.5", "0", "-1.25", "100", "ON", None]


# --- D-DD.161: one id per EV session, the pack's ---------------------------------------------------------------------

def _session_event(**change) -> dict:
    event = {"record_kind": "EV_SESSION_START", "outcome": "STARTED", "actor": "CONTROLLER", "component_id": "ch-k1-c1",
             "ordinal": 2, "correlation": None, "session_id": PACK_SESSION, "connector_id": "ch-k1-c1"}
    return {"source_id": "ch-k1-c1-charger-controller", "signal_id": "session-event",
            "start": "2026-10-12T22:05:00+03:00", "end": "2026-10-12T22:05:00+03:00", "value": None, "unit": "event",
            "event": {**event, **change}}


def _energy(session=True) -> dict:
    row = {"source_id": "ch-k1-c1-connector-meter", "signal_id": "energy", "start": "2026-10-12T22:05:00+03:00",
           "end": "2026-10-12T22:10:00+03:00", "value": "4.000", "unit": "kWh"}
    if session:
        row["session"] = {"session_id": PACK_SESSION, "connector_id": "ch-k1-c1"}
    return row


def _payload(text: str) -> dict:
    return json.loads(text)["payload"]


def test_ev_session_event_and_in_session_energy_carry_the_pack_session_id() -> None:
    (batch,) = seal_readings(_context(), [_day([_session_event(), _energy()])])
    event, energy = (_payload(t) for t in json.loads(batch.text)["envelopes"])
    assert event["session_id"] == event["correlation_id"] == energy["session_id"] == PACK_SESSION
    assert event["connector_id"] == energy["connector_id"] == "ch-k1-c1"
    assert energy["value"] == "4"


def test_ev_session_id_is_withdrawn_from_contracts() -> None:
    from assetops_contracts import gateway_report

    assert not hasattr(gateway_report, "ev_session_id")


def test_an_in_session_mean_claims_no_session() -> None:
    row = {"source_id": "ch-k1-c1-connector-controller", "signal_id": "power", "start": "2026-10-12T22:05:00+03:00",
           "end": "2026-10-12T22:10:00+03:00", "value": "30.000", "unit": "kW",
           "session": {"session_id": PACK_SESSION, "connector_id": "ch-k1-c1"}}
    payload = _payload(_only_envelope(seal_readings(_context(), [_day([row])])))
    assert payload["session_id"] is None and payload["connector_id"] is None


def test_an_ev_event_without_a_session_forms_cold_ids_over_its_correlation() -> None:
    from assetops_contracts.gateway_report import cold_correlation_id

    row = _session_event(record_kind="EV_CONNECTOR_FAULT", outcome="FAULTED", correlation=["fault", 1])
    row["event"].pop("session_id"), row["event"].pop("connector_id")
    row.update(source_id="ch-k1-c1-connector-controller", signal_id="fault-event")
    payload = _payload(_only_envelope(seal_readings(_context(), [_day([row])])))
    assert payload["correlation_id"] == cold_correlation_id(scenario_sha256=FOUNDATION_DIGEST,
                                                            correlation_key=("fault", 1))
    assert payload["session_id"] is None and payload["connector_id"] == "ch-k1-c1"


@pytest.mark.parametrize("row", [
    _session_event(session_id=None, connector_id=None, correlation=None),
    _energy(session=False),
], ids=["event", "energy"])
def test_an_ev_record_with_neither_session_nor_correlation_refuses(row) -> None:
    if "event" in row:
        row["event"] = {k: v for k, v in row["event"].items() if v is not None or k == "correlation"}
    with pytest.raises(world_seal.WorldSealRefused) as raised:
        seal_readings(_context(), [_day([row])])
    assert raised.value.code == "WORLD_SEAL_EV_UNCORRELATED"


def test_a_sealed_value_equals_its_reading_and_is_canonical() -> None:
    from decimal import Decimal

    for text in ("4.000", "0.000", "-0.000", "1250.500"):
        out = world_seal._value(text)
        assert Decimal(out) == Decimal(text)
