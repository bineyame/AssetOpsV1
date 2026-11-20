"""3C0a (spec §2, §4.1, §9; R2, R5, R6, R11, D-3C0A.11, MB1, MB2): migration 0062 and the Postgres account store.

Needs `ASSETOPS_TEST_DATABASE_URL` naming a `*_test` database (the harness routes the run to its own clone); skipped
otherwise. Run through `tools/heavy-slot.sh`.
"""
from __future__ import annotations

import hashlib
import os
import threading
import time
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError
    from test_s1_bindings_postgres import engine, store  # noqa: F401

    import pg_harness
    from assetops_backend.accounts.adapters.postgres_account_store import PostgresAccountStore
    from assetops_backend.accounts.model import Account, AccountRefused, GrantRow
    from assetops_backend.accounts.passwords import hash_password
    from assetops_backend.accounts.service import AccountService
    from assetops_backend.accounts.store import StoreConflict

PW = "correct horse battery"
EXEC = "OPERATOR_EXECUTIVE"
T0 = datetime(2026, 11, 20, 8, 0, tzinfo=timezone.utc)
TABLES = ("operator_account", "account_credential", "account_status", "role_grant", "operator_session",
          "sign_in_attempt")
APPEND_ONLY = ("operator_account", "account_credential", "account_status", "role_grant")


class Clock:
    def __init__(self, now: datetime = T0) -> None:
        self.now = now

    def __call__(self) -> datetime:
        return self.now


def seed_tenant(engine, slug: str, name: str | None = None) -> UUID:
    tid = uuid4()
    with engine.begin() as c:
        c.execute(text("INSERT INTO tenant (id, slug, name, created_at) VALUES (:id, :s, :n, :at)"),
                  {"id": tid, "s": slug, "n": name or slug.title(), "at": T0})
    return tid


def seed_site(engine, tenant_id: UUID, code: str) -> UUID:
    sid = uuid4()
    with engine.begin() as c:
        c.execute(text(
            "INSERT INTO site (id, tenant_id, site_code, site_code_key, name, site_type, timezone, lifecycle, origin, "
            "proposed_source_mode, created_at) VALUES (:id, :t, :c, lower(:c), :c, 'MINIGRID', 'UTC', 'ACTIVE', "
            "'IMPORTED', 'SIMULATED', :at)"), {"id": sid, "t": tenant_id, "c": code, "at": T0})
    return sid


@pytest.fixture()
def accounts(store, engine):  # noqa: F811 - `store` empties the tenant closure, these six tables included
    owned = PostgresAccountStore(URL)
    yield owned
    owned.dispose()


@pytest.fixture()
def world(accounts, engine):  # noqa: F811
    clock = Clock()
    svc = AccountService(accounts, clock=clock)
    acme = seed_tenant(engine, "acme", "Acme Power")
    beta = seed_tenant(engine, "beta", "Beta Cold")
    site = seed_site(engine, acme, "KOBO-001")
    beta_site = seed_site(engine, beta, "BETA-001")
    exec_id = svc.onboard_create("acme", "amina@acme.example", "Amina", PW, executive=True)
    return dict(svc=svc, clock=clock, acme=acme, beta=beta, site=site, beta_site=beta_site, exec_id=exec_id)


def _count(engine, table: str) -> int:  # noqa: F811
    with engine.connect() as c:
        return c.execute(text(f"SELECT count(*) FROM {table}")).scalar_one()


def _refused_sql(engine, sql: str, params: dict | None = None) -> None:  # noqa: F811
    with pytest.raises(DBAPIError):
        with engine.begin() as c:
            c.execute(text(sql), params or {})


# --- the schema -------------------------------------------------------------------------------------------------

