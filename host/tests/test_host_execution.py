"""A Draft created through the normal setup service, executed at host level."""

from __future__ import annotations

from fractions import Fraction

import pytest
from fixtures import draft, scenario

from execution_adapter import RunNotExecutable, run_to_end

TANK = "fuel-tank-volume@fuel-tank"


def test_the_shipped_ready_draft_executes() -> None:
    definition = scenario()
    run = draft(definition=definition)
    assert run.execution_status == "READY"

    executed = run_to_end(run, definition)

    assert executed.trajectory.outcome == "COMPLETED"
    assert executed.trajectory.is_complete
    assert executed.trajectory.boundary_at(0).stock(TANK) == Fraction(430)
