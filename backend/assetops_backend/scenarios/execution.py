"""Projecting a scenario document, against the contract the kernel executes.

This module used to hold two different things: the versioned rules a conforming
implementation obeys, and the projections of a document that report what it
declares. T021 separated them, because the first conforming kernel lives in
`assetops_simulator` and `simulator/` may not import `assetops_backend` at all
(v4 section 3.2, and `.ai/ARCHITECTURE.md` Execution Composition And Truth
Barrier).

The rules moved, unchanged, to `assetops_contracts.execution_contract` -
canonical units, half-open dispatch, the boundary cycle, what a reading
timestamped `T` describes, and what each bound policy commits a kernel to - and
are re-exported below so a product caller still reads one module and the
scenario detail screen still renders those objects rather than copies of them.
Two new functions arrived with them: `step_concerns_window` and
`window_share_of_step`, the `window-overlap` predicate and the `window-ramp`
share as executable arithmetic beside the sentences that publish them.

What stayed is what needs a `ScenarioDefinition`:

What stays is `initialization_inputs` and `state_transition_inputs`, which report
the initial world values and the declared changes a document carries. Both are
reports about a DOCUMENT: neither has a clock, a timestep, a seed, a state record
or an event cursor, and nothing that executes calls either.

## What left in T022, and why the module got shorter rather than longer

`reconcile_reported_observations` and everything that existed for it -
`ObservationReconciliation`, `RECONCILIATION_STATES`, the reason strings,
`unaccounted_observations`, `declared_bounds` and
`IMPLICIT_LOWER_BOUND_DIMENSIONS` - are gone under
`D-2026-09-22-reconciliation-panel-retirement`. The comment where they used to
be, at the end of this module, records the reasoning and the one name collision
worth not tripping over.

The short version: it compared an authored reading against the value a document's
own declared causes reach, that comparison has been a partial account since the
consumption coefficient moved to the machine, and a run now generates the reading
from a world a kernel computed. The stronger answer arrived, so the weaker one
went with the panel that showed it.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from assetops_contracts.execution_contract import (
    BOUNDARY_CYCLE,
    CanonicalValueNotRepresentable,
    BOUND_CASES,
    BOUND_POLICIES,
    BOUND_POLICY_STATEMENTS,
    CANONICAL_UNITS,
    DISPATCH_RULES,
    DURATION_UNIT_SPELLINGS,
    EXECUTION_CONTRACT_VERSION,
    NON_NEGATIVE_DIMENSIONS,
    NUMERIC_POLICY,
    NUMERIC_POLICY_VERSION,
    OBSERVATION_RULES,
    RATE_INTEGRALS,
    READING_CLASSES,
    REPORTING_RULES,
    BoundaryPhase,
    BoundCase,
    CanonicalUnit,
    DispatchRule,
    ExecutionContractIncompatible,
    ObservationRule,
    ReportingRule,
    _exact,
    cadence_is_expressible,
    canonical_fraction,
    canonical_quantity,
    frozen_canonical_value,
    normalize_authored_float,
    overlap_minutes,
    point_due_at,
    refuse_incompatible_execution,
    sample_due_at,
    step_concerns_window,
    steps_concerning_window,
    window_share_of_step,
    window_span,
)
from assetops_backend.scenarios.models import (
    STATE_CHANGING_ROLES,
    ScenarioDefinition,
    ScenarioParameter,
    TimelineEntry,
)
from assetops_backend.state_refs import StateRef

#: Re-exported so a product caller reads one module. The names are the contract
#: module's objects and not copies of them: `is` holds, which is what keeps the
#: screen, the payload and the kernel reading one answer.
__all__ = [
    "BOUNDARY_CYCLE",
    "BOUND_CASES",
    "BOUND_POLICIES",
    "BOUND_POLICY_STATEMENTS",
    "CANONICAL_UNITS",
    "DISPATCH_RULES",
    "DURATION_UNIT_SPELLINGS",
    "EXECUTION_CONTRACT_VERSION",
    "NON_NEGATIVE_DIMENSIONS",
    "NUMERIC_POLICY",
    "NUMERIC_POLICY_VERSION",
    "OBSERVATION_RULES",
    "RATE_INTEGRALS",
    "READING_CLASSES",
    "REPORTING_RULES",
    "BoundaryPhase",
    "BoundCase",
    "CanonicalUnit",
    "CanonicalValueNotRepresentable",
    "DispatchRule",
    "ExecutionContractIncompatible",
    "ObservationRule",
    "ReportingRule",
    "cadence_is_expressible",
    "canonical_fraction",
    "canonical_quantity",
    "frozen_canonical_value",
    "normalize_authored_float",
    "overlap_minutes",
    "point_due_at",
    "refuse_incompatible_execution",
    "sample_due_at",
    "step_concerns_window",
    "steps_concerning_window",
    "window_share_of_step",
    "window_span",
    "InitializationInput",
    "StateTransitionInput",
    "initialization_inputs",
    "state_transition_inputs",
]


# --- Initialization and the private-state transition surface ----------------


@dataclass(frozen=True)
class InitializationInput:
    """One initial world value, with the owner that answers for it.

    `value` and `canonical_value` are `None` exactly when the declared owner
    is `SITE_FOUNDATION`, because such a parameter states no number
    (`D-2026-09-22-foundation-value-declaration`). This record is a projection
    of the document and the document genuinely does not know the number: the
    Site does, and run setup is the component entitled to hold a document and
    a resolved Site together.

    `unit` and `dimension` are present either way. What kind of quantity the
    state is remains the scenario's to declare, and it is what run setup
    checks the Foundation's own property against.
    """

    parameter_id: str
    display_name: str
    state_ref: StateRef
    owner: str
    value: float | None
    unit: str
    canonical_value: float | None
    canonical_unit: str
    dimension: str

    @property
    def state_key(self) -> str:
        """The semantic state, without its selector."""
        return self.state_ref.state_key

    @property
    def addressed_key(self) -> str:
        """The canonical spelling of the address this concerns."""
        return self.state_ref.addressed_key


@dataclass(frozen=True)
class StateTransitionInput:
    """One declared change to private world state, and where it came from."""

    event_id: str
    state_ref: StateRef
    direction: str
    parameter_id: str
    canonical_value: float
    canonical_unit: str
    dimension: str
    #: The volume, energy or other accumulated quantity this transition
    #: amounts to once a rate has been applied across its window. Equal to
    #: `canonical_value` for a quantity effect.
    applied_value: float
    applied_unit: str
    applied_dimension: str
    #: Where the transition begins, as an offset from the interval start.
    starts_at_offset: int
    #: The offset at which the transition is complete: its own offset for a
    #: point, the end of its window otherwise. `None` for an interval-wide
    #: entry, which never completes inside the scenario.
    complete_at_offset: int | None

    @property
    def state_key(self) -> str:
        """The semantic state, without its selector."""
        return self.state_ref.state_key

    @property
    def addressed_key(self) -> str:
        """The canonical spelling of the address this concerns."""
        return self.state_ref.addressed_key


def _all_parameters(scenario: ScenarioDefinition) -> dict[str, ScenarioParameter]:
    """Every public parameter in the document, by identity.

    Parameter identities are unique across the whole document, enforced by the
    parser, so a state effect that names one names exactly one thing.
    """
    found: dict[str, ScenarioParameter] = {
        parameter.parameter_id: parameter
        for parameter in scenario.public_parameters
    }
    for entry in scenario.timeline:
        for parameter in entry.parameters:
            found[parameter.parameter_id] = parameter
    return found


def initialization_inputs(
    scenario: ScenarioDefinition,
) -> tuple[InitializationInput, ...]:
    """Every initial world value the scenario declares, with its owner.

    Two conditions, and the second is deliberately not a restatement of a
    parser rule. A parameter appears here only if its ownership says it
    initializes AND its role is one of `STATE_CHANGING_ROLES`. The parser
    refuses the combination that would make the second condition matter, so
    this is the layer that keeps holding if that refusal is ever loosened -
    which is exactly what the T018 review found had happened by accident for a
    forcing input.

    A reported observation cannot reach here at all: it carries no ownership
    record, which is the structural form of "a recording may not hide
    initialization".
    """
    inputs: list[InitializationInput] = []

    for parameter in _all_parameters(scenario).values():
        ownership = parameter.ownership
        if ownership is None or not ownership.initializes:
            continue
        if parameter.execution_role not in STATE_CHANGING_ROLES:
            continue
        if parameter.state_ref is None or parameter.unit is None:
            continue
        # A Foundation-owned parameter states no number, by construction
        # (`D-2026-09-22-foundation-value-declaration`), and it still declares
        # an initial world value: the need is what it declares, and run setup
        # resolves the answer from the Site through the profile's binding.
        # Skipping it here on the old float filter would have made the
        # decision's own parameters vanish from initialization, which is the
        # opposite of what it settles.
        if parameter.value is None:
            if ownership.owner != "SITE_FOUNDATION":
                continue
            canonical_value = None
            _, canonical_unit, dimension = canonical_quantity(
                0.0, parameter.unit
            )
            value: float | None = None
        elif isinstance(parameter.value, float):
            value = parameter.value
            canonical_value, canonical_unit, dimension = canonical_quantity(
                parameter.value, parameter.unit
            )
        else:
            continue

        inputs.append(
            InitializationInput(
                parameter_id=parameter.parameter_id,
                display_name=parameter.display_name,
                state_ref=parameter.state_ref,
                owner=ownership.owner,
                value=value,
                unit=parameter.unit,
                canonical_value=canonical_value,
                canonical_unit=canonical_unit,
                dimension=dimension,
            )
        )

    # Sorted by ADDRESS, so two components of one type hold a stable and
    # distinguishable order rather than colliding on one semantic key.
    return tuple(sorted(inputs, key=lambda entry: entry.addressed_key))


def state_transition_inputs(
    scenario: ScenarioDefinition,
) -> tuple[StateTransitionInput, ...]:
    """Every declared change to private world state, in authored order.

    Built only from `CAUSAL_INPUT` entries carrying a state effect. Nothing
    else in the document can reach this list, because no other entry kind has a
    field a state effect could be written in.
    """
    parameters = _all_parameters(scenario)
    transitions: list[StateTransitionInput] = []

    for entry in scenario.timeline:
        effect = entry.state_effect
        if effect is None or entry.state_ref is None:
            continue

        source_id = effect.quantity_parameter_id or effect.rate_parameter_id
        if source_id is None:
            continue
        parameter = parameters.get(source_id)
        if (
            parameter is None
            or parameter.unit is None
            or not isinstance(parameter.value, float)
        ):
            continue

        canonical_value, canonical_unit, dimension = canonical_quantity(
            parameter.value, parameter.unit
        )

        if effect.rate_parameter_id is not None:
            duration = entry.timing.duration_minutes or 0
            applied_value = float(
                _exact(canonical_value) * Fraction(duration)
            )
            applied_dimension = RATE_INTEGRALS[dimension]
            applied_unit = CANONICAL_UNITS[
                _canonical_unit_name(applied_dimension)
            ].canonical_unit
        else:
            applied_value = canonical_value
            applied_unit = canonical_unit
            applied_dimension = dimension

        transitions.append(
            StateTransitionInput(
                event_id=entry.event_id,
                state_ref=entry.state_ref,
                direction=effect.direction,
                parameter_id=parameter.parameter_id,
                canonical_value=canonical_value,
                canonical_unit=canonical_unit,
                dimension=dimension,
                applied_value=applied_value,
                applied_unit=applied_unit,
                applied_dimension=applied_dimension,
                starts_at_offset=entry.offset_minutes,
                complete_at_offset=_complete_at(entry),
            )
        )

    return tuple(transitions)


def _canonical_unit_name(dimension: str) -> str:
    """The authored unit whose canonical form represents a dimension."""
    for unit, canonical in CANONICAL_UNITS.items():
        if canonical.dimension == dimension and canonical.numerator == 1:
            return unit
    raise KeyError(dimension)


def _complete_at(entry: TimelineEntry) -> int | None:
    if entry.timing.shape == "POINT":
        return entry.offset_minutes
    if entry.timing.shape == "WINDOW":
        return entry.offset_minutes + (entry.timing.duration_minutes or 0)
    return None


# --- What used to be here, and where it went --------------------------------
#
# `reconcile_reported_observations`, `ObservationReconciliation`,
# `RECONCILIATION_STATES`, their seven reason strings, `unaccounted_observations`,
# `declared_bounds` and `IMPLICIT_LOWER_BOUND_DIMENSIONS` were all here until
# T022, and they left together under
# `D-2026-09-22-reconciliation-panel-retirement`.
#
# `D-2026-09-21-specification-reference-implementation` said the reference
# implementation stops being an authority the moment a kernel exists to be
# compared against, and that it goes when its last product-path caller goes. T021
# built the kernel and this slice removed the caller - the scenario detail
# screen's reconciliation panel - so both conditions are met at once.
#
# The narrower question it answered was honest and is now answered better. It
# compared an authored reading against the value the DOCUMENT's own declared
# causes reach, which after T020A is a partial account by construction: the
# document no longer declares what the generator burns, so it reported 310 L
# against a world holding 254.02 L and the 55.98 L between them was the model
# law's. A run now generates the reading from the world a kernel computed, and the
# Lab shows the true value, the reported value and the reason there is no reading
# side by side. Keeping the subtraction would have meant offering the weaker of
# two available answers.
#
# `declared_bounds` and `IMPLICIT_LOWER_BOUND_DIMENSIONS` had exactly one caller
# between them and it was the reconciler. The floor they injected is now the fuel
# model's own - `STOCK_HANDLER.floor` in `assetops_simulator.packs.fuel`, with the
# bound case that says what happens when it is reached - which is where
# `D-2026-09-21-physical-property-ownership` says a model rule belongs. Nothing
# about a validation layer asserting that volume is non-negative survives.
#
# **Nothing here is the frozen run's `declared_bounds`.** That is a different
# thing with the same name: a tuple of `FrozenDeclaredBound` on a run's
# deterministic identity, which run setup writes, provenance reads and the host
# adapter turns into the bounds a kernel executes against. It is load-bearing and
# untouched.
