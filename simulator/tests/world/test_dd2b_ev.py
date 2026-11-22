"""DD2.4 (spec `specs/DD-demo-data/spec.md` §4.5, §5.3; D-DD.49, D-DD.51, D-DD.52): the EV depot decided books."""

from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest

from assetops_contracts.native import LAYOUTS, read_layout
from assetops_simulator.world import exports_ev
from assetops_simulator.world.profile_csv import load_profile

from .books_support import EV, build, built, files_by_name, m_site, tenant_view
from .conftest import REPOSITORY_ROOT

SITES = {"EV-EMB": (20, 140), "EV-KAS": (8, 150), "EV-RUI": (14, 140)}
MONTHS = {"2026-07": 31, "2026-08": 31, "2026-09": 30, "2026-10": 31}


def rows(name: str) -> list[dict]:
    return list(files_by_name(built()[3])[f"{EV}.{name}.csv"].records)


def actual_kwh(month: str, code: str) -> int:
    view, history = built()[0], built()[1]
    site = next(s for s in tenant_view(view, EV)["sites"] if s["code"] == code)
    if month == view["accounting_period"]:
        return site["period"]["actual"]["kwh"]
    return history["tenants"][EV][site["site"]][month]["actual"]["kwh"]


def test_v1_files_and_profiles_round_trip() -> None:
    names = sorted(n for n in files_by_name(built()[3]) if n.startswith(f"{EV}."))
    assert names == [f"{EV}.expenses.csv", f"{EV}.profile.ev-budget.csv", f"{EV}.profile.ev-fleet-roster.csv",
                     f"{EV}.profile.ev-service-tickets.csv"]
    for f in built()[3].files:
        if f.tenant != EV:
            continue
        layout = LAYOUTS[f.layout_id] if f.layout_id in LAYOUTS else load_profile(f.layout_id)[1]
        read = read_layout(layout, f.data, tenant_code=EV, produced_at="2026-11-06T06:00:00+03:00",
                           provenance="source-emulated")
        assert dict(read.refused) == {}, f.key
        assert read.obj["records"] == list(f.records), f.key


def test_v2_roster_one_row_per_bus_night_july_to_october() -> None:
    roster = rows("profile.ev-fleet-roster")
    count = Counter((r["site_code"], r["clocks"]["effective_from"][:7]) for r in roster)
    assert count == {(code, month): buses * days for code, (buses, _) in SITES.items()
                     for month, days in MONTHS.items()}
    for code in SITES:
        for month in MONTHS:
            total = sum(Decimal(r["body"]["required_kwh"]) for r in roster
                        if r["site_code"] == code and r["clocks"]["effective_from"][:7] == month)
            assert total == actual_kwh(month, code), (code, month)
    assert {r["body"]["required_kwh"] for r in roster if r["site_code"] == "EV-KAS"} == {"150.000"}
    assert len({(r["site_code"], r["clocks"]["effective_from"], r["subject"]["ref"]) for r in roster}) == len(roster)


def test_v3_roster_times() -> None:
    roster = rows("profile.ev-fleet-roster")
    night = [r for r in roster if r["clocks"]["effective_from"] == "2026-10-15"]
    emb = sorted((r for r in night if r["site_code"] == "EV-EMB"), key=lambda r: r["subject"]["ref"])
    returns = [r["body"]["return_at"][11:16] for r in emb]
    assert returns[0] == "17:30" and returns[-1] == "19:30" and returns == sorted(returns) and len(set(returns)) == 20
    assert returns[1] == "17:36" and returns[2] == "17:43"  # 120/19 = 6.32 and 12.63 minutes, half to even
    assert {r["body"]["departure_at"] for r in emb} == {"2026-10-16T05:30:00+03:00"}
    for code, back, leaves in (("EV-KAS", "2026-10-15T22:00:00+03:00", "2026-10-16T05:00:00+03:00"),
                               ("EV-RUI", "2026-10-15T21:00:00+03:00", "2026-10-16T05:00:00+03:00")):
        assert {(r["body"]["return_at"], r["body"]["departure_at"]) for r in night if r["site_code"] == code} == {
            (back, leaves)}


def test_v4_one_roster_writer() -> None:
    """D-DD.52: DD4.3 widens `roster_rows`' nights; no second module writes FLEET_ROSTER."""
    package = REPOSITORY_ROOT / "simulator" / "assetops_simulator"
    writers = [p.relative_to(package).as_posix() for p in package.rglob("*.py")
               if '"FLEET_ROSTER"' in p.read_text(encoding="utf-8")]
    assert writers == ["world/exports_ev.py"]
    view = built()[0]
    from assetops_simulator.world.books import site_months
    october = next(m for m in site_months(view, built()[1], tenant_view(view, EV))
                   if m.code == "EV-KAS" and m.month == "2026-10")
    wider = exports_ev.roster_rows(october, datetime.now().astimezone().tzinfo,
                                   [date(2026, 11, 1) + timedelta(days=k) for k in range(6)])
    assert len(wider) == 8 * 6 and wider[0]["clocks"]["effective_from"] == "2026-11-01"


