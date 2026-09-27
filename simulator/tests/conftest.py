"""Frozen inputs the simulator suite starts from, and one session-wide guard.

The suite builds `FrozenWorldInputs` directly rather than through the host
adapter, for the reason the backend run-setup suite builds one request and breaks
it in exactly one way: a test about the ramp must not be able to pass because the
inputs were malformed in a second way the kernel reached first. The composing
suite in `host/tests` is where the same numbers are proved to come out of the
real product path.

`FUEL_LOSS_INPUTS` mirrors the shipped Fuel Loss Event against the shipped
hybrid template's Foundation - 500 L tank, 0.311 L/kWh generator - and
`host/tests/test_shipped_trajectory.py` asserts the two agree, so a drift in
either is a failure rather than a divergence nobody compares.

## The session guard

`test_every_execution_failure_kind_was_reached` at the end of this file is the
anti-vacuity check for the failure vocabulary. A vocabulary whose members cannot
be produced is a list of things that look protected, and this project has found
that shape in guard suites three slices running. It asserts against
`OBSERVED_KINDS`, which every `ExecutionFailure` construction adds to, so a kind
no test reaches fails the suite rather than passing unexamined.
"""

from __future__ import annotations

import os
import tempfile
from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest

from assetops_contracts.execution_contract import EXECUTION_CONTRACT_VERSION
from assetops_contracts.failures import EXECUTION_FAILURE_KINDS, OBSERVED_KINDS
from assetops_contracts.world_inputs import (
    DeclaredBound,
    DeclaredCause,
    ForcingInput,
    FrozenInterval,
    FrozenWorldInputs,
    InitialValue,
    UnmodelledInput,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
WORKSPACE_BASE_TEMP = REPOSITORY_ROOT / ".pytest-basetemp"

TANK = "fuel-tank-volume@fuel-tank"
CAPACITY = "fuel-tank-capacity@fuel-tank"
GENERATOR = "generator-output-power@generator"
COEFFICIENT = "generator-specific-fuel-consumption@generator"

#: The shipped scenario's own numbers, as exact rationals. Written as ratios
#: rather than decimals so a reader can see that nothing here was rounded on the
#: way in: 0.311 is 311/1000 and the kernel multiplies that, not a float near it.
STARTING_LEVEL = Fraction(430)
TANK_CAPACITY = Fraction(500)
SPECIFIC_CONSUMPTION = Fraction(311, 1000)
DISPATCHED_OUTPUT = Fraction(45)
VOLUME_REMOVED = Fraction(120)
VOLUME_DELIVERED = Fraction(300)


def _is_writable(directory: Path) -> bool:
    try:
        directory.mkdir(parents=True, exist_ok=True)
        probe = directory / f".write-probe-{os.getpid()}"
        probe.touch()
        probe.unlink()
    except OSError:
        return False
    return True


def pytest_configure(config: pytest.Config) -> None:
    """Keep pytest's temporary base somewhere this process can write.

    The same redirection `backend/tests/conftest.py` carries, for the same
    reason: a sandboxed agent cannot create `pytest-of-<user>` under the system
    temp directory, and a suite a reviewer cannot run is a suite whose numbers
    nobody independent has seen.
    """
    if config.option.basetemp is not None:
        return
    user = os.environ.get("USER") or os.environ.get("USERNAME") or "unknown"
    default = Path(tempfile.gettempdir()) / f"pytest-of-{user}"
    try:
        if _is_writable(default):
            return
    except OSError:
        pass
    if _is_writable(WORKSPACE_BASE_TEMP):
        config.option.basetemp = str(WORKSPACE_BASE_TEMP)


def initial_value(
    address: str,
    state_key: str,
    parameter_id: str,
    value: Fraction,
    unit: str,
    dimension: str,
    answered_by: str = "SCENARIO",
    scope: str = "COMPONENT",
) -> InitialValue:
    return InitialValue(
        address=address,
        state_key=state_key,
        scope=scope,
        parameter_id=parameter_id,
        value=value,
        canonical_unit=unit,
        dimension=dimension,
        answered_by=answered_by,
    )


def world_inputs(**overrides: Any) -> FrozenWorldInputs:
    """The shipped Fuel Loss Event's frozen content, or a variation of it."""
    base: dict[str, Any] = dict(
        run_id="run-" + "0" * 32,
        # Read from the contract rather than written as a literal. It was a 5,
        # the contract moved to 6 while fixing the returned defects, and the whole
        # suite went red without anybody noticing until a guard probe reported
        # CAUGHT against an already-failing suite. A fixture that pins a version
        # it does not own is a fixture that goes stale silently.
        execution_contract_version=EXECUTION_CONTRACT_VERSION,
        site_id="MG-001",
        foundation_version=1,
        scenario_id="fuel-loss-event",
        scenario_version=1,
        model_profile_id="minimal-fuel-tank",
        model_profile_version=1,
        publication_profile_id="simulator-lab-publication",
        publication_profile_version=1,
        interval=FrozenInterval(
            start_time="2026-09-21T00:00:00Z",
            end_time="2026-09-22T17:00:00Z",
            duration_minutes=2460,
            timestep_minutes=15,
        ),
        seed=20260927,
        initial_values=(
            initial_value(
                CAPACITY,
                "fuel-tank-capacity",
                "tank-capacity",
                TANK_CAPACITY,
                "L",
                "VOLUME",
                answered_by="SITE_FOUNDATION",
            ),
            initial_value(
                TANK,
                "fuel-tank-volume",
                "starting-fuel-level",
                STARTING_LEVEL,
                "L",
                "VOLUME",
            ),
            initial_value(
                COEFFICIENT,
                "generator-specific-fuel-consumption",
                "generator-specific-consumption",
                SPECIFIC_CONSUMPTION,
                "L/kWh",
                "VOLUME_PER_ENERGY",
                answered_by="SITE_FOUNDATION",
            ),
        ),
        bounds=(
            DeclaredBound(
                address=TANK,
                kind="UPPER",
                value=TANK_CAPACITY,
                canonical_unit="L",
                source_address=CAPACITY,
                bound_case_id="fuel-tank-capacity",
                policy="BOUNDED_AND_RECORDED",
            ),
        ),
        forcings=(
            ForcingInput(
                event_id="generator-run-window",
                address=GENERATOR,
                state_key="generator-output-power",
                parameter_id="dispatched-output",
                value=DISPATCHED_OUTPUT,
                canonical_unit="kW",
                dimension="POWER",
                shape="WINDOW",
                offset_minutes=1080,
                duration_minutes=240,
                requirement="REQUIRED",
            ),
        ),
        causes=(
            DeclaredCause(
                event_id="unaccounted-fuel-removal",
                address=TANK,
                state_key="fuel-tank-volume",
                direction="DECREASE",
                parameter_id="volume-removed",
                quantity=VOLUME_REMOVED,
                canonical_unit="L",
                dimension="VOLUME",
                shape="WINDOW",
                offset_minutes=1500,
                duration_minutes=45,
            ),
            DeclaredCause(
                event_id="scheduled-refuelling",
                address=TANK,
                state_key="fuel-tank-volume",
                direction="INCREASE",
                parameter_id="volume-delivered",
                quantity=VOLUME_DELIVERED,
                canonical_unit="L",
                dimension="VOLUME",
                shape="POINT",
                offset_minutes=2400,
                duration_minutes=None,
            ),
        ),
        # `(address, role)` pairs since the second review: a model can model a
        # state without modelling every role of it, and excluding the address
        # suppressed a role this model does support.
        unmodelled_inputs=(
            UnmodelledInput("site:plane-of-array-irradiance", "FORCING_INPUT"),
            UnmodelledInput("site:site-load-demand", "FORCING_INPUT"),
        ),
        reporting_path_addresses=("fuel-level-reporting-availability@fuel-tank",),
        intervention_history=(),
    )
    base.update(overrides)
    return FrozenWorldInputs(**base)


@pytest.fixture
def fuel_loss_inputs() -> FrozenWorldInputs:
    return world_inputs()


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Fail the session if any execution failure kind was never produced.

    Registered here rather than written as a test, because it has to run after
    every test in the session and a test cannot know it is last. It does not fire
    on a filtered run - `-k` or a single file legitimately reaches fewer kinds -
    so it checks only a full, otherwise-passing session.
    """
    if exitstatus != 0:
        return
    named_a_subset = session.config.option.keyword or any(
        not argument.startswith("-")
        for argument in session.config.invocation_params.args
    )
    if named_a_subset:
        return
    unreached = sorted(EXECUTION_FAILURE_KINDS - OBSERVED_KINDS)
    if unreached:
        session.exitstatus = 1
        raise pytest.UsageError(
            "These execution failure kinds were never produced by this "
            f"session: {unreached}. A vocabulary member no test can reach is a "
            "failure nothing has proved the kernel can raise. Reach it or "
            "remove it; do not leave it looking protected."
        )
