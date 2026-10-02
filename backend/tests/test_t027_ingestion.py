"""T027 phase 1b: committed artifact, one ingestion path, evidence read model.

Envelopes are built from the contracts alone (as `test_run_stage_api.py`
does); nothing here imports a simulator, the host, a stage or a LabProjection.
"""

from __future__ import annotations

import json
from dataclasses import replace
from fractions import Fraction
from typing import Any

import pytest
from fastapi.testclient import TestClient

from route_inventory import served_paths
from run_fixtures import FakeSites, site
from assetops_backend.config import FeatureFlags
from assetops_backend.evidence.adapters.json_evidence_store import JsonEvidenceStore
from assetops_backend.evidence.read_model import EvidenceReadModel
from assetops_backend.evidence.service import IngestionInterrupted, IngestionService
from assetops_backend.main import create_app
from assetops_backend.sites.models import (
    DeviceSignal,
    FoundationDevice,
    SiteFoundation,
    SiteSource,
)
from assetops_contracts.committed_artifact import (
    ArtifactUnreadable,
    artifact_text,
    ingestion_batch,
    parse_artifact_text,
    seal_artifact,
)
from assetops_contracts.ingestion_batch import (
    ConfigurationReference,
    IngestionBatch,
    IngestionBatchRejected,
    ingestion_batch_document,
    parse_ingestion_batch_document,
)
from assetops_contracts.source_envelope import (
    SourceEnvelope,
    SourceMappingEntry,
    SourceMappingSet,
    canonical_envelope_json,
    envelope_message_id,
)

SITE_ID = "MG-900"
SOURCE = "kobo-source"
GATEWAY = "kobo-gateway"
VALID_FROM = "2026-01-01T00:00:00Z"
STAGE_DIGEST = "b" * 64
DISABLED = FeatureFlags(simulator_lab_enabled=False)


def mapping(version: int = 1) -> SourceMappingSet:
    return SourceMappingSet(
        mapping_set_id="kobo-gateway-map",
        mapping_version=version,
        publication_latency_seconds=3,
        entries=(
            SourceMappingEntry("fuel-level-sensor", "fuel-level", "STATE_AT_INSTANT", "L", True),
            SourceMappingEntry(
                "battery-pcs-controller", "state-of-charge", "STATE_AT_INSTANT", "%", True
            ),
            # On the allowlist, but not a signal the Site's Foundation declares.
            SourceMappingEntry("mystery-device", "mystery", "STATE_AT_INSTANT", "kW", False),
        ),
    )


def devices() -> tuple[FoundationDevice, ...]:
    return (
        FoundationDevice(
            device_id="fuel-level-sensor",
            device_type="SENSOR",
            display_name="Fuel level",
            component_id="fuel-tank",
            signals=(DeviceSignal("fuel-level", "Fuel level", "L"),),
        ),
        FoundationDevice(
            device_id="battery-pcs-controller",
            device_type="CONTROLLER",
            display_name="Battery PCS",
            component_id="battery",
            signals=(DeviceSignal("state-of-charge", "State of charge", "%"),),
        ),
    )


def a_site(*, mode: str = "SIMULATED", version: int = 1, site_devices: Any = None):
    record = site(site_id=SITE_ID, devices=devices() if site_devices is None else site_devices)
    return replace(
        record,
        source=SiteSource(mode=mode),
        foundation=replace(record.foundation, version=version),
    )


def envelope(
    minute: int,
    *,
    value: str | None = "100",
    device: str = "fuel-level-sensor",
    signal: str = "fuel-level",
    unit: str = "L",
    gateway: str = GATEWAY,
    publish_delay: int = 3,
    sequence: int | None = None,
) -> SourceEnvelope:
    source_time = f"2026-09-22T00:{minute:02d}:00Z"
    published = f"2026-09-22T00:{minute:02d}:{publish_delay:02d}Z"
    identity = dict(
        site_id=SITE_ID,
        gateway_id=gateway,
        source_id=SOURCE,
        device_id=device,
        signal_id=signal,
        source_time=source_time,
    )
    return SourceEnvelope(
        message_id=envelope_message_id(**identity),
        sequence=minute if sequence is None else sequence,
        mapping_set_id="kobo-gateway-map",
        mapping_version=1,
        published_at=published,
        measurement="STATE_AT_INSTANT",
        value=None if value is None else Fraction(value),
        unit=unit,
        quality="GOOD" if value is not None else "UNAVAILABLE",
        unavailable_reason=None if value is not None else "NO_MEASUREMENT",
        interval_start=None,
        interval_end=None,
        **identity,
    )


