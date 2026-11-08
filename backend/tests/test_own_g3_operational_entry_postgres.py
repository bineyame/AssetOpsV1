"""OWN-G3a Postgres (build sheet OWN-GAPS-2026-11-08 §3.5, R2-G3a): `POST /api/sites/{code}/work/operational-entries`
through `create_app` with the entry principal, on KOBO-001 (one active `FUEL_TANK`, `Africa/Addis_Ababa`), with the
real DB clock. Requires ASSETOPS_TEST_DATABASE_URL naming a `*_test` database."""

from __future__ import annotations

import hashlib
import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID
from zoneinfo import ZoneInfo

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

CODE = "KOBO-001"
ZONE = ZoneInfo("Africa/Addis_Ababa")
PATH = f"/api/sites/{CODE}/work/operational-entries"
PRINCIPAL = "service:operator-entry"
ATTESTATION = "service=operator-entry;job=site-admin-entry;rule=oprec-entry/1"

if URL:
    from fastapi.testclient import TestClient
    from sqlalchemy import text
    from test_s1_bindings_postgres import _alembic, engine, imported, store  # noqa: F401

    from assetops_backend.config import load_feature_flags
    from assetops_backend.main import create_app
    from assetops_backend.work.composition import build_fuel_records_reader


def key(n: int) -> str:
    return f"oprec-entry-{n:032x}"


class Kobo:
    def __init__(self, store, engine, monkeypatch, *, principal: bool = True) -> None:  # noqa: F811
        result = imported(store)
        self.t, self.s, self.engine = result.tenant.id, result.site.id, engine
        with engine.connect() as c:
            self.tank = str(c.execute(text("SELECT id FROM asset WHERE site_id = :s AND asset_type = 'FUEL_TANK'"),
                                      {"s": self.s}).scalar_one())
        monkeypatch.setenv("DATABASE_URL", URL)
        extra = {"operational_entry_principal": (lambda r, c: PRINCIPAL)} if principal else {}
        self.api = TestClient(create_app(load_feature_flags(), **extra))

    def db_now(self) -> datetime:
        with self.engine.connect() as c:
            return c.execute(text("SELECT clock_timestamp()")).scalar_one().astimezone(timezone.utc)

    def local(self, delta: timedelta = timedelta(hours=-1)) -> str:
        return (self.db_now() + delta).astimezone(ZONE).strftime("%Y-%m-%dT%H:%M")

    def post(self, n: int, **over):
        body = {"entry": "TANK_DIP", "value": "706", "taken_at_local": self.local(), "ticket_reference": None,
                "idempotency_key": key(n)}
        body.update(over)
        return self.api.post(PATH, json=body)

    def rows(self) -> list[dict]:
        with self.engine.connect() as c:
            return [dict(r._mapping) for r in c.execute(text(
                "SELECT * FROM operational_record WHERE site_id = :s ORDER BY recorded_at"), {"s": self.s})]


@pytest.fixture()
def kobo(store, engine, monkeypatch):  # noqa: F811
    owned = Kobo(store, engine, monkeypatch)
    yield owned
    owned.api.close()


def test_saved_then_identical_retry_returns_the_stored_body(kobo) -> None:
    taken = kobo.local()
    first = kobo.post(1, taken_at_local=taken)
    assert first.status_code == 201, first.text
    again = kobo.post(1, taken_at_local=taken)
    assert (again.status_code, again.json()) == (200, first.json())
    assert first.json()["public_code"].startswith("REC-") and first.json()["state"] == "SUBMITTED"
    assert len(kobo.rows()) == 1


def test_the_same_key_with_another_value_is_a_duplicate(kobo) -> None:
    taken = kobo.local()
    assert kobo.post(2, taken_at_local=taken).status_code == 201
    other = kobo.post(2, taken_at_local=taken, value="707")
    assert (other.status_code, other.json()["detail"]["code"]) == (409, "WORK_EVENT_DUPLICATE_KEY")
    assert len(kobo.rows()) == 1


