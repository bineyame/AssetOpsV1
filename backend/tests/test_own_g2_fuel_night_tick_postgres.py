"""OWN-G2 (build sheet OWN-GAPS §2.7 P1-P7, as amended by R2-G2 Q1, Q5, Q6, Q7, Q10, Q12): the schedule tick's
`fuel_night` stage on Postgres.

Needs `ASSETOPS_TEST_DATABASE_URL` naming a `*_test` database; skipped without it.

One module-scoped Kisiwa Site through K1's path (`demo_combined_kisiwa.register`, `kisiwa.draft_day`, a real gateway
and S2 ingestion), registered at DB now - 12 d, beside an imported, enrolled KOBO-001 (a tank and a generator, no
`fuel_level`). Four Kisiwa story-shaped runs (15:00-15:00 local, `probe_kisiwa_nights.day_document`) end at the
latest local 15:00 at or before DB now - 15 min and 1, 2 and 9 days before it; each holds exactly one night. All are
accepted with the decision clock at DB now - 10 min. Night N2 is assessed and raised through the CLI at a virtual
instant before the ticks (P6). The tick's other stages run in process; `fuel_night` runs as a real `StageRunner`
child on the database's own clock.
"""

from __future__ import annotations

import os
import sys
from datetime import date, datetime, time, timedelta, timezone
from fractions import Fraction
from math import ceil
from pathlib import Path
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

import pytest

REPO = Path(__file__).resolve().parents[2]
for extra in (REPO / "tools", REPO / "host", REPO / "host" / "tests", REPO / "gateway" / "tests"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = [
    pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)"),
    pytest.mark.slow,
]

UTC = timezone.utc
COUNTED = ("fuel_balance_window", "finding_revision", "fuel_residual_consequence_revision")
OFFSETS = (0, 1, 2, 9)  # run k ends E - k days and holds night N_k; N9 lies outside the base set (P5)


def _q(engine, sql: str, **p) -> list[dict]:
    from sqlalchemy import text

    with engine.connect() as c:
        return [dict(r._mapping) for r in c.execute(text(sql), p)]


def _counts(engine, site_id) -> dict[str, int]:
    return {t: _q(engine, f"SELECT count(*) AS n FROM {t} WHERE site_id = :s", s=site_id)[0]["n"] for t in COUNTED}


def _windows(engine, site_id) -> list[dict]:
    return _q(engine, "SELECT id, night_date, revision, recorded_at, state, residual_low, limitations, record_ids, "
                      "window_start, window_end FROM fuel_balance_window WHERE site_id = :s "
                      "ORDER BY night_date, revision", s=site_id)


def _ids(rev: dict) -> list[str]:
    """`record_ids` as flat strings (the column may hold a list of lists)."""
    flat: list[str] = []
    for x in rev["record_ids"]:
        flat.extend(str(y) for y in x) if isinstance(x, (list, tuple)) else flat.append(str(x))
    return flat


def _latest(engine, site_id, night: date) -> dict:
    return [w for w in _windows(engine, site_id) if w["night_date"] == night][-1]


