"""3C1b (`specs/3C1-person-on-commands/spec.md` §5; R2-R4, R7, R8, P1-P3, P7): the person migration on `action_event`,
its constraints and coupling, the person path over the real stores, and the `create_app` wiring.

The migration's ids are read from its module (D-3A1.12: 0071, re-pointed at merge preparation). The
accept, apply (APPLIED and FAILED) and observe run through the real action router over the real
`PostgresActionStore`, the S1 publish and the Postgres account store, as the S6 tests do (Q-3C1b-3: no harness
composes Actions inside `create_app`); `create_app` is proved to hand the person inputs to the action router.
Needs `ASSETOPS_TEST_DATABASE_URL` naming a `*_test` database; run through `tools/heavy-slot.sh --db`.
"""
from __future__ import annotations

import importlib.util
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from test_s4_finding_store_postgres import URL, CaseRunner, run_case  # noqa: F401
from test_s6_action_store_postgres import CASES, T_ACCEPT, Harness, runner  # noqa: F401

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

_PATH = next((Path(__file__).resolve().parents[1] / "migrations" / "versions").glob("*_person_on_actions.py"))
_SPEC = importlib.util.spec_from_file_location("m3c1b", _PATH)
MIG = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(MIG)

PW = "correct horse battery"
FIXTURE = "D-action-records-v1"
T_APPLY = T_ACCEPT + timedelta(hours=1)
EFFECTIVE = T_ACCEPT + timedelta(days=1)
#: The texts `pg_get_constraintdef` prints, written out here (W2): before (0016/0019) and after this migration.
BEFORE = {
    "action_event_actor_kind_check": "CHECK ((actor_kind = 'SYSTEM'::text))",
    "action_event_actor_id_check": "CHECK ((actor_id ~ '^service:[a-z0-9-]+$'::text))",
    "action_event_source_channel_check":
        "CHECK ((source_channel = ANY (ARRAY['SYSTEM_DEMONSTRATION_API'::text, 'SYSTEM_JOB'::text])))",
}
AFTER = {
    "action_event_actor_kind_check": "CHECK ((actor_kind = ANY (ARRAY['SYSTEM'::text, 'USER'::text])))",
    "action_event_actor_id_check":
        "CHECK (((actor_id ~ '^service:[a-z0-9-]+$'::text) OR (actor_id ~ '^person:[0-9a-f-]{36}$'::text)))",
    "action_event_source_channel_check": "CHECK ((source_channel = ANY (ARRAY['SYSTEM_DEMONSTRATION_API'::text, "
                                         "'SYSTEM_JOB'::text, 'PERSON_API'::text])))",
}

if URL:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError
    from test_s1_bindings_postgres import engine, imported, store  # noqa: F401
    from test_s6_action_apply_postgres import Registry, current_foundation

    import pg_harness
    from assetops_backend.accounts.adapters.postgres_account_store import PostgresAccountStore
    from assetops_backend.accounts.service import AccountService
    from assetops_backend.action_api import build_action_router
    from assetops_backend.actions.composition import foundation_publish
    from assetops_backend.config import load_feature_flags
    from assetops_backend.main import create_app


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

    def person(self, role: str, site_code: str | None) -> tuple[UUID, str]:
        email = f"p-{uuid4().hex[:8]}@{self.slug}.example"
        pid = self.svc.onboard_create(self.slug, email, "Person", PW, executive=False)
        self.svc.grant(self.boss, pid, role, site_code)
        return pid, self.svc.sign_in(email, PW).token

    def close(self) -> None:
        self.store.dispose()


def _seed_tenant(engine, slug: str) -> UUID:
    tid = uuid4()
    with engine.begin() as c:
        c.execute(text("INSERT INTO tenant (id, slug, name, created_at) VALUES (:id, :s, :s, now())"),
                  {"id": tid, "s": slug})
    return tid


class PersonHarness(Harness):
    """The S6 harness (real store, grants file, S1 publish) with the action router given the account service."""

    def __init__(self, runner, accounts: AccountService) -> None:
        super().__init__(runner)
        self.service.publish = foundation_publish(Registry(runner))
        app = FastAPI()
        app.include_router(build_action_router(
            self.service, {"KOBO-001": ("KOBO-001", runner.tenant, runner.site)}.get,
            gate=lambda c, t, s: (True, "test gate"), accounts=accounts, require_person=False,
            accounts_unavailable=()))
        self.app = app
        self.client = TestClient(app)

    def signed(self, token: str) -> TestClient:
        return TestClient(self.app, headers={"cookie": f"assetops_session={token}"})


