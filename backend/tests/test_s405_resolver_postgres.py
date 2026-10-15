"""S4-05a phase 2: the exact-revision source provenance resolver over PostgreSQL.

`tasks/S4-05a-provenance-binding-resolver.md` phase 2; `tasks/S4-05-stored-demo-provenance.md` shared contract
item 3; `.agent/architect-S4-05-answers.md` Q2 and Follow-up M1; N-L2. Every class of the truth table is proved
from real publications and uploads (authored P01/P02, one and several registered runs, unbound uploads), plus
foreign-Site, missing and broken links (constructed inside a rolled-back transaction), a real FindingRevision
and its consequence revision, consequence-only mixed power input, and a selected historical revision that keeps
its own state after a new head. Requires ASSETOPS_TEST_DATABASE_URL (see backend/TESTING.md).
"""

from __future__ import annotations

import json
import os
from uuid import UUID, uuid4

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")


@pytest.fixture(autouse=True)
def _release_connections():
    yield
    import gc

    gc.collect()


if URL:
    from sqlalchemy import text
    from test_s1_bindings_postgres import Clock, engine, store  # noqa: F401
    from test_s2_evidence_ledger_postgres import Kit, converted_enabled
    from test_s2_registered_basis import request as run_request
    from test_s2_registered_basis_postgres import service as run_setup
    from test_s4_consequence_store_postgres import POWER_DAY, PowerSite
    from test_s4_evidence_consequence_work_postgres import clone_revision
    from test_s4_finding_store_postgres import CaseRunner
    from test_s405_publication_postgres import P01, P02, accepted_ids, ledger, publish, specs, submit

    from assetops_backend.evidence import source_provenance as sp
    from assetops_backend.evidence.adapters.postgres_evidence_ledger import PostgresEvidenceLedger
    from assetops_backend.evidence.composition import build_source_provenance
    from assetops_backend.evidence.ledger_service import BatchIngestionService
    from assetops_backend.evidence.publication import register_authored, register_run
    from assetops_backend.runs.adapters.yaml_run_store import YamlRunStore
    from assetops_backend.runs.source_publication import run_attestation, run_identity_sha256


@pytest.fixture()
def kit(store, engine):  # noqa: F811
    _, outcome = converted_enabled(store, engine)
    return Kit(engine, outcome.published.changed.id)


@pytest.fixture()
def resolver():
    r = build_source_provenance(URL)
    yield r


def upload(kit, body) -> list[str]:
    return [str(i) for i in accepted_ids(submit(kit, body).receipt)]


def authored(kit, body, fixture=P01) -> tuple[str, list[str]]:
    reg = publish(kit, body, fixture=fixture)
    return str(reg.publication_id), upload(kit, body)


def stage(run, bodies):
    """The registered gateway's staged batches for `run`, as `run_attestation` reads them (phase-1 shape)."""
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

    s = Stage()
    s.run_id, s.status = run.run_id, "STAGED"
    s.batches = tuple(Batch(b) for b in bodies)
    s.envelopes = tuple(Env(m) for b in s.batches for m in b.message_ids)
    return s


def simulated(kit, run, bodies) -> tuple[list[str], list[str]]:
    regs = register_run(ledger(), run_attestation(run, stage(run, bodies)))
    ids = [i for body in bodies for i in upload(kit, body)]
    return [str(r.publication_id) for r in regs], ids


def codes(result):
    return [r["code"] for r in result["reasons"]]


