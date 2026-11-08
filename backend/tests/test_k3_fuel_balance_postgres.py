"""DIESEL-K3 L2 (`.agent/build-sheet-DIESEL-1.md` §9d.6 B1-B6): `fuel_balance_window` over real Postgres.

Kobo is imported as K2's L2 does (`test_s1_bindings_postgres.imported`); the twin-tank Site is created from
`config/site-templates/twin-tank-mini-grid-150kw.yaml` through the product's create path and imported with
`import_site`. The work store and the fuel-balance store each run on a virtual DB clock. Requires
ASSETOPS_TEST_DATABASE_URL naming a `*_test` database.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

MIGRATION, PREVIOUS = "0055_fuel_balance_window", "0054_operational_fuel_records"
REFUSED = "0055 downgrade requires no fuel_balance_window rows"
NIGHT = date(2026, 10, 10)
TICKET = "ab" * 32
TABLE = "fuel_balance_window"

if URL:
    import pg_harness
    import yaml
    from pg_harness import alembic_head
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError, IntegrityError
    from test_s1_bindings_postgres import Clock, _alembic, engine, imported, store  # noqa: F401
    from test_w203_cold_migration_postgres import head
    from test_w401_work_service_postgres import PRINCIPAL, VirtualDbClock, oprec

    from assetops_backend.actions.adapters.postgres_action_store import PostgresActionStore
    from assetops_backend.evidence.composition import build_link_rows_reader
    from assetops_backend.fuel_balance import rules
    from assetops_backend.fuel_balance.adapters.postgres_fuel_balance_store import PostgresFuelBalanceStore
    from assetops_backend.fuel_balance.model import FuelBalanceRefused
    from assetops_backend.fuel_balance.service import FuelBalanceService
    from assetops_backend.fuel_balance.worker import main as worker_main
    from assetops_backend.sites.foundation_service import ImportSource, import_site
    from assetops_backend.sites.site_parsing import render_site_document
    from assetops_backend.work.adapters.postgres_fuel_records import PostgresFuelRecords, select_fuel_records
    from assetops_backend.work.adapters.postgres_work_store import PostgresWorkStore
    from assetops_backend.work.service import WorkService


def iso(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


class SetClock:
    """The fuel-balance store's virtual DB instant: whatever the test last set."""

    def __init__(self, now: datetime) -> None:
        self.now = now

    def __call__(self) -> datetime:
        return self.now


class Site:
    """One imported Site: its assets, a clocked work service, K2's read and K3's store and service."""

    def __init__(self, engine, result, work_start: datetime) -> None:  # noqa: F811
        self.t, self.s, self.engine = result.tenant.id, result.site.id, engine
        with engine.connect() as c:
            rows = c.execute(text("SELECT asset_code, id, asset_type FROM asset WHERE site_id = :s AND "
                                  "retired_at IS NULL"), {"s": self.s}).all()
            self.tz = c.execute(text("SELECT timezone FROM site WHERE id = :s"), {"s": self.s}).scalar_one()
        self.assets = {code: str(i) for code, i, _ in rows}
        self.types = {code: kind for code, _, kind in rows}
        self.work_clock = VirtualDbClock(work_start)
        self.work = PostgresWorkStore(URL, link_rows=build_link_rows_reader(), test_db_clock_override=self.work_clock)
        self.svc = WorkService(self.work)
        self.read = PostgresFuelRecords(URL)
        self.fb_clock = SetClock(work_start)
        self.fb = PostgresFuelBalanceStore(URL, actions=PostgresActionStore(URL), fuel_records=select_fuel_records,
                                           test_db_clock_override=self.fb_clock)
        self.balance = FuelBalanceService(self.fb)
        self.start, self.end = rules.night_window(NIGHT, self.tz)

    def post(self, body: dict) -> dict:
        status, response = self.svc.post_operational_record(self.t, self.s, body, PRINCIPAL)
        assert status == 201, response
        return response

    def records(self, tank: str, known_at: datetime):
        return self.read.fuel_records(self.t, self.s, UUID(tank), self.start, self.end, known_at)

    def assess(self, at: datetime, night: date = NIGHT):
        self.fb_clock.now = at
        return self.balance.assess_night(self.t, self.s, night)

    def count(self) -> int:
        with self.engine.connect() as c:
            return c.execute(text(f"SELECT count(*) FROM {TABLE}")).scalar_one()

    def close(self) -> None:
        self.work.dispose()
        self.read.dispose()
        self.fb.dispose()


