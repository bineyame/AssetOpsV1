"""Executing a Draft in the Lab, and what each device reported about it.

The composing tests for T022. They live here because they are the only place
allowed to see both sides at once: a `SimulationRun` frozen by the product's own
run setup, a kernel that executes it, a transform that turns what it sampled into
readings, and the gated projection that pairs the two.

Every run is built in process by `RunSetupService` from a Site instantiated by
`SiteCreationService`. None is read out of `var/runs`, and none could be: every
Draft there was frozen against an earlier execution contract and is refused,
which is the guard working rather than an obstacle to route around.

## The numbers these assert, and where they come from

The shipped Fuel Loss Event against MG-001's own Foundation holds 430 L to offset
1080, loses 2799/800 L in each of the sixteen steps of the dispatch window to
reach 374.02 L at 1320, holds that to 1500, loses 40 L in each of the three steps
the removal covers to reach 254.02 L at 1545, and at 2400 takes 245.98 L of a 300
L delivery into a 500 L tank with 54.02 L recorded refused. That trajectory is
derived in the document's own `TRAJECTORY` expectation and asserted to the litre
in `test_shipped_trajectory.py`; what is asserted here is what a DEVICE said
about it.

The demonstration the slice exists for is one row of the projection at offset
1545. The world holds 254.02 L. The newest reading is the 373.52 L the sensor
published at offset 1485, before the reporting gap `[1490, 1580)` opened. The two
disagree by exactly the 120 L the gap hides, and the reading carries its own
source time so nothing pretends otherwise.
"""

from __future__ import annotations

import hashlib
import threading
from dataclasses import replace
from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest
from fixtures import FakeRuns, FakeScenarios, FakeSites, draft, scenario, shipped_document

from assetops_backend.runs.models import SimulationRun
from assetops_backend.runs.parsing import parse_run_document, render_run_document
from assetops_backend.runs.profiles import (
    LAB_PUBLICATION_PROFILE,
    MINIMAL_FUEL_TANK_MODEL,
    DeviceSignalDeclaration,
)
from assetops_contracts.execution_contract import (
    EXECUTION_CONTRACT_VERSION,
    NUMERIC_POLICY,
    REPORTING_RULES,
    sample_due_at,
)
from assetops_contracts.lab_projection import (
    LAB_CONTROL_REFUSALS,
    LabControlRefused,
)
from assetops_contracts.observation import (
    RNG_DOMAIN,
    SAMPLE_OUTCOMES,
    DeviceSignalSpec,
    draw_fraction,
    draw_selects,
    observation_series_digest,
)
from assetops_contracts.trajectory import BoundaryState
from assetops_simulator.kernel.execute import execute, start
from assetops_simulator.kernel.model import KERNEL_VERSION
from assetops_simulator.observation.transform import (
    generate_observations,
    outcome_counts,
    reported_reading,
)

from execution_adapter import (
    frozen_world_inputs,
    reporting_inputs,
    unconfigured_signals,
)
from lab_execution import (
    HostLabExecution,
    LabSession,
    YamlExecutionArtifacts,
    project,
)

TANK = "fuel-tank-volume@fuel-tank"
GENERATOR = "generator-output-power@generator"
FUEL_SIGNAL = ("fuel-level-sensor", "fuel-level")
POWER_SIGNAL = ("generator-controller", "ac-power")

AFTER_DISPATCH = Fraction(18701, 50)  # 374.02 L
AFTER_REMOVAL = Fraction(12701, 50)  # 254.02 L
BIAS = Fraction(-1, 2)

BOUNDARIES = 165
LAST_OFFSET = 2460
BEFORE_THE_GAP = 1485
INSIDE_THE_GAP = 1545
WHEN_REPORTING_RESUMES = 1590

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


# --- Helpers ----------------------------------------------------------------


def executed_to_end(run: SimulationRun | None = None):
    """One completed execution, with the inputs and the readings beside it."""
    record = draft() if run is None else run
    inputs = frozen_world_inputs(record)
    reporting = reporting_inputs(record)
    trajectory = execute(inputs)
    return record, inputs, reporting, trajectory


def readings(trajectory, reporting) -> tuple:
    return generate_observations(trajectory.boundaries, reporting)


def signal(reporting, key: tuple[str, str]) -> DeviceSignalSpec:
    for item in reporting.signals:
        if (item.device_id, item.signal_id) == key:
            return item
    raise AssertionError(f"no signal {key} on this run")


def _requiring_site_demand(document: dict[str, Any]) -> dict[str, Any]:
    """The shipped document with its load forcing raised to REQUIRED.

    The model profile models no site demand at all, so a document that REQUIRES
    it blocks. All three positions naming the state are raised together, because
    a requirement is a property of the address and the role and two positions
    disagreeing is refused at parse rather than blocked at setup.
    """
    for entry in document["timeline"]:
        if entry["event_id"] != "baseline-load-profile":
            continue
        entry["execution_requirement"] = "REQUIRED"
        for parameter in entry["parameters"]:
            parameter["execution_requirement"] = "REQUIRED"
    return document


def _starting_at(document: dict[str, Any], litres: float) -> dict[str, Any]:
    for parameter in document["public_parameters"]:
        if parameter["parameter_id"] == "starting-fuel-level":
            parameter["value"] = litres
    return document


def _at_an_earlier_contract_version(run: SimulationRun) -> SimulationRun:
    """The same run, read back as one frozen under the previous contract.

    Rendered and re-parsed rather than mutated in place, so what comes back is a
    record the product's own strict parser accepted - which is the only way a run
    at another version ever reaches anything.
    """
    document = render_run_document(run)
    document["deterministic_identity"]["profiles"][
        "execution_contract_version"
    ] = EXECUTION_CONTRACT_VERSION - 1
    return parse_run_document(document, source="an earlier run")


def _site_store_digest() -> str:
    """A digest over every document in the writable Site store.

    The whole store rather than one record, and by content rather than by
    modification time: criterion 16 is that executing a draft writes NOTHING to
    accepted Site history, and a check that looked at one Site would miss a write
    to another.
    """
    root = REPOSITORY_ROOT / "var" / "sites"
    digest = hashlib.blake2b(digest_size=32)
    if root.exists():
        for path in sorted(root.rglob("*")):
            if path.is_file():
                digest.update(str(path.relative_to(root)).encode("utf-8"))
                digest.update(path.read_bytes())
    return digest.hexdigest()


