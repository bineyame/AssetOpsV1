"""DD3d-a (D-DD.153, D-DD.154 as amended by D-DD.168): C-DD17's tolerance floor, C-DD2's fuel kinds and C-DD8's balance
on the fuel records, judged by `tools/dd_check.py` on hand-built rows. Each plant must flip its check."""
from __future__ import annotations

import copy
import json
import sys
from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from .conftest import REPOSITORY_ROOT

sys.path.insert(0, str(REPOSITORY_ROOT / "tools"))
import dd_check  # noqa: E402

from .test_dd2_checker_on_emulated_rows import LAKESIDE, inputs, mini_rows  # noqa: E402,F401  (fixtures)

ONBOARDING = json.loads(dd_check.ONBOARDING_FILE.read_text(encoding="utf-8"))
MONTHS = dd_check.PURE_MONTHS


def _balance(burned: str, balance: str) -> dict:
    return {"open": Decimal(1000), "delivered": Decimal(0), "close": Decimal(1000) - Decimal(burned) - Decimal(balance),
            "burned": Decimal(burned), "consumed": Decimal(burned) + Decimal(balance), "balance": Decimal(balance)}


# --- C-DD17 --------------------------------------------------------------------------------------------------------------

def test_the_checker_reads_each_tanks_declared_accuracy_from_the_file() -> None:
    assert {c: dd_check.declared_accuracy(ONBOARDING, c) for c in ("KOBO-001", "KISIWA-001", "MTO-001")} == \
        {"KOBO-001": Decimal(25), "KISIWA-001": Decimal(50), "MTO-001": Decimal(10)}
    bare = copy.deepcopy(ONBOARDING)
    for site in bare["sites"]:
        for c in site["components"]:
            c["properties"] = [p for p in c.get("properties", []) if not p["property_key"].startswith("fuel-level")]
    assert dd_check.declared_accuracy(bare, "KOBO-001") is None
    assert dd_check.declared_accuracy(ONBOARDING, "NOWHERE") is None


@pytest.mark.parametrize(("burned", "draw", "a", "band", "state", "within"), [
    ("0", "12", 25, "50", "INSIDE_TOLERANCE", True),        # Kobo July: 12 of 12 L is under the gauge's 50
    ("514.2", "120", 25, "50", "RAISED", False),            # Kobo October
    ("689", "18", 50, "100", "INSIDE_TOLERANCE", True),     # Kisiwa September: 2.5 %, inside 100
    ("9000", "120", 25, "182.4", "INSIDE_TOLERANCE", True),  # the relative term binds
    ("0", "50", 25, "50", "INSIDE_TOLERANCE", True),        # at the band is inside (the product's strict >)
    ("0", "50.1", 25, "50", "RAISED", False),
    ("32.4", "0", 10, "20", "NO_GAP", True)])
def test_c_dd17_judges_the_floor(burned, draw, a, band, state, within) -> None:
    line = dd_check.judge_unexplained_month("2026-07", _balance(burned, draw), Decimal(draw), Decimal("0.02"),
                                            Decimal(a), "within" if within else "above")
    assert line[0], line[1]
    assert f"band {Decimal(band):.2f}" in line[1] and line[1].endswith(state)
    flipped = dd_check.judge_unexplained_month("2026-07", _balance(burned, draw), Decimal(draw), Decimal("0.02"),
                                               Decimal(a), "above" if within else "within")
    assert not flipped[0] and flipped[1].startswith("FAIL")


@pytest.mark.parametrize(("balance", "draw"), [("11", "12"), ("-1", "-1"), ("12.2", "12")])
def test_c_dd17_unexplained_is_the_draw_and_never_negative(balance, draw) -> None:
    assert not dd_check.judge_unexplained_month("2026-07", _balance("0", balance), Decimal(draw), Decimal("0.02"),
                                                Decimal(25), "within")[0]


def _steps(opening: Decimal, draws: dict[str, Decimal], burns: dict[str, Decimal], deliveries: dict[str, Decimal]) -> dict:
    """A Site whose tank carries the month figures exactly: the draw, the burn and the delivery fall in each month's
    first step; its generator runs that one step."""
    level, out = opening, {}
    for month in (*MONTHS, "2026-11"):
        at = datetime.fromisoformat(f"{month}-01T00:00")
        days = (datetime.fromisoformat(dd_check.next_month(month) + "-01T00:00") - at).days
        for i in range(days * 288 if month != "2026-11" else 1):
            m = (at + timedelta(minutes=5 * i)).strftime("%Y-%m-%dT%H:%M")
            out[m] = {"gen_kw": {}, "gen_state": {}, "inv": {}, "pv_kw": Decimal(0), "load_kw": Decimal(0), "tank": level}
            if i == 0 and month != "2026-11":
                if burns[month]:
                    out[m]["gen_state"]["G"], out[m]["gen_kw"]["G"] = "RUNNING", burns[month] * 12
                level = level - draws[month] - burns[month] + deliveries[month]
    return out


