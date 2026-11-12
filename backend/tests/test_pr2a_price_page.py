"""PR-2a (BL-68): the read-only Site price page read, no database.

Route matrix (401/403/404/422/503), the per-Site-type rows (stored keys first, future keys "Not set" with the
default-3 sentence), the current value without a clock, History words, the Set-by map (both actors, rev 5 §5.3),
`known_at` as the recorded cutoff, and the Part C need block. The stored selection itself is proved against
PostgreSQL in `test_pr2a_price_page_postgres.py`.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from assetops_backend.financials.assumption_read import AssumptionReadService
from assetops_backend.financials.price_page import (
    FUTURE_KEY_NOTE, SET_BY_LABEL, SIGN_IN_TEXT, SITE_KEYS, amount_text, compose)
from assetops_backend.outcomes.price_action import NEED_TEXT, PRICE_NOUN, STORED_KEYS
from assetops_backend.price_page_api import build_price_page_router

TENANT, SITE, EV_SITE = uuid4(), uuid4(), uuid4()
FACTS = {
    "KOBO-001": ("KOBO-001", "Kobo", "MINIGRID", "Africa/Nairobi", TENANT, SITE),
    "DEPOT-001": ("DEPOT-001", "Depot", "EV_CHARGING", "UTC", TENANT, EV_SITE),
    "GH-001": ("GH-001", "GreenHarvest", "COLDCHAIN", "UTC", TENANT, uuid4()),
}
PAGE = "/api/sites/KOBO-001/prices"


def utc(*args: int) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


def revision(no: int, kind: str, value: str, valid_from: datetime, recorded: datetime, *, basis="AUTHORED_ESTIMATE",
             reason=None, actor="service:assetops-assumption-publisher", key="diesel_price_per_litre"):
    return {"id": uuid4(), "revision_no": no, "prior_revision_id": None, "assumption_key": key,
            "value": Decimal(value), "currency": "USD", "unit": "currency/L" if key.startswith("diesel") else
            "currency/kWh", "basis": basis, "source_reference": "SC-88" if basis == "CONTRACT_RATE" else None,
            "valid_from": valid_from, "valid_to": None, "recorded_at": recorded, "change_kind": kind,
            "correction_reason": reason, "actor_kind": "SYSTEM", "actor_id": actor, "author_id": None,
            "channel": "SYSTEM_CLI", "authorization_basis": "x", "provenance": {}, "idempotency_key": "k",
            "request_sha256": "0" * 64}


def assignment(rev, valid_from, valid_to=None):
    return {"id": uuid4(), "revision_id": rev["id"], "publication_revision_id": rev["id"], "valid_from": valid_from,
            "valid_to": valid_to, "recorded_from": rev["recorded_at"], "recorded_to": None}


# Diesel: first price 1 Aug, a new price from 1 Sep, then a correction from 1 Sep that replaces it (mock Part B).
FIRST = revision(1, "INITIAL", "1.3800", utc(2026, 7, 31, 21), utc(2026, 8, 1, 7, 30))
NEW = revision(2, "SUCCESSION", "1.40", utc(2026, 8, 31, 21), utc(2026, 8, 28, 13, 2))
FIX = revision(3, "CORRECTION", "1.4200", utc(2026, 8, 31, 21), utc(2026, 9, 2, 6, 14), basis="CONTRACT_RATE",
               reason="supplier contract rate replaces the estimate", actor="service:operator-entry")
DIESEL = {"total": 3, "revisions": [FIRST, NEW, FIX],
          "timeline": [assignment(FIRST, FIRST["valid_from"], FIX["valid_from"]), assignment(FIX, FIX["valid_from"])],
          "cited": {FIRST["id"]: FIRST, FIX["id"]: FIX, NEW["id"]: NEW}}
EMPTY = {"total": 0, "revisions": [], "timeline": [], "cited": {}}


class Down(RuntimeError):
    pass


class Rows:
    def __init__(self, series=None, error=None) -> None:
        self.series, self.error, self.calls = series or {}, error, []

    def snapshot(self, tenant_id, site_id, key, recorded_at, after_revision_no, limit):
        self.calls.append((key, recorded_at))
        if self.error:
            raise self.error
        return self.series.get(key, EMPTY)

    def revision_detail(self, tenant_id, site_id, revision_id):
        return None


def client(rows=None, access=None, reads=True) -> TestClient:
    app = FastAPI()
    kwargs = {} if access is None else {"access": access}
    service = AssumptionReadService(rows if rows is not None else Rows()) if reads else None
    app.include_router(build_price_page_router(service, FACTS.get, (Down,), **kwargs))
    return TestClient(app)


class TestRouteMatrix:
    def test_401_and_403_come_before_any_read(self) -> None:
        rows = Rows()
        assert client(rows, access=lambda r, s: 401).get(PAGE).status_code == 401
        refused = client(rows, access=lambda r, s: 403).get(PAGE)
        assert (refused.status_code, refused.json()["detail"]["code"]) == (403, "SITE_SCOPE_FORBIDDEN")
        assert rows.calls == []

    def test_unknown_site_is_404(self) -> None:
        assert client().get("/api/sites/NOPE-001/prices").status_code == 404

    def test_naive_known_at_is_422(self) -> None:
        response = client().get(PAGE, params={"known_at": "2026-10-01T00:00:00"})
        assert (response.status_code, response.json()["detail"]["code"]) == (422, "INSTANT_NOT_ZONED")

    def test_missing_or_failing_store_is_typed_503(self) -> None:
        for c in (client(reads=False), client(Rows(error=Down("db gone")))):
            response = c.get(PAGE)
            assert (response.status_code, response.json()["detail"]["code"]) == (503, "ASSUMPTION_STORE_UNAVAILABLE")

    def test_reads_only_the_stored_keys_of_the_site_type_at_the_cutoff(self) -> None:
        rows = Rows()
        client(rows).get(PAGE, params={"known_at": "2026-10-01T00:00:00+00:00"})
        assert rows.calls == [("diesel_price_per_litre", utc(2026, 10, 1)),
                              ("productive_use_price_per_kwh", utc(2026, 10, 1))]
        rows = Rows()
        client(rows).get("/api/sites/GH-001/prices")
        assert rows.calls == []  # a cold Site has no stored key yet: its rows are all future keys


class TestRows:
    def test_minigrid_rows_in_order_with_future_keys_not_set(self) -> None:
        body = client(Rows({"diesel_price_per_litre": DIESEL})).get(PAGE).json()
        assert [p["key"] for p in body["prices"]] == list(SITE_KEYS["MINIGRID"])
        assert body["count_text"] == "4 prices · 1 set" and body["sign_in_text"] == SIGN_IN_TEXT
        assert body["title"] == "Kobo · Prices" and body["table_title"] == "All prices for Kobo"
        by = {p["key"]: p for p in body["prices"]}
        productive = by["productive_use_price_per_kwh"]
        assert (productive["state"], productive["stored"], productive["note"]) == ("NOT_SET", True, None)
        for key in ("repair_visit_cost", "planned_service_cost"):
            row = by[key]
            assert (row["state"], row["stored"], row["not_set_text"], row["note"]) == (
                "NOT_SET", False, "Not set", FUTURE_KEY_NOTE)
            assert row["current"] is None and row["history"] == []

    def test_every_listed_key_has_words_and_future_keys_are_price_action_keys(self) -> None:
        for keys in SITE_KEYS.values():
            for key in keys:
                assert key in STORED_KEYS or key in PRICE_NOUN or key == "stock_value_at_risk", key

    def test_current_is_the_open_ended_assignment_without_a_clock(self) -> None:
        diesel = client(Rows({"diesel_price_per_litre": DIESEL})).get(PAGE).json()["prices"][0]
        current = diesel["current"]
        assert diesel["state"] == "SET" and current["revision_id"] == str(FIX["id"])
        assert current["value_text"] == "1.42 USD per litre" and current["value"] == "1.4200"
        assert current["basis_text"] == "A contract rate" and current["source_reference"] == "SC-88"
        # Site-local dates (Africa/Nairobi, UTC+3): 31 Aug 21:00 UTC is 1 Sep local.
        assert current["applies_from_text"] == "1 Sep 2026" and current["applies_until_text"] is None
        assert current["set_by_label"] == "Entered by site admin"
        assert current["recorded_text"] == "recorded 2 Sep 2026, 09:14"

    def test_history_newest_first_in_plain_words(self) -> None:
        diesel = client(Rows({"diesel_price_per_litre": DIESEL})).get(PAGE).json()["prices"][0]
        assert diesel["history_title"] == "History of the diesel price · 3 versions"
        h = diesel["history"]
        assert [x["headline"] for x in h] == ["Correction from 1 Sep 2026", "New price from 1 Sep 2026",
                                             "First price from 1 Aug 2026"]
        assert h[0]["reason"] == "supplier contract rate replaces the estimate"
        assert [x["value_text"] for x in h] == ["1.42 USD per litre", "1.40 USD per litre", "1.38 USD per litre"]
        assert [x["set_by_label"] for x in h] == ["Entered by site admin", "AssetOps administrator",
                                                 "AssetOps administrator"]
        assert [x["replaced"] for x in h] == [False, True, False]
        assert h[1]["replaced_text"] == "replaced by a later correction" and h[0]["replaced_text"] is None

    def test_set_by_map_has_both_actors_and_an_unknown_actor_is_not_guessed(self) -> None:
        assert SET_BY_LABEL == {"service:assetops-assumption-publisher": "AssetOps administrator",
                                "service:operator-entry": "Entered by site admin"}
        stray = revision(1, "INITIAL", "1", utc(2026, 1, 1), utc(2026, 1, 1), actor="service:other")
        series = {"total": 1, "revisions": [stray], "timeline": [assignment(stray, stray["valid_from"])],
                  "cited": {stray["id"]: stray}}
        row = client(Rows({"diesel_price_per_litre": series})).get(PAGE).json()["prices"][0]
        assert row["current"]["set_by_label"] == "Recorded by the server"

    def test_ev_and_cold_rows(self) -> None:
        ev = client().get("/api/sites/DEPOT-001/prices").json()
        assert [p["key"] for p in ev["prices"]][0] == "ev_gross_tariff_per_kwh"
        cold = client().get("/api/sites/GH-001/prices").json()
        assert [p["label"] for p in cold["prices"]] == ["Cost per visit", "Planned service cost",
                                                       "Stock value at risk"]
        assert all(p["note"] == FUTURE_KEY_NOTE for p in cold["prices"])

    def test_known_at_text_and_need_block(self) -> None:
        body = client().get(PAGE, params={"known_at": "2026-10-01T00:00:00+00:00",
                                          "need": "battery_wear_model"}).json()
        assert body["cutoff"]["text"] == "Prices as known at 1 Oct 2026, 03:00."
        assert body["need"]["title"] == "What is needed to price this"
        assert body["need"]["text"] == NEED_TEXT["battery_wear_model"]
        assert client().get(PAGE, params={"need": "nonsense"}).json()["need"] is None
        assert client().get(PAGE).json()["cutoff"] == {"known_at": None, "text": None}

    def test_no_amount_in_any_future_or_need_word(self) -> None:
        body = compose(site_code="GH-001", site_name="GH", site_type="COLDCHAIN", timezone="UTC", series={},
                       need="stock_record", known_at=None, access_basis="x")
        words = " ".join(str(p[k]) for p in body["prices"] for k in ("note", "not_set_text", "label"))
        assert not any(ch.isdigit() for ch in words)


def test_amount_text_keeps_two_places_and_whole_numbers() -> None:
    assert [amount_text(v) for v in ("1.4200", "1.40", "0.2100", "120", "120.00", "1.23456")] == [
        "1.42", "1.40", "0.21", "120", "120.00", "1.23456"]
