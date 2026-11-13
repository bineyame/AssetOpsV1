"""SR-5a (rev 9 §9.4, rev 10a): the `site-range-overview-1` body on persisted rows, on existing Postgres worlds only.

- S4 F01 (`test_cov_partial_postgres`'s world, 2 days): coverage entry, card, partial money and status equal the
  Portfolio's; FINDINGS / NOT_ANALYSED and gaps == coverage; rows on vs off (D-ANY.10, D-SR.16) incl. absent runs.
- S4 F01 + the stale step (`test_s4_finding_read_postgres`): STILL_PROCESSING for an open job, then for an assessed
  but unmatched day (D-SR.28); FINDINGS after the match pass.
- S4 F01 + chain backfill step (a) (`test_idx_gaps_postgres` p5): NO_READINGS from the real stored day grades.
- All S4 cases + the clean day (21 days): FINDINGS, CLEAR, NOT_ANALYSED, totals, Portfolio equality, the coverage-wins
  log on F08's READINGS_CONFLICT day, and the drill-in check against `/overview?date=D`.
Not reached on any existing world (packet question): NOT_EXPECTED, READINGS_CONFLICT with day grades, an OVERLAPPING
or SUMMED money day (no priced mini-grid line in the S4 worlds).
Needs ASSETOPS_TEST_DATABASE_URL (a `*_test` DB, `assetops_sr5_test` for this slice).
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta
from urllib.parse import urlencode

import pytest

from test_w301_estate_index_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from test_s1_bindings_postgres import engine, store  # noqa: F401 - the S4/S6 mini-grid fixtures
    from test_w301_estate_index_postgres import day_of, iso, mini  # noqa: F401 - the S4 runner + estate fixture
    from test_cov_partial_postgres import run_case
    from test_w302_evidence_scope_snapshot_postgres import evidence_read
    from test_w303_portfolio_fixture_postgres import pin_snapshots

    from assetops_backend.chain.period_read import SERVED_KINDS_ENV
    from assetops_backend.estate import coverage
    from assetops_backend.estate.portfolio import EstatePortfolioService
    from assetops_backend.estate.scope import PORTFOLIO_CURSOR_KEY_ENV, estate_request
    from assetops_backend.estate.site_range import (CLEAR, FINDINGS, NO_READINGS, NOT_ANALYSED, NOT_EXPECTED,
                                                     STATE_OF_REASON,
                                                     STILL_PROCESSING, site_range_body)
    from assetops_backend.estate_portfolio_api import build_estate_portfolio_router
    from assetops_backend.estate_api import build_estate_router


def _instant(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def _build(runner, monkeypatch, first: str, days: int):
    """The Portfolio and the range body over `[first, first + days)` on the runner's persisted rows."""
    monkeypatch.setenv(PORTFOLIO_CURSOR_KEY_ENV, "c7" * 32)  # test-only Portfolio deployment key
    pin_snapshots(monkeypatch, lambda: runner.now + timedelta(minutes=1))
    service = EstatePortfolioService(evidence_read(runner.engine))
    app = FastAPI()
    for build in (build_estate_router, build_estate_portfolio_router):
        app.include_router(build(service, lambda: runner.tenant, access=lambda request, code: None))
    client = TestClient(app)

    def ok(root, **params):
        response = client.get(f"/api/estate/{root}?" + urlencode(params))
        assert response.status_code == 200, response.text
        return response.json()
    one = day_of(first)
    window = {"from": one["from"], "to": iso(_instant(one["from"]) + timedelta(days=days))}
    (site,) = [s for s in ok("scope", **window)["sites"] if s["site_id"] == str(runner.site)]
    req = replace(estate_request("portfolio", _instant(window["from"]), _instant(window["to"])), lens="all")

    def body():
        return site_range_body(service, runner.tenant, site["site_code"], req)
    return ok, window, body


def _equals_portfolio(runner, ok, window, out) -> dict:
    """Portfolio equality (rev 9 §9.4): coverage entry, OPERATING_COST card, partial money and status."""
    portfolio = ok("portfolio", **window)
    (entry,) = [s for s in portfolio["coverage"]["sites"] if s["site_id"] == str(runner.site)]
    assert out["coverage"] == {k: v for k, v in entry.items() if k != "money"}
    assert out["money"]["partial"] == entry.get("money")
    (card,) = [c for c in portfolio["value_cards"] if c["key"] == "OPERATING_COST"]
    assert out["money"]["card"] == card
    assert out["status"] == portfolio["status"]  # a one-Site estate: the same status rule
    return portfolio