KIT = {"G": (100, 1, 0)}  # 1 L/kWh, no no-load rate: the step's litres are its kWh


def _site(draws, burns, deliveries):
    steps = _steps(Decimal(1000), draws, burns, deliveries)
    records = [{"kind": "TANK_DIP", "taken_at_local": f"{m}-01T00:00", "litres": str(steps[f"{m}-01T00:00"]["tank"]),
                "source_record_id": f"d{m}"} for m in (*MONTHS, "2026-11")]
    records += [{"kind": "FUEL_DELIVERY", "taken_at_local": f"{m}-01T10:00", "litres": str(v),
                 "source_record_id": f"f{m}"} for m, v in deliveries.items() if v]
    return steps, records


def _months(*values: str) -> dict[str, Decimal]:
    return dict(zip(MONTHS, map(Decimal, values)))


WORLD = {"KOBO-001": (_months("12", "12", "11", "120"), _months("0", "0", "762", "514"), _months("0", "0", "800", "400")),
         "KISIWA-001": (_months("20", "19", "18", "20"), _months("700", "700", "680", "680"), _months("0", "800", "800", "800")),
         "MTO-001": (_months("0", "0", "0", "0"), _months("0", "0", "0", "32"), _months("0", "0", "0", "0"))}


@pytest.fixture(scope="module")
def pure() -> dict:
    sites, fuel = {}, {}
    for code, figures in WORLD.items():
        steps, records = _site(*figures)
        notes = [{"at": r["taken_at_local"] + ":00+03:00", "litres": r["litres"]} for r in records
                 if r["kind"] == "FUEL_DELIVERY"]
        sites[code], fuel[code] = {"steps": steps, "manifest": {"conditions": {"fuel_notes": notes}}}, records
    return {"sites": sites, "measured": {}, "fuel": fuel}


@pytest.fixture(autouse=True)
def _kit(monkeypatch):
    monkeypatch.setattr(dd_check, "generator_kit", lambda _onboarding, _code: KIT)


def test_c_dd17_judges_the_three_mini_grid_sites(pure) -> None:
    result = dd_check.judge_pure_c_dd17(pure, ONBOARDING)
    assert result.passed, result.detail
    states = {(line.split()[0], line.split()[1].rstrip(":")): line.rsplit(" ", 1)[1] for line in result.detail}
    assert states == {("KOBO-001", m): "RAISED" if m == "2026-10" else "INSIDE_TOLERANCE" for m in MONTHS} | \
        {("KISIWA-001", m): "INSIDE_TOLERANCE" for m in MONTHS} | {("MTO-001", m): "NO_GAP" for m in MONTHS}


def test_c_dd17_fails_without_a_declared_accuracy_or_a_site(pure) -> None:
    bare = copy.deepcopy(ONBOARDING)
    kisiwa = next(s for s in bare["sites"] if s["code"] == "KISIWA-001")
    for c in kisiwa["components"]:
        c["properties"] = [p for p in c.get("properties", []) if not p["property_key"].startswith("fuel-level")]
    result = dd_check.judge_pure_c_dd17(pure, bare)
    assert not result.passed and any(d.startswith("FAIL KISIWA-001") and "no declared level accuracy" in d for d in result.detail)
    missing = dd_check.judge_pure_c_dd17({**pure, "sites": {k: v for k, v in pure["sites"].items() if k != "MTO-001"}}, ONBOARDING)
    assert not missing.passed and "FAIL MTO-001: no readings" in missing.detail


@pytest.mark.parametrize("code", ["KOBO-001", "KISIWA-001"])
def test_c_dd17_fails_when_a_site_with_a_draw_declares_no_tolerance(pure, monkeypatch, code) -> None:
    """Review L2: never judged on the floor alone; Mto has no draw and declares none."""
    declared = dd_check.fuel_tolerances()
    assert set(declared) == {"KOBO-001", "KISIWA-001"}
    monkeypatch.setattr(dd_check, "fuel_tolerances", lambda: {c: v for c, v in declared.items() if c != code})
    result = dd_check.judge_pure_c_dd17(pure, ONBOARDING)
    assert not result.passed
    assert [d for d in result.detail if d.startswith("FAIL")] == [f"FAIL {code}: a declared draw and no tolerance_pct"]
    assert not [d for d in result.detail if d.startswith(f"{code} ")]


def test_c_dd17_fails_on_mto_unexplained_fuel(pure) -> None:
    bent = {**pure, "sites": {**pure["sites"], "MTO-001": {**pure["sites"]["MTO-001"], "steps": _steps(
        Decimal(1000), _months("0", "1", "0", "0"), WORLD["MTO-001"][1], WORLD["MTO-001"][2])}}}
    result = dd_check.judge_pure_c_dd17(bent, ONBOARDING)
    assert [d for d in result.detail if d.startswith("FAIL")] and "MTO-001 2026-08" in "".join(
        d for d in result.detail if d.startswith("FAIL"))


