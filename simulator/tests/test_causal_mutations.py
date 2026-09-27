"""Remove or retime a cause and the result changes in the way it should.

The metamorphic half of `D-2026-09-21-causal-runtime-before-golden-traces`. A
trajectory that matched a stored fixture would prove that the kernel is stable;
what has to be proved is that it is CAUSAL, which means the result has to move
when a cause moves and has to stay still when something that is not a cause
moves.

Each test below states the relationship it is about rather than only the numbers,
because the numbers alone would pass against a kernel that had memorised them.
"""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction

from conftest import (
    CAPACITY,
    COEFFICIENT,
    GENERATOR,
    SPECIFIC_CONSUMPTION,
    STARTING_LEVEL,
    TANK,
    TANK_CAPACITY,
    VOLUME_REMOVED,
    initial_value,
    world_inputs,
)

from assetops_simulator.kernel.execute import execute

AFTER_DISPATCH = Fraction(18701, 50)
AFTER_REMOVAL = Fraction(12701, 50)
DISPATCH_TOTAL = Fraction(2799, 50)


def _without(inputs, event_id: str):
    return replace(
        inputs,
        causes=tuple(
            cause for cause in inputs.causes if cause.event_id != event_id
        ),
    )


def _retimed(inputs, event_id: str, minutes: int):
    return replace(
        inputs,
        causes=tuple(
            replace(cause, offset_minutes=cause.offset_minutes + minutes)
            if cause.event_id == event_id
            else cause
            for cause in inputs.causes
        ),
    )


def _series(run) -> dict[int, Fraction]:
    return dict(run.stock_series(TANK))


class TestRemovingTheFuelRemoval:
    def test_only_the_consequences_of_that_cause_disappear(self) -> None:
        """Everything the removal did not cause is untouched, instant for instant.

        Asserted as an equality over every boundary up to the removal rather than
        at a few sampled ones, because "only its consequences" is a claim about
        all the others.
        """
        with_removal = _series(execute(world_inputs()))
        without = _series(execute(_without(world_inputs(), "unaccounted-fuel-removal")))

        before = [offset for offset in with_removal if offset <= 1500]
        assert len(before) == 101
        assert all(
            with_removal[offset] == without[offset] for offset in before
        )
        assert without[1320] == AFTER_DISPATCH

    def test_the_discontinuity_is_gone(self) -> None:
        without = _series(execute(_without(world_inputs(), "unaccounted-fuel-removal")))
        assert without[1515] == AFTER_DISPATCH
        assert without[1545] == AFTER_DISPATCH
        assert without[2385] == AFTER_DISPATCH

    def test_what_changes_downstream_is_itself_a_consequence(self) -> None:
        """The delivery refuses more, and that is not a leak.

        How much of a 300 litre delivery fits depends on how full the tank is at
        2400, and how full it is depends on the removal. So the bounded
        transition moving is the removal's consequence rather than an unrelated
        effect, and saying so is the difference between this test and one that
        quietly asserts nothing downstream changed.
        """
        with_removal = execute(world_inputs())
        without = execute(_without(world_inputs(), "unaccounted-fuel-removal"))

        assert with_removal.bounded_transitions[0].refused == Fraction("54.02")
        assert without.bounded_transitions[0].refused == Fraction("174.02")
        assert (
            without.bounded_transitions[0].refused
            - with_removal.bounded_transitions[0].refused
            == VOLUME_REMOVED
        )
        assert without.final.stock(TANK) == TANK_CAPACITY

    def test_the_consumption_the_generator_caused_is_untouched(self) -> None:
        without = execute(_without(world_inputs(), "unaccounted-fuel-removal"))
        consumed = sum(
            (
                event.declared
                for event in without.applied_events
                if event.origin == "MODEL_LAW"
            ),
            Fraction(0),
        )
        assert consumed == DISPATCH_TOTAL


