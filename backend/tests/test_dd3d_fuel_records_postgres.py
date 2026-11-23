"""DD3d-a (D-DD.154 as amended by D-DD.168): `load_fuel_records` over real Postgres.

Lakeside is onboarded by the real `onboard_operator apply` in a fresh clone; one Site's `fuel-records.json` (Kobo: five
dips, three deliveries, OOO-1's recorded nine days late) is loaded through the product's operational path, each record
at its own record time. Requires ASSETOPS_TEST_DATABASE_URL on a routed run (`tools/run-host-tests.ps1`).
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from uuid import UUID

import pytest

import pg_harness

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import create_engine, text

    from assetops_backend import load_fuel_records as command
    from assetops_backend import onboard_operator
    from assetops_backend.database_target import PG_TARGET_ENV
    from assetops_backend.fuel_balance.composition import build_fuel_balance_store
    from assetops_backend.fuel_balance.service import FuelBalanceService

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND.parent / "tools"))
import dd_check  # noqa: E402
LAKESIDE = BACKEND / "tests" / "fixtures" / "on1" / "lakeside-power.onboarding.json"
WORLD = BACKEND / "conversions" / "world"
SLUG, CODE = "lakeside-power", "KOBO-001"
EAT = timezone(timedelta(hours=3))
LATE = "2026-11-04T10:00:00+03:00"


def _dip(day: str, litres: str) -> dict:
    return {"source_record_id": f"{CODE}:dip:{day}", "kind": "TANK_DIP", "taken_at_local": f"{day}T00:00",
            "litres": litres, "ticket_reference": None, "recorded_at": f"{day}T00:00:00+03:00"}


def _delivery(rid: str, day: str, k: int, recorded: str | None = None) -> dict:
    return {"source_record_id": rid, "kind": "FUEL_DELIVERY", "taken_at_local": f"{day}T10:00", "litres": "400",
            "ticket_reference": f"FN-{CODE}-{day.replace('-', '')}-{k}",
            "recorded_at": recorded or f"{day}T10:00:00+03:00"}


RECORDS = [_dip("2026-07-01", "1250.000"), _dip("2026-08-01", "1238.000"), _dip("2026-09-01", "1226.000"),
           _delivery("lakeside-power:KOBO-001:2026-09:actual:fuel-1", "2026-09-25", 1),
           _delivery("lakeside-power:KOBO-001:2026-09:actual:fuel-2", "2026-09-25", 2),
           _dip("2026-10-01", "1252.75"), _dip("2026-11-01", "1018.125"),
           _delivery("lakeside-power:KOBO-001:2026-10:actual:fuel-1", "2026-10-26", 1, LATE)]


def _write(root: Path, records=None, *, schema="assetops.world-fuel-records/1", tenant=SLUG, code=CODE) -> Path:
    (root / SLUG).mkdir(parents=True, exist_ok=True)
    document = {"schema": schema, "tenant": tenant,
                "sites": [{"site_code": code, "records": RECORDS if records is None else records}]}
    (root / SLUG / "fuel-records.json").write_text(json.dumps(document), encoding="utf-8")
    return root


@pytest.fixture(scope="module")
def onboarded(tmp_path_factory):
    """A clone with Lakeside's `/2` file applied; every test works on it, in file order."""
    patch = pytest.MonkeyPatch()
    url = pg_harness.clone_database("dd3drec")
    keys = tmp_path_factory.mktemp("keys")
    os.chmod(keys, 0o700)
    try:
        for variable in PG_TARGET_ENV:
            patch.delenv(variable, raising=False)
        patch.delenv("ASSETOPS_REAL_OPERATOR_DATA", raising=False)
        patch.setenv("DATABASE_URL", url)
        patch.setenv("ASSETOPS_TENANT_SLUG", SLUG)
        patch.setenv("ASSETOPS_PSEUDONYM_KEY_DIR", str(keys))
        from contextlib import redirect_stdout
        from io import StringIO

        out = StringIO()
        with redirect_stdout(out):
            onboard_operator.main(["digest", "--file", str(LAKESIDE)])
            assert onboard_operator.main(["apply", "--file", str(LAKESIDE), "--confirmed-digest",
                                          out.getvalue().strip(), "--bindings", str(WORLD)]) == 0
        yield url
    finally:
        patch.undo()
        pg_harness.drop_database(url)


def _query(url: str, sql: str, **params) -> list[dict]:
    engine = create_engine(url)
    try:
        with engine.connect() as c:
            return [dict(r._mapping) for r in c.execute(text(sql), params)]
    finally:
        pg_harness.dispose(engine)


