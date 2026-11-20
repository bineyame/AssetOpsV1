"""3B3: the structure evaluator (spec §2; D-3B3.1, D-3B3.2, D-3B3.7, D-3B3.13 to D-3B3.16). Pure, no I/O.

`evaluate(registry, leaves)` folds a registry bottom-up from one Site's leaf values; `compose(registry, per_site)`
sums the `SUM` factors across Sites, factor by factor, naming the Sites left out. Unknown is never zero: a node over
any leaf with no value has no value, and the only short cut is an option-only neutral 0 in a product (D-3B3.15).
Every arithmetic step runs in one local decimal context; nothing is quantised.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from decimal import ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_EVEN, Context, Decimal, localcontext
from fractions import Fraction
from types import MappingProxyType

from assetops_backend.structure.check import StructureError
from assetops_backend.structure.expressions import Bin, Call, Expr, Neg, Num, Ref
from assetops_backend.structure.registry import Registry
from assetops_contracts.canonical.units import Unit

#: D-3B3.2: strongest first. A node takes the latest of its parts in this order.
EVIDENCE_ORDER = ("RECORDED", "MEASURED", "DECLARED", "DERIVED", "ESTIMATED", "MODELLED", "NOT_AVAILABLE")
#: D-3B3.15: an option-only neutral; outside the order, skipped by the fold.
NEUTRAL = "NEUTRAL"
NOT_AVAILABLE = "NOT_AVAILABLE"
ESTIMATED = "ESTIMATED"
CAUSES = ("NOT_RECEIVED", "NOT_CONNECTED", "NOT_CALCULATED_YET")
CARRIED_AS = ("TARGET", "ASSUMPTION", "RESIDUAL")
_ASSUMED = ("TARGET", "ASSUMPTION")
_RANK = {name: rank for rank, name in enumerate(EVIDENCE_ORDER)}


def _context() -> Context:
    return Context(prec=34, rounding=ROUND_HALF_EVEN)


@dataclass(frozen=True)
class Missing:
    """The `factor_value.missing` fields (integration-source-to-canonical-design.md §6.2); `slice` and `trigger` are
    pack-only and left out. `note` holds a price reason or the pack's note (P10)."""

    record_kind: str
    source_family: str
    cause: str
    carried_as: str | None
    blocks: tuple[str, ...]
    record_words: str | None
    assumption: str | None
    note: str | None = None


@dataclass(frozen=True)
class Coverage:
    covered: int
    expected: int  # Site-local days of the month
    grades: Mapping[str, int] = field(default_factory=dict)

    @property
    def share(self) -> Fraction:
        """R7: `covered / expected`; an `expected` of 0 is share 0."""
        return Fraction(0) if self.expected == 0 else Fraction(self.covered, self.expected)


@dataclass(frozen=True)
class LeafValue:
    value: Decimal | None
    evidence: str
    sources: tuple[str, ...]
    coverage: Coverage | None
    missing: Missing | None
    currency: str | None


@dataclass(frozen=True)
class FactorValue:
    factor_id: str
    value: Decimal | None
    unit: Unit
    evidence: str
    sources: tuple[str, ...]
    coverage: Coverage | None
    missing: Missing | None
    missing_leaves: tuple[str, ...]
    assumed_leaves: tuple[str, ...]
    currency: str | None


@dataclass(frozen=True)
class SiteStructure:
    site_code: str
    month: str
    structure_key: str
    structure_version: int
    values: Mapping[str, FactorValue]


@dataclass(frozen=True)
class PortfolioValue:
    value: FactorValue
    included: tuple[str, ...]
    excluded: Mapping[str, tuple[str, ...]]


@dataclass(frozen=True)
class Composition:
    values: Mapping[str, PortfolioValue]
    not_composed: tuple[str, ...]
    sites: tuple[str, ...]
    sites_excluded: Mapping[str, tuple[str, ...]]


# ---------------------------------------------------------------- folds (spec §2.1)


def weakest(evidence: Sequence[str]) -> str:
    """The weakest non-NEUTRAL class; NEUTRAL when every part is NEUTRAL (or there is none)."""
    ranked = [e for e in evidence if e != NEUTRAL]
    return max(ranked, key=_RANK.__getitem__) if ranked else NEUTRAL


