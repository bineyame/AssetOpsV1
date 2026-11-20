"""5a units 2 and 3 (spec `specs/5a-targets/spec.md` §3.2, §4; D-5A.4 to D-5A.10, D-5A.13, D-5A.15; D-4B.18).

The target side of a Site's structure for a month, evaluated by the one evaluator from the Site's budget lines:
a leaf line is that leaf's target, a stated heading's line is that heading's target (Declared, whatever is assumed
below it), any other node's line is a check, compared and never used. A leaf with no line takes its literal rule
(`rules.TARGET_RULE`) as a labelled assumption; a target that cannot be set is absent, naming the budget line that
would set it, and never 0. A blocked factor is held but refused (`NOT_CALCULATED_YET`). The portfolio is composed per
factor over the Sites that have a target ("k of n"); operator-level lines are listed, never added (D-5A.8).

Origins (D-4B.18): a line carries its record's provenance; an `AT_ACTUAL` target carries the actual's; a `LEAK_ZERO`
target rests on no record and carries `unknown`; a solved main factor carries its heading's line and the other
targets under that heading. Nothing is stored (D-5A.9).
"""
from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import datetime
from decimal import Decimal
from types import MappingProxyType
from uuid import UUID

from assetops_backend.chain.ports import SiteRef
from assetops_backend.structure.check import StructureError
from assetops_backend.structure.evaluate import ORIGIN_ORDER, ORIGIN_UNKNOWN, LeafValue, Missing, SiteStructure, \
    blocks_of, compose, evaluate
from assetops_backend.structure.read import NOT_DECLARED, SITE_TYPE_TO_STRUCTURE, PortfolioStructure, StructureRead
from assetops_backend.structure.registry import REGISTRIES, Registry
from assetops_backend.structure.targets.lines import LEAF, NODE, BudgetLineReader, BudgetLines, TargetLine
from assetops_backend.structure.targets.rules import AT_ACTUAL, AT_ACTUAL_TEXT, CALENDAR, LEAK_TEXT, LEAK_ZERO, MAIN, \
    MAIN_OF, MAIN_TEXT, OPTION, TARGET_FAMILY, TARGET_KIND, TARGET_RULE, TARGET_WORDS, solve_main

NOT_RECEIVED, NOT_CALCULATED_YET = "NOT_RECEIVED", "NOT_CALCULATED_YET"
TARGET_CURRENCY_UNKNOWN = "TARGET_CURRENCY_UNKNOWN"
ACTUAL_NOT_AVAILABLE = "ACTUAL_NOT_AVAILABLE"
_MONTH = re.compile(r"[0-9]{4}-(0[1-9]|1[0-2])", re.ASCII)


@dataclass(frozen=True)
class TargetCheck:
    factor_id: str
    stated: Decimal
    computed: Decimal | None
    currency: str | None
    agrees: bool


@dataclass(frozen=True)
class SiteTargets:
    structure: SiteStructure          # the target side, same key and version as the actual side
    lines: BudgetLines
    checks: tuple[TargetCheck, ...]   # registry order
    currency: str | None              # the Site's target currency


@dataclass(frozen=True)
class PortfolioTargets:
    structure: PortfolioStructure            # site_count(structure, f) is 3B3's "k of n"
    sites: Mapping[str, SiteTargets]         # by site_code, the MINI_GRID Sites asked, in order
    portfolio_lines: BudgetLines             # operator-level lines, listed, never composed (D-5A.8)


def _month(month: str) -> str:
    if not isinstance(month, str) or _MONTH.fullmatch(month) is None:
        raise ValueError(f"month {month!r} is not YYYY-MM")
    return month


def _absent(cause: str, note: str | None) -> LeafValue:
    return LeafValue(None, "NOT_AVAILABLE", (), None,
                     Missing(TARGET_KIND, TARGET_FAMILY, cause, None, (), TARGET_WORDS, None, note), None)


def _assumption(value: Decimal, text: str, source: str, currency: str | None,
                origins: tuple[str, ...]) -> LeafValue:
    return LeafValue(value, "ESTIMATED", (source,), None,
                     Missing(TARGET_KIND, TARGET_FAMILY, NOT_RECEIVED, "ASSUMPTION", (), TARGET_WORDS, text, None),
                     currency, origins)


def _declared(line: TargetLine) -> LeafValue:
    return LeafValue(line.value, "DECLARED", (f"budget:{line.revision_id}",), None, None, line.currency,
                     (line.provenance,))


def _origin_union(*groups: Sequence[str]) -> tuple[str, ...]:
    held = {o for g in groups for o in g}
    return tuple(o for o in ORIGIN_ORDER if o in held)


def _site_currency(bl: BudgetLines) -> str | None:
    currencies = {line.currency for line in bl.lines if line.currency is not None}
    return next(iter(currencies)) if len(currencies) == 1 else None


