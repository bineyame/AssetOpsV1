"""W4-02 q7 rulings 2, 3 and 5 (pure): the tick's MINI stage bounds, order, failure retention and lost-claim stop;
mini work in Site selection; the reconcile hour set across DST; and the `run-pending` CLI token.

The stage runner and schedule store are recording fakes, so these prove the tick's sequencing without a database;
`test_w402_mini_stage_postgres.py` proves the real stage child against PostgreSQL.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from assetops_backend.mini_depth import worker as worker_module
from assetops_backend.mini_depth.worker import RUN_PENDING_COMMAND, MiniDepthWorker, hours_within
from assetops_backend.scheduling.stages import MINI_JOB_LEASE_SECONDS, STAGES
from assetops_backend.scheduling.tick import ScheduleTick, SiteResult, TickLimits, select_sites

UTC = timezone.utc
ROOT = Path(__file__).resolve().parents[2]
T, S = UUID(int=1), UUID(int=2)


class FakeStore:
    def __init__(self, lose: str | None = None) -> None:
        self.lose, self.calls = lose, []

    def claim_site(self, t, s, token, owner, lease):
        self.calls.append(("claim", lease))
        return {"claimed": True, "matched_fence": None, "matched_version": None, "consecutive_failures": 0}

    def set_stage(self, t, s, token, stage):
        self.calls.append(("stage", stage))
        return stage != self.lose

    def record_s3(self, *a):
        self.calls.append(("record_s3", a[3:]))
        return True

    def record_mini(self, *a):
        self.calls.append(("record_mini", a[3:]))
        return True

    def record_s4(self, *a, **k):
        self.calls.append(("record_s4", a[3]))
        return True

    def record_consequence(self, *a):
        self.calls.append(("record_consequence", a[3:]))
        return True

    def db_now(self):
        return datetime(2026, 10, 21, tzinfo=UTC)

    def release_site(self, t, s, token, *, failure, backoff_seconds=0):
        self.calls.append(("release", failure))
        return True


class FakeRunner:
    def __init__(self, results: dict[str, dict] | None = None) -> None:
        self.results, self.calls = results or {}, []

    def run(self, stage, args, seconds):
        self.calls.append((stage, args, seconds))
        default = {"s3": {"code": "OK", "processed": 1, "deferred": 0},
                   "mini": {"code": "OK", "processed": 4, "deferred": 6, "failed": 1},
                   "s4": {"code": "SKIPPED_UNCHANGED_FENCE"},
                   "consequence": {"code": "OK", "selected": 0, "deferred": 0}}[stage]
        return self.results.get(stage, default)


def visit(runner: FakeRunner, store: FakeStore) -> SiteResult:
    limits = TickLimits()
    site = SiteResult(T, S, "MG", "EVIDENCE")
    ScheduleTick(store, runner, limits, environment="test")._site(site, uuid4())
    return site


def test_limits_bound_the_mini_stage() -> None:
    limits = TickLimits()
    assert (limits.mini_jobs_per_site, limits.mini_seconds) == (10, 120)
    assert (limits.statement_timeout_ms, limits.lock_timeout_ms) == (30_000, 5_000)
    assert limits.site_lease_seconds == 480
    assert MINI_JOB_LEASE_SECONDS == 300 == MiniDepthWorker(None, None).lease.total_seconds()
    for bad in (0, -1, 300, 301):
        with pytest.raises(ValueError, match="MINI stage bound"):
            TickLimits(mini_seconds=bad)
    with pytest.raises(ValueError, match="at least 1"):
        TickLimits(mini_jobs_per_site=0)
    with pytest.raises(ValueError, match="statement timeout"):  # mini_seconds is one of the stage bounds
        TickLimits(mini_seconds=20, statement_timeout_ms=25_000)
    assert TickLimits(mini_seconds=299).mini_seconds == 299


def test_stage_order_budget_and_counts() -> None:
    runner, store = FakeRunner(), FakeStore()
    site = visit(runner, store)
    assert [c[0] for c in runner.calls] == ["s3", "mini", "s4", "consequence"]
    assert [c[1] for c in store.calls if c[0] == "stage"] == ["S3", "MINI", "S4", "CONSEQUENCE"]
    _, args, seconds = runner.calls[1]
    assert args == {"tenant_id": str(T), "site_id": str(S), "limit": 10} and seconds == 120
    assert ("record_mini", (4, 6, 1)) in store.calls and ("claim", 480) in store.calls
    assert site.result == "COMPLETED" and site.failure is None and site.stages["mini"]["processed"] == 4
    assert "mini" in STAGES


@pytest.mark.parametrize("code", ["TIMEOUT", "FAILED", "UNAVAILABLE"])
def test_mini_failure_is_retained_and_later_stages_still_run(code) -> None:
    runner, store = FakeRunner({"mini": {"code": code, "error": "child died"}}), FakeStore()
    site = visit(runner, store)
    assert [c[0] for c in runner.calls] == ["s3", "mini", "s4", "consequence"]
    assert not [c for c in store.calls if c[0] == "record_mini"]  # no invented counts
    assert site.failure == ("MINI", code, "child died") and site.result == "FAILED"
    assert store.calls[-1] == ("release", ("MINI", code, "child died"))
    # An earlier S3 failure stays the first failure.
    runner = FakeRunner({"s3": {"code": "FAILED", "error": "s3"}, "mini": {"code": code, "error": "mini"}})
    assert visit(runner, FakeStore()).failure == ("S3", "FAILED", "s3")


@pytest.mark.parametrize("lose,ran", [("MINI", ["s3"]), ("S4", ["s3", "mini"])])
def test_lost_site_claim_stops_before_the_next_stage(lose, ran) -> None:
    runner, store = FakeRunner(), FakeStore(lose=lose)
    site = visit(runner, store)
    assert [c[0] for c in runner.calls] == ran and site.result == "CLAIM_LOST" and site.failure[0] == lose
    assert not [c for c in store.calls if c[0] == "release"]


def test_mini_work_keeps_a_site_selected_and_reported() -> None:
    """q8 ruling 2: PENDING/LEASED mini work keeps a (decommissioned) Site scheduled; FAILED-only work does not."""
    a, b, c, d, e = ((UUID(int=10), UUID(int=n)) for n in (11, 12, 13, 14, 15))
    site = lambda k, code, life, ev: {"tenant_id": k[0], "site_id": k[1], "site_code": code,  # noqa: E731
                                      "lifecycle": life, "has_evidence": ev, "enrolled": False}
    inventory = [site(a, "ONLY-MINI", "ACTIVE", False), site(b, "GONE", "DECOMMISSIONED", True),
                 site(c, "IDLE", "ACTIVE", False), site(d, "GONE-FAILED", "DECOMMISSIONED", True),
                 site(e, "GONE-LEASED", "DECOMMISSIONED", True)]
    mini = [{"id": uuid4(), "tenant_id": k[0], "site_id": k[1], "domain": "mini_fuel", "status": st,
             "last_error": err} for k, st, err in ((a, "PENDING", None), (b, "PENDING", None),
                                                   (d, "FAILED", "boom"), (e, "LEASED", None))]
    selected, excluded, not_selected = select_sites(
        {"inventory": inventory, "live_jobs": [], "live_mini_jobs": mini, "pending_work_sites": []})
    assert [(s.site_code, s.reason) for s in selected] == [("ONLY-MINI", "EXCLUDED_WITH_WORK"),
                                                          ("GONE", "EXCLUDED_WITH_WORK"),
                                                          ("GONE-LEASED", "EXCLUDED_WITH_WORK")]
    assert not_selected == 2  # IDLE and the FAILED-only decommissioned Site
    assert [(e["site_code"], e["lifecycle"], [j["status"] for j in e["live_mini_jobs"]], e["live_jobs"])
            for e in excluded] == [("ONLY-MINI", "ACTIVE", ["PENDING"], []),
                                   ("GONE", "DECOMMISSIONED", ["PENDING"], []),
                                   ("GONE-LEASED", "DECOMMISSIONED", ["LEASED"], [])]
    # A FAILED row of a Site with no import record is not work either.
    orphan = {"id": uuid4(), "tenant_id": UUID(int=10), "site_id": UUID(int=99), "domain": "mini_fuel",
              "status": "FAILED", "last_error": "boom"}
    assert select_sites({"inventory": [], "live_jobs": [], "live_mini_jobs": [orphan],
                         "pending_work_sites": []}) == ([], [], 0)


def _starts(windows) -> list[str]:
    return [w.start.strftime("%H:%M") + "-" + w.end.strftime("%H:%M") for w in windows]


def test_reconcile_hours_partial_boundary_and_dst() -> None:
    """q7 R3: first-occurrence local hours wholly inside [from, to); a repeated hour once, a nonexistent hour never."""
    ny = "America/New_York"
    # Fall back on 1 Nov 2026: local 01:00 occurs at 05:00Z (EDT) and again at 06:00Z (EST); only the first counts.
    fall = hours_within(datetime(2026, 11, 1, 4, 30, tzinfo=UTC), datetime(2026, 11, 1, 8, 0, tzinfo=UTC), ny)
    assert _starts(fall) == ["05:00-06:00", "07:00-08:00"]  # 04:30-05:00 partial; 06:00Z repeated hour skipped
    # Spring forward on 8 Mar 2026: local 02:00 does not exist.
    spring = hours_within(datetime(2026, 3, 8, 5, 0, tzinfo=UTC), datetime(2026, 3, 8, 9, 15, tzinfo=UTC), ny)
    assert _starts(spring) == ["05:00-06:00", "06:00-07:00", "07:00-08:00", "08:00-09:00"]
    assert [w.start.astimezone(__import__("zoneinfo").ZoneInfo(ny)).hour for w in spring] == [0, 1, 3, 4]
    assert all(w.end - w.start == timedelta(hours=1) for w in fall + spring)


def test_run_pending_cli_token_and_reconcile(monkeypatch) -> None:
    """q7 R4: the CLI token is spelled from the method; `run-pending --limit 1` calls `run_pending(1)`."""
    assert RUN_PENDING_COMMAND == "run" + "-pending"
    calls = []

    class Fake:
        store = type("S", (), {"dispose": lambda self: calls.append(("dispose",))})()

        def run_pending(self, limit):
            calls.append(("run_pending", limit))
            return []

        def reconcile(self, site, start, end):
            calls.append(("reconcile", site, start, end))
            return []

    monkeypatch.setenv("DATABASE_URL", "postgresql://unused")
    monkeypatch.setattr(worker_module, "build_worker", lambda url: Fake())
    assert worker_module.main([RUN_PENDING_COMMAND, "--limit", "1"]) == 0
    assert calls == [("run_pending", 1), ("dispose",)]
    calls.clear()
    assert worker_module.main(["reconcile", "--site", "MG-W402-001", "--from", "2026-10-06T00:00:00Z",
                               "--to", "2026-10-07T00:00:00Z"]) == 0
    assert calls == [("reconcile", "MG-W402-001", datetime(2026, 10, 6, tzinfo=UTC), datetime(2026, 10, 7, tzinfo=UTC)),
                     ("dispose",)]
    assert "reconcile" != RUN_PENDING_COMMAND


def test_no_second_timer_or_install_path() -> None:
    """Closure 4 S7: the tick is the only scheduler of mini work; no mini installer or periodic task exists."""
    assert not list((ROOT / "tools").glob("install-mini*"))
    units = sorted(p.name for p in (ROOT / "backend" / "deploy").rglob("*") if p.is_file())
    assert units == ["assetops-schedule-tick@.service", "assetops-schedule-tick@.timer"]
    for name in units:
        body = next((ROOT / "backend" / "deploy").rglob(name)).read_text(encoding="utf-8")
        assert "mini" not in body and "scheduling.run" in body or name.endswith(".timer"), name
