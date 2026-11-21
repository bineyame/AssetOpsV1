"""5b unit 1 (spec §2.2 to §2.4; D-5B.1 to D-5B.6, D-5B.8, D-5B.14): the bridge. Pure, no I/O.

`bridge(registry, actual, target, root)` splits one root's gap (actual minus target) into its drivers, from the root
down. A sum splits into its signed terms (AR1); a two-factor product splits into a volume effect at target price, then
a price effect at actual volume (AR2). Each row carries `scale`, the money on the root per unit of its own gap, so a
quantity's parts get money at target price (D-5B.3). The split goes as far down as both sides are observed and stops
there, saying why; a residual appears only beside a stated heading some of whose terms are not observed (D-5B.4).
Unknown is never zero: a row with a missing side has no gap and no effect. Every step runs in one 34-digit context;
nothing is quantised, and agreement is judged by `rules.agree` (D-5B.14).
"""
from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal, localcontext
from types import MappingProxyType

from assetops_backend.outcomes.catalogue import CATEGORIES
from assetops_backend.structure.attribution.rules import (
    CURRENCY_MISMATCH, DETAIL_NOT_AVAILABLE, GAP_NOT_AVAILABLE, PRICE_NOT_DECLARED, RECORD_AND_FACTORS_DIFFER,
    RULE_NOT_DECLARED, SPLIT_INEXACT, UNPLACED, agree, context)
from assetops_backend.structure.evaluate import (
    NEUTRAL, NOT_AVAILABLE, ORIGIN_ORDER, FactorValue, weakest)
from assetops_backend.structure.expressions import Bin, Expr, Neg, Ref
from assetops_backend.structure.registry import HOMES, Registry
from assetops_contracts.canonical.units import Unit

#: Spec §2.4: `by_home` keys, the categories in canonical order, then the placements, then `UNPLACED`.
_HOME_ORDER = (*CATEGORIES, HOMES["above"], HOMES["calendar"], UNPLACED)


@dataclass(frozen=True)
class BridgeRow:
    factor_id: str | None          # None only for RESIDUAL
    parent: str | None             # the factor this row splits; None for ROOT
    kind: str                      # KINDS
    rule: str | None               # "AR1" (TERM, RESIDUAL), "AR2" (VOLUME, PRICE), None (ROOT)
    home: str | None               # the factor's home category (RESIDUAL: the parent's); None when the row has none
    actual: Decimal | None
    target: Decimal | None         # the factor's own values (None for RESIDUAL)
    gap: Decimal | None            # actual - target, in the factor's unit; None when either is None, and for RESIDUAL
    scale: Decimal | None          # money on the root per unit of gap; None for RESIDUAL
    effect: Decimal | None         # scale x gap; RESIDUAL: the remainder; None only when gap is None (not RESIDUAL)
    currency: str | None           # the root's currency (every effect is in it)
    evidence: str                  # spec §2.4; NOT_AVAILABLE when effect is None
    origins: tuple[str, ...]       # spec §2.4, in ORIGIN_ORDER
    carried: bool                  # a leaf whose actual is carried at its target (missing.carried_as == "TARGET")
    split: str                     # SPLITS
    reason: str | None             # None unless NOT_SPLIT
    unobserved_actual: tuple[str, ...]   # step 6: the inputs (leaves, or stated nodes whose record is
    unobserved_target: tuple[str, ...]   # missing) that would fill this side; sorted as the side gives them
    rows: tuple["BridgeRow", ...]  # the split, in expression order; RESIDUAL last


# ---------------------------------------------------------------- small helpers


def _norm(v: Decimal | None) -> Decimal | None:
    """Spec §2.2: a zero is `copy_abs()`-normalised, never -0."""
    return v.copy_abs() if v is not None and v == 0 else v


def _money_dimension(unit: Unit) -> bool:
    return any(d == "MONEY" and e != 0 for d, e in unit.exponents)


def _is_price(unit: Unit) -> bool:
    """Step 3: money per unit of something: `("MONEY", 1)` among the exponents, and not money itself."""
    return ("MONEY", 1) in unit.exponents and not unit.is_money


