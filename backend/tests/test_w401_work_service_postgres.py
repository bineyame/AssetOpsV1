"""W4-01 commit 2: the work command service and its sole writer over real Postgres.

`.agent/W4-01-build-spec.md` "Fixture and exact test contract", Review closures B4-B6/S14-S17, closure 3 Q7/Q28
and "Run 1 rulings (q1)". The positive linked case is built from F01 through the S4 CaseRunner, the public
Finding index and the existing recommendation/accept route (no hard-coded or invented IDs). Requires
ASSETOPS_TEST_DATABASE_URL naming a `*_test` database.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from test_s4_finding_store_postgres import URL, run_case  # noqa: F401

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from test_s1_bindings_postgres import engine, imported, store  # noqa: F401
    from test_s4_finding_index_postgres import client_for, ok
    from s6_action_records import accepted_before_battery_hold
    from test_s6_action_store_postgres import CASES, Harness, harness, runner  # noqa: F401

    from assetops_backend.evidence.composition import build_link_rows_reader
    from assetops_backend.work.adapters.postgres_work_store import PostgresWorkStore
    from assetops_backend.work.service import WorkService

    from assetops_backend.work.composition import build_work_service
    from assetops_backend.work.model import WorkRefused

PRINCIPAL = "service:w401-fixture"
BASIS = "SITE_WORK_WRITE:service:w401-fixture"
ACTOR = {"kind": "SERVICE", "id": PRINCIPAL, "attestation": "service=w401-fixture;job=positive-case;rule=w401/1"}
TABLES = ("work_case", "incident", "maintenance_work_request", "work_case_revision", "work_case_finding_link",
          "work_case_action_link", "work_case_evidence", "work_event", "maintenance_plan", "maintenance_record",
          "operational_record")


def at(**delta) -> str:
    return (datetime.now(timezone.utc) - timedelta(**delta)).isoformat().replace("+00:00", "Z")


def incident(key="w401-incident-001", **over) -> dict:
    return {"kind": "INCIDENT", "occurred_at": at(hours=1), "asset_id": None, "finding_links": [],
            "action_links": [], "title": "Witnessed start request failed",
            "narrative": "Operator observed a failed start request; cause not established.",
            "cited_accepted_evidence_ids": [], "actor": dict(ACTOR), "idempotency_key": key, **over}


def request(key="w401-request-001", **over) -> dict:
    return {**incident(key), "kind": "MAINTENANCE_REQUEST", "title": "Inspect starter circuit",
            "narrative": "Witnessed failure requires inspection.", **over}


def event(kind, payload, key, **over) -> dict:
    return {"kind": kind, "occurred_at": at(minutes=30), "payload": payload, "actor": dict(ACTOR),
            "idempotency_key": key, **over}


def record(key="w401-record-001", **over) -> dict:
    return {"activity": "Starter connection inspected", "outcome_note": None, "occurred_at": at(minutes=20),
            "actor": dict(ACTOR), "idempotency_key": key, **over}


def plan(key="w401-plan-001", **over) -> dict:
    return {"asset_id": None, "title": "Witnessed start test", "trigger_kind": "CALENDAR", "next_due_at": None,
            "next_due_hours": None, "occurred_at": at(minutes=10), "actor": dict(ACTOR), "idempotency_key": key,
            **over}


def oprec(key="w401-oprec-001", **over) -> dict:
    return {"kind": "OPERATOR_LOG", "body": "Generator started by hand", "occurred_at": at(minutes=5),
            "period_end": None, "unit": None, "quantity": None, "source_document_sha256": None, "case_id": None,
            "actor": dict(ACTOR), "idempotency_key": key, **over}


def counts(engine) -> dict[str, int]:  # noqa: F811
    with engine.connect() as c:
        return {t: c.execute(text(f"SELECT count(*) FROM {t}")).scalar_one() for t in TABLES}


def refused(code: str, call, *args):
    with pytest.raises(WorkRefused) as caught:
        call(*args)
    assert caught.value.code == code, caught.value.code
    return caught.value


def scalar(engine, sql: str, **p):  # noqa: F811
    with engine.connect() as c:
        return c.execute(text(sql), p).scalar_one()


class VirtualDbClock:
    """q2 ruling 4: the private test's virtual DB instant. The store calls it once per command (its `command_now`);
    it then advances one second so successive commands stay ordered."""

    def __init__(self, start: datetime) -> None:
        self.now, self.returned = start, []

    def __call__(self) -> datetime:
        value, self.now = self.now, self.now + timedelta(seconds=1)
        self.returned.append(value)
        return value


POSITIVE_NOW = datetime(2026, 11, 1, 1, 0, tzinfo=timezone.utc)
POSITIVE_OCCURRED = "2026-11-01T00:59:00Z"


class Ctx:
    def __init__(self, runner, clock: VirtualDbClock | None = None) -> None:  # noqa: F811
        self.t, self.s, self.engine = runner.tenant, runner.site, runner.engine
        self.svc = build_work_service(URL) if clock is None else WorkService(
            PostgresWorkStore(URL, link_rows=build_link_rows_reader(), test_db_clock_override=clock))

    def case(self, body, principal=PRINCIPAL):
        return self.svc.create_case(self.t, self.s, body, principal)

    def event(self, case_id, body):
        return self.svc.post_event(self.t, self.s, case_id, body, PRINCIPAL)

    def revise(self, case_id, body):
        return self.svc.post_revision(self.t, self.s, case_id, body, PRINCIPAL)

    def record(self, case_id, body):
        return self.svc.post_record(self.t, self.s, case_id, body, PRINCIPAL)

    def plan(self, body):
        return self.svc.post_plan(self.t, self.s, body, PRINCIPAL)

    def oprec(self, body):
        return self.svc.post_operational_record(self.t, self.s, body, PRINCIPAL)

    def close(self) -> None:
        self.svc._store.dispose()


@pytest.fixture()
def ctx(runner):  # noqa: F811
    owned = Ctx(runner)
    yield owned
    owned.close()


def accepted_action(runner, finding_id: str, key: str) -> tuple[str, str]:  # noqa: F811
    """Closure 3 Q7: accept F0x's recommendation through the existing route; pin the Action's selected event."""
    h = Harness(runner)
    try:
        rec = h.recommendation(finding_id)
        assert rec.status_code == 200, rec.text
        accepted = h.accept(finding_id, rec.json()["proposal"], idempotency_key=key)
        assert accepted.status_code == 201, accepted.text
        action_id = accepted.json()["action"]["action_id"]
        events = h.client.get(f"/api/sites/KOBO-001/actions/{action_id}/events")
        assert events.status_code == 200, events.text
        last = events.json()["events"][-1]
        return action_id, last.get("event_id") or last["id"]
    finally:
        h.close()


def public_finding(runner) -> dict:  # noqa: F811
    body = ok(client_for(runner), frm="2026-10-06T00:00:00Z", to="2026-10-07T00:00:00Z", limit=50)
    assert body["status"] == "CURRENT" and body["rows"], body.get("status")
    row = body["rows"][0]
    assert row["cited"]["accepted_evidence_ids"], "the selected F01 Finding row cites no accepted evidence"
    return row


@pytest.fixture()
def clocked(runner):  # noqa: F811
    clock = VirtualDbClock(POSITIVE_NOW)
    owned = Ctx(runner, clock)
    owned.clock = clock
    yield owned
    owned.close()


def test_incident_attestation_reload_and_exact_links(runner, clocked) -> None:  # noqa: F811
    ctx = clocked
    run_case(runner, CASES["F01"])
    row = public_finding(runner)
    fid, frev, cited = row["finding_id"], row["finding_revision_id"], row["cited"]["accepted_evidence_ids"]
    action_id, action_event = accepted_action(runner, fid, "w401-action-accept-001")
    body = incident(finding_links=[{"finding_id": fid, "finding_revision_id": frev}],
                    action_links=[{"action_id": action_id, "action_event_id": action_event}],
                    cited_accepted_evidence_ids=list(cited), occurred_at=POSITIVE_OCCURRED)
    before = counts(ctx.engine)
    # Run 1 ruling 1: a client authority field, a USER actor, no server principal and a foreign attestation.
    for bad_actor, code, principal in (
            ({**ACTOR, "authorization_basis": BASIS}, "WORK_INPUT_INVALID", PRINCIPAL),
            ({**ACTOR, "authorization_basis": None}, "WORK_INPUT_INVALID", PRINCIPAL),
            ({"kind": "USER", "id": "operator-1", "attestation": "I saw it."}, "WORK_USER_AUTH_REQUIRED", PRINCIPAL),
            (ACTOR, "WORK_WRITE_FORBIDDEN", None),
            ({**ACTOR, "id": "service:other"}, "WORK_ATTESTATION_INVALID", PRINCIPAL),
            ({**ACTOR, "attestation": "service=other;job=positive-case;rule=w401/1"}, "WORK_ATTESTATION_INVALID",
             PRINCIPAL),
            ({**ACTOR, "attestation": "service=w401-fixture;job= ;rule=w401/1"}, "WORK_ATTESTATION_INVALID",
             PRINCIPAL)):
        refused(code, ctx.case, {**body, "actor": bad_actor}, principal)
    assert counts(ctx.engine) == before

    # q2 ruling 4: an in-scope accepted row received after the command's DB instant still refuses, writing nothing.
    ctx.clock.now = datetime(2026, 10, 29, 0, 0, tzinfo=timezone.utc)
    early = incident("w401-incident-early", cited_accepted_evidence_ids=list(cited),
                     occurred_at="2026-10-28T23:59:00Z")
    refused("WORK_LINK_SCOPE_INVALID", ctx.case, early)
    early_now = ctx.clock.returned[-1]
    assert scalar(ctx.engine, "SELECT count(*) FROM accepted_evidence WHERE site_id = :s AND "
                  "id = ANY(CAST(:e AS uuid[])) AND received_at > :n", s=ctx.s, e=list(cited), n=early_now) > 0
    assert counts(ctx.engine) == before

    ctx.clock.now = POSITIVE_NOW
    status, created = ctx.case(body)
    command_now = ctx.clock.returned[-1]
    assert command_now == POSITIVE_NOW
    assert status == 201 and created["schema_version"] == "work-case-1" and created["kind"] == "INCIDENT"
    received = [scalar(ctx.engine, "SELECT received_at FROM accepted_evidence WHERE id = :i", i=e) for e in cited]
    assert received and all(at_ <= command_now for at_ in received)
    assert created["state"] == "OPEN" and created["code"].startswith("INC-") and len(created["code"]) == 10
    assert created["site_id"] == str(ctx.s) and created["revision"]["number"] == 1
    assert created["event"]["kind"] == "CREATED"
    prov = created["source_provenance"]
    assert set(cited) <= set(prov["evidence_ids"]) and prov["basis_sha256"].startswith("sha256:")
    assert prov["classification"] == prov["state"] and "detail" not in prov
    # Exact retry returns the stored result; nothing new is written.
    after = counts(ctx.engine)
    assert ctx.case(body) == (200, created) and counts(ctx.engine) == after
    case_id, rev_id = created["id"], created["revision"]["id"]
    with ctx.engine.connect() as c:
        assert c.execute(text("SELECT tenant_id, site_id, case_revision_id, CAST(action_id AS text), "
                              "CAST(action_event_id AS text) FROM work_case_action_link")).one() == (
            ctx.t, ctx.s, __import__("uuid").UUID(rev_id), action_id, action_event)
        assert c.execute(text("SELECT CAST(finding_id AS text), CAST(finding_revision_id AS text) "
                              "FROM work_case_finding_link WHERE case_revision_id = :r"), {"r": rev_id}).one() == (fid, frev)
        assert sorted(c.execute(text("SELECT CAST(evidence_id AS text) FROM work_case_evidence WHERE "
                                     "case_revision_id = :r"), {"r": rev_id}).scalars()) == sorted(cited)
        for table, where, stamp in (("work_case", "id", "created_at"), ("work_case_revision", "case_id", "recorded_at"),
                                    ("work_event", "case_id", "recorded_at")):
            assert c.execute(text(f"SELECT authorization_basis, actor_kind, actor_id, {stamp} FROM {table} "
                                  f"WHERE {where} = :i"), {"i": case_id}).one() == (BASIS, "SERVICE", PRINCIPAL,
                                                                                    command_now)
    # The other roots store the same server-derived basis.
    _, req = ctx.case(request(incident_id=case_id, occurred_at=POSITIVE_OCCURRED))
    _, rec = ctx.record(req["id"], record(occurred_at=POSITIVE_OCCURRED))
    assert rec["outcome"] == "UNVERIFIED"
    _, pl = ctx.plan(plan(occurred_at=POSITIVE_OCCURRED))
    _, op = ctx.oprec(oprec(case_id=case_id, occurred_at=POSITIVE_OCCURRED))
    for table, row_id in (("maintenance_record", rec["id"]), ("maintenance_plan", pl["id"]),
                          ("operational_record", op["id"])):
        assert scalar(ctx.engine, f"SELECT authorization_basis FROM {table} WHERE id = :i", i=row_id) == BASIS


def test_request_complete_stays_unverified(runner, ctx) -> None:  # noqa: F811
    asset = scalar(ctx.engine, "SELECT CAST(id AS text) FROM asset WHERE site_id = :s ORDER BY id LIMIT 1", s=ctx.s)
    _, inc = ctx.case(incident())
    status, req = ctx.case(request(asset_id=asset, incident_id=inc["id"]))
    assert status == 201 and req["code"].startswith("WR-") and req["state"] == "OPEN"
    refused("WORK_INPUT_INVALID", ctx.record, inc["id"], record("w401-record-inc"))
    _, rec = ctx.record(req["id"], record())
    assert rec == {"schema_version": "maintenance-record-1", "id": rec["id"], "case_id": req["id"],
                   "recorded_at": rec["recorded_at"], "outcome": "UNVERIFIED"}
    assert ctx.event(req["id"], event("ASSIGN", {"assignee": "maintenance-lead"}, "w401-assign-001"))[1]["state"] == \
        "IN_PROGRESS"
    refused("WORK_INPUT_INVALID", ctx.event, req["id"], event("COMPLETE", {}, "w401-complete-000"))
    refused("WORK_LINK_SCOPE_INVALID", ctx.event, req["id"],
            event("COMPLETE", {"maintenance_record_id": str(uuid4())}, "w401-complete-001"))
    _, other = ctx.case(request("w401-request-002"))
    _, foreign_rec = ctx.record(other["id"], record("w401-record-002"))
    refused("WORK_LINK_SCOPE_INVALID", ctx.event, req["id"],
            event("COMPLETE", {"maintenance_record_id": foreign_rec["id"]}, "w401-complete-002"))
    status, done = ctx.event(req["id"], event("COMPLETE", {"maintenance_record_id": rec["id"]}, "w401-complete-003"))
    assert status == 201 and done["state"] == "COMPLETED" and done["schema_version"] == "work-event-1"
    assert done["revision_id"] == req["revision"]["id"]
    refused("WORK_TRANSITION_INVALID", ctx.event, req["id"], event("OPEN_VERIFICATION", {}, "w401-verify-001"))
    for outcome in ("VERIFIED", "INEFFECTIVE", "INCONCLUSIVE"):
        refused("WORK_OUTCOME_NOT_SUPPORTED", ctx.event, req["id"], event(outcome, {}, f"w401-{outcome.lower()}"))
    assert scalar(ctx.engine, "SELECT count(*) FROM work_event WHERE case_id = :i AND kind IN "
                              "('OPEN_VERIFICATION')", i=req["id"]) == 0


def test_transitions_and_correction_total_order(runner, ctx) -> None:  # noqa: F811
    _, inc = ctx.case(incident())
    cid = inc["id"]
    steps = [("ASSIGN", {"assignee": "a"}, "IN_PROGRESS"), ("ASSIGN", {"assignee": "b"}, "IN_PROGRESS"),
             ("REOPEN", {"reason": "back"}, "OPEN"), ("CLOSE", {"reason": "done"}, "CLOSED"),
             ("COMMENT", {"text": "note"}, "CLOSED"), ("REOPEN", {"reason": "again"}, "OPEN")]
    for n, (kind, payload, state) in enumerate(steps):
        assert ctx.event(cid, event(kind, payload, f"w401-step-{n:03d}"))[1]["state"] == state
    for kind, payload in (("REOPEN", {"reason": "x"}), ("CANCEL", {"reason": "x"}), ("COMPLETE", {
            "maintenance_record_id": str(uuid4())}), ("CREATED", {})):
        refused("WORK_TRANSITION_INVALID", ctx.event, cid, event(kind, payload, f"w401-bad-{kind.lower()}"))
    refused("WORK_INPUT_INVALID", ctx.event, cid, event("COMMENT", {"text": "x", "extra": 1}, "w401-extra-001"))
    refused("WORK_INPUT_INVALID", ctx.event, cid, event("COMMENT", {"text": "  "}, "w401-blank-001"))
    # Backdating: within 30 days accepted and kept as occurrence; order stays (recorded_at, id).
    assert ctx.event(cid, event("COMMENT", {"text": "late"}, "w401-late-001", occurred_at=at(days=2)))[0] == 201
    refused("WORK_OCCURRED_AT_TOO_OLD", ctx.event, cid, event("COMMENT", {"text": "x"}, "w401-old-001",
                                                              occurred_at=at(days=31)))
    refused("WORK_OCCURRED_AT_FUTURE", ctx.event, cid, event("COMMENT", {"text": "x"}, "w401-fut-001",
                                                             occurred_at=at(minutes=-10)))
    refused("WORK_INPUT_INVALID", ctx.event, cid, event("COMMENT", {"text": "x"}, "w401-tz-001",
                                                        occurred_at="2026-10-06T16:11:00+03:00"))
    with ctx.engine.connect() as c:
        rows = c.execute(text("SELECT kind, recorded_at, id FROM work_event WHERE case_id = :i ORDER BY recorded_at, id"),
                         {"i": cid}).all()
    assert [r[0] for r in rows] == ["CREATED"] + [s[0] for s in steps] + ["COMMENT"]
    # Corrections append a linear revision chain; a non-head predecessor is refused.
    rev1 = inc["revision"]["id"]
    correction = {"supersedes_revision_id": rev1, "title": "Witnessed start request failed",
                  "narrative": "Corrected occurrence note; cause remains unknown.", "reason": "Corrected time note",
                  "occurred_at": at(minutes=1), "actor": dict(ACTOR), "idempotency_key": "w401-correct-001"}
    status, rev2 = ctx.revise(cid, correction)
    assert status == 201 and rev2["revision_no"] == 2 and rev2["supersedes_revision_id"] == rev1
    refused("WORK_CORRECTION_CONFLICT", ctx.revise, cid, {**correction, "idempotency_key": "w401-correct-002"})
    assert ctx.revise(cid, correction) == (200, rev2)
    # A CANCELLED request accepts a text correction but no event.
    _, req = ctx.case(request())
    assert ctx.event(req["id"], event("CANCEL", {"reason": "dup"}, "w401-cancel-001"))[1]["state"] == "CANCELLED"
    for n, (kind, payload) in enumerate((("ASSIGN", {"assignee": "a"}), ("COMMENT", {"text": "x"}),
                                         ("REOPEN", {"reason": "x"}))):
        refused("WORK_TRANSITION_INVALID", ctx.event, req["id"], event(kind, payload, f"w401-after-cancel-{n}"))
    assert ctx.revise(req["id"], {**correction, "supersedes_revision_id": req["revision"]["id"],
                                  "idempotency_key": "w401-correct-003"})[0] == 201
    refused("WORK_CASE_NOT_FOUND", ctx.event, str(uuid4()), event("COMMENT", {"text": "x"}, "w401-none-001"))


def test_foreign_asset_and_evidence_refuse(runner, clocked, store) -> None:  # noqa: F811
    # q4-2: the command clock is after every F01/F02 pinned version, so each refusal below is the scope check.
    ctx = clocked
    run_case(runner, CASES["F01"])
    days = {f["anchor_start"].date().isoformat(): str(f["id"]) for f in runner.reload()["findings"]}
    f1 = days["2026-10-06"]
    a1, e1 = accepted_action(runner, f1, "w401-action-accept-001")
    # q2 ruling 5: F02's public proposal is null under the S6-02a battery hold, so the second Action is the
    # historical S6-01 Finding-scoped fixture (real evaluation + store accept with a pass-through guard).
    run_case(runner, CASES["F02"])
    h = harness(runner)
    try:
        f2 = str(h.findings()["2026-10-08"])
        a2 = accepted_before_battery_hold(h, h.findings()["2026-10-08"], "w401-wrong-action-f02")
    finally:
        h.close()
    assert a2 != a1
    with runner.engine.connect() as c:
        e2, e2_action, e2_tenant, e2_site = c.execute(text(
            "SELECT CAST(id AS text), CAST(action_id AS text), tenant_id, site_id FROM action_event "
            "WHERE action_id = :a AND kind = 'ACCEPTED'"), {"a": a2}).one()
    assert (e2_action, e2_tenant, e2_site) == (a2, runner.tenant, runner.site)
    imported(store, code="KOBO-002")
    with ctx.engine.connect() as c:
        other_site = c.execute(text("SELECT id FROM site WHERE tenant_id = :t AND id <> :s ORDER BY id LIMIT 1"),
                               {"t": ctx.t, "s": ctx.s}).scalar_one()
        foreign_asset = c.execute(text("SELECT CAST(id AS text) FROM asset WHERE site_id = :o LIMIT 1"),
                                  {"o": other_site}).scalar_one()
        rev1 = c.execute(text("SELECT CAST(id AS text) FROM finding_revision WHERE finding_id = :f LIMIT 1"),
                         {"f": f1}).scalar_one()
    before = counts(ctx.engine)
    for over in ({"asset_id": foreign_asset},
                 {"cited_accepted_evidence_ids": [str(uuid4())]},
                 {"finding_links": [{"finding_id": f2, "finding_revision_id": rev1}]},
                 {"finding_links": [{"finding_id": f1, "finding_revision_id": str(uuid4())}]},
                 {"action_links": [{"action_id": a1, "action_event_id": e2}]},
                 {"action_links": [{"action_id": str(uuid4()), "action_event_id": e1}]}):
        refused("WORK_LINK_SCOPE_INVALID", ctx.case, incident(**over))
    refused("WORK_LINK_SCOPE_INVALID", ctx.case, request(incident_id=str(uuid4())))
    refused("WORK_LINK_SCOPE_INVALID", ctx.plan, plan(asset_id=foreign_asset))
    refused("WORK_LINK_SCOPE_INVALID", ctx.oprec, oprec(case_id=str(uuid4())))
    assert counts(ctx.engine) == before
    # F01's own selected event is accepted.
    assert ctx.case(incident(action_links=[{"action_id": a1, "action_event_id": e1}]))[0] == 201


def test_idempotency_payload_conflict(runner, ctx) -> None:  # noqa: F811
    roots = ((ctx.case, incident()), (ctx.case, request()), (ctx.plan, plan()), (ctx.oprec, oprec()))
    for call, body in roots:
        status, first = call(body)
        assert status == 201
        assert call(body) == (200, first)
        refused("WORK_EVENT_DUPLICATE_KEY", call, {**body, "title" if "title" in body else "body": "Changed"})
    _, inc = ctx.case(incident("w401-incident-002"))
    body = event("COMMENT", {"text": "one"}, "w401-comment-001")
    _, first = ctx.event(inc["id"], body)
    ctx.event(inc["id"], event("ASSIGN", {"assignee": "a"}, "w401-assign-009"))
    assert ctx.event(inc["id"], body) == (200, first) and first["state"] == "OPEN"
    refused("WORK_EVENT_DUPLICATE_KEY", ctx.event, inc["id"], {**body, "payload": {"text": "two"}})
    # The create key reused for a later command on the same case is a different hash.
    refused("WORK_EVENT_DUPLICATE_KEY", ctx.event, inc["id"], event("COMMENT", {"text": "x"}, "w401-incident-002"))
    # Retry after a newer revision still returns the original result.
    corr = {"supersedes_revision_id": inc["revision"]["id"], "title": "T", "narrative": "N", "reason": "R",
            "occurred_at": at(minutes=1), "actor": dict(ACTOR), "idempotency_key": "w401-correct-001"}
    _, r2 = ctx.revise(inc["id"], corr)
    ctx.revise(inc["id"], {**corr, "supersedes_revision_id": r2["revision_id"], "idempotency_key": "w401-correct-002"})
    assert ctx.revise(inc["id"], corr) == (200, r2)
    refused("WORK_EVENT_DUPLICATE_KEY", ctx.revise, inc["id"], {**corr, "reason": "other"})


def test_plan_draft_version_and_due(runner, ctx) -> None:  # noqa: F811
    body = plan()
    status, root = ctx.plan(body)
    assert status == 201 and root["schema_version"] == "maintenance-plan-1" and root["state"] == "DRAFT"
    assert root["id"] == root["canonical_plan_id"] and root["public_code"].startswith("PM-")
    stored = scalar(ctx.engine, "SELECT occurred_at FROM maintenance_plan WHERE id = :i", i=root["id"])
    assert stored == datetime.fromisoformat(body["occurred_at"].replace("Z", "+00:00"))
    corr = plan("w401-plan-002", title="Witnessed start test (monthly)", supersedes_plan_id=root["id"],
                canonical_plan_id=root["id"], correction_reason="Name the cadence")
    status, v2 = ctx.plan(corr)
    assert status == 201 and v2["id"] != root["id"] and v2["canonical_plan_id"] == root["id"]
    assert v2["public_code"] == root["public_code"] and v2["state"] == "DRAFT"
    refused("WORK_CORRECTION_CONFLICT", ctx.plan, {**corr, "idempotency_key": "w401-plan-003"})
    refused("WORK_CORRECTION_CONFLICT", ctx.plan, {**corr, "idempotency_key": "w401-plan-004",
                                                   "supersedes_plan_id": v2["id"], "canonical_plan_id": v2["id"]})
    refused("WORK_INPUT_INVALID", ctx.plan, {k: v for k, v in plan("w401-plan-005").items() if k != "occurred_at"})
    refused("WORK_INPUT_INVALID", ctx.plan, plan("w401-plan-006", next_due_hours=5))
    refused("WORK_INPUT_INVALID", ctx.plan, {**corr, "idempotency_key": "w401-plan-007",
                                             "correction_reason": None})
    refused("WORK_OCCURRED_AT_FUTURE", ctx.plan, plan("w401-plan-008", occurred_at=at(minutes=-10)))
    refused("WORK_OCCURRED_AT_TOO_OLD", ctx.plan, plan("w401-plan-009", occurred_at=at(days=31)))
    _, hours = ctx.plan(plan("w401-plan-010", trigger_kind="RUN_HOURS", next_due_hours="250.50"))
    with ctx.engine.connect() as c:
        row = c.execute(text("SELECT next_due_hours, occurred_at, recorded_at, supersedes_plan_id, correction_reason "
                             "FROM maintenance_plan WHERE id = :i"), {"i": v2["id"]}).one()
        assert row[3] is not None and row[4] == "Name the cadence" and row[1] < row[2]
        assert str(c.execute(text("SELECT next_due_hours FROM maintenance_plan WHERE id = :i"),
                             {"i": hours["id"]}).scalar_one()) == "250.5"


def test_operational_record_attested_correction(runner, ctx) -> None:  # noqa: F811
    _, inc = ctx.case(incident())
    status, root = ctx.oprec(oprec(case_id=inc["id"]))
    assert status == 201 and root["state"] == "SUBMITTED" and root["public_code"].startswith("REC-")
    assert root["id"] == root["canonical_record_id"]
    refused("WORK_INPUT_INVALID", ctx.oprec, oprec("w401-oprec-002", kind="MANUAL_READING"))
    refused("WORK_INPUT_INVALID", ctx.oprec, oprec("w401-oprec-003", quantity=5))
    refused("WORK_INPUT_INVALID", ctx.oprec, oprec("w401-oprec-004", period_end=at(hours=2)))
    refused("WORK_INPUT_INVALID", ctx.oprec, oprec("w401-oprec-005", source_document_sha256="ABC"))
    _, reading = ctx.oprec(oprec("w401-oprec-006", kind="MANUAL_READING", quantity="12.0", unit="kWh"))
    assert scalar(ctx.engine, "SELECT unit FROM operational_record WHERE id = :i", i=reading["id"]) == "kWh"
    corr = oprec("w401-oprec-007", body="Generator started by hand at 16:14", supersedes_record_id=root["id"],
                 canonical_record_id=root["id"], correction_reason="Added the time")
    status, v2 = ctx.oprec(corr)
    assert status == 201 and v2["canonical_record_id"] == root["id"] and v2["public_code"] == root["public_code"]
    assert v2["state"] == "SUBMITTED" and v2["id"] != root["id"]
    refused("WORK_CORRECTION_CONFLICT", ctx.oprec, {**corr, "idempotency_key": "w401-oprec-008"})
    assert ctx.oprec(corr) == (200, v2)
    with ctx.engine.connect() as c:
        rows = c.execute(text("SELECT body, state, authorization_basis, attestation FROM operational_record "
                              "WHERE canonical_record_id = :r ORDER BY recorded_at, id"), {"r": root["id"]}).all()
    assert [r[0] for r in rows] == ["Generator started by hand", "Generator started by hand at 16:14"]
    assert {(r[1], r[2], r[3]) for r in rows} == {("SUBMITTED", BASIS, ACTOR["attestation"])}


def test_link_pin_newer_than_command_refuses(runner, clocked) -> None:  # noqa: F811
    """q4-2: a Finding revision or Action event created after the command's one `command_now` is not citable."""
    ctx = clocked
    run_case(runner, CASES["F01"])
    row = public_finding(runner)
    fid, frev = row["finding_id"], row["finding_revision_id"]
    action_id, action_event = accepted_action(runner, fid, "w401-newer-accept-001")
    made = scalar(ctx.engine, "SELECT created_at FROM finding_revision WHERE id = :r", r=frev)
    acted = scalar(ctx.engine, "SELECT recorded_at FROM action_event WHERE id = :e", e=action_event)
    finding = {"finding_links": [{"finding_id": fid, "finding_revision_id": frev}]}
    action = {"action_links": [{"action_id": action_id, "action_event_id": action_event}]}

    def stamp(value: datetime) -> str:
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

    before = counts(ctx.engine)
    for key, links, pinned in (("w401-newer-finding", finding, made), ("w401-newer-action", action, acted)):
        ctx.clock.now = pinned - timedelta(microseconds=1)
        body = incident(key, occurred_at=stamp(pinned - timedelta(minutes=1)), **links)
        refused("WORK_LINK_SCOPE_INVALID", ctx.case, body)
        assert ctx.clock.returned[-1] == pinned - timedelta(microseconds=1)
        assert counts(ctx.engine) == before
    # Advancing the command clock past each pinned timestamp permits the exact same pair.
    for key, links, pinned in (("w401-newer-finding", finding, made), ("w401-newer-action", action, acted)):
        ctx.clock.now = pinned + timedelta(seconds=1)
        body = incident(key, occurred_at=stamp(pinned - timedelta(minutes=1)), **links)
        status, created = ctx.case(body)
        assert status == 201, created
