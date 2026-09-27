"""Every way an execution can stop, reached rather than listed.

`conftest.py` fails the session if any member of `EXECUTION_FAILURE_KINDS` was
never produced, so this file is what keeps that vocabulary honest. Two of the ten
are reached with a deliberately broken model rather than with odd inputs, and
that is the point of them: `BALANCE_IDENTITY_VIOLATION` is a contradiction inside
a kernel and cannot be provoked from outside one, so the only way to show the
invariant bites is to break a handler and watch it fire.

A failed run is also checked for the thing a partial result must never do: pass
for a whole one. The trajectory carries `FAILED` and the reason, `is_complete` is
false, and the record refuses to be constructed in either of the two shapes that
would let a caller be misled.
"""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction

import pytest
from conftest import (
    CAPACITY,
    COEFFICIENT,
    GENERATOR,
    TANK,
    initial_value,
    world_inputs,
)

from assetops_contracts.execution_contract import (
    ExecutionContractIncompatible,
)
from assetops_contracts.failures import (
    EXECUTION_FAILURE_KINDS,
    EXECUTION_FAILURE_STATEMENTS,
    KernelExecutionFailed,
)
from assetops_contracts.trajectory import PrivateTrajectory
from assetops_contracts.world_inputs import DeclaredCause, ForcingInput
from assetops_simulator.kernel.execute import execute
from assetops_simulator.packs.fuel import (
    MINIMAL_FUEL_MODEL,
    STOCK_HANDLER,
)


def _failed(inputs, model=MINIMAL_FUEL_MODEL):
    run = execute(inputs, model)
    assert run.outcome == "FAILED", run.boundaries[-1] if run.boundaries else run
    assert run.failure is not None
    return run


class TestTheVocabularyItself:
    def test_every_kind_carries_a_statement(self) -> None:
        assert set(EXECUTION_FAILURE_STATEMENTS) == EXECUTION_FAILURE_KINDS

    def test_no_statement_is_empty_or_a_restatement_of_the_name(self) -> None:
        for kind, statement in EXECUTION_FAILURE_STATEMENTS.items():
            assert len(statement) > 60, kind
            assert kind.lower().replace("_", " ") not in statement.lower(), kind

    def test_not_comparable_is_deliberately_absent(self) -> None:
        """A comparison verdict is not an execution failure.

        v4 lists `NOT_COMPARABLE` beside these, and nothing failed when two runs
        turn out not to be comparable: both completed. Putting it here would make
        "execution failed" cover a case where nothing did.
        """
        assert "NOT_COMPARABLE" not in EXECUTION_FAILURE_KINDS


class TestAnIncompatibleContractIsRefusedBeforeAnythingIsInitialized:
    def test_a_run_frozen_against_another_version_is_not_executed(self) -> None:
        with pytest.raises(ExecutionContractIncompatible) as raised:
            execute(world_inputs(execution_contract_version=4))
        assert "version 4" in str(raised.value)
        assert "stays readable" in str(raised.value)

    def test_it_is_refused_rather_than_failing_as_an_execution(self) -> None:
        """A version mismatch is not a trajectory with a reason attached.

        Nothing ran, so there is nothing to hand back: the caller gets an
        exception rather than a `FAILED` trajectory it could mistake for a run
        that started.
        """
        with pytest.raises(ExecutionContractIncompatible):
            execute(world_inputs(execution_contract_version=6))


class TestAnEntryOutsideTheInterval:
    def test_a_point_at_the_end_instant_is_outside_a_half_open_interval(
        self,
    ) -> None:
        inputs = world_inputs()
        moved = replace(
            inputs,
            causes=tuple(
                replace(cause, offset_minutes=2460)
                if cause.event_id == "scheduled-refuelling"
                else cause
                for cause in inputs.causes
            ),
        )
        run = _failed(moved)
        assert run.failure.kind == "ENTRY_OUTSIDE_INTERVAL"
        assert run.failure.subject == "scheduled-refuelling"

    def test_a_window_running_past_the_end_is_outside_it(self) -> None:
        inputs = world_inputs()
        stretched = replace(
            inputs,
            causes=tuple(
                replace(cause, duration_minutes=1000)
                if cause.event_id == "unaccounted-fuel-removal"
                else cause
                for cause in inputs.causes
            ),
        )
        assert _failed(stretched).failure.kind == "ENTRY_OUTSIDE_INTERVAL"


