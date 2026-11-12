"""ANY-1 AR-2 (architect answer 2026-11-10 §4 AR-2; D-ANY.5-6): the board's mini depth from stored rows, no database.

The envelope from stored hour facts and stored link rows equals the envelope today's compose builds from the same
hours and link rows, after a JSON round trip (the jsonb store); the kill switch (`ASSETOPS_PERIOD_READ_KINDS` empty)
keeps the compose path; the row path reads no raw reading, no daylight hours, no link row and no `_cutoff_sha`;
absent rows render as nothing known at k and a PENDING period as PENDING_RECOMPUTE. The Postgres builder round trip
and the byte-for-byte client4 parity (`tools/checks/period_read_parity.py --kinds`) are recorded in the AR-2 packet.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from uuid import UUID

import pytest

from assetops_backend.chain.period_read import SERVED_KINDS_ENV, PeriodRead, PeriodReadResult
from assetops_backend.chain.ports import PeriodRow
from assetops_backend.evidence.source_provenance import LinkRow
from assetops_backend.mini_depth import period_rows as pr
from assetops_backend.mini_depth import read as mread
from assetops_backend.mini_depth.inputs import local_hour
from assetops_backend.mini_depth.read import MiniDepthRead, _Head, _Hour

T = UUID("00000000-0000-0000-0000-0000000000a1")
S = UUID("00000000-0000-0000-0000-0000000000b1")
CODE, TZ = "KOBO-001", "Africa/Nairobi"
D0 = date(2026, 10, 21)
REV = [UUID(f"00000000-0000-0000-0000-00000000c0{i:02d}") for i in range(12)]
ALL_KINDS = ",".join(pr.KINDS)
K = datetime(2026, 10, 27, tzinfo=timezone.utc)


def _ev(i: int) -> str:
    return f"00000000-0000-0000-0000-0000000e{i:04d}"


def _link(i: int) -> LinkRow:
    batch = ("t", "s", "gw-1", f"src-{i % 2}", f"ext-{i}", "sha")
    return LinkRow(requested_id=_ev(i), in_scope=True, in_tenant_elsewhere=False, batch_id=f"b-{i}",
                   evidence_gateway_source=("gw-1", f"src-{i % 2}"), batch=batch, link_publication_id="p-1",
                   link=batch, publication=("t", "s", "gw-1", f"src-{i % 2}", f"ext-{i}", "sha"),
                   source_class="SIMULATED", fixture_id="fx", fixture_version="1", run_id="r", run_identity_sha256="x")


LINKS = {_ev(i): _link(i) for i in range(40)}


def _db_link_rows(_c, _t, _s, ids):
    return [LINKS[i] for i in ids if i in LINKS]


def _result(n: int, decision: str = "ELIGIBLE") -> dict:
    ids = sorted(_ev(n * 2 + j) for j in range(2))
    return {"hour": {"decision": decision, "capability_kw": {"low": 10, "high": 12.5}, "used_kw": 4.25,
                     "headroom_kw": {"low": 5.75, "high": 8.25}},
            "rows": [{"day": "2026-10-21", "from": f"2026-10-21T{8 + n:02d}:00:00.000000Z", "constraints": [],
                      "evidence_ids": ids, "opportunity_kwh": {"low": 1, "high": 2}}],
            "coverage": {"required_seconds": 3600, "observed_seconds": 3600, "source_count": 2, "gaps": []},
            "basis": {"accepted_evidence_ids": ids, "committed_watermark": "2026-10-21T23:00:00.000000Z"},
            "status": "SUPPORTED", "cards": {"delivered_load_kw": 3}, "limitations": []}


def _hour(day: date, h: int, n: int, *, state: str = "CURRENT", head: bool = True, jobs: bool = False) -> _Hour:
    w = local_hour(day, h, TZ)
    hd = None
    if head:
        r = _result(n)
        hd = _Head(n + 1, REV[n], datetime(2026, 10, 22, 1, tzinfo=timezone.utc), f"sha-{n}", r,
                   tuple(r["basis"]["accepted_evidence_ids"]))
    return _Hour(day, w, hd, "PENDING" if jobs else ("SETTLED" if head else "NONE"),
                 "PENDING_RECOMPUTE" if jobs and head else state, (_ev(30), _ev(31)) if jobs else None,
                 ("job-1",) if jobs else ())


def _round_trip(value):
    return json.loads(json.dumps(value))  # what jsonb gives back


def _stored(hours: list[_Hour]) -> tuple[list[dict], dict[str, dict]]:
    """What `build_period` stores for these hours: hour facts and per-revision link rows."""
    grouped = pr.group_link_rows(LINKS.values())
    facts = [pr.hour_json(h, pending_link_rows=None if h.pending_ids is None else
                          {i: grouped[i] for i in h.pending_ids}) for h in hours]
    prov = {str(h.head.revision_id): {i: grouped[i] for i in h.head.evidence_ids} for h in hours if h.head}
    return _round_trip(facts), _round_trip(prov)


class FakeReader:
    def __init__(self, rows: dict[date, list[dict]], kind: str, *, pending: dict | None = None) -> None:
        self.rows, self.kind, self.pending, self.calls = rows, kind, pending or {}, []

    def read(self, tenant_id, sites, kinds, from_day, to_day, known_at=None):
        self.calls.append((kinds, from_day, to_day, known_at))
        out, absent = [], []
        day = from_day
        while day <= to_day:
            if day in self.rows:
                hours = self.rows[day]
                start = datetime.fromisoformat(hours[0]["window_start"].replace("Z", "+00:00")) if hours else \
                    datetime(2026, 1, 1, tzinfo=timezone.utc)
                out.append(PeriodRead(PeriodRow(T, S, self.kind, start, start + timedelta(hours=1), day, 1,
                                                pr.BUILDER_VERSION, "fp", "CURRENT", {"hours": hours}),
                                      self.pending.get(day, ())))
            else:
                absent.append((S, day, self.kind))
            day += timedelta(days=1)
        return PeriodReadResult(out, {}, 1, tuple(absent))


class FakeStore:
    def __init__(self, prov: dict[str, dict]) -> None:
        self.prov = prov

    def provenance(self, tenant_id, revision_ids, builder_version):
        assert builder_version == pr.BUILDER_VERSION
        return {r: {"link_rows": self.prov[str(r)]} for r in revision_ids if str(r) in self.prov}


@pytest.fixture
def no_raw_reads(monkeypatch):
    """The row path reads no raw reading, no daylight hours, no `_cutoff_sha` and no link row."""
    def boom(*_a, **_k):
        raise AssertionError("raw read on the row path")
    for name in ("load_hour_inputs", "daylight_hours", "_cutoff_sha", "read_hour_rows", "_hour_ids"):
        monkeypatch.setattr(mread, name, boom)


def _renewable_hours() -> list[_Hour]:
    out, n = [], 0
    for i in range(5):
        day = D0 + timedelta(days=i)
        for h in (11, 12):
            out.append(_hour(day, h, n, state="STALE_SOURCE" if n == 3 else "CURRENT", jobs=n == 5))
            n += 1
    return out


def _bounds(first: date, n: int) -> tuple[datetime, datetime]:
    return mread._local_midnight(first, TZ), mread._local_midnight(first + timedelta(days=n), TZ)


def _compose(hours, domain, lo, hi, known, historical=False):
    mini = MiniDepthRead(None, _db_link_rows)
    if historical:
        hours = [h if h.state != "CURRENT" else _Hour(h.day, h.window, h.head, h.job_state, "HISTORICAL",
                                                      h.pending_ids, h.job_ids) for h in hours]
    return mini._envelope(None, _db_link_rows, T, S, CODE, domain, lo, hi, known, TZ, hours)


class JobsConn:
    """D-ANY.6a: answers the rows path's one batched `_JOBS` statement. `live` maps an hour's `window_start` (as
    stored) to its live (job id, status) list at k; default = exactly the stored jobs (no fallback)."""

    def __init__(self, live: dict[str, list[tuple[str, str]]]) -> None:
        self.live, self.calls = live, 0

    @classmethod
    def as_stored(cls, stored_by_day) -> "JobsConn":
        return cls({f["window_start"]: [(j, f["job_state"]) for j in f["job_ids"]]
                    for facts in stored_by_day.values() for f in facts})

    def execute(self, stmt, p=None):
        assert stmt is mread._JOBS_BATCH
        self.calls += 1
        rows = [(i + 1, j, st) for i, lo in enumerate(p["los"]) for j, st in self.live.get(mread.iso(lo), [])]

        class R:
            def all(self_inner):
                return rows
        return R()


def _rows_envelope(stored_by_day, prov, domain, lo, hi, known, explicit, *, pending=None):
    reader = FakeReader(stored_by_day, pr.kind_of(domain), pending=pending)
    mini = MiniDepthRead(None, _no_link_rows, period_rows=(reader, FakeStore(prov)))
    conn = JobsConn.as_stored(stored_by_day)
    got = mini._row_hours(conn, T, S, CODE, domain, lo, hi, TZ, explicit, explicit or known,
                          explicit is not None and explicit < known)
    assert conn.calls == 1  # one batched job statement per read
    assert got is not None
    hours, links = got
    return mini._envelope(None, links, T, S, CODE, domain, lo, hi, explicit or known, TZ, hours), reader


def _no_link_rows(*_a):
    raise AssertionError("the row path reads no link row")


def _by_day(facts: list[dict]) -> dict[date, list[dict]]:
    out: dict[date, list[dict]] = {}
    for f in facts:
        out.setdefault(date.fromisoformat(f["local_day"]), []).append(f)
    return out


def test_hour_missing_flag_round_trips_through_json() -> None:
    """D-SR.62: the stored hour carries `missing` (builder `mini-depth-rows-2`); a version-1 body reads False."""
    from dataclasses import replace

    assert pr.BUILDER_VERSION == "mini-depth-rows-2"
    for h in (replace(_hour(D0, 3, 1, head=False), missing=True), _hour(D0, 12, 2)):
        value = _round_trip(pr.hour_json(h))
        assert value["missing"] is h.missing
        assert pr.hour_from_json(value, historical=False, pending=False) == h
    old = _round_trip(pr.hour_json(_hour(D0, 12, 2)))
    del old["missing"]
    assert pr.hour_from_json(old, historical=False, pending=False).missing is False


def test_link_rows_round_trip_through_json() -> None:
    row = _link(3)
    assert pr.link_row_from_json(_round_trip(pr.link_row_json(row))) == row
    assert pr.link_row_from_json(_round_trip(pr.link_row_json(LinkRow(_ev(1), False, False)))) == \
        LinkRow(_ev(1), False, False)


@pytest.mark.parametrize("historical", [False, True])
def test_renewable_envelope_from_rows_equals_compose(monkeypatch, no_raw_reads, historical) -> None:
    monkeypatch.setenv(SERVED_KINDS_ENV, ALL_KINDS)
    hours = _renewable_hours()
    facts, prov = _stored(hours)
    lo, hi = _bounds(D0, 5)
    known = datetime(2026, 10, 27, tzinfo=timezone.utc)
    explicit = known - timedelta(hours=2) if historical else None
    at = explicit or known
    expected = _compose(hours, "renewable", lo, hi, at, historical)
    got, reader = _rows_envelope(_by_day(facts), prov, "renewable", lo, hi, known, explicit)
    assert reader.calls == [(["mini_depth.renewable"], D0, D0 + timedelta(days=4), explicit)]
    assert json.dumps(got, sort_keys=False, default=str) == json.dumps(expected, sort_keys=False, default=str)
    assert got["currentness"]["state"] == "PENDING_RECOMPUTE"  # the live job hour, through the stored facts
    assert got["pending_source_provenance"] is not None


@pytest.mark.parametrize("domain", ["fuel", "service", "backup"])
def test_hourly_envelope_from_rows_equals_compose(monkeypatch, no_raw_reads, domain) -> None:
    monkeypatch.setenv(SERVED_KINDS_ENV, ALL_KINDS)
    hours = [_hour(D0, 12, 4)]
    facts, prov = _stored(hours)
    w = hours[0].window
    known = datetime(2026, 10, 27, tzinfo=timezone.utc)
    expected = _compose(hours, domain, w.start, w.end, known)
    got, _ = _rows_envelope(_by_day(facts), prov, domain, w.start, w.end, known, None)
    assert json.dumps(got, default=str) == json.dumps(expected, default=str)
    assert got["selected_source_provenance"]["evidence_ids"] == sorted(hours[0].head.evidence_ids)


def test_kill_switch_empty_keeps_the_compose_path(monkeypatch) -> None:
    reader = FakeReader({}, "mini_depth.fuel")
    mini = MiniDepthRead(None, _db_link_rows, period_rows=(reader, FakeStore({})))
    w = local_hour(D0, 12, TZ)
    monkeypatch.setenv(SERVED_KINDS_ENV, "")
    assert mini._row_hours(JobsConn({}), T, S, CODE, "fuel", w.start, w.end, TZ, None, K, False) is None
    monkeypatch.delenv(SERVED_KINDS_ENV)
    assert mini._row_hours(JobsConn({}), T, S, CODE, "fuel", w.start, w.end, TZ, None, K, False) is None
    monkeypatch.setenv(SERVED_KINDS_ENV, "mini_depth.renewable")  # another kind served: fuel still composes
    assert mini._row_hours(JobsConn({}), T, S, CODE, "fuel", w.start, w.end, TZ, None, K, False) is None
    assert reader.calls == []
    monkeypatch.setenv(SERVED_KINDS_ENV, "mini_depth.fuel")
    assert mini._row_hours(JobsConn({}), T, S, CODE, "fuel", w.start, w.end, TZ, None, K, False) is not None
    assert len(reader.calls) == 1
    # an hour the board does not read stays on the compose path
    w9 = local_hour(D0, 9, TZ)
    assert mini._row_hours(JobsConn({}), T, S, CODE, "fuel", w9.start, w9.end, TZ, None, K, False) is None
    # no row reader configured: compose
    assert MiniDepthRead(None, _db_link_rows)._row_hours(JobsConn({}), T, S, CODE, "fuel", w.start, w.end, TZ,
                                                         None, K, False) is None


def test_kill_switch_routes_read_to_compose(monkeypatch) -> None:
    """`_read` takes `_row_hours` only when it answers; empty switch -> the compose's `hour_windows`/`_hour`."""
    calls = []
    monkeypatch.setenv(SERVED_KINDS_ENV, "")

    class C:
        def execute(self, *_a, **_k):
            class R:
                def scalar_one_or_none(self_inner):
                    return TZ

                def all(self_inner):  # the rows path's batched `_JOBS`: no live job
                    return []
            return R()

    mini = MiniDepthRead(None, _db_link_rows, period_rows=(FakeReader({}, "mini_depth.fuel"), FakeStore({})))
    monkeypatch.setattr(mini, "_hour", lambda *a: calls.append("compose") or _hour(D0, 12, 4))
    w = local_hour(D0, 12, TZ)
    known = datetime(2026, 10, 27, tzinfo=timezone.utc)
    out = mini._read(C(), T, S, CODE, "fuel", w.start, w.end, None, known)
    assert calls == ["compose"] and out["currentness"]["windows"][0]["selection_id"] == 5
    monkeypatch.setenv(SERVED_KINDS_ENV, "mini_depth.fuel")
    calls.clear()
    out = mini._read(C(), T, S, CODE, "fuel", w.start, w.end, None, known)  # no row: absent, not compose
    assert calls == [] and out["status"] == "UNKNOWN" and out["currentness"]["job_state"] == "NONE"


