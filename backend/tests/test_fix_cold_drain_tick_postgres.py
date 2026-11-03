"""FIX-COLD-DRAIN U3 against PostgreSQL: the scheduled tick assesses and drains cold and EV work (build sheet §3).

- P1: the W2-02/W2-03 cold `excursion` replay (accepted cold evidence, a PENDING `cold_chain` job, no run). One tick
  leaves the job DONE, every cold consequence work item SUCCEEDED and an excursion consequence revision; the Portfolio
  read for the day is then not money-pending. A second tick appends no attempt and no revision.
- P2: the W2-05b EV `complete` replay with the W2-07 golden tariff: one tick assesses the `ev_charging` job, then
  drains the EV consequence work; the EV money guard is neither PENDING_RECOMPUTE nor STALE_BASIS and a head exists.
- P3: the cold basis read raises once. Tick 1 reports the drain OK with one failed item and one FAILED attempt; a
  tick before `retry_due_at` adds no attempt (`deferred == 1`); once due, the next tick succeeds.
- P4: a mini-only Site's tick is unchanged apart from the four new `stages` keys, each a 0-count OK (the sheet's
  "byte-identical" read as: the old stage results and the head counters equal the old stages' own counts).

The tick runs the real stage functions in-process (`InProcessRunner`), on the reset `*_test` database each replay
opens. Requires ASSETOPS_TEST_DATABASE_URL; skipped (never passed) without it.
"""

from __future__ import annotations

import os
from datetime import timedelta
from urllib.parse import urlencode

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from sqlalchemy import text
    from test_s1_bindings_postgres import engine, store  # noqa: F401 - the mini-grid fixtures (P4)
    from test_s4_schedule_tick_postgres import FAST, make_tick
    from test_w203_cold_replay_postgres import opened
    from test_w207_ev_money_postgres import ev_money_rows, golden_tariff, money_head, snapshot_state
    from test_w301_estate_golden_postgres import cold_chain, ev_chain  # noqa: F401 - the replay factories
    from test_w302_evidence_scope_snapshot_postgres import evidence_read
    from test_w402_mini_stage_postgres import _installed

    from assetops_backend.estate import portfolio
    from assetops_backend.estate.portfolio import EstatePortfolioService
    from assetops_backend.estate.scope import PORTFOLIO_CURSOR_KEY_ENV
    from assetops_backend.estate_portfolio_api import build_estate_portfolio_router
    from assetops_backend.financials.adapters.postgres_consequence_store import ColdUnit
    from assetops_backend.scheduling.tick import TickLimits

NEW = ("cold_assess", "ev_assess", "cold_consequence", "ev_consequence")
DAY = {"from": "2026-10-06T00:00:00Z", "to": "2026-10-07T00:00:00Z"}


def q(engine, sql: str, **p) -> list[dict]:  # noqa: F811
    with engine.connect() as c:
        return [dict(r._mapping) for r in c.execute(text(sql), p)]


def tick_site(tick, site_id):
    report = tick.tick()
    assert report.outcome == "COMPLETED", report.failure
    [site] = [s for s in report.selected if str(s.site_id) == str(site_id)]
    return site


def cold_counts(built) -> dict:
    return {t: q(built.engine, f"SELECT count(*) AS n FROM {t} WHERE site_id = :s", s=built.site_id)[0]["n"]
            for t in ("cold_consequence_work_attempt", "cold_consequence_revision", "analytic_run",
                      "assessment_revision")}


def unsettled_cold_work(built) -> list[dict]:
    """Cold work items of the Site with no SUCCEEDED attempt."""
    return q(built.engine, "SELECT w.id FROM cold_consequence_work w WHERE w.site_id = :s AND NOT EXISTS (SELECT 1 "
                           "FROM cold_consequence_work_attempt a WHERE a.work_id = w.id AND a.outcome = 'SUCCEEDED')",
             s=built.site_id)


def portfolio_read(built, monkeypatch) -> tuple[dict, list[bool]]:
    """The Portfolio body for the replay day, and every `money_pending` verdict the read computed."""
    monkeypatch.setenv(PORTFOLIO_CURSOR_KEY_ENV, "3e" * 32)
    verdicts: list[bool] = []
    real = portfolio.money_pending

    def spy(cov, lines):
        verdicts.append(real(cov, lines))
        return verdicts[-1]

    monkeypatch.setattr(portfolio, "money_pending", spy)
    app = FastAPI()
    app.include_router(build_estate_portfolio_router(
        EstatePortfolioService(evidence_read(built.engine)), lambda: built.tenant_id,
        access=lambda request, code: None))
    response = TestClient(app).get("/api/estate/portfolio?" + urlencode({**DAY, "limit": 100}))
    assert response.status_code == 200, response.text
    monkeypatch.setattr(portfolio, "money_pending", real)
    return response.json(), verdicts


