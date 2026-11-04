"""CH-1b fix round L2 (review REVISE M1, M2; rulings DD0-R and CH1b-R2).

- The page write: coalesced marks and every consumption row in one transaction; duplicate keys refused.
- DD0-R: about 4,400 reading events of one Site-day drain in one tick, with the stage time reported against 50% of
  its bound; and the same after a backlog of about 60,000 consumed events (per-page select ms at both sizes).
- M1: a selection is invisible before its `selected_at`; a live job is cleared only by a later selection of one of
  its own analytics; a job not yet available is not pending; a TUE-only calendar writes one NOT_EXPECTED row per
  subject on a Monday, and the reader counts that day NOT_EXPECTED, not NO_DATA.
- M2: event-driven `chain_threads` on real Finding and Action rows places only the named revisions and links an
  Action recorded before its Finding once the Finding is placed.

Needs `ASSETOPS_TEST_DATABASE_URL` naming a `*_test` database; skipped otherwise.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text

    from test_s1_bindings_postgres import engine, store  # noqa: F401
    from test_ch2_thread_store_postgres import seeded  # noqa: F401
    import test_ch1a_snapshot_postgres as ch1a
    import test_w402_reads_postgres as w402
    from assetops_backend.chain.adapters.file_chain_config import load_event_register
    from assetops_backend.chain.adapters.postgres_event_store import PostgresEventStore
    from assetops_backend.chain.adapters.postgres_snapshot_store import PostgresSnapshotStore
    from assetops_backend.chain.builder import SnapshotBuilder
    from assetops_backend.chain.composition import (build_chain_inputs, load_coverage_policy,
                                                    load_operating_calendar)
    from assetops_backend.chain.events import Event, Mark
    from assetops_backend.chain.measure_impls import build_measure_set
    from assetops_backend.chain.ports import DayCtx, SiteRef
    from assetops_backend.chain.reader import SnapshotReader

UTC = timezone.utc
BOUND = 60.0  # TickLimits.chain_snapshot_seconds


def _measure(name: str, **values) -> None:
    print("CH1B-MEASURE " + json.dumps({"case": name, **values}, default=str))


def _snapshot_types() -> list[str]:
    return sorted({k.partition("@")[0] for k in load_event_register().consumes("snapshots")})


def _readings(engine, t, s, day: date, n: int, tag: str) -> None:
    """`n` reading.accepted events of one Site-day, in the 0044 producer's subject shape (one per statement)."""
    with engine.begin() as c:
        c.execute(text(
            "INSERT INTO event_outbox (type, schema_version, occurred_at, source, tenant_id, site_id, subject, "
            "idempotency_key) SELECT 'reading.accepted', 1, :lo + g * interval '9 seconds', 'ch1b-fix-test', :t, :s, "
            "jsonb_build_object('roles', jsonb_build_array('feeder_demand'), 'asset_ids', '[]'::jsonb, "
            "'span', jsonb_build_array(:lo + g * interval '9 seconds', :lo + (g + 1) * interval '9 seconds')), "
            ":tag || g FROM generate_series(0, :n - 1) g"),
            {"lo": datetime(day.year, day.month, day.day, 6, tzinfo=UTC), "t": t, "s": s, "n": n, "tag": tag})


def _stage(t, s, items: int = 500) -> dict:
    from assetops_backend.scheduling import stages

    started = time.time()
    out = stages.chain_snapshots(URL, {"tenant_id": str(t), "site_id": str(s), "consume_limit": 500, "items": items,
                                       "bound_seconds": BOUND, "deadline_at": started + BOUND - min(5.0, BOUND / 10)})
    out["stage_ms"] = round((time.time() - started) * 1000, 1)
    return out


# --- the page write ----------------------------------------------------------------------------------------------


