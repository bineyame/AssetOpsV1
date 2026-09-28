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
differ by 119.50 L - the 120 L removal with the sensor's -0.5 L bias taken back
out, which the assertions below do explicitly - and the reading carries its own
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
import yaml
from fastapi.testclient import TestClient
from fixtures import (
    HYBRID_TEMPLATE,
    FakeRuns,
    FakeScenarios,
    FakeSites,
    draft,
    scenario,
    shipped_document,
    site_from_template,
)

from assetops_backend.config import FeatureFlags
from assetops_backend.main import create_app
from assetops_backend.sites.models import SiteRecord

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
    LAB_EXECUTION_STATUS_STATEMENTS,
    LAB_EXECUTION_STATUSES,
    LabControlRefused,
)
from assetops_contracts.observation import (
    RNG_DOMAIN,
    SHAPE_NOT_RECORDED,
    ReportingPathWindow,
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
    EXECUTION_ARTIFACT_SCHEMA_VERSION,
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

#: The shipped reporting gap redeclared as each of the other two shapes. Its
#: offset is 1490 - the authored condition opens ten minutes before the removal -
#: so a POINT there belongs to the step `[1485, 1500)` and suppresses the sample
#: due at 1485. That is one instant, which is the point of the shape.
POINT_AT_THE_GAP_OFFSET = {"shape": "POINT"}
INTERVAL_WIDE = {"shape": "INTERVAL_WIDE"}


def _reporting_condition_as(timing: dict[str, Any]) -> dict[str, Any]:
    """The shipped document with its reporting gap declared as another shape.

    Only the `timing` block changes. The condition keeps its identity, its
    address, its role and its requirement, so what the assertions compare is the
    shape and nothing else. An INTERVAL_WIDE entry starts at offset zero, which
    is what `interval-wide-span` says of every interval-wide entry.
    """
    document = shipped_document()
    for entry in document["timeline"]:
        if entry["event_id"] != "fuel-level-reporting-gap":
            continue
        entry["timing"] = dict(timing)
        if timing["shape"] == "INTERVAL_WIDE":
            entry["offset_minutes"] = 0
    return document


def _mg_001() -> SiteRecord:
    """The Site the shipped document targets, instantiated in memory."""
    return site_from_template(HYBRID_TEMPLATE, site_id="MG-001")


def _persisted(run: SimulationRun) -> tuple[SimulationRun, FakeRuns]:
    """One Draft in a store the composed application can read it back from."""
    store = FakeRuns()
    store.create_run(run)
    return run, store



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

    def test_a_run_from_an_earlier_build_names_the_contract_not_the_profile(
        self, tmp_path: Path
    ) -> None:
        """The ordering a browser found, as a regression test.

        A run frozen under an earlier contract ALSO names an earlier publication
        profile, because the two moved together in T022. Asking about the profile
        first answers "this run does not determine one experiment" for a run whose
        real answer is "these are not the rules it was frozen under" - the
        narrower of the two facts, and the less useful one.

        No suite could see it: every fixture in this repository is built in
        process at the current version, so nothing had a run that failed both
        checks. This is that run, built by hand from a rendered document and
        re-parsed, so what reaches the port is a record the strict parser
        accepted.
        """
        document = render_run_document(draft())
        profiles = document["deterministic_identity"]["profiles"]
        profiles["execution_contract_version"] = EXECUTION_CONTRACT_VERSION - 1
        profiles["publication_profile_version"] = (
            LAB_PUBLICATION_PROFILE.publication_profile_version - 1
        )
        earlier = parse_run_document(document, source="a run from an earlier build")

        # Both are genuinely wrong, which is what makes the ordering matter.
        assert earlier.deterministic_identity.profiles.execution_contract_version != (
            EXECUTION_CONTRACT_VERSION
        )
        assert earlier.deterministic_identity.profiles.publication_profile_version != (
            LAB_PUBLICATION_PROFILE.publication_profile_version
        )

        with pytest.raises(LabControlRefused) as refused:
            port(tmp_path).projection(earlier)

        assert refused.value.kind == "CONTRACT_INCOMPATIBLE"
        assert refused.value.kind != "FROZEN_RUN_NOT_RECONSTRUCTIBLE"

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

    def test_every_status_a_projection_can_hold_has_a_statement(self) -> None:
        """The same rule for the status vocabulary, which had no guard at all.

        A status is rendered beside its statement on the screen, and the
        statement is looked up by name. Adding a status without one would have
        been a `KeyError` at the moment somebody opened the run - which is
        precisely the class of defect R4 was.
        """
        assert LAB_EXECUTION_STATUSES
        for status in sorted(LAB_EXECUTION_STATUSES):
            assert len(LAB_EXECUTION_STATUS_STATEMENTS[status]) > 60
        assert (
            set(LAB_EXECUTION_STATUS_STATEMENTS) == LAB_EXECUTION_STATUSES
        ), "a statement for a status nothing can hold is a sentence nobody reads"


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

        instant = {
            boundary.offset_minutes: boundary.simulation_time
            for boundary in trajectory.boundaries
        }

        for offset in (1500, 1515, 1530, 1545, 1560, 1575):
            reading = reported_reading(published, fuel, offset)
            assert reading.quality == "STALE"
            assert reading.source_offset_minutes == BEFORE_THE_GAP
            assert reading.value == AFTER_DISPATCH + BIAS
            # The TIMESTAMP itself, which this test did not assert until an
            # independent review restamped it to the current attempt's own time
            # and watched the test pass. The offset and the value were both
            # still right under that mutation; only the timestamp was wrong,
            # which is exactly the value a reader of the screen reads.
            assert reading.source_sample_time == instant[BEFORE_THE_GAP]
            assert reading.source_sample_time != instant[offset]

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
    def test_the_draw_identity_is_the_one_v4_section_9_2_names(self) -> None:
        """Conformance to the SPECIFIED identity, not to the chosen one.

        The payload below is written from v4 section 9.2's own field list -

            digest("assetops-sim-rng-v1", seed, stream_name, step_index, ordinal)

        - in the order the specification gives, and the draw is required to
        agree. The first version of this test recomputed whatever payload the
        implementation had picked, which established determinism and said
        nothing about conformance; the production caller was meanwhile supplying
        an address and an offset in minutes, and this test could not see it.

        That is the defect shape this milestone has repeated in every slice: a
        check that proves what the code does rather than what the contract
        requires. Writing the expected payload from the spec is the difference.
        """
        from assetops_contracts.identity import IDENTITY_DOMAIN, canonical_payload

        assert RNG_DOMAIN == "assetops-sim-rng-v1"
        assert RNG_DOMAIN != IDENTITY_DOMAIN

        seed, stream, step_index, ordinal = 20260927, "dropout:a-device:a-signal", 7, 0
        payload = canonical_payload(
            [RNG_DOMAIN, seed, stream, step_index, ordinal]
        )
        expected = Fraction(
            int.from_bytes(
                hashlib.blake2b(payload, digest_size=32).digest(), "big"
            ),
            2**256,
        )

        assert draw_fraction(seed, stream, step_index, ordinal) == expected
        assert 0 <= expected < 1

    def test_the_draw_takes_the_named_fields_and_no_further_one(self) -> None:
        """The ARITY half, which is the whole of what a signature guarantees.

        This test was called "nowhere to put anything else" and the claim beside
        it said an address could not be supplied. C4: that was false, and the
        test below is the demonstration. A signature constrains how many
        arguments arrive and what they are called. It does not constrain their
        types, because Python does not enforce annotations, and a test whose
        name implies otherwise tells the next reader a guard exists where none
        does.

        What IS guaranteed is here: the four fields the contract names, no
        variadic through which a fifth could arrive, and a `TypeError` if one is
        passed anyway.
        """
        import inspect

        parameters = list(
            inspect.signature(draw_fraction).parameters.values()
        )

        assert [item.name for item in parameters] == [
            "seed",
            "stream",
            "step_index",
            "ordinal",
        ]
        assert not any(
            item.kind is inspect.Parameter.VAR_POSITIONAL
            or item.kind is inspect.Parameter.VAR_KEYWORD
            for item in parameters
        ), "a variadic parameter is somewhere to put a field the contract does not name"

        with pytest.raises(TypeError):
            draw_fraction(1, "a-stream", 0, 0, "fuel-tank-volume@fuel-tank")

    def test_an_address_in_a_whole_number_field_is_refused(self) -> None:
        """C4: the annotation is not the guard, so this is.

        An independent review passed the address as `step_index` and got a
        Fraction back. That is exactly the defect R1 was - a draw keyed on an
        address is deterministic, returns a plausible number, and is a different
        stream from the contract's with nothing on any surface to show it - so
        the substitution is refused rather than hashed.

        Narrow on purpose. This is not a licence to validate every internal
        function; it is here because a wrong digest is silent, and silent is
        what this milestone keeps paying for.
        """
        with pytest.raises(TypeError) as raised:
            draw_fraction(7, "a-stream", "fuel-tank-volume@fuel-tank", 1500)

        assert "step_index is a whole number" in str(raised.value)

        for wrong in (
            lambda: draw_fraction("7", "a-stream", 3),
            lambda: draw_fraction(7, 12, 3),
            lambda: draw_fraction(7, "a-stream", 3, "0"),
            # `True` is an `int` in Python and is not a boundary index, refused
            # for the reason the Lab's own step request refuses it.
            lambda: draw_fraction(7, "a-stream", True),
        ):
            with pytest.raises(TypeError):
                wrong()

    def test_the_refusal_does_not_reject_what_the_contract_names(self) -> None:
        """The other side, so the guard is not simply always raising.

        A check that refused everything would pass the test above and break
        every draw, and the production transform would be the thing that found
        out.
        """
        assert isinstance(draw_fraction(7, "a-stream", 3), Fraction)
        assert isinstance(draw_fraction(0, "", 0, 0), Fraction)

    def test_the_ordinal_separates_two_draws_at_one_step(self) -> None:
        """The field that exists for the second mechanism, proved to do something.

        The dropout draws once per stream per step and passes zero. A parameter
        that never varied would be a field nothing distinguishes, so the two
        ordinals are asserted to differ here rather than assumed to.
        """
        first = draw_fraction(7, "a-stream", 3, 0)
        second = draw_fraction(7, "a-stream", 3, 1)

        assert first != second
        assert draw_fraction(7, "a-stream", 3) == first

    def test_a_draw_is_reproducible_and_independent_of_call_order(self) -> None:
        first = draw_fraction(20260927, "one", 100)
        second = draw_fraction(20260927, "two", 100)

        assert first != second
        # Drawing the second does not move the first, in either order.
        assert draw_fraction(20260927, "one", 100) == first
        assert draw_fraction(20260927, "two", 100) == second
        # And the step index is a field of the identity rather than decoration.
        assert draw_fraction(20260927, "one", 101) != first

    def test_a_signal_declaring_no_dropout_still_draws(self) -> None:
        """A threshold of zero selects nothing by comparison, not by shortcut.

        It matters because it makes the threshold the only thing a reader has to
        change to see the mechanism work.
        """
        assert draw_selects(1, "s", 1000, 0) is True
        assert draw_selects(1, "s", 0, 0) is False
        with pytest.raises(ValueError):
            draw_selects(1, "s", 1001, 0)

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


# --- R2 and R3: the two defects an independent review reproduced -----------
#
# Both reached review because the tests that were supposed to cover them stopped
# one layer short of where the defect lived. R2's proved that the lower-level
# reporting object raises and never drove the HTTP composition the user meets;
# R3's covered the shipped WINDOW condition and never the other two shapes the
# parser accepts. So these two classes are written at the layer that was missing.


class TestACadenceThisRunCannotExpressIsARefusalAndNotACrash:
    """R2, at the real HTTP composition rather than at the object beneath it.

    A 30-minute timestep is an input anybody would try. It reaches READY, and
    before this fix POST execution/start returned HTTP 500: the cadence check ran
    outside the port's exception translation and the route catches only
    `LabControlRefused`, so the numeric explanation that had already been written
    never reached the user.

    The app is composed here the way `host/lab_app.py` composes it - the real
    `create_app` with a real `HostLabExecution` behind it - because that
    composition is exactly what the earlier test did not exercise.
    """

    def served(self, tmp_path: Path, run: SimulationRun, store: FakeRuns):
        return TestClient(
            create_app(
                FeatureFlags(simulator_lab_enabled=True),
                site_repository=FakeSites((_mg_001(),)),
                run_repository=store,
                execution=port(tmp_path),
            )
        )

    def test_a_thirty_minute_timestep_reaches_ready(self) -> None:
        """The precondition, asserted so the claim below is not about a refusal
        somewhere earlier. Run setup accepts this Draft."""
        run = draft(timestep_minutes=30)

        assert run.execution_status == "READY"
        assert run.deterministic_identity.interval.timestep_minutes == 30

    def test_start_answers_a_typed_refusal_carrying_both_numbers(
        self, tmp_path: Path
    ) -> None:
        run, store = _persisted(draft(timestep_minutes=30))
        client = self.served(tmp_path, run, store)

        response = client.post(
            f"/api/simulator-lab/runs/{run.run_id}/execution/start"
        )

        assert response.status_code == 409, response.text
        detail = response.json()["detail"]
        assert detail["refusal_kind"] == "CADENCE_NOT_EXPRESSIBLE"
        assert detail["code"] == "EXECUTION_CADENCE_NOT_EXPRESSIBLE"
        assert detail["advanced"] is False
        # The authored explanation, with the two numbers that make it actionable,
        # reaching the user rather than a stack trace.
        assert "every 15 minutes" in detail["message"]
        assert "steps of 30" in detail["message"]
        assert "fuel-level" in detail["message"]

    def test_the_read_refuses_the_same_way_rather_than_crashing(
        self, tmp_path: Path
    ) -> None:
        """The read is on the same path and had the same hole.

        `projection` builds the reporting inputs too, so a screen opening this
        Draft met the same 500 before a control was touched.
        """
        run, store = _persisted(draft(timestep_minutes=30))
        client = self.served(tmp_path, run, store)

        response = client.get(
            f"/api/simulator-lab/runs/{run.run_id}/execution"
        )

        assert response.status_code == 409, response.text
        assert (
            response.json()["detail"]["refusal_kind"]
            == "CADENCE_NOT_EXPRESSIBLE"
        )

    def test_a_timestep_the_cadence_divides_is_unaffected(
        self, tmp_path: Path
    ) -> None:
        """The other side, so the refusal is not simply always raised.

        Both declared cadences are whole multiples of a 15-minute timestep, so
        this Draft starts.
        """
        run, store = _persisted(draft())
        client = self.served(tmp_path, run, store)

        response = client.post(
            f"/api/simulator-lab/runs/{run.run_id}/execution/start"
        )

        assert response.status_code == 200, response.text
        assert response.json()["execution"]["status"] == "RUNNING"


class TestAReportingConditionOccupiesTimeByItsDeclaredShape:
    """R3: POINT, WINDOW and INTERVAL_WIDE are three declarations, not one.

    The frozen condition carries its shape and the adapter used to drop it, so
    every absent duration read as the interval's end: a POINT at offset 1500
    silenced 1500, 1515 and 2400 alike. Execution had discarded a frozen causal
    timing field, which is the thing freezing the projection exists to prevent.

    The shipped document declares a WINDOW, which is why the shipped case always
    passed. These cover the accepted input surface instead.
    """

    def suppressed(self, document: dict[str, Any]) -> set[int]:
        """Every offset at which the fuel sensor's sample was suppressed."""
        run = draft(definition=scenario(document))
        assert run.execution_status == "READY"
        _, _, reporting, trajectory = executed_to_end(run)
        published = readings(trajectory, reporting)
        assert published, "no sample was attempted at all"
        return {
            item.at_offset_minutes
            for item in published
            if item.key == (TANK, *FUEL_SIGNAL)
            and item.outcome == "SUPPRESSED_BY_GAP"
        }

    def test_the_shipped_window_covers_its_declared_length(self) -> None:
        """The case that always passed, kept as the comparison the others need."""
        assert self.suppressed(shipped_document()) == {
            1500,
            1515,
            1530,
            1545,
            1560,
            1575,
        }

    def test_a_point_condition_covers_one_step_and_not_the_rest_of_the_run(
        self,
    ) -> None:
        """The defect, as the difference between one instant and 65 of them.

        `point-applied-once` gives a point the one step whose half-open span
        contains its offset. The shipped condition's offset is 1490, so at a
        15-minute timestep that is `[1485, 1500)` - and because a cadence is a
        whole multiple of the timestep, that span holds exactly one due sample.

        Before the fix this set was every offset from 1490 to the end of the run.
        """
        assert self.suppressed(
            _reporting_condition_as(POINT_AT_THE_GAP_OFFSET)
        ) == {1485}

    def test_an_interval_wide_condition_covers_the_whole_interval(self) -> None:
        """The shape a POINT used to be indistinguishable from.

        This is what "the rest of the run" is supposed to look like, declared
        deliberately: `interval-wide-span` says such an entry starts at offset
        zero and holds until the run interval ends.

        164 and not 165, and the missing one is the point of the half-open span:
        the interval EXCLUDES its end instant, so the boundary at 2460 is outside
        the outage and its sample publishes. A count of 165 would mean an
        interval-wide entry had been stretched one boundary past the interval.
        """
        suppressed = self.suppressed(_reporting_condition_as(INTERVAL_WIDE))

        assert len(suppressed) == 164
        assert min(suppressed) == 0
        assert max(suppressed) == 2445
        assert 2460 not in suppressed

    def reason_at(self, document: dict[str, Any], offset: int) -> str:
        """Why the fuel sensor published nothing at one instant, in words."""
        run = draft(definition=scenario(document))
        _, _, reporting, trajectory = executed_to_end(run)
        (suppressed,) = [
            item
            for item in readings(trajectory, reporting)
            if item.key == (TANK, *FUEL_SIGNAL)
            and item.at_offset_minutes == offset
            and item.outcome == "SUPPRESSED_BY_GAP"
        ]
        return suppressed.suppression_reason or ""

    def test_the_explanation_names_the_span_it_is_explaining(self) -> None:
        """C5: the sentence used to give a span that excluded its own row.

        A POINT declared at offset 1490 suppresses the sample at 1485, which is
        right - `point-applied-once` gives it the step whose half-open span
        contains 1490, and that is `[1485, 1500)`. The explanation on that row
        said the path was unavailable "from offset 1490", a span that does not
        contain 1485. A reader could only reconcile the two by already knowing
        the containing-step rule, which is the thing the sentence exists to tell
        them.

        Both numbers are now on the row and they are labelled as what they are:
        the instant the document declared, and the interval it resolved to.
        """
        reason = self.reason_at(
            _reporting_condition_as(POINT_AT_THE_GAP_OFFSET), 1485
        )

        assert "across offset 1485 up to but not including 1500" in reason
        assert "declared at offset 1490" in reason

    def test_a_window_says_one_thing_because_it_has_one_answer(self) -> None:
        """The other side, so the extra clause is not simply always appended.

        A WINDOW's declared instant IS where its outage starts, so there is no
        second number to disclose and the sentence does not invent one. If every
        row carried both phrasings, "these two differ" would stop being
        information.
        """
        reason = self.reason_at(shipped_document(), 1545)

        assert "across offset 1490 up to but not including 1580" in reason
        assert reason.count("declared at offset 1490") == 1
        assert "which falls in the step covering" not in reason

    def test_the_three_shapes_do_not_agree_with_each_other(self) -> None:
        """The claim the first version made false, stated as a comparison.

        One instant, ninety minutes and the whole interval are three different
        experiments, and this says so in one place rather than leaving it to be
        inferred from three assertions elsewhere.

        It was claimed here that asserting the three sets separately "would not
        have caught it". That is too strong and a reviewer said so: asserting
        the POINT set equals `{1485}` alone rejects a run-long outage on its
        own. What a cross-case comparison adds is that the three are shown to
        differ from EACH OTHER, so a future change collapsing two of them again
        fails here even if each individual expectation were quietly relaxed to
        match. That is additional evidence, not the only possible protection.

        Compared by SIZE rather than by containment: the point at 1490 lands in
        the step before the window opens, so the two are disjoint rather than
        nested, and asserting containment would fail for a reason that has
        nothing to do with the defect.
        """
        point = self.suppressed(
            _reporting_condition_as(POINT_AT_THE_GAP_OFFSET)
        )
        window = self.suppressed(shipped_document())
        interval_wide = self.suppressed(_reporting_condition_as(INTERVAL_WIDE))

        assert len(point) == 1
        assert len(window) == 6
        assert len(interval_wide) == 164
        assert point != window != interval_wide

    def test_the_frozen_shape_reaches_the_window_rather_than_being_dropped(
        self,
    ) -> None:
        """The structural half: what the run froze is what the transform reads.

        Asserted on the record rather than only through its effect, because the
        effect is what a later shape with the same resolved span would hide.
        """
        run = draft(definition=scenario(_reporting_condition_as(POINT_AT_THE_GAP_OFFSET)))
        reporting = reporting_inputs(run)

        assert len(reporting.gaps) == 1
        window = reporting.gaps[0]
        assert window.timing_shape == "POINT"
        assert (
            run.deterministic_identity.reporting_path_conditions[0].timing_shape
            == "POINT"
        )
        assert window.offset_minutes == 1490
        assert window.start_offset_minutes == 1485
        assert window.end_offset_minutes == 1500

    def test_a_window_with_no_declared_length_is_refused(self) -> None:
        """Not read as either of the other two.

        A window is its length; an absent one used to be read as the rest of the
        run, which is how this whole collapse worked.
        """
        with pytest.raises(ValueError) as raised:
            ReportingPathWindow(
                event_id="a-gap",
                condition_address="fuel-level-reporting-availability@fuel-tank",
                device_id="fuel-level-sensor",
                signal_id="fuel-level",
                address=TANK,
                timing_shape="WINDOW",
                offset_minutes=1490,
                duration_minutes=None,
                interval_minutes=2460,
                timestep_minutes=15,
            )

        assert "not a window" in str(raised.value)

    def test_a_shape_outside_the_vocabulary_is_refused(self) -> None:
        with pytest.raises(ValueError) as raised:
            ReportingPathWindow(
                event_id="a-gap",
                condition_address="fuel-level-reporting-availability@fuel-tank",
                device_id="fuel-level-sensor",
                signal_id="fuel-level",
                address=TANK,
                timing_shape="FOREVER",
                offset_minutes=0,
                duration_minutes=None,
                interval_minutes=2460,
                timestep_minutes=15,
            )

        assert "an outage of a length nobody declared" in str(raised.value)

    def test_an_unrecorded_shape_with_no_recorded_span_is_refused(self) -> None:
        """The collapse again, under a new name, refused at construction.

        `SHAPE_NOT_RECORDED` says the writing build did not record which shape
        produced the outage. Without the span that build resolved, the row says
        neither how long the outage lasted nor what decides it, which is exactly
        the state the shape field was added to make impossible.
        """
        with pytest.raises(ValueError) as raised:
            ReportingPathWindow(
                event_id="a-gap",
                condition_address="fuel-level-reporting-availability@fuel-tank",
                device_id="fuel-level-sensor",
                signal_id="fuel-level",
                address=TANK,
                timing_shape=SHAPE_NOT_RECORDED,
                offset_minutes=1490,
                duration_minutes=90,
                interval_minutes=2460,
                timestep_minutes=15,
            )

        assert "records no shape and no span either" in str(raised.value)

    def test_a_declared_shape_carrying_a_recorded_span_is_refused(self) -> None:
        """Two answers to one question, which is one too many.

        A row states the shape its span follows from, or it states the span a
        record already resolved. Allowing both would leave the next reader
        guessing which is authoritative - and would let a fresh execution ship a
        span that disagrees with its own declared shape.
        """
        with pytest.raises(ValueError) as raised:
            ReportingPathWindow(
                event_id="a-gap",
                condition_address="fuel-level-reporting-availability@fuel-tank",
                device_id="fuel-level-sensor",
                signal_id="fuel-level",
                address=TANK,
                timing_shape="WINDOW",
                offset_minutes=1490,
                duration_minutes=90,
                interval_minutes=2460,
                timestep_minutes=15,
                recorded_end_offset_minutes=1580,
            )

        assert "two answers to one question" in str(raised.value)

    def test_every_window_a_fresh_execution_builds_declares_its_shape(
        self,
    ) -> None:
        """The other side of the read path, so it stays a READ path.

        `SHAPE_NOT_RECORDED` exists for records written before the shape was
        carried. A window this build resolves for a live run must never have it,
        or the absence would have become a shape a new execution can produce.
        """
        run = draft()
        reporting = reporting_inputs(run)

        assert reporting.gaps, "the shipped document declares a gap at all"
        for window in reporting.gaps:
            assert window.timing_shape != SHAPE_NOT_RECORDED
            assert window.recorded_end_offset_minutes is None


# --- R4: a record written before the rule changed --------------------------


class TestAnExecutionRecordOlderThanTheShapeRuleIsStillInspectable:
    """R4: carrying the shape changed the artifact, and broke every old one.

    `parse_projection` began reading `timing_shape` and `timestep_minutes` off
    every reporting-gap row. Records written by the build reviewed one round
    earlier carry neither, so reading one raised `KeyError 'timing_shape'`, which
    escaped the composed GET execution route as **HTTP 500**. Four completed runs
    already on disk were affected: the correction that made new results right made
    every old result unopenable, which is the fourth time this milestone that a
    change correct going forward was silent going backward.

    The fixture here is not a hand-authored corrupt file. It executes a real run,
    takes the artifact this build writes, and removes exactly what the first-pass
    build never wrote - so what is read back has the shape of a real record rather
    than a guess at one.
    """

    def strip_to_first_pass(self, path: Path) -> dict[str, Any]:
        """One persisted artifact, back in the layout that predates the shape.

        What the FIRST build on this branch wrote: no schema marker, and gap
        rows with an offset, a duration and the interval and nothing about which
        shape produced them.
        """
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        document.pop("artifact_schema_version")
        for row in document["reporting_gaps"]:
            del row["timing_shape"]
            del row["timestep_minutes"]
            del row["recorded_end_offset_minutes"]
        path.write_text(yaml.safe_dump(document), encoding="utf-8")
        return document

    def strip_to_intermediate(self, path: Path) -> dict[str, Any]:
        """One persisted artifact, back in the layout the SECOND build wrote.

        That build added `timing_shape` and the per-gap timestep and did not add
        a schema marker, because the marker did not exist yet. So a record of
        this layout carries the shape and says nothing about its own schema -
        which is precisely what the first version of the reader could not see,
        and why it assigned these records to the shapeless layout and threw the
        recorded shape away.
        """
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        document.pop("artifact_schema_version")
        for row in document["reporting_gaps"]:
            del row["recorded_end_offset_minutes"]
        path.write_text(yaml.safe_dump(document), encoding="utf-8")
        return document

    def point_run(self) -> SimulationRun:
        """A Draft whose reporting gap is a POINT at offset 1490.

        The fixture the three-layout claims need. A POINT's declared instant and
        the span it covers DIFFER - 1490 falls in the step covering
        `[1485, 1500)` - so a reader that quietly applied the shapeless layout's
        duration rule to it produces `[1490, 2460)`, a different answer rather
        than the same one by another route. Against the shipped WINDOW both
        rules agree, which is why the WINDOW records already on disk hid this.
        """
        run = draft(definition=scenario(_reporting_condition_as(POINT_AT_THE_GAP_OFFSET)))
        assert run.execution_status == "READY"
        return run

    def completed(
        self, tmp_path: Path, run: SimulationRun
    ) -> tuple[HostLabExecution, LabProjection, Path]:
        execution = port(tmp_path)
        execution.start(run)
        written = execution.run_to_end(run)
        execution.forget(run.run_id)
        return execution, written, tmp_path / f"{run.run_id}.yaml"

    def test_the_fixture_really_is_the_first_pass_shape(
        self, tmp_path: Path
    ) -> None:
        """The precondition, so the claims below are about the right file.

        A fixture that still carried the new field would pass whether or not the
        read path this class is about existed at all.
        """
        run = draft()
        _, _, path = self.completed(tmp_path, run)

        document = self.strip_to_first_pass(path)

        assert "artifact_schema_version" not in document
        assert document["reporting_gaps"], "the fixture needs a gap row at all"
        for row in document["reporting_gaps"]:
            assert "timing_shape" not in row
            assert "timestep_minutes" not in row

    def test_an_old_record_reads_back_as_the_result_it_is(
        self, tmp_path: Path
    ) -> None:
        """Criterion 12, for the records that already exist.

        Everything the old build computed is still there and still exact. The
        readings are the readings it generated and the digests are the ones it
        wrote; nothing is re-executed.
        """
        run = draft()
        execution, written, path = self.completed(tmp_path, run)
        self.strip_to_first_pass(path)

        reloaded = execution.projection(run)

        assert reloaded.status == "COMPLETED"
        assert reloaded.observations == written.observations
        assert reloaded.private_state == written.private_state
        assert reloaded.content_digest == written.content_digest
        assert (
            reloaded.observation_series_digest
            == written.observation_series_digest
        )

    def test_the_span_is_the_one_that_record_was_resolved_against(
        self, tmp_path: Path
    ) -> None:
        """Recovered, not guessed - and the row says which.

        The first-pass build resolved every window by one rule over two fields
        the record still carries, so the span its readings were generated against
        is recoverable exactly. Which authored SHAPE produced that span is not,
        and the row says so rather than giving the likelier answer.
        """
        run = draft()
        execution, _, path = self.completed(tmp_path, run)
        self.strip_to_first_pass(path)

        reloaded = execution.projection(run)

        (window,) = reloaded.reporting_gaps
        assert window.timing_shape == SHAPE_NOT_RECORDED
        assert window.recorded_end_offset_minutes == 1580
        assert window.start_offset_minutes == 1490
        assert window.end_offset_minutes == 1580
        assert window.covers(1545)
        assert not window.covers(1580)

    def test_the_reader_is_told_the_record_predates_the_rule(
        self, tmp_path: Path
    ) -> None:
        """On the projection, not in a log.

        The person looking at the screen is the one who needs to know that one
        column on it is absent and why. A record read under an older rule that
        said so nowhere would be the silent reinterpretation this is about.
        """
        run = draft()
        execution, _, path = self.completed(tmp_path, run)
        self.strip_to_first_pass(path)

        reloaded = execution.projection(run)

        note = " ".join(reloaded.notes)
        assert "before a reporting condition's declared shape was persisted" in note
        assert "is not recoverable from THIS record and is not guessed" in note

    # --- The layout in between, which the first version of this could not see -

    def test_a_record_that_recorded_its_shape_keeps_it(
        self, tmp_path: Path
    ) -> None:
        """The third layout, and the one the schema marker cannot identify.

        The build that added `timing_shape` did not add the marker, because the
        marker was invented to fix the breakage that build caused. So it left
        records with the shape ON them and no number to say so, and the first
        reader to use the number assigned every unmarked record to the shapeless
        layout - discarding a field sitting in the same file.

        A POINT is what makes that visible. Its declared instant is 1490 and the
        span it covers is `[1485, 1500)`; the shapeless layout's rule over the
        same fields gives `[1490, 2460)`. Against a WINDOW both agree, which is
        why the two real records of this layout did not expose it.
        """
        run = self.point_run()
        execution, written, path = self.completed(tmp_path, run)
        self.strip_to_intermediate(path)

        reloaded = execution.projection(run)

        (window,) = reloaded.reporting_gaps
        assert window.timing_shape == "POINT"
        assert window.recorded_end_offset_minutes is None
        assert window.start_offset_minutes == 1485
        assert window.end_offset_minutes == 1500
        # And it is the SAME window the run produced, not a near miss. A fresh
        # execution records no span, so nothing has to be allowed for here: the
        # record read back is equal to the record written.
        assert window == written.reporting_gaps[0]

    def test_the_shapeless_rule_is_not_applied_to_a_record_with_a_shape(
        self, tmp_path: Path
    ) -> None:
        """The defect, stated as the answer it used to give.

        `[1490, 2460)` is what the shapeless layout's rule produces from this
        record's fields - an instant read as the rest of the run. That is the
        collapse R3 fixed, arriving a second time through the reader instead of
        through the adapter.
        """
        run = self.point_run()
        execution, _, path = self.completed(tmp_path, run)
        self.strip_to_intermediate(path)

        (window,) = execution.projection(run).reporting_gaps

        assert (window.start_offset_minutes, window.end_offset_minutes) != (
            1490,
            2460,
        ), "the shapeless layout's duration rule was applied to a shaped record"
        assert window.timing_shape != SHAPE_NOT_RECORDED, (
            "a shape sitting in the record was reported as absent"
        )

    def test_the_note_describes_the_record_that_was_actually_read(
        self, tmp_path: Path
    ) -> None:
        """A note that misdescribes the record is worse than no note.

        It said "the shape is not recoverable from the record" on every unmarked
        record, including the ones carrying the shape - a sentence false about
        the file printed beside it, asserting that the silent reinterpretation
        had not happened while it was happening.
        """
        run = self.point_run()
        execution, _, path = self.completed(tmp_path, run)
        self.strip_to_intermediate(path)

        note = " ".join(execution.projection(run).notes)

        assert "The shape shown on each reporting gap below is the one that" in note
        assert "not recoverable" not in note

    def test_the_three_layouts_do_not_agree_with_each_other(
        self, tmp_path: Path
    ) -> None:
        """One record, three ways of having been written, three readings.

        Stated as a comparison because that is the claim: the current layout and
        the one that recorded its shape both give `[1485, 1500)` with a POINT,
        and the shapeless one gives the span it actually resolved with no shape.
        Asserting each separately leaves "these two are read the same way" as
        something a reader has to take on trust, and the defect was exactly that
        two of them WERE read the same way when they should not have been.
        """
        answers = {}
        for name, strip in (
            ("current", lambda path: None),
            ("intermediate", self.strip_to_intermediate),
            ("first-pass", self.strip_to_first_pass),
        ):
            root = tmp_path / name
            root.mkdir()
            run = self.point_run()
            execution = port(root)
            execution.start(run)
            execution.run_to_end(run)
            execution.forget(run.run_id)
            strip(root / f"{run.run_id}.yaml")
            (window,) = execution.projection(run).reporting_gaps
            answers[name] = (
                window.timing_shape,
                window.start_offset_minutes,
                window.end_offset_minutes,
            )

        assert answers["current"] == ("POINT", 1485, 1500)
        assert answers["intermediate"] == ("POINT", 1485, 1500)
        assert answers["first-pass"] == (SHAPE_NOT_RECORDED, 1490, 2460)
        assert answers["intermediate"] != answers["first-pass"], (
            "the two unmarked layouts are different records and are read "
            "differently; reading them the same way is the defect"
        )

    def test_rows_that_disagree_about_their_own_build_are_not_interpreted(
        self, tmp_path: Path
    ) -> None:
        """Neither build wrote this, so no rule here fits it.

        Both unmarked layouts wrote the shape on every gap row or on none.
        Reading half a record under one rule and half under another would be a
        result nobody produced, so it is reported instead.
        """
        run = draft()
        execution, _, path = self.completed(tmp_path, run)
        document = self.strip_to_intermediate(path)
        document["reporting_gaps"].append(
            {**document["reporting_gaps"][0], "event_id": "a-second-gap"}
        )
        del document["reporting_gaps"][1]["timing_shape"]
        path.write_text(yaml.safe_dump(document), encoding="utf-8")

        reloaded = execution.projection(run)

        assert reloaded.status == "ARTIFACT_UNREADABLE"
        note = " ".join(reloaded.notes)
        assert "1 of 2 reporting-gap rows record a timing shape" in note

    def test_a_schema_marker_that_is_not_a_number_is_reported(
        self, tmp_path: Path
    ) -> None:
        """The header is inside the guard too, which it was not.

        The marker was converted by `int()` before the protected parse, so a
        record whose marker is a word raised `ValueError` and escaped as an HTTP
        500 - one field earlier than the failure the guard was written for, and
        the same failure. A reviewer found it by writing one.
        """
        run = draft()
        execution, _, path = self.completed(tmp_path, run)
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        document["artifact_schema_version"] = "not-a-number"
        path.write_text(yaml.safe_dump(document), encoding="utf-8")

        reloaded = execution.projection(run)

        assert reloaded.status == "ARTIFACT_UNREADABLE"
        assert "is not a whole number" in " ".join(reloaded.notes)

    def test_the_composed_route_answers_rather_than_returning_five_hundred(
        self, tmp_path: Path
    ) -> None:
        """The surface the defect actually appeared on.

        Reproduced through the real `create_app` with a real `HostLabExecution`,
        because a `KeyError` inside the port is only a defect once it escapes the
        route as a 500 on the screen that exists to inspect the run.
        """
        run, store = _persisted(draft())
        execution = port(tmp_path)
        client = TestClient(
            create_app(
                FeatureFlags(simulator_lab_enabled=True),
                site_repository=FakeSites((_mg_001(),)),
                run_repository=store,
                execution=execution,
            )
        )
        client.post(f"/api/simulator-lab/runs/{run.run_id}/execution/start")
        client.post(
            f"/api/simulator-lab/runs/{run.run_id}/execution/run-to-end",
            json={"from_boundary": 0},
        )
        execution.forget(run.run_id)
        self.strip_to_first_pass(tmp_path / f"{run.run_id}.yaml")

        response = client.get(f"/api/simulator-lab/runs/{run.run_id}/execution")

        assert response.status_code == 200, response.text
        payload = response.json()["execution"]
        assert payload["status"] == "COMPLETED"
        assert payload["observations"], "the readings are still on the wire"
        (gap,) = payload["reporting_gaps"]
        assert gap["timing_shape"] == SHAPE_NOT_RECORDED
        assert gap["start_offset_minutes"] == 1490
        assert gap["end_offset_minutes"] == 1580

    def test_a_record_from_a_later_build_is_reported_and_not_reinterpreted(
        self, tmp_path: Path
    ) -> None:
        """The other direction, where nothing is recoverable.

        A build cannot honestly read a rule it does not have, so this is the
        typed unavailable answer rather than a best effort. It is still an
        ANSWER: the status says what is wrong and the note says which schema.
        """
        run = draft()
        execution, _, path = self.completed(tmp_path, run)
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        document["artifact_schema_version"] = (
            EXECUTION_ARTIFACT_SCHEMA_VERSION + 1
        )
        path.write_text(yaml.safe_dump(document), encoding="utf-8")

        reloaded = execution.projection(run)

        assert reloaded.status == "ARTIFACT_UNREADABLE"
        assert reloaded.private_state == ()
        assert reloaded.observations == ()
        assert reloaded.content_digest is None
        assert f"schema {EXECUTION_ARTIFACT_SCHEMA_VERSION + 1}" in " ".join(
            reloaded.notes
        )

    def test_no_control_executes_over_a_record_it_cannot_read(
        self, tmp_path: Path
    ) -> None:
        """The reason this is a refusal and not a shrug.

        Treating an unreadable record as no record would start a second execution
        under the first one's identity and overwrite the very result nobody could
        read.
        """
        run = draft()
        execution, _, path = self.completed(tmp_path, run)
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        document["artifact_schema_version"] = 99
        path.write_text(yaml.safe_dump(document), encoding="utf-8")
        before = path.read_bytes()

        for control in (
            lambda: execution.start(run),
            lambda: execution.step(run, boundaries=1, from_boundary=0),
            lambda: execution.run_to_end(run),
        ):
            with pytest.raises(LabControlRefused) as refused:
                control()
            assert refused.value.kind == "ARTIFACT_UNREADABLE"
            assert "schema 99" in str(refused.value.detail)

        assert path.read_bytes() == before, "the record is left exactly as it was"

    def test_a_record_that_states_a_schema_it_does_not_carry_is_named(
        self, tmp_path: Path
    ) -> None:
        """Damaged is not old, and the two get different answers.

        A record saying schema two and then missing a field schema two requires
        is hand-edited or truncated, not written by an earlier build. It is
        reported with the FIELD named, which is what a reader needs and what a
        `KeyError` escaping as an HTTP 500 gave them instead. The reviewer's own
        reproduction produces exactly this hybrid, because it removed the field
        without removing the schema marker.
        """
        run = draft()
        execution, _, path = self.completed(tmp_path, run)
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        for row in document["reporting_gaps"]:
            del row["timing_shape"]
        path.write_text(yaml.safe_dump(document), encoding="utf-8")

        reloaded = execution.projection(run)

        assert reloaded.status == "ARTIFACT_UNREADABLE"
        note = " ".join(reloaded.notes)
        assert "timing_shape" in note
        assert "damaged or hand-edited" in note

    def test_this_build_writes_the_schema_it_reads(self, tmp_path: Path) -> None:
        """The field that makes the next change survivable.

        A reader that learns which rule applied by noticing a key is absent
        cannot tell an old record from a damaged one, and cannot say which. This
        is what stops the fifth variant of this defect.
        """
        run = draft()
        _, _, path = self.completed(tmp_path, run)

        document = yaml.safe_load(path.read_text(encoding="utf-8"))

        assert (
            document["artifact_schema_version"]
            == EXECUTION_ARTIFACT_SCHEMA_VERSION
        )
        assert next(iter(document)) == "artifact_schema_version", (
            "a person opening the file reads which rule wrote it before they "
            "read anything that rule decided"
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
