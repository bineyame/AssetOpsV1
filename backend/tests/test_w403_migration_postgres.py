"""W4-03 unit 1: migration `0030_w4_mini_decisions`, its exact catalog delta, downgrade refusals and store skeleton.

`.agent/W4-03-build-spec.md` original "Migration `0030_w4_mini_decisions`", closure 1 catalog/lock paragraph and
closure 4 S3/S4/S18/S19. The catalog is compared as exact name arrays from `pg_catalog`, not counts alone.
Requires ASSETOPS_TEST_DATABASE_URL.
"""

from __future__ import annotations

import hashlib
import importlib.util
import os
from datetime import date, datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError
    from test_s1_bindings_postgres import _alembic, engine, store  # noqa: F401
    from test_s4_consequence_store_postgres import site  # noqa: F401
    from test_w203_cold_migration_postgres import _replica, head, scalar
    from test_w206_ev_enqueue_postgres import Ev
    from test_w402_migration_postgres import downgrade_config

    from assetops_backend.mini_decisions.store import MiniDecisionWriteRefused, PostgresMiniDecisionStore

HEAD = "0030_w4_mini_decisions"
PREVIOUS = "0029_w4_mini_depth"
REFUSED_HISTORY = "Downgrade of 0030_w4_mini_decisions refused: decision history exists"
REFUSED_JOBS = "Downgrade of 0030_w4_mini_decisions refused: opportunity jobs exist"
REFUSED_STAGE = "Downgrade of 0030_w4_mini_decisions refused: OPPORTUNITY stage active"

#: Closure 1's child-to-parent lock/refusal/drop order.
TABLES = (
    "mini_decision_work_link", "mini_opportunity_scenario_link", "mini_opportunity_evidence",
    "mini_alternative_evidence", "mini_opportunity_selection", "mini_opportunity_revision",
    "mini_alternative_revision", "mini_scenario_revision", "mini_opportunity", "mini_scenario",
)
#: S4: exact FK names in the original SQL's table order (20, one unscoped job FK).
FKS = (
    "mini_scenario_site_fk", "mini_scenario_revision_scenario_fk", "mini_scenario_revision_previous_fk",
    "mini_alternative_revision_finding_fk", "mini_alternative_revision_finding_revision_fk",
    "mini_alternative_revision_previous_fk", "mini_alternative_evidence_revision_fk",
    "mini_alternative_evidence_accepted_fk", "mini_opportunity_site_fk", "mini_opportunity_revision_opportunity_fk",
    "mini_opportunity_evidence_revision_fk", "mini_opportunity_evidence_accepted_fk",
    "mini_opportunity_selection_opportunity_fk", "mini_opportunity_selection_revision_fk",
    "mini_opportunity_selection_job_id_fk", "mini_decision_work_link_case_fk", "mini_decision_work_link_scenario_fk",
    "mini_decision_work_link_opportunity_fk", "mini_opportunity_scenario_link_opportunity_fk",
    "mini_opportunity_scenario_link_scenario_fk",
)
#: S4: exact non-PK UNIQUE names (22).
UNIQUES = (
    "mini_scenario_scope_uk", "mini_scenario_public_no_uk", "mini_scenario_create_key_uk",
    "mini_scenario_revision_scope_uk", "mini_scenario_revision_no_uk", "mini_scenario_revision_previous_uk",
    "mini_scenario_revision_key_uk", "mini_alternative_revision_scope_uk", "mini_alternative_revision_version_uk",
    "mini_alternative_revision_previous_uk", "mini_alternative_revision_key_uk", "mini_opportunity_scope_uk",
    "mini_opportunity_public_no_uk", "mini_opportunity_study_uk", "mini_opportunity_revision_scope_uk",
    "mini_opportunity_revision_no_uk", "mini_opportunity_revision_input_uk", "mini_decision_work_link_case_scenario_uk",
    "mini_decision_work_link_case_opportunity_uk", "mini_decision_work_link_key_uk",
    "mini_opportunity_scenario_link_scope_uk", "mini_opportunity_scenario_link_key_uk",
)
INDEXES = ("mini_scenario_site_order", "mini_alternative_selected", "mini_opportunity_head",
           "mini_decision_work_case", "mini_opportunity_scenario_order")
