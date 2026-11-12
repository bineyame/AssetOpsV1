"""PR-3 (D-PRICE.1): the site-admin price entry route and migration 0060 on real Postgres.

Design: `.agent/architect-sequence-client-scope-2026-11-11.md` revision 5 §5.3 (Tests, Postgres). The Site is S4's
`PowerSite` (a 2.75 L fuel-cost Candidate on 2026-10-06) with the demo diesel fixture's v1 (1.25 USD from 2026-01-01,
open). A price typed through the route as a CORRECTION from 1 Oct is saved by `service:operator-entry` on channel
`SITE_ADMIN_ENTRY`, raises `price.revised`, queues consequence work, and after one worker drain the fuel cost reads
the new price, while the price as known before the save still selects the old one. Requires
ASSETOPS_TEST_DATABASE_URL.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID
from zoneinfo import ZoneInfo

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError
    from test_s1_bindings_postgres import _alembic, engine, store  # noqa: F401
    from test_s4_consequence_recompute_postgres import Rig
    from test_s4_consequence_store_postgres import KEY, POWER_DAY, site  # noqa: F401
    from test_w203_cold_migration_postgres import constraint, head
    from test_ch2_thread_store_postgres import seeded  # noqa: F401
    from test_ch9b1_opportunity_actions_postgres import mill  # noqa: F401
    from test_ch9b3_mill_verdict_postgres import _after, _close, _frozen, _later, _with_productive_price

    from assetops_backend.financial_api import build_financial_assumption_router
    from assetops_backend.financials import fuel_cost as fc
    from assetops_backend.work.operational_entry import ENTRY_PRINCIPAL

THIS = "0060_site_admin_price_entry"
PREVIOUS = "0059_site_period_read"
REFUSED = "Downgrade of 0060_site_admin_price_entry refused"
CHECK_0060 = ("CHECK ((channel = ANY (ARRAY['SYSTEM_CLI'::text, 'SYSTEM_FIXTURE'::text, 'HUMAN_API'::text, "
              "'SITE_ADMIN_ENTRY'::text])))")
CHECK_0010 = "CHECK ((channel = ANY (ARRAY['SYSTEM_CLI'::text, 'SYSTEM_FIXTURE'::text, 'HUMAN_API'::text])))"
NAME = "financial_assumption_revision_channel_check"
IDEM = "price-entry-" + "a1" * 16


def entry_client(site) -> TestClient:
    with site.runner.engine.connect() as c:
        zone = c.execute(text("SELECT timezone FROM site WHERE id = :s"), {"s": site.site}).scalar_one()
    app = FastAPI()
    app.include_router(build_financial_assumption_router(
        lambda code: ("KOBO-001", site.tenant, site.site) if code == "KOBO-001" else None,
        entry_principal=lambda r, c: ENTRY_PRINCIPAL, store=site.prices, site_zone=lambda t, s: ZoneInfo(zone),
        read_access=lambda r, c: None))
    return TestClient(app)


def correction(**over) -> dict:
    body = {"key": KEY, "value": "2.00", "currency": "USD", "basis": "RECORDED_PURCHASE",
            "source": "Receipt KOBO-R-1001", "applies_from": "2026-10-01",
            "reason": "The October deliveries were billed at 2.00", "idempotency_key": IDEM}
    body.update(over)
    return body


def window_price(site, recorded_at):
    rev = site.on(POWER_DAY)
    f = site.store.load_input(site.tenant, site.site, rev["finding_id"], rev["id"])
    snap = site.prices.snapshot(site.tenant, site.site, KEY, recorded_at, 0, 100)
    return fc.select_window_price(snap["timeline"], snap["cited"], f.window_start, f.window_end)


def test_0060_widens_the_channel_check_and_downgrades_cleanly(engine) -> None:  # noqa: F811
    from alembic import command
    from alembic.script import ScriptDirectory

    config = _alembic()
    script = ScriptDirectory.from_config(config)
    assert script.get_heads() == [THIS] and script.get_revision(THIS).down_revision == PREVIOUS
    assert head(engine) == THIS and constraint(engine, NAME) == CHECK_0060
    engine.dispose()
    try:
        command.downgrade(config, PREVIOUS)  # no site-admin row: the 0010 CHECK text is restored exactly
        assert head(engine) == PREVIOUS and constraint(engine, NAME) == CHECK_0010
    finally:
        command.upgrade(config, "head")
    assert head(engine) == THIS and constraint(engine, NAME) == CHECK_0060


def test_a_saved_price_reaches_the_fuel_cost_after_one_drain(site, engine) -> None:  # noqa: F811
    rig = Rig(site)
    site.publish("v1")  # 1.25 USD from 2026-01-01, open-ended (SYSTEM_FIXTURE)
    rig.run()
    before = rig.read()["consequence"]
    assert (before["state"], Decimal(before["amount"]["high"])) == ("PRICED", Decimal("3.4375"))  # 2.75 L x 1.25
    with engine.connect() as c:
        known_before = c.execute(text("SELECT clock_timestamp()")).scalar_one()
    client = entry_client(site)

    # The dry run names the CORRECTION and writes nothing.
    dry = client.post("/api/sites/KOBO-001/financial-assumptions/entries", json=correction(dry_run=True, reason=None))
    assert dry.status_code == 200 and dry.json()["change_kind"] == "CORRECTION" and dry.json()["reason_required"]
    assert len(site.prices.revisions(site.tenant, site.site, KEY)) == 1

    saved = client.post("/api/sites/KOBO-001/financial-assumptions/entries", json=correction())
    assert saved.status_code == 201, saved.text
    body = saved.json()
    assert (body["change_kind"], body["revision_no"], body["replayed"], body["set_by"]) == (
        "CORRECTION", 2, False, "Entered by site admin")
    print("PR-3 save:", body)

    # The stored row: the entry service, a SYSTEM actor, no author, the new channel, the server provenance.
    with engine.connect() as c:
        row = c.execute(text(
            "SELECT channel, actor_kind, actor_id, author_id, correction_reason, provenance, value, basis, "
            "source_reference FROM financial_assumption_revision WHERE id = :i"), {"i": UUID(body["revision_id"])}).one()
        events = c.execute(text(
            "SELECT subject FROM event_outbox WHERE type = 'price.revised' AND site_id = :s AND recorded_at > :k"),
            {"s": site.site, "k": known_before}).scalars().all()
    assert (row.channel, row.actor_kind, row.actor_id, row.author_id) == (
        "SITE_ADMIN_ENTRY", "SYSTEM", "service:operator-entry", None)
    assert row.correction_reason == "The October deliveries were billed at 2.00"
    assert row.provenance == {"service": "operator-entry", "job": "site-admin-price-entry", "rule": "price-entry/1"}
    assert (row.value, row.basis, row.source_reference) == (Decimal("2.00"), "RECORDED_PURCHASE", "Receipt KOBO-R-1001")
    assert [e["key"] for e in events] == [KEY]

    # A replay with the same key and body is 200 and writes nothing new.
    again = client.post("/api/sites/KOBO-001/financial-assumptions/entries", json=correction())
    assert (again.status_code, again.json()["replayed"], again.json()["revision_id"]) == (200, True, body["revision_id"])
    assert len(site.prices.revisions(site.tenant, site.site, KEY)) == 2

    # The CORRECTION queued consequence work: the fuel cost reads as updating until the worker drains it.
    stale = rig.read()
    assert stale["currentness"]["state"] == "STALE" and stale["currentness"]["pending_work"]
    assert stale["consequence"]["presented_as_current"] is False
    outcomes = rig.run()
    assert outcomes and all(o.succeeded for o in outcomes)
    after = rig.read()["consequence"]
    assert (after["state"], after["presented_as_current"], after["price"]["revision_id"]) == (
        "PRICED", True, body["revision_id"])
    assert Decimal(after["amount"]["high"]) == Decimal("5.50")  # 2.75 L x 2.00
    pinned = rig.read(consequence_revision_id=UUID(before["id"]))["consequence"]
    assert Decimal(pinned["amount"]["high"]) == Decimal("3.4375") and pinned["historical"] is True
    print("PR-3 fuel cost: before", before["amount"]["high"], "after", after["amount"]["high"])

    # As known before the save, the window still selects the old price; now it selects the saved one.
    old, new = window_price(site, known_before), window_price(site, None)
    assert (old.value, new.value) == (Decimal("1.25"), Decimal("2.00"))
    print("PR-3 window price: as known before", old.value, "current", new.value)

    # L1: another save on the same key follows; a retry of the first save (lost response) still replays, not 409.
    later = client.post("/api/sites/KOBO-001/financial-assumptions/entries", json={
        "key": KEY, "value": "2.10", "currency": "USD", "basis": "RECORDED_PURCHASE", "source": "Receipt KOBO-R-1002",
        "applies_from": "2026-11-20", "idempotency_key": "price-entry-" + "b2" * 16})
    assert later.status_code == 201 and later.json()["change_kind"] == "SUCCESSION", later.text
    retry = client.post("/api/sites/KOBO-001/financial-assumptions/entries", json=correction())
    assert (retry.status_code, retry.json()["replayed"], retry.json()["revision_id"]) == (
        200, True, body["revision_id"]), retry.text
    assert len(site.prices.revisions(site.tenant, site.site, KEY)) == 3

    # With a site-admin row the downgrade refuses and changes nothing.
    from alembic import command

    site.prices.dispose()
    site.store.dispose()
    engine.dispose()
    with pytest.raises(DBAPIError, match=REFUSED):
        command.downgrade(_alembic(), PREVIOUS)
    assert head(engine) == THIS and constraint(engine, NAME) == CHECK_0060


def test_a_saved_price_moves_the_response_watermark_and_the_fresh_read_shows_it(site, engine) -> None:  # noqa: F811
    from assetops_backend.chain.adapters.postgres_response_store import PostgresResponseRows
    from assetops_backend.financial_read_api import build_financial_read_router
    from assetops_backend.financials.assumption_read import AssumptionReadService

    site.publish("v1")
    rows = PostgresResponseRows(engine=engine)
    old_mark = rows.read(lambda r: r.watermark(site.tenant, [site.site]))
    old_estate = rows.read(lambda r: r.watermark(site.tenant, None))
    rows.insert(site.tenant, old_mark, "pr3-test", 1, None, [("financials", "k", "etag-old", b'{"old": true}')])
    assert rows.read(lambda r: r.lookup("financials", "k", old_mark, "pr3-test", datetime.now(timezone.utc))) is not None

    client = entry_client(site)
    saved = client.post("/api/sites/KOBO-001/financial-assumptions/entries", json=correction(
        applies_from="2026-11-20", reason=None, value="2.00"))
    assert saved.status_code == 201, saved.text

    new_mark = rows.read(lambda r: r.watermark(site.tenant, [site.site]))
    assert new_mark != old_mark and rows.read(lambda r: r.watermark(site.tenant, None)) != old_estate
    # The body stored under the old watermark is not served: the lookup under the new one finds nothing.
    assert rows.read(lambda r: r.lookup("financials", "k", new_mark, "pr3-test", datetime.now(timezone.utc))) is None

    read_app = FastAPI()
    read_app.include_router(build_financial_read_router(
        AssumptionReadService(site.prices), lambda code: ("KOBO-001", site.tenant, site.site) if code == "KOBO-001"
        else None, access=lambda r, c: None))
    fresh = TestClient(read_app).get("/api/sites/KOBO-001/financial-assumptions", params={"key": KEY})
    assert fresh.status_code == 200 and saved.json()["revision_id"] in [r["revision_id"] for r in fresh.json()["revisions"]]


def test_a_productive_use_first_price_prices_the_mill_value_and_drops_its_price_action(mill) -> None:  # noqa: F811
    from assetops_backend.actions import verification_families as vf
    from assetops_backend.financials.adapters.postgres_assumption_store import PostgresAssumptionStore

    svc, clock, aid, eff, tz = _frozen(mill, "pr3-mill", baseline_kwh="42")
    prices = PostgresAssumptionStore(URL)
    mill.disposables.append(prices)
    try:
        _with_productive_price(svc, mill)
        _later(mill, eff, "110")
        clock.at = _after(eff, tz, 5)
        port = svc.actions.verification_ports.productive_price
        start = datetime.combine(eff - timedelta(days=3), datetime.min.time(), ZoneInfo(tz)).astimezone(timezone.utc)
        end = start + timedelta(days=7)
        details = {"baseline": {"mean_kwh_per_day": "42", "days": [1, 2, 3]},
                   "later": {"mean_kwh_per_day": "110", "days": [1, 2, 3]}}

        # Before any price: the value reads UNPRICED and carries the set-price action.
        before = vf.mill_value(details, vf.VERIFIED, port(mill.t, mill.s, start, end, clock.at), "MILL-1")
        assert before["state"] == "UNPRICED" and before["price_action"]["kind"] == "SET_PRICE", before

        app = FastAPI()
        app.include_router(build_financial_assumption_router(
            lambda code: ("MILL-1", mill.t, mill.s) if code == "MILL-1" else None,
            entry_principal=lambda r, c: ENTRY_PRINCIPAL, store=prices, read_access=lambda r, c: None,
            site_zone=lambda t, s: ZoneInfo(tz)))
        saved = TestClient(app).post("/api/sites/MILL-1/financial-assumptions/entries", json={
            "key": "productive_use_price_per_kwh", "value": "0.25", "currency": "USD", "basis": "CONTRACT_RATE",
            "source": "Mill customer price list", "applies_from": "2026-01-01", "idempotency_key": IDEM})
        assert saved.status_code == 201 and saved.json()["change_kind"] == "INITIAL", saved.text

        assert svc.evaluate_domain_plan(mill.t, mill.s, aid)["state"] == "VERIFIED"
        value = svc.domain_summary(mill.t, mill.s, aid)["value"]
        assert value["state"] == "PRICED" and value["per_day"] == "17.00", value
        assert value["price"]["revision_id"] == saved.json()["revision_id"] and "price_action" not in value
    finally:
        _close(mill)
