"""T025b phase 2: generator status and power through the observation path.

Criteria 6 and 7. The typed enum status survives the transform, the persisted
artifact and the gated Lab projection; a sample at T sees a transition already
due at T and never a request emitted at T; generator power is the mean over the
completed step; an enum refuses numeric error; publication profile 4 sits
beside 3; missing, stale and silenced status changes the report and nothing
physical; envelope schema 1 and the fuel-only mapping stay, and an enum mapping
under schema 1 is refused.
"""

from __future__ import annotations

import copy
from dataclasses import replace
from fractions import Fraction

import pytest
import yaml
from lab_history import HISTORY_MARKER

from assetops_backend.runs.profiles import (
    LAB_PUBLICATION_PROFILE,
    LAB_PUBLICATION_PROFILE_V4,
    PUBLICATION_PROFILES,
    DeviceSignalDeclaration,
    find_publication_profile,
)
from assetops_backend.simulator_lab_api import execution_payload
from assetops_contracts.control import DISCRETE_UNIT
from assetops_contracts.lab_projection import (
    GENERATOR_REPORTED_STATUS_PENDING,
    GENERATOR_STATUS_REPORTED_NOT_STAGED,
)
from assetops_contracts.observation import DeviceObservation, DeviceSignalSpec
from assetops_contracts.source_envelope import (
    SOURCE_ENVELOPE_SCHEMA_VERSION,
    EnvelopeRejected,
    SourceMappingEntry,
    SourceMappingSet,
)
from assetops_simulator.gateway.mappings import SIMULATOR_LAB_GATEWAY_MAPPINGS
from assetops_simulator.gateway.publish import publish
from assetops_simulator.observation.transform import generate_observations

from execution_adapter import (
    model_for,
    publication_profile_for,
    reporting_inputs,
    run_to_end,
)
from kobo import kobo_document, kobo_draft

START = "2026-09-22T03:00:00Z"
END = "2026-09-22T11:00:00Z"
PROLONGED = "kobo-mini-grid-prolonged"
CHANGED = "kobo-mini-grid-stop-60"
GEN = "generator-state@generator"
POWER = "generator-output-power@generator"
STATUS = ("generator-controller", "status")


def draft(name=CHANGED, *, publication=4, version=2, document=None):
    return kobo_draft(
        name,
        document=document,
        timestep_minutes=5,
        model_profile="mini-grid",
        model_profile_version=version,
        start_time=START,
        end_time=END,
        publication_profile_version=publication,
    )


def executed(run):
    return run_to_end(run, model_for(run)).trajectory


def with_signal(reporting, key, **changes):
    return replace(
        reporting,
        signals=tuple(
            replace(signal, **changes)
            if (signal.device_id, signal.signal_id) == key
            else signal
            for signal in reporting.signals
        ),
    )


def series(observations, key):
    return [
        item for item in observations if (item.device_id, item.signal_id) == key
    ]


def lab(tmp_path):
    from lab_execution import HostLabExecution, YamlExecutionArtifacts
    from source_stages import JsonSourceStages

    return HostLabExecution(
        artifacts=YamlExecutionArtifacts(tmp_path),
        stages=JsonSourceStages(tmp_path / "stages"),
    )


@pytest.fixture(scope="module")
def changed():
    run = draft()
    return run, executed(run)


# --- Criterion 6: profile 4 beside profile 3 ---------------------------------


