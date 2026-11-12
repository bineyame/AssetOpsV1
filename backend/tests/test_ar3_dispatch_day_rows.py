"""ANY-2 AR-3: the Portfolio's mini-grid dispatch days from stored `dispatch.day` rows (no database).

The builder stores the exact day dict today's compose (`select_dispatch_days_on`) builds; the read hands coverage the
same Python values back at the request's `known_at`, marks a day PENDING at k with an outstanding job, renders a day
with no row as "nothing stored by k", and returns None while the kind is not served (the kill switch). Coverage over
rows equals coverage over today's compose.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from types import MappingProxyType, SimpleNamespace
from uuid import UUID, uuid4

import pytest

from assetops_backend.chain import dispatch_day_rows as ddr
from assetops_backend.chain.adapters.file_chain_config import load_event_register
from assetops_backend.chain.events import Event, S3_BRACKET, resolve
from assetops_backend.chain.period_read import (SERVED_KINDS_ENV, absent_count, PeriodReadBuilder, PeriodReader, served_kinds,
                                                validate_body)
from assetops_backend.chain.ports import SiteRef
from assetops_backend.estate import coverage
from test_any1_period_read import FakeStore

UTC = timezone.utc
T = UUID("00000000-0000-0000-0000-0000000000a1")
KOBO = SiteRef(T, UUID("00000000-0000-0000-0000-0000000000b1"), "KOBO-001", "MINIGRID", "Africa/Nairobi")
D1, D2, D3 = date(2026, 10, 20), date(2026, 10, 21), date(2026, 10, 22)


def compose_day(d: date, *, k: datetime, status: str = "CURRENT", selected: bool = True, available: bool = True,
                jobs: tuple = (), seq: int = 5) -> dict:
    """A day shaped exactly as `PostgresAssessmentStore._dispatch_day_on` returns it (real value types)."""
    start = datetime(d.year, d.month, d.day, tzinfo=UTC)
    run, rev = UUID(int=d.toordinal()), UUID(int=d.toordinal() + 10_000)
    base = {"day": d, "window_start": start, "window_end": start + timedelta(days=1), "known_at": k,
            "available": available, "unavailable_reasons": [] if available else ["JOB_STATE_AT_CUTOFF_UNKNOWN: x"]}
    if not available or not selected:
        return {**base, "status": status if available else None, "status_reasons": [], "selection": None,
                "run_id": None, "assessment_revision_ids": [], "window_assessment_revision_id": None,
                "accepted_reading_count": None if not available else 12, "input_sha256": None,
                "configuration_sha256": None, "accepted_watermarks": None, "jobs": list(jobs)}
    return {**base, "status": status, "status_reasons": [],
            "selection": {"seq": seq, "selected_at": start + timedelta(hours=26), "selected_by_job": uuid4(),
                          "run_id": run, "model_version": "dispatch-3.2", "cohort": {"status": "OK", "n": 3}},
            "run_id": run, "assessment_revision_ids": sorted([str(rev), str(UUID(int=7))]),
            "window_assessment_revision_id": rev, "accepted_reading_count": 1440, "input_sha256": "a" * 64,
            "configuration_sha256": "b" * 64, "accepted_watermarks": {"feeder_demand": start + timedelta(hours=23)},
            "jobs": list(jobs)}


@pytest.fixture
def served(monkeypatch):
    monkeypatch.setenv(SERVED_KINDS_ENV, ddr.KIND)
    assert ddr.KIND in served_kinds()


def _built(days_by_date: dict[date, dict]) -> tuple[FakeStore, PeriodReadBuilder]:
    store = FakeStore()
    builder = PeriodReadBuilder(store, {ddr.KIND: ddr.DispatchDayKindBuilder(
        lambda t, s, d: days_by_date.get(d))})
    for d in sorted(days_by_date):
        builder.build(T, KOBO, d, ddr.KIND)
    return store, builder


def _provider(store: FakeStore) -> ddr.DispatchDayRows:
    reader = PeriodReader(store, load_event_register(), {ddr.KIND: ddr.BUILDER_VERSION}, now=lambda: store.clock[0])
    return ddr.DispatchDayRows(reader, lambda t, s: KOBO if s == KOBO.site_id else None)


# --- codec and spans --------------------------------------------------------------------------------------------


def test_body_round_trips_the_compose_values_and_meets_the_row_contract() -> None:
    k = datetime(2026, 10, 23, 5, tzinfo=UTC)
    day = compose_day(D2, k=k, jobs=(MappingProxyType({"id": uuid4(), "status": "LEASED", "attempts": 1,
                                                      "lease_until": k, "last_error": None}),))
    day["amount"] = Decimal("1.50")
    body = ddr.body_of(day)
    assert "known_at" not in body
    validate_body(ddr.KIND, body)
    stored = json.loads(json.dumps(body, sort_keys=True))  # the adapter's jsonb round trip
    back = ddr.day_from_body(stored, k, pending=False)
    expected = {**day, "jobs": [dict(day["jobs"][0])]}
    assert back == expected
    assert type(back["day"]) is date and type(back["window_start"]) is datetime
    assert isinstance(back["window_assessment_revision_id"], UUID) and back["amount"] == Decimal("1.50")
    with pytest.raises(TypeError):
        ddr.encode(datetime(2026, 10, 21))  # a naive instant is never stored
    with pytest.raises(TypeError):
        ddr.encode({"x": {1, 2}})


@pytest.mark.parametrize("from_, to, days", [
    (datetime(2026, 10, 20, tzinfo=UTC), datetime(2026, 10, 22, tzinfo=UTC), [D1, D2]),
    # a UTC+3 local week edge: 21:00Z the day before touches that UTC day too
    (datetime(2026, 10, 19, 21, tzinfo=UTC), datetime(2026, 10, 21, 21, tzinfo=UTC), [date(2026, 10, 19), D1, D2]),
    (datetime(2026, 10, 20, 12, tzinfo=UTC), datetime(2026, 10, 20, 13, tzinfo=UTC), [D1]),
    (datetime(2026, 10, 20, tzinfo=UTC), datetime(2026, 10, 20, tzinfo=UTC), []),
])
def test_spans_are_the_compose_days(from_, to, days) -> None:
    assert ddr.dispatch_spans(from_, to) == days


# --- builder ----------------------------------------------------------------------------------------------------


def test_builder_stores_one_row_per_utc_day_and_appends_only_on_change() -> None:
    k = datetime(2026, 10, 23, 5, tzinfo=UTC)
    days = {D1: compose_day(D1, k=k), D2: compose_day(D2, k=k, status="STALE_PROJECTION"),
            D3: compose_day(D3, k=k, available=False)}
    store, builder = _built(days)
    assert [(r.local_day, r.period_start, r.period_end, r.state, r.revision) for r in store.rows] == [
        (D1, datetime(2026, 10, 20, tzinfo=UTC), datetime(2026, 10, 21, tzinfo=UTC), "CURRENT", 1),
        (D2, datetime(2026, 10, 21, tzinfo=UTC), datetime(2026, 10, 22, tzinfo=UTC), "STALE_PROJECTION", 1),
        (D3, datetime(2026, 10, 22, tzinfo=UTC), datetime(2026, 10, 23, tzinfo=UTC), "UNAVAILABLE", 1)]
    # the request instant is not part of the body, so a rebuild at a later clock writes nothing
    later = {d: {**v, "known_at": k + timedelta(hours=3)} for d, v in days.items()}
    rebuilt = PeriodReadBuilder(store, {ddr.KIND: ddr.DispatchDayKindBuilder(lambda t, s, d: later.get(d))})
    assert [w.written for w in rebuilt.build(T, KOBO, D1, ddr.KIND)] == [False]
    later[D1]["jobs"] = [{"id": uuid4(), "status": "PENDING"}]
    assert [w.written for w in rebuilt.build(T, KOBO, D1, ddr.KIND)] == [True]
    assert max(r.revision for r in store.rows if r.local_day == D1) == 2
    # a Site day with nothing to compose writes no row
    assert rebuilt.build(T, KOBO, date(2026, 10, 25), ddr.KIND) == []


# --- serve-path read --------------------------------------------------------------------------------------------


def test_kill_switch_returns_none(monkeypatch) -> None:
    monkeypatch.setenv(SERVED_KINDS_ENV, "mini_depth.fuel")
    store, _ = _built({D1: compose_day(D1, k=datetime(2026, 10, 23, tzinfo=UTC))})
    assert _provider(store)(T, KOBO.site_id, datetime(2026, 10, 20, tzinfo=UTC), datetime(2026, 10, 21, tzinfo=UTC),
                            datetime(2026, 10, 23, tzinfo=UTC), False) is None


def test_rows_read_back_as_compose_days_at_the_request_cutoff(served) -> None:
    built_at = datetime(2026, 10, 23, 5, tzinfo=UTC)
    days = {d: compose_day(d, k=built_at) for d in (D1, D2)}
    store, _ = _built(days)
    k = datetime(2026, 10, 23, 9, tzinfo=UTC)
    out = _provider(store)(T, KOBO.site_id, datetime(2026, 10, 20, tzinfo=UTC), datetime(2026, 10, 22, tzinfo=UTC), k,
                           False)
    assert out == [{**days[D1], "known_at": k}, {**days[D2], "known_at": k}]
    assert store.calls == ["read_latest", "unconsumed_at", "dirty_marks"]  # one row read, then PENDING-at-k


def test_absent_day_renders_nothing_stored_and_pending_adds_an_outstanding_job(served) -> None:
    built_at = datetime(2026, 10, 21, 8, tzinfo=UTC)
    store, _ = _built({D1: compose_day(D1, k=built_at)})
    # an accepted reading for D1 recorded after the build and not consumed yet: D1 is PENDING at k
    store.events.append(Event(uuid4(), "reading.accepted", 1, built_at, built_at + timedelta(minutes=5),
                              "accepted_evidence", T, KOBO.site_id,
                              {"roles": ["feeder_demand"], "span": ["2026-10-20T10:00:00Z", "2026-10-20T11:00:00Z"]}))
    store.tick(10)
    k = store.clock[0]
    d1, d2 = _provider(store)(T, KOBO.site_id, datetime(2026, 10, 20, tzinfo=UTC),
                              datetime(2026, 10, 22, tzinfo=UTC), k, True)
    assert d1["jobs"][-1] == ddr.PENDING_JOB and d1["selection"]["seq"] == 5
    assert d2 == {**ddr.absent_day(D2, k), ddr.ABSENT_MARK: True}  # D-ANY.10: marked for compose, not rendered
    # an explicit cutoff before the build: no row at k, marked the same way
    early = built_at - timedelta(hours=1)
    first, = _provider(store)(T, KOBO.site_id, datetime(2026, 10, 20, tzinfo=UTC),
                              datetime(2026, 10, 21, tzinfo=UTC), early, True)
    assert first == {**ddr.absent_day(D1, early), ddr.ABSENT_MARK: True}


class CountingSnap:
    """Compose double that returns the day dicts it holds for the asked window and records each window."""

    def __init__(self, days) -> None:
        self.basis_historical, self.continuation, self._days = True, False, days
        self.compose_calls = 0
        self.windows = []

    def dispatch_days(self, t, s, from_, to, k):
        self.compose_calls += 1
        self.windows.append((from_, to, k))
        return [d for d in self._days if d["window_end"] > from_ and d["window_start"] < to]


def _absent_logs(caplog):
    return [r for r in caplog.records if getattr(r, "event", None) == "period_row_absent"]


def test_absent_day_at_explicit_k_is_the_compose_day_and_logged(served, caplog) -> None:
    k = datetime(2026, 10, 23, 9, tzinfo=UTC)
    store, _ = _built({})  # nothing built
    composed = [compose_day(d, k=k) for d in (D1, D2)]
    snap = CountingSnap(composed)
    before = absent_count()
    with caplog.at_level("WARNING"):
        out = coverage.dispatch_days(snap, T, KOBO.site_id, datetime(2026, 10, 20, tzinfo=UTC),
                                     datetime(2026, 10, 22, tzinfo=UTC), k) \
            if _with_provider(store, coverage) else None
    assert out == composed and snap.compose_calls == 1  # one run, one compose, the compose day exactly
    assert absent_count() - before == 1
    logs = _absent_logs(caplog)
    assert len(logs) == 1 and logs[0].days == [D1.isoformat(), D2.isoformat()] and logs[0].kind == ddr.KIND


def test_two_absent_runs_compose_twice_and_a_stored_day_is_never_composed(served, caplog) -> None:
    k = datetime(2026, 10, 24, 9, tzinfo=UTC)
    d4 = date(2026, 10, 23)
    stored = compose_day(D2, k=k)
    store, _ = _built({D2: stored})
    composed = [compose_day(d, k=k, seq=9) for d in (D1, D3, d4)]
    snap = CountingSnap(composed + [compose_day(D2, k=k, seq=99)])  # compose holds a DIFFERENT D2: must not surface
    before = absent_count()
    with caplog.at_level("WARNING"):
        _with_provider(store, coverage)
        out = coverage.dispatch_days(snap, T, KOBO.site_id, datetime(2026, 10, 20, tzinfo=UTC),
                                     datetime(2026, 10, 24, tzinfo=UTC), k)
    assert [d["day"] for d in out] == [D1, D2, D3, d4]
    assert out[1] == {**stored, "known_at": k} and out[1]["selection"]["seq"] == 5  # the stored row, not compose
    assert out[0]["selection"]["seq"] == out[2]["selection"]["seq"] == out[3]["selection"]["seq"] == 9
    assert snap.compose_calls == 2  # runs [D1] and [D3, D4]
    assert absent_count() - before == 2 and len(_absent_logs(caplog)) == 2
    assert all(ddr.ABSENT_MARK not in d for d in out)


def test_all_stored_days_never_compose_and_kill_switch_unchanged(served, monkeypatch) -> None:
    k = datetime(2026, 10, 23, 9, tzinfo=UTC)
    store, _ = _built({d: compose_day(d, k=k) for d in (D1, D2)})
    snap = CountingSnap([])
    _with_provider(store, coverage)
    coverage.dispatch_days(snap, T, KOBO.site_id, datetime(2026, 10, 20, tzinfo=UTC),
                           datetime(2026, 10, 22, tzinfo=UTC), k)
    assert snap.compose_calls == 0
    monkeypatch.setenv(SERVED_KINDS_ENV, "mini_depth.fuel")  # kill switch: today's compose, unmarked
    out = coverage.dispatch_days(snap, T, KOBO.site_id, datetime(2026, 10, 20, tzinfo=UTC),
                                 datetime(2026, 10, 22, tzinfo=UTC), k)
    assert out == [] and snap.compose_calls == 1


@pytest.fixture(autouse=True)
def _restore_provider():
    before = coverage.dispatch_rows_provider
    yield
    coverage.dispatch_rows_provider = before


def _with_provider(store, cov) -> bool:
    cov.dispatch_rows_provider = _provider(store)
    return True


def test_unknown_site_is_unavailable_not_guessed(served) -> None:
    store, _ = _built({})
    with pytest.raises(ddr.DispatchRowsUnavailable):
        _provider(store)(T, uuid4(), datetime(2026, 10, 20, tzinfo=UTC), datetime(2026, 10, 21, tzinfo=UTC),
                         datetime(2026, 10, 21, tzinfo=UTC), False)


# --- coverage over rows equals coverage over today's compose ----------------------------------------------------


class Snap:
    """A live estate snapshot double (`test_cov_partial.Snap` shape) whose compose days are given."""

    def __init__(self, days, historical=False, continuation=False) -> None:
        self.basis_historical, self.continuation, self._days = historical, continuation, days
        self.compose_calls = 0

    def evidence_cutoff(self, t, s, k):
        return datetime(2026, 10, 19, tzinfo=UTC)

    def dispatch_days(self, t, s, from_, to, k):
        self.compose_calls += 1
        return self._days

    def finding_index(self, t, s, k):
        return {"heads": [], "deferred_windows": [], "match_pass": {"matched_through_selection_seq": 5}}


def _coverage(snap, monkeypatch, provider, **kw):
    monkeypatch.setattr(coverage, "dispatch_rows_provider", provider)
    return coverage.site_coverage(snap, T, KOBO.site_id, coverage.MINI_GRID, datetime(2026, 10, 20, tzinfo=UTC),
                                  datetime(2026, 10, 23, tzinfo=UTC), datetime(2026, 10, 23, 9, tzinfo=UTC), **kw)


@pytest.mark.parametrize("statuses", [("CURRENT",) * 3, ("CURRENT", "STALE_PROJECTION", "CURRENT"),
                                      ("CURRENT", "PENDING", "FAILED")])
@pytest.mark.parametrize("grades", [None, {D1: "COMPLETE", D2: "NO_DATA", D3: "COMPLETE"}])
def test_coverage_from_rows_equals_coverage_from_compose(served, monkeypatch, statuses, grades) -> None:
    k = datetime(2026, 10, 23, 9, tzinfo=UTC)
    days = [compose_day(d, k=k, status=st) for d, st in zip((D1, D2, D3), statuses)]
    kw = {} if grades is None else {"day_grades": grades, "day_tz": "UTC"}
    oracle = _coverage(Snap(days), monkeypatch, None, **kw)
    store, _ = _built({d["day"]: d for d in days})
    snap = Snap(days)
    candidate = _coverage(snap, monkeypatch, _provider(store), **kw)
    assert snap.compose_calls == 0  # the serve path never composed a day
    assert json.dumps(candidate, sort_keys=True, default=str) == json.dumps(oracle, sort_keys=True, default=str)


def test_coverage_pending_and_absent_rows(served, monkeypatch) -> None:
    k = datetime(2026, 10, 23, 9, tzinfo=UTC)
    store, _ = _built({D1: compose_day(D1, k=k), D2: compose_day(D2, k=k)})
    snap = Snap([])
    absent = _coverage(snap, monkeypatch, _provider(store))  # D3 has no row: an unchecked day, never silent
    assert absent["state"] == "PARTIAL" and absent["days"]["checked"] == 2
    assert [g["day"] for g in absent["days"]["gaps"]] == [D3.isoformat()]
    oracle = _coverage(Snap([compose_day(D1, k=k), compose_day(D2, k=k), compose_day(D3, k=k, selected=False,
                                                                                      status="UNASSESSED")]),
                       monkeypatch, None)
    assert absent == oracle  # today's compose of a day with nothing selected reads the same
    assert snap.compose_calls == 1  # D-ANY.10: the one absent run (D3) composed (this double returns no day)
    store, _ = _built({d: compose_day(d, k=k) for d in (D1, D2, D3)})
    store.dirty.append((KOBO.site_id, D2, ddr.KIND))  # a live dirty mark not drained yet
    pending = _coverage(snap, monkeypatch, _provider(store))
    assert pending["state"] == "PENDING_RECOMPUTE" and pending["job_state"] == "PENDING"
    assert snap.compose_calls == 1  # all rows stored: no further compose


def test_explicit_cutoff_reads_rows_by_k(served, monkeypatch) -> None:
    seen = []

    def provider(t, s, from_, to, k, explicit):
        seen.append(explicit)
        return []

    for snap in (Snap([]), Snap([], historical=True), Snap([], continuation=True)):
        _coverage(snap, monkeypatch, provider)
    assert seen == [False, True, True]


# --- register and wiring ----------------------------------------------------------------------------------------


def test_register_declares_dispatch_day_with_the_s3_inputs() -> None:
    from assetops_backend.analytics.assessment_inputs import BRACKET
    from assetops_backend.analytics.assessment_worker import DISPATCH_ROLES, DOMAIN

    rule = load_event_register().kinds[ddr.KIND]
    assert rule.grain == "s3_day" and rule.site_types == frozenset({"MINIGRID"})
    assert rule.inputs.roles == frozenset(DISPATCH_ROLES)
    assert rule.inputs.analytics == frozenset({"dispatch"}) and rule.inputs.job_domains == frozenset({DOMAIN})
    assert S3_BRACKET == BRACKET


def _event(type_, subject):
    now = datetime(2026, 11, 3, tzinfo=UTC)
    return Event(uuid4(), type_, 1, now, now, "test", T, KOBO.site_id, subject)


@pytest.mark.parametrize("type_, subject, local, utc", [
    # 00:30 local (UTC+3) is 21:30Z the day before: the measures take the local day, dispatch.day the UTC days
    ("reading.accepted", {"roles": ["feeder_demand"], "span": ["2026-10-30T21:30:00Z", "2026-10-30T22:30:00Z"]},
     {date(2026, 10, 31)}, {date(2026, 10, 30), date(2026, 10, 31)}),
    # a dispatch-only role dirties no measure, only its UTC day's dispatch.day
    ("reading.accepted", {"roles": ["battery_soc"], "span": ["2026-10-30T08:00:00Z", "2026-10-30T09:00:00Z"]},
     set(), {date(2026, 10, 30)}),
    ("job.changed", {"domain": "dispatch", "window": ["2026-10-30T00:00:00Z", "2026-10-31T00:00:00Z"]},
     {date(2026, 10, 30), date(2026, 10, 31)}, {date(2026, 10, 29), date(2026, 10, 30), date(2026, 10, 31)}),
    ("assessment.revised", {"analytic_ids": ["dispatch"], "windows": [["2026-10-30T02:00:00Z",
                                                                        "2026-10-30T03:00:00Z"]]},
     {date(2026, 10, 30)}, {date(2026, 10, 29), date(2026, 10, 30)}),
    ("reading.accepted", {"roles": ["chamber_temperature"], "span": ["2026-10-30T08:00:00Z", "2026-10-30T09:00:00Z"]},
     set(), set()),
])
def test_s3_day_kind_resolves_to_utc_days_with_the_bracket(type_, subject, local, utc) -> None:
    marks = resolve(load_event_register(), _event(type_, subject), site_type="MINIGRID", tz="Africa/Addis_Ababa",
                    today=date(2026, 11, 3))
    assert {d for d, m in marks if m == ddr.KIND} == utc
    if local:
        assert {d for d, m in marks if m == "avoidable_gen_min" or m == "productive_kwh"} == local


def test_composition_wires_the_builder_only_with_an_assessment_store() -> None:
    from assetops_backend.chain.composition import dispatch_day_builders, period_kind_builders

    assert dispatch_day_builders(None) == {} and period_kind_builders(None) == {}
    inputs = SimpleNamespace(dispatch=SimpleNamespace(store=SimpleNamespace(dispatch_day_now=lambda t, s, d: None)))
    built = period_kind_builders(inputs)
    # AR-4's estate kinds (built lazily, no store needed) sit beside it
    assert sorted(built) == sorted([ddr.KIND, "evidence.claim"])
    assert built[ddr.KIND].builder_version == ddr.BUILDER_VERSION
