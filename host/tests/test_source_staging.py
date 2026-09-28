"""Staging a Draft's canonical source envelopes, composed end to end.

Every Draft here is frozen in process by the real run setup service against a
Site instantiated from the shipped template, executed by the real kernel,
observed by the real transform, published by the real gateway, and staged by the
real store into a temporary directory - never `var/stages`.

The task's proof table, row by row, is the class list below. Where a row is about
the schema alone its negative corpus is `simulator/tests/test_source_envelope_
schema.py`; here each row is proved against a real stage.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import replace
from fractions import Fraction
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from fixtures import FakeRuns, FakeSites, HYBRID_TEMPLATE, draft, site_from_template

from assetops_backend.config import FeatureFlags
from assetops_backend.main import create_app
from assetops_backend.runs.models import SimulationRun
from assetops_contracts.lab_projection import LabProjection
from assetops_contracts.source_envelope import (
    EnvelopeRejected,
    SourceEnvelope,
    canonical_envelope_json,
    parse_canonical_envelope_json,
)
from assetops_contracts.source_stage import (
    SourceStage,
    StageConflict,
    StageUnreadable,
    parse_stage_text,
)
from assetops_simulator.gateway.mappings import SIMULATOR_LAB_GATEWAY_MAPPINGS
from assetops_simulator.gateway.publish import publish
from assetops_simulator.observation.transform import generate_observations

from execution_adapter import reporting_inputs
from lab_execution import HostLabExecution, YamlExecutionArtifacts
from source_stages import JsonSourceStages

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
FUEL = ("fuel-level-sensor", "fuel-level")
STAGE_ROUTE = "/api/simulator-lab/runs/{run_id}/stage"


def port(tmp_path: Path, **changes) -> HostLabExecution:
    return HostLabExecution(
        artifacts=YamlExecutionArtifacts(tmp_path / "executions"),
        stages=JsonSourceStages(tmp_path / "stages"),
        **changes,
    )


def stage_file(tmp_path: Path, run: SimulationRun) -> Path:
    return tmp_path / "stages" / f"{run.run_id}.json"


def completed(tmp_path: Path, run: SimulationRun | None = None, **changes):
    record = draft() if run is None else run
    execution = port(tmp_path, **changes)
    execution.start(record)
    projection = execution.run_to_end(record)
    assert projection.status == "COMPLETED"
    return record, execution, projection


def to_the_gap(tmp_path: Path):
    """Offset 1545: inside the reporting gap [1490, 1580), past the removal."""
    record = draft()
    execution = port(tmp_path)
    execution.start(record)
    projection = execution.step(record, boundaries=104, from_boundary=0)
    assert projection.offset_minutes == 1545
    return record, execution


def fuel_series(record: SimulationRun, projection: LabProjection):
    """The fuel sensor's whole attempt series, recomputed independently."""
    from assetops_simulator.kernel.execute import execute

    from execution_adapter import frozen_world_inputs

    trajectory = execute(frozen_world_inputs(record))
    reporting = reporting_inputs(record)
    return tuple(
        item
        for item in generate_observations(trajectory.boundaries, reporting)
        if (item.device_id, item.signal_id) == FUEL
    )


def _site_store_digest() -> str:
    root = REPOSITORY_ROOT / "var" / "sites"
    digest = hashlib.blake2b(digest_size=32)
    if root.exists():
        for path in sorted(root.rglob("*")):
            if path.is_file():
                digest.update(str(path.relative_to(root)).encode("utf-8"))
                digest.update(path.read_bytes())
    return digest.hexdigest()


# --- Generated fuel sample -> canonical mapped envelope, original source time --