def _events(engine) -> list[dict]:
    with engine.connect() as c:
        return [dict(r) for r in c.execute(text(
            "SELECT id, kind, actor_kind, actor_id, person_id, source_channel, authorization_basis, "
            "triggering_fixture, failure_code, payload FROM action_event ORDER BY recorded_at, id")).mappings()]


def _constraint(engine, name: str) -> str | None:
    with engine.connect() as c:
        return c.execute(text("SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid = "
                              "'action_event'::regclass AND conname = :n"), {"n": name}).scalar_one_or_none()


def _has_person_column(engine) -> bool:
    with engine.connect() as c:
        return c.execute(text("SELECT count(*) FROM information_schema.columns WHERE table_name = 'action_event' "
                              "AND column_name = 'person_id'")).scalar_one() == 1


def _copy(engine, source_id, **cols) -> None:
    """INSERT a copy of one stored OBSERVED event under a new id and key, with the given columns overridden."""
    with engine.connect() as c:
        names = [r[0] for r in c.execute(text(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'action_event' "
            "ORDER BY ordinal_position"))]
    fixed = {"id": "gen_random_uuid()", "idempotency_key": "'copy-' || md5(random()::text)"}
    values = [fixed[n] if n in fixed else (f":{n}" if n in cols else n) for n in names]
    casts = {"person_id": "uuid"}
    values = [f"CAST({v} AS {casts[n]})" if n in casts and n in cols else v for n, v in zip(names, values)]
    with engine.begin() as c:
        c.execute(text(f"INSERT INTO action_event ({', '.join(names)}) SELECT {', '.join(values)} FROM action_event "
                       "WHERE id = :source"), {"source": source_id, **cols})


def _system_observed(runner) -> tuple[Harness, str, UUID]:
    """A SYSTEM accept and observe on F01 (today's path); returns the OBSERVED event id to copy."""
    run_case(runner, CASES["F01"])
    h = Harness(runner)
    finding = h.findings()["2026-10-06"]
    proposal = h.recommendation(finding).json()["proposal"]
    made = h.accept(finding, proposal, idempotency_key="sys-accept-0001")
    assert made.status_code == 201, made.text
    action_id = made.json()["action"]["action_id"]
    observed = h.observe(action_id, T_ACCEPT, "sys-observe-0001")
    assert observed.status_code == 201, observed.text
    return h, action_id, UUID(observed.json()["event"]["id"])


# ---- the constraints and the coupling ----------------------------------------------------------------------------

def test_the_constraints_exist_with_their_definitions(engine) -> None:  # noqa: F811
    assert _has_person_column(engine)
    for name, definition in AFTER.items():
        assert _constraint(engine, name) == definition, name
    assert _constraint(engine, "action_event_person_fk") == (
        "FOREIGN KEY (tenant_id, person_id) REFERENCES operator_account(tenant_id, id)")
    assert "person_id IS NOT NULL" in _constraint(engine, "action_event_person_actor")
    coupling = _constraint(engine, "action_event_person_coupling")
    assert "PERSON_API" in coupling and "PERSON_ROLE:[A-Z_]+$" in coupling
    assert _constraint(engine, "action_event_evaluator_job") is not None  # unchanged, still there


def test_each_planted_actor_fails_on_its_constraint(runner) -> None:
    h, _, observed = _system_observed(runner)
    people = People(runner.engine, runner.tenant)
    other = People(runner.engine, _seed_tenant(runner.engine, f"beta-{uuid4().hex[:6]}"))
    try:
        pid, _ = people.person("SITE_MANAGER", "KOBO-001")
        stranger, _ = other.person("FIELD_TECHNICIAN", None)
        good = {"actor_kind": "USER", "actor_id": f"person:{pid}", "person_id": str(pid),
                "source_channel": "PERSON_API", "authorization_basis": "PERSON_ROLE:SITE_MANAGER"}
        _copy(runner.engine, observed, **good)  # a well-formed person row is admitted
        plants = [
            ({**good, "person_id": None}, "action_event_person_actor"),  # USER without a person
            ({"person_id": str(pid)}, "action_event_person_actor"),  # a person on a SYSTEM row
            ({**good, "actor_id": f"person:{uuid4()}"}, "action_event_person_actor"),  # mismatched actor_id
            ({**good, "source_channel": "SYSTEM_DEMONSTRATION_API"}, "action_event_person_coupling"),
            ({**good, "authorization_basis": "SYSTEM_DEMONSTRATION_CAPABILITY: x"}, "action_event_person_coupling"),
            ({"source_channel": "PERSON_API"}, "action_event_person_coupling"),  # SYSTEM on the person channel
            ({**good, "actor_id": "person:not-a-uuid", "person_id": None}, "action_event_actor_id_check"),
            ({**good, "actor_id": f"person:{stranger}", "person_id": str(stranger)}, "action_event_person_fk"),
        ]
        for cols, constraint in plants:
            with pytest.raises(DBAPIError, match=constraint):
                _copy(runner.engine, observed, **cols)
    finally:
        h.close()
        people.close()
        other.close()


