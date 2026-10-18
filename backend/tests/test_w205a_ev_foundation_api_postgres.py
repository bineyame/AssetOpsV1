"""W2-05a selected EV Foundation read: `GET /api/sites/{code}/ev/foundation?at=`.

`D-2026-10-18-w2-05-buildspec` "Role set, binding and selected read", Q2-Q4 and QE. EV-LAB-001 is installed with
its complete 1 October basis; gap revisions are test-created on the same Site after the 6 October window and every
read pins `at`. Needs `ASSETOPS_TEST_DATABASE_URL` naming a `*_test` database; skipped (never passed) without it.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)"
)

if URL:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from assetops_backend.ev_foundation_api import build_ev_foundation_router
    from assetops_backend.sites.binding_service import BindingService
    from assetops_backend.sites.cutover import ImportedSiteRegistry
    from assetops_backend.sites.foundation_service import FoundationService
    from assetops_backend.sites.ports import SiteStoreUnavailable
    from test_s1_bindings_postgres import Clock, _alembic, engine, store  # noqa: F401
    from test_w201_cold_foundation_postgres import Health, kobo
    from test_w205a_ev_foundation_postgres import complete_requests, install

NOW = datetime(2026, 10, 17, 12, 0, tzinfo=timezone.utc)
STOCKED_AT = "2026-10-06T12:00:00Z"
GAP_FROM = datetime(2026, 10, 8, tzinfo=timezone.utc)
GAP_AT = "2026-10-08T12:00:00Z"
LIMIT_FROM = datetime(2026, 10, 12, tzinfo=timezone.utc)
LIMIT_AT = "2026-10-12T12:00:00Z"


def client(store, health=None, access=None, service=None):
    service = service or FoundationService(store, "demo", Clock(NOW))
    if health is not None:
        health.store = store
    kwargs = {} if access is None else {"access": access}
    app = FastAPI()
    app.include_router(build_ev_foundation_router(ImportedSiteRegistry(service), health, Clock(NOW), **kwargs))
    return TestClient(app)


def read(c, code="EV-LAB-001", **params):
    return c.get(f"/api/sites/{code}/ev/foundation", params=params)


def codes(body, blocking=None):
    return [m["code"] for m in body["readiness"]["messages"] if blocking is None or m["blocking"] is blocking]


def assets(store, result):
    return {a.asset_code: str(a.id) for a in store.registrations(result.tenant.id, result.site.id).assets}


def publish_without(store, result, dropped):
    requests = [r for r in complete_requests(store, result) if (r.device_id, r.signal_id) not in dropped]
    BindingService(store, Clock(NOW - timedelta(hours=1))).publish(
        result.tenant, result.site, requests=requests, effective_from=GAP_FROM, note="W2-05a API test gap.",
        role_set="ev-roles-1")


def change_foundation(store, result, change, effective_from=LIMIT_FROM):
    def changed(content, _version):
        copy = json.loads(json.dumps(content))
        change(copy)
        return copy

    FoundationService(store, "demo", Clock(NOW - timedelta(minutes=30)))._publish_content_change(
        result.tenant, result.site, effective_from=effective_from, note="W2-05a API test Foundation change.",
        unchanged=lambda _c: None, change=changed)


def test_stocked_selection_is_ready_with_exact_values(store) -> None:
    result = install(store)
    ids = assets(store, result)
    response = read(client(store), at=STOCKED_AT)
    assert response.status_code == 200, response.text
    body = response.json()
    [binding_set] = store.binding_sets(result.tenant.id, result.site.id)
    assert (body["site_id"], body["site_code"], body["site_type"]) == (str(result.site.id), "EV-LAB-001",
                                                                       "EV_CHARGING")
    assert body["selected_at"] == STOCKED_AT
    assert body["binding_revision_id"] == str(binding_set.id)
    assert body["foundation_revision_id"] == str(binding_set.foundation_revision_id)
    assert body["feed"] == {"asset_id": ids["feed-1"], "limit_kw": "80", "meter_asset_id": ids["site-meter-1"]}
    [charger] = body["chargers"]
    assert (charger["asset_id"], charger["max_kw"]) == (ids["charger-1"], "60")
    assert [c["asset_id"] for c in charger["connectors"]] == [ids["c1"], ids["c2"]]
    for connector in charger["connectors"]:
        assert (connector["max_kw"], connector["meter_resolution_kwh"], connector["meter_error_bound_kwh"]) == (
            "60", "0.001", "0.001")
        assert connector["clock_error_bound_seconds"] == "30"
        assert connector["enabled_schedule"] == {
            "enabled": True, "time_zone": "Etc/UTC",
            "weekly": [{"weekday": "TUESDAY", "local_start": "08:00", "local_end": "16:00",
                        "utc_offset_minutes": 0}]}
    assert {n["component_type"] for n in body["topology"]["nodes"]} == {"AC_BUS", "METER", "EV_CHARGER",
                                                                         "EV_CONNECTOR"}
    assert {e["medium"] for e in body["topology"]["edges"]} == {"AC", "SIGNAL"}
    assert len(body["bindings"]) == 15
    cadence = {(b["role"], b["device_id"], b["signal_id"]): b["cadence_seconds"] for b in body["bindings"]}
    assert cadence[("ev_connector_state", "c1-connector-controller", "state")] == 60
    assert cadence[("ev_connector_energy", "c2-connector-meter", "energy")] == 300
    assert cadence[("ev_site_import", "site-meter", "import")] == 300
    assert cadence[("ev_session_event", "c1-charger-controller", "session-event")] is None
    assert all(b["effective_from"] == "2026-10-01T00:00:00Z" and b["effective_to"] is None
               for b in body["bindings"])
    # Ready means configured: contact and commissioning stay separate nonblocking notices.
    assert body["readiness"]["state"] == "READY_TO_REPORT"
    assert codes(body) == ["SOURCE_NOT_CONTACTED", "COMMISSIONING_UNCONFIRMED"]
    assert body["commissioning"] == {"state": "UNCONFIRMED", "evidence_ids": []}
    assert body["contact"] == {"state": "NEVER", "as_of": None, "checked_at": "2026-10-17T12:00:00Z",
                               "gateway_id": str(binding_set.gateway_id),
                               "reason": "No gateway health read is configured"}


def test_contact_maps_s7_receipt_and_never_claims_commissioning(store) -> None:
    result = install(store)
    gateway = str(store.binding_sets(result.tenant.id, result.site.id)[0].gateway_id)
    recent = read(client(store, Health(NOW - timedelta(minutes=5))), at=STOCKED_AT).json()
    # QL: a historical selection (6 Oct) does not date the contact check; freshness is at request time.
    assert recent["contact"] == {"state": "RECENT", "as_of": "2026-10-17T11:55:00Z",
                                 "checked_at": "2026-10-17T12:00:00Z", "gateway_id": gateway,
                                 "reason": None}
    assert codes(recent) == ["COMMISSIONING_UNCONFIRMED"]
    assert recent["commissioning"] == {"state": "UNCONFIRMED", "evidence_ids": []}
    stale = read(client(store, Health(NOW - timedelta(hours=2))), at=STOCKED_AT).json()["contact"]
    assert (stale["state"], stale["as_of"]) == ("STALE", "2026-10-17T10:00:00Z")
    # QK: stale contact is not "never contacted".
    stale_body = read(client(store, Health(NOW - timedelta(hours=2))), at=STOCKED_AT).json()
    assert "SOURCE_NOT_CONTACTED" not in codes(stale_body)
    never = read(client(store, Health(None)), at=STOCKED_AT).json()
    assert never["contact"] == {"state": "NEVER", "as_of": None, "checked_at": "2026-10-17T12:00:00Z",
                                "gateway_id": gateway,
                                "reason": "No diagnostic is recorded for the selected gateway"}
    assert "SOURCE_NOT_CONTACTED" in codes(never, blocking=False)


@pytest.mark.parametrize("dropped,code,connector", [
    ({("c2-connector-meter", "energy")}, "METER_NOT_BOUND", "c2"),
    ({("c1-charger-controller", "session-event")}, "SESSION_EVENTS_NOT_BOUND", "c1"),
    ({("c1-connector-controller", "state")}, "STATUS_NOT_BOUND", "c1"),
])
def test_missing_required_binding_revision_is_incomplete_and_the_original_stays(store, dropped, code,
                                                                                connector) -> None:
    result = install(store)
    publish_without(store, result, dropped)
    c = client(store)
    gap = read(c, at=GAP_AT).json()
    assert gap["readiness"]["state"] == "CONFIGURATION_INCOMPLETE"
    [message] = [m for m in gap["readiness"]["messages"] if m["blocking"]]
    assert (message["code"], message["component_id"], message["asset_id"]) == (
        code, connector, assets(store, result)[connector])
    assert len(gap["bindings"]) == 14
    original = read(c, at=STOCKED_AT).json()
    assert original["readiness"]["state"] == "READY_TO_REPORT" and len(original["bindings"]) == 15
    assert original["binding_revision_id"] != gap["binding_revision_id"]


def test_optional_site_import_absent_is_ready_with_a_capability_notice(store) -> None:
    result = install(store)
    publish_without(store, result, {("site-meter", "import"), ("c1-connector-controller", "fault-event")})
    body = read(client(store), at=GAP_AT).json()
    assert body["readiness"]["state"] == "READY_TO_REPORT"
    assert codes(body, blocking=False)[0] == "SITE_IMPORT_NOT_BOUND"
    assert codes(body, blocking=True) == []


def test_missing_limit_revision_is_incomplete_with_null_limit(store) -> None:
    result = install(store)
    change_foundation(store, result, lambda content: next(
        c for c in content["components"] if c["component_type"] == "AC_BUS").pop("properties"))
    c = client(store)
    body = read(c, at=LIMIT_AT).json()
    assert body["feed"]["limit_kw"] is None and body["feed"]["asset_id"] is not None
    assert codes(body, blocking=True) == ["FEED_OR_LIMIT_MISSING"]
    assert read(c, at=STOCKED_AT).json()["feed"]["limit_kw"] == "80"  # older revision keeps its own limit


def test_site_import_cadence_is_the_minimum_connector_meter_cadence(store) -> None:
    """QE: Site import uses the minimum ev-meter-cadence; other meter roles use their own connector's value."""
    result = install(store)

    def faster_c1(content):
        c1 = next(c for c in content["components"] if c["component_id"] == "c1")
        next(p for p in c1["properties"] if p["property_key"] == "ev-meter-cadence")["value"] = 2

    change_foundation(store, result, faster_c1)
    body = read(client(store), at=LIMIT_AT).json()
    cadence = {(b["device_id"], b["signal_id"]): b["cadence_seconds"] for b in body["bindings"]}
    assert cadence[("site-meter", "import")] == 120
    assert cadence[("c1-connector-meter", "energy")] == 120
    assert cadence[("c2-connector-meter", "energy")] == 300
    stocked = read(client(store), at=STOCKED_AT).json()["bindings"]
    assert next(b for b in stocked if b["role"] == "ev_site_import")["cadence_seconds"] == 300


