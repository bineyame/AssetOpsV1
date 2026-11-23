"""DD2.5 (spec `specs/DD-demo-data/spec.md` §8.1; D-DD.55): C-DD2 to C-DD4 on rows, no database.

The checker's own evaluator is tested against hand figures (Kobo's July: 8190 kWh, 3276.00, 3012.62). The judges' tests on the
emulator's rows are `simulator/tests/world/test_dd2_checker_on_emulated_rows.py` (a product test may not import the
simulator).
"""
from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import dd_check  # noqa: E402

LAKESIDE = {"lakeside-power"}


@pytest.fixture(scope="module")
def inputs() -> dd_check.Inputs:
    return dd_check.read_inputs("postgresql+psycopg://u:p@dd.invalid:1/x_test")


# --- the evaluator, against hand figures ---------------------------------------------------------------------------------

def formulas_for(inputs, tenant: str, site: str, month: str) -> dd_check.Formulas:
    money = set(inputs.history["meta"]["money_leaves"])
    record = dd_check.history_record(inputs.history["tenants"][tenant][site][month]["actual"], money)
    t = next(x for x in inputs.manifest["tenants"] if x["tenant"] == tenant)
    key = {"MINI_GRID": "MINI_GRID", "COLD_CHAIN": "COLD_CHAIN"}[t["vertical"]]
    return dd_check.Formulas(inputs.manifest["structures"][key], inputs.manifest["factor_map"][key], record,
                             t["prices"], site)


def test_the_evaluator_gives_kobos_july_by_hand(inputs) -> None:
    f = formulas_for(inputs, "lakeside-power", "Kobo", "2026-07")
    # D-DD.164 (2026-11-23): Lakeside July-September re-seeded once (RUN_WRITTEN left the scope digest)
    assert f.node("billed_kwh") == Decimal(8184)      # 8615 - 388 - 0 - 43 - 0
    assert f.node("revenue") == Decimal("3273.60")   # 8184 x 0.40
    assert f.node("collected") == Decimal("3010.41")   # 3273.60 - 0 - 263.19
    assert f.node("diesel_l") == Decimal(509)          # 476 + 21 + 12
    assert f.node("fuel_cost") == Decimal("636.25")   # 513 x 1.25


def test_the_evaluator_gives_cold_revenue_and_received_by_hand(inputs) -> None:
    record = inputs.history["tenants"]["harvest-cold"]["Room A · Mwea"]["2026-07"]["actual"]
    f = formulas_for(inputs, "harvest-cold", "Room A · Mwea", "2026-07")
    assert f.node("revenue") == Decimal(record["crate_days"]) * Decimal("0.2")
    assert f.node("received") == f.node("revenue") - Decimal(record["outstanding"]) / 100


def test_the_evaluator_reads_alternatives_and_refuses_what_it_cannot_read(inputs) -> None:
    structure = {"a": "x - y", "b": "record.q | record.r | 0", "c": "(1 + 2) * 3"}
    f = dd_check.Formulas(structure, {"x": "record.p | 5", "y": "record.z | 0"}, {"p": 10, "r": 4}, {}, "S")
    assert (f.node("a"), f.node("b"), f.node("c")) == (Decimal(10), Decimal(4), Decimal(9))
    with pytest.raises(dd_check.FormulaError):
        dd_check.Formulas({"a": "min(1, 2)"}, {}, {}, {}, "S").node("a")


def test_the_three_checks_are_live_and_fail_on_an_empty_store(inputs) -> None:
    assert {"C-DD2", "C-DD3", "C-DD4"} <= set(dd_check.LIVE)
    assert not dd_check.judge_kinds(inputs, []).passed


def test_the_checker_still_imports_nothing_from_the_simulator() -> None:
    import ast
    tree = ast.parse((ROOT / "tools" / "dd_check.py").read_text(encoding="utf-8"))
    inside = {id(n) for f in ast.walk(tree) if isinstance(f, ast.FunctionDef) and f.name == "check_property_table_parity"
              for n in ast.walk(f)}  # C-DD21's one function imports the writer's table (DD3.1)
    names = {n.module if isinstance(n, ast.ImportFrom) else a.name
             for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom)) and id(n) not in inside
             for a in (n.names if isinstance(n, ast.Import) else [n])}
    assert not [x for x in names if x and ("simulator" in x or "world" in x)]


# --- D-DD.58: C-DD3 and C-DD4 never crash; the EV clause judges quantity x band price ------------------------------------

def _ev_site(inputs):
    t = next(x for x in inputs.manifest["tenants"] if x["vertical"] == "EV_DEPOT")
    site = next(s for s in t["sites"] if s["site"] == "Embakasi")
    return t["tenant"], site["code"], site["tariff"]["prices"]


