"""SR-12a (rev 10b.4): the imported Site's rejections over the date range, against real PostgreSQL.

Accepted, duplicate and rejected readings received at the S2 receipt, and a conflict received two days later. Each list in the body keeps the readings whose SOURCE time is in `[from, to)` (D-SR.76 Q8); no range is
the whole history, as before.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta

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
    from assetops_backend.evidence.ledger_reads import CONFLICT_KINDS
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

    def ranged(lo, hi) -> dict:
        r = http.get(f"/api/sites/KOBO-001/evidence/rejections?{_range(lo, hi)}")
        assert r.status_code == 200
        return r.json()

    # Source time decides, not receipt: the conflict was received two days later but describes its own reading time.
    by_kind = {r["kind"]: r for r in whole["rejections"]}
    for row in whole["rejections"]:
        assert row["source_time"] is not None
        src = datetime.fromisoformat(row["source_time"].replace("Z", "+00:00"))
        one = timedelta(seconds=1)
        inside = ranged(src, src + one)  # source == from: in
        assert row["rejection_id"] in {r["rejection_id"] for r in inside["rejections"]}
        outside = ranged(src - one, src)  # source == to: out
        assert row["rejection_id"] not in {r["rejection_id"] for r in outside["rejections"]}
        # The overview count line agrees with the list at the same edge.
        counts = http.get(f"/api/sites/KOBO-001/evidence?from={_instant(src)}&to={_instant(src + one)}").json()["counts"]
        assert counts["rejected"] + counts["conflicts"] == inside["total"] == len(inside["rejections"])
        assert len(inside["conflicts"]) == len([r for r in inside["rejections"] if r["kind"] in CONFLICT_KINDS])
    assert by_kind  # the fixture produced rows

    # Receipt does not place a timed reading: a range around the conflict's receipt holds none of the readings.
    away = ranged(later - timedelta(hours=1), later + timedelta(hours=1))
    assert away["total"] == 0 and away["conflicts"] == [] and away["duplicates"] == []

    # Duplicates follow the first accepted reading's source time (start + 0 minutes here).
    hour = ranged(kit.start, kit.start + timedelta(hours=1))
    assert len(hour["duplicates"]) == len(whole["duplicates"]) == 1
    assert hour["total"] == whole["total"]

    assert http.get(f"/api/sites/KOBO-001/evidence/rejections?from={_instant(RECEIVED)}").status_code == 422
