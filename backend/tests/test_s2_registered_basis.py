"""S2-01a phase 1 - registered Lab basis: selection, verification and freeze.

Default suite, no database: runs over `InMemoryFoundationStore` with the
imported and converted KOBO-001 (S1-02). The PostgreSQL behaviour of the same
selection is in `test_s2_registered_basis_postgres.py`.

Decision: D-2026-10-08-s2-lab-snapshot-selection-and-run-boundary.
"""

from __future__ import annotations

import hashlib
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest
import yaml
from foundation_fakes import InMemoryFoundationStore
from run_fixtures import FakeRuns, FakeScenarios, FakeSites
from test_s1_bindings import CONVERTED_AT, converted
from test_s1_cutover import NOW, Clock, app_for, legacy_root  # noqa: F401

from assetops_backend.runs.adapters.yaml_run_store import YamlRunStore
from assetops_backend.runs.parsing import parse_run_document, render_run_document
from assetops_backend.runs.ports import RunConfigurationInvalid
from assetops_backend.runs.profiles import (
    DAYTIME_MINI_GRID_MODEL,
    LAB_PUBLICATION_PROFILE,
)
from assetops_backend.runs.refusals import RunSetupRefused
from assetops_backend.runs.registered_basis import RegisteredLabBasis
from assetops_backend.runs.service import RunSetupService
from assetops_backend.scenarios.parsing import parse_scenario_document
from assetops_backend.sites.cutover import ImportedSiteRegistry
from assetops_backend.sites.foundation_content import battery_reserve
from assetops_backend.sites.foundation_records import Registrations
from assetops_backend.sites.foundation_service import FoundationService
from assetops_backend.sites.ports import SiteStoreUnavailable

REPOSITORY = Path(__file__).resolve().parents[2]
SCENARIO = parse_scenario_document(
    yaml.safe_load((REPOSITORY / "config" / "scenarios" / "kobo-daytime.yaml").read_text(encoding="utf-8")),
    source="kobo-daytime",
    origin="SHIPPED",
)
START = "2026-09-30T03:00:00Z"
END = "2026-09-30T15:00:00Z"
#: A later reserve publication effective here splits the open period.
SPLIT = datetime(2026, 10, 5, 0, 0, 0, tzinfo=timezone.utc)
SPLIT_TEXT = "2026-10-05T00:00:00Z"


def text(instant: datetime) -> str:
    return instant.strftime("%Y-%m-%dT%H:%M:%SZ")


def request(**overrides: Any) -> dict[str, Any]:
    body: dict[str, Any] = {
        "site_id": "KOBO-001",
        "foundation_version": 2,
        "scenario_id": SCENARIO.scenario_id,
        "scenario_version": SCENARIO.version.scenario_version,
        "interval": {"start_time": START, "end_time": END},
        "timestep_minutes": 15,
        "seed": 20260929,
        "model_profile": {
            "profile_id": DAYTIME_MINI_GRID_MODEL.model_profile_id,
            "profile_version": DAYTIME_MINI_GRID_MODEL.model_profile_version,
        },
        "publication_profile": {
            "profile_id": LAB_PUBLICATION_PROFILE.publication_profile_id,
            "profile_version": LAB_PUBLICATION_PROFILE.publication_profile_version,
        },
        "run_inputs": [],
    }
    body.update(overrides)
    return body


def setup_service(store, runs=None, clock=None) -> RunSetupService:
    registry = ImportedSiteRegistry(FoundationService(store, "demo", clock or Clock(NOW)))
    return RunSetupService(
        runs if runs is not None else FakeRuns(),
        FakeSites(()),
        FakeScenarios((SCENARIO,)),
        model_profiles=(DAYTIME_MINI_GRID_MODEL,),
        publication_profiles=(LAB_PUBLICATION_PROFILE,),
        now=lambda: text(NOW),
        registered_bases=RegisteredLabBasis(registry),
    )


def refusal(store, body, runs=None) -> RunSetupRefused:
    runs = runs if runs is not None else FakeRuns()
    with pytest.raises(RunSetupRefused) as caught:
        setup_service(store, runs).create_draft_run(body)
    assert runs.list_runs() == (), "a refused setup allocated a Draft"
    return caught.value


