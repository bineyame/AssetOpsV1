"""DD3c part 2 (D-DD.108 Q1, D-DD.109): migration `0074_unit_role_sets` and every reach of the mini-depth gate,
on a fresh database (`pg_harness.fresh_database()` through the `engine` fixture).

The Site is the KOBO-001 `PowerSite` fixture (the 0029/0048 tests' Site); its current binding sets are relabelled
`minigrid-roles-4` or `minigrid-roles-5` as replica (as `mg4` does), so one Site is read under each set name with
the same rows. Goldens (`fixtures/dd3c/role-sets-golden.json`) were captured on main before the change, under
roles-4 (`ASSETOPS_DD3C_CAPTURE=<path>` writes them); each roles-5 result must equal its roles-4 golden.

- T1 roles-4 unchanged: the job rows (domain, window, cause) equal main's, and again after downgrade-upgrade.
- T2 roles-5 one set: the same job rows as roles-4, from evidence and from publish (`mini_enqueue_configuration`,
  the call a publish makes).
- T3 both sets (D-DD.108 Q1): a roles-4 and a roles-5 set over one hour on one Site: no job; Python refuses.
- T4 other sets: roles-1..3, a cold and an EV Site enqueue nothing, as on main.
- T5 renewable hour on two inverters: a positive `pv_available_power` on either unit makes the hour renewable; on
  neither, not; unbound, the 12:00 rule.
- T7 coverage: the dispatch input set's role coverage under roles-5 equals roles-4's after normalising.
- P1-P4: the Python readers (`read_hour_rows`, `load_hour_inputs`, `_hour_ids`, `feeder_month`, `daylight_hours`)
  read a roles-5 set as they read the same rows under roles-4.

Requires ASSETOPS_TEST_DATABASE_URL. T6 (migration text) is `test_dd3c_migration_0074.py`.
"""

from __future__ import annotations

import json
import os
import re
from contextlib import contextmanager
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL not set")

if URL:
    from sqlalchemy import text
    import pg_harness
    from test_s1_bindings_postgres import _alembic, engine, store  # noqa: F401
    from test_s4_consequence_store_postgres import site  # noqa: F401
    from test_w203_cold_migration_postgres import _replica, head, scalar
    from test_w402_migration_postgres import clear_mini, mg, mini_jobs, set_type  # noqa: F401

GOLDEN = Path(__file__).resolve().parent / "fixtures" / "dd3c" / "role-sets-golden.json"
CAPTURE = os.environ.get("ASSETOPS_DD3C_CAPTURE")
R4, R5 = "minigrid-roles-4", "minigrid-roles-5"
PV = "pv_available_power"
DAY = date(2026, 10, 21)  # clear of the fixture Site's own 2026-10-06/08 rows and of CH-9's 2026-10-20
EVIDENCE_DAY = datetime(2026, 10, 6, tzinfo=timezone.utc)  # the fixture Site's own dispatch evidence
_UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.I)


# --- normalising and goldens ---------------------------------------------------------------------------------------

def normalise(value) -> str:
    """D-DD.45's normaliser: `sort_keys`, UUIDs as `uuid-<n>` in first-appearance order, the role-set name as
    `<role-set>`."""
    raw = json.dumps(value, sort_keys=True, default=str)
    seen: dict[str, str] = {}
    raw = _UUID.sub(lambda m: seen.setdefault(m.group(0).lower(), f"uuid-{len(seen) + 1}"), raw)
    return raw.replace(R4, "<role-set>").replace(R5, "<role-set>")


def check(key: str, got) -> None:
    """Capture mode records `got` under `key`; otherwise `got` must equal the golden byte for byte."""
    if CAPTURE:
        path = Path(CAPTURE)
        held = json.loads(path.read_text()) if path.exists() else {}
        held[key] = got
        path.write_text(json.dumps(held, indent=1, sort_keys=True) + "\n")
        return
    assert normalise(got) == normalise(json.loads(GOLDEN.read_text())[key]), key


# --- the Site under one set name -----------------------------------------------------------------------------------

def at(mg, day: date, hour: int) -> datetime:
    return datetime.combine(day, time(hour), tzinfo=ZoneInfo(mg.tz)).astimezone(timezone.utc)


