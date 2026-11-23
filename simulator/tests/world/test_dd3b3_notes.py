"""DD3b3 (D-DD.92, D-DD.130, D-DD.131, D-DD.147-149): fuel purchases follow the tank by the reorder rule.

The reorder rule (`tools/dd3_pure_run.py --restate-notes`) places 400 L notes at the next 10:00 after the level first
falls below 25 % of the tank, as many as fit in the free space, at most two; a disorder test's dated note keeps its
date. `config/world/fuel-notes.json` holds the notes; `exports.py` writes the expense ledger from it (the books carry
purchases, never consumption). `--leaves` prints `M`'s fuel leaves from the notes run. `dd_check --pure` reads the
unexplained tolerance from `M` and judges Kisiwa by D-DD.148."""

from __future__ import annotations

import importlib.util
import json
from datetime import datetime, timedelta
from decimal import Decimal
from fractions import Fraction
from zoneinfo import ZoneInfo

import pytest

from assetops_simulator.world import exports
from assetops_simulator.world.exports import build_exports
from assetops_simulator.world.history import generate_history

from .conftest import REPOSITORY_ROOT, load_fixture
from .test_dd3b2_checks import dd_check

NAIROBI = ZoneInfo("Africa/Nairobi")
NOTES_FILE = REPOSITORY_ROOT / "config/world/fuel-notes.json"
ONBOARDING = REPOSITORY_ROOT / "backend/tests/fixtures/on1/lakeside-power.onboarding.json"