# --- C-DD8 on the fuel records --------------------------------------------------------------------------------------------

def _judge(pure, fuel=None, sites=None):
    fuel = pure["fuel"] if fuel is None else fuel
    return dd_check.judge_fuel_records(fuel, {c: s["steps"] for c, s in (sites or pure["sites"]).items()}, ONBOARDING)


def test_c_dd8_balance_on_the_records_is_the_declared_draw(pure) -> None:
    failing, lines = _judge(pure)
    assert failing == [] and len(lines) == 12
    assert any(line.startswith("KOBO-001 2026-10 records ") and line.endswith("declared draw 120 L") for line in lines)


def _without(fuel, code, record_id):
    return {**fuel, code: [r for r in fuel[code] if r["source_record_id"] != record_id]}


@pytest.mark.parametrize(("code", "record_id", "named"), [
    ("KOBO-001", "d2026-09", "KOBO-001 2026-08"),   # a missing closing dip
    ("KISIWA-001", "f2026-08", "KISIWA-001 2026-08"),  # a missing delivery
    ("MTO-001", "d2026-07", "MTO-001 2026-07")])
def test_c_dd8_fails_naming_the_month_of_a_missing_record(pure, code, record_id, named) -> None:
    failing, _ = _judge(pure, _without(pure["fuel"], code, record_id))
    assert any(line.startswith(named) for line in failing)


def test_c_dd8_fails_on_a_dip_off_by_a_litre_a_site_without_records_and_a_gap_in_the_readings(pure) -> None:
    bent = copy.deepcopy(pure["fuel"])
    bent["MTO-001"][1]["litres"] = str(Decimal(bent["MTO-001"][1]["litres"]) + 1)
    assert len(_judge(pure, bent)[0]) == 2  # its two months
    assert any("KISIWA-001: no fuel records" in f for f in _judge(pure, {k: v for k, v in pure["fuel"].items() if k != "KISIWA-001"})[0])
    gap = {m: s for m, s in pure["sites"]["MTO-001"]["steps"].items() if m != "2026-08-10T00:00"}
    sites = {**pure["sites"], "MTO-001": {**pure["sites"]["MTO-001"], "steps": gap}}
    assert any(f.startswith("MTO-001 2026-08") and "8927 of 8928 steps" in f for f in _judge(pure, sites=sites)[0])
    doubled = {**pure["fuel"], "MTO-001": pure["fuel"]["MTO-001"] + [pure["fuel"]["MTO-001"][0]]}
    assert any(f.startswith("MTO-001 2026-07") and "2 dips" in f for f in _judge(pure, doubled)[0])


def test_pure_c_dd8_fails_when_the_run_holds_no_fuel_records(pure) -> None:
    result = dd_check.judge_pure_c_dd8({**pure, "fuel": {}}, ONBOARDING)
    assert not result.passed
    assert sum("no fuel records" in d for d in result.detail) == 3
    held = dd_check.judge_pure_c_dd8(pure, ONBOARDING)
    assert not any("fuel records" in d for d in held.detail) and any(" records " in d for d in held.detail)


def test_read_pure_reads_the_fuel_records(tmp_path) -> None:
    (tmp_path / "t").mkdir()
    (tmp_path / "t" / "X.manifest.json").write_text(json.dumps({"site_code": "X"}))
    (tmp_path / "t" / "fuel-records.json").write_text(json.dumps(
        {"schema": "assetops.world-fuel-records/1", "tenant": "t", "sites": [{"site_code": "X", "records": [{"kind": "TANK_DIP"}]}]}))
    assert dd_check.read_pure(tmp_path)["fuel"] == {"X": [{"kind": "TANK_DIP"}]}
    (tmp_path / "t" / "fuel-records.json").write_text(json.dumps({"schema": "other/1", "sites": []}))
    with pytest.raises(dd_check.InputError):
        dd_check.read_pure(tmp_path)


NIGHTS = {"KOBO-001": [("2026-07-01", "WITHIN_MARGIN", None), ("2026-07-02", "BELOW_MATERIALITY", None),
                       ("2026-07-03", "NOT_ASSESSED", "MISSING_OPENING")],
          "KISIWA-001": [("2026-07-01", "WITHIN_MARGIN", None)], "MTO-001": [("2026-07-01", "WITHIN_MARGIN", None)]}


