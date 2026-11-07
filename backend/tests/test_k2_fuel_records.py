"""DIESEL-K2 L0 (`.agent/build-sheet-DIESEL-1.md` §9c.2): fuel delivery and tank dip validation, no database.

A fake transaction implements only the `_Tx` methods `post_operational_record` calls. The OPERATOR_LOG command hash is
pinned to the literal computed on main (099b57c96) before any K2 edit, so an existing kind's hash stays byte-equal.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest

from assetops_backend.work import fuel_records as fr
from assetops_backend.work import model as m
from assetops_backend.work import service as svc_module
from assetops_backend.work.model import WorkRefused
from assetops_backend.work.service import WorkService
from test_w401_work_service_postgres import PRINCIPAL, oprec

TENANT = UUID("00000000-0000-4000-8000-000000000001")
SITE = UUID("00000000-0000-4000-8000-000000000002")
TANK = "00000000-0000-4000-8000-0000000000f1"
GENERATOR = "00000000-0000-4000-8000-0000000000f2"
NOW = datetime(2026, 11, 1, 1, 0, tzinfo=timezone.utc)
# Pinned on main 099b57c96 (clean tree) through this file's fake store, before any K2 edit.
OPERATOR_LOG_SHA = "078d5fcc2e16d8e3aff4c26f6f9044cbff296f9a33dd1d95d81436c9b9a23a1d"
TICKET = "ab" * 32

MESSAGES = {
    "WORK_RECORD_ASSET_REQUIRED": "A fuel delivery or tank dip must name the fuel tank it concerns.",
    "WORK_RECORD_ASSET_NOT_ALLOWED": "Only a fuel delivery or tank dip names a tank; other record kinds carry no asset.",
    "WORK_RECORD_ASSET_NOT_TANK": "The named asset is not a fuel tank at this Site.",
    "WORK_RECORD_QUANTITY_INVALID": "A fuel delivery needs a volume above 0 L, and a tank dip a volume of 0 L or more, "
                                    "in L.",
    "WORK_RECORD_TICKET_REQUIRED": "A fuel delivery needs the SHA-256 of its delivery ticket.",
}


class FakeTx:
    def __init__(self, assets: dict[str, str]) -> None:
        self.rows: dict[str, dict] = {}
        self.assets = assets

    def lineage_by_key(self, table, key):
        return self.rows.get(key)

    def db_now(self):
        return NOW

    def case(self, case_id):
        return None

    def asset_type(self, asset_id):
        return self.assets.get(asset_id)

    def next_public_no(self):
        return len(self.rows) + 1

    def insert_operational_record(self, r):
        self.rows[r["idempotency_key"]] = {**r, "recorded_at": NOW}


class FakeStore:
    def __init__(self, assets: dict[str, str] | None = None) -> None:
        self.tx = FakeTx({TANK: "FUEL_TANK", GENERATOR: "GENERATOR"} if assets is None else assets)

    def transaction(self, tenant_id, site_id, work):
        return work(self.tx)


def service(store: FakeStore | None = None) -> tuple[WorkService, FakeStore]:
    store = store or FakeStore()
    return WorkService(store, new_id=lambda: UUID("00000000-0000-4000-8000-0000000000aa")), store


def post(body: dict, store: FakeStore | None = None):
    svc, store = service(store)
    return svc.post_operational_record(TENANT, SITE, body, PRINCIPAL), store


def delivery(**over) -> dict:
    return oprec("kisiwa-kis-delivery-1", **{
        "kind": "FUEL_DELIVERY", "body": "Fuel delivery of 300 L received, ticket KIS-DT-0001.",
        "occurred_at": "2026-11-01T00:30:00Z", "unit": "L", "quantity": "300", "source_document_sha256": TICKET,
        "asset_id": TANK, **over})


def dip(**over) -> dict:
    return oprec("kisiwa-kis-dip-n4-0700", **{
        "kind": "TANK_DIP", "body": "Tank dip at the 07:00 round: 706 L.", "occurred_at": "2026-11-01T00:40:00Z",
        "unit": "L", "quantity": "706", "asset_id": TANK, **over})


def refused(code: str, body: dict, store: FakeStore | None = None) -> None:
    with pytest.raises(WorkRefused) as caught:
        post(body, store)
    assert caught.value.code == code, caught.value.code
    assert caught.value.status == (409 if code == "WORK_EVENT_DUPLICATE_KEY" else 422)
    if code in MESSAGES:
        assert caught.value.message == MESSAGES[code]


def without(body: dict, key: str) -> dict:
    return {k: v for k, v in body.items() if k != key}


# --- byte-equal existing kinds ---------------------------------------------------------------------------------


def test_operator_log_hash_equals_main_pin() -> None:
    body = oprec(occurred_at="2026-11-01T00:55:00Z")
    (status, response), store = post(body)
    assert status == 201
    assert response == {"schema_version": "operational-record-1", "id": "00000000-0000-4000-8000-0000000000aa",
                        "canonical_record_id": "00000000-0000-4000-8000-0000000000aa", "public_code": "REC-000001",
                        "state": "SUBMITTED", "recorded_at": "2026-11-01T01:00:00.000000Z"}
    row = store.tx.rows[body["idempotency_key"]]
    assert row["payload_sha256"] == OPERATOR_LOG_SHA
    assert row["asset_id"] is None


def test_kind_tuples() -> None:
    assert svc_module.FUEL_KINDS == fr.FUEL_KINDS == ("FUEL_DELIVERY", "TANK_DIP")
    assert svc_module.OPERATIONAL_KINDS[:4] == ("OPERATOR_LOG", "MANUAL_READING", "SHIFT_NOTE", "SITE_VISIT")
    assert svc_module.OPERATIONAL_OPTIONAL == svc_module.OPERATIONAL_CORRECTION + ("asset_id",)
    for code, message in MESSAGES.items():
        assert m.MESSAGES[code] == message and m.STATUS[code] == 422


# --- positive ------------------------------------------------------------------------------------------------


def test_delivery_and_dip_accepted_with_tank() -> None:
    for body in (delivery(), dip(), dip(quantity="0")):
        (status, response), store = post(body)
        assert status == 201 and response["schema_version"] == "operational-record-1"
        assert set(response) == {"schema_version", "id", "canonical_record_id", "public_code", "state", "recorded_at"}
        row = store.tx.rows[body["idempotency_key"]]
        assert row["asset_id"] == TANK and row["kind"] == body["kind"]


def test_fuel_hash_carries_the_tank() -> None:
    (_, _), one = post(delivery())
    (_, _), two = post(delivery(asset_id=TANK.upper()))  # the canonical UUID text: same hash
    other_tank = "00000000-0000-4000-8000-0000000000f3"
    (_, _), three = post(delivery(asset_id=other_tank), FakeStore({other_tank: "FUEL_TANK"}))
    key = "kisiwa-kis-delivery-1"
    assert one.tx.rows[key]["payload_sha256"] == two.tx.rows[key]["payload_sha256"]
    assert one.tx.rows[key]["payload_sha256"] != three.tx.rows[key]["payload_sha256"]


# --- refusals, in the card's order ------------------------------------------------------------------------------


def test_step_one_unchanged_comes_first() -> None:
    refused("WORK_INPUT_INVALID", delivery(kind="FUEL_REFILL"))
    refused("WORK_INPUT_INVALID", without(delivery(), "asset_id") | {"quantity": "300", "unit": None})
    refused("WORK_INPUT_INVALID", dip(quantity="-1"))  # decimal shape is step 1


def test_asset_required() -> None:
    refused("WORK_RECORD_ASSET_REQUIRED", without(delivery(), "asset_id"))
    refused("WORK_RECORD_ASSET_REQUIRED", dip(asset_id=None))
    # before period_end, quantity, ticket and UUID checks
    refused("WORK_RECORD_ASSET_REQUIRED", dip(asset_id=None, period_end="2026-11-01T00:50:00Z", quantity=None,
                                             unit=None))


def test_asset_not_allowed_on_other_kinds() -> None:
    refused("WORK_RECORD_ASSET_NOT_ALLOWED", oprec(kind="SITE_VISIT", asset_id=TANK))
    refused("WORK_RECORD_ASSET_NOT_ALLOWED", oprec(kind="SITE_VISIT", asset_id=None))
    refused("WORK_RECORD_ASSET_NOT_ALLOWED", oprec(asset_id="not-a-uuid"))


def test_period_end_before_quantity() -> None:
    refused("WORK_INPUT_INVALID", dip(period_end="2026-11-01T00:50:00Z"))
    refused("WORK_INPUT_INVALID", delivery(period_end="2026-11-01T00:50:00Z", quantity="0"))


def test_quantity_invalid() -> None:
    refused("WORK_RECORD_QUANTITY_INVALID", dip(quantity=None, unit=None))
    refused("WORK_RECORD_QUANTITY_INVALID", dip(unit="l"))
    refused("WORK_RECORD_QUANTITY_INVALID", delivery(unit="kg"))
    refused("WORK_RECORD_QUANTITY_INVALID", delivery(quantity="0"))
    refused("WORK_RECORD_QUANTITY_INVALID", delivery(quantity="0", source_document_sha256=None))  # before ticket


def test_ticket_required() -> None:
    refused("WORK_RECORD_TICKET_REQUIRED", delivery(source_document_sha256=None))
    refused("WORK_RECORD_TICKET_REQUIRED", delivery(source_document_sha256=None, asset_id="not-a-uuid"))  # before UUID


def test_asset_not_a_uuid() -> None:
    refused("WORK_INPUT_INVALID", dip(asset_id="not-a-uuid"))
    refused("WORK_INPUT_INVALID", dip(asset_id=7))


def test_in_transaction_asset_scope_then_type() -> None:
    refused("WORK_LINK_SCOPE_INVALID", dip(asset_id="00000000-0000-4000-8000-0000000000ff"))
    refused("WORK_RECORD_ASSET_NOT_TANK", dip(asset_id=GENERATOR))


def test_retry_and_duplicate_key() -> None:
    store = FakeStore()
    (status, _), _ = post(dip(), store)
    assert status == 201
    (status, _), _ = post(dip(), store)
    assert status == 200
    refused("WORK_EVENT_DUPLICATE_KEY", dip(quantity="705"), store)


# --- the read's window arguments ---------------------------------------------------------------------------------


def test_fuel_records_window_arguments() -> None:
    lo = datetime(2026, 10, 3, 18, 0, tzinfo=timezone.utc)
    hi = lo + timedelta(hours=18)
    fr.check_window(lo, hi, hi)
    fr.check_window(lo, hi, lo - timedelta(days=1))  # known_at is not capped or ordered against the window
    naive = datetime(2026, 10, 3, 18, 0)
    offset = datetime(2026, 10, 3, 21, 0, tzinfo=timezone(timedelta(hours=3)))
    for args in ((hi, lo, hi), (lo, lo, hi), (naive, hi, hi), (lo, naive, hi), (lo, hi, naive), (offset, hi, hi),
                 (lo, hi, "2026-10-04T12:00:00Z")):
        with pytest.raises(ValueError, match="^fuel_records needs UTC instants with lo < hi$"):
            fr.check_window(*args)


def test_fuel_record_shape() -> None:
    assert [f for f in fr.FuelRecord.__dataclass_fields__] == [
        "root_id", "head_id", "code", "kind", "occurred_at", "recorded_at", "root_recorded_at", "quantity_l",
        "ticket_sha256", "actor_id", "body"]
    assert fr.FuelRecord.__dataclass_params__.frozen