def publish_reserve(store, result, value: float, effective_from: datetime = SPLIT, at: datetime = NOW):
    service = FoundationService(store, "demo", Clock(at))
    current = [r for r in store.rows[result.site.id] if r.superseded_at is None]
    reserve = battery_reserve(current[-1].content)
    return service.publish_battery_reserve(
        result.tenant, result.site, asset_code=reserve["asset_code"], value=value,
        effective_from=effective_from, note="S2-01a test",
    )


def current_set(store, result, at: datetime):
    return next(
        s for s in store.sets[result.site.id]
        if s.superseded_at is None and s.valid_from <= at and (s.valid_to is None or at < s.valid_to)
    )


class TestRegisteredSelection:
    def test_imported_kobo_creates_a_draft_from_its_registered_basis(self) -> None:
        store, result, outcome = converted()
        record = setup_service(store).create_draft_run(request())
        basis = record.registered_basis
        pinned = outcome.published.changed
        assert basis is not None
        assert basis.binding_set_revision_id == str(pinned.id)
        assert basis.binding_set_version == pinned.version
        assert basis.foundation_revision_id == str(pinned.foundation_revision_id)
        assert basis.foundation_version == record.deterministic_identity.site.foundation_version == 2
        assert basis.snapshot_sha256 == pinned.snapshot_sha256
        assert basis.snapshot_canonical.encode("utf-8") == pinned.snapshot_canonical
        assert basis.snapshot_schema == "assetops.acquisition-snapshot/1"
        assert basis.source_start == START
        assert basis.knowledge_at == text(NOW), "knowledge_at defaults to the server's now, frozen"
        assert basis.selection == "CURRENT" and basis.current_registration_gaps == ()
        assert basis.foundation_valid_to is None and basis.binding_valid_to is None

    def test_signal_mappings_are_the_registered_bindings_not_the_legacy_list(self) -> None:
        store, _, outcome = converted()
        record = setup_service(store).create_draft_run(request())
        mappings = record.deterministic_identity.signal_mappings
        bound = {b.id for b in outcome.published.changed.bindings if b.asset_id is not None}
        assert {m.mapping_id for m in mappings} == {str(i) for i in bound}
        assert ("generator-controller", "status") in {(m.device_id, m.signal_id) for m in mappings}

    def test_a_mismatched_foundation_version_is_refused_with_no_draft(self) -> None:
        store, _, _ = converted()
        refused = refusal(store, request(foundation_version=1))
        assert refused.kind == "VERSION_UNAVAILABLE"
        assert "registered at Foundation version 2" in refused.message

    def test_a_knowledge_instant_before_the_bindings_were_recorded_is_refused(self) -> None:
        store, _, _ = converted()
        refused = refusal(store, request(knowledge_at=text(CONVERTED_AT - timedelta(minutes=1)),
                                         foundation_version=1))
        assert refused.kind == "REGISTERED_BASIS_UNAVAILABLE"
        assert refused.reason_code == "BINDINGS_NOT_REGISTERED"

    def test_a_period_before_any_registration_is_refused(self) -> None:
        store, _, _ = converted()
        refused = refusal(store, request(interval={"start_time": "2026-09-01T03:00:00Z",
                                                   "end_time": "2026-09-01T15:00:00Z"}))
        assert refused.reason_code == "FOUNDATION_NOT_REGISTERED"
        assert "not substituted" in refused.message

    def test_a_future_knowledge_instant_is_refused(self) -> None:
        store, _, _ = converted()
        refused = refusal(store, request(knowledge_at=text(NOW + timedelta(days=1))))
        assert refused.reason_code == "KNOWLEDGE_AT_IN_FUTURE"

    def test_knowledge_at_is_refused_for_a_legacy_yaml_site(self) -> None:
        store, _, _ = converted()
        refused = refusal(store, request(site_id="MG-LEGACY-1", knowledge_at=text(NOW)))
        assert refused.kind == "REQUEST_INVALID"

    def test_a_malformed_knowledge_instant_is_refused(self) -> None:
        store, _, _ = converted()
        assert refusal(store, request(knowledge_at="yesterday")).kind == "REQUEST_INVALID"


