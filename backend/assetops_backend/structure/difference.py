"""6c (`specs/6c-option-evaluator/spec.md` §2; D-P6.3, D-P6.4): the difference an option's leaf changes make, folded
through a registry's expressions. Pure, no I/O.

`difference(registry, base, changes)` gives, for each changed leaf and each node of the outcome's dependency closure
that rests on one, the option side minus the no-action side for the period. Both sides read the same leaves; the
no-action side is `evaluate(registry, base)` with no stated map, so a counterfactual runs through the mechanism and
never through a record that states a total. A change is folded by the product rule, so a factor that did not change
needs no value; anything else needed and missing makes the change missing and names what was missing. A change of
exactly zero is zero; it is never a missing value read as zero.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from decimal import ROUND_CEILING, ROUND_FLOOR, Decimal, localcontext
from types import MappingProxyType
from typing import TYPE_CHECKING

from assetops_backend.structure.check import StructureError
from assetops_backend.structure.evaluate import (ORIGIN_ORDER, FactorValue, LeafValue, _context, blocks_of, evaluate,
                                                 weakest)
from assetops_backend.structure.expressions import Bin, Call, Expr, Neg, Num, Ref
from assetops_backend.structure.registry import Registry

if TYPE_CHECKING:
    from assetops_contracts.canonical.units import Unit

OUTCOME_FACTOR = "contribution"
_NEUTRAL = "NEUTRAL"
_CURRENCY = "currency"  # the missing name of a currency mismatch (spec §2)


@dataclass(frozen=True)
class Delta:
    factor_id: str
    change: Decimal | None              # option side minus no-action side, monthly; None when an input is missing
    unit: Unit
    currency: str | None                # of the money values used; None for a non-money row
    missing_leaves: tuple[str, ...]     # registry order; () when change is not None
    used: tuple[str, ...]               # factor ids whose values the change needed, registry order
    evidence: str                       # weakest of the used values and the changed leaves
    origins: tuple[str, ...]            # ORIGIN_ORDER order
    zero_denominators: tuple[str, ...] = ()  # D-P6.37: nodes whose fold met a zero denominator, registry order


@dataclass(frozen=True)
class LeafChange:                       # D-P6.3: a delta on a leaf, never a replacement value
    delta: Decimal | None               # option side minus no-action side, monthly; None when it cannot be known
    evidence: str
    sources: tuple[str, ...]
    origins: tuple[str, ...]            # ORIGIN_ORDER order
    missing: tuple[str, str] | None     # (record_kind, source_family) when delta is None, else None
    currency: str | None = None         # D-P6.62: the currency of a stated money level, else None


@dataclass(frozen=True)
class _V:
    """A folded value: the value (None when missing), the names it lacks, the factors it read and its parts'
    evidence (so the option-only neutral short cut of `evaluate` is mirrored exactly)."""

    value: Decimal | None
    missing: frozenset[str] = frozenset()
    used: frozenset[str] = frozenset()
    evidence: tuple[str, ...] = ()
    zero: frozenset[str] = frozenset()  # D-P6.37: the nodes whose fold met a zero denominator

    @property
    def neutral_zero(self) -> bool:
        return (self.value is not None and self.value == 0 and bool(self.evidence)
                and all(e == _NEUTRAL for e in self.evidence))


def _merge(parts: tuple[_V, ...], value: Decimal | None) -> _V:
    return _V(value, frozenset().union(*(p.missing for p in parts)), frozenset().union(*(p.used for p in parts)),
              tuple(e for p in parts for e in p.evidence), frozenset().union(*(p.zero for p in parts)))


def _fold_v(expr: Expr, read: Callable[[str], _V], owner: str | None) -> _V:
    """`evaluate`'s arithmetic over one expression; a zero denominator is missing and names `owner`."""
    if isinstance(expr, Num):
        return _V(expr.value)
    if isinstance(expr, Ref):
        return read(expr.name)
    if isinstance(expr, Neg):
        inner = _fold_v(expr.operand, read, owner)
        return _merge((inner,), None if inner.value is None else -inner.value)
    if isinstance(expr, Bin):
        left, right = _fold_v(expr.left, read, owner), _fold_v(expr.right, read, owner)
        if expr.op == "*":
            for operand in (left, right):
                if operand.neutral_zero:
                    return operand
        if left.value is None or right.value is None:
            return _merge((left, right), None)
        if expr.op == "+":
            return _merge((left, right), left.value + right.value)
        if expr.op == "-":
            return _merge((left, right), left.value - right.value)
        if expr.op == "*":
            return _merge((left, right), left.value * right.value)
        if right.value == 0:
            named = _merge((left, right), None)
            mark = frozenset({owner}) if owner else frozenset()
            return _V(None, named.missing | mark, named.used, named.evidence, named.zero | mark)
        return _merge((left, right), left.value / right.value)
    if isinstance(expr, Call):
        args = tuple(_fold_v(a, read, owner) for a in expr.args)
        if any(a.value is None for a in args):
            return _merge(args, None)
        values = [a.value for a in args]
        if expr.func == "min":
            return _merge(args, min(values))
        if expr.func == "max":
            return _merge(args, max(values))
        rounding = ROUND_FLOOR if expr.func == "floor" else ROUND_CEILING
        return _merge(args, values[0].to_integral_value(rounding=rounding))
    raise StructureError("STRUCTURE_EXPRESSION", "", repr(expr))