def test_the_six_tables_their_triggers_and_indexes_exist(engine) -> None:  # noqa: F811
    with engine.connect() as c:
        for table in TABLES:
            assert c.execute(text("SELECT to_regclass(:t)"), {"t": table}).scalar_one() is not None, table
        triggers = {(r[0], r[1]) for r in c.execute(text(
            "SELECT tgrelid::regclass::text, tgname FROM pg_trigger WHERE NOT tgisinternal "
            "AND tgrelid::regclass::text = ANY(:t)"), {"t": list(TABLES)})}
        indexes = {r[0] for r in c.execute(text("SELECT indexname FROM pg_indexes WHERE tablename = ANY(:t)"),
                                           {"t": list(TABLES)})}
    assert triggers == {(t, f"{t}_immutable") for t in APPEND_ONLY} | {
        ("role_grant", "role_grant_removal_check"), ("operator_session", "operator_session_revoke"),
        ("sign_in_attempt", "sign_in_attempt_no_update")}
    assert {"account_credential_person", "account_status_person", "role_grant_one_removal", "role_grant_tenant_at",
            "role_grant_person", "operator_session_person", "sign_in_attempt_email", "sign_in_attempt_at"} <= indexes


def test_the_record_tables_are_append_only(world, engine) -> None:  # noqa: F811
    for table in APPEND_ONLY:
        assert _count(engine, table) == 1
        _refused_sql(engine, f"UPDATE {table} SET tenant_id = tenant_id")
        _refused_sql(engine, f"DELETE FROM {table}")
        assert _count(engine, table) == 1


def test_sign_in_attempt_is_insert_and_purge(world, engine) -> None:  # noqa: F811
    svc = world["svc"]
    svc.sign_in("amina@acme.example", PW)
    _refused_sql(engine, "UPDATE sign_in_attempt SET succeeded = succeeded")
    old, recent = uuid4(), uuid4()
    with engine.begin() as c:
        for rid, age in ((old, 31), (recent, 29)):
            c.execute(text("INSERT INTO sign_in_attempt (id, email_key_sha256, at, succeeded, person_id) "
                           "VALUES (:id, :k, :at, false, NULL)"),
                      {"id": rid, "k": "f" * 64, "at": T0 - timedelta(days=age)})
    world["clock"].now = T0 + timedelta(minutes=1)
    svc.sign_in("amina@acme.example", PW)  # its insert purges rows older than 30 days
    with engine.connect() as c:
        ids = {r[0] for r in c.execute(text("SELECT id FROM sign_in_attempt"))}
    assert old not in ids and recent in ids and len(ids) == 3
    with engine.begin() as c:  # the purge DELETE itself is accepted by the database
        assert c.execute(text("DELETE FROM sign_in_attempt WHERE at < :b"), {"b": T0}).rowcount == 1


def test_a_session_allows_only_setting_revoked_at_once(world, engine) -> None:  # noqa: F811
    signed = world["svc"].sign_in("amina@acme.example", PW)
    h = hashlib.sha256(signed.token.encode("ascii")).hexdigest()
    _refused_sql(engine, "UPDATE operator_session SET expires_at = expires_at + interval '1 hour'")
    _refused_sql(engine, "UPDATE operator_session SET revoked_at = NULL")
    _refused_sql(engine, "DELETE FROM operator_session")
    with engine.begin() as c:
        assert c.execute(text("UPDATE operator_session SET revoked_at = :at WHERE token_sha256 = :h"),
                         {"at": T0 + timedelta(minutes=1), "h": h}).rowcount == 1
    _refused_sql(engine, "UPDATE operator_session SET revoked_at = :at", {"at": T0 + timedelta(minutes=2)})


