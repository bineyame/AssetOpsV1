"""S4-02a phase 2: Site price reads over the stored fixture history (PostgreSQL).

Packet item 3: half-open valid boundary `t`, recorded cutoff `recorded_from <= c < recorded_to`, exact ID
stable after later writes, foreign Site/revision 404 (never latest), bounded pagination, NO_PRICE.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from test_s1_bindings_postgres import engine, imported, store  # noqa: F401
    from test_s4_assumptions_postgres import V2_START, _t, run_fixture

    from assetops_backend.financial_read_api import build_financial_read_router
    from assetops_backend.financials.adapters.postgres_assumption_store import (
        AssumptionStoreUnavailable,
        PostgresAssumptionStore,
    )
    from assetops_backend.financials.assumption_read import AssumptionReadService
    from assetops_backend.financials.assumptions import SYSTEM_PUBLISHER, Publication

SERIES = "/api/sites/KOBO-001/financial-assumptions"


@pytest.fixture()
def published(store, capsys):  # noqa: F811
    result = imported(store)
    prices = PostgresAssumptionStore(URL)
    out = run_fixture(prices, capsys)
    scope = {"KOBO-001": ("KOBO-001", result.tenant.id, result.site.id),
             "OTHER-001": ("OTHER-001", result.tenant.id, uuid4()),
             "FOREIGN-001": ("FOREIGN-001", uuid4(), result.site.id)}
    app = FastAPI()
    app.include_router(build_financial_read_router(AssumptionReadService(prices), scope.get,
                                                   (AssumptionStoreUnavailable,)))
    yield TestClient(app), prices, (result.tenant.id, result.site.id), [o["revision_id"] for o in out]
    prices.dispose()


def at(client, valid_at: datetime, recorded_at: datetime | None = None) -> dict:
    params = {"valid_at": valid_at.isoformat()}
    if recorded_at is not None:
        params["recorded_at"] = recorded_at.isoformat()
    response = client.get(SERIES, params=params)
    assert response.status_code == 200, response.text
    return response.json()


def recorded(client) -> list[datetime]:
    return [datetime.fromisoformat(r["recorded_at"]) for r in client.get(SERIES).json()["revisions"]]


class TestSelection:
    def test_half_open_valid_boundaries_on_the_current_series(self, published) -> None:
        client, _, _, (v1, v2, v3) = published
        for valid_at, expected in ((_t(2026, 5, 31), v1), (_t(2026, 6), v3), (_t(2026, 7), v1),
                                   (V2_START - timedelta(microseconds=1), v1), (V2_START, v2)):
            selection = at(client, valid_at)["selection"]
            assert (selection["state"], selection["revision_id"]) == ("PRICED", expected), valid_at
        before = at(client, _t(2025, 12, 31))["selection"]
        assert (before["state"], before["revision_id"]) == ("NO_PRICE", None)
        june = at(client, _t(2026, 6, 15))["selection"]
        assert (june["price"]["value"], june["price"]["currency"], june["price"]["unit"]) == \
            ("1.19", "USD", "currency/L")
        assert june["price"]["actor"] == {"kind": "SYSTEM", "id": SYSTEM_PUBLISHER.actor_id, "author_id": None}

    def test_recorded_cutoffs_select_what_was_stored_then(self, published) -> None:
        client, _, _, (v1, v2, v3) = published
        r1, r2, r3 = recorded(client)
        assert at(client, _t(2026, 6, 15), r1)["selection"]["revision_id"] == v1
        assert at(client, _t(2026, 6, 15), r3 - timedelta(microseconds=1))["selection"]["revision_id"] == v1
        assert at(client, _t(2026, 6, 15), r3)["selection"]["revision_id"] == v3
        assert at(client, V2_START, r1)["selection"]["revision_id"] == v1
        assert at(client, V2_START, r2)["selection"]["revision_id"] == v2
        empty = at(client, _t(2026, 6, 15), r1 - timedelta(microseconds=1))
        assert empty["state"] == "NO_PRICE" and empty["timeline"] == [] and empty["revisions"] == []
        assert empty["selection"]["state"] == "NO_PRICE"
        cut = at(client, _t(2026, 6, 15), r2)
        assert [r["revision_id"] for r in cut["revisions"]] == [v1, v2]
        assert [a["revision_id"] for a in cut["timeline"]] == [v1, v2]
        assert datetime.fromisoformat(cut["timeline"][0]["valid"]["to"]) == V2_START  # v1 truncated at v2
        current = client.get(SERIES).json()
        assert [a["revision_id"] for a in current["timeline"]] == [v1, v3, v1, v2]
        assert current["cutoff"]["selected_by"] == "CURRENT" and cut["cutoff"]["selected_by"] == "RECORDED_CUTOFF"

    def test_pagination_is_bounded_and_complete(self, published) -> None:
        client, _, _, ids = published
        seen, after = [], 0
        while after is not None:
            body = client.get(SERIES, params={"after_revision_no": after, "limit": 1}).json()
            assert len(body["revisions"]) <= 1 and body["revision_page"]["total"] == 3
            seen += [r["revision_id"] for r in body["revisions"]]
            after = body["revision_page"]["next_after_revision_no"]
            assert (after is None) == ("api_next_page" not in body["links"])
        assert seen == ids


class TestExactRevision:
    def test_an_exact_id_is_stable_after_later_writes(self, published) -> None:
        client, prices, site, (v1, v2, v3) = published
        r3 = recorded(client)[2]
        before = client.get(f"{SERIES}/{v1}").json()
        pinned_view = at(client, _t(2026, 8, 15), r3)
        prices.publish(*site, Publication(
            assumption_key="diesel_price_per_litre", currency="USD", value=Decimal("1.21"), basis="AUTHORED_ESTIMATE",
            source_reference="later correction", valid_from=_t(2026, 8), valid_to=_t(2026, 9),
            change_kind="CORRECTION", correction_reason="test", expected_prior_revision_id=UUID(v3),
            idempotency_key="later", channel="SYSTEM_CLI", provenance={"service": "test"}), SYSTEM_PUBLISHER)
        after = client.get(f"{SERIES}/{v1}").json()
        assert after["revision"] == before["revision"] and after["selection"]["selected_by"] == "EXACT_REVISION_ID"
        assert after["revision"]["value"] == "1.25"
        # Earlier assignment rows of v1 are kept; the August row is now closed, not rewritten.
        assert len(after["assignments"]) == len(before["assignments"]) + 2
        assert {a["assignment_id"] for a in before["assignments"]} <= {a["assignment_id"] for a in after["assignments"]}
        # A pinned cutoff reloads identically after the later write; the current read moves.
        # (Only the superseded row's recorded end is new knowledge; the selected IDs and prices are unchanged.)
        again = at(client, _t(2026, 8, 15), r3)
        assert again["selection"]["revision_id"] == pinned_view["selection"]["revision_id"] == v1
        assert again["selection"]["assignment_id"] == pinned_view["selection"]["assignment_id"]
        assert again["selection"]["price"] == pinned_view["selection"]["price"]
        assert [(a["assignment_id"], a["valid"]) for a in again["timeline"]] == \
            [(a["assignment_id"], a["valid"]) for a in pinned_view["timeline"]]
        assert pinned_view["selection"]["recorded"]["to"] is None and again["selection"]["recorded"]["to"] is not None
        assert at(client, _t(2026, 8, 15))["selection"]["revision_id"] not in (v1, v2, v3)

    def test_foreign_site_or_tenant_revision_is_404_never_latest(self, published) -> None:
        client, _, _, (v1, _, _) = published
        for site in ("OTHER-001", "FOREIGN-001"):
            response = client.get(f"/api/sites/{site}/financial-assumptions/{v1}")
            assert response.status_code == 404, site
            assert response.json()["detail"]["code"] == "ASSUMPTION_REVISION_NOT_FOUND"
            assert client.get(f"/api/sites/{site}/financial-assumptions").json()["state"] == "NO_PRICE"
        assert client.get(f"{SERIES}/{uuid4()}").status_code == 404
