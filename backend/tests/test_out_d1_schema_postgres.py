"""OUT-D U1: migration `0038_out_objectives` against Postgres (`.agent/build-sheet-OUT-D.md` §3 U1).

The sole head and its chain to `0035_w5_ev_work`; the exact `outcome_objective_revision` catalog (columns, named
CHECKs, FKs, UNIQUEs, read index, trigger); each CHECK refuses by name; the site FK refuses an unknown Site; the
append-only trigger refuses UPDATE and DELETE; `downgrade 0035_w5_ev_work` then `upgrade head` round-trips.

CHECK probes are direct SQL in the replica role (the CHECKs still apply; the FK and append-only triggers do not).
Requires ASSETOPS_TEST_DATABASE_URL naming a `*_test` database.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from test_s4_finding_store_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    import pg_harness
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError

    from test_s1_bindings_postgres import _alembic, engine  # noqa: F401
    from test_w203_cold_migration_postgres import _replica, head

HEAD = "0038_out_objectives"
PARENT = "0035_w5_ev_work"
TABLE = "outcome_objective_revision"
SHA = "a" * 64

CHECKS = sorted([f"{TABLE}_{c}_check" for c in (
    "outcome_key", "revision_no", "measure_key", "measure_kind", "comparison", "target", "unit", "currency",
    "window_rule", "source", "source_note", "actor_kind", "actor_id", "authorization_basis", "source_channel",
    "idempotency_key", "payload_sha256", "chain", "money")] + [f"{TABLE}_leading_no_money"])
FKS = sorted(f"{TABLE}_{n}" for n in ("site_fk", "supersedes_fk"))
UNIQUES = sorted(f"{TABLE}_{n}" for n in ("no_unique", "id_unique", "idempotency_unique"))
COLUMNS = [
    ("id", "uuid", True), ("tenant_id", "uuid", True), ("site_id", "uuid", True), ("outcome_key", "text", True),
    ("revision_no", "integer", True), ("supersedes_revision_id", "uuid", False), ("measure_key", "text", True),
    ("measure_kind", "text", True), ("comparison", "text", True), ("target", "numeric", True),
    ("unit", "text", True), ("currency", "text", False), ("window_rule", "text", True), ("source", "text", True),
    ("source_note", "text", True), ("actor_kind", "text", True), ("actor_id", "text", True),
    ("authorization_basis", "text", True), ("source_channel", "text", True), ("idempotency_key", "text", True),
    ("payload_sha256", "text", True), ("recorded_at", "timestamp with time zone", True),
]

INSERT = (
    f"INSERT INTO {TABLE} (id, tenant_id, site_id, outcome_key, revision_no, supersedes_revision_id, measure_key, "
    "measure_kind, comparison, target, unit, currency, window_rule, source, source_note, actor_kind, actor_id, "
    "authorization_basis, source_channel, idempotency_key, payload_sha256, recorded_at) VALUES (:id, :t, :s, :o, "
    ":no, :sup, :m, :kind, :cmp, :target, :unit, :cur, :win, :src, 'Declared for a schema probe', 'SYSTEM', "
    ":actor, 'schema probe', 'SYSTEM_CLI', :key, :sha, clock_timestamp())")


def row(**over) -> dict:
    base = {"id": str(uuid4()), "t": str(uuid4()), "s": str(uuid4()), "o": "MG-2", "no": 1, "sup": None,
            "m": "avoidable_generator_minutes", "kind": "LEADING", "cmp": "AT_MOST", "target": "0",
            "unit": "min/day", "cur": None, "win": "BOARD_DAY", "src": "DECLARED",
            "actor": "service:assetops-objective-declarer", "key": f"out-d-{uuid4().hex[:12]}", "sha": SHA}
    return {**base, **over}


def names(engine, contype: str) -> list[str]:  # noqa: F811
    with engine.connect() as c:
        return sorted(c.execute(text("SELECT conname FROM pg_constraint WHERE contype = :k AND conrelid = "
                                     f"'{TABLE}'::regclass"), {"k": contype}).scalars())


def insert(engine, values: dict, *, replica: bool = True) -> None:  # noqa: F811
    with engine.begin() as c:
        if replica:
            c.execute(text("SET LOCAL session_replication_role = replica"))
        c.execute(text(INSERT), values)


def refused(engine, values: dict, constraint: str, *, replica: bool = True) -> None:  # noqa: F811
    with pytest.raises(DBAPIError) as caught:
        insert(engine, values, replica=replica)
    assert getattr(caught.value.orig.diag, "constraint_name", None) == constraint, caught.value


def test_sole_head_chain_and_catalog(engine) -> None:  # noqa: F811
    from alembic.script import ScriptDirectory

    script = ScriptDirectory.from_config(_alembic())
    assert script.get_heads() == [HEAD] and head(engine) == HEAD
    pg_harness.assert_at_head(engine)
    assert script.get_revision(HEAD).down_revision == PARENT
    with engine.connect() as c:
        columns = [tuple(r) for r in c.execute(text(
            "SELECT a.attname, format_type(a.atttypid, a.atttypmod), a.attnotnull FROM pg_attribute a "
            f"WHERE a.attrelid = '{TABLE}'::regclass AND a.attnum > 0 AND NOT a.attisdropped ORDER BY a.attnum"))]
        index = c.execute(text("SELECT indexdef FROM pg_indexes WHERE indexname = :n"), {"n": f"{TABLE}_read"}).scalar()
        triggers = sorted(c.execute(text(
            "SELECT t.tgname || ':' || p.proname || ':' || t.tgtype FROM pg_trigger t JOIN pg_proc p ON "
            f"p.oid = t.tgfoid WHERE NOT t.tgisinternal AND t.tgrelid = '{TABLE}'::regclass")).scalars())
    assert columns == COLUMNS
    assert names(engine, "p") == [f"{TABLE}_pkey"]
    assert names(engine, "c") == CHECKS and names(engine, "f") == FKS and names(engine, "u") == UNIQUES
    assert index.endswith("(tenant_id, site_id, outcome_key, recorded_at)"), index
    # tgtype 27 = ROW | BEFORE | DELETE | UPDATE.
    assert triggers == [f"{TABLE}_immutable:w4_append_only:27"]


@pytest.mark.parametrize(("over", "constraint"), [
    ({"o": "XX-1"}, f"{TABLE}_outcome_key_check"),
    ({"o": "MG-0"}, f"{TABLE}_outcome_key_check"),
    ({"m": "supply_cost_per_kwh"}, f"{TABLE}_measure_key_check"),
    ({"kind": "TRAILING"}, f"{TABLE}_measure_kind_check"),
    ({"cmp": "EQUAL"}, f"{TABLE}_comparison_check"),
    ({"target": "-1"}, f"{TABLE}_target_check"),
    ({"unit": "hours"}, f"{TABLE}_unit_check"),
    ({"cur": "usd", "unit": "currency/km", "kind": "VALUE"}, f"{TABLE}_currency_check"),
    ({"win": "WEEK"}, f"{TABLE}_window_rule_check"),
    ({"src": "GUESSED"}, f"{TABLE}_source_check"),
    ({"actor": "person:someone"}, f"{TABLE}_actor_id_check"),
    ({"key": "short"}, f"{TABLE}_idempotency_key_check"),
    ({"sha": "A" * 64}, f"{TABLE}_payload_sha256_check"),
    ({"no": 0, "sup": str(uuid4())}, f"{TABLE}_revision_no_check"),
    ({"no": 2, "sup": None}, f"{TABLE}_chain_check"),
    ({"no": 1, "sup": str(uuid4())}, f"{TABLE}_chain_check"),
    ({"unit": "currency/km", "kind": "VALUE", "cur": None}, f"{TABLE}_money_check"),
    ({"unit": "min/day", "kind": "VALUE", "cur": "USD"}, f"{TABLE}_money_check"),
    ({"unit": "currency/km", "kind": "LEADING", "cur": "USD"}, f"{TABLE}_leading_no_money"),
])
def test_each_check_refuses_by_name(engine, over, constraint) -> None:  # noqa: F811
    refused(engine, row(**over), constraint)


def test_money_row_passes_and_site_fk_refuses_an_unknown_site(engine) -> None:  # noqa: F811
    money = row(o="EV-2", m="energy_cost_per_km", kind="VALUE", unit="currency/km", cur="USD", target="0.20",
                win="BOARD_WINDOW")
    insert(engine, money)
    _replica(engine, f"DELETE FROM {TABLE} WHERE id = '{money['id']}'")
    refused(engine, row(), f"{TABLE}_site_fk", replica=False)


def test_trigger_refuses_update_and_delete(engine) -> None:  # noqa: F811
    stored = row()
    insert(engine, stored)
    try:
        for sql in (f"UPDATE {TABLE} SET target = 5 WHERE id = :id", f"DELETE FROM {TABLE} WHERE id = :id"):
            with pytest.raises(DBAPIError, match="append only"):
                with engine.begin() as c:
                    c.execute(text(sql), {"id": stored["id"]})
    finally:
        _replica(engine, f"DELETE FROM {TABLE} WHERE id = '{stored['id']}'")


def test_downgrade_to_parent_and_upgrade_head_round_trip(engine) -> None:  # noqa: F811
    from alembic import command

    config = _alembic()
    engine.dispose()
    command.downgrade(config, PARENT)
    with engine.connect() as c:
        assert c.execute(text(f"SELECT to_regclass('{TABLE}') IS NULL")).scalar()
    assert head(engine) == PARENT
    engine.dispose()
    command.upgrade(config, "head")
    assert head(engine) == HEAD
    pg_harness.assert_at_head(engine)
    assert names(engine, "c") == CHECKS
