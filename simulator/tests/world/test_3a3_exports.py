"""3A3 E1 to E9 (spec `specs/3A3-emulators-contract-test/spec.md` §2.5, §5 "Emulator"; D-3A3.4): the emulated
native exports for October.

Every expected figure is a literal read by hand from the fixture manifest (`fixtures/view_v1.json`, W2): Kobo
billed 8645 kWh at 0.40 (revenue 3458.00), collected 3180.00, outstanding 278.00, diesel 1180 L at 1.25 (1475.00);
Kisiwa 7400 kWh at 0.55 (4070.00), collected 3800.00, diesel 2400 L at 1.30 (3120.00), O&M ESTIMATED; Mto 5400 kWh
at 0.40 (2160.00), collected 1890.00, in transit 150.00, diesel 320 L at 1.25 (400.00).
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
from decimal import Decimal

import pytest

from assetops_contracts.native import LAYOUTS, read_layout
from assetops_simulator.world.exports import build_exports, file_name
from assetops_simulator.world.history import generate_history

from .conftest import CLI, FIXTURE, load_fixture, site_of, tenant_of

TENANT = "lakeside-power"
#: E7: the files built from `fixtures/view_v1.json`, pinned (the packet records the same values).
PINNED = {
    "lakeside-power.billing.csv": "7111a18fdf8ed36ad19c7339e1266395d70065886008b2839cbc0bacd4e16534",
    "lakeside-power.collections.csv": "8b3cd80a03eaf2fa06f8f393189ca353bbd593ad6418b90551b4a3fd1a6352c3",
    "lakeside-power.expenses.csv": "320c5442ccde0a97876b276cac63a722620f890041d3dc4413d20c3d84d2366d",
    "lakeside-power.budget.csv": "5b03eb3e849031311c40bc13accd13c278867ddbf81bb0443e0c34d1c3bfcb7e",
}


def build(view: dict | None = None):
    view = view if view is not None else load_fixture()
    return build_exports(view, generate_history(view))


@pytest.fixture(scope="module")
def result():
    return build()


def records(result, key: str) -> list[dict]:
    return list(next(f for f in result.files if f.key == key).records)


def of_site(rows: list[dict], code: str) -> list[dict]:
    return [r for r in rows if r.get("site_code") == code]


def money(rows: list[dict]) -> Decimal:
    return sum((Decimal(r["amount"]["value"]) for r in rows), Decimal("0"))


def kwh(rows: list[dict]) -> int:
    return sum(int(r["quantity"]["value"]) for r in rows)


SITES = ("KISIWA-001", "KOBO-001", "MTO-001")


def test_e1_files_and_scope(result) -> None:
    assert [file_name(f) for f in result.files] == ["lakeside-power.billing.csv", "lakeside-power.collections.csv",
                                                    "lakeside-power.expenses.csv", "lakeside-power.budget.csv"]
    assert [f.layout_id for f in result.files] == ["billing-illustrative-1", "collections-illustrative-1",
                                                   "expenses-illustrative-1", "budget-illustrative-1"]
    assert ("harvest-cold", "*", "*", "*", "*", "NOT_ON_PATH_VERTICAL") in result.unwritten
    assert ("metro-bus", "*", "*", "*", "*", "NOT_ON_PATH_VERTICAL") in result.unwritten
    assert {r[0] for r in result.unwritten} == {"harvest-cold", "metro-bus", TENANT}


def test_e2_charges(result) -> None:
    charges = records(result, "billing")
    assert [len(of_site(charges, s)) for s in SITES] == [40, 40, 40]
    assert [money(of_site(charges, s)) for s in SITES] == [Decimal("4070.00"), Decimal("3458.00"),
                                                           Decimal("2160.00")]
    assert [kwh(of_site(charges, s)) for s in SITES] == [7400, 8645, 5400]
    kobo = of_site(charges, "KOBO-001")
    assert [(r["subject"]["ref"], r["quantity"]["value"], r["amount"]["value"]) for r in kobo[:6]] == [
        ("KOBO-001-C-0001", "217", "86.80"), ("KOBO-001-C-0002", "217", "86.80"), ("KOBO-001-C-0003", "217", "86.80"),
        ("KOBO-001-C-0004", "217", "86.80"), ("KOBO-001-C-0005", "217", "86.80"), ("KOBO-001-C-0006", "216", "86.40")]
    assert kobo[0]["clocks"] == {"effective_from": "2026-10-01", "effective_to": "2026-11-01",
                                 "recognition_period": "2026-10"}


def test_e3_receipts(result) -> None:
    receipts = records(result, "collections")
    by = {s: of_site(receipts, s) for s in SITES}
    collected = [money([r for r in by[s] if r["status"] == "COLLECTED"]) for s in SITES]
    transit = [money([r for r in by[s] if r["status"] == "PAID_IN_TRANSIT"]) for s in SITES]
    assert collected == [Decimal("3800.00"), Decimal("3180.00"), Decimal("1890.00")]
    assert transit == [Decimal("0"), Decimal("0"), Decimal("150.00")]
    assert [len(by[s]) for s in SITES] == [38, 37, 38]
    last = by["KOBO-001"][-1]
    assert (last["body"]["payer_ref"], last["amount"]["value"]) == ("KOBO-001-C-0037", "67.60")
    assert by["KOBO-001"][0]["clocks"]["occurred_at"] == "2026-10-01T10:00:00+03:00"
    assert by["MTO-001"][-1]["clocks"]["occurred_at"] == "2026-10-31T19:00:00+03:00"


def test_e4_fuel(result) -> None:
    fuel = [r for r in records(result, "expenses") if r["body"]["category"] == "FUEL"]
    by = {s: of_site(fuel, s) for s in SITES}
    assert [kwh(by[s]) for s in SITES] == [2400, 1180, 320]
    assert [money(by[s]) for s in SITES] == [Decimal("3120.00"), Decimal("1475.00"), Decimal("400.00")]
    assert [len(by[s]) for s in SITES] == [6, 3, 1]
    assert [r["clocks"]["occurred_at"][8:10] for r in by["KOBO-001"]] == ["01", "11", "21"]


def test_e5_gap_1_estimated_om_is_absent(result) -> None:
    expenses = records(result, "expenses")
    om = {s: [r for r in of_site(expenses, s) if r["body"]["category"] == "OM"] for s in SITES}
    staff = {s: [r for r in of_site(expenses, s) if r["body"]["category"] == "STAFF"] for s in SITES}
    assert om["KISIWA-001"] == []
    assert (TENANT, "KISIWA-001", "2026-10", "actual", "om", "ESTIMATED_NOT_RECEIVED") in result.unwritten
    assert [money(om[s]) for s in ("KOBO-001", "MTO-001")] == [Decimal("600.00"), Decimal("500.00")]
    assert [money(staff[s]) for s in SITES] == [Decimal("500.00"), Decimal("500.00"), Decimal("450.00")]


def test_e6_budget(result) -> None:
    budget = records(result, "budget")
    kobo = {r["body"]["factor_id"]: r["body"]["value"] for r in of_site(budget, "KOBO-001")}
    assert {k: kobo[k] for k in ("revenue", "fuel_cost", "billed_kwh", "diesel_l", "tariff", "diesel_price")} == {
        "revenue": "3420.00", "fuel_cost": "875.00", "billed_kwh": "8550", "diesel_l": "700", "tariff": "0.40",
        "diesel_price": "1.25"}
    assert [r["body"]["factor_id"] for r in of_site(budget, "KOBO-001")] == [
        "revenue", "fuel_cost", "om", "staff", "billed_kwh", "diesel_l", "tariff", "diesel_price"]
    kisiwa = {r["body"]["factor_id"]: r["body"]["value"] for r in of_site(budget, "KISIWA-001")}
    assert (kisiwa["tariff"], kisiwa["diesel_price"]) == ("0.55", "1.30")


def test_e7_round_trip_identical_and_pinned(result) -> None:
    for f in result.files:
        read = read_layout(LAYOUTS[f.layout_id], f.data, tenant_code=f.tenant, produced_at="2026-11-06T06:00:00+03:00",
                           provenance="source-emulated")
        assert dict(read.refused) == {}
        assert read.obj["records"] == list(f.records)
    again = build()
    assert [(file_name(f), f.data) for f in again.files] == [(file_name(f), f.data) for f in result.files]
    assert again.unwritten == result.unwritten
    assert {file_name(f): hashlib.sha256(f.data).hexdigest() for f in result.files} == PINNED


def _planted(path: tuple[str, ...], value) -> dict:
    view = load_fixture()
    site = site_of(view, TENANT, "Kobo")
    if path[0] == "prices":
        tenant_of(view, TENANT)["prices"][path[1]]["Kobo"] = value
    else:
        site["period"][path[0]][path[1]] = value
    return view


@pytest.mark.parametrize("path,value,code", [
    (("actual", "revenue"), "3459.0", "EMU_REVENUE lakeside-power/KOBO-001"),
    (("actual", "diesel_cost"), "1476.0", "EMU_FUEL lakeside-power/KOBO-001"),
    (("actual", "collected"), "3181.0", "EMU_COLLECTIONS lakeside-power/KOBO-001"),
    (("prices", "tariff_usd_per_kwh"), "0.405", "EMU_PRICE lakeside-power/KOBO-001 tariff_usd_per_kwh"),
    (("actual", "billed_kwh"), "8645.5", "EMU_QUANTITY lakeside-power/KOBO-001 billed_kwh"),
    (("plan", "diesel_cost"), "876.0", "EMU_PLAN_PRICE lakeside-power/KOBO-001 diesel_price"),
], ids=["revenue", "fuel", "collections", "price", "quantity", "plan-price"])
def test_e8_planted_manifest_stops(path, value, code) -> None:
    with pytest.raises(ValueError) as raised:
        build(_planted(path, value))
    assert str(raised.value) == code


def test_e10_budget_prices_are_the_plans_own() -> None:
    """D-3A3.13: plan money / plan quantity, independent of the price list that prices the actuals."""
    view = load_fixture()
    plan = site_of(view, TENANT, "Kobo")["period"]["plan"]
    plan.update({"revenue": "3505.5", "diesel_cost": "910.0", "contribution": "1495.5"})
    mto = site_of(view, TENANT, "Mto")["period"]["plan"]
    mto["billed_kwh"] = 0
    del mto["diesel_l"]
    result = build(view)
    budget = records(result, "budget")
    kobo = {r["body"]["factor_id"]: r["body"]["value"] for r in of_site(budget, "KOBO-001")}
    assert (kobo["tariff"], kobo["diesel_price"]) == ("0.41", "1.30")
    assert money(of_site(records(result, "billing"), "KOBO-001")) == Decimal("3458.00")
    assert money([r for r in of_site(records(result, "expenses"), "KOBO-001") if r["body"]["category"] == "FUEL"]) \
        == Decimal("1475.00")
    kisiwa = {r["body"]["factor_id"]: r["body"]["value"] for r in of_site(budget, "KISIWA-001")}
    assert (kisiwa["tariff"], kisiwa["diesel_price"]) == ("0.55", "1.30")
    mto_lines = {r["body"]["factor_id"]: r["body"]["value"] for r in of_site(budget, "MTO-001")}
    assert mto_lines["billed_kwh"] == "0" and not {"tariff", "diesel_l", "diesel_price"} & set(mto_lines)
    listed = {(r[1], r[4], r[5]) for r in result.unwritten}
    assert ("MTO-001", "tariff_usd_per_kwh", "PLAN_PRICE_UNDEFINED") in listed
    assert ("MTO-001", "diesel_l", "PLAN_FIELD_ABSENT") in listed
    assert ("MTO-001", "diesel_usd_per_l", "PLAN_FIELD_ABSENT") in listed


def test_e9_every_kept_ds1b_record_is_written_or_listed(monkeypatch) -> None:
    """Residual: a DS1b record with no `site_code`, or a Site outside the tenant, is listed SITE_NOT_IN_TENANT."""
    import json
    from assetops_simulator.world import exports

    real = exports.to_canonical_json

    def planted(batch):
        doc = json.loads(real(batch))
        for kind in ("EXPENSE", "BUDGET_LINE"):
            found = next((r for r in doc["records"] if r["kind"] == kind and r["clocks"].get("recognition_period")
                          == "2026-10" and (r["body"].get("category") == "OM" or r["body"].get("factor_id") == "om")),
                         None)
            if found is not None:
                for tag, code in (("nosite", None), ("other", "ELSEWHERE-9")):
                    copy = json.loads(json.dumps(found))
                    copy["source_record_id"] = f"plant:{kind}:{tag}"
                    copy.pop("site_code", None)
                    if code:
                        copy["site_code"] = code
                    doc["records"].append(copy)
        return json.dumps(doc)

    monkeypatch.setattr(exports, "to_canonical_json", planted)
    result = build()
    listed = {r[4]: r for r in result.unwritten if r[5] == "SITE_NOT_IN_TENANT"}
    assert set(listed) == {f"plant:{k}:{t}" for k in ("EXPENSE", "BUDGET_LINE") for t in ("nosite", "other")}
    assert listed["plant:EXPENSE:nosite"][1] == "" and listed["plant:EXPENSE:other"][1] == "ELSEWHERE-9"
    written = {r["source_record_id"] for f in result.files for r in f.records}
    assert not written & set(listed)


def test_e9_unwritten_never_lists_a_written_field(result) -> None:
    keys = {r[:5] for r in result.unwritten}
    for side, field in (("actual", "revenue"), ("actual", "collected"), ("actual", "in_transit"),
                        ("actual", "diesel_cost"), ("actual", "billed_kwh"), ("actual", "diesel_l"),
                        ("plan", "revenue"), ("plan", "diesel_cost"), ("plan", "billed_kwh"), ("plan", "diesel_l")):
        assert (TENANT, "KOBO-001", "2026-10", side, field) not in keys
    assert (TENANT, "KOBO-001", "2026-10", "actual", "outstanding", "AS_UNPAID_CHARGES") in result.unwritten
    assert (TENANT, "KISIWA-001", "2026-10", "actual", "om", "ESTIMATED_NOT_RECEIVED") in result.unwritten
    assert all(r[2] == "2026-10" for r in result.unwritten if r[0] == TENANT)


def test_tool_exports_writes_files_and_refuses(tmp_path) -> None:
    out = tmp_path / "exports"
    run = subprocess.run([sys.executable, str(CLI), "exports", "--manifest", str(FIXTURE), "--out", str(out)],
                         capture_output=True, text=True, timeout=300)
    assert run.returncode == 0, run.stderr
    cold_ev = ["harvest-cold.expenses.csv", "harvest-cold.profile.cold-budget.csv",  # DD2b: cold and EV books
               "harvest-cold.profile.cold-storage-invoices.csv", "harvest-cold.profile.cold-storage-ledger.csv",
               "harvest-cold.profile.cold-storage-receipts.csv", "metro-bus.expenses.csv",
               "metro-bus.profile.ev-budget.csv", "metro-bus.profile.ev-fleet-roster.csv",
               "metro-bus.profile.ev-service-tickets.csv"]
    assert sorted(p.name for p in out.iterdir()) == sorted([*PINNED, *cold_ev, "unwritten.json"])
    assert {n: hashlib.sha256((out / n).read_bytes()).hexdigest() for n in PINNED} == PINNED
    again = subprocess.run([sys.executable, str(CLI), "exports", "--manifest", str(FIXTURE), "--out", str(out)],
                           capture_output=True, text=True, timeout=300)
    assert again.returncode == 3 and again.stderr.strip() == "DS1B_OUT not-empty"