class TestPublicationProfileFour:
    def test_four_is_registered_beside_three_which_is_unchanged(self) -> None:
        assert find_publication_profile(
            PUBLICATION_PROFILES, "simulator-lab-publication", 3
        ) is LAB_PUBLICATION_PROFILE
        assert find_publication_profile(
            PUBLICATION_PROFILES, "simulator-lab-publication", 4
        ) is LAB_PUBLICATION_PROFILE_V4
        assert LAB_PUBLICATION_PROFILE.device_signal(*STATUS) is None
        assert (
            LAB_PUBLICATION_PROFILE.device_signal(
                "generator-controller", "ac-power"
            ).cadence_minutes
            == 60
        )

    def test_four_declares_a_typed_status_and_a_fifteen_minute_power(self) -> None:
        status = LAB_PUBLICATION_PROFILE_V4.device_signal(*STATUS)
        assert (status.state_key, status.reading_class, status.canonical_unit) == (
            "generator-state",
            "STATE_SIGNAL",
            DISCRETE_UNIT,
        )
        assert status.bias == 0
        power = LAB_PUBLICATION_PROFILE_V4.device_signal(
            "generator-controller", "ac-power"
        )
        assert (power.reading_class, power.cadence_minutes) == (
            "INTERVAL_SIGNAL",
            15,
        )

    def test_a_run_generates_through_the_profile_it_froze(self) -> None:
        three, four = draft(publication=3), draft(publication=4)
        assert publication_profile_for(three) is LAB_PUBLICATION_PROFILE
        assert publication_profile_for(four) is LAB_PUBLICATION_PROFILE_V4
        assert STATUS not in {
            (s.device_id, s.signal_id) for s in reporting_inputs(three).signals
        }
        assert STATUS in {
            (s.device_id, s.signal_id) for s in reporting_inputs(four).signals
        }


# --- Criterion 6: numeric error refused on an enum ---------------------------


class TestAnEnumRefusesNumericError:
    def declaration(self, **changes):
        fields = dict(
            device_id="generator-controller",
            signal_id="status",
            state_key="generator-state",
            reading_class="STATE_SIGNAL",
            canonical_unit=DISCRETE_UNIT,
            cadence_minutes=15,
            bias=0.0,
            dropout_per_thousand=0,
            statement="x",
        )
        fields.update(changes)
        return fields

    def test_a_bias_on_an_enum_declaration_is_refused(self) -> None:
        with pytest.raises(ValueError, match="bias, noise and quantization"):
            DeviceSignalDeclaration(**self.declaration(bias=0.5))

    def test_an_enum_is_never_an_interval_mean(self) -> None:
        with pytest.raises(ValueError, match="observed at an instant"):
            DeviceSignalDeclaration(
                **self.declaration(reading_class="INTERVAL_SIGNAL")
            )

    def test_the_contract_spec_refuses_the_same(self) -> None:
        fields = self.declaration(bias=Fraction(1, 2), address=GEN)
        with pytest.raises(ValueError, match="bias, noise and quantization"):
            DeviceSignalSpec(**fields)

    def test_an_enum_reading_is_not_a_number_nor_a_number_an_enum(self) -> None:
        common = dict(
            device_id="generator-controller",
            signal_id="status",
            address=GEN,
            state_key="generator-state",
            reading_class="STATE_SIGNAL",
            at_offset_minutes=0,
            source_sample_time=START,
            outcome="REPORTED",
        )
        with pytest.raises(ValueError, match="discrete value is text"):
            DeviceObservation(
                **common, reported_value=Fraction(2), canonical_unit=DISCRETE_UNIT
            )
        with pytest.raises(ValueError, match="discrete value is text"):
            DeviceObservation(**common, reported_value="RUNNING", canonical_unit="kW")


# --- Criterion 6: timing ------------------------------------------------------


