"""CH-9b3 L2 (CH9b3-R Q1-Q5, Q9, Q10): the mill verdict on Postgres (0052), over real `site_day_snapshot` rows.

On the CH-9b1 `mill` fixture (W4-02 MINIGRID Site, CH-4's seeded opportunity) the MINI Action is created, its case
COMPLETEd and linked, the plan frozen (CH-9b2), and then:

- VERIFIED / INEFFECTIVE TARGET_MISS / INCONCLUSIVE BASELINE_ZERO: one outcome row (`action_id` NULL,
  `domain_action_id` set, no request row, no `action_event`) with BASELINE / LATER / COMPARISON metrics; a second
  evaluation replays it; `domain_summary` reads it back;
- SHORT baseline and a still-open later window store nothing; once the look-ahead closes, INCONCLUSIVE LATER_SHORT;
- the stage helper `evaluate_domain_plans` judges every undecided plan of the Site once;
- the lifecycle read `_OUTCOMES` names the domain Action and dates a VERIFIED from the plan's `effective_from` (Q10).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
from types import SimpleNamespace

import pytest

from test_s4_finding_store_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from test_ch9b1_opportunity_actions_postgres import _complete_case, _create, mill  # noqa: F401
    from test_ch2_thread_store_postgres import seeded  # noqa: F401
    from test_s1_bindings_postgres import engine, store  # noqa: F401

    import pg_harness
    from assetops_backend.actions.adapters.postgres_action_store import PostgresActionStore
    from assetops_backend.actions.composition import evaluate_domain_plans
    from assetops_backend.actions.verification import VerificationPorts, VerificationService
    from assetops_backend.chain.adapters.postgres_snapshot_store import PostgresSnapshotStore
    from assetops_backend.chain.adapters.postgres_thread_sources import _OUTCOMES
    from assetops_backend.chain.ports import SnapshotRow
    from assetops_backend.chain.reader import SnapshotReader
    from zoneinfo import ZoneInfo


class Clock:
    def __init__(self, at: datetime) -> None:
        self.at = at

    def __call__(self) -> datetime:
        return self.at


def _service(mill, clock):
    snaps = PostgresSnapshotStore(URL)
    actions = SimpleNamespace(store=PostgresActionStore(URL), clock=clock,
                              verification_ports=VerificationPorts(snapshots=SnapshotReader(snaps)))
    mill.disposables = [actions.store, snaps]
    mill.reader = actions.verification_ports.snapshots
    return VerificationService(actions)


def _snap(mill, day, kwh, grade="COMPLETE", subject="asset:mill"):
    PostgresSnapshotStore(URL).append(SnapshotRow(
        tenant_id=mill.t, site_id=mill.s, local_day=day, subject_kind="ASSET", subject_ref=subject,
        measure="productive_kwh", evidence_class="MEASURED", revision=1, expected=True, required_seconds=36000,
        covered_seconds=36000 if grade == "COMPLETE" else 1000, coverage_pct="100.0", grade=grade,
        value={"kwh": kwh, "measured_seconds": 36000}, money=None, policy_version="p1", calendar_version="c1",
        catalogue_version=1, input_fp=hashlib.sha256(f"{day}-{subject}-{grade}-{kwh}".encode()).hexdigest()))


def _frozen(mill, tag, baseline_kwh="10", baseline_back=(1, 2, 3)):
    """Create, complete, link and freeze; returns (service, clock, action id, effective day, tz)."""
    action = _create(mill, idempotency_key=f"{tag}-mill-0001")
    case_id = _complete_case(mill, action["id"], tag)
    with mill.engine.connect() as c:
        occurred = c.execute(text("SELECT occurred_at FROM work_event WHERE case_id = :c AND kind = 'COMPLETE'"),
                             {"c": case_id}).scalar_one()
        tz = c.execute(text("SELECT timezone FROM site WHERE id = :s"), {"s": mill.s}).scalar_one()
    eff = occurred.astimezone(ZoneInfo(tz)).date()
    for back in baseline_back:
        _snap(mill, eff - timedelta(days=back), baseline_kwh)
    clock = Clock(occurred + timedelta(hours=1))
    svc = _service(mill, clock)
    status, _ = svc.freeze_domain_plan(mill.t, mill.s, action["id"])
    assert status == 201
    return svc, clock, action["id"], eff, tz


def _later(mill, eff, kwh, ahead=(1, 2, 3)):
    for d in ahead:
        _snap(mill, eff + timedelta(days=d), kwh)


def _after(eff, tz, days):
    return datetime.combine(eff + timedelta(days=days), datetime.min.time(), ZoneInfo(tz)).astimezone(timezone.utc) \
        + timedelta(hours=12)


def _count(mill, sql):
    with mill.engine.connect() as c:
        return c.execute(text(sql)).scalar_one()


def _close(mill):
    pg_harness.dispose(*getattr(mill, "disposables", []))


def test_verified_stores_one_domain_outcome_reads_back_and_links_to_lifecycle(mill) -> None:
    svc, clock, aid, eff, tz = _frozen(mill, "ch9b3-ok")
    try:
        _later(mill, eff, "11.5")
        _snap(mill, eff, "999")  # the effective day is in neither window
        clock.at = _after(eff, tz, 5)
        got = svc.evaluate_domain_plan(mill.t, mill.s, aid)
        assert got["state"] == "VERIFIED" and got["stored"] is True, got
        again = svc.evaluate_domain_plan(mill.t, mill.s, aid)
        assert again["replayed"] is True and again["outcome_id"] == got["outcome_id"]
        with mill.engine.connect() as c:
            o = c.execute(text("SELECT action_id, domain_action_id, outcome, reasons, evaluation_request_id, "
                               "triggering_job FROM verification_outcome")).one()
            metrics = c.execute(text("SELECT window_name, state, value_text, threshold_text FROM verification_metric "
                                     "ORDER BY window_name")).all()
        assert o.action_id is None and str(o.domain_action_id) == aid and o.outcome == "VERIFIED"
        assert o.reasons == ["TARGET_MET"] and o.evaluation_request_id is None
        assert [tuple(m) for m in metrics] == [("BASELINE", "PASS", "10.00", None), ("COMPARISON", "PASS", "11.50",
                                                "11.00"), ("LATER", "PASS", "11.50", None)]
        assert _count(mill, "SELECT count(*) FROM verification_evaluation_request") == 0
        body = svc.domain_summary(mill.t, mill.s, aid)
        assert body["state"] == "VERIFIED" and body["cost_check"] is None and body["trial_hours"] is None
        assert body["sentence"] == "Midday use rose by at least the declared 10% on fully checked days"
        assert body["line"] == ("Midday use before and after the change: 10.00 → 11.50 kWh a day on 3 fully "
                                "checked days each")
        assert body["metrics"][0]["before"] == "10.00" and body["metrics"][0]["after"] == "11.50"
        assert body["plan"]["later_days"] == [(eff + timedelta(days=d)).isoformat() for d in (1, 2, 3)]
        with mill.engine.connect() as c:  # Q10: the lifecycle read links the outcome to its domain Action
            lc = c.execute(text(_OUTCOMES), {"t": mill.t, "s": mill.s}).one()
            effective = c.execute(text("SELECT effective_from FROM verification_plan")).scalar_one()
        assert str(lc.action_id) == aid and lc.effective_from == effective and lc.outcome == "VERIFIED"
    finally:
        _close(mill)


def test_target_miss_is_ineffective(mill) -> None:
    svc, clock, aid, eff, tz = _frozen(mill, "ch9b3-miss")
    try:
        _later(mill, eff, "10.9")
        clock.at = _after(eff, tz, 5)
        assert svc.evaluate_domain_plan(mill.t, mill.s, aid)["state"] == "INEFFECTIVE"
        body = svc.domain_summary(mill.t, mill.s, aid)
        assert body["reasons"] == ["TARGET_MISS"] and body["sentence"] is None
        assert body["metrics"][0]["state"] == "FAIL"
    finally:
        _close(mill)


def test_short_baseline_stores_nothing_and_reads_not_judged(mill) -> None:
    svc, clock, aid, eff, tz = _frozen(mill, "ch9b3-short", baseline_back=(1, 2))
    try:
        _later(mill, eff, "20")
        clock.at = _after(eff, tz, 20)
        assert svc.evaluate_domain_plan(mill.t, mill.s, aid)["stored"] is False
        assert _count(mill, "SELECT count(*) FROM verification_outcome") == 0
        body = svc.domain_summary(mill.t, mill.s, aid)
        assert body["state"] == "NOT_JUDGED" and body["outcome"] is None
        assert body["not_judged_text"] == "Not judged yet: only 2 of 3 fully checked days before the change"
    finally:
        _close(mill)


def test_later_short_waits_then_is_inconclusive_once_the_look_ahead_closes(mill) -> None:
    svc, clock, aid, eff, tz = _frozen(mill, "ch9b3-later")
    try:
        _later(mill, eff, "12", ahead=(2, 9))
        _snap(mill, eff + timedelta(days=4), "12", grade="LOW")
        clock.at = _after(eff, tz, 10)
        assert svc.evaluate_domain_plan(mill.t, mill.s, aid)["stored"] is False
        assert svc.domain_summary(mill.t, mill.s, aid)["not_judged_text"] == \
            "Not judged yet: only 2 of 3 fully checked days after the change"
        clock.at = _after(eff, tz, 15)
        got = svc.evaluate_domain_plan(mill.t, mill.s, aid)
        assert got["state"] == "INCONCLUSIVE" and got["stored"] is True
        body = svc.domain_summary(mill.t, mill.s, aid)
        assert body["reasons"] == ["LATER_SHORT"]
        assert body["line"].startswith("Only 2 of 3 fully checked days after the change in the 14 days allowed")
    finally:
        _close(mill)


def test_zero_baseline_is_inconclusive_through_the_stage_helper(mill) -> None:
    svc, clock, aid, eff, tz = _frozen(mill, "ch9b3-zero", baseline_kwh="0")
    try:
        _later(mill, eff, "0")
        now = _after(eff, tz, 5)
        judged = evaluate_domain_plans(URL, mill.t, mill.s, mill.reader, now)
        assert [(j["domain_action_id"], j["state"], j["stored"]) for j in judged] == [(aid, "INCONCLUSIVE", True)]
        assert evaluate_domain_plans(URL, mill.t, mill.s, mill.reader, now) == []  # nothing undecided is left
        clock.at = now
        body = svc.domain_summary(mill.t, mill.s, aid)
        assert body["reasons"] == ["BASELINE_ZERO"]
        assert body["sentence"] == "No midday use was measured before the change, so a 10% rise cannot be measured"
    finally:
        _close(mill)
