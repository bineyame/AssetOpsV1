"""DIESEL-K3 L2 parity (`.agent/build-sheet-DIESEL-1.md` §9d.6 C): K3's stored windows reproduce F0's readings band.

Needs `ASSETOPS_TEST_DATABASE_URL` naming a `*_test` database (K3: `assetops_k3_test`); skipped without it.

KISIWA-001 is registered by `tools/demo_combined_kisiwa.py` `register` (import 2026-09-29T09:00Z, install 09:30Z).
Nights 2, 4 and 6 (delivery, incident, after-phase dips): each run starts from F0's committed start state, is drafted
on the registered basis (product mini-grid v7, registered-kobo-publication v5), gets F0's actions through the probe's
own hook (`probe_kisiwa_fuel.apply_actions`), and is published and accepted through a real gateway. The delivery and
the dips are posted through `WorkService.post_operational_record` (K2). Each night is assessed by
`FuelBalanceService` and compared with `.agent/DIESEL-F0/probe-result.json` `nights[k-1]["readings"]`.
"""

from __future__ import annotations

import hashlib
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

REFERENCE = ROOT / ".agent" / "DIESEL-F0" / "probe-result.json"
IMPORT_AT = datetime(2026, 9, 29, 9, 0, tzinfo=timezone.utc)
INSTALL_AT = datetime(2026, 9, 29, 9, 30, tzinfo=timezone.utc)
SETUP_AT = "2026-09-29T11:00:00Z"
NIGHTS = (2, 4, 6)
TOLERANCE_L = Fraction(1, 100000)
TICKET_TEXT = "Fuel delivery ticket KIS-DT-0001, 300 L"
DELIVERY_BODY = "Fuel delivery of 300 L received, ticket KIS-DT-0001."
EARLY_N4 = datetime(2026, 10, 5, 9, 45, tzinfo=timezone.utc)
SITE = "KISIWA-001"


