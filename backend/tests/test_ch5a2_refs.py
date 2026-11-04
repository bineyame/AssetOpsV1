"""CH-5a2a L0: `href_for` against the shared route fixture, and body `href` == `href_for(link_ref)` parity."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from assetops_backend.chain import refs as R

FIXTURE = Path(__file__).resolve().parents[2] / "frontend" / "src" / "shell" / "__fixtures__" / "route-refs.json"
ROWS = json.loads(FIXTURE.read_text(encoding="utf-8"))


@pytest.mark.parametrize("row", ROWS, ids=[r["name"] for r in ROWS])
def test_href_for_matches_shared_fixture(row):
    assert R.href_for(row["ref"]) == row["path"]


def test_fixture_covers_every_kind_and_view():
    assert {r["ref"]["kind"] for r in ROWS} == set(R.KINDS)
    assert {r["ref"].get("view", "home") for r in ROWS if r["ref"]["kind"] == "SITE"} == set(R.SITE_VIEWS)
    assert {r["ref"]["view"] for r in ROWS if r["ref"]["kind"] == "ESTATE"} == set(R.ESTATE_VIEWS)
    assert {r["ref"]["view"] for r in ROWS if r["ref"]["kind"] == "FINDING" and "view" in r["ref"]} == set(
        R.FINDING_VIEWS)
    assert {r["ref"]["view"] for r in ROWS if r["ref"]["kind"] == "ACTION" and "view" in r["ref"]} == set(
        R.ACTION_VIEWS)


def test_no_fixture_path_is_an_api_path():
    assert not [r for r in ROWS if (r["path"] or "").startswith("/api")]


def test_thread_and_none_have_no_screen():
    assert R.href_for(None) is None
    assert R.href_for(R.thread_ref("KOBO-001", "t")) is None


@pytest.mark.parametrize("bad", [{"kind": "SITE", "site": "S", "view": "nope"}, {"kind": "ESTATE", "view": "/x"},
                                 {"kind": "PATH", "path": "/api/x"}, {"kind": "FINDING", "site": "S", "id": "f",
                                                                     "view": "nope"}])
def test_unknown_kind_or_view_raises(bad):
    with pytest.raises(ValueError):
        R.href_for(bad)


def test_refs_module_holds_no_outcome_id():
    """OL-1: refs.py names no outcome category."""
    text = Path(R.__file__).read_text(encoding="utf-8")
    for outcome in ("GROW_REVENUE", "OPTIMIZE_COST", "PROTECT_ASSET", "ASSURE_PERFORMANCE"):
        assert outcome not in text
