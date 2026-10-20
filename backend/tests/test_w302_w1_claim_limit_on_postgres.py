"""W3-02 0b: the connection-taking W1 interval projection and day reduction at a cutoff.

Rows come from the real S2 ingestion and S3 worker through the S4 `CaseRunner` (no row is seeded except the one
DONE-without-selection job, as in the W3-01 helper test). Every read runs on ONE caller-owned REPEATABLE READ
connection with the store's own `_snapshot` disabled, so a second transaction fails the test. Requires
ASSETOPS_TEST_DATABASE_URL (backend/TESTING.md).
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest

from test_s4_finding_store_postgres import SPEC, URL, CaseRunner  # noqa: F401

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from test_s1_bindings_postgres import engine, store  # noqa: F401

    import pg_harness
    from assetops_backend.analytics.adapters.postgres_assessment_store import PostgresAssessmentStore
    from assetops_backend.analytics.claim_limit_read import (
        HISTORICAL, HISTORICAL_SELECTION_UNAVAILABLE, UNKNOWN, ClaimLimitReadService, ClaimLimitRefusal, reduce_day)

F02 = next(c for c in SPEC["cases"] if c["case_id"] == "F02")
F06 = next(c for c in SPEC["cases"] if c["case_id"] == "F06")
F02_DAY = datetime(2026, 10, 8, tzinfo=timezone.utc)
F06_DAY = datetime(2026, 10, 15, tzinfo=timezone.utc)


@pytest.fixture()
def runner(store, engine):  # noqa: F811
    owned = CaseRunner(store, engine)
    yield owned
    pg_harness.dispose(owned.findings)


@pytest.fixture()
def reads(monkeypatch):
    """The store and service under test; the store's own transaction is forbidden for the whole test body."""
    owned = PostgresAssessmentStore(URL)

    def no_second_transaction(self, *args, **kwargs):
        raise AssertionError("claim_limit_on opened its own transaction")

    def forbid() -> None:
        # every store entry point to a second connection/transaction: _snapshot, _run and the engine itself
        for name in ("_snapshot", "_run", "_connect_engine"):
            monkeypatch.setattr(PostgresAssessmentStore, name, no_second_transaction)

    yield owned, ClaimLimitReadService(owned), forbid
    pg_harness.dispose(owned)


@contextmanager
def caller_snapshot(engine):  # noqa: F811
    with engine.connect().execution_options(isolation_level="REPEATABLE READ") as c:
        with c.begin():
            yield c
            assert c.in_transaction(), "a read ended the caller's transaction"


def projected(service, store, c, tenant, site, frm, to, known_at):
    """Each intersecting day: its selection at the cutoff, the window-revision projection and its reduction."""
    out = []
    for d in store.select_dispatch_days_on(c, tenant, site, frm, to, known_at):
        rev = d["window_assessment_revision_id"]
        p = service.claim_limit_on(c, tenant, site, d["day"], rev, known_at)
        out.append((d, p, reduce_day(p)))
    return out