def twin_tank(store):  # noqa: F811
    """The twin-tank Site through the product's create path (`host/tests/fixtures.site_from_template`), imported."""
    from fixtures import TWIN_TANK_TEMPLATE, site_from_template

    record = site_from_template(TWIN_TANK_TEMPLATE, site_id="TWIN-001", display_name="Twin tank mini-grid")
    payload = yaml.safe_dump(render_site_document(record), sort_keys=True).encode("utf-8")
    source = ImportSource(path="var/sites/twin-001.yaml", sha256=hashlib.sha256(payload).hexdigest(), record=record)
    return import_site(store, tenant_slug="demo", configured_tenant_slug="demo", source=source, legacy_documents=(),
                       clock=Clock(datetime(2026, 10, 7, 10, 0, tzinfo=timezone.utc)))


@pytest.fixture()
def kobo(store, engine):  # noqa: F811
    owned = Site(engine, imported(store), datetime(2026, 10, 20, tzinfo=timezone.utc))
    yield owned
    owned.close()


def dip(tank: str, key: str, occurred: datetime, quantity: str = "706", **over) -> dict:
    return oprec(key, **{"kind": "TANK_DIP", "body": f"Tank dip at the 07:00 round: {quantity} L.",
                         "occurred_at": iso(occurred), "unit": "L", "quantity": quantity, "asset_id": tank, **over})


def correction(root: dict, key: str, body: dict, reason: str) -> dict:
    return {**body, "idempotency_key": key, "supersedes_record_id": root["id"], "canonical_record_id": root["id"],
            "correction_reason": reason}


# --- B1 migration -----------------------------------------------------------------------------------------------------


def shape(engine) -> tuple:  # noqa: F811
    with engine.connect() as c:
        cols = tuple(c.execute(text("SELECT column_name, data_type, is_nullable FROM information_schema.columns "
                                    "WHERE table_name = :t ORDER BY ordinal_position"), {"t": TABLE}).all())
        defs = dict(c.execute(text("SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint "
                                   "WHERE conrelid = to_regclass(:t)"), {"t": TABLE}).all())
        indexes = dict(c.execute(text("SELECT indexname, indexdef FROM pg_indexes WHERE tablename = :t"),
                                 {"t": TABLE}).all())
        triggers = tuple(c.execute(text("SELECT tgname, pg_get_triggerdef(oid) FROM pg_trigger "
                                        "WHERE tgrelid = to_regclass(:t) AND NOT tgisinternal "
                                        "AND tgname NOT LIKE '%\\_cic\\_%'"), {"t": TABLE}).all())  # 0058's W2 triggers
    return cols, defs, indexes, triggers