_AUTHORED = ("actor_kind", "actor_id", "authorization_basis", "attestation", "idempotency_key", "payload_sha256")
#: S4: every CHECK is `<table>_<checked column or semantic role>_check`.
CHECKS = tuple(
    ["mini_scenario_create_key_check", "mini_scenario_create_payload_sha256_check",
     "mini_scenario_create_actor_id_check",
     "mini_scenario_revision_revision_no_check", "mini_scenario_revision_name_check",
     "mini_scenario_revision_kind_check", "mini_scenario_revision_correction_reason_check",
     "mini_scenario_revision_chain_check"]
    + [f"mini_scenario_revision_{c}_check" for c in _AUTHORED]
    + ["mini_alternative_revision_version_no_check", "mini_alternative_revision_rank_check",
       "mini_alternative_revision_rank_key_check", "mini_alternative_revision_disposition_check",
       "mini_alternative_revision_explanation_check", "mini_alternative_revision_evidence_summary_check",
       "mini_alternative_revision_missing_evidence_reason_check", "mini_alternative_revision_reason_check"]
    + [f"mini_alternative_revision_{c}_check" for c in _AUTHORED]
    + ["mini_opportunity_window_check", "mini_opportunity_revision_revision_no_check",
       "mini_opportunity_revision_input_sha256_check", "mini_decision_work_link_target_check"]
    + [f"mini_decision_work_link_{c}_check" for c in _AUTHORED]
    + [f"mini_opportunity_scenario_link_{c}_check" for c in _AUTHORED]
)
STAGES_AT_HEAD = "'IDLE'::text, 'S3'::text, 'MINI'::text, 'OPPORTUNITY'::text, 'S4'::text, 'CONSEQUENCE'::text"
STAGES_AT_0029 = "'IDLE'::text, 'S3'::text, 'MINI'::text, 'S4'::text, 'CONSEQUENCE'::text"


def _hex(label: str) -> str:
    return hashlib.sha256(label.encode()).hexdigest()


def constraints(engine, contype: str) -> list[str]:  # noqa: F811
    with engine.connect() as c:
        return sorted(c.execute(text(
            "SELECT conname FROM pg_constraint WHERE contype = :k AND conrelid IN "
            "(SELECT oid FROM pg_class WHERE relname = ANY(:t) AND relkind = 'r')"), {"k": contype, "t": list(TABLES)}
        ).scalars())


def catalog(engine) -> dict:  # noqa: F811
    with engine.connect() as c:
        tables = sorted(c.execute(text("SELECT relname FROM pg_class WHERE relkind = 'r' AND relname = ANY(:t)"),
                                  {"t": list(TABLES)}).scalars())
        indexes = sorted(c.execute(text("SELECT indexname FROM pg_indexes WHERE indexname = ANY(:i)"),
                                   {"i": list(INDEXES)}).scalars())
        triggers = sorted(c.execute(text(
            "SELECT tgname FROM pg_trigger WHERE NOT tgisinternal AND tgrelid IN "
            "(SELECT oid FROM pg_class WHERE relname = ANY(:t))"), {"t": list(TABLES)}).scalars())
        sequence = c.execute(text("SELECT count(*) FROM pg_class WHERE relkind = 'S' "
                                  "AND relname = 'mini_decision_public_no_seq'")).scalar_one()
        stage = c.execute(text("SELECT pg_get_constraintdef(oid) FROM pg_constraint "
                               "WHERE conname = 'schedule_site_head_stage_check'")).scalar_one()
    return {"tables": tables, "pk": constraints(engine, "p"), "uk": constraints(engine, "u"),
            "fk": constraints(engine, "f"), "ck": constraints(engine, "c"), "indexes": indexes,
            "triggers": triggers, "sequence": sequence, "stage": stage}