def _min_coverage(coverages: Sequence[Coverage | None]) -> Coverage | None:
    """R7: the whole Coverage of the part with the smallest share; the first such part on a tie; None ignored."""
    best: Coverage | None = None
    for c in coverages:
        if c is not None and (best is None or c.share < best.share):
            best = c
    return best


def _union(*groups: Sequence[str]) -> tuple[str, ...]:
    return tuple(sorted({x for g in groups for x in g}))


def blocks_of(registry: Registry, leaves: Sequence[str]) -> tuple[str, ...]:
    """The nodes resting on any of `leaves`, breadth-first and nearest first, in registry order within a level (the
    pack's `ancestors()`; R11)."""
    start = set(leaves)
    out: list[str] = []
    frontier = list(leaves)
    nodes = [row.factor_id for row in registry.rows if not row.is_leaf]
    while frontier:
        reached = {p for f in frontier for p in registry.parents.get(f, ())}
        nxt = [n for n in nodes if n in reached and n not in out and n not in start]
        out += nxt
        frontier = nxt
    return tuple(out)


# ---------------------------------------------------------------- leaf-value checks (spec §2.2; R6)


def _money_dimension(unit: Unit) -> bool:
    return any(d == "MONEY" and e != 0 for d, e in unit.exponents)


def _check_leaf(registry: Registry, factor_id: str, leaf: LeafValue) -> None:
    key = registry.structure_key
    row = registry.row(factor_id)
    missing = leaf.missing
    carried = None if missing is None else missing.carried_as
    if ((leaf.value is None and missing is None)
            or (leaf.value is not None and missing is not None and carried is None)
            or (leaf.value is None and carried is not None)
            or (missing is not None and missing.blocks)):
        raise StructureError("STRUCTURE_MISSING", key, factor_id)
    if ((leaf.evidence not in _RANK and leaf.evidence != NEUTRAL)
            or (carried in _ASSUMED and leaf.evidence != ESTIMATED)
            or (leaf.value is None and leaf.evidence != NOT_AVAILABLE)
            or (leaf.evidence == NEUTRAL and (row.absent != "OPTION_ONLY" or leaf.value != row.neutral))):
        raise StructureError("STRUCTURE_EVIDENCE", key, factor_id)
    if (_money_dimension(row.unit) and leaf.value is not None and leaf.currency is None
            and leaf.evidence != NEUTRAL):
        raise StructureError("STRUCTURE_CURRENCY", key, factor_id)


# ---------------------------------------------------------------- the fold over one expression


@dataclass(frozen=True)
class _Part:
    """A sub-expression's value and what it rests on. A literal has no evidence, sources or leaves of its own."""

    value: Decimal | None
    evidence: tuple[str, ...]
    sources: tuple[str, ...]
    coverages: tuple[Coverage | None, ...]
    missing_leaves: tuple[str, ...]
    assumed_leaves: tuple[str, ...]
    currencies: tuple[str, ...]
    problem: Missing | None = None  # a node-level missing (zero denominator) found inside the expression

    @property
    def neutral_zero(self) -> bool:
        return (self.value is not None and self.value == 0 and bool(self.evidence)
                and all(e == NEUTRAL for e in self.evidence))


def _merge(parts: Sequence[_Part], value: Decimal | None) -> _Part:
    problem = next((p.problem for p in parts if p.problem is not None), None)
    return _Part(
        None if problem is not None else value,
        tuple(e for p in parts for e in p.evidence),
        _union(*(p.sources for p in parts)),
        tuple(c for p in parts for c in p.coverages),
        _union(*(p.missing_leaves for p in parts)),
        _union(*(p.assumed_leaves for p in parts)),
        tuple(c for p in parts for c in p.currencies),
        problem,
    )


def _text(expr: Expr, nested: bool = False) -> str:
    """The canonical text of an expression, for the ZERO_DENOMINATOR cause."""
    if isinstance(expr, Num):
        return str(expr.value)
    if isinstance(expr, Ref):
        return expr.name
    if isinstance(expr, Neg):
        return f"-{_text(expr.operand, True)}"
    if isinstance(expr, Call):
        return f"{expr.func}({', '.join(_text(a) for a in expr.args)})"
    inner = f"{_text(expr.left, True)} {expr.op} {_text(expr.right, True)}"
    return f"({inner})" if nested else inner


