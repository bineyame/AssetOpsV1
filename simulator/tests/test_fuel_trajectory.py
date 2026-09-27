"""The fuel trajectory, derived by hand and asserted as exact rationals.

Every number below was worked out from the shipped document's own declarations
before the kernel was run, and none of it came from a snapshot the
implementation produced. That is the point of the criterion: a trajectory
compared only against its own output is a record of what the code does, not
evidence that what it does is right.

The derivation, once, so a reader can check it rather than take it:

    dispatch      45 kW over [1080, 1320), which is 16 steps of 15 minutes
    per step      45 kW x 1/4 h = 45/4 kWh delivered
    per step      311/1000 L/kWh x 45/4 kWh = 2799/800 L consumed
    over 16       16 x 2799/800 = 2799/50 = 55.98 L
    after 1320    430 - 2799/50 = 18701/50 = 374.02 L
    removal       120 L over [1500, 1545), three steps, 40 L each
    after 1545    18701/50 - 120 = 12701/50 = 254.02 L
    delivery      300 L at 2400 would reach 27701/50 = 554.02 L
    capacity      500 L, so the tank fills and refuses 2701/50 = 54.02 L

None of those is a decimal in the code. 0.311 entered as 311/1000 at the input
boundary and every step since has been a ratio, which is what `EXACT_RATIONAL`
means and why 430 - 55.98 is exactly 18701/50 rather than a float near it.
"""

from __future__ import annotations

from fractions import Fraction

from conftest import (
    CAPACITY,
    COEFFICIENT,
    DISPATCHED_OUTPUT,
    GENERATOR,
    SPECIFIC_CONSUMPTION,
    STARTING_LEVEL,
    TANK,
    TANK_CAPACITY,
    VOLUME_DELIVERED,
    VOLUME_REMOVED,
    world_inputs,
)

from assetops_simulator.kernel.execute import execute

PER_STEP_ENERGY = Fraction(45, 4)
PER_STEP_CONSUMPTION = Fraction(2799, 800)
DISPATCH_TOTAL = Fraction(2799, 50)
AFTER_DISPATCH = Fraction(18701, 50)
AFTER_REMOVAL = Fraction(12701, 50)
UNBOUNDED_AFTER_DELIVERY = Fraction(27701, 50)
REFUSED_AT_CAPACITY = Fraction(2701, 50)


def trajectory(**overrides):
    return execute(world_inputs(**overrides))


class TestTheHandDerivedTrajectory:
    def test_the_selected_boundaries_are_the_derived_rationals(self) -> None:
        run = trajectory()
        assert run.outcome == "COMPLETED", run.failure

        expected = {
            0: STARTING_LEVEL,
            1080: STARTING_LEVEL,
            1095: STARTING_LEVEL - PER_STEP_CONSUMPTION,
            1110: STARTING_LEVEL - 2 * PER_STEP_CONSUMPTION,
            1320: AFTER_DISPATCH,
            1500: AFTER_DISPATCH,
            1515: AFTER_DISPATCH - 40,
            1530: AFTER_DISPATCH - 80,
            1545: AFTER_REMOVAL,
            2385: AFTER_REMOVAL,
            2400: TANK_CAPACITY,
            2460: TANK_CAPACITY,
        }
        for offset, value in expected.items():
            assert run.boundary_at(offset).stock(TANK) == value, offset

    def test_the_derived_numbers_are_the_decimals_a_reader_would_write(
        self,
    ) -> None:
        """The same states, as decimals, so the derivation is checkable by eye.

        Asserted through `Fraction` on both sides: comparing against a float
        would test the float rather than the arithmetic.
        """
        run = trajectory()
        assert run.boundary_at(1095).stock(TANK) == Fraction("426.50125")
        assert run.boundary_at(1320).stock(TANK) == Fraction("374.02")
        assert run.boundary_at(1545).stock(TANK) == Fraction("254.02")
        assert run.boundary_at(2400).stock(TANK) == Fraction("500")

    def test_every_boundary_of_the_interval_is_recorded_once(self) -> None:
        run = trajectory()
        offsets = [boundary.offset_minutes for boundary in run.boundaries]
        assert offsets == list(range(0, 2461, 15))
        assert len(offsets) == 165
        assert len(set(offsets)) == len(offsets)

    def test_the_step_index_and_the_instant_agree(self) -> None:
        run = trajectory()
        assert run.boundary_at(0).simulation_time == "2026-09-21T00:00:00Z"
        assert run.boundary_at(1080).step_index == 72
        assert run.boundary_at(1080).simulation_time == "2026-09-21T18:00:00Z"
        assert run.boundary_at(2460).simulation_time == "2026-09-22T17:00:00Z"


