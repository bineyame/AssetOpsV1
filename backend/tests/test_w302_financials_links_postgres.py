"""W3-02 commit 4 (closure 5 B5): generated estate Financials line links followed into the W2 Site reads.

Each selected cold/EV line's `links.bridge` and `links.evidence` are followed through the matching W2 Site API
(`/api/sites/{code}/cold/financials` and `/cold/evidence`, `/api/sites/{code}/ev/financials` and `/ev/evidence`)
with exactly the link's query: the line's own selected window and row-local cutoff, never the estate day bounds.
Each read must succeed (no 422). A line whose row-local cutoff cannot be proved keeps the base Site route and
`Opens current Site view`. Mirrors `test_w302_evidence_links_postgres.py`. Needs ASSETOPS_TEST_DATABASE_URL.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from urllib.parse import parse_qs, urlsplit

import pytest

from test_w301_estate_index_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from fastapi.testclient import TestClient
    from sqlalchemy import text
    from test_w202_cold_replay_postgres import chain  # noqa: F401 - the W2-02 cold replay fixture
    from test_w203_cold_replay_postgres import opened, run
    from test_w204_cold_consequence import drain
    from test_w205b_ev_replay_postgres import chain as ev_chain  # noqa: F401 - the W2-05b EV replay fixture
    from test_w207_ev_money_postgres import golden_tariff, money
    from test_w301_estate_index_ev_postgres import settled
    from test_w301_estate_index_postgres import DAY, imported_before, watermark
    from test_w302_evidence_links_postgres import site_client
    from test_w302_money_comparability_postgres import _read_financials
    from assetops_backend.analytics.cold_site_reads import ColdSiteReadService
    from assetops_backend.analytics.composition import build_cold_read_service
    from assetops_backend.cold_site_api import build_cold_site_router
    from assetops_backend.estate import financials
    from assetops_backend.ev_site_api import build_ev_site_router
    from assetops_backend.financials.composition import build_cold_consequence_store, build_ev_site_read_service

CURRENT_VIEW = "Opens current Site view"


def at(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def follow(c: TestClient, href: str, page_suffix: str, api_suffix: str) -> dict:
    """Follow one generated Site page link into the matching Site API with exactly its query; assert a successful
    (non-422) read and return the link's query."""
    link = urlsplit(href)
    assert link.path.endswith(page_suffix), href
    response = c.get(f"/api{link.path.removesuffix(page_suffix)}{api_suffix}?{link.query}")
    assert response.status_code == 200, (href, response.status_code, response.text[:400])
    assert response.json(), f"the Site read returned an empty body for {href}"
    return {k: at(v[0]) for k, v in parse_qs(link.query).items()}


def line_window(line: dict) -> tuple[datetime, datetime]:
    return at(line["window_start"]), at(line["window_end"])


def cold_money(chain):  # noqa: F811
    """The real W2-02 excursion replay, W2-03 cold assessment and W2-04 consequence worker, imported before DAY."""
    built = opened("excursion", chain)
    run(built)
    drain(built)
    imported_before(built.engine, built.tenant_id, built.site_id, DAY - timedelta(days=1))
    return built


def assert_followed(c: TestClient, lines: list[dict], body: dict, mark: datetime, routes: dict[str, tuple[str, str]],
                    day: datetime) -> None:
    for line in lines:
        assert line["links"]["current_view_label"] is None, line["links"]
        bridge = follow(c, line["links"]["bridge"], *routes["bridge"])
        evidence = follow(c, line["links"]["evidence"], *routes["evidence"])
        assert bridge == evidence  # both links carry the same row-local window and cutoff
        assert (bridge["from"], bridge["to"]) == line_window(line)  # the line's window, never the estate day
        assert bridge["known_at"] == mark <= at(body["window"]["known_at"]) + timedelta(seconds=1)
        assert (bridge["from"], bridge["to"]) != (day, day + timedelta(days=1))


def test_w302_financials_cold_links_follow_selected_window_and_cutoff(chain) -> None:  # noqa: F811
    built = cold_money(chain)
    body = _read_financials(built.tenant_id, DAY)
    lines = [r for r in body["rows"] if r["domain"] == "cold_chain"]
    assert lines, [(r["line_key"], r["eligibility"]) for r in body["rows"]]
    mark = watermark(built.engine, built.site_id)
    reads = ColdSiteReadService(build_cold_read_service(URL), build_cold_consequence_store(URL))
    c = site_client(built, "COLDCHAIN", lambda registry: build_cold_site_router(registry, reads))
    assert_followed(c, lines, body, mark, {"bridge": ("/financials", "/cold/financials"),
                                           "evidence": ("/evidence", "/cold/evidence")}, DAY)


def test_w302_financials_ev_links_follow_selected_window_and_cutoff(ev_chain) -> None:  # noqa: F811
    built, _estate, day = settled(ev_chain, "complete")
    golden_tariff(built)
    outcomes = money(built)
    assert outcomes and all(o.succeeded for o in outcomes), [(o.error_code, o.error_detail) for o in outcomes]
    body = _read_financials(built.tenant_id, day)
    lines = [r for r in body["rows"] if r["domain"] == "ev_charging"]
    assert lines, [(r["line_key"], r["eligibility"]) for r in body["rows"]]
    mark = watermark(built.engine, built.site_id)
    reads = build_ev_site_read_service(URL)
    c = site_client(built, "EV_CHARGING", lambda registry: build_ev_site_router(registry, reads))
    try:
        assert_followed(c, lines, body, mark, {"bridge": ("/ev/financials", "/ev/financials"),
                                               "evidence": ("/ev/evidence", "/ev/evidence")}, day)
    finally:
        reads.dispose()


def test_w302_financials_links_fall_back_without_provable_cutoff(chain, monkeypatch) -> None:  # noqa: F811
    """TEST-SCOPED tamper: the link builder sees each real pinned window with a committed watermark one microsecond
    before its row-local cutoff, so `known <= watermark` cannot be proved (the money read itself is untouched).
    Every cold line then keeps the base Site route for `site`, `bridge` and `evidence` with `Opens current Site
    view`, never a windowed Site link."""
    built = cold_money(chain)
    original = financials.window_links
    seen = []

    def unprovable(code, domain, pin, cutoff, k):
        seen.append(pin)
        assert pin is not None and pin.get("known") is not None and pin["known"] == cutoff
        return original(code, domain, {**pin, "watermark": pin["known"] - timedelta(microseconds=1)}, cutoff, k)

    monkeypatch.setattr(financials, "window_links", unprovable)
    body = _read_financials(built.tenant_id, DAY)
    lines = [r for r in body["rows"] if r["domain"] == "cold_chain"]
    assert lines, [(r["line_key"], r["eligibility"]) for r in body["rows"]]
    with built.engine.connect() as c:
        code = c.execute(text("SELECT site_code FROM site WHERE id = :s"), {"s": built.site_id}).scalar_one()
    base = f"/sites/{code}"
    assert seen  # the real pinned windows reached the link builder
    for line in lines:
        assert line["links"] == {"site": base, "bridge": base, "evidence": base, "current_view_label": CURRENT_VIEW}
