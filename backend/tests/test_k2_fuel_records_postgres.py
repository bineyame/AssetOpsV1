"""DIESEL-K2 L2 (`.agent/build-sheet-DIESEL-1.md` §9c.2): fuel delivery and tank dip records over real Postgres.

Kobo is imported through `test_s1_bindings_postgres.imported`; its `fuel-tank` asset is `FUEL_TANK`. The work store runs
on a `VirtualDbClock` (W401), so every command's `recorded_at` is known. Requires ASSETOPS_TEST_DATABASE_URL naming a
`*_test` database.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

MIGRATION, PREVIOUS = "0054_operational_fuel_records", "0053_fuel_cost_2"
REFUSED = "0054 downgrade requires no FUEL_DELIVERY or TANK_DIP operational records"
T0 = datetime(2026, 10, 20, 0, 0, tzinfo=timezone.utc)  # the virtual DB clock: command n is recorded at T0 + n s
LO = datetime(2026, 10, 10, 6, 0, tzinfo=timezone.utc)
HI = LO + timedelta(days=1)
TICKET = "ab" * 32
WINDOW = {"from": "2026-10-09T00:00:00Z", "to": "2026-10-21T00:00:00Z"}

if URL:
    import pg_harness
    from pg_harness import alembic_head
    from sqlalchemy import text
    from sqlalchemy.exc import IntegrityError
    from test_s1_bindings_postgres import _alembic, engine, imported, store  # noqa: F401
    from test_w203_cold_migration_postgres import head
    from test_w401_work_service_postgres import PRINCIPAL, VirtualDbClock, oprec
    from test_w601e_operational_index import Api, key  # noqa: F401

    from assetops_backend.evidence.composition import build_link_rows_reader
    from assetops_backend.work.adapters.postgres_fuel_records import PostgresFuelRecords, select_fuel_records
    from assetops_backend.work.adapters.postgres_work_store import PostgresWorkStore
    from assetops_backend.work.model import WorkRefused
    from assetops_backend.work.service import WorkService


def iso(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


class Kobo:
    """KOBO-001 (and a foreign KOBO-002) imported; a clocked work service; the tank and generator asset IDs."""

    def __init__(self, store, engine) -> None:  # noqa: F811
        result = imported(store)
        other = imported(store, code="KOBO-002")
        self.t, self.s, self.engine = result.tenant.id, result.site.id, engine
        self.assets = self._assets(result.site.id)
        self.foreign_tank = self._assets(other.site.id)["fuel-tank"]
        assert self.type_of(self.assets["fuel-tank"]) == "FUEL_TANK"
        self.tank, self.generator = self.assets["fuel-tank"], self.assets["generator"]
        self.clock = VirtualDbClock(T0)
        self.work = PostgresWorkStore(URL, link_rows=build_link_rows_reader(), test_db_clock_override=self.clock)
        self.svc = WorkService(self.work)
        self.read = PostgresFuelRecords(URL)

    def _assets(self, site_id) -> dict[str, str]:
        with self.engine.connect() as c:
            return {code: str(i) for code, i in c.execute(text(
                "SELECT asset_code, id FROM asset WHERE site_id = :s"), {"s": site_id})}

    def type_of(self, asset_id: str) -> str:
        with self.engine.connect() as c:
            return c.execute(text("SELECT asset_type FROM asset WHERE id = :a"), {"a": asset_id}).scalar_one()

    def post(self, body: dict):
        return self.svc.post_operational_record(self.t, self.s, body, PRINCIPAL)

    def row(self, key: str) -> dict:
        with self.engine.connect() as c:
            return dict(c.execute(text("SELECT * FROM operational_record WHERE idempotency_key = :k"),
                                  {"k": key}).one()._mapping)

    def fuel(self, known_at: datetime, lo: datetime = LO, hi: datetime = HI):
        return self.read.fuel_records(self.t, self.s, UUID(self.tank), lo, hi, known_at)

    def close(self) -> None:
        self.work.dispose()
        self.read.dispose()


@pytest.fixture()
def kobo(store, engine):  # noqa: F811
    owned = Kobo(store, engine)
    yield owned
    owned.close()


def dip(kobo, key: str, occurred: datetime, quantity: str = "706", **over) -> dict:
    return oprec(key, **{"kind": "TANK_DIP", "body": f"Tank dip at the 07:00 round: {quantity} L.",
                         "occurred_at": iso(occurred), "unit": "L", "quantity": quantity, "asset_id": kobo.tank,
                         **over})


def delivery(kobo, key: str, occurred: datetime, **over) -> dict:
    return oprec(key, **{"kind": "FUEL_DELIVERY", "body": "Fuel delivery of 300 L received, ticket KIS-DT-0001.",
                         "occurred_at": iso(occurred), "unit": "L", "quantity": "300",
                         "source_document_sha256": TICKET, "asset_id": kobo.tank, **over})


def refused(code: str, call, *args) -> WorkRefused:
    with pytest.raises(WorkRefused) as caught:
        call(*args)
    assert caught.value.code == code, caught.value.code
    return caught.value


def constraint_defs(engine) -> dict[str, str]:  # noqa: F811
    with engine.connect() as c:
        return dict(c.execute(text("SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint "
                                   "WHERE conrelid = 'operational_record'::regclass")).all())


def shape(engine) -> tuple:  # noqa: F811
    with engine.connect() as c:
        cols = set(c.execute(text("SELECT column_name FROM information_schema.columns "
                                  "WHERE table_name = 'operational_record'")).scalars())
        indexes = set(c.execute(text("SELECT indexname FROM pg_indexes WHERE tablename = 'operational_record'")).scalars())
    return cols, indexes, constraint_defs(engine)


# --- migration ----------------------------------------------------------------------------------------------------


def test_single_alembic_head(engine) -> None:  # noqa: F811
    from alembic.script import ScriptDirectory

    script = ScriptDirectory.from_config(_alembic())
    # DIESEL-K3: 0055 follows 0054, so the single head is the repository head, no longer 0054 itself.
    assert script.get_heads() == [alembic_head()] and head(engine) == alembic_head()
    assert script.get_revision(MIGRATION).down_revision == PREVIOUS


def test_migration_up_down_up_on_empty_table(store, engine) -> None:  # noqa: F811
    from alembic import command

    pg_harness.dispose(store)  # `store` emptied the tables; release its pool before the DDL lock
    up = shape(engine)
    cols, indexes, defs = up
    assert "asset_id" in cols and "operational_record_asset" in indexes
    assert "'FUEL_DELIVERY'::text" in defs["operational_record_kind_check"]
    assert defs["operational_record_asset_fk"] == ("FOREIGN KEY (tenant_id, site_id, asset_id) "
                                                   "REFERENCES asset(tenant_id, site_id, id)")
    assert {"operational_record_fuel_asset", "operational_record_fuel_quantity",
            "operational_record_delivery_ticket"} <= set(defs)
    config = _alembic()
    engine.dispose()
    try:
        command.downgrade(config, PREVIOUS)
        assert head(engine) == PREVIOUS
        cols_down, indexes_down, defs_down = shape(engine)
        assert cols - cols_down == {"asset_id"} and indexes - indexes_down == {"operational_record_asset"}
        assert set(defs) - set(defs_down) == {"operational_record_asset_fk", "operational_record_fuel_asset",
                                              "operational_record_fuel_quantity", "operational_record_delivery_ticket"}
        assert defs_down["operational_record_kind_check"] == (
            "CHECK ((kind = ANY (ARRAY['OPERATOR_LOG'::text, 'MANUAL_READING'::text, 'SHIFT_NOTE'::text, "
            "'SITE_VISIT'::text])))")
        command.upgrade(config, "head")
    finally:
        if head(engine) != alembic_head():
            command.upgrade(config, "head")
    assert shape(engine) == up


def test_downgrade_refused_with_a_fuel_row(kobo, engine) -> None:  # noqa: F811
    from alembic import command

    assert kobo.post(dip(kobo, "k2-down-dip-001", LO))[0] == 201
    kobo.close()
    config = _alembic()
    engine.dispose()
    try:
        with pytest.raises(RuntimeError, match=REFUSED):
            command.downgrade(config, PREVIOUS)
    finally:
        if head(engine) != alembic_head():
            command.upgrade(config, "head")
    assert head(engine) == alembic_head() and kobo.row("k2-down-dip-001")["asset_id"] is not None


# --- the command ----------------------------------------------------------------------------------------------------


def test_post_delivery_and_dip(kobo) -> None:
    for body in (delivery(kobo, "kisiwa-kis-delivery-1", LO), dip(kobo, "kisiwa-kis-dip-n4-0700", LO)):
        status, response = kobo.post(body)
        assert status == 201
        assert set(response) == {"schema_version", "id", "canonical_record_id", "public_code", "state", "recorded_at"}
        assert response["schema_version"] == "operational-record-1" and response["public_code"].startswith("REC-")
        row = kobo.row(body["idempotency_key"])
        assert str(row["asset_id"]) == kobo.tank and row["kind"] == body["kind"] and row["unit"] == "L"
        # identical retry: 200 with the stored body; a different body under the same key: 409
        assert kobo.post(body) == (200, response)
        error = refused("WORK_EVENT_DUPLICATE_KEY", kobo.post, {**body, "quantity": "301"})
        assert error.status == 409
    # an existing kind still stores a NULL asset
    assert kobo.post(oprec("k2-log-0001", occurred_at=iso(LO)))[0] == 201
    assert kobo.row("k2-log-0001")["asset_id"] is None


def test_asset_scope_and_type(kobo) -> None:
    assert refused("WORK_RECORD_ASSET_NOT_TANK", kobo.post, dip(kobo, "k2-gen-0001", LO, asset_id=kobo.generator)
                   ).message == "The named asset is not a fuel tank at this Site."
    refused("WORK_LINK_SCOPE_INVALID", kobo.post, dip(kobo, "k2-unk-0001", LO, asset_id=str(uuid4())))
    refused("WORK_LINK_SCOPE_INVALID", kobo.post, dip(kobo, "k2-for-0001", LO, asset_id=kobo.foreign_tank))
    with kobo.engine.connect() as c:
        assert c.execute(text("SELECT count(*) FROM operational_record")).scalar_one() == 0


def test_checks_hold_below_the_service(kobo, engine) -> None:  # noqa: F811
    sql = ("INSERT INTO operational_record (id, tenant_id, site_id, public_no, public_code, canonical_record_id, kind, "
           "body, unit, quantity, source_document_sha256, state, occurred_at, actor_id, actor_kind, "
           "authorization_basis, attestation, idempotency_key, payload_sha256, asset_id) VALUES (:i, :t, :s, "
           "nextval('work_public_no_seq'), :code, :i, :k, 'Raw', :u, CAST(:q AS numeric), :d, 'SUBMITTED', :o, "
           "'service:w401-fixture', 'SERVICE', 'SITE_WORK_WRITE', 'service=a;job=b;rule=c', :key, :h, :a)")

    def insert(match: str, **p) -> None:
        i = uuid4()
        params = {"i": i, "t": kobo.t, "s": kobo.s, "code": f"REC-9{int(i.hex[:8], 16) % 100000:05d}", "k": "TANK_DIP", "u": "L", "q": "5",
                  "d": None, "o": LO, "key": f"raw-{i.hex[:12]}", "h": "a" * 64, "a": kobo.tank, **p}
        with pytest.raises(IntegrityError, match=match):
            with engine.begin() as c:
                c.execute(text(sql), params)

    insert("operational_record_fuel_asset", a=None)
    insert("operational_record_fuel_asset", k="OPERATOR_LOG", u=None, q=None)
    insert("operational_record_fuel_quantity", u="kg")
    insert("operational_record_delivery_ticket", k="FUEL_DELIVERY", d=TICKET, q="0")
    insert("operational_record_delivery_ticket", k="FUEL_DELIVERY", d=None)
    insert("operational_record_asset_fk", a=kobo.foreign_tank)


# --- the as-known read --------------------------------------------------------------------------------------------


def test_fuel_records_as_known(kobo, engine) -> None:  # noqa: F811
    at = lambda n: T0 + timedelta(seconds=n)  # noqa: E731 - the recorded_at of command n
    a = kobo.post(dip(kobo, "k2-read-dip-lo", LO))[1]                                    # T0+0, lo edge (in)
    b = kobo.post(dip(kobo, "k2-read-dip-hi", HI))[1]                                    # T0+1, hi edge (out)
    kobo.post(dip(kobo, "k2-read-dip-early", LO - timedelta(seconds=1)))                 # T0+2, before lo (out)
    d = kobo.post(delivery(kobo, "k2-read-delivery", LO + timedelta(hours=6)))[1]        # T0+3
    kobo.post(oprec("k2-read-log-0001", occurred_at=iso(LO + timedelta(hours=6))))      # T0+4, never a fuel record
    assert kobo.clock.returned == [at(n) for n in range(5)]

    # known_at before the delivery was recorded: only the dip; at T0+4 both, ordered by occurrence
    assert [r.code for r in kobo.fuel(at(0))] == [a["public_code"]]
    rows = kobo.fuel(at(4))
    assert [(r.code, r.kind) for r in rows] == [(a["public_code"], "TANK_DIP"), (d["public_code"], "FUEL_DELIVERY")]
    first, second = rows
    assert first.root_id == first.head_id == a["id"] and first.quantity_l == Decimal("706")
    assert first.occurred_at == LO and first.recorded_at == first.root_recorded_at == at(0)
    assert first.ticket_sha256 is None and first.actor_id == PRINCIPAL and first.body.startswith("Tank dip")
    assert second.ticket_sha256 == TICKET and second.quantity_l == Decimal("300")
    assert kobo.fuel(at(0), lo=at(0) - timedelta(days=30), hi=LO) == ()  # hi is exclusive of the lo-edge dip

    # a correction of the dip (new quantity, recorded later): the head after its recorded_at, the root before it
    fix = kobo.post(dip(kobo, "k2-read-dip-lo-fix", LO, quantity="650", supersedes_record_id=a["id"],
                        canonical_record_id=a["id"], correction_reason="Dip re-read at the tank"))[1]   # T0+5
    before, after = kobo.fuel(at(4))[0], kobo.fuel(at(5))[0]
    assert before.head_id == a["id"] and before.quantity_l == Decimal("706")
    assert after.root_id == a["id"] and after.head_id == fix["id"] and after.quantity_l == Decimal("650")
    assert after.code == a["public_code"] and after.recorded_at == at(5) and after.root_recorded_at == at(0)

    # a correction that moves the delivery's occurrence out of the window drops it from the window
    kobo.post(delivery(kobo, "k2-read-delivery-fix", HI + timedelta(hours=1), supersedes_record_id=d["id"],
                       canonical_record_id=d["id"], correction_reason="Delivered the next morning"))  # T0+6
    assert [r.root_id for r in kobo.fuel(at(5))] == [a["id"], d["id"]]
    assert [r.root_id for r in kobo.fuel(at(6))] == [a["id"]]
    # the moved delivery now belongs to the next window, after the hi-edge dip
    assert [r.root_id for r in kobo.fuel(at(6), lo=HI, hi=HI + timedelta(days=1))] == [b["id"], d["id"]]

    # the caller-connection form reads the same, inside the caller's transaction
    with engine.connect() as c:
        assert select_fuel_records(c, kobo.t, kobo.s, UUID(kobo.tank), LO, HI, at(6)) == kobo.fuel(at(6))
    with pytest.raises(ValueError, match="fuel_records needs UTC instants with lo < hi"):
        kobo.fuel(at(6), lo=HI, hi=LO)


def test_global_operational_records_list(kobo, key) -> None:  # noqa: F811
    kobo.post(dip(kobo, "k2-list-dip-0001", LO))
    kobo.post(delivery(kobo, "k2-list-delivery-1", LO + timedelta(hours=1)))
    kobo.post(oprec("k2-list-log-0001", occurred_at=iso(LO + timedelta(hours=2))))
    api = Api(str(kobo.t), T0 + timedelta(hours=1))
    try:
        body = api.ok(window=WINDOW)
        assert sorted(r["kind"] for r in body["rows"]) == ["FUEL_DELIVERY", "OPERATOR_LOG", "TANK_DIP"]
        assert body["total_count"] == 3
        fuel = api.get(window=WINDOW, kind="FUEL_DELIVERY")
        bogus = api.get(window=WINDOW, kind="NOT_A_KIND")
        assert fuel.status_code == bogus.status_code == 422
        assert fuel.json() == bogus.json()
    finally:
        api.close()