def test_absent_and_pending_days(monkeypatch, no_raw_reads) -> None:
    monkeypatch.setenv(SERVED_KINDS_ENV, ALL_KINDS)
    hours = _renewable_hours()
    facts, prov = _stored(hours)
    rows = _by_day(facts)
    rows.pop(D0 + timedelta(days=1))  # one day has no row at k
    lo, hi = _bounds(D0, 5)
    known = datetime(2026, 10, 27, tzinfo=timezone.utc)
    got, _ = _rows_envelope(rows, prov, "renewable", lo, hi, known, None,
                            pending={D0 + timedelta(days=2): ("event",)})
    windows = got["currentness"]["windows"]
    absent = [w for w in windows if w["local_day"] == (D0 + timedelta(days=1)).isoformat()]
    assert absent and all(w["state"] == "UNKNOWN" and w["selection_id"] is None and w["job_state"] == "NONE"
                          for w in absent)
    pending = [w for w in windows if w["local_day"] == (D0 + timedelta(days=2)).isoformat()]
    assert pending and all(w["state"] == "PENDING_RECOMPUTE" for w in pending)
    assert got["currentness"]["state"] == "UNKNOWN" and got["status"] == "UNKNOWN"


def test_missing_provenance_is_unavailable_never_guessed(monkeypatch, no_raw_reads) -> None:
    monkeypatch.setenv(SERVED_KINDS_ENV, ALL_KINDS)
    hours = [_hour(D0, 12, 4)]
    facts, _prov = _stored(hours)
    w = hours[0].window
    with pytest.raises(mread.MiniReadUnavailable):
        _rows_envelope(_by_day(facts), {}, "fuel", w.start, w.end, datetime(2026, 10, 27, tzinfo=timezone.utc),
                       None)


