"""DIESEL-K4a L2 (`.agent/build-sheet-DIESEL-1.md` §9j.8 B1-B6, §9k.5 B7-B9): the unexplained-fuel Finding over real
Postgres.

Kobo is imported as K3's B does (`test_s1_bindings_postgres.imported`); B7-B9 use the S4 power Site
(`test_s4_consequence_store_postgres.PowerSite`), which holds a stored dispatch Finding. Fuel windows are synthetic,
appended through `PostgresFuelBalanceStore`'s own transaction on a virtual DB clock. Requires
ASSETOPS_TEST_DATABASE_URL naming a `*_test` database.
"""

from __future__ import annotations

import hashlib
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from fractions import Fraction
from uuid import UUID, uuid4

import os

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

MIGRATION, PREVIOUS = "0056_unexplained_fuel_finding", "0055_fuel_balance_window"
REFUSED = "0056 downgrade requires no fuel_balance Findings or fuel residual consequences"
TABLE = "fuel_residual_consequence_revision"
UTC = timezone.utc
PRICED_NIGHT = date(2027, 1, 10)      # after the real publication instant, so the price is known at the window end
SECOND_NIGHT = date(2027, 1, 12)
POWER_NIGHT = date(2026, 10, 5)       # its window [10-05 15:00Z, 10-06 09:00Z) holds PowerSite's dispatch episode
SUBJECT_ARM = ("((domain = 'fuel_balance'::text) AND (subject_asset_id IS NOT NULL) AND "
               "(generator_asset_id IS NULL))")
MINUTES_ARM = ("((domain = 'fuel_balance'::text) AND (candidate_minutes IS NULL) AND (necessary_minutes IS NULL) "
               "AND (indeterminate_minutes IS NULL))")

if URL:
    import pg_harness
    from pg_harness import alembic_head
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError, IntegrityError
    from test_s1_bindings_postgres import _alembic, engine, imported, store  # noqa: F401
    from test_s4_assumptions_postgres import run_fixture
    from test_s4_consequence_store_postgres import POWER_DAY, PowerSite, _release_connections  # noqa: F401
    from test_w203_cold_migration_postgres import head

    from assetops_backend.actions.verification_rules import fmt, parse_exact
    from assetops_backend.analytics.composition import build_finding_read_service, build_finding_store
    from assetops_backend.chain.adapters.postgres_chain_read import _UNSETTLED
    from assetops_backend.chain.backfill import run_threads
    from assetops_backend.chain.composition import build_thread_sources, build_thread_store
    from assetops_backend.financials.adapters.postgres_assumption_store import PostgresAssumptionStore
    from assetops_backend.financials.adapters.postgres_consequence_store import PostgresConsequenceStore
    from assetops_backend.financials.composition import build_recompute_worker
    from assetops_backend.fuel_balance import finding_text as ft
    from assetops_backend.fuel_balance import rules
    from assetops_backend.fuel_balance.composition import build_fuel_finding_service
    from assetops_backend.scheduling.stages import chain_threads


class SetClock:
    def __init__(self, now: datetime) -> None:
        self.now = now

    def __call__(self) -> datetime:
        return self.now


