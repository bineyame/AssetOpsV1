"""3C2 (spec §5 tests 6 to 8; D-3C2.3, D-3C2.7, D-3C2.9, D-3C2.13): migration 0070, the Postgres store of agreed
changes, the command end to end on ON1's Lakeside tenant, and the "once" rule held by the lock and the index each.

Needs `ASSETOPS_TEST_DATABASE_URL` naming a `*_test` database (the harness routes the run to its own clone); skipped
otherwise. Run through `tools/heavy-slot.sh --db`.
"""
from __future__ import annotations

import json
import os
import threading
import time
from datetime import date, datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from test_on1_onboarding_postgres import onboarded  # noqa: F401 - Lakeside onboarded through ON1's command
    from test_s1_bindings_postgres import engine, store  # noqa: F401

    import pg_harness
    from assetops_backend import record_action
    from assetops_backend.accounts.composition import build_account_service
    from assetops_backend.actions.adapters.postgres_agreed_action_store import PostgresAgreedActionStore
    from assetops_backend.actions.agreed import AgreedActionRow, AgreedActionService
    from assetops_backend.actions.agreed_composition import build_agreed_actions
    from test_3c0a_accounts_postgres import seed_tenant
    from test_3c0a_accounts_service import PW
    from test_3c2_agreed_actions import R1_LINE, T_R1, TITLE, Clock, email, r1

TABLE = "agreed_action"
#: Gate A's hand pair (D-3C2.9): built on the 3A6 head; renumbered at gate B with the file.
HAND_PAIR = ("0070_agreed_action", "0068_structure_finding")
VERSIONS = Path(__file__).resolve().parents[1] / "migrations" / "versions"
SLUG = "lakeside-power"


@pytest.fixture()
def lake(onboarded, engine):  # noqa: F811
    with engine.connect() as c:
        tenant = c.execute(text("SELECT id FROM tenant WHERE slug = :s"), {"s": SLUG}).scalar_one()
        people = dict(c.execute(text("SELECT display_name, id FROM operator_account WHERE tenant_id = :t"),
                                {"t": tenant}).all())
        sites = dict(c.execute(text("SELECT site_code, id FROM site WHERE tenant_id = :t"), {"t": tenant}).all())
    adapter = PostgresAgreedActionStore(URL)
    yield {"tenant": tenant, "people": people, "sites": sites, "adapter": adapter}
    adapter.dispose()


def _row(lake, **over) -> AgreedActionRow:
    values = dict(id=uuid4(), tenant_id=lake["tenant"], title=TITLE, site_id=lake["sites"]["KOBO-001"],
                  factor_id="candidate_l", owner_person_id=lake["people"]["Peter"],
                  created_by_person_id=lake["people"]["Amina"], created_role="OPERATOR_EXECUTIVE",
                  created_by_script=True, created_at=T_R1, due_on=date(2026, 12, 15), origin="DEEP_DIVE")
    values.update(over)
    return AgreedActionRow(**values)


_INSERT = text("INSERT INTO agreed_action (id, tenant_id, title, site_id, factor_id, owner_person_id, "
               "created_by_person_id, created_role, created_by_script, created_at, due_on, origin) VALUES (:id, "
               ":tenant_id, :title, :site_id, :factor_id, :owner_person_id, :created_by_person_id, :created_role, "
               ":created_by_script, :created_at, :due_on, :origin)")


def _params(row: AgreedActionRow) -> dict:
    return {f: getattr(row, f) for f in row.__dataclass_fields__}


def _count(engine) -> int:  # noqa: F811
    with engine.connect() as c:
        return c.execute(text("SELECT count(*) FROM agreed_action")).scalar_one()


def _this_migration(cfg):
    from alembic.script import ScriptDirectory

    for script in ScriptDirectory.from_config(cfg).walk_revisions():
        if TABLE in getattr(script.module, "TABLES", ()):
            return script
    raise AssertionError("no migration declares agreed_action")


def _previous_revision(name: str) -> str:
    files = sorted(p.name for p in VERSIONS.glob("[0-9][0-9][0-9][0-9]_*.py"))
    previous = files[files.index(f"{name}.py") - 1]
    for line in (VERSIONS / previous).read_text(encoding="utf-8").splitlines():
        if line.startswith("revision = "):
            return line.split("=", 1)[1].strip().strip('"')
    raise AssertionError(f"no revision line in {previous}")


def _refused_write(engine, sql: str, params: dict, match: str) -> None:  # noqa: F811
    with pytest.raises(Exception, match=match):
        with engine.begin() as c:
            c.execute(text(sql), params)


# --- test 6: the migration --------------------------------------------------------------------------------------------

