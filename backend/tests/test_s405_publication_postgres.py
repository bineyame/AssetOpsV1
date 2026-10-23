"""S4-05a phase 1: immutable pre-admission source publication and batch binding over PostgreSQL.

`D-2026-10-15-s405-stored-demo-provenance`; `.agent/architect-S4-05-answers.md` Q1, rule 8, Follow-up M1.
Covers authored and registered-run positive paths, server SYSTEM authority, scope refusals (two tenants, wrong
Site/gateway/source/digest, LIVE, manifest-only), identical retry and conflicting reuse, refusal after partial
admission, the shared slot lock (registration/upload race), commitment mismatch at upload, chunk restart,
duplicate/rejected/conflict inheritance, direct-SQL immutability/uniqueness/scoped FKs, and the open_batch
lock-cost measurement. Requires ASSETOPS_TEST_DATABASE_URL (see backend/TESTING.md).
"""

from __future__ import annotations

import json
import os
import statistics
import threading
import time
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)"
)

if URL:
    from sqlalchemy import create_engine, text
    from sqlalchemy.exc import DBAPIError, IntegrityError
    from test_s1_bindings_postgres import BACKEND, KOBO_SOURCE, NOW, Clock, engine, store  # noqa: F401
    from test_s2_evidence_ledger_postgres import RECEIVED, Kit, converted_enabled
    from test_s2_registered_basis_postgres import service as run_setup
    from test_s2_registered_basis import request as run_request

    from assetops_backend.evidence.adapters.authored_fixture_specs import AuthoredFixtureSpecs
    from assetops_backend.evidence.adapters.postgres_evidence_ledger import (
        PostgresEvidenceLedger,
        admission_lock_key,
    )
    from assetops_backend.evidence.ledger_service import BatchIngestionService, BatchRefused, SimulatedCrash
    from assetops_backend.evidence.publication import (
        AUTHORED_DEMONSTRATION,
        FIXTURE_PUBLISHER,
        REGISTERED_SIMULATION,
        PublicationAuthority,
        PublicationRecord,
        PublicationRefused,
        authored_record,
        register_authored,
        register_run,
        simulation_records,
    )
    from assetops_backend.publish_source import main as publish_source_main
    from assetops_backend.runs.adapters.yaml_run_store import YamlRunStore
    from assetops_backend.runs.source_publication import run_attestation, run_identity_sha256
    from assetops_backend.sites.adapters.import_files import read_import_source
    from assetops_backend.sites.foundation_service import ImportSource, import_site

P01 = ("assetops.s4-power-demo-cases", "1")
P02 = ("assetops.s4-power-late-demo-cases", "1")
SPECS = None


def specs():
    global SPECS
    SPECS = SPECS or AuthoredFixtureSpecs()
    return SPECS


def ledger() -> PostgresEvidenceLedger:
    return PostgresEvidenceLedger(URL)


def ingestion(led=None, **options) -> BatchIngestionService:
    return BatchIngestionService(led or ledger(), Clock(RECEIVED), **options)


@pytest.fixture()
def kit(store, engine):
    _, outcome = converted_enabled(store, engine)
    return Kit(engine, outcome.published.changed.id)


def publish(kit, body, fixture=P01, **kw):
    return register_authored(ledger(), specs(), kit.principal.tenant_id, body, fixture_id=fixture[0],
                             fixture_version=fixture[1], **kw)


def submit(kit, body, led=None, **options):
    return ingestion(led, **options).submit(kit.principal, body.encode("utf-8"))


def provenance(engine, evidence_ids) -> dict:
    """accepted_evidence_id -> (publication_id, source_class, fixture_id, fixture_version, run_id) or None."""
    with engine.connect() as c:
        rows = c.execute(text(
            "SELECT e.id, p.id AS pub, p.source_class, p.fixture_id, p.fixture_version, p.run_id "
            "FROM accepted_evidence e LEFT JOIN batch_publication_link l ON l.batch_id = e.batch_id "
            "LEFT JOIN evidence_publication p ON p.id = l.publication_id WHERE e.id = ANY(:ids)"),
            {"ids": list(evidence_ids)}).all()
    return {r.id: (None if r.pub is None else (r.pub, r.source_class, r.fixture_id, r.fixture_version, r.run_id))
            for r in rows}


def count(engine, table) -> int:
    with engine.connect() as c:
        return c.execute(text(f"SELECT count(*) FROM {table}")).scalar_one()