@pytest.fixture(scope="module")
def site(tmp_path_factory):
    from sqlalchemy import create_engine
    from sqlalchemy.engine import make_url

    import demo_combined_kisiwa as kis
    import pg_harness
    import probe_kisiwa_nights as nights
    import test_s6_verification_replay as rp
    from test_s1_bindings_postgres import imported
    from test_s4_schedule_tick_postgres import FAST, make_tick

    from assetops_backend.fuel_balance.composition import build_fuel_balance_store, build_fuel_finding_service
    from assetops_backend.fuel_balance.worker import main as fuel_cli
    from assetops_backend.scheduling.tick import TickLimits
    from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore

    url = make_url(URL)
    assert url.database and url.database.endswith("_test"), "Refusing a database not named *_test"
    pg_harness.fresh_database()
    engine = create_engine(URL)
    db_now = _q(engine, "SELECT clock_timestamp() AS n")[0]["n"].astimezone(UTC).replace(microsecond=0)
    store = PostgresFoundationStore(URL)
    try:
        kobo = imported(store)
        tick, _ = make_tick(TickLimits(**FAST))
        tick.store.enrol(kobo.tenant.id, kobo.site.id, True, "test-operator")
        work = tmp_path_factory.mktemp("g2-kisiwa")
        import_at = db_now - timedelta(days=12)
        reg = kis.register(URL, work, import_at, import_at + timedelta(minutes=30))
        tenant_id, site_id = UUID(reg["tenant_id"]), UUID(reg["site_id"])
        tz = _q(engine, "SELECT timezone FROM site WHERE id = :s", s=site_id)[0]["timezone"]
        zone = ZoneInfo(tz)
        local = (db_now - timedelta(minutes=15)).astimezone(zone)
        e_day = local.date() if local.time() >= time(15) else local.date() - timedelta(days=1)
        e_end = datetime.combine(e_day, time(15), zone).astimezone(UTC)
        setup_at = (import_at + timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
        received = db_now - timedelta(minutes=10)
        night_of_k = {}
        iso = lambda d: d.strftime("%Y-%m-%dT%H:%M:%SZ")  # noqa: E731
        reg_basis = kis.story_registered(store, setup_at, iso(e_end - timedelta(days=max(OFFSETS) + 1)), None)
        for k in OFFSETS:
            end = e_end - timedelta(days=k)
            run = reg_basis.draft(nights.day_document(nights.START_SOC, nights.START_FUEL),
                                  iso(end - timedelta(days=1)), iso(end), "v7")
            assert run.execution_status == "READY", [(r.kind, r.subject) for r in run.blocking_reasons]
            # one received_at per run: `_publish_and_accept` counts its batches by `received_at`
            rp._publish_and_accept(work / f"r{k}", run, f"epoch-g2-{k}", received + timedelta(seconds=k))
            night_of_k[k] = end.astimezone(zone).date() - timedelta(days=1)
        tank = str(_q(engine, "SELECT id FROM asset WHERE site_id = :s AND asset_type = 'FUEL_TANK' "
                              "AND retired_at IS NULL", s=site_id)[0]["id"])
        # P6: N2 assessed and raised through the CLI at a virtual instant before the ticks (as K7 does)
        p6_at = db_now - timedelta(minutes=5)
        n2 = night_of_k[2]
        span = ["--site", "KISIWA-001", "--from", n2.isoformat(), "--to", (n2 + timedelta(days=1)).isoformat()]
        fb = build_fuel_balance_store(URL, test_db_clock_override=lambda: p6_at)
        try:
            code, assessed = kis._cli_lines(lambda: fuel_cli(["assess", *span], store=fb))
        finally:
            fb.dispose()
        assert code == 0 and [(x["status"], x["revision"]) for x in assessed] == [("APPENDED", 1)], assessed
        service = build_fuel_finding_service(URL, test_db_clock_override=lambda: p6_at)
        try:
            code, raised = kis._cli_lines(lambda: fuel_cli(["raise", *span], finding_service=service))
        finally:
            service.dispose()
        assert code == 0 and len(raised) == 1, raised
        yield {"engine": engine, "tenant_id": tenant_id, "site_id": site_id, "tank": tank, "tz": tz, "zone": zone,
               "nights": night_of_k, "kobo": kobo, "p6_raise": raised[0]["status"], "db_now": db_now}
    finally:
        pg_harness.dispose(store)
        engine.dispose()


class _ChildFuelNight:
    """`InProcessRunner` for every stage but `fuel_night`, which runs as a real `StageRunner` child."""

    def __new__(cls, limits):
        from test_s4_schedule_tick_postgres import InProcessRunner

        from assetops_backend.scheduling.tick import StageRunner

        class Runner(InProcessRunner):
            def run(self, stage, args, seconds):
                if stage != "fuel_night":
                    return super().run(stage, args, seconds)
                self.calls.append((stage, str(args.get("site_id"))))
                return StageRunner.run(self, stage, args, seconds)
        return Runner(limits)


def _tick(engine) -> tuple:
    """One tick; returns (report, clock before, clock after)."""
    from test_s4_schedule_tick_postgres import FAST, make_tick

    from assetops_backend.scheduling.tick import TickLimits

    limits = TickLimits(**FAST)
    tick, _ = make_tick(limits, runner=_ChildFuelNight(limits))
    before = _q(engine, "SELECT clock_timestamp() AS n")[0]["n"]
    report = tick.tick()
    after = _q(engine, "SELECT clock_timestamp() AS n")[0]["n"]
    assert report.outcome == "COMPLETED", report.failure
    return report, before, after


def _fuel(report, site_id) -> dict:
    [s] = [s for s in report.selected if str(s.site_id) == str(site_id)]
    fuel = s.stages.get("fuel_night")
    assert fuel is not None, ("the Site's fuel_night stage did not run", s.failure, list(s.stages))
    assert fuel["code"] == "OK", fuel
    return fuel


def _night(fuel: dict, night: date) -> dict | None:
    return next((n for n in fuel.get("nights") or () if n["night_date"] == night.isoformat()), None)


def _post(record: dict) -> dict:
    from test_w401_work_service_postgres import PRINCIPAL

    from assetops_backend.work.composition import build_work_service

    service = build_work_service(URL)
    try:
        status, response = service.post_operational_record(record.pop("_t"), record.pop("_s"), record, PRINCIPAL)
    finally:
        service._store.dispose()
    assert status == 201, (status, response)
    return response


def _record(site, kind: str, key: str, occurred: datetime, quantity: str, **over) -> dict:
    from test_w401_work_service_postgres import oprec

    return {**oprec(key, kind=kind, body=f"G2 test {kind.lower()}", occurred_at=occurred.strftime(
        "%Y-%m-%dT%H:%M:%SZ"), unit="L", quantity=quantity,
        source_document_sha256="ab" * 32 if kind == "FUEL_DELIVERY" else None, asset_id=site["tank"]),
        "_t": site["tenant_id"], "_s": site["site_id"], **over}


def test_q1_bucket_edges_and_q12_a_site_without_fuel_assets(site) -> None:
    from assetops_backend.fuel_balance.adapters.postgres_fuel_balance_store import NIGHT_BUCKET_SQL
    from assetops_backend.fuel_balance.composition import build_fuel_balance_store
    from assetops_backend.fuel_balance.scheduled import RECORD_LOOKBACK, bucket_bounds, night_of

    engine = site["engine"]
    ns, ne = bucket_bounds()
    b = {"tz": site["tz"], "ns": ns, "ne": ne}
    # (a) every real tank reading, through the store's join, acceptance filter and its own CASE
    rows = _q(engine, "SELECT COALESCE(e.interval_start, e.source_time) AS at, d.decided_at, "
              f"{NIGHT_BUCKET_SQL} AS night FROM accepted_evidence e JOIN ingestion_disposition d "
              "ON d.batch_id = e.batch_id AND d.ordinal = e.ordinal WHERE e.site_id = :s AND d.decision = 'ACCEPTED' "
              "AND d.accepted_evidence_id = e.id AND e.role = 'fuel_level' AND e.asset_id = CAST(:a AS uuid)",
              s=site["site_id"], a=site["tank"], **b)
    local = [(r["at"].astimezone(site["zone"]), r) for r in rows]
    hhmm = {t.strftime("%H:%M") for t, _ in local}
    print("G2 Q1 readings", len(rows), "minutes", sorted({t.minute for t, _ in local}), "edges",
          sorted(hhmm & {"17:30", "12:30"}))
    assert len(rows) > 0 and {"17:30", "12:30"} <= hhmm, sorted(hhmm)  # the real edge readings exist
    for t, r in local:
        assert r["night"] == night_of(t), (t, r["night"])  # SQL == Python, every reading
        if t.strftime("%H:%M") == "17:30":
            assert r["night"] == t.date(), t  # start edge in
        if t.strftime("%H:%M") == "12:30":
            assert r["night"] == t.date() - timedelta(days=1), t  # end edge in (closed, = closing search)
    # (b) any cadence: synthetic instants around N0, evaluated by Postgres through the same expression
    d, z = site["nights"][0], site["zone"]
    d1 = d + timedelta(days=1)
    probe = {datetime.combine(d, time(17, 25), z): None, datetime.combine(d, time(17, 29, 59), z): None,
             datetime.combine(d, time(17, 30), z): d, datetime.combine(d, time(17, 30, 1), z): d,
             datetime.combine(d, time(23, 55), z): d, datetime.combine(d1, time(0, 5), z): d,
             datetime.combine(d1, time(12, 25), z): d, datetime.combine(d1, time(12, 29, 59), z): d,
             datetime.combine(d1, time(12, 30), z): d, datetime.combine(d1, time(12, 30, 1), z): None,
             datetime.combine(d1, time(15), z): None}
    for at, want in probe.items():
        [got] = _q(engine, f"SELECT {NIGHT_BUCKET_SQL} AS night FROM (SELECT CAST(:x AS timestamptz) AS "
                   "interval_start, CAST(NULL AS timestamptz) AS source_time) e", x=at.astimezone(UTC), **b)
        assert got["night"] == night_of(at) == want, (at, got["night"], night_of(at), want)
    # (c) the store itself: same nights, and each night's trigger instant is its readings' latest decided_at
    store = build_fuel_balance_store(URL)
    try:
        inputs = store.schedule_inputs(site["tenant_id"], site["site_id"], RECORD_LOOKBACK)
        empty = store.schedule_inputs(site["tenant_id"], uuid4(), RECORD_LOOKBACK)
    finally:
        store.dispose()
    want = {}
    for t, r in local:
        n = night_of(t)
        if n is not None:
            want[n] = max(want.get(n, r["decided_at"]), r["decided_at"])
    print("G2 Q1 reading nights", sorted(inputs.reading_nights), "want", sorted(want))
    assert set(inputs.reading_nights) == set(want) == {site["nights"][k] for k in OFFSETS}
    assert all(inputs.reading_nights[n].astimezone(UTC) == want[n].astimezone(UTC) for n in want), (
        inputs.reading_nights, want)
    assert inputs.tank_asset_id == site["tank"] and inputs.generator_asset_id is not None
    # Q12: no FUEL_TANK/GENERATOR rows (an unknown Site id): nothing is read
    assert (empty.tank_asset_id, dict(empty.reading_nights), empty.records, dict(empty.latest)) == (None, {}, (), {})


def test_p1_p2_p3_p6_p7_two_ticks(site) -> None:
    engine, s, n = site["engine"], site["site_id"], site["nights"]
    before = _counts(engine, s)
    report, t0, t1 = _tick(engine)
    fuel = _fuel(report, s)
    print("G2 tick 1 fuel_night", {k: fuel.get(k) for k in ("eligible", "processed", "deferred", "appended",
                                                             "reused", "raised", "nights")})
    assert fuel["eligible"] is True and fuel["deferred"] == 0
    # P1: N0 and N1 appended revision 1 and raised
    for k in (0, 1):
        entry = _night(fuel, n[k])
        assert entry and (entry["assess"], entry["revision"]) == ("APPENDED", 1) and entry["raise"], entry
    # P6: the CLI's story-instant night gives REUSED and the same raise outcome, and no row
    p6 = _night(fuel, n[2])
    want = "UNCHANGED" if site["p6_raise"] in ("OPENED", "REVISED", "UNCHANGED") else "NO_FINDING"
    assert p6 and (p6["assess"], p6["revision"], p6["raise"]) == ("REUSED", 1, want), (p6, site["p6_raise"])
    assert _night(fuel, n[9]) is None  # outside the base set, no record
    windows = _windows(engine, s)
    # P2: only nights with readings have rows; N9 is not assessed yet
    assert sorted({w["night_date"] for w in windows}) == sorted(n[k] for k in (0, 1, 2)), windows
    assert len(windows) == 3 and before["fuel_balance_window"] == 1
    # P7: every new window is stamped at DB time inside the tick
    new = [w for w in windows if w["night_date"] in (n[0], n[1])]
    assert all(t0 <= w["recorded_at"] <= t1 for w in new), [(w["recorded_at"], t0, t1) for w in new]
    assert [w for w in windows if w["night_date"] == n[2]][0]["recorded_at"] < t0
    # P1 tick 2: no new row in any of the three tables
    after_one = _counts(engine, s)
    report2, _, _ = _tick(engine)
    fuel2 = _fuel(report2, s)
    assert {x["assess"] for x in fuel2["nights"]} == {"REUSED"}, fuel2["nights"]
    assert _counts(engine, s) == after_one, (after_one, _counts(engine, s))
    # P3: the Kobo-like Site (tank and generator, no fuel_level) gets no window after two ticks
    kobo = site["kobo"].site.id
    assert _q(engine, "SELECT count(*) AS n FROM fuel_balance_window WHERE site_id = :s", s=kobo)[0]["n"] == 0
    kobo_fuel = _fuel(report2, kobo)
    print("G2 P3 Kobo fuel_night", kobo_fuel)
    assert kobo_fuel["processed"] == 0 and kobo_fuel["deferred"] == 0


def test_p4a_a_conflicting_dip_appends_revision_2_with_the_limitation(site) -> None:
    engine, s, n0 = site["engine"], site["site_id"], site["nights"][0]
    rev1 = _latest(engine, s, n0)
    assert rev1["revision"] == 1
    dip = _post(_record(site, "TANK_DIP", "g2-p4a-dip", rev1["window_start"] + timedelta(hours=2), "1"))
    fuel = _fuel(_tick(engine)[0], s)
    entry = _night(fuel, n0)
    rev2 = _latest(engine, s, n0)
    print("G2 P4a", entry, rev2["limitations"], rev2["record_ids"])
    assert entry and (entry["assess"], entry["revision"]) == ("APPENDED", 2), entry
    assert rev2["revision"] == 2 and dip["id"] in _ids(rev2), rev2["record_ids"]
    assert "DIP_SENSOR_CONFLICT" in rev2["limitations"], rev2["limitations"]


def test_p4b_p4c_an_unseen_delivery_opens_and_its_correction_withdraws(site) -> None:
    from assetops_backend.fuel_balance import rules

    engine, s, n1 = site["engine"], site["site_id"], site["nights"][1]
    rev = _latest(engine, s, n1)
    assert rev["state"] == "WITHIN_MARGIN", rev  # the precondition of R2-G2 Q6 (b)
    low = Fraction(str(rev["residual_low"]))
    litres = ceil((rules.MATERIALITY_L - low) / (1 - rules.DELIVERY_TOLERANCE)) + 20
    occurred = rev["window_start"] + timedelta(hours=3)
    delivery = _post(_record(site, "FUEL_DELIVERY", "g2-p4b-delivery", occurred, str(litres)))
    fuel = _fuel(_tick(engine)[0], s)
    entry, opened = _night(fuel, n1), _latest(engine, s, n1)
    print("G2 P4b", litres, entry, opened["state"])
    assert entry and (entry["assess"], entry["raise"]) == ("APPENDED", "OPENED"), entry
    assert opened["state"] == "UNEXPLAINED" and opened["revision"] == rev["revision"] + 1, opened
    # (c) a correction that moves the delivery out of the night (local 15:00 of the night's own day)
    moved = datetime.combine(n1, time(15), site["zone"]).astimezone(UTC)
    _post(_record(site, "FUEL_DELIVERY", "g2-p4c-correction", moved, str(litres),
                  supersedes_record_id=delivery["id"], canonical_record_id=delivery.get("canonical_record_id")
                  or delivery["id"], correction_reason="Delivery was in the afternoon"))
    fuel = _fuel(_tick(engine)[0], s)
    entry, back = _night(fuel, n1), _latest(engine, s, n1)
    print("G2 P4c", entry, back["state"])
    assert entry and (entry["assess"], entry["raise"]) == ("APPENDED", "WITHDRAWN"), entry
    assert back["state"] == "WITHIN_MARGIN" and back["revision"] == opened["revision"] + 1, back


def test_p5_an_old_assessed_night_is_rechecked_and_a_40_day_record_is_not_read(site) -> None:
    from test_w401_work_service_postgres import PRINCIPAL, VirtualDbClock

    from assetops_backend.fuel_balance.composition import build_fuel_balance_store
    from assetops_backend.fuel_balance.scheduled import RECORD_LOOKBACK
    from assetops_backend.fuel_balance.worker import main as fuel_cli
    from assetops_backend.work.composition import build_work_service

    import demo_combined_kisiwa as kis

    engine, s, n9 = site["engine"], site["site_id"], site["nights"][9]
    fb = build_fuel_balance_store(URL)
    try:
        code, lines = kis._cli_lines(lambda: fuel_cli(["assess", "--site", "KISIWA-001", "--from", n9.isoformat(),
                                                       "--to", (n9 + timedelta(days=1)).isoformat()], store=fb))
    finally:
        fb.dispose()
    assert code == 0 and [(x["status"], x["revision"]) for x in lines] == [("APPENDED", 1)], lines
    first = _latest(engine, s, n9)
    dip = _post(_record(site, "TANK_DIP", "g2-p5-dip", first["window_start"] + timedelta(hours=2), "1"))
    # the 40-day record, posted through the work store on a virtual DB clock at occurred + 29 d (R2-G2 Q7)
    old = site["db_now"] - timedelta(days=40)
    service = build_work_service(URL)
    service._store.test_db_clock_override = VirtualDbClock(old + timedelta(days=29))
    try:
        body = _record(site, "FUEL_DELIVERY", "g2-p5-old", old, "50")
        status, response = service.post_operational_record(body.pop("_t"), body.pop("_s"), body, PRINCIPAL)
    finally:
        service._store.dispose()
    assert status == 201, (status, response)
    store = build_fuel_balance_store(URL)
    try:
        inputs = store.schedule_inputs(site["tenant_id"], s, RECORD_LOOKBACK)
    finally:
        store.dispose()
    occurred = [o for o, _ in inputs.records]
    print("G2 P5 records", len(inputs.records), "old", old)
    assert all(abs(o - old) > timedelta(seconds=1) for o in occurred), occurred
    assert any(abs(o - (first["window_start"] + timedelta(hours=2))) < timedelta(seconds=1) for o in occurred)
    fuel = _fuel(_tick(engine)[0], s)
    entry = _night(fuel, n9)
    print("G2 P5", entry, dip["id"])
    assert entry and (entry["assess"], entry["revision"]) == ("APPENDED", 2), entry
    assert dip["id"] in _ids(_latest(engine, s, n9))
