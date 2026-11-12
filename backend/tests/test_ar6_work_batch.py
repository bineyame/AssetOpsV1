"""ANY-2 AR-6: the Site board's four work-index reads become one snapshot read (no database).

`WorkIndexService.read_many` answers several list requests in ONE snapshot, each body equal to `read`'s at that
snapshot; the board's `work` port prefetches the four first pages (incidents + three maintenance windows) through it
and falls back to the single reads, unchanged, when the batch fails; a cold/EV pin is resolved once per snapshot.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import UUID

import pytest

from assetops_backend.site_outcomes import mini
from assetops_backend.site_outcomes.mini import Reads
from assetops_backend.site_outcomes.read import BoardServices, SiteOutcomeBoardService
from assetops_backend.site_outcomes.visits import maintenance_cases, record_windows
from assetops_backend.work.adapters.postgres_work_read import _ReadTx
from assetops_backend.work.site_index import WorkIndexService, parse_list_request

UTC = timezone.utc
T, S = UUID(int=1), UUID(int=2)
TO = datetime(2026, 11, 8, tzinfo=UTC)
READ_AT = datetime(2026, 11, 11, 12, tzinfo=UTC)


class Rx:
    """A snapshot read handle with one incident and one maintenance case per window (no linked Findings)."""

    def __init__(self, read_at=READ_AT):
        self.read_at = read_at

    def action_window(self, lo, hi, k):
        return None

    def eligible_cases(self, kind, lo, hi, k):
        return []

    def site_name(self):
        return "Kobo"

    def link_rows(self, ids):
        return []


class Reads_:
    def __init__(self):
        self.snapshots = 0

    def snapshot(self, t, s, code, work):
        self.snapshots += 1
        return work(Rx())


def _req(lo, hi, known=()):
    return parse_list_request(lo.strftime("%Y-%m-%dT%H:%M:%SZ"), hi.strftime("%Y-%m-%dT%H:%M:%SZ"), None,
                              list(known), None)


SPECS = [("incidents", TO - mini.WORK_WINDOW, TO), *(("maintenance", a, b) for a, b in record_windows(TO))]


def test_read_many_is_one_snapshot_and_equals_each_read() -> None:
    reads = Reads_()
    service = WorkIndexService(reads)
    singles = [service.read(T, S, "KOBO-001", kind, _req(lo, hi), access_basis="b") for kind, lo, hi in SPECS]
    assert reads.snapshots == 4
    batch = service.read_many(T, S, "KOBO-001", [(kind, _req(lo, hi)) for kind, lo, hi in SPECS], access_basis="b")
    assert reads.snapshots == 5  # the four lists in one snapshot
    assert batch == singles


class FakeWorkIndex:
    def __init__(self, fail=False):
        self.reads, self.batches, self.fail = [], [], fail
        self._service = WorkIndexService(Reads_())

    def read(self, t, s, code, kind, req, *, access_basis):
        self.reads.append((kind, req.start, req.end, req.cursor))
        return self._service.read(t, s, code, kind, req, access_basis=access_basis)

    def read_many(self, t, s, code, requests, *, access_basis):
        self.batches.append([(kind, r.start, r.end) for kind, r in requests])
        if self.fail:
            raise RuntimeError("refused")
        return self._service.read_many(t, s, code, requests, access_basis=access_basis)


def _board_reads(index: FakeWorkIndex):
    service = SiteOutcomeBoardService(BoardServices(work_index=index, parse_work_list=parse_list_request,
                                                    work_access_basis="b"))
    site = SimpleNamespace(tenant_id=T, site_id=S, site_code="KOBO-001", domain="cold", timezone="UTC")
    work = service._shared(site, None)["work"]
    reads = Reads("KOBO-001")
    incidents = reads.pages("work_index", work, "incidents", TO - mini.WORK_WINDOW, TO)  # as cold/ev/mini compose
    visits = maintenance_cases(reads, work, "KOBO-001", TO)
    return incidents, visits, reads


def test_board_work_port_reads_the_four_lists_in_one_batch() -> None:
    index = FakeWorkIndex()
    incidents, visits, reads = _board_reads(index)
    assert index.batches == [[(k, a, b) for k, a, b in SPECS]]
    assert index.reads == []  # every first page came from the batch
    assert incidents == [] and visits == [] and reads.failed == []
    assert reads.timings["work_index"][0] == 4  # the board still records its four work_index reads


def test_board_work_port_falls_back_to_single_reads_when_the_batch_fails() -> None:
    index = FakeWorkIndex(fail=True)
    incidents, visits, reads = _board_reads(index)
    assert len(index.batches) == 1
    assert [r[:3] for r in index.reads] == SPECS and reads.failed == []
    assert incidents == [] and visits == []


def test_board_work_port_without_read_many_keeps_single_reads() -> None:
    index = FakeWorkIndex()  # wrapped below without its batch read (an index service of an older composition)
    service = SiteOutcomeBoardService(BoardServices(work_index=SimpleNamespace(read=index.read),
                                                    parse_work_list=parse_list_request, work_access_basis="b"))
    site = SimpleNamespace(tenant_id=T, site_id=S, site_code="KOBO-001", domain="cold", timezone="UTC")
    work = service._shared(site, None)["work"]
    work("incidents", TO - mini.WORK_WINDOW, TO, None)
    assert [r[0] for r in index.reads] == ["incidents"]


def test_cold_pin_is_resolved_once_per_snapshot(monkeypatch) -> None:
    ports = SimpleNamespace(cold_analytics=("cold-excursion",), ev_analytics=("ev-session/1",), cold_snapshot=None,
                            ev_snapshot=None)
    rx = _ReadTx(None, T, S, "COLD-LAB-001", READ_AT, None, ports)
    calls = []

    def cold_ev(fr, known_at, snapshot, analytics, cold):
        calls.append((fr["analytic_run_id"], known_at, cold))
        return {"state": "CURRENT", "selection_seqs": {"cold-excursion": 3}}

    monkeypatch.setattr(rx, "_cold_ev", cold_ev)
    fr = {"domain": "cold_chain", "analytic_id": "cold-excursion", "analytic_run_id": UUID(int=9),
          "assessment_revision_id": UUID(int=10), "pinned": UUID(int=11)}
    first = rx._pin(fr, TO - timedelta(days=31), TO, READ_AT)
    first["selection_seqs"]["cold-excursion"] = 99  # a caller's edit never reaches the memo
    second = rx._pin(dict(fr), TO - timedelta(days=62), TO - timedelta(days=31), READ_AT)
    assert calls == [(UUID(int=9), READ_AT, True)]
    assert second == {"state": "CURRENT", "selection_seqs": {"cold-excursion": 3}}
    rx._pin({**fr, "assessment_revision_id": UUID(int=12)}, None, None, READ_AT)  # another pinned row: resolved
    rx._pin(fr, None, None, READ_AT - timedelta(days=1))  # another cutoff: resolved
    assert len(calls) == 3
    assert rx._pin({**fr, "domain": "unknown"}, None, None, READ_AT) is None