def accepted_ids(receipt):
    return [d.evidence_id for d in receipt.dispositions if d.decision == "ACCEPTED"]


class TestAuthoredPublication:
    def test_fresh_publication_then_upload_binds_every_accepted_id(self, kit, engine) -> None:
        body = kit.seal(kit.pv(3))
        reg = publish(kit, body)
        assert reg.created
        receipt = submit(kit, body).receipt
        ids = [UUID(i) for i in accepted_ids(receipt)]
        assert len(ids) == 3
        prov = provenance(engine, ids)
        assert set(prov.values()) == {(reg.publication_id, AUTHORED_DEMONSTRATION, P01[0], P01[1], None)}
        with engine.connect() as c:
            row = c.execute(text("SELECT * FROM evidence_publication")).mappings().one()
        assert (row["actor_kind"], row["actor_id"], row["channel"]) == (
            "SYSTEM", FIXTURE_PUBLISHER.actor_id, "SYSTEM_CLI")
        assert row["publication_trigger"] == "AUTHORED_FIXTURE_PUBLICATION" and row["recorded_at"] is not None
        assert row["payload_sha256"] == json.loads(body)["payload_sha256"]

    def test_unpublished_upload_is_accepted_with_unknown_source(self, kit, engine) -> None:
        receipt = submit(kit, kit.seal(kit.pv(2))).receipt
        assert receipt.status == "COMPLETED"
        assert set(provenance(engine, [UUID(i) for i in accepted_ids(receipt)]).values()) == {None}
        assert count(engine, "batch_publication_link") == 0

    def test_identical_retry_returns_the_same_id_and_conflicting_reuse_fails(self, kit, engine) -> None:
        body = kit.seal(kit.pv(2))
        first = publish(kit, body)
        again = publish(kit, body)
        assert (again.publication_id, again.created) == (first.publication_id, False)
        assert publish(kit, body, publication_id=first.publication_id).publication_id == first.publication_id
        with pytest.raises(PublicationRefused) as changed_fixture:
            publish(kit, body, fixture=P02)
        assert changed_fixture.value.kind == "PUBLICATION_CONFLICT"
        with pytest.raises(PublicationRefused) as changed_bytes:
            publish(kit, kit.seal(kit.pv(2, value="9")))  # same batch slot, different payload digest
        assert changed_bytes.value.kind == "PUBLICATION_CONFLICT"
        with pytest.raises(PublicationRefused) as other_id:
            publish(kit, body, publication_id=uuid4())
        assert other_id.value.kind == "PUBLICATION_CONFLICT"
        with pytest.raises(PublicationRefused) as reused:
            publish(kit, kit.seal(kit.pv(2, first=10)), publication_id=first.publication_id)
        assert reused.value.kind == "PUBLICATION_ID_REUSED"
        assert count(engine, "evidence_publication") == 1

    def test_fixture_must_be_the_servers_declared_id_and_version(self, kit, tmp_path) -> None:
        body = kit.seal(kit.pv(1))
        for fixture, kind in (
            (("assetops.unknown-cases", "1"), "FIXTURE_UNKNOWN"),
            ((P01[0], "2"), "FIXTURE_VERSION_MISMATCH"),
        ):
            with pytest.raises(PublicationRefused) as caught:
                publish(kit, body, fixture=fixture)
            assert caught.value.kind == kind
        broken = AuthoredFixtureSpecs({P01[0]: tmp_path / "missing.json"})
        with pytest.raises(PublicationRefused) as caught:
            authored_record(broken, kit.principal.tenant_id, body, fixture_id=P01[0], fixture_version="1")
        assert caught.value.kind == "FIXTURE_UNREADABLE"
        # P02 is an authored fixture too.
        assert publish(kit, body, fixture=P02).created

    def test_client_authority_mode_and_tampered_bytes_designate_nothing(self, kit, engine) -> None:
        body = kit.seal(kit.pv(1))
        client = PublicationAuthority(actor_id="user:browser", authorization_basis="client said so",
                                      channel="HTTP", trigger="CLIENT", actor_kind="HUMAN")
        for authority in (client, replace(FIXTURE_PUBLISHER, channel="HTTP")):
            with pytest.raises(PublicationRefused) as caught:
                authored_record(specs(), kit.principal.tenant_id, body, fixture_id=P01[0], fixture_version="1",
                                authority=authority)
            assert caught.value.kind == "SYSTEM_PRINCIPAL_REQUIRED"
        doc = json.loads(body)
        doc["payload_sha256"] = "0" * 64
        with pytest.raises(PublicationRefused) as caught:
            publish(kit, json.dumps(doc, sort_keys=True, separators=(",", ":")))
        assert caught.value.kind == "BATCH_UNREADABLE"
        # The DB itself refuses a non-SYSTEM actor or an unknown channel.
        record = authored_record(specs(), kit.principal.tenant_id, body, fixture_id=P01[0], fixture_version="1")
        for authority in (client, replace(FIXTURE_PUBLISHER, channel="HTTP")):
            with pytest.raises(IntegrityError):
                PostgresEvidenceLedger(URL).register_publication(replace(record, authority=authority))
        # A SIMULATED gateway upload with no publication stays unknown (mode alone designates nothing).
        assert set(provenance(engine, [UUID(i) for i in accepted_ids(submit(kit, body).receipt)]).values()) == {None}

    def test_wrong_site_gateway_source_and_cross_tenant_scope_are_refused(self, kit, store, engine) -> None:
        body = kit.seal(kit.pv(1))
        record = authored_record(specs(), kit.principal.tenant_id, body, fixture_id=P01[0], fixture_version="1")
        other_source = UUID(kit.binding("generator-controller")["source_id"])
        source = read_import_source(str(KOBO_SOURCE))
        acme = import_site(store, tenant_slug="acme", configured_tenant_slug="acme",
                           source=ImportSource(path="var/sites/kobo-001.yaml", sha256=source.sha256,
                                               record=source.record),
                           legacy_documents=(), clock=Clock(NOW - timedelta(hours=2)))
        assert acme.site.id != kit.principal.site_id  # two tenants, the same Site code
        cases = (
            (replace(record, gateway_id=uuid4()), "GATEWAY_NOT_REGISTERED"),
            (replace(record, site_id=acme.site.id), "GATEWAY_NOT_REGISTERED"),
            (replace(record, tenant_id=acme.tenant.id), "GATEWAY_NOT_REGISTERED"),
            (replace(record, source_id=uuid4()), "SOURCE_NOT_AFFILIATED"),
        )
        for bad, kind in cases:
            with pytest.raises(PublicationRefused) as caught:
                ledger().register_publication(bad)
            assert caught.value.kind == kind
        assert count(engine, "evidence_publication") == 0
        # A publication for another source of the same gateway is a commitment the upload does not match.
        ledger().register_publication(replace(record, source_id=other_source))
        with pytest.raises(BatchRefused) as refused:
            submit(kit, body)
        assert (refused.value.status, refused.value.kind) == (409, "PUBLICATION_MISMATCH")

    def test_cli_publishes_the_named_site_only(self, kit, tmp_path, capsys) -> None:
        body = kit.seal(kit.pv(1))
        path = tmp_path / "batch.json"
        path.write_text(body, encoding="utf-8")
        args = ["--site", "KOBO-001", "--fixture-id", P01[0], "--fixture-version", "1", "--batch-file", str(path)]
        assert publish_source_main(args, ledger=ledger(), specs=specs()) == 0
        assert publish_source_main(args, ledger=ledger(), specs=specs()) == 0
        assert "already published (identical)" in capsys.readouterr().out
        assert publish_source_main(["--site", "NOPE-001"] + args[2:], ledger=ledger(), specs=specs()) == 2
        assert publish_source_main(args + ["--tenant", "acme"], ledger=ledger(), specs=specs()) == 2


