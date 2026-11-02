"""WALK1-3: migration 0040 (declared price per kWh for productive users) on real Postgres.

The 0026 pattern: the key/unit CHECKs widen for `productive_use_price_per_kwh` (`currency/kWh`), a strictly positive
CHECK is added for it, the store publishes it, and the downgrade refuses while any such row exists and otherwise
restores the 0026 CHECK texts byte for byte.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from decimal import Decimal

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError, IntegrityError
    from test_s1_bindings_postgres import _alembic, engine, store  # noqa: F401
    from test_s4_consequence_store_postgres import _release_connections, site  # noqa: F401
    from test_w203_cold_migration_postgres import constraint, head
    from test_w206_ev_migration_postgres import Ctx

    from assetops_backend.financials.adapters.postgres_assumption_store import PostgresAssumptionStore
    from assetops_backend.financials.assumptions import SYSTEM_PUBLISHER, Publication, PublicationRefused

HEAD = "0041_walk1_objective_min_days"  # WALK1-3b: the sole head sits above the 0040 migration under test
THIS = "0040_walk1_productive_price"
PREVIOUS = "0039_merge_objectives_cc"
KEY = "productive_use_price_per_kwh"
REFUSED = "Downgrade of 0040_walk1_productive_price refused"
KEY_CHECK_0040 = ("CHECK ((assumption_key = ANY (ARRAY['diesel_price_per_litre'::text, 'ev_gross_tariff_per_kwh'::text, "
                  "'productive_use_price_per_kwh'::text])))")
UNIT_CHECK_0040 = ("CHECK ((((assumption_key = 'diesel_price_per_litre'::text) AND (unit = 'currency/L'::text)) OR "
                   "((assumption_key = 'ev_gross_tariff_per_kwh'::text) AND (unit = 'currency/kWh'::text)) OR "
                   "((assumption_key = 'productive_use_price_per_kwh'::text) AND (unit = 'currency/kWh'::text))))")
POSITIVE_0040 = "CHECK (((assumption_key <> 'productive_use_price_per_kwh'::text) OR (value > (0)::numeric)))"
KEY_CHECK_0026 = ("CHECK ((assumption_key = ANY (ARRAY['diesel_price_per_litre'::text, "
                  "'ev_gross_tariff_per_kwh'::text])))")
UNIT_CHECK_0026 = ("CHECK ((((assumption_key = 'diesel_price_per_litre'::text) AND (unit = 'currency/L'::text)) OR "
                   "((assumption_key = 'ev_gross_tariff_per_kwh'::text) AND (unit = 'currency/kWh'::text))))")
T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)


def publication(*, value="0.25", currency="USD", idem="walk1-productive-1") -> "Publication":
    return Publication(assumption_key=KEY, currency=currency, value=Decimal(value), basis="AUTHORED_ESTIMATE",
                       source_reference="WALK1-3 authored test price", valid_from=T0, valid_to=None,
                       change_kind="INITIAL", correction_reason=None, expected_prior_revision_id=None,
                       idempotency_key=idem, channel="SYSTEM_FIXTURE", provenance={})


def publish(tenant, site_id, **kw):
    prices = PostgresAssumptionStore(URL)
    try:
        return prices.publish(tenant, site_id, publication(**kw), SYSTEM_PUBLISHER)
    finally:
        prices.dispose()


def raw_insert(engine, ctx, *, unit="currency/kWh", value="0.25") -> None:
    with engine.begin() as c:
        c.execute(text(
            "INSERT INTO financial_assumption_revision (id, tenant_id, site_id, assumption_key, revision_no, currency, "
            "unit, value, basis, source_reference, valid_from, change_kind, actor_kind, actor_id, channel, "
            "authorization_basis, provenance, idempotency_key, request_sha256, recorded_at) VALUES (gen_random_uuid(), :t, :s, "
            ":k, 1, 'USD', :u, :v, 'AUTHORED_ESTIMATE', 'raw', :f, 'INITIAL', 'SYSTEM', 'test', 'SYSTEM_FIXTURE', "
            "'test', '{}'::jsonb, 'raw-insert', repeat('a', 64), now())"),
            {"t": ctx.t, "s": ctx.s, "k": KEY, "u": unit, "v": value, "f": T0})


def release(site, engine) -> None:
    site.store.dispose()
    site.prices.dispose()
    engine.dispose()


def test_0040_widens_checks_and_the_store_publishes_the_price(site, engine) -> None:  # noqa: F811
    from alembic.script import ScriptDirectory

    script = ScriptDirectory.from_config(_alembic())
    assert script.get_heads() == [HEAD] and script.get_revision(THIS).down_revision == PREVIOUS
    assert head(engine) == HEAD
    assert constraint(engine, "financial_assumption_revision_assumption_key_check") == KEY_CHECK_0040
    assert constraint(engine, "financial_assumption_revision_unit_check") == UNIT_CHECK_0040
    assert constraint(engine, "financial_assumption_revision_productive_positive") == POSITIVE_0040
    ctx = Ctx(site, engine)
    for kw, name in (({"unit": "currency/L"}, "financial_assumption_revision_unit_check"),
                     ({"value": "0"}, "financial_assumption_revision_productive_positive"),
                     ({"value": "-0.1"}, "financial_assumption_revision")):
        with pytest.raises(IntegrityError, match=name):
            raw_insert(engine, ctx, **kw)
    raw_insert(engine, ctx)  # the raw row is admitted at a positive value and currency/kWh (control)
    with engine.begin() as c:
        c.execute(text("SET LOCAL session_replication_role = replica"))
        c.execute(text("DELETE FROM financial_assumption_revision WHERE idempotency_key = 'raw-insert'"))
    published = publish(ctx.t, ctx.s)
    with engine.connect() as c:
        row = c.execute(text("SELECT unit, value, currency FROM financial_assumption_revision WHERE id = :i"),
                        {"i": published.revision_id}).one()
    assert (row.unit, row.value, row.currency) == ("currency/kWh", Decimal("0.25"), "USD")
    for kw, code in (({"value": "0", "idem": "z"}, "VALUE_NOT_POSITIVE"),
                     ({"currency": "ABC", "idem": "c"}, "CURRENCY_NOT_ISO")):
        prices = PostgresAssumptionStore(URL)
        try:
            with pytest.raises(PublicationRefused) as refused:
                prices.publish(ctx.t, ctx.s, publication(**kw), SYSTEM_PUBLISHER)
            assert refused.value.code == code
        finally:
            prices.dispose()


def test_0040_downgrade_refuses_with_a_price_then_restores_0026_checks(site, engine) -> None:  # noqa: F811
    from alembic import command

    ctx = Ctx(site, engine)
    config = _alembic()
    # An empty downgrade restores the 0026 CHECK texts exactly and drops the productive CHECK.
    release(site, engine)
    try:
        command.downgrade(config, PREVIOUS)
        assert head(engine) == PREVIOUS
        assert constraint(engine, "financial_assumption_revision_assumption_key_check") == KEY_CHECK_0026
        assert constraint(engine, "financial_assumption_revision_unit_check") == UNIT_CHECK_0026
        assert constraint(engine, "financial_assumption_revision_productive_positive") is None
    finally:
        command.upgrade(config, "head")
    assert head(engine) == HEAD and constraint(engine, "financial_assumption_revision_unit_check") == UNIT_CHECK_0040
    # With a published productive-use price the downgrade refuses and changes nothing.
    publish(ctx.t, ctx.s)
    engine.dispose()
    with pytest.raises(DBAPIError, match=REFUSED):
        command.downgrade(config, PREVIOUS)
    assert head(engine) == HEAD
    assert constraint(engine, "financial_assumption_revision_productive_positive") == POSITIVE_0040
