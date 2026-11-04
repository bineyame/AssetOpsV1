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
from datetime import date, datetime
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
