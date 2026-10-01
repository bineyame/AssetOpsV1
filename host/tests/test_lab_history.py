"""T025c phase 1: persisted Lab history and its strict readback.

A healthy mini-grid run and a fuel run with a declared reporting gap are
executed through the Lab's own start/run-to-end path, the host is replaced (a
restart: a new `HostLabExecution` over the same artifact directory, no live
session), and the history is read back and compared with what the live session
recorded. Reads are made with the kernel made unreachable, and the artifact's
bytes are compared before and after.
"""

from __future__ import annotations

import json
from dataclasses import replace
from fractions import Fraction
from pathlib import Path

import pytest

import lab_execution
from assetops_backend.runs.adapters.yaml_run_documents import read_run_record
from assetops_contracts.lab_history import HISTORY_FAMILIES
from assetops_simulator.kernel.execute import Execution
from assetops_simulator.observation.transform import generate_observations
from lab_execution import (
    HostLabExecution,
    LabSession,
    YamlExecutionArtifacts,
    project,
)
from lab_history import HISTORY_MARKER, capture, parse_history, render_history
from source_stages import JsonSourceStages

from test_mini_grid_v2 import PROLONGED, STOP, draft, with_overrides

GATE_RUNS = Path(__file__).resolve().parent / "contract9_gate" / "runs"
#: A shipped-shape fuel run whose publication profile declares a reporting gap.
FUEL_WITH_GAP = GATE_RUNS / "run-c9000000000000000000000000000102.yaml"
#: A daytime run that fails at its first instant (topology inconsistent).
FAILS_AT_START = GATE_RUNS / "run-c9000000000000000000000000000210.yaml"


def a_lab(root: Path) -> HostLabExecution:
    return HostLabExecution(
        artifacts=YamlExecutionArtifacts(root),
        stages=JsonSourceStages(root / "stages"),
    )


def finish(run, root: Path):
    """Execute a run to its end, return (projection, live history)."""
    lab = a_lab(root)
    projection = lab.start(run)
    if not projection.is_terminal:
        projection = lab.run_to_end(run)
    return projection, lab.history(run)


def records(history):
    return (
        history.boundaries,
        history.samples,
        history.intervals,
        history.exposures,
        history.attempts,
        history.applied_events,
        history.bounded_transitions,
        history.discrete_transitions,
        history.bus_attachments,
        history.electrical_steps,
    )


@pytest.fixture(scope="module")
def mini_grid(tmp_path_factory):
    root = tmp_path_factory.mktemp("mini-grid")
    run = draft(PROLONGED)
    projection, live = finish(run, root)
    return run, root, projection, live