class TestAdmissionBinding:
    def test_mismatched_commitment_fails_upload_and_admits_nothing(self, kit, engine) -> None:
        publish(kit, kit.seal(kit.pv(2)))
        other = kit.seal(kit.pv(2, value="7"))  # same batch ID, different payload digest
        with pytest.raises(BatchRefused) as refused:
            submit(kit, other)
        assert (refused.value.status, refused.value.kind) == (409, "PUBLICATION_MISMATCH")
        assert count(engine, "ingestion_batch") == 0 and count(engine, "accepted_evidence") == 0
        with engine.connect() as c:
            assert c.execute(text("SELECT kind FROM batch_refusal")).scalar_one() == "PUBLICATION_MISMATCH"

    def test_registration_after_partial_or_full_admission_fails(self, kit, engine) -> None:
        body = kit.seal(kit.pv(3))
        step = submit(kit, body, chunk_size=1, max_chunks_per_request=1)
        assert step.status == 202
        with pytest.raises(PublicationRefused) as partial:
            publish(kit, body)
        assert partial.value.kind == "ALREADY_ADMITTED" and "IN_PROGRESS" in partial.value.detail
        submit(kit, body)
        with pytest.raises(PublicationRefused) as full:
            publish(kit, body)
        assert full.value.kind == "ALREADY_ADMITTED"
        assert count(engine, "evidence_publication") == 0  # no retroactive designation

    def test_chunk_restart_keeps_the_binding_for_every_accepted_id(self, kit, engine) -> None:
        body = kit.seal(kit.pv(4))
        reg = publish(kit, body)
        with pytest.raises(SimulatedCrash):
            submit(kit, body, chunk_size=1, crash_after_chunks=1)
        receipt = submit(kit, body).receipt
        ids = [UUID(i) for i in accepted_ids(receipt)]
        assert len(ids) == 4
        assert {v[0] for v in provenance(engine, ids).values()} == {reg.publication_id}
        assert count(engine, "batch_publication_link") == 1

    def test_duplicate_keeps_its_original_id_and_rejected_or_conflict_rows_acquire_none(self, kit, engine) -> None:
        first = kit.pv(3)
        reg = publish(kit, kit.seal(first))
        original = accepted_ids(submit(kit, kit.seal(first)).receipt)
        texts = [first[2], kit.envelope("pv-inverter-controller", 4, 3, "1.5"),
                 kit.envelope("pv-inverter-controller", 5, 4, "2", signal_id="unbound-signal")]
        second = kit.seal(texts)
        reg2 = publish(kit, second, fixture=P02)
        r = submit(kit, second).receipt
        assert [d.decision for d in r.dispositions] == ["DUPLICATE", "ACCEPTED", "REJECTED"]
        dup, new, rejected = r.dispositions
        assert dup.evidence_id == original[2] and rejected.evidence_id is None
        prov = provenance(engine, [UUID(dup.evidence_id), UUID(new.evidence_id)])
        assert prov[UUID(dup.evidence_id)][0] == reg.publication_id  # the original keeps its first provenance
        assert prov[UUID(new.evidence_id)][0] == reg2.publication_id
        conflict = kit.seal([kit.envelope("pv-inverter-controller", 1, 9, "8")])
        publish(kit, conflict, fixture=P02)
        c = submit(kit, conflict).receipt
        assert [d.decision for d in c.dispositions] == ["CONFLICT"] and c.dispositions[0].evidence_id is None

    def test_registration_and_upload_serialize_on_the_same_slot_lock(self, kit, engine) -> None:
        body = kit.seal(kit.pv(2))
        key = admission_lock_key(kit.principal.tenant_id, kit.principal.site_id, json.loads(body)["batch_id"])
        holder = create_engine(URL)
        results: dict[str, object] = {}

        def run(name, fn):
            try:
                results[name] = fn()
            except Exception as error:  # noqa: BLE001 - recorded for the assertion below
                results[name] = error

        try:
            with holder.begin() as c:
                c.execute(text("SELECT pg_advisory_xact_lock(:k)"), {"k": key})
                threads = [threading.Thread(target=run, args=("register", lambda: publish(kit, body))),
                           threading.Thread(target=run, args=("upload", lambda: submit(kit, body)))]
                for t in threads:
                    t.start()
                time.sleep(0.6)
                assert results == {}, "registration or upload ran while another transaction held the slot lock"
            for t in threads:
                t.join(30)
        finally:
            holder.dispose()
        upload = results["upload"]
        assert not isinstance(upload, Exception)
        ids = [UUID(i) for i in accepted_ids(upload.receipt)]
        bound = {v is not None for v in provenance(engine, ids).values()}
        if isinstance(results["register"], PublicationRefused):  # upload won: registration came too late
            assert results["register"].kind == "ALREADY_ADMITTED" and bound == {False}
            assert count(engine, "evidence_publication") == 0
        else:  # registration won: the upload bound it in its admission transaction
            assert bound == {True}
        # Never a publication beside an unbound admission of the same slot.
        with engine.connect() as c:
            orphan = c.execute(text(
                "SELECT count(*) FROM evidence_publication p JOIN ingestion_batch b ON b.site_id = p.site_id "
                "AND b.external_batch_id = p.external_batch_id LEFT JOIN batch_publication_link l "
                "ON l.batch_id = b.id WHERE l.batch_id IS NULL")).scalar_one()
        assert orphan == 0

    def test_many_races_never_leave_a_publication_beside_an_unbound_batch(self, kit, engine) -> None:
        outcomes = []
        for n in range(6):
            body = kit.seal(kit.pv(1, first=100 + n))
            box: dict[str, object] = {}
            barrier = threading.Barrier(2)

            def reg(body=body, box=box):
                barrier.wait()
                try:
                    box["r"] = publish(kit, body)
                except PublicationRefused as error:
                    box["r"] = error

            def up(body=body, box=box):
                barrier.wait()
                box["u"] = submit(kit, body)

            threads = [threading.Thread(target=reg), threading.Thread(target=up)]
            for t in threads:
                t.start()
            for t in threads:
                t.join(30)
            outcomes.append(type(box["r"]).__name__)
        with engine.connect() as c:
            pubs = c.execute(text("SELECT count(*) FROM evidence_publication")).scalar_one()
            links = c.execute(text("SELECT count(*) FROM batch_publication_link")).scalar_one()
        assert pubs == links == outcomes.count("Registered")


