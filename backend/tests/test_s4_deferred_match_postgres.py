"""S4 deferred-match fix on real Postgres: a window the matcher deferred never reads as matched.

`finding_episode.plan` skips a group whose 20-minute continuity margin touches a window that is not CURRENT. Before
the fix the pass was still recorded at the Site-wide selection seq, so `match_state` called the deferring day
matched: the S5-01 Overview read freshness CURRENT with a false ABSENT (scenario A) or the wrong chosen Finding
(scenario B), and the S4-04 phase-1 index could claim CURRENT with zero rows (H1, same sequence as A). Sources:
`.agent/S5-01-deferred-cluster-check.md`, `.agent/S4-04-phase-1-review.md` H1.

Each scenario walks the real S2 ingestion, S3 worker and S4 matcher (`CaseRunner`), reads the production S5 Overview
(`build_site_overview_read`) and the S4 `match_state` / S4-02d upstream seam, and proves the deferral reads
pending, then settles correctly once the neighbour is CURRENT again, retried by the scheduled tick on its own.
Requires ASSETOPS_TEST_DATABASE_URL.
"""

from __future__ import annotations

import os
from datetime import date, datetime, timedelta, timezone

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    import test_s4_finding_store_postgres as finding_cases
    from test_lr01_money_eligibility_postgres import _release_connections  # noqa: F401
    from test_s1_bindings_postgres import engine, store  # noqa: F401
    from test_s4_schedule_tick_postgres import FAST, make_tick

    from assetops_backend.evidence.adapters.postgres_evidence_ledger import PostgresEvidenceLedger
    from assetops_backend.financials.adapters.postgres_assumption_store import PostgresAssumptionStore
    from assetops_backend.financials.adapters.postgres_consequence_store import PostgresConsequenceStore
    from assetops_backend.financials.composition import CONSEQUENCE_UNAVAILABLE
    from assetops_backend.financials.recompute import ConsequenceRecomputeWorker
    from assetops_backend.scheduling.health import HealthThresholds
    from assetops_backend.scheduling.tick import TickLimits
    from assetops_backend.site_overview.composition import build_site_overview_read

UTC = timezone.utc
# Source days and decision instants lie in the real past, so the scheduled tick's DB-clock S3 stage sees them.
D, D1 = date(2026, 10, 12), date(2026, 10, 13)
START_D, START_D1 = (datetime(x.year, x.month, x.day, tzinfo=UTC) for x in (D, D1))
NIGHT = {"from": "2026-10-12T23:10:00Z", "to": "2026-10-12T23:45:00Z", "pv": "40", "dis": "20", "soc": "80",
         "stop_before": True}  # still RUNNING at 23:45: its margin reaches 00:05 on D+1
NEXT_DAY = {"from": "2026-10-13T10:00:00Z", "to": "2026-10-13T10:30:00Z", "pv": "40", "dis": "20", "soc": "80",
            "stop_before": True, "stop_after": True}
LATE_NEXT_DAY = {"from": "2026-10-13T12:00:00Z", "to": "2026-10-13T12:20:00Z", "pv": "40", "dis": "20",
                 "soc": "80", "stop_before": True, "stop_after": True}
MORNING = {"from": "2026-10-12T08:00:00Z", "to": "2026-10-12T08:30:00Z", "pv": "40", "dis": "20", "soc": "80",
           "stop_before": True, "stop_after": True}


class Harness:
    def __init__(self, store, engine, monkeypatch) -> None:  # noqa: F811
        monkeypatch.setattr(finding_cases, "SETUP_AT", datetime(2026, 10, 10, 12, tzinfo=UTC))
        self.r = finding_cases.CaseRunner(store, engine)
        self.tick, _ = make_tick(TickLimits(**FAST))
        # One early tick keeps the schedule observation healthy for the whole walk without doing its work.
        big = HealthThresholds(stop_after_seconds=10**7, site_stop_after_seconds=10**7)
        self.ledger = PostgresEvidenceLedger(URL)
        self.overview = build_site_overview_read(URL, self.ledger, big, environment=self.tick.environment)
        self.prices, self.cstore = PostgresAssumptionStore(URL), PostgresConsequenceStore(URL)
        self.worker = ConsequenceRecomputeWorker(self.cstore, self.prices, CONSEQUENCE_UNAVAILABLE)
        self.decided = datetime(2026, 10, 14, 8, tzinfo=UTC)

    def close(self) -> None:
        self.overview.dispose() if hasattr(self.overview, "dispose") else None
        self.prices.dispose()
        self.cstore.dispose()
        self.r.findings._engine and self.r.findings._engine.dispose()

    def deliver(self, *blocks: dict) -> None:
        self.decided += timedelta(minutes=10)
        self.r.step({"do": "deliver", "decided": self.decided.strftime("%Y-%m-%dT%H:%M:%SZ"),
                     "blocks": list(blocks)})

    def assess(self) -> None:
        self.r.step({"do": "assess"})

    def settle(self) -> None:
        assert all(o.succeeded for o in self.worker.run_pending(self.r.tenant, self.r.site))

    def ticked(self) -> None:
        report = self.tick.tick()
        assert report.outcome == "COMPLETED", report.as_json()

    def view(self) -> dict:
        return self.overview.read("KOBO-001", self.r.tenant, self.r.site, D, access_basis="test",
                                  source_open=True, source_reason="test")

    def match_state(self, start: datetime) -> dict:
        return self.r.findings.match_state(self.r.tenant, self.r.site, "dispatch", start)


