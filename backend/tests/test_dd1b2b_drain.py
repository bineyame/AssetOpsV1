"""DD-1b2b O2 (DD1b2-R6, R7 Q1-Q4): the R8 drain. L0: the N formula and the stop logic. L2 (own `*_test` database, from
`ASSETOPS_TEST_DATABASE_URL`): the counts read real rows, and `Demo.drain` on a seeded backlog stops at 0, reports
`over_n` and fails on a flat count. O3: `--cap-seconds` is parsed."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

import demo_combined as dc  # noqa: E402
import demo_combined_drain as dr  # noqa: E402


def site(dirty=0, snap=0, threads=0, mini=0, opp=0, ids=()):
    return {"dirty": dirty, "snapshots_pending": snap, "threads_pending": threads, "mini_deferred": mini,
            "opportunity_live": opp, "pending_ids": list(ids)}


def test_n_is_the_maximum_over_sites_of_the_per_site_formula() -> None:
    assert dr.n_for({"A": site(dirty=0), "B": site(dirty=0)}) == 2
    assert dr.n_for({"A": site(dirty=200), "B": site(dirty=1, snap=1)}) == 3  # ceil(200/200)+2 vs ceil(2/200)+2
    assert dr.n_for({"A": site(dirty=250, snap=451), "B": site(dirty=900)}) == 7  # ceil(701/200)=4 vs ceil(900/200)=5, +2
    # threads, mini and opportunity counts do not enter N (R6 O2: dirty + snapshots pending only)
    assert dr.n_for({"A": site(threads=900, mini=900, opp=900)}) == 2


def test_the_total_counts_all_five_conditions() -> None:
    for field in ("dirty", "snap", "threads", "mini", "opp"):
        assert dr.total({"A": site(**{field: 1})}) == 1
    assert dr.total({"A": site(), "B": site()}) == 0


def test_step_done_continue_over_n_and_the_two_fails() -> None:
    zero, some = {"A": site()}, {"A": site(opp=2)}
    fewer = {"A": site(opp=1)}
    assert dr.step([some, zero], 1, 3)[0] == "done"
    assert dr.step([some, fewer], 1, 3)[0] == "continue"
    assert dr.step([some, fewer], 4, 3)[0] == "over_n"
    assert dr.step([some, fewer], 7, 3)[0] == "fail"  # past 2N
    assert dr.step([some, fewer], 6, 3)[0] == "over_n"  # 2N itself is allowed
    verdict, reason = dr.step([some, some, some], 2, 3)
    assert verdict == "fail" and "flat" in reason
    # the same counts but different pending ids is not flat
    a, b, c = ({"A": site(snap=1, ids=[x])} for x in ("e1", "e2", "e3"))
    assert dr.step([a, b, c], 2, 3)[0] == "continue"
    # one flat tick is not a stop
    assert dr.step([some, some, fewer], 2, 3)[0] == "continue"


def test_cap_seconds_is_a_prepare_option() -> None:
    done = subprocess.run([sys.executable, str(REPO / "tools" / "demo_combined.py"), "--db", "x", "--work", "y",
                           "prepare", "--help"], capture_output=True, text=True)
    assert "--cap-seconds" in done.stdout
    done = subprocess.run([sys.executable, str(REPO / "tools" / "demo_combined.py"), "--db", "x", "--work", "y",
                           "tick", "--help"], capture_output=True, text=True)
    assert "--until-drained" in done.stdout


URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
l2 = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text

    from test_s1_bindings_postgres import engine, store  # noqa: F401
    import test_w402_reads_postgres as w402
    from test_ch1b_outbox_postgres import _jobs


class FakeDemo(dc.Demo):
    """The real `drain`, with the tick replaced by a SQL step that works through a seeded backlog."""

    def __init__(self, work: Path, engine, site_id, per_tick: int | None) -> None:  # noqa: D107
        self.work, self.engine, self.site_id, self.per_tick = work, engine, site_id, per_tick
        self.drains, self.ticks = {}, 0
        self.tree = work

    def counts(self) -> dict:
        return dr.counts(URL)

    def performance_and_prebuild(self) -> None:
        pass

    def py(self, *argv, **kw):  # the only child the drain starts here is the raw tick
        self.ticks += 1
        if self.per_tick is not None:
            with self.engine.begin() as c:
                c.execute(text("UPDATE recompute_job SET status = 'DONE' WHERE id IN (SELECT id FROM recompute_job "
                               "WHERE site_id = :s AND status = 'PENDING' AND domain = 'mini_opportunity' "
                               "ORDER BY created_at, id LIMIT :n)"), {"s": self.site_id, "n": self.per_tick})
                c.execute(text("UPDATE recompute_job SET status = 'DONE' WHERE site_id = :s AND status IN "
                               "('PENDING', 'LEASED') AND domain <> 'mini_opportunity'"), {"s": self.site_id})
                c.execute(text("INSERT INTO event_consumption (consumer, event_id) SELECT v.c, o.event_id FROM "
                               "event_outbox o CROSS JOIN (VALUES ('snapshots'), ('threads')) v(c) "
                               "WHERE o.site_id = :s ON CONFLICT DO NOTHING"), {"s": self.site_id})
        return subprocess.CompletedProcess(argv, 0, '{"outcome": "COMPLETED"}', "")


def _backlog(store, engine, jobs: int):  # noqa: F811
    _, t, s = w402._setup(store, engine)
    with engine.begin() as c:
        _jobs(c, t, s, jobs)
    return t, s


@l2
def test_counts_read_live_opportunity_jobs_and_pending_events(store, engine) -> None:  # noqa: F811
    t, s = _backlog(store, engine, 3)
    counts = dr.counts(URL)
    mine = next(v for k, v in counts.items() if v["opportunity_live"] >= 3)
    assert mine["opportunity_live"] >= 3 and set(dr.FIELDS) <= set(mine)
    assert mine["snapshots_pending"] + mine["threads_pending"] >= 0 and isinstance(mine["pending_ids"], list)


@l2
def test_the_drain_stops_at_zero(store, engine, tmp_path) -> None:  # noqa: F811
    t, s = _backlog(store, engine, 3)
    demo = FakeDemo(tmp_path, engine, s, per_tick=100)
    record = demo.drain("zero")
    assert dr.total(record["end"]) == 0
    assert record["over_n"] is False and demo.ticks == record["ticks"] == 1 and (tmp_path / "zero.json").is_file()


@l2
def test_the_drain_reports_over_n_and_still_finishes(store, engine, tmp_path) -> None:  # noqa: F811
    t, s = _backlog(store, engine, 4)
    demo = FakeDemo(tmp_path, engine, s, per_tick=1)
    record = demo.drain("slow")
    assert record["over_n"] is True and record["ticks"] > record["N"] and record["ticks"] <= 2 * record["N"]


@l2
def test_the_drain_fails_on_two_flat_ticks(store, engine, tmp_path) -> None:  # noqa: F811
    t, s = _backlog(store, engine, 3)
    demo = FakeDemo(tmp_path, engine, s, per_tick=None)
    with pytest.raises(SystemExit) as stop:
        demo.drain("flat")
    assert "DRAIN FAILED" in str(stop.value) and "flat" in str(stop.value)
    assert demo.ticks == 2
