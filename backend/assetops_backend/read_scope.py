"""One request, one read scope (CH5a-R R1).

`perf.route` enters a `ReadScope` for every board, summary and Portfolio route. The scope holds

- the **ledger**: every producer read executed in the request, keyed on (name, argument key), with its count and
  ms. A memo hit is not an execution and is counted under `hits`, so "no same-argument read runs twice in one
  request" is `max(ledger counts) <= 1`;
- the **memo**: `memo(name, fn, *args)` runs `fn(*args)` once per (name, argument key) and hands every later
  caller the same deep-frozen value. A call that raises is never memoised.

Outside a scope there is no ledger, no memo and no change: `memo` simply calls `fn`.
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import fields, is_dataclass, replace
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum
from types import MappingProxyType
from typing import Any, Callable, Iterator, Mapping
from uuid import UUID

_SCALARS = (str, int, float, bool, bytes, type(None), Decimal, UUID, datetime, date, Enum)


def freeze(value: Any) -> Any:
    """A deep-frozen copy: dicts become read-only mappings over frozen values, lists and sets become tuples and
    frozensets, and a dataclass gets every field frozen (QW-R: a memoised value is shared, so it is never handed
    out mutable)."""
    if isinstance(value, _SCALARS):
        return value
    if isinstance(value, (MappingProxyType, dict)) or isinstance(value, Mapping):
        return MappingProxyType({k: freeze(v) for k, v in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(freeze(v) for v in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(freeze(v) for v in value)
    if is_dataclass(value) and not isinstance(value, type):
        changes = {f.name: freeze(getattr(value, f.name)) for f in fields(value) if f.init}
        try:
            return replace(value, **changes)
        except Exception:  # noqa: BLE001 - a dataclass whose __post_init__ rejects frozen fields stays as built
            return value
    return value


def thaw(value: Any) -> Any:
    """A plain mutable copy of a frozen value, for a consumer that edits what it was given."""
    if isinstance(value, Mapping):
        return {k: thaw(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return [thaw(v) for v in value]
    return value


def arg_key(args: tuple[Any, ...]) -> tuple[Any, ...]:
    """A hashable key over call arguments: hashable values as themselves, everything else by `repr`."""
    out = []
    for a in args:
        try:
            hash(a)
            out.append(a)
        except TypeError:
            out.append(repr(a))
    return tuple(out)


class ReadScope:
    def __init__(self, route: str) -> None:
        self.route = route
        self.ledger: dict[tuple[str, tuple[Any, ...]], int] = {}
        self.ms: dict[str, float] = {}
        self.hits: dict[str, int] = {}
        self._memo: dict[tuple[str, tuple[Any, ...]], Any] = {}
        self.snapshot: tuple[Any, datetime] | None = None  # CH5c-R3 R3: (connection, read instant)
        #: CH5c-R7 C1: (boundary, at) of every registered clock comparison (`within`, `since`)
        self.boundaries: list[tuple[datetime, datetime]] = []
        #: CH5c2 fix M-A: every DB read instant the compose captured through `read_instant` (the liveness floor)
        self.instants: list[datetime] = []

    def count(self, name: str, key: tuple[Any, ...], ms: float) -> None:
        k = (name, key)
        self.ledger[k] = self.ledger.get(k, 0) + 1
        self.ms[name] = self.ms.get(name, 0.0) + ms

    def names(self) -> dict[str, int]:
        """Executions per read name, over every argument key."""
        out: dict[str, int] = {}
        for (name, _), n in self.ledger.items():
            out[name] = out.get(name, 0) + n
        return out

    def max_per_key(self, exclude: tuple[str, ...] = ()) -> int:
        return max((n for (name, _), n in self.ledger.items() if name not in exclude), default=0)

    def repeated(self) -> list[tuple[str, tuple[Any, ...], int]]:
        return [(name, key, n) for (name, key), n in self.ledger.items() if n > 1]

    def top_ms(self, n: int = 10) -> list[tuple[str, float]]:
        return sorted(self.ms.items(), key=lambda kv: -kv[1])[:n]


_SCOPE: ContextVar[ReadScope | None] = ContextVar("assetops_read_scope", default=None)


def current() -> ReadScope | None:
    return _SCOPE.get()


@contextmanager
def scope(route: str) -> Iterator[ReadScope]:
    """Enter a read scope; a nested `scope` reuses the outer one (one request, one scope)."""
    outer = _SCOPE.get()
    if outer is not None:
        yield outer
        return
    sc = ReadScope(route)
    token = _SCOPE.set(sc)
    try:
        yield sc
    finally:
        _SCOPE.reset(token)


@contextmanager
def fresh(route: str) -> Iterator[ReadScope]:
    """A new read scope even inside an outer one (CH5c-R5 R5-1(b)): the stored-route compose starts its memo after
    the watermark transaction, so no memo entry filled before the watermark can reach a stored body."""
    sc = ReadScope(route)
    token = _SCOPE.set(sc)
    try:
        yield sc
    finally:
        _SCOPE.reset(token)


def ledger() -> ReadScope | None:
    return _SCOPE.get()


def record(name: str, args: tuple[Any, ...], ms: float) -> None:
    """Count one executed read in the current scope's ledger (no-op outside a scope)."""
    sc = _SCOPE.get()
    if sc is not None:
        sc.count(name, arg_key(args), ms)