def test_kind_builder_fragment_and_versions() -> None:
    from assetops_backend.chain.composition import period_kind_builders, period_kind_versions
    from assetops_backend.chain.ports import DayCtx, SiteRef

    hours = [_hour(D0, 12, 4)]
    facts, prov = _stored(hours)

    class Mini:
        def build_period(self, **kw):
            assert kw["local_day"] == D0 and kw["domain"] == "fuel"
            return hours[0].window.start, hours[0].window.end, facts, prov

    builders = period_kind_builders(type("I", (), {"mini": Mini()})())
    # AR-4 adds `evidence.claim` (built lazily over the estate Evidence reader) beside the mini kinds.
    assert sorted(builders) == sorted((*pr.KINDS, "evidence.claim")) and period_kind_builders(None) == {}
    from assetops_backend.chain import dispatch_day_rows  # AR-3's kind joins the reader's version map
    from assetops_backend.estate import period_rows as er
    assert period_kind_versions() == {**{k: pr.BUILDER_VERSION for k in pr.KINDS},
                                      dispatch_day_rows.KIND: dispatch_day_rows.BUILDER_VERSION,
                                      **er.kind_versions()}
    site = SiteRef(T, S, CODE, "MINIGRID", TZ)
    ctx = DayCtx(T, S, CODE, "MINIGRID", TZ, D0, None, None, None)
    (frag,) = builders["mini_depth.fuel"].fragments(ctx, site)
    assert (frag.period_start, frag.state, frag.body) == (hours[0].window.start, "CURRENT", {"hours": facts})
    assert set(frag.provenance) == {REV[4]}
    from assetops_backend.chain.period_read import validate_body

    validate_body("mini_depth.fuel", frag.body)  # the stored-row contract holds for the mini facts