class TestDispatchEnergyAndTheConsumptionLaw:
    def test_the_interval_energy_is_the_forced_output_over_the_step(
        self,
    ) -> None:
        run = trajectory()
        assert run.boundary_at(1095).interval_measurement(
            GENERATOR
        ) == PER_STEP_ENERGY
        assert run.boundary_at(1320).interval_measurement(
            GENERATOR
        ) == PER_STEP_ENERGY

    def test_consumption_is_the_coefficient_times_delivered_energy(
        self,
    ) -> None:
        run = trajectory()
        consumed = [
            event.declared
            for event in run.applied_events
            if event.origin == "MODEL_LAW"
        ]
        assert len(consumed) == 16
        assert set(consumed) == {PER_STEP_CONSUMPTION}
        assert (
            sum(consumed, Fraction(0))
            == SPECIFIC_CONSUMPTION * DISPATCHED_OUTPUT * 4
        )
        assert sum(consumed, Fraction(0)) == DISPATCH_TOTAL

    def test_the_law_is_attributed_to_the_model_and_not_to_the_document(
        self,
    ) -> None:
        run = trajectory()
        origins = {event.origin for event in run.applied_events}
        assert origins == {"DECLARED_CAUSE", "MODEL_LAW"}
        law_ids = {
            event.event_id
            for event in run.applied_events
            if event.origin == "MODEL_LAW"
        }
        assert law_ids == {"fuel-consumption-follows-delivered-energy"}


class TestTheForcingOutsideItsWindow:
    def test_it_is_available_in_every_step_the_window_concerns(self) -> None:
        run = trajectory()
        available = [
            boundary.offset_minutes
            for boundary in run.boundaries
            if boundary.forcing(GENERATOR) is not None
        ]
        assert available == list(range(1080, 1320, 15))
        assert len(available) == 16
        assert run.boundary_at(1080).forcing(GENERATOR) == DISPATCHED_OUTPUT

    def test_it_is_absent_rather_than_zero_or_held(self) -> None:
        """Unavailable has no number, which is what makes it unavailable.

        Asserted as an absence on the record rather than as a zero, and asserted
        at the instant after the window closes, which is the one a hold-last rule
        would have got wrong.
        """
        run = trajectory()
        after = run.boundary_at(1320)
        assert after.forcing(GENERATOR) is None
        assert after.exposures_of(GENERATOR) == ()
        assert after.forcing_exposures == ()
        assert run.boundary_at(1065).forcing(GENERATOR) is None
        assert run.boundary_at(1065).exposures_of(GENERATOR) == ()

    def test_no_consumption_is_computed_where_the_forcing_is_unavailable(
        self,
    ) -> None:
        run = trajectory()
        consumed_at = {
            event.at_offset_minutes
            for event in run.applied_events
            if event.origin == "MODEL_LAW"
        }
        assert consumed_at == set(range(1080, 1320, 15))
        assert run.boundary_at(1335).stock(TANK) == AFTER_DISPATCH


