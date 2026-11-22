"""DD2b fix round 7 (spec `specs/DD-demo-data/spec.md` §3, §5.2, §5.3; D-DD.59 to D-DD.63, D-DD.65a): one cold
invoicing export, the source-system rule at export, the tariff schedules and their parity with the invoice rows, the
opening stock of the ledger, and the byte pins of the cold and EV files."""

from __future__ import annotations

import hashlib
import json
from datetime import date

import pytest

from assetops_simulator.world.books import check_source_systems, staged_batch
from assetops_simulator.world.exports import ExportFile, file_name
from assetops_simulator.world.profile_csv import PROFILES_DIR
from assetops_simulator.world.tariffs import tariff_schedules

from .books_support import COLD, EV, PINNED_COLD_EV, build, built, emulated_files, files_by_name, m_site, m_tenant, \
    manifest, sample_of, tenant_view
from .conftest import load_fixture, site_of

INVOICING = f"{COLD}.profile.cold-storage-invoicing.csv"


# --- D-DD.59: one cold invoicing profile ---------------------------------------------------------------------------

def test_r1_one_invoicing_profile_replaces_invoices_and_receipts() -> None:
    names = {p.name.removesuffix(".profile.json") for p in PROFILES_DIR.glob("cold-storage-*.profile.json")}
    assert names == {"cold-storage-invoicing-illustrative", "cold-storage-ledger-illustrative"}
    profile = json.loads((PROFILES_DIR / "cold-storage-invoicing-illustrative.profile.json").read_text())
    assert (profile["source_type"], profile["source_system"], profile["version"], profile["constants"]) == (
        "customer_invoicing", "cold-storage-invoicing", {"from": "row_digest"}, {})
    assert profile["columns"][0]["header"] == "Type"
    assert profile["columns"][0]["paths"][0]["path"] == "kind"


def test_r2_thikas_credit_note_is_a_row_of_the_invoicing_file() -> None:
    rows = list(files_by_name(built()[3])[INVOICING].records)
    assert {r["kind"] for r in rows} == {"CHARGE", "RECEIPT", "ADJUSTMENT"}
    (note,) = [r for r in rows if r["kind"] == "ADJUSTMENT"]
    assert (note["source_record_id"], note["site_code"], note["subject"], note["amount"]) == (
        "gen:COLD-THIKA:2026-10:actual:liability", "COLD-THIKA", {"kind": "SITE", "ref": "COLD-THIKA"},
        {"value": "-108.00", "currency": "USD"})
    assert note["body"] == {"reason_code": "CUSTOMER_COMPENSATION", "authorised_by_ref": "finance-lead",
                            "document_ref": "gen:COLD-THIKA:2026-10:actual:liability"}
    assert not any(n.endswith("customer_invoicing.json") for n, _ in built()[3].staged)  # no longer staged JSON
    assert all(r["source_version"].startswith("r") for r in rows)  # row_digest on every row


def test_r3_the_sample_shows_every_type_and_map_value() -> None:
    _, records = sample_of("cold-storage-invoicing-illustrative")
    assert {r["kind"] for r in records} == {"CHARGE", "RECEIPT", "ADJUSTMENT"}
    assert {r["body"].get("method") for r in records if r["kind"] == "RECEIPT"} == {"MOBILE_MONEY", "BANK", "CASH"}
    assert {r["status"] for r in records if r["kind"] == "RECEIPT"} == {"COLLECTED", "PAID_IN_TRANSIT"}


# --- D-DD.60: the source-system rule at export ---------------------------------------------------------------------

def test_r4_the_real_manifest_passes_and_stages_only_tariffs() -> None:
    books = built()[3]
    assert [n for n, _ in books.staged] == [f"{COLD}.storage_rate_card.json", f"{EV}.utility_invoice.json"]


def test_r5_a_nonzero_lakeside_liability_stops_emu_source_switch() -> None:
    def plant(history):
        history["tenants"]["lakeside-power"]["Kobo"]["2026-08"]["actual"]["liability"] = 2500
    with pytest.raises(ValueError, match=r"^EMU_SOURCE_SWITCH lakeside-power billing_export KOBO-001$"):
        build(edit_history=plant)


def _file(tenant: str, layout_id: str, site: str) -> ExportFile:
    return ExportFile(tenant, "k", layout_id, ({"site_code": site},), b"")


