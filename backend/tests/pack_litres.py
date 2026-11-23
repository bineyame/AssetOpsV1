"""Tests' litre leaves for the pack worlds (DD3d.4, D-DD.163).

A world that states its fuel by invoices holds no litres, so it serves no fuel cost (D-DD.177). The 5b, 5c, 3b7a and
portfolio worlds need the pack's figures, so they read October's three litre leaves from the pack's own derived
values (`derived-values.json`, the file `M` derives), never typed here. Each is MODELLED, origin unknown, source
`test:M-october-litres`, as the DDR fixture's. Any other Site or month takes the wrapped source."""
from __future__ import annotations

import json
from collections.abc import Mapping
from decimal import Decimal
from pathlib import Path

from assetops_backend.structure.evaluate import ORIGIN_UNKNOWN, LeafValue
from assetops_backend.structure.sources import ReadContext

PACK = (Path(__file__).resolve().parents[2] / "Docs" / "demo-sprint" / "product-direction-layer4"
        / "derived-values.json")
LEAVES = ("necessary_l", "candidate_l", "unexplained_l")
SOURCE = ("test:M-october-litres",)
_NAME = {"KOBO-001": "lakeside-power/Kobo", "KISIWA-001": "lakeside-power/Kisiwa", "MTO-001": "lakeside-power/Mto"}


def pack_litres(site_code: str) -> dict[str, Decimal]:
    nodes = json.loads(PACK.read_text(encoding="utf-8"), parse_float=Decimal)["sites"][_NAME[site_code]]["actual"][
        "nodes"]
    return {leaf: nodes[leaf] for leaf in LEAVES}


class PackLitres:
    """`LeafSource` for the lakeside mini-grids' October: their litre leaves from the pack, the rest from `inner`.

    `litres` (Site code to its three leaves) replaces the pack's for the Sites it names; a test that needs other litres
    than the pack's states them there, beside what it asserts."""

    def __init__(self, inner, litres: Mapping[str, Mapping[str, Decimal]]) -> None:
        self._inner, self._litres = inner, litres

    def leaf(self, ctx: ReadContext, factor_id: str) -> LeafValue:
        code = ctx.site.site_code
        if factor_id in LEAVES and ctx.month == "2026-10" and (code in self._litres or code in _NAME):
            held = self._litres[code] if code in self._litres else pack_litres(code)
            return LeafValue(held[factor_id], "MODELLED", SOURCE, None, None, None, (ORIGIN_UNKNOWN,))
        return self._inner.leaf(ctx, factor_id)


def with_litres(inner=None, litres: Mapping[str, Mapping[str, Decimal]] | None = None) -> PackLitres:
    from test_4b_money_leaves import fallback

    return PackLitres(inner or fallback(), litres or {})
