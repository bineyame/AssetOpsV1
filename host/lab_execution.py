"""The composed Lab execution: a kernel, a transform, a clock and an artifact.

The second half of the composition leaf. `execution_adapter` projects a frozen
Draft into the two neutral records an execution consumes; this holds the running
handle, pairs private truth with what each device reported, and persists enough
that a completed run can be inspected after the process that ran it is gone.

## Why the private artifact store is here and not in the product

`var/runs` is a product store: a Draft is a record the product wrote and reads
back, and `runs/ports.py` is its seam. A trajectory is not. It is private
simulator truth, and the product having a store of private truth would be the
truth barrier with a filing cabinet in it - a later slice reaching for "the
persisted trajectory" would find one in `assetops_backend` and be right to use it.

So the artifact store is the leaf's. The product receives a `LabProjection`
through a port and cannot name a file, a directory or a format. That also keeps
the configuration-persistence seam honest: `var/executions` is not configuration
and is not registered as a configuration domain, because it is neither authored
nor read as configuration by anything.

## What survives a restart, and what honestly does not

A `COMPLETED` or `FAILED` run persists its whole projection and reloads from it.
A `RUNNING` one persists that it is running and nothing else, because its state
is a live handle in one process: there is no serialized world to resume from, and
inventing one would mean re-executing and calling the result the same run. So a
persisted `RUNNING` record with no live handle reads back as `INTERRUPTED`, which
is criterion 12's "explicit interrupted/unavailable state" and is the honest
answer rather than a convenient one.

## Concurrency

One lock per run, held across read-modify-write of a session. Two controls
arriving together therefore serialize, and the second sees the boundary count the
first produced - which is what makes the `from_boundary` check a guard rather than
a race. The lock is per run rather than global so two runs do not queue behind
each other.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, replace
from fractions import Fraction
from pathlib import Path

import yaml

from assetops_backend.runs.models import SimulationRun
from assetops_backend.runs.profiles import (
    LAB_PUBLICATION_PROFILE,
    PublicationProfile,
)
from assetops_contracts.execution_contract import (
    EXECUTION_CONTRACT_VERSION,
    ExecutionContractIncompatible,
    NUMERIC_POLICY,
    NUMERIC_POLICY_VERSION,
)
from assetops_contracts.failures import ExecutionFailure
from assetops_contracts.lab_projection import (
    LAB_EXECUTION_STATUS_STATEMENTS,
    LabControlRefused,
    LabProjection,
    ObservationView,
    PrivateStateRow,
)
from assetops_contracts.observation import (
    SHAPE_NOT_RECORDED,
    DeviceObservation,
    DeviceSignalSpec,
    FrozenReportingInputs,
    ReportingPathWindow,
    ReportingResolutionUnrepresentable,
    observation_series_digest,
)
from assetops_simulator.kernel.execute import Execution, start
from assetops_simulator.kernel.model import KERNEL_VERSION, ModelSpec
from assetops_simulator.observation.transform import (
    generate_observations,
    outcome_counts,
    reported_reading,
    world_value,
)
from assetops_simulator.packs.fuel import MINIMAL_FUEL_MODEL

from execution_adapter import (
    FrozenRunNotReconstructible,
    RunNotExecutable,
    frozen_world_inputs,
    refuse_a_model_the_run_did_not_select,
    reporting_inputs,
    unconfigured_signals,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]

#: Where a private execution artifact is kept. Under `var/`, which is gitignored
#: user data, and in its own directory rather than beside the Drafts: a Draft is a
#: product record and this is private simulator truth, and a reader deleting one
#: should not have to pick the other out of the same folder.
EXECUTION_ARTIFACT_ROOT = REPOSITORY_ROOT / "var" / "executions"

#: What shape the artifact on disk is in, written into every artifact this build
#: writes and read out of every artifact it reads.
#:
#: **One: the first build that persisted an execution.** Its reporting-gap rows
#: carry an offset, a duration and the interval, and no shape - because the shape
#: was not carried anywhere yet.
#:
#: **Two: the shape and the run's timestep on every gap row**, added when
#: discarding the shape turned a declared instant into a run-long outage.
#:
#: The number exists because the correction that added the field also broke every
#: record written without it: the reader demanded the new key and four completed
#: runs on disk became an HTTP 500 on the screen that exists to inspect them. A
#: reader that learns which rule applied by finding out that a key is absent has
#: no way to tell an old record from a damaged one, and no way to say which.
#: `a-record-older-than-a-rule-is-read-as-what-it-recorded` is the published rule
#: and this integer is how a reader applies it.
#:
#: **And a marker cannot identify what was written before markers existed.** The
#: build that added the shape did not add this field, so it left records with the
#: shape ON them and no number to say so - and the first reader to use this
#: number assigned every unmarked record to schema one and threw that shape away.
#: The fix for "right going forward, silent going backward" was itself right
#: going forward and silent going backward, and it was worse than what it
#: replaced: a `KeyError` is an honest failure, and a confident wrong reading is
#: not. So `_identify_layout` reads the ROWS of an unmarked record, which is the
#: only evidence such a record carries about which build wrote it.
EXECUTION_ARTIFACT_SCHEMA_VERSION = 2

#: The three shapes an execution record on disk actually has, and every one of
#: them was written by a build on this branch.
#:
#: `SCHEMA_2` says so itself. The other two do not, and are told apart by whether
#: their reporting-gap rows carry `timing_shape` - which is the exact field the
#: build that wrote the second of them added. A record whose rows disagree with
#: each other was written by neither and is not interpreted.
LAYOUT_CURRENT = "SCHEMA_2"
LAYOUT_UNMARKED_WITH_SHAPE = "UNMARKED_WITH_SHAPE"
LAYOUT_UNMARKED_WITHOUT_SHAPE = "UNMARKED_WITHOUT_SHAPE"


def _first_pass_end_offset(row: dict[str, object]) -> int:
    """Where the shapeless build's reader put the end of this window.

    Not a guess and not a re-derivation. That build resolved every reporting
    window by one rule - the declared length where there was one, and the end of
    the interval where there was not - over two fields the record still carries.
    So the span those readings were generated against is recoverable exactly,
    which is what lets an old artifact be shown as the result it is.

    What is NOT recoverable is which authored shape produced that span: a window
    ending at the interval's end could have been declared INTERVAL_WIDE or could
    be an absent duration read as one, and those are different documents. The row
    is marked `SHAPE_NOT_RECORDED` rather than given the more likely answer.

    **It applies to that layout and to no other.** Running it over a record whose
    rows DO carry a shape is how a POINT at 1490 - an instant covering
    `[1485, 1500)` - was reported as `[1490, 2460)` with the shape called absent
    while it sat in the same file.
    """
    duration = row.get("duration_minutes")
    if duration is None:
        return int(row["interval_minutes"])
    return int(row["offset_minutes"]) + int(duration)


def _identify_layout(document: dict[str, object], run_id: str) -> str:
    """Which build wrote this record, decided from what the record carries.

    A marked record says so. An unmarked one is one of the two that predate the
    marker, and the difference between them is a field: the later build wrote
    `timing_shape` on every reporting-gap row and the earlier one had no name for
    it. That field is the only evidence such a record holds about its own
    provenance, so it is what decides - and deciding by it is not a guess, it is
    reading the record.

    All or none. A record whose gap rows disagree with each other was written by
    neither build, and interpreting half of it under one rule and half under
    another would be the collapse again with extra steps.

    An unmarked record with no gap rows at all is the shapeless layout by
    default, and nothing turns on the choice: with no row there is no shape to
    report and no span to resolve, so both layouts read it identically.

    Raises:
        ExecutionArtifactUnreadable: the rows do not agree on which build wrote
            them, or the marker is not a whole number.
    """
    marker = document.get("artifact_schema_version")
    if marker is not None:
        # Parsed here rather than at the call site, because a marker that is not
        # a number used to raise `ValueError` from `int()` BEFORE the protected
        # parse and escape as an HTTP 500 - the same failure this whole function
        # exists to stop, one field earlier.
        if isinstance(marker, bool) or not isinstance(marker, int):
            raise ExecutionArtifactUnreadable(
                run_id,
                0,
                f"Its schema marker is {marker!r}, which is not a whole number, "
                "so the record does not say which rule wrote it and nothing "
                "here will decide on its behalf.",
            )
        if marker > EXECUTION_ARTIFACT_SCHEMA_VERSION:
            raise ExecutionArtifactUnreadable(
                run_id,
                marker,
                "A later build wrote it, so what its fields mean is that "
                "build's to say. The record is left exactly as it is.",
            )
        if marker < 1:
            raise ExecutionArtifactUnreadable(
                run_id,
                marker,
                "An artifact schema is a whole number from one upwards, so this "
                "record does not say which rule wrote it.",
            )
        return LAYOUT_CURRENT

    rows = document.get("reporting_gaps") or []
    shaped = [row for row in rows if "timing_shape" in row]
    if not shaped:
        return LAYOUT_UNMARKED_WITHOUT_SHAPE
    if len(shaped) == len(rows) and all(
        "timestep_minutes" in row for row in rows
    ):
        return LAYOUT_UNMARKED_WITH_SHAPE
    raise ExecutionArtifactUnreadable(
        run_id,
        1,
        f"It carries no schema marker, and {len(shaped)} of {len(rows)} "
        "reporting-gap rows record a timing shape. The two builds that wrote "
        "unmarked records wrote it on every row or on none, so this record was "
        "written by neither and reading half of it under each rule would be a "
        "result nobody produced.",
    )


class ExecutionArtifactUnreadable(Exception):
    """A persisted execution record this build cannot interpret.

    Raised rather than a `KeyError`, and carrying the schema version and the
    reason, because the difference between "written by a build I do not know" and
    "damaged" is the whole of what a reader needs and a `KeyError` says neither.
    It is translated at every surface: the read answers `ARTIFACT_UNREADABLE` and
    every control refuses, so nothing re-executes over a record nobody can read.
    """

    def __init__(self, run_id: str, schema_version: int, reason: str) -> None:
        self.run_id = run_id
        self.schema_version = schema_version
        self.reason = reason
        # The version clause only where the versions actually differ. A record
        # damaged at the CURRENT schema would otherwise be announced as
        # "written in schema 2 and this build reads schema 2", which reads as a
        # mismatch and is not one.
        mismatch = (
            ""
            if schema_version == EXECUTION_ARTIFACT_SCHEMA_VERSION
            else (
                f" and this build reads schema "
                f"{EXECUTION_ARTIFACT_SCHEMA_VERSION}"
            )
        )
        super().__init__(
            f"The execution record for {run_id} states artifact schema "
            f"{schema_version}{mismatch}. {reason}"
        )

#: How many of the newest sample attempts a projection carries.
#:
#: A completed run of the shipped scenario makes 164 fuel-level attempts and 41
#: generator ones, and a screen showing all 205 would be a log rather than an
#: inspection. The newest few are what a reader stepping a run wants: what just
#: happened, and what happened either side of it.
RECENT_REPORT_LIMIT = 12


def _exact(text: object, where: str) -> Fraction:
    if not isinstance(text, str):
        raise ValueError(
            f"{where} in a persisted execution artifact is {text!r} and an exact "
            "value is written as a ratio of two whole numbers."
        )
    return Fraction(text)


@dataclass
class LabSession:
    """One live execution of one Draft, with everything it needs to be rendered.

    The handle, the two projected input records, and the reporting notes. Held in
    memory for as long as the process lives, which is the whole of what a live
    execution is.
    """

    run_id: str
    execution: Execution
    reporting: FrozenReportingInputs
    notes: tuple[str, ...]


def _state_key_of(address: str) -> str:
    """The semantic state an `addressed_key` names, whichever form it is in.

    Three spellings and all three appear in a frozen run: a bare key, a key with
    a component after a selector, and a site-wide key behind a scope mark.
    """
    if address.startswith("site:"):
        return address[len("site:") :]
    return address.split("@")[0]


def private_state_rows(execution: Execution) -> tuple[PrivateStateRow, ...]:
    """Every stock the world holds at the instant the run has reached.

    Private truth. It is on the Lab's record because the Lab is gated and is the
    surface entitled to see it; nothing else in this product is handed one.

    Stocks only, and the interval measurements deliberately are not here. A stock
    carries the unit the run froze for it, so the unit on the row is a fact the run
    answered for. An interval measurement's unit is the model's - the fuel pack
    accumulates kilowatt-hours - and this leaf would have to name it on the pack's
    behalf. The interval truth is not lost: it appears in the observation row
    beside what was reported, in the unit the publication profile declared for that
    signal.
    """
    boundaries = execution.boundaries
    if not boundaries:
        return ()
    boundary = boundaries[-1]
    return tuple(
        PrivateStateRow(
            address=address,
            state_key=_state_key_of(address),
            value=value,
            canonical_unit=(
                ""
                if execution.inputs.initial_value(address) is None
                else execution.inputs.initial_value(address).canonical_unit
            ),
            kind="STOCK",
        )
        for address, value in boundary.stocks
    )


def observation_views(
    execution: Execution,
    reporting: FrozenReportingInputs,
    observations: tuple[DeviceObservation, ...],
) -> tuple[ObservationView, ...]:
    """One row per reporting path at the instant the run has reached.

    **This is the deliberate exception to the truth barrier**, and it is the only
    place in the product where a true value and a reported value are fields of one
    record. The transform computes the reported half from the reading series alone
    and cannot see the world; the private state comes from the trajectory and
    cannot see a device. Pairing them is this function's whole job, it happens in
    the leaf, and what it produces goes to a gated surface and nowhere else.
    """
    boundaries = execution.boundaries
    if not boundaries:
        return ()
    boundary = boundaries[-1]
    span = (
        None
        if len(boundaries) < 2
        else boundary.offset_minutes - boundaries[-2].offset_minutes
    )
    views: list[ObservationView] = []
    for signal in reporting.signals:
        reading = reported_reading(
            observations, signal, boundary.offset_minutes
        )
        views.append(
            ObservationView(
                address=signal.address,
                state_key=signal.state_key,
                device_id=signal.device_id,
                signal_id=signal.signal_id,
                reading_class=signal.reading_class,
                at_offset_minutes=boundary.offset_minutes,
                simulation_time=boundary.simulation_time,
                canonical_unit=signal.canonical_unit,
                true_value=world_value(boundary, signal, span),
                reported_value=reading.value,
                reported_source_time=reading.source_sample_time,
                reported_at_offset_minutes=reading.source_offset_minutes,
                quality=reading.quality,
                due=reading.due,
                outcome=reading.outcome,
                suppression_reason=reading.suppression_reason,
                cadence_minutes=signal.cadence_minutes,
                bias=signal.bias,
                dropout_per_thousand=signal.dropout_per_thousand,
            )
        )
    return tuple(views)


def project(session: LabSession) -> LabProjection:
    """The gated view of one live execution, at the instant it has reached."""
    execution = session.execution
    outcome = execution.outcome
    # A started run that has not been stepped is RUNNING at boundary zero. That is
    # a different state from NOT_STARTED, which is what a Draft nothing has
    # executed is, and the Lab shows the difference.
    status = "RUNNING" if outcome is None else outcome

    observations = generate_observations(execution.boundaries, session.reporting)
    counts = outcome_counts(observations)
    final = execution.final
    interval = execution.inputs.interval

    return LabProjection(
        run_id=session.run_id,
        status=status,
        statement=LAB_EXECUTION_STATUS_STATEMENTS[status],
        boundaries_completed=execution.boundaries_completed,
        boundaries_total=execution.boundaries_total,
        offset_minutes=0 if final is None else final.offset_minutes,
        simulation_time=(
            interval.start_time if final is None else final.simulation_time
        ),
        interval_start_time=interval.start_time,
        interval_end_time=interval.end_time,
        timestep_minutes=interval.timestep_minutes,
        seed=execution.inputs.seed,
        kernel_version=KERNEL_VERSION,
        model_profile_id=execution.model.model_profile_id,
        model_profile_version=execution.model.model_profile_version,
        publication_profile_id=session.reporting.publication_profile_id,
        publication_profile_version=(
            session.reporting.publication_profile_version
        ),
        numeric_policy=NUMERIC_POLICY,
        numeric_policy_version=NUMERIC_POLICY_VERSION,
        execution_contract_version=EXECUTION_CONTRACT_VERSION,
        inputs_identity=execution.inputs_identity,
        content_digest=(
            execution.trajectory().content_digest
            if outcome is not None
            else None
        ),
        observation_series_digest=observation_series_digest(observations),
        private_state=private_state_rows(execution),
        observations=observation_views(
            execution, session.reporting, observations
        ),
        signals=session.reporting.signals,
        reporting_gaps=session.reporting.gaps,
        recent_reports=tuple(observations[-RECENT_REPORT_LIMIT:]),
        reported_count=counts.get("REPORTED", 0),
        suppressed_by_gap_count=counts.get("SUPPRESSED_BY_GAP", 0),
        dropped_count=counts.get("DROPPED", 0),
        failure=execution.failure,
        notes=session.notes + execution.notes,
    )


def not_started(
    run: SimulationRun, reporting: FrozenReportingInputs, notes: tuple[str, ...]
) -> LabProjection:
    """The projection of a Draft nothing has executed.

    A real state rather than an absence, because the Lab has to distinguish it
    from an interrupted run and from a run at its first boundary. It carries the
    identities and the declared reporting paths - those are facts about what WOULD
    be executed - and no world quantity and no reading, because nothing has run.
    """
    interval = reporting.interval
    return LabProjection(
        run_id=run.run_id,
        status="NOT_STARTED",
        statement=LAB_EXECUTION_STATUS_STATEMENTS["NOT_STARTED"],
        boundaries_completed=0,
        boundaries_total=len(interval.boundaries),
        offset_minutes=0,
        simulation_time=interval.start_time,
        interval_start_time=interval.start_time,
        interval_end_time=interval.end_time,
        timestep_minutes=interval.timestep_minutes,
        seed=reporting.seed,
        kernel_version=KERNEL_VERSION,
        model_profile_id=run.deterministic_identity.profiles.model_profile_id,
        model_profile_version=(
            run.deterministic_identity.profiles.model_profile_version
        ),
        publication_profile_id=reporting.publication_profile_id,
        publication_profile_version=reporting.publication_profile_version,
        numeric_policy=NUMERIC_POLICY,
        numeric_policy_version=NUMERIC_POLICY_VERSION,
        execution_contract_version=EXECUTION_CONTRACT_VERSION,
        inputs_identity="",
        content_digest=None,
        observation_series_digest=observation_series_digest(()),
        private_state=(),
        observations=(),
        signals=reporting.signals,
        reporting_gaps=reporting.gaps,
        recent_reports=(),
        reported_count=0,
        suppressed_by_gap_count=0,
        dropped_count=0,
        notes=notes,
    )


# --- The private artifact ----------------------------------------------------


def render_projection(projection: LabProjection) -> dict[str, object]:
    """One projection as the mapping the artifact persists.

    Every exact value is written as a ratio of two whole numbers, never as a
    float. That is the same rule `identity.py` holds for a digest payload and for
    the same reason: a persisted trajectory whose numbers came back as binary
    approximations would not be the trajectory that was executed, and an artifact
    that cannot be read back exactly is not evidence of anything.
    """
    return {
        # First, so a person opening the file sees which rule wrote it before
        # they see anything the rule decided.
        "artifact_schema_version": EXECUTION_ARTIFACT_SCHEMA_VERSION,
        "run_id": projection.run_id,
        "status": projection.status,
        "boundaries_completed": projection.boundaries_completed,
        "boundaries_total": projection.boundaries_total,
        "offset_minutes": projection.offset_minutes,
        "simulation_time": projection.simulation_time,
        "interval_start_time": projection.interval_start_time,
        "interval_end_time": projection.interval_end_time,
        "timestep_minutes": projection.timestep_minutes,
        "seed": projection.seed,
        "kernel_version": projection.kernel_version,
        "model_profile_id": projection.model_profile_id,
        "model_profile_version": projection.model_profile_version,
        "publication_profile_id": projection.publication_profile_id,
        "publication_profile_version": projection.publication_profile_version,
        "numeric_policy": projection.numeric_policy,
        "numeric_policy_version": projection.numeric_policy_version,
        "execution_contract_version": projection.execution_contract_version,
        "inputs_identity": projection.inputs_identity,
        "content_digest": projection.content_digest,
        "observation_series_digest": projection.observation_series_digest,
        "reported_count": projection.reported_count,
        "suppressed_by_gap_count": projection.suppressed_by_gap_count,
        "dropped_count": projection.dropped_count,
        "notes": list(projection.notes),
        "failure": (
            None
            if projection.failure is None
            else {
                "kind": projection.failure.kind,
                "subject": projection.failure.subject,
                "statement": projection.failure.statement,
                "at_offset_minutes": projection.failure.at_offset_minutes,
                "detail": list(projection.failure.detail),
            }
        ),
        "private_state": [
            {
                "address": row.address,
                "state_key": row.state_key,
                "value": str(row.value),
                "canonical_unit": row.canonical_unit,
                "kind": row.kind,
            }
            for row in projection.private_state
        ],
        "signals": [
            {
                "device_id": signal.device_id,
                "signal_id": signal.signal_id,
                "address": signal.address,
                "state_key": signal.state_key,
                "reading_class": signal.reading_class,
                "canonical_unit": signal.canonical_unit,
                "cadence_minutes": signal.cadence_minutes,
                "bias": str(signal.bias),
                "dropout_per_thousand": signal.dropout_per_thousand,
                "statement": signal.statement,
            }
            for signal in projection.signals
        ],
        "reporting_gaps": [
            {
                "event_id": window.event_id,
                "condition_address": window.condition_address,
                "device_id": window.device_id,
                "signal_id": window.signal_id,
                "address": window.address,
                # The SHAPE, persisted. An artifact that kept only the offset and
                # the duration could not say whether an absent duration meant an
                # instant or the rest of the run, which is the collapse this
                # field exists to prevent.
                "timing_shape": window.timing_shape,
                "offset_minutes": window.offset_minutes,
                "duration_minutes": window.duration_minutes,
                "interval_minutes": window.interval_minutes,
                "timestep_minutes": window.timestep_minutes,
                # Null on everything this build executes, and the round trip is
                # total only if it is written: a row read back out of a schema
                # one record carries its recorded span and nothing else says so.
                "recorded_end_offset_minutes": (
                    window.recorded_end_offset_minutes
                ),
            }
            for window in projection.reporting_gaps
        ],
        "observations": [
            {
                "address": view.address,
                "state_key": view.state_key,
                "device_id": view.device_id,
                "signal_id": view.signal_id,
                "reading_class": view.reading_class,
                "at_offset_minutes": view.at_offset_minutes,
                "simulation_time": view.simulation_time,
                "canonical_unit": view.canonical_unit,
                "true_value": (
                    None if view.true_value is None else str(view.true_value)
                ),
                "reported_value": (
                    None
                    if view.reported_value is None
                    else str(view.reported_value)
                ),
                "reported_source_time": view.reported_source_time,
                "reported_at_offset_minutes": view.reported_at_offset_minutes,
                "quality": view.quality,
                "due": view.due,
                "outcome": view.outcome,
                "suppression_reason": view.suppression_reason,
                "cadence_minutes": view.cadence_minutes,
                "bias": str(view.bias),
                "dropout_per_thousand": view.dropout_per_thousand,
            }
            for view in projection.observations
        ],
        "recent_reports": [
            {
                "device_id": item.device_id,
                "signal_id": item.signal_id,
                "address": item.address,
                "state_key": item.state_key,
                "reading_class": item.reading_class,
                "at_offset_minutes": item.at_offset_minutes,
                "source_sample_time": item.source_sample_time,
                "outcome": item.outcome,
                "reported_value": (
                    None
                    if item.reported_value is None
                    else str(item.reported_value)
                ),
                "canonical_unit": item.canonical_unit,
                "suppression_reason": item.suppression_reason,
            }
            for item in projection.recent_reports
        ],
    }


def _layout_notes(layout: str, gap_count: int) -> tuple[str, ...]:
    """What a reader is told when the record predates a rule.

    On the projection rather than only in a log, because the person looking at
    the screen is the one who needs to know that a column on it came from
    somewhere unusual, or is missing, and why.

    **Each note describes the record actually read.** The first version of this
    said "the shape is not recoverable from the record" on every unmarked record,
    including the ones that carry the shape - a sentence that was false about the
    file it was printed beside. A note that misdescribes the record is worse than
    no note: it is the silent reinterpretation this correction is about, with a
    paragraph asserting that it did not happen.
    """
    if layout == LAYOUT_CURRENT or gap_count == 0:
        return ()
    if layout == LAYOUT_UNMARKED_WITH_SHAPE:
        return (
            "this execution record was written before an execution record "
            "stated its schema, and after a reporting condition's declared "
            "shape was persisted. The shape shown on each reporting gap below "
            "is the one that record holds, and the span beside it follows from "
            "that shape by the same rule the build that wrote the record "
            "resolved it with - so what is shown is what was computed, not a "
            "re-derivation under a later rule",
        )
    return (
        "this execution record was written before a reporting condition's "
        "declared shape was persisted, so each reporting gap below shows the "
        "span that record was resolved against and no shape. The readings were "
        "generated against exactly that span. Which shape the document declared "
        "is not recoverable from THIS record and is not guessed here; executing "
        "the Draft again would answer it, and would be a second execution rather "
        "than this one",
    )


def _parse_reporting_gap(
    row: dict[str, object], layout: str, run_timestep_minutes: int
) -> ReportingPathWindow:
    """One persisted reporting-gap row, read under the rule that wrote it.

    Two of the three layouts recorded the shape, and for those the shape is what
    resolves the span - not a stored end offset, because the build that wrote
    them resolved by exactly the rule `end_offset_minutes` still applies. Reading
    the shape is therefore reproducing that build's own arithmetic rather than
    re-deriving under a changed one, which is the whole of what makes it honest.

    The third layout recorded no shape, and only there is the span read off the
    row and the shape reported absent.
    """
    if layout in (LAYOUT_CURRENT, LAYOUT_UNMARKED_WITH_SHAPE):
        recorded = row.get("recorded_end_offset_minutes")
        return ReportingPathWindow(
            event_id=str(row["event_id"]),
            condition_address=str(row["condition_address"]),
            device_id=str(row["device_id"]),
            signal_id=str(row["signal_id"]),
            address=str(row["address"]),
            timing_shape=str(row["timing_shape"]),
            offset_minutes=int(row["offset_minutes"]),
            duration_minutes=(
                None
                if row["duration_minutes"] is None
                else int(row["duration_minutes"])
            ),
            interval_minutes=int(row["interval_minutes"]),
            timestep_minutes=int(row["timestep_minutes"]),
            recorded_end_offset_minutes=(
                None if recorded is None else int(recorded)
            ),
        )
    # The shapeless layout. The run's own timestep is on the document and is the
    # timestep this row was resolved under, so it is carried rather than invented
    # - but it decides nothing here, because a recorded span needs no shape rule
    # to resolve it.
    return ReportingPathWindow(
        event_id=str(row["event_id"]),
        condition_address=str(row["condition_address"]),
        device_id=str(row["device_id"]),
        signal_id=str(row["signal_id"]),
        address=str(row["address"]),
        timing_shape=SHAPE_NOT_RECORDED,
        offset_minutes=int(row["offset_minutes"]),
        duration_minutes=(
            None
            if row.get("duration_minutes") is None
            else int(row["duration_minutes"])
        ),
        interval_minutes=int(row["interval_minutes"]),
        timestep_minutes=run_timestep_minutes,
        recorded_end_offset_minutes=_first_pass_end_offset(row),
    )


def parse_projection(document: dict[str, object]) -> LabProjection:
    """One persisted artifact back as the projection it was written from.

    Strict: every exact value goes back through `Fraction`, and a value that is
    not a ratio is refused rather than coerced. An artifact somebody hand-edited
    is the same boundary every other parser in this product guards.

    ## Which build wrote this, asked rather than assumed

    `_identify_layout` answers first, and it decides how the reporting-gap rows
    are built. Three layouts exist on disk and each was written by a build on
    this branch: the current one says its schema, and the two older ones are told
    apart by whether their gap rows carry `timing_shape`.

    Where the shape was recorded it is HONOURED - the row shows what the record
    holds, and the span follows from it by the rule that build resolved with.
    Where it was not, each row is read as the span that build resolved and marked
    `SHAPE_NOT_RECORDED`, so nothing claims to know a shape nobody wrote down.
    The readings were computed against exactly those spans either way, which is
    why showing them is showing the result rather than reconstructing one.

    A record from a LATER schema is refused with `ExecutionArtifactUnreadable`,
    because a build cannot honestly interpret a rule it does not have, and so is
    one whose rows disagree about which build wrote them. That is an answer
    rather than a `KeyError` at whichever field happens to be first.

    Raises:
        ExecutionArtifactUnreadable: the record was written by a build whose
            schema this one does not know, its marker is not a whole number, or
            its rows do not agree on which build wrote them.
    """
    run_id = str(document.get("run_id", "an execution record with no run id"))
    layout = _identify_layout(document, run_id)
    failure = document.get("failure")
    try:
        return LabProjection(
            run_id=str(document["run_id"]),
            status=str(document["status"]),
            statement=LAB_EXECUTION_STATUS_STATEMENTS[str(document["status"])],
            boundaries_completed=int(document["boundaries_completed"]),
            boundaries_total=int(document["boundaries_total"]),
            offset_minutes=int(document["offset_minutes"]),
            simulation_time=str(document["simulation_time"]),
            interval_start_time=str(document["interval_start_time"]),
            interval_end_time=str(document["interval_end_time"]),
            timestep_minutes=int(document["timestep_minutes"]),
            seed=int(document["seed"]),
            kernel_version=int(document["kernel_version"]),
            model_profile_id=str(document["model_profile_id"]),
            model_profile_version=int(document["model_profile_version"]),
            publication_profile_id=str(document["publication_profile_id"]),
            publication_profile_version=int(
                document["publication_profile_version"]
            ),
            numeric_policy=str(document["numeric_policy"]),
            numeric_policy_version=int(document["numeric_policy_version"]),
            execution_contract_version=int(
                document["execution_contract_version"]
            ),
            inputs_identity=str(document["inputs_identity"]),
            content_digest=(
                None
                if document["content_digest"] is None
                else str(document["content_digest"])
            ),
            observation_series_digest=str(document["observation_series_digest"]),
            reported_count=int(document["reported_count"]),
            suppressed_by_gap_count=int(document["suppressed_by_gap_count"]),
            dropped_count=int(document["dropped_count"]),
            notes=(
                tuple(str(note) for note in document.get("notes", ()))
                + _layout_notes(layout, len(document["reporting_gaps"]))
            ),
            failure=(
                None
                if failure is None
                else ExecutionFailure(
                    kind=str(failure["kind"]),
                    subject=str(failure["subject"]),
                    statement=str(failure["statement"]),
                    at_offset_minutes=(
                        None
                        if failure["at_offset_minutes"] is None
                        else int(failure["at_offset_minutes"])
                    ),
                    detail=tuple(str(item) for item in failure["detail"]),
                )
            ),
            private_state=tuple(
                PrivateStateRow(
                    address=str(row["address"]),
                    state_key=str(row["state_key"]),
                    value=_exact(row["value"], f"the value of {row['address']}"),
                    canonical_unit=str(row["canonical_unit"]),
                    kind=str(row["kind"]),
                )
                for row in document["private_state"]
            ),
            signals=tuple(
                DeviceSignalSpec(
                    device_id=str(row["device_id"]),
                    signal_id=str(row["signal_id"]),
                    address=str(row["address"]),
                    state_key=str(row["state_key"]),
                    reading_class=str(row["reading_class"]),
                    canonical_unit=str(row["canonical_unit"]),
                    cadence_minutes=int(row["cadence_minutes"]),
                    bias=_exact(row["bias"], f"the bias of {row['signal_id']}"),
                    dropout_per_thousand=int(row["dropout_per_thousand"]),
                    statement=str(row["statement"]),
                )
                for row in document["signals"]
            ),
            reporting_gaps=tuple(
                _parse_reporting_gap(row, layout, int(document["timestep_minutes"]))
                for row in document["reporting_gaps"]
            ),
            observations=tuple(
                ObservationView(
                    address=str(row["address"]),
                    state_key=str(row["state_key"]),
                    device_id=str(row["device_id"]),
                    signal_id=str(row["signal_id"]),
                    reading_class=str(row["reading_class"]),
                    at_offset_minutes=int(row["at_offset_minutes"]),
                    simulation_time=str(row["simulation_time"]),
                    canonical_unit=str(row["canonical_unit"]),
                    true_value=(
                        None
                        if row["true_value"] is None
                        else _exact(row["true_value"], "a true value")
                    ),
                    reported_value=(
                        None
                        if row["reported_value"] is None
                        else _exact(row["reported_value"], "a reported value")
                    ),
                    reported_source_time=(
                        None
                        if row["reported_source_time"] is None
                        else str(row["reported_source_time"])
                    ),
                    reported_at_offset_minutes=(
                        None
                        if row["reported_at_offset_minutes"] is None
                        else int(row["reported_at_offset_minutes"])
                    ),
                    quality=str(row["quality"]),
                    due=bool(row["due"]),
                    outcome=(
                        None if row["outcome"] is None else str(row["outcome"])
                    ),
                    suppression_reason=(
                        None
                        if row["suppression_reason"] is None
                        else str(row["suppression_reason"])
                    ),
                    cadence_minutes=int(row["cadence_minutes"]),
                    bias=_exact(row["bias"], "a signal bias"),
                    dropout_per_thousand=int(row["dropout_per_thousand"]),
                )
                for row in document["observations"]
            ),
            recent_reports=tuple(
                DeviceObservation(
                    device_id=str(row["device_id"]),
                    signal_id=str(row["signal_id"]),
                    address=str(row["address"]),
                    state_key=str(row["state_key"]),
                    reading_class=str(row["reading_class"]),
                    at_offset_minutes=int(row["at_offset_minutes"]),
                    source_sample_time=str(row["source_sample_time"]),
                    outcome=str(row["outcome"]),
                    reported_value=(
                        None
                        if row["reported_value"] is None
                        else _exact(row["reported_value"], "a reported value")
                    ),
                    canonical_unit=str(row["canonical_unit"]),
                    suppression_reason=(
                        None
                        if row["suppression_reason"] is None
                        else str(row["suppression_reason"])
                    ),
                )
                for row in document["recent_reports"]
            ),
        )
    except KeyError as missing:
        # A record that states its schema and then does not carry what that
        # schema requires is DAMAGED rather than old, and the two need
        # different answers. This one names the field, which a KeyError
        # escaping as an HTTP 500 does not.
        raise ExecutionArtifactUnreadable(
            run_id,
            EXECUTION_ARTIFACT_SCHEMA_VERSION
            if layout == LAYOUT_CURRENT
            else 1,
            f"It was read as the {layout} layout and does not carry {missing}, "
            "which that layout requires. That is a damaged or hand-edited "
            "record rather than an older one, and it is left as it is.",
        ) from missing


class YamlExecutionArtifacts:
    """One file per run under `var/executions`, written whole or not at all.

    The same atomicity discipline the run store uses, for a weaker reason: a
    half-written artifact would read back as an unparseable execution rather than
    as a corrupted product record. It is still worth having, because the failure
    it prevents - a reload that says INTERRUPTED because the write was cut short -
    would be indistinguishable from the real interruption it is meant to report.
    """

    def __init__(self, root: Path = EXECUTION_ARTIFACT_ROOT) -> None:
        self._root = root

    def _path(self, run_id: str) -> Path:
        return self._root / f"{run_id}.yaml"

    def write(self, projection: LabProjection) -> None:
        self._root.mkdir(parents=True, exist_ok=True)
        path = self._path(projection.run_id)
        temporary = path.with_suffix(".yaml.partial")
        temporary.write_text(
            yaml.safe_dump(
                render_projection(projection), sort_keys=False, allow_unicode=True
            ),
            encoding="utf-8",
        )
        temporary.replace(path)

    def read(self, run_id: str) -> LabProjection | None:
        path = self._path(run_id)
        if not path.exists():
            return None
        return parse_projection(
            yaml.safe_load(path.read_text(encoding="utf-8"))
        )

    def note_running(self, projection: LabProjection) -> None:
        """Record that a run is in flight, and nothing about its world.

        Deliberately the projection with its rows still on it, because the rows a
        RUNNING artifact carries are never read back: `read_status` is what a
        reload consults, and it answers INTERRUPTED for anything not terminal. The
        alternative - two artifact shapes - would be a second parser for a record
        nobody reads.
        """
        self.write(projection)


# --- The port the product consumes -------------------------------------------


class HostLabExecution:
    """The execution port, composed. Speaks `SimulationRun` and `LabProjection`.

    The product side of this is a `Protocol` in `assetops_backend.runs`
    `execution_ports`, and this class satisfies it without importing it - which it
    could, since the leaf may import both sides. It does not, because a port is a
    seam the consumer owns: an adapter that inherited from it would make the
    product's own declaration of what it needs depend on something implementing it.
    """

    def __init__(
        self,
        *,
        model: ModelSpec = MINIMAL_FUEL_MODEL,
        publication_profile: PublicationProfile = LAB_PUBLICATION_PROFILE,
        artifacts: YamlExecutionArtifacts | None = None,
    ) -> None:
        self._model = model
        self._publication_profile = publication_profile
        self._artifacts = (
            YamlExecutionArtifacts() if artifacts is None else artifacts
        )
        self._sessions: dict[str, LabSession] = {}
        self._locks: dict[str, threading.Lock] = {}
        self._registry = threading.Lock()

    def _lock_for(self, run_id: str) -> threading.Lock:
        with self._registry:
            return self._locks.setdefault(run_id, threading.Lock())

    def _reporting_for(self, run: SimulationRun) -> FrozenReportingInputs:
        """The reporting inputs, or a typed refusal, and never a raw exception.

        **Every way this can fail is translated here, the cadence check
        included.** It used to be called separately in `start`, outside any
        translation, so a Draft whose timestep the fuel sensor's cadence does not
        divide - `timestep_minutes=30`, an input anybody would try - reached
        READY and then returned HTTP 500 on Start. The refusal's numeric
        explanation had already been written and never reached the user.

        The check belongs here rather than beside the call site because the
        object it is about is built here: a caller holding a
        `FrozenReportingInputs` should be holding one this run can express, and
        the only way to make that true is to refuse before returning it.
        """
        try:
            reporting = reporting_inputs(run, self._publication_profile)
        except ExecutionContractIncompatible as incompatible:
            raise LabControlRefused(
                "CONTRACT_INCOMPATIBLE", run.run_id
            ) from incompatible
        except FrozenRunNotReconstructible as broken:
            raise LabControlRefused(
                "FROZEN_RUN_NOT_RECONSTRUCTIBLE", run.run_id
            ) from broken

        try:
            reporting.refuse_a_cadence_the_run_cannot_express()
        except ReportingResolutionUnrepresentable as unrepresentable:
            # The exception's own message names the signal and the two numbers,
            # and it is carried through as the refusal's detail rather than
            # replaced by a sentence that could not know them.
            raise LabControlRefused(
                "CADENCE_NOT_EXPRESSIBLE", run.run_id, str(unrepresentable)
            ) from unrepresentable
        return reporting

    def _notes(self, run: SimulationRun) -> tuple[str, ...]:
        missing = unconfigured_signals(run, self._publication_profile)
        if not missing:
            return ()
        return (
            "the publication profile declares reporting paths this site does "
            f"not configure, so they publish nothing here: {', '.join(missing)}",
        )

    def projection(self, run: SimulationRun) -> LabProjection:
        """Where this Draft's execution is, without changing it.

        Three answers and they are different facts. A live session is rendered. A
        terminal artifact is read back. A persisted RUNNING record with no live
        session is INTERRUPTED, because its world lived in a process that is gone.
        """
        with self._lock_for(run.run_id):
            session = self._sessions.get(run.run_id)
            if session is not None:
                return project(session)
            try:
                stored = self._artifacts.read(run.run_id)
            except ExecutionArtifactUnreadable as unreadable:
                return self._artifact_unreadable(run, unreadable)
            if stored is not None and stored.is_terminal:
                return stored
            if stored is not None:
                return self._interrupted(run)
            return not_started(
                run, self._reporting_for(run), self._notes(run)
            )

    def _artifact_unreadable(
        self, run: SimulationRun, unreadable: ExecutionArtifactUnreadable
    ) -> LabProjection:
        """A record exists, this build cannot interpret it, and it says so.

        Carrying no world quantity and no reading for the same reason
        INTERRUPTED carries none: there is nothing this build can honestly put
        there. What it does carry is the reason, on the projection, because the
        alternative a reader met before this existed was an HTTP 500.
        """
        base = not_started(run, self._reporting_for(run), self._notes(run))
        return replace(
            base,
            status="ARTIFACT_UNREADABLE",
            statement=LAB_EXECUTION_STATUS_STATEMENTS["ARTIFACT_UNREADABLE"],
            notes=base.notes + (str(unreadable),),
        )

    def _read_or_refuse(self, run: SimulationRun) -> LabProjection | None:
        """The stored record, or a refusal rather than an escaping exception.

        Every control goes through here. A record this build cannot read is not
        "no record": treating it as one would start a second execution under the
        first one's identity and overwrite the very result nobody could read.
        """
        try:
            return self._artifacts.read(run.run_id)
        except ExecutionArtifactUnreadable as unreadable:
            raise LabControlRefused(
                "ARTIFACT_UNREADABLE", run.run_id, str(unreadable)
            ) from unreadable

    def _interrupted(self, run: SimulationRun) -> LabProjection:
        """The same shape as NOT_STARTED, saying a different thing.

        Deliberately carrying no world quantity and no reading, because there are
        none to carry: what the interrupted run produced lived in a process that
        has ended. A projection that showed a prefix here would be showing a run
        that can still be advanced, and it cannot.
        """
        base = not_started(run, self._reporting_for(run), self._notes(run))
        return replace(
            base,
            status="INTERRUPTED",
            statement=LAB_EXECUTION_STATUS_STATEMENTS["INTERRUPTED"],
        )

    def start(self, run: SimulationRun) -> LabProjection:
        """Begin an execution of an eligible Draft, without advancing it."""
        with self._lock_for(run.run_id):
            if run.run_id in self._sessions:
                session = self._sessions[run.run_id]
                if session.execution.is_terminal:
                    raise LabControlRefused(
                        "ALREADY_TERMINAL", run.run_id
                    )
                # Starting an already-started run is a repeat rather than a new
                # execution, and answering with where it is beats either starting
                # a second one or refusing a caller who has lost track.
                return project(session)
            stored = self._read_or_refuse(run)
            if stored is not None and stored.is_terminal:
                raise LabControlRefused("ALREADY_TERMINAL", run.run_id)
            if stored is not None:
                raise LabControlRefused("INTERRUPTED", run.run_id)

            try:
                refuse_a_model_the_run_did_not_select(run, self._model)
                inputs = frozen_world_inputs(run)
            except RunNotExecutable as blocked:
                raise LabControlRefused("RUN_BLOCKED", run.run_id) from blocked
            except ExecutionContractIncompatible as incompatible:
                raise LabControlRefused(
                    "CONTRACT_INCOMPATIBLE", run.run_id
                ) from incompatible
            except FrozenRunNotReconstructible as broken:
                raise LabControlRefused(
                    "FROZEN_RUN_NOT_RECONSTRUCTIBLE", run.run_id
                ) from broken

            reporting = self._reporting_for(run)
            session = LabSession(
                run_id=run.run_id,
                execution=start(inputs, self._model),
                reporting=reporting,
                notes=self._notes(run),
            )
            self._sessions[run.run_id] = session
            projection = project(session)
            self._artifacts.note_running(projection)
            return projection

    def step(
        self, run: SimulationRun, *, boundaries: int, from_boundary: int
    ) -> LabProjection:
        """Advance a started execution by `boundaries` instants.

        `from_boundary` is the position the caller believes the run is at, and it
        is what makes a resubmitted control safe. A double click, a retried
        request or a second tab sends the same number twice; the first advances
        and the second finds the run somewhere else and is refused without
        advancing anything. The whole read-modify-write happens under this run's
        lock, so two controls arriving together cannot both pass the check.
        """
        with self._lock_for(run.run_id):
            session = self._require_session(run)
            if session.execution.is_terminal:
                raise LabControlRefused("ALREADY_TERMINAL", run.run_id)
            if session.execution.boundaries_completed != from_boundary:
                raise LabControlRefused(
                    "STEP_ALREADY_APPLIED",
                    f"{run.run_id} at boundary "
                    f"{session.execution.boundaries_completed}, requested from "
                    f"{from_boundary}",
                )
            session.execution.advance(boundaries)
            return self._persisted(session)

    def run_to_end(self, run: SimulationRun) -> LabProjection:
        """Advance a started execution until its interval is covered."""
        with self._lock_for(run.run_id):
            session = self._require_session(run)
            if session.execution.is_terminal:
                raise LabControlRefused("ALREADY_TERMINAL", run.run_id)
            session.execution.run_to_end()
            return self._persisted(session)

    def _require_session(self, run: SimulationRun) -> LabSession:
        session = self._sessions.get(run.run_id)
        if session is not None:
            return session
        stored = self._read_or_refuse(run)
        if stored is not None and stored.is_terminal:
            raise LabControlRefused("ALREADY_TERMINAL", run.run_id)
        if stored is not None:
            raise LabControlRefused("INTERRUPTED", run.run_id)
        raise LabControlRefused("NOT_STARTED", run.run_id)

    def _persisted(self, session: LabSession) -> LabProjection:
        projection = project(session)
        self._artifacts.write(projection)
        return projection

    def forget(self, run_id: str) -> None:
        """Drop the live handle for one run, as a host restart would.

        The only way to produce a genuine interruption in one process, and it
        exists so that criterion 12's claim can be measured rather than argued
        about. It removes the handle and touches no artifact, which is exactly
        what a process ending does.
        """
        with self._lock_for(run_id):
            self._sessions.pop(run_id, None)