@contextmanager
def labelled(engine, mg, role_set: str):  # noqa: F811
    """The Site's current binding sets relabelled `role_set` (test-only, as replica); restored after."""
    with engine.connect() as c:
        prior = c.execute(text("SELECT id, role_set FROM signal_binding_set_revision WHERE site_id = :s "
                               "AND superseded_at IS NULL"), {"s": mg.ctx.s}).all()
    assert prior
    _replica(engine, f"UPDATE signal_binding_set_revision SET role_set = '{role_set}' WHERE id IN ("
             + ", ".join(f"'{i}'" for i, _ in prior) + ")")
    try:
        yield mg
    finally:
        clear_mini(engine)
        _replica(engine, *[f"UPDATE signal_binding_set_revision SET role_set = '{rs}' WHERE id = '{i}'"
                           for i, rs in prior])


def covering_set(engine, mg):  # noqa: F811
    lo, hi = at(mg, DAY, 0), at(mg, DAY + timedelta(days=1), 0)
    with engine.connect() as c:
        return c.execute(text("SELECT id FROM signal_binding_set_revision WHERE site_id = :s AND superseded_at IS "
                              "NULL AND valid_from <= :lo AND (valid_to IS NULL OR valid_to >= :hi)"),
                         {"s": mg.ctx.s, "lo": lo, "hi": hi}).scalar_one()


@contextmanager
def pv_units(engine, mg, n: int):  # noqa: F811
    """The Site's `pv_available_power` bindings replaced by `n` (0, 1 or 2) on distinct assets of the covering set
    (test-only, as replica); returns the assets. Restored after."""
    set_id = covering_set(engine, mg)
    with engine.connect() as c:
        old = [r[0] for r in c.execute(text("SELECT id FROM signal_binding_revision WHERE site_id = :s AND role = :r"),
                                       {"s": mg.ctx.s, "r": PV})]
        template = c.execute(text("SELECT id FROM signal_binding_revision WHERE binding_set_revision_id = :b "
                                  "AND valid_to IS NULL ORDER BY id LIMIT 1"), {"b": set_id}).scalar_one()
        cols = [r[0] for r in c.execute(text(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'signal_binding_revision' "
            "ORDER BY ordinal_position"))]
        other = c.execute(text("SELECT id FROM asset WHERE site_id = :s AND id <> :a ORDER BY asset_code LIMIT 1"),
                          {"s": mg.ctx.s, "a": mg.ctx.connector}).scalar_one()
    assets = [mg.ctx.connector, other][:n]
    listed = ", ".join(f"'{i}'" for i in old) or "NULL"
    _replica(engine, f"UPDATE signal_binding_revision SET role = 'dd3c_unbound' WHERE id IN ({listed})")
    new = []
    for i, asset in enumerate(assets):
        bid = uuid4()
        new.append(bid)
        over = {"id": f"'{bid}'", "role": f"'{PV}'", "signal_id": f"'dd3c-pv-{i}'", "asset_id": f"'{asset}'",
                "valid_to": "NULL"}
        _replica(engine, f"INSERT INTO signal_binding_revision ({', '.join(cols)}) SELECT "
                         f"{', '.join(over.get(x, x) for x in cols)} FROM signal_binding_revision "
                         f"WHERE id = '{template}'")
    try:
        yield assets
    finally:
        clear_mini(engine)
        _replica(engine, f"DELETE FROM signal_binding_revision WHERE id IN ({', '.join(repr(str(b)) for b in new)})"
                 if new else "SELECT 1",
                 f"UPDATE signal_binding_revision SET role = '{PV}' WHERE id IN ({listed})")


def reading(mg, *, role: str, hour: int, value: str, asset=None):
    """One accepted hourly interval reading on DAY in the S2 writer's shape (CH-9's `reading`, with its asset)."""
    lo = at(mg, DAY, hour)
    hi = lo + timedelta(hours=1)
    mg.ordinal += 1
    eid, msg = uuid4(), f"w206-enq-{uuid4()}"
    over = {"id": ":id", "ordinal": ":o", "message_id": ":m", "sequence": ":seq", "role": ":role",
            "source_time": ":lo", "published_at": ":rec", "received_at": ":rec", "interval_start": ":lo",
            "interval_end": ":hi", "asset_id": ":asset", "normalized_value_text": ":v", "normalized_unit": "'kW'",
            "quality": "'GOOD'"}
    with mg.engine.begin() as c:
        c.execute(text(f"INSERT INTO accepted_evidence ({', '.join(mg.columns)}) SELECT "
                       f"{', '.join(over.get(col, col) for col in mg.columns)} FROM accepted_evidence "
                       "WHERE id = :template"),
                  {"id": eid, "o": mg.ordinal, "m": msg, "seq": 10_000_000 + mg.ordinal, "role": role, "lo": lo,
                   "hi": hi, "rec": hi + timedelta(minutes=1), "v": value, "template": mg.template,
                   "asset": asset or mg.ctx.connector})
        mg.dispose(c, eid, msg, "ACCEPTED", lo + timedelta(hours=2))
    return eid