def test_page_write_is_one_transaction_and_refuses_uncoalesced_marks(store, engine) -> None:  # noqa: F811
    _, t, s = w402._setup(store, engine)
    events = PostgresEventStore(URL)
    day = date(2026, 10, 12)
    try:
        _readings(engine, t, s, day, 3, f"{s}|page|")
        page = [e for e in events.unconsumed("snapshots", t, s, ["reading.accepted"], 10)
                if e.source == "ch1b-fix-test"]
        assert len(page) == 3
        dup = [Mark(t, s, day, "productive_kwh", page[0].event_id), Mark(t, s, day, "productive_kwh", page[1].event_id)]
        with pytest.raises(ValueError):
            events.mark_and_consume_page("snapshots", page, dup)
        bad = page + [Event(uuid4(), "reading.accepted", 1, page[0].occurred_at, page[0].recorded_at, "x", t, s, {})]
        with pytest.raises(Exception):  # an unknown event id fails the FK: nothing of the page is written
            events.mark_and_consume_page("snapshots", bad, dup[:1])
        with engine.connect() as c:
            assert c.execute(text("SELECT count(*) FROM snapshot_dirty WHERE site_id = :s AND local_day = :d"),
                             {"s": s, "d": day}).scalar_one() == 0
        events.mark_and_consume_page("snapshots", page, dup[:1] + [Mark(t, s, day, "avoidable_gen_min",
                                                                        page[0].event_id)])
        with engine.connect() as c:
            rows = c.execute(text("SELECT measure, first_event_id FROM snapshot_dirty WHERE site_id = :s "
                                  "AND local_day = :d ORDER BY 1"), {"s": s, "d": day}).all()
            consumed = c.execute(text("SELECT count(*) FROM event_consumption WHERE consumer = 'snapshots' "
                                      "AND event_id = ANY(:e)"), {"e": [e.event_id for e in page]}).scalar_one()
        assert [(m, e) for m, e in rows] == [("avoidable_gen_min", page[0].event_id),
                                            ("productive_kwh", page[0].event_id)]
        assert consumed == 3
    finally:
        events.dispose()


# --- DD0-R: one Kobo day in one tick, before and after a 60,000-event backlog ------------------------------------


def test_dd0r_one_site_day_of_readings_drains_in_one_tick(store, engine) -> None:  # noqa: F811
    _, t, s = w402._setup(store, engine)
    warm = _stage(t, s)  # the set-up's own events
    assert warm["code"] == "OK" and warm["deferred"] == 0, warm
    day = date(2026, 10, 20)
    _readings(engine, t, s, day, 4400, f"{s}|day|")
    out = _stage(t, s)
    assert out["code"] == "OK" and out["deferred"] == 0, out
    assert out["consume"]["consumed"] == 4400 and out["consume"]["stopped"] is None
    assert out["consume"]["pages"] == 9 and out["consume"]["marked"] == 9  # one coalesced mark per page
    assert out["drain"]["processed"] == 1  # the one (day, productive_kwh) row
    _measure("4400", stage_ms=out["stage_ms"], half_bound_ms=BOUND * 500, consume_ms=out["consume"]["ms"],
             drain_ms=out["drain"]["ms"], select_ms=out["consume"]["select_ms"],
             share_of_half=round(out["stage_ms"] / (BOUND * 500), 3))
    assert out["stage_ms"] < BOUND * 500, out  # within 50% of the stage bound


def test_dd0r_the_same_day_after_a_60000_event_backlog(store, engine) -> None:  # noqa: F811
    _, t, s = w402._setup(store, engine)
    assert _stage(t, s)["deferred"] == 0
    first = date(2026, 10, 1)
    for i in range(14):  # 14 Kobo days, about 4,300 events each
        _readings(engine, t, s, first + timedelta(days=i), 4300, f"{s}|backlog{i}|")
    backlog = _stage(t, s)
    while backlog["deferred"]:  # a backlog may need more than one tick; it is never a failure
        assert backlog["code"] == "OK"
        backlog = _stage(t, s)
    with engine.connect() as c:
        consumed = c.execute(text("SELECT count(*) FROM event_consumption x JOIN event_outbox o "
                                  "ON o.event_id = x.event_id WHERE o.site_id = :s AND x.consumer = 'snapshots'"),
                             {"s": s}).scalar_one()
    assert consumed >= 60200
    _readings(engine, t, s, date(2026, 10, 20), 4400, f"{s}|after|")
    out = _stage(t, s)
    assert out["code"] == "OK" and out["deferred"] == 0 and out["consume"]["consumed"] == 4400, out
    _measure("4400_after_60k", consumed_before=consumed, stage_ms=out["stage_ms"], half_bound_ms=BOUND * 500,
             consume_ms=out["consume"]["ms"], drain_ms=out["drain"]["ms"], select_ms=out["consume"]["select_ms"],
             share_of_half=round(out["stage_ms"] / (BOUND * 500), 3))