class Fuel:
    """The fuel Finding service on a virtual clock over one Site, and synthetic window appends."""

    def __init__(self, engine, tenant_id: UUID, site_id: UUID) -> None:  # noqa: F811
        self.engine, self.t, self.s = engine, tenant_id, site_id
        with engine.connect() as c:
            assets = c.execute(text("SELECT id, asset_type FROM asset WHERE site_id = :s AND retired_at IS NULL"),
                               {"s": site_id}).all()
            self.tz = c.execute(text("SELECT timezone FROM site WHERE id = :s"), {"s": site_id}).scalar_one()
        self.tank = str(next(i for i, kind in assets if kind == "FUEL_TANK"))
        self.gen = str(next(i for i, kind in assets if kind == "GENERATOR"))
        self.clock = SetClock(datetime(2026, 11, 1, tzinfo=UTC))
        self.svc = build_fuel_finding_service(URL, test_db_clock_override=self.clock)
        self.store = self.svc.stores.fuel

    def put(self, night: date, state: str, low: str | None, high: str | None, *, gap: bool = False):
        """Append the night's next window revision, recorded at the window end + 1 h (or later)."""
        start, end = rules.night_window(night, self.tz)
        self.clock.now = max(self.clock.now + timedelta(minutes=1), end + timedelta(hours=1))
        spans = [[rules.iso(start + timedelta(hours=6, minutes=45)), rules.iso(start + timedelta(hours=8, minutes=30))]]

        def work(tx):
            latest = tx.latest(self.tank, night)
            row = {"tank_asset_id": self.tank, "generator_asset_id": self.gen, "night_date": night,
                   "window_start": start, "window_end": end, "state": state,
                   "reason": "MISSING_OPENING" if state == "NOT_ASSESSED" else None,
                   "residual_low": low, "residual_high": high, "gap_minutes": 105 if gap else 0,
                   "gap_spans": spans if gap else [], "limitations": ["REPORTING_GAP"] if gap else [],
                   "terms": {"accuracy_l": "10", "accuracy_revision_id": None, "sfc_revision_id": None,
                             "no_load_revision_id": None},
                   "evidence_ids": [], "record_ids": [],
                   "input_sha256": hashlib.sha256(f"{night}{state}{low}{self.clock.now}".encode()).hexdigest()}
            return tx.append(latest, row)
        return self.store.transaction(self.t, self.s, work)

    def raise_(self, night: date, after: timedelta = timedelta(minutes=1)):
        self.clock.now += after
        return self.svc.raise_night(self.t, self.s, night)

    def rows(self, sql: str, **p) -> list:
        with self.engine.connect() as c:
            return c.execute(text(sql), {"t": self.t, "s": self.s, **p}).all()

    def consequences(self, finding_id) -> list:
        return self.rows(f"SELECT * FROM {TABLE} WHERE finding_id = :f ORDER BY recorded_at", f=finding_id)

    def dispatch_money(self, finding_id) -> int:
        return self.rows("SELECT count(*) FROM financial_consequence_revision WHERE finding_id = :f",
                         f=finding_id)[0][0]

    def close(self) -> None:
        self.svc.dispose()


@pytest.fixture()
def kobo(store, engine):  # noqa: F811
    result = imported(store)
    owned = Fuel(engine, result.tenant.id, result.site.id)
    yield owned
    owned.close()


# --- B1 migration --------------------------------------------------------------------------------------------------


def checks(engine) -> dict:  # noqa: F811
    with engine.connect() as c:
        return dict(c.execute(text(
            "SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint "
            "WHERE conname IN ('finding_domain_subject', 'finding_revision_domain_minutes')")).all())


def shape(engine) -> tuple:  # noqa: F811
    with engine.connect() as c:
        cols = tuple(c.execute(text("SELECT column_name, data_type, is_nullable FROM information_schema.columns "
                                    "WHERE table_name = :t ORDER BY ordinal_position"), {"t": TABLE}).all())
        defs = dict(c.execute(text("SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint "
                                   "WHERE conrelid = to_regclass(:t)"), {"t": TABLE}).all())
        indexes = dict(c.execute(text("SELECT indexname, indexdef FROM pg_indexes WHERE tablename = :t"),
                                 {"t": TABLE}).all())
        triggers = tuple(c.execute(text("SELECT tgname, pg_get_triggerdef(oid) FROM pg_trigger "
                                        "WHERE tgrelid = to_regclass(:t) AND NOT tgisinternal"), {"t": TABLE}).all())
    return cols, defs, indexes, triggers


COLUMNS = ("id", "tenant_id", "site_id", "finding_id", "finding_revision_id", "fuel_balance_window_id", "model_id",
           "basis", "litres_low", "litres_high", "state", "price_reason", "price_revision_id", "price_assignment_id",
           "price_value", "currency", "amount_low", "amount_high", "price_known_at", "basis_sha256", "recorded_at")