def configuration(version: int = 1) -> ConfigurationReference:
    return ConfigurationReference(SITE_ID, version, VALID_FROM)


def sealed(envelopes, run_id: str = "run-1", digest: str = STAGE_DIGEST):
    return seal_artifact(
        run_id=run_id,
        site_id=SITE_ID,
        source_id=SOURCE,
        gateway_id=GATEWAY,
        source_mode="SIMULATED",
        configuration=configuration(),
        mapping=mapping(),
        envelopes=envelopes,
        stage_integrity_digest=digest,
        sealed_at="2026-09-22T01:00:00Z",
    )


def a_batch(texts, *, batch_id: str = "batch-1", mode: str = "SIMULATED",
            gateway: str = GATEWAY, version: int = 1) -> IngestionBatch:
    return IngestionBatch(
        batch_id=batch_id,
        site_id=SITE_ID,
        source_id=SOURCE,
        gateway_id=gateway,
        source_mode=mode,
        configuration=configuration(version),
        mapping=mapping(),
        envelopes=tuple(texts),
    )


class Clock:
    def __init__(self) -> None:
        self.ticks = 0

    def __call__(self) -> str:
        self.ticks += 1
        hours, rest = divmod(self.ticks, 3600)
        return f"2026-09-23T{hours:02d}:{rest // 60:02d}:{rest % 60:02d}Z"


def service(tmp_path, sites=None, **kwargs) -> IngestionService:
    return IngestionService(
        JsonEvidenceStore(tmp_path / "evidence"),
        FakeSites((a_site(),)) if sites is None else sites,
        Clock(),
        **kwargs,
    )


def texts(*envelopes: SourceEnvelope) -> list[str]:
    return [canonical_envelope_json(item) for item in envelopes]


# --- AC1 / AC2: the committed artifact ---------------------------------------


class TestCommittedArtifact:
    def test_seal_round_trips_and_names_each_envelope(self) -> None:
        artifact = sealed([envelope(1), envelope(2)])
        text = artifact_text(artifact)
        assert parse_artifact_text(text) == artifact
        assert [m for m, _ in artifact.manifest] == [e.message_id for e in artifact.envelopes]
        assert artifact.artifact_id.startswith("commit-")
        assert len(artifact.integrity_digest) == 64

    def test_the_same_stage_seals_to_the_same_id_and_text(self) -> None:
        first = sealed([envelope(1)])
        again = sealed([envelope(1)])
        assert first.artifact_id == again.artifact_id
        assert artifact_text(first) == artifact_text(again)
        assert sealed([envelope(1)], digest="c" * 64).artifact_id != first.artifact_id

    @pytest.mark.parametrize(
        "edit",
        [
            lambda t: t.replace('"sealed_at":"2026-09-22T01:00:00Z"', '"sealed_at":"2026-09-22T01:00:01Z"'),
            lambda t: t.replace("\\\"value\\\":\\\"100\\\"", "\\\"value\\\":\\\"101\\\""),
            lambda t: t.replace('"source_mode":"SIMULATED"', '"source_mode":"LIVE"'),
            lambda t: t[:-1] + ',"truth":1}',
            lambda t: t + " ",
        ],
    )
    def test_a_tampered_text_is_unreadable(self, edit) -> None:
        text = artifact_text(sealed([envelope(1)]))
        tampered = edit(text)
        assert tampered != text
        with pytest.raises(ArtifactUnreadable):
            parse_artifact_text(tampered)

    def test_an_envelope_the_mapping_refuses_cannot_be_sealed(self) -> None:
        with pytest.raises(ArtifactUnreadable):
            sealed([envelope(1, unit="mL")])

    def test_the_artifact_is_released_only_as_an_ordinary_batch(self) -> None:
        artifact = sealed([envelope(1)])
        batch = ingestion_batch(artifact)
        assert batch.batch_id == artifact.artifact_id
        assert batch.envelopes == artifact.envelope_texts
        assert parse_ingestion_batch_document(
            json.loads(json.dumps(ingestion_batch_document(batch)))
        ) == batch