class TestRetimingTheFuelRemoval:
    def test_the_discontinuity_shifts_to_the_new_boundary(self) -> None:
        """One step later, and the whole step is later: the same shape, moved."""
        original = _series(execute(world_inputs()))
        moved = _series(
            execute(_retimed(world_inputs(), "unaccounted-fuel-removal", 15))
        )

        assert original[1515] == AFTER_DISPATCH - 40
        assert moved[1515] == AFTER_DISPATCH
        assert moved[1530] == AFTER_DISPATCH - 40
        assert moved[1545] == AFTER_DISPATCH - 80
        assert moved[1560] == AFTER_REMOVAL
        assert original[1545] == AFTER_REMOVAL

    def test_the_set_of_boundaries_the_removal_touches_moves_by_one_step(
        self,
    ) -> None:
        original = execute(world_inputs())
        moved = execute(_retimed(world_inputs(), "unaccounted-fuel-removal", 15))

        def touched(run) -> set[int]:
            return {
                event.at_offset_minutes
                for event in run.applied_events
                if event.event_id == "unaccounted-fuel-removal"
            }

        assert touched(original) == {1500, 1515, 1530}
        assert touched(moved) == {1515, 1530, 1545}
        assert {offset + 15 for offset in touched(original)} == touched(moved)

    def test_the_quantity_removed_does_not_change_with_the_timing(self) -> None:
        moved = execute(_retimed(world_inputs(), "unaccounted-fuel-removal", 15))
        removed = sum(
            (
                event.declared
                for event in moved.applied_events
                if event.event_id == "unaccounted-fuel-removal"
            ),
            Fraction(0),
        )
        assert removed == VOLUME_REMOVED
        assert moved.final.stock(TANK) == TANK_CAPACITY


class TestChangingTheConsumptionCoefficient:
    def test_consumption_changes_with_the_dispatched_energy(self) -> None:
        """Twice the coefficient over the same dispatch is twice the fuel.

        Which is what makes the relationship the law rather than a number: the
        energy delivered is unchanged, so the whole of the difference is the
        coefficient's.
        """
        doubled = execute(_with_coefficient(world_inputs(), SPECIFIC_CONSUMPTION * 2))
        consumed = sum(
            (
                event.declared
                for event in doubled.applied_events
                if event.origin == "MODEL_LAW"
            ),
            Fraction(0),
        )
        assert consumed == DISPATCH_TOTAL * 2
        assert doubled.boundary_at(1320).stock(TANK) == (
            STARTING_LEVEL - DISPATCH_TOTAL * 2
        )

    def test_the_energy_delivered_is_unchanged_by_the_coefficient(self) -> None:
        doubled = execute(_with_coefficient(world_inputs(), SPECIFIC_CONSUMPTION * 2))
        original = execute(world_inputs())
        assert doubled.boundary_at(1095).interval_measurement(
            GENERATOR
        ) == original.boundary_at(1095).interval_measurement(GENERATOR)

    def test_a_coefficient_of_nothing_burns_nothing(self) -> None:
        """The relationship at its endpoint, which a scaling test alone misses."""
        none = execute(_with_coefficient(world_inputs(), Fraction(0)))
        assert none.boundary_at(1320).stock(TANK) == STARTING_LEVEL
        assert none.boundary_at(1545).stock(TANK) == STARTING_LEVEL - VOLUME_REMOVED

    def test_a_different_dispatched_output_changes_consumption_with_it(
        self,
    ) -> None:
        """The other half of the law: consumption follows the energy too."""
        inputs = world_inputs()
        doubled_output = replace(
            inputs,
            forcings=tuple(
                replace(forcing, value=forcing.value * 2)
                for forcing in inputs.forcings
            ),
        )
        run = execute(doubled_output)
        consumed = sum(
            (
                event.declared
                for event in run.applied_events
                if event.origin == "MODEL_LAW"
            ),
            Fraction(0),
        )
        assert consumed == DISPATCH_TOTAL * 2


