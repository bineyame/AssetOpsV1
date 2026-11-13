"""SR-7b (rev 10 §10.3, D-SR.24/25): the `site-claim-limit-range-1` body on persisted rows.

One mini-grid Site through the real S4 chain (`test_cov_partial_postgres`'s world, as SR-5a's Postgres test):
2026-10-06 delivered, assessed and matched, 2026-10-07 without evidence. Pins, on that world:
- each day row equals `reduce_day` of the one-day claim-limit compose (`ClaimLimitReadService.claim_limit_on`, the
  projection the one-day read and the AR-4 fallback share) for the same day, revision and cutoff;
- rows on vs off (D-ANY.10, D-SR.16): with the `dispatch.day` provider served and no stored row (every day an
  absent run), the body is identical to the compose body.
Needs ASSETOPS_TEST_DATABASE_URL (a `*_test` DB, `assetops_sr7_test` for this slice).
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from urllib.parse import urlencode
from uuid import UUID

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

    from assetops_backend.analytics import claim_limit_read as w1
    from assetops_backend.chain.period_read import SERVED_KINDS_ENV
    from assetops_backend.estate import coverage
    from assetops_backend.estate.claim_limit_range import NO_SELECTION, claim_limit_range_body
    from assetops_backend.estate.portfolio import EstatePortfolioService
    from assetops_backend.estate.scope import estate_request
    from assetops_backend.estate_api import build_estate_router


def _instant(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


@pytest.fixture()
def world(mini, monkeypatch):  # noqa: F811
    runner, _ = mini
    run_case(runner)
    pin_snapshots(monkeypatch, lambda: runner.now + timedelta(minutes=1))
    store = evidence_read(runner.engine)
    service = EstatePortfolioService(store)
    app = FastAPI()
    app.include_router(build_estate_router(service, lambda: runner.tenant, access=lambda request, code: None))
    client = TestClient(app)
    one = day_of("2026-10-06")
    window = {"from": one["from"], "to": iso(_instant(one["from"]) + timedelta(days=2))}
    response = client.get("/api/estate/scope?" + urlencode(window))
    assert response.status_code == 200, response.text
    (site,) = [s for s in response.json()["sites"] if s["site_id"] == str(runner.site)]
    req = estate_request("evidence", _instant(window["from"]), _instant(window["to"]))

    def body():
        return claim_limit_range_body(service, runner.tenant, site["site_code"], req)
    return runner, store, body


def test_each_day_equals_reduce_day_of_the_one_day_compose(world) -> None:
    runner, store, body = world
    out = body()
    assert [d["day"] for d in out["days"]] == ["2026-10-06", "2026-10-07"]
    assert out["summary"]["days_requested"] == 2
    k = _instant(out["window"]["known_at"])
    checked = 0
    for row in out["days"]:
        if row["revision_id"] is None:
            assert row["state"] == NO_SELECTION and row["link"] is None
            continue
        with store._connect() as c, c.begin():
            projection = store.claim_limits.claim_limit_on(c, runner.tenant, runner.site, date.fromisoformat(row["day"]),
                                                           UUID(row["revision_id"]), k, basis_mode="live")
        reduced = w1.reduce_day(projection)
        assert (row["state"], row["current_ceiling"], row["ceiling_statement"], row["available"]) == (
            reduced["state"], reduced["current_ceiling"], reduced["ceiling_statement"], reduced["available"])
        assert row["window_assessment_revision_id"] == (
            None if reduced["window_assessment_revision_id"] is None else str(reduced["window_assessment_revision_id"]))
        assert row["link"] == f"/sites/{out['site']['site_code']}/evidence?day={row['day']}&revision={row['revision_id']}"
        checked += 1
    assert checked >= 1  # the delivered day has a selected window revision: the comparison ran


def test_rows_on_with_absent_runs_equals_rows_off(world, monkeypatch) -> None:
    runner, _, body = world
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


def test_each_row_link_opens_to_a_200(world) -> None:
    """D-SR.45 J4: the drill-in of every selected day opens the one-day claim-limit read for the same day and
    revision (the data route behind the `/sites/{code}/evidence?day=&revision=` page link)."""
    from assetops_backend.analytics.adapters.postgres_assessment_store import PostgresAssessmentStore
    from assetops_backend.analytics.claim_limit_read import ClaimLimitReadService
    from assetops_backend.claim_limit_api import build_claim_limit_router

    runner, _, body = world
    out = body()
    code = out["site"]["site_code"]
    assessments = PostgresAssessmentStore(URL)
    try:
        app = FastAPI()
        app.include_router(build_claim_limit_router(
            ClaimLimitReadService(assessments), {code: (code, runner.tenant, runner.site)}.get,
            gate=lambda c, t, s: (True, "test: gate open")))
        client = TestClient(app)
        opened = 0
        for row in out["days"]:
            if row["link"] is None:
                continue
            assert row["link"] == f"/sites/{code}/evidence?day={row['day']}&revision={row['revision_id']}"
            response = client.get(f"/api/sites/{code}/performance/dispatch/windows/{row['day']}/claim-limit",
                                  params={"revision": row["revision_id"]})
            assert response.status_code == 200, response.text
            opened += 1
        assert opened >= 1
    finally:
        assessments._connect_engine().dispose()
