"""W2-04 commit 2: the cold consequence worker - trigger work, race, retry, idempotence and the failed attempt.

`.agent/W2-04-build-spec.md` "Fixtures, named tests and guards" (`test_w204_cold_worker.py`) and the last paragraph
of "Money schema `0023` and rules". Replay cases run the W2-02 chain and the W2-03 worker in a fresh private
`*_test` database (no hand-inserted accepted, assessment or Finding row); the unpaired-basis case uses the W2-03
migration fixture's synthetic cold heads. Needs `ASSETOPS_TEST_DATABASE_URL`; skipped (never passed) without it.
"""

from __future__ import annotations

import os
import threading
from datetime import timedelta
from uuid import uuid4

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from test_w203_cold_replay_postgres import chain, opened, rows, run  # noqa: F401 - `chain` is the W2-02 fixture
    from test_w204_cold_migration import cold_heads, ctx, engine, site, store  # noqa: F401 - fixtures
    from test_w204_cold_migration import work as work_rows

    from assetops_backend.financials import cold_consequence as cc
    from assetops_backend.financials.composition import build_cold_consequence_worker
    from assetops_backend.financials.recompute import retry_due_at


def worker():
    return build_cold_consequence_worker(URL)


def db_now(built):
    from sqlalchemy import text

    with built.engine.connect() as c:
        return c.execute(text("SELECT clock_timestamp()")).scalar_one()


def attempts(built, work_id=None) -> list:
    sql = ("SELECT a.work_id, a.attempt_no, a.outcome, a.error_code, a.consequence_revision_ids, a.finished_at "
           "FROM cold_consequence_work_attempt a WHERE a.site_id = :s")
    if work_id is not None:
        return rows(built, sql + " AND a.work_id = :w ORDER BY a.attempt_no", w=work_id)
    return rows(built, sql + " ORDER BY a.work_id, a.attempt_no")


def excursion_work(built) -> dict:
    """The FINDING_REVISION_APPENDED work of the excursion Finding's revision."""
    [w] = rows(built, "SELECT w.* FROM cold_consequence_work w JOIN finding_revision r ON r.id = w.finding_revision_id "
                      "JOIN finding f ON f.id = r.finding_id WHERE w.site_id = :s AND f.mechanism = 'COLD_EXCURSION'")
    return w


def test_trigger_work_drains_once_and_is_idempotent(chain) -> None:  # noqa: F811
    built = opened("backup-failed", chain)
    run(built)
    work = rows(built, "SELECT * FROM cold_consequence_work WHERE site_id = :s ORDER BY enqueued_at, id")
    [room] = rows(built, "SELECT id FROM asset WHERE site_id = :s AND asset_code = 'room-1'")
    cold_revisions = rows(built, "SELECT id FROM finding_revision WHERE site_id = :s AND domain = 'cold_chain'")
    episode_revisions = rows(built, "SELECT id FROM cold_episode_revision WHERE site_id = :s")
    # The triggers (never runtime code) enqueued one item per cold FindingRevision and per episode revision, all on
    # the chamber room, never the generator.
    assert sorted(str(w["finding_revision_id"]) for w in work if w["cause"] == "FINDING_REVISION_APPENDED") == sorted(
        str(r["id"]) for r in cold_revisions)
    assert sorted(str(w["episode_revision_id"]) for w in work if w["cause"] == "EPISODE_REVISION_APPENDED") == sorted(
        str(r["id"]) for r in episode_revisions)
    assert {w["room_asset_id"] for w in work} == {room["id"]}
    first = worker().run(built.tenant_id, built.site_id, limit=100, now=db_now(built))
    assert first.claimed and first.deferred == 0 and first.backlog == 0
    assert len(first.outcomes) == len(work) and all(o.succeeded for o in first.outcomes)
    [revision] = rows(built, "SELECT id FROM cold_consequence_revision WHERE site_id = :s")
    by_work = {str(o.work_id): o for o in first.outcomes}
    exc = by_work[str(excursion_work(built)["id"])]
    assert exc.consequence_revision_ids == [revision["id"]]
    # The excursion episode item derives the same basis: it returns the stored ID (replayed), never a second row.
    [episode_item] = [by_work[str(w["id"])] for w in work if w["cause"] == "EPISODE_REVISION_APPENDED"
                      and by_work[str(w["id"])].consequence_revision_ids]
    assert episode_item.consequence_revision_ids == [revision["id"]]
    assert sorted([exc.appended, episode_item.appended], key=len) == [[], [revision["id"]]]
    # The start-failure Finding and the start episode close with a successful empty-ID attempt (no fabricated row).
    empty = [o for o in first.outcomes if not o.consequence_revision_ids]
    assert empty and all(a["consequence_revision_ids"] == [] for a in attempts(built)
                         if str(a["work_id"]) in {str(o.work_id) for o in empty})
    assert all(a["attempt_no"] == 1 and a["outcome"] == "SUCCEEDED" for a in attempts(built))
    # Idempotent: nothing is pending, and a finished item records nothing more.
    again = worker().run(built.tenant_id, built.site_id, limit=100, now=db_now(built))
    assert again.outcomes == [] and again.backlog == 0
    repeat = worker().process_one(built.tenant_id, built.site_id, exc.work_id)
    assert repeat.succeeded and repeat.already_succeeded and repeat.attempt_no == 0
    assert len(attempts(built)) == len(work)


