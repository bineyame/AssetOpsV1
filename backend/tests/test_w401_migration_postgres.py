"""W4-01 commit 1: migration `0027_w4_work_cases` against Postgres.

`.agent/W4-01-build-spec.md` "Literal migration `0027_w4_work_cases`": eleven append-only, tenant/Site-scoped work
tables, one shared public-number sequence, one append-only trigger function, seven explicit indexes, and a guarded
downgrade that refuses while any W4 work row exists (no CASCADE). Rows written here only exercise constraints; the
product writer `work/adapters/postgres_work_store.py` arrives with commit 2.

Requires ASSETOPS_TEST_DATABASE_URL naming a `*_test` database.
"""

from __future__ import annotations

import os
from uuid import UUID, uuid4

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError, IntegrityError
    from test_s1_bindings_postgres import _alembic, engine, imported, store  # noqa: F401
    from test_s4_consequence_store_postgres import _release_connections, site, site_before_0029  # noqa: F401
    from test_w203_cold_migration_postgres import _replica, constraint, head, minigrid_rows, scalar, table_exists

HEAD = "0038_out_objectives"  # W5-04a: 0035 sits above 0034; W5-03b: 0034 sits above 0033; W5-02a: 0033 sits above 0032 (W5-01b above 0030)
PREVIOUS = "0026_w2_ev_money"
REFUSED = "0027 downgrade requires empty W4 work tables"
APPEND_ONLY = "W4 work history is append only"
TABLES = ("work_case", "incident", "maintenance_work_request", "work_case_revision", "work_case_finding_link",
          "work_case_action_link", "work_case_evidence", "work_event", "maintenance_plan", "maintenance_record",
          "operational_record")
TRIGGERS = ("work_case_immutable", "incident_immutable", "maintenance_work_request_immutable",
            "work_case_finding_link_immutable", "work_case_action_link_immutable", "work_revision_immutable",
            "work_case_evidence_immutable", "work_event_immutable", "maintenance_plan_immutable",
            "maintenance_record_immutable", "operational_record_immutable")
INDEXES = ("work_case_site_window", "work_case_site_kind", "work_revision_head", "work_event_order",
           "maintenance_plan_site", "maintenance_record_case", "operational_record_site")
