"""DIESEL-1-R3 K1a: `mini-grid` v7 samples the fuel in the tank, so a tank level sensor can report it.

v7 is v6 plus the fuel pack's state sample of `fuel-tank-volume` (`fuel.SAMPLE_HANDLER`, reused, never copied).
Before v7, `model.reports("fuel-tank-volume", "STATE_SIGNAL", "L")` was false on every mini-grid version, so the
host dropped `registered-kobo-publication`'s `fuel-level-sensor`/`fuel-level` silently (`execution_adapter.
reporting_inputs`). These tests run the kernel in process (no gateway, no database):

- v7 reports the tank level and v6 does not; v7's advertised states equal the product profile's;
- the stock handler's sentence is restated for v7 only, and v1-v6 keep theirs;
- a registered Kobo-template run on v7 with `registered-kobo-publication` v5 publishes a 15-minute tank level that
  is the stock at the instant plus the declared -0.5 L bias (before quantization and dropout), and the same
  document on v6 has the same generator, battery and tank trajectory without the sample;
- byte-equal pins: a v6 registered Kobo run and a v5 Lab run keep the digests they had before v7 existed.
"""

from __future__ import annotations

import dataclasses
import sys
from fractions import Fraction
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend" / "tests"))

import test_s6_verification_publication as pub  # noqa: E402
from kobo import kobo_draft  # noqa: E402

from assetops_backend.runs.profiles import (  # noqa: E402
    MINI_GRID_V5_MODEL as V5_PROFILE,
    MINI_GRID_V6_MODEL as V6_PROFILE,
    MINI_GRID_V7_MODEL as V7_PROFILE,
    MODEL_PROFILES,
    REGISTERED_KOBO_PUBLICATION_PROFILE_V3,
    REGISTERED_KOBO_PUBLICATION_PROFILE_V4,
    REGISTERED_KOBO_PUBLICATION_PROFILE_V5,
)
from assetops_contracts.observation import observation_series_digest, quantize_half_even  # noqa: E402
from assetops_simulator.observation.transform import generate_observations, world_value  # noqa: E402
from assetops_simulator.packs import fuel, mini_grid  # noqa: E402

from execution_adapter import EXECUTABLE_MODELS, model_for, reporting_inputs, run_to_end  # noqa: E402

TANK = "fuel-tank-volume"
LEVEL = ("fuel-level-sensor", "fuel-level")
FIXED_RUN_ID = "k1a-fixed-run-id"  # a Draft's run_id is minted per Draft, so digests are pinned with it fixed


def _pairs(states) -> set[tuple[str, str, str]]:
    return {(s.state_key, s.scope, role) for s in states for role in s.supported_roles}


def _stock_handler(model):
    return next(h for h in model.handlers if h.handler_id == "fuel-tank-volume-stock")


# --- the version itself ----------------------------------------------------------------------------


def test_v7_is_a_new_version_beside_v6_and_is_listed_and_executable() -> None:
    assert (V7_PROFILE.model_profile_id, V7_PROFILE.model_profile_version) == ("mini-grid", 7)
    v7 = mini_grid.MINI_GRID_V7_MODEL
    assert (v7.model_profile_id, v7.model_profile_version) == ("mini-grid", 7)
    assert v7.coupling is mini_grid.MINI_GRID_V6_MODEL.coupling
    assert v7.measured_interval_states == mini_grid.MINI_GRID_V6_MODEL.measured_interval_states
    assert v7.component_relations == mini_grid.MINI_GRID_V6_MODEL.component_relations
    assert MODEL_PROFILES.index(V7_PROFILE) == MODEL_PROFILES.index(V6_PROFILE) + 1
    assert EXECUTABLE_MODELS.index(v7) == EXECUTABLE_MODELS.index(mini_grid.MINI_GRID_V6_MODEL) + 1


def test_v7_reports_the_tank_level_and_v6_does_not() -> None:
    assert mini_grid.MINI_GRID_V7_MODEL.reports(TANK, "STATE_SIGNAL", "L")
    for model in (mini_grid.MINI_GRID_MODEL, mini_grid.MINI_GRID_V2_MODEL, mini_grid.MINI_GRID_V3_MODEL,
                  mini_grid.MINI_GRID_V4_MODEL, mini_grid.MINI_GRID_V5_MODEL, mini_grid.MINI_GRID_V6_MODEL):
        assert not model.reports(TANK, "STATE_SIGNAL", "L"), model.model_profile_version


