"""DD4.3 (spec §4.5; D-DD.81 protocol, D-DD.87 EV clause; `DD4b-preflight.md` Q1-Q15): the EV depot writer,
tested directly on its day-level protocol before the join."""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from fractions import Fraction
from functools import lru_cache
from zoneinfo import ZoneInfo

import pytest

from assetops_simulator.packs.ev_charger import (DEFAULT_PARAMETERS, EvChargerPack, EvForcingRow, EvState,
                                                 PhysicallyUnacceptable)
from assetops_simulator.world import telemetry_ev
from assetops_simulator.world.telemetry_ev import EvSiteRun

from .books_support import EV, built, files_by_name, m_site
from .conftest import REPOSITORY_ROOT

ZONE = ZoneInfo("Africa/Nairobi")
UTC = timezone.utc


@lru_cache(maxsize=None)
def f_site(code: str) -> dict:
    onboarding = json.loads((REPOSITORY_ROOT / "backend/tests/fixtures/on1/metro-bus.onboarding.json").read_text())
    s = next(s for s in onboarding["sites"] if s["code"] == code)
    return {"code": code, "timezone": s["timezone"], "foundation": {"components": s["components"]}}


def roster(code: str) -> list[dict]:
    rows = files_by_name(built()[3])[f"{EV}.profile.ev-fleet-roster.csv"].records
    return [r for r in rows if r["site_code"] == code]


def books(code: str, **extra) -> dict:
    out = {"roster": roster(code), "practice": telemetry_ev.PRACTICE if code == "EV-EMB" else {}, "faults": [],
           "clock": []}
    out.update(extra)
    return out


def run(code: str, first: str, last: str, **extra) -> EvSiteRun:
    r = EvSiteRun(f_site(code), books(code, **extra), first, last)
    for _ in r.days:
        r.advance_day()
    return r


def local(text: str) -> datetime:
    return datetime.fromisoformat(text).replace(tzinfo=ZONE).astimezone(UTC)


def rows_of(r: EvSiteRun, device: str | None = None, signal: str | None = None) -> list[tuple]:
    out = [row for day in r.days for row in r.day_records(day)]
    return [row for row in out if (device is None or row[0] == device) and (signal is None or row[1] == signal)]


# --- the pack (pre-flight Q1) ---------------------------------------------------------------------------------------

def test_e1_the_world_pack_admits_sessions_past_two_in_order_and_v1_still_refuses_a_third() -> None:
    t = datetime(2026, 10, 6, 8, 0, tzinfo=UTC)
    state = EvState.initial(t)
    world = EvChargerPack(DEFAULT_PARAMETERS, scenario_sha256="0" * 64, max_plugs=None)
    v1 = EvChargerPack(DEFAULT_PARAMETERS, scenario_sha256="0" * 64)
    for pack in (world, v1):
        s = state
        ordinal = 0
        for n, conn in ((1, "c1"), (2, "c2")):
            s = pack.step(s, (EvForcingRow(s.minute, "PLUG", conn, f"session-{n}"),), ordinals=(ordinal,)).after
            ordinal += 1
            s = pack.step(s, (EvForcingRow(s.minute, "UNPLUG", conn, "END"),), ordinals=(ordinal,)).after
            ordinal += 1
        third = (EvForcingRow(s.minute, "PLUG", "c1", "session-3"),)
        if pack is v1:
            with pytest.raises(PhysicallyUnacceptable):
                pack.step(s, third, ordinals=(ordinal,))
        else:
            after = pack.step(s, third, ordinals=(ordinal,)).after
            assert after.connector("c1").state == "PLUGGED" and after.plugs == 3
            with pytest.raises(PhysicallyUnacceptable):  # order and no reuse still hold
                pack.step(after, (EvForcingRow(after.minute, "PLUG", "c2", "session-3"),), ordinals=(ordinal + 1,))


# --- roster in, the depot manager --------------------------------------------------------------------------------

def test_e2_kasarani_every_bus_gets_its_required_energy_inside_the_limits() -> None:
    r = run("EV-KAS", "2026-10-14", "2026-10-15")
    night = [d for d in r.departures() if d["service_day"] == "2026-10-14"]
    assert len(night) == 8 and all(d["delivered_kwh"] == Fraction(150) for d in night)
    for minute, depot in r.import_by_minute().items():
        assert depot <= 250
    for (charger, minute), kw in r.charger_draw().items():
        assert kw <= 50, (charger, minute)
    imports = rows_of(r, "site-meter", "import")
    assert imports and all(row[5] == "kW" for row in imports)


