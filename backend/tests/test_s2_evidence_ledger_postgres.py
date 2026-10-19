"""S2-02 phase 1: central evidence ledger and Batch V2 decision engine over PostgreSQL.

Covers AC1 (injected principal, scope/enablement on every upload, no Site row on
an authentication/authorization failure), AC2 (immutable batch, per-ordinal
decisions, duplicate/conflict, crash/resume, 202, concurrency), AC3 (accepted-as
validation, normalization, superseded configuration, closing boundary) and AC4
(identity hardening). Requires ASSETOPS_TEST_DATABASE_URL (see backend/README-db.md).
"""

from __future__ import annotations

import json
import os
import threading
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)"
)

if URL:
    from fastapi.testclient import TestClient
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError
    from test_s1_bindings_postgres import CHANGE_FROM, NOW, Clock, converted, engine, store  # noqa: F401
    from test_s2_registered_basis_postgres import publish_reserve

    from assetops_backend.evidence.adapters.postgres_evidence_ledger import PostgresEvidenceLedger
    from assetops_backend.evidence.ledger import GatewayPrincipal, PrincipalRefused
    from assetops_backend.evidence.ledger_service import (
        BatchIngestionService,
        BatchRefused,
        SimulatedCrash,
    )
    from assetops_backend.evidence_api import build_evidence_router
    from assetops_contracts.ingestion_batch_v2 import seal_batch_v2
    from assetops_contracts.ingestion_receipt_v2 import (
        canonical_receipt_v2_text,
        parse_canonical_receipt_v2_text,
    )
    from assetops_contracts.source_envelope_v3 import (
        SourceEnvelopeV3,
        canonical_envelope_v3_text,
        v3_message_id,
    )

RECEIVED = datetime(2026, 10, 9, 8, 30, 0, 123456, tzinfo=timezone.utc)
LEDGER_TABLES = (
    "ingestion_batch", "accepted_evidence", "evidence_rejection",
    "ingestion_disposition", "batch_refusal", "recompute_job",
)


def _z(instant: datetime) -> str:
    return instant.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class Kit:
    """One converted Kobo Site with a parsed pinned snapshot and a principal from its registration."""

    def __init__(self, engine, set_revision_id) -> None:
        with engine.connect() as connection:
            body = bytes(connection.execute(
                text("SELECT snapshot_canonical FROM signal_binding_set_revision WHERE id = :id"),
                {"id": set_revision_id},
            ).scalar_one())
        self.doc = json.loads(body)
        self.sha = __import__("hashlib").sha256(body).hexdigest()
        self.engine = engine
        self.principal = GatewayPrincipal(
            tenant_id=UUID(self.doc["tenant_id"]),
            site_id=UUID(self.doc["site"]["site_id"]),
            gateway_id=UUID(self.doc["gateway"]["gateway_id"]),
            mode=self.doc["gateway"]["mode"],
        )
        self.start = datetime.fromisoformat(self.doc["mapping"]["valid_from"].replace("Z", "+00:00"))

    def binding(self, device_id: str, signal_id: str | None = None) -> dict:
        return next(b for b in self.doc["bindings"]
                    if b["device_id"] == device_id and signal_id in (None, b["signal_id"]))

    def envelope(self, device_id, seq, minutes, value, *, signal_id=None, unit=None, epoch="epoch-1",
                 source_time=None, published=None, version=None, bound_signal=None) -> str:
        b = self.binding(device_id, bound_signal)
        source = source_time or _z(self.start + timedelta(minutes=minutes))
        e = SourceEnvelopeV3(
            message_id=v3_message_id(site_id=self.doc["site"]["site_id"], gateway_id=b["gateway_id"],
                                     source_id=b["source_id"], sequence_epoch=epoch, sequence=seq),
            sequence_epoch=epoch, sequence=seq,
            site_id=self.doc["site"]["site_id"], gateway_id=b["gateway_id"], source_id=b["source_id"],
            device_id=device_id, signal_id=signal_id or b["signal_id"],
            binding_set_id=self.doc["mapping"]["binding_set_id"], binding_version=version or self.doc["mapping"]["version"],
            source_time=source, published_at=published or source, interval_start=None, interval_end=None,
            family="MEASUREMENT", measurement="STATE_AT_INSTANT", value=value,
            unit=unit or b["source_unit"], quality="GOOD", unavailable_reason=None,
        )
        return canonical_envelope_v3_text(e)

    def seal(self, texts, *, device_id="pv-inverter-controller", mode=None, valid_from=None,
             version=None, source_id=None) -> str:
        b = self.binding(device_id)
        _, body = seal_batch_v2(
            site_id=self.doc["site"]["site_id"], gateway_id=b["gateway_id"],
            source_id=source_id or b["source_id"], source_mode=mode or self.doc["gateway"]["mode"],
            foundation_version=self.doc["foundation"]["version"],
            foundation_valid_from=valid_from or self.doc["foundation"]["valid_from"],
            binding_set_id=self.doc["mapping"]["binding_set_id"],
            binding_version=version or self.doc["mapping"]["version"],
            snapshot_sha256=self.sha, envelope_texts=texts,
        )
        return body

    def pv(self, count, *, first=1, value="1.5") -> list[str]:
        return [self.envelope("pv-inverter-controller", first + i, i, value) for i in range(count)]

    def counts(self) -> dict[str, int]:
        with self.engine.connect() as connection:
            return {t: connection.execute(text(f"SELECT count(*) FROM {t}")).scalar_one() for t in LEDGER_TABLES}