class TestAGeneratedFuelSampleIsStaged:
    def test_the_last_reading_before_the_gap_is_staged_with_its_own_times(
        self, tmp_path: Path
    ) -> None:
        record, execution = to_the_gap(tmp_path)

        view = execution.staged_envelopes(record)

        assert view.status == "STAGED"
        newest = view.stage.envelopes[-1]
        # The fuel sensor's last publication before the gap, not the instant
        # the run has reached: 00:45 is offset 1485, the run is at 1545.
        assert newest.source_time == "2026-09-22T00:45:00Z"
        assert newest.published_at == "2026-09-22T00:45:03Z"
        assert newest.value == Fraction("373.52")
        assert (newest.device_id, newest.signal_id) == FUEL
        assert newest.site_id == "MG-001"
        assert newest.source_id == "simulator-lab-source"
        assert newest.gateway_id == "simulator-lab-gateway"
        assert newest.mapping_set_id == "simulator-lab-gateway-fuel"
        assert newest.mapping_version == 1
        assert newest.measurement == "STATE_AT_INSTANT"

    def test_every_published_fuel_reading_is_staged_and_nothing_else(
        self, tmp_path: Path
    ) -> None:
        record, execution, projection = completed(tmp_path)
        series = fuel_series(record, projection)
        reported = [item for item in series if item.outcome == "REPORTED"]

        staged = execution.staged_envelopes(record).stage.envelopes

        # Non-vacuous: the shipped run publishes well over a hundred readings.
        assert len(reported) > 100
        assert [item.source_time for item in staged] == [
            item.source_sample_time for item in reported
        ]
        assert [item.value for item in staged] == [
            item.reported_value for item in reported
        ]
        # The generator's hourly power signal is generated and not allowlisted.
        assert {(item.device_id, item.signal_id) for item in staged} == {FUEL}


# --- Missing sample -> no fabricated value ------------------------------------


class TestAGapInSamplingInventsNothing:
    def test_no_envelope_exists_for_any_instant_the_gap_suppressed(
        self, tmp_path: Path
    ) -> None:
        record, execution, projection = completed(tmp_path)
        series = fuel_series(record, projection)
        suppressed = {
            item.source_sample_time
            for item in series
            if item.outcome in ("SUPPRESSED_BY_GAP", "DROPPED")
        }
        staged = execution.staged_envelopes(record).stage.envelopes

        assert suppressed, "the shipped run suppresses and drops samples"
        assert not suppressed & {item.source_time for item in staged}
        assert all(item.value is not None for item in staged)
        assert all(item.quality == "GOOD" for item in staged)

    def test_the_gap_is_visible_as_an_absence_of_publications(
        self, tmp_path: Path
    ) -> None:
        record, execution, _ = completed(tmp_path)
        times = [
            item.source_time
            for item in execution.staged_envelopes(record).stage.envelopes
        ]
        inside = [t for t in times if "2026-09-22T00:50:00Z" <= t < "2026-09-22T02:20:00Z"]

        assert inside == []
        assert "2026-09-22T00:45:00Z" in times


# --- Reload stage without runtime -> same exact canonical payload -------------


class TestTheStageReloadsWithoutTheRuntime:
    def test_a_new_process_reads_the_same_bytes(self, tmp_path: Path) -> None:
        record, execution, _ = completed(tmp_path)
        before = [
            canonical_envelope_json(item)
            for item in execution.staged_envelopes(record).stage.envelopes
        ]

        # A different port instance: no session, no handle, nothing in memory.
        reloaded = port(tmp_path).staged_envelopes(record)

        assert reloaded.status == "STAGED"
        assert [
            canonical_envelope_json(item) for item in reloaded.stage.envelopes
        ] == before

    def test_the_persisted_text_is_the_canonical_text_the_inspector_shows(
        self, tmp_path: Path
    ) -> None:
        record, execution, _ = completed(tmp_path)
        persisted = json.loads(stage_file(tmp_path, record).read_text())

        shown = [
            canonical_envelope_json(item)
            for item in port(tmp_path).staged_envelopes(record).stage.envelopes
        ]

        assert persisted["envelopes"] == shown
        for text in persisted["envelopes"]:
            assert canonical_envelope_json(parse_canonical_envelope_json(text)) == text

    def test_a_forgotten_handle_leaves_a_readable_stage_that_is_not_eligible(
        self, tmp_path: Path
    ) -> None:
        record, execution = to_the_gap(tmp_path)
        execution.forget(record.run_id)

        view = execution.staged_envelopes(record)

        assert view.status == "STAGED"
        assert view.execution_status == "INTERRUPTED"
        assert view.stage.envelopes
        assert "EXECUTION_NOT_COMPLETED" in view.release_blockers

    def test_a_completed_verified_stage_is_eligible(self, tmp_path: Path) -> None:
        record, _, _ = completed(tmp_path)

        view = port(tmp_path).staged_envelopes(record)

        assert view.execution_status == "COMPLETED"
        assert view.release_blockers == ()
        assert view.release_eligible

    def test_a_draft_nothing_executed_has_no_stage(self, tmp_path: Path) -> None:
        view = port(tmp_path).staged_envelopes(draft())

        assert view.status == "NOT_STAGED"
        assert view.stage is None
        assert set(view.release_blockers) == {
            "NOTHING_STAGED",
            "EXECUTION_NOT_COMPLETED",
        }


