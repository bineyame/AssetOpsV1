"""The private trajectory a kernel produces, and what binds its identity.

Private truth, in the sense v4 section 21 means: it holds the actual stock at
every boundary, the flows the world accepted, the events applied, the bounded
transitions and the failure if there was one. None of it is product evidence and
none of it may reach normal ingestion. It lives here rather than in the
simulator package because both sides of the barrier have to agree what one is -
the host adapter returns one and the Lab will render one - and neither may
import the other.

## What the identity binds, and why each part is in it

`inputs_identity` is the digest of the frozen inputs, the kernel version, the
model identity, the numeric policy and the execution contract version. Two runs
agreeing on all of those are the same experiment, so they must produce the same
trajectory; two runs differing in any of them are not, so they are allowed to
differ. A kernel version outside the digest would let a kernel change and a
trace still claim the old identity, which is the situation
`D-2026-09-21-causal-runtime-before-golden-traces` makes a provenance mismatch
refuse playback for.

`run_id` is deliberately NOT in it, for the same reason it is not in the run's
deterministic identity: two Drafts set up identically are two runs of one
experiment, and an identity carrying the run's own name would answer nothing.

`content_digest` is the digest of the canonical trajectory itself. The two
together are the test criterion 2 asks for: the same identity must produce the
same canonical trajectory, which is only a claim if both numbers exist and are
compared.

## A partial result says so in its own outcome

`outcome` is `COMPLETED` or `FAILED` and the constructor refuses the two
combinations that would let a partial run pass for a whole one: `COMPLETED`
with a failure attached, and `FAILED` with none. `is_complete` reads the
outcome rather than counting boundaries, because a run that failed at the last
boundary has as many boundaries as one that finished.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction

from assetops_contracts.failures import ExecutionFailure
from assetops_contracts.identity import identity_digest

#: The two ways an execution ends. There is no third: a run that is still
#: running is a handle rather than a trajectory, and this build runs to the end
#: or stops.
EXECUTION_OUTCOMES = frozenset({"COMPLETED", "FAILED"})

#: The trace record kinds this kernel produces, a subset of v4 section 21's
#: list. The absent ones are absent because nothing here makes them:
#: `CONTROL_INTENT` and `ACCEPTED_FLOW` need a controller, `DISCRETE_TRANSITION`
#: needs a discrete state, and `DEVICE_OBSERVATION` and `GATEWAY_PUBLICATION`
#: need the observation transform and the gateway. A kind listed with no
#: producer would be a claim that this kernel does more than it does.
TRACE_RECORD_KINDS = frozenset(
    {"STEP", "EVENT_APPLIED", "BOUNDED_TRANSITION", "FAILURE"}
)


@dataclass(frozen=True)
class AppliedEvent:
    """One declared cause, as much of it as one step or instant applied.

    `share` is the portion of the entry this record accounts for: exactly one
    for a point, and the window ramp's share of the span for a step of a
    window. `accepted` is what the stock took and `refused` is what a bound
    would not let in, so `accepted + refused == declared` holds exactly and the
    conservation check has both halves to compare.
    """

    event_id: str
    address: str
    direction: str
    at_offset_minutes: int
    share: Fraction
    declared: Fraction
    accepted: Fraction
    refused: Fraction
    phase_id: str

    def as_fields(self) -> tuple[object, ...]:
        return (
            self.event_id,
            self.address,
            self.direction,
            self.at_offset_minutes,
            self.share,
            self.declared,
            self.accepted,
            self.refused,
            self.phase_id,
        )


@dataclass(frozen=True)
class BoundedTransition:
    """A transition applied up to a bound, carrying the quantity refused.

    `BOUNDED_AND_RECORDED` is only distinguishable from a silent clamp by this
    record existing, so it carries the quantity that could not be accepted
    rather than only the value the stock reached.
    """

    address: str
    at_offset_minutes: int
    bound_case_id: str
    bound_kind: str
    bound_value: Fraction
    requested: Fraction
    accepted: Fraction
    refused: Fraction
    event_ids: tuple[str, ...]

    def as_fields(self) -> tuple[object, ...]:
        return (
            self.address,
            self.at_offset_minutes,
            self.bound_case_id,
            self.bound_kind,
            self.bound_value,
            self.requested,
            self.accepted,
            self.refused,
            self.event_ids,
        )


@dataclass(frozen=True)
class BoundaryState:
    """The world at one boundary, after that instant's events.

    `stocks` is the state the sampling phase would read: post-event, which is
    what `state-signal-sampled-after-events` requires. `state_samples` is what
    the model's reporting handlers produced there, privately - no device, no
    transform, no publication, and no envelope. `interval_measurements` are the
    interval readings for the span `[T - dt, T)` and are absent at the first
    boundary, where no span precedes T.

    `forcings_available` holds only the forcings whose window concerns the step
    beginning here. A forcing outside its window has no entry at all, which is
    this product's spelling of unavailable: a zero would be a fabricated number
    and a held value would be an invented persistence rule.
    """

    step_index: int
    offset_minutes: int
    simulation_time: str
    stocks: tuple[tuple[str, Fraction], ...]
    forcings_available: tuple[tuple[str, Fraction], ...]
    state_samples: tuple[tuple[str, Fraction], ...]
    interval_measurements: tuple[tuple[str, Fraction], ...]
    interval_measurements_available: bool

    def stock(self, address: str) -> Fraction | None:
        for key, value in self.stocks:
            if key == address:
                return value
        return None

    def forcing(self, address: str) -> Fraction | None:
        for key, value in self.forcings_available:
            if key == address:
                return value
        return None

    def interval_measurement(self, address: str) -> Fraction | None:
        for key, value in self.interval_measurements:
            if key == address:
                return value
        return None

    def as_fields(self) -> tuple[object, ...]:
        return (
            self.step_index,
            self.offset_minutes,
            self.simulation_time,
            tuple((key, value) for key, value in self.stocks),
            tuple((key, value) for key, value in self.forcings_available),
            tuple((key, value) for key, value in self.state_samples),
            tuple((key, value) for key, value in self.interval_measurements),
            self.interval_measurements_available,
        )


@dataclass(frozen=True)
class PrivateTrajectory:
    """One execution: private truth, its identity, and how it ended."""

    run_id: str
    outcome: str
    inputs_identity: str
    kernel_version: int
    model_profile_id: str
    model_profile_version: int
    numeric_policy: str
    execution_contract_version: int
    boundaries: tuple[BoundaryState, ...]
    applied_events: tuple[AppliedEvent, ...]
    bounded_transitions: tuple[BoundedTransition, ...]
    handlers_exercised: tuple[str, ...]
    failure: ExecutionFailure | None = None
    notes: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.outcome not in EXECUTION_OUTCOMES:
            raise ValueError(
                f"An execution ends as one of {sorted(EXECUTION_OUTCOMES)}, "
                f"not {self.outcome!r}."
            )
        if self.outcome == "COMPLETED" and self.failure is not None:
            raise ValueError(
                f"Run {self.run_id} is COMPLETED and carries the failure "
                f"{self.failure.kind}. A partial result may not be labelled a "
                "whole one: the outcome is what a reader trusts, so a "
                "trajectory that stopped says FAILED and carries the reason."
            )
        if self.outcome == "FAILED" and self.failure is None:
            raise ValueError(
                f"Run {self.run_id} is FAILED and names no reason. A failure "
                "with no record is a run that stopped for reasons nobody can "
                "inspect."
            )

    @property
    def is_complete(self) -> bool:
        """Whether this trajectory covers the whole interval it was asked for.

        Read off the outcome rather than counting boundaries. A run that failed
        in its last step has as many boundaries as one that finished, so a
        count would report the two as the same thing.
        """
        return self.outcome == "COMPLETED"

    @property
    def final(self) -> BoundaryState | None:
        return self.boundaries[-1] if self.boundaries else None

    def boundary_at(self, offset_minutes: int) -> BoundaryState | None:
        for boundary in self.boundaries:
            if boundary.offset_minutes == offset_minutes:
                return boundary
        return None

    def stock_series(self, address: str) -> tuple[tuple[int, Fraction], ...]:
        """One address's stock at every boundary, with the offset beside it."""
        series = []
        for boundary in self.boundaries:
            value = boundary.stock(address)
            if value is not None:
                series.append((boundary.offset_minutes, value))
        return tuple(series)

    @property
    def content_digest(self) -> str:
        """The digest of this trajectory's canonical content.

        Everything a run produced, including the outcome and the failure. A
        digest taken over the boundaries alone would give a failed run and a
        completed run with the same prefix one identity.
        """
        return identity_digest(
            [
                "trajectory",
                self.run_id,
                self.outcome,
                self.inputs_identity,
                tuple(
                    boundary.as_fields() for boundary in self.boundaries
                ),
                tuple(event.as_fields() for event in self.applied_events),
                tuple(
                    transition.as_fields()
                    for transition in self.bounded_transitions
                ),
                None if self.failure is None else self.failure.kind,
                None if self.failure is None else self.failure.subject,
            ]
        )