class TestTruthTableOnStoredBindings:
    def test_two_publications_of_one_fixture_version_resolve_authored(self, kit, resolver) -> None:
        p1, a = authored(kit, kit.seal(kit.pv(2)))
        p2, b = authored(kit, kit.seal(kit.pv(2, first=3)))
        r = resolver.resolve(kit.principal.tenant_id, kit.principal.site_id, a + b)
        assert r["state"] == sp.AUTHORED_DEMONSTRATION and r["reasons"] == []
        assert r["publication_ids"] == sorted([p1, p2])
        assert r["fixtures"] == [{"fixture_id": P01[0], "fixture_version": P01[1]}]
        assert {e["accepted_evidence_id"]: e["publication_id"] for e in r["evidence"]} == {
            **{i: p1 for i in a}, **{i: p2 for i in b}}
        assert all(e["batch_id"] and e["status"] == sp.BOUND for e in r["evidence"])

    def test_differing_authored_fixture_is_mixed(self, kit, resolver) -> None:
        _, a = authored(kit, kit.seal(kit.pv(2)))
        _, b = authored(kit, kit.seal(kit.pv(2, first=3)), fixture=P02)
        r = resolver.resolve(kit.principal.tenant_id, kit.principal.site_id, a + b)
        assert r["state"] == sp.MIXED and codes(r) == [sp.AUTHORED_FIXTURE_VERSION_CONFLICT]
        assert r["problematic_accepted_evidence_ids"] == sorted(a + b)

    def test_one_run_is_registered_simulation_and_two_runs_are_mixed(self, kit, store, resolver,  # noqa: F811
                                                                       tmp_path) -> None:
        runs = run_setup(store, YamlRunStore(tmp_path / "runs"))
        first, second = runs.create_draft_run(run_request()), runs.create_draft_run(run_request())
        assert first.run_id != second.run_id
        pubs, ids = simulated(kit, first, [kit.seal(kit.pv(2)), kit.seal(kit.pv(2, first=3))])
        scope = (kit.principal.tenant_id, kit.principal.site_id)
        r = resolver.resolve(*scope, ids)
        assert r["state"] == sp.REGISTERED_SIMULATION and r["publication_ids"] == sorted(pubs)
        assert r["runs"] == [{"run_id": first.run_id, "run_identity_sha256": run_identity_sha256(first)}]
        _, other = simulated(kit, second, [kit.seal(kit.pv(1, first=10))])
        both = resolver.resolve(*scope, ids + other)
        assert both["state"] == sp.MIXED and codes(both) == [sp.MULTIPLE_RUNS_WITHOUT_COMPATIBLE_BASIS]
        assert both["reasons"][0]["run_ids"] == sorted([first.run_id, second.run_id])
        # Crossed classes and bound/unbound together report both reasons.
        _, auth = authored(kit, kit.seal(kit.pv(1, first=20)))
        plain = upload(kit, kit.seal(kit.pv(1, first=30)))
        crossed = resolver.resolve(*scope, ids + auth + plain)
        assert crossed["state"] == sp.MIXED
        assert codes(crossed) == [sp.BOUND_AND_UNBOUND, sp.CROSSED_SOURCE_CLASSES]
        assert crossed["reasons"][0]["accepted_evidence_ids"] == plain

    def test_unbound_empty_missing_and_foreign_site_are_unknown(self, kit, resolver) -> None:
        scope = (kit.principal.tenant_id, kit.principal.site_id)
        _, auth = authored(kit, kit.seal(kit.pv(1)))
        plain = upload(kit, kit.seal(kit.pv(2, first=3)))
        r = resolver.resolve(*scope, plain)
        assert r["state"] == sp.UNKNOWN and codes(r) == [sp.NO_POSITIVE_BINDING]
        assert r["problematic_accepted_evidence_ids"] == sorted(plain)
        assert codes(resolver.resolve(*scope, [])) == [sp.EMPTY_CITATION_SET]
        missing = str(uuid4())
        r = resolver.resolve(*scope, auth + plain + [missing])  # would be MIXED; missing takes precedence
        assert r["state"] == sp.UNKNOWN and codes(r) == [sp.EVIDENCE_NOT_FOUND]
        assert r["problematic_accepted_evidence_ids"] == [missing]
        foreign = resolver.resolve(kit.principal.tenant_id, uuid4(), auth)  # same tenant, another Site
        assert foreign["state"] == sp.UNKNOWN and codes(foreign) == [sp.FOREIGN_SITE_EVIDENCE]
        assert foreign["evidence"][0]["publication_id"] is None  # nothing of the other Site is revealed
        other_tenant = resolver.resolve(uuid4(), kit.principal.site_id, auth)  # never disclosed across tenants
        assert codes(other_tenant) == [sp.EVIDENCE_NOT_FOUND]

    def test_broken_links_are_named_and_precede_mixed(self, kit, engine) -> None:  # noqa: F811
        """Scoped FKs make a broken link impossible in normal operation, so it is built by dropping the FKs inside
        a transaction that is rolled back, and the real adapter SQL reads it on that same connection."""
        tenant, site = kit.principal.tenant_id, kit.principal.site_id
        pub, auth = authored(kit, kit.seal(kit.pv(1)))
        _, p02 = authored(kit, kit.seal(kit.pv(1, first=5)), fixture=P02)
        plain_body = kit.seal(kit.pv(1, first=3))
        plain = upload(kit, plain_body)
        dangling = kit.seal(kit.pv(1, first=9))
        lost = upload(kit, dangling)
        with engine.connect() as c:
            tx = c.begin()
            try:
                c.execute(text("ALTER TABLE batch_publication_link DROP CONSTRAINT batch_publication_link_batch_fk"))
                c.execute(text(
                    "ALTER TABLE batch_publication_link DROP CONSTRAINT batch_publication_link_publication_fk"))
                c.execute(text("ALTER TABLE batch_publication_link DROP CONSTRAINT "
                               "batch_publication_link_publication_unique"))
                batch = {r.k: r.v for r in c.execute(text(
                    "SELECT CAST(e.id AS text) AS k, e.batch_id AS v FROM accepted_evidence e "
                    "WHERE e.id = ANY(CAST(:ids AS uuid[]))"), {"ids": plain + lost})}
                p = c.execute(text("SELECT * FROM evidence_publication WHERE id = :p"), {"p": pub}).mappings().one()
                link = ("INSERT INTO batch_publication_link (batch_id, publication_id, tenant_id, site_id, gateway_id, "
                        "source_id, external_batch_id, payload_sha256, linked_at) VALUES (:b, :p, :t, :s, :g, :src, "
                        ":eb, :sha, now())")
                # The plain batch claims the authored publication's commitment (not its own batch's).
                c.execute(text(link), {"b": batch[plain[0]], "p": pub, "t": tenant, "s": site, "g": p["gateway_id"],
                                       "src": p["source_id"], "eb": p["external_batch_id"], "sha": p["payload_sha256"]})
                # The lost batch's own commitment, pointing at a publication that does not exist.
                doc = json.loads(dangling)
                c.execute(text(link), {"b": batch[lost[0]], "p": uuid4(), "t": tenant, "s": site,
                                       "g": p["gateway_id"], "src": p["source_id"], "eb": doc["batch_id"],
                                       "sha": doc["payload_sha256"]})
                reads = PostgresEvidenceLedger(URL)
                reads._run = lambda work, write=False: work(c)  # read the uncommitted state on this connection
                r = sp.SourceProvenanceResolver(reads).resolve(tenant, site, auth + p02 + plain + lost)
            finally:
                tx.rollback()
        assert r["state"] == sp.UNKNOWN and codes(r) == [sp.BROKEN_PUBLICATION_LINK]
        assert r["reasons"][0]["details"] == sorted([
            {"accepted_evidence_id": plain[0], "detail": sp.LINK_COMMITMENT_MISMATCH},
            {"accepted_evidence_id": lost[0], "detail": sp.PUBLICATION_NOT_FOUND}],
            key=lambda d: d["accepted_evidence_id"])
        assert r["problematic_accepted_evidence_ids"] == sorted(plain + lost)
        with engine.connect() as c:  # rolled back: the constraints and the original rows are intact
            assert c.execute(text("SELECT count(*) FROM batch_publication_link")).scalar_one() == 2
            assert c.execute(text("SELECT count(*) FROM pg_constraint WHERE conname LIKE "
                                  "'batch_publication_link_%'")).scalar_one() == 4