def test_6_chain_triggers_checks_and_refused_downgrade(lake, engine) -> None:  # noqa: F811
    from alembic import command

    cfg = pg_harness._alembic(URL)
    script = _this_migration(cfg)
    assert (script.revision, script.down_revision) == HAND_PAIR
    assert script.down_revision == _previous_revision(script.revision)
    row = _row(lake)
    with engine.begin() as c:
        c.execute(_INSERT, _params(row))
    _refused_write(engine, "UPDATE agreed_action SET title = 'x' WHERE id = :i", {"i": row.id}, "append-only")
    _refused_write(engine, "DELETE FROM agreed_action WHERE id = :i", {"i": row.id}, "append-only")
    _refused_write(engine, "TRUNCATE agreed_action", {}, "append-only")
    assert _count(engine) == 1
    other = seed_tenant(engine, "other-op")
    zara = build_account_service(URL)
    zara_id = zara.onboard_create("other-op", "zara@other-op.example", "Zara", PW, executive=True)
    assert other
    _refused_write(engine, _INSERT.text, _params(_row(lake, owner_person_id=zara_id)), "foreign key")
    _refused_write(engine, _INSERT.text, _params(_row(lake, due_on=date(2026, 11, 19))), "check constraint")
    _refused_write(engine, _INSERT.text, _params(_row(lake, site_id=None)), "check constraint")
    _refused_write(engine, _INSERT.text,
                   _params(_row(lake, created_at=datetime(2026, 11, 20, 9, 30, 0, 5, tzinfo=timezone.utc))),
                   "check constraint")
    lake["adapter"].dispose()
    with pytest.raises(Exception, match="Downgrade of 0070_agreed_action refused: agreed Actions exist"):
        command.downgrade(cfg, script.down_revision)
    with engine.begin() as c:  # the test empties the table the only way the triggers allow
        c.execute(text("SET LOCAL session_replication_role = replica"))
        c.execute(text("DELETE FROM agreed_action"))
    command.downgrade(cfg, script.down_revision)
    with engine.connect() as c:
        assert c.execute(text("SELECT to_regclass('agreed_action')")).scalar_one() is None
    command.upgrade(cfg, "head")
    pg_harness.assert_at_head(engine)


# --- test 7: the command and the store on Lakeside --------------------------------------------------------------------

def _main(argv, at=T_R1) -> int:
    return record_action.main(argv, clock=Clock(at))


