"""3B1: the structure registry's records and vocabularies (spec §2.3; D-3B1.1, D-3B1.7; R1, R13, R14).

The records do no validation of their own: every refusal lives in `structure/check.py`,
so a test can plant a bad value (R14). The expression is the record (D-3B1.7): a row's
kind and signed children are read from its parsed `Expr`, never stored.

Every row names its own home. There is no lookup of a parent's home anywhere.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from types import MappingProxyType

from assetops_backend.outcomes.catalogue import CATEGORIES
from assetops_backend.structure.expressions import names, parse
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

    @property
    def is_leaf(self) -> bool:
        return self.expression is None

    @property
    def money(self) -> bool:
        return self.unit.is_money

    @property
    def children(self) -> tuple[str, ...]:
        """The distinct factor names in the expression, in first-seen order (R3)."""
        return () if self.expression is None else names(parse(self.expression))


@dataclass(frozen=True)
class Registry:
    structure_key: str
    version: int
    rows: tuple[FactorRow, ...]

    def row(self, factor_id: str) -> FactorRow:
        for candidate in self.rows:
            if candidate.factor_id == factor_id:
                return candidate
        raise KeyError(factor_id)


# The rows import the records above, so they are imported after them (the package's
# `__init__` imports this module first).
from assetops_backend.structure.rows_mini_grid import ROWS as _MINI_GRID_ROWS  # noqa: E402

#: Read at call time by `check.check_all` (P3). `3B6` adds COLD_CHAIN and EV_DEPOT_CAPTIVE.
REGISTRIES: Mapping[str, Registry] = MappingProxyType({
    "MINI_GRID": Registry("MINI_GRID", 1, _MINI_GRID_ROWS),
})