def test_concurrent_workers_append_once(chain) -> None:  # noqa: F811
    built = opened("excursion", chain)
    run(built)
    item = excursion_work(built)
    gate = threading.Barrier(2)
    outcomes: list = []

    def go() -> None:
        w = worker()
        gate.wait()
        outcomes.append(w.process_one(built.tenant_id, built.site_id, item["id"]))
        w._store.dispose()

    threads = [threading.Thread(target=go) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(60)
    assert len(outcomes) == 2 and all(o.succeeded for o in outcomes), outcomes
    assert sorted(o.already_succeeded for o in outcomes) == [False, True]
    assert [(a["attempt_no"], a["outcome"]) for a in attempts(built, item["id"])] == [(1, "SUCCEEDED")]
    assert len(rows(built, "SELECT id FROM cold_consequence_revision WHERE site_id = :s")) == 1


def test_failed_attempt_rolls_back_retries_on_schedule_and_does_not_starve(chain, monkeypatch) -> None:  # noqa: F811
    built = opened("excursion", chain)
    run(built)
    item = excursion_work(built)
    real = cc.derive

    def broken(basis):
        if basis.finding_revision_id == str(item["finding_revision_id"]):
            raise RuntimeError("derivation fault")
        return real(basis)

    monkeypatch.setattr(cc, "derive", broken)
    first = worker().run(built.tenant_id, built.site_id, limit=100, now=db_now(built))
    failed = [o for o in first.outcomes if not o.succeeded]
    # Both items that target the excursion Finding fail; every other item still succeeds in the same run.
    assert {str(o.work_id) for o in failed} >= {str(item["id"])} and len(failed) < len(first.outcomes)
    assert all(o.error_code == "COLD_RECOMPUTE_FAILED" and o.attempt_no == 1 for o in failed)
    assert rows(built, "SELECT id FROM cold_consequence_revision WHERE site_id = :s") == []  # rolled back
    [attempt] = attempts(built, item["id"])
    assert (attempt["outcome"], attempt["error_code"], attempt["consequence_revision_ids"]) == (
        "FAILED", "COLD_RECOMPUTE_FAILED", [])
    monkeypatch.setattr(cc, "derive", real)
    # A failed item stays pending and is deferred until `retry_due_at` (1 minute after its first failure).
    early = worker().run(built.tenant_id, built.site_id, limit=100, now=attempt["finished_at"] + timedelta(seconds=59))
    assert early.outcomes == [] and early.deferred == len(failed) and early.backlog == len(failed)
    due = retry_due_at(attempt["finished_at"], 1)
    retry = worker().run(built.tenant_id, built.site_id, limit=100, now=due + timedelta(seconds=len(failed)))
    assert len(retry.outcomes) == len(failed) and all(o.succeeded for o in retry.outcomes)
    assert [(a["attempt_no"], a["outcome"]) for a in attempts(built, item["id"])] == [(1, "FAILED"), (2, "SUCCEEDED")]
    assert len(rows(built, "SELECT id FROM cold_consequence_revision WHERE site_id = :s")) == 1


def test_unpaired_basis_fails_typed_and_foreign_work_is_refused(ctx, engine) -> None:  # noqa: F811
    _, frev = cold_heads(engine, ctx)  # synthetic cold heads whose claim names no episode revision
    items = {w["cause"]: w for w in work_rows(engine, ctx)}
    w = worker()
    out = w.process_one(ctx.t, ctx.s, items["FINDING_REVISION_APPENDED"]["id"])
    assert (out.succeeded, out.error_code, out.attempt_no) == (False, "COLD_BASIS_MISMATCH", 1)
    assert str(frev) in out.error_detail
    # The episode without a claiming Finding closes with a successful empty-ID attempt.
    episode = w.process_one(ctx.t, ctx.s, items["EPISODE_REVISION_APPENDED"]["id"])
    assert episode.succeeded and episode.consequence_revision_ids == [] and episode.attempt_no == 1
    # Another Site's scope cannot read or record against this work.
    foreign = w.process_one(ctx.t, uuid4(), items["FINDING_REVISION_APPENDED"]["id"])
    assert (foreign.succeeded, foreign.error_code, foreign.attempt_no) == (False, "WORK_SCOPE_MISMATCH", 0)
    pending = w._store.cold_pending_work(ctx.t, ctx.s)
    assert [p["id"] for p in pending] == [items["FINDING_REVISION_APPENDED"]["id"]]
    assert (pending[0]["last_attempt_no"], pending[0]["last_outcome"]) == (1, "FAILED")
    w._store.dispose()