# --- AC3, AC16: strict schema, inspectable rejections -------------------------


class TestStrictIngestion:
    def test_bad_siblings_are_rejected_and_valid_ones_accepted(self, tmp_path) -> None:
        good = canonical_envelope_json(envelope(1))
        unknown_field = good[:-1] + ',"truth":1}'
        bad_unit = canonical_envelope_json(envelope(2, unit="mL"))
        bad_mapping = canonical_envelope_json(replace(envelope(3), mapping_version=2))
        unknown_signal = canonical_envelope_json(
            envelope(4, device="mystery-device", signal="mystery", unit="kW")
        )
        before = canonical_envelope_json(replace(
            envelope(5),
            source_time="2025-12-31T23:59:00Z",
            published_at="2025-12-31T23:59:03Z",
            message_id=envelope_message_id(
                site_id=SITE_ID, gateway_id=GATEWAY, source_id=SOURCE,
                device_id="fuel-level-sensor", signal_id="fuel-level",
                source_time="2025-12-31T23:59:00Z",
            ),
        ))
        good2 = canonical_envelope_json(envelope(6))
        ingestion = service(tmp_path)
        progress = ingestion.ingest(a_batch(
            [good, unknown_field, bad_unit, bad_mapping, unknown_signal, before, good2]
        ))
        assert progress.status == "COMPLETED"
        assert (progress.total, progress.processed, progress.accepted, progress.rejected) == (7, 7, 2, 5)
        rejections = ingestion.store.load_site(SITE_ID).rejections
        assert [(r.index, r.kind) for r in rejections] == [
            (1, "UNKNOWN_FIELD"),
            (2, "UNIT_INCOMPATIBLE"),
            (3, "MAPPING_INCOMPATIBLE"),
            (4, "SIGNAL_NOT_IN_CONFIGURATION"),
            (5, "BEFORE_CONFIGURATION_EFFECTIVE"),
        ]
        assert all(r.detail and r.field for r in rejections)

    @pytest.mark.parametrize("where", ["top", "configuration", "mapping"])
    def test_a_private_object_key_refuses_the_batch_whole(self, where) -> None:
        document = ingestion_batch_document(a_batch(texts(envelope(1))))
        target = document if where == "top" else document[where]
        target["lab_projection"] = {"truth": 1}
        with pytest.raises(IngestionBatchRejected) as refused:
            parse_ingestion_batch_document(document)
        assert refused.value.kind == "UNKNOWN_FIELD"

    def test_an_envelope_given_as_an_object_refuses_the_batch(self) -> None:
        document = ingestion_batch_document(a_batch(texts(envelope(1))))
        document["envelopes"] = [{"observation": {}}]
        with pytest.raises(IngestionBatchRejected):
            parse_ingestion_batch_document(document)


# --- AC4, AC5, AC16 over HTTP --------------------------------------------------


def client_for(tmp_path, sites, clock=None) -> TestClient:
    return TestClient(create_app(
        DISABLED,
        site_repository=sites,
        evidence_store=JsonEvidenceStore(tmp_path / "evidence"),
        clock=clock or Clock(),
    ))


