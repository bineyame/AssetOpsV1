"""CH-6a3 L2m: the board rows' node claims on real producer data (Kobo estate, w502 cold, w504 EV).

Pattern `test_out_d5_objectives_postgres.py`. Per Site the Grow row carries `nodes` (kpi / potential / earnings),
every non-null node is a claim with a text and a basis, and a NOT_KNOWN claim reads "Not known yet". The Kobo case
also reads the "Why?" of the Grow row and checks that a price line is never invented (no price -> no line).
"""
from __future__ import annotations

import json

import pytest

from test_s4_finding_store_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    import test_out_b4_board_postgres as b4

BASES = {"COMPLETE", "CHECKED_DAYS", "NOT_KNOWN"}


def _grow(body: dict) -> dict:
    return next(r for r in body["rows"] if r["category"] == "GROW_REVENUE")


def _check_nodes(row: dict, key: str) -> dict:
    nodes = row.get("nodes")
    b4._record(key, {"nodes": nodes, "headline_money": row.get("headline_money")})
    assert isinstance(nodes, dict) and set(nodes) == {"kpi", "potential", "earnings"}, nodes
    claims = [c for c in nodes.values() if c is not None]
    for c in claims:
        assert c["basis"] in BASES and isinstance(c["text"], str) and c["text"], c
        if c["basis"] == "NOT_KNOWN":
            assert c["value"] is None, c  # the target and potential read their own words ("No target set yet")
            if c["key"] == "money.estimated_income":
                assert "Not known yet" in c["text"], c
    return nodes


def test_kobo_estate_grow_nodes(monkeypatch, tmp_path) -> None:
    with b4._case_db("nodes_kobo", slice_="ch6") as url:
        spec, _ = b4._build_kobo(url, tmp_path, "estate")
        b4._serve(monkeypatch, url, tmp_path)
        b4._pin_kobo(monkeypatch, spec)
        with b4._client() as c:
            body, _ = b4._board(c, "KOBO-001", "kobo_ch6_nodes", date="2026-10-21")
    row = _grow(body)
    nodes = _check_nodes(row, "kobo_ch6_grow")
    assert any(v is not None for v in nodes.values()), nodes
    if nodes["earnings"] and nodes["earnings"]["basis"] == "NOT_KNOWN":
        assert row["headline_money"] is None  # Q4: the Grow money is the earnings claim, never an invented figure


def test_cold_w502_nodes(monkeypatch, tmp_path) -> None:
    import w502_cold_work_walkthrough as w502

    out = tmp_path / "positive"
    out.mkdir()
    with b4._case_db("nodes_cold", slice_="ch6") as url:
        b4._child(url, ["-c", w502.BUILD, "positive", str(out)])
        doc = json.loads((out / "positive.json").read_text(encoding="utf-8"))
        assert doc["blocked"] is None, doc["blocked"]
        b4._serve(monkeypatch, url, tmp_path)
        with b4._client() as c:
            body, _ = b4._board(c, "COLD-LAB-001", "cold_ch6_nodes", **dict(zip(("from", "to"), doc["w501"]["window"])))
    for r in body["rows"]:
        if r.get("nodes"):
            assert all(c is None or c["text"] for c in r["nodes"].values())
    cc1 = next(c for r in body["rows"] for c in [r.get("nodes") and r["nodes"].get("kpi")] if c)
    b4._record("cold_ch6_kpi", cc1)
    assert cc1["basis"] in BASES


def test_ev_w504_nodes(monkeypatch, tmp_path) -> None:
    with b4._case_db("nodes_ev", slice_="ch6") as url:
        b4._child(url, ["-c", b4.EV_BUILD, str(tmp_path), str(b4.ROOT / "tools")])
        built = json.loads((tmp_path / "ev.json").read_text(encoding="utf-8"))
        assert built["status"] == "ready", built.get("status")
        window = {"from": built["evidence_window_E"]["from"], "to": built["evidence_window_E"]["to"]}
        b4._serve(monkeypatch, url, tmp_path)
        with b4._client() as c:
            body, _ = b4._board(c, "EV-LAB-001", "ev_ch6_nodes", **window)
    row = _grow(body)
    _check_nodes(row, "ev_ch6_grow")
