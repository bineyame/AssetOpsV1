"""5c unit 3: writes the screen's served worlds from the backend's own view (never by hand).

World H is unit 1's World H (Kobo's litres, nested drivers, D-5C.21). World X ("currency mismatch") is World H with
Kobo's figures in KES and its O&M and staff not compared, Kisiwa in USD with its fuel cost not compared, and Mto's
actual in KES against a USD target. So R holds two currencies (the L7 headline), Mto is out with the M3 line, and
the Optimize heading would add KES fuel cost to USD O&M (its card reads "Not available yet" for figure and word, L9).

Run from `backend/`: PYTHONPATH=$PWD:$PWD/tests:$PWD/../contracts:$PWD/../simulator python tests/fixtures/5c/make_screen_worlds.py
"""
from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path

import pytest

import test_5c_deep_dive_view as t
from assetops_backend.deep_dive import tables as T
from assetops_backend.deep_dive import view as V
from assetops_backend.structure.attribution.bridge import bridge

OUT = Path(__file__).resolve().parents[4] / "frontend" / "src" / "estate" / "__tests__" / "fixtures"


def world_x():
    real = V.site_bridge

    def site_bridge(inputs, targets):
        sb = real(inputs, targets)
        root = sb.roots[T.ROOT]
        if sb.site_code == "KOBO-001":
            return replace(sb, roots={**{k: t._in_kes(r) for k, r in sb.roots.items()},
                                      T.ROOT: t._in_kes(t._gone(t._gone(root, "om"), "staff"))})
        if sb.site_code == "KISIWA-001":
            return replace(sb, roots={**sb.roots, T.ROOT: t._gone(root, "fuel_cost")})
        values = {f: (replace(x, currency="KES") if x.currency is not None else x) for f, x in sb.actual.values.items()}
        roots = {k: bridge(t.MG, values, sb.targets.structure.values, k) for k in sb.roots}
        return replace(sb, roots=roots, actual=replace(sb.actual, values=values))

    mp = pytest.MonkeyPatch()
    mp.setattr(V, "site_bridge", site_bridge)
    try:
        return t.view("H")
    finally:
        mp.undo()


def main() -> None:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    worlds = {"deep_dive_world_h.json": t.view("H"), "deep_dive_currency_mismatch.json": world_x()}
    for name, body in worlds.items():
        (out / name).write_text(json.dumps(body, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(out / name)


if __name__ == "__main__":
    main()
