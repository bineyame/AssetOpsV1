"""W3-02 commit 2 (c2-q3, closure 5 B5): generated estate Evidence row links followed into the W2 Site reads.

Each selected cold/EV row's `links.site_readiness` is followed through the matching W2 Site API
(`/api/sites/{code}/cold/evidence`, `/api/sites/{code}/ev/evidence`) with the row's exact window and row-local
cutoff, and the read must succeed (no 422) for that window. A row without a provable cutoff keeps the base Site
route and `Opens current Site view`. The link-shape tests in `test_w302_evidence_scope_snapshot_postgres.py` and
`test_w302_evidence_ev_postgres.py` stay shape-only. Needs ASSETOPS_TEST_DATABASE_URL.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from types import SimpleNamespace
from urllib.parse import parse_qs, urlsplit

import pytest

from test_w301_estate_index_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from sqlalchemy import text
    from test_w202_cold_replay_postgres import chain  # noqa: F401 - the W2-02 cold replay fixture
    from test_w205b_ev_replay_postgres import chain as ev_chain  # noqa: F401 - the W2-05b EV replay fixture
    from test_w301_estate_index_ev_postgres import settled
    from test_w301_estate_index_postgres import DAY, add_empty_site, cold_estate, db_now, iso, watermark
    from test_w302_evidence_scope_snapshot_postgres import Evidence
    from assetops_backend.analytics.cold_site_reads import ColdSiteReadService
    from assetops_backend.analytics.composition import build_cold_read_service
    from assetops_backend.cold_site_api import build_cold_site_router
    from assetops_backend.ev_site_api import build_ev_site_router
    from assetops_backend.financials.composition import build_cold_consequence_store, build_ev_site_read_service

CURRENT_VIEW = "Opens current Site view"


def at(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def site_client(built, site_type: str, router_for) -> TestClient:
    """The W2 Site router over the real read services, with the replay Site as the only imported Site."""
    with built.engine.connect() as c:
        code, kind = c.execute(text("SELECT site_code, site_type FROM site WHERE id = :s"),
                               {"s": built.site_id}).one()
    assert kind == site_type
    site = SimpleNamespace(id=built.site_id, site_type=kind)
    registry = SimpleNamespace(imported=lambda wanted: site if wanted == code else None,
                               tenant=lambda: SimpleNamespace(id=built.tenant_id))
    app = FastAPI()
    app.include_router(router_for(registry))
    return TestClient(app)


def follow(c: TestClient, row: dict, page_suffix: str, api_suffix: str) -> tuple[dict, dict]:
    """Follow the row's generated Site page link into the matching Site API with exactly its query; assert a
    successful (non-422) read."""
    link = urlsplit(row["links"]["site_readiness"])
    assert row["links"]["site_readiness_label"] is None and link.path.endswith(page_suffix), row["links"]
    response = c.get(f"/api{link.path.removesuffix(page_suffix)}{api_suffix}?{link.query}")
    assert response.status_code == 200, (row["links"], response.status_code, response.text[:400])
    return {k: at(v[0]) for k, v in parse_qs(link.query).items()}, response.json()


def row_window(row: dict) -> tuple[datetime, datetime]:
    return at(row["window_start"]), at(row["window_end"])


def test_w302_evidence_cold_link_follows_selected_window_and_cutoff(chain) -> None:  # noqa: F811
    built, _estate = cold_estate(chain)
    body = Evidence(built.engine, built.tenant_id).ok(**{"from": iso(DAY), "to": iso(DAY + timedelta(days=1))},
                                                      limit=100)
    selected = [r for r in body["rows"] if r["domain"] == "cold_chain" and r["window_start"] is not None]
    assert selected, [(r["capability_key"], r["raw_state"]) for r in body["rows"]]
    mark = watermark(built.engine, built.site_id)
    reads = ColdSiteReadService(build_cold_read_service(URL), build_cold_consequence_store(URL))
    c = site_client(built, "COLDCHAIN", lambda registry: build_cold_site_router(registry, reads))
    for row in selected:
        q, read = follow(c, row, "/evidence", "/cold/evidence")
        assert (q["from"], q["to"]) == row_window(row)  # the row's exact window, never the estate day
        assert q["known_at"] == mark <= at(body["window"]["known_at"]) + timedelta(seconds=1)
        assert read, "the Site read returned an empty body for the selected window"
    # A Site read of the estate day bounds is a different request than the row link (the link is row-local).
    assert all(row_window(r) != (DAY, DAY + timedelta(days=1)) for r in selected)


def test_w302_evidence_ev_link_follows_selected_window_and_cutoff(ev_chain) -> None:  # noqa: F811
    built, _estate, day = settled(ev_chain, "complete")
    body = Evidence(built.engine, built.tenant_id).ok(**{"from": iso(day), "to": iso(day + timedelta(days=1))},
                                                      limit=100)
    selected = [r for r in body["rows"] if r["domain"] == "ev_charging" and r["window_start"] is not None]
    assert selected, [(r["capability_key"], r["raw_state"]) for r in body["rows"]]
    mark = watermark(built.engine, built.site_id)
    reads = build_ev_site_read_service(URL)
    c = site_client(built, "EV_CHARGING", lambda registry: build_ev_site_router(registry, reads))
    try:
        for row in selected:
            q, read = follow(c, row, "/ev/evidence", "/ev/evidence")
            assert (q["from"], q["to"]) == row_window(row)
            assert q["known_at"] == mark <= at(body["window"]["known_at"]) + timedelta(seconds=1)
            assert read, "the Site read returned an empty body for the selected window"
    finally:
        reads.dispose()


def test_w302_evidence_link_falls_back_without_provable_cutoff(chain) -> None:  # noqa: F811
    """A Site with no committed evidence cutoff has no provable row-local cutoff: its rows keep the base Site route
    and `Opens current Site view`, never a windowed Site link."""
    built, _estate = cold_estate(chain)
    empty = add_empty_site(built.engine, built.site_id, "W302-EMPTY-001")
    assert db_now(built.engine) is not None
    body = Evidence(built.engine, built.tenant_id).ok(**{"from": iso(DAY), "to": iso(DAY + timedelta(days=1))},
                                                      limit=100)
    fallback = [r for r in body["rows"] if r["site_id"] == empty]
    assert len(fallback) == 4
    for row in fallback:
        assert row["links"] == {"site": "/sites/W302-EMPTY-001", "site_readiness": "/sites/W302-EMPTY-001",
                                "site_readiness_label": CURRENT_VIEW}
        assert row["window_start"] is None and "?" not in row["links"]["site_readiness"]
    # The provable rows of the same read keep their windowed link, so the fallback is per row, not per page.
    assert any(r["links"]["site_readiness_label"] is None for r in body["rows"] if r["site_id"] != empty)
