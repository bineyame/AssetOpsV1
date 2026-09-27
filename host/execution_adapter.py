"""The composition leaf: where a frozen product Draft becomes kernel input.

`host/` is the only place that may import both sides (v4 section 3.2, rules 3
and 4). Nothing imports it, which is what lets it know about a `SimulationRun`
and about `assetops_simulator` at once without either learning about the other.

## It takes the run and nothing else, and that is the whole of R1's fix

This module used to take a `ScenarioDefinition` beside the run and project the
causes, the forcings and the bounds out of it. T021's independent review
reproduced what that allows: execute the ordinary shipped Draft, then execute the
SAME persisted run against the same document version with one offset moved from
1500 to 1515, and the tank at 1515 goes from 334.02 L to 374.02 L. Both complete.
Nothing in the run has changed.

Comparing parameter identities, which is what this did, cannot see that - and an
offset is a causally effective number exactly as a quantity is. So run setup now
freezes the whole causal projection on the run (`FrozenCause`, `FrozenForcing`,
`FrozenDeclaredBound`, `FrozenReportingPathCondition`), and `frozen_world_inputs`
takes one argument. There is no parameter through which a different experiment
can arrive, which is a stronger statement than any comparison this module could
have made.

What is left here is a mapping: frozen product records to neutral ones, with the
one-time authored-float normalization the numeric policy allows at the input
boundary and no other arithmetic. It computes no physics, applies no bound and
decides no trajectory.

**One parameter survives and it is checked rather than trusted.** A caller may
supply the `ModelSpec` to execute against, because a model is code rather than
frozen content and there is no catalog of them here. A model is part of the
experiment, so `run_to_end` refuses one whose identity is not the profile identity
the run froze: executing a run against a model it did not select would be the same
defect as executing it against a document it did not freeze, one noun along.

What the check cannot see, stated rather than implied: a model carrying the frozen
identity and different BEHAVIOUR is still injectable. That is deliberate and it is
what the conformance test and the guard probes rely on - both substitute a model at
the same identity on purpose. A product caller resolves the model from a catalog
keyed on the frozen identity, which is T022's, and this refusal is what makes that
resolution checkable rather than assumed.

## What it refuses, and why each refusal is not an execution failure

A `BLOCKED` Draft is not executed. There is no flag, no override and no partial
mode: `BLOCKED` is run setup's answer that these frozen inputs may not execute,
and a leaf that could talk a caller past it would make the status advisory. That
is a refusal here rather than an execution failure, because nothing executed.

A Draft frozen against a different execution contract is refused by
`refuse_incompatible_execution`, called before anything is built. The kernel
calls it again as its own first act, because a caller can hand a kernel inputs
this adapter never saw, and a guard that only one of two entrances has is a guard
with an entrance. It is also what makes the frozen projection safe to default to
empty on readback: a run without one is a run at an earlier version, and such a
run is never executed.

Two answers for one address are refused rather than resolved. A stored document
can carry two initialization rows for one state, and building a map from it made
the last row silently authoritative - which T021's review found and carried. A
frozen run that answers one address twice is not a run whose experiment is
determined, so it is refused here, where both rows are still visible.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from assetops_backend.runs.models import SimulationRun
from assetops_contracts.execution_contract import (
    BOUND_CASES,
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
    UnmodelledInput,
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
    """The frozen run does not determine one experiment."""


@dataclass(frozen=True)
class HostExecution:
    """One execution, with the inputs it was built from beside its result.

    Both halves, because criterion 2 is a claim about the pair: the same frozen
    inputs must produce the same canonical trajectory, and a caller that only got
    the trajectory back could not re-execute the inputs to check.
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


def frozen_world_inputs(run: SimulationRun) -> FrozenWorldInputs:
    """Project one frozen Draft into kernel input, from the run alone."""
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

    initial_values = _initial_values(run)
    # The ROLE travels with the address. `UnsupportedOptionalInput` has carried
    # both since T020A1, and dropping the role here made the exclusion suppress
    # roles the model does support.
    unmodelled = tuple(
        sorted(
            (
                UnmodelledInput(
                    address=item.addressed_key, role=item.execution_role
                )
                for item in run.unsupported_optional_inputs
            ),
            key=lambda item: (item.address, item.role),
        )
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
        initial_values=initial_values,
        bounds=_bounds(run, initial_values),
        forcings=_forcings(run),
        causes=_causes(run),
        unmodelled_inputs=unmodelled,
        reporting_path_addresses=tuple(
            sorted(
                {
                    condition.addressed_key
                    for condition in identity.reporting_path_conditions
                }
            )
        ),
        intervention_history=identity.intervention_history,
    )


def _refuse_two_answers(run: SimulationRun, kind: str, keys: list[str]) -> None:
    """Refuse a frozen run that answers one address twice.

    A map built from such a run makes the last row authoritative, silently. That
    is not a defect a kernel can notice, because by then there is one answer; it
    has to be caught where both rows are still visible. Ordinary setup cannot
    produce one - the scenario parser refuses duplicate initializers - so what
    this catches is a stored document somebody wrote or edited by hand, which is
    the same boundary every other check in `runs/parsing.py` exists for.
    """
    seen: set[str] = set()
    duplicated: set[str] = set()
    for key in keys:
        if key in seen:
            duplicated.add(key)
        seen.add(key)
    if duplicated:
        raise FrozenRunNotReconstructible(
            f"Run {run.run_id} carries more than one frozen {kind} for "
            f"{sorted(duplicated)}. One address has one answer, or the "
            "experiment being executed depends on which row was read last."
        )


