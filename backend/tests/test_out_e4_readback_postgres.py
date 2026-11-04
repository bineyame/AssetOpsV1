"""OUT-E E4: the Kobo `verified` cost check read back on the real Site outcome board (`.agent/build-sheet-OUT-E.md`).

The s602b `verified` case builds in a child into a fresh `assetops_out_e_board_test` database (the OUT-B4 helpers:
`_case_db`, `_build_kobo`, `_serve`, `_pin_kobo` with the case's `pinned_at`), the OUT-D demo objectives are declared
through `declare_objective fixture` (MG-2 target 0), and the board is read on the UTC day of the later hour's end.

Architect ruling 2026-10-31 (option b; a modelled cost claim never goes in the Protect row). Since IDX-GAPS
(`finding-index/2`, Addendum 2) the board day's Finding index reads PARTIAL with the origin Finding's day assessed, so
the Finding is in view: the Cost Earlier list holds ACT-000001 with the modelled cost line, Protect lists it in the
safeguard form with no detail, and the Assure Verified results line carries the modelled change. Register R595 is
resolved by IDX-GAPS (400d1096b); the fake-port tests (`test_out_e4_readback.py`) keep the before/after variants.
"""

from __future__ import annotations

import json

import pytest

from test_s4_finding_store_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

#: IDX-GAPS (R595 resolved): the board day's Finding index is PARTIAL with the day assessed, so ACT-000001's linked
#: Finding is in view: Protect lists the safeguard check, and the Action reads back under Cost.
PROTECT = "Reliable service and battery and generator life checked as safeguards in ACT-001"
COST_DETAIL = ("Estimated effect of the trial (not money saved): 0.042–0.046 USD less supply cost per kWh."
               " Goal before the trial: missed; after: met · checked over 11:00–12:00 on 2 Nov.")  # CH-3 I-11 scope
ASSURE = ("ACT-001 verified on example data: estimated effect of the trial (not money saved): 0.042–0.046 USD less "
          "supply cost per kWh")
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
    from test_out_b4_board_postgres import _board, _client, _pin_kobo, _record, _serve, _settle_chain

    url, work, spec, declared = kobo_verified
    _record("out_e4_spec", {k: spec.get(k) for k in ("outcome", "outcome_reasons", "pinned_at", "windows")})
    assert any(d.get("outcome_key") == "MG-2" for d in declared), declared
    day = spec["windows"]["later"]["end"][:10]
    _settle_chain(url, "KOBO-001")  # CH-5a1 R8: the board reads the chain (threads consumed, snapshots)
    _serve(monkeypatch, url, work)
    _pin_kobo(monkeypatch, spec)
    with _client() as c:
        body, failed = _board(c, "KOBO-001", "out_e4_verified", date=day)
        # CH-5a1 (lineage deleted, §A4): Must-not-harm follows the thread join (test_out_b4_board_postgres)
        _record("out_e4_must_not_harm", {r["category"]: r for r in body["rows"]}["OPTIMIZE_COST"]["must_not_harm"])
    _record("out_e4_earlier", {r["category"]: r["earlier"] for r in body["rows"]})
    rows = {r["category"]: r for r in body["rows"]}
    cost = rows["OPTIMIZE_COST"]["earlier"]
    assert [(e["text"], e["result_label"], e["detail"]) for e in cost] == [
        ("ACT-001", "Verified on example data", COST_DETAIL)], cost
    assert cost[0]["href"].startswith("/sites/KOBO-001/actions/")
    entry = next(e for e in rows["PROTECT_ASSET"]["earlier"] if e["text"] == PROTECT)
    assert (entry["result_label"], entry["detail"]) == ("Verified on example data", None)
    assert entry["href"].startswith("/sites/KOBO-001/actions/") and "/verification?event_id=" in entry["href"]
    assert "outside this view" not in json.dumps(body["rows"])
    # IDX-GAPS: only the Cost row's Earlier entry carries a detail (the modelled change pinned above)
    assert all(e["detail"] is None for c, r in rows.items() if c != "OPTIMIZE_COST" for e in r["earlier"])
    assure = [c["text"] for c in rows["ASSURE_PERFORMANCE"]["contributors"] if c["key"] == "verified_results"]
    assert assure == [ASSURE]
    shown = [t for r in body["rows"] for t in _texts({k: r[k] for k in ("contributors", "earlier", "issues",
                                                                         "in_hand", "options")})]
    assert [(t, code) for t in shown for code in CODES if code in t] == []
    # the cost line sits in the Cost row and may sit in Assure's verified-results line (R594); nowhere else in the
    # whole board body (IDX-GAPS U2 review L1)
    assert "not money saved" in json.dumps(rows["OPTIMIZE_COST"])
    rest = {k: v for k, v in body.items() if k != "rows"}
    rest["rows"] = [r if r["category"] != "ASSURE_PERFORMANCE" else
                    {**r, "contributors": [c for c in r["contributors"] if c["key"] != "verified_results"]}
                    for r in body["rows"] if r["category"] != "OPTIMIZE_COST"]
    assert "not money saved" not in json.dumps(rest)
