"""5b unit 3 (spec §4.1; D-5B.9, D-5B.11, D-5B.12): the portfolio bridge. Pure.

Each row is one set of Sites against the same set: the Sites whose own row has an effect ("k of n"), the others named
with their reasons. Effects (money on the root) always add; a factor's own actual, target and gap add only when its
registry row composes by `SUM`, so a price or a rate never adds across Sites (D-5B.11). Currencies are never added
together. Operator-level budget lines are listed, never added (D-5A.8); every target check that disagrees is kept.
"""
from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal, localcontext
from types import MappingProxyType

from assetops_backend.structure import registry as _registry
from assetops_backend.structure.attribution.bridge import _HOME_ORDER, BridgeRow
from assetops_backend.structure.attribution.rules import BRIDGE_ROOTS, CURRENCY_MISMATCH, context
from assetops_backend.structure.attribution.site import SiteBridge
from assetops_backend.structure.check import StructureError
from assetops_backend.structure.evaluate import NOT_AVAILABLE, ORIGIN_ORDER, weakest
from assetops_backend.structure.read import NOT_DECLARED
from assetops_backend.structure.targets.lines import BudgetLines
from assetops_backend.structure.targets.read import TargetCheck

NOT_SPLIT = ("NOT_SPLIT",)  # the reason a Site whose root has an effect is not in k: its figure is not split this far


@dataclass(frozen=True)
class PortfolioRow:
    key: str                     # the factor id; "residual:<parent>" for residual rows
    kind: str                    # the Sites' row kind (ROOT, TERM, VOLUME, PRICE, RESIDUAL)
    actual: Decimal | None       # sums over the included Sites, only when the factor's row has
    target: Decimal | None       # composes == "SUM" (D-5B.11); else None; None for RESIDUAL
    gap: Decimal | None
    effect: Decimal | None       # sum (always: money on the root); None only on a currency mismatch
    currency: str | None
    note: str | None             # "CURRENCY_MISMATCH:<a>,<b>" or None
    evidence: str
    origins: tuple[str, ...]
    k: int
    n: int
    out: tuple[tuple[str, tuple[str, ...]], ...]   # Sites not in k, in `asked` order, with their reasons
    carried: tuple[str, ...]     # included Sites (asked order) whose own row rests on a carried leaf (D-5B.12)


@dataclass(frozen=True)
class PortfolioBridge:
    month: str
    structure_key: str
    structure_version: int
    asked: tuple[str, ...]                          # every Site code asked, in order
    sites: Mapping[str, SiteBridge]                 # the MINI_GRID Sites, in `asked` order
    rows: Mapping[str, Mapping[str, PortfolioRow]]  # root -> key -> row, keys in first-seen depth-first order
    by_home: Mapping[str, Decimal]                  # Σ of the included Sites' by_home, same key order
    disagreements: tuple[tuple[str, TargetCheck], ...]   # every check with agrees False, `asked` order
    portfolio_lines: BudgetLines                    # operator-level lines, listed, never added (D-5A.8)


def _key(row: BridgeRow) -> str:
    return f"residual:{row.parent}" if row.kind == "RESIDUAL" else row.factor_id


def _walk(row: BridgeRow) -> Iterator[BridgeRow]:
    yield row
    for child in row.rows:
        yield from _walk(child)


def _rests_on_carried(row: BridgeRow) -> bool:
    return any(r.carried for r in _walk(row))


def _index(root: BridgeRow) -> dict[str, BridgeRow]:
    """One Site's tree by key, depth-first; a key twice under one root is refused (handshake R11)."""
    out: dict[str, BridgeRow] = {}
    for r in _walk(root):
        k = _key(r)
        if k in out:
            raise ValueError(f"REPEATED_FACTOR:{k}")
        out[k] = r
    return out


def _sum(values: Sequence[Decimal]) -> Decimal:
    total = Decimal(0)
    for v in values:
        total += v
    return total.copy_abs() if total == 0 else total