class TestOnePath:
    def test_simulated_and_live_batches_cross_the_same_ingest(self, tmp_path) -> None:
        sim = client_for(tmp_path / "sim", FakeSites((a_site(),)))
        live = client_for(tmp_path / "live", FakeSites((a_site(mode="LIVE"),)))
        artifact_doc = ingestion_batch_document(ingestion_batch(sealed([envelope(1), envelope(2)])))
        live_doc = ingestion_batch_document(
            a_batch(texts(envelope(1), envelope(2)), batch_id="live-1", mode="LIVE")
        )
        a = sim.post("/api/ingestion/batches", json=artifact_doc)
        b = live.post("/api/ingestion/batches", json=live_doc)
        assert a.status_code == b.status_code == 200
        strip = lambda p: {k: v for k, v in p.items() if k not in {"batch_id", "source_mode"}}
        assert strip(a.json()) == strip(b.json())
        record_a = sim.get(f"/api/sites/{SITE_ID}/evidence/records").json()["records"]
        record_b = live.get(f"/api/sites/{SITE_ID}/evidence/records").json()["records"]
        assert record_a == record_b
        message = record_a[0]["message_id"]
        assert sim.get(f"/api/sites/{SITE_ID}/evidence/records/{message}").json()["source_mode"] == "SIMULATED"
        assert live.get(f"/api/sites/{SITE_ID}/evidence/records/{message}").json()["source_mode"] == "LIVE"

    def test_a_source_mode_the_site_does_not_have_is_refused(self, tmp_path) -> None:
        client = client_for(tmp_path, FakeSites((a_site(),)))
        doc = ingestion_batch_document(a_batch(texts(envelope(1)), mode="LIVE"))
        response = client.post("/api/ingestion/batches", json=doc)
        assert response.status_code == 409
        assert response.json()["refusal"]["kind"] == "SOURCE_MODE_MISMATCH"
        assert client.get(f"/api/sites/{SITE_ID}/evidence/records").json()["total"] == 0

    def test_a_private_payload_is_refused_whole_over_http(self, tmp_path) -> None:
        client = client_for(tmp_path, FakeSites((a_site(),)))
        doc = ingestion_batch_document(a_batch(texts(envelope(1))))
        doc["truth"] = {"fuel": 1}
        response = client.post("/api/ingestion/batches", json=doc)
        assert response.status_code == 422
        assert response.json()["detail"]["kind"] == "UNKNOWN_FIELD"
        assert client.get("/api/ingestion/batches/batch-1").status_code == 404
        assert client.get(f"/api/sites/{SITE_ID}/evidence/records").json()["total"] == 0

    def test_received_at_is_ingestions_and_distinct_from_both_source_times(self, tmp_path) -> None:
        client = client_for(tmp_path, FakeSites((a_site(),)))
        delayed = envelope(1, publish_delay=45)
        client.post("/api/ingestion/batches",
                    json=ingestion_batch_document(a_batch(texts(delayed))))
        detail = client.get(
            f"/api/sites/{SITE_ID}/evidence/records/{delayed.message_id}"
        ).json()
        assert detail["source_time"] == "2026-09-22T00:01:00Z"
        assert detail["published_at"] == "2026-09-22T00:01:45Z"
        assert detail["received_at"].startswith("2026-09-23T")
        assert len({detail["source_time"], detail["published_at"], detail["received_at"]}) == 3
        assert detail["normalization"] == "IDENTITY"
        assert detail["original"] == detail["normalized"] == {"value": "100", "unit": "L"}


# --- AC6, AC7: idempotence, conflict, interruption ----------------------------


class TestDurability:
    def test_a_duplicate_after_restart_is_idempotent(self, tmp_path) -> None:
        batch = a_batch(texts(envelope(1), envelope(2)))
        first = service(tmp_path).ingest(batch)
        restarted = service(tmp_path)
        again = restarted.ingest(batch)
        assert again == first
        other_id = restarted.ingest(replace(batch, batch_id="batch-2"))
        assert (other_id.accepted, other_id.duplicates) == (0, 2)
        assert len(restarted.store.load_site(SITE_ID).records) == 2

    def test_same_id_other_content_is_a_conflict_and_the_original_stays(self, tmp_path) -> None:
        original = envelope(1, value="100")
        changed = envelope(1, value="250")
        assert original.message_id == changed.message_id
        ingestion = service(tmp_path)
        ingestion.ingest(a_batch(texts(original)))
        progress = service(tmp_path).ingest(a_batch(texts(changed), batch_id="batch-2"))
        assert (progress.accepted, progress.conflicts) == (0, 1)
        evidence = ingestion.store.load_site(SITE_ID)
        assert [r.original_value for r in evidence.records] == ["100"]
        assert evidence.conflicts[0].message_id == original.message_id
        detail = EvidenceReadModel(ingestion.store).record(SITE_ID, original.message_id)
        assert detail["original"]["value"] == "100" and len(detail["conflicts"]) == 1

    def test_a_reused_batch_id_with_other_content_is_refused(self, tmp_path) -> None:
        ingestion = service(tmp_path)
        first = ingestion.ingest(a_batch(texts(envelope(1))))
        refused = ingestion.ingest(a_batch(texts(envelope(2))))
        assert refused.status == "REFUSED" and refused.refusal_kind == "BATCH_ID_CONFLICT"
        assert EvidenceReadModel(ingestion.store).batch("batch-1")["accepted"] == first.accepted

    def test_an_interrupted_batch_resumes_without_duplicates(self, tmp_path) -> None:
        bad = canonical_envelope_json(envelope(3, unit="mL"))
        batch = a_batch(texts(envelope(1), envelope(2)) + [bad] + texts(envelope(4), envelope(5)))
        crashing = service(tmp_path, chunk_size=2, fail_after=3)
        with pytest.raises(IngestionInterrupted):
            crashing.ingest(batch)
        reloaded = service(tmp_path)
        progress = EvidenceReadModel(reloaded.store).batch("batch-1")
        assert progress["status"] == "IN_PROGRESS"
        assert progress["processed"] == 2 < progress["total"] == 5
        assert len(reloaded.store.load_site(SITE_ID).records) == 2
        done = reloaded.ingest(batch)
        assert done.status == "COMPLETED"
        assert (done.processed, done.accepted, done.rejected, done.duplicates) == (5, 4, 1, 0)
        evidence = reloaded.store.load_site(SITE_ID)
        assert len(evidence.records) == 4 and len(evidence.rejections) == 1