class TestBoundary:
    def test_an_interval_crossing_a_configuration_boundary_is_refused(self) -> None:
        store, result, _ = converted()
        publish_reserve(store, result, 40)
        refused = refusal(store, request(interval={"start_time": "2026-10-04T18:00:00Z",
                                                   "end_time": "2026-10-05T06:00:00Z"}))
        assert refused.kind == "REGISTERED_BASIS_BOUNDARY"
        assert SPLIT_TEXT in refused.message and "inside the run interval" in refused.message

    def test_an_interval_ending_exactly_at_the_boundary_is_refused(self) -> None:
        store, result, _ = converted()
        publish_reserve(store, result, 40)
        refused = refusal(store, request(interval={"start_time": "2026-10-04T12:00:00Z",
                                                   "end_time": SPLIT_TEXT}))
        assert refused.kind == "REGISTERED_BASIS_BOUNDARY"
        assert "at the run's end_time" in refused.message

    def test_an_interval_ending_one_step_before_the_boundary_is_accepted(self) -> None:
        store, result, _ = converted()
        publish_reserve(store, result, 40)
        record = setup_service(store).create_draft_run(
            request(interval={"start_time": "2026-10-04T11:45:00Z", "end_time": "2026-10-04T23:45:00Z"},
                    foundation_version=3)
        )
        assert record.registered_basis.binding_valid_to == SPLIT_TEXT

    def test_a_run_starting_at_the_boundary_selects_the_later_basis(self) -> None:
        store, result, _ = converted()
        publish_reserve(store, result, 40)
        later = current_set(store, result, SPLIT)
        record = setup_service(store).create_draft_run(
            request(interval={"start_time": SPLIT_TEXT, "end_time": "2026-10-05T12:00:00Z"},
                    foundation_version=4)
        )
        assert record.registered_basis.binding_set_revision_id == str(later.id)


class TestFrozenAcrossPublication:
    def test_a_later_publication_never_changes_an_existing_draft(self, tmp_path) -> None:
        store, result, _ = converted()
        runs = YamlRunStore(tmp_path / "runs")
        first = setup_service(store, runs).create_draft_run(request())
        publish_reserve(store, result, 40)
        reloaded = YamlRunStore(tmp_path / "runs").get_run(first.run_id)  # a fresh process
        assert reloaded.registered_basis == first.registered_basis
        second = setup_service(store, runs).create_draft_run(
            request(interval={"start_time": "2026-10-05T03:00:00Z", "end_time": "2026-10-05T15:00:00Z"},
                    foundation_version=4)
        )
        assert second.registered_basis.binding_set_revision_id != first.registered_basis.binding_set_revision_id
        assert second.registered_basis.snapshot_sha256 != first.registered_basis.snapshot_sha256
        assert YamlRunStore(tmp_path / "runs").get_run(second.run_id).registered_basis == second.registered_basis

    def test_default_knowledge_selects_the_correction_and_earlier_knowledge_the_original(self) -> None:
        store, result, outcome = converted()
        original = outcome.published.changed
        knowledge = text(NOW - timedelta(minutes=1))
        publish_reserve(store, result, 40)
        corrected = setup_service(store).create_draft_run(request(foundation_version=3)).registered_basis
        assert corrected.binding_set_revision_id != str(original.id)
        # The correction's earlier segment ended at SPLIT, before NOW: historical.
        assert corrected.selection == "HISTORICAL" and corrected.binding_valid_to == SPLIT_TEXT
        recovered = setup_service(store).create_draft_run(
            request(knowledge_at=knowledge)
        ).registered_basis
        assert recovered.binding_set_revision_id == str(original.id)
        assert recovered.knowledge_at == knowledge
        assert recovered.selection == "HISTORICAL"
        assert recovered.snapshot_canonical.encode("utf-8") == original.snapshot_canonical
        assert recovered.snapshot_sha256 == original.snapshot_sha256
        assert recovered.binding_valid_to is None, "the ORIGINAL valid period is what was checked"


def edit_current_sources(store, result) -> None:
    """An allowed current registration identity edit: rename every source."""
    regs = store.registered[result.site.id]
    store.registered[result.site.id] = Registrations(
        regs.assets,
        regs.gateways,
        tuple(replace(s, source_external_id=s.source_external_id + "-renamed") for s in regs.sources),
    )