def test_v7_reuses_the_fuel_pack_sampler_and_adds_nothing_else() -> None:
    v6, v7 = mini_grid.MINI_GRID_V6_MODEL.handlers, mini_grid.MINI_GRID_V7_MODEL.handlers
    assert v7[-1] is fuel.SAMPLE_HANDLER
    assert [h.handler_id for h in v7[:-1]] == [h.handler_id for h in v6]
    changed = [(a.handler_id, a.statement, b.statement) for a, b in zip(v6, v7[:-1]) if a != b]
    assert [c[0] for c in changed] == ["fuel-tank-volume-stock"]


def test_the_stock_sentence_is_restated_for_v7_only() -> None:
    old = "The fuel in the tank, initialized by the scenario and moved only by accepted generator energy."
    new = ("The fuel in the tank, initialized by the scenario, moved by accepted generator energy and by any "
           "frozen declared cause, such as a recorded operational action.")
    v6_stock, v7_stock = _stock_handler(mini_grid.MINI_GRID_V6_MODEL), _stock_handler(mini_grid.MINI_GRID_V7_MODEL)
    for model in (mini_grid.MINI_GRID_MODEL, mini_grid.MINI_GRID_V5_MODEL, mini_grid.MINI_GRID_V6_MODEL):
        assert _stock_handler(model).statement == old
    assert v7_stock.statement == new
    assert dataclasses.replace(v7_stock, statement=old) == v6_stock  # same id, role, kind, floor, law, initializer
    by_key = {p.model_profile_version: {s.state_key: s for s in p.supported_states}
              for p in (V6_PROFILE, V7_PROFILE)}
    assert by_key[6][TANK].statement == old and by_key[6][TANK].supported_roles == {"CAUSAL_INPUT"}
    assert by_key[7][TANK].statement == new
    assert by_key[7][TANK].supported_roles == {"CAUSAL_INPUT", "REPORTED_OBSERVATION"}
    assert {k: v for k, v in by_key[7].items() if k != TANK} == {k: v for k, v in by_key[6].items() if k != TANK}
    sentence = (" Version seven also samples the fuel in the tank at an instant, after that instant's events, "
                "so a tank level sensor can report it.")
    assert mini_grid.MINI_GRID_V7_MODEL.statement == mini_grid.MINI_GRID_V6_MODEL.statement + sentence
    assert V7_PROFILE.statement == V6_PROFILE.statement + sentence


def test_v7_advertises_what_the_product_profile_declares() -> None:
    assert _pairs(mini_grid.MINI_GRID_V7_MODEL.advertised_supported_states()) == _pairs(V7_PROFILE.supported_states)
    assert (TANK, "COMPONENT", "REPORTED_OBSERVATION") in _pairs(V7_PROFILE.supported_states)
    assert (TANK, "COMPONENT", "REPORTED_OBSERVATION") not in _pairs(V6_PROFILE.supported_states)


# --- a registered Kobo-template run: v7 against v6 -------------------------------------------------


@pytest.fixture(scope="module")
def store():
    store, result, _ = pub.registered.converted()
    pub.configure(store, result)
    return store


def _registered_draft(store, model):
    registered = pub.registered
    clock = registered.Clock(registered.NOW)
    service = registered.RunSetupService(
        registered.FakeRuns(), registered.FakeSites(()), registered.FakeScenarios((pub.PROLONGED,)),
        model_profiles=(model,),
        publication_profiles=(REGISTERED_KOBO_PUBLICATION_PROFILE_V3, REGISTERED_KOBO_PUBLICATION_PROFILE_V4,
                              REGISTERED_KOBO_PUBLICATION_PROFILE_V5),
        now=lambda: registered.text(registered.NOW),
        registered_bases=registered.RegisteredLabBasis(
            registered.ImportedSiteRegistry(registered.FoundationService(store, "demo", clock))),
    )
    foundation = registered.FoundationService(store, "demo", clock)
    tenant = foundation.tenant()
    view = foundation.read(foundation.site(tenant, "KOBO-001"), tenant, pub._at(pub.START), None)
    run = service.create_draft_run(registered.request(
        foundation_version=view.revision.version, scenario_id=pub.PROLONGED.scenario_id,
        scenario_version=pub.PROLONGED.version.scenario_version,
        interval={"start_time": pub.START, "end_time": pub.END}, timestep_minutes=5,
        model_profile={"profile_id": model.model_profile_id, "profile_version": model.model_profile_version},
        publication_profile={"profile_id": "registered-kobo-publication", "profile_version": 5},
    ))
    assert run.execution_status == "READY" and run.blocking_reasons == (), (run.execution_status,
                                                                             run.blocking_reasons)
    return run


def _executed(run):
    model = model_for(run)
    trajectory = run_to_end(run, model).trajectory
    reporting = reporting_inputs(run, None, model)
    return trajectory, reporting, generate_observations(trajectory.boundaries, reporting)


def _level(reporting):
    return next((s for s in reporting.signals if (s.device_id, s.signal_id) == LEVEL), None)