def _widened(before: str, arm: str) -> str:
    """pg's text for `CHECK (old OR arm)`: the old expression nested one level deeper."""
    assert before.startswith("CHECK (") and before.endswith(")")
    return f"CHECK (({before[len('CHECK ('):-1]} OR {arm}))"


def test_b6_single_alembic_head(engine) -> None:  # noqa: F811
    from alembic.script import ScriptDirectory

    script = ScriptDirectory.from_config(_alembic())
    assert script.get_heads() == [alembic_head()] and head(engine) == alembic_head()
    assert script.get_revision(MIGRATION).down_revision == PREVIOUS


def test_b1_migration_up_down_up_on_empty_tables(store, engine) -> None:  # noqa: F811
    from alembic import command

    pg_harness.dispose(store)
    up_checks, up = checks(engine), shape(engine)
    cols, defs, indexes, triggers = up
    assert tuple(c[0] for c in cols) == COLUMNS
    assert {c[0] for c in cols if c[2] == "YES"} == {"price_reason", "price_revision_id", "price_assignment_id",
                                                      "price_value", "currency", "amount_low", "amount_high"}
    assert set(defs) >= {"fuel_residual_priced", "fuel_residual_finding_fk", "fuel_residual_revision_fk",
                         "fuel_residual_price_fk", "fuel_residual_window_fk", "fuel_residual_once",
                         "fuel_residual_scope_unique"}
    assert defs["fuel_residual_once"] == "UNIQUE (finding_revision_id)"
    assert defs["fuel_residual_finding_fk"] == ("FOREIGN KEY (tenant_id, site_id, finding_id) "
                                                "REFERENCES finding(tenant_id, site_id, id)")
    assert indexes["fuel_residual_finding"] == (
        "CREATE INDEX fuel_residual_finding ON public.fuel_residual_consequence_revision USING btree "
        "(tenant_id, site_id, finding_id, recorded_at)")
    assert triggers == (("fuel_residual_consequence_revision_immutable", "CREATE TRIGGER "
                         "fuel_residual_consequence_revision_immutable BEFORE DELETE OR UPDATE ON "
                         "public.fuel_residual_consequence_revision FOR EACH ROW EXECUTE FUNCTION "
                         "ledger_append_only()"),)
    config = _alembic()
    engine.dispose()
    try:
        command.downgrade(config, PREVIOUS)
        assert head(engine) == PREVIOUS and shape(engine) == ((), {}, {}, ())
        down_checks = checks(engine)
        assert "fuel_balance" not in " ".join(down_checks.values())
        assert up_checks["finding_domain_subject"] == _widened(down_checks["finding_domain_subject"], SUBJECT_ARM)
        assert up_checks["finding_revision_domain_minutes"] == _widened(
            down_checks["finding_revision_domain_minutes"], MINUTES_ARM)
        command.upgrade(config, "head")
    finally:
        if head(engine) != alembic_head():
            command.upgrade(config, "head")
    assert shape(engine) == up and checks(engine) == up_checks


def _downgrade_refused(engine) -> None:  # noqa: F811
    from alembic import command

    config = _alembic()
    engine.dispose()
    try:
        with pytest.raises(RuntimeError, match=REFUSED):
            command.downgrade(config, PREVIOUS)
    finally:
        if head(engine) != alembic_head():
            command.upgrade(config, "head")
    assert head(engine) == alembic_head()


def test_b1_downgrade_refused_with_a_fuel_finding_and_rows_are_immutable(kobo, engine) -> None:  # noqa: F811
    kobo.put(PRICED_NIGHT, "UNEXPLAINED", "45", "60")
    opened = kobo.raise_(PRICED_NIGHT)
    assert opened.status == "OPENED"
    (row,) = kobo.consequences(opened.finding_id)
    for sql in (f"UPDATE {TABLE} SET litres_low = '1' WHERE id = :i", f"DELETE FROM {TABLE} WHERE id = :i"):
        with pytest.raises(DBAPIError, match="append-only"):
            with engine.begin() as c:
                c.execute(text(sql), {"i": row.id})
    kobo.close()
    _downgrade_refused(engine)


