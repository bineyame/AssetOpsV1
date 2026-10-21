"""W3-02 0c: the pinned cold/EV Site facades' fail-closed pin and cutoff rules (pure; no database).

`ColdSiteReadService.capabilities_on/money_on` and `EvSiteReads.capabilities_on/money_on` accept only an already
pinned estate snapshot; 0c r1: the head recorded by the pinned cutoff is selected and a later head is neither
selected nor refused; the default W2 paths are unchanged.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from assetops_backend.analytics.cold_reads import ColdPinnedLineageUnavailable
from assetops_backend.analytics.cold_site_reads import SCREEN_WORDING, ColdSiteReadService
from assetops_backend.analytics.ev_reads import EvPinnedLineageUnavailable
from assetops_backend.ev_site_reads import STALE_AS_OF_COPY, EvSiteReads

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


def head(kind: str, created_at: datetime, group: str = "g1", finding=None, revision_no: int = 1) -> dict:
    return {"id": uuid4(), "finding_revision_id": finding or uuid4(), "revision_no": revision_no, "episode_revision_id": uuid4(),
            "assessment_revision_id": uuid4(), "kind": kind, "state": "QUANTIFIED", "reason": None,
            "quantity_low": 0, "quantity_high": 3, "quantity_unit": "PRODUCT_HOURS", "overlap_group": group,
            "window_start": T0, "window_end": T0 + timedelta(hours=1), "evidence_ids": [], "source_gate_sha256": "AB",
            "assumption_revision_ids": [], "consequence_basis_sha256": "CD", "created_at": created_at, "limitation": None}


class ColdMoney:
    """The store's two selectors: unbounded (W2) and, with `known_at` K, the 0c r1 as-of predicates (head by
    `created_at <= K` before the per (Finding revision, kind) pick; work enqueued by K, attempts finished by K)."""

    def __init__(self, heads, pending, attempts=()):
        self.heads, self.pending, self.attempts = heads, pending, list(attempts)

    def cold_heads_on(self, c, t, s, ids, known_at=None):
        rows = [h for h in self.heads if known_at is None or h["created_at"] <= known_at]
        if known_at is None:
            return list(rows)
        best: dict = {}
        for h in rows:
            key = (h["finding_revision_id"], h["kind"])
            if key not in best or (h["revision_no"], str(h["id"])) > (best[key]["revision_no"], str(best[key]["id"])):
                best[key] = h
        return list(best.values())

    def cold_pending_on(self, c, t, s, lo, hi):
        return list(self.pending)

    def cold_pending_as_of_on(self, c, t, s, lo, hi, known_at):
        out = []
        for w in self.pending:
            done = [a for a in self.attempts if a["work_id"] == w["id"] and a["finished_at"] <= known_at]
            if w["enqueued_at"] > known_at or any(a["outcome"] == "SUCCEEDED" for a in done):
                continue
            last = max(done, key=lambda a: a["attempt_no"])["outcome"] if done else None
            out.append({"id": w["id"], "enqueued_at": w["enqueued_at"], "last_outcome": last})
        return out


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


def test_cold_money_on_selects_the_as_of_head_and_ignores_later_work() -> None:
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



def test_cold_money_on_same_finding_and_kind_old_head_at_k_new_head_after() -> None:
    """0c r1 H1 / L2: the same Finding revision and kind, revision 1 by K and revision 2 at K + epsilon: K selects
    revision 1 (counted), a later cutoff selects revision 2; the later head is never grounds for a refusal."""
    finding = uuid4()
    old = head("PRODUCT_EXPOSURE", K - timedelta(minutes=5), finding=finding, revision_no=1)
    new = head("PRODUCT_EXPOSURE", K + timedelta(microseconds=1), finding=finding, revision_no=2)
    svc = ColdSiteReadService(SimpleNamespace(), ColdMoney([old, new], []))
    sel = [{"finding_revision_id": str(finding)}]
    at_k = svc.money_on(None, cold_snap(), sel)
    assert [(r["id"], r["counted"]) for r in at_k["consequences"]] == [(str(old["id"]), True)]
    assert at_k["consequences"][0]["exact_basis"]["finding_revision_id"] == str(finding)
    later = K + timedelta(hours=1)
    after = svc.money_on(None, cold_snap(selection_cutoff=later), sel)
    assert [(r["id"], r["counted"]) for r in after["consequences"]] == [(str(new["id"]), True)]
    # A kind with no head by K produces no row.
    only_new = ColdSiteReadService(SimpleNamespace(), ColdMoney([new], []))
    assert only_new.money_on(None, cold_snap(), sel)["consequences"] == []


def test_cold_money_on_work_state_as_of_k() -> None:
    """0c r1 L1: an attempt after K neither erases K's pending work nor turns K's hold into today's outcome."""
    work = {"id": uuid4(), "enqueued_at": K - timedelta(minutes=30), "last_outcome": None}
    snap = cold_snap()
    # A FAILED attempt by K: held with the failure wording; a SUCCEEDED attempt after K does not clear it.
    attempts = [{"work_id": work["id"], "attempt_no": 1, "outcome": "FAILED", "finished_at": K - timedelta(minutes=1)},
                {"work_id": work["id"], "attempt_no": 2, "outcome": "SUCCEEDED", "finished_at": K + timedelta(minutes=1)}]
    svc = ColdSiteReadService(SimpleNamespace(), ColdMoney([], [work], attempts))
    got = svc.money_on(None, snap, [])
    assert got["withheld"] is True and got["hold"] == SCREEN_WORDING["COLD_RECOMPUTE_FAILED"]
    # A FAILED attempt only after K: still pending at K, and the hold is not today's FAILED.
    late_fail = [{"work_id": work["id"], "attempt_no": 1, "outcome": "FAILED", "finished_at": K + timedelta(minutes=1)}]
    got = ColdSiteReadService(SimpleNamespace(), ColdMoney([], [work], late_fail)).money_on(None, snap, [])
    assert got["withheld"] is True and got["hold"] != SCREEN_WORDING["COLD_RECOMPUTE_FAILED"]
    # A SUCCEEDED attempt by K: not pending at K.
    done = [{"work_id": work["id"], "attempt_no": 1, "outcome": "SUCCEEDED", "finished_at": K - timedelta(minutes=1)}]
    got = ColdSiteReadService(SimpleNamespace(), ColdMoney([], [work], done)).money_on(None, snap, [])
    assert got["withheld"] is False and got["hold"] is None


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
    """`current` is the W2 (unbounded) head; with `known_at` K the 0c r1 selector picks the highest matching
    revision recorded by K among `heads` (default: `current` alone). `bases` records the basis cutoffs asked for."""

    def __init__(self, history, current, heads=None):
        self.history, self.current = history, current
        self.heads = [current] if heads is None and current is not None else list(heads or [])
        self.bases: list = []

    def history_on(self, c, t, s, lo, hi):
        return list(self.history)

    def basis_on(self, c, t, s, lo, hi, sel, known_at=None):
        self.bases.append(known_at)
        return object()

    def select_on(self, c, t, s, lo, hi, basis, known_at=None):
        if known_at is None:
            return self.current
        rows = [h for h in self.heads if h["recorded_at"] <= known_at]
        return max(rows, key=lambda h: (h["revision_no"], str(h["id"]))) if rows else None

    def tariff_on(self, c, t, s, lo, hi, known_at=None):
        return []