EXPECTED_DEFS = {
    "fuel_balance_window_band": "CHECK ((((state = 'NOT_ASSESSED'::text) = (residual_low IS NULL)) AND "
                                "((residual_low IS NULL) = (residual_high IS NULL))))",
    "fuel_balance_window_closed": "CHECK (((window_end > window_start) AND "
                                  "(recorded_at >= (window_end + '00:30:00'::interval))))",
    "fuel_balance_window_reason": "CHECK (((state = 'NOT_ASSESSED'::text) = (reason IS NOT NULL)))",
    "fuel_balance_window_revision_unique": "UNIQUE (tenant_id, site_id, tank_asset_id, night_date, revision)",
    "fuel_balance_window_tank_fk": "FOREIGN KEY (tenant_id, site_id, tank_asset_id) "
                                   "REFERENCES asset(tenant_id, site_id, id)",
    "fuel_balance_window_generator_fk": "FOREIGN KEY (tenant_id, site_id, generator_asset_id) "
                                        "REFERENCES asset(tenant_id, site_id, id)",
    "fuel_balance_window_pkey": "PRIMARY KEY (id)",
    "fuel_balance_window_revision_check": "CHECK ((revision >= 1))",
    "fuel_balance_window_parameter_version_check": "CHECK ((parameter_version = 'fuel-balance-1/v1'::text))",
    "fuel_balance_window_gap_minutes_check": "CHECK ((gap_minutes >= 0))",
    "fuel_balance_window_input_sha256_check": "CHECK ((input_sha256 ~ '^[0-9a-f]{64}$'::text))",
    "fuel_balance_window_state_check": "CHECK ((state = ANY (ARRAY['UNEXPLAINED'::text, 'BELOW_MATERIALITY'::text, "
                                       "'WITHIN_MARGIN'::text, 'EXCESS'::text, 'NOT_ASSESSED'::text])))",
    "fuel_balance_window_reason_check": "CHECK ((reason = ANY (ARRAY['NO_SENSOR_ACCURACY'::text, 'SFC_MISSING'::text, "
                                        "'NO_LOAD_RATE_MISSING'::text, 'MISSING_OPENING'::text, "
                                        "'MISSING_CLOSING'::text, 'FUEL_LEVEL_CONFLICT'::text, "
                                        "'GENERATOR_KWH_UNKNOWN'::text, 'IDLE_SECONDS_UNKNOWN'::text])))",
}
COLUMNS = ("id", "tenant_id", "site_id", "tank_asset_id", "generator_asset_id", "night_date", "window_start",
           "window_end", "revision", "parameter_version", "recorded_at", "state", "reason", "residual_low",
           "residual_high", "gap_minutes", "gap_spans", "limitations", "terms", "evidence_ids", "record_ids",
           "input_sha256")


def test_b1_single_alembic_head(engine) -> None:  # noqa: F811
    from alembic.script import ScriptDirectory

    script = ScriptDirectory.from_config(_alembic())
    # DIESEL-K4a (§9j.8 B6): head-agnostic head bookkeeping; 0055 is no longer the head.
    assert script.get_heads() == [alembic_head()] and head(engine) == alembic_head()
    assert script.get_revision(MIGRATION).down_revision == PREVIOUS


def test_b1_migration_up_down_up_on_empty_table(store, engine) -> None:  # noqa: F811
    from alembic import command

    pg_harness.dispose(store)
    up = shape(engine)
    cols, defs, indexes, triggers = up
    assert tuple(c[0] for c in cols) == COLUMNS
    assert {c[0] for c in cols if c[2] == "YES"} == {"reason", "residual_low", "residual_high"}
    assert defs == EXPECTED_DEFS
    assert indexes["fuel_balance_window_night"] == (
        "CREATE INDEX fuel_balance_window_night ON public.fuel_balance_window USING btree "
        "(tenant_id, site_id, tank_asset_id, night_date, recorded_at)")
    assert triggers == (("fuel_balance_window_immutable", "CREATE TRIGGER fuel_balance_window_immutable BEFORE "
                         "DELETE OR UPDATE ON public.fuel_balance_window FOR EACH ROW EXECUTE FUNCTION "
                         "ledger_append_only()"),)
    config = _alembic()
    engine.dispose()
    try:
        command.downgrade(config, PREVIOUS)
        assert head(engine) == PREVIOUS and shape(engine) == ((), {}, {}, ())
        command.upgrade(config, "head")
    finally:
        if head(engine) != alembic_head():
            command.upgrade(config, "head")
    assert shape(engine) == up


def test_b1_downgrade_refused_with_a_row_and_rows_are_immutable(kobo, engine) -> None:  # noqa: F811
    from alembic import command

    window = kobo.assess(kobo.end + timedelta(hours=1)).window
    for sql in (f"UPDATE {TABLE} SET gap_minutes = 1 WHERE id = :i", f"DELETE FROM {TABLE} WHERE id = :i"):
        with pytest.raises(DBAPIError, match="append-only"):
            with engine.begin() as c:
                c.execute(text(sql), {"i": window.id})
    kobo.close()
    config = _alembic()
    engine.dispose()
    try:
        with pytest.raises(RuntimeError, match=REFUSED):
            command.downgrade(config, PREVIOUS)
    finally:
        if head(engine) != alembic_head():
            command.upgrade(config, "head")
    assert head(engine) == alembic_head() and kobo.count() == 1