def publishing_submit(policy):
    """`CaseRunner.submit` that first publishes each exact sealed batch per `policy(device, texts)` -> fixture or
    None (unbound), so the real Finding/consequence pipeline cites bound evidence."""
    def submit(self, envelopes, decided_at):
        service = BatchIngestionService(PostgresEvidenceLedger(URL), Clock(decided_at))
        by_device: dict[str, list[str]] = {}
        for device, text_ in envelopes:
            by_device.setdefault(device, []).append(text_)
        for device, texts in by_device.items():
            body = self.kit.seal(texts, device_id=device)
            fixture = policy(device, texts)
            if fixture is not None:
                register_authored(ledger(), specs(), self.kit.principal.tenant_id, body, fixture_id=fixture[0],
                                  fixture_version=fixture[1])
            answer = service.submit(self.kit.principal, body.encode("utf-8"))
            assert answer.status == 200 and answer.receipt.status == "COMPLETED", answer
    return submit


def power_site(store, engine, capsys, monkeypatch, policy):  # noqa: F811
    monkeypatch.setattr(CaseRunner, "submit", publishing_submit(policy))
    s = PowerSite(store, engine, capsys)
    s.publish("v1", "v2", "v3")
    rev = s.on(POWER_DAY)
    appended = s.store.append(s.derive(rev))
    return s, rev, UUID(str(appended.consequence_revision_id))


def is_power(texts) -> bool:
    return any('"ac-power"' in t for t in texts)


