"""The Modbus TCP poller: CLI and loop (build spec TEL-04, 0.6-0.8, Q-T19..Q-T36, TEL-T1-Q6).

    python -m assetops_field.modbus_poller --profile <json> --host <h> --port <p>
        --gateway-address <ipc address> --ipc-credential <gateway.credential> --snapshot-sha256 <hex>
        --expect-identity <json file> --state-dir <dir> [--read-timeout-s 1.0]
        [--replay-start <Z> --replay-rate <n> --replay-wall-epoch <Z> --stop-at <Z>]
        [--stop-at <Z>]

Exit codes: 0 after `--stop-at` and a final seal-and-release; 2 configuration
refused; 3 admission refused; 4 gateway unavailable at 10 consecutive publish
instants or more than 4096 retained report texts (Q-T33). The test-only crash
hook `ASSETOPS_FIELD_CRASH_AFTER_ADMIT=<n>` exits 9 right after the n-th admit,
before its seal, and only against a SIMULATED identity (Q-T28).

The poller reads, aggregates and admits. It never activates a snapshot and never
uploads: only the ops in `publish.OPS_USED` are reachable.
"""

from __future__ import annotations

import argparse
import hashlib
import heapq
import itertools
import json
import math
import os
import re
import secrets
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterator, Sequence

from assetops_contracts.source_envelope import canonical_json
from assetops_gateway.ipc import GatewayLink, GatewayRequestRefused, GatewayUnavailable

from assetops_field.aggregate import IntervalAggregator, Poll, PollOutcome, Result, StateSampler, expected_polls
from assetops_field.clock import ReplayClock, WallClock, utc_now
from assetops_field.modbus_tcp import ModbusTcpClient, ReadResult, classify, requests_for
from assetops_field.profile import FieldProfile, ProfileRefused, ProfileRow, load_profile
from assetops_field.publish import SOURCE_MODE, GatewayPublisher, IdentityMismatch
from assetops_field.report import build_report, instant_z, report_text

EXIT_OK, EXIT_CONFIG, EXIT_ADMISSION, EXIT_UNAVAILABLE, EXIT_CRASH = 0, 2, 3, 4, 9
CRASH_ENV = "ASSETOPS_FIELD_CRASH_AFTER_ADMIT"
RETAINED_LIMIT = 4096
UNAVAILABLE_LIMIT = 10
SEAL_REFUSAL_LIMIT = 3
COUNTERS = ("VALUE", "NO_VALUE", "FAILED", "NO_ANSWER", "CONFIG_FAULT", "SKIPPED_LATE")
ADMISSIONS = ("ADMITTED", "ALREADY_ADMITTED", "HELD")
RETRIED_EXCEPTIONS = frozenset({0x04, 0x06})
_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
_TOKEN = re.compile(r"[0-9a-f]{8}")


class ConfigurationRefused(Exception):
    """Exit 2: a bad argument or a refused configuration; nothing was admitted."""


class _Stop(Exception):
    def __init__(self, code: int, detail: str) -> None:
        self.code, self.detail = code, detail
        super().__init__(detail)


# --- session reference (TEL-T1-Q6, Q-T34, Q-T35) -------------------------------------------------------------


def new_session_ref(profile: FieldProfile, wall_now: datetime,
                    token: Callable[[], str] = lambda: secrets.token_hex(4)) -> str:
    """`field:<profile_id>:<profile_version>:<YYYYMMDDTHHMMSSZ>:<8 lowercase hex>` (wall time plus a random suffix)."""
    if wall_now.tzinfo is None or wall_now.utcoffset() != timedelta(0):
        raise ValueError("the session wall time is an aware UTC instant")
    suffix = token()
    if not isinstance(suffix, str) or not _TOKEN.fullmatch(suffix):
        raise ValueError(f"the session token must be 8 lowercase hex digits, not {suffix!r}")
    return f"field:{profile.profile_id}:{profile.profile_version}:{wall_now:%Y%m%dT%H%M%SZ}:{suffix}"


def session_stamp(session_ref: str) -> str:
    """`YYYYMMDDTHHMMSSZ-<8 hex>`, the raw-capture file stem (no colons)."""
    stamp, suffix = session_ref.split(":")[-2:]
    return f"{stamp}-{suffix}"


# --- small helpers -------------------------------------------------------------------------------------------


