"""3B4 unit 1 (spec §2.1, §3; D-3B4.1 to D-3B4.4): what is observed, its adverse direction, and the signs.

Imports only `structure.registry`, `structure.expressions` and `structure.attribution.rules` (D-3B4.20): never
`check`, `evaluate`, `targets.rules` or `observe.observe`, so `check` may import this module at its top.
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from types import MappingProxyType

from assetops_backend.structure.attribution.rules import BRIDGE_ROOTS
from assetops_backend.structure.expressions import Bin, Expr, Neg, Ref
from assetops_backend.structure.registry import HOMES, Registry

UP, DOWN = "UP", "DOWN"                      # the adverse direction: a rise is adverse, a fall is adverse
MECHANISM = "STRUCTURE_DEVIATION"            # D-3B4.1: the one mechanism
OBSERVER_ANALYTIC = "structure-observer-1"   # not ANALYTIC_ID, and not under analytics/ (analytic-declaration guard)
OBSERVER_MODEL = "structure-observer-1/v1"
OBSERVER_MATCHER = "structure-observer/1"
DOMAIN = "structure"
KINDS = ("BOTTOM_LINE", "CASH", "PROTECT")   # D-3B4.4; derived, never declared
REASONS = ("DECLARED_SOURCE", "OPTION_ONLY", "CALENDAR", "EXPOSURE_RATE", "NO_OWNER_RULE_KIND")

#: D-3B4.3: structure key -> leaf -> adverse direction. MINI_GRID order is the registry's leaf order.
OBSERVED: Mapping[str, Mapping[str, str]] = MappingProxyType({
    "MINI_GRID": MappingProxyType({
        "delivered_kwh": DOWN,
        "unexplained_loss_kwh": UP,
        "adjustments_kwh": UP,
        "unmapped_kwh": UP,
        "tariff": DOWN,
        "productive_kwh": DOWN,
        "productive_tariff": DOWN,
        "in_transit": UP,
        "outstanding": UP,
        "necessary_l": UP,
        "candidate_l": UP,
        "unexplained_l": UP,
        "diesel_price": UP,
        "om": UP,
        "staff": UP,
        "reduced_days": UP,
        "unserved_critical_kwh": UP,
        "customer_hours_interrupted": UP,
        "dawn_days_below": UP,
    }),
})

#: D-3B4.3: every other leaf of the structure -> why it is not observed. OBSERVED and NOT_OBSERVED cover every leaf once.
NOT_OBSERVED: Mapping[str, Mapping[str, str]] = MappingProxyType({
    "MINI_GRID": MappingProxyType({
        "technical_loss_kwh": "DECLARED_SOURCE",
        "extra_l": "OPTION_ONLY",
        "battery_throughput_kwh": "OPTION_ONLY",
        "wear_rate": "DECLARED_SOURCE",
        "collection_cost": "OPTION_ONLY",
        "hours_per_day": "EXPOSURE_RATE",
        "major_assets": "DECLARED_SOURCE",
        "field_visits": "NO_OWNER_RULE_KIND",
        "liability": "NO_OWNER_RULE_KIND",
        "period_days": "CALENDAR",
        "standby_kw": "DECLARED_SOURCE",
        "lost_unit_kw": "DECLARED_SOURCE",
    }),
})

#: Spec §4.3: the observer Finding's key; its leaf is its pin (D-3B4.1).
KEY_PATTERN = r"structure:(?P<key>[A-Z][A-Z_]+):(?P<factor>[a-z][a-z0-9_]*):(?P<month>[0-9]{4}-[0-9]{2}):(?P<dir>UP|DOWN)"
_KEY = re.compile(KEY_PATTERN, re.ASCII)


def finding_key(structure_key: str, factor_id: str, month: str, direction: str) -> str:
    return f"structure:{structure_key}:{factor_id}:{month}:{direction}"


def pin_of_key(finding_key: str) -> tuple[str, str]:
    """Spec §3: `(structure_key, factor_id)` of an observer Finding's key; `ValueError` for any other text."""
    m = _KEY.fullmatch(finding_key) if isinstance(finding_key, str) else None
    if m is None:
        raise ValueError(finding_key)
    return m.group("key"), m.group("factor")


def signs(registry: Registry, root: str) -> Mapping[str, frozenset[int]]:
    """Spec §2.1: the sign(s) with which each leaf enters `root`. Pure; a leaf not reached is absent."""
    leaves = {row.factor_id for row in registry.rows if row.is_leaf}
    out: dict[str, set[int]] = {}

    def ref(name: str, s: int) -> None:
        if name in leaves:
            out.setdefault(name, set()).add(s)
        elif name in registry.parsed:
            walk(registry.parsed[name], s)

    def walk(expr: Expr, s: int) -> None:
        if isinstance(expr, Ref):
            ref(expr.name, s)
        elif isinstance(expr, Neg):
            walk(expr.operand, -s)
        elif isinstance(expr, Bin):
            if expr.op == "+":
                walk(expr.left, s)
                walk(expr.right, s)
            elif expr.op == "-":
                walk(expr.left, s)
                walk(expr.right, -s)
            elif expr.op == "*" and isinstance(expr.left, Ref) and isinstance(expr.right, Ref):
                walk(expr.left, s)
                walk(expr.right, s)
        # Call, "/", Num, "*" with a non-Ref side: nothing below is recorded

    ref(root, 1)
    return MappingProxyType({k: frozenset(v) for k, v in out.items()})


def reached(registry: Registry, key: str) -> Mapping[str, frozenset[int]]:
    """The union of `signs` over `BRIDGE_ROOTS[key]`."""
    out: dict[str, frozenset[int]] = {}
    for root in BRIDGE_ROOTS[key]:
        for leaf, s in signs(registry, root).items():
            out[leaf] = out.get(leaf, frozenset()) | s
    return MappingProxyType(out)


def first_root_leaves(registry: Registry, key: str) -> frozenset[str]:
    return frozenset(signs(registry, BRIDGE_ROOTS[key][0]))


def kind_of(registry: Registry, key: str, leaf: str) -> str:
    """D-3B4.4: PROTECT by home; else BOTTOM_LINE when the first root reaches the leaf; else CASH."""
    home = registry.row(leaf).home
    if home is not None and home.category == HOMES["protect"]:
        return "PROTECT"
    return "BOTTOM_LINE" if leaf in first_root_leaves(registry, key) else "CASH"


def money_dimension(unit) -> bool:
    """A unit with a money dimension (`MONEY`, `MONEY/KWH`, `MONEY/L`): its values carry a currency (spec §2.2 step
    3, §5.3's money leaves). Same rule as the evaluator's currency check."""
    return any(d == "MONEY" and e != 0 for d, e in unit.exponents)
