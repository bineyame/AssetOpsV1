"""CH-1b L0 (build sheet CH-1b §3, §4, §6 step 1): consume and drain on memory ports, the drain's cap and defer
reporting, the fingerprint deciding every skip (CH-1a M1), L6 revision printing and L3 per-subject attribution."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from assetops_backend.chain.adapters.file_chain_config import load_event_register
from assetops_backend.chain.builder import SnapshotBuilder
from assetops_backend.chain.composition import load_coverage_policy, load_operating_calendar
from assetops_backend.chain.drain import Deadline, DirtyRow, drain
from assetops_backend.chain.events import Event, SiteInfo, coalesce, consume, consume_exactly
from assetops_backend.chain.measure_impls import BackupStartChain, ChamberTemperature, build_measure_set
from assetops_backend.chain.ports import DayCtx, SiteRef

UTC = timezone.utc
TENANT, SITE_ID = uuid4(), uuid4()
SITE = SiteRef(TENANT, SITE_ID, "KOBO-001", "MINIGRID", "UTC")
DAY = date(2026, 10, 27)
T0 = datetime(2026, 10, 27, 8, tzinfo=UTC)


class MemQueue:
    def __init__(self, keys) -> None:
        self.clock = 0
        self.rows = {}
        for k in keys:
            self.mark(*k)

    def mark(self, day, measure) -> None:
        self.clock += 1
        self.rows[(day, measure)] = datetime(2026, 1, 1, tzinfo=UTC) + timedelta(seconds=self.clock)

    def pop(self, tenant_id, site_id, limit):
        return [DirtyRow(d, m, at) for (d, m), at in sorted(self.rows.items())[:limit]]

    def queued(self, tenant_id, site_id) -> int:
        return len(self.rows)

    def done(self, tenant_id, site_id, row) -> bool:
        if self.rows.get((row.local_day, row.measure)) != row.marked_at:
            return False
        del self.rows[(row.local_day, row.measure)]
        return True


class FakeBuilder:
    def __init__(self, on_build=None) -> None:
        self.calls, self.on_build = [], on_build

    def build(self, tenant_id, site, local_day, measure, known_at=None):
        self.calls.append((local_day, measure))
        if self.on_build:
            self.on_build(local_day, measure)
        return [SimpleNamespace(written=True)]


def _keys(n: int):
    return [(DAY + timedelta(days=i), "productive_kwh") for i in range(n)]


def test_item_cap_defers_the_rest_without_failing() -> None:
    queue = MemQueue(_keys(5))
    report = drain(queue, FakeBuilder(), TENANT, SITE, limit=2)
    assert (report.processed, report.written, report.deferred, report.stopped) == (2, 2, 3, "items")
    assert report.as_json()["deferred"] == 3


def test_deadline_stops_with_the_rest_queued() -> None:
    queue = MemQueue(_keys(4))
    ticks = iter([False, False, True, True])
    report = drain(queue, FakeBuilder(), TENANT, SITE, limit=10, deadline=lambda: next(ticks))
    assert (report.processed, report.deferred, report.stopped) == (2, 2, "deadline")


def test_a_re_mark_during_the_build_survives_compare_and_delete() -> None:
    queue = MemQueue(_keys(1))
    report = drain(queue, FakeBuilder(on_build=lambda d, m: queue.mark(d, m)), TENANT, SITE, limit=10)
    assert (report.processed, report.re_marked, report.deferred) == (1, 1, 1)
    again = drain(queue, FakeBuilder(), TENANT, SITE, limit=10)
    assert (again.processed, again.re_marked, again.deferred, again.stopped) == (1, 0, 0, None)


def test_an_unknown_measure_row_is_cleared_without_a_build() -> None:
    queue = MemQueue([(DAY, "retired_measure")])
    builder = FakeBuilder()
    report = drain(queue, builder, TENANT, SITE, limit=10)
    assert builder.calls == [] and (report.processed, report.deferred) == (1, 0)


def test_deadline_reserves_the_slowest_item() -> None:
    now = iter([0.0, 1.0, 4.0, 6.5])
    deadline = Deadline(at=9.0, now=lambda: next(now))
    assert [deadline(), deadline(), deadline()] == [False, False, True]  # 6.5 + slowest 3.0 >= 9


# --- the real builder: the fingerprint decides every skip (CH-1a M1) and L6 ---------------------------------------


class MemStore:
    def __init__(self) -> None:
        self.rows: dict = {}

    def latest(self, key):
        rows = self.rows.get(key)
        return None if not rows else (rows[-1].revision, rows[-1].input_fp)

    def append(self, row) -> None:
        self.rows.setdefault(row.key(), []).append(row)


class DispatchReader:
    ASSET = str(uuid4())

    def __init__(self) -> None:
        self.pending = False

    def foundation_assets(self, ctx, component_type):
        return [self.ASSET]

    def dispatch_days(self, ctx):
        iv = {"id": "iv-1", "result": {"generator_asset_id": self.ASSET,
                                        "interval": {"first_on": ctx.period_start_utc},
                                        "portions_minutes": {"candidate": 10, "indeterminate": 0}}}
        return [{"status": "CURRENT", "selection": {"run_id": "sel-a"}, "intervals": [iv]}]

    def run_evidence_intervals(self, ctx, run_ids):
        lo = ctx.period_start_utc
        return [("ev-1", lo, lo + timedelta(hours=1))]

    def pending_jobs(self, ctx, domains):
        return self.pending


def _builder(reader, store):
    return SnapshotBuilder(store, build_measure_set(reader), load_coverage_policy(), load_operating_calendar())


def test_drain_twice_writes_nothing_the_second_time_and_pending_then_settled_revisions() -> None:
    reader, store = DispatchReader(), MemStore()
    builder = _builder(reader, store)
    reader.pending = True
    first = drain(MemQueue([(DAY, "avoidable_gen_min")]), builder, TENANT, SITE, limit=10)
    assert first.written == 1
    again = drain(MemQueue([(DAY, "avoidable_gen_min")]), builder, TENANT, SITE, limit=10)
    assert (again.written, again.unchanged) == (0, 1)
    reader.pending = False  # the job settles over the same evidence ids: a new revision
    settled = drain(MemQueue([(DAY, "avoidable_gen_min")]), builder, TENANT, SITE, limit=10)
    assert settled.written == 1
    (rows,) = store.rows.values()
    assert [r.revision for r in rows] == [1, 2]


def test_l6_a_skip_reports_the_stored_revision() -> None:
    reader, store = DispatchReader(), MemStore()
    builder = _builder(reader, store)
    builder.build(TENANT, SITE, DAY, "avoidable_gen_min")
    reader.pending = True
    builder.build(TENANT, SITE, DAY, "avoidable_gen_min")
    (skip,) = builder.build(TENANT, SITE, DAY, "avoidable_gen_min")
    assert (skip.written, skip.row.revision) == (False, 2)


# --- consume ------------------------------------------------------------------------------------------------------


class MemPort:
    def __init__(self, events) -> None:
        self.events, self.consumed, self.marks, self.pages = list(events), set(), [], []

    def unconsumed(self, consumer, tenant_id, site_id, types, limit):
        return [e for e in self.events if e.type in types and (consumer, e.event_id) not in self.consumed][:limit]

    def mark_and_consume(self, consumer, event, marks) -> None:
        self.marks += list(marks)
        self.consumed.add((consumer, event.event_id))

    def mark_and_consume_page(self, consumer, events, marks) -> None:
        keys = [(m.tenant_id, m.site_id, m.local_day, m.measure) for m in marks]
        assert len(set(keys)) == len(keys), "marks must be coalesced before the upsert"
        self.pages.append(([e.event_id for e in events], list(marks)))
        self.marks += [(m.local_day, m.measure) for m in marks]
        self.consumed.update((consumer, e.event_id) for e in events)

    def site_today(self, tenant_id, site_id, tz):
        return date(2026, 11, 3)


def _ev(type_: str, subject: dict) -> Event:
    return Event(uuid4(), type_, 1, T0, T0, "test", TENANT, SITE_ID, subject)


MINI = SiteInfo("MINIGRID", "UTC")
READING = {"roles": ["feeder_demand"], "span": ["2026-10-27T08:00:00Z", "2026-10-27T09:00:00Z"]}


def test_consume_is_idempotent_and_marks_once() -> None:
    port = MemPort([_ev("reading.accepted", READING)])
    register = load_event_register()
    first = consume(port, register, "snapshots", TENANT, SITE_ID, MINI, 10)
    second = consume(port, register, "snapshots", TENANT, SITE_ID, MINI, 10)
    assert (first.consumed, first.marked, second.consumed) == (1, 1, 0)
    assert port.marks == [(DAY, "productive_kwh")]


def test_consume_pages_until_the_queue_is_empty() -> None:
    """DD0-R: the page size bounds one transaction, not the run; consume pages until the queue is empty."""
    events = [_ev("reading.accepted", READING) for _ in range(5)]
    port = MemPort(events)
    report = consume(port, load_event_register(), "snapshots", TENANT, SITE_ID, MINI, 2)
    assert (report.consumed, report.pages, report.stopped) == (5, 3, None)
    assert [ids for ids, _ in port.pages] == [[e.event_id for e in events[i:i + 2]] for i in (0, 2, 4)]
    # one coalesced mark per page, whose first event is the page's earliest in read order
    assert [[(m.local_day, m.measure, m.first_event_id) for m in marks] for _, marks in port.pages] == [
        [(DAY, "productive_kwh", events[i].event_id)] for i in (0, 2, 4)]
    assert len(report.select_ms) == 3


def test_consume_deadline_leaves_the_rest_for_the_next_tick() -> None:
    port = MemPort([_ev("reading.accepted", READING) for _ in range(5)])
    register = load_event_register()
    calls = iter([False, True])
    report = consume(port, register, "snapshots", TENANT, SITE_ID, MINI, 2, deadline=lambda: next(calls))
    assert (report.consumed, report.pages, report.stopped) == (2, 1, "deadline")
    assert consume(port, register, "snapshots", TENANT, SITE_ID, MINI, 2).consumed == 3


def test_coalesce_keeps_one_mark_per_key_with_the_first_event() -> None:
    a = _ev("reading.accepted", READING)
    b = _ev("reading.accepted", READING)
    other = date(2026, 10, 28)
    marks = coalesce([(a, [(DAY, "productive_kwh")]), (b, [(other, "productive_kwh"), (DAY, "productive_kwh")])])
    assert [(m.local_day, m.measure, m.first_event_id) for m in marks] == [
        (DAY, "productive_kwh", a.event_id), (other, "productive_kwh", b.event_id)]


def test_today_is_read_once_per_run_and_a_given_today_is_used() -> None:
    class Counting(MemPort):
        reads = 0

        def site_today(self, tenant_id, site_id, tz):
            Counting.reads += 1
            return super().site_today(tenant_id, site_id, tz)
    port = Counting([_ev("reading.accepted", READING) for _ in range(4)])
    consume(port, load_event_register(), "snapshots", TENANT, SITE_ID, MINI, 1)
    assert Counting.reads == 1
    open_ended = _ev("price.revised", {"key": "productive_use_price_per_kwh", "valid": ["2026-10-26T00:00:00Z", None]})
    port = Counting([open_ended])
    consume(port, load_event_register(), "snapshots", TENANT, SITE_ID, MINI, 10, today=DAY)
    assert Counting.reads == 1 and port.marks == [(date(2026, 10, 26), "productive_kwh"), (DAY, "productive_kwh")]


def test_consume_exactly_records_only_the_events_read_before_the_run() -> None:
    first, late = _ev("action.event", {"action_ids": ["a1"]}), _ev("action.event", {"action_ids": ["a2"]})
    port = MemPort([first])
    read = port.unconsumed("lifecycle", TENANT, SITE_ID, ["action.event"], 10)
    port.events.append(late)  # committed while run_lifecycle read the state
    assert consume_exactly(port, "lifecycle", read).consumed == 1
    assert port.consumed == {("lifecycle", first.event_id)}


def test_a_failing_thread_handler_leaves_the_event_unconsumed() -> None:
    port = MemPort([_ev("finding.revised", {"ids": ["f1"]})])
    register = load_event_register()

    def boom(event):
        raise RuntimeError("thread store down")
    with pytest.raises(RuntimeError):
        consume(port, register, "threads", TENANT, SITE_ID, MINI, 10, on_event=boom)
    assert port.consumed == set()
    seen = []
    assert consume(port, register, "threads", TENANT, SITE_ID, MINI, 10, on_event=seen.append).consumed == 1
    assert [e.subject["ids"] for e in seen] == [["f1"]]


def test_snapshots_ignores_thread_events_and_threads_ignores_readings() -> None:
    port = MemPort([_ev("reading.accepted", READING), _ev("finding.revised", {"ids": ["f1"]})])
    register = load_event_register()
    assert consume(port, register, "snapshots", TENANT, SITE_ID, MINI, 10).by_type == {"reading.accepted@1": 1}
    assert consume(port, register, "threads", TENANT, SITE_ID, MINI, 10,
                   on_event=lambda e: None).by_type == {"finding.revised@1": 1}


# --- L3: per-subject attribution (ruling CH1b-R Q1) ---------------------------------------------------------------


class ColdReader:
    def __init__(self, subjects) -> None:
        self.subjects = subjects

    def foundation_assets(self, ctx, component_type):
        return list(self.subjects)

    def readings(self, ctx, roles, lo, hi):
        at = lo + timedelta(minutes=5)
        if "chamber_temperature" in roles:
            return [{"evidence_id": "t-1", "asset_id": "probe-1", "source_time": at, "value": "4.0"}]
        return [{"evidence_id": "grid", "asset_id": "grid-1", "source_time": at},
                {"evidence_id": "g1", "asset_id": "gen-1", "source_time": at},
                {"evidence_id": "g2", "asset_id": "gen-2", "source_time": at}]

    def selected_windows(self, ctx, analytic_ids):
        return [(ctx.period_start_utc, ctx.period_end_utc, "run-a")]

    def cold_temperature(self, ctx, lo, hi):
        return {"policy": {}, "gaps": [], "points": []}

    def cold_backup_chain(self, ctx, lo, hi):  # the read carries no policy (verified against the assessment store)
        return {"state": "OBSERVED", "chains": [
            {"result": "OBSERVED_SUCCESS", "steps": [{"evidence_ids": ["GRID"]}, {"evidence_ids": ["G1"]}]},
            {"result": "OBSERVED_FAILURE", "steps": [{"evidence_ids": ["grid"]}, {"evidence_ids": ["g2"]}]}]}

    def pending_jobs(self, ctx, domains):
        return False


def _ctx() -> DayCtx:
    return DayCtx(TENANT, SITE_ID, "COLD-LAB-001", "COLDCHAIN", "UTC", DAY, T0, T0 + timedelta(hours=8), None)


def test_l3_backup_chains_are_attributed_to_the_generator_in_them() -> None:
    adapter = BackupStartChain(ColdReader(["gen-1", "gen-2"]))
    one, two = (adapter.inputs(_ctx(), s) for s in ("gen-1", "gen-2"))
    assert [c["result"] for c in one.payload] == ["OBSERVED_SUCCESS"]
    assert [c["result"] for c in two.payload] == ["OBSERVED_FAILURE"]
    assert "g2" not in one.ids and "g1" not in two.ids


def test_l3_a_single_generator_keeps_every_chain() -> None:
    inputs = BackupStartChain(ColdReader(["gen-1"])).inputs(_ctx(), "gen-1")
    assert [c["result"] for c in inputs.payload] == ["OBSERVED_SUCCESS", "OBSERVED_FAILURE"]


def test_l3_a_probe_reading_counts_only_for_a_single_room() -> None:
    single = ChamberTemperature(ColdReader(["room-1"])).inputs(_ctx(), "room-1")
    double = ChamberTemperature(ColdReader(["room-1", "room-2"])).inputs(_ctx(), "room-1")
    assert [x["evidence_id"] for x in single.payload] == ["t-1"]
    assert double.payload == []


# --- backfill step (a): one provenance event per Site (ruling CH1b-R Q2) -----------------------------------------


def test_backfill_step_a_records_one_backfill_event_per_site() -> None:
    from assetops_backend.chain import backfill

    first = datetime(2026, 10, 1, 5, tzinfo=UTC)
    site = SimpleNamespace(site_id=uuid4(), timezone="UTC")
    recorded = []
    services = SimpleNamespace(
        inputs=SimpleNamespace(site=lambda t, c: site, first_evidence_time=lambda t, s: first),
        builder=SimpleNamespace(build_range=lambda *a, **k: [SimpleNamespace(written=True)]),
        events=SimpleNamespace(record_backfill=lambda *a: recorded.append(a)), dispose=lambda: None)
    reader = SimpleNamespace(site_ids=lambda t: [(site.site_id, "KOBO-001")])
    out = backfill._step_a(reader, TENANT, None, "postgresql://x/y", False, services)
    assert out["written"] == 1
    ((tenant, site_id, occurred, subject, key),) = recorded
    assert (tenant, site_id, occurred, subject["site_code"], subject["from"]) == (TENANT, site.site_id, first,
                                                                                 "KOBO-001", "2026-10-01")
    assert key == f"{site.site_id}|2026-10-01|{subject['to']}"


# --- the tick (build sheet §3, ruling CH1b-R): a cap hit defers and never backs off; a real error fails the Site --


def _tick_with(stage_results):
    from test_ch0_tick_timing import FakeRunner, FakeStore

    from assetops_backend.scheduling.tick import ScheduleTick, TickLimits

    class Store(FakeStore):
        released = None

        def release_site(self, *a, **k):
            Store.released = k
            return True

    class Runner(FakeRunner):
        def run(self, stage, args, seconds):
            out = super().run(stage, args, seconds)
            self.args = getattr(self, "args", {})
            self.args[stage] = args
            return {**out, **stage_results.get(stage, {})}

    runner = Runner()
    report = ScheduleTick(Store(), runner, TickLimits(), environment="test").tick()
    return report.selected[0], Store.released, runner


def test_tick_limits_declare_the_chain_bounds() -> None:
    from assetops_backend.scheduling.tick import STAGE_LIMIT_FIELDS, TickLimits

    limits = TickLimits()
    assert (limits.chain_snapshot_seconds, limits.chain_snapshot_items, limits.chain_consume_events) == (60, 200, 500)
    assert STAGE_LIMIT_FIELDS["chain_snapshots"] == "chain_snapshot_seconds"
    assert TickLimits(chain_snapshot_seconds=90).site_lease_seconds == limits.site_lease_seconds + 30
    for bad in ({"chain_snapshot_items": 0}, {"chain_consume_events": 0}, {"chain_snapshot_seconds": 0},
                {"chain_snapshot_seconds": 20, "statement_timeout_ms": 25_000}):
        with pytest.raises(ValueError):
            TickLimits(**bad)


def test_a_cap_hit_in_either_chain_stage_defers_and_never_backs_off_the_site() -> None:
    deferred = {"code": "OK", "processed": 3, "deferred": 7}
    site, released, runner = _tick_with({"chain_threads": deferred, "chain_snapshots": deferred})
    assert site.result == "COMPLETED" and site.failure is None and released["failure"] is None
    assert site.stages["chain_snapshots"]["deferred"] == 7 and site.stages["chain_threads"]["deferred"] == 7
    snap, threads = runner.args["chain_snapshots"], runner.args["chain_threads"]
    assert (snap["consume_limit"], snap["items"], threads["limit"]) == (500, 200, 500)
    assert snap["deadline_at"] > 0 and threads["deadline_at"] > 0


def test_a_real_chain_snapshots_error_fails_the_site() -> None:
    site, released, _ = _tick_with({"chain_snapshots": {"code": "FAILED", "error": "boom"}})
    assert site.result == "FAILED" and released["failure"][:2] == ("CHAIN_SNAPSHOTS", "FAILED")


def test_counts_a_not_expected_day_with_a_missing_measure_is_not_expected() -> None:
    """Review M1 (L0): a NOT_EXPECTED day with a requested measure missing counts NOT_EXPECTED, never NO_DATA."""
    from assetops_backend.chain.reader import _counts

    monday, tuesday = date(2026, 10, 12), date(2026, 10, 13)
    rows = [SimpleNamespace(local_day=monday, measure="productive_kwh", grade="NOT_EXPECTED")]
    counts = _counts(rows, monday, tuesday, ["productive_kwh", "noon_headroom_kw"])
    assert (counts.not_expected, counts.no_data, counts.expected, counts.requested) == (1, 1, 1, 2)
