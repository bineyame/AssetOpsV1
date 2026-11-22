"""DD4.2 (D-DD.81, D-DD.83, D-DD.85, D-DD.86): `ColdSiteRun` on the day-level protocol, tested directly before the
join with DD3a's frame. Refusals are asserted by their `TEL_*` first word."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from fractions import Fraction

import pytest

from assetops_simulator.packs.cold import DEFAULT_PROPERTY_VALUES, PROPERTY_FIELDS
from assetops_simulator.world.telemetry import TelemetryRefused
from assetops_simulator.world.telemetry_cold import ColdSiteRun

NAIROBI = timezone(timedelta(hours=3))
UTC = timezone.utc


def _site(**drop) -> dict:
    values = dict(DEFAULT_PROPERTY_VALUES, **{"cold-cooling-capacity": "6"})
    props = [{"property_key": k, "value": v, "unit": PROPERTY_FIELDS[k][1]} for k, v in values.items() if k not in drop]
    return {"code": "COLD-T", "timezone": "Africa/Nairobi",
            "foundation": {"components": [{"id": "room-1", "type": "COLD_ROOM", "properties": props}]}}


def _move(at: str, direction: str, n: int, ref: str = "B1") -> dict:
    return {"site_code": "COLD-T", "clocks": {"occurred_at": at}, "quantity": {"value": str(n), "unit": "crate"},
            "body": {"batch_ref": ref, "direction": direction}}


def _books(**extra) -> dict:
    books = {
        "ledger": [_move("2026-09-29T08:00:00+03:00", "IN", 40), _move("2026-09-30T16:00:00+03:00", "IN", 40, "B2"),
                   _move("2026-09-30T16:00:00+03:00", "OUT", 10)],
        "cooling": {"season": {"cool_dry": "0.97", "short_rains": "1.00", "warm_dry": "1.02"},
                    "day": {"SA": "1.00", "SU": "1.00", "WD": "1.00"}, "jitter": "0.01"},
        "seasons": {"2026-09": "warm_dry", "2026-10": "short_rains"},
        "day_classes": {"SA": [6], "SU": [7], "WD": [1, 2, 3, 4, 5]},
        "efficiency": {"2026-09": "117/100", "2026-10": "500/403"},
    }
    return books | extra


def _run(first="2026-09-29", last="2026-10-01", **extra) -> ColdSiteRun:
    run = ColdSiteRun(_site(), _books(**extra), first, last)
    for _ in run.days:
        run.advance_day()
    return run


def _local(at: datetime) -> str:
    return at.astimezone(NAIROBI).isoformat()[:16]


def test_ambient_and_efficiency_forcings_at_local_midnights():
    run = _run()
    ambient = [(_local(r[2]), r[4]) for d in run.days for r in run.day_records(d) if r[0] == "ambient-probe"]
    assert ambient[0] == ("2026-09-29T00:00", Fraction("24.8"))  # the first day's ambient from the initial state
    assert ("2026-09-30T23:55", Fraction("24.8")) in ambient and ("2026-10-01T00:00", Fraction(24)) in ambient
    rows = {(_local(f.at), f.kind, f.value) for fs in run.forcings.values() for f in fs
            if f.kind in ("AMBIENT", "EFFICIENCY")}
    assert rows == {("2026-09-29T00:00", "EFFICIENCY", "117/100"), ("2026-09-30T00:00", "AMBIENT", "24.8"),
                    ("2026-10-01T00:00", "AMBIENT", "24"), ("2026-10-01T00:00", "EFFICIENCY", "500/403")}
    assert run.private_parameters()["efficiency"] == {"2026-09": "117/100", "2026-10": "500/403"}


def test_crates_and_one_door_cycle_per_movement_instant():
    run = _run()
    kinds = sorted((_local(f.at), f.kind, f.value) for fs in run.forcings.values() for f in fs
                   if f.kind.startswith(("CRATES", "DOOR")))
    assert kinds == [("2026-09-29T08:00", "CRATES_IN", "40"), ("2026-09-29T08:00", "DOOR_OPEN", "OPEN"),
                     ("2026-09-29T08:05", "DOOR_CLOSE", "CLOSED"), ("2026-09-30T16:00", "CRATES_IN", "40"),
                     ("2026-09-30T16:00", "CRATES_OUT", "10"), ("2026-09-30T16:00", "DOOR_OPEN", "OPEN"),
                     ("2026-09-30T16:05", "DOOR_CLOSE", "CLOSED")]
    assert run.state.crates == 70


def test_days_chain_and_every_day_has_its_readings():
    run = _run()
    for d in run.days:
        rows = run.day_records(d)
        start = datetime.combine(d, datetime.min.time(), tzinfo=NAIROBI)
        chamber = [r for r in rows if r[0] == "chamber-probe"]
        meter = [r for r in rows if r[0] == "compressor-meter"]
        assert len(chamber) == 288 and len(meter) == 288
        assert all(start <= r[2] < start + timedelta(days=1) for r in rows)
        assert all(r[3] - r[2] == timedelta(minutes=5) for r in meter)
        assert all(r[4] >= 1 for r in meter)  # auxiliary on a powered bus
    prq = run.private_parameters()
    assert prq["temperature_quantum"] == "1/1000000" and set(prq["rounding_total_kwh"]) == {"2026-09", "2026-10"}


def test_thika_sequence_is_native():
    events = [{"kind": "GRID_LOSS", "at": "2026-09-30T19:11:00+03:00", "source": "incident.backup"},
              {"kind": "GENERATOR_FAILURE", "at": "2026-09-30T19:11:00+03:00", "source": "incident.backup"},
              {"kind": "GENERATOR_HAND_START", "at": "2026-09-30T19:14:00+03:00", "source": "incident.backup"},
              {"kind": "GRID_RESTORE", "at": "2026-09-30T22:00:00+03:00", "source": "Assumed"}]
    run = _run(events=events)
    rows = run.day_records(date(2026, 9, 30))
    gen = [(_local(r[2]), r[4], r[5], r[6]["record_kind"], r[6]["outcome"], r[6]["actor"], r[6]["ordinal"])
           for r in rows if r[1] == "start-event"]  # D-DD.91: value None, unit event, the v4 fields
    assert gen == [("2026-09-30T19:11", None, "event", "START_REQUEST", "REQUESTED", "CONTROLLER", 1),
                   ("2026-09-30T19:11", None, "event", "START_RESULT", "FAILED", "CONTROLLER", 2),
                   ("2026-09-30T19:14", None, "event", "START_RESULT", "SUCCEEDED", "OPERATOR", 3)]
    bus = [(_local(r[2]), r[4]) for r in rows if r[0] == "backup-bus-meter" and "19:1" in _local(r[2])]
    assert ("2026-09-30T19:11", "UNPOWERED") in bus and ("2026-09-30T19:15", "POWERED") in bus
    assert {c["condition"] for c in run.conditions()} >= {"GRID_LOSS", "GENERATOR_HAND_START", "GRID_RESTORE"}


@pytest.mark.parametrize("make, code", [
    (lambda: ColdSiteRun(_site(**{"cold-heat-leak": 1}), _books(), "2026-09-29", "2026-09-30"), "TEL_FOUNDATION"),
    (lambda: ColdSiteRun(_site(), _books(), "2026-08-31", "2026-09-30"), "TEL_FOUNDATION"),  # no August season
    (lambda: ColdSiteRun(_site(), _books(events=[{"kind": "GRID_LOSS", "at": "2026-10-09T10:00:00+03:00",
                                                  "source": "x"}]), "2026-09-29", "2026-09-30"),
     "TEL_EVENT_UNPLACED"),
    (lambda: _run(events=[{"kind": "GENERATOR_HAND_START", "at": "2026-09-30T10:00:00+03:00", "source": "x"}]),
     "TEL_PACK"),
])
def test_refusals_carry_their_code(make, code):
    with pytest.raises(TelemetryRefused) as caught:  # the frame's class since the join (D-DD.81)
        make()
    assert caught.value.code == code and str(caught.value).split()[0] == code