def test_e3_embakasi_practice_first_by_return_plug_on_arrival_the_rest_at_22() -> None:
    r = run("EV-EMB", "2026-07-15", "2026-07-15")
    plugs = sorted(r.plug_ins("2026-07-15"))  # (plug-in instant, bus) of the night
    on_arrival = round(Fraction(20) * Fraction(telemetry_ev.PRACTICE["2026-07"]))  # 7.2 -> 7
    late = [p for p in plugs if p[0] == local("2026-07-15T22:00:00")]
    assert len(plugs) == 20 and len(late) == 20 - on_arrival == 13
    early = [p for p in plugs if p[0] < local("2026-07-15T22:00:00")]
    returns = {row["body"]["vehicle_ref"]: row["body"]["return_at"] for row in roster("EV-EMB")
               if row["clocks"]["effective_from"] == "2026-07-15"}
    assert sorted(b for _, b in early) == sorted(sorted(returns, key=lambda b: (returns[b], b))[:on_arrival])
    assert all(at == datetime.fromisoformat(returns[b]).astimezone(UTC) for at, b in early)


def test_e4_lowest_declared_connector_and_charger_order() -> None:
    r = run("EV-RUI", "2026-07-02", "2026-07-02")
    assign = sorted(r.assignments("2026-07-02"))  # (plug-in instant, bus, connector asset)
    assert [a[2] for a in assign][:14] == [f"ch-r{1 + k // 2}-c{1 + k % 2}" for k in range(14)]


# --- faults (pre-flight Q7) ----------------------------------------------------------------------------------------

def test_e5_kasarani_ch_k2_faults_both_connectors_at_23_40_and_the_aborted_buses_wait() -> None:
    fault = {"asset": "ch-k2", "at": "2026-11-01T23:40:00+03:00", "source": "M tenants.metro-bus.sites.EV-KAS.incident"}
    r = run("EV-KAS", "2026-11-01", "2026-11-02", faults=[fault])
    at = datetime.fromisoformat(fault["at"]).astimezone(UTC)
    for c in ("ch-k2-c1", "ch-k2-c2"):
        events = [row for row in rows_of(r, c) if row[1] in ("fault-event", "session-event") and row[2] == at]
        assert sorted(row[4].split()[0] for row in events) == ["EV_CONNECTOR_FAULT", "EV_SESSION_ABORT"]
        later = [row for row in rows_of(r, c, "state") if row[2] > at]
        assert later and {row[4] for row in later} == {"FAULTED"}
    assert any(c["condition"] == "fault" and c["value"].startswith("ch-k2") for c in r.conditions())


def test_e6_ruiru_ch_r7_c2_faults_at_00_00_and_no_departure_is_short() -> None:
    fault = {"asset": "ch-r7-c2", "at": "2026-10-06T00:00:00+03:00", "source": "M tenants.metro-bus.sites.EV-RUI.incident"}
    r = run("EV-RUI", "2026-10-05", "2026-10-07", faults=[fault])
    night = [d for d in r.departures() if d["service_day"] in ("2026-10-05", "2026-10-06")]
    assert len(night) == 28 and all(d["delivered_kwh"] == Fraction(140) for d in night)
    assert {row[4] for row in rows_of(r, "ch-r7-c2", "state")
            if row[2] > datetime.fromisoformat(fault["at"]).astimezone(UTC)} == {"FAULTED"}


# --- CLOCK-1 (pre-flight Q12) --------------------------------------------------------------------------------------