def ingestion(**options) -> BatchIngestionService:
    # S4-07: decisions take DB time in production; these fixtures pin them through the test-only override.
    return BatchIngestionService(PostgresEvidenceLedger(URL, test_decision_clock_override=Clock(RECEIVED)),
                                 Clock(RECEIVED), **options)


def enable(engine, site_id) -> None:
    """Import registers the gateway and sources disabled until a credential is provisioned
    (phase 2). Stand in for provisioning here; phase 1 tests inject the principal."""
    with engine.begin() as connection:
        connection.execute(text("UPDATE gateway SET disabled_at = NULL WHERE site_id = :s"), {"s": site_id})
        connection.execute(text("UPDATE source SET disabled_at = NULL WHERE site_id = :s"), {"s": site_id})


def converted_enabled(store, engine):
    result, outcome = converted(store)
    enable(engine, result.site.id)
    return result, outcome


@pytest.fixture()
def kit(store, engine):
    _, outcome = converted_enabled(store, engine)
    return Kit(engine, outcome.published.changed.id)


def submit(kit, body: str, **options):
    return ingestion(**options).submit(kit.principal, body.encode("utf-8"))


class TestAcceptedEvidence:
    def test_a_batch_is_decided_per_ordinal_normalized_and_receipted(self, kit, engine) -> None:
        body = kit.seal(kit.pv(3))
        answer = submit(kit, body)
        r = answer.receipt
        assert answer.status == 200 and r.status == "COMPLETED"
        assert (r.counts.total, r.counts.accepted, r.received_at) == (3, 3, "2026-10-09T08:30:00.123456Z")
        assert [d.decision for d in r.dispositions] == ["ACCEPTED"] * 3
        # The receipt text round-trips through the strict parser with its digest.
        assert parse_canonical_receipt_v2_text(canonical_receipt_v2_text(r)) == r
        with engine.connect() as connection:
            row = connection.execute(text(
                "SELECT e.*, b.external_batch_id FROM accepted_evidence e JOIN ingestion_batch b ON b.id = e.batch_id "
                "WHERE e.id = :id"), {"id": r.dispositions[0].evidence_id}).mappings().one()
            job = connection.execute(text("SELECT * FROM recompute_job")).mappings().all()
        binding = kit.binding("pv-inverter-controller")
        assert row["original_value_text"] == "1.5" and row["normalized_value_text"] == "1.5"
        assert (row["original_unit"], row["normalized_unit"], row["conversion_kind"]) == ("kW", "kW", "IDENTITY")
        assert str(row["binding_revision_id"]) == binding["binding_revision_id"]
        assert str(row["foundation_revision_id"]) == kit.doc["foundation"]["revision_id"]
        assert row["asset_id"] is not None and str(row["asset_id"]) == binding["asset_id"]
        assert row["received_at"] == RECEIVED and row["configuration_outdated"] is False
        assert row["source_mode"] == "SIMULATED" and row["envelope_text"] == json.loads(body)["envelopes"][0]
        assert len(job) == 1 and job[0]["status"] == "PENDING" and job[0]["domain"] == "dispatch"
        assert job[0]["window_start"] == kit.start and job[0]["window_end"] > kit.start + timedelta(minutes=2)

    def test_enum_status_uses_the_registered_map_and_rejects_an_unmapped_label(self, kit, engine) -> None:
        texts = [
            kit.envelope("generator-controller", 1, 0, "RUNNING", bound_signal="status"),
            kit.envelope("generator-controller", 2, 1, "IDLE", bound_signal="status"),
        ]
        r = submit(kit, kit.seal(texts, device_id="generator-controller")).receipt
        assert [d.decision for d in r.dispositions] == ["ACCEPTED", "REJECTED"]
        assert (r.dispositions[1].rejection.kind, r.dispositions[1].rejection.field) == ("INVALID_ENUM", "payload.value")
        with engine.connect() as connection:
            row = connection.execute(text("SELECT normalized_value_text, conversion_kind, role FROM accepted_evidence")).one()
        assert tuple(row) == ("RUNNING", "ENUM", "generator_state")

    def test_a_rejected_sibling_does_not_erase_valid_decisions(self, kit) -> None:
        texts = [
            kit.envelope("pv-inverter-controller", 1, 0, "1"),
            kit.envelope("pv-inverter-controller", 2, 1, "2", signal_id="unbound-signal"),
            kit.envelope("pv-inverter-controller", 3, 2, "3", source_time=_z(kit.start - timedelta(hours=1))),
            kit.envelope("pv-inverter-controller", 4, 3, "4"),
        ]
        r = submit(kit, kit.seal(texts)).receipt
        assert [d.decision for d in r.dispositions] == ["ACCEPTED", "REJECTED", "REJECTED", "ACCEPTED"]
        assert [d.rejection.kind for d in r.dispositions if d.rejection] == [
            "BINDING_NOT_REGISTERED", "OUTSIDE_FOUNDATION_PERIOD"]
        assert (r.counts.accepted, r.counts.rejected) == (2, 2)

    def test_virtual_published_time_is_kept_and_received_is_server_time(self, kit, engine) -> None:
        later = _z(kit.start + timedelta(minutes=25))
        text_ = kit.envelope("pv-inverter-controller", 1, 0, "1", published=later)
        submit(kit, kit.seal([text_]))
        with engine.connect() as connection:
            row = connection.execute(text("SELECT source_time, published_at, received_at FROM accepted_evidence")).one()
        assert row.source_time == kit.start and row.published_at == kit.start + timedelta(minutes=25)
        assert row.received_at == RECEIVED