def frozen_inputs_identity(
    inputs: object,
    *,
    kernel_version: int,
    model_profile_id: str,
    model_profile_version: int,
    numeric_policy: str,
) -> str:
    """The identity of one execution's inputs, kernel and numeric policy.

    `inputs` is a `FrozenWorldInputs`. It is typed loosely here so this module
    depends on nothing that depends on it; the fields it reads are named below
    and a test asserts the encoding covers every field of that record, so a
    field added there without entering the identity fails the build rather than
    producing two runs that claim one identity.
    """
    return identity_digest(
        [
            "frozen-world-inputs",
            inputs.execution_contract_version,
            inputs.site_id,
            inputs.foundation_version,
            inputs.scenario_id,
            inputs.scenario_version,
            inputs.model_profile_id,
            inputs.model_profile_version,
            inputs.publication_profile_id,
            inputs.publication_profile_version,
            inputs.interval.start_time,
            inputs.interval.end_time,
            inputs.interval.duration_minutes,
            inputs.interval.timestep_minutes,
            inputs.seed,
            tuple(
                (
                    entry.address,
                    entry.state_key,
                    entry.scope,
                    entry.parameter_id,
                    entry.value,
                    entry.canonical_unit,
                    entry.dimension,
                    entry.answered_by,
                )
                for entry in inputs.initial_values
            ),
            tuple(
                (
                    entry.address,
                    entry.kind,
                    entry.value,
                    entry.canonical_unit,
                    entry.source_address,
                    entry.bound_case_id,
                    entry.policy,
                )
                for entry in inputs.bounds
            ),
            tuple(
                (
                    entry.event_id,
                    entry.address,
                    entry.state_key,
                    entry.parameter_id,
                    entry.value,
                    entry.canonical_unit,
                    entry.dimension,
                    entry.shape,
                    entry.offset_minutes,
                    entry.duration_minutes,
                    entry.requirement,
                )
                for entry in inputs.forcings
            ),
            tuple(
                (
                    entry.event_id,
                    entry.address,
                    entry.state_key,
                    entry.direction,
                    entry.parameter_id,
                    entry.quantity,
                    entry.canonical_unit,
                    entry.dimension,
                    entry.shape,
                    entry.offset_minutes,
                    entry.duration_minutes,
                )
                for entry in inputs.causes
            ),
            tuple(inputs.unmodelled_addresses),
            tuple(inputs.intervention_history),
            kernel_version,
            model_profile_id,
            model_profile_version,
            numeric_policy,
        ]
    )


#: Every field of `FrozenWorldInputs` that `frozen_inputs_identity` reads.
#:
#: `run_id` is the one field it does not, and the module docstring says why.
#: The test that compares this against the record's own fields is what makes
#: "the identity binds the frozen inputs" a checked statement rather than a
#: sentence beside a function.
IDENTITY_FIELDS_READ = frozenset(
    {
        "execution_contract_version",
        "site_id",
        "foundation_version",
        "scenario_id",
        "scenario_version",
        "model_profile_id",
        "model_profile_version",
        "publication_profile_id",
        "publication_profile_version",
        "interval",
        "seed",
        "initial_values",
        "bounds",
        "forcings",
        "causes",
        "unmodelled_addresses",
        "intervention_history",
    }
)

#: The one field deliberately outside the identity.
IDENTITY_FIELDS_EXCLUDED = frozenset({"run_id"})