def test_e7_clock_1_shifts_the_third_chargers_session_rows_by_four_minutes_only() -> None:
    clock = [{"charger": 3, "day": "2026-10-15", "minutes": 4, "source": "M disorder_tests CLOCK-1"}]
    plain = run("EV-EMB", "2026-10-15", "2026-10-15")
    shifted = run("EV-EMB", "2026-10-15", "2026-10-15", clock=clock)
    day = date(2026, 10, 15)
    a, b = plain.day_records(day), shifted.day_records(day)
    assert [row for row in a if not row[0].startswith("ch-e3-")] == [row for row in b if not row[0].startswith("ch-e3-")]
    a3 = [row for row in a if row[0].startswith("ch-e3-")]
    b3 = sorted((row for row in b if row[0].startswith("ch-e3-")), key=lambda row: (row[2], row[3], row[0], row[1]))
    assert len(a3) == len(b3) and a3
    four = timedelta(minutes=4)
    pairs = {(row[0], row[1], row[4], row[5]) for row in b3}
    assert pairs == {(row[0], row[1], row[4], row[5]) for row in a3}
    shifted_rows = set(b3) - set(a3)
    assert shifted_rows and all((row[0], row[1], row[2] - four, row[3] - four, row[4], row[5]) in set(a3)
                                for row in shifted_rows)
    assert any(c["condition"] == "CLOCK-1" for c in shifted.conditions())


# --- the protocol and refusals --------------------------------------------------------------------------------------

def test_e8_protocol_days_chain_and_refusals_carry_their_code() -> None:
    r = EvSiteRun(f_site("EV-KAS"), books("EV-KAS"), "2026-10-14", "2026-10-15")
    with pytest.raises(ValueError, match=r"^TEL_EVENT_UNPLACED "):
        r.day_records(date(2026, 10, 14))
    r.advance_day()
    r.advance_day()
    with pytest.raises(ValueError, match=r"^TEL_EVENT_UNPLACED "):
        r.advance_day()
    # the 14 Oct night's sessions cross midnight into the 15th's file
    assert any(row[1] == "session-event" and row[4].startswith("EV_SESSION_END") for row in r.day_records(date(2026, 10, 15)))
    site = json.loads(json.dumps(f_site("EV-KAS")))
    for c in site["foundation"]["components"]:
        c["properties"] = [p for p in c.get("properties", []) if p["property_key"] != "ev-site-import-limit"]
    with pytest.raises(ValueError, match=r"^TEL_FOUNDATION "):
        EvSiteRun(site, books("EV-KAS"), "2026-10-14", "2026-10-15")
    with pytest.raises(ValueError, match=r"^TEL_EVENT_UNPLACED "):
        EvSiteRun(f_site("EV-KAS"), books("EV-KAS", faults=[{"asset": "ch-k2", "at": "2026-12-01T00:00:00+03:00",
                                                                "source": "test"}]), "2026-10-14", "2026-10-15")
    assert r.private_parameters()["model"] == "ev-charger/1 (max_plugs None)"


def test_e9_initial_state_no_bus_before_its_first_return() -> None:
    r = run("EV-RUI", "2026-07-01", "2026-07-01")
    morning = [row for row in rows_of(r, signal="state") if row[2] < local("2026-07-01T21:00:00")]
    assert morning and {row[4] for row in morning} == {"UNPLUGGED"}


def test_e10_energy_denominators_stay_bounded_over_seven_days() -> None:
    """D-DD.87's EV clause: denominators divide 3000 (1 kW quanta or need x 60 on milli-kWh needs)."""
    r = run("EV-KAS", "2026-10-01", "2026-10-07")
    values = [Fraction(row[4]) for row in rows_of(r) if row[5] in ("kWh",)]
    assert values and all(3000 % v.denominator == 0 for v in values)
    assert all(3000 % d["delivered_kwh"].denominator == 0 for d in r.departures())


def test_e11_practice_table_parity_with_the_manifest() -> None:
    emb = m_site(EV, "EV-EMB")
    assert Fraction(str(emb["period"]["actual"]["peak_share"])) == Fraction(telemetry_ev.PRACTICE["2026-10"])
    assert telemetry_ev.PRACTICE["2026-11"] == telemetry_ev.PRACTICE["2026-10"]
    family = (REPOSITORY_ROOT / "Docs/demo-sprint/product-direction-layer4/demo-site-scenario-manifest.yaml").read_text()
    lines = family.splitlines()
    line = lines[next(i for i, ln in enumerate(lines) if ln.strip() == "metro-bus/Embakasi:") + 1]
    assert line.split("peak_kwh: share kwh")[1].split(",")[0].split() == [
        telemetry_ev.PRACTICE[m] for m in ("2026-07", "2026-08", "2026-09")]