class TestRevisionSets:
    def test_unbound_finding_and_consequence_are_unknown_from_their_exact_sets(
            self, store, engine, capsys, monkeypatch, resolver) -> None:  # noqa: F811
        s, rev, cid = power_site(store, engine, capsys, monkeypatch, lambda d, t: None)
        try:
            f = resolver.finding_revision(s.tenant, s.site, rev["id"])
            c = resolver.consequence_revision(s.tenant, s.site, cid)
            with engine.connect() as conn:
                cited = sorted(str(x) for x in conn.execute(text(
                    "SELECT evidence_id FROM finding_revision_evidence WHERE finding_revision_id = :r"),
                    {"r": rev["id"]}).scalars())
                power = sorted(str(x) for x in conn.execute(text(
                    "SELECT evidence_id FROM financial_consequence_power_interval WHERE consequence_revision_id = :c"),
                    {"c": cid}).scalars())
            assert cited and power
            assert f["state"] == sp.UNKNOWN and codes(f) == [sp.NO_POSITIVE_BINDING]
            assert f["finding_revision_id"] == str(rev["id"]) and f["cited_accepted_evidence_ids"] == cited
            assert c["state"] == sp.UNKNOWN and c["finding_revision_id"] == str(rev["id"])
            assert c["consequence_revision_id"] == str(cid) and c["power_accepted_evidence_ids"] == power
            assert c["accepted_evidence_ids"] == sorted(set(cited) | set(power))
            # Scope: another tenant or Site sees no revision at all.
            assert resolver.finding_revision(uuid4(), s.site, rev["id"]) is None
            assert resolver.finding_revision(s.tenant, uuid4(), rev["id"]) is None
            assert resolver.consequence_revision(s.tenant, uuid4(), cid) is None
        finally:
            s.prices.dispose()
            s.store.dispose()

    def test_authored_finding_keeps_its_state_after_a_new_head_and_its_consequence_is_authored(
            self, store, engine, capsys, monkeypatch, resolver) -> None:  # noqa: F811
        s, rev, cid = power_site(store, engine, capsys, monkeypatch, lambda d, t: P01)
        try:
            f = resolver.finding_revision(s.tenant, s.site, rev["id"])
            assert f["state"] == sp.AUTHORED_DEMONSTRATION and len(f["publication_ids"]) >= 2
            c = resolver.consequence_revision(s.tenant, s.site, cid)
            assert c["state"] == sp.AUTHORED_DEMONSTRATION and c["finding_revision_state"] == sp.AUTHORED_DEMONSTRATION
            head = clone_revision(engine, rev)  # a new latest revision with an empty cited set
            assert resolver.finding_revision(s.tenant, s.site, head)["state"] == sp.UNKNOWN
            again = resolver.finding_revision(s.tenant, s.site, rev["id"])
            assert again["state"] == sp.AUTHORED_DEMONSTRATION and again["publication_ids"] == f["publication_ids"]
        finally:
            s.prices.dispose()
            s.store.dispose()

    def test_unknown_finding_makes_its_consequence_unknown_even_with_bound_power_inputs(
            self, store, engine, capsys, monkeypatch, resolver) -> None:  # noqa: F811
        s, rev, cid = power_site(store, engine, capsys, monkeypatch, lambda d, t: P01 if is_power(t) else None)
        try:
            c = resolver.consequence_revision(s.tenant, s.site, cid)
            assert c["finding_revision_state"] == sp.UNKNOWN and c["state"] == sp.UNKNOWN, c["reasons"]
            assert codes(c)[0] == sp.NO_POSITIVE_BINDING
        finally:
            s.prices.dispose()
            s.store.dispose()

    def test_consequence_only_power_input_is_mixed_beside_its_finding(
            self, store, engine, capsys, monkeypatch, resolver) -> None:  # noqa: F811
        s, rev, cid = power_site(store, engine, capsys, monkeypatch, lambda d, t: P02 if is_power(t) else P01)
        try:
            f = resolver.finding_revision(s.tenant, s.site, rev["id"])
            c = resolver.consequence_revision(s.tenant, s.site, cid)
            power_only = sorted(set(c["power_accepted_evidence_ids"]) - set(c["cited_accepted_evidence_ids"]))
            assert power_only, "the consequence's power IDs must include IDs the Finding does not cite"
            assert f["state"] == sp.AUTHORED_DEMONSTRATION, f["reasons"]
            assert c["state"] == sp.MIXED and c["finding_revision_state"] == sp.AUTHORED_DEMONSTRATION
            assert codes(c) == [sp.AUTHORED_FIXTURE_VERSION_CONFLICT, sp.CONSEQUENCE_POWER_INPUT_CONFLICT]
            assert c["reasons"][1]["accepted_evidence_ids"] == power_only
        finally:
            s.prices.dispose()
            s.store.dispose()
