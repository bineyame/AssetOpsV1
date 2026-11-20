"""3C1a (`specs/3C1-person-on-commands/spec.md` §4; R4, R8, P1, P2, P7): the person migration, its constraints, and
the person path through `create_app` with the real stores.

The migration's ids are read from its module (D-3A1.12: it may be renumbered at merge). Every test starts from a
fresh migrated database (`pg_harness.fresh_database`), since the cold replay fixture makes its own. Needs
`ASSETOPS_TEST_DATABASE_URL` naming a `*_test` database; run through `tools/heavy-slot.sh --db`.
"""
from __future__ import annotations

import importlib.util
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

_PATH = next((Path(__file__).resolve().parents[1] / "migrations" / "versions").glob("*_person_on_work.py"))
_SPEC = importlib.util.spec_from_file_location("m3c1a", _PATH)
MIG = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(MIG)

TABLES = ("domain_action_case_link", "domain_action_intent", "domain_action", "operational_record",
          "maintenance_record", "maintenance_plan", "work_event", "work_case_revision", "work_case")
DOMAIN = ("domain_action", "domain_action_intent", "domain_action_case_link")
PW = "correct horse battery"
SERVICE_ONLY = "CHECK ((actor_kind = 'SERVICE'::text))"

if URL:
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine, text
    from sqlalchemy.exc import DBAPIError
    from test_s1_bindings_postgres import imported
    from test_w202_cold_replay_postgres import chain  # noqa: F401 - the cold replay behind `cold`
    from test_w401_work_service_postgres import ACTOR, PRINCIPAL, event, incident, oprec, plan, record, request
    from test_w502_domain_intent_postgres import (action_body, cold, create, head_event, intent,  # noqa: F401
                                                  intent_body, link_body, w4_request)

    import pg_harness
    from assetops_backend.accounts.adapters.postgres_account_store import PostgresAccountStore
    from assetops_backend.accounts.service import AccountService
    from assetops_backend.config import load_feature_flags
    from assetops_backend.main import create_app
    from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore
    from assetops_backend.work.composition import build_work_service
    from assetops_backend.work.model import PersonActor


def _now() -> datetime:
    return datetime.now(timezone.utc)


class People:
    """Real accounts in one tenant (Postgres account store), each signed in once."""

    def __init__(self, engine, tenant_id: UUID) -> None:
        self.store = PostgresAccountStore(URL)
        self.svc = AccountService(self.store, clock=_now)
        with engine.connect() as c:
            self.slug = c.execute(text("SELECT slug FROM tenant WHERE id = :t"), {"t": tenant_id}).scalar_one()
        email = f"exec-{uuid4().hex[:8]}@{self.slug}.example"
        self.svc.onboard_create(self.slug, email, "Exec", PW, executive=True)
        self.boss = self.svc.sign_in(email, PW).principal

    def person(self, role: str, site_code: str | None) -> tuple[UUID, str, UUID]:
        email = f"p-{uuid4().hex[:8]}@{self.slug}.example"
        pid = self.svc.onboard_create(self.slug, email, "Person", PW, executive=False)
        self.svc.grant(self.boss, pid, role, site_code)
        signed = self.svc.sign_in(email, PW)
        return pid, signed.token, signed.principal.session_id

    def close(self) -> None:
        self.store.dispose()


@pytest.fixture()
def db():
    """A fresh migrated database for one test (cold tests get theirs from the replay fixture)."""
    pg_harness.fresh_database()
    engine = create_engine(URL)
    store = PostgresFoundationStore(URL)
    yield engine, store
    pg_harness.dispose(store)
    engine.dispose()


def _seed_tenant(engine, slug: str) -> UUID:
    tid = uuid4()
    with engine.begin() as c:
        c.execute(text("INSERT INTO tenant (id, slug, name, created_at) VALUES (:id, :s, :s, now())"),
                  {"id": tid, "s": slug})
    return tid


def _constraint(engine, table: str, name: str) -> str | None:
    with engine.connect() as c:
        return c.execute(text("SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid = CAST(:t AS "
                              "regclass) AND conname = :n"), {"t": table, "n": name}).scalar_one_or_none()


def _has_person_column(engine, table: str) -> bool:
    with engine.connect() as c:
        return c.execute(text("SELECT count(*) FROM information_schema.columns WHERE table_name = :t AND "
                              "column_name = 'person_id'"), {"t": table}).scalar_one() == 1


def _fails(engine, sql: str, params: dict, constraint: str) -> None:
    with pytest.raises(DBAPIError, match=constraint):
        with engine.begin() as c:
            c.execute(text(sql), params)


