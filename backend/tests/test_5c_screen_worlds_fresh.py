"""5c screen fix, test 17 (L4; no database): the screen's committed worlds equal what the backend builds now."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

GEN = Path(__file__).resolve().parent / "fixtures" / "5c" / "make_screen_worlds.py"


def _generator():
    spec = importlib.util.spec_from_file_location("make_screen_worlds", GEN)
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(GEN.parents[2]))  # backend/tests, for deep_dive_worlds
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.path.remove(str(GEN.parents[2]))
    return mod


GENERATOR = _generator()


@pytest.mark.parametrize("name", sorted(GENERATOR.FILES))
def test_17_screen_world_is_fresh(name):
    fresh = GENERATOR.worlds()[name].encode("utf-8")
    committed = (GENERATOR.OUT / name).read_bytes()
    assert committed == fresh, f"{name} is stale: rerun make_screen_worlds.py (backend/tests/fixtures/5c/)"
