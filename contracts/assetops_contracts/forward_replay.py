"""The forward replay request and projection, neutral to both sides (0K1).

A forward replay executes a frozen mini-grid run's world again with series, a start state and settings supplied by
the caller, and returns what the generator, the battery and the tank did. The product needs it to value a
generator setting (design `domain-and-decision-models.md` §4.2) and may not reach the kernel, so the request and
the projection live here, where both sides may import them, and nothing here imports anything outside the
standard library.

Exact numbers only (D-0K1.9): every numeric field of a request is a `Fraction`. A `float`, an `int` or a
`Decimal` is a `TypeError` naming the field, because the kernel has no tolerance and an unstated rounding at the
seam would be invisible to an equality proof. `None` is allowed only inside a series, where it is a gap the
adapter refuses (`INPUT_GAP`, D-0K1.5).

The generator's start state is not judged here: a state outside `REPLAY_GENERATOR_STATES` is the adapter's
refusal `REPLAY_START_STATE_INVALID`, so the reason reaches the caller as a code (D-0K1.18).

The projection is `MODELLED` evidence and carries only `Fraction`, `int`, `str`, `bool`, `None` and `ReplayStep`
(D-0K1.6). A refusal means nothing executed; a kernel failure is a projection with `status == "FAILED"`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from fractions import Fraction

REPLAY_GENERATOR_STATES = frozenset({"STOPPED", "FAILED"})
REPLAY_STATUSES = frozenset({"COMPLETED", "FAILED"})
FORWARD_REPLAY_REFUSALS = frozenset(
    {
        "REPLAY_RUN_NOT_EXECUTABLE",
        "REPLAY_MODEL_UNSUPPORTED",
        "REPLAY_SERIES_MISALIGNED",
        "INPUT_GAP",
        "REPLAY_SERIES_INVALID",
        "REPLAY_ADDRESS_UNKNOWN",
        "POLICY_BAND_INVALID",
        "REPLAY_START_STATE_INVALID",
    }
)
CASE_ID = re.compile(r"[a-z0-9][a-z0-9-]{0,39}")
EVIDENCE_CLASS = "MODELLED"
STOP_SOURCES = frozenset({"BASELINE", "SETTING"})


def _exact(value: object, name: str) -> None:
    # `Fraction` only: an int is refused too (and a bool, which is an int), so no caller relies on a coercion.
    if type(value) is not Fraction:
        raise TypeError(f"{name} must be a Fraction, not {type(value).__name__}")


def _series(values: object, name: str) -> None:
    if not isinstance(values, tuple):
        raise TypeError(f"{name} must be a tuple, not {type(values).__name__}")
    for index, value in enumerate(values):
        if value is not None:
            _exact(value, f"{name}[{index}]")


@dataclass(frozen=True)
class LoadSeries:
    """One load's average requested kW over each step, in step order; `load_id` is the component id."""

    load_id: str
    kw: tuple[Fraction | None, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.load_id, str) or not self.load_id:
            raise ValueError("load_id must be a non-empty component id")
        _series(self.kw, f"loads[{self.load_id}].kw")


@dataclass(frozen=True)
class ReplayStartState:
    """The run-start state of the replay. `generator_state` is judged by the adapter, not here (D-0K1.18)."""

    soc_pct: Fraction
    fuel_l: Fraction
    generator_state: str

    def __post_init__(self) -> None:
        _exact(self.soc_pct, "start.soc_pct")
        _exact(self.fuel_l, "start.fuel_l")
        if not isinstance(self.generator_state, str):
            raise TypeError("start.generator_state must be a str")


@dataclass(frozen=True)
class ReplaySettings:
    """A changed Site policy; `None` keeps the base run's frozen baseline."""

    stop_soc_pct: Fraction | None = None
    reserve_soc_pct: Fraction | None = None

    def __post_init__(self) -> None:
        if self.stop_soc_pct is not None:
            _exact(self.stop_soc_pct, "settings.stop_soc_pct")
        if self.reserve_soc_pct is not None:
            _exact(self.reserve_soc_pct, "settings.reserve_soc_pct")


