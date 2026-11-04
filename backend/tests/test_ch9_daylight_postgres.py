"""CH-9 u1 (build sheet CH-9 §9 R1-R3, §10 CH9-R2 Q2-Q4): migration `0046_daylight_enqueue` and
`store.daylight_hours` on a fresh database (`pg_harness.fresh_database()` through the `engine` fixture).

- 0046 enqueues renewable work for an hour holding a positive accepted `pv_available_power` reading, also when a
  later renewable-role reading lands in such an hour, and refuses a renewable hour without one;
- a Site with no `pv_available_power` binding keeps the noon hour, exactly as 0029;
- `daylight_hours` reads the declared operating hours: a gap is a missing hour, a zero hour is not daylight, the
  cutoff is `received_at <= k`;
- the downgrade restores the 0029 bodies.

Requires ASSETOPS_TEST_DATABASE_URL.
"""

from __future__ import annotations

import os
from datetime import date, datetime, time, timedelta, timezone
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError
    from test_s1_bindings_postgres import _alembic, engine, store  # noqa: F401
    from test_s4_consequence_store_postgres import site  # noqa: F401
    from test_w203_cold_migration_postgres import _replica, head, scalar
    from test_w402_migration_postgres import clear_mini, functiondef, mg, mg4, mg4_nopv, mini_jobs  # noqa: F401

    from assetops_backend.mini_depth.store import daylight_hours

DAY = date(2026, 10, 20)  # clear of the fixture Site's own 2026-10-06/08 rows
PV = "pv_available_power"


def at(mg, hour: int, minute: int = 0) -> datetime:
    return datetime.combine(DAY, time(hour, minute), tzinfo=ZoneInfo(mg.tz)).astimezone(timezone.utc)


def reading(mg, c, *, role: str, lo: datetime, hi: datetime | None, value: str, decided: datetime,
            received: datetime | None = None):
    """One accepted interval reading in the S2 writer's shape (`Ev.write`, with value, interval and receipt)."""
    mg.ordinal += 1
    eid, msg = uuid4(), f"w206-enq-{uuid4()}"
    over = {"id": ":id", "ordinal": ":o", "message_id": ":m", "sequence": ":seq", "role": ":role",
            "source_time": ":lo", "published_at": ":rec", "received_at": ":rec", "interval_start": ":lo",
            "interval_end": ":hi", "asset_id": ":asset", "normalized_value_text": ":v", "normalized_unit": "'kW'",
            "quality": "'GOOD'"}
    cols = ", ".join(mg.columns)
    values = ", ".join(over.get(col, col) for col in mg.columns)
    c.execute(text(f"INSERT INTO accepted_evidence ({cols}) SELECT {values} FROM accepted_evidence "
                   "WHERE id = :template"),
              {"id": eid, "o": mg.ordinal, "m": msg, "seq": 10_000_000 + mg.ordinal, "role": role, "lo": lo,
               "hi": hi, "rec": received or (hi or lo) + timedelta(minutes=1), "v": value,
               "template": mg.template, "asset": mg.ctx.connector})
    mg.dispose(c, eid, msg, "ACCEPTED", decided)
    return eid


def hour_reading(mg, hour: int, value: str, *, role: str = PV, received: datetime | None = None):
    lo = at(mg, hour)
    with mg.engine.begin() as c:
        return reading(mg, c, role=role, lo=lo, hi=lo + timedelta(hours=1), value=value,
                       decided=lo + timedelta(hours=2), received=received)


def renewable(engine, mg) -> list[datetime]:  # noqa: F811
    return sorted(j["window_start"] for j in mini_jobs(engine, mg.ctx.s) if j["domain"] == "mini_renewable")


@pytest.fixture()
def pv(mg4, engine):  # noqa: F811
    """`mg4` with one `pv_available_power` binding added to its current roles-4 set (test-only, as replica)."""
    mg = mg4
    with engine.connect() as c:
        set_id = c.execute(text("SELECT id FROM signal_binding_set_revision WHERE site_id = :s "
                                "AND superseded_at IS NULL ORDER BY id LIMIT 1"), {"s": mg.ctx.s}).scalar_one()
        template = c.execute(text("SELECT id FROM signal_binding_revision WHERE binding_set_revision_id = :b "
                                  "ORDER BY id LIMIT 1"), {"b": set_id}).scalar_one()
        cols = [r[0] for r in c.execute(text(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'signal_binding_revision' "
            "ORDER BY ordinal_position"))]
        bound = c.execute(text("SELECT count(*) FROM signal_binding_revision WHERE binding_set_revision_id = :b "
                               "AND role = :r AND valid_to IS NULL"), {"b": set_id, "r": PV}).scalar_one()
    new = uuid4()
    over = {"id": f"'{new}'", "role": f"'{PV}'", "signal_id": "'ch9-pv-available'", "valid_to": "NULL"}
    if not bound:
        _replica(engine, f"INSERT INTO signal_binding_revision ({', '.join(cols)}) SELECT "
                         f"{', '.join(over.get(x, x) for x in cols)} FROM signal_binding_revision "
                         f"WHERE id = '{template}'")
    yield mg
    clear_mini(engine)
    _replica(engine, f"DELETE FROM signal_binding_revision WHERE id = '{new}'")