class TestTopology:
    def test_two_tanks_are_named_rather_than_paired(self) -> None:
        inputs = world_inputs()
        two = replace(
            inputs,
            initial_values=inputs.initial_values
            + (
                initial_value(
                    "fuel-tank-volume@south-tank",
                    "fuel-tank-volume",
                    "south-starting-level",
                    Fraction(200),
                    "L",
                    "VOLUME",
                ),
            ),
        )
        run = _failed(two)
        assert run.failure.kind == "TOPOLOGY_INCONSISTENT"
        assert "fuel-tank" in run.failure.subject
        assert "south-tank" in run.failure.subject

    def test_no_tank_at_all_is_the_same_failure(self) -> None:
        inputs = world_inputs()
        none = replace(
            inputs,
            initial_values=tuple(
                item
                for item in inputs.initial_values
                if item.address not in {TANK, CAPACITY}
            ),
            bounds=(),
            causes=(),
        )
        run = _failed(none)
        assert run.failure.kind == "TOPOLOGY_INCONSISTENT"
        assert run.failure.subject == "no fuel tank"


class TestAStateThisModelDoesNotModel:
    def test_an_initial_value_with_no_handler_stops_the_run(self) -> None:
        """The backlog's trap, from the kernel's side.

        A `READY` run can carry an initialization input for a state this build
        does not model, and nothing on the row says so. The disqualification lives
        in the run's unsupported optional inputs, so an initial value for an
        unhandled state that is NOT recorded there stops the run rather than being
        silently skipped.
        """
        inputs = world_inputs()
        smuggled = replace(
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
        )
        run = _failed(smuggled)
        assert run.failure.kind == "UNSUPPORTED_MODEL_STATE"
        assert run.failure.subject == "battery-state-of-charge@battery"
        assert "unsupported optional input" in run.failure.detail[0]

    def test_the_same_row_recorded_as_unsupported_is_skipped_instead(
        self,
    ) -> None:
        """The cross-reference is what makes the difference, and it is the only
        thing that does."""
        inputs = world_inputs()
        recorded = replace(
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
        run = execute(recorded)
        assert run.outcome == "COMPLETED", run.failure
        assert "battery-state-of-charge@battery" not in dict(
            run.final.stocks
        )


class TestAnUnansweredInitialCondition:
    def test_a_stock_the_model_moves_with_no_initial_value_stops_the_run(
        self,
    ) -> None:
        """Unknown never silently becomes zero."""
        inputs = world_inputs()
        missing = replace(
            inputs,
            initial_values=tuple(
                item for item in inputs.initial_values if item.address != TANK
            ),
        )
        run = _failed(missing)
        assert run.failure.kind == "INITIAL_STATE_UNANSWERED"
        assert run.failure.subject == TANK


class TestAForcingThisModelRequires:
    def test_a_law_whose_forcing_is_declared_nowhere_stops_the_run(
        self,
    ) -> None:
        run = _failed(replace(world_inputs(), forcings=()))
        assert run.failure.kind == "FORCING_NOT_AVAILABLE"
        # The ADDRESS since the law-binding pass, not the bare semantic key: the
        # law's operand is resolved to the machine the model's relation selected,
        # so the failure can say which generator declared no window rather than
        # which kind of state one would have been about.
        assert run.failure.subject == GENERATOR

    def test_two_declared_values_for_one_address_are_refused_not_composed(
        self,
    ) -> None:
        """The gap T020B's review left open, met rather than discovered.

        `baseline-load-profile` declares two parameters for one address and one
        role, and nothing says whether they are the two ends of a ramp or two
        named levels a shape selects between. The kernel will not pick, because
        picking would invent one of two legitimate readings. It does not reach
        this on the shipped document only because nothing models site demand; a
        modelled state in the same shape reaches it here.
        """
        inputs = world_inputs()
        two_values = replace(
            inputs,
            forcings=inputs.forcings
            + (
                ForcingInput(
                    event_id="generator-run-window",
                    address=GENERATOR,
                    state_key="generator-output-power",
                    parameter_id="second-declared-output",
                    value=Fraction(18),
                    canonical_unit="kW",
                    dimension="POWER",
                    shape="WINDOW",
                    offset_minutes=1080,
                    duration_minutes=240,
                    requirement="REQUIRED",
                ),
            ),
        )
        run = _failed(two_values)
        assert run.failure.kind == "FORCING_VALUE_AMBIGUOUS"
        assert run.failure.subject == GENERATOR
        assert len(run.failure.detail) == 2


class TestAPhysicallyImpossibleValue:
    def test_a_negative_dispatched_output_is_refused_by_the_resolver(
        self,
    ) -> None:
        """The same fact as `invalid-rate`, one phase later.

        The parser refuses a negative power when a document is read, which is
        `REFUSED_AT_PARSE` and means no kernel ever sees one. This is what happens
        to content that reached a kernel without crossing that parser.
        """
        inputs = world_inputs()
        negative = replace(
            inputs,
            forcings=tuple(
                replace(forcing, value=Fraction(-45))
                for forcing in inputs.forcings
            ),
        )
        run = _failed(negative)
        assert run.failure.kind == "PHYSICAL_RESOLUTION_FAILURE"
        assert run.failure.at_offset_minutes == 1080

    def test_a_negative_initial_volume_is_refused_before_the_first_step(
        self,
    ) -> None:
        inputs = world_inputs()
        negative = replace(
            inputs,
            initial_values=tuple(
                replace(item, value=Fraction(-10))
                if item.address == TANK
                else item
                for item in inputs.initial_values
            ),
        )
        run = _failed(negative)
        assert run.failure.kind == "PHYSICAL_RESOLUTION_FAILURE"
        assert run.boundaries == ()


class TestABoundWhosePolicyFailsTheRun:
    def test_a_draw_the_tank_cannot_supply_fails_and_names_the_entry(
        self,
    ) -> None:
        """`insufficient-fuel` is `FAIL_RUN`, so this does not empty quietly."""
        inputs = world_inputs()
        nearly_empty = replace(
            inputs,
            initial_values=tuple(
                replace(item, value=Fraction(100))
                if item.address == TANK
                else item
                for item in inputs.initial_values
            ),
        )
        run = _failed(nearly_empty)
        assert run.failure.kind == "INTEGRATION_BOUND_FAILURE"
        assert run.failure.subject == TANK
        assert "insufficient-fuel" in run.failure.detail[0]
        assert "FAIL_RUN" in run.failure.detail[0]

    def test_the_run_stops_where_it_failed_and_says_it_is_not_complete(
        self,
    ) -> None:
        inputs = world_inputs()
        nearly_empty = replace(
            inputs,
            initial_values=tuple(
                replace(item, value=Fraction(100))
                if item.address == TANK
                else item
                for item in inputs.initial_values
            ),
        )
        run = _failed(nearly_empty)
        assert run.is_complete is False
        assert run.boundaries
        assert run.boundaries[-1].offset_minutes < 2460
        assert run.final.offset_minutes == run.failure.at_offset_minutes

    def test_a_caller_that_wants_an_exception_gets_the_same_record(self) -> None:
        inputs = world_inputs()
        nearly_empty = replace(
            inputs,
            initial_values=tuple(
                replace(item, value=Fraction(100))
                if item.address == TANK
                else item
                for item in inputs.initial_values
            ),
        )
        with pytest.raises(KernelExecutionFailed) as raised:
            execute(nearly_empty, raise_on_failure=True)
        assert raised.value.failure.kind == "INTEGRATION_BOUND_FAILURE"


class TestASimultaneousGroupWhoseOutcomeDependsOnOrder:
    def test_a_group_whose_extreme_reaches_a_bound_is_refused(self) -> None:
        """`intra-instant-order`, at the case it declines to answer.

        The tank holds 450 of 500. A delivery of 100 and a draw of 80 at one
        instant net to 470, which is inside the capacity; applied delivery-first
        the tank would reach 550, which is not. Two orderings, two answers, and
        the scenario declares them simultaneous, so no order is the true one.
        """
        inputs = _simultaneous_group(Fraction(450), Fraction(100), Fraction(80))
        run = _failed(inputs)
        assert run.failure.kind == "ORDER_DEPENDENT_GROUP"
        assert run.failure.subject == TANK
        assert len(run.failure.detail) == 2

    def test_the_same_group_with_no_bound_between_the_extremes_stands(
        self,
    ) -> None:
        """The other side of the same decision, so the refusal is not blanket.

        The tank holds 300. The same pair of causes peaks at 400 and troughs at
        220, both inside the bounds, so no ordering reaches a bound and the net
        stands. A kernel that refused every simultaneous group would pass the
        test above for the wrong reason.
        """
        inputs = _simultaneous_group(Fraction(300), Fraction(100), Fraction(80))
        run = execute(inputs)
        assert run.outcome == "COMPLETED", run.failure
        assert run.boundary_at(600).stock(TANK) == Fraction(320)

    def test_a_group_whose_net_breaks_the_bound_is_the_ordinary_bound_case(
        self,
    ) -> None:
        """Every ordering reaches it, so it is not an ambiguity.

        The tank holds 480, gains 100 and loses 20: the net is 560 against a 500
        capacity, so the bound is broken however the group is applied. That is
        `BOUNDED_AND_RECORDED` rather than a refusal to answer.
        """
        inputs = _simultaneous_group(Fraction(480), Fraction(100), Fraction(20))
        run = execute(inputs)
        assert run.outcome == "COMPLETED", run.failure
        assert run.boundary_at(600).stock(TANK) == Fraction(500)
        bounded = [
            transition
            for transition in run.bounded_transitions
            if transition.at_offset_minutes == 600
        ]
        assert len(bounded) == 1
        assert bounded[0].refused == Fraction(60)
        assert set(bounded[0].event_ids) == {"a-delivery", "a-draw"}


class TestTheConservationCheckBites:
    def test_a_stock_handler_that_moves_more_than_the_records_account_for(
        self,
    ) -> None:
        """`BALANCE_IDENTITY_VIOLATION`, reached by breaking a handler.

        It cannot be provoked from outside a kernel, because it is a
        contradiction inside one. So the model is broken on purpose: the stock
        handler adds one litre nobody declared, the invariant check recomputes the
        step from the records, and the two disagree. Without this the check would
        be a phase nothing had ever shown could fail.
        """
        liar = replace(
            STOCK_HANDLER,
            consume=lambda current, delta: current + delta + Fraction(1),
        )
        broken = replace(
            MINIMAL_FUEL_MODEL,
            handlers=tuple(
                liar if handler.handler_id == STOCK_HANDLER.handler_id else handler
                for handler in MINIMAL_FUEL_MODEL.handlers
            ),
        )
        run = _failed(world_inputs(), broken)
        assert run.failure.kind == "BALANCE_IDENTITY_VIOLATION"
        assert run.failure.subject == TANK
        assert "the stock moved by" in run.failure.detail[0]

    def test_the_honest_handler_passes_the_same_check(self) -> None:
        """Otherwise the test above would pass against any model at all."""
        assert execute(world_inputs()).outcome == "COMPLETED"


class TestAPartialResultCannotPassForAWholeOne:
    def test_completed_with_a_failure_attached_is_refused(self) -> None:
        run = _failed(replace(world_inputs(), forcings=()))
        with pytest.raises(ValueError) as raised:
            replace(run, outcome="COMPLETED")
        assert "may not be labelled a whole one" in str(raised.value)

    def test_failed_with_no_reason_is_refused(self) -> None:
        run = execute(world_inputs())
        with pytest.raises(ValueError) as raised:
            replace(run, outcome="FAILED")
        assert "names no reason" in str(raised.value)

    def test_an_outcome_outside_the_vocabulary_is_refused(self) -> None:
        run = execute(world_inputs())
        with pytest.raises(ValueError):
            replace(run, outcome="PARTIAL")

    def test_the_content_digest_distinguishes_a_failed_run(self) -> None:
        """A failed run and a completed one are not the same trajectory.

        They can share every boundary they both have, so a digest over the
        boundaries alone would give them one identity and a caller comparing
        digests would conclude they were the same run.
        """
        completed = execute(world_inputs())
        failed = _failed(
            replace(
                world_inputs(),
                causes=world_inputs().causes
                + (
                    DeclaredCause(
                        event_id="an-impossible-draw",
                        address=TANK,
                        state_key="fuel-tank-volume",
                        direction="DECREASE",
                        parameter_id="impossible",
                        quantity=Fraction(10_000),
                        canonical_unit="L",
                        dimension="VOLUME",
                        shape="POINT",
                        offset_minutes=2445,
                        duration_minutes=None,
                    ),
                ),
            )
        )
        assert isinstance(failed, PrivateTrajectory)
        assert failed.content_digest != completed.content_digest
        assert failed.failure.kind == "INTEGRATION_BOUND_FAILURE"


def _simultaneous_group(
    starting: Fraction, delivered: Fraction, drawn: Fraction
):
    """Two causes on one stock at one instant, and nothing else.

    The dispatch forcing is kept, because the law requires one to be declared,
    and its coefficient is set to nothing so the generator burns nothing. That is
    what makes the group the only thing acting: with the shipped coefficient the
    level at offset 600 would also carry four steps of consumption, and a test
    whose expected number folded in an unrelated quantity would be a test of the
    arithmetic in its own docstring.
    """
    inputs = world_inputs()
    return replace(
        inputs,
        initial_values=tuple(
            replace(item, value=starting)
            if item.address == TANK
            else replace(item, value=Fraction(0))
            if item.address == COEFFICIENT
            else item
            for item in inputs.initial_values
        ),
        forcings=tuple(
            replace(forcing, offset_minutes=0, duration_minutes=60)
            for forcing in inputs.forcings
        ),
        causes=(
            DeclaredCause(
                event_id="a-delivery",
                address=TANK,
                state_key="fuel-tank-volume",
                direction="INCREASE",
                parameter_id="delivered",
                quantity=delivered,
                canonical_unit="L",
                dimension="VOLUME",
                shape="POINT",
                offset_minutes=600,
                duration_minutes=None,
            ),
            DeclaredCause(
                event_id="a-draw",
                address=TANK,
                state_key="fuel-tank-volume",
                direction="DECREASE",
                parameter_id="drawn",
                quantity=drawn,
                canonical_unit="L",
                dimension="VOLUME",
                shape="POINT",
                offset_minutes=600,
                duration_minutes=None,
            ),
        ),
    )
