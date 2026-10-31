"""OUT-E E4: the Kobo `verified` cost check read back on the real Site outcome board (`.agent/build-sheet-OUT-E.md`).

The s602b `verified` case builds in a child into a fresh `assetops_out_e_board_test` database (the OUT-B4 helpers:
`_case_db`, `_build_kobo`, `_serve`, `_pin_kobo` with the case's `pinned_at`), the OUT-D demo objectives are declared
through `declare_objective fixture` (MG-2 target 0), and the board is read on the UTC day of the later hour's end.
The Cost row's Earlier ACT-048 entry keeps today's VERIFIED label and gains the modelled change and the before/after
line; the Assure row's Verified results line adds the modelled change; no reason or state code is on the page.
"""

from __future__ import annotations

import json

import pytest

from test_s4_finding_store_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

DETAIL = ("Modelled change after the trial · not realised savings: 0.042–0.046 USD less per kWh of feeder demand · "
          "Supply cost per kWh before the trial: missed · after: met")
ASSURE = "ACT-048 verified on test data · modelled change 0.042–0.046 USD less per kWh of feeder demand"
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


def test_kobo_verified_cost_row_and_assure_read_back(kobo_verified, monkeypatch) -> None:
    from test_out_b4_board_postgres import _board, _client, _pin_kobo, _record, _serve

    url, work, spec, declared = kobo_verified
    _record("out_e4_spec", {k: spec.get(k) for k in ("outcome", "outcome_reasons", "pinned_at", "windows")})
    assert any(d.get("outcome_key") == "MG-2" for d in declared), declared
    day = spec["windows"]["later"]["end"][:10]
    _serve(monkeypatch, url, work)
    _pin_kobo(monkeypatch, spec)
    with _client() as c:
        summary = c.get(f"/api/sites/KOBO-001/actions/{spec['action']}/verification")
        body, failed = _board(c, "KOBO-001", "out_e4_verified", date=day)
    _record("out_e4_summary", summary.json() if summary.status_code == 200 else summary.status_code)
    rows = {r["category"]: r for r in body["rows"]}
    entry = next(e for e in rows["OPTIMIZE_COST"]["earlier"] if e["text"].startswith("ACT-048"))
    _record("out_e4_cost_earlier", entry)
    assert entry["result_label"] == "Verified on test data"
    assert entry["detail"] == DETAIL
    others = [e for r in rows.values() for e in r["earlier"] if e is not entry]
    assert all(e["detail"] is None for e in others), others
    assure = [c for c in rows["ASSURE_PERFORMANCE"]["contributors"] if c["key"] == "verified_results"]
    _record("out_e4_assure", assure)
    assert [c["text"] for c in assure] == [ASSURE]
    shown = [t for r in body["rows"] for t in _texts({k: r[k] for k in ("contributors", "earlier", "issues",
                                                                         "in_hand", "options")})]
    assert [(t, code) for t in shown for code in CODES if code in t] == []
    assert json.dumps(body).count("not realised savings") == 1