def _at(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _iso(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def run_start(k: int) -> datetime:
    return datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc) + timedelta(days=k - 1)


def night_date(k: int) -> date:
    return date(2026, 10, k)


class SetClock:
    """The fuel-balance store's virtual DB instant: whatever the test last set."""

    def __init__(self, now: datetime) -> None:
        self.now = now

    def __call__(self) -> datetime:
        return self.now


def _records(ref: dict, tank: str) -> dict[int, list[tuple[datetime, dict]]]:
    """Per night: (recorded_at, body) for K2's records, in recording order."""
    from test_w401_work_service_postgres import oprec

    dips = {d["at"]: d["dip_l"] for d in ref["dips"]}

    def dip(key: str, at: str, round_: str) -> tuple[datetime, dict]:
        litres = str(dips[at])
        return _at(at) + timedelta(minutes=15), oprec(
            key, kind="TANK_DIP", body=f"Tank dip at the {round_} round: {litres} L.", occurred_at=at, unit="L",
            quantity=litres, asset_id=tank)

    delivery = oprec("kisiwa-kis-delivery-1", kind="FUEL_DELIVERY", body=DELIVERY_BODY,
                     occurred_at="2026-10-03T07:00:00Z", unit="L", quantity="300",
                     source_document_sha256=hashlib.sha256(TICKET_TEXT.encode("ascii")).hexdigest(), asset_id=tank)
    return {
        2: [(datetime(2026, 10, 3, 7, 30, tzinfo=timezone.utc), delivery)],
        4: [dip("kisiwa-kis-dip-n4-0700", "2026-10-05T04:00:00Z", "07:00")],
        6: [dip("kisiwa-kis-dip-r6-1800", "2026-10-06T15:00:00Z", "18:00"),
            dip("kisiwa-kis-dip-r6-0600", "2026-10-07T03:00:00Z", "06:00")],
    }


@pytest.fixture(scope="module")
def kisiwa(tmp_path_factory):
    """The whole flow, in time order; every assessment result is kept for the tests below."""
    import pg_harness
    from sqlalchemy import create_engine, text
    from sqlalchemy.engine import make_url

    import demo_combined_kisiwa as kis
    import probe_kisiwa_fuel as probe
    import probe_kisiwa_nights as nights
    import test_s6_verification_replay as rp
    from execution_adapter import run_to_end
    from kisiwa import KisiwaRegistered
    from test_w401_work_service_postgres import PRINCIPAL, VirtualDbClock

    from assetops_backend.evidence.composition import build_link_rows_reader
    from assetops_backend.fuel_balance.composition import build_fuel_balance_store
    from assetops_backend.fuel_balance.service import FuelBalanceService
    from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore
    from assetops_backend.work.adapters.postgres_work_store import PostgresWorkStore
    from assetops_backend.work.service import WorkService

    url = make_url(URL)
    assert url.database and url.database.endswith("_test"), "Refusing a database not named *_test"
    pg_harness.fresh_database()
    registered = kis.register(URL, tmp_path_factory.mktemp("k3-register"), IMPORT_AT, INSTALL_AT)
    tenant, site = UUID(registered["tenant_id"]), UUID(registered["site_id"])
    ref = json.loads(REFERENCE.read_text(encoding="utf-8"))
    engine = create_engine(URL)
    with engine.connect() as c:
        tank = str(c.execute(text("SELECT id FROM asset WHERE site_id = :s AND asset_type = 'FUEL_TANK' "
                                  "AND retired_at IS NULL"), {"s": site}).scalar_one())

    foundation = PostgresFoundationStore(URL)
    work_clock = VirtualDbClock(INSTALL_AT + timedelta(days=1))
    work = PostgresWorkStore(URL, link_rows=build_link_rows_reader(), test_db_clock_override=work_clock)
    svc = WorkService(work)
    fb_clock = SetClock(INSTALL_AT)
    fb = build_fuel_balance_store(URL, test_db_clock_override=fb_clock)  # the production composition (DIESEL-1-R3g)
    balance = FuelBalanceService(fb)
    records = _records(ref, tank)
    out: dict = {"tenant": tenant, "site": site, "tank": UUID(tank), "ref": ref, "engine": engine, "fb": fb,
                 "fb_clock": fb_clock, "windows": {}, "published": {}}

    def assess(k: int, at: datetime):
        fb_clock.now = at
        return balance.assess_night(tenant, site, night_date(k))

    try:
        for k in NIGHTS:
            run_ref = ref["runs"][k - 1]
            start, end = run_start(k), run_start(k) + timedelta(days=1)
            soc, fuel = float(Fraction(run_ref["start"]["soc"])), float(Fraction(run_ref["start"]["fuel"]))
            reg = KisiwaRegistered(foundation, SETUP_AT)
            run = reg.draft(nights.day_document(soc, fuel), _iso(start), _iso(end))
            assert run.execution_status == "READY", [(r.kind, r.subject) for r in run.blocking_reasons]
            assert run.registered_basis is not None
            run, history = probe.apply_actions(run, probe.load_actions(), start)
            assert list(history) == run_ref["intervention_history"], (k, history)
            # physics guard: the action-applied run ends where F0's run k ended
            last = dict(run_to_end(run, reg.sim("v7")).trajectory.boundaries[-1].stocks)
            assert (last[probe.SOC], last[probe.FUEL]) == (Fraction(run_ref["end"]["soc"]),
                                                          Fraction(run_ref["end"]["fuel"])), (k, last)
            for recorded_at, body in records[k]:
                work_clock.now = recorded_at
                status, response = svc.post_operational_record(tenant, site, body, PRINCIPAL)
                assert status == 201, response
            if k == 4:  # as known: before the night's evidence is accepted (12:10Z)
                out["early"] = assess(k, EARLY_N4)
            out["published"][k] = rp._publish_and_accept(
                tmp_path_factory.mktemp(f"k3-night-{k}"), run, f"epoch-{k}", end + timedelta(minutes=10))
            print(f"K3 night {k} published {out['published'][k]}")
            out["windows"][k] = assess(k, end + timedelta(minutes=30))
        yield out
    finally:
        work.dispose()
        fb.dispose()
        engine.dispose()
        pg_harness.dispose(foundation)


def _exact(text_value) -> Fraction:
    from assetops_backend.actions.verification_rules import parse_exact

    value = parse_exact(text_value)
    assert value is not None, text_value
    return value


@pytest.mark.parametrize("k", NIGHTS)
def test_night_matches_f0_readings_band(kisiwa, k: int) -> None:
    result = kisiwa["windows"][k]
    w, night = result.window, kisiwa["ref"]["nights"][k - 1]
    want = night["readings"]
    assert result.appended and w.revision == (2 if k == 4 else 1)
    print(f"K3 night {k} window {w.state} reason={w.reason} gap={w.gap_minutes} spans={w.gap_spans} "
          f"limitations={w.limitations} terms={json.dumps(w.terms, sort_keys=True)}")
    exact = {
        "state": (w.state, want["state"]),
        "reason": (w.reason, None),
        "gap_minutes": (w.gap_minutes, want["gap_minutes"]),
        "opening": (_exact(w.terms["opening_l"]), Fraction(night["opening_reading_l"]["exact"])),
        "closing": (_exact(w.terms["closing_l"]), Fraction(night["closing_reading_l"]["exact"])),
        "D": (_exact(w.terms["deliveries_l"]), Fraction(want["deliveries"]["exact"])),
        "D_tol": (_exact(w.terms["delivery_tolerance_l"]), Fraction(want["delivery_tolerance"]["exact"])),
    }
    toleranced = {
        "loaded_litres": (_exact(w.terms["loaded_litres"]), Fraction(night["loaded_litres"]["exact"])),
        "use_low": (_exact(w.terms["use_low"]), Fraction(want["use_low"]["exact"])),
        "use_high": (_exact(w.terms["use_high"]), Fraction(want["use_high"]["exact"])),
        "residual_low": (w.residual_low, Fraction(want["residual_low"]["exact"])),
        "residual_high": (w.residual_high, Fraction(want["residual_high"]["exact"])),
    }
    failures = []
    for term, (got, ref) in exact.items():
        print(f"K3 night {k} exact {term}: K3 {got} F0 {ref}")
        if got != ref:
            failures.append(f"night {k} {term}: K3 {got} F0 {ref}")
    for term, (got, ref) in toleranced.items():
        delta = abs(got - ref)
        print(f"K3 night {k} toleranced {term}: K3 {got} F0 {ref} |delta| {delta} ({float(delta):.3e} L)")
        if delta > TOLERANCE_L:
            failures.append(f"night {k} {term}: K3 {got} F0 {ref} |delta| {delta}")
    assert not failures, "\n".join(failures)
    assert w.terms["idle_seconds"] == 0
    if k == 4:
        assert w.gap_spans == ((datetime(2026, 10, 4, 21, 45, tzinfo=timezone.utc),
                                datetime(2026, 10, 4, 23, 30, tzinfo=timezone.utc)),)
        assert w.limitations == ("REPORTING_GAP",)
    else:
        assert w.limitations == ()


def test_night_4_generator_kwh_equals_an_independent_sum(kisiwa) -> None:
    """§9c.3 L2 (a): K3's use comes only from accepted generator readings."""
    from sqlalchemy import text

    w = kisiwa["windows"][4].window
    with kisiwa["engine"].connect() as c:
        rows = c.execute(text(
            "SELECT normalized_value_text FROM accepted_evidence WHERE site_id = :s AND role = 'generator_power' "
            "AND interval_start >= :lo AND interval_end <= :hi"),
            {"s": kisiwa["site"], "lo": w.window_start, "hi": w.window_end}).scalars().all()
    total = sum((_exact(v) * Fraction(5, 60) for v in rows), Fraction(0))
    print(f"K3 night 4 generator_kwh K3 {w.terms['generator_kwh']} SQL {total} over {len(rows)} readings")
    assert _exact(w.terms["generator_kwh"]) == total


def test_night_4_as_known(kisiwa) -> None:
    early, late = kisiwa["early"], kisiwa["windows"][4]
    first, second = early.window, late.window
    assert early.appended and (first.revision, first.state, first.reason) == (1, "NOT_ASSESSED", "MISSING_OPENING")
    assert first.recorded_at == EARLY_N4
    assert (second.revision, second.state) == (2, "UNEXPLAINED")
    fb, t, s, a = kisiwa["fb"], kisiwa["tenant"], kisiwa["site"], kisiwa["tank"]
    lo, hi = night_date(4), night_date(5)
    assert fb.windows(t, s, a, lo, hi, datetime(2026, 10, 5, 10, 0, tzinfo=timezone.utc)) == (first,)
    assert fb.windows(t, s, a, lo, hi, datetime(2026, 10, 5, 12, 30, tzinfo=timezone.utc)) == (second,)
    assert fb.window(t, s, first.id) == first


def test_cli_reuses_night_6(kisiwa, capsys) -> None:
    from assetops_backend.fuel_balance.worker import main as worker_main

    kisiwa["fb_clock"].now = run_start(6) + timedelta(days=1, minutes=30)
    capsys.readouterr()
    code = worker_main(["assess", "--site", SITE, "--from", "2026-10-06", "--to", "2026-10-07"], store=kisiwa["fb"])
    lines = capsys.readouterr().out.splitlines()
    print("K3 CLI", lines)
    assert code == 0 and len(lines) == 1
    line = json.loads(lines[0])
    assert (line["site_code"], line["night_date"], line["status"], line["revision"]) == (
        SITE, "2026-10-06", "REUSED", 1)
