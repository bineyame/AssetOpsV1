"""WALK1-3 §4.1-§4.3: the Kobo producer declares supply uses and the productive-use price; the reader finds them.

`tools/demo_combined_kobo.py` `configure_at` adds one additive Foundation change at install + 25 min (supply use on
the three feeders; every existing property kept) and `publish_price` publishes the productive-use price beside the
diesel price. The read-only mini-depth reader then names the Grain mill as the one productive user from that
revision on, none before it, and its readings port returns only that feeder's `feeder_demand` rows. Needs
`ASSETOPS_TEST_DATABASE_URL` naming a `*_test` database; skipped (never passed) without it.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "host" / "tests"))  # the S6 demo configuration fixtures configure_at loads

if URL:
    from sqlalchemy import text
    from assetops_backend.financials.adapters.postgres_assumption_store import PostgresAssumptionStore
    from assetops_backend.financials.assumption_read import AssumptionReadService
    from assetops_backend.mini_depth.read import MiniDepthRead
    import test_s1_bindings_postgres as pgb
    from test_s1_bindings_postgres import engine, store  # noqa: F401
    import demo_combined_kobo as producer  # noqa: E402
    import pg_harness

IMPORT_AT = datetime(2026, 10, 1, 6, 0, tzinfo=timezone.utc)
INSTALL_AT = datetime(2026, 10, 2, 6, 0, tzinfo=timezone.utc)


def test_fixture_is_the_declared_demo_price() -> None:
    doc = json.loads(producer.FIXTURE_PRODUCTIVE_PRICE.read_text(encoding="utf-8"))
    assert doc["assumption_key"] == "productive_use_price_per_kwh"
    (step,) = doc["steps"]
    assert (step["step"], step["change_kind"], step["currency"], step["value"], step["basis"],
            step["valid_from"], step["valid_to"], step["idempotency_key"]) == (
        "v1", "INITIAL", "USD", "0.25", "AUTHORED_ESTIMATE", "2026-01-01T00:00:00Z", None, "demo-productive-price-v1")
    assert step["source_reference"] == ("Demonstration price per kWh for productive users, set by the system "
                                        "(illustrative, not a contract rate)")


def _properties(engine, site_id, at: datetime) -> dict[str, dict[str, object]]:  # noqa: F811
    with engine.connect() as c:
        (content,) = c.execute(text(
            "SELECT content FROM foundation_revision WHERE site_id = :s AND valid_from <= :at "
            "AND (valid_to IS NULL OR valid_to > :at) AND superseded_at IS NULL"), {"s": site_id, "at": at}).one()
    content = content if isinstance(content, dict) else json.loads(content)
    return {x["component_id"]: {p["property_key"]: p["value"] for p in x.get("properties") or ()}
            for x in content["components"]}


def test_kobo_declares_supply_uses_and_the_reader_finds_the_productive_user(store, engine) -> None:  # noqa: F811
    result = pgb.imported(store, when=IMPORT_AT)
    pgb.convert(store, pgb.BindingService(store, pgb.Clock(INSTALL_AT)), result.tenant, result.site, pgb.FIXTURE)
    configuration = producer.configure_at(store, result, INSTALL_AT)
    assert configuration["supply_uses_effective_from"] == "2026-10-02T06:25:00Z"
    before = _properties(engine, result.site.id, INSTALL_AT + timedelta(minutes=24))
    after = _properties(engine, result.site.id, INSTALL_AT + timedelta(minutes=26))
    assert not any("supply-use" in props for props in before.values())
    assert {code: props.get("supply-use") for code, props in after.items() if "supply-use" in props} == {
        "load-mill": "PRODUCTIVE", "load-res": "HOUSEHOLD", "load-clinic": "ESSENTIAL_SERVICE"}
    # the declaration carries forward to the story days (it must follow the +20 roles-3 revision to do so)
    assert _properties(engine, result.site.id, INSTALL_AT + timedelta(days=20)) == after
    # additive: every property declared before the change is still declared, with its value
    for code, props in before.items():
        assert {k: v for k, v in after[code].items() if k != "supply-use"} == props

    reader = MiniDepthRead(engine, link_rows=None)
    t, s = result.tenant.id, result.site.id
    assert reader.productive_users(tenant_id=t, site_id=s, at=INSTALL_AT + timedelta(minutes=24), known_at=None) == []
    (mill,) = reader.productive_users(tenant_id=t, site_id=s, at=INSTALL_AT + timedelta(days=1), known_at=None)
    assert (mill["asset_code"], mill["name"]) == ("load-mill", "Grain mill") and mill["asset_id"] is not None
    # a cutoff before the change was recorded (install + 30 min) does not see it
    assert reader.productive_users(tenant_id=t, site_id=s, at=INSTALL_AT + timedelta(days=1),
                                   known_at=INSTALL_AT + timedelta(minutes=29)) == []
    assert reader.productive_readings(tenant_id=t, site_id=s, asset_ids=[mill["asset_id"]], lo=INSTALL_AT,
                                      hi=INSTALL_AT + timedelta(days=1), known_at=None) == []
    assert reader.productive_readings(tenant_id=t, site_id=s, asset_ids=[], lo=INSTALL_AT,
                                      hi=INSTALL_AT + timedelta(days=1), known_at=None) == []

    producer.publish_price(URL, INSTALL_AT + timedelta(hours=1))
    assumptions = PostgresAssumptionStore(URL)
    try:
        series = AssumptionReadService(assumptions).series(t, s, "productive_use_price_per_kwh",
                                                           valid_at=INSTALL_AT + timedelta(days=1), recorded_at=None)
        diesel = assumptions.revisions(t, s, "diesel_price_per_litre")
    finally:
        pg_harness.dispose(assumptions)
    assert series["unit"] == "currency/kWh" and series["selection"]["state"] == "PRICED"
    assert (str(series["selection"]["price"]["value"]), series["selection"]["price"]["currency"]) == ("0.25", "USD")
    assert len(diesel) == 1  # published at the same instant as the diesel price, once each
