"""CH-1a L2 (build sheet §6 step 2, ruling Q8): the 0043 catalogue, the insert-only store, the downgrade refusal,
the builder with a stub chain input reader against the real store (productive_kwh, idempotency, revision 2), the
real noon-headroom adapter on MG-W402-001, and `grade_counts_many` in one statement.

Needs `ASSETOPS_TEST_DATABASE_URL` naming a `*_test` database; skipped otherwise.
"""
from __future__ import annotations

import os
from datetime import date, datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import event, text
    from sqlalchemy.exc import DBAPIError
    from test_s1_bindings_postgres import engine, store  # noqa: F401

    import pg_harness
    import test_w402_reads_postgres as w402
    from assetops_backend.chain.adapters.postgres_snapshot_store import PostgresSnapshotStore
    from assetops_backend.chain.builder import SnapshotBuilder
    from assetops_backend.chain.composition import (
        build_chain_inputs,
        load_coverage_policy,
        load_operating_calendar,
    )
    from assetops_backend.chain.measure_impls import build_measure_set
    from assetops_backend.chain.ports import SiteRef
    from assetops_backend.chain.reader import SnapshotReader

ASSET = str(uuid4())
PRICE_REV = str(uuid4())
DAYS3 = [date(2026, 10, 6), date(2026, 10, 7), date(2026, 10, 8)]


def _midnight(day: date) -> datetime:  # Africa/Nairobi is UTC+3
    return datetime(day.year, day.month, day.day, tzinfo=timezone.utc) - timedelta(hours=3)


class StubInputs:
    """A stub ChainInputReader for productive_kwh only (ruling Q8)."""

    def __init__(self, hours_by_day: dict[date, int], kw: str = "10") -> None:
        self.hours_by_day, self.kw, self.extra = hours_by_day, kw, {}

    def productive_assets(self, ctx):
        return [{"asset_id": ASSET, "asset_code": "LOAD-1", "name": "Mill"}]

    def feeder_demand_readings(self, ctx, asset_id):
        start = _midnight(ctx.local_day)
        hours = self.hours_by_day.get(ctx.local_day, 0)
        rows = [{"evidence_id": f"{ctx.local_day}-{i}", "asset_id": asset_id, "start": start + timedelta(hours=i),
                 "end": start + timedelta(hours=i + 1), "value_kw": self.kw, "quality": "GOOD"}
                for i in range(hours)]
        return rows + self.extra.get(ctx.local_day, [])

    def declared_price(self, ctx, key):
        assert key == "productive_use_price_per_kwh"
        return {"state": "PRICED", "revision_id": PRICE_REV, "price": {"value": "0.25", "currency": "USD"}}

    def pending_jobs(self, ctx, domains):
        return False


def _builder(adapters_from, snapshot_store):
    return SnapshotBuilder(snapshot_store, build_measure_set(adapters_from), load_coverage_policy(),
                           load_operating_calendar())


def _site(t, s, code=w402.CODE):
    return SiteRef(t, s, code, "MINIGRID", w402.ZONE)