def _count(url: str) -> int:
    return _query(url, "SELECT count(*) AS n FROM operational_record")[0]["n"]


def _run(capsys, *argv: str) -> tuple[int, str, str]:
    capsys.readouterr()
    code = command.main(list(argv))
    out, err = capsys.readouterr()
    return code, out.strip(), err.strip()


@pytest.mark.parametrize("database", ["assetops", "assetops_op_lakeside", "assetops_op_x_test", "ASSETOPS_OP_x_test"])
def test_a_database_outside_the_guard_refuses_with_nothing_written(onboarded, tmp_path, monkeypatch, capsys,
                                                                   database) -> None:
    from assetops_backend.work import composition

    def no_store(*_a, **_k):
        raise AssertionError("a refused load must not build a store")

    monkeypatch.setattr(composition, "build_work_store", no_store)
    monkeypatch.setenv("DATABASE_URL", f"postgresql+psycopg://u:p@127.0.0.1:1/{database}")
    code, out, err = _run(capsys, "--dir", str(_write(tmp_path)), "--tenant", SLUG)
    assert (code, out) == (2, "") and err.startswith("PREPARE_CLOCK_REFUSED")
    assert _count(onboarded) == 0


@pytest.mark.parametrize(("change", "error"), [
    ({"schema": "assetops.world-fuel-records/2"}, "FUEL_RECORDS_FILE - schema assetops.world-fuel-records/2"),
    ({"tenant": "harvest-cold"}, "FUEL_RECORDS_FILE - tenant harvest-cold"),
    ({"code": "NOWHERE-001"}, "FUEL_RECORDS_SITE - NOWHERE-001"),
    ({"code": "COLD-THIKA"}, "FUEL_RECORDS_SITE - COLD-THIKA")])  # another tenant's Site
def test_a_file_that_is_not_this_tenants_refuses_with_nothing_written(onboarded, tmp_path, capsys, change,
                                                                      error) -> None:
    code, out, err = _run(capsys, "--dir", str(_write(tmp_path, **change)), "--tenant", SLUG)
    assert (code, out, err) == (2, "", error)
    assert _count(onboarded) == 0


def test_a_refused_record_exits_2_with_its_code_and_id(onboarded, tmp_path, capsys) -> None:
    bad = {**_delivery("bad-1", "2026-09-25", 1), "ticket_reference": None}
    code, out, err = _run(capsys, "--dir", str(_write(tmp_path, [bad])), "--tenant", SLUG)
    assert (code, out, err) == (2, "", "OPREC_ENTRY_TICKET_REQUIRED bad-1")
    late = {**_dip("2026-07-01", "1"), "recorded_at": "2026-09-01T00:00:00+03:00"}  # past the backdate limit
    code, out, err = _run(capsys, "--dir", str(_write(tmp_path, [late])), "--tenant", SLUG)
    assert (code, out, err) == (2, "", f"WORK_OCCURRED_AT_TOO_OLD {CODE}:dip:2026-07-01")
    assert _count(onboarded) == 0


@pytest.mark.parametrize(("change", "where"), [
    ({"litres": ...}, "bad-1"), ({"kind": ...}, "bad-1"), ({"source_record_id": ...}, "-"), ({"recorded_at": ...}, "bad-1"),
    ({"recorded_at": "yesterday"}, "bad-1"), ({"recorded_at": 3}, "bad-1"), ({"source_record_id": 7}, "-"),
    ({"recorded_at": "2026-09-25T10:00:00"}, "bad-1")])  # a naive instant is never read in the host's zone
def test_a_malformed_record_refuses_with_its_id_and_writes_nothing(onboarded, tmp_path, capsys, change, where) -> None:
    """Review L3: every record is read before the first is written, so the good one before it is not stored."""
    bad = {k: v for k, v in {**_delivery("bad-1", "2026-09-25", 1), **change}.items() if v is not ...}
    code, out, err = _run(capsys, "--dir", str(_write(tmp_path, [RECORDS[0], bad])), "--tenant", SLUG)
    assert (code, out, err) == (2, "", f"FUEL_RECORDS_FILE {where} record")
    assert _count(onboarded) == 0


@pytest.mark.parametrize("sites", [None, {}, [7], [{"records": []}], [{"site_code": CODE}], [{"site_code": CODE, "records": 7}],
                                   [{"site_code": CODE, "records": [7]}]])
