"""W5-02a K1a: migration `0033_w5_cold_work`, its DB checks/triggers, and the three domain Action commands.

`.agent/W5-02-build-spec.md` "K1 migration", "Backend wire, validation and lineage (K1a-K1c)" and the Architect
pre-flight ruling A1-A4. The cold Finding is produced by the ordinary W2-02 registered replay (`backup-failed`)
and the W2-03 worker, and its selection is the real W4 linked-selection pin; no Finding, evidence or pin is
invented. W4 cases are created through the W4 service. Direct-SQL rows exercise only DB constraints.
Requires ASSETOPS_TEST_DATABASE_URL naming a `*_test` database.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from test_s4_finding_store_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError, IntegrityError
    from test_s1_bindings_postgres import _alembic, imported
    from test_w202_cold_replay_postgres import COLD, chain  # noqa: F401 - the W2-02 replay fixture
    from test_w203_cold_migration_postgres import _replica, head
    from test_w203_cold_replay_postgres import opened, run
    from test_w401_work_service_postgres import ACTOR, PRINCIPAL, event, incident, oprec, record, request

    from assetops_backend.work import domain_action as d
    from assetops_backend.work.adapters.postgres_domain_intent import PostgresDomainIntentStore
    from assetops_backend.work.domain_intent import DomainIntentService
    from assetops_backend.work.composition import build_domain_intent_service, build_work_service
    from assetops_backend.work.model import WorkRefused

HEAD = "0034_w5_ev_scenarios"
PREVIOUS = "0032_w5_cold_scenarios"
REFUSED = "Downgrade of 0033_w5_cold_work refused: domain Action rows exist."
TABLES = ("domain_action", "domain_action_intent", "domain_action_case_link")
APPEND_ONLY = "W4 work history is append only"
SHA = "0" * 64


def iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def now_utc(engine) -> datetime:
    with engine.connect() as c:
        return c.execute(text("SELECT clock_timestamp()")).scalar_one().astimezone(timezone.utc)


def criteria() -> list[dict]:
    return [{"key": k, "label": label, "required_evidence": req} for k, label, req in d.CRITERIA]


def counts(engine) -> list[int]:
    with engine.connect() as c:
        return [c.execute(text(f"SELECT count(*) FROM {t}")).scalar_one() for t in TABLES]


def refused(code: str, call, *args):
    with pytest.raises(d.DomainIntentRefused) as caught:
        call(*args)
    assert (caught.value.code, caught.value.message, caught.value.status) == (code, d.MESSAGES[code], d.STATUS[code])


@pytest.fixture()
def cold(chain):  # noqa: F811
    """One ordinary cold replay, its selected cold Finding revision and cited accepted evidence."""
    built = opened("backup-failed", chain)
    run(built)
    with built.engine.connect() as c:
        pin = c.execute(text(
            "SELECT CAST(finding_id AS text), CAST(id AS text) FROM finding_revision WHERE site_id = :s "
            "AND domain = 'cold_chain' ORDER BY created_at DESC, id LIMIT 1"), {"s": built.site_id}).first()
        assert pin is not None, "the cold replay wrote no cold Finding"
        cited = sorted(str(v) for v in c.execute(text(
            "SELECT evidence_id FROM finding_revision_evidence WHERE finding_revision_id = :r"),
            {"r": pin[1]}).scalars())
    assert cited, "the selected cold Finding revision cites no accepted evidence"
    svc, work = build_domain_intent_service(URL), build_work_service(URL)
    ns = SimpleNamespace(t=built.tenant_id, s=built.site_id, engine=built.engine, store=built.store, finding_id=pin[0],
                         revision_id=pin[1], cited=cited, svc=svc, work=work, code=COLD)
    yield ns
    svc._store.dispose()
    work._store.dispose()


def action_body(cold, key="w502-action-0001", **over) -> dict:
    return {"domain": "COLDCHAIN", "origin_finding_id": cold.finding_id, "origin_finding_revision_id": cold.revision_id,
            "title": "Witness automatic-start test", "owner_label": "Maintenance lead", "due_at": None,
            "raised_at": iso(now_utc(cold.engine) - timedelta(minutes=10)), "actor": dict(ACTOR),
            "idempotency_key": key, **over}


def create(cold, body):
    return cold.svc.create_action(cold.t, cold.s, cold.code, body, PRINCIPAL)


def intent(cold, action_id, body):
    return cold.svc.post_intent(cold.t, cold.s, cold.code, action_id, body, PRINCIPAL)


def link(cold, action_id, body):
    return cold.svc.post_case_link(cold.t, cold.s, cold.code, action_id, body, PRINCIPAL)


def intent_body(cold, key="w502-intent-0001", supersedes=None, **basis) -> dict:
    return {"supersedes_id": supersedes, "declared_at": iso(now_utc(cold.engine) - timedelta(minutes=1)),
            "criteria": criteria(), "basis": {"finding_revision_id": cold.revision_id, "work_case_id": None,
                                              "work_record_id": None, "accepted_evidence_ids": list(cold.cited),
                                              **basis},
            "actor": dict(ACTOR), "idempotency_key": key}


def w4_request(cold, key: str) -> dict:
    status, created = cold.work.create_case(cold.t, cold.s, request(key), PRINCIPAL)
    assert status == 201, created
    return created


def head_event(cold, case_id: str) -> str:
    with cold.engine.connect() as c:
        return str(c.execute(text("SELECT id FROM work_event WHERE case_id = :c ORDER BY recorded_at DESC, id DESC "
                                  "LIMIT 1"), {"c": case_id}).scalar_one())


def link_body(case_id, revision_id, event_id, key="w502-link-0001") -> dict:
    return {"case_id": case_id, "case_revision_id": revision_id, "case_event_id": event_id, "actor": dict(ACTOR),
            "idempotency_key": key}


# ---- commands ----------------------------------------------------------------------------------------------------

def test_action_root_idempotency_and_selection(cold) -> None:
    body = action_body(cold, title="  Witness automatic-start test  ")
    status, first = create(cold, body)
    assert status == 201 and set(first) == {"schema_version", "id", "action_code", "recorded_at"}, first
    assert first["schema_version"] == "domain-action-1" and first["action_code"].startswith("ACT-")
    with cold.engine.connect() as c:
        row = c.execute(text("SELECT action_no, action_code, title, domain, recorded_at, actor_kind, attestation "
                             "FROM domain_action WHERE id = :i"), {"i": first["id"]}).one()
    assert row.action_code == f"ACT-{row.action_no:06d}" and row.title == "Witness automatic-start test"
    assert (row.domain, row.actor_kind, row.attestation) == ("COLDCHAIN", "SERVICE", ACTOR["attestation"])
    assert iso(row.recorded_at) == first["recorded_at"]
    # Identical retry (trimmed title hashes the same): 200 with the original response; nothing new written.
    assert create(cold, {**body, "title": "Witness automatic-start test"}) == (200, first)
    assert counts(cold.engine) == [1, 0, 0]
    refused("DOMAIN_INTENT_CONFLICT", create, cold, {**body, "owner_label": None})
    # The code comes from the shared W1 sequence: the next root takes the next number.
    status, second = create(cold, action_body(cold, "w502-action-0002"))
    assert status == 201 and int(second["action_code"][4:]) > int(first["action_code"][4:])
    # DB-time bounds and the selected cold Finding.
    old = iso(now_utc(cold.engine) - timedelta(days=31))
    refused("DOMAIN_INTENT_INVALID", create, cold, action_body(cold, "w502-action-0003", raised_at=old))
    future = iso(now_utc(cold.engine) + timedelta(minutes=10))
    refused("DOMAIN_INTENT_INVALID", create, cold, action_body(cold, "w502-action-0004", raised_at=future))
    refused("DOMAIN_INTENT_LINK_INVALID", create, cold,
            action_body(cold, "w502-action-0005", origin_finding_revision_id=str(uuid4())))
    # The exact revision exists but is not the selected cold result at the command time: refused, nothing written.
    unselected = DomainIntentService(PostgresDomainIntentStore(URL, pin_of=lambda *args: None))
    try:
        refused("DOMAIN_INTENT_LINK_INVALID", unselected.create_action, cold.t, cold.s, cold.code,
                action_body(cold, "w502-action-0007"), PRINCIPAL)
    finally:
        unselected._store.dispose()
    assert counts(cold.engine) == [2, 0, 0]
    # The W4 gate: no principal 403, a USER actor 403, a bad attestation 422; nothing written.
    with pytest.raises(WorkRefused) as caught:
        cold.svc.create_action(cold.t, cold.s, cold.code, action_body(cold, "w502-action-0006"), None)
    assert caught.value.code == "WORK_WRITE_FORBIDDEN"
    with pytest.raises(WorkRefused) as caught:
        create(cold, action_body(cold, "w502-action-0006", actor={**ACTOR, "kind": "USER"}))
    assert caught.value.code == "WORK_USER_AUTH_REQUIRED"
    with pytest.raises(WorkRefused) as caught:
        create(cold, action_body(cold, "w502-action-0006", actor={**ACTOR, "attestation": "nope"}))
    assert caught.value.code == "WORK_ATTESTATION_INVALID"
    assert counts(cold.engine) == [2, 0, 0]


def test_case_link_and_intent_chain(cold) -> None:
    _, action = create(cold, action_body(cold))
    aid = action["id"]
    wr = w4_request(cold, "w502-request-0001")
    case_id, rev_id = wr["id"], wr["revision"]["id"]
    ev = head_event(cold, case_id)
    # Missing Action is 404 for both child commands.
    refused("ACTION_NOT_FOUND", link, cold, str(uuid4()), link_body(case_id, rev_id, ev))
    refused("ACTION_NOT_FOUND", intent, cold, "not-a-uuid", intent_body(cold))
    status, linked = link(cold, aid, link_body(case_id, rev_id, ev))
    assert status == 201 and linked["schema_version"] == "domain-action-case-link-1", linked
    assert (linked["action_id"], linked["case_id"]) == (aid, case_id)
    assert link(cold, aid, link_body(case_id, rev_id, ev)) == (200, linked)
    other = w4_request(cold, "w502-request-0002")
    refused("DOMAIN_INTENT_BASIS_CHANGED", link, cold, aid, link_body(other["id"], other["revision"]["id"],
                                                                      head_event(cold, other["id"])))
    refused("DOMAIN_INTENT_LINK_INVALID", link, cold, aid,
            link_body(case_id, rev_id, head_event(cold, other["id"]), key="w502-link-0002"))
    # A newer event makes the named selection stale: 409 basis changed; the new head links.
    s, _ = cold.work.post_event(cold.t, cold.s, case_id, event("ASSIGN", {"assignee": "maintenance-lead"},
                                                                      "w502-assign-0001"), PRINCIPAL)
    assert s == 201
    refused("DOMAIN_INTENT_BASIS_CHANGED", link, cold, aid, link_body(case_id, rev_id, ev, key="w502-link-0003"))
    s, rec = cold.work.post_record(cold.t, cold.s, case_id, record("w502-record-0001"), PRINCIPAL)
    assert s == 201, rec
    record_id = rec["id"]
    new_ev = head_event(cold, case_id)
    status, relinked = link(cold, aid, link_body(case_id, rev_id, new_ev, key="w502-link-0004"))
    assert status == 201
    refused("DOMAIN_INTENT_CONFLICT", link, cold, aid, link_body(case_id, rev_id, new_ev, key="w502-link-0005"))

    # Intent: an unlinked case, a foreign record, uncited evidence and a different Finding pin refuse.
    refused("DOMAIN_INTENT_LINK_INVALID", intent, cold, aid,
            intent_body(cold, work_case_id=other["id"]))
    refused("DOMAIN_INTENT_LINK_INVALID", intent, cold, aid,
            intent_body(cold, work_case_id=case_id, work_record_id=str(uuid4())))
    refused("DOMAIN_INTENT_LINK_INVALID", intent, cold, aid,
            intent_body(cold, accepted_evidence_ids=[str(uuid4())]))
    refused("DOMAIN_INTENT_LINK_INVALID", intent, cold, aid, intent_body(cold, finding_revision_id=str(uuid4())))
    early = intent_body(cold)
    early["declared_at"] = iso(now_utc(cold.engine) - timedelta(hours=2))  # before the Action's raised_at
    refused("DOMAIN_INTENT_INVALID", intent, cold, aid, early)
    assert counts(cold.engine)[1] == 0

    body = intent_body(cold, work_case_id=case_id, work_record_id=record_id)
    status, root = intent(cold, aid, body)
    assert status == 201 and set(root) == {"schema_version", "intent_id", "action_id", "recorded_at",
                                           "selection_token"}, root
    assert root["schema_version"] == "domain-action-intent-1" and root["selection_token"].startswith("sha256:")
    with cold.engine.connect() as c:
        raised = c.execute(text("SELECT raised_at FROM domain_action WHERE id = :i"), {"i": aid}).scalar_one()
    assert root["selection_token"] == d.selection_token(
        cold.t, cold.s, {"id": aid, "raised_at": raised}, cold.revision_id, root["intent_id"],
        {"case_id": case_id, "case_revision_id": rev_id, "case_event_id": new_ev}, record_id, cold.cited)
    assert intent(cold, aid, body) == (200, root)
    refused("DOMAIN_INTENT_CONFLICT", intent, cold, aid, {**body, "basis": {**body["basis"], "work_record_id": None}})
    refused("DOMAIN_INTENT_CONFLICT", intent, cold, aid, intent_body(cold, "w502-intent-0002"))  # second root
    status, v2 = intent(cold, aid, intent_body(cold, "w502-intent-0003", supersedes=root["intent_id"]))
    assert status == 201
    refused("DOMAIN_INTENT_CONFLICT", intent, cold, aid,
            intent_body(cold, "w502-intent-0004", supersedes=root["intent_id"]))  # not the head
    assert counts(cold.engine) == [1, 2, 2]
    assert relinked["case_link_id"] != linked["case_link_id"] and v2["intent_id"] != root["intent_id"]


def _advance_case(cold, case_id: str, key: str) -> None:
    status, _ = cold.work.post_event(cold.t, cold.s, case_id, event("ASSIGN", {"assignee": "maintenance-lead"}, key),
                                     PRINCIPAL)
    assert status == 201


@pytest.mark.parametrize("kind", ["operational_record", "other_case_record", "other_site_record"])
def test_intent_rejects_operational_or_foreign_maintenance_record(cold, kind) -> None:
    _, action = create(cold, action_body(cold))
    aid = action["id"]
    wr = w4_request(cold, "w502-request-0001")
    case_id, rev_id = wr["id"], wr["revision"]["id"]
    assert link(cold, aid, link_body(case_id, rev_id, head_event(cold, case_id)))[0] == 201
    if kind == "operational_record":
        status, made = cold.work.post_operational_record(cold.t, cold.s, oprec("w502-oprec-0001"), PRINCIPAL)
    elif kind == "other_case_record":
        other = w4_request(cold, "w502-request-0002")
        status, made = cold.work.post_record(cold.t, cold.s, other["id"], record("w502-record-0002"), PRINCIPAL)
    else:
        imported(cold.store, code="KOBO-002")
        with cold.engine.connect() as c:
            other_site = c.execute(text("SELECT id FROM site WHERE tenant_id = :t AND id <> :s ORDER BY id LIMIT 1"),
                                   {"t": cold.t, "s": cold.s}).scalar_one()
        status, other = cold.work.create_case(cold.t, other_site, request("w502-request-0003"), PRINCIPAL)
        assert status == 201, other
        status, made = cold.work.post_record(cold.t, other_site, other["id"], record("w502-record-0003"), PRINCIPAL)
    assert status == 201, made
    refused("DOMAIN_INTENT_LINK_INVALID", intent, cold, aid,
            intent_body(cold, work_case_id=case_id, work_record_id=made["id"]))
    assert counts(cold.engine)[1] == 0


def test_case_link_original_retry_after_case_advance_returns_200(cold) -> None:
    _, action = create(cold, action_body(cold))
    wr = w4_request(cold, "w502-request-0001")
    case_id, rev_id = wr["id"], wr["revision"]["id"]
    body = link_body(case_id, rev_id, head_event(cold, case_id))
    status, linked = link(cold, action["id"], body)
    assert status == 201
    _advance_case(cold, case_id, "w502-assign-0001")
    refused("DOMAIN_INTENT_BASIS_CHANGED", link, cold, action["id"], {**body, "idempotency_key": "w502-link-0009"})
    assert link(cold, action["id"], body) == (200, linked)
    assert counts(cold.engine)[2] == 1


def test_absent_action_precedes_invalid_link_with_404(cold) -> None:
    _, action = create(cold, action_body(cold))
    wr = w4_request(cold, "w502-request-0001")
    case_id, rev_id = wr["id"], wr["revision"]["id"]
    invalid = link_body(case_id, rev_id, str(uuid4()), key="w502-link-0001")
    refused("ACTION_NOT_FOUND", link, cold, str(uuid4()), invalid)
    refused("ACTION_NOT_FOUND", intent, cold, str(uuid4()),
            intent_body(cold, work_case_id=str(uuid4()), work_record_id=str(uuid4())))
    refused("DOMAIN_INTENT_LINK_INVALID", link, cold, action["id"], invalid)
    assert counts(cold.engine) == [1, 0, 0]


# ---- schema, triggers and downgrade --------------------------------------------------------------------------------

def _root_sql(cold, code="ACT-900001", no=900001, **over) -> dict:
    return {"id": str(uuid4()), "t": cold.t, "s": cold.s, "no": no, "code": code, "f": cold.finding_id,
            "r": cold.revision_id, "title": "T", "dom": "COLDCHAIN", "sha": SHA, "key": f"w502-sql-{no}", **over}


ROOT_INSERT = ("INSERT INTO domain_action (id, tenant_id, site_id, action_no, action_code, domain, origin_finding_id, "
               "origin_finding_revision_id, title, raised_at, actor_kind, actor_id, attestation, idempotency_key, "
               "payload_sha256) VALUES (:id, :t, :s, :no, :code, :dom, :f, :r, :title, clock_timestamp(), 'SERVICE', "
               "'service:x', 'a', :key, :sha)")
INTENT_INSERT = ("INSERT INTO domain_action_intent (id, tenant_id, site_id, action_id, supersedes_id, declared_at, "
                 "criteria, basis, actor_kind, actor_id, attestation, idempotency_key, payload_sha256) VALUES "
                 "(:id, :t, :s, :a, :p, clock_timestamp(), CAST(:c AS jsonb), CAST(:b AS jsonb), 'SERVICE', 's', 'a', "
                 ":key, :sha)")
LINK_INSERT = ("INSERT INTO domain_action_case_link (id, tenant_id, site_id, action_id, case_id, case_revision_id, "
               "case_event_id, actor_kind, actor_id, attestation, idempotency_key, payload_sha256) VALUES "
               "(:id, :t, :s, :a, :c, :r, :e, 'SERVICE', 's', 'a', :key, :sha)")


def _rejects(engine, sql: str, params: dict, match: str | None = None) -> None:
    with pytest.raises(DBAPIError) as caught:
        with engine.begin() as c:
            c.execute(text(sql), params)
    if match is not None:
        constraint = getattr(getattr(caught.value.orig, "diag", None), "constraint_name", None)
        assert match == constraint or match in str(caught.value), caught.value


def test_db_checks_triggers_and_downgrade(cold) -> None:
    import json

    engine = cold.engine
    assert head(engine) == HEAD
    for over in ({"code": "ACT-12345"}, {"code": "WR-000001"}, {"dom": "MINIGRID"}, {"title": " T"},
                 {"title": "x" * 161}, {"sha": "ABC"}, {"key": "short"}, {"r": str(uuid4())}):
        _rejects(engine, ROOT_INSERT, _root_sql(cold, **over))
    root = _root_sql(cold)
    with engine.begin() as c:
        c.execute(text(ROOT_INSERT), root)
    _rejects(engine, ROOT_INSERT, _root_sql(cold, no=900002), "domain_action_code")  # same code twice
    four, base = json.dumps(criteria()), json.dumps({"finding_revision_id": cold.revision_id})
    three = json.dumps(criteria()[:3])
    ip = {"t": cold.t, "s": cold.s, "a": root["id"], "p": None, "sha": SHA}
    _rejects(engine, INTENT_INSERT, {**ip, "id": str(uuid4()), "c": three, "b": base, "key": "w502-i-0001"},
             "domain_action_intent_criteria_count_chk")
    _rejects(engine, INTENT_INSERT, {**ip, "id": str(uuid4()), "c": four, "b": "[]", "key": "w502-i-0001"})
    first = str(uuid4())
    with engine.begin() as c:
        c.execute(text(INTENT_INSERT), {**ip, "id": first, "c": four, "b": base, "key": "w502-i-0001"})
    _rejects(engine, INTENT_INSERT, {**ip, "id": str(uuid4()), "c": four, "b": base, "key": "w502-i-0002"},
             "domain_action_intent_root")
    _rejects(engine, INTENT_INSERT, {**ip, "id": str(uuid4()), "p": str(uuid4()), "c": four, "b": base,
                                     "key": "w502-i-0003"}, "domain_action_intent_prev_fk")
    with engine.begin() as c:
        c.execute(text(INTENT_INSERT), {**ip, "id": str(uuid4()), "p": first, "c": four, "b": base,
                                        "key": "w502-i-0004"})
    _rejects(engine, INTENT_INSERT, {**ip, "id": str(uuid4()), "p": first, "c": four, "b": base,
                                     "key": "w502-i-0005"}, "domain_action_intent_one_successor")
    # Case link: revision and event must be of the named case (direct SQL refused by the trigger).
    a = w4_request(cold, "w502-sql-request-01")
    b = w4_request(cold, "w502-sql-request-02")
    lp = {"t": cold.t, "s": cold.s, "a": root["id"], "sha": SHA}
    a_ev, b_ev = head_event(cold, a["id"]), head_event(cold, b["id"])
    for case, rev, ev in ((a["id"], a["revision"]["id"], b_ev), (a["id"], b["revision"]["id"], a_ev)):
        _rejects(engine, LINK_INSERT, {**lp, "id": str(uuid4()), "c": case, "r": rev, "e": ev, "key": "w502-l-0001"},
                 "domain_action_case_link_case_consistency")
    with engine.begin() as c:
        c.execute(text(LINK_INSERT), {**lp, "id": str(uuid4()), "c": a["id"], "r": a["revision"]["id"], "e": a_ev,
                                      "key": "w502-l-0001"})
    # Append-only: every table refuses UPDATE and DELETE (root included).
    for table in TABLES:
        _rejects(engine, f"UPDATE {table} SET recorded_at = recorded_at", {}, APPEND_ONLY)
        _rejects(engine, f"DELETE FROM {table}", {}, APPEND_ONLY)
    assert counts(engine) == [1, 2, 1]

    cold.svc._store.dispose()
    cold.work._store.dispose()
    from alembic import command

    config = _alembic()
    engine.dispose()
    with pytest.raises(DBAPIError, match=REFUSED):
        command.downgrade(config, PREVIOUS)
    assert head(engine) == HEAD and counts(engine) == [1, 2, 1]
    _replica(engine, "DELETE FROM domain_action_case_link", "DELETE FROM domain_action_intent",
             "DELETE FROM domain_action")
    engine.dispose()
    command.downgrade(config, PREVIOUS)
    with engine.connect() as c:
        assert head(engine) == PREVIOUS
        assert [c.execute(text("SELECT to_regclass(:n)"), {"n": t}).scalar() for t in TABLES] == [None] * 3
        assert c.execute(text("SELECT count(*) FROM pg_trigger WHERE tgname = 'w1_action_cross_domain_code'")
                         ).scalar_one() == 0
        assert c.execute(text("SELECT count(*) FROM pg_proc WHERE proname IN "
                              "('reject_cross_domain_action_code', 'domain_action_case_link_consistency')")
                         ).scalar_one() == 0
    engine.dispose()
    command.upgrade(config, "head")
    assert head(engine) == HEAD
    with engine.connect() as c:
        assert c.execute(text("SELECT count(*) FROM pg_trigger WHERE tgname IN ('w1_action_cross_domain_code', "
                              "'domain_action_cross_domain_code')")).scalar_one() == 2


# Ruling A4: one global Action code space per tenant across W1 `action` and `domain_action`, held by the 0033
# trigger under an advisory lock. W1 rows here are direct SQL against the cold replay's real persisted rows.
CROSS = "action_cross_domain_code_conflict"
CROSS_MESSAGE = "Action code already belongs to another Action."
W1_INSERT = ("INSERT INTO action (id, tenant_id, site_id, action_no, action_code, recommendation_key, acceptance_key, "
             "acceptance_payload_sha256, origin_finding_id, origin_finding_revision_id, primary_assessment_revision_id, "
             "foundation_revision_id, asset_id, rule_id, rule_version, field, unit, old_value, proposed_value, "
             "limitation_code, limitation_text, input_sha256, snapshot, snapshot_sha256, created_at) VALUES "
             "(:id, :t, :s, :no, :code, :rk, :rk, :sha, :f, :r, :ar, :fo, :asset, 'reserve-trial-1', 1, "
             "'reserve-state-of-charge', '%', 20, 15, 'x', 'x', :sha, CAST('{}' AS jsonb), :sha, clock_timestamp())")


def _w1_sql(cold, no: int) -> dict:
    with cold.engine.connect() as c:
        ar = c.execute(text("SELECT id FROM assessment_revision WHERE site_id = :s LIMIT 1"), {"s": cold.s}).scalar()
        fo = c.execute(text("SELECT id FROM foundation_revision WHERE site_id = :s LIMIT 1"), {"s": cold.s}).scalar()
        asset = c.execute(text("SELECT id FROM asset WHERE site_id = :s LIMIT 1"), {"s": cold.s}).scalar()
    assert None not in (ar, fo, asset), "the cold replay has no assessment, Foundation revision or asset to cite"
    return {"id": str(uuid4()), "t": cold.t, "s": cold.s, "no": no, "code": f"ACT-{no:06d}", "rk": f"{no:064x}",
            "sha": SHA, "f": cold.finding_id, "r": cold.revision_id, "ar": ar, "fo": fo, "asset": asset}


def _held(engine, code: str) -> tuple[int, int]:
    with engine.connect() as c:
        return tuple(c.execute(text(f"SELECT count(*) FROM {t} WHERE action_code = :c"), {"c": code}).scalar_one()
                     for t in ("action", "domain_action"))


def _cross_refused(engine, sql: str, params: dict) -> None:
    with pytest.raises(IntegrityError) as caught:
        with engine.begin() as c:
            c.execute(text(sql), params)
    orig = caught.value.orig
    assert (orig.sqlstate, orig.diag.constraint_name, orig.diag.message_primary) == ("23505", CROSS, CROSS_MESSAGE)


def test_cross_domain_code_collisions(cold) -> None:
    import threading

    engine = cold.engine
    # Direct SQL, W1 first: the domain insert of the same code is refused.
    with engine.begin() as c:
        c.execute(text(W1_INSERT), _w1_sql(cold, 910001))
    _cross_refused(engine, ROOT_INSERT, _root_sql(cold, code="ACT-910001", no=910001))
    assert _held(engine, "ACT-910001") == (1, 0)
    # Direct SQL, domain first: the W1 insert of the same code is refused.
    with engine.begin() as c:
        c.execute(text(ROOT_INSERT), _root_sql(cold, code="ACT-910002", no=910002))
    _cross_refused(engine, W1_INSERT, _w1_sql(cold, 910002))
    assert _held(engine, "ACT-910002") == (0, 1)

    # Domain command: the shared sequence's next code already belongs to a W1 Action -> 409 DOMAIN_INTENT_CONFLICT.
    with engine.begin() as c:
        number = c.execute(text("SELECT nextval('action_code_seq')")).scalar_one() + 1
        c.execute(text(W1_INSERT), _w1_sql(cold, number))
    before = counts(engine)
    with pytest.raises(d.DomainIntentRefused) as caught:
        create(cold, action_body(cold, "w502-collision-0001"))
    assert (caught.value.status, caught.value.code, caught.value.message) == (
        409, "DOMAIN_INTENT_CONFLICT", "This Action declaration has a newer version; reload it.")
    assert counts(engine) == before and _held(engine, f"ACT-{number:06d}") == (1, 0)

    # Two concurrent sessions, each order: the first committed root wins, the second waits on the advisory lock
    # and gets the named 23505; nothing of the loser is stored.
    for no, (first_sql, first), (second_sql, second), expected in (
            (910003, (ROOT_INSERT, _root_sql(cold, code="ACT-910003", no=910003)),
             (W1_INSERT, _w1_sql(cold, 910003)), (0, 1)),
            (910004, (W1_INSERT, _w1_sql(cold, 910004)),
             (ROOT_INSERT, _root_sql(cold, code="ACT-910004", no=910004)), (1, 0))):
        errors: list = []

        def loser(sql=second_sql, params=second) -> None:
            try:
                with engine.begin() as c:
                    c.execute(text(sql), params)
            except IntegrityError as error:
                errors.append(error.orig)

        with engine.connect() as winner:
            tx = winner.begin()
            winner.execute(text(first_sql), first)
            thread = threading.Thread(target=loser)
            thread.start()
            with engine.connect() as probe:
                for _ in range(200):
                    waiting = probe.execute(text(
                        "SELECT count(*) FROM pg_stat_activity WHERE wait_event_type = 'Lock' "
                        "AND wait_event = 'advisory' AND datname = current_database()")).scalar_one()
                    if waiting:
                        break
                    threading.Event().wait(0.05)
            assert waiting == 1, "the second session never waited on the cross-domain code lock"
            tx.commit()
        thread.join(30)
        assert not thread.is_alive() and len(errors) == 1
        assert (errors[0].sqlstate, errors[0].diag.constraint_name) == ("23505", CROSS)
        assert _held(engine, f"ACT-{no:06d}") == expected


# ---- W5-02c K5: end-to-end lineage through the product GET (P-K5-1, ruling 5) -------------------------------------

def test_k5_cold_action_lineage_through_product_get(cold, monkeypatch) -> None:
    """Accepted envelope IDs -> selected cold Finding revision -> domain Action -> selected completed WR revision and
    performed record -> intent basis, then the same chain read through `GET /api/sites/{site}/domain-work/actions/{id}`
    at the captured cutoffs. The initial results stay `NOT_TESTED, NOT_TESTED, NOT_ESTABLISHED, PENDING` with no
    evidence; no restoration or verification is inferred (`.agent/W5-02c-K4-preflight-rulings.md` ruling 5)."""
    from fastapi.testclient import TestClient
    from test_w401_work_service_postgres import at as w4_at

    from assetops_backend.config import load_feature_flags
    from assetops_backend.main import create_app

    # 1. The selected Finding revision cites only ACCEPTED ingested evidence.
    with cold.engine.connect() as c:
        accepted = sorted(str(v) for v in c.execute(text(
            "SELECT accepted_evidence_id FROM ingestion_disposition WHERE site_id = :s AND decision = 'ACCEPTED' "
            "AND accepted_evidence_id = ANY(CAST(:e AS uuid[]))"), {"s": cold.s, "e": cold.cited}).scalars())
    assert accepted == cold.cited
    # 2. The WR, its performed record and its completion, all before the Action root (as the producer orders them).
    wr = w4_request(cold, "w502c-k5-request")
    case_id, rev_id = wr["id"], wr["revision"]["id"]
    s, rec = cold.work.post_record(cold.t, cold.s, case_id, record("w502c-k5-record", occurred_at=w4_at(minutes=20)),
                                   PRINCIPAL)
    assert s == 201, rec
    s, got = cold.work.post_event(cold.t, cold.s, case_id, event("ASSIGN", {"assignee": "Maintenance lead"},
                                                                 "w502c-k5-assign", occurred_at=w4_at(minutes=15)),
                                  PRINCIPAL)
    assert s == 201 and got["state"] == "IN_PROGRESS", got
    s, got = cold.work.post_event(cold.t, cold.s, case_id, event("COMPLETE", {"maintenance_record_id": rec["id"]},
                                                                 "w502c-k5-complete", occurred_at=w4_at(minutes=10)),
                                  PRINCIPAL)
    assert s == 201 and got["state"] == "COMPLETED", got
    before_action = now_utc(cold.engine)
    # 3. Action root (K1), case link (K2), intent (K3), each pinned to the selected IDs.
    _, action = create(cold, action_body(cold, "w502c-k5-action"))
    aid = action["id"]
    k1 = datetime.fromisoformat(action["recorded_at"].replace("Z", "+00:00"))
    s, linked = link(cold, aid, link_body(case_id, rev_id, head_event(cold, case_id), key="w502c-k5-link"))
    assert s == 201, linked
    refused("DOMAIN_INTENT_LINK_INVALID", intent, cold, aid,
            intent_body(cold, "w502c-k5-altered", finding_revision_id=str(uuid4()), work_case_id=case_id,
                        work_record_id=rec["id"]))  # an altered Finding pin is refused, nothing written
    s, root = intent(cold, aid, intent_body(cold, "w502c-k5-intent", work_case_id=case_id, work_record_id=rec["id"]))
    assert s == 201, root
    with cold.engine.connect() as c:
        stored = c.execute(text(
            "SELECT a.origin_finding_revision_id, l.case_id, l.case_revision_id, i.basis FROM domain_action a "
            "JOIN domain_action_case_link l ON l.action_id = a.id JOIN domain_action_intent i ON i.action_id = a.id "
            "WHERE a.id = :a"), {"a": aid}).one()
    assert (str(stored[0]), str(stored[1]), str(stored[2])) == (cold.revision_id, case_id, rev_id)
    assert stored[3]["finding_revision_id"] == cold.revision_id and stored[3]["work_record_id"] == rec["id"]
    assert sorted(stored[3]["accepted_evidence_ids"]) == accepted

    # 4. The product GET at the captured cutoffs.
    monkeypatch.setenv("DATABASE_URL", URL)
    api = TestClient(create_app(load_feature_flags()))
    path = f"/api/sites/{cold.code}/domain-work/actions/{aid}"
    current = api.get(path)
    assert current.status_code == 200, current.text
    body = current.json()
    assert body["intent"]["id"] == root["intent_id"]
    assert [r["result"] for r in body["results"]] == ["NOT_TESTED", "NOT_TESTED", "NOT_ESTABLISHED", "PENDING"]
    assert all(r["evidence_ids"] == [] for r in body["results"]) and "VERIFIED" not in current.text
    assert sorted(body["intent"]["basis"]["accepted_evidence_ids"]) == accepted
    with cold.engine.connect() as c:
        code = c.execute(text("SELECT public_code FROM work_case WHERE id = :c"), {"c": case_id}).scalar_one()
        title = c.execute(text("SELECT title FROM work_case_revision WHERE id = :r"), {"r": rev_id}).scalar_one()
    assert body["links"]["work"] == {"case_id": case_id, "case_code": code, "case_title": title,
                                     "request_state": "COMPLETED", "record_id": rec["id"],
                                     "label": f"Maintenance request {code}", "href": None}
    # K1 <= cutoff < K2: the Action exists, no case link yet; links.work all null and no declaration yet.
    not_linked = api.get(path, params={"known_at": iso(k1)})
    assert not_linked.status_code == 200, not_linked.text
    nl = not_linked.json()
    assert nl["links"]["work"] == dict.fromkeys(("case_id", "case_code", "case_title", "request_state", "record_id",
                                                 "label", "href"))
    assert (nl["intent"], nl["results"]) == (None, None)
    # A cutoff before the WR completed predates the Action root: ACTION_NOT_FOUND, and an absent Action likewise.
    for missing in (api.get(path, params={"known_at": iso(before_action)}),
                    api.get(f"/api/sites/{cold.code}/domain-work/actions/{uuid4()}")):
        assert missing.status_code == 404, missing.text
        assert missing.json()["detail"]["code"] == "ACTION_NOT_FOUND"