# --- AC8, AC9, AC10: the read model -------------------------------------------


class TestReadModel:
    def test_coverage_reads_accepted_content_only(self, tmp_path) -> None:
        ingestion = service(tmp_path)
        ingestion.ingest(a_batch(texts(envelope(1)) + [canonical_envelope_json(envelope(2, unit="mL"))]))
        ingestion.ingest(a_batch(texts(envelope(1, value="999")), batch_id="batch-2"))
        payload = EvidenceReadModel(ingestion.store).site_evidence(a_site())
        fuel = next(r for r in payload["coverage"] if r["signal_id"] == "fuel-level")
        assert fuel["records"] == 1
        listed = EvidenceReadModel(ingestion.store).records(SITE_ID)["records"]
        assert [r["value"] for r in listed] == ["100"]
        assert payload["rejection_count"] == 1 and payload["conflict_count"] == 1

    def test_distinct_ids_at_the_same_signal_and_time_are_both_kept(self, tmp_path) -> None:
        ingestion = service(tmp_path)
        a = envelope(1, value="100")
        b = envelope(1, value="104", gateway="kobo-gateway-b")
        ingestion.ingest(a_batch(texts(a)))
        ingestion.ingest(a_batch(texts(b), batch_id="batch-b", gateway="kobo-gateway-b"))
        model = EvidenceReadModel(ingestion.store)
        fuel = next(r for r in model.site_evidence(a_site(), "2026-09-22T00:00:00Z",
                                                   "2026-09-22T01:00:00Z")["coverage"]
                    if r["signal_id"] == "fuel-level")
        assert (fuel["records"], fuel["overlapping"]) == (2, 2)
        assert sorted(r["value"] for r in model.records(SITE_ID)["records"]) == ["100", "104"]
        assert model.record(SITE_ID, a.message_id)["overlapping_with"] == [b.message_id]

    def test_coverage_names_needed_signals_and_never_fills_a_gap(self, tmp_path) -> None:
        ingestion = service(tmp_path)
        ingestion.ingest(a_batch(texts(
            envelope(1), envelope(5),
            envelope(2, value=None, device="battery-pcs-controller",
                     signal="state-of-charge", unit="%"),
        )))
        payload = EvidenceReadModel(ingestion.store).site_evidence(a_site())
        rows = {(r["device_id"], r["signal_id"]): r for r in payload["coverage"]}
        fuel = rows[("fuel-level-sensor", "fuel-level")]
        assert (fuel["records"], fuel["longest_silence_seconds"], fuel["needed_by"]) == (2, 240, ["Fuel"])
        soc = rows[("battery-pcs-controller", "state-of-charge")]
        assert (soc["records"], soc["good"], soc["unavailable"]) == (1, 0, 1)
        pv = rows[("pv-inverter-controller", "ac-power")]
        assert pv["status"] == "NOT_REPORTED" and pv["records"] == 0
        assert pv["first_source_time"] is None and pv["needed_by"] == ["Renewable"]
        assert "value" not in pv
        assert {r["needed_by"][0] for r in payload["coverage"] if r["needed_by"]} == {
            "Service", "Dispatch", "Battery", "Fuel", "Renewable"}
        unavailable = EvidenceReadModel(ingestion.store).records(
            SITE_ID, signal_id="state-of-charge")["records"][0]
        assert unavailable["value"] is None and unavailable["quality"] == "UNAVAILABLE"


