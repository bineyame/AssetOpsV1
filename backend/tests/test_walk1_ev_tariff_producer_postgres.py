"""WALK1-2 §3.1/§3.4: the Depot producer publishes the demo charging tariff once; a second call is a replay.

The step is `tools/demo_combined_ev.py` `publish_tariff` (the `demo_combined_kobo.publish_price` pattern) over the
`backend/conversions/demo-ev-tariff-publications.json` fixture, recorded at `ev.install_at` + 30 min. Needs
`ASSETOPS_TEST_DATABASE_URL` naming a `*_test` database; skipped (never passed) without it.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

if URL:
    from assetops_backend.financials.adapters.postgres_assumption_store import PostgresAssumptionStore
    from assetops_backend.sites.ev_lab import install_ev_lab
    from test_s1_bindings_postgres import Clock, engine, store  # noqa: F401
    import demo_combined_ev as producer  # noqa: E402
    import pg_harness

INSTALL_AT = datetime(2026, 10, 3, 6, 0, tzinfo=timezone.utc)


def test_fixture_is_the_declared_demo_tariff() -> None:
    doc = json.loads(producer.FIXTURE_TARIFF.read_text(encoding="utf-8"))
    assert doc["assumption_key"] == "ev_gross_tariff_per_kwh"
    (step,) = doc["steps"]
    assert (step["step"], step["change_kind"], step["currency"], step["value"], step["basis"],
            step["valid_from"], step["valid_to"], step["idempotency_key"]) == (
        "v1", "INITIAL", "USD", "0.30", "AUTHORED_ESTIMATE", "2026-01-01T00:00:00Z", None, "demo-ev-tariff-v1")
    assert step["source_reference"] == (
        "Demonstration charging tariff set by the system (illustrative, not a contract rate)")


def test_tariff_publication_runs_once_and_replays(store) -> None:  # noqa: F811
    result = install_ev_lab(store, tenant_slug="demo", clock=Clock(INSTALL_AT))
    recorded = INSTALL_AT + producer.TARIFF_AFTER_INSTALL
    first = producer.publish_tariff(URL, recorded)
    again = producer.publish_tariff(URL, recorded + timedelta(hours=5))
    assert (first["site_code"], first["step"], first["change_kind"], first["replayed"]) == (
        "EV-LAB-001", "v1", "INITIAL", False)
    assert again["replayed"] is True and again["revision_id"] == first["revision_id"]

    assumptions = PostgresAssumptionStore(URL)
    try:
        rows = assumptions.revisions(result.tenant.id, result.site.id, "ev_gross_tariff_per_kwh")
    finally:
        pg_harness.dispose(assumptions)
    assert len(rows) == 1
    (row,) = rows
    assert (str(row["id"]), row["currency"], Decimal(row["value"])) == (first["revision_id"], "USD", Decimal("0.30"))
    assert row["recorded_at"] == recorded  # the configuration knowledge instant, not build time