def rows(engine, mg, labels: dict) -> list[list]:  # noqa: F811
    """The Site's mini job rows as (domain, window start, window end, cause label), in a fixed order."""
    return sorted([j["domain"], j["window_start"].isoformat(), j["window_end"].isoformat(),
                   labels.get(j["cause_evidence_id"], None if j["cause_evidence_id"] is None else "other")]
                  for j in mini_jobs(engine, mg.ctx.s))


#: The evidence scenario (T1, T2): role, local hour, value.
EVIDENCE = (("pv_available_power", 3, "0"), ("pv_available_power", 9, "12.5"), ("feeder_demand", 9, "5.0"),
            ("feeder_demand", 12, "5.0"), ("generator_power", 14, "7.0"))


def from_evidence(engine, mg) -> list[list]:  # noqa: F811
    labels = {reading(mg, role=r, hour=h, value=v): f"{r}@{h}" for r, h, v in EVIDENCE}
    return rows(engine, mg, labels)


def from_publish(engine, mg) -> list[list]:  # noqa: F811
    """The publish reach: `mini_enqueue_configuration` (called at publish) over DAY, retention from DAY + 1."""
    clear_mini(engine)
    with engine.begin() as c:
        c.execute(text("SELECT mini_enqueue_configuration(:t, :s, :f, :to, :at)"),
                  mg.ctx.p(f=at(mg, DAY, 0), to=at(mg, DAY + timedelta(days=1), 0),
                           at=at(mg, DAY + timedelta(days=1), 1)))
    return rows(engine, mg, {})


def scenario(engine, mg) -> dict:  # noqa: F811
    with pv_units(engine, mg, 1):
        got = {"evidence": from_evidence(engine, mg), "publish": from_publish(engine, mg)}
    assert got["evidence"] and got["publish"]  # non-empty: the gate opened
    return got


# --- T1, T2 --------------------------------------------------------------------------------------------------------

def test_t1_roles4_job_rows_unchanged_and_after_downgrade_upgrade(mg, engine) -> None:  # noqa: F811
    with labelled(engine, mg, R4):
        check("T1", scenario(engine, mg))
    if CAPTURE:
        return
    from alembic import command

    config = _alembic()
    engine.dispose()
    try:
        command.downgrade(config, "0073_named_option_levers")
    finally:
        command.upgrade(config, "head")
    assert head(engine) == pg_harness.alembic_head()
    _replica(engine, "DELETE FROM ingestion_disposition WHERE ordinal > 100000",
             "DELETE FROM accepted_evidence WHERE message_id LIKE 'w206-enq-%'")
    with labelled(engine, mg, R4):
        check("T1", scenario(engine, mg))


def test_t2_roles5_one_set_enqueues_as_roles4(mg, engine) -> None:  # noqa: F811
    if CAPTURE:
        pytest.skip("T2's golden is T1's (roles-4 on main)")
    with labelled(engine, mg, R5):
        check("T1", scenario(engine, mg))


# --- T3: both sets over one hour (D-DD.108 Q1) ---------------------------------------------------------------------

