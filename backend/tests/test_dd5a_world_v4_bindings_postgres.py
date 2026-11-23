"""DD5a unit 1 (D-DD.138): a world cold or EV conversion publishes v4 channel metadata, so the ledger accepts the
world's v4 envelopes; mini-grid conversions keep v3 (byte-equal digest to main).

Needs `ASSETOPS_TEST_DATABASE_URL`; run through `tools/heavy-slot.sh --db-lane`.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from test_dd1_onboarding_postgres import ON1, WORLD, _env, _run
    from test_s1_bindings_postgres import Clock, engine, store  # noqa: F401

    from assetops_backend.evidence.adapters.postgres_evidence_ledger import PostgresEvidenceLedger
    from assetops_backend.evidence.ledger import GatewayPrincipal
    from assetops_backend.evidence.ledger_service import BatchIngestionService
    from assetops_contracts.ingestion_batch_v2 import seal_batch_v2
    from assetops_contracts.source_envelope import canonical_json

    from assetops_backend.sites.binding_alignment import canonical_bytes
    from assetops_contracts.source_envelope_v3 import v3_message_id

RECEIVED = datetime(2026, 10, 13, 8, 0, tzinfo=timezone.utc)
#: The v3 binding keys main's conversion digest covers (`binding_alignment.binding_content` without v4 keys).
V3_KEYS = ("device_id", "signal_id", "source_id", "gateway_id", "asset_id", "role", "source_unit", "canonical_unit",
           "conversion")


def _snapshot(engine, code):
    with engine.connect() as c:
        body = bytes(c.execute(text(
            "SELECT r.snapshot_canonical FROM signal_binding_set_revision r JOIN site s ON s.id = r.site_id "
            "WHERE s.site_code = :c AND r.superseded_at IS NULL"), {"c": code}).scalar_one())
    return json.loads(body), hashlib.sha256(body).hexdigest()


def _row(doc, device, signal):
    return next(b for b in doc["bindings"] if b["device_id"] == device and b["signal_id"] == signal)


def _envelope(doc, b, seq, timing, payload):
    return canonical_json({
        "schema": {"id": "assetops.source-envelope", "version": 4},
        "message": {"message_id": v3_message_id(site_id=doc["site"]["site_id"], gateway_id=b["gateway_id"],
                                                source_id=b["source_id"], sequence_epoch="dd5a", sequence=seq),
                    "sequence_epoch": "dd5a", "sequence": seq},
        "source": {"site_id": doc["site"]["site_id"], "gateway_id": b["gateway_id"], "source_id": b["source_id"],
                   "device_id": b["device_id"], "signal_id": b["signal_id"]},
        "mapping": {"binding_set_id": doc["mapping"]["binding_set_id"], "version": doc["mapping"]["version"]},
        "timing": timing,
        "payload": {"session_id": None, "connector_id": None, **payload}})


def _measurement(measurement, value, unit, start, end, **ids):
    return ({"source_time": end, "published_at": end, "interval_start": start,
             "interval_end": end if measurement != "STATE_AT_INSTANT" else None},
            {"family": "MEASUREMENT", "measurement": measurement, "value": value, "unit": unit, "quality": "GOOD",
             "unavailable_reason": None, **ids})


def _submit(engine, doc, sha, b, texts):
    _, body = seal_batch_v2(
        site_id=doc["site"]["site_id"], gateway_id=b["gateway_id"], source_id=b["source_id"],
        source_mode=doc["gateway"]["mode"], foundation_version=doc["foundation"]["version"],
        foundation_valid_from=doc["foundation"]["valid_from"], binding_set_id=doc["mapping"]["binding_set_id"],
        binding_version=doc["mapping"]["version"], snapshot_sha256=sha, envelope_texts=texts)
    service = BatchIngestionService(PostgresEvidenceLedger(URL, test_decision_clock_override=Clock(RECEIVED)),
                                    Clock(RECEIVED))
    principal = GatewayPrincipal(tenant_id=UUID(doc["tenant_id"]), site_id=UUID(doc["site"]["site_id"]),
                                 gateway_id=UUID(doc["gateway"]["gateway_id"]), mode=doc["gateway"]["mode"])
    return [(d.decision, d.rejection and d.rejection.kind)
            for d in service.submit(principal, body.encode("utf-8")).receipt.dispositions]


def _metadata_rows(doc):
    return [b for b in doc["bindings"] if b.get("allowed_units") is not None]


def test_cold_thika_conversion_carries_v4_metadata_and_accepts_a_meter_and_an_event(
        store, engine, tmp_path, monkeypatch, capsys) -> None:  # noqa: F811
    _env(monkeypatch, tmp_path, "harvest-cold")
    code, _, err = _run(capsys, ON1 / "harvest-cold.onboarding.json", ("--bindings", str(WORLD)))
    assert code == 0, err
    doc, sha = _snapshot(engine, "COLD-THIKA")
    meter = _row(doc, "compressor-meter", "power")
    timing, payload = _measurement("INTERVAL_MEAN", "3.2", "kW", "2026-10-12T09:25:00Z", "2026-10-12T09:30:00Z")
    assert _submit(engine, doc, sha, meter, [_envelope(doc, meter, 1, timing, payload)]) == [("ACCEPTED", None)]
    door = _row(doc, "door-sensor", "event")
    event = {"family": "EVENT", "record_kind": "DOOR_OPEN", "outcome": "OPEN", "actor": "SENSOR",
             "component_id": _component(doc, door),
             "event_id": "dd5a-door-1", "correlation_id": "dd5a-door", "unit": None, "value": None,
             "quality": "GOOD"}
    t = "2026-10-12T09:31:00Z"
    timing = {"source_time": t, "published_at": t, "interval_start": None, "interval_end": None}
    assert _submit(engine, doc, sha, door, [_envelope(doc, door, 1, timing, event)]) == [("ACCEPTED", None)]
    assert len(_metadata_rows(doc)) == len(doc["bindings"])


def _component(doc, b):
    return b.get("asset_code") or b["device_id"]


def test_ev_kas_conversion_carries_v4_metadata_and_accepts_connector_energy_and_the_site_import(
        store, engine, tmp_path, monkeypatch, capsys) -> None:  # noqa: F811
    _env(monkeypatch, tmp_path, "metro-bus")
    code, _, err = _run(capsys, ON1 / "metro-bus.onboarding.json", ("--bindings", str(WORLD)))
    assert code == 0, err
    doc, sha = _snapshot(engine, "EV-KAS")
    assert len(_metadata_rows(doc)) == len(doc["bindings"])
    energy = _row(doc, "ch-k1-c1-connector-meter", "energy")
    timing, payload = _measurement("INTERVAL_DELTA", "1.25", "kWh", "2026-10-12T09:25:00Z", "2026-10-12T09:30:00Z",
                                   session_id="dd5a-session-1", connector_id="ch-k1-c1")
    assert _submit(engine, doc, sha, energy, [_envelope(doc, energy, 1, timing, payload)]) == [("ACCEPTED", None)]
    site = _row(doc, "site-meter", "import")
    timing, payload = _measurement("INTERVAL_MEAN", "40.5", "kW", "2026-10-12T09:25:00Z", "2026-10-12T09:30:00Z")
    assert _submit(engine, doc, sha, site, [_envelope(doc, site, 1, timing, payload)]) == [("ACCEPTED", None)]


def test_mini_grid_conversions_stay_v3_with_kobo_digest_equal_to_main(
        store, engine, tmp_path, monkeypatch, capsys) -> None:  # noqa: F811
    _env(monkeypatch, tmp_path, "lakeside-power")
    code, _, err = _run(capsys, ON1 / "lakeside-power.onboarding.json", ("--bindings", str(WORLD)))
    assert code == 0, err
    doc, _ = _snapshot(engine, "KOBO-001")
    assert _metadata_rows(doc) == []
    with engine.connect() as c:
        digest = c.execute(text(
            "SELECT r.bindings_sha256 FROM signal_binding_set_revision r JOIN site s ON s.id = r.site_id "
            "WHERE s.site_code = 'KOBO-001' AND r.superseded_at IS NULL")).scalar_one()
    # Row ids are fresh UUIDs per run, so main's digest is recomputed from these rows the way main forms it: the
    # v3 content only (a measured main value differs run to run and cannot be pinned).
    rows = sorted(({k: b[k] for k in V3_KEYS} for b in doc["bindings"]), key=lambda r: (r["device_id"], r["signal_id"]))
    assert digest == hashlib.sha256(canonical_bytes({"role_set": doc["mapping"]["role_set"] if "role_set" in doc["mapping"]
                                                     else doc["role_set"], "bindings": rows})).hexdigest()