def test_b1_checks_hold_below_the_service(kobo, engine) -> None:  # noqa: F811
    tank, gen = kobo.assets["fuel-tank"], kobo.assets["generator"]
    sql = (f"INSERT INTO {TABLE} (id, tenant_id, site_id, tank_asset_id, generator_asset_id, night_date, window_start, "
           "window_end, revision, parameter_version, recorded_at, state, reason, residual_low, residual_high, "
           "gap_minutes, gap_spans, limitations, terms, evidence_ids, record_ids, input_sha256) VALUES (:i, :t, :s, "
           ":tank, :gen, :d, :ws, :we, 1, 'fuel-balance-1/v1', :rec, :state, :reason, :lo, :hi, 0, '[]', '[]', "
           "'{}', '[]', '[]', :h)")

    def insert(match: str | None, **p) -> None:
        params = {"i": uuid4(), "t": kobo.t, "s": kobo.s, "tank": tank, "gen": gen, "d": NIGHT, "ws": kobo.start,
                  "we": kobo.end, "rec": kobo.end + timedelta(minutes=30), "state": "NOT_ASSESSED",
                  "reason": "MISSING_OPENING", "lo": None, "hi": None, "h": "a" * 64, **p}
        if match is None:
            with engine.begin() as c:
                c.execute(text(sql), params)
            return
        with pytest.raises(IntegrityError, match=match):
            with engine.begin() as c:
                c.execute(text(sql), params)

    insert("fuel_balance_window_reason", reason=None)
    insert("fuel_balance_window_closed", rec=kobo.end + timedelta(minutes=29, seconds=59))
    insert("fuel_balance_window_band", lo="1", hi="2")
    insert("fuel_balance_window_band", state="UNEXPLAINED", reason=None, lo="41", hi=None)
    insert("fuel_balance_window_reason", state="UNEXPLAINED", lo="41", hi="60")
    insert("fuel_balance_window_tank_fk", tank=str(uuid4()))
    insert("fuel_balance_window_input_sha256_check", h="A" * 64)
    insert(None)  # the base row is valid
    assert kobo.count() == 1


# --- B2-B4 K2 L1 and the cross-kind correction ------------------------------------------------------------------------


def test_b2_kind_change_drops_the_dip_after_the_correction(kobo) -> None:
    tank = kobo.assets["fuel-tank"]
    t0 = kobo.work_clock.now
    root = kobo.post(dip(tank, "k3-b2-dip", kobo.start + timedelta(hours=10)))
    t1 = kobo.work_clock.now
    kobo.post(correction(root, "k3-b2-fix", oprec("x", body="Not a dip: the round was skipped.",
                                                  occurred_at=iso(kobo.start + timedelta(hours=10))),
                         "Logged as a dip by mistake"))
    before = kobo.records(tank, t1 - timedelta(microseconds=1))
    assert [(r.root_id, r.kind) for r in before] == [(root["id"], "TANK_DIP")] and before[0].recorded_at == t0
    assert kobo.records(tank, t1) == ()
    # K3 reads the same through its own connection: the stored record_ids follow the as-known head
    first = kobo.assess(t1 - timedelta(microseconds=1)).window
    second = kobo.assess(t1).window
    assert first.record_ids == ((root["id"], root["id"]),) and second.record_ids == ()
    assert (first.revision, second.revision) == (1, 2)


def test_b3_tank_change_moves_the_dip_between_tanks(store, engine) -> None:  # noqa: F811
    twin = Site(engine, twin_tank(store), datetime(2026, 10, 20, tzinfo=timezone.utc))
    try:
        tanks = sorted(code for code, kind in twin.types.items() if kind == "FUEL_TANK")
        assert tanks == ["north-tank", "south-tank"]
        north, south = twin.assets["north-tank"], twin.assets["south-tank"]
        occurred = twin.start + timedelta(hours=10)
        root = twin.post(dip(north, "k3-b3-dip", occurred))
        t1 = twin.work_clock.now
        twin.post(correction(root, "k3-b3-fix", dip(south, "x", occurred), "Dipped the south tank"))
        just_before = t1 - timedelta(microseconds=1)
        assert [r.root_id for r in twin.records(north, just_before)] == [root["id"]]
        assert twin.records(north, t1) == ()
        assert twin.records(south, just_before) == ()
        moved = twin.records(south, t1)
        assert [(r.root_id, r.code, r.kind) for r in moved] == [(root["id"], root["public_code"], "TANK_DIP")]
    finally:
        twin.close()


