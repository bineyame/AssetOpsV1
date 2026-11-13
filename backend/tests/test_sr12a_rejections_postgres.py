"""SR-12a (rev 10b.4): the imported Site's rejections over the date range, against real PostgreSQL.

Accepted, duplicate and rejected readings received at the S2 receipt, and a conflict received two days later. Each list in the body keeps the batches received in `[from, to)`; no range is
the whole history, as before.
"""

from __future__ import annotations

import os
from datetime import timedelta

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)"
)

if URL:
    from sqlalchemy import text
    from test_s1_bindings_postgres import engine, store  # noqa: F401
    from test_s1_bindings_postgres import Clock
    from test_s2_evidence_ledger_postgres import RECEIVED, submit
    from test_s2_site_evidence_postgres import client, empty_set_report, kit  # noqa: F401

    from assetops_backend.evidence.adapters.postgres_evidence_ledger import PostgresEvidenceLedger
    from assetops_backend.evidence.ledger_service import BatchIngestionService


def _instant(at) -> str:
    return at.strftime("%Y-%m-%dT%H:%M:%SZ")


def _range(lo, hi) -> str:
    return f"from={_instant(lo)}&to={_instant(hi)}"


def test_each_list_keeps_the_batches_received_in_the_range(kit, engine) -> None:  # noqa: F811
    pv = "pv-inverter-controller"
    submit(kit, kit.seal(kit.pv(3)))
    submit(kit, kit.seal([kit.pv(1)[0], kit.envelope(pv, 4, 3, "1.5")]))  # one duplicate
    submit(kit, kit.seal([kit.envelope(pv, 6, 31, "2", signal_id="unbound-signal")]))  # one rejected
    # The conflict arrives two days later (its batch receipt), a whole second so `to=later` is exact.
    later = (RECEIVED + timedelta(days=2)).replace(microsecond=0)
    conflict = BatchIngestionService(PostgresEvidenceLedger(URL, test_decision_clock_override=Clock(later)),
                                     Clock(later)).submit(kit.principal,
                                                          kit.seal([kit.envelope(pv, 2, 1, "7")]).encode()).receipt
    receipts = {"conflict": conflict}
    http = client(kit, empty_set_report(kit))
    whole = http.get("/api/sites/KOBO-001/evidence/rejections").json()
    assert len(whole["conflicts"]) == 1 and len(whole["duplicates"]) == 1 and whole["total"] == 2

    day = RECEIVED.replace(hour=0, minute=0, second=0, microsecond=0)
    first = http.get(f"/api/sites/KOBO-001/evidence/rejections?{_range(day, day + timedelta(days=1))}")
    assert first.status_code == 200
    first_body = first.json()
    assert first_body["conflicts"] == []
    assert len(first_body["duplicates"]) == 1
    assert first_body["total"] == whole["total"] - 1
    assert {r["batch_id"] for r in first_body["rejections"]} == {
        r["batch_id"] for r in whole["rejections"]} - {receipts["conflict"].batch_id}

    moved = http.get(f"/api/sites/KOBO-001/evidence/rejections?{_range(later - timedelta(hours=1), later + timedelta(hours=1))}")
    moved_body = moved.json()
    assert [r["batch_id"] for r in moved_body["rejections"]] == [receipts["conflict"].batch_id]
    assert len(moved_body["conflicts"]) == 1 and moved_body["duplicates"] == []

    # `to` is excluded: a range ending at the moved batch's receipt does not hold it.
    edge = http.get(f"/api/sites/KOBO-001/evidence/rejections?{_range(later - timedelta(hours=1), later)}").json()
    assert edge["total"] == 0 and edge["conflicts"] == [] and edge["duplicates"] == []

    assert http.get(f"/api/sites/KOBO-001/evidence/rejections?from={_instant(day)}").status_code == 422