# ---- the person path over the real stores ------------------------------------------------------------------------

def test_accept_apply_and_observe_are_stored_under_the_person(runner) -> None:
    run_case(runner, CASES["F01"])
    people = People(runner.engine, runner.tenant)
    h = PersonHarness(runner, people.svc)
    try:
        peter, peter_token = people.person("SITE_MANAGER", "KOBO-001")
        fatma, fatma_token = people.person("FIELD_TECHNICIAN", None)
        sam, sam_token = people.person("SITE_MANAGER", "KOBO-001")
        finding = h.findings()["2026-10-06"]
        proposal = h.recommendation(finding).json()["proposal"]
        body = {"revision_id": proposal["finding_revision_id"], "recommendation_key": proposal["recommendation_key"],
                "foundation_revision_id": proposal["foundation_revision_id"],
                "proposed_value": proposal["proposed_value"], "idempotency_key": "person-accept-01"}
        path = f"/api/sites/KOBO-001/findings/{finding}/recommendation/accept"
        made = h.signed(peter_token).post(path, json=body)
        assert made.status_code == 201, made.text
        assert made.json()["event"]["actor"]["label"] is None  # Q-3C1b-1
        second = h.signed(sam_token).post(path, json=body)  # R2: never a replay of Peter's event
        assert second.status_code == 409, second.text
        assert second.json()["detail"]["code"] == "ACTION_ACCEPTANCE_CONFLICT"
        action_id = made.json()["action"]["action_id"]
        h.clock.at = T_APPLY
        expected = current_foundation(h, action_id)
        apply_path = f"/api/sites/KOBO-001/actions/{action_id}/apply"
        apply_body = {"expected_foundation_revision_id": expected, "value": "15",
                      "effective_from": EFFECTIVE.isoformat(), "idempotency_key": "person-apply-01"}
        failed = h.signed(peter_token).post(apply_path, json={**apply_body, "value": "12",
                                                               "idempotency_key": "person-apply-00"})
        assert failed.status_code == 422 and failed.json()["detail"]["code"] == "ACTION_VALUE_INVALID"
        applied = h.signed(peter_token).post(apply_path, json=apply_body)
        assert applied.status_code == 201, applied.text
        change = applied.json()["change"]
        assert change["label"] is None and change["statement"] is None
        read = h.client.get(f"/api/sites/KOBO-001/foundation/changes/{change['change_id']}").json()["change"]
        assert read["label"] is None and read["statement"] is None
        observed = h.signed(fatma_token).post(f"/api/sites/KOBO-001/actions/{action_id}/observations", json={
            "observation_code": "DEMO_REVIEW_NOTE", "occurred_at": T_APPLY.isoformat(),
            "idempotency_key": "person-observe-01"})
        assert observed.status_code == 201, observed.text
        rows = {r["kind"]: r for r in _events(runner.engine)}
        expected_rows = {"ACCEPTED": (peter, "SITE_MANAGER"), "FAILED": (peter, "SITE_MANAGER"),
                         "APPLIED": (peter, "SITE_MANAGER"), "OBSERVED": (fatma, "FIELD_TECHNICIAN")}
        assert set(rows) == set(expected_rows)
        for kind, (pid, role) in expected_rows.items():
            row = rows[kind]
            assert (row["actor_kind"], row["actor_id"], row["person_id"]) == ("USER", f"person:{pid}", pid), kind
            assert row["source_channel"] == "PERSON_API" and row["authorization_basis"] == f"PERSON_ROLE:{role}"
            assert row["triggering_fixture"] == FIXTURE, kind  # R3: the grant file still supplies it
            assert row["payload"]["actor_id"] == f"person:{pid}", kind  # R2
        assert rows["FAILED"]["failure_code"] == "ACTION_VALUE_INVALID"
        events = h.client.get(f"/api/sites/KOBO-001/actions/{action_id}/events").json()["events"]
        assert len(events) == 4 and all("person_id" not in e for e in events)
        assert {e["actor"]["label"] for e in events} == {None}
    finally:
        h.close()
        people.close()


