"""SR-5a (rev 9 §9.4): the `site-range-overview-1` body on persisted rows.

One mini-grid Site through the real S4 chain (`test_cov_partial_postgres`'s world): 2026-10-06 delivered, assessed
and matched (S4 F01, a Finding at 08:00), 2026-10-07 without evidence. Pins, on that world:
- the body's coverage entry and partial money equal the Portfolio's for the same range and cutoff;
- the per-day states (FINDINGS, NOT_ANALYSED) and the gaps-equal-coverage rule;
- rows on vs off (D-ANY.10, D-SR.16): with the `dispatch.day` provider served and no stored row (every day an
  absent run), the body is identical to the compose body.
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
    from assetops_backend.estate.site_range import FINDINGS, NOT_ANALYSED, STATE_OF_REASON, site_range_body
    from assetops_backend.estate_portfolio_api import build_estate_portfolio_router
    from assetops_backend.estate_api import build_estate_router


def _instant(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


@pytest.fixture()
def world(mini, monkeypatch):  # noqa: F811
    monkeypatch.setenv(PORTFOLIO_CURSOR_KEY_ENV, "c7" * 32)  # test-only Portfolio deployment key
    runner, _ = mini
    run_case(runner)
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
    one = day_of("2026-10-06")
    window = {"from": one["from"], "to": iso(_instant(one["from"]) + timedelta(days=2))}
    (site,) = [s for s in ok("scope", **window)["sites"] if s["site_id"] == str(runner.site)]
    req = replace(estate_request("portfolio", _instant(window["from"]), _instant(window["to"])), lens="all")

    def body():
        return site_range_body(service, runner.tenant, site["site_code"], req)
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