class TargetRead:
    def __init__(self, lines: BudgetLineReader, actual: StructureRead) -> None:
        self._lines = lines
        self._actual = actual

    def site(self, site: SiteRef, month: str, known_at: datetime | None = None) -> SiteTargets:
        """Spec §3.2, steps 1 to 8."""
        key = SITE_TYPE_TO_STRUCTURE.get(site.site_type)
        if key is None:
            raise StructureError(NOT_DECLARED[0], str(site.site_type), site.site_code)
        _month(month)
        reg = REGISTRIES[key]
        bl = self._lines.site(site.tenant_id, site.site_id, month, structure_key=key, known_at=known_at)
        act = self._actual.site(site, month, known_at).values
        currency = _site_currency(bl)
        by_factor = {line.factor_id: line for line in bl.lines}
        rule = TARGET_RULE[key]

        leaves: dict[str, LeafValue] = {}
        mains: list[str] = []
        for row in reg.rows:
            if not row.is_leaf:
                continue
            f = row.factor_id
            line = by_factor.get(f)
            if f in bl.blocked:
                leaves[f] = _absent(NOT_CALCULATED_YET, bl.blocked[f])
            elif line is not None and line.place == LEAF:
                leaves[f] = _declared(line)
            elif rule[f] == OPTION:
                leaves[f] = LeafValue(row.neutral, "NEUTRAL", ("option-only neutral",), None, None, None)
            elif rule[f] == CALENDAR:
                a = act[f]
                leaves[f] = LeafValue(a.value, a.evidence, ("calendar",), None, None, None, a.origins)
            elif rule[f] == LEAK_ZERO:
                if row.money and currency is None:
                    leaves[f] = _absent(NOT_RECEIVED, TARGET_CURRENCY_UNKNOWN)
                else:
                    leaves[f] = _assumption(Decimal("0"), LEAK_TEXT, "assumption:zero",
                                            currency if row.money else None, (ORIGIN_UNKNOWN,))
            elif rule[f] == AT_ACTUAL:
                a = act[f]
                if a.value is None:
                    leaves[f] = _absent(NOT_RECEIVED, ACTUAL_NOT_AVAILABLE)
                else:
                    leaves[f] = _assumption(a.value, AT_ACTUAL_TEXT, "assumption:at-actual", a.currency,
                                            a.origins or (ORIGIN_UNKNOWN,))
            elif rule[f] == MAIN:
                mains.append(f)
                leaves[f] = _absent(NOT_RECEIVED, None)  # step 5 decides; until then it counts as absent
            else:  # a rule outside RULES: a table bug, never a silent target
                raise StructureError("STRUCTURE_LEAF_INPUT", key, f)

        stated: dict[str, LeafValue] = {}
        for row in reg.rows:
            if row.stated_by is None:
                continue
            f = row.factor_id
            line = by_factor.get(f)
            if f in bl.blocked:  # D-5A.13: held but refused; 4b1's blocking row keeps the heading absent
                stated[f] = _absent(NOT_CALCULATED_YET, bl.blocked[f])
            elif line is not None and line.place == NODE:
                stated[f] = _declared(line)
            else:
                stated[f] = _absent(NOT_RECEIVED, None)

        for f in mains:
            heading = MAIN_OF[key][f]
            target = stated[heading]
            if target.value is None:
                leaves[f] = _absent(NOT_RECEIVED, f"MAIN_FACTOR_UNSOLVED:{heading}")
                continue
            value, note = solve_main(reg, leaves, heading, f, target.value, currency=target.currency)
            if value is None:
                leaves[f] = _absent(NOT_RECEIVED, note)
                continue
            under = (leaves[g].origins for g in leaves if g != f and heading in blocks_of(reg, (g,)))
            leaves[f] = _assumption(value, MAIN_TEXT, f"assumption:main-factor:{heading}",
                                    target.currency if reg.row(f).money else None,
                                    _origin_union(target.origins, *under))

        values = evaluate(reg, leaves, stated)
        checks = tuple(
            TargetCheck(row.factor_id, by_factor[row.factor_id].value, values[row.factor_id].value,
                        by_factor[row.factor_id].currency,
                        values[row.factor_id].value is not None
                        and values[row.factor_id].value == by_factor[row.factor_id].value
                        and values[row.factor_id].currency == by_factor[row.factor_id].currency)
            for row in reg.rows
            if row.factor_id in by_factor and by_factor[row.factor_id].place == NODE and row.stated_by is None)
        return SiteTargets(SiteStructure(site.site_code, month, key, reg.version, values), bl, checks, currency)

    def portfolio(self, tenant_id: UUID, sites: Sequence[SiteRef], month: str,
                  known_at: datetime | None = None) -> PortfolioTargets:
        """Spec §4: the MINI_GRID Sites' targets composed factor by factor; any other type left out whole."""
        _month(month)
        key = SITE_TYPE_TO_STRUCTURE["MINIGRID"]
        reg: Registry = REGISTRIES[key]
        seen: set[object] = set()
        for s in sites:
            if s.tenant_id != tenant_id or s.site_code in seen or s.site_id in seen:
                raise StructureError("STRUCTURE_COMPOSE", key, s.site_code)
            seen.update((s.site_code, s.site_id))
        per_site = {s.site_code: self.site(s, month, known_at) for s in sites
                    if SITE_TYPE_TO_STRUCTURE.get(s.site_type) == key}
        excluded = MappingProxyType({s.site_code: NOT_DECLARED for s in sites
                                     if SITE_TYPE_TO_STRUCTURE.get(s.site_type) is None})
        composition = replace(compose(reg, {code: t.structure for code, t in per_site.items()}),
                              sites_excluded=excluded)
        structure = PortfolioStructure(month, key, reg.version, composition, tuple(s.site_code for s in sites))
        portfolio_lines = self._lines.portfolio(tenant_id, month, structure_key=key, known_at=known_at)
        return PortfolioTargets(structure, MappingProxyType(per_site), portfolio_lines)


__all__ = [
    "ACTUAL_NOT_AVAILABLE", "TARGET_CURRENCY_UNKNOWN", "PortfolioTargets", "SiteTargets", "TargetCheck", "TargetRead",
]
