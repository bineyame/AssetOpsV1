"""CH-5b1 R5 (CH5b1-R Q4/Q5): the budget guard's own tests. Run: python -m pytest tools/checks/test_perf_budget.py"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

CHECKS = Path(__file__).resolve().parent
sys.path.insert(0, str(CHECKS))
sys.path.insert(0, str(CHECKS.parent))

import chain_perf_probe  # noqa: E402
import perf_budget  # noqa: E402


def test_budgets_equal_the_probe_and_design() -> None:
    b = perf_budget.load_budgets()
    fam = {k: (v["cold_ms"], v["warm_p95_ms"], v["max_bytes"]) for k, v in b["families"].items()}
    assert fam == chain_perf_probe.BUDGETS
    assert {k: v["limit"] for k, v in b["other"].items()} == {
        "why_trace_ms": 50, "tick_chain_stage_fraction": 0.5, "snapshot_rebuild_ms_per_measure_day": 50}
    assert {k: v["measured_by"] is None for k, v in b["other"].items()} == {
        "why_trace_ms": False, "tick_chain_stage_fraction": True, "snapshot_rebuild_ms_per_measure_day": True}
    assert b["other"]["why_trace_ms"]["owner"] == "CH-5b2"


def test_every_probe_and_chain_route_is_declared() -> None:
    routes = perf_budget.load_budgets()["routes"]
    assert set(routes) == set(chain_perf_probe.URLS) | set(perf_budget.CHAIN_URLS)
    for key in chain_perf_probe.URLS:  # the probe's own family rule
        want = chain_perf_probe.budget(key)
        got = routes[key]
        assert (None if got is None else chain_perf_probe.BUDGETS[got]) == want


def test_fixture_self_test_passes() -> None:
    assert perf_budget.run_fixtures(perf_budget.load_budgets()) == 0


def test_fixture_self_test_fails_on_a_wrong_expectation(tmp_path: Path) -> None:
    for f in perf_budget.FIXTURES.glob("*.json"):
        shutil.copy(f, tmp_path / f.name)
    fx = json.loads((tmp_path / "breach-cold.json").read_text(encoding="utf-8"))
    fx["record"]["routes"]["kobo_board_31oct"]["cold_ms"] = [700, 711, 720]  # the breach is gone
    (tmp_path / "breach-cold.json").write_text(json.dumps(fx), encoding="utf-8")
    assert perf_budget.run_fixtures(perf_budget.load_budgets(), tmp_path) == 1


def test_no_fixtures_is_a_failure(tmp_path: Path) -> None:
    assert perf_budget.run_fixtures(perf_budget.load_budgets(), tmp_path) == 1


def test_not_measured_is_never_a_pass() -> None:
    fx = json.loads((perf_budget.FIXTURES / "pass.json").read_text(encoding="utf-8"))
    rec = fx["record"]
    rec["other"].pop("why_trace_ms")
    rows = perf_budget.evaluate(perf_budget.load_budgets(), rec)
    assert ("why_trace_ms", "owner CH-5b2", None, 50, "NOT_MEASURED") in rows
    assert perf_budget.failed(rows)


def test_p95_is_nearest_rank() -> None:
    assert perf_budget.p95([1, 2, 3]) == 3
    assert perf_budget.p95(list(range(1, 21))) == 19


def test_a_budget_passes_once_it_is_measured() -> None:
    """L1: the `measured_by: null` budgets are not permanent failures; a recorded value within the limit passes."""
    fx = json.loads((perf_budget.FIXTURES / "pass.json").read_text(encoding="utf-8"))
    budgets = perf_budget.load_budgets()
    rows = perf_budget.evaluate(budgets, fx["record"])
    others = [r for r in rows if r[0] in budgets["other"]]
    assert others and all(r[4] == "PASS" for r in others)
    assert not perf_budget.failed(rows)


def _stub_measure(monkeypatch, fixture: str) -> None:
    rec = json.loads((perf_budget.FIXTURES / fixture).read_text(encoding="utf-8"))["record"]
    monkeypatch.setattr(perf_budget, "measure", lambda *a, **k: rec)


def test_report_mode_exits_zero_on_a_breach(monkeypatch, tmp_path: Path) -> None:
    _stub_measure(monkeypatch, "breach-cold.json")
    argv = ["--database-url", "x", "--work", str(tmp_path)]
    assert perf_budget.main(argv + ["--report"]) == 0


def test_a_breach_exits_one_without_report(monkeypatch, tmp_path: Path) -> None:
    _stub_measure(monkeypatch, "breach-cold.json")
    assert perf_budget.main(["--database-url", "x", "--work", str(tmp_path)]) == 1


# --- DD-1b2b O4 (DD1b2-R Q9, Q10): `--story` -----------------------------------------------------------------------

_STORY = {"S": "2026-11-05T00:00:00Z"}
_DAYS = [
    {"site": "kobo", "kind": "normal", "start": "2026-11-05T00:00:00Z", "end": "2026-11-06T00:00:00Z"},
    {"site": "cold", "kind": "failure", "start": "2026-11-05T16:00:00Z", "end": "2026-11-05T17:05:00Z"},
    {"site": "ev", "kind": "fault", "start": "2026-11-05T08:00:00Z", "end": "2026-11-05T09:00:00Z"},
]


def _story_files(tmp_path: Path, days=_DAYS) -> Path:
    (tmp_path / "story.json").write_text(json.dumps(_STORY), encoding="utf-8")
    (tmp_path / "days.json").write_text(json.dumps({"days": days}), encoding="utf-8")
    return tmp_path / "story.json"


def test_story_urls_keep_every_route_key_and_move_to_the_story_days(tmp_path: Path) -> None:
    urls = perf_budget.all_urls(_story_files(tmp_path))
    assert set(urls) == set(perf_budget.all_urls())  # same keys: the budgets still match every route
    assert urls["kobo_board_31oct"].endswith("date=2026-11-05")
    assert "from=2026-11-05T16:00:00Z&to=2026-11-05T17:05:00Z" in urls["cold_board_failure_night"]
    assert "from=2026-11-05T08:00:00Z&to=2026-11-05T09:00:00Z" in urls["ev_chain_27oct"]
    assert "from=2026-10-30T00:00:00Z&to=2026-11-06T00:00:00Z" in urls["portfolio_week"]  # S-6 .. S+1
    assert not any("2026-10-31" in u or "2026-10-27" in u for u in urls.values())  # non-vacuous: all moved


def test_without_story_the_fixed_dates_are_unchanged() -> None:
    urls = perf_budget.all_urls()
    assert urls["kobo_chain_31oct"] == "/api/sites/KOBO-001/chain?date=2026-10-31"
    assert perf_budget.WEEK in urls["summary_week"]


def test_a_story_without_the_cold_failure_run_is_refused_not_defaulted(tmp_path: Path) -> None:
    import pytest

    story = _story_files(tmp_path, [d for d in _DAYS if d["kind"] != "failure"])
    with pytest.raises(StopIteration):
        perf_budget.all_urls(story)


def test_main_passes_story_to_measure(monkeypatch, tmp_path: Path) -> None:
    seen: dict = {}
    rec = json.loads((perf_budget.FIXTURES / "breach-cold.json").read_text(encoding="utf-8"))["record"]
    monkeypatch.setattr(perf_budget, "measure", lambda *a, **k: seen.update(args=a) or rec)
    story = _story_files(tmp_path)
    perf_budget.main(["--database-url", "x", "--work", str(tmp_path), "--story", str(story), "--report"])
    assert seen["args"][-1] == story


# --- ANY-1 AR-0: arbitrary-range cases --------------------------------------------------------------------------


def test_any_range_budgets_are_the_architect_numbers() -> None:
    b = perf_budget.load_budgets(perf_budget.ANY_RANGE_BUDGETS_PATH)
    assert b["store"] == "off"
    assert b["families"] == {"board_any_day": {"cold_ms": 2000}, "portfolio_any_range": {"cold_ms": 2000}}


def test_any_range_fixtures_as_expected_and_not_vacuous(tmp_path: Path) -> None:
    budgets = perf_budget.load_budgets(perf_budget.ANY_RANGE_BUDGETS_PATH)
    assert perf_budget.run_any_range_fixtures(budgets) == 0
    assert perf_budget.run_any_range_fixtures(budgets, tmp_path) == 1  # no fixtures: a failure
    fx = json.loads((perf_budget.ANY_RANGE_FIXTURES / "breach-cold.json").read_text(encoding="utf-8"))
    fx["expect"] = {"breaches": [], "not_measured": [], "verdict": "PASS"}
    (tmp_path / "wrong.json").write_text(json.dumps(fx), encoding="utf-8")
    assert perf_budget.run_any_range_fixtures(budgets, tmp_path) == 1
    assert perf_budget.main(["--fixture"]) == 0


def test_any_range_cases_cover_both_families_and_a_month(tmp_path: Path) -> None:
    cases = perf_budget.any_range_cases(3, 12, _story_files(tmp_path))
    assert {c.family for c in cases} == {"board_any_day", "portfolio_any_range"}
    import period_read_parity

    assert any(period_read_parity.portfolio_days(c.path) == 31 for c in cases if c.family == "portfolio_any_range")


def test_any_range_refuses_the_store_on_and_measures_cold_store_off(monkeypatch, tmp_path: Path) -> None:
    import pytest

    with pytest.raises(SystemExit):
        perf_budget.main(["--database-url", "x", "--work", str(tmp_path), "--any-range", "--store", "on"])
    seen: dict = {}
    rec = json.loads((perf_budget.ANY_RANGE_FIXTURES / "breach-cold.json").read_text(encoding="utf-8"))["record"]
    monkeypatch.setattr(perf_budget, "measure_any_range", lambda *a, **k: seen.update(args=a) or rec)
    assert perf_budget.main(["--database-url", "x", "--work", str(tmp_path), "--any-range", "--store", "off"]) == 1
    assert perf_budget.main(["--database-url", "x", "--work", str(tmp_path), "--any-range", "--store", "off",
                             "--report"]) == 0
    assert len(seen["args"][-1]) == 16
