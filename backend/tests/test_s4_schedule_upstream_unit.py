"""S4-02d phase 2 without a database: the S5 seam's commit-safe selection comparison and eligibility derivation,
health derivations against DB time, and the one-off consequence runner's `now` source (I3)."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

from assetops_backend.recompute_consequences import main as consequence_main
from assetops_backend.scheduling.health import HealthThresholds, environment_health, site_observation
from assetops_backend.scheduling.upstream import UpstreamCurrentness

UTC = timezone.utc
NOW = datetime(2026, 10, 14, 12, tzinfo=UTC)
DAY = datetime(2026, 10, 6, tzinfo=UTC)


class Findings:
    def __init__(self) -> None:
        self.seq = 5

    def match_state(self, t, s, a, window_start):
        return {"window_selection_seq": self.seq, "matcher_version": "v", "match_pass_id": "p",
                "matched_through_selection_seq": 5, "match_completed_at": NOW, "matched": self.seq <= 5}

    def findings_over(self, t, s, lo, hi):
        return []


class Read:
    def __init__(self, findings: Findings, move: bool, status="CURRENT", selection=True) -> None:
        self.findings, self.move, self.status, self.selection = findings, move, status, selection

    def window(self, t, s, day):
        return {"status": self.status, "status_reasons": [], "selection": {"run_id": "r"} if self.selection
                else None, "jobs": [], "window": {}, "limitations": [], "current_basis": {}}


class Schedule:
    def __init__(self, heartbeat_age: float = 5, completed_age: float = 5) -> None:
        self.tick = {"heartbeat_at": NOW - timedelta(seconds=heartbeat_age), "claim_token": None,
                     "consecutive_failures": 0, "claim_skips": 0, "retry_due_at": None}
        self.head = {"last_completed_at": NOW - timedelta(seconds=completed_age), "last_failed_at": None,
                     "claim_token": None, "claim_skips": 0, "consecutive_failures": 0, "fence_moved_streak": 0}

    def db_now(self):
        return NOW

    def tick_head(self, env):
        return self.tick

    def site_head(self, t, s):
        return self.head


def seam(read, findings, schedule=None):
    consequences = SimpleNamespace(pending_work=lambda t, s: [])
    return UpstreamCurrentness(schedule or Schedule(), read, findings, consequences, None,
                               analytic_id="dispatch").window(uuid4(), uuid4(), DAY, DAY + timedelta(days=1))


def test_a_healthy_read_is_current() -> None:
    f = Findings()
    assert seam(Read(f, False), f)["eligibility"]["status"] == "CURRENT"


def test_a_selection_committed_during_the_read_is_never_current() -> None:
    class Moving(Findings):
        calls = 0

        def match_state(self, t, s, a, window_start):
            self.calls += 1
            out = super().match_state(t, s, a, window_start)
            if self.calls > 3:  # the after-read sees the newer selection seq 6, already matched by a fast pass
                out.update(window_selection_seq=6, matched_through_selection_seq=6, matched=True)
            return out

    f = Moving()
    e = seam(Read(f, False), f)["eligibility"]
    assert e["status"] == "STALE_PROJECTION" and e["stage"] == "S4"
    assert "SELECTION_MOVED_DURING_READ" in e["reasons"]


def test_eligibility_statuses_and_db_time_schedule_thresholds() -> None:
    f = Findings()
    assert seam(Read(f, False, "FAILED", selection=False), f)["eligibility"]["status"] == "FAILED"
    assert seam(Read(f, False, "UNASSESSED", selection=False), f)["eligibility"]["status"] == "UNASSESSED"
    assert seam(Read(f, False, "PENDING", selection=False), f)["eligibility"]["status"] == "PENDING"
    stopped = seam(Read(f, False), f, Schedule(heartbeat_age=301))["eligibility"]
    assert stopped["status"] == "STALE_PROJECTION" and stopped["reasons"] == ["SCHEDULE_STOPPED"]
    site = seam(Read(f, False), f, Schedule(completed_age=901))["eligibility"]
    assert site["stage"] == "SCHEDULE" and "SITE_VISIT_STALE" in site["reasons"]  # Q1: Site head required too


def test_health_uses_the_supplied_db_time_not_the_host_clock() -> None:
    th = HealthThresholds()
    beat = {"heartbeat_at": NOW - timedelta(seconds=10), "claim_token": None}
    assert environment_health(beat, NOW, th)["state"] == "IDLE"
    # The same head read against a DB time far ahead of the heartbeat is STOPPED, whatever the host clock says.
    assert environment_health(beat, NOW + timedelta(hours=1), th)["state"] == "STOPPED"
    head = {"last_completed_at": NOW, "last_failed_at": None, "claim_token": uuid4(),
            "lease_until": NOW - timedelta(seconds=1), "claimed_at": NOW - timedelta(minutes=10)}
    assert "SITE_CLAIM_STALE" in {o["code"] for o in site_observation(head, NOW, th)}


class Worker:
    def __init__(self) -> None:
        self.now = "unset"

    def run(self, tenant_id, site_id, limit, now=None):
        from assetops_backend.financials.recompute import RunReport

        self.now = now
        return RunReport(tenant_id, site_id, True, now or NOW, [], deferred=0, backlog=0)


def test_the_one_off_runner_uses_db_time_or_reports_an_override(capsys) -> None:
    prices = SimpleNamespace(site_scope=lambda tenant, code: ("KOBO-001", uuid4(), uuid4()))
    db = NOW + timedelta(minutes=7)
    w = Worker()
    assert consequence_main(["run", "--tenant", "demo", "--site", "KOBO-001"], worker=w, prices=prices,
                            db_clock=lambda: db) == 0
    assert w.now == db
    assert json.loads(capsys.readouterr().out.splitlines()[-1])["now_source"] == "database"
    w = Worker()
    assert consequence_main(["run", "--tenant", "demo", "--site", "KOBO-001", "--now", "2026-10-14T13:00:00Z"],
                            worker=w, prices=prices, db_clock=lambda: db) == 0
    assert w.now == datetime(2026, 10, 14, 13, tzinfo=UTC)
    assert json.loads(capsys.readouterr().out.splitlines()[-1])["now_source"] == "override"


def _seam_with_finding(gate_state: str, schedule: Schedule | None = None, consequence_state: str = "CURRENT"):
    class OneFinding(Findings):
        def findings_over(self, t, s, lo, hi):
            return [{"finding_id": uuid4(), "revision_id": uuid4(), "lifecycle": "OPEN", "episode_start": DAY,
                     "episode_end": DAY + timedelta(hours=1)}]

    gate = {"state": gate_state, "version": "money-eligibility-1", "latest_finding_revision_id": "rev-1",
            "series_limits": [], "pending_reasons": []}
    reader = SimpleNamespace(read=lambda *a, **k: {
        "currentness": {"state": consequence_state, "reasons": [], "pending_work": []},
        "consequence_selection": {"head_consequence_revision_id": "c1"}, "money_eligibility": gate})
    f = OneFinding()
    consequences = SimpleNamespace(pending_work=lambda t, s: [])
    out = UpstreamCurrentness(schedule or Schedule(), Read(f, False), f, consequences, reader,
                              analytic_id="dispatch").window(uuid4(), uuid4(), DAY, DAY + timedelta(days=1))
    return out["findings"][0], gate


def test_a_stopped_schedule_keeps_the_raw_gate_eligible_and_blocks_the_amount_with_a_named_reason() -> None:
    f, gate = _seam_with_finding("ELIGIBLE", Schedule(heartbeat_age=301))
    assert f["money_eligibility"] == gate and f["money_eligibility"]["state"] == "ELIGIBLE"
    assert f["upstream_status"] == {"status": "BLOCKED", "reasons": [{"stage": "SCHEDULE", "code": "SCHEDULE_STOPPED"}]}
    assert f["current_amount_permitted"] is False


def test_an_amount_is_permitted_only_when_the_gate_is_eligible_and_upstream_is_current() -> None:
    ok, _ = _seam_with_finding("ELIGIBLE")
    assert ok["upstream_status"]["status"] == "CURRENT" and ok["current_amount_permitted"] is True
    for state in ("WITHHELD_GENERATOR_SERIES", "PENDING_REASSESSMENT"):
        f, _ = _seam_with_finding(state)
        assert f["money_eligibility"]["state"] == state  # never rewritten
        assert f["upstream_status"]["status"] == "CURRENT" and f["current_amount_permitted"] is False
    stale, _ = _seam_with_finding("ELIGIBLE", consequence_state="STALE")
    assert stale["current_amount_permitted"] is False
    assert stale["upstream_status"]["reasons"] == [{"stage": "CONSEQUENCE", "code": "CONSEQUENCE_STALE"}]
