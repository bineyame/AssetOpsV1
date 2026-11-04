"""MD-0 L1 shape parity (build sheet MD-0 §17, MD0-S4 R1.3): the guard against the next fixture drift.

For every (device, signal) the MD-0 generator emits, its measurement kind must equal the producer mapping's
(`simulator/assetops_simulator/gateway/mappings.py` SIMULATOR_LAB_DISPATCH_MAPPINGS) and an interval mean must span
the producer's interval and end at its source time (`gateway/publish.py:199-203`). It lives in `host/tests` because
only the composition leaf may import both the simulator and the backend test harness. Pure: no database.
"""

from __future__ import annotations

import importlib.util
import sys
from datetime import timedelta
from pathlib import Path

import pytest

from assetops_simulator.gateway.mappings import SIMULATOR_LAB_DISPATCH_MAPPINGS

ROOT = Path(__file__).resolve().parents[2]
#: The producer's interval: the polish build's KOBO-001 power roles are 300 s means ending at their source time
#: (measured, SELECT only; build sheet MD-0 §17 F2). The mapping fixes the kind; the run's timestep fixes the span.
PRODUCER_INTERVAL = timedelta(seconds=300)
#: Channels only the reviewed w4 spare-solar variant carries (the D12/D13 noon remap, 60 s means from
#: `backend/conversions/w4-mini-depth-cases-v1.json`); the dispatch mapping has no entry for them.
W4_ONLY = {("battery-pcs-controller", "charge-requested-power"), ("clinic-meter", "requested-power"),
           ("clinic-meter", "delivered-power"), ("residential-meter", "requested-power"),
           ("mill-meter", "requested-power")}


def _harness():
    if str(ROOT / "backend" / "tests") not in sys.path:
        sys.path.append(str(ROOT / "backend" / "tests"))
    spec = importlib.util.spec_from_file_location("md0_harness", ROOT / "backend" / "tests" / "mechanism_dataset.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


md = _harness()
SPEC = md.load()
PRODUCER = {(e.device_id, e.signal_id): e.measurement for e in SIMULATOR_LAB_DISPATCH_MAPPINGS.entries
            if e.family == "MEASUREMENT"}


@pytest.mark.parametrize("n,kind", [(1, "normal"), (4, "overrun"), (7, "overrun")])
def test_every_generated_channel_has_the_producer_shape(n, kind) -> None:
    rows = md.kobo_rows(SPEC, n, kind)
    shapes = {md.row_shape(r) for r in rows}
    assert shapes, "no rows generated"
    for device, signal, measurement, seconds in shapes:
        assert (device, signal) in PRODUCER, f"{device}/{signal} is not a producer channel"
        assert measurement == PRODUCER[(device, signal)], (device, signal, measurement)
        if measurement == "INTERVAL_MEAN":
            assert seconds == PRODUCER_INTERVAL.total_seconds(), (device, signal, seconds)
    # non-vacuous: both kinds occur
    assert {s[2] for s in shapes} == {"INTERVAL_MEAN", "STATE_AT_INSTANT"}
    for r in rows:
        if not isinstance(r, tuple):  # an interval mean ends at its source time (publish.py:199-203)
            assert r.interval_start + PRODUCER_INTERVAL == r.source_time


def test_the_noon_remap_keeps_the_producer_kind_on_every_mapped_channel() -> None:
    import w402_mini_depth_cases as cases

    noon = SPEC["sites"]["kobo"]["noon"]
    variant = next(v for v in cases.load_spec()["variants"] if v["variant"] == noon["variant"])
    moved = {k: v for k, v in variant.items() if k not in noon.get("omit", ())}
    planned = cases.plan_variant(moved)
    assert planned
    unmapped = set()
    for p in planned:
        if (p.device, p.signal) not in PRODUCER:
            unmapped.add((p.device, p.signal))
            continue
        assert md.row_shape(p)[2] == PRODUCER[(p.device, p.signal)], (p.device, p.signal)
    assert unmapped <= W4_ONLY, unmapped - W4_ONLY
