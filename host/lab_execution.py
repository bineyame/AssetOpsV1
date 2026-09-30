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

import json
import threading
from dataclasses import dataclass, field, replace
from fractions import Fraction
from pathlib import Path

import yaml

from assetops_backend.runs.models import SimulationRun
from assetops_backend.runs.profiles import PublicationProfile
from assetops_contracts.execution_contract import (
    EXECUTION_CONTRACT_VERSION,
    ExecutionContractIncompatible,
    NUMERIC_POLICY,
    NUMERIC_POLICY_VERSION,
)
from assetops_contracts.failures import ExecutionFailure
from assetops_contracts.control import (
    DISCRETE_UNIT,
    AcceptedControl,
    AcceptedFlow,
    ControlRequest,
    EffectiveControl,
    LoadService,
    ViewEntry,
)
from assetops_contracts.lab_projection import (
    GENERATOR_STATUS_REPORTED_NOT_STAGED,
    LAB_EXECUTION_STATUS_STATEMENTS,
    ElectricalStepRow,
    ElectricalView,
    GeneratorStepRow,
    GeneratorView,
    LabControlRefused,
    LabProjection,
    ObservationView,
    PrivateStateRow,
)
from assetops_contracts.observation import (
    READING_QUALITIES,
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
from assetops_contracts.source_envelope import EnvelopeRejected, SourceMappingSet
from assetops_contracts.trajectory import DiscreteTransition
from assetops_contracts.source_stage import (
    SOURCE_STAGE_STATUS_STATEMENTS,
    SourceStageView,
    StageConflict,
    StageUnreadable,
    release_blockers,
    stage_integrity_digest,
)
from assetops_simulator.gateway.mappings import SIMULATOR_LAB_GATEWAY_MAPPINGS
from assetops_simulator.gateway.publish import publish
from assetops_simulator.packs.fuel import MINIMAL_FUEL_MODEL
from assetops_simulator.packs.mini_grid import GENERATOR_LIFECYCLE, RUN, STOP

from lab_history import (
    HISTORY_MARKER,
    HistoryUnreadable,
    capture as capture_history,
    history_text,
    parse_history,
    render_history,
    without_history,
    write_failed_document,
)
from assetops_contracts.lab_history import LabHistory
from execution_adapter import (
    FrozenRunNotReconstructible,
    RunNotExecutable,
    frozen_world_inputs,
    model_for,
    refuse_a_model_the_run_did_not_select,
    reporting_inputs,
    unconfigured_signals,
)
from source_stages import JsonSourceStages

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
#:
#: **Three: the electrical world (T024)**, an `electrical` key carrying the
#: per-step PV, battery and service rows and the latest step's view, intent,
#: acceptance, flows, loads and effective controls - `null` for a model with
#: no controller. A schema-two record is read as what it recorded: no
#: electrical view, because none was written.
#:
#: **Four: the generator (T025a)**, an optional `generator` key inside
#: `electrical` carrying the lifecycle state at T and over each step, the
#: request, the accepted output, fuel, and every discrete transition with its
#: phase, cause and instant. Four is written ONLY for a record that carries a
#: generator: a record without one has exactly the schema-three layout, so it
#: is still written as three and every pre-change Draft re-executes to the
#: same bytes (the contract-9 merge gate). A three that carries a generator,
#: or a four that does not, is refused as damaged.
#:
#: **Five: typed discrete readings (T025b)**. An observation or recent-report
#: row in unit `state` carries its true and reported values as the member text
#: (`RUNNING`) rather than a ratio, which a schema-four reader would refuse as
#: an inexact number. Five is written ONLY for a record carrying such a row, so
#: every record without one keeps its number and bytes; a five without a
#: discrete reading, or a lower marker with one, is refused as damaged.
EXECUTION_ARTIFACT_SCHEMA_VERSION = 5

#: The schema a record carrying a generator, and no discrete reading, is
#: written in (T025a's layout, unchanged).
SCHEMA_WITH_GENERATOR = 4

#: The schema a record without a generator is written in: its layout did not
#: change, so its number does not either.
SCHEMA_WITHOUT_GENERATOR = 3


def _carries_discrete_readings(projection) -> bool:
    return any(
        row.canonical_unit == DISCRETE_UNIT
        for row in (*projection.observations, *projection.recent_reports)
    )


def _schema_written(projection) -> int:
    if _carries_discrete_readings(projection):
        return EXECUTION_ARTIFACT_SCHEMA_VERSION
    electrical = projection.electrical
    if electrical is not None and electrical.generator is not None:
        return SCHEMA_WITH_GENERATOR
    return SCHEMA_WITHOUT_GENERATOR

#: The three shapes an execution record on disk actually has, and every one of
#: them was written by a build on this branch.
#:
#: `SCHEMA_2` says so itself. The other two do not, and are told apart by whether
#: their reporting-gap rows carry `timing_shape` - which is the exact field the
#: build that wrote the second of them added. A record whose rows disagree with
#: each other was written by neither and is not interpreted.
#:
#: The names say `UNMARKED` because that is how those two records reach us, but
#: what they identify is a SERIALIZED SHAPE rather than the presence of a
#: marker. A record that states `artifact_schema_version: 1` is naming the
#: shapeless layout explicitly, and is read as that layout if its rows agree -
#: no build wrote such a record, and honouring what one says is still what
#: "a reader decides which rule applied by reading it" means.
LAYOUT_CURRENT = "SCHEMA_3"
LAYOUT_SCHEMA_2 = "SCHEMA_2"
LAYOUT_UNMARKED_WITH_SHAPE = "UNMARKED_WITH_SHAPE"
LAYOUT_UNMARKED_WITHOUT_SHAPE = "UNMARKED_WITHOUT_SHAPE"

#: How each layout is described to a person, so a message never has to
#: interpolate a constant whose spelling is an implementation detail - and never
#: has to call a record that states a marker "unmarked".
LAYOUT_DESCRIPTIONS = {
    LAYOUT_CURRENT: (
        "the current layout, which records a reporting condition's shape and "
        "the run's timestep on every gap row, and the electrical world"
    ),
    LAYOUT_SCHEMA_2: (
        "schema 2, which records a reporting condition's shape and the run's "
        "timestep on every gap row and predates the electrical world"
    ),
    LAYOUT_UNMARKED_WITH_SHAPE: (
        "the layout that records a reporting condition's shape and states no "
        "schema of its own"
    ),
    LAYOUT_UNMARKED_WITHOUT_SHAPE: (
        "the layout written before a reporting condition's shape was recorded "
        "at all"
    ),
}


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


def _identify_layout(
    document: dict[str, object], run_id: str
) -> tuple[str, int | None]:
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

    **A stated marker is obeyed, including one no build wrote.** The first
    version of this refused only a marker above the current version or below
    one, so `artifact_schema_version: 1` fell through to the current layout and
    was then told, in the failure message, that it stated a 2. Ignoring what a
    record says about itself and asserting a different number in its place is
    the confident wrong reading this whole correction is about, arriving inside
    the correction.

    Returns:
        The layout, and the marker the record states - `None` where it states
        none. The marker travels because a message about a record must report
        the number that record carries and not the one this build writes.

    Raises:
        ExecutionArtifactUnreadable: the rows do not agree on which build wrote
            them, the marker is not a whole number, or the marker names a layout
            the rows contradict.
    """
    rows = document.get("reporting_gaps") or []
    shaped = [row for row in rows if "timing_shape" in row]
    stepped = [row for row in rows if "timestep_minutes" in row]
    marker = document.get("artifact_schema_version")

    if marker is not None:
        # Parsed here rather than at the call site, because a marker that is not
        # a number used to raise `ValueError` from `int()` BEFORE the protected
        # parse and escape as an HTTP 500 - the same failure this whole function
        # exists to stop, one field earlier.
        if isinstance(marker, bool) or not isinstance(marker, int):
            raise ExecutionArtifactUnreadable(
                run_id,
                None,
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
        if marker == 1:
            # Schema one names the shapeless layout, and a record claiming it
            # while carrying shapes is claiming two things at once. Reading it
            # under either rule would honour half of what it says.
            if shaped:
                raise ExecutionArtifactUnreadable(
                    run_id,
                    marker,
                    f"It states schema 1, which is the layout written before a "
                    f"reporting condition's shape was recorded, and "
                    f"{len(shaped)} of {len(rows)} of its reporting-gap rows "
                    "record a shape. The marker and the rows describe different "
                    "layouts, and honouring one would mean ignoring the other.",
                )
            return LAYOUT_UNMARKED_WITHOUT_SHAPE, marker
        if marker == 2:
            return LAYOUT_SCHEMA_2, marker
        electrical = document.get("electrical")
        carries_generator = isinstance(electrical, dict) and "generator" in electrical
        if carries_generator != (marker >= SCHEMA_WITH_GENERATOR):
            raise ExecutionArtifactUnreadable(
                run_id,
                marker,
                f"It states schema {marker} and "
                + ("carries" if carries_generator else "does not carry")
                + " a generator. Schemas 4 and 5 are written only when a "
                "generator is recorded and schema 3 exactly when none is, so "
                "the marker and the record disagree.",
            )
        carries_discrete = any(
            isinstance(row, dict) and row.get("canonical_unit") == DISCRETE_UNIT
            for key in ("observations", "recent_reports")
            for row in (document.get(key) or ())
        )
        if carries_discrete != (marker == EXECUTION_ARTIFACT_SCHEMA_VERSION):
            raise ExecutionArtifactUnreadable(
                run_id,
                marker,
                f"It states schema {marker} and "
                + ("carries" if carries_discrete else "does not carry")
                + " a discrete (enum) reading. Schema 5 is written exactly when "
                "a reading in unit 'state' is recorded, so the marker and the "
                "record disagree.",
            )
        return LAYOUT_CURRENT, marker

    if not shaped:
        return LAYOUT_UNMARKED_WITHOUT_SHAPE, None
    if len(shaped) == len(rows) and len(stepped) == len(rows):
        return LAYOUT_UNMARKED_WITH_SHAPE, None
    # Name the field that actually decided. Counting only `timing_shape` here
    # produced "1 of 1 rows record a timing shape ... so this record was written
    # by neither": a sentence that states agreement and concludes disagreement,
    # while the field that disagreed went unmentioned.
    disagreeing = (
        "a timing shape" if len(shaped) != len(rows) else "the run's timestep"
    )
    counted = shaped if len(shaped) != len(rows) else stepped
    raise ExecutionArtifactUnreadable(
        run_id,
        None,
        f"It carries no schema marker, and {len(counted)} of {len(rows)} "
        f"reporting-gap rows record {disagreeing}. The two builds that wrote "
        "unmarked records wrote both fields on every row or neither on any, so "
        "this record was written by neither and reading half of it under each "
        "rule would be a result nobody produced.",
    )


class ExecutionArtifactUnreadable(Exception):
    """A persisted execution record this build cannot interpret.

    Raised rather than a `KeyError`, and carrying the schema version and the
    reason, because the difference between "written by a build I do not know" and
    "damaged" is the whole of what a reader needs and a `KeyError` says neither.
    It is translated at every surface: the read answers `ARTIFACT_UNREADABLE` and
    every control refuses, so nothing re-executes over a record nobody can read.
    """

    def __init__(
        self, run_id: str, schema_version: int | None, reason: str
    ) -> None:
        self.run_id = run_id
        self.schema_version = schema_version
        self.reason = reason
        # Three openings, because there are three things a record can say about
        # its own schema and reporting the wrong one is its own small lie. A
        # record damaged at the CURRENT schema announced as "written in schema 2
        # and this build reads schema 2" reads as a mismatch and is not one; a
        # record whose marker is a word has no number at all, and printing a
        # placeholder for one - "states artifact schema 0" - invents a fact the
        # very next sentence contradicts.
        if schema_version is None:
            states = "does not state a readable artifact schema"
        elif schema_version in (
            EXECUTION_ARTIFACT_SCHEMA_VERSION,
            SCHEMA_WITH_GENERATOR,
            SCHEMA_WITHOUT_GENERATOR,
        ):
            states = f"states artifact schema {schema_version}"
        else:
            states = (
                f"states artifact schema {schema_version} and this build reads "
                f"schema {EXECUTION_ARTIFACT_SCHEMA_VERSION}"
            )
        super().__init__(
            f"The execution record for {run_id} {states}. {reason}"
        )

#: How many of the newest sample attempts a projection carries.
#:
#: A completed run of the shipped scenario makes 164 fuel-level attempts and 41
#: generator ones, and a screen showing all 205 would be a log rather than an
#: inspection. The newest few are what a reader stepping a run wants: what just
#: happened, and what happened either side of it.
RECENT_REPORT_LIMIT = 12


def _reading(text: object, unit: object, where: str) -> Fraction | str:
    """A persisted reading value, typed by its unit (T025b).

    A reading in unit `state` is a generator lifecycle member - the only
    discrete signal this build publishes - and is refused if it is not one;
    every other reading is an exact ratio.
    """
    if unit == DISCRETE_UNIT:
        return _member(text, _LIFECYCLE, where)
    return _exact(text, where)


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
    #: The publication identities the Draft froze and the gateway mapping this
    #: session stages under. The mapping is captured when the run starts, so a
    #: change to the gateway's current mapping mid-run cannot mix two mappings
    #: into one stage.
    site_id: str = ""
    source_id: str = ""
    gateway_id: str = ""
    mapping: SourceMappingSet = SIMULATOR_LAB_GATEWAY_MAPPINGS
    #: What staging had to say, e.g. a refused conflicting publication. Mutable,
    #: because it accrues as the run is stepped.
    staging_notes: list[str] = field(default_factory=list)


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


def with_reported_generator_status(
    electrical: ElectricalView | None,
    reporting: FrozenReportingInputs,
    observations: tuple[DeviceObservation, ...],
) -> ElectricalView | None:
    """T025b: put the REPORTED generator status beside the physical one.

    Only when the run publishes a discrete status reading about the generator's
    state address (publication profile 4, on a Site that configures it). Each
    step row gains the status a consumer sees at the step's instant T - the
    newest reading at or before T, from the reading series alone - and its
    quality, so a missing or retained (STALE) status sits beside the private
    state it did or did not describe. Nothing here reads back into the world:
    the trajectory is already complete when this runs.
    """
    if electrical is None or electrical.generator is None:
        return electrical
    generator = electrical.generator
    status = next(
        (
            signal
            for signal in reporting.signals
            if signal.is_discrete and signal.address == generator.state_address
        ),
        None,
    )
    if status is None:
        return electrical
    steps = []
    for row in generator.steps:
        reading = reported_reading(observations, status, row.from_offset)
        steps.append(
            replace(
                row,
                reported_state=(
                    None if reading.value is None else str(reading.value)
                ),
                reported_quality=reading.quality,
            )
        )
    return replace(
        electrical,
        generator=replace(
            generator,
            steps=tuple(steps),
            reported_status=GENERATOR_STATUS_REPORTED_NOT_STAGED,
        ),
    )


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
        notes=session.notes + tuple(session.staging_notes) + execution.notes,
        electrical=with_reported_generator_status(
            electrical_view(execution), session.reporting, observations
        ),
    )

# --- The electrical world (T024) ---------------------------------------------


def electrical_view(execution: Execution) -> ElectricalView | None:
    """The electrical world of an execution whose model has a controller.

    Built from the trajectory's own control steps - what the controller saw,
    asked for and what was accepted - and nothing else. `None` for a model
    with no controller, which is the fuel model.
    """
    steps: list[ElectricalStepRow] = []
    generator_steps: list[GeneratorStepRow] = []
    generator_state = ""
    fuel_address = ""
    latest = None
    battery = ""
    zero = AcceptedFlow("absent", "", "", Fraction(0), Fraction(0))
    for boundary in execution.boundaries:
        step = boundary.control_step
        if step is None:
            continue
        accepted = step.accepted
        flows = {item.flow_id: item for item in accepted.flows}
        # T025a: a model with a generator names two more flows; for the
        # daytime model they are absent and contribute nothing, so its rows
        # are exactly the T024 rows.
        generator_to_load = flows.get("generator_to_load", zero).mean_power
        generator_to_battery = flows.get("generator_to_battery", zero).mean_power
        account = accepted.stock_accounts[0]
        battery = account.address
        soc_start = boundary.stock(account.address) or Fraction(0)
        request = step.intent.requests[0]
        control = accepted.controls[0]
        reserve = accepted.effective_controls[0]
        steps.append(
            ElectricalStepRow(
                from_offset=accepted.from_offset,
                to_offset=accepted.to_offset,
                simulation_time=boundary.simulation_time,
                soc_start=soc_start,
                soc_end=soc_start + account.delta,
                reserve=reserve.value,
                reserve_origin=reserve.origin,
                pv_potential=flows["pv_potential"].mean_power,
                pv_output=(
                    flows["pv_to_load"].mean_power
                    + flows["pv_to_battery"].mean_power
                ),
                curtailed=flows["curtailed_pv"].mean_power,
                clipped=flows["inverter_clipping"].mean_power,
                battery_power=(
                    flows["battery_to_load"].mean_power
                    - flows["pv_to_battery"].mean_power
                    - generator_to_battery
                ),
                requested_battery_power=request.requested,
                limited_by=control.limited_by,
                demand=flows["load_demand"].mean_power,
                served=(
                    flows["pv_to_load"].mean_power
                    + flows["battery_to_load"].mean_power
                    + generator_to_load
                ),
                unserved=flows["unserved_load"].mean_power,
            )
        )
        run = next(
            (item for item in step.intent.requests if item.quantity == "generator-run"),
            None,
        )
        if run is not None:
            generator_state = run.address
            outcome = next(
                item for item in accepted.controls if item.quantity == "generator-run"
            )
            fuel = next(
                item for item in accepted.stock_accounts if item.outflows == ("generator_output",)
            )
            fuel_address = fuel.address
            fuel_start = boundary.stock(fuel.address) or Fraction(0)
            generator_steps.append(
                GeneratorStepRow(
                    from_offset=accepted.from_offset,
                    to_offset=accepted.to_offset,
                    simulation_time=boundary.simulation_time,
                    state_at_t=boundary.discrete_state(run.address) or "",
                    state_for_step=boundary.discrete_state_for_step(run.address) or "",
                    requested=str(run.requested),
                    request_reason=run.reason,
                    output=flows["generator_output"].mean_power,
                    to_load=generator_to_load,
                    to_battery=generator_to_battery,
                    fuel_start=fuel_start,
                    fuel_end=fuel_start + fuel.delta,
                    limited_by=outcome.limited_by,
                )
            )
        latest = step
    if latest is None:
        return None
    generator = (
        None
        if not generator_steps
        else GeneratorView(
            state_address=generator_state,
            fuel_address=fuel_address,
            steps=tuple(generator_steps),
            transitions=execution.discrete_transitions,
        )
    )
    return ElectricalView(
        battery_address=battery,
        steps=tuple(steps),
        latest_view=latest.view.entries,
        latest_requests=latest.intent.requests,
        latest_controls=latest.accepted.controls,
        latest_loads=latest.accepted.loads,
        latest_flows=latest.accepted.flows,
        latest_effective_controls=latest.accepted.effective_controls,
        latest_balances=tuple(
            item.identity_id for item in latest.accepted.balances
        ),
        latest_segments=latest.accepted.segments,
        notes=latest.accepted.notes,
        generator=generator,
    )


def _text(value: Fraction | str | None) -> str | None:
    return None if value is None else str(value)


def render_electrical(view: ElectricalView | None) -> dict[str, object] | None:
    """The electrical view as the artifact persists it, exact as ratios."""
    if view is None:
        return None
    return {
        "battery_address": view.battery_address,
        "steps": [
            {
                "from_offset": row.from_offset,
                "to_offset": row.to_offset,
                "simulation_time": row.simulation_time,
                "soc_start": str(row.soc_start),
                "soc_end": str(row.soc_end),
                "reserve": str(row.reserve),
                "reserve_origin": row.reserve_origin,
                "pv_potential": str(row.pv_potential),
                "pv_output": str(row.pv_output),
                "curtailed": str(row.curtailed),
                "clipped": str(row.clipped),
                "battery_power": str(row.battery_power),
                "requested_battery_power": str(row.requested_battery_power),
                "limited_by": list(row.limited_by),
                "demand": str(row.demand),
                "served": str(row.served),
                "unserved": str(row.unserved),
            }
            for row in view.steps
        ],
        "latest_view": [
            {
                "name": item.name,
                "address": item.address,
                "value": _text(item.value),
                "unit": item.unit,
            }
            for item in view.latest_view
        ],
        "latest_requests": [
            {
                "address": item.address,
                "quantity": item.quantity,
                "requested": str(item.requested),
                "unit": item.unit,
                "reason": item.reason,
            }
            for item in view.latest_requests
        ],
        "latest_controls": [
            {
                "address": item.address,
                "quantity": item.quantity,
                "requested": str(item.requested),
                "accepted": str(item.accepted),
                "unit": item.unit,
                "limited_by": list(item.limited_by),
            }
            for item in view.latest_controls
        ],
        "latest_loads": [
            {
                "address": item.address,
                "priority_rank": item.priority_rank,
                "demand_energy": str(item.demand_energy),
                "served_energy": str(item.served_energy),
                "unserved_energy": str(item.unserved_energy),
                "demand_power": str(item.demand_power),
                "served_power": str(item.served_power),
                "unserved_power": str(item.unserved_power),
            }
            for item in view.latest_loads
        ],
        "latest_flows": [
            {
                "flow_id": item.flow_id,
                "from_address": item.from_address,
                "to_address": item.to_address,
                "energy": str(item.energy),
                "mean_power": str(item.mean_power),
            }
            for item in view.latest_flows
        ],
        "latest_effective_controls": [
            {
                "address": item.address,
                "from_offset": item.from_offset,
                "to_offset": item.to_offset,
                "value": str(item.value),
                "unit": item.unit,
                "origin": item.origin,
                "provenance": item.provenance,
            }
            for item in view.latest_effective_controls
        ],
        "latest_balances": list(view.latest_balances),
        "latest_segments": [list(item) for item in view.latest_segments],
        "notes": list(view.notes),
    } | ({} if view.generator is None else {"generator": _render_generator(view.generator)})


def _render_generator(view: GeneratorView) -> dict[str, object]:
    """T025a. The generator as artifact schema 4 persists it."""
    return {
        "state_address": view.state_address,
        "fuel_address": view.fuel_address,
        "reported_status": view.reported_status,
        "steps": [
            {
                "from_offset": row.from_offset,
                "to_offset": row.to_offset,
                "simulation_time": row.simulation_time,
                "state_at_t": row.state_at_t,
                "state_for_step": row.state_for_step,
                "requested": row.requested,
                "request_reason": row.request_reason,
                "output": str(row.output),
                "to_load": str(row.to_load),
                "to_battery": str(row.to_battery),
                "fuel_start": str(row.fuel_start),
                "fuel_end": str(row.fuel_end),
                "limited_by": list(row.limited_by),
            }
            # T025b: written only when a status reading exists (schema 5), so
            # a schema-4 record keeps its bytes.
            | (
                {}
                if row.reported_quality is None
                else {
                    "reported_state": row.reported_state,
                    "reported_quality": row.reported_quality,
                }
            )
            for row in view.steps
        ],
        "transitions": [
            {
                "address": item.address,
                "state_key": item.state_key,
                "previous": item.previous,
                "next": item.next,
                "phase": item.phase,
                "cause": item.cause,
                "controller_ref": item.controller_ref,
                "at_offset_minutes": item.at_offset_minutes,
                "simulation_time": item.simulation_time,
            }
            for item in view.transitions
        ],
    }


#: T025a. The two closed vocabularies a persisted discrete value may take: a
#: lifecycle member (a physical state), or a request naming one (RUN / STOP).
_LIFECYCLE = frozenset(GENERATOR_LIFECYCLE.allowed_values)
_REQUESTS = frozenset({RUN, STOP})


def _member(value: object, allowed: frozenset[str], where: str) -> str:
    """A persisted enum member: text, and declared. The original type is
    checked before anything converts it, so `1` is refused rather than
    becoming `'1'`, and an undeclared member is refused rather than passed on."""
    if not isinstance(value, str):
        raise ValueError(
            f"{where} in a persisted execution artifact is {value!r} and an "
            f"enum member is written as text, one of {sorted(allowed)}."
        )
    if value not in allowed:
        raise ValueError(
            f"{where} in a persisted execution artifact is {value!r}, which is "
            f"not one of the declared members {sorted(allowed)}."
        )
    return value


def _parse_generator(raw: object) -> GeneratorView:
    """T025a. The persisted generator, strictly: members stay text, numbers
    go back through `Fraction`."""
    if not isinstance(raw, dict):
        raise KeyError("generator")

    def x(value: object, where: str) -> Fraction:
        return _exact(value, where)

    return GeneratorView(
        state_address=str(raw["state_address"]),
        fuel_address=str(raw["fuel_address"]),
        reported_status=str(raw["reported_status"]),
        steps=tuple(
            GeneratorStepRow(
                from_offset=int(row["from_offset"]),
                to_offset=int(row["to_offset"]),
                simulation_time=str(row["simulation_time"]),
                state_at_t=_member(row["state_at_t"], _LIFECYCLE, "a generator state_at_t"),
                state_for_step=_member(row["state_for_step"], _LIFECYCLE, "a generator state_for_step"),
                requested=_member(row["requested"], _REQUESTS, "a generator request"),
                request_reason=str(row["request_reason"]),
                output=x(row["output"], "a generator output"),
                to_load=x(row["to_load"], "a generator output"),
                to_battery=x(row["to_battery"], "a generator output"),
                fuel_start=x(row["fuel_start"], "a fuel volume"),
                fuel_end=x(row["fuel_end"], "a fuel volume"),
                limited_by=tuple(str(item) for item in row["limited_by"]),
                reported_state=(
                    None
                    if row.get("reported_state") is None
                    else _member(
                        row["reported_state"], _LIFECYCLE, "a reported generator status"
                    )
                ),
                reported_quality=(
                    None
                    if row.get("reported_quality") is None
                    else _member(
                        row["reported_quality"],
                        READING_QUALITIES,
                        "a reported status quality",
                    )
                ),
            )
            for row in raw["steps"]
        ),
        transitions=tuple(
            DiscreteTransition(
                address=str(item["address"]),
                state_key=str(item["state_key"]),
                previous=_member(item["previous"], _LIFECYCLE, "a transition previous state"),
                next=_member(item["next"], _LIFECYCLE, "a transition next state"),
                phase=str(item["phase"]),
                cause=str(item["cause"]),
                controller_ref=(
                    None if item["controller_ref"] is None else str(item["controller_ref"])
                ),
                at_offset_minutes=int(item["at_offset_minutes"]),
                simulation_time=str(item["simulation_time"]),
            )
            for item in raw["transitions"]
        ),
    )


def _typed_value(
    value: object, unit: str, where: str, allowed: frozenset[str] = _LIFECYCLE
):
    """A persisted control value: a discrete member stays text and stays
    declared (T025a)."""
    if unit == DISCRETE_UNIT:
        return _member(value, allowed, where)
    return _exact(value, where)


def parse_electrical(raw: object) -> ElectricalView | None:
    """The persisted electrical view, strictly. A value that is not a ratio
    is refused, as everywhere else in the artifact."""
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise KeyError("electrical")

    def x(value: object, where: str) -> Fraction:
        return _exact(value, where)

    return ElectricalView(
        battery_address=str(raw["battery_address"]),
        steps=tuple(
            ElectricalStepRow(
                from_offset=int(row["from_offset"]),
                to_offset=int(row["to_offset"]),
                simulation_time=str(row["simulation_time"]),
                soc_start=x(row["soc_start"], "a state of charge"),
                soc_end=x(row["soc_end"], "a state of charge"),
                reserve=x(row["reserve"], "a reserve"),
                reserve_origin=str(row["reserve_origin"]),
                pv_potential=x(row["pv_potential"], "a PV potential"),
                pv_output=x(row["pv_output"], "a PV output"),
                curtailed=x(row["curtailed"], "a curtailment"),
                clipped=x(row["clipped"], "a clipping"),
                battery_power=x(row["battery_power"], "a battery power"),
                requested_battery_power=x(
                    row["requested_battery_power"], "a requested power"
                ),
                limited_by=tuple(str(item) for item in row["limited_by"]),
                demand=x(row["demand"], "a demand"),
                served=x(row["served"], "a service"),
                unserved=x(row["unserved"], "an unserved load"),
            )
            for row in raw["steps"]
        ),
        latest_view=tuple(
            ViewEntry(
                name=str(row["name"]),
                address=str(row["address"]),
                value=(
                    None
                    if row["value"] is None
                    else _typed_value(row["value"], str(row["unit"]), "a view value")
                ),
                unit=str(row["unit"]),
            )
            for row in raw["latest_view"]
        ),
        latest_requests=tuple(
            ControlRequest(
                address=str(row["address"]),
                quantity=str(row["quantity"]),
                requested=_typed_value(row["requested"], str(row["unit"]), "a request", _REQUESTS),
                unit=str(row["unit"]),
                reason=str(row["reason"]),
            )
            for row in raw["latest_requests"]
        ),
        latest_controls=tuple(
            AcceptedControl(
                address=str(row["address"]),
                quantity=str(row["quantity"]),
                requested=_typed_value(row["requested"], str(row["unit"]), "a request", _REQUESTS),
                accepted=_typed_value(row["accepted"], str(row["unit"]), "an accepted power"),
                unit=str(row["unit"]),
                limited_by=tuple(str(item) for item in row["limited_by"]),
            )
            for row in raw["latest_controls"]
        ),
        latest_loads=tuple(
            LoadService(
                address=str(row["address"]),
                priority_rank=int(row["priority_rank"]),
                demand_energy=x(row["demand_energy"], "a demand"),
                served_energy=x(row["served_energy"], "a service"),
                unserved_energy=x(row["unserved_energy"], "an unserved load"),
                demand_power=x(row["demand_power"], "a demand"),
                served_power=x(row["served_power"], "a service"),
                unserved_power=x(row["unserved_power"], "an unserved load"),
            )
            for row in raw["latest_loads"]
        ),
        latest_flows=tuple(
            AcceptedFlow(
                flow_id=str(row["flow_id"]),
                from_address=str(row["from_address"]),
                to_address=str(row["to_address"]),
                energy=x(row["energy"], "a flow energy"),
                mean_power=x(row["mean_power"], "a flow power"),
            )
            for row in raw["latest_flows"]
        ),
        latest_effective_controls=tuple(
            EffectiveControl(
                address=str(row["address"]),
                from_offset=int(row["from_offset"]),
                to_offset=int(row["to_offset"]),
                value=x(row["value"], "a control value"),
                unit=str(row["unit"]),
                origin=str(row["origin"]),
                provenance=str(row["provenance"]),
            )
            for row in raw["latest_effective_controls"]
        ),
        latest_balances=tuple(str(item) for item in raw["latest_balances"]),
        latest_segments=tuple(
            (int(item[0]), int(item[1])) for item in raw["latest_segments"]
        ),
        notes=tuple(str(item) for item in raw["notes"]),
        generator=(
            _parse_generator(raw["generator"]) if "generator" in raw else None
        ),
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
        "artifact_schema_version": _schema_written(projection),
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
        "electrical": render_electrical(projection.electrical),
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
    if layout in (LAYOUT_CURRENT, LAYOUT_SCHEMA_2) or gap_count == 0:
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
    if layout in (LAYOUT_CURRENT, LAYOUT_SCHEMA_2, LAYOUT_UNMARKED_WITH_SHAPE):
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
    layout, marker = _identify_layout(document, run_id)
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
                        else _reading(
                            row["true_value"],
                            row["canonical_unit"],
                            "a true value",
                        )
                    ),
                    reported_value=(
                        None
                        if row["reported_value"] is None
                        else _reading(
                            row["reported_value"],
                            row["canonical_unit"],
                            "a reported value",
                        )
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
                        else _reading(
                            row["reported_value"],
                            row["canonical_unit"],
                            "a reported value",
                        )
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
            # Required at schema three, where `null` is the answer for a model
            # with no controller; absent at every earlier layout, which wrote
            # no electrical world.
            electrical=(
                parse_electrical(document["electrical"])
                if layout == LAYOUT_CURRENT
                else None
            ),
        )
    except KeyError as missing:
        # A record that states its schema and then does not carry what that
        # schema requires is DAMAGED rather than old, and the two need
        # different answers. This one names the field, which a KeyError
        # escaping as an HTTP 500 does not.
        raise ExecutionArtifactUnreadable(
            run_id,
            # The marker the RECORD states, not the one this build writes. It
            # used to be the module constant whenever the record was read as
            # the current layout, so a file saying 1 was announced as saying 2.
            marker,
            f"It was read as {LAYOUT_DESCRIPTIONS[layout]}, and does not carry "
            f"{missing}, which that layout requires. That is a damaged or "
            "hand-edited record rather than an older one, and it is left as it "
            "is.",
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

    def write(
        self, projection: LabProjection, history: dict | None = None
    ) -> None:
        """Replace this run's artifact whole: the projection, then its history.

        The projection document is byte-for-byte what every earlier build
        wrote. A terminal run's history follows it after `HISTORY_MARKER` as a
        second document (T025c), so the pair is replaced by one rename and a
        reader never sees a projection with another write's history.
        """
        self._root.mkdir(parents=True, exist_ok=True)
        path = self._path(projection.run_id)
        temporary = path.with_suffix(".yaml.partial")
        text = yaml.safe_dump(
            render_projection(projection), sort_keys=False, allow_unicode=True
        )
        if history is not None:
            text += history_text(history)
        temporary.write_text(text, encoding="utf-8")
        temporary.replace(path)

    def _texts(self, run_id: str) -> tuple[str, str | None] | None:
        path = self._path(run_id)
        if not path.exists():
            return None
        head, marker, tail = path.read_text(encoding="utf-8").partition(
            HISTORY_MARKER
        )
        return head, (tail if marker else None)

    def read(self, run_id: str) -> LabProjection | None:
        """The projection alone. A history after it is never parsed here."""
        texts = self._texts(run_id)
        if texts is None:
            return None
        return parse_projection(yaml.safe_load(texts[0]))

    def read_history(self, run_id: str, projection: LabProjection) -> LabHistory:
        """This run's persisted history, strictly verified, or why there is none.

        Reads and never writes: an unreadable history is reported as
        HISTORY_UNREADABLE and left on disk exactly as it was.
        """
        texts = self._texts(run_id)
        if texts is None or texts[1] is None:
            return without_history(projection, "LEGACY_ARTIFACT")
        try:
            document = json.loads(texts[1])
        except ValueError as error:
            return without_history(
                projection,
                "HISTORY_UNREADABLE",
                f"The history of {run_id} is not a readable document: {error}",
            )
        try:
            return parse_history(document, projection)
        except HistoryUnreadable as unreadable:
            return without_history(
                projection, "HISTORY_UNREADABLE", str(unreadable)
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
        model: ModelSpec | None = None,
        # T025b: None resolves each run's frozen publication profile (the
        # build carries versions three and four); a test may inject one.
        publication_profile: PublicationProfile | None = None,
        artifacts: YamlExecutionArtifacts | None = None,
        stages: JsonSourceStages | None = None,
        gateway_mapping: SourceMappingSet = SIMULATOR_LAB_GATEWAY_MAPPINGS,
    ) -> None:
        self._model = model
        self._publication_profile = publication_profile
        self._artifacts = (
            YamlExecutionArtifacts() if artifacts is None else artifacts
        )
        self._stages = JsonSourceStages() if stages is None else stages
        self._gateway_mapping = gateway_mapping
        self._sessions: dict[str, LabSession] = {}
        self._locks: dict[str, threading.Lock] = {}
        self._registry = threading.Lock()

    def _model_for(self, run: SimulationRun) -> ModelSpec:
        """The model this run executes against.

        The injected one when a caller composed one - a test proving the
        identity check does - and otherwise the executable model whose identity
        the run froze (T024: there are two).
        """
        if self._model is not None:
            return self._model
        try:
            return model_for(run)
        except FrozenRunNotReconstructible as broken:
            raise LabControlRefused(
                "FROZEN_RUN_NOT_RECONSTRUCTIBLE", run.run_id
            ) from broken

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
            reporting = reporting_inputs(
                run, self._publication_profile, self._model_for(run)
            )
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
        missing = unconfigured_signals(
            run, self._publication_profile, self._model_for(run)
        )
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
                model = self._model_for(run)
                refuse_a_model_the_run_did_not_select(run, model)
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
            publication = run.deterministic_identity.publication
            session = LabSession(
                run_id=run.run_id,
                execution=start(inputs, model),
                reporting=reporting,
                notes=self._notes(run),
                site_id=run.deterministic_identity.site.site_id,
                source_id=publication.simulator_source_id or "",
                gateway_id=publication.gateway_id or "",
                mapping=self._gateway_mapping,
            )
            self._sessions[run.run_id] = session
            # Staged before the artifact says the run is running, so the stage
            # exists - and has frozen its mapping - from the run's first instant.
            self._stage(session)
            projection = project(session)
            if projection.is_terminal:
                self._artifacts.write(
                    projection, self._history_document(session, projection)
                )
            else:
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
        # The stage is written before the execution artifact. That order alone
        # does NOT make eligibility honest - the independent review showed a
        # failed final stage write with the process still alive, and a caught
        # publication refusal, both reading as eligible. What does is the
        # stage's own publication watermark: eligibility requires it to reach
        # the run's last boundary, and it moves only when a stage write
        # succeeds. The order does one narrower thing: when the stage write
        # RAISES, the step aborts before the artifact is written. It does not
        # keep the artifact behind the stage in general - a publication refusal
        # is caught in `_stage` by design, the artifact is then written, and
        # the persisted execution can be ahead of the stage's watermark (the
        # review, R5, measured 106 against 105). The watermark is what keeps
        # that divergence from reading as releasable.
        self._stage(session)
        projection = project(session)
        self._artifacts.write(
            projection, self._history_document(session, projection)
        )
        return projection

    def _captured(
        self, session: LabSession, projection: LabProjection
    ) -> LabHistory:
        return capture_history(
            session.execution,
            session.reporting,
            generate_observations(session.execution.boundaries, session.reporting),
            run_id=session.run_id,
            status=projection.status,
            content_digest=projection.content_digest,
            observation_series_digest=projection.observation_series_digest,
        )

    def _history_document(
        self, session: LabSession, projection: LabProjection
    ) -> dict | None:
        """The history a terminal artifact carries, or the record that it failed.

        None for a run still going: a RUNNING artifact is never read back, so a
        history in it would be rewritten at every step for nobody. A history
        that cannot be built is written as a WRITE_FAILED record with its
        reason, so the result reads back as finished with its history stated
        missing - never as a durable complete cockpit.
        """
        if not projection.is_terminal:
            return None
        try:
            return render_history(self._captured(session, projection), projection)
        except Exception as error:  # noqa: BLE001 - the failure is the record
            return write_failed_document(
                projection,
                f"The history of {projection.run_id} could not be recorded: "
                f"{type(error).__name__}: {error}",
            )

    def history(self, run: SimulationRun) -> LabHistory:
        """What this Draft's execution recorded, without executing anything.

        A live session answers with its in-memory prefix. A terminal artifact
        answers with its persisted history, verified, or says it has none.
        Anything else - never executed, interrupted, unreadable - has no
        history and says which.
        """
        with self._lock_for(run.run_id):
            session = self._sessions.get(run.run_id)
            if session is not None:
                return self._captured(session, project(session))
            try:
                stored = self._artifacts.read(run.run_id)
            except ExecutionArtifactUnreadable as unreadable:
                return without_history(
                    self._artifact_unreadable(run, unreadable),
                    "HISTORY_UNREADABLE",
                    str(unreadable),
                )
            if stored is not None and stored.is_terminal:
                return self._artifacts.read_history(run.run_id, stored)
            if stored is not None:
                return without_history(self._interrupted(run), "NOT_RECORDED")
            return without_history(
                not_started(run, self._reporting_for(run), self._notes(run)),
                "NOT_RECORDED",
            )

    def _stage(self, session: LabSession) -> None:
        """Publish the reading series so far through the gateway, into the stage.

        The whole series every time, which is the retry case by construction:
        every envelope staged by an earlier step is re-published with the same
        message id and the same content, and admission counts it as already
        staged rather than staging it twice.

        A refused admission does not stop the execution - the world has already
        advanced - and it is not swallowed either: the stage's publication
        watermark does not move, so the stage stays ineligible for release (after
        a reload too), a content conflict is also recorded by id, and the
        projection says what happened.
        """
        observations = generate_observations(
            session.execution.boundaries, session.reporting
        )
        try:
            envelopes = publish(
                observations,
                session.mapping,
                session.reporting.interval,
                site_id=session.site_id,
                source_id=session.source_id,
                gateway_id=session.gateway_id,
            )
            self._stages.admit(
                run_id=session.run_id,
                site_id=session.site_id,
                source_id=session.source_id,
                gateway_id=session.gateway_id,
                mapping=session.mapping,
                envelopes=envelopes,
                boundaries_total=session.execution.boundaries_total,
                # Every boundary so far was just published in full, so the
                # watermark moves to here - but only if this write succeeds. A
                # failed write or a refusal below leaves it where it was, and
                # the stage stays ineligible even after its execution completes.
                published_through=session.execution.boundaries_completed,
            )
        except (StageConflict, StageUnreadable, EnvelopeRejected) as refused:
            note = (
                "staging refused a publication and changed nothing already "
                f"staged: {refused}"
            )
            if note not in session.staging_notes:
                session.staging_notes.append(note)

    def staged_envelopes(self, run: SimulationRun) -> SourceStageView:
        """This Draft's staged envelopes, re-read from persistence and verified.

        Never read from a live session: what the inspector presents is what a
        reload reads, which is criterion 9's "reloaded content matches what the
        inspector presents as releasable" as a property of where the data comes
        from. A Draft whose live handle is gone reads exactly the same.
        """
        with self._lock_for(run.run_id):
            execution_status = self._execution_status(run)
            try:
                stored = self._stages.read(run.run_id)
            except StageUnreadable as unreadable:
                return SourceStageView(
                    run_id=run.run_id,
                    status="STAGE_UNREADABLE",
                    statement=SOURCE_STAGE_STATUS_STATEMENTS["STAGE_UNREADABLE"],
                    execution_status=execution_status,
                    release_blockers=release_blockers(
                        "STAGE_UNREADABLE", execution_status, None
                    ),
                    stage=None,
                    integrity_digest=None,
                    unreadable_detail=unreadable.detail,
                )
            status = "NOT_STAGED" if stored is None else "STAGED"
            return SourceStageView(
                run_id=run.run_id,
                status=status,
                statement=SOURCE_STAGE_STATUS_STATEMENTS[status],
                execution_status=execution_status,
                release_blockers=release_blockers(
                    status, execution_status, stored
                ),
                stage=stored,
                integrity_digest=(
                    None if stored is None else stage_integrity_digest(stored)
                ),
            )

    def _execution_status(self, run: SimulationRun) -> str:
        """Where the execution publishing into a stage is, without executing.

        Cheaper than a projection and never refused: a stage is readable for a
        Draft whatever its execution's state, including one frozen under an
        earlier contract.
        """
        session = self._sessions.get(run.run_id)
        if session is not None:
            outcome = session.execution.outcome
            return "RUNNING" if outcome is None else outcome
        try:
            stored = self._artifacts.read(run.run_id)
        except ExecutionArtifactUnreadable:
            return "ARTIFACT_UNREADABLE"
        if stored is None:
            return "NOT_STARTED"
        return stored.status if stored.is_terminal else "INTERRUPTED"

    def forget(self, run_id: str) -> None:
        """Drop the live handle for one run, as a host restart would.

        The only way to produce a genuine interruption in one process, and it
        exists so that criterion 12's claim can be measured rather than argued
        about. It removes the handle and touches no artifact, which is exactly
        what a process ending does.
        """
        with self._lock_for(run_id):
            self._sessions.pop(run_id, None)