def test_7a_r1_through_main_then_again_then_two_at_once(lake, engine, capsys, monkeypatch) -> None:  # noqa: F811
    monkeypatch.setenv("DATABASE_URL", URL)
    assert _main(r1()) == 0
    out, err = capsys.readouterr()
    line = json.loads(out)
    with engine.connect() as c:
        stored = c.execute(text("SELECT id, created_at FROM agreed_action")).one()
    assert err == "" and "@" not in out
    assert line == {**R1_LINE, "action_id": str(stored.id)}
    assert stored.created_at == T_R1
    assert _main(r1()) == 0
    assert json.loads(capsys.readouterr().out) == {**R1_LINE, "action_id": str(stored.id), "already_recorded": True}
    assert _count(engine) == 1

    other = r1(title="Change B", owner=email("joseph"), site=None, factor=None)
    gate = threading.Barrier(2)
    codes: list[int] = []

    def run() -> None:
        gate.wait()
        codes.append(_main(other))

    threads = [threading.Thread(target=run) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(30)
    out, err = capsys.readouterr()
    assert codes == [0, 0] and err == ""
    lines = [json.loads(x) for x in out.splitlines()]
    assert sorted(x["already_recorded"] for x in lines) == [False, True]
    assert len({x["action_id"] for x in lines}) == 1
    assert _count(engine) == 2


def _wait_for(engine, sql: str, limit: float = 5.0) -> None:  # noqa: F811
    deadline = time.monotonic() + limit
    with engine.connect() as c:
        while time.monotonic() < deadline:
            if c.execute(text(sql)).scalar_one() > 0:
                return
            time.sleep(0.05)
    raise AssertionError(f"no waiting backend within {limit} s: {sql}")


def _add_in_thread(adapter, row) -> tuple[threading.Thread, list]:
    result: list = []
    thread = threading.Thread(target=lambda: result.append(adapter.add(row)))
    thread.start()
    return thread, result


def test_7b_the_index_catch_returns_the_stored_row(lake, engine) -> None:  # noqa: F811
    mine = _row(lake)
    theirs = _row(lake)  # the same key, another id
    with engine.connect() as c:
        tx = c.begin()
        c.execute(_INSERT, _params(mine))  # without the advisory lock
        thread, result = _add_in_thread(lake["adapter"], theirs)
        _wait_for(engine, "SELECT count(*) FROM pg_locks l JOIN pg_stat_activity a ON a.pid = l.pid "
                          "WHERE NOT l.granted AND a.datname = current_database()")
        tx.commit()
    thread.join(10)
    assert result == [(mine, True)]
    assert _count(engine) == 1


def test_7c_the_advisory_lock_serialises_the_identity_read(lake, engine) -> None:  # noqa: F811
    row = _row(lake)
    with engine.connect() as c:
        tx = c.begin()
        c.execute(text("SELECT pg_advisory_xact_lock(hashtextextended('agreed_action:' || CAST(:t AS text), 0))"),
                  {"t": str(lake["tenant"])})
        thread, result = _add_in_thread(lake["adapter"], row)
        _wait_for(engine, "SELECT count(*) FROM pg_locks WHERE locktype = 'advisory' AND NOT granted")
        tx.commit()
    thread.join(10)
    assert result == [(row, False)]
    assert _count(engine) == 1


def test_7d_the_site_lookup_folds_case(lake, engine) -> None:  # noqa: F811
    assert lake["adapter"].site(lake["tenant"], "kobo-001") == (lake["sites"]["KOBO-001"], "MINIGRID", "KOBO-001")
    assert lake["adapter"].site(lake["tenant"], "NOPE-001") is None
    other_op = seed_tenant(engine, "other-op")  # F2: a Site code another tenant does not own is not found
    assert lake["adapter"].site(other_op, "KOBO-001") is None


# --- test 8: the read over the adapter ----------------------------------------------------------------------------

def test_8_the_read_is_newest_first_with_names(lake, engine) -> None:  # noqa: F811
    ids = iter((1, 2, 3, 5, 4))
    clock = Clock(T_R1)
    service = AgreedActionService(lake["adapter"], build_account_service(URL), clock=clock,
                                  new_id=lambda: UUID(int=next(ids)))
    records = [(T_R1, dict(title=TITLE, owner_email=email("peter"), due_on=date(2026, 12, 15), site_code="KOBO-001",
                           factor_id="candidate_l")),
               (datetime(2026, 11, 20, 10, 0, tzinfo=timezone.utc),
                dict(title="Change B", owner_email=email("joseph"), due_on=date(2026, 11, 30), site_code=None,
                     factor_id=None)),
               (datetime(2026, 11, 20, 10, 30, tzinfo=timezone.utc),
                dict(title="Change C", owner_email=email("peter"), due_on=date(2026, 12, 1), site_code="KOBO-001",
                     factor_id=None)),
               (datetime(2026, 11, 20, 11, 0, tzinfo=timezone.utc),
                dict(title="Change E", owner_email=email("joseph"), due_on=date(2026, 12, 20), site_code=None,
                     factor_id=None)),
               (datetime(2026, 11, 20, 11, 0, tzinfo=timezone.utc),
                dict(title="Change D", owner_email=email("joseph"), due_on=date(2026, 12, 20), site_code=None,
                     factor_id=None))]
    for at, fields in records:
        clock.set(at)
        assert not service.record(tenant_slug=SLUG, as_email=email("amina"), **fields).already_recorded
    clock.set(datetime(2026, 12, 1, tzinfo=timezone.utc))
    views = service.for_tenant(lake["tenant"])
    expected = [(5, "Change E", "Joseph", None), (4, "Change D", "Joseph", None), (3, "Change C", "Peter", "KOBO-001"),
                (2, "Change B", "Joseph", None), (1, TITLE, "Peter", "KOBO-001")]
    assert [(v.action_id.int, v.title, v.owner_name, v.site_code) for v in views] == expected
    assert {v.created_by_name for v in views} == {"Amina"}
    assert [v.state_code for v in views] == ["OPEN", "OPEN", "OPEN", "OVERDUE", "OPEN"]
    assert [v.state_words for v in views] == ["Open", "Open", "Open", "Overdue", "Open"]
    composed = build_agreed_actions(URL)
    try:
        read = composed.service.for_tenant(lake["tenant"])
    finally:
        composed.dispose()
    assert [(v.action_id.int, v.title, v.owner_name, v.site_code) for v in read] == expected


def test_8b_the_read_is_tenant_scoped(lake, engine) -> None:  # noqa: F811
    """F2: an agreed change in a second tenant never shows in Lakeside's read, and Lakeside's never in theirs."""
    other = seed_tenant(engine, "other-op")
    accounts = build_account_service(URL)
    try:
        zara_id = accounts.onboard_create("other-op", "zara@other-op.example", "Zara", PW, executive=True)
    finally:
        accounts._store.dispose()
    service = AgreedActionService(lake["adapter"], build_account_service(URL), clock=Clock(T_R1))
    service.record(tenant_slug=SLUG, as_email=email("amina"), title=TITLE, owner_email=email("peter"),
                   due_on=date(2026, 12, 15), site_code="KOBO-001", factor_id=None)
    service.record(tenant_slug="other-op", as_email="zara@other-op.example", title="Zara change",
                   owner_email="zara@other-op.example", due_on=date(2026, 12, 15), site_code=None, factor_id=None)
    assert [v.title for v in service.for_tenant(lake["tenant"])] == [TITLE]
    theirs = service.for_tenant(other)
    assert [(v.title, v.owner_name) for v in theirs] == [("Zara change", "Zara")]
    assert zara_id
