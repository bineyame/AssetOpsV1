"""OWN-G3a units (build sheet OWN-GAPS-2026-11-08 §3.5, R2-G3a): `compose_entry` and the entry route with a fake
service and `TestClient`. The startup-refusal case lives in `host/tests/test_own_g3_entry_env.py` (R2-G3a 6)."""

from __future__ import annotations

import hashlib
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from assetops_backend.work import model as m
from assetops_backend.work.model import WorkRefused, WorkStoreUnavailable
from assetops_backend.work.operational_entry import (ENTRY_ACTOR, compose_entry, entry_site_context,
                                                       validate_entry)
from assetops_backend.work_api import build_work_router

TENANT = UUID("00000000-0000-4000-8000-000000000001")
SITE = UUID("00000000-0000-4000-8000-000000000002")
TANK = "00000000-0000-4000-8000-0000000000aa"
DAR = "Africa/Dar_es_Salaam"
KEY = "oprec-entry-" + "0123456789abcdef" * 2
URL = "/api/sites/KISIWA-001/work/operational-entries"


def entry(**over) -> dict:
    body = {"entry": "TANK_DIP", "value": "198", "taken_at_local": "2026-11-14T06:00", "ticket_reference": None,
            "idempotency_key": KEY}
    body.update(over)
    return body


def refused_code(call, *args) -> str:
    with pytest.raises(WorkRefused) as caught:
        call(*args)
    return caught.value.code


# ---- compose_entry -----------------------------------------------------------------------------------------------

def test_tank_dip_maps_to_a_tank_record() -> None:
    c = compose_entry(entry(), DAR, TANK)
    assert c == {"kind": "TANK_DIP", "body": "Tank dip at the 06:00 round: 198 L.",
                 "occurred_at": "2026-11-14T03:00:00Z", "period_end": None, "unit": "L", "quantity": "198",
                 "source_document_sha256": None, "case_id": None, "actor": ENTRY_ACTOR, "idempotency_key": KEY,
                 "asset_id": TANK}
    assert ENTRY_ACTOR == {"kind": "SERVICE", "id": "service:operator-entry",
                           "attestation": "service=operator-entry;job=site-admin-entry;rule=oprec-entry/1"}


def test_fuel_delivery_maps_with_the_ticket_digest() -> None:
    c = compose_entry(entry(entry="FUEL_DELIVERY", value="300", ticket_reference="KIS-DT-0002"), DAR, TANK)
    assert (c["kind"], c["unit"], c["quantity"], c["asset_id"]) == ("FUEL_DELIVERY", "L", "300", TANK)
    assert c["body"] == "Fuel delivery of 300 L received, ticket KIS-DT-0002."
    assert c["source_document_sha256"] == hashlib.sha256(b"Fuel delivery ticket KIS-DT-0002, 300 L").hexdigest()


def test_stock_and_meter_are_manual_readings_without_an_asset() -> None:
    stock = compose_entry(entry(entry="STOCK_IN_CHAMBER", value="40"), DAR, None)
    meter = compose_entry(entry(entry="METER_READING", value="1520.5"), DAR, TANK)
    assert (stock["kind"], stock["unit"], stock["body"], stock["source_document_sha256"]) == (
        "MANUAL_READING", "kg", "Stock in chamber: 40 kg.", None)
    assert (meter["kind"], meter["unit"], meter["body"], meter["quantity"]) == (
        "MANUAL_READING", "kWh", "Meter reading: 1520.5 kWh.", "1520.5")
    assert "asset_id" not in stock and "asset_id" not in meter


def test_dar_es_salaam_six_local_is_three_utc() -> None:
    assert compose_entry(entry(), DAR, TANK)["occurred_at"] == "2026-11-14T03:00:00Z"
    assert compose_entry(entry(taken_at_local="2026-11-14T00:30"), DAR, TANK)["occurred_at"] == "2026-11-13T21:30:00Z"


def test_value_is_normalised_in_body_digest_and_quantity() -> None:
    """R2-G3a 3: `198`, `198.0` and `0198` compose identical commands; `198.50` stores `198.5`."""
    deliveries = [compose_entry(entry(entry="FUEL_DELIVERY", value=v, ticket_reference="T-1"), DAR, TANK)
                  for v in ("198", "198.0", "0198")]
    assert deliveries[0] == deliveries[1] == deliveries[2]
    dip = compose_entry(entry(value="198.50"), DAR, TANK)
    assert (dip["quantity"], dip["body"]) == ("198.5", "Tank dip at the 06:00 round: 198.5 L.")
    assert compose_entry(entry(value="0"), DAR, TANK)["quantity"] == "0"