class TestHistoricalAvailability:
    """S1-02 carry n5: historical selection does not depend on current rows."""

    def test_a_historical_basis_survives_a_current_registration_edit(self, legacy_root) -> None:
        store, result, outcome = converted()
        knowledge = text(NOW - timedelta(minutes=1))
        publish_reserve(store, result, 40)
        edit_current_sources(store, result)
        basis = setup_service(store).create_draft_run(request(knowledge_at=knowledge)).registered_basis
        assert basis.selection == "HISTORICAL"
        assert basis.snapshot_sha256 == outcome.published.changed.snapshot_sha256
        assert "SOURCE_NOT_REGISTERED" in basis.current_registration_gaps
        client = app_for(store, legacy_root)
        download = client.get("/api/sites/KOBO-001/foundation/snapshot",
                              params={"at": START, "knowledge_at": knowledge})
        assert download.status_code == 200, download.text
        assert download.headers["X-AssetOps-Snapshot-Selection"] == "HISTORICAL"
        assert hashlib.sha256(download.content).hexdigest() == outcome.published.changed.snapshot_sha256

    def test_a_current_basis_still_refuses_on_a_current_registration_gap(self, legacy_root) -> None:
        store, result, _ = converted()
        edit_current_sources(store, result)
        refused = refusal(store, request())
        assert refused.kind == "REGISTERED_BASIS_UNAVAILABLE"
        assert refused.reason_code == "ACQUISITION_SNAPSHOT_UNAVAILABLE"
        assert "SOURCE_NOT_REGISTERED" in refused.message
        client = app_for(store, legacy_root)
        assert client.get("/api/sites/KOBO-001/foundation/snapshot").status_code == 409

    def test_an_ended_period_is_historical_and_survives_the_edit(self) -> None:
        store, result, _ = converted()
        publish_reserve(store, result, 40, effective_from=NOW - timedelta(days=1))
        edit_current_sources(store, result)
        basis = setup_service(store).create_draft_run(request(foundation_version=3)).registered_basis
        assert basis.selection == "HISTORICAL" and basis.binding_valid_to is not None

    def test_a_site_row_the_parser_refuses_is_typed_even_for_a_historical_basis(self) -> None:
        # Known limit (S2-01a-questions-1): the Site row's name, type and time
        # zone are not in the pinned snapshot, so the Lab record still reads
        # them from the current row. A row the parser refuses is a typed
        # refusal with no Draft, never a substituted value.
        store, result, _ = converted()
        knowledge = text(NOW - timedelta(minutes=1))
        publish_reserve(store, result, 40)
        store.sites = [replace(s, name=" ") if s.id == result.site.id else s for s in store.sites]
        refused = refusal(store, request(knowledge_at=knowledge))
        assert refused.kind == "REGISTERED_BASIS_UNAVAILABLE"
        assert refused.reason_code == "SITE_RECORD_INVALID"

    def test_a_site_type_the_role_set_does_not_serve_refuses_even_historically(self) -> None:
        store, result, _ = converted()
        knowledge = text(NOW - timedelta(minutes=1))
        publish_reserve(store, result, 40)
        store.sites = [replace(s, site_type="SOLAR_HOME") if s.id == result.site.id else s for s in store.sites]
        refused = refusal(store, request(knowledge_at=knowledge))
        assert refused.reason_code == "SITE_TYPE_ROLE_SET_MISMATCH"

    def test_selected_foundation_content_gaps_always_refuse(self, tmp_path) -> None:
        store, result, _ = converted()
        rows = store.rows[result.site.id]
        store.rows[result.site.id] = [
            replace(r, content={**r.content, "site_controls": []}) if r.superseded_at is None else r
            for r in rows
        ]
        refused = refusal(store, request())
        assert refused.reason_code == "ACQUISITION_SNAPSHOT_UNAVAILABLE"
        assert "SITE_CONTROL_MISSING" in refused.message


def tamper(store, result, **changes) -> None:
    pinned = current_set(store, result, datetime(2026, 9, 30, 3, tzinfo=timezone.utc))
    store.sets[result.site.id] = [
        replace(s, **changes) if s.id == pinned.id else s for s in store.sets[result.site.id]
    ]


