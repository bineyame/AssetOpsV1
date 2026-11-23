"""3B1: the structure registry's records and vocabularies (spec §2.3; D-3B1.1, D-3B1.7; R1, R13, R14).

The records do no validation of their own: every refusal lives in `structure/check.py`,
so a test can plant a bad value (R14). The expression is the record (D-3B1.7): a row's
kind and signed children are read from its parsed `Expr`, never stored.

Every row names its own home. There is no lookup of a parent's home anywhere.
"""

from __future__ import annotations

import functools
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from decimal import Decimal
from types import MappingProxyType

from assetops_backend.outcomes.catalogue import CATEGORIES
from assetops_backend.structure import expressions
from assetops_backend.structure.expressions import Expr, names
from assetops_contracts.canonical.units import Unit

_GROW, _OPTIMIZE, _PROTECT, _ASSURE = CATEGORIES

#: The manifest's home words to their codes. `ABOVE` and `CALENDAR` are placements, not
#: categories: a category read iterates `CATEGORIES`, never `HOMES` (R1).
HOMES: Mapping[str, str] = MappingProxyType({
    "grow": _GROW,
    "optimize": _OPTIMIZE,
    "protect": _PROTECT,
    "assure": _ASSURE,
    "above": "ABOVE",
    "calendar": "CALENDAR",
})

ABSENT = ("MISSING", "ZERO_WHEN_HELD", "OPTION_ONLY", "NEVER_EMPTY")
#: 3B3 (D-3B3.14): what a portfolio does with a row. `NONE` is the default and fails closed (no total).
COMPOSES = ("SUM", "NONE")
FAMILIES = ("COMMERCIAL_RECORD", "READING", "OPERATIONAL_RECORD", "OBSERVER", "DECLARED", "DOCUMENT", "CALENDAR")


@dataclass(frozen=True)
class Home:
    category: str
    objective: str | None


@dataclass(frozen=True)
class FilledBy:
    family: str
    kind: str
    words: str | None = None


@dataclass(frozen=True)
class Tolerance:
    """The structure default, a per cent of `of_factor`; a Site's declared value overrides it (R12)."""

    of_factor: str
    pct: Decimal


@dataclass(frozen=True)
class FactorRow:
    factor_id: str
    expression: str | None
    unit: Unit
    home: Home | None
    filled_by: FilledBy | None
    absent: str | None
    tolerance: Tolerance | None
    levers: tuple[str, ...] = ()
    #: 3B3 (D-3B3.9): the value an OPTION_ONLY leaf carries on an observed side; None on every other row.
    neutral: Decimal | None = None
    #: 3B3 (D-3B3.14): `SUM` (summed across Sites) or `NONE`; checked by `STRUCTURE_COMPOSES`.
    composes: str = "NONE"
    #: 4b1 (D-4B.1): the record that states this node's total; product-only (no manifest counterpart). Checked by
    #: `STRUCTURE_STATED`: a `SUM` node with a money unit, family `COMMERCIAL_RECORD`.
    stated_by: FilledBy | None = None

    @property
    def is_leaf(self) -> bool:
        return self.expression is None

    @property
    def money(self) -> bool:
        return self.unit.is_money

    @property
    def children(self) -> tuple[str, ...]:
        """The distinct factor names in the expression, in first-seen order (R3)."""
        return () if self.expression is None else names(parsed_text(self.expression))


@functools.lru_cache(maxsize=None)
def parsed_text(text: str) -> Expr:
    """3B3 (P5): parse once per expression text. Calls `expressions.parse` by attribute, so a test can count it."""
    return expressions.parse(text)


class _LazyParsed(Mapping[str, Expr]):
    """A registry's node expressions, parsed on first access per row (P5): a planted bad expression is refused
    by `check`, never at attribute access."""

    def __init__(self, reg: "Registry") -> None:
        self._rows = {row.factor_id: row for row in reg.rows if not row.is_leaf}
        self._done: dict[str, Expr] = {}

    def __getitem__(self, factor_id: str) -> Expr:
        if factor_id not in self._done:
            self._done[factor_id] = parsed_text(self._rows[factor_id].expression)
        return self._done[factor_id]

    def __iter__(self) -> Iterator[str]:
        return iter(self._rows)

    def __len__(self) -> int:
        return len(self._rows)