def _ev_line(tenant, code, band, line_type, quantity, amount, month="2026-10"):
    return {"tenant": tenant, "site": code, "kind": "CHARGE", "month": month, "provenance": "source-emulated",
            "amount": Decimal(amount), "quantity": Decimal(quantity), "status": None,
            "body": {"line_type": line_type, "band": band}}


def test_c_dd3_and_c_dd4_on_the_real_inputs_with_no_tenant_filter_raise_nothing(inputs) -> None:
    for judge in (dd_check.judge_identities, dd_check.judge_leaves_and_nodes):
        result = judge(inputs, [], None)
        assert result.check in ("C-DD3", "C-DD4")


def test_a_dropped_cold_crate_days_is_a_fail_line_not_an_exception(inputs) -> None:
    import copy
    planted = dd_check.Inputs(manifest=inputs.manifest, history=copy.deepcopy(inputs.history), database_url=inputs.database_url)
    cold = next(t for t in planted.manifest["tenants"] if t["vertical"] == "COLD_CHAIN")
    site = cold["sites"][0]
    del planted.history["tenants"][cold["tenant"]][site["site"]]["2026-07"]["actual"]["crate_days"]
    result = dd_check.judge_identities(planted, [], {cold["tenant"]})
    assert not result.passed
    assert f"{cold['tenant']}/{site['code']} 2026-07: crate_days not recorded" in result.detail


def test_the_ev_clause_is_pending_while_no_ev_charge_row_is_stored(inputs) -> None:
    result = dd_check.judge_identities(inputs, [], {"metro-bus"})
    assert result.pending == ["EV utility invoices are DD4.4's"]
    assert not any("energy" in line for line in result.detail)


def test_the_ev_clause_judges_each_line_as_quantity_times_band_price_half_even(inputs) -> None:
    tenant, code, prices = _ev_site(inputs)
    good = [_ev_line(tenant, code, "PEAK", "USAGE", "47740", "11457.60"),
            _ev_line(tenant, code, "OFFPEAK", "USAGE", "39060", "4687.20"),
            _ev_line(tenant, code, "DEMAND", "DEMAND", "500", "6000.00")]
    result = dd_check.judge_identities(inputs, good, {tenant})
    assert not result.pending and not [l for l in result.detail if "2026-10" in l and code in l and "!=" in l]
    bad = [dict(good[0], amount=Decimal("11457.61"))] + good[1:]
    result = dd_check.judge_identities(inputs, bad, {tenant})
    assert not result.passed and any(f"{tenant}/{code} 2026-10 PEAK" in l for l in result.detail)
    half = _ev_line(tenant, code, "PEAK", "USAGE", "0.0625", "0.02")  # 0.0625 x 0.24 = 0.015 -> half-even 0.02
    assert not [l for l in dd_check.judge_identities(inputs, [half], {tenant}).detail if "PEAK" in l]
    half = _ev_line(tenant, code, "PEAK", "USAGE", "0.0625", "0.01")
    assert [l for l in dd_check.judge_identities(inputs, [half], {tenant}).detail if "PEAK" in l]


def test_an_ev_line_without_a_price_in_m_is_a_fail_line(inputs) -> None:
    tenant, code, _ = _ev_site(inputs)
    result = dd_check.judge_identities(inputs, [_ev_line(tenant, code, "FLAT", "USAGE", "10", "1.50")], {tenant})
    assert not result.passed and any("usd_per_kwh not recorded" in l for l in result.detail)


def test_book_months_is_gone() -> None:
    assert not hasattr(dd_check, "BOOK_MONTHS")


# --- DD3d.4 (D-DD.180): C-DD4's fuel clause on hand rows ----------------------------------------------------------------
KOBO, KISIWA, MTO = "KOBO-001", "KISIWA-001", "MTO-001"
NO_PRICE = "no invoice and no declared price"


def _fuel(code: str, kind: str, at: str, litres: str) -> dict:
    return {"tenant": "lakeside-power", "site": code, "kind": kind, "taken_at_local": at, "litres": Decimal(litres)}


def _dip(code: str, month: str, litres: str) -> dict:
    return _fuel(code, "TANK_DIP", f"{month}-01T00:00", litres)


def _bought(code: str, quantity: str, amount: str, month: str = "2026-10") -> dict:
    return {"tenant": "lakeside-power", "site": code, "kind": "EXPENSE", "month": month, "provenance": "source-emulated",
            "amount": Decimal(amount), "quantity": Decimal(quantity), "status": None, "body": {"category": "FUEL"}}