def test_p1_one_tick_assesses_and_drains_cold_work(cold_chain, monkeypatch) -> None:  # noqa: F811
    built = opened("excursion", cold_chain)
    jobs = q(built.engine, "SELECT status FROM recompute_job WHERE site_id = :s AND domain = 'cold_chain'",
             s=built.site_id)
    assert jobs and {j["status"] for j in jobs} == {"PENDING"}, jobs
    assert cold_counts(built)["analytic_run"] == 0
    tick, runner = make_tick(TickLimits(**FAST))
    site = tick_site(tick, built.site_id)
    assert [c for c, s in runner.calls if s in (None, str(built.site_id))] == [
        "discover", "s3", "cold_assess", "ev_assess", "mini", "opportunity", "s4", "chain_threads", "consequence",
        "cold_consequence",
        "ev_consequence"]
    assert site.result == "COMPLETED" and site.failure is None, (site.failure, site.stages)
    assess, drain = site.stages["cold_assess"], site.stages["cold_consequence"]
    assert assess["code"] == "OK" and assess["processed"] == len(jobs) and assess["failed"] == 0, assess
    assert drain["code"] == "OK" and drain["selected"] >= 1 and drain["failed"] == 0 and drain["backlog"] == 0, drain
    assert {j["status"] for j in q(built.engine, "SELECT status FROM recompute_job WHERE site_id = :s AND "
                                                 "domain = 'cold_chain'", s=built.site_id)} == {"DONE"}
    assert q(built.engine, "SELECT count(*) AS n FROM cold_consequence_work WHERE site_id = :s",
             s=built.site_id)[0]["n"] >= 1
    assert unsettled_cold_work(built) == []
    assert q(built.engine, "SELECT count(*) AS n FROM cold_consequence_revision r JOIN finding_revision f ON "
                           "f.id = r.finding_revision_id JOIN finding g ON g.id = f.finding_id WHERE r.site_id = :s "
                           "AND g.mechanism = 'COLD_EXCURSION'", s=built.site_id)[0]["n"] >= 1
    head = tick.store.site_head(built.tenant_id, built.site_id)
    assert head["s3_processed"] == site.stages["s3"]["processed"] + assess["processed"] + site.stages[
        "ev_assess"]["processed"]
    assert head["consequence_processed"] == site.stages["consequence"]["selected"] + drain["selected"] + site.stages[
        "ev_consequence"]["selected"]
    body, verdicts = portfolio_read(built, monkeypatch)
    assert verdicts and not any(verdicts), verdicts  # the cold window is no longer money-pending
    assert body["status"] != "PENDING", body["status"]

    settled = cold_counts(built)
    again = tick_site(tick, built.site_id)
    assert again.result == "COMPLETED" and again.stages["cold_assess"]["processed"] == 0
    assert again.stages["cold_consequence"]["selected"] == 0
    assert cold_counts(built) == settled  # zero new attempts, revisions or runs


def test_p2_one_tick_assesses_then_drains_ev_work(ev_chain) -> None:  # noqa: F811
    built = ev_chain("complete")
    built.start_release_upload()
    golden_tariff(built)
    assert q(built.engine, "SELECT status FROM recompute_job WHERE site_id = :s AND domain = 'ev_charging'",
             s=built.site_id), "the replay enqueued no EV job"
    assert ev_money_rows(built)["ev_consequence_revision"] == []
    tick, runner = make_tick(TickLimits(**FAST))
    site = tick_site(tick, built.site_id)
    assert site.result == "COMPLETED" and site.failure is None, (site.failure, site.stages)
    assess, drain = site.stages["ev_assess"], site.stages["ev_consequence"]
    assert assess["code"] == "OK" and assess["processed"] >= 1 and assess["failed"] == 0, assess
    assert drain["code"] == "OK" and drain["selected"] >= 1 and drain["failed"] == 0, drain
    assert {j["status"] for j in q(built.engine, "SELECT status FROM recompute_job WHERE site_id = :s AND "
                                                 "domain = 'ev_charging'", s=built.site_id)} == {"DONE"}
    assert snapshot_state(built) not in ("PENDING_RECOMPUTE", "STALE_BASIS")
    head = money_head(ev_money_rows(built))
    assert (head["state"], head["reason"]) == ("ESTIMATED", "ELIGIBLE_COMPLETE_INTERVALS"), head


