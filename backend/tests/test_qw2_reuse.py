"""QW-2 (design proposal §14b): reuse inside one request. No database.

The outcome summary's batched estate reads give a response equal to the per-Site reads, serve every Site's estate port
on an exact argument match (zero single-Site calls), and fall back to the per-Site reads when a batch fails or the
estate has no batched methods."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from assetops_backend.site_outcomes import read
from assetops_backend.site_outcomes.mini import Reads
from assetops_backend.site_outcomes.read import BoardServices, SiteOutcomeBoardService, SiteRef

UTC = timezone.utc
T = uuid4()
KOBO = SiteRef(T, uuid4(), "KOBO-001", "Kobo", "MINIGRID", "Africa/Nairobi")
COLD = SiteRef(T, uuid4(), "COLD-LAB-001", "GreenHarvest", "COLDCHAIN", None)
EV = SiteRef(T, uuid4(), "EV-LAB-001", "Charge", "EV_CHARGING", None)
ODD = SiteRef(T, uuid4(), "ODD-1", "Odd", "UNKNOWN_TYPE", None)
LO, HI = datetime(2026, 10, 25, tzinfo=UTC), datetime(2026, 11, 1, tzinfo=UTC)


# ---------------------------------------------------------------- summary batching

def _win(lo, hi, seq=1):
    return {"window_start": lo, "window_end": hi, "selected_at": hi, "seq": seq, "selection_id": f"s{seq}"}


class SingleEstate:
    """Deterministic per-Site estate answers keyed on the exact arguments; counts every single-Site call."""

    def __init__(self) -> None:
        self.single = 0

    def site_readiness(self, t, code, lo, hi, known_at=None):
        self.single += 1
        return {"KOBO-001": "FULL", "COLD-LAB-001": "LIMITED", "EV-LAB-001": "NONE"}.get(code) + f"@{lo:%d}-{hi:%d}"

    def site_selected_windows(self, t, code, lo, hi, known_at=None):
        self.single += 1
        if code == "COLD-LAB-001":
            return [_win(datetime(2026, 10, 28, 3, tzinfo=UTC), datetime(2026, 10, 28, 9, tzinfo=UTC))]
        return [] if code == "EV-LAB-001" else None

    def site_work_rows(self, t, code, day_lo, day_hi, work_lo, work_hi, known_at=None):
        self.single += 1
        return {"site_cov": {"state": "COMPLETE"}, "findings": [], "actions": []}


class ManyEstate(SingleEstate):
    def __init__(self, fail: bool = False) -> None:
        super().__init__()
        self.fail, self.snapshots, self.batches = fail, 0, 0

    def read_snapshot(self, work):
        self.snapshots += 1
        return work(object())

    def _batch(self):
        self.batches += 1
        if self.fail:
            raise RuntimeError("batch refused")
        before = self.single
        return before

    def site_selected_windows_many(self, t, codes, lo, hi, known_at=None, *, snap=None):
        before = self._batch()
        out = {c: SingleEstate.site_selected_windows(self, t, c, lo, hi, known_at) for c in codes}
        self.single = before
        return out

    def site_readiness_many(self, t, windows, known_at=None, *, snap=None):
        before = self._batch()
        out = {c: SingleEstate.site_readiness(self, t, c, a, b, known_at) for c, (a, b) in windows.items()}
        self.single = before
        return out

    def site_work_rows_many(self, t, windows, known_at=None, *, snap=None):
        before = self._batch()
        out = {c: SingleEstate.site_work_rows(self, t, c, *w, known_at) for c, w in windows.items()}
        self.single = before
        return out


def _readiness_spy(monkeypatch) -> list:
    """The readiness and estate values each board's composer received (the batched value must reach the board).
    The mini, cold and EV composers share the one `Reads` class."""
    seen: list = []
    real = Reads.call

    def call(self, name, fn, *args):
        out = real(self, name, fn, *args)
        if name in ("evidence_readiness", "readiness_of", "estate"):
            seen.append((name, out))
        return out

    monkeypatch.setattr(Reads, "call", call)
    return seen


@pytest.mark.parametrize("known_at", [None, datetime(2026, 11, 2, tzinfo=UTC)])
def test_summary_equal_with_and_without_batching_and_every_port_served(monkeypatch, known_at) -> None:
    sites = [KOBO, COLD, EV, ODD]
    seen = _readiness_spy(monkeypatch)
    plain = SingleEstate()
    expected = SiteOutcomeBoardService(BoardServices(estate=plain)).summary(sites, LO, HI, known_at)
    expected_seen = list(seen)
    seen.clear()
    many = ManyEstate()
    got = SiteOutcomeBoardService(BoardServices(estate=many)).summary(sites, LO, HI, known_at)
    assert got == expected
    # CH-5a1 §A4: readiness is `readiness_of` on the ChainReader (no chain reader here: a failed read, None on both
    # sides), never the estate, so no readiness batch; the estate serves the windows and the mini work rows.
    assert seen == expected_seen and [n for n, _ in seen] == ["estate", "readiness_of", "readiness_of"]
    assert plain.single == 4  # 3 windows (ODD too) + 1 work rows, one Site at a time
    assert many.single == 1 and many.snapshots == 1 and many.batches == 2  # only ODD, which has no board
    cold = next(s for s in got["sites"] if s["site_code"] == "COLD-LAB-001")
    assert cold["window_basis"] == read.WINDOW_BASIS_EVENT  # the batched window choice was used


def test_failed_batch_falls_back_to_the_per_site_reads(monkeypatch, caplog) -> None:
    sites = [KOBO, COLD, EV]
    expected = SiteOutcomeBoardService(BoardServices(estate=SingleEstate())).summary(sites, LO, HI)
    failing = ManyEstate(fail=True)
    got = SiteOutcomeBoardService(BoardServices(estate=failing)).summary(sites, LO, HI)
    assert got == expected and failing.single == 3  # CH-5a1: 2 windows (cold, EV) + 1 work rows (no estate readiness)
    assert "fell back to per-Site reads (RuntimeError)" in caplog.text


def test_prefetch_is_request_local_and_cleared_after_the_summary() -> None:
    SiteOutcomeBoardService(BoardServices(estate=ManyEstate())).summary([KOBO], LO, HI)
    assert read._PREFETCH.get() is None
    leftover = SingleEstate()
    SiteOutcomeBoardService(BoardServices(estate=leftover)).board(KOBO, day=(HI - timedelta(days=1)).date())
    assert leftover.single == 1  # a board outside a summary reads live (CH-5a1: work rows only, no readiness)
