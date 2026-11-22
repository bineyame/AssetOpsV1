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
    "lakeside-power.billing.csv": "20955b91fe9b94ec8f2c9d3ae5d0be0c617a569752e83afb3759cd3c33125013",
    "lakeside-power.collections.csv": "8b3cd80a03eaf2fa06f8f393189ca353bbd593ad6418b90551b4a3fd1a6352c3",
    "lakeside-power.expenses.csv": "74c5ad181475d6b025d25de2c78f3b71fd941c839dfb16811b83e55f0bec37d4",
    "lakeside-power.budget.csv": "1c10cdb5442e83f3980d7ecfb0dae99229d5b76bbe8155f82aafc128bbd6d368",
}
#: DD2.1: what `world_history.py exports` writes by default, every month (the packet lists both moves). The receipts
#: keep `source_version` "1" (the collections layout's constant), so that October file's hash did not move.
PINNED_ALL_MONTHS = {
    "lakeside-power.billing.csv": "e5b74fbbc6816d1cd1059fc0d7d0786e373c9f0be8fb19ce4a6df9bd74fe39d6",
    "lakeside-power.collections.csv": "8bb39b30e13123ff9e33d3fba4f551d115717d488dc9c6a9f5e826899f0eb00f",
    "lakeside-power.expenses.csv": "00e3449a7a1ec107b639d8003b1e4d578aff0b7b7d237f0d22abd504015bf5b5",
    "lakeside-power.budget.csv": "e12bcd1f78886ff4c5e13291c7fd3c6636a067f95e6537ca7dd104ce9ea34adc",
}


def build(view: dict | None = None):
    """October only: DD2.1 widened `build_exports` to every month; these E-tests are the October books (D-DD.48)."""
    view = view if view is not None else load_fixture()
    return build_exports(view, generate_history(view), months=["2026-10"])


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
    # D-DD.53: OOO-1's dated note (26 Oct) is cut first; the rest of Kobo's 780 L is 400 L on the 1st, 380 L on the 8th.
    assert [(r["clocks"]["occurred_at"][8:10], r["quantity"]["value"]) for r in by["KOBO-001"]] == [
        ("26", "400"), ("01", "400"), ("08", "380")]
    assert [r["clocks"]["occurred_at"][8:10] for r in by["KISIWA-001"]] == ["01", "08", "15", "22", "29", "01"]


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


def _planted(changes: dict[tuple[str, str], object]) -> dict:
    view = load_fixture()
    site = site_of(view, TENANT, "Kobo")
    for (side, name), value in changes.items():
        if side == "prices":
            tenant_of(view, TENANT)["prices"][name]["Kobo"] = value
        else:
            site["period"][side][name] = value
    return view


#: D-DD.48: the books are the structure's nodes, so a planted record that disagrees with its node stops the emulator at
#: `EMU_NODE` first; the rows' own totals checks (`EMU_REVENUE`, `EMU_COLLECTIONS`, `EMU_FUEL`) hold behind it.
@pytest.mark.parametrize("changes,code", [
    ({("actual", "revenue"): "3459.0"}, "EMU_NODE lakeside-power/KOBO-001 2026-10 revenue"),
    ({("actual", "diesel_cost"): "1476.0"}, "EMU_NODE lakeside-power/KOBO-001 2026-10 fuel_cost"),
    ({("actual", "collected"): "3181.0"}, "EMU_NODE lakeside-power/KOBO-001 2026-10 collected"),
    ({("prices", "tariff_usd_per_kwh"): "0.405"}, "EMU_PRICE lakeside-power/KOBO-001 tariff_usd_per_kwh"),
    ({("actual", "delivered_kwh"): 9100.5, ("actual", "metered_kwh"): "8690.5", ("actual", "billed_kwh"): "8645.5",
      ("actual", "revenue"): "3458.2", ("actual", "collected"): "3180.2"},
     "EMU_QUANTITY lakeside-power/KOBO-001 billed_kwh"),
    ({("plan", "diesel_cost"): "876.0"}, "EMU_NODE lakeside-power/KOBO-001 2026-10 plan.fuel_cost"),
], ids=["revenue", "fuel", "collections", "price", "quantity", "plan-node"])
def test_e8_planted_manifest_stops(changes, code) -> None:
    with pytest.raises(ValueError) as raised:
        build(_planted(changes))
    assert str(raised.value) == code


def test_e10_budget_prices_follow_the_evaluated_plan_nodes() -> None:
    """D-DD.48: D-3A3.13's unit prices are the evaluated plan node over the plan quantity."""
    view = load_fixture()
    mto = site_of(view, TENANT, "Mto")["period"]["plan"]
    mto["billed_kwh"] = 0
    mto["revenue"] = "0.0"  # the node is now 0, and the period records it
    del mto["diesel_l"]
    result = build(view)
    budget = records(result, "budget")
    kobo = {r["body"]["factor_id"]: r["body"]["value"] for r in of_site(budget, "KOBO-001")}
    assert (kobo["tariff"], kobo["diesel_price"]) == ("0.40", "1.25")
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
    assert sorted(p.name for p in out.iterdir()) == sorted([
        *PINNED_ALL_MONTHS, "harvest-cold.customer_invoicing.json", "lakeside-power.statements.json", "unwritten.json"])
    assert {n: hashlib.sha256((out / n).read_bytes()).hexdigest() for n in PINNED_ALL_MONTHS} == PINNED_ALL_MONTHS
    again = subprocess.run([sys.executable, str(CLI), "exports", "--manifest", str(FIXTURE), "--out", str(out)],
                           capture_output=True, text=True, timeout=300)
    assert again.returncode == 3 and again.stderr.strip() == "DS1B_OUT not-empty"
