"""PR-3 (D-PRICE.1): the site-admin price entry route, no database.

Design: `.agent/architect-sequence-client-scope-2026-11-11.md` revision 5 §5.3. The store is a fake with the
`PostgresAssumptionStore` read/publish shape; the stored rules (channel CHECK, outbox, recompute) are proved in
`test_pr3_price_entry_postgres.py`.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from assetops_backend.financial_api import build_financial_assumption_router
from assetops_backend.financials import assumptions as a
from assetops_backend.financials import price_entry as pe
from assetops_backend.financials.adapters.postgres_assumption_store import Published
from assetops_backend.outcomes import price_action
from assetops_backend.work.operational_entry import ENTRY_PRINCIPAL

TENANT, SITE = uuid4(), uuid4()
SCOPE = {"KOBO-001": ("KOBO-001", TENANT, SITE)}
URL = "/api/sites/KOBO-001/financial-assumptions/entries"
NOW = datetime(2026, 11, 12, 10, 0, tzinfo=timezone.utc)
NAIROBI = ZoneInfo("Africa/Nairobi")  # UTC+3, no daylight saving
KEY = "price-entry-" + "0" * 32
FAR_PAST = datetime(2025, 1, 1, tzinfo=timezone.utc)


class Down(RuntimeError):
    pass


def body(**over):
    b = {"key": "diesel_price_per_litre", "value": "1.45", "currency": "USD", "basis": "CONTRACT_RATE",
         "source": "Supplier contract SC-88", "applies_from": "2026-11-13", "reason": None, "dry_run": False,
         "idempotency_key": KEY}
    b.update(over)
    return {k: v for k, v in b.items() if v is not DROP}


DROP = object()


def revision(no: int, currency: str = "USD"):
    return {"id": uuid4(), "revision_no": no, "currency": currency}


def series(*assignments, currency: str = "USD"):
    """A current snapshot: each assignment is (valid_from, valid_to), cited by one revision per assignment."""
    revs = [revision(i + 1, currency) for i in range(len(assignments))]
    timeline = [{"id": uuid4(), "revision_id": r["id"], "publication_revision_id": r["id"], "valid_from": f,
                 "valid_to": t} for r, (f, t) in zip(revs, assignments)]
    return {"total": len(revs), "revisions": revs[:1], "timeline": timeline, "cited": {r["id"]: r for r in revs}}


EMPTY = {"total": 0, "revisions": [], "timeline": [], "cited": {}}


class Store:
    def __init__(self, snap=None, error=None, refuse=None, replayed=False):
        self.snap, self.error, self.refuse, self.replayed = snap or EMPTY, error, refuse, replayed
        self.published: list = []

    def snapshot(self, tenant_id, site_id, key, recorded_at, after_revision_no, limit):
        if self.error:
            raise self.error
        assert (tenant_id, site_id, recorded_at) == (TENANT, SITE, None)
        return self.snap

    def publish(self, tenant_id, site_id, p, principal):
        a.validate(p)  # the store's own validation runs first, as in the adapter
        if self.refuse:
            raise self.refuse
        self.published.append((tenant_id, site_id, p, principal))
        return Published(uuid4(), 4, NOW, p.change_kind, self.replayed)


def client(store=None, *, entry=True, access=None, zone=NAIROBI, scope=SCOPE.get, no_store=False,
           site_name=None):
    app = FastAPI()
    app.include_router(build_financial_assumption_router(
        scope, entry_principal=(lambda r, c: ENTRY_PRINCIPAL) if entry else (lambda r, c: None),
        store=None if no_store else (store or Store()), site_zone=lambda t, s: zone,
        read_access=access or (lambda r, c: None), unavailable=(Down,), site_name=site_name,
        clock=lambda: NOW))
    return TestClient(app)


def post(c, payload):
    raw = payload if isinstance(payload, (str, bytes)) else json.dumps(payload)
    return c.post(URL, content=raw, headers={"content-type": "application/json"})


def code(r):
    return r.json()["detail"]["code"]


class TestRefusalOrder:
    """Each step refuses with every later step also failing, so the order itself is pinned."""

    def test_1_unknown_site_404_before_access(self):
        r = post(client(entry=False, access=lambda r, c: 403, scope=lambda c: None), {"actor": "x"})
        assert r.status_code == 404

    def test_2_read_access_403(self):
        r = post(client(entry=False, access=lambda r, c: 403), "not json")
        assert (r.status_code, code(r)) == (403, "SITE_SCOPE_FORBIDDEN")

    def test_3_entry_off_403(self):
        r = post(client(entry=False, no_store=True), "not json")
        assert (r.status_code, code(r)) == (403, "PRICE_ENTRY_OFF")
        assert r.json()["detail"]["message"] == "Saving prices is switched off on this server."

    def test_4_body_not_json(self):
        r = post(client(no_store=True), "not json")
        assert (r.status_code, code(r)) == (422, "BODY_NOT_JSON")

    def test_5_client_actor_before_shape(self):
        r = post(client(no_store=True), {"actor_id": "user:me", "key": "nope"})
        assert (r.status_code, code(r)) == (422, "CLIENT_ACTOR_FORBIDDEN")
        assert r.json()["detail"]["fields"] == ["actor_id"]

    def test_6_shape_before_store(self):
        r = post(client(no_store=True), body(value="-1"))
        assert (r.status_code, code(r)) == (422, "PRICE_ENTRY_INVALID")
        assert r.json()["detail"]["fields"] == ["value"]

    def test_7_future_key_before_store(self):
        r = post(client(no_store=True), body(key="repair_visit_cost"))
        assert (r.status_code, code(r)) == (422, "PRICE_KEY_NOT_ENTERABLE")
        assert r.json()["detail"]["message"] == "No figure uses this price yet, so it cannot be saved here."

    def test_8_no_store_503(self):
        r = post(client(no_store=True), body(applies_from="1999-01-01"))
        assert (r.status_code, code(r)) == (503, "ASSUMPTION_STORE_UNAVAILABLE")

    def test_8_store_failure_503(self):
        r = post(client(Store(error=Down("down"))), body())
        assert (r.status_code, code(r)) == (503, "ASSUMPTION_STORE_UNAVAILABLE")

    def test_9_out_of_range_before_currency(self):
        store = Store(series((FAR_PAST, None), currency="KES"))
        r = post(client(store), body(applies_from="2024-01-01"))
        assert (r.status_code, code(r)) == (422, "APPLIES_FROM_OUT_OF_RANGE")

    def test_9_currency_before_reason(self):
        store = Store(series((FAR_PAST, None), currency="KES"))
        r = post(client(store), body(applies_from="2026-11-01"))
        assert (r.status_code, code(r)) == (422, "CURRENCY_DIFFERS")
        assert r.json()["detail"]["message"] == "This site's diesel price is kept in KES."
        assert store.published == []

    def test_9_reason_required(self):
        store = Store(series((FAR_PAST, None)))
        r = post(client(store), body(applies_from="2026-11-01"))
        assert (r.status_code, code(r)) == (422, "REASON_REQUIRED")
        assert r.json()["detail"]["message"] == "This date changes figures already shown. Say why."
        assert store.published == []

    def test_10_plan_refusal_passes_through(self):
        # A scheduled open price from +10 days; a SUCCESSION from +5 days may not shorten it (store rule, 409).
        store = Store(series((NOW + timedelta(days=10), None)))
        r = post(client(store), body(applies_from="2026-11-17"))
        assert (r.status_code, code(r)) == (409, "SUCCESSION_OVERLAP_NOT_PERMITTED")
        assert store.published == []

    def test_10_store_refusal_passes_through(self):
        store = Store(refuse=a.PublicationRefused(409, "IDEMPOTENCY_KEY_REUSED", "reused"))
        r = post(client(store), body())
        assert (r.status_code, r.json()["detail"]) == (409, {"code": "IDEMPOTENCY_KEY_REUSED", "message": "reused"})

    def test_bounds_are_inclusive(self):
        for day in ("2025-10-08", "2027-11-13"):  # today (12 Nov 2026, Nairobi) - 400 and + 366
            assert post(client(), body(applies_from=day)).status_code == 201, day
        for day in ("2025-10-07", "2027-11-14"):
            assert code(post(client(), body(applies_from=day))) == "APPLIES_FROM_OUT_OF_RANGE", day


class TestShape:
    @pytest.mark.parametrize("field,value", [
        ("key", "unknown_key"), ("key", 3),
        ("value", "0"), ("value", "1.23456"), ("value", "1234567"), ("value", 1.45), ("value", "1e3"), ("value", " 1"),
        ("currency", "usd"), ("currency", "XXX"), ("currency", None),
        ("basis", "SCENARIO"),
        ("source", ""), ("source", "   "), ("source", "x" * 121), ("source", "bad\x07char"), ("source", None),
        ("applies_from", "2026-11-31"), ("applies_from", "20261113"), ("applies_from", "2026-11-13T00:00"),
        ("reason", ""), ("reason", "x" * 201), ("reason", 5),
        ("dry_run", "yes"), ("dry_run", None),
        ("idempotency_key", "price-entry-" + "A" * 32), ("idempotency_key", "oprec-entry-" + "0" * 32),
    ])
    def test_each_field(self, field, value):
        r = post(client(), body(**{field: value}))
        assert (r.status_code, code(r), r.json()["detail"]["fields"]) == (422, "PRICE_ENTRY_INVALID", [field])

    @pytest.mark.parametrize("field", ["key", "value", "currency", "basis", "source", "applies_from",
                                       "idempotency_key"])
    def test_missing_required(self, field):
        r = post(client(), body(**{field: DROP}))
        assert r.json()["detail"]["fields"] == [field]

    def test_closed_object(self):
        r = post(client(), body(change_kind="INITIAL"))
        assert (code(r), r.json()["detail"]["fields"]) == ("PRICE_ENTRY_INVALID", ["change_kind"])
        assert code(post(client(), [body()])) == "PRICE_ENTRY_INVALID"

    def test_optional_fields_may_be_absent(self):
        assert post(client(), body(reason=DROP, dry_run=DROP)).status_code == 201

    def test_source_trimmed_and_limits(self):
        store = Store()
        assert post(client(store), body(source="  " + "s" * 120 + " ", value="999999.9999")).status_code == 201
        assert store.published[0][2].source_reference == "s" * 120

    @pytest.mark.parametrize("key", ["repair_visit_cost", "planned_service_cost", "charger_repair_cost",
                                     "interrupted_session_cost"])
    def test_every_future_key_refused(self, key):
        assert code(post(client(), body(key=key))) == "PRICE_KEY_NOT_ENTERABLE"

    @pytest.mark.parametrize("key", ["diesel_price_per_litre", "ev_gross_tariff_per_kwh",
                                     "productive_use_price_per_kwh"])
    def test_every_stored_key_saves(self, key):
        assert post(client(), body(key=key)).status_code == 201


class TestDerivation:
    @pytest.mark.parametrize("current,applies,kind", [
        ((), "2026-11-01", "INITIAL"),
        ((), "2026-11-13", "INITIAL"),
        (((FAR_PAST, datetime(2026, 1, 1, tzinfo=timezone.utc)),), "2026-11-01", "INITIAL"),  # no overlap
        (((FAR_PAST, None),), "2026-11-13", "SUCCESSION"),  # tomorrow
        (((FAR_PAST, None),), "2026-11-12", "CORRECTION"),  # today
        (((FAR_PAST, None),), "2026-10-01", "CORRECTION"),  # past
    ])
    def test_change_kind_table(self, current, applies, kind):
        store = Store(series(*current))
        r = post(client(store), body(applies_from=applies, reason="Contract rate replaces the estimate"))
        assert (r.status_code, r.json()["change_kind"]) == (201, kind)
        assert store.published[0][2].change_kind == kind

    def test_valid_from_is_site_local_midnight(self):
        store = Store()
        post(client(store), body(applies_from="2026-11-10"))
        p = store.published[0][2]
        assert p.valid_from == datetime(2026, 11, 9, 21, 0, tzinfo=timezone.utc) and p.valid_to is None

    def test_site_today_is_local(self):
        # 22:30 UTC on 12 Nov is 13 Nov in Nairobi: 13 Nov is "today" there, so over a price it is a CORRECTION.
        late = datetime(2026, 11, 12, 22, 30, tzinfo=timezone.utc)
        app = FastAPI()
        app.include_router(build_financial_assumption_router(
            SCOPE.get, entry_principal=lambda r, c: ENTRY_PRINCIPAL, store=Store(series((FAR_PAST, None))),
            site_zone=lambda t, s: NAIROBI, read_access=lambda r, c: None, clock=lambda: late))
        r = post(TestClient(app), body(applies_from="2026-11-13", dry_run=True))
        assert r.json()["change_kind"] == "CORRECTION"

    def test_expected_prior_is_series_head(self):
        snap = series((FAR_PAST, datetime(2026, 1, 1, tzinfo=timezone.utc)), (datetime(2026, 1, 1, tzinfo=timezone.utc),
                                                                               None))
        head = max(snap["cited"].values(), key=lambda r: r["revision_no"])
        store = Store(snap)
        post(client(store), body())
        assert store.published[0][2].expected_prior_revision_id == head["id"]
        empty = Store()
        post(client(empty), body())
        assert empty.published[0][2].expected_prior_revision_id is None

    def test_a_retry_of_the_head_save_rederives_that_save(self):
        # The INITIAL just saved under KEY is now the open current price: a naive re-derivation would read
        # CORRECTION against a new head. The retry derives the head's own kind and prior, so the store replays it.
        snap = series((datetime(2026, 11, 9, 21, tzinfo=timezone.utc), None))
        (head,) = snap["cited"].values()
        head.update(idempotency_key=KEY, change_kind="INITIAL", prior_revision_id=None)
        store = Store(snap, replayed=True)
        r = post(client(store), body(applies_from="2026-11-10"))
        assert (r.status_code, r.json()["change_kind"], r.json()["replayed"]) == (200, "INITIAL", True)
        p = store.published[0][2]
        assert (p.change_kind, p.expected_prior_revision_id) == ("INITIAL", None)

    def test_a_retry_replays_when_another_save_followed_it(self):
        # KEY made revision 1; revision 2 (another key) is now the head. The retry of KEY still replays (200), not 409.
        first = (datetime(2026, 11, 9, 21, tzinfo=timezone.utc), datetime(2026, 11, 20, tzinfo=timezone.utc))
        snap = series(first, (datetime(2026, 11, 20, tzinfo=timezone.utc), None))
        older, head = sorted(snap["cited"].values(), key=lambda r: r["revision_no"])
        older.update(idempotency_key=KEY, change_kind="INITIAL", prior_revision_id=None)
        head.update(idempotency_key="price-entry-" + "1" * 32, change_kind="SUCCESSION", prior_revision_id=older["id"])
        snap["revisions"] = [older]
        store = Store(snap, replayed=True)
        r = post(client(store), body(applies_from="2026-11-10"))
        assert (r.status_code, r.json()["change_kind"], r.json()["replayed"]) == (200, "INITIAL", True)
        p = store.published[0][2]
        assert (p.change_kind, p.expected_prior_revision_id) == ("INITIAL", None)

    def test_any_active_currency_without_a_series(self):
        assert post(client(), body(currency="KES")).status_code == 201


class TestDryRun:
    def test_never_publishes(self):
        store = Store(series((FAR_PAST, None)))
        r = post(client(store), body(applies_from="2026-11-01", dry_run=True))
        assert r.status_code == 200 and store.published == []
        assert r.json() == {
            "dry_run": True, "change_kind": "CORRECTION", "applies_from": "2026-11-01", "reason_required": True,
            "summary": "Correction from 1 Nov 2026. Figures from 1 Nov 2026 are recalculated with this price; the "
                       "earlier version is kept in the history."}

    def test_summary_words(self):
        r = post(client(), body(dry_run=True, applies_from="2026-11-10"))
        assert r.json()["summary"] == ("First diesel price for KOBO-001: 1.45 USD per litre from 10 Nov 2026. "
                                       "Figures from that date get a price.")
        assert r.json()["reason_required"] is False
        r = post(client(Store(series((FAR_PAST, None)))), body(dry_run=True))
        assert r.json()["summary"] == "New diesel price from 13 Nov 2026. Earlier figures keep the current price."

    def test_first_price_summary_uses_the_site_display_name(self):
        r = post(client(site_name=lambda t, s: "Kobo Solar Mini-grid"), body(dry_run=True, applies_from="2026-11-10"))
        assert r.json()["summary"].startswith("First diesel price for Kobo Solar Mini-grid: 1.45 USD")
        r = post(client(site_name=lambda t, s: "Kobo Solar Mini-grid"), body(applies_from="2026-11-10", key="ev_gross_tariff_per_kwh"))
        assert r.status_code == 201

    def test_null_site_name_falls_back_to_the_code(self):
        r = post(client(site_name=lambda t, s: None), body(dry_run=True, applies_from="2026-11-10"))
        assert r.json()["summary"].startswith("First diesel price for KOBO-001: ")

    def test_failed_name_lookup_is_503(self):
        def broken(t, s):
            raise Down("name lookup failed")
        r = post(client(site_name=broken), body(dry_run=True))
        assert (r.status_code, code(r)) == (503, "ASSUMPTION_STORE_UNAVAILABLE")

    def test_dry_run_still_refuses_shape_and_conflicts(self):
        assert code(post(client(), body(dry_run=True, value="0"))) == "PRICE_ENTRY_INVALID"
        store = Store(series((NOW + timedelta(days=10), None)))
        assert code(post(client(store), body(dry_run=True, applies_from="2026-11-17"))) == \
            "SUCCESSION_OVERLAP_NOT_PERMITTED"


class TestSave:
    def test_actor_channel_attestation_provenance(self):
        store = Store()
        r = post(client(store), body())
        _, _, p, principal = store.published[0]
        assert principal is a.SITE_ADMIN_PRICE_PUBLISHER
        assert (principal.actor_id, principal.actor_kind) == ("service:operator-entry", "SYSTEM")
        assert principal.authorization_basis == (
            "SITE_ADMIN_ENTRY: entered on screen through the server-configured entry service, labelled 'Entered by "
            "site admin'; no signed-in person (D-PRICE.1)")
        assert p.channel == "SITE_ADMIN_ENTRY" == a.SITE_ADMIN_CHANNEL and p.channel in a.SYSTEM_CHANNELS
        assert p.provenance == {"service": "operator-entry", "job": "site-admin-price-entry", "rule": "price-entry/1"}
        assert (p.correction_reason, p.basis, p.currency, str(p.value)) == (None, "CONTRACT_RATE", "USD", "1.45")
        assert r.status_code == 201

    def test_entry_note_for_non_correction(self):
        store = Store()
        post(client(store), body(reason="  Contract rate replaces the estimate "))
        p = store.published[0][2]
        assert p.correction_reason is None
        assert p.provenance["entry_note"] == "Contract rate replaces the estimate"

    def test_correction_reason_not_entry_note(self):
        store = Store(series((FAR_PAST, None)))
        post(client(store), body(applies_from="2026-11-01", reason="Wrong price typed"))
        p = store.published[0][2]
        assert (p.change_kind, p.correction_reason) == ("CORRECTION", "Wrong price typed")
        assert "entry_note" not in p.provenance

    def test_response_words(self):
        r = post(client(), body(key="ev_gross_tariff_per_kwh", value="0.3", applies_from="2026-11-10"))
        got = r.json()
        assert r.status_code == 201 and got["set_by"] == "Entered by site admin"
        assert (got["revision_no"], got["change_kind"], got["applies_from"], got["replayed"]) == \
            (4, "INITIAL", "2026-11-10", False)
        assert got["recorded_at"] == NOW.isoformat()
        assert got["summary"] == ("Saved. Charging tariff 0.3 USD per kWh from 10 Nov 2026. Figures that use it read "
                                  "\"Updating…\" for a few minutes, then show the new price.")

    def test_replay_is_200(self):
        r = post(client(Store(replayed=True)), body())
        assert (r.status_code, r.json()["replayed"]) == (200, True)

    def test_human_route_still_refused(self):
        r = client().post("/api/sites/KOBO-001/financial-assumptions", json=body())
        assert (r.status_code, code(r)) == (401, "UNAUTHENTICATED")


def test_default_read_access_admits_nobody():
    app = FastAPI()
    app.include_router(build_financial_assumption_router(SCOPE.get, entry_principal=lambda r, c: ENTRY_PRINCIPAL,
                                                         store=Store(), site_zone=lambda t, s: NAIROBI))
    r = post(TestClient(app), body())
    assert (r.status_code, code(r)) == (401, "UNAUTHENTICATED")


def test_scope_outage_is_503():
    def down(site_code):
        raise Down("no site store")
    r = post(client(scope=down), body())
    assert (r.status_code, code(r)) == (503, "ASSUMPTION_STORE_UNAVAILABLE")


def test_product_app_composes_the_route_without_a_database(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    from assetops_backend.main import create_app
    app = create_app(operational_entry_principal=lambda r, c: ENTRY_PRINCIPAL)
    r = TestClient(app).post(URL, json=body())
    # Without a database the Site scope itself is unreachable: a typed 503, never a 500 or a write.
    assert (r.status_code, code(r)) == (503, "ASSUMPTION_STORE_UNAVAILABLE")


def test_constants_reuse_the_entry_service():
    assert a.SITE_ADMIN_PRICE_PUBLISHER.actor_id == ENTRY_PRINCIPAL
    assert pe.SET_BY == "Entered by site admin"


def test_pr1_label_for_future_keys():
    class Links:
        def prices_ref(self, site_code, key=None, need=None):
            return {"site_code": site_code, "key": key}

        def href_for(self, ref):
            return f"/sites/{ref['site_code']}/financials/prices?key={ref['key']}"

    future = price_action.wire(price_action.WARNING_SPEC["REPEATED_MAINTENANCE_NO_RESULT"], "KOBO-001", "Kobo", Links())
    stored = price_action.wire(price_action.FINDING_FUEL_SPEC, "KOBO-001", "Kobo", Links())
    assert future["label"] == "What pricing this needs →"
    assert stored["label"] == "Set a diesel price for Kobo →"
    assert set(pe.PRICE_NOUN) - set(price_action.STORED_KEYS) == {
        "repair_visit_cost", "planned_service_cost", "charger_repair_cost", "interrupted_session_cost"}