@dataclass(frozen=True)
class ForwardReplayRequest:
    case_id: str
    pv_available_kw: tuple[Fraction | None, ...]  # average PV-available kW (after the inverter limit) per step
    loads: tuple[LoadSeries, ...]
    start: ReplayStartState
    settings: ReplaySettings = field(default_factory=ReplaySettings)

    def __post_init__(self) -> None:
        if not isinstance(self.case_id, str) or CASE_ID.fullmatch(self.case_id) is None:
            raise ValueError(f"case_id {self.case_id!r} must match {CASE_ID.pattern}")
        _series(self.pv_available_kw, "pv_available_kw")
        if not isinstance(self.loads, tuple) or not all(isinstance(x, LoadSeries) for x in self.loads):
            raise TypeError("loads must be a tuple of LoadSeries")
        if not isinstance(self.start, ReplayStartState):
            raise TypeError("start must be a ReplayStartState")
        if not isinstance(self.settings, ReplaySettings):
            raise TypeError("settings must be ReplaySettings")


@dataclass(frozen=True)
class ReplayStep:
    offset_minutes: int
    generator_state: str
    generator_kwh: Fraction
    unserved_kwh: Fraction
    soc_start_pct: Fraction
    fuel_start_l: Fraction
    pv_clipped: bool


@dataclass(frozen=True)
class ForwardReplayProjection:
    base_run_id: str
    case_id: str
    status: str
    model_profile_id: str
    model_profile_version: int
    interval_start: str
    timestep_minutes: int
    stop_soc_pct: Fraction
    stop_source: str
    reserve_soc_pct: Fraction
    reserve_source: str
    steps: tuple[ReplayStep, ...]
    soc_end_pct: Fraction | None
    fuel_end_l: Fraction | None
    min_soc_pct: Fraction
    generator_kwh: Fraction
    unserved_kwh: Fraction
    starts: int
    running_steps: int
    fuel_burned_l: Fraction | None
    clipped_offsets: tuple[int, ...]
    replay_identity: str
    evidence_class: str = EVIDENCE_CLASS
    failure_kind: str | None = None
    failure_subject: str | None = None

    def __post_init__(self) -> None:
        if self.status not in REPLAY_STATUSES:
            raise ValueError(f"status {self.status!r} is not one of {sorted(REPLAY_STATUSES)}")
        if (self.status == "FAILED") != (self.failure_kind is not None):
            raise ValueError("failure_kind is set if and only if status is FAILED")
        if self.stop_source not in STOP_SOURCES or self.reserve_source not in STOP_SOURCES:
            raise ValueError(f"a setting's source is one of {sorted(STOP_SOURCES)}")
        if self.evidence_class != EVIDENCE_CLASS:
            raise ValueError(f"a replay is {EVIDENCE_CLASS} evidence")


class ForwardReplayRefused(Exception):
    """Nothing executed: the request or the run was judged and refused."""

    def __init__(self, code: str, subject: str, detail: str) -> None:
        if code not in FORWARD_REPLAY_REFUSALS:
            raise ValueError(f"{code!r} is not a forward replay refusal")
        super().__init__(f"{code} ({subject}): {detail}")
        self.code = code
        self.subject = subject
        self.detail = detail


__all__ = [
    "CASE_ID",
    "EVIDENCE_CLASS",
    "FORWARD_REPLAY_REFUSALS",
    "REPLAY_GENERATOR_STATES",
    "REPLAY_STATUSES",
    "ForwardReplayProjection",
    "ForwardReplayRefused",
    "ForwardReplayRequest",
    "LoadSeries",
    "ReplaySettings",
    "ReplayStartState",
    "ReplayStep",
]
