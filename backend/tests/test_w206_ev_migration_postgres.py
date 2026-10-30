"""W2-06 commit 1: migration `0025_w2_ev_session` against Postgres.

`.agent/W2-06-build-spec.md` "Pre-build closure (2026-10-19)" 0025 DDL: four tenant/Site-scoped append-only EV session
tables, the widened `finding_domain_subject` / `finding_revision_domain_minutes` checks (mini_grid and cold_chain arms
unchanged), and a guarded downgrade that refuses while EV rows, EV Findings or `ev_charging` jobs exist and otherwise
restores the exact 0022 checks. Schema-level only: no analytic row here is produced by the product writer (commit 3).
Requires ASSETOPS_TEST_DATABASE_URL.
"""

from __future__ import annotations

import os
from datetime import timedelta
from uuid import uuid4

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError, IntegrityError
    from test_s1_bindings_postgres import _alembic, engine, store  # noqa: F401
    from test_s4_consequence_store_postgres import _release_connections, site, site_before_0029  # noqa: F401
    from test_w203_cold_migration_postgres import (
        T0, _replica, _sha, constraint, head, minigrid_rows, scalar, table_exists)

HEAD = "0038_out_objectives"  # W5-04a: 0035 sits above 0034; W5-03b: 0034 sits above 0033; W5-02a: 0033 sits above 0032 (W5-01b above 0030)
PREVIOUS = "0024_w2_ev_config"
REFUSED = "Downgrade of 0025_w2_ev_session refused"
EV = ("ev_session", "ev_session_revision", "ev_session_evidence", "ev_meter_interval")


class Ctx:
    """Existing ids of the mini-grid Site fixture: two assets (charger/connector stand-ins), a selected assessment,
    its run and three accepted evidence rows. The schema scopes by Site and asset only, never by component type."""

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
        self.charger, self.connector = self.assets[0], self.assets[1]

    def p(self, **kw) -> dict:
        return {"t": self.t, "s": self.s, **kw}


def remove_ev(engine) -> None:  # noqa: F811
    _replica(engine, "DELETE FROM ev_meter_interval", "DELETE FROM ev_session_evidence",
             "DELETE FROM ev_session_revision", "DELETE FROM ev_session",
             "DELETE FROM finding_revision WHERE domain = 'ev_charging'",
             "DELETE FROM finding WHERE domain = 'ev_charging'",
             "DELETE FROM recompute_job WHERE domain = 'ev_charging'")


def insert_session(engine, ctx, *, external="ev-session-1", tenant=None, charger=None, connector=None,
                   start_evidence=None):  # noqa: F811
    sid = uuid4()
    with engine.begin() as c:
        c.execute(text(
            "INSERT INTO ev_session (id, tenant_id, site_id, charger_asset_id, connector_asset_id, "
            "external_session_id, first_start_evidence_id, anchor_time, created_at) "
            "VALUES (:i, :t, :s, :ch, :co, :x, :e, :at, now())"),
            {"i": sid, "t": tenant or ctx.t, "s": ctx.s, "ch": charger or ctx.charger,
             "co": connector or ctx.connector, "x": external, "e": start_evidence or ctx.evidence[0],
             "at": T0 + timedelta(minutes=1)})
    return sid


def insert_revision(engine, ctx, session_id, *, n=1, basis="basis-1", **over):  # noqa: F811
    rid = uuid4()
    cols = {"state": "COMPLETED", "start_at": T0 + timedelta(minutes=1), "end_at": T0 + timedelta(minutes=31),
            "start_earliest": None, "start_latest": None, "end_earliest": None, "end_latest": None,
            "supported_kwh": "30.000", "unknown_meter_seconds": 0, "fault_evidence_id": None,
            "reason_codes": "[]", "assessment": ctx.assessment, "run": ctx.run}
    cols.update(over)
    with engine.begin() as c:
        c.execute(text(
            "INSERT INTO ev_session_revision (id, tenant_id, site_id, session_id, revision_no, "
            "assessment_revision_id, analytic_run_id, basis_sha256, state, start_at, end_at, start_earliest, "
            "start_latest, end_earliest, end_latest, supported_kwh, unknown_meter_seconds, fault_evidence_id, "
            "reason_codes, created_at) VALUES (:i, :t, :s, :e, :n, :assessment, :run, :b, :state, :start_at, "
            ":end_at, :start_earliest, :start_latest, :end_earliest, :end_latest, CAST(:supported_kwh AS numeric), "
            ":unknown_meter_seconds, :fault_evidence_id, CAST(:reason_codes AS jsonb), now())"),
            ctx.p(i=rid, e=session_id, n=n, b=_sha(basis), **cols))
    return rid