class TestThingsThatAreNotCauses:
    def test_an_unrelated_unmodelled_declaration_leaves_the_fuel_result_stable(
        self,
    ) -> None:
        """Adding a component's state this model does not model changes nothing.

        The run records it as an unsupported optional input, the kernel skips it
        with a note saying so, and the tank's trajectory is identical instant for
        instant. The trajectory's IDENTITY legitimately differs, because the
        frozen inputs differ: what must not move is the fuel result.
        """
        inputs = world_inputs()
        widened = replace(
            inputs,
            initial_values=inputs.initial_values
            + (
                initial_value(
                    "battery-state-of-charge@battery",
                    "battery-state-of-charge",
                    "starting-state-of-charge",
                    Fraction(62),
                    "%",
                    "FRACTION",
                ),
            ),
            unmodelled_addresses=inputs.unmodelled_addresses
            + ("battery-state-of-charge@battery",),
        )
        original = execute(inputs)
        wider = execute(widened)

        assert wider.outcome == "COMPLETED", wider.failure
        assert _series(wider) == _series(original)
        assert any(
            "battery-state-of-charge@battery" in note for note in wider.notes
        )
        assert wider.inputs_identity != original.inputs_identity

    def test_repeating_a_run_produces_an_identical_canonical_trajectory(
        self,
    ) -> None:
        """Criterion 2's other half, and the mutation table's last row."""
        first = execute(world_inputs())
        second = execute(world_inputs())
        assert first.inputs_identity == second.inputs_identity
        assert first.content_digest == second.content_digest
        assert first.boundaries == second.boundaries
        assert first.applied_events == second.applied_events
        assert first.bounded_transitions == second.bounded_transitions

    def test_the_run_identity_is_not_part_of_the_world_identity(self) -> None:
        """Two Drafts of one experiment are the same experiment."""
        first = execute(world_inputs())
        second = execute(world_inputs(run_id="run-" + "1" * 32))
        assert first.inputs_identity == second.inputs_identity
        assert first.boundaries == second.boundaries
        assert first.content_digest != second.content_digest

    def test_a_reporting_path_condition_changes_no_world_quantity(self) -> None:
        """The publication profile's declaration is not a cause.

        Same world, same world identity. What differs between a run with a
        reporting gap and one without is which readings exist to publish, and
        that is the observation transform's business.
        """
        with_gap = execute(world_inputs())
        without_gap = execute(world_inputs(reporting_path_addresses=()))
        assert with_gap.inputs_identity == without_gap.inputs_identity
        assert _series(with_gap) == _series(without_gap)


class TestTheIdentityMovesWhenTheExperimentDoes:
    def test_a_different_seed_is_a_different_experiment(self) -> None:
        assert (
            execute(world_inputs()).inputs_identity
            != execute(world_inputs(seed=1)).inputs_identity
        )

    def test_a_different_capacity_is_a_different_experiment(self) -> None:
        inputs = world_inputs()
        changed = replace(
            inputs,
            initial_values=tuple(
                replace(item, value=Fraction(600))
                if item.address == CAPACITY
                else item
                for item in inputs.initial_values
            ),
            bounds=tuple(
                replace(bound, value=Fraction(600)) for bound in inputs.bounds
            ),
        )
        assert (
            execute(inputs).inputs_identity
            != execute(changed).inputs_identity
        )

    def test_a_different_timestep_is_a_different_experiment(self) -> None:
        inputs = world_inputs()
        assert (
            execute(inputs).inputs_identity
            != execute(
                replace(
                    inputs,
                    interval=replace(inputs.interval, timestep_minutes=60),
                )
            ).inputs_identity
        )

    def test_the_same_quantity_resolved_at_a_coarser_timestep_still_moves_in_full(
        self,
    ) -> None:
        """A timestep decides how finely a window is resolved, not what it does.

        At sixty minutes the removal window `[1500, 1545)` is off the grid and
        concerns exactly one step, so the whole 120 litres moves there. The
        trajectory differs in resolution and the quantity does not.
        """
        inputs = world_inputs()
        coarse = execute(
            replace(
                inputs, interval=replace(inputs.interval, timestep_minutes=60)
            )
        )
        assert coarse.outcome == "COMPLETED", coarse.failure
        removal = [
            event
            for event in coarse.applied_events
            if event.event_id == "unaccounted-fuel-removal"
        ]
        assert [event.at_offset_minutes for event in removal] == [1500]
        assert removal[0].declared == VOLUME_REMOVED
        assert removal[0].share == 1


def _with_coefficient(inputs, coefficient: Fraction):
    return replace(
        inputs,
        initial_values=tuple(
            replace(item, value=coefficient)
            if item.address == COEFFICIENT
            else item
            for item in inputs.initial_values
        ),
    )
