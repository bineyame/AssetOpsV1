"""3A6 (spec §5, §6 "Postgres"; D-3A6.2, D-3A6.12, D-3A6.15): migration 0067, the profile reads and writes of the
Postgres commercial store, and the acceptance re-check under the tenant's lock.

Needs `ASSETOPS_TEST_DATABASE_URL` naming a `*_test` database (the harness routes the run to its own clone); skipped
otherwise. Run through `tools/heavy-slot.sh --db`.
"""
from __future__ import annotations

import os
from dataclasses import fields
from uuid import UUID

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from test_s1_bindings_postgres import engine, store  # noqa: F401

    import pg_harness
    from assetops_backend.commercial.adapters.postgres_commercial_store import PostgresCommercialStore
    from assetops_backend.commercial.profiles import SourceProfiles
    from assetops_backend.commercial.service import CommercialRecords
    from assetops_backend.commercial.uploads import Actor, CommercialUploads, UploadRefused, UploadScope
    from test_3a1_commercial_postgres import Seeder
    from test_3a1_commercial_service import Clock
    from test_3a2_commercial_upload_postgres import _count, _person
    from test_3a2_commercial_upload_service import KEY, KISIWA, KOBO, T_SUBMIT, Keys
    from test_3a6_source_profiles import (KOBO_EXPECTED, KOBO_PROFILE, KOBO_SAMPLE, V1, V2, _template,
                                          profile_with)

FIN, ANALYST = "FINANCE_AND_COMMERCIAL_LEAD", "ANALYST"
TABLE = "commercial_source_profile"


@pytest.fixture()
def w(store, engine):  # noqa: F811 - `store` empties the tenant closure, this table included
    seeder = Seeder(engine)
    tid = seeder.add_tenant("acme")
    seeder.add_site(tid, KOBO)
    seeder.add_site(tid, KISIWA)
    pg = PostgresCommercialStore(URL)
    clock = Clock(T_SUBMIT)
    profiles = SourceProfiles(pg, clock=clock, real_data=False)
    svc = CommercialUploads(CommercialRecords(pg, clock=clock), pg, Keys({tid: KEY}), clock=clock, real_data=False,
                            profiles=profiles)
    people = {n: _person(engine, tid, n) for n in ("ana", "fiona")}
    yield dict(store=pg, profiles=profiles, svc=svc, tid=tid, org=UploadScope(None, None),
               ana=Actor(people["ana"], ANALYST), fiona=Actor(people["fiona"], FIN))
    pg.dispose()


def _admit(w, profile=KOBO_PROFILE):
    return w["profiles"].admit(w["tid"], w["ana"], profile, KOBO_SAMPLE, KOBO_EXPECTED)


def _upload(w, data=KOBO_SAMPLE, reader=V1, name="kobo-ledger.csv") -> dict:
    return w["svc"].submit(w["tid"], w["org"], w["ana"], data, file_name=name, reader_id=reader,
                           media_type="text/csv")


def _accept(w, answer: dict) -> dict:
    return w["svc"].decide(w["tid"], w["org"], w["fiona"], answer["upload_id"], "ACCEPT")


def _this_migration(cfg):
    from alembic.script import ScriptDirectory

    for script in ScriptDirectory.from_config(cfg).walk_revisions():
        if TABLE in getattr(script.module, "TABLES", ()):
            return script
    raise AssertionError("no migration declares the profile table")


# --- Q1: the migration ---------------------------------------------------------------------------------------------

def test_q1_migration_chain_trigger_and_refused_downgrade(w, engine) -> None:  # noqa: F811
    from alembic import command

    cfg = pg_harness._alembic(URL)
    script = _this_migration(cfg)
    assert (script.revision, script.down_revision) == ("0067_source_profile", "0066_structure_snapshot")
    with engine.connect() as c:
        assert c.execute(text("SELECT count(*) FROM pg_trigger WHERE tgrelid = to_regclass(:t) "
                              "AND tgname = :t || '_immutable'"), {"t": TABLE}).scalar_one() == 1
    row = _admit(w)
    with pytest.raises(Exception, match="append-only|append only|immutable"):
        with engine.begin() as c:
            c.execute(text("UPDATE commercial_source_profile SET status = 'PINNED' WHERE id = :i"),
                      {"i": row.profile_row_id})
    w["store"].dispose()
    with pytest.raises(Exception, match="refused: admitted source profiles exist"):
        command.downgrade(cfg, script.down_revision)
    with engine.begin() as c:  # TRUNCATE is not a row DELETE; the append-only trigger does not fire on it
        c.execute(text(f"TRUNCATE {TABLE}"))
    command.downgrade(cfg, script.down_revision)
    with engine.connect() as c:
        assert c.execute(text("SELECT to_regclass(:t)"), {"t": TABLE}).scalar_one() is None
        assert c.execute(text("SELECT to_regclass('structure_snapshot')")).scalar_one() is not None
    command.upgrade(cfg, "head")
    pg_harness.assert_at_head(engine)


# --- Q2: the three reads round-trip every column -------------------------------------------------------------------

def test_q2_admit_two_versions_and_read_back(w) -> None:
    v1 = _admit(w)
    v2 = _admit(w, profile_with())
    assert (v1.version, v2.version, v2.reader) == (1, 2, V2)
    store, tid = w["store"], w["tid"]
    assert store.source_profiles_all(tid, "kobo-ledger-expenses") == (v1, v2)
    assert store.source_profile_latest(tid, "kobo-ledger-expenses") == v2
    assert store.source_profiles_latest(tid) == (v2,)
    for f in fields(v2):  # every column, value for value
        assert getattr(store.source_profile_latest(tid, "kobo-ledger-expenses"), f.name) == getattr(v2, f.name)
    assert _admit(w) == v1  # already admitted: nothing written
    assert _count(w["store"]._engine, TABLE) == 2


# --- Q3: U1 end to end, then U3's race ------------------------------------------------------------------------------

def test_q3_upload_end_to_end_then_the_race(w, engine) -> None:  # noqa: F811
    _admit(w)
    template = _upload(w, _template(), "expenses-illustrative-1", "template.csv")
    store = w["store"]
    real = store.held_uploads
    store.held_uploads = lambda tenant_id: ()  # the concurrent submit that passed its check first
    try:
        answer = _upload(w)
    finally:
        store.held_uploads = real
    assert _accept(w, answer)["state"] == "ACCEPTED"
    held = {h.upload_id: h for h in store.held_uploads(w["tid"])}
    accepted = held[UUID(answer["upload_id"])]
    assert (accepted.source_system, accepted.site_codes, accepted.waiting) == ("lakeside-purchases-ledger",
                                                                                (KOBO,), False)
    waiting = held[UUID(template["upload_id"])]
    assert waiting.waiting and waiting.site_codes == (KOBO,)
    before = [_count(engine, t) for t in ("commercial_intake", "commercial_record_revision",
                                          "commercial_upload_decision")]
    with pytest.raises(UploadRefused) as raised:
        _accept(w, template)
    assert (raised.value.status, raised.value.code, raised.value.params) == (
        409, "UPLOAD_SOURCE_SWITCHED", {"source_type": "expense_ledger", "system": "lakeside-purchases-ledger"})
    assert [_count(engine, t) for t in ("commercial_intake", "commercial_record_revision",
                                        "commercial_upload_decision")] == before
    assert w["svc"].get(w["tid"], w["org"], template["upload_id"])["state"] == "WAITING"