# --- M1: the bitemporal SQL of residuals 1 and 2 and the subject instant (CH-1a L2) -------------------------------


def _ctx(t, s, lo: datetime, hi: datetime, known_at: datetime) -> DayCtx:
    return DayCtx(t, s, w402.CODE, "MINIGRID", w402.ZONE, lo.date(), lo, hi, known_at)


def _now(engine) -> datetime:
    with engine.connect() as c:
        return c.execute(text("SELECT clock_timestamp()")).scalar_one()


def _run_id(engine, t, s):
    """A completed analytic run for the selections to reference (TEST-SCOPED; the w402 set-up runs none)."""
    run = uuid4()
    with engine.begin() as c:
        c.execute(text(
            "INSERT INTO analytic_run (id, tenant_id, site_id, analytic_id, model_version, window_start, window_end, "
            "knowledge_cutoff, input_sha256, cohort_status, cohort_sha256, cohort, configuration_sha256, "
            "foundation_revision_ids, binding_set_revision_ids, role_coverage, watermarks, selection, job_id, status, "
            "started_at, completed_at) VALUES (:id, :t, :s, 'dispatch', 'test', :lo, :hi, :lo, 'x', 'COMPLETE', 'x', "
            "'{}', 'x', '[]', '[]', '{}', '{}', 'DEFAULT', NULL, 'COMPLETED', :lo, :lo)"),
            {"id": run, "t": t, "s": s, "lo": datetime(2026, 10, 1, tzinfo=UTC), "hi": datetime(2026, 10, 2, tzinfo=UTC)})
    return run


def _select(engine, t, s, run, analytic: str, lo: datetime, hi: datetime) -> datetime:
    with engine.begin() as c:
        return c.execute(text(
            "INSERT INTO analytic_run_selection (tenant_id, site_id, analytic_id, window_start, window_end, run_id, "
            "job_id, selected_at) VALUES (:t, :s, :a, :lo, :hi, :r, NULL, clock_timestamp()) RETURNING selected_at"),
            {"t": t, "s": s, "a": analytic, "lo": lo, "hi": hi, "r": run}).scalar_one()


def _job(engine, t, s, domain: str, lo: datetime, hi: datetime, available_at: datetime) -> None:
    with engine.begin() as c:
        c.execute(text(
            "INSERT INTO recompute_job (id, tenant_id, site_id, domain, window_start, window_end, cause_evidence_id, "
            "status, available_at, created_at) VALUES (:id, :t, :s, :d, :lo, :hi, NULL, 'PENDING', :at, :at)"),
            {"id": uuid4(), "t": t, "s": s, "d": domain, "lo": lo, "hi": hi, "at": available_at})


def test_m1_selection_and_job_visibility_at_the_cutoff(store, engine) -> None:  # noqa: F811
    _, t, s = w402._setup(store, engine)
    inputs = build_chain_inputs(URL)
    run = _run_id(engine, t, s)
    lo = datetime(2026, 11, 1, 21, tzinfo=UTC)  # a window no set-up selection covers
    hi = lo + timedelta(days=1)
    try:
        # residual 1: a selection is invisible at any cutoff before its selected_at
        at = _select(engine, t, s, run, "dispatch", lo, hi)
        assert inputs.selected_windows(_ctx(t, s, lo, hi, at - timedelta(microseconds=1)), ["dispatch"]) == []
        assert [w[:2] for w in inputs.selected_windows(_ctx(t, s, lo, hi, at), ["dispatch"])] == [(lo, hi)]
        # residual 2: a live job is cleared only by a later selection of one of its own domain's analytics
        lo2, hi2 = lo + timedelta(days=2), hi + timedelta(days=2)
        available = _now(engine)
        _job(engine, t, s, "dispatch", lo2, hi2, available)
        ctx = lambda k: _ctx(t, s, lo2, hi2, k)  # noqa: E731
        assert inputs.pending_jobs(ctx(_now(engine)), ["dispatch"]) is True
        assert inputs.pending_jobs(ctx(available - timedelta(microseconds=1)), ["dispatch"]) is False  # not yet
        other = _select(engine, t, s, run, "cold-excursion", lo2, hi2)  # another analytic over the same window
        assert inputs.pending_jobs(ctx(other), ["dispatch"]) is True
        own = _select(engine, t, s, run, "dispatch", lo2, hi2)
        assert inputs.pending_jobs(ctx(own - timedelta(microseconds=1)), ["dispatch"]) is True
        assert inputs.pending_jobs(ctx(own), ["dispatch"]) is False
        # a job that becomes available after the cutoff is not pending at it
        lo3, hi3 = lo + timedelta(days=4), hi + timedelta(days=4)
        k = _now(engine)
        _job(engine, t, s, "dispatch", lo3, hi3, k + timedelta(hours=1))
        assert inputs.pending_jobs(_ctx(t, s, lo3, hi3, k + timedelta(minutes=1)), ["dispatch"]) is False
        assert inputs.pending_jobs(_ctx(t, s, lo3, hi3, k + timedelta(hours=2)), ["dispatch"]) is True
    finally:
        inputs.dispose()