# --- Retry publication -> same message/content, no duplicate staged fact ------


class TestARetryIsIdempotent:
    def test_restaging_the_whole_series_adds_nothing(self, tmp_path: Path) -> None:
        record, execution, _ = completed(tmp_path)
        stages = JsonSourceStages(tmp_path / "stages")
        existing = stages.read(record.run_id)
        before = stage_file(tmp_path, record).read_bytes()

        admission = stages.admit(
            run_id=record.run_id,
            site_id=existing.site_id,
            source_id=existing.source_id,
            gateway_id=existing.gateway_id,
            mapping=existing.mapping,
            envelopes=existing.envelopes,
        )

        assert admission.added == 0
        assert admission.already_staged == len(existing.envelopes)
        assert stage_file(tmp_path, record).read_bytes() == before

    def test_stepping_republishes_every_earlier_envelope_as_a_retry(
        self, tmp_path: Path
    ) -> None:
        record = draft()
        execution = port(tmp_path)
        execution.start(record)
        execution.step(record, boundaries=10, from_boundary=0)
        first = execution.staged_envelopes(record).stage.envelopes
        execution.step(record, boundaries=10, from_boundary=10)
        second = execution.staged_envelopes(record).stage.envelopes

        assert second[: len(first)] == first
        assert len({item.message_id for item in second}) == len(second)


# --- Same id with changed payload -> explicit conflict -------------------------


class TestSameIdentityDifferentContentConflicts:
    def test_a_changed_payload_is_refused_and_the_stage_is_unchanged(
        self, tmp_path: Path
    ) -> None:
        record, _, _ = completed(tmp_path)
        stages = JsonSourceStages(tmp_path / "stages")
        existing = stages.read(record.run_id)
        target = existing.envelopes[5]
        altered = replace(target, value=target.value + 1)
        assert altered.message_id == target.message_id

        with pytest.raises(StageConflict) as raised:
            stages.admit(
                run_id=record.run_id,
                site_id=existing.site_id,
                source_id=existing.source_id,
                gateway_id=existing.gateway_id,
                mapping=existing.mapping,
                envelopes=[altered],
            )

        assert raised.value.kind == "CONTENT_CONFLICT"
        reread = stages.read(record.run_id)
        assert reread.envelopes == existing.envelopes
        assert reread.envelope(target.message_id) == target

    def test_a_refused_conflict_is_recorded_and_blocks_release(
        self, tmp_path: Path
    ) -> None:
        record, _, _ = completed(tmp_path)
        stages = JsonSourceStages(tmp_path / "stages")
        existing = stages.read(record.run_id)
        altered = replace(existing.envelopes[0], value=Fraction(1))
        with pytest.raises(StageConflict):
            stages.admit(
                run_id=record.run_id,
                site_id=existing.site_id,
                source_id=existing.source_id,
                gateway_id=existing.gateway_id,
                mapping=existing.mapping,
                envelopes=[altered],
            )

        view = port(tmp_path).staged_envelopes(record)

        assert view.status == "STAGED"
        assert "CONFLICTING_PUBLICATION" in view.release_blockers
        assert [item.message_id for item in view.stage.refused] == [
            altered.message_id
        ]


# --- Inject private truth / unknown field -> strict boundary rejection --------