def october_fuel() -> dict:
    """Hand records that burn M's litres: Kobo 634.224, Kisiwa 902.600 (both round to M's whole litres), Mto 32.500 (half-even
    32). A delivery at November's first instant and one the minute before October are other months'."""
    return {"fuel": [
        _dip(KOBO, "2026-10", "400.000"), _fuel(KOBO, "FUEL_DELIVERY", "2026-10-01T00:00", "150"),
        _fuel(KOBO, "FUEL_DELIVERY", "2026-10-19T10:30", "250"), _dip(KOBO, "2026-11", "165.776"),
        _fuel(KOBO, "FUEL_DELIVERY", "2026-11-01T00:00", "90"), _fuel(KOBO, "FUEL_DELIVERY", "2026-09-30T23:59", "70"),
        _dip(KISIWA, "2026-10", "710"), _fuel(KISIWA, "FUEL_DELIVERY", "2026-10-12T09:00", "800"),
        _dip(KISIWA, "2026-11", "607.4"), _fuel(KISIWA, "TANK_DIP", "2026-10-15T00:00", "5"),
        _dip(MTO, "2026-10", "100"), _dip(MTO, "2026-11", "67.500")],
        "rows": [_bought(KOBO, "150", "187.50"), _bought(KOBO, "250", "312.50"), _bought(KISIWA, "800", "1040.00")],
        "prices": {("lakeside-power", MTO): Decimal("1.25")}}


def fuel_lines(inputs, given: dict) -> list[str]:
    return dd_check.judge_october_fuel(inputs, given["rows"], given["fuel"], given["prices"], LAKESIDE)


def test_c_dd4_october_fuel_passes_at_all_three_sites(inputs) -> None:
    assert fuel_lines(inputs, october_fuel()) == []
    assert not [x for x in dd_check.judge_leaves_and_nodes(inputs, october_fuel()["rows"], LAKESIDE, october_fuel()["fuel"],
                                                           october_fuel()["prices"]).detail
                if "diesel_l" in x or "fuel_cost" in x or NO_PRICE in x or "dips at" in x]


def test_c_dd4_one_delivery_litre_moved_fails_diesel_l(inputs) -> None:
    given = october_fuel()
    given["fuel"][2]["litres"] += 1
    (line,) = [x for x in fuel_lines(inputs, given) if "diesel_l" in x]
    assert line == "lakeside-power/KOBO-001 2026-10: diesel_l 635 (635.224 L) != recorded 634"
    given = october_fuel()  # the same litre moved across the month's end
    given["fuel"][2]["taken_at_local"] = "2026-11-01T00:00"
    assert "lakeside-power/KOBO-001 2026-10: diesel_l 384 (384.224 L) != recorded 634" in fuel_lines(inputs, given)
    given = october_fuel()  # 33.5 is half-even 34, not 33: no tolerance but the rounding
    given["fuel"][-1]["litres"] = Decimal("66.5")
    assert "lakeside-power/MTO-001 2026-10: diesel_l 34 (33.5 L) != recorded 32" in fuel_lines(inputs, given)


def test_c_dd4_a_wrong_invoice_amount_fails_fuel_cost(inputs) -> None:
    given = october_fuel()
    given["rows"][1]["amount"] += Decimal("0.01")
    assert fuel_lines(inputs, given) == ["lakeside-power/KOBO-001 2026-10: fuel_cost 792.52 (634 L x 500.01 / 400) != recorded 792.5"]
    given = october_fuel()
    given["rows"][2]["quantity"] = Decimal(0)  # invoices that state no litres give no price
    assert fuel_lines(inputs, given) == ["lakeside-power/KISIWA-001 2026-10: fuel invoices with no litres or no amount, no price"]
    given["rows"][2].update(quantity=None, amount=None)
    assert fuel_lines(inputs, given) == ["lakeside-power/KISIWA-001 2026-10: fuel invoices with no litres or no amount, no price"]


def test_c_dd4_mto_is_judged_on_the_declared_price(inputs) -> None:
    given = {**october_fuel(), "prices": {("lakeside-power", MTO): Decimal("1.26")}}
    assert fuel_lines(inputs, given) == ["lakeside-power/MTO-001 2026-10: fuel_cost 40.32 (32 L x 1.26) != recorded 40.0"]
    # without it, and with another tenant's or Site's only
    for prices in ({}, {("harvest-cold", MTO): Decimal("1.25"), ("lakeside-power", KOBO): Decimal("1.25")}):
        assert fuel_lines(inputs, {**given, "prices": prices}) == [f"lakeside-power/MTO-001 2026-10: {NO_PRICE}"]
    # an invoice governs where there is one: a declared price beside it is not read
    both = {**october_fuel(), "prices": {("lakeside-power", c): Decimal("1.25") for c in (KOBO, KISIWA, MTO)}}
    assert fuel_lines(inputs, both) == []
    # September's invoices and another tenant's are not October's
    given = october_fuel()
    given["rows"] += [_bought(MTO, "10", "99.00", month="2026-09"), {**_bought(MTO, "10", "99.00"), "tenant": "harvest-cold"}]
    assert fuel_lines(inputs, given) == []


