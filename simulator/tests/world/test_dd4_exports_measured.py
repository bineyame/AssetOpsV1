"""DD4.4 (spec §5.6, §5.4; D-DD.20, D-DD.99, D-DD.124): the measured books from `measured.json`.

The documents here are hand-written in `measured.json`'s schema (D-DD.99) so each rule is asserted on known text: the
cold bill (room meter kWh at T-GRID-COLD), the EV invoice (one USAGE row per price class with `body.band`, DEMAND where
the schedule has a demand rate), the departure log (`block_met` derived), `meter_billed` and the statements (EV without
revenue). Prices are asserted against `M`, read here as YAML (the modules never read it)."""

from __future__ import annotations

import copy
import json
from decimal import Decimal

import pytest

from assetops_simulator.world import exports_measured as em
from assetops_simulator.world.profile_csv import load_profile

from .books_support import COLD, EV, built, files_by_name, m_site, m_tenant

MONTHS = ("2026-07", "2026-08", "2026-09", "2026-10")


def tenant(slug: str) -> dict:
    return next(t for t in built()[0]["tenants"] if t["tenant"] == slug)


def cold_doc() -> dict:
    sites = {}
    for i, s in enumerate(tenant(COLD)["sites"]):
        months = {m: {"room_kwh": f"{1500 + 10 * i + j}.325"} for j, m in enumerate(MONTHS)}
        months["2026-11"] = {"room_kwh": "250.000", "partial_to": "2026-11-06T06:00:00+03:00"}
        sites[s["code"]] = months
    return {"schema": em.MEASURED_SCHEMA, "tenant": COLD, "sites": sites}


def _bands(code: str, month: str) -> dict:
    if code == "EV-KAS":
        return {"FLAT": "30000.500"}
    out = {"OFFPEAK": "50000.125", "PEAK": "20000.375"}
    if code == "EV-EMB" and month == "2026-11":
        out["NIGHT"] = "4000.000"
    return out


def ev_doc() -> dict:
    sites = {}
    for s in tenant(EV)["sites"]:
        months = {}
        for m in MONTHS + ("2026-11",):
            b = _bands(s["code"], m)
            months[m] = {"bands": b, "demand_kw": "480.333",
                         "import_kwh": f"{sum(Decimal(v) for v in b.values()):.3f}",
                         "windows": {"0000_0500": "9000.250", "2200_2400": "11000.125"}}
        months["2026-11"]["partial_to"] = "2026-11-06T06:00:00+03:00"
        sites[s["code"]] = months
    departures = [
        {"site_code": "EV-KAS", "vehicle_ref": "EV-KAS-B01", "block_ref": "EV-KAS-BLK-01", "service_day": "2026-11-02",
         "departure_at": "2026-11-03T05:00:00+03:00", "required_kwh": "150.000", "kwh_at_departure": "150.000"},
        {"site_code": "EV-KAS", "vehicle_ref": "EV-KAS-S01", "block_ref": "EV-KAS-BLK-S1", "service_day": "2026-11-02",
         "departure_at": "2026-11-03T05:00:00+03:00", "required_kwh": "150.000", "kwh_at_departure": "149.999"}]
    return {"schema": em.MEASURED_SCHEMA, "tenant": EV, "sites": sites, "departures": departures}


@pytest.fixture(scope="module")
def result() -> em.MeasuredResult:
    view, history, _, books = built()
    return em.build_measured_exports(view, history, books.files, {COLD: cold_doc(), EV: ev_doc()})


def _file(result, name: str):
    return next(f for f in result.files if f"{f.tenant}.{f.key}.csv" == name)


