"""W4-02 unit 1: migration `0029_w4_mini_depth`, its enqueue functions and the mini-depth store writer.

`D-2026-10-20-w4-02-buildspec` base DDL, closure 1 Q14/Q25/Q26, closure 2 "Enqueue, selection and registration",
closure 3 and closure 4 B1/N5/S2. Accepted rows are written in the S2 writer's shape (the row, then its ACCEPTED
disposition, one transaction) by cloning one accepted row of the mini-grid Site fixture (`Ev.write`).
Requires ASSETOPS_TEST_DATABASE_URL.
"""

from __future__ import annotations

import hashlib
import os
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError
    from test_s1_bindings_postgres import _alembic, engine, store  # noqa: F401
    from test_s4_consequence_store_postgres import _release_connections, site  # noqa: F401
    from test_w203_cold_migration_postgres import _replica, head, scalar, table_exists
    from test_w206_ev_enqueue_postgres import Ev

    from assetops_backend.mini_depth.store import (
        JOB_DOMAIN,
        MiniDepthWriteRefused,
        MiniRevision,
        PostgresMiniDepthStore,
    )
    from assetops_backend.sites.binding_roles import MINIGRID_ROLES_4

HEAD = "0034_w5_ev_scenarios"  # W5-03b: 0034 sits above 0033; W5-02a: the current head (0033) sits above 0032 and 0030
MIGRATION = "0029_w4_mini_depth"
PREVIOUS = "0027_w4_work_cases"
REFUSED = "Downgrade of 0029_w4_mini_depth refused: mini-depth history exists"
REFUSED_BASIS = "Downgrade of 0029_w4_mini_depth refused: cutover basis history exists"
#: The three mini tables and the q12-6 `site_cutover_basis` table, all created by 0029.
TABLES = ("mini_depth_revision", "mini_depth_revision_evidence", "mini_depth_selection", "site_cutover_basis")
FUNCTIONS = ("mini_enqueue_hour", "mini_enqueue_accepted", "mini_enqueue_configuration")
MINI = tuple(JOB_DOMAIN.values()) if URL else ()
#: Closure 4 B1, restated independently of the migration module.
MATRIX = {
    "mini_renewable": {"pv_available_power", "pv_power", "feeder_demand", "battery_soc",
                       "storage_charge_requested_power", "critical_load_requested_power",
                       "critical_load_delivered_power"},
    "mini_service": {"feeder_demand", "feeder_requested_power", "critical_load_requested_power",
                     "critical_load_delivered_power"},
    "mini_fuel": {"generator_power", "fuel_level"},
    "mini_backup": {"site_supply_state", "mini_backup_start_event", "generator_state", "generator_power",
                    "mini_backup_bus_state", "critical_load_requested_power", "critical_load_delivered_power",
                    "feeder_demand"},
}


def _sha(label: str) -> str:
    return "sha256:" + hashlib.sha256(label.encode()).hexdigest()


def functiondef(engine, name: str) -> str:  # noqa: F811
    return scalar(engine, "SELECT pg_get_functiondef(p.oid) FROM pg_proc p WHERE p.proname = :n", n=name)


def catalog(engine) -> tuple[int, int, int, int]:  # noqa: F811
    """(0029 tables incl. `site_cutover_basis`, mini functions, triggers on mini tables plus enqueue_mini_depth, the selection job FK)."""
    return (
        sum(table_exists(engine, t) for t in TABLES),
        scalar(engine, "SELECT count(*) FROM pg_proc WHERE proname = ANY(:n)", n=list(FUNCTIONS)),
        scalar(engine, "SELECT count(*) FROM pg_trigger WHERE NOT tgisinternal AND (tgname LIKE 'mini_depth_%' "
                       "OR tgname = 'enqueue_mini_depth')"),
        scalar(engine, "SELECT count(*) FROM pg_constraint WHERE conname = 'mini_depth_selection_job_fk'"),
    )


SITE_STAGES_BEFORE = "'IDLE'::text, 'S3'::text, 'S4'::text, 'CONSEQUENCE'::text"
# W4-03 closure 4 S1: at the current head 0030 also admits OPPORTUNITY after MINI.
SITE_STAGES_AFTER = "'IDLE'::text, 'S3'::text, 'MINI'::text, 'OPPORTUNITY'::text, 'S4'::text, 'CONSEQUENCE'::text"
MINI_COUNTERS = [(n, "integer", "0", "NO") for n in ("mini_deferred", "mini_failed", "mini_processed")]


