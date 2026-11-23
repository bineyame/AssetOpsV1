"""DD5a unit 3 at load level (spec §4.6 as amended by D-DD.139, D-DD.140): `load_world_inputs` resolves a Site
through `PostgresEvidenceLedger.site_scope` and its pinned binding snapshot, seals two local days of readings with one
sequence per source over the span, and the bulk path loads them; a re-run loads nothing new; an unknown Site refuses.
Plant (b) of the card (a sequence reset per day) fails `test_two_days_seal_and_load_with_one_sequence_per_source`: the
second day reuses the first day's message ids, and the load stops at exit 2 (`BATCH_ID_CONFLICT`: the batch id is
formed over the same message ids, so the collision surfaces at the batch). The converted Kobo Site (mini-grid, v3) is the seed. Requires ASSETOPS_TEST_DATABASE_URL."""
from __future__ import annotations

import json
import os

import pytest

import pg_harness

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import create_engine, text
    from test_ds3_bulk_load_postgres import seed_database

    from assetops_backend import load_world_inputs

DAYS = ("2026-10-06", "2026-10-07")
DIGEST = "e" * 64


@pytest.fixture(scope="module")
def seed():
    url, kit, _ = seed_database("dd5als")
    try:
        yield url, kit
    finally:
        pg_harness.drop_database(url)


@pytest.fixture()
def world(seed, tmp_path, monkeypatch):
    url, kit = seed
    clone = pg_harness.clone_database("dd5alc", url)
    engine = create_engine(clone)
    try:
        with engine.connect() as c:
            slug = c.execute(text("SELECT slug FROM tenant WHERE id = :t"), {"t": kit.principal.tenant_id}).scalar_one()
        code = kit.doc["site"]["site_code"]
        b = kit.binding("pv-inverter-controller")
        telemetry = tmp_path / slug / "telemetry"
        telemetry.mkdir(parents=True)
        for day in DAYS:
            rows = [{"source_id": b["device_id"], "signal_id": b["signal_id"], "start": f"{day}T{h}:00:00+03:00",
                     "end": f"{day}T{h}:00:00+03:00", "value": "1.500", "unit": b["source_unit"]}
                    for h in (10, 11, 12)]
            (telemetry / f"{code}.{day}.readings.json").write_text(json.dumps(
                {"day": day, "role_set": kit.doc["mapping"]["role_set"], "schema": "assetops.world-readings/1",
                 "site_code": code, "timezone": "Africa/Nairobi", "readings": rows}))
        (tmp_path / "site-inputs.json").write_text(json.dumps(
            {"sites": [{"tenant": slug, "code": code, "foundation_digest": DIGEST}]}))
        monkeypatch.setenv("DATABASE_URL", clone)
        yield tmp_path, slug, code, engine
    finally:
        pg_harness.dispose(engine)
        pg_harness.drop_database(clone)


def run(path) -> int:
    return load_world_inputs.main(["--world", str(path), "--submit-as", "s@x", "--accept-as", "a@x"])


def test_two_days_seal_and_load_with_one_sequence_per_source(world, capsys) -> None:
    path, slug, code, engine = world
    assert run(path) == 0, capsys.readouterr().err
    line = json.loads(capsys.readouterr().out)
    assert (line["readings_files"], line["sealed_batches"], line["batches"], line["envelopes"]) == (2, 2, 2, 6)
    assert sorted(p.name.split(".")[2] for p in (path / slug / "sealed").iterdir()) == list(DAYS)
    with engine.connect() as c:
        rows = c.execute(text("SELECT sequence_epoch, sequence, message_id FROM accepted_evidence "
                              "WHERE device_id = 'pv-inverter-controller' ORDER BY sequence")).all()
    assert [(r.sequence_epoch, r.sequence) for r in rows] == [("1", n) for n in range(1, 7)]
    assert len({r.message_id for r in rows}) == 6


def test_a_rerun_loads_nothing_new_and_writes_no_sealed_bytes(world, capsys) -> None:
    path, slug, _, _ = world
    assert run(path) == 0
    capsys.readouterr()
    sealed = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in (path / slug / "sealed").iterdir()}
    assert run(path) == 0
    line = json.loads(capsys.readouterr().out)
    assert (line["sealed_batches"], line["already_loaded"]) == (2, 2)
    assert {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in (path / slug / "sealed").iterdir()} == sealed


def test_an_unknown_site_refuses_with_exit_2(world, capsys) -> None:
    path, slug, code, engine = world
    telemetry = path / slug / "telemetry"
    for f in telemetry.iterdir():
        f.rename(telemetry / f.name.replace(code, "NOPE-1"))
        f = telemetry / f.name.replace(code, "NOPE-1")
        f.write_text(f.read_text().replace(code, "NOPE-1"))
    (path / "site-inputs.json").write_text(json.dumps(
        {"sites": [{"tenant": slug, "code": "NOPE-1", "foundation_digest": DIGEST}]}))
    assert run(path) == 2
    assert capsys.readouterr().err == f"WORLD_TELEMETRY_UNRESOLVED NOPE-1.{DAYS[0]}.readings.json site NOPE-1\n"
    with engine.connect() as c:
        assert c.execute(text("SELECT count(*) FROM accepted_evidence")).scalar_one() == 0