# 11 primary keys + 27 UNIQUE constraints (work_case 5, incident 1, request 1, revision 5, event 2, plan 5,
# record 3, operational record 5) + the 7 explicit indexes.
INDEX_TOTAL = 11 + 27 + 7
# Scoped foreign keys whose exact column lists are the second boundary behind the service (spec section).
SCOPED_FKS = {
    "work_case_site_fk": "FOREIGN KEY (tenant_id, site_id) REFERENCES site(tenant_id, id)",
    "work_case_asset_fk": "FOREIGN KEY (tenant_id, site_id, asset_id) REFERENCES asset(tenant_id, site_id, id)",
    "incident_case_fk": "FOREIGN KEY (tenant_id, site_id, id, kind) REFERENCES work_case(tenant_id, site_id, id, kind)",
    "maintenance_request_case_fk": "FOREIGN KEY (tenant_id, site_id, id, kind) REFERENCES "
                                   "work_case(tenant_id, site_id, id, kind)",
    "maintenance_request_incident_fk": "FOREIGN KEY (tenant_id, site_id, incident_id) REFERENCES "
                                       "incident(tenant_id, site_id, id)",
    "work_revision_case_fk": "FOREIGN KEY (tenant_id, site_id, case_id) REFERENCES work_case(tenant_id, site_id, id)",
    "work_revision_prev_fk": "FOREIGN KEY (case_id, supersedes_revision_id) REFERENCES work_case_revision(case_id, id)",
    "work_finding_case_fk": "FOREIGN KEY (tenant_id, site_id, case_revision_id) REFERENCES "
                            "work_case_revision(tenant_id, site_id, id)",
    "work_finding_revision_fk": "FOREIGN KEY (tenant_id, site_id, finding_id, finding_revision_id) REFERENCES "
                                "finding_revision(tenant_id, site_id, finding_id, id)",
    "work_action_case_fk": "FOREIGN KEY (tenant_id, site_id, case_revision_id) REFERENCES "
                           "work_case_revision(tenant_id, site_id, id)",
    "work_action_fk": "FOREIGN KEY (tenant_id, site_id, action_id) REFERENCES action(tenant_id, site_id, id)",
    "work_action_event_fk": "FOREIGN KEY (tenant_id, site_id, action_event_id) REFERENCES "
                            "action_event(tenant_id, site_id, id)",
    "work_case_evidence_revision_fk": "FOREIGN KEY (tenant_id, site_id, case_revision_id) REFERENCES "
                                      "work_case_revision(tenant_id, site_id, id)",
    "work_case_evidence_accepted_fk": "FOREIGN KEY (tenant_id, site_id, evidence_id) REFERENCES "
                                      "accepted_evidence(tenant_id, site_id, id)",
    "work_event_case_fk": "FOREIGN KEY (tenant_id, site_id, case_id) REFERENCES work_case(tenant_id, site_id, id)",
    "maintenance_plan_site_fk": "FOREIGN KEY (tenant_id, site_id) REFERENCES site(tenant_id, id)",
    "maintenance_plan_asset_fk": "FOREIGN KEY (tenant_id, site_id, asset_id) REFERENCES "
                                 "asset(tenant_id, site_id, id)",
    "maintenance_plan_prev_fk": "FOREIGN KEY (tenant_id, site_id, supersedes_plan_id) REFERENCES "
                                "maintenance_plan(tenant_id, site_id, id)",
    "maintenance_plan_canonical_fk": "FOREIGN KEY (tenant_id, site_id, canonical_plan_id) REFERENCES "
                                     "maintenance_plan(tenant_id, site_id, id)",
    "maintenance_record_case_fk": "FOREIGN KEY (tenant_id, site_id, case_id) REFERENCES "
                                  "work_case(tenant_id, site_id, id)",
    "maintenance_record_prev_fk": "FOREIGN KEY (tenant_id, site_id, supersedes_record_id) REFERENCES "
                                  "maintenance_record(tenant_id, site_id, id)",
    "operational_record_site_fk": "FOREIGN KEY (tenant_id, site_id) REFERENCES site(tenant_id, id)",
    "operational_record_case_fk": "FOREIGN KEY (tenant_id, site_id, case_id) REFERENCES "
                                  "work_case(tenant_id, site_id, id)",
    "operational_record_prev_fk": "FOREIGN KEY (tenant_id, site_id, supersedes_record_id) REFERENCES "
                                  "operational_record(tenant_id, site_id, id)",
    "operational_record_canonical_fk": "FOREIGN KEY (tenant_id, site_id, canonical_record_id) REFERENCES "
                                       "operational_record(tenant_id, site_id, id)",
}
SHA = "a" * 64
T_OCC = "2026-10-06T16:11:00Z"
ACTOR = {"ak": "SERVICE", "ai": "service:w401-fixture", "ab": "SITE_WORK_WRITE",
         "at": "service=w401-fixture;job=migration-test;rule=w401/1"}


# --- helpers -----------------------------------------------------------------------------------------------------


def count(engine, sql, **params) -> int:  # noqa: F811
    return int(scalar(engine, sql, **params))


def run(engine, sql, **params) -> None:  # noqa: F811
    with engine.begin() as c:
        c.execute(text(sql), params)


def raises(engine, sql, match, error=IntegrityError, **params) -> None:  # noqa: F811
    with pytest.raises(error, match=match):
        run(engine, sql, **params)