def _gaps_equal_coverage(out) -> None:
    """The consistency requirement: non-FINDINGS/CLEAR/NOT_EXPECTED/STILL_PROCESSING days == `coverage.days.gaps`."""
    gaps = {(g["day"], STATE_OF_REASON[g["reason"]]) for g in out["coverage"]["days"]["gaps"]}
    assert {(d["day"], d["state"]) for d in out["days"]
            if d["state"] not in (FINDINGS, CLEAR, NOT_EXPECTED, STILL_PROCESSING)} == gaps


@pytest.fixture()
def world(mini, monkeypatch):  # noqa: F811
    runner, _ = mini
    run_case(runner)
    ok, window, body = _build(runner, monkeypatch, "2026-10-06", 2)
    return runner, ok, window, body


def test_range_body_equals_portfolio_and_days_on_persisted_rows(world) -> None:
    runner, ok, window, body = world
    out = body()
    portfolio = ok("portfolio", **window)
    (entry,) = [s for s in portfolio["coverage"]["sites"] if s["site_id"] == str(runner.site)]
    assert out["coverage"] == {k: v for k, v in entry.items() if k != "money"}
    assert out["coverage"]["state"] == "PARTIAL"
    assert out["money"]["partial"] == entry.get("money")
    assert out["status"] == portfolio["status"] == "PARTIAL"  # a one-Site estate: the same status rule

    states = [(d["day"], d["state"]) for d in out["days"]]
    assert states == [("2026-10-06", FINDINGS), ("2026-10-07", NOT_ANALYSED)]
    gaps = {(g["day"], STATE_OF_REASON[g["reason"]]) for g in out["coverage"]["days"]["gaps"]}
    assert {(d["day"], d["state"]) for d in out["days"] if d["state"] not in (FINDINGS, "CLEAR", "NOT_EXPECTED")} \
        == gaps
    assert out["days"][0]["finding_count"] == 1 and out["days"][1]["finding_count"] is None
    assert out["findings"]["count"] == 1
    assert out["dispatch"]["days_requested"] == 2 and out["dispatch"]["days_analysed"] == 1
    assert out["dispatch"]["days_with_findings"] == 1


def test_rows_on_with_absent_runs_equals_rows_off(world, monkeypatch) -> None:
    runner, _, _, body = world
    from assetops_backend.chain.composition import build_dispatch_day_rows

    before = coverage.dispatch_rows_provider
    try:
        coverage.dispatch_rows_provider = None
        off = body()
        monkeypatch.setenv(SERVED_KINDS_ENV, "dispatch.day,evidence.claim")
        built = build_dispatch_day_rows(runner.engine.url.render_as_string(hide_password=False))
        assert built is not None
        served = []

        def provider(*args):  # no stored `dispatch.day` row: every day is an absent run
            days = built[0](*args)
            served.append(days)
            return days
        coverage.dispatch_rows_provider = provider
        on = body()
    finally:
        coverage.dispatch_rows_provider = before
    assert served and all(days is not None for days in served)  # the rows path ran, not the kill switch
    assert on == off



CLEAN_DAY = [{"do": "deliver", "decided": "2026-10-30T08:00:00Z", "blocks": [  # `test_s4_finding_read_postgres`'s
    {"from": "2026-10-25T08:00:00Z", "to": "2026-10-25T09:00:00Z", "pv": "5", "dis": "5", "soc": "80",  # clean day
     "stop_before": True, "stop_after": True}]}, {"do": "assess"}]
#: The S4 F01-F08 Site (`test_s4_finding_read_postgres.EXPECTED_DAYS`) plus its complete day without a candidate.
ALL_CASES_DAYS = {
    "2026-10-05": "NOT_ANALYSED", "2026-10-06": "FINDINGS", "2026-10-07": "NOT_ANALYSED", "2026-10-08": "FINDINGS",
    "2026-10-09": "FINDINGS", "2026-10-10": "NOT_ANALYSED", "2026-10-11": "FINDINGS", "2026-10-12": "NOT_ANALYSED",
    "2026-10-13": "FINDINGS", "2026-10-14": "NOT_ANALYSED", "2026-10-15": "FINDINGS", "2026-10-16": "NOT_ANALYSED",
    "2026-10-17": "NOT_ANALYSED", "2026-10-18": "NOT_ANALYSED",
    "2026-10-19": "CLEAR",  # F08's ambiguous cohort: READINGS_CONFLICT by the day rule; coverage (no day grades) wins
    "2026-10-20": "NOT_ANALYSED", "2026-10-21": "CLEAR", "2026-10-22": "NOT_ANALYSED", "2026-10-23": "NOT_ANALYSED",
    "2026-10-24": "NOT_ANALYSED", "2026-10-25": "CLEAR"}


