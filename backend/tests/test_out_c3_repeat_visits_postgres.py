"""OUT-C U3: GreenHarvest repeat visits on real Postgres (build sheet OUT-C §2 U3, acceptance 3 and P-C1).

BUILDs the w502 `positive` dataset (with the OUT-C authored visits and plans) in `assetops_out_c_cold_test`, reads
the board on the W5-01 window with no `known_at`, and records P-C1: the estate summary over the covering UTC day
`[D, D+1)`. P-C1 is asserted only when GreenHarvest's summary Cost row reads NEEDS_ATTENTION with one warning;
otherwise the honest state is printed and estate acceptance is carried to the combined dataset."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from test_out_b4_board_postgres import _board, _case_db, _child, _client, _record, _serve, _states
from test_out_c1_never_money import money_hits

REPEATED = "REPEATED_MAINTENANCE_NO_RESULT"


def _day(iso_text: str) -> datetime:
    at = datetime.fromisoformat(iso_text.replace("Z", "+00:00")).astimezone(timezone.utc)
    return at.replace(hour=0, minute=0, second=0, microsecond=0)


def _z(at: datetime) -> str:
    return at.strftime("%Y-%m-%dT%H:%M:%SZ")


def test_cold_repeat_visits_board_and_estate(monkeypatch, tmp_path) -> None:
    import w502_cold_work_walkthrough as w502

    out = tmp_path / "positive"
    out.mkdir()
    with _case_db("cold", "c") as url:
        _child(url, ["-c", w502.BUILD, "positive", str(out)])
        doc = json.loads((out / "positive.json").read_text(encoding="utf-8"))
        assert doc["blocked"] is None, doc["blocked"]
        oc = doc["out_c"]
        assert [len(oc[k]) for k in ("cases", "records", "plans")] == [2, 2, 2], oc
        _record("out_c_authored", oc)
        _serve(monkeypatch, url, tmp_path)
        lo, hi = doc["w501"]["window"]
        with _client() as c:
            body, _ = _board(c, "COLD-LAB-001", "out_c_cold_board", **{"from": lo, "to": hi})
            day = _day(lo)  # D: the w502 day (the W5-01 window lies inside it)
            r = c.get("/api/estate/outcome-summary", params={"from": _z(day), "to": _z(day + timedelta(days=1))})
            summary = (r.status_code, r.json())

    # the board (acceptance 3)
    warnings = body["warnings"]
    repeats = [w for w in warnings if w["kind"] == REPEATED]
    assert len(repeats) == 1 and repeats[0]["count"] == 3, warnings
    rows = {r["category"]: r for r in body["rows"]}
    cost, protect = rows["OPTIMIZE_COST"], rows["PROTECT_ASSET"]
    assert _states(body)[1] == "NEEDS_ATTENTION"
    assert cost["state"] == "NEEDS_ATTENTION" and cost["lead_outcome"] == {"key": "CC-3",
                                                                           "label": "Cost per cooling unit"}
    assert cost["headline"] == "3 repair visits in 60 days without a result"
    assert [e["result_label"] for e in cost["earlier"]] == ["Did not fix it", "Did not fix it", "Not yet verified"]
    assert cost["must_not_harm"] is not None and cost["must_not_harm"]["href"], cost["must_not_harm"]
    assert cost["must_not_harm"]["text"].endswith(": a repair counts only when the fault it answers stops")
    plan_issue = [i for i in protect["issues"] if i["text"] == "Witnessed backup start test overdue"]
    assert [i["kind"] for i in plan_issue] == ["EARLY_WARNING"], protect["issues"]
    coil = [i for i in protect["in_hand"] if "Compressor coil cleaning" in i["text"]]
    assert [i["state_label"] for i in coil] == ["Due soon"], protect["in_hand"]
    assert money_hits(warnings) == []
    assert not [k for k in ("amount", "amount_low", "amount_high", "currency")
                if any(k in w for w in warnings)]
    _record("out_c_cold_warnings", [(w["kind"], w["title"], w["seen"]) for w in warnings])

    # P-C1: record, then branch
    status, sbody = summary
    site = next((s for s in sbody.get("sites") or () if s["site_code"] == "COLD-LAB-001"), None) if status == 200 \
        else None
    site_cost = next((r for r in (site or {}).get("rows") or () if r["category"] == "OPTIMIZE_COST"), None)
    site_warnings = [w for w in sbody.get("warnings") or () if w["site_code"] == "COLD-LAB-001"] \
        if status == 200 else []
    passed = (site_cost is not None and site_cost["state"] == "NEEDS_ATTENTION"
              and [w["kind"] for w in site_warnings].count(REPEATED) == 1)
    _record("P-C1", {"status": status, "day": _z(day), "cost": site_cost, "warnings": [
        (w["kind"], w["title"]) for w in site_warnings], "passed": passed,
        "categories": sbody.get("categories") if status == 200 else sbody})
    if passed:
        counts = {x["category"]: x["warning_count"] for x in sbody["categories"]}
        assert counts["OPTIMIZE_COST"] >= 1
        assert money_hits(sbody["warnings"]) == []
