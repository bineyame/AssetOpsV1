"""DS4 T15 to T17 (spec `specs/DS4-template-ladder/spec.md` §3.7, §5; D-DS4.17): the bulk load's batch-cover rule
over PostgreSQL.

A module seed (`seed_database("ds4g")`: the converted Kobo Site, enabled, nothing ingested) is cloned afresh for
every case (`ds4g<n>`), each dropped in `finally`. Envelopes are `pv-inverter-controller` readings, sequences from
900001. Requires ASSETOPS_TEST_DATABASE_URL (backend/TESTING.md).
"""

from __future__ import annotations

import itertools
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

import pg_harness

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from test_ds3_bulk_load_postgres import Db, seed_database

    from assetops_backend import load_world_inputs
    from assetops_backend.evidence.bulk_load import BulkLoaded, BulkLoadRefused
    from assetops_backend.evidence.ledger_service import BatchIngestionService
    from assetops_contracts.ingestion_batch_v2 import parse_canonical_batch_v2_text

GAP = ("2026-10-06T10:00:00Z", "2026-10-07T22:00:00Z")  # local (+03:00) days 6 and 8
CONTIGUOUS = ("2026-10-06T10:00:00Z", "2026-10-07T10:00:00Z")
_CLONES = itertools.count(1)


@pytest.fixture(scope="module")
def seed():
    url, kit, _ = seed_database("ds4g")
    try:
        yield url, kit
    finally:
        pg_harness.drop_database(url)


@pytest.fixture()
def db(seed):
    url, kit = seed
    clone = Db(pg_harness.clone_database(f"ds4g{next(_CLONES)}", url))
    clone.kit = kit
    try:
        yield clone
    finally:
        clone.close()


def points(kit, times, first=900001) -> bytes:
    texts = [kit.envelope("pv-inverter-controller", first + i, 0, "1.5", source_time=t) for i, t in enumerate(times)]
    return kit.seal(texts).encode("utf-8")


def batch_id(raw: bytes) -> str:
    return parse_canonical_batch_v2_text(raw.decode("utf-8")).batch_id


def test_t15_a_local_day_gap_is_refused_and_nothing_is_written(db) -> None:
    [(zone,)] = db.rows("SELECT timezone FROM site WHERE id = :s", s=db.kit.principal.site_id)
    assert datetime(2026, 10, 6, tzinfo=ZoneInfo(zone)).utcoffset() == timedelta(hours=3)  # the case's premise
    raw = points(db.kit, GAP)
    before = db.counts()
    with pytest.raises(BulkLoadRefused) as caught:
        db.load([raw])
    assert caught.value.code == "BULK_BATCH_GAP_DAYS"
    assert caught.value.external_batch_id == batch_id(raw)
    assert "2026-10-07" in caught.value.detail and caught.value.detail.startswith("local ")
    assert db.counts() == before


def test_t16_contiguous_local_days_load(db) -> None:
    assert db.load([points(db.kit, CONTIGUOUS)]) == BulkLoaded(1, 0, 2)


def test_t16b_an_interval_across_local_midnight_and_a_point_the_next_local_day_load(db) -> None:
    interval = db.kit.envelope("pv-inverter-controller", 900001, 0, "1.5", source_time="2026-10-06T21:15:00Z",
                               interval_start="2026-10-06T20:45:00Z")
    point = db.kit.envelope("pv-inverter-controller", 900002, 0, "1.5", source_time="2026-10-07T22:00:00Z")
    assert db.load([db.kit.seal([interval, point]).encode("utf-8")]) == BulkLoaded(1, 0, 2)


def test_t16c_a_gap_batch_completed_by_the_real_path_is_already_loaded_not_refused(db) -> None:
    raw = points(db.kit, GAP)
    answer = BatchIngestionService(db.ledger).submit(db.kit.principal, raw)
    assert answer.status == 200 and answer.receipt.status == "COMPLETED", answer
    assert db.load([raw]) == BulkLoaded(1, 1, 2)


def test_t17_load_world_inputs_stops_at_the_gap_batch_with_exit_2(db, tmp_path, monkeypatch, capsys) -> None:
    telemetry = tmp_path / "demo" / "telemetry"
    telemetry.mkdir(parents=True)
    a, b = points(db.kit, CONTIGUOUS), points(db.kit, GAP, first=900003)
    (telemetry / "a.batch.json").write_bytes(a)
    (telemetry / "b.batch.json").write_bytes(b)
    monkeypatch.setenv("DATABASE_URL", db.url)
    for variable in ("PGDATABASE", "PGHOST", "PGHOSTADDR", "PGPORT", "PGSERVICE", "PGSERVICEFILE", "ASSETOPS_PG_PORT"):
        monkeypatch.delenv(variable, raising=False)
    code = load_world_inputs.main(["--world", str(tmp_path), "--submit-as", "s@x", "--accept-as", "a@x"],
                                  ledger=db.ledger)
    assert code == 2
    assert capsys.readouterr().err.startswith(f"BULK_BATCH_GAP_DAYS {batch_id(b)} ")
    stored = {r[0] for r in db.rows("SELECT external_batch_id FROM ingestion_batch")}
    assert batch_id(a) in stored and batch_id(b) not in stored