def _raw_consequence(c, kobo, finding_id, revision_id, window_id, **over) -> None:
    p = {"id": uuid4(), "t": kobo.t, "s": kobo.s, "f": finding_id, "r": revision_id, "w": window_id,
         "state": "UNPRICED", "reason": "NO_PRICE", "pr": None, "pv": None, "cur": None, "al": None, "ah": None,
         "known": datetime(2027, 1, 1, tzinfo=UTC), **over}
    c.execute(text(
        f"INSERT INTO {TABLE} (id, tenant_id, site_id, finding_id, finding_revision_id, fuel_balance_window_id, "
        "model_id, basis, litres_low, litres_high, state, price_reason, price_revision_id, price_value, currency, "
        "amount_low, amount_high, price_known_at, basis_sha256, recorded_at) VALUES (:id, :t, :s, :f, :r, :w, "
        "'fuel-residual-1', 'UNEXPLAINED_FUEL_AT_DECLARED_PRICE', '1', '2', :state, :reason, :pr, :pv, :cur, :al, "
        ":ah, :known, repeat('a', 64), :known)"), p)


def test_b1_priced_check_and_subject_check_hold_below_the_service(kobo, engine) -> None:  # noqa: F811
    kobo.put(PRICED_NIGHT, "UNEXPLAINED", "45", "60")
    kobo.raise_(PRICED_NIGHT)
    (fid, rid, wid) = kobo.rows("SELECT f.id, r.id, CAST(r.claim->>'fuel_balance_window_id' AS uuid) FROM finding f "
                                "JOIN finding_revision r ON r.finding_id = f.id WHERE f.domain = 'fuel_balance'")[0]
    price_rev = kobo.rows(f"SELECT price_revision_id FROM {TABLE}")[0][0]
    cases = [{"state": "PRICED", "reason": None, "pr": price_rev, "pv": Decimal("1.25"), "cur": "USD"},  # no amount
             {"pr": price_rev, "pv": Decimal("1.25"), "cur": "USD"},                                    # unpriced + price
             {"state": "PRICED", "reason": "NO_PRICE", "pr": price_rev, "pv": Decimal("1.25"), "cur": "USD",
              "al": "1", "ah": "2"}]                                                                    # priced + reason
    for over in cases:
        with pytest.raises(IntegrityError, match="fuel_residual_priced"):
            with engine.begin() as c:
                _raw_consequence(c, kobo, fid, rid, wid, **over)
    with pytest.raises(IntegrityError, match="finding_domain_subject"):
        with engine.begin() as c:
            c.execute(text(
                "INSERT INTO finding (id, tenant_id, site_id, finding_key, domain, mechanism, analytic_id, "
                "generator_asset_id, subject_asset_id, anchor_start, anchor_assessment_revision_id, matcher_version, "
                "opened_at, created_at) SELECT :id, tenant_id, site_id, 'x', 'fuel_balance', mechanism, analytic_id, "
                ":g, subject_asset_id, anchor_start, anchor_assessment_revision_id, matcher_version, opened_at, "
                "created_at FROM finding WHERE id = :f"), {"id": uuid4(), "g": kobo.gen, "f": fid})


def test_b1_downgrade_refused_with_only_a_consequence_row(store, engine, capsys) -> None:  # noqa: F811
    """A consequence row citing a dispatch Finding (no fuel_balance Finding anywhere) still refuses the downgrade."""
    site = PowerSite(store, engine, capsys)
    try:
        fuel = Fuel(engine, site.tenant, site.site)
        window = fuel.put(POWER_NIGHT, "UNEXPLAINED", "45", "60")
        dispatch = site.on(POWER_DAY)
        with engine.begin() as c:
            _raw_consequence(c, fuel, dispatch["finding_id"], dispatch["id"], window.id)
        assert fuel.rows("SELECT count(*) FROM finding WHERE domain = 'fuel_balance'")[0][0] == 0
        fuel.close()
    finally:
        site.prices.dispose()
        site.store.dispose()
    _downgrade_refused(engine)