class TestACompletedRunReloadsWithoutExecuting:
    def test_the_reloaded_history_is_what_the_live_session_recorded(
        self, mini_grid
    ) -> None:
        run, root, projection, live = mini_grid
        assert live.source == "LIVE_SESSION"
        reloaded = a_lab(root).history(run)
        assert reloaded.source == "PERSISTED", reloaded.notes
        assert records(reloaded) == records(live)
        assert reloaded.content_digest == projection.content_digest
        assert reloaded.history_digest is not None
        assert reloaded.history_digest != projection.content_digest
        assert [c.availability for c in reloaded.coverage] == ["RECORDED"] * 5

    def test_reading_invokes_no_kernel_and_changes_no_byte(
        self, mini_grid, monkeypatch
    ) -> None:
        run, root, _, live = mini_grid
        path = root / f"{run.run_id}.yaml"
        before = path.read_bytes()

        def refuse(*_args, **_kwargs):
            raise AssertionError("a read executed the kernel")

        monkeypatch.setattr(lab_execution, "start", refuse)
        monkeypatch.setattr(Execution, "advance", refuse)
        monkeypatch.setattr(Execution, "run_to_end", refuse)
        lab = a_lab(root)
        assert lab.projection(run).status == "COMPLETED"
        assert records(lab.history(run)) == records(live)
        assert path.read_bytes() == before

    def test_the_whole_attempt_series_is_recorded_not_the_tail(
        self, mini_grid
    ) -> None:
        run, root, projection, _ = mini_grid
        history = a_lab(root).history(run)
        assert len(history.attempts) > lab_execution.RECENT_REPORT_LIMIT
        outcomes = [a.outcome for a in history.attempts]
        assert outcomes.count("REPORTED") == projection.reported_count
        assert outcomes.count("DROPPED") == projection.dropped_count
        assert tuple(history.attempts[-12:]) == projection.recent_reports

    def test_each_load_stays_addressed(self, mini_grid) -> None:
        run, root, projection, _ = mini_grid
        history = a_lab(root).history(run)
        addresses = {
            load.address
            for interval in history.intervals
            for load in interval.step.accepted.loads
        }
        assert addresses == {
            "load-demand@load-clinic",
            "load-demand@load-mill",
            "load-demand@load-res",
        }
        assert all(len(i.step.accepted.loads) == 3 for i in history.intervals)
        # The history agrees with the summary at the last recorded interval.
        assert history.intervals[-1].step.accepted.loads == (
            projection.electrical.latest_loads
        )

    def test_the_last_boundary_agrees_with_the_projection(self, mini_grid) -> None:
        run, root, projection, _ = mini_grid
        history = a_lab(root).history(run)
        last = history.recorded_through_offset
        assert last == projection.offset_minutes
        stocks = {
            (s.address, s.value, s.unit)
            for s in history.samples
            if s.offset_minutes == last and s.phase == "POST_EVENT" and s.unit != "state"
        }
        assert stocks == {
            (row.address, row.value, row.canonical_unit)
            for row in projection.private_state
        }

    def test_first_interval_timing_is_absence_not_zero(self, mini_grid) -> None:
        run, root, _, _ = mini_grid
        history = a_lab(root).history(run)
        first, second = history.boundaries[:2]
        assert not first.has_preceding_interval and second.has_preceding_interval
        at_zero = {s.phase for s in history.samples if s.offset_minutes == 0}
        assert "PRECEDING_INTERVAL" not in at_zero
        assert "POST_EVENT" in at_zero
        # Each interval sample at T describes [T - dt, T); each resolved
        # interval decided at T governs [T, T + dt).
        step = history.boundaries[1].offset_minutes
        assert all(
            i.to_offset - i.from_offset == step for i in history.intervals
        )
        assert history.intervals[0].from_offset == 0
        # The first interval measurements have no reading, and say why.
        first_attempts = [a for a in history.attempts if a.at_offset_minutes == 0]
        assert any(a.outcome == "NO_PRECEDING_INTERVAL" for a in first_attempts)
        assert all(
            a.reported_value is None
            for a in first_attempts
            if a.outcome != "REPORTED"
        )

    def test_a_valid_zero_and_a_missing_reading_stay_different(
        self, mini_grid
    ) -> None:
        run, root, _, _ = mini_grid
        history = a_lab(root).history(run)
        zeros = [
            a for a in history.attempts
            if a.outcome == "REPORTED" and a.reported_value == 0
        ]
        missing = [a for a in history.attempts if a.outcome != "REPORTED"]
        assert zeros and missing
        assert all(a.reported_value is None for a in missing)
        assert all(a.suppression_reason is not None for a in missing)

    def test_state_at_t_and_state_for_step_are_both_recorded(
        self, mini_grid
    ) -> None:
        run, root, _, _ = mini_grid
        history = a_lab(root).history(run)
        generator = [s for s in history.samples if s.address.startswith("generator-state@")]
        phases = {s.phase for s in generator}
        assert phases == {"POST_EVENT", "FOR_STEP"}
        assert all(isinstance(s.value, str) for s in generator)
        assert history.discrete_transitions

    def test_exact_values_round_trip_losslessly(self, mini_grid) -> None:
        run, root, _, live = mini_grid
        reloaded = a_lab(root).history(run)
        inexact = [
            s.value for s in reloaded.samples
            if isinstance(s.value, Fraction) and s.value.denominator not in (1,)
        ]
        assert inexact, "the fixture should carry non-integer exact values"
        assert reloaded.samples == live.samples
        assert all(
            type(a) is type(b) for a, b in zip(reloaded.samples, live.samples)
        )

    def test_the_drawing_references_are_the_frozen_attachments(
        self, mini_grid
    ) -> None:
        run, root, _, _ = mini_grid
        history = a_lab(root).history(run)
        roles = {a.role for a in history.bus_attachments}
        assert history.bus_attachments and "LOAD" in {r.upper() for r in roles}