class TestFailureIntegrity:
    @pytest.mark.parametrize(
        "changes,code",
        [
            ({"snapshot_sha256": "0" * 64}, "ACQUISITION_SNAPSHOT_HASH_MISMATCH"),
            ({"snapshot_canonical": b""}, "ACQUISITION_SNAPSHOT_INCONSISTENT"),
            ({"snapshot_schema": "assetops.acquisition-snapshot/9"}, "ACQUISITION_SNAPSHOT_SCHEMA_UNSUPPORTED"),
        ],
    )
    def test_bad_stored_snapshots_fail_closed_with_no_draft(self, changes, code) -> None:
        store, result, _ = converted()
        tamper(store, result, **changes)
        refused = refusal(store, request())
        assert refused.kind == "REGISTERED_BASIS_UNAVAILABLE" and refused.reason_code == code

    def test_snapshot_bytes_disagreeing_with_their_publication_references_fail_closed(self) -> None:
        store, result, _ = converted()
        pinned = current_set(store, result, datetime(2026, 9, 30, 3, tzinfo=timezone.utc))
        forged = pinned.snapshot_canonical.replace(str(pinned.gateway_id).encode(), b"0" * 8 + str(pinned.gateway_id).encode()[8:])
        tamper(store, result, snapshot_canonical=forged, snapshot_sha256=hashlib.sha256(forged).hexdigest())
        refused = refusal(store, request())
        assert refused.reason_code == "ACQUISITION_SNAPSHOT_INCONSISTENT"
        assert "gateway" in refused.message

    def test_an_unreachable_store_fails_closed_with_no_draft(self) -> None:
        store, _, _ = converted()
        store.unavailable = True
        runs = FakeRuns()
        with pytest.raises(SiteStoreUnavailable):
            setup_service(store, runs).create_draft_run(request())
        assert runs.list_runs() == ()

    def test_a_stored_run_whose_snapshot_text_was_altered_is_refused_on_reload(self) -> None:
        store, _, _ = converted()
        record = setup_service(store).create_draft_run(request())
        document = render_run_document(record)
        assert parse_run_document(document, source="test") == record
        document["registered_basis"]["snapshot_canonical"] += " "
        with pytest.raises(RunConfigurationInvalid, match="hashes to"):
            parse_run_document(document, source="test")

    def test_a_legacy_run_document_round_trips_without_a_basis(self) -> None:
        store, _, _ = converted()
        record = replace(setup_service(store).create_draft_run(request()), registered_basis=None)
        document = render_run_document(record)
        assert "registered_basis" not in document
        assert parse_run_document(document, source="test").registered_basis is None


class TestOverHttp:
    def test_setup_route_creates_and_refuses_with_typed_reasons(self, tmp_path, legacy_root) -> None:
        from test_s1_cutover import ON

        store, result, _ = converted()
        publish_reserve(store, result, 40)
        client = app_for(
            store, legacy_root, flags=ON, run_repository=YamlRunStore(tmp_path / "runs"),
            scenario_repository=FakeScenarios((SCENARIO,)),
        )
        created = client.post("/api/simulator-lab/runs", json=request(foundation_version=3))
        assert created.status_code == 201, created.text
        basis = created.json()["run"]["configuration_basis"]
        assert basis["store"] == "REGISTERED" and basis["accepted_evidence"] is False
        assert basis["binding_valid_to"] == SPLIT_TEXT and basis["knowledge_at"] == text(NOW)
        assert "snapshot_canonical" not in basis
        run_id = created.json()["run"]["run_id"]
        reread = client.get(f"/api/simulator-lab/runs/{run_id}").json()["run"]["configuration_basis"]
        assert reread == basis
        crossing = client.post("/api/simulator-lab/runs", json=request(
            interval={"start_time": "2026-10-04T18:00:00Z", "end_time": "2026-10-05T06:00:00Z"},
            foundation_version=3))
        assert crossing.status_code == 422
        detail = crossing.json()["detail"]
        assert detail["refusal_kind"] == "REGISTERED_BASIS_BOUNDARY" and detail["run_created"] is False
        assert detail["reason_code"] == "BASIS_BOUNDARY"
        assert len(YamlRunStore(tmp_path / "runs").list_runs()) == 1


