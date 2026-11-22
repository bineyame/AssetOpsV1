"""0K4a commit 2: `decide_v8`, v5's controller with a running generator ranked ahead of the battery (spec §2.3).

Pure: views are built by hand, and each expected request is a hand literal (W2); the v5 comparison is the spec's own
statement of the rule (v8 on order PV, battery, generator asks what v5 asks on order PV, generator, battery).
"""

from __future__ import annotations

from fractions import Fraction as F

import pytest

from assetops_contracts.control import DISCRETE_UNIT, ControllerView, ViewEntry
from assetops_simulator.packs.mini_grid import decide_v5, decide_v8

NOTE = " (v8 cycle charging: a running generator is ahead of the battery)"
IDS = {"pv": "pv-inverter", "battery": "battery", "generator": "generator"}


def view(*, state="RUNNING", order=("pv", "battery", "generator"), soc=50, demand=75, pv=0, rated=40,
         running_for=10) -> ControllerView:
    entries = [
        ViewEntry("state-of-charge", "battery-state-of-charge@battery", F(soc), "%"),
        ViewEntry("reserve-in-effect", "battery-reserve-state-of-charge@battery", F(30), "%"),
        ViewEntry("pv-available", "pv-ac-power@pv-inverter", F(pv), "kW"),
        ViewEntry("load-demand", "load-demand@load-res", F(demand), "kW"),
        ViewEntry("generator-state", "generator-state@generator", state, DISCRETE_UNIT),
        ViewEntry("generator-running-for", "generator-state@generator",
                  F(running_for) if state == "RUNNING" else None, "min"),
        ViewEntry("generator-rated-power", "generator-rated-power@generator", F(rated), "kW"),
        ViewEntry("start-soc-threshold", "generator-start-soc-threshold@generator", F(35), "%"),
        ViewEntry("stop-soc-threshold", "generator-stop-soc-threshold@generator", F(90), "%"),
        ViewEntry("minimum-runtime", "generator-minimum-runtime@generator", F(30), "min"),
        ViewEntry("fuel-in-tank", "fuel-tank-volume@fuel-tank", F(1000), "L"),
    ]
    entries += [ViewEntry("source-priority-rank", IDS[s], F(rank), "rank") for rank, s in enumerate(order, start=1)]
    return ControllerView(at_offset_minutes=0, for_until_offset=5, entries=tuple(entries))


def battery(intent):
    return next(r for r in intent.requests if r.quantity == "battery-power")


def generator(intent):
    return next(r for r in intent.requests if r.quantity == "generator-run")


@pytest.mark.parametrize("demand, pv, expected", [
    (75, 0, F(35)),     # support: discharge only demand - pv - rating
    (13, 0, F(-27)),    # night charge from everything beyond demand
    (20, 15, F(-35)),   # PV and the generator both ahead: charge from 15 + 40 - 20
], ids=["support", "night-charge", "with-pv"])
def test_a_running_generator_ranks_ahead_of_the_battery(demand, pv, expected) -> None:
    site = view(demand=demand, pv=pv)
    v8 = decide_v8(site)
    v5_reordered = decide_v5(view(demand=demand, pv=pv, order=("pv", "generator", "battery")))
    assert battery(v8).requested == expected
    assert battery(v8).requested == battery(v5_reordered).requested
    assert battery(v8).reason == battery(v5_reordered).reason + NOTE
    assert generator(v8) == generator(decide_v5(site))  # the run decision is v5's exactly


def test_v5_on_the_site_order_is_battery_first() -> None:
    """The fault v8 fixes, stated on v5: battery ahead of a running generator discharges the whole demand."""
    assert battery(decide_v5(view(demand=75))).requested == F(75)
    assert battery(decide_v5(view(demand=13))).requested == F(13)


def test_only_the_generator_moves() -> None:
    """Order battery, PV, generator: the generator goes immediately before the battery and PV keeps its place behind
    it, so only the rating counts ahead of the battery: 75 - 40."""
    v8 = decide_v8(view(order=("battery", "pv", "generator"), demand=75, pv=20))
    assert battery(v8).requested == F(35)
    assert battery(v8).reason.endswith(NOTE)


@pytest.mark.parametrize("site", [
    view(state="STOPPED", soc=60),
    view(state="STARTING"),
    view(state="FAILED", soc=60),
    view(order=("pv", "generator", "battery")),
    view(order=("generator", "pv", "battery")),
], ids=["stopped", "starting", "failed", "already-ahead", "generator-first"])
def test_otherwise_v5_unchanged(site) -> None:
    assert decide_v8(site) == decide_v5(site)