class TestTheFirstBoundaryHasNoPrecedingInterval:
    def test_the_first_boundary_carries_no_interval_measurement(self) -> None:
        run = trajectory()
        first = run.boundary_at(0)
        assert first.has_preceding_interval is False
        assert first.interval_measurements == ()

    def test_every_later_boundary_has_an_interval_behind_it(self) -> None:
        run = trajectory()
        later = [
            boundary
            for boundary in run.boundaries
            if boundary.offset_minutes > 0
        ]
        assert len(later) == 164
        assert all(boundary.has_preceding_interval for boundary in later)

    def test_a_preceding_interval_is_not_the_same_as_a_measurement_in_it(
        self,
    ) -> None:
        """Two facts, and the field names keep them apart.

        At offset 1080 an interval has ended and the generator was not dispatched
        over it, so there is an interval and no measurement. At 1095 there is
        both. A field called "measurements available" would have made the first
        case unsayable, and the honest answer there is an absent measurement
        rather than a zero.
        """
        run = trajectory()
        at_start_of_dispatch = run.boundary_at(1080)
        assert at_start_of_dispatch.has_preceding_interval is True
        assert at_start_of_dispatch.interval_measurements == ()
        after_one_step = run.boundary_at(1095)
        assert after_one_step.has_preceding_interval is True
        assert after_one_step.interval_measurement(GENERATOR) == PER_STEP_ENERGY

    def test_the_stock_sample_at_the_first_boundary_is_unaffected(self) -> None:
        """The rule is about interval readings, and only about those."""
        run = trajectory()
        assert dict(run.boundary_at(0).state_samples) == {
            TANK: STARTING_LEVEL
        }

    def test_no_profile_record_can_declare_an_initial_historical_window(
        self,
    ) -> None:
        """The rule states its exception is unreachable; this is why.

        `no-interval-signal-at-the-first-boundary` says no profile record carries
        such a field and nothing parses one, so the kernel has no branch for it.
        That claim is about the product's profile records, which this suite
        cannot import - it is asserted in `host/tests/test_kernel_conformance.py`,
        where both sides are visible. What is asserted here is the other half:
        that this kernel's first boundary is unconditional.
        """
        run = trajectory(
            interval=world_inputs().interval,
        )
        assert run.boundary_at(0).has_preceding_interval is False


class TestSamplingHappensAfterTheEventsDueAtThatInstant:
    def test_the_delivery_is_visible_in_the_sample_timestamped_at_it(
        self,
    ) -> None:
        """The case `D-2026-09-22-kernel-step-semantics` names.

        At offset 2400 the sample is 500 L and not 254.02 L: a stock reading
        timestamped T is the state after T's events, and the delivery is due at
        T. A kernel sampling before the events would report the pre-delivery
        level under a timestamp at which the delivery had happened.
        """
        run = trajectory()
        at_delivery = run.boundary_at(2400)
        assert dict(at_delivery.state_samples) == {TANK: TANK_CAPACITY}
        assert at_delivery.stock(TANK) == TANK_CAPACITY
        assert run.boundary_at(2385).stock(TANK) == AFTER_REMOVAL

    def test_an_interval_reading_at_that_instant_still_describes_before_it(
        self,
    ) -> None:
        """Two conventions at one timestamp, which is the pair that matters."""
        run = trajectory()
        at_dispatch_end = run.boundary_at(1320)
        assert at_dispatch_end.stock(TANK) == AFTER_DISPATCH
        assert (
            at_dispatch_end.interval_measurement(GENERATOR) == PER_STEP_ENERGY
        )
        assert at_dispatch_end.forcing(GENERATOR) is None


