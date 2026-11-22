"""`mini-grid` v9: units (DD3b1; spec DD §4.3; D-DD.127; C-DD19 mini part).

v9 runs ordered generator and PV-inverter units, each with its own lifecycle, and the `UNIT_FAIL` / `UNIT_RESTORE`
forcings. With one generator and one inverter it runs v8's code path, so v8's trajectory is v9's (C-DD19, by
construction and by the October test below). Inputs are Kobo's, frozen by the writer from the fixture view's books;
the multi-unit cases add a unit to them by hand, each stated where it is added.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
from fractions import Fraction

import pytest

from assetops_contracts.world_inputs import BusAttachmentInput, DiscreteInitialValue, ForcingInput, InitialValue
from assetops_simulator.kernel.execute import start as start_execution
from assetops_simulator.packs import mini_grid
from assetops_simulator.world import telemetry as tel

from .conftest import REPOSITORY_ROOT, load_fixture
from .test_dd4_span_end import _kobo

LAYER4 = REPOSITORY_ROOT / "Docs" / "demo-sprint" / "product-direction-layer4"
V8, V9 = mini_grid.MINI_GRID_V8_MODEL, mini_grid.MINI_GRID_V9_MODEL
INVERTER_STATE = "inverter-state"


@pytest.fixture(scope="module")
def books() -> dict:
    history = json.loads((LAYER4 / "history.json").read_text(encoding="utf-8"))
    return tel.books_for(load_fixture(), history, {})["KOBO-001"]


def _v9(frozen, *, inverters: tuple[str, ...] = ("pv-inverter",)):
    """The same frozen inputs declared for v9: the model version and each inverter's scenario-owned state."""
    return dataclasses.replace(
        frozen, model_profile_version=9,
        discrete_initial_values=frozen.discrete_initial_values + tuple(
            DiscreteInitialValue(address=f"{INVERTER_STATE}@{inv}", state_key=INVERTER_STATE, scope="COMPONENT",
                                 value="AVAILABLE", answered_by="SCENARIO") for inv in inverters))


def _value(component: str, key: str, value: Fraction, unit: str, dimension: str) -> InitialValue:
    return InitialValue(address=f"{key}@{component}", state_key=key, scope="COMPONENT", parameter_id=f"test:{key}",
                        value=value, canonical_unit=unit, dimension=dimension, answered_by="SITE_FOUNDATION")


def _second_generator(frozen, rated: Fraction = Fraction(24)):
    """A second set `generator-b` (the test's own unit: rating `rated`, Kobo's SFC, no-load rule 0.08 L/h per kW,
    minimum load 30 %) on Kobo's tank and bus."""
    values = frozen.initial_values + (
        _value("generator-b", "generator-rated-power", rated, "kW", "POWER"),
        _value("generator-b", "generator-specific-fuel-consumption", Fraction(2917, 10000), "L/kWh",
               "VOLUME_PER_ENERGY"),
        _value("generator-b", "generator-no-load-fuel-rate", rated * Fraction(8, 100) / 60, "L/min", "VOLUME_RATE"),
        _value("generator-b", "generator-minimum-load", Fraction(30), "%", "FRACTION"))
    return dataclasses.replace(
        frozen, initial_values=values,
        bus_attachments=frozen.bus_attachments + (
            BusAttachmentInput("GENERATION", "generator-b", None, "ac-bus"),
            BusAttachmentInput("FUEL_SUPPLY", "fuel-tank", "generator-b", "ac-bus")),
        discrete_initial_values=frozen.discrete_initial_values + (
            DiscreteInitialValue(address="generator-state@generator-b", state_key="generator-state",
                                 scope="COMPONENT", value="STOPPED", answered_by="SCENARIO"),))


def _two_inverters(frozen):
    """Kobo's array wired half to `pv-inverter` and half to a second `pv-inverter-b`, each 25 kW (Mto's split)."""
    values = tuple(v for v in frozen.initial_values if v.state_key != "inverter-ac-limit") + (
        _value("pv-inverter", "inverter-ac-limit", Fraction(25), "kW", "POWER"),
        _value("pv-inverter-b", "inverter-ac-limit", Fraction(25), "kW", "POWER"),
        _value("pv-inverter", "pv-array-share", Fraction(1, 2), "1", "FRACTION"),
        _value("pv-inverter-b", "pv-array-share", Fraction(1, 2), "1", "FRACTION"))
    return dataclasses.replace(
        frozen, initial_values=values,
        bus_attachments=frozen.bus_attachments + (BusAttachmentInput("PV_SOURCE", "pv-array", "pv-inverter-b",
                                                                     "ac-bus"),))


