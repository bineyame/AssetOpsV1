"""3B1: the structure start-up check (spec §4-§5; D-3B1.3, D-3B1.6, D-3B1.9; R1, R8-R12, R17).

`check(registry)` raises the first `StructureError`; it refuses, never repairs. The codes run
code-major (R9): each code runs over every row in `ROWS` order before the next code starts.
Nothing here is specific to one structure key, and nothing looks up a parent's home: every
row is judged on its own `home`.

3B3 added `STRUCTURE_NEUTRAL` and `STRUCTURE_COMPOSES`; the runtime leaf-value checks are in `evaluate.py`.
4b1 added `STRUCTURE_STATED` (D-4B.1, D-4B.17); `evaluate` raises it at run time too, for a stated key on a row
without `stated_by`.

3B2 added `check_pins` (D-3B2.10 to D-3B2.13): mechanism pins, run by `check_all()` on the start-up path only.

3B6 added `STRUCTURE_NOT_APPLICABLE` (D-3B6.3): per registry (pattern, repeat, own row) as the last code, and across
the checked set in `check_all` (each entry a row of another checked registry); and the key check (3B1's L2, D-3B6.4):
a `REGISTRIES` key that differs from its registry's `structure_key` refuses as `STRUCTURE_CATALOGUE <key>/-`.

3B4 added `check_observed` (D-3B4.2, D-3B4.16, D-3B4.20, D-3B4.25): the observer's tables against the registries,
run by `check_all()` on the start-up path after `check_pins`.

6a added `check_levers` (D-P6.12, D-P6.23; spec §3.1): the levers against the registries and the pins, run by
`check_all()` between `check_pins` and `check_observed`, on the start-up path only. It was D-3B1.6's deferred item.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from decimal import Decimal

from assetops_backend.config import ConfigurationError
from assetops_backend.outcomes import outcome_map as _outcome_map
from assetops_backend.structure import pins as _pins
from assetops_backend.structure import levers as _levers
from assetops_backend.structure import registry as _registry
from assetops_backend.structure.attribution.rules import BRIDGE_ROOTS
from assetops_backend.structure.observe import rules as _observe
from assetops_backend.structure.expressions import (
    Bin, Expr, ExpressionError, Neg, Num, Ref, UnitError, names, parse, unit_of,
)
from assetops_backend.structure.registry import ABSENT, COMPOSES, FAMILIES, HOMES, FactorRow, Registry
from assetops_contracts.canonical.factors import FACTOR_ID_PATTERN, LEAF_FACTORS, STRUCTURE_KEYS, leaves_of
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


def _not_applicable(ctx: _Context) -> None:
    """3B6 (D-3B6.3): each declared not-applicable ID is a well-formed factor ID, named once, and not a row here."""
    seen: set[str] = set()
    for entry in ctx.reg.not_applicable:
        if not isinstance(entry, str) or FACTOR_ID_PATTERN.fullmatch(entry) is None:
            raise ctx.refuse("STRUCTURE_NOT_APPLICABLE", str(entry))
        if entry in seen:
            raise ctx.refuse("STRUCTURE_NOT_APPLICABLE", entry)
        if entry in ctx.units:
            raise ctx.refuse("STRUCTURE_NOT_APPLICABLE", entry)
        seen.add(entry)


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
    ("STRUCTURE_NOT_APPLICABLE", _not_applicable),
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


_LEVER_ID = re.compile(r"[a-z][a-z0-9_]{0,63}", re.ASCII)
_OPTION_KEY = re.compile(r"[a-z0-9][a-z0-9-]{0,63}", re.ASCII)
_NO_ACTION_KEY = "no-action"


def _lever_fault(lever: "_levers.Lever", registries: Mapping[str, Registry], pins: Mapping[str, "_pins.Pin"],
                 all_levers: Mapping[str, "_levers.Lever"]) -> None:
    """Branches 2 to 14 of 6a spec §3.1 for one lever, in order (6 to 13 for `SETTING_GRID` only, D-P6.63), then
    6h's 15 to 22."""
    def refuse() -> StructureError:
        return StructureError("STRUCTURE_LEVER", lever.structure_key, lever.lever_id)

    reg = registries.get(lever.structure_key)
    if reg is None:
        raise refuse()
    purpose = next((row for row in reg.rows if row.factor_id == lever.purpose_factor), None)
    if purpose is None:
        raise refuse()
    if lever.lever_id not in purpose.levers:
        raise refuse()
    leaves = {row.factor_id for row in reg.rows if row.is_leaf}
    if any(name not in leaves for name in lever.changes):
        raise refuse()
    if lever.generator == "SETTING_GRID":  # 6 to 13 (D-P6.63): the grid branches, for the grid generator only
        if any(not _LEVER_ID.fullmatch(axis.name) for axis in lever.axes):
            raise refuse()
        if any(len(axis.values) == 0 for axis in lever.axes):
            raise refuse()
        if any(len(set(axis.values)) != len(axis.values) for axis in lever.axes):
            raise refuse()
        if len({axis.unit for axis in lever.axes}) > 1:
            raise refuse()
        if set(re.findall(r"\{(\w*)\}", lever.key_template)) != {axis.name for axis in lever.axes}:
            raise refuse()
        if any(value != value.to_integral_value() for axis in lever.axes for value in axis.values):
            raise refuse()
        keys = [_levers.option_key(lever, point) for point in _levers.grid(lever)]
        if len(set(keys)) != len(keys):
            raise refuse()
        if any(not _OPTION_KEY.fullmatch(key) for key in keys):
            raise refuse()
    for pin in pins.values():
        pin_reg = registries.get(pin.structure_key)
        pin_row = None if pin_reg is None else next((r for r in pin_reg.rows if r.factor_id == pin.factor_id), None)
        if pin_row is None or lever.lever_id not in pin_row.levers or pin_row.home is None or purpose.home is None:
            continue
        if pin_row.home.category != purpose.home.category:
            raise refuse()
    _named_fault(lever, purpose, refuse)