def test_e1_cold_bill_is_the_room_meter_at_the_declared_grid_tariff(result) -> None:
    assert em.COLD_GRID_PRICE == Decimal(str(m_tenant(COLD)["prices"]["electricity_usd_per_kwh"]))  # parity with M
    rows = _file(result, f"{COLD}.profile.cold-electricity-bill.csv").records
    assert len(rows) == 3 * 4 and {r["clocks"]["recognition_period"] for r in rows} == set(MONTHS)  # whole months
    doc = cold_doc()
    for r in rows:
        kwh = doc["sites"][r["site_code"]][r["clocks"]["recognition_period"]]["room_kwh"]
        assert r["quantity"] == {"value": kwh, "unit": "kWh"}
        assert Decimal(r["amount"]["value"]) == (Decimal(kwh) * Decimal("0.20")).quantize(Decimal("0.01"), "ROUND_HALF_EVEN")
        assert r["body"] == {"account_ref": f"{r['site_code']}-UTIL", "line_type": "USAGE", "tariff_code": "T-GRID-COLD"}
        month = r["clocks"]["recognition_period"]
        assert (r["clocks"]["effective_from"], r["subject"]) == (f"{month}-01", {"kind": "SITE", "ref": r["site_code"]})
    first = tenant(COLD)["sites"][0]["code"]
    july = next(r for r in rows if r["clocks"]["recognition_period"] == "2026-07" and r["site_code"] == first)
    assert july["amount"]["value"] == "300.06" and july["clocks"]["effective_to"] == "2026-08-01"  # 1500.325 x 0.20, half-even


def test_e2_ev_invoice_lines_by_price_class_from_the_schedule(result) -> None:
    rows = _file(result, f"{EV}.profile.ev-utility-invoice.csv").records
    assert all("band" in r["body"] for r in rows)
    emb = {r["body"]["band"]: r for r in rows if r["site_code"] == "EV-EMB" and r["clocks"]["recognition_period"] == "2026-10"}
    assert set(emb) == {"OFFPEAK", "PEAK", "DEMAND"}  # no NIGHT: November is partial, not invoiced
    prices = m_site(EV, "EV-EMB")["tariff"]["prices"]
    assert Decimal(emb["PEAK"]["amount"]["value"]) == (Decimal("20000.375") * Decimal(str(prices["peak"]))).quantize(Decimal("0.01"), "ROUND_HALF_EVEN")
    assert emb["DEMAND"]["quantity"] == {"value": "480.333", "unit": "kW"} and emb["DEMAND"]["body"]["line_type"] == "DEMAND"
    assert Decimal(emb["DEMAND"]["amount"]["value"]) == (Decimal("480.333") * Decimal(str(prices["demand_per_kw_month"]))).quantize(Decimal("0.01"), "ROUND_HALF_EVEN")
    assert {r["body"]["tariff_code"] for r in emb.values()} == {"C-114"}
    kas = [r for r in rows if r["site_code"] == "EV-KAS"]
    assert {r["body"]["band"] for r in kas} == {"FLAT"} and len(kas) == 4  # no demand rate at Kasarani
    flat = Decimal(str(m_site(EV, "EV-KAS")["tariff"]["usd_per_kwh"]))  # D-DD.82: the FLAT price's key in M
    assert all(Decimal(r["amount"]["value"]) == (Decimal("30000.500") * flat).quantize(Decimal("0.01"), "ROUND_HALF_EVEN") for r in kas)


def test_e3_invoice_bands_must_be_the_schedules_classes() -> None:
    view, history, _, books = built()
    doc = ev_doc()
    doc["sites"]["EV-RUI"]["2026-08"]["bands"]["NIGHT"] = "1.000"  # Ruiru's schedule has no night tier
    with pytest.raises(em.MeasuredRefused, match=r"^EMU_MEASURED EV-RUI 2026-08 bands"):
        em.build_measured_exports(view, history, books.files, {EV: doc})


def test_e4_departures_derive_block_met_and_keep_one_id_per_bus_night(result) -> None:
    rows = _file(result, f"{EV}.profile.ev-departures.csv").records
    assert [r["body"]["block_met"] for r in rows] == [True, False]  # 150.000 >= 150.000; 149.999 < 150.000
    assert len({r["source_record_id"] for r in rows}) == 2  # the spare's id is not B01's
    assert rows[0]["clocks"]["occurred_at"] == "2026-11-03T05:00:00+03:00" and rows[0]["body"]["kwh_at_departure"] == "150.000"


def test_e5_a_month_outside_the_fixed_key_set_refuses_at_read() -> None:
    view, history, _, books = built()
    for planted in ("extra", "departures"):
        doc = cold_doc()
        if planted == "extra":
            doc["sites"]["COLD-MWEA"]["2026-07"]["kwh_model"] = "1.000"
        else:
            doc["departures"] = []
        with pytest.raises(em.MeasuredRefused, match=r"^TEL_FOUNDATION"):
            em.build_measured_exports(view, history, books.files, {COLD: doc})