def _label(values: Sequence[FactorValue]) -> tuple[str, tuple[str, ...]]:
    """D-5B.6: the weakest evidence and the union of origins (in `ORIGIN_ORDER`) of the values an amount rests on."""
    held = {o for v in values for o in v.origins}
    return weakest([v.evidence for v in values]), tuple(o for o in ORIGIN_ORDER if o in held)


def _sum(values: Sequence[Decimal]) -> Decimal:
    total = Decimal(0)
    for v in values:
        total += v
    return total


def _terms(expr: Expr, sign: int = 1) -> list[tuple[int, Expr]] | None:
    """Step 3: the signed terms of a sum, or None when the shape is not a signed sum of `Ref`s and `Ref * Ref`s."""
    if isinstance(expr, Bin) and expr.op in ("+", "-"):
        left = _terms(expr.left, sign)
        right = _terms(expr.right, sign if expr.op == "+" else -sign)
        return None if left is None or right is None else left + right
    if isinstance(expr, Neg):
        return _terms(expr.operand, -sign)
    if isinstance(expr, Ref):
        return [(sign, expr)]
    if isinstance(expr, Bin) and expr.op == "*" and isinstance(expr.left, Ref) and isinstance(expr.right, Ref):
        return [(sign, expr)]
    return None


def _factors(term: Expr) -> tuple[str, ...]:
    return (term.name,) if isinstance(term, Ref) else (term.left.name, term.right.name)


# ---------------------------------------------------------------- the engine (spec §2.3)


class _Bridge:
    def __init__(self, registry: Registry, actual: Mapping[str, FactorValue], target: Mapping[str, FactorValue],
                 currency: str | None) -> None:
        self.reg = registry
        self.a = actual
        self.t = target
        self.currency = currency

    def _home(self, factor_id: str) -> str | None:
        home = self.reg.row(factor_id).home
        return None if home is None else home.category

    def row(self, f: str, parent: str | None, kind: str, rule: str | None, scale: Decimal,
            label_values: Sequence[FactorValue]) -> BridgeRow:
        a, t = self.a[f], self.t[f]
        reg_row = self.reg.row(f)
        carried = reg_row.is_leaf and a.missing is not None and a.missing.carried_as == "TARGET"
        scale = _norm(scale)

        def made(gap, effect, split, reason, unobserved=((), ()), rows=()) -> BridgeRow:
            evidence, origins = _label(label_values)
            if effect is None:
                evidence = NOT_AVAILABLE
            return BridgeRow(f, parent, kind, rule, self._home(f), a.value, t.value, _norm(gap), scale,
                             _norm(effect), self.currency, evidence, origins, carried, split, reason,
                             tuple(unobserved[0]), tuple(unobserved[1]), tuple(rows))

        # 1. Gap
        if a.value is None or t.value is None:
            return made(None, None, "NOT_SPLIT", GAP_NOT_AVAILABLE, (a.missing_leaves, t.missing_leaves))
        if _money_dimension(reg_row.unit) and a.currency != t.currency:
            currencies = ",".join(sorted(c for c in (a.currency, t.currency) if c is not None))
            return made(None, None, "NOT_SPLIT", CURRENCY_MISMATCH + currencies)
        gap = a.value - t.value
        effect = scale * gap
        # 2. Leaf
        if reg_row.is_leaf:
            return made(gap, effect, "LEAF", None)
        # 3. Shape
        terms = _terms(self.reg.parsed[f])
        if terms is None:
            return made(gap, effect, "NOT_SPLIT", RULE_NOT_DECLARED)
        products: dict[int, tuple[str, str]] = {}  # term index -> (quantity, price)
        for i, (_, term) in enumerate(terms):
            if isinstance(term, Bin):
                pair = (term.left.name, term.right.name)
                prices = [n for n in pair if _is_price(self.reg.row(n).unit)]
                if len(prices) != 1:
                    return made(gap, effect, "NOT_SPLIT", PRICE_NOT_DECLARED)
                price = prices[0]
                quantity = pair[1] if pair[0] == price else pair[0]
                products[i] = (quantity, price)
        # 4. A record that its factors do not explain
        for side in (a, t):
            if side.stated and side.computed is not None and not agree(side.computed, side.value):
                return made(gap, effect, "NOT_SPLIT", RECORD_AND_FACTORS_DIFFER)
        # 5. Terms
        children: list[BridgeRow] = []
        whole = True
        for i, (sign, term) in enumerate(terms):
            names = _factors(term)
            if any(self.a[n].evidence == NEUTRAL and self.t[n].evidence == NEUTRAL for n in names):
                continue  # neutral: an option-only factor gives no row (D-5B.5)
            if any(self.a[n].value is None or self.t[n].value is None for n in names):
                whole = False
                continue
            m = scale * sign
            if i in products:
                q, p = products[i]
                aq, tq, ap, tp = self.a[q], self.t[q], self.a[p], self.t[p]
                children.append(self.row(q, f, "VOLUME", "AR2", m * tp.value, (aq, tq, tp)))
                children.append(self.row(p, f, "PRICE", "AR2", m * aq.value, (ap, tp, aq)))
            else:
                g = term.name
                children.append(self.row(g, f, "TERM", "AR1", m, (self.a[g], self.t[g])))
        # 6. The split
        if whole:
            effects = [c.effect for c in children]
            if any(e is None for e in effects) or not agree(_sum(effects), effect):
                return made(gap, effect, "NOT_SPLIT", SPLIT_INEXACT)
            return made(gap, effect, "SPLIT", None, rows=children)
        unobserved = (a.detail_missing if a.stated else (), t.detail_missing if t.stated else ())
        if not children:
            return made(gap, effect, "NOT_SPLIT", DETAIL_NOT_AVAILABLE, unobserved)
        if any(c.effect is None for c in children):
            return made(gap, effect, "NOT_SPLIT", SPLIT_INEXACT)
        evidence, origins = _label((a, t))
        # D-5B.15 (mid-build Q1): a RESIDUAL carries NOT_SPLIT / DETAIL_NOT_AVAILABLE.
        residual = BridgeRow(None, f, "RESIDUAL", "AR1", self._home(f), None, None, None, None,
                             _norm(effect - _sum([c.effect for c in children])), self.currency, evidence, origins,
                             False, "NOT_SPLIT", DETAIL_NOT_AVAILABLE, unobserved[0], unobserved[1], ())
        return made(gap, effect, "SPLIT", None, rows=[*children, residual])