def test_0043_catalogue_and_insert_only(store, engine) -> None:  # noqa: F811
    with engine.connect() as c:
        cols = {r[0] for r in c.execute(text("SELECT column_name FROM information_schema.columns "
                                             "WHERE table_name = 'site_day_snapshot'"))}
        checks = c.execute(text("SELECT count(*) FROM pg_constraint WHERE conrelid = 'site_day_snapshot'::regclass "
                                "AND contype = 'c'")).scalar_one()
        indexes = {r[0] for r in c.execute(text("SELECT indexname FROM pg_indexes WHERE tablename IN "
                                                "('site_day_snapshot', 'accepted_evidence')"))}
        trigger = c.execute(text("SELECT tgname FROM pg_trigger WHERE tgrelid = 'site_day_snapshot'::regclass "
                                 "AND NOT tgisinternal")).scalars().all()
    assert {"tenant_id", "site_id", "local_day", "subject_kind", "subject_ref", "measure", "evidence_class",
            "revision", "expected", "required_seconds", "covered_seconds", "coverage_pct", "grade", "value", "money",
            "policy_version", "calendar_version", "catalogue_version", "input_fp", "computed_at"} <= cols
    assert checks >= 12, checks
    assert {"site_day_snapshot_read", "accepted_evidence_site_role_time"} <= indexes
    assert trigger == ["site_day_snapshot_immutable"]

    _, t, s = w402._setup(store, engine)
    snaps = PostgresSnapshotStore(URL)
    try:
        _builder(StubInputs({DAYS3[0]: 8}), snaps).build(t, _site(t, s), DAYS3[0], "productive_kwh")
        for sql in ("UPDATE site_day_snapshot SET grade = 'LOW'", "DELETE FROM site_day_snapshot"):
            with pytest.raises(DBAPIError):
                with engine.begin() as c:
                    c.execute(text(sql))
        with engine.begin() as c:  # a refused CHECK: NO_DATA with covered seconds
            with pytest.raises(DBAPIError):
                with c.begin_nested():
                    c.execute(text(
                        "INSERT INTO site_day_snapshot (tenant_id, site_id, local_day, subject_kind, subject_ref, "
                        "measure, evidence_class, revision, expected, required_seconds, covered_seconds, coverage_pct, "
                        "grade, policy_version, calendar_version, catalogue_version, input_fp) VALUES (:t, :s, "
                        "'2026-10-09', 'SITE', 'SITE', 'daylight_headroom_kw', 'MEASURED', 1, true, 3600, 60, 1.67, "
                        "'NO_DATA', 'p', 'c', 1, :fp)"), {"t": t, "s": s, "fp": "a" * 64})
    finally:
        snaps.dispose()


def test_productive_builder_idempotent_and_revision_two(store, engine) -> None:  # noqa: F811
    _, t, s = w402._setup(store, engine)
    snaps = PostgresSnapshotStore(URL)
    try:
        stub = StubInputs({DAYS3[0]: 8, DAYS3[1]: 24, DAYS3[2]: 0})
        builder, site = _builder(stub, snaps), _site(t, s)
        first = builder.build_range(t, site, DAYS3[0], DAYS3[-1], ["productive_kwh"])
        assert [w.written for w in first] == [True, True, True]
        rows = {w.row.local_day: w.row for w in first}
        a, b, c = (rows[d] for d in DAYS3)
        assert (a.grade, a.covered_seconds, a.required_seconds, a.coverage_pct) == ("PARTIAL", 28800, 86400, "33.33")
        assert a.value == {"kwh": "80.000", "measured_seconds": 28800}
        assert a.money == {"amount": "20.00", "currency": "USD", "assumption_revision_id": PRICE_REV}
        assert (b.grade, b.value["kwh"], b.money["amount"]) == ("COMPLETE", "240.000", "60.00")
        assert (c.grade, c.value, c.money) == ("NO_DATA", None, None)
        assert all(r.subject_kind == "ASSET" and r.subject_ref == ASSET and r.revision == 1 for r in rows.values())

        again = builder.build_range(t, site, DAYS3[0], DAYS3[-1], ["productive_kwh"])
        assert [w.written for w in again] == [False, False, False]

        start = _midnight(DAYS3[2])
        stub.extra[DAYS3[2]] = [{"evidence_id": "late-1", "asset_id": ASSET, "start": start,
                                 "end": start + timedelta(minutes=30), "value_kw": "0", "quality": "GOOD"}]
        third = builder.build_range(t, site, DAYS3[0], DAYS3[-1], ["productive_kwh"])
        assert [w.written for w in third] == [False, False, True]
        late = third[-1].row
        assert (late.revision, late.grade, late.value) == (2, "LOW", {"kwh": "0.000", "measured_seconds": 1800})
        assert late.money == {"amount": "0.00", "currency": "USD", "assumption_revision_id": PRICE_REV}  # Q7

        reader = SnapshotReader(snaps)
        counts = reader.grade_counts(t, s, DAYS3[0], DAYS3[-1], ["productive_kwh"]).to_json()
        assert counts["requested"] == 3 and counts["complete"] == 1 and counts["partial"] == 1
        assert counts["low"] == 1 and counts["enough_data_days"] == 1, counts
        latest = reader.latest(t, s, DAYS3[0], DAYS3[-1], ["productive_kwh"])
        assert sorted(r.revision for r in latest) == [1, 1, 2]
    finally:
        snaps.dispose()