def test_each_check_refuses_a_planted_row(world, engine) -> None:  # noqa: F811
    acme, exec_id, site = world["acme"], world["exec_id"], world["site"]
    grant = ("INSERT INTO role_grant (id, tenant_id, person_id, role, site_id, action, grant_id, by_person_id, "
             "by_service, at) VALUES (gen_random_uuid(), :t, :p, :role, :site, :action, :g, :byp, :bys, :at)")
    base = dict(t=acme, p=exec_id, role="ANALYST", site=None, action="GRANTED", g=None, byp=exec_id, bys=None, at=T0)
    for change in ({"role": "SITE_MANAGER"},                       # a Site manager without a Site
                   {"site": site},                                  # another role with a Site
                   {"g": uuid4()},                                  # a GRANTED row naming a grant
                   {"action": "REMOVED"},                           # a removal naming none
                   {"bys": "service:onboarding"},                   # both actors
                   {"byp": None},                                   # no actor
                   {"role": "ADMIN"}):
        _refused_sql(engine, grant, {**base, **change})
    account = ("INSERT INTO operator_account (id, tenant_id, email, email_key, display_name, created_at, created_by) "
               "VALUES (gen_random_uuid(), :t, :e, :k, 'X', :at, 'service:onboarding')")
    _refused_sql(engine, account, {"t": acme, "e": "X@acme.example", "k": "X@acme.example", "at": T0})
    _refused_sql(engine, account, {"t": acme, "e": " x@acme.example", "k": " x@acme.example", "at": T0})
    attempt = ("INSERT INTO sign_in_attempt (id, email_key_sha256, at, succeeded, person_id) "
               "VALUES (gen_random_uuid(), :k, :at, :ok, :p)")
    _refused_sql(engine, attempt, {"k": "amina@acme.example", "at": T0, "ok": False, "p": None})
    _refused_sql(engine, attempt, {"k": "a" * 64, "at": T0, "ok": True, "p": None})
    _refused_sql(engine, attempt, {"k": "a" * 64, "at": T0, "ok": False, "p": exec_id})
    _refused_sql(engine, "INSERT INTO account_credential (id, tenant_id, person_id, password_hash, set_at, set_by) "
                         "VALUES (gen_random_uuid(), :t, :p, 'plain', :at, 'service:onboarding')",
                 {"t": acme, "p": exec_id, "at": T0})


def test_the_removal_trigger_and_the_one_removal_index(world, engine) -> None:  # noqa: F811
    acme, exec_id = world["acme"], world["exec_id"]
    with engine.connect() as c:
        granted = c.execute(text("SELECT id FROM role_grant")).scalar_one()
    removal = ("INSERT INTO role_grant (id, tenant_id, person_id, role, site_id, action, grant_id, by_person_id, "
               "by_service, at) VALUES (gen_random_uuid(), :t, :p, :role, NULL, 'REMOVED', :g, NULL, "
               "'service:onboarding', :at)")
    _refused_sql(engine, removal, {"t": acme, "p": exec_id, "role": "ANALYST", "g": granted, "at": T0})  # mismatch
    with engine.begin() as c:
        c.execute(text(removal), {"t": acme, "p": exec_id, "role": EXEC, "g": granted, "at": T0})
    _refused_sql(engine, removal, {"t": acme, "p": exec_id, "role": EXEC, "g": granted, "at": T0})


def test_email_key_is_unique_across_tenants(world, accounts, engine) -> None:  # noqa: F811
    _refused_sql(engine, "INSERT INTO operator_account (id, tenant_id, email, email_key, display_name, created_at, "
                         "created_by) VALUES (gen_random_uuid(), :t, 'AMINA@acme.example', 'amina@acme.example', 'A', "
                         ":at, 'service:onboarding')", {"t": world["beta"], "at": T0})
    other = Account(uuid4(), world["beta"], "Amina@Acme.example", "Amina B")
    with pytest.raises(StoreConflict) as conflict:
        accounts.create_account(other, hash_password(PW), T0, "service:onboarding", None)
    assert conflict.value.code == "EMAIL_TAKEN"


# --- the port, round trip ---------------------------------------------------------------------------------------

