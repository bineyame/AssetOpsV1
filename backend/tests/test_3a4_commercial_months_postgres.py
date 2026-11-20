"""3A4 (spec `specs/3A4-amounts-by-month/spec.md` §2, §6 "Postgres"; D-3A4.7, D-3A1.8): the three store reads and money
by month over the Postgres commercial store.

Needs `ASSETOPS_TEST_DATABASE_URL` naming a `*_test` database (the harness routes the run to its own clone); skipped
otherwise. Run through `tools/heavy-slot.sh --db`. Sites are inserted by `NairobiSeeder` (3A1's `Seeder` with
`timezone 'Africa/Nairobi'`; 3A1's file is not edited).
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from test_s1_bindings_postgres import engine, store  # noqa: F401

    import test_3a4_commercial_months as nodb
    from assetops_backend.commercial.adapters.postgres_commercial_store import PostgresCommercialStore
    from assetops_backend.commercial.months import CommercialMonths
    from assetops_backend.commercial.service import CommercialRecords
    from test_3a1_commercial_postgres import Seeder
    from test_3a1_commercial_service import SITES, T0, Clock, make_world


class NairobiSeeder(Seeder if URL else object):
    """3A1's `Seeder`, with every Site in `Africa/Nairobi` (P1)."""

    def add_site(self, tenant_id: UUID, code: str) -> UUID:
        sid = uuid4()
        with self.engine.begin() as c:
            c.execute(text(
                "INSERT INTO site (id, tenant_id, site_code, site_code_key, name, site_type, timezone, lifecycle, "
                "origin, proposed_source_mode, created_at) VALUES (:id, :t, :c, lower(:c), :c, 'MINIGRID', "
                "'Africa/Nairobi', 'ACTIVE', 'IMPORTED', 'SIMULATED', :at)"),
                {"id": sid, "t": tenant_id, "c": code, "at": T0})
        return sid


@pytest.fixture()
def pgworld(store, engine):  # noqa: F811 - `store` empties the tenant closure, the commercial tables included
    owned = PostgresCommercialStore(URL)
    w = make_world(NairobiSeeder(engine))
    clock = Clock()
    yield dict(w, store=owned, clock=clock, svc=CommercialRecords(owned, clock=clock),
               tid=w["tenants"]["lakeside-power"], kobo=w["sites"]["KOBO-001"],
               months=CommercialMonths(owned, clock=lambda: nodb.READ_AT))
    owned.dispose()


def mirror(w) -> dict:
    """An in-memory world with the same tenant and Site IDs (3A1's `mirror`, over `MonthsMemoryStore`)."""
    mem = nodb.MonthsMemoryStore()
    mem.slugs.update({tid: slug for slug, tid in w["tenants"].items()})
    for slug, codes in SITES.items():
        for code in codes:
            mem.sites[(w["tenants"][slug], code.lower())] = w["sites"][code]
    clock = Clock()
    return dict(tenants=w["tenants"], sites=w["sites"], store=mem, clock=clock,
                svc=CommercialRecords(mem, clock=clock), tid=w["tid"], kobo=w["kobo"],
                months=CommercialMonths(mem, clock=lambda: nodb.READ_AT))


def _key(r):
    return (r.site_id, r.kind, r.revision_no, r.source_version, r.recognition_period, r.settled_at, r.source_system,
            r.source_record_id, r.canonical, r.amount, r.quantity, r.provenance, r.recorded_at)


# --- 1: the fixture through Postgres; no-database tests 1 to 3 and 6 against it ------------------------------------

def test_pg_01_october_after_f(pgworld) -> None:
    nodb.test_01_october_after_f_line_by_line(pgworld)


def test_pg_01_known_at(pgworld) -> None:
    nodb.test_02_known_at_reads_the_month_as_known(pgworld)


def test_pg_01_november_and_portfolio(pgworld) -> None:
    nodb.test_02_november_and_the_portfolio(pgworld)


def test_pg_01_stamps_and_months_touched(pgworld) -> None:
    nodb.test_02_stamps_go_stale_and_months_touched(pgworld)


def test_pg_01_settlement_boundary(pgworld) -> None:
    nodb.test_03_settlement_falls_in_its_site_local_month(pgworld)


