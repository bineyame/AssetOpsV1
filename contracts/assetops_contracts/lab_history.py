"""The recorded history of one Lab execution, as the gated Lab receives it.

T025c (L1a), under `D-2026-09-30-lab-cockpit-history`. `LabProjection` is where
a run IS; this is what it RECORDED on the way there - every boundary, every
addressed state sample, every resolved interval, every observation attempt and
every applied event or transition - so that a completed or failed run can be
inspected after a host restart without executing it again.

It is a projection of the same result, not a second truth store. The host
captures it from the execution it already ran (`host/lab_history.py`) and
persists it beside the projection in the host-owned execution artifact; a read
returns what was recorded and never re-runs a kernel. The product backend sees
this record only through the gated Lab port, exactly as it sees
`LabProjection`, and no operator view consumes it.

Three rules the record holds rather than documents:

- **Each fact once.** A boundary's stocks are one sample per address; a
  resolved interval is one row; an attempt is one row. Nothing is a cumulative
  snapshot per boundary, so storage grows with records, not with the square of
  the boundary count.
- **Timing is stated, not implied.** A sample's `phase` says whether it is the
  post-event state at T (`POST_EVENT`), the discrete state over the step
  beginning at T (`FOR_STEP`), or a measurement of the interval that ENDED at T
  (`PRECEDING_INTERVAL`, describing `[T - dt, T)`). A resolved interval names
  its own `[from, to)`. The first boundary has no preceding interval and
  therefore no such sample: its absence is the record, not a gap to fill.
- **Absence is a coverage fact.** `coverage` says per family whether it was
  RECORDED, is NOT_APPLICABLE to this model, or is UNAVAILABLE and why - an
  artifact written before history existed, a failed history write, an
  interrupted run. A final snapshot or the twelve-report tail is never
  presented as a full curve.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction

from assetops_contracts.control import DISCRETE_UNIT, ControlStep
from assetops_contracts.failures import ExecutionFailure
from assetops_contracts.observation import (
    DeviceObservation,
    DeviceSignalSpec,
    ReportingPathWindow,
)
from assetops_contracts.trajectory import (
    AppliedEvent,
    BoundedTransition,
    DiscreteTransition,
    ForcingExposure,
)
from assetops_contracts.world_inputs import BusAttachmentInput

#: The persisted history layout this build writes and reads. Independent of the
#: execution contract, the kernel, the publication profile and the projection
#: artifact's own schema: adding a recorded family is an artifact change, not a
#: change to what a frozen Draft means (`D-2026-09-22-contract-version-scope`).
LAB_HISTORY_SCHEMA_VERSION = 1

#: The recorded families, in the order a reader meets them.
HISTORY_FAMILIES = (
    "state_samples",
    "intervals",
    "observation_attempts",
    "timeline",
    "drawing",
)

HISTORY_FAMILY_STATEMENTS = {
    "state_samples": (
        "Addressed private state at every recorded boundary: stocks and "
        "discrete state after that instant's events, the discrete state over "
        "the step beginning there, and interval measurements of the step that "
        "ended there."
    ),
    "intervals": (
        "Every resolved interval: what the controller saw and requested, what "
        "the resolver accepted and what limited it, per-load service, named "
        "flows, effective controls with provenance and balance identities."
    ),
    "observation_attempts": (
        "Every due observation attempt with its outcome, not the recent-report "
        "tail. Instants a signal was not due are not attempts; its cadence says "
        "which they are."
    ),
    "timeline": (
        "Applied events, bounded transitions and discrete transitions in the "
        "order the kernel applied them, with the recorded failure if any."
    ),
    "drawing": (
        "The run's frozen bus attachments: the component, converter and bus "
        "identities this run executed against, not the Site's current topology."
    ),
}

#: Per family, what the record holds.
FAMILY_AVAILABILITY_STATEMENTS = {
    "RECORDED": "Recorded for every boundary this run reached.",
    "NOT_APPLICABLE": "This model produces no records of this family.",
    "UNAVAILABLE": "Not recorded for this run; nothing is shown in its place.",
}

#: Where a history came from. Different facts, so different words.
LAB_HISTORY_SOURCES = {
    "LIVE_SESSION": (
        "The in-memory prefix of a run this host is still executing. It grows "
        "as the run is stepped."
    ),
    "PERSISTED": (
        "Read back from the run's execution artifact, verified against its "
        "integrity digest. Nothing was executed to produce it."
    ),
    "LEGACY_ARTIFACT": (
        "This run's artifact was written before execution history was "
        "recorded. Its execution summary series remain on the execution "
        "record; the families below were never written and are not "
        "reconstructed."
    ),
    "NOT_RECORDED": (
        "This run has no recorded history: it has not been executed, or its "
        "live session ended with the process that ran it."
    ),
    "WRITE_FAILED": (
        "The run finished but its history could not be written. The execution "
        "record stands; the history is not a durable complete record."
    ),
    "HISTORY_UNREADABLE": (
        "A history is on disk and this build cannot verify it. It is shown as "
        "unreadable rather than guessed at, and it was not changed."
    ),
}

#: The timing of one sample, relative to the boundary it is recorded at.
SAMPLE_PHASES = {
    "POST_EVENT": "The state at T after that instant's events.",
    "FOR_STEP": "The discrete state over the step beginning at T.",
    "PRECEDING_INTERVAL": "A measurement of the interval [T - dt, T).",
}


@dataclass(frozen=True)
class FamilyCoverage:
    family: str
    availability: str
    statement: str

    def __post_init__(self) -> None:
        if self.family not in HISTORY_FAMILIES:
            raise ValueError(f"Unknown history family {self.family!r}.")
        if self.availability not in FAMILY_AVAILABILITY_STATEMENTS:
            raise ValueError(
                f"History family {self.family} is {self.availability!r}; a "
                f"family is one of {sorted(FAMILY_AVAILABILITY_STATEMENTS)}."
            )


@dataclass(frozen=True)
class HistoryBoundary:
    """One recorded instant. `has_preceding_interval` is false only at the first."""

    step_index: int
    offset_minutes: int
    simulation_time: str
    has_preceding_interval: bool


@dataclass(frozen=True)
class HistorySample:
    """One addressed private value at one boundary, in one stated phase.

    `unit` is the unit the run froze for a stock, `state` for a discrete
    member, and empty for an interval measurement whose unit is the model's
    rather than one the run declared (the reason `PrivateStateRow` gives).
    """

    offset_minutes: int
    address: str
    state_key: str
    phase: str
    unit: str
    value: Fraction | str

    def __post_init__(self) -> None:
        if self.phase not in SAMPLE_PHASES:
            raise ValueError(
                f"Sample {self.address} at offset {self.offset_minutes} has "
                f"phase {self.phase!r}; a phase is one of {sorted(SAMPLE_PHASES)}."
            )
        if (self.unit == DISCRETE_UNIT) != isinstance(self.value, str):
            raise ValueError(
                f"Sample {self.address} at offset {self.offset_minutes} is "
                f"{self.value!r} in unit {self.unit!r}: a discrete value is a "
                "member text in unit 'state' and every other value is exact."
            )


@dataclass(frozen=True)
class HistoryInterval:
    """One resolved interval `[from_offset, to_offset)`, whole.

    The control step is the kernel's own record of the step, carried as it
    was produced: the view at `from_offset`, the intent for the step, and the
    accepted flow set with its segments. A reserve change inside the step is a
    second segment and a second effective-control row, not a rewrite.
    """

    from_offset: int
    to_offset: int
    step: ControlStep


@dataclass(frozen=True)
class LabHistory:
    """One run's recorded history, or the stated reason there is none."""

    run_id: str
    status: str
    source: str
    statement: str
    history_schema_version: int | None
    boundaries_total: int
    inputs_identity: str
    content_digest: str | None
    observation_series_digest: str | None
    #: The history's own integrity digest over its manifest and records, and a
    #: different thing from `content_digest`: that one identifies the kernel's
    #: canonical trajectory; this one identifies the recorded projection of it.
    history_digest: str | None
    coverage: tuple[FamilyCoverage, ...]
    failure: ExecutionFailure | None = None
    boundaries: tuple[HistoryBoundary, ...] = ()
    samples: tuple[HistorySample, ...] = ()
    intervals: tuple[HistoryInterval, ...] = ()
    exposures: tuple[ForcingExposure, ...] = ()
    attempts: tuple[DeviceObservation, ...] = ()
    signals: tuple[DeviceSignalSpec, ...] = ()
    reporting_gaps: tuple[ReportingPathWindow, ...] = ()
    applied_events: tuple[AppliedEvent, ...] = ()
    bounded_transitions: tuple[BoundedTransition, ...] = ()
    discrete_transitions: tuple[DiscreteTransition, ...] = ()
    bus_attachments: tuple[BusAttachmentInput, ...] = ()
    notes: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.source not in LAB_HISTORY_SOURCES:
            raise ValueError(f"Unknown history source {self.source!r}.")
        families = tuple(entry.family for entry in self.coverage)
        if families != HISTORY_FAMILIES:
            raise ValueError(
                f"A history states coverage for {HISTORY_FAMILIES}, in that "
                f"order, and this one states {families}."
            )

    @property
    def recorded_through_offset(self) -> int | None:
        return self.boundaries[-1].offset_minutes if self.boundaries else None

    def availability(self, family: str) -> str:
        for entry in self.coverage:
            if entry.family == family:
                return entry.availability
        raise KeyError(family)


def unavailable_coverage(reason: str) -> tuple[FamilyCoverage, ...]:
    """Every family UNAVAILABLE, for one stated reason."""
    return tuple(
        FamilyCoverage(family=family, availability="UNAVAILABLE", statement=reason)
        for family in HISTORY_FAMILIES
    )