def site_head_shape(engine) -> tuple[list[tuple], list[str]]:  # noqa: F811
    """q7 ruling 1: the `mini_*` counters of `schedule_site_head` (name, type, default, nullable) and every CHECK
    definition naming its `stage` column."""
    with engine.connect() as c:
        columns = [tuple(r) for r in c.execute(text(
            "SELECT column_name, data_type, column_default, is_nullable FROM information_schema.columns "
            "WHERE table_name = 'schedule_site_head' AND column_name LIKE 'mini\\_%' ORDER BY column_name"))]
        checks = [r[0] for r in c.execute(text(
            "SELECT conname || ' ' || pg_get_constraintdef(oid) FROM pg_constraint "
            "WHERE conrelid = 'schedule_site_head'::regclass AND contype = 'c' ORDER BY conname"))]
    return columns, checks


def assert_site_head(engine, *, upgraded: bool) -> None:  # noqa: F811
    columns, checks = site_head_shape(engine)
    stages = SITE_STAGES_AFTER if upgraded else SITE_STAGES_BEFORE
    assert columns == (MINI_COUNTERS if upgraded else []), columns
    assert [x for x in checks if x.startswith("schedule_site_head_stage_check ")] == [
        f"schedule_site_head_stage_check CHECK ((stage = ANY (ARRAY[{stages}])))"], checks
    assert len(checks) == 2, checks  # stage CHECK + the unchanged claim-shape CHECK: zero net CHECKs


def mini_jobs(engine, site_id, *, cause=None) -> list[dict]:  # noqa: F811
    with engine.connect() as c:
        return [dict(r._mapping) for r in c.execute(text(
            "SELECT id, domain, window_start, window_end, cause_evidence_id, status, available_at FROM recompute_job "
            "WHERE site_id = :s AND domain LIKE 'mini\\_%' AND (CAST(:c AS uuid) IS NULL OR cause_evidence_id = :c) "
            "ORDER BY domain, window_start"), {"s": site_id, "c": cause})]


def clear_mini(engine) -> None:  # noqa: F811
    _replica(engine, "DELETE FROM mini_depth_selection", "DELETE FROM mini_depth_revision_evidence",
             "DELETE FROM mini_depth_revision", "DELETE FROM recompute_job WHERE domain LIKE 'mini\\_%'")


def set_type(c, site_id, site_type: str) -> None:
    """Test-only: the 0020 guard fixes a Site type once evidence exists, so the flip runs as replica; the role is
    restored before any accepted row is written, so the deferred mini trigger still fires at commit."""
    c.execute(text("SET LOCAL session_replication_role = replica"))
    c.execute(text("UPDATE site SET site_type = :st WHERE id = :s"), {"st": site_type, "s": site_id})
    c.execute(text("SET LOCAL session_replication_role = origin"))


def local_hours(tz: str, lo: datetime, hi: datetime) -> list[tuple[datetime, datetime]]:
    zone = ZoneInfo(tz)
    h = lo.astimezone(zone).replace(minute=0, second=0, microsecond=0)
    out = []
    while h.astimezone(timezone.utc) < hi:
        start = h.astimezone(timezone.utc)
        out.append((start, start + timedelta(hours=1)))
        h = (start + timedelta(hours=1)).astimezone(zone)
    return out


@pytest.fixture()
def mg(site, engine):  # noqa: F811
    built = Ev(site, engine)
    built.tz = scalar(engine, "SELECT timezone FROM site WHERE id = :s", s=built.ctx.s)
    built.site_obj = site
    clear_mini(engine)
    yield built
    clear_mini(engine)
    _replica(engine, "DELETE FROM ingestion_disposition WHERE ordinal > 100000",
             "DELETE FROM accepted_evidence WHERE message_id LIKE 'w206-enq-%'")