class TestStatusTiming:
    def test_a_sample_at_t_sees_due_transitions_and_not_new_requests(
        self, changed
    ) -> None:
        run, trajectory = changed
        # Every boundary is sampled, so every transition instant is one.
        reporting = with_signal(
            reporting_inputs(run), STATUS, cadence_minutes=5, dropout_per_thousand=0
        )
        reported = {
            item.at_offset_minutes: item.reported_value
            for item in series(
                generate_observations(trajectory.boundaries, reporting), STATUS
            )
        }
        transitions = trajectory.discrete_transitions
        due = [t for t in transitions if t.phase == "apply-events"]
        emitted = [t for t in transitions if t.phase == "physical-acceptance"]
        assert due and emitted, "both phases occur, so neither claim is vacuous"
        for item in due:
            assert reported[item.at_offset_minutes] == item.next
        for item in emitted:
            assert reported[item.at_offset_minutes] == item.previous
            # ...and the next boundary's sample is the first to see it.
            assert reported[item.at_offset_minutes + 5] != item.previous

    def test_status_readings_are_typed_members(self, changed) -> None:
        run, trajectory = changed
        values = {
            item.reported_value
            for item in series(
                generate_observations(trajectory.boundaries, reporting_inputs(run)),
                STATUS,
            )
            if item.outcome == "REPORTED"
        }
        assert values == {"STOPPED", "RUNNING"}
        assert all(isinstance(value, str) for value in values)

    def test_power_is_the_mean_over_the_completed_step(self, changed) -> None:
        run, trajectory = changed
        reporting = with_signal(
            reporting_inputs(run), ("generator-controller", "ac-power"), cadence_minutes=5
        )
        power = {
            item.at_offset_minutes: item.reported_value
            for item in series(
                generate_observations(trajectory.boundaries, reporting),
                ("generator-controller", "ac-power"),
            )
            if item.outcome == "REPORTED"
        }
        boundaries = trajectory.boundaries
        checked = 0
        for before, at in zip(boundaries, boundaries[1:]):
            flows = {f.flow_id: f for f in before.control_step.accepted.flows}
            assert power[at.offset_minutes] == flows["generator_output"].mean_power
            checked += flows["generator_output"].mean_power > 0
        assert checked > 0, "the generator ran, so the claim covers real output"
        assert 0 not in power, "no interval has completed at the first boundary"


# --- Criterion 7: missing / stale / silenced status leaves physics alone -----


def silenced(document):
    raw = copy.deepcopy(document)
    raw["timeline"].append(
        {
            "event_id": "generator-status-gap",
            "sequence": 99,
            "offset_minutes": 240,
            "entry_kind": "EVENT",
            "category": "DATA_QUALITY",
            "description": "The generator controller reports no status for an hour, across the stop.",
            "execution_role": "FORCING_INPUT",
            "state_key": "generator-status-reporting-availability@generator",
            "execution_requirement": "REQUIRED",
            "timing": {"shape": "WINDOW", "duration_minutes": 60},
        }
    )
    return raw


class TestMissingStatusChangesOnlyTheReport:
    def test_profile_three_and_four_execute_the_same_world(self, changed) -> None:
        _, four = changed
        three = executed(draft(publication=3))
        assert three.boundaries == four.boundaries
        assert three.discrete_transitions == four.discrete_transitions

    def test_a_silenced_status_window_changes_reports_not_the_world(
        self, changed
    ) -> None:
        run, trajectory = changed
        gapped_run = draft(document=silenced(kobo_document(CHANGED)))
        assert gapped_run.blocking_reasons == ()
        gapped = executed(gapped_run)
        assert gapped.boundaries == trajectory.boundaries
        assert gapped.discrete_transitions == trajectory.discrete_transitions

        plain = series(
            generate_observations(trajectory.boundaries, reporting_inputs(run)), STATUS
        )
        hidden = series(
            generate_observations(gapped.boundaries, reporting_inputs(gapped_run)),
            STATUS,
        )
        suppressed = [i.at_offset_minutes for i in hidden if i.outcome == "SUPPRESSED_BY_GAP"]
        assert suppressed == [240, 255, 270, 285]
        assert [i.outcome for i in plain if i.at_offset_minutes in suppressed] != [
            "SUPPRESSED_BY_GAP"
        ] * 4
        # Other paths are untouched by a gap on this one.
        others = lambda items: [i for i in items if (i.device_id, i.signal_id) != STATUS]  # noqa: E731
        assert others(
            generate_observations(trajectory.boundaries, reporting_inputs(run))
        ) == others(
            generate_observations(gapped.boundaries, reporting_inputs(gapped_run))
        )

    def test_a_silenced_status_is_stale_beside_the_physical_state(
        self, tmp_path
    ) -> None:
        run = draft(document=silenced(kobo_document(CHANGED)))
        port = lab(tmp_path)
        port.start(run)
        finished = port.run_to_end(run)
        rows = {row.from_offset: row for row in finished.electrical.generator.steps}
        # The generator stops inside the gap: physics moves, the report holds
        # the last RUNNING it published, marked STALE.
        inside = [rows[offset] for offset in range(245, 300, 5)]
        assert {row.reported_quality for row in inside} == {"STALE"}
        assert {row.reported_state for row in inside} == {"RUNNING"}
        assert any(row.state_at_t == "STOPPED" for row in inside)

    def test_dropout_everywhere_leaves_the_world_and_other_paths(self, changed) -> None:
        run, trajectory = changed
        lost = with_signal(reporting_inputs(run), STATUS, dropout_per_thousand=1000)
        observations = generate_observations(trajectory.boundaries, lost)
        assert {i.outcome for i in series(observations, STATUS)} == {"DROPPED"}
        kept = generate_observations(trajectory.boundaries, reporting_inputs(run))
        assert [i for i in observations if (i.device_id, i.signal_id) != STATUS] == [
            i for i in kept if (i.device_id, i.signal_id) != STATUS
        ]