def test_t3_a_roles4_and_a_roles5_set_give_no_job_and_python_refuses(mg, engine) -> None:  # noqa: F811
    from assetops_backend.mini_depth import rules
    from assetops_backend.mini_depth.inputs import CONFIGURATION_MISSING, MiniInputsRefused, load_hour_inputs

    if CAPTURE:
        pytest.skip("T3 is ruled (D-DD.108 Q1), not a main parity")
    with labelled(engine, mg, R4), pv_units(engine, mg, 1):
        set_id, twin = covering_set(engine, mg), uuid4()
        with engine.connect() as c:
            cols = [r[0] for r in c.execute(text(
                "SELECT column_name FROM information_schema.columns WHERE table_name = 'signal_binding_set_revision' "
                "ORDER BY ordinal_position"))]
        over = {"id": f"'{twin}'", "binding_set_id": f"'{uuid4()}'", "role_set": f"'{R5}'"}
        _replica(engine, f"INSERT INTO signal_binding_set_revision ({', '.join(cols)}) SELECT "
                         f"{', '.join(over.get(x, x) for x in cols)} FROM signal_binding_set_revision "
                         f"WHERE id = '{set_id}'")
        try:
            assert from_evidence(engine, mg) == []
            assert from_publish(engine, mg) == []
            with engine.begin() as c:
                c.execute(text("SELECT mini_enqueue_hour(:t, :s, 'mini_fuel', :lo, :hi, NULL, now())"),
                          mg.ctx.p(lo=at(mg, DAY, 9), hi=at(mg, DAY, 10)))
            assert not mini_jobs(engine, mg.ctx.s)
            k = scalar(engine, "SELECT now()") + timedelta(hours=1)
            with engine.connect() as c, pytest.raises(MiniInputsRefused) as refused:
                load_hour_inputs(c, mg.ctx.t, mg.ctx.s, rules.Window(at(mg, DAY, 9), at(mg, DAY, 10)), k)
            assert refused.value.code == CONFIGURATION_MISSING
        finally:
            _replica(engine, f"DELETE FROM signal_binding_set_revision WHERE id = '{twin}'")


# --- T4: other sets enqueue nothing --------------------------------------------------------------------------------

def test_t4_other_sets_and_site_types_enqueue_nothing(mg, engine) -> None:  # noqa: F811
    with engine.connect() as c:
        sets = {r[0] for r in c.execute(text("SELECT role_set FROM signal_binding_set_revision WHERE site_id = :s "
                                             "AND superseded_at IS NULL"), {"s": mg.ctx.s})}
    assert sets and not sets & {R4, R5}  # the legacy roles-1/2/3 Site
    with pv_units(engine, mg, 1):
        got = {"legacy": {"evidence": from_evidence(engine, mg), "publish": from_publish(engine, mg)}}
    for role_set in (R4,) if CAPTURE else (R4, R5):
        for site_type in ("COLDCHAIN", "EV_CHARGING"):
            with labelled(engine, mg, role_set):
                clear_mini(engine)
                with engine.begin() as c:
                    set_type(c, mg.ctx.s, site_type)
                    c.execute(text("SELECT mini_enqueue_configuration(:t, :s, :f, :to, :at)"),
                              mg.ctx.p(f=at(mg, DAY, 0), to=at(mg, DAY + timedelta(days=1), 0),
                                       at=at(mg, DAY + timedelta(days=1), 1)))
                    set_type(c, mg.ctx.s, "MINIGRID")
                got[site_type] = rows(engine, mg, {})
        check("T4", got)


# --- T5: the renewable hour on two inverters -----------------------------------------------------------------------

def renewable(engine, mg) -> list[str]:  # noqa: F811
    return [r[1] for r in rows(engine, mg, {}) if r[0] == "mini_renewable"]


def t5(engine, mg) -> dict:  # noqa: F811
    with pv_units(engine, mg, 2) as (a, b):
        reading(mg, role=PV, hour=9, value="12.5", asset=a)   # positive on unit A only
        reading(mg, role=PV, hour=9, value="0", asset=b)
        reading(mg, role=PV, hour=10, value="0", asset=a)     # positive on unit B only
        reading(mg, role=PV, hour=10, value="3", asset=b)
        reading(mg, role=PV, hour=11, value="0", asset=a)     # on neither
        reading(mg, role=PV, hour=11, value="0", asset=b)
        reading(mg, role="feeder_demand", hour=12, value="5.0")
        two = renewable(engine, mg)
        k = scalar(engine, "SELECT now()") + timedelta(hours=1)
        from assetops_backend.mini_depth.store import daylight_hours
        with engine.connect() as c:
            measured = daylight_hours(c, mg.ctx.t, mg.ctx.s, DAY, k).measured
    with pv_units(engine, mg, 0):
        reading(mg, role="feeder_demand", hour=9, value="5.0")
        reading(mg, role="feeder_demand", hour=12, value="5.0")
        unbound = renewable(engine, mg)
    assert two and unbound  # non-empty: both rules enqueued
    return {"two_units": two, "unbound": unbound, "measured": measured}


