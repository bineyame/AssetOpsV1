"""3A7 Q1 to Q3 (spec §4, §7 "Postgres"; D-3A6.12, D-3A7.5): migration 0069, the statement and tolerance tables of
the Postgres commercial store, and §6.2's T1, T2 and T4 on the routed database with R2's literals.

Needs `ASSETOPS_TEST_DATABASE_URL` naming a `*_test` database (the harness routes the run to its own clone); skipped
otherwise. Run through `tools/heavy-slot.sh --db`.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError
    from test_s1_bindings_postgres import engine, store  # noqa: F401

    import pg_harness
    from assetops_backend.commercial.adapters.postgres_commercial_store import PostgresCommercialStore
    from assetops_backend.commercial.months import CommercialMonths
    from assetops_backend.commercial.service import CommercialRecords
    from assetops_backend.structure.reconciliation import CommercialReconciliation
    from test_3a1_commercial_service import Clock
    from test_3a7_reconciliation import FIONA, S1_AT, S2_AT, load, only, record, standing

MIGRATION, PREVIOUS = "0069_commercial_reconciliation", "0068_structure_finding"
T0 = datetime(2026, 11, 1, tzinfo=timezone.utc)
T2_FUEL = ("Fuel bought (invoices) (Recorded, Emulated and Declared): the accounts say $505.00 and the records say $512.50, $7.50 "
           "more (1.49%), beyond the $5.05 allowed (1%).")


def _tenant(engine, slug: str) -> UUID:  # noqa: F811
    tid = uuid4()
    with engine.begin() as c:
        c.execute(text("INSERT INTO tenant (id, slug, name, created_at) VALUES (:id, :s, :s, :at)"),
                  {"id": tid, "s": slug, "at": T0})
    return tid


def _site(engine, tid: UUID, code: str, site_type: str) -> UUID:  # noqa: F811
    sid = uuid4()
    with engine.begin() as c:
        c.execute(text(
            "INSERT INTO site (id, tenant_id, site_code, site_code_key, name, site_type, timezone, lifecycle, "
            "origin, proposed_source_mode, created_at) VALUES (:id, :t, :c, lower(:c), :c, :k, 'Africa/Nairobi', "
            "'ACTIVE', 'IMPORTED', 'SIMULATED', :at)"), {"id": sid, "t": tid, "c": code, "k": site_type, "at": T0})
    return sid


@pytest.fixture()
def w(store, engine):  # noqa: F811 - `store` empties the tenant closure, these two tables included
    tid = _tenant(engine, "lakeside-power")
    sites = {code: _site(engine, tid, code, kind) for code, kind in
             (("KOBO-001", "MINIGRID"), ("MTO-001", "MINIGRID"), ("FRZ-001", "COLDCHAIN"))}
    other = _tenant(engine, "harvest-cold")
    sites["COLD-THIKA"] = _site(engine, other, "COLD-THIKA", "COLDCHAIN")
    pg = PostgresCommercialStore(URL)
    clock = Clock()
    months = CommercialMonths(pg, clock=clock)
    yield dict(store=pg, clock=clock, svc=CommercialRecords(pg, clock=clock), months=months, tid=tid, other=other,
               sites=sites, recon=CommercialReconciliation(months, pg))
    pg.dispose()


_STATEMENT = ("INSERT INTO commercial_accounts_statement (id, tenant_id, site_id, period, currency, revenue, fuel_cost, "
              "source_ref, recorded_at, recorded_by, recorded_role, recorded_by_script, result_at_record, "
              "tolerance_at_record) VALUES (:id, :t, :s, '2026-10', 'USD', '1.00', '1.00', 'ref', :at, :by, "
              "'FINANCE_AND_COMMERCIAL_LEAD', true, 'MATCHED', '0.01')")
_TOLERANCE = ("INSERT INTO commercial_reconciliation_tolerance (id, tenant_id, tolerance, owner_ref, owner_ref_sha256, "
              "set_at) VALUES (:id, :t, :v, 'owner/owner-tol.md', :h, :at)")


def _sqlstate(engine, sql: str, params: dict) -> str:  # noqa: F811
    with pytest.raises(DBAPIError) as raised:
        with engine.begin() as c:
            c.execute(text(sql), params)
    return raised.value.orig.sqlstate


def _statement(w, site: UUID | None, tenant: UUID | None = None) -> dict:
    return {"id": uuid4(), "t": tenant or w["tid"], "s": site, "at": T0, "by": FIONA.person_id}


def _tolerance(w, value: str) -> dict:
    return {"id": uuid4(), "t": w["tid"], "v": value, "h": "0" * 64, "at": T0}


# --- Q1: the migration ---------------------------------------------------------------------------------------------

def test_q1_chain_triggers_checks_and_refused_downgrade(w, engine) -> None:  # noqa: F811
    from alembic import command
    from alembic.script import ScriptDirectory

    cfg = pg_harness._alembic(URL)
    script = ScriptDirectory.from_config(cfg).get_revision(MIGRATION)
    assert (script.revision, script.down_revision) == (MIGRATION, PREVIOUS)
    for value in ("0.06", "abc", "0.0000"):  # each a CHECK violation, never a cast error
        assert _sqlstate(engine, _TOLERANCE, _tolerance(w, value)) == "23514", value
    with engine.begin() as c:  # anti-vacuity: the planted rows insert
        c.execute(text(_STATEMENT), _statement(w, w["sites"]["KOBO-001"]))
        c.execute(text(_TOLERANCE), _tolerance(w, "0.02"))
    for table in ("commercial_accounts_statement", "commercial_reconciliation_tolerance"):
        for sql in (f"UPDATE {table} SET tenant_id = tenant_id", f"DELETE FROM {table}"):
            with pytest.raises(DBAPIError, match="append-only|append only|immutable"):
                with engine.begin() as c:
                    c.execute(text(sql))
    w["store"].dispose()
    with pytest.raises(Exception, match="Downgrade refused: management accounts statements or tolerances exist"):
        command.downgrade(cfg, PREVIOUS)
    with engine.begin() as c:  # TRUNCATE is not a row DELETE; the append-only trigger does not fire on it
        c.execute(text("TRUNCATE commercial_accounts_statement, commercial_reconciliation_tolerance"))
    command.downgrade(cfg, PREVIOUS)
    with engine.connect() as c:
        assert c.execute(text("SELECT to_regclass('commercial_accounts_statement')")).scalar_one() is None
        assert c.execute(text("SELECT to_regclass('structure_tolerance')")).scalar_one() is not None
    command.upgrade(cfg, "head")
    pg_harness.assert_at_head(engine)


# --- Q2: §6.2 on the routed database ------------------------------------------------------------------------------

def test_q2_t1_t2_t4_give_r2s_literals(w) -> None:
    load(w, "A", "B")
    s1 = record(w, S1_AT, site=None, revenue="755.00", fuel="505.00")
    (row,) = w["store"].accounts_statements(w["tid"])
    assert (row.id, row.result_at_record, row.tolerance_at_record, row.site_id) == (s1.statement_id, "MATCHED",
                                                                                    "0.01", None)
    assert standing(w, "KOBO-001").text == ("Reconciled: October 2026 (the organisation) matches the management "
                                            "accounts within 1% (Declared).")
    load(w, "C")
    assert only(w).headings[1].text == T2_FUEL
    st = standing(w, "MTO-001")
    assert (st.reason, st.details) == ("THIS_MONTH_NOT_MATCHED", (T2_FUEL,))
    record(w, S2_AT, site=None, revenue="755.00", fuel="510.00")
    assert only(w).headings[1].text == ("Fuel bought (invoices) (Recorded, Emulated and Declared): the accounts say $510.00 and "
                                        "the records say $512.50, $2.50 more, within the $5.10 allowed (1%).")
    assert standing(w, "KOBO-001").reason == "RECONCILED"
    assert [r.site_code for r in w["store"].site_rows(w["tid"])] == ["FRZ-001", "KOBO-001", "MTO-001"]


# --- Q3: the statement's Site is the tenant's -----------------------------------------------------------------------

def test_q3_another_tenants_site_is_refused_by_the_foreign_key(w, engine) -> None:  # noqa: F811
    assert _sqlstate(engine, _STATEMENT, _statement(w, w["sites"]["COLD-THIKA"])) == "23503"
    with engine.begin() as c:  # anti-vacuity: the same Site under its own tenant inserts
        c.execute(text(_STATEMENT), _statement(w, w["sites"]["COLD-THIKA"], w["other"]))