# --- B2 Kobo's existing Findings and the fuel-cost trigger ---------------------------------------------------------


def test_b2_dispatch_rows_byte_equal_and_no_fuel_cost_work(store, engine, capsys) -> None:  # noqa: F811
    site = PowerSite(store, engine, capsys)
    fuel = Fuel(engine, site.tenant, site.site)
    try:
        def mini() -> tuple:
            return (tuple(fuel.rows("SELECT * FROM finding WHERE domain = 'mini_grid' ORDER BY id")),
                    tuple(fuel.rows("SELECT * FROM finding_revision WHERE domain = 'mini_grid' ORDER BY id")))
        before, work = mini(), fuel.rows("SELECT count(*) FROM financial_consequence_work")[0][0]
        trigger = fuel.rows("SELECT pg_get_triggerdef(oid) FROM pg_trigger "
                            "WHERE tgname = 'financial_consequence_dirty_on_finding_revision'")[0][0]
        assert "WHEN ((new.domain = 'mini_grid'::text))" in trigger
        fuel.put(POWER_NIGHT, "UNEXPLAINED", "45", "60")
        assert fuel.raise_(POWER_NIGHT).status == "OPENED"
        assert mini() == before
        # must fail if the trigger's WHEN is dropped: the fuel revision would enqueue fuel-cost work
        assert fuel.rows("SELECT count(*) FROM financial_consequence_work")[0][0] == work
    finally:
        fuel.close()
        site.prices.dispose()
        site.store.dispose()


# --- B3-B5 raise lifecycle, threads and reads ----------------------------------------------------------------------


