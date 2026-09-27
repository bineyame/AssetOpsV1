"""The composition leaf: where a frozen product Draft becomes kernel input.

`host/` is the only place that may import both sides (v4 section 3.2, rules 3
and 4). Nothing imports it, which is what lets it know about a `SimulationRun`
and about `assetops_simulator` at once without either learning about the other.

What it does is narrow on purpose. It holds a frozen Draft and the versioned
definition that Draft names, and it produces the neutral `FrozenWorldInputs` a
kernel executes. It computes no physics, applies no bound and decides no
trajectory: every number it produces came from the frozen run, and the only
arithmetic it does is the one-time authored-float normalization the numeric
policy allows at the input boundary.

## What it refuses, and why each refusal is not a kernel failure

A `BLOCKED` Draft is not executed. There is no flag, no override and no partial
mode: `BLOCKED` is run setup's answer that these frozen inputs may not execute,
and a leaf that could talk a caller past it would make the status advisory. That
is a refusal here rather than an execution failure, because nothing executed.

A Draft frozen against a different execution contract is refused by
`refuse_incompatible_execution`, called before anything is built. The kernel
calls it again as its own first act, because a caller can hand a kernel inputs
this adapter never saw, and a guard that only one of two entrances has is a
guard with an entrance.

A Draft whose definition has drifted is refused as not reconstructible. The
values a run froze are the values it executes, so a changed parameter cannot
reach a trajectory; what a changed DOCUMENT can still change is structure, and
the adapter compares the two halves it can compare - the scenario version, and
the exact set of parameters the document declares against the set the run froze.
An entry added or removed since the freeze is caught. **An in-place edit that
moves an existing entry's offset or window length, at an unchanged scenario
version, is not**, because a Draft freezes resolved values and profile answers
rather than a copy of the timeline. That residual is recorded in
`.ai/MILESTONE_REVIEW_BACKLOG.md` rather than described as covered.

## Where a bound's number comes from

`D-2026-09-22-capacity-bound-source`: the declaration is the document's and the
value is the site's. `declared_bounds` is therefore right to report no upper
number for the tank volume, and this is the component entitled to hold both
halves - it reads the `bounds` block for WHICH state caps which, and the frozen
initialization input for HOW LARGE. `BOUND_CASE_BY_DECLARED_BOUND` names which
contract bound case a declared bound falls under, explicitly, and an unmapped
one is refused: deriving the case from a state key's spelling is the rule a
later author moves by renaming something.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from assetops_backend.runs.models import SimulationRun
from assetops_backend.runs.profiles import REPORTING_PATH_STATES
from assetops_backend.scenarios.models import ScenarioDefinition
from assetops_contracts.execution_contract import (
    BOUND_CASES,
    CANONICAL_UNITS,
    RATE_INTEGRALS,
    normalize_authored_float,
    refuse_incompatible_execution,
)
from assetops_contracts.trajectory import PrivateTrajectory
from assetops_contracts.world_inputs import (
    DeclaredBound,
    DeclaredCause,
    ForcingInput,
    FrozenInterval,
    FrozenWorldInputs,
    InitialValue,
)
from assetops_simulator.kernel.execute import execute
from assetops_simulator.kernel.model import ModelSpec
from assetops_simulator.packs.fuel import MINIMAL_FUEL_MODEL

#: Which contract bound case a declared bound falls under, keyed on the state
#: whose value supplies the limit and the direction of the limit.
#:
#: Explicit rather than inferred. The two strings on this one row happen to
#: coincide, and that is a naming coincidence rather than the rule: nothing here
#: matches a bound to a case by spelling, for the same reason a bound is a
#: declaration rather than a shared prefix between two state keys. A declared
#: bound with no row is refused, so a second bound cannot arrive with a policy
#: nobody chose.
BOUND_CASE_BY_DECLARED_BOUND: dict[tuple[str, str], str] = {
    ("fuel-tank-capacity", "UPPER"): "fuel-tank-capacity",
}

_POLICY_BY_CASE = {case.case_id: case.policy for case in BOUND_CASES}


class RunNotExecutable(Exception):
    """This Draft may not be executed, and nothing was executed.

    Distinct from every execution failure: an execution failure means a run
    started and stopped, and this means it never started.
    """


class FrozenRunNotReconstructible(Exception):
    """The run and the definition it names no longer describe one experiment."""


@dataclass(frozen=True)
class HostExecution:
    """One execution, with the inputs it was built from beside its result.

    Both halves, because criterion 2 is a claim about the pair: the same frozen
    inputs must produce the same canonical trajectory, and a caller that only
    got the trajectory back could not re-execute the inputs to check.
    """

    inputs: FrozenWorldInputs
    trajectory: PrivateTrajectory


def _fraction(value: float | None, where: str) -> Fraction:
    if value is None:
        raise FrozenRunNotReconstructible(
            f"{where} has no frozen value. A READY run answers every initial "
            "value it declares, so a run reaching here without one is a run "
            "whose status and whose content disagree."
        )
    return normalize_authored_float(float(value))


def _canonical(value: float, unit: str) -> tuple[Fraction, str, str]:
    canonical = CANONICAL_UNITS[unit]
    return (
        normalize_authored_float(value)
        * Fraction(canonical.numerator, canonical.denominator),
        canonical.canonical_unit,
        canonical.dimension,
    )


def frozen_world_inputs(
    run: SimulationRun, scenario: ScenarioDefinition
) -> FrozenWorldInputs:
    """Project one frozen Draft and its definition into kernel input."""
    if run.execution_status != "READY":
        raise RunNotExecutable(
            f"Run {run.run_id} is {run.execution_status} and carries "
            f"{len(run.blocking_reasons)} blocking reason(s): "
            + "; ".join(
                f"{reason.kind} about {reason.subject}"
                for reason in run.blocking_reasons
            )
            + ". A blocked Draft says these frozen inputs may not execute, and "
            "there is no mode in which they do."
        )

    identity = run.deterministic_identity
    refuse_incompatible_execution(identity.profiles.execution_contract_version)

    if scenario.scenario_id != identity.scenario.scenario_id:
        raise FrozenRunNotReconstructible(
            f"Run {run.run_id} froze scenario "
            f"{identity.scenario.scenario_id!r} and was handed "
            f"{scenario.scenario_id!r}."
        )
    if scenario.version.scenario_version != identity.scenario.scenario_version:
        raise FrozenRunNotReconstructible(
            f"Run {run.run_id} froze version "
            f"{identity.scenario.scenario_version} of "
            f"{scenario.scenario_id} and was handed version "
            f"{scenario.version.scenario_version}. A run executes the version "
            "it froze; reading a later one here would be reinterpretation "
            "wearing the old run's identity."
        )

    parameters = _parameters_by_id(scenario)
    frozen_values = {
        item.parameter_id: item.value
        for item in identity.scenario.resolved_parameters
    }
    frozen_initial = {
        item.parameter_id: item for item in identity.initialization_inputs
    }
    _refuse_drifted_parameter_sets(
        run, scenario, parameters, frozen_values, frozen_initial
    )

    unmodelled = tuple(
        sorted(item.addressed_key for item in run.unsupported_optional_inputs)
    )

    return FrozenWorldInputs(
        run_id=run.run_id,
        execution_contract_version=(
            identity.profiles.execution_contract_version
        ),
        site_id=identity.site.site_id,
        foundation_version=identity.site.foundation_version,
        scenario_id=identity.scenario.scenario_id,
        scenario_version=identity.scenario.scenario_version,
        model_profile_id=identity.profiles.model_profile_id,
        model_profile_version=identity.profiles.model_profile_version,
        publication_profile_id=identity.profiles.publication_profile_id,
        publication_profile_version=(
            identity.profiles.publication_profile_version
        ),
        interval=FrozenInterval(
            start_time=identity.interval.start_time,
            end_time=identity.interval.end_time,
            duration_minutes=identity.interval.duration_minutes,
            timestep_minutes=identity.interval.timestep_minutes,
        ),
        seed=identity.seed,
        initial_values=_initial_values(identity),
        bounds=_bounds(scenario, frozen_initial),
        forcings=_forcings(scenario, frozen_values),
        causes=_causes(scenario, parameters, frozen_values),
        unmodelled_addresses=unmodelled,
        reporting_path_addresses=_reporting_path_addresses(scenario),
        intervention_history=identity.intervention_history,
    )


def _parameters_by_id(scenario: ScenarioDefinition) -> dict[str, object]:
    found: dict[str, object] = {
        parameter.parameter_id: parameter
        for parameter in scenario.public_parameters
    }
    for entry in scenario.timeline:
        for parameter in entry.parameters:
            found[parameter.parameter_id] = parameter
    return found


def _refuse_drifted_parameter_sets(
    run: SimulationRun,
    scenario: ScenarioDefinition,
    parameters: dict[str, object],
    frozen_values: dict[str, float | str],
    frozen_initial: dict[str, object],
) -> None:
    """Refuse a definition whose parameter set is not the one the run froze.

    The half of definition drift a frozen run can see. A run freezes every
    parameter exactly once - as an initialization input or as a resolved
    parameter - so an entry added or removed since the freeze changes this set,
    and an edited VALUE cannot reach a trajectory at all because the frozen
    number is the one that executes.
    """
    declared = set(parameters)
    froze = set(frozen_values) | set(frozen_initial)
    added = sorted(declared - froze)
    removed = sorted(froze - declared)
    if added or removed:
        raise FrozenRunNotReconstructible(
            f"Run {run.run_id} froze {len(froze)} parameters of "
            f"{scenario.scenario_id} and the definition now declares "
            f"{len(declared)}. Added since the freeze: {added or 'none'}. "
            f"Gone since the freeze: {removed or 'none'}. A run executes the "
            "content it froze, so a definition that has gained or lost an "
            "entry is a different experiment under the same version."
        )


def _initial_values(identity: object) -> tuple[InitialValue, ...]:
    return tuple(
        InitialValue(
            address=item.addressed_key,
            state_key=item.state_key,
            scope=item.state_ref.scope,
            parameter_id=item.parameter_id,
            value=_fraction(
                item.canonical_value,
                f"the initial value of {item.addressed_key}",
            ),
            canonical_unit=item.canonical_unit,
            dimension=item.dimension,
            answered_by=item.answered_by,
        )
        for item in identity.initialization_inputs
    )


def _bounds(
    scenario: ScenarioDefinition, frozen_initial: dict[str, object]
) -> tuple[DeclaredBound, ...]:
    bounds: list[DeclaredBound] = []
    for parameter in _parameters_by_id(scenario).values():
        declaration = parameter.bounds
        if declaration is None:
            continue
        key = (parameter.state_ref.state_key, declaration.bound_kind)
        case_id = BOUND_CASE_BY_DECLARED_BOUND.get(key)
        if case_id is None:
            raise FrozenRunNotReconstructible(
                f"{scenario.scenario_id} declares a {declaration.bound_kind} "
                f"bound whose value comes from "
                f"{parameter.state_ref.state_key!r}, and no bound case says "
                "what a kernel does when it is reached. A bound with no policy "
                "is a silent clamp waiting to be written, so this is refused "
                "rather than defaulted."
            )

        frozen = frozen_initial.get(parameter.parameter_id)
        if frozen is None or frozen.canonical_value is None:
            if parameter.value is None or parameter.unit is None:
                raise FrozenRunNotReconstructible(
                    f"{scenario.scenario_id} declares a bound on "
                    f"{declaration.state_ref.addressed_key} and neither the "
                    f"definition nor the frozen run supplies a number for "
                    f"{parameter.parameter_id}."
                )
            value, unit, _ = _canonical(parameter.value, parameter.unit)
            source = parameter.addressed_key
        else:
            value = _fraction(
                frozen.canonical_value,
                f"the bound value for {declaration.state_ref.addressed_key}",
            )
            unit = frozen.canonical_unit
            source = frozen.addressed_key

        bounds.append(
            DeclaredBound(
                address=declaration.state_ref.addressed_key,
                kind=declaration.bound_kind,
                value=value,
                canonical_unit=unit,
                source_address=source,
                bound_case_id=case_id,
                policy=_POLICY_BY_CASE[case_id],
            )
        )
    return tuple(bounds)


def _forcings(
    scenario: ScenarioDefinition, frozen_values: dict[str, float | str]
) -> tuple[ForcingInput, ...]:
    forcings: list[ForcingInput] = []
    for entry in scenario.timeline:
        if entry.execution_role != "FORCING_INPUT":
            continue
        if entry.state_ref is not None and (
            entry.state_ref.state_key in REPORTING_PATH_STATES
        ):
            continue
        for parameter in entry.parameters:
            if parameter.execution_role != "FORCING_INPUT":
                continue
            if parameter.state_ref is None or parameter.unit is None:
                continue
            frozen = frozen_values.get(parameter.parameter_id)
            if not isinstance(frozen, (int, float)):
                continue
            value, unit, dimension = _canonical(float(frozen), parameter.unit)
            forcings.append(
                ForcingInput(
                    event_id=entry.event_id,
                    address=parameter.state_ref.addressed_key,
                    state_key=parameter.state_ref.state_key,
                    parameter_id=parameter.parameter_id,
                    value=value,
                    canonical_unit=unit,
                    dimension=dimension,
                    shape=entry.timing.shape,
                    offset_minutes=entry.offset_minutes,
                    duration_minutes=entry.timing.duration_minutes,
                    requirement=parameter.execution_requirement,
                )
            )
    return tuple(forcings)


def _causes(
    scenario: ScenarioDefinition,
    parameters: dict[str, object],
    frozen_values: dict[str, float | str],
) -> tuple[DeclaredCause, ...]:
    """Every declared change to a stock, with the quantity a run froze.

    A rate declared over a window is integrated here, at the input boundary and
    once, exactly as the document projection does it - the difference being that
    the number comes from the frozen run. How much of the result has moved part
    way through the window is the contract's ramp and the kernel's to apply.
    """
    causes: list[DeclaredCause] = []
    for entry in scenario.timeline:
        effect = entry.state_effect
        if effect is None or entry.state_ref is None:
            continue
        source_id = effect.quantity_parameter_id or effect.rate_parameter_id
        if source_id is None:
            continue
        parameter = parameters.get(source_id)
        if parameter is None or parameter.unit is None:
            continue
        frozen = frozen_values.get(source_id)
        if not isinstance(frozen, (int, float)):
            continue

        value, unit, dimension = _canonical(float(frozen), parameter.unit)
        if effect.rate_parameter_id is not None:
            # A rate declared over a window is integrated here, once, at the
            # input boundary: 14 L/h is 14/60 L/min and over 240 minutes that is
            # exactly 56 L, which is the number an author would write down. What
            # the kernel receives is the total, because how much of it has moved
            # part way through is the window ramp's answer and not a cause's.
            minutes = entry.timing.duration_minutes or 0
            value = value * Fraction(minutes)
            dimension = RATE_INTEGRALS[dimension]
            unit = _canonical_unit_of(dimension)

        causes.append(
            DeclaredCause(
                event_id=entry.event_id,
                address=entry.state_ref.addressed_key,
                state_key=entry.state_ref.state_key,
                direction=effect.direction,
                parameter_id=source_id,
                quantity=value,
                canonical_unit=unit,
                dimension=dimension,
                shape=entry.timing.shape,
                offset_minutes=entry.offset_minutes,
                duration_minutes=entry.timing.duration_minutes,
            )
        )
    return tuple(causes)


def _canonical_unit_of(dimension: str) -> str:
    """The canonical unit a dimension is measured in.

    Read from the conversion table rather than spelled here, so a dimension whose
    canonical unit changes changes in one place.
    """
    return next(
        canonical.canonical_unit
        for canonical in CANONICAL_UNITS.values()
        if canonical.dimension == dimension and canonical.numerator == 1
    )


def _reporting_path_addresses(scenario: ScenarioDefinition) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                entry.state_ref.addressed_key
                for entry in scenario.timeline
                if entry.state_ref is not None
                and entry.state_ref.state_key in REPORTING_PATH_STATES
            }
        )
    )


def run_to_end(
    run: SimulationRun,
    scenario: ScenarioDefinition,
    model: ModelSpec = MINIMAL_FUEL_MODEL,
) -> HostExecution:
    """Execute a Draft to the end of its interval and return both halves."""
    inputs = frozen_world_inputs(run, scenario)
    return HostExecution(inputs=inputs, trajectory=execute(inputs, model))