class _Evaluation:
    def __init__(self, registry: Registry, leaves: Mapping[str, LeafValue]) -> None:
        self.reg = registry
        self.leaves = leaves
        self.done: dict[str, FactorValue] = {}

    def factor(self, factor_id: str) -> FactorValue:
        if factor_id not in self.done:
            row = self.reg.row(factor_id)
            self.done[factor_id] = self._leaf(factor_id) if row.is_leaf else self._node(factor_id)
        return self.done[factor_id]

    def _leaf(self, factor_id: str) -> FactorValue:
        row = self.reg.row(factor_id)
        leaf = self.leaves[factor_id]
        missing = leaf.missing
        if missing is not None:  # P6: blocks are computed here, never typed
            missing = dataclasses.replace(missing, blocks=blocks_of(self.reg, (factor_id,)))
        carried = None if missing is None else missing.carried_as
        return FactorValue(factor_id, leaf.value, row.unit, leaf.evidence, _union(leaf.sources), leaf.coverage,
                           missing, (factor_id,) if leaf.value is None else (),
                           (factor_id,) if carried in _ASSUMED else (), leaf.currency)

    def _part_of(self, factor_id: str) -> _Part:
        fv = self.factor(factor_id)
        return _Part(fv.value, (fv.evidence,), fv.sources, (fv.coverage,), fv.missing_leaves, fv.assumed_leaves,
                     () if fv.currency is None else (fv.currency,))

    def _expr(self, expr: Expr) -> _Part:
        if isinstance(expr, Num):
            return _Part(expr.value, (), (), (), (), (), ())
        if isinstance(expr, Ref):
            return self._part_of(expr.name)
        if isinstance(expr, Neg):
            inner = self._expr(expr.operand)
            return _merge((inner,), None if inner.value is None else -inner.value)
        if isinstance(expr, Bin):
            left, right = self._expr(expr.left), self._expr(expr.right)
            if expr.op == "*":
                for operand in (left, right):  # D-3B3.15: the only short cut
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
            if right.value == 0:  # D-3B3.7: never infinite, never zero
                zero = Missing(f"ZERO_DENOMINATOR:{_text(expr.right)}", "OBSERVER", "NOT_CALCULATED_YET", None,
                               (), None, None)
                return dataclasses.replace(_merge((left, right), None), problem=zero)
            return _merge((left, right), left.value / right.value)
        if isinstance(expr, Call):
            args = [self._expr(a) for a in expr.args]
            if any(a.value is None for a in args):
                return _merge(args, None)
            values = [a.value for a in args]
            if expr.func == "min":
                return _merge(args, min(values))
            if expr.func == "max":
                return _merge(args, max(values))
            rounding = ROUND_FLOOR if expr.func == "floor" else ROUND_CEILING
            return _merge(args, values[0].to_integral_value(rounding=rounding))
        raise StructureError("STRUCTURE_EXPRESSION", self.reg.structure_key, repr(expr))

    def _node(self, factor_id: str) -> FactorValue:
        row = self.reg.row(factor_id)
        part = self._expr(self.reg.parsed[factor_id])
        blocks = blocks_of(self.reg, (factor_id,))
        currencies = sorted(set(part.currencies))
        missing = None if part.problem is None else dataclasses.replace(part.problem, blocks=blocks)
        value = part.value
        if value is not None and len(currencies) > 1:  # D-3B3.16: nothing is converted
            missing = Missing(f"CURRENCY_MISMATCH:{','.join(currencies)}", "OBSERVER", "NOT_CALCULATED_YET", None,
                              blocks, None, None)
            value = None
        if value is not None and value == 0:
            value = value.copy_abs()  # P10: never -0
        evidence = NOT_AVAILABLE if value is None else weakest(part.evidence)
        blocked_by = part.missing_leaves if value is None else ()
        if value is None and not blocked_by:  # M1: a node-level cause names this node, so ancestors keep a reason
            blocked_by = (factor_id,)
        return FactorValue(factor_id, value, row.unit, evidence, part.sources, _min_coverage(part.coverages),
                           missing, blocked_by, part.assumed_leaves,
                           currencies[0] if len(currencies) == 1 else None)


