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
    assert all(v["measured_by"] is None for v in b["other"].values())
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
