"""DIESEL-K4a L2 parity (`.agent/build-sheet-DIESEL-1.md` §9j.8 C): Kisiwa's night-4 unexplained-fuel Finding.

Needs `ASSETOPS_TEST_DATABASE_URL` naming a `*_test` database (K4: `assetops_k4_test`); skipped without it.

K3 part C's flow for night 4 only, reusing its helpers by import (`host/tests/test_k3_fuel_balance_parity.py`):
KISIWA-001 registered by `tools/demo_combined_kisiwa.py` `register`, night 4 drafted on the registered basis, F0's
actions applied through the probe's hook, the 07:00 dip posted through K2, published and accepted through a real
gateway; then `assess` and `raise` at the run end + 30 min through the production composition
(`build_fuel_finding_service`), then the existing threads step (`chain.backfill.run_threads`).
"""

from __future__ import annotations

import json
import os
import sys
from datetime import date, datetime, timedelta, timezone
from fractions import Fraction
from pathlib import Path
from uuid import UUID

import pytest

ROOT = Path(__file__).resolve().parents[2]
for extra in (ROOT / "backend" / "tests", ROOT / "tools", ROOT / "host", Path(__file__).resolve().parent):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)"
)

K = 4
TZ = "Africa/Dar_es_Salaam"
EXPECTED_CLAIM = ("About 95.7–144.3 L left the tank on the night of 4 Oct (6 pm to noon) that the generator's "
                  "modelled use and the recorded deliveries don't explain.")
EXPECTED_GAP = "The tank sensor sent no readings from 00:45 to 02:30."
EXPECTED_MONEY = ("Worth about 119.57–180.43 USD at your declared 1.25 USD per litre "
                  "(a modelled range that includes the stated margin)")


@pytest.fixture(scope="module")
def night4(tmp_path_factory):
    import pg_harness
    from sqlalchemy import create_engine, text
    from sqlalchemy.engine import make_url

    import demo_combined_kisiwa as kis
    import probe_kisiwa_fuel as probe
    import probe_kisiwa_nights as nights
    import test_s6_verification_replay as rp
    from execution_adapter import run_to_end
    from kisiwa import KisiwaRegistered
    from test_k3_fuel_balance_parity import (
        IMPORT_AT, INSTALL_AT, REFERENCE, SETUP_AT, SetClock, _iso, _records, night_date, run_start)
    from test_w401_work_service_postgres import PRINCIPAL, VirtualDbClock

    from assetops_backend.chain.backfill import run_threads
    from assetops_backend.chain.composition import build_thread_sources, build_thread_store
    from assetops_backend.evidence.composition import build_link_rows_reader
    from assetops_backend.fuel_balance.composition import build_fuel_finding_service
    from assetops_backend.fuel_balance.service import FuelBalanceService
    from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore
    from assetops_backend.work.adapters.postgres_work_store import PostgresWorkStore
    from assetops_backend.work.service import WorkService

    url = make_url(URL)
    assert url.database and url.database.endswith("_test"), "Refusing a database not named *_test"
    pg_harness.fresh_database()
    registered = kis.register(URL, tmp_path_factory.mktemp("k4a-register"), IMPORT_AT, INSTALL_AT)
    tenant, site = UUID(registered["tenant_id"]), UUID(registered["site_id"])
    ref = json.loads(REFERENCE.read_text(encoding="utf-8"))
    engine = create_engine(URL)
    with engine.connect() as c:
        tank = str(c.execute(text("SELECT id FROM asset WHERE site_id = :s AND asset_type = 'FUEL_TANK' "
                                  "AND retired_at IS NULL"), {"s": site}).scalar_one())
    foundation = PostgresFoundationStore(URL)
    work_clock = VirtualDbClock(INSTALL_AT + timedelta(days=1))
    work = PostgresWorkStore(URL, link_rows=build_link_rows_reader(), test_db_clock_override=work_clock)
    clock = SetClock(INSTALL_AT)
    findings = build_fuel_finding_service(URL, test_db_clock_override=clock)   # the production composition
    balance = FuelBalanceService(findings.stores.fuel)
    try:
        run_ref = ref["runs"][K - 1]
        start, end = run_start(K), run_start(K) + timedelta(days=1)
        soc, fuel = float(Fraction(run_ref["start"]["soc"])), float(Fraction(run_ref["start"]["fuel"]))
        reg = KisiwaRegistered(foundation, SETUP_AT)
        run = reg.draft(nights.day_document(soc, fuel), _iso(start), _iso(end))
        assert run.execution_status == "READY", [(r.kind, r.subject) for r in run.blocking_reasons]
        run, history = probe.apply_actions(run, probe.load_actions(), start)
        assert list(history) == run_ref["intervention_history"], history
        last = dict(run_to_end(run, reg.sim("v7")).trajectory.boundaries[-1].stocks)
        assert (last[probe.SOC], last[probe.FUEL]) == (Fraction(run_ref["end"]["soc"]),
                                                      Fraction(run_ref["end"]["fuel"]))
        for recorded_at, body in _records(ref, tank)[K]:
            work_clock.now = recorded_at
            status, response = WorkService(work).post_operational_record(tenant, site, body, PRINCIPAL)
            assert status == 201, response
        rp._publish_and_accept(tmp_path_factory.mktemp("k4a-night-4"), run, "epoch-4", end + timedelta(minutes=10))
        clock.now = end + timedelta(minutes=30)
        assessed = balance.assess_night(tenant, site, night_date(K))
        raised = findings.raise_night(tenant, site, night_date(K))
        reader, threads = build_thread_sources(URL), build_thread_store(URL)
        try:
            steps = run_threads(reader, threads, tenant, site)
        finally:
            reader.dispose()
            threads.dispose()
        yield {"tenant": tenant, "site": site, "tank": tank, "ref": ref, "engine": engine, "assessed": assessed,
               "raised": raised, "steps": steps, "findings": findings, "clock": clock}
    finally:
        work.dispose()
        findings.dispose()
        engine.dispose()
        pg_harness.dispose(foundation)


