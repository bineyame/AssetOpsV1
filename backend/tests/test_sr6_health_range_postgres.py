"""SR-6a (rev 10 §10.2, rev 10a §10a.1, D-SR.19-23): `site-health-range-1` on persisted rows.

One mini-grid Site through the real S4 chain (`test_sr5_range_overview_postgres`'s world: 2026-10-06 delivered,
assessed and matched; 2026-10-07 without evidence). Pins, on that world:
- registration and the two grouped reads run on the estate snapshot's one connection;
- diagnostics added per day give IN_CONTACT / PARTIAL_CONTACT / NO_CONTACT, and a pre-registration day NOT_EXPECTED;
- accepted readings count on the day their interval starts, cut at the ACCEPTED disposition's `decided_at`
  (D-SR.19): a cutoff before every decision counts none; diagnostics are cut at `received_at`;
- `days[]` equal SR-5a's days (ANALYSED <-> FINDINGS/CLEAR, every other state equal; D-SR.22);
- rows on vs off (D-ANY.10, D-SR.16): with the `dispatch.day` provider served and no stored row (every day an absent
  run), the body is identical to the compose body.
Needs ASSETOPS_TEST_DATABASE_URL (a `*_test` DB, `assetops_sr6_test` for this slice).
"""

from __future__ import annotations

import uuid
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from test_w301_estate_index_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text

    from test_s1_bindings_postgres import engine, store  # noqa: F401 - the S4/S6 mini-grid fixtures
    from test_w301_estate_index_postgres import mini  # noqa: F401 - the S4 runner + estate fixture
    from test_cov_partial_postgres import run_case
    from test_w302_evidence_scope_snapshot_postgres import evidence_read
    from test_w303_portfolio_fixture_postgres import pin_snapshots

    from assetops_backend.chain.period_read import SERVED_KINDS_ENV
    from assetops_backend.estate import coverage
    from assetops_backend.estate.portfolio import EstatePortfolioService
    from assetops_backend.estate.range_days import ANALYSED
    from assetops_backend.estate.scope import PORTFOLIO_CURSOR_KEY_ENV, estate_request
    from assetops_backend.estate.site_range import CLEAR, FINDINGS, site_range_body
    from assetops_backend.evidence.composition import health_registration
    from assetops_backend.sites.adapters.postgres_health_range import health_range_counts
    from assetops_backend.sites import site_health_range
    from assetops_backend.sites.site_health_range import (
        IN_CONTACT, NO_CONTACT, NOT_EXPECTED, PARTIAL_CONTACT, READINGS_ONLY)

    def health_range_body(service, tenant_id, code, req):
        return site_health_range.health_range_body(service, tenant_id, code, req, health_registration(),
                                                   health_range_counts)

D5 = datetime(2026, 10, 5, tzinfo=timezone.utc)
DAYS = ["2026-10-05", "2026-10-06", "2026-10-07", "2026-10-08"]


def _diagnostics(engine, tenant, site, gateway, start: datetime, count: int, step: timedelta) -> None:
    with engine.begin() as c:
        c.execute(text(
            "INSERT INTO gateway_diagnostic (id, tenant_id, site_id, gateway_id, sequence_epoch, diagnostic_sequence, "
            "observed_at, received_at, last_device_contact_by_source, queue_count, oldest_queue_age_seconds, "
            "disk_pressure, clock_offset_ms, mapping_error_count, payload_sha256, diagnostic_text) "
            "SELECT gen_random_uuid(), :t, :s, :g, :epoch, n, :at + n * :step, :at + n * :step, '{}'::jsonb, 0, NULL, "
            "'OK', 0, 0, repeat('a', 64), '{}' FROM generate_series(0, :count - 1) AS n"),
            {"t": tenant, "s": site, "g": gateway, "epoch": f"sr6-{uuid.uuid4().hex[:8]}", "at": start,
             "step": step, "count": count})


@pytest.fixture()
def world(mini, monkeypatch):  # noqa: F811
    monkeypatch.setenv(PORTFOLIO_CURSOR_KEY_ENV, "c7" * 32)  # test-only Portfolio deployment key
    runner, _ = mini
    run_case(runner)
    pin_snapshots(monkeypatch, lambda: runner.now + timedelta(minutes=1))
    with runner.engine.connect() as c:
        (gateway, registered), = c.execute(text(
            "SELECT id, registered_at FROM gateway WHERE tenant_id = :t AND site_id = :s"),
            {"t": runner.tenant, "s": runner.site}).all()
        site_code = c.execute(text("SELECT site_code FROM site WHERE id = :s"), {"s": runner.site}).scalar_one()
    service = EstatePortfolioService(evidence_read(runner.engine))
    req = replace(estate_request("portfolio", D5, D5 + timedelta(days=4)), lens="all")
    return runner, service, site_code, gateway, registered, req