# --- Criteria 6 and 7: the gated Lab, the artifact and the wire --------------


class TestTheGatedLab:
    def test_status_and_power_reach_the_reported_side_and_read_back(
        self, tmp_path
    ) -> None:
        run = draft()
        port = lab(tmp_path)
        port.start(run)
        finished = port.run_to_end(run)
        rows = {(v.device_id, v.signal_id): v for v in finished.observations}
        status = rows[STATUS]
        assert (status.canonical_unit, status.true_value) == (DISCRETE_UNIT, "STOPPED")
        assert isinstance(status.reported_value, str)
        assert ("generator-controller", "ac-power") in rows
        generator = finished.electrical.generator
        assert generator.reported_status == GENERATOR_STATUS_REPORTED_NOT_STAGED
        assert {row.reported_quality for row in generator.steps} >= {"GOOD", "STALE"}
        assert all(
            row.reported_state == row.state_at_t
            for row in generator.steps
            if row.reported_quality == "GOOD"
        )

        document = yaml.safe_load((tmp_path / f"{run.run_id}.yaml").read_text("utf-8").partition(HISTORY_MARKER)[0])
        assert document["artifact_schema_version"] == 5
        port.forget(run.run_id)
        reloaded = lab(tmp_path).projection(run)
        assert reloaded.observations == finished.observations
        assert reloaded.recent_reports == finished.recent_reports
        assert reloaded.electrical == finished.electrical

        payload = execution_payload(finished)
        wire = next(
            row
            for row in payload["observations"]
            if (row["device_id"], row["signal_id"]) == STATUS
        )
        assert (wire["true_value"], wire["canonical_unit"]) == ("STOPPED", "state")
        step = payload["electrical"]["generator"]["steps"][0]
        assert step["reported_state"] == "STOPPED"
        assert step["reported_quality"] == "GOOD"

    def test_a_profile_three_run_keeps_schema_four_and_the_pending_text(
        self, tmp_path
    ) -> None:
        run = draft(publication=3)
        port = lab(tmp_path)
        port.start(run)
        finished = port.run_to_end(run)
        assert finished.electrical.generator.reported_status == (
            GENERATOR_REPORTED_STATUS_PENDING
        )
        assert all(row.reported_quality is None for row in finished.electrical.generator.steps)
        document = yaml.safe_load((tmp_path / f"{run.run_id}.yaml").read_text("utf-8").partition(HISTORY_MARKER)[0])
        assert document["artifact_schema_version"] == 4
        assert "reported_state" not in document["electrical"]["generator"]["steps"][0]

    def test_a_marker_that_disagrees_with_its_readings_is_refused(
        self, tmp_path
    ) -> None:
        run = draft()
        port = lab(tmp_path)
        port.start(run)
        port.run_to_end(run)
        port.forget(run.run_id)
        path = tmp_path / f"{run.run_id}.yaml"
        document = yaml.safe_load(path.read_text("utf-8").partition(HISTORY_MARKER)[0])
        document["artifact_schema_version"] = 4
        path.write_text(yaml.safe_dump(document, sort_keys=False), "utf-8")
        reloaded = lab(tmp_path).projection(run)
        assert reloaded.status == "ARTIFACT_UNREADABLE"
        assert "discrete" in " ".join(reloaded.notes)


