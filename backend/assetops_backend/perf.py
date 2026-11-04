"""QW-1 (design proposal §14b): per-read timing inside one request.

A route opens `request(route)`; while it is open, `record(name, ms)` and `timed(name)` add `(calls, ms)` to that
request's recorder (a `ContextVar`, so a timer outside any request is a no-op). `finish` logs one structured JSON
line to the `assetops.perf` logger and, only when `ASSETOPS_SERVER_TIMING=1`, sets a `Server-Timing` header.
Timing never changes a return value, a failure or a response body.
"""
from __future__ import annotations

import json
import logging
import os
import sys
import time
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Iterator

LOG = logging.getLogger("assetops.perf")
SERVER_TIMING_ENV = "ASSETOPS_SERVER_TIMING"
#: The `Server-Timing` header carries the request total and at most this many named timers, largest first.
HEADER_TIMERS = 12
HANDLER_NAME = "assetops.perf.stderr"


def enable_log(stream: Any = None) -> logging.Handler:
    """CH-0 (CH0-R): give `assetops.perf` one INFO handler writing `assetops.perf {json}` lines to stderr, so a
    process that configures no logging (the tick CLI, `host/lab_app.py` under serve) emits them. Idempotent: an
    existing handler of this name is reused, never duplicated. `propagate` is off so a configured root logger
    does not print each line a second time."""
    for handler in LOG.handlers:
        if handler.get_name() == HANDLER_NAME:
            return handler
    handler = logging.StreamHandler(stream if stream is not None else sys.stderr)
    handler.set_name(HANDLER_NAME)
    handler.setFormatter(logging.Formatter("%(name)s %(message)s"))
    LOG.addHandler(handler)
    LOG.setLevel(logging.INFO)
    LOG.propagate = False
    return handler


class Recorder:
    def __init__(self, route: str) -> None:
        self.route = route
        self.started = time.perf_counter()
        self.timings: dict[str, list[float]] = {}  # name -> [calls, ms]

    def add(self, name: str, ms: float, calls: int = 1) -> None:
        entry = self.timings.setdefault(name, [0, 0.0])
        entry[0] += calls
        entry[1] += ms

    def total_ms(self) -> float:
        return (time.perf_counter() - self.started) * 1000

    def ranked(self) -> list[tuple[str, int, float]]:
        return sorted(((n, int(c), round(ms, 1)) for n, (c, ms) in self.timings.items()),
                      key=lambda x: (-x[2], x[0]))


_CURRENT: ContextVar[Recorder | None] = ContextVar("assetops_perf_recorder", default=None)


def record(name: str, ms: float, calls: int = 1) -> None:
    rec = _CURRENT.get()
    if rec is not None:
        rec.add(name, ms, calls)


@contextmanager
def timed(name: str) -> Iterator[None]:
    started = time.perf_counter()
    try:
        yield
    finally:
        record(name, (time.perf_counter() - started) * 1000)


class Laps:
    """Section timers for one straight-line body: each `lap(name)` records the time since the previous lap."""

    def __init__(self, prefix: str) -> None:
        self.prefix = prefix
        self.last = time.perf_counter()

    def __call__(self, name: str) -> None:
        now = time.perf_counter()
        record(f"{self.prefix}.{name}", (now - self.last) * 1000)
        self.last = now


@contextmanager
def request(route: str) -> Iterator[Recorder]:
    rec = Recorder(route)
    token = _CURRENT.set(rec)
    try:
        yield rec
    finally:
        _CURRENT.reset(token)


def server_timing_enabled() -> bool:
    return os.environ.get(SERVER_TIMING_ENV) == "1"


def server_timing(rec: Recorder, total_ms: float) -> str:
    parts = [f"total;dur={total_ms:.1f}"]
    for name, calls, ms in rec.ranked()[:HEADER_TIMERS]:
        safe = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in name)
        parts.append(f'{safe};dur={ms:.1f};desc="calls={calls}"')
    return ", ".join(parts)


def finish(rec: Recorder, response: Any = None, status: str = "ok") -> None:
    """One structured line per request; the header only behind the setting. Never raises."""
    total = rec.total_ms()
    try:
        LOG.info(json.dumps({"route": rec.route, "status": status, "total_ms": round(total, 1),
                             "timings": [{"name": n, "calls": c, "ms": ms} for n, c, ms in rec.ranked()]}))
        if response is not None and server_timing_enabled():
            response.headers["Server-Timing"] = server_timing(rec, total)
    except Exception:  # noqa: BLE001 - timing never fails a request
        pass


@contextmanager
def route(name: str, response: Any = None) -> Iterator[Recorder]:
    """`request` plus `finish` for a route body: the line is logged on success and on failure."""
    from . import read_scope  # CH5a-R R1: one request, one read scope (ledger + memo)

    status = "error"
    with request(name) as rec, read_scope.scope(name):
        try:
            yield rec
            status = "ok"
        finally:
            finish(rec, response if status == "ok" else None, status)
