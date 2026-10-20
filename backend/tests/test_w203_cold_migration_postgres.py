"""W2-03 commit 1: migration `0022_w2_cold_assessment` against Postgres.

`.agent/W2-03-build-spec.md` "Migration 0022": upgrade over existing mini-grid Findings keeps their rows,
reads and constraints; the three cold episode tables are scoped and append-only; episode key and basis are
unique; and downgrade refuses while any cold episode row or cold Finding exists, deleting nothing.
Requires ASSETOPS_TEST_DATABASE_URL.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError, IntegrityError
    from test_s1_bindings_postgres import _alembic, engine, store  # noqa: F401
    from test_s4_consequence_store_postgres import _release_connections, site  # noqa: F401

    from assetops_backend.analytics.adapters.postgres_finding_store import PostgresFindingStore

HEAD = "0027_w4_work_cases"  # W4-01: 0027 sits above 0026
PREVIOUS = "0021_w2_cold_config"
REFUSED = "Downgrade of 0022_w2_cold_assessment refused"
COLD = ("cold_episode", "cold_episode_revision", "cold_episode_evidence")
T0 = datetime(2026, 10, 6, 19, 0, tzinfo=timezone.utc)


def _sha(label: str) -> str:
    return hashlib.sha256(label.encode()).hexdigest()


def head(engine) -> str:  # noqa: F811
    with engine.connect() as c:
        return c.execute(text("SELECT version_num FROM alembic_version")).scalar_one()


def scalar(engine, sql, **params):  # noqa: F811
    with engine.connect() as c:
        return c.execute(text(sql), params).scalar()


def table_exists(engine, name) -> bool:  # noqa: F811
    return bool(scalar(engine, "SELECT to_regclass(:n) IS NOT NULL", n=name))


def column(engine, table, name):  # noqa: F811
    with engine.connect() as c:
        row = c.execute(text("SELECT is_nullable, column_default FROM information_schema.columns "
                             "WHERE table_name = :t AND column_name = :c"), {"t": table, "c": name}).first()
    return None if row is None else tuple(row)


def constraint(engine, name):  # noqa: F811
    return scalar(engine, "SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conname = :n", n=name)


def _replica(engine, *statements) -> None:  # noqa: F811
    """Test-only cleanup of rows this test created: the replica role skips the append-only trigger."""
    with engine.begin() as c:
        c.execute(text("SET LOCAL session_replication_role = replica"))
        for sql in statements:
            c.execute(text(sql))


# W2-04 (0023) triggers enqueue cold consequence work for every cold episode/Finding revision; 0023's own downgrade
# refuses while that work exists, so a 0022 downgrade test clears it first to exercise 0022's refusal.
CLEAR_W204 = ("DELETE FROM cold_consequence_work_attempt", "DELETE FROM cold_consequence_evidence",
              "DELETE FROM cold_consequence_revision", "DELETE FROM cold_consequence_work")


def remove_cold(engine) -> None:  # noqa: F811
    _replica(engine, *CLEAR_W204, "DELETE FROM cold_episode_evidence", "DELETE FROM cold_episode_revision",
             "DELETE FROM cold_episode",
             "DELETE FROM finding_revision WHERE domain = 'cold_chain'",
             "DELETE FROM finding WHERE domain = 'cold_chain'")


def _copy(c, table, where, **override) -> None:  # noqa: F811
    """INSERT a copy of the one `table` row matching `where`, with `override` column -> SQL expression."""
    cols = [r[0] for r in c.execute(text(
        "SELECT column_name FROM information_schema.columns WHERE table_name = :t ORDER BY ordinal_position"),
        {"t": table})]
    exprs = ", ".join(override.get(col, col) for col in cols)
    c.execute(text(f"INSERT INTO {table} ({', '.join(cols)}) SELECT {exprs} FROM {table} WHERE {where}"))


def cold_room_assessment(engine, ctx, assessment):  # noqa: F811
    """W2-04 Q1: a copy of `assessment` (and its run) whose run Foundation basis names exactly one COLD_ROOM, the
    Site asset `ctx.assets[0]`, so 0023 resolves the chamber room. The Foundation row is superseded and valid only
    in 2000, so no current or historical Site read selects it."""
    fid, rid, aid = uuid4(), uuid4(), uuid4()
    with engine.begin() as c:
        code = c.execute(text("SELECT asset_code FROM asset WHERE id = :a"), {"a": ctx.assets[0]}).scalar_one()
        version = c.execute(text("SELECT coalesce(max(version), 0) + 1000 FROM foundation_revision "
                                 "WHERE site_id = :s"), {"s": ctx.s}).scalar_one()
        content = json.dumps({"components": [{"component_type": "COLD_ROOM", "component_id": code}]})
        c.execute(text(
            "INSERT INTO foundation_revision (id, tenant_id, site_id, version, valid_from, valid_to, recorded_at, "
            "superseded_at, schema_version, content, content_sha256, origin, derived_from_revision_id, change_note) "
            "VALUES (:i, :t, :s, :v, '2000-01-01T00:00:00Z', '2000-01-02T00:00:00Z', '2000-01-01T00:00:00Z', "
            "'2000-01-01T00:00:00Z', 1, CAST(:c AS jsonb), :h, 'IMPORT', NULL, 'W2-04 test chamber-room basis')"),
            ctx.p(i=fid, v=version, c=content, h=_sha(content)))
        run = c.execute(text("SELECT analytic_run_id FROM assessment_revision WHERE id = :a"),
                        {"a": assessment}).scalar_one()
        _copy(c, "analytic_run", f"id = '{run}'", id=f"'{rid}'::uuid",
              foundation_revision_ids=f"jsonb_build_array('{fid}')", input_sha256=f"'{_sha(str(rid))}'")
        _copy(c, "assessment_revision", f"id = '{assessment}'", id=f"'{aid}'::uuid",
              analytic_run_id=f"'{rid}'::uuid", assessment_key=f"assessment_key || '-w204-room-{aid}'")
    return aid, rid


class Ctx:
    """Existing ids of the mini-grid Site: a probe-like asset, a selected assessment, its run and evidence.

    W2-04: `assessment`/`run` are a copy whose Foundation basis names `assets[0]` as the one chamber room (0023 Q1);
    `mini_assessment` is the original, which resolves no room."""

    def __init__(self, site, engine) -> None:  # noqa: F811
        self.t, self.s = site.tenant, site.site
        with engine.connect() as c:
            self.assets = [r[0] for r in c.execute(text(
                "SELECT id FROM asset WHERE site_id = :s ORDER BY id"), {"s": self.s})]
            self.assessment, self.run = c.execute(text(
                "SELECT id, analytic_run_id FROM assessment_revision WHERE site_id = :s ORDER BY id LIMIT 1"),
                {"s": self.s}).one()
            self.evidence = [r[0] for r in c.execute(text(
                "SELECT id FROM accepted_evidence WHERE site_id = :s ORDER BY id LIMIT 3"), {"s": self.s})]
        assert len(self.assets) >= 2 and len(self.evidence) == 3
        self.mini_assessment, self.room = self.assessment, self.assets[0]
        self.assessment, self.run = cold_room_assessment(engine, self, self.mini_assessment)

    def p(self, **kw) -> dict:
        return {"t": self.t, "s": self.s, **kw}


def insert_episode(engine, ctx, *, key="anchor-1", asset=None, split=None, episode_id=None):  # noqa: F811
    eid = episode_id or uuid4()
    with engine.begin() as c:
        c.execute(text(
            "INSERT INTO cold_episode (id, tenant_id, site_id, kind, asset_id, anchor_time, episode_key_sha256, "
            "split_from_episode_id, finding_id, created_at) VALUES (:i, :t, :s, 'EXCURSION', :a, :at, :k, :sp, "
            "NULL, now())"),
            ctx.p(i=eid, a=asset or ctx.assets[0], at=T0 + timedelta(minutes=15), k=_sha(key), sp=split))
    return eid


def insert_revision(engine, ctx, episode_id, *, n=1, basis="basis-1", assessment=None, **over):  # noqa: F811
    rid = uuid4()
    cols = {"lower_start": T0 + timedelta(minutes=10), "upper_start": T0 + timedelta(minutes=15),
            "lower_end": None, "upper_end": None, "duration_low": "45", "duration_high": None,
            "degree_minutes_low": "30", "degree_minutes_high": "60", "peak_observed": "9.5",
            "coverage": "1.0000", "missing_steps": "[]", "claim_level": "BOUNDED"}
    cols.update(over)
    with engine.begin() as c:
        c.execute(text(
            "INSERT INTO cold_episode_revision (id, tenant_id, site_id, episode_id, revision_no, "
            "assessment_revision_id, basis_sha256, claim_level, lower_start, upper_start, lower_end, upper_end, "
            "duration_low, duration_high, degree_minutes_low, degree_minutes_high, peak_observed, coverage, "
            "missing_steps, created_at) VALUES (:i, :t, :s, :e, :n, :ar, :b, :claim_level, :lower_start, "
            ":upper_start, :lower_end, :upper_end, :duration_low, :duration_high, :degree_minutes_low, "
            ":degree_minutes_high, :peak_observed, :coverage, CAST(:missing_steps AS jsonb), now())"),
            ctx.p(i=rid, e=episode_id, n=n, ar=assessment or ctx.assessment, b=_sha(basis), **cols))
    return rid


def insert_link(engine, ctx, revision_id, evidence_id, use="SUPPORT", *, site_id=None):  # noqa: F811
    with engine.begin() as c:
        c.execute(text(
            "INSERT INTO cold_episode_evidence (episode_revision_id, tenant_id, site_id, evidence_id, use, reason) "
            "VALUES (:r, :t, :s, :e, :u, NULL)"),
            {"t": ctx.t, "s": site_id or ctx.s, "r": revision_id, "e": evidence_id, "u": use})


def insert_cold_finding(engine, ctx, *, generator=None, subject="asset", minutes=None,  # noqa: F811
                        revision_domain="cold_chain", episode=(None, None)):
    fid = uuid4()
    with engine.begin() as c:
        c.execute(text(
            "INSERT INTO finding (id, tenant_id, site_id, finding_key, domain, mechanism, analytic_id, "
            "generator_asset_id, subject_asset_id, anchor_start, anchor_assessment_revision_id, cohort_sha256, "
            "matcher_version, opened_at, created_at) VALUES (:i, :t, :s, :k, 'cold_chain', 'COLD_EXCURSION', "
            "'cold-excursion/1', :g, :sub, :at, :ar, NULL, 'cold-episode/1', now(), now())"),
            ctx.p(i=fid, k=f"cold:{fid}", g=generator, sub=ctx.assets[0] if subject == "asset" else subject,
                  at=T0, ar=ctx.assessment))
        c.execute(text(
            "INSERT INTO finding_revision (id, tenant_id, site_id, finding_id, domain, revision_no, transition, "
            "lifecycle, claim_level, title, mechanism, matcher_version, analytic_id, model_version, "
            "assessment_revision_id, analytic_run_id, episode_start, episode_end, candidate_minutes, "
            "necessary_minutes, indeterminate_minutes, claim, limitations, basis_sha256, support_sha256, "
            "cited_evidence_sha256, input_evidence_sha256, created_at) VALUES (:i, :t, :s, :f, :d, 1, 'OPENED', "
            "'SUPPORTED', 'BOUNDED', 'Cold excursion', 'COLD_EXCURSION', 'cold-episode/1', 'cold-excursion/1', "
            "'1', :ar, :run, :es, :ee, :m, :m, :m, '{}'::jsonb, '[]'::jsonb, :b, :b, :b, :b, now())"),
            ctx.p(i=uuid4(), f=fid, d=revision_domain, ar=ctx.assessment, run=ctx.run, es=episode[0],
                  ee=episode[1], m=minutes, b=_sha(f"cold-finding:{fid}")))
    return fid


def minigrid_rows(engine) -> dict:  # noqa: F811
    with engine.connect() as c:
        return {
            "finding": [tuple(r) for r in c.execute(text(
                "SELECT id, domain, generator_asset_id, anchor_start, finding_key FROM finding ORDER BY id"))],
            "finding_revision": [tuple(r) for r in c.execute(text(
                "SELECT id, finding_id, revision_no, episode_start, episode_end, candidate_minutes, "
                "necessary_minutes, indeterminate_minutes, basis_sha256 FROM finding_revision ORDER BY id"))],
        }


class TestMigration0022:
    def test_upgrade_preserves_minigrid_and_constraints(self, site, engine) -> None:  # noqa: F811
        from alembic import command

        ctx = Ctx(site, engine)
        analytic_id = scalar(engine, "SELECT analytic_id FROM finding WHERE site_id = :s LIMIT 1", s=ctx.s)
        reader = PostgresFindingStore(URL)

        def reads():
            return reader.index_snapshot(ctx.t, ctx.s, "mini_grid", analytic_id)

        before_rows, before_reads = minigrid_rows(engine), reads()
        assert before_rows["finding"] and before_rows["finding_revision"]
        assert head(engine) == HEAD
        config = _alembic()
        reader._engine.dispose()
        engine.dispose()
        try:
            command.downgrade(config, PREVIOUS)
            assert head(engine) == PREVIOUS
            assert not any(table_exists(engine, t) for t in COLD)
            assert column(engine, "finding", "subject_asset_id") is None
            assert column(engine, "finding_revision", "domain") is None
            assert column(engine, "finding", "generator_asset_id")[0] == "NO"
            assert [column(engine, "finding_revision", c)[0] for c in (
                "episode_start", "episode_end", "candidate_minutes", "necessary_minutes",
                "indeterminate_minutes")] == ["NO"] * 5
            assert constraint(engine, "finding_revision_bounds") == "CHECK ((episode_start <= episode_end))"
            assert "REFERENCES finding(tenant_id, site_id, id)" in constraint(engine, "finding_revision_finding_fk")
            assert minigrid_rows(engine) == before_rows
            command.upgrade(config, "head")
        finally:
            if head(engine) != HEAD:
                command.upgrade(config, "head")
        assert head(engine) == HEAD and all(table_exists(engine, t) for t in COLD)
        assert minigrid_rows(engine) == before_rows and reads() == before_reads
        assert scalar(engine, "SELECT count(*) FROM finding_revision WHERE domain <> 'mini_grid'") == 0
        assert column(engine, "finding_revision", "domain") == ("NO", None)  # backfilled, default removed
        assert column(engine, "finding", "generator_asset_id")[0] == "YES"
        assert column(engine, "finding", "subject_asset_id")[0] == "YES"
        assert constraint(engine, "finding_revision_finding_fk") is None
        assert "(tenant_id, site_id, finding_id, domain)" in constraint(engine, "finding_revision_finding_domain_fk")
        assert scalar(engine, "SELECT count(*) FROM pg_indexes WHERE indexname = 'finding_domain_subject_anchor'") == 1

        (fid, rid) = before_rows["finding_revision"][0][1], before_rows["finding_revision"][0][0]
        # Mini-grid shape stays required: a NULL generator, NULL bounds or NULL/negative minutes are refused.
        for sql, name in (
            ("INSERT INTO finding (id, tenant_id, site_id, finding_key, domain, mechanism, analytic_id, "
             "generator_asset_id, anchor_start, anchor_assessment_revision_id, matcher_version, opened_at, "
             "created_at) SELECT gen_random_uuid(), tenant_id, site_id, finding_key || '-x', domain, mechanism, "
             "analytic_id, NULL, anchor_start, anchor_assessment_revision_id, matcher_version, opened_at, "
             "created_at FROM finding WHERE id = :f", "finding_domain_subject"),
            ("INSERT INTO finding (id, tenant_id, site_id, finding_key, domain, mechanism, analytic_id, "
             "generator_asset_id, subject_asset_id, anchor_start, anchor_assessment_revision_id, matcher_version, "
             "opened_at, created_at) SELECT gen_random_uuid(), tenant_id, site_id, finding_key || '-y', domain, "
             "mechanism, analytic_id, generator_asset_id, :a, anchor_start, anchor_assessment_revision_id, "
             "matcher_version, opened_at, created_at FROM finding WHERE id = :f", "finding_domain_subject"),
        ):
            with pytest.raises(IntegrityError, match=name):
                with engine.begin() as c:
                    c.execute(text(sql), {"f": fid, "a": ctx.assets[0]})
        for override, name in (
            ("episode_start = NULL", "finding_revision_minigrid_bounds"),
            ("candidate_minutes = NULL", "finding_revision_domain_minutes"),
            ("necessary_minutes = -1", "finding_revision_domain_minutes"),
            ("episode_start = episode_end + interval '1 minute'", "finding_revision_bounds"),
            ("domain = 'cold_chain', candidate_minutes = NULL, necessary_minutes = NULL, "
             "indeterminate_minutes = NULL", "finding_revision_finding_domain_fk"),
        ):
            with pytest.raises(IntegrityError, match=name):
                with engine.begin() as c:
                    c.execute(text("CREATE TEMP TABLE fr_copy ON COMMIT DROP AS SELECT * FROM finding_revision "
                                   "WHERE id = :r"), {"r": rid})
                    c.execute(text(f"UPDATE fr_copy SET id = gen_random_uuid(), revision_no = revision_no + 100, "
                                   f"basis_sha256 = repeat('e', 64), {override}"))
                    c.execute(text("INSERT INTO finding_revision SELECT * FROM fr_copy"))
        # The cold shape: subject required, generator NULL, all three minute fields NULL, bounds may be NULL.
        insert_cold_finding(engine, ctx)
        for kw, name in (({"generator": "gen-1"}, "finding_domain_subject"),
                         ({"subject": None}, "finding_domain_subject"),
                         ({"minutes": "0"}, "finding_revision_domain_minutes"),
                         ({"revision_domain": "mini_grid", "minutes": "0", "episode": (T0, T0)},
                          "finding_revision_finding_domain_fk"),
                         ({"episode": (T0 + timedelta(minutes=5), T0)}, "finding_revision_bounds")):
            with pytest.raises(IntegrityError, match=name):
                insert_cold_finding(engine, ctx, **kw)
        remove_cold(engine)

    def test_fuel_trigger_is_mini_grid_only(self, site, engine) -> None:  # noqa: F811
        """D-2026-10-18-w2-03-answers Q1: a cold revision with NULL bounds queues no fuel work; mini-grid still does."""
        ctx = Ctx(site, engine)
        assert "WHEN ((new.domain = 'mini_grid'::text))" in scalar(
            engine, "SELECT pg_get_triggerdef(oid) FROM pg_trigger "
            "WHERE tgname = 'financial_consequence_dirty_on_finding_revision'")
        work = "SELECT count(*) FROM financial_consequence_work w JOIN finding_revision r ON r.id = w.finding_revision_id"
        before = scalar(engine, work)
        fid = insert_cold_finding(engine, ctx)
        assert scalar(engine, "SELECT count(*) FROM finding_revision WHERE finding_id = :f AND episode_start IS NULL "
                      "AND episode_end IS NULL", f=fid) == 1
        assert scalar(engine, work + " WHERE r.domain = 'cold_chain'") == 0
        assert scalar(engine, work) == before
        new_rid = uuid4()
        try:
            with engine.begin() as c:
                c.execute(text("CREATE TEMP TABLE fr_copy ON COMMIT DROP AS SELECT * FROM finding_revision "
                               "WHERE domain = 'mini_grid' ORDER BY id LIMIT 1"))
                c.execute(text("UPDATE fr_copy SET id = :r, revision_no = revision_no + 100, "
                               "basis_sha256 = repeat('d', 64)"), {"r": new_rid})
                c.execute(text("INSERT INTO finding_revision SELECT * FROM fr_copy"))
            assert scalar(engine, "SELECT count(*) FROM financial_consequence_work WHERE finding_revision_id = :r "
                          "AND cause = 'FINDING_REVISION_APPENDED'", r=new_rid) == 1
        finally:
            _replica(engine, f"DELETE FROM financial_consequence_work WHERE finding_revision_id = '{new_rid}'",
                     f"DELETE FROM finding_revision WHERE id = '{new_rid}'")
            remove_cold(engine)

    def test_scoped_fk_and_append_only(self, site, engine) -> None:  # noqa: F811
        ctx = Ctx(site, engine)
        episode = insert_episode(engine, ctx)
        revision = insert_revision(engine, ctx, episode)
        insert_link(engine, ctx, revision, ctx.evidence[0], "SUPPORT")
        insert_link(engine, ctx, revision, ctx.evidence[1], "CONTEXT")
        insert_link(engine, ctx, revision, ctx.evidence[1], "EXCLUDED")  # (revision, evidence, use) is the key
        child = insert_episode(engine, ctx, key="anchor-2", split=episode)
        assert scalar(engine, "SELECT split_from_episode_id FROM cold_episode WHERE id = :i", i=child) == episode

        # Scoped composite FKs: another Site's scope, an unknown asset, split or evidence are refused.
        other_site = uuid4()
        for call, name in (
            (lambda: insert_episode(engine, ctx, key="x1", asset=uuid4()), "cold_episode_asset_fk"),
            (lambda: insert_episode(engine, ctx, key="x2", split=uuid4()), "cold_episode_split_fk"),
            (lambda: insert_revision(engine, ctx, uuid4(), basis="x3"), "cold_episode_revision_episode_fk"),
            (lambda: insert_link(engine, ctx, revision, uuid4()), "cold_episode_evidence_evidence_fk"),
            (lambda: insert_link(engine, ctx, revision, ctx.evidence[2], site_id=other_site),
             "cold_episode_evidence_(revision|evidence)_fk"),
        ):
            with pytest.raises(IntegrityError, match=name):
                call()
        with pytest.raises(IntegrityError, match="cold_episode_finding_fk"):
            with engine.begin() as c:
                c.execute(text("INSERT INTO cold_episode (id, tenant_id, site_id, kind, asset_id, anchor_time, "
                               "episode_key_sha256, finding_id, created_at) VALUES (gen_random_uuid(), :t, :s, "
                               "'START_RESPONSE', :a, now(), :k, :f, now())"),
                          ctx.p(a=ctx.assets[1], k=_sha("x4"), f=uuid4()))

        # Value CHECKs: closed vocabularies, ordered bounds, nonnegative ordered numeric pairs, array shape, peak.
        for over, name in (
            ({"claim_level": "LIKELY"}, "cold_episode_revision_claim_level_check"),
            ({"lower_start": T0 + timedelta(minutes=20)}, "cold_episode_revision_start_order"),
            ({"lower_end": T0 + timedelta(minutes=50), "upper_end": T0 + timedelta(minutes=40)},
             "cold_episode_revision_end_order"),
            ({"duration_low": "-1"}, "cold_episode_revision_duration"),
            ({"duration_low": "50", "duration_high": "40"}, "cold_episode_revision_duration"),
            ({"degree_minutes_low": "70"}, "cold_episode_revision_degree_minutes"),
            ({"degree_minutes_high": "-1", "degree_minutes_low": None}, "cold_episode_revision_degree_minutes"),
            ({"missing_steps": '{"step": "TRANSFER_RESULT"}'}, "cold_episode_revision_missing_steps_array"),
            ({"coverage": "0", "peak_observed": "9.5"}, "cold_episode_revision_peak_needs_point"),
            ({"coverage": "1.5"}, "cold_episode_revision_coverage_check"),
        ):
            with pytest.raises(IntegrityError, match=name):
                insert_revision(engine, ctx, episode, n=9, basis=f"check-{name}-{len(over)}", **over)
        with pytest.raises(IntegrityError, match="cold_episode_evidence_use_check"):
            insert_link(engine, ctx, revision, ctx.evidence[2], "CITED")
        with pytest.raises(IntegrityError, match="cold_episode_kind_check"):
            with engine.begin() as c:
                c.execute(text("INSERT INTO cold_episode (id, tenant_id, site_id, kind, asset_id, anchor_time, "
                               "episode_key_sha256, created_at) VALUES (gen_random_uuid(), :t, :s, 'SPOILAGE', "
                               ":a, now(), :k, now())"), ctx.p(a=ctx.assets[0], k=_sha("x5")))
        # An unknown open episode: NULL bounds, NULL peak with zero coverage and a missing step are accepted.
        insert_revision(engine, ctx, child, basis="unknown", claim_level="UNKNOWN", lower_start=None,
                        upper_start=None, duration_low=None, degree_minutes_low=None, degree_minutes_high=None,
                        peak_observed=None, coverage="0", missing_steps='["TRANSFER_RESULT"]')

        # Append-only: UPDATE and DELETE are refused on all three tables, with no upsert path either.
        for table, where in (("cold_episode", f"id = '{episode}'"), ("cold_episode_revision", f"id = '{revision}'"),
                             ("cold_episode_evidence", f"episode_revision_id = '{revision}'")):
            for sql in (f"UPDATE {table} SET site_id = site_id WHERE {where}", f"DELETE FROM {table} WHERE {where}"):
                with pytest.raises(DBAPIError, match="append-only"):
                    with engine.begin() as c:
                        c.execute(text(sql))
        with pytest.raises(DBAPIError, match="append-only"):
            with engine.begin() as c:
                c.execute(text(
                    "INSERT INTO cold_episode (id, tenant_id, site_id, kind, asset_id, anchor_time, "
                    "episode_key_sha256, created_at) SELECT id, tenant_id, site_id, kind, asset_id, anchor_time, "
                    "episode_key_sha256, created_at FROM cold_episode WHERE id = :i "
                    "ON CONFLICT (id) DO UPDATE SET anchor_time = EXCLUDED.anchor_time"), {"i": episode})
        assert scalar(engine, "SELECT count(*) FROM cold_episode_evidence WHERE episode_revision_id = :r",
                      r=revision) == 3
        remove_cold(engine)

    def test_duplicate_episode_basis(self, site, engine) -> None:  # noqa: F811
        ctx = Ctx(site, engine)
        episode = insert_episode(engine, ctx)
        insert_revision(engine, ctx, episode, n=1, basis="basis-1")
        with pytest.raises(IntegrityError, match="cold_episode_key_unique"):
            insert_episode(engine, ctx, key="anchor-1", asset=ctx.assets[1])
        with pytest.raises(IntegrityError, match="cold_episode_revision_basis_unique"):
            insert_revision(engine, ctx, episode, n=2, basis="basis-1")
        with pytest.raises(IntegrityError, match="cold_episode_revision_no_unique"):
            insert_revision(engine, ctx, episode, n=1, basis="basis-2")
        with pytest.raises(IntegrityError, match="cold_episode_revision_revision_no_check"):
            insert_revision(engine, ctx, episode, n=0, basis="basis-0")
        insert_revision(engine, ctx, episode, n=2, basis="basis-2")  # a changed basis appends
        other = insert_episode(engine, ctx, key="anchor-2")
        insert_revision(engine, ctx, other, n=1, basis="basis-1")  # basis is unique per episode only
        assert scalar(engine, "SELECT count(*) FROM cold_episode_revision") == 3
        remove_cold(engine)

    def test_downgrade_refuses_live_cold(self, site, engine) -> None:  # noqa: F811
        from alembic import command

        ctx = Ctx(site, engine)
        config = _alembic()
        before = minigrid_rows(engine)
        engine.dispose()
        try:
            episode = insert_episode(engine, ctx)
            revision = insert_revision(engine, ctx, episode)
            insert_link(engine, ctx, revision, ctx.evidence[0])
            for blocker in ("cold_episode_evidence", "cold_episode_revision", "cold_episode"):
                counts = {t: scalar(engine, f"SELECT count(*) FROM {t}") for t in COLD}
                _replica(engine, *CLEAR_W204)
                with pytest.raises(DBAPIError, match=REFUSED):
                    command.downgrade(config, PREVIOUS)
                assert head(engine) == HEAD  # the whole downgrade rolled back
                assert {t: scalar(engine, f"SELECT count(*) FROM {t}") for t in COLD} == counts  # nothing deleted
                _replica(engine, f"DELETE FROM {blocker}")
            insert_cold_finding(engine, ctx)  # a cold Finding alone blocks too
            _replica(engine, *CLEAR_W204)
            with pytest.raises(DBAPIError, match=REFUSED):
                command.downgrade(config, PREVIOUS)
            assert head(engine) == HEAD
            assert scalar(engine, "SELECT count(*) FROM finding WHERE domain = 'cold_chain'") == 1
            remove_cold(engine)
            command.downgrade(config, PREVIOUS)
            assert head(engine) == PREVIOUS and minigrid_rows(engine) == before
            trigger = scalar(engine, "SELECT pg_get_triggerdef(oid) FROM pg_trigger "
                             "WHERE tgname = 'financial_consequence_dirty_on_finding_revision'")
            assert trigger and " WHEN " not in trigger  # the original unconditional 0011 trigger is back
        finally:
            if head(engine) != HEAD:
                command.upgrade(config, "head")
        assert head(engine) == HEAD and minigrid_rows(engine) == before
