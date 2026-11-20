"""3B7a unit 3 (spec §6 "Postgres"; D-3B7A.1, D-3B7A.9): the snapshot store, composition, command and migration 0066.

Needs `ASSETOPS_TEST_DATABASE_URL` naming a `*_test` database (the harness routes the run to its own clone); skipped
otherwise. Run through `tools/heavy-slot.sh --db`. Sites by 3A4's `NairobiSeeder`; the world through
`PostgresCommercialStore` as `test_5a_targets_postgres.py` (5a's step-1 `entered_by` renamed as there).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from decimal import Decimal
from uuid import UUID

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from test_s1_bindings_postgres import engine, store  # noqa: F401

    import pg_harness
    import test_3a4_commercial_months as months_nodb
    import test_3b7a_structure_snapshot as nodb
    import test_5a_targets as t5a
    from assetops_backend.commercial.adapters.postgres_commercial_store import PostgresCommercialStore
    from assetops_backend.commercial.months import CommercialMonths
    from assetops_backend.commercial.service import CommercialRecords
    from assetops_backend.structure_snapshot.adapters.postgres_structure_snapshot_store import \
        PostgresStructureSnapshotStore
    from assetops_backend.structure_snapshot.composition import build_structure_snapshot
    from assetops_backend.structure_snapshot.store import SnapshotExists
    from test_3a1_commercial_service import Clock, make_world
    from test_3a4_commercial_months_postgres import NairobiSeeder

    class CountingStore(PostgresStructureSnapshotStore):
        """The adapter plus a row count for the tests (`row_count`)."""

        def count_rows(self) -> int:
            with self._engine.connect() as c:
                return c.execute(text("SELECT count(*) FROM structure_snapshot")).scalar_one()

TABLES = ("structure_snapshot",)
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture()
def pgworld(store, engine):  # noqa: F811 - `store` empties the tenant closure, the snapshot table included
    owned = PostgresCommercialStore(URL)
    w = make_world(NairobiSeeder(engine))
    clock = Clock()
    w = dict(w, store=owned, clock=clock, svc=CommercialRecords(owned, clock=clock),
             tid=w["tenants"]["lakeside-power"], months=CommercialMonths(owned, clock=lambda: months_nodb.READ_AT))
    snapshots = CountingStore(URL)
    yield nodb.lakeside(w, names={t5a.LOADER: "service:ds3-loader"}), snapshots
    snapshots.dispose()
    owned.dispose()


def _pg_refs(w):
    """The three seeded Sites; Thika (COLDCHAIN, not in the database) is asked for as in memory."""
    return nodb.refs(w)


# --- 1: tests 3, 4(a), 4(b), 4(d) and 9 against the Postgres store ---------------------------------------------------

def test_pg_1_build_and_serve(pgworld) -> None:
    w, snapshots = pgworld
    nodb.check_3_build_and_serve(w, snapshots)


def test_pg_1_late_invoice_and_rebuild(pgworld) -> None:
    w, snapshots = pgworld
    nodb.check_4b_rebuild(w, snapshots)  # runs 3 and 4(a) first


def test_pg_1_new_kind(pgworld) -> None:
    w, snapshots = pgworld
    nodb.check_4d_new_kind(w, snapshots)


def test_pg_1_verify(pgworld) -> None:
    w, snapshots = pgworld
    nodb.check_9_verify(w, snapshots)


# --- 2: the table refuses change; a same-instant put; tenant_sites ---------------------------------------------------

def test_pg_2_append_only_and_same_instant(pgworld, engine) -> None:  # noqa: F811
    w, snapshots = pgworld
    s = nodb.setup(w, snapshots)
    result = s.builder.build(w["tid"], nodb.refs(w), nodb.OCT, built_by=nodb.BY)
    kobo_id = result.sites["KOBO-001"]
    first = snapshots.get(w["tid"], [kobo_id])
    for sql in ("UPDATE structure_snapshot SET built_by = 'service:x' WHERE id = :i",
                "DELETE FROM structure_snapshot WHERE id = :i"):
        with pytest.raises(Exception, match="structure_snapshot rows are append-only"):
            with engine.begin() as c:
                c.execute(text(sql), {"i": kobo_id})
    before = snapshots.count_rows()
    with pytest.raises(SnapshotExists):
        snapshots.put(first)
    assert snapshots.count_rows() == before and snapshots.get(w["tid"], [kobo_id]) == first
    tenant, sites = snapshots.tenant_sites("lakeside-power")
    assert tenant == w["tid"] and [x.site_code for x in sites] == sorted(nodb.CODES)
    assert {x.site_code: x.site_id for x in sites} == {c: w["sites"][c] for c in nodb.CODES}
    assert {(x.site_type, x.timezone) for x in sites} == {("MINIGRID", nodb.NAIROBI)}
    assert snapshots.tenant_sites("nope") is None
    with pytest.raises(LookupError):
        snapshots.get(w["tid"], [UUID(int=4242)])


# --- 3: the composition and the command ------------------------------------------------------------------------------

def test_pg_3_composition_and_command(pgworld) -> None:
    w, _ = pgworld
    service = build_structure_snapshot(URL)
    try:
        tenant, sites = service.store.tenant_sites("lakeside-power")
        service.builder.build(tenant, sites, nodb.OCT, built_by=nodb.BY)
        kobo = {x.site_code: x for x in sites}["KOBO-001"]
        served = service.read.site(tenant, kobo, nodb.OCT)
    finally:
        service.dispose()
    assert served.state == "SERVED" and served.freshness.reasons == ()
    assert served.snapshot.actual.values["contribution"].value == Decimal("883.00")

    env = dict(os.environ, DATABASE_URL=URL)

    def run(*args):
        return subprocess.run([sys.executable, "-m", "assetops_backend.build_structure_snapshot", *args], env=env,
                              cwd=REPO, capture_output=True, text=True, timeout=300)

    built = run("build", "--tenant", "lakeside-power", "--month", nodb.OCT, "--by", nodb.BY)
    assert built.returncode == 0, built.stderr
    lines = built.stdout.strip().splitlines()
    assert len(lines) == 1
    line = json.loads(lines[0])
    assert list(line["sites"]) == sorted(nodb.CODES) and line["excluded"] == [] and len(line["rules_digest"]) == 64
    verified = run("verify", "--tenant", "lakeside-power", "--snapshot", line["portfolio_snapshot_id"])
    assert verified.returncode == 0, verified.stderr
    assert json.loads(verified.stdout)["matches"] is True
    refused = run("build", "--tenant", "nope", "--month", nodb.OCT, "--by", nodb.BY)
    assert refused.returncode == 2 and refused.stderr.startswith("UNKNOWN_TENANT ")


# --- 4: migration up, down (empty) and refusal (a row present) -------------------------------------------------------

def _this_migration(cfg):
    from alembic.script import ScriptDirectory

    for script in ScriptDirectory.from_config(cfg).walk_revisions():
        if "structure_snapshot" in getattr(script.module, "TABLES", ()):
            return script
    raise AssertionError("no migration declares the structure_snapshot table")


def test_pg_4_migration_down_refused_then_down_and_up(pgworld, engine) -> None:  # noqa: F811
    from alembic import command
    from alembic.script import ScriptDirectory

    w, snapshots = pgworld
    cfg = pg_harness._alembic(URL)
    script = _this_migration(cfg)
    assert script.revision == ScriptDirectory.from_config(cfg).get_current_head()
    assert isinstance(script.down_revision, str) and script.down_revision != script.revision
    nodb.setup(w, snapshots).builder.build(w["tid"], nodb.refs(w), nodb.OCT, built_by=nodb.BY)
    snapshots.dispose()
    w["store"].dispose()
    with pytest.raises(Exception, match="refused: structure snapshots exist"):
        command.downgrade(cfg, script.down_revision)
    with engine.begin() as c:  # TRUNCATE is not a row DELETE; the append-only trigger does not fire on it
        c.execute(text("TRUNCATE " + ", ".join(TABLES)))
    command.downgrade(cfg, script.down_revision)
    with engine.connect() as c:
        assert c.execute(text("SELECT to_regclass('structure_snapshot')")).scalar_one() is None
        assert c.execute(text("SELECT to_regclass('commercial_upload')")).scalar_one() is not None
    command.upgrade(cfg, "head")
    pg_harness.assert_at_head(engine)
