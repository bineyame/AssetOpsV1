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


# --- flips on real input tables (CH5c-R4 R7 cases, CH5c-R5 R5-2 scoping) -----------------------------------------

def _seed(engine, n_sites: int = 3):
    """A tenant and `n_sites` Sites written straight to the input tables (the change triggers fire)."""
    tenant, sites = uuid4(), [uuid4() for _ in range(n_sites)]
    with engine.begin() as c:
        c.execute(text("INSERT INTO tenant (id, slug, name, created_at) VALUES (:t, :slug, 'CH-5c', now())"),
                  {"t": tenant, "slug": f"ch5c-{tenant.hex[:12]}"})
        for i, s in enumerate(sites):
            c.execute(text(
                "INSERT INTO site (id, tenant_id, site_code, site_code_key, name, site_type, timezone, lifecycle, "
                "origin, proposed_source_mode, created_at) VALUES (:s, :t, :code, lower(:code), 'Site', 'MINIGRID', "
                "'UTC', 'ACTIVE', 'TEST', 'SIMULATED', now())"), {"s": s, "t": tenant, "code": f"CH5C-{i}"})
    return tenant, sites


def _outbox(c, tenant, site, key: str, recorded_at: str | None = None):
    return c.execute(text(
        "INSERT INTO event_outbox (type, schema_version, occurred_at, recorded_at, source, tenant_id, site_id, "
        "subject, idempotency_key) VALUES ('test.flip', 1, now(), COALESCE(CAST(:r AS timestamptz), "
        "clock_timestamp()), 'ch5c-test', :t, :s, '{}'::jsonb, :k) RETURNING event_id"),
        {"t": tenant, "s": site, "k": key, "r": recorded_at}).scalar_one()


def test_real_table_insert_update_delete_flip_only_their_site(engine) -> None:  # noqa: F811
    tenant, (a, b, c_site) = _seed(engine)
    wa, wb = _wm(engine, tenant, [a]), _wm(engine, tenant, [b])
    with engine.begin() as c:  # UPDATE: `site` is scoped by its own id (R5-2)
        c.execute(text("UPDATE site SET name = 'Renamed' WHERE id = :s"), {"s": a})
    assert _wm(engine, tenant, [a]) != wa and _wm(engine, tenant, [b]) == wb
    wa = _wm(engine, tenant, [a])
    with engine.connect() as c:
        rows = c.execute(text("SELECT site_id, table_name FROM chain_input_change WHERE tenant_id = :t "
                              "AND table_name = 'site' ORDER BY change_id"), {"t": tenant}).all()
    assert [r[0] for r in rows] == [a, b, c_site, a]  # three inserts, then the update of `a` only
    # DELETE: `site` rows refuse DELETE (registration identity); a Site-less `tenant` row is a real input table
    # that accepts it. The delete moves that tenant's watermark and leaves this tenant's untouched.
    gone = uuid4()
    with engine.begin() as c:
        c.execute(text("INSERT INTO tenant (id, slug, name, created_at) VALUES (:t, :slug, 'gone', now())"),
                  {"t": gone, "slug": f"ch5c-{gone.hex[:12]}"})
    w_gone = _wm(engine, gone, [a])
    with engine.begin() as c:
        c.execute(text("DELETE FROM tenant WHERE id = :t"), {"t": gone})
    assert _wm(engine, gone, [a]) != w_gone
    assert _wm(engine, tenant, [a]) == wa and _wm(engine, tenant, [b]) == wb  # another tenant's delete
    with engine.begin() as c:  # an INSERT on the outbox and its consumption: Site-scoped through the outbox row
        event_id = _outbox(c, tenant, a, "flip-1")
    wa2 = _wm(engine, tenant, [a])
    assert wa2 != wa and _wm(engine, tenant, [b]) == wb
    with engine.begin() as c:
        c.execute(text("INSERT INTO event_consumption (consumer, event_id) VALUES ('threads', :e)"), {"e": event_id})
    assert _wm(engine, tenant, [a]) != wa2 and _wm(engine, tenant, [b]) == wb  # R5-2: not tenant-wide
    with engine.begin() as c:  # `tenant` stays tenant-wide: every Site's watermark moves
        c.execute(text("UPDATE tenant SET name = 'CH-5c renamed' WHERE id = :t"), {"t": tenant})
    assert _wm(engine, tenant, [b]) != wb


def test_real_table_out_of_order_update_and_late_outbox_row(engine) -> None:  # noqa: F811
    tenant, (a, b, _) = _seed(engine)
    scope = [a, b]
    w0 = _wm(engine, tenant, scope)
    t1, t2 = engine.connect(), engine.connect()
    try:
        x1 = t1.begin()
        t1.execute(text("UPDATE site SET lifecycle = 'PAUSED' WHERE id = :s"), {"s": a})  # T1: earlier xid
        with t2.begin():
            t2.execute(text("UPDATE site SET name = 'T2' WHERE id = :s"), {"s": b})
        w2 = _wm(engine, tenant, scope)
        assert w2 != w0
        x1.commit()  # T1 commits after T2
        w3 = _wm(engine, tenant, scope)
        assert w3 != w2
        x1 = t1.begin()  # a late-committing outbox row with an earlier `recorded_at`
        _outbox(t1, tenant, a, "late", "2020-01-01T00:00:00Z")
        with t2.begin():
            _outbox(t2, tenant, a, "early")
        w4 = _wm(engine, tenant, scope)
        assert w4 != w3
        x1.commit()
        assert _wm(engine, tenant, scope) != w4
    finally:
        t1.close()
        t2.close()


def test_flip_depends_on_the_trigger_non_vacuous(engine) -> None:  # noqa: F811
    """Dropping the UPDATE trigger (rolled back) leaves the watermark unchanged by an UPDATE: the flips above are the
    triggers' doing, and the four-trigger check from `pg_trigger` is what keeps them."""
    tenant, (a, _, _) = _seed(engine)
    with engine.connect().execution_options(isolation_level="REPEATABLE READ") as c, c.begin():
        before = read_watermark(c, tenant, [a])
        c.execute(text("DROP TRIGGER site_cic_upd ON site"))
        c.execute(text("UPDATE site SET name = 'Untracked' WHERE id = :s"), {"s": a})
        assert read_watermark(c, tenant, [a]) == before
        c.rollback()
    with engine.begin() as c:
        c.execute(text("UPDATE site SET name = 'Tracked' WHERE id = :s"), {"s": a})
    assert _wm(engine, tenant, [a]) != before


def test_code_version_hashes_head_and_composer_settings(monkeypatch) -> None:
    """Q5: the alembic head and every composer setting move the code version (here, the Portfolio cursor key)."""
    from assetops_backend.chain import watermark

    assert watermark.alembic_head() == "0047_chain_response"
    watermark.code_version.cache_clear()
    monkeypatch.setenv("ASSETOPS_ESTATE_PORTFOLIO_CURSOR_KEY_HEX", "1a" * 32)
    one = watermark.code_version()
    watermark.code_version.cache_clear()
    monkeypatch.setenv("ASSETOPS_ESTATE_PORTFOLIO_CURSOR_KEY_HEX", "2b" * 32)
    try:
        assert watermark.code_version() != one
    finally:
        watermark.code_version.cache_clear()