class TestRegisteredSimulation:
    @pytest.fixture()
    def run(self, kit, store, tmp_path):
        return run_setup(store, YamlRunStore(tmp_path / "runs")).create_draft_run(run_request())

    def stage(self, run, bodies, *, status="STAGED", run_id=None, extra_messages=()):
        class Env:
            def __init__(self, message_id):
                self.message_id = message_id

        class Batch:
            def __init__(self, body):
                doc = json.loads(body)
                self.batch_id, self.payload_text, self.sha256 = doc["batch_id"], body, doc["payload_sha256"]
                self.message_ids = tuple(json.loads(e)["message"]["message_id"] for e in doc["envelopes"])

        class Stage:
            pass

        stage = Stage()
        stage.run_id, stage.status = run_id or run.run_id, status
        stage.batches = tuple(Batch(b) for b in bodies)
        stage.envelopes = tuple(Env(m) for b in stage.batches for m in b.message_ids) + tuple(
            Env(m) for m in extra_messages)
        return stage

    def test_one_run_several_batches_bind_with_the_server_run_identity(self, kit, engine, run) -> None:
        assert run.registered_basis.snapshot_sha256 == kit.sha
        assert run.registered_basis.site_record_id == str(kit.principal.site_id)
        bodies = [kit.seal(kit.pv(2)), kit.seal(kit.pv(2, first=3))]
        regs = register_run(ledger(), run_attestation(run, self.stage(run, bodies)))
        assert len(regs) == 2 and all(r.created for r in regs)
        assert register_run(ledger(), run_attestation(run, self.stage(run, bodies)))[0].created is False
        ids = []
        for body in bodies:
            ids += [UUID(i) for i in accepted_ids(submit(kit, body).receipt)]
        prov = provenance(engine, ids)
        assert {v[1:] for v in prov.values()} == {(REGISTERED_SIMULATION, None, None, run.run_id)}
        assert {v[0] for v in prov.values()} == {r.publication_id for r in regs}
        with engine.connect() as c:
            digest = c.execute(text("SELECT DISTINCT run_identity_sha256 FROM evidence_publication")).scalar_one()
            texts = " ".join(str(v) for row in c.execute(text("SELECT * FROM evidence_publication")).all() for v in row)
        assert digest == run_identity_sha256(run)
        assert run.deterministic_identity.scenario.scenario_id not in texts  # private scenario truth stays out

    def test_manifest_only_foreign_or_unstaged_proof_is_refused(self, kit, run) -> None:
        body = kit.seal(kit.pv(2))
        foreign = kit.seal(kit.pv(1, first=50))
        doc = json.loads(body)
        cases = (
            (self.stage(run, [body], run_id="run-other"), "RUN_STAGE_MISMATCH"),
            (self.stage(run, [body], status="SEALING_PENDING"), "RUN_NOT_STAGED"),
            (self.stage(run, []), "RUN_NOT_STAGED"),
        )
        for stage, kind in cases:
            with pytest.raises(PublicationRefused) as caught:
                simulation_records(run_attestation(run, stage))
            assert caught.value.kind == kind
        # A manifest that claims a batch whose bytes are not the stated digest proves nothing.
        stage = self.stage(run, [body])
        stage.batches[0].sha256 = "f" * 64
        with pytest.raises(PublicationRefused) as caught:
            simulation_records(run_attestation(run, stage))
        assert caught.value.kind == "RUN_BATCH_MISMATCH"
        # A batch holding messages the run did not stage is foreign.
        stage = self.stage(run, [foreign])
        stage.envelopes = ()
        with pytest.raises(PublicationRefused) as caught:
            simulation_records(run_attestation(run, stage))
        assert caught.value.kind == "RUN_BATCH_FOREIGN"
        assert doc["batch_id"]
        # A run with no registered basis cannot be designated.
        with pytest.raises(PublicationRefused) as caught:
            run_attestation(replace(run, registered_basis=None), self.stage(run, [body]))
        assert caught.value.kind == "RUN_NOT_REGISTERED"

    def test_a_snapshot_other_than_the_runs_is_refused(self, kit, run) -> None:
        body = kit.seal(kit.pv(1))
        attestation = run_attestation(run, self.stage(run, [body]))
        with pytest.raises(PublicationRefused) as caught:
            simulation_records(replace(attestation, snapshot_sha256="a" * 64))
        assert caught.value.kind == "RUN_SNAPSHOT_MISMATCH"
        with pytest.raises(PublicationRefused) as caught:
            simulation_records(replace(attestation, site_id=str(uuid4())))
        assert caught.value.kind == "RUN_SCOPE_MISMATCH"

    def test_a_live_gateway_cannot_carry_any_publication(self, kit, engine, run) -> None:
        body = kit.seal(kit.pv(1))
        (record,) = simulation_records(run_attestation(run, self.stage(run, [body])))
        live_gateway, live_source = uuid4(), uuid4()
        with engine.begin() as c:
            asset = c.execute(text("SELECT asset_id FROM source WHERE id = :s"), {"s": record.source_id}).scalar_one()
            c.execute(text(
                "INSERT INTO gateway (id, tenant_id, site_id, gateway_external_id, mode, registered_at) "
                "VALUES (:g, :t, :s, 'live-gw', 'LIVE', now())"),
                {"g": live_gateway, "t": record.tenant_id, "s": record.site_id})
            c.execute(text(
                "INSERT INTO source (id, tenant_id, site_id, gateway_id, source_external_id, device_kind, asset_id, "
                "registered_at) VALUES (:id, :t, :s, :g, 'live-src', 'meter', :a, now())"),
                {"id": live_source, "t": record.tenant_id, "s": record.site_id, "g": live_gateway, "a": asset})
        with pytest.raises(PublicationRefused) as caught:
            ledger().register_publication(replace(record, gateway_id=live_gateway, source_id=live_source))
        assert caught.value.kind == "GATEWAY_NOT_SIMULATED"
        # Phase-1 review M1: an authored designation on a LIVE gateway is refused too, with nothing written.
        authored = replace(record, gateway_id=live_gateway, source_id=live_source, source_class=AUTHORED_DEMONSTRATION,
                           fixture_id=P01[0], fixture_version="1", run_id=None, run_identity_sha256=None,
                           authority=FIXTURE_PUBLISHER)
        with pytest.raises(PublicationRefused) as caught:
            ledger().register_publication(authored)
        assert caught.value.kind == "GATEWAY_NOT_SIMULATED"
        assert count(engine, "evidence_publication") == 0


