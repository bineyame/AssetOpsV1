"""5b unit 1 (spec §2.1; D-5B.2, D-5B.4, D-5B.14): the bridge's literals, as written in the spec.

The roots a structure's bridge starts from (outcome first, cash second), the row kinds, the split states and the
reasons a row is not split. `agree` is the one comparison steps 4 and 6 use: within `SOLVE_TOLERANCE`, never by
quantising (D-5B.14).
"""
from __future__ import annotations

from collections.abc import Mapping
from decimal import ROUND_HALF_EVEN, Context, Decimal, localcontext
from types import MappingProxyType

BRIDGE_ROOTS: Mapping[str, tuple[str, ...]] = MappingProxyType(
    {"MINI_GRID": ("contribution", "collected")})  # outcome first, cash second
KINDS = ("ROOT", "TERM", "VOLUME", "PRICE", "RESIDUAL")
SPLITS = ("SPLIT", "LEAF", "NOT_SPLIT")
GAP_NOT_AVAILABLE, DETAIL_NOT_AVAILABLE = "GAP_NOT_AVAILABLE", "DETAIL_NOT_AVAILABLE"
RECORD_AND_FACTORS_DIFFER, RULE_NOT_DECLARED = "RECORD_AND_FACTORS_DIFFER", "RULE_NOT_DECLARED"
PRICE_NOT_DECLARED, SPLIT_INEXACT = "PRICE_NOT_DECLARED", "SPLIT_INEXACT"
CURRENCY_MISMATCH = "CURRENCY_MISMATCH:"          # + sorted currencies, comma-joined
UNPLACED = "UNPLACED"                              # by_home key for a row whose factor has no home
SOLVE_TOLERANCE = Decimal("1E-12")                 # D-5B.14: agreement in steps 4 and 6; never a quantum


def context() -> Context:
    """Spec §2.2: every bridge step runs in this context; nothing is quantised."""
    return Context(prec=34, rounding=ROUND_HALF_EVEN)


def agree(x: Decimal, y: Decimal) -> bool:
    """D-5B.14: two values agree when `abs(x - y) <= SOLVE_TOLERANCE`."""
    with localcontext(context()):
        return abs(x - y) <= SOLVE_TOLERANCE
