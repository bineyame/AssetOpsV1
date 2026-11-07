"""COV-PARTIAL U4: the `estate-coverage/2` PARTIAL Site on persisted rows (build sheet §4 U4).

One mini-grid Site through the real S4 chain: 2026-10-06 delivered, assessed and matched (S4 F01, a Finding at
08:00), 2026-10-07 without evidence. The two-day estate period reads the Site partly checked on the Portfolio,
Findings and Financials roots; the one-day period is unchanged. Needs ASSETOPS_TEST_DATABASE_URL (a `*_test` DB,
`assetops_covp_test` for this slice).
"""

from __future__ import annotations

from datetime import timedelta
from urllib.parse import urlencode

import pytest

from test_w301_estate_index_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from test_s1_bindings_postgres import engine, store  # noqa: F401 - the S4/S6 mini-grid fixtures
    from test_w301_estate_index_postgres import day_of, iso, mini  # noqa: F401 - the S4 runner + estate fixture
    from test_s6_action_store_postgres import CASES as S4_CASES
    from test_w302_evidence_scope_snapshot_postgres import evidence_read
    from test_w303_portfolio_fixture_postgres import pin_snapshots

    from assetops_backend.estate.portfolio import EstatePortfolioService
    from assetops_backend.estate.scope import PORTFOLIO_CURSOR_KEY_ENV
    from assetops_backend.estate_api import build_estate_router
    from assetops_backend.estate_evidence_money_api import build_estate_evidence_money_router
    from assetops_backend.estate_portfolio_api import build_estate_portfolio_router


def _roots(engine, tenant_id):
    """Every estate root over the W3-02 one-transaction reader (the W3-03 Postgres tests' composition)."""
    service = EstatePortfolioService(evidence_read(engine))
    app = FastAPI()
    allow = {"access": lambda request, code: None}
    for build in (build_estate_router, build_estate_evidence_money_router, build_estate_portfolio_router):
        app.include_router(build(service, lambda: tenant_id, **allow))
    client = TestClient(app)

    def ok(root, **params):
        response = client.get(f"/api/estate/{root}?" + urlencode(params))
        assert response.status_code == 200, response.text
        return response.json()
    return ok


def test_partly_checked_site_on_persisted_rows(mini, monkeypatch) -> None:  # noqa: F811
    monkeypatch.setenv(PORTFOLIO_CURSOR_KEY_ENV, "c7" * 32)  # test-only Portfolio deployment key
    runner, estate = mini
    run_case(runner)
    pin_snapshots(monkeypatch, lambda: runner.now + timedelta(minutes=1))
    ok = _roots(runner.engine, runner.tenant)
    one = day_of("2026-10-06")
    two = {"from": one["from"], "to": iso(runner_day(one) + timedelta(days=2))}
    site_id = str(runner.site)

    # The one-day period: CURRENT, and its `days` block names no gap.
    single = ok("findings", **one)
    (cov,) = single["coverage"]["sites"]
    assert single["status"] == "CURRENT" and cov["state"] == "CURRENT"
    assert cov["days"] == {"policy": "estate-coverage/2", "requested": 1, "checked": 1, "gaps": [],
                           "withheld": False, "text": None}
    (f01,) = single["rows"]

    portfolio = ok("portfolio", **two)
    disclosed = next(s for s in portfolio["scope_disclosure"]["sites"] if s["site_id"] == site_id)
    days = {"policy": "estate-coverage/2", "requested": 2, "checked": 1,
            "gaps": [{"day": "2026-10-07", "state": "UNASSESSED", "reason": "NO_ASSESSED_SELECTION"}],
            "withheld": False, "text": "1 of 2 days assessed · 1 day not available yet"}
    assert disclosed["coverage"]["state"] == "PARTIAL" and disclosed["coverage"]["days"] == days
    (p_cov,) = [s for s in portfolio["coverage"]["sites"] if s["site_id"] == site_id]
    assert p_cov["state"] == "PARTIAL" and p_cov["days"] == days
    assert portfolio["status"] == "PARTIAL"
    (p_row,) = [r for r in portfolio["rows"] if r["finding_id"] == f01["finding_id"]]
    assert p_row["consequence"]["amount"] is None and p_row["consequence"]["amount_low"] is None

    findings = ok("findings", **two)
    (f_cov,) = findings["coverage"]["sites"]
    assert findings["status"] == "UNKNOWN" and f_cov["state"] == "PARTIAL" and f_cov["days"] == days
    assert [r["finding_id"] for r in findings["rows"]] == [f01["finding_id"]]
    assert findings["rows"][0]["consequence"]["amount"] is None and findings["total_count"] is None

    money = ok("financials", **two, limit=100)
    assert money["status"] != "CURRENT"
    assert not [line for line in money["rows"] or () if line.get("site_id") == site_id]

    # The one-day period is unchanged after the two-day reads.
    assert ok("findings", **one) == single


def run_case(runner) -> None:
    from test_s4_finding_store_postgres import run_case as run
    run(runner, S4_CASES["F01"])


def runner_day(window: dict):
    from datetime import datetime
    return datetime.fromisoformat(window["from"].replace("Z", "+00:00"))
