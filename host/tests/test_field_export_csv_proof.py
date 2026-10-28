"""TEL-06a: the illustrative generic interval CSV collector, end to end through a real gateway process.

The pinned `assetops-generic-interval-csv/1` fixture (illustrative, defined by
AssetOps) -> `CsvCollector` in process -> a real `python -m assetops_gateway
serve` over its authenticated IPC channel -> `FakeCentral` over real TLS. The
gateway, activation and central come from the TEL-04 `Bench` (ruling M Q3); no
emulator and no poller run. The value oracle is built from the daytime JSONL,
not from the CSV.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import field_bench  # noqa: E402
import test_field_modbus_tcp_proof as tel4  # noqa: E402

from assetops_contracts.observation import quantize_half_even  # noqa: E402
from assetops_gateway.ipc import GatewayLink  # noqa: E402

from assetops_field.export_csv import CsvCollector, CsvRefused  # noqa: E402
from assetops_field.modbus_poller import new_session_ref  # noqa: E402
from assetops_field.profile import load_profile  # noqa: E402
from assetops_field.publish import GatewayPublisher  # noqa: E402

PROFILE_PATH = ROOT / "field" / "profiles" / "generic-interval-csv-illustrative-1.json"
FIXTURE = ROOT / "contract-fixtures" / "telemetry" / "generic-interval-csv-v1" / "kobo-window.csv"
RESOLUTION = Fraction("0.001")
CELLS = 196


def _oracle(profile) -> tuple[dict[tuple[str, str, str], Fraction | None], dict[tuple[str, str, str], Fraction]]:
    """(device, signal, source_time) -> the rounded REPORTED value, or None for a blank cell (ruling M Q2)."""
    signals = {(row.device_id, row.signal_id) for row in profile.rows}
    expected: dict[tuple[str, str, str], Fraction | None] = {}
    raw: dict[tuple[str, str, str], Fraction] = {}
    for line in tel4.JSONL.read_text(encoding="utf-8").splitlines():
        document = json.loads(line)
        if (document["device_id"], document["signal_id"]) not in signals:
            continue
        key = (document["device_id"], document["signal_id"], document["source_sample_time"])
        if document["outcome"] == "REPORTED":
            raw[key] = Fraction(document["reported_value"])
            expected[key] = quantize_half_even(raw[key], RESOLUTION)
        else:
            assert document["outcome"] in ("NO_PRECEDING_INTERVAL", "NO_VALUE_AT_BOUNDARY"), document
            expected[key] = None
    return expected, raw


def _publisher(bench: tel4.Bench, profile, expect) -> GatewayPublisher:
    link = GatewayLink(bench.address, bench.state / "gateway.credential")
    publisher = GatewayPublisher(link, tel4.snapshot_sha256(), new_session_ref(profile, datetime.now(timezone.utc)),
                                 expect)
    publisher.check_identity()
    return publisher


def _ledger_state(bench: tel4.Bench) -> dict[str, object]:
    with bench.database() as db:
        return {
            "sequence_state": sorted(db.execute("SELECT source_id, last_sequence FROM sequence_state").fetchall()),
            "envelope_outbox": db.execute("SELECT COUNT(*) FROM envelope_outbox").fetchone()[0],
            "upload_batch": db.execute("SELECT COUNT(*) FROM upload_batch").fetchone()[0],
            "report_admission": db.execute("SELECT COUNT(*) FROM report_admission").fetchone()[0],
            "mapping_hold": db.execute("SELECT COUNT(*) FROM mapping_hold").fetchone()[0],
        }


def _variant(tmp_path: Path, name: str, old: str, new: str) -> Path:
    text = FIXTURE.read_bytes().decode("utf-8")
    assert old in text
    path = tmp_path / name
    path.write_bytes(text.replace(old, new).encode("utf-8"))
    return path


def test_generic_csv_through_a_real_gateway(tmp_path: Path) -> None:
    profile = load_profile(PROFILE_PATH)
    document = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    expect = field_bench.expect_identity_from_snapshot(tel4.basis().snapshot_canonical, document, tel4.EPOCH)
    oracle, raw = _oracle(profile)
    assert len(oracle) == CELLS
    bench = tel4.Bench(tmp_path)
    try:
        # 1. First collect: 196 admitted, delivered, and equal to the oracle exactly.
        first = _publisher(bench, profile, expect)
        result = CsvCollector(profile, first).collect(FIXTURE)
        print("TEL-06a first collect", json.dumps({k: result[k] for k in
              ("profile_sha256", "file_sha256", "session_ref", "report_count")}))
        assert result["report_count"] == CELLS and len(result["admissions"]) == CELLS
        assert {a["outcome"] for a in result["admissions"]} == {"ADMITTED"}
        bench.deliver_all()
        assert bench.process.link.call("diagnostics")["queue"]["sealed_pending_batches"] == 0
        envelopes = bench.envelopes()
        arrived = {(e.device_id, e.signal_id, e.source_time): e for e in envelopes}
        assert len(envelopes) == len(arrived) == CELLS and set(arrived) == set(oracle)
        for key, value in oracle.items():
            e = arrived[key]
            assert e.unit == "kW" and e.measurement == "INTERVAL_MEAN", e
            if value is None:
                assert (e.quality, e.unavailable_reason, e.value) == ("UNAVAILABLE", "NO_MEASUREMENT", None), e
                assert (e.source_time, e.interval_start) == ("2026-09-30T03:00:00Z", "2026-09-30T02:45:00Z"), e
            else:
                assert e.quality == "GOOD" and Fraction(e.value) == value, (e, value)
                assert abs(Fraction(e.value) - raw[key]) <= RESOLUTION / 2, e
        assert sum(1 for v in oracle.values() if v is None) == 4

        # 2. The same file again, new session after release_previous: same IDs and sequences, nothing new.
        before = _ledger_state(bench)
        second = _publisher(bench, profile, expect)
        assert second.session_ref != first.session_ref
        second.release_previous(first.session_ref)
        again = CsvCollector(profile, second).collect(FIXTURE)
        assert [a["outcome"] for a in again["admissions"]] == ["ALREADY_ADMITTED"] * CELLS
        assert [(a["message_id"], a["sequence"]) for a in again["admissions"]] == [
            (a["message_id"], a["sequence"]) for a in result["admissions"]]
        assert again["sealed"]["batch_ids"] == []
        assert again["file_sha256"] == result["file_sha256"]
        after = _ledger_state(bench)
        assert {k: after[k] for k in ("sequence_state", "envelope_outbox", "upload_batch")} == {
            k: before[k] for k in ("sequence_state", "envelope_outbox", "upload_batch")}

        # 3. A renamed header and a timestamp without Z refuse the whole file; nothing reaches the gateway.
        counted = ("envelope_outbox", "report_admission", "mapping_hold")
        before = _ledger_state(bench)
        renamed = _variant(tmp_path, "renamed.csv", "pv_ac_power [kW]", "pv_power [kW]")
        with pytest.raises(CsvRefused) as caught:
            CsvCollector(profile, second).collect(renamed)
        assert caught.value.code == "HEADER_MISMATCH" and caught.value.profile_sha256 == profile.sha256
        no_z = _variant(tmp_path, "no-z.csv", "\n2026-09-30T03:15:00Z,", "\n2026-09-30T03:15:00,")
        with pytest.raises(CsvRefused) as caught:
            CsvCollector(profile, second).collect(no_z)
        assert caught.value.code == "INVALID_TIMING"
        after = _ledger_state(bench)
        assert {k: after[k] for k in counted} == {k: before[k] for k in counted}

        # 4. A [W] header: the PV column is held UNIT_INCOMPATIBLE (the unit check precedes the dedup).
        before = _ledger_state(bench)
        watts = _variant(tmp_path, "watts.csv", "pv_ac_power [kW]", "pv_ac_power [W]")
        held = CsvCollector(profile, second).collect(watts)
        # Reports go in file order, each CSV row in profile row order, so the PV row is every fourth.
        pv = held["admissions"][0::4]
        rest = [a for index, a in enumerate(held["admissions"]) if index % 4]
        assert len(pv) == 49 and {(a["outcome"], a["kind"], a["field"]) for a in pv} == {
            ("HELD", "UNIT_INCOMPATIBLE", "unit")}
        assert len(rest) == 147 and {a["outcome"] for a in rest} == {"ALREADY_ADMITTED"}
        after = _ledger_state(bench)
        assert (after["envelope_outbox"], after["sequence_state"]) == (before["envelope_outbox"],
                                                                         before["sequence_state"])
    finally:
        bench.stop()