def insert_link(engine, ctx, revision_id, evidence_id, use="SUPPORT", reason=None, *, site_id=None):  # noqa: F811
    with engine.begin() as c:
        c.execute(text(
            "INSERT INTO ev_session_evidence (tenant_id, site_id, revision_id, evidence_id, use, reason) "
            "VALUES (:t, :s, :r, :e, :u, :why)"),
            {"t": ctx.t, "s": site_id or ctx.s, "r": revision_id, "e": evidence_id, "u": use, "why": reason})


def insert_interval(engine, ctx, revision_id, evidence_id, start_min, end_min, *, kwh="5.000",
                    error="0.001", use="SUPPORT", reason=None, connector=None):  # noqa: F811
    iid = uuid4()
    with engine.begin() as c:
        c.execute(text(
            "INSERT INTO ev_meter_interval (id, tenant_id, site_id, revision_id, connector_asset_id, evidence_id, "
            "start_at, end_at, kwh, error_bound_kwh, use, reason) VALUES (:i, :t, :s, :r, :co, :e, :a, :b, "
            "CAST(:k AS numeric), CAST(:err AS numeric), :u, :why)"),
            ctx.p(i=iid, r=revision_id, co=connector or ctx.connector, e=evidence_id,
                  a=T0 + timedelta(minutes=start_min), b=T0 + timedelta(minutes=end_min), k=kwh, err=error,
                  u=use, why=reason))
    return iid


def insert_ev_finding(engine, ctx, *, generator=None, subject="connector", minutes=None,
                      episode=(T0 + timedelta(minutes=1), T0 + timedelta(minutes=16))):  # noqa: F811
    fid = uuid4()
    with engine.begin() as c:
        c.execute(text(
            "INSERT INTO finding (id, tenant_id, site_id, finding_key, domain, mechanism, analytic_id, "
            "generator_asset_id, subject_asset_id, anchor_start, anchor_assessment_revision_id, cohort_sha256, "
            "matcher_version, opened_at, created_at) VALUES (:i, :t, :s, :k, 'ev_charging', 'EV_INTERRUPTION', "
            "'ev-session/1', :g, :sub, :at, :ar, NULL, 'ev-session/1', now(), now())"),
            ctx.p(i=fid, k=_sha(f"ev:{fid}"), g=generator, sub=ctx.connector if subject == "connector" else subject,
                  at=episode[0] or T0, ar=ctx.assessment))
        c.execute(text(
            "INSERT INTO finding_revision (id, tenant_id, site_id, finding_id, domain, revision_no, transition, "
            "lifecycle, claim_level, title, mechanism, matcher_version, analytic_id, model_version, "
            "assessment_revision_id, analytic_run_id, episode_start, episode_end, candidate_minutes, "
            "necessary_minutes, indeterminate_minutes, claim, limitations, basis_sha256, support_sha256, "
            "cited_evidence_sha256, input_evidence_sha256, created_at) VALUES (:i, :t, :s, :f, 'ev_charging', 1, "
            "'OPENED', 'SUPPORTED', 'OBSERVED', 'Observed interruption', 'EV_INTERRUPTION', 'ev-session/1', "
            "'ev-session/1', '1', :ar, :run, :es, :ee, :m, :m, :m, '{}'::jsonb, '[]'::jsonb, :b, :b, :b, :b, now())"),
            ctx.p(i=uuid4(), f=fid, ar=ctx.assessment, run=ctx.run, es=episode[0], ee=episode[1], m=minutes,
                  b=_sha(f"ev-finding:{fid}")))
    return fid


def ev_triggers(engine) -> int:  # noqa: F811
    return scalar(engine, "SELECT count(*) FROM pg_trigger WHERE tgname IN ('ev_session_append_only', "
                  "'ev_session_revision_append_only', 'ev_session_evidence_append_only', "
                  "'ev_meter_interval_append_only', 'enqueue_ev_assessment')")