def catalog(engine) -> dict:  # noqa: F811
    return {
        "tables": count(engine, "SELECT count(*) FROM pg_class WHERE relkind = 'r' AND relname = ANY(:n)",
                        n=list(TABLES)),
        "triggers": count(engine, "SELECT count(*) FROM pg_trigger WHERE tgname = ANY(:n)", n=list(TRIGGERS)),
        "explicit_indexes": count(engine, "SELECT count(*) FROM pg_class WHERE relkind = 'i' AND relname = ANY(:n)",
                                  n=list(INDEXES)),
        "all_indexes": count(engine, "SELECT count(*) FROM pg_index i JOIN pg_class t ON t.oid = i.indrelid "
                                     "WHERE t.relname = ANY(:n)", n=list(TABLES)),
        "sequence": count(engine, "SELECT count(*) FROM pg_class WHERE relkind = 'S' AND relname = "
                                  "'work_public_no_seq'"),
        "function": count(engine, "SELECT count(*) FROM pg_proc WHERE proname = 'w4_append_only'"),
    }


def stocked(engine) -> dict:  # noqa: F811
    return {t: count(engine, f"SELECT count(*) FROM {t}") for t in TABLES}


def release(site, engine) -> None:  # noqa: F811
    site.store.dispose()
    site.prices.dispose()
    engine.dispose()


def new_case(engine, t: UUID, s: UUID, kind="INCIDENT", asset=None, key=None) -> UUID:  # noqa: F811
    """A work_case with its mandatory typed child, as one transaction (schema-level; no product writer yet)."""
    case_id = uuid4()
    prefix = "INC" if kind == "INCIDENT" else "WR"
    key = key or f"mig-{case_id.hex[:12]}"
    with engine.begin() as c:
        no = c.execute(text("SELECT nextval('work_public_no_seq')")).scalar_one()
        c.execute(text(
            "INSERT INTO work_case (id, tenant_id, site_id, kind, public_no, public_code, asset_id, occurred_at, "
            "actor_kind, actor_id, authorization_basis, attestation, create_key, create_payload_sha256) VALUES "
            "(:i, :t, :s, :k, :n, :code, :a, :o, :ak, :ai, :ab, :at, :key, :h)"),
            {"i": case_id, "t": t, "s": s, "k": kind, "n": no, "code": f"{prefix}-{no:06d}", "a": asset, "o": T_OCC,
             "key": key, "h": SHA, **ACTOR})
        child = "incident (tenant_id, site_id, id, incident_key)" if kind == "INCIDENT" else (
            "maintenance_work_request (tenant_id, site_id, id, request_key)")
        c.execute(text(f"INSERT INTO {child} VALUES (:t, :s, :i, :key)"), {"t": t, "s": s, "i": case_id, "key": key})
    return case_id


REVISION = ("INSERT INTO work_case_revision (id, tenant_id, site_id, case_id, revision_no, supersedes_revision_id, "
            "title, narrative, actor_kind, actor_id, attestation, authorization_basis, occurred_at, idempotency_key, "
            "payload_sha256, reason) VALUES (:i, :t, :s, :c, :no, :prev, 'Title', 'Narrative', :ak, :ai, :at, :ab, "
            ":o, :key, :h, :reason)")


def new_revision(engine, t, s, case_id, no=1, prev=None, reason=None) -> UUID:  # noqa: F811
    rid = uuid4()
    run(engine, REVISION, i=rid, t=t, s=s, c=case_id, no=no, prev=prev, o=T_OCC, key=f"rev-{rid.hex[:12]}", h=SHA,
        reason=reason, **ACTOR)
    return rid


EVENT = ("INSERT INTO work_event (id, tenant_id, site_id, case_id, kind, occurred_at, actor_kind, actor_id, "
         "authorization_basis, attestation, idempotency_key, payload_sha256) VALUES (:i, :t, :s, :c, :k, :o, :ak, "
         ":ai, :ab, :at, :key, :h)")
PLAN = ("INSERT INTO maintenance_plan (id, tenant_id, site_id, asset_id, public_no, public_code, canonical_plan_id, "
        "title, trigger_kind, next_due_at, next_due_hours, state, supersedes_plan_id, actor_id, actor_kind, "
        "authorization_basis, occurred_at, correction_reason, attestation, idempotency_key, payload_sha256) VALUES "
        "(:i, :t, :s, NULL, nextval('work_public_no_seq'), :code, :canon, 'Plan', :trig, :due_at, :due_h, 'DRAFT', "
        ":prev, :ai, :ak, :ab, :o, :reason, :at, :key, :h)")
