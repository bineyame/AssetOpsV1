"""3B1: the structure start-up check (spec §4-§5; D-3B1.3, D-3B1.6, D-3B1.9; R1, R8-R12, R17).

`check(registry)` raises the first `StructureError`; it refuses, never repairs. The codes run
code-major (R9): each code runs over every row in `ROWS` order before the next code starts.
Nothing here is specific to one structure key, and nothing looks up a parent's home: every
row is judged on its own `home`.

3B3 added `STRUCTURE_NEUTRAL` and `STRUCTURE_COMPOSES`; the runtime leaf-value checks are in `evaluate.py`.
4b1 added `STRUCTURE_STATED` (D-4B.1, D-4B.17); `evaluate` raises it at run time too, for a stated key on a row
without `stated_by`.

3B2 added `check_pins` (D-3B2.10 to D-3B2.13): mechanism pins, run by `check_all()` on the start-up path only.

Deferred (D-3B1.6): observer existence (3B4), and levers (step 6).
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from decimal import Decimal

from assetops_backend.config import ConfigurationError
from assetops_backend.outcomes import outcome_map as _outcome_map
from assetops_backend.structure import pins as _pins
from assetops_backend.structure import registry as _registry
from assetops_backend.structure.expressions import (
    Bin, Expr, ExpressionError, Neg, Num, Ref, UnitError, names, parse, unit_of,
)
from assetops_backend.structure.registry import ABSENT, COMPOSES, FAMILIES, HOMES, Registry
from assetops_contracts.canonical.factors import LEAF_FACTORS, STRUCTURE_KEYS, leaves_of
from assetops_contracts.canonical.units import KWH

_ABOVE, _CALENDAR = HOMES["above"], HOMES["calendar"]
_PLACEMENTS = frozenset({_ABOVE, _CALENDAR})
_HOME_CODES = frozenset(HOMES.values())
#: R1: the only homes a money row may have.
_MONEY_HOMES = frozenset({HOMES["grow"], HOMES["optimize"], _ABOVE})
_OBJECTIVE = re.compile(r"[GOPA][1-9]", re.ASCII)


class StructureError(ValueError):
    """A declared structure that may not start. Its text is `"<CODE> <structure_key>/<factor_id>"`."""

    def __init__(self, code: str, structure_key: str, factor_id: str) -> None:
        super().__init__(f"{code} {structure_key}/{factor_id}")
        self.code = code
        self.structure_key = structure_key
        self.factor_id = factor_id


class _Context:
    """What earlier codes established, for the later codes of one `check` call."""

    def __init__(self, reg: Registry) -> None:
        self.reg = reg
        self.key = reg.structure_key
        self.parsed: dict[str, Expr] = {}
        self.units: dict[str, object] = {}

    def refuse(self, code: str, factor_id: str) -> StructureError:
        return StructureError(code, self.key, factor_id)


def _duplicate(ctx: _Context) -> None:
    seen: set[str] = set()
    for row in ctx.reg.rows:
        if row.factor_id in seen:
            raise ctx.refuse("STRUCTURE_DUPLICATE", row.factor_id)
        seen.add(row.factor_id)
    ctx.units = {row.factor_id: row.unit for row in ctx.reg.rows}


def _expression(ctx: _Context) -> None:
    for row in ctx.reg.rows:
        if row.is_leaf:
            continue
        try:
            ctx.parsed[row.factor_id] = parse(row.expression)
        except (ExpressionError, SyntaxError, ValueError) as error:  # R8
            raise ctx.refuse("STRUCTURE_EXPRESSION", row.factor_id) from error


def _unknown_factor(ctx: _Context) -> None:
    for row in ctx.reg.rows:
        if not row.is_leaf and any(name not in ctx.units for name in names(ctx.parsed[row.factor_id])):
            raise ctx.refuse("STRUCTURE_UNKNOWN_FACTOR", row.factor_id)


def _cycle(ctx: _Context) -> None:
    children = {factor_id: names(expr) for factor_id, expr in ctx.parsed.items()}
    for row in ctx.reg.rows:
        if row.is_leaf:
            continue
        seen: set[str] = set()
        stack = list(children[row.factor_id])
        while stack:
            current = stack.pop()
            if current == row.factor_id:
                raise ctx.refuse("STRUCTURE_CYCLE", row.factor_id)
            if current not in seen:
                seen.add(current)
                stack.extend(children.get(current, ()))


def _catalogue(ctx: _Context) -> None:
    if ctx.key not in STRUCTURE_KEYS:
        raise ctx.refuse("STRUCTURE_CATALOGUE", "-")
    catalogue_ids = leaves_of(ctx.key)
    for row in ctx.reg.rows:
        if row.is_leaf:
            if row.factor_id not in catalogue_ids or row.unit != LEAF_FACTORS[row.factor_id].unit:
                raise ctx.refuse("STRUCTURE_CATALOGUE", row.factor_id)
        elif row.factor_id in LEAF_FACTORS:
            raise ctx.refuse("STRUCTURE_CATALOGUE", row.factor_id)
    leaf_ids = {row.factor_id for row in ctx.reg.rows if row.is_leaf}
    for factor_id in catalogue_ids:  # the reverse direction, in the catalogue's order (R10)
        if factor_id not in leaf_ids:
            raise ctx.refuse("STRUCTURE_CATALOGUE", factor_id)


def _leaf_source(ctx: _Context) -> None:
    for row in ctx.reg.rows:
        if row.is_leaf:
            bad = row.filled_by is None or row.filled_by.family not in FAMILIES
        else:
            bad = row.filled_by is not None  # R17
        if bad:
            raise ctx.refuse("STRUCTURE_LEAF_SOURCE", row.factor_id)


def _leaf_absent(ctx: _Context) -> None:
    for row in ctx.reg.rows:
        if row.is_leaf:
            calendar = row.filled_by.family == "CALENDAR"
            bad = row.absent not in ABSENT or (row.absent == "NEVER_EMPTY") != calendar
        else:
            bad = row.absent is not None  # R17
        if bad:
            raise ctx.refuse("STRUCTURE_LEAF_ABSENT", row.factor_id)


def _finite_decimal(value: object) -> bool:
    """3B3 (carried L1, P7): a `Decimal` that is neither NaN nor infinite; never compares a float or a NaN."""
    return isinstance(value, Decimal) and value.is_finite()


def _neutral(ctx: _Context) -> None:
    """3B3 (D-3B3.9, P7): exactly the OPTION_ONLY leaves carry a finite `Decimal` neutral value."""
    for row in ctx.reg.rows:
        option_only = row.is_leaf and row.absent == "OPTION_ONLY"
        if option_only != (row.neutral is not None) or (option_only and not _finite_decimal(row.neutral)):
            raise ctx.refuse("STRUCTURE_NEUTRAL", row.factor_id)


def _tolerance(ctx: _Context) -> None:
    for row in ctx.reg.rows:
        tolerance = row.tolerance
        if tolerance is None:
            continue
        if (tolerance.of_factor not in ctx.units or ctx.units[tolerance.of_factor] != row.unit
                or not _finite_decimal(tolerance.pct) or not tolerance.pct > 0):  # 3B3 carried L1
            raise ctx.refuse("STRUCTURE_TOLERANCE", row.factor_id)


def _unit(ctx: _Context) -> None:
    for row in ctx.reg.rows:
        if row.is_leaf:
            continue
        try:
            composed = unit_of(ctx.parsed[row.factor_id], ctx.units)  # children's declared units (R9)
        except UnitError as error:
            raise ctx.refuse("STRUCTURE_UNIT", row.factor_id) from error
        if composed != row.unit:
            raise ctx.refuse("STRUCTURE_UNIT", row.factor_id)


def _composes(ctx: _Context) -> None:
    """3B3 (D-3B3.14): `SUM` or `NONE`; a unit with a denominator (a price, a rate) is never summed."""
    for row in ctx.reg.rows:
        if row.composes not in COMPOSES or (
                row.composes == "SUM" and any(exponent < 0 for _, exponent in row.unit.exponents)):
            raise ctx.refuse("STRUCTURE_COMPOSES", row.factor_id)


def _stated(ctx: _Context) -> None:
    """4b1 (D-4B.1, D-4B.17), 4a (D-4A.1): a record states only a summed money or kWh node's total, and is a
    commercial record."""
    for row in ctx.reg.rows:
        stated = row.stated_by
        if stated is not None and (row.is_leaf or stated.family != "COMMERCIAL_RECORD" or row.composes != "SUM"
                                   or not (row.unit.is_money or row.unit == KWH)):
            raise ctx.refuse("STRUCTURE_STATED", row.factor_id)


def _category(ctx: _Context) -> None:
    for row in ctx.reg.rows:
        home = row.home
        calendar_leaf = row.is_leaf and row.filled_by.family == "CALENDAR"
        if (home is None or home.category not in _HOME_CODES
                or (home.category == _CALENDAR) != calendar_leaf
                or (home.category == _ABOVE and row.is_leaf)):
            raise ctx.refuse("STRUCTURE_CATEGORY", row.factor_id)


def _objective(ctx: _Context) -> None:
    for row in ctx.reg.rows:
        category, objective = row.home.category, row.home.objective
        if category in _PLACEMENTS:
            bad = objective is not None
        else:  # R11: the objective's letter is its category's
            bad = (not isinstance(objective, str) or _OBJECTIVE.fullmatch(objective) is None
                   or objective[0] != category[0])
        if bad:
            raise ctx.refuse("STRUCTURE_OBJECTIVE", row.factor_id)


def _money_home(ctx: _Context) -> None:
    for row in ctx.reg.rows:
        if row.money and row.home.category not in _MONEY_HOMES:
            raise ctx.refuse("STRUCTURE_MONEY_HOME", row.factor_id)


_CHECKS: tuple[tuple[str, Callable[[_Context], None]], ...] = (
    ("STRUCTURE_DUPLICATE", _duplicate),
    ("STRUCTURE_EXPRESSION", _expression),
    ("STRUCTURE_UNKNOWN_FACTOR", _unknown_factor),
    ("STRUCTURE_CYCLE", _cycle),
    ("STRUCTURE_CATALOGUE", _catalogue),
    ("STRUCTURE_LEAF_SOURCE", _leaf_source),
    ("STRUCTURE_LEAF_ABSENT", _leaf_absent),
    ("STRUCTURE_NEUTRAL", _neutral),
    ("STRUCTURE_TOLERANCE", _tolerance),
    ("STRUCTURE_UNIT", _unit),
    ("STRUCTURE_COMPOSES", _composes),
    ("STRUCTURE_STATED", _stated),
    ("STRUCTURE_CATEGORY", _category),
    ("STRUCTURE_OBJECTIVE", _objective),
    ("STRUCTURE_MONEY_HOME", _money_home),
)
#: The codes in the order they run.
CODES = tuple(code for code, _ in _CHECKS)


def check(reg: Registry) -> None:
    """Raise the first `StructureError` of `reg`, code by code in `CODES` order (R9)."""
    ctx = _Context(reg)
    for _, run in _CHECKS:
        run(ctx)


#: 3B2 (D-3B2.13): the pin codes in the order they run; separate from the per-registry `CODES`.
PIN_CODES = ("STRUCTURE_PIN", "STRUCTURE_PIN_TOTAL", "STRUCTURE_PIN_DUPLICATE", "STRUCTURE_PIN_UNKNOWN",
             "STRUCTURE_PIN_MISSING")
_FINDING = "FINDING:"
_UNMAPPED_KEY = _FINDING + _outcome_map.UNMAPPED
#: STRUCTURE_PIN_MISSING names no structure: the mechanism has none (the "-" of `STRUCTURE_CATALOGUE`).
_NO_KEY = "-"


def _is_total(expr: Expr) -> bool:
    """D-3B2.12: only `+`/`-`, `Neg`, `Ref` and `Num` (a bare `Ref` counts); any `Call`, `*` or `/` is not."""
    if isinstance(expr, (Ref, Num)):
        return True
    if isinstance(expr, Neg):
        return _is_total(expr.operand)
    if isinstance(expr, Bin):
        return expr.op in ("+", "-") and _is_total(expr.left) and _is_total(expr.right)
    return False


def check_pins(pins: Mapping[str, "_pins.Pin"] | None = None, registries: Mapping[str, Registry] | None = None,
               pending: Mapping[str, str] | None = None,
               entries: Mapping[str, object] | None = None) -> None:
    """3B2 (spec §3): raise the first pin fault, code by code in `PIN_CODES` order. A `None` argument reads the real
    `PINS`, `REGISTRIES`, `PENDING_PINS` or `outcome_map.ENTRIES` at call time (D-3B2.10)."""
    pins = _pins.PINS if pins is None else pins
    registries = _registry.REGISTRIES if registries is None else registries
    pending = _pins.PENDING_PINS if pending is None else pending
    entries = _outcome_map.ENTRIES if entries is None else entries
    for pin in pins.values():
        reg = registries.get(pin.structure_key)
        if reg is None or all(row.factor_id != pin.factor_id for row in reg.rows):
            raise StructureError("STRUCTURE_PIN", pin.structure_key, pin.factor_id)
    for pin in pins.values():
        row = registries[pin.structure_key].row(pin.factor_id)
        if not row.is_leaf and _is_total(_registry.parsed_text(row.expression)):
            raise StructureError("STRUCTURE_PIN_TOTAL", pin.structure_key, pin.factor_id)
    for mechanism, pin in pins.items():
        if mechanism in pending:
            raise StructureError("STRUCTURE_PIN_DUPLICATE", pin.structure_key, mechanism)
    named = [(m, p.structure_key) for m, p in pins.items()] + list(pending.items())
    for mechanism, structure_key in named:
        if _FINDING + mechanism not in entries:
            raise StructureError("STRUCTURE_PIN_UNKNOWN", structure_key, mechanism)
    for key in entries:
        if key.startswith(_FINDING) and key != _UNMAPPED_KEY:
            mechanism = key[len(_FINDING):]
            if mechanism not in pins and mechanism not in pending:
                raise StructureError("STRUCTURE_PIN_MISSING", _NO_KEY, mechanism)


def check_all(registries: Mapping[str, Registry] | None = None) -> None:
    """Check every registry; `registry.REGISTRIES` is read at call time (P3). Nothing is cached (R6).

    3B2 (D-3B2.10): with no argument (the start-up path) the pins are checked last; `check_all(registries=X)` checks
    `X` alone and runs no pin check."""
    for reg in (_registry.REGISTRIES if registries is None else registries).values():
        check(reg)
    if registries is None:
        check_pins()


def check_at_start() -> None:
    """The start-up call in `create_app` (D-3B1.9): a broken structure stops the process, naming the row."""
    try:
        check_all()
    except StructureError as error:
        raise ConfigurationError(str(error)) from error


__all__ = ["CODES", "PIN_CODES", "StructureError", "check", "check_all", "check_at_start", "check_pins"]