def test_w1_two_days_each_reduced_from_all_selected_intervals(runner, reads, monkeypatch) -> None:
    for step in F02["steps"][:2]:  # deliver both sides of midnight, assess
        runner.step(step)
    known = runner.now
    monkeypatch.setattr(PostgresAssessmentStore, "_transaction_time", staticmethod(lambda c: known))
    store, service, forbid = reads
    forbid()
    with caller_snapshot(runner.engine) as c:
        days = projected(service, store, c, runner.tenant, runner.site, F02_DAY, F02_DAY + timedelta(days=2),
                         known)
    assert [d["day"] for d, _, _ in days] == [F02_DAY.date(), (F02_DAY + timedelta(days=1)).date()]
    for d, p, r in days:
        assert d["run_id"] is not None and p["available"] and p["scope"] == "WINDOW"
        intervals = sorted(str(x) for x in d["assessment_revision_ids"]
                           if str(x) != str(d["window_assessment_revision_id"]))
        # the row cites exactly the selected interval revisions; the window revision stays in the disclosure
        assert intervals and r["assessment_revision_ids"] == intervals
        assert r["window_assessment_revision_id"] == str(d["window_assessment_revision_id"])
        assert str(d["window_assessment_revision_id"]) not in r["assessment_revision_ids"]
        for i in p["intervals"]:
            assert i["currentness"] == "CURRENT" and i["accepted_evidence_ids"]
            assert set(i["accepted_evidence_ids"]) <= set(r["accepted_evidence_ids"])
            assert all(x.get("role") for x in i["reasons"] if x["code"] in ("MISSING_ROLE", "POOR_QUALITY"))
        # the window revision's claim is never the day's ceiling: a ceiling only from agreeing intervals
        pairs = {(i["ceiling"], i["statement"]) for i in p["intervals"]}
        if r["current_ceiling"] is not None:
            assert len(pairs) == 1 and r["ceiling_source"] == "W1_CLAIM_LIMIT"
        # role-less window reasons are disclosed but never become gaps
        assert all("role" not in w for w in p["window_reasons"])
        assert all(g["missing_role"] for g in r["gaps"])
        assert {(g["gap_code"], g["missing_role"]) for g in r["gaps"]} == {
            (x["code"], x["role"]) for i in p["intervals"] for x in i["reasons"]
            if x.get("role") and x["code"] in ("MISSING_ROLE", "GENERATOR_UNOBSERVED", "POOR_QUALITY",
                                               "CONFLICTING")}


