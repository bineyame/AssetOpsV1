"""CH-5c u2 (CH5c-R4 W1-W2, W5, R7 flips): the change-log watermark moves on every input write, in commit order.

Flips: an INSERT, an UPDATE, a DELETE; T1/T2 out-of-order commits on an UPDATEd table; a late-committing outbox
row with an earlier `recorded_at`. An unrelated Site's change does not flip it. W5: a harness reset empties the
stored responses and the change log together. W6 (partial): every declared input table carries the four triggers,
read from `pg_trigger`.
"""
from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

import pytest

from test_s1_bindings_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from test_s1_bindings_postgres import engine  # noqa: F401

    import pg_harness
    from assetops_backend.chain.watermark import read_watermark

ROOT = Path(__file__).resolve().parents[2]


def _migration_tables() -> tuple[str, ...]:
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "m0047", ROOT / "backend" / "migrations" / "versions" / "0047_chain_response.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.INPUT_TABLES


def test_declared_inputs_equal_the_frozen_migration_list() -> None:
    declared = json.loads((ROOT / "config" / "chain" / "watermark-inputs-v1.json").read_text())["tables"]
    assert set(declared) - {"chain_action"} == set(_migration_tables())


def _wm(engine, tenant, sites):
    with engine.connect().execution_options(isolation_level="REPEATABLE READ") as c, c.begin():
        return read_watermark(c, tenant, sites)


def test_every_declared_input_has_the_four_change_triggers(engine) -> None:  # noqa: F811
    with engine.connect() as c:
        rows = c.execute(text(
            "SELECT c.relname, t.tgtype FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid "
            "WHERE t.tgname LIKE '%\\_cic\\_%' AND NOT t.tgisinternal")).all()
    events: dict[str, int] = {}
    for table, tgtype in rows:  # tgtype bits: 4 INSERT, 8 DELETE, 16 UPDATE, 32 TRUNCATE
        events[table] = events.get(table, 0) | (tgtype & (4 | 8 | 16 | 32))
    missing = [t for t in _migration_tables() if events.get(t) != 60]
    assert not missing, missing


def test_watermark_flips_on_insert_update_delete_and_not_on_another_site(engine) -> None:  # noqa: F811
    tenant, site, other = uuid4(), uuid4(), uuid4()
    before = _wm(engine, tenant, [site])
    with engine.begin() as c:
        c.execute(text("INSERT INTO chain_input_change (tenant_id, site_id, table_name) VALUES (:t, :o, 'x')"),
                  {"t": tenant, "o": other})
    assert _wm(engine, tenant, [site]) == before  # another Site's change
    with engine.begin() as c:
        c.execute(text("INSERT INTO chain_input_change (tenant_id, site_id, table_name) VALUES (:t, NULL, 'x')"),
                  {"t": tenant})
    assert _wm(engine, tenant, [site]) != before  # a tenant-wide row over-invalidates


def test_out_of_order_commits_and_late_outbox_row_flip(engine) -> None:  # noqa: F811
    """T1 starts first and commits last; the watermark read between the two commits must still move at T1's."""
    tenant, site = uuid4(), uuid4()
    w0 = _wm(engine, tenant, [site])
    t1 = engine.connect()
    t2 = engine.connect()
    try:
        x1 = t1.begin()
        t1.execute(text("INSERT INTO chain_input_change (tenant_id, site_id, table_name) VALUES (:t, :s, 'u1')"),
                   {"t": tenant, "s": site})  # T1: the earlier xid
        with t2.begin():
            t2.execute(text("INSERT INTO chain_input_change (tenant_id, site_id, table_name) VALUES (:t, :s, 'u2')"),
                       {"t": tenant, "s": site})
        w2 = _wm(engine, tenant, [site])
        assert w2 != w0
        x1.commit()  # T1 commits after T2, with an earlier clock: a max(xmin) / max(recorded_at) term misses this
        assert _wm(engine, tenant, [site]) != w2
    finally:
        t1.close()
        t2.close()


def test_reset_empties_responses_and_change_log_together(engine) -> None:  # noqa: F811
    assert pg_harness.RESPONSE_TABLES == ("chain_response", "chain_input_change")
    with engine.begin() as c:
        c.execute(text("INSERT INTO chain_input_change (tenant_id, site_id, table_name) VALUES (NULL, NULL, 'x')"))
        c.execute(text("INSERT INTO chain_response (tenant_id, route, request_key, watermark, code_version, etag, "
                       "body, build_ms) VALUES (:t, 'r', 'k', 'w', 'v', 'e', '\\x00', 1)"), {"t": uuid4()})
    pg_harness.empty_tables(engine, ("tenant",))
    with engine.connect() as c:
        assert c.execute(text("SELECT count(*) FROM chain_input_change")).scalar_one() == 0
        assert c.execute(text("SELECT count(*) FROM chain_response")).scalar_one() == 0