def test_every_port_method_round_trips(world, accounts, engine) -> None:  # noqa: F811
    svc, clock, acme, site, exec_id = world["svc"], world["clock"], world["acme"], world["site"], world["exec_id"]
    assert accounts.tenant_by_slug("acme") == (acme, "Acme Power") and accounts.tenant_by_slug("nope") is None
    assert accounts.tenant(acme) == ("acme", "Acme Power") and accounts.tenant(uuid4()) is None
    assert accounts.site_id(acme, "kobo-001") == site and accounts.site_id(world["beta"], "KOBO-001") is None
    amina = accounts.account_by_email_key("amina@acme.example")
    assert amina == Account(exec_id, acme, "amina@acme.example", "Amina")
    assert accounts.account(acme, exec_id) == amina and accounts.account(world["beta"], exec_id) is None
    stored, set_at = accounts.current_credential(exec_id)
    assert stored.startswith("scrypt$") and set_at == T0
    assert accounts.current_credential(uuid4()) is None and accounts.current_status(uuid4()) is None
    assert accounts.current_status(exec_id) == "ACTIVE"

    clock.now = T0 + timedelta(seconds=1)
    joseph = svc.onboard_create("acme", "joseph@acme.example", "Joseph", PW, executive=False)
    clock.now = T0 + timedelta(seconds=2)
    svc.onboard_set_password("joseph@acme.example", "a newer passphrase")
    assert accounts.current_credential(joseph)[1] == T0 + timedelta(seconds=2)
    svc.onboard_set_status("joseph@acme.example", "DISABLED", "on leave")
    assert accounts.current_status(joseph) == "DISABLED"
    clock.now = T0 + timedelta(seconds=3)
    accounts.set_status(acme, joseph, "ACTIVE", None, clock.now, "service:onboarding")
    assert accounts.current_status(joseph) == "ACTIVE"

    executive = svc.resolve(svc.sign_in("amina@acme.example", PW).token)
    assert executive.has_role(EXEC) and executive.session_expires_at == clock.now + timedelta(hours=12)
    clock.now = T0 + timedelta(seconds=4)
    first = svc.grant(executive, joseph, "SITE_MANAGER", "KOBO-001")
    assert accounts.grant_row(acme, first.row_id) == first
    assert first.site_code == "KOBO-001" and first.by_display_name == "Amina"
    assert accounts.grant_row(world["beta"], first.row_id) is None
    assert accounts.held_grants(acme, joseph) == (first,)
    clock.now = T0 + timedelta(seconds=5)
    removal = svc.remove(executive, first.row_id)
    assert accounts.grant_row(acme, removal.row_id) == removal and accounts.held_grants(acme, joseph) == ()
    clock.now = T0 + timedelta(seconds=6)
    second = svc.grant(executive, joseph, "ANALYST", None)
    rows = accounts.grant_rows(acme)
    assert [r.row_id for r in rows] == [second.row_id, removal.row_id, first.row_id, rows[-1].row_id]
    assert rows[-1].by_service == "service:onboarding" and rows[-1].by_person_id is None
    people = accounts.people(acme)
    assert [(p.display_name, p.email, p.status) for p in people] == [
        ("Amina", "amina@acme.example", "ACTIVE"), ("Joseph", "joseph@acme.example", "ACTIVE")]
    assert people[1].grants == (second,)

    token = "t" * 43
    h = hashlib.sha256(token.encode("ascii")).hexdigest()
    sid = uuid4()
    accounts.add_session(sid, acme, joseph, h, clock.now, clock.now + timedelta(hours=12))
    row = accounts.session(h)
    assert (row.id, row.tenant_id, row.person_id, row.created_at, row.expires_at, row.revoked_at) == (
        sid, acme, joseph, clock.now, clock.now + timedelta(hours=12), None)
    accounts.revoke(h, clock.now + timedelta(minutes=1))
    accounts.revoke(h, clock.now + timedelta(minutes=2))  # a no-op once revoked
    assert accounts.session(h).revoked_at == clock.now + timedelta(minutes=1)
    assert accounts.session("0" * 64) is None

    with pytest.raises(StoreConflict) as held:
        accounts.add_grant(GrantRow(uuid4(), None, acme, joseph, "Joseph", "ANALYST", None, None, "GRANTED", exec_id,
                                    "Amina", None, clock.now), exec_id)
    assert held.value.code == "ROLE_ALREADY_HELD"