def test_e12_ev_windows_key_set_is_fixed_and_meter_billed_writes_them() -> None:
    """D-DD.158: the EV month's `windows` holds exactly `2200_2400` and `0000_0500` (an absent or extra key refuses
    `TEL_FOUNDATION`); `meter_billed` writes them as `metered` beside the manifest's `kwh_2200_2400`, `kwh_0000_0500`."""
    view, history, _, books = built()
    for planted in ("absent", "extra", "no-windows"):
        doc = ev_doc()
        month = doc["sites"]["EV-EMB"]["2026-08"]
        if planted == "absent":
            del month["windows"]["0000_0500"]
        elif planted == "extra":
            month["windows"]["1800_2200"] = "1.000"
        else:
            del month["windows"]
        with pytest.raises(em.MeasuredRefused, match=r"^TEL_FOUNDATION"):
            em.build_measured_exports(view, history, books.files, {EV: doc})
    out = em.build_measured_exports(view, history, books.files, {EV: ev_doc()})
    rows = json.loads(dict(out.extras)[f"{EV}.meter-billed.json"])["rows"]
    got = {(r["site_code"], r["month"], r["leaf"]): r["metered"] for r in rows if r["leaf"] in ("kwh_2200_2400", "kwh_0000_0500")}
    assert got and all(v == ("11000.125" if leaf == "kwh_2200_2400" else "9000.250") for (_c, _m, leaf), v in got.items())


def test_e6_statements_cold_revenue_from_invoicing_and_ev_without_revenue(result) -> None:
    extras = dict(result.extras)
    cold = json.loads(extras[f"{COLD}.statements.json"])
    invoicing = files_by_name(built()[3])[f"{COLD}.profile.cold-storage-invoicing.csv"].records
    bill = _file(result, f"{COLD}.profile.cold-electricity-bill.csv").records
    assert [s["period"] for s in cold["statements"]] == list(MONTHS)
    for s in cold["statements"]:
        month = s["period"]
        assert Decimal(s["revenue"]) == sum(Decimal(r["amount"]["value"]) for r in invoicing
                                            if r["kind"] == "CHARGE" and r["clocks"]["recognition_period"] == month)
        assert Decimal(s["energy_cost"]) == sum(Decimal(r["amount"]["value"]) for r in bill
                                                if r["clocks"]["recognition_period"] == month)
    ev = json.loads(extras[f"{EV}.statements.json"])
    assert ev["schema"] == "assetops.world-statements/1" and all("revenue" not in s for s in ev["statements"])
    invoice = _file(result, f"{EV}.profile.ev-utility-invoice.csv").records
    oct_cost = sum(Decimal(r["amount"]["value"]) for r in invoice if r["clocks"]["recognition_period"] == "2026-10")
    assert Decimal(next(s for s in ev["statements"] if s["period"] == "2026-10")["energy_cost"]) == oct_cost
    with pytest.raises(em.MeasuredRefused, match="EV_DEPOT only"):
        em.statements(tenant(COLD), "USD", bill, None)


def test_e7_meter_billed_sets_the_manifest_beside_the_meter(result) -> None:
    doc = json.loads(dict(result.extras)[f"{COLD}.meter-billed.json"])
    assert doc["schema"] == "assetops.world-meter-billed/1"
    mwea = {(r["month"], r["leaf"]): r for r in doc["rows"] if r["site_code"] == "COLD-MWEA"}
    assert mwea[("2026-10", "kwh")]["manifest"] == str(m_site(COLD, "COLD-MWEA")["period"]["actual"]["kwh"])
    assert mwea[("2026-10", "kwh")]["metered"] == cold_doc()["sites"]["COLD-MWEA"]["2026-10"]["room_kwh"]
    assert ("2026-10", "energy") in mwea and ("2026-07", "kwh") in mwea
    assert not any(m == "2026-11" for m, _ in mwea)  # no books in November
    ev = json.loads(dict(result.extras)[f"{EV}.meter-billed.json"])
    leaves = {r["leaf"] for r in ev["rows"] if r["site_code"] == "EV-EMB" and r["month"] == "2026-10"}
    assert {"peak_kwh", "offpeak_kwh", "max_kw", "peak_cost", "demand_cost"} <= leaves
    assert all(set(r) == {"site_code", "month", "leaf", "metered", "manifest", "manifest_path"} for r in ev["rows"])


