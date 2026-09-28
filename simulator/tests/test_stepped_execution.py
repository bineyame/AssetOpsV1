"""One execution as a handle, advanced a boundary at a time.

T021 built a kernel that ran to the end and returned a trajectory. T022 needs the
Lab to step one and show the world at the instant it has reached, which is a
different shape: a run in progress is a handle rather than a trajectory, and
`PrivateTrajectory` has two outcomes and no third precisely so that a prefix
cannot pass for a whole result.

What these prove is the property the refactor has to have and could quietly lose:
advancing in any pattern produces the same trajectory advancing in one call does.
Every scrap of execution state lives on one mutable object, so the phases visit
the same object in the same order whichever way they are driven - but "so it must
be fine" is the argument this project has been wrong about before, so it is
measured.
"""

from __future__ import annotations

import pytest

from assetops_contracts.execution_contract import (
    EXECUTION_CONTRACT_VERSION,
    ExecutionContractIncompatible,
)
from assetops_contracts.world_inputs import FrozenWorldInputs
from assetops_simulator.kernel.execute import (
    Execution,
    ExecutionStillRunning,
    execute,
    start,
)


def test_a_handle_starts_with_no_boundary_covered(
    fuel_loss_inputs: FrozenWorldInputs,
) -> None:
    """Opening an execution and advancing it are two acts.

    A `start` that advanced would lose the difference between a Draft nothing has
    executed and a run sitting at its first boundary, and the Lab shows exactly
    that difference.
    """
    handle = start(fuel_loss_inputs)

    assert handle.boundaries_completed == 0
    assert handle.boundaries_total == len(fuel_loss_inputs.interval.boundaries)
    assert handle.is_terminal is False
    assert handle.outcome is None
    assert handle.final is None
    # The identity is computable before anything has run, because it is a
    # property of what is being executed rather than of what happened.
    assert handle.inputs_identity


@pytest.mark.parametrize("batch", [1, 2, 7, 16, 1000])
def test_any_batching_produces_the_same_trajectory(
    fuel_loss_inputs: FrozenWorldInputs, batch: int
) -> None:
    """Criterion 2's claim, over five genuinely different call sequences.

    Compared by content digest AND by boundaries, because a digest over an empty
    prefix would agree with itself: the boundary count is asserted to be the
    whole interval first.
    """
    whole = execute(fuel_loss_inputs)

    handle = start(fuel_loss_inputs)
    calls = 0
    while not handle.is_terminal:
        handle.advance(batch)
        calls += 1
    stepped = handle.trajectory()

    assert len(whole.boundaries) == len(fuel_loss_inputs.interval.boundaries)
    assert calls >= 1
    assert stepped.content_digest == whole.content_digest
    assert stepped.boundaries == whole.boundaries
    assert stepped.applied_events == whole.applied_events
    assert stepped.bounded_transitions == whole.bounded_transitions
    assert stepped.handlers_exercised == whole.handlers_exercised


def test_the_world_so_far_is_readable_mid_flight(
    fuel_loss_inputs: FrozenWorldInputs,
) -> None:
    """The whole point of a handle.

    The boundaries a run has reached are a fact, and a kernel that only exposed
    them at a terminal outcome would make a stepped run unobservable - which is
    the same as not having stepped it.
    """
    handle = start(fuel_loss_inputs)
    handle.advance(3)

    assert handle.boundaries_completed == 3
    assert handle.final is not None
    assert handle.final.offset_minutes == 30
    assert len(handle.boundaries) == 3
    # And they are the first three the full execution produced.
    assert handle.boundaries == execute(fuel_loss_inputs).boundaries[:3]


def test_a_trajectory_is_refused_while_the_run_is_still_going(
    fuel_loss_inputs: FrozenWorldInputs,
) -> None:
    """A prefix may not pass for a whole result.

    `PrivateTrajectory` has no status for a run in progress, and inventing one
    would let a partial result be read as a finished one.
    """
    handle = start(fuel_loss_inputs)
    handle.advance(2)

    with pytest.raises(ExecutionStillRunning) as raised:
        handle.trajectory()

    assert "has not finished producing it" in str(raised.value)


def test_advancing_a_finished_run_advances_nothing_and_says_so(
    fuel_loss_inputs: FrozenWorldInputs,
) -> None:
    """A question with an answer, and the answer is none.

    What a control surface does about a repeated request is its own business and
    is decided by the boundary the request names; the kernel simply reports how
    far it got.
    """
    handle = start(fuel_loss_inputs)
    handle.run_to_end()
    covered = handle.boundaries_completed

    assert handle.advance(5) == 0
    assert handle.run_to_end() == 0
    assert handle.boundaries_completed == covered
    assert handle.outcome == "COMPLETED"


def test_advancing_past_the_end_stops_at_the_end(
    fuel_loss_inputs: FrozenWorldInputs,
) -> None:
    total = len(fuel_loss_inputs.interval.boundaries)
    handle = start(fuel_loss_inputs)

    assert handle.advance(total + 50) == total
    assert handle.boundaries_completed == total
    assert handle.is_terminal is True


def test_a_step_of_less_than_one_boundary_is_not_a_step(
    fuel_loss_inputs: FrozenWorldInputs,
) -> None:
    handle = start(fuel_loss_inputs)

    for boundaries in (0, -1):
        with pytest.raises(ValueError) as raised:
            handle.advance(boundaries)
        assert "is not advancing" in str(raised.value)


def test_the_version_guard_runs_before_anything_is_initialized(
    fuel_loss_inputs: FrozenWorldInputs,
) -> None:
    """Refused at construction, so no caller can hold a handle to it.

    A guard that only stopped the first `advance` would leave a handle in
    existence for a run this build may not execute, and every read on it would
    look like a legitimate inspection.
    """
    from dataclasses import replace

    earlier = replace(
        fuel_loss_inputs,
        execution_contract_version=EXECUTION_CONTRACT_VERSION - 1,
    )

    with pytest.raises(ExecutionContractIncompatible):
        Execution(earlier)

    with pytest.raises(ExecutionContractIncompatible):
        execute(earlier)