def memo(name: str, fn: Callable[..., Any], *args: Any, key: tuple[Any, ...] | None = None) -> Any:
    """`fn(*args)` once per (name, key) in the current scope, deep-frozen; a raising call is not memoised.

    `key` overrides the argument key (for a call whose identity is a subset of its arguments)."""
    sc = _SCOPE.get()
    if sc is None:
        return fn(*args)
    k = (name, arg_key(args) if key is None else arg_key(key))
    if k in sc._memo:
        sc.hits[name] = sc.hits.get(name, 0) + 1
        return sc._memo[k]
    started = time.perf_counter()
    out = fn(*args)
    sc.count(name, k[1], (time.perf_counter() - started) * 1000)
    frozen = freeze(out)
    sc._memo[k] = frozen
    return frozen


def memoised(name: str, key: tuple[Any, ...]) -> bool:
    """CH5c-R3 R1: whether `memo(name, ..., key=key)` would hit in the current scope (a prefetch is skipped)."""
    sc = _SCOPE.get()
    return sc is not None and (name, arg_key(key)) in sc._memo


@contextmanager
def snapshot(c: Any, read_at: datetime) -> Iterator[None]:
    """CH5c-R3 R3: bind the current scope to connection `c`'s REPEATABLE READ snapshot and its read instant
    `read_at` for the duration of the block (no-op outside a scope)."""
    sc = _SCOPE.get()
    if sc is None:
        yield
        return
    previous = sc.snapshot
    sc.snapshot = (c, read_at)
    try:
        yield
    finally:
        sc.snapshot = previous


def clock() -> datetime:
    """CH5c-R7 C1: the one wall-clock read of compose code (aware UTC). Tests move it with `monkeypatch`."""
    return datetime.now(timezone.utc)


def read_instant(db_value: datetime) -> datetime:
    """CH5c2-R1 Q1: a compose read instant captured from the DB (`SELECT clock_timestamp()`, the snapshot's first
    statement). The named seam of every such capture: identity in the product; the C4 sweep moves it with the
    clock."""
    sc = _SCOPE.get()
    if sc is not None:
        sc.instants.append(db_value)
    return db_value


def _register(boundary: datetime, at: datetime) -> None:
    sc = _SCOPE.get()
    if sc is not None:
        sc.boundaries.append((boundary, at))


def within(start: datetime | None, end: datetime | None, at: datetime) -> bool:
    """CH5c-R7 C1: `start <= at < end` (half-open; a None bound is unbounded). Registers `start` when `at < start`
    and `end` when `start <= at < end`: the earliest instant at which the verdict can change."""
    if start is not None and at < start:
        _register(start, at)
        return False
    if end is not None and at >= end:
        return False
    if end is not None:
        _register(end, at)
    return True


def since(t: datetime, lookback: timedelta, at: datetime) -> bool:
    """CH5c-R7 C1: `at - lookback <= t <= at`. Registers `t` when `t > at` (it turns true at `t`), else
    `t + lookback` (it turns false just after; the inclusive end is the instant itself, never +1 µs)."""
    if t > at:
        _register(t, at)
        return False
    _register(t + lookback, at)
    return at - lookback <= t


def boundaries() -> tuple[tuple[datetime, datetime], ...]:
    sc = _SCOPE.get()
    return () if sc is None else tuple(sc.boundaries)


#: CH5c-R7 F4: the route a stored-route compose is running for (set by `chain.response_store`); a test-only audit
#: hook reads it, so its scope is exactly the compose.
COMPOSING: ContextVar[str | None] = ContextVar("assetops_composing", default=None)


@contextmanager
def composing(route: str) -> Iterator[None]:
    token = COMPOSING.set(route)
    try:
        yield
    finally:
        COMPOSING.reset(token)


def at_or_after_snapshot(c: Any, cutoff: datetime) -> bool:
    """True when `c` is the scope's bound snapshot connection and `cutoff` is at or after its read instant."""
    sc = _SCOPE.get()
    bound = None if sc is None else sc.snapshot
    return bound is not None and bound[0] is c and cutoff >= bound[1]