def test_b3_b4_b5_lifecycle_threads_and_reads(kobo, engine, capsys) -> None:  # noqa: F811
    prices = PostgresAssumptionStore(URL)
    try:
        run_fixture(prices, capsys, "v1")
    finally:
        prices.dispose()
    kobo.put(PRICED_NIGHT, "UNEXPLAINED", "95.657", "144.343", gap=True)
    opened = kobo.raise_(PRICED_NIGHT)
    assert opened.status == "OPENED"
    (money,) = kobo.consequences(opened.finding_id)
    assert money.state == "PRICED" and money.currency == "USD" and money.price_value == Decimal("1.25")
    assert parse_exact(money.amount_low) == Fraction("95.657") * Fraction(5, 4)
    assert parse_exact(money.amount_high) == Fraction("144.343") * Fraction(5, 4)
    assert kobo.dispatch_money(opened.finding_id) == 0
    rev = kobo.rows("SELECT * FROM finding_revision WHERE id = :r", r=opened.revision_id)[0]
    assert (rev.domain, rev.transition, rev.lifecycle, rev.claim_level, rev.title, rev.mechanism) == (
        "fuel_balance", "OPENED", "SUPPORTED", "COMPLETE", ft.TITLE, "UNEXPLAINED_FUEL")
    assert rev.candidate_minutes is None and rev.window_assessment_revision_id is None
    assert rev.limitations[:2] == [ft.NOT_WHY, ft.margin_line("10")] and rev.limitations[2].startswith(
        "The tank sensor sent no readings from ")
    root = kobo.rows("SELECT * FROM finding WHERE id = :f", f=opened.finding_id)[0]
    assert (root.generator_asset_id, str(root.subject_asset_id), root.matcher_version) == (
        None, kobo.tank, "fuel-finding/1")
    assert root.finding_key == f"fuel:{kobo.tank}:{PRICED_NIGHT.isoformat()}"
    assert kobo.raise_(PRICED_NIGHT).status == "UNCHANGED"
    before_withdrawal = kobo.clock.now
    kobo.put(PRICED_NIGHT, "WITHIN_MARGIN", "-5", "10")
    withdrawn = kobo.raise_(PRICED_NIGHT)
    assert withdrawn.status == "WITHDRAWN" and withdrawn.finding_id == opened.finding_id
    assert len(kobo.consequences(opened.finding_id)) == 1   # no consequence for NO_LONGER_SUPPORTED
    assert kobo.rows("SELECT lifecycle FROM finding_revision WHERE id = :r", r=withdrawn.revision_id)[0][0] == \
        "NO_LONGER_SUPPORTED"

    # B5: the reads as known before and after the withdrawal
    lo = datetime(2027, 1, 1, tzinfo=UTC)
    hi = datetime(2027, 2, 1, tzinfo=UTC)
    (old,) = kobo.store.fuel_findings(kobo.t, kobo.s, lo, hi, before_withdrawal)
    (now,) = kobo.store.fuel_findings(kobo.t, kobo.s, lo, hi, None)
    assert (old.lifecycle, old.revision_no, old.consequence["state"]) == ("SUPPORTED", 1, "PRICED")
    assert (now.lifecycle, now.revision_no, now.consequence) == ("NO_LONGER_SUPPORTED", 2, None)
    assert kobo.store.fuel_finding(kobo.t, kobo.s, opened.finding_id, before_withdrawal).revision_id == \
        opened.revision_id
    assert kobo.store.fuel_findings(kobo.t, kobo.s, hi, hi + timedelta(days=1), None) == ()
    with pytest.raises(ValueError, match="fuel findings need lo < hi and UTC instants"):
        kobo.store.fuel_findings(kobo.t, kobo.s, hi, lo, None)

    # B3/B4: a second night's UNEXPLAINED Finding is occurrence 2 on the same thread
    kobo.put(SECOND_NIGHT, "UNEXPLAINED", "41", "70")
    second = kobo.raise_(SECOND_NIGHT)
    assert second.status == "OPENED" and second.finding_id != opened.finding_id
    with engine.connect() as c:
        assert c.execute(_UNSETTLED, {"t": kobo.t, "s": kobo.s, "k": None}).scalar() is True
    reader, threads = build_thread_sources(URL), build_thread_store(URL)
    try:
        run_threads(reader, threads, kobo.t, kobo.s)
    finally:
        reader.dispose()
        threads.dispose()
    (thread,) = kobo.rows("SELECT * FROM finding_thread WHERE site_id = :s")
    assert (thread.mechanism, thread.subject_kind, thread.subject_ref, thread.finding_type) == (
        "UNEXPLAINED_FUEL", "ASSET", kobo.tank, "UNEXPLAINED_FUEL@fuel-finding/1")
    occ = kobo.rows("SELECT finding_id, occurrence_no FROM finding_thread_occurrence WHERE thread_id = :i "
                    "ORDER BY occurrence_no", i=thread.id)
    assert [(str(f), n) for f, n in occ] == [(str(opened.finding_id), 1), (str(second.finding_id), 2)]
    # R8: the board stays unsettled until the threads consumer has consumed the finding.revised events
    out = chain_threads(URL, {"tenant_id": str(kobo.t), "site_id": str(kobo.s)})
    assert out["code"] == "OK", out
    with engine.connect() as c:
        assert c.execute(_UNSETTLED, {"t": kobo.t, "s": kobo.s, "k": None}).scalar() is False


def test_b3_no_price_declared_is_unpriced(kobo) -> None:
    kobo.put(PRICED_NIGHT, "UNEXPLAINED", "45", "60")
    opened = kobo.raise_(PRICED_NIGHT)
    (row,) = kobo.consequences(opened.finding_id)
    assert (row.state, row.price_reason, row.price_value, row.amount_low) == ("UNPRICED", "NO_PRICE", None, None)
    assert kobo.raise_(date(2027, 2, 1)).status == "NO_WINDOW"
    kobo.put(SECOND_NIGHT, "BELOW_MATERIALITY", "10", "30")
    assert kobo.raise_(SECOND_NIGHT).status == "NO_FINDING"
    assert kobo.rows("SELECT count(*) FROM assessment_revision WHERE analytic_id = 'fuel-balance-1'")[0][0] == 1