def test_disabled_connector_schedule_and_per_connector_clock_bound(store) -> None:
    """QH/QI: a disabled connector serves enabled=false with an empty weekly array; clock bound per connector."""
    result = install(store)

    def disable_c2(content):
        by_id = {c["component_id"]: c for c in content["components"]}
        prop = {p["property_key"]: p for p in by_id["c2"]["properties"]}
        prop["ev-connector-enabled"]["value"] = "DISABLED"
        prop["ev-clock-error-bound"]["value"] = 45
        next(e for e in content["connector_enable_schedules"]
             if e["connector_asset_id"] == "c2")["weekly"] = []

    change_foundation(store, result, disable_c2)
    [charger] = read(client(store), at=LIMIT_AT).json()["chargers"]
    c1, c2 = charger["connectors"]
    assert c1["enabled_schedule"]["enabled"] is True and len(c1["enabled_schedule"]["weekly"]) == 1
    assert c2["enabled_schedule"] == {"enabled": False, "time_zone": "Etc/UTC", "weekly": []}
    assert (c1["clock_error_bound_seconds"], c2["clock_error_bound_seconds"]) == ("30", "45")


def test_no_declared_feed_serves_a_null_feed_object(store) -> None:
    """QJ: no feed -> feed is an object of three nulls; chargers and connectors stay visible."""
    result = install(store)

    def drop_feed(content):
        content["components"] = [c for c in content["components"] if c["component_type"] != "AC_BUS"]
        topology = content["topology"]
        dropped = {n["node_id"] for n in topology["nodes"] if n.get("component_id") == "feed-1"}
        topology["nodes"] = [n for n in topology["nodes"] if n["node_id"] not in dropped]
        topology["connections"] = [e for e in topology["connections"] if e["from_node"] not in dropped]
        for entry in content["connector_enable_schedules"]:
            entry["weekly"] = []

    change_foundation(store, result, drop_feed)
    body = read(client(store), at=LIMIT_AT).json()
    assert body["feed"] == {"asset_id": None, "limit_kw": None, "meter_asset_id": None}
    assert len(body["chargers"][0]["connectors"]) == 2
    assert "FEED_OR_LIMIT_MISSING" in codes(body, blocking=True)


