"""S2-01c phase 1: R1 state-safe seal refusals, GatewayDiagnosticsV1 and local counters."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import subprocess
import sys
import textwrap
from datetime import timedelta
from pathlib import Path

import pytest
from conftest import EPOCH, GATEWAY, PROVISIONING, SITE, SRC_BMS, SRC_GEN, SRC_PV, report, snapshot

from assetops_contracts.gateway_diagnostics import (
    DiagnosticConfig,
    DiagnosticRejected,
    parse_canonical_gateway_diagnostics_v1_text,
    parse_diagnostic_config_text,
)
from assetops_gateway.service import GatewayReader, GatewayRefused, GatewayService
from assetops_gateway.snapshot import Provisioning

VECTORS = json.loads(
    (Path(__file__).resolve().parents[2] / "contract-fixtures" / "gateway-diagnostics-v1-vectors.json").read_text(
        encoding="utf-8"
    )
)


def _rows(db_path: Path, sql: str, params: tuple = ()) -> list[tuple]:
    with sqlite3.connect(db_path) as db:
        return db.execute(sql, params).fetchall()


def _canonical(document: object) -> str:
    return json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


# --- R1: a seal refusal belongs to its (source, epoch, snapshot, state) group ------


def _mixed_groups(gateway: GatewayService, sha: str) -> set[str]:
    """Two BMS groups that differ only by outbox state; returns the READY ids."""
    for minute in ("00", "15"):
        gateway.admit(report(at=f"2026-10-01T08:{minute}:00Z", key=f"s-{minute}"), snapshot_sha256=sha, lab_run_ref="run-1")
    ready = set()
    for minute in ("30", "45"):
        admission = gateway.admit(
            report(at=f"2026-10-01T08:{minute}:00Z", key=f"r-{minute}"),
            snapshot_sha256=sha,
            lab_run_ref="run-1",
            initial_state="READY",
        )
        ready.add(admission.message_id)
    return ready


def _refusing(ids: set[str], real):
    from assetops_contracts.ingestion_batch_v2 import BatchRejected
    from assetops_contracts.source_envelope_v3 import parse_canonical_envelope_v3_text

    def seal(**kwargs):
        if {parse_canonical_envelope_v3_text(t).message_id for t in kwargs["envelope_texts"]} & ids:
            raise BatchRejected("TOO_LARGE", "batch", "forced for the test")
        return real(**kwargs)

    return seal


@pytest.mark.parametrize("refused_state", ["READY", "STAGED", "BOTH"])
def test_r1_a_sibling_group_sealing_never_erases_another_states_refusal(
    gateway, active: str, db_path: Path, clock, monkeypatch, refused_state: str
) -> None:
    import assetops_gateway.service as service_module

    ready = _mixed_groups(gateway, active)
    staged = {m for (m,) in _rows(db_path, "SELECT message_id FROM envelope_outbox WHERE state='STAGED'")}
    refused = {"READY": ready, "STAGED": staged, "BOTH": ready | staged}[refused_state]
    states = ["READY", "STAGED"] if refused_state == "BOTH" else [refused_state]
    real = service_module.seal_batch_v2
    monkeypatch.setattr(service_module, "seal_batch_v2", _refusing(refused, real))
    with pytest.raises(GatewayRefused) as error:
        gateway.seal()
    assert error.value.kind == "SEAL_REFUSED"
    # Groups seal in (source, epoch, snapshot, state) order, so a refused READY
    # group is recorded before its STAGED sibling seals in the same pass: the
    # pass that would have erased a state-blind refusal.
    with GatewayReader(db_path) as reader:
        assert sorted(r.outbox_state for r in reader.run_stage("run-1").seal_refusals) == states
    with pytest.raises(GatewayRefused):
        gateway.seal()  # a second pass: the sibling is sealed, the refusal must stay
    gateway.close()
    monkeypatch.setattr(service_module, "seal_batch_v2", real)

    with GatewayReader(db_path) as reader:  # after a restart
        stage = reader.run_stage("run-1")
    assert sorted((r.outbox_state, r.kind, r.message_id in refused) for r in stage.seal_refusals) == [
        (state, "TOO_LARGE", True) for state in states
    ]
    sealed_ids = {m for b in stage.batches for m in b.message_ids}
    assert sealed_ids == (staged | ready) - refused  # partial progress for the sibling
    assert {e.message_id for e in stage.envelopes if e.batch_id is None} == refused
    sealed_before = _rows(db_path, "SELECT batch_id, payload_text, sha256 FROM upload_batch")

    reopened = GatewayService(db_path, clock=clock)
    try:
        assert len(reopened.seal()) == len(states)  # each refused group's own success clears it
    finally:
        reopened.close()
    with GatewayReader(db_path) as reader:
        stage = reader.run_stage("run-1")
    assert stage.seal_refusals == ()
    assert all(e.batch_id is not None for e in stage.envelopes)
    after = _rows(db_path, "SELECT batch_id, payload_text, sha256 FROM upload_batch")
    assert set(sealed_before) <= set(after)  # earlier bytes and ids unchanged


def test_r1_migration_keeps_a_version_2_refusal_with_its_groups_state(db_path: Path, clock) -> None:
    from assetops_gateway.ledger import MIGRATION_1, MIGRATION_2, _statements

    db = sqlite3.connect(db_path)
    for script in (MIGRATION_1, MIGRATION_2):
        for statement in _statements(script):
            db.execute(statement)
    db.execute("INSERT INTO schema_migration VALUES (1, '2026-10-01T00:00:00Z'), (2, '2026-10-02T00:00:00Z')")
    db.execute(
        "INSERT INTO envelope_outbox (message_id, gateway_id, source_id, sequence_epoch, sequence, source_time, "
        "snapshot_sha256, envelope_text, sha256, state, created_at) "
        "VALUES ('m-1','g','src','e',1,'2026-10-01T08:00:00Z','snap','{}','h','READY','2026-10-01T08:00:00Z')"
    )
    db.execute(
        "INSERT INTO seal_refusal (source_id, sequence_epoch, snapshot_sha256, message_id, kind, field, detail, "
        "first_seen_at, last_seen_at, seen_count) VALUES ('src','e','snap','m-1','TOO_LARGE','batch','x',"
        "'2026-10-01T09:00:00Z','2026-10-01T09:05:00Z',2)"
    )
    db.commit()
    db.close()
    GatewayService(db_path, clock=clock).close()
    assert _rows(db_path, "SELECT source_id, outbox_state, message_id, seen_count FROM seal_refusal") == [
        ("src", "READY", "m-1", 2)
    ]
    assert _rows(db_path, "SELECT envelope_text, sha256 FROM envelope_outbox") == [("{}", "h")]


# --- the wire: canonical vectors and refusals ----------------------------------------


def test_diagnostic_vectors_parse_and_their_digest_excludes_itself() -> None:
    assert VECTORS["diagnostics"][0]["payload_sha256"] == (
        "e7fde117ad15fb79661af44a0a04e1dbd0d0790bb82416ffa0059844f815f787"
    )
    for vector in VECTORS["diagnostics"]:
        parsed = parse_canonical_gateway_diagnostics_v1_text(vector["text"])
        assert parsed.payload_sha256 == vector["payload_sha256"]
        body = json.loads(vector["text"])
        body.pop("payload_sha256")
        assert hashlib.sha256(_canonical(body).encode("utf-8")).hexdigest() == vector["payload_sha256"]
        assert hashlib.sha256(vector["text"].encode("utf-8")).hexdigest() == vector["text_sha256"]
    assert VECTORS["default_config"]["text"] == DiagnosticConfig().text()
    assert parse_diagnostic_config_text(VECTORS["default_config"]["text"]) == DiagnosticConfig()


def _resealed(mutate) -> str:
    document = json.loads(VECTORS["diagnostics"][0]["text"])
    mutate(document)
    document.pop("payload_sha256", None)
    document["payload_sha256"] = hashlib.sha256(_canonical(document).encode("utf-8")).hexdigest()
    return _canonical(document)


@pytest.mark.parametrize(
    ("text", "kind"),
    [
        (lambda: _resealed(lambda d: d.__setitem__("lab_run_id", "run-1")), "UNKNOWN_FIELD"),
        (lambda: _resealed(lambda d: d.__setitem__("received_at", "2026-10-08T12:00:01Z")), "UNKNOWN_FIELD"),
        (lambda: _resealed(lambda d: d.__setitem__("scheduled_release_at", "2026-10-08T12:00:01Z")), "UNKNOWN_FIELD"),
        (lambda: _resealed(lambda d: d["schema"].__setitem__("version", 2)), "SCHEMA_UNSUPPORTED"),
        (lambda: _resealed(lambda d: d.__setitem__("disk_pressure", "FULL")), "INVALID_FIELD"),
        (lambda: _resealed(lambda d: d.__setitem__("oldest_queue_age_seconds", None)), "INCONSISTENT"),
        (lambda: _resealed(lambda d: d.__setitem__("queue_count", -1)), "INVALID_FIELD"),
        (lambda: _resealed(lambda d: d.__setitem__("diagnostic_sequence", 0)), "INVALID_FIELD"),
        (lambda: _resealed(lambda d: d.__setitem__("observed_at", "2026-10-08 12:00:00")), "INVALID_TIMING"),
        (
            lambda: _resealed(
                lambda d: d["last_device_contact_by_source"].__setitem__(SRC_BMS, "2026-10-08T12:00:01Z")
            ),
            "INVALID_TIMING",
        ),
        (
            lambda: _resealed(
                lambda d: d.__setitem__(
                    "last_device_contact_by_source", {f"s-{n}": None for n in range(257)}
                )
            ),
            "TOO_LARGE",
        ),
        (lambda: VECTORS["diagnostics"][0]["text"].replace('"queue_count":3', '"queue_count":4'), "DIGEST_MISMATCH"),
        (lambda: VECTORS["diagnostics"][0]["text"] + " ", "NOT_CANONICAL"),
        (lambda: VECTORS["diagnostics"][0]["text"].replace('"queue_count":3', '"queue_count":3.0'), "MALFORMED_TEXT"),
    ],
)
def test_diagnostic_refusals(text, kind: str) -> None:
    with pytest.raises(DiagnosticRejected) as error:
        parse_canonical_gateway_diagnostics_v1_text(text())
    assert error.value.kind == kind


# --- the ledger: allocation, retry, restart, immutability ------------------------------


def test_emission_is_one_identity_per_cadence_slot_and_survives_restart(
    gateway, active: str, db_path: Path, clock
) -> None:
    first = gateway.emit_diagnostic()
    assert (first.diagnostic_sequence, first.state, first.sequence_epoch) == (1, "READY", EPOCH)
    clock.now += timedelta(seconds=30)  # still inside the 60 s slot
    assert gateway.emit_diagnostic() == first
    gateway.close()
    reopened = GatewayService(db_path, clock=clock)
    try:
        assert reopened.emit_diagnostic() == first  # restart: same identity and bytes
        clock.now += timedelta(seconds=60)
        second = reopened.emit_diagnostic()
        assert second.diagnostic_sequence == 2 and second.payload_text != first.payload_text
        clock.now -= timedelta(seconds=120)
        with pytest.raises(GatewayRefused) as error:
            reopened.emit_diagnostic()
        assert error.value.kind == "CLOCK_BEHIND"
    finally:
        reopened.close()
    parsed = parse_canonical_gateway_diagnostics_v1_text(first.payload_text)
    assert (parsed.site_id, parsed.gateway_id, parsed.payload_sha256) == (SITE, GATEWAY, first.sha256)
    rows = _rows(db_path, "SELECT state, server_received_at, last_attempt_at FROM diagnostic_outbox")
    assert rows == [("READY", None, None)] * 2  # no ACKED, no local receipt
    assert _rows(db_path, "SELECT COUNT(*) FROM acknowledgement") == [(0,)]


def test_stored_diagnostic_bytes_and_identity_cannot_change(gateway, active: str, db_path: Path) -> None:
    gateway.emit_diagnostic()
    with sqlite3.connect(db_path) as db:
        for statement in (
            "UPDATE diagnostic_outbox SET payload_text='{}'",
            "UPDATE diagnostic_outbox SET sha256='0'",
            "UPDATE diagnostic_outbox SET diagnostic_sequence=9",
            "DELETE FROM diagnostic_outbox",
            "UPDATE diagnostic_config SET config_text='{}'",
        ):
            with pytest.raises(sqlite3.IntegrityError):
                db.execute(statement)
        with pytest.raises(sqlite3.IntegrityError):  # same identity, different bytes
            db.execute(
                "INSERT INTO diagnostic_outbox (gateway_id, sequence_epoch, diagnostic_sequence, cadence_slot, "
                "payload_text, sha256, state, observed_at) VALUES (?,?,1,0,'{}','0','READY','2026-10-08T12:00:00Z')",
                (GATEWAY, EPOCH),
            )


def test_diagnostic_configuration_is_frozen_and_returned(gateway, db_path: Path) -> None:
    gateway.provision(PROVISIONING, sequence_epoch=EPOCH)  # identical repeat
    with pytest.raises(GatewayRefused) as error:
        gateway.provision(PROVISIONING, sequence_epoch=EPOCH, diagnostics=DiagnosticConfig(emission_cadence_seconds=30))
    assert error.value.kind == "DIAGNOSTIC_CONFIG_FIXED"
    config = gateway.local_diagnostics()["config"]
    assert (config["emission_cadence_seconds"], config["max_sources"], config["max_payload_bytes"]) == (60, 256, 65536)
    assert config["text"] == DiagnosticConfig().text()


_CRASH = textwrap.dedent(
    """
    import os, sys
    from datetime import datetime, timezone
    sys.path.insert(0, {tests!r})
    from conftest import PROVISIONING, EPOCH
    from assetops_gateway.service import GatewayService

    point = sys.argv[1]
    def fault(at):
        if at == point:
            os._exit(17)
    service = GatewayService({db!r}, clock=lambda: datetime(2026, 10, 8, 12, tzinfo=timezone.utc), fault=fault)
    service.provision(PROVISIONING, sequence_epoch=EPOCH)
    service.emit_diagnostic()
    os._exit(0)
    """
)


@pytest.mark.parametrize(("point", "rows"), [("after_diagnostic_sequence_read", 0), ("after_diagnostic_commit", 1)])
def test_a_kill_around_emission_leaves_nothing_or_the_same_bytes(db_path: Path, clock, point: str, rows: int) -> None:
    script = _CRASH.format(tests=str(Path(__file__).parent), db=str(db_path))
    assert subprocess.run([sys.executable, "-c", script, point], timeout=60).returncode == 17
    before = _rows(db_path, "SELECT diagnostic_sequence, payload_text, sha256 FROM diagnostic_outbox")
    assert len(before) == rows
    with GatewayService(db_path, clock=clock) as service:
        again = service.emit_diagnostic()
    assert again.diagnostic_sequence == 1
    if rows:
        assert (again.diagnostic_sequence, again.payload_text, again.sha256) == before[0]


# --- truthful counters ----------------------------------------------------------------


def test_counters_derive_from_ledger_rows(gateway, active: str, db_path: Path, clock, monkeypatch) -> None:
    import assetops_gateway.service as service_module

    first = gateway.local_diagnostics()
    assert first["queue"]["queue_count"] == 0 and first["queue"]["oldest_queue_age_seconds"] is None
    assert [c["last_contact_at"] for c in first["source_contacts"]] == [None, None, None]  # unknown, not healthy
    assert first["clock_offset"] == {"value_ms": None, "provenance": None, "observed_at": None}

    pv = gateway.admit(
        report(device="pv-inverter", signal="ac_power", unit="kW", value="3.5", key="pv-1"), snapshot_sha256=active
    )
    gateway.seal()
    gateway.admit(report(key="bms-1"), snapshot_sha256=active)
    gateway.admit(report(key="bms-2", at="2026-10-01T08:15:00Z"), snapshot_sha256=active)
    gateway.admit(report(key="bad", unit="degF"), snapshot_sha256=active)  # held: UNIT_INCOMPATIBLE
    # held, but not a mapping error: same key, different content
    conflicting = gateway.admit(report(key="bms-1", value="99"), snapshot_sha256=active)
    assert conflicting.kind == "CONFLICTING_REPORT"
    real = service_module.seal_batch_v2
    bms = {m for (m,) in _rows(db_path, "SELECT message_id FROM envelope_outbox WHERE source_id=?", (SRC_BMS,))}
    monkeypatch.setattr(service_module, "seal_batch_v2", _refusing(bms, real))
    with pytest.raises(GatewayRefused):
        gateway.seal()
    clock.now += timedelta(seconds=90)
    read = gateway.local_diagnostics()
    assert read["queue"] == {
        "queue_count": 3,
        "oldest_queued_at": "2026-10-08T12:00:00Z",
        "oldest_queue_age_seconds": 90,
        "sealed_pending_batches": 1,
        "sealed_pending_envelopes": 1,
        "unbatched_envelopes": 2,
        "held_reports": 2,
        "active_seal_refusals": 1,
        "dead_letter_envelopes": 0,
    }
    assert read["mapping_error_count"] == 1
    contacts = {c["source_id"]: c for c in read["source_contacts"]}
    assert contacts[SRC_GEN]["last_contact_at"] is None
    # the gateway's own clock when it heard the report, not the report's source time
    assert contacts[SRC_BMS] == {
        "source_id": SRC_BMS,
        "last_contact_at": "2026-10-08T12:00:00Z",
        "provenance": "OBSERVED_SIMULATED_REPORT",
    }
    assert pv.outcome == "ADMITTED"
    row = gateway.emit_diagnostic()
    wire = parse_canonical_gateway_diagnostics_v1_text(row.payload_text)
    assert (wire.queue_count, wire.oldest_queue_age_seconds, wire.mapping_error_count) == (3, 90, 1)
    assert dict(wire.last_device_contact_by_source)[SRC_GEN] is None
    assert wire.clock_offset_ms is None
    assert read["upload"] == "PENDING" and read["acquisition"] == "ACCEPTING"


def test_stop_pressure_refuses_acquisition_before_a_sequence_and_keeps_bytes(
    gateway, active: str, db_path: Path
) -> None:
    gateway.admit(report(key="before"), snapshot_sha256=active, lab_run_ref="run-1")
    gateway.seal()
    kept = _rows(db_path, "SELECT message_id, envelope_text FROM envelope_outbox") + _rows(
        db_path, "SELECT batch_id, payload_text FROM upload_batch"
    )
    sequence = _rows(db_path, "SELECT * FROM sequence_state")
    gateway.inject_disk_pressure("STOP")
    for call in (
        lambda: gateway.admit(report(key="after", at="2026-10-01T08:15:00Z"), snapshot_sha256=active),
        lambda: gateway.admit_texts([report(key="after-2")], snapshot_sha256=active),
    ):
        with pytest.raises(GatewayRefused) as error:
            call()
        assert error.value.kind == "DISK_PRESSURE_STOP"
    assert _rows(db_path, "SELECT * FROM sequence_state") == sequence
    assert _rows(db_path, "SELECT COUNT(*) FROM mapping_hold") == [(0,)]
    assert (
        _rows(db_path, "SELECT message_id, envelope_text FROM envelope_outbox")
        + _rows(db_path, "SELECT batch_id, payload_text FROM upload_batch")
        == kept
    )
    read = gateway.local_diagnostics()
    assert read["disk_pressure"]["level"] == "STOP" and read["disk_pressure"]["provenance"] == "INJECTED_FAULT_FIXTURE"
    assert read["acquisition"] == "REFUSED_DISK_PRESSURE_STOP"
    assert parse_canonical_gateway_diagnostics_v1_text(gateway.emit_diagnostic().payload_text).disk_pressure == "STOP"
    gateway.inject_disk_pressure(None)
    assert gateway.admit(report(key="after", at="2026-10-01T08:15:00Z"), snapshot_sha256=active).sequence == 2


@pytest.mark.parametrize(("free", "level"), [(2**31, "OK"), (2**29, "WARN"), (2**27, "STOP")])
def test_measured_pressure_uses_the_frozen_triggers(db_path: Path, clock, free: int, level: str) -> None:
    with GatewayService(db_path, clock=clock, disk_free=lambda: free) as service:
        service.provision(PROVISIONING, sequence_epoch=EPOCH)
        disk = service.local_diagnostics()["disk_pressure"]
    assert (disk["level"], disk["provenance"], disk["free_bytes"]) == (level, "MEASURED", free)


def test_an_unmeasurable_disk_fails_closed(db_path: Path, clock) -> None:
    def broken() -> int:
        raise OSError("no such volume")

    with GatewayService(db_path, clock=clock, disk_free=broken) as service:
        service.provision(PROVISIONING, sequence_epoch=EPOCH)
        assert service.local_diagnostics()["disk_pressure"]["provenance"] == "UNMEASURABLE"
        with pytest.raises(GatewayRefused):
            service.admit(report(key="x"), snapshot_sha256="0" * 64)


def test_clock_offset_is_unknown_unless_injected_and_labelled(gateway, active: str) -> None:
    gateway.inject_clock_offset(-1500)
    clock_offset = gateway.local_diagnostics()["clock_offset"]
    assert (clock_offset["value_ms"], clock_offset["provenance"]) == (-1500, "INJECTED_FAULT_FIXTURE")
    assert parse_canonical_gateway_diagnostics_v1_text(gateway.emit_diagnostic().payload_text).clock_offset_ms == -1500
    gateway.inject_clock_offset(None)
    assert gateway.local_diagnostics()["clock_offset"]["value_ms"] is None


def test_a_live_gateway_takes_no_fault_injection(tmp_path: Path, clock) -> None:
    live = Provisioning(
        tenant_id=PROVISIONING.tenant_id,
        site_id=SITE,
        gateway_id=GATEWAY,
        source_mode="LIVE",
        permitted_source_ids=frozenset({SRC_BMS, SRC_PV}),
    )
    with GatewayService(tmp_path / "live.sqlite3", clock=clock) as service:
        service.provision(live, sequence_epoch=EPOCH)
        for inject in (lambda: service.inject_disk_pressure("STOP"), lambda: service.inject_clock_offset(5)):
            with pytest.raises(GatewayRefused) as error:
                inject()
            assert error.value.kind == "NOT_SIMULATED"
