"""TEL-03 GX-shaped emulator against the TEL-02 client, on a fake wall (Q-T40). No real time except the CLI smoke."""

from __future__ import annotations

import inspect
import json
import os
import socket
import struct
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from fractions import Fraction
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

from field_emulators.gx_server import FaultWindow, GxEmulator, ObservationTimeline  # noqa: E402
from field_fixtures import FakeWall, at, profile_document, row_document  # noqa: E402

from assetops_contracts.observation import exact_decimal_text, quantize_half_even  # noqa: E402

from assetops_field.aggregate import PollOutcome  # noqa: E402
from assetops_field.clock import ReplayClock  # noqa: E402
from assetops_field.modbus_tcp import ModbusTcpClient, classify, requests_for  # noqa: E402
from assetops_field.profile import load_profile, parse_profile  # noqa: E402

JSONL = ROOT / "contract-fixtures" / "telemetry" / "kobo-public-observations-v1" / "observations.jsonl"
PROFILE = load_profile(ROOT / "field" / "profiles" / "gx-system-illustrative-1.json")
PV = next(row for row in PROFILE.rows if row.row_id == "pv-ac-output")
SOC = next(row for row in PROFILE.rows if row.row_id == "battery-soc")
START = at("2026-09-30T03:00:00Z")
WALL0 = datetime(2026, 10, 27, 12, 0, 0, tzinfo=timezone.utc)


class Bench:
    def __init__(self, faults=()) -> None:
        self.wall = FakeWall(WALL0)
        self.clock = ReplayClock(START, 1, WALL0, wall=self.wall)
        self.timeline = ObservationTimeline(JSONL, PROFILE)
        self.emulator = GxEmulator(self.timeline, self.clock, host="127.0.0.1", port=0, faults=faults)
        self.port = self.emulator.start()
        self.client = ModbusTcpClient("127.0.0.1", self.port, timeout_s=0.3)

    def at(self, source_instant: datetime) -> None:
        self.wall.set(WALL0 + (source_instant - START))
        assert self.clock.now() == source_instant

    def poll(self, row):
        results = [self.client.read(*request) for request in requests_for(row)]
        return results, classify(results, row)

    def raw(self, frame: bytes) -> bytes:
        with socket.create_connection(("127.0.0.1", self.port), timeout=1.0) as connection:
            connection.sendall(frame)
            return connection.recv(260)

    def close(self) -> None:
        self.client.close()
        self.emulator.stop()


@pytest.fixture
def bench():
    benches: list[Bench] = []

    def make(faults=()) -> Bench:
        benches.append(Bench(faults))
        return benches[-1]

    yield make
    for b in benches:
        assert b.emulator.writes == 0, "a test other than the write test reached the write counter"
        b.close()


def observations():
    return [json.loads(line) for line in JSONL.read_text(encoding="utf-8").splitlines()]


def expected_presented(row, raw_text: str) -> Fraction:
    scale = Fraction(10) ** row.exponent
    return quantize_half_even(Fraction(raw_text) / scale, row.register_quantum) * scale


def test_window_maxima_fit_the_registers():
    values = {(o["device_id"], o["signal_id"]): [] for o in observations()}
    for o in observations():
        if o["outcome"] == "REPORTED":
            values[(o["device_id"], o["signal_id"])].append(Fraction(o["reported_value"]))
    pv_max = max(values[(PV.device_id, PV.signal_id)])
    soc_max = max(values[(SOC.device_id, SOC.signal_id)])
    print(f"\nWINDOW MAXIMA pv_kw={exact_decimal_text(pv_max)} soc_pct={exact_decimal_text(soc_max)}")  # noqa
    assert pv_max <= Fraction(65534, 1000) and soc_max <= 100