def test_all_s4_cases_day_states_totals_portfolio_and_drill_in(mini, monkeypatch, caplog) -> None:  # noqa: F811
    from test_s4_finding_store_postgres import SPEC, run_case as run

    runner, _ = mini
    for case in SPEC["cases"]:
        run(runner, case)
    for step in CLEAN_DAY:
        runner.step(step)
    runner.match()
    ok, window, body = _build(runner, monkeypatch, "2026-10-05", 21)
    with caplog.at_level("WARNING", logger="assetops.site_range"):
        out = body()
    _equals_portfolio(runner, ok, window, out)
    assert out["status"] == "PARTIAL" and out["coverage"]["state"] == "PARTIAL"
    assert {d["day"]: d["state"] for d in out["days"]} == ALL_CASES_DAYS
    _gaps_equal_coverage(out)
    # Coverage wins (D-SR.22): the persisted F08 day reads READINGS_CONFLICT by the day rule, coverage names no gap
    mismatches = [r.getMessage() for r in caplog.records if "site_range_day_mismatch" in r.getMessage()]
    assert mismatches == ["site_range_day_mismatch site=KOBO-001 day=2026-10-19 state=READINGS_CONFLICT "
                          "coverage=none"], mismatches
    for d in out["days"]:
        if d["state"] == NOT_ANALYSED:
            assert (d["finding_count"], d["money"], d["money_state"], d["accepted_readings"]) == \
                (None, None, "WITHHELD", None), d
        else:  # analysed: counted, read, and no priced line on this Site (no tariff in the S4 world)
            assert (d["finding_count"] > 0) == (d["state"] == FINDINGS), d
            assert d["money"] is None and d["money_state"] == "NO_ELIGIBLE_LINES", d
            assert isinstance(d["accepted_readings"], int) and d["accepted_readings"] > 0, d
    analysed = [d for d in out["days"] if d["state"] in (FINDINGS, CLEAR)]
    assert out["dispatch"] == {"days_requested": 21, "days_analysed": len(analysed),
                               "days_with_findings": sum(1 for d in analysed if d["state"] == FINDINGS),
                               "days_with_retired_findings": sum(1 for d in analysed if d["retired_finding_count"]),
                               "accepted_readings": sum(d["accepted_readings"] for d in analysed)}
    assert out["dispatch"]["days_analysed"] == 9 and out["dispatch"]["days_with_findings"] == 6
    assert out["money"]["card"]["state"] == "NO_LINE" and out["money"]["quantity"] is None
    assert out["findings"]["count"] == 8

    # Drill-in consistency: each analysed day's FINDINGS/CLEAR against whether `/overview?date=D` selects a Finding.
    from sqlalchemy import text
    from test_s4_schedule_tick_postgres import FAST, make_tick
    from test_s5_overview_postgres import Gates, overview_client

    from assetops_backend.evidence.adapters.postgres_evidence_ledger import PostgresEvidenceLedger
    from assetops_backend.scheduling.tick import TickLimits
    from assetops_backend.site_overview.composition import build_site_overview_read

    tick, _ = make_tick(TickLimits(**FAST))
    read = build_site_overview_read(URL, PostgresEvidenceLedger(URL), environment=tick.environment)
    client = overview_client(read, {"KOBO-001": ("KOBO-001", runner.tenant, runner.site)}, Gates())
    selected = {}
    for d in analysed:
        response = client.get(f"/api/sites/KOBO-001/overview?date={d['day']}")
        assert response.status_code == 200, response.text
        selected[d["day"]] = response.json()["known_finding"]
    # D-SR.50: agreement. The board's Findings on a day = members (finding_count) + retired (retired_finding_count);
    # F05's 10-21 Finding is NO_LONGER_SUPPORTED, so 10-21 reads CLEAR with one retired Finding.
    by_day = {d["day"]: d for d in analysed}
    for day, kf in selected.items():
        assert (kf is not None) == (by_day[day]["finding_count"] + by_day[day]["retired_finding_count"] > 0), day
    assert by_day["2026-10-21"]["state"] == "CLEAR" and by_day["2026-10-21"]["retired_finding_count"] == 1
    assert by_day["2026-10-21"]["finding_count"] == 0
    with runner.engine.connect() as c:
        lifecycle = c.execute(text("SELECT lifecycle FROM finding_revision WHERE id = :r"),
                              {"r": selected["2026-10-21"]["revision_id"]}).scalar_one()
    assert lifecycle == "NO_LONGER_SUPPORTED"