def test_guarded_attempt_counts_failures_and_locks(world, accounts) -> None:
    key = "c" * 64
    for minute in range(5):
        result = accounts.guarded_attempt(key, T0 + timedelta(minutes=minute), lambda: (False, uuid4()))
        assert (result.locked, result.succeeded, result.person_id) == (False, False, None)
    locked = accounts.guarded_attempt(key, T0 + timedelta(minutes=5), lambda: pytest.fail("verified while locked"))
    assert locked.locked and locked.retry_at == T0 + timedelta(minutes=15)
    ok = accounts.guarded_attempt(key, T0 + timedelta(minutes=15), lambda: (True, world["exec_id"]))
    assert (ok.locked, ok.succeeded, ok.person_id) == (False, True, world["exec_id"])


def test_a_success_resets_the_count_in_postgres(world, accounts) -> None:
    """RV1-L1: 4 failures, a success, 2 failures: not locked (the adapter's SQL, not the memory store's)."""
    key = "d" * 64
    for minute in range(4):
        accounts.guarded_attempt(key, T0 + timedelta(minutes=minute), lambda: (False, None))
    accounts.guarded_attempt(key, T0 + timedelta(minutes=4), lambda: (True, world["exec_id"]))
    accounts.guarded_attempt(key, T0 + timedelta(minutes=5), lambda: (False, None))
    assert not accounts.guarded_attempt(key, T0 + timedelta(minutes=6), lambda: (False, None)).locked


def test_an_integrity_error_leaves_the_store_as_a_bare_refusal(world, accounts, monkeypatch, capsys) -> None:
    """RV1-L2b: a value the service would refuse (a padded name) reaches the database CHECK. The store answers
    ACCOUNTS_STORE_REFUSED carrying only the constraint name: no cause, no driver text, no email."""
    import traceback

    from assetops_backend.accounts import onboard
    email = "leaky.person@acme.example"
    with pytest.raises(StoreConflict) as failed:
        accounts.create_account(Account(uuid4(), world["acme"], email, " Padded "), hash_password(PW), T0,
                                "service:onboarding", None)
    error = failed.value
    assert error.code == "ACCOUNTS_STORE_REFUSED" and error.constraint and "name" in error.constraint
    assert error.__cause__ is None and error.__suppress_context__ is True
    assert email not in "".join(traceback.format_exception(error)) and "DETAIL" not in str(error)
    # The command: the same store refusal reaches its stderr as the code, the words and the constraint.
    from assetops_backend.accounts.service import AccountService as Service
    real = Service.onboard_create

    def padded(self, tenant_slug, email_, display_name, password, *, executive):
        monkeypatch.setattr(self._store, "create_account", lambda a, *rest: PostgresAccountStore.create_account(
            self._store, Account(a.id, a.tenant_id, a.email, " Padded "), *rest))
        return real(self, tenant_slug, email_, display_name, password, executive=executive)

    monkeypatch.setattr(Service, "onboard_create", padded)
    monkeypatch.setenv("DATABASE_URL", URL)
    monkeypatch.setattr("sys.stdin", __import__("io").StringIO(PW + "\n"))
    assert onboard.main(["create", "--tenant", "acme", "--email", email, "--name", "Pat"]) == 2
    err = capsys.readouterr().err
    assert err.startswith("ACCOUNTS_STORE_REFUSED The change was not saved: a value is not allowed. constraint=")
    assert email not in err and "Traceback" not in err


# --- lock proofs (R2) -------------------------------------------------------------------------------------------

def _hold(engine, key_sql: str, value: str):  # noqa: F811
    conn = engine.connect()
    tx = conn.begin()
    conn.execute(text(f"SELECT pg_advisory_xact_lock(hashtextextended({key_sql}, 0))"), {"v": value})
    return conn, tx


def _waiting_on_advisory(engine) -> int:  # noqa: F811
    with engine.connect() as c:
        return c.execute(text("SELECT count(*) FROM pg_locks WHERE locktype = 'advisory' AND NOT granted "
                              "AND database = (SELECT oid FROM pg_database WHERE datname = current_database())")
                         ).scalar_one()