# --- B7-B9 the dispatch readers, the price recompute and the evidence path (§9k.5) -------------------------------


@pytest.fixture()
def power(store, engine, capsys):  # noqa: F811
    site = PowerSite(store, engine, capsys)
    fuel = Fuel(engine, site.tenant, site.site)
    fuel.put(POWER_NIGHT, "UNEXPLAINED", "45", "60")
    opened = fuel.raise_(POWER_NIGHT)
    assert opened.status == "OPENED"
    yield site, fuel, opened
    fuel.close()
    site.prices.dispose()
    site.store.dispose()


def test_b7_findings_over_excludes_the_fuel_finding(power) -> None:
    site, fuel, opened = power
    dispatch = site.on(POWER_DAY)
    lo, hi = POWER_DAY, POWER_DAY + timedelta(days=1)
    findings = build_finding_store(URL)
    over = [str(f["finding_id"]) for f in findings.findings_over(site.tenant, site.site, lo, hi)]
    assert over == [str(dispatch["finding_id"])]
    fuel_only = findings.findings_over(site.tenant, site.site, lo, hi, domain="fuel_balance",
                                       analytic_id="fuel-balance-1")
    assert [str(f["finding_id"]) for f in fuel_only] == [str(opened.finding_id)]   # non-vacuous
    state = build_finding_read_service(URL).window_state(site.tenant, site.site, POWER_DAY.date())
    assert str(opened.finding_id) not in {str(f["finding_id"]) for f in state["findings"]}


def test_b8_recompute_never_derives_on_the_fuel_finding(power) -> None:
    site, fuel, opened = power
    worker = build_recompute_worker(URL)
    assert all(o.succeeded for o in worker.run_pending(site.tenant, site.site))
    dispatch = site.on(POWER_DAY)
    before = fuel.dispatch_money(dispatch["finding_id"])
    site.publish("v1")   # ASSUMPTION_PUBLISHED over every October night
    outcomes = worker.run_pending(site.tenant, site.site)
    assert outcomes and all(o.succeeded for o in outcomes), [(o.cause, o.error_code) for o in outcomes]
    assert fuel.dispatch_money(dispatch["finding_id"]) > before          # the dispatch Finding is re-priced
    assert fuel.dispatch_money(opened.finding_id) == 0                   # never the fuel Finding
    store = PostgresConsequenceStore(URL)
    try:
        targets = store.latest_revisions_overlapping(site.tenant, site.site, POWER_DAY - timedelta(days=1), None)
    finally:
        store.dispose()
    assert str(opened.finding_id) not in {str(f) for f, _ in targets}
    assert str(dispatch["finding_id"]) in {str(f) for f, _ in targets}


def test_b9_the_evidence_path_no_ops_on_the_fuel_finding(power) -> None:
    site, fuel, opened = power
    worker = build_recompute_worker(URL)
    worker.run_pending(site.tenant, site.site)
    r = site.runner
    r.submit([site.power(POWER_DAY + timedelta(hours=8, minutes=35), "20")], r.tick("2026-10-30T11:00:00Z"))
    queued = fuel.rows("SELECT id FROM financial_consequence_work WHERE cause = 'EVIDENCE_ACCEPTED' "
                       "AND finding_id = :f", f=opened.finding_id)
    assert queued, "the 0012 trigger enqueues EVIDENCE_ACCEPTED work for the overlapping fuel revision"
    worker.run_pending(site.tenant, site.site)
    attempts = fuel.rows("SELECT outcome, no_op_reason FROM financial_consequence_work_attempt "
                         "WHERE work_id = ANY(:w)", w=[q[0] for q in queued])
    assert attempts and all(a == ("SUCCEEDED", "EVIDENCE_ASSET_NOT_RELEVANT") for a in attempts), attempts
    assert fuel.dispatch_money(opened.finding_id) == 0