@pytest.fixture()
def mg4(mg, engine):  # noqa: F811
    """q8 ruling 1: the fixture Site with its current binding sets relabelled `minigrid-roles-4` (test-only, as
    replica; the no-current-overlap exclusion forbids a second current set), so enqueue gates open; restored after."""
    with engine.connect() as c:
        prior = c.execute(text("SELECT id, role_set FROM signal_binding_set_revision WHERE site_id = :s "
                               "AND superseded_at IS NULL"), {"s": mg.ctx.s}).all()
    assert prior
    _replica(engine, "UPDATE signal_binding_set_revision SET role_set = 'minigrid-roles-4' WHERE id IN ("
             + ", ".join(f"'{i}'" for i, _ in prior) + ")")
    yield mg
    clear_mini(engine)
    _replica(engine, *[f"UPDATE signal_binding_set_revision SET role_set = '{rs}' WHERE id = '{i}'" for i, rs in prior])


def revision(ctx, *, lo, hi, domain="service", digest="a", cutoff=None, evidence=(), result=None) -> "MiniRevision":
    return MiniRevision(
        tenant_id=ctx.t, site_id=ctx.s, domain=domain, model_version=f"mini-{domain}/1", window_start=lo,
        window_end=hi, knowledge_cutoff=cutoff or hi + timedelta(hours=1), input_sha256=_sha(digest),
        foundation_revision_ids=[], binding_set_revision_ids=[], result=result or {"status": "UNKNOWN"},
        evidence_ids=list(evidence))


def cutover_rows(engine, site_id) -> int:  # noqa: F811
    return scalar(engine, "SELECT count(*) FROM site_cutover_basis WHERE site_id = :s", s=site_id)


def downgrade_config(site, engine):  # noqa: F811
    site.store.dispose()
    site.prices.dispose()
    engine.dispose()
    return _alembic()