def test_c_dd8_prints_every_assessed_night_by_state_and_fails_naming_a_raised_one() -> None:
    failing, lines = dd_check.judge_fuel_nights(NIGHTS)
    assert failing == []
    assert "KOBO-001 nights WITHIN_MARGIN 1: 2026-07-01" in lines
    assert "KOBO-001 nights BELOW_MATERIALITY 1: 2026-07-02" in lines
    assert "KOBO-001 nights NOT_ASSESSED 1 (MISSING_OPENING 1)" in lines
    for state in ("UNEXPLAINED", "EXCESS"):
        failing, _ = dd_check.judge_fuel_nights({**NIGHTS, "MTO-001": [("2026-08-04", state, None)]})
        assert failing == [f"MTO-001 night 2026-08-04 {state}"]
    failing, _ = dd_check.judge_fuel_nights({**NIGHTS, "MTO-001": [("2026-08-04", "NOT_ASSESSED", "MISSING_OPENING")]})
    assert failing == ["MTO-001: no assessed night"]
    assert "MTO-001: no assessed night" in dd_check.judge_fuel_nights({})[0]


def test_c_dd8_on_the_store_names_the_readings_dd5_1_loads(pure) -> None:
    result = dd_check.judge_store_c_dd8(pure["fuel"], {}, NIGHTS, ONBOARDING)
    assert not result.passed
    assert any("no readings stored: the loader is DD5.1's" in d for d in result.detail)
    held = dd_check.judge_store_c_dd8(pure["fuel"], {c: s["steps"] for c, s in pure["sites"].items()}, NIGHTS, ONBOARDING)
    assert held.passed, held.detail
    assert held.pending


# --- C-DD2: the fuel kinds -------------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def stored(mini_rows) -> list[dict]:  # noqa: F811
    """Stored fuel records as `stored_fuel_records` returns them: the dips, and one delivery per fuel EXPENSE row."""
    out = [{"tenant": "lakeside-power", "site": code, "kind": "TANK_DIP", "taken_at_local": f"{m}-01T00:00",
            "litres": Decimal(1000)} for code in WORLD for m in MONTHS]
    out += [{"tenant": "lakeside-power", "site": r["site"], "kind": "FUEL_DELIVERY", "litres": r["quantity"],
             "taken_at_local": f"{r['month']}-16T10:00"} for r in mini_rows
            if r["kind"] == "EXPENSE" and r["body"].get("category") == "FUEL"]
    return out


def test_c_dd2_holds_the_fuel_kinds_against_the_books(inputs, mini_rows, stored) -> None:  # noqa: F811
    bought = {(r["site"], r["taken_at_local"][:7]) for r in stored if r["kind"] == "FUEL_DELIVERY"}
    assert ("KOBO-001", "2026-07") not in bought and not any(site == "MTO-001" for site, _ in bought)  # months of none
    result = dd_check.judge_kinds(inputs, mini_rows, LAKESIDE, stored)
    assert result.passed and result.pending == [], result.detail


def test_c_dd2_prints_the_fuel_kinds_pending_without_the_stored_records(inputs, mini_rows) -> None:  # noqa: F811
    result = dd_check.judge_kinds(inputs, mini_rows, LAKESIDE)
    assert result.passed and result.pending == ["FUEL_DELIVERY and TANK_DIP: no stored records given"]


def _drop(rows, kind, site, month):
    return [r for r in rows if (r["kind"], r["site"], r["taken_at_local"][:7]) != (kind, site, month)]


def test_c_dd2_fails_on_a_missing_dip_a_missing_delivery_and_one_the_books_did_not_buy(inputs, mini_rows, stored) -> None:  # noqa: F811
    dip = dd_check.judge_kinds(inputs, mini_rows, LAKESIDE, _drop(stored, "TANK_DIP", "MTO-001", "2026-08"))
    assert dip.detail == ["lakeside-power/MTO-001 2026-08: no TANK_DIP record"]
    gone = dd_check.judge_kinds(inputs, mini_rows, LAKESIDE, _drop(stored, "FUEL_DELIVERY", "KOBO-001", "2026-10"))
    assert gone.detail == ["lakeside-power/KOBO-001 2026-10: FUEL_DELIVERY 0 L != fuel expense rows 400 L"]
    extra = stored + [{"tenant": "lakeside-power", "site": "KOBO-001", "kind": "FUEL_DELIVERY", "litres": Decimal(400),
                       "taken_at_local": "2026-07-05T10:00"}]
    bent = dd_check.judge_kinds(inputs, mini_rows, LAKESIDE, extra)
    assert bent.detail == ["lakeside-power/KOBO-001 2026-07: FUEL_DELIVERY 400 L != fuel expense rows 0 L"]
    assert not dd_check.judge_kinds(inputs, mini_rows, LAKESIDE, []).passed


def test_c_dd8_is_live_and_c_dd17_waits_for_its_served_clause() -> None:
    assert "C-DD8" in dd_check.LIVE and "C-DD8" not in dd_check.STUBS
    assert dd_check.STUBS["C-DD17"] == "DD6.1"