def pending(h: Harness, body: dict) -> None:
    """The deferral reads as S4 work outstanding: never CURRENT, never ABSENT, never a ruled Finding choice."""
    assert body["freshness"]["state"] != "CURRENT", body["freshness"]
    assert "MATCH_PENDING" in str(body["freshness"]["reasons"]), body["freshness"]
    assert body["money"]["state"] != "ABSENT", body["money"]
    ms = h.match_state(START_D)
    assert ms["match_deferred"] is True and ms["matched"] is False, ms


@pytest.fixture()
def h(store, engine, monkeypatch):  # noqa: F811
    harness = Harness(store, engine, monkeypatch)
    yield harness
    harness.close()


def test_scenario_a_deferred_edge_cluster_is_pending_not_absent(h) -> None:
    """Scenario A / S4-04 H1: D+1 matched; D gets a Candidate run 23:10-23:45; late D+1 evidence makes D+1 stale and
    the matcher runs (planned 0). Formerly CURRENT / no Finding / ABSENT; now MATCH_PENDING until the rematch."""
    h.deliver(NEXT_DAY)
    h.assess()
    h.r.match()
    h.ticked()

    h.deliver(NIGHT)
    h.assess()
    assert h.view()["freshness"]["state"] != "CURRENT"  # not matched yet (seq moved)

    h.deliver(LATE_NEXT_DAY)  # D+1 now STALE_PROJECTION with a live recompute job
    out = h.r.match()
    assert out.planned == 0
    assert out.window_statuses == {D.isoformat(): "CURRENT", D1.isoformat(): "STALE_PROJECTION"}
    assert set(out.deferred_windows) == {START_D, START_D1}
    pass_seq = h.match_state(START_D)["matched_through_selection_seq"]
    assert pass_seq >= h.match_state(START_D)["window_selection_seq"]  # the old reading: "matched"
    body = h.view()
    pending(h, body)
    assert body["known_finding"] is None

    # Form 2: D+1 reassessed, no rematch yet: still pending (D+1's newer selection and D's deferral).
    h.assess()
    body = h.view()
    pending(h, body)
    assert not h.match_state(START_D1)["matched"]

    # The scheduled tick alone retries the deferral (the fence moved) and drains the consequence work.
    h.ticked()
    ms = h.match_state(START_D)
    assert ms["matched"] is True and ms["match_deferred"] is False, ms
    body = h.view()
    assert body["freshness"]["state"] == "CURRENT", body["freshness"]
    assert body["known_finding"]["episode"] == {"start": "2026-10-12T23:10:00Z", "end": "2026-10-12T23:45:00Z"}
    assert body["money"]["state"] != "ABSENT"


def test_scenario_b_deferred_cluster_never_presents_an_earlier_finding_as_current(h) -> None:
    """Scenario B: an existing Finding on D, then a later deferred cluster near midnight. Formerly the earlier
    Finding was the ruled choice under CURRENT; now pending until the rematch picks the greatest-start Finding."""
    h.deliver(MORNING, NEXT_DAY)
    h.assess()
    h.r.match()
    h.settle()
    h.ticked()
    body = h.view()
    assert body["freshness"]["state"] == "CURRENT", body["freshness"]
    morning = body["known_finding"]
    assert morning["episode"]["start"] == "2026-10-12T08:00:00Z"

    h.deliver(NIGHT)
    h.assess()
    h.deliver(LATE_NEXT_DAY)
    out = h.r.match()
    assert set(out.deferred_windows) == {START_D, START_D1}
    h.settle()
    body = h.view()
    pending(h, body)

    # No manual rematch: the scheduled tick reassesses D+1, rematches and settles.
    h.ticked()
    body = h.view()
    assert body["freshness"]["state"] == "CURRENT", body["freshness"]
    assert body["known_finding"]["episode"]["start"] == "2026-10-12T23:10:00Z"
    assert body["known_finding"]["several_intersect"] is True
    assert h.match_state(START_D)["matched"] is True


def test_a_neighbour_that_stays_stale_keeps_the_window_pending_across_passes(h) -> None:
    """Fail closed: a later pass under the same deferral (no change to the neighbour) still records it; a pass
    with nothing deferred clears it. Old passes stay as they were (append-only)."""
    h.deliver(NEXT_DAY)
    h.assess()
    h.r.match()
    h.deliver(NIGHT)
    h.assess()
    h.deliver(LATE_NEXT_DAY)
    first = h.r.match()
    second = h.r.match()  # same fence, recorded again: still deferred
    assert set(first.deferred_windows) == set(second.deferred_windows) == {START_D, START_D1}
    assert h.match_state(START_D)["match_deferred"] is True
    h.assess()
    third = h.r.match()
    assert third.deferred_windows == () and h.match_state(START_D)["matched"] is True
    with h.r.engine.connect() as c:
        from sqlalchemy import text
        rows = c.execute(text("SELECT cardinality(deferred_window_starts) FROM finding_match_pass "
                              "WHERE site_id = :s ORDER BY completed_at"), {"s": h.r.site}).scalars().all()
    assert rows[-3:] == [2, 2, 0]