def test_w1_cutoff_excludes_later_assessment_and_acceptance(runner, reads, monkeypatch) -> None:
    runner.step(F06["steps"][0])  # deliver
    runner.step(F06["steps"][1])  # assess: the day's first selection
    cutoff = runner.now
    for step in F06["steps"][3:5]:  # release the held contradiction, assess: a later selection of the same day
        runner.step(step)
    present = runner.now

    def clock(at):
        monkeypatch.setattr(PostgresAssessmentStore, "_transaction_time", staticmethod(lambda c: at))

    clock(present)
    store, service, forbid = reads
    with caller_snapshot(runner.engine) as c:
        later_accepted = c.execute(text(
            "SELECT min(decided_at) FROM ingestion_disposition d JOIN accepted_evidence e "
            "ON e.id = d.accepted_evidence_id WHERE e.site_id = :s AND d.decided_at > :k"),
            {"s": runner.site, "k": cutoff}).scalar_one()
        forbid()
        (d_then, then_hist, r_hist), = projected(service, store, c, runner.tenant, runner.site, F06_DAY,
                                                 F06_DAY + timedelta(days=1), cutoff)
        clock(cutoff)  # the same selection read live (the cutoff is the transaction time): a current claim
        (d_then, then, r_then), = projected(service, store, c, runner.tenant, runner.site, F06_DAY,
                                            F06_DAY + timedelta(days=1), cutoff)
        clock(present)
        (d_now, now, r_now), = projected(service, store, c, runner.tenant, runner.site, F06_DAY,
                                         F06_DAY + timedelta(days=1), present)
        # the later window revision read at the earlier cutoff: recorded after it, so not reconstructable
        late = service.claim_limit_on(c, runner.tenant, runner.site, F06_DAY.date(),
                                      d_now["window_assessment_revision_id"], cutoff)
        # the earlier selection read at the present: kept with its IDs as history, no current claim
        old = service.claim_limit_on(c, runner.tenant, runner.site, F06_DAY.date(),
                                     d_then["window_assessment_revision_id"], present)
    assert later_accepted is not None and later_accepted > cutoff  # acceptance on both sides of the cutoff
    assert d_then["run_id"] != d_now["run_id"]
    assert r_then["assessment_revision_ids"] != r_now["assessment_revision_ids"]
    # disagreeing intervals at the cutoff: a FULL and a LIMITED interval give a LIMITED day with no single ceiling,
    # each interval keeping its own ceiling in the disclosure; role-tagged gaps come from the LIMITED interval only
    assert sorted(i["state"] for i in then["intervals"]) == ["FULL", "LIMITED"]
    assert r_then["state"] == "LIMITED" and r_then["current_ceiling"] is None and r_then["ceiling_source"] is None
    assert len({(c["ceiling"], c["statement"]) for c in r_then["interval_ceilings"]}) == 2
    limited = [i["assessment_revision_id"] for i in then["intervals"] if i["state"] == "LIMITED"]
    assert r_then["gaps"] and all(g["missing_role"] and g["assessment_revision_ids"] == limited
                                  for g in r_then["gaps"])
    assert {g["domain"] for g in r_then["gaps"]} == {"mini_grid"}
    assert ("GENERATOR_UNOBSERVED", "generator_state") in {(g["gap_code"], g["missing_role"]) for g in r_then["gaps"]}
    # the later selection (after the released contradiction) is CONTRADICTORY and never borrows the earlier ceiling
    assert r_now["state"] == "CONTRADICTORY" and r_now["current_ceiling"] is None
    # nothing accepted after the cutoff is cited by the cutoff's day
    with caller_snapshot(runner.engine) as c:
        cited_late = c.execute(text(
            "SELECT count(*) FROM ingestion_disposition WHERE accepted_evidence_id = ANY(:ids) "
            "AND decided_at > :k"),
            {"ids": [UUID(x) for x in r_then["accepted_evidence_ids"]], "k": cutoff}).scalar_one()
    assert r_then["accepted_evidence_ids"] and cited_late == 0
    assert late["available"] is False and late["intervals"] == []
    assert {x["code"] for x in late["reasons"]} == {HISTORICAL_SELECTION_UNAVAILABLE}
    assert any(x["text"].startswith("REVISION_AFTER_CUTOFF") for x in late["reasons"])
    assert reduce_day(late)["state"] == UNKNOWN and reduce_day(late)["current_ceiling"] is None
    # the same cutoff read from the present is HISTORICAL: exact IDs and disclosure, no current claim at all
    assert then_hist["currentness"] == HISTORICAL and r_hist["currentness"] == HISTORICAL
    assert r_hist["state"] == UNKNOWN and r_hist["current_ceiling"] is None and r_hist["ceiling_source"] is None
    assert r_hist["ceiling_statement"] is None and r_hist["gaps"] == [] and r_hist["historical_gaps"]
    assert r_hist["assessment_revision_ids"] == r_then["assessment_revision_ids"]
    assert r_hist["accepted_evidence_ids"] == r_then["accepted_evidence_ids"]
    assert r_hist["window_assessment_revision_id"] == r_then["window_assessment_revision_id"]
    assert r_hist["historical_statements"][1] == "No current ceiling"
    for i, live in zip(then_hist["intervals"], then["intervals"]):
        assert i["currentness"] == HISTORICAL and i["current_positive_claim"] is False
        assert all(i[k] is None for k in ("ceiling", "support", "supported_minutes", "statement"))
        assert i["historical_ceiling"] == {k: live[k] for k in ("ceiling", "support", "supported_minutes",
                                                                "statement")}
    assert old["available"] and old["currentness"] == HISTORICAL and old["intervals"]
    for i in old["intervals"]:
        assert i["currentness"] == HISTORICAL and i["ceiling"] is None and i["statement"] is None
        assert not i["current_positive_claim"] and i["historical_ceiling"] is not None
        assert i["accepted_evidence_ids"] and i["reasons"][0]["code"] == "NOT_CURRENT"
    old_day = reduce_day(old)
    assert old_day["current_ceiling"] is None and old_day["state"] == UNKNOWN
    assert old_day["assessment_revision_ids"] == r_then["assessment_revision_ids"]


