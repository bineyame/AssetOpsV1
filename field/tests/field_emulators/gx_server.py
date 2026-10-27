"""GX-shaped Modbus TCP emulator, stdlib only (build spec TEL-03, Q-T37, Q-T39, Q-T42, Q-T43).

Serves FC 03/04 from a pinned public-observation JSONL through a field profile.
Every fault is native and in-process: a paused server that reads but never
answers, wrong unit and transaction IDs, per-row exceptions and sentinels.
Any write function code is counted in `writes` and answered with exception 01.

Value-at-instant rule: a state observation at `T` holds over
`[T - STATE_LEAD_SECONDS, T_next - STATE_LEAD_SECONDS)`; an interval
observation at `T` with span `S` holds over `[T - S, T)`. Outside every hold
period the row's registers hold its sentinel. `REPORTED` presents the value at
the register's resolution (GX-layout rows) through `encode_value`;
`NO_VALUE_AT_BOUNDARY` and `NO_PRECEDING_INTERVAL` present the sentinel;
`SUPPRESSED_BY_GAP` and `DROPPED` answer exception 0B (nothing published).
"""

from __future__ import annotations

import argparse
import bisect
import json
import socketserver
import struct
import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from fractions import Fraction
from pathlib import Path
from typing import Sequence

from assetops_contracts.observation import quantize_half_even

from assetops_field.clock import Clock, ReplayClock
from assetops_field.decode import encode_sentinel, encode_value
from assetops_field.profile import FieldProfile, ProfileRow, load_profile

STATE_LEAD_SECONDS = 1
WRITE_FUNCTIONS = frozenset({5, 6, 15, 16, 23})
MAX_COUNT = 125
SENTINEL_OUTCOMES = frozenset({"NO_VALUE_AT_BOUNDARY", "NO_PRECEDING_INTERVAL"})
SILENT_OUTCOMES = frozenset({"SUPPRESSED_BY_GAP", "DROPPED"})
FAULT_KINDS = ("PAUSE", "EXCEPTION", "SENTINEL", "WRONG_UNIT_ID", "WRONG_TID")
_MBAP = struct.Struct(">HHHB")


def _instant(text: str) -> datetime:
    return datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def presented_value(row: ProfileRow, value: Fraction) -> Fraction:
    """The value a GX-layout register presents: quantized to its register quantum (amended TEL-03).

    Illustrative-block rows (status ILLUSTRATIVE) are never quantized.
    """
    if row.status == "ILLUSTRATIVE":
        return value
    scale = Fraction(10) ** row.exponent
    return quantize_half_even(value / scale, row.register_quantum) * scale


Words = list[list[int]]


@dataclass(frozen=True)
class _Hold:
    start: datetime
    end: datetime
    words: Words | None  # None: answer exception 0B
    observation: dict