def bridge(registry: Registry, actual: Mapping[str, FactorValue], target: Mapping[str, FactorValue],
           root: str) -> BridgeRow:
    """Spec §2.3: the root row (`kind` ROOT, `scale` 1) and its split, from `actual` and `target` (each a full
    `evaluate` result over `registry`)."""
    a, t = actual[root], target[root]
    currency = a.currency if a.currency == t.currency else None
    with localcontext(context()):
        return _Bridge(registry, actual, target, currency).row(root, None, "ROOT", None, Decimal(1), (a, t))


def lowest(row: BridgeRow) -> tuple[BridgeRow, ...]:
    """Depth-first: the rows with split LEAF or NOT_SPLIT, and RESIDUALs."""
    def walk(r: BridgeRow) -> Iterator[BridgeRow]:
        if r.kind == "RESIDUAL" or r.split in ("LEAF", "NOT_SPLIT"):
            yield r
        else:
            for child in r.rows:
                yield from walk(child)
    return tuple(walk(row))


def by_home(row: BridgeRow) -> Mapping[str, Decimal]:
    """D-5B.8: the effects of `lowest(row)` summed per each row's own home (RESIDUAL: its parent's; none:
    `UNPLACED`); keys in `CATEGORIES` order, then `ABOVE`, `CALENDAR`, `UNPLACED`. Empty when `row` has no effect."""
    if row.effect is None:
        return MappingProxyType({})
    totals: dict[str, list[Decimal]] = {}
    for r in lowest(row):
        if r.effect is not None:
            totals.setdefault(r.home if r.home is not None else UNPLACED, []).append(r.effect)
    with localcontext(context()):
        return MappingProxyType({k: _norm(_sum(totals[k])) for k in _HOME_ORDER if k in totals})