def test_noon_headroom_real_adapter_and_grade_counts_many(store, engine) -> None:  # noqa: F811
    installed, t, s = w402._setup(store, engine)
    w402._ingest(engine, installed)
    w402._reconcile(engine, w402.DAYS)
    body = w402._read(engine, t, s, "renewable", w402._midnight(w402.DAYS[0]),
                      w402._midnight(w402.DAYS[-1] + timedelta(days=1)))
    decisions = {r["local_day"]: r["decision"] for r in body["rows"]} if body["rows"] and "local_day" in \
        body["rows"][0] else None
    snaps = PostgresSnapshotStore(URL)
    inputs = build_chain_inputs(URL)
    try:
        builder, site = _builder(inputs, snaps), _site(t, s)
        out = builder.build_range(t, site, w402.DAYS[0], w402.DAYS[-1], ["daylight_headroom_kw"])
        assert len(out) == 5 and all(w.written for w in out)
        for w in out:
            r = w.row
            assert (r.subject_kind, r.subject_ref, r.required_seconds) == ("SITE", "SITE", 3600)
            assert r.grade in ("COMPLETE", "PARTIAL", "LOW"), r
            assert r.value["decision"] in ("ELIGIBLE", "EXCLUDED") and r.money is None
            assert r.value["low_kw"] is not None and r.value["high_kw"] is not None
            if decisions is not None:
                assert r.value["decision"] == decisions[r.local_day.isoformat()]
        assert sorted(w.row.value["decision"] for w in out) == sorted(x["decision"] for x in body["rows"])
        assert not any(w.written for w in builder.build_range(t, site, w402.DAYS[0], w402.DAYS[-1],
                                                              ["daylight_headroom_kw"]))
        # a stub productive measure on the same Site, so the day counts cover two measures
        _builder(StubInputs({d: 24 for d in w402.DAYS}), snaps).build_range(
            t, site, w402.DAYS[0], w402.DAYS[-1], ["productive_kwh"])

        reader = SnapshotReader(snaps)
        other = uuid4()
        measures = {s: ["productive_kwh", "daylight_headroom_kw"], other: ["daylight_headroom_kw"]}
        statements: list[str] = []

        def count(conn, cursor, statement, *args):
            statements.append(statement)

        event.listen(snaps._engine, "before_cursor_execute", count)
        try:
            many = reader.grade_counts_many(t, [s, other], w402.DAYS[0], w402.DAYS[-1], measures)
        finally:
            event.remove(snaps._engine, "before_cursor_execute", count)
        assert len([x for x in statements if "site_day_snapshot" in x]) == 1, statements
        for site_id in (s, other):
            assert many[site_id] == reader.grade_counts(t, site_id, w402.DAYS[0], w402.DAYS[-1], measures[site_id])
        assert many[other].to_json()["no_data"] == 5 and many[s].to_json()["requested"] == 5
    finally:
        inputs.dispose()
        snaps.dispose()


def test_downgrade_refused_with_rows_then_allowed(store, engine) -> None:  # noqa: F811
    from alembic import command

    _, t, s = w402._setup(store, engine)
    snaps = PostgresSnapshotStore(URL)
    try:
        _builder(StubInputs({DAYS3[0]: 8}), snaps).build(t, _site(t, s), DAYS3[0], "productive_kwh")
    finally:
        snaps.dispose()
    cfg = pg_harness._alembic(URL)
    # CH-1b: 0044 sits above 0043 and refuses first while the seeded facts' outbox events exist
    with pytest.raises(Exception, match="event history exists"):
        command.downgrade(cfg, "0041_walk1_objective_min_days")
    with engine.begin() as c:
        c.execute(text("TRUNCATE event_consumption, snapshot_dirty, event_outbox"))
    with pytest.raises(Exception, match="snapshot history exists"):
        command.downgrade(cfg, "0041_walk1_objective_min_days")
    with engine.begin() as c:  # TRUNCATE is not a row DELETE; the append-only trigger does not fire on it
        c.execute(text("TRUNCATE site_day_snapshot"))
    command.downgrade(cfg, "0041_walk1_objective_min_days")
    with engine.connect() as c:
        assert c.execute(text("SELECT to_regclass('site_day_snapshot')")).scalar_one() is None
    command.upgrade(cfg, "head")
    pg_harness.assert_at_head(engine)
    assert isinstance(UUID(str(s)), UUID)