def _rows(night4, sql: str, **p) -> list:
    from sqlalchemy import text

    with night4["engine"].connect() as c:
        return c.execute(text(sql), {"s": night4["site"], **p}).all()


def test_night4_finding_as_stored_and_rendered(night4) -> None:
    from assetops_backend.actions.verification_rules import parse_exact
    from assetops_backend.fuel_balance import finding_text as ft

    raised, w = night4["raised"], night4["assessed"].window
    assert w.state == "UNEXPLAINED" and raised.status == "OPENED"
    store = night4["findings"].stores.fuel
    ff = store.fuel_finding(night4["tenant"], night4["site"], raised.finding_id, None)
    assert ff.lifecycle == "SUPPORTED" and ff.window == w
    claim = _rows(night4, "SELECT claim FROM finding_revision WHERE id = :r", r=raised.revision_id)[0][0]
    assert (parse_exact(claim["residual_low"]), parse_exact(claim["residual_high"])) == (w.residual_low,
                                                                                      w.residual_high)
    band = night4["ref"]["nights"][3]["readings"]
    for got, want in ((w.residual_low, band["residual_low"]["exact"]), (w.residual_high, band["residual_high"]["exact"])):
        delta = abs(got - Fraction(want))
        print(f"K4a night 4 band: stored {got} F0 {want} |delta| {float(delta):.3e} L")
        assert delta <= Fraction(1, 100000)
    c = ff.consequence
    print(f"K4a night 4 consequence: {json.dumps(c, default=str, sort_keys=True)}")
    assert c["state"] == "PRICED" and c["currency"] == "USD" and Fraction(c["price_value"]) == Fraction(5, 4)
    assert parse_exact(c["amount_low"]) == w.residual_low * Fraction(5, 4)
    assert parse_exact(c["amount_high"]) == w.residual_high * Fraction(5, 4)
    lines = ft.finding_lines(ff, TZ)
    print("K4a night 4 lines:", json.dumps(lines, ensure_ascii=False, indent=1))
    assert (lines["claim"], lines["gap"], lines["money"]) == (EXPECTED_CLAIM, EXPECTED_GAP, EXPECTED_MONEY)
    assert _rows(night4, "SELECT count(*) FROM financial_consequence_revision WHERE finding_id = :f",
                 f=raised.finding_id)[0][0] == 0


