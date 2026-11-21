"""5a unit 2 (spec `specs/5a-targets/spec.md` §3.1; D-5A.5, D-5A.6, D-5A.10): the target rules, as literals.

A leaf with no budget line of its own takes one rule (P5 rule 3): leaks and avoidable use at zero (`LEAK_ZERO`), prices
and other drivers at this month's actual (`AT_ACTUAL`), the main factor under a stated heading carrying the rest of
that heading (`MAIN`), an option-only leaf at its neutral (`OPTION`), the month's days (`CALENDAR`). The first three
are labelled assumptions with the words below. The main factor is solved through the one evaluator, only when the
heading is linear in it with a slope (D-5A.6).
"""
from __future__ import annotations

from collections.abc import Mapping
from decimal import ROUND_HALF_EVEN, Context, Decimal, localcontext
from types import MappingProxyType

from assetops_backend.structure.evaluate import ORIGIN_UNKNOWN, LeafValue, evaluate
from assetops_backend.structure.registry import Registry

TARGET_KIND, TARGET_FAMILY = "BUDGET_LINE", "COMMERCIAL_RECORD"
TARGET_WORDS = "Budget line for the month"
LEAK_TEXT = "No target line: taken at zero (assumption)"
AT_ACTUAL_TEXT = "No target line: taken at this month's actual, so no gap is put on it (assumption)"
MAIN_TEXT = "No target line: the rest of the heading's target, on its main factor (assumption)"
LEAK_ZERO, AT_ACTUAL, MAIN, OPTION, CALENDAR = "LEAK_ZERO", "AT_ACTUAL", "MAIN", "OPTION", "CALENDAR"
RULES = (LEAK_ZERO, AT_ACTUAL, MAIN, OPTION, CALENDAR)


def _rules(**by_rule: tuple[str, ...]) -> Mapping[str, str]:
    return MappingProxyType({leaf: rule for rule, leaves in by_rule.items() for leaf in leaves})


#: Spec §3.1's table: structure key -> leaf -> rule. Every one of MINI_GRID's 31 leaves.
TARGET_RULE: Mapping[str, Mapping[str, str]] = MappingProxyType({
    "MINI_GRID": _rules(
        LEAK_ZERO=("technical_loss_kwh", "unexplained_loss_kwh", "adjustments_kwh", "unmapped_kwh", "in_transit",
                   "outstanding", "candidate_l", "unexplained_l", "reduced_days", "unserved_critical_kwh",
                   "customer_hours_interrupted", "field_visits", "liability", "dawn_days_below"),
        AT_ACTUAL=("tariff", "productive_kwh", "productive_tariff", "diesel_price", "wear_rate", "om", "staff",
                   "hours_per_day", "major_assets", "standby_kw", "lost_unit_kw"),
        MAIN=("delivered_kwh", "necessary_l"),
        OPTION=("extra_l", "battery_throughput_kwh", "collection_cost"),
        CALENDAR=("period_days",),
    ),
})

#: Structure key -> MAIN leaf -> its stated headings, nearest first. 4a (D-4A.9): the main leaf is solved under the
#: first heading whose stated target has a value.
MAIN_OF: Mapping[str, Mapping[str, tuple[str, ...]]] = MappingProxyType({
    "MINI_GRID": MappingProxyType({"delivered_kwh": ("billed_kwh", "revenue"), "necessary_l": ("fuel_cost",)}),
})


def _context() -> Context:
    return Context(prec=34, rounding=ROUND_HALF_EVEN)


def solve_main(registry: Registry, leaves: Mapping[str, LeafValue], heading: str, leaf: str, target: Decimal, *,
               currency: str | None = None) -> tuple[Decimal | None, str | None]:
    """D-5A.6: the main leaf's value that makes `heading`'s computed value equal `target`, or a note.

    `leaves` holds every leaf (the main one is replaced). Evaluated three times with no `stated`, the main leaf at 0, 1
    and 2; linear when the two steps are equal, with a slope when they are not zero. `currency` is the heading's, used
    for the probe only when the main leaf is money. The probe rests on no record, so it carries `unknown` (D-4B.18);
    the probe's origins never reach the returned value."""
    probe_currency = currency if registry.row(leaf).unit.has_money_dimension else None
    v: list[Decimal] = []
    for k in (0, 1, 2):
        probe = LeafValue(Decimal(k), "DECLARED", ("solve",), None, None, probe_currency, (ORIGIN_UNKNOWN,))
        value = evaluate(registry, {**leaves, leaf: probe})[heading].value
        if value is None:
            return None, f"MAIN_FACTOR_UNSOLVED:{heading}"
        v.append(value)
    with localcontext(_context()):
        a = v[1] - v[0]
        if v[2] - v[1] != a:
            return None, f"MAIN_FACTOR_NONLINEAR:{heading}"
        if a == 0:
            return None, f"MAIN_FACTOR_ZERO_SLOPE:{heading}"
        return (target - v[0]) / a, None


__all__ = [
    "AT_ACTUAL", "AT_ACTUAL_TEXT", "CALENDAR", "LEAK_TEXT", "LEAK_ZERO", "MAIN", "MAIN_OF", "MAIN_TEXT", "OPTION",
    "RULES", "TARGET_FAMILY", "TARGET_KIND", "TARGET_RULE", "TARGET_WORDS", "solve_main",
]