def test_health_range_on_persisted_rows(world) -> None:
    runner, service, code, gateway, registered, req = world
    one, two = D5 + timedelta(days=1), D5 + timedelta(days=2)
    _diagnostics(runner.engine, runner.tenant, runner.site, gateway, one, 1440, timedelta(minutes=1))  # full day
    _diagnostics(runner.engine, runner.tenant, runner.site, gateway, two, 10, timedelta(minutes=1))    # partial
    out = health_range_body(service, runner.tenant, code, req)
    assert [d["day"] for d in out["days"]] == DAYS
    (g,) = out["gateways"]
    contact = {d["day"]: d["contact"] for d in g["days"]}
    assert registered == datetime(2026, 10, 7, 10, tzinfo=timezone.utc)  # the world's gateway registration
    assert contact == {"2026-10-05": NOT_EXPECTED, "2026-10-06": IN_CONTACT, "2026-10-07": PARTIAL_CONTACT,
                       "2026-10-08": NO_CONTACT}
    assert g["days"][1]["diagnostics"] == 1440 and g["days"][2]["diagnostics"] == 10
    by_source = {s["source_external_id"]: [(d["accepted_readings"], d["state"]) for d in s["days"]]
                 for s in out["sources"]}
    assert by_source["clinic-meter"] == [(0, "NO_READINGS"), (13, "READINGS"), (0, "NO_READINGS"),
                                         (0, "NO_READINGS")]
    assert by_source["fuel-level-sensor"] == [(0, "NO_READINGS")] * 4
    assert [(d["day"], d["state"]) for d in out["days"]] == [
        ("2026-10-05", "NOT_ANALYSED"), ("2026-10-06", ANALYSED), ("2026-10-07", "NOT_ANALYSED"),
        ("2026-10-08", "NOT_ANALYSED")]
    assert out["summary"] == {"days_requested": 4, "days_with_readings": 1, "days_without_readings": 0,
                              "gateways_in_contact_all_days": 0}


def test_readings_without_diagnostics_read_readings_only(world) -> None:
    """D-SR.20: readings on 10-06 arrived through a gateway registered on 10-07 with no status reports."""
    runner, service, code, _, _, req = world
    (g,) = health_range_body(service, runner.tenant, code, req)["gateways"]
    assert [d["contact"] for d in g["days"]] == [NOT_EXPECTED, READINGS_ONLY, NO_CONTACT, NO_CONTACT]


def test_cutoffs_disposition_for_readings_receipt_for_diagnostics(world) -> None:
    runner, _, _, gateway, _, req = world
    one = D5 + timedelta(days=1)
    _diagnostics(runner.engine, runner.tenant, runner.site, gateway, one, 10, timedelta(hours=1))
    with runner.engine.connect() as c:
        first, last = c.execute(text(
            "SELECT min(d.decided_at), max(d.decided_at) FROM ingestion_disposition d JOIN accepted_evidence e "
            "ON d.accepted_evidence_id = e.id WHERE e.site_id = :s AND d.decision = 'ACCEPTED'"),
            {"s": runner.site}).one()
        total = c.execute(text("SELECT count(*) FROM accepted_evidence WHERE site_id = :s"),
                          {"s": runner.site}).scalar_one()
        lo, hi = req.from_, req.to
        diag, reads = health_range_counts(c, runner.tenant, runner.site, lo, hi, last)
        assert sum(x["n"] for x in reads.values()) == total > 0
        _, none = health_range_counts(c, runner.tenant, runner.site, lo, hi, first - timedelta(microseconds=1))
        assert none == {}
        cut, _ = health_range_counts(c, runner.tenant, runner.site, lo, hi, one + timedelta(hours=4, minutes=30))
        assert sum(x["n"] for x in cut.values()) == 5  # receipts at 00:00..04:00
        assert sum(x["n"] for x in diag.values()) >= 10


def test_days_equal_the_range_overview(world) -> None:
    runner, service, code, _, _, req = world
    mine = {d["day"]: d for d in health_range_body(service, runner.tenant, code, req)["days"]}
    theirs = {d["day"]: d for d in site_range_body(service, runner.tenant, code, req)["days"]}
    assert list(mine) == list(theirs) == DAYS
    for day, d in mine.items():
        assert (d["state"] == ANALYSED) == (theirs[day]["state"] in (FINDINGS, CLEAR))
        if d["state"] != ANALYSED:
            assert d["state"] == theirs[day]["state"]


def test_rows_on_with_absent_runs_equals_rows_off(world, monkeypatch) -> None:
    runner, service, code, _, _, req = world
    from assetops_backend.chain.composition import build_dispatch_day_rows

    before = coverage.dispatch_rows_provider
    try:
        coverage.dispatch_rows_provider = None
        off = health_range_body(service, runner.tenant, code, req)
        monkeypatch.setenv(SERVED_KINDS_ENV, "dispatch.day,evidence.claim")
        built = build_dispatch_day_rows(runner.engine.url.render_as_string(hide_password=False))
        assert built is not None
        served = []

        def provider(*args):  # no stored `dispatch.day` row: every day is an absent run
            days = built[0](*args)
            served.append(days)
            return days
        coverage.dispatch_rows_provider = provider
        on = health_range_body(service, runner.tenant, code, req)
    finally:
        coverage.dispatch_rows_provider = before
    assert served and all(days is not None for days in served)
    assert on == off
