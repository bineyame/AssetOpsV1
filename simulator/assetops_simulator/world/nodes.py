"""D-DD.62 (spec `specs/DD-demo-data/spec.md` §5.1, §5.2; D-DD.48, D-DD.50): the one table of the structure nodes the
emulated books carry, and the one October check.

`NODES[key]` holds, in dependency order, (node, the manifest's expression text, the same expression). `key` is a
`structures` key of the manifest (`MINI_GRID`, `COLD_CHAIN`). A parity test reads the manifest and asserts each text;
this module never reads it. `tools/dd_check.py` keeps its own evaluator on purpose (D-DD.55, independence).

Standard library only.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Mapping

NODES = {
    "MINI_GRID": (
        ("metered_kwh", "delivered_kwh - technical_loss_kwh - unexplained_loss_kwh",
         lambda v: v["delivered_kwh"] - v["technical_loss_kwh"] - v["unexplained_loss_kwh"]),
        ("billed_kwh", "metered_kwh - adjustments_kwh - unmapped_kwh",
         lambda v: v["metered_kwh"] - v["adjustments_kwh"] - v["unmapped_kwh"]),
        ("revenue", "billed_kwh * tariff + productive_kwh * productive_tariff",
         lambda v: v["billed_kwh"] * v["tariff"] + v["productive_kwh"] * v["productive_tariff"]),
        ("collected", "revenue - in_transit - outstanding",
         lambda v: v["revenue"] - v["in_transit"] - v["outstanding"]),
        ("diesel_l", "necessary_l + candidate_l + unexplained_l + extra_l",
         lambda v: v["necessary_l"] + v["candidate_l"] + v["unexplained_l"] + v["extra_l"]),
        ("fuel_cost", "diesel_l * diesel_price", lambda v: v["diesel_l"] * v["diesel_price"]),
    ),
    #: Money in integer cents. `contract_crate_days` and `contract_rate` are the constant 0 (factor_map).
    "COLD_CHAIN": (
        ("revenue", "crate_days * rate + contract_crate_days * contract_rate",
         lambda v: v["crate_days"] * v["rate"] + v["contract_crate_days"] * v["contract_rate"]),
        ("received", "revenue - outstanding", lambda v: v["revenue"] - v["outstanding"]),
    ),
}


def evaluate(key: str, leaves: Mapping) -> dict:
    """The nodes of `NODES[key]` that `leaves` reach. A node whose leaf is absent, and every node that depends on it,
    is left out."""
    nodes: dict = {}
    for name, _, fn in NODES[key]:
        try:
            nodes[name] = fn({**leaves, **nodes})
        except KeyError:
            continue
    return nodes


def emu_node(tenant: str, code: str, month: str, values: Mapping[str, Decimal | int],
             recorded: Mapping[str, Decimal | int | None], prefix: str = "") -> None:
    """The October check: a node the record also holds must equal it, or `EMU_NODE <tenant>/<code> <month> <node>`.
    `recorded` maps a node to the value the period record holds (None or a node `values` lacks is not compared);
    `prefix` names the side of the record in the message (`plan.`)."""
    for node, held in recorded.items():
        if node in values and held is not None and held != values[node]:
            raise ValueError(f"EMU_NODE {tenant}/{code} {month} {prefix}{node}")
