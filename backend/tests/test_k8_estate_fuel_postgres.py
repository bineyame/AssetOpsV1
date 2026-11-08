"""DIESEL-K8 (`.agent/build-sheet-DIESEL-1.md` §9p.12, ruling DIESEL-1-R3p): the unexplained-fuel Finding in the estate
Finding rows over real Postgres, and never in the estate money.

Reuses `test_k4a_fuel_finding_postgres`'s `kobo` fixture (Kobo imported, the fuel Finding service on a virtual clock)
by import. TEST-SCOPED (K8 coordinator ruling on handoff 2's caveat, option (i)):
- the `kobo` Site has no settled mini selection for January 2027, so the estate Finding coverage of that one Site
  is forced to CURRENT by wrapping `estate.index.site_coverage`; the money scope's own `site_coverage`
  (`estate/evidence_money.py`) is never wrapped and stays real;
- the estate snapshot's read time is pinned to 2027-01-20 (after the virtual clock), or the cutoff hides the Finding.
A second read with the real coverage proves the coverage gate (`index.py` `select_finding_scope`) by itself.
Requires ASSETOPS_TEST_DATABASE_URL naming a `*_test` database.
"""

from __future__ import annotations

import os
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

UTC = timezone.utc
READ_AT = datetime(2027, 1, 20, tzinfo=UTC)

if URL:
    from sqlalchemy import event
    from sqlalchemy.pool import Pool

    from test_k4a_fuel_finding_postgres import PRICED_NIGHT, kobo  # noqa: F401 - the K4a fixture
    from test_s1_bindings_postgres import engine, store  # noqa: F401
    from test_s4_assumptions_postgres import run_fixture
    from test_w301_estate_index_postgres import pin_read_at

    from assetops_backend.estate import index
    from assetops_backend.estate.composition import build_estate_index_service, build_estate_portfolio_service
    from assetops_backend.estate.coverage import CURRENT, MINI_GRID
    from assetops_backend.estate.scope import estate_request
    from assetops_backend.financials.adapters.postgres_assumption_store import PostgresAssumptionStore


def _priced_fuel_finding(kobo, capsys):  # noqa: F811
    prices = PostgresAssumptionStore(URL)
    try:
        run_fixture(prices, capsys, "v1")
    finally:
        prices.dispose()
    kobo.put(PRICED_NIGHT, "UNEXPLAINED", "33", "46.2")
    opened = kobo.raise_(PRICED_NIGHT)
    assert opened.status == "OPENED"
    (money,) = kobo.consequences(opened.finding_id)
    assert money.state == "PRICED"
    return opened, money


def _force_current(monkeypatch, site_id) -> None:
    real = index.site_coverage

    def forced(snap, tenant_id, sid, domain, from_, to, k):
        cov = real(snap, tenant_id, sid, domain, from_, to, k)
        return {**cov, "state": CURRENT} if domain == MINI_GRID and str(sid) == str(site_id) else cov
    monkeypatch.setattr(index, "site_coverage", forced)


def _request():
    start = datetime.combine(PRICED_NIGHT, datetime.min.time(), UTC)
    return replace(estate_request("findings", start, start + timedelta(days=2)), lens="all", state_filter="all")


def _fuel(body: dict, fid: str) -> list[dict]:
    return [r for r in body["rows"] if r["finding_id"] == fid]


def _ids(value) -> set[str]:
    """Every string anywhere inside a JSON-like value."""
    if isinstance(value, dict):
        return set().union(*(_ids(v) for v in value.values())) if value else set()
    if isinstance(value, (list, tuple)):
        return set().union(*(_ids(v) for v in value)) if value else set()
    return {value} if isinstance(value, str) else set()


def test_k8_fuel_row_in_estate_findings_never_in_money(kobo, capsys, monkeypatch) -> None:  # noqa: F811
    opened, money = _priced_fuel_finding(kobo, capsys)
    fid, frid = str(opened.finding_id), str(opened.revision_id)
    pin_read_at(monkeypatch, lambda: READ_AT)
    admit = lambda code: True  # noqa: E731
    svc = build_estate_index_service(URL)
    portfolio_svc = build_estate_portfolio_service(URL)
    try:
        # The gate on real coverage: this Site's mini coverage is not CURRENT/HISTORICAL/PARTIAL, so no fuel row.
        real_body = svc.findings(kobo.t, _request(), admit)
        assert _fuel(real_body, fid) == []

        _force_current(monkeypatch, kobo.s)
        checkouts: list[int] = []
        counter = lambda *a: checkouts.append(1)  # noqa: E731
        event.listen(Pool, "checkout", counter)
        try:
            body = svc.findings(kobo.t, _request(), admit)
        finally:
            event.remove(Pool, "checkout", counter)
        assert len(checkouts) == 1, checkouts          # one estate read, one connection (the join adds none)
        (row,) = _fuel(body, fid)
        assert row["finding_revision_id"] == frid and row["lens_flags"] == ["RISK"]
        assert row["title"] == "Unexplained fuel overnight" and row["status"] == CURRENT
        code = row["site_code"]
        assert row["links"]["finding"] == f"/sites/{code}/fuel-findings/{fid}"
        assert row["link_refs"]["finding"]["kind"] == "FUEL_FINDING"
        c = row["consequence"]
        assert (c["state"], c["amount_low"], c["amount_high"], c["currency"], c["source_revision_id"]) == (
            "PRICED", "41.25", "57.75", "USD", str(money.id))
        assert c["basis"] == "UNEXPLAINED_FUEL_AT_DECLARED_PRICE"
        # The provenance is the snapshot's real read of the revision's stored citations. K4a's synthetic windows cite
        # no evidence, so it is honestly UNKNOWN (EMPTY_CITATION_SET) here; the evidence-backed state is shown on the
        # Kisiwa clone (review packet K8, clone evidence).
        provenance = row["source_provenance"]
        print("K8 fuel row source_provenance:", provenance)
        assert provenance["evidence_ids"] == [] and provenance["state"] == "UNKNOWN"
        assert [r["code"] for r in provenance["reasons"]] == ["EMPTY_CITATION_SET"]

        # Money: the Portfolio over the same forced Finding coverage; its money scope reads real coverage.
        p = portfolio_svc.portfolio(kobo.t, _request(), admit)
        assert any(r.get("finding_id") == fid for r in p["rows"])          # the row reaches the Portfolio list
        money_ids = _ids(p["money"]["groups"]) | _ids(p["selected_lines"])
        assert fid not in money_ids and frid not in money_ids and str(money.id) not in money_ids
        print("K8 portfolio money groups", len(p["money"]["groups"]), "selected_lines", len(p["selected_lines"]))
    finally:
        svc.store.dispose()
        portfolio_svc.store.dispose()
