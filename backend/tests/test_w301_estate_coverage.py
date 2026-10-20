"""W3-01 q10 ruling 2: the windowed (cold/EV) coverage states that the golden replay does not persist.

UNIT PROOF ONLY. `StaleProbe`/`OpenJobs` below are a test-only `EstateSnapshot` double with one exact selected cold
window; nothing here is persisted replay coverage. STALE_SOURCE is also proven on persisted rows by
`test_w203_cold_reads_postgres.py` (`currentness_state(... latest_probe_at=TO-25 minutes)`); the real pending replay
stays in `test_w301_estate_index_postgres.py`. `LEASED` is a stored job status, never an estate coverage state.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from assetops_backend.estate import coverage

T, S = "00000000-0000-4000-8000-00000000a301", "00000000-0000-4000-8000-00000000b301"
DAY = datetime(2026, 10, 6, tzinfo=timezone.utc)
K = DAY + timedelta(hours=20)
WATERMARK = DAY + timedelta(hours=10)


class WindowSnapshot:
    """A live (non-historical, no cursor) estate snapshot with one exact selected cold window."""

    def __init__(self, probe_fresh: bool = True, jobs: tuple[str, ...] = ()) -> None:
        self.read_at, self.historical, self.continuation = K, False, False
        self.basis_historical = False
        self.probe_fresh, self.jobs = probe_fresh, list(jobs)

    def evidence_cutoff(self, t, s, k):
        return WATERMARK

    def selected_windows(self, t, s, domain, from_, to, cutoff, k):
        assert domain == coverage.COLD and (from_, to) == (DAY, DAY + timedelta(days=1))
        return [{"selection_id": "sel-1", "seq": 1, "selected_at": WATERMARK, "state": coverage.CURRENT,
                 "window_start": DAY + timedelta(hours=8), "window_end": DAY + timedelta(hours=9),
                 "probe_fresh": self.probe_fresh, "assessment_revision_ids": ["a-1"], "evidence_ids": ["e-1"],
                 "findings": []}]

    def open_jobs(self, t, s, domain, from_, to, k):
        return list(self.jobs)


def site(snapshot: WindowSnapshot) -> dict:
    return coverage.site_coverage(snapshot, T, S, coverage.COLD, DAY, DAY + timedelta(days=1), K)


def test_windowed_stale_probe() -> None:
    cov = site(WindowSnapshot(probe_fresh=False))
    assert cov["state"] == "STALE_SOURCE" and cov["source_freshness"] == "STALE"
    assert cov["job_state"] == "SETTLED" and cov["selection_id"] == "sel-1"


def test_windowed_leased_and_failed_jobs() -> None:
    leased = site(WindowSnapshot(jobs=("LEASED",)))
    failed = site(WindowSnapshot(jobs=("FAILED",)))
    assert leased["state"] == failed["state"] == "PENDING_RECOMPUTE"
    assert leased["job_state"] == "PENDING" and failed["job_state"] == "FAILED"
    assert "LEASED" not in {leased["state"], failed["state"]}