RECORD = ("INSERT INTO maintenance_record (id, tenant_id, site_id, case_id, activity, occurred_at, actor_id, "
          "actor_kind, authorization_basis, attestation, idempotency_key, payload_sha256) VALUES (:i, :t, :s, :c, "
          "'Starter connection inspected', :o, :ai, :ak, :ab, :at, :key, :h)")
OPREC = ("INSERT INTO operational_record (id, tenant_id, site_id, public_no, public_code, canonical_record_id, kind, "
         "body, period_end, unit, quantity, state, case_id, occurred_at, actor_id, actor_kind, authorization_basis, "
         "attestation, idempotency_key, payload_sha256) VALUES (:i, :t, :s, nextval('work_public_no_seq'), :code, "
         ":canon, :k, 'Log entry', CAST(:pe AS timestamptz), :u, CAST(:q AS numeric), 'SUBMITTED', :c, :o, :ai, "
         ":ak, :ab, :at, :key, :h)")


def new_plan(engine, t, s, trig="CALENDAR", due_at=None, due_h=None, canon=None, code="PM-900001") -> UUID:  # noqa: F811
    pid = uuid4()
    run(engine, PLAN, i=pid, t=t, s=s, code=code, canon=canon or pid, trig=trig, due_at=due_at, due_h=due_h,
        prev=None, o=T_OCC, reason=None, key=f"plan-{pid.hex[:12]}", h=SHA, **ACTOR)
    return pid


def new_oprec(engine, t, s, k="OPERATOR_LOG", unit=None, qty=None, period_end=None, case_id=None, canon=None,
              code="REC-900001") -> UUID:  # noqa: F811
    oid = uuid4()
    run(engine, OPREC, i=oid, t=t, s=s, code=code, canon=canon or oid, k=k, pe=period_end, u=unit, q=qty, c=case_id,
        o=T_OCC, key=f"oprec-{oid.hex[:12]}", h=SHA, **ACTOR)
    return oid


def remove_work(engine) -> None:  # noqa: F811
    _replica(engine, *(f"DELETE FROM {t}" for t in reversed(TABLES)))


# --- tests -------------------------------------------------------------------------------------------------------