def _copy_sql(engine, table: str) -> tuple[str, dict]:
    """An INSERT copying one existing row of `table` verbatim, with the actor columns as parameters. A CHECK is
    evaluated before any unique index or foreign key, so a planted actor fails on its own constraint."""
    with engine.connect() as c:
        row = dict(c.execute(text(f"SELECT * FROM {table} LIMIT 1")).mappings().one())
    cols = [k for k in row if k not in ("actor_kind", "actor_id", "person_id")]
    sql = (f"INSERT INTO {table} ({', '.join(cols)}, actor_kind, actor_id, person_id) SELECT {', '.join(cols)}, "
           f":kind, :aid, CAST(:pid AS uuid) FROM {table} WHERE id = :id")
    return sql, {"id": row["id"]}


def _all_nine(c0) -> dict:
    """SERVICE rows in all nine tables through today's services, on the cold Site."""
    case = w4_request(c0, "p3c1a-req-0001")
    work = c0.work
    assert work.post_event(c0.t, c0.s, case["id"], event("ASSIGN", {"assignee": "crew"}, "p3c1a-ev-0001"),
                           PRINCIPAL)[0] == 201
    assert work.post_record(c0.t, c0.s, case["id"], record("p3c1a-rec-0001"), PRINCIPAL)[0] == 201
    assert work.post_plan(c0.t, c0.s, plan("p3c1a-plan-0001"), PRINCIPAL)[0] == 201
    assert work.post_operational_record(c0.t, c0.s, oprec("p3c1a-oprec-0001"), PRINCIPAL)[0] == 201
    status, action = create(c0, action_body(c0, "p3c1a-act-0001"))
    assert status == 201, action
    status, declared = intent(c0, action["id"], intent_body(c0, "p3c1a-int-0001"))
    assert status == 201, declared
    assert c0.svc.post_case_link(c0.t, c0.s, c0.code, action["id"],
                                 link_body(case["id"], case["revision"]["id"], head_event(c0, case["id"]),
                                           "p3c1a-lnk-0001"), PRINCIPAL)[0] == 201
    return {"case": case, "action": action, "intent": declared["intent_id"]}


# ---- the migration's shape -------------------------------------------------------------------------------------

def test_the_migration_chains_from_accounts_through_the_script_directory() -> None:
    from alembic.script import ScriptDirectory

    directory = ScriptDirectory.from_config(pg_harness._alembic("postgresql://unused/unused_test"))
    pg_harness.alembic_head()  # one head, whichever it is
    script = directory.get_revision(MIG.revision)
    assert script is not None and script.down_revision == MIG.down_revision
    assert directory.get_revision(MIG.down_revision) is not None
    accounts = next(r for r in directory.walk_revisions() if Path(r.path).name.endswith("_operator_accounts.py"))
    assert accounts.revision in {r.revision for r in directory.iterate_revisions(MIG.revision, "base")}
    assert MIG.TABLES == TABLES  # child-first lock order (P2)


def test_every_table_has_the_column_the_fk_and_the_person_check(db) -> None:
    engine, _ = db
    for table in TABLES:
        assert _has_person_column(engine, table), table
        assert _constraint(engine, table, f"{table}_person_fk") == (
            "FOREIGN KEY (tenant_id, person_id) REFERENCES operator_account(tenant_id, id)"), table
        check = _constraint(engine, table, f"{table}_person_actor")
        assert check is not None and "person:" in check and "USER" in check, table
    for table in DOMAIN:
        assert _constraint(engine, table, f"{table}_actor_kind_check") == (
            "CHECK ((actor_kind = ANY (ARRAY['SERVICE'::text, 'USER'::text])))"), table


# ---- planted rows ----------------------------------------------------------------------------------------------

def test_each_table_refuses_a_planted_actor(cold) -> None:  # noqa: F811
    _all_nine(cold)
    people = People(cold.engine, cold.t)
    try:
        pid, _, _ = people.person("SITE_MANAGER", cold.code)
        other = uuid4()
        for table in TABLES:
            sql, params = _copy_sql(cold.engine, table)
            check = f"{table}_person_actor"
            _fails(cold.engine, sql, {**params, "kind": "USER", "aid": PRINCIPAL, "pid": None}, check)
            _fails(cold.engine, sql, {**params, "kind": "SERVICE", "aid": f"person:{pid}", "pid": str(pid)}, check)
            _fails(cold.engine, sql, {**params, "kind": "USER", "aid": f"person:{other}", "pid": str(pid)}, check)
    finally:
        people.close()