@dataclass(frozen=True)
class Registry:
    structure_key: str
    version: int
    rows: tuple[FactorRow, ...]
    #: 3B6 (D-3B6.3): factor IDs a reader of another structure may ask this one for, declared not to apply to its
    #: business. Not rows and carrying no value; checked by `STRUCTURE_NOT_APPLICABLE`. Read only via
    #: `applicability()` (D-3B6.14): a reader must never infer "not applicable" from a missing key.
    not_applicable: tuple[str, ...] = ()

    def row(self, factor_id: str) -> FactorRow:
        for candidate in self.rows:
            if candidate.factor_id == factor_id:
                return candidate
        raise KeyError(factor_id)

    @functools.cached_property
    def parsed(self) -> Mapping[str, Expr]:
        """3B3 (P5): every node's `Expr`, per instance (a planted registry starts empty), parsed lazily per row."""
        return _LazyParsed(self)

    @functools.cached_property
    def parents(self) -> Mapping[str, tuple[str, ...]]:
        """3B3 (P5): each factor's nodes that name it, in registry order."""
        out: dict[str, list[str]] = {row.factor_id: [] for row in self.rows}
        for row in self.rows:
            if not row.is_leaf:
                for child in names(self.parsed[row.factor_id]):
                    out.setdefault(child, []).append(row.factor_id)
        return MappingProxyType({k: tuple(v) for k, v in out.items()})


#: 3B6 (D-3B6.3): the three answers of `applicability`.
APPLIES, NOT_APPLICABLE, NOT_IN_STRUCTURE = "APPLIES", "NOT_APPLICABLE", "NOT_IN_STRUCTURE"


def applicability(reg: Registry, factor_id: str) -> str:
    """APPLIES when `factor_id` is a row of `reg`; NOT_APPLICABLE when `reg.not_applicable` names it;
    NOT_IN_STRUCTURE otherwise. Pure; never raises for an unknown ID."""
    if any(row.factor_id == factor_id for row in reg.rows):
        return APPLIES
    if factor_id in reg.not_applicable:
        return NOT_APPLICABLE
    return NOT_IN_STRUCTURE


# The rows import the records above, so they are imported after them (the package's
# `__init__` imports this module first).
from assetops_backend.structure.rows_cold_chain import ROWS as _COLD_CHAIN_ROWS  # noqa: E402
from assetops_backend.structure.rows_ev_depot import ROWS as _EV_DEPOT_ROWS  # noqa: E402
from assetops_backend.structure.rows_mini_grid import ROWS as _MINI_GRID_ROWS  # noqa: E402

#: Read at call time by `check.check_all` (P3). 3B6 (D-3B6.1) added COLD_CHAIN and EV_DEPOT_CAPTIVE, version 1 each;
#: a captive depot declares revenue not applicable (D-3B6.3).
REGISTRIES: Mapping[str, Registry] = MappingProxyType({
    # 3B3 (D-3B3.9): v2, rows gained neutral and composes. 4b1 (D-4B.10): v3, revenue and fuel_cost gained stated_by.
    # 4a (D-4A.1): v4, metered_kwh and billed_kwh gained stated_by. DD3d (D-DD.163): v5, fuel_cost lost its own.
    "MINI_GRID": Registry("MINI_GRID", 5, _MINI_GRID_ROWS),
    "COLD_CHAIN": Registry("COLD_CHAIN", 1, _COLD_CHAIN_ROWS),
    "EV_DEPOT_CAPTIVE": Registry("EV_DEPOT_CAPTIVE", 1, _EV_DEPOT_ROWS, not_applicable=("revenue",)),
})
