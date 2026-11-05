"""CH-5b1 R6 (CH5b1-R Q3): write the generated chain diagram, `Docs/demo-sprint/chain-graph.{dot,svg}`.

    python tools/chain_graph_render.py

The backend writes no files (configuration-persistence guard), so the render lives in `chain/graph.py` and this tool
only saves it. It refuses to write a broken graph. `backend/tests/test_ch5b_graph.py` diffs the committed files with a
fresh render; check-all runs `python -m assetops_backend.chain.graph check` only and never rewrites them.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "Docs" / "demo-sprint"
sys.path.insert(0, str(REPO / "backend"))
sys.path.insert(0, str(REPO / "contracts"))


def main() -> int:
    from assetops_backend.chain.composition import declared_graph_inputs
    from assetops_backend.chain.graph import ChainGraphError, check, render_dot, render_svg

    g = declared_graph_inputs()
    try:
        check(g)
    except ChainGraphError as exc:
        print(f"FAIL {exc}")
        return 1
    for name, text in (("chain-graph.dot", render_dot(g)), ("chain-graph.svg", render_svg(g))):
        (OUT / name).write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote {OUT / name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
