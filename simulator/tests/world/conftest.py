"""DS1a: the world generator's tests (spec `specs/DS1-history-generator/spec.md` §10).

`--update-golden` rewrites `golden/history_v1.json`; nothing else does. A commit
that uses it names the input that changed (spec §4.5).
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
REPOSITORY_ROOT = HERE.parents[2]
FIXTURE = HERE / "fixtures" / "view_v1.json"
GOLDEN = HERE / "golden" / "history_v1.json"
CLI = REPOSITORY_ROOT / "tools" / "world_history.py"


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--update-golden",
        action="store_true",
        default=False,
        help="DS1a: rewrite simulator/tests/world/golden/history_v1.json from the fixture view",
    )


_FIXTURE_CACHE: dict = {}


def load_fixture() -> dict:
    """A fresh deep copy of the fixture view, so a test may plant changes in it."""
    if "view" not in _FIXTURE_CACHE:
        _FIXTURE_CACHE["view"] = json.loads(FIXTURE.read_text(encoding="utf-8"))
    return copy.deepcopy(_FIXTURE_CACHE["view"])


@pytest.fixture
def view() -> dict:
    return load_fixture()


def tenant_of(doc: dict, name: str) -> dict:
    return next(t for t in doc["tenants"] if t["tenant"] == name)


def site_of(doc: dict, tenant: str, site: str) -> dict:
    return next(s for s in tenant_of(doc, tenant)["sites"] if s["site"] == site)


def scope_blocks(history: dict) -> dict:
    """`{scope_key: block}` read from a history document's own layout (§7.1)."""
    out = {}
    for tenant, sites in history["tenants"].items():
        for site, months in sites.items():
            for month, block in months.items():
                out[f"{tenant}/{site}/{month}"] = block
    return out