def test_a_file_of_another_shape_refuses_with_nothing_written(onboarded, tmp_path, capsys, sites) -> None:
    path = _write(tmp_path) / SLUG / "fuel-records.json"
    path.write_text(json.dumps({"schema": "assetops.world-fuel-records/1", "tenant": SLUG, "sites": sites}), encoding="utf-8")
    code, out, err = _run(capsys, "--dir", str(tmp_path), "--tenant", SLUG)
    assert (code, out) == (2, "") and err.startswith("FUEL_RECORDS_FILE - ")
    path.write_text("[]", encoding="utf-8")
    assert _run(capsys, "--dir", str(tmp_path), "--tenant", SLUG) == (2, "", "FUEL_RECORDS_FILE - shape")
    assert _count(onboarded) == 0


@pytest.mark.parametrize("fails", ["scope", "context", "post"])
def test_an_unavailable_store_exits_2_with_the_record_it_was_at(onboarded, tmp_path, monkeypatch, capsys, fails) -> None:
    from assetops_backend.evidence.adapters.postgres_evidence_ledger import PostgresEvidenceLedger
    from assetops_backend.evidence.ledger import LedgerUnavailable
    from assetops_backend.work.model import WorkStoreUnavailable
    from assetops_backend.work.service import WorkService

    def down(error):
        def raises(*_a, **_k):
            raise error("down")
        return raises

    if fails == "scope":
        monkeypatch.setattr(PostgresEvidenceLedger, "site_scope", down(LedgerUnavailable))
    elif fails == "context":
        monkeypatch.setattr(command, "entry_site_context", lambda read: down(WorkStoreUnavailable))
    else:
        monkeypatch.setattr(WorkService, "post_operational_record", down(WorkStoreUnavailable))
    code, out, err = _run(capsys, "--dir", str(_write(tmp_path)), "--tenant", SLUG)
    assert (code, out, err) == (2, "", f"FUEL_RECORDS_STORE {'-' if fails == 'scope' else RECORDS[0]['source_record_id']}")
    assert _count(onboarded) == 0


def test_one_sites_file_loads_each_record_at_its_own_time(onboarded, tmp_path, capsys) -> None:
    from assetops_backend.work import composition

    saved = composition.build_work_store
    code, out, err = _run(capsys, "--dir", str(_write(tmp_path)), "--tenant", SLUG)
    assert (code, err) == (0, "")
    assert composition.build_work_store is saved  # the clock swap does not outlive the load
    assert json.loads(out) == {"tenant": SLUG, "recorded": 8, "already": 0,
                               "by_kind": {"FUEL_DELIVERY": 3, "TANK_DIP": 5}}
    rows = {r["idempotency_key"]: r for r in _query(onboarded, (
        "SELECT r.*, a.asset_type, t.slug FROM operational_record r JOIN asset a ON a.id = r.asset_id "
        "JOIN tenant t ON t.id = r.tenant_id"))}
    assert len(rows) == len(RECORDS)
    for record in RECORDS:
        row = rows["oprec-entry-" + hashlib.sha256(record["source_record_id"].encode("utf-8")).hexdigest()[:32]]
        assert (row["kind"], Decimal(row["quantity"]), row["unit"], row["asset_type"], row["slug"]) == (
            record["kind"], Decimal(record["litres"]), "L", "FUEL_TANK", SLUG)
        assert row["recorded_at"] == datetime.fromisoformat(record["recorded_at"])
        assert row["occurred_at"] == datetime.fromisoformat(record["taken_at_local"]).replace(tzinfo=EAT)
        assert row["actor_id"] == "service:operator-entry"


def _store_site(url: str) -> tuple[UUID, UUID]:
    [site] = _query(url, "SELECT tenant_id, id FROM site WHERE site_code = :c", c=CODE)
    return site["tenant_id"], site["id"]


def test_the_night_check_reads_each_record_at_its_record_time(onboarded) -> None:
    tenant_id, site_id = _store_site(onboarded)
    store = build_fuel_balance_store(onboarded)
    try:
        def work(tx):
            [tank] = [a for a in tx.active_assets() if a.asset_type == "FUEL_TANK"]
            return tx.fuel_records(tank.id, datetime(2026, 6, 30, tzinfo=timezone.utc),
                                   datetime(2026, 11, 2, tzinfo=timezone.utc))

        read = store.read_at(tenant_id, site_id, datetime(2026, 11, 6, tzinfo=timezone.utc), work)
        before = store.read_at(tenant_id, site_id,
                               datetime.fromisoformat(LATE).astimezone(timezone.utc) - timedelta(minutes=1), work)
    finally:
        store.dispose()
    assert sorted((r.kind, r.occurred_at, r.quantity_l, r.root_recorded_at) for r in read) == sorted(
        (r["kind"], datetime.fromisoformat(r["taken_at_local"]).replace(tzinfo=EAT), Decimal(r["litres"]),
         datetime.fromisoformat(r["recorded_at"])) for r in RECORDS)
    assert len(before) == len(RECORDS) - 1  # OOO-1's note is not yet known


