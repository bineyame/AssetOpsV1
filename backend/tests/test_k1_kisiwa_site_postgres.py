"""DIESEL-1 K1 (ruling DIESEL-1-R3c §9c.1) L2: the registered Kisiwa Site on Postgres, and one Kisiwa day end to end.

Needs `ASSETOPS_TEST_DATABASE_URL` naming a `*_test` database (K1: `assetops_k1_test`); skipped without it.

`tools/demo_combined_kisiwa.py` `register` (import 2026-09-29T09:00Z, install 09:30Z), then F0r run 1
(2026-10-01T12:00Z to 2026-10-02T12:00Z, D0's day document, no actions) drafted on the registered basis (product
mini-grid v7, registered-kobo-publication v5), published by a real gateway, accepted by S2 at 2026-10-02T12:10Z,
assessed (S3) and matched (S4) 5 minutes later. The Site outcome board is read through the app.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID

import pytest

import pg_harness

REPO = Path(__file__).resolve().parents[2]
for extra in (REPO / "tools", REPO / "host", REPO / "host" / "tests", REPO / "gateway" / "tests"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)"
)

IMPORT_AT = datetime(2026, 9, 29, 9, 0, tzinfo=timezone.utc)
INSTALL_AT = datetime(2026, 9, 29, 9, 30, tzinfo=timezone.utc)
RUN_START, RUN_END = "2026-10-01T12:00:00Z", "2026-10-02T12:00:00Z"
RECEIVED_AT = datetime(2026, 10, 2, 12, 10, tzinfo=timezone.utc)
SETUP_AT = "2026-09-29T11:00:00Z"


@pytest.fixture(scope="module")
def registered(tmp_path_factory):
    from sqlalchemy.engine import make_url

    import demo_combined_kisiwa as kis

    url = make_url(URL)
    assert url.database and url.database.endswith("_test"), "Refusing a database not named *_test"
    pg_harness.fresh_database()
    work = tmp_path_factory.mktemp("kisiwa-register")
    result = kis.register(URL, work, IMPORT_AT, INSTALL_AT)
    assert json.loads((work / "kisiwa-register.json").read_text(encoding="utf-8"))["site_code"] == "KISIWA-001"
    return result


def test_the_registered_foundation_facts(registered) -> None:
    from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore
    from test_k1_kisiwa_fixtures import assert_registered_facts, facts

    store = PostgresFoundationStore(URL)
    try:
        found = facts(store, registered["tenant_id"], registered["site_id"], datetime(2026, 10, 1, 12, 0,
                      tzinfo=timezone.utc), INSTALL_AT + timedelta(minutes=30))
    finally:
        pg_harness.dispose(store)
    assert_registered_facts(found)


def test_diesel_price_v1_is_known_at_install_plus_one_hour(registered) -> None:
    from assetops_backend.financials import fuel_cost
    from assetops_backend.financials.adapters.postgres_assumption_store import PostgresAssumptionStore

    store = PostgresAssumptionStore(URL)
    try:
        _, tenant_id, site_id = store.site_scope("demo", "KISIWA-001")
        start, end = datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc), datetime(2026, 10, 2, 12, 0,
                                                                                 tzinfo=timezone.utc)
        before = store.snapshot(tenant_id, site_id, fuel_cost.PRICE_KEY,
                                INSTALL_AT + timedelta(minutes=59), 0, 1)
        known = store.snapshot(tenant_id, site_id, fuel_cost.PRICE_KEY, INSTALL_AT + timedelta(hours=1), 0, 1)
        unpriced = fuel_cost.select_window_price(before["timeline"], before["cited"], start, end)
        priced = fuel_cost.select_window_price(known["timeline"], known["cited"], start, end)
    finally:
        pg_harness.dispose(store)
    print("K1 price", unpriced.state, unpriced.reason, "->", priced.state, priced.value, priced.currency)
    assert unpriced.state == "UNPRICED"
    assert (priced.state, str(priced.value), priced.currency) == ("PRICED", "1.25", "USD")


def test_one_kisiwa_day_end_to_end(registered, tmp_path, monkeypatch) -> None:
    from sqlalchemy import create_engine, text

    import probe_kisiwa_fuel as probe
    import probe_kisiwa_nights as nights
    import test_s6_verification_replay as rp
    from kisiwa import draft_day
    from assetops_backend.outcomes.status import STATE_LABEL
    from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore

    store = PostgresFoundationStore(URL)
    engine = create_engine(URL)
    site_id, tenant_id = UUID(registered["site_id"]), UUID(registered["tenant_id"])
    try:
        run = draft_day(store, nights.day_document(probe.START_SOC, probe.START_FUEL), RUN_START, RUN_END, SETUP_AT)
        assert run.execution_status == "READY", [(r.kind, r.subject) for r in run.blocking_reasons]
        assert run.registered_basis is not None
        published = rp._publish_and_accept(tmp_path, run, "epoch-1", RECEIVED_AT)
        print("K1 published", published)
        result = SimpleNamespace(tenant=SimpleNamespace(id=tenant_id), site=SimpleNamespace(id=site_id))
        runner = rp.LabRunner(store, engine, result, RECEIVED_AT + timedelta(minutes=5))
        runner.step({"do": "assess"})
        runner.step({"do": "match"})
        with engine.connect() as c:
            fuel = c.execute(text("SELECT count(*), min(source_time), max(source_time) FROM accepted_evidence "
                                  "WHERE site_id = :s AND role = 'fuel_level'"), {"s": site_id}).one()
            assessed = [tuple(r) for r in c.execute(text(
                "SELECT analytic_id, claim_level, count(*) FROM assessment_revision WHERE site_id = :s "
                "AND window_start < :e AND window_end > :b GROUP BY analytic_id, claim_level ORDER BY 1, 2"),
                {"s": site_id, "b": rp._at(RUN_START), "e": rp._at(RUN_END)})]
    finally:
        engine.dispose()
        pg_harness.dispose(store)
    print("K1 fuel_level accepted", tuple(fuel))
    print("K1 assessments", assessed)
    assert fuel[0] > 0
    assert assessed and any("dispatch" in str(a[0]) for a in assessed), assessed

    from fastapi.testclient import TestClient

    from assetops_backend.config import load_feature_flags
    from assetops_backend.estate.scope import PORTFOLIO_CURSOR_KEY_ENV
    from assetops_backend.evidence.adapters import json_evidence_store, legacy_comparison_file
    from assetops_backend.main import create_app

    monkeypatch.setenv("DATABASE_URL", URL)
    monkeypatch.setenv(PORTFOLIO_CURSOR_KEY_ENV, "0" * 64)
    monkeypatch.setattr(json_evidence_store, "EVIDENCE_STORE_ROOT", tmp_path / "evidence")
    monkeypatch.setattr(legacy_comparison_file, "EVIDENCE_STORE_ROOT", tmp_path / "evidence")
    with TestClient(create_app(load_feature_flags())) as client:
        response = client.get("/api/sites/KISIWA-001/outcome-board", params={"date": "2026-10-01"})
    print("K1 board status", response.status_code)
    assert response.status_code == 200, response.text
    body = response.json()
    print("K1 board read_state", body.get("read_state"))
    for row in body["rows"]:
        print("K1 board row", json.dumps(row, sort_keys=True, default=str))
        assert row["state"] in STATE_LABEL, row["state"]
        for outcome in row.get("outcomes") or ():
            assert outcome["state"] in STATE_LABEL, outcome
    served = json.dumps(body).lower()
    for word in ("theft", "stolen", "siphon", "pilfer"):
        assert word not in served