def test_p3_failed_cold_item_retries_on_its_own_schedule(cold_chain, monkeypatch) -> None:  # noqa: F811
    built = opened("excursion", cold_chain)
    real, raised = ColdUnit.basis, []

    def once(self, finding_revision_id):
        if not raised:
            raised.append(finding_revision_id)
            raise RuntimeError("injected cold basis read failure")
        return real(self, finding_revision_id)

    monkeypatch.setattr(ColdUnit, "basis", once)
    tick, _ = make_tick(TickLimits(**FAST))
    first = tick_site(tick, built.site_id)
    drain = first.stages["cold_consequence"]
    assert raised and drain["code"] == "OK" and drain["failed"] == 1, drain
    failed = q(built.engine, "SELECT work_id, attempt_no, error_code FROM cold_consequence_work_attempt "
                             "WHERE site_id = :s AND outcome = 'FAILED'", s=built.site_id)
    assert len(failed) == 1 and failed[0]["attempt_no"] == 1, failed
    assert first.failure is None  # ruling (b): an item failure retries under its own `retry_due_at`
    body, verdicts = portfolio_read(built, monkeypatch)
    assert any(verdicts) and body["status"] == "PENDING", (verdicts, body["status"])  # P1's read can say pending

    attempts = cold_counts(built)["cold_consequence_work_attempt"]
    early = tick_site(tick, built.site_id)
    assert early.stages["cold_consequence"]["deferred"] == 1 and early.stages["cold_consequence"]["selected"] == 0
    assert cold_counts(built)["cold_consequence_work_attempt"] == attempts  # not due yet: no new attempt

    with built.engine.begin() as c:  # test DB only: make the failed attempt's retry due
        c.execute(text("SET LOCAL session_replication_role = replica"))
        c.execute(text("UPDATE cold_consequence_work_attempt SET finished_at = finished_at - :d WHERE site_id = :s "
                       "AND outcome = 'FAILED'"), {"d": timedelta(minutes=5), "s": built.site_id})
    due = tick_site(tick, built.site_id)
    assert due.stages["cold_consequence"]["selected"] == 1 and due.stages["cold_consequence"]["failed"] == 0
    assert unsettled_cold_work(built) == []
    assert q(built.engine, "SELECT attempt_no FROM cold_consequence_work_attempt WHERE work_id = :w AND "
                           "outcome = 'SUCCEEDED'", w=failed[0]["work_id"]) == [{"attempt_no": 2}]


def test_p4_mini_only_site_unchanged_apart_from_four_zero_count_keys(store, engine) -> None:  # noqa: F811
    tenant_id, site_id = _installed(store, engine)
    tick, _ = make_tick(TickLimits(**FAST))
    site = tick_site(tick, site_id)
    assert list(site.stages) == ["s3", "cold_assess", "ev_assess", "mini", "opportunity", "s4", "chain_threads",
                                 "consequence",
                                 "cold_consequence", "ev_consequence"]
    for name in ("cold_assess", "ev_assess"):
        r = site.stages[name]
        assert (r["code"], r["processed"], r["failed"], r["deferred"], r["outcomes"], r["live_jobs"]) == (
            "OK", 0, 0, 0, [], []), r
    for name in ("cold_consequence", "ev_consequence"):
        r = site.stages[name]
        assert (r["code"], r["selected"], r["failed"], r["deferred"], r["backlog"], r["outcomes"]) == (
            "OK", 0, 0, 0, 0, []), r
    head = tick.store.site_head(tenant_id, site_id)
    assert (head["s3_processed"], head["s3_deferred"]) == (site.stages["s3"]["processed"],
                                                           site.stages["s3"]["deferred"])
    assert (head["consequence_processed"], head["consequence_deferred"]) == (
        site.stages["consequence"]["selected"], site.stages["consequence"]["deferred"])
    assert site.stages["mini"]["code"] == "OK" and site.stages["mini"]["processed"] == 10
    assert head["stage"] == "IDLE" and head["claim_token"] is None
    assert site.result == "COMPLETED" and site.failure is None, site.failure
