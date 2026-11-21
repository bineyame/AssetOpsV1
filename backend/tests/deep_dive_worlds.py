"""5c rev 4 (spec section 11, D-5C.26 to D-5C.28): the served worlds the view tests and the screen's generator share.

Test support, no database. World H is unit 1's World H (Kobo's litres, nested drivers, D-5C.21). World X ("currency
mismatch") is World H with Kobo's figures in KES and its O&M and staff not compared, Kisiwa in USD with its fuel cost
not compared, and Mto's actual in KES against a USD target: R holds two currencies (no gap, the L7 headline), Mto is
out with the M3 line, and the Optimize heading would add KES fuel cost to USD O&M (its card has no figure and no word).
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from assetops_backend.deep_dive import tables as T
from assetops_backend.deep_dive import view as V
from assetops_backend.structure.attribution.bridge import bridge
from assetops_backend.structure.registry import REGISTRIES

MG = REGISTRIES["MINI_GRID"]


def in_kes(row):
    """`row` and its parts in KES (a row with no currency keeps none)."""
    return replace(row, currency="KES" if row.currency is not None else None, rows=tuple(in_kes(c) for c in row.rows))


def gone(row, factor_id: str):
    """`row` with `factor_id`'s own row not compared (its records missing): no effect, no split."""
    if row.factor_id == factor_id and row.kind != "RESIDUAL":
        return replace(row, gap=None, effect=None, evidence="NOT_AVAILABLE", origins=(), split="NOT_SPLIT",
                       reason="GAP_NOT_AVAILABLE", rows=())
    return replace(row, rows=tuple(gone(c, factor_id) for c in row.rows))


def world_h(**kwargs) -> dict:
    import test_5c_deep_dive_view as t  # the view tests own the served worlds; imported here to avoid a cycle
    return t.view("H", **kwargs)


def _x(sb):
    root = sb.roots[T.ROOT]
    if sb.site_code == "KOBO-001":
        return replace(sb, roots={**{k: in_kes(r) for k, r in sb.roots.items()},
                                  T.ROOT: in_kes(gone(gone(root, "om"), "staff"))})
    if sb.site_code == "KISIWA-001":
        return replace(sb, roots={**sb.roots, T.ROOT: gone(root, "fuel_cost")})
    values = {f: (replace(x, currency="KES") if x.currency is not None else x) for f, x in sb.actual.values.items()}
    roots = {k: bridge(MG, values, sb.targets.structure.values, k) for k in sb.roots}
    return replace(sb, roots=roots, actual=replace(sb.actual, values=values))


def world_x(**kwargs) -> dict:
    """World X's payload; the `site_bridge` patch is applied and undone inside this call."""
    real = V.site_bridge
    mp = pytest.MonkeyPatch()
    mp.setattr(V, "site_bridge", lambda inputs, targets: _x(real(inputs, targets)))
    try:
        return world_h(**kwargs)
    finally:
        mp.undo()