def port(tmp_path: Path) -> HostLabExecution:
    """An execution port whose private artifacts land in a temporary directory.

    Never `var/executions`. A test that wrote there would be adding to the user's
    own data to prove something about a run built for one test.
    """
    return HostLabExecution(artifacts=YamlExecutionArtifacts(tmp_path))


# --- Criterion 1: what start accepts, and what it refuses by name -----------


class TestStartAcceptsAnEligibleDraftAndNothingElse:
    def test_an_eligible_draft_starts_without_advancing(
        self, tmp_path: Path
    ) -> None:
        """Starting and stepping are two acts, and the projection shows it.

        A start that also advanced would lose the difference between a Draft
        nothing has executed and a run sitting at its first boundary, and the
        screen shows exactly that difference.
        """
        run = draft()
        execution = port(tmp_path)

        before = execution.projection(run)
        assert before.status == "NOT_STARTED"
        assert before.boundaries_completed == 0
        assert before.observations == ()

        after = execution.start(run)
        assert after.status == "RUNNING"
        assert after.boundaries_completed == 0
        assert after.boundaries_total == BOUNDARIES
        assert after.inputs_identity

    def test_a_blocked_draft_is_refused_by_name(self, tmp_path: Path) -> None:
        run = draft(definition=scenario(_requiring_site_demand(shipped_document())))
        assert run.execution_status == "BLOCKED"

        with pytest.raises(LabControlRefused) as refused:
            port(tmp_path).start(run)

        assert refused.value.kind == "RUN_BLOCKED"
        assert "no override" in refused.value.statement

    def test_a_run_frozen_against_another_contract_is_refused_by_name(
        self, tmp_path: Path
    ) -> None:
        """The guard the whole local run store is currently behind.

        Every Draft in `var/runs` is at an earlier version, so this is not a
        hypothetical: it is what the Lab answers for all 165 of them.
        """
        earlier = _at_an_earlier_contract_version(draft())

        with pytest.raises(LabControlRefused) as refused:
            port(tmp_path).start(earlier)

        assert refused.value.kind == "CONTRACT_INCOMPATIBLE"
        assert "stays readable" in refused.value.statement

    def test_an_already_terminal_run_is_refused_by_name(
        self, tmp_path: Path
    ) -> None:
        run = draft()
        execution = port(tmp_path)
        execution.start(run)
        execution.run_to_end(run)

        with pytest.raises(LabControlRefused) as refused:
            execution.start(run)

        assert refused.value.kind == "ALREADY_TERMINAL"

    def test_stepping_a_run_nobody_started_is_refused_by_name(
        self, tmp_path: Path
    ) -> None:
        with pytest.raises(LabControlRefused) as refused:
            port(tmp_path).step(draft(), boundaries=1, from_boundary=0)

        assert refused.value.kind == "NOT_STARTED"

    def test_every_refusal_kind_carries_a_statement_somebody_wrote(
        self,
    ) -> None:
        """A vocabulary whose members have no statement is a list of names.

        The same rule `EXECUTION_FAILURE_STATEMENTS` holds one layer along, and
        the same reason: the statement is never written at the raising site, so
        two callers meaning one thing cannot drift apart.
        """
        assert LAB_CONTROL_REFUSALS
        for kind in sorted(LAB_CONTROL_REFUSALS):
            refusal = LabControlRefused(kind, "a subject")
            assert len(refusal.statement) > 60
            assert refusal.subject == "a subject"

        with pytest.raises(ValueError):
            LabControlRefused("NOT_A_REFUSAL", "a subject")


# --- Criterion 2: stepping, batching and the simulated clock ----------------


class TestSteppingAdvancesDeclaredSimulationTime:
    def test_a_step_moves_the_clock_by_the_timestep(self, tmp_path: Path) -> None:
        run = draft()
        execution = port(tmp_path)
        execution.start(run)

        first = execution.step(run, boundaries=1, from_boundary=0)
        second = execution.step(run, boundaries=1, from_boundary=1)

        assert first.offset_minutes == 0
        assert first.simulation_time == "2026-09-21T00:00:00Z"
        assert second.offset_minutes == 15
        assert second.simulation_time == "2026-09-21T00:15:00Z"
        assert second.boundaries_completed == 2

    def test_run_to_end_and_a_sequence_of_steps_produce_one_trajectory(
        self,
    ) -> None:
        """Criterion 2, as the pair of digests rather than as a claim.

        Three genuinely different call sequences over three separate handles: one
        advanced to the end in a single call, one advanced a boundary at a time,
        and one in batches of seven. If stepping were re-execution from the start
        this would be trivially true, so the handles are checked to have made the
        number of calls they claim.
        """
        _, inputs, reporting, whole = executed_to_end()

        stepped = start(inputs)
        steps = 0
        while not stepped.is_terminal:
            stepped.advance(1)
            steps += 1
        assert steps == BOUNDARIES

        batched = start(inputs)
        batches = 0
        while not batched.is_terminal:
            batched.advance(7)
            batches += 1
        assert 1 < batches < BOUNDARIES

        one_at_a_time = stepped.trajectory()
        seven_at_a_time = batched.trajectory()

        assert one_at_a_time.content_digest == whole.content_digest
        assert seven_at_a_time.content_digest == whole.content_digest
        assert one_at_a_time.boundaries == whole.boundaries

        # And the READING series too, which the trajectory digest cannot cover:
        # the world's identity excludes the reporting path deliberately.
        assert observation_series_digest(
            readings(one_at_a_time, reporting)
        ) == observation_series_digest(readings(whole, reporting))
        assert observation_series_digest(
            readings(seven_at_a_time, reporting)
        ) == observation_series_digest(readings(whole, reporting))

    def test_execution_speed_does_not_change_a_simulated_timestamp(
        self,
    ) -> None:
        """A timestamp is a function of the offset and the interval start.

        Nothing reads a wall clock, so a run stepped over an hour and a run
        executed in a millisecond carry identical instants. Asserted by comparing
        two handles advanced at different rates rather than by inspecting the
        code that builds the string.
        """
        _, inputs, _, whole = executed_to_end()

        slow = start(inputs)
        while not slow.is_terminal:
            slow.advance(1)

        stamps = {
            boundary.offset_minutes: boundary.simulation_time
            for boundary in whole.boundaries
        }
        assert len(stamps) == BOUNDARIES
        for boundary in slow.boundaries:
            assert stamps[boundary.offset_minutes] == boundary.simulation_time


