"""DD4b rejoin (D-DD.98, D-DD.123): rotation of a full bus off its connector and the daytime spare.

The parity golden is the plant days' physics on `8d519ef49` (before rotation): every measurement row (asset,
channel, start, end, exact value, unit) and every departure. Rotation acts only where a bus waits, so Embakasi and
Ruiru stay byte-identical (D-DD.98 "Reach")."""

from __future__ import annotations

import hashlib
from fractions import Fraction

from .test_dd4_telemetry_ev import local, run

RUI_FAULT = {"asset": "ch-r7-c2", "at": "2026-10-06T00:00:00+03:00", "source": "M tenants.metro-bus.sites.EV-RUI.incident"}
KAS_FAULT = {"asset": "ch-k2", "at": "2026-11-01T23:40:00+03:00", "source": "M tenants.metro-bus.sites.EV-KAS.incident"}

#: sha256 of `_physics` on `8d519ef49` (computed there, before rotation and the rejoin).
GOLDEN = {
    ("EV-EMB", "2026-10-15", "2026-10-15"): "f3859e43af8061023cc5867bb5a361d17aec28456b8405702ab0ffc68baa5ee2",
    ("EV-RUI", "2026-10-05", "2026-10-07"): "4e2cf326f54f05378fa61b3a8a4322bbd04674dc10b183e76b3ed10b6976b9e1",
}


def _physics(r) -> str:
    h = hashlib.sha256()
    for day in r.days:
        for row in r.day_records(day):
            if row[5] in ("event", "state"):
                continue
            h.update(repr((row[0], row[1], row[2].isoformat(), row[3].isoformat(), str(row[4]), row[5])).encode())
    for d in sorted(r.departures(), key=lambda d: (d["departure_at"], d["vehicle_ref"])):
        h.update(repr((d["vehicle_ref"], d["service_day"], d["departure_at"].isoformat(), str(d["required_kwh"]),
                       str(d["delivered_kwh"]))).encode())
    return h.hexdigest()


def test_v1_embakasi_and_ruiru_plant_days_are_unchanged_by_rotation() -> None:
    for (code, first, last), digest in GOLDEN.items():
        faults = [RUI_FAULT] if code == "EV-RUI" else []
        assert _physics(run(code, first, last, faults=faults)) == digest, code


def test_v2_kasarani_rotation_unplugs_a_full_bus_for_a_waiting_one_five_minutes_later() -> None:
    from assetops_simulator.world import telemetry_ev

    assert telemetry_ev.ROTATION_MINUTES == 5
    r = run("EV-KAS", "2026-11-02", "2026-11-03", faults=[KAS_FAULT])
    plugs = r.assignments("2026-11-02")
    # every bus of the night gets a connector: the waiting ones on a connector a full bus left 5 minutes before
    refs = {bus for _, bus, _ in plugs}
    assert {f"EV-KAS-B0{i}" for i in range(1, 9)} <= refs
    ends = r.unplugs()
    for t, bus, asset in plugs:
        if t > local("2026-11-02T22:00"):
            left = [u for u in ends if u[2] == asset and u[0] == t - telemetry_ev.ROTATION_MINUTES_DELTA]
            assert left, (t, bus, asset)


def test_v3_the_spare_arrives_at_10_charges_by_day_and_is_rotated_off_at_22() -> None:
    r = run("EV-KAS", "2026-11-02", "2026-11-03", faults=[KAS_FAULT])
    spare = [p for p in r.assignments("2026-11-02") if p[1] == "EV-KAS-S01"]
    assert len(spare) == 1 and spare[0][0] == local("2026-11-02T10:00")
    out = [u for u in r.unplugs() if u[1] == "EV-KAS-S01"]
    assert out and out[0][0] == local("2026-11-02T22:00")
    d = next(d for d in r.departures() if d["vehicle_ref"] == "EV-KAS-S01" and d["service_day"] == "2026-11-02")
    assert d["delivered_kwh"] == Fraction(150) and d["departure_at"] == local("2026-11-03T05:00")
    assert any(c["condition"] == "rotation" for c in r.conditions())
    assert any(c["condition"] == "spare arrival" for c in r.conditions())