class TestDatabaseImmutability:
    def test_downgrade_refuses_while_a_publication_exists(self, store, engine) -> None:  # noqa: F811
        """Phase-1 review L3: 0014's downgrade never deletes immutable provenance; it refuses and stays at head."""
        from alembic import command
        from alembic.config import Config
        from mini_depth_probe import assert_no_mini_history, seeded_before_0029

        config = Config(str(BACKEND / "alembic.ini"))
        config.attributes["database_url"] = URL
        # W4-02 q1 ruling 2: the MINIGRID Site and its publication are seeded before 0029 is installed.
        with seeded_before_0029(config, engine, store):
            _, outcome = converted_enabled(store, engine)
            kit = Kit(engine, outcome.published.changed.id)
            reg = publish(kit, kit.seal(kit.pv(1)))
        assert_no_mini_history(engine)
        engine.dispose()
        try:
            with pytest.raises(Exception, match="Downgrade of 0017_evidence_publication refused"):
                __import__("mini_depth_probe").assert_no_mini_history(engine)  # q1 ruling 2: before 0029
                command.downgrade(config, "0016_action_store")
            with engine.connect() as c:
                assert c.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == (
                    "0034_w5_ev_scenarios")
                assert c.execute(text("SELECT id FROM evidence_publication")).scalar_one() == reg.publication_id
        finally:
            command.upgrade(config, "head")

    def test_provenance_rows_refuse_update_delete_and_wrong_links(self, kit, engine) -> None:
        body = kit.seal(kit.pv(2))
        reg = publish(kit, body)
        receipt = submit(kit, body).receipt
        unbound = kit.seal(kit.pv(1, first=20))
        submit(kit, unbound)
        with engine.connect() as c:
            batch = c.execute(text("SELECT * FROM ingestion_batch WHERE external_batch_id = :b"),
                              {"b": json.loads(body)["batch_id"]}).mappings().one()
            other = c.execute(text("SELECT * FROM ingestion_batch WHERE external_batch_id = :b"),
                              {"b": json.loads(unbound)["batch_id"]}).mappings().one()
        assert receipt.status == "COMPLETED"
        probes = (
            ("UPDATE evidence_publication SET fixture_version = '2'", "immutable source provenance"),
            ("DELETE FROM evidence_publication", "immutable source provenance"),
            ("UPDATE batch_publication_link SET linked_at = now()", "immutable source provenance"),
            ("DELETE FROM batch_publication_link", "immutable source provenance"),
            ("UPDATE ingestion_batch SET payload_sha256 = repeat('0', 64) WHERE id = :b", "immutable"),
            # Retroactive binding of an admitted unbound batch: the commitment FK refuses another batch.
            ("INSERT INTO batch_publication_link (batch_id, publication_id, tenant_id, site_id, gateway_id, "
             "source_id, external_batch_id, payload_sha256, linked_at) VALUES (:o, :p, :t, :s, :g, :src, :ob, "
             ":osha, now())", "batch_publication_link_publication_fk|publication_unique"),
            # A second publication for the same Site batch slot.
            ("INSERT INTO evidence_publication (id, tenant_id, site_id, gateway_id, source_id, external_batch_id, "
             "payload_sha256, source_class, fixture_id, fixture_version, actor_kind, actor_id, authorization_basis, "
             "channel, publication_trigger, recorded_at) VALUES (gen_random_uuid(), :t, :s, :g, :src, :eb, :sha, "
             "'AUTHORED_DEMONSTRATION', 'x', '1', 'SYSTEM', 'a', 'b', 'SYSTEM_CLI', 'c', now())",
             "evidence_publication_slot_unique"),
            # A class without its basis.
            ("INSERT INTO evidence_publication (id, tenant_id, site_id, gateway_id, source_id, external_batch_id, "
             "payload_sha256, source_class, actor_kind, actor_id, authorization_basis, channel, publication_trigger, "
             "recorded_at) VALUES (gen_random_uuid(), :t, :s, :g, :src, 'other', :sha, 'REGISTERED_SIMULATION', "
             "'SYSTEM', 'a', 'b', 'SYSTEM_CLI', 'c', now())", "evidence_publication_class"),
        )
        params = {"b": batch["id"], "o": other["id"], "p": reg.publication_id, "t": batch["tenant_id"],
                  "s": batch["site_id"], "g": batch["gateway_id"], "src": batch["source_id"],
                  "ob": other["external_batch_id"], "osha": other["payload_sha256"],
                  "eb": batch["external_batch_id"], "sha": batch["payload_sha256"]}
        for sql, message in probes:
            try:
                with engine.begin() as c:
                    c.execute(text(sql), params)
            except DBAPIError as error:
                assert __import__("re").search(message, str(error)), (sql, str(error)[:300])
            else:
                pytest.fail(f"direct SQL was not refused: {sql}")

    def test_a_link_cannot_cross_site_or_digest(self, kit, store, engine) -> None:
        body = kit.seal(kit.pv(1))
        unbound = kit.seal(kit.pv(1, first=30))
        submit(kit, unbound)
        reg = publish(kit, body)
        with engine.connect() as c:
            other = c.execute(text("SELECT * FROM ingestion_batch")).mappings().one()
        # Point a new link at the unbound batch while claiming the publication's own commitment: FK refuses.
        doc = json.loads(body)
        with pytest.raises(IntegrityError, match="batch_publication_link_batch_fk"):
            with engine.begin() as c:
                c.execute(text(
                    "INSERT INTO batch_publication_link (batch_id, publication_id, tenant_id, site_id, gateway_id, "
                    "source_id, external_batch_id, payload_sha256, linked_at) VALUES (:b, :p, :t, :s, :g, :src, :eb, "
                    ":sha, now())"),
                    {"b": other["id"], "p": reg.publication_id, "t": other["tenant_id"], "s": other["site_id"],
                     "g": other["gateway_id"], "src": other["source_id"], "eb": doc["batch_id"],
                     "sha": doc["payload_sha256"]})


