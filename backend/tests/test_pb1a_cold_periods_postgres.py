"""PB-1a (D-E5.31): Cold analysed periods inside a requested window, default Site selection only.

Rule (`.agent/architect-answer-non-kobo-sites-2026-11-10.md` D-E5.31): (i) a stored selection that contains or
equals the window is unchanged; (ii) otherwise the selected analysed periods lying wholly inside the window are
listed and the snapshot reads the most recent one with an open (SUPPORTED) Finding, or else the most recent one;
(iii) none inside is today's empty selection. Pinned mode is unchanged.

Over the registered W2-02 `excursion` replay and the real cold worker. The extra periods of the week case are
further `analytic_run_selection` rows (append-only, inserted only) re-selecting the same stored runs on later days,
so they carry no Finding of their own. Needs ASSETOPS_TEST_DATABASE_URL.
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

    from assetops_backend.analytics.adapters.postgres_assessment_store import ColdReadService

CODE = "COLD-READ"
DAY = datetime(2026, 10, 6, tzinfo=timezone.utc)
WEEK = (datetime(2026, 10, 5, tzinfo=timezone.utc), datetime(2026, 10, 12, tzinfo=timezone.utc))


@contextmanager
def snapshot(built):
    with built.engine.connect().execution_options(isolation_level="REPEATABLE READ") as c:
        with c.begin():
            yield c


def watermark(built) -> datetime:
    with built.engine.connect() as c:
        return c.execute(text("SELECT max(decided_at) FROM ingestion_disposition WHERE site_id = :s"),
                         {"s": built.site_id}).scalar_one()


def now(built) -> datetime:
    with built.engine.connect() as c:
        return c.execute(text("SELECT clock_timestamp()")).scalar_one()


def period(built) -> tuple[datetime, datetime]:
    """The one stored selected cold window of the replay (both analytics share it)."""
    with built.engine.connect() as c:
        rows = c.execute(text("SELECT DISTINCT window_start, window_end FROM analytic_run_selection "
                              "WHERE site_id = :s"), {"s": built.site_id}).all()
    assert len(rows) == 1, rows
    return rows[0][0], rows[0][1]


def reselect_later_days(built, days: tuple[int, ...]) -> list[tuple[datetime, datetime]]:
    """Insert selections of the same stored runs shifted by whole days: further analysed periods, no Finding."""
    with built.engine.begin() as c:
        heads = c.execute(text(
            "SELECT DISTINCT ON (analytic_id) tenant_id, site_id, analytic_id, window_start, window_end, run_id "
            "FROM analytic_run_selection WHERE site_id = :s ORDER BY analytic_id, seq DESC"), {"s": built.site_id}).all()
        for d in days:
            for h in heads:
                c.execute(text(
                    "INSERT INTO analytic_run_selection (tenant_id, site_id, analytic_id, window_start, window_end, "
                    "run_id, job_id, selected_at) VALUES (:t, :s, :a, :lo, :hi, :r, NULL, clock_timestamp())"),
                    {"t": h[0], "s": h[1], "a": h[2], "lo": h[3] + timedelta(days=d), "hi": h[4] + timedelta(days=d),
                     "r": h[5]})
    lo, hi = heads[0][3], heads[0][4]
    return [(lo + timedelta(days=d), hi + timedelta(days=d)) for d in days]


def open_finding_anchors(built) -> list[datetime]:
    with built.engine.connect() as c:
        return [r[0] for r in c.execute(text(
            "SELECT f.anchor_start FROM finding f WHERE f.site_id = :s AND f.domain = 'cold_chain' AND "
            "(SELECT r.lifecycle FROM finding_revision r WHERE r.finding_id = f.id ORDER BY r.revision_no DESC "
            "LIMIT 1) = 'SUPPORTED'"), {"s": built.site_id}).all()]


def revision_ids(snap: dict) -> dict:
    return {a: str(x.revision_id) for a, x in snap["selected"].items()}


def test_day_window_over_one_period(chain) -> None:  # noqa: F811
    built = opened("excursion", chain)
    run(built)
    lo, hi = period(built)
    wm = watermark(built)
    svc = ColdReadService(engine=built.engine)
    t, s = built.tenant_id, built.site_id
    with snapshot(built) as c:
        day = svc._snapshot(c, t, s, CODE, DAY, DAY + timedelta(days=1), wm)
        exact = svc._snapshot(c, t, s, CODE, lo, hi, wm)
    assert DAY <= lo and hi <= DAY + timedelta(days=1)
    assert day["analysed_periods"] == [(lo, hi)] and day["shown_period"] == (lo, hi)
    assert (day["lo"], day["hi"]) == (lo, hi)  # the status bar and Needs attention read the analysed period
    assert day["selected"] and revision_ids(day) == revision_ids(exact)
    assert day["state"] == exact["state"]
    # (i) a stored selection equal to the window is unchanged: nothing is substituted or listed.
    assert exact["analysed_periods"] == [] and exact["shown_period"] is None
    assert (exact["lo"], exact["hi"]) == (lo, hi)


def test_week_over_four_periods_open_finding_wins(chain) -> None:  # noqa: F811
    built = opened("excursion", chain)
    run(built)
    failure = period(built)
    anchors = open_finding_anchors(built)
    assert anchors and all(failure[0] <= a < failure[1] for a in anchors), anchors  # only the failure day
    later = reselect_later_days(built, (1, 2, 3))
    wm = watermark(built)
    svc = ColdReadService(engine=built.engine)
    t, s = built.tenant_id, built.site_id
    with snapshot(built) as c:
        week = svc._snapshot(c, t, s, CODE, *WEEK, wm)
        quiet = svc._snapshot(c, t, s, CODE, later[0][0] - timedelta(hours=1), WEEK[1], wm)
    assert week["analysed_periods"] == [failure, *later]
    assert week["shown_period"] == failure and (week["lo"], week["hi"]) == failure  # the open Finding wins
    assert week["selected"]
    # With no open Finding among the periods inside, the most recent one is shown.
    assert quiet["analysed_periods"] == later and quiet["shown_period"] == later[-1]
    assert (quiet["lo"], quiet["hi"]) == later[-1] and quiet["selected"]


def test_window_with_no_period_inside(chain) -> None:  # noqa: F811
    built = opened("excursion", chain)
    run(built)
    lo, hi = period(built)
    wm = watermark(built)
    svc = ColdReadService(engine=built.engine)
    t, s = built.tenant_id, built.site_id
    empty = (datetime(2026, 10, 20, tzinfo=timezone.utc), datetime(2026, 10, 27, tzinfo=timezone.utc))
    straddle = (lo + timedelta(minutes=5), hi + timedelta(hours=1))  # overlaps the period but does not hold it
    with snapshot(built) as c:
        none = svc._snapshot(c, t, s, CODE, *empty, wm)
        partial = svc._snapshot(c, t, s, CODE, *straddle, wm)
    for snap, window in ((none, empty), (partial, straddle)):
        assert snap["analysed_periods"] == [] and snap["shown_period"] is None
        assert snap["selected"] == {} and (snap["lo"], snap["hi"]) == window


def test_pinned_mode_unchanged(chain) -> None:  # noqa: F811
    built = opened("excursion", chain)
    run(built)
    failure = period(built)
    later = reselect_later_days(built, (1, 2, 3))
    wm, k = watermark(built), now(built)
    svc = ColdReadService(engine=built.engine)
    t, s = built.tenant_id, built.site_id
    with snapshot(built) as c:
        pinned = svc.estate_snapshots_on(c, t, s, CODE, *WEEK, wm, k)
    assert [(p["lo"], p["hi"]) for p in pinned] == [failure, *later]  # one exact snapshot per stored window
    for p in pinned:
        assert p["selected"] and p["selection_seqs"]
        assert p["analysed_periods"] == [] and p["shown_period"] is None