def test_r6_two_files_of_one_source_type_stop() -> None:
    a = _file("t", "billing-illustrative-1", "S-1")
    with pytest.raises(ValueError, match=r"^EMU_SOURCE_SWITCH t billing_export S-1$"):
        check_source_systems([a, _file("t", "billing-illustrative-1", "S-1")], [])
    check_source_systems([a, _file("u", "billing-illustrative-1", "S-1")], [])  # another tenant is no clash


def test_r7_a_staged_batch_in_another_system_stops_only_on_a_shared_site() -> None:
    view = load_fixture()
    record = {"format_version": 1, "kind": "ADJUSTMENT", "source_record_id": "x", "source_version": "1",
              "site_code": "S-1", "subject": {"kind": "SITE", "ref": "S-1"},
              "clocks": {"effective_from": "2026-10-01", "recognition_period": "2026-10"},
              "amount": {"value": "-1.00", "currency": "USD"},
              "body": {"reason_code": "CUSTOMER_COMPENSATION", "authorised_by_ref": "a", "document_ref": "x"}}
    staged = [staged_batch(view, "t", "billing_export", [record])]
    with pytest.raises(ValueError, match=r"^EMU_SOURCE_SWITCH t billing_export S-1$"):
        check_source_systems([_file("t", "billing-illustrative-1", "S-1")], staged)
    check_source_systems([_file("t", "billing-illustrative-1", "S-2")], staged)
    check_source_systems([_file("t", "expenses-illustrative-1", "S-1")], staged)


def test_r8_cold_adjustment_is_staged_only_where_no_invoicing_file_exists() -> None:
    def estimated(history):  # GAP-1: an estimated month writes no invoice and no receipt
        for site in history["tenants"][COLD].values():
            for block in site.values():
                block.setdefault("coverage", {})["revenue"] = "ESTIMATED"
    view = load_fixture()
    for site in tenant_view(view, COLD)["sites"]:
        site["period"].setdefault("coverage", {})["revenue"] = "ESTIMATED"
    books = build(view, estimated)[3]
    assert INVOICING not in files_by_name(books)
    assert f"{COLD}.customer_invoicing.json" in [n for n, _ in books.staged]


# --- D-DD.61: tariff schedules --------------------------------------------------------------------------------------

def _schedules() -> dict:
    out = {}
    for tenant, batch in tariff_schedules(built()[0]).items():
        for r in batch["records"]:
            out.setdefault((tenant, r["site_code"]), []).append(r)
    return out


def _price(text: str) -> str:
    return f"{float(text):.2f}"


def test_r9_cold_rate_card_is_t_storage_at_the_manifests_price() -> None:
    schedules = _schedules()
    price = _price(m_tenant(COLD)["prices"]["storage_usd_per_crate_day"])
    for site in m_tenant(COLD)["sites"]:
        (r,) = schedules[(COLD, site["code"])]
        assert r["source_record_id"] == f"gen:{site['code']}:tariff:2026-07-01"
        assert (r["body"]["contract_ref"], r["clocks"]) == ("T-STORAGE", {"effective_from": "2026-07-01"})
        assert r["body"]["bands"] == [{"band": "STORAGE", "from": "00:00", "to": "24:00", "rate": price,
                                       "unit": "per_crate_day"}]
    batch = tariff_schedules(built()[0])[COLD]
    assert (batch["source_type"], batch["source_system"]) == ("storage_rate_card", "cold-storage-invoicing")


def test_r10_ev_schedules_are_c114_twice_c117_and_the_flat_tariff() -> None:
    schedules = _schedules()
    batch = tariff_schedules(built()[0])[EV]
    assert (batch["source_type"], batch["source_system"]) == ("utility_invoice", "ev-utility-invoice")
    old, new = schedules[(EV, "EV-EMB")]
    assert (old["body"]["contract_ref"], old["clocks"]) == ("C-114", {"effective_from": "2026-07-01",
                                                                      "effective_to": "2026-10-31"})
    assert (new["body"]["contract_ref"], new["clocks"]) == ("C-114", {"effective_from": "2026-11-01"})
    bands = lambda r: [(b["band"], b["from"], b["to"], b["rate"]) for b in r["body"]["bands"]]  # noqa: E731
    assert bands(old) == [("OFFPEAK-AM", "00:00", "18:00", "0.12"), ("PEAK", "18:00", "22:00", "0.24"),
                          ("OFFPEAK-PM", "22:00", "24:00", "0.12")]
    assert bands(new) == [("NIGHT", "00:00", "05:00", "0.09"), ("OFFPEAK-AM", "05:00", "18:00", "0.12"),
                          ("PEAK", "18:00", "22:00", "0.24"), ("OFFPEAK-PM", "22:00", "24:00", "0.12")]
    assert old["body"]["demand_rate"] == new["body"]["demand_rate"] == "12.00"
    (ruiru,) = schedules[(EV, "EV-RUI")]
    assert (ruiru["body"]["contract_ref"], bands(ruiru), ruiru["body"]["demand_rate"]) == (
        "C-117", bands(old), "12.00")
    (kasarani,) = schedules[(EV, "EV-KAS")]
    assert kasarani["body"]["contract_ref"] == "FLAT-EV-KASARANI" and "demand_rate" not in kasarani["body"]
    assert bands(kasarani) == [("FLAT", "00:00", "24:00", "0.15")]