class TestMigration0029:
    def test_upgrade_single_head_and_empty_downgrade(self, engine) -> None:  # noqa: F811
        from alembic import command
        from alembic.script import ScriptDirectory

        config = _alembic()
        assert ScriptDirectory.from_config(config).get_heads() == [HEAD]
        assert ScriptDirectory.from_config(config).get_revision(MIGRATION).down_revision == PREVIOUS
        assert head(engine) == HEAD and catalog(engine) == (4, 3, 4, 1)
        assert_site_head(engine, upgraded=True)
        assert scalar(engine, "SELECT count(*) FROM pg_indexes WHERE indexname IN ('mini_depth_selection_head', "
                              "'mini_depth_revision_evidence_lookup')") == 2
        recompute_columns = scalar(engine, "SELECT count(*) FROM information_schema.columns "
                                           "WHERE table_name = 'recompute_job'")
        engine.dispose()
        try:
            command.downgrade(config, PREVIOUS)
            assert head(engine) == PREVIOUS and catalog(engine) == (0, 0, 0, 0)
            assert_site_head(engine, upgraded=False)
            command.upgrade(config, "head")
        finally:
            if head(engine) != HEAD:
                command.upgrade(config, "head")
        assert head(engine) == HEAD and catalog(engine) == (4, 3, 4, 1)
        assert_site_head(engine, upgraded=True)
        assert scalar(engine, "SELECT count(*) FROM information_schema.columns "
                              "WHERE table_name = 'recompute_job'") == recompute_columns

    def test_downgrade_locks_site_cutover_basis_before_counting(self, engine) -> None:  # noqa: F811
        """B-M1: the downgrade's refusal step takes ACCESS EXCLUSIVE on `site_cutover_basis` (with the mini tables)
        before counting: a concurrent ACCESS SHARE holder makes it time out, where a plain SELECT would not."""
        import importlib.util
        from pathlib import Path

        path = Path(__file__).resolve().parents[1] / "migrations" / "versions" / "0029_w4_mini_depth.py"
        spec = importlib.util.spec_from_file_location("m0029", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        assert "site_cutover_basis" in module.REFUSE_IF_USED.split("DO $$")[0]
        holder = engine.connect()
        try:
            holding = holder.begin()
            holder.execute(text("LOCK TABLE site_cutover_basis IN ACCESS SHARE MODE"))
            with engine.connect() as c, c.begin():
                c.execute(text("SET LOCAL lock_timeout = '300ms'"))
                with pytest.raises(DBAPIError) as timed_out:
                    c.exec_driver_sql(module.REFUSE_IF_USED)
                assert getattr(timed_out.value.orig, "sqlstate", None) == "55P03"
            holding.rollback()
        finally:
            holder.close()
        assert head(engine) == HEAD and catalog(engine) == (4, 3, 4, 1)

    def test_downgrade_refuses_active_mini_stage(self, mg, engine) -> None:  # noqa: F811
        """q7 ruling 1: an active MINI Site stage refuses the downgrade; head and schema are unchanged."""
        from alembic import command

        with engine.begin() as c:
            c.execute(text("DELETE FROM schedule_site_head WHERE tenant_id = :t AND site_id = :s"),
                      {"t": mg.ctx.t, "s": mg.ctx.s})
            c.execute(text("INSERT INTO schedule_site_head (tenant_id, site_id, stage, stage_started_at, created_at) "
                           "VALUES (:t, :s, 'MINI', clock_timestamp(), clock_timestamp())"),
                      {"t": mg.ctx.t, "s": mg.ctx.s})
        config = downgrade_config(mg.site_obj, engine)
        try:
            with pytest.raises(DBAPIError, match="MINI stage active"):
                command.downgrade(config, PREVIOUS)
            assert head(engine) == HEAD and catalog(engine) == (4, 3, 4, 1)
            assert_site_head(engine, upgraded=True)
            assert scalar(engine, "SELECT stage FROM schedule_site_head WHERE site_id = :s", s=mg.ctx.s) == "MINI"
        finally:
            with engine.begin() as c:
                c.execute(text("DELETE FROM schedule_site_head WHERE tenant_id = :t AND site_id = :s"),
                          {"t": mg.ctx.t, "s": mg.ctx.s})
            if head(engine) != HEAD:
                command.upgrade(config, "head")

    @pytest.mark.parametrize("blocker", ["job_only", "revision", "cutover_basis"])
    def test_downgrade_refuses_history(self, blocker, mg4, engine) -> None:  # noqa: F811
        mg = mg4
        from alembic import command

        lo = datetime(2026, 10, 6, 9, tzinfo=timezone.utc)
        if blocker == "job_only":
            mg.accept(role="generator_power", when=lo + timedelta(minutes=5), decided=lo + timedelta(hours=2))
            assert mini_jobs(engine, mg.ctx.s)
        elif blocker == "cutover_basis":
            # B-M1: only a q12-6 cutover basis row exists (written by its sole writer); no mini history at all.
            from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore

            PostgresFoundationStore(URL).record_no_legacy_evidence_basis(mg.ctx.t, mg.ctx.s, now=lo)
            assert not mini_jobs(engine, mg.ctx.s) and cutover_rows(engine, mg.ctx.s) == 1
            assert scalar(engine, "SELECT count(*) FROM mini_depth_revision") == 0
        else:
            PostgresMiniDepthStore(engine).append_selection(
                revision(mg.ctx, lo=lo, hi=lo + timedelta(hours=1)), job_id=None, backfill=True)
            assert not mini_jobs(engine, mg.ctx.s)
        config = downgrade_config(mg.site_obj, engine)
        try:
            with pytest.raises(DBAPIError, match=REFUSED_BASIS if blocker == "cutover_basis" else REFUSED):
                command.downgrade(config, PREVIOUS)
            assert head(engine) == HEAD and catalog(engine) == (4, 3, 4, 1)  # nothing dropped
            assert (blocker == "job_only") == bool(mini_jobs(engine, mg.ctx.s))  # nothing deleted
            assert cutover_rows(engine, mg.ctx.s) == (1 if blocker == "cutover_basis" else 0)
        finally:
            clear_mini(engine)
            _replica(engine, "DELETE FROM site_cutover_basis")
            if head(engine) != HEAD:
                command.upgrade(config, "head")

    def test_cross_site_fk_and_selection_mismatch(self, mg4, engine) -> None:  # noqa: F811
        mg = mg4
        store = PostgresMiniDepthStore(engine)
        ctx = mg.ctx
        lo = datetime(2026, 10, 6, 9, tzinfo=timezone.utc)
        hi = lo + timedelta(hours=1)
        cause = mg.accept(role="feeder_demand", when=lo + timedelta(minutes=10), decided=hi + timedelta(minutes=5))
        job = next(j for j in mini_jobs(engine, ctx.s) if j["domain"] == "mini_service")
        assert (job["window_start"], job["window_end"], job["cause_evidence_id"]) == (lo, hi, cause)
        # A job of another domain or window, or no job outside an explicit backfill, is refused; nothing written.
        other = next(j for j in mini_jobs(engine, ctx.s) if j["domain"] == "mini_fuel" or j["domain"] == "mini_backup")
        for bad_job in (other["id"], uuid4()):
            with pytest.raises(MiniDepthWriteRefused, match="does not match"):
                store.append_selection(revision(ctx, lo=lo, hi=hi, evidence=[cause]), job_id=bad_job)
        with pytest.raises(MiniDepthWriteRefused, match="backfill"):
            store.append_selection(revision(ctx, lo=lo, hi=hi), job_id=None)
        with pytest.raises(MiniDepthWriteRefused, match="does not match"):
            store.append_selection(revision(ctx, lo=lo + timedelta(hours=1), hi=hi + timedelta(hours=1)),
                                   job_id=job["id"])
        # Evidence of no accepted row of this Site is refused by the scoped FK.
        with pytest.raises(MiniDepthWriteRefused, match="mini_depth_evidence_accepted_fk"):
            store.append_selection(revision(ctx, lo=lo, hi=hi, evidence=[uuid4()]), job_id=job["id"])
        assert scalar(engine, "SELECT count(*) FROM mini_depth_revision") == 0
        # The matching job: one revision, its exact evidence links and one selection with the job.
        first = store.append_selection(revision(ctx, lo=lo, hi=hi, evidence=[cause]), job_id=job["id"])
        assert not first.reused and first.seq > 0
        with engine.connect() as c:
            linked = c.execute(text("SELECT evidence_id FROM mini_depth_revision_evidence WHERE revision_id = :r"),
                               {"r": first.revision_id}).scalars().all()
            sel = c.execute(text("SELECT revision_id, job_id, domain, window_start, window_end FROM "
                                 "mini_depth_selection WHERE seq = :q"), {"q": first.seq}).one()
        assert linked == [cause] and tuple(sel) == (first.revision_id, job["id"], "service", lo, hi)
        # Identical digest: a later cutoff reuses the immutable revision with a new selection; an earlier is refused.
        again = store.append_selection(revision(ctx, lo=lo, hi=hi, evidence=[cause], cutoff=hi + timedelta(hours=3)),
                                       job_id=job["id"])
        assert again.reused and again.revision_id == first.revision_id and again.seq > first.seq
        with pytest.raises(MiniDepthWriteRefused, match="later knowledge cutoff"):
            store.append_selection(revision(ctx, lo=lo, hi=hi, evidence=[cause], cutoff=hi), job_id=job["id"])
        assert scalar(engine, "SELECT count(*) FROM mini_depth_revision") == 1
        # A selection naming the revision under another Site fails the composite FK; append-only on all three.
        with pytest.raises(DBAPIError, match="mini_depth_selection_revision_fk"):
            with engine.begin() as c:
                c.execute(text("INSERT INTO mini_depth_selection (tenant_id, site_id, domain, window_start, "
                               "window_end, revision_id, selected_at) VALUES (:t, :s2, 'service', :lo, :hi, :r, "
                               "now())"), ctx.p(s2=uuid4(), lo=lo, hi=hi, r=first.revision_id))
        for sql in ("UPDATE mini_depth_revision SET model_version = 'x'", "DELETE FROM mini_depth_revision_evidence",
                    "UPDATE mini_depth_selection SET job_id = NULL"):
            with pytest.raises(DBAPIError, match="append-only"):
                with engine.begin() as c:
                    c.execute(text(sql))

    def test_mini_enqueue_trigger_roles_equal_minigrid_roles_4_channels(self, mg, engine) -> None:  # noqa: F811
        body = functiondef(engine, "mini_enqueue_accepted")
        listed = re.search(r"NEW\.role IN \(([^)]*)\)", body).group(1)
        trigger_roles = re.findall(r"'([a-z_0-9]+)'", listed)
        assert len(trigger_roles) == len(set(trigger_roles)) == 17
        assert set(trigger_roles) == {r.role for r in MINIGRID_ROLES_4} - {"battery_reserve"}
        lo = datetime(2026, 10, 6, 9, tzinfo=timezone.utc)
        # An eligible MINIGRID accepted row without its same-transaction disposition fails the whole transaction.
        before = scalar(engine, "SELECT count(*) FROM accepted_evidence")
        with pytest.raises(DBAPIError) as refused:
            mg.accept(role="generator_power", when=lo, decided=lo, disposition=None)
        assert getattr(refused.value.orig, "sqlstate", None) == "23514"
        assert "same-transaction ACCEPTED disposition" in str(refused.value)
        assert scalar(engine, "SELECT count(*) FROM accepted_evidence") == before and not mini_jobs(engine, mg.ctx.s)
        # A shared-role accepted row on a non-MINIGRID Site enqueues no mini work.
        for site_type in ("COLDCHAIN", "EV_CHARGING"):
            with engine.begin() as c:
                set_type(c, mg.ctx.s, site_type)
                mg.write(c, role="generator_state", when=lo, decided=lo)
            with engine.begin() as c:
                set_type(c, mg.ctx.s, "MINIGRID")
            assert not mini_jobs(engine, mg.ctx.s)

    def test_mini_enqueue_domain_role_matrix(self, mg4, engine) -> None:  # noqa: F811
        mg = mg4
        body = functiondef(engine, "mini_enqueue_accepted")
        pairs = set(re.findall(r"\('(mini_[a-z]+)', '([a-z_0-9]+)'\)", body))
        assert pairs == {(d, r) for d, roles in MATRIX.items() for r in roles}
        noon = datetime(2026, 10, 6, 12, tzinfo=ZoneInfo(mg.tz)).astimezone(timezone.utc)
        decided = noon + timedelta(hours=2)
        channels = [r.role for r in MINIGRID_ROLES_4 if r.covered_by == "CHANNEL"]
        for role in channels:
            when = noon + timedelta(minutes=20)
            cause = mg.accept(role=role, when=when, decided=decided)
            got = Counter(j["domain"] for j in mini_jobs(engine, mg.ctx.s, cause=cause))
            expected = Counter(d for d, roles in MATRIX.items() if role in roles)
            assert got == expected, role
            for job in mini_jobs(engine, mg.ctx.s, cause=cause):
                assert (job["window_start"], job["window_end"], job["status"], job["available_at"]) == (
                    noon, noon + timedelta(hours=1), "PENDING", decided)
            clear_mini(engine)
        # Renewable work is the local noon hour only; other domains enqueue every intersected local hour.
        morning = noon - timedelta(hours=3)
        mg.accept(role="feeder_demand", when=morning, decided=decided)
        assert {j["domain"] for j in mini_jobs(engine, mg.ctx.s)} == {"mini_service", "mini_backup"}
        clear_mini(engine)
        # An event at an hour boundary belongs to the hour beginning there; a repeat coalesces into the PENDING job.
        mg.accept(role="generator_power", when=noon + timedelta(hours=1), decided=decided)
        mg.accept(role="generator_power", when=noon + timedelta(hours=1, minutes=30), decided=decided + timedelta(1))
        fuel = [j for j in mini_jobs(engine, mg.ctx.s) if j["domain"] == "mini_fuel"]
        assert [(j["window_start"], j["available_at"]) for j in fuel] == [
            (noon + timedelta(hours=1), decided + timedelta(1))]
        # Repeat on a COLDCHAIN or EV_CHARGING Site: zero mini jobs.
        clear_mini(engine)
        for site_type in ("COLDCHAIN", "EV_CHARGING"):
            with engine.begin() as c:
                set_type(c, mg.ctx.s, site_type)
                for role in ("feeder_demand", "generator_state", "generator_power"):
                    mg.write(c, role=role, when=noon, decided=decided)
            with engine.begin() as c:
                set_type(c, mg.ctx.s, "MINIGRID")
        assert not mini_jobs(engine, mg.ctx.s)

    def test_enqueue_hour_refuses_non_hour_and_wrong_domain(self, mg, engine) -> None:  # noqa: F811
        noon = datetime(2026, 10, 6, 12, tzinfo=ZoneInfo(mg.tz)).astimezone(timezone.utc)
        for domain, lo, hi in (("dispatch", noon, noon + timedelta(hours=1)),
                               ("mini_fuel", noon, noon + timedelta(minutes=30)),
                               ("mini_fuel", noon + timedelta(minutes=30), noon + timedelta(minutes=90)),
                               ("mini_renewable", noon + timedelta(hours=1), noon + timedelta(hours=2))):
            with pytest.raises(DBAPIError, match="mini_enqueue_hour"):
                with engine.begin() as c:
                    c.execute(text("SELECT mini_enqueue_hour(:t, :s, :d, :lo, :hi, NULL, now())"),
                              mg.ctx.p(d=domain, lo=lo, hi=hi))
        assert not mini_jobs(engine, mg.ctx.s)


class TestPublicationEnqueue:
    def test_configuration_enqueue_within_retention_and_rollback(self, mg4, engine) -> None:  # noqa: F811
        mg = mg4
        at = datetime(2026, 10, 10, 15, 30, tzinfo=timezone.utc)
        with engine.begin() as c:
            c.execute(text("SELECT mini_enqueue_configuration(:t, :s, :f, NULL, :at)"),
                      mg.ctx.p(f=datetime(2026, 1, 1, tzinfo=timezone.utc), at=at))
        jobs = mini_jobs(engine, mg.ctx.s)
        hours = local_hours(mg.tz, at - timedelta(days=5), at)
        noons = [h for h in hours if h[0].astimezone(ZoneInfo(mg.tz)).hour == 12]
        got = Counter(j["domain"] for j in jobs)
        assert got == Counter({"mini_service": len(hours), "mini_fuel": len(hours), "mini_backup": len(hours),
                               "mini_renewable": len(noons)})
        assert all(j["cause_evidence_id"] is None and j["available_at"] == at for j in jobs)
        assert {(j["window_start"], j["window_end"]) for j in jobs if j["domain"] == "mini_renewable"} == set(noons)
        clear_mini(engine)
        # A bounded change before the retention window enqueues nothing; a non-MINIGRID Site enqueues nothing.
        with engine.begin() as c:
            c.execute(text("SELECT mini_enqueue_configuration(:t, :s, :f, :to, :at)"),
                      mg.ctx.p(f=at - timedelta(days=9), to=at - timedelta(days=6), at=at))
            set_type(c, mg.ctx.s, "COLDCHAIN")
            c.execute(text("SELECT mini_enqueue_configuration(:t, :s, :f, NULL, :at)"),
                      mg.ctx.p(f=at - timedelta(days=1), at=at))
            set_type(c, mg.ctx.s, "MINIGRID")
        assert not mini_jobs(engine, mg.ctx.s)

    def test_foundation_publication_enqueues_and_rolls_back_on_enqueue_failure(self, mg4, engine) -> None:  # noqa: F811
        mg = mg4
        from test_s1_bindings_postgres import Clock

        from assetops_backend.sites.foundation_service import FoundationService

        runner = mg.site_obj.runner
        at = datetime(2026, 11, 2, 12, 0, tzinfo=timezone.utc)  # after the fixture's last Foundation change
        service = FoundationService(runner.store, "demo", Clock(at))

        def reserve(value: float) -> None:
            service.publish_battery_reserve(runner.result.tenant, runner.result.site, asset_code="battery",
                                            value=value, effective_from=at - timedelta(days=2), note=None)

        count = "SELECT count(*) FROM foundation_revision WHERE site_id = :s"
        original = functiondef(engine, "mini_enqueue_configuration")
        with engine.begin() as c:
            c.execute(text(
                "CREATE OR REPLACE FUNCTION mini_enqueue_configuration(p_tenant uuid, p_site uuid, "
                "p_effective_from timestamptz, p_effective_to timestamptz, p_at timestamptz) RETURNS void "
                "LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'w402 forced enqueue failure'; END; $$"))
        before = scalar(engine, count, s=mg.ctx.s)
        try:
            with pytest.raises(Exception, match="w402 forced enqueue failure"):
                reserve(35.0)
            assert scalar(engine, count, s=mg.ctx.s) == before and not mini_jobs(engine, mg.ctx.s)
        finally:
            with engine.begin() as c:
                c.execute(text(original))
        reserve(35.0)
        assert scalar(engine, count, s=mg.ctx.s) > before
        jobs = mini_jobs(engine, mg.ctx.s)
        assert {j["domain"] for j in jobs} == set(MINI)
        # Every inserted revision (a split's re-inserted earlier part included) enqueues within the retention only.
        assert all(j["cause_evidence_id"] is None and at - timedelta(days=5) < j["window_end"]
                   and j["window_start"] < at for j in jobs)


class TestRoles4Gate:
    """q8 ruling 1: `mini_enqueue_hour` is the common final gate; work exists only for an hour wholly covered by
    exactly one current `minigrid-roles-4` binding set. Roles-4 accepted evidence and publication (the four-domain
    mapping) are covered under `mg4` by the matrix and publication tests above."""

    def test_legacy_roles_accepted_evidence_and_publication_enqueue_nothing(self, mg, engine) -> None:  # noqa: F811
        with engine.connect() as c:
            sets = {r[0] for r in c.execute(text("SELECT role_set FROM signal_binding_set_revision WHERE site_id = :s "
                                                 "AND superseded_at IS NULL"), {"s": mg.ctx.s})}
        assert sets and "minigrid-roles-4" not in sets  # the legacy roles-1/2/3 Site
        noon = datetime(2026, 10, 6, 12, tzinfo=ZoneInfo(mg.tz)).astimezone(timezone.utc)
        for role in ("generator_power", "feeder_demand", "pv_power", "site_supply_state"):
            mg.accept(role=role, when=noon + timedelta(minutes=10), decided=noon + timedelta(hours=2))
        at = datetime(2026, 10, 10, 15, 30, tzinfo=timezone.utc)
        with engine.begin() as c:
            c.execute(text("SELECT mini_enqueue_configuration(:t, :s, :f, NULL, :at)"),
                      mg.ctx.p(f=datetime(2026, 1, 1, tzinfo=timezone.utc), at=at))
            # A direct call is a no-op, not a refusal and not a job destined for CONFIGURATION_MISSING.
            c.execute(text("SELECT mini_enqueue_hour(:t, :s, 'mini_fuel', :lo, :hi, NULL, now())"),
                      mg.ctx.p(lo=noon, hi=noon + timedelta(hours=1)))
        assert not mini_jobs(engine, mg.ctx.s)

    def test_hour_straddling_a_set_boundary_gets_no_job_and_no_lift(self, mg4, engine) -> None:  # noqa: F811
        mg = mg4
        noon = datetime(2026, 10, 6, 12, tzinfo=ZoneInfo(mg.tz)).astimezone(timezone.utc)
        with engine.connect() as c:
            (first_id, first_from), = c.execute(text(
                "SELECT id, valid_from FROM signal_binding_set_revision WHERE site_id = :s AND superseded_at IS NULL "
                "AND valid_from <= :lo AND (valid_to IS NULL OR valid_to >= :hi)"),
                {"s": mg.ctx.s, "lo": noon, "hi": noon + timedelta(hours=2)}).all()
        boundary = noon + timedelta(minutes=30)
        enqueue = "SELECT mini_enqueue_hour(:t, :s, 'mini_fuel', :lo, :hi, NULL, :at)"
        try:
            # The covering roles-4 set now begins inside the noon hour: noon is not wholly covered, 13:00 is.
            _replica(engine, f"UPDATE signal_binding_set_revision SET valid_from = '{boundary.isoformat()}' "
                             f"WHERE id = '{first_id}'")
            with engine.begin() as c:
                for lo in (noon, noon + timedelta(hours=1)):
                    c.execute(text(enqueue), mg.ctx.p(lo=lo, hi=lo + timedelta(hours=1), at=noon))
            assert [j["window_start"] for j in mini_jobs(engine, mg.ctx.s)] == [noon + timedelta(hours=1)]
            # Accepted evidence in the straddled hour enqueues nothing for it either.
            mg.accept(role="generator_power", when=noon + timedelta(minutes=40), decided=noon + timedelta(hours=2))
            assert [j["window_start"] for j in mini_jobs(engine, mg.ctx.s)] == [noon + timedelta(hours=1)]
            # An existing PENDING job of an hour that is no longer eligible is not lifted (recheck under the lock).
            stale = uuid4()
            with engine.begin() as c:
                c.execute(text("INSERT INTO recompute_job (id, tenant_id, site_id, domain, window_start, window_end, "
                               "status, available_at, created_at) VALUES (:id, :t, :s, 'mini_service', :lo, :hi, "
                               "'PENDING', :lo, :lo)"), mg.ctx.p(id=stale, lo=noon, hi=noon + timedelta(hours=1)))
                c.execute(text("SELECT mini_enqueue_hour(:t, :s, 'mini_service', :lo, :hi, NULL, :at)"),
                          mg.ctx.p(lo=noon, hi=noon + timedelta(hours=1), at=noon + timedelta(days=1)))
            assert scalar(engine, "SELECT available_at FROM recompute_job WHERE id = :i", i=stale) == noon
        finally:
            _replica(engine, f"UPDATE signal_binding_set_revision SET valid_from = '{first_from.isoformat()}' "
                             f"WHERE id = '{first_id}'")