def test_open_job_then_unmatched_day_reads_still_processing(world) -> None:
    """STILL_PROCESSING twice on persisted rows (`test_s4_finding_read_postgres`'s stale step): a late block leaves an
    open assessment job on 10-06, then the assessed but not yet matched selection; the match pass clears it."""
    runner, ok, window, body = world
    runner.step({"do": "deliver", "decided": "2026-10-31T08:00:00Z", "blocks": [
        {"from": "2026-10-06T08:25:00Z", "to": "2026-10-06T08:30:00Z", "pv": "41", "only": ["pv"]}]})
    for _ in range(2):  # open job, then assessed but unmatched
        out = body()
        assert [(d["day"], d["state"]) for d in out["days"]] == [("2026-10-06", STILL_PROCESSING),
                                                                   ("2026-10-07", NOT_ANALYSED)]
        assert out["days"][0]["money_state"] == "WITHHELD" and out["days"][0]["money"] is None
        # pending work beside the 10-07 gap: not a clean PARTIAL, so the gap reads as unknown (COV-PARTIAL §2.3)
        assert out["coverage"]["state"] == "UNKNOWN"
        _equals_portfolio(runner, ok, window, out)
        _gaps_equal_coverage(out)
        assert out["dispatch"]["days_with_findings"] == 0
        runner.step({"do": "assess"})
    runner.match()
    out = body()
    assert [(d["day"], d["state"]) for d in out["days"]] == [("2026-10-06", FINDINGS), ("2026-10-07", NOT_ANALYSED)]
    _equals_portfolio(runner, ok, window, out)


def test_no_readings_days_from_the_stored_chain_grades(world, monkeypatch) -> None:
    """NO_READINGS on stored chain day rows (`test_idx_gaps_postgres` p5's world): the S4 case delivers dispatch
    blocks only, so the chain backfill step (a) grades every day NO_DATA; with the real `EstateClaims.day_grades`
    provider the range days and the coverage gaps are NO_READINGS on both days."""
    from sqlalchemy import text

    from assetops_backend.chain.backfill import main as backfill
    from assetops_backend.chain.composition import build_chain_reader, build_estate_claims
    from assetops_backend.site_outcomes.read import SiteRef

    runner, ok, window, body = world
    monkeypatch.setenv("DATABASE_URL", URL)
    assert backfill(["--site", "KOBO-001", "--steps", "a"]) == 0
    with runner.engine.connect() as c:
        code, name, kind, tz = c.execute(text("SELECT site_code, name, site_type, timezone FROM site "
                                              "WHERE tenant_id = :t AND id = :s"),
                                         {"t": runner.tenant, "s": runner.site}).one()
    ref = SiteRef(runner.tenant, runner.site, code, name, kind, tz)
    reader, dispose = build_chain_reader(URL)
    before = coverage.day_grades_provider
    try:
        claims = build_estate_claims(lambda: reader, lambda: None, lambda c: ref if c == code else None)
        coverage.day_grades_provider = claims.day_grades
        out = body()
        portfolio = _equals_portfolio(runner, ok, window, out)
    finally:
        coverage.day_grades_provider = before
        dispose()
    assert [(d["day"], d["state"]) for d in out["days"]] == [("2026-10-06", NO_READINGS),
                                                               ("2026-10-07", NO_READINGS)]
    assert [g["reason"] for g in out["coverage"]["days"]["gaps"]] == ["NO_READINGS", "NO_READINGS"]
    _gaps_equal_coverage(out)
    assert all((d["finding_count"], d["money_state"], d["accepted_readings"]) == (None, "WITHHELD", None)
               for d in out["days"])
    assert out["dispatch"]["days_analysed"] == 0 and portfolio["status"] == out["status"]