class TestRetryDuplicateConflict:
    def test_identical_retry_returns_the_durable_receipt_and_writes_nothing(self, kit) -> None:
        body = kit.seal(kit.pv(3))
        first = submit(kit, body)
        before = kit.counts()
        again = ingestion().submit(kit.principal, body.encode())
        assert canonical_receipt_v2_text(again.receipt) == canonical_receipt_v2_text(first.receipt)
        assert kit.counts() == before

    def test_same_batch_id_with_changed_bytes_is_409_and_the_stored_batch_is_untouched(self, kit, engine) -> None:
        body = kit.seal(kit.pv(2))
        first = submit(kit, body).receipt
        changed = kit.seal(kit.pv(2, value="9.9"))
        assert json.loads(changed)["batch_id"] == json.loads(body)["batch_id"] and changed != body
        with pytest.raises(BatchRefused) as refused:
            submit(kit, changed)
        assert (refused.value.status, refused.value.kind) == (409, "BATCH_ID_CONFLICT")
        assert canonical_receipt_v2_text(ingestion().receipt(kit.principal, first.batch_id)) == \
            canonical_receipt_v2_text(first)
        with engine.connect() as connection:
            assert connection.execute(text("SELECT count(*) FROM batch_refusal WHERE kind = 'BATCH_ID_CONFLICT'")).scalar_one() == 1
            assert connection.execute(text("SELECT normalized_value_text FROM accepted_evidence")).scalars().all() == ["1.5", "1.5"]

    def test_a_redelivered_message_is_duplicate_and_changed_bytes_are_a_conflict(self, kit, engine) -> None:
        first = submit(kit, kit.seal(kit.pv(2))).receipt
        # A different batch (different count) carrying message 1 again unchanged, plus message 3.
        dup = submit(kit, kit.seal([kit.pv(1)[0], kit.envelope("pv-inverter-controller", 3, 2, "1.5")])).receipt
        assert [d.decision for d in dup.dispositions] == ["DUPLICATE", "ACCEPTED"]
        assert dup.dispositions[0].evidence_id == first.dispositions[0].evidence_id
        # Message 2 with different bytes in a third batch.
        conflict = submit(kit, kit.seal([kit.envelope("pv-inverter-controller", 2, 1, "7")])).receipt
        d = conflict.dispositions[0]
        assert d.decision == "CONFLICT" and d.rejection.kind == "MESSAGE_CONFLICT"
        assert d.rejection.conflicts_with_evidence_id == first.dispositions[1].evidence_id
        with engine.connect() as connection:
            values = connection.execute(text("SELECT normalized_value_text FROM accepted_evidence ORDER BY sequence")).scalars().all()
        assert values == ["1.5", "1.5", "1.5"]  # the original is preserved

    def test_two_same_timestamp_readings_with_different_sequences_are_both_accepted(self, kit) -> None:
        same = _z(kit.start)
        texts = [kit.envelope("pv-inverter-controller", s, 0, v, source_time=same) for s, v in ((1, "1"), (2, "2"))]
        r = submit(kit, kit.seal(texts)).receipt
        assert [d.decision for d in r.dispositions] == ["ACCEPTED", "ACCEPTED"]