def test_b4_cross_kind_correction_keeps_the_first_recording(store, engine) -> None:  # noqa: F811
    result = imported(store)
    probe = Site(engine, result, datetime(2026, 10, 20, tzinfo=timezone.utc))
    start, end = probe.start, probe.end
    probe.close()
    on_time = end + timedelta(minutes=10)
    kobo = Site(engine, result, on_time)
    try:
        tank = kobo.assets["fuel-tank"]
        occurred = start + timedelta(hours=13)
        body = "Fuel delivery of 300 L received, ticket KIS-DT-0001."
        root = kobo.post(oprec("k3-b4-log", body=body, occurred_at=iso(occurred)))   # T0 = end + 10 min, on time
        kobo.work_clock.now = t1 = end + timedelta(hours=2)                          # after end + 30 min
        kobo.post(correction(root, "k3-b4-fix", oprec(
            "x", kind="FUEL_DELIVERY", body=body, occurred_at=iso(occurred), unit="L", quantity="300",
            source_document_sha256=TICKET, asset_id=tank), "Retyped as a fuel delivery"))
        assert kobo.records(tank, t1 - timedelta(microseconds=1)) == ()
        after = kobo.records(tank, t1)
        assert len(after) == 1
        rec = after[0]
        assert (rec.kind, rec.code, rec.root_id, rec.root_recorded_at) == (
            "FUEL_DELIVERY", root["public_code"], root["id"], on_time)
        assert rec.quantity_l == Decimal("300")
        assert rules.limitations(gap_minutes=0, levels=[], records=after, accuracy_l=None, end=end) == ()
        # K3's stored windows keep both: before the correction the delivery is absent, after it is counted
        before_w = kobo.assess(t1 - timedelta(microseconds=1)).window
        after_w = kobo.assess(t1).window
        assert before_w.terms["deliveries_l"] == "0" and after_w.terms["deliveries_l"] == "300"
        # (Kobo has no accepted tank readings in this database, so the whole night is a reporting gap)
        assert after_w.limitations == ("REPORTING_GAP",) and after_w.record_ids == ((root["id"], after[0].head_id),)

        # the converse: a FUEL_DELIVERY root first recorded at end + 31 min is flagged
        kobo.work_clock.now = late = end + timedelta(minutes=31)
        late_root = kobo.post(oprec("k3-b4-late", kind="FUEL_DELIVERY", body="Fuel delivery of 150 L received.",
                                    occurred_at=iso(occurred + timedelta(hours=1)), unit="L", quantity="150",
                                    source_document_sha256=TICKET, asset_id=tank))
        flagged = kobo.assess(t1 + timedelta(hours=1)).window
        assert flagged.limitations == ("REPORTING_GAP", "DELIVERY_RECORDED_LATE") and flagged.terms["deliveries_l"] == "450"
        assert [r.root_recorded_at for r in kobo.records(tank, t1 + timedelta(hours=1))
                if r.root_id == late_root["id"]] == [late]
    finally:
        kobo.close()


# --- B5 Kobo is NOT_ASSESSED --------------------------------------------------------------------------------------------


def test_b5_kobo_is_not_assessed_for_want_of_sensor_accuracy(kobo) -> None:
    result = kobo.assess(kobo.end + timedelta(minutes=30))
    w = result.window
    assert result.appended and (w.state, w.reason, w.residual_low, w.residual_high) == (
        "NOT_ASSESSED", "NO_SENSOR_ACCURACY", None, None)
    assert (w.revision, w.night_date, w.window_start, w.window_end) == (1, NIGHT, kobo.start, kobo.end)
    assert w.recorded_at == kobo.end + timedelta(minutes=30) and w.parameter_version == "fuel-balance-1/v1"
    assert str(w.tank_asset_id) == kobo.assets["fuel-tank"] and str(w.generator_asset_id) == kobo.assets["generator"]
    assert w.terms["accuracy_l"] is None and len(w.input_sha256) == 64


