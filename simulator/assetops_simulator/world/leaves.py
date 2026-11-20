"""Money record fields at month grain (spec §4.4; D-DS1.1; D-DS1B.2).

`MONEY_LEAVES` names history *record fields* that hold money (written in cents), not
factor IDs: the history's fields (`total`, `energy_cost` and so on) are record names.
Factor IDs and units come only from `assetops_contracts.canonical`; the mapping from a
record field to a leaf factor is DS1b's (`records.PASS_THROUGH`, `records.ACTUAL_WRITERS`).
"""

from __future__ import annotations

MONEY_LEAVES = frozenset(
    {"energy_cost", "in_transit", "liability", "maint", "maintenance", "om", "outstanding", "staff", "total"}
)


def is_money(leaf: str) -> bool:
    return leaf in MONEY_LEAVES