def _fold(expr: Expr, values: Mapping[str, Decimal | None]) -> Decimal | None:
    """The value of `expr` over plain values (the parity test's view of `_fold_v`)."""
    with localcontext(_context()):
        return _fold_v(expr, lambda name: _V(values[name]), None).value


class _Difference:
    def __init__(self, registry: Registry, base: Mapping[str, LeafValue], changes: Mapping[str, LeafChange],
                 v0: Mapping[str, FactorValue]) -> None:
        self.reg = registry
        self.base = base
        self.changes = changes
        self.v0 = v0
        self.over = frozenset(blocks_of(registry, tuple(changes)))  # nodes resting on a changed leaf
        self._d: dict[str, _V] = {}
        self._v1: dict[str, _V] = {}

    # the no-action side
    def read0(self, name: str) -> _V:
        fv = self.v0[name]
        if fv.value is None:
            return _V(None, frozenset(fv.missing_leaves) or frozenset({name}), frozenset(), (fv.evidence,))
        return _V(fv.value, frozenset(), frozenset({name}), (fv.evidence,))

    def val0(self, expr: Expr, owner: str) -> _V:
        return _fold_v(expr, self.read0, owner)

    # the option side
    def read1(self, name: str) -> _V:
        if name in self.changes:
            ch, base = self.changes[name], self.base[name].value
            value = None if ch.delta is None or base is None else base + ch.delta
            return _V(value, frozenset() if value is not None else frozenset({name}), frozenset({name}),
                      (ch.evidence,))
        if name in self.over:
            if name not in self._v1:
                self._v1[name] = _fold_v(self.reg.parsed[name], self.read1, name)
            return self._v1[name]
        return self.read0(name)

    def val1(self, expr: Expr, owner: str) -> _V:
        return _fold_v(expr, self.read1, owner)

    # the difference
    def d_ref(self, name: str) -> _V:
        if name in self.changes:
            delta = self.changes[name].delta
            return _V(delta, frozenset({name}) if delta is None else frozenset(), frozenset({name}))
        if name not in self.over:
            return _V(Decimal(0))
        if name not in self._d:
            self._d[name] = self.d(self.reg.parsed[name], name)
        return self._d[name]

    def d(self, expr: Expr, owner: str) -> _V:
        if isinstance(expr, Num):
            return _V(Decimal(0))
        if isinstance(expr, Ref):
            return self.d_ref(expr.name)
        if isinstance(expr, Neg):
            inner = self.d(expr.operand, owner)
            return _merge((inner,), None if inner.value is None else -inner.value)
        if isinstance(expr, Bin) and expr.op in ("+", "-"):
            a, b = self.d(expr.left, owner), self.d(expr.right, owner)
            if a.value is None or b.value is None:
                return _merge((a, b), None)
            return _merge((a, b), a.value + b.value if expr.op == "+" else a.value - b.value)
        if isinstance(expr, Bin) and expr.op == "*":
            da, db = self.d(expr.left, owner), self.d(expr.right, owner)
            parts = [da, db]
            t1: Decimal | None = Decimal(0)
            if not _exactly_zero(da):
                v1b = self.val1(expr.right, owner)
                parts.append(v1b)
                t1 = None if da.value is None or v1b.value is None else da.value * v1b.value
            t2: Decimal | None = Decimal(0)
            if not _exactly_zero(db):
                v0a = self.val0(expr.left, owner)
                parts.append(v0a)
                t2 = None if db.value is None or v0a.value is None else v0a.value * db.value
            return _merge(tuple(parts), None if t1 is None or t2 is None else t1 + t2)
        # a / b, min, max, ceil, floor: zero when no operand changed; otherwise the two sides folded
        operands = (expr.left, expr.right) if isinstance(expr, Bin) else expr.args
        ds = tuple(self.d(o, owner) for o in operands)
        if all(_exactly_zero(x) for x in ds):
            return _merge(ds, Decimal(0))
        one, zero = self.val1(expr, owner), self.val0(expr, owner)
        return _merge(ds + (one, zero), None if one.value is None or zero.value is None else one.value - zero.value)

    # the result
    def delta(self, factor_id: str) -> Delta:
        row = self.reg.row(factor_id)
        got = self.d_ref(factor_id)
        order = {r.factor_id: i for i, r in enumerate(self.reg.rows)}
        used = tuple(sorted(got.used, key=order.__getitem__))
        evidence: list[str] = []
        origins: set[str] = set()
        currencies: set[str] = set()
        for name in used:
            parts: list[LeafValue | FactorValue | LeafChange] = []
            if name in self.changes:
                parts.append(self.changes[name])
                if self.base[name].value is not None:
                    parts.append(self.v0[name])
            else:
                parts.append(self.v0[name])
            for part in parts:
                evidence.append(part.evidence)
                origins.update(part.origins)
                if part.currency is not None:
                    currencies.add(part.currency)
        change = got.value
        missing = () if change is not None else tuple(sorted(got.missing, key=lambda n: order.get(n, len(order))))
        currency = None
        if row.money:
            if len(currencies) > 1:
                change, missing = None, (_CURRENCY,)
            elif currencies:
                currency = next(iter(currencies))
        if change is not None and change == 0:
            change = change.copy_abs()  # never -0
        zero = tuple(sorted(got.zero, key=lambda n: order.get(n, len(order))))
        return Delta(factor_id, change, row.unit, currency, missing, used, weakest(evidence),
                     tuple(o for o in ORIGIN_ORDER if o in origins), zero)