# --- Criterion 7: envelope schema 1 and the fuel-only mapping stay -----------


class TestStatusIsNotStaged:
    def test_schema_one_and_the_fuel_only_mapping_are_unchanged(self) -> None:
        # T026: the build writes schema 2 for new mappings; the fuel-only
        # mapping a profile-3/4 Draft stages under still publishes schema 1.
        assert SOURCE_ENVELOPE_SCHEMA_VERSION == 2
        assert SIMULATOR_LAB_GATEWAY_MAPPINGS.envelope_schema_version == 1
        assert SIMULATOR_LAB_GATEWAY_MAPPINGS.mapping_version == 1
        assert [e.key for e in SIMULATOR_LAB_GATEWAY_MAPPINGS.entries] == [
            ("fuel-level-sensor", "fuel-level")
        ]

    def test_a_mapping_promising_an_enum_under_schema_one_is_refused(self) -> None:
        with pytest.raises(EnvelopeRejected) as refused:
            SourceMappingEntry(
                device_id="generator-controller",
                signal_id="status",
                measurement="STATE_AT_INSTANT",
                unit=DISCRETE_UNIT,
                publishes_unavailable=True,
            )
        assert refused.value.kind == "MAPPING_INCOMPATIBLE"
        assert "schema 1 carries numbers only" in str(refused.value)

    def test_an_allowlisted_status_is_refused_not_omitted_or_disguised(
        self, changed
    ) -> None:
        run, trajectory = changed
        reporting = reporting_inputs(run)
        observations = generate_observations(trajectory.boundaries, reporting)
        # A mapping claiming the status as a number is the disguise; the
        # gateway refuses it from the reading's own unit.
        disguised = replace(
            SIMULATOR_LAB_GATEWAY_MAPPINGS,
            entries=SIMULATOR_LAB_GATEWAY_MAPPINGS.entries
            + (
                SourceMappingEntry(
                    device_id="generator-controller",
                    signal_id="status",
                    measurement="STATE_AT_INSTANT",
                    unit="L",
                    publishes_unavailable=True,
                ),
            ),
        )
        with pytest.raises(EnvelopeRejected) as refused:
            publish(
                observations,
                disguised,
                reporting.interval,
                site_id="KOBO-001",
                source_id="simulator-lab-source",
                gateway_id="simulator-lab-gateway",
            )
        assert refused.value.kind == "MAPPING_INCOMPATIBLE"

    def test_the_shipped_mapping_stages_fuel_only_from_a_profile_four_run(
        self, tmp_path
    ) -> None:
        run = draft()
        port = lab(tmp_path)
        port.start(run)
        port.run_to_end(run)
        view = port.staged_envelopes(run)
        assert view.status == "STAGED", view.statement
        # Nothing but the allowlisted fuel path is staged; the status the run
        # publishes in the Lab is not, and the stage is not refused over it.
        assert {(e.device_id, e.signal_id) for e in view.stage.envelopes} <= {
            ("fuel-level-sensor", "fuel-level")
        }
        assert view.stage.mapping == SIMULATOR_LAB_GATEWAY_MAPPINGS