def _named_fault(lever: "_levers.Lever", purpose: FactorRow, refuse: Callable[[], StructureError]) -> None:
    """6h (spec §3.2): branches 15 to 22, in order."""
    if lever.generator not in _levers.GENERATORS:  # 15
        raise refuse()
    if set(lever.change_sources) != set(lever.changes) or any(  # 16
            source.kind not in _levers.CHANGE_SOURCE_KINDS for source in lever.change_sources.values()):
        raise refuse()
    if lever.generator == "SETTING_GRID" and lever.options:  # 17
        raise refuse()
    if lever.generator == "STATED_OPTIONS" and (lever.axes or not lever.options or lever.key_template):
        raise refuse()
    keys = [option.key for option in lever.options]  # 18
    if any(not _OPTION_KEY.fullmatch(key) or key == _NO_ACTION_KEY for key in keys) or len(set(keys)) != len(keys):
        raise refuse()
    if any(option.kind not in _levers.OPTION_KINDS for option in lever.options):  # 19
        raise refuse()
    for option in lever.options:  # 20
        if not option.changes or any(name not in lever.changes for name in option.changes):
            raise refuse()
        if list(option.changes) != [name for name in lever.changes if name in option.changes]:
            raise refuse()
    if lever.no_action_words not in _levers.NO_ACTION_WORDS:  # 21
        raise refuse()
    if lever.bounds_required and (purpose.home is None or purpose.home.category != HOMES["protect"]):  # 22
        raise refuse()


def check_levers(levers: Mapping[str, "_levers.Lever"] | None = None,
                 registries: Mapping[str, Registry] | None = None,
                 pins: Mapping[str, "_pins.Pin"] | None = None) -> None:
    """6a (spec §3.1): raise the first lever fault as `STRUCTURE_LEVER <structure_key>/<lever_id>`, lever by lever
    (all of a lever's branches, 2 to 14, run in order before the next lever starts). A `None` argument reads the
    real table at call time."""
    levers = _levers.LEVERS if levers is None else levers
    registries = _registry.REGISTRIES if registries is None else registries
    pins = _pins.PINS if pins is None else pins
    for key, reg in registries.items():  # 1: a row's lever names no lever
        for row in reg.rows:
            for name in row.levers:
                if name not in levers:
                    raise StructureError("STRUCTURE_LEVER", key, name)
    for lever in levers.values():
        _lever_fault(lever, registries, pins, levers)


OBSERVE_CODES = ("STRUCTURE_OBSERVE_KEY", "STRUCTURE_OBSERVE_COVER", "STRUCTURE_OBSERVE_LEAF",
                 "STRUCTURE_OBSERVE_SOURCE", "STRUCTURE_OBSERVE_DIRECTION", "STRUCTURE_OBSERVE_KIND")
_NOT_SOURCES = frozenset({"DECLARED", "CALENDAR"})
_NOT_ABSENT = frozenset({"OPTION_ONLY", "NEVER_EMPTY"})