def _event(kind: str, component: str, offset: int) -> ForcingInput:
    """A unit event at an instant: one minute at the instant, so it reaches exactly the step that holds it."""
    return ForcingInput(event_id=f"{kind}:{component}:{offset}", address=f"{kind}@{component}", state_key=kind,
                        parameter_id="unit-event", value=Fraction(1), canonical_unit="1", dimension="COUNT",
                        shape="WINDOW", offset_minutes=offset, duration_minutes=1, requirement="REQUIRED")


def _with(frozen, *events: ForcingInput):
    return dataclasses.replace(frozen, forcings=frozen.forcings + events)


def _run(frozen, model):
    execution = start_execution(frozen, model)
    execution.run_to_end()
    assert execution.outcome == "COMPLETED", execution.failure
    return execution


def _projected(boundary):
    """A boundary with v9's inverter states left out (the only state v8 does not carry)."""
    keep = lambda pairs: tuple(p for p in pairs if not p[0].startswith(f"{INVERTER_STATE}@"))  # noqa: E731
    return dataclasses.replace(boundary, discrete=keep(boundary.discrete),
                               discrete_for_step=keep(boundary.discrete_for_step))


def _digest(execution) -> str:
    rows = [repr(_projected(b)) for b in execution.boundaries] + [repr(t) for t in execution.discrete_transitions]
    return hashlib.sha256("\n".join(rows).encode()).hexdigest()


def _transitions(execution, address: str) -> list[tuple[int, str, str]]:
    return [(t.at_offset_minutes, t.previous, t.next) for t in execution.discrete_transitions if t.address == address]


def _interval(execution, address: str) -> list[Fraction]:
    return [dict(b.interval_measurements).get(address) for b in execution.boundaries[1:]]


# --- the version ----------------------------------------------------------------------------------------------------


def test_v9_is_a_new_version_with_its_own_lifecycle_and_v8_is_untouched() -> None:
    assert (V9.model_profile_id, V9.model_profile_version) == (V8.model_profile_id, 9)
    assert V8.discrete_state("generator-state").transitions == frozenset(
        {("STOPPED", "STARTING"), ("STARTING", "RUNNING"), ("RUNNING", "STOPPED")})
    assert V9.discrete_state("generator-state").transitions == V8.discrete_state("generator-state").transitions | {
        ("STOPPED", "FAILED"), ("STARTING", "FAILED"), ("RUNNING", "FAILED"), ("FAILED", "STOPPED")}
    inverter = V9.discrete_state(INVERTER_STATE)
    assert inverter.allowed_values == ("AVAILABLE", "FAILED")
    assert inverter.transitions == frozenset({("AVAILABLE", "FAILED"), ("FAILED", "AVAILABLE")})
    for key in ("unit-fail", "unit-restore"):
        assert V9.handler(key, "FORCING_INPUT", "COMPONENT") is not None
        assert V8.handler(key, "FORCING_INPUT", "COMPONENT") is None
    assert V9.handler("pv-array-share", "CAUSAL_INPUT", "COMPONENT") is not None
    assert V9.statement.startswith(V8.statement)


def test_c_dd19_one_of_each_is_v8_on_kobo_october(books: dict) -> None:
    """C-DD19 (mini part): v9 with one generator and one inverter is v8's trajectory on Kobo's October inputs."""
    frozen = tel.frozen_inputs(_kobo(), books, "2026-10-01", "2026-10-31")
    v8, v9 = _run(frozen, V8), _run(_v9(frozen), V9)
    assert len(v8.boundaries) == 31 * 288 + 1
    assert any(t.next == "RUNNING" for t in v8.discrete_transitions)
    assert _digest(v8) == _digest(v9)
    assert {dict(b.discrete)[f"{INVERTER_STATE}@pv-inverter"] for b in v9.boundaries} == {"AVAILABLE"}


# --- units ----------------------------------------------------------------------------------------------------------


def _lead_rated(frozen, rated: Fraction):
    """Kobo's set re-rated to `rated` kW (the test's own figure, so one set cannot carry the evening alone)."""
    return dataclasses.replace(frozen, initial_values=tuple(
        dataclasses.replace(v, value=rated) if v.address == "generator-rated-power@generator" else v
        for v in frozen.initial_values))