def test_m1_tue_only_asset_measure_writes_not_expected_per_subject_on_a_monday(store, engine) -> None:  # noqa: F811
    import test_walk1_productive_producer_postgres as walk1  # the Kobo producer: the Grain mill is productive

    result = walk1.pgb.imported(store, when=walk1.IMPORT_AT)
    walk1.pgb.convert(store, walk1.pgb.BindingService(store, walk1.pgb.Clock(walk1.INSTALL_AT)), result.tenant,
                      result.site, walk1.pgb.FIXTURE)
    walk1.producer.configure_at(store, result, walk1.INSTALL_AT)
    t, s = result.tenant.id, result.site.id
    code, zone = result.site.site_code, result.site.timezone
    loaded = load_operating_calendar()
    tue_only = replace(loaded, sites={**loaded.sites, code: replace(loaded.entry_for(code), days=frozenset({"TUE"}))})
    inputs, snaps = build_chain_inputs(URL), PostgresSnapshotStore(URL)
    monday, tuesday = date(2026, 10, 12), date(2026, 10, 13)
    assert monday.weekday() == 0
    try:
        builder = SnapshotBuilder(snaps, build_measure_set(inputs), load_coverage_policy(), tue_only)
        site = SiteRef(t, s, code, "MINIGRID", zone)
        on_tuesday = builder.build(t, site, tuesday, "productive_kwh")
        on_monday = builder.build(t, site, monday, "productive_kwh")
        subjects = sorted(w.row.subject_ref for w in on_tuesday)
        assert subjects and all(w.row.subject_kind == "ASSET" for w in on_tuesday)
        # the subjects resolve at the Site-local day start on a NOT_EXPECTED day: one row per subject
        assert sorted(w.row.subject_ref for w in on_monday) == subjects
        assert {w.row.grade for w in on_monday} == {"NOT_EXPECTED"} and all(w.written for w in on_monday)
        counts = SnapshotReader(snaps).grade_counts(t, s, monday, monday, ["productive_kwh", "daylight_headroom_kw"])
        body = counts.to_json()
        assert (body["not_expected"], body["no_data"], body["expected"]) == (1, 0, 0), body
    finally:
        inputs.dispose()
        snaps.dispose()


# --- M2: event-driven chain_threads on real Finding and Action rows ----------------------------------------------


def _thread_events(engine, s) -> list:
    with engine.connect() as c:
        return c.execute(text("SELECT event_id, type, subject FROM event_outbox WHERE site_id = :s AND type IN "
                              "('finding.revised', 'opportunity.revised', 'action.event') ORDER BY recorded_at, "
                              "event_id"), {"s": s}).all()


def _placed(engine) -> set:
    with engine.connect() as c:
        return set(c.execute(text("SELECT finding_id FROM finding_thread_occurrence")).scalars())


def _linked(engine) -> int:
    with engine.connect() as c:
        return c.execute(text("SELECT count(*) FROM chain_action WHERE thread_id IS NOT NULL")).scalar_one()