def test_v7_publishes_the_tank_level_every_15_minutes_as_the_stock_less_half_a_litre(store) -> None:
    trajectory, reporting, observations = _executed(_registered_draft(store, V7_PROFILE))
    signal = _level(reporting)
    assert signal is not None, "v7 must carry the tank level as a reporting path"
    assert signal.reading_class == "STATE_SIGNAL" and signal.canonical_unit == "L"
    assert signal.bias == Fraction(-1, 2)
    assert signal.address.startswith(f"{TANK}@")
    due = [o for o in observations if (o.device_id, o.signal_id) == LEVEL]
    assert [o.at_offset_minutes for o in due] == list(range(0, trajectory.boundaries[-1].offset_minutes + 1, 15))
    by_offset = {b.offset_minutes: b for b in trajectory.boundaries}
    reported = 0
    for item in due:
        boundary = by_offset[item.at_offset_minutes]
        stock = boundary.stock(signal.address)
        assert stock is not None and world_value(boundary, signal, None) == stock
        if item.outcome != "REPORTED":
            assert item.outcome in ("DROPPED", "SUPPRESSED_BY_GAP"), item
            continue
        expected = stock - Fraction(1, 2)
        if signal.resolution is not None:
            expected = quantize_half_even(expected, signal.resolution)
        assert item.reported_value == expected, (item.at_offset_minutes, item.reported_value, stock)
        reported += 1
    assert reported > 0, "no tank level was reported: the equality above was checked on an empty set"
    assert len({by_offset[o.at_offset_minutes].stock(signal.address) for o in due}) > 1, "the tank never moved"


def test_v7_and_v6_share_one_physics_and_differ_only_by_the_sample(store) -> None:
    v6_trajectory, v6_reporting, _ = _executed(_registered_draft(store, V6_PROFILE))
    v7_trajectory, v7_reporting, _ = _executed(_registered_draft(store, V7_PROFILE))
    assert _level(v6_reporting) is None  # v6 never carries the tank level (Kobo stays on v6)
    address = _level(v7_reporting).address
    keys = lambda reporting: [(s.device_id, s.signal_id) for s in reporting.signals]  # noqa: E731
    assert [k for k in keys(v7_reporting) if k != LEVEL] == keys(v6_reporting)
    assert len(v6_trajectory.boundaries) == len(v7_trajectory.boundaries)
    for a, b in zip(v6_trajectory.boundaries, v7_trajectory.boundaries):
        samples = dict(b.state_samples)
        assert samples.pop(address) == b.stock(address)
        assert address not in dict(a.state_samples)
        assert dataclasses.replace(b, state_samples=tuple(sorted(samples.items()))) == dataclasses.replace(
            a, state_samples=tuple(sorted(a.state_samples)))
    assert v6_trajectory.applied_events == v7_trajectory.applied_events
    assert v6_trajectory.bounded_transitions == v7_trajectory.bounded_transitions
    assert v6_trajectory.outcome == v7_trajectory.outcome == "COMPLETED"


# --- byte-equal pins (computed on main b5b3e7f03 before v7 existed) ---------------------------------


def _digests(run) -> tuple[str, str, str]:
    trajectory, _, observations = _executed(run)
    fixed = dataclasses.replace(trajectory, run_id=FIXED_RUN_ID)
    return fixed.content_digest, trajectory.inputs_identity, observation_series_digest(observations)


def test_a_v6_registered_kobo_run_keeps_its_digests(store) -> None:
    assert _digests(_registered_draft(store, V6_PROFILE)) == (
        "b0d800f360e035a9fa150c21f1fc6671b104b7df97a610dd742363cc8ebce24f",
        "c703db7f803806f30e36183af9eb995f03fcbddae832bc55452520212a5ada92",
        "bc9989c23afda6bf0ced1600ad0f4f6b5004c293cd62a0e19cc1fdf4374e7cc9",
    )


def test_a_v5_lab_run_keeps_its_digests() -> None:
    run = kobo_draft("kobo-mini-grid-reserve-trial", timestep_minutes=5, model_profile="mini-grid",
                     model_profile_version=V5_PROFILE.model_profile_version,
                     start_time="2026-09-22T03:00:00Z", end_time="2026-09-22T11:00:00Z")
    assert run.execution_status == "READY"
    assert _digests(run) == (
        "6c49e7c00e75d0ac465134a6d996133ea73df2b492858cd3bf30996ddddf84a5",
        "5c79b256e104e2ec23da0c2e6da788f3e1dd47ccabd01e67f110ae6a7dc349da",
        "ee83becde77bc74539aef998d14b80268f2f37dd226bf5d57a4176173b43fb98",
    )