class TestAdmissionLockCost:
    def test_measure_open_batch_lock_cost_against_the_unbound_baseline(self, kit, engine) -> None:
        """Times `open_batch` (lock + publication read [+ link]) against the pre-S4-05a statement alone."""

        class Timed(PostgresEvidenceLedger):
            def __init__(self, url, sink, baseline=False):
                super().__init__(url)
                self.sink, self.baseline = sink, baseline

            def open_batch(self, principal, **kw):
                start = time.perf_counter()
                try:
                    if not self.baseline:
                        return super().open_batch(principal, **kw)
                    return self._baseline(principal, **kw)
                finally:
                    self.sink.append((time.perf_counter() - start) * 1000)

            def _baseline(self, principal, *, external_batch_id, payload_sha256, source_id, source_mode, basis,
                          batch_text, total, received_at):
                from assetops_backend.evidence.ledger import BatchHandle

                def work(c):
                    c.execute(text(
                        "INSERT INTO ingestion_batch (id, tenant_id, site_id, gateway_id, source_id, "
                        "external_batch_id, payload_sha256, schema_version, source_mode, foundation_revision_id, "
                        "binding_set_revision_id, snapshot_sha256, batch_text, status, total_count, received_at) "
                        "VALUES (:id, :t, :site, :g, :src, :b, :sha, 2, :mode, :f, :bs, :snap, :body, "
                        "'IN_PROGRESS', :total, :at) ON CONFLICT ON CONSTRAINT ingestion_batch_external_unique "
                        "DO NOTHING"),
                        {"id": uuid4(), "t": principal.tenant_id, "site": principal.site_id,
                         "g": principal.gateway_id, "src": UUID(source_id), "b": external_batch_id,
                         "sha": payload_sha256, "mode": source_mode, "f": basis.foundation_revision_id,
                         "bs": basis.binding_set_revision_id, "snap": basis.snapshot_sha256, "body": batch_text,
                         "total": total, "at": received_at})
                    row = c.execute(text(
                        "SELECT id, payload_sha256, status FROM ingestion_batch WHERE tenant_id = :t AND "
                        "site_id = :site AND external_batch_id = :b"),
                        {"t": principal.tenant_id, "site": principal.site_id, "b": external_batch_id}).one()
                    return BatchHandle(row.id, row.payload_sha256, row.status)

                return self._run(work, write=True)

        n = int(os.environ.get("ASSETOPS_S405_LOCK_SAMPLES", "20"))
        samples = {"baseline": [], "unbound": [], "bound": []}
        led = {k: Timed(URL, samples[k], baseline=(k == "baseline")) for k in samples}
        seq = 1000
        for i in range(n):
            for kind in ("baseline", "unbound", "bound"):  # interleaved so drift hits all three alike
                body = kit.seal(kit.pv(1, first=seq))
                seq += 1
                if kind == "bound":
                    publish(kit, body)
                submit(kit, body, led=led[kind])
        # Contention: open_batch while two threads upload distinct slots at once (distinct lock keys).
        waits = []
        concurrent = Timed(URL, waits)
        bodies = [kit.seal(kit.pv(1, first=seq + j)) for j in range(20)]

        def burst(chunk):
            for body in chunk:
                submit(kit, body, led=concurrent)

        threads = [threading.Thread(target=burst, args=(bodies[j::2],)) for j in range(2)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(60)

        def stats(xs):
            xs = sorted(xs)
            return {"n": len(xs), "median_ms": round(statistics.median(xs), 3),
                    "p95_ms": round(xs[max(0, int(round(0.95 * len(xs))) - 1)], 3)}

        report = {k: stats(v) for k, v in samples.items()}
        report["unbound_two_threads_distinct_slots"] = stats(waits)
        print("S4-05a open_batch lock cost:", json.dumps(report))
        out = os.environ.get("ASSETOPS_S405_LOCK_REPORT")
        if out:
            with open(out, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)
        assert report["unbound"]["n"] == report["bound"]["n"] == report["baseline"]["n"] == n
        assert len(waits) == 20
        # A coarse ceiling only: the measured figures, not this bound, are the evidence.
        assert report["bound"]["median_ms"] < report["baseline"]["median_ms"] + 50