class TestCrashAndResume:
    def test_a_crash_after_a_committed_chunk_resumes_from_the_watermark(self, kit) -> None:
        body = kit.seal(kit.pv(5))
        with pytest.raises(SimulatedCrash):
            submit(kit, body, chunk_size=2, crash_after_chunks=1)
        partial = ingestion().receipt(kit.principal, json.loads(body)["batch_id"])
        assert (partial.status, partial.counts.processed, partial.completed_at) == ("IN_PROGRESS", 2, None)
        resumed = submit(kit, body, chunk_size=2)
        assert resumed.status == 200 and resumed.receipt.counts.accepted == 5
        assert resumed.receipt.dispositions[:2] == partial.dispositions
        assert kit.counts()["ingestion_disposition"] == 5 and kit.counts()["accepted_evidence"] == 5

    def test_a_bounded_request_returns_202_in_progress_until_terminal(self, kit) -> None:
        body = kit.seal(kit.pv(5))
        step = submit(kit, body, chunk_size=2, max_chunks_per_request=1)
        assert step.status == 202 and step.receipt.status == "IN_PROGRESS" and step.receipt.counts.processed == 2
        step = submit(kit, body, chunk_size=2, max_chunks_per_request=1)
        assert (step.status, step.receipt.counts.processed) == (202, 4)
        step = submit(kit, body, chunk_size=2, max_chunks_per_request=1)
        assert (step.status, step.receipt.status) == (200, "COMPLETED")

    def test_concurrent_deliveries_decide_each_ordinal_and_message_once(self, kit) -> None:
        body = kit.seal(kit.pv(6))
        other = kit.seal([kit.pv(1)[0], kit.envelope("pv-inverter-controller", 7, 6, "1.5")])
        results, errors = [], []

        def run(payload):
            try:
                results.append(ingestion(chunk_size=1).submit(kit.principal, payload.encode()))
            except Exception as error:  # pragma: no cover - reported below
                errors.append(error)

        threads = [threading.Thread(target=run, args=(p,)) for p in (body, body, other, body)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert not errors
        assert kit.counts()["ingestion_batch"] == 2 and kit.counts()["accepted_evidence"] == 7
        assert kit.counts()["ingestion_disposition"] == 8
        decisions = sorted(d.decision for r in results if r.receipt.counts.total == 2 for d in r.receipt.dispositions)
        assert decisions in (["ACCEPTED", "DUPLICATE"], ["ACCEPTED", "ACCEPTED"])
        receipts = {canonical_receipt_v2_text(r.receipt) for r in results if r.receipt.counts.total == 6}
        assert len(receipts) == 1


class TestScopeAndRefusals:
    def _no_rows(self, kit) -> None:
        assert kit.counts() == {t: 0 for t in LEDGER_TABLES}

    def test_a_cross_site_principal_or_wrong_mode_is_403_without_a_ledger_row(self, kit) -> None:
        body = kit.seal(kit.pv(1)).encode()
        for principal, kind in (
            (replace(kit.principal, site_id=uuid4()), "SCOPE_MISMATCH"),
            (replace(kit.principal, gateway_id=uuid4()), "SCOPE_MISMATCH"),
            (replace(kit.principal, mode="LIVE"), "MODE_MISMATCH"),
        ):
            with pytest.raises(BatchRefused) as refused:
                ingestion().submit(principal, body)
            assert (refused.value.status, refused.value.kind) == (403, kind)
        self._no_rows(kit)

    def test_an_unaffiliated_source_is_403_without_a_ledger_row(self, kit) -> None:
        stranger = str(uuid4())
        b = kit.binding("pv-inverter-controller")
        e = SourceEnvelopeV3(
            message_id=v3_message_id(site_id=kit.doc["site"]["site_id"], gateway_id=b["gateway_id"],
                                     source_id=stranger, sequence_epoch="epoch-1", sequence=1),
            sequence_epoch="epoch-1", sequence=1, site_id=kit.doc["site"]["site_id"], gateway_id=b["gateway_id"],
            source_id=stranger, device_id="pv-inverter-controller", signal_id="ac-power",
            binding_set_id=kit.doc["mapping"]["binding_set_id"], binding_version=kit.doc["mapping"]["version"],
            source_time=_z(kit.start), published_at=_z(kit.start), interval_start=None, interval_end=None,
            family="MEASUREMENT", measurement="STATE_AT_INSTANT", value="1", unit="kW", quality="GOOD",
            unavailable_reason=None,
        )
        with pytest.raises(BatchRefused) as refused:
            submit(kit, kit.seal([canonical_envelope_v3_text(e)], source_id=stranger))
        assert (refused.value.status, refused.value.kind) == (403, "SOURCE_NOT_AFFILIATED")
        self._no_rows(kit)

    def test_disable_takes_effect_on_the_next_request_including_identical_retries(self, kit, engine) -> None:
        body = kit.seal(kit.pv(1))
        submit(kit, body)
        before = kit.counts()
        source_id = kit.binding("pv-inverter-controller")["source_id"]
        with engine.begin() as connection:
            connection.execute(text("UPDATE source SET disabled_at = :now WHERE id = :s"), {"now": NOW, "s": source_id})
        with pytest.raises(BatchRefused) as refused:
            submit(kit, body)
        assert (refused.value.status, refused.value.kind) == (403, "SOURCE_DISABLED")
        with engine.begin() as connection:
            connection.execute(text("UPDATE source SET disabled_at = NULL WHERE id = :s"), {"s": source_id})
            connection.execute(text("UPDATE gateway SET disabled_at = :now WHERE id = :g"),
                               {"now": NOW, "g": kit.principal.gateway_id})
        with pytest.raises(BatchRefused) as refused:
            submit(kit, body)
        assert (refused.value.status, refused.value.kind) == (403, "GATEWAY_DISABLED")
        assert kit.counts() == before

    def test_malformed_and_unregistered_configuration_are_whole_batch_refusals(self, kit) -> None:
        cases = [
            (b"{not json", 422, "MALFORMED_TEXT"),
            (kit.seal([kit.envelope("pv-inverter-controller", 1, 0, "1", version=99)], version=99).encode(),
             422, "CONFIGURATION_UNREGISTERED"),
            (kit.seal(kit.pv(1), valid_from=kit.doc["foundation"]["valid_from"].replace("Z", ".0Z")).encode(),
             422, "CONFIGURATION_MISMATCH"),
        ]
        for raw, status, kind in cases:
            with pytest.raises(BatchRefused) as refused:
                ingestion().submit(kit.principal, raw)
            assert (refused.value.status, refused.value.kind) == (status, kind)
            assert refused.value.refusal_id is not None
        counts = kit.counts()
        assert counts["batch_refusal"] == 3 and counts["ingestion_batch"] == 0
        # The same refusal again is the same row.
        with pytest.raises(BatchRefused) as again:
            ingestion().submit(kit.principal, cases[0][0])
        assert kit.counts()["batch_refusal"] == 3 and again.value.refusal_id is not None

    def test_an_oversized_body_is_refused_before_parsing(self, kit) -> None:
        with pytest.raises(BatchRefused) as refused:
            ingestion().submit(kit.principal, b" " * (1_048_576 + 1))
        assert (refused.value.status, refused.value.kind) == (413, "TOO_LARGE")


class TestAcceptedAsConfiguration:
    def test_a_superseded_original_pair_is_accepted_with_an_outdated_flag(self, store, engine) -> None:
        result, outcome = converted_enabled(store, engine)
        kit = Kit(engine, outcome.published.changed.id)
        publish_reserve(store, result)  # supersedes the original Foundation/binding pair at CHANGE_FROM
        after = kit.envelope("pv-inverter-controller", 1, 0, "2", source_time=_z(CHANGE_FROM + timedelta(hours=1)))
        r = submit(kit, kit.seal([after])).receipt
        assert r.dispositions[0].decision == "ACCEPTED"
        with engine.connect() as connection:
            row = connection.execute(text(
                "SELECT foundation_revision_id, configuration_outdated FROM accepted_evidence")).one()
        assert str(row.foundation_revision_id) == kit.doc["foundation"]["revision_id"] and row.configuration_outdated

    def test_a_closing_boundary_reading_is_outside_its_half_open_period(self, store, engine) -> None:
        result, _ = converted_enabled(store, engine)
        publish_reserve(store, result)
        with engine.connect() as connection:
            earlier = connection.execute(text(
                "SELECT id FROM signal_binding_set_revision WHERE superseded_at IS NULL AND valid_to = :to"),
                {"to": CHANGE_FROM}).scalar_one()
        kit = Kit(engine, earlier)
        boundary = kit.envelope("pv-inverter-controller", 1, 0, "2", source_time=_z(CHANGE_FROM))
        inside = kit.envelope("pv-inverter-controller", 2, 0, "2", source_time=_z(CHANGE_FROM - timedelta(minutes=10)))
        r = submit(kit, kit.seal([boundary, inside])).receipt
        assert [d.decision for d in r.dispositions] == ["REJECTED", "ACCEPTED"]
        assert r.dispositions[0].rejection.kind == "OUTSIDE_FOUNDATION_PERIOD"


class TestIdentityHardening:
    def test_asset_code_is_immutable_and_the_binding_asset_resolves_to_its_foundation_component(self, kit, engine) -> None:
        binding = kit.binding("pv-inverter-controller")
        with pytest.raises(DBAPIError, match="asset identity is immutable"):
            with engine.begin() as connection:
                connection.execute(text("UPDATE asset SET asset_code = 'renamed' WHERE id = :a"), {"a": binding["asset_id"]})
        with engine.connect() as connection:
            code = connection.execute(text(
                "SELECT a.asset_code FROM asset a JOIN foundation_revision f ON f.site_id = a.site_id "
                "WHERE a.id = :a AND f.id = :f AND EXISTS (SELECT 1 FROM jsonb_array_elements(f.content->'components') c "
                "WHERE c->>'component_id' = a.asset_code)"),
                {"a": binding["asset_id"], "f": kit.doc["foundation"]["revision_id"]}).scalar_one()
        assert code == "pv-inverter"

    def test_migration_0005_refuses_to_freeze_a_drifted_asset_code(self, kit, engine) -> None:
        from alembic import command
        from test_s1_bindings_postgres import _alembic

        asset_id = kit.binding("pv-inverter-controller")["asset_id"]
        config = _alembic()
        try:
            command.downgrade(config, "0004_snapshot_canonical_bytes")
            with engine.begin() as connection:
                connection.execute(text("UPDATE asset SET asset_code = 'drifted' WHERE id = :a"), {"a": asset_id})
            with pytest.raises(RuntimeError, match="refuses to freeze asset identity over drifted rows"):
                command.upgrade(config, "head")
            with engine.begin() as connection:
                connection.execute(text("UPDATE asset SET asset_code = 'pv-inverter' WHERE id = :a"), {"a": asset_id})
        finally:
            command.upgrade(config, "head")
        with engine.connect() as connection:
            assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == "0024_w2_ev_config"

    def test_registration_affiliation_and_mode_are_immutable(self, kit, engine) -> None:
        source_id = kit.binding("pv-inverter-controller")["source_id"]
        for sql, message in (
            ("UPDATE gateway SET mode = 'LIVE' WHERE id = :g", "gateway registration is immutable"),
            ("UPDATE source SET gateway_id = gen_random_uuid() WHERE id = :s", "source registration is immutable"),
        ):
            with pytest.raises(DBAPIError, match=message):
                with engine.begin() as connection:
                    connection.execute(text(sql), {"g": kit.principal.gateway_id, "s": source_id})

    def test_site_type_is_fixed_and_ledger_rows_are_append_only_once_evidence_exists(self, kit, engine) -> None:
        with engine.begin() as connection:  # allowed before any evidence
            connection.execute(text("UPDATE site SET site_type = 'MINIGRID' WHERE id = :s"), {"s": kit.principal.site_id})
        submit(kit, kit.seal(kit.pv(1)))
        for sql, message in (
            ("UPDATE site SET site_type = 'COLDCHAIN' WHERE id = :s", "Site type is fixed"),
            ("UPDATE accepted_evidence SET normalized_value_text = '0'", "append-only"),
            ("DELETE FROM ingestion_disposition", "append-only"),
            ("UPDATE ingestion_batch SET batch_text = 'x'", "immutable"),
        ):
            with pytest.raises(DBAPIError, match=message):
                with engine.begin() as connection:
                    connection.execute(text(sql), {"s": kit.principal.site_id})


class FixedPrincipals:
    def __init__(self, principal) -> None:
        self.principal = principal

    def resolve(self, authorization):
        if authorization != "Bearer test-token":
            raise PrincipalRefused(401, "GATEWAY_CREDENTIAL_INVALID", "unknown credential")
        return self.principal


class TestHttpBoundary:
    def _client(self, principals=None):
        from fastapi import FastAPI

        from assetops_backend.evidence.service import IngestionService

        class _NoSites:
            def get_site(self, site_id):  # pragma: no cover - V2 never reads YAML Sites
                raise AssertionError

        app = FastAPI()
        app.include_router(build_evidence_router(
            IngestionService(None, _NoSites()),  # type: ignore[arg-type]
            _NoSites(),  # type: ignore[arg-type]
            batch_ingestion=ingestion(),
            gateway_principals=principals,
        ))
        return TestClient(app)

    def test_network_upload_is_closed_by_default_and_needs_a_credential(self, kit) -> None:
        body = kit.seal(kit.pv(1))
        closed = self._client().post("/api/ingestion/batches", content=body, headers={"Authorization": "Bearer x"})
        assert closed.status_code == 401 and closed.json()["detail"]["code"] == "GATEWAY_UPLOAD_CLOSED"
        anonymous = self._client().post("/api/ingestion/batches", content=body)
        assert anonymous.status_code == 401 and anonymous.json()["detail"]["code"] == "GATEWAY_CREDENTIAL_REQUIRED"
        wrong = self._client(FixedPrincipals(kit.principal)).post(
            "/api/ingestion/batches", content=body, headers={"Authorization": "Bearer nope"})
        assert wrong.status_code == 401
        assert kit.counts() == {t: 0 for t in LEDGER_TABLES}

    def test_an_injected_principal_posts_and_reads_the_exact_receipt(self, kit) -> None:
        client = self._client(FixedPrincipals(kit.principal))
        auth = {"Authorization": "Bearer test-token"}
        body = kit.seal(kit.pv(2))
        posted = client.post("/api/ingestion/batches", content=body, headers=auth)
        assert posted.status_code == 200
        receipt = parse_canonical_receipt_v2_text(posted.text)
        read = client.get(f"/api/ingestion/batches/{receipt.batch_id}", headers=auth)
        assert read.status_code == 200 and read.text == posted.text
        changed = kit.seal(kit.pv(2, value="3"))
        assert client.post("/api/ingestion/batches", content=changed, headers=auth).status_code == 409
        assert client.post("/api/ingestion/batches", content="{}", headers=auth).status_code == 422
        assert client.get("/api/ingestion/batches/unknown", headers=auth).status_code == 404


class TestIdentityKwhNormalization:
    """W2-05b q3 Q17: `_normalize` passes the canonical kWh decimal through as `IDENTITY_KWH` only for the
    selected `ev_connector_energy` kWh-to-kWh binding with empty parameters; every other shape refuses."""

    @staticmethod
    def _energy(**changes):
        from assetops_backend.evidence.ledger import BindingBasis

        basis = BindingBasis(
            binding_revision_id=uuid4(), device_id="c1-connector-meter", signal_id="energy", source_id="src",
            asset_id=uuid4(), role="ev_connector_energy", source_unit="kWh", canonical_unit="kWh",
            conversion={"kind": "IDENTITY_KWH", "parameters": {}}, asset_code="c1",
        )
        return replace(basis, **changes)

    def test_the_one_shape_is_an_unchanged_passthrough(self) -> None:
        from assetops_backend.evidence.ledger import _normalize

        assert _normalize(self._energy(), "0.125") == ("0.125", "IDENTITY_KWH", None)
        assert _normalize(self._energy(), "15") == ("15", "IDENTITY_KWH", None)

    @pytest.mark.parametrize("changes,value", [
        ({"role": "ev_connector_power"}, "1"),
        ({"source_unit": "Wh"}, "1"),
        ({"canonical_unit": "MWh"}, "1"),
        ({"conversion": {"kind": "IDENTITY_KWH", "parameters": {"scale": "1"}}}, "1"),
        ({"conversion": {"kind": "IDENTITY_KWH"}}, "1"),
        ({}, "0.1250"),
        ({}, "1e3"),
    ])
    def test_a_foreign_or_malformed_use_refuses(self, changes, value) -> None:
        from assetops_backend.evidence.ledger import _normalize

        assert _normalize(self._energy(**changes), value) == (None, "IDENTITY_KWH", "CONVERSION_UNSUPPORTED")

    def test_older_conversions_are_unchanged(self) -> None:
        from assetops_backend.evidence.ledger import _normalize

        identity = self._energy(role="pv_power", source_unit="kW", canonical_unit="kW",
                                conversion={"kind": "IDENTITY", "parameters": {}})
        assert _normalize(identity, "1.5") == ("1.5", "IDENTITY", None)
        assert _normalize(self._energy(conversion={"kind": "SCALE", "parameters": {}}), "1") == (
            None, "SCALE", "CONVERSION_UNSUPPORTED")
