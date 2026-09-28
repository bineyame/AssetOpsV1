"""The one record where private truth and a reported value sit in one row.

`LabProjection` is what the gated Simulator Lab receives (v4 section 21, and
`.ai/ARCHITECTURE.md` Execution Composition And Truth Barrier). It is the
deliberate exception to the truth barrier rather than a hole in it, and the
exception is what the whole slice is for: the owner has to be able to see, at one
instant and on one screen, what the world held, what a device said, and that
those are not the same number.

## Why it is a separate record rather than a widened `DeviceObservation`

A `DeviceObservation` cannot carry a true value, and its own docstring says why.
So the pairing lives here, in a record whose name says it is the Lab's. Three
consequences, each intended:

- nothing outside the Lab may be handed one, because the only producer is the
  composition leaf and the only consumer is a gated surface;
- the world record and the reporting record stay separable, so criterion 8's
  claim - changing a cadence, a bias or a dropout changes the reports and not
  the world - is a fact about two records rather than a promise about a caller;
- a reader of `observations` below can see the gap in the reported column
  against a moving true column, which is the demonstration
  `D-2026-09-22-forcing-state-requirements` left unowned when the publication
  profile took over the reporting path.

## A run in progress is a status, not a trajectory

`PrivateTrajectory` has two outcomes and no third, because "a run that is still
running is a handle rather than a trajectory". The Lab needs to render one
mid-flight anyway, so `LAB_EXECUTION_STATUSES` has the three the trajectory
cannot have: `NOT_STARTED`, `RUNNING` and `INTERRUPTED`. `content_digest` is
present only when the run reached a terminal outcome, for the same reason: a
digest over a prefix would be an identity for something that is not yet a thing.

`INTERRUPTED` is the honest answer to a host restart. A live handle lives in one
process; when that process is gone and the persisted artifact says the run was
`RUNNING`, there is no resuming it and no pretending it completed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction

from assetops_contracts.failures import ExecutionFailure
from assetops_contracts.observation import (
    DeviceObservation,
    DeviceSignalSpec,
    ReportingPathWindow,
)

#: What state a Lab execution is in. Six, and the four the private trajectory
#: cannot express are the reason this vocabulary exists rather than reusing
#: `EXECUTION_OUTCOMES`.
#:
#: `ARTIFACT_UNREADABLE` is about the RECORD rather than about the run: the run
#: happened, and this build cannot interpret what was written down about it. It
#: is deliberately not `INTERRUPTED`, which says a process died mid-flight, and
#: deliberately not `FAILED`, which says an execution stopped. Collapsing it into
#: either would report an execution event that did not occur.
LAB_EXECUTION_STATUSES = frozenset(
    {
        "NOT_STARTED",
        "RUNNING",
        "COMPLETED",
        "FAILED",
        "INTERRUPTED",
        "ARTIFACT_UNREADABLE",
    }
)

#: The terminal ones. A terminal run accepts no control and carries a digest.
TERMINAL_LAB_STATUSES = frozenset({"COMPLETED", "FAILED"})

#: Why a control request was refused, as a vocabulary distinct from run setup's
#: refusals, a Draft's blocking reasons and an execution failure's kinds.
#:
#: A fourth phase can say no, and it is not any of the three that already could.
#: A refusal here means the request was judged and nothing was executed: no
#: boundary advanced, no artifact changed, and the run is exactly where it was.
#: An execution failure, by contrast, means a run started and stopped, and it
#: arrives on the projection as `FAILED` with the failure record attached.
#: The names carry no `EXECUTION_` prefix, because the surface that renders them
#: adds one: `execution_refusal_code` turns `RUN_BLOCKED` into
#: `EXECUTION_RUN_BLOCKED` exactly as `run_refusal_code` prefixes the setup
#: vocabulary. A kind spelled with the prefix already on it would arrive at a
#: client doubled.
LAB_CONTROL_REFUSALS = frozenset(
    {
        "RUN_BLOCKED",
        "CONTRACT_INCOMPATIBLE",
        "ALREADY_TERMINAL",
        "NOT_STARTED",
        "STEP_ALREADY_APPLIED",
        "INTERRUPTED",
        "PORT_NOT_COMPOSED",
        "FROZEN_RUN_NOT_RECONSTRUCTIBLE",
        "CADENCE_NOT_EXPRESSIBLE",
        "ARTIFACT_UNREADABLE",
    }
)

#: What each refusal tells a reader. A test asserts this covers the vocabulary
#: exactly, so a refusal cannot be raised without a statement somebody wrote.
LAB_CONTROL_REFUSAL_STATEMENTS: dict[str, str] = {
    "RUN_BLOCKED": (
        "This Draft is BLOCKED, which is run setup's answer that its frozen "
        "inputs may not execute. There is no override and no partial mode: a "
        "status a control could talk past would be advisory. The blocking "
        "reasons on the run say what to change, and changing it means setting a "
        "new run up."
    ),
    "CONTRACT_INCOMPATIBLE": (
        "This Draft froze its inputs against a different version of the "
        "execution contract, so the meanings behind those inputs have changed. "
        "The run stays readable exactly as it was frozen and is not executed, "
        "because executing it here would apply these rules to inputs resolved "
        "under different ones."
    ),
    "ALREADY_TERMINAL": (
        "This execution has already completed or failed. A terminal run is a "
        "record, not a handle: advancing it would mean producing a second "
        "trajectory under the identity of the first."
    ),
    "NOT_STARTED": (
        "There is no execution of this Draft to advance. Start it first; a step "
        "that silently started a run would make the two controls one and lose "
        "the distinction between a run that has not begun and a run at its "
        "first boundary."
    ),
    "STEP_ALREADY_APPLIED": (
        "The request named the boundary it expected to advance from and the run "
        "is not at that boundary, so nothing was advanced. A resubmitted control "
        "- a double click, a retried request, a second tab - is the ordinary case "
        "and this is what stops it stepping twice. The run's current position is "
        "on the refusal, so a caller can see where it actually is."
    ),
    "INTERRUPTED": (
        "An execution of this Draft was recorded as running and the process "
        "holding it is gone, so there is nothing to resume. What it had produced "
        "was private state in one process and was not persisted as a completed "
        "result. Set a new run up, or execute this one again from the start."
    ),
    "PORT_NOT_COMPOSED": (
        "This build serves the Simulator Lab without an execution port composed "
        "behind it, so no kernel is reachable from here. The composition leaf is "
        "what wires one; a build serving the product package alone can inspect "
        "Drafts and cannot execute them."
    ),
    "FROZEN_RUN_NOT_RECONSTRUCTIBLE": (
        "The frozen run does not determine one experiment, so it is not "
        "executed. What is wrong is named on the refusal: an address answered "
        "twice, a bound with no policy, or a profile the run did not select."
    ),
    "CADENCE_NOT_EXPRESSIBLE": (
        "A configured signal publishes at a rate this run's timestep cannot "
        "express, so some sample would be due between two boundaries. It is not "
        "moved to the nearest one, which would report a value at a time it was "
        "not taken, and it is not skipped, which would turn a declared cadence "
        "into a different one. The detail names the signal and the two numbers. "
        "A timestep is chosen at run setup, so setting a run up with a timestep "
        "the cadence divides is what makes this document executable."
    ),
    "ARTIFACT_UNREADABLE": (
        "This Draft has an execution record this build cannot interpret, so no "
        "control is offered. It is not started again, because a second execution "
        "under the first one's identity would overwrite a result nobody can "
        "currently read - and a record that cannot be read is exactly the one "
        "worth not overwriting. The detail names the schema and the field."
    ),
}


class LabControlRefused(Exception):
    """A control request was judged and nothing was executed.

    Carries the kind, what it is about, the vocabulary's own statement, and -
    where there is one - the detail that names the particular numbers. The
    statement is never written at the raising site, for the reason
    `assetops_contracts.failures.failure` records one layer along: a message
    composed where it is raised drifts between two sites meaning one thing.

    ## `detail` exists because a statement alone lost an authored explanation

    The cadence refusal below is about two numbers - this signal's rate and this
    run's timestep - and a per-kind statement cannot name them. Before this field
    existed the exception carrying them escaped the port untranslated and reached
    the user as an HTTP 500, so an explanation that had already been written never
    arrived. `detail` is where a raising site puts what only it knows, and it is
    rendered beside the statement rather than instead of it.
    """

    def __init__(
        self, kind: str, subject: str, detail: str | None = None
    ) -> None:
        if kind not in LAB_CONTROL_REFUSALS:
            raise ValueError(
                f"{kind!r} is not a Lab control refusal. A control request is "
                f"refused for one of {sorted(LAB_CONTROL_REFUSALS)}; a run that "
                "could not be set up is refused, a frozen run that may not "
                "execute is blocked, and an execution that stopped has failed."
            )
        self.kind = kind
        self.subject = subject
        self.statement = LAB_CONTROL_REFUSAL_STATEMENTS[kind]
        self.detail = detail
        super().__init__(f"{kind}: {self.statement}")


@dataclass(frozen=True)
class PrivateStateRow:
    """One world quantity at the instant the run has reached.

    Private truth, in the sense v4 section 21 means: the actual stock, exact, as
    the kernel holds it. It is on this record because the Lab is gated and is
    the one surface entitled to see it, and it is on no other record at all.
    """

    address: str
    state_key: str
    value: Fraction
    canonical_unit: str
    kind: str


@dataclass(frozen=True)
class ObservationView:
    """One signal at one instant: what was true, and what was reported.

    The five things criterion 5 asks for, each in its own field so that a screen
    can pin each to its own cell rather than to a paragraph that happens to
    contain all of them.

    `true_value` is the world's; `reported_value` is the freshest reading at or
    before this instant; `reported_source_time` is that reading's OWN time, which
    is what makes a retained value inspectable rather than misleading; `quality`
    says which of the three a reader is looking at; and `outcome` is what the
    sample attempt at THIS instant did, or nothing when none was due.

    The pair that carries the scenario is `true_value` moving while
    `reported_value` does not. Across the shipped reporting gap the tank loses
    120 litres and the newest reading is the one taken before the gap opened, so
    the two columns disagree by that quantity plus whatever the instrument's
    declared bias contributes - which is why they are two fields. A reader who
    wants the quantity the gap hid subtracts the bias from the reported value
    first; a reader who wants to know what the sensor said reads the column.
    """

    address: str
    state_key: str
    device_id: str
    signal_id: str
    reading_class: str
    at_offset_minutes: int
    simulation_time: str
    canonical_unit: str
    true_value: Fraction | None
    reported_value: Fraction | None
    reported_source_time: str | None
    reported_at_offset_minutes: int | None
    quality: str
    due: bool
    outcome: str | None
    suppression_reason: str | None
    cadence_minutes: int
    bias: Fraction
    dropout_per_thousand: int


@dataclass(frozen=True)
class LabProjection:
    """One gated view of one execution: where it is, what is true, what was said.

    Everything a reader needs to judge the run and nothing a product path may
    consume. `inputs_identity` and `content_digest` are what criterion 13 binds:
    two executions of identical frozen content against the same kernel, model,
    publication profile and numeric policy produce the same pair, and a reader
    comparing two runs has both numbers rather than being told they agree.

    `observation_series_digest` is the same claim for the reporting half. The
    world identity deliberately excludes the reporting path, so a trajectory
    digest alone would be identical for two runs whose reports differ - which is
    correct about the world and useless for checking the transform. Two digests
    are what makes "the same world, a changed report series" a statement with
    evidence under it.
    """

    run_id: str
    status: str
    statement: str
    boundaries_completed: int
    boundaries_total: int
    offset_minutes: int
    simulation_time: str
    interval_start_time: str
    interval_end_time: str
    timestep_minutes: int
    seed: int
    kernel_version: int
    model_profile_id: str
    model_profile_version: int
    publication_profile_id: str
    publication_profile_version: int
    numeric_policy: str
    numeric_policy_version: int
    execution_contract_version: int
    inputs_identity: str
    content_digest: str | None
    observation_series_digest: str
    private_state: tuple[PrivateStateRow, ...]
    observations: tuple[ObservationView, ...]
    signals: tuple[DeviceSignalSpec, ...]
    reporting_gaps: tuple[ReportingPathWindow, ...]
    recent_reports: tuple[DeviceObservation, ...]
    reported_count: int
    suppressed_by_gap_count: int
    dropped_count: int
    failure: ExecutionFailure | None = None
    notes: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.status not in LAB_EXECUTION_STATUSES:
            raise ValueError(
                f"A Lab execution is in one of "
                f"{sorted(LAB_EXECUTION_STATUSES)}, not {self.status!r}."
            )
        if self.status == "FAILED" and self.failure is None:
            raise ValueError(
                f"Run {self.run_id} is FAILED and names no reason. A failure "
                "with no record is a run that stopped for reasons nobody can "
                "inspect."
            )
        if self.status != "FAILED" and self.failure is not None:
            raise ValueError(
                f"Run {self.run_id} is {self.status} and carries the failure "
                f"{self.failure.kind}. A partial or finished run may not be "
                "labelled one thing and carry the record of another."
            )
        if (self.content_digest is not None) != (
            self.status in TERMINAL_LAB_STATUSES
        ):
            raise ValueError(
                f"Run {self.run_id} is {self.status} and "
                f"{'carries' if self.content_digest is not None else 'carries no'}"
                " content digest. A digest over a prefix would be an identity "
                "for something that is not yet a thing, and a terminal run "
                "without one could not be compared against a second execution."
            )

    @property
    def is_terminal(self) -> bool:
        return self.status in TERMINAL_LAB_STATUSES

    def view(
        self, device_id: str, signal_id: str
    ) -> ObservationView | None:
        for item in self.observations:
            if item.device_id == device_id and item.signal_id == signal_id:
                return item
        return None


#: What each status tells a reader, placed rather than composed on a screen.
LAB_EXECUTION_STATUS_STATEMENTS: dict[str, str] = {
    # It said "Its frozen inputs are eligible" until a BLOCKED Draft was looked
    # at: NOT_STARTED is the absence of an execution and says nothing about
    # whether one may begin. Whether the frozen inputs may execute is the run's
    # own status, sitting on the same screen and sometimes saying the opposite.
    "NOT_STARTED": (
        "This Draft has not been executed: nothing has run, so there is no "
        "trajectory, no reading and no clock. Whether its frozen inputs MAY "
        "execute is a separate question this status does not answer - the run's "
        "own execution status is what says, and a BLOCKED one is offered no "
        "control at all."
    ),
    "RUNNING": (
        "This execution has reached the instant shown and has not finished. "
        "Everything below is the world and the readings at that instant; the "
        "rest of the interval has not happened."
    ),
    "COMPLETED": (
        "This execution covered its whole interval. The trajectory and the "
        "reading series are final, and the digests beside them are what a "
        "second execution of the same frozen content must reproduce."
    ),
    "FAILED": (
        "This execution stopped before the end of its interval, and the failure "
        "names why and where. What it produced up to that instant is kept: a run "
        "that stopped is still a run somebody needs to inspect."
    ),
    "INTERRUPTED": (
        "An execution of this Draft was running when the process holding it "
        "ended. Its private state lived in that process and was not persisted "
        "as a completed result, so there is nothing to resume and nothing to "
        "show."
    ),
    "ARTIFACT_UNREADABLE": (
        "This Draft has an execution record and this build cannot interpret it. "
        "The record itself is untouched and is not re-executed, rewritten or "
        "discarded: a result silently replaced by a newer one would be the loss "
        "worth avoiding here. The note below names the schema it was written in "
        "and what is missing, which is a question a person can act on."
    ),
}
