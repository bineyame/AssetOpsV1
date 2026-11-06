"""QW-2 (design proposal §14b): reuse inside one request. No database.

CH6b1-R Q2/Q3: the OUT-W window choice (and with it the QW-2 estate window batch) is deleted, so the outcome summary
reads no estate rows at all; a batched or failing estate gives the same response as a per-Site one."""
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
        self.single = 0  # selected-window reads, one Site per call (CH6b1-R3: the only estate read a board may make)
        self.readiness = 0  # estate evidence-readiness reads: deleted (CH-5a1 A4), must stay 0

    def site_readiness(self, t, code, lo, hi, known_at=None):
        self.readiness += 1
        return {"KOBO-001": "FULL", "COLD-LAB-001": "LIMITED", "EV-LAB-001": "NONE"}.get(code) + f"@{lo:%d}-{hi:%d}"

    def site_selected_windows(self, t, code, lo, hi, known_at=None):
        self.single += 1
        if code == "COLD-LAB-001":
            return [_win(datetime(2026, 10, 28, 3, tzinfo=UTC), datetime(2026, 10, 28, 9, tzinfo=UTC))]
        return [] if code == "EV-LAB-001" else None



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
    # sides), never the estate, so no readiness batch; the estate serves only the cold/EV windows (CH-5a2b R1: the
    # mini Finding and Action rows come from the ChainReader).
    assert seen == expected_seen and [n for n, _ in seen] == ["readiness_of", "readiness_of"]
    # CH6b1-R Q2/Q3: the OUT-W window choice and its QW-2 estate batch are deleted; the summary reads no estate
    # windows (cold/EV are PERIOD), and the one batched read is the chain snapshot read (`test_ch6b_estate_chain`).
    # CH6b1-R3: the cold/EV rows read their contained event windows: per Site on the plain estate (cold + EV = 2),
    # one batch on the batched one (no per-Site call). No readiness read on either.
    assert plain.single == 2 and many.single == 0 and many.snapshots == 0 and many.batches == 1
    assert plain.readiness == 0 and many.readiness == 0
    cold = next(s for s in got["sites"] if s["site_code"] == "COLD-LAB-001")
    assert cold["window_basis"] == read.WINDOW_BASIS_PERIOD


def test_failed_estate_never_reaches_the_summary(monkeypatch, caplog) -> None:
    sites = [KOBO, COLD, EV]
    expected = SiteOutcomeBoardService(BoardServices(estate=SingleEstate())).summary(sites, LO, HI)
    failing = ManyEstate(fail=True)
    got = SiteOutcomeBoardService(BoardServices(estate=failing)).summary(sites, LO, HI)
    # the refused batch is not fatal: the summary falls back to the per-Site window reads (counted + logged) and
    # returns the same response; no estate readiness read happens.
    assert got == expected and failing.batches == 1 and failing.single == 2 and failing.readiness == 0


def test_a_board_reads_no_estate_rows() -> None:
    leftover = SingleEstate()
    SiteOutcomeBoardService(BoardServices(estate=leftover)).board(COLD, lo=LO, hi=HI)
    # CH-5a2b R1: a board reads no estate ROWS and no readiness. CH6b1-R3: the one allowed estate read is the
    # cold/EV contained-window read (exactly one Site, the board's own).
    assert leftover.single == 1 and leftover.readiness == 0