class TestRegisteredControls:
    """AC4: a registered Draft runs through its frozen basis; Commit refuses."""

    def client_with_draft(self, tmp_path, legacy_root):
        from test_s1_cutover import ON, StagedExecution

        store, result, _ = converted()
        execution = StagedExecution()
        runs = YamlRunStore(tmp_path / "runs")
        client = app_for(
            store, legacy_root, flags=ON, run_repository=runs, execution=execution,
            scenario_repository=FakeScenarios((SCENARIO,)),
        )
        created = client.post("/api/simulator-lab/runs", json=request())
        assert created.status_code == 201, created.text
        return client, execution, runs, created.json()["run"]

    def test_start_step_and_run_to_end_reach_the_port_for_a_registered_draft(
        self, tmp_path, legacy_root
    ) -> None:
        client, execution, _, run = self.client_with_draft(tmp_path, legacy_root)
        base = f"/api/simulator-lab/runs/{run['run_id']}"
        assert client.post(f"{base}/execution/start").status_code == 200
        step = client.post(f"{base}/execution/step", json={"boundaries": 1, "from_boundary": 0})
        assert step.status_code == 200, step.text
        assert client.post(f"{base}/execution/run-to-end").status_code == 200
        assert [call[0] for call in execution.calls] == ["start", "step", "run_to_end"]

    def test_commit_refuses_a_registered_run_before_the_port_or_commit_store(
        self, tmp_path, legacy_root
    ) -> None:
        client, execution, _, run = self.client_with_draft(tmp_path, legacy_root)
        response = client.post(f"/api/simulator-lab/runs/{run['run_id']}/commit")
        assert response.status_code == 409, response.text
        assert response.json()["detail"]["code"] == "REGISTERED_COMMIT_UNAVAILABLE"
        assert execution.calls == [], "a refused Commit asked the port for its stage"

    def test_stage_is_labelled_registered_with_no_evidence_claim_after_reload(
        self, tmp_path, legacy_root
    ) -> None:
        client, execution, runs, run = self.client_with_draft(tmp_path, legacy_root)
        # A fresh store over the same directory stands for a process restart.
        reread = YamlRunStore(tmp_path / "runs").get_run(run["run_id"])
        assert reread is not None and reread.registered_basis is not None
        stage = client.get(f"/api/simulator-lab/runs/{run['run_id']}/stage")
        assert stage.status_code == 200, stage.text
        basis = stage.json()["frozen_basis"]
        assert basis["configuration_store"] == "REGISTERED"
        assert basis["can_release"] is False and basis["site_imported"] is True
        assert basis["registered_basis"] == run["configuration_basis"]
        assert basis["registered_basis"]["accepted_evidence"] is False
        assert basis["registered_basis"]["snapshot_sha256"] == reread.registered_basis.snapshot_sha256
        # S2-01b: the Stage itself is the gateway ledger's, never the file Stage.
        staged = stage.json()["stage"]
        assert staged["store"] == "GATEWAY_LEDGER" and staged["upload_state"] == "PENDING"
        assert staged["receipts"] == [] and staged["release_eligible"] is False
        assert staged["snapshot_sha256"] == reread.registered_basis.snapshot_sha256
        assert ("staged_envelopes", run["run_id"]) not in execution.calls
        assert staged["seal_refusals"] == []

    def test_a_durable_seal_refusal_travels_with_the_stage(self) -> None:
        """F1: a refusal to seal is carried to the Lab verbatim, not dropped."""
        from assetops_backend.simulator_lab_api import registered_stage_payload
        from assetops_contracts.gateway_stage import (
            REGISTERED_STAGE_STATEMENTS,
            GatewaySealRefusal,
            RegisteredStageView,
        )

        refusal = GatewaySealRefusal(
            source_id="src", sequence_epoch="1", snapshot_sha256="ab" * 32, message_id="m-2",
            kind="TOO_LARGE", field="batch", detail="more than 1048576 bytes",
            last_seen_at="2026-10-01T09:00:00Z", seen_count=2, outbox_state="STAGED",
        )
        view = RegisteredStageView(
            run_id="run", status="SEALING_REFUSED", statement=REGISTERED_STAGE_STATEMENTS["SEALING_REFUSED"],
            execution_status="COMPLETED", snapshot_sha256="ab" * 32, site_id="s", gateway_id="g",
            sequence_epoch="1", envelopes=(), batches=(), holds=(), queue_depth_by_state={},
            seal_refusals=(refusal,),
        )
        payload = registered_stage_payload(view)
        assert payload["status"] == "SEALING_REFUSED"
        assert payload["seal_refusals"] == [{
            "source_id": "src", "sequence_epoch": "1", "message_id": "m-2", "kind": "TOO_LARGE",
            "field": "batch", "detail": "more than 1048576 bytes", "last_seen_at": "2026-10-01T09:00:00Z",
            "seen_count": 2,
        }]

    def test_site_name_and_time_zone_are_labelled_current_row_metadata(
        self, tmp_path, legacy_root
    ) -> None:
        _, _, _, run = self.client_with_draft(tmp_path, legacy_root)
        metadata = run["configuration_basis"]["site_metadata"]
        assert metadata["source"] == "CURRENT_SITE_ROW_AT_SETUP"
        assert metadata["display_name"] and metadata["timezone"] and metadata["site_type"]
