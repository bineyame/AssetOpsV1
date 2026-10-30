"""OUT-C U3: GreenHarvest repeat visits on real Postgres (build sheet OUT-C §2 U3, acceptance 3 and P-C1).

BUILDs the w502 `positive` dataset (with the OUT-C authored visits and plans) in `assetops_out_c_cold_test`, reads
the board on the W5-01 window with no `known_at`, and asserts P-C1 (OUT-W, option A): the estate summary over the
day `[D, D+1)` and the week `[D-6, D+1)` judges GreenHarvest on its latest selected window, where the Cost row reads
NEEDS_ATTENTION with exactly one repeat warning and the Portfolio link opens the Site on that window."""
from __future__ import annotations

import json
import time
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
        windows = _spy_selected_windows(monkeypatch)
        lo, hi = doc["w501"]["window"]
        with _client() as c:
            body, _ = _board(c, "COLD-LAB-001", "out_c_cold_board", **{"from": lo, "to": hi})
            day = _day(lo)  # D: the w502 day (the W5-01 window lies inside it)
            summary = _summary(c, day, day + timedelta(days=1))
            week = _summary(c, day - timedelta(days=6), day + timedelta(days=1))

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
    # Rulings C final review F1/H1: the authored data names the open start-failure Finding (R572)
    assert repeats[0]["fault_name"] == "automatic start failure", repeats[0]
    assert repeats[0]["seen"].endswith("; the automatic start failure is still open"), repeats[0]["seen"]
    assert repeats[0]["badge"] == "RISK"
    assert cost["subline"] == ("None of the visits has fixed the automatic start failure yet; repair cost is not "
                               "recorded"), cost["subline"]
    effect = next(x for x in cost["contributors"] if x["key"] == "maintenance_effectiveness")
    assert effect["text"].endswith("; the automatic start failure is still open"), effect["text"]
    start_option = [o for o in protect["options"] if o["text"] == "Witnessed automatic-start test"]
    assert [o["text"] for o in cost["options"]] == ["Witnessed automatic-start test"], cost["options"]
    assert cost["options"][0]["href"] == start_option[0]["href"], (cost["options"], protect["options"])
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

    # P-C1 (OUT-W): asserted on the day and on the week ending D
    latest = {}
    for key, (status, sbody, seconds) in (("day", summary), ("week", week)):
        assert status == 200, sbody
        site = next(x for x in sbody["sites"] if x["site_code"] == "COLD-LAB-001")
        chosen = [w for w in windows if w["site_code"] == "COLD-LAB-001" and w["from"] == sbody["window"]["from"]]
        assert len(chosen) == 1, windows
        latest[key] = max(chosen[0]["windows"], key=lambda w: (w[1], w[0]))
        site_cost = next(r for r in site["rows"] if r["category"] == "OPTIMIZE_COST")
        site_warnings = [w for w in sbody["warnings"] if w["site_code"] == "COLD-LAB-001"]
        _record("P-C1", {"period": key, "status": status, "day": _z(day), "window": site["window"],
                         "window_basis": site["window_basis"], "overview_href": site["overview_href"],
                         "w501_window": [lo, hi], "selected": chosen[0]["windows"], "cost": site_cost,
                         "warnings": [(w["kind"], w["title"]) for w in site_warnings],
                         "summary_seconds": seconds, "windows_read_seconds": chosen[0]["seconds"],
                         "categories": sbody["categories"]})
        assert site["window_basis"] == "LATEST_EVENT", site
        assert (site["window"]["from"], site["window"]["to"]) == latest[key], (site["window"], latest[key])
        assert site_cost["state"] == "NEEDS_ATTENTION" and site_cost["lead_outcome"]["key"] == "CC-3", site_cost
        assert [w["kind"] for w in site_warnings].count(REPEATED) == 1, site_warnings
        counts = {x["category"]: x["warning_count"] for x in sbody["categories"]}
        assert counts["OPTIMIZE_COST"] >= 1
        assert site["overview_href"].startswith("/sites/COLD-LAB-001?from="), site["overview_href"]
        assert "known_at" not in site["overview_href"]
        assert money_hits(sbody["warnings"]) == []
        assert chosen[0]["seconds"] < 2.0, chosen[0]  # sheet §7: the windows read adds under 2 s per Site
    # the latest event in the week is still D's; record whether it is the W5-01 window itself
    assert latest["week"] == latest["day"], latest
    _record("P-C1 w501", {"latest": latest["day"], "w501": [lo, hi],
                          "is_w501": latest["day"] == (_w(lo), _w(hi))})


def _w(text: str) -> str:
    return _z(datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(timezone.utc))


def _summary(c, lo: datetime, hi: datetime) -> tuple[int, dict, float]:
    start = time.perf_counter()
    r = c.get("/api/estate/outcome-summary", params={"from": _z(lo), "to": _z(hi)})
    return r.status_code, r.json(), round(time.perf_counter() - start, 3)


def _spy_selected_windows(monkeypatch) -> list[dict]:
    """Every `site_selected_windows` call the summary makes, with its wire-text result and its own wall time."""
    from assetops_backend.estate.evidence_money import EstateEvidenceService

    seen: list[dict] = []
    real = EstateEvidenceService.site_selected_windows

    def spy(self, tenant_id, site_code, from_, to, known_at=None):
        start = time.perf_counter()
        out = real(self, tenant_id, site_code, from_, to, known_at)
        seen.append({"site_code": site_code, "from": _z(from_), "to": _z(to),
                     "windows": None if out is None else [(_z(a), _z(b)) for a, b in out],
                     "seconds": round(time.perf_counter() - start, 3)})
        return out

    monkeypatch.setattr(EstateEvidenceService, "site_selected_windows", spy)
    return seen