def test_each_table_refuses_a_person_of_another_tenant(cold) -> None:  # noqa: F811
    """The FK: each command, run with a valid body as a person of another tenant, fails on `<t>_person_fk`."""
    made = _all_nine(cold)
    beta = _seed_tenant(cold.engine, "beta")
    people = People(cold.engine, beta)
    try:
        pid, _, sid = people.person("FIELD_TECHNICIAN", None)
        stranger = PersonActor(pid, sid, "SITE_MANAGER")
        case, action = made["case"], made["action"]
        work, t, s = cold.work, cold.t, cold.s
        no_actor = {k: v for k, v in incident("p3c1a-x-case").items() if k != "actor"}

        def body(b: dict) -> dict:
            return {k: v for k, v in b.items() if k != "actor"}

        calls = {
            "work_case": lambda: work.create_case(t, s, no_actor, None, person=stranger),
            "work_event": lambda: work.post_event(t, s, case["id"], body(event("COMMENT", {"text": "x"}, "p3c1a-x-ev")),
                                                  None, person=stranger),
            "work_case_revision": lambda: work.post_revision(t, s, case["id"], {
                "supersedes_revision_id": case["revision"]["id"], "title": "t", "narrative": "n", "reason": "r",
                "occurred_at": incident()["occurred_at"], "idempotency_key": "p3c1a-x-rev"}, None, person=stranger),
            "maintenance_record": lambda: work.post_record(t, s, case["id"], body(record("p3c1a-x-rec")), None,
                                                           person=stranger),
            "maintenance_plan": lambda: work.post_plan(t, s, body(plan("p3c1a-x-plan")), None, person=stranger),
            "operational_record": lambda: work.post_operational_record(t, s, body(oprec("p3c1a-x-oprec")), None,
                                                                       person=stranger),
            "domain_action": lambda: cold.svc.create_action(t, s, cold.code, body(action_body(cold, "p3c1a-x-act")),
                                                            None, person=stranger),
            "domain_action_intent": lambda: cold.svc.post_intent(
                t, s, cold.code, action["id"], body(intent_body(cold, "p3c1a-x-int", supersedes=made["intent"])), None, person=stranger),
        }
        for table, call in calls.items():
            with pytest.raises(Exception, match=f"{table}_person_fk"):
                call()
        # A link to the current head: a second request, so the selection is new.
        second = w4_request(cold, "p3c1a-req-0002")
        with pytest.raises(Exception, match="domain_action_case_link_person_fk"):
            cold.svc.post_case_link(t, s, cold.code, action["id"], body(link_body(
                second["id"], second["revision"]["id"], head_event(cold, second["id"]), "p3c1a-x-lnk")), None,
                person=stranger)
    finally:
        people.close()


# ---- through create_app (P7): one work command, one domain command ---------------------------------------------

ZONE = ZoneInfo("Africa/Addis_Ababa")


def _entry(engine, key: str) -> dict:
    with engine.connect() as c:
        db_now = c.execute(text("SELECT clock_timestamp()")).scalar_one()
    taken = (db_now - timedelta(hours=1)).astimezone(ZONE).strftime("%Y-%m-%dT%H:%M")
    return {"entry": "METER_READING", "value": "1520", "taken_at_local": taken, "ticket_reference": None,
            "idempotency_key": key}


def test_create_app_records_a_work_entry_under_the_person(db, monkeypatch) -> None:
    engine, store = db
    site = imported(store)
    people = People(engine, site.tenant.id)
    try:
        pid, token, sid = people.person("FIELD_TECHNICIAN", None)
        monkeypatch.setenv("DATABASE_URL", URL)
        monkeypatch.delenv("ASSETOPS_REQUIRE_PERSON", raising=False)
        api = TestClient(create_app(load_feature_flags(), accounts=people.svc,
                                    operational_entry_principal=lambda r, c: "service:operator-entry"))
        path = "/api/sites/KOBO-001/work/operational-entries"
        signed = api.post(path, json=_entry(engine, "oprec-entry-" + "a" * 32),
                          headers={"cookie": f"assetops_session={token}"})
        assert signed.status_code == 201, signed.text
        unsigned = api.post(path, json=_entry(engine, "oprec-entry-" + "b" * 32))
        assert unsigned.status_code == 201, unsigned.text  # switch off: today's path
        with engine.connect() as c:
            rows = {r["idempotency_key"]: r for r in c.execute(text(
                "SELECT idempotency_key, actor_kind, actor_id, person_id, attestation, authorization_basis "
                "FROM operational_record")).mappings()}
        person = rows["oprec-entry-" + "a" * 32]
        assert (person["actor_kind"], person["actor_id"], person["person_id"]) == ("USER", f"person:{pid}", pid)
        assert person["attestation"] == f"person={pid};session={sid};role=FIELD_TECHNICIAN"
        assert person["authorization_basis"] == "PERSON_ROLE:FIELD_TECHNICIAN"
        service = rows["oprec-entry-" + "b" * 32]
        assert (service["actor_kind"], service["actor_id"], service["person_id"]) == (
            "SERVICE", "service:operator-entry", None)
        api.close()
        monkeypatch.setenv("ASSETOPS_REQUIRE_PERSON", "on")  # read once by create_app (R10)
        strict = TestClient(create_app(load_feature_flags(), accounts=people.svc,
                                       operational_entry_principal=lambda r, c: "service:operator-entry"))
        refused = strict.post(path, json=_entry(engine, "oprec-entry-" + "c" * 32))
        assert refused.status_code == 401 and refused.json()["detail"]["code"] == "PERSON_REQUIRED"
        strict.close()
    finally:
        people.close()