EV_FUNCTIONS = ("enqueue_ev_assessment", "ev_enqueue_configuration", "ev_enqueue_window", "ev_enqueue_ceil",
                "ev_enqueue_floor")


def ev_functions(engine) -> int:  # noqa: F811
    return scalar(engine, "SELECT count(*) FROM pg_proc WHERE proname IN ("
                  + ", ".join(f"'{f}'" for f in EV_FUNCTIONS) + ")")


class TestMigration0025:
    def test_upgrade_downgrade_round_trip_preserves_minigrid_and_restores_0022_checks(self, site_before_0029, engine) -> None:  # noqa: F811
        site = site_before_0029  # W4-02 q1 ruling 2: seeded before 0029
        from alembic import command

        Ctx(site, engine)
        assert head(engine) == HEAD
        assert all(table_exists(engine, t) for t in EV) and ev_triggers(engine) == 5 and ev_functions(engine) == 5
        subject, minutes = constraint(engine, "finding_domain_subject"), constraint(engine, "finding_revision_domain_minutes")
        for definition in (subject, minutes):
            assert "'mini_grid'" in definition and "'cold_chain'" in definition and "'ev_charging'" in definition
        bounds = (constraint(engine, "finding_revision_bounds"), constraint(engine, "finding_revision_minigrid_bounds"))
        before_rows = minigrid_rows(engine)
        assert before_rows["finding"] and before_rows["finding_revision"]
        config = _alembic()
        site.store.dispose()
        site.prices.dispose()
        engine.dispose()
        try:
            __import__("mini_depth_probe").assert_no_mini_history(engine)  # q1 ruling 2: before 0029
            command.downgrade(config, PREVIOUS)
            assert head(engine) == PREVIOUS
            assert not any(table_exists(engine, t) for t in EV) and ev_triggers(engine) == 0 and ev_functions(engine) == 0
            for name in ("finding_domain_subject", "finding_revision_domain_minutes"):
                restored = constraint(engine, name)
                assert "'ev_charging'" not in restored
                assert "'mini_grid'" in restored and "'cold_chain'" in restored
            assert (constraint(engine, "finding_revision_bounds"),
                    constraint(engine, "finding_revision_minigrid_bounds")) == bounds
            assert minigrid_rows(engine) == before_rows
            command.upgrade(config, "head")
        finally:
            if head(engine) != HEAD:
                command.upgrade(config, "head")
        assert head(engine) == HEAD and all(table_exists(engine, t) for t in EV)
        assert constraint(engine, "finding_domain_subject") == subject
        assert constraint(engine, "finding_revision_domain_minutes") == minutes
        assert minigrid_rows(engine) == before_rows
        assert scalar(engine, "SELECT count(*) FROM pg_indexes WHERE indexname IN ('ev_session_site_anchor', "
                      "'ev_session_connector_anchor', 'ev_session_revision_session_latest', "
                      "'ev_meter_interval_bounds')") == 4

    @pytest.mark.parametrize("blocker", ["session", "finding", "job"])
    def test_downgrade_refuses_while_ev_rows_exist(self, blocker, site_before_0029, engine) -> None:  # noqa: F811
        site = site_before_0029  # W4-02 q1 ruling 2: seeded before 0029
        from alembic import command

        ctx = Ctx(site, engine)
        if blocker == "session":
            insert_session(engine, ctx)
        elif blocker == "finding":
            insert_ev_finding(engine, ctx)
        else:
            with engine.begin() as c:
                c.execute(text(
                    "INSERT INTO recompute_job (id, tenant_id, site_id, domain, window_start, window_end, status, "
                    "available_at, created_at) VALUES (gen_random_uuid(), :t, :s, 'ev_charging', :a, :b, 'PENDING', "
                    "now(), now())"), ctx.p(a=T0, b=T0 + timedelta(hours=1)))
        config = _alembic()
        site.store.dispose()
        site.prices.dispose()
        engine.dispose()
        try:
            with pytest.raises(DBAPIError, match=REFUSED):
                __import__("mini_depth_probe").assert_no_mini_history(engine)  # q1 ruling 2: before 0029
                command.downgrade(config, PREVIOUS)
            assert head(engine) == HEAD and all(table_exists(engine, t) for t in EV)  # nothing dropped
        finally:
            remove_ev(engine)
            if head(engine) != HEAD:
                command.upgrade(config, "head")

    def test_ev_finding_arm_and_minigrid_cold_arms_hold(self, site, engine) -> None:  # noqa: F811
        ctx = Ctx(site, engine)
        try:
            fid = insert_ev_finding(engine, ctx)
            assert scalar(engine, "SELECT subject_asset_id FROM finding WHERE id = :f", f=fid) == ctx.connector
            for kw, name in (({"generator": "gen-1"}, "finding_domain_subject"),
                             ({"subject": None}, "finding_domain_subject"),
                             ({"minutes": "0"}, "finding_revision_domain_minutes"),
                             ({"episode": (T0 + timedelta(minutes=16), T0)}, "finding_revision_bounds")):
                with pytest.raises(IntegrityError, match=name):
                    insert_ev_finding(engine, ctx, **kw)
            # The mini-grid arm still requires a generator and all three minute fields.
            mini = scalar(engine, "SELECT id FROM finding_revision WHERE domain = 'mini_grid' ORDER BY id LIMIT 1")
            for override in ("candidate_minutes = NULL", "domain = 'ev_charging'"):
                with pytest.raises(IntegrityError, match="finding_revision_(domain_minutes|finding_domain_fk)"):
                    with engine.begin() as c:
                        c.execute(text("CREATE TEMP TABLE fr_copy ON COMMIT DROP AS SELECT * FROM finding_revision "
                                       "WHERE id = :r"), {"r": mini})
                        c.execute(text(f"UPDATE fr_copy SET id = gen_random_uuid(), revision_no = revision_no + 100, "
                                       f"basis_sha256 = repeat('e', 64), {override}"))
                        c.execute(text("INSERT INTO finding_revision SELECT * FROM fr_copy"))
        finally:
            remove_ev(engine)

    def test_scoped_fks_value_checks_and_uniques(self, site, engine) -> None:  # noqa: F811
        ctx = Ctx(site, engine)
        try:
            session = insert_session(engine, ctx)
            revision = insert_revision(engine, ctx, session)
            insert_link(engine, ctx, revision, ctx.evidence[0], "SUPPORT")
            insert_link(engine, ctx, revision, ctx.evidence[1], "CONTEXT")
            insert_link(engine, ctx, revision, ctx.evidence[2], "CONTEXT", "CLOCK_UNATTESTED")
            insert_interval(engine, ctx, revision, ctx.evidence[0], 1, 5)
            insert_interval(engine, ctx, revision, ctx.evidence[1], 5, 10)  # half-open: adjacency is not overlap
            insert_interval(engine, ctx, revision, ctx.evidence[2], 3, 8, use="EXCLUDED", reason="METER_OVERLAP")

            # Cross-tenant, cross-Site and unknown scoped references are refused (a fresh revision for the
            # interval FK, since the unique evidence key is checked before the deferred-to-row-end FK triggers).
            fresh = insert_revision(engine, ctx, session, n=30, basis="fk")
            for call, name in (
                (lambda: insert_session(engine, ctx, external="x1", tenant=uuid4()), "ev_session_.*_fk"),
                (lambda: insert_session(engine, ctx, external="x2", charger=uuid4()), "ev_session_charger_fk"),
                (lambda: insert_session(engine, ctx, external="x3", connector=uuid4()), "ev_session_connector_fk"),
                (lambda: insert_session(engine, ctx, external="x4", start_evidence=uuid4()),
                 "ev_session_start_evidence_fk"),
                (lambda: insert_revision(engine, ctx, uuid4(), basis="x5"), "ev_session_revision_session_fk"),
                (lambda: insert_revision(engine, ctx, session, n=5, basis="x6", assessment=uuid4()),
                 "ev_session_revision_assessment_fk"),
                (lambda: insert_revision(engine, ctx, session, n=5, basis="x7", run=uuid4()),
                 "ev_session_revision_run_fk"),
                (lambda: insert_revision(engine, ctx, session, n=5, basis="x8", fault_evidence_id=uuid4()),
                 "ev_session_revision_fault_fk"),
                (lambda: insert_link(engine, ctx, revision, uuid4()), "ev_session_evidence_evidence_fk"),
                (lambda: insert_link(engine, ctx, revision, ctx.evidence[2], site_id=uuid4()),
                 "ev_session_evidence_(revision|evidence)_fk"),
                (lambda: insert_interval(engine, ctx, fresh, ctx.evidence[0], 20, 25, connector=uuid4()),
                 "ev_meter_interval_connector_fk"),
                (lambda: insert_interval(engine, ctx, uuid4(), ctx.evidence[0], 20, 25),
                 "ev_meter_interval_revision_fk"),
            ):
                with pytest.raises(IntegrityError, match=name):
                    call()

            # Identity: blank or overlong external IDs refused; the five-part scoped identity is unique.
            for external in ("", "   ", "x" * 129):
                with pytest.raises(IntegrityError, match="ev_session_external_id"):
                    insert_session(engine, ctx, external=external)
            insert_session(engine, ctx, external="x" * 128)
            with pytest.raises(IntegrityError, match="ev_session_identity_unique"):
                insert_session(engine, ctx)
            insert_session(engine, ctx, charger=ctx.connector, connector=ctx.charger)  # another scoped identity

            # Revision value checks.
            later = T0 + timedelta(minutes=40)
            for over, name in (
                ({"n": 0}, "ev_session_revision_no_positive"),
                ({"state": "FAILED"}, "ev_session_revision_state"),
                ({"end_at": T0}, "ev_session_revision_end_order"),
                ({"state": "COMPLETED", "end_at": None}, "ev_session_revision_state_end"),
                ({"state": "OBSERVED_ABORT", "end_at": None}, "ev_session_revision_state_end"),
                ({"state": "INCOMPLETE"}, "ev_session_revision_state_end"),
                ({"start_earliest": later, "start_latest": T0}, "ev_session_revision_start_bounds"),
                ({"end_earliest": later, "end_latest": T0}, "ev_session_revision_end_bounds"),
                ({"supported_kwh": "-0.001"}, "ev_session_revision_supported_kwh"),
                ({"supported_kwh": "NaN"}, "ev_session_revision_supported_kwh"),
                ({"supported_kwh": "Infinity"}, "ev_session_revision_supported_kwh"),
                ({"unknown_meter_seconds": -1}, "ev_session_revision_unknown_seconds"),
                # R1 (q1): only CONTRADICTORY carries the null quantity pair, and it must carry both nulls.
                ({"unknown_meter_seconds": None}, "ev_session_revision_quantity_state"),
                ({"state": "INCOMPLETE", "end_at": None, "unknown_meter_seconds": None},
                 "ev_session_revision_quantity_state"),
                ({"state": "CONTRADICTORY", "supported_kwh": None, "unknown_meter_seconds": 0},
                 "ev_session_revision_quantity_state"),
                ({"state": "CONTRADICTORY", "supported_kwh": "30.000", "unknown_meter_seconds": None},
                 "ev_session_revision_quantity_state"),
                ({"state": "CONTRADICTORY", "supported_kwh": "0.000", "unknown_meter_seconds": None},
                 "ev_session_revision_quantity_state"),
                ({"reason_codes": '{"code": "METER_GAP"}'}, "ev_session_revision_reason_codes_array"),
            ):
                kw = {"n": 9, "basis": f"check-{name}-{sorted(over)}", **over}
                with pytest.raises(IntegrityError, match=name):
                    insert_revision(engine, ctx, session, **kw)
            # INCOMPLETE without end; CONTRADICTORY (R1) with null end and the null quantity pair.
            insert_revision(engine, ctx, session, n=2, basis="incomplete", state="INCOMPLETE", end_at=None,
                            supported_kwh="30.000", unknown_meter_seconds=0, reason_codes='["MISSING_TERMINAL"]')
            insert_revision(engine, ctx, session, n=3, basis="contradictory", state="CONTRADICTORY",
                            end_at=None, supported_kwh=None, unknown_meter_seconds=None,
                            reason_codes='["CONFLICTING_TERMINAL"]')
            # R1: an unambiguous state with no SUPPORT delta stores NULL energy but integer unknown seconds.
            insert_revision(engine, ctx, session, n=5, basis="no-support", state="INCOMPLETE", end_at=None,
                            supported_kwh=None, unknown_meter_seconds=0, reason_codes='["MISSING_TERMINAL"]')
            with pytest.raises(IntegrityError, match="ev_session_revision_basis_unique"):
                insert_revision(engine, ctx, session, n=4, basis="basis-1")
            with pytest.raises(IntegrityError, match="ev_session_revision_no_unique"):
                insert_revision(engine, ctx, session, n=1, basis="basis-other")

            # Evidence-link checks.
            other = insert_revision(engine, ctx, session, n=10, basis="links")
            for use, reason, name in (("CITED", None, "ev_session_evidence_(use|reason)"),
                                      ("EXCLUDED", None, "ev_session_evidence_reason"),
                                      ("SUPPORT", "METER_GAP", "ev_session_evidence_reason")):
                with pytest.raises(IntegrityError, match=name):
                    insert_link(engine, ctx, other, ctx.evidence[0], use, reason)
            insert_link(engine, ctx, other, ctx.evidence[0], "EXCLUDED", "SOURCE_UNVERIFIED")
            with pytest.raises(IntegrityError, match="ev_session_evidence_pkey"):
                insert_link(engine, ctx, revision, ctx.evidence[0], "CONTEXT")

            # Meter-interval checks: order, finite nonnegative energy/error, use/reason, unique evidence, overlap.
            r2 = insert_revision(engine, ctx, session, n=20, basis="intervals")
            for kw, name in (
                ({"start_min": 10, "end_min": 10}, "ev_meter_interval_order"),
                ({"kwh": "-1"}, "ev_meter_interval_kwh"),
                ({"kwh": "NaN"}, "ev_meter_interval_kwh"),
                ({"error": "Infinity"}, "ev_meter_interval_error"),
                ({"use": "CONTEXT", "reason": "X"}, "ev_meter_interval_(use|reason)"),
                ({"use": "EXCLUDED"}, "ev_meter_interval_reason"),
                ({"reason": "METER_GAP"}, "ev_meter_interval_reason"),
            ):
                args = {"start_min": 1, "end_min": 5, **kw}
                with pytest.raises(IntegrityError, match=name):
                    insert_interval(engine, ctx, r2, ctx.evidence[0], args.pop("start_min"), args.pop("end_min"),
                                    **args)
            with pytest.raises(IntegrityError, match="ev_meter_interval_evidence_unique"):
                insert_interval(engine, ctx, revision, ctx.evidence[0], 30, 35)
            insert_interval(engine, ctx, r2, ctx.evidence[0], 1, 5)
            insert_interval(engine, ctx, r2, ctx.evidence[2], 4, 6, use="EXCLUDED", reason="METER_OVERLAP")
            with pytest.raises(IntegrityError, match="ev_meter_interval_no_support_overlap"):
                insert_interval(engine, ctx, r2, ctx.evidence[1], 4, 6)
            r3 = insert_revision(engine, ctx, session, n=21, basis="other-connector")
            insert_interval(engine, ctx, r3, ctx.evidence[1], 4, 6)  # another revision may reuse the span
        finally:
            remove_ev(engine)

    def test_append_only_on_all_four_tables(self, site, engine) -> None:  # noqa: F811
        ctx = Ctx(site, engine)
        try:
            session = insert_session(engine, ctx)
            revision = insert_revision(engine, ctx, session)
            insert_link(engine, ctx, revision, ctx.evidence[0])
            interval = insert_interval(engine, ctx, revision, ctx.evidence[0], 1, 5)
            for table, where in (("ev_session", f"id = '{session}'"), ("ev_session_revision", f"id = '{revision}'"),
                                 ("ev_session_evidence", f"revision_id = '{revision}'"),
                                 ("ev_meter_interval", f"id = '{interval}'")):
                for sql in (f"UPDATE {table} SET site_id = site_id WHERE {where}", f"DELETE FROM {table} WHERE {where}"):
                    with pytest.raises(DBAPIError, match="append-only"):
                        with engine.begin() as c:
                            c.execute(text(sql))
            assert scalar(engine, "SELECT count(*) FROM ev_meter_interval WHERE revision_id = :r", r=revision) == 1
        finally:
            remove_ev(engine)