def _initial_values(run: SimulationRun) -> tuple[InitialValue, ...]:
    frozen = run.deterministic_identity.initialization_inputs
    _refuse_two_answers(
        run, "initial value", [item.addressed_key for item in frozen]
    )
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
        for item in frozen
    )


def _bounds(
    run: SimulationRun, initial_values: tuple[InitialValue, ...]
) -> tuple[DeclaredBound, ...]:
    """Each frozen bound relationship, with the number the run froze for it.

    `D-2026-09-22-capacity-bound-source`: the declaration is the document's and
    the value is the site's. Both halves are frozen now - the relationship as a
    `FrozenDeclaredBound` and the number as the initialization input it points at
    - so this pairs two frozen records rather than a frozen record and a live
    document.
    """
    by_address = {item.address: item for item in initial_values}
    bounds: list[DeclaredBound] = []
    for declaration in run.deterministic_identity.declared_bounds:
        key = (declaration.source_state_ref.state_key, declaration.bound_kind)
        case_id = BOUND_CASE_BY_DECLARED_BOUND.get(key)
        if case_id is None:
            raise FrozenRunNotReconstructible(
                f"Run {run.run_id} froze a {declaration.bound_kind} bound whose "
                f"value comes from {declaration.source_state_ref.state_key!r}, "
                "and no bound case says what a kernel does when it is reached. "
                "A bound with no policy is a silent clamp waiting to be "
                "written, so this is refused rather than defaulted."
            )
        source = by_address.get(declaration.source_addressed_key)
        if source is None:
            raise FrozenRunNotReconstructible(
                f"Run {run.run_id} froze a bound on "
                f"{declaration.addressed_key} sourced from "
                f"{declaration.source_addressed_key}, and froze no initial "
                "value for that address. A bound relationship with no number "
                "behind it is a limit nobody stated."
            )
        bounds.append(
            DeclaredBound(
                address=declaration.addressed_key,
                kind=declaration.bound_kind,
                value=source.value,
                canonical_unit=source.canonical_unit,
                source_address=declaration.source_addressed_key,
                bound_case_id=case_id,
                policy=_POLICY_BY_CASE[case_id],
            )
        )
    return tuple(bounds)


def _forcings(run: SimulationRun) -> tuple[ForcingInput, ...]:
    return tuple(
        ForcingInput(
            event_id=item.event_id,
            address=item.addressed_key,
            state_key=item.state_key,
            parameter_id=item.parameter_id,
            value=_fraction(
                item.canonical_value, f"the forcing {item.parameter_id}"
            ),
            canonical_unit=item.canonical_unit,
            dimension=item.dimension,
            shape=item.timing_shape,
            offset_minutes=item.offset_minutes,
            duration_minutes=item.duration_minutes,
            requirement=item.execution_requirement,
        )
        for item in run.deterministic_identity.forcings
    )


def _causes(run: SimulationRun) -> tuple[DeclaredCause, ...]:
    """Every frozen change to a stock, with the quantity the run froze.

    A rate declared over a window was integrated once, at the input boundary, by
    run setup. How much of the result has moved part way through is the
    contract's ramp and the kernel's to apply.
    """
    return tuple(
        DeclaredCause(
            event_id=item.event_id,
            address=item.addressed_key,
            state_key=item.state_key,
            direction=item.direction,
            parameter_id=item.parameter_id,
            quantity=_fraction(
                item.canonical_value, f"the cause {item.event_id}"
            ),
            canonical_unit=item.canonical_unit,
            dimension=item.dimension,
            shape=item.timing_shape,
            offset_minutes=item.offset_minutes,
            duration_minutes=item.duration_minutes,
        )
        for item in run.deterministic_identity.causes
    )


def refuse_a_model_the_run_did_not_select(
    run: SimulationRun, model: ModelSpec
) -> None:
    """Refuse a model whose identity is not the one the run froze.

    A run freezes WHICH model profile answered and at which version, precisely so
    that the same run is reproducible without the profile catalog being frozen with
    it. Executing it against a model of another identity would discard that, and it
    is the same defect as executing it against a document it did not freeze.

    It checks the identity and cannot check the behaviour. A model carrying the
    frozen identity and different code is still injectable, which the conformance
    test and the guard probes both do deliberately.
    """
    frozen = run.deterministic_identity.profiles
    if (
        model.model_profile_id == frozen.model_profile_id
        and model.model_profile_version == frozen.model_profile_version
    ):
        return
    raise FrozenRunNotReconstructible(
        f"Run {run.run_id} froze model profile {frozen.model_profile_id} version "
        f"{frozen.model_profile_version} and was handed "
        f"{model.model_profile_id} version {model.model_profile_version}. A run "
        "executes the model it selected; executing it against another is "
        "reinterpretation wearing the old run's identity."
    )


def run_to_end(
    run: SimulationRun, model: ModelSpec = MINIMAL_FUEL_MODEL
) -> HostExecution:
    """Execute a Draft to the end of its interval and return both halves."""
    refuse_a_model_the_run_did_not_select(run, model)
    inputs = frozen_world_inputs(run)
    return HostExecution(inputs=inputs, trajectory=execute(inputs, model))