class TestPrivateTruthCannotEnterAStage:
    def test_the_stage_file_carries_no_private_value_or_label(
        self, tmp_path: Path
    ) -> None:
        """Smuggling attempted by looking for what WOULD leak, not a known field.

        The true tank level at every boundary differs from every published
        reading by the sensor's bias, so if any true value had been copied in it
        would appear as a number here. The scenario's event and cause names are
        what a suppression sentence carries.
        """
        record, _, projection = completed(tmp_path)
        text = stage_file(tmp_path, record).read_text()
        from assetops_simulator.kernel.execute import execute

        from execution_adapter import frozen_world_inputs

        trajectory = execute(frozen_world_inputs(record))
        true_levels = {
            value
            for boundary in trajectory.boundaries
            for address, value in boundary.stocks
            if address == "fuel-tank-volume@fuel-tank"
        }
        staged_values = {
            item.value
            for item in port(tmp_path).staged_envelopes(record).stage.envelopes
        }
        assert true_levels and staged_values
        assert not true_levels & staged_values
        for private in (
            "fuel-level-reporting-gap",
            "fuel-removal",
            "reporting-availability",
            "fuel-tank-volume@",
            "SUPPRESSED_BY_GAP",
            "true_value",
            "received_at",
            "fuel-loss-event",
        ):
            assert private not in text, private

    def test_an_envelope_carrying_a_smuggled_field_cannot_be_read_back(
        self, tmp_path: Path
    ) -> None:
        """Edit the persisted stage to add a private field to one envelope.

        Even with the integrity digest recomputed to match - the strongest
        tamper - the strict envelope parser refuses it, so the stage is
        unreadable rather than carrying the field.
        """
        record, _, _ = completed(tmp_path)
        path = stage_file(tmp_path, record)
        document = json.loads(path.read_text())
        envelope = json.loads(document["envelopes"][0])
        envelope["payload"]["true_value"] = "254.02"
        document["envelopes"][0] = json.dumps(
            envelope, sort_keys=True, separators=(",", ":")
        )
        path.write_text(
            json.dumps(document, sort_keys=True, separators=(",", ":"))
        )

        view = port(tmp_path).staged_envelopes(record)

        assert view.status == "STAGE_UNREADABLE"
        assert "true_value" in view.unreadable_detail
        assert view.release_blockers == ("INTEGRITY_FAILURE",)

    def test_admission_refuses_anything_that_is_not_an_envelope(
        self, tmp_path: Path
    ) -> None:
        record, _, projection = completed(tmp_path)
        stages = JsonSourceStages(tmp_path / "stages")
        existing = stages.read(record.run_id)
        for smuggled in (
            projection,
            projection.observations[0],
            projection.recent_reports[0],
            {"true_value": "254.02"},
            json.loads(canonical_envelope_json(existing.envelopes[0])),
        ):
            with pytest.raises(EnvelopeRejected) as raised:
                stages.admit(
                    run_id=record.run_id,
                    site_id=existing.site_id,
                    source_id=existing.source_id,
                    gateway_id=existing.gateway_id,
                    mapping=existing.mapping,
                    envelopes=[smuggled],
                )
            assert raised.value.kind == "NOT_AN_ENVELOPE"


# --- Change current mapping -> existing stage unchanged ------------------------


class TestAChangedMappingCannotReinterpretAStage:
    def test_a_reader_under_a_new_mapping_reads_the_old_stage_unchanged(
        self, tmp_path: Path
    ) -> None:
        record, _, _ = completed(tmp_path)
        before = stage_file(tmp_path, record).read_bytes()
        changed = replace(
            SIMULATOR_LAB_GATEWAY_MAPPINGS,
            mapping_version=2,
            publication_latency_seconds=30,
        )

        view = port(tmp_path, gateway_mapping=changed).staged_envelopes(record)

        assert view.stage.mapping == SIMULATOR_LAB_GATEWAY_MAPPINGS
        assert all(item.mapping_version == 1 for item in view.stage.envelopes)
        assert view.stage.envelopes[-1].published_at.endswith(":03Z")
        assert stage_file(tmp_path, record).read_bytes() == before

    def test_envelopes_under_a_new_mapping_are_refused_not_mixed_in(
        self, tmp_path: Path
    ) -> None:
        record, _, projection = completed(tmp_path)
        stages = JsonSourceStages(tmp_path / "stages")
        existing = stages.read(record.run_id)
        changed = replace(SIMULATOR_LAB_GATEWAY_MAPPINGS, mapping_version=2)
        republished = publish(
            fuel_series(record, projection),
            changed,
            reporting_inputs(record).interval,
            site_id=existing.site_id,
            source_id=existing.source_id,
            gateway_id=existing.gateway_id,
        )

        with pytest.raises(StageConflict) as raised:
            stages.admit(
                run_id=record.run_id,
                site_id=existing.site_id,
                source_id=existing.source_id,
                gateway_id=existing.gateway_id,
                mapping=changed,
                envelopes=republished,
            )

        assert raised.value.kind == "MAPPING_CONFLICT"
        assert stages.read(record.run_id).envelopes == existing.envelopes

    def test_a_run_staged_under_a_new_mapping_says_so(self, tmp_path: Path) -> None:
        changed = replace(
            SIMULATOR_LAB_GATEWAY_MAPPINGS,
            mapping_version=2,
            publication_latency_seconds=30,
        )
        record, execution, _ = completed(tmp_path, gateway_mapping=changed)

        view = execution.staged_envelopes(record)

        assert view.stage.mapping.mapping_version == 2
        assert view.stage.envelopes[-1].published_at.endswith(":30Z")