def test_m2_threads_place_only_named_revisions_and_link_an_action_recorded_before_its_finding(
        seeded, engine) -> None:  # noqa: F811
    """F01 and F02 are real Finding revisions; F01 has a real Mini-grid trial and a domain Action. F01's own
    finding.revised event is consumed out of the way first, so its Actions' events arrive while F01 is unplaced
    (PENDING_PLACEMENT). A later finding.revised naming F01's revisions places F01 and links both Actions."""
    from assetops_backend.scheduling import stages

    runner, _, _, f01, _ = seeded
    t, s = runner.tenant, runner.site
    ids = {"tenant_id": str(t), "site_id": str(s), "limit": 500}
    with engine.connect() as c:
        f01_revs = {str(r) for r in c.execute(text("SELECT id FROM finding_revision WHERE finding_id = :f"),
                                              {"f": f01}).scalars()}
        f02 = c.execute(text("SELECT DISTINCT finding_id FROM finding_revision WHERE site_id = :s AND finding_id <> :f"),
                        {"s": s, "f": f01}).scalars().all()
    assert len(f02) == 1
    evs = _thread_events(engine, s)
    kinds = [e.type for e in evs]
    assert "finding.revised" in kinds and "action.event" in kinds, kinds
    f01_events = [e for e in evs if e.type == "finding.revised" and set(e.subject["ids"]) & f01_revs]
    assert f01_events and all(set(e.subject["ids"]) <= f01_revs for e in f01_events)
    with engine.begin() as c:  # F01's placement event is consumed out of the way: F01 stays unplaced
        for e in f01_events:
            c.execute(text("INSERT INTO event_consumption (consumer, event_id) VALUES ('threads', :e)"),
                      {"e": e.event_id})
    first = stages.chain_threads(URL, ids)
    assert first["code"] == "OK" and first["deferred"] == 0, first
    assert _placed(engine) == set(f02)  # only the named (F02) revisions are placed
    assert _linked(engine) == 0 and first["steps"][1]["counts"].get("PENDING_PLACEMENT", 0) >= 2, first
    with engine.begin() as c:  # a later finding.revised naming F01's revisions (the producer's subject shape)
        c.execute(text(
            "INSERT INTO event_outbox (type, schema_version, occurred_at, source, tenant_id, site_id, subject, "
            "idempotency_key) SELECT type, schema_version, occurred_at, 'ch1b-fix-test', tenant_id, site_id, "
            "subject, 'replay-' || event_id FROM event_outbox WHERE event_id = :e"), {"e": f01_events[-1].event_id})
    second = stages.chain_threads(URL, ids)
    assert second["code"] == "OK" and second["consumed"]["threads"]["consumed"] == 1, second
    assert _placed(engine) == set(f02) | {f01}
    assert second["steps"][1]["counts"].get("LINKED") == 2 and _linked(engine) == 2, second
    rerun = stages.chain_threads(URL, ids)
    assert rerun["consumed"]["threads"]["consumed"] == 0 and rerun["processed"] == 0, rerun


def test_threads_stage_consumes_an_ineligible_opportunity_event_as_skipped(store, engine) -> None:  # noqa: F811
    """CH-4 merge (review M3, ruling CH1b-R2 4): study A's revision is below the eligible-day minimum, so its
    `opportunity.revised` event places nothing and is consumed, reported as `skipped_ineligible`, never a failure."""
    import test_ch4_opportunity_postgres as ch4
    from assetops_backend.scheduling import stages

    seed = ch4.seed_opportunities(store, engine)
    t, s = seed["t"], seed["s"]
    evs = [e for e in _thread_events(engine, s) if e.type == "opportunity.revised"]
    only_a = [e for e in evs if e.subject["ids"] == [str(seed["a_r1"])]]
    assert len(evs) == 3 and len(only_a) == 1, evs  # A r1, B r1, B r2, one event per statement
    ids = {"tenant_id": str(t), "site_id": str(s), "limit": 500}
    first = stages.chain_threads(URL, ids)
    assert first["code"] == "OK" and first["deferred"] == 0, first
    assert first["consumed"]["threads"]["by_type"] == {"opportunity.revised@1": 3}, first
    assert first["steps"][0]["skipped_ineligible"] == 1, first
    with engine.connect() as c:
        occurrences = c.execute(text("SELECT count(*) FROM finding_thread_occurrence WHERE site_id = :s"), {"s": s}).scalar_one()
        consumed = c.execute(text("SELECT count(*) FROM event_consumption WHERE consumer = 'threads' "
                                  "AND event_id = :e"), {"e": only_a[0].event_id}).scalar_one()
    assert occurrences == 1 and consumed == 1  # study B only; A's event is consumed
    rerun = stages.chain_threads(URL, ids)
    assert rerun["consumed"]["threads"]["consumed"] == 0 and rerun["processed"] == 0, rerun