def test_t5_renewable_hour_on_two_inverters(mg, engine) -> None:  # noqa: F811
    with labelled(engine, mg, R4):
        check("T5", t5(engine, mg))
    if not CAPTURE:
        with labelled(engine, mg, R5):
            check("T5", t5(engine, mg))


# --- T7: dispatch input-set role coverage --------------------------------------------------------------------------

def coverage(engine, mg) -> dict:  # noqa: F811
    from assetops_backend.analytics.adapters.postgres_assessment_store import PostgresAssessmentStore
    from assetops_backend.analytics.assessment_inputs import EvidenceQuery, Window
    from assetops_backend.analytics.assessment_worker import DISPATCH_ROLES, DOMAIN, input_basis

    owned = PostgresAssessmentStore(URL)
    try:
        k = scalar(engine, "SELECT now()") + timedelta(hours=1)
        result = owned.query_evidence(EvidenceQuery(mg.ctx.t, mg.ctx.s, DOMAIN,
                                                    Window(EVIDENCE_DAY, EVIDENCE_DAY + timedelta(days=1)), k,
                                                    roles=DISPATCH_ROLES))
        inputs, _ = input_basis(result)
    finally:
        pg_harness.dispose(owned)
    assert any(v.get("readings") for v in inputs.role_coverage.values())  # non-empty: coverage with readings
    return {"role_sets": sorted(inputs.role_sets), "role_coverage": inputs.role_coverage}


def test_t7_dispatch_role_coverage_roles5_equals_roles4(mg, engine) -> None:  # noqa: F811
    with labelled(engine, mg, R4):
        check("T7", coverage(engine, mg))
    if not CAPTURE:
        with labelled(engine, mg, R5):
            check("T7", coverage(engine, mg))


# --- P1-P4: the Python readers read roles-5 as roles-4 (same rows, relabelled) -------------------------------------

def python_reads(engine, mg, k) -> dict:  # noqa: F811
    from assetops_backend.mini_depth import rules
    from assetops_backend.mini_depth.inputs import QUERY_ROLES, load_hour_inputs
    from assetops_backend.mini_depth.read import MiniDepthRead, _hour_ids
    from assetops_backend.mini_depth.store import daylight_hours, read_hour_rows
    from assetops_backend.sites.binding_roles import MINI_DEPTH_ROLE_SETS

    window = rules.Window(at(mg, DAY, 9), at(mg, DAY, 10))
    with engine.connect() as c:
        raw = read_hour_rows(c, mg.ctx.t, mg.ctx.s, window.start, window.end, k, role_sets=MINI_DEPTH_ROLE_SETS,
                             roles=QUERY_ROLES, supply_role=rules.SITE_SUPPLY)
        inputs = load_hour_inputs(c, mg.ctx.t, mg.ctx.s, window, k)
        ids = _hour_ids(c, mg.ctx.t, mg.ctx.s, window, k)
        daylight = daylight_hours(c, mg.ctx.t, mg.ctx.s, DAY, k)
    feeders = MiniDepthRead(engine, link_rows=None).feeder_month(
        tenant_id=mg.ctx.t, site_id=mg.ctx.s, lo=at(mg, DAY, 0), hi=at(mg, DAY + timedelta(days=1), 0),
        known_at=None)  # live: a future cutoff is refused by the read
    assert len(raw.binding_sets) == 1 and ids and feeders.binding_sets and daylight.measured  # non-empty
    return {"sets": [list(map(str, s)) for s in raw.binding_sets], "inputs": repr(inputs), "ids": ids,
            "daylight": repr(daylight), "feeders": repr(feeders)}


def test_p1_p4_python_readers_read_roles5_as_roles4(mg, engine) -> None:  # noqa: F811
    """The same rows (one write) and one cutoff, read under each set name."""
    if CAPTURE:
        pytest.skip("in-run parity: the same rows under each set name")
    with pv_units(engine, mg, 1):
        for r, h, v in EVIDENCE:
            reading(mg, role=r, hour=h, value=v)
        k = scalar(engine, "SELECT now()") + timedelta(hours=1)
        with labelled(engine, mg, R4):
            four = python_reads(engine, mg, k)
        with labelled(engine, mg, R5):
            five = python_reads(engine, mg, k)
    assert normalise(five) == normalise(four)
