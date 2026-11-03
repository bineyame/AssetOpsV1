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
from assetops_backend.chain.events import Event, SiteInfo, consume
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
        self.events, self.consumed, self.marks = list(events), set(), []

    def unconsumed(self, consumer, tenant_id, site_id, types, limit):
        return [e for e in self.events if e.type in types and (consumer, e.event_id) not in self.consumed][:limit]

    def mark_and_consume(self, consumer, event, marks) -> None:
        self.marks += list(marks)
        self.consumed.add((consumer, event.event_id))

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


def test_consume_cap_leaves_the_rest_for_the_next_tick() -> None:
    port = MemPort([_ev("reading.accepted", READING) for _ in range(3)])
    register = load_event_register()
    assert consume(port, register, "snapshots", TENANT, SITE_ID, MINI, 2).consumed == 2
    assert consume(port, register, "snapshots", TENANT, SITE_ID, MINI, 2).consumed == 1


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