@pytest.mark.parametrize("over", [
    {"entry": "OPERATOR_LOG"}, {"entry": None},
    {"value": 198}, {"value": "-1"}, {"value": "1234567"}, {"value": "1.2345"}, {"value": "1e3"}, {"value": " 1"},
    {"value": "198\n"}, {"value": "١٩٨"},
    {"entry": "FUEL_DELIVERY", "value": "0", "ticket_reference": None},
    {"entry": "FUEL_DELIVERY", "value": "0.000", "ticket_reference": "T-1"},
    {"taken_at_local": "2026-11-14 06:00"}, {"taken_at_local": "2026-11-14T06:00:00"},
    {"taken_at_local": "2026-02-30T06:00"}, {"taken_at_local": "2026-11-14T24:00"}, {"taken_at_local": None},
    {"entry": "FUEL_DELIVERY", "ticket_reference": ""}, {"entry": "FUEL_DELIVERY", "ticket_reference": "-bad"},
    {"entry": "FUEL_DELIVERY", "ticket_reference": "A" * 41}, {"entry": "FUEL_DELIVERY", "ticket_reference": 7},
    {"ticket_reference": "T-1"},
    {"idempotency_key": "oprec-entry-" + "A" * 32}, {"idempotency_key": "oprec-entry-abc"}, {"idempotency_key": None},
    {"actor": {"kind": "SERVICE", "id": "service:operator-entry", "attestation": "x"}},
    {"occurred_at": "2026-11-14T03:00:00Z"},
])
def test_each_invalid_shape_is_oprec_entry_invalid(over) -> None:
    assert refused_code(validate_entry, entry(**over)) == "OPREC_ENTRY_INVALID"


@pytest.mark.parametrize("missing", ["entry", "value", "taken_at_local", "ticket_reference", "idempotency_key"])
def test_a_missing_key_is_invalid(missing) -> None:
    body = entry()
    del body[missing]
    assert refused_code(validate_entry, body) == "OPREC_ENTRY_INVALID"


def test_non_objects_are_invalid() -> None:
    for body in (None, [], "x", 3):
        assert refused_code(validate_entry, body) == "OPREC_ENTRY_INVALID"


def test_a_delivery_without_a_ticket_is_ticket_required() -> None:
    assert refused_code(validate_entry, entry(entry="FUEL_DELIVERY", value="300")) == "OPREC_ENTRY_TICKET_REQUIRED"


def test_a_fuel_entry_with_no_single_tank_is_no_tank() -> None:
    assert refused_code(compose_entry, entry(), DAR, None) == "OPREC_ENTRY_NO_TANK"
    assert refused_code(compose_entry, entry(entry="FUEL_DELIVERY", ticket_reference="T-1"), DAR,
                        None) == "OPREC_ENTRY_NO_TANK"
    assert m.MESSAGES["OPREC_ENTRY_NO_TANK"] == "This Site has no single fuel tank to record against."
    assert m.MESSAGES["OPREC_ENTRY_INVALID"] == ("The entry, value, time taken, ticket reference or key is not "
                                                 "valid.")
    assert m.MESSAGES["OPREC_ENTRY_TICKET_REQUIRED"] == "A fuel delivery needs its ticket reference."
    assert {c: m.STATUS[c] for c in ("OPREC_ENTRY_INVALID", "OPREC_ENTRY_TICKET_REQUIRED",
                                     "OPREC_ENTRY_NO_TANK")} == dict.fromkeys(
        ("OPREC_ENTRY_INVALID", "OPREC_ENTRY_TICKET_REQUIRED", "OPREC_ENTRY_NO_TANK"), 422)


def test_site_context_maps_store_failures_to_unavailable() -> None:
    def broken(t, s):
        raise RuntimeError("DATABASE_URL is not set")

    def ok(t, s):
        return DAR, TANK, object()

    assert entry_site_context(ok)(TENANT, SITE) == (DAR, TANK)
    with pytest.raises(WorkStoreUnavailable):
        entry_site_context(broken)(TENANT, SITE)

    def bug(t, s):
        raise KeyError("x")

    with pytest.raises(KeyError):
        entry_site_context(bug)(TENANT, SITE)


# ---- the route -------------------------------------------------------------------------------------------------

class FakeService:
    def __init__(self, result=(201, {"public_code": "REC-000001"}), refuse: str | None = None) -> None:
        self.calls: list[tuple] = []
        self.result, self.refuse = result, refuse

    def post_operational_record(self, tenant_id, site_id, body, principal):
        self.calls.append((tenant_id, site_id, body, principal))
        if self.refuse:
            raise WorkRefused(self.refuse)
        return self.result


def scope(code: str):
    return ("KISIWA-001", TENANT, SITE) if code == "KISIWA-001" else None


def client(service=None, *, principal=True, context=True, tank=TANK, access=None, grant=None) -> TestClient:
    calls = []

    def site_context(t, s):
        calls.append((t, s))
        return DAR, tank

    kwargs = {}
    if access is not None:
        kwargs["access"] = access
    if grant is not None:
        kwargs["command_access"] = grant
    app = FastAPI()
    app.include_router(build_work_router(
        service, scope, (WorkStoreUnavailable,),
        entry_principal=(lambda r, c: "service:operator-entry") if principal else (lambda r, c: None),
        site_context=site_context if context else None, **kwargs))
    tc = TestClient(app)
    tc.context_calls = calls
    return tc