def test_pg_01_exact_sums(pgworld) -> None:
    nodb.test_06_sums_are_exact_past_28_digits(pgworld)


# --- 2: known_at agrees with the in-memory store at each step -----------------------------------------------------

def test_pg_02_known_at_matches_memory(pgworld) -> None:
    mem = mirror(pgworld)
    tid, kobo = pgworld["tid"], pgworld["kobo"]
    instants = []
    for step in nodb.steps():
        for w in (pgworld, mem):
            nodb.ingest_at(w, step["at"], step["batch"])
        at = datetime.fromisoformat(step["at"])
        instants += [at - timedelta(microseconds=1), at]
    instants.append(datetime(2026, 10, 31, 20, 0, tzinfo=timezone.utc))
    seen = set()
    for known in instants:
        for filters in ({}, {"site_id": kobo}, {"recognition_period": "2026-10"}, {"kind": "CHARGE"},
                        {"recognition_period": "2026-11"}):
            pg = pgworld["store"].latest_revisions(tid, known_at=known, **filters)
            assert [_key(r) for r in pg] == [_key(r) for r in mem["store"].latest_revisions(tid, known_at=known,
                                                                                            **filters)]
            seen.add(len(pg))
    assert 0 in seen and len(seen) > 4  # the comparison covers empty and growing reads
    fuel = [r for r in pgworld["store"].latest_revisions(tid, known_at=datetime(2026, 11, 5, tzinfo=timezone.utc))
            if r.source_record_id == "KOBO-EX-FUEL-1028"]
    assert [(r.revision_no, str(r.amount)) for r in fuel] == [(1, "262.50")]


# --- 3: latest before the filter (D-3A1.8) --------------------------------------------------------------------------

def test_pg_03_period_filter_applies_after_latest(pgworld) -> None:
    nodb.ingest_steps(pgworld)
    ids = [r.source_record_id for r in pgworld["store"].latest_revisions(pgworld["tid"], recognition_period="2026-10")]
    assert "KOBO-CH-0001" in ids and "KOBO-CH-0004" not in ids
    (moved,) = [r for r in pgworld["store"].latest_revisions(pgworld["tid"], recognition_period="2026-11")
                if r.source_record_id == "KOBO-CH-0004"]
    assert moved.revision_no == 2


# --- 4: intake_revisions round-trips --------------------------------------------------------------------------------

def test_pg_04_intake_revisions(pgworld) -> None:
    store, tid = pgworld["store"], pgworld["tid"]
    intakes = nodb.ingest_steps(pgworld)
    first = store.intake_revisions(tid, intakes[0])
    assert [(n.source_record_id, n.revision_no, o) for n, o in first] == [
        ("KOBO-CH-0001", 1, None), ("KOBO-CH-0002", 1, None), ("KOBO-CH-0003", 1, None), ("KOBO-CH-0004", 1, None),
        ("KOBO-RC-0001", 1, None), ("KOBO-RC-0002", 1, None)]
    late = store.intake_revisions(tid, intakes[4])
    assert [(n.source_record_id, n.revision_no, o and o.revision_no) for n, o in late] == [
        ("KOBO-EX-FUEL-1028", 2, 1), ("KOBO-EX-OM-1029", 1, None)]
    (moved,) = store.intake_revisions(tid, intakes[5])
    new, old = moved
    assert (new.source_record_id, new.revision_no, new.recognition_period) == ("KOBO-CH-0004", 2, "2026-11")
    assert old is not None and (old.revision_no, old.recognition_period) == (1, "2026-10")
    history = store.record_history(tid, new.record_id)
    assert (old, new) == history  # the same rows, every column
    assert new.supersedes_revision_id == old.id
    assert store.intake_revisions(tid, uuid4()) == ()


# --- 5: site_zones ----------------------------------------------------------------------------------------------

def test_pg_05_site_zones(pgworld) -> None:
    for slug, codes in SITES.items():
        zones = pgworld["store"].site_zones(pgworld["tenants"][slug])
        assert dict(zones) == {pgworld["sites"][code]: "Africa/Nairobi" for code in codes}
    assert pgworld["store"].site_zones(uuid4()) == {}