# --- B6 store ---------------------------------------------------------------------------------------------------------


def test_b6_store(kobo, store, engine) -> None:  # noqa: F811
    closes = kobo.end + timedelta(minutes=30)
    with pytest.raises(FuelBalanceRefused) as open_:
        kobo.assess(closes - timedelta(microseconds=1))
    assert open_.value.code == "FUEL_BALANCE_WINDOW_OPEN" and kobo.count() == 0

    first = kobo.assess(closes + timedelta(hours=1))
    again = kobo.assess(closes + timedelta(hours=2))
    assert first.appended and not again.appended and again.window == first.window and kobo.count() == 1
    with pytest.raises(FuelBalanceRefused) as back:
        kobo.assess(closes + timedelta(minutes=30))
    assert back.value.code == "FUEL_BALANCE_CLOCK_BACKWARDS" and kobo.count() == 1

    # a new input (a dip in the window) is a new revision; the old one stays readable as known
    tank = kobo.assets["fuel-tank"]
    kobo.work_clock.now = closes + timedelta(hours=3)
    kobo.post(dip(tank, "k3-b6-dip", kobo.start + timedelta(hours=10)))
    third = kobo.assess(closes + timedelta(hours=4))
    assert third.appended and third.window.revision == 2 and kobo.count() == 2
    t, s, a = kobo.t, kobo.s, UUID(tank)
    assert kobo.fb.windows(t, s, a, NIGHT, NIGHT + timedelta(days=1), closes + timedelta(hours=3)) == (first.window,)
    assert kobo.fb.windows(t, s, a, NIGHT, NIGHT + timedelta(days=1), closes + timedelta(hours=4)) == (third.window,)
    assert kobo.fb.windows(t, s, a, NIGHT - timedelta(days=3), NIGHT, closes + timedelta(hours=4)) == ()
    assert kobo.fb.window(t, s, first.window.id) == first.window
    assert kobo.fb.window(t, s, uuid4()) is None
    for lo, hi, known in ((NIGHT, NIGHT, closes), (NIGHT, NIGHT - timedelta(days=1), closes),
                          (NIGHT, NIGHT + timedelta(days=1), closes.replace(tzinfo=None)),
                          (NIGHT, NIGHT + timedelta(days=1), closes.astimezone(timezone(timedelta(hours=3))))):
        with pytest.raises(ValueError, match="fuel balance windows need lo < hi and a UTC known_at"):
            kobo.fb.windows(t, s, a, lo, hi, known)

    twin = Site(engine, twin_tank(store), datetime(2026, 10, 20, tzinfo=timezone.utc))
    try:
        with pytest.raises(FuelBalanceRefused) as many:
            twin.assess(twin.end + timedelta(hours=1))
        assert many.value.code == "FUEL_BALANCE_ASSETS_UNSUPPORTED"
    finally:
        twin.close()
    assert kobo.count() == 2


def test_b6_cli(kobo, capsys) -> None:
    kobo.fb_clock.now = kobo.end + timedelta(hours=1)  # night 10-10 closed; 10-11 still open
    code = worker_main(["assess", "--site", "KOBO-001", "--from", "2026-10-10", "--to", "2026-10-12"], store=kobo.fb)
    lines = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert code == 0
    assert lines == [{"site_code": "KOBO-001", "night_date": "2026-10-10", "status": "APPENDED", "revision": 1,
                      "state": "NOT_ASSESSED", "reason": "NO_SENSOR_ACCURACY"},
                     {"site_code": "KOBO-001", "night_date": "2026-10-11", "status": "OPEN", "revision": None,
                      "state": None, "reason": None}]
    assert worker_main(["assess", "--site", "KOBO-001", "--from", "2026-10-10", "--to", "2026-10-11"],
                       store=kobo.fb) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "REUSED"
    assert worker_main(["assess", "--site", "NOPE-001", "--from", "2026-10-10", "--to", "2026-10-11"],
                       store=kobo.fb) == 2