def detail(response) -> tuple[int, str]:
    return response.status_code, response.json()["detail"]["code"]


def test_success_passes_the_composed_command_and_server_principal() -> None:
    service = FakeService()
    response = client(service).post(URL, json=entry())
    assert (response.status_code, response.json()) == (201, {"public_code": "REC-000001"})
    [(tenant, site, body, who)] = service.calls
    assert (tenant, site, who) == (TENANT, SITE, "service:operator-entry")
    assert body == compose_entry(entry(), DAR, TANK)


def test_an_identical_retry_returns_the_service_200() -> None:
    service = FakeService(result=(200, {"public_code": "REC-000001"}))
    assert client(service).post(URL, json=entry()).status_code == 200


def test_no_principal_is_403_even_with_an_invalid_body_and_no_store() -> None:
    for service in (FakeService(), None):
        tc = client(service, principal=False, context=service is not None)
        assert detail(tc.post(URL, json={"actor": "x"})) == (403, "WORK_WRITE_FORBIDDEN")
        assert tc.context_calls == []


def test_a_principal_with_no_store_is_503_before_shape() -> None:
    assert detail(client(None).post(URL, json={"bad": 1})) == (503, "WORK_STORE_UNAVAILABLE")
    assert detail(client(FakeService(), context=False).post(URL, json={"bad": 1})) == (503, "WORK_STORE_UNAVAILABLE")


def test_access_404_and_the_write_grant_precede_the_principal() -> None:
    assert detail(client(FakeService(), principal=False).post(
        "/api/sites/NOPE-1/work/operational-entries", json=entry())) == (404, "SITE_NOT_FOUND")
    assert detail(client(FakeService(), access=lambda r, c: 403).post(URL, json=entry()))[0] == 403
    assert detail(client(FakeService(), principal=False, grant=lambda r, c: 401).post(URL, json=entry())) == (
        401, "UNAUTHENTICATED")


def test_shape_is_checked_before_the_site_context() -> None:
    service = FakeService()
    tc = client(service)
    assert detail(tc.post(URL, json=entry(value="x"))) == (422, "OPREC_ENTRY_INVALID")
    assert detail(tc.post(URL, content=b"not json", headers={"content-type": "application/json"})) == (
        422, "OPREC_ENTRY_INVALID")
    assert tc.context_calls == [] and service.calls == []


def test_the_browser_cannot_send_an_actor() -> None:
    service = FakeService()
    body = {**entry(), "actor": {"kind": "SERVICE", "id": "service:operator-entry",
                                 "attestation": "service=operator-entry;job=site-admin-entry;rule=oprec-entry/1"}}
    assert detail(client(service).post(URL, json=body)) == (422, "OPREC_ENTRY_INVALID")
    assert service.calls == []


def test_ticket_required_and_no_tank_over_the_wire() -> None:
    service = FakeService()
    assert detail(client(service).post(URL, json=entry(entry="FUEL_DELIVERY"))) == (
        422, "OPREC_ENTRY_TICKET_REQUIRED")
    assert detail(client(service, tank=None).post(URL, json=entry())) == (422, "OPREC_ENTRY_NO_TANK")
    assert client(service, tank=None).post(URL, json=entry(entry="METER_READING")).status_code == 201
    assert len(service.calls) == 1


@pytest.mark.parametrize("code", ["WORK_OCCURRED_AT_FUTURE", "WORK_OCCURRED_AT_TOO_OLD",
                                  "WORK_RECORD_QUANTITY_INVALID", "WORK_EVENT_DUPLICATE_KEY"])
def test_service_refusals_pass_through_with_their_status(code) -> None:
    assert detail(client(FakeService(refuse=code)).post(URL, json=entry())) == (m.STATUS[code], code)


def test_a_site_context_outage_is_503() -> None:
    def down(t, s):
        raise WorkStoreUnavailable("down")

    app = FastAPI()
    app.include_router(build_work_router(FakeService(), scope, (WorkStoreUnavailable,),
                                         entry_principal=lambda r, c: "service:operator-entry", site_context=down))
    assert detail(TestClient(app).post(URL, json=entry())) == (503, "WORK_STORE_UNAVAILABLE")


def test_the_existing_record_route_keeps_its_own_principal() -> None:
    """The entry principal is not the generic SERVICE principal: `/operational-records` stays 403 by default."""
    service = FakeService()
    client(service).post("/api/sites/KISIWA-001/work/operational-records", json={})
    assert [call[3] for call in service.calls] == [None]  # no_service_principal: the real service then answers 403