@pytest.mark.parametrize("change", ["new_job", "moved_later", "status"])
def test_job_set_differs_falls_back_to_hour_for_that_hour_only(monkeypatch, change) -> None:
    """D-ANY.6a: an hour whose live jobs at k (the `_JOBS` predicate) differ from its row's is served by `_hour`
    (logged `period_row_job_fallback`, counted); every other hour stays on its row; link rows then read live."""
    monkeypatch.setenv(SERVED_KINDS_ENV, ALL_KINDS)
    hours = _renewable_hours()  # hour n=5 (D0+2 11:00) holds job-1 PENDING; the others none
    facts, prov = _stored(hours)
    rows = _by_day(facts)
    conn = JobsConn.as_stored(rows)
    target = {"new_job": hours[1], "moved_later": hours[5], "status": hours[5]}[change]
    key = mread.iso(target.window.start)
    conn.live[key] = {"new_job": [("job-9", "PENDING")], "moved_later": [],
                      "status": [("job-1", "FAILED")]}[change]
    replaced = []
    mini = MiniDepthRead(None, _db_link_rows, period_rows=(FakeReader(rows, "mini_depth.renewable"), FakeStore(prov)))
    sentinel = _hour(target.day, 12, 9, state="STALE_SOURCE")
    monkeypatch.setattr(mini, "_hour", lambda c, t, s, d, day, w, k, hist: replaced.append(w) or sentinel)
    lo, hi = _bounds(D0, 5)
    before = mread.job_fallback_count()
    got = mini._row_hours(conn, T, S, CODE, "renewable", lo, hi, TZ, None, K, False)
    assert got is not None
    out, links = got
    assert replaced == [target.window] and mread.job_fallback_count() == before + 1
    assert [h for h in out if h is sentinel] == [sentinel] and len(out) == len(hours)
    assert links == mini._link_rows  # a fallback read takes link rows as the compose does
    conn.live[key] = [(j, f["job_state"]) for f in facts if f["window_start"] == key for j in f["job_ids"]]
    replaced.clear()
    mini._row_hours(conn, T, S, CODE, "renewable", lo, hi, TZ, None, K, False)
    assert replaced == []  # the stored job set again: every hour from its row