def _exactly_zero(v: _V) -> bool:
    return v.value is not None and v.value == 0


def _closure(registry: Registry, factor_id: str) -> frozenset[str]:
    seen: set[str] = set()
    stack = [factor_id]
    while stack:
        name = stack.pop()
        if name in seen:
            continue
        seen.add(name)
        stack.extend(registry.row(name).children)
    return frozenset(seen)


def difference(registry: Registry, base: Mapping[str, LeafValue],
               changes: Mapping[str, LeafChange], *, also: tuple[str, ...] = ()) -> Mapping[str, Delta]:
    """Each changed leaf and each node of the outcome's closure (and of each `also` factor's, D-P6.57) resting on
    one, in registry order; the outcome factor is always in scope (spec §2)."""
    leaf_ids = {row.factor_id for row in registry.rows if row.is_leaf}
    for name in changes:
        if name not in leaf_ids:
            raise StructureError("STRUCTURE_LEAF_INPUT", registry.structure_key, str(name))
    v0 = evaluate(registry, base)
    with localcontext(_context()):
        run = _Difference(registry, base, changes, v0)
        closure = _closure(registry, OUTCOME_FACTOR).union(*(_closure(registry, f) for f in also))
        scope = [row.factor_id for row in registry.rows
                 if row.factor_id in changes or row.factor_id == OUTCOME_FACTOR
                 or (row.factor_id in run.over and row.factor_id in closure)]
        return MappingProxyType({factor_id: run.delta(factor_id) for factor_id in scope})


__all__ = ["OUTCOME_FACTOR", "Delta", "LeafChange", "difference"]