# --- Truncated / corrupt persisted content -> inspection error, not valid stage -


class TestDamagedContentIsAnErrorNotAStage:
    @pytest.mark.parametrize(
        "damage",
        [
            lambda text: text[: len(text) // 2],
            lambda text: text[:-1],
            lambda text: "",
            lambda text: text.replace('373.52', '373.53', 1),
            lambda text: text.replace("simulator-lab-gateway-fuel", "other", 1),
            lambda text: text + "\n",
        ],
        ids=["half", "last-byte", "empty", "edited-value", "edited-mapping", "reformatted"],
    )
    def test_the_stage_is_unreadable_and_not_eligible(
        self, tmp_path: Path, damage
    ) -> None:
        record, _, _ = completed(tmp_path)
        path = stage_file(tmp_path, record)
        original = path.read_text()
        damaged = damage(original)
        assert damaged != original
        path.write_text(damaged)

        view = port(tmp_path).staged_envelopes(record)

        assert view.status == "STAGE_UNREADABLE"
        assert view.stage is None
        assert view.release_blockers == ("INTEGRITY_FAILURE",)
        assert view.unreadable_detail

    def test_an_unreadable_stage_is_never_overwritten_by_staging(
        self, tmp_path: Path
    ) -> None:
        record = draft()
        execution = port(tmp_path)
        execution.start(record)
        execution.step(record, boundaries=10, from_boundary=0)
        path = stage_file(tmp_path, record)
        path.write_text(path.read_text()[:100])
        damaged = path.read_bytes()

        projection = execution.step(record, boundaries=10, from_boundary=10)

        assert path.read_bytes() == damaged
        assert any("staging refused" in note for note in projection.notes)

    def test_a_write_that_dies_midway_leaves_the_previous_stage(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        record = draft()
        execution = port(tmp_path)
        execution.start(record)
        execution.step(record, boundaries=10, from_boundary=0)
        path = stage_file(tmp_path, record)
        before = path.read_bytes()

        def dies(*_args, **_kwargs):
            raise OSError("the process died before the rename")

        monkeypatch.setattr(os, "replace", dies)
        with pytest.raises(OSError):
            execution.step(record, boundaries=10, from_boundary=10)
        monkeypatch.undo()

        # The complete earlier stage is what reads back, and verifies.
        assert path.read_bytes() == before
        assert parse_stage_text(before.decode("utf-8"), record.run_id).envelopes
        # The half-finished write exists only under a name no reader opens.
        assert (tmp_path / "stages" / f"{record.run_id}.json.partial").exists()
        assert port(tmp_path).staged_envelopes(record).status == "STAGED"

    def test_a_partial_file_alone_is_not_a_stage(self, tmp_path: Path) -> None:
        record = draft()
        root = tmp_path / "stages"
        root.mkdir(parents=True)
        (root / f"{record.run_id}.json.partial").write_text('{"envelopes":[')

        assert port(tmp_path).staged_envelopes(record).status == "NOT_STAGED"

    def test_a_stage_declaring_another_run_is_refused(self, tmp_path: Path) -> None:
        record, _, _ = completed(tmp_path)
        text = stage_file(tmp_path, record).read_text()

        with pytest.raises(StageUnreadable):
            parse_stage_text(text, "run-someone-else")


# --- Stage a complete Draft -> accepted history unchanged ----------------------


class TestStagingWritesNoAcceptedHistory:
    def test_the_site_store_is_byte_identical(self, tmp_path: Path) -> None:
        before = _site_store_digest()

        completed(tmp_path)

        assert _site_store_digest() == before

    def test_the_operator_site_routes_answer_the_same_before_and_after(
        self, tmp_path: Path
    ) -> None:
        site = site_from_template(HYBRID_TEMPLATE, site_id="MG-001")
        record = draft(site=site)
        store = FakeRuns()
        store.create_run(record)
        execution = port(tmp_path)
        client = TestClient(
            create_app(
                FeatureFlags(simulator_lab_enabled=True),
                site_repository=FakeSites((site,)),
                run_repository=store,
                execution=execution,
            )
        )
        before = (
            client.get("/api/sites").json(),
            client.get("/api/sites/MG-001").json(),
        )

        client.post(f"/api/simulator-lab/runs/{record.run_id}/execution/start")
        client.post(f"/api/simulator-lab/runs/{record.run_id}/execution/run-to-end")
        staged = client.get(STAGE_ROUTE.format(run_id=record.run_id)).json()
        assert staged["stage"]["envelopes"], "something was staged"

        after = (
            client.get("/api/sites").json(),
            client.get("/api/sites/MG-001").json(),
        )
        assert after == before
        assert "envelope" not in json.dumps(after)
        assert "373.52" not in json.dumps(after)


# --- The gated API: what it serves, and what disabling the Lab does ------------


class TestTheInspectorApi:
    def served(self, tmp_path: Path, enabled: bool = True):
        site = site_from_template(HYBRID_TEMPLATE, site_id="MG-001")
        record = draft(site=site)
        store = FakeRuns()
        store.create_run(record)
        return (
            TestClient(
                create_app(
                    FeatureFlags(simulator_lab_enabled=enabled),
                    site_repository=FakeSites((site,)),
                    run_repository=store,
                    execution=port(tmp_path) if enabled else None,
                )
            ),
            record,
        )

    def test_the_payload_is_the_reloaded_stage_byte_for_byte(
        self, tmp_path: Path
    ) -> None:
        client, record = self.served(tmp_path)
        client.post(f"/api/simulator-lab/runs/{record.run_id}/execution/start")
        client.post(f"/api/simulator-lab/runs/{record.run_id}/execution/run-to-end")

        payload = client.get(STAGE_ROUTE.format(run_id=record.run_id)).json()[
            "stage"
        ]
        persisted = json.loads(stage_file(tmp_path, record).read_text())

        assert payload["status"] == "STAGED"
        assert payload["release_eligible"] is True
        assert [item["canonical"] for item in payload["envelopes"]] == persisted[
            "envelopes"
        ]
        assert payload["integrity_digest"] == persisted["integrity"]["digest"]
        newest = payload["envelopes"][-1]
        assert newest["source_time"] != newest["published_at"]
        assert payload["mapping"]["mapping_version"] == 1
        assert payload["envelope_schema_version"] == 1
        # Every value on the wire is text; no float anywhere.
        assert "." not in "".join(
            str(v) for v in _numbers(payload)
        ), "a float reached the wire"

    def test_nothing_edits_a_staged_record(self, tmp_path: Path) -> None:
        client, record = self.served(tmp_path)
        path = STAGE_ROUTE.format(run_id=record.run_id)
        for method in ("post", "put", "patch", "delete"):
            assert getattr(client, method)(path).status_code == 405, method

    def test_disabling_the_lab_serves_no_stage(self, tmp_path: Path) -> None:
        client, record = self.served(tmp_path, enabled=False)

        response = client.get(STAGE_ROUTE.format(run_id=record.run_id))

        assert response.status_code == 404


def _numbers(value: object):
    if isinstance(value, bool):
        return
    if isinstance(value, (int, float)):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _numbers(item)
    elif isinstance(value, list):
        for item in value:
            yield from _numbers(item)