def late_nights(url: str) -> dict[str, bool]:
    """Per delivery night: does the assessed window carry DELIVERY_RECORDED_LATE?"""
    tenant_id, site_id = _store_site(url)
    store = build_fuel_balance_store(url)
    try:
        service = FuelBalanceService(store)
        nights = (date(2026, 9, 24), date(2026, 10, 25))
        return {n.isoformat(): "DELIVERY_RECORDED_LATE" in service.assess_night(tenant_id, site_id, n).window.limitations
                for n in nights}
    finally:
        store.dispose()


def test_only_the_late_notes_night_carries_the_limitation(onboarded) -> None:
    assert late_nights(onboarded) == {"2026-09-24": False, "2026-10-25": True}


def test_the_checker_reads_the_stored_records_at_the_sites_local_minute(onboarded) -> None:
    read = dd_check.stored_fuel_records(onboarded)
    assert sorted((r["tenant"], r["site"], r["kind"], r["taken_at_local"], r["litres"]) for r in read) == sorted(
        (SLUG, CODE, r["kind"], r["taken_at_local"], Decimal(r["litres"])) for r in RECORDS)


def test_the_checker_reads_each_nights_latest_revision_and_c_dd8_fails_without_readings(onboarded) -> None:
    late_nights(onboarded)
    read = dd_check.stored_fuel_nights(onboarded)
    assert [(n, s) for n, s, _ in read[CODE]] == [("2026-09-24", "NOT_ASSESSED"), ("2026-10-25", "NOT_ASSESSED")]
    result = dd_check.check_fuel(dd_check.read_inputs(onboarded))
    assert not result.passed
    assert {"FAIL KOBO-001: no assessed night", "FAIL KISIWA-001: no fuel records", "FAIL MTO-001: no fuel records",
            "FAIL no readings stored: the loader is DD5.1's; the records' balance is not judged"} <= set(result.detail)


def test_a_re_run_records_nothing_new(onboarded, tmp_path, capsys) -> None:
    before = _count(onboarded)
    code, out, err = _run(capsys, "--dir", str(_write(tmp_path)), "--tenant", SLUG)
    assert (code, err) == (0, "")
    assert json.loads(out) == {"tenant": SLUG, "recorded": 0, "already": 8,
                               "by_kind": {"FUEL_DELIVERY": 3, "TANK_DIP": 5}}
    assert _count(onboarded) == before == 8


def test_the_same_id_with_other_litres_refuses(onboarded, tmp_path, capsys) -> None:
    changed = [{**RECORDS[0], "litres": "1251.000"}]
    code, out, err = _run(capsys, "--dir", str(_write(tmp_path, changed)), "--tenant", SLUG)
    assert (code, out) == (2, "") and err.endswith(f" {CODE}:dip:2026-07-01")
    assert _count(onboarded) == 8


@pytest.mark.parametrize(("site_code", "litres"), [("KOBO-001", 50), ("KISIWA-001", 100), ("MTO-001", 20)])
def test_the_declared_accuracy_is_the_floor_from_july(onboarded, site_code, litres) -> None:
    """D-DD.153 through the real Foundation read (review L1): the published Foundation covers July, so the floor is 2a in
    every month July to October, and there is none in June."""
    from assetops_backend.commercial.months import month_bounds
    from assetops_backend.structure.observe.floor import StoreFloorRead

    [site] = _query(onboarded, "SELECT tenant_id, id FROM site WHERE site_code = :c", c=site_code)
    store = build_fuel_balance_store(onboarded)
    now = datetime.now(timezone.utc) + timedelta(hours=1)
    try:
        floors = {m: StoreFloorRead(store).read(site["tenant_id"], site["id"], month_bounds(m, "Africa/Nairobi"), now)
                  for m in ("2026-06", "2026-07", "2026-08", "2026-09", "2026-10")}
    finally:
        store.dispose()
    assert floors.pop("2026-06") is None
    assert {m: (f.litres, f.accuracy_l, f.basis) for m, f in floors.items()} == {
        m: (Decimal(litres), Decimal(litres) / 2, "GENERIC_DEFAULT") for m in floors}