# --- AC17: Foundation edits do not rewrite history ----------------------------


class TestConfigurationBasis:
    def test_a_foundation_edit_leaves_accepted_basis_unchanged(self, tmp_path) -> None:
        store_root = tmp_path
        service(store_root).ingest(a_batch(texts(envelope(1))))
        edited = a_site(version=2, site_devices=(
            FoundationDevice("fuel-level-sensor", "SENSOR", "Fuel level", "fuel-tank",
                             (DeviceSignal("fuel-level", "Fuel level", "m3"),)),
        ))
        later = service(store_root, sites=FakeSites((edited,)))
        progress = later.ingest(a_batch(texts(envelope(2)), batch_id="batch-2"))
        assert progress.accepted == 1
        model = EvidenceReadModel(later.store)
        records = later.store.load_site(SITE_ID).records
        assert {r.foundation_version for r in records} == {1}
        basis = later.store.get_configuration(SITE_ID, 1)
        assert basis.signal("fuel-level-sensor", "fuel-level").unit == "L"
        payload = model.site_evidence(edited)
        assert payload["basis"]["configurations"][0]["foundation_version"] == 1
        assert payload["basis"]["current_foundation"]["foundation_version"] == 2

    def test_an_unregistered_older_version_is_unresolved(self, tmp_path) -> None:
        current = a_site(version=3)
        progress = service(tmp_path, sites=FakeSites((current,))).ingest(
            a_batch(texts(envelope(1)), version=2)
        )
        assert progress.status == "REFUSED"
        assert progress.refusal_kind == "CONFIGURATION_UNRESOLVED"


# --- AC13, AC19: gate closed ---------------------------------------------------


class TestGateClosed:
    def test_evidence_routes_are_served_and_lab_routes_are_not(self, tmp_path) -> None:
        client = client_for(tmp_path, FakeSites((a_site(),)))
        client.post("/api/ingestion/batches",
                    json=ingestion_batch_document(a_batch(texts(envelope(1)))))
        assert client.get(f"/api/sites/{SITE_ID}/evidence").status_code == 200
        assert client.get(f"/api/sites/{SITE_ID}/evidence/records").json()["total"] == 1
        assert client.get(f"/api/sites/{SITE_ID}/evidence/rejections").status_code == 200
        assert client.get("/api/ingestion/batches/batch-1").json()["status"] == "COMPLETED"
        paths = served_paths(client.app)
        assert f"/api/sites/{{site_id}}/evidence" in paths
        assert not any("simulator-lab" in path for path in paths)
        assert client.get("/api/simulator-lab/runs").status_code == 404


# --- AC14: rebuild from committed artifacts alone -----------------------------


def _without_audit_times(value: Any) -> Any:
    audit = {"received_at", "last_received_at", "started_at", "completed_at"}
    if isinstance(value, dict):
        return {k: _without_audit_times(v) for k, v in value.items() if k not in audit}
    if isinstance(value, list):
        return [_without_audit_times(v) for v in value]
    return value


class TestRebuild:
    def test_rebuild_from_artifact_texts_matches_the_original(self, tmp_path) -> None:
        artifacts = [
            artifact_text(sealed([envelope(1), envelope(2),
                                  envelope(3, value=None)], run_id="run-1")),
            artifact_text(sealed([envelope(4), envelope(5)], run_id="run-2")),
        ]
        ingestion = service(tmp_path)
        for text in artifacts:
            ingestion.ingest(ingestion_batch(parse_artifact_text(text)))
        model = EvidenceReadModel(ingestion.store)

        def snapshot():
            records = model.records(SITE_ID)
            return {
                "evidence": model.site_evidence(a_site()),
                "records": records,
                "details": [model.record(SITE_ID, r["message_id"]) for r in records["records"]],
            }

        before = snapshot()
        ingestion.store.clear_derived()
        assert model.records(SITE_ID)["total"] == 0
        rebuilt = service(tmp_path)
        for text in artifacts:
            rebuilt.ingest(ingestion_batch(parse_artifact_text(text)))
        after = snapshot()
        assert after["records"]["total"] == 5
        assert _without_audit_times(after) == _without_audit_times(before)
