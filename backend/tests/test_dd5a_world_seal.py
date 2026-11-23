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
}


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
