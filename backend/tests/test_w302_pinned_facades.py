"""W3-02 0c: the pinned cold/EV Site facades' fail-closed pin and cutoff rules (pure; no database).

`ColdSiteReadService.capabilities_on/money_on` and `EvSiteReads.capabilities_on/money_on` accept only an already
pinned estate snapshot; a head recorded after the pinned cutoff is refused, never selected; the default W2 paths
are unchanged.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from assetops_backend.analytics.cold_reads import ColdPinnedLineageUnavailable
from assetops_backend.analytics.cold_site_reads import ColdSiteReadService
from assetops_backend.analytics.ev_reads import EvPinnedLineageUnavailable
from assetops_backend.ev_site_reads import EvSiteReads

T0 = datetime(2026, 10, 6, 8, tzinfo=timezone.utc)
K = T0 + timedelta(hours=6)
EXC = "cold-excursion"
EV = "ev-session/1"


def cold_snap(**over):
    rev = SimpleNamespace(revision_id=uuid4(), evidence_ids=[str(uuid4())])
    snap = {"code": "C", "t": uuid4(), "s": uuid4(), "lo": T0, "hi": T0 + timedelta(hours=1), "known": K - timedelta(hours=1),
            "watermark": K - timedelta(hours=1), "selected": {EXC: rev}, "state": "CURRENT",
            "selection_seqs": {EXC: 7}, "selection_cutoff": K}
    snap.update(over)
    return snap


def head(kind: str, created_at: datetime, group: str = "g1") -> dict:
    return {"id": uuid4(), "finding_revision_id": uuid4(), "episode_revision_id": uuid4(),
            "assessment_revision_id": uuid4(), "kind": kind, "state": "QUANTIFIED", "reason": None,
            "quantity_low": 0, "quantity_high": 3, "quantity_unit": "PRODUCT_HOURS", "overlap_group": group,
            "window_start": T0, "window_end": T0 + timedelta(hours=1), "evidence_ids": [], "source_gate_sha256": "AB",
            "assumption_revision_ids": [], "consequence_basis_sha256": "CD", "created_at": created_at, "limitation": None}


class ColdMoney:
    def __init__(self, heads, pending):
        self.heads, self.pending = heads, pending

    def cold_heads_on(self, c, t, s, ids):
        return list(self.heads)

    def cold_pending_on(self, c, t, s, lo, hi):
        return list(self.pending)


@pytest.mark.parametrize("over", [
    {"selection_cutoff": None}, {"selection_seqs": None}, {"selection_seqs": {"cold-start-response": 1}},
    {"selected": {}}, {"lo": None}, {"known": K + timedelta(seconds=1)},
    {"watermark": K - timedelta(hours=2)}])
def test_cold_facades_refuse_an_unprovable_pin(over) -> None:
    svc = ColdSiteReadService(SimpleNamespace(), ColdMoney([], []))
    for call in (lambda: svc.capabilities_on(None, cold_snap(**over)),
                 lambda: svc.money_on(None, cold_snap(**over), [])):
        with pytest.raises(ColdPinnedLineageUnavailable):
            call()


def test_cold_money_on_refuses_newer_head_and_ignores_later_work() -> None:
    old_exposure, repair = head("PRODUCT_EXPOSURE", K - timedelta(minutes=5)), head("RECORDED_REPAIR", K)
    later_work = {"id": uuid4(), "enqueued_at": K + timedelta(seconds=1), "last_outcome": "FAILED"}
    svc = ColdSiteReadService(SimpleNamespace(), ColdMoney([old_exposure, repair], [later_work]))
    snap = cold_snap()
    got = svc.money_on(None, snap, [{"finding_revision_id": str(old_exposure["finding_revision_id"])}])
    assert got["withheld"] is False and got["hold"] is None  # work enqueued after the cutoff does not withhold
    assert {r["id"]: (r["kind"], r["counted"]) for r in got["consequences"]} == {
        str(old_exposure["id"]): ("PRODUCT_EXPOSURE", True), str(repair["id"]): ("RECORDED_REPAIR", False)}
    assert got["selection_seqs"] == {EXC: 7} and got["assessment_revision_ids"] == {
        EXC: str(snap["selected"][EXC].revision_id)}
    # The default W2 money is unchanged: later work still withholds and no head is refused.
    assert svc._money(None, snap, [{"revision_id": "x"}])["withheld"] is True
    newer = head("PRODUCT_EXPOSURE", K + timedelta(microseconds=1))
    svc = ColdSiteReadService(SimpleNamespace(), ColdMoney([old_exposure, newer], []))
    assert len(svc._money(None, snap, [{"revision_id": "x"}])["heads"]) == 2
    with pytest.raises(ColdPinnedLineageUnavailable, match=str(newer["id"])):
        svc.money_on(None, snap, [{"revision_id": "x"}])


def ev_snap(**over):
    snap = {"code": "E", "t": uuid4(), "s": uuid4(), "lo": T0, "hi": T0 + timedelta(hours=1), "known": K,
            "watermark": K, "state": "CURRENT", "selection_seqs": {EV: 3}, "selection_cutoff": K,
            "selected": {"revision_id": uuid4(), "evidence_ids": ["e1"]}}
    snap.update(over)
    return snap


def ev_row(recorded_at: datetime, n: int) -> dict:
    return {"id": uuid4(), "revision_no": n, "state": "PRICED", "reason": None, "quantity_kwh": 1,
            "tariff_revision_id": uuid4(), "tariff_value": 1, "currency": "USD", "amount": 1, "overlap_group": "g",
            "recorded_at": recorded_at, "tariff_recorded_at": recorded_at, "source_gate": "ok",
            "session_revision_ids": [], "evidence_ids": []}


class EvMoney:
    def __init__(self, history, current):
        self.history, self.current = history, current

    def history_on(self, c, t, s, lo, hi):
        return list(self.history)

    def basis_on(self, c, t, s, lo, hi, sel):
        return object()

    def select_on(self, c, t, s, lo, hi, basis):
        return self.current

    def tariff_on(self, c, t, s, lo, hi):
        return []


def ev_reads(money) -> EvSiteReads:
    return EvSiteReads(SimpleNamespace(), money, derive=lambda basis: SimpleNamespace(basis_sha256="b"))


@pytest.mark.parametrize("over", [
    {"selection_cutoff": None}, {"selection_seqs": None}, {"selection_seqs": {EV: 1, "x": 2}}, {"selected": None},
    {"hi": None}, {"known": K + timedelta(seconds=1)}, {"watermark": K - timedelta(seconds=1)}])
def test_ev_facades_refuse_an_unprovable_pin(over) -> None:
    svc = ev_reads(EvMoney([], None))
    for call in (lambda: svc.capabilities_on(None, ev_snap(**over)), lambda: svc.money_on(None, ev_snap(**over))):
        with pytest.raises(EvPinnedLineageUnavailable):
            call()


def test_ev_money_on_refuses_newer_head_and_drops_later_history() -> None:
    old, current, later = ev_row(K - timedelta(hours=1), 1), ev_row(K, 2), ev_row(K + timedelta(seconds=1), 3)
    got = ev_reads(EvMoney([old, current, later], current)).money_on(None, ev_snap())
    assert got["consequence"]["revision_id"] == str(current["id"]) and got["guard"] is None
    assert [h["revision_id"] for h in got["history"]] == [str(old["id"])]  # recorded after the cutoff: absent
    assert got["selection_seqs"] == {EV: 3} and got["evidence_ids"] == ["e1"]
    # STALE_BASIS: the transient guard, never a stored row or revision.
    stale = ev_reads(EvMoney([old], None)).money_on(None, ev_snap())
    assert stale["guard"] == "STALE_BASIS" and stale["consequence"]["revision_id"] is None
    newer = ev_row(K + timedelta(microseconds=1), 4)
    svc = ev_reads(EvMoney([old, newer], newer))
    ctx = {"c": None, "t": uuid4(), "s": uuid4(), "snap": ev_snap()}
    assert svc._select(ctx)["current"] is newer  # the default W2 selector is unchanged
    with pytest.raises(EvPinnedLineageUnavailable, match=str(newer["id"])):
        svc.money_on(None, ev_snap())
