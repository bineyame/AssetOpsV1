"""TEL-04: the Modbus TCP poller, end to end through a real gateway process.

GX-shaped emulator (in-process, replaying the pinned `-1` JSONL) -> poller
subprocess (`python -m assetops_field.modbus_poller`) -> real
`python -m assetops_gateway serve` over its authenticated IPC channel ->
`FakeCentral` over real TLS, driven by the harness's `deliver` (Q-T46).

The harness activates the snapshot (a provisioning act the poller may not do)
and computes every expected report and counter independently from the fault
windows, the schedule (0.8) and the timeline. Values compare exactly at the
emulator's register resolution (TEL-T1-Q7). Gates 1-12 are the TEL-04 card list.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import time
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from fractions import Fraction
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend" / "tests"))
sys.path.insert(0, str(ROOT / "gateway" / "tests"))
sys.path.insert(0, str(ROOT / "field" / "tests"))

import field_bench  # noqa: E402
import test_s2_registered_basis as registered  # noqa: E402
from fake_central import CERT, DROP, SERVER_INSTANT, FakeCentral, receipt_text  # noqa: E402
from field_emulators.gx_server import FaultWindow, GxEmulator, ObservationTimeline, presented_value  # noqa: E402
from gateway_process import GatewayProcess, provisioning_from_snapshot, write_config, write_upload_credential  # noqa: E402
from gateway_publication import claimed_references  # noqa: E402

from assetops_contracts.ingestion_batch_v2 import parse_canonical_batch_v2_text  # noqa: E402
from assetops_gateway.uploader import BATCHES_ROUTE  # noqa: E402
from assetops_contracts.observation import quantize_half_even  # noqa: E402
from assetops_contracts.source_envelope_v3 import parse_canonical_envelope_v3_text  # noqa: E402
from assetops_field.aggregate import PollOutcome, Result, expected_polls  # noqa: E402
from assetops_field.clock import ReplayClock  # noqa: E402
from assetops_field.modbus_poller import new_session_ref, session_stamp  # noqa: E402
from assetops_field.modbus_tcp import ReadResult, classify, exception_outcome  # noqa: E402
from assetops_field.profile import FieldProfile, ProfileRow, load_profile, parse_profile  # noqa: E402
from assetops_field.publish import GatewayPublisher  # noqa: E402
from assetops_field.report import build_report, instant_z, report_key, report_text  # noqa: E402

PROFILE_PATH = ROOT / "field" / "profiles" / "gx-system-illustrative-1.json"
JSONL = ROOT / "contract-fixtures" / "telemetry" / "kobo-public-observations-v1" / "observations.jsonl"
RATE = 120
START = datetime(2026, 9, 30, 6, 0, tzinfo=timezone.utc)
STOP = datetime(2026, 9, 30, 8, 0, tzinfo=timezone.utc)
EPOCH_LEAD = timedelta(seconds=5)
EPOCH = "epoch-1"
PYTHONPATH = os.pathsep.join(
    [str(ROOT / part) for part in ("backend", "contracts", "simulator", "gateway", "host", "field")] + [str(ROOT)]
)
DRAINED_STATES = ("STAGED", "READY")


def at(text: str) -> datetime:
    return datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def wall_text(instant: datetime) -> str:
    return instant.strftime("%Y-%m-%dT%H:%M:%S.") + f"{instant.microsecond // 1000:03d}Z"


# --- the registered snapshot (daytime draft) -----------------------------------------------------------------


@lru_cache(maxsize=1)
def basis():
    store, _, _ = registered.converted()
    draft = registered.setup_service(store).create_draft_run(registered.request())
    assert draft.execution_status == "READY", draft.blocking_reasons
    return draft.registered_basis


def snapshot_sha256() -> str:
    return hashlib.sha256(basis().snapshot_canonical.encode("utf-8")).hexdigest()


# --- the bench: gateway, central, emulator, poller -----------------------------------------------------------


@dataclass
class PollerRun:
    returncode: int
    start: dict[str, Any] | None
    holds: list[dict[str, Any]]
    exit_line: tuple[int, dict[str, Any]] | None
    stderr: str


def batch_receipt(path: str, headers: dict[str, str], body: bytes):
    """The Q-T46 responder for the batch route: `(200, receipt_text(body))`."""
    return 200, receipt_text(body.decode("utf-8"))


def with_diagnostics(batches: Callable) -> Callable:
    """Batch posts go to `batches`; the gateway's own diagnostic posts get the answer
    `gateway/tests/test_gateway_upload.py:503-506` gives them (201 with the payload SHA-256)."""

    def respond(path: str, headers: dict[str, str], body: bytes):
        if path == BATCHES_ROUTE:
            return batches(path, headers, body)
        assert path.endswith("/diagnostics"), path
        return 201, json.dumps({"diagnostic_id": hashlib.sha256(body).hexdigest()[:16], "received_at": SERVER_INSTANT,
                                "payload_sha256": hashlib.sha256(body).hexdigest()}).encode("utf-8")

    return respond


def batch_requests(central: FakeCentral) -> list:
    return [r for r in central.requests if r.path == BATCHES_ROUTE]


class Bench:
    def __init__(self, tmp: Path, responder: Callable | None = None) -> None:
        self.tmp = tmp
        self.state = tmp / "gateway"
        self.central = FakeCentral(with_diagnostics(responder or batch_receipt))
        config = write_config(self.state, provisioning_from_snapshot(basis().snapshot_canonical, epoch=EPOCH))
        write_upload_credential(self.state, "aog1." + "ab" * 16 + "." + "c" * 43)
        document = json.loads(config.read_text(encoding="utf-8"))
        document["upload"] = {"server_url": self.central.url, "upload_credential_file": "upload.credential",
                              "ca_file": str(CERT), "interval_seconds": 3600}
        config.write_text(json.dumps(document), encoding="utf-8")
        self.address = document["address"]
        self.process = GatewayProcess(config)
        assert self.process.ready, self.process.first_line
        # Gate 10: the gateway refuses nothing in the snapshot; activation is the harness's act.
        activated = self.process.link.call(
            "activate", {"snapshot_text": basis().snapshot_canonical, "claimed": claimed_references(basis())})
        assert activated == {"snapshot_sha256": snapshot_sha256()}
        assert self.process.link.call("diagnostics")["mapping_error_count"] == 0
        self.profile_document = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        self.expect = field_bench.expect_identity_from_snapshot(
            basis().snapshot_canonical, self.profile_document, EPOCH)
        self.expect_path = tmp / "expect-identity.json"
        self.expect_path.write_text(json.dumps(self.expect), encoding="utf-8")
        self.emulator: GxEmulator | None = None
        self.stopped = False

    def start_emulator(self, faults=(), start: datetime = START) -> tuple[ReplayClock, datetime]:
        wall_epoch = datetime.now(timezone.utc) + EPOCH_LEAD
        clock = ReplayClock(start, RATE, wall_epoch)
        timeline = ObservationTimeline(JSONL, load_profile(PROFILE_PATH))
        self.emulator = GxEmulator(timeline, clock, host="127.0.0.1", port=0, faults=faults)
        self.emulator.start()
        return clock, wall_epoch

    def poller(self, profile_path: Path, wall_epoch: datetime, *, poller_dir: Path, stop_at: datetime = STOP,
               start: datetime = START, env: dict[str, str] | None = None,
               tick: Callable[[Path], None] | None = None) -> PollerRun:
        command = [
            sys.executable, "-m", "assetops_field.modbus_poller", "--profile", str(profile_path),
            "--host", "127.0.0.1", "--port", str(self.emulator.port), "--gateway-address", self.address,
            "--ipc-credential", str(self.state / "gateway.credential"), "--snapshot-sha256", snapshot_sha256(),
            "--expect-identity", str(self.expect_path), "--state-dir", str(poller_dir), "--read-timeout-s", "0.25",
            "--replay-start", instant_z(start), "--replay-rate", str(RATE),
            "--replay-wall-epoch", wall_text(wall_epoch), "--stop-at", instant_z(stop_at),
        ]
        return run_poller(command, self.tmp, env=env, tick=tick, poller_dir=poller_dir,
                          budget=2 * (stop_at - start).total_seconds() / RATE + 60)

    def deliver_all(self, deadline_s: float = 120) -> None:
        """`deliver` until nothing is attempted, then again after any back-off, until no batch is pending."""
        deadline = time.monotonic() + deadline_s
        while True:
            while self.process.link.call("deliver", {"max_batches": 50})["batches"]["attempted"]:
                pass
            if self.process.link.call("diagnostics")["queue"]["sealed_pending_batches"] == 0:
                return
            assert time.monotonic() < deadline, "batches still pending after the delivery deadline"
            time.sleep(1.0)

    def stop(self) -> None:
        if self.stopped:
            return
        self.stopped = True
        try:
            if self.emulator is not None:
                self.emulator.stop()
        finally:
            try:
                self.process.kill()
            finally:
                self.central.close()

    def database(self) -> sqlite3.Connection:
        return sqlite3.connect(f"file:{self.process.database.as_posix()}?mode=ro", uri=True)

    def envelopes(self) -> list:
        with self.database() as db:
            rows = db.execute("SELECT envelope_text FROM envelope_outbox ORDER BY source_id, sequence").fetchall()
        return [parse_canonical_envelope_v3_text(text) for (text,) in rows]


def run_poller(command: list[str], tmp: Path, *, env: dict[str, str] | None, tick: Callable[[Path], None] | None,
               poller_dir: Path, budget: float) -> PollerRun:
    environment = {**os.environ, "PYTHONPATH": PYTHONPATH, "PYTHONDONTWRITEBYTECODE": "1"}
    environment.pop("ASSETOPS_FIELD_CRASH_AFTER_ADMIT", None)
    environment.update(env or {})
    index = len(list(tmp.glob("poller-*.out")))
    out_path, err_path = tmp / f"poller-{index}.out", tmp / f"poller-{index}.err"
    with out_path.open("w", encoding="utf-8") as out, err_path.open("w", encoding="utf-8") as err:
        process = subprocess.Popen(command, stdout=out, stderr=err, env=environment, cwd=str(ROOT))
        deadline = time.monotonic() + budget
        try:
            while process.poll() is None:
                if time.monotonic() > deadline:
                    raise AssertionError(f"the poller ran past its {budget:.0f} s budget")
                if tick is not None:
                    tick(poller_dir)
                time.sleep(0.05)
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=30)
    start, holds, exit_line = None, [], None
    for line in out_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("FIELD-POLLER START "):
            start = json.loads(line.removeprefix("FIELD-POLLER START "))
        elif line.startswith("FIELD-POLLER HOLD "):
            holds.append(json.loads(line.removeprefix("FIELD-POLLER HOLD ")))
        elif line.startswith("FIELD-POLLER EXIT "):
            code, _, document = line.removeprefix("FIELD-POLLER EXIT ").partition(" ")
            exit_line = (int(code), json.loads(document))
    return PollerRun(process.returncode, start, holds, exit_line, err_path.read_text(encoding="utf-8"))


def read_status(poller_dir: Path) -> dict[str, Any] | None:
    try:
        return json.loads((poller_dir / "status.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None  # not written yet, or replaced under us


def drained(db: sqlite3.Connection) -> tuple[int, int]:
    """(STAGED upload batches, unbatched STAGED/READY outbox rows)."""
    staged = db.execute("SELECT COUNT(*) FROM upload_batch WHERE state='STAGED'").fetchone()[0]
    unbatched = db.execute(
        "SELECT COUNT(*) FROM envelope_outbox o WHERE o.state IN (?, ?) "
        "AND NOT EXISTS (SELECT 1 FROM batch_item b WHERE b.message_id = o.message_id)", DRAINED_STATES,
    ).fetchone()[0]
    return staged, unbatched


# --- the independent expectation (0.7, 0.8, TEL-T1-Q7) -------------------------------------------------------


def oracle_outcome(timeline: ObservationTimeline, row: ProfileRow, instant: datetime, faults) -> PollOutcome:
    """What one read of `row` at source `instant` returns, from the fault windows and the timeline alone."""
    active = [fault for fault in faults if fault.active(instant)]
    if any(fault.kind in ("PAUSE", "WRONG_TID", "WRONG_UNIT_ID") for fault in active):
        return PollOutcome.NO_ANSWER
    for fault in active:
        if fault.kind == "EXCEPTION" and fault.row_id == row.row_id:
            return exception_outcome(fault.code)
    if any(fault.kind == "SENTINEL" and fault.row_id == row.row_id for fault in active):
        return PollOutcome.NO_VALUE
    words = timeline.row_words(timeline.rows[row.row_id], instant)
    if words is None:
        return PollOutcome.NO_ANSWER  # exception 0B: a suppressed or dropped observation
    return classify([ReadResult("WORDS", words=tuple(word for register in words for word in register))], row)[0]


def expected_value(timeline: ObservationTimeline, row: ProfileRow, instant: datetime) -> Fraction:
    observation = timeline.hold_at(row.row_id, instant).observation
    assert observation["outcome"] == "REPORTED"
    emulated = timeline.rows[row.row_id]
    return quantize_half_even(presented_value(emulated, Fraction(observation["reported_value"])),
                              row.output_resolution)


def expected_run(profile: FieldProfile, session_start: datetime, stop_at: datetime, faults=()):
    """({(device, signal, source_time): (quality, reason, interval_start, value)}, counters)."""
    timeline = ObservationTimeline(JSONL, load_profile(PROFILE_PATH))
    reports: dict[tuple[str, str, str], tuple] = {}
    counters: Counter = Counter()
    for row in profile.rows:
        key = lambda instant: (row.device_id, row.signal_id, instant_z(instant))  # noqa: E731
        cadence = timedelta(seconds=row.cadence_seconds)
        if row.reading_class == "INTERVAL_SIGNAL":
            span = timedelta(seconds=row.span_seconds)
            end = START + cadence
            while end <= stop_at:
                if end > session_start:
                    polls = [p for p in expected_polls(row, end - span) if p >= session_start]
                    outcomes = [oracle_outcome(timeline, row, p, faults) for p in polls]
                    counters.update(outcome.value for outcome in outcomes)
                    start = instant_z(end - span)
                    if end - span < session_start:
                        reports[key(end)] = ("UNAVAILABLE", "NO_COMPLETED_INTERVAL", start, None)
                    elif not any(o in (PollOutcome.VALUE, PollOutcome.NO_VALUE) for o in outcomes):
                        pass  # no poll answered: nothing is published
                    elif all(o is PollOutcome.VALUE for o in outcomes):
                        reports[key(end)] = ("GOOD", None, start, expected_value(timeline, row, polls[0]))
                    else:
                        reports[key(end)] = ("UNAVAILABLE", "NO_MEASUREMENT", start, None)
                end += cadence
        else:
            boundary = START
            while boundary <= stop_at:
                if boundary >= session_start:
                    read_at = boundary + timedelta(seconds=1)  # B + ceil(skew / 2)
                    outcome = oracle_outcome(timeline, row, read_at, faults)
                    counters[outcome.value] += 1
                    if outcome is PollOutcome.VALUE:
                        reports[key(boundary)] = ("GOOD", None, None, expected_value(timeline, row, read_at))
                    elif outcome is PollOutcome.NO_VALUE:
                        reports[key(boundary)] = ("UNAVAILABLE", "NO_MEASUREMENT", None, None)
                boundary += cadence
    for name in ("VALUE", "NO_VALUE", "FAILED", "NO_ANSWER", "CONFIG_FAULT", "SKIPPED_LATE"):
        counters.setdefault(name, 0)
    return reports, dict(counters)


def arrived(envelopes) -> dict[tuple[str, str, str], tuple]:
    out = {}
    for e in envelopes:
        value = None if e.value is None else Fraction(e.value)
        out[(e.device_id, e.signal_id, e.source_time)] = (e.quality, e.unavailable_reason, e.interval_start, value)
    return out


def assert_values_at_register_resolution(profile: FieldProfile, envelopes) -> int:
    """TEL-T1-Q7: an independent bound, |arrived - observation| <= q / 2, for every GOOD report."""
    timeline = ObservationTimeline(JSONL, load_profile(PROFILE_PATH))
    rows = {(row.device_id, row.signal_id): row for row in profile.rows}
    checked = 0
    for e in envelopes:
        if e.quality != "GOOD":
            continue
        row = rows[(e.device_id, e.signal_id)]
        instant = at(e.source_time) + (timedelta(seconds=-1) if e.interval_start else timedelta(seconds=1))
        observation = timeline.hold_at(row.row_id, instant).observation
        assert observation["outcome"] == "REPORTED", (e, observation)
        quantum = row.register_quantum * Fraction(10) ** row.exponent
        assert abs(Fraction(e.value) - Fraction(observation["reported_value"])) <= quantum / 2, (e, observation)
        checked += 1
    return checked


# --- light: the session reference, configuration refusals ----------------------------------------------------


def test_session_ref_format_with_an_injected_token() -> None:
    profile = load_profile(PROFILE_PATH)
    ref = new_session_ref(profile, datetime(2026, 10, 27, 9, 8, 7, 654321, tzinfo=timezone.utc),
                          token=lambda: "0a1b2c3d")
    assert ref == "field:gx-system-illustrative-1:1:20261027T090807Z:0a1b2c3d"
    assert session_stamp(ref) == "20261027T090807Z-0a1b2c3d"
    for bad in ("0A1B2C3D", "0a1b2c3", "0a1b2c3d4"):
        try:
            new_session_ref(profile, datetime(2026, 10, 27, tzinfo=timezone.utc), token=lambda bad=bad: bad)
        except ValueError:
            continue
        raise AssertionError(f"token {bad!r} was accepted")
    import re
    assert re.fullmatch(r"field:gx-system-illustrative-1:1:\d{8}T\d{6}Z:[0-9a-f]{8}",
                        new_session_ref(profile, datetime.now(timezone.utc)))


def _offline_command(tmp: Path, expect: dict[str, Any], *replay: str) -> list[str]:
    expect_path = tmp / "expect.json"
    expect_path.write_text(json.dumps(expect), encoding="utf-8")
    return [sys.executable, "-m", "assetops_field.modbus_poller", "--profile", str(PROFILE_PATH),
            "--host", "127.0.0.1", "--port", "1", "--gateway-address", r"\\.\pipe\assetops-tel4-none",
            "--ipc-credential", str(tmp / "none.credential"), "--snapshot-sha256", "0" * 64,
            "--expect-identity", str(expect_path), "--state-dir", str(tmp / "state"), *replay]


def test_replay_without_stop_at_and_a_crash_hook_off_simulated_exit_2(tmp_path: Path) -> None:
    expect = {"tenant_id": "t", "site_id": "s", "gateway_id": "g", "source_mode": "SIMULATED",
              "sequence_epoch": EPOCH, "row_sources": {}}
    replay = ("--replay-start", "2026-09-30T06:00:00Z", "--replay-rate", "120",
              "--replay-wall-epoch", "2026-10-27T00:00:00.000Z")
    no_stop = run_poller(_offline_command(tmp_path, expect, *replay), tmp_path, env=None, tick=None,
                         poller_dir=tmp_path / "state", budget=60)
    assert no_stop.returncode == 2 and "--stop-at" in no_stop.stderr and no_stop.start is None
    crash = run_poller(_offline_command(tmp_path, {**expect, "source_mode": "LIVE"}, *replay,
                                        "--stop-at", "2026-09-30T07:00:00Z"),
                       tmp_path, env={"ASSETOPS_FIELD_CRASH_AFTER_ADMIT": "1"}, tick=None,
                       poller_dir=tmp_path / "state", budget=60)
    assert crash.returncode == 2 and "SIMULATED" in crash.stderr and crash.start is None


# --- the four end-to-end cases ------------------------------------------------------------------------------


def test_clean_window_lands_acknowledged(tmp_path: Path) -> None:
    posts = {"n": 0}

    def respond(path, headers, body):
        posts["n"] += 1
        if posts["n"] <= 2:
            return DROP  # gate 6: the first two batch posts drop
        return batch_receipt(path, headers, body)

    bench = Bench(tmp_path, respond)
    try:
        _, wall_epoch = bench.start_emulator()
        run = bench.poller(PROFILE_PATH, wall_epoch, poller_dir=tmp_path / "poller")
        assert run.returncode == 0, run.stderr
        assert run.start["session_start"] == instant_z(START) and run.start["previous_ref"] is None
        assert run.start["clock"]["mode"] == "REPLAY" and run.holds == []
        status = run.exit_line[1]
        assert run.exit_line[0] == 0 and status == read_status(tmp_path / "poller")
        bench.deliver_all()
        assert bench.emulator.writes == 0  # gate 9
        bench.stop()
        profile = load_profile(PROFILE_PATH)
        expected, counters = expected_run(profile, START, STOP)
        envelopes = bench.envelopes()
        assert arrived(envelopes) == expected
        assert status["counters"] == counters and counters["SKIPPED_LATE"] == 0
        assert status["admissions"] == {"ADMITTED": len(expected), "ALREADY_ADMITTED": 0, "HELD": 0}
        assert assert_values_at_register_resolution(profile, envelopes) == sum(
            1 for v in expected.values() if v[0] == "GOOD") > 0
        # Gate 11: the first interval after the session start is GOOD.
        first = expected[("pv-inverter-controller", "ac-power", "2026-09-30T06:15:00Z")]
        assert first[0] == "GOOD" and first[2] == "2026-09-30T06:00:00Z"
        # Gate 1: every admitted envelope is acknowledged with a 200 receipt.
        with bench.database() as db:
            states = Counter(state for (state,) in db.execute("SELECT state FROM envelope_outbox"))
            batches = Counter(state for (state,) in db.execute("SELECT state FROM upload_batch"))
            receipts = db.execute("SELECT COUNT(*) FROM acknowledgement").fetchone()[0]
        assert states == {"ACKED": len(expected)} and set(batches) == {"ACKED"}
        assert receipts == len(expected)
        # Gate 6: each dropped body was posted again byte-identically and recorded.
        bodies = [r.body for r in batch_requests(bench.central)]
        assert len(bodies) == sum(batches.values()) + 2
        assert all(bodies.count(dropped) == 2 for dropped in bodies[:2])
        posted = {parse_canonical_envelope_v3_text(t).message_id
                  for body in bodies for t in parse_canonical_batch_v2_text(body.decode("utf-8")).envelopes}
        assert posted == {e.message_id for e in envelopes}
    finally:
        bench.stop()


FAULTS = (
    FaultWindow(at("2026-09-30T06:15:00Z"), at("2026-09-30T06:45:00Z"), "SENTINEL", row_id="pv-ac-output"),
    FaultWindow(at("2026-09-30T06:45:00Z"), at("2026-09-30T07:15:00Z"), "EXCEPTION", row_id="battery-soc", code=0x02),
    FaultWindow(at("2026-09-30T07:15:00Z"), at("2026-09-30T07:30:00Z"), "PAUSE"),
    FaultWindow(at("2026-09-30T07:30:00Z"), at("2026-09-30T07:45:00Z"), "WRONG_TID"),
)
PAUSE_START, PAUSE_END = "2026-09-30T07:15:00Z", "2026-09-30T07:30:00Z"


def test_faults_follow_the_table(tmp_path: Path) -> None:
    bench = Bench(tmp_path)
    reads: dict[str, Any] = {}

    def tick(poller_dir: Path) -> None:
        # Gate 7 (Q-T69): diagnostics after the last admission before the pause, and >= 3 s of wall later.
        status = read_status(poller_dir)
        if status is None:
            return
        if "first" not in reads and status["last_publish_instant"] == PAUSE_START:
            reads["first"] = bench.process.link.call("diagnostics")
            reads["first_monotonic"] = time.monotonic()
        elif "first" in reads and "second" not in reads and time.monotonic() - reads["first_monotonic"] >= 3.5:
            reads["second"] = bench.process.link.call("diagnostics")
            reads["second_status"] = read_status(poller_dir) or status

    try:
        _, wall_epoch = bench.start_emulator(FAULTS)
        run = bench.poller(PROFILE_PATH, wall_epoch, poller_dir=tmp_path / "poller", tick=tick)
        assert run.returncode == 0, run.stderr
        assert bench.emulator.writes == 0
        bench.deliver_all()
        bench.stop()
        profile = load_profile(PROFILE_PATH)
        expected, counters = expected_run(profile, START, STOP, FAULTS)
        envelopes = bench.envelopes()
        got = arrived(envelopes)
        # Gate 2: sentinel and exception 02 give UNAVAILABLE / NO_MEASUREMENT envelopes, not holds.
        for device, signal, times in (("pv-inverter-controller", "ac-power", ("06:30", "06:45")),
                                      ("battery-pcs-controller", "state-of-charge", ("06:45", "07:00"))):
            for hhmm in times:
                assert got[(device, signal, f"2026-09-30T{hhmm}:00Z")][:2] == ("UNAVAILABLE", "NO_MEASUREMENT")
        assert run.exit_line[1]["holds_by_kind"] == {} and run.holds == []
        assert got == expected
        # Gate 7: nothing for the paused boundaries...
        assert ("battery-pcs-controller", "state-of-charge", PAUSE_START) not in got
        assert ("pv-inverter-controller", "ac-power", PAUSE_END) not in got
        # ...and contact age grows in diagnostics while the emulator is paused.
        assert "second" in reads, "the pause was never observed"
        assert reads["second_status"]["last_publish_instant"] == PAUSE_START, "the second read missed the pause"
        for source_id in sorted(set(bench.expect["row_sources"].values())):
            first = {c["source_id"]: c for c in reads["first"]["source_contacts"]}[source_id]
            second = {c["source_id"]: c for c in reads["second"]["source_contacts"]}[source_id]
            assert first["last_contact_at"] is not None and first["last_contact_at"] == second["last_contact_at"]
            age = lambda d, c: (at(d["observed_at"]) - at(c["last_contact_at"])).total_seconds()  # noqa: E731
            assert age(reads["second"], second) - age(reads["first"], first) >= 2
        # Gate 8: the status counters match the injected faults.
        status = run.exit_line[1]
        assert status["counters"] == counters
        assert counters["NO_VALUE"] == 6 + 2 and counters["NO_ANSWER"] >= 3 + 3 + 1 + 1
        assert status["faulted_rows"] == [] and status["retained_reports"] == 0
        assert status["admissions"] == {"ADMITTED": len(expected), "ALREADY_ADMITTED": 0, "HELD": 0}
        raw = [json.loads(line) for line in
               (tmp_path / "poller" / f"raw-{session_stamp(status['session_ref'])}.jsonl").read_text().splitlines()]
        outcomes = Counter(line["outcome"] for line in raw)
        assert outcomes["NO_ANSWER_TIMEOUT"] >= 2 * 3 + 1 and outcomes["NO_ANSWER_TID_MISMATCH"] == 3 + 1
        assert outcomes["EXCEPTION_02"] == 2 and all(line["profile_sha256"] == profile.sha256 for line in raw)
    finally:
        bench.stop()


def test_unit_w_is_held_and_conflicts_are_held(tmp_path: Path) -> None:
    document = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    document["rows"][0]["source_unit"] = "W"
    edited = tmp_path / "gx-unit-w.json"
    edited.write_text(json.dumps(document), encoding="utf-8")
    profile = parse_profile(document)
    stop_at = at("2026-09-30T06:30:00Z")
    bench = Bench(tmp_path)
    try:
        _, wall_epoch = bench.start_emulator()
        run = bench.poller(edited, wall_epoch, poller_dir=tmp_path / "poller", stop_at=stop_at)
        # Gate 3: UNIT_INCOMPATIBLE holds, not fatal; the poller exits 0.
        assert run.returncode == 0, run.stderr
        expected, _ = expected_run(profile, START, stop_at)
        held = sorted(k for k in expected if k[0] == "pv-inverter-controller")
        assert len(held) == 2
        status = run.exit_line[1]
        assert status["holds_by_kind"] == {"UNIT_INCOMPATIBLE": len(held)}
        assert [h["kind"] for h in run.holds] == ["UNIT_INCOMPATIBLE"] * len(held)
        assert sorted(h["report_key"] for h in run.holds) == sorted(
            report_key(profile, profile.rows[0], at(k[2])) for k in held)
        # Gates 4 and 5: the same report text again, then the same key with another value.
        soc = profile.rows[1]
        timeline = ObservationTimeline(JSONL, load_profile(PROFILE_PATH))
        boundary = START
        value = expected_value(timeline, soc, boundary + timedelta(seconds=1))
        text = report_text(build_report(profile, soc, Result("GOOD", None, value, boundary, None)))
        other = report_text(build_report(profile, soc, Result("GOOD", None, value + 1, boundary, None)))
        session_ref = json.loads((tmp_path / "poller" / "session.json").read_text(encoding="utf-8"))["session_ref"]
        publisher = GatewayPublisher(bench.process.link, snapshot_sha256(), session_ref, bench.expect)
        again, conflict = publisher.admit([text, other])
        bench.stop()
        with bench.database() as db:
            pv_rows = db.execute("SELECT COUNT(*) FROM envelope_outbox WHERE source_id = ?",
                                 (bench.expect["row_sources"]["pv-inverter-controller/ac-power"],)).fetchone()[0]
            (message_id,) = db.execute("SELECT message_id FROM report_admission WHERE report_key = ?",
                                       (report_key(profile, soc, boundary),)).fetchone()
        assert pv_rows == 0  # no sequence allocated for a held report
        assert again["outcome"] == "ALREADY_ADMITTED" and again["message_id"] == message_id
        assert conflict["outcome"] == "HELD" and conflict["kind"] == "CONFLICTING_REPORT"
    finally:
        bench.stop()


def test_restart_releases_the_killed_session(tmp_path: Path) -> None:
    bench = Bench(tmp_path)
    poller_dir = tmp_path / "poller"
    try:
        _, wall_epoch = bench.start_emulator()
        killed = bench.poller(PROFILE_PATH, wall_epoch, poller_dir=poller_dir,
                              env={"ASSETOPS_FIELD_CRASH_AFTER_ADMIT": "3"})
        assert killed.returncode == 9 and killed.exit_line is None, killed.stderr
        with bench.database() as db:
            assert drained(db)[1] > 0  # the crash left admitted, unsealed envelopes behind
        restarted = bench.poller(PROFILE_PATH, wall_epoch, poller_dir=poller_dir)
        assert restarted.returncode == 0, restarted.stderr
        # Gate 12: START names the killed session, whose reference was never reused.
        assert restarted.start["previous_ref"] == killed.start["session_ref"]
        assert restarted.start["session_ref"] != killed.start["session_ref"]
        session_start = at(restarted.start["session_start"])
        assert session_start > at("2026-09-30T06:30:00Z") and (session_start - START).total_seconds() % 900
        bench.stop()
        with bench.database() as db:
            assert drained(db) == (0, 0)  # no stranded batch
        pv = sorted((e for e in bench.envelopes() if e.device_id == "pv-inverter-controller"
                     and at(e.source_time) > session_start), key=lambda e: e.source_time)
        first = pv[0]
        assert (first.quality, first.unavailable_reason) == ("UNAVAILABLE", "NO_COMPLETED_INTERVAL")
        assert at(first.interval_start) == at(first.source_time) - timedelta(seconds=900) < session_start
        assert pv[1].quality == "GOOD"
    finally:
        bench.stop()