def test_w1_unavailable_history_is_unknown(runner, reads, monkeypatch) -> None:
    runner.step(F06["steps"][0])  # deliver: the recompute job is recorded, still unselected
    queued = runner.now
    present = queued + timedelta(hours=1)
    monkeypatch.setattr(PostgresAssessmentStore, "_transaction_time", staticmethod(lambda c: present))
    with runner.engine.begin() as c:  # a DONE job with zero selections: its state at the cutoff is not stored
        assert c.execute(text("UPDATE recompute_job SET status = 'DONE' WHERE site_id = :s"),
                         {"s": runner.site}).rowcount >= 1
    store, service, forbid = reads
    forbid()
    with caller_snapshot(runner.engine) as c:
        p = service.claim_limit_on(c, runner.tenant, runner.site, F06_DAY.date(), None, queued)
    assert p["available"] is False and p["intervals"] == [] and p["currentness"] is None
    assert [x["code"] for x in p["reasons"]] == [HISTORICAL_SELECTION_UNAVAILABLE]
    assert p["reasons"][0]["text"].startswith("JOB_STATE_AT_CUTOFF_UNKNOWN")
    day = reduce_day(p)
    assert day["state"] == UNKNOWN and day["current_ceiling"] is None and day["ceiling_source"] is None
    assert [x["code"] for x in day["reasons"]] == [HISTORICAL_SELECTION_UNAVAILABLE]


def test_w1_historical_conflict_is_contradictory_without_a_current_ceiling(runner, reads, monkeypatch) -> None:
    for step in F06["steps"][:2] + F06["steps"][3:5]:  # the released contradiction is the day's later selection
        runner.step(step)
    present = runner.now
    later = present + timedelta(hours=1)
    monkeypatch.setattr(PostgresAssessmentStore, "_transaction_time", staticmethod(lambda c: later))
    store, service, forbid = reads
    forbid()
    with caller_snapshot(runner.engine) as c:
        (d, p, r), = projected(service, store, c, runner.tenant, runner.site, F06_DAY, F06_DAY + timedelta(days=1),
                               present)
    assert p["currentness"] == HISTORICAL and r["state"] == "CONTRADICTORY"
    assert r["current_ceiling"] is None and r["ceiling_source"] is None and r["gaps"] == []
    assert r["assessment_revision_ids"] and r["accepted_evidence_ids"]
    assert "Conflicting records (historical, as of the cutoff)" in r["historical_statements"]
    assert any("REPORTS_OVERLAP" in x for x in r["historical_statements"][3:]), r["historical_statements"]


def test_w1_window_path_projects_the_selected_later_run_of_a_reused_interval(runner, reads, monkeypatch) -> None:
    for step in F06["steps"][:2] + F06["steps"][3:5]:
        runner.step(step)
    present = runner.now
    monkeypatch.setattr(PostgresAssessmentStore, "_transaction_time", staticmethod(lambda c: present))
    store, service, forbid = reads
    forbid()
    with caller_snapshot(runner.engine) as c:
        (d, p, r), = projected(service, store, c, runner.tenant, runner.site, F06_DAY, F06_DAY + timedelta(days=1),
                               present)
        reused = c.execute(text(
            "SELECT v.id, v.analytic_run_id FROM assessment_revision v JOIN analytic_run_assessment l "
            "ON l.assessment_revision_id = v.id WHERE l.run_id = :r AND l.scope = 'INTERVAL' "
            "AND v.analytic_run_id <> :r"), {"r": d["run_id"]}).all()
        assert reused, "fixture: the later selected run must reuse an interval revision created by an earlier run"
        interval_rev = str(reused[0][0])
        with pytest.raises(ClaimLimitRefusal) as refused:  # a single INTERVAL revision is not a selection
            service.claim_limit_on(c, runner.tenant, runner.site, F06_DAY.date(), UUID(interval_rev), present)
    assert (refused.value.status, refused.value.detail["code"]) == (422, "REVISION_NOT_WINDOW")
    by_id = {i["assessment_revision_id"]: i for i in p["intervals"]}
    assert interval_rev in by_id and p["run_id"] == str(d["run_id"]) != str(reused[0][1])
    assert sorted(by_id) == r["assessment_revision_ids"]
    # currentness comes from the selected later run's membership, not the interval revision's creating run
    assert by_id[interval_rev]["currentness"] != HISTORICAL and by_id[interval_rev]["accepted_evidence_ids"]
    assert by_id[interval_rev]["selected"] is True


def test_w1_second_transaction_entry_points_are_trapped(reads) -> None:
    store, _, forbid = reads
    forbid()
    for call in (lambda: store._run(lambda c: None), lambda: store._snapshot(lambda c: None),
                 lambda: store._connect_engine()):
        with pytest.raises(AssertionError, match="opened its own transaction"):
            call()