class TestTheCapacityBound:
    def test_the_delivery_fills_the_tank_and_records_what_it_refused(
        self,
    ) -> None:
        run = trajectory()
        assert len(run.bounded_transitions) == 1
        bounded = run.bounded_transitions[0]
        assert bounded.address == TANK
        assert bounded.at_offset_minutes == 2400
        assert bounded.bound_case_id == "fuel-tank-capacity"
        assert bounded.bound_value == TANK_CAPACITY
        assert bounded.requested == UNBOUNDED_AFTER_DELIVERY
        assert bounded.accepted == TANK_CAPACITY
        assert bounded.refused == REFUSED_AT_CAPACITY
        assert bounded.event_ids == ("scheduled-refuelling",)

    def test_the_run_continues_and_later_state_is_the_bounded_value(
        self,
    ) -> None:
        """`BOUNDED_AND_RECORDED` only means something if there is a rest of the
        run for the refusal to be recorded in."""
        run = trajectory()
        assert run.outcome == "COMPLETED"
        assert run.boundary_at(2460).stock(TANK) == TANK_CAPACITY
        assert run.final.stock(TANK) == TANK_CAPACITY

    def test_a_larger_capacity_is_not_reached_at_all(self) -> None:
        """Bound behaviour follows the frozen capacity, not the document.

        With 600 L frozen, the same 300 L delivery into the same 254.02 L fits,
        so nothing is bounded and the tank ends at 554.02 L. Only the capacity
        changed.
        """
        inputs = world_inputs()
        run = execute(_with_capacity(inputs, Fraction(600)))
        assert run.bounded_transitions == ()
        assert run.boundary_at(2400).stock(TANK) == UNBOUNDED_AFTER_DELIVERY
        assert run.final.stock(TANK) == Fraction("554.02")

    def test_a_smaller_capacity_refuses_more(self) -> None:
        inputs = world_inputs()
        run = execute(_with_capacity(inputs, Fraction(450)))
        assert run.boundary_at(2400).stock(TANK) == Fraction(450)
        assert run.bounded_transitions[0].refused == (
            UNBOUNDED_AFTER_DELIVERY - 450
        )


class TestConservationIsExact:
    def test_the_whole_run_balances_against_the_declared_quantities(
        self,
    ) -> None:
        """Both sides computed from different records.

        The left side is the difference between two boundary states the model's
        own handler produced. The right side is built from the declared inputs,
        the applied-event records and the bounded-transition records. An equality
        between two numbers one function produced would prove nothing.
        """
        run = trajectory()
        initial = run.boundary_at(0).stock(TANK)
        final = run.final.stock(TANK)

        increases = sum(
            (
                event.declared
                for event in run.applied_events
                if event.address == TANK and event.direction == "INCREASE"
            ),
            Fraction(0),
        )
        decreases = sum(
            (
                event.declared
                for event in run.applied_events
                if event.address == TANK and event.direction == "DECREASE"
            ),
            Fraction(0),
        )
        refused_at_upper = sum(
            (
                transition.refused
                for transition in run.bounded_transitions
                if transition.address == TANK and transition.bound_kind == "UPPER"
            ),
            Fraction(0),
        )

        assert increases == VOLUME_DELIVERED
        assert decreases == VOLUME_REMOVED + DISPATCH_TOTAL
        assert refused_at_upper == REFUSED_AT_CAPACITY
        assert final - initial == increases - decreases - refused_at_upper

    def test_the_declared_window_quantity_moves_in_full(self) -> None:
        """The shares sum to one, so 120 litres leave the tank and not 119.99."""
        run = trajectory()
        removal = [
            event
            for event in run.applied_events
            if event.event_id == "unaccounted-fuel-removal"
        ]
        assert len(removal) == 3
        assert sum(event.share for event in removal) == 1
        assert sum(
            (event.declared for event in removal), Fraction(0)
        ) == VOLUME_REMOVED
        assert {event.declared for event in removal} == {Fraction(40)}


def _with_capacity(inputs, capacity: Fraction):
    """The same inputs with only the frozen capacity changed.

    Both places the number appears - the initial value the Foundation answered
    and the bound resolved from it - because changing one and not the other would
    be changing the document rather than the site.
    """
    from dataclasses import replace

    return replace(
        inputs,
        initial_values=tuple(
            replace(item, value=capacity)
            if item.address == CAPACITY
            else item
            for item in inputs.initial_values
        ),
        bounds=tuple(
            replace(bound, value=capacity) for bound in inputs.bounds
        ),
    )