def test_0027_parent_scoped_fks_append_only_and_clean_downgrade(site_before_0029, store, engine) -> None:  # noqa: F811
    site = site_before_0029  # W4-02 q1 ruling 2: seeded before 0029
    from alembic import command
    from alembic.script import ScriptDirectory

    script = ScriptDirectory.from_config(_alembic())
    assert script.get_heads() == [HEAD] and script.get_revision("0027_w4_work_cases").down_revision == PREVIOUS
    assert head(engine) == HEAD
    installed = {"tables": 11, "triggers": 11, "explicit_indexes": 7, "all_indexes": INDEX_TOTAL, "sequence": 1,
                 "function": 1}
    assert catalog(engine) == installed
    assert {name: constraint(engine, name) for name in SCOPED_FKS} == SCOPED_FKS
    # No CASCADE anywhere on a W4 foreign key.
    assert count(engine, "SELECT count(*) FROM pg_constraint c JOIN pg_class t ON t.oid = c.conrelid WHERE "
                         "c.contype = 'f' AND t.relname = ANY(:n) AND (c.confdeltype <> 'a' OR c.confupdtype <> 'a')",
                 n=list(TABLES)) == 0

    # Clean downgrade on an empty W4 store leaves 0026 intact; then re-upgrade to the single head.
    assert stocked(engine) == {t: 0 for t in TABLES}
    before_rows = minigrid_rows(engine)
    ev_money = count(engine, "SELECT count(*) FROM ev_consequence_revision")
    config = _alembic()
    release(site, engine)
    try:
        __import__("mini_depth_probe").assert_no_mini_history(engine)  # q1 ruling 2: before 0029
        command.downgrade(config, PREVIOUS)
        assert head(engine) == PREVIOUS
        assert not any(table_exists(engine, t) for t in TABLES)
        assert catalog(engine) == {k: 0 for k in installed}
        assert table_exists(engine, "ev_consequence_revision") and minigrid_rows(engine) == before_rows
        assert count(engine, "SELECT count(*) FROM ev_consequence_revision") == ev_money
        command.upgrade(config, "head")
    finally:
        if head(engine) != HEAD:
            command.upgrade(config, "head")
    assert catalog(engine) == installed and minigrid_rows(engine) == before_rows

    t, s = site.tenant, site.site
    imported(store, code="KOBO-002")
    with engine.connect() as c:
        own_asset = c.execute(text("SELECT id FROM asset WHERE site_id = :s ORDER BY id LIMIT 1"), {"s": s}).scalar_one()
        other_site = c.execute(text("SELECT id FROM site WHERE tenant_id = :t AND id <> :s ORDER BY id LIMIT 1"),
                               {"t": t, "s": s}).scalar_one()
        foreign_asset = c.execute(text("SELECT id FROM asset WHERE site_id = :o ORDER BY id LIMIT 1"),
                                  {"o": other_site}).scalar_one()
        finding_id, finding_rev = c.execute(text(
            "SELECT finding_id, id FROM finding_revision WHERE site_id = :s ORDER BY id LIMIT 1"), {"s": s}).one()
        other_finding = c.execute(text(
            "SELECT finding_id FROM finding_revision WHERE site_id = :s AND finding_id <> :f LIMIT 1"),
            {"s": s, "f": finding_id}).scalar()
        evidence = c.execute(text("SELECT id FROM accepted_evidence WHERE site_id = :s ORDER BY id LIMIT 1"),
                             {"s": s}).scalar_one()
    try:
        # Parent and scope: a case's Asset must be in its own tenant/Site; the typed child must match the kind.
        incident = new_case(engine, t, s, asset=own_asset)
        request = new_case(engine, t, s, kind="MAINTENANCE_REQUEST")
        with pytest.raises(IntegrityError, match="work_case_asset_fk"):
            new_case(engine, t, s, asset=foreign_asset)
        with pytest.raises(IntegrityError, match="work_case_site_fk"):
            new_case(engine, t, uuid4())
        with pytest.raises(IntegrityError, match='constraint "work_case_check"'):
            run(engine, "INSERT INTO work_case (id, tenant_id, site_id, kind, public_no, public_code, occurred_at, "
                        "actor_kind, actor_id, authorization_basis, attestation, create_key, create_payload_sha256) "
                        "VALUES (:i, :t, :s, 'INCIDENT', nextval('work_public_no_seq'), 'WR-000009', :o, :ak, :ai, "
                        ":ab, :at, 'mig-code-1', :h)", i=uuid4(), t=t, s=s, o=T_OCC, h=SHA, **ACTOR)
        raises(engine, "INSERT INTO incident (tenant_id, site_id, id, incident_key) VALUES (:t, :s, :i, 'mig-wrong')",
               "incident_case_fk", t=t, s=s, i=request)
        raises(engine, "INSERT INTO maintenance_work_request (tenant_id, site_id, id, request_key) VALUES "
                       "(:t, :s, :i, 'mig-wrong')", "maintenance_request_case_fk", t=t, s=s, i=incident)
        raises(engine, "INSERT INTO maintenance_work_request (tenant_id, site_id, id, request_key, incident_id) "
                       "VALUES (:t, :o, :i, 'mig-cross', :inc)", "maintenance_request_case_fk|"
               "maintenance_request_incident_fk", t=t, o=other_site, i=request, inc=incident)
        with pytest.raises(IntegrityError, match="maintenance_request_incident_fk"):
            with engine.begin() as c:  # a request at another Site cannot cite this Site's Incident
                rid = uuid4()
                no = c.execute(text("SELECT nextval('work_public_no_seq')")).scalar_one()
                c.execute(text(
                    "INSERT INTO work_case (id, tenant_id, site_id, kind, public_no, public_code, occurred_at, "
                    "actor_kind, actor_id, authorization_basis, attestation, create_key, create_payload_sha256) VALUES "
                    "(:i, :t, :o, 'MAINTENANCE_REQUEST', :n, :code, :oc, :ak, :ai, :ab, :at, 'mig-cross-2', :h)"),
                    {"i": rid, "t": t, "o": other_site, "n": no, "code": f"WR-{no:06d}", "oc": T_OCC, "h": SHA,
                     **ACTOR})
                c.execute(text("INSERT INTO maintenance_work_request (tenant_id, site_id, id, request_key, "
                               "incident_id) VALUES (:t, :o, :i, 'mig-cross-2', :inc)"),
                          {"t": t, "o": other_site, "i": rid, "inc": incident})

        # Linear revision chain per case, scoped to the case; one successor per predecessor.
        r1 = new_revision(engine, t, s, incident)
        r2 = new_revision(engine, t, s, incident, no=2, prev=r1, reason="Corrected note")
        other_r1 = new_revision(engine, t, s, request)
        with pytest.raises(IntegrityError, match="work_revision_prev_fk"):
            new_revision(engine, t, s, incident, no=3, prev=other_r1, reason="Wrong chain")
        with pytest.raises(IntegrityError, match="work_revision_one_successor"):
            new_revision(engine, t, s, incident, no=3, prev=r1, reason="Fork")
        with pytest.raises(IntegrityError, match="work_revision_number"):
            new_revision(engine, t, s, incident, no=2, prev=r2, reason="Same number")
        with pytest.raises(IntegrityError, match="work_revision_case_fk"):
            new_revision(engine, t, other_site, incident, no=9)

        # Exact pinned Finding revision and accepted evidence, scoped to the case revision's tenant/Site.
        run(engine, "INSERT INTO work_case_finding_link VALUES (:t, :s, :r, :f, :fr)", t=t, s=s, r=r2, f=finding_id,
            fr=finding_rev)
        if other_finding is not None:
            raises(engine, "INSERT INTO work_case_finding_link VALUES (:t, :s, :r, :f, :fr)",
                   "work_finding_revision_fk", t=t, s=s, r=r1, f=other_finding, fr=finding_rev)
        raises(engine, "INSERT INTO work_case_finding_link VALUES (:t, :s, :r, :f, :fr)", "work_finding_revision_fk",
               t=t, s=s, r=r1, f=uuid4(), fr=finding_rev)
        raises(engine, "INSERT INTO work_case_finding_link VALUES (:t, :o, :r, :f, :fr)",
               "work_finding_case_fk|work_finding_revision_fk", t=t, o=other_site, r=r1, f=finding_id, fr=finding_rev)
        run(engine, "INSERT INTO work_case_evidence VALUES (:t, :s, :r, :e)", t=t, s=s, r=r2, e=evidence)
        raises(engine, "INSERT INTO work_case_evidence VALUES (:t, :s, :r, :e)", "work_case_evidence_accepted_fk",
               t=t, s=s, r=r1, e=uuid4())
        raises(engine, "INSERT INTO work_case_evidence VALUES (:t, :o, :r, :e)",
               "work_case_evidence_revision_fk|work_case_evidence_accepted_fk", t=t, o=other_site, r=r1, e=evidence)
        raises(engine, "INSERT INTO work_case_action_link VALUES (:t, :s, :r, :a, :ev)", "work_action_fk|"
               "work_action_event_fk", t=t, s=s, r=r2, a=uuid4(), ev=uuid4())

        # Events, records, plans and operational records.
        run(engine, EVENT, i=uuid4(), t=t, s=s, c=incident, k="CREATED", o=T_OCC, key="mig-event-1", h=SHA, **ACTOR)
        raises(engine, EVENT, "work_event_kind_check", i=uuid4(), t=t, s=s, c=incident, k="VERIFIED", o=T_OCC,
               key="mig-event-2", h=SHA, **ACTOR)
        raises(engine, EVENT, "work_event_case_fk", i=uuid4(), t=t, s=other_site, c=incident, k="COMMENT", o=T_OCC,
               key="mig-event-3", h=SHA, **ACTOR)
        run(engine, RECORD, i=uuid4(), t=t, s=s, c=request, o=T_OCC, key="mig-record-1", h=SHA, **ACTOR)
        raises(engine, RECORD, "maintenance_record_case_fk", i=uuid4(), t=t, s=other_site, c=request, o=T_OCC,
               key="mig-record-2", h=SHA, **ACTOR)
        new_plan(engine, t, s)
        with pytest.raises(IntegrityError, match="maintenance_plan_root"):
            new_plan(engine, t, s, canon=new_plan(engine, t, s, code="PM-900002"), code="PM-900003")
        with pytest.raises(IntegrityError, match="maintenance_plan_due"):
            new_plan(engine, t, s, trig="RUN_HOURS", due_at=T_OCC, code="PM-900004")
        with pytest.raises(IntegrityError, match="maintenance_plan_due"):
            new_plan(engine, t, s, trig="RUN_HOURS", due_h=-1, code="PM-900005")
        new_plan(engine, t, s, trig="RUN_HOURS", due_h=250, code="PM-900006")
        new_oprec(engine, t, s, case_id=incident)
        new_oprec(engine, t, s, k="MANUAL_READING", unit="kWh", qty="12.5", code="REC-900002")
        for bad in ("Infinity", "NaN", "-1"):
            with pytest.raises(IntegrityError, match="operational_record_quantity_check"):
                new_oprec(engine, t, s, k="MANUAL_READING", unit="kWh", qty=bad, code="REC-900003")
        with pytest.raises(IntegrityError, match='constraint "operational_record_quantity"'):
            new_oprec(engine, t, s, k="MANUAL_READING", qty="3", code="REC-900004")
        with pytest.raises(IntegrityError, match='constraint "operational_record_period"'):
            new_oprec(engine, t, s, period_end="2026-10-06T16:10:00Z", code="REC-900005")
        with pytest.raises(IntegrityError, match="operational_record_case_fk"):
            new_oprec(engine, t, other_site, case_id=incident, code="REC-900006")

        # Every W4 table now holds a row; each refuses UPDATE and DELETE through the append-only trigger.
        rows = stocked(engine)
        assert all(rows[tb] >= 1 for tb in TABLES if tb != "work_case_action_link"), rows
        for table in TABLES:
            if rows[table] == 0:
                continue
            column = "tenant_id"
            with pytest.raises(DBAPIError, match=APPEND_ONLY):
                run(engine, f"UPDATE {table} SET {column} = {column}")
            with pytest.raises(DBAPIError, match=APPEND_ONLY):
                run(engine, f"DELETE FROM {table}")
        assert stocked(engine) == rows
    finally:
        remove_work(engine)
    assert stocked(engine) == {t_: 0 for t_ in TABLES}