class TestTheRecordedTotalsAreTheProjectionsOwnRows:
    """T025e addendum B (option R): `electrical_steps` is joined, never re-summed."""

    def test_live_and_persisted_carry_the_projection_step_rows(
        self, mini_grid
    ) -> None:
        run, root, projection, live = mini_grid
        assert projection.electrical is not None and projection.electrical.steps
        assert live.electrical_steps == projection.electrical.steps
        reloaded = a_lab(root).history(run)
        assert reloaded.source == "PERSISTED"
        assert reloaded.electrical_steps == a_lab(root).projection(run).electrical.steps
        assert [r.from_offset for r in reloaded.electrical_steps] == [
            i.from_offset for i in reloaded.intervals
        ]


class TestTheArtifactLayout:
    def test_the_projection_document_is_unchanged_and_never_parses_history(
        self, mini_grid
    ) -> None:
        run, root, projection, _ = mini_grid
        text = (root / f"{run.run_id}.yaml").read_text(encoding="utf-8")
        head, marker, tail = text.partition(HISTORY_MARKER)
        assert marker and tail.endswith("\n")
        assert head == lab_execution.yaml.safe_dump(
            lab_execution.render_projection(projection),
            sort_keys=False,
            allow_unicode=True,
        )

    def test_a_running_artifact_carries_no_history(self, tmp_path) -> None:
        run = draft(PROLONGED)
        lab = a_lab(tmp_path)
        lab.start(run)
        lab.step(run, boundaries=3, from_boundary=0)
        text = (tmp_path / f"{run.run_id}.yaml").read_text(encoding="utf-8")
        assert HISTORY_MARKER not in text
        live = lab.history(run)
        assert live.source == "LIVE_SESSION"
        assert len(live.boundaries) == 3
        assert len(live.intervals) == 3

    def test_a_lost_live_session_is_interrupted_with_no_history(
        self, tmp_path
    ) -> None:
        run = draft(PROLONGED)
        lab = a_lab(tmp_path)
        lab.start(run)
        lab.step(run, boundaries=5, from_boundary=0)
        history = a_lab(tmp_path).history(run)
        assert history.status == "INTERRUPTED"
        assert history.source == "NOT_RECORDED"
        assert records(history) == ((),) * 10
        assert {c.availability for c in history.coverage} == {"UNAVAILABLE"}

    def test_a_draft_never_executed_has_no_history(self, tmp_path) -> None:
        history = a_lab(tmp_path).history(draft(PROLONGED))
        assert history.status == "NOT_STARTED"
        assert history.source == "NOT_RECORDED"
        assert history.boundaries == ()