def test_e8_the_cold_bill_profile_reads_its_rows_back(result) -> None:
    from assetops_contracts.native import read_layout as read

    f = _file(result, f"{COLD}.profile.cold-electricity-bill.csv")
    read_back = read(load_profile("cold-electricity-bill-illustrative")[1], f.data, tenant_code="acme",
                     produced_at="2026-11-06T06:00:00+03:00", provenance="source-emulated")
    assert dict(read_back.refused) == {} and read_back.obj["records"] == list(f.records)


def test_e9_a_changed_electricity_price_refuses() -> None:
    view, history, _, books = built()
    changed = copy.deepcopy(view)
    next(t for t in changed["tenants"] if t["tenant"] == COLD)["prices"]["electricity_usd_per_kwh"] = "0.21"
    with pytest.raises(em.MeasuredRefused, match="T-GRID-COLD"):
        em.build_measured_exports(changed, history, books.files, {COLD: cold_doc()})


def _cli(*args: str):
    import subprocess
    import sys

    from .conftest import CLI
    from .books_support import MANIFEST

    return subprocess.run([sys.executable, str(CLI), "exports", "--manifest", str(MANIFEST), *args],
                          capture_output=True, text=True, timeout=600)


def test_e10_exports_telemetry_writes_the_measured_books_after_the_decided(tmp_path) -> None:
    from .test_dd3d_fuel_records_file import LAKE, write_telemetry  # D-DD.168: the mini-grid dips come from readings

    write_telemetry(tmp_path / "tel-lake")
    for slug, doc in ((COLD, cold_doc()), (EV, ev_doc())):
        target = tmp_path / f"tel-{slug}" / slug / "telemetry"
        target.mkdir(parents=True)
        (target / "measured.json").write_text(json.dumps(doc), encoding="utf-8")
    plain, measured = tmp_path / "plain", tmp_path / "measured"
    assert _cli("--out", str(plain / "b"), "--extras", str(plain / "x")).returncode == 0
    done = _cli("--out", str(measured / "b"), "--extras", str(measured / "x"),
                "--telemetry", str(tmp_path / f"tel-{COLD}"), "--telemetry", str(tmp_path / f"tel-{EV}"),
                "--telemetry", str(tmp_path / "tel-lake"))
    assert done.returncode == 0, done.stderr
    before = {p.name: p.read_bytes() for p in (plain / "b").iterdir()}
    after = {p.name: p.read_bytes() for p in (measured / "b").iterdir() if p.is_file()}
    assert [p.name for p in (measured / "b").iterdir() if p.is_dir()] == [LAKE]
    assert {k: v for k, v in after.items() if k in before} == before  # the decided books are unchanged
    assert set(after) - set(before) == {f"{COLD}.profile.cold-electricity-bill.csv", f"{EV}.profile.ev-utility-invoice.csv",
                                        f"{EV}.profile.ev-departures.csv"}
    extras = {p.name for p in (measured / "x").iterdir()}
    assert {f"{COLD}.meter-billed.json", f"{EV}.meter-billed.json", f"{COLD}.statements.json",
            f"{EV}.statements.json"} <= extras
    assert {p.name: p.read_bytes() for p in (plain / "x").iterdir()} == {
        n: (measured / "x" / n).read_bytes() for n in (p.name for p in (plain / "x").iterdir())}  # mini statements


def test_e11_exports_telemetry_refuses_a_tenant_without_its_measured_file(tmp_path) -> None:
    target = tmp_path / "tel" / COLD / "telemetry"
    target.mkdir(parents=True)
    (target / "measured.json").write_text(json.dumps(cold_doc()), encoding="utf-8")
    done = _cli("--out", str(tmp_path / "b"), "--extras", str(tmp_path / "x"), "--telemetry", str(tmp_path / "tel"))
    assert done.returncode == 3 and done.stderr.startswith(f"EMU_MEASURED {EV}"), done.stderr
    assert _cli("--out", str(tmp_path / "b2"), "--extras", str(tmp_path / "x2"), "--tenant", COLD,
                "--telemetry", str(tmp_path / "tel")).returncode == 0  # only the named tenants need their file