def _race(engine, key_sql: str, value: str, *calls):  # noqa: F811
    """Hold the lock, start both calls, prove both wait on it, release, and return each outcome."""
    conn, tx = _hold(engine, key_sql, value)
    results: list[object] = [None, None]

    def run(i, call):
        try:
            results[i] = call()
        except (AccountRefused, StoreConflict) as refused:
            results[i] = refused.code

    threads = [threading.Thread(target=run, args=(i, call)) for i, call in enumerate(calls)]
    try:
        for thread in threads:
            thread.start()
        deadline = time.monotonic() + 10
        while _waiting_on_advisory(engine) < 2 and time.monotonic() < deadline:
            time.sleep(0.05)
        time.sleep(0.5)
        assert all(thread.is_alive() for thread in threads), "a call finished while the lock was held"
        assert _waiting_on_advisory(engine) == 2
    finally:
        tx.commit()
        conn.close()
    for thread in threads:
        thread.join(30)
    return results


TENANT_KEY = "'role_grant:' || CAST(:v AS text)"


def test_lock_two_removals_of_the_last_two_executives(world, accounts, engine) -> None:  # noqa: F811
    svc, acme = world["svc"], world["acme"]
    joseph = svc.onboard_create("acme", "joseph@acme.example", "Joseph", PW, executive=False)
    amina = svc.resolve(svc.sign_in("amina@acme.example", PW).token)
    world["clock"].now = T0 + timedelta(seconds=1)
    svc.grant(amina, joseph, EXEC, None)
    jo = svc.resolve(svc.sign_in("joseph@acme.example", PW).token)
    mine = accounts.held_grants(acme, world["exec_id"])[0].row_id
    his = accounts.held_grants(acme, joseph)[0].row_id
    world["clock"].now = T0 + timedelta(seconds=2)
    results = _race(engine, TENANT_KEY, str(acme), lambda: svc.remove(amina, mine), lambda: svc.remove(jo, his))
    assert sorted(r if isinstance(r, str) else "removed" for r in results) == ["LAST_EXECUTIVE", "removed"]
    held = [g for p in (world["exec_id"], joseph) for g in accounts.held_grants(acme, p) if g.role == EXEC]
    assert len(held) == 1


def test_lock_two_identical_grants(world, accounts, engine) -> None:  # noqa: F811
    svc, acme = world["svc"], world["acme"]
    joseph = svc.onboard_create("acme", "joseph@acme.example", "Joseph", PW, executive=False)
    amina = svc.resolve(svc.sign_in("amina@acme.example", PW).token)
    results = _race(engine, TENANT_KEY, str(acme), lambda: svc.grant(amina, joseph, "ANALYST", None),
                    lambda: svc.grant(amina, joseph, "ANALYST", None))
    assert sorted(r if isinstance(r, str) else "granted" for r in results) == ["ROLE_ALREADY_HELD", "granted"]
    assert len(accounts.held_grants(acme, joseph)) == 1


def test_lock_two_creates_with_an_executive_grant(world, accounts, engine) -> None:  # noqa: F811
    svc, beta = world["svc"], world["beta"]
    results = _race(engine, TENANT_KEY, str(beta),
                    lambda: svc.onboard_create("beta", "omar@beta.example", "Omar", PW, executive=True),
                    lambda: svc.onboard_create("beta", "zara@beta.example", "Zara", PW, executive=True))
    assert sorted(r if isinstance(r, str) else "created" for r in results) == ["EXECUTIVE_EXISTS", "created"]
    assert sum(1 for p in accounts.people(beta) for g in p.grants if g.role == EXEC) == 1


def test_lock_two_sign_ins_wait_on_the_per_email_lock(world, engine) -> None:  # noqa: F811
    svc = world["svc"]
    key = hashlib.sha256(b"amina@acme.example").hexdigest()
    results = _race(engine, "'sign_in:' || :v", key, lambda: svc.sign_in("amina@acme.example", PW),
                    lambda: svc.sign_in("amina@acme.example", PW))
    assert all(not isinstance(r, str) for r in results)
    with engine.connect() as c:
        rows = c.execute(text("SELECT succeeded, person_id FROM sign_in_attempt")).all()
    assert rows == [(True, world["exec_id"])] * 2