# --- Criterion 3: a repeated control, and two arriving together -------------


class TestARepeatedControlCannotAdvanceTwice:
    def test_the_same_step_submitted_twice_advances_once(
        self, tmp_path: Path
    ) -> None:
        run = draft()
        execution = port(tmp_path)
        execution.start(run)

        first = execution.step(run, boundaries=1, from_boundary=0)
        assert first.boundaries_completed == 1

        with pytest.raises(LabControlRefused) as refused:
            execution.step(run, boundaries=1, from_boundary=0)

        assert refused.value.kind == "STEP_ALREADY_APPLIED"
        # Nothing advanced, which is the half that matters.
        assert execution.projection(run).boundaries_completed == 1

    def test_two_controls_arriving_together_advance_once(
        self, tmp_path: Path
    ) -> None:
        """Concurrency, with the read-modify-write held under one lock.

        Both threads name the same boundary, so exactly one may advance. Without
        the lock both would read zero, both would pass the check, and the run
        would be two boundaries further on than either caller believes.
        """
        run = draft()
        execution = port(tmp_path)
        execution.start(run)

        ready = threading.Barrier(2)
        outcomes: list[str] = []
        lock = threading.Lock()

        def attempt() -> None:
            ready.wait()
            try:
                execution.step(run, boundaries=1, from_boundary=0)
                result = "advanced"
            except LabControlRefused as refused:
                result = refused.kind
            with lock:
                outcomes.append(result)

        threads = [threading.Thread(target=attempt) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert sorted(outcomes) == ["STEP_ALREADY_APPLIED", "advanced"]
        assert execution.projection(run).boundaries_completed == 1


# --- Criterion 4: a failure is not a refusal --------------------------------


class TestAnExecutionFailureIsNotASetupRefusal:
    def test_a_run_that_stops_comes_back_failed_with_its_reason(
        self, tmp_path: Path
    ) -> None:
        """A draw the tank cannot supply, which is `FAIL_RUN`.

        Starting from 100 L, the dispatch window burns 55.98 L and the removal
        then asks for 120 L that is not there. The run STOPS - it is not refused,
        because it started - and the projection carries the failure and what it
        produced before it.
        """
        run = draft(definition=scenario(_starting_at(shipped_document(), 100)))
        assert run.execution_status == "READY"

        execution = port(tmp_path)
        execution.start(run)
        projection = execution.run_to_end(run)

        assert projection.status == "FAILED"
        assert projection.failure is not None
        assert projection.failure.kind == "INTEGRATION_BOUND_FAILURE"
        assert projection.failure.subject == TANK
        # It kept what it produced. A failed run is still a run somebody has to
        # inspect in order to find out why.
        assert projection.boundaries_completed > 1
        assert projection.content_digest

    def test_a_terminal_run_keeps_its_frozen_identity_and_its_digests(
        self, tmp_path: Path
    ) -> None:
        run = draft()
        execution = port(tmp_path)
        execution.start(run)
        projection = execution.run_to_end(run)

        identity = run.deterministic_identity
        assert projection.status == "COMPLETED"
        assert projection.run_id == run.run_id
        assert projection.seed == identity.seed
        assert projection.model_profile_id == identity.profiles.model_profile_id
        assert (
            projection.publication_profile_version
            == identity.profiles.publication_profile_version
        )
        assert projection.execution_contract_version == EXECUTION_CONTRACT_VERSION
        assert projection.kernel_version == KERNEL_VERSION
        assert projection.numeric_policy == NUMERIC_POLICY
        assert projection.content_digest
        assert projection.observation_series_digest


# --- Criteria 5, 7 and 9: the three columns, and the gap between them -------


class TestWhatTheWorldHeldAndWhatTheDeviceSaid:
    def projection_at(self, offset: int, tmp_path: Path):
        run = draft()
        execution = port(tmp_path)
        execution.start(run)
        # Advanced to the boundary the assertion is about, by stepping, because
        # the Lab's own path is stepping.
        boundaries = offset // 15 + 1
        execution.step(run, boundaries=boundaries, from_boundary=0)
        projection = execution.projection(run)
        assert projection.offset_minutes == offset
        return projection

    def test_the_selected_boundary_carries_all_five_facts(
        self, tmp_path: Path
    ) -> None:
        """Criterion 5, field by field.

        True tank volume, generated reported value, device and signal, source
        sample time, and quality. Each is its own field, because the whole
        difficulty of this screen is that they sit inches apart.
        """
        projection = self.projection_at(BEFORE_THE_GAP, tmp_path)
        view = projection.view(*FUEL_SIGNAL)

        assert view is not None
        assert view.device_id == "fuel-level-sensor"
        assert view.signal_id == "fuel-level"
        assert view.address == TANK
        assert view.true_value == AFTER_DISPATCH
        assert view.reported_value == AFTER_DISPATCH + BIAS
        assert view.reported_source_time == "2026-09-22T00:45:00Z"
        assert view.quality == "GOOD"
        assert view.outcome == "REPORTED"

        # The private stock is on its own row, in its own collection.
        stocks = {row.address: row.value for row in projection.private_state}
        assert stocks[TANK] == AFTER_DISPATCH
        assert stocks[TANK] != view.reported_value

    def test_inside_the_gap_the_world_moves_and_the_reading_does_not(
        self, tmp_path: Path
    ) -> None:
        """The demonstration the scenario was authored for.

        The removal `[1500, 1545)` sits entirely inside the reporting gap
        `[1490, 1580)`. At 1545 the tank has lost its 120 L and the newest reading
        is the one taken at 1485, before the gap opened.
        """
        projection = self.projection_at(INSIDE_THE_GAP, tmp_path)
        view = projection.view(*FUEL_SIGNAL)

        assert view is not None
        assert view.true_value == AFTER_REMOVAL
        assert view.reported_value == AFTER_DISPATCH + BIAS
        assert view.quality == "STALE"
        assert view.due is True
        assert view.outcome == "SUPPRESSED_BY_GAP"
        assert view.reported_at_offset_minutes == BEFORE_THE_GAP
        assert view.reported_source_time != projection.simulation_time
        assert "fuel-level-reporting-gap" in (view.suppression_reason or "")

        # The quantity the gap hides, stated as the arithmetic rather than as a
        # sentence: the difference between the two columns is the removal.
        assert view.true_value - (view.reported_value - BIAS) == Fraction(-120)

    def test_when_reporting_resumes_the_reading_is_the_biased_truth(
        self, tmp_path: Path
    ) -> None:
        projection = self.projection_at(WHEN_REPORTING_RESUMES, tmp_path)
        view = projection.view(*FUEL_SIGNAL)

        assert view is not None
        assert view.true_value == AFTER_REMOVAL
        assert view.reported_value == AFTER_REMOVAL + BIAS
        assert view.quality == "GOOD"
        assert view.outcome == "REPORTED"

    def test_the_generated_reading_is_not_the_authored_one(self) -> None:
        """Criterion 9: generated readings replace authored readings.

        The document authors 254.02 L at offset 1590. The device reports 253.52 L,
        because the sensor reads half a litre low - and the authored number is
        nowhere in the run's output. A runtime that showed the authored value
        would be showing what somebody wrote down, not what a sensor would say.
        """
        run, _, reporting, trajectory = executed_to_end()
        published = readings(trajectory, reporting)

        at_resume = [
            item
            for item in published
            if item.key == (TANK, *FUEL_SIGNAL)
            and item.at_offset_minutes == WHEN_REPORTING_RESUMES
        ]
        assert len(at_resume) == 1
        assert at_resume[0].reported_value == AFTER_REMOVAL + BIAS
        assert at_resume[0].reported_value != AFTER_REMOVAL

        # And no authored reading reached the kernel at all: the record it
        # consumes has no field one could arrive in.
        inputs = frozen_world_inputs(run)
        assert not hasattr(inputs, "readings")
        assert not hasattr(inputs, "expectations")


# --- Criterion 6: what a timestamped reading describes ----------------------


class TestWhatAReadingAtAnInstantDescribes:
    def test_a_state_reading_at_t_is_the_state_after_the_events_at_t(
        self,
    ) -> None:
        """`state-signal-sampled-after-events`, measured at the delivery.

        Offset 2400 is where a 300 L delivery lands on a tank holding 254.02 L
        against a 500 L capacity. The reading there is 500 L minus the bias: the
        post-event stock, never the 254.02 L that preceded it by an instant.
        """
        _, _, reporting, trajectory = executed_to_end()
        published = readings(trajectory, reporting)

        at_delivery = [
            item
            for item in published
            if item.key == (TANK, *FUEL_SIGNAL) and item.at_offset_minutes == 2400
        ]
        assert len(at_delivery) == 1
        assert at_delivery[0].outcome == "REPORTED"
        assert at_delivery[0].reported_value == Fraction(500) + BIAS

    def test_an_interval_reading_describes_the_span_that_just_ended(
        self,
    ) -> None:
        """The dispatch is forced at 45 kW and the reading says 45 kW.

        The kernel accumulates 11.25 kWh over the fifteen minutes ending at 1320;
        the interval reading publishes the mean over that span, which is exactly
        the forced output. Exact arithmetic throughout: 45, not 44.99999999.
        """
        _, _, reporting, trajectory = executed_to_end()
        published = readings(trajectory, reporting)

        at_1320 = [
            item
            for item in published
            if item.key == (GENERATOR, *POWER_SIGNAL)
            and item.at_offset_minutes == 1320
        ]
        assert len(at_1320) == 1
        assert at_1320[0].outcome == "REPORTED"
        assert at_1320[0].reported_value == Fraction(45)
        assert at_1320[0].canonical_unit == "kW"

        measured = trajectory.boundary_at(1320).interval_measurement(GENERATOR)
        assert measured == Fraction(45, 4)  # 11.25 kWh over a quarter hour

    def test_an_interval_reading_is_unavailable_at_the_first_boundary(
        self,
    ) -> None:
        """`no-interval-signal-at-the-first-boundary`, as an outcome.

        Not zero and not the first step's own value: both would attribute a
        number to a span the run never covered.
        """
        _, _, reporting, trajectory = executed_to_end()
        published = readings(trajectory, reporting)

        first = [
            item
            for item in published
            if item.key == (GENERATOR, *POWER_SIGNAL)
            and item.at_offset_minutes == 0
        ]
        assert len(first) == 1
        assert first[0].outcome == "NO_PRECEDING_INTERVAL"
        assert first[0].reported_value is None
        assert trajectory.boundaries[0].has_preceding_interval is False

    def test_a_span_that_ended_with_nothing_measured_is_its_own_answer(
        self,
    ) -> None:
        """Three absences, kept apart.

        At offset 2400 a span has ended and the generator delivered nothing in it,
        which is a different fact from no span having ended and from the path
        being down. The `BoundaryState` docstring already draws the first
        distinction; this is the reporting side of it.
        """
        _, _, reporting, trajectory = executed_to_end()
        published = readings(trajectory, reporting)

        at_2400 = [
            item
            for item in published
            if item.key == (GENERATOR, *POWER_SIGNAL)
            and item.at_offset_minutes == 2400
        ]
        assert len(at_2400) == 1
        assert at_2400[0].outcome == "NO_VALUE_AT_BOUNDARY"
        assert trajectory.boundary_at(2400).has_preceding_interval is True

    def test_every_sample_outcome_the_vocabulary_declares_is_reached(
        self,
    ) -> None:
        """A vocabulary whose members cannot be produced is decoration.

        The same rule `EXECUTION_FAILURE_KINDS` holds, and the same reason this
        project has learnt three slices running: a list of things that look
        protected is not protection. One run of the shipped document reaches all
        five.
        """
        _, _, reporting, trajectory = executed_to_end()
        counts = outcome_counts(readings(trajectory, reporting))

        assert set(counts) == set(SAMPLE_OUTCOMES)
        for outcome in sorted(SAMPLE_OUTCOMES):
            assert counts[outcome] > 0, f"{outcome} was never reached"


# --- Criterion 7: sampling only when due, and the gap -----------------------


class TestSamplingHappensOnlyWhenDue:
    def test_a_sample_exists_at_every_due_instant_and_no_other(self) -> None:
        _, _, reporting, trajectory = executed_to_end()
        published = readings(trajectory, reporting)

        for spec in reporting.signals:
            offsets = {
                item.at_offset_minutes
                for item in published
                if item.key == spec.key
            }
            expected = {
                boundary.offset_minutes
                for boundary in trajectory.boundaries
                if sample_due_at(boundary.offset_minutes, spec.cadence_minutes)
            }
            assert offsets, f"{spec.key} published nothing at all"
            assert offsets == expected

    def test_the_gap_suppresses_every_sample_inside_it_and_none_outside(
        self,
    ) -> None:
        _, _, reporting, trajectory = executed_to_end()
        published = readings(trajectory, reporting)
        window = reporting.gaps[0]

        suppressed = {
            item.at_offset_minutes
            for item in published
            if item.outcome == "SUPPRESSED_BY_GAP"
        }
        assert suppressed == {1500, 1515, 1530, 1545, 1560, 1575}
        assert all(window.covers(offset) for offset in suppressed)
        # The instant reporting resumes is exactly the instant the half-open
        # window excludes, and 1485 is the last one before it opens.
        assert not window.covers(1580)
        assert not window.covers(BEFORE_THE_GAP)

    def test_the_gap_silences_the_signal_it_names_and_not_the_other(
        self,
    ) -> None:
        """Keyed on the signal, not on the address or the component.

        A second sensor on the same tank would be a second path, and nothing about
        one being cut says the other was.
        """
        _, _, reporting, trajectory = executed_to_end()
        published = readings(trajectory, reporting)
        window = reporting.gaps[0]

        assert (window.device_id, window.signal_id) == FUEL_SIGNAL
        generator_inside = [
            item
            for item in published
            if item.key == (GENERATOR, *POWER_SIGNAL)
            and 1490 <= item.at_offset_minutes < 1580
        ]
        assert generator_inside
        assert all(
            item.outcome != "SUPPRESSED_BY_GAP" for item in generator_inside
        )

    def test_a_retained_reading_carries_its_own_time_at_every_gap_instant(
        self,
    ) -> None:
        _, _, reporting, trajectory = executed_to_end()
        published = readings(trajectory, reporting)
        fuel = signal(reporting, FUEL_SIGNAL)

        for offset in (1500, 1515, 1530, 1545, 1560, 1575):
            reading = reported_reading(published, fuel, offset)
            assert reading.quality == "STALE"
            assert reading.source_offset_minutes == BEFORE_THE_GAP
            assert reading.value == AFTER_DISPATCH + BIAS

    def test_a_signal_that_has_never_published_is_unavailable_not_stale(
        self,
    ) -> None:
        """Three states, and the third is not the second with no number.

        At offset 0 the interval signal has published nothing and there is nothing
        to retain, which is a different statement from a retained reading that no
        longer describes now.
        """
        _, _, reporting, trajectory = executed_to_end()
        published = readings(trajectory, reporting)
        power = signal(reporting, POWER_SIGNAL)

        first = reported_reading(published, power, 0)
        assert first.quality == "UNAVAILABLE"
        assert first.value is None
        assert first.source_sample_time is None


# --- Criterion 8: reporting parameters move no world quantity ---------------


class TestChangingTheReportingPathChangesOnlyTheReports:
    def rebuilt(self, reporting, key: tuple[str, str], **changes):
        """The same reporting inputs with one signal's parameters changed."""
        return replace(
            reporting,
            signals=tuple(
                replace(item, **changes)
                if (item.device_id, item.signal_id) == key
                else item
                for item in reporting.signals
            ),
        )

    @pytest.mark.parametrize(
        "changes",
        [
            {"cadence_minutes": 60},
            {"bias": Fraction(3)},
            {"dropout_per_thousand": 400},
        ],
    )
    def test_a_changed_parameter_changes_the_reports_and_not_the_world(
        self, changes: dict
    ) -> None:
        """Criterion 8, three ways, against one world.

        The same trajectory is read twice, because the trajectory cannot differ:
        the kernel is handed a record with no field any of these could arrive in.
        So the assertion is that the reading series moved and the world's identity
        did not.
        """
        _, inputs, reporting, trajectory = executed_to_end()
        before = readings(trajectory, reporting)
        after = readings(
            trajectory, self.rebuilt(reporting, FUEL_SIGNAL, **changes)
        )

        assert before
        assert observation_series_digest(before) != observation_series_digest(
            after
        )
        # The world, re-executed against the unchanged inputs, is the same world.
        again = execute(inputs)
        assert again.content_digest == trajectory.content_digest
        assert again.inputs_identity == trajectory.inputs_identity

    def test_the_kernel_is_handed_no_reporting_parameter_at_all(self) -> None:
        """The structural half, which is what makes the claim hold.

        A rule saying "do not read the cadence" is a rule an adapter can forget.
        A record with no field for one cannot be passed it.
        """
        _, inputs, _, _ = executed_to_end()

        for absent in (
            "signals",
            "cadence_minutes",
            "bias",
            "dropout_per_thousand",
            "gaps",
        ):
            assert not hasattr(inputs, absent)

        # And the one thing it IS told about the reporting path is the addresses,
        # so it can say a declared entry was withheld deliberately rather than
        # silently dropped.
        assert inputs.reporting_path_addresses == (
            "fuel-level-reporting-availability@fuel-tank",
        )

    def test_the_rule_is_published_beside_the_behaviour(self) -> None:
        rule = {item.rule_id: item for item in REPORTING_RULES}[
            "reporting-parameters-move-no-world-quantity"
        ]

        assert "no stock" in rule.statement
        assert "same trajectory" in rule.statement


# --- Criterion 10: the key is the address, the device and the signal --------


class TestTwoReportingPathsAreTwoThings:
    def test_the_shipped_profile_declares_two_devices_and_two_classes(
        self,
    ) -> None:
        _, _, reporting, _ = executed_to_end()

        assert len(reporting.signals) == 2
        assert {item.device_id for item in reporting.signals} == {
            "fuel-level-sensor",
            "generator-controller",
        }
        assert {item.reading_class for item in reporting.signals} == {
            "STATE_SIGNAL",
            "INTERVAL_SIGNAL",
        }
        # Different in every parameter that decides anything, so a change to one
        # is visible as a change to one.
        assert signal(reporting, FUEL_SIGNAL).cadence_minutes == 15
        assert signal(reporting, POWER_SIGNAL).cadence_minutes == 60
        assert signal(reporting, FUEL_SIGNAL).bias == BIAS
        assert signal(reporting, POWER_SIGNAL).bias == 0

    def test_changing_one_path_leaves_the_others_byte_identical(self) -> None:
        """Criterion 10's own claim, and it needs a non-empty other path.

        The generator's series is asserted non-empty before it is asserted
        unchanged: an empty series is unchanged by anything.
        """
        _, _, reporting, trajectory = executed_to_end()
        before = readings(trajectory, reporting)
        after = readings(
            trajectory,
            replace(
                reporting,
                signals=tuple(
                    replace(item, cadence_minutes=45)
                    if (item.device_id, item.signal_id) == FUEL_SIGNAL
                    else item
                    for item in reporting.signals
                ),
            ),
        )

        def series(published, key):
            return tuple(
                item.as_fields() for item in published if item.key == key
            )

        generator = (GENERATOR, *POWER_SIGNAL)
        assert len(series(before, generator)) == 42
        assert series(before, generator) == series(after, generator)
        # And the one that changed really did change.
        fuel = (TANK, *FUEL_SIGNAL)
        assert series(before, fuel) != series(after, fuel)

    def test_one_state_on_two_components_is_two_reporting_paths(self) -> None:
        """Repeated component addresses, at the transform.

        The narrow fuel model relates one tank to one generator and refuses a
        frozen run naming two, so this cannot be shown through a real execution.
        It is a property of the KEY rather than of the kernel, so it is shown
        where it lives: two boundaries' worth of samples on two tanks, read by two
        sensors, come back as two series that do not share a value.
        """
        north = "fuel-tank-volume@north-tank"
        south = "fuel-tank-volume@south-tank"
        boundaries = (
            BoundaryState(
                step_index=0,
                offset_minutes=0,
                simulation_time="2026-09-21T00:00:00Z",
                stocks=((north, Fraction(400)), (south, Fraction(700))),
                forcing_exposures=(),
                state_samples=((north, Fraction(400)), (south, Fraction(700))),
                interval_measurements=(),
                has_preceding_interval=False,
            ),
        )
        specs = tuple(
            DeviceSignalSpec(
                device_id=device,
                signal_id="fuel-level",
                address=address,
                state_key="fuel-tank-volume",
                reading_class="STATE_SIGNAL",
                canonical_unit="L",
                cadence_minutes=15,
                bias=Fraction(0),
                dropout_per_thousand=0,
                statement="a sensor on one tank",
            )
            for device, address in (
                ("north-sensor", north),
                ("south-sensor", south),
            )
        )
        _, _, reporting, _ = executed_to_end()
        published = generate_observations(
            boundaries, replace(reporting, signals=specs, gaps=())
        )

        by_key = {item.key: item.reported_value for item in published}
        assert len(by_key) == 2
        assert by_key[(north, "north-sensor", "fuel-level")] == Fraction(400)
        assert by_key[(south, "south-sensor", "fuel-level")] == Fraction(700)


# --- Criterion 11: the draw contract ----------------------------------------


class TestTheFirstStochasticMechanism:
    def test_the_draw_is_blake2b_over_the_reserved_rng_domain(self) -> None:
        """v4 section 9's family and domain, named rather than assumed.

        Recomputed here from `hashlib` directly, so the assertion is about the
        hash family and the domain separator rather than about the function
        agreeing with itself.
        """
        from assetops_contracts.identity import IDENTITY_DOMAIN, canonical_payload

        assert RNG_DOMAIN == "assetops-sim-rng-v1"
        assert RNG_DOMAIN != IDENTITY_DOMAIN

        payload = canonical_payload([RNG_DOMAIN, "a-stream", 7, ["a", 1]])
        expected = Fraction(
            int.from_bytes(
                hashlib.blake2b(payload, digest_size=32).digest(), "big"
            ),
            2**256,
        )
        assert draw_fraction(7, "a-stream", "a", 1) == expected
        assert 0 <= expected < 1

    def test_a_draw_is_reproducible_and_independent_of_call_order(self) -> None:
        first = draw_fraction(20260927, "one", TANK, 1500)
        second = draw_fraction(20260927, "two", TANK, 1500)

        assert first != second
        # Drawing the second does not move the first, in either order.
        assert draw_fraction(20260927, "one", TANK, 1500) == first
        assert draw_fraction(20260927, "two", TANK, 1500) == second

    def test_a_signal_declaring_no_dropout_still_draws(self) -> None:
        """A threshold of zero selects nothing by comparison, not by shortcut.

        It matters because it makes the threshold the only thing a reader has to
        change to see the mechanism work.
        """
        assert draw_selects(1, "s", 1000, "x") is True
        assert draw_selects(1, "s", 0, "x") is False
        with pytest.raises(ValueError):
            draw_selects(1, "s", 1001, "x")

    def test_adding_an_unrelated_stream_changes_no_existing_stream(self) -> None:
        """Criterion 11, with the existing stream proved non-empty first.

        The fuel sensor drops one sample in twenty-five, and over this interval
        that is a visible handful. Both facts are asserted before the invariant,
        because "adding a stream changed nothing" is trivially true of a stream
        that drew nothing and dropped nothing.
        """
        _, _, reporting, trajectory = executed_to_end()
        before = readings(trajectory, reporting)
        counts = outcome_counts(before)

        # Non-empty, and genuinely stochastic: the mechanism did something.
        assert counts["REPORTED"] > 100
        assert counts["DROPPED"] > 5

        third = DeviceSignalSpec(
            device_id="a-later-device",
            signal_id="a-later-signal",
            address=TANK,
            state_key="fuel-tank-volume",
            reading_class="STATE_SIGNAL",
            canonical_unit="L",
            cadence_minutes=15,
            bias=Fraction(0),
            dropout_per_thousand=500,
            statement="an unrelated stochastic mechanism",
        )
        after = readings(
            trajectory, replace(reporting, signals=reporting.signals + (third,))
        )

        existing = tuple(
            item.as_fields()
            for item in after
            if item.key != third.key
        )
        assert existing == tuple(item.as_fields() for item in before)
        # And the new stream really did draw, so this is not an invariant over a
        # stream that was never consulted.
        new_counts = outcome_counts(
            tuple(item for item in after if item.key == third.key)
        )
        assert new_counts.get("DROPPED", 0) > 0

    def test_the_seed_and_the_reporting_parameters_are_frozen(self) -> None:
        """What a reproduction needs, and where each of it lives.

        The seed is the run's and is frozen on its deterministic identity. The
        cadence, the bias and the dropout are the publication profile's, and the
        run freezes WHICH profile answered and at which version - so the pair
        reconstructs the series without the profile catalog being frozen with it.
        """
        run, _, reporting, _ = executed_to_end()
        identity = run.deterministic_identity

        assert reporting.seed == identity.seed
        assert (
            reporting.publication_profile_id
            == identity.profiles.publication_profile_id
        )
        assert (
            reporting.publication_profile_version
            == identity.profiles.publication_profile_version
        )

    def test_a_profile_the_run_did_not_select_is_refused(self) -> None:
        run = draft()
        other = replace(LAB_PUBLICATION_PROFILE, publication_profile_version=99)

        with pytest.raises(Exception) as raised:
            reporting_inputs(run, other)

        assert "publishes through the profile it selected" in str(raised.value)


# --- Criterion 12: what survives a restart, and what honestly does not ------


class TestPersistedArtifactsAndAnHonestInterruption:
    def test_a_completed_run_reloads_from_its_persisted_artifact(
        self, tmp_path: Path
    ) -> None:
        """Criterion 12: reloadable completed-run inspection.

        The live handle is dropped, which is what a process ending does, and the
        projection comes back from the file with the same digests and the same
        rows it had in memory.
        """
        run = draft()
        execution = port(tmp_path)
        execution.start(run)
        in_memory = execution.run_to_end(run)

        execution.forget(run.run_id)
        reloaded = execution.projection(run)

        assert reloaded.status == "COMPLETED"
        assert reloaded.content_digest == in_memory.content_digest
        assert (
            reloaded.observation_series_digest
            == in_memory.observation_series_digest
        )
        assert reloaded.private_state == in_memory.private_state
        assert reloaded.observations == in_memory.observations
        assert reloaded.reported_count == in_memory.reported_count

    def test_a_run_in_flight_reads_back_as_interrupted(
        self, tmp_path: Path
    ) -> None:
        """The honest answer rather than a convenient one.

        A running execution's state is a live handle in one process. There is no
        serialized world to resume from, and re-executing and calling the result
        the same run would be a second trajectory under the first one's identity.
        """
        run = draft()
        execution = port(tmp_path)
        execution.start(run)
        execution.step(run, boundaries=4, from_boundary=0)

        execution.forget(run.run_id)
        reloaded = execution.projection(run)

        assert reloaded.status == "INTERRUPTED"
        assert reloaded.private_state == ()
        assert reloaded.observations == ()
        assert reloaded.content_digest is None

        # And no control talks past it.
        for control in (
            lambda: execution.start(run),
            lambda: execution.step(run, boundaries=1, from_boundary=4),
            lambda: execution.run_to_end(run),
        ):
            with pytest.raises(LabControlRefused) as refused:
                control()
            assert refused.value.kind == "INTERRUPTED"

    def test_the_artifact_round_trips_every_exact_value(
        self, tmp_path: Path
    ) -> None:
        """Exact in, exact out. No float anywhere on the way.

        A persisted trajectory whose numbers came back as binary approximations
        would not be the trajectory that was executed, and an artifact that cannot
        be read back exactly is not evidence of anything.
        """
        run = draft()
        execution = port(tmp_path)
        execution.start(run)
        written = execution.run_to_end(run)

        stored = YamlExecutionArtifacts(tmp_path).read(run.run_id)
        assert stored is not None
        assert stored == written

        stocks = {row.address: row.value for row in stored.private_state}
        assert isinstance(stocks[TANK], Fraction)
        assert stocks[TANK] == Fraction(500)

    def test_a_draft_nobody_executed_has_no_artifact_and_says_not_started(
        self, tmp_path: Path
    ) -> None:
        run = draft()

        projection = port(tmp_path).projection(run)

        assert projection.status == "NOT_STARTED"
        assert not list(tmp_path.glob("*.yaml"))


# --- Criterion 13: what a second execution must reproduce -------------------


class TestGeneratedArtifactsBindToTheirInputs:
    def test_a_second_execution_of_identical_content_is_canonical(
        self, tmp_path: Path
    ) -> None:
        """Two runs, two identities, one experiment.

        Two Drafts set up identically are two runs of one experiment, so the
        world identity - which excludes the run's own name - agrees, and so do
        both digests. The run ids differ, which is what makes this a claim about
        content rather than about caching.
        """
        first = draft()
        second = draft()
        assert first.run_id != second.run_id

        execution = port(tmp_path)
        execution.start(first)
        one = execution.run_to_end(first)
        execution.start(second)
        two = execution.run_to_end(second)

        assert one.inputs_identity == two.inputs_identity
        assert one.observation_series_digest == two.observation_series_digest
        # The trajectory digest carries the run id, so the two differ there and
        # the boundaries they were taken over do not.
        assert one.private_state == two.private_state
        assert one.observations == two.observations

    def test_the_identity_binds_the_kernel_the_profiles_and_the_policy(
        self,
    ) -> None:
        """Criterion 13, as what changes the number.

        Two runs agreeing on the frozen inputs, the kernel version, the model
        identity and the numeric policy are the same experiment. A kernel version
        outside the digest would let a kernel change and a trace still claim the
        old identity.
        """
        from assetops_contracts.trajectory import frozen_inputs_identity

        _, inputs, _, trajectory = executed_to_end()
        base = dict(
            kernel_version=KERNEL_VERSION,
            model_profile_id=MINIMAL_FUEL_TANK_MODEL.model_profile_id,
            model_profile_version=(
                MINIMAL_FUEL_TANK_MODEL.model_profile_version
            ),
            numeric_policy=NUMERIC_POLICY,
        )
        assert frozen_inputs_identity(inputs, **base) == trajectory.inputs_identity

        for field, value in (
            ("kernel_version", KERNEL_VERSION + 1),
            ("model_profile_version", 99),
            ("numeric_policy", "SOMETHING_ELSE"),
        ):
            assert (
                frozen_inputs_identity(inputs, **{**base, field: value})
                != trajectory.inputs_identity
            )

    def test_the_reading_series_has_an_identity_of_its_own(self) -> None:
        """Two digests, because one could not answer both questions.

        The world's identity excludes the reporting path deliberately, so a
        trajectory digest alone is identical for two runs whose readings differ.
        """
        _, _, reporting, trajectory = executed_to_end()
        published = readings(trajectory, reporting)

        assert published
        assert observation_series_digest(published) == (
            observation_series_digest(published)
        )
        assert observation_series_digest(published) != (
            observation_series_digest(published[:-1])
        )
        assert observation_series_digest(()) != observation_series_digest(
            published
        )


# --- Criterion 16: executing a draft writes nothing ------------------------


class TestExecutingADraftWritesNoSiteHistory:
    def test_the_site_store_is_byte_identical_before_and_after(
        self, tmp_path: Path
    ) -> None:
        """Criterion 16, over the whole writable store rather than one record.

        The digest covers every file under `var/sites`, by path and by content.
        A run that wrote to a site the test did not name would fail here.
        """
        before = _site_store_digest()

        run = draft()
        execution = port(tmp_path)
        execution.start(run)
        projection = execution.run_to_end(run)
        assert projection.status == "COMPLETED"

        assert _site_store_digest() == before

    def test_the_run_setup_the_execution_used_could_not_write_a_site(
        self,
    ) -> None:
        """The structural half: the port it is handed refuses.

        `FakeSites.create_site` raises, so a run route that wrote a Site would
        fail loudly rather than silently. Asserted rather than assumed, because
        the claim above is a measurement and this is the reason it holds.
        """
        with pytest.raises(AssertionError):
            FakeSites().create_site(object())

    def test_there_is_no_commit_or_release_anywhere_on_the_port(
        self, tmp_path: Path
    ) -> None:
        """The scope limit, as an absence of methods rather than a promise.

        A caller cannot commit, stage, release an envelope, reset or inject an
        event, because there is nothing on the port that could.
        """
        execution = port(tmp_path)

        for absent in (
            "commit",
            "release",
            "stage",
            "publish",
            "ingest",
            "reset",
            "inject",
            "rerun",
            "replay",
        ):
            assert not hasattr(execution, absent), absent

        assert sorted(
            name
            for name in dir(execution)
            if not name.startswith("_")
        ) == ["forget", "projection", "run_to_end", "start", "step"]


# --- The composed whole -----------------------------------------------------


class TestTheCompositionItself:
    def test_the_projection_is_built_from_a_session_and_nothing_else(
        self, tmp_path: Path
    ) -> None:
        """The leaf composes; it does not compute.

        A session is a handle, two projected input records and the reporting
        notes. Everything the Lab renders comes from those, which is what keeps
        the crossing in one place.
        """
        run = draft()
        inputs = frozen_world_inputs(run)
        reporting = reporting_inputs(run)
        handle = start(inputs)
        handle.advance(4)

        projection = project(
            LabSession(
                run_id=run.run_id,
                execution=handle,
                reporting=reporting,
                notes=(),
            )
        )

        assert projection.boundaries_completed == 4
        assert projection.offset_minutes == 45
        assert projection.status == "RUNNING"
        assert projection.content_digest is None

    def test_a_declared_signal_this_site_does_not_configure_is_stated(
        self,
    ) -> None:
        """Left out rather than invented, and named rather than dropped.

        A profile is versioned simulator configuration and is the same for every
        Site, so it may declare a signal a given installation has not got. That is
        not an error, but it IS a reason a reading somebody expected is missing.
        """
        run = draft()

        assert unconfigured_signals(run) == ()

        widened = replace(
            LAB_PUBLICATION_PROFILE,
            device_signals=LAB_PUBLICATION_PROFILE.device_signals
            + (
                DeviceSignalDeclaration(
                    device_id="a-sensor-this-site-has-not-got",
                    signal_id="fuel-level",
                    state_key="fuel-tank-volume",
                    reading_class="STATE_SIGNAL",
                    canonical_unit="L",
                    cadence_minutes=15,
                    bias=0.0,
                    dropout_per_thousand=0,
                    statement="declared by the profile, absent from this site",
                ),
            ),
        )
        assert unconfigured_signals(run, widened) == (
            "a-sensor-this-site-has-not-got/fuel-level",
        )
        # And it contributes no reporting path at all, rather than one that
        # publishes nothing for reasons nobody stated.
        assert len(reporting_inputs(run, widened).signals) == 2

    def test_a_cadence_the_run_cannot_express_is_refused(self) -> None:
        """A sample is due at an instant, and the run's instants are its boundaries.

        Neither moving it to the nearest boundary nor skipping it is what the
        cadence says, so it is refused with both numbers named.
        """
        from assetops_contracts.observation import (
            ReportingResolutionUnrepresentable,
        )

        _, _, reporting, _ = executed_to_end()
        awkward = replace(
            reporting,
            signals=tuple(
                replace(item, cadence_minutes=10) for item in reporting.signals
            ),
        )

        with pytest.raises(ReportingResolutionUnrepresentable) as raised:
            awkward.refuse_a_cadence_the_run_cannot_express()

        assert "every 10 minutes" in str(raised.value)
        assert "steps of 15" in str(raised.value)
