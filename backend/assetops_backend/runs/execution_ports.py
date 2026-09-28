"""The Lab execution port, owned by the product and implemented elsewhere.

The fourth port in this domain's neighbourhood and the first that is not
persistence. `runs/ports.py` is how a Draft is stored; this is how a Draft is
EXECUTED, and the two are deliberately separate seams because a store and a
kernel are different things to replace.

## What may and may not cross it

Two record families and no third. Going in: `SimulationRun`, which is the
product's own frozen record. Coming back: `LabProjection`, which lives in the
dependency-neutral contracts. Nothing simulator-shaped appears in either
direction - no `PrivateTrajectory`, no `BoundaryState`, no `ModelSpec`, no
`DeviceObservation` - and that is the criterion "the backend consumes the neutral
port/projection contract, not simulator types" as a signature rather than as a
rule somebody remembers.

`tools/checks/dependency-direction.ps1` is what makes it structural: the simulator
package is unreachable from this tree by any spelling, so a route that wanted a
trajectory could not name its type. The port could not be widened to carry one
without the build failing.

(That guard scans for an import statement with a pattern that also matches the
phrase in a sentence, so this paragraph says which package it means without
writing the line the guard is looking for. The neutral contracts' half of the
same check is anchored to the start of a line and does not have the problem;
these three are older. It is a false positive rather than a hole - a guard that
is too eager is safe - and it is recorded in the backlog rather than fixed here,
because loosening a dependency check in the slice that tripped over it is the
one edit this file's own header forbids.)

## Why the product cannot build an implementation of it

`host/` is the only place that may import both sides, and nothing may import
`host/`. So the product declares what it needs here and receives it by injection,
exactly as it does for every store. The composition happens in the leaf's own
application module, which is the process entry point for a build that executes.

A build serving `assetops_backend.main:app` alone therefore has no execution port
and says so: the routes exist while the Lab gate is open and answer
`EXECUTION_NOT_COMPOSED`. That is one honest state rather than two serving shapes
whose route sets differ, which would make the gate's own test compare three things
instead of two.

## The refusal vocabulary is not this module's

A refused control speaks `LAB_CONTROL_REFUSALS` in the neutral contracts, because
both sides need it: the leaf raises `LabControlRefused` and a route renders it.
Run setup's `RunSetupRefused`, a Draft's `BLOCKING_REASON_KINDS` and an execution
failure's `EXECUTION_FAILURE_KINDS` remain three other vocabularies, and a
composing test asserts all four are pairwise disjoint.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from assetops_backend.runs.models import SimulationRun
from assetops_contracts.lab_projection import LabProjection


@runtime_checkable
class LabExecutionPort(Protocol):
    """Execute, step and inspect one frozen Draft, in the gated Lab only.

    Every method may raise `assetops_contracts.lab_projection.LabControlRefused`,
    which means the request was judged and NOTHING was executed: no boundary
    advanced and no artifact changed. An execution that started and stopped is not
    a refusal - it comes back as a `FAILED` projection carrying the failure - and
    keeping the two apart is criterion 4's "start/step/run-to-end failures are
    visible separately from setup eligibility".
    """

    def projection(self, run: SimulationRun) -> LabProjection:
        """Where this Draft's execution is, without changing it.

        Answers for a Draft nothing has executed, for one in flight, for one that
        finished or failed, and for one whose live handle is gone. Those are four
        different facts and the projection's status is which.
        """
        ...

    def start(self, run: SimulationRun) -> LabProjection:
        """Begin an execution without advancing it.

        Separate from stepping so that starting and stepping are two observable
        acts. Raises `LabControlRefused` for a `BLOCKED` Draft, for one frozen
        against another contract version, for one already terminal, and for one
        whose earlier execution was interrupted.
        """
        ...

    def step(
        self, run: SimulationRun, *, boundaries: int, from_boundary: int
    ) -> LabProjection:
        """Advance a started execution by `boundaries` instants.

        `from_boundary` is the position the caller believes the run is at, and it
        is what stops a resubmitted control stepping twice: a request naming a
        boundary the run has left is refused without advancing anything.
        """
        ...

    def run_to_end(self, run: SimulationRun) -> LabProjection:
        """Advance a started execution until its interval is covered."""
        ...
