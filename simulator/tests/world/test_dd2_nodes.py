"""DD2.1 (spec `specs/DD-demo-data/spec.md` §5.1; D-DD.48, D-DD.51-54): mini-grid books from the structure's own nodes.

Every expected figure is written by hand from the pinned inputs: Kobo's July billed 8318 kWh, revenue 3327.20 and
collected 3059.74 (`history.json`: delivered 8755, technical loss 394, adjustments 43, outstanding 267.46 at 0.40).
The parity tests read the manifest; the exporter does not.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from decimal import Decimal

import pytest
import yaml

from assetops_simulator.world import exports
from assetops_simulator.world.exports import ZERO_LEAVES, build_exports, evaluate_mini_grid
from assetops_simulator.world.nodes import NODES
from assetops_simulator.world.history import generate_history
from assetops_simulator.world.records import PASS_THROUGH, build_records

from .conftest import REPOSITORY_ROOT, load_fixture, site_of, tenant_of

MANIFEST = REPOSITORY_ROOT / "Docs/demo-sprint/product-direction-layer4/demo-site-scenario-manifest.yaml"
TENANT = "lakeside-power"
SITES = ("KISIWA-001", "KOBO-001", "MTO-001")
MONTHS = ("2026-07", "2026-08", "2026-09", "2026-10")
OCTOBER_OLD_PINS = {  # test_3a3_exports.PINNED before DD2.1, with SOURCE_VERSION "1"
    "billing": "7111a18fdf8ed36ad19c7339e1266395d70065886008b2839cbc0bacd4e16534",
    "collections": "8b3cd80a03eaf2fa06f8f393189ca353bbd593ad6418b90551b4a3fd1a6352c3",
    "budget": "5b03eb3e849031311c40bc13accd13c278867ddbf81bb0443e0c34d1c3bfcb7e",
}


@pytest.fixture(scope="module")
def manifest() -> dict:
    return yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def full():
    view = load_fixture()
    return build_exports(view, generate_history(view))


def rows(result, key: str) -> list[dict]:
    return list(next(f for f in result.files if f.key == key).records)


def month_of(r: dict) -> str:
    return r["clocks"]["recognition_period"]


def total(rs: list[dict]) -> Decimal:
    return sum((Decimal(r["amount"]["value"]) for r in rs), Decimal(0))


# --- parity (D-DD.48 item 4a) -------------------------------------------------------------------------------------------

def test_the_leaf_alternatives_are_the_manifests(manifest) -> None:
    factor_map = manifest["factor_map"]["MINI_GRID"]
    read = set()
    for _, text, _ in NODES["MINI_GRID"]:
        read |= set(re.findall(r"[a-z_]+", text))
    leaves = {name for name in read if name in factor_map}
    assert leaves == {"delivered_kwh", "technical_loss_kwh", "unexplained_loss_kwh", "adjustments_kwh", "unmapped_kwh",
                      "tariff", "productive_kwh", "productive_tariff", "in_transit", "outstanding", "necessary_l",
                      "candidate_l", "unexplained_l", "extra_l", "diesel_price"}
    zero = set()
    for leaf in leaves:
        alternatives = [a.strip() for a in factor_map[leaf].split("|")]
        if alternatives[-1] == "0" and len(alternatives) > 1:
            zero.add(leaf)
        fields = tuple(a[len("record."):] for a in alternatives if a.startswith("record."))
        if fields:
            assert PASS_THROUGH["MINI_GRID"][leaf] == fields, leaf
    assert zero == ZERO_LEAVES == {"technical_loss_kwh", "unexplained_loss_kwh", "adjustments_kwh", "unmapped_kwh",
                                   "in_transit", "outstanding", "candidate_l", "unexplained_l"}
    assert factor_map["productive_kwh"] == '0' and factor_map["extra_l"] == '0'


# --- October proves the derivation against the world's own record (item 4b) --------------------------------------------

def test_october_evaluated_equals_recorded_on_both_sides_at_every_site() -> None:
    view = load_fixture()
    tenant = tenant_of(view, TENANT)
    expected = {  # by hand: the period's own nodes
        "Kobo": ({"metered_kwh": 8690, "billed_kwh": 8645, "revenue": "3458", "collected": "3180", "diesel_l": 1180,
                  "fuel_cost": "1475"}, {"billed_kwh": 8550, "revenue": "3420", "diesel_l": 700, "fuel_cost": "875"}),
        "Kisiwa": ({"billed_kwh": 7400, "revenue": "4070", "collected": "3800", "diesel_l": 2400, "fuel_cost": "3120"},
                   {"billed_kwh": 7500, "revenue": "4125", "fuel_cost": "2990"}),
        "Mto": ({"billed_kwh": 5400, "revenue": "2160", "collected": "1890", "diesel_l": 320, "fuel_cost": "400"},
                {"billed_kwh": 5600, "revenue": "2240", "fuel_cost": "375"}),
    }
    for name, (actual, plan) in expected.items():
        site = site_of(view, TENANT, name)
        prices = dict(tariff=Decimal(tenant["prices"]["tariff_usd_per_kwh"][name]),
                      diesel_price=Decimal(tenant["prices"]["diesel_usd_per_l"][name]),
                      productive_tariff=Decimal(tenant["prices"]["productive_tariff_usd_per_kwh"]))
        for side, want in (("actual", actual), ("plan", plan)):
            got = evaluate_mini_grid(site["period"][side], money_in_cents=False, **prices)
            for node, value in want.items():
                assert got[node] == Decimal(str(value)), (name, side, node)


def test_a_changed_october_leaf_stops_the_emulator_with_emu_node() -> None:
    view = load_fixture()
    site_of(view, TENANT, "Kobo")["period"]["actual"]["adjustments_kwh"] = 50
    with pytest.raises(ValueError) as raised:
        build_exports(view, generate_history(view))
    assert str(raised.value) == "EMU_NODE lakeside-power/KOBO-001 2026-10 billed_kwh"


def test_a_changed_october_plan_leaf_stops_it_too() -> None:
    view = load_fixture()
    site_of(view, TENANT, "Kobo")["period"]["plan"]["diesel_l"] = 710
    with pytest.raises(ValueError) as raised:
        build_exports(view, generate_history(view))
    assert str(raised.value) == "EMU_NODE lakeside-power/KOBO-001 2026-10 plan.fuel_cost"


# --- history months (item 4d) ------------------------------------------------------------------------------------------

def test_july_at_kobo_is_derived_from_the_pinned_leaves(full) -> None:
    july = [r for r in rows(full, "billing") if month_of(r) == "2026-07" and r["site_code"] == "KOBO-001"]
    assert sum(int(r["quantity"]["value"]) for r in july) == 8318
    assert total(july) == Decimal("3327.20")
    receipts = [r for r in rows(full, "collections") if month_of(r) == "2026-07" and r["site_code"] == "KOBO-001"]
    assert total([r for r in receipts if r["status"] == "COLLECTED"]) == Decimal("3059.74")
    assert total(receipts) == Decimal("3059.74")  # no in transit in July


def test_every_month_has_billing_receipts_and_fuel_at_every_site(full) -> None:
    for month in MONTHS:
        for site in SITES:
            assert any(month_of(r) == month and r["site_code"] == site for r in rows(full, "billing")), (month, site)
            assert any(month_of(r) == month and r["site_code"] == site and r["body"]["category"] == "FUEL"
                       for r in rows(full, "expenses")), (month, site)
            assert any(month_of(r) == month and r["site_code"] == site and r["body"]["factor_id"] == "revenue"
                       for r in rows(full, "budget")), (month, site)


def test_rows_are_ordered_by_month_then_site(full) -> None:
    for key in ("billing", "collections", "expenses", "budget"):
        order = [(month_of(r), r["site_code"]) for r in rows(full, key)]
        assert order == sorted(order), key


def test_history_money_is_in_cents_and_october_in_dollars(full) -> None:
    expenses = rows(full, "expenses")
    kobo = lambda month, cat: [r["amount"]["value"] for r in expenses  # noqa: E731
                               if r["site_code"] == "KOBO-001" and month_of(r) == month and r["body"]["category"] == cat]
    assert kobo("2026-07", "OM") == ["600.00"] and kobo("2026-07", "STAFF") == ["500.00"]  # 60000 and 50000 cents
    assert kobo("2026-10", "OM") == ["600.00"] and kobo("2026-10", "STAFF") == ["500.00"]  # "600.0" and "500.0" dollars


def test_the_plan_side_is_evaluated_every_month(full) -> None:
    kobo = {(month_of(r), r["body"]["factor_id"]): r["body"]["value"] for r in rows(full, "budget")
            if r["site_code"] == "KOBO-001"}
    assert kobo[("2026-07", "revenue")] == "3420.00" and kobo[("2026-07", "fuel_cost")] == "875.00"  # 8550 x .40, 700 x 1.25
    assert kobo[("2026-07", "tariff")] == "0.40" and kobo[("2026-07", "diesel_price")] == "1.25"


def test_months_selects_and_default_is_history_plus_the_period() -> None:
    view = load_fixture()
    history = generate_history(view)
    default = build_exports(view, history)
    assert {month_of(r) for f in default.files for r in f.records} == set(MONTHS)
    only = build_exports(view, history, months=["2026-10"])
    assert {month_of(r) for f in only.files for r in f.records} == {"2026-10"}
    with pytest.raises(ValueError, match="EMU_MONTH 2026-06"):
        build_exports(view, history, months=["2026-06"])


# --- October bytes are unchanged by the node derivation (D-DD.48 "one mechanism") --------------------------------------

def test_october_billing_collections_and_budget_bytes_are_unchanged(monkeypatch) -> None:
    monkeypatch.setattr(exports, "SOURCE_VERSION", "1")
    view = load_fixture()
    result = build_exports(view, generate_history(view), months=["2026-10"])
    got = {f.key: hashlib.sha256(f.data).hexdigest() for f in result.files}
    assert {k: got[k] for k in OCTOBER_OLD_PINS} == OCTOBER_OLD_PINS


def test_source_version_is_two_except_on_receipts() -> None:
    """The collections layout holds `source_version` "1" as a constant, so receipts keep it (a packet deviation)."""
    assert exports.SOURCE_VERSION == "2"
    view = load_fixture()
    result = build_exports(view, generate_history(view))
    own = [r for f in result.files for r in f.records
           if re.search(r":(charge|fuel|receipt)-\d+$|:fuel-\d+$", r["source_record_id"])]
    assert {r["source_version"] for r in own if r["kind"] != "RECEIPT"} == {"2"}
    assert {r["source_version"] for r in own if r["kind"] == "RECEIPT"} == {"1"}


# --- fuel notes (D-DD.53) ----------------------------------------------------------------------------------------------

def test_the_dated_note_table_is_the_manifests_disorder_test(manifest) -> None:
    (test,) = [t for t in manifest["disorder_tests"] if t["id"] == "OOO-1"]
    found = re.fullmatch(r"(\w+) fuel delivery note of (\d+) L arrives \d+ days late \(recorded [\d-]+ for ([\d-]+)\)",
                         test["what"])
    assert found is not None
    assert exports.DATED_NOTES == (("OOO-1", TENANT, found.group(1), found.group(3), int(found.group(2))),)


def test_kobo_october_notes(full) -> None:
    notes = [(r["clocks"]["occurred_at"], r["quantity"]["value"]) for r in rows(full, "expenses")
             if r["site_code"] == "KOBO-001" and month_of(r) == "2026-10" and r["body"]["category"] == "FUEL"]
    assert sorted(notes) == [("2026-10-01T10:00:00+03:00", "400"), ("2026-10-08T10:00:00+03:00", "380"),
                             ("2026-10-26T10:00:00+03:00", "400")]


def test_other_months_cut_400_l_notes_on_the_fixed_days(full) -> None:
    for month in MONTHS[:3]:
        for site in SITES:
            fuel = [r for r in rows(full, "expenses") if r["site_code"] == site and month_of(r) == month
                    and r["body"]["category"] == "FUEL"]
            days = [r["clocks"]["occurred_at"][8:10] for r in fuel]
            assert days == ["01", "08", "15", "22", "29", "01", "08", "15"][: len(fuel)], (month, site)
            assert all(r["clocks"]["occurred_at"][11:19] == "10:00:00" for r in fuel)
            assert [r["quantity"]["value"] for r in fuel[:-1]] == ["400"] * (len(fuel) - 1)
    kobo_july = [r for r in rows(full, "expenses") if r["site_code"] == "KOBO-001" and month_of(r) == "2026-07"
                 and r["body"]["category"] == "FUEL"]
    assert sum(int(r["quantity"]["value"]) for r in kobo_july) == 703 + 257 + 12  # necessary + candidate + unexplained
    assert "remainder" in kobo_july[-1]["body"]["document_ref"]


# --- every DS1b record lands in exactly one place (D-DD.54) ------------------------------------------------------------

def test_every_ds1b_record_is_written_staged_or_listed_for_all_three_tenants(full) -> None:
    view = load_fixture()
    history = generate_history(view)
    made = build_records(view, history)
    written = {r["source_record_id"] for f in full.files for r in f.records}
    staged = {}
    for name, data in full.staged:
        for r in json.loads(data)["records"]:
            staged.setdefault(r["source_record_id"], []).append(name)
    listed = {}
    for row in full.unwritten:
        if row[4].startswith("gen:"):
            listed.setdefault(row[4], []).append(row)
    seen = 0
    for batch in made.batches:
        for r in json.loads(__import__("assetops_contracts.canonical", fromlist=["x"]).to_canonical_json(batch))["records"]:
            rid = r["source_record_id"]
            places = (rid in written) + len(staged.get(rid, [])) + len(listed.get(rid, []))
            assert places == 1, (rid, places)
            seen += 1
    assert seen > 0
    assert {t for t in (b.batch.tenant_code for b in made.batches)} == {"lakeside-power", "harvest-cold", "metro-bus"}


def test_staged_files_are_named_by_tenant_and_source_type(full) -> None:
    names = [n for n, _ in full.staged]
    assert names and all(re.fullmatch(r"[a-z-]+\.(billing_export|customer_invoicing)\.json", n) for n in names)
    assert names == sorted(names)


# --- absent leaves and negative nodes (D-DD.48 item 3) -----------------------------------------------------------------

def test_an_absent_required_leaf_writes_no_row_and_is_listed_not_in_history() -> None:
    view = load_fixture()
    actual = site_of(view, TENANT, "Kobo")["period"]["actual"]
    for field in ("delivered_kwh", "billed_kwh", "metered_kwh", "revenue", "collected"):
        del actual[field]
    result = build_exports(view, generate_history(view), months=["2026-10"])
    assert not [r for r in rows(result, "billing") if r["site_code"] == "KOBO-001"]
    assert not [r for r in rows(result, "collections") if r["site_code"] == "KOBO-001"]
    assert [r for r in rows(result, "expenses") if r["site_code"] == "KOBO-001" and r["body"]["category"] == "FUEL"]
    listed = {(r[1], r[4], r[5]) for r in result.unwritten if r[2] == "2026-10"}
    for node in ("billed_kwh", "revenue", "collected"):
        assert ("KOBO-001", node, "NOT_IN_HISTORY") in listed


def test_a_negative_collected_node_stops_the_emulator() -> None:
    view = load_fixture()
    actual = site_of(view, TENANT, "Kobo")["period"]["actual"]
    actual.update({"outstanding": "9000.0", "collected": "-5542.0"})  # the period records the node it implies
    with pytest.raises(ValueError) as raised:
        build_exports(view, generate_history(view), months=["2026-10"])
    assert str(raised.value) == "EMU_COLLECTIONS lakeside-power/KOBO-001"


# --- statements (DD2.5; DD spec §5.4) ----------------------------------------------------------------------------------

def test_lakesides_statements_are_the_sums_of_its_history_month_rows(full) -> None:
    (name, data), = full.statements
    assert name == "lakeside-power.statements.json"
    doc = json.loads(data)
    assert doc["schema"] == "assetops.world-statements/1" and doc["tenant"] == TENANT
    assert [s["period"] for s in doc["statements"]] == ["2026-07", "2026-08", "2026-09"]  # October stays in the walk
    july = doc["statements"][0]
    assert july["currency"] == "USD"
    assert july["source_ref"] == "Emulated management accounts, July 2026, final"
    billing = [r for r in rows(full, "billing") if month_of(r) == "2026-07"]
    fuel = [r for r in rows(full, "expenses") if month_of(r) == "2026-07" and r["body"]["category"] == "FUEL"]
    assert Decimal(july["revenue"]) == total(billing) and Decimal(july["fuel_cost"]) == total(fuel)
    assert set(july) == {"period", "currency", "revenue", "fuel_cost", "source_ref"}


def test_the_statements_writer_takes_cold_and_ev_rows_with_energy_cost() -> None:
    """DD2.5: the cold and EV writer, on a fixture of measured bill rows (the real rows come with DD4.4)."""
    from assetops_simulator.world.statements import figures_from_rows, statements_document
    invoices = [{"clocks": {"recognition_period": "2026-10"}, "amount": {"value": "868.00"}},
                {"clocks": {"recognition_period": "2026-10"}, "amount": {"value": "1736.00"}}]
    bills = [{"clocks": {"recognition_period": "2026-10"}, "amount": {"value": "250.50"}},
             {"clocks": {"recognition_period": "2026-10"}, "amount": {"value": "300.25"}}]
    figures = figures_from_rows(invoices, bills, ["2026-07", "2026-10"])
    doc = statements_document("harvest-cold", "USD", "energy_cost", figures)
    assert doc["statements"] == [{"period": "2026-10", "currency": "USD", "revenue": "2604.00",
                                  "energy_cost": "550.75",
                                  "source_ref": "Emulated management accounts, October 2026, final"}]
    with pytest.raises(ValueError, match="STATEMENT_INCOMPLETE 2026-10"):
        figures_from_rows(invoices, [], ["2026-10"])