# ---- create_app hands the person inputs to the action router (P7) -----------------------------------------------

def test_create_app_wires_the_person_step_into_the_action_routes(store, engine, monkeypatch) -> None:  # noqa: F811
    site = imported(store)
    people = People(engine, site.tenant.id)
    other = People(engine, _seed_tenant(engine, f"beta-{uuid4().hex[:6]}"))
    try:
        _, peter_token = people.person("SITE_MANAGER", "KOBO-001")
        _, stranger_token = other.person("FIELD_TECHNICIAN", None)
        monkeypatch.setenv("DATABASE_URL", URL)
        monkeypatch.delenv("ASSETOPS_REQUIRE_PERSON", raising=False)
        path = f"/api/sites/KOBO-001/findings/{uuid4()}/recommendation/accept"
        api = TestClient(create_app(load_feature_flags(), accounts=people.svc))
        signed = api.post(path, json={}, headers={"cookie": f"assetops_session={peter_token}"})
        assert signed.status_code == 404 and signed.json()["detail"]["code"] == "FINDING_NOT_FOUND"
        stranger = api.post(path, json={}, headers={"cookie": f"assetops_session={stranger_token}"})
        unknown = api.post(path.replace("KOBO-001", "NOPE-001"), json={})
        assert stranger.status_code == 404
        assert stranger.content == unknown.content.replace(b"NOPE-001", b"KOBO-001")
        api.close()
        monkeypatch.setenv("ASSETOPS_REQUIRE_PERSON", "on")  # read once by create_app (R10)
        strict = TestClient(create_app(load_feature_flags(), accounts=people.svc))
        refused = strict.post(path, json={})
        assert refused.status_code == 401 and refused.json()["detail"]["code"] == "PERSON_REQUIRED"
        strict.close()
    finally:
        people.close()
        other.close()


# ---- downgrade refusal, down and up, and the upgrade refusal (P1, P2) --------------------------------------------
# Last in the module: it moves the shared module database down and back to head.

def test_downgrade_refused_with_a_person_row_then_down_up_and_the_upgrade_refusal(runner) -> None:
    from alembic import command

    h, _, observed = _system_observed(runner)
    people = People(runner.engine, runner.tenant)
    engine = runner.engine
    try:
        pid, _ = people.person("SITE_MANAGER", "KOBO-001")
        _copy(engine, observed, actor_kind="USER", actor_id=f"person:{pid}", person_id=str(pid),
              source_channel="PERSON_API", authorization_basis="PERSON_ROLE:SITE_MANAGER")
        cfg = pg_harness._alembic(URL)
        with pytest.raises(Exception, match=f"{MIG.DOWNGRADE_REFUSED} action_event"):
            command.downgrade(cfg, MIG.down_revision)

        def remove(where: str) -> None:  # the append-only trigger blocks a row DELETE; lift it for this test only
            with engine.begin() as c:
                c.execute(text("ALTER TABLE action_event DISABLE TRIGGER action_event_append_only"))
                c.execute(text(f"DELETE FROM action_event WHERE {where}"))
                c.execute(text("ALTER TABLE action_event ENABLE TRIGGER action_event_append_only"))

        remove("person_id IS NOT NULL")
        command.downgrade(cfg, MIG.down_revision)
        assert not _has_person_column(engine)
        for name in ("action_event_person_fk", "action_event_person_actor", "action_event_person_coupling"):
            assert _constraint(engine, name) is None, name
        for name, definition in BEFORE.items():  # the exact 0016/0019 texts, under their names
            assert _constraint(engine, name) == definition, name
        with engine.begin() as c:  # before this migration a USER row cannot exist; force one past the kind check
            c.execute(text("ALTER TABLE action_event DROP CONSTRAINT action_event_actor_kind_check"))
        _copy(engine, observed, actor_kind="USER")
        with pytest.raises(Exception, match=f"{MIG.UPGRADE_REFUSED} action_event"):
            command.upgrade(cfg, "head")
        remove("actor_kind = 'USER'")
        with engine.begin() as c:
            c.execute(text("ALTER TABLE action_event ADD CONSTRAINT action_event_actor_kind_check "
                           "CHECK (actor_kind = 'SYSTEM')"))
        command.upgrade(cfg, "head")
        pg_harness.assert_at_head(engine)
        assert _has_person_column(engine)
        for name, definition in AFTER.items():
            assert _constraint(engine, name) == definition, name
    finally:
        h.close()
        people.close()