def check_observed(observed: Mapping[str, Mapping[str, str]] | None = None,
                   not_observed: Mapping[str, Mapping[str, str]] | None = None,
                   registries: Mapping[str, Registry] | None = None) -> None:
    """3B4 (spec §2.3; D-3B4.2, D-3B4.16): raise the first observer-table fault, code by code in `OBSERVE_CODES`
    order, each over keys in `OBSERVED` order then leaves in table order. A `None` reads the real table at call time.
    `KEY` runs over `OBSERVED`'s keys only: a registry the observer does not name is not a fault (D-3B4.25)."""
    observed = _observe.OBSERVED if observed is None else observed
    not_observed = _observe.NOT_OBSERVED if not_observed is None else not_observed
    registries = _registry.REGISTRIES if registries is None else registries
    # D-3B4.20: the one function-local import; at call time `check` is loaded, so the cycle cannot close.
    from assetops_backend.structure.targets import rules as _targets

    def refuse(code: str, key: str, leaf: str) -> StructureError:
        return StructureError("STRUCTURE_OBSERVE_" + code, key, leaf)

    for key in observed:
        if key not in registries or key not in BRIDGE_ROOTS or key not in _targets.TARGET_RULE:
            raise refuse("KEY", key, _NO_KEY)
    if set(observed) != set(not_observed):
        key = next(iter(k for k in (*observed, *not_observed) if k not in observed or k not in not_observed))
        raise refuse("KEY", key, _NO_KEY)

    for key, table in observed.items():
        reg, other = registries[key], not_observed[key]
        rows = {row.factor_id: row for row in reg.rows}
        for row in reg.rows:
            if row.is_leaf and (row.factor_id in table) == (row.factor_id in other):
                raise refuse("COVER", key, row.factor_id)
        for leaf in (*table, *other):
            if leaf not in rows:
                raise refuse("COVER", key, leaf)
        for leaf, reason in other.items():
            if not rows[leaf].is_leaf or reason not in _observe.REASONS:
                raise refuse("COVER", key, leaf)
    for key, table in observed.items():
        reg = registries[key]
        for leaf in table:
            if not reg.row(leaf).is_leaf:
                raise refuse("LEAF", key, leaf)
    for key, table in observed.items():
        reg = registries[key]
        for leaf in table:
            row = reg.row(leaf)
            family = row.filled_by.family if row.filled_by is not None else None
            if family in _NOT_SOURCES or row.absent in _NOT_ABSENT:
                raise refuse("SOURCE", key, leaf)
    for key, table in observed.items():
        got = _observe.reached(registries[key], key)
        for leaf, direction in table.items():
            s = got.get(leaf, frozenset())
            if (direction not in (_observe.UP, _observe.DOWN) or len(s) > 1
                    or (s == {-1} and direction == _observe.DOWN) or (s == {1} and direction == _observe.UP)):
                raise refuse("DIRECTION", key, leaf)
    protect = HOMES["protect"]
    for key, table in observed.items():
        reg = registries[key]
        got = _observe.reached(reg, key)
        for leaf in table:
            home = reg.row(leaf).home
            if leaf not in got and (home is None or home.category != protect):
                raise refuse("KIND", key, leaf)


def check_all(registries: Mapping[str, Registry] | None = None) -> None:
    """Check every registry; `registry.REGISTRIES` is read at call time (P3). Nothing is cached (R6).

    3B2 (D-3B2.10): with no argument (the start-up path) the pins are checked last; `check_all(registries=X)` checks
    `X` alone and runs no pin check. 3B4 (spec §2.3): the observer tables are checked after the pins, on the same
    path only.

    3B6 (D-3B6.3, D-3B6.4): per entry, the key check (L2) then `check`; then every not-applicable entry must be a
    row of another registry of the checked set."""
    checked = _registry.REGISTRIES if registries is None else registries
    for key, reg in checked.items():
        if key != reg.structure_key:
            raise StructureError("STRUCTURE_CATALOGUE", key, _NO_KEY)
        check(reg)
    for key, reg in checked.items():
        for entry in reg.not_applicable:
            if not any(other_key != key and any(row.factor_id == entry for row in other.rows)
                       for other_key, other in checked.items()):
                raise StructureError("STRUCTURE_NOT_APPLICABLE", key, entry)
    if registries is None:
        check_pins()
        check_levers()
        check_observed()


def check_at_start() -> None:
    """The start-up call in `create_app` (D-3B1.9): a broken structure stops the process, naming the row."""
    try:
        check_all()
    except StructureError as error:
        raise ConfigurationError(str(error)) from error


__all__ = ["CODES", "OBSERVE_CODES", "PIN_CODES", "StructureError", "check", "check_all", "check_at_start",
           "check_levers", "check_observed", "check_pins"]