class TestOldAndDamagedArtifacts:
    def copy(self, mini_grid, tmp_path: Path) -> tuple[object, Path, str]:
        run, root, _, _ = mini_grid
        source = (root / f"{run.run_id}.yaml").read_text(encoding="utf-8")
        path = tmp_path / f"{run.run_id}.yaml"
        path.write_text(source, encoding="utf-8")
        return run, path, source

    def test_an_artifact_written_before_history_discloses_every_family(
        self, mini_grid, tmp_path
    ) -> None:
        run, path, source = self.copy(mini_grid, tmp_path)
        path.write_text(source.partition(HISTORY_MARKER)[0], encoding="utf-8")
        lab = a_lab(tmp_path)
        projection = lab.projection(run)
        history = lab.history(run)
        assert projection.status == "COMPLETED"
        # Its existing series are still on the execution record ...
        assert projection.electrical is not None and projection.electrical.steps
        # ... and every history family says it was never written.
        assert history.source == "LEGACY_ARTIFACT"
        assert [c.family for c in history.coverage] == list(HISTORY_FAMILIES)
        assert {c.availability for c in history.coverage} == {"UNAVAILABLE"}
        assert history.samples == () and history.attempts == ()
        # Addendum B: the step rows join only where intervals are recorded.
        assert history.electrical_steps == ()

    @pytest.mark.parametrize(
        "damage",
        ["value", "schema", "digest", "order", "truncated", "manifest"],
    )
    def test_a_damaged_or_unknown_history_is_unreadable_and_untouched(
        self, mini_grid, tmp_path, damage
    ) -> None:
        run, path, source = self.copy(mini_grid, tmp_path)
        head, marker, tail = source.partition(HISTORY_MARKER)
        document = json.loads(tail)
        if damage == "value":
            document["samples"][3][4] = "1/3"
        elif damage == "schema":
            document["history_schema_version"] = 3
        elif damage == "digest":
            document["manifest"]["history_digest"] = "0" * 64
        elif damage == "order":
            document["attempts"].reverse()
        elif damage == "manifest":
            document["manifest"]["seed"] += 1
        if damage in ("order", "manifest"):
            # Re-sign, so the check that fires is the record check itself.
            from lab_history import history_digest

            document["manifest"]["history_digest"] = history_digest(document)
        text = json.dumps(document) + "\n"
        if damage == "truncated":
            text = tail[: len(tail) // 2]
        path.write_text(head + marker + text, encoding="utf-8")
        before = path.read_bytes()

        lab = a_lab(tmp_path)
        history = lab.history(run)
        assert history.source == "HISTORY_UNREADABLE", damage
        assert history.notes and history.samples == ()
        # The execution record beside it still reads, and nothing was rewritten.
        assert lab.projection(run).status == "COMPLETED"
        assert path.read_bytes() == before


class TestFailuresStayInspectable:
    def test_a_failed_history_write_never_claims_a_complete_history(
        self, tmp_path, monkeypatch
    ) -> None:
        run = draft(PROLONGED)

        def broken(*_args, **_kwargs):
            raise RuntimeError("disk said no")

        monkeypatch.setattr(lab_execution, "render_history", broken)
        finished, live = finish(run, tmp_path)
        monkeypatch.undo()
        # The same host, still holding the session, answers what the artifact
        # says rather than a complete-looking in-memory history (backlog C3).
        assert live.source == "WRITE_FAILED"
        assert "disk said no" in live.notes[0]
        assert live.samples == () and live.intervals == ()
        lab = a_lab(tmp_path)
        assert lab.projection(run).status == "COMPLETED"
        history = lab.history(run)
        assert finished.status == "COMPLETED"
        assert history.source == "WRITE_FAILED"
        assert "disk said no" in history.notes[0]
        assert {c.availability for c in history.coverage} == {"UNAVAILABLE"}

    def test_a_run_failing_at_its_first_instant_records_its_failure(
        self, tmp_path
    ) -> None:
        run = read_run_record(FAILS_AT_START)
        projection, _ = finish(run, tmp_path)
        assert projection.status == "FAILED"
        history = a_lab(tmp_path).history(run)
        assert history.source == "PERSISTED", history.notes
        assert history.failure == projection.failure
        assert history.boundaries == ()

    def test_a_failed_prefix_persists_with_its_failure_location(
        self, tmp_path
    ) -> None:
        from assetops_simulator.kernel.execute import start
        from assetops_simulator.packs.mini_grid import MINI_GRID_V2_MODEL
        from execution_adapter import frozen_world_inputs

        run = draft(document_edit=with_overrides((120, 120, 60)))
        inputs = frozen_world_inputs(run)
        moved = tuple(
            replace(item, offset_minutes=122) if item.address == STOP else item
            for item in inputs.forcings
        )
        lab = a_lab(tmp_path)
        reporting = lab._reporting_for(run)
        execution = start(replace(inputs, forcings=moved), MINI_GRID_V2_MODEL)
        execution.run_to_end()
        assert execution.outcome == "FAILED"
        session = LabSession(
            run_id=run.run_id, execution=execution, reporting=reporting, notes=()
        )
        projection = project(session)
        observations = generate_observations(execution.boundaries, reporting)
        live = capture(
            execution, reporting, observations,
            run_id=run.run_id, status="FAILED",
            content_digest=projection.content_digest,
            observation_series_digest=projection.observation_series_digest,
            electrical=projection.electrical,
        )
        YamlExecutionArtifacts(tmp_path).write(
            projection, render_history(live, projection)
        )
        history = a_lab(tmp_path).history(run)
        assert history.source == "PERSISTED", history.notes
        assert history.failure.at_offset_minutes == 120
        # The failing instant was never recorded: the prefix ends one step
        # before it, and nothing is filled in after it.
        assert history.recorded_through_offset == 115
        assert len(history.boundaries) < history.boundaries_total
        assert records(history) == records(live)


class TestAFuelRunWithAReportingGap:
    def test_the_gap_is_recorded_as_suppressed_attempts(self, tmp_path) -> None:
        run = read_run_record(FUEL_WITH_GAP)
        projection, _ = finish(run, tmp_path)
        history = a_lab(tmp_path).history(run)
        assert history.source == "PERSISTED", history.notes
        suppressed = [a for a in history.attempts if a.outcome == "SUPPRESSED_BY_GAP"]
        assert len(suppressed) == projection.suppressed_by_gap_count > 0
        assert all(a.reported_value is None for a in suppressed)
        # A fuel model has no controller and froze no bus attachment: both
        # families say so rather than appearing empty.
        assert history.availability("intervals") == "NOT_APPLICABLE"
        assert history.availability("drawing") == "NOT_APPLICABLE"
        assert history.applied_events
        assert history.electrical_steps == ()


def test_parse_refuses_a_history_that_names_another_run(mini_grid) -> None:
    run, root, projection, _ = mini_grid
    tail = (root / f"{run.run_id}.yaml").read_text(encoding="utf-8").partition(
        HISTORY_MARKER
    )[2]
    other = replace(projection, run_id="run-00000000000000000000000000000009")
    from lab_history import HistoryUnreadable

    with pytest.raises(HistoryUnreadable, match="run_id"):
        parse_history(json.loads(tail), other)


@pytest.fixture(scope="module")
def recorded(tmp_path_factory):
    """The fuel run executed and reloaded: (persisted history, reporting)."""
    root = tmp_path_factory.mktemp("fuel-window")
    run = read_run_record(FUEL_WITH_GAP)
    finish(run, root)
    lab = a_lab(root)
    history = lab.history(run)
    assert history.source == "PERSISTED", history.notes
    return history, lab._reporting_for(run)


class TestAnIndependentlyDerivedShortWindow:
    """T025c proof: a short window of the recorded fuel history, derived by hand.

    Every expected value below comes from the run's declared inputs and the
    contract's rules, not from the kernel: 430 L at the start; the dispatched
    generator window burns 45 kW x 4 h x 0.311 L/kWh = 55.98 L; the 120 L
    removal is a WINDOW of 45 minutes applied in nine equal five-minute shares;
    the reporting gap [1490, 1580) suppresses every fuel-level sample due in
    it at the sensor's 15-minute cadence; the 300 L delivery at 2400 is a POINT
    event against the 500 L capacity, so the bound refuses what does not fit.
    The window [1485, 1590] holds the boundary events and the whole gap; 2400
    holds the bounded boundary event.
    """

    def test_the_stock_follows_the_declared_causes(self, recorded) -> None:
        history, _ = recorded
        fuel = {
            s.offset_minutes: s.value
            for s in history.samples
            if s.address == "fuel-tank-volume@fuel-tank" and s.phase == "POST_EVENT"
        }
        before = Fraction(430) - Fraction(45) * 4 * Fraction("0.311")
        assert before == Fraction("374.02")
        share = Fraction(120) / 9
        for offset in range(1485, 1591, 5):
            steps_applied = min(max((offset - 1500) // 5, 0), 9)
            assert fuel[offset] == before - steps_applied * share, offset
        assert fuel[1545] == Fraction("254.02")
        # The removal is recorded where the ledger applied it: nine entries,
        # one per step of the window, each at the boundary that begins its step.
        removal = [
            e for e in history.applied_events if e.event_id == "unaccounted-fuel-removal"
        ]
        assert [e.at_offset_minutes for e in removal] == list(range(1500, 1545, 5))
        assert all(e.share == Fraction(1, 9) for e in removal)

    def test_the_gap_suppresses_exactly_the_due_samples_inside_it(
        self, recorded
    ) -> None:
        history, reporting = recorded
        signal = next(
            s for s in reporting.signals if s.address == "fuel-tank-volume@fuel-tank"
        )
        assert signal.cadence_minutes == 15
        level = [
            a
            for a in history.attempts
            if a.address == "fuel-tank-volume@fuel-tank"
            and 1485 <= a.at_offset_minutes <= 1590
        ]
        # Due every 15 minutes and nowhere else: the instants between are
        # cadence, recorded as no attempt at all.
        assert [a.at_offset_minutes for a in level] == list(range(1485, 1591, 15))
        inside = [a for a in level if 1490 <= a.at_offset_minutes < 1580]
        assert [a.outcome for a in inside] == ["SUPPRESSED_BY_GAP"] * 6
        assert all(a.reported_value is None for a in inside)
        edges = [a for a in level if a not in inside]
        assert [a.outcome for a in edges] == ["REPORTED", "REPORTED"]
        truth = {
            s.offset_minutes: s.value
            for s in history.samples
            if s.address == "fuel-tank-volume@fuel-tank" and s.phase == "POST_EVENT"
        }
        # A reading is the state at its own source time plus the profile's
        # declared bias - never a value restamped from another instant.
        for attempt in edges:
            assert attempt.reported_value == truth[attempt.at_offset_minutes] + signal.bias

    def test_the_bounded_delivery_refuses_what_does_not_fit(self, recorded) -> None:
        history, _ = recorded
        (bounded,) = history.bounded_transitions
        level = Fraction("254.02")
        assert bounded.at_offset_minutes == 2400
        assert bounded.requested == level + 300
        assert bounded.accepted == Fraction(500)
        assert bounded.refused == level + 300 - 500
        fuel = {
            s.offset_minutes: s.value
            for s in history.samples
            if s.address == "fuel-tank-volume@fuel-tank" and s.phase == "POST_EVENT"
        }
        # State at T is after T's events: the delivery shows at 2400 itself.
        assert (fuel[2395], fuel[2400]) == (level, Fraction(500))


class TestProjectionBackedDataIsBoundToTheHistory:
    """R1: the cockpit reads signals, gaps and electrical steps from the
    projection. Editing the projection alone, with the appended history left
    untouched, must be an explicit integrity failure, not a verified cockpit."""

    @staticmethod
    def edit_projection(path: Path, change) -> bytes:
        import yaml

        source = path.read_text(encoding="utf-8")
        head, marker, tail = source.partition(HISTORY_MARKER)
        document = yaml.safe_load(head)
        change(document)
        path.write_text(
            yaml.safe_dump(document, sort_keys=False) + marker + tail,
            encoding="utf-8",
        )
        return path.read_bytes()

    def prepared(self, run, root, tmp_path):
        path = tmp_path / f"{run.run_id}.yaml"
        path.write_text(
            (root / f"{run.run_id}.yaml").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        return path

    def assert_refused(self, lab, run, path, before) -> None:
        history = lab.history(run)
        assert history.source == "HISTORY_UNREADABLE"
        assert history.history_digest is None and history.samples == ()
        assert any("execution record beside the history" in n for n in history.notes)
        assert path.read_bytes() == before

    def test_an_unedited_copy_still_verifies(self, mini_grid, tmp_path) -> None:
        run, root, _, live = mini_grid
        self.prepared(run, root, tmp_path)
        history = a_lab(tmp_path).history(run)
        assert history.source == "PERSISTED"
        assert history.history_digest == a_lab(root).history(run).history_digest

    def test_a_changed_signal_cadence_is_refused(self, mini_grid, tmp_path) -> None:
        run, root, _, _ = mini_grid
        path = self.prepared(run, root, tmp_path)
        before = self.edit_projection(
            path, lambda d: d["signals"][0].update(cadence_minutes=120)
        )
        self.assert_refused(a_lab(tmp_path), run, path, before)

    def test_a_changed_chart_value_is_refused(self, mini_grid, tmp_path) -> None:
        run, root, _, _ = mini_grid
        path = self.prepared(run, root, tmp_path)
        before = self.edit_projection(
            path, lambda d: d["electrical"]["steps"][0].update(pv_output="1234")
        )
        self.assert_refused(a_lab(tmp_path), run, path, before)

    def test_a_changed_battery_value_is_refused(self, mini_grid, tmp_path) -> None:
        run, root, _, _ = mini_grid
        path = self.prepared(run, root, tmp_path)
        before = self.edit_projection(
            path, lambda d: d["electrical"]["steps"][5].update(battery_power="999")
        )
        self.assert_refused(a_lab(tmp_path), run, path, before)

    def test_a_changed_reporting_gap_is_refused(self, tmp_path) -> None:
        run = read_run_record(FUEL_WITH_GAP)
        finish(run, tmp_path)
        path = tmp_path / f"{run.run_id}.yaml"
        before = self.edit_projection(
            path, lambda d: d["reporting_gaps"][0].update(offset_minutes=1)
        )
        self.assert_refused(a_lab(tmp_path), run, path, before)