def test_create_app_records_a_domain_action_under_the_person(cold, monkeypatch) -> None:  # noqa: F811
    people = People(cold.engine, cold.t)
    try:
        pid, token, sid = people.person("SITE_MANAGER", cold.code)
        monkeypatch.setenv("DATABASE_URL", URL)
        monkeypatch.delenv("ASSETOPS_REQUIRE_PERSON", raising=False)
        api = TestClient(create_app(load_feature_flags(), accounts=people.svc,
                                    domain_work_principal=lambda r, c: PRINCIPAL))
        body = {k: v for k, v in action_body(cold, "p3c1a-app-act-01").items() if k != "actor"}
        r = api.post(f"/api/sites/{cold.code}/domain-work/actions", json=body,
                     headers={"cookie": f"assetops_session={token}"})
        assert r.status_code == 201, r.text
        with cold.engine.connect() as c:
            row = c.execute(text("SELECT actor_kind, actor_id, person_id, attestation FROM domain_action WHERE "
                                 "idempotency_key = 'p3c1a-app-act-01'")).mappings().one()
        assert dict(row) == {"actor_kind": "USER", "actor_id": f"person:{pid}", "person_id": pid,
                             "attestation": f"person={pid};session={sid};role=SITE_MANAGER"}
        api.close()
    finally:
        people.close()


# ---- upgrade refusal and downgrade (P1, P2) --------------------------------------------------------------------

def test_downgrade_refused_with_a_person_row_then_down_up_and_the_upgrade_refusal(db) -> None:
    from alembic import command

    engine, store = db
    site = imported(store)
    t, s = site.tenant.id, site.site.id
    people = People(engine, t)
    work = build_work_service(URL)
    try:
        pid, _, sid = people.person("SITE_MANAGER", "KOBO-001")
        status, case = work.create_case(t, s, incident("p3c1a-dn-case"), PRINCIPAL)
        assert status == 201, case
        comment = {k: v for k, v in event("COMMENT", {"text": "x"}, "p3c1a-dn-ev").items() if k != "actor"}
        assert work.post_event(t, s, case["id"], comment, None, person=PersonActor(pid, sid, "SITE_MANAGER"))[0] == 201
        cfg = pg_harness._alembic(URL)
        with pytest.raises(Exception, match=f"{MIG.DOWNGRADE_REFUSED} work_event"):
            command.downgrade(cfg, MIG.down_revision)
        with engine.begin() as c:  # TRUNCATE is not a row DELETE: the append-only triggers do not fire
            c.execute(text("TRUNCATE work_event CASCADE"))
        command.downgrade(cfg, MIG.down_revision)
        for table in TABLES:
            assert not _has_person_column(engine, table), table
            assert _constraint(engine, table, f"{table}_person_fk") is None
        for table in DOMAIN:  # the exact 0033 checks, under their names
            assert _constraint(engine, table, f"{table}_actor_kind_check") == SERVICE_ONLY, table
        with engine.begin() as c:  # before this migration a USER work row without a person is still possible: plant one
            c.execute(text(
                "INSERT INTO work_event (id, tenant_id, site_id, case_id, kind, payload, occurred_at, actor_kind, "
                "actor_id, authorization_basis, attestation, idempotency_key, payload_sha256) VALUES (:id, :t, :s, "
                ":c, 'COMMENT', '{}', now(), 'USER', 'user-1', 'grant', 'I attest', 'p3c1a-planted', :h)"),
                {"id": uuid4(), "t": t, "s": s, "c": case["id"], "h": "0" * 64})
        with pytest.raises(Exception, match=f"{MIG.UPGRADE_REFUSED} work_event"):
            command.upgrade(cfg, "head")
        with engine.begin() as c:
            c.execute(text("TRUNCATE work_event CASCADE"))
        command.upgrade(cfg, "head")
        pg_harness.assert_at_head(engine)
        for table in TABLES:
            assert _has_person_column(engine, table), table
    finally:
        work._store.dispose()
        people.close()
