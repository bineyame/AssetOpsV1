"""What a kernel executes: frozen content, in terms no product record owns.

A `SimulationRun` is a product record. It carries a Site reference, a scenario
reference, resolved parameters, blocking reasons and the readiness disclosure,
and a kernel has no business with most of that. `FrozenWorldInputs` is the
projection of one frozen Draft that an execution needs and nothing more, built
by the neutral host adapter from the run and the versioned definition it names.

## The truth barrier is the shape of this record, not a rule beside it

There is no field here for a scenario expectation, an authored reported
reading, a reconciliation result, a Site name, a device, a source mode or a
lifecycle status. That is deliberate and it is the whole of criterion 5: the
evolution path cannot consult an authored reading to decide where the tank
level goes, because nothing it is handed can carry one. A rule saying "do not
read the expectations" would be a rule an adapter could forget; a record with
no field for them cannot be passed one.

`simulator/` also may not import `assetops_backend` at all, so the private
expectation record and the reconciliation reference implementation are not
reachable from a kernel by any spelling. The two together are why the mutation
that changes an authored reading and an authored expectation leaves the
canonical trajectory byte-identical: the numbers never entered.

## Values come from the frozen run and structure from the versioned definition

Every number below is the number a run froze. The definition supplies shape -
which entry is a cause and which a forcing, at what offset, over what window,
in which direction, against which address - because a Draft freezes resolved
values and profile answers rather than a copy of the timeline.

The adapter that builds this is where the two halves meet, and it refuses a
mismatch rather than preferring one side. What it cannot see is named in the
review packet and the backlog: an in-place edit that moves an existing entry's
offset or window length, at an unchanged scenario version, changes structure
without changing any value the adapter compares.

## Addresses are canonical text

An address is the `addressed_key` spelling - `fuel-tank-volume@fuel-tank`,
`site:site-load-demand` - which is what a frozen run document persists and what
every comparison, lookup and blocking reason in the product already keys on. It
round-trips through the product's address parser exactly, so the kernel speaks
the same identity without the addressing record itself having to cross the
barrier. This is the minimum shared schema rather than the largest available
one: moving `StateRef` here would have relocated a validator with twenty
product callers and bought this slice no behaviour.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

#: The two directions a declared cause moves a stock in.
CAUSE_DIRECTIONS = frozenset({"INCREASE", "DECREASE"})

#: The shapes an entry occupies time in, matching the authored vocabulary.
ENTRY_SHAPES = frozenset({"POINT", "WINDOW", "INTERVAL_WIDE"})


@dataclass(frozen=True)
class FrozenInterval:
    """The interval a run covers and the step it is walked in.

    Half-open, `[start_time, end_time)`, so an instant belongs to exactly one
    step. `duration_minutes` is the length in the units every authored offset
    is written in, which is what makes an offset and this interval comparable
    without reading a clock.
    """

    start_time: str
    end_time: str
    duration_minutes: int
    timestep_minutes: int

    @property
    def step_starts(self) -> tuple[int, ...]:
        """Every offset a step begins at, in order.

        The end instant is not among them: it begins no step, because the
        interval excludes it.
        """
        return tuple(
            range(0, self.duration_minutes, self.timestep_minutes)
        )

    @property
    def boundaries(self) -> tuple[int, ...]:
        """Every instant the boundary cycle runs at, including the end.

        The end instant is a boundary - the state there is what the last step
        carried forward, and a reading there describes the span that just
        finished - and it is not a step start. Nothing is due there and nothing
        is evolved from there.
        """
        return self.step_starts + (self.duration_minutes,)


@dataclass(frozen=True)
class InitialValue:
    """One initial world value a run froze, with who answered for it."""

    address: str
    state_key: str
    scope: str
    parameter_id: str
    value: Fraction
    canonical_unit: str
    dimension: str
    answered_by: str


@dataclass(frozen=True)
class DeclaredBound:
    """One bound on one address, with the number and where the number came from.

    `source_address` is the split `D-2026-09-22-capacity-bound-source` settles.
    The definition declares WHICH state bounds which; the frozen run carries
    HOW LARGE it is, as the initial value of the bounding state. So a bound
    here names both: the address it limits, and the address whose frozen value
    supplied the limit. A bound that could not name its source would be a
    number with no answerer, which is the thing a frozen run exists to prevent.
    """

    address: str
    kind: str
    value: Fraction
    canonical_unit: str
    source_address: str
    bound_case_id: str
    policy: str

    def __post_init__(self) -> None:
        if self.kind not in {"UPPER", "LOWER"}:
            raise ValueError(
                f"A bound on {self.address!r} is an UPPER or a LOWER one, not "
                f"{self.kind!r}."
            )


@dataclass(frozen=True)
class ForcingInput:
    """One exogenous condition the definition forces, over its declared span.

    A forcing is not a cause: it moves no stock by itself. What reads it is a
    model law, and outside its span it is UNAVAILABLE rather than zero or held.
    """

    event_id: str
    address: str
    state_key: str
    parameter_id: str
    value: Fraction
    canonical_unit: str
    dimension: str
    shape: str
    offset_minutes: int
    duration_minutes: int | None
    requirement: str

    def __post_init__(self) -> None:
        if self.shape not in ENTRY_SHAPES:
            raise ValueError(
                f"Forcing {self.event_id!r} occupies time as {self.shape!r}, "
                f"and an entry is one of {sorted(ENTRY_SHAPES)}."
            )


@dataclass(frozen=True)
class DeclaredCause:
    """One declared change to a stock, and the span it is spread across.

    `quantity` is the total the entry moves, in canonical units, already
    integrated if the definition declared a rate over a window. How much of it
    has moved part way through is the window ramp's answer and never this
    record's: a cause carries what it moves and when, and the contract carries
    how it is apportioned.
    """

    event_id: str
    address: str
    state_key: str
    direction: str
    parameter_id: str
    quantity: Fraction
    canonical_unit: str
    dimension: str
    shape: str
    offset_minutes: int
    duration_minutes: int | None

    def __post_init__(self) -> None:
        if self.direction not in CAUSE_DIRECTIONS:
            raise ValueError(
                f"Cause {self.event_id!r} moves {self.address!r} in direction "
                f"{self.direction!r}, and a cause moves a stock one of "
                f"{sorted(CAUSE_DIRECTIONS)}."
            )
        if self.shape not in ENTRY_SHAPES:
            raise ValueError(
                f"Cause {self.event_id!r} occupies time as {self.shape!r}, and "
                f"an entry is one of {sorted(ENTRY_SHAPES)}."
            )


@dataclass(frozen=True)
class FrozenWorldInputs:
    """Everything one execution of one frozen Draft consumes.

    `unmodelled_addresses` is the cross-reference a kernel cannot do without.
    A `READY` run can carry an initialization input for a state this build does
    not model at that scope, and nothing on the row says so - the
    disqualification lives in the run's unsupported optional inputs. A kernel
    reading initialization inputs alone would initialize from it. So the
    addresses the run recorded as unsupported travel with the inputs, and the
    kernel treats an initial value for a state it has no handler for as an
    error unless it is named here.
    """

    run_id: str
    execution_contract_version: int
    site_id: str
    foundation_version: int
    scenario_id: str
    scenario_version: int
    model_profile_id: str
    model_profile_version: int
    publication_profile_id: str
    publication_profile_version: int
    interval: FrozenInterval
    seed: int
    initial_values: tuple[InitialValue, ...]
    bounds: tuple[DeclaredBound, ...]
    forcings: tuple[ForcingInput, ...]
    causes: tuple[DeclaredCause, ...]
    unmodelled_addresses: tuple[str, ...]
    intervention_history: tuple[str, ...]

    def initial_value(self, address: str) -> InitialValue | None:
        for entry in self.initial_values:
            if entry.address == address:
                return entry
        return None

    def bound(self, address: str, kind: str) -> DeclaredBound | None:
        for entry in self.bounds:
            if entry.address == address and entry.kind == kind:
                return entry
        return None

    def addresses_of_state(self, state_key: str) -> tuple[str, ...]:
        """Every address in these inputs claiming one semantic state.

        Sorted, and deduplicated, so a model asking "which tanks does this run
        concern" gets a stable answer rather than authoring order.
        """
        found = {
            entry.address
            for entry in self.initial_values
            if entry.state_key == state_key
        }
        found |= {
            entry.address
            for entry in self.forcings
            if entry.state_key == state_key
        }
        found |= {
            entry.address
            for entry in self.causes
            if entry.state_key == state_key
        }
        return tuple(sorted(found))