def _z(text: str, name: str) -> datetime:
    try:
        return datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except (TypeError, ValueError) as error:
        raise ConfigurationRefused(f"{name} {text!r} is not a whole-second UTC instant ending in Z") from error


def _wall_z(text: str, name: str) -> datetime:
    for pattern in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return datetime.strptime(text, pattern).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    raise ConfigurationRefused(f"{name} {text!r} is not a UTC instant ending in Z")


def _wall_text(instant: datetime) -> str:
    return instant.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.") + f"{instant.microsecond // 1000:03d}Z"


def _seconds(instant: datetime) -> int:
    return int((instant - _EPOCH).total_seconds())


def _at(seconds: int) -> datetime:
    return _EPOCH + timedelta(seconds=seconds)


def _write_json(path: Path, document: Any) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(canonical_json(document) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _emit(line: str) -> None:
    print(line, flush=True)


# --- the schedule (0.8) --------------------------------------------------------------------------------------

# Events are (instant, phase, row index, kind, payload). Phase 0 reads, phase 1
# closes and publishes, so a state boundary's attempts at B + 1 come before
# the publish at B. Every per-row stream is ascending; they are merged lazily
# so a wall-mode run without `--stop-at` never builds an unbounded list.


def _interval_events(index: int, row: ProfileRow, session_start: datetime,
                     stop_at: datetime | None) -> Iterator[tuple]:
    cadence = row.cadence_seconds
    end = (_seconds(session_start) // cadence + 1) * cadence
    while stop_at is None or end <= _seconds(stop_at):
        closes = _at(end)
        for instant in expected_polls(row, closes - timedelta(seconds=row.span_seconds)):
            if instant >= session_start:
                yield (instant, 0, index, "POLL", closes)
        yield (closes, 1, index, "CLOSE", closes)
        end += cadence


def _state_events(index: int, row: ProfileRow, session_start: datetime,
                  stop_at: datetime | None) -> Iterator[tuple]:
    cadence = row.cadence_seconds
    boundary = -(-_seconds(session_start) // cadence) * cadence  # a boundary equal to session_start is sampled
    while stop_at is None or boundary <= _seconds(stop_at):
        instant = _at(boundary)
        yield (instant, 0, index, "STATE", instant)
        yield (instant, 1, index, "CLOSE", instant)
        boundary += cadence


def schedule(profile: FieldProfile, session_start: datetime, stop_at: datetime | None) -> Iterator[tuple]:
    streams = []
    for index, row in enumerate(profile.rows):
        if row.reading_class == "INTERVAL_SIGNAL":
            streams.append(_interval_events(index, row, session_start, stop_at))
        else:
            streams.append(_state_events(index, row, session_start, stop_at))
    return heapq.merge(*streams, key=lambda event: event[:4])


# --- the poller ----------------------------------------------------------------------------------------------


class Poller:
    def __init__(self, *, profile: FieldProfile, clock: ReplayClock | WallClock, clock_document: dict[str, Any],
                 client: ModbusTcpClient, publisher: GatewayPublisher, state_dir: Path, session_start: datetime,
                 stop_at: datetime | None, crash_after_admit: int | None = None,
                 wall: Callable[[], datetime] = utc_now) -> None:
        self.profile, self.clock, self.client, self.publisher = profile, clock, client, publisher
        self.clock_document = clock_document
        self.state_dir, self.session_start, self.stop_at = state_dir, session_start, stop_at
        self.crash_after_admit, self.wall = crash_after_admit, wall
        self.raw_path = state_dir / f"raw-{session_stamp(publisher.session_ref)}.jsonl"
        self.status_path = state_dir / "status.json"
        self.skew = profile.state_skew_max_seconds
        self.samplers = {row.row_id: StateSampler(row, self.skew)
                         for row in profile.rows if row.reading_class == "STATE_SIGNAL"}
        self.aggregators: dict[tuple[int, datetime], IntervalAggregator] = {}
        self.state_results: dict[tuple[int, datetime], Result | None] = {}
        self.faulted: dict[str, datetime] = {}  # row_id -> the last instant whose result still closes
        self.counters = {name: 0 for name in COUNTERS}
        self.admissions = {name: 0 for name in ADMISSIONS}
        self.holds_by_kind: dict[str, int] = {}
        self.seal_refusals = 0
        self.consecutive_seal_refusals = 0
        self.consecutive_unavailable = 0
        self.retained: list[tuple[str, str]] = []  # (report_key, text), oldest first
        self.admit_calls = 0
        self.last_publish_instant: datetime | None = None

    # --- status --------------------------------------------------------------------------------------------

    def status(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile.profile_id,
            "profile_version": self.profile.profile_version,
            "profile_sha256": self.profile.sha256,
            "clock": self.clock_document,
            "session_ref": self.publisher.session_ref,
            "session_start": instant_z(self.session_start),
            "counters": dict(self.counters),
            "admissions": dict(self.admissions),
            "holds_by_kind": dict(sorted(self.holds_by_kind.items())),
            "seal_refusals": self.seal_refusals,
            "retained_reports": len(self.retained),
            "last_publish_instant": None if self.last_publish_instant is None else instant_z(self.last_publish_instant),
            "faulted_rows": [row.row_id for row in self.profile.rows if row.row_id in self.faulted],
        }

    def write_status(self) -> dict[str, Any]:
        document = self.status()
        _write_json(self.status_path, document)
        return document

    # --- reads ---------------------------------------------------------------------------------------------

    def _capture(self, *, at: datetime, wall_at: datetime, scheduled: datetime, row: ProfileRow,
                 request: tuple[int, int, int, int], attempt: int, result: ReadResult | None) -> None:
        unit_id, function, address, count = request
        if result is None:
            sent, answer, outcome = b"", None, "SKIPPED_LATE"
        else:
            sent, answer = result.request, result.response
            if result.kind == "WORDS":
                outcome = "WORDS"
            elif result.kind == "EXCEPTION":
                outcome = f"EXCEPTION_{result.exception_code:02X}"
            else:
                outcome = f"NO_ANSWER_{result.no_answer}"
        line = {
            "at": instant_z(at), "wall_at": _wall_text(wall_at), "scheduled_at": instant_z(scheduled),
            "row_id": row.row_id, "unit_id": unit_id, "function": function, "address": address, "count": count,
            "attempt": attempt, "request_hex": sent.hex() if result is not None else None,
            "response_hex": None if answer is None else answer.hex(),
            "sha256": hashlib.sha256(sent + (answer or b"")).hexdigest(),
            "outcome": outcome, "profile_sha256": self.profile.sha256,
        }
        with self.raw_path.open("a", encoding="utf-8", newline="\n") as raw:
            raw.write(canonical_json(line) + "\n")

    def _attempt(self, row: ProfileRow, scheduled: datetime, attempt: int) -> tuple[Poll, bool]:
        """One attempt: every request of the row, one raw line each. Returns the poll and whether it may retry."""
        results: list[ReadResult] = []
        sent_at: datetime | None = None
        for request in requests_for(row):
            at = self.clock.now()  # read just before the read's send
            wall_at = self.wall()
            sent_at = at if sent_at is None else sent_at
            result = self.client.read(*request)
            self._capture(at=at, wall_at=wall_at, scheduled=scheduled, row=row, request=request,
                          attempt=attempt, result=result)
            results.append(result)
        outcome, decoded = classify(results, row)
        retryable = any(
            (r.kind == "NO_ANSWER" and r.no_answer == "TIMEOUT")
            or (r.kind == "EXCEPTION" and r.exception_code in RETRIED_EXCEPTIONS)
            for r in results
        ) and outcome in (PollOutcome.NO_ANSWER, PollOutcome.FAILED)
        return Poll(sent_at, outcome, decoded), retryable

    def _skipped(self, row: ProfileRow, scheduled: datetime) -> None:
        at, wall_at = self.clock.now(), self.wall()
        for request in requests_for(row):
            self._capture(at=at, wall_at=wall_at, scheduled=scheduled, row=row, request=request, attempt=1,
                          result=None)
        self.counters["SKIPPED_LATE"] += 1

    def _fault(self, row: ProfileRow, closes: datetime) -> None:
        # Q-T24: the whole row stops for the session; the current result still closes.
        self.faulted.setdefault(row.row_id, closes)

    def poll_interval(self, index: int, row: ProfileRow, instant: datetime, closes: datetime) -> None:
        aggregator = self._aggregator(index, row, closes)
        window_end = instant + timedelta(seconds=row.poll_period_seconds // 2)
        self.clock.sleep_until(instant)
        if self.clock.now() >= window_end:
            self._skipped(row, instant)
            aggregator.add(Poll(instant, PollOutcome.NO_ANSWER, None))  # a late poll counts as missing
            return
        poll, retryable = self._attempt(row, instant, 1)
        if retryable and self.clock.now() < window_end:
            poll, _ = self._attempt(row, instant, 2)
        self.counters[poll.outcome.value] += 1
        if poll.outcome is PollOutcome.CONFIG_FAULT:
            self._fault(row, closes)
        # Q-T23: the interval poll carries its scheduled instant and only the final outcome.
        aggregator.add(Poll(instant, poll.outcome, poll.decoded))

    def poll_state(self, index: int, row: ProfileRow, boundary: datetime) -> None:
        first = boundary + timedelta(seconds=math.ceil(self.skew / 2))
        limit = boundary + timedelta(seconds=self.skew)
        self.clock.sleep_until(first)
        if self.clock.now() > limit:
            self._skipped(row, boundary)
            self.state_results[(index, boundary)] = None
            return
        attempts: list[Poll] = []
        poll, retryable = self._attempt(row, boundary, 1)
        attempts.append(poll)
        if retryable and self.clock.now() <= limit:
            poll, _ = self._attempt(row, boundary, 2)
            attempts.append(poll)
        self.counters[poll.outcome.value] += 1
        if poll.outcome is PollOutcome.CONFIG_FAULT:
            self._fault(row, boundary)
        self.state_results[(index, boundary)] = self.samplers[row.row_id].sample(boundary, attempts)

    def _aggregator(self, index: int, row: ProfileRow, closes: datetime) -> IntervalAggregator:
        key = (index, closes)
        if key not in self.aggregators:
            self.aggregators[key] = IntervalAggregator(row, self.session_start, closes)
        return self.aggregators[key]

    def close(self, index: int, row: ProfileRow, instant: datetime) -> Result | None:
        if row.reading_class == "INTERVAL_SIGNAL":
            aggregator = self.aggregators.pop((index, instant), None) or IntervalAggregator(row, self.session_start, instant)
            result = aggregator.close()
        else:
            result = self.state_results.pop((index, instant), None)
        faulted = self.faulted.get(row.row_id)
        if faulted is not None and instant > faulted:
            return None
        return result

    # --- publish (TEL-04 loop step 4) ----------------------------------------------------------------------

    def publish(self, instant: datetime, results: Sequence[tuple[int, ProfileRow, Result]]) -> None:
        built = []
        for index, row, result in results:
            report = build_report(self.profile, row, result)
            built.append((result.source_time, index, report.report_key, report_text(report)))
        built.sort(key=lambda item: (item[0], item[1]))
        pending = self.retained + [(key, text) for _, _, key, text in built]
        try:
            if pending:
                admissions = self.publisher.admit([text for _, text in pending])
                self.admit_calls += 1
                if self.crash_after_admit is not None and self.admit_calls == self.crash_after_admit:
                    os._exit(EXIT_CRASH)
                self.retained = []
                self._count(pending, admissions)
            sealed = self.publisher.seal_and_release()
        except GatewayUnavailable as unavailable:
            self.retained = pending
            self.consecutive_unavailable += 1
            print(f"FIELD-POLLER gateway unavailable at {instant_z(instant)}: {unavailable}", file=sys.stderr,
                  flush=True)
            self.last_publish_instant = instant
            self.write_status()
            if self.consecutive_unavailable >= UNAVAILABLE_LIMIT:
                raise _Stop(EXIT_UNAVAILABLE, f"gateway unavailable at {UNAVAILABLE_LIMIT} consecutive publish instants")
            if len(self.retained) > RETAINED_LIMIT:
                raise _Stop(EXIT_UNAVAILABLE, f"more than {RETAINED_LIMIT} retained report texts")
            return
        except GatewayRequestRefused as refused:
            self.last_publish_instant = instant
            self.write_status()
            raise _Stop(EXIT_ADMISSION, f"{refused.kind} at {refused.field}: {refused.detail}") from refused
        self.consecutive_unavailable = 0
        self.last_publish_instant = instant
        self._sealed(sealed)
        self.write_status()

    def _sealed(self, sealed: dict[str, Any]) -> None:
        if sealed["seal_refused"] is not None:
            self.seal_refusals += 1
            self.consecutive_seal_refusals += 1
            print(f"FIELD-POLLER SEAL_REFUSED {sealed['seal_refused']}", file=sys.stderr, flush=True)
            if self.consecutive_seal_refusals >= SEAL_REFUSAL_LIMIT:
                self.write_status()
                raise _Stop(EXIT_ADMISSION, f"SEAL_REFUSED at {SEAL_REFUSAL_LIMIT} consecutive publish instants")
        else:
            self.consecutive_seal_refusals = 0

    def _count(self, pending: Sequence[tuple[str, str]], admissions: Sequence[dict[str, Any]]) -> None:
        if len(admissions) != len(pending):
            raise _Stop(EXIT_ADMISSION, f"{len(pending)} reports admitted, {len(admissions)} answers")
        for (key, _), admission in zip(pending, admissions):
            outcome = admission["outcome"]
            if outcome not in self.admissions:
                raise _Stop(EXIT_ADMISSION, f"unknown admission outcome {outcome!r}")
            self.admissions[outcome] += 1
            if outcome == "HELD":
                kind = admission.get("kind")
                self.holds_by_kind[kind] = self.holds_by_kind.get(kind, 0) + 1
                _emit("FIELD-POLLER HOLD " + canonical_json(
                    {"report_key": key, "kind": kind, "field": admission.get("field"),
                     "detail": admission.get("detail")}))

    # --- the loop ------------------------------------------------------------------------------------------

    def run(self) -> None:
        events = schedule(self.profile, self.session_start, self.stop_at)
        for (instant, phase), group in itertools.groupby(events, key=lambda event: (event[0], event[1])):
            if phase == 0:
                for _, _, index, kind, payload in group:
                    row = self.profile.rows[index]
                    if row.row_id in self.faulted:
                        continue
                    if kind == "POLL":
                        self.poll_interval(index, row, instant, payload)
                    else:
                        self.poll_state(index, row, payload)
                continue
            results = []
            for _, _, index, _, _ in group:
                row = self.profile.rows[index]
                result = self.close(index, row, instant)
                if result is not None:
                    results.append((index, row, result))
            self.publish(instant, results)
        if self.stop_at is not None:
            self.clock.sleep_until(self.stop_at)
        try:
            sealed = self.publisher.seal_and_release()
        except GatewayRequestRefused as refused:
            self.write_status()
            raise _Stop(EXIT_ADMISSION, f"{refused.kind} at {refused.field}: {refused.detail}") from refused
        self._sealed(sealed)


# --- CLI -----------------------------------------------------------------------------------------------------


def _arguments(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="assetops_field.modbus_poller",
                                     description="Read-only Modbus TCP poller feeding a colocated gateway")
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", required=True, type=int)
    parser.add_argument("--gateway-address", required=True)
    parser.add_argument("--ipc-credential", required=True, type=Path)
    parser.add_argument("--snapshot-sha256", required=True)
    parser.add_argument("--expect-identity", required=True, type=Path)
    parser.add_argument("--state-dir", required=True, type=Path)
    parser.add_argument("--read-timeout-s", type=float, default=1.0)
    parser.add_argument("--replay-start")
    parser.add_argument("--replay-rate", type=int)
    parser.add_argument("--replay-wall-epoch")
    parser.add_argument("--stop-at")
    return parser.parse_args(argv)


def _clock(args: argparse.Namespace) -> tuple[ReplayClock | WallClock, dict[str, Any], datetime | None]:
    replay = (args.replay_start, args.replay_rate, args.replay_wall_epoch)
    stop_at = None if args.stop_at is None else _z(args.stop_at, "--stop-at")
    if all(value is None for value in replay):
        return WallClock(), {"mode": "WALL", "start": None, "rate": None, "wall_epoch": None}, stop_at
    if any(value is None for value in replay) or stop_at is None:
        raise ConfigurationRefused("--replay-start, --replay-rate, --replay-wall-epoch and --stop-at go together")
    start = _z(args.replay_start, "--replay-start")
    wall_epoch = _wall_z(args.replay_wall_epoch, "--replay-wall-epoch")
    try:
        clock = ReplayClock(start, args.replay_rate, wall_epoch)
    except ValueError as error:
        raise ConfigurationRefused(str(error)) from error
    if stop_at <= start:
        raise ConfigurationRefused("--stop-at must be after --replay-start")
    document = {"mode": "REPLAY", "start": instant_z(start), "rate": args.replay_rate,
                "wall_epoch": _wall_text(wall_epoch)}
    return clock, document, stop_at


def _crash_after_admit(expected: dict[str, Any]) -> int | None:
    value = os.environ.get(CRASH_ENV)
    if value is None:
        return None
    if expected.get("source_mode") != SOURCE_MODE:
        raise ConfigurationRefused(f"{CRASH_ENV} is honoured only against a {SOURCE_MODE} identity")
    if not value.isdigit() or int(value) < 1:
        raise ConfigurationRefused(f"{CRASH_ENV} must be a positive integer")
    return int(value)


def main(argv: Sequence[str] | None = None) -> int:
    args = _arguments(argv)
    try:
        profile = load_profile(args.profile)
        if profile.interface != "MODBUS_TCP":
            raise ConfigurationRefused(f"profile interface {profile.interface} is not MODBUS_TCP")
        clock, clock_document, stop_at = _clock(args)
        if not re.fullmatch(r"[0-9a-f]{64}", args.snapshot_sha256):
            raise ConfigurationRefused("--snapshot-sha256 is 64 lowercase hex digits")
        if args.read_timeout_s <= 0:
            raise ConfigurationRefused("--read-timeout-s must be positive")
        expected = json.loads(args.expect_identity.read_text(encoding="utf-8"))
        crash_after_admit = _crash_after_admit(expected)
        args.state_dir.mkdir(parents=True, exist_ok=True)
        session_path = args.state_dir / "session.json"
        previous = json.loads(session_path.read_text(encoding="utf-8")) if session_path.exists() else None
        link = GatewayLink(args.gateway_address, args.ipc_credential)
        publisher = GatewayPublisher(link, args.snapshot_sha256, new_session_ref(profile, utc_now()), expected)
        publisher.check_identity()
    except ProfileRefused as refused:
        print(f"FIELD-POLLER profile refused: {refused}", file=sys.stderr, flush=True)
        return EXIT_CONFIG
    except IdentityMismatch as mismatch:
        print(f"FIELD-POLLER identity mismatch: {mismatch}", file=sys.stderr, flush=True)
        return EXIT_CONFIG
    except (ConfigurationRefused, OSError, json.JSONDecodeError, KeyError) as refused:
        print(f"FIELD-POLLER configuration refused: {refused}", file=sys.stderr, flush=True)
        return EXIT_CONFIG

    previous_ref = None if previous is None else previous["session_ref"]
    if previous_ref is not None:
        try:
            publisher.release_previous(previous_ref)
        except GatewayRequestRefused as refused:
            print(f"FIELD-POLLER release_previous refused: {refused}", file=sys.stderr, flush=True)
            return EXIT_ADMISSION

    session_start = clock.now()
    if isinstance(clock, ReplayClock) and session_start < clock.start:
        session_start = clock.start
    _write_json(session_path, {"session_ref": publisher.session_ref, "session_start": instant_z(session_start),
                               "profile_sha256": profile.sha256})
    clock.sleep_until(session_start)
    poller = Poller(profile=profile, clock=clock, clock_document=clock_document,
                    client=ModbusTcpClient(args.host, args.port, timeout_s=args.read_timeout_s),
                    publisher=publisher, state_dir=args.state_dir, session_start=session_start, stop_at=stop_at,
                    crash_after_admit=crash_after_admit)
    _emit("FIELD-POLLER START " + canonical_json({
        "profile_id": profile.profile_id, "profile_version": profile.profile_version,
        "profile_sha256": profile.sha256, "clock": clock_document, "session_ref": publisher.session_ref,
        "session_start": instant_z(session_start), "previous_ref": previous_ref,
    }))
    code = EXIT_OK
    try:
        poller.run()
    except _Stop as stop:
        print(f"FIELD-POLLER stopped: {stop.detail}", file=sys.stderr, flush=True)
        code = stop.code
    finally:
        poller.client.close()
    _emit(f"FIELD-POLLER EXIT {code} " + canonical_json(poller.write_status()))
    return code


if __name__ == "__main__":
    sys.exit(main())
