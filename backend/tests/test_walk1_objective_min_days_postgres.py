"""WALK1-3b §A2.5: migration `0041_walk1_objective_min_days` and the declared minimum of checked days on Postgres.

The nullable column and its two named CHECKs (range 1-28; monthly measure only), the store writing NULL when the
declaration names no minimum and the value when it does (a changed minimum is a new revision), the board facts reading
the stored value, and the downgrade refusing while any row carries a minimum, otherwise dropping the column.
CHECK probes are direct SQL in the replica role (the CHECKs still apply; the FK and append-only triggers do not).
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from test_s4_finding_store_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError

    from test_out_d1_schema_postgres import INSERT, TABLE, row
    from test_s1_bindings_postgres import _alembic, engine, imported, store  # noqa: F401
    from test_w203_cold_migration_postgres import head

    from assetops_backend.objectives.composition import build_objective_store
    from assetops_backend.objectives.model import SYSTEM_DECLARER, Declaration, ObjectiveRefused
    from assetops_backend.site_outcomes import mini, objective_facts

HEAD = "0041_walk1_objective_min_days"
PREVIOUS = "0040_walk1_productive_price"
REFUSED = "Downgrade of 0041_walk1_objective_min_days refused"
NOTE = "Declared for the demonstration; not a customer target"
INSERT_MIN = INSERT.replace("payload_sha256, recorded_at)", "payload_sha256, recorded_at, min_checked_days)").replace(
    ":sha, clock_timestamp())", ":sha, clock_timestamp(), :min_days)")


def insert(engine, values: dict) -> None:  # noqa: F811
    with engine.begin() as c:
        c.execute(text("SET LOCAL session_replication_role = replica"))
        c.execute(text(INSERT_MIN), values)


def empty(engine) -> None:  # noqa: F811
    with engine.begin() as c:
        c.execute(text("SET LOCAL session_replication_role = replica"))
        c.execute(text(f"DELETE FROM {TABLE}"))


def mg1(**over) -> dict:
    return row(o="MG-1", m="productive_use_kwh", cmp="AT_LEAST", target="300", unit="kWh/month", **over)


def test_0041_column_and_checks(engine) -> None:  # noqa: F811
    from alembic.script import ScriptDirectory

    script = ScriptDirectory.from_config(_alembic())
    assert script.get_heads() == [HEAD] and script.get_revision(HEAD).down_revision == PREVIOUS
    assert head(engine) == HEAD
    with engine.connect() as c:
        column = c.execute(text(
            "SELECT format_type(a.atttypid, a.atttypmod), a.attnotnull FROM pg_attribute a WHERE a.attrelid = "
            f"'{TABLE}'::regclass AND a.attname = 'min_checked_days'")).one()
    assert tuple(column) == ("integer", False)
    for value in (None, 1, 28):
        insert(engine, mg1(min_days=value))
    insert(engine, row(min_days=None))  # a non-monthly measure without a minimum
    for values, constraint in ((mg1(min_days=0), f"{TABLE}_min_checked_days_range"),
                               (mg1(min_days=29), f"{TABLE}_min_checked_days_range"),
                               (row(min_days=3), f"{TABLE}_min_checked_days_monthly")):
        with pytest.raises(DBAPIError) as caught:
            insert(engine, values)
        assert getattr(caught.value.orig.diag, "constraint_name", None) == constraint, caught.value
    empty(engine)


def test_store_writes_null_or_the_minimum_and_the_board_reads_it(store, engine) -> None:  # noqa: F811
    imported(store, "KOBO-001")
    objectives = build_objective_store(URL)
    try:
        tenant_id = objectives.tenant_id("demo")
        site_id = objectives.site_id(tenant_id, "KOBO-001")
        first, inserted = objectives.declare(tenant_id, Declaration(
            "KOBO-001", "MG-1", "productive_use_kwh", Decimal("300"), None, "DECLARED", NOTE, None,
            "walk1-3b-kobo-mg-1-v1"), SYSTEM_DECLARER, "SYSTEM_CLI")
        assert inserted and first["min_checked_days"] is None
        second, inserted = objectives.declare(tenant_id, Declaration(
            "KOBO-001", "MG-1", "productive_use_kwh", Decimal("300"), None, "DECLARED", NOTE, first["id"],
            "walk1-3b-kobo-mg-1-v2", 5), SYSTEM_DECLARER, "SYSTEM_CLI")
        assert inserted and second["min_checked_days"] == 5 and second["revision_no"] == 2
        with pytest.raises(ObjectiveRefused) as refused:
            objectives.declare(tenant_id, Declaration(
                "KOBO-001", "MG-2", "avoidable_generator_minutes", Decimal("0"), None, "DECLARED", NOTE, None,
                "walk1-3b-kobo-mg-2-v1", 3), SYSTEM_DECLARER, "SYSTEM_CLI")
        assert (refused.value.status, refused.value.code) == (422, "OBJECTIVE_INVALID")
        [fact] = objective_facts.from_rows(objectives.current(tenant_id, site_id, None), mini.num)
        assert fact.min_checked_days == 5
        [old] = objective_facts.from_rows(objectives.current(tenant_id, site_id, first["recorded_at"]), mini.num)
        assert old.min_checked_days == 3  # NULL is the default
    finally:
        objectives.dispose()


def test_0041_downgrade_refuses_with_a_minimum_then_drops_the_column(engine) -> None:  # noqa: F811
    from alembic import command

    config = _alembic()
    empty(engine)  # rows an earlier test of this module declared
    engine.dispose()
    command.downgrade(config, PREVIOUS)
    try:
        with engine.connect() as c:
            assert c.execute(text(
                f"SELECT count(*) FROM pg_attribute WHERE attrelid = '{TABLE}'::regclass "
                "AND attname = 'min_checked_days' AND NOT attisdropped")).scalar() == 0
            assert c.execute(text(f"SELECT count(*) FROM pg_constraint WHERE conrelid = '{TABLE}'::regclass "
                                  "AND conname LIKE '%min_checked_days%'")).scalar() == 0
        assert head(engine) == PREVIOUS
    finally:
        engine.dispose()
        command.upgrade(config, "head")
    assert head(engine) == HEAD
    insert(engine, mg1(min_days=4))
    engine.dispose()
    with pytest.raises(DBAPIError, match=REFUSED):
        command.downgrade(config, PREVIOUS)
    assert head(engine) == HEAD
    empty(engine)
    engine.dispose()
    command.downgrade(config, PREVIOUS)  # with no minimum stored, the downgrade passes again
    engine.dispose()
    command.upgrade(config, "head")
    assert head(engine) == HEAD
