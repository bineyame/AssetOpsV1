"""DD3b2 checks (D-DD.146, D-DD.132, C-DD21's v9 row): the checker judges the writer's Kisiwa and Mto rows.

C-DD6's Kisiwa clause reads GEN-KS-01's state row, Mto's reads INV-MT-02's power (D-DD.146). `dd_check --pure DIR`
judges C-DD8, C-DD17's pure part and C-DD20's Kisiwa and Mto clauses from the pure run's files (D-DD.132). Every
clause is shown failing on a planted row."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

from assetops_simulator.world import telemetry as tel

from .conftest import REPOSITORY_ROOT, load_fixture
from .test_dd3b2_units import _f, _run, _site, _values


def _dd_check():
    spec = importlib.util.spec_from_file_location("dd_check", REPOSITORY_ROOT / "tools/dd_check.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["dd_check"] = module  # its dataclasses resolve their module
    spec.loader.exec_module(module)
    return module


dd_check = _dd_check()


@pytest.fixture(scope="module")
def books() -> dict:
    history = json.loads((REPOSITORY_ROOT / "Docs/demo-sprint/product-direction-layer4/history.json").read_text())
    return tel.books_for(load_fixture(), history, {"lakeside-power": ""})


@pytest.fixture(scope="module")
def kisiwa(books) -> list[dict]:
    return _run(books, "KISIWA-001", "2026-10-30", "2026-10-30")[0]


@pytest.fixture(scope="module")
def mto(books) -> list[dict]:
    return _run(books, "MTO-001", "2026-10-28", "2026-10-28")[0]


def _mini_failures(result) -> list[str]:
    return [d for d in result.detail if d.startswith(("KISIWA-001", "MTO-001")) and "FAIL" in d]


# --- C-DD6 (D-DD.146): Kisiwa's state clause and Mto's power clause, live --------------------------------------------

def test_c_dd6_kisiwa_and_mto_clauses_live_on_the_writer_rows(books, kisiwa, mto) -> None:
    result = dd_check.judge_failures_at_instant({"KISIWA-001": kisiwa, "MTO-001": mto})
    assert not _mini_failures(result), result.detail
    assert result.pending == []  # the EV clauses are live too (DD4.4, merged from main)
    assert [c["evidence"] for c in dd_check.FAILURES_LIVE] == ["event", "event", "event", "state", "power"]
    assert any("11:02 is the O&M record's" in d for d in result.detail)
    # information (D-DD.146): the August outage fails at 19:20 and restores to STOPPED at 11:00
    august = _run(books, "KISIWA-001", "2026-08-14", "2026-08-17")[0]
    state = {r["start"][:16]: r["value"] for r in august if (r["source_id"], r["signal_id"]) ==
             ("gen-ks-01-controller", "status")}
    assert state["2026-08-14T19:20"] == "FAILED" and state["2026-08-17T11:00"] == "STOPPED"


def test_c_dd6_kisiwa_fails_when_the_failed_state_starts_late_or_on_another_unit(kisiwa) -> None:
    late = [dict(r, value="RUNNING") if r["source_id"] == "gen-ks-01-controller" and r["signal_id"] == "status"
            and r["start"][11:16] == "18:40" else r for r in kisiwa]
    assert _mini_failures(dd_check.judge_failures_at_instant({"KISIWA-001": late}))
    shared = [dict(r, value="FAILED") if r["source_id"] == "gen-ks-02-controller" and r["signal_id"] == "status"
              and r["start"][11:16] == "18:40" else r for r in kisiwa]
    assert _mini_failures(dd_check.judge_failures_at_instant({"KISIWA-001": shared}))
    assert _mini_failures(dd_check.judge_failures_at_instant({}))  # no Kisiwa rows


def _mto_power(rows, source, minute, value):
    return [dict(r, value=value) if (r["source_id"], r["signal_id"], r["start"][11:16]) == (source, "ac-power", minute)
            else r for r in rows]


def test_c_dd6_mto_fails_when_inv_mt_02_returns_or_was_already_off(mto) -> None:
    for planted in (_mto_power(mto, "inv-mt-02-controller", "16:00", "1.000"),   # power returns before span end
                    _mto_power(mto, "inv-mt-02-controller", "10:55", "0.000"),   # already off the step before
                    _mto_power(mto, "inv-mt-01-controller", "11:00", "0.000")):  # the healthy inverter is off too
        assert _mini_failures(dd_check.judge_failures_at_instant({"MTO-001": planted}))
    dark = [dict(r, value="0.000") if r["signal_id"] == "irradiance" and r["start"][11:16] == "11:00" else r for r in mto]
    assert _mini_failures(dd_check.judge_failures_at_instant({"MTO-001": dark}))


# --- --pure (D-DD.132): C-DD8, C-DD17 pure, C-DD20 Kisiwa and Mto without a database ---------------------------------

@pytest.fixture(scope="module")
def onboarding() -> dict:
    return json.loads((REPOSITORY_ROOT / "backend/tests/fixtures/on1/lakeside-power.onboarding.json").read_text())


def test_pure_tank_bound_holds_on_the_writer_rows_and_fails_on_an_overfill(kisiwa, onboarding) -> None:
    sites = {"KISIWA-001": dd_check.pure_steps(kisiwa)}
    assert not dd_check.tank_outside_bounds(sites, onboarding)
    over = [dict(r, value="5000.5") if r["signal_id"] == "fuel-level" and r["start"][11:16] == "03:00" else r
            for r in kisiwa]
    assert dd_check.tank_outside_bounds({"KISIWA-001": dd_check.pure_steps(over)}, onboarding)


def test_pure_kisiwa_candidate_minutes_count_generator_running_while_pv_carries_the_load(kisiwa) -> None:
    # the counter, not the world: the world's own count is C-DD8's to judge on the pure run (reported, never tuned)
    base = dd_check.candidate_minutes(dd_check.pure_steps(kisiwa))["2026-10"]
    noon = [dict(r, value="20.000") if r["source_id"] == "gen-ks-02-controller" and r["signal_id"] == "ac-power"
            and r["start"][11:16] == "10:20" else r for r in kisiwa]  # PV charging the battery
    assert dd_check.candidate_minutes(dd_check.pure_steps(noon)) == {"2026-10": base + 5}
    night = [dict(r, value="20.000") if r["source_id"] == "gen-ks-02-controller" and r["signal_id"] == "ac-power"
             and r["start"][11:16] == "21:00" else r for r in kisiwa]  # PV carries nothing at night: necessary
    assert dd_check.candidate_minutes(dd_check.pure_steps(night)) == {"2026-10": base}


def test_pure_mto_generator_litres_per_day_rise_after_the_trip_or_fail() -> None:
    kit = {"gen": (25, "0.30", "2.4")}  # rated kW, SFC L/kWh, no-load L/h

    def steps(before_kw, after_kw):
        from datetime import datetime, timedelta
        out, at = {}, datetime(2026, 9, 29)
        while at < datetime(2026, 11, 1):
            minute = at.strftime("%Y-%m-%dT%H:%M")
            kw = before_kw if minute < "2026-10-28T11:00" else after_kw
            out[minute] = {"gen_kw": {"gen": kw}, "gen_state": {"gen": "RUNNING" if kw else "STOPPED"}}
            at += timedelta(hours=1)
        return out
    assert dd_check.litres_per_day_rise(steps(5, 10), kit, "2026-10-28T11:00", step_minutes=60)[0]
    assert not dd_check.litres_per_day_rise(steps(10, 5), kit, "2026-10-28T11:00", step_minutes=60)[0]
    assert not dd_check.litres_per_day_rise({}, kit, "2026-10-28T11:00", step_minutes=60)[0]  # nothing before: fails


def test_pure_is_judged_without_a_database_url(books, tmp_path: Path, capsys) -> None:
    result = tel.build_telemetry(load_fixture(), _f(), books, start="2026-10-30", end="2026-10-30",
                                 only=("KISIWA-001",))
    for name, data in result.files:
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / name).write_bytes(data)
    for name, manifest in result.manifests:
        (tmp_path / name).write_text(json.dumps(manifest), encoding="utf-8")
    code = dd_check.main(["--pure", str(tmp_path)])
    out = capsys.readouterr().out
    assert code in (0, 1) and "DD_CHECK_USAGE" not in out
    assert [line.split()[0] for line in out.splitlines() if line.startswith("C-DD")] == ["C-DD8", "C-DD17", "C-DD20"]


# --- C-DD21's v9 row on Kisiwa ----------------------------------------------------------------------------------------

def test_c_dd21_v9_rows_on_kisiwa_hold_and_fail_on_a_planted_gap(books) -> None:
    frozen = tel.frozen_inputs(_site("KISIWA-001"), books["KISIWA-001"], "2026-10-30", "2026-10-30")
    values = {a: (v.value, v.canonical_unit, v.dimension) for a, v in _values(frozen).items()}
    units = {"GENERATOR": ("gen-ks-01", "gen-ks-02"), "INVERTER": ("pv-inverter",)}
    needs = [(n.state_key, n.component_type, n.unit, n.dimension, n.per_unit) for n in tel.NEEDS
             if n.version == 9 or n.per_unit]
    assert dd_check.judge_v9_rows(values, units, needs) == []
    gap = {a: v for a, v in values.items() if a != "generator-no-load-fuel-rate@gen-ks-02"}
    assert dd_check.judge_v9_rows(gap, units, needs)
    half = dict(values, **{"pv-array-share@pv-inverter": (values["pv-array-share@pv-inverter"][0] / 2, "1", "FRACTION")})
    assert dd_check.judge_v9_rows(half, units, needs)


# --- dd3_pure_run.py --site (DD3.3): Kisiwa and Mto on v9 from their committed kit -----------------------------------

def test_the_pure_run_tool_runs_kisiwa_on_v9(tmp_path: Path, capsys) -> None:
    spec = importlib.util.spec_from_file_location("dd3_pure_run", REPOSITORY_ROOT / "tools/dd3_pure_run.py")
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    (tmp_path / "lakeside-power.expenses.csv").write_text("", encoding="utf-8")
    assert tool.main(["--books", str(tmp_path), "--site", "KISIWA-001", "--start", "2026-10-30",
                      "--end", "2026-10-30"]) == 0
    out = capsys.readouterr().out
    assert "KISIWA-001 2026-10-30..2026-10-30; pack v9; tank capacity 5000 L" in out
    assert "2026-10" in out and "bound hit: no" in out
