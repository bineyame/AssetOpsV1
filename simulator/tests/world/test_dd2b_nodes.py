"""D-DD.62 (spec `specs/DD-demo-data/spec.md` §5.1, §5.2): one NODES table and one October check, for the mini-grid
and cold-chain structures; the manifest is read here, never by the emulator."""

from __future__ import annotations

from decimal import Decimal

import pytest

from assetops_simulator.world import exports, exports_cold
from assetops_simulator.world.nodes import NODES, emu_node, evaluate

from .books_support import manifest


def test_n1_one_table_for_both_structures() -> None:
    assert sorted(NODES) == ["COLD_CHAIN", "MINI_GRID"]
    assert not hasattr(exports, "NODES")  # the old copies are deleted: cold reads the same object
    assert exports_cold.NODES is NODES


@pytest.mark.parametrize("key", sorted(NODES))
def test_n2_every_node_is_the_manifests_text(key: str) -> None:
    structure = manifest()["structures"][key]
    assert [name for name, _, _ in NODES[key]] == {
        "MINI_GRID": ["metered_kwh", "billed_kwh", "revenue", "collected", "diesel_l", "fuel_cost"],
        "COLD_CHAIN": ["revenue", "received"]}[key]
    for name, text, _ in NODES[key]:
        assert text == structure[name], (key, name)


def test_n3_evaluate_leaves_out_a_node_whose_leaf_is_absent() -> None:
    leaves = {"crate_days": 10, "rate": 20, "contract_crate_days": 0, "contract_rate": 0}
    assert evaluate("COLD_CHAIN", leaves) == {"revenue": 200}  # `received` needs `outstanding`
    assert evaluate("COLD_CHAIN", leaves | {"outstanding": 50}) == {"revenue": 200, "received": 150}


def test_n4_emu_node_is_the_one_october_check() -> None:
    emu_node("t", "S-1", "2026-10", {"revenue": Decimal("5.00")}, {"revenue": Decimal("5"), "received": None})
    with pytest.raises(ValueError, match=r"^EMU_NODE t/S-1 2026-10 revenue$"):
        emu_node("t", "S-1", "2026-10", {"revenue": 5}, {"revenue": 6})
    with pytest.raises(ValueError, match=r"^EMU_NODE t/S-1 2026-10 plan\.revenue$"):
        emu_node("t", "S-1", "2026-10", {"revenue": 5}, {"revenue": 6}, "plan.")
