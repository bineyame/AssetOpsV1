"""W2-07: migration `0026_w2_ev_money` (commit 1) against Postgres.

`.agent/W2-07-build-spec.md` "Concrete-artifact closure (2026-10-19)" section 1 and "Post-W2-06 reconciliation
(2026-10-20)" commit 1: the authored EV tariff key, five append-only scoped EV consequence tables, trigger-only work
with the exact scoped `ON CONFLICT (tenant_id,site_id,window_start,window_end,dirty_basis_sha256) DO NOTHING` target,
backfill and a guarded downgrade that refuses while any EV tariff or 0026 row exists. Schema-level rows written here
(revisions, links, attempts) only exercise constraints; the product writer arrives with commit 2.

The mini-grid `site` tests run first; the registered EV `chain` test recreates the module database, so it runs last.
Requires ASSETOPS_TEST_DATABASE_URL.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError, IntegrityError
    from test_s1_bindings_postgres import _alembic, engine, store  # noqa: F401
    from test_s4_consequence_store_postgres import _release_connections, site  # noqa: F401
    from test_w203_cold_migration_postgres import T0, _replica, _sha, constraint, head, minigrid_rows, scalar, table_exists
    from test_w205b_ev_replay_postgres import chain  # noqa: F401
    from test_w206_ev_migration_postgres import Ctx, insert_revision, insert_session

    from assetops_backend.financials.adapters.postgres_assumption_store import PostgresAssumptionStore
    from assetops_backend.financials.assumptions import SYSTEM_PUBLISHER, Publication, PublicationRefused

HEAD = "0026_w2_ev_money"
PREVIOUS = "0025_w2_ev_session"
REFUSED = "Downgrade of 0026_w2_ev_money refused"
EV_MONEY = ("ev_consequence_revision", "ev_consequence_session", "ev_consequence_evidence", "ev_consequence_work",
            "ev_consequence_work_attempt")
EV_KEY = "ev_gross_tariff_per_kwh"
DIRTY_KEY = "ev_consequence_work_dirty_unique"
ARBITER = "ON CONFLICT (tenant_id,site_id,window_start,window_end,dirty_basis_sha256) DO NOTHING"
TRIGGERS = ("ev_consequence_dirty_session", "ev_consequence_dirty_assessment", "ev_consequence_dirty_tariff",
            "ev_consequence_dirty_source_gate", "ev_consequence_dirty_accepted", "ev_consequence_tariff_key") + tuple(
    f"{t}_append_only" for t in EV_MONEY)
FUNCTIONS = ("ev_consequence_enqueue", "ev_consequence_on_session", "ev_consequence_on_assessment",
             "ev_consequence_on_tariff", "ev_consequence_on_source_gate", "ev_consequence_on_accepted",
             "ev_consequence_tariff_key")


# --- helpers -----------------------------------------------------------------------------------------------------


def publication(*, value="0.27775", currency="KES", valid_from=T0, valid_to=T0 + timedelta(hours=8),
                idem="w207-tariff-1", key=EV_KEY) -> "Publication":
    return Publication(assumption_key=key, currency=currency, value=Decimal(value), basis="AUTHORED_ESTIMATE",
                       source_reference="W2-07 authored test tariff", valid_from=valid_from, valid_to=valid_to,
                       change_kind="INITIAL", correction_reason=None, expected_prior_revision_id=None,
                       idempotency_key=idem, channel="SYSTEM_FIXTURE", provenance={})


def publish(tenant: UUID, site_id: UUID, **kw) -> UUID:
    prices = PostgresAssumptionStore(URL)
    try:
        return prices.publish(tenant, site_id, publication(**kw), SYSTEM_PUBLISHER).revision_id
    finally:
        prices.dispose()


def refused_code(tenant: UUID, site_id: UUID, **kw) -> str:
    prices = PostgresAssumptionStore(URL)
    try:
        with pytest.raises(PublicationRefused) as refused:
            prices.publish(tenant, site_id, publication(**kw), SYSTEM_PUBLISHER)
        return refused.value.code
    finally:
        prices.dispose()


def remove_money(engine) -> None:  # noqa: F811
    _replica(engine, "DELETE FROM ev_consequence_work_attempt", "DELETE FROM ev_consequence_work",
             "DELETE FROM ev_consequence_evidence", "DELETE FROM ev_consequence_session",
             "DELETE FROM ev_consequence_revision",
             f"DELETE FROM financial_assumption_assignment WHERE assumption_key = '{EV_KEY}'",
             f"DELETE FROM financial_assumption_revision WHERE assumption_key = '{EV_KEY}'")


def remove_sessions(engine) -> None:  # noqa: F811
    _replica(engine, "DELETE FROM ev_meter_interval", "DELETE FROM ev_session_evidence",
             "DELETE FROM ev_session_revision", "DELETE FROM ev_session")


def financial_constraints(engine) -> dict:  # noqa: F811
    """Every constraint on the 0010-0012 financial tables except the two widened key/unit CHECKs and the EV-only
    positive CHECK: byte-identical across 0025 and 0026."""
    with engine.connect() as c:
        return {r[0]: r[1] for r in c.execute(text(
            "SELECT conrelid::regclass::text || '.' || conname, pg_get_constraintdef(oid) FROM pg_constraint "
            "WHERE conrelid::regclass::text LIKE 'financial\\_%' AND conname NOT IN ("
            "'financial_assumption_revision_assumption_key_check', 'financial_assumption_revision_unit_check', "
            "'financial_assumption_revision_ev_positive')"))}


def counted(engine, sql, **params) -> int:  # noqa: F811
    return int(scalar(engine, sql, **params))


def insert_consequence(engine, ctx, *, state="UNPRICED", quantity=None, tariff=None, value=None, currency=None,
                       amount=None, basis="c-1", revision_no=1, site_id=None, finding=None):  # noqa: F811
    cid = uuid4()
    with engine.begin() as c:
        c.execute(text(
            "INSERT INTO ev_consequence_revision (id, tenant_id, site_id, finding_revision_id, assessment_revision_id, "
            "revision_no, basis_sha256, technical_input_sha256, window_start, window_end, quantity_kwh, "
            "tariff_revision_id, tariff_value, currency, amount, state, reason, source_gate, overlap_group, "
            "recorded_at) VALUES (:i, :t, :s, :f, :a, :n, :b, :ti, :ws, :we, CAST(:q AS numeric), :tr, "
            "CAST(:v AS numeric), :cur, CAST(:amt AS numeric), :state, 'TARIFF_MISSING', 'REGISTERED_SIMULATION', "
            ":og, now())"),
            {"i": cid, "t": ctx.t, "s": site_id or ctx.s, "f": finding, "a": ctx.assessment, "n": revision_no,
             "b": _sha(basis), "ti": _sha(f"technical:{basis}"), "ws": T0, "we": T0 + timedelta(hours=1),
             "q": quantity, "tr": tariff, "v": value, "cur": currency, "amt": amount, "state": state,
             "og": "ev:" + _sha(f"overlap:{basis}")})
    return cid


def insert_attempt(engine, ctx, work_id, n, outcome="SUCCEEDED", error=None):  # noqa: F811
    with engine.begin() as c:
        c.execute(text(
            "INSERT INTO ev_consequence_work_attempt (id, tenant_id, site_id, work_id, attempt_no, outcome, "
            "error_code, started_at, finished_at) VALUES (gen_random_uuid(), :t, :s, :w, :n, :o, :e, now(), now())"),
            ctx.p(w=work_id, n=n, o=outcome, e=error))


def raises(engine, sql, params, error=IntegrityError, match=None) -> None:  # noqa: F811
    with pytest.raises(error, match=match):
        with engine.begin() as c:
            c.execute(text(sql), params)


def downgrade_refused(site, engine) -> None:  # noqa: F811
    from alembic import command

    config = _alembic()
    site.store.dispose()
    site.prices.dispose()
    engine.dispose()
    with pytest.raises(DBAPIError, match=REFUSED):
        command.downgrade(config, PREVIOUS)
    assert head(engine) == HEAD and all(table_exists(engine, t) for t in EV_MONEY)  # nothing dropped


def dirty(engine, tenant, site_id, start, end, cause, locator) -> str:  # noqa: F811
    """The dirty-event SHA the 0026 enqueue function computes (identifies the event, not a money basis)."""
    return scalar(engine, "SELECT encode(sha256(convert_to(jsonb_build_array(CAST(:t AS text), CAST(:s AS text), "
                          "CAST(:a AS timestamptz), CAST(:b AS timestamptz), CAST(:c AS text), CAST(:i AS text))::text, "
                          "'UTF8')), 'hex')", t=str(tenant), s=str(site_id), a=start, b=end, c=cause, i=str(locator))


# --- commit 1: schema, key and downgrade -------------------------------------------------------------------------


class TestMigration0026:
    def test_0026_follows_installed_0025_and_preserves_diesel(self, site, engine) -> None:  # noqa: F811
        from alembic import command
        from alembic.script import ScriptDirectory

        ctx = Ctx(site, engine)
        script = ScriptDirectory.from_config(_alembic())
        assert script.get_heads() == [HEAD] and script.get_revision(HEAD).down_revision == PREVIOUS
        assert head(engine) == HEAD
        assert constraint(engine, "financial_assumption_revision_assumption_key_check") == (
            "CHECK ((assumption_key = ANY (ARRAY['diesel_price_per_litre'::text, 'ev_gross_tariff_per_kwh'::text])))")
        assert constraint(engine, "financial_assumption_revision_unit_check") == (
            "CHECK ((((assumption_key = 'diesel_price_per_litre'::text) AND (unit = 'currency/L'::text)) OR "
            "((assumption_key = 'ev_gross_tariff_per_kwh'::text) AND (unit = 'currency/kWh'::text))))")
        assert constraint(engine, "financial_assumption_revision_ev_positive") == (
            "CHECK (((assumption_key <> 'ev_gross_tariff_per_kwh'::text) OR (value > (0)::numeric)))")
        assert constraint(engine, "ev_consequence_revision_tariff_fk") == (
            "FOREIGN KEY (tenant_id, site_id, tariff_assumption_key, tariff_revision_id) REFERENCES "
            "financial_assumption_revision(tenant_id, site_id, assumption_key, id)")
        assert counted(engine, "SELECT count(*) FROM pg_trigger WHERE tgname = ANY(:n)", n=list(TRIGGERS)) == 11
        assert counted(engine, "SELECT count(*) FROM pg_proc WHERE proname = ANY(:n)", n=list(FUNCTIONS)) == 7

        # Diesel publication and reads are unchanged; the EV key is authored, positive and ISO-coded only.
        site.publish("v1")
        diesel = scalar(engine, "SELECT unit FROM financial_assumption_revision WHERE assumption_key = "
                                "'diesel_price_per_litre' ORDER BY revision_no LIMIT 1")
        assert diesel == "currency/L"
        assert refused_code(ctx.t, ctx.s, currency="ABC") == "CURRENCY_NOT_ISO"
        assert refused_code(ctx.t, ctx.s, currency="kes") == "CURRENCY_NOT_ISO"
        assert refused_code(ctx.t, ctx.s, value="0") == "VALUE_NOT_POSITIVE"
        assert refused_code(ctx.t, ctx.s, value="-0.1") == "VALUE_NOT_POSITIVE"
        assert refused_code(ctx.t, ctx.s, key="ev_tariff") == "UNKNOWN_ASSUMPTION_KEY"
        diesel_id = scalar(engine, "SELECT id FROM financial_assumption_revision WHERE assumption_key = "
                                   "'diesel_price_per_litre' ORDER BY revision_no LIMIT 1")
        with engine.connect() as c:
            columns = [r[0] for r in c.execute(text(
                "SELECT column_name FROM information_schema.columns WHERE table_name = 'financial_assumption_revision' "
                "ORDER BY ordinal_position"))]
        override = {"id": "gen_random_uuid()", "assumption_key": f"'{EV_KEY}'", "unit": ":unit",
                    "value": "CAST(:value AS numeric)", "idempotency_key": "'raw-ev'", "prior_revision_id": "NULL"}
        copy = (f"INSERT INTO financial_assumption_revision ({', '.join(columns)}) SELECT "
                + ", ".join(override.get(col, col) for col in columns)
                + " FROM financial_assumption_revision WHERE id = :d")
        raises(engine, copy, {"d": diesel_id, "unit": "currency/L", "value": "0.3"},
               match="financial_assumption_revision_unit_check")
        raises(engine, copy, {"d": diesel_id, "unit": "currency/kWh", "value": "0"},
               match="financial_assumption_revision_ev_positive")
        tariff = publish(ctx.t, ctx.s)
        stored = scalar(engine, "SELECT unit || ' ' || value::text || ' ' || currency FROM "
                                "financial_assumption_revision WHERE id = :i", i=tariff)
        assert stored == "currency/kWh 0.27775 KES"
        assert counted(engine, "SELECT count(*) FROM ev_consequence_work") == 0  # no EV assessment on this Site
        at_head = financial_constraints(engine)
        before_rows = minigrid_rows(engine)
        key_check = constraint(engine, "financial_assumption_revision_assumption_key_check")

        # An EV tariff alone refuses the downgrade; nothing is dropped or deleted.
        downgrade_refused(site, engine)
        remove_money(engine)
        config = _alembic()
        try:
            command.downgrade(config, PREVIOUS)  # genuinely empty: allowed
            assert head(engine) == PREVIOUS and not any(table_exists(engine, t) for t in EV_MONEY)
            assert counted(engine, "SELECT count(*) FROM pg_trigger WHERE tgname = ANY(:n)", n=list(TRIGGERS)) == 0
            assert counted(engine, "SELECT count(*) FROM pg_proc WHERE proname = ANY(:n)", n=list(FUNCTIONS)) == 0
            assert constraint(engine, "financial_assumption_revision_assumption_key_check") == (
                "CHECK ((assumption_key = 'diesel_price_per_litre'::text))")
            assert constraint(engine, "financial_assumption_revision_unit_check") == "CHECK ((unit = 'currency/L'::text))"
            assert constraint(engine, "financial_assumption_revision_ev_positive") is None
            assert financial_constraints(engine) == at_head and minigrid_rows(engine) == before_rows
            assert scalar(engine, "SELECT count(*) FROM financial_assumption_revision WHERE id = :d", d=diesel_id) == 1
            command.upgrade(config, "head")
        finally:
            if head(engine) != HEAD:
                command.upgrade(config, "head")
        assert constraint(engine, "financial_assumption_revision_assumption_key_check") == key_check
        assert financial_constraints(engine) == at_head and minigrid_rows(engine) == before_rows

        # Backfilled or trigger work alone, and a consequence revision alone, each refuse the downgrade.
        session = insert_session(engine, ctx)
        insert_revision(engine, ctx, session)
        assert counted(engine, "SELECT count(*) FROM ev_consequence_work") == 1
        try:
            downgrade_refused(site, engine)
        finally:
            remove_money(engine)
            remove_sessions(engine)
        insert_consequence(engine, ctx)
        assert counted(engine, "SELECT count(*) FROM ev_consequence_work") == 0
        try:
            downgrade_refused(site, engine)
        finally:
            remove_money(engine)
        assert head(engine) == HEAD

    def test_0026_scoped_constraints_state_arithmetic_and_append_only(self, site, engine) -> None:  # noqa: F811
        ctx = Ctx(site, engine)
        tariff = publish(ctx.t, ctx.s)
        site.publish("v1")
        diesel = scalar(engine, "SELECT id FROM financial_assumption_revision WHERE assumption_key = "
                                "'diesel_price_per_litre' ORDER BY revision_no LIMIT 1")
        try:
            estimated = insert_consequence(engine, ctx, state="ESTIMATED", quantity="30.000", tariff=tariff,
                                           value="0.27775", currency="KES", amount="8.33250000", basis="est")
            assert scalar(engine, "SELECT amount::text FROM ev_consequence_revision WHERE id = :i",
                          i=estimated) == "8.33250000"
            assert scalar(engine, "SELECT tariff_assumption_key FROM ev_consequence_revision WHERE id = :i",
                          i=estimated) == EV_KEY
            bad = [
                # ESTIMATED needs every field and the exact unrounded product.
                (dict(state="ESTIMATED", quantity="30.000", tariff=tariff, value="0.27775", currency="KES",
                      amount="8.33"), "ev_consequence_revision_state"),
                (dict(state="ESTIMATED", quantity=None, tariff=tariff, value="0.27775", currency="KES",
                      amount="8.33250000"), "ev_consequence_revision_state"),
                # UNPRICED/WITHHELD never carry an amount or currency.
                (dict(state="UNPRICED", quantity="30.000", amount="0"), "ev_consequence_revision_state"),
                (dict(state="WITHHELD", currency="KES"), "ev_consequence_revision_state"),
                (dict(quantity="NaN"), "ev_consequence_revision_quantity"),
                (dict(quantity="-1"), "ev_consequence_revision_quantity"),
                (dict(state="WITHHELD", value="0"), "ev_consequence_revision_tariff_value"),
                (dict(state="WITHHELD", currency="kes"), "ev_consequence_revision_currency"),  # CHECKs by name
                # A diesel revision is not an EV tariff (insert trigger before the generated-key scoped FK), and a
                # value/currency mismatch is refused.
                (dict(state="UNPRICED", tariff=diesel, value="1.25"), "same-Site EV tariff revision"),
                (dict(state="UNPRICED", tariff=tariff, value="0.3"), "same-Site EV tariff revision"),
                (dict(state="ESTIMATED", quantity="1", tariff=tariff, value="0.27775", currency="USD",
                      amount="0.27775"), "same-Site EV tariff revision"),
                (dict(site_id=uuid4()), "ev_consequence_revision_site_fk"),
                (dict(basis="est"), "ev_consequence_revision_basis_unique"),
                (dict(basis="other", revision_no=1), "ev_consequence_revision_number_unique"),
            ]
            for i, (kw, name) in enumerate(bad):
                kw = {"basis": f"bad-{i}", "revision_no": 100 + i, **kw}
                with pytest.raises(DBAPIError, match=name):
                    insert_consequence(engine, ctx, **kw)
            with pytest.raises(DBAPIError, match="revision_no"):
                insert_consequence(engine, ctx, basis="zero", revision_no=0)

            # Scoped links: a foreign Site never reaches this Site's revision, session or evidence.
            session = insert_session(engine, ctx)
            srev = insert_revision(engine, ctx, session)
            with engine.begin() as c:
                c.execute(text("INSERT INTO ev_consequence_session (tenant_id, site_id, consequence_revision_id, "
                               "session_revision_id, included_kwh) VALUES (:t, :s, :c, :r, 30.000)"),
                          ctx.p(c=estimated, r=srev))
                c.execute(text("INSERT INTO ev_consequence_evidence (tenant_id, site_id, consequence_revision_id, "
                               "evidence_id) VALUES (:t, :s, :c, :e)"), ctx.p(c=estimated, e=ctx.evidence[0]))
            other = uuid4()
            raises(engine, "INSERT INTO ev_consequence_session (tenant_id, site_id, consequence_revision_id, "
                           "session_revision_id, included_kwh) VALUES (:t, :o, :c, :r, 1)",
                   ctx.p(o=other, c=estimated, r=srev), match="ev_consequence_session_consequence_fk")
            raises(engine, "INSERT INTO ev_consequence_session (tenant_id, site_id, consequence_revision_id, "
                           "session_revision_id, included_kwh) VALUES (:t, :s, :c, :r, -1)",
                   ctx.p(c=estimated, r=srev), match="ev_consequence_session_quantity")
            raises(engine, "INSERT INTO ev_consequence_session (tenant_id, site_id, consequence_revision_id, "
                           "session_revision_id, included_kwh) VALUES (:t, :s, :c, :r, 1)",
                   ctx.p(c=estimated, r=uuid4()), match="ev_consequence_session_session_fk")
            raises(engine, "INSERT INTO ev_consequence_evidence (tenant_id, site_id, consequence_revision_id, "
                           "evidence_id) VALUES (:t, :s, :c, :e)", ctx.p(c=estimated, e=uuid4()),
                   match="ev_consequence_evidence_accepted_fk")
            raises(engine, "INSERT INTO ev_consequence_evidence (tenant_id, site_id, consequence_revision_id, "
                           "evidence_id) VALUES (:t, :s, :c, :e)", ctx.p(c=estimated, e=ctx.evidence[0]),
                   match="ev_consequence_evidence_pkey")

            # Work comes from the session-revision trigger; attempts are append-only with one success.
            work = scalar(engine, "SELECT id FROM ev_consequence_work")
            assert counted(engine, "SELECT count(*) FROM ev_consequence_work") == 1
            insert_attempt(engine, ctx, work, 1, "FAILED", "INPUT_UNAVAILABLE")
            raises(engine, "INSERT INTO ev_consequence_work_attempt (id, tenant_id, site_id, work_id, attempt_no, "
                           "outcome, error_code, started_at, finished_at) VALUES (gen_random_uuid(), :t, :s, :w, 2, "
                           "'FAILED', NULL, now(), now())", ctx.p(w=work), match="ev_consequence_attempt_error")
            raises(engine, "INSERT INTO ev_consequence_work_attempt (id, tenant_id, site_id, work_id, attempt_no, "
                           "outcome, error_code, started_at, finished_at) VALUES (gen_random_uuid(), :t, :s, :w, 2, "
                           "'SUCCEEDED', 'X', now(), now())", ctx.p(w=work), match="ev_consequence_attempt_error")
            raises(engine, "INSERT INTO ev_consequence_work_attempt (id, tenant_id, site_id, work_id, attempt_no, "
                           "outcome, error_code, started_at, finished_at) VALUES (gen_random_uuid(), :t, :s, :w, 1, "
                           "'SUCCEEDED', NULL, now(), now())", ctx.p(w=work), match="ev_consequence_attempt_no_unique")
            insert_attempt(engine, ctx, work, 2)
            with pytest.raises(IntegrityError, match="ev_consequence_attempt_one_success"):
                insert_attempt(engine, ctx, work, 3)
            raises(engine, "INSERT INTO ev_consequence_work_attempt (id, tenant_id, site_id, work_id, attempt_no, "
                           "outcome, error_code, started_at, finished_at) VALUES (gen_random_uuid(), :t, :s, :w, 4, "
                           "'FAILED', 'X', now(), now() - interval '1 second')", ctx.p(w=work),
                   match="ev_consequence_attempt_time")

            for table in EV_MONEY:
                for statement in (f"UPDATE {table} SET tenant_id = tenant_id", f"DELETE FROM {table}"):
                    with pytest.raises(DBAPIError, match="append-only"):
                        with engine.begin() as c:
                            c.execute(text(statement))
                assert counted(engine, f"SELECT count(*) FROM {table}") >= 1, table
        finally:
            remove_money(engine)
            remove_sessions(engine)

    def test_r3_store_publishes_ev_tariff_and_public_post_stays_401(self, site, engine) -> None:  # noqa: F811
        # q1 R3: the fixture publication is a store request under SYSTEM_PUBLISHER/SYSTEM_FIXTURE, never HTTP.
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        from assetops_backend.financial_api import build_financial_assumption_router

        ctx = Ctx(site, engine)
        try:
            prices = PostgresAssumptionStore(URL)
            try:
                published = prices.publish(ctx.t, ctx.s, publication(idem="w207-r3-store"), SYSTEM_PUBLISHER)
            finally:
                prices.dispose()
            assert isinstance(published.revision_id, UUID) and published.recorded_at.tzinfo is not None
            assert not published.replayed and published.change_kind == "INITIAL"
            row = scalar(engine, "SELECT channel || '|' || assumption_key || '|' || unit || '|' || value::text "
                                 "|| '|' || currency FROM financial_assumption_revision WHERE id = :i",
                         i=published.revision_id)
            assert row == f"SYSTEM_FIXTURE|{EV_KEY}|currency/kWh|0.27775|KES"
            before = counted(engine, "SELECT count(*) FROM financial_assumption_revision")
            app = FastAPI()
            app.include_router(build_financial_assumption_router(lambda code: ("EV-LAB-001", ctx.t, ctx.s)))
            response = TestClient(app).post("/api/sites/EV-LAB-001/financial-assumptions", json={
                "assumption_key": EV_KEY, "value": "0.27775", "currency": "KES"})
            assert response.status_code == 401 and response.json()["detail"]["code"] == "UNAUTHENTICATED"
            assert counted(engine, "SELECT count(*) FROM financial_assumption_revision") == before
        finally:
            remove_money(engine)


def test_r4_ev_currency_and_value_validation_is_ev_only() -> None:
    # q1 R4: active ISO-4217 and strictly positive for the EV key only; diesel keeps its shape rule and zero.
    from assetops_backend.financials.assumptions import validate

    validate(publication())  # KES accepted
    for kw, code in (({"currency": "ABC"}, "CURRENCY_NOT_ISO"), ({"value": "0"}, "VALUE_NOT_POSITIVE"),
                     ({"value": "-1"}, "VALUE_NOT_POSITIVE")):
        with pytest.raises(PublicationRefused) as refused:
            validate(publication(**kw))
        assert refused.value.code == code
    validate(publication(key="diesel_price_per_litre", currency="ABC", value="1.30"))
    validate(publication(key="diesel_price_per_litre", currency="ABC", value="0"))


# --- commit 1: trigger-only work through the registered EV path (recreates the module database: keep last) ---------


def work_rows(built) -> set[tuple]:
    with built.engine.connect() as c:
        return {(r.window_start, r.window_end, r.dirty_basis_sha256) for r in c.execute(text(
            "SELECT window_start, window_end, dirty_basis_sha256 FROM ev_consequence_work WHERE tenant_id = :t "
            "AND site_id = :s"), {"t": built.tenant_id, "s": built.site_id})}


def assessments(built) -> list:
    with built.engine.connect() as c:
        return c.execute(text("SELECT id, window_start, window_end FROM assessment_revision WHERE site_id = :s "
                              "AND analytic_id = 'ev-session/1' ORDER BY id"), {"s": built.site_id}).all()


def expected(built, rows) -> set[tuple]:
    return {(a, b, dirty(built.engine, built.tenant_id, built.site_id, a, b, cause, locator))
            for a, b, cause, locator in rows}


def ev_accepted(built) -> list:
    with built.engine.connect() as c:
        return c.execute(text(
            "SELECT id, source_time, batch_id FROM accepted_evidence WHERE site_id = :s AND ((family = 'EVENT' AND "
            "record_kind LIKE 'EV_%') OR (family = 'MEASUREMENT' AND measurement = 'INTERVAL_DELTA' AND connector_id "
            "IS NOT NULL)) ORDER BY id"), {"s": built.site_id}).all()


def unpublished_ev_upload(built, linked_batch_id) -> tuple[UUID, UUID]:
    """Re-seal one qualifying EV envelope of a linked batch under a new sequence and event identity, as an upload with
    no publication, through `BatchIngestionService` and the same `PostgresEvidenceLedger`; return (accepted, batch)."""
    import dataclasses

    from assetops_backend.evidence.adapters.postgres_evidence_ledger import PostgresEvidenceLedger
    from assetops_backend.evidence.ledger_service import BatchIngestionService
    from assetops_backend.evidence.ledger import GatewayPrincipal
    from assetops_contracts.ingestion_batch_v2 import parse_canonical_batch_v2_text, seal_batch_v2
    from assetops_contracts.source_envelope_v3 import v3_message_id
    from assetops_contracts.source_envelope_v4 import canonical_envelope_v4_text, parse_canonical_envelope_v4_text

    with built.engine.connect() as c:
        body = c.execute(text("SELECT batch_text FROM ingestion_batch WHERE id = :b"), {"b": linked_batch_id}).scalar_one()
    batch = parse_canonical_batch_v2_text(body)
    envelope = next(e for e in map(parse_canonical_envelope_v4_text, batch.envelopes)
                    if (e.family == "EVENT" and e.record_kind.startswith("EV_"))
                    or (e.family == "MEASUREMENT" and e.measurement == "INTERVAL_DELTA" and e.connector_id))
    sequence = envelope.sequence + 100000
    changed = dataclasses.replace(
        envelope, sequence=sequence, message_id=v3_message_id(
            site_id=envelope.site_id, gateway_id=envelope.gateway_id, source_id=envelope.source_id,
            sequence_epoch=envelope.sequence_epoch, sequence=sequence),
        **({"event_id": f"{envelope.event_id}-unlinked"} if envelope.family == "EVENT" else
           {"value": str(Decimal(envelope.value) + Decimal("0.001"))}))
    _, sealed = seal_batch_v2(
        site_id=batch.site_id, gateway_id=batch.gateway_id, source_id=batch.source_id, source_mode=batch.source_mode,
        foundation_version=batch.foundation_version, foundation_valid_from=batch.foundation_valid_from,
        binding_set_id=batch.binding_set_id, binding_version=batch.binding_version,
        snapshot_sha256=batch.snapshot_sha256, envelope_texts=[canonical_envelope_v4_text(changed)])
    principal = GatewayPrincipal(tenant_id=built.tenant_id, site_id=built.site_id, gateway_id=UUID(batch.gateway_id),
                                 mode=batch.source_mode)
    receipt = BatchIngestionService(PostgresEvidenceLedger(URL, test_decision_clock_override=built.decision_clock),
                                    built.decision_clock).submit(principal, sealed.encode("utf-8")).receipt
    [accepted] = [d.evidence_id for d in receipt.dispositions if d.decision == "ACCEPTED"]
    with built.engine.connect() as c:
        return UUID(str(accepted)), c.execute(text("SELECT batch_id FROM accepted_evidence WHERE id = :i"),
                                              {"i": UUID(str(accepted))}).scalar_one()


def test_0026_trigger_only_work_and_exact_conflict_constraint(chain, monkeypatch) -> None:  # noqa: F811
    from alembic import command

    from test_w206_ev_store_postgres import run_worker

    built = chain("late-record")
    engine = built.engine
    with engine.connect() as c:
        columns = c.execute(text(
            "SELECT array_agg(a.attname ORDER BY k.ord) FROM pg_constraint x CROSS JOIN LATERAL "
            "unnest(x.conkey) WITH ORDINALITY k(attnum, ord) JOIN pg_attribute a ON a.attrelid = x.conrelid "
            "AND a.attnum = k.attnum WHERE x.conname = :n"), {"n": DIRTY_KEY}).scalar_one()
        enqueue = c.execute(text("SELECT prosrc FROM pg_proc WHERE proname = 'ev_consequence_enqueue'")).scalar_one()
    assert list(columns) == ["tenant_id", "site_id", "window_start", "window_end", "dirty_basis_sha256"]
    assert enqueue.count("ON CONFLICT") == 1 and ARBITER in enqueue

    # Accepted EV rows and their batch links arrive before any EV assessment window exists: no work yet.
    built.start_release_upload()
    first_accepted = {r.id for r in ev_accepted(built)}
    assert first_accepted and work_rows(built) == set()

    # The worker's assessment and session revisions enqueue their exact window (assessment/session triggers).
    run_worker(built)
    heads = assessments(built)
    with engine.connect() as c:
        sessions = c.execute(text("SELECT r.id, a.window_start, a.window_end FROM ev_session_revision r JOIN "
                                  "assessment_revision a ON a.id = r.assessment_revision_id WHERE r.site_id = :s"),
                             {"s": built.site_id}).all()
    assert heads and sessions
    after_run = expected(built, [(a.window_start, a.window_end, "ASSESSMENT_REVISION", a.id) for a in heads]
                         + [(s.window_start, s.window_end, "SESSION_REVISION", s.id) for s in sessions])
    assert work_rows(built) == after_run

    # The late END, split at the ledger's open_batch/decide_chunk seam (q2 R7): the committed link precedes the first
    # accepted row of its batch, so the link trigger finds no EV row; the accepted-row trigger enqueues SOURCE_GATE.
    from assetops_backend.evidence.adapters.postgres_evidence_ledger import PostgresEvidenceLedger

    before_decide: dict = {}
    original = PostgresEvidenceLedger.decide_chunk

    def inspected(self, batch, *args, **kwargs):
        if batch.id not in before_decide:
            before_decide[batch.id] = (work_rows(built), counted(
                engine, "SELECT count(*) FROM batch_publication_link WHERE batch_id = :b", b=batch.id))
        return original(self, batch, *args, **kwargs)

    monkeypatch.setattr(PostgresEvidenceLedger, "decide_chunk", inspected)
    built.advance_late()
    monkeypatch.setattr(PostgresEvidenceLedger, "decide_chunk", original)
    late = [r for r in ev_accepted(built) if r.id not in first_accepted]
    late_rows = [(a.window_start, a.window_end, "ACCEPTED_EV", e.id) for e in late for a in heads
                 if a.window_start <= e.source_time < a.window_end]
    late_batches = sorted({e.batch_id for e in late})
    assert len(late_batches) == 1, late_batches
    [late_batch_id] = late_batches
    gate = expected(built, [(a.window_start, a.window_end, "SOURCE_GATE", late_batch_id) for a in heads])
    # After the late link's open_batch transaction commits, before decide_chunk:
    pre_work, pre_links = before_decide[late_batch_id]
    assert pre_work == after_run
    assert pre_links == 1
    assert gate.isdisjoint(pre_work)
    # After all late accepted chunks commit:
    assert late and late_rows and gate
    assert work_rows(built) == after_run | expected(built, late_rows) | gate
    assert all(counted(engine, "SELECT count(*) FROM ev_consequence_work WHERE tenant_id=:t AND site_id=:s "
                       "AND window_start=:a AND window_end=:b AND dirty_basis_sha256=:d",
                       t=built.tenant_id, s=built.site_id, a=a, b=b, d=d) == 1 for a, b, d in gate)
    with engine.begin() as c:
        for a in heads:
            for _ in range(2):
                c.execute(text("SELECT ev_consequence_enqueue(:t,:s,:a,:b,'SOURCE_GATE',:i)"),
                          {"t": built.tenant_id, "s": built.site_id, "a": a.window_start,
                           "b": a.window_end, "i": late_batch_id})
    assert work_rows(built) == after_run | expected(built, late_rows) | gate

    # Committed linked batches with no qualifying accepted EV row (non-EV records through the ledger): the registered
    # late phase delivers one EV batch only, so these are the first upload's non-EV batches (work stayed empty then).
    with engine.connect() as c:
        quiet = list(c.execute(text(
            "SELECT b.id FROM ingestion_batch b WHERE b.site_id = :s AND b.id <> :late AND NOT EXISTS (SELECT 1 FROM "
            "accepted_evidence e WHERE e.batch_id = b.id AND ((e.family = 'EVENT' AND e.record_kind LIKE 'EV_%') OR "
            "(e.family = 'MEASUREMENT' AND e.measurement = 'INTERVAL_DELTA' AND e.connector_id IS NOT NULL)))"),
            {"s": built.site_id, "late": late_batch_id}).scalars())
    assert quiet and late_batch_id not in quiet
    for b in quiet:
        assert counted(engine, "SELECT count(*) FROM batch_publication_link WHERE batch_id = :b", b=b) == 1
        assert expected(built, [(a.window_start, a.window_end, "SOURCE_GATE", b) for a in heads]).isdisjoint(
            work_rows(built))
    # One real tariff INSERT enqueues every overlapping EV window; a diesel price would not.
    before_tariff = work_rows(built)
    tariff = publish(built.tenant_id, built.site_id, valid_from=datetime(2026, 10, 6, 8, tzinfo=timezone.utc),
                     valid_to=datetime(2026, 10, 6, 16, tzinfo=timezone.utc), idem="w207-trigger-tariff")
    tariff_rows = expected(built, [(a.window_start, a.window_end, "TARIFF_REVISION", tariff) for a in heads])
    assert work_rows(built) == before_tariff | tariff_rows

    # Duplicate enqueue of an existing dirty event: the exact scoped arbiter keeps one row.
    a = heads[0]
    with engine.begin() as c:
        for _ in range(2):
            c.execute(text("SELECT ev_consequence_enqueue(:t, :s, :a, :b, 'TARIFF_REVISION', :i)"),
                      {"t": built.tenant_id, "s": built.site_id, "a": a.window_start, "b": a.window_end, "i": tariff})
    assert work_rows(built) == before_tariff | tariff_rows

    # Backfill: with 0026 rows cleared the downgrade is allowed; upgrade enqueues one BACKFILL row per EV assessment.
    run_worker(built)
    heads = assessments(built)
    remove_money(engine)
    config = _alembic()
    pg_harness_dispose(built)
    try:
        command.downgrade(config, PREVIOUS)
        assert head(engine) == PREVIOUS
        command.upgrade(config, "head")
    finally:
        if head(engine) != HEAD:
            command.upgrade(config, "head")
    backfilled = expected(built, [(a.window_start, a.window_end, "BACKFILL", a.id) for a in heads])
    assert work_rows(built) == backfilled

    # An unlinked qualifying EV acceptance (an unpublished upload through the same ledger) enqueues only ACCEPTED_EV.
    # Last: it makes the Site's EV source MIXED, so no worker runs after it.
    unlinked_id, unlinked_batch = unpublished_ev_upload(built, late_batch_id)
    assert counted(engine, "SELECT count(*) FROM batch_publication_link WHERE batch_id = :b", b=unlinked_batch) == 0
    unlinked_rows = expected(built, [(a.window_start, a.window_end, "ACCEPTED_EV", unlinked_id) for a in heads
                                     if a.window_start <= scalar(engine, "SELECT source_time FROM accepted_evidence "
                                                                 "WHERE id = :i", i=unlinked_id) < a.window_end])
    assert unlinked_rows
    assert work_rows(built) == backfilled | unlinked_rows
    assert expected(built, [(a.window_start, a.window_end, "SOURCE_GATE", unlinked_batch) for a in heads]).isdisjoint(
        work_rows(built))


def pg_harness_dispose(built) -> None:
    import pg_harness

    built.engine.dispose()
    pg_harness.dispose(built.store)
