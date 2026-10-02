"""Policy and operational records: the first non-telemetry source family (T026).

Neutral, because both sides speak it: the host projects a frozen Draft into
`FrozenRecordInputs`, the simulator's record transform turns those into
`RecordObservation`s as the run reaches them, and the gateway publishes the
reported ones as schema-2 envelopes of family `POLICY` or `OPERATIONAL_RECORD`.

## Records are not telemetry

A record has no cadence, no measurement class, no quality and no interval
semantics. It exists once, at the instant it occurred, and it is either
published or it is not. So it does not inherit a signal's dropout draw, and the
two ways it can fail to arrive are the two reporting-path causes a scenario can
declare against its channel: a gap (the record is never published - and its
absence never establishes that nothing was commanded) and a delay (published
late, source time unchanged).

## Where the content comes from, and what it may not come from

Policy records carry the Foundation answers the run FROZE - the value, the
Foundation version it was answered under and that version's validity start -
never a live Site and never the controller's private view. Override commands
carry a scenario CONTROL override window, executed as an operator command:
occurrence, effective interval, value and actor. Neither reads a stock, a flow
or an intent.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from fractions import Fraction

from assetops_contracts.observation import PublicationDelayWindow
from assetops_contracts.world_inputs import FrozenInterval

RECORD_OUTCOMES = frozenset({"REPORTED", "SUPPRESSED_BY_GAP"})


def offset_instant(interval: FrozenInterval, offset_minutes: int) -> str:
    """The UTC instant `offset_minutes` into a run's interval."""
    start = datetime.strptime(interval.start_time, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc
    )
    return (start + timedelta(minutes=offset_minutes)).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass(frozen=True)
class PolicyDeclaration:
    """One frozen control value and the Foundation version that answered it."""

    device_id: str
    signal_id: str
    control: str
    component_id: str | None
    value: Fraction | None
    members: tuple[str, ...] | None
    unit: str
    policy_version: int
    policy_source: str
    effective_start: str

    def __post_init__(self) -> None:
        if (self.value is None) == (self.members is None):
            raise ValueError(
                f"Policy {self.control!r} carries a value or a member list, "
                "exactly one."
            )


@dataclass(frozen=True)
class OverrideCommand:
    """One operator-commanded override, from a frozen scenario CONTROL window."""

    event_id: str
    device_id: str
    signal_id: str
    control: str
    component_id: str
    value: Fraction
    unit: str
    occurrence_offset_minutes: int
    effective_start_offset_minutes: int
    effective_end_offset_minutes: int | None
    actor: str = "OPERATOR"

    def __post_init__(self) -> None:
        if self.effective_start_offset_minutes < self.occurrence_offset_minutes:
            raise ValueError(
                f"Override {self.event_id!r} takes effect before it was given."
            )
        if (
            self.effective_end_offset_minutes is not None
            and self.effective_end_offset_minutes
            <= self.effective_start_offset_minutes
        ):
            raise ValueError(f"Override {self.event_id!r} is in force for no time.")


@dataclass(frozen=True)
class RecordGap:
    """A declared span across which one record channel publishes nothing."""

    event_id: str
    device_id: str
    signal_id: str
    start_offset_minutes: int
    end_offset_minutes: int

    def covers(self, offset_minutes: int) -> bool:
        return self.start_offset_minutes <= offset_minutes < self.end_offset_minutes


@dataclass(frozen=True)
class FrozenRecordInputs:
    """Everything the record transform reads, and no world quantity."""

    run_id: str
    interval: FrozenInterval
    policies: tuple[PolicyDeclaration, ...] = ()
    overrides: tuple[OverrideCommand, ...] = ()
    gaps: tuple[RecordGap, ...] = ()
    delays: tuple[PublicationDelayWindow, ...] = ()


@dataclass(frozen=True)
class RecordObservation:
    """One record occurrence, and whether its channel published it.

    `SUPPRESSED_BY_GAP` is the missing case: the record OCCURRED (the override
    is in force in the world) and nothing was published. A consumer seeing no
    record sees "none observed", never "none occurred".
    """

    family: str
    device_id: str
    signal_id: str
    at_offset_minutes: int
    source_time: str
    outcome: str
    control: str
    component_id: str | None
    value: Fraction | None
    members: tuple[str, ...] | None
    unit: str
    effective_start: str
    effective_end: str | None
    policy_version: int | None = None
    policy_source: str | None = None
    record_kind: str | None = None
    actor: str | None = None
    #: The authored event behind an override or a suppression; Lab-only, it
    #: never crosses into an envelope (no envelope field could carry it).
    event_id: str | None = None

    def __post_init__(self) -> None:
        if self.outcome not in RECORD_OUTCOMES:
            raise ValueError(f"{self.outcome!r} is not a record outcome.")
        if self.family not in ("POLICY", "OPERATIONAL_RECORD"):
            raise ValueError(f"{self.family!r} is not a record family.")