class ObservationTimeline:
    def __init__(self, jsonl: Path, profile: FieldProfile) -> None:
        self.profile = profile
        rows_by_signal = {(row.device_id, row.signal_id): row for row in profile.rows}
        series: dict[str, list[dict]] = {row.row_id: [] for row in profile.rows}
        for line in Path(jsonl).read_text(encoding="utf-8").splitlines():
            observation = json.loads(line)
            row = rows_by_signal.get((observation["device_id"], observation["signal_id"]))
            if row is None:
                continue
            if observation["canonical_unit"] != row.source_unit:
                raise ValueError(f"row {row.row_id} is in {row.source_unit}, the observations in "
                                 f"{observation['canonical_unit']}")
            series[row.row_id].append(observation)
        self._holds: dict[str, list[_Hold]] = {}
        self._starts: dict[str, list[datetime]] = {}
        self.rows = {row.row_id: row for row in profile.rows}
        for row in profile.rows:
            observations = sorted(series[row.row_id], key=lambda o: o["source_sample_time"])
            if not observations:
                raise ValueError(f"row {row.row_id} has no observation in {jsonl}")
            holds = [self._hold(row, observation, observations[index + 1] if index + 1 < len(observations) else None)
                     for index, observation in enumerate(observations)]
            self._holds[row.row_id] = holds
            self._starts[row.row_id] = [hold.start for hold in holds]
        self.declared = {(register.unit_id, register.address + offset)
                         for row in profile.rows for register in row.registers for offset in range(register.words)}
        self.units = {register.unit_id for row in profile.rows for register in row.registers}

    @staticmethod
    def _hold(row: ProfileRow, observation: dict, following: dict | None) -> _Hold:
        at = _instant(observation["source_sample_time"])
        if row.reading_class == "STATE_SIGNAL":
            lead = timedelta(seconds=STATE_LEAD_SECONDS)
            end = _instant(following["source_sample_time"]) if following else at + timedelta(seconds=row.cadence_seconds)
            start, end = at - lead, end - lead
        else:
            start, end = at - timedelta(seconds=row.span_seconds), at
        outcome = observation["outcome"]
        if outcome == "REPORTED":
            raw = observation["reported_value"]
            value = raw if row.decode == "ENUM" else presented_value(row, Fraction(raw))
            words: Words | None = encode_value(row, value)
        elif outcome in SENTINEL_OUTCOMES:
            words = encode_sentinel(row)
        elif outcome in SILENT_OUTCOMES:
            words = None
        else:
            raise ValueError(f"unknown observation outcome {outcome!r}")
        return _Hold(start, end, words, observation)

    def hold_at(self, row_id: str, source_instant: datetime) -> _Hold | None:
        starts = self._starts[row_id]
        index = bisect.bisect_right(starts, source_instant) - 1
        if index >= 0:
            hold = self._holds[row_id][index]
            if hold.start <= source_instant < hold.end:
                return hold
        return None

    def observations(self, row_id: str) -> list[dict]:
        return [hold.observation for hold in self._holds[row_id]]

    def row_words(self, row: ProfileRow, source_instant: datetime) -> Words | None:
        hold = self.hold_at(row.row_id, source_instant)
        return encode_sentinel(row) if hold is None else hold.words

    def registers_at(self, source_instant: datetime) -> dict[tuple[int, int], int | tuple[str, int]]:
        served: dict[tuple[int, int], int | tuple[str, int]] = {}
        for row in self.profile.rows:
            words = self.row_words(row, source_instant)
            for index, register in enumerate(row.registers):
                for offset in range(register.words):
                    key = (register.unit_id, register.address + offset)
                    served[key] = ("EXCEPTION", 0x0B) if words is None else words[index][offset]
        return served


@dataclass(frozen=True)
class FaultWindow:
    start: datetime
    end: datetime
    kind: str
    row_id: str | None = None
    code: int | None = None

    def __post_init__(self) -> None:
        if self.kind not in FAULT_KINDS:
            raise ValueError(f"unknown fault kind {self.kind!r}")
        if self.kind in ("EXCEPTION", "SENTINEL") and self.row_id is None:
            raise ValueError(f"a {self.kind} fault names its row")
        if self.kind == "EXCEPTION" and self.code is None:
            raise ValueError("an EXCEPTION fault names its code")

    def active(self, instant: datetime) -> bool:
        return self.start <= instant < self.end