def test_r11_every_schedule_rate_is_the_manifests_price() -> None:
    for site in m_tenant(EV)["sites"]:
        prices = site["tariff"]["prices"]
        wanted = {_price(prices["peak"]), _price(prices["offpeak"]), _price(prices["night_from_1_nov"]),
                  _price(site["tariff"].get("usd_per_kwh", prices["peak"]))}
        for r in _schedules()[(EV, site["code"])]:
            assert {b["rate"] for b in r["body"]["bands"]} <= wanted, site["code"]
            if "demand_rate" in r["body"]:
                assert r["body"]["demand_rate"] == _price(prices["demand_per_kw_month"])


def _in_force(tenant: str, site: str, code: str, on: str) -> bool:
    return any(r["body"]["contract_ref"] == code and r["clocks"]["effective_from"] <= on
               and r["clocks"].get("effective_to", "9999") >= on for r in _schedules()[(tenant, site)])


def test_r12_every_invoice_tariff_code_is_a_schedule_in_force() -> None:
    checked = 0
    for r in files_by_name(built()[3])[INVOICING].records:
        if r["kind"] == "CHARGE":
            assert _in_force(COLD, r["site_code"], r["body"]["tariff_code"], r["clocks"]["effective_from"]), r
            checked += 1
    invoice = emulated_files()[f"{EV}.profile.ev-utility-invoice.csv"].records  # DD4.4: from the measured fixture
    for r in invoice:
        assert _in_force(EV, r["site_code"], r["body"]["tariff_code"], r["clocks"]["effective_from"]), r
        checked += 1
    assert len(invoice) >= 28 and checked > 50
    assert not _in_force(COLD, "COLD-THIKA", "T-STORAGE", "2026-06-30")  # the rule can fail


def test_r13_a_tariff_code_with_no_schedule_fails_the_parity() -> None:
    assert not _in_force(EV, "EV-RUI", "C-114", "2026-10-01")  # Ruiru has C-117 only


# --- D-DD.63: opening stock -----------------------------------------------------------------------------------------

def test_r14_june_ledger_rows_are_opening_stock() -> None:
    ledger = list(files_by_name(built()[3])[f"{COLD}.profile.cold-storage-ledger.csv"].records)
    june = [r for r in ledger if r["clocks"]["occurred_at"] < "2026-07"]
    assert june and {r["body"]["direction"] for r in june} == {"IN"}
    for r in june:  # still in on 1 July: an OUT of the same batch on or after the first
        outs = [o for o in ledger if o["body"]["batch_ref"] == r["body"]["batch_ref"] and o["body"]["direction"] == "OUT"]
        assert outs and min(o["clocks"]["occurred_at"] for o in outs) >= "2026-07-01"
    ins = {r["body"]["batch_ref"] for r in ledger if r["body"]["direction"] == "IN"}
    assert all(r["body"]["batch_ref"] in ins for r in ledger)  # every stored OUT has its IN
    months = {r["clocks"]["recognition_period"] for r in files_by_name(built()[3])[INVOICING].records}
    assert months == {"2026-07", "2026-08", "2026-09", "2026-10"}  # June has no invoice or receipt


# --- D-DD.65a: sha256 pins ------------------------------------------------------------------------------------------

def test_r15_cold_and_ev_files_are_byte_pinned(request) -> None:
    got = {file_name(f): hashlib.sha256(f.data).hexdigest() for f in built()[3].files if f.tenant in (COLD, EV)}
    if request.config.getoption("--update-golden"):
        print(json.dumps(got, indent=4))
    assert got == PINNED_COLD_EV
