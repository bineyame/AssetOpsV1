"""DD4.4 (D-DD.99, D-DD.123): the measured hooks and `measured.json` per vertical.

Each run class offers `measured_months()` with its vertical's fixed key set (exact values; the frame rounds once, at
writing). The expected figures here are computed independently: the cold room's from the compressor meter's own
5-minute rows, the EV depot's from the depot import by minute with the spec's band hours written as literals (§5.6),
not from the tariff records the hook reads. Mini-grid's `measured.json` stays byte-identical to main's
(`golden/measured_kobo_main.json`, captured from main 0c44ae75b before this change)."""

from __future__ import annotations

import copy
import hashlib
import json
from datetime import timedelta
from fractions import Fraction
from zoneinfo import ZoneInfo

import pytest

from assetops_simulator.world import telemetry as tel
from assetops_simulator.world.tariffs import tariff_schedules

from .books_support import EV, built
from .conftest import HERE
from .test_dd4_telemetry_cold import _run as cold_run
from .test_dd4_telemetry_ev import books, f_site
from .test_telemetry_join_parity import W1_BOOKS, _w1_kobo

ZONE = ZoneInfo("Africa/Nairobi")
KOBO_GOLDEN = json.loads((HERE / "golden" / "measured_kobo_main.json").read_text(encoding="utf-8"))


def _tariffs(code: str) -> list[dict]:
    return [r for r in tariff_schedules(built()[0])[EV]["records"] if r["site_code"] == code]


def _ev(code: str, first: str, last: str):
    from assetops_simulator.world.telemetry_ev import EvSiteRun

    r = EvSiteRun(f_site(code), books(code, tariffs=_tariffs(code)), first, last)
    for _ in r.days:
        r.advance_day()
    return r


def test_m1_cold_room_kwh_is_the_meters_exact_slot_energy_by_local_month() -> None:
    r = cold_run("2026-09-30", "2026-10-01")
    expected: dict[str, Fraction] = {}
    for day in r.days:
        for row in r.day_records(day):
            if row[0] == "compressor-meter":
                month = row[2].astimezone(ZONE).strftime("%Y-%m")
                expected[month] = expected.get(month, Fraction(0)) + row[4] * Fraction((row[3] - row[2]).seconds, 3600)
    months = r.measured_months()
    assert set(months) == {"2026-09", "2026-10"}
    assert all(set(m) == {"room_kwh"} for m in months.values())
    assert {k: v["room_kwh"] for k, v in months.items()} == expected
    assert all(isinstance(v["room_kwh"], Fraction) and v["room_kwh"] > 0 for v in months.values())


@pytest.fixture(scope="module")
def emb():
    return _ev("EV-EMB", "2026-10-31", "2026-11-01")


def _band_literal(local) -> str:
    if 18 <= local.hour < 22:
        return "PEAK"
    if local.date().isoformat() >= "2026-11-01" and local.hour < 5:
        return "NIGHT"
    return "OFFPEAK"


def test_m2_ev_bands_demand_and_import_from_the_depot_meter(emb) -> None:
    bands: dict[str, dict[str, Fraction]] = {}
    windows: dict[tuple[str, object], Fraction] = {}
    for t, kw in emb.import_by_minute().items():
        lt = t.astimezone(ZONE)
        month = lt.strftime("%Y-%m")
        b = bands.setdefault(month, {})
        b[_band_literal(lt)] = b.get(_band_literal(lt), Fraction(0)) + kw / 60
        key = (month, lt.replace(minute=lt.minute - lt.minute % 30))
        windows[key] = windows.get(key, Fraction(0)) + kw
    months = emb.measured_months()
    assert set(months) == {"2026-10", "2026-11"}
    assert set(months["2026-10"]["bands"]) == {"PEAK", "OFFPEAK"}  # the classes of the schedule in force that month
    assert set(months["2026-11"]["bands"]) == {"PEAK", "OFFPEAK", "NIGHT"}
    for month, m in months.items():
        assert set(m) == {"bands", "demand_kw", "import_kwh"}
        assert {k: v for k, v in m["bands"].items() if v} == bands[month]
        assert m["import_kwh"] == sum(m["bands"].values())
        assert m["demand_kw"] == max(v for (mo, _), v in windows.items() if mo == month) / 30
    assert months["2026-11"]["bands"]["NIGHT"] > 0 and months["2026-10"]["bands"]["PEAK"] > 0


def test_m3_ev_bands_refuse_a_minute_no_schedule_prices() -> None:
    from assetops_simulator.world.telemetry_ev import EvSiteRun

    r = EvSiteRun(f_site("EV-RUI"), books("EV-RUI", tariffs=[]), "2026-10-05", "2026-10-05")
    r.advance_day()
    with pytest.raises(tel.TelemetryRefused, match=r"^TEL_BOOKS"):
        r.measured_months()


def test_m4_measured_json_writes_every_vertical_and_departures_only_for_ev(emb) -> None:
    cold = cold_run("2026-09-30", "2026-10-01")
    doc = tel.measured_for("metro-bus", [emb])
    assert set(doc) == {"schema", "tenant", "sites", "departures"} and doc["schema"] == "assetops.world-measured/1"
    nov = doc["sites"]["EV-EMB"]["2026-11"]
    assert nov["partial_to"] == "2026-11-02T00:00:00+03:00" and "partial_to" not in doc["sites"]["EV-EMB"]["2026-10"]
    assert nov["import_kwh"] == tel._decimal(emb.measured_months()["2026-11"]["import_kwh"])
    deps = doc["departures"]
    assert deps and deps == sorted(deps, key=lambda d: (d["site_code"], d["departure_at"], d["vehicle_ref"]))
    assert {frozenset(d) for d in deps} == {frozenset({"site_code", "vehicle_ref", "block_ref", "service_day",
                                                       "departure_at", "required_kwh", "kwh_at_departure"})}
    first = sorted(emb.departures(), key=lambda d: (d["departure_at"], d["vehicle_ref"]))[0]
    assert deps[0]["kwh_at_departure"] == tel._decimal(first["delivered_kwh"])
    assert deps[0]["departure_at"].endswith("+03:00")  # the roster's local instant
    cold_doc = tel.measured_for("harvest-cold", [cold])
    assert "departures" not in cold_doc
    assert cold_doc["sites"][cold.code]["2026-10"]["room_kwh"] == tel._decimal(cold.measured_months()["2026-10"]["room_kwh"])


def test_m5_a_span_ending_inside_november_marks_the_month_partial() -> None:
    r = _ev("EV-KAS", "2026-11-05", "2026-11-06T06:00")
    month = tel.measured_for("metro-bus", [r])["sites"]["EV-KAS"]["2026-11"]
    assert month["partial_to"] == "2026-11-06T06:00:00+03:00"
    assert set(month["bands"]) == {"FLAT"}


def test_m6_mini_grid_measured_bytes_equal_mains() -> None:
    result = tel.build_telemetry({}, {"sites": [_w1_kobo()]}, {"KOBO-001": copy.deepcopy(W1_BOOKS)},
                                 start="2026-07-01", end="2026-07-07")
    found = {p: hashlib.sha256(b).hexdigest() for p, b in result.files}
    assert found == KOBO_GOLDEN["files"]
    assert "lakeside-power/telemetry/measured.json" in found


def test_m7_span_end_is_the_local_end_instant_for_every_run(emb) -> None:
    cold = cold_run("2026-09-30", "2026-10-01")
    assert emb.end_local == (emb.end).astimezone(ZONE) and cold.end_local.utcoffset() == timedelta(hours=3)