def test_v5_tickets_from_the_incident_blocks() -> None:
    tickets = rows("profile.ev-service-tickets")
    assert [(r["site_code"], r["subject"]["ref"], r["clocks"]["occurred_at"], r["status"]) for r in tickets] == [
        ("EV-KAS", "CH-K2", "2026-11-01T23:40:00+03:00", "OPEN"), ("EV-RUI", "CH-R7", "2026-10-06T00:00:00+03:00", "OPEN")]
    assert all("acknowledged_at" not in r["body"] and r["body"]["counterparty_ref"] == "oem-contractor"
               for r in tickets)
    # D-DD.51 parity: the table equals the manifest's incident blocks
    kas, rui = m_site(EV, "EV-KAS"), m_site(EV, "EV-RUI")
    assert kas["incident"]["asset"] == "CH-K2"
    assert datetime.fromisoformat(kas["incident"]["fault"]["at"]) == datetime.fromisoformat(exports_ev.TICKETS[0][2])
    assert rui["incident"]["asset"].startswith("CH-R7 ")
    assert rui["observations"]["october"]["charger_out_from"] == exports_ev.TICKETS[1][2][:10]
    assert exports_ev.TICKETS[1][2][10:] == "T00:00:00+03:00"
    assert "acknowledged" not in str(kas["incident"]).lower()  # the ACKNOWLEDGED event is the claim's


def test_v6_budget_lines_and_unwritten_plan_fields() -> None:
    books = built()[3]
    budget = files_by_name(books)[f"{EV}.profile.ev-budget.csv"].records
    by: dict = {}
    for r in budget:
        by.setdefault((r["site_code"], r["clocks"]["recognition_period"]), []).append(r["body"]["factor_id"])
    assert by[("EV-EMB", "2026-07")] == ["peak_kwh", "max_kw", "maintenance"]
    assert by[("EV-KAS", "2026-07")] == ["maintenance"]
    assert by[("EV-RUI", "2026-07")] == ["maintenance", "energy_cost", "departures_required"]
    assert by[("EV-EMB", "2026-10")] == ["peak_kwh", "max_kw", "maintenance", "energy_cost", "departures_required"]
    cost = next(r for r in budget if r["source_record_id"] == "gen:EV-RUI:2026-07:plan:energy_cost")
    assert cost["body"] == {"factor_id": "energy_cost", "value": "12600.00", "version_ref": "budget-2026-v1",
                            "line_ref": "energy_cost", "currency": "USD"}
    plan = {(r[1], r[2], r[4]): r[5] for r in books.unwritten if r[0] == EV and r[3] == "plan"}
    assert plan[("EV-RUI", "2026-07", "total")] == "NOT_READ_BY_A_LEAF"
    assert plan[("EV-EMB", "2026-07", "kwh")] == "NOT_OWN_LINE"
    assert plan[("EV-EMB", "2026-07", "offpeak_kwh")] == "NOT_OWN_LINE"
    assert ("EV-RUI", "2026-07", "energy_cost") not in plan and ("EV-RUI", "2026-07", "departures_required") not in plan


def test_v7_missing_kwh_is_listed_never_zero() -> None:
    def drop(history: dict) -> None:
        del history["tenants"][EV]["Ruiru"]["2026-08"]["actual"]["kwh"]

    books = build(None, drop)[3]
    assert (EV, "EV-RUI", "2026-08", "actual", "kwh", "NOT_IN_HISTORY") in books.unwritten
    roster = files_by_name(books)[f"{EV}.profile.ev-fleet-roster.csv"].records
    assert not [r for r in roster if r["site_code"] == "EV-RUI" and r["clocks"]["effective_from"][:7] == "2026-08"]


def test_v8_no_penalty_row_and_estimated_maintenance_absent() -> None:
    books = built()[3]
    expenses = files_by_name(books)[f"{EV}.expenses.csv"].records
    assert {r["body"]["category"] for r in expenses} == {"OM"}
    assert not [r for r in expenses if r["site_code"] == "EV-KAS" and r["clocks"]["recognition_period"] == "2026-10"]
    assert (EV, "EV-KAS", "2026-10", "actual", "maintenance", "ESTIMATED_NOT_RECEIVED") in books.unwritten
