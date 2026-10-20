"""W3-01 Run 6 Blocker 1 (and W4-01 Run 3 ruling 6): the pinned, connection-taking EV selection mode.

Over the registered W2-05b `complete` replay and the production EV worker (the W2-06 read fixture),
`selected_windows_on`/`EvReadService.estate_snapshots_on` enumerate the exact stored selected session windows
intersecting a whole UTC day as of a cutoff and pin each window's selected seq through the single `_snapshot`
implementation, on ONE caller-owned REPEATABLE READ connection. Needs ASSETOPS_TEST_DATABASE_URL.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

import pytest

from test_w205b_ev_replay_postgres import URL, chain  # noqa: F401 - the W2-05b replay fixture

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from test_w206_ev_store_postgres import LATE_HI, LATE_LO, run_worker, select_exact

    from assetops_backend.analytics.adapters.postgres_assessment_store import (
        EvReadRefused,
        EvReadService,
        SelectionPinRefused,
        selected_windows_on,
    )
    from assetops_backend.evidence.composition import build_link_rows_reader

CODE = "EV-LAB-001"
EV = "ev-session/1"  # ev.SESSION_ANALYTIC


@contextmanager
def snapshot(built):
    with built.engine.connect().execution_options(isolation_level="REPEATABLE READ") as c:
        with c.begin():
            yield c
            assert c.in_transaction(), "a helper ended the caller's transaction"


def scalar(built, sql: str):
    with built.engine.connect() as c:
        return c.execute(text(sql), {"s": built.site_id}).scalar_one()


def stored(built) -> list[dict]:
    with built.engine.connect() as c:
        return [dict(r._mapping) for r in c.execute(text(
            "SELECT window_start, window_end, seq, selected_at FROM analytic_run_selection WHERE site_id = :s "
            "AND analytic_id = :a ORDER BY seq"), {"s": built.site_id, "a": EV})]


def settled(chain, case: str = "complete"):  # noqa: F811
    built = chain(case)
    built.start_release_upload()
    run_worker(built)
    return built


def clocks(built) -> tuple[datetime, datetime]:
    """(the Site's committed evidence watermark, the database clock now)."""
    return (scalar(built, "SELECT max(decided_at) FROM ingestion_disposition WHERE site_id = :s"),
            scalar(built, "SELECT clock_timestamp()"))


def day_of(at: datetime) -> datetime:
    return datetime(at.year, at.month, at.day, tzinfo=timezone.utc)


def test_ev_day_intersection_selects_exact_windows(chain) -> None:  # noqa: F811
    built = settled(chain)
    rows = stored(built)
    wm, k = clocks(built)
    day = day_of(rows[0]["window_start"])
    latest = {}
    for r in rows:
        if r["window_start"] < day + timedelta(days=1) and r["window_end"] > day:
            latest[(r["window_start"], r["window_end"])] = r["seq"]
    svc, t, s = EvReadService(engine=built.engine, link_rows=build_link_rows_reader()), built.tenant_id, built.site_id
    with snapshot(built) as c:
        whole_day = svc._snapshot(c, t, s, CODE, day, day + timedelta(days=1), wm)  # the q6 Blocker 1 shape
        keys = selected_windows_on(c, t, s, (EV,), day, day + timedelta(days=1), k)
        # The selection cutoff may follow the watermark; `known_at` stays clamped to it, so no EV_TIME_INVALID.
        snaps = svc.estate_snapshots_on(c, t, s, CODE, day, day + timedelta(days=1), wm, k)
        sites = [svc._snapshot(c, t, s, CODE, x["lo"], x["hi"], wm) for x in snaps]
        with pytest.raises(EvReadRefused):  # the W2 validation is not reinterpreted: an unclamped known_at
            svc._snapshot(c, t, s, CODE, snaps[0]["lo"], snaps[0]["hi"], k, selection_cutoff=k,
                          selection_seqs=snaps[0]["selection_seqs"])
        outside = svc.estate_snapshots_on(c, t, s, CODE, day + timedelta(days=2), day + timedelta(days=3), wm, k)
    assert whole_day["selected"] is None  # the equality predicate discards every stored session window
    assert keys == [{"analytic_id": EV, "window_start": lo, "window_end": hi, "seq": seq}
                    for (lo, hi), seq in sorted(latest.items())]
    assert [((x["lo"], x["hi"]), x["selection_seqs"]) for x in snaps] == [(w, {EV: q}) for w, q in sorted(latest.items())]
    for snap, site in zip(snaps, sites):
        assert snap["selected"] is not None and snap["selected"]["revision_id"] == site["selected"]["revision_id"]
        assert snap["state"] == site["state"] and "selection_seqs" not in site
    assert outside == []


def test_ev_cutoff_precedes_reselection_and_multiwindow(chain) -> None:  # noqa: F811
    """`late-record`: the job's own window plus an exact DEFAULT selection of `[LATE_LO, LATE_HI)` (the W2-06
    shape) give two stored windows in one day; the late terminal then re-heads the exact window with a later seq."""
    built = settled(chain, "late-record")
    svc, t, s = EvReadService(engine=built.engine, link_rows=build_link_rows_reader()), built.tenant_id, built.site_id
    day = day_of(LATE_LO)
    wm0, k0 = clocks(built)
    with snapshot(built) as c:
        before = svc.estate_snapshots_on(c, t, s, CODE, day, day + timedelta(days=1), wm0, k0)
    # A selection written after k0 over the already-committed evidence: its run's knowledge cutoff is at or before
    # k0, so only `selected_at` keeps it out of a k0 read.
    select_exact(built, LATE_LO, LATE_HI)
    wm1, k1 = clocks(built)
    with snapshot(built) as c:
        first = svc.estate_snapshots_on(c, t, s, CODE, day, day + timedelta(days=1), wm1, k1)
        late_seq = next(x for x in first if (x["lo"], x["hi"]) == (LATE_LO, LATE_HI))["selection_seqs"]
        assert [x for x in svc.estate_snapshots_on(c, t, s, CODE, day, day + timedelta(days=1), wm1, k0)
                if (x["lo"], x["hi"]) == (LATE_LO, LATE_HI)] == []
        with pytest.raises(SelectionPinRefused):
            svc._snapshot(c, t, s, CODE, LATE_LO, LATE_HI, wm1, selection_cutoff=k0, selection_seqs=late_seq)
    assert wm1 == wm0 and (LATE_LO, LATE_HI) not in [(x["lo"], x["hi"]) for x in before]
    built.advance_late()
    run_worker(built)  # re-heads every intersecting exact selection
    wm2, k2 = clocks(built)
    with snapshot(built) as c:
        again = svc.estate_snapshots_on(c, t, s, CODE, day, day + timedelta(days=1), wm1, k1)
        later = svc.estate_snapshots_on(c, t, s, CODE, day, day + timedelta(days=1), wm2, k2)
        old = next(x for x in first if (x["lo"], x["hi"]) == (LATE_LO, LATE_HI))
        new = next(x for x in later if (x["lo"], x["hi"]) == (LATE_LO, LATE_HI))
        with pytest.raises(SelectionPinRefused):  # a seq selected after the cutoff is never pinned at it
            svc._snapshot(c, t, s, CODE, LATE_LO, LATE_HI, wm1, selection_cutoff=k1,
                          selection_seqs=new["selection_seqs"])
    windows = [(x["lo"], x["hi"]) for x in first]
    assert len(windows) >= 2 and windows == sorted(windows)
    assert all(x["selected"] is not None for x in first)
    pick = [(x["lo"], x["hi"], x["selection_seqs"], x["selected"]["revision_id"]) for x in first]
    assert [(x["lo"], x["hi"], x["selection_seqs"], x["selected"]["revision_id"]) for x in again] == pick
    assert new["selection_seqs"][EV] > old["selection_seqs"][EV]
    assert new["selected"]["revision_id"] != old["selected"]["revision_id"]
