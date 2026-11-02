"""WALK1-4 (D-W1-7, D-W1-8): `mini-grid` v6 measures the battery controller's raw charge request.

v6 is v5 plus one interval measurement, `battery-charge-requested-power@battery-pcs`: the step's
`max(-requested, 0)` of the battery request, stored as energy over the step like every interval
measurement, so the published reading is its mean kW. These tests run the kernel in process (no gateway,
no database) on the reserve-trial scenario and compare v6 with v5 step by step:

- every v5 stock, intent and interval measurement is byte-identical under v6 (measurement only);
- the published mean kW of the new measurement equals `max(-requested, 0)` of the preceding step, and the
  set of steps with a positive request is not empty;
- v5's resolution and profiles are unchanged.
"""

from __future__ import annotations

from fractions import Fraction
from types import SimpleNamespace

from assetops_backend.runs.profiles import (
    MINI_GRID_V5_MODEL as V5_PROFILE,
    MINI_GRID_V6_MODEL as V6_PROFILE,
    REGISTERED_KOBO_PUBLICATION_PROFILE_V4,
    REGISTERED_KOBO_PUBLICATION_PROFILE_V5,
)
from assetops_simulator.observation.transform import world_value
from assetops_simulator.packs import mini_grid

from execution_adapter import model_for, run_to_end
from kobo import kobo_draft

START = "2026-09-22T03:00:00Z"  # 06:00 in Africa/Addis_Ababa
END = "2026-09-22T11:00:00Z"
TRIAL = "kobo-mini-grid-reserve-trial"
CHARGE = f"{mini_grid.BATTERY_CHARGE_REQUESTED_POWER}@battery-pcs"


def _trajectory(version: int):
    run = kobo_draft(TRIAL, timestep_minutes=5, model_profile="mini-grid", model_profile_version=version,
                     start_time=START, end_time=END)
    assert run.execution_status == "READY", [(r.kind, r.subject) for r in run.blocking_reasons]
    return run_to_end(run, model_for(run)).trajectory


def test_v6_is_a_new_version_beside_v5() -> None:
    assert (V6_PROFILE.model_profile_id, V6_PROFILE.model_profile_version) == ("mini-grid", 6)
    assert (mini_grid.MINI_GRID_V6_MODEL.model_profile_id, mini_grid.MINI_GRID_V6_MODEL.model_profile_version) == (
        "mini-grid", 6)
    assert mini_grid.MINI_GRID_V5_MODEL.coupling.resolve is mini_grid.resolve_v4
    assert mini_grid.MINI_GRID_V6_MODEL.coupling.resolve is mini_grid.resolve_v6
    assert mini_grid.MINI_GRID_V6_MODEL.coupling.decide is mini_grid.decide_v5
    assert mini_grid.MINI_GRID_V6_MODEL.measured_interval_states == (
        mini_grid.MINI_GRID_V5_MODEL.measured_interval_states | {mini_grid.BATTERY_CHARGE_REQUESTED_POWER})
    assert V5_PROFILE.model_profile_version == 5


def test_publication_v5_is_v4_plus_the_charge_request() -> None:
    v4, v5 = REGISTERED_KOBO_PUBLICATION_PROFILE_V4, REGISTERED_KOBO_PUBLICATION_PROFILE_V5
    assert (v5.publication_profile_id, v5.publication_profile_version) == ("registered-kobo-publication", 5)
    assert v5.device_signals[: len(v4.device_signals)] == v4.device_signals
    (added,) = v5.device_signals[len(v4.device_signals):]
    assert (added.device_id, added.signal_id, added.state_key) == (
        "battery-pcs-controller", "charge-requested-power", mini_grid.BATTERY_CHARGE_REQUESTED_POWER)
    assert (added.reading_class, added.canonical_unit, added.cadence_minutes) == ("INTERVAL_SIGNAL", "kW", 5)


def test_v6_measures_every_v5_quantity_identically_and_adds_the_raw_charge_request() -> None:
    v5, v6 = _trajectory(5), _trajectory(6)
    assert len(v5.boundaries) == len(v6.boundaries)
    signal = SimpleNamespace(is_discrete=False, reading_class="INTERVAL_SIGNAL", address=CHARGE)
    positive, previous = 0, None
    for a, b in zip(v5.boundaries, v6.boundaries):
        assert a.stocks == b.stocks
        assert a.discrete_for_step == b.discrete_for_step
        assert tuple(m for m in b.interval_measurements if m[0] != CHARGE) == a.interval_measurements
        if a.control_step is not None:
            assert a.control_step.intent == b.control_step.intent
        if previous is not None:
            requested = {r.quantity: r.requested for r in previous.control_step.intent.requests}["battery-power"]
            published = world_value(b, signal, 5)
            assert published == max(-requested, Fraction(0)), (b.offset_minutes, published, requested)
            positive += published > 0
        previous = b if b.control_step is not None else None
    assert positive > 0, "no step requested a charge: the equality above was checked only on zeros"