def test_c_dd4_fails_on_missing_records_and_is_never_pending(inputs) -> None:
    given = october_fuel()
    assert fuel_lines(inputs, {**given, "fuel": []}) == [
        f"lakeside-power/{code} 2026-10: 0 dips at 2026-{m}-01T00:00, not one" for code in (KOBO, KISIWA, MTO)
        for m in ("10", "11")]
    given["fuel"].append(_dip(KOBO, "2026-11", "1"))
    assert fuel_lines(inputs, given) == ["lakeside-power/KOBO-001 2026-10: 2 dips at 2026-11-01T00:00, not one"]
    result = dd_check.judge_leaves_and_nodes(inputs, [], None, [], {})
    assert not result.passed and result.pending == [] and len(result.detail) == 40
    assert result.detail[:9] == [f"lakeside-power/{code} 2026-10: {what}" for code in (KOBO, KISIWA, MTO) for what in (
        "0 dips at 2026-10-01T00:00, not one", "0 dips at 2026-11-01T00:00, not one", NO_PRICE)]  # before the 40-line cut
    # only a caller that gives no records at all (the pure tests on books) reads pending
    assert dd_check.judge_leaves_and_nodes(inputs, [], LAKESIDE).pending == ["mini-grid fuel_cost: no stored records given"]
    assert dd_check.judge_leaves_and_nodes(inputs, [], {"harvest-cold"}).pending == []


def test_c_dd4_the_manifests_figures_judge_never_price(inputs) -> None:
    """The price is never M's: with M's own price and cost both moved, the stored records still say 1.25."""
    import copy
    planted = dd_check.Inputs(manifest=copy.deepcopy(inputs.manifest), history=inputs.history, database_url=inputs.database_url)
    lake = next(t for t in planted.manifest["tenants"] if t["tenant"] == "lakeside-power")
    lake["prices"]["diesel_usd_per_l"] = {name: 2.5 for name in lake["prices"]["diesel_usd_per_l"]}
    assert fuel_lines(planted, october_fuel()) == []
    mto = next(s for s in lake["sites"] if s["code"] == MTO)["period"]["actual"]
    mto["diesel_cost"] = 80.0
    assert fuel_lines(planted, october_fuel()) == ["lakeside-power/MTO-001 2026-10: fuel_cost 40.00 (32 L x 1.25) != recorded 80.0"]
    del mto["diesel_cost"], mto["diesel_l"]
    assert fuel_lines(planted, october_fuel()) == ["lakeside-power/MTO-001 2026-10: diesel_l not recorded",
                                                   "lakeside-power/MTO-001 2026-10: diesel_cost not recorded"]


def test_c_dd4_history_months_fuel_is_not_judged_and_says_so(inputs) -> None:
    given = october_fuel()
    given["fuel"] += [_dip(KOBO, m, "9999") for m in ("2026-07", "2026-08", "2026-09")]
    given["rows"] += [_bought(KOBO, "1", "77.00", month=m) for m in ("2026-07", "2026-08", "2026-09")]
    assert fuel_lines(inputs, given) == []
    result = dd_check.judge_leaves_and_nodes(inputs, given["rows"], LAKESIDE, given["fuel"], given["prices"])
    assert not [x for x in result.detail if "diesel_l" in x or "fuel_cost" in x]
    assert result.info == ["mini-grid July to September litres and fuel cost: not judged here; C-DD8 judges every month's "
                           "fuel records (D-DD.180)"]
    assert dd_check.judge_leaves_and_nodes(inputs, [], {"harvest-cold"}).info == []


def test_c_dd4_the_live_check_reads_the_stored_records(inputs, monkeypatch) -> None:
    given, read = october_fuel(), []
    monkeypatch.setattr(dd_check, "stored_books", lambda url: read.append(("books", url)) or given["rows"])
    monkeypatch.setattr(dd_check, "stored_fuel_records", lambda url: read.append(("fuel", url)) or given["fuel"])
    monkeypatch.setattr(dd_check, "stored_diesel_prices", lambda url, month: read.append((month, url)) or {})
    result = dd_check.LIVE["C-DD4"](inputs)
    assert read == [(x, inputs.database_url) for x in ("books", "fuel", "2026-10")]
    assert result.detail[0] == f"lakeside-power/MTO-001 2026-10: {NO_PRICE}"
