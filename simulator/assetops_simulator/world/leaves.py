"""Leaf identities at month grain (spec §4.4; D-DS1.1).

The single mapping point the canonical format version 1 (`2a`) replaces: today the
history is keyed by the manifest's own leaf keys, and a money leaf is known by name.
"""

from __future__ import annotations

MONEY_LEAVES = frozenset(
    {"energy_cost", "in_transit", "liability", "maint", "maintenance", "om", "outstanding", "staff", "total"}
)


def is_money(leaf: str) -> bool:
    return leaf in MONEY_LEAVES