# --- the downgrade (R11) ----------------------------------------------------------------------------------------

def test_downgrade_refused_with_an_account_then_down_and_up(world, engine) -> None:  # noqa: F811
    from alembic import command

    cfg = pg_harness._alembic(URL)
    with pytest.raises(Exception, match="Downgrade of 0062_operator_accounts refused: accounts exist"):
        command.downgrade(cfg, "0061_reading_upload")
    upload = uuid4()
    with engine.begin() as c:  # TRUNCATE is not a row DELETE; the append-only triggers do not fire on it
        c.execute(text("TRUNCATE " + ", ".join(TABLES)))
        c.execute(text(
            "INSERT INTO reading_upload (id, tenant_id, site_id, file_name, file_sha256, profile_sha256, state, "
            "period_start, period_end, entered_by) VALUES (:id, :t, :s, 'k.csv', :h, :h, 'SENT', :a, :b, "
            "'service:operator-entry')"),
            {"id": upload, "t": world["acme"], "s": world["site"], "h": "a" * 64, "a": T0, "b": T0 + timedelta(hours=1)})
    command.downgrade(cfg, "0061_reading_upload")
    with engine.connect() as c:
        for table in TABLES:
            assert c.execute(text("SELECT to_regclass(:t)"), {"t": table}).scalar_one() is None
        functions = {r[0] for r in c.execute(text("SELECT proname FROM pg_proc WHERE proname = ANY(:n)"), {"n": [
            "role_grant_removal_matches", "operator_session_revoke_only", "sign_in_attempt_no_update",
            "ledger_append_only"]})}
    assert functions == {"ledger_append_only"}
    _refused_sql(engine, "UPDATE reading_upload SET file_name = 'x.csv'")  # an 0005 trigger still refuses
    with engine.begin() as c:
        c.execute(text("TRUNCATE reading_upload"))
    command.upgrade(cfg, "head")
    pg_harness.assert_at_head(engine)


def test_lock_a_grant_waits_while_the_actors_role_is_removed(world, accounts, engine) -> None:  # noqa: F811
    """RV1-R2: the grant by executive A waits on the tenant lock; the other executive removes A's role under it;
    A's grant comes back ROLE_REQUIRED."""
    from assetops_backend.accounts.adapters.postgres_account_store import _INSERT_GRANT, _grant_values
    svc, acme = world["svc"], world["acme"]
    joseph = svc.onboard_create("acme", "joseph@acme.example", "Joseph", PW, executive=False)
    amina = svc.resolve(svc.sign_in("amina@acme.example", PW).token)
    world["clock"].now = T0 + timedelta(seconds=1)
    svc.grant(amina, joseph, EXEC, None)
    mine = accounts.held_grants(acme, world["exec_id"])[0]
    world["clock"].now = T0 + timedelta(seconds=2)
    analyst = svc.onboard_create("acme", "zed@acme.example", "Zed", PW, executive=False)
    removal = GrantRow(uuid4(), mine.row_id, acme, mine.person_id, mine.display_name, EXEC, None, None, "REMOVED",
                       joseph, "Joseph", None, T0 + timedelta(seconds=3))
    conn, tx = _hold(engine, TENANT_KEY, str(acme))
    result: list[object] = []

    def grant() -> None:
        try:
            result.append(svc.grant(amina, analyst, "ANALYST", None))
        except AccountRefused as refused:
            result.append(refused.code)

    thread = threading.Thread(target=grant)
    try:
        thread.start()
        deadline = time.monotonic() + 10
        while _waiting_on_advisory(engine) < 1 and time.monotonic() < deadline:
            time.sleep(0.05)
        time.sleep(0.5)
        assert thread.is_alive() and _waiting_on_advisory(engine) == 1, "the grant did not wait on the lock"
        conn.execute(_INSERT_GRANT, _grant_values(removal))  # the other executive removes A's role under the lock
    finally:
        tx.commit()
        conn.close()
    thread.join(30)
    assert result == ["ROLE_REQUIRED"], result
    assert accounts.held_grants(acme, analyst) == ()
