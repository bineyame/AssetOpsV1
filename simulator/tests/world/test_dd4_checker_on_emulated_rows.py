"""DD4.4 (spec §8.1; D-DD.55, D-DD.124): C-DD5, C-DD6's EV clauses, C-DD7 and C-DD20 judged on the writer's own rows.

Local days are run through the frame (`build_telemetry`): Kasarani 1-2 Nov (CH-K2's fault), Ruiru on 6 Oct
(CH-R7 c2's fault; PEAK, OFFPEAK and DEMAND) and Mwea on 1 Oct. Their books are `exports_measured`'s rows over the same
run's `measured.json`, with the day's `partial_to` taken off so the one-day month is written (the rule the books follow is
the whole-month rule's; only the span is short). C-DD20 reads the books of the committed `measured.json` fixtures.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta

import pytest

from assetops_simulator.world import exports_measured as em
from assetops_simulator.world import telemetry as tel
from assetops_simulator.world.tariffs import tariff_schedules
from assetops_simulator.world.telemetry_cold import cold_books_for

from .books_support import COLD, EV, built, emulated_files
from .conftest import REPOSITORY_ROOT
from .test_dd4_ev_join import _decided, _sites
from .test_dd4_thika_incident import _dd_check

URL = "postgresql+psycopg://u:p@dd.invalid:1/x_test"


def _whole(document: dict) -> dict:
    for months in document["sites"].values():
        for month in months.values():
            month.pop("partial_to", None)
    return document


def _ev_days(code: str, first: str, last: str):
    result = tel.build_telemetry({}, _sites(), {code: _decided(code)}, start=first, end=last, only=(code,))
    rows = [r for name, data in result.files if name.startswith(f"{EV}/telemetry/{code}.")
            for r in json.loads(data)["readings"]]
    return rows, _whole(json.loads(dict(result.files)[f"{EV}/telemetry/measured.json"]))


@pytest.fixture(scope="module")
def kasarani():
    return _ev_days("EV-KAS", "2026-11-01", "2026-11-02")  # the 1 Nov bus-night departs on 2 Nov


@pytest.fixture(scope="module")
def ruiru():
    return _ev_days("EV-RUI", "2026-10-06", "2026-10-06")


@pytest.fixture(scope="module")
def mwea():
    view, history, records, _ = built()
    onboarding = json.loads((REPOSITORY_ROOT / "backend/tests/fixtures/on1/harvest-cold.onboarding.json").read_text())
    bindings = {"COLD-MWEA": json.loads((REPOSITORY_ROOT / "backend/conversions/world/COLD-MWEA-bindings.json").read_text())}
    sites = tel.site_inputs(onboarding, bindings)
    books = cold_books_for(view, history, records)
    result = tel.build_telemetry({}, sites, books, start="2026-10-01", end="2026-10-01", only=("COLD-MWEA",))
    files = dict(result.files)
    rows = json.loads(files[f"{COLD}/telemetry/COLD-MWEA.2026-10-01.readings.json"])["readings"]
    return rows, _whole(json.loads(files[f"{COLD}/telemetry/measured.json"]))


def _tenant(slug: str) -> dict:
    return next(t for t in built()[0]["tenants"] if t["tenant"] == slug)


def _ev_books(code: str, document: dict) -> list[dict]:
    schedules = [r for r in tariff_schedules(built()[0])[EV]["records"] if r["site_code"] == code]
    invoice = em.ev_invoice_rows(document, schedules, built()[0]["currency"])
    departures = em.departure_rows(document)
    nights = {(r["body"]["vehicle_ref"], r["body"]["service_day"]) for r in departures}
    roster = [r for r in emulated_files()[f"{EV}.profile.ev-fleet-roster.csv"].records
              if r["site_code"] == code and (r["body"]["vehicle_ref"], r["clocks"]["effective_from"]) in nights]
    return invoice + departures + roster + schedules


def _span(day: str, days: int = 1):
    start = datetime.fromisoformat(f"{day}T00:00:00+03:00")
    return start, start + timedelta(days=days)


def test_c5_on_the_writers_rows(kasarani, ruiru, mwea) -> None:
    dd_check = _dd_check()
    for code, (rows, _doc), day, days in (("EV-KAS", kasarani, "2026-11-01", 2), ("EV-RUI", ruiru, "2026-10-06", 1),
                                          ("COLD-MWEA", mwea, "2026-10-01", 1)):
        result = dd_check.judge_cadence({code: rows}, {code: "SIMULATED"}, (code,), *_span(day, days), {})
        assert result.passed, (code, result.detail[:5])
        gap = [r for r in rows if not r["start"].startswith(f"{day}T12:")]  # an hour of readings lost
        assert any("gap" in d for d in dd_check.judge_cadence({code: gap}, {code: "SIMULATED"}, (code,),
                                                               *_span(day, days), {}).detail)


def test_c6_ev_clauses_on_the_writers_rows(kasarani, ruiru) -> None:
    dd_check = _dd_check()
    readings = {"EV-KAS": kasarani[0], "EV-RUI": ruiru[0]}
    result = dd_check.judge_failures_at_instant(readings, sites=("EV-KAS", "EV-RUI"))
    assert result.passed, result.detail
    late = {"EV-KAS": [dict(r, start=r["start"].replace("T23:40", "T23:45")) if r["signal_id"] == "fault-event" else r
                       for r in kasarani[0]], "EV-RUI": ruiru[0]}
    assert not dd_check.judge_failures_at_instant(late, sites=("EV-KAS", "EV-RUI")).passed


def test_c7_on_the_writers_rows(kasarani, ruiru, mwea) -> None:
    dd_check = _dd_check()
    readings = {"EV-KAS": kasarani[0], "EV-RUI": ruiru[0], "COLD-MWEA": mwea[0]}
    rows = _ev_books("EV-KAS", kasarani[1]) + _ev_books("EV-RUI", ruiru[1])
    rows += em.cold_bill_rows({**_tenant(COLD), "sites": [s for s in _tenant(COLD)["sites"] if s["code"] == "COLD-MWEA"]},
                              mwea[1], built()[0]["currency"])
    assert {r["body"].get("band") for r in rows if r["kind"] == "CHARGE" and r["site_code"] == "EV-RUI"} == {
        "PEAK", "OFFPEAK", "DEMAND"}
    assert any(r["kind"] == "DEPARTURE" and not r["body"]["block_met"] for r in rows)  # Kasarani's short buses
    sites = ("EV-KAS", "EV-RUI", "COLD-MWEA")
    result = dd_check.judge_meter_books({}, readings, rows, sites)
    assert result.passed, result.detail[:5]
    demand = next(r for r in rows if r["site_code"] == "EV-RUI" and r["body"].get("band") == "DEMAND")
    demand["quantity"]["value"] = str(float(demand["quantity"]["value"]) + 0.001)
    assert not dd_check.judge_meter_books({}, readings, rows, sites).passed


def test_c20_on_the_measured_books_of_the_plant_fixtures() -> None:
    dd_check = _dd_check()
    files = emulated_files()
    rows = list(files[f"{COLD}.profile.cold-electricity-bill.csv"].records)
    rows += files[f"{EV}.profile.ev-utility-invoice.csv"].records
    crate_days = dd_check.crate_days_of(dd_check.read_inputs(URL))
    result = dd_check.judge_story_directions(rows, crate_days)
    assert result.passed, result.detail
    assert [p.split()[0] for p in result.pending] == ["KISIWA-001", "MTO-001"]