def _row(key: str, per_site: Mapping[str, BridgeRow], sites: Mapping[str, SiteBridge], root: str,
         asked: Sequence[str], sites_excluded: Mapping[str, tuple[str, ...]], structure_key: str) -> PortfolioRow:
    reg = _registry.REGISTRIES[structure_key]
    kind = next(iter(per_site.values())).kind
    included = [c for c in asked if c in per_site and per_site[c].effect is not None]
    out = []
    for code in asked:
        if code in included:
            continue
        if code in sites_excluded:
            reasons = tuple(sites_excluded[code])
        elif code not in sites:
            reasons = NOT_DECLARED
        else:
            r = sites[code].roots[root]
            if r.effect is None:
                reasons = (tuple(f"actual:{leaf}" for leaf in r.unobserved_actual)
                           + tuple(f"target:{leaf}" for leaf in r.unobserved_target))
            else:
                reasons = NOT_SPLIT
        out.append((code, reasons))
    rows = [per_site[c] for c in included]
    held = {o for r in rows for o in r.origins}
    origins = tuple(o for o in ORIGIN_ORDER if o in held)
    evidence = weakest([r.evidence for r in rows]) if rows else NOT_AVAILABLE
    carried = tuple(c for c in included if _rests_on_carried(per_site[c]))
    currencies = sorted({r.currency for r in rows if r.currency is not None})
    actual = target = gap = effect = None
    note = None
    if len(currencies) > 1:
        note = CURRENCY_MISMATCH + ",".join(currencies)
        currency = None
    else:
        currency = currencies[0] if currencies else None
        if rows:
            effect = _sum([r.effect for r in rows])
            if kind != "RESIDUAL" and reg.row(key).composes == "SUM":
                actual, target, gap = (_sum([r.actual for r in rows]), _sum([r.target for r in rows]),
                                       _sum([r.gap for r in rows]))
    if effect is None:
        evidence = NOT_AVAILABLE
    return PortfolioRow(key, kind, actual, target, gap, effect, currency, note, evidence, origins, len(included),
                        len(asked), tuple(out), carried)


def portfolio_bridge(sites: Mapping[str, SiteBridge], asked: Sequence[str],
                     sites_excluded: Mapping[str, tuple[str, ...]], portfolio_lines: BudgetLines,
                     month: str, structure_key: str, structure_version: int) -> PortfolioBridge:
    """Spec §4.1: per root, per key seen in any Site's tree, the sum over the Sites whose row has an effect."""
    asked = tuple(asked)
    for code, sb in sites.items():
        if (sb.month, sb.structure_key, sb.structure_version) != (month, structure_key, structure_version):
            raise StructureError("STRUCTURE_COMPOSE", structure_key, code)
    ordered = {c: sites[c] for c in asked if c in sites}
    rows: dict[str, Mapping[str, PortfolioRow]] = {}
    with localcontext(context()):
        for root in BRIDGE_ROOTS[structure_key]:
            indexed = {c: _index(sb.roots[root]) for c, sb in ordered.items()}
            keys: list[str] = []
            for tree in indexed.values():
                keys += [k for k in tree if k not in keys]
            rows[root] = MappingProxyType({
                k: _row(k, {c: tree[k] for c, tree in indexed.items() if k in tree}, ordered, root, asked,
                        sites_excluded, structure_key)
                for k in keys})
        first = BRIDGE_ROOTS[structure_key][0]
        homes: dict[str, list[Decimal]] = {}
        head = rows[first].get(first)
        if head is not None and head.note is None:
            for code in asked:
                if code in ordered and ordered[code].roots[first].effect is not None:
                    for h, v in ordered[code].by_home.items():
                        homes.setdefault(h, []).append(v)
        by_home = MappingProxyType({h: _sum(homes[h]) for h in _HOME_ORDER if h in homes})
    disagreements = tuple((code, check) for code in asked if code in ordered
                          for check in ordered[code].targets.checks if not check.agrees)
    return PortfolioBridge(month, structure_key, structure_version, asked, MappingProxyType(ordered),
                           MappingProxyType(rows), by_home, disagreements, portfolio_lines)


__all__ = ["PortfolioBridge", "PortfolioRow", "portfolio_bridge"]