def _tool():
    spec = importlib.util.spec_from_file_location("dd3_pure_run_dd3b3", REPOSITORY_ROOT / "tools/dd3_pure_run.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


tool = _tool()


def at(text: str) -> datetime:
    return datetime.fromisoformat(text).replace(tzinfo=NAIROBI)


# --- the reorder rule (D-DD.92) ---------------------------------------------------------------------------------------

def test_a_note_is_placed_at_the_next_10_00_the_same_day_only_before_10_00() -> None:
    assert tool.note_instant(at("2026-08-03T09:55")) == at("2026-08-03T10:00")
    assert tool.note_instant(at("2026-08-03T10:00")) == at("2026-08-04T10:00")
    assert tool.note_instant(at("2026-08-03T23:55")) == at("2026-08-04T10:00")


def test_as_many_400_l_notes_as_fit_in_the_free_space_at_most_two() -> None:
    assert [tool.note_count(Fraction(f)) for f in (1200, 800, 799, 400, 399)] == [2, 2, 1, 1, 0]


def test_the_first_crossing_is_a_step_from_at_or_above_25_percent_to_below() -> None:
    levels = [(at("2026-08-01T00:00") + timedelta(minutes=5 * k), Fraction(v))
              for k, v in enumerate((1300, 1250, 1249, 1200, 1300, 1240))]
    assert tool.first_crossing(levels, Fraction(1250), None) == at("2026-08-01T00:10")
    assert tool.first_crossing(levels, Fraction(1250), at("2026-08-01T00:10")) == at("2026-08-01T00:25")
    assert tool.first_crossing(levels, Fraction(1250), at("2026-08-01T00:25")) is None


def _linear_tank(capacity: int, start_l: int, burn_per_step: Fraction, first: datetime, steps: int):
    """A fake run: the tank burns a fixed amount every 5 minutes and takes each note at its instant."""
    def simulate(notes):
        level = Fraction(start_l)
        added = {}
        for note in notes:
            added[datetime.fromisoformat(note["at"])] = added.get(datetime.fromisoformat(note["at"]), 0) + int(note["litres"])
        for k in range(steps + 1):
            instant = first + timedelta(minutes=5 * k)
            yield instant, level
            level += added.get(instant, 0)
            assert level <= capacity, f"overfill at {instant}"
            level -= burn_per_step
    return simulate


def test_restating_iterates_until_no_crossing_and_never_overfills() -> None:
    first = at("2026-07-01T00:00")
    steps = 31 * 288
    simulate = _linear_tank(1000, 500, Fraction(1, 4), first, steps)  # 72 L a day on a 1000 L tank
    dated = [{"at": "2026-07-01T10:00:00+03:00", "litres": "400", "basis": "STORY:OOO-1"}]  # kept at its date
    notes = tool.restate(simulate, Fraction(1000), dated)
    reorder = [n for n in notes if n["basis"] == "REORDER"]
    assert reorder and all(n["litres"] == "400" for n in notes)
    assert all(n["at"][11:16] == "10:00" for n in notes)
    assert dated[0] in notes
    assert [n["at"] for n in notes] == sorted(n["at"] for n in notes)
    levels = list(simulate(notes))  # the fake asserts no overfill
    assert tool.first_crossing(levels, Fraction(250), datetime.fromisoformat(reorder[-1]["at"])) is None


# --- the committed notes file (D-DD.92) and the books (D-DD.130) -------------------------------------------------------

def test_the_notes_file_lists_the_three_mini_grid_sites_with_their_tanks() -> None:
    document = json.loads(NOTES_FILE.read_text(encoding="utf-8"))
    assert document["schema"] == "assetops.world-fuel-notes/1"
    tanks = {s["code"]: str(c["rating"]["value"]) for s in json.loads(ONBOARDING.read_text())["sites"]
             for c in s["components"] if c["type"] == "FUEL_TANK"}
    sites = {s["site_code"]: s for s in document["sites"]}
    assert sorted(sites) == ["KISIWA-001", "KOBO-001", "MTO-001"]
    for code, site in sites.items():
        assert site["rule"] == "D-DD.92" and site["tank_l"] == tanks[code]
        assert all(n["litres"] == "400" and n["basis"] in ("REORDER", "STORY:OOO-1") for n in site["notes"])
    assert {"at": "2026-10-26T10:00:00+03:00", "litres": "400", "basis": "STORY:OOO-1"} in sites["KOBO-001"]["notes"]
    assert not [n for n in sites["MTO-001"]["notes"] if n["at"] < "2026-11"]  # D-DD.147: Mto buys no fuel Jul-Oct


def _fuel(result, code: str) -> list[tuple[str, str, str]]:
    rows = next(f for f in result.files if f.key == "expenses").records
    return [(r["clocks"]["occurred_at"], r["quantity"]["value"], r["amount"]["value"]) for r in rows
            if r["site_code"] == code and r["body"]["category"] == "FUEL"]


def test_the_expense_ledger_follows_the_notes_file_and_not_consumption() -> None:
    view = load_fixture()
    history = generate_history(view)
    notes = {"schema": "assetops.world-fuel-notes/1", "sites": [
        {"site_code": "KISIWA-001", "rule": "D-DD.92", "tank_l": "5000",
         "notes": [{"at": "2026-07-27T10:00:00+03:00", "litres": "400", "basis": "REORDER"},
                   {"at": "2026-07-27T10:00:00+03:00", "litres": "400", "basis": "REORDER"}]}]}
    result = build_exports(view, history, months=["2026-07", "2026-10"], fuel_notes=notes)
    assert _fuel(result, "KISIWA-001") == [("2026-07-27T10:00:00+03:00", "400", "520.00")] * 2
    assert _fuel(result, "KOBO-001")  # a Site not in the file keeps the cycle


def test_exports_read_the_committed_notes_file_by_default() -> None:
    view = load_fixture()
    result = build_exports(view, generate_history(view), months=["2026-07", "2026-08", "2026-09", "2026-10"])
    document = json.loads(NOTES_FILE.read_text(encoding="utf-8"))
    for site in document["sites"]:
        wanted = [(n["at"], n["litres"]) for n in site["notes"] if n["at"] < "2026-11"]
        assert [(a, q) for a, q, _ in _fuel(result, site["site_code"])] == wanted


def test_c_dd4_no_longer_judges_mini_grid_litres_or_fuel_cost() -> None:
    assert "diesel_l" not in dd_check._RECORDED_NODE["MINI_GRID"]
    assert "fuel_cost" not in dd_check._RECORDED_NODE["MINI_GRID"]


# --- D-DD.131: the leaves from the notes run --------------------------------------------------------------------------

def test_the_leaves_follow_their_stated_rules() -> None:
    ledger = {"tank_open": Fraction(2000), "tank_close": Fraction(1500), "modelled_l": Fraction(88356, 100),
              "standin_candidate_l": Fraction(6693, 100)}
    notes = [{"at": "2026-10-04T10:00:00+03:00", "litres": "400", "basis": "REORDER"}]
    plan = {"diesel_l": 2300, "diesel_cost": 2990.00, "revenue": 4125.00, "om": 700.00, "staff": 500.00,
            "contribution": -65.00}
    actual = {"revenue": 4070.00, "om": 700.00, "staff": 500.00, "unexplained_l": 20}
    leaves = tool.october_leaves(ledger, notes, Decimal("1.3"), plan, actual)
    assert leaves["diesel_l"] == 904  # 883.56 + 20 to whole litres
    assert leaves["candidate_l"] == 67 and leaves["necessary_l"] == 904 - 67 - 20
    assert leaves["diesel_cost"] == Decimal("1175.20")
    assert leaves["contribution"] == Decimal("4070.00") - Decimal("1175.20") - 700 - 500
    assert leaves["variance"] == leaves["contribution"] - Decimal("-65.00")
    assert leaves["fuel_balance"] == {"opening_dip_l": 2000, "deliveries_l": 400, "closing_dip_l": 1500,
                                      "consumed_l": 900, "model_implied_l": 884, "residual_l": 16}
    assert leaves["bridge"]["CANDIDATE_RUNNING"] == Decimal("-87.10")
    assert leaves["bridge"]["NECESSARY"] == -(Decimal(817) - 2300) * Decimal("1.3")
    assert leaves["bridge"]["UNEXPLAINED_RESIDUAL"] == Decimal("-26.00")


# --- D-DD.149: `--pure` reads the tolerance from `M`; Kisiwa by D-DD.148 -----------------------------------------------

def test_the_unexplained_tolerance_is_read_from_the_manifest() -> None:
    assert dd_check.fuel_tolerances() == {"KOBO-001": Decimal("0.02"), "KISIWA-001": Decimal("0.02")}


def _steps(spec: dict[str, tuple]) -> dict[str, dict]:
    """minute -> (gen-ks-01 kW, state, gen-ks-02 kW, state, pv kW, load kW)"""
    out = {}
    for minute, (k1, s1, k2, s2, pv, load) in spec.items():
        out[minute] = {"gen_kw": {"gen-ks-01": Decimal(k1), "gen-ks-02": Decimal(k2)},
                       "gen_state": {"gen-ks-01": s1, "gen-ks-02": s2}, "inv": {}, "pv_kw": Decimal(pv),
                       "load_kw": Decimal(load)}
    return out


def test_kisiwa_candidate_time_is_printed_per_month_with_no_bound() -> None:
    """D-DD.151: the share is printed, not bounded; only a month without computed minutes fails."""
    running = {f"2026-{mm}-{d:02d}T{h:02d}:{m:02d}": (20, "RUNNING", 0, "STOPPED", 0, 20)
               for mm in ("07", "08", "09", "10") for d in range(1, 21) for h in range(18, 23) for m in range(0, 60, 5)}
    sunny = {f"2026-08-22T10:{m:02d}": (20, "RUNNING", 0, "STOPPED", 30, 20) for m in range(0, 60, 5)}  # 60 min
    ok, line = dd_check.judge_candidate_share(_steps(running | sunny))
    assert ok, line
    assert "2026-08: 60 of 6060 min (0.99 %)" in line and "2026-07: 0 of 6000 min (0.00 %)" in line
    many = {f"2026-08-23T{h:02d}:{m:02d}": (20, "RUNNING", 0, "STOPPED", 30, 20) for h in (10, 11, 12)
            for m in range(0, 60, 5)}
    ok, line = dd_check.judge_candidate_share(_steps(running | sunny | many))
    assert ok and "2026-08: 240 of 6240 min (3.85 %)" in line and "FAIL" not in line
    no_october = {m: v for m, v in running.items() if not m.startswith("2026-10")}
    ok, line = dd_check.judge_candidate_share(_steps(no_october))
    assert not ok and "FAIL 2026-10: no generator minutes computed" in line


def test_c_dd20_kisiwa_holds_on_the_writer_rows_and_fails_on_a_planted_row(kisiwa) -> None:
    steps = dd_check.pure_steps(kisiwa)
    measured = {"2026-10": {"unserved_kwh": {"clinic": "0", "households": "0"}}}
    ok, line = dd_check.judge_kisiwa_failure(steps, measured)
    assert ok, line
    late = {m: dict(s, gen_kw=dict(s["gen_kw"], **{"gen-ks-01": Decimal(5)})) if m == "2026-10-30T20:00" else s
            for m, s in steps.items()}
    assert not dd_check.judge_kisiwa_failure(late, measured)[0]
    restored = {m: dict(s, gen_state=dict(s["gen_state"], **{"gen-ks-01": "STOPPED"})) if m == "2026-10-30T22:00" else s
                for m, s in steps.items()}
    assert not dd_check.judge_kisiwa_failure(restored, measured)[0]
    dark = {"2026-10": {"unserved_kwh": {"clinic": "0", "households": "0.5"}}}
    assert not dd_check.judge_kisiwa_failure(steps, dark)[0]


@pytest.fixture(scope="module")
def kisiwa():
    from .test_dd3b2_checks import _run, books as _books  # noqa: F401
    from assetops_simulator.world import telemetry as tel
    history = json.loads((REPOSITORY_ROOT / "Docs/demo-sprint/product-direction-layer4/history.json").read_text())
    books = tel.books_for(load_fixture(), history, {"lakeside-power": ""})
    return _run(books, "KISIWA-001", "2026-10-30", "2026-10-30")[0]


# --- D-DD.150: every mini-grid bridge carries the same three fuel lines -----------------------------------------------

MINI = {"KOBO-001": "Kobo", "KISIWA-001": "Kisiwa", "MTO-001": "Mto"}
FUEL_LEAVES = REPOSITORY_ROOT / "config/world/fuel-leaves.json"


def _manifest() -> dict:
    import yaml
    return yaml.safe_load(dd_check.MANIFEST.read_text(encoding="utf-8"))


def _site(code: str) -> tuple[dict, dict]:
    doc = _manifest()
    for tenant in doc["tenants"]:
        for site in tenant.get("sites", []):
            if site.get("code") == code:
                return tenant, site
    raise AssertionError(code)


def test_the_restated_bridge_adds_a_missing_fuel_line_before_the_necessary_line() -> None:
    lines = [{"driver": "DEMAND_VOLUME", "amount": -55.00}, {"driver": "SOLAR_SHORTFALL_NECESSARY_GEN", "amount": -104.00},
             {"driver": "UNEXPLAINED_RESIDUAL", "amount": -26.00}]
    leaves = {"bridge": {"CANDIDATE_RUNNING": Decimal("-87.10"), "NECESSARY": Decimal("1927.90"),
                         "UNEXPLAINED_RESIDUAL": Decimal("-26.00")}}
    out = tool.restated_bridge(lines, leaves)
    assert [d for d, _, _ in out] == ["DEMAND_VOLUME", "CANDIDATE_RUNNING", "SOLAR_SHORTFALL_NECESSARY_GEN",
                                      "UNEXPLAINED_RESIDUAL"]
    assert out[1] == ("CANDIDATE_RUNNING", None, Decimal("-87.10"))
    assert sum(new for _, _, new in out) == Decimal("1759.80")
    mto = tool.restated_bridge([{"driver": "EVENING_NECESSARY_GEN", "amount": -25.00}],
                               {"bridge": {"CANDIDATE_RUNNING": Decimal("-40.00"), "NECESSARY": Decimal("375.00"),
                                           "UNEXPLAINED_RESIDUAL": Decimal("0.00")}})
    assert [d for d, _, _ in mto] == ["CANDIDATE_RUNNING", "EVENING_NECESSARY_GEN", "UNEXPLAINED_RESIDUAL"]


@pytest.mark.parametrize("code", sorted(MINI))
def test_every_mini_grid_bridge_in_m_has_the_three_fuel_lines_and_closes(code: str) -> None:
    _, site = _site(code)
    period = site["period"]
    fuel = [line for line in period["bridge"] if line["overlap_group"].endswith("-2026-10-FUEL")]
    drivers = [line["driver"] for line in fuel]
    assert len(drivers) == 3 and drivers[0] == "CANDIDATE_RUNNING" and drivers[2] == "UNEXPLAINED_RESIDUAL"
    assert drivers[1] in tool.NECESSARY_DRIVERS
    total = sum((Decimal(str(line["amount"])) for line in period["bridge"]), Decimal(0))
    assert total == Decimal(str(period["variance"]))
    assert MINI[code] in fuel[0]["basis"]


@pytest.mark.parametrize("code", sorted(MINI))
def test_the_fuel_leaves_record_was_run_on_the_live_world(code: str) -> None:
    """DD3b review H1 (D-DD.164): the record is only a record of the run if the run's inputs are today's. The
    notes run's inputs (the Site's `/2` kit, the books from the live history, the notes file's notes) are hashed
    when `--leaves --write` records the ledger; a world that moved under the record fails here, without a rerun."""
    record = next(s for s in json.loads(FUEL_LEAVES.read_text(encoding="utf-8"))["sites"] if s["site_code"] == code)
    notes = next(s for s in json.loads(NOTES_FILE.read_text(encoding="utf-8"))["sites"] if s["site_code"] == code)
    first, last = record["span"]
    assert record["inputs_sha256"] == tool.run_inputs_sha256(code, notes["notes"], first, last)


@pytest.mark.parametrize("code", sorted(MINI))
def test_m_october_fuel_leaves_equal_the_tool_output(code: str) -> None:
    """D-DD.131 (D-DD.93): `M`'s October fuel leaves are the tool's output on the notes run's October ledger."""
    record = next(s for s in json.loads(FUEL_LEAVES.read_text(encoding="utf-8"))["sites"] if s["site_code"] == code)
    notes = next(s for s in json.loads(NOTES_FILE.read_text(encoding="utf-8"))["sites"] if s["site_code"] == code)
    tenant, site = _site(code)
    price = Decimal(str(tenant["prices"]["diesel_usd_per_l"][site["site"]]))
    period = site["period"]
    leaves = tool.october_leaves(tool.ledger_from_record(record), notes["notes"], price, period["plan"],
                                 period["actual"])
    for leaf in ("diesel_l", "necessary_l", "candidate_l", "unexplained_l"):
        assert period["actual"][leaf] == leaves[leaf], leaf
    for leaf in ("diesel_cost", "contribution"):
        assert Decimal(str(period["actual"][leaf])).quantize(Decimal("0.01")) == leaves[leaf], leaf
    assert Decimal(str(period["variance"])).quantize(Decimal("0.01")) == leaves["variance"]
    balance = {k: v for k, v in period["fuel_balance"].items() if k != "tolerance_pct"}
    assert balance == leaves["fuel_balance"]
    by_driver = {("NECESSARY" if line["driver"] in tool.NECESSARY_DRIVERS else line["driver"]): line["amount"]
                 for line in period["bridge"]}
    for key, amount in leaves["bridge"].items():
        assert Decimal(str(by_driver[key])).quantize(Decimal("0.01")) == amount, key
    candidate = next(f for f in site["findings_expected"] if f.get("mechanism") == "GENERATOR_SUPPORT_CANDIDATE")
    assert candidate["days"] == f"{record['candidate_days']} of 31"
    assert candidate["gross_exposure_l"] == [0, leaves["candidate_l"]]
    assert [Decimal(str(v)).quantize(Decimal("0.01")) for v in candidate["gross_exposure_usd"]] == \
        [Decimal("0.00"), -leaves["bridge"]["CANDIDATE_RUNNING"]]


def test_kisiwa_evening_load_and_or_mg_2_read_from_the_run() -> None:
    """D-DD.151: GEN-KS-02's evening load prints from the readings; OR-MG-2 prints the share, no negative control."""
    record = next(s for s in json.loads(FUEL_LEAVES.read_text(encoding="utf-8"))["sites"]
                  if s["site_code"] == "KISIWA-001")
    share = round(Fraction(record["peak_evening_generator_kw"]) / 60 * 100)
    _, site = _site("KISIWA-001")
    assert share == 70
    assert f"{share}% load" in site["decision"]["thread"] and "95%" not in site["decision"]["thread"]
    standby = next(line for line in dd_check.MANIFEST.read_text(encoding="utf-8").splitlines()
                   if "standby_kw:" in line and "GEN-KS-02" in line)  # the record is the line's YAML comment
    assert f"({share}%" in standby and "95%" not in standby
    assert "negative control" not in site["role_in_story"]
    expect = next(o["expect"] for o in _manifest()["oracle"] if o["id"] == "OR-MG-2")
    assert expect == "Kisiwa: candidate time printed per month; no fuel-saving option is in M"


# --- D-DD.152: C-DD17 judges the tolerance only in months the generator burned -----------------------------------------

def _balance(burned: str, balance: str) -> dict:
    return {"open": Decimal(1000), "delivered": Decimal(0), "close": Decimal(1000) - Decimal(burned) - Decimal(balance),
            "burned": Decimal(burned), "consumed": Decimal(burned) + Decimal(balance), "balance": Decimal(balance)}


def test_c_dd17_month_with_no_burn_states_what_the_product_shows() -> None:
    ok, line = dd_check.judge_unexplained_month("2026-07", _balance("0", "12"), Decimal(12), Decimal("0.02"))
    assert ok, line
    assert "no burn: 12 L unexplained, which the product shows against a 12 L consumption" in line
    assert not dd_check.judge_unexplained_month("2026-07", _balance("0", "11"), Decimal(12), Decimal("0.02"))[0]


def test_c_dd17_judges_the_tolerance_where_the_generator_burned() -> None:
    tolerance = Decimal("0.02")
    assert dd_check.judge_unexplained_month("2026-09", _balance("762.2", "11"), Decimal(11), tolerance)[0]
    assert not dd_check.judge_unexplained_month("2026-09", _balance("300", "11"), Decimal(11), tolerance)[0]
    assert dd_check.judge_unexplained_month("2026-10", _balance("514.2", "120"), Decimal(120), tolerance)[0]
    assert not dd_check.judge_unexplained_month("2026-10", _balance("9000", "120"), Decimal(120), tolerance)[0]
    assert not dd_check.judge_unexplained_month("2026-09", _balance("762.2", "10"), Decimal(11), tolerance)[0]
    assert not dd_check.judge_unexplained_month("2026-09", _balance("762.2", "-1"), Decimal(-1), tolerance)[0]


def test_c_dd17_reads_the_declared_draws_from_history_and_m() -> None:
    assert dd_check.declared_draws("KOBO-001") == {"2026-07": Decimal(12), "2026-08": Decimal(12),
                                                    "2026-09": Decimal(11), "2026-10": Decimal(120)}