def test_every_observation_reads_back_through_profile_1(bench):
    b = bench()
    tally = {"REPORTED": 0, "SENTINEL": 0, "0B": 0}
    for row in (PV, SOC):
        for o in b.timeline.observations(row.row_id):
            t = at(o["source_sample_time"])
            b.at(t - timedelta(seconds=row.span_seconds // 2) if row.reading_class == "INTERVAL_SIGNAL" else t)
            results, (outcome, decoded) = b.poll(row)
            if o["outcome"] == "REPORTED":
                assert outcome is PollOutcome.VALUE, (row.row_id, o)
                assert decoded.value == expected_presented(row, o["reported_value"]), (row.row_id, o)
                tally["REPORTED"] += 1
            elif o["outcome"] in ("NO_VALUE_AT_BOUNDARY", "NO_PRECEDING_INTERVAL"):
                assert (outcome, decoded.kind) == (PollOutcome.NO_VALUE, "SENTINEL"), (row.row_id, o)
                tally["SENTINEL"] += 1
            else:
                assert o["outcome"] in ("DROPPED", "SUPPRESSED_BY_GAP")
                assert [(r.kind, r.exception_code) for r in results] == [("EXCEPTION", 0x0B)], (row.row_id, o)
                tally["0B"] += 1
    print(f"\nREAD-BACK TALLY {tally}")  # noqa
    assert tally["REPORTED"] > 0
    assert sum(tally.values()) == len(b.timeline.observations(PV.row_id)) + len(b.timeline.observations(SOC.row_id))


def test_state_presents_from_one_second_before_its_sample_and_sentinels_outside_the_window(bench):
    b = bench()
    first, second = b.timeline.observations(SOC.row_id)[:2]
    t1, t2 = at(first["source_sample_time"]), at(second["source_sample_time"])
    b.at(t1 - timedelta(seconds=2))
    assert b.poll(SOC)[1][0] is PollOutcome.NO_VALUE  # before the first observation: sentinel
    if second["outcome"] == "REPORTED":
        b.at(t2 - timedelta(seconds=1))
        assert b.poll(SOC)[1][1].value == expected_presented(SOC, second["reported_value"])
    last = b.timeline.observations(SOC.row_id)[-1]
    b.at(at(last["source_sample_time"]) + timedelta(seconds=SOC.cadence_seconds))
    assert b.poll(SOC)[1][0] is PollOutcome.NO_VALUE
    last_pv = b.timeline.observations(PV.row_id)[-1]
    b.at(at(last_pv["source_sample_time"]) + timedelta(seconds=1))
    assert b.poll(PV)[1][0] is PollOutcome.NO_VALUE


def test_whole_pv_value_is_on_808_and_zero_on_809_810(bench):
    b = bench()
    reported = [o for o in b.timeline.observations(PV.row_id) if o["outcome"] == "REPORTED"
                and Fraction(o["reported_value"]) > 1]
    o = reported[0]
    b.at(at(o["source_sample_time"]) - timedelta(seconds=450))
    results, _ = b.poll(PV)
    words = results[0].words
    assert words[1:] == (0, 0) and Fraction(words[0], 1000) == expected_presented(PV, o["reported_value"])


def test_pymodbus_client_reads_the_same_words(bench):
    pymodbus = pytest.importorskip("pymodbus")
    assert pymodbus.__version__ == "3.16.1"
    from pymodbus.client import ModbusTcpClient as PymodbusClient

    b = bench()
    other = PymodbusClient("127.0.0.1", port=b.port, timeout=1)
    assert other.connect()
    unit_kw = "device_id" if "device_id" in inspect.signature(other.read_holding_registers).parameters else "slave"
    try:
        reported = [o for o in b.timeline.observations(PV.row_id) if o["outcome"] == "REPORTED"]
        for o in reported[:: max(len(reported) // 3, 1)][:3]:
            b.at(at(o["source_sample_time"]) - timedelta(seconds=450))
            for address, count in ((808, 3), (843, 1)):
                ours = b.client.read(100, 3, address, count)
                theirs = other.read_holding_registers(address, count=count, **{unit_kw: 100})
                assert not theirs.isError() and tuple(theirs.registers) == ours.words
    finally:
        other.close()


@pytest.mark.parametrize(
    "fault, outcome",
    [
        (dict(kind="PAUSE"), PollOutcome.NO_ANSWER),
        (dict(kind="EXCEPTION", row_id="pv-ac-output", code=0x04), PollOutcome.FAILED),
        (dict(kind="EXCEPTION", row_id="pv-ac-output", code=0x06), PollOutcome.FAILED),
        (dict(kind="EXCEPTION", row_id="pv-ac-output", code=0x02), PollOutcome.NO_VALUE),
        (dict(kind="EXCEPTION", row_id="pv-ac-output", code=0x03), PollOutcome.CONFIG_FAULT),
        (dict(kind="SENTINEL", row_id="pv-ac-output"), PollOutcome.NO_VALUE),
        (dict(kind="WRONG_UNIT_ID"), PollOutcome.NO_ANSWER),
        (dict(kind="WRONG_TID"), PollOutcome.NO_ANSWER),
    ],
)
def test_each_fault_window_kind_gives_its_outcome_through_classify(bench, fault, outcome):
    b = bench()
    reported = next(o for o in b.timeline.observations(PV.row_id) if o["outcome"] == "REPORTED")
    instant = at(reported["source_sample_time"]) - timedelta(seconds=450)
    b.at(instant)
    assert b.poll(PV)[1][0] is PollOutcome.VALUE
    soc_before = b.poll(SOC)[1]
    b.emulator.faults.append(FaultWindow(instant, instant + timedelta(seconds=60), **fault))
    assert b.poll(PV)[1][0] is outcome
    if "row_id" in fault:
        assert b.poll(SOC)[1] == soc_before  # a row fault leaves the other rows alone
    b.at(instant + timedelta(seconds=60))  # half-open: the window has ended
    assert b.poll(PV)[1][0] is PollOutcome.VALUE


def frame(unit: int, function: int, payload: bytes, tid: int = 7) -> bytes:
    pdu = bytes([function]) + payload
    return struct.pack(">HHHB", tid, 0, len(pdu) + 1, unit) + pdu


@pytest.mark.parametrize(
    "request_frame, code",
    [
        (frame(99, 3, struct.pack(">HH", 808, 3)), 0x0B),  # unit no row declares
        (frame(100, 3, struct.pack(">HH", 811, 1)), 0x02),  # address no row declares
        (frame(100, 3, struct.pack(">HH", 807, 2)), 0x02),
        (frame(100, 3, struct.pack(">HH", 808, 0)), 0x03),
        (frame(100, 3, struct.pack(">HH", 808, 126)), 0x03),
        (frame(100, 1, struct.pack(">HH", 808, 1)), 0x01),  # a read the GX shape does not serve
    ],
)
def test_framing_exceptions(bench, request_frame, code):
    b = bench()
    b.at(START + timedelta(hours=6))
    answer = b.raw(request_frame)
    tid, _, length, unit = struct.unpack(">HHHB", answer[:7])
    assert (tid, length, answer[7] & 0x80, answer[8]) == (7, 3, 0x80, code)


def test_a_write_frame_is_counted_and_answered_exception_01():
    b = Bench()
    try:
        b.at(START + timedelta(hours=6))
        answer = b.raw(frame(100, 6, struct.pack(">HH", 808, 1)))
        assert answer[7:9] == bytes([0x86, 0x01])
        assert b.emulator.writes == 1
    finally:
        b.close()


def test_the_timeline_refuses_a_row_without_observations_or_with_another_unit(tmp_path):
    missing = row_document(row_id="ghost", device_id="ghost-meter")
    with pytest.raises(ValueError, match="no observation"):
        ObservationTimeline(JSONL, parse_profile(profile_document(rows=[missing])))
    watts = row_document(source_unit="W", unit_exponent=0, output_resolution="1")
    with pytest.raises(ValueError, match="observations in"):
        ObservationTimeline(JSONL, parse_profile(profile_document(rows=[watts])))


def test_cli_prints_ready_and_stops_at_stop_at():
    epoch = datetime.now(timezone.utc) + timedelta(seconds=1)
    env = dict(os.environ)
    command = [sys.executable, str(HERE / "field_emulators" / "gx_server.py"), "--jsonl", str(JSONL),
               "--profile", str(ROOT / "field" / "profiles" / "gx-system-illustrative-1.json"), "--port", "0",
               "--replay-start", "2026-09-30T06:00:00Z", "--replay-rate", "600",
               "--replay-wall-epoch", epoch.strftime("%Y-%m-%dT%H:%M:%S.%fZ")[:-4] + "Z",
               "--stop-at", "2026-09-30T06:10:00Z"]
    process = subprocess.run(command, capture_output=True, text=True, timeout=30, env=env)
    assert process.returncode == 0, process.stderr
    assert process.stdout.startswith("READY 127.0.0.1:")
    assert int(process.stdout.split(":")[1]) > 0
