"""FX-COLD-LINKED (build sheet OWN-GAPS, DS-1f ruling D-E5.8) on real Postgres: a clean Cold assessment after the
start failure must not drop the repeat-visit notice.

BUILDs the w502 `positive` dataset (start failure on D at 16:00, its open Finding, three linked visits) in
`assetops_out_c_fxcold_test`, then replays one clean `cold-normal` run later that day (18:00, the demo add-day path,
`tools/demo_combined_cold.py` `run_day`). The estate summary over `[D, D+1)` reads Cold on the latest contained
selected window, the clean one, whose selection holds no Finding. The repeat warning must still fire and cite the
start-failure Finding, so the Maintenance "Repeat visits" card does not say "None found"."""
from __future__ import annotations

import json
from datetime import timedelta

from test_out_b4_board_postgres import _board, _case_db, _child, _client, _record, _serve
from test_out_c3_repeat_visits_postgres import _day, _spy_selected_windows, _summary, _z

REPEATED = "REPEATED_MAINTENANCE_NO_RESULT"
SITE = "COLD-LAB-001"

#: the demo add-day replay of one clean Cold run (`demo_combined_cold.run_day`, wall-clock worker)
CLEAN = r'''
import json, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
sys.path.insert(0, sys.argv[4])
import demo_combined_cold as dcc
import demo_story_days as sd
url, start, out = sys.argv[1], datetime.fromisoformat(sys.argv[2]), Path(sys.argv[3])
day = sd.DayRun(site="cold", day=start.date().isoformat(), offset=0, kind="normal", start=start,
                end=start + timedelta(minutes=60), received_at=datetime.now(timezone.utc), assess="build",
                scenario={"scenario_id": "cold-normal", "scenario_version": "1"}, epoch="fx-cold-linked-clean")
result = dcc.run_day(url, out, day)
result["findings"] = dcc.findings_on(url, day.day)
(out / "clean.json").write_text(json.dumps(result, default=str), encoding="utf-8")
'''


def test_clean_assessment_after_the_failure_keeps_the_repeat_notice(monkeypatch, tmp_path) -> None:
    import w502_cold_work_walkthrough as w502
    from test_out_b4_board_postgres import ROOT

    out = tmp_path / "positive"
    out.mkdir()
    clean_out = tmp_path / "clean"
    clean_out.mkdir()
    with _case_db("fxcold", "c") as url:
        _child(url, ["-c", w502.BUILD, "positive", str(out)])
        doc = json.loads((out / "positive.json").read_text(encoding="utf-8"))
        assert doc["blocked"] is None, doc["blocked"]
        lo, hi = doc["w501"]["window"]
        day = _day(lo)
        clean_start = day + timedelta(hours=18)
        _child(url, ["-c", CLEAN, url, clean_start.isoformat(), str(clean_out), str(ROOT / "tools")])
        clean = json.loads((clean_out / "clean.json").read_text(encoding="utf-8"))
        _record("fx_cold_clean_run", clean)
        _serve(monkeypatch, url, tmp_path)
        windows = _spy_selected_windows(monkeypatch)
        with _client() as c:
            status, summary, _ = _summary(c, day, day + timedelta(days=1))
            board, _ = _board(c, SITE, "fx_cold_day_board", **{"from": _z(day), "to": _z(day + timedelta(days=1))})
            later, _ = _board(c, SITE, "fx_cold_clean_board",
                              **{"from": _z(clean_start), "to": _z(clean_start + timedelta(minutes=65))})

    # the clean run is a later selected window with no Finding of its own, and the summary reads Cold on it
    assert clean.get("run_id"), clean
    assert len({w["windows"][-1] for w in windows if w["site_code"] == SITE and w["windows"]}) == 1, windows
    cold_windows = next(w["windows"] for w in windows if w["site_code"] == SITE and w["windows"])
    assert len(cold_windows) == 2 and cold_windows[-1][0] == _z(clean_start), cold_windows

    assert status == 200, summary
    repeats = [w for w in summary["warnings"] if w["site_code"] == SITE and w["kind"] == REPEATED]
    _record("fx_cold_summary_warnings", [(w["kind"], w["title"], w["seen"]) for w in summary["warnings"]])
    assert len(repeats) == 1 and repeats[0]["count"] == 3, summary["warnings"]
    assert repeats[0]["fault_name"] == "automatic start failure", repeats[0]
    assert repeats[0]["seen"].endswith("; the automatic start failure is still open"), repeats[0]["seen"]
    assert any(r["kind"] == "FINDING" for r in repeats[0]["evidence_refs"]), repeats[0]["evidence_refs"]
    site = next(x for x in summary["sites"] if x["site_code"] == SITE)
    cost = next(r for r in site["rows"] if r["category"] == "OPTIMIZE_COST")
    assert cost["state"] == "NEEDS_ATTENTION" and cost["lead_outcome"]["key"] == "CC-3", cost
    # the Site board over the same day, and over the clean window alone, say the same
    for body in (board, later):
        assert [w["kind"] for w in body["warnings"]].count(REPEATED) == 1, body["warnings"]