def ev_reads(money) -> EvSiteReads:
    return EvSiteReads(SimpleNamespace(), money, derive=lambda basis: SimpleNamespace(basis_sha256="b"))


@pytest.mark.parametrize("over", [
    {"selection_cutoff": None}, {"selection_seqs": None}, {"selection_seqs": {EV: 1, "x": 2}},
    {"selection_seqs": {"cold-excursion": 3}}, {"selection_seqs": {EV: 0}}, {"selected": None},
    {"hi": None}, {"known": K + timedelta(seconds=1)}, {"watermark": K - timedelta(seconds=1)}])
def test_ev_facades_refuse_an_unprovable_pin(over) -> None:
    svc = ev_reads(EvMoney([], None))
    for call in (lambda: svc.capabilities_on(None, ev_snap(**over)), lambda: svc.money_on(None, ev_snap(**over))):
        with pytest.raises(EvPinnedLineageUnavailable):
            call()


def test_ev_money_on_selects_the_as_of_head_and_drops_later_history() -> None:
    old, current, later = ev_row(K - timedelta(hours=1), 1), ev_row(K, 2), ev_row(K + timedelta(seconds=1), 3)
    money = EvMoney([old, current, later], later, heads=[current, later])
    got = ev_reads(money).money_on(None, ev_snap())
    assert money.bases == [K]  # the basis is derived from the tariff assignments recorded at K
    assert got["consequence"]["revision_id"] == str(current["id"]) and got["guard"] is None
    assert [h["revision_id"] for h in got["history"]] == [str(old["id"])]  # recorded after the cutoff: absent
    assert got["selection_seqs"] == {EV: 3} and got["evidence_ids"] == ["e1"] and got["historical_label"] is None
    # STALE_BASIS: the transient guard, never a stored row or revision, with the as-of copy.
    stale = ev_reads(EvMoney([old], None)).money_on(None, ev_snap())
    assert stale["guard"] == "STALE_BASIS" and stale["consequence"]["revision_id"] is None
    assert stale["consequence"]["limitation"] == STALE_AS_OF_COPY and stale["consequence"]["amount"] is None
    assert [h["label"] for h in stale["history"]] == ["Historical scenario"]


def test_ev_money_on_later_head_is_neither_selected_nor_refused() -> None:
    """0c r1 H1 / L2: a head at K + epsilon is absent at K (no refusal) and selected at a later cutoff; the default
    W2 selector is unchanged."""
    old, newer = ev_row(K - timedelta(hours=1), 1), ev_row(K + timedelta(microseconds=1), 2)
    svc = ev_reads(EvMoney([old, newer], newer, heads=[old, newer]))
    ctx = {"c": None, "t": uuid4(), "s": uuid4(), "snap": ev_snap()}
    assert svc._select(ctx)["current"] is newer  # the default W2 selector is unchanged
    at_k = svc.money_on(None, ev_snap())
    assert at_k["consequence"]["revision_id"] == str(old["id"]) and at_k["history"] == []
    later = K + timedelta(hours=1)
    after = svc.money_on(None, ev_snap(selection_cutoff=later, watermark=later))
    assert after["consequence"]["revision_id"] == str(newer["id"])
    assert [h["revision_id"] for h in after["history"]] == [str(old["id"])]
    # A HISTORICAL pin still identifies its stored as-of head, labelled history with no current claim.
    hist = svc.money_on(None, ev_snap(state="HISTORICAL"))
    assert hist["guard"] == "HISTORICAL_CURRENT_CLAIM" and hist["consequence"]["revision_id"] == str(old["id"])
    assert hist["consequence"]["label"] == "Historical scenario"
    assert hist["historical_label"] == f"Historical as of {hist['known_at']}"
