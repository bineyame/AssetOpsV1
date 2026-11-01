"""POLISH PA-1 (OUT-E L3, build sheet Addendum 2 Q-A): `PostgresTrialComparisonStore.history()` orders one Action's
revisions by `recorded_at, revision_no, id`. `revision_no` is unique only within one verification outcome, so the
time leads; with a fixed demo clock two revisions of one outcome share `recorded_at`, and `revision_no` (not the
random uuid) decides their order.

The rows are direct SQL in the replica role (CHECKs apply; the FK and append-only triggers do not), as the CC-M
schema test does for its CHECK probes: the read's ORDER BY is what is pinned, not the write path.
Requires ASSETOPS_TEST_DATABASE_URL naming a `*_test` database.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest

from test_s4_finding_store_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    import pg_harness  # noqa: F401
    from sqlalchemy import text

    from test_s1_bindings_postgres import engine  # noqa: F401
    from test_w203_cold_migration_postgres import _replica

TABLE = "trial_cost_comparison_revision"
INSERT = (
    f"INSERT INTO {TABLE} (id, tenant_id, site_id, action_id, verification_outcome_id, revision_no, "
    "supersedes_revision_id, formula, state, reason, result, intervention_cost, price_revision_id, basis_sha256, "
    "actor_kind, actor_id, source_channel, authorization_basis, triggering_service, triggering_fixture, "
    "idempotency_key, payload_sha256, recorded_at) VALUES (:id, :t, :s, :a, :o, :no, :sup, "
    "'trial-fuel-comparison/1', 'UNAVAILABLE', 'OUTCOME_INCONCLUSIVE', CAST(:result AS jsonb), "
    "CAST(:cost AS jsonb), NULL, :basis, 'SYSTEM', 'service:polish-pa1', 'SYSTEM_DEMONSTRATION_API', "
    "'POLISH PA-1 history order probe', 'polish', 'polish-pa1', :key, :sha, :at)")
T0, T1, T2 = (datetime(2026, 10, 29, h, tzinfo=timezone.utc) for h in (8, 9, 10))


def _row(t: str, s: str, a: str, o: str, no: int, sup: str | None, at: datetime, rid: str) -> dict:
    return {"id": rid, "t": t, "s": s, "a": a, "o": o, "no": no, "sup": sup, "at": at,
            "result": json.dumps({"state": "UNAVAILABLE"}),
            "cost": json.dumps({"amount": "0", "currency": None, "source": "DEFAULT"}),
            "basis": uuid4().hex + uuid4().hex, "key": f"polish-{uuid4().hex[:12]}", "sha": "a" * 64}


def test_history_orders_by_time_then_revision_across_two_outcomes(engine) -> None:  # noqa: F811
    from assetops_backend.financials.adapters.postgres_trial_comparison_store import PostgresTrialComparisonStore

    t, s, a, o1, o2 = (str(uuid4()) for _ in range(5))
    # Outcome 1: both revisions at T1 (a fixed clock), ids chosen so uuid order is the reverse of revision order.
    o1r1 = _row(t, s, a, o1, 1, None, T1, "ffffffff-ffff-4fff-bfff-ffffffffffff")
    o1r2 = _row(t, s, a, o1, 2, o1r1["id"], T1, "00000000-0000-4000-8000-000000000001")
    # Outcome 2 interleaves: revision 1 before outcome 1, revision 2 after it.
    o2r1 = _row(t, s, a, o2, 1, None, T0, str(uuid4()))
    o2r2 = _row(t, s, a, o2, 2, o2r1["id"], T2, str(uuid4()))
    with engine.begin() as c:
        c.execute(text("SET LOCAL session_replication_role = replica"))
        for row in (o1r2, o2r2, o1r1, o2r1):  # inserted out of order on purpose
            c.execute(text(INSERT), row)
    try:
        got = PostgresTrialComparisonStore(URL).history(UUID(t), UUID(s), UUID(a))
        assert [(str(r["verification_outcome_id"]), r["revision_no"]) for r in got] == [
            (o2, 1), (o1, 1), (o1, 2), (o2, 2)]
        assert [str(r["id"]) for r in got] == [o2r1["id"], o1r1["id"], o1r2["id"], o2r2["id"]]
    finally:
        _replica(engine, f"DELETE FROM {TABLE} WHERE action_id = '{a}'")
