"""W3-01 Run 6 Blocker 1 (and W4-01 Run 3 ruling 6): the pinned, connection-taking cold selection mode.

Over the registered W2-02 `late-reading` replay (the W2-03 read fixture: authenticated Batch V2 intake and the real
cold worker), `selected_windows_on`/`ColdReadService.estate_snapshots_on` enumerate the exact stored selected
windows intersecting a whole UTC day as of a cutoff and pin each window's selected seqs through the single
`_snapshot` implementation, on ONE caller-owned REPEATABLE READ connection. Needs ASSETOPS_TEST_DATABASE_URL.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from test_w202_cold_replay_postgres import chain  # noqa: F401 - the W2-02 replay fixture
    from test_w203_cold_replay_postgres import opened, run

    from assetops_backend.analytics.adapters.postgres_assessment_store import (
        ColdReadService,
        SelectionPinRefused,
        selected_windows_on,
    )

CODE = "COLD-READ"
DAY = datetime(2026, 10, 6, tzinfo=timezone.utc)
ANALYTICS = ("cold-excursion", "cold-start-response")  # cold.EXCURSION_ANALYTIC, cold.START_RESPONSE_ANALYTIC


@contextmanager
def snapshot(built):
    with built.engine.connect().execution_options(isolation_level="REPEATABLE READ") as c:
        with c.begin():
            yield c
            assert c.in_transaction(), "a helper ended the caller's transaction"


def stored(built) -> list[dict]:
    with built.engine.connect() as c:
        return [dict(r._mapping) for r in c.execute(text(
            "SELECT sel.analytic_id, sel.window_start, sel.window_end, sel.seq, sel.selected_at, r.completed_at, "
            "r.knowledge_cutoff FROM analytic_run_selection sel JOIN analytic_run r ON r.id = sel.run_id "
            "WHERE sel.site_id = :s ORDER BY sel.seq"), {"s": built.site_id})]


def watermark(built) -> datetime:
    with built.engine.connect() as c:
        return c.execute(text("SELECT max(decided_at) FROM ingestion_disposition WHERE site_id = :s"),
                         {"s": built.site_id}).scalar_one()


def now(built) -> datetime:
    with built.engine.connect() as c:
        return c.execute(text("SELECT clock_timestamp()")).scalar_one()


def revision_ids(snap: dict) -> dict:
    return {a: str(x.revision_id) for a, x in snap["selected"].items()}


def test_cold_day_intersection_selects_exact_windows(chain) -> None:  # noqa: F811
    built = opened("late-reading", chain)
    run(built)
    rows, wm, k = stored(built), watermark(built), now(built)
    svc = ColdReadService(engine=built.engine)
    t, s = built.tenant_id, built.site_id
    with snapshot(built) as c:
        whole_day = svc._snapshot(c, t, s, CODE, DAY, DAY + timedelta(days=1), wm)  # the q6 Blocker 1 shape
        keys = selected_windows_on(c, t, s, ANALYTICS, DAY, DAY + timedelta(days=1), k)
        snaps = svc.estate_snapshots_on(c, t, s, CODE, DAY, DAY + timedelta(days=1), wm, k)
        (snap,) = snaps
        site = svc._snapshot(c, t, s, CODE, snap["lo"], snap["hi"], wm)  # the W2 Site read of that exact window
        outside = svc.estate_snapshots_on(c, t, s, CODE, DAY + timedelta(days=2), DAY + timedelta(days=3), wm, k)
        before_selection = selected_windows_on(c, t, s, ANALYTICS, DAY, DAY + timedelta(days=1), wm)
    assert whole_day["selected"] == {}  # the covering predicate discards the hour-scale selected window
    assert keys == [{"analytic_id": r["analytic_id"], "window_start": r["window_start"],
                     "window_end": r["window_end"], "seq": r["seq"]} for r in rows]
    assert (snap["lo"], snap["hi"]) == (rows[0]["window_start"], rows[0]["window_end"])
    assert snap["selection_seqs"] == {r["analytic_id"]: r["seq"] for r in rows}
    assert snap["selected"] and revision_ids(snap) == revision_ids(site)
    assert snap["state"] == site["state"] == "CURRENT" and "selection_seqs" not in site
    assert outside == []
    # The selection is recorded after the last decided evidence: at the watermark itself nothing is selected yet.
    assert all(r["selected_at"] > wm for r in rows) and before_selection == []


def test_cold_cutoff_precedes_reselection_and_revision(chain) -> None:  # noqa: F811
    built = opened("late-reading", chain)
    run(built)
    svc = ColdReadService(engine=built.engine)
    t, s = built.tenant_id, built.site_id
    wm1, k1 = watermark(built), now(built)
    with snapshot(built) as c:
        (first,) = svc.estate_snapshots_on(c, t, s, CODE, DAY, DAY + timedelta(days=1), wm1, k1)
    built.advance_late()
    run(built)  # a later selection of the same stored window, with new assessment revisions
    wm2, k2 = watermark(built), now(built)
    with snapshot(built) as c:
        (again,) = svc.estate_snapshots_on(c, t, s, CODE, DAY, DAY + timedelta(days=1), wm1, k1)
        (later,) = svc.estate_snapshots_on(c, t, s, CODE, DAY, DAY + timedelta(days=1), wm2, k2)
        assert (later["lo"], later["hi"]) == (first["lo"], first["hi"])
        with pytest.raises(SelectionPinRefused):  # a seq selected after the cutoff is never pinned at it
            svc._snapshot(c, t, s, CODE, first["lo"], first["hi"], wm1, selection_cutoff=k1,
                          selection_seqs=later["selection_seqs"])
    assert again["selection_seqs"] == first["selection_seqs"] and revision_ids(again) == revision_ids(first)
    assert all(later["selection_seqs"][a] > first["selection_seqs"][a] for a in first["selection_seqs"])
    assert set(revision_ids(later).values()).isdisjoint(revision_ids(first).values())
    assert again["state"] == "HISTORICAL" and later["state"] == "CURRENT"


def test_cold_reselection_of_an_old_run_is_invisible_earlier(chain) -> None:  # noqa: F811
    """A later selection row naming an already-completed run (its knowledge cutoff and completion are before k1)
    is excluded at k1 only by `selected_at`. TEST-SCOPED: the row is appended directly (the table is append-only;
    no current writer reselects an old run), the one shape Run 6 names that the replay cannot produce."""
    built = opened("late-reading", chain)
    run(built)
    svc = ColdReadService(engine=built.engine)
    t, s, wm = built.tenant_id, built.site_id, watermark(built)
    k1 = now(built)
    with built.engine.begin() as conn:
        conn.execute(text(
            "INSERT INTO analytic_run_selection (tenant_id, site_id, analytic_id, window_start, window_end, run_id, "
            "job_id, selected_at) SELECT tenant_id, site_id, analytic_id, window_start, window_end, run_id, NULL, "
            "clock_timestamp() FROM analytic_run_selection WHERE site_id = :s AND analytic_id = :a "
            "ORDER BY seq DESC LIMIT 1"), {"s": s, "a": ANALYTICS[0]})
    k2 = now(built)
    with snapshot(built) as c:
        (old,) = svc.estate_snapshots_on(c, t, s, CODE, DAY, DAY + timedelta(days=1), wm, k1)
        (new,) = svc.estate_snapshots_on(c, t, s, CODE, DAY, DAY + timedelta(days=1), wm, k2)
        with pytest.raises(SelectionPinRefused):
            svc._snapshot(c, t, s, CODE, old["lo"], old["hi"], wm, selection_cutoff=k1,
                          selection_seqs=new["selection_seqs"])
    assert new["selection_seqs"][ANALYTICS[0]] > old["selection_seqs"][ANALYTICS[0]]
    assert new["selection_seqs"][ANALYTICS[1]] == old["selection_seqs"][ANALYTICS[1]]
    assert revision_ids(new) == revision_ids(old)  # the same run: only the selection row differs
