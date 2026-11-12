"""ANY-2 AR-4 phase 1 (no database): `evidence.claim` stored claim days and their serve path.

The Postgres equality (rows vs today's compose, live and historical) and the client4 AR-0 parity are in the AR-4
packet's remaining steps; here every seam is proven on fakes, each with a must-fail counterpart.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace
from uuid import UUID

import pytest

from assetops_backend.analytics.claim_limit_read import ClaimLimitReadService
from assetops_backend.chain.adapters.file_chain_config import load_event_register
from assetops_backend.chain.period_read import SERVED_KINDS_ENV, PeriodReadBuilder, PeriodReader, validate_body
from assetops_backend.chain.ports import SiteRef
from assetops_backend.estate import period_rows as pr
from assetops_backend.estate.adapters.postgres_evidence_money_read import EvidenceMoneySnapshot
from assetops_backend.evidence.source_provenance import LinkRow
from test_any1_period_read import FakeStore

UTC = timezone.utc
T = UUID("00000000-0000-0000-0000-0000000000a1")
S = UUID("00000000-0000-0000-0000-0000000000b1")
SITE = SiteRef(T, S, "KOBO-001", "MINIGRID", "Africa/Nairobi")
DAY = date(2026, 10, 13)
RID = UUID("00000000-0000-4000-8000-0000000000f1")
EV1, EV2 = "00000000-0000-4000-8000-00000000e001", "00000000-0000-4000-8000-00000000e002"
NOW = datetime(2026, 10, 21, 8, tzinfo=UTC)
DETAIL = {"id": RID, "created_at": datetime(2026, 10, 14, 1, 2, 3, 456789, tzinfo=UTC), "amount": Decimal("1.50"),
          "pair": ("a", "b"), "run": {"id": "run-1", "completed_at": datetime(2026, 10, 14, 2, tzinfo=UTC),
                                      "revisions": [{"scope": "INTERVAL", "evidence_ids": [EV2, EV1.upper()]},
                                                    {"scope": "WINDOW", "evidence_ids": ["ignored"]}]},
          "day": DAY, "result": {"limitations": ["x"], "n": 1, "f": 0.5, "ok": True, "none": None}}


def page_day(rid=RID, day=DAY):
    return {"day": day, "window_start": datetime(2026, 10, 13, tzinfo=UTC),
            "window_end": datetime(2026, 10, 14, tzinfo=UTC), "known_at": NOW, "available": True,
            "unavailable_reasons": [], "status": "CURRENT", "status_reasons": [], "selection": {"seq": 1},
            "run_id": "run-1", "assessment_revision_ids": [str(rid)], "window_assessment_revision_id": rid}


def link(i, in_scope=True):
    return LinkRow(requested_id=i, in_scope=in_scope, in_tenant_elsewhere=False, batch_id="b1",
                   evidence_gateway_source=("g", "src"), batch=("t", "s", "g", "src", "x", "sha"))


# --- codec and days ---------------------------------------------------------------------------------------------

def test_codec_round_trips_types_and_refuses_tag_keys() -> None:
    assert pr.decode(pr.encode(DETAIL)) == DETAIL
    back = pr.decode(pr.encode(DETAIL))
    assert type(back["created_at"]) is datetime and back["created_at"].isoformat() == DETAIL["created_at"].isoformat()
    assert type(back["id"]) is UUID and type(back["amount"]) is Decimal and back["pair"] == ("a", "b")
    with pytest.raises(ValueError):
        pr.encode({"$t": "x"})  # must-fail: a stored key that looks like a tag would decode as another type
    with pytest.raises(ValueError):
        pr.encode({"s": {1, 2}})


def test_link_rows_round_trip() -> None:
    row = link(EV1)
    assert pr.link_row_decode(pr.link_row_encode(row)) == row
    with pytest.raises(ValueError):
        pr.link_row_decode({"requested_id": EV1})


def test_utc_days_and_local_days() -> None:
    lo = datetime(2026, 10, 13, 21, tzinfo=UTC)  # Nairobi local 2026-10-14 00:00
    assert pr.utc_days(lo, lo + timedelta(days=1)) == [date(2026, 10, 13), date(2026, 10, 14)]
    assert pr.utc_days(datetime(2026, 10, 13, tzinfo=UTC), datetime(2026, 10, 14, tzinfo=UTC)) == [DAY]
    assert pr.local_days_of(DAY, "Africa/Nairobi") == [DAY, date(2026, 10, 14)]
    assert pr.local_days_of(DAY, "America/New_York") == [date(2026, 10, 12), DAY]
    assert pr.local_days_of(DAY, "UTC") == [DAY]


def test_interval_ids_and_day_revision() -> None:
    assert pr.interval_evidence_ids(DETAIL) == sorted([EV1.lower(), EV2])
    assert pr.day_revision(page_day()) == RID
    assert pr.day_revision({**page_day(), "selection": None}) is None
    assert pr.day_revision({**page_day(), "available": False}) is None


# --- the builder ---------------------------------------------------------------------------------------------------

class BuildSnap:
    def __init__(self, days, detail=DETAIL):
        self.read_at, self._c, self.calls = NOW, object(), []
        outer = self

        class Store:
            def claim_limit_snapshot_on(self, c, t, s, day, rid, k):
                outer.calls.append(("detail", day, rid, k))
                return {"ignored": True}, detail

        class Reads:
            def link_rows(self, t, s, ids):
                outer.calls.append(("links", tuple(ids)))
                return [link(i) for i in ids]

        self._o = SimpleNamespace(claim_limits=SimpleNamespace(store=Store()), provenance_reads=lambda c: Reads())
        self._days = days

    def dispatch_days(self, t, s, lo, hi, k):
        return [d for d in self._days if lo.date() == d["day"]]


class EstateRead:
    def __init__(self, snap):
        self.snap = snap

    def read(self, work):
        return work(self.snap)


def test_builder_stores_detail_and_link_rows_per_utc_claim_day() -> None:
    store = FakeStore()
    snap = BuildSnap([page_day(), page_day(day=date(2026, 10, 14))])
    builder = PeriodReadBuilder(store, pr.kind_builders(EstateRead(snap)))
    written = builder.build(T, SITE, date(2026, 10, 14), pr.KIND_CLAIM)  # Nairobi day touches UTC 13 and 14
    assert [(w.row.local_day, w.row.state, w.written) for w in written] == [
        (date(2026, 10, 13), "SELECTED", True), (date(2026, 10, 14), "SELECTED", True)]
    body = written[0].row.body
    validate_body(pr.KIND_CLAIM, body)
    assert body["revision_id"] == str(RID) and pr.decode(body["detail"]) == DETAIL
    assert store.prov[(RID, pr.BUILDER_VERSION)]["link_rows"][EV2] == [pr.link_row_encode(link(EV2))]
    # the same day rebuilt from the other local day it touches writes nothing (unchanged fingerprint)
    again = builder.build(T, SITE, DAY, pr.KIND_CLAIM)
    assert [w.written for w in again if w.row.local_day == DAY] == [False]


def test_builder_unassessed_and_no_day_and_not_minigrid() -> None:
    snap = BuildSnap([{**page_day(), "selection": None}])
    frag = pr.EvidenceClaimKindBuilder(EstateRead(snap)).fragment(snap, T, S, DAY)
    assert (frag.state, frag.body["revision_id"], frag.body["detail"], dict(frag.provenance)) == (
        "UNASSESSED", None, None, {})
    assert not [c for c in snap.calls if c[0] == "detail"]
    frag = pr.EvidenceClaimKindBuilder(EstateRead(snap)).fragment(snap, T, S, date(2026, 10, 20))
    assert frag.state == "NO_DAY"
    cold = SiteRef(T, S, "COLD-1", "COLDCHAIN", "Africa/Nairobi")
    assert pr.EvidenceClaimKindBuilder(EstateRead(snap)).fragments(SimpleNamespace(), cold) == []


# --- the read -------------------------------------------------------------------------------------------------------

class Conn:
    def execute(self, *_a, **_k):
        return SimpleNamespace(one=lambda: ("KOBO-001", "MINIGRID", "Africa/Nairobi"))


class Service:
    def __init__(self):
        self.calls = []

    def project_claim_limit(self, t, s, day, rid, k, selected, detail, *, basis_mode=None):
        self.calls.append((day, rid, k, selected, detail, basis_mode))
        return {"served": True, "day": day.isoformat()}


def built_store(days=(DAY,)):
    store = FakeStore(clock=[NOW - timedelta(hours=1)])
    snap = BuildSnap([page_day(day=d) for d in days])
    PeriodReadBuilder(store, pr.kind_builders(EstateRead(snap))).build_range(T, SITE, days[0], days[-1],
                                                                            [pr.KIND_CLAIM])
    return store


def request_rows(store, historical=False):
    reader = PeriodReader(store, load_event_register(), pr.kind_versions(), now=lambda: NOW)
    snap = SimpleNamespace(_c=Conn(), read_at=NOW, basis_historical=historical, site_ref=lambda t, s: SITE)
    return pr.RequestRows(pr.EvidenceRows(reader, store), snap)


def test_request_serves_a_stored_day_with_the_page_selection(monkeypatch) -> None:
    store, svc = built_store(), Service()
    rows = request_rows(store)
    lo, hi = datetime(2026, 10, 13, tzinfo=UTC), datetime(2026, 10, 14, tzinfo=UTC)
    rows.note_days(T, S, lo, hi, NOW, [page_day()])
    assert rows.claim(svc, T, S, DAY, RID, NOW, "live") == {"served": True, "day": "2026-10-13"}
    day, rid, k, selected, detail, mode = svc.calls[0]
    assert selected == {**page_day(), "transaction_time": NOW} and detail == DETAIL and mode == "live"
    assert rows.link_rows(S, [EV2, EV1]) == {(str(S), EV2): [link(EV2)], (str(S), EV1): [link(EV1)]}
    assert rows.link_rows(S, [EV2, "00000000-0000-4000-8000-00000000e999"]) is None  # one unstored ID: as today


def test_request_misses_are_read_as_today() -> None:
    store, svc = built_store(), Service()
    before = pr.row_misses()
    rows = request_rows(store)
    lo, hi = datetime(2026, 10, 13, tzinfo=UTC), datetime(2026, 10, 15, tzinfo=UTC)
    other = UUID("00000000-0000-4000-8000-0000000000f2")
    rows.note_days(T, S, lo, hi, NOW, [page_day(), page_day(day=date(2026, 10, 14))])
    assert rows.claim(svc, T, S, DAY, other, NOW, "live") is None  # another revision selected than stored
    assert rows.claim(svc, T, S, date(2026, 10, 14), RID, NOW, "live") is None  # no row for the day
    assert rows.claim(svc, T, S, DAY, RID, NOW + timedelta(seconds=1), "live") is None  # not the page's day
    assert svc.calls == [] and pr.row_misses() == before + 3


def test_no_revision_selected_is_projected_without_a_row_or_compose() -> None:
    """D-ANY.5: a page day with no selected revision needs no stored input: projected, never composed, no miss."""
    store, svc = FakeStore(clock=[NOW]), Service()  # no row was ever built
    before, norev = pr.row_misses(), pr.no_revision_days()
    rows = request_rows(store)
    rows.note_days(T, S, datetime(2026, 10, 13, tzinfo=UTC), datetime(2026, 10, 14, tzinfo=UTC), NOW,
                   [page_day(rid=None)])
    assert rows.claim(svc, T, S, DAY, None, NOW, "live") == {"served": True, "day": "2026-10-13"}
    assert svc.calls[0][1] is None and svc.calls[0][4] is None and pr.row_misses() == before
    assert pr.no_revision_days() == norev + 1
    assert rows.statements == 0  # no row read at all


def test_claim_inputs_keep_only_accepted_evidence_fields_the_projection_reads() -> None:
    full = {"id": RID, "evidence": [{"evidence_id": "e0", "disposition": "REJECTED", "role": "x"}],
            "run": {"id": "run-1", "revisions": [], "evidence": [
                {"evidence_id": "e1", "disposition": "ACCEPTED", "role": "generator_state", "payload": {"big": 1},
                 "interval_end": None, "source_time": NOW, "accepted_at": NOW, "quality": "GOOD"},
                {"evidence_id": "e2", "disposition": "HELD", "role": "feeder_demand"}]}}
    out = pr.claim_inputs(full)
    assert out["evidence"] == [] and out["run"]["revisions"] == [] and out["id"] == RID
    assert out["run"]["evidence"] == [{"evidence_id": "e1", "disposition": "ACCEPTED", "role": "generator_state",
                                       "interval_end": None, "source_time": NOW, "accepted_at": NOW}]
    assert full["run"]["evidence"][0]["payload"] == {"big": 1}  # the input is not mutated
    assert pr.claim_inputs(None) is None and pr.claim_inputs(DETAIL) == DETAIL


def test_pending_local_day_and_old_builder_are_read_as_today() -> None:
    store, svc = built_store(), Service()
    store.dirty.append((S, date(2026, 10, 14), pr.KIND_CLAIM))  # Nairobi 14th is part of UTC day 13
    rows = request_rows(store)
    rows.note_days(T, S, datetime(2026, 10, 13, tzinfo=UTC), datetime(2026, 10, 14, tzinfo=UTC), NOW, [page_day()])
    assert rows.claim(svc, T, S, DAY, RID, NOW, "live") is None
    store = built_store()
    store.rows[:] = [r.__class__(**{**r.__dict__, "builder_version": "estate-evidence-rows-0"}) for r in store.rows]
    rows = request_rows(store)
    rows.note_days(T, S, datetime(2026, 10, 13, tzinfo=UTC), datetime(2026, 10, 14, tzinfo=UTC), NOW, [page_day()])
    assert rows.claim(svc, T, S, DAY, RID, NOW, "live") is None and svc.calls == []


def test_historical_request_reads_rows_known_at_k() -> None:
    store, svc = built_store(), Service()
    built = store.rows[0].computed_at
    rows = request_rows(store, historical=True)
    rows.note_days(T, S, datetime(2026, 10, 13, tzinfo=UTC), datetime(2026, 10, 14, tzinfo=UTC),
                   built - timedelta(seconds=1), [page_day()])
    assert rows.claim(svc, T, S, DAY, RID, built - timedelta(seconds=1), "historical") is None  # before the row
    rows = request_rows(store, historical=True)
    rows.note_days(T, S, datetime(2026, 10, 13, tzinfo=UTC), datetime(2026, 10, 14, tzinfo=UTC), built,
                   [page_day()])
    assert rows.claim(svc, T, S, DAY, RID, built, "historical") is not None
    assert svc.calls[-1][2] == built and svc.calls[-1][5] == "historical"


def test_kill_switch_and_snapshot_seam(monkeypatch) -> None:
    store = built_store()
    reader = PeriodReader(store, load_event_register(), pr.kind_versions(), now=lambda: NOW)
    source = pr.EvidenceRows(reader, store)
    monkeypatch.delenv(SERVED_KINDS_ENV, raising=False)
    assert source.request(SimpleNamespace()) is None  # unset = today's compose everywhere
    monkeypatch.setenv(SERVED_KINDS_ENV, pr.KIND_CLAIM)

    live_calls = []

    class Limits(Service):
        def claim_limit_on(self, c, t, s, day, rid, k, basis_mode=None):
            live_calls.append(day)
            return {"live": True}

    class Snap(EvidenceMoneySnapshot):
        def __init__(self):
            self._o = SimpleNamespace(period_rows=source, claim_limits=Limits(), claim_limit_refused=())
            self._c, self.read_at, self.basis_historical = Conn(), NOW, False

    snap = Snap()
    pr.RequestRows.note_days(snap._period_rows(), T, S, datetime(2026, 10, 13, tzinfo=UTC),
                             datetime(2026, 10, 15, tzinfo=UTC), NOW, [page_day(), page_day(day=date(2026, 10, 14))])
    assert snap.claim_limit_on(T, S, DAY, RID, NOW, "live") == {"served": True, "day": "2026-10-13"}
    assert snap.claim_limit_on(T, S, date(2026, 10, 14), RID, NOW, "live") == {"live": True}
    assert live_calls == [date(2026, 10, 14)]


def test_claim_limit_on_is_snapshot_read_then_pure_projection(monkeypatch) -> None:
    seen = {}

    class Store:
        def claim_limit_snapshot_on(self, c, t, s, day, rid, k):
            return "SEL", "REV"

    svc = ClaimLimitReadService.__new__(ClaimLimitReadService)
    svc.store = Store()
    monkeypatch.setattr(ClaimLimitReadService, "project_claim_limit",
                        lambda self, *a, **kw: seen.update(args=a, kw=kw) or "OUT")
    assert svc.claim_limit_on(None, T, S, DAY, RID, NOW, basis_mode="live") == "OUT"
    assert seen == {"args": (T, S, DAY, RID, NOW, "SEL", "REV"), "kw": {"basis_mode": "live"}}


def test_unassessed_projection_is_pure_and_equals_compose() -> None:
    """A real projection (no revision selected) over a stored day equals the composed one, byte for byte."""
    import json

    svc = ClaimLimitReadService.__new__(ClaimLimitReadService)
    day = {**page_day(rid=None), "selection": None, "window_assessment_revision_id": None}

    class Store:
        def claim_limit_snapshot_on(self, c, t, s, d, rid, k):
            return {**day, "transaction_time": NOW}, None

    svc.store = Store()
    composed = svc.claim_limit_on(None, T, S, DAY, None, NOW, basis_mode="live")
    stored = pr.decode(pr.encode({k: v for k, v in day.items()}))
    projected = svc.project_claim_limit(T, S, DAY, None, NOW, {**stored, "transaction_time": NOW}, None,
                                        basis_mode="live")
    assert json.dumps(projected, default=str, sort_keys=True) == json.dumps(composed, default=str, sort_keys=True)


class _Stop(Exception):
    pass


@pytest.mark.parametrize("provided", [True, False])
def test_mini_grid_rows_reads_the_coverage_dispatch_days_and_notes_them(monkeypatch, provided: bool) -> None:
    """D-ANY.8 step 3: the Evidence rows read the same S3 days the coverage reads (AR-3's `dispatch.day` rows when
    the provider serves them, else the snapshot compose) and note exactly those days for the claim rows."""
    from assetops_backend.estate import coverage, evidence_money
    from assetops_backend.estate.scope import estate_request

    row_day = {"day": DAY, "window_assessment_revision_id": None, "source": "rows"}
    composed = {"day": DAY, "window_assessment_revision_id": None, "source": "compose"}
    asked: list = []
    monkeypatch.setattr(coverage, "dispatch_rows_provider",
                        (lambda t, s, lo, hi, k, explicit: asked.append(explicit) or [row_day]) if provided else None)
    noted: list = []

    class Snap:
        basis_historical = False

        def dispatch_days(self, t, s, lo, hi, k):
            assert not provided, "the snapshot compose is not read when the rows serve the days"
            return [composed]

        def note_page_days(self, t, s, lo, hi, k, days):
            noted.append(days)

        def claim_limit_on(self, t, s, day, revision, k, mode):
            raise _Stop(day)

    req = estate_request("evidence", datetime(2026, 11, 1, tzinfo=UTC), datetime(2026, 11, 2, tzinfo=UTC), None)
    with pytest.raises(_Stop):
        evidence_money.mini_grid_rows(Snap(), T, {"site_id": S, "site_code": "KOBO-001"}, req, NOW)
    expected = row_day if provided else composed
    assert noted == [[expected]] and asked == ([False] if provided else [])