class GxEmulator:
    def __init__(self, timeline: ObservationTimeline, clock: Clock, *, host: str, port: int,
                 faults: Sequence[FaultWindow] = ()) -> None:
        self.timeline, self.clock, self.host, self.port = timeline, clock, host, port
        self.faults: list[FaultWindow] = list(faults)
        self.writes = 0
        self.requests = 0
        self._lock = threading.Lock()
        self._server: socketserver.ThreadingTCPServer | None = None
        self._thread: threading.Thread | None = None

    # --- lifecycle ---------------------------------------------------------------------------------------

    def start(self) -> int:
        emulator = self

        class Handler(socketserver.BaseRequestHandler):
            def handle(self) -> None:
                emulator._serve(self.request)

        server = socketserver.ThreadingTCPServer((self.host, self.port), Handler, bind_and_activate=False)
        server.allow_reuse_address = False
        server.daemon_threads = True
        server.server_bind()
        server.server_activate()
        self._server = server
        self._thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
        self._thread.start()
        self.port = server.server_address[1]
        return self.port

    def stop(self) -> None:
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
            self._server = None

    # --- protocol ----------------------------------------------------------------------------------------

    def _serve(self, connection) -> None:
        buffer = b""
        while True:
            try:
                chunk = connection.recv(4096)
            except OSError:
                return
            if not chunk:
                return
            buffer += chunk
            while len(buffer) >= _MBAP.size:
                tid, protocol, length, unit = _MBAP.unpack(buffer[:_MBAP.size])
                if protocol != 0 or not 2 <= length <= 254:
                    return  # not a Modbus TCP stream: drop the connection
                if len(buffer) < 6 + length:
                    break
                pdu, buffer = buffer[_MBAP.size:6 + length], buffer[6 + length:]
                answer = self._answer(tid, unit, pdu)
                if answer is not None:
                    try:
                        connection.sendall(answer)
                    except OSError:
                        return

    def _active(self, instant: datetime, kind: str) -> list[FaultWindow]:
        return [fault for fault in list(self.faults) if fault.kind == kind and fault.active(instant)]

    def _answer(self, tid: int, unit: int, pdu: bytes) -> bytes | None:
        with self._lock:
            self.requests += 1
        now = self.clock.now()
        function = pdu[0]
        if self._active(now, "PAUSE"):
            return None
        if function in WRITE_FUNCTIONS:
            with self._lock:
                self.writes += 1
        if unit not in self.timeline.units:
            body = bytes([function | 0x80, 0x0B])
        elif function not in (3, 4):
            body = bytes([function | 0x80, 0x01])
        else:
            body = self._read(now, unit, function, pdu)
        if self._active(now, "WRONG_UNIT_ID"):
            unit = (unit + 1) % 256
        if self._active(now, "WRONG_TID"):
            tid = (tid + 1) % 65536
        return _MBAP.pack(tid, 0, len(body) + 1, unit) + body

    def _read(self, now: datetime, unit: int, function: int, pdu: bytes) -> bytes:
        if len(pdu) != 5:
            return bytes([function | 0x80, 0x03])
        address, count = struct.unpack(">HH", pdu[1:5])
        if not 1 <= count <= MAX_COUNT:
            return bytes([function | 0x80, 0x03])
        wanted = [(unit, address + offset) for offset in range(count)]
        if any(key not in self.timeline.declared for key in wanted):
            return bytes([function | 0x80, 0x02])
        served = self.timeline.registers_at(now)
        for fault in self._active(now, "SENTINEL"):
            row = self.timeline.rows[fault.row_id]
            for index, register in enumerate(row.registers):
                for offset, word in enumerate(encode_sentinel(row)[index]):
                    served[(register.unit_id, register.address + offset)] = word
        for fault in self._active(now, "EXCEPTION"):
            row = self.timeline.rows[fault.row_id]
            covered = {(r.unit_id, r.address + o) for r in row.registers for o in range(r.words)}
            if covered & set(wanted):
                return bytes([function | 0x80, fault.code])
        words = []
        for key in wanted:
            word = served[key]
            if isinstance(word, tuple):
                return bytes([function | 0x80, word[1]])
            words.append(word)
        return bytes([function, 2 * count]) + struct.pack(f">{count}H", *words)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="gx_server", description="GX-shaped Modbus TCP emulator (test only)")
    parser.add_argument("--jsonl", required=True, type=Path)
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5020)
    parser.add_argument("--replay-start", required=True)
    parser.add_argument("--replay-rate", required=True, type=int)
    parser.add_argument("--replay-wall-epoch", required=True)
    parser.add_argument("--stop-at")
    args = parser.parse_args(argv)
    profile = load_profile(args.profile)
    clock = ReplayClock(_instant(args.replay_start), args.replay_rate, _wall_instant(args.replay_wall_epoch))
    stop_at = _instant(args.stop_at) if args.stop_at else None
    emulator = GxEmulator(ObservationTimeline(args.jsonl, profile), clock, host=args.host, port=args.port)
    port = emulator.start()
    print(f"READY {args.host}:{port}", flush=True)
    try:
        while stop_at is None or clock.now() < stop_at:
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        emulator.stop()
    return 0


def _wall_instant(text: str) -> datetime:
    """A wall epoch as `...Z`, with optional milliseconds."""
    for pattern in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return datetime.strptime(text, pattern).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    raise SystemExit(f"--replay-wall-epoch {text!r} is not a UTC instant ending in Z")


if __name__ == "__main__":
    sys.exit(main())