def evaluate(registry: Registry, leaves: Mapping[str, LeafValue]) -> Mapping[str, FactorValue]:
    """Every factor of `registry` from one Site's `leaves` (spec §2.2), in registry order."""
    key = registry.structure_key
    leaf_ids = [row.factor_id for row in registry.rows if row.is_leaf]
    for factor_id in leaf_ids:
        if factor_id not in leaves:
            raise StructureError("STRUCTURE_LEAF_INPUT", key, factor_id)  # a caller bug, never a zero
    for factor_id in leaf_ids:
        _check_leaf(registry, factor_id, leaves[factor_id])
    with localcontext(_context()):
        run = _Evaluation(registry, leaves)
        out = {row.factor_id: run.factor(row.factor_id) for row in registry.rows}
    return MappingProxyType(out)


# ---------------------------------------------------------------- the portfolio (spec §2.3)


def _sum(values: Sequence[Decimal]) -> Decimal:
    total = values[0]
    for v in values[1:]:
        total += v
    return total


def _summed_coverage(coverages: Sequence[Coverage | None]) -> Coverage | None:
    held = [c for c in coverages if c is not None]
    if not held:
        return None
    grades: dict[str, int] = {}
    for c in held:
        for grade, n in c.grades.items():
            grades[grade] = grades.get(grade, 0) + n
    return Coverage(sum(c.covered for c in held), sum(c.expected for c in held), MappingProxyType(grades))


def _compose_factor(registry: Registry, factor_id: str, per_site: Mapping[str, SiteStructure]) -> PortfolioValue:
    row = registry.row(factor_id)
    included = tuple(s for s, ss in per_site.items() if ss.values[factor_id].value is not None)
    excluded = MappingProxyType({s: ss.values[factor_id].missing_leaves for s, ss in per_site.items()
                                 if s not in included})
    if not included:  # D-3B3.13: never 0
        missing_leaves = _union(*([f"{s}:{leaf}" for leaf in leaves] for s, leaves in excluded.items()))
        fv = FactorValue(factor_id, None, row.unit, NOT_AVAILABLE, (), None, None, missing_leaves, (), None)
        return PortfolioValue(fv, included, excluded)
    parts = [per_site[s].values[factor_id] for s in included]
    sources = _union(*(p.sources for p in parts))
    coverage = _summed_coverage([p.coverage for p in parts])
    assumed = _union(*([f"{s}:{leaf}" for leaf in p.assumed_leaves] for s, p in zip(included, parts)))
    currencies = sorted({p.currency for p in parts if p.currency is not None})
    if len(currencies) > 1:
        missing = Missing(f"CURRENCY_MISMATCH:{','.join(currencies)}", "OBSERVER", "NOT_CALCULATED_YET", None, (),
                          None, None)
        fv = FactorValue(factor_id, None, row.unit, NOT_AVAILABLE, sources, coverage, missing, (), assumed, None)
        return PortfolioValue(fv, included, excluded)
    value = _sum([p.value for p in parts])
    if value == 0:
        value = value.copy_abs()
    fv = FactorValue(factor_id, value, row.unit, weakest([p.evidence for p in parts]), sources, coverage, None, (),
                     assumed, currencies[0] if currencies else None)
    return PortfolioValue(fv, included, excluded)


def compose(registry: Registry, per_site: Mapping[str, SiteStructure]) -> Composition:
    """The `SUM` factors summed over the Sites that have them, each naming the Sites left out (D-3B3.13)."""
    key = registry.structure_key
    for site_code, ss in per_site.items():
        if ss.structure_key != key or ss.structure_version != registry.version:
            raise StructureError("STRUCTURE_COMPOSE", key, site_code)
    with localcontext(_context()):
        values = {row.factor_id: _compose_factor(registry, row.factor_id, per_site)
                  for row in registry.rows if row.composes == "SUM"}
    not_composed = tuple(row.factor_id for row in registry.rows if row.composes != "SUM")
    return Composition(MappingProxyType(values), not_composed, tuple(per_site), MappingProxyType({}))


__all__ = [
    "CARRIED_AS", "CAUSES", "EVIDENCE_ORDER", "NEUTRAL", "Composition", "Coverage", "FactorValue", "LeafValue",
    "Missing", "PortfolioValue", "SiteStructure", "blocks_of", "compose", "evaluate", "weakest",
]