def test_the_stored_row_carries_the_server_identity_and_audit_columns(kobo) -> None:
    before = kobo.db_now()
    taken = kobo.local()
    response = kobo.post(3, taken_at_local=taken, value="198.50")
    after = kobo.db_now()
    assert response.status_code == 201, response.text
    [row] = kobo.rows()
    assert (row["actor_kind"], row["actor_id"], row["attestation"], row["authorization_basis"]) == (
        "SERVICE", PRINCIPAL, ATTESTATION, "SITE_WORK_WRITE:" + PRINCIPAL)
    assert row["public_code"] == response.json()["public_code"] and row["public_code"].startswith("REC-")
    assert len(row["payload_sha256"]) == 64 and row["idempotency_key"] == key(3)
    assert before <= row["recorded_at"] <= after  # the DB's command time, not the host clock
    assert (row["kind"], row["unit"], str(row["asset_id"]), row["state"]) == ("TANK_DIP", "L", kobo.tank, "SUBMITTED")
    assert row["body"] == f"Tank dip at the {taken[11:]} round: 198.5 L."
    occurred = datetime.strptime(taken, "%Y-%m-%dT%H:%M").replace(tzinfo=ZONE).astimezone(timezone.utc)
    assert row["occurred_at"] == occurred


def test_a_delivery_is_stored_with_its_ticket_digest(kobo) -> None:
    response = kobo.post(4, entry="FUEL_DELIVERY", value="300", ticket_reference="KIS-DT-0002")
    assert response.status_code == 201, response.text
    [row] = kobo.rows()
    assert row["source_document_sha256"] == hashlib.sha256(b"Fuel delivery ticket KIS-DT-0002, 300 L").hexdigest()
    assert (row["kind"], str(row["asset_id"])) == ("FUEL_DELIVERY", kobo.tank)


def test_too_old_and_future_entries_are_refused_with_zero_rows(kobo) -> None:
    old = kobo.post(5, taken_at_local=kobo.local(timedelta(days=-31)))
    ahead = kobo.post(6, taken_at_local=kobo.local(timedelta(minutes=10)))
    assert (old.status_code, old.json()["detail"]["code"]) == (422, "WORK_OCCURRED_AT_TOO_OLD")
    assert (ahead.status_code, ahead.json()["detail"]["code"]) == (422, "WORK_OCCURRED_AT_FUTURE")
    assert kobo.rows() == []


def test_an_app_with_no_entry_principal_is_403_with_zero_rows(store, engine, monkeypatch) -> None:  # noqa: F811
    off = Kobo(store, engine, monkeypatch, principal=False)
    try:
        response = off.post(7)
        assert (response.status_code, response.json()["detail"]["code"]) == (403, "WORK_WRITE_FORBIDDEN")
        assert off.rows() == []
    finally:
        off.api.close()


def test_a_saved_dip_is_read_by_the_fuel_balance_records_reader(kobo) -> None:
    taken = kobo.local()
    assert kobo.post(8, taken_at_local=taken, value="512").status_code == 201
    occurred = datetime.strptime(taken, "%Y-%m-%dT%H:%M").replace(tzinfo=ZONE).astimezone(timezone.utc)
    read = build_fuel_records_reader()
    with kobo.engine.connect() as c:
        records = read(c, kobo.t, kobo.s, UUID(kobo.tank), occurred - timedelta(hours=1),
                       occurred + timedelta(hours=1), kobo.db_now())
    [record] = records
    assert (record.kind, record.occurred_at, record.quantity_l) == ("TANK_DIP", occurred, Decimal("512"))


def test_manual_readings_are_stored_with_their_unit_and_no_asset(kobo) -> None:
    assert kobo.post(9, entry="STOCK_IN_CHAMBER", value="40").status_code == 201
    assert kobo.post(10, entry="METER_READING", value="1520").status_code == 201
    rows = kobo.rows()
    assert [(r["kind"], r["unit"], Decimal(str(r["quantity"])), r["asset_id"]) for r in rows] == [
        ("MANUAL_READING", "kg", Decimal("40"), None), ("MANUAL_READING", "kWh", Decimal("1520"), None)]
    assert [r["body"] for r in rows] == ["Stock in chamber: 40 kg.", "Meter reading: 1520 kWh."]