def test_night4_price_is_kisiwa_diesel_v1(night4) -> None:
    from assetops_backend.financials.composition import build_trial_comparison_ports

    raised, w = night4["raised"], night4["assessed"].window
    (row,) = _rows(night4, "SELECT price_revision_id, price_value FROM fuel_residual_consequence_revision "
                           "WHERE finding_id = :f", f=raised.finding_id)
    again = build_trial_comparison_ports(URL).price_selection(night4["tenant"], night4["site"], w.window_start,
                                                              w.window_end, w.window_end)
    (v1,) = _rows(night4, "SELECT id FROM financial_assumption_revision WHERE site_id = :s "
                          "AND assumption_key = 'diesel_price_per_litre' ORDER BY recorded_at LIMIT 1")
    assert str(row.price_revision_id) == str(again.revision_id) == str(v1[0])


def test_night4_thread(night4) -> None:
    raised = night4["raised"]
    (thread,) = _rows(night4, "SELECT id, mechanism, subject_kind, subject_ref, finding_type FROM finding_thread "
                              "WHERE site_id = :s AND mechanism = 'UNEXPLAINED_FUEL'")
    assert (thread.subject_kind, thread.subject_ref, thread.finding_type) == (
        "ASSET", night4["tank"], "UNEXPLAINED_FUEL@fuel-finding/1")
    occ = _rows(night4, "SELECT finding_id, occurrence_no FROM finding_thread_occurrence WHERE thread_id = :i",
                i=thread.id)
    assert [(str(f), n) for f, n in occ] == [(str(raised.finding_id), 1)]


def test_night4_kis4_pure_check_passes_on_this_database(night4) -> None:
    import demo_combined_rows as demo_rows

    from assetops_backend.financials.composition import build_trial_comparison_ports

    def dicts(sql: str) -> list[dict]:
        from sqlalchemy import text

        with night4["engine"].connect() as c:
            return [dict(r._mapping) for r in c.execute(text(sql), {"s": night4["site"]})]

    windows = {str(r["id"]): r for r in dicts("SELECT id, residual_low, residual_high, window_start, window_end "
                                              "FROM fuel_balance_window WHERE site_id = :s")}
    findings = dicts("SELECT DISTINCT ON (r.finding_id) r.finding_id, r.id AS revision_id, r.lifecycle, "
                     "r.claim->>'fuel_balance_window_id' AS window_id FROM finding_revision r WHERE r.site_id = :s "
                     "AND r.domain = 'fuel_balance' ORDER BY r.finding_id, r.revision_no DESC")
    consequences = dicts("SELECT * FROM fuel_residual_consequence_revision WHERE site_id = :s")
    dispatch = dicts("SELECT finding_id, amount_low, amount_high FROM financial_consequence_revision "
                     "WHERE site_id = :s")
    select = build_trial_comparison_ports(URL).price_selection
    prices = {}
    for f in findings:
        w = windows[str(f["window_id"])]
        p = select(night4["tenant"], night4["site"], w["window_start"], w["window_end"], w["window_end"])
        prices[str(f["window_id"])] = {"state": p.state, "revision_id": p.revision_id, "value": p.value}
    out = demo_rows.kis4(windows, findings, consequences, prices, dispatch)
    print("K4a KIS-4 on the night-4 database:", out)
    assert out["supported"] == 1 and out["priced"] == 1