def test_0027_nonempty_downgrade_refuses(site_before_0029, engine) -> None:  # noqa: F811
    """A single row in any W4 root (operational record, plan, case) refuses the downgrade; nothing is dropped."""
    site = site_before_0029  # W4-02 q1 ruling 2: seeded before 0029
    for stock in ("operational_record", "maintenance_plan", "case"):
        refuse_with(site, engine, stock)


def refuse_with(site, engine, stock: str) -> None:  # noqa: F811
    from alembic import command

    t, s = site.tenant, site.site
    assert stocked(engine) == {tb: 0 for tb in TABLES}
    try:
        if stock == "operational_record":
            new_oprec(engine, t, s)
        elif stock == "maintenance_plan":
            new_plan(engine, t, s)
        else:
            case_id = new_case(engine, t, s)
            new_revision(engine, t, s, case_id)
        before = stocked(engine)
        assert sum(before.values()) >= 1
        config = _alembic()
        release(site, engine)
        try:
            with pytest.raises(RuntimeError, match=REFUSED):
                __import__("mini_depth_probe").assert_no_mini_history(engine)  # q1 ruling 2: before 0029
                command.downgrade(config, PREVIOUS)
        finally:
            if head(engine) != HEAD:
                command.upgrade(config, "head")
        # The whole downgrade rolled back: still at head, every table and row intact, nothing cascaded.
        assert head(engine) == HEAD and all(table_exists(engine, tb) for tb in TABLES)
        assert stocked(engine) == before
    finally:
        remove_work(engine)
