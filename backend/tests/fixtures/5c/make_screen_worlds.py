"""5c screen fix: writes the screen's served worlds from the backend's own view (never by hand).

The worlds come only from `backend/tests/deep_dive_worlds.py` (spec section 11, screen fix 1): World H
(`world_h()`, Kobo's litres, nested drivers, D-5C.21) and World X (`world_x()`, the currency mismatch: R in two
currencies, Mto out with the M3 line, no gap so no share, bar or scale, D-5C.26 to D-5C.28).
`test_5c_screen_worlds_fresh.py` fails when the committed files differ from these bytes.

Run from `backend/`: PYTHONPATH=$PWD:$PWD/tests:$PWD/../contracts:$PWD/../simulator python tests/fixtures/5c/make_screen_worlds.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from deep_dive_worlds import world_h, world_x

OUT = Path(__file__).resolve().parents[4] / "frontend" / "src" / "estate" / "__tests__" / "fixtures"
FILES = {"deep_dive_world_h.json": world_h, "deep_dive_currency_mismatch.json": world_x}


def text(body: dict) -> str:
    return json.dumps(body, ensure_ascii=False, indent=2) + "\n"


def worlds() -> dict[str, str]:
    """Each committed file's name and the text the backend builds for it now."""
    return {name: text(build()) for name, build in FILES.items()}


def main() -> None:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    for name, body in worlds().items():
        (out / name).write_text(body, encoding="utf-8")
        print(out / name)


if __name__ == "__main__":
    main()