def test_refusals(store) -> None:
    install(store)
    kobo(store)
    c = client(store, Health(NOW))
    for status in (401, 403):
        denied = read(client(store, access=lambda request, code, s=status: s), at=STOCKED_AT)
        assert denied.status_code == status and set(denied.json()) == {"error"}
    assert read(client(store, access=lambda r, code: 401)).json()["error"]["code"] == "UNAUTHENTICATED"
    assert read(client(store, access=lambda r, code: 403)).json()["error"]["code"] == "SITE_SCOPE_FORBIDDEN"
    for code in ("EV-LAB-999", "KOBO-001"):  # unknown, and wrong Site type after the access check
        missing = read(c, code)
        assert missing.status_code == 404 and missing.json()["error"]["code"] == "SITE_NOT_FOUND"
    for bad in ("yesterday", "2026-10-06T12:00:00", "2026-10-06T15:00:00+03:00"):
        refused = read(c, at=bad)
        assert refused.status_code == 422 and refused.json()["error"]["code"] == "EV_SELECTION_INVALID"
    extra = c.get("/api/sites/EV-LAB-001/ev/foundation", params={"at": STOCKED_AT, "connector": "c1"})
    assert extra.status_code == 422 and extra.json()["error"]["code"] == "EV_SELECTION_INVALID"
    repeated = c.get(f"/api/sites/EV-LAB-001/ev/foundation?at={STOCKED_AT}&at={STOCKED_AT}")
    assert repeated.status_code == 422 and repeated.json()["error"]["code"] == "EV_SELECTION_INVALID"
    down = read(client(store, Health(fail=True)), at=STOCKED_AT)
    assert down.status_code == 503 and down.json()["error"]["code"] == "EV_FOUNDATION_UNAVAILABLE"

    class Down(FoundationService):
        def read(self, *args, **kwargs):
            raise SiteStoreUnavailable("Foundation store down")

    unavailable = read(client(store, service=Down(store, "demo", Clock(NOW))), at=STOCKED_AT)
    assert unavailable.status_code == 503 and unavailable.json()["error"]["code"] == "EV_FOUNDATION_UNAVAILABLE"