def test_two_generators_run_in_order_and_share_by_rating(books: dict) -> None:
    """Kobo's evening asks about 34 kW of the set (load plus the battery's acceptance); a 20 kW lead cannot carry it,
    so the 24 kW second set joins and each carries the set's output in proportion to its rating."""
    frozen = _v9(_second_generator(_lead_rated(tel.frozen_inputs(_kobo(), books, "2026-10-01", "2026-10-02"),
                                               Fraction(20))))
    run = _run(frozen, V9)
    lead, second = _interval(run, "generator-output-power@generator"), _interval(run, "generator-output-power@generator-b")
    both = [i for i, (a, b) in enumerate(zip(lead, second)) if a and b]
    assert both, "no step had both sets carrying"
    for i in both:
        assert lead[i] * 24 == second[i] * 20  # P x rating / the set's summed rating
    assert all(b == 0 for a, b in zip(lead, second) if not a)  # the second never carries before the lead
    total = [next(f.energy for f in b.control_step.accepted.flows if f.flow_id == "generator_output")
             for b in run.boundaries[:-1]]
    assert [a + b for a, b in zip(lead, second)] == total


def test_a_unit_failing_while_running_stops_at_that_step_and_restores_to_stopped(books: dict) -> None:
    base = _v9(_second_generator(tel.frozen_inputs(_kobo(), books, "2026-10-01", "2026-10-02")))
    first = _transitions(_run(base, V9), "generator-state@generator")
    on = next(at for at, _, nxt in first if nxt == "RUNNING")
    fail_at, restore_at = on + 12, on + 12 + 600  # 12 minutes into its run (inside a step), restored 10 h later
    run = _run(_with(base, _event("unit-fail", "generator", fail_at),
                     _event("unit-restore", "generator", restore_at)), V9)
    lead = _transitions(run, "generator-state@generator")
    step = fail_at - fail_at % 5
    assert (step, "RUNNING", "FAILED") in lead
    assert (restore_at - restore_at % 5, "FAILED", "STOPPED") in lead
    output = _interval(run, "generator-output-power@generator")
    failed = range(step // 5, (restore_at - restore_at % 5) // 5)
    assert all(output[i] == 0 for i in failed)
    assert any(_interval(run, "generator-output-power@generator-b")[i] for i in failed)


def test_a_failed_inverter_delivers_nothing_and_the_other_its_share(books: dict) -> None:
    base = _v9(_two_inverters(tel.frozen_inputs(_kobo(), books, "2026-10-01", "2026-10-01")),
               inverters=("pv-inverter", "pv-inverter-b"))
    healthy = _run(base, V9)
    run = _run(_with(base, _event("unit-fail", "pv-inverter-b", 6 * 60 + 2)), V9)
    a, b = _interval(run, "pv-available-power@pv-inverter"), _interval(run, "pv-available-power@pv-inverter-b")
    assert _interval(healthy, "pv-available-power@pv-inverter") == _interval(healthy, "pv-available-power@pv-inverter-b")
    assert any(a) and all(x == 0 for x in b[6 * 12:])
    assert a == _interval(healthy, "pv-available-power@pv-inverter")
    assert (6 * 60, "AVAILABLE", "FAILED") in _transitions(run, f"{INVERTER_STATE}@pv-inverter-b")


def test_one_generator_fails_under_v9_and_v8_refuses_the_forcing(books: dict) -> None:
    frozen = _with(tel.frozen_inputs(_kobo(), books, "2026-10-01", "2026-10-01"), _event("unit-fail", "generator", 60))
    v8 = start_execution(frozen, V8)
    v8.run_to_end()
    assert v8.outcome != "COMPLETED"
    run = _run(_v9(frozen), V9)
    assert _transitions(run, "generator-state@generator") == [(60, "STOPPED", "FAILED")]
    assert all(x == 0 for x in _interval(run, "generator-output-power@generator"))


@pytest.mark.parametrize("event", [("unit-restore", "generator"), ("unit-fail", "no-such-unit")])
def test_an_event_the_plant_cannot_take_refuses(books: dict, event: tuple[str, str]) -> None:
    frozen = _v9(_with(tel.frozen_inputs(_kobo(), books, "2026-10-01", "2026-10-01"), _event(*event, 60)))
    execution = start_execution(frozen, V9)
    execution.run_to_end()
    assert execution.outcome != "COMPLETED"


def test_an_inverter_without_its_state_or_shares_not_summing_to_one_refuses(books: dict) -> None:
    frozen = _two_inverters(tel.frozen_inputs(_kobo(), books, "2026-10-01", "2026-10-01"))
    missing = start_execution(_v9(frozen), V9)  # pv-inverter-b has no declared state
    missing.run_to_end()
    assert missing.outcome != "COMPLETED"
    uneven = dataclasses.replace(frozen, initial_values=tuple(
        dataclasses.replace(v, value=Fraction(3, 4)) if v.address == "pv-array-share@pv-inverter" else v
        for v in frozen.initial_values))
    execution = start_execution(_v9(uneven, inverters=("pv-inverter", "pv-inverter-b")), V9)
    execution.run_to_end()
    assert execution.outcome != "COMPLETED"
