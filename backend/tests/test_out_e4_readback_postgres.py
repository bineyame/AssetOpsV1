"""OUT-E E4: the Kobo `verified` cost check read back on the real Site outcome board (`.agent/build-sheet-OUT-E.md`).

The s602b `verified` case builds in a child into a fresh `assetops_out_e_board_test` database (the OUT-B4 helpers:
`_case_db`, `_build_kobo`, `_serve`, `_pin_kobo` with the case's `pinned_at`), the OUT-D demo objectives are declared
through `declare_objective fixture` (MG-2 target 0), and the board is read on the UTC day of the later hour's end.

Architect ruling 2026-10-31 (option b; a modelled cost claim never goes in the Protect row): this test asserts what
the data shows. The board day's Finding index is UNASSESSED (OUT-B4 Addendum 6), so the origin Finding is outside the
one-day view and B-Q18 places the Action under Protect: its Earlier entry carries no detail and the Cost Earlier list
is empty. The Assure Verified results line carries the modelled change. The Cost-row cost line and before/after
line are proven by the fake-port tests (`test_out_e4_readback.py`); register R595 (open) holds the real-data
Cost-row read-back until the combined dataset makes the Finding index current on the board day.
"""

from __future__ import annotations

import json

import pytest

from test_s4_finding_store_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

PROTECT = "Verified on test data · linked finding outside this view"
ASSURE = "ACT-000001 verified on test data · modelled change 0.042–0.046 USD less per kWh of feeder demand"
CODES = ("MODELLED_IMPROVEMENT", "MODELLED_NO_IMPROVEMENT", "UNAVAILABLE", "OUTCOME_INCONCLUSIVE",
         "trial-fuel-comparison", "candidate", "VERIFIED")


@pytest.fixture(scope="module")
def kobo_verified(tmp_path_factory):
    from test_out_b4_board_postgres import _build_kobo, _case_db
    from test_out_d5_objectives_postgres import _declare

    work = tmp_path_factory.mktemp("verified")
    with _case_db("board", "e") as url:
        spec, _ = _build_kobo(url, work, "verified")
        declared = _declare(url)
        yield url, work, spec, declared


def _texts(value) -> list[str]:
    if isinstance(value, dict):
        return [t for v in value.values() for t in _texts(v)]
    if isinstance(value, list):
        return [t for v in value for t in _texts(v)]
    return [value] if isinstance(value, str) else []


def test_kobo_verified_protect_entry_and_assure_read_back(kobo_verified, monkeypatch) -> None:
    from test_out_b4_board_postgres import _board, _client, _pin_kobo, _record, _serve

    url, work, spec, declared = kobo_verified
    _record("out_e4_spec", {k: spec.get(k) for k in ("outcome", "outcome_reasons", "pinned_at", "windows")})
    assert any(d.get("outcome_key") == "MG-2" for d in declared), declared
    day = spec["windows"]["later"]["end"][:10]
    _serve(monkeypatch, url, work)
    _pin_kobo(monkeypatch, spec)
    with _client() as c:
        body, failed = _board(c, "KOBO-001", "out_e4_verified", date=day)
    _record("out_e4_earlier", {r["category"]: r["earlier"] for r in body["rows"]})
    rows = {r["category"]: r for r in body["rows"]}
    assert rows["OPTIMIZE_COST"]["earlier"] == []
    entry = next(e for e in rows["PROTECT_ASSET"]["earlier"] if e["text"].startswith("ACT-000001"))
    assert (entry["result_label"], entry["detail"]) == (PROTECT, None)
    assert all(e["detail"] is None for r in rows.values() for e in r["earlier"])
    assure = [c["text"] for c in rows["ASSURE_PERFORMANCE"]["contributors"] if c["key"] == "verified_results"]
    assert assure == [ASSURE]
    shown = [t for r in body["rows"] for t in _texts({k: r[k] for k in ("contributors", "earlier", "issues",
                                                                         "in_hand", "options")})]
    assert [(t, code) for t in shown for code in CODES if code in t] == []
    assert "not realised savings" not in json.dumps(body)  # no cost line outside the Cost row
