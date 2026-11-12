"""PR-2a (BL-68): the Site price page read over stored price history (PostgreSQL).

The S4-02a fixture history (v1 INITIAL, v2 future SUCCESSION, v3 CORRECTION) reads as one diesel row with three
History versions in plain words, newest first; `known_at` before v3 reads the history as it was then; a revision
recorded by the PR-3 entry actor reads "Entered by site admin"; a Site without a productive price reads "Not set".
"""

from __future__ import annotations

import os
from datetime import timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from test_s1_bindings_postgres import engine, imported, store  # noqa: F401
    from test_s4_assumptions_postgres import _t, run_fixture

    from assetops_backend.financials.adapters.postgres_assumption_store import (
        AssumptionStoreUnavailable,
        PostgresAssumptionStore,
    )
    from assetops_backend.financials.assumption_read import AssumptionReadService
    from assetops_backend.financials.assumptions import Publication, SystemPrincipal
    from assetops_backend.price_page_api import build_price_page_router, registry_site_facts

PAGE = "/api/sites/KOBO-001/prices"


class Registry:
    def __init__(self, site) -> None:
        self.site = site

    def imported(self, code: str):
        return self.site if code == self.site.site_code else None


@pytest.fixture()
def page(store, capsys):  # noqa: F811
    result = imported(store)
    prices = PostgresAssumptionStore(URL)
    out = run_fixture(prices, capsys)
    app = FastAPI()
    app.include_router(build_price_page_router(AssumptionReadService(prices), registry_site_facts(Registry(result.site)),
                                               (AssumptionStoreUnavailable,)))
    yield TestClient(app), prices, result, out
    prices.dispose()


def body(client, **params) -> dict:
    response = client.get(PAGE, params=params)
    assert response.status_code == 200, response.text
    return response.json()


def test_fixture_history_reads_as_one_row_with_plain_word_history(page) -> None:
    client, _, result, out = page
    b = body(client)
    assert b["site_code"] == "KOBO-001" and b["title"].endswith(" · Prices")
    assert b["prices"][0]["key"] == "diesel_price_per_litre"
    diesel = b["prices"][0]
    assert diesel["state"] == "SET"
    kinds = [h["change_kind"] for h in diesel["history"]]
    assert kinds == ["CORRECTION", "SUCCESSION", "INITIAL"]
    assert [h["revision_no"] for h in diesel["history"]] == [3, 2, 1]
    assert diesel["history"][0]["headline"].startswith("Correction from ")
    assert diesel["history"][0]["reason"]
    assert diesel["history"][1]["headline"].startswith("New price from ")
    assert diesel["history"][2]["headline"].startswith("First price from ")
    assert {h["set_by_label"] for h in diesel["history"]} == {"AssetOps administrator"}
    assert diesel["history_title"] == "History of the diesel price · 3 versions"
    # The current value is the open-ended assignment of the stored timeline, never a "today" pick.
    assert diesel["current"]["revision_id"] in {str(o["revision_id"]) for o in out}
    assert diesel["current"]["applies_until_text"] is None
    assert diesel["current"]["value_text"].endswith(" per litre")
    productive = next(p for p in b["prices"] if p["key"] == "productive_use_price_per_kwh")
    assert (productive["state"], productive["not_set_text"], productive["note"]) == ("NOT_SET", "Not set", None)


def test_known_at_reads_the_history_as_recorded_then(page) -> None:
    client, prices, result, _ = page
    # The cutoff comes from the stored rows: one second before the correction (v3) was recorded.
    snap = prices.snapshot(result.tenant.id, result.site.id, "diesel_price_per_litre", None, 0, 10)
    v3_recorded = max(r["recorded_at"] for r in snap["revisions"])
    before = body(client, known_at=(v3_recorded - timedelta(seconds=1)).isoformat())
    diesel = before["prices"][0]
    assert [h["revision_no"] for h in diesel["history"]] == [2, 1]
    assert before["cutoff"]["text"].startswith("Prices as known at ")
    assert [h["revision_no"] for h in body(client)["prices"][0]["history"]] == [3, 2, 1]


def test_a_revision_by_the_entry_actor_reads_entered_by_site_admin(page) -> None:
    client, prices, result, _ = page
    entry = SystemPrincipal(actor_id="service:operator-entry", authorization_basis="PR-2a test: the PR-3 entry actor")
    prices.publish(result.tenant.id, result.site.id, Publication(
        assumption_key="productive_use_price_per_kwh", currency="USD", value=Decimal("0.21"),
        basis="AUTHORED_ESTIMATE", source_reference="test source", valid_from=_t(2026, 1), valid_to=None,
        change_kind="INITIAL", correction_reason=None, expected_prior_revision_id=None,
        idempotency_key="pr2a-entry-actor", channel="SYSTEM_CLI", provenance={"service": "test"}), entry)
    productive = next(p for p in body(client)["prices"] if p["key"] == "productive_use_price_per_kwh")
    assert productive["state"] == "SET"
    assert productive["current"]["value_text"] == "0.21 USD per kWh"
    assert productive["current"]["set_by_label"] == "Entered by site admin"
    assert productive["history"][0]["headline"].startswith("First price from ")


def test_unknown_site_is_404_and_dates_are_site_local(page) -> None:
    client, prices, result, _ = page
    assert client.get("/api/sites/NOPE-001/prices").status_code == 404
    diesel = body(client)["prices"][0]
    snap = prices.snapshot(result.tenant.id, result.site.id, "diesel_price_per_litre", None, 0, 10)
    first = min(snap["revisions"], key=lambda r: r["revision_no"])
    local = first["valid_from"].astimezone(ZoneInfo(result.site.timezone))
    assert diesel["history"][-1]["headline"] == f"First price from {local.day} {local:%b %Y}"