def expected_at_head() -> dict:
    return {"tables": sorted(TABLES), "pk": sorted(f"{t}_pkey" for t in TABLES), "uk": sorted(UNIQUES),
            "fk": sorted(FKS), "ck": sorted(CHECKS), "indexes": sorted(INDEXES),
            "triggers": sorted(f"{t}_immutable" for t in TABLES), "sequence": 1,
            "stage": f"CHECK ((stage = ANY (ARRAY[{STAGES_AT_HEAD}])))"}


def expected_at_0029() -> dict:
    return {"tables": [], "pk": [], "uk": [], "fk": [], "ck": [], "indexes": [], "triggers": [], "sequence": 0,
            "stage": f"CHECK ((stage = ANY (ARRAY[{STAGES_AT_0029}])))"}


def module_0030():
    path = Path(__file__).resolve().parents[1] / "migrations" / "versions" / "0030_w4_mini_decisions.py"
    spec = importlib.util.spec_from_file_location("m0030", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def authored(label: str) -> dict:
    return {"actor_kind": "USER", "actor_id": "user-1", "authorization_basis": "site-grant",
            "attestation": "I attest", "idempotency_key": f"key-{label}-0001", "payload_sha256": _hex(label)}


@pytest.fixture()
def ctx(site, engine):  # noqa: F811
    built = Ev(site, engine)
    built.site_obj = site
    yield built
    _replica(engine, *[f"DELETE FROM {t}" for t in TABLES],
             "DELETE FROM recompute_job WHERE domain = 'mini_opportunity'")


def scenario(store, c, tenant_id, site_id, label="a"):
    scenario_id = uuid4()
    store.insert_scenario(c, {"id": scenario_id, "tenant_id": tenant_id, "site_id": site_id,
                              "create_key": f"create-{label}-0001", "create_payload_sha256": _hex(label),
                              "create_actor_id": "user-1"})
    return scenario_id


def opportunity(store, c, tenant_id, site_id, *, first=date(2026, 10, 6)):
    opportunity_id, revision_id = uuid4(), uuid4()
    store.insert_opportunity(c, {"id": opportunity_id, "tenant_id": tenant_id, "site_id": site_id,
                                 "first_day": first, "last_day": date(first.year, first.month, first.day + 4),
                                 "model_version": "mini-opportunity/1"})
    store.insert_opportunity_revision(c, {
        "id": revision_id, "tenant_id": tenant_id, "site_id": site_id, "opportunity_id": opportunity_id,
        "revision_no": 1, "selected_hours": [], "result": {"status": "UNKNOWN"},
        "input_sha256": "sha256:" + _hex(str(revision_id)), "producer_id": "mini-decisions-worker",
        "model_version": "mini-opportunity/1"}, backfill=True)
    return opportunity_id, revision_id


def opportunity_job(engine, tenant_id, site_id, *, status="DONE") -> object:  # noqa: F811
    job_id = uuid4()
    lo = datetime(2026, 10, 5, 21, tzinfo=timezone.utc)
    with engine.begin() as c:
        c.execute(text("INSERT INTO recompute_job (id, tenant_id, site_id, domain, window_start, window_end, status, "
                       "available_at, created_at) VALUES (:i, :t, :s, 'mini_opportunity', :lo, :hi, :st, :lo, :lo)"),
                  {"i": job_id, "t": tenant_id, "s": site_id, "lo": lo, "hi": datetime(2026, 10, 10, 21,
                   tzinfo=timezone.utc), "st": status})
    return job_id


class TestMigration0030:
    def test_upgrade_single_head_exact_catalog_and_empty_downgrade(self, engine) -> None:  # noqa: F811
        from alembic import command
        from alembic.script import ScriptDirectory

        config = _alembic()
        script = ScriptDirectory.from_config(config)
        assert script.get_heads() == [HEAD] and script.get_revision(HEAD).down_revision == PREVIOUS
        assert head(engine) == HEAD and catalog(engine) == expected_at_head()
        assert (len(TABLES), len(UNIQUES), len(FKS), len(INDEXES)) == (10, 22, 20, 5)
        # S3/S4: the selection job FK is the one ordinary, unscoped reference to recompute_job(id).
        with engine.connect() as c:
            job_fk = c.execute(text(
                "SELECT confrelid::regclass::text, (SELECT array_agg(attname ORDER BY attname) FROM pg_attribute "
                "WHERE attrelid = conrelid AND attnum = ANY(conkey)) FROM pg_constraint "
                "WHERE conname = 'mini_opportunity_selection_job_id_fk'")).one()
            scoped = c.execute(text(
                "SELECT count(*) FROM pg_constraint WHERE contype = 'f' AND conname = ANY(:n) AND cardinality(conkey) "
                ">= 2"), {"n": list(FKS)}).scalar_one()
            source_job_fk = c.execute(text(
                "SELECT count(*) FROM pg_constraint c JOIN pg_attribute a ON a.attrelid = c.conrelid "
                "AND a.attnum = ANY(c.conkey) WHERE c.contype = 'f' AND a.attname = 'source_job_id'")).scalar_one()
        assert tuple(job_fk) == ("recompute_job", ["job_id"]) and scoped == 19 and source_job_fk == 0
        engine.dispose()
        try:
            command.downgrade(config, PREVIOUS)
            assert head(engine) == PREVIOUS and catalog(engine) == expected_at_0029()
            command.upgrade(config, "head")
        finally:
            if head(engine) != HEAD:
                command.upgrade(config, "head")
        assert head(engine) == HEAD and catalog(engine) == expected_at_head()

    def test_downgrade_locks_child_to_parent_before_counting(self, engine) -> None:  # noqa: F811
        """Closure 1: ACCESS EXCLUSIVE on the ten tables in the exact child-to-parent order, then the job and
        Site-head locks, all before any refusal check; a concurrent ACCESS SHARE holder makes it time out."""
        module = module_0030()
        locks = module.REFUSE_IF_USED.split("DO $$")[0]
        first = locks.splitlines()[0]
        assert first == f"LOCK TABLE {', '.join(TABLES)} IN ACCESS EXCLUSIVE MODE;"
        assert "LOCK TABLE recompute_job IN EXCLUSIVE MODE;" in locks
        assert "LOCK TABLE schedule_site_head IN EXCLUSIVE MODE;" in locks
        assert [line.split()[2].rstrip(";") for line in module.DROP.splitlines() if line.startswith("DROP TABLE")] == list(TABLES)
        assert module.DROP.rstrip().splitlines()[-1] == "DROP SEQUENCE mini_decision_public_no_seq;"
        holder = engine.connect()
        try:
            holding = holder.begin()
            holder.execute(text("LOCK TABLE mini_scenario IN ACCESS SHARE MODE"))
            with engine.connect() as c, c.begin():
                c.execute(text("SET LOCAL lock_timeout = '300ms'"))
                with pytest.raises(DBAPIError) as timed_out:
                    c.exec_driver_sql(module.REFUSE_IF_USED)
                assert getattr(timed_out.value.orig, "sqlstate", None) == "55P03"
            holding.rollback()
        finally:
            holder.close()
        assert head(engine) == HEAD and catalog(engine) == expected_at_head()

    @pytest.mark.parametrize("status", ["PENDING", "DONE", "FAILED"])
    def test_downgrade_refuses_job_only(self, status, ctx, engine) -> None:  # noqa: F811
        """S19: tables empty, one mini_opportunity job of any status refuses; nothing is deleted or relabelled."""
        from alembic import command

        job_id = opportunity_job(engine, ctx.ctx.t, ctx.ctx.s, status=status)
        assert all(scalar(engine, f"SELECT count(*) FROM {t}") == 0 for t in TABLES)
        config = downgrade_config(ctx.site_obj, engine)
        try:
            with pytest.raises(DBAPIError, match=REFUSED_JOBS):
                command.downgrade(config, PREVIOUS)
            assert head(engine) == HEAD and catalog(engine) == expected_at_head()
            assert scalar(engine, "SELECT domain || '/' || status FROM recompute_job WHERE id = :j",
                          j=job_id) == f"mini_opportunity/{status}"
        finally:
            if head(engine) != HEAD:
                command.upgrade(config, "head")

    def test_downgrade_refuses_active_opportunity_stage(self, ctx, engine) -> None:  # noqa: F811
        from alembic import command

        t, s = ctx.ctx.t, ctx.ctx.s
        with engine.begin() as c:
            c.execute(text("DELETE FROM schedule_site_head WHERE tenant_id = :t AND site_id = :s"), {"t": t, "s": s})
            c.execute(text("INSERT INTO schedule_site_head (tenant_id, site_id, stage, stage_started_at, created_at) "
                           "VALUES (:t, :s, 'OPPORTUNITY', clock_timestamp(), clock_timestamp())"), {"t": t, "s": s})
        config = downgrade_config(ctx.site_obj, engine)
        try:
            with pytest.raises(DBAPIError, match=REFUSED_STAGE):
                command.downgrade(config, PREVIOUS)
            assert head(engine) == HEAD and catalog(engine) == expected_at_head()
            assert scalar(engine, "SELECT stage FROM schedule_site_head WHERE site_id = :s", s=s) == "OPPORTUNITY"
        finally:
            with engine.begin() as c:
                c.execute(text("DELETE FROM schedule_site_head WHERE tenant_id = :t AND site_id = :s"),
                          {"t": t, "s": s})
            if head(engine) != HEAD:
                command.upgrade(config, "head")

    def test_downgrade_refuses_decision_history(self, ctx, engine) -> None:  # noqa: F811
        from alembic import command

        store = PostgresMiniDecisionStore(engine)
        with store.transaction() as c:
            scenario(store, c, ctx.ctx.t, ctx.ctx.s)
        config = downgrade_config(ctx.site_obj, engine)
        try:
            with pytest.raises(DBAPIError, match=REFUSED_HISTORY):
                command.downgrade(config, PREVIOUS)
            assert head(engine) == HEAD and catalog(engine) == expected_at_head()
            assert scalar(engine, "SELECT count(*) FROM mini_scenario") == 1
        finally:
            if head(engine) != HEAD:
                command.upgrade(config, "head")


class TestMiniDecisionStoreSkeleton:
    def test_inserts_service_checks_and_append_only(self, ctx, engine) -> None:  # noqa: F811
        store = PostgresMiniDecisionStore(engine)
        t, s = ctx.ctx.t, ctx.ctx.s
        with store.transaction() as c:
            scenario_id = scenario(store, c, t, s)
            store.insert_scenario_revision(c, {
                "id": uuid4(), "tenant_id": t, "site_id": s, "scenario_id": scenario_id, "revision_no": 1,
                "supersedes_revision_id": None, "name": "Stop SOC 40%", "kind": "STOP_SOC",
                "assumptions": {"unit": "%"}, "calculation": {"value": "40"}, "correction_reason": None,
                **authored("rev1")})
            opportunity_id, revision_id = opportunity(store, c, t, s)
        public_nos = [scalar(engine, f"SELECT public_no FROM {t_} WHERE site_id = :s", s=s)
                      for t_ in ("mini_scenario", "mini_opportunity")]
        assert public_nos[0] < public_nos[1]  # one shared public-number sequence
        good_job = opportunity_job(engine, t, s, status="LEASED")
        # S3/S4: a job of another Site (same tenant), a wrong-domain job and a null job outside backfill are refused.
        foreign_job = uuid4()
        _replica(engine, "INSERT INTO recompute_job (id, tenant_id, site_id, domain, window_start, window_end, status, "
                         f"available_at, created_at) VALUES ('{foreign_job}', '{t}', '{uuid4()}', 'mini_opportunity', "
                         "now(), now() + interval '1 day', 'PENDING', now(), now())")
        wrong_domain = uuid4()
        _replica(engine, "INSERT INTO recompute_job (id, tenant_id, site_id, domain, window_start, window_end, status, "
                         f"available_at, created_at) VALUES ('{wrong_domain}', '{t}', '{s}', 'mini_renewable', "
                         "now(), now() + interval '1 hour', 'PENDING', now(), now())")
        row = {"tenant_id": t, "site_id": s, "opportunity_id": opportunity_id, "revision_id": revision_id}
        for bad in (foreign_job, wrong_domain, uuid4()):
            with pytest.raises(MiniDecisionWriteRefused, match="does not match"):
                with store.transaction() as c:
                    store.insert_opportunity_selection(c, {**row, "job_id": bad})
        with pytest.raises(MiniDecisionWriteRefused, match="named backfill"):
            with store.transaction() as c:
                store.insert_opportunity_selection(c, {**row, "job_id": None})
        # A revision of another opportunity is refused by the service check.
        with pytest.raises(MiniDecisionWriteRefused, match="does not belong"):
            with store.transaction() as c:
                other_id, _ = opportunity(store, c, t, s, first=date(2026, 10, 1))
                store.insert_opportunity_selection(c, {**row, "opportunity_id": other_id, "job_id": good_job})
        assert scalar(engine, "SELECT count(*) FROM mini_opportunity_selection") == 0
        with store.transaction() as c:
            seq = store.insert_opportunity_selection(c, {**row, "job_id": good_job})
            backfill = store.insert_opportunity_selection(c, {**row, "job_id": None}, backfill=True)
        assert 0 < seq < backfill
        # The scoped FK refuses an alternative whose Finding is not of this Site; a work link names one target.
        with pytest.raises(MiniDecisionWriteRefused):
            with store.transaction() as c:
                store.insert_work_link(c, {"id": uuid4(), "tenant_id": t, "site_id": s, "case_id": uuid4(),
                                           "scenario_id": scenario_id, "opportunity_id": opportunity_id,
                                           **authored("link")})
        with pytest.raises(MiniDecisionWriteRefused, match="does not belong"):
            with store.transaction() as c:
                store.insert_alternative_revision(c, {"tenant_id": t, "site_id": s, "finding_id": uuid4(),
                                                      "finding_revision_id": uuid4()})
        with store.transaction() as c:
            store.insert_opportunity_scenario_link(c, {"id": uuid4(), "tenant_id": t, "site_id": s,
                                                       "opportunity_id": opportunity_id, "scenario_id": scenario_id,
                                                       **authored("osl")})
        # Append-only on the ten tables (existing ledger_append_only()).
        for sql in ("UPDATE mini_scenario SET create_actor_id = 'x'", "DELETE FROM mini_scenario_revision",
                    "UPDATE mini_opportunity_selection SET job_id = NULL", "DELETE FROM mini_opportunity_scenario_link"):
            with pytest.raises(DBAPIError, match="append-only"):
                with engine.begin() as c:
                    c.execute(text(sql))
        _replica(engine, f"DELETE FROM recompute_job WHERE id IN ('{foreign_job}', '{wrong_domain}')")

    def test_rank_key_pair_and_authored_bounds(self, ctx, engine) -> None:  # noqa: F811
        """S4: the fixed rank/key pair and authored key bounds are database CHECKs, refused before any service."""
        t, s = ctx.ctx.t, ctx.ctx.s
        with engine.connect() as c:
            names = c.execute(text("SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint WHERE conname IN "
                                   "('mini_alternative_revision_rank_key_check', "
                                   "'mini_decision_work_link_idempotency_key_check')")).all()
        defs = dict(names)
        assert "POLICY" in defs["mini_alternative_revision_rank_key_check"]
        assert "CAPABILITY" in defs["mini_alternative_revision_rank_key_check"]
        with pytest.raises(DBAPIError, match="mini_scenario_create_key_check"):
            with engine.begin() as c:
                c.execute(text("INSERT INTO mini_scenario (id, tenant_id, site_id, create_key, create_payload_sha256, "
                               "create_actor_id) VALUES (:i, :t, :s, 'short', :h, 'u')"),
                          {"i": uuid4(), "t": t, "s": s, "h": _hex("x")})