def test_0046_is_head_and_replaces_the_noon_only_bodies(engine) -> None:  # noqa: F811
    assert head(engine) == "0046_daylight_enqueue"
    assert "12:00 hour only" not in functiondef(engine, "mini_enqueue_hour")
    for name in ("mini_enqueue_hour", "mini_enqueue_accepted", "mini_enqueue_configuration"):
        assert "mini_renewable_hour" in functiondef(engine, name), name
    assert scalar(engine, "SELECT count(*) FROM pg_trigger WHERE tgname = 'enqueue_mini_depth'") == 1


def test_site_without_pv_binding_keeps_noon(mg4_nopv, engine) -> None:  # noqa: F811
    mg = mg4_nopv
    hour_reading(mg, 9, "5.0", role="feeder_demand")
    hour_reading(mg, 12, "5.0", role="feeder_demand")
    assert renewable(engine, mg) == [at(mg, 12)]
    with engine.connect() as c:
        found = daylight_hours(c, mg.ctx.t, mg.ctx.s, DAY, at(mg, 23) + timedelta(days=1))
    assert (found.hours, found.missing, found.measured) == ((12,), (), False)


def test_positive_pv_hours_enqueue_and_late_feeder(pv, engine) -> None:  # noqa: F811
    mg = pv
    hour_reading(mg, 3, "0")
    hour_reading(mg, 9, "12.5")
    hour_reading(mg, 12, "5.0", role="feeder_demand")  # noon without positive PV: no renewable work
    assert renewable(engine, mg) == [at(mg, 9)]
    clear_mini(engine)
    late = hour_reading(mg, 9, "4.0", role="feeder_demand")  # a later renewable-role row in a positive-PV hour
    jobs = [j for j in mini_jobs(engine, mg.ctx.s, cause=late) if j["domain"] == "mini_renewable"]
    assert [j["window_start"] for j in jobs] == [at(mg, 9)]


def test_enqueue_hour_refuses_a_renewable_hour_without_positive_pv(pv, engine) -> None:  # noqa: F811
    mg = pv
    hour_reading(mg, 3, "0")
    for hour in (3, 12):
        with pytest.raises(DBAPIError, match="positive pv_available_power"):
            with engine.begin() as c:
                c.execute(text("SELECT mini_enqueue_hour(:t, :s, 'mini_renewable', :lo, :hi, NULL, now())"),
                          mg.ctx.p(lo=at(mg, hour), hi=at(mg, hour + 1)))
    hour_reading(mg, 10, "1")
    clear_mini(engine)
    with engine.begin() as c:
        c.execute(text("SELECT mini_enqueue_hour(:t, :s, 'mini_renewable', :lo, :hi, NULL, now())"),
                  mg.ctx.p(lo=at(mg, 10), hi=at(mg, 11)))
    assert renewable(engine, mg) == [at(mg, 10)]


def test_daylight_hours_measured_from_pv_available(pv, engine) -> None:  # noqa: F811
    mg = pv
    # Bindings are read as known at the cutoff, and the fixture's were recorded at the database clock: receive the
    # day's rows after that.
    received = scalar(engine, "SELECT now()") + timedelta(minutes=5)
    with engine.begin() as c:
        for hour in range(24):
            if hour == 12:
                continue  # a gap: the noon hour is missing, never non-daylight
            value = "40" if 6 <= hour < 18 else "0"
            if hour == 6:  # dawn: a zero half then a positive half; covered, not daylight
                reading(mg, c, role=PV, lo=at(mg, 6), hi=at(mg, 6, 30), value="0", decided=received,
                        received=received)
                reading(mg, c, role=PV, lo=at(mg, 6, 30), hi=at(mg, 7), value="3", decided=received,
                        received=received)
                continue
            if hour == 15:  # a 30-minute hole inside a positive hour: missing
                reading(mg, c, role=PV, lo=at(mg, 15), hi=at(mg, 15, 30), value=value, decided=received,
                        received=received)
                continue
            reading(mg, c, role=PV, lo=at(mg, hour), hi=at(mg, hour + 1) if hour < 23 else at(mg, 23) + timedelta(
                hours=1), value=value, decided=received, received=received)
    with engine.connect() as c:
        found = daylight_hours(c, mg.ctx.t, mg.ctx.s, DAY, received)
        before = daylight_hours(c, mg.ctx.t, mg.ctx.s, DAY, received - timedelta(seconds=1))
    assert found.hours == (7, 8, 9, 10, 11, 13, 14, 16, 17)
    assert found.missing == (12, 15)
    assert found.measured
    # The cutoff is `received_at <= k`: before the rows are received, every operating hour is missing (GAP-K7).
    assert (before.hours, before.missing) == ((), tuple(range(24)))


def test_downgrade_restores_the_0029_bodies(engine) -> None:  # noqa: F811
    from alembic import command

    config = _alembic()
    engine.dispose()
    try:
        command.downgrade(config, "0044_chain_events")
        assert "12:00 hour only" in functiondef(engine, "mini_enqueue_hour")
        assert "extract(hour FROM h) = 12" in functiondef(engine, "mini_enqueue_accepted")
        assert scalar(engine, "SELECT count(*) FROM pg_proc WHERE proname = 'mini_renewable_hour'") == 0
    finally:
        command.upgrade(config, "head")
    assert head(engine) == "0046_daylight_enqueue"
